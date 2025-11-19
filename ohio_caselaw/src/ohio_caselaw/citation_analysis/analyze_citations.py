#!/usr/bin/env python3
"""
Analyze citations in Ohio case law corpus
Builds citation graph, calculates metrics, and enriches metadata
"""
import json
from pathlib import Path
from typing import Dict, List
from collections import defaultdict
import pickle

from ohio_caselaw.citation_analysis.citation_mapper import get_citation_mapper, Citation
from ohio_caselaw.citation_analysis.ohio_caselaw_mapping import get_mapper

# Configuration
JSONL_INPUT = Path("/Volumes/Jnice4tb/ohio_scotus_caselaw/jsonl/ohio_case_law_complete.jsonl")
OUTPUT_DIR = Path("/Volumes/Jnice4tb/ohio_scotus_caselaw/analysis")
PROGRESS_FILE = OUTPUT_DIR / "citation_analysis_progress.json"

# Output files
CITATION_GRAPH_FILE = OUTPUT_DIR / "citation_graph.pkl"
REVERSE_GRAPH_FILE = OUTPUT_DIR / "reverse_citation_graph.pkl"
ENRICHED_METADATA_FILE = OUTPUT_DIR / "enriched_case_metadata.jsonl"
CITATION_REPORT_FILE = OUTPUT_DIR / "citation_analysis_report.txt"

# Create output directory
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_progress():
    """Load analysis progress"""
    if PROGRESS_FILE.exists():
        try:
            with open(PROGRESS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {'processed_cases': 0, 'total_citations': 0}
    return {'processed_cases': 0, 'total_citations': 0}


def save_progress(progress):
    """Save analysis progress"""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)


