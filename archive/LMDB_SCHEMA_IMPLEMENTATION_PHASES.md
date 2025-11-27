# LMDB Schema Implementation Phases

**Date:** 2025-11-20
**Status:** Roadmap for Full Schema Population

---

## Vision

A comprehensive legal research platform with:
- **Graph navigation** - Bidirectional citation traversal
- **Visual network** - Corpus-colored nodes, depth-based opacity
- **Semantic enrichment** - AI-generated summaries and analysis
- **LLM research workflows** - Deep contextual analysis

---

## Schema Status by Field

### PRIMARY.LMDB Schema

#### ✅ Phase 1: Core Storage (CURRENTLY POPULATED)

```python
{
  # Basic identifiers
  "section_number": str,        # ✅ Populated
  "url": str,                   # ✅ Populated
  "url_hash": str,              # ✅ Populated

  # Display fields
  "header": str,                # ✅ Populated (full header with title)
  "section_title": str,         # ✅ Populated (extracted from header)

  # Legal text
  "paragraphs": list[str],      # ✅ Populated (preserved original)
  "full_text": str,             # ✅ Populated (joined paragraphs)
  "word_count": int,            # ✅ Populated
  "paragraph_count": int,       # ✅ Populated

  # Citation metadata (for graph)
  "has_citations": bool,        # ✅ Populated (forward citations exist)
  "citation_count": int,        # ✅ Populated (number of forward refs)
  "in_complex_chain": bool,     # ✅ Populated (in chains.lmdb)
  "is_clickable": bool,         # ✅ Populated (has forward OR reverse citations)

  # Timestamp
  "scraped_date": str,          # ✅ Populated (ISO8601)
}
```

**Status:** COMPLETE ✅
**Location:** All 4 corpora (`build_comprehensive_lmdb.py`)

---

#### 🔨 Phase 2: Extractable Metadata (NEXT PRIORITY)

```python
{
  # Organizational hierarchy (extractable from existing data)
  "chapter": str | None,        # 📋 TODO: Extract from section_number or header
  "title": str | None,          # 📋 TODO: Extract from header structure

  # Temporal validity (basic implementation)
  "valid_from": str | None,     # 📋 TODO: Extract from scraped_date or metadata
  "valid_until": str | None,    # 📋 TODO: Set to null (assume current = valid)
  "treatment_status": str | None, # 📋 TODO: Default to "valid" for statutes

  # Case law specific (corpus-dependent)
  "court_level": str | None,    # 📋 TODO: Extract from case metadata (ohio_caselaw only)
  "binding_on": list[str] | None, # 📋 TODO: Compute from court hierarchy
  "precedent_value": str | None, # 📋 TODO: Derive from court_level
}
```

**Implementation Notes:**

1. **Chapter/Title Extraction:**
   - Ohio Revised Code: Section "2913.02" → Chapter "29" (Criminal Code)
   - Admin Code: Rule "3701-17-01" → Chapter "3701-17"
   - Constitution: "Article I, Section 1" → Article "I"
   - Case Law: Extract from case metadata

2. **Treatment Status Logic:**
   ```python
   # Statutes: default to "valid" (assume current law is valid)
   treatment_status = "valid"

   # Case law: could be "valid", "overruled", "questioned", "superseded"
   # Start with "valid", update when relationship tracking is built
   ```

3. **Court Hierarchy (Case Law Only):**
   ```python
   court_levels = {
       "supreme_court": {
           "binding_on": ["all_ohio_courts"],
           "precedent_value": "binding"
       },
       "appellate": {
           "binding_on": ["trial_courts_in_district"],
           "precedent_value": "persuasive"  # for other districts
       },
       "trial": {
           "binding_on": [],
           "precedent_value": "persuasive"
       }
   }
   ```

**Effort:** MEDIUM (extraction logic + corpus-specific handling)
**Benefit:** Organizational context, basic temporal tracking

---

#### 🧮 Phase 3: Graph Metrics (COMPUTE FROM NETWORK)

