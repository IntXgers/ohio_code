# Claude Session Notes - Ohio Legal Code Project

## Last Session Summary (2025-11-07)

### What We Just Completed ✓

1. **Fixed Ohio Constitution Scraper**
   - Fixed empty state file handling (JSONDecodeError)
   - Corrected output path from `../../data/` to `../data/`
   - Simplified scraping logic to just grab h1 + all p tags
   - Restored Roman numeral mapping (ROMAN_MAP)
   - Successfully scraped 226 constitution sections
   - Files saved to: `ohio_constitution/src/ohio_constitution/data/scraped_constitution/`

2. **Created Comprehensive Citation Patterns** ✓
   - Created `citation_patterns.py` at project root
   - Defined corpus-specific regex patterns for all 4 corpora:
     - **ORC**: Section formats like "section 124.01", "R.C. 2903.01"
     - **OAC**: Rule formats like "rule 123-4-56", "OAC 789-10-11"
     - **Constitution**: Article formats like "Article I, Section 1" → "I-1"
     - **Case Law**: All above + case citations like "123 Ohio St. 456"
   - Includes reference classification and validation
   - Handles cross-corpus citations
   - **Tested and working**

### Important Notes

- **DO NOT git add large JSON/JSONL files** - user gets rejected, they're too large
- `.gitignore` only blocks `report.[0-9]*.[0-9]*.[0-9]*.[0-9]*.json` (diagnostic reports)
- Data files exist but should NOT be committed to git

### Current Repository State

**4 Main Corpora:**

