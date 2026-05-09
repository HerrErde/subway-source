import json

input_file_path = "temp/gamedata/boards.json"
output_file_path = "temp/output/boards_output.json"


def normalize_id(value):
    if not isinstance(value, str) or not value:
        return None
    return value.replace(" ", "")


def main():
    with open(input_file_path, "r", encoding="utf-8") as file:
        json_data = json.load(file)

    boards = json_data.get("boards", {})
    extracted_data = []

    for name, data in boards.items():
        print("Item Name:", name)
        item_id = normalize_id(data.get("id"))
        if item_id is None:
            continue

        upgrades = []
        for upgrade in data.get("upgrades", []) or []:
            upgrade_id = normalize_id(upgrade.get("id"))
            if upgrade_id is not None:
                upgrades.append({"id": upgrade_id})

        extracted_data.append({"id": item_id, "upgrades": upgrades or None})

    with open(output_file_path, "w", encoding="utf-8") as file:
        json.dump(extracted_data, file, indent=2)


if __name__ == "__main__":
    main()
