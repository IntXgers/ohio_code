# Ohio Legal Data Pipeline - Complete Status & Guide

**Last Updated:** 2025-11-25
**Repository:** `ohio_code` (Data Pipeline)
**Application:** `ohio-legal-ai.io` (Knowledge Service)

---

## Executive Summary: 75% Complete ✅

### What's Built (3 of 4 Ohio Corpuses)

| Corpus | Records | LMDB Size | Status | Location |
|--------|---------|-----------|--------|----------|
| **Ohio Revised Code** | 40,000 sections | 1.5 GB | ✅ Built | `dist/ohio_revised/` |
| **Ohio Admin Code** | 6,976 rules | 95 MB | ✅ Built | `dist/ohio_admin/` |
| **Ohio Constitution** | ~200 sections | 1.8 MB | ✅ Built | `dist/ohio_constitution/` |
| **Ohio Case Law** | 175,857 cases | Not built | ⏳ **Ready** | Data on external drive |

**Next Step:** Build Ohio Case Law LMDB → 100% MVP Complete

---

## 1. Data Collection Status

### Ohio State Law (Complete ✅)

#### Statutes & Regulations
- ✅ **Ohio Revised Code**: 40,000 sections scraped, analyzed, built
- ✅ **Ohio Administrative Code**: 6,976 rules scraped, analyzed, built
- ✅ **Ohio Constitution**: ~200 sections scraped, analyzed, built

#### Case Law
- ✅ **Court Reporters (Filtered)**: 9,369 cases (historical reporters, junk removed)
- ✅ **12 Courts of Appeals + Supreme Court**: 166,488 cases (official website)
- ✅ **Combined Total**: 175,857 cases ready to build
- **Location**: `/Volumes/Jnice4tb/Jurist_ohio_corpus/ohio_case_law copy/`
- **Symlinked to**: `ohio_caselaw/src/ohio_caselaw/data/pre_enriched_input/`

### Federal Law (Raw Data Available, Not Processed)

- 🆕 **US Code (USC)**: 58 titles in XML format
- 🆕 **Code of Federal Regulations (CFR)**: 149 XML files
- 🆕 **SCOTUS 1937-1975**: Plain text decisions
- 🆕 **6th Circuit Court of Appeals**: CSV data through Dec 2023

### Judge Prediction Data (Available, Not Processed)

- 🆕 **Judge People DB**: 445KB biographical data
- 🆕 **Judge Positions DB**: 1.0MB career history
- 🆕 **Courts DB**: 79KB court metadata
- 🆕 **Dockets DB**: 4.3GB case outcomes (MASSIVE - ML goldmine)

---

## 2. Architecture Overview

### Data Flow
```
External Drive (Jurist corpus)
  ↓ (symlink)
ohio_code/{corpus}/data/pre_enriched_input/
  ↓ (citation analysis)
ohio_code/{corpus}/data/citation_analysis/
  ↓ (LMDB build with auto-enrichment)
ohio_code/dist/{corpus}/
  ↓ (symlink)
ohio-legal-ai.io/knowledge_service/lmdb_data/{corpus}/
  ↓ (FastAPI endpoints)
Knowledge Service APIs
```

### Repository Structure
```
ohio_code/
├── dist/                          # ← All LMDBs output here (central distribution)
│   ├── ohio_revised/             # ✅ 1.5 GB (40K sections)
│   ├── ohio_admin/               # ✅ 95 MB (6,976 rules)
│   ├── ohio_constitution/        # ✅ 1.8 MB (~200 sections)
│   └── ohio_caselaw/             # ❌ Not built (175,857 cases ready)
│
├── ohio_revised/                  # Statutory code corpus
│   ├── src/ohio_revised/
│   │   ├── scraper/              # Data collection scripts
│   │   ├── citation_analysis/    # Extract citation graph
│   │   ├── lmdb/                 # Build databases
│   │   │   ├── auto_enricher.py          # Add metadata (legal_type, practice_areas, etc.)
│   │   │   ├── build_comprehensive_lmdb.py   # Build 5 LMDB databases
│   │   │   └── generated_schemas.py      # TypedDicts from Pydantic models (zero-drift)
│   │   └── data/                 # Input data
│   └── pyproject.toml
│
├── ohio_administration/           # Administrative rules corpus (same structure)
├── ohio_constitution/             # State constitution corpus (same structure)
├── ohio_caselaw/                  # Court opinions corpus (same structure)
│
└── docs/
    └── DATA_PIPELINE_STATUS.md   # This file
```

