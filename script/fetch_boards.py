import json

# Read the file content into a variable
with open("gamedata/boards.json") as file:
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
    priority = data.get("priority")

    # Extract upgrades if available, otherwise set as "none"
    upgrades = [
        {"id": upgrade.get("id")}
        if "name" not in upgrade or "powerType" not in upgrade
        else {"id": upgrade.get("id")}
        for upgrade in data.get("upgrades", [])
    ] or "none"

    # Store the extracted data
    extracted_data.append({"id": item_id, "priority": priority, "upgrades": upgrades})

# Save the extracted data to a JSON file
with open("boards_output.json", "w") as file:
    json.dump(extracted_data, file, indent=2)
