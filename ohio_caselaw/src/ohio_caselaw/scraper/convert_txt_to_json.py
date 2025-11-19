#!/usr/bin/env python3
"""
Transform modern Ohio Supreme Court TXT files to JSON format
Matches CourtListener schema for compatibility
"""
import json
from pathlib import Path
from datetime import datetime
import re

# Configuration
TXT_CORPUS = Path("/Volumes/Jnice4tb/ohio_scotus_caselaw/txt")
JSON_OUTPUT = Path("/Volumes/Jnice4tb/ohio_scotus_caselaw/json")
PROGRESS_FILE = JSON_OUTPUT / "txt_to_json_progress.json"

# Create output directory
JSON_OUTPUT.mkdir(parents=True, exist_ok=True)

# Court directory to ID mapping (for metadata)
COURT_METADATA = {
    'supreme_court_of_ohio': {
        'court_id': 'ohio-supreme',
        'court_name': 'Supreme Court of Ohio',
        'jurisdiction': 'Ohio'
    },
    'first_district_court_of_appeals': {
        'court_id': 'ohio-app-1',
        'court_name': 'Court of Appeals of Ohio, First Appellate District',
        'jurisdiction': 'Ohio'
    },
    'second_district_court_of_appeals': {
        'court_id': 'ohio-app-2',
        'court_name': 'Court of Appeals of Ohio, Second Appellate District',
        'jurisdiction': 'Ohio'
    },
    'third_district_court_of_appeals': {
        'court_id': 'ohio-app-3',
        'court_name': 'Court of Appeals of Ohio, Third Appellate District',
        'jurisdiction': 'Ohio'
    },
    'fourth_district_court_of_appeals': {
        'court_id': 'ohio-app-4',
        'court_name': 'Court of Appeals of Ohio, Fourth Appellate District',
        'jurisdiction': 'Ohio'
    },
    'fifth_district_court_of_appeals': {
        'court_id': 'ohio-app-5',
        'court_name': 'Court of Appeals of Ohio, Fifth Appellate District',
        'jurisdiction': 'Ohio'
    },
    'sixth_district_court_of_appeals': {
        'court_id': 'ohio-app-6',
        'court_name': 'Court of Appeals of Ohio, Sixth Appellate District',
        'jurisdiction': 'Ohio'
    },
    'seventh_district_court_of_appeals': {
        'court_id': 'ohio-app-7',
        'court_name': 'Court of Appeals of Ohio, Seventh Appellate District',
        'jurisdiction': 'Ohio'
    },
    'eighth_district_court_of_appeals': {
        'court_id': 'ohio-app-8',
        'court_name': 'Court of Appeals of Ohio, Eighth Appellate District',
        'jurisdiction': 'Ohio'
    },
    'ninth_district_court_of_appeals': {
        'court_id': 'ohio-app-9',
        'court_name': 'Court of Appeals of Ohio, Ninth Appellate District',
        'jurisdiction': 'Ohio'
    },
    'tenth_district_court_of_appeals': {
        'court_id': 'ohio-app-10',
        'court_name': 'Court of Appeals of Ohio, Tenth Appellate District',
        'jurisdiction': 'Ohio'
    },
    'eleventh_district_court_of_appeals': {
        'court_id': 'ohio-app-11',
        'court_name': 'Court of Appeals of Ohio, Eleventh Appellate District',
        'jurisdiction': 'Ohio'
    },
    'twelfth_district_court_of_appeals': {
        'court_id': 'ohio-app-12',
        'court_name': 'Court of Appeals of Ohio, Twelfth Appellate District',
        'jurisdiction': 'Ohio'
    },
    'scotus_court_of_claims': {
        'court_id': 'ohio-claims',
        'court_name': 'Ohio Court of Claims',
        'jurisdiction': 'Ohio'
    },
    'miscellaneous_scotus_opinions': {
        'court_id': 'ohio-misc',
        'court_name': 'Ohio Miscellaneous',
        'jurisdiction': 'Ohio'
    }
}