### Each Corpus Outputs 5 LMDB Databases

Every corpus produces the same 5 database structure:

1. **primary.lmdb** - Full text of all sections/cases/rules/articles
2. **citations.lmdb** - Forward citations (what this cites)
3. **reverse_citations.lmdb** - Reverse citations (what cites this)
4. **chains.lmdb** - Pre-computed citation chains for visualization
5. **metadata.lmdb** - Corpus statistics and metrics

**Why "primary.lmdb" not "sections.lmdb"?**
- Same name across all corpora for consistency
- Content type determined by corpus directory, not database name
- Knowledge service uses same code for all corpora

---

## 3. LMDB Schema Contract (CRITICAL)

**⚠️ THIS IS THE INTERFACE BETWEEN DATA PIPELINE AND APPLICATION**

### Zero-Drift Architecture

```
ohio-legal-ai.io (Application)
  ↓ Pydantic models (source of truth)
  ↓ Generate TypedDicts
  ↓
ohio_code (Data Pipeline)
  ↓ Use generated schemas
  ↓ Build LMDBs
  ↓
ohio-legal-ai.io (Application)
  ↓ Read LMDB
  ↓ Map back to Pydantic (guaranteed match)
```

### primary.lmdb Schema (All Corpuses)

```python
{
  "section_number": "string (unique ID)",
  "url": "string",
  "url_hash": "string",
  "header": "string",
  "section_title": "string",
  "paragraphs": ["array of strings - EXACT LEGAL TEXT"],
  "full_text": "string (concatenated)",
  "word_count": "number",
  "paragraph_count": "number",
  "has_citations": "boolean",
  "citation_count": "number",
  "in_complex_chain": "boolean",
  "is_clickable": "boolean (has graph data)",
  "scraped_date": "ISO8601 string",
  "enrichment": {
    "summary": "string (optional)",
    "legal_type": "criminal_statute | civil_statute | definitional | procedural",
    "practice_areas": ["criminal_law", "family_law", "business_law", ...],
    "complexity": "number 1-10",
    "key_terms": ["array of legal terms"],
    "offense_level": "felony | misdemeanor (criminal only)",
    "offense_degree": "F1-F5 | M1-M4 (criminal only)"
  }
}
```

### citations.lmdb Schema

```python
{
  "section": "string",
  "direct_references": ["array of section IDs"],
  "reference_count": "number",
  "references_details": [
    {
      "section": "string",
      "title": "string",
      "url": "string",
      "url_hash": "string",
      "relationship": "cross_reference | defines | modifies | etc.",
      "context": "string (citation context)",
      "position": "number (position in text)"
    }
  ]
}
```

### reverse_citations.lmdb Schema

```python
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

### chains.lmdb Schema

```python
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

### metadata.lmdb Schema (corpus_info key)

```python
{
  "total_sections": "number",
  "sections_with_citations": "number",
  "complex_chains": "number",
  "reverse_citations": "number",
  "build_date": "ISO8601 string",
  "source": "string (URL)",
  "version": "string",
  "builder": "string",
  "databases": ["primary", "citations", "reverse_citations", "chains", "metadata"]
}
```

**⚠️ BREAKING CHANGES PROTOCOL:**
If you MUST change the schema:
1. Update this document first
2. Update ohio_code LMDB builders
3. Update knowledge service code
4. Update TypedDict schemas
5. Update Pydantic models
6. Rebuild ALL LMDBs
7. Test ALL endpoints

---

## 4. Knowledge Service Integration

### Symlink Architecture

**Application Repo**: `ohio-legal-ai.io`

```
knowledge_service/
├── lmdb_data -> /ohio_code/dist/     # Single symlink to entire dist/ folder
├── lmdb_store.py                     # Query logic
└── main.py                           # FastAPI endpoints
```

**Current Configuration:**
- Knowledge service defaults to `lmdb_data/ohio_revised/`
- Can switch corpuses via `LMDB_DATA_DIR` environment variable
- Eventually will support querying all 4 corpuses simultaneously

### Setup Commands

```bash
# In ohio-legal-ai.io repo
cd services/knowledge_service/src/knowledge_service

# Create symlink to entire dist/ folder
ln -s /Users/justinrussell/active_projects/LEGAL/ohio_code/dist lmdb_data

# Verify
ls -la lmdb_data/
# Should show:
#   ohio_revised/
#   ohio_admin/
#   ohio_constitution/
#   ohio_caselaw/ (when built)
```

