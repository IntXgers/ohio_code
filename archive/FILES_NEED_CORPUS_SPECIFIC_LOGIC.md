# Files That Need Corpus-Specific Logic Updates

**Date:** 2025-11-13
**Issue:** Files were cloned from ohio_revised without adapting logic for each corpus

---

## ❌ PROBLEM: Blindly Cloned Files

I cloned files to all corpuses but DID NOT update the corpus-specific logic. Every file still has Ohio Revised Code logic (section numbers like "123.45" instead of proper formats for each corpus).

---

## 📋 WHAT NEEDS TO BE FIXED

### Ohio Constitution

**Data Format:**
```json
{
  "header": "Article I, Section 1|Inalienable Rights",
  "article": "Article I|Bill of Rights",
  "paragraphs": ["..."]
}
```

**Section Number Format:** "Article I, Section 1" (NOT "123.45")

**Files Needing Updates:**

1. **`ohio_constitution/src/ohio_constitution/citation_analysis/citation_mapper.py`**
   - Line 48-54: Reference patterns (needs constitutional citation patterns)
   - Line 152-154: `extract_section_number()` (needs "Article I, Section 1" extraction)
   - Line 355: Print statement ("OHIO REVISED CODE" → "OHIO CONSTITUTION")
   - Line 382: Import path (wrong module)

2. **`ohio_constitution/src/ohio_constitution/citation_analysis/ohio_constitution_mapping.py`**
   - ENTIRE FILE is Ohio Revised Code title mappings
   - Needs Ohio Constitution article/section mapping instead
   - Should map "Article I" → "Bill of Rights", etc.

3. **`ohio_constitution/src/ohio_constitution/lmdb/auto_enricher.py`**
   - Needs constitutional enrichment fields (not criminal statute fields)
   - Should detect article types (rights, structure, amendments)

4. **`ohio_constitution/src/ohio_constitution/lmdb/build_comprehensive_lmdb.py`**
   - Line referencing section number extraction (needs Article format)
   - Source URL
   - Import paths

---

### Ohio Case Law

**Data Format:**
```json
{
  "header": "2023-Ohio-1234",
  "court": "Ohio Supreme Court",
  "decision_date": "2023-01-15",
  "paragraphs": ["..."],
  "citations": ["R.C. 2903.01", "O.A.C. 3701-17-01", "Ohio Const. Art. I § 1"]
}
```

**Section Number Format:** "2023-Ohio-1234" (case citations)

**Files Needing Updates:**

1. **`ohio_case_law/src/ohio_case_law/citation_analysis/citation_mapper.py`**
   - Reference patterns (needs multi-corpus citations: R.C., O.A.C., Ohio Const., USC, F.3d, etc.)
   - `extract_section_number()` (needs case citation extraction "2023-Ohio-1234")
   - Cross-corpus citation detection

2. **`ohio_case_law/src/ohio_case_law/citation_analysis/ohio_case_law_mapping.py`**
   - ENTIRE FILE is Ohio Revised Code mappings
   - Needs court hierarchy mapping instead
   - Should map courts: Ohio Supreme Court, Courts of Appeals (1st-12th District), etc.

3. **`ohio_case_law/src/ohio_case_law/lmdb/auto_enricher.py`**
   - Needs case-specific enrichment:
     - court_level (supreme_court, appeals, common_pleas)
     - case_type (criminal, civil, family)
     - decision_type (affirmed, reversed, remanded)
     - judge_name (for judge prediction later)

4. **`ohio_case_law/src/ohio_case_law/lmdb/build_comprehensive_lmdb.py`**
   - Case number extraction (not section number)
   - Multi-corpus citation linking
   - Court metadata

---

## ✅ Ohio Administrative Code - CORRECT

This one was actually built correctly because we did it together step-by-step. It has:
- Correct citation patterns (O.A.C. format, rule references)
- Correct section extraction (rule numbers)
- Agency mappings
- Everything adapted properly

---

## 🎯 WHAT TO DO NEXT

**Option 1: Fix Them Now**
- Go through each corpus systematically
- Update citation patterns, section extraction, enrichment fields
- Test each one

**Option 2: Wait Until Ready to Build**
- Ohio Constitution is next (fastest build ~5 min)
- Fix ohio_constitution files when ready to build
- Then fix ohio_case_law when ready for that build

**Option 3: Just Document for Now**
- This document serves as the spec
- When you're ready to build each corpus, reference this doc
- Update files at that time

---

## 📊 CORPUS-SPECIFIC DETAILS

### Ohio Constitution (~200 sections)

**Citation Patterns Needed:**
```python
[
    r'Article\s+([IVXLCDM]+),\s+Section\s+(\d+)',  # Article I, Section 1
    r'Art\.\s*([IVXLCDM]+)\s*§\s*(\d+)',            # Art. I § 1
    r'Ohio\s+Const\.\s+Art\.\s+([IVXLCDM]+)',       # Ohio Const. Art. I
]
```

**Section Extraction:**
```python
def extract_section_number(header: str) -> Optional[str]:
    match = re.search(r'Article\s+([IVXLCDM]+),\s+Section\s+(\d+)', header)
    return f"Article {match.group(1)}, Section {match.group(2)}" if match else None
```

**Enrichment Fields:**
```python
- article_type: "bill_of_rights" | "structure" | "amendment"
- rights_category: "fundamental_rights" | "government_structure" | "elections"
- complexity: 1-10
```

---

### Ohio Case Law (~500,000 cases)

**Citation Patterns Needed:**
```python
[
    r'(\d{4})-Ohio-(\d+)',                          # 2023-Ohio-1234
    r'R\.C\.\s+(\d{3,4}\.\d+)',                     # R.C. 2903.01
    r'O\.A\.C\.\s+(\d{4}-\d+-\d+)',                 # O.A.C. 3701-17-01
    r'Ohio\s+Const\.\s+Art\.\s+([IVXLCDM]+)\s+§\s+(\d+)',  # Ohio Const. Art. I § 1
    r'(\d+)\s+U\.S\.\s+(\d+)',                      # 123 U.S. 456 (SCOTUS)
    r'(\d+)\s+F\.3d\s+(\d+)',                       # 123 F.3d 456 (6th Circuit)
]
```

**Section Extraction:**
```python
def extract_case_number(header: str) -> Optional[str]:
    match = re.search(r'(\d{4})-Ohio-(\d+)', header)
    return f"{match.group(1)}-Ohio-{match.group(2)}" if match else None
```

**Enrichment Fields:**
```python
- court_level: "supreme_court" | "appeals" | "common_pleas"
- appellate_district: "1st" | "2nd" | ... | "12th" (for appeals)
- case_type: "criminal" | "civil" | "family" | "administrative"
- decision_type: "affirmed" | "reversed" | "remanded" | "vacated"
- judge_name: str (for judge prediction)
- decision_date: str
```

---

## 🚨 CRITICAL: Don't Run These Builds Yet

DO NOT run `build_comprehensive_lmdb.py` for ohio_constitution or ohio_case_law yet - the files aren't properly adapted and will fail or produce incorrect results.

Fix the logic FIRST, then build.

---

## ✅ Summary

- **Ohio Revised Code:** Working correctly
- **Ohio Administrative Code:** Working correctly
- **Ohio Constitution:** Files cloned but logic NOT adapted
- **Ohio Case Law:** Files cloned but logic NOT adapted

**Next Step:** Fix ohio_constitution files (smallest corpus, fastest to test)