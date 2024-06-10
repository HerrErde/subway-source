import json

input_file_path = "gamedata/cities.json"
output_file_path = "upload/cities_data.json"

with open(input_file_path, "r") as input_file:
    data = json.load(input_file)
    cities = data.get(
        "cities", {}
    )  # Get the "entries" dictionary from the loaded JSON data

    # Extract names of each entry dictionary
    names = list(cities.keys())

output_data = {"cities": names}

with open(output_file_path, "w") as output_file:
    json.dump(output_data, output_file, indent=2)