### Switching Corpuses

**Method 1: Environment Variable**
```bash
LMDB_DATA_DIR=/path/to/lmdb_data/ohio_admin python main.py
```

**Method 2: Update Default in main.py**
```python
LMDB_DATA_DIR = Path(os.getenv(
    "LMDB_DATA_DIR",
    str(Path(__file__).parent / "lmdb_data" / "ohio_constitution")  # Change this
)).expanduser()
```

---

## 5. Current Build Status

### ✅ Completed (3 of 4 Ohio Corpuses)

#### Ohio Revised Code
- **Sections**: 40,000 statutory sections
- **Citations**: Citation analysis complete
- **LMDB**: All 5 databases built (1.5 GB total)
- **Enrichment**: Auto-enrichment with 7 metadata fields
- **Output**: `dist/ohio_revised/`
- **Status**: ✅ Complete

#### Ohio Administrative Code
- **Rules**: 6,976 administrative rules
- **Citations**: 3,386 with citations (48.5%)
- **Complex Chains**: 184 chains
- **LMDB**: All 5 databases built (95 MB total)
- **Enrichment**: Auto-enrichment complete
- **Output**: `dist/ohio_admin/`
- **Status**: ✅ Complete

#### Ohio Constitution
- **Sections**: ~200 constitutional sections
- **Citations**: Citation analysis complete
- **LMDB**: All 5 databases built (1.8 MB total)
- **Enrichment**: Auto-enrichment complete
- **Output**: `dist/ohio_constitution/`
- **Status**: ✅ Complete

### ⏳ Ready to Build (1 of 4 Ohio Corpuses)

#### Ohio Case Law
- **Cases**: 175,857 court opinions
  - Court Reporters (filtered): 9,369 cases
  - 12 Courts of Appeals + Supreme Court: 166,488 cases
- **Data Location**: `/Volumes/Jnice4tb/Jurist_ohio_corpus/ohio_case_law copy/`
- **Symlink**: `ohio_caselaw/src/ohio_caselaw/data/pre_enriched_input/` ✅ Fixed
- **Citations**: ⏳ Needs to run citation analysis
- **LMDB**: ⏳ Needs to build
- **Estimated Build Time**: 12-24 hours
- **Output**: `dist/ohio_caselaw/`
- **Status**: ⏳ Data ready, needs to build

---

## 6. Next Immediate Steps

### To Complete MVP (100% of Ohio Legal Data)

1. **Run Citation Analysis for Ohio Case Law**
   ```bash
   cd ohio_caselaw/src/ohio_caselaw/citation_analysis
   python citation_mapper.py
   ```
   - Extract case-to-case citations
   - Extract case-to-statute citations (cross-corpus)
   - Build citation graph
   - Output: `citation_map.json`, `complex_chains.jsonl`

2. **Build Ohio Case Law LMDB**
   ```bash
   cd ohio_caselaw/src/ohio_caselaw/lmdb
   python build_comprehensive_lmdb.py
   ```
   - Read 175,857 cases
   - Build 5 LMDB databases
   - Output to `dist/ohio_caselaw/`
   - **Time**: 12-24 hours

3. **Verify Knowledge Service Access**
   ```bash
   # In ohio-legal-ai.io repo
   cd services/knowledge_service/src/knowledge_service

   # Update main.py to point to ohio_caselaw
   # Then start service and test endpoints
   python main.py
   ```

**Result**: 100% of Ohio legal data (4 corpuses, 20 LMDB databases) ready for production

---

## 7. Future Enhancements (Post-MVP)

### Phase 1: Authority Scoring & Treatment Detection (2-3 weeks)
- Run PageRank on citation graphs to compute authority scores
- Detect treatment status (valid, superseded, amended, repealed)
- Parse effective dates from statute text
- Add temporal tracking (valid_from, valid_until)
- Enhance all existing data without adding new corpuses

### Phase 2: Federal Law Integration (4-6 weeks)
- Parse US Code XML (58 titles)
- Parse CFR XML (149 files)
- Parse SCOTUS 1937-1975 text
- Parse 6th Circuit CSV
- Build federal LMDBs (3 more corpuses = 15 databases)
- Cross-reference federal → Ohio citations

