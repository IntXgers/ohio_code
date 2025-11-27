# Knowledge Service Integration Guide

**⚠️ CRITICAL: This document defines the interface contract for LMDB integration**
**✅ This matches the LMDB SCHEMA CONTRACT in COMPLETE_DATA_INVENTORY.md**

---

## What This Document Is For

This document tells your **application repo** (ohio-legal-ai.io) exactly what to expect from the **data pipeline repo** (ohio_code). It defines:

1. **Database file names** you will receive
2. **Exact schema structure** of each database
3. **How to query** the databases
4. **What NOT to assume** about the data

**DO NOT copy implementation code from here** - implement your own logic based on these contracts.

---

## 1. LMDB Files You Will Receive (Per Corpus)

Every corpus produces exactly **5 LMDB databases** in this structure:

```
ohio_revised/lmdb/
├── primary.lmdb              ← Main content (sections/cases/rules/articles)
├── citations.lmdb            ← Forward citations
├── reverse_citations.lmdb    ← Backward citations
├── chains.lmdb               ← Pre-computed citation chains
└── metadata.lmdb             ← Corpus metadata

ohio_caselaw/lmdb/
├── primary.lmdb              ← Main content (court opinions)
├── citations.lmdb            ← Forward citations
├── reverse_citations.lmdb    ← Backward citations
├── chains.lmdb               ← Pre-computed citation chains
└── metadata.lmdb             ← Corpus metadata

ohio_administration/lmdb/
├── primary.lmdb              ← Main content (administrative rules)
├── citations.lmdb            ← Forward citations
├── reverse_citations.lmdb    ← Backward citations
├── chains.lmdb               ← Pre-computed citation chains
└── metadata.lmdb             ← Corpus metadata
```

### File Naming Convention

**All corpora use `primary.lmdb` for their main content database.**

Why?
- **Consistency**: Same file name across all corpora
- **Simplicity**: Your code can always look for `primary.lmdb` regardless of corpus
- **No confusion**: Content type is determined by corpus directory, not filename

| Corpus | Directory | Primary Content Type |
|--------|-----------|---------------------|
| Ohio Revised | `ohio_revised/lmdb/` | Statutory sections |
| Ohio Admin | `ohio_administration/lmdb/` | Administrative rules |
| Ohio Constitution | `ohio_constitution/lmdb/` | Constitutional articles |
| Ohio Case Law | `ohio_caselaw/lmdb/` | Court opinions |
| US Code | `us_code/lmdb/` | Federal statutes |
| SCOTUS | `scotus/lmdb/` | Supreme Court cases |
| 6th Circuit | `sixth_circuit/lmdb/` | Circuit court cases |

---

## 2. Database Schemas (JSON Format)

### 2.1 primary.lmdb Schema

**Key**: `section_number` (encoded as bytes)
**Value**: JSON object with this EXACT structure:

```json
{
  "section_number": "string (unique ID - format varies by corpus)",
  "url": "string (source URL)",
  "url_hash": "string (hash of URL)",
  "header": "string (full header with title)",
  "section_title": "string (title only)",
  "paragraphs": ["array of paragraph strings"],
  "full_text": "string (all paragraphs concatenated)",
  "word_count": "number (total words)",
  "paragraph_count": "number (total paragraphs)",
  "has_citations": "boolean (true if this item cites others)",
  "citation_count": "number (how many items this cites)",
  "in_complex_chain": "boolean (true if part of a chain)",
  "is_clickable": "boolean (true if has forward or reverse citations)",
  "scraped_date": "ISO8601 string (when data was scraped)",
  "enrichment": {
    "summary": "string | null (plain language summary - optional)",
    "legal_type": "string | null (criminal_statute, civil_statute, definitional, procedural - optional)",
    "practice_areas": "array | null (list of legal domains - optional)",
    "complexity": "number | null (1-10 score - optional)",
    "key_terms": "array | null (important legal terms - optional)",
    "offense_level": "string | null (felony, misdemeanor - criminal statutes only)",
    "offense_degree": "string | null (F1-F5, M1-M4 - criminal statutes only)"
  }
}
```

