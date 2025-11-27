# Actual LMDB Schemas Being Built

**Date:** 2025-11-20
**Status:** CURRENT IMPLEMENTATION
**Source:** Analyzed from `build_comprehensive_lmdb.py` across all corpora

---

## ⚠️ SCHEMA STATUS CLARIFICATION

**The generated schemas in `generated_schemas.py` represent the FULL VISION for this legal research platform.**

- **Generated schemas**: Include all fields for graph metrics, enrichment, and temporal tracking
- **Currently populated**: Core storage fields + citation graph (see Phase 1 below)
- **Planned implementation**: Additional fields will be populated incrementally (Phases 2-5)

**This document describes what is CURRENTLY being populated in LMDB databases.**
**See `LMDB_SCHEMA_IMPLEMENTATION_PHASES.md` for the full roadmap.**

---

## 1. primary.lmdb Schema

**Purpose:** Main content storage for legal documents
**Key:** Section identifier (e.g., `b'2913.02'`, `b'2023-Ohio-1234'`)
**Value:** JSON object with this structure:

### ✅ Currently Populated (Phase 1)

```typescript
{
  // Core identifiers
  "section_number": string,        // Unique ID (format varies by corpus)
  "url": string,                   // Source URL
  "url_hash": string,              // Hash of URL

  // Display fields
  "header": string,                // Full header with title pipe-delimited
  "section_title": string,         // Title only (extracted from header)

  // Legal text (PRESERVED - never modified)
  "paragraphs": string[],          // Array of paragraph strings
  "full_text": string,             // All paragraphs joined with \n

  // Content metrics
  "word_count": number,            // Total words in full_text
  "paragraph_count": number,       // Number of paragraphs

  // Citation metadata
  "has_citations": boolean,        // True if this item cites others
  "citation_count": number,        // Number of forward citations
  "in_complex_chain": boolean,     // True if part of a citation chain
  "is_clickable": boolean,         // True if has forward OR reverse citations (for UI)

  // Timestamp
  "scraped_date": string,          // ISO8601 datetime when data was scraped

  // AI-generated enrichment (✅ STRUCTURE EXISTS, 🤖 POPULATION PLANNED - Phase 4)
  "enrichment": {
    "summary": string | null,              // Plain language summary (Phase 4)
    "legal_type": string | null,           // "criminal_statute", "civil_statute", etc. (Phase 4)
    "practice_areas": string[] | null,     // ["criminal_law", "family_law", ...] (Phase 4)
    "complexity": number | null,           // 1-10 scale (Phase 4)
    "key_terms": string[] | null,          // Important legal terms (Phase 4)
    "offense_level": string | null,        // "felony", "misdemeanor" (Phase 4)
    "offense_degree": string | null        // "F1"-"F5", "M1"-"M4" (Phase 4)
  }
}
```

### 📋 Planned for Phase 2 (Extractable Metadata)

```typescript
{
  // Organizational hierarchy
  "chapter": string | null,              // Extract from section_number
  "title": string | null,                // Extract from header structure

  // Temporal validity
  "valid_from": string | null,           // ISO8601 date
  "valid_until": string | null,          // ISO8601 date or null if current
  "treatment_status": string | null,     // "valid", "overruled", "superseded", etc.

  // Case law specific (ohio_caselaw corpus only)
  "court_level": string | null,          // "supreme_court", "appellate", "trial"
  "binding_on": string[] | null,         // List of courts this binds
  "precedent_value": string | null       // "binding", "persuasive"
}
```

### 🧮 Planned for Phase 3 (Graph Metrics)

```typescript
{
  // Network analysis (computed from citation graph)
  "authority_score": float | null,       // PageRank-based authority (0-1)
  "betweenness_centrality": float | null, // Network centrality (0-1)
  "citation_velocity": float | null      // Recent citations per year
}
```

### 🔗 Planned for Phase 5 (Relationship Tracking)

```typescript
{
  // Legal relationship tracking
  "invalidated_by": string | null,       // Reference to invalidating case/law
  "superseded_by": string | null         // Reference to superseding law
}
```

### Example Entry:

