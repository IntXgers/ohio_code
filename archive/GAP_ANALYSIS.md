# Gap Analysis Checklist - Ohio Legal AI Platform

## What You Have ✅ (Complete)

### 1. Execution Architecture ✅
- [x] Temporal worker that orchestrates workflows
- [x] BFF that classifies queries and routes to workflows
- [x] Activities that call services
- [x] LLM integration (vLLM setup ready)

### 2. Ohio Revised Code Data ✅
- [x] Complete ORC corpus in LMDB (23,644 sections)
- [x] Forward citations (what each statute cites)
- [x] Reverse citations (what cites each statute)
- [x] Pre-computed citation chains
- [x] Basic metadata (practice areas, complexity)

### 3. Models Defined ✅
- [x] Pydantic models for statutes, citations, cases
- [x] Temporal workflow Input/Result models
- [x] Graph visualization models
- [x] Generator 10 copies models to tworker automatically

### 4. Recent Session Completions ✅
- [x] Updated deprecated `on_event` handler in knowledge service → modern `lifespan`
- [x] Refactored tworker (removed old logic, clean structure)
- [x] Created generator 10 for automatic model copying
- [x] Fixed CitationChainWorkflow type hints
- [x] Created `build_citation_graph_activity`
- [x] All workflows and activities properly registered

---

## What You Need to Build 🔨

## PHASE 1: Enrich Your LMDB (Without Adding New Data)
**Time Estimate: 2-3 weeks**
**Priority: MVP - START HERE**

### 1.1 Authority Scoring Algorithm
- [ ] Run PageRank on existing citation graph
- [ ] Compute authority scores for every statute (0.0-1.0)
- [ ] Store in `metadata.lmdb`: `{"2913.02": 0.85, ...}`
- [ ] Add `authority_score` field to each section in `sections.lmdb`

### 1.2 Treatment Detection
- [ ] Analyze citation contexts to detect negative treatment
- [ ] Mark statutes as: `valid`, `superseded`, `amended`, `repealed`
- [ ] Add `treatment_status` field to `sections.lmdb`
- [ ] Create `treatment_index` in `metadata.lmdb`

### 1.3 Temporal Data Extraction
- [ ] Parse effective dates from statute text
- [ ] Extract "Amended by" references from text
- [ ] Add `effective_date`, `superseded_by`, `superseded_date` fields
- [ ] Track validity windows (valid_from, valid_until)

### 1.4 Citation Strength Scoring
- [ ] Analyze how often each citation is referenced
- [ ] Weight citations by context (definitional > procedural)
- [ ] Add strength scores to edges in `citations.lmdb`

---

## PHASE 2: Add Case Law Corpus
**Time Estimate: 4-6 weeks**
**Priority: Post-MVP**

### 2.1 Scrape Ohio Case Law
- [ ] Ohio Supreme Court opinions (CourtListener API or web scraping)
- [ ] Ohio Courts of Appeals (12 districts)
- [ ] Target: 15,000-25,000 opinions
- [ ] Focus on last 20 years initially

### 2.2 Process Case Law Into LMDB
- [ ] Extract citations from opinions
- [ ] Build case-to-case citation graph
- [ ] Build case-to-statute links
- [ ] Store in new `cases.lmdb` database

### 2.3 Compute Case Authority Metrics
- [ ] Run PageRank on case citation network
- [ ] Weight by court level (Supreme > Appeals > Common Pleas)
- [ ] Apply recency decay (newer cases weighted higher)
- [ ] Store authority scores in `metadata.lmdb`

---

## PHASE 3: Treatment Engine
**Time Estimate: 2-3 weeks**
**Priority: Post-MVP, After Phase 2**

### 3.1 Citation Context Analysis
- [ ] Parse how cases cite each other
- [ ] Detect phrases: "overruled by", "questioned in", "distinguished in"
- [ ] Expand existing `RELATIONSHIP_PATTERNS` in citation_mapper.py

