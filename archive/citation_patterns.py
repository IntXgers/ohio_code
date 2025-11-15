#!/usr/bin/env python3
"""
Corpus-specific citation patterns for Ohio legal codes
Each corpus has unique citation formats that need specialized regex patterns
"""

import re
from typing import Dict, List, Tuple, Set

# =============================================================================
# OHIO REVISED CODE (ORC) PATTERNS
# =============================================================================

ORC_PATTERNS = [
    # Primary section references
    r'[Ss]ections?\s+(\d+\.\d+)(?:\s+to\s+(\d+\.\d+))?',  # "section 124.01" or "sections 124.01 to 124.64"
    r'division\s*\([A-Z]\d*\)\s+of\s+section\s+(\d+\.\d+)',  # "division (A) of section 124.23"
    r'(?:Chapter\s+)?(\d{3,4})\.\s+of\s+the\s+Revised\s+Code',  # "Chapter 119. of the Revised Code"
    r'(?<![.\d])(\d{3,4}\.\d+)(?![.\d])',  # Standalone numeric like "5907.01"
    r'R\.?C\.?\s+(\d+\.\d+)',  # "R.C. 2903.01" or "RC 2903.01"
    r'ORC\s+(\d+\.\d+)',  # "ORC 2903.01"
]

def extract_orc_section_number(header: str) -> str:
    """Extract ORC section number from header like 'Section 124.01|Title'"""
    match = re.search(r'Section\s+(\d+\.\d+)', header)
    return match.group(1) if match else None


# =============================================================================
# OHIO ADMINISTRATIVE CODE (OAC) PATTERNS
# =============================================================================

OAC_PATTERNS = [
    # Primary rule references
    r'[Rr]ules?\s+(\d+-\d+-\d+)',  # "rule 011-1-01" or "Rule 123-4-56"
    r'OAC\s+(\d+-\d+-\d+)',  # "OAC 123-4-56"
    r'Ohio\s+Adm\.?\s+Code\s+(\d+-\d+-\d+)',  # "Ohio Adm. Code 123-4-56"
    r'administrative\s+code\s+(?:section\s+)?(\d+-\d+-\d+)',  # "administrative code section 123-4-56"
    r'(?<!\d)(\d{3,4}-\d+-\d+)(?!\d)',  # Standalone like "123-4-56"

    # ORC references from within OAC (Admin Code frequently cites Revised Code)
    r'section\s*(\d+\.\d+)\s*of\s*the\s*Revised\s*Code',  # "section 121.22 of the Revised Code"
    r'division\s*\([A-Z]\d*\)\s+of\s+section\s*(\d+\.\d+)',  # "division (F) of section121.22"
    r'R\.?C\.?\s+(\d+\.\d+)',  # "R.C. 124.01"
]

def extract_oac_rule_number(header: str) -> str:
    """Extract OAC rule number from header like 'Rule 011-1-01|Title'"""
    match = re.search(r'Rule\s+(\d+-\d+-\d+)', header)
    return match.group(1) if match else None


# =============================================================================
# OHIO CONSTITUTION PATTERNS
# =============================================================================

CONSTITUTION_PATTERNS = [
    # Article and section references
    r'[Aa]rticle\s+([IVXLCDM]+),?\s+[Ss]ection\s+(\d+[a-z]?)',  # "Article I, Section 1"
    r'[Aa]rt\.?\s+([IVXLCDM]+),?\s+[Ss]ec\.?\s+(\d+[a-z]?)',  # "Art. I, Sec. 1"
    r'[Aa]rticle\s+(\d+),?\s+[Ss]ection\s+(\d+[a-z]?)',  # "Article 1, Section 1"
    r'Ohio\s+Const(?:itution)?\.\s+[Aa]rt\.?\s+([IVXLCDM]+),?\s+§\s*(\d+[a-z]?)',  # "Ohio Const. Art. I, § 1"

    # ORC references from Constitution
    r'[Ss]ections?\s+(\d+\.\d+)',  # "section 124.01"
    r'(?:Chapter\s+)?(\d{3,4})\.\s+of\s+the\s+Revised\s+Code',  # "Chapter 119. of the Revised Code"
]

