"""
Questions specific to Title 1 - State Government
Covers legislative procedures, state agencies, administrative law, and government operations
"""

def get_title_01_questions(section_num):
    """Questions specific to Title 1 - State Government of Ohio Revised Code"""
    return [
        # Universal government/administrative questions that work across all Title 1 chapters
        ("What governmental procedure is established by Section {section}?", "government_procedure"),
        ("What authority is granted or limited by Section {section}?", "government_authority"),
        ("What duties or responsibilities are assigned by Section {section}?", "official_duties"),
        ("What qualifications or requirements are specified in Section {section}?", "qualifications"),
        ("What deadlines or time limits are established by Section {section}?", "time_limits"),
        ("What documentation or records are required under Section {section}?", "documentation_requirements"),
        ("What penalties or enforcement provisions exist in Section {section}?", "penalties"),
        ("What fees, salaries, or financial provisions are specified in Section {section}?", "financial_provisions"),
        ("What approval or consent requirements exist under Section {section}?", "approval_requirements"),
        ("What notice or publication requirements are mandated by Section {section}?", "notice_requirements")
    ]