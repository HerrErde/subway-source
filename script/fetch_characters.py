import json

input_file_path = "temp/gamedata/characters.json"
output_file_path = "temp/output/characters_output.json"


with open(input_file_path) as file:
    json_data = json.load(file)

names = json_data["characters"].keys()

extracted_data = []

for name in names:
    print("Item Name:", name)

    # Extract the data for the current item
    data = json_data["characters"][name]

    # Extract the desired fields from the data
    item_id = data["id"]

    # Extract outfits if available, otherwise set as null
    outfits = []
    if "outfits" in data and len(data["outfits"]) > 0:
        outfits = [
            (
                {"id": outfit["id"], "variation": {"name": outfit["name"]}}
                if "name" in outfit
                else {"id": outfit["id"]}
            )
            for outfit in data["outfits"]
        ]
    else:
        outfits = None

    # Print the extracted data
    # print("Item ID:", item_id)
    # print("Outfits:")
    # print(json.dumps(outfits, indent=2))
    # print()

    extracted_data.append({"id": item_id.replace(" ", ""), "outfits": outfits})

with open(output_file_path, "w", encoding="utf-8") as file:
    json.dump(extracted_data, file, indent=2)
