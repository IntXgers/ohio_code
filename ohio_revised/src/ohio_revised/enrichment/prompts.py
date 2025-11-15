"""
Ohio Revised Code targeted extraction prompts for legal training data generation
Covers all 50+ titles of Ohio Revised Code
"""
import logging
from validate_output import validate_output

logger = logging.getLogger(__name__)


def prepare_semantic_context(doc):
    """Parse document structure for Ohio Revised Code"""
    header = doc.get('header', '')

    # Split at pipe to separate section number from title
    parts = header.split('|', 1)
    section_num = parts[0].replace('Section ', '').strip()
    title = parts[1].strip() if len(parts) > 1 else ''

    # Combine paragraphs (the actual statutory text)
    law_text = '\n'.join(doc.get('paragraphs', []))

    return {
        'section_num': section_num,
        'title': title,
        'law_text': law_text,
        'text_lower': law_text.lower()
    }


def generate_targeted_qa(doc, llm_generator, max_questions=15):
    """
    Generate targeted Q&A pairs for Ohio Revised Code training data

    Args:
        doc: Dictionary with 'header' and 'paragraphs' from JSONL
        llm_generator: Function that takes (prompt, max_tokens) and returns text
        max_questions: Maximum number of Q&A pairs to generate

    Returns:
        List of dictionaries with 'question', 'answer', 'type', 'section', 'title'
    """
    context = prepare_semantic_context(doc)
    qa_pairs = []
    asked_types = set()

    # Get available templates
    templates = LEGAL_QA_TEMPLATES.copy()

    # Add title-specific templates if applicable
    title = get_title_from_section(context['section_num'])
    if title and title in TITLE_SPECIFIC_TEMPLATES:
        templates.extend(TITLE_SPECIFIC_TEMPLATES[title])
        logger.debug(f"Added {title} specific templates")

    # Prioritize templates based on content relevance
    law_text_lower = context['text_lower']
    relevant_templates = []

    for template, q_type in templates:
        if q_type in asked_types:
            continue

        # Check if this question type is relevant to the content
        if should_ask_question(law_text_lower, q_type):
            # Calculate priority based on keyword matches
            priority = 2  # Default priority

            if q_type in QUESTION_APPLICABILITY:
                triggers = QUESTION_APPLICABILITY[q_type]
                matches = sum(1 for trigger in triggers if trigger in law_text_lower)
                if matches > 2:
                    priority = 0  # Highest priority - multiple keyword matches
                elif matches > 0:
                    priority = 1  # Medium priority - some keyword matches

            relevant_templates.append((priority, template, q_type))

    # Sort by priority (lower number = higher priority)
    relevant_templates.sort(key=lambda x: x[0])

    # Generate Q&A pairs up to max_questions
    for priority, question_template, q_type in relevant_templates:
        if len(qa_pairs) >= max_questions:
            break

        # Format the actual question
        question = question_template.format(section=context['section_num'])

        # Create the extraction prompt
        prompt = get_extraction_prompt(
            question,
            context['section_num'],
            context['title'],
            context['law_text']
        )

        try:
            # Generate response using the provided LLM function
            response = llm_generator(prompt, max_tokens=400)

            # Validate the response quality
            if response and len(response.strip()) > 20:
                # Import validation function from validate_output module
                from validate_output import validate_output

                if validate_output(response.strip(), q_type, context['law_text']):
                    qa_pairs.append({
                        'question': question,
                        'answer': response.strip(),
                        'type': q_type,
                        'section': context['section_num'],
                        'title': context['title']
                    })
                    asked_types.add(q_type)
                    logger.debug(f"Generated {q_type}: {question[:50]}...")
                else:
                    logger.debug(f"Validation failed for {q_type}")
            else:
                logger.debug(f"Response too short for {q_type}")

        except Exception as e:
            logger.error(f"Failed to generate {q_type}: {e}")
            continue

    logger.info(f"Generated {len(qa_pairs)} validated Q&A pairs for section {context['section_num']}")
    return qa_pairs


def should_ask_question(law_text_lower, question_type):
    """Determine if a question type applies to the law text"""
    if question_type not in QUESTION_APPLICABILITY:
        return True  # Ask generic questions

    triggers = QUESTION_APPLICABILITY[question_type]
    return any(trigger in law_text_lower for trigger in triggers)


