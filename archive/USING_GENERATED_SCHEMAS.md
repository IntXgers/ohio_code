# Using Generated LMDB Schemas

**Date:** 2025-11-20
**Status:** Implementation Guide

---

## Overview

The generated schemas in `generated_schemas.py` provide TypedDict definitions that match your Pydantic models exactly. By using these in your LMDB builders, you get:

1. **IDE Autocomplete** - Type hints help you write code faster
2. **Type Checking** - Catch schema mismatches at development time (with mypy/pyright)
3. **Zero Drift** - LMDB structure guaranteed to match Pydantic models
4. **Self-Documentation** - Code clearly shows what fields are expected

---

## How to Use in LMDB Builders

### 1. Import the Schemas

At the top of your `build_comprehensive_lmdb.py`:

```python
# Import generated LMDB schemas for type validation
from generated_schemas import (
    OhioSectionDict,
    CitationDataDict,
    ReverseCitationDataDict,
    CitationChainDict,
    CorpusInfoDict,
    ReferenceDetailDict,
    CitingDetailDict
)
```

### 2. Annotate Dictionary Creation

When creating section entries, use type annotations:

```python
# Build complete section record (type-validated with OhioSectionDict)
section_data: OhioSectionDict = {
    'section_number': section_num,
    'url': doc.get('url', ''),
    'url_hash': doc.get('url_hash', ''),
    'header': header,
    'section_title': section_title,
    'paragraphs': paragraphs,
    'full_text': '\n'.join(paragraphs),
    'word_count': sum(len(p.split()) for p in paragraphs),
    'paragraph_count': len(paragraphs),
    'has_citations': has_forward_citations,
    'citation_count': len(self.citation_map.get(section_num, [])),
    'in_complex_chain': section_num in self.chains_map,
    'is_clickable': is_clickable,
    'scraped_date': datetime.now().isoformat(),
    # Optional fields (can be added later)
    # 'treatment_status': 'valid',
    # 'authority_score': 0.85,
    # etc.
}
```

### 3. What the Type Annotation Does

The `: OhioSectionDict` annotation tells Python (and your IDE/type checker):

- **What fields are expected** in this dictionary
- **What types each field should be**
- **Which fields are required vs optional** (NotRequired)

**Important:** TypedDict doesn't enforce anything at runtime - it's purely for static analysis. But that's exactly what you want for LMDB builders!

---

## Example: Using CitationDataDict

```python
def build_citations_database(self):
    """Build citations database with enhanced relationship types and context"""
    logger.info("Building enhanced citations database...")

    with self.citations_db.begin(write=True) as txn:
        for section_num, references in self.citation_map.items():
            # Type-annotate with CitationDataDict
            citation_data: CitationDataDict = {
                'section': section_num,
                'direct_references': references,
                'reference_count': len(references),
                'references_details': []  # Will be filled with ReferenceDetailDict items
            }

            # Add reference details (each one is a ReferenceDetailDict)
            for ref in references:
                detail: ReferenceDetailDict = {
                    'target_section': ref,
                    'context': enhanced_info.get('context', ''),
                    'relationship_type': 'cross_reference'
                }
                citation_data['references_details'].append(detail)

            # Store in LMDB
            key = section_num.encode()
            value = json.dumps(citation_data, ensure_ascii=False).encode()
            txn.put(key, value)
```

---

## Example: Using ReverseCitationDataDict

```python
def build_reverse_citations_database(self):
    """Build reverse citations database"""

    with self.reverse_citations_db.begin(write=True) as txn:
        for section_num, citing_sections in reverse_map.items():
            # Type-annotate with ReverseCitationDataDict
            reverse_data: ReverseCitationDataDict = {
                'section': section_num,
                'cited_by': sorted(list(citing_sections)),
                'cited_by_count': len(citing_sections),
                'citing_details': []
            }

            # Add citing details
            for citing in sorted(citing_sections):
                detail: CitingDetailDict = {
                    'citing_section': citing,
                    'context': ''  # Add context if available
                }
                reverse_data['citing_details'].append(detail)

            # Store
            key = section_num.encode()
            value = json.dumps(reverse_data).encode()
            txn.put(key, value)
```

---

## Benefits You Get

### 1. IDE Autocomplete
When you type `section_data['`, your IDE shows all available fields:
- section_number
- url
- paragraphs
- treatment_status
- authority_score
- etc.

