"""
Ohio Constitution Article Mapping
Maps articles to their names and categories
"""

import re
from typing import Optional


def get_article_name(section_id: str) -> Optional[str]:
    """
    Get the article name from a section identifier

    Args:
        section_id: Section identifier like "Article I, Section 1" or "I.1"

    Returns:
        String: Article name or None if not found
    """
    # Extract article number (roman numeral)
    article_match = re.search(r'Article\s+([IVXLCDM]+)', section_id, re.IGNORECASE)
    if not article_match:
        # Try shorthand format "I.1"
        article_match = re.match(r'^([IVXLCDM]+)\.', section_id)

    if not article_match:
        return None

    article_num = article_match.group(1).upper()
    return OHIO_CONSTITUTION_ARTICLES.get(article_num)


def get_article_category(section_id: str) -> Optional[str]:
    """
    Get the category of an article (bill_of_rights, structure, etc.)

    Args:
        section_id: Section identifier like "Article I, Section 1"

    Returns:
        String: Category name or None
    """
    article_name = get_article_name(section_id)
    if not article_name:
        return None

    # Map article to category
    if "Bill of Rights" in article_name:
        return "bill_of_rights"
    elif "Legislative" in article_name:
        return "legislative_branch"
    elif "Executive" in article_name:
        return "executive_branch"
    elif "Judicial" in article_name:
        return "judicial_branch"
    elif "Education" in article_name or "School" in article_name:
        return "education"
    elif "Election" in article_name or "Suffrage" in article_name:
        return "elections"
    elif "Finance" in article_name or "Revenue" in article_name or "Taxation" in article_name:
        return "finance"
    elif "Municipal" in article_name or "Corporation" in article_name:
        return "municipal"
    elif "Public" in article_name:
        return "public_institutions"
    elif "Amendment" in article_name or "Revision" in article_name:
        return "amendments"
    else:
        return "other"


# Ohio Constitution Articles (19 total)
OHIO_CONSTITUTION_ARTICLES = {
    "I": "Article I - Bill of Rights",
    "II": "Article II - Legislative",
    "III": "Article III - Executive",
    "IV": "Article IV - Judicial",
    "V": "Article V - Elective Franchise",
    "VI": "Article VI - Education",
    "VII": "Article VII - Public Institutions",
    "VIII": "Article VIII - Public Debt and Public Works",
    "IX": "Article IX - Militia",
    "X": "Article X - County and Township Organizations",
    "XI": "Article XI - Apportionment",
    "XII": "Article XII - Finance and Taxation",
    "XIII": "Article XIII - Corporations",
    "XIV": "Article XIV - Jurisprudence",
    "XV": "Article XV - Miscellaneous",
    "XVI": "Article XVI - Amendments",
    "XVII": "Article XVII - Elections",
    "XVIII": "Article XVIII - Municipal Corporations",
    "XIX": "Article XIX - Initiative and Referendum"
}

# Article descriptions for enrichment
ARTICLE_DESCRIPTIONS = {
    "I": "Fundamental individual rights and liberties",
    "II": "Structure and powers of the General Assembly",
    "III": "Powers and duties of the Governor and executive branch",
    "IV": "Structure and jurisdiction of the court system",
    "V": "Voting rights and qualifications",
    "VI": "Public education system and school funding",
    "VII": "State institutions for welfare and corrections",
    "VIII": "State borrowing and public works limitations",
    "IX": "State military forces and militia organization",
    "X": "County and township government structure",
    "XI": "Legislative and congressional district apportionment",
    "XII": "State revenue, taxation, and budget procedures",
    "XIII": "Regulation of corporations and business entities",
    "XIV": "Judicial procedures and court administration",
    "XV": "Provisions not fitting other articles",
    "XVI": "Process for amending the constitution",
    "XVII": "Election procedures and ballot measures",
    "XVIII": "Municipal home rule and local government powers",
    "XIX": "Citizen initiative and referendum procedures"
}

# Rights categories for Bill of Rights (Article I)
BILL_OF_RIGHTS_CATEGORIES = {
    "1": "inalienable_rights",
    "2": "government_powers",
    "3": "religious_freedom",
    "4": "habeas_corpus",
    "5": "trial_by_jury",
    "6": "slavery_prohibition",
    "7": "political_rights",
    "8": "writ_of_habeas_corpus",
    "9": "bail_and_punishment",
    "10": "criminal_procedure",
    "11": "free_speech",
    "12": "assembly_and_petition",
    "13": "quartering_soldiers",
    "14": "search_and_seizure",
    "15": "grand_jury",
    "16": "criminal_justice",
    "17": "civil_trials",
    "18": "suspension_of_laws",
    "19": "eminent_domain",
    "20": "powers_reserved",
}


def normalize_section_id(section_str: str) -> Optional[str]:
    """
    Normalize section identifier to standard format

    Args:
        section_str: Various formats like "Article I, Section 1", "I.1", "Art. I § 1"

    Returns:
        Normalized format: "Article I, Section 1" or None
    """
    # Handle "Article I, Section 1" format
    match = re.search(r'Article\s+([IVXLCDM]+),?\s+Section\s+(\d+)', section_str, re.IGNORECASE)
    if match:
        return f"Article {match.group(1).upper()}, Section {match.group(2)}"

    # Handle "Art. I § 1" format
    match = re.search(r'Art\.?\s*([IVXLCDM]+)\s*§\s*(\d+)', section_str, re.IGNORECASE)
    if match:
        return f"Article {match.group(1).upper()}, Section {match.group(2)}"

    # Handle "I.1" format
    match = re.match(r'^([IVXLCDM]+)\.(\d+)$', section_str.strip())
    if match:
        return f"Article {match.group(1).upper()}, Section {match.group(2)}"

    return None