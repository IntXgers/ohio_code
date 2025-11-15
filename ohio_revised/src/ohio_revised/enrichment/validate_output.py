import re



def validate_output(response: str, q_type: str, source_text: str) -> bool:
    """
    Validate extraction quality for legal training data.

    Args:
        response: The LLM's response to validate
        q_type: The question type (e.g., 'mandatory_actions', 'deadlines')
        source_text: The original law text to check against

    Returns:
        bool: True if response passes validation, False otherwise
    """
    # Basic checks
    if not response or len(response.strip()) < 20:
        return False

    response_lower = response.lower().strip()
    source_lower = source_text.lower()

    # Reject non-answers and evasive responses
    non_answers = [
        "not specified", "no information", "does not mention",
        "not found", "unclear", "n/a", "none", "not applicable",
        "cannot determine", "no such", "does not contain",
        "not present", "not provided", "not stated", "not included"
    ]
    if any(phrase in response_lower for phrase in non_answers):
        return False

    # Reject interpretation/speculation/analysis language
    speculation = [
        "appears to", "seems to", "likely", "probably",
        "suggests", "implies", "might", "could be", "possibly",
        "may be", "presumably", "apparently", "arguably",
        "it looks like", "this indicates", "one could interpret"
    ]
    if any(phrase in response_lower for phrase in speculation):
        return False

    # Reject meta-commentary about the task
    meta_commentary = [
        "the text says", "according to", "the section states",
        "the law provides", "the statute mentions", "it is written"
    ]
    if sum(1 for phrase in meta_commentary if phrase in response_lower) > 2:
        return False  # Too much meta-language instead of direct extraction

    # Type-specific content requirements
    type_requirements = {
        "mandatory_actions": ["shall", "must", "required", "obligated", "duty"],
        "prohibitions": ["shall not", "prohibited", "may not", "unlawful", "forbidden"],
        "shall_requirements": ["shall"],  # Must contain "shall" specifically
        "criminal_penalties": ["misdemeanor", "felony", "degree", "imprisonment", "jail"],
        "civil_penalties": ["fine", "penalty", "forfeiture", "dollar", "$", "violation"],
        "deadlines": ["day", "hour", "month", "year", "within", "before", "after", "prior"],
        "timeframes": ["within", "not later than", "no more than", "at least"],
        "notice_periods": ["notice", "days", "advance", "prior", "before"],
        "fines": ["$", "dollar", "fine", "penalty", "thousand", "hundred"],
        "authorities": ["board", "commission", "director", "department", "officer", "agency"],
        "court_jurisdiction": ["court", "jurisdiction", "venue", "district", "county"],
        "definitions": ["means", "includes", "defined", "refers to", "term"],
        "exemptions": ["except", "exemption", "does not apply", "excluding", "unless"],
        "procedures": ["shall", "must", "submit", "file", "provide", "follow"],
        "appeals": ["appeal", "review", "hearing", "contest", "challenge"],
        "documentation": ["document", "record", "form", "report", "certificate", "maintain"],
        "approval_requirements": ["approval", "consent", "vote", "majority", "quorum"],
        "financial_thresholds": ["$", "dollar", "amount", "exceeds", "less than", "more than"],
        "fees": ["fee", "cost", "charge", "payment", "assessment"],
        "rights": ["right", "entitled", "may", "privilege", "authority"],
        "remedies": ["remedy", "relief", "damages", "injunction", "action"],
        "cross_references": ["section", "chapter", "division", "subsection", "paragraph"],
        "numerical_extraction": [r"\d+", "$", "%", "percent"],  # regex pattern
        "if_then_conditions": ["if", "when", "unless", "provided that", "in the event"],
        "compliance_checklist": ["must", "shall", "required", "submit", "file", "maintain"],
        "entity_roles": ["shall", "may", "authorized", "responsible", "duties"],
        "positions": ["elect", "appoint", "officer", "member", "chair", "director"],
        "venue_requirements": ["county", "court", "district", "jurisdiction", "venue"]
    }

    # Check for required content based on question type
    if q_type in type_requirements:
        requirements = type_requirements[q_type]
        has_required_content = False

        for req in requirements:
            # Check if requirement is a regex pattern
            if req.startswith(r"\d") or req.startswith(r"\w") or req.startswith(r"\s"):
                if re.search(req, response_lower):
                    has_required_content = True
                    break
            else:
                if req in response_lower:
                    has_required_content = True
                    break

        if not has_required_content:
            return False

    # Verify response content comes from source (anti-hallucination check)
    # Remove common words for more meaningful comparison
    common_words = {
        "the", "and", "for", "are", "but", "not", "you", "all", "with",
        "from", "this", "that", "have", "has", "will", "can", "may", "shall",
        "must", "such", "any", "each", "both", "other", "same", "been"
    }

    # Extract meaningful words (4+ characters, not common)
    response_words = {
        word.lower().strip('.,;:()[]{}"\'-')
        for word in response.split()
        if len(word) > 3 and word.lower() not in common_words
    }

    source_words = {
        word.lower().strip('.,;:()[]{}"\'-')
        for word in source_text.split()
        if len(word) > 3 and word.lower() not in common_words
    }

    # Calculate overlap of meaningful words
    if response_words:
        overlap_ratio = len(response_words & source_words) / len(response_words)
        if overlap_ratio < 0.35:  # At least 35% overlap required
            return False

    # Check for hallucinated section references
    section_pattern = r'(?:section|§)\s*(\d+(?:\.\d+)*)'
    referenced_sections = re.findall(section_pattern, response_lower)

    for ref in referenced_sections:
        # Check if the referenced section appears in the source
        ref_normalized = ref.replace('.', '')
        source_normalized = source_lower.replace('.', '')
        if ref_normalized not in source_normalized:
            return False  # Hallucinated section reference

    # Minimum length requirements by type
    min_lengths = {
        "compliance_checklist": 100,
        "entity_roles": 50,
        "if_then_conditions": 50,
        "procedures": 50,
        "shall_requirements": 40,
        "mandatory_actions": 40
    }

    if q_type in min_lengths and len(response) < min_lengths[q_type]:
        return False

    # Check for list formatting in checklist/enumeration types
    list_types = ["compliance_checklist", "entity_roles", "shall_requirements"]
    if q_type in list_types:
        # Should have some structure (bullets, numbers, or line breaks)
        list_indicators = ['\n', '•', '-', '1.', '2.', '(a)', '(1)', '(i)']
        if not any(indicator in response for indicator in list_indicators):
            # If no list formatting, should at least have semicolons or "and"
            if ';' not in response and response.count(' and ') < 2:
                return False

    # Final quality check - response should be substantive
    if len(response.split()) < 5:  # Too short to be useful
        return False

    return True