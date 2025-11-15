#!/usr/bin/env python3
"""
Production-ready JSONL enricher with state management and resumability
"""

import json
import logging
import hashlib
import signal
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Set, Optional
from dataclasses import dataclass
from llama_cpp import Llama
from ohio_revised.citation_analysis.ohio_revised_mapping import get_title_from_section
from validate_output import validate_output
from template_loader import get_questions_with_fallback
import lmdb

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('enricher.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class ProcessingState:
    """Persistent state for resumable processing"""
    processed_hashes: Set[str]
    failed_hashes: Set[str]
    last_line_number: int
    total_processed: int
    total_failed: int
    start_time: str
    last_checkpoint: str
    model_path: str
    input_file: str

    def to_dict(self) -> Dict:
        return {
            'processed_hashes': list(self.processed_hashes),
            'failed_hashes': list(self.failed_hashes),
            'last_line_number': self.last_line_number,
            'total_processed': self.total_processed,
            'total_failed': self.total_failed,
            'start_time': self.start_time,
            'last_checkpoint': self.last_checkpoint,
            'model_path': self.model_path,
            'input_file': str(self.input_file)
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'ProcessingState':
        return cls(
            processed_hashes=set(data.get('processed_hashes', [])),
            failed_hashes=set(data.get('failed_hashes', [])),
            last_line_number=data.get('last_line_number', 0),
            total_processed=data.get('total_processed', 0),
            total_failed=data.get('total_failed', 0),
            start_time=data.get('start_time', ''),
            last_checkpoint=data.get('last_checkpoint', ''),
            model_path=data.get('model_path', ''),
            input_file=data.get('input_file', '')
        )


class RobustEnricher:
    lmdb_path: Path
    def __init__(self, MODEL_PATH: str, OHIO_CORPUS_FILE: str, ENRICHED_OUTPUT_DIR: str = "enriched_output"):
        self.model_path = MODEL_PATH
        self.input_file = Path(OHIO_CORPUS_FILE)
        self.output_dir = Path(ENRICHED_OUTPUT_DIR)
        self.output_dir.mkdir(exist_ok=True)
        self.lmdb_path = self.output_dir / "sections.lmdb"
        self.setup_lmdb()

        # State management
        self.state_file = self.output_dir / "processing_state.json"
        self.checkpoint_interval = 10  # Save state every N documents
        self.buffer = []  # Buffer for batch writing
        self.buffer_size = 5

        # Load or initialize state
        self.state = self._load_state()

        # Initialize model
        self._init_model()

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        self.shutdown_requested = False

    def setup_lmdb(self):
        """Build or load LMDB database of all sections"""
        # Create LMDB with 10GB max size (adjust as needed)
        self.env = lmdb.open(str(self.lmdb_path), map_size=10737418240)

        # Check if already populated
        with self.env.begin() as txn:
            if txn.stat()['entries'] == 0:
                logger.info("Building LMDB database from corpus...")
                self.populate_lmdb()
            else:
                logger.info(f"LMDB loaded with {txn.stat()['entries']} sections")

    def populate_lmdb(self):
        """One-time population of LMDB with all sections"""
        with self.env.begin(write=True) as txn:
            with open(self.input_file, 'r') as f:
                for line in f:
                    doc = json.loads(line)
                    header = doc.get('header', '')
                    if '|' in header:
                        section_num = header.split('|')[0].replace('Section ', '').strip()
                        # Store as JSON for full document
                        txn.put(section_num.encode(), json.dumps(doc).encode())

    def get_section_text(self, section_num: str) -> str:
        """Fetch section text from LMDB"""
        with self.env.begin() as txn:
            data = txn.get(section_num.encode())
            if data:
                doc = json.loads(data.decode())
                return '\n'.join(doc.get('paragraphs', []))
        return ""

    def _signal_handler(self, _signum, _frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"\nShutdown signal received. Saving state...")
        self.shutdown_requested = True
        self._save_state()
        self._flush_buffer()
        logger.info(f"State saved. Processed {self.state.total_processed} documents.")
        sys.exit(0)

    def _init_model(self):
        """Initialize the language model"""
        logger.info("Loading model...")
        try:
            self.model = Llama(
                model_path=str(self.model_path),
                n_ctx=8192,
                n_threads=8,
                n_gpu_layers=-1,  # Metal acceleration
                verbose=False,
                seed=42  # Reproducibility
            )
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    @staticmethod
    def _compute_hash(doc: Dict) -> str:
        """Generate deterministic hash for a document"""
        content = json.dumps(doc, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()

    def _load_state(self) -> ProcessingState:
        """Load previous processing state if exists"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                state = ProcessingState.from_dict(data)

                # Verify same input file and model
                if state.input_file != str(self.input_file):
                    logger.warning(f"Input file changed. Starting fresh.")
                    return self._create_new_state()

                logger.info(f"Resumed from checkpoint: {state.total_processed} documents processed")
                logger.info(f"Skipping to line {state.last_line_number + 1}")
                return state

            except Exception as e:
                logger.error(f"Failed to load state: {e}")
                return self._create_new_state()
        else:
            return self._create_new_state()

    def _create_new_state(self) -> ProcessingState:
        """Create fresh processing state"""
        return ProcessingState(
            processed_hashes=set(),
            failed_hashes=set(),
            last_line_number=0,
            total_processed=0,
            total_failed=0,
            start_time=datetime.now().isoformat(),
            last_checkpoint=datetime.now().isoformat(),
            model_path=self.model_path,
            input_file=str(self.input_file)
        )

    def _save_state(self):
        """Persist current processing state"""
        self.state.last_checkpoint = datetime.now().isoformat()
        with open(self.state_file, 'w') as f:
            json.dump(self.state.to_dict(), f, indent=2)
        logger.debug(f"State saved: {self.state.total_processed} processed, {self.state.total_failed} failed")

    def _generate_text(self, prompt: str, max_tokens: int = 400) -> str:
        """Generate text with better parameters for Mistral"""
        try:
            response = self.model(
                prompt,
                max_tokens=max_tokens,
                temperature=0.4,  # Slightly higher for less repetition
                top_p=0.95,  # Slightly higher for more diversity
                stop=["Question:", "\n\nSection", "\n\nStatutory"],  # Better stop sequences
                echo=False
            )
            return response['choices'][0]['text'].strip()
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return ""

    def _process_document(self, doc: Dict) -> Optional[Dict]:
        """Process single document with proper order and title-specific templates"""

        # 1. Compute hash first (identifies the document)
        doc_hash = self._compute_hash(doc)

        # 2. State checks - early returns to avoid unnecessary work
        if doc_hash in self.state.processed_hashes:
            logger.debug(f"Skipping already processed: {doc_hash[:8]}")
            return None

        if doc_hash in self.state.failed_hashes:
            logger.debug(f"Skipping previously failed: {doc_hash[:8]}")
            return None

        try:
            # 3. Title detection and validation - do this before expensive processing
            header = doc.get('header', '')
            if '|' in header:
                section_part = header.split('|')[0].replace('Section ', '').strip()

                # Load citation map if not already loaded
                if not hasattr(self, 'citation_map'):
                    citation_map_file = self.output_dir.parent / 'citation_analysis' / 'citation_map.json'
                    if citation_map_file.exists():
                        with open(citation_map_file, 'r') as f:
                            self.citation_map = json.load(f)
                    else:
                        self.citation_map = {}

                # Get referenced sections and fetch their actual text
                referenced_sections = self.citation_map.get(section_part, [])
                reference_texts = []

                for ref_section in referenced_sections[:3]:  # Limit to top 3
                    ref_text = self.get_section_text(ref_section)  # This uses LMDB
                    if ref_text:
                        reference_texts.append(f"Section {ref_section}:\n{ref_text[:1000]}")

                # Build context with actual referenced text
                reference_context = ""
                if reference_texts:
                    reference_context = "\n\nReferenced Sections:\n" + "\n\n".join(reference_texts)

                title = get_title_from_section(section_part)

                if not title or title.startswith("Unknown Title"):
                    logger.warning(f"Could not map title for section: {section_part}")
                    self.state.failed_hashes.add(doc_hash)
                    self.state.total_failed += 1
                    return None

                logger.debug(f"Processing {title}: Section {section_part}")
            else:
                logger.warning(f"Could not parse section from header: {header}")
                self.state.failed_hashes.add(doc_hash)
                self.state.total_failed += 1
                return None

            # 4. Get title-appropriate questions using the template loader
            questions = get_questions_with_fallback(section_part)
            logger.info(f"Template loader returned {len(questions)} questions for {title}")

            if not questions:
                logger.warning(f"No questions available for section {section_part}")
                self.state.failed_hashes.add(doc_hash)
                self.state.total_failed += 1
                return None

            # 5. Generate Q&A pairs using title-specific questions
            qa_pairs = []
            law_text = '\n'.join(doc.get('paragraphs', []))
            section_title = header.split('|')[1].strip() if '|' in header else ''

            for question, q_type in questions[:10]:  # Limit to 10 questions max
                # Create enhanced prompt with actual reference context
                prompt = f"""Extract information from the Ohio Revised Code.

    Section {section_part}: {section_title}

    Statutory Text:
    {law_text[:3000]}{reference_context}

    Question: {question}

    Instructions: Provide only factual information directly stated in the text. If the information is not present, respond "Not specified in this section."

    Answer:"""

                try:
                    # Generate response
                    response = self._generate_text(prompt, max_tokens=400)

                    # Validate response quality
                    if response and len(response.strip()) > 20:
                        response_clean = response.strip()

                        # Validate using imported function
                        if validate_output(response_clean, q_type, law_text):
                            qa_pairs.append({
                                'question': question,
                                'answer': response_clean,
                                'type': q_type,
                                'section': section_part,
                                'title': title
                            })
                            logger.debug(f"Generated {q_type} (validated)")
                        else:
                            logger.debug(f"Validation failed for {q_type}")

                except Exception as e:
                    logger.error(f"Failed to generate {q_type}: {e}")
                    continue

            if not qa_pairs:
                logger.warning(f"No valid QA pairs generated for: {header[:50]}")
                self.state.failed_hashes.add(doc_hash)
                self.state.total_failed += 1
                return None

            # 6. State updates - mark as successfully processed
            self.state.processed_hashes.add(doc_hash)
            self.state.total_processed += 1

            logger.info(f"Generated {len(qa_pairs)} QA pairs for {title}")

            return {
                "doc_hash": doc_hash[:8],
                "title": title,
                "section": section_part,
                "original": doc,
                "qa_pairs": qa_pairs,
                "processed_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to process document: {e}")
            # State updates - mark as failed
            self.state.failed_hashes.add(doc_hash)
            self.state.total_failed += 1
            return None

    def _write_to_file(self, data: Dict, file_type: str):
        """Append data to appropriate output file"""
        timestamp = self.state.start_time.replace(':', '-')[:10]
        output_file = self.output_dir / f"{file_type}_{timestamp}.jsonl"

        with open(output_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False) + '\n')

    def _flush_buffer(self):
        """Write buffered results to disk"""
        if not self.buffer:
            return

        for doc in self.buffer:
            # Write Q&A pairs in simple format for training
            for qa in doc.get('qa_pairs', []):
                # Enhanced Q&A format with title context
                enhanced_qa = {
                    'question': qa['question'],
                    'answer': qa['answer'],
                    'title': doc.get('title', 'Unknown'),
                    'section': doc.get('section', 'Unknown'),
                    'type': qa.get('type', 'unknown')
                }
                self._write_to_file(enhanced_qa, 'training_qa')

        logger.info(f"Flushed {len(self.buffer)} documents to disk")
        self.buffer.clear()

    def run(self, max_docs: Optional[int] = None):
        """Main processing loop with resumability"""
        logger.info(f"Starting processing from line {self.state.last_line_number + 1}")

        if max_docs:
            logger.info(f"Processing maximum {max_docs} documents")

        docs_in_session = 0

        with open(self.input_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                # Skip to resume point
                if line_num <= self.state.last_line_number:
                    continue

                # Check limits
                if max_docs and docs_in_session >= max_docs:
                    break

                # Check for shutdown
                if self.shutdown_requested:
                    break

                try:
                    doc = json.loads(line.strip())
                    header = doc.get('header', '')[:80]

                    logger.info(f"[{line_num}] Processing: {header}...")

                    enriched = self._process_document(doc)

                    if enriched:
                        self.buffer.append(enriched)
                        docs_in_session += 1

                        # Flush buffer if full
                        if len(self.buffer) >= self.buffer_size:
                            self._flush_buffer()

                        # Checkpoint periodically
                        if self.state.total_processed % self.checkpoint_interval == 0:
                            self._save_state()
                            logger.info(f"Checkpoint: {self.state.total_processed} total processed")

                    self.state.last_line_number = line_num

                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON at line {line_num}: {e}")
                    self.state.last_line_number = line_num
                    continue
                except Exception as e:
                    logger.error(f"Error at line {line_num}: {e}")
                    self.state.last_line_number = line_num
                    continue

        # Final flush and save
        self._flush_buffer()
        self._save_state()

        # Summary
        logger.info(f"\n{'=' * 50}")
        logger.info(f"Processing complete!")
        logger.info(f"Total processed: {self.state.total_processed}")
        logger.info(f"Total failed: {self.state.total_failed}")
        logger.info(f"Session processed: {docs_in_session}")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info(f"{'=' * 50}")


if __name__ == "__main__":
    # Configuration
    from config import OHIO_CORPUS_FILE, MODEL_PATH, ENRICHED_OUTPUT_DIR

    enricher = RobustEnricher(
        MODEL_PATH=MODEL_PATH,
        OHIO_CORPUS_FILE=str(OHIO_CORPUS_FILE),
        ENRICHED_OUTPUT_DIR=str(ENRICHED_OUTPUT_DIR)
    )
