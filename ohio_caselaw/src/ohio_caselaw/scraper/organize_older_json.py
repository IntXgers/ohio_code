#!/usr/bin/env python3
"""
Organize JSON files from 'older' folder into hierarchical court structure
Matches Ohio court system: Supreme Court → Appeals → County → Municipal → Historical → Federal
"""
import json
import shutil
import re
from pathlib import Path
from collections import defaultdict

# Configuration
OLDER_CORPUS = Path("/Volumes/Jnice4tb/ohio_scotus_caselaw/older")
JSON_OUTPUT = Path("/Volumes/Jnice4tb/ohio_scotus_caselaw/json")

def normalize_county_name(county_name):
    """
    Extract and normalize county name
    'Cuyahoga County Court of Common Pleas' -> 'cuyahoga'
    """
    # Remove common suffixes
    county = county_name.lower()
    county = re.sub(r'\s*(county|circuit|court).*$', '', county)
    county = county.strip().replace(' ', '-')
    return county

def normalize_city_name(city_name):
    """
    Extract and normalize city name
    'Cincinnati Municipal Court' -> 'cincinnati'
    """
    city = city_name.lower()
    city = re.sub(r'\s*(municipal|city|police).*$', '', city)
    city = city.strip().replace(' ', '-')
    return city

def determine_target_directory(court_name, year):
    """
    Determine target directory based on hierarchical court structure

    Structure:
    - supreme-court/YYYY/
    - appeals-courts/district-NN/YYYY/
    - county-courts/county-name/court-type/YYYY/
    - municipal-courts/city-name/YYYY/
    - historical-courts/circuit/county-name/YYYY/
    - federal-courts/court-name/YYYY/
    - other-courts/court-type/YYYY/

    Returns:
        Path or None if court should be skipped
    """
    court_lower = court_name.lower()

    # 1. SUPREME COURT OF OHIO
    if 'supreme court of ohio' in court_lower:
        return JSON_OUTPUT / 'supreme-court' / year

    # 2. OHIO COURT OF APPEALS (Appellate Districts)
    elif 'court of appeals' in court_lower and 'ohio' in court_lower:
        # Try to extract district number from court name
        # "Court of Appeals of Ohio, First Appellate District" -> district-01
        district_match = re.search(r'(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth)', court_lower)
        if district_match:
            district_map = {
                'first': '01', 'second': '02', 'third': '03', 'fourth': '04',
                'fifth': '05', 'sixth': '06', 'seventh': '07', 'eighth': '08',
                'ninth': '09', 'tenth': '10', 'eleventh': '11', 'twelfth': '12'
            }
            district_num = district_map[district_match.group(1)]
            return JSON_OUTPUT / 'appeals-courts' / f'district-{district_num}' / year
        else:
            # Generic appeals court (no district specified)
            return JSON_OUTPUT / 'appeals-courts' / 'general' / year

    # 3. OHIO COURT OF CLAIMS
    elif 'court of claims' in court_lower and 'ohio' in court_lower:
        return JSON_OUTPUT / 'state-courts' / 'court-of-claims' / year

    # 4. CIRCUIT COURTS (Historical, abolished 1912)
    elif 'circuit court' in court_lower or 'circuit' in court_name and 'Court' in court_name:
        county = normalize_county_name(court_name)
        if county and county != 'ohio':  # Specific county circuit court
            return JSON_OUTPUT / 'historical-courts' / 'circuit' / county / year
        else:  # Ohio Circuit Court (general)
            return JSON_OUTPUT / 'historical-courts' / 'circuit' / 'general' / year

    # 5. COUNTY COURTS - COMMON PLEAS
    elif 'common pleas' in court_lower or 'court of common pleas' in court_lower:
        county = normalize_county_name(court_name)
        if county:
            return JSON_OUTPUT / 'county-courts' / county / 'common-pleas' / year
        else:
            return JSON_OUTPUT / 'county-courts' / 'unknown' / 'common-pleas' / year

    # 6. COUNTY COURTS - PROBATE
    elif 'probate' in court_lower:
        county = normalize_county_name(court_name)
        if county:
            return JSON_OUTPUT / 'county-courts' / county / 'probate' / year
        else:
            return JSON_OUTPUT / 'county-courts' / 'unknown' / 'probate' / year

    # 7. COUNTY COURTS - JUVENILE
    elif 'juvenile' in court_lower:
        county = normalize_county_name(court_name)
        if county:
            return JSON_OUTPUT / 'county-courts' / county / 'juvenile' / year
        else:
            return JSON_OUTPUT / 'county-courts' / 'unknown' / 'juvenile' / year

    # 8. MUNICIPAL COURTS
    elif 'municipal court' in court_lower or 'police court' in court_lower:
        city = normalize_city_name(court_name)
        if city:
            return JSON_OUTPUT / 'municipal-courts' / city / year
        else:
            return JSON_OUTPUT / 'municipal-courts' / 'unknown' / year

    # 9. SUPERIOR COURTS (Historical)
    elif 'superior court' in court_lower:
        city = normalize_city_name(court_name)
        if city:
            return JSON_OUTPUT / 'historical-courts' / 'superior' / city / year
        else:
            return JSON_OUTPUT / 'historical-courts' / 'superior' / 'general' / year

    # 10. FEDERAL COURTS
    elif 'united states' in court_lower or 'federal' in court_lower:
        if 'sixth circuit' in court_lower or 'court of appeals for the sixth circuit' in court_lower:
            return JSON_OUTPUT / 'federal-courts' / 'sixth-circuit' / year
        elif 'northern district of ohio' in court_lower:
            return JSON_OUTPUT / 'federal-courts' / 'district-northern' / year
        elif 'southern district of ohio' in court_lower:
            return JSON_OUTPUT / 'federal-courts' / 'district-southern' / year
        else:
            # Other federal courts
            return JSON_OUTPUT / 'federal-courts' / 'other' / year

    # 11. STATE AGENCIES/BOARDS
    elif 'board of tax appeals' in court_lower or 'tax appeals' in court_lower:
        return JSON_OUTPUT / 'state-agencies' / 'board-of-tax-appeals' / year
    elif 'public utilities commission' in court_lower:
        return JSON_OUTPUT / 'state-agencies' / 'public-utilities' / year
    elif 'civil rights commission' in court_lower:
        return JSON_OUTPUT / 'state-agencies' / 'civil-rights' / year
    elif 'racing commission' in court_lower:
        return JSON_OUTPUT / 'state-agencies' / 'racing' / year

    # 12. OUT OF STATE COURTS (for reference cases)
    elif 'supreme court' in court_lower and 'ohio' not in court_lower:
        # Other state supreme courts or SCOTUS
        if 'united states' in court_lower:
            return JSON_OUTPUT / 'federal-courts' / 'supreme-court-us' / year
        else:
            return JSON_OUTPUT / 'out-of-state' / 'supreme-courts' / year

    # 13. MISCELLANEOUS/OTHER
    else:
        return JSON_OUTPUT / 'other-courts' / 'miscellaneous' / year

