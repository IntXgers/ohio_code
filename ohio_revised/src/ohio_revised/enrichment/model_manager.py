#!/usr/bin/env python3
"""
Title context analyzer for Ohio Revised Code
Generates context for template creation
"""

import json
import lmdb
from llama_cpp import Llama
from collections import Counter


class ContextAgent:
    def __init__(self):
        # Hardcoded paths
        self.model = Llama(
            model_path="/Users/justinrussell/ohio_code/llm_model/Meta-Llama-3.1-8B-Instruct-Q8_0.gguf",
            n_ctx=8192,
            n_threads=8,
            n_gpu_layers=-1,
            verbose=False
        )
        self.conversation_history = []
        self.context = None

        # Load citation map
        # Separate statements - cleaner and easier to debug
        with open('/Users/justinrussell/ohio_code/ohio_revised/data/citation_analysis/citation_map.json', 'r') as f:
            self.citation_map = json.load(f)

        with open('/Users/justinrussell/ohio_code/ohio_revised/data/citation_analysis/citation_analysis.json',
                  'r') as f:
            self.citation_analysis = json.load(f)

        # For JSONL (line by line)
        with open('/Users/justinrussell/ohio_code/ohio_revised/data/citation_analysis/complex_chains.jsonl', 'r') as f:
            self.complex_chains = [json.loads(line) for line in f]

        with open(
                '/Users/justinrussell/ohio_code/ohio_revised/data/pre_enriched_input/ohio_revised_code_complete.jsonl',
                'r') as f:
            self.ohio_code = [json.loads(line) for line in f]


        # Load LMDB
        self.env = lmdb.open('/Users/justinrussell/ohio_code/ohio_revised/data/enriched_output/sections.lmdb')



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


# Run for all titles
if __name__ == "__main__":
    analyzer = TitleContextAnalyzer()

    # Ohio titles (odd numbers mostly)
    titles = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31, 33, 35, 37, 39, 41, 43, 45, 47, 49, 51, 53, 55,
              57, 58, 59, 61, 63]

    for title in titles:
        try:
            analyzer.analyze_title(title)
        except Exception as e:
            print(f"Error on title {title}: {e}")