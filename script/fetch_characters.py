import json

input_file_path = "temp/gamedata/characters.json"
output_file_path = "temp/output/characters_output.json"


def normalize_id(value):
    if not isinstance(value, str) or not value:
        return None
    return value.replace(" ", "")


def main():
    with open(input_file_path, "r", encoding="utf-8") as file:
        json_data = json.load(file)

    extracted_data = []
    for name, data in json_data.get("characters", {}).items():
        print("Item Name:", name)

        item_id = normalize_id(data.get("id"))
        if item_id is None:
            continue

        outfits = []
        for outfit in data.get("outfits", []) or []:
            outfit_id = normalize_id(outfit.get("id"))
            if outfit_id is None:
                continue

            outfit_data = {"id": outfit_id}
            variation_name = outfit.get("name")
            if isinstance(variation_name, str) and variation_name:
                outfit_data["variation"] = {"name": variation_name}

            outfits.append(outfit_data)

        extracted_data.append({"id": item_id, "outfits": outfits or None})

    with open(output_file_path, "w", encoding="utf-8") as file:
        json.dump(extracted_data, file, indent=2)


if __name__ == "__main__":
    main()