def analyze_citations():
    """
    Main analysis pipeline:
    1. Load all cases from JSONL
    2. Extract citations from each case
    3. Build citation graph (forward and reverse)
    4. Calculate citation metrics
    5. Enrich case metadata
    6. Save results
    """
    print("=" * 100)
    print("OHIO CASE LAW CITATION ANALYSIS")
    print("=" * 100)
    print(f"\nInput: {JSONL_INPUT}")
    print(f"Output: {OUTPUT_DIR}\n")

    # Initialize mappers
    citation_mapper = get_citation_mapper()
    court_mapper = get_mapper()

    # Statistics
    stats = {
        'total_cases': 0,
        'total_citations_extracted': 0,
        'citations_from_cites_to': 0,
        'citations_from_text': 0,
        'by_court_type': defaultdict(int),
        'by_year': defaultdict(int),
        'by_citation_type': defaultdict(int),
        'by_relationship': defaultdict(int),
    }

    # Storage for building graphs
    all_cases = []
    citation_graph = {}
    case_metadata = {}

    print("Phase 1: Loading cases and extracting citations...")
    print("-" * 100)

    # Read JSONL line by line
    with open(JSONL_INPUT, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if line_num % 1000 == 0:
                print(f"  Processed {line_num:,} cases...", end='\r')

            try:
                case_data = json.loads(line)
                all_cases.append(case_data)

                case_id = str(case_data.get('id', ''))
                stats['total_cases'] += 1

                # Extract court metadata
                court_meta = court_mapper.get_case_metadata(case_data)
                stats['by_court_type'][court_meta['court_type']] += 1

                year = court_meta.get('decision_year', 'unknown')
                stats['by_year'][year] += 1

                # Extract citations
                cites_to_citations, text_citations = citation_mapper.extract_all_citations(case_data)

                stats['citations_from_cites_to'] += len(cites_to_citations)
                stats['citations_from_text'] += len(text_citations)
                stats['total_citations_extracted'] += len(cites_to_citations) + len(text_citations)

                # Track citation types and relationships
                for citation in text_citations:
                    stats['by_citation_type'][citation.cite_type] += 1
                    stats['by_relationship'][citation.relationship_type] += 1

                # Build citation graph entry
                all_citations = set()
                for citation in cites_to_citations + text_citations:
                    all_citations.add(citation.cited_case)

                citation_graph[case_id] = list(all_citations)

                # Store metadata
                case_metadata[case_id] = court_meta

            except Exception as e:
                print(f"\nERROR processing line {line_num}: {e}")
                continue

    print(f"\n  Completed: {stats['total_cases']:,} cases processed")

    # Phase 2: Build reverse citation graph
    print("\nPhase 2: Building reverse citation graph...")
    print("-" * 100)

    reverse_graph = citation_mapper.build_reverse_citation_graph(citation_graph)
    print(f"  Reverse graph built: {len(reverse_graph):,} cases cited")

    # Phase 3: Calculate citation metrics
    print("\nPhase 3: Calculating citation metrics...")
    print("-" * 100)

    for idx, case_id in enumerate(case_metadata.keys(), 1):
        if idx % 1000 == 0:
            print(f"  Calculated metrics for {idx:,} cases...", end='\r')

        metrics = citation_mapper.calculate_citation_metrics(
            case_id,
            citation_graph,
            reverse_graph
        )

        # Add metrics to case metadata
        case_metadata[case_id].update(metrics)

    print(f"\n  Completed: Metrics calculated for {len(case_metadata):,} cases")

    # Phase 4: Save results
    print("\nPhase 4: Saving results...")
    print("-" * 100)

    # Save citation graphs
    with open(CITATION_GRAPH_FILE, 'wb') as f:
        pickle.dump(citation_graph, f)
    print(f"  ✓ Citation graph saved: {CITATION_GRAPH_FILE}")

    with open(REVERSE_GRAPH_FILE, 'wb') as f:
        pickle.dump(reverse_graph, f)
    print(f"  ✓ Reverse graph saved: {REVERSE_GRAPH_FILE}")

    # Save enriched metadata as JSONL
    with open(ENRICHED_METADATA_FILE, 'w', encoding='utf-8') as f:
        for case_id, metadata in case_metadata.items():
            f.write(json.dumps({'case_id': case_id, **metadata}) + '\n')
    print(f"  ✓ Enriched metadata saved: {ENRICHED_METADATA_FILE}")

    # Phase 5: Generate report
    print("\nPhase 5: Generating analysis report...")
    print("-" * 100)

    # Find most cited cases
    most_cited = sorted(
        [(case_id, len(reverse_graph.get(case_id, [])))
         for case_id in case_metadata.keys()],
        key=lambda x: x[1],
        reverse=True
    )[:50]

    # Find most citing cases
    most_citing = sorted(
        [(case_id, len(citation_graph.get(case_id, [])))
         for case_id in case_metadata.keys()],
        key=lambda x: x[1],
        reverse=True
    )[:50]

    # Generate report
    with open(CITATION_REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write("=" * 100 + "\n")
        f.write("OHIO CASE LAW CITATION ANALYSIS REPORT\n")
        f.write("=" * 100 + "\n\n")

        f.write("SUMMARY STATISTICS\n")
        f.write("-" * 100 + "\n")
        f.write(f"Total cases analyzed: {stats['total_cases']:,}\n")
        f.write(f"Total citations extracted: {stats['total_citations_extracted']:,}\n")
        f.write(f"  From cites_to arrays: {stats['citations_from_cites_to']:,}\n")
        f.write(f"  From opinion text: {stats['citations_from_text']:,}\n\n")

        f.write("CASES BY COURT TYPE\n")
        f.write("-" * 100 + "\n")
        for court_type, count in sorted(stats['by_court_type'].items(), key=lambda x: x[1], reverse=True):
            f.write(f"  {court_type:30s} : {count:>8,} cases\n")

        f.write("\nCASES BY YEAR (Top 20)\n")
        f.write("-" * 100 + "\n")
        sorted_years = sorted(stats['by_year'].items(), key=lambda x: x[0], reverse=True)[:20]
        for year, count in sorted_years:
            f.write(f"  {year}: {count:>8,} cases\n")

        f.write("\nCITATION TYPES\n")
        f.write("-" * 100 + "\n")
        for cite_type, count in sorted(stats['by_citation_type'].items(), key=lambda x: x[1], reverse=True):
            f.write(f"  {cite_type:30s} : {count:>8,} citations\n")

        f.write("\nRELATIONSHIP TYPES\n")
        f.write("-" * 100 + "\n")
        for relationship, count in sorted(stats['by_relationship'].items(), key=lambda x: x[1], reverse=True):
            f.write(f"  {relationship:30s} : {count:>8,} citations\n")

        f.write("\nMOST CITED CASES (Top 50)\n")
        f.write("-" * 100 + "\n")
        for idx, (case_id, citation_count) in enumerate(most_cited, 1):
            meta = case_metadata.get(case_id, {})
            court = meta.get('court_name', 'Unknown')[:50]
            year = meta.get('decision_year', '????')
            f.write(f"  {idx:2d}. [{citation_count:>4,} citations] {case_id:20s} | {year} | {court}\n")

        f.write("\nMOST CITING CASES (Top 50)\n")
        f.write("-" * 100 + "\n")
        for idx, (case_id, citation_count) in enumerate(most_citing, 1):
            meta = case_metadata.get(case_id, {})
            court = meta.get('court_name', 'Unknown')[:50]
            year = meta.get('decision_year', '????')
            f.write(f"  {idx:2d}. [{citation_count:>4,} citations] {case_id:20s} | {year} | {court}\n")

        f.write("\n" + "=" * 100 + "\n")

    print(f"  ✓ Report saved: {CITATION_REPORT_FILE}")

    # Final summary
    print("\n" + "=" * 100)
    print("CITATION ANALYSIS COMPLETE")
    print("=" * 100)
    print(f"\nTotal cases: {stats['total_cases']:,}")
    print(f"Total citations: {stats['total_citations_extracted']:,}")
    print(f"Average citations per case: {stats['total_citations_extracted'] / stats['total_cases']:.2f}")
    print(f"\nOutput directory: {OUTPUT_DIR}")
    print("=" * 100)


if __name__ == "__main__":
    analyze_citations()
