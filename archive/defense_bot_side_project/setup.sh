#!/bin/bash
# Defense Attorney Bot - Complete Setup and Training Pipeline
# Run this script to set up and train your defense attorney bot

set - e  # Exit on error

echo
"🚀 Defense Attorney Bot Setup"
echo
"============================="

# Colors for output
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
NC = '\033[0m'  # No Color

# Configuration
PROJECT_DIR = "defense-attorney-bot"
PYTHON_VERSION = "3.10"
VENV_NAME = "venv"

# Function to print colored output
print_status()
{
    echo - e
"${GREEN}[✓]${NC} $1"
}

print_warning()
{
    echo - e
"${YELLOW}[!]${NC} $1"
}

print_error()
{
    echo - e
"${RED}[✗]${NC} $1"
}

# Check system requirements
check_requirements()
{
    echo
"Checking system requirements..."

# Check Python
if ! command - v
python3 & > / dev / null;
then
print_error
"Python 3 not found. Please install Python 3.10+"
exit
1
fi

# Check CUDA (for GPU training)
if command - v
nvidia - smi & > / dev / null;
then
print_status
"NVIDIA GPU detected"
nvidia - smi - -query - gpu = name, memory.total - -format = csv, noheader
else
print_warning
"No NVIDIA GPU detected. Training will be slower on CPU"
fi

# Check disk space (need at least 100GB for models and data)
available_space =$(df - BG. | awk 'NR==2 {print $4}' | sed 's/G//')
if ["$available_space" - lt 100];
then
print_warning
"Less than 100GB disk space available. You may need more space for large models"
else
print_status
"Sufficient disk space available: ${available_space}GB"
fi
}

# Create project structure
setup_project_structure()
{
    echo - e
"\nSetting up project structure..."

mkdir - p $PROJECT_DIR / {data / {raw, enriched, training}, models / {base, checkpoints},
                          scripts / {enrichment, training, evaluation}, configs, logs}

cd $PROJECT_DIR

# Create .gitignore
cat >.gitignore << 'EOF'
# Python
__pycache__ /
*.py[cod]
  *$py.


class
    *.so

.Python
env /
venv /
ENV /
.venv

# Models (too large for git)
models / base / *.gguf
models / base / *.bin
models / checkpoints /

# Data
data / raw / *.jsonl
data / enriched /
data / training /

# Logs
logs /
*.log

# Checkpoints
checkpoints /
*.ckpt

# IDE
.vscode /
.idea /
*.swp

# OS
.DS_Store
Thumbs.db

# Weights & Biases
wandb /
EOF

print_status
"Project structure created"
}

# Setup Python environment
setup_python_env()
{
echo - e
"\nSetting up Python environment..."

# Create virtual environment
python3 - m
venv $VENV_NAME

# Activate virtual environment
source $VENV_NAME / bin / activate

# Upgrade pip
pip
install - -upgrade
pip

# Install requirements
cat > requirements.txt << 'EOF'
# Core ML libraries
torch >= 2.0
.0
transformers >= 4.35
.0
datasets >= 2.14
.0
accelerate >= 0.24
.0
peft >= 0.6
.0
bitsandbytes >= 0.41
.0

# LLM inference
llama - cpp - python >= 0.2
.0

# Data processing
pandas >= 2.0
.0
numpy >= 1.24
.0
tqdm >= 4.65
.0
pyyaml >= 6.0

# Logging and monitoring
wandb >= 0.15
.0
tensorboard >= 2.13
.0

# Legal text processing
spacy >= 3.6
.0
nltk >= 3.8
.0

# Development tools
jupyter >= 1.0
.0
ipython >= 8.14
.0
black >= 23.0
.0
pytest >= 7.4
.0

# Additional utilities
fire >= 0.5
.0
rich >= 13.5
.0
python - dotenv >= 1.0
.0
EOF

print_status
"Installing Python packages..."
pip
install - r
requirements.txt

# Install spaCy model for legal text
python - m
spacy
download
en_core_web_sm

print_status
"Python environment ready"
}

