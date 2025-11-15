# Ohio Revised Code - Complete Data Flow & File Reference

## Overview
This document maps the complete data pipeline from web scraping to LMDB database creation (the primary goal), showing what each file does, what data it processes, and who uses its output.

**PRIMARY GOAL:** Create comprehensive LMDB databases for fast retrieval in legal applications.

**SECONDARY/OPTIONAL:** AI enrichment and fine-tuning for potential commercial legal AI models.

---

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         OHIO REVISED CODE PIPELINE                       │
│                                                                           │
│  WEB SCRAPING → JSON CONVERSION → CITATION ANALYSIS                     │
│                                           ↓                               │
│                                   ═══════════════                         │
│                                   ║ LMDB DATABASE ║  ← PRIMARY GOAL      │
│                                   ═══════════════                         │
│                                           ↓                               │
│                                   External App Uses LMDB                  │
│                                                                           │
│  ┌────────────────────────────────────────────────────────┐             │
│  │ OPTIONAL: AI Enrichment → Fine-tuning                  │             │
│  │ (For commercial legal AI model development)            │             │
│  └────────────────────────────────────────────────────────┘             │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## STAGE 1: WEB SCRAPING & DATA COLLECTION

### 📄 File: `scraper/law_scraper.py`

**Purpose:** Scrapes Ohio Revised Code from codes.ohio.gov

**Input:**
- URLs from `https://codes.ohio.gov/ohio-revised-code/`
- Resume state from `scraper/scraper_state.json`

**Process:**
1. Crawls titles 1-63 (odd numbered)
2. For each title, extracts all chapters
3. For each chapter, follows section links
4. Extracts header and paragraphs from each section
5. Saves progress to state file for resumability

**Output:**
- `scraped_titles/title-XXX.json` (one per title)
  - Format: JSON array of sections
  - Each section contains:
    ```json
    {
      "url": "https://codes.ohio.gov/...",
      "header": "Section 1234.56 | Title of Section",
      "paragraphs": ["text...", "text..."],
      "url_hash": "abc123def456"
    }
    ```

**Used By:** `convert_to_jsonl.py`

**Key Classes/Functions:**
- `OhioCodeScraper` - Main scraper class
- `crawl_all_titles()` - Entry point for scraping
- `crawl_sections_from_chapter()` - Section-by-section crawler

---

## STAGE 2: FORMAT CONVERSION

### 📄 File: `scraper/convert_to_jsonl.py`

**Purpose:** Converts JSON arrays to JSONL format (one record per line)

**Input:**
- `data/pre_enriched_input/ohio_revised_code_complete.json`
  - Combined JSON array from all title files

**Process:**
1. Reads JSON array
2. Keeps only essential fields: url, url_hash, header, paragraphs
3. Writes each object as single-line JSON

**Output:**
- `data/pre_enriched_input/ohio_revised_code_complete.jsonl`
  - Format: JSONL (one JSON per line)
  - Each line:
    ```json
    {"url": "...", "url_hash": "...", "header": "...", "paragraphs": [...]}
    ```

**Used By:**
- `enrichment/enrichment.py`
- `citation_analysis/citation_mapper.py`

---

### 📄 File: `scraper/transform.py`

**Purpose:** Alternative transformation that joins paragraphs into content string

**Input:**
- `output_cleaned.json` (JSON array)

**Process:**
1. Takes header + paragraphs array
2. Joins paragraphs into single content string

**Output:**
- `output_sorted.jsonl`
  - Format: JSONL with flat structure
  - Each line:
    ```json
    {"header": "...", "content": "full text here"}
    ```

**Used By:** Alternative preprocessing path (not main pipeline)

---

## STAGE 3: CITATION ANALYSIS (CORE PIPELINE)

### 📄 File: `citation_analysis/citation_mapper.py`

**Purpose:** Builds citation graph showing which sections reference other sections

**Input:**
- `ohio_revised_code_complete.jsonl`
- Resume from `citation_analysis/citation_state.json`

**Process:**
1. Extracts section numbers from headers
2. Uses regex patterns to find cross-references:
   - "Section 124.01"
   - "sections 124.01 to 124.64"
   - "division (A) of section 124.23"
   - "Chapter 119. of the Revised Code"
3. Builds forward citation map (who does this cite?)
4. Analyzes complexity:
   - Isolated sections (no references)
   - Simple chains (2-3 sections)
   - Complex chains (4+ sections)
5. Saves checkpoints every 1000 sections

**Output:**
- `data/citation_analysis/citation_map.json`
  - Format: `{"section": ["ref1", "ref2", ...]}`
  - Maps each section to its references
