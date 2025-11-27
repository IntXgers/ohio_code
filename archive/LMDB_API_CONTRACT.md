# LMDB API Contract - Frontend Reference

**Purpose:** This document shows exactly what data structures the frontend receives from Knowledge Service API endpoints that read LMDB databases.

**Audience:** Frontend developers, API consumers, Temporal activity authors

**Last Updated:** 2025-11-21

---

## Overview

The Knowledge Service (port 8001) reads from 5 LMDB databases and returns JSON. This document shows the exact structure of each response.

### The 5 LMDB Databases

| Database | Purpose | Key Format | Used For |
|----------|---------|------------|----------|
| **primary.lmdb** | Full statute text + metadata | `"2903.13"` | Main content, search results |
| **citations.lmdb** | Forward citations (what this cites) | `"2903.13"` | Citation graph, related sections |
| **reverse_citations.lmdb** | Backward citations (what cites this) | `"2903.13"` | Authority analysis, importance |
| **chains.lmdb** | Pre-computed citation chains | `"2903.13"` | Deep research, graph visualization |
| **metadata.lmdb** | Corpus statistics | `"corpus_info"` | Stats dashboard, health checks |

---

## 1. Primary Database (Statute Content)

**Endpoint:** `GET /sections/{section_id}`

**What it returns:** Complete statute with full text, metadata, and enrichment.

### Response Structure

```typescript
{
  // Core identifiers
  section_number: string;              // "2903.13"
  url: string;                         // "https://codes.ohio.gov/ohio-revised-code/section-2903.13"
  url_hash: string;                    // "sha256:abc123..."

  // Display fields
  header: string;                      // "Section 2903.13|Assault"
  section_title: string;               // "Assault"

  // Legal text (array preserves paragraph structure)
  paragraphs: string[];                // ["(A) No person shall...", "(B) Whoever..."]
  full_text: string;                   // All paragraphs joined with \n

  // Content metrics
  word_count: number;                  // 347
  paragraph_count: number;             // 5

  // Citation metadata (for UI)
  has_citations: boolean;              // true if this cites other sections
  citation_count: number;              // 3 (number of forward citations)
  in_complex_chain: boolean;           // true if part of pre-computed chain
  is_clickable: boolean;               // true if has forward OR reverse citations

  // Timestamp
  scraped_date: string;                // "2025-11-20T12:34:56Z"

  // AI-generated enrichment (may be null)
  enrichment: {
    summary: string | null;            // "Defines the crime of assault and penalties"
    legal_type: string | null;         // "criminal_statute" | "civil_statute" | "definitional" | "procedural"
    practice_areas: string[] | null;   // ["criminal_law"]
    complexity: number | null;         // 1-10 scale
    key_terms: string[] | null;        // ["assault", "physical harm", "recklessly"]
    offense_level: string | null;      // "felony" | "misdemeanor" (criminal statutes only)
    offense_degree: string | null;     // "F1"-"F5", "M1"-"M4" (criminal statutes only)
  } | null;

  // Phase 2+ fields (may be null until computed)
  treatment_status?: string;           // "valid" | "overruled" | "superseded" | "questioned"
  invalidated_by?: string;             // Section/case that invalidated this
  superseded_by?: string;              // Section that superseded this
  valid_from?: string;                 // "2020-01-01" (ISO date)
  valid_until?: string;                // "2025-12-31" or null if still valid

  // Graph metrics (Phase 3 - computed during LMDB build)
  authority_score?: number;            // 0.0-1.0 (PageRank score)
  betweenness_centrality?: number;     // 0.0-1.0 (network centrality)
  citation_velocity?: number;          // Citations per year

  // Court hierarchy (case law only)
  court_level?: string;                // "supreme_court" | "appellate" | "trial"
  binding_on?: string[];               // ["all_ohio_courts"] or ["district_5"]
  precedent_value?: string;            // "binding" | "persuasive"

  // Organizational (Phase 2 - extracted from section_number)
  title?: string;                      // "29" (ORC Title - criminal code)
  chapter?: string;                    // "2903" (ORC Chapter)
}
```

### Example Response

