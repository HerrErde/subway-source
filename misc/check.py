import json
import re
import sys
from pathlib import Path

import requests

org_name = "HerrErde"
repo_name = "subway-source"

files = ["characters_data.json", "boards_data.json", "playerprofile_data.json"]

characters = "characters_data.json"
hoverboards = "boards_data.json"
playerprofile = "playerprofile_data.json"

output_file = "temp/update.txt"
products_file = "temp/gamedata/products.json"
locale_file = "temp/output/en_locale.json"


def download_latest_files(version):
    if version:
        base_url = (
            f"https://github.com/{org_name}/{repo_name}/releases/download/{version}/"
        )
    else:
        base_url = (
            f"https://github.com/{org_name}/{repo_name}/releases/latest/download/"
        )

    for file in files:
        url = f"{base_url}{file}"
        download_file(url, Path("temp") / file.replace(".json", "_old.json"))


def download_file(url, filename):
    filename = Path(filename)
    filename.parent.mkdir(parents=True, exist_ok=True)

    with requests.Session() as session:
        response = session.get(url)
        response.raise_for_status()
        with filename.open("wb") as file:
            file.write(response.content)


def load_product_names(products_path):
    with Path(products_path).open("r", encoding="utf-8") as f:
        data = json.load(f)

    products = data.get("products", {})
    return {
        product_id: product_data.get("name", product_id)
        for product_id, product_data in products.items()
    }


def load_locale(locale_path):
    locale_path = Path(locale_path)
    if not locale_path.exists():
        return {}

    with locale_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_name(product_names, item_id):
    name = product_names.get(item_id)
    if name is not None:
        return str(name)
    if item_id is None:
        return "(missing id)"
    return str(item_id)


def has_valid_id(value):
    return isinstance(value, str) and bool(value)


def prettify_name(value):
    if not has_valid_id(value):
        return "(missing id)"

    value = value.replace("_", " ").replace(".", " ")
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", value)
    return value[:1].upper() + value[1:]


def get_locale_name(locale_data, *keys):
    for key in keys:
        if isinstance(key, str) and key:
            value = locale_data.get(key)
            if isinstance(value, str) and value:
                return value
    return None


def resolve_outfit_name(product_names, locale_data, character_id, outfit):
    outfit_id = outfit.get("id")
    variation = outfit.get("variation") or {}
    variation_name = variation.get("name") if isinstance(variation, dict) else None

    locale_name = get_locale_name(
        locale_data,
        variation_name,
        f"characters.{character_id}.{variation_name}.name" if variation_name else None,
        (
            f"characters.{character_id}.outfits.{variation_name}.name"
            if variation_name
            else None
        ),
        (
            f"characters.{character_id}.variations.{variation_name}.name"
            if variation_name
            else None
        ),
        f"characters.{character_id}.{outfit_id}.name" if outfit_id else None,
        f"characters.{character_id}.outfits.{outfit_id}.name" if outfit_id else None,
        f"characters.{character_id}.variations.{outfit_id}.name" if outfit_id else None,
        f"characters.{variation_name}.name" if variation_name else None,
        f"characters.{outfit_id}.name" if outfit_id else None,
    )
    if locale_name:
        return locale_name

    product_name = get_name(product_names, outfit_id)
    if product_name != str(outfit_id):
        return product_name

    if isinstance(variation_name, str) and variation_name:
        return prettify_name(variation_name)

    return prettify_name(outfit_id)


