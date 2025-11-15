from pathlib import Path

# Absolute paths
OHIO_CODE_ROOT = Path("/Users/justinrussell/active_projects/LEGAL/ohio_code/ohio_revised/")
OHIO_CODE_BASE = Path("/Users/justinrussell/active_projects/LEGAL/ohio_code/")

# Data directories
DATA_DIR = OHIO_CODE_ROOT / "src" / "ohio_revised" /  "data"
OHIO_CORPUS_FILE = DATA_DIR / "ohio_revised_code" / "ohio_revised_code_complete.jsonl"

# These will be created when needed
CITATION_ANALYSIS_DIR = DATA_DIR / "citation_analysis"
ENRICHED_OUTPUT_DIR = DATA_DIR / "enriched_output"

# Model path - use absolute path to ohio_code base directory
MODEL_PATH = OHIO_CODE_BASE / "llm_model" / "Meta-Llama-3.1-8B-Instruct-Q8_0.gguf"

# Create output directories if they don't exist
CITATION_ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
ENRICHED_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)