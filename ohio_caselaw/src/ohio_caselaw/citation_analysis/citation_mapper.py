#!/usr/bin/env python3
"""
Ohio Case Law Citation Extraction and Mapping
Extracts citations from case opinions and builds citation relationships
"""
from typing import Dict, List, Set, Tuple, Optional
import re
from dataclasses import dataclass


@dataclass
class Citation:
    """Represents a case citation with context"""
    cited_case: str
    citation_string: str
    context: str
    relationship_type: str
    cite_type: str  # 'ohio-neutral', 'ohio-reports', 'northeast', 'federal', 'other'


class OhioCaseLawCitationMapper:
    """
    Extracts and maps citations from Ohio case law opinions

    Citation formats:
    - Ohio Neutral: 2024-Ohio-123, 2023-Ohio-4567
    - Ohio Reports: 174 Ohio St. 471, 123 Ohio App. 3d 456
    - North Eastern Reporter: 123 N.E.2d 456, 789 N.E.3d 123
    - Ohio State Reports: 123 Ohio St. 2d 456, 456 Ohio St. 3d 789
    - Federal: 123 F.3d 456, 456 U.S. 789
    """

    # Citation patterns with named groups
    CITATION_PATTERNS = {
        'ohio_neutral': re.compile(
            r'\b(\d{4})-Ohio-(\d+)\b',
            re.IGNORECASE
        ),
        'ohio_state': re.compile(
            r'\b(\d+)\s+Ohio\s+St\.?\s*(\d[dr]d?)?\s+(\d+)\b',
            re.IGNORECASE
        ),
        'ohio_app': re.compile(
            r'\b(\d+)\s+Ohio\s+App\.?\s*(\d[dr]d?)?\s+(\d+)\b',
            re.IGNORECASE
        ),
        'ohio_misc': re.compile(
            r'\b(\d+)\s+Ohio\s+(Misc\.?|Dec\.?|N\.P\.?)\s*(\d[dr]d?)?\s+(\d+)\b',
            re.IGNORECASE
        ),
        'northeast': re.compile(
            r'\b(\d+)\s+N\.E\.\s*(\d[dr]d?)?\s+(\d+)\b',
            re.IGNORECASE
        ),
        'federal_supreme': re.compile(
            r'\b(\d+)\s+U\.S\.\s+(\d+)\b',
            re.IGNORECASE
        ),
        'federal_reporter': re.compile(
            r'\b(\d+)\s+F\.\s*(\d[dr]d?)?\s+(\d+)\b',
            re.IGNORECASE
        ),
        'federal_supp': re.compile(
            r'\b(\d+)\s+F\.\s*Supp\.\s*(\d[dr]d?)?\s+(\d+)\b',
            re.IGNORECASE
        ),
    }

    # Relationship patterns (how the citation is used)
    RELATIONSHIP_PATTERNS = {
        'overruled': [
            r'overrul(?:ed|ing)\s+(?:in\s+)?(.{0,100})',
            r'(.{0,100})\s+(?:was|is)\s+overruled',
        ],
        'reversed': [
            r'revers(?:ed|ing)\s+(.{0,100})',
            r'(.{0,100})\s+(?:was|is)\s+reversed',
        ],
        'affirmed': [
            r'affirm(?:ed|ing)\s+(.{0,100})',
            r'(.{0,100})\s+(?:was|is)\s+affirmed',
        ],
        'distinguished': [
            r'distinguish(?:ed|ing)\s+(?:from\s+)?(.{0,100})',
            r'(.{0,100})\s+(?:is|was)\s+distinguished',
        ],
        'followed': [
            r'follow(?:ed|ing|s)\s+(.{0,100})',
            r'pursuant\s+to\s+(.{0,100})',
            r'consistent\s+with\s+(.{0,100})',
        ],
        'cited': [
            r'(?:see|citing|accord)\s+(.{0,100})',
            r'as\s+(?:stated|held|noted)\s+in\s+(.{0,100})',
        ],
        'questioned': [
            r'question(?:ed|ing)\s+(.{0,100})',
            r'doubt(?:ed|ing)\s+(.{0,100})',
        ],
        'compared': [
            r'compar(?:ed|ing)\s+(?:with\s+)?(.{0,100})',
            r'(?:cf\.|contrast)\s+(.{0,100})',
        ],
    }

    def __init__(self):
        """Initialize citation mapper"""
        self.citation_cache: Dict[str, List[Citation]] = {}

    def extract_citations_from_cites_to(self, case_data: Dict) -> List[Citation]:
        """
        Extract citations from the cites_to array (already parsed by CourtListener)

        Args:
            case_data: Full case JSON data with cites_to array

        Returns:
            List of Citation objects
        """
        citations = []
        cites_to = case_data.get('cites_to', [])

        for cited_case in cites_to:
            # cited_case is typically a case ID or citation string
            citation = Citation(
                cited_case=str(cited_case),
                citation_string=str(cited_case),
                context='',
                relationship_type='cited',
                cite_type=self._classify_citation_type(str(cited_case))
            )
            citations.append(citation)

        return citations

    def extract_citations_from_text(self, opinion_text: str, case_id: str) -> List[Citation]:
        """
        Extract citations from opinion text with context and relationship type

        Args:
            opinion_text: Full text of the opinion
            case_id: ID of the current case

        Returns:
            List of Citation objects with context
        """
        # Check cache
        if case_id in self.citation_cache:
            return self.citation_cache[case_id]

        citations = []
        seen_citations = set()

        # Extract all citation patterns
        for cite_type, pattern in self.CITATION_PATTERNS.items():
            for match in pattern.finditer(opinion_text):
                citation_string = match.group(0)

                # Skip duplicates
                if citation_string in seen_citations:
                    continue
                seen_citations.add(citation_string)

                # Extract context (surrounding text)
                start = max(0, match.start() - 100)
                end = min(len(opinion_text), match.end() + 100)
                context = opinion_text[start:end]

                # Determine relationship type
                relationship = self._determine_relationship(context, citation_string)

                citation = Citation(
                    cited_case=citation_string,
                    citation_string=citation_string,
                    context=context,
                    relationship_type=relationship,
                    cite_type=cite_type
                )
                citations.append(citation)

        # Cache results
        self.citation_cache[case_id] = citations
        return citations

    def extract_all_citations(self, case_data: Dict) -> Tuple[List[Citation], List[Citation]]:
        """
        Extract citations from both cites_to array and opinion text

        Args:
            case_data: Full case JSON data

        Returns:
            Tuple of (cites_to_citations, text_citations)
        """
        case_id = str(case_data.get('id', ''))

        # Extract from cites_to array
        cites_to_citations = self.extract_citations_from_cites_to(case_data)

        # Extract from opinion text
        casebody = case_data.get('casebody', {})
        opinions = casebody.get('data', {}).get('opinions', [])

        text_citations = []
        for opinion in opinions:
            opinion_text = opinion.get('text', '')
            if opinion_text:
                text_citations.extend(
                    self.extract_citations_from_text(opinion_text, case_id)
                )

        return cites_to_citations, text_citations

    def _classify_citation_type(self, citation: str) -> str:
        """
        Classify the citation format type

        Args:
            citation: Citation string

        Returns:
            Citation type category
        """
        citation_lower = citation.lower()

        if re.search(r'\d{4}-ohio-\d+', citation_lower):
            return 'ohio-neutral'
        elif 'ohio st' in citation_lower:
            return 'ohio-state'
        elif 'ohio app' in citation_lower:
            return 'ohio-app'
        elif 'n.e.' in citation_lower:
            return 'northeast'
        elif 'u.s.' in citation_lower:
            return 'federal-supreme'
        elif 'f.' in citation_lower and 'supp' not in citation_lower:
            return 'federal-reporter'
        elif 'f. supp' in citation_lower:
            return 'federal-supp'
        else:
            return 'other'

    def _determine_relationship(self, context: str, citation: str) -> str:
        """
        Determine the relationship type based on surrounding context

        Args:
            context: Text surrounding the citation
            citation: The citation string

        Returns:
            Relationship type
        """
        context_lower = context.lower()

        # Check each relationship pattern
        for relationship, patterns in self.RELATIONSHIP_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, context_lower, re.IGNORECASE):
                    return relationship

        # Default to generic 'cited'
        return 'cited'

    def build_citation_graph(self, all_cases: List[Dict]) -> Dict[str, List[str]]:
        """
        Build a citation graph from all cases

        Args:
            all_cases: List of all case data dictionaries

        Returns:
            Dictionary mapping case_id -> [cited_case_ids]
        """
        citation_graph = {}

        for case_data in all_cases:
            case_id = str(case_data.get('id', ''))

            # Get all citations
            cites_to_citations, text_citations = self.extract_all_citations(case_data)

            # Combine unique citations
            all_citations = set()
            for citation in cites_to_citations + text_citations:
                all_citations.add(citation.cited_case)

            citation_graph[case_id] = list(all_citations)

        return citation_graph

    def build_reverse_citation_graph(
        self,
        citation_graph: Dict[str, List[str]]
    ) -> Dict[str, List[str]]:
        """
        Build reverse citation graph (cited_by relationships)

        Args:
            citation_graph: Forward citation graph

        Returns:
            Dictionary mapping case_id -> [citing_case_ids]
        """
        reverse_graph = {}

        for citing_case, cited_cases in citation_graph.items():
            for cited_case in cited_cases:
                if cited_case not in reverse_graph:
                    reverse_graph[cited_case] = []
                reverse_graph[cited_case].append(citing_case)

        return reverse_graph

    def calculate_citation_metrics(
        self,
        case_id: str,
        citation_graph: Dict[str, List[str]],
        reverse_graph: Dict[str, List[str]]
    ) -> Dict[str, int]:
        """
        Calculate citation metrics for a case

        Args:
            case_id: Case identifier
            citation_graph: Forward citations
            reverse_graph: Reverse citations (cited_by)

        Returns:
            Dictionary of metrics
        """
        outgoing = len(citation_graph.get(case_id, []))
        incoming = len(reverse_graph.get(case_id, []))

        return {
            'outgoing_citations': outgoing,
            'incoming_citations': incoming,
            'citation_impact': incoming,  # Simple impact score
            'centrality': incoming + (outgoing * 0.1),  # Weighted centrality
        }

    def get_citation_chains(
        self,
        case_id: str,
        citation_graph: Dict[str, List[str]],
        max_depth: int = 3
    ) -> List[List[str]]:
        """
        Find citation chains (paths) from this case

        Args:
            case_id: Starting case
            citation_graph: Forward citation graph
            max_depth: Maximum chain length

        Returns:
            List of citation chains (each chain is a list of case IDs)
        """
        chains = []
        visited = set()

        def dfs(current_case: str, path: List[str], depth: int):
            if depth > max_depth:
                return

            if current_case in visited and current_case != case_id:
                return

            visited.add(current_case)
            path.append(current_case)

            # Get citations from current case
            cited_cases = citation_graph.get(current_case, [])

            if not cited_cases or depth == max_depth:
                # End of chain
                if len(path) > 1:
                    chains.append(path.copy())
            else:
                # Continue exploring
                for cited_case in cited_cases[:5]:  # Limit branches
                    dfs(cited_case, path.copy(), depth + 1)

            visited.remove(current_case)

        dfs(case_id, [], 0)
        return chains


def get_citation_mapper() -> OhioCaseLawCitationMapper:
    """Get singleton instance of citation mapper"""
    return OhioCaseLawCitationMapper()