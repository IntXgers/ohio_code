# Cross-Corpus Citation Architecture

## The Problem

**Intra-corpus citations** (already built):
- Ohio Revised Code section 2913.02 → references → Ohio Revised Code section 2913.01 ✅
- Ohio Case Law case A → cites → Ohio Case Law case B ✅

**Cross-corpus citations** (need to build):
- Ohio Admin Code rule → references → Ohio Revised Code statute ❌
- Ohio Case Law case → cites → Ohio Revised Code statute ❌
- Ohio Constitution Article → references → Ohio Revised Code statute ❌

## Solution: Cross-Corpus Citation Database

### Architecture Option 1: Separate Cross-Corpus LMDB (Recommended)

```
ohio_code/dist/
├── ohio_revised/                (5 databases - intra-corpus)
├── ohio_administration/         (5 databases - intra-corpus)
├── ohio_constitution/           (5 databases - intra-corpus)
├── ohio_case_law/               (5 databases - intra-corpus)
└── cross_corpus/                (NEW - cross-corpus citations)
    ├── forward_citations.lmdb   # What does this reference in other corpuses?
    ├── reverse_citations.lmdb   # What in other corpuses references this?
    └── metadata.lmdb            # Cross-corpus statistics
```

### Schema Design

#### forward_citations.lmdb (Cross-Corpus)

**Key:** `{source_corpus}:{source_section}`
**Example:** `ohio_administration:3701-17-01`

```json
{
  "source_corpus": "ohio_administration",
  "source_section": "3701-17-01",
  "source_title": "Hospital Licensing Rules",

  "cross_references": [
    {
      "target_corpus": "ohio_revised",
      "target_section": "3727.01",
      "target_title": "Hospital Definitions",
      "relationship_type": "implements",  // implements, cites, references, defines
      "context_snippet": "...as defined in section 3727.01 of the Revised Code..."
    },
    {
      "target_corpus": "ohio_revised",
      "target_section": "3727.02",
      "target_title": "Hospital Requirements",
      "relationship_type": "implements"
    }
  ],

  "reference_count": 2,
  "corpuses_referenced": ["ohio_revised"]
}
```

#### reverse_citations.lmdb (Cross-Corpus)

**Key:** `{target_corpus}:{target_section}`
**Example:** `ohio_revised:3727.01`

```json
{
  "target_corpus": "ohio_revised",
  "target_section": "3727.01",
  "target_title": "Hospital Definitions",

  "referenced_by": [
    {
      "source_corpus": "ohio_administration",
      "source_section": "3701-17-01",
      "source_title": "Hospital Licensing Rules",
      "relationship_type": "implements"
    },
    {
      "source_corpus": "ohio_case_law",
      "source_section": "2023-Ohio-1234",
      "source_title": "State v. Hospital Corp",
      "relationship_type": "cites"
    }
  ],

  "referenced_by_count": 2,
  "referencing_corpuses": ["ohio_administration", "ohio_case_law"]
}
```

#### metadata.lmdb (Cross-Corpus)

```json
{
  "total_cross_references": 15000,
  "build_date": "2025-11-13",
  "version": "1.0",

  "corpus_interconnections": {
    "ohio_administration": {
      "references_ohio_revised": 8500,
      "references_ohio_constitution": 150,
      "total_outbound": 8650
    },
    "ohio_case_law": {
      "cites_ohio_revised": 50000,
      "cites_ohio_constitution": 2000,
      "cites_ohio_administration": 1500,
      "total_outbound": 53500
    },
    "ohio_revised": {
      "referenced_by_ohio_administration": 8500,
      "referenced_by_ohio_case_law": 50000,
      "total_inbound": 58500
    }
  },

  "relationship_types": {
    "implements": 8500,    // Admin code implements statute
    "cites": 53500,        // Case law cites statute/rule
    "references": 2000,    // General reference
    "defines": 500         // Provides definitions for
  }
}
```

---

## Implementation Plan

### Phase 1: Cross-Corpus Citation Analysis

Create `cross_corpus_citation_mapper.py`:

