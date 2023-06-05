import os
import requests
import subprocess
import shutil
import sys
import re


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

    # Unpack the .zip file to the temporary directory
    subprocess.run(["unzip", zip_file, "base.apk"])
    subprocess.run(["unzip", "base.apk", f"{extract_folder}/*"])

    print("Unpacking completed!")
    shutil.move(extract_folder, "gamedata/")
    shutil.rmtree("assets/")

    print("Move and deletion completed!")

    os.rename(zip_file, apk_file)


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