### Phase 3: Judge Prediction (Killer Feature) (1-2 weeks data + 1 week ML)
- Parse judge people/positions data (445K people, 1M positions)
- Parse courts database (jurisdiction hierarchy)
- Parse dockets database (4.3GB case outcomes)
- Train judge outcome prediction model
- Integrate with case law LMDB
- API: Predict how specific judges will rule on case types

### Phase 4: Advanced Features (Optional)
- Semantic search (fact pattern embeddings)
- Holdings extraction (ratio decidendi vs obiter dicta)
- Citation strength scoring
- Treatment propagation (transitive invalidation)
- Shepardization system

---

## 8. Disk Space Summary

| Corpus | LMDB Size | Records | Status |
|--------|-----------|---------|--------|
| Ohio Revised | 1.5 GB | 40,000 | ✅ Built |
| Ohio Admin | 95 MB | 6,976 | ✅ Built |
| Ohio Constitution | 1.8 MB | ~200 | ✅ Built |
| Ohio Case Law | TBD (~5-10 GB) | 175,857 | ⏳ Ready to build |
| **Ohio Total (MVP)** | **~7-12 GB** | **223,033** | **75% Complete** |
| US Code (future) | ~2 GB | ~54,000 | 🆕 Raw data available |
| SCOTUS (future) | ~5 GB | ~35,000 | 🆕 Raw data available |
| 6th Circuit (future) | ~8 GB | ~80,000 | 🆕 Raw data available |
| **Full System** | **~22-27 GB** | **~392,000** | **Future** |

---

## 9. Key Files & Locations

### Build Scripts (Pattern Repeated Across All Corpuses)

```
{corpus}/src/{corpus}/
├── scraper/
│   ├── scraper_script.py          # Web scraping
│   └── convert_to_jsonl.py        # JSONL conversion
├── citation_analysis/
│   ├── citation_mapper.py         # Extract citations
│   └── {corpus}_mapping.py        # Corpus-specific patterns
├── lmdb/
│   ├── auto_enricher.py           # Add metadata
│   ├── build_comprehensive_lmdb.py    # Build 5 databases
│   ├── generated_schemas.py       # TypedDicts (auto-generated)
│   └── inspect_lmdb.py            # Inspection tool
└── data/
    ├── pre_enriched_input/        # Raw JSONL (symlinked to external drive)
    ├── citation_analysis/         # Citation graph output
    └── enriched_output/           # Local LMDB (copied to dist/)
        └── comprehensive_lmdb/
```

### External Drive Data

```
/Volumes/Jnice4tb/Jurist_ohio_corpus/
├── ohio_revised copy/
├── ohio_administration copy/
├── ohio_constitution copy/
└── ohio_case_law copy/
    └── src/ohio_case_law/data/pre_enriched_input/ohio_caselaw_complete/
        ├── jsonl_all/ohio_case_law_complete.jsonl  # 175,857 cases ← Use this
        └── jsonl_json_html_older/                   # Older version (9,369 cases)
```

---

## 10. Documentation Consolidation

**This document replaces:**
- ✅ `COMPLETE_DATA_INVENTORY.md` (merged)
- ✅ `GAP_ANALYSIS.md` (merged)
- ✅ `MASTER_CHECKLIST.md` (merged)
- ✅ `SYMLINK_STRUCTURE.md` (merged)
- ✅ `TASK_COMPLETION_REPORT.md` (merged)
- ✅ `MVP/document_checklist.md` (merged)

**Move to archive:**
```bash
cd docs
mv COMPLETE_DATA_INVENTORY.md archive/
mv GAP_ANALYSIS.md archive/
mv MASTER_CHECKLIST.md archive/
mv SYMLINK_STRUCTURE.md archive/
mv TASK_COMPLETION_REPORT.md archive/
mv MVP/document_checklist.md archive/
```

**Single source of truth**: This file (`DATA_PIPELINE_STATUS.md`)

---

## Summary

**Current State**: 75% Complete (3 of 4 Ohio corpuses built)

**Next Action**: Build Ohio Case Law LMDB (~12-24 hours)

**MVP Complete**: After Ohio Case Law LMDB is built

**Total Databases**: 20 LMDB databases (4 corpuses × 5 databases each)

**Architecture**: Zero-drift schema generation from Pydantic models

**Integration**: Symlinked to knowledge service via `lmdb_data/` folder

**Future**: Federal law (15 more databases) + Judge prediction (killer feature)

---

*This is the single source of truth for the ohio_code data pipeline. Keep this document updated as work progresses.*
