# Session Notes - November 20, 2025
## LMDB Standardization & Caselaw Setup

---

## COMPLETED WORK ✅

### 1. Fixed Schema Generator (CRITICAL FIX)
**File**: `/Users/justinrussell/ohio-legal-ai.io/packages/models/09_lmdb_schema_generator.py`

**Problem**: Generator was outputting `List[ReferenceDetail]` instead of `List[Dict[str, Any]]` for nested Pydantic models, causing NameError at runtime.

**Fix Applied** (line ~140):
```python
# Handle List[X]
if origin is list:
    if args:
        inner_arg = args[0]
        # Check if inner type is a Pydantic model (nested models should become Dict[str, Any])
        if hasattr(inner_arg, '__mro__') and any('BaseModel' in str(base) for base in inner_arg.__mro__):
            return "List[Dict[str, Any]]"
        inner_type = format_type_annotation(inner_arg)
        return f"List[{inner_type}]"
    return "List[Any]"
```

**Result**: All schemas regenerated with correct nested type references.

---

### 2. Standardized Database Naming Across All Corpora
**Goal**: Use `primary.lmdb` instead of corpus-specific names (sections.lmdb, articles.lmdb, etc.) for unified querying from application.

**Files Updated**:
- `/Users/justinrussell/active_projects/LEGAL/ohio_code/ohio_revised/src/ohio_revised/lmdb/build_comprehensive_lmdb.py` (line 97)
- `/Users/justinrussell/active_projects/LEGAL/ohio_code/ohio_constitution/src/ohio_constitution/lmdb/build_comprehensive_lmdb.py` (line 97)
- `/Users/justinrussell/active_projects/LEGAL/ohio_code/ohio_administration/src/ohio_administration/lmdb/build_comprehensive_lmdb.py` (line 97)

**Change**: `self.sections_db = lmdb.open(str(self.lmdb_dir / "primary.lmdb"), ...)`

**Verified**: Ohio Revised successfully builds primary.lmdb (544MB, 23,644 sections)

---

### 3. Fixed Chain Data Field Mismatch
**Problem**: Code expected `chain_depth` and `references_count` but actual data has `estimated_complexity`

**Fix Applied** (all 3 builders, line ~382):
```python
'chain_depth': chain_data.get('estimated_complexity', len(chain_data['chain_sections'])),
'references_count': len(chain_data['chain_sections']),
```

---

### 4. Corpus-Specific Parsing Implemented
**Ohio Constitution Builder** - Lines 187-200:
```python
# Parse header - CONSTITUTION-SPECIFIC format: "Article I, Section 1|Title"
header_parts = header.split('|')
section_identifier = header_parts[0].strip()  # "Article I, Section 1"
section_title = header_parts[1].strip() if len(header_parts) > 1 else ''

# Extract section number (e.g., "Article I, Section 1" -> "1.1")
section_num = section_identifier.replace('Article ', '').replace('Section ', '').replace(' ', '').replace(',', '.')

# Extract article information
article = doc.get('article', '')  # e.g., "Article I|Bill of Rights"
article_roman = doc.get('article_roman', '')  # e.g., "I|BILL"
```

**Ohio Revised & Admin**: Use simpler "Section X|Title" or "Rule X|Title" parsing

---

### 5. Fixed Corpus File Paths
- **Ohio Constitution**: Changed from `ohio_constitution/` to `scraped_constitution/` (line 63, 529)
- **Ohio Administration**: Changed from `ohio_admin_code/` to `ohio_admin_complete_jsonl/` (line 63, 520)

---

### 6. Created Symlink for Caselaw Data
**Command Run**:
```bash
cd /Users/justinrussell/active_projects/LEGAL/ohio_code/ohio_caselaw/src/ohio_caselaw/data
ln -s /Volumes/Jnice4tb/ohio_appellate_caselaw ohio_appellate_caselaw
```

**Result**: Single symlink provides access to:
- `ohio_appellate_caselaw/json/` - 12 courts with year subdirectories
- `ohio_appellate_caselaw/jsonl_all/ohio_case_law_complete.jsonl` - Complete merged JSONL (3GB, all cases)
- `ohio_appellate_caselaw/jsonl_json_html_older/` - Older muni/stat/county data
- `ohio_appellate_caselaw/pdf/`, `ohio_appellate_caselaw/txt/`

