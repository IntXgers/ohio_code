#!/usr/bin/env python3
"""
Quick Start Script for Comprehensive Legal Query System
Run this after building the LMDB databases
"""

import sys
from pathlib import Path
from legal_chain_retriever import LegalChainRetriever
from legal_query_processor import LegalQueryProcessor

def main():
    print("="*80)
    print("OHIO REVISED CODE - COMPREHENSIVE LEGAL QUERY SYSTEM")
    print("="*80)

    # Import config
    try:
        from config import MODEL_PATH, DATA_DIR
    except ImportError:
        print("Error: Could not import config.py")
        print("Please ensure config.py is in the same directory")
        sys.exit(1)

    lmdb_dir = DATA_DIR / "enriched_output" / "comprehensive_lmdb"

    # Check if LMDB exists
    if not lmdb_dir.exists():
        print(f"\n❌ LMDB databases not found at: {lmdb_dir}")
        print("\nPlease build the databases first:")
        print("  python build_comprehensive_lmdb.py")
        sys.exit(1)

    print(f"\n✓ LMDB databases found at: {lmdb_dir}")

    # Initialize retriever
    print("\nInitializing retriever...")
    retriever = LegalChainRetriever(lmdb_dir)

    # Get corpus info
    metadata = retriever.get_metadata("corpus_info")
    if metadata:
        print(f"\n📊 Corpus Information:")
        print(f"  Total sections: {metadata.get('total_sections', 'N/A'):,}")
        print(f"  Sections with citations: {metadata.get('sections_with_citations', 'N/A'):,}")
        print(f"  Complex chains: {metadata.get('complex_chains', 'N/A'):,}")
        print(f"  Build date: {metadata.get('build_date', 'N/A')}")

    # Demo queries
    print("\n" + "="*80)
    print("DEMONSTRATION QUERIES")
    print("="*80)

    # 1. Simple section lookup
    print("\n1️⃣  SIMPLE SECTION LOOKUP")
    print("-" * 80)
    section = retriever.get_section("101.15")
    if section:
        print(f"Section: {section['section_number']}")
        print(f"Title: {section.get('section_title', 'N/A')}")
        print(f"URL: {section.get('url', 'N/A')}")
        print(f"Hash: {section.get('url_hash', 'N/A')}")
        print(f"Word count: {section.get('word_count', 0):,}")
        print(f"Has citations: {section.get('has_citations', False)}")
        print(f"Citation count: {section.get('citation_count', 0)}")

    # 2. Citation chain
    print("\n2️⃣  CITATION CHAIN")
    print("-" * 80)
    chain = retriever.get_chain("101.15")
    if chain:
        print(f"Primary section: {chain['primary_section']}")
        print(f"Chain depth: {chain['chain_depth']}")
        print(f"Sections in chain:")
        for i, section_num in enumerate(chain['chain_sections'][:5], 1):
            print(f"  {i}. Section {section_num}")
        if len(chain['chain_sections']) > 5:
            print(f"  ... and {len(chain['chain_sections']) - 5} more")

    # 3. Most cited sections
    print("\n3️⃣  MOST CITED SECTIONS")
    print("-" * 80)
    most_cited = retriever.get_most_cited_sections(limit=5)
    for i, section in enumerate(most_cited, 1):
        print(f"{i}. Section {section['section']}: {section['title'][:60]}")
        print(f"   Cited by {section['cited_by_count']} sections")

    # 4. Search
    print("\n4️⃣  KEYWORD SEARCH: 'ethics'")
    print("-" * 80)
    search_results = retriever.search_sections_by_keyword("ethics", max_results=3)
    for i, result in enumerate(search_results, 1):
        print(f"{i}. Section {result['section']}: {result['title']}")
        print(f"   Relevance: {result['relevance']}")

    # 5. LLM Context Example
    print("\n5️⃣  LLM CONTEXT PREVIEW (Section 101.15)")
    print("-" * 80)
    context_text = retriever.build_llm_context("101.15", max_chain_depth=2)
    print(context_text[:800] + "\n... [truncated]")

    # Option to run LLM query
    print("\n" + "="*80)
    print("LLM QUERY PROCESSOR")
    print("="*80)

    response = input("\n❓ Run LLM query example? (requires model, may take 30 seconds) [y/N]: ")

    if response.lower() == 'y':
        print("\nInitializing LLM...")
        try:
            processor = LegalQueryProcessor(MODEL_PATH, lmdb_dir)

            print("\n6️⃣  LLM QUERY EXAMPLE")
            print("-" * 80)
            print("Query: What are the penalties for violating public meeting requirements?")
            print("Section: 101.15")
            print("\nGenerating answer (please wait)...")

            result = processor.query_section(
                "101.15",
                "What are the penalties for violating public meeting requirements?",
                include_chain=True,
                max_chain_depth=2
            )

            print("\n📝 ANSWER:")
            print(result['answer'])

            print("\n📊 CONTEXT STATS:")
            stats = result['context_stats']
            print(f"  Total context words: {stats['total_context_words']:,}")
            print(f"  Direct citations: {stats['direct_citations']}")
            print(f"  Chain depth: {stats['chain_depth']}")
            print(f"  Sources: {stats['sources_count']}")

            print("\n📚 SOURCES:")
            for source in result['sources'][:3]:
                print(f"  • Section {source['section']}")
                print(f"    URL: {source['url']}")
                print(f"    Hash: {source['url_hash']}")

            processor.close()

        except Exception as e:
            print(f"\n❌ Error running LLM query: {e}")
            print("This is normal if the model is not available")

    # Cleanup
    retriever.close()

    print("\n" + "="*80)
    print("QUICK START COMPLETE")
    print("="*80)
    print("\nNext steps:")
    print("  1. Review README.md for full documentation")
    print("  2. Run test_legal_system.py for comprehensive testing")
    print("  3. Use legal_query_processor.py for custom queries")
    print("\nFor interactive queries, see the examples in legal_query_processor.py")
    print("="*80)


if __name__ == "__main__":
    main()