# Corpus Cloning Complete - Adaptation Guide

**Date:** 2025-11-13
**Status:** Files cloned to all 3 corpuses ✅

---

## ✅ What Was Cloned

Successfully copied from `ohio_revised` to:
1. ✅ **Ohio Administration Code**
2. ✅ **Ohio Constitution**
3. ✅ **Ohio Case Law**

### Files Cloned Per Corpus

**Citation Analysis** (2 files):
- `citation_mapper.py` (unchanged - generic)
- `{corpus}_mapping.py` (renamed from ohio_revised_mapping.py)

**LMDB** (2 files):
- `auto_enricher.py` (unchanged - works for all)
- `build_comprehensive_lmdb.py` (unchanged - generic)

---

## 📋 What Needs Adaptation

### 1. Ohio Administration Code

**File:** `ohio_administration/src/ohio_administration/citation_analysis/ohio_admin_mapping.py`

**Changes Needed:**
```python
# Line 1: Update class name
class OhioRevisedMapping:  # CHANGE TO: OhioAdminMapping

# Line 10-15: Update citation patterns
CITATION_PATTERNS = [
    # Ohio Admin Code format: "O.A.C. 3701-17-01" or "Ohio Adm.Code 3701-17-01"
    r'(?:O\.A\.C\.|Ohio\s+Adm(?:\.|ministrative)\s*Code)\s+([\d-:]+)',

    # Also match internal refs: "rule 3701-17-01"
    r'rule\s+([\d-:]+)',

    # May reference Ohio Revised Code (cross-corpus)
    r'(?:section\s+)?(\d+\.\d+)\s+of\s+the\s+Revised\s+Code'
]

# Line 20: Update section number extraction
def extract_section_number(self, text: str) -> Optional[str]:
    # Admin code uses format: 3701-17-01 (chapter-rule-subrule)
    match = re.search(r'(\d{4}-\d{1,2}-\d{1,2})', text)
    return match.group(1) if match else None
```

**Data Structure:**
- Admin code sections use: `3701-17-01` format
- More verbose than Revised Code
- Often implements Revised Code statutes (cross-corpus citations)

---

### 2. Ohio Constitution

**File:** `ohio_constitution/src/ohio_constitution/citation_analysis/ohio_constitution_mapping.py`

**Changes Needed:**
```python
# Line 1: Update class name
class OhioRevisedMapping:  # CHANGE TO: OhioConstitutionMapping

# Line 10-15: Update citation patterns
CITATION_PATTERNS = [
    # Article and Section format: "Article I, Section 1" or "Art. I, § 1"
    r'(?:Article|Art\.?)\s+([IVX]+),?\s+(?:Section|§)\s+(\d+)',

    # May also reference Revised Code statutes (cross-corpus)
    r'(?:section\s+)?(\d+\.\d+)\s+of\s+the\s+Revised\s+Code'
]

# Line 20: Update section number extraction
def extract_section_number(self, text: str) -> Optional[str]:
    # Constitution uses: "Article_I_Section_1" or "I.1" format
    # Depends on your scraper's format - check data structure
    match = re.search(r'Article\s+([IVX]+).*?Section\s+(\d+)', text, re.IGNORECASE)
    if match:
        return f"{match.group(1)}.{match.group(2)}"  # e.g., "I.1"
    return None
```

