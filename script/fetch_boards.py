import json

input_file_path = "temp/gamedata/boards.json"
output_file_path = "temp/output/boards_output.json"

with open(input_file_path) as file:
    json_data = json.load(file)

names = list(json_data["boards"].keys())

# Create a list to store the extracted data
extracted_data = []

# Loop through each item name
for name in names:
    print("Item Name:", name)

    data = json_data["boards"].get(name, {})

    item_id = data.get("id")

    # Extract upgrades if available, otherwise set as null
    upgrades = [
        (
            {"id": upgrade.get("id").replace(" ", "")}
            if "name" not in upgrade and " " not in upgrade.get("id")
            else {"id": upgrade.get("id").replace(" ", "")}
        )
        for upgrade in data.get("upgrades", [])
    ] or None

    extracted_data.append({"id": item_id.replace(" ", ""), "upgrades": upgrades})

with open(output_file_path, "w", encoding="utf-8") as file:
    json.dump(extracted_data, file, indent=2)
