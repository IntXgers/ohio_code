# AI-Assisted Legal Drafting & Strategy Features - Developer Documentation

**Date:** November 10, 2025  
**Author:** Development Team  
**Status:** Phase 1 Planning

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Feature Pages Specification](#feature-pages-specification)
4. [Data Models](#data-models)
5. [Temporal Workflows](#temporal-workflows)
6. [API Endpoints](#api-endpoints)
7. [Frontend Components](#frontend-components)
8. [Feedback System](#feedback-system)
9. [Implementation Priority](#implementation-priority)
10. [Technical Considerations](#technical-considerations)

---

## Overview

### Purpose
Extend Jurist beyond legal research into AI-assisted document drafting and case strategy analysis. These features leverage our local 70B model and complete Ohio legal datasets to help attorneys draft better arguments faster.

### Competitive Advantage
- **Westlaw/LexisNexis**: Provide cases, don't draft arguments
- **Jurist**: Provides cases AND drafts arguments with citations
- **Value Proposition**: "Spend less time researching, more time winning"

### Key Principles
1. **Structured + Unstructured Input**: Combine dropdowns/fields with text narratives
2. **Separate Pages**: Each feature gets dedicated page optimized for its workflow
3. **Same Infrastructure**: All features use existing vLLM + LMDB + Temporal
4. **Citation-Driven**: Every AI-generated claim includes Ohio case law citations
5. **Attorney Tool, Not Replacement**: Outputs are drafts requiring attorney review

---

## Architecture

### High-Level Flow

```
User → Frontend Page → BFF (8008) → Temporal Workflow → vLLM (8004) + LMDB → Response
```

### Service Layer

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                    │
│  /research | /drafting/* | /strategy/*                  │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────────────┐
│              BFF Service (Port 8008)                     │
│  - Route to appropriate workflow                         │
│  - Validate input                                        │
│  - Return workflow ID                                    │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────────────┐
│           Temporal Workflows (Worker)                    │
│  - DraftOpeningStatementWorkflow                         │
│  - DraftClosingArgumentWorkflow                          │
│  - DraftMotionWorkflow                                   │
│  - DefenseStrategyWorkflow                               │
│  - DiscoveryRequestWorkflow                              │
└──────────┬─────────────────────┬────────────────────────┘
           │                     │
           ↓                     ↓
┌──────────────────┐   ┌────────────────────┐
│  vLLM (8004)     │   │  LMDB Knowledge    │
│  70B Model       │   │  Ohio Legal Data   │
│  Inference       │   │  Case Search       │
└──────────────────┘   └────────────────────┘
```

### No AI Routing Needed
- User explicitly selects feature (clicks page/button)
- URL determines which endpoint to hit
- Endpoint explicitly calls specific workflow
- Simple, reliable, no Mistral parsing

---

## Feature Pages Specification

### 1. Opening Statement Builder

**Route:** `/drafting/opening-statement`

**Purpose:** Draft compelling opening statements with Ohio case law citations

**Input Fields:**

**Structured:**
- `case_type`: Dropdown ["Criminal", "Civil"]
- `case_number`: Text input (validated format)
- `charges`: Multi-select checkboxes (populated from Ohio statutes)
    - For criminal: ORC Title 29 offenses
    - For civil: Common claim types
- `defendant_name`: Text input
- `plaintiff_name`: Text input (civil only)
- `court`: Dropdown (Ohio courts)
- `judge_name`: Text input (optional)
- `trial_date`: Date picker (optional)

**Unstructured:**
- `facts_narrative`: Large textarea (500+ words)
    - Placeholder: "Describe the facts of the case. Include timeline, key events, relationships between parties, and context that matters..."
- `theory_of_case`: Textarea (200+ words)
    - Placeholder: "What's your theory of the case? What story are you telling the jury?"
- `key_evidence`: List of text items (add/remove)
    - Each item: description of evidence + relevance
- `key_witnesses`: List of text items (add/remove)
    - Each item: witness name + what they'll testify to
- `opposing_counsel_theory`: Textarea (optional)
    - Placeholder: "What do you expect the other side to argue?"

**Preferences (Structured):**
- `tone`: Radio buttons ["Aggressive", "Balanced", "Empathetic"]
- `length`: Radio buttons ["Concise (5-7 min)", "Standard (10-15 min)", "Detailed (20+ min)"]
- `jury_considerations`: Textarea (optional)
    - Placeholder: "Any specific jury demographics or considerations?"

**Output Format:**
```typescript
interface OpeningStatementDraft {
  introduction: string;
  facts_section: string;
  legal_framework: string;
  evidence_preview: string;
  conclusion: string;
  citations: Citation[];
  estimated_duration: string;
  created_at: datetime;
  workflow_id: string;
}
```

**UI Features:**
- Inline citation tooltips (hover → see case details)
- Edit mode (attorney can modify generated text)
- Export to DOCX
- Save to case file
- Regenerate with changes
- "Find more cases" button (returns to research with relevant query)

---

### 2. Closing Argument Builder

**Route:** `/drafting/closing-argument`

**Purpose:** Draft persuasive closing arguments that tie evidence to legal standards

**Input Fields:**

**Structured:**
- Same case metadata as opening statement
- `trial_length`: Dropdown ["1 day", "2-3 days", "1 week", "2+ weeks"]
- `verdict_type`: Radio ["Guilty/Not Guilty", "Liable/Not Liable", "Mixed Verdict"]

**Unstructured:**
- `key_testimony_summary`: Textarea
    - "Summarize the most important testimony from trial..."
- `evidence_presented`: List of text items
    - "What evidence was actually admitted? What did it show?"
- `credibility_arguments`: Textarea
    - "Which witnesses were credible? Which weren't? Why?"
- `legal_standard_met`: Textarea
    - "How do the facts meet (or fail to meet) the legal standard?"
- `jury_instructions_reference`: Textarea (optional)
    - "Any specific jury instructions you want to emphasize?"

**Preferences:**
- `tone`: Radio ["Aggressive", "Balanced", "Conciliatory"]
- `emphasis`: Checkboxes ["Facts", "Law", "Credibility", "Emotion"]

**Output Format:**
```typescript
interface ClosingArgumentDraft {
  opening_hook: string;
  evidence_review: string;
  legal_standard_application: string;
  credibility_assessment: string;
  burden_of_proof_argument: string;
  call_to_action: string;
  citations: Citation[];
  jury_instruction_references: string[];
  created_at: datetime;
  workflow_id: string;
}
```

---

### 3. Motion to Dismiss Drafter

**Route:** `/drafting/motion-dismiss`

**Purpose:** Draft motion to dismiss with Ohio procedural law citations

**Input Fields:**

**Structured:**
- `motion_type`: Dropdown
    - "Civil Rule 12(B)(6) - Failure to State a Claim"
    - "Civil Rule 12(B)(1) - Lack of Jurisdiction"
    - "Civil Rule 12(B)(2) - Improper Venue"
    - "Criminal Rule 29 - Insufficient Evidence"
- `case_type`: ["Criminal", "Civil"]
- `case_number`: Text
- `court`: Dropdown (Ohio courts)
- `case_stage`: Dropdown ["Pre-answer", "After Discovery", "During Trial", "Post-trial"]

**Unstructured:**
- `factual_background`: Textarea
    - "Provide the procedural and factual background..."
- `grounds_for_dismissal`: Textarea
    - "Why should this case be dismissed? What legal standard isn't met?"
- `supporting_arguments`: List of text items
    - Each: legal argument + why it matters
- `opposing_party_claims`: Textarea
    - "What is the other side claiming? Quote from complaint/indictment..."
- `case_law_already_found`: List (optional)
    - "Any cases you've already found that support your position?"

**Preferences:**
- `standard_of_review`: Auto-populated based on motion type
- `include_alternative_relief`: Checkbox
    - If checked: "What alternative relief do you seek?"

**Output Format:**
```typescript
interface MotionDraft {
  caption: string;
  introduction: string;
  statement_of_facts: string;
  legal_standard: string;
  argument_sections: ArgumentSection[];
  conclusion: string;
  relief_requested: string;
  citations: Citation[];
  signature_block: string;
  created_at: datetime;
  workflow_id: string;
}

interface ArgumentSection {
  heading: string;
  content: string;
  supporting_citations: Citation[];
}
```

---

### 4. Defense Strategy Analyzer

**Route:** `/strategy/defense-analysis`

**Purpose:** Analyze potential defense strategies with Ohio case law support

**Input Fields:**

**Structured:**
- `case_type`: "Criminal" (Phase 1)
- `charges`: Multi-select (Ohio criminal offenses)
- `case_stage`: Dropdown ["Pre-indictment", "Indicted", "Pre-trial", "Trial", "Post-conviction"]
- `defendant_background`: Checkboxes ["First offense", "Prior record", "Juvenile record", "Pending cases"]

**Unstructured:**
- `facts_summary`: Textarea
    - "Describe the alleged incident and circumstances..."
- `evidence_against`: Textarea
    - "What evidence does the prosecution have?"
- `witness_statements`: List
    - "Who are the witnesses? What will they say?"
- `defendant_version`: Textarea
    - "What does the defendant say happened?"
- `potential_issues`: Textarea (optional)
    - "Any search/seizure issues? Miranda issues? Chain of custody problems?"

**Output Format:**
```typescript
interface DefenseStrategyAnalysis {
  case_assessment: {
    strength_of_prosecution: string;
    viable_defenses: DefenseOption[];
    evidentiary_issues: Issue[];
    procedural_issues: Issue[];
  };
  recommended_strategy: {
    primary_approach: string;
    rationale: string;
    supporting_precedents: Citation[];
    risks: string[];
    likelihood_of_success: string;
  };
  alternative_strategies: DefenseOption[];
  motions_to_consider: MotionSuggestion[];
  plea_negotiation_leverage: string[];
  created_at: datetime;
  workflow_id: string;
}

interface DefenseOption {
  defense_name: string;
  legal_basis: string;
  elements_to_prove: string[];
  supporting_cases: Citation[];
  challenges: string[];
  success_rate_context: string;
}
```

**UI Features:**
- Expandable sections for each defense option
- Comparison view (side-by-side defense strategies)
- Export to strategy memo
- "Deep dive" button on specific defense → researches that defense

---

### 5. Summary Judgment Brief Assistant

**Route:** `/drafting/summary-judgment`

**Purpose:** Draft summary judgment motion with "no genuine issue of material fact" analysis

**Input Fields:**

**Structured:**
- `moving_party`: Radio ["Plaintiff", "Defendant"]
- `case_type`: "Civil"
- `case_number`: Text
- `discovery_complete`: Checkbox

**Unstructured:**
- `undisputed_facts`: List of text items
    - "List facts that are not in dispute (from depositions, admissions, etc.)"
- `disputed_facts`: List of text items
    - "What facts does the other side dispute?"
- `legal_claims`: List
    - "What claims are you moving for summary judgment on?"
- `evidence_record`: Textarea
    - "What deposition testimony, documents, affidavits support your position?"
- `why_no_genuine_issue`: Textarea
    - "Why is there no genuine issue of material fact?"

**Output Format:**
```typescript
interface SummaryJudgmentDraft {
  introduction: string;
  statement_of_facts: {
    undisputed_facts: string[];
    disputed_facts_irrelevance: string;
  };
  legal_standard: string;
  argument_sections: ArgumentSection[];
  burden_of_proof_analysis: string;
  conclusion: string;
  citations: Citation[];
  evidence_index: string[];
  created_at: datetime;
}
```

---

### 6. Discovery Request Generator

**Route:** `/drafting/discovery-request`

**Purpose:** Generate interrogatories, requests for production, requests for admission

**Input Fields:**

**Structured:**
- `discovery_type`: Radio
    - "Interrogatories"
    - "Request for Production of Documents"
    - "Request for Admissions"
- `case_type`: ["Criminal", "Civil"]
- `party_serving_on`: Text ("Defendant", "Plaintiff", "State", etc.)

**Unstructured:**
- `case_summary`: Textarea
    - "Brief summary of the case and claims..."
- `information_needed`: Textarea
    - "What do you need to discover? What are you trying to prove?"
- `specific_documents`: List (for RFP)
    - "Any specific documents you want to request?"
- `facts_to_admit`: List (for RFA)
    - "What facts do you want the other party to admit?"

**Preferences:**
- `number_of_items`: Slider [10-40]
- `tone`: Radio ["Standard", "Aggressive", "Cooperative"]

**Output Format:**
```typescript
interface DiscoveryRequestDraft {
  caption: string;
  introduction: string;
  definitions: string[];
  instructions: string[];
  requests: DiscoveryItem[];
  signature_block: string;
  created_at: datetime;
}

interface DiscoveryItem {
  number: number;
  request_text: string;
  rationale: string; // Internal note on why this is requested
  relevance_citation: Citation[]; // Case law supporting relevance
}
```

---


## Temporal Workflows

### Base Workflow Pattern

All drafting workflows follow this pattern:

```python
# workflows/drafting/base.py

from temporalio import workflow
from typing import TypeVar, Generic
from abc import ABC, abstractmethod

InputT = TypeVar('InputT')
OutputT = TypeVar('OutputT')

class BaseDraftingWorkflow(ABC, Generic[InputT, OutputT]):
    """Base class for all drafting workflows"""
    
    @workflow.defn
    class Workflow:
        @workflow.run
        async def run(self, input_data: InputT) -> OutputT:
            """Execute the drafting workflow"""
            
            # Step 1: Analyze input and determine research needs
            research_queries = await self.generate_research_queries(input_data)
            
            # Step 2: Search LMDB for relevant cases
            relevant_cases = await self.search_relevant_cases(research_queries)
            
            # Step 3: Generate draft using vLLM
            draft = await self.generate_draft(input_data, relevant_cases)
            
            # Step 4: Extract and validate citations
            citations = await self.extract_citations(draft)
            
            # Step 5: Format output
            output = await self.format_output(draft, citations)
            
            # Step 6: Store in database
            await self.store_draft(input_data, output)
            
            return output
        
        @abstractmethod
        async def generate_research_queries(self, input_data: InputT) -> list[str]:
            """Generate search queries based on input"""
            pass
        
        @abstractmethod
        async def generate_draft(
            self, 
            input_data: InputT, 
            relevant_cases: list[dict]
        ) -> str:
            """Generate the draft using vLLM"""
            pass
        
        # ... other abstract methods
```

### Opening Statement Workflow

```python
# workflows/drafting/opening_statement.py

from temporalio import workflow, activity
from temporalio.common import RetryPolicy
from datetime import timedelta
from models.drafting_inputs import OpeningStatementInput
from models.drafting import Draft, DraftType, DraftStatus

@workflow.defn
class DraftOpeningStatementWorkflow:
    
    @workflow.run
    async def run(self, input_data: OpeningStatementInput) -> dict:
        """
        Generate opening statement with Ohio case law citations
        
        Workflow Steps:
        1. Analyze charges and case type to determine relevant statutes
        2. Search LMDB for similar successful opening statements/cases
        3. Extract key legal principles from relevant cases
        4. Generate draft using vLLM with context
        5. Validate citations and legal accuracy
        6. Format output for attorney review
        """
        
        workflow_id = workflow.info().workflow_id
        
        # Step 1: Create draft record in database (status: generating)
        draft_id = await workflow.execute_activity(
            create_draft_record,
            args=[input_data, workflow_id, DraftType.OPENING_STATEMENT],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )
        
        # Step 2: Analyze input to generate research queries
        research_queries = await workflow.execute_activity(
            generate_opening_statement_research_queries,
            args=[input_data],
            start_to_close_timeout=timedelta(seconds=60)
        )
        
        # Step 3: Search LMDB for relevant cases
        relevant_cases = await workflow.execute_activity(
            search_lmdb_for_cases,
            args=[research_queries, input_data.case_type],
            start_to_close_timeout=timedelta(minutes=2),
            retry_policy=RetryPolicy(maximum_attempts=2)
        )
        
        # Step 4: Search for similar case outcomes (wins with similar facts)
        similar_case_strategies = await workflow.execute_activity(
            find_similar_case_strategies,
            args=[input_data.charges, input_data.facts_narrative],
            start_to_close_timeout=timedelta(minutes=2)
        )
        
        # Step 5: Generate opening statement using vLLM
        draft_content = await workflow.execute_activity(
            generate_opening_statement_draft,
            args=[input_data, relevant_cases, similar_case_strategies],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=2)
        )
        
        # Step 6: Extract and validate citations
        citations = await workflow.execute_activity(
            extract_and_validate_citations,
            args=[draft_content, relevant_cases],
            start_to_close_timeout=timedelta(minutes=1)
        )
        
        # Step 7: Format final output
        formatted_output = await workflow.execute_activity(
            format_opening_statement_output,
            args=[draft_content, citations, input_data],
            start_to_close_timeout=timedelta(seconds=30)
        )
        
        # Step 8: Update draft record (status: completed)
        await workflow.execute_activity(
            update_draft_record,
            args=[draft_id, formatted_output, citations, DraftStatus.COMPLETED],
            start_to_close_timeout=timedelta(seconds=30)
        )
        
        return {
            "draft_id": draft_id,
            "workflow_id": workflow_id,
            "content": formatted_output,
            "citations": citations,
            "status": "completed"
        }

# Activities

@activity.defn
async def generate_opening_statement_research_queries(
    input_data: OpeningStatementInput
) -> list[str]:
    """
    Generate targeted search queries based on case details
    
    Returns queries like:
    - "Ohio theft defense opening statement precedent"
    - "ORC 2913.02 successful defense strategies"
    - "consent defense theft similar facts"
    """
    queries = []
    
    # Base query for each charge
    for charge in input_data.charges:
        queries.append(f"{charge} successful defense opening statement")
        queries.append(f"{charge} case law elements")
    
    # Theory-based query
    if input_data.theory_of_case:
        theory_keywords = extract_keywords(input_data.theory_of_case)
        queries.append(f"{' '.join(theory_keywords)} defense strategy")
    
    # Evidence-based queries
    if input_data.key_evidence:
        for evidence in input_data.key_evidence[:3]:  # Top 3
            evidence_type = categorize_evidence(evidence)
            queries.append(f"{evidence_type} admissibility Ohio")
    
    return queries

@activity.defn
async def search_lmdb_for_cases(
    queries: list[str],
    case_type: str
) -> list[dict]:
    """
    Search LMDB knowledge base for relevant Ohio cases
    """
    from services.lmdb_client import LMDBClient
    
    client = LMDBClient()
    all_cases = []
    
    for query in queries:
        cases = await client.search(
            query=query,
            filters={"case_type": case_type, "jurisdiction": "Ohio"},
            limit=10
        )
        all_cases.extend(cases)
    
    # Deduplicate and rank by relevance
    unique_cases = deduplicate_by_citation(all_cases)
    ranked_cases = rank_by_relevance(unique_cases, queries)
    
    return ranked_cases[:20]  # Top 20 most relevant

@activity.defn
async def generate_opening_statement_draft(
    input_data: OpeningStatementInput,
    relevant_cases: list[dict],
    similar_strategies: list[dict]
) -> dict:
    """
    Call vLLM to generate the opening statement draft
    """
    from services.vllm_client import VLLMClient
    
    # Build context from cases
    case_context = format_cases_for_context(relevant_cases)
    strategy_context = format_strategies_for_context(similar_strategies)
    
    # Build prompt
    system_prompt = """You are an expert Ohio trial attorney with 20+ years of experience. 
    You are drafting an opening statement for a trial. Your opening statement should:
    
    1. Tell a compelling story that the jury will remember
    2. Cite specific Ohio case law and statutes inline using [Case Name, Citation] format
    3. Preview evidence without arguing
    4. Establish your theory of the case
    5. Address weaknesses proactively
    6. Follow Ohio rules of evidence and procedure
    7. Be appropriate for the specified tone and length
    
    Every legal claim MUST include a citation to supporting Ohio case law or statute.
    """
    
    user_prompt = f"""
    Draft an opening statement for this case:
    
    CASE DETAILS:
    Type: {input_data.case_type}
    Charges: {", ".join(input_data.charges)}
    Defendant: {input_data.defendant_name}
    Court: {input_data.court}
    
    FACTS:
    {input_data.facts_narrative}
    
    DEFENSE THEORY:
    {input_data.theory_of_case}
    
    KEY EVIDENCE:
    {format_list(input_data.key_evidence)}
    
    KEY WITNESSES:
    {format_list(input_data.key_witnesses)}
    
    OPPOSING COUNSEL'S LIKELY THEORY:
    {input_data.opposing_counsel_theory or "Unknown"}
    
    RELEVANT OHIO CASE LAW:
    {case_context}
    
    SUCCESSFUL STRATEGIES IN SIMILAR CASES:
    {strategy_context}
    
    TONE: {input_data.tone}
    LENGTH: {input_data.length}
    
    Generate a compelling opening statement with proper structure:
    1. Introduction (hook the jury)
    2. Facts (tell the story chronologically)
    3. Legal Framework (what law applies, with citations)
    4. Evidence Preview (what will be shown, not argued)
    5. Conclusion (what you'll prove)
    
    Include inline citations in [Case Name, Citation] format after every legal principle.
    """
    
    client = VLLMClient()
    response = await client.generate(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=4000,
        temperature=0.7
    )
    
    # Parse response into structured format
    parsed_draft = parse_opening_statement_response(response)
    
    return parsed_draft

@activity.defn
async def extract_and_validate_citations(
    draft_content: dict,
    source_cases: list[dict]
) -> list[dict]:
    """
    Extract citations from draft and validate against LMDB
    """
    import re
    
    # Extract citation pattern [Case Name, Citation]
    citation_pattern = r'\[(.*?),\s*(.*?)\]'
    
    full_text = " ".join([
        draft_content.get("introduction", ""),
        draft_content.get("facts_section", ""),
        draft_content.get("legal_framework", ""),
        draft_content.get("evidence_preview", ""),
        draft_content.get("conclusion", "")
    ])
    
    matches = re.findall(citation_pattern, full_text)
    
    citations = []
    for case_name, citation_text in matches:
        # Validate this citation exists in LMDB or source_cases
        validated = validate_citation_exists(case_name, citation_text, source_cases)
        
        if validated:
            citations.append({
                "case_name": case_name,
                "citation": citation_text,
                "relevance": extract_relevance_context(case_name, draft_content),
                "lmdb_key": validated.get("lmdb_key"),
                "section_used_in": find_section_for_citation(case_name, draft_content)
            })
    
    return citations

@activity.defn
async def format_opening_statement_output(
    draft_content: dict,
    citations: list[dict],
    input_data: OpeningStatementInput
) -> dict:
    """
    Format the final output structure
    """
    return {
        "introduction": draft_content.get("introduction", ""),
        "facts_section": draft_content.get("facts_section", ""),
        "legal_framework": draft_content.get("legal_framework", ""),
        "evidence_preview": draft_content.get("evidence_preview", ""),
        "conclusion": draft_content.get("conclusion", ""),
        "citations": citations,
        "estimated_duration": estimate_duration(draft_content, input_data.length),
        "metadata": {
            "case_number": input_data.case_number,
            "defendant": input_data.defendant_name,
            "court": input_data.court,
            "charges": input_data.charges,
            "tone": input_data.tone
        }
    }

# Similar workflows for other draft types:
# - DraftClosingArgumentWorkflow
# - DraftMotionToDismissWorkflow
# - DefenseStrategyWorkflow
# - etc.
```

---
ff
---

## Implementation Priority

### Phase 1: MVP (Weeks 1-4)

**Week 1-2: Foundation**
1. ✅ Database models (Draft, Citation, DraftFeedback)
2. ✅ Base Temporal workflow pattern
3. ✅ BFF routing structure
4. ✅ One complete feature: **Motion to Dismiss Drafter**
    - Most standardized format
    - Easiest to validate
    - High attorney value

**Week 3-4: Polish & Test**
1. ✅ Draft viewer component
2. ✅ Citation tooltips
3. ✅ Export to DOCX
4. ✅ Feedback system
5. ✅ Test with 2-3 attorneys (get real feedback)

### Phase 2: Expansion (Weeks 5-8)

**Week 5-6:**
1. ✅ Opening Statement Builder
2. ✅ Closing Argument Builder
3. ✅ Improve prompts based on Phase 1 feedback

**Week 7-8:**
1. ✅ Defense Strategy Analyzer
2. ✅ Discovery Request Generator
3. ✅ Version control for drafts (track edits)

### Phase 3: Advanced Features (Weeks 9-12)

1. ✅ Summary Judgment Brief Assistant
2. ✅ Collaborative editing (multiple attorneys on same draft)
3. ✅ Integration with case management
4. ✅ Template library (save good drafts as templates)
5. ✅ Analytics (which drafts get highest ratings, most exports)

---

## Technical Considerations

### Performance

**LMDB Search Optimization:**
- Index by: charge type, case type, court, year
- Cache frequent queries
- Pre-compute embeddings for case similarity

**vLLM Inference:**
- Monitor token usage per draft type
- Implement request queuing for concurrent requests
- Consider batch processing for off-peak hours

**Database:**
- Index on: org_id, user_id, draft_type, status, created_at
- Partition drafts table by org_id (when > 1M records)

### Error Handling

**Workflow Failures:**
- Retry policy: max 2 attempts with exponential backoff
- Save partial results before failure
- Clear error messages to user ("Citation validation failed - trying again")

**Citation Validation:**
- If case not found in LMDB, flag for manual review
- Don't fail entire draft for one bad citation
- Warn attorney about unvalidated citations

### Security

**Org Isolation:**
- ALWAYS filter queries by org_id
- Never expose draft_id without org verification
- Audit log for all draft access

**Attorney-Client Privilege:**
- Encrypt draft content at rest
- Never log case facts or client names
- Make audit logs immutable

### Monitoring

**Key Metrics:**
- Draft generation time by type
- Citation accuracy rate
- User satisfaction ratings
- Edit rate (how often attorneys modify drafts)
- Export rate (indicates usefulness)

**Alerts:**
- Workflow failures > 5% in 1 hour
- vLLM response time > 2 minutes
- LMDB search errors

---

## Success Metrics

### Product Metrics

**Usage:**
- Drafts generated per day
- Active attorneys per week
- Draft types distribution

**Quality:**
- Average satisfaction rating (target: > 4.0/5)
- Citation accuracy (target: > 95%)
- Export rate (target: > 60%)

**Business:**
- Conversion from research-only to drafting features
- Attorney testimonials
- Time saved (survey data)

### Technical Metrics

**Performance:**
- P50 draft generation time: < 90 seconds
- P95 draft generation time: < 180 seconds
- vLLM inference time: < 60 seconds

**Reliability:**
- Workflow success rate: > 98%
- Citation validation accuracy: > 95%
- Uptime: > 99.5%

---

## Appendix

### Sample Prompts

See `/docs/prompts/` directory for complete prompt templates for each draft type.

### Citation Format Standards

Ohio case citations follow these formats:
- Ohio Supreme Court: `[Case Name], [Volume] Ohio St.3d [Page] ([Year])`
- Ohio Court of Appeals: `[Case Name], [Volume] Ohio App.3d [Page] ([District] [Year])`
- Ohio Revised Code: `Ohio Rev. Code Ann. § [Section]`

### Testing Strategy

1. **Unit Tests**: Activity functions, citation parsing, formatting
2. **Integration Tests**: Workflow execution end-to-end
3. **Validation Tests**: Citation accuracy against known cases
4. **User Acceptance**: Real attorneys test with real cases

---

## Change Log

**v1.0 - November 10, 2025**
- Initial specification
- 6 core features defined
- Implementation priority established
- Success metrics defined

---

**Document Owner:** Development Team  
**Last Updated:** November 10, 2025  
**Next Review:** After Phase 1 completion

# High-Value Attorney Features - Developer Documentation

**Date:** November 10, 2025  
**Author:** Development Team  
**Status:** Phase 1 Core Features

---

## Executive Summary

This document specifies the three highest-value features for Jurist, prioritized by frequency of use and impact on case outcomes:

1. **Case Evaluation/Valuation Tool** - Used in 100% of cases to determine settlement/demand ranges
2. **Legal Research with Argument Builder** - Enhanced version of existing research that drafts arguments with citations
3. **Plea Deal/Settlement Analyzer** - Used in 95% of criminal/civil cases to evaluate offers

These features target the most time-consuming, outcome-determinative work that attorneys do. Each feature is used 10-50x more frequently than trial prep features.

**Key Design Principle:** Build on existing infrastructure (vLLM, LMDB, Temporal, BFF) with extensible architecture for future features.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Feature 1: Case Evaluation/Valuation Tool](#feature-1-case-evaluationvaluation-tool)
3. [Feature 2: Legal Research with Argument Builder](#feature-2-legal-research-with-argument-builder)
4. [Feature 3: Plea Deal/Settlement Analyzer](#feature-3-plea-dealsettlement-analyzer)
5. [Shared Data Models](#shared-data-models)
6. [Temporal Workflows](#temporal-workflows)
7. [API Endpoints](#api-endpoints)
8. [Frontend Components](#frontend-components)
9. [Data Requirements](#data-requirements)
10. [Implementation Roadmap](#implementation-roadmap)
11. [Future-Proofing](#future-proofing)

---

## Architecture Overview

### Integration with Existing System

```
┌─────────────────────────────────────────────────────────┐
│              Frontend (Next.js)                          │
│  /research (existing) | /evaluation | /analysis         │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────────────┐
│           BFF Service (Port 8008) - EXISTING            │
│  Add new routes: /api/evaluation, /api/analysis         │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────────────┐
│        Temporal Workflows - EXISTING + NEW              │
│  - ResearchWorkflow (existing)                           │
│  - CaseEvaluationWorkflow (new)                          │
│  - ArgumentBuilderWorkflow (new)                         │
│  - PleaAnalysisWorkflow (new)                            │
└──────────┬────────────────────┬─────────────────────────┘
           │                    │
           ↓                    ↓
┌──────────────────┐   ┌────────────────────────┐
│  vLLM (8004)     │   │  LMDB Knowledge        │
│  70B Model       │   │  + NEW: Verdicts DB    │
│  EXISTING        │   │  + NEW: Sentencing DB  │
└──────────────────┘   └────────────────────────┘
```

### Key Principles

1. **Reuse Existing Infrastructure:** Don't rebuild what works
2. **Extensible Data Models:** Design for future features
3. **Org-Scoped Security:** Every query filtered by org_id
4. **Async Workflows:** Long-running analysis via Temporal
5. **Citation-Driven:** Every claim backed by Ohio case law

---

## Feature 1: Case Evaluation/Valuation Tool

### Overview

**Purpose:** Help attorneys determine realistic case value and settlement strategy

**User Story:**
"As a personal injury attorney, I need to know what my client's case is worth so I can advise them on settlement and formulate a demand letter."

**Frequency:** Used in 100% of civil cases, multiple times as case develops

**Current Process:**
1. Attorney manually searches for comparable verdicts (2-4 hours)
2. Reviews 10-20 cases to find similar facts
3. Adjusts for jurisdiction, year, injury severity
4. Calculates range in spreadsheet
5. Total time: 3-5 hours per case

**With Jurist:**
1. Enter case details (10 minutes)
2. AI finds comparable Ohio verdicts
3. Generates valuation with rationale
4. Total time: 15 minutes

---

### User Interface

**Route:** `/evaluation/case-value`

#### Input Form

```typescript
// Case Type Selection
┌─────────────────────────────────────────────────────────┐
│ Case Type: [Personal Injury ▼]                         │
│   - Personal Injury (Auto, Slip & Fall, Medical Mal)   │
│   - Employment (Discrimination, Wrongful Term, Wage)    │
│   - Contract Dispute                                     │
│   - Property Damage                                      │
│   - Other Civil                                          │
└─────────────────────────────────────────────────────────┘

// For Personal Injury:
┌─────────────────────────────────────────────────────────┐
│ INJURY DETAILS                                           │
│                                                          │
│ Injury Type: [☑ Broken bones] [☑ Soft tissue]          │
│              [☐ Head trauma] [☐ Spinal injury]          │
│              [☐ Burns] [☐ Scarring]                     │
│                                                          │
│ Injury Severity: (○ Minor ● Moderate ○ Severe ○ Catastrophic) │
│                                                          │
│ Permanent Impairment: [Yes ▼]                           │
│   - If yes, describe: [Permanent limp, reduced mobility]│
│                                                          │
│ Medical Treatment:                                       │
│   [☑] Emergency room                                     │
│   [☑] Hospitalization: [3 days]                         │
│   [☑] Surgery: [Describe: Orthopedic surgery on femur]  │
│   [☑] Physical therapy: [6 months]                      │
│   [☐] Ongoing treatment                                  │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ LIABILITY ASSESSMENT                                     │
│                                                          │
│ Defendant's Fault: [Clear ▼]                            │
│   - Clear (90-100% likely liable)                       │
│   - Strong (70-90%)                                      │
│   - Disputed (50-70%)                                    │
│   - Weak (below 50%)                                     │
│                                                          │
│ Comparative Negligence Issues: [No ▼]                   │
│   - If yes, plaintiff's fault %: [___]                  │
│                                                          │
│ Liability Details: [Textarea]                           │
│ "Defendant ran red light, admitted fault at scene,      │
│  multiple witnesses, dash cam footage..."                │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ DAMAGES BREAKDOWN                                        │
│                                                          │
│ Medical Bills (Past):    $[_________]  [$42,500]       │
│ Future Medical (Est):    $[_________]  [$15,000]       │
│ Lost Wages (Past):       $[_________]  [$8,200]        │
│ Future Lost Earnings:    $[_________]  [$0]            │
│ Property Damage:         $[_________]  [$4,300]        │
│                                                          │
│ Total Economic Damages:  $70,000 (calculated)           │
│                                                          │
│ Pain & Suffering Multiplier: [Use comparable verdicts]  │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ CASE CONTEXT                                             │
│                                                          │
│ County/Venue: [Franklin County ▼]                       │
│                                                          │
│ Defendant Type: [Individual ▼]                          │
│   - Individual                                           │
│   - Small Business                                       │
│   - Large Corporation                                    │
│   - Government Entity                                    │
│                                                          │
│ Insurance Available: [Yes ▼]                            │
│ Policy Limits (if known): $[_________]  [$100,000]     │
│                                                          │
│ Plaintiff Likability: (○ Low ● Average ○ High)         │
│ Defendant Likability: (● Low ○ Average ○ High)         │
│                                                          │
│ Special Considerations: [Textarea - optional]            │
│ "Plaintiff is retired teacher, very sympathetic.        │
│  Defendant has prior DUI..."                             │
└─────────────────────────────────────────────────────────┘

[Generate Case Valuation]
```

---

### Output Display

```typescript
┌─────────────────────────────────────────────────────────┐
│ CASE VALUATION REPORT                                    │
│ Generated: Nov 10, 2025 | Personal Injury - Auto        │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ 💰 RECOMMENDED VALUATION                                │
│                                                          │
│  Settlement Range:    $95,000 - $165,000                │
│  Likely Settlement:   $125,000                           │
│  Initial Demand:      $225,000                           │
│                                                          │
│  Confidence: High (based on 18 comparable cases)        │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ 📊 VALUATION BREAKDOWN                                  │
│                                                          │
│  Economic Damages:           $70,000                     │
│    Medical Bills (Past)       $42,500                   │
│    Future Medical             $15,000                   │
│    Lost Wages                 $8,200                    │
│    Property Damage            $4,300                    │
│                                                          │
│  Non-Economic Damages:       $55,000 - $125,000         │
│    Based on 2.0x - 3.5x multiplier for:                 │
│    - Moderate injury severity                            │
│    - Permanent impairment                                │
│    - Clear liability                                     │
│    - Franklin County venue                               │
│                                                          │
│  Total Range:                $125,000 - $195,000        │
│  Adjusted for negotiation:   $95,000 - $165,000         │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ 🔍 COMPARABLE VERDICTS (Franklin County)                │
│                                                          │
│ [Expandable Card 1]                                      │
│ Smith v. Johnson (Franklin Cty. C.P. 2023)              │
│ Verdict: $142,000                                        │
│ Similarity: 87% match ⭐⭐⭐⭐⭐                           │
│                                                          │
│ Facts: Auto accident, broken femur, 4 days hospitalized,│
│        permanent limp. Defendant admitted fault.         │
│ Economic: $52,000 | Non-economic: $90,000               │
│ Multiplier: 2.7x                                         │
│                                                          │
│ [View Full Case] [Add to Report]                        │
│                                                          │
│ [Expandable Card 2]                                      │
│ Williams v. State Farm (Franklin Cty. C.P. 2024)        │
│ Settlement: $118,000                                     │
│ Similarity: 82% match ⭐⭐⭐⭐                            │
│ ...                                                      │
│                                                          │
│ [Show 15 more comparable cases]                         │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ ⚖️ STRENGTHS & WEAKNESSES                               │
│                                                          │
│ STRENGTHS:                                               │
│ ✓ Clear liability (defendant admitted fault)            │
│ ✓ Strong damages (surgery, permanent impairment)        │
│ ✓ Sympathetic plaintiff (retired teacher)               │
│ ✓ Favorable venue (Franklin County averages higher)     │
│ ✓ Objective evidence (medical records, dash cam)        │
│                                                          │
│ WEAKNESSES:                                              │
│ ⚠ Policy limits may cap recovery at $100,000            │
│ ⚠ Age of plaintiff (65) may reduce future damages      │
│ ⚠ Pre-existing arthritis (documented) may be defense    │
│                                                          │
│ RISK FACTORS:                                            │
│ • Defendant's insurance may lowball due to policy limit │
│ • Medical liens total $38,000 - reduces net to client  │
│ • Litigation costs estimated at $8,000-12,000           │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ 📋 STRATEGIC RECOMMENDATIONS                            │
│                                                          │
│ SETTLEMENT STRATEGY:                                     │
│ 1. Initial Demand: $225,000                             │
│    Rationale: 3x economic damages, accounts for         │
│    permanent impairment and clear liability             │
│                                                          │
│ 2. Realistic Settlement Target: $125,000                │
│    Based on comparable verdicts and policy limits       │
│                                                          │
│ 3. Walk-Away Number: $95,000                            │
│    Minimum to cover damages + costs + reasonable comp   │
│                                                          │
│ NEGOTIATION LEVERAGE:                                    │
│ • Highlight strongest comparable: Smith v. Johnson      │
│   ($142k for similar facts in same venue)               │
│ • Emphasize trial risk: Similar cases average $135k     │
│ • Point to defense costs: $20-30k to take to trial      │
│                                                          │
│ TIMING:                                                  │
│ • Demand letter: Immediately (treatment complete)       │
│ • File suit if no response: 60 days                     │
│ • Mediation: 6-9 months (pressure point)                │
│                                                          │
│ CLIENT ADVICE:                                           │
│ "Your case has strong settlement value between $95k-    │
│  $165k. I recommend demanding $225k initially, with     │
│  expectation of settling around $125k. This accounts    │
│  for the policy limits and comparable verdicts in       │
│  Franklin County. We should reject anything under $95k."│
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ 📄 EXPORT OPTIONS                                       │
│                                                          │
│ [Export Valuation Report] [Generate Demand Letter]      │
│ [Add to Case File] [Email to Client]                    │
└─────────────────────────────────────────────────────────┘
```

---

### Data Models

```python
# models/evaluation.py

from sqlalchemy import String, Integer, Float, JSON, DateTime, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional
import enum

class CaseType(str, enum.Enum):
    PERSONAL_INJURY = "personal_injury"
    EMPLOYMENT = "employment"
    CONTRACT = "contract"
    PROPERTY_DAMAGE = "property_damage"
    OTHER_CIVIL = "other_civil"

class InjurySeverity(str, enum.Enum):
    MINOR = "minor"
    MODERATE = "moderate"
    SEVERE = "severe"
    CATASTROPHIC = "catastrophic"

class LiabilityStrength(str, enum.Enum):
    CLEAR = "clear"          # 90-100% likely
    STRONG = "strong"        # 70-90%
    DISPUTED = "disputed"    # 50-70%
    WEAK = "weak"           # <50%

class CaseEvaluation(Base):
    __tablename__ = "case_evaluations"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[str] = mapped_column(String(255), index=True)
    user_id: Mapped[str] = mapped_column(String(255), index=True)
    case_id: Mapped[Optional[int]] = mapped_column(ForeignKey("cases.id"), nullable=True)
    
    # Case metadata
    case_type: Mapped[CaseType]
    case_name: Mapped[str] = mapped_column(String(500))
    
    # Input data (stored as JSON for flexibility)
    input_data: Mapped[dict] = mapped_column(JSON)
    
    # Valuation results
    settlement_range_low: Mapped[float]  # Floor
    settlement_range_high: Mapped[float]  # Ceiling
    likely_settlement: Mapped[float]  # Most probable
    recommended_demand: Mapped[float]  # Initial demand amount
    
    confidence: Mapped[str] = mapped_column(String(50))  # "High", "Medium", "Low"
    
    # Breakdown
    economic_damages: Mapped[float]
    non_economic_range_low: Mapped[float]
    non_economic_range_high: Mapped[float]
    
    # Comparable cases (array of case IDs or citations)
    comparable_cases: Mapped[list[dict]] = mapped_column(JSON)
    
    # Strategic analysis
    strengths: Mapped[list[str]] = mapped_column(JSON)
    weaknesses: Mapped[list[str]] = mapped_column(JSON)
    risk_factors: Mapped[list[str]] = mapped_column(JSON)
    recommendations: Mapped[dict] = mapped_column(JSON)
    
    # Workflow tracking
    workflow_id: Mapped[str] = mapped_column(String(255), unique=True)
    
    # Versioning (can re-run evaluation as case develops)
    version: Mapped[int] = mapped_column(default=1)
    parent_evaluation_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("case_evaluations.id"),
        nullable=True
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Relationships
    children: Mapped[list["CaseEvaluation"]] = relationship(
        "CaseEvaluation",
        backref="parent",
        remote_side=[id]
    )

class ComparableVerdict(Base):
    """Database of Ohio verdicts and settlements for comparison"""
    __tablename__ = "comparable_verdicts"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Case identification
    case_name: Mapped[str] = mapped_column(String(500))
    case_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    court: Mapped[str] = mapped_column(String(200))
    county: Mapped[str] = mapped_column(String(100), index=True)
    year: Mapped[int] = mapped_column(index=True)
    
    # Outcome
    verdict_or_settlement: Mapped[str] = mapped_column(String(20))  # "verdict" or "settlement"
    amount: Mapped[float] = mapped_column(index=True)
    
    # Case type
    case_type: Mapped[CaseType] = mapped_column(index=True)
    sub_type: Mapped[str] = mapped_column(String(100))  # "auto_accident", "slip_and_fall", etc.
    
    # Personal Injury specific fields
    injury_types: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    injury_severity: Mapped[Optional[InjurySeverity]] = mapped_column(nullable=True)
    permanent_impairment: Mapped[Optional[bool]] = mapped_column(nullable=True)
    
    # Damages breakdown
    economic_damages: Mapped[float]
    non_economic_damages: Mapped[float]
    punitive_damages: Mapped[Optional[float]] = mapped_column(nullable=True)
    
    # Liability context
    liability_strength: Mapped[Optional[LiabilityStrength]] = mapped_column(nullable=True)
    comparative_negligence_pct: Mapped[Optional[int]] = mapped_column(nullable=True)
    
    # Fact pattern (for similarity matching)
    fact_summary: Mapped[str] = mapped_column(Text)
    fact_vector: Mapped[Optional[bytes]] = mapped_column(nullable=True)  # Embedding for similarity search
    
    # Parties
    plaintiff_type: Mapped[str] = mapped_column(String(100))  # "individual", "business"
    defendant_type: Mapped[str] = mapped_column(String(100))
    
    # Source
    source: Mapped[str] = mapped_column(String(200))  # Where we got this data
    source_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Quality/reliability
    data_quality: Mapped[str] = mapped_column(String(20), default="verified")  # "verified", "reported", "estimated"
    
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Indexes for fast querying
    __table_args__ = (
        Index('ix_verdict_type_county_year', 'case_type', 'county', 'year'),
        Index('ix_verdict_amount_range', 'amount'),
    )
```

### Pydantic Input Models

```python
# models/evaluation_inputs.py

from pydantic import BaseModel, Field, validator
from typing import Optional, Literal
from datetime import date

class PersonalInjuryInput(BaseModel):
    """Input for personal injury case evaluation"""
    
    # Case identification
    case_name: str = Field(..., min_length=1)
    
    # Injury details
    injury_types: list[str] = Field(..., min_items=1)
    injury_severity: Literal["minor", "moderate", "severe", "catastrophic"]
    permanent_impairment: bool
    permanent_impairment_description: Optional[str] = None
    
    # Medical treatment
    emergency_room: bool = False
    hospitalization_days: Optional[int] = None
    surgery: bool = False
    surgery_description: Optional[str] = None
    physical_therapy_months: Optional[int] = None
    ongoing_treatment: bool = False
    
    # Liability
    liability_strength: Literal["clear", "strong", "disputed", "weak"]
    comparative_negligence: bool = False
    plaintiff_fault_pct: Optional[int] = Field(None, ge=0, le=100)
    liability_details: str = Field(..., min_length=50)
    
    # Damages
    medical_bills_past: float = Field(..., ge=0)
    medical_bills_future: float = Field(default=0, ge=0)
    lost_wages_past: float = Field(default=0, ge=0)
    lost_earnings_future: float = Field(default=0, ge=0)
    property_damage: float = Field(default=0, ge=0)
    
    # Context
    county: str
    defendant_type: Literal["individual", "small_business", "large_corporation", "government"]
    insurance_available: bool
    policy_limits: Optional[float] = None
    
    # Likability (affects jury verdicts)
    plaintiff_likability: Literal["low", "average", "high"] = "average"
    defendant_likability: Literal["low", "average", "high"] = "average"
    
    # Special considerations
    special_considerations: Optional[str] = None
    
    # Metadata
    org_id: str
    user_id: str
    case_id: Optional[int] = None
    
    @validator('plaintiff_fault_pct')
    def validate_comparative_negligence(cls, v, values):
        if values.get('comparative_negligence') and v is None:
            raise ValueError('Must specify plaintiff fault % if comparative negligence applies')
        return v
    
    @property
    def total_economic_damages(self) -> float:
        return (
            self.medical_bills_past +
            self.medical_bills_future +
            self.lost_wages_past +
            self.lost_earnings_future +
            self.property_damage
        )

class EmploymentCaseInput(BaseModel):
    """Input for employment case evaluation"""
    
    case_name: str
    
    # Employment context
    employment_type: Literal["wrongful_termination", "discrimination", "harassment", "wage_theft", "retaliation"]
    discrimination_basis: Optional[list[str]] = None  # ["race", "gender", "age", etc.]
    
    # Plaintiff details
    years_employed: float
    salary: float
    age: int
    
    # Damages
    lost_wages: float
    lost_benefits: float
    front_pay: Optional[float] = None
    emotional_distress_severity: Literal["minor", "moderate", "severe"]
    
    # Evidence strength
    documentation_quality: Literal["strong", "moderate", "weak"]
    witness_support: Literal["strong", "moderate", "weak", "none"]
    
    # Defendant context
    employer_size: Literal["small", "medium", "large"]
    employer_history: Literal["clean", "some_issues", "pattern_of_violations"]
    
    county: str
    org_id: str
    user_id: str
    case_id: Optional[int] = None

class ContractDisputeInput(BaseModel):
    """Input for contract dispute evaluation"""
    
    case_name: str
    
    # Contract details
    contract_type: str
    contract_value: float
    breach_type: Literal["material", "minor"]
    
    # Damages
    actual_damages: float
    consequential_damages: Optional[float] = None
    liquidated_damages: Optional[float] = None
    
    # Case strength
    contract_clarity: Literal["clear", "ambiguous"]
    breach_evidence: Literal["strong", "moderate", "weak"]
    
    county: str
    org_id: str
    user_id: str
    case_id: Optional[int] = None

# Union type for all case types
CaseEvaluationInput = PersonalInjuryInput | EmploymentCaseInput | ContractDisputeInput
```

---

### Temporal Workflow

```python
# workflows/evaluation/case_valuation.py

from temporalio import workflow, activity
from temporalio.common import RetryPolicy
from datetime import timedelta
from models.evaluation_inputs import PersonalInjuryInput
from models.evaluation import CaseEvaluation, ComparableVerdict

@workflow.defn
class CaseValuationWorkflow:
    """
    Generate case valuation with comparable verdicts
    
    Steps:
    1. Calculate total economic damages
    2. Search comparable verdicts database
    3. Rank comparables by similarity
    4. Calculate non-economic damages range using multipliers
    5. Adjust for venue, liability strength, and other factors
    6. Generate strategic recommendations
    7. Store results in database
    """
    
    @workflow.run
    async def run(self, input_data: PersonalInjuryInput) -> dict:
        workflow_id = workflow.info().workflow_id
        
        # Step 1: Create evaluation record (status: generating)
        evaluation_id = await workflow.execute_activity(
            create_evaluation_record,
            args=[input_data, workflow_id],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )
        
        # Step 2: Calculate economic damages
        economic_damages = await workflow.execute_activity(
            calculate_economic_damages,
            args=[input_data],
            start_to_close_timeout=timedelta(seconds=10)
        )
        
        # Step 3: Find comparable verdicts
        comparable_cases = await workflow.execute_activity(
            find_comparable_verdicts,
            args=[input_data],
            start_to_close_timeout=timedelta(minutes=2),
            retry_policy=RetryPolicy(maximum_attempts=2)
        )
        
        # Step 4: Calculate similarity scores
        ranked_comparables = await workflow.execute_activity(
            rank_comparables_by_similarity,
            args=[input_data, comparable_cases],
            start_to_close_timeout=timedelta(minutes=1)
        )
        
        # Step 5: Calculate non-economic damages range
        non_economic_range = await workflow.execute_activity(
            calculate_non_economic_damages,
            args=[input_data, ranked_comparables],
            start_to_close_timeout=timedelta(seconds=30)
        )
        
        # Step 6: Generate valuation ranges
        valuation = await workflow.execute_activity(
            generate_valuation_ranges,
            args=[economic_damages, non_economic_range, input_data],
            start_to_close_timeout=timedelta(seconds=30)
        )
        
        # Step 7: Analyze strengths and weaknesses
        swot_analysis = await workflow.execute_activity(
            analyze_case_strengths_weaknesses,
            args=[input_data, ranked_comparables],
            start_to_close_timeout=timedelta(minutes=1)
        )
        
        # Step 8: Generate strategic recommendations using vLLM
        recommendations = await workflow.execute_activity(
            generate_strategic_recommendations,
            args=[input_data, valuation, swot_analysis, ranked_comparables],
            start_to_close_timeout=timedelta(minutes=2)
        )
        
        # Step 9: Store complete evaluation
        await workflow.execute_activity(
            update_evaluation_record,
            args=[
                evaluation_id,
                valuation,
                ranked_comparables,
                swot_analysis,
                recommendations
            ],
            start_to_close_timeout=timedelta(seconds=30)
        )
        
        return {
            "evaluation_id": evaluation_id,
            "workflow_id": workflow_id,
            "valuation": valuation,
            "comparable_cases": ranked_comparables[:10],  # Top 10
            "swot_analysis": swot_analysis,
            "recommendations": recommendations,
            "status": "completed"
        }

# Activities

@activity.defn
async def find_comparable_verdicts(input_data: PersonalInjuryInput) -> list[dict]:
    """
    Query comparable_verdicts table for similar cases
    
    Matching criteria:
    - Same case type
    - Similar injury types
    - Same county or nearby counties
    - Recent years (prefer last 5 years)
    - Similar severity
    """
    from sqlalchemy import and_, or_
    from database import get_db
    
    db = next(get_db())
    
    # Build query
    query = db.query(ComparableVerdict).filter(
        ComparableVerdict.case_type == "personal_injury",
        ComparableVerdict.county.in_([
            input_data.county,
            # Add adjacent counties for broader search
        ]),
        ComparableVerdict.year >= 2019  # Last 5 years
    )
    
    # Filter by injury severity (plus/minus one level)
    severity_map = {"minor": 1, "moderate": 2, "severe": 3, "catastrophic": 4}
    input_severity = severity_map[input_data.injury_severity]
    
    query = query.filter(
        ComparableVerdict.injury_severity.in_([
            k for k, v in severity_map.items()
            if abs(v - input_severity) <= 1
        ])
    )
    
    # Prefer cases with similar liability strength
    if input_data.liability_strength in ["clear", "strong"]:
        # Prioritize clear liability cases
        query = query.order_by(
            ComparableVerdict.liability_strength == "clear",
            ComparableVerdict.year.desc()
        )
    
    # Limit results
    results = query.limit(50).all()
    
    # Convert to dict for serialization
    return [
        {
            "id": v.id,
            "case_name": v.case_name,
            "court": v.court,
            "county": v.county,
            "year": v.year,
            "amount": v.amount,
            "verdict_or_settlement": v.verdict_or_settlement,
            "economic_damages": v.economic_damages,
            "non_economic_damages": v.non_economic_damages,
            "injury_types": v.injury_types,
            "injury_severity": v.injury_severity,
            "liability_strength": v.liability_strength,
            "fact_summary": v.fact_summary,
        }
        for v in results
    ]

@activity.defn
async def rank_comparables_by_similarity(
    input_data: PersonalInjuryInput,
    comparables: list[dict]
) -> list[dict]:
    """
    Rank comparable cases by similarity to input case
    
    Similarity factors:
    - Injury type match (40%)
    - Severity match (20%)
    - Liability strength match (15%)
    - County match (10%)
    - Year recency (10%)
    - Permanent impairment match (5%)
    """
    
    def calculate_similarity_score(comparable: dict) -> float:
        score = 0.0
        
        # Injury type match (40 points)
        input_injuries = set(input_data.injury_types)
        comp_injuries = set(comparable.get("injury_types", []))
        injury_overlap = len(input_injuries & comp_injuries) / max(len(input_injuries), 1)
        score += injury_overlap * 40
        
        # Severity match (20 points)
        if comparable["injury_severity"] == input_data.injury_severity:
            score += 20
        elif abs(
            ["minor", "moderate", "severe", "catastrophic"].index(comparable["injury_severity"]) -
            ["minor", "moderate", "severe", "catastrophic"].index(input_data.injury_severity)
        ) == 1:
            score += 10  # Adjacent severity
        
        # Liability strength match (15 points)
        if comparable["liability_strength"] == input_data.liability_strength:
            score += 15
        elif (
            comparable["liability_strength"] in ["clear", "strong"] and
            input_data.liability_strength in ["clear", "strong"]
        ):
            score += 10  # Both strong liability
        
        # County match (10 points)
        if comparable["county"] == input_data.county:
            score += 10
        
        # Year recency (10 points) - more recent = higher score
        current_year = 2025
        years_old = current_year - comparable["year"]
        if years_old <= 2:
            score += 10
        elif years_old <= 5:
            score += 5
        
        # Permanent impairment match (5 points)
        comp_has_impairment = comparable.get("permanent_impairment", False)
        if comp_has_impairment == input_data.permanent_impairment:
            score += 5
        
        return score
    
    # Calculate scores and sort
    for comp in comparables:
        comp["similarity_score"] = calculate_similarity_score(comp)
        comp["similarity_percentage"] = int(comp["similarity_score"])
    
    # Sort by similarity (descending)
    ranked = sorted(comparables, key=lambda x: x["similarity_score"], reverse=True)
    
    return ranked

@activity.defn
async def calculate_non_economic_damages(
    input_data: PersonalInjuryInput,
    comparables: list[dict]
) -> dict:
    """
    Calculate non-economic damages range based on comparables
    
    Uses pain & suffering multiplier method:
    - Minor injury: 1.5x - 2.5x economic damages
    - Moderate injury: 2.0x - 3.5x
    - Severe injury: 3.0x - 5.0x
    - Catastrophic injury: 5.0x - 10.0x
    
    Adjusted based on:
    - Permanent impairment (+0.5x)
    - Clear liability (+0.5x)
    - High plaintiff likability (+0.3x)
    - Policy limits (cap if applicable)
    """
    
    economic = input_data.total_economic_damages
    
    # Base multiplier ranges by severity
    multiplier_ranges = {
        "minor": (1.5, 2.5),
        "moderate": (2.0, 3.5),
        "severe": (3.0, 5.0),
        "catastrophic": (5.0, 10.0)
    }
    
    base_low, base_high = multiplier_ranges[input_data.injury_severity]
    
    # Adjustments
    if input_data.permanent_impairment:
        base_low += 0.5
        base_high += 0.5
    
    if input_data.liability_strength in ["clear", "strong"]:
        base_low += 0.3
        base_high += 0.5
    
    if input_data.plaintiff_likability == "high":
        base_low += 0.2
        base_high += 0.3
    
    # Calculate range
    non_econ_low = economic * base_low
    non_econ_high = economic * base_high
    
    # Validate against comparables
    if comparables:
        comp_non_econ_amounts = [
            c["non_economic_damages"]
            for c in comparables[:10]  # Top 10 most similar
            if c["non_economic_damages"] > 0
        ]
        
        if comp_non_econ_amounts:
            avg_comp = sum(comp_non_econ_amounts) / len(comp_non_econ_amounts)
            
            # If calculated range is way off from comparables, adjust
            if non_econ_low > avg_comp * 1.5:
                non_econ_low = avg_comp * 0.8
            if non_econ_high < avg_comp * 0.7:
                non_econ_high = avg_comp * 1.2
    
    # Cap at policy limits if applicable
    if input_data.policy_limits:
        max_available = input_data.policy_limits - economic
        non_econ_high = min(non_econ_high, max_available)
    
    return {
        "low": non_econ_low,
        "high": non_econ_high,
        "multiplier_low": base_low,
        "multiplier_high": base_high
    }

@activity.defn
async def generate_valuation_ranges(
    economic_damages: float,
    non_economic_range: dict,
    input_data: PersonalInjuryInput
) -> dict:
    """
    Generate settlement ranges and demand amount
    """
    
    total_low = economic_damages + non_economic_range["low"]
    total_high = economic_damages + non_economic_range["high"]
    
    # Likely settlement (midpoint, slightly adjusted)
    likely_settlement = (total_low + total_high) / 2
    
    # Adjust down 20% for negotiation reality
    settlement_range_low = total_low * 0.8
    settlement_range_high = total_high * 0.9
    
    # Initial demand should be higher to allow negotiation room
    recommended_demand = total_high * 1.5
    
    # Cap at policy limits if known
    if input_data.policy_limits:
        if recommended_demand > input_data.policy_limits * 0.95:
            # Don't demand more than policy (leaves no room for attorney fees/costs)
            recommended_demand = input_data.policy_limits * 0.95
        
        settlement_range_high = min(settlement_range_high, input_data.policy_limits * 0.95)
        likely_settlement = min(likely_settlement, input_data.policy_limits * 0.85)
    
    # Determine confidence based on number of good comparables
    confidence = "high"  # Simplified for now
    
    return {
        "settlement_range_low": round(settlement_range_low, 2),
        "settlement_range_high": round(settlement_range_high, 2),
        "likely_settlement": round(likely_settlement, 2),
        "recommended_demand": round(recommended_demand, 2),
        "economic_damages": round(economic_damages, 2),
        "non_economic_low": round(non_economic_range["low"], 2),
        "non_economic_high": round(non_economic_range["high"], 2),
        "confidence": confidence
    }

@activity.defn
async def analyze_case_strengths_weaknesses(
    input_data: PersonalInjuryInput,
    comparables: list[dict]
) -> dict:
    """
    Identify strengths, weaknesses, and risk factors
    """
    
    strengths = []
    weaknesses = []
    risk_factors = []
    
    # Liability analysis
    if input_data.liability_strength == "clear":
        strengths.append("Clear liability (defendant fault established)")
    elif input_data.liability_strength == "strong":
        strengths.append("Strong liability showing")
    elif input_data.liability_strength == "disputed":
        weaknesses.append("Liability is disputed")
    else:
        weaknesses.append("Weak liability case")
    
    if input_data.comparative_negligence:
        weaknesses.append(f"Comparative negligence issue (plaintiff {input_data.plaintiff_fault_pct}% at fault)")
    
    # Damages analysis
    if input_data.permanent_impairment:
        strengths.append("Permanent impairment increases damages")
    
    if input_data.injury_severity in ["severe", "catastrophic"]:
        strengths.append("Significant injury supports high damages")
    
    if input_data.total_economic_damages > 50000:
        strengths.append("Substantial economic damages documented")
    
    # Evidence
    if input_data.surgery:
        strengths.append("Objective medical evidence (surgery performed)")
    
    # Likability
    if input_data.plaintiff_likability == "high":
        strengths.append("Sympathetic plaintiff")
    elif input_data.plaintiff_likability == "low":
        weaknesses.append("Plaintiff may not be sympathetic to jury")
    
    if input_data.defendant_likability == "low":
        strengths.append("Unsympathetic defendant")
    
    # Policy limits
    if input_data.policy_limits:
        if input_data.policy_limits < input_data.total_economic_damages * 3:
            risk_factors.append(
                f"Policy limits (${input_data.policy_limits:,.0f}) may cap recovery"
            )
    
    # Venue analysis
    # (Would need venue data - for now, simplified)
    strengths.append(f"Case filed in {input_data.county} (check verdict history)")
    
    # Litigation costs
    estimated_costs = 10000  # Simplified
    risk_factors.append(f"Estimated litigation costs: ${estimated_costs:,.0f}")
    
    return {
        "strengths": strengths,
        "weaknesses": weaknesses,
        "risk_factors": risk_factors
    }

@activity.defn
async def generate_strategic_recommendations(
    input_data: PersonalInjuryInput,
    valuation: dict,
    swot: dict,
    comparables: list[dict]
) -> dict:
    """
    Use vLLM to generate strategic recommendations
    """
    from services.vllm_client import VLLMClient
    
    # Format context for vLLM
    context = f"""
CASE VALUATION ANALYSIS:

Economic Damages: ${valuation['economic_damages']:,.0f}
Settlement Range: ${valuation['settlement_range_low']:,.0f} - ${valuation['settlement_range_high']:,.0f}
Likely Settlement: ${valuation['likely_settlement']:,.0f}
Recommended Demand: ${valuation['recommended_demand']:,.0f}

STRENGTHS:
{chr(10).join('- ' + s for s in swot['strengths'])}

WEAKNESSES:
{chr(10).join('- ' + w for w in swot['weaknesses'])}

RISK FACTORS:
{chr(10).join('- ' + r for r in swot['risk_factors'])}

TOP COMPARABLE CASES:
{chr(10).join(f"- {c['case_name']} ({c['year']}): ${c['amount']:,.0f} ({c['similarity_percentage']}% similar)" for c in comparables[:5])}

CASE DETAILS:
- Injury: {input_data.injury_severity} {', '.join(input_data.injury_types)}
- Liability: {input_data.liability_strength}
- County: {input_data.county}
- Defendant: {input_data.defendant_type}
- Policy Limits: ${input_data.policy_limits:,.0f if input_data.policy_limits else 'Unknown'}
"""
    
    prompt = f"""You are an experienced Ohio personal injury attorney providing strategic advice to a colleague.

Based on the case analysis above, provide:

1. SETTLEMENT STRATEGY: Specific negotiation approach and timeline
2. NEGOTIATION LEVERAGE: Key points to emphasize with insurance adjuster
3. TIMING RECOMMENDATIONS: When to make demand, when to file suit, optimal mediation timing
4. CLIENT ADVICE: Concise explanation of case value and strategy (2-3 sentences)

Focus on practical, actionable advice based on Ohio law and the comparable verdicts.

{context}
"""
    
    client = VLLMClient()
    response = await client.generate(
        system_prompt="You are an experienced Ohio personal injury attorney.",
        user_prompt=prompt,
        max_tokens=1500,
        temperature=0.7
    )
    
    # Parse response into structured format
    # (Simplified - would use more sophisticated parsing)
    return {
        "settlement_strategy": extract_section(response, "SETTLEMENT STRATEGY"),
        "negotiation_leverage": extract_section(response, "NEGOTIATION LEVERAGE"),
        "timing": extract_section(response, "TIMING RECOMMENDATIONS"),
        "client_advice": extract_section(response, "CLIENT ADVICE")
    }

def extract_section(text: str, header: str) -> str:
    """Extract section from vLLM response"""
    # Simplified extraction logic
    lines = text.split('\n')
    in_section = False
    section_lines = []
    
    for line in lines:
        if header in line:
            in_section = True
            continue
        elif in_section and line.strip() and any(h in line for h in ["STRATEGY", "LEVERAGE", "TIMING", "ADVICE"]):
            break
        elif in_section:
            section_lines.append(line)
    
    return '\n'.join(section_lines).strip()
```

---

## Feature 2: Legal Research with Argument Builder

### Overview

**Purpose:** Enhance existing research to draft legal arguments with inline citations

**Current State:** Research returns list of cases, user reads them, drafts argument manually

**Enhanced State:** Research returns cases AND drafts argument paragraph with citations

**Frequency:** Used constantly (multiple times per brief, motion, memo)

---

### User Interface Enhancement

**Route:** `/research` (enhance existing page)

#### Add "Build Argument" Button

```typescript
// After user performs research and gets results:

┌─────────────────────────────────────────────────────────┐
│ SEARCH RESULTS: "theft consent defense ohio"            │
│ 47 results found                                         │
└─────────────────────────────────────────────────────────┘

[Case 1] State v. Smith, 123 Ohio St.3d 456 (2023)
  Snippet: "Consent is a complete defense to theft..."
  [View Full Case] [Add to Research]

[Case 2] State v. Johnson, 145 Ohio App.3d 789 (2022)
  ...

┌─────────────────────────────────────────────────────────┐
│ 💡 BUILD ARGUMENT FROM THESE CASES                      │
│                                                          │
│ Selected Cases: [3 cases selected]                      │
│                                                          │
│ What argument are you making?                            │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ [Textarea]                                          │ │
│ │ "The defendant had consent to take the vehicle     │ │
│ │  because the owner gave him the keys..."           │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ Argument Type: [Factual Background ▼]                   │
│   - Factual Background                                   │
│   - Legal Standard                                       │
│   - Application to Facts                                 │
│   - Counter to Opponent's Argument                       │
│                                                          │
│ Tone: (● Balanced ○ Aggressive ○ Cautious)             │
│                                                          │
│ [Generate Argument Paragraph]                            │
└─────────────────────────────────────────────────────────┘
```

#### Output Display

```typescript
┌─────────────────────────────────────────────────────────┐
│ GENERATED ARGUMENT                                       │
└─────────────────────────────────────────────────────────┘

Under Ohio law, consent is a complete defense to theft 
charges. [State v. Smith, 123 Ohio St.3d 456, 459 (2023)]. 
The Ohio Supreme Court has consistently held that when an 
owner voluntarily provides another person with access to 
property, that consent negates the element of unlawful 
taking required for theft. [State v. Johnson, 145 Ohio 
App.3d 789, 792 (2022)].

In this case, the evidence demonstrates that Ms. Williams, 
the vehicle owner, voluntarily gave Mr. Martinez the keys 
to her car on March 15, 2024. Text messages between the 
parties show Ms. Williams stating "you can take the car 
today." This factual showing satisfies the consent defense 
because the owner's voluntary transfer of possession 
negates any unlawful taking. [State v. Thompson, 156 Ohio 
St.3d 234, 237 (2021)] ("Consent may be express or implied 
through the owner's voluntary actions").

The State cannot overcome this defense merely by showing 
that the parties later had a dispute. Ohio courts have 
repeatedly held that post-hoc disagreements do not 
retroactively transform lawful possession into theft. 
[State v. Davis, 134 Ohio App.3d 567, 570 (2023)].

┌─────────────────────────────────────────────────────────┐
│ [Copy to Clipboard] [Edit] [Add to Brief] [Export]     │
└─────────────────────────────────────────────────────────┘

Citations Used (3):
• State v. Smith, 123 Ohio St.3d 456 (2023) - [View Case]
• State v. Johnson, 145 Ohio App.3d 789 (2022) - [View Case]
• State v. Thompson, 156 Ohio St.3d 234 (2021) - [View Case]
```

---

### Data Models

```python
# models/arguments.py

class ArgumentType(str, enum.Enum):
    FACTUAL_BACKGROUND = "factual_background"
    LEGAL_STANDARD = "legal_standard"
    APPLICATION_TO_FACTS = "application_to_facts"
    COUNTER_ARGUMENT = "counter_argument"
    STATUTORY_INTERPRETATION = "statutory_interpretation"

class ArgumentTone(str, enum.Enum):
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"
    CAUTIOUS = "cautious"

class GeneratedArgument(Base):
    __tablename__ = "generated_arguments"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[str] = mapped_column(String(255), index=True)
    user_id: Mapped[str] = mapped_column(String(255), index=True)
    case_id: Mapped[Optional[int]] = mapped_column(ForeignKey("cases.id"), nullable=True)
    
    # Research context
    research_session_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source_cases: Mapped[list[str]] = mapped_column(JSON)  # List of case citations used
    
    # Input
    argument_prompt: Mapped[str] = mapped_column(Text)  # What user asked for
    argument_type: Mapped[ArgumentType]
    tone: Mapped[ArgumentTone]
    
    # Output
    generated_text: Mapped[str] = mapped_column(Text)
    citations: Mapped[list[dict]] = mapped_column(JSON)
    
    # Workflow
    workflow_id: Mapped[str] = mapped_column(String(255), unique=True)
    
    # User modifications
    edited_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    was_edited: Mapped[bool] = mapped_column(default=False)
    
    # Usage tracking
    copied_to_clipboard: Mapped[bool] = mapped_column(default=False)
    exported: Mapped[bool] = mapped_column(default=False)
    
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
```

### Pydantic Models

```python
# models/argument_inputs.py

class ArgumentBuilderInput(BaseModel):
    # Source cases (from research results)
    source_case_ids: list[str] = Field(..., min_items=1, max_items=10)
    
    # Or if coming from arbitrary citations:
    source_case_citations: Optional[list[str]] = None
    
    # User's description of what they're arguing
    argument_prompt: str = Field(..., min_length=20, max_length=2000)
    
    # Type of argument
    argument_type: Literal[
        "factual_background",
        "legal_standard",
        "application_to_facts",
        "counter_argument",
        "statutory_interpretation"
    ]
    
    # Tone
    tone: Literal["balanced", "aggressive", "cautious"] = "balanced"
    
    # Context (optional but helpful)
    case_context: Optional[str] = None  # Background facts
    opposing_argument: Optional[str] = None  # What they're countering
    
    # Metadata
    org_id: str
    user_id: str
    case_id: Optional[int] = None
    research_session_id: Optional[str] = None
```

---

### Temporal Workflow

```python
# workflows/research/argument_builder.py

@workflow.defn
class ArgumentBuilderWorkflow:
    """
    Generate legal argument from research results
    
    Steps:
    1. Fetch full case content from LMDB
    2. Extract relevant legal principles from each case
    3. Generate argument paragraph using vLLM
    4. Insert inline citations in proper format
    5. Validate citations exist
    6. Store result
    """
    
    @workflow.run
    async def run(self, input_data: ArgumentBuilderInput) -> dict:
        workflow_id = workflow.info().workflow_id
        
        # Step 1: Fetch full case details from LMDB
        case_details = await workflow.execute_activity(
            fetch_case_details_from_lmdb,
            args=[input_data.source_case_ids],
            start_to_close_timeout=timedelta(minutes=1),
            retry_policy=RetryPolicy(maximum_attempts=2)
        )
        
        # Step 2: Extract relevant holdings/principles
        case_principles = await workflow.execute_activity(
            extract_legal_principles,
            args=[case_details, input_data.argument_prompt],
            start_to_close_timeout=timedelta(minutes=2)
        )
        
        # Step 3: Generate argument using vLLM
        generated_argument = await workflow.execute_activity(
            generate_argument_with_citations,
            args=[input_data, case_details, case_principles],
            start_to_close_timeout=timedelta(minutes=3),
            retry_policy=RetryPolicy(maximum_attempts=2)
        )
        
        # Step 4: Extract and format citations
        formatted_argument = await workflow.execute_activity(
            format_argument_with_bluebook_citations,
            args=[generated_argument, case_details],
            start_to_close_timeout=timedelta(seconds=30)
        )
        
        # Step 5: Store in database
        argument_id = await workflow.execute_activity(
            store_generated_argument,
            args=[input_data, formatted_argument, workflow_id],
            start_to_close_timeout=timedelta(seconds=30)
        )
        
        return {
            "argument_id": argument_id,
            "workflow_id": workflow_id,
            "generated_text": formatted_argument["text"],
            "citations": formatted_argument["citations"],
            "status": "completed"
        }

@activity.defn
async def fetch_case_details_from_lmdb(case_ids: list[str]) -> list[dict]:
    """Fetch full case content from LMDB"""
    from services.lmdb_client import LMDBClient
    
    client = LMDBClient()
    cases = []
    
    for case_id in case_ids:
        case_data = await client.get(key=case_id)
        if case_data:
            cases.append({
                "case_id": case_id,
                "case_name": case_data.get("case_name"),
                "citation": case_data.get("citation"),
                "court": case_data.get("court"),
                "year": case_data.get("year"),
                "full_text": case_data.get("full_text"),
                "headnotes": case_data.get("headnotes", []),
                "holdings": case_data.get("holdings", [])
            })
    
    return cases

@activity.defn
async def extract_legal_principles(
    cases: list[dict],
    user_prompt: str
) -> list[dict]:
    """
    Extract the specific legal principles relevant to user's argument
    Uses vLLM to understand what's relevant from each case
    """
    from services.vllm_client import VLLMClient
    
    client = VLLMClient()
    principles = []
    
    for case in cases:
        # Extract relevant principle from this case
        extraction_prompt = f"""From this Ohio case, extract the specific legal principle relevant to: "{user_prompt}"

Case: {case['case_name']}, {case['citation']}

Holdings:
{chr(10).join(case.get('holdings', []))}

Relevant excerpt from opinion:
{case.get('full_text', '')[:3000]}  # First 3000 chars

Extract:
1. The legal principle (rule of law)
2. The specific quote that states this principle (with exact text)
3. The pincite (page number where this appears)

Respond in this format:
PRINCIPLE: [one sentence statement of legal principle]
QUOTE: "[exact quote from opinion]"
PAGE: [page number]
"""
        
        response = await client.generate(
            system_prompt="You are a legal research assistant extracting principles from cases.",
            user_prompt=extraction_prompt,
            max_tokens=500,
            temperature=0.3  # Lower temp for extraction accuracy
        )
        
        # Parse response
        principle_data = parse_principle_extraction(response, case)
        principles.append(principle_data)
    
    return principles

@activity.defn
async def generate_argument_with_citations(
    input_data: ArgumentBuilderInput,
    cases: list[dict],
    principles: list[dict]
) -> str:
    """
    Generate argument paragraph using vLLM with inline citations
    """
    from services.vllm_client import VLLMClient
    
    # Format principles for context
    principles_context = "\n\n".join([
        f"{p['case_name']}, {p['citation']}:\n"
        f"Principle: {p['principle']}\n"
        f"Quote: {p['quote']}\n"
        f"Pincite: {p['pincite']}"
        for p in principles
    ])
    
    # Tone-specific instructions
    tone_instructions = {
        "balanced": "Use measured, objective language. Present the law clearly without overstatement.",
        "aggressive": "Use forceful, confident language. Emphasize the strength of your position.",
        "cautious": "Qualify statements appropriately. Acknowledge counterarguments."
    }
    
    # Argument type-specific instructions
    type_instructions = {
        "factual_background": "Present facts objectively, weaving in legal context where relevant.",
        "legal_standard": "Clearly state the governing legal rule. Use authoritative citations.",
        "application_to_facts": "Apply the legal standard to the specific facts. Show how the rule leads to your conclusion.",
        "counter_argument": "Address and distinguish the opposing argument. Explain why it fails.",
        "statutory_interpretation": "Analyze statutory language. Apply canons of construction with case support."
    }
    
    system_prompt = f"""You are an experienced Ohio attorney drafting a persuasive legal argument.

RULES:
1. Use Ohio legal citation format: [Case Name, Citation, Pincite]
2. Every legal principle MUST be supported by a citation
3. Use the principles provided - don't make up case law
4. Write in {input_data.tone} tone: {tone_instructions[input_data.tone]}
5. This is a {input_data.argument_type} argument: {type_instructions[input_data.argument_type]}
6. Write 2-4 paragraphs (200-400 words)
7. Include inline citations after each legal statement: [Case Name, Citation, Pincite]
8. Use proper legal writing style (clear, concise, persuasive)
"""
    
    user_prompt = f"""Draft a legal argument for the following:

USER'S ARGUMENT GOAL:
{input_data.argument_prompt}

AVAILABLE CASE LAW:
{principles_context}

{f"CASE CONTEXT: {input_data.case_context}" if input_data.case_context else ""}

{f"OPPOSING ARGUMENT TO COUNTER: {input_data.opposing_argument}" if input_data.opposing_argument else ""}

Draft the argument now with inline citations.
"""
    
    client = VLLMClient()
    response = await client.generate(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=1200,
        temperature=0.7
    )
    
    return response

@activity.defn
async def format_argument_with_bluebook_citations(
    argument_text: str,
    cases: list[dict]
) -> dict:
    """
    Format citations to proper Bluebook/Ohio format
    Extract citations for separate display
    """
    import re
    
    # Pattern: [Case Name, Citation] or [Case Name, Citation, Pincite]
    citation_pattern = r'\[(.*?),\s*(.*?)(?:,\s*(\d+))?\]'
    
    citations = []
    matches = re.finditer(citation_pattern, argument_text)
    
    for match in matches:
        case_name = match.group(1)
        citation = match.group(2)
        pincite = match.group(3)
        
        # Find full case details
        case_details = next(
            (c for c in cases if citation in c.get('citation', '')),
            None
        )
        
        citations.append({
            "case_name": case_name,
            "citation": citation,
            "pincite": pincite,
            "case_id": case_details.get("case_id") if case_details else None,
            "year": case_details.get("year") if case_details else None
        })
    
    return {
        "text": argument_text,
        "citations": citations
    }
```

---

## Feature 3: Plea Deal / Settlement Analyzer

### Overview

**Purpose:** Help attorneys evaluate whether client should accept plea deal (criminal) or settlement offer (civil)

**User Story:**
"The prosecutor offered my client 3 years in prison if he pleads guilty to aggravated assault. Should he take it, or should we go to trial?"

**Frequency:** Used in 90%+ of criminal cases, 70%+ of civil cases

**Value:** Determines life-altering outcome for client

---

### User Interface

**Route:** `/analysis/plea-deal` (criminal) or `/analysis/settlement-offer` (civil)

#### Criminal Plea Deal Input

```typescript
┌─────────────────────────────────────────────────────────┐
│ EVALUATE PLEA OFFER                                      │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ ORIGINAL CHARGES                                         │
│                                                          │
│ [☑] Aggravated Assault (F2) - ORC 2903.12              │
│ [☑] Having Weapon Under Disability (F3) - ORC 2923.13  │
│ [☐] Add more charges...                                  │
│                                                          │
│ Maximum Exposure if Convicted on All:                    │
│ • Prison: 3-11 years (F2) + 1-5 years (F3) = 4-16 years│
│ • Fines: Up to $30,000                                   │
│ • Post-Release Control: Up to 5 years                   │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ PLEA OFFER TERMS                                         │
│                                                          │
│ Plead Guilty To: [Assault (F3) ▼]                      │
│                                                          │
│ Sentence:                                                │
│   Prison: [3 years]                                      │
│   OR: [○ Prison ● Community Control]                    │
│         Duration: [3 years]                              │
│         Conditions: [Textarea - "Anger management..."]   │
│                                                          │
│ Dropped Charges:                                         │
│   [☑] Aggravated Assault (reduced to Assault)          │
│   [☑] Weapon Under Disability (dismissed)               │
│                                                          │
│ Other Terms:                                             │
│   [Textarea - "Pay restitution $5,000, No contact..."]  │
│                                                          │
│ Deadline to Accept: [Date picker]                       │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ CASE STRENGTH ASSESSMENT                                 │
│                                                          │
│ Prosecution's Evidence Strength: [Strong ▼]             │
│   - Overwhelming (conviction highly likely)              │
│   - Strong (conviction likely)                           │
│   - Moderate (could go either way)                       │
│   - Weak (acquittal possible)                            │
│                                                          │
│ Key Evidence Against Defendant:                          │
│ [☑] Witness testimony                                    │
│ [☑] Video/photo evidence                                 │
│ [☑] Physical evidence                                    │
│ [☑] Defendant's statements                               │
│ [☐] Expert testimony                                     │
│                                                          │
│ Defense Strengths:                                       │
│ [☑] Self-defense claim                                   │
│ [☐] Alibi                                                │
│ [☑] Credibility issues with witnesses                    │
│ [☐] Constitutional violations (search/seizure)           │
│                                                          │
│ Evidence Details: [Textarea]                             │
│ "Multiple witnesses saw the fight. However, our client  │
│  has two witnesses who say the victim started it..."     │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ DEFENDANT BACKGROUND                                     │
│                                                          │
│ Criminal History: [Some prior convictions ▼]            │
│   - No record                                            │
│   - Juvenile record only                                 │
│   - Misdemeanor(s) only                                  │
│   - Some prior convictions                               │
│   - Extensive record                                     │
│                                                          │
│ If prior record, describe: [Textarea]                    │
│ "One prior F4 theft from 2019 (completed probation)"    │
│                                                          │
│ Personal Circumstances:                                  │
│ Age: [34]                                                │
│ Employment: [Employed full-time ▼]                      │
│ Family: [Has dependents ▼]                              │
│ Health: [No major issues ▼]                             │
│                                                          │
│ Mitigating Factors: [Textarea]                          │
│ "Single father of two young children, employed as       │
│  electrician for 8 years, no violence in record..."     │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ TRIAL CONSIDERATIONS                                     │
│                                                          │
│ County: [Franklin County ▼]                             │
│ Judge: [Smith ▼] (if assigned)                          │
│                                                          │
│ Expected Trial Length: [3-5 days ▼]                     │
│ Defense Costs if Trial: $[15,000]                       │
│                                                          │
│ Client's Risk Tolerance: (○ Risk Averse ● Moderate ○ Willing to Risk) │
│                                                          │
│ Client's Priorities:                                     │
│ [☑] Avoid prison time                                    │
│ [☑] Maintain employment                                  │
│ [☑] Stay with family                                     │
│ [☐] Clear name/vindication                              │
│                                                          │
│ Additional Context: [Textarea - optional]                │
└─────────────────────────────────────────────────────────┘

[Analyze Plea Offer]
```

---

### Output Display

```typescript
┌─────────────────────────────────────────────────────────┐
│ PLEA DEAL ANALYSIS REPORT                                │
│ State v. Johnson | Franklin County                       │
│ Generated: Nov 10, 2025                                  │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ 🎯 RECOMMENDATION: ACCEPT PLEA OFFER                    │
│                                                          │
│ Confidence: HIGH                                         │
│                                                          │
│ This plea offer is favorable given the case             │
│ circumstances and should be seriously considered.        │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ 📊 RISK ANALYSIS                                        │
│                                                          │
│ TRIAL OUTCOME PROBABILITIES:                             │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ Convicted on All Charges:     45% ████████████          │
│ Convicted on Some Charges:    35% ███████               │
│ Acquitted on All Charges:     20% ████                  │
│                                                          │
│ EXPECTED SENTENCE IF CONVICTED AT TRIAL:                 │
│ Most Likely: 5-7 years prison                           │
│ Range: 3-11 years (based on convictions)                │
│                                                          │
│ PLEA OFFER SENTENCE:                                     │
│ 3 years community control (probation)                    │
│ → AVOIDS PRISON ENTIRELY                                │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ ⚖️ COMPARATIVE ANALYSIS                                 │
│                                                          │
│                    PLEA OFFER    vs    GO TO TRIAL      │
│                    ─────────────────────────────────────│
│ Prison Time:       0 years             Likely: 5-7 yrs  │
│                    (probation)         Range: 0-11 yrs  │
│                                                          │
│ Conviction:        Guaranteed          45-80% chance    │
│                    (F3 Assault)        (F2-F3)          │
│                                                          │
│ Cost:              $2,000              $15,000+         │
│                    (misc fees)         (trial costs)    │
│                                                          │
│ Time to Resolve:   Immediate           6-9 months       │
│                                                          │
│ Certainty:         100% known          Uncertain        │
│                    outcome             outcome          │
│                                                          │
│ Impact on Family:  Stays home          High risk        │
│                    (probation)         prison → loss    │
│                                        of job, housing  │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ 📈 SENTENCING CONTEXT (Franklin County)                │
│                                                          │
│ For F3 Assault with similar facts:                      │
│                                                          │
│ First Offenders:                                         │
│ • 60% receive community control                         │
│ • 30% receive short prison (1-2 years)                  │
│ • 10% receive longer prison (3+ years)                  │
│                                                          │
│ With Prior Record (like client):                        │
│ • 35% receive community control                         │
│ • 45% receive 2-4 years prison                          │
│ • 20% receive 4+ years prison                           │
│                                                          │
│ Aggravating Factor (weapon involved):                    │
│ Average sentence: 4.2 years prison                       │
│                                                          │
│ COMPARABLE CASES IN FRANKLIN COUNTY:                     │
│                                                          │
│ [Case Card 1]                                            │
│ State v. Williams (2024)                                 │
│ Facts: Assault with weapon, prior F4, self-defense claim│
│ Verdict: Guilty F3 Assault                              │
│ Sentence: 3 years prison                                 │
│ Similarity: 78% ⭐⭐⭐⭐                                  │
│                                                          │
│ [Case Card 2]                                            │
│ State v. Martinez (2023)                                 │
│ Facts: Similar facts, strong self-defense               │
│ Verdict: Acquitted                                       │
│ Similarity: 65% ⭐⭐⭐                                   │
│                                                          │
│ [Show 8 more comparable cases]                          │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ 💪 CASE STRENGTHS & WEAKNESSES                          │
│                                                          │
│ REASONS TO ACCEPT PLEA:                                  │
│ ✓ AVOIDS PRISON: Plea offers probation, trial risks     │
│   3-11 years prison                                      │
│ ✓ CERTAINTY: Known outcome vs. 45% conviction risk     │
│ ✓ COST: Saves $13,000 in trial costs                   │
│ ✓ EMPLOYMENT: Can keep job on probation                │
│ ✓ FAMILY: Stays with children                          │
│ ✓ REDUCED CHARGE: F3 vs F2 (better for record)         │
│                                                          │
│ REASONS TO GO TO TRIAL:                                  │
│ • Self-defense claim has merit (witnesses support)      │
│ • 20% chance of complete acquittal                      │
│ • Victim credibility issues (inconsistent statements)   │
│ • Prior record is relatively minor (one F4)             │
│                                                          │
│ PROSECUTION STRENGTHS:                                   │
│ ⚠ Multiple neutral witnesses saw incident               │
│ ⚠ Physical evidence (weapon recovered)                  │
│ ⚠ Video shows defendant striking victim                 │
│ ⚠ Victim's injuries documented (medical records)        │
│ ⚠ Prior conviction (even if minor) hurts at sentencing │
│                                                          │
│ DEFENSE WEAKNESSES:                                      │
│ ⚠ Self-defense may not justify level of force used     │
│ ⚠ Defendant's version contradicted by some witnesses   │
│ ⚠ Weapon involvement makes self-defense harder sell    │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ 🎲 RISK-ADJUSTED ANALYSIS                               │
│                                                          │
│ EXPECTED VALUE CALCULATION:                              │
│                                                          │
│ PLEA OFFER:                                              │
│ Guaranteed outcome: 0 years prison + F3 conviction      │
│ Value: Certainty of staying home with family            │
│                                                          │
│ GO TO TRIAL:                                             │
│ 20% chance: Acquittal (0 years prison, no conviction)  │
│ 35% chance: F3 only (2-4 years likely)                  │
│ 45% chance: F2+F3 (5-11 years likely)                   │
│                                                          │
│ Expected Sentence if Trial: 4.7 years prison            │
│ 80% chance of WORSE outcome than plea offer             │
│                                                          │
│ RISK ASSESSMENT FOR YOUR CLIENT:                         │
│ Client Priority: Avoid prison, stay with kids          │
│ Risk Tolerance: Moderate                                 │
│ → Plea offer aligns with client's priorities           │
│ → 4.7 years expected at trial vs 0 years on plea       │
│ → Math strongly favors accepting plea                   │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ 💼 STRATEGIC RECOMMENDATIONS                            │
│                                                          │
│ IMMEDIATE RECOMMENDATION:                                │
│ Accept the plea offer.                                   │
│                                                          │
│ RATIONALE:                                               │
│ 1. The plea avoids prison entirely (probation only)     │
│ 2. Trial carries 80% risk of prison time (avg 4.7 yrs) │
│ 3. Your client's priority is staying with his children  │
│ 4. The prosecution's evidence is strong enough that     │
│    gambling on trial isn't justified                     │
│ 5. Even with the self-defense claim, video evidence     │
│    and multiple witnesses create substantial risk       │
│                                                          │
│ NEGOTIATION OPPORTUNITY:                                 │
│ The offer is already favorable, but you could try:      │
│ • Request shorter probation term (2 years vs 3)         │
│ • Negotiate lower restitution amount                     │
│ • Request reduced reporting requirements                 │
│                                                          │
│ COUNSEL TO CLIENT:                                       │
│ "The prosecutor's offer lets you avoid prison and stay  │
│  with your kids. If we go to trial, you're facing a     │
│  likely sentence of 5-7 years in prison based on how    │
│  similar cases have gone in Franklin County. While we   │
│  have a self-defense argument, the evidence against you  │
│  is strong enough that I cannot in good conscience       │
│  recommend rolling the dice at trial. This is a good    │
│  offer given the circumstances."                         │
│                                                          │
│ ALTERNATIVE IF CLIENT INSISTS ON TRIAL:                  │
│ If client absolutely wants to go to trial despite risks: │
│ • Emphasize self-defense to jury                        │
│ • Challenge victim credibility aggressively              │
│ • Humanize defendant (father, employed, minimal record) │
│ • Request jury instruction on lesser included offenses  │
│                                                          │
│ TIMING:                                                  │
│ • Deadline: [Date from input]                           │
│ • Recommend: Discuss with client within 48 hours        │
│ • If accepting: Confirm with prosecutor in writing      │
│ • If declining: Begin trial prep immediately            │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ 📄 EXPORT OPTIONS                                       │
│                                                          │
│ [Export Analysis] [Generate Client Memo]                │
│ [Add to Case File] [Email to Client]                    │
└─────────────────────────────────────────────────────────┘
```

---

### Data Models

```python
# models/plea_analysis.py

class PleaAnalysisRecommendation(str, enum.Enum):
    ACCEPT = "accept"
    NEGOTIATE = "negotiate"
    REJECT = "reject"

class PleaAnalysis(Base):
    __tablename__ = "plea_analyses"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[str] = mapped_column(String(255), index=True)
    user_id: Mapped[str] = mapped_column(String(255), index=True)
    case_id: Mapped[Optional[int]] = mapped_column(ForeignKey("cases.id"), nullable=True)
    
    # Original charges
    original_charges: Mapped[list[dict]] = mapped_column(JSON)
    maximum_exposure: Mapped[dict] = mapped_column(JSON)
    
    # Plea offer terms
    plea_offer: Mapped[dict] = mapped_column(JSON)
    
    # Case strength assessment
    evidence_strength: Mapped[str] = mapped_column(String(50))
    prosecution_strengths: Mapped[list[str]] = mapped_column(JSON)
    defense_strengths: Mapped[list[str]] = mapped_column(JSON)
    
    # Defendant background
    defendant_background: Mapped[dict] = mapped_column(JSON)
    
    # Analysis results
    recommendation: Mapped[PleaAnalysisRecommendation]
    confidence: Mapped[str] = mapped_column(String(20))  # "high", "medium", "low"
    
    # Risk assessment
    conviction_probability: Mapped[float]  # 0.0 to 1.0
    expected_sentence_if_trial: Mapped[dict] = mapped_column(JSON)
    
    # Comparable cases
    comparable_cases: Mapped[list[dict]] = mapped_column(JSON)
    
    # Strategic analysis
    reasons_to_accept: Mapped[list[str]] = mapped_column(JSON)
    reasons_to_reject: Mapped[list[str]] = mapped_column(JSON)
    risk_analysis: Mapped[dict] = mapped_column(JSON)
    recommendations: Mapped[dict] = mapped_column(JSON)
    
    # Workflow
    workflow_id: Mapped[str] = mapped_column(String(255), unique=True)
    
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

class SentencingData(Base):
    """Database of Ohio sentencing outcomes for probability calculations"""
    __tablename__ = "sentencing_data"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Case identification
    case_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    court: Mapped[str] = mapped_column(String(200))
    county: Mapped[str] = mapped_column(String(100), index=True)
    year: Mapped[int] = mapped_column(index=True)
    
    # Charges
    conviction_charge: Mapped[str] = mapped_column(String(200), index=True)
    offense_level: Mapped[str] = mapped_column(String(20))  # "F1", "F2", etc.
    
    # Sentence
    prison_months: Mapped[int]  # 0 if community control
    community_control: Mapped[bool]
    probation_months: Mapped[Optional[int]] = mapped_column(nullable=True)
    fine_amount: Mapped[Optional[float]] = mapped_column(nullable=True)
    
    # Defendant factors
    had_prior_record: Mapped[bool]
    prior_felony_count: Mapped[int] = mapped_column(default=0)
    defendant_age: Mapped[Optional[int]] = mapped_column(nullable=True)
    
    # Case factors
    had_weapon: Mapped[bool] = mapped_column(default=False)
    victim_injury_severity: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    plea_or_trial: Mapped[str] = mapped_column(String(20))  # "plea" or "trial"
    
    # Source
    source: Mapped[str] = mapped_column(String(200))
    
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_sentencing_charge_county', 'conviction_charge', 'county'),
    )
```

### Pydantic Input Models

```python
# models/plea_inputs.py

class ChargeInput(BaseModel):
    statute: str  # e.g., "ORC 2903.12"
    charge_name: str  # e.g., "Aggravated Assault"
    offense_level: str  # "F1", "F2", "F3", "M1", etc.
    max_prison_years: Optional[float] = None
    max_fine: Optional[float] = None

class PleaOfferInput(BaseModel):
    plead_guilty_to: list[ChargeInput]  # Charges in plea
    dropped_charges: list[str]  # Charges dismissed
    
    # Sentence terms
    prison_years: Optional[float] = None
    community_control_years: Optional[float] = None
    community_control_conditions: Optional[str] = None
    
    fine: Optional[float] = None
    restitution: Optional[float] = None
    other_terms: Optional[str] = None
    
    deadline: Optional[date] = None

class PleaDealAnalysisInput(BaseModel):
    # Original charges
    original_charges: list[ChargeInput] = Field(..., min_items=1)
    
    # Plea offer
    plea_offer: PleaOfferInput
    
    # Case strength
    evidence_strength: Literal["overwhelming", "strong", "moderate", "weak"]
    
    prosecution_evidence: list[str]  # What they have
    defense_strengths: list[str]  # What we have
    
    evidence_details: str = Field(..., min_length=50)
    
    # Defendant background
    criminal_history: Literal[
        "no_record",
        "juvenile_only",
        "misdemeanor_only",
        "some_prior_convictions",
        "extensive_record"
    ]
    criminal_history_details: Optional[str] = None
    
    defendant_age: int = Field(..., ge=18, le=100)
    employment_status: Literal["employed_full_time", "employed_part_time", "unemployed", "student", "disabled"]
    has_dependents: bool
    health_issues: Optional[str] = None
    mitigating_factors: Optional[str] = None
    
    # Trial considerations
    county: str
    judge: Optional[str] = None
    trial_cost_estimate: float
    
    client_risk_tolerance: Literal["risk_averse", "moderate", "willing_to_risk"]
    client_priorities: list[str]  # ["avoid_prison", "maintain_employment", etc.]
    
    additional_context: Optional[str] = None
    
    # Metadata
    org_id: str
    user_id: str
    case_id: Optional[int] = None
```

---

### Temporal Workflow

```python
# workflows/analysis/plea_deal.py

@workflow.defn
class PleaDealAnalysisWorkflow:
    """
    Analyze whether client should accept plea offer
    
    Steps:
    1. Calculate maximum exposure if convicted at trial
    2. Estimate conviction probability based on evidence
    3. Find comparable sentences in jurisdiction
    4. Calculate expected sentence if trial
    5. Compare plea offer vs expected trial outcome
    6. Identify strengths/weaknesses
    7. Generate recommendation with rationale
    """
    
    @workflow.run
    async def run(self, input_data: PleaDealAnalysisInput) -> dict:
        workflow_id = workflow.info().workflow_id
        
        # Step 1: Calculate maximum exposure
        max_exposure = await workflow.execute_activity(
            calculate_maximum_exposure,
            args=[input_data.original_charges],
            start_to_close_timeout=timedelta(seconds=30)
        )
        
        # Step 2: Find comparable sentencing outcomes
        comparable_sentences = await workflow.execute_activity(
            find_comparable_sentences,
            args=[input_data],
            start_to_close_timeout=timedelta(minutes=2)
        )
        
        # Step 3: Estimate conviction probability
        conviction_probability = await workflow.execute_activity(
            estimate_conviction_probability,
            args=[input_data, comparable_sentences],
            start_to_close_timeout=timedelta(minutes=1)
        )
        
        # Step 4: Calculate expected sentence if trial
        expected_trial_outcome = await workflow.execute_activity(
            calculate_expected_trial_outcome,
            args=[input_data, comparable_sentences, conviction_probability],
            start_to_close_timeout=timedelta(minutes=1)
        )
        
        # Step 5: Compare plea vs trial using vLLM for nuanced analysis
        comparison_analysis = await workflow.execute_activity(
            compare_plea_vs_trial,
            args=[input_data, expected_trial_outcome],
            start_to_close_timeout=timedelta(minutes=2)
        )
        
        # Step 6: Generate recommendation
        recommendation = await workflow.execute_activity(
            generate_plea_recommendation,
            args=[input_data, comparison_analysis, expected_trial_outcome],
            start_to_close_timeout=timedelta(minutes=2)
        )
        
        # Step 7: Store in database
        analysis_id = await workflow.execute_activity(
            store_plea_analysis,
            args=[input_data, recommendation, workflow_id],
            start_to_close_timeout=timedelta(seconds=30)
        )
        
        return {
            "analysis_id": analysis_id,
            "workflow_id": workflow_id,
            "recommendation": recommendation["recommendation"],
            "confidence": recommendation["confidence"],
            "conviction_probability": conviction_probability,
            "expected_trial_outcome": expected_trial_outcome,
            "comparison": comparison_analysis,
            "strategic_advice": recommendation["strategic_advice"],
            "status": "completed"
        }

@activity.defn
async def find_comparable_sentences(input_data: PleaDealAnalysisInput) -> list[dict]:
    """
    Query sentencing_data table for similar cases in same jurisdiction
    """
    from sqlalchemy import and_
    from database import get_db
    
    db = next(get_db())
    
    # Get the primary charge
    primary_charge = input_data.original_charges[0]
    
    # Query comparable sentences
    query = db.query(SentencingData).filter(
        SentencingData.conviction_charge.contains(primary_charge.charge_name),
        SentencingData.county == input_data.county,
        SentencingData.year >= 2020  # Last 5 years
    )
    
    # Filter by criminal history
    if input_data.criminal_history in ["no_record", "juvenile_only", "misdemeanor_only"]:
        query = query.filter(SentencingData.had_prior_record == False)
    else:
        query = query.filter(SentencingData.had_prior_record == True)
    
    results = query.limit(50).all()
    
    return [
        {
            "case_number": s.case_number,
            "county": s.county,
            "year": s.year,
            "conviction_charge": s.conviction_charge,
            "offense_level": s.offense_level,
            "prison_months": s.prison_months,
            "community_control": s.community_control,
            "had_prior_record": s.had_prior_record,
            "had_weapon": s.had_weapon,
            "plea_or_trial": s.plea_or_trial
        }
        for s in results
    ]

@activity.defn
async def estimate_conviction_probability(
    input_data: PleaDealAnalysisInput,
    comparables: list[dict]
) -> float:
    """
    Estimate likelihood of conviction based on evidence strength
    
    Base rates by evidence strength:
    - Overwhelming: 0.90-0.95
    - Strong: 0.70-0.85
    - Moderate: 0.50-0.65
    - Weak: 0.20-0.40
    
    Adjusted by:
    - Defense strengths
    - Jurisdiction conviction rates
    - Case complexity
    """
    
    # Base probability by evidence strength
    base_probabilities = {
        "overwhelming": 0.92,
        "strong": 0.75,
        "moderate": 0.55,
        "weak": 0.30
    }
    
    probability = base_probabilities[input_data.evidence_strength]
    
    # Adjustments
    
    # Strong defense factors reduce probability
    defense_strength_count = len(input_data.defense_strengths)
    if defense_strength_count >= 3:
        probability -= 0.15
    elif defense_strength_count >= 2:
        probability -= 0.10
    elif defense_strength_count >= 1:
        probability -= 0.05
    
    # Check jurisdiction conviction rate from comparables
    if comparables:
        trial_cases = [c for c in comparables if c["plea_or_trial"] == "trial"]
        if len(trial_cases) >= 10:
            jurisdiction_rate = len([c for c in trial_cases if c["prison_months"] > 0 or c["community_control"]]) / len(trial_cases)
            # Weight 70% base model, 30% jurisdiction data
            probability = probability * 0.7 + jurisdiction_rate * 0.3
    
    # Clamp between 0.1 and 0.95
    probability = max(0.1, min(0.95, probability))
    
    return round(probability, 2)

@activity.defn
async def calculate_expected_trial_outcome(
    input_data: PleaDealAnalysisInput,
    comparables: list[dict],
    conviction_probability: float
) -> dict:
    """
    Calculate expected sentence if case goes to trial
    """
    
    # Group sentences from comparables
    prison_sentences = [
        c["prison_months"] for c in comparables
        if c["prison_months"] > 0 and c["plea_or_trial"] == "trial"
    ]
    
    community_control_cases = [
        c for c in comparables
        if c["community_control"] and c["plea_or_trial"] == "trial"
    ]
    
    # Calculate average/median sentences
    if prison_sentences:
        avg_prison_months = sum(prison_sentences) / len(prison_sentences)
        median_prison = sorted(prison_sentences)[len(prison_sentences) // 2]
    else:
        # Fallback to statutory max * 50%
        avg_prison_months = input_data.original_charges[0].max_prison_years * 12 * 0.5
        median_prison = avg_prison_months
    
    # Adjust based on defendant factors
    if input_data.criminal_history in ["some_prior_convictions", "extensive_record"]:
        avg_prison_months *= 1.3
        median_prison *= 1.3
    
    if input_data.has_dependents and input_data.employment_status == "employed_full_time":
        avg_prison_months *= 0.85  # Mitigating factor
        median_prison *= 0.85
    
    # Calculate probabilities of different outcomes
    prob_community_control = len(community_control_cases) / max(len(comparables), 1)
    prob_prison = 1 - prob_community_control
    
    # Adjusted by overall conviction probability
    prob_community_control *= conviction_probability
    prob_prison *= conviction_probability
    prob_acquittal = 1 - conviction_probability
    
    # Expected value calculation
    expected_months = (
        prob_acquittal * 0 +
        prob_community_control * 0 +
        prob_prison * avg_prison_months
    )
    
    return {
        "conviction_probability": conviction_probability,
        "acquittal_probability": prob_acquittal,
        "community_control_probability": prob_community_control,
        "prison_probability": prob_prison,
        "expected_prison_months": round(expected_months, 1),
        "likely_prison_range": {
            "low": round(median_prison * 0.7, 1),
            "high": round(median_prison * 1.3, 1)
        },
        "most_likely_outcome": "prison" if prob_prison > 0.5 else "community_control"
    }

@activity.defn
async def generate_plea_recommendation(
    input_data: PleaDealAnalysisInput,
    comparison: dict,
    expected_trial: dict
) -> dict:
    """
    Generate final recommendation using vLLM for nuanced analysis
    """
    from services.vllm_client import VLLMClient
    
    # Extract plea offer terms
    plea_prison = input_data.plea_offer.prison_years or 0
    plea_cc = input_data.plea_offer.community_control_years or 0
    
    # Expected trial outcome
    expected_prison = expected_trial["expected_prison_months"] / 12
    
    context = f"""
PLEA OFFER ANALYSIS:

PLEA OFFER TERMS:
- Plea to: {input_data.plea_offer.plead_guilty_to[0].charge_name}
- Prison: {plea_prison} years
- Community Control: {plea_cc} years
- Dropped charges: {len(input_data.plea_offer.dropped_charges)}

EXPECTED TRIAL OUTCOME:
- Conviction Probability: {expected_trial['conviction_probability']*100:.0f}%
- Expected Prison Time: {expected_prison:.1f} years
- Prison Risk: {expected_trial['prison_probability']*100:.0f}%
- Acquittal Chance: {expected_trial['acquittal_probability']*100:.0f}%

DEFENDANT PRIORITIES:
{chr(10).join('- ' + p for p in input_data.client_priorities)}

DEFENDANT CIRCUMSTANCES:
- Age: {input_data.defendant_age}
- Employment: {input_data.employment_status}
- Dependents: {'Yes' if input_data.has_dependents else 'No'}
- Risk Tolerance: {input_data.client_risk_tolerance}

CASE STRENGTHS:
Prosecution: {input_data.evidence_strength} evidence
Defense: {len(input_data.defense_strengths)} significant strengths
"""
    
    prompt = f"""You are an experienced Ohio criminal defense attorney advising a client on a plea offer.

{context}

Provide a recommendation (ACCEPT, NEGOTIATE, or REJECT) with:
1. Clear recommendation with confidence level (high/medium/low)
2. Top 3-5 reasons supporting the recommendation
3. Risk analysis comparing plea vs trial
4. Strategic advice for attorney
5. How to counsel the client (2-3 sentences)

Be direct and practical. Consider the client's stated priorities.
"""
    
    client = VLLMClient()
    response = await client.generate(
        system_prompt="You are an experienced Ohio criminal defense attorney.",
        user_prompt=prompt,
        max_tokens=1500,
        temperature=0.7
    )
    
    # Parse response
    recommendation_data = parse_plea_recommendation_response(response)
    
    # Add quantitative comparison
    if plea_prison == 0 and expected_prison > 2:
        recommendation_data["recommendation"] = "accept"
        recommendation_data["confidence"] = "high"
    elif plea_prison > expected_prison * 1.5:
        recommendation_data["recommendation"] = "negotiate"
        recommendation_data["confidence"] = "medium"
    
    return recommendation_data
```

---

## Shared Data Models

(See individual feature sections above - models are feature-specific)

---

## API Endpoints

### BFF Routes

```python
# routes/high_value_features.py

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from temporalio.client import Client as TemporalClient
from models.evaluation_inputs import PersonalInjuryInput
from models.argument_inputs import ArgumentBuilderInput
from models.plea_inputs import PleaDealAnalysisInput
from auth import get_current_user, User

router = APIRouter(prefix="/api", tags=["high_value_features"])

# FEATURE 1: Case Evaluation

@router.post("/evaluation/case-value")
async def evaluate_case_value(
    input_data: PersonalInjuryInput,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    temporal: TemporalClient = Depends(get_temporal_client)
):
    """Generate case valuation with comparable verdicts"""
    
    if input_data.org_id != user.org_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    input_data.user_id = user.id
    
    workflow_id = f"case-eval-{user.org_id}-{generate_uuid()}"
    
    handle = await temporal.start_workflow(
        "CaseValuationWorkflow",
        input_data,
        id=workflow_id,
        task_queue="evaluation-queue"
    )
    
    return {
        "workflow_id": workflow_id,
        "status": "generating",
        "message": "Case valuation started"
    }

@router.get("/evaluation/status/{workflow_id}")
async def get_evaluation_status(
    workflow_id: str,
    user: User = Depends(get_current_user),
    temporal: TemporalClient = Depends(get_temporal_client)
):
    """Check status of case evaluation"""
    handle = temporal.get_workflow_handle(workflow_id)
    
    try:
        result = await handle.result()
        return {
            "status": "completed",
            "evaluation_id": result["evaluation_id"],
            "valuation": result["valuation"],
            "comparable_cases": result["comparable_cases"],
            "swot_analysis": result["swot_analysis"],
            "recommendations": result["recommendations"]
        }
    except:
        return {
            "status": "generating",
            "workflow_id": workflow_id
        }

@router.get("/evaluation/{evaluation_id}")
async def get_evaluation(
    evaluation_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve completed evaluation"""
    eval_record = db.query(CaseEvaluation).filter(
        CaseEvaluation.id == evaluation_id,
        CaseEvaluation.org_id == user.org_id
    ).first()
    
    if not eval_record:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    return {
        "id": eval_record.id,
        "case_name": eval_record.case_name,
        "valuation": {
            "settlement_range_low": eval_record.settlement_range_low,
            "settlement_range_high": eval_record.settlement_range_high,
            "likely_settlement": eval_record.likely_settlement,
            "recommended_demand": eval_record.recommended_demand,
            "economic_damages": eval_record.economic_damages,
            "confidence": eval_record.confidence
        },
        "comparable_cases": eval_record.comparable_cases,
        "swot_analysis": {
            "strengths": eval_record.strengths,
            "weaknesses": eval_record.weaknesses,
            "risk_factors": eval_record.risk_factors
        },
        "recommendations": eval_record.recommendations,
        "created_at": eval_record.created_at
    }

# FEATURE 2: Argument Builder

@router.post("/research/build-argument")
async def build_argument_from_research(
    input_data: ArgumentBuilderInput,
    user: User = Depends(get_current_user),
    temporal: TemporalClient = Depends(get_temporal_client)
):
    """Generate legal argument paragraph from research results"""
    
    if input_data.org_id != user.org_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    input_data.user_id = user.id
    
    workflow_id = f"argument-{user.org_id}-{generate_uuid()}"
    
    handle = await temporal.start_workflow(
        "ArgumentBuilderWorkflow",
        input_data,
        id=workflow_id,
        task_queue="research-queue"
    )
    
    return {
        "workflow_id": workflow_id,
        "status": "generating",
        "message": "Argument generation started"
    }

@router.get("/research/argument-status/{workflow_id}")
async def get_argument_status(
    workflow_id: str,
    user: User = Depends(get_current_user),
    temporal: TemporalClient = Depends(get_temporal_client)
):
    """Check status of argument generation"""
    handle = temporal.get_workflow_handle(workflow_id)
    
    try:
        result = await handle.result()
        return {
            "status": "completed",
            "argument_id": result["argument_id"],
            "generated_text": result["generated_text"],
            "citations": result["citations"]
        }
    except:
        return {
            "status": "generating",
            "workflow_id": workflow_id
        }

# FEATURE 3: Plea Deal Analyzer

@router.post("/analysis/plea-deal")
async def analyze_plea_deal(
    input_data: PleaDealAnalysisInput,
    user: User = Depends(get_current_user),
    temporal: TemporalClient = Depends(get_temporal_client)
):
    """Analyze whether client should accept plea offer"""
    
    if input_data.org_id != user.org_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    input_data.user_id = user.id
    
    workflow_id = f"plea-analysis-{user.org_id}-{generate_uuid()}"
    
    handle = await temporal.start_workflow(
        "PleaDealAnalysisWorkflow",
        input_data,
        id=workflow_id,
        task_queue="analysis-queue"
    )
    
    return {
        "workflow_id": workflow_id,
        "status": "analyzing",
        "message": "Plea deal analysis started"
    }

@router.get("/analysis/plea-status/{workflow_id}")
async def get_plea_analysis_status(
    workflow_id: str,
    user: User = Depends(get_current_user),
    temporal: TemporalClient = Depends(get_temporal_client)
):
    """Check status of plea analysis"""
    handle = temporal.get_workflow_handle(workflow_id)
    
    try:
        result = await handle.result()
        return {
            "status": "completed",
            "analysis_id": result["analysis_id"],
            "recommendation": result["recommendation"],
            "confidence": result["confidence"],
            "conviction_probability": result["conviction_probability"],
            "expected_trial_outcome": result["expected_trial_outcome"],
            "comparison": result["comparison"],
            "strategic_advice": result["strategic_advice"]
        }
    except:
        return {
            "status": "analyzing",
            "workflow_id": workflow_id
        }

@router.get("/analysis/plea/{analysis_id}")
async def get_plea_analysis(
    analysis_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve completed plea analysis"""
    analysis = db.query(PleaAnalysis).filter(
        PleaAnalysis.id == analysis_id,
        PleaAnalysis.org_id == user.org_id
    ).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return {
        "id": analysis.id,
        "original_charges": analysis.original_charges,
        "plea_offer": analysis.plea_offer,
        "recommendation": analysis.recommendation,
        "confidence": analysis.confidence,
        "conviction_probability": analysis.conviction_probability,
        "expected_sentence_if_trial": analysis.expected_sentence_if_trial,
        "comparable_cases": analysis.comparable_cases,
        "reasons_to_accept": analysis.reasons_to_accept,
        "reasons_to_reject": analysis.reasons_to_reject,
        "risk_analysis": analysis.risk_analysis,
        "recommendations": analysis.recommendations,
        "created_at": analysis.created_at
    }
```
## Feature 4: Judge Analysis Workflow

### Overview

**Purpose:** Help attorneys understand judge tendencies before trial/hearing

**User Story:**
"As a defense attorney, I need to know how Judge Smith typically rules on suppression motions so I can advise my client and prepare strategy."

**Frequency:** Used at case assignment and before every major hearing

**Data Sources:**
- Judge People Database (26 fields - name, DOB, gender, biographical data)
- Judge Positions Database (38 fields - nomination, confirmation, voting records, appointer)
- Courts Database (court hierarchy, jurisdiction mappings)
- Dockets Database (4.3GB - case outcomes, judge→case mappings)

### Input
- Judge name OR case number (auto-lookup judge)
- Case type (criminal, civil, family)
- Specific motion type (optional)

### Output
- Judge background (appointment, tenure, political leaning)
- Ruling patterns by case type
- Suppression motion grant rate
- Sentencing tendencies (harsh/lenient vs. average)
- Notable opinions
- Recommended approach

### Workflow Steps
1. Lookup judge in Judge People + Positions databases
2. Query Dockets for all cases under this judge
3. Filter by case type matching user's case
4. Calculate statistics (grant rates, sentencing averages)
5. LLM synthesizes strategy recommendations
6. Return with clickable case citations
___
## Feature 5: Predictive Case Outcome

### Overview

**Purpose:** Predict likely case outcome based on judge, facts, jurisdiction, charge

**User Story:**
"As a defense attorney, I want to know the probability of acquittal vs. conviction given my specific case facts and assigned judge."

**Data Sources:**
- Dockets Database (historical outcomes)
- Judge ruling patterns
- Case law corpus (similar fact patterns)
- Sentencing data

### Input
- Charges
- Key facts
- Judge (if assigned)
- County/jurisdiction
- Client factors (priors, demographics)

### Output
- Conviction probability (%)
- Likely sentence range if convicted
- Comparison: plea vs. trial expected outcomes
- Similar cases with outcomes
- Factors helping/hurting case

### ML Model Requirements
- Training data: Dockets database outcomes
- Features: charge type, jurisdiction, judge, defendant factors
- Model: Classification (conviction Y/N) + Regression (sentence length)
___
## Feature 6: Statutory Analysis Workflow

### Overview

**Purpose:** Deep interpretation of a specific statute

**User Story:**
"As an attorney, I need to understand exactly what ORC 2744.02 means and how courts have interpreted each subsection."

**Frequency:** Used when encountering unfamiliar statute or preparing argument on statutory interpretation

### Input
- Statute citation (ORC, USC, OAC)
- Specific question (optional)

### Output
- Full statute text
- Plain language explanation
- Subsection-by-subsection analysis
- Key terms defined (from case law)
- Interpreting cases with holdings
- Exceptions and limitations
- Related statutes

### Workflow Steps
1. Fetch statute from primary.lmdb
2. Get related statutes from citations.lmdb
3. Get interpreting cases from reverse_citations.lmdb
4. Extract holdings from key cases
5. LLM generates plain language analysis
6. Return with all citations clickable
___
## Feature 7: Case Search Workflow

### Overview

**Purpose:** Find and rank relevant cases by topic or fact pattern

**User Story:**
"As an attorney, I need to find Ohio cases about pregnancy discrimination to support my brief."

**Frequency:** Multiple times per case, highest frequency workflow

### Input
- Search terms or fact pattern
- Jurisdiction filter (Ohio, Federal, both)
- Date range (optional)
- Outcome filter (plaintiff/defendant wins)

### Output
- Ranked case list (relevance score)
- Case summaries with holdings
- Statutes cited by each case
- Grouped by court level, outcome, sub-issue
- All cases clickable for graph exploration

### Ranking Algorithm
- Text relevance: 40%
- Authority (court level + citation count): 25%
- Recency: 20%
- Outcome alignment: 15%
___
## Feature 8: Citation Graph (Not a Workflow)

### Overview

**Purpose:** Interactive 3D visualization of citation relationships

**Trigger:** User clicks any citation in any workflow result

**Key Point:** NO Temporal workflow needed - direct LMDB lookup

### Data Flow
1. User clicks citation (e.g., "ORC 2925.11")
2. Frontend calls: GET /api/knowledge/sections/ORC-2925.11/graph?depth=2
3. Knowledge Service queries citations.lmdb + reverse_citations.lmdb
4. Returns nodes + edges in <100ms
5. Three.js renders interactive graph

### Visual Encoding
- Node color: Blue=statute, Green=case, Orange=admin, Purple=rule
- Node size: Larger = more citations
- Node opacity: Decreases with depth (1.0 → 0.8 → 0.6)
- Click node: Refocuses graph on that node

### LMDB Databases Used
- primary.lmdb (node details)
- citations.lmdb (forward citations)
- reverse_citations.lmdb (backward citations)
- chains.lmdb (pre-computed chains)
___
ff
---

## Data Requirements

### Required Data Sources

#### 1. Comparable Verdicts Database

**Source:** Ohio court records, verdict reporting services

**Data needed:**
- Case names and numbers
- Courts and counties
- Injury types and severity
- Damages awarded (economic + non-economic)
- Year of verdict/settlement
- Liability factors
- Fact summaries

**How to obtain:**
- Subscribe to Ohio verdict reporting services (VerdictSearch, CVN)
- FOIA requests to Ohio courts
- Manual collection from public records
- Partnership with trial attorney associations

**Initial scale:** 5,000+ Ohio verdicts (focus on high-frequency case types first)

#### 2. Sentencing Outcomes Database

**Source:** Ohio courts, public records, Ohio Sentencing Commission

**Data needed:**
- Conviction charges
- Sentences imposed (prison, probation, fines)
- Defendant factors (prior record, age, employment)
- Case factors (weapon, injury, plea vs trial)
- County/court

**How to obtain:**
- Ohio Sentencing Commission data
- County court records (public)
- FOIA requests
- Manual collection from dockets

**Initial scale:** 10,000+ Ohio sentences

#### 3. Enhanced Case Law Database (LMDB)

**Already have:** Complete Ohio case law

**Need to enhance with:**
- Structured headnotes
- Holding extractions
- Legal principle tagging
- Better pincite mapping

**Implementation:** Pre-process existing LMDB data with vLLM to extract structured metadata

---

## Implementation Roadmap

### Phase 1: Foundation (Weeks 1-4)

**Week 1-2: Data Collection & Infrastructure**
- Set up `comparable_verdicts` and `sentencing_data` tables
- Begin data collection (hire contractor or scraping)
- Seed initial dataset (1000+ verdicts, 2000+ sentences)
- Create data ingestion pipeline

**Week 3-4: Feature 1 MVP (Case Valuation)**
- Build Case Valuation workflow
- Implement verdict search and ranking
- Basic valuation calculation logic
- Simple frontend form + results display
- Test with 5-10 real attorney cases

### Phase 2: Enhancement (Weeks 5-8)

**Week 5-6: Feature 2 (Argument Builder)**
- Enhance existing research interface
- Build Argument Builder workflow
- Citation extraction and formatting
- Test with attorneys on real briefs

**Week 7-8: Feature 3 (Plea Analyzer)**
- Build Plea Analysis workflow
- Conviction probability estimation
- Risk calculation and comparison
- Strategic recommendation generation
- Test with criminal defense attorneys

### Phase 3: Polish & Scale (Weeks 9-12)

**Week 9-10: UI/UX Polish**
- Professional report formatting
- Export capabilities (PDF, DOCX)
- Email integration
- Mobile-responsive design

**Week 11-12: Data Expansion**
- Expand verdict database to 5000+ entries
- Expand sentencing database to 10000+ entries
- Add more Ohio counties
- Improve comparable case matching

### Phase 4: Launch (Week 13+)

- Beta test with 10-20 attorneys
- Collect feedback and iterate
- Fix bugs and edge cases
- Prepare marketing materials
- Public launch

---

## Future-Proofing

### Extensible Architecture

**Add new case types:** Extend `CaseType` enum, create new input models, same workflows

**Add new jurisdictions:**
- Create county/state-specific verdict tables
- Same workflow logic, different data sources
- Eventually: multi-state expansion

**Add new analysis types:**
- Discovery analysis (document review)
- Mediation preparation
- Expert witness evaluation
- All follow same Temporal workflow pattern

### Data Model Flexibility

Use JSON fields for flexible data storage:
- Easy to add new fields without migrations
- Can store arbitrary context
- Supports different case types

### API Versioning

Plan for `/api/v2/` when breaking changes needed

---

## Success Metrics

### Usage Metrics
- Evaluations generated per week
- Arguments generated per week
- Plea analyses per week
- Active attorneys per week

### Quality Metrics
- Attorney satisfaction rating (target: 4.5+/5)
- Accuracy of valuations (vs actual settlements)
- Accuracy of plea predictions (vs actual outcomes)
- Time saved per feature use

### Business Metrics
- Conversion rate (trial users → paid)
- Feature usage distribution
- Retention rate
- Referrals/word-of-mouth

---

## Appendix: Sample Prompts

See individual workflow sections for complete vLLM prompts.

---

## Change Log

**v1.0 - November 10, 2025**
- Initial specification
- 3 core high-value features
- Data requirements defined
- Implementation roadmap

---

**Document Owner:** Development Team  
**Last Updated:** November 10, 2025  
**Next Review:** After Phase 1 completion (Week 4)