#!/usr/bin/env python3
"""
Title context analyzer for Ohio Revised Code
Generates context for template creation
"""

import json
import lmdb
from llama_cpp import Llama
from collections import Counter


class ModelManager:
    def __init__(self):
        # Hardcoded paths
        self.model = Llama(
            model_path="/Users/justinrussell/ohio_code/llm_model/Meta-Llama-3.1-8B-Instruct-Q8_0.gguf",
            n_ctx=8192,
            n_threads=8,
            n_gpu_layers=-1,
            verbose=False
        )

        # Load citation map
        with open('/Users/justinrussell/ohio_code/ohio_revised/data/citation_analysis/citation_map.json', 'r') as f:
            self.citation_map = json.load(f)

        # Load LMDB
        self.env = lmdb.open('/Users/justinrussell/ohio_code/ohio_revised/data/enriched_output/sections.lmdb')

    def analyze_title(self, title_num):
        # Get all sections for this title
        title_sections = {}
        for section, refs in self.citation_map.items():
            if section.startswith(str(title_num)):
                title_sections[section] = refs

        # Find most referenced sections
        all_refs = []
        for refs in title_sections.values():
            all_refs.extend(refs)
        ref_counts = Counter(all_refs)
        top_refs = ref_counts.most_common(10)

        # Get sample text from key sections
        samples = []
        with self.env.begin() as txn:
            for section in list(title_sections.keys())[:5]:
                data = txn.get(section.encode())
                if data:
                    doc = json.loads(data.decode())
                    text = '\n'.join(doc.get('paragraphs', []))[:1500]
                    samples.append(f"Section {section}:\n{text}\n")

        # Analyze with model
        prompt = f"""Analyze Ohio Revised Code Title {title_num}:

Total sections: {len(title_sections)}
Most referenced: {top_refs}

Sample sections:
{''.join(samples)}

Provide:
1. Main legal areas covered
2. Common requirement types
3. Key concepts and terms
4. Enforcement mechanisms
5. Typical penalties or consequences
6. Cross-reference patterns
"""

        response = self.model(prompt, max_tokens=2000)

        # Save results
        output = {
            'title': title_num,
            'sections': len(title_sections),
            'top_references': top_refs,
            'analysis': response['choices'][0]['text']
        }

        # Write to file
        with open(f'/Users/justinrussell/ohio_code/title_{title_num}_context.json', 'w') as f:
            json.dump(output, f, indent=2)

        print(f"Title {title_num}: {len(title_sections)} sections analyzed")
        return output