# Download sample model
download_models()
{
echo - e
"\nModel setup instructions..."

cat > models / README.md << 'EOF'
# Model Setup

## Base Models

For
the
enrichment
phase, download
one
of
these
GGUF
models:

### Option 1: Mistral 7B Instruct (Recommended for start)
```bash
cd
models / base
wget
https: // huggingface.co / TheBloke / Mistral - 7
B - Instruct - v0
.2 - GGUF / resolve / main / mistral - 7
b - instruct - v0
.2.Q4_K_M.gguf
```

### Option 2: Mixtral 8x7B (Better quality, needs more RAM)
```bash
cd
models / base
wget
https: // huggingface.co / TheBloke / Mixtral - 8
x7B - Instruct - v0
.1 - GGUF / resolve / main / mixtral - 8
x7b - instruct - v0
.1.Q4_K_M.gguf
```

### Option 3: DeepSeek 33B (Best for structured output)
```bash
cd
models / base
wget
https: // huggingface.co / TheBloke / deepseek - coder - 33
B - instruct - GGUF / resolve / main / deepseek - coder - 33
b - instruct.Q4_K_M.gguf
```

## For Fine-tuning

The
fine - tuning
script
will
automatically
download
models
from HuggingFace.

Recommended
base
models
for fine - tuning:

- mistralai / Mistral - 7
B - Instruct - v0
.2
- meta - llama / Llama - 2 - 7
b - chat - hf(requires
access
approval)
- NousResearch / Nous - Hermes - 2 - Mixtral - 8
x7B - DPO
EOF

print_status
"Model download instructions created in models/README.md"
}

# Create configuration files
create_configs()
{
echo - e
"\nCreating configuration files..."

# Enrichment config
cat > configs / enrichment_config.yaml << 'EOF'
# Defense Attorney Bot - Enrichment Configuration

model:
path: "models/base/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
context_length: 8192
threads: 8
gpu_layers: -1  # Use all GPU layers

processing:
batch_size: 10
max_retries: 3
temperature: 0.3  # Lower for consistent JSON output
max_tokens: 2000
num_workers: 1  # Increase for parallel processing

paths:
input_file: "data/raw/ohio_revised_code_complete.jsonl"
case_law_dir: "data/raw/case_law"
output_dir: "data/enriched"
checkpoint_dir: "checkpoints"

defense_focus:
include_scenarios: true
include_constitutional: true
include_evidence: true
include_jury: true
include_negotiation: true
include_cross_examination: true

# Weights for different types of enrichment
enrichment_weights:
defense_scenarios: 1.0
constitutional_analysis: 0.8
evidence_challenges: 0.9
jury_strategy: 0.7
negotiation_strategy: 0.8
cross_examination: 0.9
EOF

# Fine-tuning config
cat > configs / finetune_config.yaml << 'EOF'
# Defense Attorney Bot - Fine-tuning Configuration

model_name: "mistralai/Mistral-7B-Instruct-v0.2"
data_dir: "data/enriched/stage_1_statutory"
output_dir: "models/defense-attorney-v1"

# Training parameters
num_epochs: 3
batch_size: 4
learning_rate: 0.0002
warmup_steps: 100
gradient_accumulation_steps: 4
gradient_checkpointing: true
max_length: 2048

# LoRA configuration
use_quantization: true
lora_r: 16
lora_alpha: 32
lora_dropout: 0.1
target_modules: ["q_proj", "v_proj", "k_proj", "o_proj"]

# Optimization
optimizer: "paged_adamw_8bit"
weight_decay: 0.01
max_grad_norm: 0.3

# Evaluation
eval_steps: 500
save_steps: 500
logging_steps: 10

# Monitoring
use_wandb: false
wandb_project: "defense-attorney-bot"

# Hardware
fp16: true
device_map: "auto"
EOF

print_status
"Configuration files created"
}