**Example IDs by corpus:**
- Ohio Revised: `"2913.02"` (statutory section)
- Ohio Case Law: `"2023-Ohio-1234"` (case citation)
- Ohio Admin: `"3701-17-01"` (rule number)
- Ohio Constitution: `"Article I, Section 1"` (constitutional section)

### 2.2 citations.lmdb Schema

**Key**: `section_number` (encoded as bytes)
**Value**: JSON object:

```json
{
  "section": "string (item identifier)",
  "direct_references": ["array of section IDs this item cites"],
  "reference_count": "number (length of direct_references)",
  "references_details": [
    {
      "section": "string (referenced section ID)",
      "title": "string (referenced section title)",
      "url": "string (referenced section URL)",
      "url_hash": "string (hash of URL)"
    }
  ]
}
```

**If an item has no citations**: The key will NOT exist in the database (not an empty object).

### 2.3 reverse_citations.lmdb Schema

**Key**: `section_number` (encoded as bytes)
**Value**: JSON object:

```json
{
  "section": "string (item identifier)",
  "cited_by": ["array of section IDs that cite this item"],
  "cited_by_count": "number (length of cited_by)",
  "citing_details": [
    {
      "section": "string (citing section ID)",
      "title": "string (citing section title)",
      "url": "string (citing section URL)"
    }
  ]
}
```

**If an item is not cited by anything**: The key will NOT exist in the database.

### 2.4 chains.lmdb Schema

**Key**: `chain_id` (encoded as bytes) - same as the primary section ID
**Value**: JSON object:

```json
{
  "chain_id": "string (primary section ID)",
  "primary_section": "string (starting section ID)",
  "chain_sections": ["array of section IDs in chain"],
  "chain_depth": "number (number of sections in chain)",
  "references_count": "number (total references in chain)",
  "created_at": "ISO8601 string (when chain was built)",
  "complete_chain": [
    {
      "section": "string (section ID)",
      "title": "string (section title)",
      "url": "string (section URL)",
      "url_hash": "string (hash of URL)",
      "full_text": "string (complete legal text)",
      "word_count": "number (words in this section)"
    }
  ]
}
```

**If an item is not part of a chain**: The key will NOT exist in the database.

### 2.5 metadata.lmdb Schema

**Special Key**: `b'corpus_info'` (literal bytes)
**Value**: JSON object:

```json
{
  "total_primary": "number (total items in primary.lmdb)",
  "primary_with_citations": "number (items that cite others)",
  "complex_chains": "number (total citation chains)",
  "reverse_citations": "number (items cited by others)",
  "build_date": "ISO8601 string (when LMDB was built)",
  "source": "string (source URL - e.g., https://codes.ohio.gov/ohio-revised-code)",
  "version": "string (LMDB builder version)",
  "builder": "string (builder script name)",
  "databases": {
    "primary": "string (description of primary.lmdb)",
    "citations": "string (description of citations.lmdb)",
    "reverse_citations": "string (description of reverse_citations.lmdb)",
    "chains": "string (description of chains.lmdb)",
    "metadata": "string (description of metadata.lmdb)"
  }
}
```

---

## 3. How to Query LMDB Databases

### Basic LMDB Access Pattern

```python
import lmdb
import json

# Open database (read-only)
env = lmdb.open('/path/to/corpus/lmdb/primary.lmdb', readonly=True, lock=False)

# Query by key
with env.begin() as txn:
    data = txn.get(b'2913.02')  # Key must be bytes
    if data:
        section = json.loads(data.decode())  # Value is JSON string
        print(section['section_title'])

# Iterate all items
with env.begin() as txn:
    cursor = txn.cursor()
    for key, value in cursor:
        section_id = key.decode()
        section_data = json.loads(value.decode())
        # Process each item...

# Close when done
env.close()
```

### Query Pattern for Each Database

| Database | Query Key | Returns |
|----------|-----------|---------|
| `primary.lmdb` | Section ID (e.g., `b'2913.02'`) | Full section data with enrichment |
| `citations.lmdb` | Section ID | List of items this section cites |
| `reverse_citations.lmdb` | Section ID | List of items that cite this section |
| `chains.lmdb` | Section ID | Pre-computed citation chain |
| `metadata.lmdb` | `b'corpus_info'` (literal) | Corpus-level statistics |

---

