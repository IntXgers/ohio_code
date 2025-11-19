# 🚀 Ohio Legal AI - Developer Checklist

**Last Updated**: 2025-11-15
**Project Status**: Phase 1 (Ohio Corpora) - 25% Complete

---

## 📊 PROJECT OVERVIEW

Building a comprehensive legal research platform with:
- Multi-corpus legal data (Ohio + Federal)
- Full citation graph analysis
- AI enrichment for context
- Fast LMDB query system
- Cross-corpus relationship mapping
- Interactive 3D graph visualization

---

## ✅ PHASE 1: OHIO STATE LAW (4 Corpora)

### 1. Ohio Revised Code (ORC) ✅ **COMPLETE**
**Status**: Production Ready
**Source**: codes.ohio.gov/ohio-revised-code
**Data**: 23,644 sections

#### Pipeline Status:
- ✅ Scraper: Fully implemented
- ✅ Data Transform: JSONL structured
- ✅ Citation Analysis: 23,644 forward + 15,515 reverse citations
- ✅ Complex Chains: 8,619 chains identified
- ✅ Enrichment: AI summaries, legal types, practice areas, key terms
- ✅ LMDB Build: 5 databases (sections, citations, reverse, chains, metadata)
- ✅ Graph Feature: `is_clickable` field added
- ✅ Testing: Inspection scripts verified

#### Deliverables:
```
ohio_revised/
├── src/ohio_revised/
│   ├── scraper/           ✅ Working
│   ├── citation_analysis/ ✅ Working
│   ├── enrichment/        ✅ Working
│   ├── lmdb/              ✅ Working (is_clickable added)
│   └── data/
│       ├── ohio_revised_code/         ✅ 23,644 sections
│       ├── citation_analysis/         ✅ Full graph
│       └── enriched_output/
│           └── comprehensive_lmdb/    ✅ 5 databases
```

---

### 2. Ohio Administrative Code (OAC) ⏳ **IN PROGRESS - 80%**
**Status**: Logic cloned, needs pipeline execution
**Source**: codes.ohio.gov/ohio-administrative-code

#### Pipeline Status:
- ✅ Scraper: Cloned, adapted for "Rule" naming
- ✅ Data Transform: Ready
- ✅ Citation Analysis: Logic cloned
- ✅ Enrichment: Logic cloned
- ✅ LMDB Build: Updated with `is_clickable`
- ⏳ **NEEDS**: Run full pipeline (scrape → analyze → enrich → build)
- ⏳ **NEEDS**: Verify data quality
- ⏳ **NEEDS**: Test LMDB queries

#### Next Steps:
1. Run scraper: `python code_scraper.py`
2. Run citation analysis
3. Run enrichment
4. Build LMDB with `is_clickable`
5. Verify with inspect_lmdb.py

---

### 3. Ohio Constitution ⏳ **IN PROGRESS - 70%**
**Status**: Logic cloned, needs customization + pipeline execution
**Source**: codes.ohio.gov/ohio-constitution

#### Pipeline Status:
- ✅ Scraper: Cloned
- ✅ Citation Analysis: Logic cloned
- ✅ LMDB Build: Logic cloned
- ⏳ **NEEDS**: Customize for Article/Section naming (not "Section X.XX")
- ⏳ **NEEDS**: Update citation patterns (constitution references differ)
- ⏳ **NEEDS**: Add `is_clickable` to LMDB builder
- ⏳ **NEEDS**: Run full pipeline
- ⏳ **NEEDS**: Test cross-references to ORC

#### Customizations Required:
```python
# Article I § 16 instead of Section 1.16
# Article naming: "Article I", "Article II"
# Section naming within articles
# Constitutional amendment tracking
```

---

### 4. Ohio Case Law ⏳ **IN PROGRESS - 60%**
**Status**: Logic cloned, needs major customization
**Source**: Pre-downloaded case archives

