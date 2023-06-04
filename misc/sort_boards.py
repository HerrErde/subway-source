import json


json_input = "boards_output.json"
json_input_links = "boards_links.json"
json_output = "boards_data.json"


def extract(json_input_links):
    with open(json_input_links, "r") as f:
        data = json.load(f)

    names = [item.get("name", "") for item in data]
    names = [name.replace(" ", "") for name in names]
    names = [name.replace("Hoverboard", "default") for name in names]
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

    for name in names:
        for item in data:
            if "id" in item and item["id"].replace(" ", "").lower() == name:
                item_with_number = {
                    "number": count,
                    "id": item["id"],
                    "upgrades": item["upgrades"],
                }
                count += 1
                ordered_data.append(item_with_number)

    with open(json_output, "w") as f:
        json.dump(ordered_data, f, indent=2)


names = extract(json_input_links)
sort_json(json_input, names, json_output)
