import json
import re

json_input = "boards_output.json"
json_input_links = "upload/boards_links.json"
json_output = "upload/boards_data.json"

ignore_strings = ["nflpa", "sakar"]


def read_json(file_path):
    with open(file_path, "r") as f:
        return json.load(f)


def extract(json_input_links):
    link_data = read_json(json_input_links)
    replace_data = read_json("replace.json")

    link_names = []
    item_replace = replace_data.get("Hoverboards", {})

    for item in link_data:
        if item.get("available", True):
            name = item.get("name", "")

            for item, replacement in item_replace.items():
                name = name.replace(item, replacement)

            name = re.sub(r"[^a-zA-Z0-9]", "", name)

            name = re.sub(r"\bhoverboard\b", "default", name.lower())
            link_names.append(name)

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
            "upgrades": item.get("upgrades", ""),
        }
    )


def sort_json(json_input, link_names, json_output):
    data = read_json(json_input)
    ordered_data = []
    skipped_names = []

    for name in link_names:
        for item in data:
            item_id = item["id"].lower()

            # Apply replacements and transformations to the item_id
            for ignore in ignore_strings:
                item_id = item_id.replace(ignore, "")

            # Check if the modified name matches the current item_id
            if item_id == name:
                # If there is a match, create a dictionary with relevant information
                append_data(item_id, len(ordered_data) + 1, ordered_data, item)
                # Break out of the inner loop
                break

    # Check for skipped item IDs in ordered_data
    ordered_ids = {entry["id"] for entry in ordered_data}
    all_ids = {item["id"] for item in data}
    skipped_ids = all_ids - ordered_ids
    if skipped_ids:
        print("Skipped IDs:")
        for skipped_id in skipped_ids:
            print(skipped_id)
            for item in data:
                item_id = item["id"].lower()

                # Check if the modified name matches the current item_id
                if item_id == skipped_id:
                    append_data(item_id, len(ordered_data) + 1, ordered_data, item)

    # Write the processed data to the output JSON file
    with open(json_output, "w") as f:
        json.dump(ordered_data, f, indent=2)


link_names = extract(json_input_links)
sort_json(json_input, link_names, json_output)