1. **ohio_revised/** - COMPLETE ✓
   - 23,654 sections scraped
   - Citation analysis DONE (citation_map.json, citation_analysis.json)
   - LMDB built (660 MB, 5 databases)
   - Enrichment logic exists (enricher.py)

2. **ohio_administration/** - Partially Complete
   - 6,976 rules scraped (JSONL exists)
   - NO citation analysis yet
   - NO LMDB yet
   - NO enrichment yet

3. **ohio_case_law/** - Data Only
   - 22,205 cases scraped
   - NO citation analysis yet
   - Cross-references: 24% cite ORC, 8.2% cite Constitution, 0.3% cite Admin

4. **ohio_constitution/** - Just Scraped ✓
   - 226 sections scraped (JUST FINISHED)
   - NO citation analysis yet
   - NO LMDB yet

### Architecture Plan - 3 Layers

**Layer 1: Self-Analysis** (each corpus analyzes itself)
- ORC → ORC citations
- OAC → OAC citations
- Constitution → Constitution citations
- Case Law → Case citations

**Layer 2: Pairwise Cross-Corpus** (12 combinations)
- ORC ↔ OAC
- ORC ↔ Constitution
- ORC ↔ Case Law
- OAC ↔ Constitution
- OAC ↔ Case Law
- Constitution ↔ Case Law

**Layer 3: Unified Graph**
- All self-analysis + all pairwise → complete citation graph

### What Needs to Happen Next

**Immediate Next Steps:**

1. **Copy citation_mapper.py to each corpus**
   - ohio_administration/src/ohio_administration/citation_analysis/
   - ohio_constitution/src/ohio_constitution/citation_analysis/
   - ohio_case_law/src/ohio_case_law/citation_analysis/

2. **Customize each citation_mapper.py**
   - Import patterns from `citation_patterns.py`
   - Update `self.reference_patterns` to use corpus-specific patterns
   - Update `extract_section_number()` to use corpus-specific extractor

3. **Run citation analysis for remaining corpora**
   - Admin Code
   - Constitution
   - Case Law

4. **Build LMDB for remaining corpora**
   - Use `build_comprehensive_lmdb.py` as template
   - Customize for each corpus

5. **Cross-corpus citation analysis** (Layer 2)
   - Need new script for pairwise analysis
   - Each corpus needs to find references to OTHER corpora

### Key Files Reference

**Patterns & Config:**
- `/citation_patterns.py` - All corpus-specific regex patterns (JUST CREATED)

**ORC (Complete):**
- `ohio_revised/src/ohio_revised/citation_analysis/citation_mapper.py` - Analysis logic
- `ohio_revised/src/ohio_revised/data/citation_analysis/citation_map.json` - Results
- `ohio_revised/src/ohio_revised/lmdb/build_comprehensive_lmdb.py` - LMDB builder
- `ohio_revised/src/ohio_revised/enrichment/enricher.py` - Q&A enrichment

**Admin Code (Needs Work):**
- Data: `ohio_administration/src/ohio_administration/data/ohio_admin_complete_jsonl/ohio_admin_code_complete.jsonl`
- Header format: `"Rule 011-1-01|Rule to provide for notification of meeting."`
- ID format: `123-4-56`

**Constitution (Needs Work):**
- Data: `ohio_constitution/src/ohio_constitution/data/scraped_constitution/ohio_constitution_complete.jsonl`
- Header format: `"Article I, Section 1|Inalienable Rights"`
- ID format: `I-1`

**Case Law (Needs Work):**
- Data: `ohio_case_law/src/ohio_case_law/data/jsonl_output/ohio_case_law_complete.jsonl`
- Has `case_id` and `citation` fields
- ID format: `case_500105` or citation-based

### User Preferences

- User wants corpus-specific patterns (NOT shared library approach)
- Be careful not to do things without being asked
- Don't add large files to git
- When fixing code, restore everything - don't simplify or remove features
- Ask if unsure about approach

### Where We Left Off

User said: "Make yourself a set of notes. I gotta close and reopen the editors. It's freezing up so we can pick up right where we left off"

**Status:** Citation patterns created and tested. Ready to copy citation_mapper.py to other corpora and customize with new patterns.

**Next Action When Resuming:**
User will tell me to look at these notes. Then likely proceed with:
1. Copy citation_mapper.py to Admin Code
2. Customize it with OAC_PATTERNS
3. Run citation analysis on Admin Code

---

## CRITICAL NOTES - 2025-11-27

### BEFORE Building Ohio Case Law LMDB

⚠️ **MUST REVIEW ENRICHMENT WITH USER FIRST** ⚠️

- DO NOT build the Case Law LMDB until we review the enrichment strategy together
- User wants to go over the JSONL enrichment approach before or during the LMDB build
- We need to ensure we're querying the best possible data
- The 7 enrichment fields may need adjustment based on case law specifics

**Action Required:**
1. Review current enrichment fields with user
2. Discuss if we should pre-enrich the JSONL or enrich during LMDB build
3. Confirm the 7 fields are optimal for case law queries
4. Get approval before running the full 175K case build

### LMDB ARCHITECTURE - KEEP SEPARATE ✅

**DECISION: Keep LMDBs separate per corpus (NOT combined)**

**Why Separate is Better:**
- Agent queries across multiple LMDBs and assembles context for the LLM
- With 512GB RAM, all LMDBs stay cached in memory → same speed as one combined DB
- Easier maintenance: rebuild only the corpus that changed
- Easier debugging: isolate issues to specific corpus
- Negligible performance difference between separate lookups vs. combined

**How It Works:**
1. Knowledge service opens all corpus LMDBs at startup (all cached in RAM)
2. Agent queries primary.lmdb for content
3. Agent follows citations across corpuses using citation.lmdb
4. Agent assembles all related content into coherent context
5. LLM receives assembled text (never touches LMDB directly)

**Example Flow:**
```
User asks about ORC 2903.01
→ Agent queries ohio_revised/primary.lmdb (RAM cached)
→ Agent checks ohio_revised/citations.lmdb → finds refs to Constitution I-16 and 2 cases
→ Agent queries ohio_constitution/primary.lmdb for I-16 (RAM cached)
→ Agent queries ohio_caselaw/primary.lmdb for cases (RAM cached)
→ Agent assembles: statute + constitutional article + case law
→ LLM receives complete context bundle
```

**Architecture:**
- Build: `dist/ohio_revised/`, `dist/ohio_admin/`, `dist/ohio_constitution/`, `dist/ohio_caselaw/`
- Deploy: Knowledge service opens all 4 (or eventually 8) at once
- Query: Agent hops between DBs following citation IDs
- Performance: With 512GB RAM, all lookups are instant (cached)

**No combined LMDB needed!**

---
*Session saved: 2025-11-27*