## 4. What Your Application Should Do

### Your LMDBStore Class Should:

1. **Open all 5 databases** for a corpus (read-only, no lock)
2. **Provide query methods** for each database type:
   - `get_section(section_id)` → queries `primary.lmdb`
   - `get_citations(section_id)` → queries `citations.lmdb`
   - `get_reverse_citations(section_id)` → queries `reverse_citations.lmdb`
   - `get_chain(section_id)` → queries `chains.lmdb`
   - `get_corpus_info()` → queries `metadata.lmdb` with key `b'corpus_info'`
3. **Handle missing keys gracefully** (return None or empty structure)
4. **Close databases** on shutdown

### Your Application Should:

1. **Create one LMDBStore instance per corpus**
   ```python
   ohio_revised = LMDBStore(Path("./lmdb_data/ohio_revised/lmdb"))
   ohio_caselaw = LMDBStore(Path("./lmdb_data/ohio_caselaw/lmdb"))
   ```

2. **Map LMDB data to Pydantic models**
   - LMDBStore returns raw dicts
   - Your data service converts to Pydantic models (OhioSection, OhioCaseLaw, etc.)

3. **NOT implement business logic in LMDBStore**
   - LMDBStore = data access only
   - SearchService = filtering, ranking, search logic
   - Keep them separate!

---

## 5. Symlink Setup

Your application should symlink to the LMDB output directories:

```bash
# In your application repo
cd ohio-legal-ai.io/packages/knowledge_service/lmdb_data/

# Create symlinks to data pipeline output
ln -s /path/to/ohio_code/ohio_revised/src/ohio_revised/data/enriched_output/comprehensive_lmdb ohio_revised
ln -s /path/to/ohio_code/ohio_caselaw/src/ohio_caselaw/data/enriched_output/comprehensive_lmdb ohio_caselaw
ln -s /path/to/ohio_code/ohio_administration/src/ohio_administration/data/enriched_output/comprehensive_lmdb ohio_administration
ln -s /path/to/ohio_code/ohio_constitution/src/ohio_constitution/data/enriched_output/comprehensive_lmdb ohio_constitution

# Verify
ls -la ohio_revised/
# Should show: primary.lmdb, citations.lmdb, reverse_citations.lmdb, chains.lmdb, metadata.lmdb
```

---

## 6. Important Assumptions and Guarantees

### ✅ What You CAN Assume:

1. All corpora will have exactly **5 LMDB databases** with these exact names
2. Database schemas will match the JSON structures above
3. All keys and values are **UTF-8 encoded** strings (bytes)
4. Missing keys mean the item doesn't have that data (not an error)
5. `enrichment` fields may be `null` (enrichment is optional)
6. `metadata.lmdb` always has `b'corpus_info'` key

### ❌ What You CANNOT Assume:

1. **Section ID format** - varies by corpus (see examples above)
2. **All items have citations** - many items cite nothing
3. **All items are cited** - many items have no reverse citations
4. **All items are in chains** - chains are only for complex citation patterns
5. **Enrichment is complete** - enrichment fields may be null
6. **Field order in JSON** - don't rely on key order
7. **Database file sizes** - vary greatly by corpus

---

## 7. Breaking Changes Protocol

**If the data pipeline changes the schema**, you will be notified and the following will happen:

1. ⚠️ `COMPLETE_DATA_INVENTORY.md` will be updated FIRST
2. ⚠️ This document will be updated
3. ⚠️ All LMDB builders will be updated
4. ⚠️ **You must update your Pydantic models**
5. ⚠️ **You must update your LMDBStore class**
6. ⚠️ **You must rebuild your TypedDict schemas** (if using)
7. ⚠️ **You must test all endpoints**

**Version tracking**: Check `metadata.lmdb` → `corpus_info` → `version` field to detect schema changes.

---

## 8. Testing Your Integration

### Verify LMDB Files Exist

```bash
# Check symlinks work
ls -la lmdb_data/ohio_revised/
# Should show all 5 .lmdb files

# Check file sizes (should not be 0 bytes)
ls -lh lmdb_data/ohio_revised/
```

### Test Basic Queries

