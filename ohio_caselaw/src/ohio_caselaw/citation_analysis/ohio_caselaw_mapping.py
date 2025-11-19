#!/usr/bin/env python3
"""
Ohio Case Law Court Hierarchy Mapping
Provides classification, precedent authority, and relationship mapping for Ohio courts
"""
from typing import Dict, List, Optional, Tuple
import re


class OhioCaseLawMapper:
    """
    Maps Ohio court cases to hierarchical structure with precedent authority

    Court Hierarchy (top to bottom):
    1. Supreme Court of Ohio
    2. Courts of Appeals (12 districts)
    3. Court of Claims
    4. Common Pleas Courts (88 counties)
    5. Probate Courts
    6. Juvenile Courts
    7. Municipal Courts
    8. County Courts
    9. Mayor's Courts (limited jurisdiction)

    Historical courts:
    - Circuit Courts (abolished 1912)
    - Superior Courts (abolished 1913)
    """

    # Court level hierarchy (higher number = higher authority)
    COURT_LEVELS = {
        'supreme': 100,
        'appeals': 80,
        'claims': 70,
        'common-pleas': 60,
        'probate': 50,
        'juvenile': 50,
        'municipal': 40,
        'county': 30,
        'mayor': 20,
        'circuit': 75,  # Historical
        'superior': 65,  # Historical
        'federal-supreme': 110,  # US Supreme Court
        'federal-circuit': 90,  # Federal Circuit Courts
        'federal-district': 70,  # Federal District Courts
    }

    # Appellate district to county mapping
    APPELLATE_DISTRICTS = {
        '01': ['Butler', 'Clermont', 'Hamilton', 'Warren'],
        '02': ['Champaign', 'Clark', 'Darke', 'Greene', 'Miami', 'Montgomery', 'Preble'],
        '03': ['Allen', 'Auglaize', 'Crawford', 'Defiance', 'Hancock', 'Hardin', 'Henry',
               'Logan', 'Marion', 'Mercer', 'Paulding', 'Putnam', 'Shelby', 'Union',
               'Van Wert', 'Williams', 'Wyandot'],
        '04': ['Adams', 'Athens', 'Gallia', 'Highland', 'Hocking', 'Jackson', 'Lawrence',
               'Meigs', 'Pickaway', 'Pike', 'Ross', 'Scioto', 'Vinton', 'Washington'],
        '05': ['Delaware', 'Fairfield', 'Franklin', 'Knox', 'Licking', 'Madison',
               'Morrow', 'Perry', 'Richland', 'Union'],
        '06': ['Erie', 'Fulton', 'Huron', 'Lucas', 'Ottawa', 'Sandusky', 'Williams', 'Wood'],
        '07': ['Belmont', 'Carroll', 'Columbiana', 'Harrison', 'Jefferson', 'Mahoning',
               'Monroe', 'Noble'],
        '08': ['Cuyahoga'],
        '09': ['Lorain', 'Medina', 'Summit', 'Wayne'],
        '10': ['Franklin'],
        '11': ['Ashtabula', 'Geauga', 'Lake', 'Portage', 'Trumbull'],
        '12': ['Brown', 'Butler', 'Clermont', 'Clinton', 'Fayette', 'Madison', 'Preble', 'Warren'],
    }

    def __init__(self):
        """Initialize the mapper with reverse county-to-district lookup"""
        self.county_to_district = {}
        for district, counties in self.APPELLATE_DISTRICTS.items():
            for county in counties:
                self.county_to_district[county.lower()] = district

    def get_court_level(self, court_name: str) -> Tuple[str, int]:
        """
        Determine court level and precedent authority

        Args:
            court_name: Full court name from case data

        Returns:
            Tuple of (court_type, authority_level)
        """
        court_lower = court_name.lower()

        # Supreme Court
        if 'supreme court of ohio' in court_lower:
            return ('supreme', self.COURT_LEVELS['supreme'])

        # Federal courts
        if 'supreme court' in court_lower and 'united states' in court_lower:
            return ('federal-supreme', self.COURT_LEVELS['federal-supreme'])
        if 'sixth circuit' in court_lower or 'court of appeals for the sixth circuit' in court_lower:
            return ('federal-circuit', self.COURT_LEVELS['federal-circuit'])
        if 'district' in court_lower and ('northern' in court_lower or 'southern' in court_lower):
            return ('federal-district', self.COURT_LEVELS['federal-district'])

        # Appeals courts
        if 'court of appeals' in court_lower and 'ohio' in court_lower:
            return ('appeals', self.COURT_LEVELS['appeals'])

        # Court of Claims
        if 'court of claims' in court_lower:
            return ('claims', self.COURT_LEVELS['claims'])

        # Historical courts
        if 'circuit court' in court_lower or ('circuit' in court_name and 'Court' in court_name):
            return ('circuit', self.COURT_LEVELS['circuit'])
        if 'superior court' in court_lower:
            return ('superior', self.COURT_LEVELS['superior'])

        # County courts - Common Pleas
        if 'common pleas' in court_lower or 'court of common pleas' in court_lower:
            return ('common-pleas', self.COURT_LEVELS['common-pleas'])

        # Probate
        if 'probate' in court_lower:
            return ('probate', self.COURT_LEVELS['probate'])

        # Juvenile
        if 'juvenile' in court_lower:
            return ('juvenile', self.COURT_LEVELS['juvenile'])

        # Municipal
        if 'municipal court' in court_lower or 'police court' in court_lower:
            return ('municipal', self.COURT_LEVELS['municipal'])

        # County court
        if 'county court' in court_lower:
            return ('county', self.COURT_LEVELS['county'])

        # Mayor's court
        if 'mayor' in court_lower:
            return ('mayor', self.COURT_LEVELS['mayor'])

        # Default to unknown
        return ('unknown', 0)

    def get_appellate_district(self, court_name: str) -> Optional[str]:
        """
        Extract appellate district number from court name

        Args:
            court_name: Full court name

        Returns:
            District number (01-12) or None
        """
        court_lower = court_name.lower()

        # Direct match in court name
        district_match = re.search(
            r'(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth)',
            court_lower
        )

        if district_match:
            district_map = {
                'first': '01', 'second': '02', 'third': '03', 'fourth': '04',
                'fifth': '05', 'sixth': '06', 'seventh': '07', 'eighth': '08',
                'ninth': '09', 'tenth': '10', 'eleventh': '11', 'twelfth': '12'
            }
            return district_map[district_match.group(1)]

        # Try to extract from county name
        county = self._extract_county(court_name)
        if county:
            return self.county_to_district.get(county.lower())

        return None

    def _extract_county(self, court_name: str) -> Optional[str]:
        """
        Extract county name from court name

        Args:
            court_name: Full court name

        Returns:
            County name or None
        """
        # Remove common court suffixes
        county = court_name.lower()
        county = re.sub(r'\s*(county|circuit|court|common|pleas|probate|juvenile|municipal).*$', '', county)
        county = county.strip().title()

        # Check if it's in our county list
        for district, counties in self.APPELLATE_DISTRICTS.items():
            if county in counties:
                return county

        return None

    def get_precedent_authority(self, court_name: str, cited_court_name: str) -> str:
        """
        Determine precedent relationship between two courts

        Args:
            court_name: The citing court
            cited_court_name: The cited court

        Returns:
            Relationship type: 'binding', 'persuasive', 'horizontal', 'lower'
        """
        court_type, court_level = self.get_court_level(court_name)
        cited_type, cited_level = self.get_court_level(cited_court_name)

        # Binding precedent (higher court)
        if cited_level > court_level:
            # Ohio Supreme Court is binding on all Ohio courts
            if cited_type == 'supreme' and court_type != 'federal-supreme':
                return 'binding'
            # Federal Supreme Court binding on all courts
            if cited_type == 'federal-supreme':
                return 'binding'
            # Federal Circuit binding on federal district courts
            if cited_type == 'federal-circuit' and court_type == 'federal-district':
                return 'binding'
            # Appeals court binding on lower courts in same district
            if cited_type == 'appeals' and court_level < self.COURT_LEVELS['appeals']:
                # Check if same district
                citing_district = self.get_appellate_district(court_name)
                cited_district = self.get_appellate_district(cited_court_name)
                if citing_district and cited_district and citing_district == cited_district:
                    return 'binding'
                return 'persuasive'

        # Same level (horizontal precedent)
        elif cited_level == court_level:
            # Same district appeals courts
            if court_type == 'appeals' and cited_type == 'appeals':
                citing_district = self.get_appellate_district(court_name)
                cited_district = self.get_appellate_district(cited_court_name)
                if citing_district and cited_district and citing_district == cited_district:
                    return 'horizontal'
            return 'persuasive'

        # Lower court (not binding)
        else:
            return 'lower'

    def get_case_metadata(self, case_data: Dict) -> Dict:
        """
        Extract comprehensive metadata for a case

        Args:
            case_data: Full case JSON data

        Returns:
            Dictionary with court classification and authority metadata
        """
        court = case_data.get('court', {})
        court_name = court.get('name', 'Unknown')

        court_type, authority_level = self.get_court_level(court_name)
        appellate_district = self.get_appellate_district(court_name)
        county = self._extract_county(court_name)

        metadata = {
            'court_name': court_name,
            'court_type': court_type,
            'authority_level': authority_level,
            'appellate_district': appellate_district,
            'county': county,
            'is_supreme_court': court_type == 'supreme',
            'is_appellate': court_type in ['supreme', 'appeals', 'federal-circuit', 'federal-supreme'],
            'is_federal': court_type.startswith('federal-'),
            'is_historical': court_type in ['circuit', 'superior'],
        }

        # Add citation count
        cites_to = case_data.get('cites_to', [])
        metadata['outgoing_citations'] = len(cites_to)

        # Extract decision year
        decision_date = case_data.get('decision_date', '')
        if decision_date:
            metadata['decision_year'] = decision_date[:4]

        return metadata

    def classify_case_type(self, case_data: Dict) -> List[str]:
        """
        Classify case by subject matter based on case name and court

        Args:
            case_data: Full case JSON data

        Returns:
            List of subject classifications
        """
        case_name = case_data.get('name', '').lower()
        casebody = case_data.get('casebody', {})
        opinions = casebody.get('data', {}).get('opinions', [])

        # Combine all opinion text
        opinion_text = ' '.join([
            opinion.get('text', '')[:1000]  # First 1000 chars per opinion
            for opinion in opinions
        ]).lower()

        classifications = []

        # Subject matter patterns
        patterns = {
            'criminal': [r'\bstate\s+v\.', r'\bcriminal\b', r'\bconviction\b', r'\bsentenc(e|ing)\b'],
            'civil': [r'\bcontract\b', r'\btort\b', r'\bnegligence\b', r'\bdamages\b'],
            'family': [r'\bdivorce\b', r'\bcustody\b', r'\bchild support\b', r'\badoption\b'],
            'probate': [r'\bestate\b', r'\bwill\b', r'\btrust\b', r'\bguardianship\b'],
            'corporate': [r'\bcorporation\b', r'\bshareholder\b', r'\bllc\b', r'\bpartnership\b'],
            'tax': [r'\btax\b', r'\brevenue\b', r'\bassess(ment|or)\b'],
            'employment': [r'\bemployment\b', r'\bworker\b', r'\blabor\b', r'\bwage\b'],
            'property': [r'\breal estate\b', r'\bforeclosure\b', r'\beasement\b', r'\bzoning\b'],
            'constitutional': [r'\bconstitution(al)?\b', r'\bamendment\b', r'\brights?\b'],
            'administrative': [r'\bagency\b', r'\bregulation\b', r'\badministrative\b'],
        }

        for category, pattern_list in patterns.items():
            for pattern in pattern_list:
                if re.search(pattern, case_name) or re.search(pattern, opinion_text):
                    classifications.append(category)
                    break

        return classifications if classifications else ['general']


def get_mapper() -> OhioCaseLawMapper:
    """Get singleton instance of the case law mapper"""
    return OhioCaseLawMapper()