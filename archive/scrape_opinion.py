def extract_total_results(self, html):
    """Extract total result count from page"""
    soup = BeautifulSoup(html, 'html.parser')

    # This element MUST exist
    row_count = soup.find('span', {'id': 'MainContent_lblRowCount'})
    if not row_count:
        raise Exception("CRITICAL: Could not find MainContent_lblRowCount span - page structure changed!")

    text = row_count.text
    # Format: "This search returned XXX rows."
    match = re.search(r'(\d+)\s+rows', text)

    if not match:
        raise Exception(f"CRITICAL: Could not parse result count from: '{text}'")

    return int(match.group(1))

def calculate_total_pages(self, total_results, results_per_page=50):
    """Calculate total pages based on result count"""
    if total_results == 0:
        return 1
    # Website shows 50 results per page regardless of our request
    import math
    return math.ceil(total_results / results_per_page)