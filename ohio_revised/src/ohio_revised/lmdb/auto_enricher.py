#!/usr/bin/env python3
"""
Automatic enrichment of legal sections with essential metadata
Simplified for DeepSeek LLM context + pre-filtering (not autonomous agents)
"""

import re
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class EnrichmentData:
    """Essential enrichment metadata for DeepSeek + filtering"""
    # Core classification
    summary: str = None  # 1-2 sentence plain language
    legal_type: str = "statute"
    practice_areas: List[str] = None
    complexity: int = 5  # 1-10 scale
    key_terms: List[str] = None

    # Criminal statute specific
    offense_level: Optional[str] = None  # felony, misdemeanor, etc.
    offense_degree: Optional[str] = None  # F1-F5, M1-M4

    def __post_init__(self):
        if self.practice_areas is None:
            self.practice_areas = []
        if self.key_terms is None:
            self.key_terms = []

    def to_dict(self):
        return {
            "summary": self.summary,
            "legal_type": self.legal_type,
            "practice_areas": self.practice_areas,
            "complexity": self.complexity,
            "key_terms": self.key_terms,
            "offense_level": self.offense_level,
            "offense_degree": self.offense_degree
        }


class AutoEnricher:
    """Automatically enrich legal sections with essential metadata"""

    # Criminal statute indicators
    CRIMINAL_PATTERNS = [
        r'felony', r'misdemeanor', r'imprisonment', r'imprisoned',
        r'convicted', r'guilty', r'offense', r'violation', r'penalty'
    ]

    # Practice area keywords
    PRACTICE_AREA_KEYWORDS = {
        'criminal_law': [
            'felony', 'misdemeanor', 'imprisonment', 'convicted', 'offense',
            'guilty', 'crime', 'criminal', 'penal', 'defendant', 'prosecution',
            'sentence', 'jail', 'prison', 'punish'
        ],
        'family_law': [
            'marriage', 'divorce', 'custody', 'child support', 'adoption',
            'spouse', 'parent', 'guardian', 'domestic', 'alimony', 'visitation'
        ],
        'property_law': [
            'property', 'real estate', 'conveyance', 'deed', 'mortgage',
            'landlord', 'tenant', 'lease', 'title', 'easement', 'lien'
        ],
        'business_law': [
            'corporation', 'llc', 'partnership', 'business', 'commercial',
            'contract', 'enterprise', 'company', 'shareholder', 'entity'
        ],
        'tax_law': [
            'tax', 'revenue', 'assessment', 'levy', 'taxation', 'taxable',
            'income tax', 'sales tax', 'property tax'
        ],
        'employment_law': [
            'employment', 'employee', 'employer', 'workplace', 'labor',
            'wage', 'worker', 'compensation', 'unemployment', 'benefits'
        ],
        'administrative_law': [
            'agency', 'regulation', 'administrative', 'rule', 'board',
            'commission', 'department', 'licensing', 'permit'
        ],
        'civil_procedure': [
            'complaint', 'summons', 'pleading', 'discovery', 'trial',
            'judgment', 'appeal', 'motion', 'filing'
        ]
    }

    def enrich_section(self, section_data: Dict, citation_count: int = 0) -> Dict:
        """
        Auto-enrich a section with essential metadata

        Args:
            section_data: Section dict with paragraphs, header, etc.
            citation_count: Number of citations in this section

        Returns:
            Section data with 'enrichment' field added
        """
        paragraphs = section_data.get('paragraphs', [])
        header = section_data.get('header', '')
        section_num = section_data.get('section_number', '')
        full_text = '\n'.join(paragraphs).lower()

        enrichment = EnrichmentData()

        # Generate summary from header
        enrichment.summary = self._generate_summary(header)

        # Classify legal type
        enrichment.legal_type = self._classify_legal_type(full_text, header)

        # Identify practice areas
        enrichment.practice_areas = self._identify_practice_areas(full_text, section_num)

        # Extract criminal offense info (if applicable)
        if enrichment.legal_type == 'criminal_statute':
            enrichment.offense_level = self._extract_offense_level(full_text)
            enrichment.offense_degree = self._extract_offense_degree(full_text)

        # Calculate complexity
        enrichment.complexity = self._calculate_complexity(
            word_count=section_data.get('word_count', 0),
            paragraph_count=section_data.get('paragraph_count', 0),
            citation_count=citation_count
        )

        # Extract key terms
        enrichment.key_terms = self._extract_key_terms(header, full_text)

        # Add enrichment to section data
        section_data['enrichment'] = enrichment.to_dict()

        return section_data

    def _generate_summary(self, header: str) -> str:
        """Generate plain language summary from header"""
        if '|' not in header:
            return header.strip()

        # Extract title part after |
        parts = header.split('|')
        if len(parts) < 2:
            return header.strip()

        section_part = parts[0].strip()  # e.g., "Section 2903.01"
        title_part = parts[1].strip()     # e.g., "Aggravated Murder"

        # Create summary: "Defines [title]" or "Relates to [title]"
        # Use simple heuristic based on title
        if any(word in title_part.lower() for word in ['definition', 'definitions', 'defined']):
            return f"Defines {title_part.lower()}"
        elif any(word in title_part.lower() for word in ['penalty', 'penalties', 'punishment']):
            return f"Establishes penalties for {title_part.lower()}"
        elif any(word in title_part.lower() for word in ['procedure', 'process', 'filing']):
            return f"Describes procedure for {title_part.lower()}"
        else:
            return f"Relates to {title_part.lower()}"

    def _classify_legal_type(self, text: str, header: str) -> str:
        """Classify statute type"""
        text_lower = text.lower()
        header_lower = header.lower()

        # Check for criminal statutes
        criminal_matches = sum(1 for pattern in self.CRIMINAL_PATTERNS
                             if re.search(pattern, text_lower))

        if criminal_matches >= 2:
            return 'criminal_statute'

        # Check for definitional sections
        if 'as used in' in text_lower or 'definition' in header_lower:
            return 'definitional'

        # Check for procedural
        if any(word in text_lower for word in ['procedure', 'process', 'filing', 'hearing', 'motion']):
            return 'procedural'

        # Default
        return 'civil_statute'

    def _identify_practice_areas(self, text: str, section_num: str) -> List[str]:
        """Identify practice areas based on keywords and section number"""
        areas = []

        # Check keywords
        for area, keywords in self.PRACTICE_AREA_KEYWORDS.items():
            matches = sum(1 for keyword in keywords if keyword in text)
            if matches >= 2:  # At least 2 keyword matches
                areas.append(area)

        # Check by title number (Ohio Revised Code specific)
        try:
            title_num = int(section_num.split('.')[0]) if '.' in section_num else int(section_num)

            # Criminal law is primarily in Title 29
            if 2900 <= title_num < 3000:
                if 'criminal_law' not in areas:
                    areas.append('criminal_law')

            # Family law is Title 31
            if 3100 <= title_num < 3200:
                if 'family_law' not in areas:
                    areas.append('family_law')

            # Tax is Title 55-57
            if 5500 <= title_num < 5800:
                if 'tax_law' not in areas:
                    areas.append('tax_law')

            # Business/Corporations is Title 17
            if 1700 <= title_num < 1800:
                if 'business_law' not in areas:
                    areas.append('business_law')

        except (ValueError, IndexError):
            pass

        return areas if areas else ['general']

    def _extract_offense_level(self, text: str) -> Optional[str]:
        """Extract felony/misdemeanor classification"""
        if re.search(r'felony', text, re.IGNORECASE):
            return 'felony'
        elif re.search(r'misdemeanor', text, re.IGNORECASE):
            return 'misdemeanor'
        elif re.search(r'minor misdemeanor', text, re.IGNORECASE):
            return 'minor_misdemeanor'
        return None

    def _extract_offense_degree(self, text: str) -> Optional[str]:
        """Extract specific degree (F1, F5, M1, etc.)"""
        # Look for patterns like "felony of the first degree"
        felony_match = re.search(r'felony of the (first|second|third|fourth|fifth) degree', text, re.IGNORECASE)
        if felony_match:
            degree_map = {'first': 'F1', 'second': 'F2', 'third': 'F3', 'fourth': 'F4', 'fifth': 'F5'}
            return degree_map.get(felony_match.group(1).lower())

        # Look for misdemeanor degrees
        misdemeanor_match = re.search(r'misdemeanor of the (first|second|third|fourth) degree', text, re.IGNORECASE)
        if misdemeanor_match:
            degree_map = {'first': 'M1', 'second': 'M2', 'third': 'M3', 'fourth': 'M4'}
            return degree_map.get(misdemeanor_match.group(1).lower())

        return None

    def _calculate_complexity(self, word_count: int, paragraph_count: int, citation_count: int) -> int:
        """Calculate complexity score 1-10"""
        score = 5  # Default medium

        # Word count factor
        if word_count > 1000:
            score += 2
        elif word_count > 500:
            score += 1
        elif word_count < 100:
            score -= 1

        # Paragraph factor (more paragraphs = more complex)
        if paragraph_count > 15:
            score += 2
        elif paragraph_count > 10:
            score += 1

        # Citation factor (more citations = more interconnected = more complex)
        if citation_count > 10:
            score += 2
        elif citation_count > 5:
            score += 1
        elif citation_count == 0:
            score -= 1

        return max(1, min(10, score))  # Clamp between 1-10

    def _extract_key_terms(self, header: str, text: str) -> List[str]:
        """Extract key legal terms from header and text"""
        terms = []

        # Get title from header
        if '|' in header:
            title = header.split('|')[1].strip().lower()
            # Split on common separators and take significant words
            words = re.split(r'[,;.\-\s]+', title)
            significant_words = [w for w in words
                               if len(w) > 3 and w not in ['the', 'and', 'for', 'with', 'from', 'this', 'that']]
            terms.extend(significant_words)

        # Look for defined terms in quotes
        quoted_terms = re.findall(r'"([^"]+)"', text)
        terms.extend([t.lower() for t in quoted_terms if len(t) < 30])

        # Look for capitalized legal terms (e.g., "Aggravated Murder")
        capitalized_terms = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', text[:500])  # First 500 chars
        terms.extend([t.lower() for t in capitalized_terms if len(t) > 5 and t.lower() not in terms])

        # Remove duplicates and limit
        unique_terms = list(dict.fromkeys(terms))  # Preserves order
        return unique_terms[:10]


