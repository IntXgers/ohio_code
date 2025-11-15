import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


def debug_article_page (article_url):
    """
    Debug function to examine what's actually on an article page
    """
    print (f"🔍 Debugging: {article_url}")

    headers = {"User-Agent":"Mozilla/5.0 (OhioScraper/1.0)"}
    response = requests.get (article_url,headers=headers,timeout=10)
    response.raise_for_status ()
    soup = BeautifulSoup (response.text,"html.parser")

    print ("="*60)
    print ("ALL LINKS ON THE PAGE:")
    print ("="*60)

    # Find ALL links on the page
    all_links = soup.find_all ("a",href=True)
    for i,link in enumerate (all_links [:20]):  # Show first 20 links
        href = link.get ("href")
        text = link.get_text (strip=True)
        full_url = urljoin ("https://codes.ohio.gov",href)
        print (f"{i + 1:2d}. href='{href}' -> '{full_url}'")
        print (f"    text: '{text}'")
        print ()

    print ("="*60)
    print ("LINKS CONTAINING 'section':")
    print ("="*60)

    # Find links containing 'section'
    section_links = soup.find_all ("a",href=lambda x:x and "section" in x.lower ())
    for i,link in enumerate (section_links):
        href = link.get ("href")
        text = link.get_text (strip=True)
        full_url = urljoin ("https://codes.ohio.gov",href)
        print (f"{i + 1}. href='{href}' -> '{full_url}'")
        print (f"   text: '{text}'")
        print ()

    print ("="*60)
    print ("PAGE TITLE AND MAIN CONTENT STRUCTURE:")
    print ("="*60)

    title = soup.find ("title")
    if title:
        print (f"Title: {title.get_text (strip=True)}")

    # Look for main content areas
    main_content = soup.find ("main") or soup.find ("div",class_="content") or soup.find ("div",id="content")
    if main_content:
        print ("\nMain content structure:")
        # Show the first few elements in main content
        for child in main_content.children:
            if hasattr (child,'name') and child.name:
                print (f"  <{child.name}> {child.get ('class','')} - {child.get_text (strip=True) [:100]}...")

    return soup


# Test with the first article
if __name__ == "__main__":
    debug_article_page ("https://codes.ohio.gov/ohio-constitution/article-1")