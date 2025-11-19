#!/usr/bin/env python3
"""
Convert Ohio Supreme Court PDFs to text files
Processes all court/year directories and extracts text from each PDF
"""
import PyPDF2
from pathlib import Path
import json
from datetime import datetime
import os  # ADDED: for atomic file operations
import time  # ADDED: for tracking elapsed time

# Configuration
PDF_BASE_DIR = Path("/Volumes/Jnice4tb/ohio_scotus")
TXT_BASE_DIR = Path("/Volumes/Jnice4tb/ohio_scotus_txt")
PROGRESS_FILE = TXT_BASE_DIR / "pdf_to_text_progress.json"

# Create output directory
TXT_BASE_DIR.mkdir(parents=True, exist_ok=True)

# Court directories (matching scraper output)
COURT_DIRS = [
    "supreme_court_of_ohio",
    "first_district_court_of_appeals",
    "second_district_court_of_appeals",
    "third_district_court_of_appeals",
    "fourth_district_court_of_appeals",
    "fifth_district_court_of_appeals",
    "sixth_district_court_of_appeals",
    "seventh_district_court_of_appeals",
    "eighth_district_court_of_appeals",
    "ninth_district_court_of_appeals",
    "tenth_district_court_of_appeals",
    "eleventh_district_court_of_appeals",
    "twelfth_district_court_of_appeals",
    "scotus_court_of_claims",
    "miscellaneous_scotus_opinions"
]

def load_progress():
    """
    Load progress tracking from disk, or start fresh

    ENHANCED: Added error handling for corrupted progress files
    """
    if PROGRESS_FILE.exists():
        try:
            with open(PROGRESS_FILE, 'r') as f:
                progress = json.load(f)
            # Log restart info so you know where you're resuming from
            print(f"📂 Resuming from saved progress: {progress['total_processed']} files already processed")
            if progress.get('errors'):
                print(f"⚠️  Previous run had {len(progress['errors'])} errors")
            return progress
        except (json.JSONDecodeError, KeyError) as e:
            # If progress file is corrupted, back it up and start fresh
            # This prevents losing the corrupted file for debugging
            print(f"⚠️  Corrupted progress file detected: {e}")
            backup_path = PROGRESS_FILE.with_suffix('.json.backup')
            PROGRESS_FILE.rename(backup_path)
            print(f"📋 Backed up corrupted file to: {backup_path}")
            print("🔄 Starting fresh...")
            return _fresh_progress()
    else:
        print("🆕 Starting fresh processing (no previous progress found)")
        return _fresh_progress()

def _fresh_progress():
    """
    Return fresh progress state

    NEW FUNCTION: Centralized place to define progress structure
    Makes it easy to add new fields later
    """
    return {
        'processed_files': {},     # filename -> metadata dict
        'total_processed': 0,      # Count of successfully processed files
        'total_errors': 0,         # Count of failures
        'errors': [],              # List of error details
        'started_at': datetime.now().isoformat(),  # When this batch started
        'last_updated': None       # Last time progress was saved
    }

