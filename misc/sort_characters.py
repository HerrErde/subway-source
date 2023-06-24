import json

json_input = "characters_output.json"
json_input_links = "characters_links.json"
json_output = "characters_data.json"


def extract(json_input_links):
    with open(json_input_links, "r") as f:
        link_data = json.load(f)

    names = [item.get("name", "") for item in link_data]
    names = [
        name.replace("Hoverboard", "default")
        .replace("Super Runner Fernando", "fernando")
        .replace(" ", "")
        for name in names
    ]

    return names


def sort_json(json_input, names, json_output):
    with open(json_input, "r") as f:
        data = json.load(f)

    names = [name.lower() for name in names]

    ordered_data = []
    count = 1

    for name in names:
        for item in data:
            if "id" in item and item["id"].lower() == name:
                item_with_number = {
                    "number": count,
                    "id": item["id"],
                    "outfits": item["outfits"],
                }
                count += 1
                ordered_data.append(item_with_number)

    with open(json_output, "w") as f:
        json.dump(ordered_data, f, indent=2)


names = extract(json_input_links)
sort_json(json_input, names, json_output)
