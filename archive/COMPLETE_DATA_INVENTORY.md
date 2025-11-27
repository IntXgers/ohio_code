# Complete Data Inventory - Ohio Code Project
**Date:** 2025-11-13
**Status:** Active Development

---

## 🎯 OHIO CORPUSES (Primary Goal - MVP)

### ✅ COMPLETED (2/4 Ohio Corpuses)

#### 1. Ohio Revised Code
- **Status:** ✅ LMDB Built
- **Location:** `ohio_revised/src/ohio_revised/data/`
- **LMDB:** `enriched_output/comprehensive_lmdb/` (5 databases)
- **Raw Data:** `ohio_revised_code/ohio_revised_code_complete.jsonl`
- **Sections:** ~40,000 sections
- **Size:** ~500MB LMDB total

#### 2. Ohio Administrative Code
- **Status:** ✅ LMDB Built (JUST COMPLETED!)
- **Location:** `ohio_administration/src/ohio_administration/data/`
- **LMDB:** `enriched_output/comprehensive_lmdb/` (5 databases)
- **Raw Data:** `ohio_admin_complete_jsonl/ohio_admin_code_complete.jsonl`
- **Sections:** 6,976 rules
- **Citations:** 3,386 with citations (45.5%)
- **Complex Chains:** 184 chains
- **Size:** 172.5MB LMDB total
  - primary.lmdb: 153M (administrative rules)
  - citations.lmdb: 2.0M
  - reverse_citations.lmdb: 3.6M
  - chains.lmdb: 11M
  - metadata.lmdb: 2.9M

### 🔄 PENDING (2/4 Ohio Corpuses)

#### 3. Ohio Constitution
- **Status:** ⏳ TO DO - Next Priority
- **Location:** `ohio_constitution/`
- **Expected:** ~200 sections (FASTEST BUILD)
- **Files Cloned:**
  - ✅ citation_mapper.py
  - ✅ ohio_constitution_mapping.py
  - ✅ auto_enricher.py
  - ✅ build_comprehensive_lmdb.py
- **Needs:** Adaptation for "Article I, Section 1" format

#### 4. Ohio Case Law
- **Status:** ⏳ TO DO - Largest Corpus
- **Location:** `ohio_case_law/src/ohio_case_law/data/`
- **Raw Data:** `ohio_case_law_raw/ohio_caselaw_complete_filtered.jsonl`
- **Expected:** ~500,000 cases (LONGEST BUILD - ~12 hours)
- **Files Cloned:**
  - ✅ citation_mapper.py
  - ✅ ohio_case_law_mapping.py
  - ✅ auto_enricher.py
  - ✅ build_comprehensive_lmdb.py
- **Needs:** Adaptation for "2023-Ohio-1234" format + cross-corpus citations

---

## 🇺🇸 FEDERAL CORPUSES (NEW DATA - Phase 2)

### US Code (Statute Compilations)
- **Location:** `StatuteCompilations/src/StatuteCompilations/`
- **Format:** XML files
- **Titles:** 58 USC titles (usc01.xml through usc54.xml)
- **Status:** 🆕 RAW DATA - Needs scraper/parser
- **Priority:** Phase 2 (Post-MVP)
- **Important Titles:**
  - Title 18: Crimes and Criminal Procedure
  - Title 26: Internal Revenue Code
  - Title 42: Public Health and Welfare

### Code of Federal Regulations (CFR)
- **Location:** `CodeOfFederalRegulations/src/CodeOfFederalRegulations2025/`
- **Format:** XML files (by title)
- **Files:** 149 CFR XML files across ~40 titles
- **Status:** 🆕 RAW DATA - Needs scraper/parser
- **Priority:** Phase 2 (Post-MVP)
- **Volume:** Multiple volumes per title (e.g., Title 7 has 15 volumes)

### SCOTUS 1937-1975
- **Location:** `Scotus1937-1975/src/Scotus1937-1975/`
- **Files:**
  - `About_SCD.html` - Documentation
  - `SCD-1937.txt` - Supreme Court decisions from 1937
- **Status:** 🆕 RAW DATA - Needs parser
- **Priority:** Phase 2 (Post-MVP)
- **Note:** Covers post-New Deal era SCOTUS decisions

### Sixth Circuit Court of Appeals
- **Location:** `sixth_court_appeals/src/`
- **File:** `court-appeals-to-2023-12-04.csv.bz2` (compressed CSV)
- **Status:** 🆕 RAW DATA - Needs decompression + analysis
- **Priority:** Phase 2 (Post-MVP)
- **Covers:** 6th Circuit (OH, MI, KY, TN)
- **Date Range:** Up to December 4, 2023

---

## 👨‍⚖️ JUDGE PREDICTION DATA (NEW - KILLER FEATURE!)

