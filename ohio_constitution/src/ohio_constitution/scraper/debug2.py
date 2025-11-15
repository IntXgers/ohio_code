import os
import requests
from bs4 import BeautifulSoup
import time
import json
import hashlib
from urllib.parse import urljoin
from typing import Set, Dict, List, Optional
import traceback
from datetime import datetime

BASE_URL = "https://codes.ohio.gov"
INDEX_URL = f"{BASE_URL}/ohio-constitution"

ROMAN_MAP = {
    'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5,
    'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10,
    'XI': 11, 'XII': 12, 'XIII': 13, 'XIV': 14, 'XV': 15,
    'XVI': 16, 'XVII': 17, 'XVIII': 18
}


def debug_request(url: str):
    """Debug a single request with detailed error info"""
    print(f"\n{'=' * 60}")
    print(f"🔍 DEBUG REQUEST: {url}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Try different approaches
    approaches = [
        {
            "name": "Basic Request",
            "func": lambda: requests.get(url, timeout=30)
        },
        {
            "name": "With Headers",
            "func": lambda: requests.get(url,
                                         headers={
                                             'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                                             'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                                             'Accept-Language': 'en-US,en;q=0.5',
                                             'Accept-Encoding': 'gzip, deflate',
                                             'Connection': 'keep-alive',
                                         },
                                         timeout=60)
        },
        {
            "name": "With Session",
            "func": lambda: requests.Session().get(url, timeout=60)
        }
    ]

    for approach in approaches:
        print(f"\n📋 Trying: {approach['name']}")
        try:
            start_time = time.time()
            response = approach['func']()
            elapsed = time.time() - start_time

            print(f"✅ Success!")
            print(f"   Status Code: {response.status_code}")
            print(f"   Response Time: {elapsed:.2f}s")
            print(f"   Content Length: {len(response.content)} bytes")
            print(f"   Headers: {dict(response.headers)}")
            return response

        except requests.exceptions.SSLError as e:
            print(f"❌ SSL Error: {e}")
            print(f"   Full trace: {traceback.format_exc()}")

        except requests.exceptions.Timeout as e:
            print(f"❌ Timeout Error: {e}")
            elapsed = time.time() - start_time
            print(f"   Failed after: {elapsed:.2f}s")

        except requests.exceptions.ConnectionError as e:
            print(f"❌ Connection Error: {e}")
            print(f"   Full trace: {traceback.format_exc()}")

        except Exception as e:
            print(f"❌ Unexpected Error ({type(e).__name__}): {e}")
            print(f"   Full trace: {traceback.format_exc()}")

    print(f"\n🚨 All approaches failed for {url}")
    return None


def fetch_page(url: str) -> BeautifulSoup:
    """Fetch page with detailed debugging"""
    print(f"\n🌐 Fetching: {url}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    }

    # Debug: Show exactly what we're sending
    print(f"📤 Request Headers: {json.dumps(headers, indent=2)}")

    try:
        # Create session to reuse connection
        session = requests.Session()
        session.headers.update(headers)

        print(f"⏱️  Starting request at {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
        response = session.get(url, timeout=120)
        print(f"✅ Response received at {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")

        response.raise_for_status()
        print(f"📊 Status: {response.status_code}, Size: {len(response.content)} bytes")

        return BeautifulSoup(response.text, "html.parser")

    except Exception as e:
        print(f"❌ Error in fetch_page: {type(e).__name__}: {e}")
        raise


def get_all_article_entrypoints() -> List[Dict[str, str]]:
    """Extract all article links with debugging"""
    print(f"\n🔍 Getting article entrypoints from: {INDEX_URL}")

    try:
        # First, let's debug the connection to the main index
        response = debug_request(INDEX_URL)
        if not response:
            print("❌ Could not connect to index page")
            return []

        soup = BeautifulSoup(response.text, "html.parser")

        # Debug: Show what we're looking for
        print(f"\n🔍 Looking for links matching: a[href*='ohio-constitution/article-']")

        links = soup.select("a[href*='ohio-constitution/article-']")
        print(f"📊 Found {len(links)} article links")

        articles = []

        for i, link in enumerate(links):
            href = link.get("href")
            print(f"\n  [{i + 1}] Processing link: {href}")

            full_url = urljoin(BASE_URL, href)
            print(f"      Full URL: {full_url}")

            text = ''.join(link.stripped_strings)
            print(f"      Text: '{text}'")

            parts = text.split()
            roman = parts[1].upper().strip() if len(parts) > 1 else ""
            article_num = roman_to_int(roman)
            print(f"      Roman: {roman} → Number: {article_num}")

            articles.append({
                "roman": roman,
                "num": article_num,
                "text": text,
                "url": full_url
            })

        print(f"\n📘 Successfully parsed {len(articles)} articles")
        return articles

    except Exception as e:
        print(f"❌ Error in get_all_article_entrypoints: {type(e).__name__}: {e}")
        print(f"   Full trace: {traceback.format_exc()}")
        return []


class OhioConstitutionScraper:
    def __init__(self, state_file: str = "scraper_state_constitution.json"):
        print(f"\n🚀 Initializing OhioConstitutionScraper")
        print(f"📁 State file: {state_file}")

        self.state_file = state_file
        self.visited_urls: Set[str] = set()
        self.completed_articles: Dict[str, Set[str]] = {}
        self.all_scraped_data: List[Dict] = []
        self.load_state()

    def crawl_sections_from_article(self, first_section_url: str) -> List[Dict]:
        """Crawl with detailed debugging"""
        article_data = []
        current_url = first_section_url
        article_section_visited = set()

        print(f"\n📖 Starting section crawl from: {first_section_url}")

        section_count = 0
        while current_url and current_url not in article_section_visited:
            section_count += 1
            print(f"\n  🔄 Section #{section_count}")
            print(f"      URL: {current_url}")

            if current_url in self.visited_urls:
                print(f"      ⭕ Already in visited_urls, skipping")
                break

            try:
                print(f"      🌐 Fetching page...")
                soup = fetch_page(current_url)

                print(f"      📝 Extracting section data...")
                section_data = extract_section_data(soup, current_url)

                print(f"      ✅ Got header: {section_data['header']}")
                print(f"      📊 Paragraphs: {len(section_data['paragraphs'])}")

                article_data.append(section_data)
                article_section_visited.add(current_url)
                self.visited_urls.add(current_url)

                # Look for next section
                print(f"      🔍 Looking for next section link...")
                next_url = get_next_section_url(soup)

                if next_url:
                    print(f"      ➡️  Next URL found: {next_url}")
                    if next_url in article_section_visited:
                        print(f"      🔄 Loop detected! Stopping article crawl")
                        break
                else:
                    print(f"      🏁 No next URL - end of article")

                current_url = next_url

                print(f"      💤 Sleeping 1.5s...")
                time.sleep(1.5)

            except Exception as e:
                print(f"      ❌ Error: {type(e).__name__}: {e}")
                print(f"         Trace: {traceback.format_exc()}")
                break

        print(f"\n  📊 Article crawl complete: {len(article_data)} sections")
        return article_data

    def crawl_all_articles(self):
        """Main crawl with debugging"""
        print(f"\n{'=' * 60}")
        print("🚀 STARTING OHIO CONSTITUTION SCRAPE")
        print(f"{'=' * 60}")

        # First test if we can connect at all
        print("\n🧪 Testing basic connectivity...")
        test_response = debug_request(BASE_URL)
        if not test_response:
            print("❌ Cannot connect to base URL. Check network/VPN settings.")
            return

        print("\n✅ Basic connectivity OK, proceeding with article fetch...")

        articles = get_all_article_entrypoints()
        if not articles:
            print("⚠️  No articles found")
            return

        for article in articles:
            roman = article["roman"]
            article_num = article["num"]
            article_url = article["url"]
            article_hash = url_hash(article_url)

            print(f"\n{'=' * 60}")
            print(f"📂 ARTICLE {roman} (#{article_num})")
            print(f"URL: {article_url}")
            print(f"Hash: {article_hash}")

            article_key = "constitution"
            if article_key not in self.completed_articles:
                self.completed_articles[article_key] = set()

            if article_hash in self.completed_articles[article_key]:
                print(f"⭕ Already completed, skipping")
                continue

            try:
                print(f"\n🌐 Fetching article page...")
                time.sleep(1)
                soup = fetch_page(article_url)
                time.sleep(1)

                print(f"🔍 Looking for first section link...")
                first_section_link = soup.select_one("a[href^='section-']")

                if not first_section_link:
                    print(f"⚠️  No section links found inside article")
                    continue

                first_section_href = first_section_link.get("href")
                print(f"✅ Found first section: {first_section_href}")

                first_section_url = urljoin(BASE_URL, first_section_href)
                print(f"📍 Full first section URL: {first_section_url}")

                article_data = self.crawl_sections_from_article(first_section_url)
                self.all_scraped_data.extend(article_data)

                self.completed_articles[article_key].add(article_hash)
                self.save_state()

                print(f"\n✅ Article {roman} complete: {len(article_data)} sections")
                print(f"💤 Sleeping 2s before next article...")
                time.sleep(2)

            except Exception as e:
                print(f"\n❌ Error processing Article {roman}:")
                print(f"   Type: {type(e).__name__}")
                print(f"   Message: {e}")
                print(f"   Trace: {traceback.format_exc()}")
                continue

        print(f"\n{'=' * 60}")
        print(f"🎉 ALL ARTICLES COMPLETE")
        print(f"📊 Total sections scraped: {len(self.all_scraped_data)}")
        print(f"{'=' * 60}")

# Keep all other functions the same...