```json
{
  "section_number": "2903.13",
  "url": "https://codes.ohio.gov/ohio-revised-code/section-2903.13",
  "url_hash": "sha256:a1b2c3d4e5f6...",
  "header": "Section 2903.13|Assault",
  "section_title": "Assault",
  "paragraphs": [
    "(A) No person shall knowingly cause or attempt to cause physical harm to another or to another's unborn.",
    "(B) No person shall recklessly cause serious physical harm to another or to another's unborn.",
    "(C) Whoever violates this section is guilty of assault..."
  ],
  "full_text": "(A) No person shall knowingly cause or attempt to cause physical harm to another or to another's unborn.\n(B) No person shall recklessly cause serious physical harm...",
  "word_count": 347,
  "paragraph_count": 5,
  "has_citations": true,
  "citation_count": 3,
  "in_complex_chain": true,
  "is_clickable": true,
  "scraped_date": "2025-11-20T12:34:56Z",
  "enrichment": {
    "summary": "Defines the crime of assault, including knowingly causing physical harm and recklessly causing serious harm, with penalties ranging from misdemeanor to felony depending on circumstances.",
    "legal_type": "criminal_statute",
    "practice_areas": ["criminal_law"],
    "complexity": 4,
    "key_terms": ["assault", "physical harm", "serious physical harm", "recklessly", "knowingly"],
    "offense_level": "misdemeanor",
    "offense_degree": "M1"
  },
  "treatment_status": "valid",
  "title": "29",
  "chapter": "2903"
}
```

### Frontend Usage

```typescript
// Display statute card
<StatuteCard>
  <h2>{section.section_title}</h2>
  <Badge color={section.enrichment?.legal_type}>
    {section.enrichment?.legal_type}
  </Badge>

  <p className="summary">{section.enrichment?.summary}</p>

  {section.paragraphs.map(p => (
    <p className="legal-text">{p}</p>
  ))}

  <CitationBadge
    count={section.citation_count}
    clickable={section.is_clickable}
  />
</StatuteCard>
```

---

## 2. Citations Database (Forward Citations)

**Endpoint:** `GET /sections/{section_id}/citations`

**What it returns:** What sections this statute cites (forward references).

### Response Structure

```typescript
{
  section: string;                     // "2903.13" (source section)
  direct_references: string[];         // ["2901.22", "2903.11", "2929.13"]
  reference_count: number;             // 3
  references_details: [
    {
      section: string;                 // "2901.22" (target section)
      title: string;                   // "Criminal liability definitions"
      url: string;                     // "https://codes.ohio.gov/..."
      url_hash: string;                // "sha256:..."
      relationship: string;            // "defines" | "cross_reference" | "cites" | "amends" | "supersedes"
      context: string;                 // "...with purpose as defined in section 2901.22..." (max 100 chars)
      position: number;                // 67 (character position in source text)
    }
  ]
}
```

### Example Response

```json
{
  "section": "2903.13",
  "direct_references": ["2901.22", "2903.11", "2929.13"],
  "reference_count": 3,
  "references_details": [
    {
      "section": "2901.22",
      "title": "Criminal liability - culpable mental states",
      "url": "https://codes.ohio.gov/ohio-revised-code/section-2901.22",
      "url_hash": "sha256:def456...",
      "relationship": "defines",
      "context": "...with purpose to deprive as defined in section 2901.22 of the Revised Code...",
      "position": 45
    },
    {
      "section": "2903.11",
      "title": "Felonious assault",
      "url": "https://codes.ohio.gov/ohio-revised-code/section-2903.11",
      "url_hash": "sha256:ghi789...",
      "relationship": "cross_reference",
      "context": "...in the manner described in division (A) of section 2903.11...",
      "position": 234
    },
    {
      "section": "2929.13",
      "title": "Felony sentencing guidelines",
      "url": "https://codes.ohio.gov/ohio-revised-code/section-2929.13",
      "url_hash": "sha256:jkl012...",
      "relationship": "cites",
      "context": "...shall be sentenced pursuant to section 2929.13 of the Revised Code...",
      "position": 567
    }
  ]
}
```

### Frontend Usage

```typescript
// Display related sections
<RelatedSections>
  <h3>This section cites:</h3>
  {citations.references_details.map(ref => (
    <CitationLink
      section={ref.section}
      title={ref.title}
      relationship={ref.relationship}
      context={ref.context}
    />
  ))}
</RelatedSections>

// Build citation graph
const nodes = citations.references_details.map(ref => ({
  id: ref.section,
  label: ref.title,
  relationship: ref.relationship
}));
```