def get_extraction_prompt(question_text, section_num, title, law_text):
    """Generate extraction prompt with proper context for Mistral"""
    # Use more text for better context
    text_to_use = law_text[:4000] if len(law_text) > 4000 else law_text

    # Format for Mistral model
    prompt = f"""Extract information from the Ohio Revised Code.

Section {section_num}: {title}

Statutory Text:
{text_to_use}

Question: {question_text}

Instructions: Provide only factual information directly stated in the text. If the information is not present, respond "Not specified in this section."

Answer:"""

    return prompt


# Question applicability triggers based on full Ohio Revised Code structure
QUESTION_APPLICABILITY = {
    # Criminal Law (Title 29)
    "criminal_elements": ["knowingly", "recklessly", "purposely", "negligently", "intent", "mens rea"],
    "criminal_penalties": ["misdemeanor", "felony", "degree", "imprisonment", "jail", "prison"],
    "criminal_procedures": ["arrest", "warrant", "indictment", "plea", "trial", "sentencing"],

    # Civil Law & Procedures (Title 23)
    "civil_procedures": ["complaint", "answer", "discovery", "motion", "judgment", "service"],
    "statutes_limitations": ["limitation", "within", "years from", "barred", "commence"],
    "damages": ["compensatory", "punitive", "treble", "actual damages", "consequential"],

    # Property Law (Title 53)
    "property_rights": ["deed", "title", "easement", "covenant", "lien", "mortgage"],
    "property_transfers": ["convey", "transfer", "grant", "devise", "inherit"],

    # Commercial Law (Title 13)
    "commercial_transactions": ["sale", "merchant", "goods", "warranty", "delivery", "payment"],
    "secured_transactions": ["security interest", "collateral", "perfection", "priority"],

    # Corporate/Business (Title 17)
    "business_formation": ["articles", "incorporation", "LLC", "partnership", "bylaws"],
    "corporate_governance": ["directors", "shareholders", "quorum", "proxy", "merger"],

    # Tax Law (Title 57)
    "tax_obligations": ["taxable", "rate", "assessment", "exemption", "deduction"],
    "tax_procedures": ["return", "audit", "appeal", "refund", "collection"],

    # Family Law (Title 31)
    "marriage_divorce": ["marriage", "divorce", "dissolution", "custody", "support"],
    "child_welfare": ["abuse", "neglect", "dependency", "adoption", "guardian"],

    # Labor & Employment (Title 41)
    "employment_rights": ["wages", "hours", "overtime", "discrimination", "termination"],
    "workers_comp": ["injury", "occupational", "benefits", "disability", "compensation"],

    # Environmental (Title 37)
    "environmental_standards": ["emission", "discharge", "permit", "pollution", "contamination"],
    "environmental_penalties": ["violation", "cease", "remediation", "cleanup"],

    # Healthcare (Title 37)
    "medical_licensing": ["physician", "nurse", "license", "practice", "board"],
    "patient_rights": ["consent", "confidentiality", "HIPAA", "treatment", "refuse"],

    # Insurance (Title 39)
    "insurance_requirements": ["policy", "coverage", "premium", "deductible", "claim"],
    "insurance_regulations": ["underwriting", "cancellation", "renewal", "disclosure"],

    # Banking & Finance (Title 11)
    "banking_operations": ["deposit", "loan", "interest", "mortgage", "foreclosure"],
    "financial_regulations": ["fiduciary", "trust", "securities", "investment"],

    # Education (Title 33)
    "school_governance": ["board", "superintendent", "district", "levy", "curriculum"],
    "student_rights": ["attendance", "discipline", "special education", "transportation"],

    # Elections (Title 35)
    "election_procedures": ["ballot", "candidate", "petition", "primary", "recount"],
    "campaign_finance": ["contribution", "expenditure", "disclosure", "PAC"],

    # Public Safety (Title 45)
    "law_enforcement": ["arrest", "search", "seizure", "miranda", "probable cause"],
    "emergency_services": ["EMS", "fire", "rescue", "dispatch", "response"],

    # Administrative Law (Title 1)
    "rulemaking": ["adopt", "promulgate", "rule", "regulation", "comment period"],
    "administrative_procedures": ["hearing", "adjudication", "order", "review", "appeal"],

    # Municipal Law (Title 7)
    "municipal_powers": ["ordinance", "charter", "home rule", "annexation", "zoning"],
    "municipal_services": ["utilities", "streets", "parks", "police", "fire"],

    # Agriculture (Title 9)
    "agricultural_regulations": ["livestock", "crops", "pesticide", "organic", "inspection"],

    # Professional Licensing (Title 47)
    "professional_requirements": ["license", "certification", "renewal", "continuing education"],
    "disciplinary_actions": ["suspension", "revocation", "censure", "probation"],

    # Public Records (Title 1)
    "records_access": ["public record", "disclosure", "exemption", "redaction", "retention"],

    # Utilities (Title 49)
    "utility_regulation": ["rates", "service", "PUCO", "tariff", "disconnect"],

    # Transportation (Title 45, 55)
    "traffic_violations": ["speed", "OVI", "reckless", "license", "suspension"],
    "vehicle_regulations": ["registration", "title", "inspection", "insurance"],

    # General procedural and administrative
    "notice_requirements": ["notice", "notify", "publication", "mail", "serve"],
    "filing_requirements": ["file", "submit", "record", "register", "application"],
    "hearing_procedures": ["hearing", "testimony", "evidence", "subpoena", "witness"],
    "appeal_procedures": ["appeal", "review", "contest", "challenge", "petition"],
    "time_limits": ["within", "days", "hours", "before", "after", "deadline"],
    "fees": ["fee", "cost", "charge", "payment", "assessment"],
    "penalties": ["penalty", "fine", "forfeiture", "violation", "sanction"],
    "enforcement": ["enforce", "compliance", "inspection", "audit", "investigation"],
}