- `data/citation_analysis/processing_manifest.json`
  - Categorizes sections by complexity
- `data/citation_analysis/complex_chains.jsonl`
  - JSONL of complex citation chains
  - Each line:
    ```json
    {
      "chain_id": "complex_0",
      "primary_section": "1234.56",
      "chain_sections": ["1234.56", "1234.57", "1234.58", ...],
      "estimated_complexity": 6
    }
    ```
- `data/citation_analysis/citation_analysis.json`
  - Statistics: total sections, reference counts, etc.

**Used By:** `lmdb/build_comprehensive_lmdb.py`

**Key Classes/Functions:**
- `CitationMapper` - Main citation analyzer
- `build_citation_mapping()` - Builds forward citation graph
- `analyze_citation_patterns()` - Categorizes by complexity
- `extract_cross_references()` - Regex-based reference extraction

---

## STAGE 4: LMDB DATABASE CREATION (PRIMARY GOAL)

### 📄 File: `lmdb/build_comprehensive_lmdb.py`

**Purpose:** Creates optimized LMDB databases for fast legal code retrieval

**Input:**
- `data/ohio_revised_code/ohio_revised_code_complete.jsonl`
- `data/citation_analysis/citation_map.json`
- `data/citation_analysis/complex_chains.jsonl`
- `data/citation_analysis/citation_analysis.json`

**Process:**
1. Opens 5 separate LMDB databases (2GB each)
2. **Sections DB:** Full text + metadata for each section
3. **Citations DB:** Forward references (who does this cite?)
4. **Reverse Citations DB:** Backward references (who cites this?)
5. **Chains DB:** Complex citation chains with full text
6. **Metadata DB:** Corpus statistics + per-section metadata

**Output:**
- `data/enriched_output/comprehensive_lmdb/sections.lmdb`
  - Key: section number
  - Value: Full section data with metadata
  ```json
  {
    "section_number": "1234.56",
    "url": "...",
    "header": "...",
    "full_text": "...",
    "word_count": 523,
    "has_citations": true,
    "citation_count": 3
  }
  ```

- `data/enriched_output/comprehensive_lmdb/citations.lmdb`
  - Key: section number
  - Value: All sections this section references
  ```json
  {
    "section": "1234.56",
    "direct_references": ["1234.57", "1234.58"],
    "references_details": [{"section": "1234.57", "title": "...", "url": "..."}]
  }
  ```

- `data/enriched_output/comprehensive_lmdb/reverse_citations.lmdb`
  - Key: section number
  - Value: All sections that cite this section
  ```json
  {
    "section": "1234.56",
    "cited_by": ["1234.55", "1234.60"],
    "cited_by_count": 2
  }
  ```

- `data/enriched_output/comprehensive_lmdb/chains.lmdb`
  - Key: chain_id
  - Value: Full chain with all section texts
  ```json
  {
    "chain_id": "complex_0",
    "chain_sections": ["1234.56", "1234.57", ...],
    "complete_chain": [{"section": "...", "full_text": "..."}]
  }
  ```

- `data/enriched_output/comprehensive_lmdb/metadata.lmdb`
  - Key: "corpus_info" or "section_XXX_meta"
  - Value: Corpus or section metadata

**Used By:**
- `lmdb/legal_chain_retriever.py`
- `lmdb/legal_query_processor.py`
- External application (your other repo)

**Key Classes/Functions:**
- `ComprehensiveLMDBBuilder` - Main builder
- `build_sections_database()` - Sections with full metadata
- `build_citations_database()` - Forward references
- `build_reverse_citations_database()` - Backward references
- `build_chains_database()` - Complex chains

---

## OPTIONAL STAGES (For Commercial AI Model Development)

These stages are not required for the main LMDB database but provide value for developing fine-tuned legal AI models that could be sold commercially.

### 📄 File: `enrichment/enrichment.py` (OPTIONAL)

**Purpose:** Enriches legal sections with defense attorney analysis using LLM

**Input:**
- `ohio_revised_code_complete.jsonl`
- LLM model (llama.cpp format, path from config)
- Resume from `checkpoints/defense_enrichment_checkpoint.json`

**Process:**
1. Loads each section from JSONL
2. For each section, generates 6 types of defense-focused analysis:
   - **Defense Scenarios** (4 scenarios per section)
   - **Constitutional Analysis** (4th, 5th, 6th Amendment issues)
   - **Evidence Challenges** (suppression strategies)
   - **Jury Strategy** (voir dire, themes)
   - **Negotiation Strategy** (plea deals, leverage)
   - **Cross Examination** (witness strategies)