### 3.2 Treatment Propagation
- [ ] If Case A overrules Case B, and Case C relies on B, flag C as weakened
- [ ] Build transitive invalidation logic
- [ ] Build treatment chains

### 3.3 Shepardization System
- [ ] API endpoint: `POST /case/{citation}/treatment`
- [ ] Returns: positive history, negative history, current status
- [ ] Shows full treatment chain

---

## PHASE 4: Semantic Layer (Optional But Powerful)
**Time Estimate: 3-4 weeks**
**Priority: Optional Enhancement**

### 4.1 Fact Pattern Embeddings
- [ ] Extract facts from case opinions (LLM-based extraction)
- [ ] Generate embeddings for fact patterns
- [ ] Store in vector DB (Qdrant, Pinecone, or Weaviate)

### 4.2 Holdings Extraction
- [ ] Use LLM to extract "ratio decidendi" (binding rule)
- [ ] Separate from "obiter dicta" (non-binding commentary)
- [ ] Embed holdings for semantic search

### 4.3 Similarity Search
- [ ] Query: "Find cases with similar facts to X"
- [ ] Vector DB returns top-k similar fact patterns
- [ ] Enrich with citation analysis

---

## PHASE 5: Judge Analytics (Optional)
**Time Estimate: 2-3 weeks**
**Priority: Optional Enhancement**

### 5.1 Data Aggregation
- [ ] Group cases by judge
- [ ] Calculate: total opinions, citation count, reversal rate
- [ ] Track plaintiff vs defendant favorability

### 5.2 Pattern Analysis
- [ ] Identify doctrinal preferences (textualist vs purposivist)
- [ ] Extract decision patterns on specific issues
- [ ] Statistical significance testing

### 5.3 API Integration
- [ ] `GET /judge/{name}/profile` endpoint
- [ ] Returns voting patterns, reversal rates, notable cases

---

## PHASE 6: Knowledge Service Enhancements
**Time Estimate: 2-3 weeks**
**Priority: MVP - After Phase 1**

### 6.1 Authority Queries
- [ ] `GET /authority/strongest/{practice_area}` - most authoritative cases
- [ ] `GET /authority/binding/{jurisdiction}/{statute}` - binding precedent only
- [ ] `GET /authority/score/{citation}` - get pre-computed authority score

### 6.2 Treatment Queries
- [ ] `GET /treatment/status/{citation}` - is this still good law?
- [ ] `GET /treatment/history/{citation}` - full treatment timeline
- [ ] `GET /treatment/affected-by/{citation}` - what depends on this?

### 6.3 Temporal Queries
- [ ] `GET /temporal/valid-at/{citation}/{date}` - was this valid on date X?
- [ ] `GET /temporal/changes/{citation}` - show amendment history
- [ ] `GET /temporal/range/{start}/{end}` - law valid during period

### 6.4 Graph Algorithms
- [ ] `GET /graph/path/{from}/{to}` - shortest citation path
- [ ] `GET /graph/cluster/{citation}` - find citation clusters
- [ ] `GET /graph/subgraph/{citation}/{depth}` - extract subgraph

---

## PHASE 7: Activity Library
**Time Estimate: 1-2 weeks**
**Priority: MVP - After Phase 1 & 6**

### 7.1 Authority Activities
- [ ] `get_most_authoritative_cases(practice_area, limit)`
- [ ] `filter_by_authority_threshold(cases, min_score)`
- [ ] `rank_by_binding_weight(cases, jurisdiction)`

### 7.2 Treatment Activities
- [ ] `check_validity_status(citation)`
- [ ] `get_treatment_chain(citation, depth)`
- [ ] `find_negative_treatment(citation)`

### 7.3 Graph Activities
- [ ] `bfs_citation_traversal(start, filters, max_depth)`
- [ ] `find_citation_path(from, to)`
- [ ] `get_citation_cluster(center, radius)`

### 7.4 Semantic Activities (if Phase 4 built)
- [ ] `find_similar_fact_patterns(query, top_k)`
- [ ] `extract_holdings(case_text)`
- [ ] `match_legal_issue(fact_pattern)`

---

