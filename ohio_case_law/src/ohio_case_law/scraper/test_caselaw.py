#!/usr/bin/env python3
"""
TEST VERSION: Convert Ohio case law JSON to JSONL format
Processes only 3 files from ohio directory for validation
"""

import json
from pathlib import Path
from typing import Dict, List, Any


def extract_opinion_text(casebody: Dict[str, Any]) -> str:
    """
    Extract and concatenate all opinion texts.
    Multiple opinions (majority, dissent, concurrence) merged into single text.
    """
    if not casebody or 'opinions' not in casebody:
        return ""

    opinion_texts = []
    for opinion in casebody.get('opinions', []):
        text = opinion.get('text', '').strip()
        if text:
            # Prefix with opinion type and author if available
            opinion_type = opinion.get('type', 'opinion')
            author = opinion.get('author')

            header = f"[{opinion_type.upper()}"
            if author:
                header += f" - {author}"
            header += "]\n"

            opinion_texts.append(header + text)

    return "\n\n".join(opinion_texts)


def extract_case_record(case: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract essential fields for legal research and citation analysis.

    Returns JSONL record with:
    - Identifying metadata
    - Full opinion text
    - Complete citation network (precedent graph)
    - Authority metrics
    """

    # Core identification
    record = {
        'case_id': case.get('id'),
        'name': case.get('name', ''),
        'name_abbreviation': case.get('name_abbreviation', ''),
        'decision_date': case.get('decision_date', ''),
        'docket_number': case.get('docket_number', ''),
    }

    # Official citation (primary identifier for legal research)
    citations = case.get('citations', [])
    official_cite = next(
        (c['cite'] for c in citations if c.get('type') == 'official'),
        citations[0]['cite'] if citations else ''
    )
    record['citation'] = official_cite
    record['all_citations'] = [c['cite'] for c in citations]

    # Court hierarchy (critical for precedent weight)
    court = case.get('court', {})
    record['court_name'] = court.get('name', '')
    record['court_abbreviation'] = court.get('name_abbreviation', '')
    record['court_id'] = court.get('id')

    # Jurisdiction
    jurisdiction = case.get('jurisdiction', {})
    record['jurisdiction'] = jurisdiction.get('name', '')

    # Full opinion text (all opinions concatenated)
    casebody = case.get('casebody', {})
    record['opinion_text'] = extract_opinion_text(casebody)

    # Additional casebody elements
    record['parties'] = casebody.get('parties', [])
    record['judges'] = casebody.get('judges', [])
    record['attorneys'] = casebody.get('attorneys', [])
    record['head_matter'] = casebody.get('head_matter', '')

    # Precedent graph - CRITICAL for citation analysis
    # This is what differentiates case law from statutes
    cites_to = case.get('cites_to', [])
    record['cites_to'] = [
        {
            'cite': ref.get('cite', ''),
            'case_ids': ref.get('case_ids', []),
            'case_paths': ref.get('case_paths', []),
            'category': ref.get('category', ''),
            'reporter': ref.get('reporter', ''),
        }
        for ref in cites_to
    ]

    # Authority metrics (for search ranking)
    analysis = case.get('analysis', {})
    record['pagerank_raw'] = analysis.get('pagerank', {}).get('raw', 0.0)
    record['pagerank_percentile'] = analysis.get('pagerank', {}).get('percentile', 0.0)
    record['word_count'] = analysis.get('word_count', 0)
    record['char_count'] = analysis.get('char_count', 0)
    record['citation_count'] = len(cites_to)  # Number of cases cited

    # Provenance
    provenance = case.get('provenance', {})
    record['source'] = provenance.get('source', '')
    record['date_added'] = provenance.get('date_added', '')

    return record


def test_conversion():
    """
    Test conversion on 3 files from ohio directory
    """
    # Paths
    BASE_DIR = Path("/ohio_case_law")
    TEST_INPUT = BASE_DIR / "data/pre_enriched_input/ohio/extracted/json"
    TEST_OUTPUT = BASE_DIR / "data/TEST_OUTPUT.jsonl"

    # Clear output if exists
    if TEST_OUTPUT.exists():
        TEST_OUTPUT.unlink()

    # Get first 3 JSON files
    json_files = sorted(TEST_INPUT.glob('*.json'))[:3]

    if not json_files:
        print(f"ERROR: No JSON files found in {TEST_INPUT}")
        return

    print(f"Testing conversion on {len(json_files)} files from 'ohio' directory:\n")

    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                case = json.load(f)

            record = extract_case_record(case)

            with open(TEST_OUTPUT, 'a', encoding='utf-8') as f:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')

            print(f"✓ {json_file.name}")
            print(f"  Case: {record['name']}")
            print(f"  Citation: {record['citation']}")
            print(f"  Court: {record['court_name']}")
            print(f"  Cites {len(record['cites_to'])} cases")
            print(f"  Opinion: {record['word_count']} words")
            print()

        except Exception as e:
            print(f"✗ {json_file.name}: {e}\n")

    print(f"\nTest output saved to: {TEST_OUTPUT}")
    print("\nValidate the JSONL structure, then run the full converter.")

    # Show a sample of one complete record
    print("\n" + "=" * 80)
    print("SAMPLE RECORD STRUCTURE (first case):")
    print("=" * 80)
    with open(TEST_OUTPUT, 'r', encoding='utf-8') as f:
        sample = json.loads(f.readline())
        # Show structure without full opinion text
        sample_display = {k: v for k, v in sample.items() if k != 'opinion_text'}
        sample_display['opinion_text'] = f"<{len(sample['opinion_text'])} characters>"
        print(json.dumps(sample_display, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    test_conversion()