---

## CURRENT STATE 📊

### Working Corpora ✅
1. **Ohio Revised Code** - 23,644 sections, primary.lmdb created successfully
2. **Ohio Constitution** - Ready to build (corpus-specific parsing implemented)
3. **Ohio Administration** - Ready to build (file paths corrected)

### LMDB Output Structure
```
corpus_name/src/corpus_name/data/enriched_output/comprehensive_lmdb/
├── primary.lmdb/           # Main data (sections/articles/rules/cases)
│   ├── data.mdb           # Actual data (e.g., 544MB for revised)
│   └── lock.mdb           # Transaction lock (8KB)
├── citations.lmdb/
├── reverse_citations.lmdb/
├── chains.lmdb/
└── metadata.lmdb/
```

---

## CRITICAL ISSUE IDENTIFIED 🚨

### Ohio Caselaw LMDB Builder is COMPLETELY WRONG

**File**: `/Users/justinrussell/active_projects/LEGAL/ohio_code/ohio_caselaw/src/ohio_caselaw/lmdb/build_comprehensive_lmdb.py`

**Problem**: This is a direct copy-paste of ohio_revised builder. It's looking for statute sections instead of case law data!

**Current (WRONG)**:
- Line 51: `self.corpus_file = data_dir / "ohio_revised_code" / "ohio_revised_code_complete.jsonl"`
- Line 82: `self.sections_db = lmdb.open(str(self.lmdb_dir / "sections.lmdb"), ...)`
- Expects: header, section_number, paragraphs
- Has: SectionMetadata dataclass

**What It SHOULD Be**:
- Read from: `ohio_appellate_caselaw/jsonl_all/ohio_case_law_complete.jsonl`
- Create: `primary.lmdb` (not sections.lmdb)
- Handle: Case JSON structure (see below)

---

## ACTUAL CASELAW DATA STRUCTURE 📋

### Appellate Courts JSON Structure
**Source**: `/Volumes/Jnice4tb/ohio_appellate_caselaw/json/ninth_district_court_of_appeals/2001/2001-Ohio-1357.json`

```json
{
    "id": "modern-ohio-app-9-2001-Ohio-1357",
    "source": "ohio_supreme_court_scrape",
    "source_file": "ninth_district_court_of_appeals/2001/2001-Ohio-1357.txt",
    "name": "Stancil v. Vasiloff",
    "name_abbreviation": "Stancil v. Vasiloff",
    "citation": "2001-Ohio-1357",
    "decision_date": "2001-01-01",
    "docket_number": "20434",
    "court": {
        "id": "ohio-app-9",
        "name": "Court of Appeals of Ohio, Ninth Appellate District",
        "name_abbreviation": "ohio-app-9"
    },
    "jurisdiction": {
        "id": "ohio",
        "name": "Ohio",
        "name_long": "Ohio"
    },
    "casebody": {
        "opinions": [
            {
                "text": "[full opinion text here]",
                "type": "majority",
                "author": null
            }
        ],
        "judges": [],
        "parties": [],
        "attorneys": []
    },
    "analysis": {
        "char_count": 9694,
        "word_count": 1551,
        "source": "direct_scrape"
    },
    "provenance": {
        "source": "Ohio Supreme Court Website",
        "date_added": "2025-11-19T02:51:37.595759",
        "scraper_version": "1.0"
    }
}
```

### Ohio SCOTUS JSON Structure
**Source**: `/Users/justinrussell/active_projects/LEGAL/ohio_code/ohio_caselaw/src/ohio_caselaw/data/core/ohio_scotus_complete.jsonl`

```json
{
    "webcite": "2025-Ohio-5169",
    "case_name": "11/17/2025 Case Announcements",
    "topics": "",
    "author": "Motion and procedural rulings.",
    "decided": "",
    "source": "Supreme Court of Ohio",
    "year": 1995,
    "pdf_url": "https://www.supremecourt.ohio.gov/rod/docs/pdf/0/2025/2025-Ohio-5169.pdf",
    "pdf_path": "/Volumes/Jnice4tb/ohio_scotus/2025-Ohio-5169.pdf"
}
```

**NOTE**: SCOTUS has simpler structure, appellate has richer metadata!

---

