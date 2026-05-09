import json
import unicodedata

from rapidfuzz import fuzz

json_input = "temp/output/playerprofile_output.json"
json_input_links = "temp/upload/playerprofile_links.json"
json_output = "temp/upload/playerprofile_data.json"
products_file = "temp/gamedata/products.json"


def read_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def normalize_string(input_string):
    normalized = (
        unicodedata.normalize("NFKD", input_string)
        .encode("ASCII", "ignore")
        .decode("utf-8")
    )
    return normalized


def normalize_name(name):
    normalized = normalize_string(name)
    normalized = normalized.replace(" ", "").lower()
    normalized = normalized.replace("graffiti", "")
    return normalized


def extract_name(profile_str):
    name = profile_str.split("_")[0]
    normalized_name = normalize_name(name)
    return normalized_name


def create_name_list(data_list):
    name_list = [normalize_name(item["name"]) for item in data_list]
    return name_list


def calculate_similarity(name1, name2):
    similarity = fuzz.ratio(name1, name2)
    return similarity


def match_profiles(profiles, name_list):
    matched_profiles = []
    unmatched_profiles = []

    for profile in profiles:
        profile_name = extract_name(profile)
        best_match = None
        best_score = 0
        for name in name_list:
            if profile_name[:3] == name[:3]:
                score = calculate_similarity(profile_name, name)
                if score > best_score:
                    best_score = score
                    best_match = name
        if best_match:
            matched_profiles.append((profile, best_match, best_score))
        else:
            unmatched_profiles.append(profile)

    return matched_profiles, unmatched_profiles


def sort_profiles(matched_profiles, name_list):
    matched_profiles.sort(key=lambda x: (-x[2], name_list.index(x[1])))
    sorted_profiles = [profile for profile, _, _ in matched_profiles]
    return sorted_profiles


def match_frames(frames, name_list):
    matched_frames = []
    unmatched_frames = []

    for frame in frames:
        frame_name = normalize_name(frame)
        best_match = None
        best_score = 0
        for name in name_list:
            if frame_name[:3] == name[:3]:
                score = calculate_similarity(frame_name, name)
                if score > best_score:
                    best_score = score
                    best_match = name
        if best_match:
            matched_frames.append((frame, best_match, best_score))
        else:
            unmatched_frames.append(frame)

    return matched_frames, unmatched_frames


def sort_frames(matched_frames, name_list):
    matched_frames.sort(key=lambda x: (-x[2], name_list.index(x[1])))
    sorted_frames = [frame for frame, _, _ in matched_frames]
    return sorted_frames


def main():
    profile_data = read_json(json_input)
    link_data = read_json(json_input_links)

    name_list_portraits = create_name_list(link_data["Portraits"])
    name_list_frames = create_name_list(link_data["Frames"])

    matched_profiles, unmatched_profiles = match_profiles(
        profile_data["profilePortraits"], name_list_portraits
    )
    sorted_portraits = (
        sort_profiles(matched_profiles, name_list_portraits) + unmatched_profiles
    )

    matched_frames, unmatched_frames = match_frames(
        profile_data["profileFrames"], name_list_frames
    )
    sorted_frames = sort_frames(matched_frames, name_list_frames) + unmatched_frames

    sorted_backgrounds = profile_data["profileBackgrounds"]

    sorted_output = {
        "profilePortraits": sorted_portraits,
        "profileFrames": sorted_frames,
        "profileBackgrounds": sorted_backgrounds,
    }

    with open(json_output, "w", encoding="utf-8") as f:
        json.dump(sorted_output, f, indent=2)


if __name__ == "__main__":
    main()
