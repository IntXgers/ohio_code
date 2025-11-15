#!/usr/bin/env python3
"""
Legal Query Processor
Processes user queries with full citation chain context and provenance
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from llama_cpp import Llama
from legal_chain_retriever import LegalChainRetriever

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LegalQueryProcessor:
    """Process legal queries with complete citation context"""

    def __init__(self, model_path: Path, lmdb_dir: Path):
        self.model_path = model_path
        self.retriever = LegalChainRetriever(lmdb_dir)

        # Initialize LLM
        logger.info("Loading Llama model...")
        self.model = Llama(
            model_path=str(model_path),
            n_ctx=16384,  # Larger context for full chains
            n_threads=8,
            n_gpu_layers=-1,
            verbose=False,
            seed=42
        )
        logger.info("Model loaded successfully")

    def close(self):
        """Close resources"""
        self.retriever.close()

    def build_legal_prompt(self, query: str, section_number: str,
                          include_chain: bool = True,
                          max_chain_depth: int = 3) -> str:
        """
        Build comprehensive legal prompt with:
        - Full section context
        - Citation chains
        - Source verification
        - Clear instructions for accuracy
        """

        # Get complete context
        context_text = self.retriever.build_llm_context(
            section_number,
            include_chain=include_chain,
            max_chain_depth=max_chain_depth
        )

        prompt = f"""You are a legal research assistant analyzing the Ohio Revised Code. Your task is to provide accurate, well-sourced answers based ONLY on the provided statutory text.

LEGAL CONTEXT PROVIDED:
{context_text}

USER QUESTION:
{query}

INSTRUCTIONS:
1. Answer ONLY based on the statutory text provided above
2. Cite specific section numbers when referencing laws
3. If the answer requires information from cited sections, reference them explicitly
4. Include the url_hash for each section you cite for verification
5. If the information is not in the provided context, state "This information is not specified in the provided sections"
6. For legal relationships, explain how the sections interconnect
7. Always include source verification at the end

ANSWER FORMAT:
[Your detailed answer with section citations]

SOURCES CITED:
[List each section referenced with its url and hash]

LEGAL DISCLAIMER:
[Standard disclaimer about verifying current law]

YOUR ANSWER:"""

        return prompt

    def build_search_prompt(self, query: str, search_results: List[Dict]) -> str:
        """Build prompt for search-based queries"""

        sections_context = []
        for i, result in enumerate(search_results, 1):
            section_data = self.retriever.get_section(result['section'])
            if section_data:
                sections_context.append(f"""
[RESULT {i}] Section {result['section']}
Title: {result['title']}
URL: {result['url']}
Text: {section_data['full_text'][:1000]}...
""")

        prompt = f"""You are a legal research assistant. The user searched for information and these are the relevant sections found.

USER SEARCH QUERY:
{query}

RELEVANT SECTIONS FOUND:
{''.join(sections_context)}

INSTRUCTIONS:
1. Identify which section(s) best answer the user's query
2. Provide specific citations
3. Explain the relevance of each section
4. If multiple sections apply, explain their relationships

YOUR ANSWER:"""

        return prompt

    def build_relationship_prompt(self, section_number: str) -> str:
        """Build prompt to explain legal relationships"""

        context = self.retriever.get_complete_context(section_number, include_chain=True)
        if not context:
            return f"Section {section_number} not found."

        prompt = f"""Analyze the legal relationships for Ohio Revised Code Section {section_number}.

PRIMARY SECTION: {section_number}
Title: {context['primary_section']['title']}

SECTIONS IT CITES: {len(context['direct_citations'])}
{', '.join([c['section'] for c in context['direct_citations']])}

SECTIONS THAT CITE IT: {len(context['reverse_citations'])}
{', '.join([r['section'] for r in context['reverse_citations'][:10]])}

CITATION CHAIN DEPTH: {context.get('chain_depth', 0)}

TASK:
Explain how Section {section_number} fits within the broader legal framework. Describe:
1. What sections it depends on and why
2. What sections depend on it and why
3. The overall legal structure it's part of

