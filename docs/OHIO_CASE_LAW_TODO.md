# Ohio Case Law - Implementation Plan

**Status**: Ready to implement
**Complexity**: High (different from statute corpora)
**Estimated Time**: 4-6 hours

---

## 📊 Current State

**Data Available:**
- ✅ 9,369 cases in `ohio_caselaw_complete_filtered/ohio_case_law_complete.jsonl`
- ✅ Raw case files in various formats
- ✅ LMDB builder script exists (`build_comprehensive_lmdb.py`)
- ✅ Auto-enricher exists

**Data Structure (Different from Statutes):**
```json
{
  "case_id": "...",
  "name": "Shafher v. State",
  "name_abbreviation": "...",
  "decision_date": "1851-12",
  "docket_number": "...",
  "reporter": "...",
  "citation": "...",
  "all_citations": [...],
  "court_name": "...",
  "court_abbreviation": "...",
  "court_id": "...",
  "jurisdiction": "...",
  "opinion_text": "...",
  "parties": "...",
  "judges": "..."
}
```

---

## 🔧 Required Customizations

### 1. **Update LMDB Builder** (`build_comprehensive_lmdb.py`)

Currently expects statute format. Needs to handle case law format:

#### Changes Needed:

**A. Corpus File Path:**
```python
# Change from:
self.corpus_file = data_dir / "ohio_revised_code" / "ohio_revised_code_complete.jsonl"

# To:
self.corpus_file = data_dir / "ohio_caselaw_complete_filtered" / "ohio_case_law_complete.jsonl"
```

**B. Section Parsing Logic:**
```python
# Cases don't have "header" field
# Instead use:
# - case_id as unique identifier
# - name / name_abbreviation for display
# - citation for reference
```

**C. Add Case-Specific Fields:**
```python
section_data = {
    'case_id': doc.get('case_id'),
    'case_name': doc.get('name'),
    'name_abbreviation': doc.get('name_abbreviation'),
    'citation': doc.get('citation'),
    'all_citations': doc.get('all_citations', []),
    'decision_date': doc.get('decision_date'),
    'docket_number': doc.get('docket_number'),
    'court_name': doc.get('court_name'),
    'court_abbreviation': doc.get('court_abbreviation'),
    'jurisdiction': doc.get('jurisdiction'),
    'opinion_text': doc.get('opinion_text', ''),  # Full opinion
    'parties': doc.get('parties', ''),
    'judges': doc.get('judges', ''),
    'word_count': len(doc.get('opinion_text', '').split()),

    # Citation analysis (needs custom parser)
    'has_citations': False,  # TODO: Parse from opinion_text
    'citation_count': 0,
    'cites_statutes': [],  # References to ORC, OAC, etc.
    'cites_cases': [],      # References to other cases
    'is_clickable': False,  # TODO: After citation analysis
    'scraped_date': datetime.now().isoformat()
}
```

**D. Add Reverse Citation Map:**
```python
# Same as other corpora
self.reverse_citation_map: Dict[str, Set[str]] = {}
```

**E. Calculate is_clickable:**
```python
# After citation analysis
has_forward_citations = case_id in self.citation_map
has_reverse_citations = case_id in self.reverse_citation_map
is_clickable = has_forward_citations or has_reverse_citations
```

---

### 2. **Create Case Law Citation Parser**

Cases cite differently than statutes:
- **Statute citations**: "R.C. 2913.02", "O.A.C. 123:1-01"
- **Case citations**: "State v. Smith, 123 Ohio St.3d 456", "2021-Ohio-1234"

**New file needed:** `ohio_case_law/src/ohio_case_law/citation_analysis/case_citation_parser.py`

```python
class CaseCitationParser:
    """Parse citations from case opinion text"""

    def extract_statute_citations(self, opinion_text: str) -> List[str]:
        """Extract ORC, OAC, Constitution citations"""
        # R.C. 2913.02
        # O.A.C. 123:1-01
        # Ohio Constitution Article I, Section 1
        pass

    def extract_case_citations(self, opinion_text: str) -> List[str]:
        """Extract case-to-case citations"""
        # State v. Smith, 123 Ohio St.3d 456
        # 2021-Ohio-1234
        # App.R. 12
        pass

    def extract_all_citations(self, opinion_text: str) -> Dict:
        """Return both types"""
        return {
            'statute_citations': self.extract_statute_citations(opinion_text),
            'case_citations': self.extract_case_citations(opinion_text),
        }
```

---

### 3. **Update Auto-Enricher** (if needed)

Current enricher works on statutes. May need case-specific enrichment:

```python
# Case-specific enrichment
enrichment = {
    'summary': "...",  # AI summary of holding
    'legal_issues': [...],  # Key issues decided
    'procedural_posture': "...",  # Appeal, original, etc.
    'outcome': "...",  # Affirmed, reversed, remanded
    'key_holdings': [...],  # Main legal principles
    'statutes_applied': [...],  # Which laws were interpreted
    'precedent_value': "...",  # High, medium, low
}
```

---

### 4. **Update Citation Mapper**

Existing `citation_mapper.py` expects statute format.

**Options:**
1. Create new `case_citation_mapper.py` specifically for cases
2. Update existing mapper to handle both formats

**Recommended:** Create case-specific mapper that:
- Parses opinion text for citations
- Builds case-to-case reference graph
- Builds case-to-statute reference graph
- Identifies precedent relationships

---

