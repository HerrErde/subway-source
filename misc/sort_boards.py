import json
import re
import unicodedata

json_input = "temp/output/boards_output.json"
json_input_links = "temp/upload/boards_links.json"
json_output = "temp/upload/boards_data.json"
replace_file = "replace.json"

ignore_strings = ["nflpa", "sakar"]


def read_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_string(input_string):
    # Normalize strings by replacing accented characters with their base counterparts
    return (
        unicodedata.normalize("NFKD", input_string)
        .encode("ASCII", "ignore")
        .decode("utf-8")
    )


def extract(link_data, replace_data):
    # Extract and process link names
    item_replace = replace_data.get("Hoverboards", {})

    def process_name(name):
        name = normalize_string(name)
        for item, replacement in item_replace.items():
            name = name.replace(item, replacement)
        name = re.sub(r"[^a-zA-Z0-9]", "", name).lower()
        name = re.sub(r"\bhoverboard\b", "default", name)
        return name

    link_names = [
        process_name(item.get("name", ""))
        for item in link_data
    ]

    # Replace birthdays in link names
    year = 2021
    for i in range(2, len(link_names) + 1):
        exponent = i + 7
        birthday = f"{exponent}thbirthday"
        link_names = [name.replace(birthday, f"birthday{year}") for name in link_names]
        year += 1

    return link_names


def append_data(count, ordered_data, item):
    ordered_data.append(
        {
            "number": count,
            "id": item["id"],
            "upgrades": item.get("upgrades"),
        }
    )


def sort_json(data, link_names):
    def norm_id(s):
        return re.sub(r"[^a-zA-Z0-9]", "", s).lower()

    def remove_ignores(s):
        for ignore in ignore_strings:
            s = s.replace(ignore, "")
        return s

    item_dict = {norm_id(item["id"]): item for item in data}
    ordered_data = []
    matched_items = set()

    for idx, name in enumerate(link_names):
        found_item = item_dict.get(name)
        # fuzzysearch: Exact match after removing ignore_strings
        if not found_item:
            for key, item in item_dict.items():
                key_ohne_ign = remove_ignores(key)
                if key_ohne_ign == name and key not in matched_items:
                    found_item = item
                    break
        # even fuzzier search: Exact match after removing ignore_strings
        if not found_item:
            for key, item in item_dict.items():
                key_ohne_ign = remove_ignores(key)
                name = remove_ignores(name)
                if name in key_ohne_ign or key_ohne_ign in name:
                    if key not in matched_items:
                        found_item = item
                        break
        if found_item and norm_id(found_item["id"]) not in matched_items:
            append_data(
                len(ordered_data) + 1,
                ordered_data,
                found_item,
            )
            matched_items.add(norm_id(found_item["id"]))
            print(f"[{idx+1}] Match: {name} -> {found_item['id']}")
        else:
            print(f"[{idx+1}] No Match für: {name}")

    # append rest items alphabetically
    remaining_items = [
        item for item in data if norm_id(item["id"]) not in matched_items
    ]
    remaining_items.sort(key=lambda x: x["id"].lower())
    for item in remaining_items:
        append_data(len(ordered_data) + 1, ordered_data, item)
        print(f"Rest: {item['id']} gets appended alphabetically.")

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
