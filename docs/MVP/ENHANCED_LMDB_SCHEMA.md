# Enhanced LMDB Schema - With Enrichment Metadata

## Design Principles

1. **NEVER alter scraped legal text** - `paragraphs` field is sacred
2. **Add metadata fields** for AI agent intelligence
3. **Keep schema consistent** across all 4 corpuses
4. **Make fields optional** - can be null/empty initially, enriched later
5. **Optimize for agent queries** - "What statutes relate to X?", "Is this criminal/civil?"

---

## Enhanced Schema Design

### 1. sections.lmdb (Enhanced)

```json
{
  // ========== ORIGINAL FIELDS (PRESERVED) ==========
  "section_number": "2913.02",
  "url": "https://codes.ohio.gov/ohio-revised-code/section-2913.02",
  "url_hash": "abc123def456",
  "header": "Section 2913.02|Theft.",
  "section_title": "Theft.",
  "paragraphs": [
    "EXACT LEGAL TEXT - NEVER MODIFIED",
    "Paragraph 2...",
    "Paragraph 3..."
  ],

  // ========== NEW ENRICHMENT FIELDS ==========
  "enrichment": {
    // Plain Language
    "plain_summary": "Defines theft as knowingly depriving someone of property...",
    "key_terms": ["theft", "deprive", "property", "permanent", "consent"],

    // Classification
    "practice_areas": ["criminal_law", "property_crimes"],
    "legal_type": "criminal_statute",  // criminal_statute, civil_statute, procedural, definitional
    "offense_level": "felony",  // felony, misdemeanor, violation, civil, n/a
    "offense_degree": "varies",  // e.g., "F1", "F5", "M1", etc.

    // Complexity
    "complexity_score": 7,  // 1-10 (1=simple definition, 10=complex multi-part)
    "citation_density": "high",  // low, medium, high (based on # of citations)

    // Legal Strategy (for attorneys)
    "defendant_relevance": "critical",  // critical, high, medium, low, none
    "prosecution_relevance": "critical",
    "defense_angles": [
      "lack_of_intent",
      "consent_present",
      "ownership_dispute",
      "value_threshold"
    ],
    "common_defenses": [
      "No intent to permanently deprive",
      "Believed had consent",
      "Good faith claim of right"
    ],

    // Related Concepts
    "related_topics": ["robbery", "fraud", "receiving_stolen_property"],
    "parent_chapter": "Chapter 2913 - Theft and Fraud Offenses",

    // Constitutional Issues
    "constitutional_concerns": ["due_process", "vagueness"],
    "common_challenges": ["intent_element", "property_valuation"],

    // AI Metadata
    "embeddings_generated": false,  // For vector search later
    "last_enriched": null,
    "enrichment_version": "1.0"
  },

  // ========== COMPUTED FIELDS (auto-generated) ==========
  "word_count": 523,
  "paragraph_count": 15,
  "has_citations": true,
  "citation_count": 12,
  "effective_date": "2023-01-01",  // If we can extract from text
  "last_amended": "2022-12-15"  // If available
}
```

---

### 2. citations.lmdb (Enhanced)

```json
{
  "section": "2913.02",
  "direct_references": ["2913.01", "2913.71", "2929.11"],
  "reference_count": 3,

  "references_details": [
    {
      "section": "2913.01",
      "title": "Theft and fraud offenses definitions",
      "url": "https://codes.ohio.gov/ohio-revised-code/section-2913.01",
      "url_hash": "...",

      // NEW: Relationship context
      "relationship_type": "definitional",  // definitional, procedural, penalty, cross_reference
      "context_snippet": "...as defined in section 2913.01...",
      "importance": "critical"  // critical, high, medium, low
    }
  ],

  // NEW: Citation analysis
  "citation_types": {
    "definitional": 1,
    "penalty": 1,
    "procedural": 1
  },
  "citation_complexity": "moderate"
}
```

---

### 3. reverse_citations.lmdb (Enhanced)

```json
{
  "section": "2913.01",
  "cited_by": ["2913.02", "2913.03", "2913.04"],
  "cited_by_count": 3,

  "citing_details": [
    {
      "section": "2913.02",
      "title": "Theft",
      "url": "...",

      // NEW: Reverse relationship context
      "how_used": "Relies on definitions from this section",
      "citation_frequency": "multiple"  // single, multiple
    }
  ],

  // NEW: Impact analysis
  "is_foundational": true,  // Is this section heavily relied upon?
  "impact_score": 8  // 1-10 based on how many sections depend on it
}
```

---

### 4. chains.lmdb (Enhanced)

```json
{
  "chain_id": "2913.02",
  "primary_section": "2913.02",
  "chain_sections": ["2913.02", "2913.01", "2913.71", "2929.11"],
  "chain_depth": 4,

  // NEW: Chain analysis
  "chain_type": "criminal_offense_definition",  // Type of legal reasoning
  "reasoning_flow": "offense → definitions → penalties → sentencing",
  "complexity_rating": "moderate",

  "complete_chain": [
    {
      "section": "2913.02",
      "title": "Theft",
      "url": "...",
      "full_text": "...",
      "word_count": 523,

      // NEW: Position in chain
      "chain_position": 1,
      "role_in_chain": "primary_offense"  // primary_offense, definition, penalty, procedure
    }
  ],

  // NEW: Chain insights
  "attorney_notes": "Follow this chain to build complete theft analysis",
  "practice_tip": "Review all sections in chain for complete defense strategy"
}
```

