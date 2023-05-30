import json

# Read the file content into a variable
with open("gamedata/characters.json") as file:
    json_data = json.load(file)

# Extract the board names
names = json_data["characters"].keys()

# Create a list to store the extracted data
extracted_data = []

# Loop through each item name
for name in names:
    print("Item Name:", name)

    # Extract the data for the current item
    data = json_data["characters"][name]

    # Extract the desired fields from the data
    item_id = data["id"]

    # Extract outfits if available, otherwise set as "none"
    outfits = []
    if "outfits" in data and len(data["outfits"]) > 0:
        outfits = [
            {"id": outfit["id"], "variation": {"name": outfit["name"]}}
            if "name" in outfit
            else {"id": outfit["id"]}
            for outfit in data["outfits"]
        ]
    else:
        outfits = "none"

    # Print the extracted data
    # print("Item ID:", item_id)
    # print("Outfits:")
    # print(json.dumps(outfits, indent=2))
    # print()

    # Store the extracted data
    extracted_data.append({"id": item_id.replace(" ", ""), "outfits": outfits})

# Save the extracted data to a JSON file
with open("characters_output.json", "w") as file:
    json.dump(extracted_data, file, indent=2)
