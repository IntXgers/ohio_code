# Documentation Directory - Ohio Legal Code Project

This directory contains project documentation, analysis reports, and reference guides for the Ohio Legal Code data pipeline and application.

---

## Core Reference Documents

### 📊 LMDB_DATABASE_STRUCTURE.md
**What it is:** Detailed documentation of the 5 LMDB databases that power the application

**Contents:**
- Complete data pipeline flow (scraping → enrichment → LMDB)
- Each LMDB database structure (sections, citations, reverse_citations, chains, metadata)
- Key/value schemas with examples
- Query patterns and usage examples
- File purposes for retrieval and query scripts

**Use this when:** You need to understand the LMDB structure, query patterns, or data flow

**Related files:** `ohio_revised/src/ohio_revised/lmdb/`

---

### 🔗 SYMLINK_STRUCTURE.md
**What it is:** Complete symlink architecture for all 7 corpuses and application integration

**Contents:**
- Complete directory structure for ohio_code repository (data pipeline)
- dist/ folder organization (35 LMDB databases)
- Symlink setup commands for your app repository
- Build process for each corpus
- Knowledge service configuration (lmdb_store.py)
- FastAPI endpoint examples
- Disk space estimates (~27 GB total)

**Use this when:** Setting up symlinks, deploying LMDB databases, or understanding app/pipeline separation

**Related files:** All corpus folders, your app's knowledge_service directory

**Architecture:**
- ohio_code/dist/ = final output (35 LMDB databases)
- Your app symlinks to dist/
- Query logic stays in your app
- Data pipeline stays in ohio_code

---

### 🎨 SIMPLIFIED_ENRICHMENT_FINAL.md
**What it is:** Final simplified enrichment system (7 metadata fields for UX)

**Contents:**
- What enrichment provides: Better UX, visual tree graphs, progressive disclosure, domain filtering
- 7 essential fields: summary, legal_type, practice_areas, complexity, key_terms, offense_level, offense_degree
- UX value proposition (75% fewer sections shown = less scrolling)
- Temporal workflow integration examples
- Comparison: before vs after enrichment
- Testing results and next steps

**Use this when:** Understanding enrichment purpose, implementing enrichment in other corpuses, or querying with filters

**Related files:** `ohio_revised/src/ohio_revised/lmdb/auto_enricher.py`, `build_comprehensive_lmdb.py`

**Key insight:** Enrichment is for UX (not cost savings). User has local hardware. Focus is on preventing information overload.

---

### 📐 ENHANCED_LMDB_SCHEMA.md
**What it is:** Comprehensive schema documentation with enrichment metadata (reference guide)

**Contents:**
- Enhanced schema design for all 5 LMDB databases
- Enrichment field descriptions and purposes
- Implementation strategy (Phase 1-4)
- Query examples with enhanced schema
- Benefits: AI agents filter by practice area, complexity filtering, relationship understanding

**Use this when:** Implementing enrichment, designing new fields, or understanding full schema capabilities

**Related files:** `ohio_revised/src/ohio_revised/lmdb/auto_enricher.py`, `build_comprehensive_lmdb.py`

**Note:** This is the comprehensive reference. SIMPLIFIED_ENRICHMENT_FINAL.md is the final implementation (7 fields, not 15).

---

### 📋 ENRICHMENT_ANALYSIS.md
**What it is:** Analysis of the AI enrichment pipeline for generating training data

**Contents:**
- Current enrichment files and their purposes
- Template system architecture (title-specific question generation)
- Missing template files (32 of 33 titles)
- Quality metrics and validation
- Training data generation capabilities
- Recommendations for completing template library

**Use this when:** Planning AI enrichment, understanding training data generation, or implementing new title templates

**Related files:** `ohio_revised/src/ohio_revised/enrichment/`

**Status:**
- ✅ Core pipeline complete
- ⚠️ Only 1 of 33 title templates implemented
- 📊 Can generate ~400K Q&A pairs with fallback questions

---

### 📝 document_checklist.md
**What it is:** Comprehensive checklist of legal data sources for the platform

**Contents:**
- ✅ Tier 1 (Ship with MVP): Ohio Revised Code, Ohio Admin Code, Ohio Constitution, Ohio Case Law, US Code, SCOTUS, 6th Circuit = 7 corpuses
- ⏳ Tier 2 (Post-launch): Court rules, CFR, agency opinions
- 📋 Tier 3 (Different product): Forms, jury instructions, legislative history
- ❌ Tier 4 (Out of scope): All circuits, all districts, specialty courts
- Data source URLs and scraping methods
- Priority tiers with "Agent-First Test" decision framework

**Use this when:** Planning data collection, understanding current coverage, or prioritizing new data sources

**Related files:** All scraper modules across `ohio_*` directories

**Coverage:**
- Ohio State Law: 90% complete (4 corpuses)
- Federal Law: 0% (US Code, SCOTUS, 6th Circuit to be added)
- Total MVP: 7 corpuses = 35 LMDB databases

