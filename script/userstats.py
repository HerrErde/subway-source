import json

input_file_path = "temp/gamedata/cities.json"
output_file_path = "temp/upload/cities_data.json"


def main():
    with open(input_file_path, "r", encoding="utf-8") as input_file:
        data = json.load(input_file)
        cities = data.get("cities", {})

    output_data = {"cities": list(cities.keys())}

    with open(output_file_path, "w", encoding="utf-8") as output_file:
        json.dump(output_data, output_file, indent=2)


if __name__ == "__main__":
    main()
