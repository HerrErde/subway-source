import json
import re

json_input = "temp/output/boards_output.json"
json_input_links = "temp/upload/boards_links.json"
json_output = "temp/upload/boards_data.json"
replace_file = "replace.json"

ignore_strings = ["nflpa", "sakar"]


def read_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract(link_data, replace_data):
    # Extract and process link names
    item_replace = replace_data.get("Hoverboards", {})

    def process_name(name):
        # Process the name according to rules
        for item, replacement in item_replace.items():
            name = name.replace(item, replacement)
        name = re.sub(r"[^a-zA-Z0-9]", "", name)
        name = re.sub(r"\bhoverboard\b", "default", name.lower())
        return name

    link_names = [
        process_name(item.get("name", ""))
        for item in link_data
        if item.get("available", True)
    ]

    # Replace birthdays in link names
    year = 2021
    for i in range(2, len(link_names) + 1):
        exponent = i + 7
        birthday = f"{exponent}thbirthday"
        link_names = [name.replace(birthday, f"birthday{year}") for name in link_names]
        year += 1

    return link_names


def append_data(item_id, count, ordered_data, item):
    ordered_data.append(
        {
            "number": count,
            "id": item["id"],
            "upgrades": item.get("upgrades"),
        }
    )


def sort_json(data, link_names, ignore_strings):
    # Sort and write JSON data based on link names
    item_dict = {}

    # Preprocess items and create a dictionary for fast lookups
    for item in data:
        item_id = item["id"].lower()
        for ignore in ignore_strings:
            item_id = item_id.replace(ignore, "")
        item_dict[item_id] = item

    ordered_data = []

    # Process link names first
    for name in link_names:
        item = item_dict.pop(name, None)
        if item:
            append_data(name, len(ordered_data) + 1, ordered_data, item)

    # Process remaining items
    for item_id, item in item_dict.items():
        append_data(item_id, len(ordered_data) + 1, ordered_data, item)

    # Write the processed data to the output JSON file
    with open(json_output, "w", encoding="utf-8")as f:
        json.dump(ordered_data, f, indent=2)


def main():
    link_data = read_json(json_input_links)
    replace_data = read_json(replace_file)
    json_data = read_json(json_input)

    link_names = extract(link_data, replace_data)
    sort_json(json_data, link_names, ignore_strings)


if __name__ == "__main__":
    main()
