#!/usr/bin/env python3
"""
Quality-focused JSONL enricher - single output stream with maximum quality
"""

import json
import logging
import hashlib
import signal
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Set, Optional, List
from dataclasses import dataclass
from llama_cpp import Llama

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
    """Minimal state for resumable processing"""
    processed_hashes: Set[str]
    last_line_number: int
    total_processed: int
    qa_pairs_generated: int
    start_time: str
    model_path: str
    input_file: str

    def to_dict(self) -> Dict:
        return {
            'processed_hashes': list(self.processed_hashes),
            'last_line_number': self.last_line_number,
            'total_processed': self.total_processed,
            'qa_pairs_generated': self.qa_pairs_generated,
            'start_time': self.start_time,
            'model_path': self.model_path,
            'input_file': self.input_file
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'ProcessingState':
        return cls(
            processed_hashes=set(data.get('processed_hashes', [])),
            last_line_number=data.get('last_line_number', 0),
            total_processed=data.get('total_processed', 0),
            qa_pairs_generated=data.get('qa_pairs_generated', 0),
            start_time=data.get('start_time', ''),
            model_path=data.get('model_path', ''),
            input_file=data.get('input_file', '')
        )


class QualityEnricher:
    def __init__(self, model_path: str, input_file: str, output_dir: str = "training_data"):
        self.model_path = model_path
        self.input_file = Path(input_file)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Single output file for training
        timestamp = datetime.now().strftime("%Y-%m-%d")
        self.output_file = self.output_dir / f"legal_qa_training_{timestamp}.jsonl"

        # State management
        self.state_file = self.output_dir / "processing_state.json"
        self.state = self._load_state()

        # Initialize model
        self._init_model()

        # Graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        self.shutdown_requested = False

    def _signal_handler(self, _signum, _frame):
        logger.info("\nShutdown signal received. Saving state...")
        self.shutdown_requested = True
        self._save_state()
        sys.exit(0)

    def _init_model(self):
        """Initialize model with optimized settings for quality"""
        logger.info("Loading model...")
        try:
            self.model = Llama(
                model_path=self.model_path,
                n_ctx=4096,
                n_threads=8,
                n_gpu_layers=35,
                verbose=False,
                seed=42  # Consistent outputs
            )
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def _load_state(self) -> ProcessingState:
        """Load processing state"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                state = ProcessingState.from_dict(data)

                if state.input_file != str(self.input_file):
                    logger.warning("Input file changed. Starting fresh.")
                    return self._create_new_state()

                logger.info(f"Resumed: {state.total_processed} docs, {state.qa_pairs_generated} Q&A pairs")
                return state
            except Exception as e:
                logger.error(f"Failed to load state: {e}")
                return self._create_new_state()
        return self._create_new_state()

    def _create_new_state(self) -> ProcessingState:
        return ProcessingState(
            processed_hashes=set(),
            last_line_number=0,
            total_processed=0,
            qa_pairs_generated=0,
            start_time=datetime.now().isoformat(),
            model_path=self.model_path,
            input_file=str(self.input_file)
        )

    def _save_state(self):
        """Save current state"""
        with open(self.state_file, 'w') as f:
            json.dump(self.state.to_dict(), f, indent=2)

    def _generate_high_quality_qa(self, doc: Dict) -> List[Dict]:
        """Generate high-quality Q&A pairs with enhanced validation"""
        header = doc.get('header', '')
        paragraphs = doc.get('paragraphs', [])
        full_text = '\n'.join(paragraphs)

        # Parse section info
        parts = header.split('|', 1)
        section_num = parts[0].replace('Section ', '').strip()
        title = parts[1].strip() if len(parts) > 1 else ''

        # High-priority question types for legal training
        priority_questions = [
            ("What actions are mandated by Section {section}?", "mandatory_actions"),
            ("What is prohibited under Section {section}?", "prohibitions"),
            ("Who must comply with Section {section}?", "covered_entities"),
            ("What are the penalties for violating Section {section}?", "penalties"),
            ("What exceptions exist to Section {section}?", "exemptions"),
            ("What conditions precedent exist in Section {section}?", "conditions"),
            ("What jurisdiction is specified in Section {section}?", "jurisdiction"),
        ]

        qa_pairs = []

        for question_template, q_type in priority_questions:
            if len(qa_pairs) >= 8:  # Increased from 7 to 8 core questions
                break

            question = question_template.format(section=section_num)

            # Enhanced prompt for better extraction
            prompt = f"""<|im_start|>system
You are a legal expert extracting precise information from Ohio Revised Code sections. Provide only factual information directly stated in the text. Be complete but concise.<|im_end|>

<|im_start|>user
Section {section_num}: {title}

Statutory Text:
{full_text[:3500]}

Question: {question}

Extract the specific information requested. If not stated in the text, respond "Not specified in this section."<|im_end|>

<|im_start|>assistant
"""

            try:
                response = self.model(
                    prompt,
                    max_tokens=300,
                    temperature=0.2,  # Lower for more factual
                    top_p=0.8,  # More focused
                    stop=["<|im_end|>", "\n\nQuestion:", "Section "],
                    echo=False
                )

                answer = response['choices'][0]['text'].strip()

                # Strict quality validation
                if self._is_high_quality_answer(answer, q_type, full_text):
                    qa_pairs.append({
                        'question': question,
                        'answer': answer
                    })
                    logger.debug(f"✓ Generated {q_type}")
                else:
                    logger.debug(f"✗ Rejected {q_type} - quality check failed")

            except Exception as e:
                logger.error(f"Generation failed for {q_type}: {e}")
                continue

        return qa_pairs

    def _generate_contextual_questions(self, doc: Dict, existing_qa: List[Dict]) -> List[Dict]:
        """Generate additional questions based on document content and existing Q&As"""
        header = doc.get('header', '')
        paragraphs = doc.get('paragraphs', [])
        full_text = '\n'.join(paragraphs)

        # Parse section info
        parts = header.split('|', 1)
        section_num = parts[0].replace('Section ', '').strip()
        title = parts[1].strip() if len(parts) > 1 else ''

        contextual_qa = []
        existing_types = {qa.get('type', '') for qa in existing_qa}

        # Content-driven questions based on what's actually in the text
        content_questions = []
        text_lower = full_text.lower()

        # Numbers and amounts (fees, penalties, timeframes)
        if any(term in text_lower for term in ['dollar', '
                                                         """Strict validation for training quality"""
               if not answer or len(answer.strip()) < 25:
            return False

        answer_lower = answer.lower().strip()

        # Reject non-answers immediately
        non_answers = [
            "not specified", "no information", "does not mention",
            "not found", "unclear", "n/a", "none specified",
            "not stated", "not provided", "text does not"
        ]
        if any(phrase in answer_lower for phrase in non_answers):
            return False

        # Reject speculation
        speculation = [
            "appears to", "seems to", "likely", "probably", "suggests",
            "implies", "might", "could be", "may be", "presumably"
        ]
        if any(phrase in answer_lower for phrase in speculation):
            return False

        # Check for incomplete sentences (trail-offs)
        if answer.endswith((',', ';', 'and', 'or', 'the', 'a', 'an')):
            return False

        # Must contain expected content for question type
        type_requirements = {
            "mandatory_actions": ["shall", "must", "required"],
            "prohibitions": ["shall not", "prohibited", "may not", "unlawful"],
            "covered_entities": ["member", "person", "individual", "entity", "board"],
            "penalties": ["penalty", "fine", "violation", "misdemeanor", "felony"],
            "exemptions": ["except", "does not apply", "exemption", "excluding"],
            "conditions": ["if", "when", "provided", "condition", "precedent"],
            "jurisdiction": ["court", "state", "county", "jurisdiction", "ohio"]
        }

        if q_type in type_requirements:
            required_terms = type_requirements[q_type]
            if not any(term in answer_lower for term in required_terms):
                return False

        # Check answer comes from source (anti-hallucination)
        meaningful_words = set(
            word.lower().strip('.,;:()[]{}"\'-')
            for word in answer.split()
            if len(word) > 4 and word not in {'shall', 'must', 'required', 'section', 'under'}
        )

        source_words = set(
            word.lower().strip('.,;:()[]{}"\'-')
            for word in source_text.split()
            if len(word) > 4
        )

        if meaningful_words:
            overlap = len(meaningful_words & source_words) / len(meaningful_words)
            if overlap < 0.4:  # Require 40% overlap
                return False

        return True

    def _write_qa_pair(self, qa_pair: Dict):
        """Write single Q&A pair to training file"""
        with open(self.output_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(qa_pair, ensure_ascii=False) + '\n')

    def run(self, max_docs: Optional[int] = None):
        """Streamlined processing focused on quality"""
        logger.info(f"Starting quality-focused processing")
        logger.info(f"Output file: {self.output_file}")

        docs_processed = 0

        with open(self.input_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                # Resume from checkpoint
                if line_num <= self.state.last_line_number:
                    continue

                if max_docs and docs_processed >= max_docs:
                    break

                if self.shutdown_requested:
                    break

                try:
                    doc = json.loads(line.strip())
                    doc_hash = hashlib.sha256(
                        json.dumps(doc, sort_keys=True).encode()
                    ).hexdigest()

                    if doc_hash in self.state.processed_hashes:
                        continue

                    header = doc.get('header', '')[:80]
                    logger.info(f"[{line_num}] Processing: {header}...")

                    # Generate Q&A pairs with higher yield
                    qa_pairs = self._generate_high_quality_qa(doc)

                    # Generate additional contextual questions if document is rich
                    if len(full_text) > 500:
                        contextual_qa = self._generate_contextual_questions(doc, qa_pairs)
                        qa_pairs.extend(contextual_qa)

                    if qa_pairs:
                        # Write each Q&A pair immediately for streaming
                        for qa in qa_pairs:
                            self._write_qa_pair(qa)
                            self.state.qa_pairs_generated += 1

                        self.state.processed_hashes.add(doc_hash)
                        self.state.total_processed += 1
                        docs_processed += 1

                        logger.info(f"✓ Generated {len(qa_pairs)} high-quality Q&A pairs")
                    else:
                        logger.warning(f"✗ No quality Q&A pairs generated")

                    self.state.last_line_number = line_num

                    # Save state every 10 docs
                    if self.state.total_processed % 10 == 0:
                        self._save_state()
                        logger.info(
                            f"Checkpoint: {self.state.total_processed} docs, {self.state.qa_pairs_generated} Q&A pairs")

                except Exception as e:
                    logger.error(f"Error at line {line_num}: {e}")
                    self.state.last_line_number = line_num
                    continue

        self._save_state()

        # Final summary
        logger.info(f"\n{'=' * 50}")
        logger.info(f"Quality processing complete!")
        logger.info(f"Documents processed: {self.state.total_processed}")
        logger.info(f"Q&A pairs generated: {self.state.qa_pairs_generated}")
        logger.info(f"Average Q&A per doc: {self.state.qa_pairs_generated / max(1, self.state.total_processed):.1f}")
        logger.info(f"Training file: {self.output_file}")
        logger.info(f"{'=' * 50}")


if __name__ == "__main__":
    # Your configuration
    MODEL_PATH = "/Users/justinrussell/.cache/huggingface/hub/models--bachbouch--GGUF-mistral-7b-instruct-v0.2-bnb-q4_k_m-tax-1/blobs/eefac64c338082318dd45aca85b3193b61a93469d1807546883e7829a84eaf19"
    INPUT_FILE = "/src/ohio_revised_data/scraped_code/ohio_revised_code_complete.jsonl"

    enricher = QualityEnricher(
        model_path=MODEL_PATH,
        input_file=INPUT_FILE,
        output_dir="training_data"
    )

    # Process all documents for maximum training data
    enricher.run(max_docs=None), 'fee', 'fine', 'cost']):
    content_questions.append(("What fees are specified in Section {section}?", "fees"))

    if any(term in text_lower for term in ['day', 'days', 'month', 'year', 'within', 'before']):
        content_questions.append(("What time limits are established in Section {section}?", "time_limits"))

    # Forms and documentation
    if any(term in text_lower for term in ['form', 'document', 'record', 'report', 'application']):
        content_questions.append(("What documentation is required by Section {section}?", "documentation"))

    # Approval processes
    if any(term in text_lower for term in ['approval', 'approve', 'consent', 'authorize']):
        content_questions.append(("What approval requirements exist in Section {section}?", "approval_requirements"))

    # Board/agency authorities
    if any(term in text_lower for term in ['board', 'commission', 'director', 'department']):
        content_questions.append(("What authorities are established by Section {section}?", "authorities"))

    # Meeting/procedural requirements
    if any(term in text_lower for term in ['meeting', 'vote', 'quorum', 'majority']):
        content_questions.append(("What meeting requirements exist in Section {section}?", "meetings"))

    # Generate contextual Q&A pairs
    for question_template, q_type in content_questions:
        if
    q_type in existing_types or len(contextual_qa) >= 5:  # Limit additional questions
    continue

    question = question_template.format(section=section_num)

    prompt = f"""<|im_start|>system
Extract specific factual details from the Ohio statute. Focus on concrete requirements, amounts, and procedures.<|im_end|>

<|im_start|>user
Section {section_num}: {title}

Statutory Text:
{full_text[:3000]}

Question: {question}

Extract only the specific details requested. If not explicitly stated, respond "Not specified in this section."<|im_end|>

<|im_start|>assistant
"""

    try:
        response = self.model(
            prompt,
            max_tokens=200,
            temperature=0.1,  # Very low for factual extraction
            top_p=0.7,
            stop=["<|im_end|>", "\n\nQuestion:"],
            echo=False
        )

        answer = response['choices'][0]['text'].strip()

        # Lighter validation for contextual questions
        if self._is_contextual_answer_valid(answer, full_text):
            contextual_qa.append({
                'question': question,
                'answer': answer
            })
            logger.debug(f"✓ Contextual: {q_type}")

    except Exception as e:
        logger.debug(f"Contextual generation failed for {q_type}: {e}")
        continue

return contextual_qa
"""Strict validation for training quality"""
if not answer or len(answer.strip()) < 25:
    return False

answer_lower = answer.lower().strip()

# Reject non-answers immediately
non_answers = [
    "not specified", "no information", "does not mention",
    "not found", "unclear", "n/a", "none specified",
    "not stated", "not provided", "text does not"
]
if any(phrase in answer_lower for phrase in non_answers):
    return False

# Reject speculation
speculation = [
    "appears to", "seems to", "likely", "probably", "suggests",
    "implies", "might", "could be", "may be", "presumably"
]
if any(phrase in answer_lower for phrase in speculation):
    return False

# Check for incomplete sentences (trail-offs)
if answer.endswith((',', ';', 'and', 'or', 'the', 'a', 'an')):
    return False

# Must contain expected content for question type
type_requirements = {
    "mandatory_actions": ["shall", "must", "required"],
    "prohibitions": ["shall not", "prohibited", "may not", "unlawful"],
    "covered_entities": ["member", "person", "individual", "entity", "board"],
    "penalties": ["penalty", "fine", "violation", "misdemeanor", "felony"],
    "exemptions": ["except", "does not apply", "exemption", "excluding"],
    "conditions": ["if", "when", "provided", "condition", "precedent"],
    "jurisdiction": ["court", "state", "county", "jurisdiction", "ohio"]
}

if q_type in type_requirements:
    required_terms = type_requirements[q_type]
    if not any(term in answer_lower for term in required_terms):
        return False

# Check answer comes from source (anti-hallucination)
meaningful_words = set(
    word.lower().strip('.,;:()[]{}"\'-')
    for word in answer.split()
    if len(word) > 4 and word not in {'shall', 'must', 'required', 'section', 'under'}
)

source_words = set(
    word.lower().strip('.,;:()[]{}"\'-')
    for word in source_text.split()
    if len(word) > 4
)

if meaningful_words:
    overlap = len(meaningful_words & source_words) / len(meaningful_words)
    if overlap < 0.4:  # Require 40% overlap
        return False

return True


def _write_qa_pair(self, qa_pair: Dict):
    """Write single Q&A pair to training file"""
    with open(self.output_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(qa_pair, ensure_ascii=False) + '\n')


def run(self, max_docs: Optional[int] = None):
    """Streamlined processing focused on quality"""
    logger.info(f"Starting quality-focused processing")
    logger.info(f"Output file: {self.output_file}")

    docs_processed = 0

    with open(self.input_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            # Resume from checkpoint
            if line_num <= self.state.last_line_number:
                continue

            if max_docs and docs_processed >= max_docs:
                break

            if self.shutdown_requested:
                break

            try:
                doc = json.loads(line.strip())
                doc_hash = hashlib.sha256(
                    json.dumps(doc, sort_keys=True).encode()
                ).hexdigest()

                if doc_hash in self.state.processed_hashes:
                    continue

                header = doc.get('header', '')[:80]
                logger.info(f"[{line_num}] Processing: {header}...")

                # Generate Q&A pairs with higher yield
                qa_pairs = self._generate_high_quality_qa(doc)

                # Generate additional contextual questions if document is rich
                if len(full_text) > 500:
                    contextual_qa = self._generate_contextual_questions(doc, qa_pairs)
                    qa_pairs.extend(contextual_qa)

                if qa_pairs:
                    # Write each Q&A pair immediately for streaming
                    for qa in qa_pairs:
                        self._write_qa_pair(qa)
                        self.state.qa_pairs_generated += 1

                    self.state.processed_hashes.add(doc_hash)
                    self.state.total_processed += 1
                    docs_processed += 1

                    logger.info(f"✓ Generated {len(qa_pairs)} high-quality Q&A pairs")
                else:
                    logger.warning(f"✗ No quality Q&A pairs generated")

                self.state.last_line_number = line_num

                # Save state every 10 docs
                if self.state.total_processed % 10 == 0:
                    self._save_state()
                    logger.info(
                        f"Checkpoint: {self.state.total_processed} docs, {self.state.qa_pairs_generated} Q&A pairs")

            except Exception as e:
                logger.error(f"Error at line {line_num}: {e}")
                self.state.last_line_number = line_num
                continue

    self._save_state()

    # Final summary
    logger.info(f"\n{'=' * 50}")
    logger.info(f"Quality processing complete!")
    logger.info(f"Documents processed: {self.state.total_processed}")
    logger.info(f"Q&A pairs generated: {self.state.qa_pairs_generated}")
    logger.info(f"Average Q&A per doc: {self.state.qa_pairs_generated / max(1, self.state.total_processed):.1f}")
    logger.info(f"Training file: {self.output_file}")
    logger.info(f"{'=' * 50}")


if __name__ == "__main__":
    # Your configuration
    MODEL_PATH = "/Users/justinrussell/.cache/huggingface/hub/models--bachbouch--GGUF-mistral-7b-instruct-v0.2-bnb-q4_k_m-tax-1/blobs/eefac64c338082318dd45aca85b3193b61a93469d1807546883e7829a84eaf19"
    INPUT_FILE = "/src/ohio_revised_data/scraped_code/ohio_revised_code_complete.jsonl"

    enricher = QualityEnricher(
        model_path=MODEL_PATH,
        input_file=INPUT_FILE,
        output_dir="training_data"
    )

    # Process all documents for maximum training data
    enricher.run(max_docs=None)