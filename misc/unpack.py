import os
import subprocess
import shutil
import sys
import re
import zipfile


def extract_from_zip(zip_file, extract_folder):
    with zipfile.ZipFile(zip_file, "r") as zf:
        if "base.apk" in zf.namelist():
            zf.extract("base.apk")
            subprocess.run(["unzip", "base.apk", f"{extract_folder}/*"])
        else:
            subprocess.run(["unzip", zip_file, f"{extract_folder}/*"])


def main(version, appName):
    # Specify the path to the .apk file
    apk_file = f"{appName}-{version}.apk"
    print(apk_file)

    # Specify the folder to be extracted
    extract_folder = "assets/tower/gamedata"

    # Check if the specified file exists
    if not os.path.isfile(apk_file):
        print("Error: The specified .apk file does not exist.")
        exit(1)

    # Rename the .apk file to .zip
    zip_file = f"{os.path.splitext(apk_file)[0]}.zip"
    os.rename(apk_file, zip_file)

    # Extract from the zip file
    extract_from_zip(zip_file, extract_folder)

    print("Unpacking completed!")
    shutil.move(extract_folder, "gamedata/")
    shutil.rmtree("assets/")

    print("Move and deletion completed!")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python unpack.py <version> <appName>")
        exit(1)

    version = sys.argv[1]
    appName = sys.argv[2]

    if not re.match(r"^\d{1,2}-\d{1,2}-\d{1,2}$", version):
        print(
            "Error: Invalid version format. Please use the format 'X-Y-Z' (e.g., '3-12-2')."
        )
        exit(1)

    main(version, appName)