# Create helper scripts
create_helper_scripts()
{
echo - e
"\nCreating helper scripts..."

# Data preparation script
cat > scripts / prepare_data.py << 'EOF'
# !/usr/bin/env python3
"""Prepare and validate data for training"""

import json
from pathlib import Path
import logging
from typing import Dict, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def validate_jsonl(file_path: str) -> tuple[int, int]:
    """Validate JSONL file and return (valid_count, error_count)"""
    valid_count = 0
    error_count = 0

    with open(file_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            try:
                data = json.loads(line.strip())
                # Check required fields
                if 'header' in data and 'paragraphs' in data:
                    valid_count += 1
                else:
                    logger.warning(f"Line {i + 1}: Missing required fields")
                    error_count += 1
            except json.JSONDecodeError as e:
                logger.error(f"Line {i + 1}: JSON decode error: {e}")
                error_count += 1

    return valid_count, error_count


def main():
    # Validate input data
    input_file = "data/raw/ohio_revised_code_complete.jsonl"
    if Path(input_file).exists():
        valid, errors = validate_jsonl(input_file)
        logger.info(f"Input file: {valid} valid entries, {errors} errors")
    else:
        logger.error(f"Input file not found: {input_file}")


if __name__ == "__main__":
    main()
EOF

# Evaluation script
cat > scripts / evaluate_model.py << 'EOF'
# !/usr/bin/env python3
"""Evaluate the fine-tuned defense attorney model"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_model(model_path: str):
    """Load fine-tuned model for evaluation"""
    logger.info(f"Loading model from {model_path}")

    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.bfloat16,
        device_map="auto"
    )

    return model, tokenizer


def evaluate_response(model, tokenizer, prompt: str, max_length: int = 512):
    """Generate and evaluate model response"""
    inputs = tokenizer(prompt, return_tensors="pt")

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_length=max_length,
            temperature=0.7,
            do_sample=True,
            top_p=0.9
        )

    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response


def run_test_cases():
    """Run standard test cases"""
    test_cases = [
        "I was pulled over and the officer searched my car without asking. What are my options?",
        "I'm charged with possession but the drugs weren't mine. How do I defend this?",
        "The prosecution offered a plea deal. Should I take it or go to trial?",
        "What constitutional issues can I raise in an OVI case?",
        "How do I challenge the credibility of a confidential informant?"
    ]

    model_path = "models/defense-attorney-v1"
    model, tokenizer = load_model(model_path)

    for i, test in enumerate(test_cases, 1):
        logger.info(f"\nTest Case {i}: {test}")
        response = evaluate_response(model, tokenizer, test)
        logger.info(f"Response: {response}\n")


if __name__ == "__main__":
    run_test_cases()
EOF

chmod + x
scripts / prepare_data.py
chmod + x
scripts / evaluate_model.py

print_status
"Helper scripts created"
}

# Create run scripts
create_run_scripts()
{
echo - e
"\nCreating run scripts..."

# Main run script
cat > run_enrichment.sh << 'EOF'
# !/bin/bash
# Run the enrichment pipeline

source
venv / bin / activate

echo
"🚀 Starting Defense Attorney Bot Enrichment"
echo
"=========================================="

# Check if model exists
if [ ! -f "models/base/mistral-7b-instruct-v0.2.Q4_K_M.gguf"]; then
echo
"❌ Model not found! Please download it first:"
echo
"cd models/base && wget https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
exit
1
fi

# Check if input data exists
if [ ! -f "data/raw/ohio_revised_code_complete.jsonl"]; then
echo
"❌ Input data not found at data/raw/ohio_revised_code_complete.jsonl"
exit
1
fi

# Run enrichment
python
scripts / enrichment / defense_enricher.py \
- -config
configs / enrichment_config.yaml \
- -input
data / raw / ohio_revised_code_complete.jsonl \
- -model
models / base / mistral - 7
b - instruct - v0
.2.Q4_K_M.gguf

echo
"✅ Enrichment complete!"
EOF

# Fine-tuning run script
cat > run_finetuning.sh << 'EOF'
# !/bin/bash
# Run the fine-tuning pipeline

source
venv / bin / activate

echo
"🚀 Starting Defense Attorney Bot Fine-tuning"
echo
"==========================================="

# Check if enriched data exists
if [ ! -d "data/enriched/stage_1_statutory"]; then
echo
"❌ Enriched data not found! Run enrichment first."
exit
1
fi

# Check GPU
if ! nvidia-smi > / dev / null 2 > & 1; then
echo
"⚠️  No GPU detected. Training will be very slow!"
read - p
"Continue anyway? (y/n) " - n
1 - r
echo
if [[ ! $REPLY =~ ^[Yy]$]]; then
exit
1
fi
fi

# Run fine-tuning
python
scripts / training / fine_tune.py \
- -config - file
configs / finetune_config.yaml

echo
"✅ Fine-tuning complete!"
EOF

chmod + x
run_enrichment.sh
chmod + x
run_finetuning.sh

print_status
"Run scripts created"
}

# Create monitoring script
create_monitoring()
{
echo - e
"\nCreating monitoring tools..."

cat > monitor_training.py << 'EOF'
# !/usr/bin/env python3
"""Monitor training progress"""

import json
from pathlib import Path
import time
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.live import Live

console = Console()


def load_checkpoint(checkpoint_file: str = "checkpoints/defense_enrichment_checkpoint.json"):
    """Load checkpoint data"""
    if Path(checkpoint_file).exists():
        with open(checkpoint_file, 'r') as f:
            return json.load(f)
    return None


def monitor_enrichment():
    """Monitor enrichment progress"""
    with Live(console=console, refresh_per_second=1) as live:
        while True:
            checkpoint = load_checkpoint()

            if checkpoint:
                table = Table(title="Defense Attorney Bot - Enrichment Progress")
                table.add_column("Metric", style="cyan")
                table.add_column("Value", style="green")

                table.add_row("Documents Processed", str(checkpoint['processed_count']))
                table.add_row("Last Update", checkpoint['timestamp'])
                table.add_row("Status", "🟢 Running")

                # Estimate completion
                total_docs = 23654  # Adjust based on your dataset
                if checkpoint['processed_count'] > 0:
                    progress = checkpoint['processed_count'] / total_docs * 100
                    table.add_row("Progress", f"{progress:.1f}%")

                live.update(table)

            time.sleep(1)


if __name__ == "__main__":
    try:
        monitor_enrichment()
    except KeyboardInterrupt:
        console.print("\n[yellow]Monitoring stopped[/yellow]")
EOF

chmod + x
monitor_training.py

print_status
"Monitoring tools created"
}

# Main setup flow
main()
{
echo
"🏛️  Defense Attorney Bot - Complete Setup"
echo
"========================================"
echo

# Check requirements
check_requirements

# Create project structure
setup_project_structure

# Setup Python environment
setup_python_env

# Create all necessary files
create_configs
create_helper_scripts
create_run_scripts
create_monitoring

# Copy the main scripts
echo - e
"\nCopying main scripts..."
cp.. / defense_enricher.py
scripts / enrichment /
cp.. / fine_tune.py
scripts / training /

# Download models info
download_models

# Create README
cat > README.md << 'EOF'
# Defense Attorney Bot 🏛️

A
specialized
AI
assistant
trained
to
think
like
a
criminal
defense
attorney, focusing
on
protecting
client
rights and identifying
defense
strategies.

## Quick Start

1. ** Download
a
model ** (see models / README.md):
```bash
cd
models / base
wget
https: // huggingface.co / TheBloke / Mistral - 7
B - Instruct - v0
.2 - GGUF / resolve / main / mistral - 7
b - instruct - v0
.2.Q4_K_M.gguf
```

2. ** Place
your
data **:
- Put
`ohio_revised_code_complete.jsonl` in `data / raw / `

3. ** Run
enrichment **:
```bash
./ run_enrichment.sh
```

4. ** Monitor
progress ** (in another terminal):
```bash
python
monitor_training.py
```

5. ** Fine - tune
the
model **:
```bash
./ run_finetuning.sh
```

## Project Structure

- `data / ` - Raw and enriched
training
data
- `models / ` - Base
models and fine - tuned
checkpoints
- `scripts / ` - All
processing
scripts
- `configs / ` - Configuration
files
- `logs / ` - Training and processing
logs

## Features

- Constitutional
challenge
identification
- Evidence
suppression
strategies
- Jury
selection
optimization
- Cross - examination
preparation
- Plea
negotiation
tactics
- Motion
practice
templates

## Hardware Requirements

- ** Minimum **: 16
GB
RAM, 6
GB
VRAM
- ** Recommended **: 32
GB
RAM, 24
GB
VRAM(RTX
3090 / 4090)
- ** Storage **: 100
GB +
for models and data

## Training Stages

1. ** Enrichment **: Convert
statutes → defense
scenarios
2. ** Fine - tuning **: Train
model
on
enriched
data
3. ** Evaluation **: Test
on
real
case
scenarios

## License

This
project is
for educational and research purposes only.
EOF

# Final summary
echo
echo
"✅ Setup Complete!"
echo
"=================="
echo
echo
"Next steps:"
echo
"1. Download a model to models/base/ (see models/README.md)"
echo
"2. Copy your ohio_revised_code_complete.jsonl to data/raw/"
echo
"3. Run ./run_enrichment.sh to start enrichment"
echo
"4. Run ./run_finetuning.sh after enrichment completes"
echo
echo
"📁 Project location: $(pwd)"
echo
print_status
"Happy training! 🚀"
}

# Run main setup
main