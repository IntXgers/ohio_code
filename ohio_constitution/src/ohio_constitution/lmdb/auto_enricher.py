#!/usr/bin/env python3
"""
Automatic enrichment of Ohio Constitution sections with essential metadata
"""

import re
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from citation_analysis.ohio_constitution_mapping import (
    get_article_name,
    get_article_category,
    BILL_OF_RIGHTS_CATEGORIES
)


@dataclass
class EnrichmentData:
    """Enrichment metadata for Ohio Constitution sections"""
    # Core classification
    summary: str = None  # 1-2 sentence plain language
    article_type: str = None  # bill_of_rights, legislative_branch, etc.
    article_name: str = None  # "Article I - Bill of Rights"
    complexity: int = 5  # 1-10 scale
    key_terms: List[str] = None

    # Constitutional specific
    rights_category: Optional[str] = None  # For Bill of Rights sections
    government_branch: Optional[str] = None  # legislative, executive, judicial
    subject_matter: List[str] = None  # elections, taxation, education, etc.

    def __post_init__(self):
        if self.key_terms is None:
            self.key_terms = []
        if self.subject_matter is None:
            self.subject_matter = []

    def to_dict(self):
        return {
            "summary": self.summary,
            "article_type": self.article_type,
            "article_name": self.article_name,
            "complexity": self.complexity,
            "key_terms": self.key_terms,
            "rights_category": self.rights_category,
            "government_branch": self.government_branch,
            "subject_matter": self.subject_matter
        }


