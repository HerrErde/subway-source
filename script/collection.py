import json
import re
from pathlib import Path

input_file = "temp/gamedata/collections.json"
output_file = "temp/upload/collections_data.json"

type_mapping = {"Character": 2, "Hoverboard": 3}


def read_json(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def extract_items(collection_info):
    return [
        {
            "id": item["id"],
            "type": type_mapping.get(item["type"]),
            "points": item["collectionPoints"],
        }
        for item in collection_info.get("items", {}).values()
    ]


def get_time_slot(data):
    pattern = r"collection_season_S(\d+)"
    for key, value in data.get("seasonalCollections", {}).items():
        if re.match(pattern, key):
            return value.get("timeSlot", "")
    return ""


def main():
    input_path = Path(input_file)
    output_path = Path(output_file)

    if not input_path.exists():
        print(f"Error: Input file '{input_file}' not found.")
        return

    data = read_json(input_path)
    collections_data = data.get("collections", {})
    seasonal_collections_data = data.get("seasonalCollections", {})

    collections = [
        {"id": collection_id, "items": extract_items(collection_info)}
        for collection_id, collection_info in collections_data.items()
    ]

    seasonal_collections = [
        {"id": collection_id, "items": extract_items(collection_info)}
        for collection_id, collection_info in seasonal_collections_data.items()
    ]

    meter_tiers = data.get("common", {}).get("meterTiers", [])
    meterTiers = len(meter_tiers)
    meterScore = meter_tiers[-1].get("requiredScore") if meter_tiers else None

    output_data = {
        "timeSlot": get_time_slot(data),
        "collections": collections,
        "seasonalCollections": seasonal_collections,
        "meterTiers": meterTiers,
        "meterScore": meterScore,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(output_data, file, indent=2)


if __name__ == "__main__":
    main()