```python
import lmdb
import json

# Test primary.lmdb
env = lmdb.open('lmdb_data/ohio_revised/primary.lmdb', readonly=True, lock=False)
with env.begin() as txn:
    # Get first item
    cursor = txn.cursor()
    key, value = next(cursor.iternext())
    print(f"First section ID: {key.decode()}")
    section = json.loads(value.decode())
    print(f"Has enrichment: {'enrichment' in section}")
    print(f"Schema valid: {all(k in section for k in ['section_number', 'paragraphs', 'full_text'])}")
env.close()

# Test metadata.lmdb
env = lmdb.open('lmdb_data/ohio_revised/metadata.lmdb', readonly=True, lock=False)
with env.begin() as txn:
    data = txn.get(b'corpus_info')
    corpus_info = json.loads(data.decode())
    print(f"Total items: {corpus_info['total_primary']}")
    print(f"Build date: {corpus_info['build_date']}")
    print(f"Version: {corpus_info['version']}")
env.close()
```

### Test Missing Keys

```python
# Test that missing keys return None (not error)
env = lmdb.open('lmdb_data/ohio_revised/citations.lmdb', readonly=True, lock=False)
with env.begin() as txn:
    # Query section that has no citations
    data = txn.get(b'999999.99')
    assert data is None  # Should be None, not throw error
env.close()
```

---

## 9. Performance Considerations

### LMDB is Fast, But:

1. **Read-only mode**: Always open with `readonly=True, lock=False`
2. **Connection pooling**: Reuse LMDB environments (don't open/close per query)
3. **Memory-mapped**: LMDB uses mmap, so OS caches data automatically
4. **Cursor iteration**: Use cursors for bulk iteration (not individual gets)
5. **Large corpora**: Case law has 500K items - avoid `get_all()` operations

### Recommended Pattern:

```python
class LMDBStore:
    def __init__(self, data_dir: Path):
        # Open environments ONCE in __init__
        self.primary_env = lmdb.open(...)
        self.citations_env = lmdb.open(...)
        # ... keep open for lifetime of application

    def close(self):
        # Close on application shutdown
        self.primary_env.close()
        self.citations_env.close()
```

---

## 10. Summary Checklist

When integrating LMDB data into your application:

- [ ] Create symlinks to ohio_code LMDB output directories
- [ ] Verify all 5 .lmdb files exist per corpus
- [ ] Open databases with `readonly=True, lock=False`
- [ ] Query with bytes keys, decode JSON values
- [ ] Handle missing keys (return None, not error)
- [ ] Map LMDB dicts to Pydantic models in data service
- [ ] Keep LMDBStore simple (data access only)
- [ ] Put search/filter logic in separate SearchService
- [ ] Check `metadata.lmdb` version field for schema changes
- [ ] Test with all corpora (not just ohio_revised)

---

## 11. Questions and Support

**If you encounter issues:**

1. Check `COMPLETE_DATA_INVENTORY.md` for schema contract
2. Verify LMDB files were built correctly (check file sizes, dates)
3. Test with simple queries first (single item lookup)
4. Check that enrichment fields may be null (handle gracefully)

**If schema needs to change:**

1. Discuss in both repos (ohio_code + ohio-legal-ai.io)
2. Follow the 7-step breaking changes protocol
3. Update both sides simultaneously
4. Rebuild all LMDB databases
5. Test all API endpoints

---

## 12. File Location Reference

| What | Where |
|------|-------|
| **This document** | `ohio_code/docs/UPDATED_KNOWLEDGE_SERVICE_CODE.md` |
| **Schema contract** | `ohio_code/docs/COMPLETE_DATA_INVENTORY.md` |
| **LMDB output** | `ohio_code/{corpus}/src/{corpus}/data/enriched_output/comprehensive_lmdb/` |
| **Your symlinks** | `ohio-legal-ai.io/packages/knowledge_service/lmdb_data/{corpus}/` |
| **Your LMDBStore** | `ohio-legal-ai.io/packages/knowledge_service/lmdb_store.py` |
| **Your Pydantic models** | `ohio-legal-ai.io/packages/models/src/models/` |

---

**✅ This document defines the complete interface contract.**
**❌ DO NOT assume anything not explicitly documented here.**
**🔒 Both repos must follow this contract to prevent breaking changes.**