import json

input_file_path = "temp/gamedata/chainoffers.json"
output_file_path = "temp/upload/chainoffers_data.json"


def main():
    try:
        with open(input_file_path, "r") as file:
            data = json.load(file)

        chainoffers = data.get("chainOffers", [])

        chainOffers = []

        for chainoffer in chainoffers:
            id = chainoffer.get("id", "")
            timeSlot = chainoffer.get("timeSlot", "")
            fallbackProductId = chainoffer.get("fallbackProductId", "")
            homeButton = chainoffer.get("homeButton", {})
            fallbackReward = chainoffer.get("fallbackReward", {})

            offers = chainoffer.get("offers", [])

            chainOffers.append(
                {
                    "id": id,
                    "timeSlot": timeSlot,
                    "fallbackProductId": fallbackProductId,
                    "fallbackReward": fallbackReward,
                    "homeButton": homeButton,
                    "offers": offers,
                }
            )

        output_data = {
            "chainOffers": chainOffers,
        }

        with open(output_file_path, "w", encoding="utf-8") as f:
            json.dump(chainOffers, f, indent=4)

    except Exception as e:
        print(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    main()
