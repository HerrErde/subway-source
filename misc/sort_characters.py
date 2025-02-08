import json
import re
import unicodedata

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
    # Normalize strings by replacing accented characters with their base counterparts.
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


def sort_json(data, link_names):
    # Sort and process JSON data based on link names.
    item_dict = {item["id"].lower(): item for item in data}
    ordered_data = []

    for name in link_names:
        found_item = item_dict.get(name.lower())  # Direct match by 'id'

        if not found_item:
            for key, item in item_dict.items():
                modified_key = key
                for ignore in ignore_strings:
                    modified_key = modified_key.replace(ignore, "")

                for other in other_strings:
                    if other in modified_key:
                        modified_key = modified_key.split(other)[0] + other
                        break

                if name.lower() in modified_key or modified_key in name.lower():
                    found_item = item
                    break

        if found_item:
            append_data(
                found_item["id"].lower(),
                len(ordered_data) + 1,
                ordered_data,
                found_item,
            )
            item_dict.pop(found_item["id"].lower(), None)

    for item_id, item in item_dict.items():
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
