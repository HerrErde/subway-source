import json

input_file_path = "temp/gamedata/products.json"
output_file_path = "temp/upload/products_data.json"


with open(input_file_path, "r", encoding="utf-8") as input_file:
    data = json.load(input_file)

    modifiers = data.get("modifiers", {})

    output_data = {"modifiers": modifiers}

with open(output_file_path, "w", encoding="utf-8") as output_file:
    json.dump(output_data, output_file, indent=2)
