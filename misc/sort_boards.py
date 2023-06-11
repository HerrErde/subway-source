import json
import re

json_input = "boards_output.json"
json_input_links = "boards_links.json"
json_output = "boards_data.json"

ignore_strings = ["nflpa", "sakar"]


def extract(json_input_links):
    with open(json_input_links, "r") as f:
        link_data = json.load(f)

    names = [item.get("name", "") for item in link_data]
    names = [name.replace(" ", "").replace("-", "").replace("&", "").replace("Jr.", "")for name in names]
    names = [name.replace("Wrapped", "xmas2022") for name in names]
    names = [re.sub(r"\bHoverboard\b", "default", name).replace("8thBirthday", "birthday")for name in names]

    year = 2021
    for i in range(2, len(names) + 1):
        exponent = i + 7
        birthday = f"{exponent}thBirthday"
        names = [name.replace(birthday, f"birthday{year}") for name in names]
        year += 1

    names = [name.lower() for name in names]

    return names


def sort_json(json_input, names, json_output):
    with open(json_input, "r") as f:
        data = json.load(f)

    ordered_data = []
    count = 1
    skipped_names = []

    for item in data:
        if "id" in item:
            item_id = item["id"].lower()
            for ignore in ignore_strings:
                item_id = item_id.split(ignore)[-1].lower()

            # Check if the modified item_id is present in the names list
            if item_id in names:
                item_with_number = {
                    "number": count,
                    "id": item["id"],
                    "upgrades": item.get("upgrades", ""),
                }
                count += 1
                ordered_data.append(item_with_number)
            else:
                skipped_names.append(item["id"])

    with open(json_output, "w") as f:
        json.dump(ordered_data, f, indent=2)

    return skipped_names


names = extract(json_input_links)
skipped_names = sort_json(json_input, names, json_output)

if skipped_names:
    print("Skipped Names:")
    for name in skipped_names:
        print(name)

