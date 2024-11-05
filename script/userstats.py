import json

input_file_path = "temp/gamedata/cities.json"
output_file_path = "temp/upload/cities_data.json"

with open(input_file_path, "r", encoding="utf-8") as input_file:
    data = json.load(input_file)
    cities = data.get("cities", {})

    names = list(cities.keys())

output_data = {"cities": names}

with open(output_file_path, "w") as output_file:
    json.dump(output_data, output_file, indent=2)
