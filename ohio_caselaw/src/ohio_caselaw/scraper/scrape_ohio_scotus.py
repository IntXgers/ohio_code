#!/usr/bin/env python3
"""
Ohio Supreme Court Case Scraper - Selenium Version
Uses real browser to handle forms and pagination
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import Select
import json
import time
import hashlib
from pathlib import Path
from datetime import datetime
import sys
import requests

# Configuration
BASE_URL = "https://www.supremecourt.ohio.gov/rod/docs/"
OUTPUT_DIR = Path("/Volumes/Jnice4tb/ohio_scotus")
PROGRESS_FILE = OUTPUT_DIR / "scraper_progress.json"
METADATA_FILE = OUTPUT_DIR / "cases_metadata.json"
ERROR_LOG = OUTPUT_DIR / "scraper_errors.log"

# Test mode
TEST_MODE_LIMIT = None

# Sources to scrape
SOURCES = [
    ("0", "Supreme Court of Ohio"),
    ("1", "First District Court of Appeals"),
    ("2", "Second District Court of Appeals"),
    ("3", "Third District Court of Appeals"),
    ("4", "Fourth District Court of Appeals"),
    ("5", "Fifth District Court of Appeals"),
    ("6", "Sixth District Court of Appeals"),
    ("7", "Seventh District Court of Appeals"),
    ("8", "Eighth District Court of Appeals"),
    ("9", "Ninth District Court of Appeals"),
    ("10", "Tenth District Court of Appeals"),
    ("11", "Eleventh District Court of Appeals"),
    ("12", "Twelfth District Court of Appeals"),
    ("13", "Court of Claims"),
    ("98", "Miscellaneous")
]

YEARS = list(range(1992, 2026))

# At top with other config
FOLDER_NAMES = {
    "Supreme Court of Ohio": "supreme_court_of_ohio",
    "First District Court of Appeals": "first_district_court_of_appeals",
    "Second District Court of Appeals": "second_district_court_of_appeals",
    "Third District Court of Appeals": "third_district_court_of_appeals",
    "Fourth District Court of Appeals": "fourth_district_court_of_appeals",
    "Fifth District Court of Appeals": "fifth_district_court_of_appeals",
    "Sixth District Court of Appeals": "sixth_district_court_of_appeals",
    "Seventh District Court of Appeals": "seventh_district_court_of_appeals",
    "Eighth District Court of Appeals": "eighth_district_court_of_appeals",
    "Ninth District Court of Appeals": "ninth_district_court_of_appeals",
    "Tenth District Court of Appeals": "tenth_district_court_of_appeals",
    "Eleventh District Court of Appeals": "eleventh_district_court_of_appeals",
    "Twelfth District Court of Appeals": "twelfth_district_court_of_appeals",
    "Court of Claims": "scotus_court_of_claims",
    "Miscellaneous": "miscellaneous_scotus_opinions"
}


class OhioSeleniumScraper:
    """Selenium-based scraper for Ohio Supreme Court"""

    def __init__(self):
        self.progress = self.load_progress()
        self.metadata = self.load_metadata()
        self.downloaded_count = 0
        self.driver = None

        # Create output directory
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def load_progress():
        """Load progress from checkpoint"""
        if PROGRESS_FILE.exists():
            try:
                with open(PROGRESS_FILE, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print("Warning: Corrupted progress file, starting fresh")
                PROGRESS_FILE.unlink()
        return {
            'completed_queries': {},
            'downloaded_cases': {}
        }

    def save_progress(self):
        """Save checkpoint"""
        with open(PROGRESS_FILE, 'w') as f:
            json.dump(self.progress, f, indent=2)

    @staticmethod
    def load_metadata():
        """Load case metadata"""
        if METADATA_FILE.exists():
            with open(METADATA_FILE, 'r') as f:
                return json.load(f)
        return {}

    def save_metadata(self):
        """Save case metadata"""
        with open(METADATA_FILE, 'w') as f:
            json.dump(self.metadata, f, indent=2)

    @staticmethod
    def log_error(message):
        """Log error to file"""
        timestamp = datetime.now().isoformat()
        with open(ERROR_LOG, 'a') as f:
            f.write(f"[{timestamp}] {message}\n")
        print(f"ERROR: {message}")

    def init_driver(self):
        """Initialize Selenium WebDriver"""
        options = webdriver.ChromeOptions()
        # Run headless (no visible browser window)
        # options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')

        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(10)

    def close_driver(self):
        """Close browser"""
        if self.driver:
            self.driver.quit()

    def submit_search(self, source_value, year):
        """Submit search form"""
        print(f"  Navigating to search page...")
        self.driver.get(BASE_URL)

        # Wait for form to load
        WebDriverWait(self.driver, 10).until(
            ec.presence_of_element_located((By.ID, "MainContent_ddlCourt"))
        )

        # Select court
        court_dropdown = Select(self.driver.find_element(By.ID, "MainContent_ddlCourt"))
        court_dropdown.select_by_value(source_value)

        # Select year range
        year_from = Select(self.driver.find_element(By.ID, "MainContent_ddlDecidedYearMin"))
        year_from.select_by_value(str(year))

        year_to = Select(self.driver.find_element(By.ID, "MainContent_ddlDecidedYearMax"))
        year_to.select_by_value(str(year))

        # Set rows per page to 200
        rows_per_page = Select(self.driver.find_element(By.ID, "MainContent_ddlRowsPerPage"))
        rows_per_page.select_by_value("200")

        print(f"  Submitting search: {source_value}, year {year}")

        # Click submit
        submit_btn = self.driver.find_element(By.ID, "MainContent_btnSubmit")
        submit_btn.click()

        # Wait for results to load
        time.sleep(2)

    def get_result_count(self):
        """Get total result count from page"""
        try:
            result_span = self.driver.find_element(By.ID, "MainContent_lblRowCount")
            text = result_span.text
            # Extract number from "This search returned XXX rows."
            import re
            match = re.search(r'(\d+)\s+rows', text)
            if match:
                return int(match.group(1))
        except Exception as ResultCountError:
          print(f"  Error getting result count: {ResultCountError}")
        return 0

    def extract_cases_from_current_page(self):
        """Extract case data from current page"""
        cases = []

        try:
            # Find results table
            table = self.driver.find_element(By.ID, "MainContent_gvResults")
            rows = table.find_elements(By.TAG_NAME, "tr")

            for row in rows:
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")

                    # Skip if not enough cells or header row
                    if len(cells) < 6:
                        continue

                    # Get case link from first cell
                    try:
                        link = cells[0].find_element(By.TAG_NAME, "a")
                        pdf_url = link.get_attribute("href")

                        # Skip pagination links
                        if not pdf_url or 'javascript:' in pdf_url:
                            continue

                        case_name = link.text.strip()

                        # Get webcite from last cell
                        webcite = cells[-1].text.strip()

                        # Skip if webcite looks like a date
                        if '/' in webcite or not webcite:
                            continue

                        # Get other metadata
                        topics = cells[1].text.strip()
                        author = cells[2].text.strip()
                        decided = cells[3].text.strip()

                        cases.append({
                            'webcite': webcite,
                            'case_name': case_name,
                            'pdf_url': pdf_url,
                            'topics': topics,
                            'author': author,
                            'decided': decided
                        })
                    except:
                        continue

                except:
                    continue

        except Exception as e:
            print(f"  Error extracting cases: {e}")

        return cases

    def go_to_next_page(self, current_page):
        """Navigate to next page"""
        try:
            next_page_num = current_page + 1

            # Find the results table
            table = self.driver.find_element(By.ID, "MainContent_gvResults")

            # Get first row (pagination row)
            first_row = table.find_elements(By.TAG_NAME, "tr")[0]

            # Find all links in that row
            links = first_row.find_elements(By.TAG_NAME, "a")

            # Look for a link with next page number
            for link in links:
                if link.text.strip() == str(next_page_num):
                    link.click()
                    time.sleep(3)
                    return True

            return False
        except:
            return False

    def download_pdf(self, pdf_url, webcite, source_name, year):
        """Download PDF file into organized directory"""
        # Create court/year subdirectory
        folder_name = FOLDER_NAMES[source_name]
        
        year_dir = OUTPUT_DIR / folder_name / str(year)
        year_dir.mkdir(parents=True, exist_ok=True)

        filepath = year_dir / f"{webcite}.pdf"

        if filepath.exists():
            print(f"    Already downloaded: {webcite}")
            return True

        # Check test mode limit
        if TEST_MODE_LIMIT and self.downloaded_count >= TEST_MODE_LIMIT:
            print(f"    TEST MODE: Reached limit")
            return False

        try:
            response = requests.get(pdf_url, timeout=30)

            if response.status_code != 200:
                self.log_error(f"Failed to download {webcite}: HTTP {response.status_code}")
                return False

            with open(filepath, 'wb') as f:
                f.write(response.content)

            file_hash = hashlib.sha256(response.content).hexdigest()

            self.progress['downloaded_cases'][webcite] = {
                'hash': file_hash,
                'filename': str(filepath.relative_to(OUTPUT_DIR)),  # Store relative path
                'downloaded_at': datetime.now().isoformat()
            }

            self.downloaded_count += 1
            print(f"    Downloaded: {webcite} ({self.downloaded_count} total)")
            return True

        except Exception as e:
            self.log_error(f"Exception downloading {webcite}: {str(e)}")
            return False

    def scrape_query(self, source_value, source_name, year):
        """Scrape all cases for a source/year combination"""
        query_key = f"{source_name}_{year}"

        if query_key in self.progress['completed_queries']:
            print(f"Skipping completed query: {source_name} {year}")
            return

        print(f"\nSearching: {source_name} - {year}")

        try:
            # Submit search
            self.submit_search(source_value, year)

            # Get result count
            result_count = self.get_result_count()
            print(f"  Total results: {result_count}")

            if result_count == 0:
                print(f"  No results found")
                self.progress['completed_queries'][query_key] = {
                    'completed_at': datetime.now().isoformat(),
                    'total_results': 0,
                    'downloaded': 0
                }
                self.save_progress()
                return

            # Scrape all pages
            all_cases = []
            page_num = 1

            while True:
                print(f"  Scraping page {page_num}...")

                cases = self.extract_cases_from_current_page()

                if not cases:
                    print(f"  Page {page_num} empty, done")
                    break

                print(f"  Found {len(cases)} cases on page {page_num}")
                all_cases.extend(cases)

                # Try to go to next page
                if not self.go_to_next_page(page_num):
                    print(f"  No more pages")
                    break

                page_num += 1

            print(f"  Total found: {len(all_cases)} cases")

            # Download PDFs
            print(f"  Downloading PDFs...")
            downloaded = 0
            for case in all_cases:
                # Store metadata
                self.metadata[case['webcite']] = {
                    'case_name': case['case_name'],
                    'topics': case['topics'],
                    'author': case['author'],
                    'decided': case['decided'],
                    'source': source_name,
                    'year': year,
                    'pdf_url': case['pdf_url']
                }

                # Download PDF
                if self.download_pdf(case['pdf_url'], case['webcite'], source_name, year):
                    downloaded += 1

                    # Check test mode limit
                    if TEST_MODE_LIMIT and self.downloaded_count >= TEST_MODE_LIMIT:
                        print(f"\nTEST MODE: Stopping at {TEST_MODE_LIMIT} downloads")
                        self.save_progress()
                        self.save_metadata()
                        return

            # Mark query as complete
            self.progress['completed_queries'][query_key] = {
                'completed_at': datetime.now().isoformat(),
                'total_results': len(all_cases),
                'downloaded': downloaded
            }

            # Save checkpoint
            self.save_progress()
            self.save_metadata()


        except Exception as e:
            self.log_error(f"Exception in query {query_key}: {str(e)}")
            import traceback
            traceback.print_exc()

    def run(self):
        """Main scraper loop"""
        print("Ohio Supreme Court Scraper - Selenium Version")
        print(f"Output directory: {OUTPUT_DIR}")
        if TEST_MODE_LIMIT:
            print(f"TEST MODE: Limited to {TEST_MODE_LIMIT} downloads")
        print("=" * 80)

        # Initialize browser
        self.init_driver()

        try:
            # Iterate through all sourcDude I just gave you the whole file so what's up answer the question oh my God you're fucking retarded dude holy fuck man fuck this dude man.es and years
            for source_value, source_name in SOURCES:
                for year in YEARS:
                    self.scrape_query(source_value, source_name, year)

                    # Check test mode limit
                    if TEST_MODE_LIMIT and self.downloaded_count >= TEST_MODE_LIMIT:
                        break

                if TEST_MODE_LIMIT and self.downloaded_count >= TEST_MODE_LIMIT:
                    break

        finally:
            # Always close browser
            self.close_driver()

            print("\n" + "=" * 80)
            print("Scraping complete!")
            print(f"Total cases downloaded: {self.downloaded_count}")
            print(f"Metadata file: {METADATA_FILE}")
            print(f"Progress file: {PROGRESS_FILE}")


if __name__ == "__main__":
    # Set test mode
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        TEST_MODE_LIMIT = 51
        print("Running in TEST MODE with 51 download limit")

    scraper = OhioSeleniumScraper()
    scraper.run()