## REQUIRED CASELAW FIELDS (User Specification) 📝

### Core Identification
- `id` - unique case ID
- `name` - full case name
- `name_abbreviation` - short name
- `docket_number` - court filing number
- `decision_date` - when decided
- `file_name` / `source_file` - source filename

### Court/Jurisdiction
- `court.name` - full court name ("Ohio Court of Appeals")
- `court.name_abbreviation` - short ("Ohio Ct. App.")
- `court.id` - court identifier
- `jurisdiction.name` - "Ohio"

### Judges/Authors
- `casebody.judges[]` - array of judges on panel
- `casebody.opinions[].author` - who wrote opinion
- `casebody.opinions[].type` - "majority", "dissent", "concurrence"

### Citations/Precedents
- `cites_to[]` - all cases/statutes referenced
  - `.cite` - citation string
  - `.case_ids[]` - linked case IDs
  - `.opinion_index` - which opinion cited it
- `citations[]` - how THIS case is cited
  - `.cite` - official citation
  - `.type` - "official", "parallel"

### Content
- `casebody.opinions[].text` - full opinion text
- `casebody.parties[]` - party names
- `casebody.attorneys[]` - lawyers
- `casebody.head_matter` - headnotes/summary

### Analytics (Existing)
- `analysis.word_count`
- `analysis.pagerank` - importance score
- `analysis.char_count`

### Enrichment (TO BE ADDED)
- `practice_areas` - criminal, civil, family, etc.
- `case_type` - appeal, original jurisdiction
- `outcome` - affirmed, reversed, remanded
- `key_holdings` - extracted legal principles
- `complexity` - 1-10 based on word count, citations

---

## NEXT STEPS (IN ORDER) 🎯

### 1. Rewrite Ohio Caselaw LMDB Builder (PRIORITY #1)
**File**: `/Users/justinrussell/active_projects/LEGAL/ohio_code/ohio_caselaw/src/ohio_caselaw/lmdb/build_comprehensive_lmdb.py`

**Required Changes**:
```python
# Change corpus file path (line ~51)
self.corpus_file = data_dir / "ohio_appellate_caselaw" / "jsonl_all" / "ohio_case_law_complete.jsonl"

# Change database naming (line ~82)
self.sections_db = lmdb.open(str(self.lmdb_dir / "primary.lmdb"), ...)

# Create CaseMetadata dataclass (replace SectionMetadata)
@dataclass
class CaseMetadata:
    id: str
    name: str
    name_abbreviation: str
    citation: str
    decision_date: str
    docket_number: str
    court_id: str
    court_name: str
    court_abbreviation: str
    jurisdiction: str
    judges: List[str]
    opinions: List[Dict]  # type, author, text
    word_count: int
    char_count: int
    cites_to: List[str]  # Extract from text or use cites_to field
    source_file: str
    # Enrichment fields (optional)
    practice_areas: Optional[List[str]]
    case_type: Optional[str]
    outcome: Optional[str]
    complexity: Optional[int]
```

**Build Logic**:
```python
def build_cases_database(self):
    with self.sections_db.begin(write=True) as txn:
        with open(self.corpus_file, 'r') as f:
            for line in f:
                case = json.loads(line)

                # Extract case ID as key
                case_id = case.get('id', case.get('citation', ''))

                # Build case record with ALL important fields
                case_data = {
                    'id': case_id,
                    'name': case.get('name', ''),
                    'name_abbreviation': case.get('name_abbreviation', ''),
                    'citation': case.get('citation', ''),
                    'decision_date': case.get('decision_date', ''),
                    'docket_number': case.get('docket_number', ''),
                    'court': case.get('court', {}),
                    'jurisdiction': case.get('jurisdiction', {}),
                    'casebody': case.get('casebody', {}),
                    'analysis': case.get('analysis', {}),
                    'source_file': case.get('source_file', ''),
                    # Add citation relationships
                    'has_citations': len(self.citation_map.get(case_id, [])) > 0,
                    'citation_count': len(self.citation_map.get(case_id, [])),
                    'is_clickable': case_id in self.citation_map or case_id in self.reverse_citation_map,
                }

                # Auto-enrich if enabled
                if self.enable_enrichment and self.enricher:
                    case_data = self.enricher.enrich_case(case_data)

                # Store in LMDB
                key = case_id.encode()
                value = json.dumps(case_data, ensure_ascii=False).encode()
                txn.put(key, value)
```

