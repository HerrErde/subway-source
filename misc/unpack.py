import os
import re
import shutil
import sys
import zipfile


def extract_zip(zip_file, extract_folder):
    with zipfile.ZipFile(zip_file, "r") as zf:
        for item in zf.namelist():
            if item.startswith(extract_folder):
                zf.extract(item, "")


def find_base(zip_file):
    with zipfile.ZipFile(zip_file, "r") as zf:
        for item in zf.namelist():
            if item.startswith("base.apk"):
                return "base.apk"
        return None


def find_extraction_folder(zip_file):
    with zipfile.ZipFile(zip_file, "r") as zf:
        for item in zf.namelist():
            if item.startswith("assets/tower/gamedata"):
                return "assets/tower/gamedata"
        return None


def main(version, app_name):
    # Specify the path to the .apk file
    apk_file = f"{app_name}-{version}.apk"
    print(apk_file)

    # Check if the specified file exists and rename it to .zip
    zip_file = f"{os.path.splitext(apk_file)[0]}.zip"
    try:
        os.rename(apk_file, zip_file)
    except FileNotFoundError:
        print(f"Error: The specified .apk file '{apk_file}' does not exist.")
        exit(1)

    # Check for "assets/tower/gamedata" folder or "base.apk" file
    extract_folder = find_extraction_folder(zip_file)
    extract_base = find_base(zip_file)

    if extract_folder is not None:
        print("Extracting assets/tower/gamedata folder...")
        extract_zip(zip_file, extract_folder)
        print("Extraction completed!")

        target_folder = "gamedata"
        shutil.move(extract_folder, target_folder)
        print("Move completed!")
        shutil.rmtree("assets/")
        print("Deletion completed!")

    elif extract_base is not None:
        print("Extracting base.apk...")
        extract_zip(zip_file, extract_base)
        print("Extraction completed!")

        # Now, extract "assets/tower/gamedata" from the extracted base.apk
        base_apk_folder = find_extraction_folder(extract_base)
        if base_apk_folder is not None:
            print("Extracting assets/tower/gamedata folder from base.apk...")
            extract_zip(extract_base, base_apk_folder)
            print("Extraction completed!")

            target_folder = "gamedata"
            shutil.move(base_apk_folder, target_folder)
            print("Move completed!")
            shutil.rmtree("assets/")
            print("Deletion completed!")

        os.remove(extract_base)

    else:
        print(
            "Error: Neither 'assets/tower/gamedata' folder nor 'base.apk' file found."
        )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python unpack.py <version>")
        exit(1)

    version = sys.argv[1]
    app_name = "subwaysurfers"

    if not re.match(r"^\d{1,2}-\d{1,2}-\d{1,2}$", version):
        print(
            "Error: Invalid version format. Please use the format 'X-Y-Z' (e.g., '3-12-2')."
        )
        exit(1)

    main(version, app_name)