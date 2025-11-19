#!/usr/bin/env python3
"""
Check scraping progress
"""
import json
from pathlib import Path

SCOTUS_DIR = Path("/Volumes/Jnice4tb/ohio_scotus")
PROGRESS_FILE = SCOTUS_DIR / "scraper_progress.json"

def check_progress():
    """Display scraping progress"""

    if not PROGRESS_FILE.exists():
        print("No progress file found. Scraper not started yet.")
        return

    with open(PROGRESS_FILE, 'r') as f:
        progress = json.load(f)

    completed = progress.get('completed_queries', {})
    downloaded = progress.get('downloaded_cases', {})

    print("=" * 80)
    print("OHIO SUPREME COURT SCRAPER - PROGRESS REPORT")
    print("=" * 80)
    print(f"\nTotal queries completed: {len(completed)}")
    print(f"Total cases downloaded: {len(downloaded)}")

    # Count by result status
    with_results = sum(1 for q in completed.values() if q['total_results'] > 0)
    no_results = sum(1 for q in completed.values() if q['total_results'] == 0)

    print(f"\nQueries with results: {with_results}")
    print(f"Queries with no results: {no_results}")

    # Show recent downloads
    if downloaded:
        print(f"\nMost recent downloads:")
        sorted_downloads = sorted(
            downloaded.items(),
            key=lambda x: x[1]['downloaded_at'],
            reverse=True
        )
        for webcite, data in sorted_downloads[:5]:
            timestamp = data['downloaded_at'].split('T')[1].split('.')[0]
            print(f"  {webcite} - {timestamp}")

    # Show queries with results
    if with_results > 0:
        print(f"\nQueries with cases found:")
        for query_name, data in completed.items():
            if data['total_results'] > 0:
                results = data['total_results']
                downloaded_count = data.get('downloaded', 0)
                print(f"  {query_name}: {results} results, {downloaded_count} downloaded")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    check_progress()