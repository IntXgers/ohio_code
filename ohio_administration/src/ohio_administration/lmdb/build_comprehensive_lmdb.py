#!/usr/bin/env python3
"""
Comprehensive LMDB builder for Ohio Administration Code
Creates multiple specialized databases with full metadata and citation chains
"""

import json
import lmdb
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Optional, cast
from dataclasses import dataclass, asdict
import sys

# Import auto-enricher
from auto_enricher import AutoEnricher

# Import generated LMDB schemas for type validation
from generated_schemas import (
    OhioSectionDict,
    CitationDataDict,
    ReverseCitationDataDict,
    CitationChainDict,
    CorpusInfoDict,
    ReferenceDetailDict,
    CitingDetailDict
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class SectionMetadata:
    """Complete metadata for a legal section"""
    section_number: str
    url: str
    url_hash: str
    header: str
    title: str
    paragraphs: List[str]
    scraped_date: str
    word_count: int
    paragraph_count: int

    def to_dict(self):
        return asdict(self)


class ComprehensiveLMDBBuilder:
    """Builds multiple LMDB databases with complete legal code data"""

    def __init__(self, data_dir: Path, output_dir: Path = None, enable_enrichment: bool = True):
        self.data_dir = data_dir
        # Use central dist/ folder at project root if provided, otherwise fall back to local
        if output_dir:
            self.lmdb_dir = output_dir
        else:
            self.lmdb_dir = data_dir / "enriched_output" / "comprehensive_lmdb"
        self.lmdb_dir.mkdir(parents=True, exist_ok=True)

        # Input files
        self.corpus_file = data_dir / "ohio_admin_complete_jsonl" / "ohio_admin_code_complete.jsonl"
        self.citation_map_file = data_dir / "citation_analysis" / "citation_map.json"
        self.complex_chains_file = data_dir / "citation_analysis" / "complex_chains.jsonl"
        self.citation_analysis_file = data_dir / "citation_analysis" / "citation_analysis.json"
        self.citation_contexts_file = data_dir / "citation_analysis" / "citation_contexts.jsonl"

        # LMDB environments
        self.sections_db = None
        self.citations_db = None
        self.chains_db = None
        self.metadata_db = None
        self.reverse_citations_db = None

        # In-memory data
        self.citation_map: Dict[str, List[str]] = {}
        self.chains_map: Dict[str, Dict] = {}
        self.sections_data: Dict[str, OhioSectionDict] = {}
        self.citation_contexts_map: Dict[str, List[Dict]] = {}  # Enhanced citation contexts
        self.reverse_citation_map: Dict[str, Set[str]] = {}  # Reverse citations (who cites this)

        # Auto-enrichment
        self.enable_enrichment = enable_enrichment
        self.enricher = AutoEnricher() if enable_enrichment else None
        if enable_enrichment:
            logger.info("🎨 Auto-enrichment ENABLED - metadata will be added to sections")

    def open_databases(self):
        """Open all LMDB databases"""
        logger.info("Opening LMDB databases...")

        # Each database gets 2GB max size
        map_size = 2 * 1024 * 1024 * 1024

        self.sections_db = lmdb.open(
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

        logger.info("All databases opened successfully")

    def close_databases(self):
        """Close all LMDB databases"""
        for db in [self.sections_db, self.citations_db, self.chains_db,
                   self.metadata_db, self.reverse_citations_db]:
            if db:
                db.close()
        logger.info("All databases closed")

    def load_citation_data(self):
        """Load all citation analysis data into memory"""
        logger.info("Loading citation data...")

        # Load citation map
        if self.citation_map_file.exists():
            with open(self.citation_map_file, 'r') as f:
                self.citation_map = json.load(f)
            logger.info(f"Loaded citation map with {len(self.citation_map)} entries")

            # Build reverse citation map immediately for is_clickable calculation
            for section, references in self.citation_map.items():
                for ref in references:
                    if ref not in self.reverse_citation_map:
                        self.reverse_citation_map[ref] = set()
                    self.reverse_citation_map[ref].add(section)
            logger.info(f"Built reverse citation map: {len(self.reverse_citation_map)} entries")

        # Load complex chains
        if self.complex_chains_file.exists():
            with open(self.complex_chains_file, 'r') as f:
                for line in f:
                    chain = json.loads(line)
                    self.chains_map[chain['chain_id']] = chain
            logger.info(f"Loaded {len(self.chains_map)} complex chains")

        # Load citation contexts (enhanced)
        if self.citation_contexts_file.exists():
            with open(self.citation_contexts_file, 'r') as f:
                for line in f:
                    context_record = json.loads(line)
                    section_num = context_record['source_section']
                    self.citation_contexts_map[section_num] = context_record['citations']
            logger.info(f"Loaded enhanced citation contexts for {len(self.citation_contexts_map)} sections")

    def build_sections_database(self):
        """Build main sections database with full metadata"""
        logger.info("Building sections database...")

        sections_count = 0

        with self.sections_db.begin(write=True) as txn:
            with open(self.corpus_file, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    doc = json.loads(line)
                    header = doc.get('header', '')

                    if '|' not in header:
                        logger.warning(f"Skipping line {line_num}: Invalid header format")
                        continue

                    # Parse header - format: "Section 2913.02|Title" or "2913.02|Title"
                    header_parts = header.split('|')
                    section_num = header_parts[0].replace('Section ', '').replace('Rule ', '').strip()
                    section_title = header_parts[1].strip() if len(header_parts) > 1 else ''
                    paragraphs = doc.get('paragraphs', [])

                    # Check if section has graph data (for UI clickability)
                    has_forward_citations = section_num in self.citation_map
                    has_reverse_citations = section_num in self.reverse_citation_map
                    is_clickable = has_forward_citations or has_reverse_citations

                    # Build complete section record (type-validated with OhioSectionDict)
                    section_data: OhioSectionDict = {
                        'section_number': section_num,
                        'url': doc.get('url', ''),
                        'url_hash': doc.get('url_hash', ''),
                        'header': header,
                        'section_title': section_title,
                        'paragraphs': paragraphs,  # PRESERVED - exact legal text
                        'full_text': '\n'.join(paragraphs),
                        'word_count': sum(len(p.split()) for p in paragraphs),
                        'paragraph_count': len(paragraphs),
                        'has_citations': has_forward_citations,
                        'citation_count': len(self.citation_map.get(section_num, [])),
                        'in_complex_chain': section_num in self.chains_map,
                        'is_clickable': is_clickable,  # For graph visualization
                        'scraped_date': datetime.now().isoformat(),
                        # Graph metrics (will be computed later - for now set as empty)
                        # 'treatment_status': None,
                        # 'authority_score': None,
                        # 'betweenness_centrality': None,
                        # 'citation_velocity': None,
                        # 'court_level': None,
                        # 'binding_on': None,
                        # 'precedent_value': None,
                    }

                    # AUTO-ENRICH: Add metadata without touching legal text
                    if self.enable_enrichment and self.enricher:
                        citation_count = len(self.citation_map.get(section_num, []))
                        section_data = cast(OhioSectionDict, self.enricher.enrich_section(cast(Dict, section_data), citation_count))

                    # Store in memory for later use
                    self.sections_data[section_num] = section_data

                    # Store in LMDB
                    key = section_num.encode()
                    value = json.dumps(section_data, ensure_ascii=False).encode()
                    txn.put(key, value)

                    sections_count += 1

                    if sections_count % 1000 == 0:
                        logger.info(f"Processed {sections_count} sections...")

        logger.info(f"Sections database built: {sections_count} sections")
        return sections_count

    def build_citations_database(self):
        """Build citations database with enhanced relationship types and context"""
        logger.info("Building enhanced citations database...")

        citations_count = 0

        with self.citations_db.begin(write=True) as txn:
            for section_num, references in self.citation_map.items():
                # Type-validated with CitationDataDict
                citation_data: CitationDataDict = {
                    'section': section_num,
                    'direct_references': references,
                    'reference_count': len(references),
                    'references_details': []
                }

                # Get enhanced citation contexts if available
                enhanced_citations = self.citation_contexts_map.get(section_num, [])

                # Build a map of target -> enhanced citation info
                enhanced_map = {}
                for citation in enhanced_citations:
                    target = citation['target']
                    enhanced_map[target] = citation

                # Add details for each referenced section
                for ref in references:
                    # Get enhanced citation info if available
                    if ref in enhanced_map:
                        enhanced_info = enhanced_map[ref]
                        relationship = enhanced_info.get('relationship', 'cross_reference')
                        context = enhanced_info.get('context', '')[:100]  # Limit to 100 chars
                        position = enhanced_info.get('position', 0)
                    else:
                        # Fallback for citations without enhanced data
                        relationship = 'cross_reference'
                        context = ''
                        position = 0

                    # Get section metadata
                    title = ''
                    url = ''
                    url_hash = ''
                    if ref in self.sections_data:
                        ref_data = self.sections_data[ref]
                        title = ref_data.get('section_title', '')
                        url = ref_data.get('url', '')
                        url_hash = ref_data.get('url_hash', '')

                    # Type-validated with ReferenceDetailDict
                    detail: ReferenceDetailDict = {
                        'section': ref,
                        'title': title,
                        'url': url,
                        'url_hash': url_hash,
                        'relationship': relationship,
                        'context': context,
                        'position': position
                    }

                    citation_data['references_details'].append(detail)

                key = section_num.encode()
                value = json.dumps(citation_data, ensure_ascii=False).encode()
                txn.put(key, value)
                citations_count += 1

        logger.info(f"Enhanced citations database built: {citations_count} entries")
        return citations_count

    def build_reverse_citations_database(self):
        """Build reverse citations database (what cites this section)"""
        logger.info("Building reverse citations database...")

        # Build reverse map
        reverse_map: Dict[str, Set[str]] = {}

        for section, references in self.citation_map.items():
            for ref in references:
                if ref not in reverse_map:
                    reverse_map[ref] = set()
                reverse_map[ref].add(section)

        reverse_count = 0

        with self.reverse_citations_db.begin(write=True) as txn:
            for section_num, citing_sections in reverse_map.items():
                # Type-validated with ReverseCitationDataDict
                reverse_data: ReverseCitationDataDict = {
                    'section': section_num,
                    'cited_by': sorted(list(citing_sections)),
                    'cited_by_count': len(citing_sections),
                    'citing_details': []
                }

                # Add details for citing sections
                for citing in sorted(citing_sections):
                    if citing in self.sections_data:
                        citing_data = self.sections_data[citing]
                        # Type-validated with CitingDetailDict
                        citing_detail: CitingDetailDict = {
                            'section': citing,
                            'title': citing_data.get('section_title', ''),
                            'url': citing_data.get('url', '')
                        }
                        reverse_data['citing_details'].append(citing_detail)

                key = section_num.encode()
                value = json.dumps(reverse_data, ensure_ascii=False).encode()
                txn.put(key, value)
                reverse_count += 1

        logger.info(f"Reverse citations database built: {reverse_count} entries")
        return reverse_count

    def build_chains_database(self):
        """Build complex chains database with full text"""
        logger.info("Building chains database...")

        chains_count = 0

        with self.chains_db.begin(write=True) as txn:
            for chain_id, chain_data in self.chains_map.items():
                # Type-validated with CitationChainDict
                enhanced_chain: CitationChainDict = {
                    'chain_id': chain_id,
                    'primary_section': chain_data['primary_section'],
                    'chain_sections': chain_data['chain_sections'],
                    'chain_depth': chain_data.get('estimated_complexity', len(chain_data['chain_sections'])),
                    'references_count': len(chain_data['chain_sections']),
                    'created_at': chain_data.get('created_at', ''),
                    'complete_chain': []  # Array of section objects
                }

                # Add full data for each section in chain
                for section in chain_data['chain_sections']:
                    if section in self.sections_data:
                        section_data = self.sections_data[section]
                        enhanced_chain['complete_chain'].append({
                            'section': section,
                            'title': section_data.get('section_title', ''),
                            'url': section_data.get('url', ''),
                            'url_hash': section_data.get('url_hash', ''),
                            'full_text': section_data.get('full_text', ''),
                            'word_count': section_data.get('word_count', 0)
                        })

                key = chain_id.encode()
                value = json.dumps(enhanced_chain, ensure_ascii=False).encode()
                txn.put(key, value)
                chains_count += 1

                if chains_count % 1000 == 0:
                    logger.info(f"Processed {chains_count} chains...")

        logger.info(f"Chains database built: {chains_count} chains")
        return chains_count

    def calculate_inbound_counts(self):
        """
        Calculate how many times each statute is cited by others
        Store in metadata_db as "inbound_count_{section}"
        """
        logger.info("Calculating inbound citation counts...")

        inbound_counts = {}

        # Count how many times each section is referenced
        with self.citations_db.begin() as txn:
            cursor = txn.cursor()
            for key, value in cursor:
                citation_data = json.loads(value.decode())

                for ref in citation_data['direct_references']:
                    if ref not in inbound_counts:
                        inbound_counts[ref] = 0
                    inbound_counts[ref] += 1

        # Store inbound counts in metadata
        with self.metadata_db.begin(write=True) as txn:
            for section, count in inbound_counts.items():
                txn.put(
                    f"inbound_count_{section}".encode(),
                    json.dumps({"section": section, "count": count}).encode()
                )

        logger.info(f"Inbound citation counts calculated for {len(inbound_counts)} sections")
        return len(inbound_counts)

    def build_metadata_database(self, sections_count: int, citations_count: int,
                                chains_count: int, reverse_count: int):
        """Build metadata database with corpus information"""
        logger.info("Building metadata database...")

        with self.metadata_db.begin(write=True) as txn:
            # Corpus-level metadata (type-validated with CorpusInfoDict)
            corpus_meta: CorpusInfoDict = {
                'total_sections': sections_count,
                'sections_with_citations': citations_count,
                'complex_chains': chains_count,
                'reverse_citations': reverse_count,
                'build_date': datetime.now().isoformat(),
                'source': 'https://codes.ohio.gov/ohio-administrative-code',
                'version': '2.0',
                'builder': 'comprehensive_lmdb_builder',
                'databases': ['primary', 'citations', 'reverse_citations', 'chains', 'metadata']
            }

            txn.put(b'corpus_info', json.dumps(corpus_meta, indent=2).encode())

            # Per-section metadata
            for section_num, section_data in self.sections_data.items():
                meta_key = f"section_{section_num}_meta".encode()
                meta_value = {
                    'section': section_num,
                    'url_hash': section_data.get('url_hash', ''),
                    'url': section_data.get('url', ''),
                    'scraped_date': section_data.get('scraped_date', ''),
                    'word_count': section_data.get('word_count', 0),
                    'has_citations': section_data.get('has_citations', False),
                    'citation_count': section_data.get('citation_count', 0),
                    'in_complex_chain': section_data.get('in_complex_chain', False)
                }
                txn.put(meta_key, json.dumps(meta_value).encode())

        logger.info("Metadata database built")

    def build_all(self):
        """Build all databases"""
        logger.info("="*60)
        logger.info("Starting comprehensive LMDB build")
        logger.info("="*60)

        try:
            # Open databases
            self.open_databases()

            # Load citation data
            self.load_citation_data()

            # Build each database
            sections_count = self.build_sections_database()
            citations_count = self.build_citations_database()
            reverse_count = self.build_reverse_citations_database()
            chains_count = self.build_chains_database()
            self.build_metadata_database(sections_count, citations_count,
                                        chains_count, reverse_count)

            # Calculate inbound citation counts
            inbound_count = self.calculate_inbound_counts()

            logger.info("="*60)
            logger.info("Build Summary:")
            logger.info(f"  Sections: {sections_count}")
            logger.info(f"  Citations: {citations_count}")
            logger.info(f"  Reverse Citations: {reverse_count}")
            logger.info(f"  Complex Chains: {chains_count}")
            logger.info(f"  Inbound Citation Counts: {inbound_count}")
            logger.info(f"  Output: {self.lmdb_dir}")
            logger.info("="*60)

        finally:
            self.close_databases()


if __name__ == "__main__":
    from pathlib import Path

    # Use relative path from lmdb/ to data/
    DATA_DIR = Path(__file__).parent.parent / "data"

    # Output to central dist/ folder at project root
    PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
    DIST_DIR = PROJECT_ROOT / "dist" / "ohio_admin"

    print(f"DATA_DIR: {DATA_DIR}")
    print(f"OUTPUT_DIR: {DIST_DIR}")
    print(f"Checking required files...")

    # Verify files exist
    corpus_file = DATA_DIR / "ohio_admin_complete_jsonl" / "ohio_admin_code_complete.jsonl"
    citation_map = DATA_DIR / "citation_analysis" / "citation_map.json"
    chains_file = DATA_DIR / "citation_analysis" / "complex_chains.jsonl"

    if not corpus_file.exists():
        print(f"ERROR: Corpus file not found: {corpus_file}")
        exit(1)
    if not citation_map.exists():
        print(f"ERROR: Citation map not found: {citation_map}")
        exit(1)
    if not chains_file.exists():
        print(f"ERROR: Chains file not found: {chains_file}")
        exit(1)

    print("✓ All required files found")

    builder = ComprehensiveLMDBBuilder(DATA_DIR, output_dir=DIST_DIR)
    builder.build_all()