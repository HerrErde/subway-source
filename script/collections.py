import json

input_file = "gamedata/collections.json"
output_file = "upload/collections_data.json"

type_mapping = {"Character": 2, "Hoverboard": 3}


def read_json(file_path):
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return {}


def extract_items(collection_info):
    return [
        {"id": item["id"], "type": type_mapping.get(item["type"], "")}
        for item in collection_info.get("items", {}).values()
    ]


def main():
    # Read the input JSON file
    data = read_json(input_file)

    # Extract data from the "seasonalCollections" section
    seasonal_data = [
        {"id": collection_id, "items": extract_items(collection_info)}
        for collection_id, collection_info in data.get(
            "seasonalCollections", {}
        ).items()
    ]

    # Extract data from the "collections" section
    collection_data = [
        {
            "id": collection_id,
            "items": {
                item["id"]: {
                    "id": item["id"],
                    "type": type_mapping.get(item["type"], ""),
                }
                for item in collection_info.get("items", {}).values()
            },
        }
        for collection_id, collection_info in data.get("collections", {}).items()
    ]

    # Get the "timeSlot" value from the input data
    time_slot = (
        data.get("seasonalCollections", {})
        .get("collection_season_S73", {})
        .get("timeSlot", "")
    )

    # Create a dictionary with the desired structure
    output_data = {
        "timeSlot": time_slot,
        "collections": collection_data,
        "seasonalCollections": seasonal_data,
    }

    # Write the extracted data to the output JSON file
    with open(output_file, "w") as file:
        json.dump(output_data, file, indent=4)


main()
