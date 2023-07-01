import json
import sys

json_input = "characters_output.json"
json_input_links = "characters_links.json"
json_output = "characters_data.json"

ignore_strings = ["nflpa"]

other_strings = ["dak", "lamar", "tom", "odell", "patrick", "saquon"]


def extract(json_input_links):
    with open(json_input_links, "r") as f:
        link_data = json.load(f)

    with open("replace.json", "r") as f:
        replace_data = json.load(f)

    link_names = []
    global_replace = replace_data.get("Global", {})
    character_replace = replace_data.get("Characters", {})

    for item in link_data:
        if item.get("available", True):
            name = item.get("name", "")

            for board, replacement in character_replace.items():
                name = name.replace(board, replacement)

            for key, value in global_replace.items():
                name = name.replace(key, value)

            name = name.lower()
            link_names.append(name)

    return link_names


def sort_json(json_input, link_names, json_output):
    with open(json_input, "r") as f:
        data = json.load(f)

    ordered_data = []
    skipped_names = []
    count = 1

    for item in data:
        if "id" in item:
            item_id = item["id"].lower()
            for ignore in ignore_strings:
                item_id = item_id.replace(ignore, "")

            for other in other_strings:
                if other in item_id:
                    item_id = item_id.split(other)[0] + other

            # Check if the modified item_id is present in the names list
            if item_id in link_names:
                item_with_number = {
                    "number": count,
                    "id": item["id"],
                    "outfits": item["outfits"],
                }
                count += 1
                ordered_data.append(item_with_number)
            else:
                skipped_names.append(item["id"])

    with open(json_output, "w") as f:
        json.dump(ordered_data, f, indent=2)

    return skipped_names


link_names = extract(json_input_links)
skipped_names = sort_json(json_input, link_names, json_output)

if skipped_names:
    print("Skipped:")
    for name in skipped_names:
        print(name)
    sys.exit("Error: Items in skipped list.")
