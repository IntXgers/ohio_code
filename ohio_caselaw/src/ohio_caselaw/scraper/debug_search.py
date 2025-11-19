#!/usr/bin/env python3
"""
Debug script to inspect search form submission
"""
import requests
from bs4 import BeautifulSoup
import json

BASE_URL = "https://www.supremecourt.ohio.gov/rod/docs/"

def debug_search():
    """Debug a single search to see what's happening"""

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    })

    # Get initial page
    print("Fetching initial page...")
    response = session.get(BASE_URL)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract ViewState
    viewstate = soup.find('input', {'name': '__VIEWSTATE'})
    viewstate_gen = soup.find('input', {'name': '__VIEWSTATEGENERATOR'})
    event_val = soup.find('input', {'name': '__EVENTVALIDATION'})

    print(f"\n__VIEWSTATE: {viewstate['value'][:50]}..." if viewstate else "NOT FOUND")
    print(f"__VIEWSTATEGENERATOR: {viewstate_gen['value']}" if viewstate_gen else "NOT FOUND")
    print(f"__EVENTVALIDATION: {event_val['value'][:50]}..." if event_val else "NOT FOUND")

    # Check all form fields
    print("\n" + "="*80)
    print("FORM FIELDS ON PAGE:")
    print("="*80)
    all_inputs = soup.find_all('input')
    for inp in all_inputs:
        name = inp.get('name', '')
        input_type = inp.get('type', '')
        value = inp.get('value', '')
        if name:
            print(f"{name}: type={input_type}, value={value[:50] if value else '(empty)'}")

    # Check dropdowns
    print("\n" + "="*80)
    print("DROPDOWNS:")
    print("="*80)
    all_selects = soup.find_all('select')
    for select in all_selects:
        name = select.get('name', '')
        options = select.find_all('option')
        print(f"\n{name}:")
        for opt in options[:5]:  # First 5 options
            value = opt.get('value', '')
            text = opt.text.strip()
            print(f"  value='{value}' -> '{text}'")
        if len(options) > 5:
            print(f"  ... and {len(options) - 5} more options")

    # Submit search for Supreme Court 2020
    print("\n" + "="*80)
    print("SUBMITTING SEARCH: Supreme Court (0), Year 2020")
    print("="*80)

    data = {
        '__EVENTTARGET': '',
        '__EVENTARGUMENT': '',
        '__LASTFOCUS': '',
        '__VIEWSTATE': viewstate['value'] if viewstate else '',
        '__VIEWSTATEGENERATOR': viewstate_gen['value'] if viewstate_gen else '',
        '__SCROLLPOSITIONX': '0',
        '__SCROLLPOSITIONY': '0',
        '__EVENTVALIDATION': event_val['value'] if event_val else '',
        'ctl00$MainContent$tbQueryText': '',
        'ctl00$MainContent$ddlCourt': '0',
        'ctl00$MainContent$ddlDecidedYearMin': '2020',
        'ctl00$MainContent$ddlDecidedYearMax': '2020',
        'ctl00$MainContent$ddlCounty': '0',
        'ctl00$MainContent$tbCaseNumber': '',
        'ctl00$MainContent$tbAuthor': '',
        'ctl00$MainContent$tbTopics': '',
        'ctl00$MainContent$tbWebCiteNoYear': '',
        'ctl00$MainContent$tbWebCiteNoNumber': '',
        'ctl00$MainContent$tbCitation': '',
        'ctl00$MainContent$ddlRowsPerPage': '50',
        'ctl00$MainContent$btnSubmit': 'Submit'
    }

    print("\nPOST Data:")
    for key, value in data.items():
        if '__VIEW' not in key and '__EVENT' not in key:
            print(f"  {key} = '{value}'")

    response = session.post(BASE_URL, data=data)

    # Parse response
    soup = BeautifulSoup(response.text, 'html.parser')

    # Check result count
    row_count = soup.find('span', {'id': 'MainContent_lblRowCount'})
    if row_count:
        print(f"\nResult: {row_count.text}")
    else:
        print("\nNo result count found!")

    # Check first few cases
    table = soup.find('table', {'id': 'MainContent_gvResults'})
    if table:
        rows = table.find_all('tr')
        print(f"\nFound {len(rows)} rows in table")

        # Get first data row
        for row in rows:
            if row.find('th'):
                continue
            cells = row.find_all('td')
            if len(cells) < 6:
                continue

            # Get first case
            case_link = cells[0].find('a', href=True)
            if case_link and not case_link['href'].startswith('javascript:'):
                webcite = cells[-1].text.strip()
                case_name = case_link.text.strip()
                decided = cells[3].text.strip() if len(cells) > 3 else ""

                print(f"\nFirst case:")
                print(f"  WebCite: {webcite}")
                print(f"  Name: {case_name}")
                print(f"  Decided: {decided}")
                print(f"  PDF: {case_link['href']}")
                break
    else:
        print("\nNo results table found!")

    # Save response for manual inspection
    with open('/tmp/ohio_search_response.html', 'w') as f:
        f.write(response.text)
    print("\nFull response saved to: /tmp/ohio_search_response.html")

if __name__ == "__main__":
    debug_search()
