# Pipeline Modifications for 30B Model Integration

## Critical Files Requiring Updates

### 1. enricher.py - Model Configuration
```python
# REPLACE this section in _init_model():
def _init_model(self):
    """Initialize the 30B language model for enhanced processing"""
    logger.info("Loading Llama 3 30B model...")
    try:
        self.model = Llama(
            model_path="/data/models/legal-ai/llama3-30b-instruct.q4_k_m.gguf",  # UPDATE PATH
            n_ctx=16384,          # INCREASED from 4096
            n_threads=16,         # Adjust based on CPU cores
            n_gpu_layers=60,      # Full GPU utilization
            verbose=False,
            seed=42
        )
        logger.info("30B model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load 30B model: {e}")
        raise
```

### 2. Complex Chain Processing Addition
```python
# ADD this method to RobustEnricher class:
def _process_complex_chain(self, chain_sections: List[Dict]) -> Optional[Dict]:
    """Process interdependent sections with full context"""
    if len(chain_sections) == 1:
        return self._process_document(chain_sections[0])
    
    # Build comprehensive context for all sections
    primary_doc = chain_sections[0]
    context_sections = []
    
    for doc in chain_sections[1:]:
        section_num = self._extract_section_number(doc.get('header', ''))
        context_sections.append({
            'section': section_num,
            'header': doc.get('header', ''),
            'content': '\n'.join(doc.get('paragraphs', []))
        })
    
    # Generate enhanced prompt with full relational context
    enhanced_prompt = self._build_relational_prompt(primary_doc, context_sections)
    
    # Process with expanded context window
    return self._generate_relational_qa(enhanced_prompt, primary_doc)
```

### 3. Citation Integration Requirements
```python
# MODIFY existing _process_document method to use citation analysis:
def _process_document(self, doc: Dict) -> Optional[Dict]:
    section_num = self._extract_section_number(doc.get('header', ''))
    
    # Load citation analysis results
    if hasattr(self, 'citation_map') and section_num in self.citation_map:
        referenced_sections = self.citation_map[section_num]
        
        if len(referenced_sections) >= 3:  # Complex chain threshold
            # Build chain from citation analysis
            chain = self._build_section_chain(section_num, referenced_sections)
            return self._process_complex_chain(chain)
    
    # Standard processing for isolated sections
    return super()._process_document(doc)
```

## New Configuration Requirements

### Model Download Commands
```bash
# Execute these commands after workstation setup:
huggingface-cli download microsoft/Llama-3-30B-Instruct-GGUF --local-dir /data/models/legal-ai/
```

### Environment Variables
```bash
# Add to ~/.bashrc or environment configuration:
export CUDA_VISIBLE_DEVICES=0
export LLAMA_CPP_BATCH_SIZE=2048
export LLAMA_CPP_N_THREADS=16
```

## Integration Testing Checklist

### Performance Validation
- [ ] Model loads within 5 minutes
- [ ] Context window handles 16K+ tokens
- [ ] Inference completes within 90 seconds per chain
- [ ] Memory usage stays below 50GB

### Quality Validation  
- [ ] Complex chain processing generates 6+ QA pairs
- [ ] Cross-reference questions produce coherent answers
- [ ] Validation success rate >70%
- [ ] Output quality subjectively superior to 7B results

### Production Readiness
- [ ] State management functions with complex chains
- [ ] Error handling for memory overflow scenarios
- [ ] Checkpoint system compatible with longer processing times
- [ ] Output format consistent with existing training data

## Expected Processing Timeline

### With 30B Model Configuration
- **Complex chains**: 294 chains × 90 seconds = ~7.5 hours
- **Simple chains**: ~200 chains × 60 seconds = ~3.5 hours  
- **Isolated sections**: 7,215 sections × 30 seconds = ~60 hours
- **Total estimated time**: 71 hours (3 days continuous processing)

### Quality Targets
- **Overall weighted quality**: 8.2/10
- **Complex chain improvement**: 3.4/10 → 8.2/10
- **Training data volume**: 180K+ high-quality QA pairs
- **Attorney-grade accuracy**: >90% validation pass rate