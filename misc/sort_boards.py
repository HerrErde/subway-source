import json
import re


json_input = "boards_output.json"
json_input_links = "boards_links.json"
json_output = "boards_data.json"


def extract(json_input_links):
    with open(json_input_links, "r") as f:
        data = json.load(f)

    names = [item.get("name", "") for item in data]
    names = [name.replace(" ", "").replace("-", "") for name in names]
    names = [name.replace("Wrapped", "xmas2022") for name in names]
    names = [re.sub(r"\bHoverboard\b", "default", name) for name in names]
    names = [name.replace("8thBirthday", "birthday") for name in names]

    year = 2021
    for i in range(2, len(names) + 1):
        exponent = i + 7
        birthday = f"{exponent}thBirthday"
        names = [name.replace(birthday, f"birthday{year}") for name in names]
        year += 1

    return names


def sort_json(json_input, names, json_output):
    with open(json_input, "r") as f:
        data = json.load(f)

    names = [name.lower() for name in names]

    ordered_data = []
    count = 1
    skipped_names = []

    for name in names:
        found = False
        for item in data:
            if "id" in item and item["id"].replace(" ", "").lower() == name:
                item_with_number = {
                    "number": count,
                    "id": item["id"],
                    "upgrades": item["upgrades"],
                }
                count += 1
                ordered_data.append(item_with_number)
                found = True
                break

        if not found:
            skipped_names.append(name)

    with open(json_output, "w") as f:
        json.dump(ordered_data, f, indent=2)

    return skipped_names


names = extract(json_input_links)
skipped_names = sort_json(json_input, names, json_output)
print("Skipped Names:")
for name in skipped_names:
    print(name)
