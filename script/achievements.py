import json

input_file_path = "temp/gamedata/achievements.json"
output_file_path = "temp/upload/achievements_data.json"

with open(input_file_path, "r", encoding="utf-8") as input_file:
    data = json.load(input_file)

output_data = []
achievement_data = data.get("achievementData", {})

for _, achievements_data in achievement_data.items():
    objective = achievements_data.get("objective", {})
    id = objective.get("id", "")
    tierGoals = achievements_data.get("tierGoals", [])
    badgeIconId = achievements_data.get("badgeIconId")

    entry = {"id": id, "tierGoals": tierGoals}
    if badgeIconId:
        entry["badgeIconId"] = badgeIconId

    output_data.append(entry)

with open(output_file_path, "w", encoding="utf-8") as output_file:
    json.dump(output_data, output_file, indent=2)
