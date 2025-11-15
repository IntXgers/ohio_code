# Complete Symlink Structure - All 7 Corpuses

## Overview

This document shows the complete directory structure for the **ohio_code** repository (data pipeline) and how your app repository should symlink to the enriched LMDB databases.

**Architecture**:
- `ohio_code/`: Data pipeline repository (scraping, enrichment, LMDB building)
- `ohio_code/dist/`: Final output directory containing all enriched LMDB databases
- Your app: Symlinks to `dist/` and includes query logic (knowledge service + Temporal workflows)

---

## Complete Directory Structure

```
ohio_code/
├── dist/                                    # ← Final output (35 LMDB databases)
│   ├── ohio_revised/
│   │   ├── sections.lmdb
│   │   ├── citations.lmdb
│   │   ├── reverse_citations.lmdb
│   │   ├── chains.lmdb
│   │   └── metadata.lmdb
│   ├── ohio_administration/
│   │   ├── sections.lmdb
│   │   ├── citations.lmdb
│   │   ├── reverse_citations.lmdb
│   │   ├── chains.lmdb
│   │   └── metadata.lmdb
│   ├── ohio_constitution/
│   │   ├── sections.lmdb
│   │   ├── citations.lmdb
│   │   ├── reverse_citations.lmdb
│   │   ├── chains.lmdb
│   │   └── metadata.lmdb
│   ├── ohio_case_law/
│   │   ├── sections.lmdb
│   │   ├── citations.lmdb
│   │   ├── reverse_citations.lmdb
│   │   ├── chains.lmdb
│   │   └── metadata.lmdb
│   ├── us_code/
│   │   ├── sections.lmdb
│   │   ├── citations.lmdb
│   │   ├── reverse_citations.lmdb
│   │   ├── chains.lmdb
│   │   └── metadata.lmdb
│   ├── scotus/
│   │   ├── sections.lmdb
│   │   ├── citations.lmdb
│   │   ├── reverse_citations.lmdb
│   │   ├── chains.lmdb
│   │   └── metadata.lmdb
│   └── sixth_circuit/
│       ├── sections.lmdb
│       ├── citations.lmdb
│       ├── reverse_citations.lmdb
│       ├── chains.lmdb
│       └── metadata.lmdb
│
├── ohio_revised/
│   ├── src/ohio_revised/
│   │   ├── scraper/
│   │   │   ├── law_scraper.py
│   │   │   ├── convert_to_jsonl.py
│   │   │   └── transform.py
│   │   ├── citation_analysis/
│   │   │   ├── citation_mapper.py
│   │   │   └── ohio_revised_mapping.py
│   │   ├── lmdb/
│   │   │   ├── auto_enricher.py              # ← Copy to other corpuses
│   │   │   ├── build_comprehensive_lmdb.py   # ← Adapt for other corpuses
│   │   │   └── inspect_lmdb.py
│   │   ├── enrichment/
│   │   │   └── (optional LLM enrichment - not used in MVP)
│   │   └── finetuning/
│   │       └── (optional fine-tuning - not used in MVP)
│   └── data/
│       ├── ohio_revised_code/
│       │   └── ohio_revised_code_complete.jsonl
│       ├── citation_analysis/
│       │   ├── citation_map.json
│       │   └── complex_chains.jsonl
│       └── enriched_output/
│           └── comprehensive_lmdb/  # ← Gets copied to dist/ohio_revised/
│
├── ohio_administration/
│   └── (same structure as ohio_revised)
│
├── ohio_constitution/
│   └── (same structure as ohio_revised)
│
├── ohio_case_law/
│   └── (same structure as ohio_revised)
│
├── us_code/
│   └── (same structure as ohio_revised)
│
├── scotus/
│   └── (same structure as ohio_revised)
│
├── sixth_circuit/
│   └── (same structure as ohio_revised)
│
└── docs/
    ├── README.md
    ├── LMDB_DATABASE_STRUCTURE.md
    ├── SIMPLIFIED_ENRICHMENT_FINAL.md
    ├── ENHANCED_LMDB_SCHEMA.md
    ├── SYMLINK_STRUCTURE.md (this file)
    └── document_checklist.md
```

---

## Your App Repository Structure

```
your_app/
├── knowledge_service/
│   ├── lmdb_store.py                # Query logic (from UPDATED_KNOWLEDGE_SERVICE_CODE.md)
│   ├── main.py                      # FastAPI endpoints
│   └── lmdb_data/                   # ← Symlink directory
│       ├── ohio_revised -> /path/to/ohio_code/dist/ohio_revised/
│       ├── ohio_administration -> /path/to/ohio_code/dist/ohio_administration/
│       ├── ohio_constitution -> /path/to/ohio_code/dist/ohio_constitution/
│       ├── ohio_case_law -> /path/to/ohio_code/dist/ohio_case_law/
│       ├── us_code -> /path/to/ohio_code/dist/us_code/
│       ├── scotus -> /path/to/ohio_code/dist/scotus/
│       └── sixth_circuit -> /path/to/ohio_code/dist/sixth_circuit/
│
├── temporal_workflows/
│   ├── statute_analysis_workflow.py
│   ├── case_law_research_workflow.py
│   └── activities/
│       ├── lmdb_activities.py       # Calls knowledge_service
│       └── deepseek_activities.py   # Calls DeepSeek 30B
│
└── ui/
    ├── citation_tree_visualizer.tsx  # Visual tree graphs
    └── focused_results_view.tsx      # Collapsible sections
```