```python
{
  # Network analysis (computed from citation graph)
  "authority_score": float | None,      # 🔮 TODO: PageRank or HITS authority
  "betweenness_centrality": float | None, # 🔮 TODO: NetworkX centrality
  "citation_velocity": float | None,    # 🔮 TODO: Citations per year (recent)
}
```

**Implementation Approach:**

1. **Build Citation Graph:**
   ```python
   import networkx as nx

   # Create directed graph from citations.lmdb and reverse_citations.lmdb
   G = nx.DiGraph()

   # Add all sections as nodes
   for section in primary_db:
       G.add_node(section_id)

   # Add edges from citation relationships
   for section, citations in citations_db:
       for cited in citations:
           G.add_edge(section, cited)
   ```

2. **Compute Authority (PageRank):**
   ```python
   # Higher score = more cited by important sections
   authority_scores = nx.pagerank(G, alpha=0.85)
   ```

3. **Compute Centrality:**
   ```python
   # Higher score = more important for connecting parts of the graph
   centrality = nx.betweenness_centrality(G)
   ```

4. **Citation Velocity:**
   ```python
   # Count citations per year (requires case dates)
   def compute_velocity(section_id, lookback_years=5):
       citing_cases = get_citing_cases_with_dates(section_id)
       recent = [c for c in citing_cases if c.year >= current_year - lookback_years]
       return len(recent) / lookback_years
   ```

**Effort:** HIGH (requires networkx, graph computation pipeline)
**Benefit:** Authority ranking, importance scoring for search results

---

#### 🤖 Phase 4: AI Enrichment (LLM-GENERATED)

```python
{
  "enrichment": {
    # Semantic understanding (AI-generated)
    "summary": str | None,              # 🤖 TODO: LLM 2-sentence plain language summary
    "legal_type": str | None,           # 🤖 TODO: "criminal_statute", "civil_statute", etc.
    "practice_areas": list[str] | None, # 🤖 TODO: ["criminal_law", "property_law", ...]
    "complexity": int | None,           # 🤖 TODO: 1-10 scale
    "key_terms": list[str] | None,      # 🤖 TODO: Extracted important terms

    # Criminal law specific
    "offense_level": str | None,        # 🤖 TODO: "felony", "misdemeanor" (if applicable)
    "offense_degree": str | None        # 🤖 TODO: "F1"-"F5", "M1"-"M4" (if applicable)
  }
}
```

**Implementation Approach:**

1. **Batch Enrichment Pipeline:**
   ```python
   # Use auto_enricher.py (already exists in ohio_caselaw/lmdb/)
   from auto_enricher import LMDBEnricher

   enricher = LMDBEnricher(
       lmdb_path="path/to/corpus.lmdb",
       model="claude-3-5-sonnet-20241022"
   )

   enricher.enrich_all_sections(batch_size=100)
   ```

2. **Prompts for Enrichment:**
   ```
   Analyze this legal text and provide:
   1. A 1-2 sentence plain language summary
   2. Legal type (criminal_statute, civil_statute, definitional, procedural)
   3. Practice areas (list of relevant legal practice areas)
   4. Complexity (1-10 scale, where 1=simple, 10=extremely complex)
   5. Key legal terms (important terms a lawyer would search for)
   6. If criminal statute: offense level and degree
   ```

3. **Storage Strategy:**
   ```python
   # Store as nested JSON in enrichment field
   section_data["enrichment"] = {
       "summary": "Defines the crime of theft...",
       "legal_type": "criminal_statute",
       "practice_areas": ["criminal_law"],
       "complexity": 4,
       "key_terms": ["theft", "property", "deprive"],
       "offense_level": "felony",
       "offense_degree": "F5"
   }
   ```

**Effort:** MEDIUM-HIGH (LLM API costs, batch processing time)
**Benefit:** Semantic search, plain language summaries, practice area filtering

---

#### 🔗 Phase 5: Relationship Tracking (ADVANCED)

```python
{
  # Legal relationship tracking
  "invalidated_by": str | None,   # 🔮 TODO: Reference to invalidating case/law
  "superseded_by": str | None,    # 🔮 TODO: Reference to superseding law
}
```