---

## 3. Reverse Citations Database (Backward Citations)

**Endpoint:** `GET /sections/{section_id}/reverse-citations`

**What it returns:** What sections cite this statute (backward references = authority analysis).

### Response Structure

```typescript
{
  section: string;                     // "2901.22" (this is the cited section)
  cited_by: string[];                  // ["2903.13", "2913.02", "2917.11", ...] (sorted)
  cited_by_count: number;              // 47 (authority indicator - heavily cited)
  citing_details: [
    {
      section: string;                 // "2903.13" (section that cites this)
      title: string;                   // "Assault"
      url: string;                     // "https://codes.ohio.gov/..."
    }
  ]
}
```

### Example Response

```json
{
  "section": "2901.22",
  "cited_by": ["2903.11", "2903.13", "2913.02", "2917.11"],
  "cited_by_count": 47,
  "citing_details": [
    {
      "section": "2903.13",
      "title": "Assault",
      "url": "https://codes.ohio.gov/ohio-revised-code/section-2903.13"
    },
    {
      "section": "2913.02",
      "title": "Theft",
      "url": "https://codes.ohio.gov/ohio-revised-code/section-2913.02"
    },
    {
      "section": "2917.11",
      "title": "Disorderly conduct",
      "url": "https://codes.ohio.gov/ohio-revised-code/section-2917.11"
    }
  ]
}
```

### Frontend Usage

```typescript
// Display authority indicator
<AuthorityBadge count={reverseCitations.cited_by_count}>
  Cited by {reverseCitations.cited_by_count} other sections
</AuthorityBadge>

// Show citing sections
<CitedByList>
  <h3>Sections that cite this:</h3>
  {reverseCitations.citing_details.map(citing => (
    <Link to={`/section/${citing.section}`}>
      {citing.section}: {citing.title}
    </Link>
  ))}
</CitedByList>

// Authority ranking (high citation count = important section)
const authorityRank = reverseCitations.cited_by_count > 20 ? 'high' : 'medium';
```

---

## 4. Citation Chains Database (Complex Relationships)

**Endpoint:** `GET /sections/{section_id}/complete-chain`

**What it returns:** Pre-computed citation chain with full text of all related sections.

**Use case:** Deep research workflows, graph visualization, "get everything I need" queries.

### Response Structure

```typescript
{
  chain_id: string;                    // "2903.13" (same as primary section)
  primary_section: string;             // "2903.13" (starting point)
  chain_sections: string[];            // ["2903.13", "2901.22", "2903.11", "2929.13"]
  chain_depth: number;                 // 3 (max hops from primary)
  references_count: number;            // 4 (total sections in chain)
  created_at: string;                  // "2025-11-20T13:00:00Z"
  complete_chain: [                    // Full text of all sections
    {
      section: string;                 // "2903.13"
      title: string;                   // "Assault"
      url: string;                     // Full URL
      url_hash: string;                // Hash
      full_text: string;               // Complete legal text (could be 1000+ words)
      word_count: number;              // 347
    }
  ]
}
```

### Example Response

```json
{
  "chain_id": "2903.13",
  "primary_section": "2903.13",
  "chain_sections": ["2903.13", "2901.22", "2903.11", "2929.13"],
  "chain_depth": 3,
  "references_count": 4,
  "created_at": "2025-11-20T13:00:00Z",
  "complete_chain": [
    {
      "section": "2903.13",
      "title": "Assault",
      "url": "https://codes.ohio.gov/ohio-revised-code/section-2903.13",
      "url_hash": "sha256:abc123...",
      "full_text": "(A) No person shall knowingly cause or attempt to cause physical harm to another or to another's unborn.\n(B) No person shall recklessly cause serious physical harm...\n(Full 347 word statute text)",
      "word_count": 347
    },
    {
      "section": "2901.22",
      "title": "Criminal liability - culpable mental states",
      "url": "https://codes.ohio.gov/ohio-revised-code/section-2901.22",
      "url_hash": "sha256:def456...",
      "full_text": "(A) A person acts knowingly, regardless of purpose, when the person is aware that the person's conduct will probably cause a certain result...\n(Full 567 word statute text)",
      "word_count": 567
    },
    {
      "section": "2903.11",
      "title": "Felonious assault",
      "url": "https://codes.ohio.gov/ohio-revised-code/section-2903.11",
      "url_hash": "sha256:ghi789...",
      "full_text": "(A) No person shall knowingly do either of the following: (1) Cause serious physical harm to another...\n(Full 423 word statute text)",
      "word_count": 423
    }
  ]
}
```

