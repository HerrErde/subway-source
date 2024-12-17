import json
import re
import unicodedata

from rapidfuzz import fuzz

json_input = "temp/output/characters_output.json"
json_input_links = "temp/upload/characters_links.json"
json_output = "temp/upload/characters_data.json"
replace_file = "replace.json"

ignore_strings = ["nflpa"]
other_strings = ["dak", "lamar", "tom", "odell", "patrick", "saquon"]


def read_json(file_path):
    # Read and return JSON data from the specified file
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_string(input_string):
    # Normalize strings by replacing accented characters with their base counterparts."""
    return (
        unicodedata.normalize("NFKD", input_string)
        .encode("ASCII", "ignore")
        .decode("utf-8")
    )


def extract(link_data, replace_data):
    # Extract and process link names from input data.
    item_replace = replace_data.get("Characters", {})

    def process_name(name):
        name = normalize_string(name)
        for search_item, replacement in item_replace.items():
            name = name.replace(search_item, replacement)
        return re.sub(r"[ .\-&]", "", name.lower())

    return [
        process_name(item.get("name", ""))
        for item in link_data
        if item.get("available", True)
    ]


def append_data(item_id, count, ordered_data, item):
    # Append processed item data to the ordered data list
    ordered_data.append(
        {
            "number": count,
            "id": item["id"],
            "outfits": item.get("outfits"),
        }
    )


def calculate_similarity(name1, name2):
    similarity = fuzz.ratio(name1, name2)
    return similarity


def sort_json(data, link_names):
    ordered_data = []

    data_dict = {item["id"].lower(): item for item in data}

    for name in link_names:
        best_match = None
        best_score = 0

        for key, item in data_dict.items():
            modified_key = key

            for ignore in ignore_strings:
                modified_key = modified_key.replace(ignore, "")

            for other in other_strings:
                if other in modified_key:
                    modified_key = modified_key.split(other)[0] + other
                    break

            score = calculate_similarity(name, modified_key)

            if score > best_score:
                best_score = score
                best_match = item

            if name == modified_key or name in modified_key:
                best_match = item
                break

        if best_match:
            append_data(
                best_match["id"].lower(),
                len(ordered_data) + 1,
                ordered_data,
                best_match,
            )
            data_dict.pop(best_match["id"].lower(), None)

    for item_id, item in data_dict.items():
        append_data(item_id.lower(), len(ordered_data) + 1, ordered_data, item)

    return ordered_data


def main():
    link_data = read_json(json_input_links)
    replace_data = read_json(replace_file)
    json_data = read_json(json_input)

    extracted_names = extract(link_data, replace_data)
    ordered_data = sort_json(json_data, extracted_names)

    with open(json_output, "w", encoding="utf-8") as f:
        json.dump(ordered_data, f, indent=2)


if __name__ == "__main__":
    main()
