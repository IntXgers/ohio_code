import json


def transform_json_to_jsonl (input_file_path,output_file_path):
    """
    Simple transformation: JSON array to JSONL format.

    Takes each object with header + paragraphs array and creates
    one JSONL line with header + joined content.
    """

    # Read the JSON array from the input file
    with open (input_file_path,'r',encoding='utf-8') as input_file:
        data = json.load (input_file)

    # Process each object and write to JSONL
    with open (output_file_path,'w',encoding='utf-8') as output_file:
        for item in data:
            # Get the header and paragraphs from each object
            header = item.get ("header","")
            paragraphs = item.get ("paragraphs",[])

            # Join all paragraphs into one content string
            content = " ".join (paragraphs)

            # Create the JSONL line: one JSON object with header and content
            jsonl_line = {
                "header":header,
                "content":content
                }

            # Write this line to the output file
            output_file.write (json.dumps (jsonl_line,ensure_ascii=False) + '\n')

    print (f"✅ Converted {len (data)} sections to JSONL format")
    print (f"📁 Output saved to: {output_file_path}")


# Usage
if __name__ == "__main__":
    input_file = "output_cleaned.json"  # Your JSON file
    output_file = "output_sorted.jsonl"  # Your JSONL output

    transform_json_to_jsonl (input_file,output_file)