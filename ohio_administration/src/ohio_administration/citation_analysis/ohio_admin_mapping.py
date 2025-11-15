"""
Ohio Administrative Code Chapter Mapping
Based on official structure from codes.ohio.gov
"""


def get_agency_from_rule(rule_num):
    """
    Map Ohio Administrative Code rule numbers to state agencies

    Args:
        rule_num: Rule number like "3701-17-01" or "011-1-01"

    Returns:
        String: Agency name or None if not found
    """
    try:
        if '-' in rule_num:
            chapter = int(rule_num.split('-')[0])
        else:
            chapter = int(rule_num)
    except (ValueError, IndexError):
        return None

    # Ohio Administrative Code chapter-to-agency mapping
    # Format: chapter_number -> (agency_name, agency_abbreviation)
    chapter_mapping = {
        # Legislative/Constitutional Offices
        range(1, 100): ("Legislative Service Commission", "LSC"),
        range(101, 200): ("Auditor of State", "AUD"),
        range(111, 120): ("Secretary of State", "SOS"),
        range(121, 130): ("Attorney General", "AGO"),
        range(131, 140): ("Treasurer of State", "TRE"),

        # Executive Agencies
        range(123, 130): ("Governor's Office", "GOV"),
        range(126, 135): ("Office of Budget and Management", "OBM"),

        # Health & Human Services
        range(3701, 3800): ("Department of Health", "ODH"),
        range(5101, 5200): ("Department of Job and Family Services", "ODJFS"),
        range(5122, 5160): ("Department of Mental Health and Addiction Services", "OhioMHAS"),
        range(5123, 5130): ("Department of Developmental Disabilities", "DODD"),
        range(5160, 5170): ("Department of Aging", "ODA"),
        range(4723, 4730): ("Board of Nursing", "OBN"),
        range(4731, 4740): ("State Medical Board", "SMBO"),
        range(4755, 4760): ("Board of Pharmacy", "BOPHAR"),

        # Education
        range(3301, 3400): ("Department of Education", "ODE"),
        range(3333, 3340): ("Chancellor of Higher Education", "ODHE"),
        range(3345, 3350): ("State Board of Career Colleges and Schools", "SBCCS"),

        # Business & Commerce
        range(1301, 1400): ("Department of Commerce", "COM"),
        range(1501, 1600): ("Division of Real Estate", "DRE"),
        range(1701, 1800): ("Division of Securities", "DOS"),
        range(4101, 4200): ("Department of Industrial Compliance", "DIC"),

        # Insurance
        range(3901, 4000): ("Department of Insurance", "ODI"),

        # Transportation
        range(4501, 4600): ("Department of Public Safety", "DPS"),
        range(5501, 5600): ("Department of Transportation", "ODOT"),

        # Natural Resources & Environment
        range(1501, 1600): ("Department of Natural Resources", "ODNR"),
        range(3745, 3750): ("Environmental Protection Agency", "OEPA"),
        range(901, 1000): ("Department of Agriculture", "ODA"),

        # Public Safety & Corrections
        range(5120, 5125): ("Department of Rehabilitation and Correction", "DRC"),
        range(109, 115): ("Public Defender Commission", "PDC"),
        range(5502, 5510): ("State Highway Patrol", "OSHP"),

        # Labor & Workers
        range(4121, 4130): ("Bureau of Workers' Compensation", "BWC"),
        range(4141, 4150): ("Department of Job and Family Services - Unemployment", "ODJFS-UC"),

        # Tax & Revenue
        range(5703, 5750): ("Department of Taxation", "TAX"),
        range(3769, 3775): ("State Racing Commission", "SRC"),
        range(3772, 3775): ("Ohio Lottery Commission", "OLC"),

        # Utilities & Public Service
        range(4901, 5000): ("Public Utilities Commission", "PUCO"),

        # Gaming & Liquor Control
        range(4301, 4400): ("Division of Liquor Control", "DLC"),
        range(3772, 3775): ("Casino Control Commission", "CCC"),
    }

    # Find matching range
    for chapter_range, (agency_name, agency_abbr) in chapter_mapping.items():
        if chapter in chapter_range:
            return f"{agency_name} ({agency_abbr})"

    # Default for unmapped chapters
    return "State Agency (Unknown)"


def extract_rule_number(text):
    """
    Extract Ohio Admin Code rule number from text

    Args:
        text: Text containing rule reference

    Returns:
        String: Rule number or None

    Examples:
        "O.A.C. 3701-17-01" -> "3701-17-01"
        "rule 3701-17-01" -> "3701-17-01"
        "Rule 011-1-01" -> "011-1-01"
    """
    import re

    # Ohio Admin Code patterns
    patterns = [
        r'(?:O\.A\.C\.|Ohio\s+Adm(?:\.|ministrative)\s*Code)\s+([\d-:]+)',
        r'[Rr]ule\s+([\d-:]+)',
        r'([\d]{3,4}-[\d]{1,2}-[\d]{1,2})',  # Direct format
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)

    return None


def get_rule_type(rule_num):
    """
    Determine type of administrative rule

    Args:
        rule_num: Rule number like "3701-17-01"

    Returns:
        String: Rule type category
    """
    try:
        if '-' in rule_num:
            chapter = int(rule_num.split('-')[0])
        else:
            return "General"
    except (ValueError, IndexError):
        return "General"

    # Categorize by function
    if 3700 <= chapter < 3800 or 4700 <= chapter < 4800:
        return "Healthcare Licensing"
    elif 5100 <= chapter < 5200:
        return "Social Services"
    elif 3300 <= chapter < 3400:
        return "Education"
    elif 3900 <= chapter < 4000:
        return "Insurance"
    elif 4500 <= chapter < 4600 or 5500 <= chapter < 5600:
        return "Transportation"
    elif 1500 <= chapter < 1600 or 3745 <= chapter < 3750:
        return "Environment"
    elif 5700 <= chapter < 5750:
        return "Taxation"
    elif 4900 <= chapter < 5000:
        return "Utilities"
    elif 5120 <= chapter < 5130:
        return "Corrections"
    elif 4100 <= chapter < 4200 or 4120 <= chapter < 4150:
        return "Labor & Employment"
    else:
        return "Regulatory"