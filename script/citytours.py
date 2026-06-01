import json

input_file_path = "temp/gamedata/citytours.json"
output_file_path = "temp/upload/citytours_data.json"


def main():
    with open(input_file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    citytours_list = []
    for tour in data.get("cityTours", []):
        citytours_list.append(
            {
                "id": tour.get("id", ""),
                "icon": tour.get("icon", ""),
                "titleImage": tour.get("titleImage", ""),
                "colorSchema": tour.get("colorSchema", ""),
                "description": tour.get("description", ""),
                "timeSlot": tour.get("timeSlot", ""),
                "gameMode": tour.get("gameMode", ""),
                "tokenId": tour.get("tokenId", ""),
                "sunsetPeriodInSeconds": tour.get("sunsetPeriodInSeconds", ""),
                "infoPopup": tour.get("infoPopup", ""),
                "cities": tour.get("cities", ""),
                "rewards": tour.get("rewards", ""),
            }
        )

    gauntlets_list = []
    for tour in data.get("gauntlets", []):
        gauntlets_list.append(
            {
                "id": tour.get("id", ""),
                "tiers": tour.get("tiers", []),
            }
        )

    output_data = {"cityTours": citytours_list, "gauntlets": gauntlets_list}

    with open(output_file_path, "w", encoding="utf-8") as output_file:
        json.dump(output_data, output_file, indent=4)


if __name__ == "__main__":
    main()
