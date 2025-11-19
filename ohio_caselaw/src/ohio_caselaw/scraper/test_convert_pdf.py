#!/usr/bin/env python3
"""
TEST VERSION - Convert PDFs to text for a single directory
Tests on: twelfth_district_court_of_appeals/2001
"""
import PyPDF2
from pathlib import Path
import json
from datetime import datetime

# Test on specific directory using symlink
TEST_DIR = Path("/ohio_scotus_caselaw/src/ohio_scotus/data/ohio_scotus/pdfs/twelfth_district_court_of_appeals/2001")

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

def test_conversion():
    """Test PDF to text conversion on single directory"""
    print("=" * 80)
    print("TEST - PDF TO TEXT CONVERSION")
    print("=" * 80)
    print(f"\nTest directory: {TEST_DIR}")

    if not TEST_DIR.exists():
        print(f"ERROR: Directory does not exist!")
        return

    # Find all PDFs
    pdf_files = list(TEST_DIR.glob("*.pdf"))
    print(f"Found {len(pdf_files)} PDFs\n")

    if not pdf_files:
        print("No PDFs to process!")
        return

    processed = 0
    errors = 0

    for pdf_file in pdf_files:
        try:
            print(f"Processing: {pdf_file.name}")

            # Extract text
            text = extract_text_from_pdf(pdf_file)

            # Save as .txt file
            txt_file = pdf_file.with_suffix('.txt')
            with open(txt_file, 'w', encoding='utf-8') as f:
                f.write(text)

            print(f"  ✓ Created: {txt_file.name} ({len(text)} chars)")
            processed += 1

        except Exception as e:
            print(f"  ✗ ERROR: {str(e)}")
            errors += 1

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    print(f"Processed: {processed}")
    print(f"Errors: {errors}")

if __name__ == "__main__":
    test_conversion()