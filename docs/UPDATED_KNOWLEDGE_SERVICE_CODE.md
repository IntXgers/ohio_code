# Updated Knowledge Service Code

## Updated lmdb_store.py

**IMPORTANT**: This file lives in YOUR APP repository, not ohio_code.
ohio_code only produces the LMDB databases. All query logic is in your app.

```python
"""LMDB store for legal code lookups with enrichment support

This module provides a read-only interface to the enriched LMDB databases.
All databases use memory-mapped I/O for ultra-fast lookups.

Architecture:
  - Each corpus (Ohio Revised, Ohio Case Law, etc.) has its own 5 LMDB databases
  - This class manages one corpus at a time
  - Use multiple LMDBStore instances for multiple corpuses
  - This class ONLY does READ operations - no filtering/search logic here
  - Filtering/search logic goes in search_service.py (separate file)

Per-Corpus Databases (5 per corpus):
  - sections.lmdb: Legal sections/opinions with enrichment metadata
  - citations.lmdb: Forward citation references
  - reverse_citations.lmdb: Backward citation references (who cites this)
  - chains.lmdb: Pre-computed citation chains
  - metadata.lmdb: Corpus-level metadata

Key Features:
  - sections.lmdb has enrichment field with 7 metadata fields
  - reverse_citations.lmdb for "who cites this" queries
  - metadata.lmdb for corpus info
  - Works with all corpus types (statutes, case law, admin code, etc.)

Usage:
    # Ohio Revised Code
    ohio_revised = LMDBStore(Path("./lmdb_data/ohio_revised"))
    statute = ohio_revised.get_section("148.01")

    # Ohio Case Law (separate corpus, separate LMDB)
    ohio_cases = LMDBStore(Path("./lmdb_data/ohio_case_law"))
    case = ohio_cases.get_section("2023-Ohio-1234")

    # Get citation chain
    chain = ohio_revised.get_chain("148.01")

    # Get reverse citations (who cites this)
    cited_by = ohio_revised.get_reverse_citations("148.01")

    # For filtering/search, use search_service.py (not this file)
"""
import lmdb
import json
from pathlib import Path
from typing import Optional, List, Dict


class LMDBStore:
    def __init__(self, data_dir: Path):
        """Initialize read-only LMDB environments"""
        self.sections_env = lmdb.open(str(data_dir / "sections.lmdb"), readonly=True, lock=False)
        self.citations_env = lmdb.open(str(data_dir / "citations.lmdb"), readonly=True, lock=False)
        self.reverse_citations_env = lmdb.open(str(data_dir / "reverse_citations.lmdb"), readonly=True, lock=False)
        self.chains_env = lmdb.open(str(data_dir / "chains.lmdb"), readonly=True, lock=False)
        self.metadata_env = lmdb.open(str(data_dir / "metadata.lmdb"), readonly=True, lock=False)

    def get_section(self, section: str) -> Optional[Dict]:
        """Get statute section by number (e.g., '148.01')

        Returns:
            dict with keys:
              - section_number: Section identifier
              - header: Section header with title
              - paragraphs: Full legal text (array of paragraphs)
              - full_text: Concatenated text
              - word_count, paragraph_count, has_citations, citation_count
              - enrichment: Metadata dict with:
                  - summary: Plain language summary
                  - legal_type: criminal_statute, civil_statute, definitional, procedural
                  - practice_areas: List of legal domains
                  - complexity: 1-10 score
                  - key_terms: Important legal terms
                  - offense_level: felony, misdemeanor (criminal only)
                  - offense_degree: F1-F5, M1-M4 (criminal only)
            None if section not found
        """
        with self.sections_env.begin() as txn:
            data = txn.get(section.encode())
            if not data:
                return None
            return json.loads(data.decode())

    def get_citations(self, section: str) -> Optional[Dict]:
        """Get forward citations (what this section references)

        Args:
            section: Section number like "148.01"

        Returns:
            dict with keys:
              - section: Section number
              - direct_references: List of section numbers cited
              - reference_count: Number of citations
              - references_details: List of dicts with section, title, url
            None if no citations found
        """
        with self.citations_env.begin() as txn:
            data = txn.get(section.encode())
            if not data:
                return None
            return json.loads(data.decode())

    def get_reverse_citations(self, section: str) -> Optional[Dict]:
        """Get reverse citations (what sections cite this one)

        Args:
            section: Section number like "148.01"

        Returns:
            dict with keys:
              - section: Section number
              - cited_by: List of section numbers that cite this
              - cited_by_count: Number of sections citing this
              - citing_details: List of dicts with section, title, url
            None if not cited by anything
        """
        with self.reverse_citations_env.begin() as txn:
            data = txn.get(section.encode())
            if not data:
                return None
            return json.loads(data.decode())

    def get_chain(self, section: str) -> Optional[Dict]:
        """Get pre-computed citation chain for a statute

        Citation chains show the full dependency tree of related statutes.

        Args:
            section: Section number like "148.01"

        Returns:
            dict with keys:
              - chain_id: Primary section
              - primary_section: Starting section
              - chain_sections: List of related section numbers
              - chain_depth: Number of sections in chain
              - complete_chain: Full data for each section in chain
            None if no chain exists
        """
        with self.chains_env.begin() as txn:
            data = txn.get(section.encode())
            if not data:
                return None
            return json.loads(data.decode())

    def get_corpus_info(self) -> Dict:
        """Get metadata about the entire corpus

        Returns:
            dict with total_sections, build_date, version, etc.
        """
        with self.metadata_env.begin() as txn:
            data = txn.get(b'corpus_info')
            if not data:
                return {}
            return json.loads(data.decode())

    def get_all_sections(self, limit: Optional[int] = None) -> List[Dict]:
        """Get all sections (or up to limit)

        WARNING: This reads ALL sections into memory. Use with caution.
        For large corpuses, use pagination or iterate with cursor.

        Args:
            limit: Maximum sections to return (None = all)

        Returns:
            List of all section documents
        """
        sections = []

        with self.sections_env.begin() as txn:
            cursor = txn.cursor()
            for key, value in cursor:
                if limit and len(sections) >= limit:
                    break
                sections.append(json.loads(value.decode()))

        return sections

    def close(self):
        """Close all LMDB environments"""
        self.sections_env.close()
        self.citations_env.close()
        self.reverse_citations_env.close()
        self.chains_env.close()
        self.metadata_env.close()
```

