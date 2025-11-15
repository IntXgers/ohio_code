import os
import requests
from bs4 import BeautifulSoup
import time
import json
import hashlib
from urllib.parse import urljoin
from typing import Set, Dict, List, Optional

BASE_URL = "https://codes.ohio.gov"
INDEX_URL = f"{BASE_URL}/ohio-constitution"

ROMAN_MAP = {
    'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5,
    'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10,
    'XI': 11, 'XII': 12, 'XIII': 13, 'XIV': 14, 'XV': 15,
    'XVI': 16, 'XVII': 17, 'XVIII': 18
}


def roman_to_int(roman: str) -> int:
    """Convert Roman numeral to integer"""
    return ROMAN_MAP.get(roman.upper().strip(), 0)


def url_hash(url: str) -> str:
    """Generate SHA256 hash for URL tracking"""
    return hashlib.sha256(url.encode()).hexdigest()[:16]


def fetch_page(url: str) -> BeautifulSoup:
    """Fetch page with error handling"""
    headers = {"User-Agent": "Mozilla/5.0 (OhioScraper/1.0)"}
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def get_all_article_urls() -> List[Dict[str, str]]:
    """
    Get all article URLs from constitution index with Roman numerals
    """
    try:
        soup = fetch_page(INDEX_URL)
        links = soup.select("a[href*='ohio-constitution/article-']")

        articles = []
        for link in links:
            href = link.get("href")
            if not href or href == "/ohio-constitution":
                continue

            full_url = urljoin(BASE_URL, href)
            text = ''.join(link.stripped_strings)

            # Extract Roman numeral
            parts = text.split()
            roman = parts[1].upper().strip() if len(parts) > 1 else ""
            article_num = roman_to_int(roman)

            articles.append({
                "roman": roman,
                "num": article_num,
                "text": text,
                "url": full_url
            })

        print(f"📘 Found {len(articles)} articles")
        return articles

    except Exception as e:
        print(f"❌ Error loading Constitution index: {e}")
        return []


def scrape_article_page(article_url: str, article_name: str, article_roman: str = "") -> List[Dict]:
    """
    Scrape sections from an article page
    Gets section links from article page, then visits each section page
    """
    print(f"\n📖 Scraping {article_name} from {article_url}")

    try:
        soup = fetch_page(article_url)
        sections_data = []

        # Find all links to sections
        section_links = soup.find_all("a", href=lambda x: x and "section-" in x)

        print(f"  Found {len(section_links)} section links")

        # Visit each section page
        for idx, link in enumerate(section_links, 1):
            try:
                section_href = link.get("href")
                if not section_href:
                    continue

                section_url = urljoin(BASE_URL, section_href)

                print(f"  [{idx}/{len(section_links)}] Fetching {section_url}")

                # Get the section page
                section_soup = fetch_page(section_url)

                # Get h1 - has everything: "Article I, Section 1|Inalienable Rights"
                h1 = section_soup.find("h1")
                header_text = h1.get_text(strip=True) if h1 else ""

                # Get all paragraphs - just grab them all, no filtering
                paragraphs = []
                for p in section_soup.find_all("p"):
                    text = p.get_text(strip=True)
                    if text:  # Any text at all
                        paragraphs.append(text)

                # Build the data - NO validation, just save what we got
                section_data = {
                    "url": section_url,
                    "url_hash": url_hash(section_url),
                    "header": header_text,
                    "article_name": article_name,
                    "article_roman": article_roman,
                    "paragraphs": paragraphs
                }

                sections_data.append(section_data)
                print(f"    ✓ Header: {header_text}")
                print(f"    ✓ Paragraphs: {len(paragraphs)}")

                time.sleep(0.5)

            except Exception as e:
                print(f"    ❌ Error: {e}")
                continue

        return sections_data

    except Exception as e:
        print(f"❌ Error scraping article page: {e}")
        return []


class OhioConstitutionScraper:
    """
    Main scraper for Ohio Constitution
    """
    def __init__(self, state_file: str = "scraper_state_constitution.json", output_dir: str = None):
        self.state_file = state_file

        # Set absolute path for output directory
        if output_dir is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            # From scraper/ go up one level to ohio_constitution/, then to data/scraped_constitution
            self.output_dir = os.path.join(script_dir, "../data/scraped_constitution")
        else:
            self.output_dir = output_dir

        self.visited_articles: Set[str] = set()
        self.all_scraped_data: List[Dict] = []

        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        print(f"📁 Output directory: {os.path.abspath(self.output_dir)}")

        self.load_state()

    def save_state(self):
        """Persist scraper state to file"""
        state = {
            "visited_articles": list(self.visited_articles),
            "scraped_count": len(self.all_scraped_data)
        }
        with open(self.state_file, "w") as f:
            json.dump(state, f, indent=2)

    def load_state(self):
        """Load previous scraper state if exists"""
        try:
            with open(self.state_file) as f:
                content = f.read().strip()
                if not content:  # Handle empty file
                    print("🆕 Starting fresh - state file is empty")
                    return
                state = json.loads(content)
            self.visited_articles = set(state.get("visited_articles", []))
            print(f"📂 Loaded state: {len(self.visited_articles)} visited articles")
        except FileNotFoundError:
            print("🆕 Starting fresh - no previous state found")
        except json.JSONDecodeError as e:
            print(f"⚠️ State file corrupted, starting fresh: {e}")

    def save_results(self, filename: str = "ohio_constitution_complete.json"):
        """Save all scraped data to JSON file"""
        output_path = os.path.join(self.output_dir, filename)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.all_scraped_data, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Saved {len(self.all_scraped_data)} sections to {output_path}")

        # Also save as JSONL
        jsonl_path = os.path.join(self.output_dir, "ohio_constitution_complete.jsonl")
        with open(jsonl_path, "w", encoding="utf-8") as f:
            for item in self.all_scraped_data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

        print(f"💾 Saved JSONL to {jsonl_path}")

    def scrape_all(self):
        """Scrape entire Ohio Constitution"""
        print("=" * 80)
        print("OHIO CONSTITUTION SCRAPER")
        print("=" * 80)

        # Get all article URLs
        articles = get_all_article_urls()

        if not articles:
            print("❌ No articles found!")
            return

        print(f"\n🎯 Will scrape {len(articles)} articles")

        # Scrape each article
        for idx, article in enumerate(articles, 1):
            article_url = article["url"]
            article_name = article["text"]

            # Skip if already visited
            if article_url in self.visited_articles:
                print(f"\n[{idx}/{len(articles)}] ⏭️ Skipping {article_name} (already scraped)")
                continue

            print(f"\n[{idx}/{len(articles)}] Processing {article_name}")

            # Scrape all sections from this article
            article_roman = article.get("roman", "")
            sections = scrape_article_page(article_url, article_name, article_roman)

            if sections:
                self.all_scraped_data.extend(sections)
                self.visited_articles.add(article_url)
                print(f"  ✓ Added {len(sections)} sections")

                # Save state after each article
                self.save_state()
            else:
                print(f"  ⚠️ No sections found for {article_name}")

            # Be nice to the server
            time.sleep(2)

        # Final save
        self.save_results()

        print("\n" + "=" * 80)
        print(f"✅ SCRAPING COMPLETE")
        print(f"Total sections scraped: {len(self.all_scraped_data)}")
        print(f"Articles completed: {len(self.visited_articles)}")
        print("=" * 80)


def main():
    """Main entry point"""
    scraper = OhioConstitutionScraper()
    scraper.scrape_all()


if __name__ == "__main__":
    main()
