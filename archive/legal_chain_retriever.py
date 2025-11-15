#!/usr/bin/env python3
"""
Legal Chain Retriever
Retrieves complete citation chains with full context for LLM processing
"""

import json
import lmdb
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class SectionContext:
    """Complete context for a legal section"""
    section: str
    title: str
    url: str
    url_hash: str
    full_text: str
    word_count: int
    direct_citations: List[str]
    cited_by: List[str]
    chain_depth: int
    chain_sections: List[str]


class LegalChainRetriever:
    """Retrieves complete citation chains with full context"""

    def __init__(self, lmdb_dir: Path):
        self.lmdb_dir = lmdb_dir

        # Open all databases in read-only mode
        self.sections_db = lmdb.open(str(lmdb_dir / "sections.lmdb"), readonly=True)
        self.citations_db = lmdb.open(str(lmdb_dir / "citations.lmdb"), readonly=True)
        self.chains_db = lmdb.open(str(lmdb_dir / "chains.lmdb"), readonly=True)
        self.metadata_db = lmdb.open(str(lmdb_dir / "metadata.lmdb"), readonly=True)
        self.reverse_citations_db = lmdb.open(str(lmdb_dir / "reverse_citations.lmdb"), readonly=True)

        logger.info("Legal Chain Retriever initialized")

    def close(self):
        """Close all database connections"""
        for db in [self.sections_db, self.citations_db, self.chains_db,
                   self.metadata_db, self.reverse_citations_db]:
            if db:
                db.close()

    def get_section(self, section_number: str) -> Optional[Dict]:
        """Get complete section data"""
        with self.sections_db.begin() as txn:
            data = txn.get(section_number.encode())
            if data:
                return json.loads(data.decode())
        return None

    def get_citations(self, section_number: str) -> Optional[Dict]:
        """Get forward citations for a section"""
        with self.citations_db.begin() as txn:
            data = txn.get(section_number.encode())
            if data:
                return json.loads(data.decode())
        return None

    def get_reverse_citations(self, section_number: str) -> Optional[Dict]:
        """Get reverse citations (what cites this section)"""
        with self.reverse_citations_db.begin() as txn:
            data = txn.get(section_number.encode())
            if data:
                return json.loads(data.decode())
        return None

    def get_chain(self, section_number: str) -> Optional[Dict]:
        """Get complete citation chain for a section"""
        with self.chains_db.begin() as txn:
            data = txn.get(section_number.encode())
            if data:
                return json.loads(data.decode())
        return None

    def get_metadata(self, key: str = "corpus_info") -> Optional[Dict]:
        """Get metadata"""
        with self.metadata_db.begin() as txn:
            data = txn.get(key.encode())
            if data:
                return json.loads(data.decode())
        return None

    def get_complete_context(self, section_number: str,
                           include_chain: bool = True,
                           include_reverse: bool = True,
                           max_chain_depth: int = 5) -> Optional[Dict]:
        """
        Get complete context for a section including:
        - Full section text
        - Direct citations
        - Reverse citations
        - Complete citation chain with full text
        """
        # Get main section
        section = self.get_section(section_number)
        if not section:
            logger.warning(f"Section {section_number} not found")
            return None

        context = {
            'primary_section': {
                'section': section_number,
                'title': section.get('section_title', ''),
                'url': section.get('url', ''),
                'url_hash': section.get('url_hash', ''),
                'full_text': section.get('full_text', ''),
                'word_count': section.get('word_count', 0),
                'paragraph_count': section.get('paragraph_count', 0)
            },
            'direct_citations': [],
            'reverse_citations': [],
            'citation_chain': [],
            'total_context_words': section.get('word_count', 0),
            'sources': []
        }

        # Add source info
        context['sources'].append({
            'section': section_number,
            'url': section.get('url', ''),
            'url_hash': section.get('url_hash', ''),
            'verified_date': section.get('scraped_date', '')
        })

        # Get direct citations
        citations = self.get_citations(section_number)
        if citations:
            for ref_detail in citations.get('references_details', []):
                ref_section = self.get_section(ref_detail['section'])
                if ref_section:
                    citation_data = {
                        'section': ref_detail['section'],
                        'title': ref_section.get('section_title', ''),
                        'url': ref_section.get('url', ''),
                        'url_hash': ref_section.get('url_hash', ''),
                        'full_text': ref_section.get('full_text', ''),
                        'word_count': ref_section.get('word_count', 0)
                    }
                    context['direct_citations'].append(citation_data)
                    context['total_context_words'] += ref_section.get('word_count', 0)
                    context['sources'].append({
                        'section': ref_detail['section'],
                        'url': ref_section.get('url', ''),
                        'url_hash': ref_section.get('url_hash', ''),
                        'verified_date': ref_section.get('scraped_date', '')
                    })

        # Get reverse citations if requested
        if include_reverse:
            reverse = self.get_reverse_citations(section_number)
            if reverse:
                for citing_detail in reverse.get('citing_details', []):
                    citing_section = self.get_section(citing_detail['section'])
                    if citing_section:
                        context['reverse_citations'].append({
                            'section': citing_detail['section'],
                            'title': citing_section.get('section_title', ''),
                            'url': citing_section.get('url', ''),
                            'url_hash': citing_section.get('url_hash', '')
                        })

        # Get complete chain if requested
        if include_chain:
            chain = self.get_chain(section_number)
            if chain:
                # Limit chain depth
                chain_sections = chain.get('complete_chain', [])[:max_chain_depth]
                context['citation_chain'] = chain_sections
                context['chain_depth'] = len(chain_sections)

                # Add to total context
                for chain_item in chain_sections:
                    if chain_item['section'] != section_number:  # Don't double count
                        context['total_context_words'] += chain_item.get('word_count', 0)

        return context

    def search_sections_by_keyword(self, keyword: str, max_results: int = 10) -> List[Dict]:
        """Search sections by keyword in title or text"""
        results = []
        keyword_lower = keyword.lower()

        with self.sections_db.begin() as txn:
            cursor = txn.cursor()
            for key, value in cursor:
                section_data = json.loads(value.decode())

                # Search in title and text
                title = section_data.get('section_title', '').lower()
                text = section_data.get('full_text', '').lower()

                if keyword_lower in title or keyword_lower in text:
                    results.append({
                        'section': section_data['section_number'],
                        'title': section_data.get('section_title', ''),
                        'url': section_data.get('url', ''),
                        'relevance': 'title' if keyword_lower in title else 'text',
                        'preview': section_data.get('full_text', '')[:200] + '...'
                    })

                    if len(results) >= max_results:
                        break

        return results

    def get_most_cited_sections(self, limit: int = 10) -> List[Dict]:
        """Get the most frequently cited sections"""
        citation_counts = []

        with self.reverse_citations_db.begin() as txn:
            cursor = txn.cursor()
            for key, value in cursor:
                reverse_data = json.loads(value.decode())
                section = reverse_data['section']
                count = reverse_data['cited_by_count']

                section_data = self.get_section(section)
                if section_data:
                    citation_counts.append({
                        'section': section,
                        'title': section_data.get('section_title', ''),
                        'cited_by_count': count,
                        'url': section_data.get('url', '')
                    })

        # Sort by citation count
        citation_counts.sort(key=lambda x: x['cited_by_count'], reverse=True)
        return citation_counts[:limit]

    def get_related_sections(self, section_number: str, max_related: int = 5) -> List[Dict]:
        """
        Get related sections based on:
        1. Direct citations
        2. Reverse citations
        3. Shared chain membership
        """
        related = []
        seen = {section_number}

        # Add direct citations
        citations = self.get_citations(section_number)
        if citations:
            for ref in citations.get('direct_references', [])[:max_related]:
                if ref not in seen:
                    section_data = self.get_section(ref)
                    if section_data:
                        related.append({
                            'section': ref,
                            'title': section_data.get('section_title', ''),
                            'relationship': 'cited_by_primary',
                            'url': section_data.get('url', '')
                        })
                        seen.add(ref)

        # Add reverse citations
        reverse = self.get_reverse_citations(section_number)
        if reverse and len(related) < max_related:
            for citing in reverse.get('cited_by', [])[:max_related - len(related)]:
                if citing not in seen:
                    section_data = self.get_section(citing)
                    if section_data:
                        related.append({
                            'section': citing,
                            'title': section_data.get('section_title', ''),
                            'relationship': 'cites_primary',
                            'url': section_data.get('url', '')
                        })
                        seen.add(citing)

        return related[:max_related]

    def build_llm_context(self, section_number: str,
                         include_chain: bool = True,
                         include_citations: bool = True,
                         max_chain_depth: int = 3) -> str:
        """
        Build formatted context string for LLM with full provenance
        """
        context = self.get_complete_context(
            section_number,
            include_chain=include_chain,
            max_chain_depth=max_chain_depth
        )

        if not context:
            return f"Section {section_number} not found in database."

        # Build formatted context
        output = []

        # Header
        output.append("="*80)
        output.append(f"OHIO REVISED CODE - SECTION {section_number}")
        output.append("="*80)

        # Primary section
        primary = context['primary_section']
        output.append(f"\n📋 PRIMARY SECTION: {primary['section']}")
        output.append(f"Title: {primary['title']}")
        output.append(f"Source: {primary['url']}")
        output.append(f"Hash: {primary['url_hash']}")
        output.append(f"\n{primary['full_text']}\n")

        # Direct citations
        if include_citations and context['direct_citations']:
            output.append("\n" + "="*80)
            output.append(f"📎 SECTIONS CITED BY {section_number} ({len(context['direct_citations'])} sections)")
            output.append("="*80)

            for i, citation in enumerate(context['direct_citations'], 1):
                output.append(f"\n[Citation {i}] Section {citation['section']}")
                output.append(f"Title: {citation['title']}")
                output.append(f"Source: {citation['url']} (Hash: {citation['url_hash']})")
                output.append(f"\n{citation['full_text']}\n")

        # Citation chain
        if include_chain and context.get('citation_chain'):
            output.append("\n" + "="*80)
            output.append(f"🔗 COMPLETE CITATION CHAIN (Depth: {context['chain_depth']})")
            output.append("="*80)

            for i, chain_item in enumerate(context['citation_chain'], 1):
                if chain_item['section'] != section_number:  # Skip primary (already shown)
                    output.append(f"\n[Chain {i}] Section {chain_item['section']}")
                    output.append(f"Title: {chain_item['title']}")
                    output.append(f"Source: {chain_item['url']} (Hash: {chain_item['url_hash']})")
                    output.append(f"\n{chain_item['full_text'][:500]}...")  # Truncate for context

        # Reverse citations summary
        if context['reverse_citations']:
            output.append("\n" + "="*80)
            output.append(f"🔙 SECTIONS THAT CITE {section_number} ({len(context['reverse_citations'])} sections)")
            output.append("="*80)
            for rev in context['reverse_citations'][:5]:  # Show first 5
                output.append(f"  • Section {rev['section']}: {rev['title']}")

        # Sources and provenance
        output.append("\n" + "="*80)
        output.append("📚 SOURCE VERIFICATION")
        output.append("="*80)
        for source in context['sources']:
            output.append(f"  • Section {source['section']}")
            output.append(f"    URL: {source['url']}")
            output.append(f"    Hash: {source['url_hash']}")
            output.append(f"    Verified: {source.get('verified_date', 'N/A')}")

        # Statistics
        output.append("\n" + "="*80)
        output.append("📊 CONTEXT STATISTICS")
        output.append("="*80)
        output.append(f"  Total context words: {context['total_context_words']:,}")
        output.append(f"  Direct citations: {len(context['direct_citations'])}")
        output.append(f"  Reverse citations: {len(context['reverse_citations'])}")
        output.append(f"  Chain depth: {context.get('chain_depth', 0)}")
        output.append(f"  Total sections: {len(context['sources'])}")

        return '\n'.join(output)


if __name__ == "__main__":
    from config import DATA_DIR

    lmdb_dir = DATA_DIR / "enriched_output" / "comprehensive_lmdb"
    retriever = LegalChainRetriever(lmdb_dir)

    # Test retrieval
    print("\nTesting Section 101.15 (Public committee meetings):")
    print("="*80)
    context_text = retriever.build_llm_context("101.15", max_chain_depth=3)
    print(context_text)

    retriever.close()