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