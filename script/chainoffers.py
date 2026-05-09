import json

input_file_path = "temp/gamedata/chainoffers.json"
output_file_path = "temp/upload/chainoffers_data.json"


def main():
    try:
        with open(input_file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        offer_output = []

        chainoffers = data.get("chainOffers", [])

        for offer in chainoffers:
            offer_id = offer.get("id", "")
            time_slot = offer.get("timeSlot", "")
            fallback_product_id = offer.get("fallbackProductId", "")
            home_button = offer.get("homeButton", {})
            fallback_reward = offer.get("fallbackReward", {})
            offers = offer.get("offers", [])

            offer_output.append(
                {
                    "id": offer_id,
                    "timeSlot": time_slot,
                    "fallbackProductId": fallback_product_id,
                    "fallbackReward": fallback_reward,
                    "homeButton": home_button,
                    "offers": offers,
                }
            )

        with open(output_file_path, "w", encoding="utf-8") as f:
            json.dump(offer_output, f, indent=4)

    except Exception as e:
        print(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    main()
