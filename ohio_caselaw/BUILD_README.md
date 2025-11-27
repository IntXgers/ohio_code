# Ohio Case Law LMDB Build - README

## Overview

Complete rewrite of the Ohio Case Law LMDB builder to handle 175,857 cases with proper infrastructure for production builds.

## Files Created

### 1. `auto_enricher_caselaw.py`
- Auto-enrichment system adapted for case law structure
- Generates 7 essential metadata fields without modifying legal text:
  1. **summary** - Plain language case summary from case name
  2. **legal_type** - criminal_case, civil_case, appellate_case
  3. **practice_areas** - Array of relevant practice areas
  4. **complexity** - 1-10 score based on word count, opinions, citations
  5. **key_terms** - Key legal terms extracted from case
  6. **offense_level** - felony, misdemeanor (criminal cases only)
  7. **offense_degree** - F1-F5, M1-M4 (criminal cases only)

### 2. `build_comprehensive_lmdb_new.py`
- Production-grade LMDB builder for 175K+ cases
- All 7 required features implemented

## Key Features Implemented

### 1. Case Law Schema ✅
- **case_id**: Unique case identifier
- **case_name**: Full case name
- **citation**: Official citations
- **decision_date**: Date of decision
- **court**: Court information (name, abbreviation, id)
- **casebody.opinions**: Full opinion text (PRESERVED - exact legal text)
- **judges**, **parties**, **attorneys**: Extracted from casebody
- **enrichment**: 7 auto-generated metadata fields

### 2. Progress Checkpointing ✅
- Saves state every 10,000 cases
- Checkpoint file: `dist/ohio_caselaw/build_progress.pkl`
- Tracks: total_processed, last_case_id, database counts, timestamps

### 3. Resume Capability ✅
- Automatically loads previous progress on startup
- Skips already-processed cases by case_id
- Resume enabled by default: `resume=True`
- Progress file removed on successful completion

### 4. Large Map Size ✅
- **15GB** per database (increased from 2GB)
- 5 databases total = 75GB maximum capacity
- Handles full 175K case corpus with room to grow

### 5. Batch Processing ✅
- **Batch size**: 5,000 cases per batch
- Processes batches sequentially
- Clears batch data from memory after processing
- **Never loads all 175K cases into memory**

### 6. Output Directory ✅
- Outputs to: `/ohio_code/dist/ohio_caselaw/`
- Central distribution folder for all corpuses
- Knowledge service can access via single symlink

### 7. Database Naming ✅
- **primary.lmdb** - Main case database (NOT sections.lmdb)
- **citations.lmdb** - Forward citations
- **reverse_citations.lmdb** - Backward citations
- **chains.lmdb** - Citation chains (reserved for future use)
- **metadata.lmdb** - Corpus metadata

## Data Source

**Location**: `/ohio_caselaw/src/ohio_caselaw/data/pre_enriched_input/jsonl_all/ohio_case_law_complete.jsonl`

**Size**: ~3 GB (2.9 GB)

**Cases**: 175,857 (minus 1 metadata line = 175,856 actual cases)

**Symlink**: Points to `/Volumes/Jnice4tb/Jurist_ohio_corpus/ohio_case_law copy/`

## How to Run

### Standard Build (with resume)
```bash
cd /ohio_code/ohio_caselaw/src/ohio_caselaw/lmdb
python3 build_comprehensive_lmdb_new.py
```

### Fresh Build (ignore previous progress)
Edit line 471:
```python
builder = ComprehensiveLMDBBuilder(DATA_DIR, OUTPUT_DIR, enable_enrichment=True, resume=False)
```

### Disable Enrichment (faster build for testing)
Edit line 471:
```python
builder = ComprehensiveLMDBBuilder(DATA_DIR, OUTPUT_DIR, enable_enrichment=False, resume=True)
```

## Build Process

1. **Initialization**
   - Verifies corpus file exists (175,857 cases)
   - Loads previous progress if resuming
   - Opens 5 LMDB databases with 15GB map_size each

2. **Batch Processing**
   - Reads cases in 5K batches
   - Skips already-processed cases (if resuming)
   - Enriches each case with 7 metadata fields
   - Writes to primary.lmdb
   - Builds citations and reverse citations for batch

3. **Checkpointing**
   - Saves progress every 10K cases
   - If build crashes, resume from last checkpoint
   - Progress includes case_id set to skip duplicates

4. **Finalization**
   - Writes metadata database with corpus info
   - Removes progress file on success
   - Closes all databases

## Expected Output

**Location**: `/ohio_code/dist/ohio_caselaw/`

**Files**:
```
primary.lmdb/           # ~10-15 GB (175K cases with enrichment)
citations.lmdb/         # ~1-2 GB (citation maps)
reverse_citations.lmdb/ # ~1-2 GB (reverse citation maps)
chains.lmdb/            # Reserved for future
metadata.lmdb/          # <1 MB (corpus metadata)
```

## Estimated Build Time

- **With enrichment**: ~2-4 hours (175K cases, 7 fields per case)
- **Without enrichment**: ~30-60 minutes (just database writes)
- **Resume from 50% complete**: ~1-2 hours

## Verification

After build completes, verify:

```bash
# Check database exists
ls -lh /Users/justinrussell/active_projects/LEGAL/ohio_code/dist/ohio_caselaw/

# Check corpus metadata
cd /ohio_code/ohio_caselaw/src/ohio_caselaw/lmdb
python3 inspect_lmdb.py

# Sample query
python3 -c "
import lmdb
import json

env = lmdb.open('/Users/justinrussell/active_projects/LEGAL/ohio_code/dist/ohio_caselaw/metadata.lmdb')
with env.begin() as txn:
    data = txn.get(b'corpus_info')
    print(json.dumps(json.loads(data), indent=2))
"
```

## Troubleshooting

### Build Crashes
- Progress is automatically saved every 10K cases
- Simply re-run `python3 build_comprehensive_lmdb_new.py`
- It will resume from last checkpoint

### Out of Memory
- Batch size is 5K (configurable via `BATCH_SIZE`)
- Memory is cleared after each batch
- Should not exceed ~2-3 GB RAM usage

### Out of Disk Space
- Each database can grow to 15GB
- Total maximum: 75GB (5 databases × 15GB)
- Actual usage: ~15-20GB for 175K cases

### Wrong Data Path
- Verify symlink: `ls -la /ohio_code/ohio_caselaw/src/ohio_caselaw/data/pre_enriched_input/`
- Should point to external drive: `/Volumes/Jnice4tb/Jurist_ohio_corpus/ohio_case_law copy/`

## Schema Alignment

This builder outputs to the standardized schema:
- **primary.lmdb**: Main records with enrichment
- **citations.lmdb**: Forward citation references
- **reverse_citations.lmdb**: Backward citation references
- **chains.lmdb**: Citation chains (future use)
- **metadata.lmdb**: Corpus information

Matches schema for ohio_revised, ohio_admin, ohio_constitution.

## Next Steps

After successful build:

1. **Verify** dist/ohio_caselaw/ contains all 5 databases
2. **Update** knowledge service to access ohio_caselaw corpus
3. **Test** queries against case law LMDB
4. **Document** in DATA_PIPELINE_STATUS.md (4 of 4 corpuses complete)

## Notes

- The old `build_comprehensive_lmdb.py` was a copy of Ohio Revised builder (wrong schema)
- This new builder is case law specific
- All 7 required features from TODO list implemented
- Tested and verified to start correctly
- Ready for production build of 175K cases