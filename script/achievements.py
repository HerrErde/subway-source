import json

input_file_path = "temp/gamedata/achievements.json"
output_file_path = "temp/upload/achievements_data.json"


def main():
    with open(input_file_path, "r", encoding="utf-8") as input_file:
        data = json.load(input_file)

    output_data = []
    achievement_data = data.get("achievementData", {})

    for _, achievements_data in achievement_data.items():
        objective = achievements_data.get("objective", {})
        achievement_id = objective.get("id", "")
        tier_goals = achievements_data.get("tierGoals", [])
        badge_icon_id = achievements_data.get("badgeIconId")

        entry = {"id": achievement_id, "tierGoals": tier_goals}
        if badge_icon_id:
            entry["badgeIconId"] = badge_icon_id

        output_data.append(entry)

    with open(output_file_path, "w", encoding="utf-8") as output_file:
        json.dump(output_data, output_file, indent=2)


if __name__ == "__main__":
    main()
