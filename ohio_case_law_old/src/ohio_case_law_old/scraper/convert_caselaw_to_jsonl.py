#!/usr/bin/env python3
"""
PRODUCTION VERSION: Convert all Ohio case law JSON to JSONL format
Recursively processes all reporter directories (ohio, ohio-app, ohio-st-2d, etc.)
"""

import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


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


def extract_case_record(case: Dict[str, Any], reporter: str) -> Dict[str, Any]:
    """
    Extract essential fields for legal research and citation analysis.

    Args:
        case: Case JSON object
        reporter: Reporter name (ohio, ohio-st-2d, etc.) for tracking source

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
        'reporter': reporter,  # Track which reporter this came from
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


def process_reporter_directory(reporter_path: Path, output_file: Path) -> tuple[int, int]:
    """
    Process all JSON files in a single reporter directory.

    Returns:
        (success_count, error_count)
    """
    json_dir = reporter_path / "extracted/json"

    if not json_dir.exists():
        return (0, 0)

    reporter_name = reporter_path.name
    json_files = sorted(json_dir.glob('*.json'))

    success = 0
    errors = 0

    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                case = json.load(f)

            record = extract_case_record(case, reporter_name)

            with open(output_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')

            success += 1

        except Exception as e:
            errors += 1
            print(f"  ERROR: {json_file.name} - {e}")

    return (success, errors)


def convert_all_reporters():
    """
    Recursively process all reporter directories and combine into single JSONL.
    """
    # Paths
    BASE_DIR = Path("/ohio_case_law")
    INPUT_ROOT = BASE_DIR / "data/pre_enriched_input"
    OUTPUT_FILE = BASE_DIR / "data/ohio_case_law_complete.jsonl"

    # Clear output file if exists
    if OUTPUT_FILE.exists():
        OUTPUT_FILE.unlink()

    print(f"Ohio Case Law JSONL Converter")
    print(f"{'=' * 80}\n")
    print(f"Starting conversion: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Find all reporter directories
    reporter_dirs = sorted([d for d in INPUT_ROOT.iterdir() if d.is_dir()])

    print(f"Found {len(reporter_dirs)} reporter directories:\n")
    for d in reporter_dirs:
        print(f"  - {d.name}")
    print()

    # Process each reporter
    total_success = 0
    total_errors = 0
    reporter_stats = []

    for idx, reporter_dir in enumerate(reporter_dirs, 1):
        reporter_name = reporter_dir.name
        print(f"[{idx}/{len(reporter_dirs)}] Processing {reporter_name}...", end=" ", flush=True)

        success, errors = process_reporter_directory(reporter_dir, OUTPUT_FILE)

        total_success += success
        total_errors += errors
        reporter_stats.append({
            'reporter': reporter_name,
            'success': success,
            'errors': errors
        })

        print(f"{success} cases processed, {errors} errors")

    print(f"\n{'=' * 80}")
    print(f"CONVERSION COMPLETE: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 80}\n")

    print(f"Total cases processed: {total_success:,}")
    print(f"Total errors: {total_errors:,}")
    print(f"Output file: {OUTPUT_FILE}\n")

    # Validate output
    with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
        line_count = sum(1 for _ in f)
    print(f"JSONL lines written: {line_count:,}")

    # Show breakdown by reporter
    print(f"\nBreakdown by reporter:")
    print(f"{'-' * 60}")
    for stat in reporter_stats:
        if stat['success'] > 0:
            print(f"  {stat['reporter']:20s} : {stat['success']:>6,} cases")

    # Show sample from output
    print(f"\n{'=' * 80}")
    print("SAMPLE RECORDS:")
    print(f"{'=' * 80}\n")

    with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
        for i in range(min(3, line_count)):
            record = json.loads(f.readline())
            print(f"Case {i + 1}:")
            print(f"  Name: {record['name']}")
            print(f"  Citation: {record['citation']}")
            print(f"  Reporter: {record['reporter']}")
            print(f"  Court: {record['court_name']}")
            print(f"  Date: {record['decision_date']}")
            print(f"  Cites: {len(record['cites_to'])} cases")
            print(f"  Opinion: {record['word_count']:,} words")
            print(f"  PageRank: {record['pagerank_percentile']:.2f} percentile")
            print()


if __name__ == "__main__":
    convert_all_reporters()