### 5. **Add Inspection Script**

Copy and update `inspect_lmdb.py` to show case-specific fields:

```python
important_fields = [
    'case_id',
    'case_name',
    'citation',
    'decision_date',
    'court_name',
    'is_clickable',
    'has_citations',
    'citation_count',
    'cites_statutes',
    'cites_cases'
]
```

---

## 📝 Implementation Steps

### Phase 1: Prepare Data (30 min)
1. ✅ Verify ohio_case_law_complete.jsonl format
2. ✅ Count entries (9,369 cases)
3. ⏳ Sample 5-10 cases to understand citation patterns
4. ⏳ Document common citation formats

### Phase 2: Build Citation Parser (2 hours)
1. ⏳ Create `case_citation_parser.py`
2. ⏳ Implement statute citation regex patterns
3. ⏳ Implement case citation regex patterns
4. ⏳ Test on sample opinions
5. ⏳ Handle edge cases (parallel citations, etc.)

### Phase 3: Update LMDB Builder (1 hour)
1. ⏳ Add `reverse_citation_map`
2. ⏳ Update corpus file path
3. ⏳ Change section parsing to case parsing
4. ⏳ Add case-specific fields
5. ⏳ Add `is_clickable` calculation
6. ⏳ Update build methods for case format

### Phase 4: Run Citation Analysis (30 min)
1. ⏳ Create `case_citation_mapper.py`
2. ⏳ Run citation analysis on all 9,369 cases
3. ⏳ Generate citation_map.json
4. ⏳ Generate complex_chains.jsonl (precedent chains)

### Phase 5: Build LMDB (30 min)
1. ⏳ Run `build_comprehensive_lmdb.py`
2. ⏳ Verify all 5 databases created
3. ⏳ Check `is_clickable` field present

### Phase 6: Verify & Test (30 min)
1. ⏳ Update `inspect_lmdb.py` title
2. ⏳ Run inspection
3. ⏳ Verify case data structure
4. ⏳ Test sample queries
5. ⏳ Verify is_clickable accuracy

---

## 🎯 Expected Results

**LMDB Databases:**
```
✓ sections.lmdb:          9,369 entries (cases)
✓ citations.lmdb:         ~5,000-7,000 entries (estimated)
✓ reverse_citations.lmdb: ~3,000-5,000 entries (estimated)
✓ chains.lmdb:            ~500-1,000 precedent chains (estimated)
✓ metadata.lmdb:          ~9,400 entries
```

**Each case will have:**
- Full opinion text
- Case metadata (name, citation, date, court, judges)
- `is_clickable: true/false` for graph
- Citations to statutes (ORC, OAC, Constitution)
- Citations to other cases
- Reverse citations (cases that cite this one)
- AI enrichment (summary, holdings, issues)

---

## 🚨 Challenges & Considerations

### 1. **Citation Parsing Complexity**
- Cases use many citation formats
- Need to handle:
  - Ohio Supreme Court: `123 Ohio St.3d 456`
  - Ohio Appeals: `2021-Ohio-1234`
  - Federal: `123 F.3d 456`
  - Old format: `1 Ohio 123`
  - Parallel citations: `123 Ohio St.3d 456, 789 N.E.2d 123`

### 2. **Large Opinion Text**
- Some opinions are 50+ pages
- Need to handle long text in LMDB
- Consider truncating for display, keeping full text in separate field

### 3. **Cross-Corpus Citations**
- Cases cite statutes (ORC, OAC)
- Cases cite constitution
- Need to track these for cross-corpus graph

### 4. **Precedent vs. Citation**
- Not all case citations are precedent
- Need to distinguish:
  - Binding precedent (followed)
  - Persuasive authority (cited)
  - Distinguished (rejected)
  - Overruled (no longer valid)

### 5. **Court Hierarchy**
- Ohio Supreme Court (highest)
- Ohio Appeals Courts (by district)
- Common Pleas Courts (trial level)
- Graph should reflect hierarchy

---

## 🔗 Integration with Other Corpora

Once complete, cases will link to:
- **Ohio Revised Code**: When cases interpret statutes
- **Ohio Administrative Code**: When cases interpret rules
- **Ohio Constitution**: When cases involve constitutional issues

**Example Cross-Corpus Connection:**
```
Case: State v. Smith (2021-Ohio-1234)
  ├─ Cites: ORC 2913.02 (Theft statute)
  ├─ Cites: OAC 123:1-01 (Admin rule)
  ├─ Cites: Ohio Constitution Article I, § 16 (Due process)
  └─ Cited by: 15 later cases
```

---

## 📊 Priority vs. Complexity

**Priority: Medium-High**
- Needed for complete Ohio legal system
- Enables case law research
- Critical for lawyer/researcher use case

**Complexity: High**
- Most complex of 4 Ohio corpora
- Different data structure
- Citation parsing is non-trivial
- Requires legal domain knowledge

**Recommendation:**
- Complete after federal statute corpora (USC, CFR)
- Or complete now to finish all Ohio law first
- Either approach is valid

---

## ✅ Next Session Checklist

When ready to implement:

1. Start with citation parser
2. Test on 10-20 sample cases
3. Iterate until accurate
4. Then update LMDB builder
5. Run on full dataset
6. Verify and test

**Estimated Total Time: 4-6 hours of focused work**

---

**Status**: Documented and ready for implementation
**Blocker**: None (all data available)
**Dependencies**: None (can be done now)