## PHASE 8: High-Value Workflows
**Time Estimate: 3-4 weeks**
**Priority: MVP - After Phase 1, 6, 7**

### 8.1 Comprehensive Research Workflow (enhance existing)
- [ ] Add authority filtering (authority > 0.7)
- [ ] Add treatment checking (exclude superseded)
- [ ] Add temporal validation (valid at query date)
- [ ] Implement LLM context review loop (25-step flow)

### 8.2 Shepardization Workflow
- [ ] Input: citation
- [ ] Output: full treatment history, current validity, affected precedent

### 8.3 Case Valuation Workflow
- [ ] Input: fact pattern, jurisdiction
- [ ] Searches: similar facts, damages awarded, settlement ranges
- [ ] Output: estimated case value with confidence intervals

### 8.4 Argument Builder Workflow
- [ ] Input: legal position to argue
- [ ] Searches: supporting authority, binding precedent
- [ ] Anticipates: counterarguments, distinguishing facts
- [ ] Output: structured brief outline with citations

---

## Priority Roadmap

### 🎯 MVP (6-8 weeks)
1. **Phase 1**: Enrich LMDB with authority scores and treatment ✅ START HERE
2. **Phase 6 (partial)**: Add authority/treatment query endpoints
3. **Phase 7 (partial)**: Build authority/treatment activities
4. **Phase 8 (partial)**: Enhance LegalResearchWorkflow to use these

**Result**: Your current workflow gets much smarter without adding case law yet

### 🚀 Full System (16-20 weeks)
1. All of Phase 1 ✅
2. Phase 2: Add case law corpus
3. Phase 3: Treatment engine
4. Phase 6: All advanced endpoints
5. Phase 7: All activities
6. Phase 8: High-value workflows

**Result**: Complete legal research platform

### 🌟 Ultimate System (24-30 weeks)
1. Everything above +
2. Phase 4: Semantic/fact pattern matching
3. Phase 5: Judge analytics
4. Additional data sources (6th Circuit, SCOTUS)

---

## What You DON'T Need to Build ❌

- ❌ New Temporal infrastructure (you have it)
- ❌ New BFF routing (you have it)
- ❌ New model structure (your Pydantic models are good)
- ❌ New LMDB architecture (your 5-database setup is correct)

---

## Current Status Summary

### ✅ Completed (Infrastructure Ready)
- Temporal worker + workflows setup
- BFF with routing logic
- Knowledge service with LMDB
- Citation Chain workflow working
- All generators running
- Models synced to tworker

### 🔨 Next Immediate Steps (MVP Track)
1. **Start Phase 1.1**: Run PageRank on your existing citation graph
2. **Start Phase 1.2**: Build treatment detection logic
3. Once Phase 1 complete → Build Phase 6 endpoints
4. Once Phase 6 complete → Build Phase 7 activities
5. Once Phase 7 complete → Enhance LegalResearchWorkflow (Phase 8.1)

### 📊 Progress Metrics
- **Infrastructure**: 95% complete ✅
- **Core Data**: 40% complete (statutes done, cases missing)
- **Advanced Features**: 5% complete (authority, treatment, temporal all pending)
- **MVP Features**: 15% complete

---

## TL;DR - The Gap

### You Have:
- ✅ The execution engine (Temporal workflows)
- ✅ Ohio statutes with basic citations
- ✅ Model definitions

### You Need:
- 🔨 Enriched LMDB with computed metrics (Phase 1) **← START HERE**
- 🔨 Case law corpus (Phase 2)
- 🔨 Treatment logic (Phase 3)
- 🔨 Enhanced Knowledge Service endpoints (Phase 6)
- 🔨 Activities that use the new data (Phase 7)
- 🔨 Workflows that orchestrate it all (Phase 8)

**Recommendation**: Start with Phase 1. You can make your existing system dramatically better in 2-3 weeks just by computing authority scores and treatment status on your existing Ohio Revised Code data.

---

*Last Updated: 2025-11-21*
*Current Focus: App startup + timers working, then begin Phase 1*