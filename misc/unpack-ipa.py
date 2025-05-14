import os
import re
import shutil
import sys
import zipfile


def extract_zip(zip_file, extract_folder, output_folder):
    with zipfile.ZipFile(zip_file, "r") as zf:
        for item in zf.namelist():
            # If the item is within the extract_folder, process it
            if item.startswith(extract_folder):
                # Get the relative path, starting after the extract_folder
                relative_path = os.path.relpath(item, extract_folder)

                # Build the target path in the output_folder
                target_path = os.path.join(output_folder, relative_path)

                if item.endswith("/"):
                    # If the item is a directory, create it
                    os.makedirs(target_path, exist_ok=True)
                else:
                    # If the item is a file, extract it
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    with zf.open(item) as source, open(target_path, "wb") as target:
                        shutil.copyfileobj(source, target)


def main(version, app_name):
    # Specify the path to the .ipa file
    ipa_file = f"temp/{app_name}-{version}.ipa"

    # Check if the specified file exists and rename it to .zip
    zip_file = f"{os.path.splitext(ipa_file)[0]}.zip"
    try:
        os.rename(ipa_file, zip_file)
    except FileNotFoundError:
        print(f"Error: The specified .ipa file '{ipa_file}' does not exist.")
        sys.exit(1)
    extract_folder = "Payload/SubwaySurf.app/Data/Raw/tower/gamedata"
    target_folder = "temp/gamedata"

    print(f"Extracting {extract_folder} folder...")
    extract_zip(zip_file, extract_folder, target_folder)
    print("Extraction completed!")
    os.rename(zip_file, ipa_file)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python unpack.py <version>")
        sys.exit(1)

    version = sys.argv[1]
    app_name = "subway-surfers"

    if not re.match(r"^\d{1,2}-\d{1,2}-\d{1,2}$", version):
        print(
            "Error: Invalid version format. Please use the format 'X-Y-Z' (e.g., '3-12-2')."
        )
        exit(1)

    main(version, app_name)