---

## Symlink Setup Commands

After building all LMDB databases in `ohio_code`, run these commands in your app repository:

```bash
# Create symlink directory
mkdir -p knowledge_service/lmdb_data

# Set path to ohio_code repository
OHIO_CODE_PATH="/Users/justinrussell/active_projects/LEGAL/ohio_code"

# Create symlinks to all 7 corpuses
ln -s "$OHIO_CODE_PATH/dist/ohio_revised" knowledge_service/lmdb_data/ohio_revised
ln -s "$OHIO_CODE_PATH/dist/ohio_administration" knowledge_service/lmdb_data/ohio_administration
ln -s "$OHIO_CODE_PATH/dist/ohio_constitution" knowledge_service/lmdb_data/ohio_constitution
ln -s "$OHIO_CODE_PATH/dist/ohio_case_law" knowledge_service/lmdb_data/ohio_case_law
ln -s "$OHIO_CODE_PATH/dist/us_code" knowledge_service/lmdb_data/us_code
ln -s "$OHIO_CODE_PATH/dist/scotus" knowledge_service/lmdb_data/scotus
ln -s "$OHIO_CODE_PATH/dist/sixth_circuit" knowledge_service/lmdb_data/sixth_circuit

# Verify symlinks
ls -la knowledge_service/lmdb_data/
```

**Expected output**:
```
ohio_revised -> /Users/justinrussell/active_projects/LEGAL/ohio_code/dist/ohio_revised
ohio_administration -> /Users/justinrussell/active_projects/LEGAL/ohio_code/dist/ohio_administration
ohio_constitution -> /Users/justinrussell/active_projects/LEGAL/ohio_code/dist/ohio_constitution
ohio_case_law -> /Users/justinrussell/active_projects/LEGAL/ohio_code/dist/ohio_case_law
us_code -> /Users/justinrussell/active_projects/LEGAL/ohio_code/dist/us_code
scotus -> /Users/justinrussell/active_projects/LEGAL/ohio_code/dist/scotus
sixth_circuit -> /Users/justinrussell/active_projects/LEGAL/ohio_code/dist/sixth_circuit
```

---

## Build Process for Each Corpus

### 1. Ohio Revised Code (✅ Complete)
```bash
cd ohio_revised/src/ohio_revised/lmdb
python build_comprehensive_lmdb.py
# Outputs to: ohio_revised/data/enriched_output/comprehensive_lmdb/
cp -r ../../../../ohio_revised/data/enriched_output/comprehensive_lmdb/* ../../../dist/ohio_revised/
```

### 2. Ohio Administration Code
```bash
cd ohio_administration/src/ohio_administration/lmdb
python build_comprehensive_lmdb.py
cp -r ../../../../ohio_administration/data/enriched_output/comprehensive_lmdb/* ../../../dist/ohio_administration/
```

### 3. Ohio Constitution
```bash
cd ohio_constitution/src/ohio_constitution/lmdb
python build_comprehensive_lmdb.py
cp -r ../../../../ohio_constitution/data/enriched_output/comprehensive_lmdb/* ../../../dist/ohio_constitution/
```

### 4. Ohio Case Law
```bash
cd ohio_case_law/src/ohio_case_law/lmdb
python build_comprehensive_lmdb.py
cp -r ../../../../ohio_case_law/data/enriched_output/comprehensive_lmdb/* ../../../dist/ohio_case_law/
```

### 5. US Code
```bash
cd us_code/src/us_code/lmdb
python build_comprehensive_lmdb.py
cp -r ../../../../us_code/data/enriched_output/comprehensive_lmdb/* ../../../dist/us_code/
```

### 6. SCOTUS
```bash
cd scotus/src/scotus/lmdb
python build_comprehensive_lmdb.py
cp -r ../../../../scotus/data/enriched_output/comprehensive_lmdb/* ../../../dist/scotus/
```

### 7. Sixth Circuit
```bash
cd sixth_circuit/src/sixth_circuit/lmdb
python build_comprehensive_lmdb.py
cp -r ../../../../sixth_circuit/data/enriched_output/comprehensive_lmdb/* ../../../dist/sixth_circuit/
```

---

## Total Database Count

**7 corpuses × 5 databases each = 35 LMDB databases**

| Corpus | sections.lmdb | citations.lmdb | reverse_citations.lmdb | chains.lmdb | metadata.lmdb |
|--------|--------------|----------------|------------------------|-------------|---------------|
| Ohio Revised | ✅ | ✅ | ✅ | ✅ | ✅ |
| Ohio Admin | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ |
| Ohio Constitution | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ |
| Ohio Case Law | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ |
| US Code | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ |
| SCOTUS | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ |
| Sixth Circuit | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ |

