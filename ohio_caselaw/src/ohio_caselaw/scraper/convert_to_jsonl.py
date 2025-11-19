#!/usr/bin/env python3
"""
Convert Ohio Supreme Court metadata to JSONL format
"""
import json
from pathlib import Path

SCOTUS_DIR = Path("/Volumes/Jnice4tb/ohio_scotus")
METADATA_FILE = SCOTUS_DIR / "cases_metadata.json"
OUTPUT_FILE = Path(__file__).parent.parent / "data" / "core" / "ohio_scotus_complete.jsonl"

def convert_metadata():
    """Convert metadata.json to JSONL format"""

    # Load metadata
    with open(METADATA_FILE, 'r') as f:
        metadata = json.load(f)

    print(f"Loaded {len(metadata)} cases")

    # Create output directory
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Convert to JSONL
    with open(OUTPUT_FILE, 'w') as f:
        for webcite, case_data in metadata.items():
            # Create JSONL entry
            entry = {
                'webcite': webcite,
                'case_name': case_data.get('case_name', ''),
                'topics': case_data.get('topics', ''),
                'author': case_data.get('author', ''),
                'decided': case_data.get('decided', ''),
                'source': case_data.get('source', ''),
                'year': case_data.get('year', ''),
                'pdf_url': case_data.get('pdf_url', ''),
                'pdf_path': str(SCOTUS_DIR / f"{webcite}.pdf")
            }

            f.write(json.dumps(entry) + '\n')

    print(f"Converted to JSONL: {OUTPUT_FILE}")
    print(f"Total entries: {len(metadata)}")

if __name__ == "__main__":
    convert_metadata()