```json
{
  "section_number": "2913.02",
  "url": "https://codes.ohio.gov/ohio-revised-code/section-2913.02",
  "url_hash": "sha256:abc123...",
  "header": "Section 2913.02|Theft",
  "section_title": "Theft",
  "paragraphs": [
    "(A) No person, with purpose to deprive the owner of property or services, shall knowingly obtain or exert control over either the property or services in any of the following ways:",
    "(1) Without the consent of the owner or person authorized to give consent;",
    "..."
  ],
  "full_text": "(A) No person, with purpose to deprive...\n(1) Without the consent...",
  "word_count": 456,
  "paragraph_count": 12,
  "has_citations": true,
  "citation_count": 3,
  "in_complex_chain": false,
  "is_clickable": true,
  "scraped_date": "2025-11-20T12:34:56",
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

### Corpus-Specific Variations:

| Corpus | section_number format | Content type | header format |
|--------|----------------------|--------------|---------------|
| ohio_revised | "2913.02" | Statutory sections | "Section 2913.02\|Theft" |
| ohio_administration | "3701-17-01" | Administrative rules | "Rule 3701-17-01\|Title" |
| ohio_constitution | "Article I, Section 1" | Constitutional articles | "Article I, Section 1\|Title" |
| ohio_caselaw | "2023-Ohio-1234" | Court opinions | "State v. Smith\|Citation" |

---

## 2. citations.lmdb Schema (ACTUAL)

**Purpose:** Forward citations (what this item references)
**Key:** Section identifier (e.g., `b'2913.02'`)
**Value:** JSON object:

```typescript
{
  "section": string,                     // Source section ID
  "direct_references": string[],         // Array of referenced section IDs
  "reference_count": number,             // Length of direct_references
  "references_details": [
    {
      "section": string,                 // Target section ID
      "title": string,                   // Target section title
      "url": string,                     // Target section URL
      "url_hash": string,                // Target URL hash
      "relationship": string,            // "cross_reference", "defines", "cites", etc.
      "context": string,                 // Surrounding text (max 100 chars)
      "position": number                 // Position in source text (0-indexed)
    }
  ]
}
```

### Example Entry:

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
    },
    {
      "section": "2913.03",
      "title": "Unauthorized use of vehicle",
      "url": "https://codes.ohio.gov/ohio-revised-code/section-2913.03",
      "url_hash": "sha256:ghi789...",
      "relationship": "cross_reference",
      "context": "Except as otherwise provided in division (C) of section 2913.03",
      "position": 123
    },
    {
      "section": "2901.21",
      "title": "Requirements for criminal liability",
      "url": "https://codes.ohio.gov/ohio-revised-code/section-2901.21",
      "url_hash": "sha256:jkl012...",
      "relationship": "cites",
      "context": "with purpose as defined in section 2901.21 of the Revised Code",
      "position": 67
    }
  ]
}
```

**Note:** If a section has no citations, the key will NOT exist in this database.

---

## 3. reverse_citations.lmdb Schema (ACTUAL)

**Purpose:** Backward citations (what items cite this one)
**Key:** Section identifier (e.g., `b'2913.01'`)
**Value:** JSON object:

```typescript
{
  "section": string,                     // Target section ID
  "cited_by": string[],                  // Array of citing section IDs (sorted)
  "cited_by_count": number,              // Length of cited_by array
  "citing_details": [
    {
      "section": string,                 // Citing section ID
      "title": string,                   // Citing section title
      "url": string                      // Citing section URL
    }
  ]
}
```

### Example Entry:

```json
{
  "section": "2913.01",
  "cited_by": ["2913.02", "2913.03", "2913.04", "2913.11"],
  "cited_by_count": 4,
  "citing_details": [
    {
      "section": "2913.02",
      "title": "Theft",
      "url": "https://codes.ohio.gov/ohio-revised-code/section-2913.02"
    },
    {
      "section": "2913.03",
      "title": "Unauthorized use of vehicle",
      "url": "https://codes.ohio.gov/ohio-revised-code/section-2913.03"
    },
    {
      "section": "2913.04",
      "title": "Unauthorized use of property",
      "url": "https://codes.ohio.gov/ohio-revised-code/section-2913.04"
    },
    {
      "section": "2913.11",
      "title": "Passing bad checks",
      "url": "https://codes.ohio.gov/ohio-revised-code/section-2913.11"
    }
  ]
}
```

**Note:** If a section is not cited by anything, the key will NOT exist in this database.

---

## 4. chains.lmdb Schema (ACTUAL)

**Purpose:** Pre-computed citation chains for complex relationships
**Key:** Chain ID (same as primary section ID, e.g., `b'2913.02'`)
**Value:** JSON object:

```typescript
{
  "chain_id": string,                    // Primary section ID
  "primary_section": string,             // Starting section
  "chain_sections": string[],            // All sections in chain (ordered)
  "chain_depth": number,                 // Number of sections in chain
  "references_count": number,            // Total references in chain
  "created_at": string,                  // ISO8601 timestamp
  "complete_chain": [
    {
      "section": string,                 // Section ID
      "title": string,                   // Section title
      "url": string,                     // Section URL
      "url_hash": string,                // URL hash
      "full_text": string,               // Complete legal text
      "word_count": number               // Words in this section
    }
  ]
}
```

