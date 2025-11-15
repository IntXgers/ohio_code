# Workstation Setup Guide - 64GB VRAM Configuration

## Hardware Assembly Checklist

### Components Verification
- [ ] GPU with 64GB VRAM (likely A6000 Ada or H100)
- [ ] Compatible motherboard with PCIe 4.0/5.0 x16 slot
- [ ] Sufficient PSU (1000W+ recommended)
- [ ] Adequate cooling solution
- [ ] 64GB+ system RAM
- [ ] NVMe SSD for model storage (500GB+ recommended)

### Assembly Priority Order
1. **Motherboard and CPU installation**
2. **System RAM installation**
3. **GPU mounting** (ensure proper PCIe power connections)
4. **Storage configuration**
5. **Power supply connections**
6. **Cooling system verification**

## Software Configuration

### CUDA Installation (Critical Path)
```bash
# Ubuntu/Debian
wget https://developer.download.nvidia.com/compute/cuda/12.3/local_installers/cuda_12.3.0_545.23.06_linux.run
sudo sh cuda_12.3.0_545.23.06_linux.run

# Verify installation
nvidia-smi
nvcc --version
```

### Python Environment Setup
```bash
# Create isolated environment for legal AI pipeline
conda create -n legal-ai python=3.11
conda activate legal-ai

# Install dependencies
pip install llama-cpp-python[cuda] --no-cache-dir
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install transformers accelerate
```

### Model Download Preparation
```bash
# Create model storage directory
mkdir -p /data/models/legal-ai
cd /data/models/legal-ai

# Download Llama 3 30B Instruct (GGUF format recommended)
# Size: ~20GB - ensure sufficient disk space
huggingface-cli download microsoft/Llama-3-30B-Instruct-GGUF
```

## Performance Verification Tests

### GPU Memory Test
```python
import torch
print(f"CUDA Available: {torch.cuda.is_available()}")
print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

# Memory allocation test
test_tensor = torch.randn(8000, 8000).cuda()
print("GPU memory allocation successful")
```

### Inference Speed Benchmark
```python
from llama_cpp import Llama

# Test configuration
model = Llama(
    model_path="/data/models/legal-ai/llama3-30b-instruct.q4_k_m.gguf",
    n_ctx=16384,
    n_gpu_layers=60,
    verbose=True
)

# Benchmark prompt
start_time = time.time()
response = model("Test legal reasoning prompt", max_tokens=100)
inference_time = time.time() - start_time

print(f"Inference time: {inference_time:.2f} seconds")
print(f"Tokens per second: {100/inference_time:.1f}")
```

## Integration Points

### Existing Pipeline Modifications Required
1. **enricher.py**: Update model initialization parameters
2. **Context window**: Increase from 4096 to 16384 tokens
3. **Batch size**: Adjust for 64GB VRAM capacity
4. **Validation**: Ensure quality improvements are measurable

### File Paths to Update
- Model path configuration in enricher.py
- Output directory paths for enhanced training data
- State file locations for new processing runs

## Success Criteria
- [ ] GPU recognized and CUDA functional
- [ ] 30B model loads successfully in <5 minutes
- [ ] Inference speed: <90 seconds per complex chain
- [ ] Memory utilization: <45GB during processing
- [ ] Quality validation: >8.0/10 on sample chains