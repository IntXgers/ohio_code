#!/usr/bin/env python3
"""
Test suite for the comprehensive legal query system
Tests LMDB databases, retrieval, and query processing
"""

import json
import logging
from pathlib import Path
from legal_chain_retriever import LegalChainRetriever
from legal_query_processor import LegalQueryProcessor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LegalSystemTester:
    """Comprehensive test suite for legal query system"""

    def __init__(self, lmdb_dir: Path, model_path: Path):
        self.lmdb_dir = lmdb_dir
        self.model_path = model_path
        self.retriever = None
        self.processor = None
        self.test_results = []

    def setup(self):
        """Initialize retriever and processor"""
        logger.info("Setting up test environment...")
        self.retriever = LegalChainRetriever(self.lmdb_dir)
        self.processor = LegalQueryProcessor(self.model_path, self.lmdb_dir)
        logger.info("Test environment ready")

    def teardown(self):
        """Clean up resources"""
        if self.retriever:
            self.retriever.close()
        if self.processor:
            self.processor.close()

    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log test result"""
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{status}: {test_name}")
        if details:
            logger.info(f"  Details: {details}")

        self.test_results.append({
            'test': test_name,
            'passed': passed,
            'details': details
        })

    def test_database_integrity(self):
        """Test that all databases are accessible and have data"""
        logger.info("\n" + "="*80)
        logger.info("TEST SUITE 1: Database Integrity")
        logger.info("="*80)

        # Test metadata
        metadata = self.retriever.get_metadata("corpus_info")
        self.log_test(
            "Corpus metadata exists",
            metadata is not None,
            f"Total sections: {metadata.get('total_sections', 0) if metadata else 0}"
        )

        # Test section retrieval
        section = self.retriever.get_section("101.15")
        self.log_test(
            "Section retrieval works",
            section is not None and 'url_hash' in section,
            f"Found section with {section.get('word_count', 0) if section else 0} words"
        )

        # Test citations
        citations = self.retriever.get_citations("101.15")
        self.log_test(
            "Citations database works",
            citations is not None,
            f"Found {len(citations.get('direct_references', [])) if citations else 0} citations"
        )

        # Test reverse citations
        reverse = self.retriever.get_reverse_citations("101.15")
        self.log_test(
            "Reverse citations database works",
            reverse is not None,
            f"Cited by {reverse.get('cited_by_count', 0) if reverse else 0} sections"
        )

        # Test chains
        chain = self.retriever.get_chain("101.15")
        self.log_test(
            "Chains database works",
            chain is not None,
            f"Chain depth: {chain.get('chain_depth', 0) if chain else 0}"
        )

    def test_data_completeness(self):
        """Test that critical fields are present"""
        logger.info("\n" + "="*80)
        logger.info("TEST SUITE 2: Data Completeness")
        logger.info("="*80)

        section = self.retriever.get_section("101.15")

        if section:
            # Check required fields
            required_fields = ['section_number', 'url', 'url_hash', 'full_text',
                             'word_count', 'paragraphs']

            for field in required_fields:
                self.log_test(
                    f"Section has field: {field}",
                    field in section and section[field],
                    f"Value: {str(section.get(field, 'MISSING'))[:50]}..."
                )

            # Check url_hash format
            url_hash = section.get('url_hash', '')
            self.log_test(
                "url_hash has correct format",
                len(url_hash) == 16,
                f"Hash: {url_hash}"
            )

    def test_citation_chain_integrity(self):
        """Test that citation chains are complete"""
        logger.info("\n" + "="*80)
        logger.info("TEST SUITE 3: Citation Chain Integrity")
        logger.info("="*80)

        chain = self.retriever.get_chain("101.15")

        if chain:
            # Check chain has complete data
            self.log_test(
                "Chain has complete_chain field",
                'complete_chain' in chain,
                f"Chain sections: {len(chain.get('complete_chain', []))}"
            )

            # Verify each chain item has full text
            complete_chain = chain.get('complete_chain', [])
            if complete_chain:
                first_item = complete_chain[0]
                required_fields = ['section', 'title', 'url', 'url_hash', 'full_text']

                for field in required_fields:
                    self.log_test(
                        f"Chain items have field: {field}",
                        field in first_item,
                        f"Sample: {first_item.get('section', 'N/A')}"
                    )

    def test_context_retrieval(self):
        """Test complete context retrieval"""
        logger.info("\n" + "="*80)
        logger.info("TEST SUITE 4: Context Retrieval")
        logger.info("="*80)

        context = self.retriever.get_complete_context("101.15", include_chain=True)

        if context:
            self.log_test(
                "Complete context retrieval works",
                'primary_section' in context,
                f"Context words: {context.get('total_context_words', 0):,}"
            )

            self.log_test(
                "Context includes sources",
                len(context.get('sources', [])) > 0,
                f"Sources: {len(context.get('sources', []))}"
            )

            self.log_test(
                "Context includes provenance",
                all('url_hash' in s for s in context.get('sources', [])),
                "All sources have url_hash"
            )

    def test_search_functionality(self):
        """Test keyword search"""
        logger.info("\n" + "="*80)
        logger.info("TEST SUITE 5: Search Functionality")
        logger.info("="*80)

        # Search for common legal term
        results = self.retriever.search_sections_by_keyword("penalty", max_results=5)

        self.log_test(
            "Keyword search returns results",
            len(results) > 0,
            f"Found {len(results)} sections"
        )

        if results:
            self.log_test(
                "Search results have required fields",
                all('section' in r and 'url' in r for r in results),
                f"First result: Section {results[0].get('section', 'N/A')}"
            )

    def test_most_cited(self):
        """Test most cited sections retrieval"""
        logger.info("\n" + "="*80)
        logger.info("TEST SUITE 6: Most Cited Sections")
        logger.info("="*80)

        most_cited = self.retriever.get_most_cited_sections(limit=5)

        self.log_test(
            "Most cited sections retrieval works",
            len(most_cited) > 0,
            f"Found {len(most_cited)} highly cited sections"
        )

        if most_cited:
            top = most_cited[0]
            self.log_test(
                "Most cited section has citation count",
                'cited_by_count' in top,
                f"Top: Section {top.get('section', 'N/A')} "
                f"cited {top.get('cited_by_count', 0)} times"
            )

    def test_llm_context_building(self):
        """Test LLM context string building"""
        logger.info("\n" + "="*80)
        logger.info("TEST SUITE 7: LLM Context Building")
        logger.info("="*80)

        context_text = self.retriever.build_llm_context("101.15", max_chain_depth=2)

        self.log_test(
            "LLM context string is generated",
            len(context_text) > 0,
            f"Context length: {len(context_text):,} characters"
        )

        # Check for required sections in context
        required_sections = [
            "OHIO REVISED CODE",
            "PRIMARY SECTION",
            "SOURCE VERIFICATION",
            "url_hash",
            "CONTEXT STATISTICS"
        ]

        for section in required_sections:
            self.log_test(
                f"Context includes: {section}",
                section in context_text,
                "Found in output"
            )

    def test_query_processing(self):
        """Test actual query processing with LLM"""
        logger.info("\n" + "="*80)
        logger.info("TEST SUITE 8: Query Processing (LLM)")
        logger.info("="*80)

        result = self.processor.query_section(
            "101.15",
            "What are the requirements for public committee meetings?",
            include_chain=True,
            max_chain_depth=2
        )

        self.log_test(
            "Query processing returns result",
            'answer' in result,
            f"Answer length: {len(result.get('answer', ''))} characters"
        )

        self.log_test(
            "Result includes context stats",
            'context_stats' in result,
            f"Context words: {result.get('context_stats', {}).get('total_context_words', 0):,}"
        )

        self.log_test(
            "Result includes sources with url_hash",
            all('url_hash' in s for s in result.get('sources', [])),
            f"Sources: {len(result.get('sources', []))}"
        )

        # Display sample answer
        logger.info("\nSample Answer:")
        logger.info("-" * 80)
        logger.info(result.get('answer', 'No answer')[:500] + "...")

    def test_relationship_analysis(self):
        """Test section relationship analysis"""
        logger.info("\n" + "="*80)
        logger.info("TEST SUITE 9: Relationship Analysis")
        logger.info("="*80)

        related = self.retriever.get_related_sections("101.15", max_related=5)

        self.log_test(
            "Related sections retrieval works",
            len(related) > 0,
            f"Found {len(related)} related sections"
        )

        if related:
            self.log_test(
                "Related sections have relationship type",
                all('relationship' in r for r in related),
                f"Relationships: {', '.join(set(r['relationship'] for r in related))}"
            )

    def test_comparison(self):
        """Test section comparison"""
        logger.info("\n" + "="*80)
        logger.info("TEST SUITE 10: Section Comparison")
        logger.info("="*80)

        # Compare two related sections
        result = self.processor.compare_sections("101.15", "101.34")

        self.log_test(
            "Section comparison works",
            'analysis' in result,
            f"Relationship: {result.get('relationship', 'Unknown')}"
        )

        self.log_test(
            "Comparison includes url_hash for both sections",
            'url_hash' in result.get('section1', {}) and
            'url_hash' in result.get('section2', {}),
            "Provenance maintained"
        )

    def run_all_tests(self):
        """Run complete test suite"""
        logger.info("\n" + "="*80)
        logger.info("COMPREHENSIVE LEGAL SYSTEM TEST SUITE")
        logger.info("="*80)

        try:
            self.setup()

            # Run all tests
            self.test_database_integrity()
            self.test_data_completeness()
            self.test_citation_chain_integrity()
            self.test_context_retrieval()
            self.test_search_functionality()
            self.test_most_cited()
            self.test_llm_context_building()
            self.test_query_processing()
            self.test_relationship_analysis()
            self.test_comparison()

            # Summary
            self.print_summary()

        finally:
            self.teardown()

    def print_summary(self):
        """Print test summary"""
        logger.info("\n" + "="*80)
        logger.info("TEST SUMMARY")
        logger.info("="*80)

        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r['passed'])
        failed = total - passed

        logger.info(f"Total tests: {total}")
        logger.info(f"Passed: {passed} ✓")
        logger.info(f"Failed: {failed} ✗")
        logger.info(f"Success rate: {(passed/total*100):.1f}%")

        if failed > 0:
            logger.info("\nFailed tests:")
            for result in self.test_results:
                if not result['passed']:
                    logger.info(f"  ✗ {result['test']}")
                    if result['details']:
                        logger.info(f"    {result['details']}")


if __name__ == "__main__":
    from config import MODEL_PATH, DATA_DIR

    lmdb_dir = DATA_DIR / "enriched_output" / "comprehensive_lmdb"

    # Check if LMDB exists
    if not lmdb_dir.exists():
        logger.error(f"LMDB directory not found: {lmdb_dir}")
        logger.error("Please run build_comprehensive_lmdb.py first")
        exit(1)

    tester = LegalSystemTester(lmdb_dir, MODEL_PATH)
    tester.run_all_tests()