**Data Structure:**
- Constitution sections use: Article + Section (e.g., "Article I, Section 1")
- Short corpus (~200 sections)
- Foundational - many reverse citations from statutes
- Few forward citations (doesn't cite much)

---

### 3. Ohio Case Law

**File:** `ohio_case_law/src/ohio_case_law/citation_analysis/ohio_case_law_mapping.py`

**Changes Needed:**
```python
# Line 1: Update class name
class OhioRevisedMapping:  # CHANGE TO: OhioCaseLawMapping

# Line 10-20: Update citation patterns
CITATION_PATTERNS = [
    # Ohio case citation: "2023-Ohio-1234"
    r'(\d{4}-Ohio-\d+)',

    # May also cite:
    # - Ohio Revised Code: "R.C. 2913.02"
    r'(?:R\.C\.|ORC)\s+(\d+\.\d+)',

    # - Ohio Admin Code: "O.A.C. 3701-17-01"
    r'(?:O\.A\.C\.|Ohio\s+Adm\.Code)\s+([\d-:]+)',

    # - Ohio Constitution: "Ohio Const. Art. I, § 1"
    r'Ohio\s+Const(?:\.|itution)\.?\s+Art(?:\.|icle)?\s+([IVX]+),?\s+§?\s*(\d+)',

    # - US Code: "42 U.S.C. § 1983" or "42 USC 1983"
    r'(\d+)\s+U\.?S\.?C\.?\s+§?\s*(\d+)',

    # - SCOTUS: "467 U.S. 837" (reporter citation)
    r'(\d+)\s+U\.S\.\s+(\d+)',

    # - Federal Circuit: "6th Cir." cases
    r'(\d+)\s+F\.\d+d\s+(\d+)',
]

# Line 30: Update section number extraction
def extract_section_number(self, text: str) -> Optional[str]:
    # Case law uses: "2023-Ohio-1234" format
    match = re.search(r'(\d{4}-Ohio-\d+)', text)
    return match.group(1) if match else None
```

**Data Structure:**
- Case citations: `2023-Ohio-1234` format
- Large corpus (~500,000 cases)
- Heavy cross-corpus citations (statutes, constitution, federal law)
- Important for judge prediction feature later

---

## 🔧 LMDB Builder Adaptations

The `build_comprehensive_lmdb.py` file **should work for all corpuses** with minimal changes:

### Update DATA_DIR path (line 398):

**Ohio Administration:**
```python
DATA_DIR = Path(__file__).parent.parent / "data"
```

**Ohio Constitution:**
```python
DATA_DIR = Path(__file__).parent.parent / "data"
```

**Ohio Case Law:**
```python
DATA_DIR = Path(__file__).parent.parent / "data"
```

### Update corpus file names (line 51, 404):

**Ohio Administration:**
```python
self.corpus_file = data_dir / "ohio_admin_code" / "ohio_admin_code_complete.jsonl"
corpus_file = DATA_DIR / "ohio_admin_code" / "ohio_admin_code_complete.jsonl"
```

**Ohio Constitution:**
```python
self.corpus_file = data_dir / "ohio_constitution" / "ohio_constitution_complete.jsonl"
corpus_file = DATA_DIR / "ohio_constitution" / "ohio_constitution_complete.jsonl"
```

**Ohio Case Law:**
```python
self.corpus_file = data_dir / "ohio_case_law_raw" / "ohio_caselaw_complete_filtered.jsonl"  # Or whatever your file is named
corpus_file = DATA_DIR / "ohio_case_law_raw" / "ohio_caselaw_complete_filtered.jsonl"
```

---

## 🎨 Auto-Enricher Adaptations

The `auto_enricher.py` **should work for all corpuses** BUT you may want to customize:

### Ohio Constitution - Add constitution-specific fields:

```python
# Add to EnrichmentData dataclass (line 25):
constitutional_provision: Optional[str] = None  # "bill_of_rights", "legislative", "executive", etc.
article_number: Optional[str] = None  # "I", "II", etc.
```

### Ohio Case Law - Add case-specific fields:

```python
# Add to EnrichmentData dataclass (line 25):
court_level: Optional[str] = None  # "supreme_court", "appeals", "common_pleas"
case_type: Optional[str] = None  # "criminal", "civil", "family", etc.
decision_type: Optional[str] = None  # "affirmed", "reversed", "remanded"
precedential_value: Optional[str] = None  # "binding", "persuasive"
judge_name: Optional[str] = None  # For judge prediction later
```

These are **optional enhancements**. The base 7 fields will work for all corpuses.

---

## 📂 Expected Data Structure

Before running citation analysis + LMDB build, verify your data files exist:

### Ohio Administration:
```
ohio_administration/data/
├── ohio_admin_code/
│   └── ohio_admin_code_complete.jsonl  # Must exist
├── citation_analysis/  # Will be created
└── enriched_output/    # Will be created
```

### Ohio Constitution:
```
ohio_constitution/data/
├── ohio_constitution/
│   └── ohio_constitution_complete.jsonl  # Must exist
├── citation_analysis/  # Will be created
└── enriched_output/    # Will be created
```

### Ohio Case Law:
```
ohio_case_law/data/
├── ohio_case_law_raw/
│   └── ohio_caselaw_complete_filtered.jsonl  # Must exist
├── citation_analysis/  # Will be created
└── enriched_output/    # Will be created
```

---

## 🚀 Next Steps

### For Each Corpus (in order):

1. **Update citation mapping file** with corpus-specific patterns
2. **Run citation analysis**:
   ```bash
   cd {corpus}/src/{corpus}/citation_analysis
   python ohio_{corpus}_mapping.py
   ```
3. **Update build_comprehensive_lmdb.py** with correct file paths
4. **Run LMDB build**:
   ```bash
   cd {corpus}/src/{corpus}/lmdb
   python build_comprehensive_lmdb.py
   ```
5. **Verify output**:
   ```bash
   ls -la {corpus}/data/enriched_output/comprehensive_lmdb/
   # Should show: primary.lmdb, citations.lmdb, reverse_citations.lmdb, chains.lmdb, metadata.lmdb
   ```
6. **Copy to dist/**:
   ```bash
   mkdir -p dist/{corpus}
   cp -r {corpus}/data/enriched_output/comprehensive_lmdb/* dist/{corpus}/
   ```

---

## ⚠️ Important Notes

1. **auto_enricher.py is corpus-agnostic** - Should work for all without changes (unless you want custom fields)

2. **Citation patterns MUST be adapted** - Each corpus has different citation formats

3. **Test with small sample first** - Use `limit` parameter in build_comprehensive_lmdb.py for testing

4. **Case Law is HUGE** (~500K cases) - Will take longest to process

5. **Constitution is tiny** (~200 sections) - Will be fastest

---

## 📊 Estimated Processing Times

| Corpus | Sections | Citation Analysis | LMDB Build | Total |
|--------|----------|------------------|------------|-------|
| Ohio Admin | ~40,000 | ~30 min | ~20 min | ~50 min |
| Ohio Constitution | ~200 | ~1 min | ~1 min | ~2 min |
| Ohio Case Law | ~500,000 | ~10 hours | ~2 hours | ~12 hours |

**Total for all 3:** ~13 hours

---

## ✅ Verification Checklist

After each corpus build:

- [ ] Citation map created (`citation_map.json`)
- [ ] Complex chains identified (`complex_chains.jsonl`)
- [ ] Citation analysis summary (`citation_analysis.json`)
- [ ] All 5 LMDB databases created
- [ ] Enrichment metadata present in sections
- [ ] Legal text unchanged in paragraphs field
- [ ] Metadata includes corpus statistics

---

**All files cloned successfully!** Ready for adaptation and building.