3. Saves in batches of 10 with checkpointing
4. Creates multiple training formats

**Output:**
- `data/enriched/stage_1_statutory/scenarios_TIMESTAMP.jsonl`
- `data/enriched/stage_1_statutory/constitutional_TIMESTAMP.jsonl`
- `data/enriched/stage_1_statutory/evidence_TIMESTAMP.jsonl`
- `data/enriched/stage_1_statutory/jury_TIMESTAMP.jsonl`
- `data/enriched/stage_1_statutory/chatml_TIMESTAMP.jsonl`
- `data/enriched/stage_1_statutory/enriched_complete_TIMESTAMP.jsonl`

**Used By:** `finetuning/pipeline.py`

**Commercial Potential:** Could be used to create fine-tuned legal classification models for sale

---

### 📄 File: `finetuning/pipeline.py` (OPTIONAL)

**Purpose:** Fine-tunes LLM models on enriched defense attorney data for commercial legal AI development

**Input:**
- All JSONL files from `data/enriched/stage_1_statutory/`:
  - scenarios_*.jsonl
  - constitutional_*.jsonl
  - evidence_*.jsonl
  - jury_*.jsonl
  - chatml_*.jsonl

**Process:**
1. Loads all enriched JSONL files
2. Formats for training (ChatML, instruction, or Q&A format)
3. Tokenizes with padding/truncation
4. Creates train/eval split (90/10)
5. Configures LoRA for parameter-efficient fine-tuning
6. Trains model with gradient accumulation
7. Saves checkpoints every 500 steps

**Output:**
- `models/defense-attorney-v1/` (or configured output_dir)
  - Fine-tuned model weights (LoRA adapters)
  - Tokenizer files
  - `training_config.yaml` - Training configuration
  - Training checkpoints

**Used By:** Inference/deployment systems

**Key Classes/Functions:**
- `DefenseFineTuner` - Main training orchestrator
- `DefenseDatasetBuilder` - Dataset preparation
- `format_for_training()` - ChatML/instruction formatting
- `train()` - Training loop with HuggingFace Trainer

---

## RETRIEVAL & QUERY (Supporting Files)

### 📄 File: `lmdb/legal_chain_retriever.py`

**Purpose:** Retrieves legal sections and their citation chains from LMDB

**Input:**
- LMDB databases from `build_comprehensive_lmdb.py`
- Query: section number or search criteria

**Process:**
1. Opens LMDB databases
2. Retrieves section by key
3. Optionally expands to citation chain
4. Returns full text + metadata

**Output:**
- Python dictionary with section data and citations

**Used By:** Query processor, external applications

---

### 📄 File: `lmdb/legal_query_processor.py`

**Purpose:** Processes natural language queries against legal database

**Input:**
- LMDB databases
- User query (e.g., "What are the OVI penalties?")

**Process:**
1. Parses query
2. Searches sections database
3. Retrieves relevant sections + chains
4. Formats response

**Output:**
- Structured response with relevant legal sections

**Used By:** External application, chatbot interface

---

## DATA DIRECTORY STRUCTURE

```
ohio_revised/src/ohio_revised/data/
├── pre_enriched_input/
│   ├── ohio_revised_code_complete.json      [Scraped data: JSON array]
│   └── ohio_revised_code_complete.jsonl     [Converted: JSONL format]
│
├── ohio_revised_code/
│   └── ohio_revised_code_complete.jsonl     [Canonical corpus]
│
├── citation_analysis/
│   ├── citation_map.json                     [Section → References]
│   ├── processing_manifest.json              [Complexity categories]
│   ├── complex_chains.jsonl                  [Complex citation chains]
│   └── citation_analysis.json                [Statistics]
│
├── enriched/
│   └── stage_1_statutory/
│       ├── scenarios_TIMESTAMP.jsonl         [Defense scenarios]
│       ├── constitutional_TIMESTAMP.jsonl    [Constitutional analysis]
│       ├── evidence_TIMESTAMP.jsonl          [Evidence challenges]
│       ├── jury_TIMESTAMP.jsonl              [Jury strategies]
│       ├── chatml_TIMESTAMP.jsonl            [Conversational format]
│       └── enriched_complete_TIMESTAMP.jsonl [Full enrichment]
│
└── enriched_output/
    └── comprehensive_lmdb/
        ├── sections.lmdb                     [Full section texts]
        ├── citations.lmdb                    [Forward citations]
        ├── reverse_citations.lmdb            [Backward citations]
        ├── chains.lmdb                       [Complex chains]
        └── metadata.lmdb                     [Corpus metadata]
```

