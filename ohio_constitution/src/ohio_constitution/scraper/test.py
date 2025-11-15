import requests
from urllib.parse import urljoin


def test_url_resolution ():
    """
    Test different ways of resolving the section URLs to see which works
    """
    base_page = "https://codes.ohio.gov/ohio-constitution/article-1"
    section_href = "section-1.1"

    # Method 1: Direct join (what we were doing - WRONG)
    wrong_url = urljoin ("https://codes.ohio.gov",section_href)
    print (f"Method 1 (Wrong): {wrong_url}")

    # Method 2: Join from the article page context (CORRECT)
    correct_url = urljoin (base_page,section_href)
    print (f"Method 2 (Correct): {correct_url}")

    # Method 3: Manual construction based on patterns we see
    manual_url = f"https://codes.ohio.gov/ohio-constitution/{section_href}"
    print (f"Method 3 (Manual): {manual_url}")

    print ("\nTesting which URLs actually work:")
    print ("="*50)

    headers = {"User-Agent":"Mozilla/5.0 (OhioScraper/1.0)"}

    for name,url in [("Wrong",wrong_url),("Correct",correct_url),("Manual",manual_url)]:
        try:
            response = requests.head (url,headers=headers,timeout=10)
            print (f"✅ {name:8} ({response.status_code}): {url}")
        except requests.exceptions.RequestException as e:
            print (f"❌ {name:8} (ERROR): {url}")
            print (f"   Error: {e}")
        print ()


if __name__ == "__main__":
    test_url_resolution ()