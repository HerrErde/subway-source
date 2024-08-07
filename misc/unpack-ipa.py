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


def find_extraction_folder(zip_file):
    with zipfile.ZipFile(zip_file, "r") as zf:
        for item in zf.namelist():
            if item.startswith("Payload/SubwaySurf.app/Data/Raw/tower/gamedata"):
                return "Payload/SubwaySurf.app/Data/Raw/tower/gamedata"
        return None


def main(version, app_name):
    # Specify the path to the .apk file
    ipa_file = f"temp/{app_name}-{version}.ipa"
    print(ipa_file)

    # Check if the specified file exists and rename it to .zip
    zip_file = f"{os.path.splitext(ipa_file)[0]}.zip"
    try:
        os.rename(ipa_file, zip_file)
    except FileNotFoundError:
        print(f"Error: The specified .ipa file '{ipa_file}' does not exist.")
        exit(1)

    # Check for "assets/tower/gamedata" folder or "base.apk" file
    extract_folder = find_extraction_folder(zip_file)

    if extract_folder is not None:
        print("Extracting assets/tower/gamedata folder...")
        extract_zip(zip_file, extract_folder)
        print("Extraction completed!")

        target_folder = "temp/gamedata"
        shutil.move(extract_folder, target_folder)
        print("Move completed!")
        shutil.rmtree("Payload/")
        print("Deletion completed!")
        os.rename(zip_file, ipa_file)

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