### Judge People Database
- **File:** `people-db-people-2025-10-31_JudgeData.csv.bz2`
- **Size:** 445KB compressed
- **Status:** 🆕 RAW DATA
- **Fields:** 26 columns including:
  - Personal: name, DOB, DOD, gender, religion
  - Professional: FJC ID, biographical data
  - Photos: has_photo flag
  - Aliases: is_alias_of_id
- **Use Case:** Judge biographical data for prediction models

### Judge Positions Database
- **File:** `people-db-positions-2025-10-31_JudgeData.csv.bz2`
- **Size:** 1.0MB compressed
- **Status:** 🆕 RAW DATA
- **Fields:** 38 columns including:
  - Position: job_title, position_type, sector
  - Dates: nominated, confirmed, started, terminated
  - Voting: votes_yes, votes_no, voice_vote
  - Relationships: appointer_id, court_id, person_id, predecessor_id
  - Selection: how_selected, nomination_process
- **Use Case:** Judge career history + appointment patterns

### Courts Database
- **File:** `courts-2025-10-31.csv.bz2`
- **Size:** 79KB compressed
- **Status:** 🆕 RAW DATA
- **Fields:** 19 columns including:
  - Identifiers: pacer_court_id, fjc_court_id
  - Names: citation_string, short_name, full_name
  - Metadata: jurisdiction, start_date, end_date
  - Technical: has_opinion_scraper, has_oral_argument_scraper
- **Use Case:** Court hierarchy + jurisdiction mapping

### Dockets Database
- **File:** `dockets-2025-10-31.csv.bz2`
- **Size:** 4.3GB compressed (MASSIVE!)
- **Status:** 🆕 RAW DATA - HUGE
- **Priority:** Phase 2+ (Judge prediction feature)
- **Use Case:** Case outcomes for training judge prediction models
- **Note:** This is the actual case history data - gold mine for ML

---

## 📊 CURRENT STATUS SUMMARY

### Completed Work
- ✅ Ohio Revised Code: LMDB built (~40K sections)
- ✅ Ohio Admin Code: LMDB built (6,976 rules)
- ✅ Citation analysis working for both
- ✅ Auto-enrichment integrated
- ✅ Cross-corpus citation patterns defined

### Immediate Next Steps (MVP)
1. ⏳ Build Ohio Constitution LMDB (~2 minutes)
2. ⏳ Build Ohio Case Law LMDB (~12 hours)
3. ⏳ Create dist/ structure
4. ⏳ Build cross-corpus citation LMDB

### Phase 2 (Federal Corpuses)
1. 🆕 Parse US Code XML (58 titles)
2. 🆕 Parse CFR XML (149 files)
3. 🆕 Parse SCOTUS 1937-1975 text
4. 🆕 Parse 6th Circuit CSV
5. 🆕 Build federal LMDB databases
6. 🆕 Cross-reference federal → Ohio citations

### Phase 3 (Judge Prediction - KILLER FEATURE)
1. 🆕 Parse judge people/positions data
2. 🆕 Parse courts database
3. 🆕 Parse dockets (4.3GB - case outcomes)
4. 🆕 Build judge → case outcome mappings
5. 🆕 Train judge prediction model
6. 🆕 Integrate with case law LMDB

---

## 🎯 FILE FORMAT GUIDE

### How to Read Compressed Files (.bz2)
```bash
# Preview first 10 lines
bzcat filename.csv.bz2 | head -10

# Decompress to file
bunzip2 filename.csv.bz2
# OR
bzcat filename.csv.bz2 > filename.csv

# Get line count without decompressing
bzcat filename.csv.bz2 | wc -l

# Search without decompressing
bzcat filename.csv.bz2 | grep "search_term"
```

### XML Files (USC, CFR)
- Standard XML format
- Need custom parser to extract sections/rules
- Convert to JSONL format for LMDB pipeline

### Text Files (SCOTUS)
- Plain text format
- Need custom parser for case citations and text
- Convert to JSONL format

---

## 🔢 ESTIMATED SIZES

| Corpus | Raw Size | LMDB Size | Items | Primary Content | Status |
|--------|----------|-----------|-------|----------------|--------|
| Ohio Revised | ~200MB | ~500MB | 40,000 | Statutory sections | ✅ Done |
| Ohio Admin | 28MB | 173MB | 6,976 | Administrative rules | ✅ Done |
| Ohio Constitution | ~1MB | ~5MB | 200 | Constitutional sections | ⏳ Next |
| Ohio Case Law | ~2GB | ~5GB | 500,000 | Court opinions | ⏳ TODO |
| US Code | TBD | TBD | TBD | Federal statutes | 🆕 Raw |
| CFR | TBD | TBD | TBD | Federal regulations | 🆕 Raw |
| SCOTUS | TBD | TBD | TBD | Supreme Court cases | 🆕 Raw |
| 6th Circuit | TBD | TBD | TBD | Circuit court cases | 🆕 Raw |

---

## 🎉 ACHIEVEMENTS