# Example usage and testing
if __name__ == "__main__":
    enricher = AutoEnricher()

    # Test section 1: Criminal statute
    test_section_1 = {
        "section_number": "2913.02",
        "header": "Section 2913.02|Theft.",
        "paragraphs": [
            "No person, with purpose to deprive the owner of property or services, shall knowingly obtain or exert control over either the property or services in any of the following ways:",
            "(A) Without the consent of the owner or person authorized to give consent;",
            "(B) Beyond the scope of the express or implied consent of the owner or person authorized to give consent;",
            "Whoever violates this section is guilty of theft, a felony of the fifth degree."
        ],
        "word_count": 75,
        "paragraph_count": 4
    }

    # Test section 2: Definitional
    test_section_2 = {
        "section_number": "1.02",
        "header": "Section 1.02|Definitions in Revised Code.",
        "paragraphs": [
            "As used in the Revised Code, unless the context otherwise requires:",
            "(A) 'Whoever' includes all persons, natural and artificial; partners; principals, agents, and employees; and all officials, public or private.",
            "(B) 'Another,' when used to designate the owner of property which is the subject of an offense, includes not only natural persons but also every other owner of property."
        ],
        "word_count": 58,
        "paragraph_count": 3
    }

    print("="*60)
    print("SIMPLIFIED ENRICHMENT TEST")
    print("="*60)

    print("\n📄 Test 1: Criminal Statute (Theft)")
    enriched_1 = enricher.enrich_section(test_section_1, citation_count=3)
    import json
    print(json.dumps(enriched_1['enrichment'], indent=2))

    print("\n📄 Test 2: Definitional Statute")
    enriched_2 = enricher.enrich_section(test_section_2, citation_count=0)
    print(json.dumps(enriched_2['enrichment'], indent=2))

    print("\n" + "="*60)
    print("✅ Simplified enrichment working!")
    print("Fields: summary, legal_type, practice_areas, complexity,")
    print("        key_terms, offense_level, offense_degree")
    print("="*60)