```python
"""Cross-corpus citation mapper
Identifies citations that span multiple corpuses
"""

class CrossCorpusCitationMapper:
    def __init__(self, corpuses_dir: Path):
        self.corpuses = {
            'ohio_revised': corpuses_dir / 'ohio_revised' / 'data',
            'ohio_administration': corpuses_dir / 'ohio_administration' / 'data',
            'ohio_constitution': corpuses_dir / 'ohio_constitution' / 'data',
            'ohio_case_law': corpuses_dir / 'ohio_case_law' / 'data'
        }

    def analyze_cross_references(self):
        """Find all citations that cross corpus boundaries"""
        cross_refs = []

        for source_corpus, source_path in self.corpuses.items():
            # Load source corpus jsonl
            corpus_file = source_path / f"{source_corpus}_complete.jsonl"

            for line in open(corpus_file):
                doc = json.loads(line)
                section_num = self._extract_section_number(doc)
                full_text = '\n'.join(doc.get('paragraphs', []))

                # Find citations to OTHER corpuses
                for target_corpus in self.corpuses.keys():
                    if target_corpus == source_corpus:
                        continue  # Skip intra-corpus (already handled)

                    # Extract citations to target corpus
                    citations = self._extract_citations(
                        full_text,
                        target_corpus
                    )

                    for cited_section in citations:
                        cross_refs.append({
                            'source_corpus': source_corpus,
                            'source_section': section_num,
                            'target_corpus': target_corpus,
                            'target_section': cited_section,
                            'relationship_type': self._infer_relationship(
                                source_corpus,
                                target_corpus
                            )
                        })

        return cross_refs

    def _extract_citations(self, text: str, target_corpus: str) -> List[str]:
        """Extract citations to a specific corpus"""
        if target_corpus == 'ohio_revised':
            # Match "section 3727.01 of the Revised Code"
            # Match "R.C. 3727.01"
            # Match "ORC 3727.01"
            pattern = r'(?:section\s+)?(\d+\.\d+)\s+(?:of\s+the\s+Revised\s+Code|R\.C\.|ORC)'

        elif target_corpus == 'ohio_administration':
            # Match "Ohio Adm.Code 3701-17-01"
            # Match "O.A.C. 3701-17-01"
            pattern = r'(?:Ohio\s+Adm\.Code|O\.A\.C\.)\s+([\d-:]+)'

        elif target_corpus == 'ohio_constitution':
            # Match "Ohio Constitution, Article I, Section 1"
            # Match "Ohio Const. Art. I, § 1"
            pattern = r'Ohio\s+Const(?:itution)?\.?\s+Art(?:icle|\.)?\s+([IVX]+),?\s+(?:Section|§)\s+(\d+)'

        elif target_corpus == 'ohio_case_law':
            # Match "State v. Smith, 2023-Ohio-1234"
            pattern = r'\d{4}-Ohio-\d+'

        return re.findall(pattern, text, re.IGNORECASE)

    def _infer_relationship(self, source: str, target: str) -> str:
        """Infer relationship type based on corpus types"""
        if source == 'ohio_administration' and target == 'ohio_revised':
            return 'implements'  # Admin code implements statutes
        elif source == 'ohio_case_law':
            return 'cites'  # Case law cites everything
        elif target == 'ohio_constitution':
            return 'references'  # Constitution is foundational
        else:
            return 'references'  # Generic reference
```

### Phase 2: Build Cross-Corpus LMDB

Create `build_cross_corpus_lmdb.py`:

```python
"""Build cross-corpus citation LMDB databases"""

class CrossCorpusLMDBBuilder:
    def __init__(self, data_dir: Path, cross_refs: List[Dict]):
        self.data_dir = data_dir
        self.cross_refs = cross_refs
        self.lmdb_dir = data_dir / 'cross_corpus'
        self.lmdb_dir.mkdir(parents=True, exist_ok=True)

    def build_forward_citations(self):
        """Build forward cross-corpus citations"""
        # Group by source
        forward_map = {}

        for ref in self.cross_refs:
            source_key = f"{ref['source_corpus']}:{ref['source_section']}"

            if source_key not in forward_map:
                forward_map[source_key] = {
                    'source_corpus': ref['source_corpus'],
                    'source_section': ref['source_section'],
                    'cross_references': [],
                    'corpuses_referenced': set()
                }

            forward_map[source_key]['cross_references'].append({
                'target_corpus': ref['target_corpus'],
                'target_section': ref['target_section'],
                'relationship_type': ref['relationship_type']
            })
            forward_map[source_key]['corpuses_referenced'].add(ref['target_corpus'])

        # Write to LMDB
        env = lmdb.open(str(self.lmdb_dir / 'forward_citations.lmdb'),
                       map_size=1024*1024*1024)

        with env.begin(write=True) as txn:
            for key, data in forward_map.items():
                data['corpuses_referenced'] = list(data['corpuses_referenced'])
                data['reference_count'] = len(data['cross_references'])

                txn.put(key.encode(),
                       json.dumps(data, ensure_ascii=False).encode())

        env.close()

    def build_reverse_citations(self):
        """Build reverse cross-corpus citations"""
        # Group by target
        reverse_map = {}

        for ref in self.cross_refs:
            target_key = f"{ref['target_corpus']}:{ref['target_section']}"

            if target_key not in reverse_map:
                reverse_map[target_key] = {
                    'target_corpus': ref['target_corpus'],
                    'target_section': ref['target_section'],
                    'referenced_by': [],
                    'referencing_corpuses': set()
                }

            reverse_map[target_key]['referenced_by'].append({
                'source_corpus': ref['source_corpus'],
                'source_section': ref['source_section'],
                'relationship_type': ref['relationship_type']
            })
            reverse_map[target_key]['referencing_corpuses'].add(ref['source_corpus'])

        # Write to LMDB
        env = lmdb.open(str(self.lmdb_dir / 'reverse_citations.lmdb'),
                       map_size=1024*1024*1024)

        with env.begin(write=True) as txn:
            for key, data in reverse_map.items():
                data['referencing_corpuses'] = list(data['referencing_corpuses'])
                data['referenced_by_count'] = len(data['referenced_by'])

                txn.put(key.encode(),
                       json.dumps(data, ensure_ascii=False).encode())

        env.close()
```

---

## Updated Knowledge Service

### Updated lmdb_store.py (Add CrossCorpusStore)

```python
class CrossCorpusStore:
    """Store for cross-corpus citations"""

    def __init__(self, cross_corpus_dir: Path):
        self.forward_env = lmdb.open(
            str(cross_corpus_dir / 'forward_citations.lmdb'),
            readonly=True, lock=False
        )
        self.reverse_env = lmdb.open(
            str(cross_corpus_dir / 'reverse_citations.lmdb'),
            readonly=True, lock=False
        )
        self.metadata_env = lmdb.open(
            str(cross_corpus_dir / 'metadata.lmdb'),
            readonly=True, lock=False
        )

    def get_cross_references(self, corpus: str, section: str) -> Optional[Dict]:
        """Get what other corpuses this section references"""
        key = f"{corpus}:{section}".encode()

        with self.forward_env.begin() as txn:
            data = txn.get(key)
            if not data:
                return None
            return json.loads(data.decode())

    def get_cross_citations(self, corpus: str, section: str) -> Optional[Dict]:
        """Get what sections in other corpuses reference this"""
        key = f"{corpus}:{section}".encode()

        with self.reverse_env.begin() as txn:
            data = txn.get(key)
            if not data:
                return None
            return json.loads(data.decode())

    def get_metadata(self) -> Dict:
        """Get cross-corpus statistics"""
        with self.metadata_env.begin() as txn:
            data = txn.get(b'corpus_interconnections')
            if not data:
                return {}
            return json.loads(data.decode())
```

### Updated main.py (Add Cross-Corpus Endpoints)

```python
# Initialize cross-corpus store
CROSS_CORPUS_DIR = Path(os.getenv(
    "CROSS_CORPUS_DIR",
    str(Path(__file__).parent / "lmdb_data" / "cross_corpus")
))
cross_corpus_store = CrossCorpusStore(CROSS_CORPUS_DIR)


@app.get("/cross-corpus/{corpus}/{section}/references")
def get_cross_corpus_references(corpus: str, section: str):
    """Get what this section references in OTHER corpuses

    Example:
        GET /cross-corpus/ohio_administration/3701-17-01/references

        Shows all Ohio Revised Code statutes referenced by this admin rule
    """
    refs = cross_corpus_store.get_cross_references(corpus, section)

    if not refs:
        return {
            'source_corpus': corpus,
            'source_section': section,
            'cross_references': [],
            'reference_count': 0
        }

    return refs


@app.get("/cross-corpus/{corpus}/{section}/citations")
def get_cross_corpus_citations(corpus: str, section: str):
    """Get what sections in OTHER corpuses reference this

    Example:
        GET /cross-corpus/ohio_revised/3727.01/citations

        Shows:
        - Admin rules that implement this statute
        - Cases that cite this statute
        - Constitution provisions that reference this
    """
    citations = cross_corpus_store.get_cross_citations(corpus, section)

    if not citations:
        return {
            'target_corpus': corpus,
            'target_section': section,
            'referenced_by': [],
            'referenced_by_count': 0
        }

    return citations


@app.get("/cross-corpus/stats")
def get_cross_corpus_stats():
    """Get cross-corpus interconnection statistics

    Shows how corpuses reference each other
    """
    return cross_corpus_store.get_metadata()
```