def load_progress():
    """Load progress tracking"""
    if PROGRESS_FILE.exists():
        try:
            with open(PROGRESS_FILE, 'r') as f:
                return json.load(f)
        except:
            return _fresh_progress()
    return _fresh_progress()

def _fresh_progress():
    """Fresh progress state"""
    return {
        'processed_files': {},
        'total_processed': 0,
        'total_errors': 0,
        'errors': [],
        'started_at': datetime.now().isoformat()
    }

def save_progress(progress):
    """Save progress atomically"""
    progress['last_updated'] = datetime.now().isoformat()

    temp_file = PROGRESS_FILE.with_suffix('.tmp')
    with open(temp_file, 'w') as f:
        json.dump(progress, f, indent=2)

    import os
    os.replace(temp_file, PROGRESS_FILE)

def extract_case_metadata(text, filename):
    """
    Extract metadata from case text
    Looks for citation patterns like [Cite as State v. Smith, 2016-Ohio-462]
    """
    metadata = {
        'case_name': None,
        'citation': None,
        'docket_number': None,
        'decision_date': None
    }

    # Try to extract citation from first line
    # Pattern: [Cite as Name, YYYY-Ohio-NNNN]
    cite_pattern = r'\[Cite as ([^,]+),\s*(\d{4}-Ohio-\d+)\]'
    match = re.search(cite_pattern, text[:500])
    if match:
        metadata['case_name'] = match.group(1).strip()
        metadata['citation'] = match.group(2).strip()

        # Extract year from citation
        year_match = re.search(r'(\d{4})-Ohio', metadata['citation'])
        if year_match:
            year = year_match.group(1)
            # Default to January 1 if we don't have exact date
            metadata['decision_date'] = f"{year}-01-01"

    # Try to extract docket/case number
    # Pattern: CASE NO. XX-XXXX or No. XXXX
    docket_pattern = r'(?:CASE NO\.|Case No\.|No\.)\s*([\w\-]+)'
    docket_match = re.search(docket_pattern, text[:1000])
    if docket_match and docket_match.group(1):
        metadata['docket_number'] = docket_match.group(1).strip()

    # If we couldn't find case name, try filename
    if not metadata['case_name']:
        # Filename might be like "2016-Ohio-462.txt"
        name_match = re.search(r'(\d{4}-Ohio-\d+)', filename)
        if name_match:
            citation = name_match.group(1)
            metadata['citation'] = citation
            metadata['case_name'] = f"Case {citation}"

    return metadata

def txt_to_json(txt_file, court_dir, year):
    """
    Convert single TXT file to JSON format matching CourtListener schema

    Args:
        txt_file: Path to .txt file
        court_dir: Court directory name (e.g., 'supreme_court_of_ohio')
        year: Year string (e.g., '2016')

    Returns:
        dict: JSON representation of case
    """
    # Read text content
    with open(txt_file, 'r', encoding='utf-8') as f:
        text = f.read()

    # Extract metadata from text
    metadata = extract_case_metadata(text, txt_file.name)

    # Get court metadata
    court_info = COURT_METADATA.get(court_dir, {
        'court_id': 'ohio-unknown',
        'court_name': court_dir.replace('_', ' ').title(),
        'jurisdiction': 'Ohio'
    })

    # Generate unique ID from filename
    # Use filename without extension as base ID
    file_id = f"modern-{court_info['court_id']}-{txt_file.stem}"

    # Create JSON structure matching CourtListener format
    case_json = {
        # Basic identification
        'id': file_id,
        'source': 'ohio_supreme_court_scrape',
        'source_file': str(txt_file.relative_to(TXT_CORPUS)),

        # Case names and citations
        'name': metadata.get('case_name', f"Case {txt_file.stem}"),
        'name_abbreviation': metadata.get('case_name', f"Case {txt_file.stem}"),
        'citation': metadata.get('citation'),
        'decision_date': metadata.get('decision_date', f"{year}-01-01"),
        'docket_number': metadata.get('docket_number'),

        # Court information
        'court': {
            'id': court_info['court_id'],
            'name': court_info['court_name'],
            'name_abbreviation': court_info['court_id']
        },

        # Jurisdiction
        'jurisdiction': {
            'id': 'ohio',
            'name': 'Ohio',
            'name_long': 'Ohio'
        },

        # Case body (the actual opinion text)
        'casebody': {
            'opinions': [
                {
                    'text': text,
                    'type': 'majority',
                    'author': None  # Could extract if needed
                }
            ],
            'judges': [],  # Could extract if needed
            'parties': [],
            'attorneys': []
        },

        # Analysis metadata
        'analysis': {
            'char_count': len(text),
            'word_count': len(text.split()),
            'source': 'direct_scrape'
        },

        # Provenance
        'provenance': {
            'source': 'Ohio Supreme Court Website',
            'date_added': datetime.now().isoformat(),
            'scraper_version': '1.0'
        }
    }

    return case_json

