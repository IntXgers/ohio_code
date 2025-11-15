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
        self.state_file = state_file
        self.visited_urls: Set[str] = set()
        self.completed_chapters: Dict[str, Set[str]] = {}
        self.load_state()

    def url_hash(self, url: str) -> str:
        """Generate SHA256 hash for URL tracking"""
        return hashlib.sha256(url.encode()).hexdigest()[:16]

    def save_state(self):
        """Persist scraper state to file"""
        state = {
            "visited_urls": list(self.visited_urls),
            "completed_chapters": {k: list(v) for k, v in self.completed_chapters.items()}
        }
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

    def load_state(self):
        """Load previous scraper state if it exists"""
        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                state = json.load(f)
            self.visited_urls = set(state.get("visited_urls", []))
            self.completed_chapters = {
                k: set(v) for k, v in state.get("completed_chapters", {}).items()
            }
            print(f"📂 Loaded state: {len(self.visited_urls)} visited URLs, "
                  f"{sum(len(v) for v in self.completed_chapters.values())} completed chapters")
        except FileNotFoundError:
            print("🆕 Starting fresh - no previous state found")

    def fetch_page(self, url: str) -> BeautifulSoup:
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

    def get_next_section_url(self, soup: BeautifulSoup) -> Optional[str]:
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
                print(f"  ⏭️  Already scraped: {current_url}")
                break

            try:
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

            except Exception as e:
                print(f"  ❌ Error scraping {current_url}: {e}")
                break

        return chapter_data

    def get_title_chapters(self, title_num: int) -> List[str]:
        """Return list of all chapter URLs within a given title"""
        title_url = f"{BASE_URL}/ohio-revised-code/title-{title_num}"

        try:
            soup = self.fetch_page(title_url)
            table = soup.select_one("table.data-grid.laws-table")
            if not table:
                print(f"  ⚠️  No laws table found for Title {title_num}")
                return []

            chapter_links = table.select("a[href*='chapter-']")
            chapter_urls = []

            for link in chapter_links:
                href = link.get("href")
                if href:
                    chapter_url = f"{BASE_URL}/ohio-revised-code/{href}" if href.startswith("chapter-") else urljoin(BASE_URL, href)
                    chapter_urls.append(chapter_url)

            print(f"  📋 Found {len(chapter_urls)} chapters in Title {title_num}")
            return chapter_urls

        except Exception as e:
            print(f"❌ Error fetching title {title_num}: {e}")
            return []

    def get_chapter_first_section(self, chapter_url: str) -> Optional[str]:
        """Extract the first section URL from a chapter page"""
        try:
            soup = self.fetch_page(chapter_url)
            section_links = soup.select("a[href*='/section-']")
            if section_links:
                return urljoin(BASE_URL, section_links[0].get("href"))
        except Exception as e:
            print(f"❌ Error fetching chapter {chapter_url}: {e}")
        return None

    def save_title_results(self, title_num: int, title_data: List[Dict]):
        """Write out all scraped sections for a title to disk"""
        os.makedirs("scraped_titles", exist_ok=True)
        path = os.path.join("scraped_titles", f"title-{title_num:03}.json")

        with open(path, "w", encoding="utf-8") as f:
            json.dump(title_data, f, indent=2, ensure_ascii=False)

        print(f"💾 Saved Title {title_num} to {path} ({len(title_data)} sections)")

    def crawl_all_titles(self, start_title: int = 1, max_title: int = 63):
        """Main driver: iterate through Titles 1–63 (odd only) and scrape all sections"""
        print(f"🚀 Starting Ohio Revised Code crawl from Title {start_title} to {max_title}")

        for title_num in range(start_title, max_title + 1, 2):  # odd-numbered titles only
            title_key = f"title-{title_num}"
            print(f"\n📚 Processing Title {title_num}")

            chapter_urls = self.get_title_chapters(title_num)
            if not chapter_urls:
                print(f"  ⚠️  No chapters found for Title {title_num}")
                continue

            if title_key not in self.completed_chapters:
                self.completed_chapters[title_key] = set()

            title_data = []

            for chapter_url in chapter_urls:
                chapter_hash = self.url_hash(chapter_url)
                if chapter_hash in self.completed_chapters[title_key]:
                    print(f"  ⏭️  Chapter already completed: {chapter_url}")
                    continue

                print(f"  📂 Processing chapter: {chapter_url}")
                first_section_url = self.get_chapter_first_section(chapter_url)
                if not first_section_url:
                    print("    ⚠️  No sections found in chapter")
                    continue

                chapter_data = self.crawl_sections_from_chapter(first_section_url)
                title_data.extend(chapter_data)
                self.completed_chapters[title_key].add(chapter_hash)
                self.save_state()
                time.sleep(3)

            self.save_title_results(title_num, title_data)

        print("\n🎉 Crawl complete!")


def main():
    scraper = OhioCodeScraper()

    try:
        scraper.crawl_all_titles(start_title=1, max_title=63)

    except KeyboardInterrupt:
        print("\n⏸️  Crawl interrupted by user")
        scraper.save_state()
        print("💾 Progress saved - can resume later")

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        scraper.save_state()
        print("💾 Error state saved")


if __name__ == "__main__":
    main()