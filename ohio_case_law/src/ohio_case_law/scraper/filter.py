"""
Dead-simple case law quality filter.
Removes procedural garbage, keeps substantive opinions.

Usage:
    python -m ohio_case_law.filter
"""

import json
from pathlib import Path
from collections import defaultdict

# ============================================================================
# CONFIGURATION - Adjust these if needed
# ============================================================================

INPUT_FILE = "/Users/justinrussell/active_projects/LEGAL/ohio_code/ohio_case_law/src/ohio_case_law/data/jsonl_output/ohio_case_law_complete.jsonl"
OUTPUT_FILE = "/Users/justinrussell/active_projects/LEGAL/ohio_code/ohio_case_law/src/ohio_case_law/data/jsonl_output/ohio_case_law_filtered.jsonl"

# Quality thresholds
MIN_WORD_COUNT = 500               # Absolute minimum - anything shorter is definitely junk
SUBSTANTIVE_WORD_COUNT = 1000      # Preferred length for full substantive opinions
HIGH_AUTHORITY_THRESHOLD = 0.5     # PageRank threshold for keeping short but influential cases
MIN_CITATIONS = 0                  # Minimum citations (0 = any citations acceptable)
MIN_PAGERANK = 0.0                 # Minimum PageRank (0 = any PageRank acceptable)
EARLY_CASE_YEAR = 1900             # Old cases exempt from citation requirement

# Known junk reporters (optional - leave empty if unsure)
EXCLUDE_REPORTERS = []  # e.g., ["ohio-misc", "ohio-np"]


# ============================================================================
# FILTER LOGIC
# ============================================================================

def is_good_case(case):
    """
    Returns True if case is substantive opinion worth keeping.
    Returns False if procedural garbage.
    """

    word_count = case.get('word_count', 0)
    citation_count = case.get('citation_count', 0)
    pagerank = case.get('pagerank_percentile', 0.0)
    reporter = case.get('reporter', '')
    decision_date = case.get('decision_date', '')

    # Parse year
    try:
        year = int(decision_date.split('-')[0]) if decision_date else 9999
    except:
        year = 9999

    # EARLY EXIT: High authority cases are ALWAYS valuable
    # Even if short (per curiam opinions, procedural precedents from Supreme Court)
    if pagerank >= HIGH_AUTHORITY_THRESHOLD:
        return True

    # Filter 1: Too short (motion orders, administrative stays)
    if word_count < MIN_WORD_COUNT:
        return False

    # Filter 2: Excluded reporters
    if reporter in EXCLUDE_REPORTERS:
        return False

    # Filter 3: Modern cases with no citations AND no authority (likely junk)
    if year >= EARLY_CASE_YEAR:
        has_citations = citation_count > MIN_CITATIONS
        has_authority = pagerank > MIN_PAGERANK
        if not (has_citations or has_authority):
            return False

    # Filter 4: Zero PageRank + short = always junk
    # (Keep original logic - don't be more restrictive)
    if pagerank == 0.0 and word_count < SUBSTANTIVE_WORD_COUNT:
        return False

    return True


def filter_cases():
    """Main filtering function - reads input, filters, writes output."""

    input_path = Path(INPUT_FILE)
    output_path = Path(OUTPUT_FILE)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("OHIO CASE LAW QUALITY FILTER")
    print("=" * 80)
    print(f"\nInput:  {input_path}")
    print(f"Output: {output_path}")
    print(f"\nCriteria:")
    print(f"  • Minimum words: {MIN_WORD_COUNT}")
    print(f"  • Require citations OR authority for cases after {EARLY_CASE_YEAR}")
    if EXCLUDE_REPORTERS:
        print(f"  • Excluding reporters: {', '.join(EXCLUDE_REPORTERS)}")
    print("\nFiltering...\n")

    # Statistics tracking
    total = 0
    kept = 0
    reasons = defaultdict(int)
    reporter_stats = defaultdict(lambda: {'total': 0, 'kept': 0})

    # Process file
    with open(input_path, 'r', encoding='utf-8') as infile, \
            open(output_path, 'w', encoding='utf-8') as outfile:

        for line_num, line in enumerate(infile, 1):
            try:
                case = json.loads(line)
                total += 1

                reporter = case.get('reporter', 'unknown')
                reporter_stats[reporter]['total'] += 1

                if is_good_case(case):
                    outfile.write(line)
                    kept += 1
                    reporter_stats[reporter]['kept'] += 1
                else:
                    # Track why rejected (for debugging)
                    word_count = case.get('word_count', 0)
                    if word_count < MIN_WORD_COUNT:
                        reasons['too_short'] += 1
                    elif case.get('pagerank_percentile', 0) == 0 and word_count < 1000:
                        reasons['zero_authority'] += 1
                    else:
                        reasons['no_citations'] += 1

                # Progress update
                if line_num % 1000 == 0:
                    pct = (kept / total) * 100
                    print(f"  Processed {line_num:,} | Kept {kept:,} ({pct:.1f}%)")

            except Exception as e:
                print(f"  ⚠ Line {line_num} error: {e}")
                continue

    # Print results
    keep_pct = (kept / total) * 100
    reject_pct = 100 - keep_pct

    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    print(f"\nTotal cases:     {total:,}")
    print(f"Kept:            {kept:,} ({keep_pct:.1f}%)")
    print(f"Rejected:        {total - kept:,} ({reject_pct:.1f}%)")

    print(f"\nRejection reasons:")
    for reason, count in reasons.items():
        pct = (count / total) * 100
        print(f"  {reason:20s} {count:6,} ({pct:5.1f}%)")

    print(f"\nTop reporters kept:")
    sorted_reporters = sorted(
        reporter_stats.items(),
        key=lambda x: x[1]['kept'],
        reverse=True
    )
    for reporter, stats in sorted_reporters[:10]:
        rate = (stats['kept'] / stats['total'] * 100) if stats['total'] > 0 else 0
        print(f"  {reporter:25s} {stats['kept']:5,} / {stats['total']:5,} ({rate:5.1f}%)")

    print(f"\n✓ Filtered cases written to: {output_path}")
    print("=" * 80 + "\n")


if __name__ == '__main__':
    filter_cases()