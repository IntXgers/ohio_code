import json
from pathlib import Path
import glob


def convert_json_array_to_jsonl(input_file, output_file):
    """
    Converts a JSON array file to JSONL format, keeping only header and paragraphs.
    Each line in the output will be a valid JSON object.
    """

    # Read the JSON array
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Write each object as a separate line in JSONL format
    with open(output_file, 'w', encoding='utf-8') as f:
        for obj in data:
            # Create new object with only header and paragraphs
            simple_obj = {
                'url': obj.get('url', ''),
                'url_hash': obj.get('url_hash', ''),
                'header': obj.get('header', ''),
                'paragraphs': obj.get('paragraphs', [])
            }
            # Write as single line JSON (this is JSONL format)
            f.write(json.dumps(simple_obj, ensure_ascii=False) + '\n')

    print(f"Successfully converted {len(data)} objects to JSONL format")
    print(f"Output saved to: {output_file}")

    # Show a sample of the output
    print("\nSample output (first 2 lines):")
    with open(output_file, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i < 2:
                print(f"Line {i + 1}: {line.strip()[:100]}...")
            else:
                break


def merge_all_codes_to_jsonl(input_dir, output_file):
    """
    Merges all code-*.json files from the scraped_codes directory into a single JSONL file.

    Args:
        input_dir: Directory containing the code-*.json files
        output_file: Path to the output JSONL file
    """
    input_path = Path(input_dir)

    # Find all code-*.json files
    json_files = sorted(input_path.glob('code-*.json'))

    if not json_files:
        print(f"No code-*.json files found in {input_dir}")
        return

    print(f"Found {len(json_files)} code files to merge")

    total_sections = 0

    # Open output file for writing
    with open(output_file, 'w', encoding='utf-8') as out_f:
        for json_file in json_files:
            print(f"Processing {json_file.name}...")

            try:
                with open(json_file, 'r', encoding='utf-8') as in_f:
                    data = json.load(in_f)

                # Write each section as a JSONL line
                for obj in data:
                    simple_obj = {
                        'url': obj.get('url', ''),
                        'url_hash': obj.get('url_hash', ''),
                        'header': obj.get('header', ''),
                        'paragraphs': obj.get('paragraphs', [])
                    }
                    out_f.write(json.dumps(simple_obj, ensure_ascii=False) + '\n')
                    total_sections += 1

            except Exception as e:
                print(f"  Error processing {json_file.name}: {e}")
                continue

    print(f"\nSuccessfully merged {total_sections} sections from {len(json_files)} files")
    print(f"Output saved to: {output_file}")

    # Show a sample of the output
    print("\nSample output (first 2 lines):")
    with open(output_file, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i < 2:
                print(f"Line {i + 1}: {line.strip()[:100]}...")
            else:
                break


# Example usage
if __name__ == "__main__":
    # Get the base directory
    base_dir = Path(__file__).parent.parent

    # Input directory with all the scraped code files
    input_dir = base_dir / "data" / "scraped_codes"

    # Output file for the complete merged JSONL
    output_file = base_dir / "data" / "ohio_admin_code_complete.jsonl"

    # Merge all code files into a single JSONL file
    merge_all_codes_to_jsonl(input_dir, output_file)