---

## Knowledge Service Configuration

**lmdb_store.py** should initialize all corpuses:

```python
from pathlib import Path
import lmdb

class LMDBStore:
    def __init__(self, base_path: Path):
        self.corpuses = {
            'ohio_revised': self._open_corpus(base_path / 'ohio_revised'),
            'ohio_administration': self._open_corpus(base_path / 'ohio_administration'),
            'ohio_constitution': self._open_corpus(base_path / 'ohio_constitution'),
            'ohio_case_law': self._open_corpus(base_path / 'ohio_case_law'),
            'us_code': self._open_corpus(base_path / 'us_code'),
            'scotus': self._open_corpus(base_path / 'scotus'),
            'sixth_circuit': self._open_corpus(base_path / 'sixth_circuit'),
        }

    def _open_corpus(self, corpus_path: Path):
        return {
            'sections': lmdb.open(str(corpus_path / 'sections.lmdb'), readonly=True),
            'citations': lmdb.open(str(corpus_path / 'citations.lmdb'), readonly=True),
            'reverse_citations': lmdb.open(str(corpus_path / 'reverse_citations.lmdb'), readonly=True),
            'chains': lmdb.open(str(corpus_path / 'chains.lmdb'), readonly=True),
            'metadata': lmdb.open(str(corpus_path / 'metadata.lmdb'), readonly=True),
        }
```

---

## FastAPI Endpoint Examples

```python
# Cross-corpus search
@app.get("/search")
async def search_all_corpuses(
    query: str,
    corpuses: List[str] = ["ohio_revised", "ohio_case_law", "scotus"],
    legal_type: Optional[str] = None,
    practice_areas: Optional[List[str]] = None
):
    results = {}
    for corpus in corpuses:
        results[corpus] = lmdb_store.search_sections(
            corpus=corpus,
            text=query,
            legal_type=legal_type,
            practice_areas=practice_areas
        )
    return results

# Get corpus info
@app.get("/corpus/{corpus}/info")
async def get_corpus_info(corpus: str):
    return lmdb_store.get_corpus_metadata(corpus)
```

---

## Symlink Behavior Notes

1. **LMDB files are read-only in your app** - All writes happen in ohio_code repo
2. **Symlinks are transparent to Python** - `lmdb.open()` works the same
3. **Changes in ohio_code/dist/ immediately reflect in your app** - No need to restart (LMDB is memory-mapped)
4. **Query logic stays in your app** - lmdb_store.py, main.py, Temporal workflows
5. **Data pipeline stays in ohio_code** - Scraping, enrichment, LMDB building

---

## Disk Space Estimates

| Corpus | Estimated Size | Sections | Notes |
|--------|---------------|----------|-------|
| Ohio Revised | ~500 MB | 23,644 | ✅ Complete |
| Ohio Admin | ~800 MB | ~40,000 | More verbose rules |
| Ohio Constitution | ~5 MB | ~200 | Small corpus |
| Ohio Case Law | ~10 GB | ~500,000 | Large corpus |
| US Code | ~2 GB | ~54,000 | Federal statutes |
| SCOTUS | ~5 GB | ~25,000 | Supreme Court opinions |
| Sixth Circuit | ~8 GB | ~100,000 | Circuit court opinions |

**Total**: ~27 GB for all 35 databases

---

## Next Steps

1. ✅ Ohio Revised Code LMDB built with enrichment
2. ⏳ Copy `auto_enricher.py` and `build_comprehensive_lmdb.py` to other 3 Ohio corpuses
3. ⏳ Run citation analysis + LMDB build for Ohio Admin, Constitution, Case Law
4. ⏳ Create `dist/` folder and move all LMDB outputs there
5. ⏳ Create symlinks in your app repository
6. ⏳ Plan US Code, SCOTUS, Sixth Circuit scraping/enrichment

---

## Verification Commands

```bash
# Check symlinks work
cd your_app/knowledge_service/lmdb_data
ls -la ohio_revised/sections.lmdb  # Should show symlink and file size

# Test LMDB access from Python
python -c "
import lmdb
env = lmdb.open('lmdb_data/ohio_revised/sections.lmdb', readonly=True)
with env.begin() as txn:
    cursor = txn.cursor()
    key, value = next(cursor.iternext())
    print(f'First section: {key.decode()}')
env.close()
"

# Check all corpuses available
python -c "
from pathlib import Path
base = Path('lmdb_data')
corpuses = [d.name for d in base.iterdir() if d.is_dir()]
print(f'Available corpuses: {corpuses}')
"
```

---

## Summary

- **35 LMDB databases** (7 corpuses × 5 databases each)
- **Symlink from your app** to `ohio_code/dist/`
- **Query logic in your app**, data pipeline in ohio_code
- **Enrichment metadata** in all sections for filtering
- **Ready for Temporal workflows** to orchestrate and DeepSeek to infer
- **Visual tree graphs** from chains.lmdb for UX