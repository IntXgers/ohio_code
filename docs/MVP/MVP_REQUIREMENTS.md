# MVP Requirements - What Each Corpus Needs

## Current Status

### ✅ Ohio Revised Code (COMPLETE)
```
✅ Scraper - Data collected
✅ Citation Analysis - citation_mapper.py implemented
✅ LMDB Builder - build_comprehensive_lmdb.py implemented
✅ Enrichment - 14 files (OPTIONAL for MVP)
✅ Fine-tuning - pipeline.py (OPTIONAL for MVP)
```

### 🚧 Other Corpuses (EMPTY FOLDERS)
```
ohio_administration/
ohio_constitution/
ohio_case_law/
  ├── ✅ scraper/ (data collected)
  ├── ❌ citation_analysis/ (only __init__.py)
  ├── ❌ lmdb/ (only __init__.py)
  ├── ❌ enrichment/ (only __init__.py)
  └── ❌ finetuning/ (only __init__.py)
```

---

## 🎯 WHAT YOU ACTUALLY NEED FOR MVP

### Required for Each Corpus (Ship-Critical)

#### 1. ✅ Scraper (DONE)
**Purpose:** Get the raw legal data
**Status:** You have this for all 4 corpuses

#### 2. ⚠️ Citation Analysis (COPY & ADAPT)
**Purpose:** Build citation graphs - THIS IS YOUR COMPETITIVE MOAT
**Files needed:**
- `citation_mapper.py` - Main citation extraction engine
- `ohio_revised_mapping.py` - Maps sections to titles (adapt per corpus)

**Why critical:** Without this, you just have documents. With it, you have a citation graph that Westlaw doesn't offer.

**Action:** Copy from `ohio_revised/` and adapt for:
- Ohio Admin Code citation patterns
- Ohio Constitution citation patterns
- Case law citation patterns (case → statute, case → case)

#### 3. ⚠️ LMDB Builder (COPY & ADAPT)
**Purpose:** Create 5 optimized databases for fast retrieval
**Files needed:**
- `build_comprehensive_lmdb.py` - Creates 5 LMDB databases

**5 Databases per corpus:**
1. `sections.lmdb` - Full text + metadata
2. `citations.lmdb` - Forward citations (what does this cite?)
3. `reverse_citations.lmdb` - Backward citations (what cites this?)
4. `chains.lmdb` - Complete citation chains
5. `metadata.lmdb` - Corpus statistics

**Why critical:** This is what your app queries. No LMDB = no app.

**Action:** Copy from `ohio_revised/` and adapt for different data structures

---

### Optional (NOT Needed for MVP)

#### 4. ❌ Enrichment (SKIP FOR MVP)
**Purpose:** Generate AI training data for fine-tuning
**Files:** 14 files in `ohio_revised/enrichment/`

**What it does:**
- Takes legal sections
- Uses LLM to generate Q&A pairs
- Creates training data for fine-tuning models

**Why skip:**
- NOT needed for the app to work
- Only needed if you want to fine-tune custom legal AI models
- Could be used for commercial model training later (sell legal classification models)

**When to use:**
- After MVP ships
- If you want to create fine-tuned legal AI models
- For generating synthetic training data

#### 5. ❌ Fine-tuning (SKIP FOR MVP)
**Purpose:** Train custom legal AI models
**Files:** `pipeline.py`

**What it does:**
- Takes enriched Q&A data
- Fine-tunes LLM models (Llama, Mistral, etc.)
- Creates specialized legal models

**Why skip:**
- NOT needed for the app to work
- Your app uses LMDB as source of truth (not model weights)
- Optional for creating commercial AI products later

---

## 📊 MVP Architecture (What Actually Ships)

```
┌─────────────────────────────────────────────────────────────┐
│                        YOUR MVP APP                          │
└─────────────────────────────────────────────────────────────┘
                              ↓
                    Queries LMDB databases
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              20 LMDB Databases (5 per corpus)                │
├─────────────────────────────────────────────────────────────┤
│  Ohio Revised Code:                                          │
│    ✅ sections.lmdb, citations.lmdb, reverse_citations.lmdb │
│    ✅ chains.lmdb, metadata.lmdb                             │
│                                                               │
│  Ohio Admin Code:                                            │
│    ⚠️ sections.lmdb, citations.lmdb, reverse_citations.lmdb │
│    ⚠️ chains.lmdb, metadata.lmdb                             │
│                                                               │
│  Ohio Constitution:                                          │
│    ⚠️ sections.lmdb, citations.lmdb, reverse_citations.lmdb │
│    ⚠️ chains.lmdb, metadata.lmdb                             │
│                                                               │
│  Ohio Case Law:                                              │
│    ⚠️ sections.lmdb, citations.lmdb, reverse_citations.lmdb │
│    ⚠️ chains.lmdb, metadata.lmdb                             │
└─────────────────────────────────────────────────────────────┘
                              ↑
                    Built from raw data
                              ↑
┌─────────────────────────────────────────────────────────────┐
│                     Citation Analysis                        │
│  Extracts citation relationships from scraped data           │
└─────────────────────────────────────────────────────────────┘
                              ↑
┌─────────────────────────────────────────────────────────────┐
│                      Scraped Data                            │
│  ✅ Ohio Revised Code (23,644 sections)                     │
│  ✅ Ohio Admin Code                                          │
│  ✅ Ohio Constitution                                        │
│  ✅ Ohio Case Law (22,245 cases)                            │
└─────────────────────────────────────────────────────────────┘
```