### 2. Type Checking
Run `mypy` or `pyright` to catch errors:

```bash
# This will catch typos and type mismatches
pyright build_comprehensive_lmdb.py
```

Example errors caught:
```python
section_data: OhioSectionDict = {
    'secton_number': '2913.02',  # ❌ Typo! Should be 'section_number'
    'word_count': '456',          # ❌ Type error! Should be int, not str
}
```

### 3. Self-Documenting Code
Future developers (including yourself) can see exactly what structure is expected:

```python
# Clear intent: this dict follows the OhioSection schema
section_data: OhioSectionDict = {...}

# vs unclear:
section_data = {...}  # What fields does this have? Who knows!
```

---

## Optional vs Required Fields

All fields in the generated schemas are `NotRequired` by default. This means:

```python
# This is valid - you can include only some fields
section_data: OhioSectionDict = {
    'section_number': '2913.02',
    'url': 'https://...',
    'full_text': 'legal text here'
}

# This is also valid - include all fields
section_data: OhioSectionDict = {
    'section_number': '2913.02',
    'url': 'https://...',
    'full_text': 'legal text here',
    'treatment_status': 'valid',
    'authority_score': 0.85,
    # ... all other fields
}
```

The `NotRequired` approach gives you flexibility while still providing type safety for the fields you do include.

---

## Graph Metrics Integration

The `OhioSectionDict` schema includes the new graph metric fields:

```python
section_data: OhioSectionDict = {
    # ... basic fields ...

    # Treatment status (for temporal validity)
    'treatment_status': 'valid',  # or 'overruled', 'superseded', etc.
    'invalidated_by': None,       # Reference to invalidating case
    'superseded_by': None,        # Reference to superseding law
    'valid_from': '2020-01-01',   # ISO date string
    'valid_until': None,          # None = still valid

    # Graph metrics (computed from citation network)
    'authority_score': 0.85,            # PageRank-style authority (0-1)
    'betweenness_centrality': 0.42,     # Network centrality (0-1)
    'citation_velocity': 15.3,          # Recent citations per year

    # Court hierarchy (for case law)
    'court_level': 'supreme_court',     # or 'appellate', 'trial'
    'binding_on': ['all_ohio_courts'],  # List of courts this binds
    'precedent_value': 'binding'        # or 'persuasive'
}
```

**Note:** You don't need to compute all these fields immediately. Start with the basics and add computed metrics in a separate processing step.

---

## Workflow: Schema Update → Rebuild

When you add new fields to the Pydantic models:

1. **Edit Pydantic model** in `ohio-legal-ai.io/packages/models/src/models/lmdb_data.py`
   ```python
   class OhioSection(BaseModel):
       # Add new field
       statutory_authority: Optional[str] = None
   ```

2. **Regenerate schemas** in `ohio-legal-ai.io`
   ```bash
   cd ~/ohio-legal-ai.io/packages/models
   python 09_lmdb_schema_generator.py
   ```

3. **Schemas auto-update** in `ohio_code/*/lmdb/generated_schemas.py`
   ```python
   class OhioSectionDict(TypedDict):
       # New field automatically appears
       statutory_authority: NotRequired[str]
   ```

4. **Update LMDB builder** to populate the new field
   ```python
   section_data: OhioSectionDict = {
       # ... existing fields ...
       'statutory_authority': doc.get('authority', None)  # Populate new field
   }
   ```

5. **Rebuild LMDB** with new structure
   ```bash
   cd ohio_revised/src/ohio_revised/lmdb
   python build_comprehensive_lmdb.py
   ```

---

## Summary

**What you should do:**

1. ✅ Import the generated schemas in your LMDB builders
2. ✅ Annotate dictionary creation with the appropriate TypedDict
3. ✅ Use IDE autocomplete to fill in fields correctly
4. ✅ Run type checkers (optional but recommended)
5. ✅ Add new fields gradually as you implement features

**What you should NOT do:**

- ❌ Manually edit `generated_schemas.py` (it will be overwritten)
- ❌ Expect runtime validation (TypedDict is for static analysis only)
- ❌ Feel required to fill every field (all are `NotRequired`)

**The goal:** Zero-drift architecture where LMDB structure always matches Pydantic models, enforced by automated schema generation and static type checking.