**Implementation Notes:**

- **Requires:** Treatment status analysis (Phase 2) + citation context analysis
- **Detection:** Look for phrases like "overruled", "superseded by", "no longer valid"
- **Validation:** May require manual review for critical relationships

**Effort:** HIGH (relationship detection, validation)
**Benefit:** Temporal validity, avoid citing invalid law

---

## CITATIONS.LMDB Schema

### ✅ Currently Populated

```python
{
  "section": str,                     # ✅ Source section ID
  "direct_references": list[str],     # ✅ Referenced section IDs
  "reference_count": int,             # ✅ Count
  "references_details": [             # ✅ Enhanced details
    {
      "section": str,                 # ✅ Target section
      "title": str,                   # ✅ Target title
      "url": str,                     # ✅ Target URL
      "url_hash": str,                # ✅ URL hash
      "relationship": str,            # ✅ Type: "cross_reference", "defines", "cites"
      "context": str,                 # ✅ Surrounding text (100 chars)
      "position": int                 # ✅ Position in source (0-indexed)
    }
  ]
}
```

**Status:** COMPLETE ✅ (all fields populated by builders)

---

## REVERSE_CITATIONS.LMDB Schema

### ✅ Currently Populated

```python
{
  "section": str,                     # ✅ Target section ID
  "cited_by": list[str],              # ✅ Citing section IDs (sorted)
  "cited_by_count": int,              # ✅ Count
  "citing_details": [                 # ✅ Details
    {
      "section": str,                 # ✅ Citing section
      "title": str,                   # ✅ Citing section title
      "url": str                      # ✅ Citing section URL
    }
  ]
}
```

**Status:** COMPLETE ✅ (supports backward traversal)

---

## CHAINS.LMDB Schema

### ✅ Currently Populated

```python
{
  "chain_id": str,                    # ✅ Primary section ID
  "primary_section": str,             # ✅ Starting point
  "chain_sections": list[str],        # ✅ All sections in chain (ordered)
  "chain_depth": int,                 # ✅ Number of sections
  "references_count": int,            # ✅ Total references
  "created_at": str,                  # ✅ ISO8601 timestamp
  "complete_chain": [                 # ✅ Full text of all sections
    {
      "section": str,                 # ✅ Section ID
      "title": str,                   # ✅ Title
      "url": str,                     # ✅ URL
      "url_hash": str,                # ✅ Hash
      "full_text": str,               # ✅ Complete legal text
      "word_count": int               # ✅ Word count
    }
  ]
}
```

**Status:** COMPLETE ✅ (supports complex chain traversal)

---

## METADATA.LMDB Schema

### ✅ Currently Populated

```python
{
  # Key: b'corpus_info'
  "total_sections": int,              # ✅ Total items
  "sections_with_citations": int,     # ✅ Items citing others
  "complex_chains": int,              # ✅ Chain count
  "reverse_citations": int,           # ✅ Items cited by others
  "build_date": str,                  # ✅ ISO8601 timestamp
  "source": str,                      # ✅ Source URL
  "version": str,                     # ✅ Builder version
  "builder": str,                     # ✅ Builder script name
  "databases": dict                   # ✅ Database descriptions
}

{
  # Key: b'inbound_count_{section_id}'
  "section": str,                     # ✅ Section ID
  "count": int                        # ✅ Times cited
}
```

**Status:** COMPLETE ✅

---

## Implementation Priority

### Immediate (This Week):
1. ✅ Core storage fields (DONE)
2. 📋 Extract `chapter` and `title` from existing data (Phase 2)
3. 📋 Add basic `treatment_status` = "valid" (Phase 2)

### Short Term (Next 2 Weeks):
4. 📋 Court hierarchy for case law (Phase 2)
5. 🤖 Start enrichment pipeline (Phase 4) - run on small batch first

### Medium Term (Next Month):
6. 🧮 Graph metrics computation (Phase 3)
7. 🤖 Full corpus enrichment (Phase 4)

