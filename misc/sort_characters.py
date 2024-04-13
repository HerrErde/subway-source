import json
import unicodedata

json_input = "characters_output.json"
json_input_links = "upload/characters_links.json"
json_output = "upload/characters_data.json"

ignore_strings = ["nflpa"]

other_strings = ["dak", "lamar", "tom", "odell", "patrick", "saquon"]


def read_json(file_path):
    with open(file_path, "r") as f:
        return json.load(f)


def normalize_string(input_string):
    # Normalize the string by replacing accented characters with their base counterparts
    normalized_string = (
        unicodedata.normalize("NFKD", input_string)
        .encode("ASCII", "ignore")
        .decode("utf-8")
    )
    return normalized_string


def extract(json_input_links):
    link_data = read_json(json_input_links)
    replace_data = read_json("replace.json")

    link_names = []
    global_replace = replace_data.get("Global", {})
    character_replace = replace_data.get("Characters", {})

    for item in link_data:
        if item.get("available", True):
            name = item.get("name", "")

            # Normalize the name by replacing accented characters
            name = normalize_string(name)

            for board, replacement in character_replace.items():
                name = name.replace(normalize_string(board), replacement)

            for key, value in global_replace.items():
                name = name.replace(normalize_string(key), value)

            name = name.lower()
            link_names.append(name)

    return link_names


def append_data(item_id, count, ordered_data, item):
    ordered_data.append(
        {
            "number": count,
            "id": item["id"],
            "outfits": item.get("outfits"),
        }
    )


def sort_json(json_input, link_names, json_output):
    data = read_json(json_input)
    ordered_data = []

    for name in link_names:
        found_item = None

        # Check for direct matches
        for item in data:
            item_id = item.get("id", "").lower()

            if item_id == name:
                found_item = item
                break

        if found_item is None:
            for item in data:
                item_id = item["id"].lower()

                # Apply replacements and transformations to item_id
                for ignore in ignore_strings:
                    item_id = item_id.replace(ignore, "")

                # Check if any other_strings are present in item_id
                for other in other_strings:
                    if other in item_id:
                        item_id = item_id.split(other)[0] + other
                        if item_id == name:
                            found_item = item
                            break

                # If the lowercase variant of the name is contained anywhere in the ID data
                if found_item is None and name in item_id:
                    found_item = item
                    break

        # If a match is found, append relevant information to ordered_data
        if found_item:
            append_data(
                found_item["id"].lower(),
                len(ordered_data) + 1,
                ordered_data,
                found_item,
            )

    # Check for skipped item IDs in ordered_data
    ordered_ids = {entry["id"] for entry in ordered_data}
    all_ids = {item["id"] for item in data}
    skipped_ids = all_ids - ordered_ids

    # Append skipped items to ordered_data
    for item_id in skipped_ids:
        for item in data:
            if item["id"] == item_id:
                append_data(
                    item_id.lower(),
                    len(ordered_data) + 1,
                    ordered_data,
                    item,
                )

    with open(json_output, "w") as f:
        json.dump(ordered_data, f, indent=2)


extracted_names = extract(json_input_links)
sort_json(json_input, extracted_names, json_output)
