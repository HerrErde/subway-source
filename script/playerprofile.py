import json

input_file_path = "temp/gamedata/playerprofile.json"
output_file_path = "temp/output/playerprofile_output.json"

with open(input_file_path, encoding="utf-8") as file:
    json_data = json.load(file)

profile_portraits_ids = [
    data["id"]
    for data in json_data.get("profilePortraits", {}).values()
    if "id" in data
]

profile_frames_ids = [
    data["id"] for data in json_data.get("profileFrames", {}).values() if "id" in data
]

profile_backgrounds_ids = [
    data["id"]
    for data in json_data.get("profileBackgrounds", {}).values()
    if "id" in data
]

extracted_data = {
    "profilePortraits": profile_portraits_ids,
    "profileFrames": profile_frames_ids,
    "profileBackgrounds": profile_backgrounds_ids,
}

with open(output_file_path, "w", encoding="utf-8") as file:
    json.dump(extracted_data, file, indent=2)