def extract_court_and_year(json_file):
    """
    Extract court name and decision year from JSON file

    Returns:
        tuple: (court_name, year) or (None, None) on error
    """
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Extract year from decision_date
        decision_date = data.get('decision_date', '')
        year = decision_date[:4] if decision_date else None

        # Extract court name
        court = data.get('court', {})
        court_name = court.get('name', None)

        return court_name, year

    except Exception as e:
        print(f"    ERROR reading {json_file.name}: {e}")
        return None, None

def organize_older_files():
    """
    Move and organize all JSON files from older folder into modern structure
    """
    print("=" * 100)
    print("ORGANIZING OLDER CASE LAW JSON FILES")
    print("=" * 100)
    print(f"\nSource: {OLDER_CORPUS}")
    print(f"Target: {JSON_OUTPUT}\n")

    # Statistics
    stats = {
        'total_processed': 0,
        'total_moved': 0,
        'total_skipped': 0,
        'total_errors': 0,
        'by_destination': defaultdict(int),
        'errors': []
    }

    # Find all reporter directories
    reporter_dirs = sorted([d for d in OLDER_CORPUS.iterdir() if d.is_dir() and d.name.startswith('ohio')])

    print(f"Found {len(reporter_dirs)} reporter directories\n")

    # Process each reporter directory
    for reporter_idx, reporter_dir in enumerate(reporter_dirs, 1):
        reporter_name = reporter_dir.name
        json_dir = reporter_dir / "extracted" / "json"

        if not json_dir.exists():
            continue

        json_files = list(json_dir.glob("*.json"))

        if not json_files:
            continue

        print(f"\n[{reporter_idx}/{len(reporter_dirs)}] {reporter_name}: {len(json_files)} files")
        print(f"{'='*100}")

        # Process each JSON file
        for file_idx, json_file in enumerate(json_files, 1):
            stats['total_processed'] += 1

            # Extract metadata
            court_name, year = extract_court_and_year(json_file)

            if not court_name or not year:
                stats['total_skipped'] += 1
                if file_idx % 100 == 0 or file_idx == len(json_files):
                    print(f"  Progress: {file_idx}/{len(json_files)} files...", end="\r")
                continue

            # Determine target directory
            target_dir = determine_target_directory(court_name, year)

            if not target_dir:
                stats['total_skipped'] += 1
                if file_idx % 100 == 0 or file_idx == len(json_files):
                    print(f"  Progress: {file_idx}/{len(json_files)} files...", end="\r")
                continue

            # Create target directory
            target_dir.mkdir(parents=True, exist_ok=True)

            # Copy file (use copy instead of move to preserve originals)
            target_file = target_dir / json_file.name

            try:
                # Check if file already exists
                if target_file.exists():
                    # File exists, skip
                    stats['total_skipped'] += 1
                else:
                    shutil.copy2(json_file, target_file)
                    stats['total_moved'] += 1
                    stats['by_destination'][str(target_dir.relative_to(JSON_OUTPUT))] += 1

                # Progress indicator
                if file_idx % 100 == 0 or file_idx == len(json_files):
                    print(f"  Progress: {file_idx}/{len(json_files)} files (moved: {stats['total_moved']}, skipped: {stats['total_skipped']})", end="\r")

            except Exception as e:
                stats['total_errors'] += 1
                error_msg = f"{json_file.name}: {str(e)}"
                stats['errors'].append(error_msg)
                print(f"\n  ERROR: {error_msg}")

        print(f"\n  Completed: {len(json_files)} files processed")

    # Print summary
    print("\n" + "=" * 100)
    print("ORGANIZATION COMPLETE")
    print("=" * 100)
    print(f"\nTotal processed: {stats['total_processed']:,}")
    print(f"Total moved: {stats['total_moved']:,}")
    print(f"Total skipped: {stats['total_skipped']:,}")
    print(f"Total errors: {stats['total_errors']:,}")

    # Destination breakdown
    print(f"\n{'='*100}")
    print("FILES BY DESTINATION")
    print(f"{'='*100}")

    sorted_destinations = sorted(stats['by_destination'].items(), key=lambda x: x[1], reverse=True)
    for dest, count in sorted_destinations[:50]:  # Show top 50
        print(f"{dest:60s} : {count:>6,} files")

    if len(sorted_destinations) > 50:
        print(f"\n... and {len(sorted_destinations) - 50} more destinations")

    # Errors
    if stats['errors']:
        print(f"\n{'='*100}")
        print(f"ERRORS ({len(stats['errors'])})")
        print(f"{'='*100}")
        for error in stats['errors'][:20]:
            print(f"  {error}")
        if len(stats['errors']) > 20:
            print(f"\n... and {len(stats['errors']) - 20} more errors")

    print("\n" + "=" * 100)

if __name__ == "__main__":
    organize_older_files()