# Comprehensive question templates covering all Ohio law areas
LEGAL_QA_TEMPLATES = [
    # Universal statutory requirements
    ("What actions are mandated by Section {section}?", "mandatory_actions"),
    ("What is prohibited under Section {section}?", "prohibitions"),
    ("Who must comply with Section {section}?", "covered_entities"),
    ("What are the penalties for violating Section {section}?", "penalties"),

    # Criminal law specific
    ("What are the elements of the offense in Section {section}?", "criminal_elements"),
    ("What degree of offense is specified in Section {section}?", "criminal_penalties"),
    ("What are the sentencing guidelines in Section {section}?", "criminal_penalties"),

    # Civil law specific
    ("What is the statute of limitations under Section {section}?", "statutes_limitations"),
    ("What damages are available under Section {section}?", "damages"),
    ("What procedures must be followed under Section {section}?", "civil_procedures"),

    # Business and commercial
    ("What formation requirements are in Section {section}?", "business_formation"),
    ("What disclosures are required by Section {section}?", "corporate_governance"),
    ("What warranties apply under Section {section}?", "commercial_transactions"),

    # Property and real estate
    ("What property rights are created by Section {section}?", "property_rights"),
    ("How is property transferred under Section {section}?", "property_transfers"),
    ("What recording requirements exist in Section {section}?", "property_transfers"),

    # Tax and revenue
    ("What is taxable under Section {section}?", "tax_obligations"),
    ("What are the tax rates in Section {section}?", "tax_obligations"),
    ("What exemptions apply under Section {section}?", "tax_obligations"),

    # Family law
    ("What factors are considered under Section {section}?", "marriage_divorce"),
    ("What is the standard applied in Section {section}?", "child_welfare"),
    ("How is support calculated under Section {section}?", "marriage_divorce"),

    # Employment and labor
    ("What employee rights exist under Section {section}?", "employment_rights"),
    ("What employer obligations are in Section {section}?", "employment_rights"),
    ("What benefits are provided under Section {section}?", "workers_comp"),

    # Environmental and health
    ("What standards are established by Section {section}?", "environmental_standards"),
    ("What permits are required under Section {section}?", "environmental_standards"),
    ("What reporting is required by Section {section}?", "environmental_standards"),

    # Professional and occupational
    ("What licensing requirements are in Section {section}?", "professional_requirements"),
    ("What grounds for discipline exist in Section {section}?", "disciplinary_actions"),
    ("What continuing education is required by Section {section}?", "professional_requirements"),

    # Government operations
    ("What notice must be provided under Section {section}?", "notice_requirements"),
    ("What records must be maintained under Section {section}?", "records_access"),
    ("What meetings are required by Section {section}?", "hearing_procedures"),

    # Administrative procedures
    ("What appeal rights exist under Section {section}?", "appeal_procedures"),
    ("What hearing procedures apply under Section {section}?", "hearing_procedures"),
    ("How are rules adopted under Section {section}?", "rulemaking"),

    # Elections and political
    ("What filing requirements exist in Section {section}?", "election_procedures"),
    ("What are the contribution limits in Section {section}?", "campaign_finance"),
    ("What disclosure is required by Section {section}?", "campaign_finance"),

    # Municipal and local
    ("What powers are granted by Section {section}?", "municipal_powers"),
    ("What procedures apply to ordinances under Section {section}?", "municipal_powers"),
    ("What services must be provided under Section {section}?", "municipal_services"),

    # Financial and banking
    ("What interest rates apply under Section {section}?", "banking_operations"),
    ("What disclosures are required by Section {section}?", "financial_regulations"),
    ("What fiduciary duties exist under Section {section}?", "financial_regulations"),

    # Insurance
    ("What coverage is required by Section {section}?", "insurance_requirements"),
    ("What are the claim procedures in Section {section}?", "insurance_requirements"),
    ("When can a policy be cancelled under Section {section}?", "insurance_regulations"),

    # Transportation and vehicles
    ("What are the penalties in Section {section}?", "traffic_violations"),
    ("What are the requirements for Section {section}?", "vehicle_regulations"),
    ("When is a license suspended under Section {section}?", "traffic_violations"),

    # Public utilities
    ("How are rates determined under Section {section}?", "utility_regulation"),
    ("What service standards apply in Section {section}?", "utility_regulation"),
    ("When can service be disconnected under Section {section}?", "utility_regulation"),

    # Cross-cutting legal concepts
    ("What definitions apply in Section {section}?", "definitions"),
    ("What exceptions exist to Section {section}?", "exemptions"),
    ("What other sections does Section {section} reference?", "cross_references"),
    ("What effective date applies to Section {section}?", "effective_dates"),
    ("What presumptions are created by Section {section}?", "presumptions"),
    ("What is the legislative intent of Section {section}?", "legislative_intent"),
    ("What conditions precedent exist in Section {section}?", "conditions"),
    ("What standards of proof apply under Section {section}?", "standards_proof"),
    ("What jurisdiction is specified in Section {section}?", "jurisdiction"),
    ("What venue requirements exist in Section {section}?", "venue"),
]