def transform_all_txt_to_json():
    """
    Transform all TXT files to JSON format
    Maintains directory structure: court/year/
    """
    progress = load_progress()

    print("=" * 80)
    print("TXT TO JSON TRANSFORMATION")
    print("=" * 80)
    print(f"\nSource: {TXT_CORPUS}")
    print(f"Output: {JSON_OUTPUT}")
    print(f"Previously processed: {progress['total_processed']}\n")

    total_processed = 0
    total_errors = 0

    # Process each court directory
    for court_dir in TXT_CORPUS.iterdir():
        if not court_dir.is_dir():
            continue

        court_name = court_dir.name
        print(f"\n{'='*80}")
        print(f"Processing: {court_name}")
        print(f"{'='*80}")

        # Process each year within court
        for year_dir in sorted(court_dir.iterdir()):
            if not year_dir.is_dir():
                continue

            year = year_dir.name
            print(f"\n  Year: {year}")

            # Find all TXT files
            txt_files = list(year_dir.glob("*.txt"))

            if not txt_files:
                print(f"    No TXT files found")
                continue

            print(f"    Found {len(txt_files)} TXT files")

            # Create output directory
            json_output_dir = JSON_OUTPUT / court_name / year
            json_output_dir.mkdir(parents=True, exist_ok=True)

            # Process each TXT file
            for txt_file in txt_files:
                file_key = str(txt_file.relative_to(TXT_CORPUS))

                # Skip if already processed
                if file_key in progress['processed_files']:
                    continue

                try:
                    # Convert to JSON
                    case_json = txt_to_json(txt_file, court_name, year)

                    # Write JSON file (same name, .json extension)
                    json_file = json_output_dir / f"{txt_file.stem}.json"
                    with open(json_file, 'w', encoding='utf-8') as f:
                        json.dump(case_json, f, indent=2, ensure_ascii=False)

                    # Track progress
                    progress['processed_files'][file_key] = str(json_file.relative_to(JSON_OUTPUT))
                    total_processed += 1
                    progress['total_processed'] += 1

                    # Save progress every 100 files
                    if total_processed % 100 == 0:
                        save_progress(progress)
                        print(f"    Processed: {total_processed} files...")

                except Exception as e:
                    progress['errors'].append({
                        'file': file_key,
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    })
                    progress['total_errors'] += 1
                    total_errors += 1
                    print(f"    ❌ ERROR: {txt_file.name} - {str(e)}")

            # Save after each year
            save_progress(progress)

    # Final save
    save_progress(progress)

    # Summary
    print("\n" + "=" * 80)
    print("TRANSFORMATION COMPLETE")
    print("=" * 80)
    print(f"Total processed: {total_processed:,}")
    print(f"Total errors: {total_errors:,}")
    print(f"Output directory: {JSON_OUTPUT}")
    print(f"Progress file: {PROGRESS_FILE}\n")

if __name__ == "__main__":
    transform_all_txt_to_json()