class AutoEnricher:
    """Automatically enrich Ohio Constitution sections with metadata"""

    # Subject matter keywords
    SUBJECT_MATTER_KEYWORDS = {
        'fundamental_rights': [
            'rights', 'liberty', 'freedom', 'equality', 'justice',
            'free', 'independent', 'inalienable', 'protect'
        ],
        'voting_elections': [
            'election', 'vote', 'ballot', 'suffrage', 'voter',
            'elect', 'electoral', 'candidate', 'poll'
        ],
        'judicial_system': [
            'court', 'judge', 'justice', 'judicial', 'trial',
            'jury', 'judgment', 'appeal', 'supreme court'
        ],
        'legislative_process': [
            'general assembly', 'legislature', 'bill', 'law',
            'senate', 'house', 'representatives', 'enact'
        ],
        'executive_powers': [
            'governor', 'executive', 'veto', 'appointment',
            'pardon', 'command', 'enforce'
        ],
        'education': [
            'school', 'education', 'educational', 'university',
            'college', 'instruction', 'learning', 'teacher'
        ],
        'taxation_finance': [
            'tax', 'revenue', 'debt', 'fiscal', 'appropriation',
            'treasury', 'fund', 'levy', 'assessment'
        ],
        'local_government': [
            'municipal', 'county', 'township', 'city', 'local',
            'home rule', 'charter', 'corporation'
        ],
        'amendments': [
            'amend', 'amendment', 'revision', 'constitution',
            'propose', 'ratify', 'convention'
        ]
    }

    def enrich_section(self, section_data: Dict, citation_count: int = 0) -> Dict:
        """
        Auto-enrich a constitutional section with metadata

        Args:
            section_data: Section dict with paragraphs, header, etc.
            citation_count: Number of citations in this section

        Returns:
            Section data with 'enrichment' field added
        """
        paragraphs = section_data.get('paragraphs', [])
        header = section_data.get('header', '')
        section_id = section_data.get('section_number', '')
        full_text = '\n'.join(paragraphs).lower()

        enrichment = EnrichmentData()

        # Get article information
        enrichment.article_name = get_article_name(section_id)
        enrichment.article_type = get_article_category(section_id)

        # Generate summary from header
        enrichment.summary = self._generate_summary(header)

        # Identify subject matter
        enrichment.subject_matter = self._identify_subject_matter(full_text)

        # Extract rights category (if Bill of Rights)
        if enrichment.article_type == 'bill_of_rights':
            enrichment.rights_category = self._extract_rights_category(section_id, full_text, header)

        # Identify government branch (if applicable)
        enrichment.government_branch = self._identify_government_branch(enrichment.article_type)

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

        section_part = parts[0].strip()  # e.g., "Article I, Section 1"
        title_part = parts[1].strip()     # e.g., "Inalienable Rights"

        # Create summary based on title
        if any(word in title_part.lower() for word in ['rights', 'freedom', 'liberty']):
            return f"Guarantees {title_part.lower()}"
        elif any(word in title_part.lower() for word in ['power', 'authority', 'duty']):
            return f"Establishes {title_part.lower()}"
        elif any(word in title_part.lower() for word in ['procedure', 'process', 'election']):
            return f"Governs {title_part.lower()}"
        elif any(word in title_part.lower() for word in ['prohibition', 'prohibited', 'limit']):
            return f"Prohibits or limits {title_part.lower()}"
        else:
            return f"Addresses {title_part.lower()}"

    def _identify_subject_matter(self, text: str) -> List[str]:
        """Identify subject matter based on keywords"""
        matters = []

        for subject, keywords in self.SUBJECT_MATTER_KEYWORDS.items():
            matches = sum(1 for keyword in keywords if keyword in text)
            if matches >= 1:  # At least 1 keyword match for constitution
                matters.append(subject)

        return matters if matters else ['general']

    def _extract_rights_category(self, section_id: str, text: str, header: str) -> Optional[str]:
        """Extract rights category for Bill of Rights sections"""
        # Try to get from section number first
        section_match = re.search(r'Section\s+(\d+)', section_id)
        if section_match:
            section_num = section_match.group(1)
            if section_num in BILL_OF_RIGHTS_CATEGORIES:
                return BILL_OF_RIGHTS_CATEGORIES[section_num]

        # Fallback to keyword matching
        header_lower = header.lower()
        text_lower = text.lower()

        if any(word in header_lower or word in text_lower for word in ['speech', 'press', 'expression']):
            return 'free_speech'
        elif any(word in header_lower or word in text_lower for word in ['religion', 'worship']):
            return 'religious_freedom'
        elif any(word in header_lower or word in text_lower for word in ['search', 'seizure', 'warrant']):
            return 'search_and_seizure'
        elif any(word in header_lower or word in text_lower for word in ['jury', 'trial']):
            return 'trial_by_jury'
        elif any(word in header_lower or word in text_lower for word in ['bail', 'punishment', 'cruel']):
            return 'bail_and_punishment'
        elif any(word in header_lower or word in text_lower for word in ['property', 'eminent domain', 'taking']):
            return 'eminent_domain'
        elif any(word in header_lower or word in text_lower for word in ['assembly', 'petition']):
            return 'assembly_and_petition'

        return 'general_rights'

    def _identify_government_branch(self, article_type: str) -> Optional[str]:
        """Identify which government branch this section relates to"""
        if article_type == 'legislative_branch':
            return 'legislative'
        elif article_type == 'executive_branch':
            return 'executive'
        elif article_type == 'judicial_branch':
            return 'judicial'
        return None

    def _calculate_complexity(self, word_count: int, paragraph_count: int, citation_count: int) -> int:
        """Calculate complexity score 1-10"""
        score = 5  # Default medium

        # Word count factor
        if word_count > 800:
            score += 2
        elif word_count > 400:
            score += 1
        elif word_count < 100:
            score -= 1

        # Paragraph factor (constitutional sections tend to be shorter)
        if paragraph_count > 10:
            score += 2
        elif paragraph_count > 5:
            score += 1

        # Citation factor (more citations = more interconnected)
        if citation_count > 5:
            score += 2
        elif citation_count > 2:
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

        # Look for constitutional terms in quotes
        quoted_terms = re.findall(r'"([^"]+)"', text)
        terms.extend([t.lower() for t in quoted_terms if len(t) < 30])

        # Look for capitalized legal terms
        capitalized_terms = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', text[:500])
        terms.extend([t.lower() for t in capitalized_terms if len(t) > 5 and t.lower() not in terms])

        # Remove duplicates and limit
        unique_terms = list(dict.fromkeys(terms))
        return unique_terms[:10]


# Example usage and testing
if __name__ == "__main__":
    enricher = AutoEnricher()

    # Test section: Bill of Rights
    test_section = {
        "section_number": "Article I, Section 1",
        "header": "Article I, Section 1|Inalienable Rights",
        "paragraphs": [
            "All men are, by nature, free and independent, and have certain inalienable rights, among which are those of enjoying and defending life and liberty, acquiring, possessing, and protecting property, and seeking and obtaining happiness and safety."
        ],
        "word_count": 42,
        "paragraph_count": 1
    }

    print("="*60)
    print("OHIO CONSTITUTION ENRICHMENT TEST")
    print("="*60)

    print("\n📄 Test: Bill of Rights (Article I, Section 1)")
    enriched = enricher.enrich_section(test_section, citation_count=0)
    import json
    print(json.dumps(enriched['enrichment'], indent=2))

    print("\n" + "="*60)
    print("✅ Constitutional enrichment working!")
    print("Fields: summary, article_type, article_name, complexity,")
    print("        key_terms, rights_category, government_branch, subject_matter")
    print("="*60)