#### Pipeline Status:
- ✅ Data: Have case archives in zip files
- ✅ Basic structure: Cloned from ohio_revised
- ⏳ **NEEDS**: Case-specific citation parser (different from statutes)
- ⏳ **NEEDS**: Opinion extraction logic
- ⏳ **NEEDS**: Judge/court metadata handling
- ⏳ **NEEDS**: Add `is_clickable` to LMDB builder
- ⏳ **NEEDS**: Precedent relationship mapping
- ⏳ **NEEDS**: Run full pipeline

#### Special Requirements:
```python
# Case citations: "State v. Smith, 2021-Ohio-1234"
# Opinions: Majority, Concurring, Dissenting
# Court levels: Supreme, Appellate, Common Pleas
# Judge attribution
# Legal precedent chains (different from statute citations)
```

---

## 🇺🇸 PHASE 2: FEDERAL LAW (6+ Corpora)

### 5. SCOTUS (Supreme Court) ⏳ **PARTIAL DATA - 40%**
**Status**: Have 1937-1975, need 1976-present
**Location**: `/Scotus1937-1975/` (has HTML + TXT)

#### Data Inventory:
- ✅ Have: 1937-1975 (HTML + TXT format)
- ❌ Missing: 1976-2025 (48 years of opinions)

#### Pipeline Status:
- ❌ No scraper logic yet
- ❌ No structure (needs corpus/src/corpus layout)
- ❌ Citation analysis not adapted
- ❌ LMDB builder not created

#### Next Steps:
1. Move to `/federal/scotus/`
2. Create proper structure
3. Find data source for 1976-present (courtlistener.com?)
4. Build parser for both HTML and TXT
5. Adapt citation analysis for case law
6. Build LMDB

---

### 6. United States Code (USC) ❌ **MISSING - 0%**
**Status**: Not acquired yet
**Source**: TBD (uscode.house.gov?)

#### Needs:
- ❌ Data source identified
- ❌ Scraper built
- ❌ All pipeline steps
- ❌ Federal statute citation patterns

---

### 7. Code of Federal Regulations (CFR) ⏳ **DATA ONLY - 10%**
**Status**: Have XML data, no processing
**Location**: `/CodeOfFederalRegulations/` (XML format)

#### Data Inventory:
- ✅ Have: XML files
- ❌ No processing logic

#### Pipeline Status:
- ❌ No XML parser yet
- ❌ No structure
- ❌ No citation analysis
- ❌ No LMDB builder

#### Next Steps:
1. Move to `/federal/cfr/`
2. Build XML parser
3. Create proper structure
4. Adapt pipeline for federal regulations
5. Map CFR ↔ USC relationships

---

### 8. Statute Compilations ⏳ **DATA ONLY - 10%**
**Status**: Have XML data, unclear purpose
**Location**: `/StatuteCompilations/` (XML format)

#### Questions:
- ❓ What statutes are these?
- ❓ Federal or state?
- ❓ How do they relate to USC/ORC?

#### Needs:
- Clarify purpose and scope
- Determine if separate corpus or supplement
- Build processing logic

---

### 9. Sixth District Court of Appeals ⏳ **DATA ONLY - 10%**
**Status**: Have data, no processing
**Location**: `/sixth_court_appeals/` + CSV.BZ2 at root

#### Data Inventory:
- ✅ Have: CSV.BZ2 files
- ❓ Format unclear (court records? opinions?)

#### Needs:
- Inspect CSV structure
- Determine data type (opinions, dockets, metadata)
- Build parser
- Integrate with Ohio Case Law

---

## 👨‍⚖️ PHASE 3: JUDGE & COURT DATA (4 Datasets)

### 10. Judge Opinions - People DB (People) ✓ **DATA ACQUIRED**
**File**: `people-db-people-2025-10-31_JudgeData.csv.bz2` (445KB)
**Purpose**: Judge biographical data and opinion authorship

#### Status:
- ✅ Data file present
- ❌ Not extracted/inspected
- ❌ Schema unknown
- ❌ Integration plan needed

#### Likely Use:
- Link judges to their opinions
- Track judicial history
- Enable "ask the assistant about judge X"
- Graph nodes for judges

---

