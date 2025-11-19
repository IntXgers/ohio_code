#!/usr/bin/env python3
"""
Create year subdirectories in all court folders
"""

from pathlib import Path

BASE_DIR = Path("/Volumes/Jnice4tb/ohio_scotus")
YEARS = range(1992, 2026)  # 1992-2025

COURT_FOLDERS = [
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

print("Creating year folders in all court directories...")

for court_folder in COURT_FOLDERS:
    court_path = BASE_DIR / court_folder

    # Create court folder if it doesn't exist
    court_path.mkdir(parents=True, exist_ok=True)
    print(f"\n{court_folder}/")

    # Create year folders
    for year in YEARS:
        year_path = court_path / str(year)
        year_path.mkdir(exist_ok=True)
        print(f"  {year}/")

print("\nDone! Created year folders 1992-2025 in all 15 court directories.")