### Frontend Usage

```typescript
// Send entire chain to LLM for analysis
const buildLLMPrompt = (chain: CitationChain) => {
  return `Analyze these ${chain.references_count} related Ohio statutes:

  ${chain.complete_chain.map(section => `
    STATUTE ${section.section}: ${section.title}
    ${section.full_text}
  `).join('\n\n')}

  User question: What are the penalties for assault?`;
};

// Visualize citation graph
const graphData = {
  nodes: chain.complete_chain.map(s => ({
    id: s.section,
    label: s.title,
    size: s.word_count / 10  // Node size based on text length
  })),
  edges: buildEdgesFromChain(chain.chain_sections)
};

<CitationGraphVisualization data={graphData} />
```

---

## 5. Metadata Database (Corpus Statistics)

**Endpoint:** `GET /corpus/metadata`

**What it returns:** Statistics about the entire legal corpus.

### Response Structure

```typescript
{
  total_sections: number;              // 23644 (total statutes in corpus)
  sections_with_citations: number;     // 15678 (statutes that cite others)
  complex_chains: number;              // 2345 (pre-computed chains)
  reverse_citations: number;           // 12456 (statutes cited by others)
  build_date: string;                  // "2025-11-20T13:00:00Z"
  source: string;                      // "https://codes.ohio.gov/ohio-revised-code"
  version: string;                     // "2.0"
  builder: string;                     // "comprehensive_lmdb_builder"
  databases: string[];                 // ["primary", "citations", "reverse_citations", "chains", "metadata"]
}
```

### Example Response

```json
{
  "total_sections": 23644,
  "sections_with_citations": 15678,
  "complex_chains": 2345,
  "reverse_citations": 12456,
  "build_date": "2025-11-20T13:00:00Z",
  "source": "https://codes.ohio.gov/ohio-revised-code",
  "version": "2.0",
  "builder": "comprehensive_lmdb_builder",
  "databases": ["primary", "citations", "reverse_citations", "chains", "metadata"]
}
```

### Frontend Usage

```typescript
// Stats dashboard
<CorpusStats>
  <Stat label="Total Statutes" value={metadata.total_sections.toLocaleString()} />
  <Stat label="With Citations" value={metadata.sections_with_citations.toLocaleString()} />
  <Stat label="Citation Chains" value={metadata.complex_chains.toLocaleString()} />
  <Stat label="Last Updated" value={formatDate(metadata.build_date)} />
</CorpusStats>

// Health check
const isStale = Date.now() - Date.parse(metadata.build_date) > 30 * 24 * 60 * 60 * 1000;
{isStale && <Warning>Corpus data is over 30 days old</Warning>}
```

---

## Common Frontend Patterns

### 1. Load Statute with Citations

```typescript
const loadStatuteWithCitations = async (sectionId: string) => {
  const [statute, citations, reverseCitations] = await Promise.all([
    fetch(`/sections/${sectionId}`),
    fetch(`/sections/${sectionId}/citations`),
    fetch(`/sections/${sectionId}/reverse-citations`)
  ]);

  return {
    statute: await statute.json(),
    citations: await citations.json(),
    reverseCitations: await reverseCitations.json()
  };
};
```

### 2. Build Citation Graph for Visualization

```typescript
const buildCitationGraph = (
  section: OhioSection,
  citations: CitationData,
  reverseCitations: ReverseCitationData
) => {
  const nodes = [
    { id: section.section_number, label: section.section_title, type: 'primary' },
    ...citations.references_details.map(ref => ({
      id: ref.section,
      label: ref.title,
      type: 'cited',
      relationship: ref.relationship
    })),
    ...reverseCitations.citing_details.map(citing => ({
      id: citing.section,
      label: citing.title,
      type: 'citing'
    }))
  ];

  const edges = [
    ...citations.references_details.map(ref => ({
      source: section.section_number,
      target: ref.section,
      label: ref.relationship
    })),
    ...reverseCitations.citing_details.map(citing => ({
      source: citing.section,
      target: section.section_number,
      label: 'cites'
    }))
  ];

  return { nodes, edges };
};
```

