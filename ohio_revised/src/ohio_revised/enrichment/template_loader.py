"""
Template loader system for all 33 Ohio Revised Code titles
Dynamically imports the appropriate template file based on section number
"""

import logging
from ohio_revised_mapping import get_title_from_section

logger = logging.getLogger(__name__)


def get_questions_for_section(section_num):
    """
    Load appropriate question templates based on section number

    Args:
        section_num: Section number like "101.11" or "3503.19"

    Returns:
        List of tuples: [(question_template, question_type), ...]
    """
    title = get_title_from_section(section_num)

    if not title or title.startswith("Unknown Title"):
        logger.warning(f"No title mapping found for section {section_num}")
        return []

    try:
        # Dynamic imports for all 33 titles
        if "Title 1" in title:
            from title_01_templates import get_title_01_questions
            return get_title_01_questions(section_num)

        elif "Title 3" in title:
            from title_03_templates import get_title_03_questions
            return get_title_03_questions(section_num)

        elif "Title 5" in title:
            from title_05_templates import get_title_05_questions
            return get_title_05_questions(section_num)

        elif "Title 7" in title:
            from title_07_templates import get_title_07_questions
            return get_title_07_questions(section_num)

        elif "Title 9" in title:
            from title_09_templates import get_title_09_questions
            return get_title_09_questions(section_num)

        elif "Title 11" in title:
            from title_11_templates import get_title_11_questions
            return get_title_11_questions(section_num)

        elif "Title 13" in title:
            from title_13_templates import get_title_13_questions
            return get_title_13_questions(section_num)

        elif "Title 15" in title:
            from title_15_templates import get_title_15_questions
            return get_title_15_questions(section_num)

        elif "Title 17" in title:
            from title_17_templates import get_title_17_questions
            return get_title_17_questions(section_num)

        elif "Title 19" in title:
            from title_19_templates import get_title_19_questions
            return get_title_19_questions(section_num)

        elif "Title 21" in title:
            from title_21_templates import get_title_21_questions
            return get_title_21_questions(section_num)

        elif "Title 23" in title:
            from title_23_templates import get_title_23_questions
            return get_title_23_questions(section_num)

        elif "Title 25" in title:
            from title_25_templates import get_title_25_questions
            return get_title_25_questions(section_num)

        elif "Title 27" in title:
            from title_27_templates import get_title_27_questions
            return get_title_27_questions(section_num)

        elif "Title 29" in title:
            from title_29_templates import get_title_29_questions
            return get_title_29_questions(section_num)

        elif "Title 31" in title:
            from title_31_templates import get_title_31_questions
            return get_title_31_questions(section_num)

        elif "Title 33" in title:
            from title_33_templates import get_title_33_questions
            return get_title_33_questions(section_num)

        elif "Title 35" in title:
            from title_35_templates import get_title_35_questions
            return get_title_35_questions(section_num)

        elif "Title 37" in title:
            from title_37_templates import get_title_37_questions
            return get_title_37_questions(section_num)

        elif "Title 39" in title:
            from title_39_templates import get_title_39_questions
            return get_title_39_questions(section_num)

        elif "Title 41" in title:
            from title_41_templates import get_title_41_questions
            return get_title_41_questions(section_num)

        elif "Title 43" in title:
            from title_43_templates import get_title_43_questions
            return get_title_43_questions(section_num)

        elif "Title 45" in title:
            from title_45_templates import get_title_45_questions
            return get_title_45_questions(section_num)

        elif "Title 47" in title:
            from title_47_templates import get_title_47_questions
            return get_title_47_questions(section_num)

        elif "Title 49" in title:
            from title_49_templates import get_title_49_questions
            return get_title_49_questions(section_num)

        elif "Title 51" in title:
            from title_51_templates import get_title_51_questions
            return get_title_51_questions(section_num)

        elif "Title 53" in title:
            from title_53_templates import get_title_53_questions
            return get_title_53_questions(section_num)

        elif "Title 55" in title:
            from title_55_templates import get_title_55_questions
            return get_title_55_questions(section_num)

        elif "Title 57" in title:
            from title_57_templates import get_title_57_questions
            return get_title_57_questions(section_num)

        elif "Title 58" in title:
            from title_58_templates import get_title_58_questions
            return get_title_58_questions(section_num)

        elif "Title 59" in title:
            from title_59_templates import get_title_59_questions
            return get_title_59_questions(section_num)

        elif "Title 61" in title:
            from title_61_templates import get_title_61_questions
            return get_title_61_questions(section_num)

        elif "Title 63" in title:
            from title_63_templates import get_title_63_questions
            return get_title_63_questions(section_num)

        else:
            logger.warning(f"No template file implemented for {title}")
            return []

    except ImportError as e:
        logger.warning(f"Template file not found for {title}: {e}")
        return []
    except Exception as e:
        logger.error(f"Error loading template for {title}: {e}")
        return []


def get_fallback_questions(section_num):
    """
    Comprehensive universal questions that work for any Ohio statute
    Used when title-specific templates aren't available
    """
    return [
        # Core statutory elements (highest priority)
        ("What actions are mandated by Section {section}?", "mandatory_actions"),
        ("What is prohibited under Section {section}?", "prohibitions"),
        ("Who must comply with Section {section}?", "covered_entities"),
        ("What penalties apply under Section {section}?", "penalties"),

        # Common statutory features
        ("What exceptions exist to Section {section}?", "exemptions"),
        ("What definitions apply in Section {section}?", "definitions"),
        ("What procedures must be followed under Section {section}?", "procedures"),

        # Timing and deadlines (very common)
        ("What time limits are established in Section {section}?", "time_limits"),
        ("What deadlines exist under Section {section}?", "deadlines"),

        # Documentation and records
        ("What records must be maintained under Section {section}?", "record_keeping"),
        ("What documentation is required by Section {section}?", "documentation"),

        # Financial aspects
        ("What fees are specified in Section {section}?", "fees"),
        ("What costs apply under Section {section}?", "costs"),

        # Authority and jurisdiction
        ("What authority has jurisdiction under Section {section}?", "jurisdiction"),
        ("What approval requirements exist in Section {section}?", "approval_requirements"),

        # Notice and communication
        ("What notice requirements exist in Section {section}?", "notice_requirements"),

        # Cross-references and structure
        ("What other sections does Section {section} reference?", "cross_references"),
        ("What conditions must be met under Section {section}?", "conditions")
    ]


def get_questions_with_fallback(section_num):
    """
    Get title-specific questions, fall back to universal questions if needed
    """
    # Try title-specific templates first
    questions = get_questions_for_section(section_num)

    # If no title-specific templates available, use fallback
    if not questions:
        logger.info(f"Using fallback questions for section {section_num}")
        questions = get_fallback_questions(section_num)

    # Format questions with actual section number
    formatted_questions = []
    for template, q_type in questions:
        formatted_questions.append((template.format(section=section_num), q_type))

    return formatted_questions