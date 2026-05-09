import json

input_file_path = "temp/gamedata/products.json"
output_file_path = "temp/upload/products_data.json"


def main():
    with open(input_file_path, "r", encoding="utf-8") as input_file:
        data = json.load(input_file)

    output_data = {"modifiers": data.get("modifiers", {})}

    with open(output_file_path, "w", encoding="utf-8") as output_file:
        json.dump(output_data, output_file, indent=2)


if __name__ == "__main__":
    main()