---

## search_service.py (Application Logic - Separate File)

**This file lives in YOUR APP, not ohio_code.**
**This is where filtering and search logic belongs.**

```python
"""Search service for filtering and querying LMDB data

This is APPLICATION LOGIC - not data access.
Implements filtering, ranking, and search algorithms.
"""
from typing import List, Dict, Optional
from .lmdb_store import LMDBStore


class SearchService:
    """Search and filter logic for LMDB data"""

    def __init__(self, store: LMDBStore):
        self.store = store

    def search_sections(
        self,
        text: Optional[str] = None,
        legal_type: Optional[str] = None,
        practice_areas: Optional[List[str]] = None,
        offense_level: Optional[str] = None,
        max_complexity: int = 10,
        limit: int = 50
    ) -> List[Dict]:
        """Search sections with enrichment filters

        This is a basic linear scan. For production, consider:
        - Full-text search index (Elasticsearch, Meilisearch)
        - Separate indexes for enrichment fields

        Args:
            text: Search in full_text field (case-insensitive substring)
            legal_type: Filter by legal_type (criminal_statute, civil_statute, etc.)
            practice_areas: Filter by practice areas (must match at least one)
            offense_level: Filter by offense_level (felony, misdemeanor)
            max_complexity: Filter by complexity <= this value
            limit: Maximum results to return

        Returns:
            List of matching section documents (with enrichment)

        Example:
            # Find felony theft statutes
            results = store.search_sections(
                text="theft",
                legal_type="criminal_statute",
                offense_level="felony",
                limit=10
            )
        """
        results = []

        with self.sections_env.begin() as txn:
            cursor = txn.cursor()
            for key, value in cursor:
                if len(results) >= limit:
                    break

                section = json.loads(value.decode())
                enrichment = section.get('enrichment', {})

                # Text search (simple substring - consider upgrading to FTS)
                if text:
                    full_text = section.get('full_text', '').lower()
                    if text.lower() not in full_text:
                        continue

                # Filter by legal_type
                if legal_type and enrichment.get('legal_type') != legal_type:
                    continue

                # Filter by practice_areas (match any)
                if practice_areas:
                    section_areas = enrichment.get('practice_areas', [])
                    if not any(area in section_areas for area in practice_areas):
                        continue

                # Filter by offense_level
                if offense_level and enrichment.get('offense_level') != offense_level:
                    continue

                # Filter by complexity
                if enrichment.get('complexity', 0) > max_complexity:
                    continue

                results.append(section)

        return results

    def autocomplete_search(self, query: str, limit: int = 10) -> List[Dict]:
        """Fast autocomplete search using enrichment summaries

        Searches section numbers, headers, and enrichment summaries.

        Args:
            query: Search query string (minimum 2 characters)
            limit: Maximum results to return (default 10)

        Returns:
            List of matches with type, id, label, and preview fields

        Example:
            results = store.autocomplete_search("theft", limit=5)
            # Returns:
            # [
            #   {
            #     "type": "statute",
            #     "id": "2913.02",
            #     "label": "ORC 2913.02: Theft",
            #     "preview": "Relates to theft of property or services",
            #     "legal_type": "criminal_statute",
            #     "complexity": 4
            #   }
            # ]
        """
        if len(query) < 2:
            return []

        query_lower = query.lower()
        results = []

        with self.sections_env.begin() as txn:
            cursor = txn.cursor()
            for key, value in cursor:
                if len(results) >= limit:
                    break

                section_num = key.decode()
                section = json.loads(value.decode())
                header = section.get('header', '')
                enrichment = section.get('enrichment', {})
                summary = enrichment.get('summary', '')

                # Match section number, header, or summary
                if (query_lower in section_num.lower() or
                    query_lower in header.lower() or
                    query_lower in summary.lower()):

                    results.append({
                        'type': 'statute',
                        'id': section_num,
                        'label': f"ORC {section_num}: {section.get('section_title', '')}",
                        'preview': summary,
                        'legal_type': enrichment.get('legal_type'),
                        'practice_areas': enrichment.get('practice_areas', []),
                        'complexity': enrichment.get('complexity')
                    })

        return results

    def close(self):
        """Close all LMDB environments"""
        self.sections_env.close()
        self.citations_env.close()
        self.reverse_citations_env.close()
        self.chains_env.close()
        self.metadata_env.close()
```

