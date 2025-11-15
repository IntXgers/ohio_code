"""
Complete Ohio Revised Code Title Mapping
Based on official structure from codes.ohio.gov
"""


def get_title_from_section(section_num):
    """
    Complete mapping of Ohio Revised Code chapter numbers to titles

    Args:
        section_num: Section number like "101.11" or "3503.19"

    Returns:
        String: Title name or None if not found
    """
    try:
        if '.' in section_num:
            chapter = int(section_num.split('.')[0])
        else:
            chapter = int(section_num)
    except (ValueError, IndexError):
        return None

    # Complete Ohio Revised Code chapter-to-title mapping
    # All titles use odd numbers except Title 58
    chapter_mapping = {
        # Title 1 - General Provisions
        range(101, 200): "Title 1 - General Provisions",

        # Title 3 - State Government
        range(301, 400): "Title 3 - State Government",

        # Title 5 - Townships
        range(501, 600): "Title 5 - Townships",

        # Title 7 - Municipal Corporations
        range(701, 800): "Title 7 - Municipal Corporations",

        # Title 9 - Agriculture-Animals-Fences
        range(901, 1000): "Title 9 - Agriculture-Animals-Fences",

        # Title 11 - Banks-Savings and Loan Associations
        range(1101, 1200): "Title 11 - Banks-Savings and Loan Associations",

        # Title 13 - Commercial Transactions
        range(1301, 1400): "Title 13 - Commercial Transactions",

        # Title 15 - Conservation of Natural Resources
        range(1501, 1600): "Title 15 - Conservation of Natural Resources",

        # Title 17 - Corporations-Partnerships
        range(1701, 1800): "Title 17 - Corporations-Partnerships",

        # Title 19 - Courts-Municipal-Mayor's-County
        range(1901, 2000): "Title 19 - Courts-Municipal-Mayor's-County",

        # Title 21 - Courts-Probate-Juvenile
        range(2101, 2200): "Title 21 - Courts-Probate-Juvenile",

        # Title 23 - Courts-Common Pleas
        range(2301, 2400): "Title 23 - Courts-Common Pleas",

        # Title 25 - Courts-Appellate
        range(2501, 2600): "Title 25 - Courts-Appellate",

        # Title 27 - Courts-General Provisions-Special Remedies
        range(2701, 2800): "Title 27 - Courts-General Provisions-Special Remedies",

        # Title 29 - Crimes-Procedure
        range(2901, 3000): "Title 29 - Crimes-Procedure",

        # Title 31 - Domestic Relations-Children
        range(3101, 3200): "Title 31 - Domestic Relations-Children",

        # Title 33 - Education-Libraries
        range(3301, 3400): "Title 33 - Education-Libraries",

        # Title 35 - Elections
        range(3501, 3600): "Title 35 - Elections",

        # Title 37 - Health-Safety-Morals
        range(3701, 3800): "Title 37 - Health-Safety-Morals",

        # Title 39 - Insurance
        range(3901, 4000): "Title 39 - Insurance",

        # Title 41 - Labor and Industry
        range(4101, 4200): "Title 41 - Labor and Industry",

        # Title 43 - Liquor
        range(4301, 4400): "Title 43 - Liquor",

        # Title 45 - Motor Vehicles-Aeronautics-Watercraft
        range(4501, 4600): "Title 45 - Motor Vehicles-Aeronautics-Watercraft",

        # Title 47 - Occupations-Professions
        range(4701, 4800): "Title 47 - Occupations-Professions",

        # Title 49 - Public Utilities
        range(4901, 5000): "Title 49 - Public Utilities",

        # Title 51 - Public Welfare
        range(5101, 5200): "Title 51 - Public Welfare",

        # Title 53 - Real Property
        range(5301, 5400): "Title 53 - Real Property",

        # Title 55 - Roads-Highways-Bridges
        range(5501, 5600): "Title 55 - Roads-Highways-Bridges",

        # Title 57 - Taxation
        range(5701, 5800): "Title 57 - Taxation",

        # Title 58 - Trusts (only even-numbered title)
        range(5801, 5900): "Title 58 - Trusts",

        # Title 59 - Veterans-Military Affairs
        range(5901, 6000): "Title 59 - Veterans-Military Affairs",

        # Title 61 - Water Supply-Sanitation-Ditches
        range(6101, 6200): "Title 61 - Water Supply-Sanitation-Ditches",

        # Title 63 - Workforce Development
        range(6301, 6400): "Title 63 - Workforce Development"
    }

    # Find matching title
    for chapter_range, title in chapter_mapping.items():
        if chapter in chapter_range:
            return title

    return f"Unknown Title (Chapter {chapter})"