---

## COMPLETE DATA FLOW DIAGRAM

```
                    ┌────────────────────────┐
                    │   codes.ohio.gov       │
                    │   (Web Source)         │
                    └───────────┬────────────┘
                                │
                                ▼
                    ┌────────────────────────┐
                    │  law_scraper.py        │
                    │  Scrapes all titles    │
                    └───────────┬────────────┘
                                │
                    scraped_titles/title-XXX.json
                                │
                                ▼
                    ┌────────────────────────┐
                    │  convert_to_jsonl.py   │
                    │  JSON → JSONL          │
                    └───────────┬────────────┘
                                │
              ohio_revised_code_complete.jsonl
                                │
                    ┌───────────┴──────────┐
                    ▼                      ▼
        ┌────────────────────┐  ┌────────────────────┐
        │ enrichment.py      │  │ citation_mapper.py │
        │ AI enrichment      │  │ Build citation map │
        └─────────┬──────────┘  └─────────┬──────────┘
                  │                        │
    enriched/*.jsonl              citation_map.json
                  │                complex_chains.jsonl
                  │                        │
                  │                        │
                  ▼                        ▼
        ┌─────────────────────────────────────────┐
        │     build_comprehensive_lmdb.py         │
        │     Creates 5 LMDB databases            │
        └─────────────────┬───────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
    sections.lmdb  citations.lmdb  chains.lmdb
                          │
          ┌───────────────┴───────────────┐
          ▼                               ▼
    ┌──────────────┐            ┌──────────────────┐
    │ pipeline.py  │            │ legal_chain_     │
    │ Fine-tuning  │            │ retriever.py     │
    └──────────────┘            │ Query engine     │
          │                     └──────────────────┘
          ▼                               ▼
    Fine-tuned Model              External App
   (defense-attorney-v1)         (Your other repo)
```

---

## KEY FILE PURPOSES SUMMARY

| File | Input | Output | Purpose |
|------|-------|--------|---------|
| `law_scraper.py` | codes.ohio.gov URLs | `title-XXX.json` | Web scraping |
| `convert_to_jsonl.py` | JSON arrays | `*.jsonl` | Format conversion |
| `transform.py` | JSON arrays | `*.jsonl` | Alternative conversion |
| `enrichment.py` | Raw JSONL + LLM | Enriched JSONL (6 types) | AI enrichment |
| `citation_mapper.py` | Raw JSONL | Citation maps/chains | Citation analysis |
| `build_comprehensive_lmdb.py` | JSONL + citations | 5 LMDB databases | Database creation |
| `pipeline.py` | Enriched JSONL | Fine-tuned model | Model training |
| `legal_chain_retriever.py` | LMDB databases | Section + chains | Data retrieval |
| `legal_query_processor.py` | LMDB + query | Search results | Query processing |

---

## USAGE NOTES

### Core Pipeline (Required for LMDB Database):

1. **Scrape:** `python -m ohio_revised.scraper.law_scraper`
2. **Convert:** `python -m ohio_revised.scraper.convert_to_jsonl`
3. **Analyze Citations:** `python -m ohio_revised.citation_analysis.citation_mapper`
4. **Build LMDB:** `python -m ohio_revised.lmdb.build_comprehensive_lmdb` ← **PRIMARY GOAL**

### Optional Pipeline (For Commercial AI Models):

5. **Enrich (Optional):** `python -m ohio_revised.enrichment.enrichment`
6. **Fine-tune (Optional):** `python -m ohio_revised.finetuning.pipeline`

### To Query Existing Data:

```python
from ohio_revised.lmdb.legal_chain_retriever import LegalChainRetriever

retriever = LegalChainRetriever("data/enriched_output/comprehensive_lmdb")
result = retriever.get_section("2913.02")  # Theft statute
```

---

## CHECKPOINTING & RESUMABILITY

All major processes support resumability:

- **Scraping:** `scraper_state.json` tracks progress
- **Enrichment:** `defense_enrichment_checkpoint.json` tracks processed items
- **Citation Analysis:** `citation_state.json` tracks last processed line

To resume after interruption, simply re-run the script. It will load state and continue.

---

## EXTERNAL DEPENDENCIES

- **Web scraping:** `requests`, `beautifulsoup4`
- **Enrichment:** `llama-cpp-python` (for local LLM)
- **LMDB:** `lmdb` library
- **Fine-tuning:** `transformers`, `peft`, `torch`
- **Analysis:** `numpy`, `tqdm`, `pyyaml`

---

**Generated:** 2025-11-12
**Pipeline Version:** 2.0
**Author:** Claude Code