### Long Term (Future):
8. 🔗 Relationship tracking (Phase 5)
9. 🔗 Temporal validity windows (Phase 5)

---

## UI Graph Visualization Requirements

Based on your vision, the LMDB data supports:

### ✅ Already Supported:
- **Bidirectional traversal:** citations.lmdb (forward) + reverse_citations.lmdb (backward)
- **Clickability detection:** `is_clickable` field in primary.lmdb
- **Citation chains:** chains.lmdb for complex relationships
- **Relationship context:** `relationship` and `context` fields in citation details

### 📋 Needs Phase 2:
- **Corpus color-coding:** Use `chapter` or corpus identifier for color mapping
- **Court level indication:** `court_level` for different node styling

### 🧮 Needs Phase 3:
- **Node importance sizing:** Use `authority_score` for node size
- **Depth-based opacity:** Compute from graph traversal distance + use `betweenness_centrality`

### Graph Traversal Algorithm (Pseudocode):

```python
def build_interactive_graph(clicked_section_id, depth=3):
    """
    Build graph data for UI visualization

    Returns:
    {
      "nodes": [
        {
          "id": "2913.02",
          "title": "Theft",
          "corpus": "ohio_revised",
          "color": "#FF5733",  # Based on corpus
          "opacity": 1.0,       # Distance 0 from clicked node
          "size": 50,           # Based on authority_score
          "court_level": null   # For case law only
        },
        {
          "id": "2913.01",
          "title": "Definitions",
          "corpus": "ohio_revised",
          "color": "#FF5733",
          "opacity": 0.7,       # Distance 1 from clicked node
          "size": 30,
          "court_level": null
        }
      ],
      "edges": [
        {
          "source": "2913.02",
          "target": "2913.01",
          "relationship": "defines",
          "context": "As used in sections 2913.01...",
          "weight": 1.0
        }
      ]
    }
    """

    # 1. Get clicked section data
    section = primary_db.get(clicked_section_id)

    # 2. Get forward citations (what this cites)
    forward_citations = citations_db.get(clicked_section_id)

    # 3. Get reverse citations (what cites this)
    reverse_citations = reverse_citations_db.get(clicked_section_id)

    # 4. Build graph with BFS up to depth limit
    graph = {
        "nodes": [],
        "edges": []
    }

    visited = set()
    queue = [(clicked_section_id, 0)]  # (section_id, distance)

    while queue:
        current_id, distance = queue.pop(0)

        if current_id in visited or distance > depth:
            continue

        visited.add(current_id)

        # Get section data
        section_data = primary_db.get(current_id)

        # Calculate opacity based on distance
        opacity = 1.0 - (distance * 0.2)  # Decrease by 0.2 per level

        # Add node
        graph["nodes"].append({
            "id": current_id,
            "title": section_data["section_title"],
            "corpus": extract_corpus(current_id),
            "color": get_corpus_color(extract_corpus(current_id)),
            "opacity": max(0.2, opacity),
            "size": section_data.get("authority_score", 0.5) * 100,
            "court_level": section_data.get("court_level")
        })

        # Add forward edges
        citations = citations_db.get(current_id)
        if citations:
            for ref in citations["references_details"]:
                graph["edges"].append({
                    "source": current_id,
                    "target": ref["section"],
                    "relationship": ref["relationship"],
                    "context": ref["context"],
                    "weight": 1.0
                })

                # Add to queue for BFS
                if distance < depth:
                    queue.append((ref["section"], distance + 1))

        # Add backward edges
        reverse = reverse_citations_db.get(current_id)
        if reverse:
            for citing in reverse["citing_details"]:
                graph["edges"].append({
                    "source": citing["section"],
                    "target": current_id,
                    "relationship": "cites",
                    "context": "",
                    "weight": 1.0
                })

                if distance < depth:
                    queue.append((citing["section"], distance + 1))

    return graph

# Corpus color mapping
CORPUS_COLORS = {
    "ohio_revised": "#FF5733",      # Red-orange
    "ohio_administration": "#33C3FF", # Light blue
    "ohio_constitution": "#FFD700",  # Gold
    "ohio_caselaw": "#9B59B6"        # Purple
}
```

