import os
import json
import requests

org_name = "HerrErde"
repo_name = "subway-source"

files = ["characters_data.json", "boards_data.json", "playerprofile_data.json"]

characters = "characters_data.json"
hoverboards = "boards_data.json"
playerprofile = "playerprofile_data.json"

output_file = "temp/update.txt"


def download_latest_files():
    base_url = f"https://github.com/{org_name}/{repo_name}/releases/latest/download/"
    # base_url = f"https://github.com/{org_name}/{repo_name}/releases/download/3-32-0/" # specific version
    for file in files:
        url = f"{base_url}{file}"
        download_file(url, "temp/" + file.replace(".json", "_old.json"))


def download_file(url, filename):
    directory = os.path.dirname(filename)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with requests.Session() as session:
        response = session.get(url)
        response.raise_for_status()
        with open(filename, "wb") as file:
            file.write(response.content)


def compare_characters(file, output_file):
    old_file = file.replace(".json", "_old.json")

    with open(f"temp/{old_file}", "r") as f:
        old_data = json.load(f)

    with open(f"temp/upload/{file}", "r") as f:
        new_data = json.load(f)

    old_ids = {entry["id"] for entry in old_data}
    new_ids = {entry["id"] for entry in new_data}

    added_ids = new_ids - old_ids

    if not added_ids:
        return

    with open(output_file, "a") as f:
        f.write("- Added Characters " + ", ".join(added_ids) + "\n")

        for entry in new_data:
            id_val = entry["id"]
            old_entry = next(
                (old_entry for old_entry in old_data if old_entry["id"] == id_val), None
            )

            if old_entry:
                old_outfits = {outfit["id"] for outfit in old_entry.get("outfits", [])}
                new_outfits = {outfit["id"] for outfit in entry.get("outfits", [])}

                added_outfits = new_outfits - old_outfits
                if added_outfits:
                    f.write(
                        f"- Added Outfit {', '.join(added_outfits)} ({entry['id']})\n"
                    )


def compare_boards(file, output_file):
    old_file = file.replace(".json", "_old.json")

    with open(f"temp/{old_file}", "r") as f:
        old_data = json.load(f)

    with open(f"temp/upload/{file}", "r") as f:
        new_data = json.load(f)

    old_ids = {entry["id"] for entry in old_data}
    new_ids = {entry["id"] for entry in new_data}

    added_ids = new_ids - old_ids

    if not added_ids:
        return

    with open(output_file, "a") as f:
        f.write("- Added Boards " + ", ".join(added_ids) + "\n")

        for entry in new_data:
            id_val = entry["id"]
            old_entry = next(
                (old_entry for old_entry in old_data if old_entry["id"] == id_val), None
            )

            if old_entry:
                old_upgrades = {
                    upgrade["id"] for upgrade in old_entry.get("upgrades", []) or []
                }
                new_upgrades = {
                    upgrade["id"] for upgrade in entry.get("upgrades", []) or []
                }

                added_upgrades = new_upgrades - old_upgrades
                if added_upgrades:
                    f.write(
                        "- Added Upgrades "
                        + entry.get("name", "Unknown Name")
                        + ": "
                        + ", ".join(added_upgrades)
                        + "\n"
                    )


def compare_profile(file, output_file):
    old_file = file.replace(".json", "_old.json")

    with open(f"temp/{old_file}", "r") as f:
        old_data = json.load(f)

    with open(f"temp/upload/{file}", "r") as f:
        new_data = json.load(f)

    added_portrait = set(new_data["profilePortraits"]) - set(
        old_data["profilePortraits"]
    )
    added_frame = set(new_data["profileFrames"]) - set(old_data["profileFrames"])
    added_background = set(new_data["profileBackgrounds"]) - set(
        old_data["profileBackgrounds"]
    )

    if not added_portrait and not added_frame and not added_background:
        return

    with open(output_file, "a") as f:
        if added_portrait:
            f.write("- Added Portraits: " + ", ".join(added_portrait) + "\n")
        if added_frame:
            f.write("- Added Frames: " + ", ".join(added_frame) + "\n")
        if added_background:
            f.write("- Added Backgrounds: " + ", ".join(added_background) + "\n")


if __name__ == "__main__":
    download_latest_files()
    with open(output_file, "w") as file:
        compare_characters(characters, output_file)
        compare_boards(hoverboards, output_file)
        compare_profile(playerprofile, output_file)