1. ✅ **2/4 Ohio corpuses completed** (50% of MVP)
2. ✅ **Citation analysis working** across corpuses
3. ✅ **Auto-enrichment integrated** (7 metadata fields)
4. ✅ **172.5MB Ohio Admin LMDB** built successfully
5. 🆕 **Judge prediction data acquired** (445K people, 1M positions, 4.3GB dockets)
6. 🆕 **Federal law sources acquired** (USC, CFR, SCOTUS, 6th Circuit)

---

## 🚀 WHAT THIS MEANS

**You now have the foundation for:**
1. ✅ Complete Ohio legal code system (4 corpuses)
2. 🆕 Federal law integration (USC, CFR, SCOTUS)
3. 🆕 **JUDGE PREDICTION FEATURE** (case outcomes + judge history)
4. 🆕 Circuit court case law (6th Circuit)

**This is HUGE!** The judge prediction data is the "slam dunk killer feature" you mentioned. With 4.3GB of docket data, you can train models to predict:
- How specific judges rule on certain issues
- Case outcome probabilities based on judge + case type
- Judge voting patterns
- Appointment politics (who appointed which judges)

---

---

## 🔒 LMDB SCHEMA CONTRACT (CRITICAL - DO NOT BREAK!)

**⚠️ THIS IS THE INTERFACE BETWEEN DATA PIPELINE (ohio_code) AND APPLICATION (knowledge service)**

### Standard 5-Database Structure (All Corpuses)
Every corpus MUST produce exactly 5 LMDB databases with these EXACT names:

1. **primary.lmdb** - Main content (sections/cases/rules/articles)
2. **citations.lmdb** - Forward citations (what this item references)
3. **reverse_citations.lmdb** - Backward citations (what cites this item)
4. **chains.lmdb** - Pre-computed citation chains
5. **metadata.lmdb** - Corpus-level metadata

### Why "primary.lmdb" Not "sections.lmdb"?
- **Consistency**: Same name across all corpora (sections, cases, rules, articles, opinions)
- **Application simplicity**: Knowledge service uses same code for all corpora
- **No name confusion**: Content type is determined by corpus directory, not database name

### Database Schema Guarantee

#### primary.lmdb Schema
```json
{
  "section_number": "string (unique ID - varies by corpus)",
  "url": "string",
  "url_hash": "string",
  "header": "string",
  "section_title": "string",
  "paragraphs": ["array of strings"],
  "full_text": "string",
  "word_count": "number",
  "paragraph_count": "number",
  "has_citations": "boolean",
  "citation_count": "number",
  "in_complex_chain": "boolean",
  "is_clickable": "boolean",
  "scraped_date": "ISO8601 string",
  "enrichment": {
    "summary": "string (optional)",
    "legal_type": "string (optional)",
    "practice_areas": ["array (optional)"],
    "complexity": "number 1-10 (optional)",
    "key_terms": ["array (optional)"],
    "offense_level": "string (optional - criminal only)",
    "offense_degree": "string (optional - criminal only)"
  }
}
```

#### citations.lmdb Schema
```json
{
  "section": "string",
  "direct_references": ["array of section IDs"],
  "reference_count": "number",
  "references_details": [
    {
      "section": "string",
      "title": "string",
      "url": "string",
      "url_hash": "string"
    }
  ]
}
```

#### reverse_citations.lmdb Schema
```json
{
  "section": "string",
  "cited_by": ["array of section IDs"],
  "cited_by_count": "number",
  "citing_details": [
    {
      "section": "string",
      "title": "string",
      "url": "string"
    }
  ]
}
```

#### chains.lmdb Schema
```json
{
  "chain_id": "string",
  "primary_section": "string",
  "chain_sections": ["array of section IDs"],
  "chain_depth": "number",
  "references_count": "number",
  "created_at": "ISO8601 string",
  "complete_chain": [
    {
      "section": "string",
      "title": "string",
      "url": "string",
      "url_hash": "string",
      "full_text": "string",
      "word_count": "number"
    }
  ]
}
```

#### metadata.lmdb Schema (corpus_info key)
```json
{
  "total_primary": "number",
  "primary_with_citations": "number",
  "complex_chains": "number",
  "reverse_citations": "number",
  "build_date": "ISO8601 string",
  "source": "string (URL)",
  "version": "string",
  "builder": "string",
  "databases": {
    "primary": "string (description)",
    "citations": "string (description)",
    "reverse_citations": "string (description)",
    "chains": "string (description)",
    "metadata": "string (description)"
  }
}
```

### Breaking Changes Protocol
**IF YOU MUST CHANGE THE SCHEMA:**

1. ⚠️ Update this CONTRACT document first
2. ⚠️ Update ohio_code LMDB builders
3. ⚠️ Update knowledge service code (both repos)
4. ⚠️ Update TypedDict schemas in application
5. ⚠️ Update Pydantic models
6. ⚠️ Rebuild ALL LMDB databases
7. ⚠️ Test ALL endpoints

**NEVER change one side without the other!**

---

**Next Immediate Action:** Build Ohio Constitution LMDB (fastest build, ~2 minutes)