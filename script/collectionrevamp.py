import json
from pathlib import Path

input_file = "temp/gamedata/collectionsrevamp.json"
output_file = "temp/upload/collectionsrevamp_data.json"

type_mapping = {"Character": 2, "Hoverboard": 3}


def extract_items(collection_info):
    return [
        {
            "id": item["id"],
            "type": type_mapping.get(item["type"]),
        }
        for item in collection_info.get("items", {}).values()
    ]


def main():
    input_path = Path(input_file)
    output_path = Path(output_file)

    if not input_path.exists():
        print(f"Error: Input file '{input_file}' not found.")
        return

    with open(input_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    collections_data = data.get("collections", {})

    collections = [
        {"id": collection_id, "items": extract_items(collection_info)}
        for collection_id, collection_info in collections_data.items()
    ]

    reward_track = data.get("common", {}).get("rewardTrack", [])
    rewardTiers = len(reward_track)
    rewardScore = reward_track[-1].get("requiredScore") if reward_track else None

    output_data = {
        "collections": collections,
        "rewardTiers": rewardTiers,
        "rewardScore": rewardScore,
        "crewCapsuleRewardTrackId": data.get(
            "crewCapsuleRewardTrackId", "crew_capsule_reward_track"
        ),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(output_data, file, indent=2)


if __name__ == "__main__":
    main()
