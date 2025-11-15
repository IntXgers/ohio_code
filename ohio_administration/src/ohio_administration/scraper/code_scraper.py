import os
import time
import json
import hashlib
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import Set, Dict, List, Optional

BASE_URL = "https://codes.ohio.gov"


class OhioCodeScraper:
    def __init__(self, state_file: str = "scraper_state.json"):
        self.current_code_num = None
        self.current_code_data = []  # Changed to list instead of None
        self.state_file = state_file
        self.visited_urls: Set[str] = set()
        self.completed_codes: Set[str] = set()  # Add this line after the other instance variables
        self.completed_chapters: Dict[str, Set[str]] = {}
        self.load_state()

    @staticmethod
    def url_hash(url: str) -> str:
        """Generate SHA256 hash for URL tracking"""
        return hashlib.sha256(url.encode()).hexdigest()[:16]

    def save_state(self):
        """Persist scraper state to file"""
        import tempfile
        import shutil
        state = {
            "visited_urls": list(self.visited_urls),
            "completed_codes": list(self.completed_codes),  # Add this line
            "completed_chapters": {k: list(v) for k, v in self.completed_chapters.items()}
        }
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix='.json') as tmp:
            json.dump(state, tmp)
            temp_path = tmp.name
        shutil.move(temp_path, self.state_file)

        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

    def load_state(self):
        """Load previous scraper state if it exists"""
        if not os.path.exists(self.state_file):
            print("🆕 Starting fresh - no previous state found")
            return

        with open(self.state_file, "r", encoding="utf-8") as f:
            state = json.load(f)
        self.visited_urls = set(state.get("visited_urls", []))
        self.completed_codes = set(state.get("completed_codes", []))
        self.completed_chapters = {
            k: set(v) for k, v in state.get("completed_chapters", {}).items()
        }
        print(f"📂 Loaded state: {len(self.visited_urls)} visited URLs, "
              f"{sum(len(v) for v in self.completed_chapters.values())} completed chapters, "
              f"{len(self.completed_codes)} completed codes")  # Update the print statement
        print(f"📂 Loaded state: {len(self.visited_urls)} visited URLs, "
              f"{sum(len(v) for v in self.completed_chapters.values())} completed chapters")

    @staticmethod
    def fetch_page(url: str) -> BeautifulSoup:
        """Fetch and parse HTML page with basic headers and retry delay"""
        headers = {"User-Agent": "Mozilla/5.0 (OhioScraper/1.0)"}
        time.sleep(1)
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")

    def extract_section_data(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extract header and paragraphs from a section page"""
        h1 = soup.find("h1")
        header = h1.get_text(strip=True) if h1 else None
        body = soup.find("section", class_="laws-body")
        paragraphs = [p.get_text(strip=True) for p in body.find_all("p")] if body else []

        return {
            "url": url,
            "header": header,
            "paragraphs": paragraphs,
            "url_hash": self.url_hash(url)
        }

    @staticmethod
    def get_next_section_url(soup: BeautifulSoup) -> Optional[str]:
        """Extract next section URL from navigation block"""
        next_link = soup.select_one(".profile-navigator .next a")
        if next_link and next_link.get("href"):
            return urljoin(BASE_URL, next_link["href"])
        return None

    def crawl_sections_from_chapter(self, first_section_url: str) -> List[Dict]:
        """Sequentially crawl all sections in a chapter starting at given URL"""
        chapter_data = []
        current_url = first_section_url
        chapter_visited = set()

        print(f"  📖 Starting section crawl from: {first_section_url}")

        while current_url and current_url not in chapter_visited:
            if current_url in self.visited_urls:
                print(f"  ⭐️ Already scraped: {current_url}")
                break

            soup = self.fetch_page(current_url)
            section_data = self.extract_section_data(soup, current_url)
            chapter_data.append(section_data)
            chapter_visited.add(current_url)
            self.visited_urls.add(current_url)

            print(f"  ✅ Scraped: {section_data['header']}")

            next_url = self.get_next_section_url(soup)
            if next_url in chapter_visited:
                print("  🔄 Loop detected, stopping chapter crawl")
                break

            current_url = next_url
            time.sleep(2)

        return chapter_data

    def get_code_chapters(self, code_num: str) -> List[str]:
        """Return list of all chapter URLs within a given admin code
        Handles formats like: 3701-1, 3701:1-1, 3701:1-01, etc."""

        # code_num should be a string now to handle formats like "3701-1" or "3701:1"
        code_url = f"{BASE_URL}/ohio-administrative-code/{code_num}"

        soup = self.fetch_page(code_url)
        table = soup.select_one("table.data-grid.laws-table")
        if not table:
            print(f"  ⚠️ No laws table found for Code {code_num}")
            return []

        # Admin code uses 'chapter-' in URLs regardless of the display format
        chapter_links = table.select("a[href*='chapter-']")
        chapter_urls = []

        for link in chapter_links:
            href = link.get("href")
            if href:
                # The href already contains the full path with special characters encoded
                # Don't try to construct it manually
                chapter_url = urljoin(BASE_URL, href)
                chapter_urls.append(chapter_url)

                # Log what we found for debugging
                chapter_text = link.get_text(strip=True)
                print(f"    Found chapter: {chapter_text} -> {chapter_url}")

        print(f"  📋 Found {len(chapter_urls)} chapters in code {code_num}")
        return chapter_urls

    def get_chapter_first_rule(self, chapter_url: str) -> Optional[str]:
        """Extract the first section URL from a chapter page"""
        soup = self.fetch_page(chapter_url)
        rule_links = soup.select("a[href*='/rule-']")
        if rule_links:
            return urljoin(BASE_URL, rule_links[0].get("href"))
        return None

    def get_all_admin_codes(self) -> List[str]:
        """Scrape the main admin code page to get all code numbers"""
        main_url = f"{BASE_URL}/ohio-administrative-code"

        soup = self.fetch_page(main_url)

        # Find all links that point to individual codes
        code_links = soup.select("a[href*='/ohio-administrative-code/']")

        codes = []
        for link in code_links:
            href = link.get("href")
            if href and href != "/ohio-administrative-code":
                # Extract code number from URL
                # e.g., /ohio-administrative-code/109:8 -> 109:8
                code_num = href.split("/ohio-administrative-code/")[-1]
                if code_num and code_num not in codes:
                    codes.append(code_num)

        print(f"Found {len(codes)} admin codes to scrape")
        return sorted(codes)  # Sort for consistent ordering

    def crawl_all_codes(self):
        """Main driver for admin codes - discovers and crawls all automatically"""
        # First, get all admin codes from the main page
        main_url = f"{BASE_URL}/ohio-administrative-code"

        soup = self.fetch_page(main_url)
        code_links = soup.select("a[href*='/ohio-administrative-code/']")

        admin_codes = []
        for link in code_links:
            href = link.get("href")
            if href and href != "/ohio-administrative-code":
                code_num = href.split("/ohio-administrative-code/")[-1]
                if code_num and code_num not in admin_codes:
                    admin_codes.append(code_num)

        print(f"🚀 Found {len(admin_codes)} admin codes to crawl")

        remaining_codes = [code for code in sorted(admin_codes) if code not in self.completed_codes]
        print(f"✅ {len(self.completed_codes)} codes already completed")
        print(f"📋 {len(remaining_codes)} codes remaining to process")

        if remaining_codes:
            print(f"🎯 Starting from code: {remaining_codes[0]}")

        # Now crawl each code
        for code_num in remaining_codes:
            self.current_code_num = code_num
            self.current_code_data = []  # CRITICAL: Reset for new code
            code_key = f"code-{code_num.replace(':', '_')}"
            print(f"\n📚 Processing Admin Code {code_num}")

            chapter_urls = self.get_code_chapters(code_num)
            if not chapter_urls:
                print(f"  ⚠️ No chapters found for Code {code_num}")
                continue

            if code_key not in self.completed_chapters:
                self.completed_chapters[code_key] = set()

            # REMOVED local code_data variable - use self.current_code_data instead

            for chapter_url in chapter_urls:
                chapter_hash = self.url_hash(chapter_url)
                if chapter_hash in self.completed_chapters[code_key]:
                    print(f"  ⭐️ Chapter already completed: {chapter_url}")
                    continue

                print(f"  📂 Processing chapter: {chapter_url}")
                first_rule_url = self.get_chapter_first_rule(chapter_url)  # Changed to rule
                if not first_rule_url:
                    print("    ⚠️ No rules found in chapter")
                    continue

                chapter_data = self.crawl_sections_from_chapter(first_rule_url)
                self.current_code_data.extend(chapter_data)  # CHANGED: Use self.current_code_data
                self.completed_chapters[code_key].add(chapter_hash)
                self.save_state()
                time.sleep(3)

            if self.current_code_data:  # CHANGED: Use self.current_code_data
                self.save_code_results(code_num, self.current_code_data)  # CHANGED: Use self.current_code_data
            else:
                print(f"No new data to save for Code {code_num}")

        print("\n🎉 Crawl complete!")

    @staticmethod
    def save_code_results(code_num: str, code_data: List[Dict]):
        """Write out all scraped sections for a code to disk"""
        os.makedirs("scraped_codes", exist_ok=True)

        # Replace colons with underscore for valid filenames
        safe_filename = code_num.replace(":", "_")
        path = os.path.join("scraped_codes", f"code-{safe_filename}.json")

        print(f"About to save {len(code_data)} codes to {path}")
        print(f"  📊 About to save {len(code_data)} rules for Code {code_num}")

        with open(path, "w", encoding="utf-8") as f:
            json.dump(code_data, f, indent=2, ensure_ascii=False)

        print(f"💾 Saved Code {code_num} to {path} ({len(code_data)} rules)")

        if os.path.exists(path):
            file_size = os.path.getsize(path)
            print(f"  ✅ File created successfully (size: {file_size:,} bytes)")

    def save_partial_data(self):
        """Save any partially scraped data before exit"""
        if self.current_code_data and self.current_code_num:
            print(f"\n💾 Saving partial data for {self.current_code_num}...")
            print(f"  Found {len(self.current_code_data)} rules to save")  # ADDED: Debug info

            # Save with a special filename to indicate it's partial
            os.makedirs("scraped_codes", exist_ok=True)
            safe_filename = self.current_code_num.replace(":", "_")
            path = os.path.join("scraped_codes", f"code-{safe_filename}-PARTIAL.json")

            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.current_code_data, f, indent=2, ensure_ascii=False)

            print(f"💾 Saved {len(self.current_code_data)} partial rules to {path}")


def main():
    scraper = OhioCodeScraper()

    try:
        scraper.crawl_all_codes()

    except KeyboardInterrupt:
        scraper.save_state()
        scraper.save_partial_data()
        print("\n⏸️ Crawl interrupted by user")
        print("💾 Progress saved - can resume later")


if __name__ == "__main__":
    main()