---

## Example Queries

### Query 1: What does this admin rule implement?

```bash
GET /cross-corpus/ohio_administration/3701-17-01/references

Response:
{
  "source_corpus": "ohio_administration",
  "source_section": "3701-17-01",
  "source_title": "Hospital Licensing Rules",
  "cross_references": [
    {
      "target_corpus": "ohio_revised",
      "target_section": "3727.01",
      "target_title": "Hospital Definitions",
      "relationship_type": "implements"
    },
    {
      "target_corpus": "ohio_revised",
      "target_section": "3727.02",
      "target_title": "Hospital Requirements",
      "relationship_type": "implements"
    }
  ],
  "reference_count": 2,
  "corpuses_referenced": ["ohio_revised"]
}
```

### Query 2: What cites this statute?

```bash
GET /cross-corpus/ohio_revised/3727.01/citations

Response:
{
  "target_corpus": "ohio_revised",
  "target_section": "3727.01",
  "target_title": "Hospital Definitions",
  "referenced_by": [
    {
      "source_corpus": "ohio_administration",
      "source_section": "3701-17-01",
      "source_title": "Hospital Licensing Rules",
      "relationship_type": "implements"
    },
    {
      "source_corpus": "ohio_case_law",
      "source_section": "2023-Ohio-1234",
      "source_title": "State v. Hospital Corp",
      "relationship_type": "cites"
    },
    {
      "source_corpus": "sixth_circuit",
      "source_section": "21-3456",
      "source_title": "Smith v. Ohio Dept of Health",
      "relationship_type": "cites"
    }
  ],
  "referenced_by_count": 3,
  "referencing_corpuses": ["ohio_administration", "ohio_case_law", "sixth_circuit"]
}
```

### Query 3: Federal Case Citing State and Federal Law

```bash
GET /cross-corpus/sixth_circuit/21-3456/references

Response:
{
  "source_corpus": "sixth_circuit",
  "source_section": "21-3456",
  "source_title": "Smith v. Ohio Dept of Health",
  "cross_references": [
    {
      "target_corpus": "ohio_revised",
      "target_section": "3727.01",
      "target_title": "Hospital Definitions",
      "relationship_type": "cites"
    },
    {
      "target_corpus": "ohio_case_law",
      "target_section": "2020-Ohio-5678",
      "target_title": "Jones v. State Medical Board",
      "relationship_type": "cites"
    },
    {
      "target_corpus": "us_code",
      "target_section": "42 USC 1983",
      "target_title": "Civil Rights - Deprivation of Rights",
      "relationship_type": "cites"
    },
    {
      "target_corpus": "scotus",
      "target_section": "556 U.S. 662",
      "target_title": "Ashcroft v. Iqbal",
      "relationship_type": "cites"
    }
  ],
  "reference_count": 4,
  "corpuses_referenced": ["ohio_revised", "ohio_case_law", "us_code", "scotus"]
}
```

### Query 4: What Federal Law Does This Cite?

```bash
GET /cross-corpus/ohio_case_law/2023-Ohio-1234/references

Response:
{
  "source_corpus": "ohio_case_law",
  "source_section": "2023-Ohio-1234",
  "source_title": "State v. Hospital Corp",
  "cross_references": [
    {
      "target_corpus": "ohio_revised",
      "target_section": "3727.01",
      "target_title": "Hospital Definitions",
      "relationship_type": "cites"
    },
    {
      "target_corpus": "us_code",
      "target_section": "42 USC 1395",
      "target_title": "Medicare",
      "relationship_type": "cites"
    },
    {
      "target_corpus": "scotus",
      "target_section": "467 U.S. 837",
      "target_title": "Chevron v. NRDC",
      "relationship_type": "cites"
    }
  ],
  "reference_count": 3,
  "corpuses_referenced": ["ohio_revised", "us_code", "scotus"]
}
```

