# LMDB Schema Reference - Complete Guide

**Last Updated:** 2025-11-25
**Purpose:** Single source of truth for LMDB database schemas, implementation status, and usage

---

## Table of Contents

1. [Overview](#overview)
2. [The 5 LMDB Databases](#the-5-lmdb-databases)
3. [Implementation Status](#implementation-status)
4. [Primary Database Schema](#primary-database-schema)
5. [Citations Database Schema](#citations-database-schema)
6. [Reverse Citations Database Schema](#reverse-citations-database-schema)
7. [Chains Database Schema](#chains-database-schema)
8. [Metadata Database Schema](#metadata-database-schema)
9. [Zero-Drift Architecture](#zero-drift-architecture)
10. [Future Enhancement Phases](#future-enhancement-phases)
11. [API Contract](#api-contract)
12. [Breaking Changes Protocol](#breaking-changes-protocol)

---

## Overview

Every corpus (Ohio Revised, Ohio Admin, Ohio Constitution, Ohio Case Law) produces **exactly 5 LMDB databases** with identical structure. Content type is determined by corpus directory, not database names.

### Why Standardized Names?

- **Consistency**: Same query logic works across all corpuses
- **Simplicity**: Knowledge service uses one codebase for all corpuses
- **No Confusion**: Content type from directory path, not database name

---

## The 5 LMDB Databases

| Database | Purpose | Key Example | Size (Ohio Revised) |
|----------|---------|-------------|---------------------|
| **primary.lmdb** | Full legal text + metadata | `"2913.02"` | 1.4 GB |
| **citations.lmdb** | Forward citations (what this cites) | `"2913.02"` | ~20 MB |
| **reverse_citations.lmdb** | Backward citations (who cites this) | `"2913.02"` | ~30 MB |
| **chains.lmdb** | Pre-computed citation chains | `"2913.02"` | ~50 MB |
| **metadata.lmdb** | Corpus statistics | `"corpus_info"` | <1 MB |

**Total per corpus**: ~1.5 GB average (varies by corpus size)

---

## Implementation Status

### ✅ Phase 1: Core Storage (CURRENTLY POPULATED)

All essential fields for legal research are **COMPLETE** and populated in all built LMDBs:

- Core identifiers (section_number, url, url_hash)
- Display fields (header, section_title)
- Legal text (paragraphs, full_text) - **NEVER MODIFIED**
- Content metrics (word_count, paragraph_count)
- Citation metadata (has_citations, citation_count, in_complex_chain, is_clickable)
- Timestamps (scraped_date)
- Auto-enrichment (7 metadata fields)

### 📋 Phase 2: Extractable Metadata (NEXT PRIORITY)

Fields that can be extracted from existing data without LLM:

- Organizational hierarchy (chapter, title)
- Temporal validity (valid_from, valid_until, treatment_status)
- Court hierarchy (court_level, binding_on, precedent_value) - Case law only

### 🧮 Phase 3: Graph Metrics (COMPUTE FROM NETWORK)

Computed from citation graph analysis:

- Authority scoring (PageRank-based)
- Network centrality
- Citation velocity

### 🤖 Phase 4: LLM Enhancement (FUTURE)

Advanced semantic analysis (optional):

- Improved summaries using LLM
- Deeper practice area classification
- Holdings extraction (case law)

### 🔗 Phase 5: Relationship Tracking (ADVANCED)

Legal relationship detection:

- Treatment propagation
- Shepardization
- Temporal chains

---

## Primary Database Schema

**Purpose**: Main content storage for all legal documents
**Key**: Section identifier (e.g., `b'2913.02'`)
**Value**: JSON object

### Complete Schema

```typescript
{
  // ✅ CORE IDENTIFIERS (Phase 1 - POPULATED)
  section_number: string,              // Unique ID (format varies by corpus)
  url: string,                         // Source URL
  url_hash: string,                    // SHA256 hash of URL

  // ✅ DISPLAY FIELDS (Phase 1 - POPULATED)
  header: string,                      // Full header with title (pipe-delimited)
  section_title: string,               // Title extracted from header

  // ✅ LEGAL TEXT (Phase 1 - POPULATED - NEVER MODIFIED)
  paragraphs: string[],                // Array of paragraph strings (EXACT SOURCE)
  full_text: string,                   // All paragraphs joined with \n

  // ✅ CONTENT METRICS (Phase 1 - POPULATED)
  word_count: number,                  // Total words in full_text
  paragraph_count: number,             // Number of paragraphs

  // ✅ CITATION METADATA (Phase 1 - POPULATED)
  has_citations: boolean,              // True if this item cites others
  citation_count: number,              // Number of forward citations
  in_complex_chain: boolean,           // True if part of a citation chain
  is_clickable: boolean,               // True if has forward OR reverse citations (for UI)

  // ✅ TIMESTAMP (Phase 1 - POPULATED)
  scraped_date: string,                // ISO8601 datetime

  // ✅ AUTO-ENRICHMENT (Phase 1 - POPULATED)
  enrichment: {
    summary: string | null,            // Plain language summary (auto-generated from header)
    legal_type: string | null,         // "criminal_statute", "civil_statute", "definitional", "procedural"
    practice_areas: string[] | null,   // ["criminal_law", "family_law", ...]
    complexity: number | null,         // 1-10 scale
    key_terms: string[] | null,        // Important legal terms
    offense_level: string | null,      // "felony", "misdemeanor" (criminal only)
    offense_degree: string | null      // "F1"-"F5", "M1"-"M4" (criminal only)
  } | null,

  // 📋 EXTRACTABLE METADATA (Phase 2 - TODO)
  chapter: string | null,              // Extract from section_number or header
  title: string | null,                // Extract from header structure
  valid_from: string | null,           // ISO8601 date
  valid_until: string | null,          // ISO8601 date or null if current
  treatment_status: string | null,     // "valid", "overruled", "superseded", "questioned"

  // 📋 COURT HIERARCHY (Phase 2 - Case law only)
  court_level: string | null,          // "supreme_court", "appellate", "trial"
  binding_on: string[] | null,         // ["all_ohio_courts"] or ["district_5"]
  precedent_value: string | null,      // "binding", "persuasive"

  // 🧮 GRAPH METRICS (Phase 3 - TODO)
  authority_score: number | null,      // 0.0-1.0 (PageRank-based)
  betweenness_centrality: number | null, // 0.0-1.0 (network centrality)
  citation_velocity: number | null,    // Citations per year (recent)

  // 🔗 RELATIONSHIP TRACKING (Phase 5 - TODO)
  invalidated_by: string | null,       // Reference to invalidating case/law
  superseded_by: string | null         // Reference to superseding law
}
```

### Corpus-Specific Section Number Formats

| Corpus | Format | Example |
|--------|--------|---------|
| Ohio Revised Code | `"chapter.section"` | `"2913.02"` |
| Ohio Admin Code | `"agency-chapter-rule"` | `"3701-17-01"` |
| Ohio Constitution | `"Article X, Section Y"` | `"Article I, Section 1"` |
| Ohio Case Law | `"year-Ohio-number"` | `"2023-Ohio-1234"` |

### Example Entry (Ohio Revised Code - Theft Statute)

```json
{
  "section_number": "2913.02",
  "url": "https://codes.ohio.gov/ohio-revised-code/section-2913.02",
  "url_hash": "sha256:abc123...",
  "header": "Section 2913.02|Theft",
  "section_title": "Theft",
  "paragraphs": [
    "(A) No person, with purpose to deprive the owner of property or services, shall knowingly obtain or exert control over either the property or services in any of the following ways:",
    "(1) Without the consent of the owner or person authorized to give consent;"
  ],
  "full_text": "(A) No person, with purpose to deprive the owner of property or services...\n(1) Without the consent...",
  "word_count": 456,
  "paragraph_count": 12,
  "has_citations": true,
  "citation_count": 3,
  "in_complex_chain": false,
  "is_clickable": true,
  "scraped_date": "2025-11-25T12:34:56Z",
  "enrichment": {
    "summary": "Defines the crime of theft and its various forms",
    "legal_type": "criminal_statute",
    "practice_areas": ["criminal_law"],
    "complexity": 4,
    "key_terms": ["theft", "deprive", "property", "services"],
    "offense_level": "felony",
    "offense_degree": "F5"
  }
}
```

---

## Citations Database Schema

**Purpose**: Forward citations (what this item references)
**Key**: Section identifier (e.g., `b'2913.02'`)
**Value**: JSON object

**Note**: If a section has no citations, the key will NOT exist in this database.

### Schema

```typescript
{
  section: string,                     // Source section ID
  direct_references: string[],         // Array of referenced section IDs
  reference_count: number,             // Length of direct_references
  references_details: [
    {
      section: string,                 // Target section ID
      title: string,                   // Target section title
      url: string,                     // Target section URL
      url_hash: string,                // Target URL hash
      relationship: string,            // "cross_reference", "defines", "cites", "amends", "supersedes"
      context: string,                 // Surrounding text (max 100 chars)
      position: number                 // Position in source text (0-indexed character position)
    }
  ]
}
```

### Example Entry

```json
{
  "section": "2913.02",
  "direct_references": ["2913.01", "2913.03", "2901.21"],
  "reference_count": 3,
  "references_details": [
    {
      "section": "2913.01",
      "title": "Theft-related definitions",
      "url": "https://codes.ohio.gov/ohio-revised-code/section-2913.01",
      "url_hash": "sha256:def456...",
      "relationship": "defines",
      "context": "As used in sections 2913.01 to 2913.34 of the Revised Code",
      "position": 45
    }
  ]
}
```

---

## Reverse Citations Database Schema

**Purpose**: Backward citations (what items cite this one)
**Key**: Section identifier (e.g., `b'2913.01'`)
**Value**: JSON object

**Note**: If a section is not cited by anything, the key will NOT exist in this database.

### Schema

```typescript
{
  section: string,                     // Target section ID
  cited_by: string[],                  // Array of citing section IDs (sorted)
  cited_by_count: number,              // Length of cited_by array (authority indicator)
  citing_details: [
    {
      section: string,                 // Citing section ID
      title: string,                   // Citing section title
      url: string                      // Citing section URL
    }
  ]
}
```

### Example Entry

```json
{
  "section": "2913.01",
  "cited_by": ["2913.02", "2913.03", "2913.04", "2913.11"],
  "cited_by_count": 47,
  "citing_details": [
    {
      "section": "2913.02",
      "title": "Theft",
      "url": "https://codes.ohio.gov/ohio-revised-code/section-2913.02"
    }
  ]
}
```

**Authority Indicator**: High `cited_by_count` means this section is foundational/important.

---

## Chains Database Schema

**Purpose**: Pre-computed citation chains for complex relationships
**Key**: Chain ID (same as primary section ID, e.g., `b'2913.02'`)
**Value**: JSON object

**Note**: Only sections that are part of complex citation chains (depth >= 3 typically) will have entries.

### Schema

```typescript
{
  chain_id: string,                    // Primary section ID
  primary_section: string,             // Starting section
  chain_sections: string[],            // All sections in chain (ordered)
  chain_depth: number,                 // Number of sections in chain
  references_count: number,            // Total references in chain
  created_at: string,                  // ISO8601 timestamp
  complete_chain: [
    {
      section: string,                 // Section ID
      title: string,                   // Section title
      url: string,                     // Section URL
      url_hash: string,                // URL hash
      full_text: string,               // Complete legal text
      word_count: number               // Words in this section
    }
  ]
}
```

### Example Entry

```json
{
  "chain_id": "2913.02",
  "primary_section": "2913.02",
  "chain_sections": ["2913.02", "2913.01", "2901.21", "1.01"],
  "chain_depth": 4,
  "references_count": 3,
  "created_at": "2025-11-25T12:45:00Z",
  "complete_chain": [
    {
      "section": "2913.02",
      "title": "Theft",
      "url": "https://codes.ohio.gov/ohio-revised-code/section-2913.02",
      "url_hash": "sha256:abc123...",
      "full_text": "(A) No person, with purpose to deprive...",
      "word_count": 456
    }
  ]
}
```

**Use Case**: Deep research, graph visualization, LLM context building

---

## Metadata Database Schema

**Purpose**: Corpus-level metadata and statistics
**Key**: `b'corpus_info'` OR `b'inbound_count_{section_id}'`
**Value**: JSON object (schema varies by key type)

### corpus_info Schema

```typescript
{
  total_sections: number,              // Total items in primary.lmdb
  sections_with_citations: number,     // Items that cite others
  complex_chains: number,              // Number of citation chains
  reverse_citations: number,           // Items cited by others
  build_date: string,                  // ISO8601 build timestamp
  source: string,                      // Source URL
  version: string,                     // Builder version
  builder: string,                     // Builder script name
  databases: {
    primary: string,                   // Description
    citations: string,                 // Description
    reverse_citations: string,         // Description
    chains: string,                    // Description
    metadata: string                   // Description
  }
}
```

### inbound_count Schema

```typescript
{
  section: string,                     // Section ID
  count: number                        // Number of times cited
}
```

### Example Entries

```json
// Key: b'corpus_info'
{
  "total_sections": 40000,
  "sections_with_citations": 15678,
  "complex_chains": 2345,
  "reverse_citations": 12456,
  "build_date": "2025-11-25T13:00:00Z",
  "source": "https://codes.ohio.gov/ohio-revised-code",
  "version": "2.0",
  "builder": "comprehensive_lmdb_builder",
  "databases": {
    "primary": "Full section text with metadata and enrichment",
    "citations": "Forward citation references with relationship types",
    "reverse_citations": "Backward citation references (authority analysis)",
    "chains": "Complex citation chains with full text",
    "metadata": "Corpus and section metadata"
  }
}

// Key: b'inbound_count_2913.01'
{
  "section": "2913.01",
  "count": 47
}
```

---

## Zero-Drift Architecture

### How It Works

```
ohio-legal-ai.io (Application Repository)
  ↓
  Pydantic Models (Source of Truth)
  ↓
  09_lmdb_schema_generator.py
  ↓
  Generates TypedDict Schemas
  ↓
ohio_code (Data Pipeline Repository)
  ↓
  generated_schemas.py (auto-generated)
  ↓
  build_comprehensive_lmdb.py (uses schemas)
  ↓
  LMDB Databases
  ↓
ohio-legal-ai.io (Application Repository)
  ↓
  Knowledge Service (reads LMDB)
  ↓
  Maps back to Pydantic Models (guaranteed match)
```

### Using Generated Schemas in LMDB Builders

```python
# Import generated schemas for type validation
from generated_schemas import (
    OhioSectionDict,
    CitationDataDict,
    ReverseCitationDataDict,
    CitationChainDict
)

# Type-annotate dictionary creation
section_data: OhioSectionDict = {
    'section_number': section_num,
    'url': doc.get('url', ''),
    'url_hash': doc.get('url_hash', ''),
    'header': header,
    'section_title': section_title,
    'paragraphs': paragraphs,  # EXACT LEGAL TEXT - NEVER MODIFIED
    'full_text': '\n'.join(paragraphs),
    'word_count': len(' '.join(paragraphs).split()),
    'paragraph_count': len(paragraphs),
    'has_citations': bool(citations),
    'citation_count': len(citations),
    'in_complex_chain': section_num in chains,
    'is_clickable': has_citations or has_reverse_citations,
    'scraped_date': datetime.now().isoformat(),
    'enrichment': auto_enricher.enrich_section(section_data)
}
```

### Benefits

1. **IDE Autocomplete**: Type hints show available fields
2. **Type Checking**: Catch schema mismatches at development time
3. **Zero Drift**: LMDB structure always matches Pydantic models
4. **Self-Documentation**: Code clearly shows expected structure

### Workflow When Adding New Fields

1. Edit Pydantic model in `ohio-legal-ai.io`
2. Regenerate schemas: `python 09_lmdb_schema_generator.py`
3. Schemas auto-update in `ohio_code/*/lmdb/generated_schemas.py`
4. Update LMDB builder to populate new field
5. Rebuild LMDB databases
6. Knowledge service automatically reads new fields

---

## Future Enhancement Phases

### Phase 2: Extractable Metadata (2-3 weeks)

**Goal**: Add organizational and temporal context without LLM

**Implementation**:
```python
# Extract chapter from section number
def extract_chapter(section_number: str) -> str:
    # "2913.02" → "2913"
    return section_number.split('.')[0]

# Default treatment status
treatment_status = "valid"  # Assume current law is valid

# Court hierarchy (case law only)
court_levels = {
    "supreme_court": {
        "binding_on": ["all_ohio_courts"],
        "precedent_value": "binding"
    },
    "appellate": {
        "binding_on": ["trial_courts_in_district"],
        "precedent_value": "persuasive"
    }
}
```

### Phase 3: Graph Metrics (3-4 weeks)

**Goal**: Compute authority scores and network metrics

**Implementation**:
```python
import networkx as nx

# Build citation graph
G = nx.DiGraph()
for section, citations in citation_map.items():
    for cited in citations:
        G.add_edge(section, cited)

# Compute PageRank authority
authority_scores = nx.pagerank(G, alpha=0.85)

# Compute centrality
centrality = nx.betweenness_centrality(G)

# Citation velocity (citations per year)
velocity = count_recent_citations(section_id) / 5  # Last 5 years
```

### Phase 4: LLM Enhancement (Optional)

**Goal**: Improved semantic analysis

**Implementation**:
- Better summaries using Claude/GPT
- Deeper practice area classification
- Holdings extraction (case law)
- Fact pattern identification

### Phase 5: Relationship Tracking (Advanced)

**Goal**: Legal relationship detection

**Implementation**:
- Treatment detection (overruled, superseded)
- Shepardization system
- Temporal validity chains
- Transitive invalidation logic

---

## API Contract

### Knowledge Service Endpoints

| Endpoint | LMDB Database | Response Schema |
|----------|---------------|-----------------|
| `GET /sections/{id}` | primary.lmdb | OhioSectionDict |
| `GET /sections/{id}/citations` | citations.lmdb | CitationDataDict |
| `GET /sections/{id}/reverse-citations` | reverse_citations.lmdb | ReverseCitationDataDict |
| `GET /sections/{id}/chain` | chains.lmdb | CitationChainDict |
| `GET /corpus/info` | metadata.lmdb | CorpusInfoDict |

### Response Size Estimates

| Endpoint | Typical Size | Use Case |
|----------|-------------|----------|
| `/sections/{id}` | 2-10 KB | Display statute |
| `/sections/{id}/citations` | 1-5 KB | Show related sections |
| `/sections/{id}/reverse-citations` | 1-20 KB | Authority analysis |
| `/sections/{id}/chain` | **50-500 KB** | Deep research, LLM context |
| `/corpus/info` | 1 KB | Stats, health check |

**⚠️ Warning**: Complete chains can be **very large** (15+ sections with full text). Only request when needed.

---

## Breaking Changes Protocol

**⚠️ IF YOU MUST CHANGE THE SCHEMA:**

1. Update this document first
2. Update Pydantic models in `ohio-legal-ai.io`
3. Regenerate TypedDict schemas
4. Update all LMDB builders in `ohio_code`
5. Update knowledge service code
6. Rebuild ALL LMDB databases
7. Test ALL endpoints
8. Update API documentation

**NEVER change one side without the other!**

---

## Key Principles

1. **Legal text is sacred**: `paragraphs` and `full_text` are EXACT SOURCE - never modified
2. **Storage schema ≠ API schema**: LMDB stores raw data, API may transform for presentation
3. **enrichment is optional**: All enrichment fields may be null, application must handle gracefully
4. **is_clickable is UI-specific**: Helps frontend know if item has citation graph data
5. **Corpus-agnostic structure**: All corpora use same schema, different section_number formats
6. **Relationship data is rich**: Citations include context, position, and relationship type
7. **Zero-drift by design**: Automated schema generation prevents drift between repos

---

## Summary

**Current Status:**
- ✅ Core storage fields: **COMPLETE** (Phase 1)
- ✅ Citation graph: **COMPLETE** (Phase 1)
- ✅ Auto-enrichment: **COMPLETE** (Phase 1)
- 📋 Extractable metadata: **NEXT PRIORITY** (Phase 2)
- 🧮 Graph metrics: **MEDIUM TERM** (Phase 3)
- 🤖 LLM enhancement: **OPTIONAL** (Phase 4)
- 🔗 Relationship tracking: **ADVANCED** (Phase 5)

**This document replaces:**
- ✅ ACTUAL_LMDB_SCHEMAS.md
- ✅ LMDB_API_CONTRACT.md
- ✅ LMDB_SCHEMA_IMPLEMENTATION_PHASES.md
- ✅ SIMPLIFIED_LMDB_ENRICHMENT_FINAL.md
- ✅ USING_GENERATED_SCHEMAS.md

**Single source of truth**: This file (`LMDB_SCHEMA_REFERENCE.md`)

---

*Keep this document updated as schemas evolve. This is the contract between data pipeline and application.*