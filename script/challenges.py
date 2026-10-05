import json
import re
import sys

input_file_path = "temp/gamedata/challenges.json"
output_file_path = "temp/upload/challenges_data.json"

# s124_london_mrt and season_S124_subwayshowdown_season -> 124
SEASON_RE = re.compile(r"s(?:eason_S)?(\d+)_", re.IGNORECASE)
# no season prefix, but they always belong to the current season
SEASONLESS_IDS = {"coinChallenge", "dailyChallenge"}


def read_json(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def get_latest_season(challenges):
    seasons = [
        int(match.group(1))
        for match in (
            SEASON_RE.match(challenge.get("id", ""))
            for challenge in challenges.values()
        )
        if match
    ]
    if not seasons:
        raise ValueError(
            "Unable to determine season: no season-prefixed challenge IDs found"
        )
    return max(seasons)


def is_current_season(challenge_id, season_number):
    return challenge_id in SEASONLESS_IDS or challenge_id.lower().startswith(
        (f"s{season_number}_", f"season_s{season_number}_")
    )


def main():
    data = read_json(input_file_path)
    challenges = data.get("challenges", {})

    season_number = sys.argv[1] if len(sys.argv) > 1 else get_latest_season(challenges)
    season_number = str(season_number).strip().lower().lstrip("s")

    definitions = {
        definition.get("id", "").lower(): definition
        for definition in data.get("challengeDefinitions", {}).values()
    }

    challenge_data_output = {}

    for challenge_id, challenge in challenges.items():
        if not is_current_season(challenge_id, season_number):
            continue

        # the timeslot lives on the set entry, not on the challenge itself
        sets = [
            entry
            for entry in challenge.get("seasonChallengeSets", [])
            if entry.get("challenges")
        ]
        set_entry = sets[0] if sets else {}
        timeSlot = set_entry.get("timeSlot", "")

        definition = definitions.get(set_entry.get("challenges", [""])[0].lower(), {})

        challenge_data_output[challenge_id] = {
            "gameMode": challenge.get("gameMode", ""),
            "matchmakingId": challenge.get("matchmakingId", ""),
            "kind": challenge.get("kind", ""),
            "targetCity": challenge.get("targetCity", ""),
            "accessRequirement": challenge.get("accessRequirement", {}),
            "visibilityRequirement": challenge.get("visibilityRequirement", []),
            "participationRequirement": definition.get("participationRequirement", {}),
            "rewardTiers": definition.get("rewardTiers", []),
            "serverId": challenge.get("serverId", ""),
            "headerTitleKey": challenge.get("ui", {}).get("headerTitleKey", ""),
            "rewardUnlockOffset": definition.get("groupRewardUnlockOffset", []),
            "currentSetEntryID": set_entry.get("challenges", [""])[0],
            "currentSetEntryTimeSlot": timeSlot,
            "timeSlot": timeSlot,
            "sunsetPeriod": challenge.get("sunsetPeriod", ""),
            "skipStageCost": challenge.get("skipStageCost", ""),
        }

    output_data = {
        "challenges": challenge_data_output,
        "eliteChallenges": data.get("eliteChallenges", {}),
    }

    with open(output_file_path, "w", encoding="utf-8") as output_file:
        json.dump(output_data, output_file, indent=2)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
