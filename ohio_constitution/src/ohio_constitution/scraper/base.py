"""
Generic Web Scraping Framework
Provides reusable components for building site-specific scrapers
"""

import requests
from bs4 import BeautifulSoup
import time
import json
import hashlib
from urllib.parse import urljoin,urlparse
from typing import Dict,List,Optional,Set,Callable,Any
from abc import ABC,abstractmethod
import logging
from dataclasses import dataclass,field


@dataclass
class ScrapingConfig:
    """Configuration for scraping behavior"""
    delay_between_requests: float = 1.0
    max_retries: int = 3
    timeout: int = 10
    user_agent: str = "Mozilla/5.0 (GenericScraper/1.0)"
    respect_robots_txt: bool = True
    save_state: bool = True
    state_file: str = "scraper_state.json"


@dataclass
class ContentItem:
    """Standardized data structure for scraped content"""
    url: str
    title: str = ""
    content: str = ""
    metadata: Dict [str,Any] = field (default_factory=dict)
    links: List [str] = field (default_factory=list)
    timestamp: float = field (default_factory=time.time)

    def to_dict (self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "url":self.url,
            "title":self.title,
            "content":self.content,
            "metadata":self.metadata,
            "links":self.links,
            "timestamp":self.timestamp
            }


class BaseScraper (ABC):
    """
    Abstract base class that provides common scraping infrastructure.
    Site-specific scrapers inherit from this and implement the abstract methods.
    """

    def __init__ (self,config: ScrapingConfig = None):
        self.config = config or ScrapingConfig ()
        self.session = requests.Session ()
        self.session.headers.update ({"User-Agent":self.config.user_agent})

        # State management
        self.visited_urls: Set [str] = set ()
        self.scraped_items: List [ContentItem] = []
        self.failed_urls: Set [str] = set ()

        # Setup logging
        logging.basicConfig (level=logging.INFO)
        self.logger = logging.getLogger (self.__class__.__name__)

        if self.config.save_state:
            self.load_state ()

    def fetch_page (self,url: str) -> Optional [BeautifulSoup]:
        """
        Robust page fetching with retries and error handling.
        This is reusable across all scrapers.
        """
        for attempt in range (self.config.max_retries):
            try:
                self.logger.info (f"Fetching: {url} (attempt {attempt + 1})")
                response = self.session.get (url,timeout=self.config.timeout)
                response.raise_for_status ()

                # Add delay to be respectful
                time.sleep (self.config.delay_between_requests)

                return BeautifulSoup (response.text,"html.parser")

            except requests.exceptions.RequestException as e:
                self.logger.warning (f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt == self.config.max_retries - 1:
                    self.failed_urls.add (url)
                    return None
                time.sleep (2**attempt)  # Exponential backoff

        return None

    def save_state (self):
        """Save scraping progress to resume later"""
        if not self.config.save_state:
            return

        state = {
            "visited_urls":list (self.visited_urls),
            "failed_urls":list (self.failed_urls),
            "scraped_count":len (self.scraped_items),
            "scraper_class":self.__class__.__name__
            }

        with open (self.config.state_file,"w") as f:
            json.dump (state,f,indent=2)

    def load_state (self):
        """Load previous scraping state"""
        try:
            with open (self.config.state_file) as f:
                state = json.load (f)

            self.visited_urls = set (state.get ("visited_urls",[]))
            self.failed_urls = set (state.get ("failed_urls",[]))

            self.logger.info (f"Loaded state: {len (self.visited_urls)} visited URLs")

        except FileNotFoundError:
            self.logger.info ("No previous state found, starting fresh")

    def save_results (self,filename: str):
        """Save scraped content to JSON file"""
        data = [item.to_dict () for item in self.scraped_items]
        with open (filename,"w",encoding="utf-8") as f:
            json.dump (data,f,indent=2,ensure_ascii=False)

        self.logger.info (f"Saved {len (data)} items to {filename}")

    # Abstract methods that site-specific scrapers must implement
    @abstractmethod
    def get_start_urls (self) -> List [str]:
        """Return list of URLs to start scraping from"""
        pass

    @abstractmethod
    def extract_content (self,soup: BeautifulSoup,url: str) -> ContentItem:
        """Extract content from a page and return structured data"""
        pass

    @abstractmethod
    def find_next_urls (self,soup: BeautifulSoup,current_url: str) -> List [str]:
        """Find URLs to scrape next from the current page"""
        pass

    @abstractmethod
    def should_scrape_url (self,url: str) -> bool:
        """Determine if a URL should be scraped (filtering logic)"""
        pass

    def scrape (self):
        """
        Main scraping orchestration method.
        This workflow is reusable across different sites.
        """
        self.logger.info ("Starting scrape")

        # Get starting URLs from the site-specific implementation
        start_urls = self.get_start_urls ()
        urls_to_visit = set (start_urls) - self.visited_urls

        while urls_to_visit:
            current_url = urls_to_visit.pop ()

            if not self.should_scrape_url (current_url):
                continue

            if current_url in self.visited_urls:
                continue

            # Fetch and parse the page
            soup = self.fetch_page (current_url)
            if not soup:
                continue

            # Extract content using site-specific logic
            try:
                content_item = self.extract_content (soup,current_url)
                self.scraped_items.append (content_item)
                self.visited_urls.add (current_url)

                self.logger.info (f"Scraped: {content_item.title}")

                # Find next URLs to visit
                next_urls = self.find_next_urls (soup,current_url)
                new_urls = set (next_urls) - self.visited_urls - urls_to_visit
                urls_to_visit.update (new_urls)

                # Save state periodically
                if len (self.scraped_items)%10 == 0:
                    self.save_state ()

            except Exception as e:
                self.logger.error (f"Error processing {current_url}: {e}")
                self.failed_urls.add (current_url)

        self.logger.info (f"Scraping complete: {len (self.scraped_items)} items")
        self.save_state ()


class OhioConstitutionScraper (BaseScraper):
    """
    Site-specific implementation for Ohio Constitution.
    Notice how much simpler this is now that we have the framework!
    """

    def __init__ (self,config: ScrapingConfig = None):
        super ().__init__ (config)
        self.base_url = "https://codes.ohio.gov"
        self.constitution_base = f"{self.base_url}/ohio-constitution"

    def get_start_urls (self) -> List [str]:
        """Get all article URLs as starting points"""
        index_url = self.constitution_base
        soup = self.fetch_page (index_url)
        if not soup:
            return []

        article_links = soup.select ("a[href*='ohio-constitution/article-']")
        return [urljoin (self.base_url,link.get ("href")) for link in article_links]

    def extract_content (self,soup: BeautifulSoup,url: str) -> ContentItem:
        """Extract section content from Ohio Constitution pages"""
        # Extract title
        h1 = soup.find ("h1")
        title = h1.get_text (strip=True) if h1 else ""

        # Extract main content
        body = soup.find ("section",class_="laws-body")
        content_paragraphs = []
        if body:
            content_paragraphs = [p.get_text (strip=True) for p in body.find_all ("p")]

        content = "\n\n".join (content_paragraphs)

        # Extract metadata
        metadata = {
            "content_type":"constitution_section",
            "paragraph_count":len (content_paragraphs)
            }

        return ContentItem (
            url=url,
            title=title,
            content=content,
            metadata=metadata
            )

    def find_next_urls (self,soup: BeautifulSoup,current_url: str) -> List [str]:
        """Find section links and next navigation links"""
        urls = []

        # If we're on an article page, find all section links
        if "/article-" in current_url and "/section-" not in current_url:
            section_links = soup.select ("a[href^='section-']")
            for link in section_links:
                section_url = urljoin (current_url,link.get ("href"))
                urls.append (section_url)

        # If we're on a section page, find the next section
        elif "/section-" in current_url:
            next_link = soup.select_one (".profile-navigator .next a")
            if next_link and next_link.get ("href"):
                next_url = urljoin (self.base_url,next_link ["href"])
                urls.append (next_url)

        return urls

    def should_scrape_url (self,url: str) -> bool:
        """Only scrape Ohio Constitution section pages"""
        return (
                url.startswith (self.constitution_base) and
                ("/section-" in url or "/article-" in url)
        )


# Example of how easy it would be to create a scraper for a different site
class ExampleNewsScraper (BaseScraper):
    """
    Example of how to implement a scraper for a news site.
    Most of the infrastructure is already handled by BaseScraper.
    """

    def get_start_urls (self) -> List [str]:
        return ["https://example-news.com/latest"]

    def extract_content (self,soup: BeautifulSoup,url: str) -> ContentItem:
        title = soup.find ("h1",class_="article-title")
        content = soup.find ("div",class_="article-content")

        return ContentItem (
            url=url,
            title=title.get_text (strip=True) if title else "",
            content=content.get_text (strip=True) if content else "",
            metadata={"content_type":"news_article"}
            )

    def find_next_urls (self,soup: BeautifulSoup,current_url: str) -> List [str]:
        article_links = soup.select ("a.article-link")
        return [urljoin (current_url,link.get ("href")) for link in article_links]

    def should_scrape_url (self,url: str) -> bool:
        return "example-news.com" in url and "/article/" in url


def main ():
    """Example usage"""
    # Configure scraping behavior
    config = ScrapingConfig (
        delay_between_requests=1.5,
        save_state=True,
        state_file="ohio_constitution_state.json"
        )

    # Create and run the Ohio Constitution scraper
    scraper = OhioConstitutionScraper (config)

    try:
        scraper.scrape ()
        scraper.save_results ("ohio_constitution_complete.json")

    except KeyboardInterrupt:
        print ("\nScraping interrupted by user")
        scraper.save_state ()
        scraper.save_results ("ohio_constitution_partial.json")


if __name__ == "__main__":
    main ()