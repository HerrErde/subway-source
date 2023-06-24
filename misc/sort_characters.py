import json

json_input = "characters_output.json"
json_input_links = "characters_links.json"
json_output = "characters_data.json"

ignore_strings = ["nflpa"]

other_strings = ["dak", "lamar", "tom", "odell", "patrick", "saquon"]


def extract(json_input_links):
    with open(json_input_links, "r") as f:
        link_data = json.load(f)

    link_names = [item.get("name", "") for item in link_data]
    link_names = [
        name
        .replace("Super Runner Fernando", "fernando")
        .replace(" ", "")
        .replace(".", "")
        .lower()
        for name in link_names
    ]

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