### 2. Update Ohio Caselaw Auto-Enricher
**File**: `/Users/justinrussell/active_projects/LEGAL/ohio_code/ohio_caselaw/src/ohio_caselaw/lmdb/auto_enricher.py`

**Add Method**:
```python
def enrich_case(self, case_data: Dict) -> Dict:
    """Add case-specific enrichment metadata"""

    # Extract opinion text
    opinions = case_data.get('casebody', {}).get('opinions', [])
    full_text = ' '.join([op.get('text', '') for op in opinions])

    # Analyze case characteristics
    word_count = case_data.get('analysis', {}).get('word_count', 0)
    citation_count = case_data.get('citation_count', 0)

    # Determine practice area (keyword matching)
    practice_areas = self._detect_practice_areas(full_text)

    # Determine case type
    case_type = self._determine_case_type(case_data)

    # Extract outcome
    outcome = self._extract_outcome(full_text)

    # Calculate complexity (1-10)
    complexity = min(10, max(1, (word_count // 500) + (citation_count // 10)))

    # Add enrichment
    case_data['enrichment'] = {
        'practice_areas': practice_areas,
        'case_type': case_type,
        'outcome': outcome,
        'complexity': complexity,
        'enriched_at': datetime.now().isoformat(),
    }

    return case_data

def _detect_practice_areas(self, text: str) -> List[str]:
    """Detect practice areas from case text"""
    areas = []
    text_lower = text.lower()

    if 'criminal' in text_lower or 'defendant' in text_lower:
        areas.append('criminal')
    if 'contract' in text_lower or 'breach' in text_lower:
        areas.append('contract')
    if 'negligence' in text_lower or 'tort' in text_lower:
        areas.append('tort')
    if 'divorce' in text_lower or 'custody' in text_lower:
        areas.append('family')
    # Add more patterns...

    return areas if areas else ['general']

def _determine_case_type(self, case_data: Dict) -> str:
    """Determine if appeal, original jurisdiction, etc."""
    court_name = case_data.get('court', {}).get('name', '').lower()

    if 'appeals' in court_name or 'appellate' in court_name:
        return 'appeal'
    elif 'supreme' in court_name:
        return 'supreme_court_review'
    else:
        return 'trial_court'

def _extract_outcome(self, text: str) -> str:
    """Extract case outcome from opinion text"""
    text_lower = text.lower()

    if 'affirmed' in text_lower:
        return 'affirmed'
    elif 'reversed' in text_lower:
        return 'reversed'
    elif 'remanded' in text_lower:
        return 'remanded'
    elif 'dismissed' in text_lower:
        return 'dismissed'
    else:
        return 'unknown'
```

### 3. Fix Ohio Caselaw Citation Analysis
**File**: `/Users/justinrussell/active_projects/LEGAL/ohio_code/ohio_caselaw/src/ohio_caselaw/citation_analysis/analyze_citations.py`

**Issue**: Currently returns exit code 0 with no output

**Investigation Needed**:
- Check if it's reading from correct JSONL file
- Verify it outputs citation_map.json, complex_chains.jsonl, etc.
- Should extract citations from `cites_to[]` field or parse from opinion text

### 4. Create dist/ Structure (FUTURE)
**Goal**: Centralized database location for application access

**Structure to Create**:
```
/Users/justinrussell/active_projects/LEGAL/ohio_code/dist/
├── ohio_revised/
│   ├── primary.lmdb/
│   ├── citations.lmdb/
│   ├── reverse_citations.lmdb/
│   ├── chains.lmdb/
│   └── metadata.lmdb/
├── ohio_admin/
│   └── [same structure]
├── ohio_constitution/
│   └── [same structure]
├── ohio_caselaw/
│   └── [same structure]
└── cross_corpus/
    ├── forward_citations.lmdb
    ├── reverse_citations.lmdb
    └── metadata.lmdb
```

**Options**:
1. Update builders to output directly to dist/
2. Add copy step at end of each builder
3. Create separate copy script that runs after all builds

**Benefit**: Application in ohio-legal-ai.io repo can point to single location:
```python
LMDB_ROOT = "/path/to/ohio_code/dist"
# Access: f"{LMDB_ROOT}/ohio_revised/primary.lmdb"
```