def extract_constitution_section(header: str) -> str:
    """Extract constitution section from header like 'Article I, Section 1|Title'"""
    # Match "Article I, Section 1" format
    match = re.search(r'Article\s+([IVXLCDM]+),\s+Section\s+(\d+[a-z]?)', header)
    if match:
        return f"{match.group(1)}-{match.group(2)}"  # Returns "I-1"
    return None


# =============================================================================
# OHIO CASE LAW PATTERNS
# =============================================================================

CASE_LAW_PATTERNS = [
    # ORC citations
    r'R\.?C\.?\s+§?\s*(\d+\.\d+)',  # "R.C. 2903.01" or "RC § 2903.01"
    r'ORC\s+§?\s*(\d+\.\d+)',  # "ORC 2903.01"
    r'[Ss]ection\s+(\d+\.\d+)\s+of\s+the\s+Revised\s+Code',  # "section 2903.01 of the Revised Code"
    r'Ohio\s+Rev\.?\s+Code\s+(?:§|Ann\.)?\s*(\d+\.\d+)',  # "Ohio Rev. Code 2903.01"
    r'(?:Swan\'?s|Page\'?s)\s+Stat\.?\s+(\d+)',  # Historical: "Swan's Stat. 230"

    # OAC citations
    r'Ohio\s+Adm\.?\s+Code\s+(\d+-\d+-\d+)',  # "Ohio Adm. Code 123-4-56"
    r'OAC\s+(\d+-\d+-\d+)',  # "OAC 123-4-56"
    r'[Rr]ule\s+(\d+-\d+-\d+)',  # "rule 123-4-56"

    # Constitution citations
    r'Ohio\s+Const(?:itution)?\.?,?\s+[Aa]rt(?:icle)?\.?\s+([IVXLCDM]+),?\s+§?\s*(\d+[a-z]?)',  # "Ohio Constitution, Art. I, § 1"
    r'[Aa]rticle\s+([IVXLCDM]+),?\s+[Ss]ection\s+(\d+[a-z]?)',  # "Article I, Section 1"

    # Case citations (for cross-references between cases)
    r'(\d+)\s+(Ohio\s+St\.?\s*(?:\d+d)?)\s+(\d+)',  # "123 Ohio St. 456" or "123 Ohio St. 2d 456"
    r'(\d+)\s+(Ohio\s+App\.?\s*(?:\d+d)?)\s+(\d+)',  # "123 Ohio App. 456"
    r'(\d+)\s+(N\.?E\.?(?:\s*\d+d)?)\s+(\d+)',  # "123 N.E. 456" or "123 N.E.2d 456"
    r'(\d+)\s+(Ohio)\s+(\d+)',  # "20 Ohio 1" (older format)
]

def extract_case_identifier(doc: Dict) -> str:
    """
    Extract case identifier from case law document
    Uses case_id as primary identifier, falls back to citation
    """
    case_id = doc.get('case_id')
    if case_id:
        return f"case_{case_id}"

    # Fallback to citation if available
    citation = doc.get('citation', '')
    if citation:
        # Normalize citation: "20 Ohio 1" -> "20_Ohio_1"
        return citation.replace(' ', '_').replace('.', '')

    return None


# =============================================================================
# REFERENCE TYPE DETECTION
# =============================================================================

def classify_reference(ref: str) -> str:
    """
    Classify what type of reference this is based on format
    Returns: 'orc', 'oac', 'constitution', 'case', 'unknown'
    """
    # ORC format: digits.digits (e.g., "2903.01")
    if re.match(r'^\d{3,4}\.\d+$', ref):
        return 'orc'

    # OAC format: digits-digits-digits (e.g., "123-4-56")
    if re.match(r'^\d+-\d+-\d+$', ref):
        return 'oac'

    # Constitution format: Roman-digits (e.g., "I-1")
    if re.match(r'^[IVXLCDM]+-\d+[a-z]?$', ref):
        return 'constitution'

    # Case format: case_digits or citation format
    if ref.startswith('case_') or '_' in ref:
        return 'case'

    return 'unknown'


# =============================================================================
# CORPUS CONFIGURATIONS
# =============================================================================

