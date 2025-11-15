import json
import os
from llama_cpp import Llama
import logging
from typing import Dict, List, Any

# Set up logging for debugging and monitoring
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# File paths and configuration
INPUT_FILE = "/Users/justinrussell/lawscraper/revised-code/training_datasets/raw/title-001.json"
OUTPUT_BASE = "ohio_legal_enriched"
OUTPUT_FILE = f"/Users/justinrussell/lawscraper/revised-code/training_datasets/{OUTPUT_BASE}.jsonl"
MODEL_PATH = "/Users/justinrussell/mistral7b"

# Initialize the local Mistral 7B model using llama-cpp-python
try:
    llm = Llama(model_path=MODEL_PATH, n_ctx=4096, n_threads=4, verbose=False)
    logger.info("Model loaded successfully.")
except Exception as e:
    logger.error(f"Failed to load model: {e}")
    raise

def create_prompt(header: str, paragraphs: List[str]) -> str:
    """
    Create a prompt for the LLM based on the header and paragraphs.
    """
    content = "\n- " + "\n- ".join(paragraphs)
    prompt = f"""
Generate enriched training data for the following legal content in three styles: Instruction, Q&A, and Chat/Analysis.

Header: {header}
Content: {content}

Format the output as a JSON object with keys 'instruction', 'qa', and 'chat_analysis'. Ensure the response is valid JSON.
"""
    return prompt

def generate_enriched_data(prompt: str) -> Dict[str, Any]:
    """
    Generate enriched training data using the local Mistral 7B model.
    Retries up to 3 times if the output is not valid JSON.
    """
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = llm(prompt, max_tokens=2000, temperature=0.7, stop=["\n\n\n"])
            response_text = response['choices'][0]['text'].strip()
            # Clean up potential JSON formatting issues
            response_text = response_text.replace("```json", "").replace("```", "").strip()
            enriched_data = json.loads(response_text)
            if all(key in enriched_data for key in ["instruction", "qa", "chat_analysis"]):
                return enriched_data
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON from model output (attempt {attempt+1}/{max_retries}): {e}")
        except Exception as e:
            logger.warning(f"Error generating enriched data (attempt {attempt+1}/{max_retries}): {e}")

    logger.error("Failed to generate valid enriched data after retries. Returning empty structure.")
    return {
        "instruction": {"prompt": "", "response": "Error: Could not generate data."},
        "qa": {"question": "", "answer": "Error: Could not generate data."},
        "chat_analysis": {"chat": "Error: Could not generate data."}
    }

def process_jsonl_file(input_file: str, output_file: str):
    """
    Read input JSONL file, process each line with the LLM, and write enriched data to output JSONL file.
    """
    processed_count = 0
    error_count = 0

    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', encoding='utf-8') as outfile:
        for line in infile:
            try:
                # Parse the input JSON object
                data = json.loads(line.strip())
                header = data.get("header", "")
                paragraphs = data.get("paragraphs", [])

                if not header or not paragraphs:
                    logger.warning(f"Skipping entry with missing header or paragraphs: {data.get('url', 'Unknown URL')}")
                    error_count += 1
                    continue

                logger.info(f"Processing entry: {header}")

                # Create prompt and generate enriched data
                prompt = create_prompt(header, paragraphs)
                enriched_data = generate_enriched_data(prompt)

                # Combine original data with enriched data
                output_data = {
                    "url": data["url"],
                    "header": data["header"],
                    "paragraphs": data["paragraphs"],
                    "url_hash": data["url_hash"],
                    "enriched_data": enriched_data
                }

                # Write to output JSONL file
                json.dump(output_data, outfile, ensure_ascii=False)
                outfile.write('\n')
                processed_count += 1

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse input JSON line: {line[:50]}... Error: {e}")
                error_count += 1
            except Exception as e:
                logger.error(f"Unexpected error processing line: {line[:50]}... Error: {e}")
                error_count += 1

    logger.info(f"Processing complete. Successfully processed: {processed_count}, Errors: {error_count}")

def main():
    """
    Main function to execute the enrichment process.
    """
    try:
        logger.info(f"Starting enrichment process. Input: {INPUT_FILE}, Output: {OUTPUT_FILE}")
        process_jsonl_file(INPUT_FILE, OUTPUT_FILE)
        logger.info("Enrichment process completed successfully.")
    except Exception as e:
        logger.error(f"Failed to complete enrichment process: {e}")
        raise

if __name__ == "__main__":
    main()
