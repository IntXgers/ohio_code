#!/usr/bin/env python3
"""
Citation graph builder for Ohio Constitution corpus
Extracts constitutional section references and builds dependency mappings
"""

import re
import json
import logging
from pathlib import Path
from typing import Dict, Set, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CitationAnalysis:
    """Complete citation analysis results"""
    total_sections: int
    sections_with_references: int
    total_references: int
    avg_references_per_section: float
    max_references: int
    most_referenced_section: str
    isolated_sections: List[str]
    complex_chains: List[List[str]]
    simple_pairs: List[List[str]]
    processing_manifest: Dict[str, List[str]]


class CitationMapper:
    def __init__(self, input_file: str, output_dir: str = "citation_analysis"):
        self.input_file = Path(input_file)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Output files
        self.citation_map_file = self.output_dir / "citation_map.json"
        self.processing_manifest_file = self.output_dir / "processing_manifest.json"
        self.complex_chains_file = self.output_dir / "complex_chains.jsonl"
        self.analysis_report_file = self.output_dir / "citation_analysis.json"
        self.state_file = self.output_dir / "citation_state.json"

        # Reference extraction patterns for Ohio Constitution
        self.reference_patterns = [
            r'Article\s+([IVXLCDM]+),?\s+Section\s+(\d+)',  # Article I, Section 1
            r'Art\.?\s*([IVXLCDM]+)\s*§\s*(\d+)',            # Art. I § 1
            r'section\s+(\d+)\s+of\s+[Aa]rticle\s+([IVXLCDM]+)',  # section 1 of Article I
            r'([IVXLCDM]+)\.(\d+)',                          # I.1 (shorthand)
        ]

        # State management
        self.checkpoint_interval = 1000
        self.last_processed_line = 0
        self.shutdown_requested = False

        # Setup signal handlers
        import signal
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, _signum, _frame):
        """Handle shutdown signals gracefully"""
        logger.info("Shutdown signal received. Saving state...")
        self.shutdown_requested = True
        self._save_state()
        logger.info("Citation mapping state saved.")
        sys.exit(0)

    def _load_state(self):
        """Load previous processing state if exists"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    state_data = json.load(f)
                self.last_processed_line = state_data.get('last_processed_line', 0)
                logger.info(f"Resuming from line {self.last_processed_line + 1}")
                return state_data.get('partial_citation_map', {})
            except Exception as e:
                logger.error(f"Failed to load state: {e}")
        return {}

    def _save_state(self, citation_map: Dict[str, Set[str]] = None):
        """Save current processing state"""
        state_data = {
            'last_processed_line': self.last_processed_line,
            'partial_citation_map': {k: list(v) for k, v in (citation_map or {}).items()},
            'timestamp': datetime.now().isoformat()
        }
        with open(self.state_file, 'w') as f:
            json.dump(state_data, f, indent=2)

    def build_citation_mapping(self) -> Dict[str, Set[str]]:
        """Build complete citation graph from JSONL corpus with resumability"""
        logger.info(f"Building citation mapping from {self.input_file}")

        # Load existing state
        citation_map = {}
        if self.state_file.exists():
            partial_map = self._load_state()
            citation_map = {k: set(v) for k, v in partial_map.items()}

        section_count = len(citation_map)

        with open(self.input_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                # Skip to resume point
                if line_num <= self.last_processed_line:
                    continue

                # Check for shutdown
                if self.shutdown_requested:
                    break

                try:
                    doc = json.loads(line.strip())
                    section_num = self.extract_section_number(doc.get('header', ''))

                    if section_num:
                        # Extract all references from paragraphs
                        full_text = ' '.join(doc.get('paragraphs', []))
                        references = self.extract_cross_references(full_text)

                        citation_map[section_num] = references
                        section_count += 1

                    self.last_processed_line = line_num

                    # Checkpoint periodically
                    if section_count % self.checkpoint_interval == 0:
                        self._save_state(citation_map)
                        logger.info(f"Checkpoint: {section_count} sections processed")

                except json.JSONDecodeError as e:
                    logger.error(f"JSON error at line {line_num}: {e}")
                    self.last_processed_line = line_num
                except Exception as e:
                    logger.error(f"Processing error at line {line_num}: {e}")
                    self.last_processed_line = line_num

        # Final save
        self._save_state(citation_map)
        logger.info(f"Citation mapping complete: {len(citation_map)} sections")
        return citation_map

    @staticmethod
    def extract_section_number(header: str) -> Optional[str]:
        """Extract section number from header - Ohio Constitution format"""
        # Header format: "Article I, Section 1|Inalienable Rights"
        match = re.search(r'Article\s+([IVXLCDM]+),\s+Section\s+(\d+)', header, re.IGNORECASE)
        if match:
            return f"Article {match.group(1).upper()}, Section {match.group(2)}"
        return None

    def extract_cross_references(self, text: str) -> Set[str]:
        """Extract all constitutional section references from text"""
        references = set()

        for pattern in self.reference_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    # Constitutional patterns return tuples like (article, section)
                    article = match[0].upper()
                    section = match[1] if len(match) > 1 else None

                    if section:
                        # Standard format: "Article I, Section 1"
                        ref = f"Article {article}, Section {section}"
                        references.add(ref)
                else:
                    # Single match - shouldn't happen with constitution patterns
                    references.add(match)

        return references

    def analyze_citation_patterns(self, citation_map: Dict[str, Set[str]]) -> CitationAnalysis:
        """Analyze citation patterns and complexity"""
        total_sections = len(citation_map)
        sections_with_refs = sum(1 for refs in citation_map.values() if refs)
        total_references = sum(len(refs) for refs in citation_map.values())

        # Find most referenced sections
        reference_counts = {}
        for refs in citation_map.values():
            for ref in refs:
                reference_counts[ref] = reference_counts.get(ref, 0) + 1

        most_referenced = max(reference_counts.items(), key=lambda x: x[1]) if reference_counts else ("None", 0)
        max_outbound_refs = max(len(refs) for refs in citation_map.values()) if citation_map else 0

        # Categorize sections
        isolated = [s for s, refs in citation_map.items() if not refs]
        simple_pairs = []
        complex_chains = []

        # Build reference chains to identify complexity
        visited_global = set()
        for section, refs in citation_map.items():
            if section not in visited_global and refs:
                chain = self._build_reference_chain(section, citation_map, max_size=8)
                visited_global.update(chain)

                if len(chain) >= 4:
                    complex_chains.append(chain)
                elif len(chain) >= 2:
                    simple_pairs.append(chain)

        # Create processing manifest
        processing_manifest = {
            "isolated_sections": isolated,
            "simple_chains": simple_pairs,
            "complex_chains": complex_chains
        }

        return CitationAnalysis(
            total_sections=total_sections,
            sections_with_references=sections_with_refs,
            total_references=total_references,
            avg_references_per_section=total_references / total_sections if total_sections else 0,
            max_references=max_outbound_refs,
            most_referenced_section=most_referenced[0],
            isolated_sections=isolated,
            complex_chains=complex_chains,
            simple_pairs=simple_pairs,
            processing_manifest=processing_manifest
        )

    @staticmethod
    def _build_reference_chain(start_section: str, citation_map: Dict[str, Set[str]], max_size: int = 8) -> List[
        str]:
        """Build reference chain with cycle detection"""
        chain = []
        visited = set()
        queue = [start_section]

        while queue and len(chain) < max_size:
            current = queue.pop(0)
            if current in visited:
                continue

            chain.append(current)
            visited.add(current)

            # Add references to queue
            refs = citation_map.get(current, set())
            for ref in list(refs)[:3]:  # Limit expansion
                if ref not in visited and ref in citation_map:
                    queue.append(ref)

        return chain

    def save_results(self, citation_map: Dict[str, Set[str]], analysis: CitationAnalysis):
        """Save all analysis results to files"""
        # Save citation mapping
        serializable_map = {k: list(v) for k, v in citation_map.items()}
        with open(self.citation_map_file, 'w') as f:
            json.dump(serializable_map, f, indent=2)
        logger.info(f"Citation map saved to {self.citation_map_file}")

        # Save processing manifest
        with open(self.processing_manifest_file, 'w') as f:
            json.dump(analysis.processing_manifest, f, indent=2)
        logger.info(f"Processing manifest saved to {self.processing_manifest_file}")

        # Save complex chains for frontier processing
        with open(self.complex_chains_file, 'w') as f:
            for i, chain in enumerate(analysis.complex_chains):
                chain_data = {
                    "chain_id": f"complex_{i}",
                    "primary_section": chain[0],
                    "chain_sections": chain,
                    "estimated_complexity": len(chain),
                    "created_at": datetime.now().isoformat()
                }
                f.write(json.dumps(chain_data) + '\n')
        logger.info(f"Complex chains saved to {self.complex_chains_file}")

        # Save analysis report
        with open(self.analysis_report_file, 'w') as f:
            json.dump(asdict(analysis), f, indent=2)
        logger.info(f"Analysis report saved to {self.analysis_report_file}")

    def run_analysis(self):
        """Complete citation analysis pipeline"""
        logger.info("Starting citation analysis pipeline")

        # Build citation mapping
        citation_map = self.build_citation_mapping()

        # Analyze patterns
        analysis = self.analyze_citation_patterns(citation_map)

        # Save results
        self.save_results(citation_map, analysis)

        # Print summary
        self._print_analysis_summary(analysis)

        return citation_map, analysis

    def _print_analysis_summary(self, analysis: CitationAnalysis):
        """Print comprehensive analysis summary"""
        print(f"\n{'=' * 60}")
        print(f"OHIO CONSTITUTION CITATION ANALYSIS")
        print(f"{'=' * 60}")
        print(f"Total sections: {analysis.total_sections:,}")

        if analysis.total_sections > 0:
            print(
                f"Sections with references: {analysis.sections_with_references:,} ({analysis.sections_with_references / analysis.total_sections * 100:.1f}%)")
            print(f"Total cross-references: {analysis.total_references:,}")
            print(f"Average references per section: {analysis.avg_references_per_section:.2f}")
            print(f"Most referenced section: {analysis.most_referenced_section}")
            print(f"\nProcessing Categories:")
            print(
                f"  Isolated sections: {len(analysis.isolated_sections):,} ({len(analysis.isolated_sections) / analysis.total_sections * 100:.1f}%)")
            print(f"  Simple chains: {len(analysis.simple_pairs):,}")
            print(f"  Complex chains: {len(analysis.complex_chains):,}")
            print(f"\nRecommended Processing Strategy:")
            print(f"  Local model: {len(analysis.isolated_sections) + len(analysis.simple_pairs):,} sections")
            print(f"  Frontier model: {sum(len(chain) for chain in analysis.complex_chains):,} sections")
        else:
            print("ERROR: No sections were successfully processed!")
            print("Check input file format and file path.")

        print(f"{'=' * 60}")


if __name__ == "__main__":
    # Configuration
    from pathlib import Path

    # Paths for Ohio Constitution
    base_dir = Path(__file__).parent.parent
    input_file = base_dir / "data" / "scraped_constitution" / "ohio_constitution_complete.jsonl"
    output_dir = base_dir / "data" / "citation_analysis"

    mapper = CitationMapper(
        input_file=str(input_file),
        output_dir=str(output_dir)
    )

    citation_map, analysis = mapper.run_analysis()

    # Print actionable recommendations
    print(f"\nNext Steps:")
    print(f"1. Review {mapper.processing_manifest_file} for processing groups")
    print(f"2. Process {len(analysis.isolated_sections + analysis.simple_pairs):,} sections with local enricher")
    print(f"3. Process {len(analysis.complex_chains):,} complex chains with frontier model")
    print(f"4. Estimated frontier model cost: ${len(analysis.complex_chains) * 0.05:.2f}")