### 11. Judge Opinions - People DB (Positions) ✓ **DATA ACQUIRED**
**File**: `people-db-positions-2025-10-31_JudgeData.csv.bz2` (1.0MB)
**Purpose**: Judge positions/appointments over time

#### Status:
- ✅ Data file present
- ❌ Not extracted/inspected
- ❌ Schema unknown

#### Likely Use:
- Track when judges served on which courts
- Historical context for opinions
- Judicial appointment timeline

---

### 12. Courts Database ✓ **DATA ACQUIRED**
**File**: `courts-2025-10-31.csv.bz2` (79KB)
**Purpose**: Court metadata and hierarchy

#### Status:
- ✅ Data file present
- ❌ Not extracted/inspected
- ❌ Schema unknown

#### Likely Use:
- Court hierarchy (Supreme → Appellate → Trial)
- Jurisdiction mapping
- Court location/type metadata

---

### 13. Dockets Database ✓ **DATA ACQUIRED**
**File**: `dockets-2025-10-31.csv.bz2` (4.3GB) ⚠️ **LARGE**
**Purpose**: Case docket information (TBD - why needed?)

#### Status:
- ✅ Data file present (4.3GB - in .gitignore)
- ❌ Not extracted/inspected
- ❌ Schema unknown
- ❓ **Why needed?** (Sonnet 4.5 recommended - verify use case)

#### Questions:
- What's in the dockets?
- How does this enhance the legal research?
- Case tracking? Filing history?

---

## 🌐 PHASE 4: CROSS-CORPUS INTEGRATION

### 14. Master Cross-Corpus LMDB ❌ **NOT STARTED - 0%**
**Status**: Planned for after all corpora complete
**Purpose**: Map relationships BETWEEN corpora

#### Prerequisites:
- ✅ Ohio Revised (done)
- ⏳ Ohio Admin (in progress)
- ⏳ Ohio Constitution (in progress)
- ⏳ Ohio Case Law (in progress)
- ❌ Federal corpora (not started)

#### Will Enable:
```python
{
  "section": "ORC-2913.02",
  "cross_corpus_citations": {
    "cites": [
      {"corpus": "ohio_constitution", "ref": "Art-I-16"},
      {"corpus": "cfr", "ref": "21-CFR-1304.11"}
    ],
    "cited_by": [
      {"corpus": "ohio_case_law", "case": "State v. Smith"},
      {"corpus": "ohio_admin", "rule": "123:1-01"}
    ]
  }
}
```

#### Next Steps:
1. Wait for all corpora to have LMDBs
2. Build cross-corpus citation extractor
3. Create unified graph schema
4. Build master LMDB with all relationships
5. Enable full legal system navigation

---

## 📁 RECOMMENDED FOLDER RESTRUCTURE

```
ohio_code/
├── ohio/                    ← Ohio State Law
│   ├── revised/            ✅ DONE
│   ├── administration/     ⏳ 80%
│   ├── constitution/       ⏳ 70%
│   └── case_law/          ⏳ 60%
│
├── federal/                ← Federal Law (organize here)
│   ├── scotus/            ⏳ 40% (1937-1975 only)
│   ├── usc/               ❌ Missing
│   ├── cfr/               ⏳ 10% (XML only)
│   ├── sixth_appeals/     ⏳ 10%
│   └── statute_compilations/ ⏳ 10% (unclear purpose)
│
├── judges/                ← Judge & Court Data
│   ├── people/           ✓ CSV acquired
│   ├── positions/        ✓ CSV acquired
│   ├── courts/           ✓ CSV acquired
│   └── dockets/          ✓ CSV acquired (4.3GB)
│
├── cross_corpus/          ← Master Integration (future)
│   └── unified_lmdb/     ❌ Not started
│
├── docs/                  ← Documentation
└── scripts/              ← Build scripts
```

---

## 🎯 CURRENT PRIORITY (Finish Ohio Law First)

### Immediate Next Steps:

1. **Ohio Administration** (1-2 days)
   - Run full pipeline
   - Verify LMDB with `is_clickable`
   - Test queries