def save_progress(progress):
    """
    Save progress tracking atomically

    CHANGED: Now uses atomic write-and-rename pattern
    WHY: Prevents corruption if script is killed during save

    HOW IT WORKS:
    1. Write complete JSON to a temporary file
    2. Only after write succeeds, atomically rename temp -> final
    3. os.replace() is guaranteed atomic by the OS
    4. Either old file persists (if killed before replace)
       OR new file is complete (if replace succeeds)
    5. Never get a half-written corrupted file
    """
    # Update timestamp so you can see when last save occurred
    progress['last_updated'] = datetime.now().isoformat()

    # Write to temporary file first (doesn't touch existing progress file)
    temp_file = PROGRESS_FILE.with_suffix('.tmp')
    with open(temp_file, 'w') as f:
        json.dump(progress, f, indent=2)

    # Atomic rename - this either completes fully or doesn't happen
    # If killed during os.replace(), old progress.json remains intact
    os.replace(temp_file, PROGRESS_FILE)

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file"""
    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        raise Exception(f"Failed to extract text: {str(e)}")

def process_all_pdfs():
    """Process all PDFs in court/year directory structure"""
    progress = load_progress()

    # ADDED: Track script start time for performance metrics
    script_start = time.time()

    print("=" * 80)
    print("OHIO SUPREME COURT - PDF TO TEXT CONVERSION")
    print("=" * 80)
    print(f"\nBase directory: {PDF_BASE_DIR}")
    print(f"Output directory: {TXT_BASE_DIR}")  # ADDED: show output location
    print(f"Progress file: {PROGRESS_FILE}")
    print(f"Previously processed: {progress['total_processed']} files\n")

    total_found = 0
    total_processed = 0
    total_skipped = 0
    total_errors = 0

    # Process each court directory
    for court_dir in COURT_DIRS:
        court_path = PDF_BASE_DIR / court_dir

        if not court_path.exists():
            print(f"⚠️  Court directory not found: {court_dir}")
            continue

        print(f"\n{'='*80}")
        print(f"Processing: {court_dir}")
        print(f"{'='*80}")

        # Process each year within the court
        for year_dir in sorted(court_path.iterdir()):
            if not year_dir.is_dir():
                continue

            year = year_dir.name
            print(f"\n  Year: {year}")

            # Find all PDFs in this year
            pdf_files = list(year_dir.glob("*.pdf"))
            total_found += len(pdf_files)

            if not pdf_files:
                print(f"    No PDFs found")
                continue

            print(f"    Found {len(pdf_files)} PDFs")

            # Process each PDF
            for pdf_file in pdf_files:
                pdf_key = str(pdf_file.relative_to(PDF_BASE_DIR))

                # Skip if already processed successfully
                if pdf_key in progress['processed_files']:
                    total_skipped += 1
                    continue

                try:
                    # Extract text
                    text = extract_text_from_pdf(pdf_file)

                    # Create mirrored directory structure in txt corpus
                    txt_court_dir = TXT_BASE_DIR / court_dir / year
                    txt_court_dir.mkdir(parents=True, exist_ok=True)

                    # Save as .txt file in mirrored location
                    txt_file = txt_court_dir / f"{pdf_file.stem}.txt"
                    with open(txt_file, 'w', encoding='utf-8') as f:
                        f.write(text)

                    # Track progress with more metadata
                    # ENHANCED: Now stores char count for validation/debugging
                    progress['processed_files'][pdf_key] = {
                        'txt_file': str(txt_file.relative_to(TXT_BASE_DIR)),
                        'processed_at': datetime.now().isoformat(),
                        'char_count': len(text)
                    }

                    total_processed += 1
                    progress['total_processed'] = len(progress['processed_files'])

                    # CHANGED: Save every 100 files instead of every 10
                    # WHY: 100 is better balance of safety vs I/O overhead
                    # For 168k files, this gives ~1,680 saves vs 16,800
                    if total_processed % 100 == 0:
                        save_progress(progress)  # Atomic save
                        # ENHANCED: Show progress as fraction of total found
                        print(f"    💾 Progress saved: {total_processed}/{total_found} files processed")

                except Exception as e:
                    # ENHANCED: Track errors more thoroughly
                    error_info = {
                        'file': pdf_key,
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    }
                    progress['errors'].append(error_info)
                    progress['total_errors'] = len(progress['errors'])  # ADDED: count

                    print(f"    ❌ ERROR: {pdf_file.name} - {str(e)}")
                    total_errors += 1

                    # ADDED: Save immediately on error so we don't lose error info
                    save_progress(progress)

            # REMOVED: Year-level save is redundant with every-100 saves
            # It would save too frequently for large years

    # ADDED: Final save to ensure everything is captured
    # Even if last batch was < 100 files, this ensures it's saved
    save_progress(progress)

    # ADDED: Calculate performance metrics
    elapsed_time = time.time() - script_start
    files_per_second = total_processed / elapsed_time if elapsed_time > 0 else 0

    # Final summary
    print("\n" + "=" * 80)
    print("CONVERSION COMPLETE")
    print("=" * 80)
    print(f"Total PDFs found: {total_found}")
    print(f"Newly processed: {total_processed}")
    print(f"Skipped (already done): {total_skipped}")
    print(f"Errors: {total_errors}")
    print(f"Total in progress file: {progress['total_processed']}")

    # ADDED: Performance metrics
    print(f"\n⏱️  Time elapsed: {elapsed_time:.1f} seconds")
    print(f"⚡ Processing speed: {files_per_second:.1f} files/second")

    print(f"\n💾 Progress saved to: {PROGRESS_FILE}")

    # ADDED: If there were errors, tell user where to find them
    if total_errors > 0:
        print(f"\n⚠️  {total_errors} files had errors - check {PROGRESS_FILE} for details")

if __name__ == "__main__":
    process_all_pdfs()