def compare_characters(file, output_file, product_names, locale_data):
    old_file = file.replace(".json", "_old.json")

    with open(f"temp/{old_file}", "r", encoding="utf-8") as f:
        old_data = json.load(f)

    with open(f"temp/upload/{file}", "r", encoding="utf-8") as f:
        new_data = json.load(f)

    old_ids = {entry["id"] for entry in old_data if has_valid_id(entry.get("id"))}
    new_ids = {entry["id"] for entry in new_data if has_valid_id(entry.get("id"))}

    added_ids = new_ids - old_ids

    with open(output_file, "a", encoding="utf-8") as f:
        if added_ids:
            added_names = [
                get_name(product_names, item_id) for item_id in sorted(added_ids)
            ]
            f.write("- Added Characters " + ", ".join(added_names) + "\n")

        for entry in new_data:
            id_val = entry.get("id")
            if not has_valid_id(id_val):
                continue

            old_entry = next(
                (old_entry for old_entry in old_data if old_entry["id"] == id_val), None
            )

            if old_entry:
                old_outfits = {
                    outfit["id"]
                    for outfit in (old_entry.get("outfits", []) or [])
                    if has_valid_id(outfit.get("id"))
                }
                new_outfits = {
                    outfit["id"]: outfit
                    for outfit in (entry.get("outfits", []) or [])
                    if has_valid_id(outfit.get("id"))
                }

                added_outfits = set(new_outfits) - old_outfits
                if added_outfits:
                    added_outfit_names = [
                        resolve_outfit_name(
                            product_names,
                            locale_data,
                            entry["id"],
                            new_outfits[outfit_id],
                        )
                        for outfit_id in sorted(added_outfits)
                    ]
                    character_name = get_name(product_names, entry["id"])
                    f.write(
                        f"- Added Outfit {', '.join(added_outfit_names)} ({character_name})\n"
                    )


def compare_boards(file, output_file, product_names):
    old_file = file.replace(".json", "_old.json")

    with open(f"temp/{old_file}", "r", encoding="utf-8") as f:
        old_data = json.load(f)

    with open(f"temp/upload/{file}", "r", encoding="utf-8") as f:
        new_data = json.load(f)

    def resolve_name(board_id):
        if board_id in product_names:
            return get_name(product_names, board_id)

        dotted_default = f"{board_id}.default"
        if dotted_default in product_names:
            return get_name(product_names, dotted_default)

        underscored_default = f"{board_id}_default"
        if underscored_default in product_names:
            return get_name(product_names, underscored_default)

        return get_name(product_names, board_id)

    old_ids = {entry["id"] for entry in old_data}
    new_ids = {entry["id"] for entry in new_data}

    added_ids = new_ids - old_ids

    with open(output_file, "a", encoding="utf-8") as f:
        if added_ids:
            added_names = [resolve_name(item_id) for item_id in sorted(added_ids)]
            f.write("- Added Boards " + ", ".join(added_names) + "\n")

        for entry in new_data:
            id_val = entry["id"]
            old_entry = next(
                (old_entry for old_entry in old_data if old_entry["id"] == id_val), None
            )

            if old_entry:
                old_upgrades = {
                    upgrade["id"] for upgrade in (old_entry.get("upgrades", []) or [])
                }
                new_upgrades = {
                    upgrade["id"] for upgrade in (entry.get("upgrades", []) or [])
                }

                added_upgrades = new_upgrades - old_upgrades
                if added_upgrades:
                    added_upgrade_names = [
                        resolve_name(upgrade_id)
                        for upgrade_id in sorted(added_upgrades)
                    ]
                    board_name = resolve_name(entry["id"])
                    f.write(
                        "- Added Upgrades "
                        + board_name
                        + ": "
                        + ", ".join(added_upgrade_names)
                        + "\n"
                    )


def compare_profile(file, output_file, product_names):
    old_file = file.replace(".json", "_old.json")

    with open(f"temp/{old_file}", "r", encoding="utf-8") as f:
        old_data = json.load(f)

    with open(f"temp/upload/{file}", "r", encoding="utf-8") as f:
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

    with open(output_file, "a", encoding="utf-8") as f:
        if added_portrait:
            names = [
                get_name(product_names, item_id) for item_id in sorted(added_portrait)
            ]
            f.write("- Added Portraits: " + ", ".join(names) + "\n")
        if added_frame:
            names = [
                get_name(product_names, item_id) for item_id in sorted(added_frame)
            ]
            f.write("- Added Frames: " + ", ".join(names) + "\n")
        if added_background:
            names = [
                get_name(product_names, item_id) for item_id in sorted(added_background)
            ]
            f.write("- Added Backgrounds: " + ", ".join(names) + "\n")


if __name__ == "__main__":
    version = None
    if len(sys.argv) > 1:
        version = sys.argv[1]
        version = version.replace(".", "-")

    product_names = load_product_names(products_file)
    locale_data = load_locale(locale_file)

    download_latest_files(version)

    open(output_file, "w", encoding="utf-8").close()

    compare_characters(characters, output_file, product_names, locale_data)
    compare_boards(hoverboards, output_file, product_names)
    compare_profile(playerprofile, output_file, product_names)