### Example Entry:

```json
{
  "chain_id": "2913.02",
  "primary_section": "2913.02",
  "chain_sections": ["2913.02", "2913.01", "2901.21", "1.01"],
  "chain_depth": 4,
  "references_count": 3,
  "created_at": "2025-11-20T12:45:00",
  "complete_chain": [
    {
      "section": "2913.02",
      "title": "Theft",
      "url": "https://codes.ohio.gov/ohio-revised-code/section-2913.02",
      "url_hash": "sha256:abc123...",
      "full_text": "(A) No person, with purpose to deprive...",
      "word_count": 456
    },
    {
      "section": "2913.01",
      "title": "Theft-related definitions",
      "url": "https://codes.ohio.gov/ohio-revised-code/section-2913.01",
      "url_hash": "sha256:def456...",
      "full_text": "As used in sections 2913.01 to 2913.34...",
      "word_count": 234
    },
    {
      "section": "2901.21",
      "title": "Requirements for criminal liability",
      "url": "https://codes.ohio.gov/ohio-revised-code/section-2901.21",
      "url_hash": "sha256:ghi789...",
      "full_text": "A person is not guilty of an offense...",
      "word_count": 567
    },
    {
      "section": "1.01",
      "title": "Definitions",
      "url": "https://codes.ohio.gov/ohio-revised-code/section-1.01",
      "url_hash": "sha256:jkl012...",
      "full_text": "As used in the Revised Code...",
      "word_count": 123
    }
  ]
}
```

**Note:** Only sections that are part of complex citation chains (depth >= 3 typically) will have entries in this database.

---

## 5. metadata.lmdb Schema (ACTUAL)

**Purpose:** Corpus-level metadata and statistics
**Key:** `b'corpus_info'` (special literal key) OR `b'inbound_count_{section_id}'`
**Value:** JSON object (different schemas for different keys)

### corpus_info Entry:

```typescript
{
  "total_sections": number,              // Total items in primary.lmdb
  "sections_with_citations": number,     // Items that cite others
  "complex_chains": number,              // Number of citation chains
  "reverse_citations": number,           // Items cited by others
  "build_date": string,                  // ISO8601 build timestamp
  "source": string,                      // Source URL
  "version": string,                     // Builder version
  "builder": string,                     // Builder script name
  "databases": {
    "primary": string,                   // Description
    "citations": string,                 // Description
    "reverse_citations": string,         // Description
    "chains": string,                    // Description
    "metadata": string                   // Description
  }
}
```

### inbound_count Entry:

```typescript
{
  "section": string,                     // Section ID
  "count": number                        // Number of times cited
}
```

### Example Entries:

```json
// Key: b'corpus_info'
{
  "total_sections": 40123,
  "sections_with_citations": 15678,
  "complex_chains": 2345,
  "reverse_citations": 12456,
  "build_date": "2025-11-20T13:00:00",
  "source": "https://codes.ohio.gov/ohio-revised-code",
  "version": "2.0",
  "builder": "comprehensive_lmdb_builder",
  "databases": {
    "primary": "Full section text with metadata",
    "citations": "Forward citation references",
    "reverse_citations": "Backward citation references",
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

## Summary: Implementation Status

### ✅ COMPLETE (Phase 1):
- Core storage fields (section_number, url, header, paragraphs, full_text, etc.)
- Citation graph structure (forward and reverse citations)
- Citation chains for complex relationships
- Corpus metadata and statistics

### 📋 NEXT PRIORITY (Phase 2):
- Extract `chapter` and `title` from existing data
- Add basic `treatment_status` (default to "valid")
- Court hierarchy for case law corpus

### 🤖 MEDIUM TERM (Phases 3-4):
- AI enrichment pipeline (summaries, legal types, practice areas)
- Graph metrics computation (authority scores, centrality)

### 🔗 LONG TERM (Phase 5):
- Relationship tracking (invalidated_by, superseded_by)
- Temporal validity windows

**See `LMDB_SCHEMA_IMPLEMENTATION_PHASES.md` for detailed roadmap and implementation guide.**

---

## Key Insights:

1. **Storage schema ≠ API schema**: LMDB stores raw legal text with enrichment, API may return transformed data
2. **enrichment is optional**: Many fields may be null, application must handle gracefully
3. **is_clickable is UI-specific**: Helps frontend know if item has citation graph data
4. **Corpus-agnostic structure**: All corpora use same schema, just different section_number formats
5. **Relationship data is rich**: Citations include context, position, and relationship type

This is the TRUE contract that must be maintained!