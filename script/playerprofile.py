import json

input_file_path = "temp/gamedata/playerprofile.json"
output_file_path = "temp/output/playerprofile_output.json"


with open(input_file_path) as file:
    json_data = json.load(file)

profile_portraits_ids = []
profile_frames_ids = []
profile_backgrounds_ids = []

# Extract the "id" data for profilePortraits
profile_portraits_data = json_data.get("profilePortraits", {})
profile_portraits_ids = [data["id"] for data in profile_portraits_data.values()]

# Extract the "id" data for profileFrames
profile_frames_data = json_data.get("profileFrames", {})
profile_frames_ids = [data["id"] for data in profile_frames_data.values()]

# Extract the "id" data for profileBackgrounds
profile_backgrounds_data = json_data.get("profileBackgrounds", {})
profile_backgrounds_ids = [data["id"] for data in profile_backgrounds_data.values()]

# Consolidate extracted IDs into a dictionary
extracted_data = {
    "profilePortraits": profile_portraits_ids,
    "profileFrames": profile_frames_ids,
    "profileBackgrounds": profile_backgrounds_ids,
}

with open(output_file_path, "w", encoding="utf-8") as file:
    json.dump(extracted_data, file, indent=2)