**Enrichment & Fine-tuning are NOT in this pipeline!**

---

## 🚀 Implementation Priority

### Week 1: Copy & Adapt Core Pipeline
```bash
Priority 1: Ohio Admin Code
- [ ] Copy citation_mapper.py → adapt for OAC citation patterns
- [ ] Copy build_comprehensive_lmdb.py → adapt for OAC data structure
- [ ] Run citation analysis
- [ ] Build 5 LMDB databases
- [ ] Test with queries

Priority 2: Ohio Case Law
- [ ] Copy citation_mapper.py → adapt for case citations
- [ ] Copy build_comprehensive_lmdb.py → adapt for case data
- [ ] Run citation analysis (case→statute, case→case)
- [ ] Build 5 LMDB databases
- [ ] Test with queries

Priority 3: Ohio Constitution
- [ ] Copy citation_mapper.py → adapt for constitution citations
- [ ] Copy build_comprehensive_lmdb.py → adapt for constitution data
- [ ] Run citation analysis
- [ ] Build 5 LMDB databases
- [ ] Test with queries
```

### Week 2: Integration & Testing
```bash
- [ ] Unified query interface across all 4 corpuses
- [ ] Cross-corpus citation tracking (ORC → OAC, Case → ORC)
- [ ] Test citation chains across corpuses
- [ ] Performance testing
- [ ] Deploy to your app
```

---

## 📂 File Copying Guide

### For Each Corpus, Copy These 2 Core Files:

#### 1. Citation Mapper
```bash
# Copy template
cp ohio_revised/src/ohio_revised/citation_analysis/citation_mapper.py \
   ohio_administration/src/ohio_administration/citation_analysis/

# Adapt regex patterns for corpus-specific citations
# Ohio Admin Code: "Ohio Adm.Code 3701-1-01"
# Case Law: "State v. Smith, 123 Ohio St.3d 456"
# Constitution: "Ohio Const. Art. I, § 10"
```

#### 2. LMDB Builder
```bash
# Copy template
cp ohio_revised/src/ohio_revised/lmdb/build_comprehensive_lmdb.py \
   ohio_administration/src/ohio_administration/lmdb/

# Adapt input file paths and data structure parsing
# Each corpus has slightly different JSONL structure
```

---

## ❓ Your Questions Answered

### Q: Is enrichment purely for fine-tuning or other reasons?
**A: Purely for fine-tuning.**

Enrichment creates AI training data (Q&A pairs) from legal sections. This is ONLY used if you want to:
- Fine-tune custom legal models (Llama, Mistral, etc.)
- Sell fine-tuned legal classification models commercially
- Create synthetic training data

**Your app does NOT need enrichment.** Your app uses LMDB as the source of truth, not fine-tuned model weights.

### Q: Which folders need citation_analysis, enrichment, lmdb, finetuning?
**For MVP:**
- ✅ `citation_analysis/` - REQUIRED for all 4 corpuses
- ✅ `lmdb/` - REQUIRED for all 4 corpuses
- ❌ `enrichment/` - SKIP (only for fine-tuning)
- ❌ `finetuning/` - SKIP (only for creating custom models)

### Q: At the very least we need citation_analysis and lmdb?
**A: YES! Exactly right.**

**Minimum for MVP:**
1. ✅ Scraped data (you have this)
2. ✅ `citation_analysis/` → creates citation graphs
3. ✅ `lmdb/` → creates databases your app queries

**Skip entirely:**
- ❌ `enrichment/` (fine-tuning prep)
- ❌ `finetuning/` (model training)

---

## 🎯 The Bottom Line

**To ship MVP:**
```
For each of 4 corpuses:
  1. ✅ Raw data (scraped) - YOU HAVE THIS
  2. ⚠️ Citation mapper - COPY & ADAPT FROM ohio_revised
  3. ⚠️ LMDB builder - COPY & ADAPT FROM ohio_revised

Total: 2 files × 3 corpuses = 6 files to create
```

**Enrichment and fine-tuning are future features for building commercial AI models - NOT needed for app to work.**

---

## 📋 Next Actions

1. **Confirm data structure** for each corpus (check scraped JSONL format)
2. **Copy citation_mapper.py** to other 3 corpuses
3. **Adapt regex patterns** for each corpus's citation style
4. **Run citation analysis** on all corpuses
5. **Copy build_comprehensive_lmdb.py** to other 3 corpuses
6. **Build 20 LMDB databases** (5 × 4 corpuses)
7. **Test queries** against all databases
8. **Ship MVP** with 4 Ohio corpuses

Then later, add federal law (US Code, SCOTUS, 6th Circuit) using the same pattern.

---

**Key Insight:** Your competitive moat is the citation graph, not enrichment/fine-tuning. Get the 20 LMDB databases built first. Everything else is optional.