---

### 5. metadata.lmdb (Enhanced)

**Corpus-level metadata:**
```json
{
  "total_sections": 23644,
  "sections_with_citations": 23644,
  "complex_chains": 8619,

  // NEW: Enrichment tracking
  "enrichment_status": {
    "total_enriched": 0,
    "total_unenriched": 23644,
    "enrichment_progress": 0.0,
    "last_enrichment_run": null
  },

  // NEW: Content analysis
  "content_breakdown": {
    "criminal_statutes": 3200,
    "civil_statutes": 15000,
    "procedural": 2500,
    "definitional": 2944
  },

  // NEW: Practice area distribution
  "practice_areas": {
    "criminal_law": 3500,
    "family_law": 800,
    "business_law": 2000,
    "property_law": 1500
  }
}
```

**Section-level metadata (unchanged):**
```json
{
  "section": "2913.02",
  "url_hash": "...",
  "scraped_date": "2025-11-05",
  "word_count": 523,
  "has_citations": true,
  "citation_count": 12,
  "in_complex_chain": true,

  // NEW: Enrichment status
  "enriched": false,
  "enrichment_date": null,
  "needs_review": false
}
```

---

## Enrichment Field Descriptions

### Classification Fields

| Field | Purpose | Values | Example |
|-------|---------|--------|---------|
| `legal_type` | Type of statute | criminal_statute, civil_statute, procedural, definitional | "criminal_statute" |
| `practice_areas` | Legal domains | Array of strings | ["criminal_law", "property_crimes"] |
| `offense_level` | Criminal severity | felony, misdemeanor, violation, civil, n/a | "felony" |
| `complexity_score` | Reading difficulty | 1-10 | 7 |

### Strategy Fields (for attorneys)

| Field | Purpose | Values |
|-------|---------|--------|
| `defendant_relevance` | How important for defense | critical, high, medium, low, none |
| `defense_angles` | Common defense strategies | Array of strings |
| `common_defenses` | Typical defenses used | Array of strings |
| `constitutional_concerns` | Potential challenges | Array of strings |

### Relationship Fields

| Field | Purpose | Values |
|-------|---------|--------|
| `relationship_type` | How sections relate | definitional, procedural, penalty, cross_reference |
| `importance` | Strength of relationship | critical, high, medium, low |
| `is_foundational` | Is this heavily cited? | true/false |

---

## Implementation Strategy

### Phase 1: Schema Update (Week 1)
1. Update `build_comprehensive_lmdb.py` to include new fields
2. Set all enrichment fields to `null` or empty initially
3. Rebuild Ohio Revised LMDB with new schema

### Phase 2: Auto-Enrichment (Week 2)
1. Create `auto_enricher.py` - analyzes text to fill basic fields:
   - Extract `offense_level` from text (felony/misdemeanor)
   - Calculate `complexity_score` from word count + citation density
   - Classify `legal_type` from section patterns
   - Identify `practice_areas` from chapter organization

### Phase 3: AI Enrichment (Week 3 - Optional)
1. Use LLM to generate:
   - `plain_summary`
   - `key_terms`
   - `defense_angles`
   - `common_defenses`

### Phase 4: Clone to Other Corpuses (Week 4)
1. Apply same schema to Ohio Admin Code
2. Apply to Ohio Constitution
3. Apply to Ohio Case Law

---

## Query Examples with Enhanced Schema

### Query 1: "Find all criminal statutes related to property"
```python
for section in sections_db:
    if ("criminal_law" in section['enrichment']['practice_areas'] and
        "property" in section['enrichment']['related_topics']):
        return section
```

### Query 2: "What are common defenses for theft?"
```python
section = sections_db.get("2913.02")
defenses = section['enrichment']['common_defenses']
# Returns: ["No intent to permanently deprive", "Believed had consent", ...]
```

### Query 3: "Find foundational sections in criminal law"
```python
for section in reverse_citations_db:
    if (section['is_foundational'] and
        section['impact_score'] > 7):
        return section
```

---

## Benefits of Enhanced Schema

1. **AI agents can filter by practice area** - "Show me family law statutes"
2. **Attorneys get defense strategies** - Built-in legal strategy metadata
3. **Complexity filtering** - "Show me simple statutes to start"
4. **Relationship understanding** - Know WHY sections cite each other
5. **Foundational section identification** - Find key definitions
6. **Future-proof** - Schema supports vector embeddings later

---

## What Stays The Same

- `paragraphs` field is NEVER touched (exact legal text preserved)
- Existing citation graph structure unchanged
- All current query patterns still work
- Backwards compatible (new fields can be null)

---

**Next Step:** Update `build_comprehensive_lmdb.py` to implement this enhanced schema.