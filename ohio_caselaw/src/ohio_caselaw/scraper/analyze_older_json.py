#!/usr/bin/env python3
"""
Analyze JSON files in the 'older' folder to determine court and year
for organizing into the modern structure
"""
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Configuration
OLDER_CORPUS = Path("/Volumes/Jnice4tb/ohio_scotus_caselaw/older")

def extract_court_and_year(json_file):
    """
    Extract court name and decision year from JSON file

    Returns:
        tuple: (court_name, year, reporter_folder, citation)
    """
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Extract year from decision_date
        decision_date = data.get('decision_date', '')
        year = decision_date[:4] if decision_date else 'unknown'

        # Extract court name
        court = data.get('court', {})
        court_name = court.get('name', 'Unknown Court')
        court_abbrev = court.get('name_abbreviation', '')

        # Get reporter folder (ohio-st, ohio-app, etc.)
        reporter_folder = json_file.parts[-4]  # Goes up from json/file.json to ohio-*/

        # Get citation
        citations = data.get('citations', [])
        citation = citations[0].get('cite', 'No citation') if citations else 'No citation'

        return court_name, year, reporter_folder, citation, court_abbrev

    except Exception as e:
        return 'ERROR', 'unknown', 'unknown', str(e), ''

def analyze_all_older_files():
    """
    Analyze all JSON files in the older folder
    """
    print("=" * 100)
    print("ANALYZING OLDER CASE LAW JSON FILES")
    print("=" * 100)
    print(f"\nSource: {OLDER_CORPUS}\n")

    # Track statistics
    stats = {
        'total_files': 0,
        'by_reporter': defaultdict(int),
        'by_court': defaultdict(int),
        'by_year': defaultdict(int),
        'by_reporter_and_court': defaultdict(lambda: defaultdict(int)),
        'reporter_to_court_mapping': defaultdict(set),
        'year_range': defaultdict(lambda: {'min': 9999, 'max': 0}),
        'errors': []
    }

    # Find all reporter directories (ohio-st, ohio-app, etc.)
    reporter_dirs = sorted([d for d in OLDER_CORPUS.iterdir() if d.is_dir() and d.name.startswith('ohio')])

    print(f"Found {len(reporter_dirs)} reporter directories:\n")

    # Process each reporter directory
    for reporter_dir in reporter_dirs:
        reporter_name = reporter_dir.name
        json_dir = reporter_dir / "extracted" / "json"

        if not json_dir.exists():
            print(f"⚠️  {reporter_name}: No JSON directory found")
            continue

        json_files = list(json_dir.glob("*.json"))

        if not json_files:
            print(f"⚠️  {reporter_name}: No JSON files found")
            continue

        print(f"\n{'='*100}")
        print(f"Reporter: {reporter_name}")
        print(f"{'='*100}")
        print(f"Found {len(json_files)} JSON files")

        # Process all files
        print(f"Processing all {len(json_files)} files...", end=" ", flush=True)

        for idx, json_file in enumerate(json_files, 1):
            court_name, year, reporter, citation, court_abbrev = extract_court_and_year(json_file)

            # Update stats
            stats['total_files'] += 1
            stats['by_reporter'][reporter_name] += 1
            stats['by_court'][court_name] += 1
            stats['by_year'][year] += 1
            stats['by_reporter_and_court'][reporter_name][court_name] += 1
            stats['reporter_to_court_mapping'][reporter_name].add(court_name)

            if year != 'unknown' and year != 'ERROR':
                try:
                    year_int = int(year)
                    stats['year_range'][court_name]['min'] = min(stats['year_range'][court_name]['min'], year_int)
                    stats['year_range'][court_name]['max'] = max(stats['year_range'][court_name]['max'], year_int)
                except:
                    pass

            if court_name == 'ERROR':
                stats['errors'].append((str(json_file), citation))

            # Progress indicator
            if idx % 100 == 0:
                print(f"{idx}...", end=" ", flush=True)

        print(f"Done! ({len(json_files)} files processed)")

    # Print comprehensive summary
    print("\n" + "=" * 100)
    print("COMPREHENSIVE ANALYSIS SUMMARY")
    print("=" * 100)

    print(f"\n📊 TOTAL FILES: {stats['total_files']:,}\n")

    # Reporter breakdown
    print(f"\n{'='*100}")
    print("REPORTER DIRECTORIES → COURTS MAPPING")
    print(f"{'='*100}")
    for reporter, courts in sorted(stats['reporter_to_court_mapping'].items()):
        print(f"\n{reporter}:")
        for court in sorted(courts):
            count = stats['by_reporter_and_court'][reporter][court]
            print(f"  → {court:50s} ({count:,} files)")

    # Court breakdown with year ranges
    print(f"\n{'='*100}")
    print("COURTS WITH YEAR RANGES")
    print(f"{'='*100}")
    for court, years in sorted(stats['year_range'].items()):
        if years['min'] != 9999:
            count = stats['by_court'][court]
            print(f"{court:50s} | {years['min']}-{years['max']} | {count:,} files")

    # Year distribution
    print(f"\n{'='*100}")
    print("YEAR DISTRIBUTION (Top 20)")
    print(f"{'='*100}")
    sorted_years = sorted(stats['by_year'].items(), key=lambda x: x[0])
    for year, count in sorted_years[:20]:
        print(f"{year}: {count:,} files")

    # Errors
    if stats['errors']:
        print(f"\n{'='*100}")
        print(f"⚠️  ERRORS ({len(stats['errors'])})")
        print(f"{'='*100}")
        for file_path, error in stats['errors'][:10]:
            print(f"  {file_path}")
            print(f"    Error: {error}")

    print("\n" + "=" * 100)
    print("ANALYSIS COMPLETE")
    print("=" * 100)

if __name__ == "__main__":
    analyze_all_older_files()