YOUR ANALYSIS:"""

        return prompt

    def query_section(self, section_number: str, query: str,
                     include_chain: bool = True,
                     max_chain_depth: int = 3,
                     max_tokens: int = 1000) -> Dict:
        """
        Query a specific section with full context
        """
        logger.info(f"Processing query for section {section_number}")

        # Build prompt
        prompt = self.build_legal_prompt(
            query,
            section_number,
            include_chain=include_chain,
            max_chain_depth=max_chain_depth
        )

        # Generate response
        logger.info("Generating response...")
        response = self.model(
            prompt,
            max_tokens=max_tokens,
            temperature=0.3,  # Lower for more factual
            top_p=0.9,
            stop=["\n\nUSER QUESTION:", "\n\nLEGAL CONTEXT"],
            echo=False
        )

        answer = response['choices'][0]['text'].strip()

        # Get context for response metadata
        context = self.retriever.get_complete_context(section_number)

        return {
            'query': query,
            'section': section_number,
            'answer': answer,
            'context_stats': {
                'total_context_words': context['total_context_words'],
                'direct_citations': len(context['direct_citations']),
                'reverse_citations': len(context['reverse_citations']),
                'chain_depth': context.get('chain_depth', 0),
                'sources_count': len(context['sources'])
            },
            'sources': context['sources'],
            'model_params': {
                'max_tokens': max_tokens,
                'temperature': 0.3,
                'model': 'Meta-Llama-3.1-8B-Instruct'
            }
        }

    def search_and_query(self, query: str, keyword: str = None,
                        max_results: int = 5) -> Dict:
        """
        Search for sections and answer query
        """
        # Use query as keyword if not provided
        search_keyword = keyword or query.split()[0]

        logger.info(f"Searching for sections matching: {search_keyword}")
        search_results = self.retriever.search_sections_by_keyword(
            search_keyword,
            max_results=max_results
        )

        if not search_results:
            return {
                'query': query,
                'found_sections': 0,
                'answer': f"No sections found matching '{search_keyword}'"
            }

        # Build prompt with search results
        prompt = self.build_search_prompt(query, search_results)

        # Generate response
        logger.info("Generating response from search results...")
        response = self.model(
            prompt,
            max_tokens=800,
            temperature=0.3,
            top_p=0.9,
            echo=False
        )

        return {
            'query': query,
            'search_keyword': search_keyword,
            'found_sections': len(search_results),
            'sections': search_results,
            'answer': response['choices'][0]['text'].strip()
        }

    def analyze_relationships(self, section_number: str) -> Dict:
        """
        Analyze and explain legal relationships for a section
        """
        logger.info(f"Analyzing relationships for section {section_number}")

        prompt = self.build_relationship_prompt(section_number)

        response = self.model(
            prompt,
            max_tokens=800,
            temperature=0.4,
            top_p=0.9,
            echo=False
        )

        # Get related sections
        related = self.retriever.get_related_sections(section_number)

        return {
            'section': section_number,
            'analysis': response['choices'][0]['text'].strip(),
            'related_sections': related,
            'context': self.retriever.get_complete_context(section_number)
        }

    def compare_sections(self, section1: str, section2: str) -> Dict:
        """
        Compare two sections and explain their relationship
        """
        logger.info(f"Comparing sections {section1} and {section2}")

        # Get both sections
        s1_data = self.retriever.get_section(section1)
        s2_data = self.retriever.get_section(section2)

        if not s1_data or not s2_data:
            return {
                'error': f"One or both sections not found: {section1}, {section2}"
            }

        # Check if they cite each other
        s1_citations = self.retriever.get_citations(section1)
        s2_citations = self.retriever.get_citations(section2)

        s1_refs = s1_citations.get('direct_references', []) if s1_citations else []
        s2_refs = s2_citations.get('direct_references', []) if s2_citations else []

        relationship = "No direct citation"
        if section2 in s1_refs and section1 in s2_refs:
            relationship = "Mutual citation (both cite each other)"
        elif section2 in s1_refs:
            relationship = f"{section1} cites {section2}"
        elif section1 in s2_refs:
            relationship = f"{section2} cites {section1}"

        prompt = f"""Compare these two Ohio Revised Code sections:

SECTION {section1}: {s1_data['section_title']}
{s1_data['full_text'][:1000]}

SECTION {section2}: {s2_data['section_title']}
{s2_data['full_text'][:1000]}

RELATIONSHIP: {relationship}

TASK: Explain how these sections relate to each other, their similarities and differences, and how they work together in the legal framework.

YOUR ANALYSIS:"""

        response = self.model(
            prompt,
            max_tokens=800,
            temperature=0.4,
            top_p=0.9,
            echo=False
        )

        return {
            'section1': {
                'number': section1,
                'title': s1_data['section_title'],
                'url': s1_data['url'],
                'url_hash': s1_data['url_hash']
            },
            'section2': {
                'number': section2,
                'title': s2_data['section_title'],
                'url': s2_data['url'],
                'url_hash': s2_data['url_hash']
            },
            'relationship': relationship,
            'analysis': response['choices'][0]['text'].strip()
        }


if __name__ == "__main__":
    from config import MODEL_PATH, DATA_DIR

    lmdb_dir = DATA_DIR / "enriched_output" / "comprehensive_lmdb"
    processor = LegalQueryProcessor(MODEL_PATH, lmdb_dir)

    # Test query
    print("\n" + "="*80)
    print("TEST QUERY: What are the penalties for violating public meeting requirements?")
    print("="*80)

    result = processor.query_section(
        "101.15",
        "What are the penalties for violating public meeting requirements?",
        include_chain=True,
        max_chain_depth=3
    )

    print("\nANSWER:")
    print(result['answer'])

    print("\n\nCONTEXT STATS:")
    print(json.dumps(result['context_stats'], indent=2))

    print("\n\nSOURCES:")
    for source in result['sources']:
        print(f"  • Section {source['section']}: {source['url']}")
        print(f"    Hash: {source['url_hash']}")

    processor.close()