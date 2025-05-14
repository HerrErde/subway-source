import json

input_file_path = "temp/gamedata/citytours.json"
output_file_path = "temp/upload/citytours_data.json"


def main():
    with open(input_file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    citytours_data_output = {}

    for tour in data.get("cityTours", []):
        tour_id = tour.get("id", "")

        citytours_data_output[tour_id] = {
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

    with open(output_file_path, "w", encoding="utf-8") as output_file:
        json.dump(citytours_data_output, output_file, indent=4)


if __name__ == "__main__":
    main()
