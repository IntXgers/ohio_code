#!/usr/bin/env python3
"""
Convert organized JSON case files to JSONL format
Prepares data for citation analysis and LMDB database
"""
import json
from pathlib import Path
from datetime import datetime

# Configuration
JSON_INPUT = Path("/Volumes/Jnice4tb/ohio_scotus_caselaw/json")
JSONL_OUTPUT = Path("/Volumes/Jnice4tb/ohio_scotus_caselaw/jsonl")
PROGRESS_FILE = JSONL_OUTPUT / "conversion_progress.json"

# Create output directory
JSONL_OUTPUT.mkdir(parents=True, exist_ok=True)

def load_progress():
    """Load conversion progress"""
    if PROGRESS_FILE.exists():
        try:
            with open(PROGRESS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {'processed_files': set(), 'total_converted': 0}
    return {'processed_files': set(), 'total_converted': 0}

def save_progress(progress):
    """Save conversion progress"""
    # Convert set to list for JSON serialization
    progress_data = {
        'processed_files': list(progress['processed_files']),
        'total_converted': progress['total_converted'],
        'last_updated': datetime.now().isoformat()
    }

    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress_data, f, indent=2)

def convert_to_jsonl():
    """
    Convert all JSON files to a single JSONL file
    Each line is a complete case record
    """
    print("=" * 100)
    print("CONVERTING JSON TO JSONL")
    print("=" * 100)
    print(f"\nSource: {JSON_INPUT}")
    print(f"Output: {JSONL_OUTPUT}\n")

    # Load progress
    progress = load_progress()
    processed_files = set(progress.get('processed_files', []))

    # Output file
    output_file = JSONL_OUTPUT / "ohio_case_law_complete.jsonl"

    # Statistics
    total_files = 0
    converted = 0
    skipped = 0
    errors = 0

    # Open output file in append mode
    with open(output_file, 'a', encoding='utf-8') as outf:
        # Find all JSON files recursively
        for json_file in JSON_INPUT.rglob("*.json"):
            total_files += 1

            # Skip if already processed
            file_key = str(json_file.relative_to(JSON_INPUT))
            if file_key in processed_files:
                skipped += 1
                continue

            try:
                # Read JSON
                with open(json_file, 'r', encoding='utf-8') as inf:
                    case_data = json.load(inf)

                # Add file metadata
                case_data['_source_file'] = file_key
                case_data['_converted_at'] = datetime.now().isoformat()

                # Write as JSONL
                outf.write(json.dumps(case_data, ensure_ascii=False) + '\n')

                # Track progress
                processed_files.add(file_key)
                converted += 1

                # Save progress every 100 files
                if converted % 100 == 0:
                    progress['processed_files'] = processed_files
                    progress['total_converted'] = converted
                    save_progress(progress)
                    print(f"Progress: {converted:,} files converted...", end="\r")

            except Exception as e:
                errors += 1
                print(f"\nERROR: {json_file.name} - {e}")

    # Final save
    progress['processed_files'] = processed_files
    progress['total_converted'] = converted
    save_progress(progress)

    # Summary
    print("\n" + "=" * 100)
    print("CONVERSION COMPLETE")
    print("=" * 100)
    print(f"Total files found: {total_files:,}")
    print(f"Converted: {converted:,}")
    print(f"Skipped (already processed): {skipped:,}")
    print(f"Errors: {errors:,}")
    print(f"\nOutput file: {output_file}")
    print(f"File size: {output_file.stat().st_size / (1024**3):.2f} GB")
    print("=" * 100)

if __name__ == "__main__":
    convert_to_jsonl()