# List of all Ohio Revised Code titles for reference
OHIO_REVISED_CODE_TITLES = [
    "Title 1 - General Provisions",
    "Title 3 - State Government",
    "Title 5 - Townships",
    "Title 7 - Municipal Corporations",
    "Title 9 - Agriculture-Animals-Fences",
    "Title 11 - Banks-Savings and Loan Associations",
    "Title 13 - Commercial Transactions",
    "Title 15 - Conservation of Natural Resources",
    "Title 17 - Corporations-Partnerships",
    "Title 19 - Courts-Municipal-Mayor's-County",
    "Title 21 - Courts-Probate-Juvenile",
    "Title 23 - Courts-Common Pleas",
    "Title 25 - Courts-Appellate",
    "Title 27 - Courts-General Provisions-Special Remedies",
    "Title 29 - Crimes-Procedure",
    "Title 31 - Domestic Relations-Children",
    "Title 33 - Education-Libraries",
    "Title 35 - Elections",
    "Title 37 - Health-Safety-Morals",
    "Title 39 - Insurance",
    "Title 41 - Labor and Industry",
    "Title 43 - Liquor",
    "Title 45 - Motor Vehicles-Aeronautics-Watercraft",
    "Title 47 - Occupations-Professions",
    "Title 49 - Public Utilities",
    "Title 51 - Public Welfare",
    "Title 53 - Real Property",
    "Title 55 - Roads-Highways-Bridges",
    "Title 57 - Taxation",
    "Title 58 - Trusts",
    "Title 59 - Veterans-Military Affairs",
    "Title 61 - Water Supply-Sanitation-Ditches",
    "Title 63 - Workforce Development"
]

# Chapter ranges for quick reference
TITLE_CHAPTER_RANGES = {
    "Title 1 - General Provisions": "101-199",
    "Title 3 - State Government": "301-399",
    "Title 5 - Townships": "501-599",
    "Title 7 - Municipal Corporations": "701-799",
    "Title 9 - Agriculture-Animals-Fences": "901-999",
    "Title 11 - Banks-Savings and Loan Associations": "1101-1199",
    "Title 13 - Commercial Transactions": "1301-1399",
    "Title 15 - Conservation of Natural Resources": "1501-1599",
    "Title 17 - Corporations-Partnerships": "1701-1799",
    "Title 19 - Courts-Municipal-Mayor's-County": "1901-1999",
    "Title 21 - Courts-Probate-Juvenile": "2101-2199",
    "Title 23 - Courts-Common Pleas": "2301-2399",
    "Title 25 - Courts-Appellate": "2501-2599",
    "Title 27 - Courts-General Provisions-Special Remedies": "2701-2799",
    "Title 29 - Crimes-Procedure": "2901-2999",
    "Title 31 - Domestic Relations-Children": "3101-3199",
    "Title 33 - Education-Libraries": "3301-3399",
    "Title 35 - Elections": "3501-3599",
    "Title 37 - Health-Safety-Morals": "3701-3799",
    "Title 39 - Insurance": "3901-3999",
    "Title 41 - Labor and Industry": "4101-4199",
    "Title 43 - Liquor": "4301-4399",
    "Title 45 - Motor Vehicles-Aeronautics-Watercraft": "4501-4599",
    "Title 47 - Occupations-Professions": "4701-4799",
    "Title 49 - Public Utilities": "4901-4999",
    "Title 51 - Public Welfare": "5101-5199",
    "Title 53 - Real Property": "5301-5399",
    "Title 55 - Roads-Highways-Bridges": "5501-5599",
    "Title 57 - Taxation": "5701-5799",
    "Title 58 - Trusts": "5801-5899",
    "Title 59 - Veterans-Military Affairs": "5901-5999",
    "Title 61 - Water Supply-Sanitation-Ditches": "6101-6199",
    "Title 63 - Workforce Development": "6301-6399"
}