# Title-specific specialized templates
TITLE_SPECIFIC_TEMPLATES = {
    "Title 29": [  # Criminal Code
        ("What is the mens rea requirement in Section {section}?", "criminal_elements"),
        ("Are there affirmative defenses in Section {section}?", "criminal_elements"),
        ("What are the aggravating factors in Section {section}?", "criminal_penalties"),
        ("What are the mitigating factors in Section {section}?", "criminal_penalties"),
    ],
    "Title 31": [  # Domestic Relations
        ("What is the best interest standard in Section {section}?", "child_welfare"),
        ("How is marital property divided under Section {section}?", "marriage_divorce"),
        ("What are the grounds specified in Section {section}?", "marriage_divorce"),
    ],
    "Title 39": [  # Insurance
        ("What are the minimum coverage requirements in Section {section}?", "insurance_requirements"),
        ("What constitutes bad faith under Section {section}?", "insurance_regulations"),
        ("What are the underwriting restrictions in Section {section}?", "insurance_regulations"),
    ],
    "Title 41": [  # Labor
        ("What constitutes a violation under Section {section}?", "employment_rights"),
        ("What are the posting requirements in Section {section}?", "employment_rights"),
        ("How are benefits calculated under Section {section}?", "workers_comp"),
    ],
    "Title 47": [  # Occupations and Professions
        ("What are the examination requirements in Section {section}?", "professional_requirements"),
        ("What constitutes unprofessional conduct in Section {section}?", "disciplinary_actions"),
        ("What are the renewal requirements in Section {section}?", "professional_requirements"),
    ],
    "Title 1": [  # General Provisions
        ("How are terms defined in Section {section}?", "definitions"),
        ("What is the scope of application in Section {section}?", "scope"),
        ("What conflicts of law rules apply in Section {section}?", "conflicts"),
    ],
    "Title 23": [  # Courts - Civil Procedures
        ("What is the standard of review in Section {section}?", "standards_review"),
        ("What discovery is permitted under Section {section}?", "civil_procedures"),
        ("What are the pleading requirements in Section {section}?", "civil_procedures"),
    ],
}