### 3. Authority Badge (Citation Count)

```typescript
const getAuthorityLevel = (citedByCount: number): string => {
  if (citedByCount > 50) return 'very-high';
  if (citedByCount > 20) return 'high';
  if (citedByCount > 5) return 'medium';
  return 'low';
};

<Badge level={getAuthorityLevel(reverseCitations.cited_by_count)}>
  Authority: {getAuthorityLevel(reverseCitations.cited_by_count)}
</Badge>
```

### 4. Deep Research Request (for Temporal Workflow)

```typescript
const requestDeepResearch = async (query: string, sectionId: string) => {
  // Get complete citation chain for LLM context
  const chain = await fetch(`/sections/${sectionId}/complete-chain`).then(r => r.json());

  // Send to BFF to start Temporal workflow
  const workflow = await fetch('/api/research', {
    method: 'POST',
    body: JSON.stringify({
      query,
      initial_sections: chain.chain_sections,
      full_text_context: chain.complete_chain.map(s => s.full_text).join('\n\n')
    })
  });

  return workflow.json(); // { workflow_id: "...", status: "started" }
};
```

---

## Error Responses

All endpoints may return:

```typescript
{
  error: string;           // "Section not found" | "Database error" | etc.
  code: string;            // "NOT_FOUND" | "INTERNAL_ERROR"
  section?: string;        // The section_id that was requested (if applicable)
}
```

**Example:**
```json
{
  "error": "Section 9999.99 not found in primary database",
  "code": "NOT_FOUND",
  "section": "9999.99"
}
```

---

## Corpus-Specific Differences

### Ohio Revised Code (Statutes)
- `section_number` format: `"2903.13"` (chapter.section)
- Has `title` and `chapter` fields
- May have `offense_level` and `offense_degree` in enrichment

### Ohio Case Law (Court Decisions)
- `section_number` format: `"2023-Ohio-1234"` (year-state-number)
- Has `court_level`, `binding_on`, `precedent_value`
- May have `treatment_status` showing if overruled

### Ohio Administrative Code (Rules)
- `section_number` format: `"3701-17-01"` (agency-chapter-rule)
- Has agency-specific metadata

### Ohio Constitution (Constitutional Law)
- `section_number` format: `"Article I, Section 1"`
- Highest authority (all statutes must comply)

---

## TypeScript Types

For type safety in your frontend:

```typescript
// Copy from ohio-legal-ai.io/packages/models after code generation
import type {
  OhioSection,
  CitationData,
  ReverseCitationData,
  CitationChain,
  CorpusInfo
} from '@/types/lmdb';
```

Or generate from the Pydantic models using the schema generator output.

---

## Performance Notes

### Response Sizes

| Endpoint | Typical Size | Use Case |
|----------|-------------|----------|
| `/sections/{id}` | 2-10 KB | Display statute |
| `/sections/{id}/citations` | 1-5 KB | Show related sections |
| `/sections/{id}/reverse-citations` | 1-20 KB | Authority analysis |
| `/sections/{id}/complete-chain` | **50-500 KB** | Deep research, LLM context |
| `/corpus/metadata` | 1 KB | Stats, health check |

**⚠️ Warning:** `complete-chain` can be **very large** (15+ statutes with full text). Only request when needed for deep analysis.

### Caching Recommendations

```typescript
// Cache statute content (changes rarely)
const cacheKey = `statute:${sectionId}`;
const cached = await cache.get(cacheKey);
if (cached) return cached;

const statute = await fetch(`/sections/${sectionId}`).then(r => r.json());
await cache.set(cacheKey, statute, { ttl: 86400 }); // 24 hours
```

---

## Questions?

**⚡ RELAY to ohio-legal-ai.io Claude:**
Use these structures when:
- Building Knowledge Service API endpoints
- Defining TypeScript types for frontend
- Validating Pydantic models
- Writing Temporal activities that call Knowledge Service

**This document is the contract between data pipeline and application.**