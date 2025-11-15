import json
from typing import Any, Union
# Basic installation


def remove_keys_recursive(obj: Union[dict, list], keys_to_remove: set) -> Union[dict, list]:
    """
    Recursively remove specified keys from a nested JSON object.

    Args:
        obj (Union[dict, list]): The input JSON structure (dict or list).
        keys_to_remove (set): Set of string keys to remove from all levels.

    Returns:
        Union[dict, list]: A new JSON structure with specified keys removed.
    """
    if isinstance(obj, dict):
        return {
            k: remove_keys_recursive(v, keys_to_remove)
            for k, v in obj.items() if k not in keys_to_remove
        }
    elif isinstance(obj, list):
        return [remove_keys_recursive(item, keys_to_remove) for item in obj]
    else:
        return obj  # base case: return as-is if not dict/list

# Example usage:
if __name__ == "__main__":
    input_path = "title1.json"
    output_path = "output_cleaned.json"
    keys_to_strip = {"url", "url_hash"}

    with open(input_path, "r", encoding="utf-8") as infile:
        data = json.load(infile)

    cleaned = remove_keys_recursive(data, keys_to_strip)

    with open(output_path, "w", encoding="utf-8") as outfile:
        json.dump(cleaned, outfile, indent=2, ensure_ascii=False)