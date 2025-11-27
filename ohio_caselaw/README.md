# Ohio Supreme Court & Courts of Appeals Scraper

This corpus contains opinions from:
- Ohio Supreme Court (Court 0)
- 12 District Courts of Appeals (Courts 1-12)
- Court of Claims (Court 13)
- Miscellaneous (Court 98)

## Data Source

- **Website**: https://www.supremecourt.ohio.gov/rod/docs/
- **Years**: 1992-2025
- **Format**: PDF opinions with metadata

## Directory Structure

```
ohio_scotus/
├── scraper/           # Web scraping code
│   ├── scrape_ohio_scotus.py    # Main scraper
│   └── convert_to_jsonl.py      # Convert metadata to JSONL
├── data/              # Output data
│   └── core/          # JSONL files
├── citation_analysis/ # Citation parsing (TODO)
├── enrichment/        # AI enrichment (TODO)
├── finetuning/        # Model fine-tuning (TODO)
└── lmdb/             # LMDB database (TODO)
```

## Usage

### 1. Run Scraper

```bash
# Test mode (3 downloads)
python3 scrape_ohio_scotus.py test

# Production mode (all cases)
python3 scrape_ohio_scotus.py
```

The scraper will:
- Download PDFs to `/Volumes/Jnice4tb/ohio_scotus/`
- Save metadata to `cases_metadata.json`
- Track progress in `scraper_progress.json`
- Resume from checkpoint if interrupted

### 2. Convert to JSONL

```bash
python3 convert_to_jsonl.py
```

This creates `data/core/ohio_scotus_complete.jsonl` with all case metadata.

## Data Format

Each case entry contains:
```json
{
  "webcite": "2025-Ohio-5169",
  "case_name": "Case Name",
  "topics": "Topic tags",
  "author": "Author/Judge",
  "decided": "Decision date",
  "source": "Court name",
  "year": 1995,
  "pdf_url": "https://...",
  "pdf_path": "/Volumes/Jnice4tb/ohio_scotus/..."
}
```

## Progress Tracking

The scraper maintains checkpoints:
- **Completed Queries**: Tracks which court/year combinations are done
- **Downloaded Cases**: Tracks which PDFs have been downloaded (with SHA256 hashes)
- **Resume Support**: Can be stopped/restarted without re-downloading

## Rate Limiting

- 1 second between page requests
- 2 seconds between PDF downloads

## Status

- ✅ Scraper implemented and tested
- ✅ JSONL conversion working
- ⏳ Production scraping in progress
- ⏳ Citation analysis (TODO)
- ⏳ AI enrichment (TODO)
- ⏳ LMDB database (TODO)

## Next Steps

1. Complete production scraping (all courts, all years)
2. Build citation analysis (case-to-case, case-to-statute references)
3. Implement AI enrichment (summaries, holdings, key issues)
4. Build LMDB database following ohio_revised/ohio_constitution pattern
5. Create inspection tools


# Ohio Case Law JSONL Converter

Two-step conversion process for transforming case law JSON files into JSONL format.

## Structure

Your case law is organized across 20 reporter directories:
```
data/ohio_case_law_raw/pre_filtered_data/
├── ohio/              (Ohio Reports - Supreme Court)
├── ohio-st-2d/        (Ohio State 2d)
├── ohio-st-3d/        (Ohio State 3d)
├── ohio-app/          (Ohio Appellate Reports)
├── ohio-app-2d/       (Ohio Appellate 2d)
├── ohio-app-3d/       (Ohio Appellate 3d)
├── ohio-app-unrep/    (Unreported appellate decisions)
└── ... (13 more reporters)
```

Each contains `extracted/json/*.json` files (50-100 per directory).

## Step 1: Test Conversion

Run the test script first to validate output format on 3 files:

```bash
python test_caselaw_converter.py
```

**What it does:**
- Processes only 3 files from `ohio/` directory
- Creates `data/TEST_OUTPUT.jsonl`
- Shows sample record structure
- Validates extraction logic

**Review the output:**
1. Check JSONL structure is correct
2. Verify citation network (`cites_to` array) is preserved
3. Confirm opinion text extraction works
4. Validate metadata fields

## Step 2: Full Conversion

After validating test output, run the production script:

```bash
python convert_caselaw_full.py
```

**What it does:**
- Recursively processes ALL 20 reporter directories
- Combines everything into single `data/ohio_case_law_complete.jsonl`
- Tracks progress by reporter
- Reports success/error counts
- Shows statistics and samples

**Expected output:**
- ~10,000-50,000+ cases (depends on what you downloaded)
- Single JSONL file with all reporters combined
- Each case includes reporter source for tracking

## Output Format

Each JSONL line contains:

```json
{
  "case_id": 494360,
  "name": "Jesse Keene v. Henry Mould",
  "citation": "16 Ohio 12",
  "decision_date": "1847-12",
  "reporter": "ohio",
  "court_name": "Supreme Court of Ohio",
  "opinion_text": "[MAJORITY - Avert, J.]\nThe plaintiff by this demurrer...",
  "cites_to": [
    {
      "cite": "10 Johns. 161",
      "case_ids": [2136018],
      "case_paths": ["/johns/10/0163-01"],
      "category": "reporters:state",
      "reporter": "Johns."
    }
  ],
  "pagerank_percentile": 0.297,
  "word_count": 1570,
  "citation_count": 7
}
```

## Key Fields Preserved

**Precedent Graph:**
- `cites_to` - Array of all cases cited (builds precedent network)
- `citation_count` - Number of cases this case cites

**Authority Metrics:**
- `pagerank_percentile` - Authority score (0-100, higher = more authoritative)
- `pagerank_raw` - Raw PageRank score

**Court Hierarchy:**
- `court_name` - Full court name
- `reporter` - Which reporter series (tracks court level)

**Opinion Content:**
- `opinion_text` - Full text of all opinions (majority/dissent/concurrence)
- `word_count` - Length of opinion

## Next Steps

After conversion:

1. **Citation Analysis** - Extract precedent graph from `cites_to` arrays
2. **Statute Cross-References** - Find cases citing Ohio Revised Code sections
3. **LMDB Loading** - Load JSONL into memory-mapped database
4. **Authority Ranking** - Use PageRank percentiles for search result ranking

## Differences from Statute Conversion

**Case law is NOT statutes:**
- Cases cite other cases (precedent graph) + statutes
- Multiple opinions per case (majority/dissent/concurrence)
- Authority metrics matter (PageRank for ranking)
- Court hierarchy matters (Supreme > Appeals > Trial)
- No question templates needed (cases don't have structured Q&A)

**Citation extraction needs different regex:**
- Case citations: "123 Ohio St.3d 456" or "Smith v. Jones, 123 Ohio 456"
- Statute citations: "RC 2901.01" or "O.R.C. § 2901.01"
- Extract both types from opinion text