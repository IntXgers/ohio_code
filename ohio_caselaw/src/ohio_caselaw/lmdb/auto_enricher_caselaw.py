#!/usr/bin/env python3
"""
Automatic enrichment of legal case opinions with essential metadata
Adapted for case law structure (opinions, not statutes)
"""

import re
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class EnrichmentData:
    """Essential enrichment metadata for case law"""
    # Core classification
    summary: str = None  # 1-2 sentence plain language
    legal_type: str = "case_opinion"
    practice_areas: List[str] = None
    complexity: int = 5  # 1-10 scale
    key_terms: List[str] = None

    # Criminal case specific
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
    """Automatically enrich case law opinions with essential metadata"""

    # Criminal case indicators
    CRIMINAL_PATTERNS = [
        r'felony', r'misdemeanor', r'imprisonment', r'imprisoned',
        r'convicted', r'guilty', r'offense', r'violation', r'penalty',
        r'defendant', r'prosecution', r'sentence', r'criminal'
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
        ],
        'constitutional_law': [
            'constitutional', 'amendment', 'due process', 'equal protection',
            'first amendment', 'fourth amendment', 'rights'
        ],
        'tort_law': [
            'negligence', 'damages', 'liability', 'injury', 'tort',
            'personal injury', 'wrongful death', 'malpractice'
        ]
    }

    def enrich_case(self, case_data: Dict, citation_count: int = 0) -> Dict:
        """
        Auto-enrich a case with essential metadata

        Args:
            case_data: Case dict with casebody, name, etc.
            citation_count: Number of citations in this case

        Returns:
            Case data with 'enrichment' field added
        """
        case_name = case_data.get('name', '')
        casebody = case_data.get('casebody', {})
        opinions = casebody.get('opinions', [])

        # Combine all opinion text
        opinion_texts = [op.get('text', '') for op in opinions]
        full_text = '\n'.join(opinion_texts).lower()

        enrichment = EnrichmentData()

        # Generate summary from case name
        enrichment.summary = self._generate_summary(case_name)

        # Classify legal type (always case_opinion, but could be criminal_case, civil_case, etc.)
        enrichment.legal_type = self._classify_legal_type(full_text, case_name)

        # Identify practice areas
        enrichment.practice_areas = self._identify_practice_areas(full_text)

        # Extract criminal offense info (if applicable)
        if 'criminal' in enrichment.legal_type:
            enrichment.offense_level = self._extract_offense_level(full_text)
            enrichment.offense_degree = self._extract_offense_degree(full_text)

        # Calculate complexity
        word_count = sum(len(text.split()) for text in opinion_texts)
        opinion_count = len(opinions)

        enrichment.complexity = self._calculate_complexity(
            word_count=word_count,
            opinion_count=opinion_count,
            citation_count=citation_count
        )

        # Extract key terms
        enrichment.key_terms = self._extract_key_terms(case_name, full_text)

        # Add enrichment to case data
        case_data['enrichment'] = enrichment.to_dict()

        return case_data

    def _generate_summary(self, case_name: str) -> str:
        """Generate plain language summary from case name"""
        # Clean up case name
        name = case_name.strip()

        # Extract parties (before " v. " or " vs. ")
        if ' v. ' in name:
            parties = name.split(' v. ')[0:2]
            return f"Case between {parties[0]} and {parties[1] if len(parties) > 1 else 'other party'}"
        elif ' vs. ' in name:
            parties = name.split(' vs. ')[0:2]
            return f"Case between {parties[0]} and {parties[1] if len(parties) > 1 else 'other party'}"
        else:
            return f"Case regarding {name[:100]}"

    def _classify_legal_type(self, text: str, case_name: str) -> str:
        """Classify case type"""
        text_lower = text.lower()
        name_lower = case_name.lower()

        # Check for criminal cases
        criminal_matches = sum(1 for pattern in self.CRIMINAL_PATTERNS
                             if re.search(pattern, text_lower))

        if criminal_matches >= 3:
            return 'criminal_case'

        # Check for appeals
        if 'appeal' in text_lower or 'appellant' in text_lower or 'appellee' in name_lower:
            return 'appellate_case'

        # Default
        return 'civil_case'

    def _identify_practice_areas(self, text: str) -> List[str]:
        """Identify practice areas based on keywords"""
        areas = []

        # Check keywords
        for area, keywords in self.PRACTICE_AREA_KEYWORDS.items():
            matches = sum(1 for keyword in keywords if keyword in text)
            if matches >= 2:  # At least 2 keyword matches
                areas.append(area)

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

    def _calculate_complexity(self, word_count: int, opinion_count: int, citation_count: int) -> int:
        """Calculate complexity score 1-10"""
        score = 5  # Default medium

        # Word count factor
        if word_count > 5000:
            score += 2
        elif word_count > 2000:
            score += 1
        elif word_count < 500:
            score -= 1

        # Opinion count factor (multiple opinions = more complex)
        if opinion_count > 2:
            score += 2
        elif opinion_count > 1:
            score += 1

        # Citation factor
        if citation_count > 20:
            score += 2
        elif citation_count > 10:
            score += 1
        elif citation_count == 0:
            score -= 1

        return max(1, min(10, score))  # Clamp between 1-10

    def _extract_key_terms(self, case_name: str, text: str) -> List[str]:
        """Extract key legal terms from case name and text"""
        terms = []

        # Get party names from case name
        if ' v. ' in case_name:
            parties = case_name.split(' v. ')
            for party in parties[:2]:  # First two parties
                party_clean = party.strip().split(',')[0]  # Remove titles/suffixes
                if len(party_clean) > 3:
                    terms.append(party_clean.lower())

        # Look for quoted terms
        quoted_terms = re.findall(r'"([^"]+)"', text)
        terms.extend([t.lower() for t in quoted_terms if len(t) < 30])

        # Look for common legal phrases
        legal_phrases = re.findall(r'\b(summary judgment|due process|probable cause|reasonable doubt|'
                                   r'good faith|bad faith|strict liability|proximate cause)\b', text, re.IGNORECASE)
        terms.extend([phrase.lower() for phrase in legal_phrases])

        # Remove duplicates and limit
        unique_terms = list(dict.fromkeys(terms))  # Preserves order
        return unique_terms[:10]


# Example usage
if __name__ == "__main__":
    enricher = AutoEnricher()

    test_case = {
        "id": 1234567,
        "name": "State of Ohio v. John Doe",
        "casebody": {
            "opinions": [
                {
                    "text": "Defendant was convicted of theft, a felony of the fifth degree. "
                            "The court sentenced the defendant to imprisonment. We affirm the conviction.",
                    "type": "majority"
                }
            ]
        }
    }

    print("=" * 60)
    print("CASE LAW ENRICHMENT TEST")
    print("=" * 60)

    enriched = enricher.enrich_case(test_case, citation_count=5)
    import json
    print(json.dumps(enriched['enrichment'], indent=2))
    print("=" * 60)