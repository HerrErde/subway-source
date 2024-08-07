import json

input_file_path = "temp/gamedata/boards.json"
output_file_path = "temp/output/boards_output.json"

# Read the file content into a variable
with open(input_file_path) as file:
    json_data = json.load(file)

# Extract the board names using list comprehension
names = list(json_data["boards"].keys())

# Create a list to store the extracted data
extracted_data = []

# Loop through each item name
for name in names:
    print("Item Name:", name)

    # Extract the data for the current item
    data = json_data["boards"].get(name, {})

    # Extract the desired fields from the data
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

    # Store the extracted data
    extracted_data.append({"id": item_id.replace(" ", ""), "upgrades": upgrades})

# Save the extracted data to a JSON file
with open(output_file_path, "w") as file:
    json.dump(extracted_data, file, indent=2)