---

## Visual Representation

### Before (Intra-Corpus Only)

```
┌─────────────────┐     ┌─────────────────┐
│ Ohio Revised    │     │ Ohio Admin Code │
│                 │     │                 │
│ 3727.01 ←──┐   │     │ 3701-17-01      │
│            │    │     │                 │
│ 3727.02 ───┘   │     │                 │
└─────────────────┘     └─────────────────┘
  (internal refs)         (internal refs)
```

### After (With Cross-Corpus)

```
┌─────────────────┐     ┌─────────────────┐
│ Ohio Revised    │◄────│ Ohio Admin Code │
│                 │     │                 │
│ 3727.01 ←──┐   │     │ 3701-17-01      │
│            │    │     │   │ implements  │
│ 3727.02 ───┘   │◄────┤   └─────────────┤
└─────────────────┘     └─────────────────┘
         ▲
         │ cites
         │
┌─────────────────┐
│ Ohio Case Law   │
│                 │
│ 2023-Ohio-1234  │
└─────────────────┘
```

---

## Benefits

1. **Complete Citation Graph**: See how statutes, rules, and cases interconnect
2. **Regulatory Context**: Admin rules show which statutes they implement
3. **Case Law Analysis**: See which statutes are most cited in case law
4. **Constitutional Review**: Track constitutional basis for statutes
5. **Better UX**: "Show me all admin rules that implement this statute"
6. **DeepSeek Context**: Include cross-corpus citations in context

---

## Build Order

1. ✅ Build intra-corpus LMDB for each corpus (already done for Ohio Revised)
2. ⏳ Build intra-corpus LMDB for Ohio Admin, Constitution, Case Law
3. ⏳ Run cross-corpus citation analysis (scan all corpuses for cross-refs)
4. ⏳ Build cross-corpus LMDB (3 databases: forward, reverse, metadata)
5. ⏳ Update knowledge service with cross-corpus endpoints
6. ⏳ Update Temporal workflows to use cross-corpus data

---

## Estimated Cross-Corpus Citations (All 7 Corpuses)

### State Law Internal Cross-References

| Source Corpus | Target Corpus | Estimated Citations | Relationship |
|--------------|---------------|-------------------|--------------|
| Ohio Admin Code | Ohio Revised Code | ~8,500 | Implements |
| Ohio Admin Code | Ohio Constitution | ~150 | References |
| Ohio Case Law | Ohio Revised Code | ~50,000 | Cites |
| Ohio Case Law | Ohio Constitution | ~2,000 | Cites |
| Ohio Case Law | Ohio Admin Code | ~1,500 | Cites |

### Federal-State Cross-References

| Source Corpus | Target Corpus | Estimated Citations | Relationship |
|--------------|---------------|-------------------|--------------|
| Ohio Case Law | US Code | ~25,000 | Cites federal statutes |
| Ohio Case Law | SCOTUS | ~15,000 | Cites Supreme Court precedent |
| 6th Circuit | Ohio Revised Code | ~5,000 | References state law |
| 6th Circuit | Ohio Case Law | ~20,000 | Cites state precedent |
| 6th Circuit | US Code | ~40,000 | Cites federal statutes |
| 6th Circuit | SCOTUS | ~30,000 | Cites Supreme Court |
| SCOTUS | US Code | ~50,000 | Interprets federal law |

### Federal-Federal Cross-References

| Source Corpus | Target Corpus | Estimated Citations | Relationship |
|--------------|---------------|-------------------|--------------|
| 6th Circuit | 6th Circuit | ~30,000 | Circuit precedent (intra-corpus) |
| SCOTUS | SCOTUS | ~40,000 | Supreme Court precedent (intra-corpus) |

### Summary

| Citation Type | Estimated Total |
|--------------|----------------|
| **State-to-State** | ~62,150 |
| **Federal-to-State** | ~25,000 |
| **State-to-Federal** | ~40,000 |
| **Federal-to-Federal** | ~150,000 |
| **Grand Total** | **~277,150** |

**Disk Space:** ~800 MB for cross-corpus LMDB databases (all 7 corpuses)

---

**This is a separate analysis phase that runs AFTER all individual corpus LMDB builds are complete.**