---

## Updated main.py (FastAPI endpoints)

```python
"""Knowledge Service - FastAPI service for Ohio legal data lookups

Updated to support enriched LMDB schema with metadata filtering.

New Features:
  - Search with enrichment filters (legal_type, practice_areas, offense_level, complexity)
  - Reverse citations endpoint (who cites this statute)
  - Enrichment metadata in all responses
  - Better autocomplete using enrichment summaries

Endpoints:
  GET /health - Health check
  GET /sections/{section} - Get section with enrichment
  GET /sections/{section}/citations - Get forward citations
  GET /sections/{section}/reverse-citations - Get reverse citations (NEW)
  GET /sections/{section}/chain - Get citation chain
  GET /search - Search with enrichment filters (NEW)
  GET /autocomplete - Autocomplete with enrichment
  GET /corpus/info - Get corpus metadata (NEW)

Environment Variables:
  LMDB_DATA_DIR - Path to LMDB databases
  PORT - Service port (default: 8001)
  LOG_LEVEL - Logging level (default: info)

Usage:
    uvicorn knowledge_service.main:app --host 0.0.0.0 --port 8001
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import os
import logging
from typing import Optional, List
from .lmdb_store import LMDBStore

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Ohio Legal Knowledge Service",
    description="Fast lookup service for Ohio Revised Code with enrichment metadata",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize LMDB store (SYMLINK TO ohio_code output)
LMDB_DATA_DIR = Path(os.getenv(
    "LMDB_DATA_DIR",
    str(Path(__file__).parent / "ohio_revised_lmdb")  # Symlink here
)).expanduser()

logger.info(f"Initializing LMDB store from: {LMDB_DATA_DIR}")
store = LMDBStore(LMDB_DATA_DIR)
logger.info("LMDB store initialized successfully")


@app.on_event("shutdown")
def shutdown_event():
    """Clean shutdown of LMDB connections"""
    logger.info("Shutting down LMDB store")
    store.close()


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "knowledge-service",
        "version": "2.0.0",
        "lmdb_path": str(LMDB_DATA_DIR)
    }


@app.get("/sections/{section}")
def get_section(section: str):
    """Get Ohio Revised Code section by number (with enrichment)

    Args:
        section: Section number (e.g., "148.01")

    Returns:
        Section document with paragraphs, metadata, and enrichment

    Example:
        GET /sections/2913.02

        Response includes enrichment:
        {
          "section_number": "2913.02",
          "header": "Section 2913.02|Theft",
          "paragraphs": ["legal text..."],
          "enrichment": {
            "summary": "Relates to theft of property",
            "legal_type": "criminal_statute",
            "practice_areas": ["criminal_law"],
            "complexity": 4,
            "offense_level": "felony",
            "offense_degree": "F5"
          }
        }
    """
    logger.info(f"Lookup section: {section}")
    section_data = store.get_section(section)

    if not section_data:
        logger.warning(f"Section not found: {section}")
        raise HTTPException(status_code=404, detail=f"Section {section} not found")

    return section_data


@app.get("/sections/{section}/citations")
def get_section_citations(section: str):
    """Get forward citations (what this section references)

    Args:
        section: Section number (e.g., "148.01")

    Returns:
        Citation data with direct_references and details

    Example:
        GET /sections/2913.02/citations
    """
    logger.info(f"Lookup citations for: {section}")
    citations = store.get_citations(section)

    if not citations:
        # Section exists but has no citations
        return {
            "section": section,
            "direct_references": [],
            "reference_count": 0,
            "references_details": []
        }

    return citations


@app.get("/sections/{section}/reverse-citations")
def get_section_reverse_citations(section: str):
    """Get reverse citations (what sections cite this one)

    NEW ENDPOINT - Shows who references this statute

    Args:
        section: Section number (e.g., "148.01")

    Returns:
        dict with cited_by list and citing_details

    Example:
        GET /sections/2913.01/reverse-citations

        Response shows all sections that cite 2913.01
    """
    logger.info(f"Lookup reverse citations for: {section}")
    reverse_citations = store.get_reverse_citations(section)

    if not reverse_citations:
        return {
            "section": section,
            "cited_by": [],
            "cited_by_count": 0,
            "citing_details": []
        }

    return reverse_citations


@app.get("/sections/{section}/chain")
def get_section_chain(section: str):
    """Get pre-computed citation chain

    Returns full chain with all section data for tree visualization

    Args:
        section: Section number (e.g., "148.01")

    Returns:
        Citation chain with complete_chain containing all section data

    Example:
        GET /sections/2913.02/chain

        Use complete_chain for tree visualization
    """
    logger.info(f"Lookup chain for: {section}")
    chain = store.get_chain(section)

    if not chain:
        logger.warning(f"Chain not found: {section}")
        raise HTTPException(status_code=404, detail=f"Chain for {section} not found")

    return chain


@app.get("/search")
def search_sections(
    text: Optional[str] = Query(None, description="Search text in statute content"),
    legal_type: Optional[str] = Query(None, description="Filter by legal type (criminal_statute, civil_statute, definitional, procedural)"),
    practice_areas: Optional[List[str]] = Query(None, description="Filter by practice areas (criminal_law, family_law, etc.)"),
    offense_level: Optional[str] = Query(None, description="Filter by offense level (felony, misdemeanor)"),
    max_complexity: int = Query(10, ge=1, le=10, description="Maximum complexity (1-10)"),
    limit: int = Query(50, ge=1, le=100, description="Maximum results")
):
    """Search sections with enrichment filters

    NEW ENDPOINT - Enables focused searches using metadata

    Args:
        text: Search in full statute text
        legal_type: Filter by statute type
        practice_areas: Filter by legal domains (can specify multiple)
        offense_level: Filter criminal statutes by level
        max_complexity: Show only statutes with complexity <= this
        limit: Maximum results

    Returns:
        List of matching sections with enrichment

    Examples:
        # Find felony theft statutes
        GET /search?text=theft&legal_type=criminal_statute&offense_level=felony

        # Find simple criminal statutes
        GET /search?legal_type=criminal_statute&max_complexity=3

        # Find family law statutes
        GET /search?practice_areas=family_law&limit=20
    """
    logger.info(f"Search sections: text={text}, legal_type={legal_type}, practice_areas={practice_areas}")

    results = store.search_sections(
        text=text,
        legal_type=legal_type,
        practice_areas=practice_areas,
        offense_level=offense_level,
        max_complexity=max_complexity,
        limit=limit
    )

    return {
        "query": {
            "text": text,
            "legal_type": legal_type,
            "practice_areas": practice_areas,
            "offense_level": offense_level,
            "max_complexity": max_complexity
        },
        "results": results,
        "count": len(results)
    }


@app.get("/autocomplete")
def autocomplete(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(10, ge=1, le=50)
):
    """Autocomplete search with enrichment metadata

    Searches section numbers, headers, and enrichment summaries

    Args:
        q: Search query (minimum 2 characters)
        limit: Maximum results (1-50, default 10)

    Returns:
        List of matches with enrichment preview

    Example:
        GET /autocomplete?q=theft&limit=5

        Returns results with summary, legal_type, complexity in preview
    """
    logger.info(f"Autocomplete search: {q}")
    results = store.autocomplete_search(q, limit)

    return {
        "query": q,
        "results": results,
        "count": len(results)
    }


@app.get("/corpus/info")
def get_corpus_info():
    """Get metadata about the corpus

    NEW ENDPOINT - Shows corpus statistics and build info

    Returns:
        dict with total_sections, build_date, version, enrichment status

    Example:
        GET /corpus/info
    """
    info = store.get_corpus_info()
    return info


@app.get("/")
def root():
    """Root endpoint with service information"""
    return {
        "service": "Ohio Legal Knowledge Service",
        "version": "2.0.0",
        "features": [
            "Enrichment metadata (7 fields per section)",
            "Search with practice area, legal type, complexity filters",
            "Forward and reverse citations",
            "Citation chain visualization data",
            "Fast autocomplete with enrichment"
        ],
        "endpoints": {
            "health": "/health",
            "sections": "/sections/{section}",
            "citations": "/sections/{section}/citations",
            "reverse_citations": "/sections/{section}/reverse-citations",
            "chains": "/sections/{section}/chain",
            "search": "/search?text=...&legal_type=...&practice_areas=...&offense_level=...&max_complexity=...",
            "autocomplete": "/autocomplete?q={query}&limit={limit}",
            "corpus_info": "/corpus/info"
        }
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
```

---

## Setup Instructions

### 1. Symlink LMDB to Knowledge Service
```bash
cd your_app/knowledge_service/
ln -s /path/to/ohio_code/ohio_revised/src/ohio_revised/data/enriched_output/comprehensive_lmdb ohio_revised_lmdb

# Verify
ls -la ohio_revised_lmdb/
# Should show: sections.lmdb, citations.lmdb, etc.
```

### 2. Update Environment Variable
```bash
# In knowledge_service/.env or docker-compose
LMDB_DATA_DIR=./ohio_revised_lmdb
```

### 3. Test Endpoints
```bash
# Health check
curl http://localhost:8001/health

# Get section with enrichment
curl http://localhost:8001/sections/2913.02

# Search with filters
curl "http://localhost:8001/search?text=theft&legal_type=criminal_statute&offense_level=felony"

# Get chain for tree visualization
curl http://localhost:8001/sections/2913.02/chain
```