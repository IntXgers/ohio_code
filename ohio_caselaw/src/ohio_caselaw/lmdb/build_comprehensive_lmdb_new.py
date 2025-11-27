#!/usr/bin/env python3
"""
Comprehensive LMDB builder for Ohio Case Law
Creates multiple specialized databases with full metadata and citation chains
Includes progress checkpointing and resume capability for 175K+ cases
"""

import json
import lmdb
import logging
import pickle
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Optional, Iterator
from dataclasses import dataclass, asdict

# Import auto-enricher
from auto_enricher_caselaw import AutoEnricher

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class BuildProgress:
    """Track build progress for resume capability"""
    total_processed: int = 0
    last_case_id: Optional[int] = None
    primary_count: int = 0
    citations_count: int = 0
    reverse_citations_count: int = 0
    chains_count: int = 0
    start_time: str = None
    last_checkpoint: str = None

    def to_dict(self):
        return asdict(self)


class ComprehensiveLMDBBuilder:
    """Builds multiple LMDB databases with complete case law data"""

    # CHECKPOINT: Save progress every 10K cases
    CHECKPOINT_INTERVAL = 10000

    # BATCH SIZE: Process in batches to avoid loading all 175K into memory
    BATCH_SIZE = 5000

    def __init__(self, data_dir: Path, output_dir: Path = None, enable_enrichment: bool = True, resume: bool = True):
        self.data_dir = data_dir

        # Output to central dist/ folder
        if output_dir:
            self.lmdb_dir = output_dir
        else:
            # Find project root (4 levels up from lmdb/)
            PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
            self.lmdb_dir = PROJECT_ROOT / "dist" / "ohio_caselaw"

        self.lmdb_dir.mkdir(parents=True, exist_ok=True)

        # Input file - 175,857 cases
        self.corpus_file = data_dir / "pre_enriched_input" / "jsonl_all" / "ohio_case_law_complete.jsonl"

        # Progress tracking
        self.progress_file = self.lmdb_dir / "build_progress.pkl"
        self.resume_enabled = resume
        self.progress = BuildProgress()
        self.processed_case_ids = set()

        # LMDB environments (RENAMED: primary.lmdb not sections.lmdb)
        self.primary_db = None
        self.citations_db = None
        self.chains_db = None
        self.metadata_db = None
        self.reverse_citations_db = None

        # In-memory data (for current batch only)
        self.citation_map: Dict[str, List[str]] = {}
        self.cases_data: Dict[str, Dict] = {}

        # Auto-enrichment
        self.enable_enrichment = enable_enrichment
        self.enricher = AutoEnricher() if enable_enrichment else None
        if enable_enrichment:
            logger.info("🎨 Auto-enrichment ENABLED - metadata will be added to cases")

        # Load previous progress if resuming
        if self.resume_enabled and self.progress_file.exists():
            self._load_progress()

    def _load_progress(self):
        """Load previous build progress"""
        try:
            with open(self.progress_file, 'rb') as f:
                saved_progress = pickle.load(f)
                self.progress = saved_progress['progress']
                self.processed_case_ids = saved_progress['processed_ids']
                logger.info(f"📥 Resuming from previous build: {self.progress.total_processed} cases processed")
                logger.info(f"   Last checkpoint: {self.progress.last_checkpoint}")
        except Exception as e:
            logger.warning(f"Could not load progress: {e}. Starting fresh.")
            self.progress = BuildProgress()
            self.processed_case_ids = set()

    def _save_progress(self):
        """Save current build progress"""
        try:
            self.progress.last_checkpoint = datetime.now().isoformat()
            with open(self.progress_file, 'wb') as f:
                pickle.dump({
                    'progress': self.progress,
                    'processed_ids': self.processed_case_ids
                }, f)
            logger.info(f"💾 Progress checkpoint saved: {self.progress.total_processed} cases")
        except Exception as e:
            logger.error(f"Failed to save progress: {e}")

    def open_databases(self):
        """Open all LMDB databases with 10-15GB map_size"""
        logger.info("Opening LMDB databases...")

        # INCREASED: 15GB max size per database (was 2GB)
        map_size = 15 * 1024 * 1024 * 1024

        # RENAMED: primary.lmdb instead of sections.lmdb
        self.primary_db = lmdb.open(
            str(self.lmdb_dir / "primary.lmdb"),
            map_size=map_size,
            max_dbs=0
        )

        self.citations_db = lmdb.open(
            str(self.lmdb_dir / "citations.lmdb"),
            map_size=map_size,
            max_dbs=0
        )

        self.chains_db = lmdb.open(
            str(self.lmdb_dir / "chains.lmdb"),
            map_size=map_size,
            max_dbs=0
        )

        self.metadata_db = lmdb.open(
            str(self.lmdb_dir / "metadata.lmdb"),
            map_size=map_size,
            max_dbs=0
        )

        self.reverse_citations_db = lmdb.open(
            str(self.lmdb_dir / "reverse_citations.lmdb"),
            map_size=map_size,
            max_dbs=0
        )

        logger.info(f"All databases opened successfully (15GB map_size each)")

    def close_databases(self):
        """Close all LMDB databases"""
        for db in [self.primary_db, self.citations_db, self.chains_db,
                   self.metadata_db, self.reverse_citations_db]:
            if db:
                db.close()
        logger.info("All databases closed")

    def _read_cases_in_batches(self) -> Iterator[List[Dict]]:
        """
        BATCH PROCESSING: Read cases in batches instead of loading all 175K into memory
        Yields batches of cases to process
        """
        batch = []
        skipped = 0

        with open(self.corpus_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    # Skip first line if it's metadata
                    if line_num == 1 and 'processed_files' in line:
                        logger.info("Skipping metadata line")
                        continue

                    case = json.loads(line)
                    case_id = case.get('id')

                    # RESUME CAPABILITY: Skip already processed cases
                    if self.resume_enabled and case_id in self.processed_case_ids:
                        skipped += 1
                        continue

                    batch.append(case)

                    # Yield batch when it reaches BATCH_SIZE
                    if len(batch) >= self.BATCH_SIZE:
                        if skipped > 0:
                            logger.info(f"Skipped {skipped} already-processed cases")
                            skipped = 0
                        yield batch
                        batch = []

                except json.JSONDecodeError as e:
                    logger.warning(f"Skipping invalid JSON on line {line_num}: {e}")
                    continue

        # Yield remaining cases
        if batch:
            if skipped > 0:
                logger.info(f"Skipped {skipped} already-processed cases (final batch)")
            yield batch

    def build_primary_database(self):
        """Build main cases database with full metadata"""
        logger.info("Building primary cases database...")

        if self.progress.start_time is None:
            self.progress.start_time = datetime.now().isoformat()

        for batch_num, batch in enumerate(self._read_cases_in_batches(), 1):
            logger.info(f"📦 Processing batch {batch_num} ({len(batch)} cases)...")

            with self.primary_db.begin(write=True) as txn:
                for case in batch:
                    case_id = case.get('id')
                    if not case_id:
                        logger.warning("Skipping case without ID")
                        continue

                    # Extract key fields for case law schema
                    casebody = case.get('casebody', {})
                    opinions = casebody.get('opinions', [])
                    court = case.get('court', {})
                    citations = case.get('citations', [])

                    # Build complete case record
                    case_data = {
                        'case_id': case_id,
                        'case_name': case.get('name', ''),
                        'name_abbreviation': case.get('name_abbreviation', ''),
                        'decision_date': case.get('decision_date', ''),
                        'docket_number': case.get('docket_number', ''),
                        'court': {
                            'name': court.get('name', ''),
                            'name_abbreviation': court.get('name_abbreviation', ''),
                            'id': court.get('id')
                        },
                        'citations': citations,
                        'casebody': casebody,  # PRESERVED - exact legal text
                        'opinions': opinions,
                        'judges': casebody.get('judges', []),
                        'parties': casebody.get('parties', []),
                        'attorneys': casebody.get('attorneys', []),
                        'word_count': sum(len(op.get('text', '').split()) for op in opinions),
                        'opinion_count': len(opinions),
                        'citation_count': len(case.get('cites_to', [])),
                        'scraped_date': datetime.now().isoformat()
                    }

                    # AUTO-ENRICH: Add metadata without touching legal text
                    if self.enable_enrichment and self.enricher:
                        citation_count = len(case.get('cites_to', []))
                        case_data = self.enricher.enrich_case(case_data, citation_count)

                    # Store in memory for later use (citations, reverse citations)
                    case_key = str(case_id)
                    self.cases_data[case_key] = case_data

                    # Build citation map
                    cites_to = case.get('cites_to', [])
                    if cites_to:
                        self.citation_map[case_key] = [
                            str(cite.get('case_ids', [])[0])
                            for cite in cites_to
                            if cite.get('case_ids')
                        ]

                    # Store in LMDB
                    key = str(case_id).encode()
                    value = json.dumps(case_data, ensure_ascii=False).encode()
                    txn.put(key, value)

                    # Track progress
                    self.progress.total_processed += 1
                    self.progress.primary_count += 1
                    self.progress.last_case_id = case_id
                    self.processed_case_ids.add(case_id)

                    # CHECKPOINT: Save progress every 10K cases
                    if self.progress.total_processed % self.CHECKPOINT_INTERVAL == 0:
                        logger.info(f"✓ Processed {self.progress.total_processed} cases...")
                        self._save_progress()

            # Build citations and reverse citations for this batch
            self._build_batch_citations()

            # Clear batch data from memory
            self.cases_data.clear()
            self.citation_map.clear()

        logger.info(f"Primary database built: {self.progress.primary_count} cases")
        return self.progress.primary_count

    def _build_batch_citations(self):
        """Build citations and reverse citations for current batch"""
        # Build citations database
        with self.citations_db.begin(write=True) as txn:
            for case_id, references in self.citation_map.items():
                citation_data = {
                    'case_id': case_id,
                    'cites_to': references,
                    'citation_count': len(references)
                }

                key = case_id.encode()
                value = json.dumps(citation_data, ensure_ascii=False).encode()
                txn.put(key, value)
                self.progress.citations_count += 1

        # Build reverse citations (what cites this case)
        reverse_map: Dict[str, Set[str]] = {}
        for case_id, references in self.citation_map.items():
            for ref in references:
                if ref not in reverse_map:
                    reverse_map[ref] = set()
                reverse_map[ref].add(case_id)

        with self.reverse_citations_db.begin(write=True) as txn:
            for case_id, citing_cases in reverse_map.items():
                reverse_data = {
                    'case_id': case_id,
                    'cited_by': sorted(list(citing_cases)),
                    'cited_by_count': len(citing_cases)
                }

                key = case_id.encode()
                value = json.dumps(reverse_data, ensure_ascii=False).encode()
                txn.put(key, value)
                self.progress.reverse_citations_count += 1

    def build_metadata_database(self):
        """Build metadata database with corpus information"""
        logger.info("Building metadata database...")

        with self.metadata_db.begin(write=True) as txn:
            # Corpus-level metadata
            corpus_meta = {
                'total_cases': self.progress.primary_count,
                'cases_with_citations': self.progress.citations_count,
                'reverse_citations': self.progress.reverse_citations_count,
                'complex_chains': self.progress.chains_count,
                'build_date': datetime.now().isoformat(),
                'build_start': self.progress.start_time,
                'source': 'Ohio Case Law Complete Corpus',
                'version': '3.0',
                'builder': 'comprehensive_lmdb_builder_caselaw',
                'enrichment_enabled': self.enable_enrichment,
                'databases': {
                    'primary': 'Full case opinions with metadata',
                    'citations': 'Forward citation references',
                    'reverse_citations': 'Backward citation references',
                    'chains': 'Citation chains with full text',
                    'metadata': 'Corpus and case metadata'
                }
            }

            txn.put(b'corpus_info', json.dumps(corpus_meta, indent=2).encode())

        logger.info("Metadata database built")

    def build_all(self):
        """Build all databases"""
        logger.info("="*80)
        logger.info("Starting comprehensive Ohio Case Law LMDB build")
        logger.info(f"Corpus file: {self.corpus_file}")
        logger.info(f"Output directory: {self.lmdb_dir}")
        logger.info(f"Resume enabled: {self.resume_enabled}")
        logger.info(f"Batch size: {self.BATCH_SIZE}")
        logger.info(f"Checkpoint interval: {self.CHECKPOINT_INTERVAL}")
        logger.info("="*80)

        try:
            # Verify input file exists
            if not self.corpus_file.exists():
                raise FileNotFoundError(f"Corpus file not found: {self.corpus_file}")

            # Open databases
            self.open_databases()

            # Build primary database (handles batching, checkpointing, resume)
            primary_count = self.build_primary_database()

            # Build metadata database
            self.build_metadata_database()

            # Final checkpoint
            self._save_progress()

            # Build complete!
            logger.info("="*80)
            logger.info("Build Summary:")
            logger.info(f"  Total Cases: {primary_count}")
            logger.info(f"  Citations: {self.progress.citations_count}")
            logger.info(f"  Reverse Citations: {self.progress.reverse_citations_count}")
            logger.info(f"  Output: {self.lmdb_dir}")
            logger.info(f"  Start Time: {self.progress.start_time}")
            logger.info(f"  End Time: {datetime.now().isoformat()}")
            logger.info("="*80)

            # Remove progress file on successful completion
            if self.progress_file.exists():
                self.progress_file.unlink()
                logger.info("✅ Build completed successfully - progress file removed")

        except Exception as e:
            logger.error(f"Build failed: {e}")
            self._save_progress()
            logger.info("💾 Progress saved - you can resume with resume=True")
            raise

        finally:
            self.close_databases()


if __name__ == "__main__":
    from pathlib import Path

    # Use path from symlink
    DATA_DIR = Path(__file__).parent.parent / "data"

    # Output to central dist/ folder
    PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
    OUTPUT_DIR = PROJECT_ROOT / "dist" / "ohio_caselaw"

    print(f"DATA_DIR: {DATA_DIR}")
    print(f"OUTPUT_DIR: {OUTPUT_DIR}")
    print(f"Checking required files...")

    # Verify corpus file exists
    corpus_file = DATA_DIR / "pre_enriched_input" / "jsonl_all" / "ohio_case_law_complete.jsonl"

    if not corpus_file.exists():
        print(f"ERROR: Corpus file not found: {corpus_file}")
        print(f"  Checking if symlink exists...")
        if DATA_DIR.exists():
            print(f"  DATA_DIR exists: {DATA_DIR}")
            print(f"  Contents: {list(DATA_DIR.iterdir())}")
        exit(1)

    print("✓ Corpus file found")
    print(f"  Size: {corpus_file.stat().st_size / (1024**3):.2f} GB")

    # Count lines to verify
    print("Counting cases...")
    import subprocess
    result = subprocess.run(['wc', '-l', str(corpus_file)], capture_output=True, text=True)
    total_lines = int(result.stdout.split()[0])
    print(f"  Total lines: {total_lines:,}")
    print(f"  Expected cases: ~{total_lines-1:,} (minus metadata line)")

    print("\n" + "="*80)
    print("Starting build with:")
    print("  - Progress checkpointing every 10K cases")
    print("  - Resume capability (resume=True)")
    print("  - Batch processing (5K cases per batch)")
    print("  - 15GB map_size per database")
    print("  - Auto-enrichment enabled (7 fields)")
    print("="*80 + "\n")

    builder = ComprehensiveLMDBBuilder(DATA_DIR, OUTPUT_DIR, enable_enrichment=True, resume=True)
    builder.build_all()