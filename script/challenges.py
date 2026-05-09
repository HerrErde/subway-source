import json
import re
import sys

input_file_path = "temp/gamedata/challenges.json"
output_file_path = "temp/upload/challenges_data.json"

collections_file_path = "temp/upload/collections_data.json"


def read_json(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def extract_season_number(time_slot):
    match = re.search(r"_S(\d+)", time_slot or "")
    if not match:
        raise ValueError(f"Unable to determine season from timeSlot: {time_slot!r}")
    return int(match.group(1))


def season():
    with open(collections_file_path, "r", encoding="utf-8") as input_file:
        data = json.load(input_file)
        timeslot = data.get("timeSlot", "")
        return extract_season_number(timeslot)


def main():
    if len(sys.argv) >= 2:
        season_number = sys.argv[1]
    else:
        season_number = season()

    try:
        data = read_json(input_file_path)

        format_prefix = f"s{season_number}_"
        challenge_data_output = {}

        challenges = data.get("challenges", [])
        eliteChallenges = data.get("eliteChallenges", {})
        challengeDefinitions = data.get("challengeDefinitions", [])

        print(f"Processing season {season_number} challenges...")

        # Process each challenge
        for challenge in challenges:
            challengeId = challenge.get("id", "")

            # Check if challengeId starts with the current season
            if not challengeId.startswith(
                format_prefix.lower()
            ) and challengeId not in {"coinChallenge", "dailyChallenge"}:

                # print(f"Skipping challenge ID {challengeId} - does not match format {format_prefix}")
                continue

            print(f"Found challenge with ID: {challengeId}")

            gameMode = challenge.get("gameMode", "")
            timeSlot = challenge.get("timeSlot", "")
            skipStageCost = challenge.get("skipStageCost", "")
            sunsetPeriod = challenge.get("sunsetPeriod", "")
            kind = challenge.get("kind", "")
            targetCity = challenge.get("targetCity", "")
            matchmakingId = challenge.get("matchmakingId", "")
            serverId = challenge.get("serverId", "")
            seasonChallengeSets = challenge.get("seasonChallengeSets", [])

            ui = challenge.get("ui", {})
            headerTitleKey = ui.get("headerTitleKey", "")

            accessRequirement = challenge.get("accessRequirement", [])
            visibilityRequirement = challenge.get("visibilityRequirement", [])

            if seasonChallengeSets and seasonChallengeSets[0].get("challenges"):
                related_challenge_id = seasonChallengeSets[0]["challenges"][0]
                print(f"Related challenge: {related_challenge_id}")

                # Find the corresponding definition
                matching_definition = next(
                    (
                        definition
                        for definition in challengeDefinitions
                        if definition.get("id", "").lower()
                        == related_challenge_id.lower()
                    ),
                    None,
                )

                if matching_definition:
                    print(f"Found related challenge: {related_challenge_id}")

                    participationRequirement = matching_definition.get(
                        "participationRequirement", {}
                    )
                    # print(f"Adding participationRequirement: {participationRequirement}")

                    rewardTiers = matching_definition.get("rewardTiers", [])

                    # print(f"Adding rewardTiers: {rewardTiers}")

                    groupRewardUnlockOffset = matching_definition.get(
                        "groupRewardUnlockOffset", []
                    )

                    challenge_data_output[challengeId] = {
                        "gameMode": gameMode,
                        "matchmakingId": matchmakingId,
                        "kind": kind,
                        "targetCity": targetCity,
                        "accessRequirement": accessRequirement,
                        "visibilityRequirement": visibilityRequirement,
                        "participationRequirement": participationRequirement,
                        "rewardTiers": rewardTiers,
                        "serverId": serverId,
                        "headerTitleKey": headerTitleKey,
                        "rewardUnlockOffset": groupRewardUnlockOffset,
                        "currentSetEntryID": seasonChallengeSets[0].get("challenges")[
                            0
                        ],
                        "currentSetEntryTimeSlot": seasonChallengeSets[0].get(
                            "timeSlot"
                        ),
                        "sunsetPeriod": sunsetPeriod,
                        "timeSlot": timeSlot,
                        "skipStageCost": skipStageCost,
                    }
                else:
                    print(
                        f"No matching definition found for related challenge ID {related_challenge_id}"
                    )
            else:
                challenge_data_output[challengeId] = {
                    "gameMode": gameMode,
                    "matchmakingId": matchmakingId,
                    "kind": kind,
                    "accessRequirement": accessRequirement,
                }

        output_data = {
            "challenges": challenge_data_output,
            "eliteChallenges": eliteChallenges,
        }

        with open(output_file_path, "w", encoding="utf-8") as output_file:
            json.dump(output_data, output_file, indent=2)

    except FileNotFoundError:
        print(f"Error: Input file '{input_file_path}' not found.")
    except json.JSONDecodeError:
        print(f"Error: Failed to decode JSON from '{input_file_path}'.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    main()