---

### 🤖 finetune.md
**What it is:** Security and behavioral guide for fine-tuning the legal AI model (Jurist)

**Contents:**
- Model architecture principles (LMDB as source of truth)
- Behavioral fine-tuning vs content fine-tuning
- Security measures (protecting proprietary system)
- Accuracy guardrails (preventing hallucinations)
- Response structure guidelines
- Liability protection measures
- Testing and monitoring checklists

**Use this when:** Fine-tuning models, writing system prompts, or implementing security measures

**Key principle:** DO NOT fine-tune on legal content (LMDB is source of truth). DO fine-tune on behavior (how to retrieve, format, and reason).

**Models mentioned:**
- DeepSeek R1 32B (reasoning-focused)
- Llama (raw/base models)
- Mistral 8B (some instruction following)

---

### 📈 project_status.md
**What it is:** Historical project status snapshot from August 2025

**Contents:**
- Citation analysis pipeline completion status
- Architecture analysis results (23,644 sections)
- Quality metrics with different models
- Hardware upgrade plans (64GB VRAM workstation)
- Processing expectations

**Use this when:** Understanding historical context or baseline metrics

**Note:** This is a historical snapshot. Current status should be tracked elsewhere.

**Key metrics:**
- Total sections: 23,644
- Sections with cross-references: 16,429 (69%)
- Complex chains: 294 (11,429 sections)

---

## Legacy/Archive Documents

### 001*.py and 001*.yaml files
**What they are:** Early experimental scripts and configurations

**Contents:**
- `001config.yaml` - Old configuration file
- `001context_analyzer.py` - Early context analysis script
- `001modelman_config.py` - Model configuration
- `001web.py` - Web scraping experiments

**Use these when:** Reviewing historical approaches (likely superseded by current implementations)

**Status:** Archive - kept for reference

---

### linux_setup.md
**What it is:** Linux server setup instructions

**Contents:** Instructions for setting up the pipeline on Linux servers

**Use this when:** Deploying to Linux environments

---

### pipline_mod.md
**What it is:** Pipeline modification notes

**Contents:** Notes on modifying the data processing pipeline

**Use this when:** Making changes to pipeline architecture

---

## Document Organization

### By Use Case

**Understanding the system:**
1. Start with `LMDB_DATABASE_STRUCTURE.md` for database structure
2. Review `SIMPLIFIED_ENRICHMENT_FINAL.md` for enrichment (UX focus)
3. Check `SYMLINK_STRUCTURE.md` for deployment architecture
4. Review `document_checklist.md` for data coverage

**Working on AI/ML:**
1. Read `finetune.md` for model training principles
2. Review `ENRICHMENT_ANALYSIS.md` for training data generation (optional fine-tuning)
3. Check `SIMPLIFIED_ENRICHMENT_FINAL.md` for LMDB enrichment (not fine-tuning)

**Adding new data sources:**
1. Check `document_checklist.md` for what's missing (7 corpuses in Tier 1)
2. Review existing scrapers in related modules
3. Copy `auto_enricher.py` and adapt for new corpus

**Deployment:**
1. `SYMLINK_STRUCTURE.md` for symlink setup
2. `linux_setup.md` for server setup
3. `finetune.md` for model deployment security

---

## Quick Reference

| Document | Topic | Status |
|----------|-------|--------|
| LMDB_DATABASE_STRUCTURE.md | Database architecture | ✅ Current |
| SYMLINK_STRUCTURE.md | Deployment architecture (7 corpuses) | ✅ Current |
| SIMPLIFIED_ENRICHMENT_FINAL.md | Enrichment for UX (7 fields) | ✅ Current |
| ENHANCED_LMDB_SCHEMA.md | Comprehensive schema reference | ✅ Current |
| ENRICHMENT_ANALYSIS.md | AI training data (fine-tuning) | ✅ Current |
| document_checklist.md | Data coverage (Tier 1-4) | ✅ Current |
| finetune.md | Model security/training | ✅ Current |
| project_status.md | Historical metrics | 📅 Aug 2025 snapshot |
| UPDATED_KNOWLEDGE_SERVICE_CODE.md | lmdb_store.py & main.py code | ✅ Current |
| linux_setup.md | Linux deployment | 📋 Reference |
| pipline_mod.md | Pipeline changes | 📋 Reference |
| 001*.* files | Legacy experiments | 📦 Archive |

---

## Related Documentation

**For detailed pipeline documentation**, see:
- `ohio_revised/src/ohio_revised/OHIO_REVISED_DATA_FLOW.md` - Complete data flow from web scraping to LMDB

**For code documentation**, see:
- Each module's `README.md` in respective directories
- Inline code comments in Python files

---

**Last Updated:** 2025-11-13
**Maintained By:** Project team
**Documentation Standard:** Markdown with emojis for quick scanning