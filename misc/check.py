import os
import json
import requests

org_name = "HerrErde"
repo_name = "subway-source"

files = [
    "boards_data.json",
    "characters_data.json",
]

new_characters = "characters_data.json"
old_characters = "characters_data_old.json"

new_boards = "boards_data.json"
old_boards = "boards_data_old.json"
output_file_name = "update.txt"


def download_latest_files():
    base_url = f"https://github.com/{org_name}/{repo_name}/releases/latest/download/"
    for file in files:
        url = f"{base_url}{file}"
        download_file(url, file[:-5] + "_old.json")


def download_file(url, filename):
    with requests.Session() as session:
        response = session.get(url)
        response.raise_for_status()
        with open(filename, "wb") as file:
            file.write(response.content)


def compare_characters(new_file, old_file, output_file):
    with open(old_file, "r") as f:
        old_data = json.load(f)

    with open(new_file, "r") as f:
        new_data = json.load(f)

    old_ids = {entry["id"] for entry in old_data}
    new_ids = {entry["id"] for entry in new_data}

    added_ids = new_ids - old_ids

    if not added_ids:
        return

    with open(output_file, "a") as f:
        f.write(f"- Added Characters: {added_ids}\n")

        for entry in new_data:
            id_val = entry["id"]
            old_entry = next(
                (old_entry for old_entry in old_data if old_entry["id"] == id_val), None
            )

            if old_entry:
                old_outfits = old_entry["outfits"]
                new_outfits = entry["outfits"]

                if old_outfits != new_outfits:
                    added_outfits = {
                        outfit["id"]
                        for outfit in new_outfits
                        if outfit not in old_outfits
                    }
                    for outfit in added_outfits:
                        f.write(f"- Added Outfit {outfit} ({id_val})\n")


def compare_boards(new_file, old_file, output_file):
    with open(old_file, "r") as f:
        old_data = json.load(f)

    with open(new_file, "r") as f:
        new_data = json.load(f)

    old_ids = {entry["id"] for entry in old_data}
    new_ids = {entry["id"] for entry in new_data}

    added_ids = new_ids - old_ids

    if not added_ids:
        return

    with open(output_file, "a") as f:
        f.write(f"- Added Boards: {added_ids}\n")

        for entry in new_data:
            id_val = entry["id"]
            old_entry = next(
                (old_entry for old_entry in old_data if old_entry["id"] == id_val), None
            )

            if old_entry:
                old_upgrades = old_entry["upgrades"]
                new_upgrades = entry["upgrades"]

                if old_upgrades != new_upgrades:
                    added_upgrades = {
                        upgrade["id"]
                        for upgrade in new_upgrades
                        if upgrade not in old_upgrades
                    }
                    for upgrade in added_upgrades:
                        f.write(f"- Added Upgrade {upgrade} ({id_val})\n")


if __name__ == "__main__":
    download_latest_files()
    with open(output_file_name, "w") as output_file:
        compare_characters(new_characters, old_characters, output_file_name)
        compare_boards(new_boards, old_boards, output_file_name)