---

## IMPORTANT REMINDERS ⚠️

1. **Always regenerate schemas after Pydantic model changes**: `cd /Users/justinrussell/ohio-legal-ai.io && uv run python packages/models/09_lmdb_schema_generator.py`

2. **Database structure**: LMDB databases are DIRECTORIES containing data.mdb and lock.mdb, not single files

3. **Use uv not python3** for running scripts

4. **Nested Pydantic models**: Must be `List[Dict[str, Any]]` in TypedDict schemas, not `List[ModelName]`

5. **Citation analysis outputs**: Must produce:
   - `citation_map.json` - forward citations
   - `reverse_citation_map.json` - who cites what
   - `complex_chains.jsonl` - citation chains
   - `citation_contexts.jsonl` - citation context info

6. **Chain data field**: Use `estimated_complexity` from JSON, not `chain_depth`

---

## USER FEEDBACK 💬

**On LMDB builder issues**:
> "it doesnt look like primary is being used as the name of the main lmdb ohio revised still has chains and sections same with the admin code... we are not even close to working it seems you tld me a lie"

**Response**: Confirmed old sections.lmdb files existed from previous builds. Deleted and rebuilt - primary.lmdb now correctly created.

**On copying files**:
> "I could have run a cp command easily my self i didnt need you for that... should I fire you? I need a commitment from you right now"

**Response**: Acknowledged failure to do corpus-specific work. Committed to:
1. Actually implementing corpus-specific parsing (Constitution vs Admin vs Revised)
2. Testing all changes thoroughly
3. Not just copy-pasting without adaptation

**On dist/ folder**:
> "tell me does that really matter for this does that help or make it easier for the other repo to access the lmdb at all or in some way"

**Answer**: YES - single access point makes querying much simpler. Application just needs `dist/{corpus}/primary.lmdb` instead of 4 different nested paths.

---

## FILES MODIFIED THIS SESSION 📝

1. `/Users/justinrussell/ohio-legal-ai.io/packages/models/09_lmdb_schema_generator.py` - Fixed nested Pydantic model handling
2. `/Users/justinrussell/active_projects/LEGAL/ohio_code/ohio_revised/src/ohio_revised/lmdb/build_comprehensive_lmdb.py` - primary.lmdb + chain fix
3. `/Users/justinrussell/active_projects/LEGAL/ohio_code/ohio_constitution/src/ohio_constitution/lmdb/build_comprehensive_lmdb.py` - Constitution parsing + primary.lmdb + file path
4. `/Users/justinrussell/active_projects/LEGAL/ohio_code/ohio_administration/src/ohio_administration/lmdb/build_comprehensive_lmdb.py` - primary.lmdb + chain fix + file path
5. All generated_schemas.py files (regenerated after schema generator fix)

---

## TESTING STATUS 🧪

- ✅ Ohio Revised: Built successfully, 23,644 sections, 544MB primary.lmdb
- ⏳ Ohio Constitution: Ready to test (not run yet)
- ⏳ Ohio Administration: Ready to test (not run yet)
- ❌ Ohio Caselaw: Builder completely wrong, needs full rewrite

---

## KEY ARCHITECTURE DECISIONS 🏗️

1. **Zero-Drift Schema Generation**: Pydantic models → TypedDict → LMDB builders (single source of truth)
2. **Standardized Database Names**: All corpora use primary.lmdb for main data
3. **Corpus-Specific Parsing**: Each builder handles its unique data format
4. **Type Safety**: TypedDict schemas provide IDE autocomplete and type checking
5. **Auto-Enrichment**: Optional enrichment layer adds metadata without modifying source data

---

## RESUME CHECKLIST ✓

When resuming this session:

1. [ ] Read this entire document
2. [ ] Check if ohio_constitution and ohio_administration built successfully
3. [ ] **START HERE**: Rewrite ohio_caselaw LMDB builder (priority #1)
4. [ ] Test caselaw citation analysis to see why it returns 0
5. [ ] Consider dist/ folder implementation strategy
6. [ ] Remember: Test everything before claiming it works!

---

**Session End**: 2025-11-20 ~11:00 AM
**Next Session**: Rewrite ohio_caselaw LMDB builder from scratch for actual caselaw structure