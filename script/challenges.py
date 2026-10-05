import json
import re
import sys

input_file_path = "temp/gamedata/challenges.json"
output_file_path = "temp/upload/challenges_data.json"


def read_json(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def get_latest_season(challenges):
    seasons = []
    for challenge in challenges.values():
        match = re.match(r"s(\d+)_", challenge.get("id", ""), re.IGNORECASE)
        if match:
            seasons.append(int(match.group(1)))
    if not seasons:
        raise ValueError("Unable to determine season: no season-prefixed challenge IDs found")
    return max(seasons)


def main():
    data = read_json(input_file_path)
    challenges = data.get("challenges", {})

    if len(sys.argv) >= 2:
        season_number = sys.argv[1]
    else:
        season_number = get_latest_season(challenges)

    format_prefix = f"s{season_number}_"
    challenge_data_output = {}

    eliteChallenges = data.get("eliteChallenges", {})
    challengeDefinitions = data.get("challengeDefinitions", {})

    print(f"Processing season {season_number} challenges...")

    # Process each challenge
    for challenge in challenges.values():
        challengeId = challenge.get("id", "")

        # Check if challengeId starts with the current season
        if not challengeId.startswith(
            format_prefix.lower()
        ) and challengeId not in {"coinChallenge", "dailyChallenge"}:

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
                    for definition in challengeDefinitions.values()
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

                rewardTiers = matching_definition.get("rewardTiers", [])

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


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