2. **Ohio Constitution** (2-3 days)
   - Customize Article/Section naming
   - Add `is_clickable` to builder
   - Run full pipeline
   - Test constitutional citations

3. **Ohio Case Law** (3-5 days)
   - Build case citation parser
   - Adapt enrichment for opinions
   - Add `is_clickable` to builder
   - Run full pipeline
   - Test precedent chains

**Target**: All 4 Ohio corpora complete by end of month

---

## 🔧 TECHNICAL DEBT & MISSING PIECES

### Required for Each Corpus:
- [x] Scraper/Data Loader
- [x] Citation Analysis
- [x] Enrichment (AI summaries)
- [x] LMDB Builder
- [x] `is_clickable` field for graph
- [x] Inspection/Testing tools

### Global Infrastructure Needed:
- [ ] USC data source and scraper
- [ ] SCOTUS 1976-present data source
- [ ] Judge data ETL pipeline
- [ ] Cross-corpus citation extractor
- [ ] Master LMDB builder
- [ ] Unified query API

### Documentation Needed:
- [ ] Architecture diagram (all corpora + relationships)
- [ ] API documentation (LMDB query patterns)
- [ ] Data flow diagrams
- [ ] Citation pattern guide (per corpus type)

---

## 📊 PROGRESS SUMMARY

| Corpus | Scraper | Analysis | Enrich | LMDB | is_clickable | Status |
|--------|---------|----------|--------|------|--------------|--------|
| **OHIO** |
| ORC | ✅ | ✅ | ✅ | ✅ | ✅ | **DONE** |
| OAC | ✅ | ✅ | ✅ | ✅ | ✅ | 80% - Run pipeline |
| Constitution | ✅ | ⏳ | ⏳ | ⏳ | ❌ | 70% - Customize + run |
| Case Law | ⏳ | ⏳ | ⏳ | ⏳ | ❌ | 60% - Major work |
| **FEDERAL** |
| SCOTUS | ❌ | ❌ | ❌ | ❌ | ❌ | 40% - Need 1976+ |
| USC | ❌ | ❌ | ❌ | ❌ | ❌ | 0% - Missing |
| CFR | ❌ | ❌ | ❌ | ❌ | ❌ | 10% - XML only |
| Sixth Appeals | ❌ | ❌ | ❌ | ❌ | ❌ | 10% - CSV only |
| Statute Comp | ❌ | ❌ | ❌ | ❌ | ❌ | 10% - Unclear |
| **JUDGES** |
| People DB | ❌ | - | - | ❌ | - | Data only |
| Positions DB | ❌ | - | - | ❌ | - | Data only |
| Courts DB | ❌ | - | - | ❌ | - | Data only |
| Dockets DB | ❌ | - | - | ❌ | - | Data only |
| **INTEGRATION** |
| Cross-Corpus | - | ❌ | - | ❌ | - | Not started |

**Overall Progress**: ~25% (1 of 4 Ohio corpora done, 0 of 5+ federal)

---

## 🎯 SUCCESS CRITERIA

### Phase 1 Complete When:
- ✅ All 4 Ohio corpora have full LMDBs
- ✅ All have `is_clickable` for graph
- ✅ Citation analysis works across all
- ✅ Can query any Ohio legal reference instantly

### Phase 2 Complete When:
- ✅ All federal corpora processed
- ✅ Judge data integrated
- ✅ Federal ↔ Ohio citations mapped

### Phase 3 Complete When:
- ✅ Cross-corpus LMDB built
- ✅ Can navigate full legal graph
- ✅ Frontend displays unified results
- ✅ Graph shows all relationships

---

## 📝 NOTES

- **is_clickable**: Critical for UX - marks sections with graph data
- **Citation patterns**: Each corpus type has unique citation format
- **Federal priority**: Get USC before other federal sources (most cited)
- **Judge data**: V2 feature - enable "ask about this judge's rulings"
- **Dockets**: Verify actual use case before processing 4.3GB

---

**Next Review**: After Ohio Administration pipeline completes