---

## LLM Research Workflow

Your LMDB structure supports deep analysis workflows:

### Workflow Example: "What are the penalties for theft in Ohio?"

```python
async def perform_legal_research(user_query: str):
    """
    Multi-step research workflow using LMDB data + LLM
    """

    # Step 1: Vector search for relevant sections
    relevant_sections = await vector_search(user_query, top_k=5)
    # Returns: ["2913.02", "2913.03", "2913.51", ...]

    # Step 2: Fetch full section data from LMDB
    sections_data = []
    for section_id in relevant_sections:
        section = primary_db.get(section_id)
        sections_data.append({
            "id": section_id,
            "title": section["section_title"],
            "text": section["full_text"],
            "enrichment": section.get("enrichment", {}),
            "authority_score": section.get("authority_score", 0),
            "citation_count": section["citation_count"]
        })

    # Step 3: Get citation context (related sections)
    citation_context = []
    for section_id in relevant_sections:
        # Get what this section references
        citations = citations_db.get(section_id)
        if citations:
            for ref in citations["references_details"][:3]:  # Top 3
                ref_section = primary_db.get(ref["section"])
                citation_context.append({
                    "id": ref["section"],
                    "title": ref_section["section_title"],
                    "relationship": ref["relationship"],
                    "context": ref["context"]
                })

        # Get case law citing this statute
        reverse = reverse_citations_db.get(section_id)
        if reverse:
            for citing in reverse["citing_details"][:3]:
                citing_section = primary_db.get(citing["section"])
                citation_context.append({
                    "id": citing["section"],
                    "title": citing_section["section_title"],
                    "type": "case_law_application"
                })

    # Step 4: Build comprehensive context for LLM
    llm_context = f"""
    User Query: {user_query}

    Relevant Statutes:
    {format_sections(sections_data)}

    Related Provisions:
    {format_citations(citation_context)}

    Enrichment Data:
    {format_enrichment(sections_data)}
    """

    # Step 5: LLM Analysis
    analysis = await llm.analyze(
        prompt="""You are an expert Ohio legal researcher. Based on the provided
        statutes, case law, and citation relationships, provide a comprehensive
        answer to the user's question. Include:

        1. Direct answer with specific statute references
        2. Explanation of relevant provisions
        3. How courts have applied these statutes (case law)
        4. Practical implications
        5. Related areas of law the user should be aware of
        """,
        context=llm_context
    )

    # Step 6: Return rich response with citations
    return {
        "answer": analysis,
        "primary_sources": sections_data,
        "related_sections": citation_context,
        "graph_data": build_interactive_graph(relevant_sections[0]),
        "confidence_score": calculate_confidence(sections_data)
    }
```

### Key Features Enabled by Current Schema:

✅ **Full text retrieval:** `full_text` field
✅ **Citation network:** citations.lmdb + reverse_citations.lmdb
✅ **Relationship context:** `relationship` and `context` fields
✅ **Authority ranking:** `citation_count` (Phase 3: `authority_score`)
✅ **Semantic understanding:** `enrichment` field (Phase 4)
✅ **Practice area filtering:** `enrichment.practice_areas` (Phase 4)
✅ **Chain analysis:** chains.lmdb for deep dependencies

---

## Summary

**Your schemas are CORRECT** - they represent the full vision.

**Current Status:**
- ✅ Core graph traversal: READY
- ✅ Citation relationships: COMPLETE
- ✅ Full text storage: COMPLETE
- 📋 Metadata extraction: NEXT PRIORITY
- 🤖 AI enrichment: MEDIUM TERM
- 🧮 Graph metrics: MEDIUM TERM

**Next Steps:**
1. Extract `chapter` and `title` from existing data (easy win)
2. Add basic `treatment_status` (default to "valid")
3. Start enrichment pipeline on small batch
4. Build graph visualization prototype using current data
5. Compute graph metrics once all corpora are loaded

The foundation is solid. You have everything needed for the graph visualization and LLM workflows - just need to populate the remaining fields incrementally.