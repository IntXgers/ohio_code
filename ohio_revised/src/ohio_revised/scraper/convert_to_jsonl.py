import json
from pathlib import Path 


def convert_json_array_to_jsonl (input_file,output_file):
    """
    Converts a JSON array file to JSONL format, keeping only header and paragraphs.
    Each line in the output will be a valid JSON object.
    """

    # Read the JSON array
    with open (input_file,'r',encoding='utf-8') as f:
        data = json.load (f)

    # Write each object as a separate line in JSONL format
    with open (output_file,'w',encoding='utf-8') as f:
        for obj in data:
            # Create new object with only header and paragraphs
            simple_obj = {
                'url': obj.get('url', ''),
                'url_hash': obj.get('url_hash', ''),
                'header':obj.get ('header',''),
                'paragraphs':obj.get ('paragraphs',[])
                }
            # Write as single line JSON (this is JSONL format)
            f.write (json.dumps (simple_obj,ensure_ascii=False) + '\n')

    print (f"Successfully converted {len (data)} objects to JSONL format")
    print (f"Output saved to: {output_file}")

    # Show a sample of the output
    print ("\nSample output (first 2 lines):")
    with open (output_file,'r',encoding='utf-8') as f:
        for i,line in enumerate (f):
            if i < 2:
                print (f"Line {i + 1}: {line.strip () [:100]}...")
            else:
                break


# Example usage
if __name__ == "__main__":
    # Replace these with your actual file names
    input_file = "/Users/justinrussell/active_projects/LEGAL/ohio_code/ohio_revised/src/ohio_revised/data/pre_enriched_input/ohio_revised_code_complete.json"  # Your JSON array file
    output_file = "/Users/justinrussell/active_projects/LEGAL/ohio_code/ohio_revised/src/ohio_revised/data/pre_enriched_input/ohio_revised_code_complete.jsonl"  # Output JSONL file

    convert_json_array_to_jsonl (input_file,output_file)