def get_title_from_section(section_num):
    """Map section numbers to Ohio Revised Code titles"""
    try:
        # Extract the first two digits
        first_two = int(section_num.split('.')[0][:2])

        # Ohio Revised Code Title mapping (simplified - expand as needed)
        if first_two <= 1:
            return "Title 1"  # General Provisions
        elif first_two <= 3:
            return "Title 3"  # Counties
        elif first_two <= 5:
            return "Title 5"  # Townships
        elif first_two <= 7:
            return "Title 7"  # Municipal Corporations
        elif first_two <= 9:
            return "Title 9"  # Agriculture
        elif first_two <= 11:
            return "Title 11"  # Financial Institutions
        elif first_two <= 13:
            return "Title 13"  # Commercial Transactions
        elif first_two <= 15:
            return "Title 15"  # Conservation
        elif first_two <= 17:
            return "Title 17"  # Corporations
        elif first_two <= 19:
            return "Title 19"  # Courts - County
        elif first_two <= 21:
            return "Title 21"  # Courts - Probate
        elif first_two <= 23:
            return "Title 23"  # Courts - Civil Procedures
        elif first_two <= 25:
            return "Title 25"  # Courts - Criminal Procedures
        elif first_two <= 27:
            return "Title 27"  # Courts - General
        elif first_two == 29:
            return "Title 29"  # Criminal Code
        elif first_two == 31:
            return "Title 31"  # Domestic Relations
        elif first_two == 33:
            return "Title 33"  # Education
        elif first_two == 35:
            return "Title 35"  # Elections
        elif first_two == 37:
            return "Title 37"  # Health-Safety-Morals
        elif first_two == 39:
            return "Title 39"  # Insurance
        elif first_two == 41:
            return "Title 41"  # Labor and Industry
        elif first_two == 43:
            return "Title 43"  # Liquor
        elif first_two == 45:
            return "Title 45"  # Motor Vehicles
        elif first_two == 47:
            return "Title 47"  # Occupations-Professions
        elif first_two == 49:
            return "Title 49"  # Public Utilities
        elif first_two == 51:
            return "Title 51"  # Public Welfare
        elif first_two == 53:
            return "Title 53"  # Real Property
        elif first_two == 55:
            return "Title 55"  # Roads-Highways
        elif first_two == 57:
            return "Title 57"  # Taxation
        elif first_two == 59:
            return "Title 59"  # Veterans
    except Exception as Value_Error:
      logging.error(f"Error occurred: {Value_Error}")

    return None


def generate_targeted_qa(doc, llm_generator, max_questions=15):
    """Generate Q&A pairs covering full scope of Ohio law"""
    context = prepare_semantic_context(doc)
    qa_pairs = []
    asked_types = set()

    # Start with universal templates
    templates = LEGAL_QA_TEMPLATES.copy()

    # Add title-specific templates if applicable
    title = get_title_from_section(context['section_num'])
    if title and title in TITLE_SPECIFIC_TEMPLATES:
        templates.extend(TITLE_SPECIFIC_TEMPLATES[title])

    # Prioritize templates based on content relevance
    law_text_lower = context['text_lower']
    relevant_templates = []

    for template, q_type in templates:
        if q_type in asked_types:
            continue

        # Check if this question type is relevant to the content
        if should_ask_question(law_text_lower, q_type):
            # Prioritize questions with keyword matches
            priority = 2  # Default priority

            if q_type in QUESTION_APPLICABILITY:
                triggers = QUESTION_APPLICABILITY[q_type]
                matches = sum(1 for trigger in triggers if trigger in law_text_lower)
                if matches > 2:
                    priority = 0  # Highest priority
                elif matches > 0:
                    priority = 1  # Medium priority

            relevant_templates.append((priority, template, q_type))

    # Sort by priority
    relevant_templates.sort(key=lambda x: x[0])

    # Generate Q&A pairs
    for _, question_template, q_type in relevant_templates:
        if len(qa_pairs) >= max_questions:
            break

        # Format the actual question
        question = question_template.format(section=context['section_num'])

        # Create the prompt
        prompt = get_extraction_prompt(
            question,
            context['section_num'],
            context['title'],
            context['law_text']
        )

        # Generate response
        response = llm_generator(prompt, max_tokens=400)

        # Validate response
        if response and len(response.strip()) > 20:

            if validate_output(response, q_type, context['law_text']):
                qa_pairs.append({
                    'question': question,
                    'answer': response.strip(),
                    'type': q_type,
                    'section': context['section_num'],
                    'title': context['title']
                })
                asked_types.add(q_type)
                logger.info(f"Generated {q_type}: {question[:50]}...")
            else:
                logger.debug(f"Validation failed for {q_type}")

    return qa_pairs