CORPUS_CONFIGS = {
    'ohio_revised': {
        'name': 'Ohio Revised Code',
        'patterns': ORC_PATTERNS,
        'extract_id': extract_orc_section_number,
        'file_pattern': 'ohio_revised_code_complete.jsonl',
        'id_format': r'^\d{3,4}\.\d+$',
    },

    'ohio_administration': {
        'name': 'Ohio Administrative Code',
        'patterns': OAC_PATTERNS,
        'extract_id': extract_oac_rule_number,
        'file_pattern': 'ohio_admin_code_complete.jsonl',
        'id_format': r'^\d+-\d+-\d+$',
    },

    'ohio_constitution': {
        'name': 'Ohio Constitution',
        'patterns': CONSTITUTION_PATTERNS,
        'extract_id': extract_constitution_section,
        'file_pattern': 'ohio_constitution_complete.jsonl',
        'id_format': r'^[IVXLCDM]+-\d+[a-z]?$',
    },

    'ohio_case_law': {
        'name': 'Ohio Case Law',
        'patterns': CASE_LAW_PATTERNS,
        'extract_id': extract_case_identifier,
        'file_pattern': 'ohio_case_law_complete.jsonl',
        'id_format': r'^(case_\d+|[\w_]+)$',
    }
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_corpus_config(corpus_name: str) -> Dict:
    """Get configuration for a specific corpus"""
    if corpus_name not in CORPUS_CONFIGS:
        raise ValueError(f"Unknown corpus: {corpus_name}. Available: {list(CORPUS_CONFIGS.keys())}")
    return CORPUS_CONFIGS[corpus_name]


def extract_all_references(text: str, patterns: List[str]) -> Set[str]:
    """
    Extract all references from text using provided patterns
    Returns normalized set of reference identifiers
    """
    references = set()

    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                # Filter out empty strings from tuple
                match = tuple(m for m in match if m)

                # Handle multi-group matches
                if len(match) == 2:
                    # Check if second element looks like a section number (digits)
                    if re.match(r'^\d+[a-z]?$', match[1]):
                        # Article + Section pattern - format as "Article-Section" (e.g., "I-1")
                        references.add(f"{match[0]}-{match[1]}")
                    else:
                        # Range pattern like "124.01 to 124.64"
                        references.add(match[0])
                        references.add(match[1])
                elif len(match) == 3:  # Case citation pattern (volume, reporter, page)
                    # Format as "volume_reporter_page" (e.g., "20_Ohio_1")
                    references.add(f"{match[0]}_{match[1]}_{match[2]}")
                elif len(match) == 1:
                    references.add(match[0])
            else:
                references.add(match)

    return references


def validate_reference(ref: str, id_format: str) -> bool:
    """Validate that a reference matches the expected format"""
    return bool(re.match(id_format, ref.strip()))


# =============================================================================
# TESTING EXAMPLES
# =============================================================================

if __name__ == "__main__":
    # Test ORC patterns
    orc_text = "This section references sections 124.01 to 124.64 and division (A) of section 124.23. See also Chapter 119. of the Revised Code and R.C. 2903.01."
    orc_refs = extract_all_references(orc_text, ORC_PATTERNS)
    print(f"ORC References: {orc_refs}")

    # Test OAC patterns
    oac_text = "This rule is adopted under authority of section121.22of the Revised Code. See also rule 123-4-56 and OAC 789-10-11."
    oac_refs = extract_all_references(oac_text, OAC_PATTERNS)
    print(f"OAC References: {oac_refs}")

    # Test Constitution patterns
    const_text = "Article I, Section 1 and Art. IV, Sec. 2 of the Ohio Constitution reference section 124.01 of the Revised Code."
    const_refs = extract_all_references(const_text, CONSTITUTION_PATTERNS)
    print(f"Constitution References: {const_refs}")

    # Test Case Law patterns
    case_text = "This case cites R.C. 2903.01, Ohio Adm. Code 123-4-56, Ohio Constitution, Art. I, § 1, and 20 Ohio 1. See also 123 Ohio St. 456."
    case_refs = extract_all_references(case_text, CASE_LAW_PATTERNS)
    print(f"Case Law References: {case_refs}")

    # Test classification
    print(f"\nClassification:")
    print(f"  '2903.01' -> {classify_reference('2903.01')}")
    print(f"  '123-4-56' -> {classify_reference('123-4-56')}")
    print(f"  'I-1' -> {classify_reference('I-1')}")
    print(f"  'case_500105' -> {classify_reference('case_500105')}")
