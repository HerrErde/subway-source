import subprocess
import requests
import os
import re
import shutil
import time
import glob
import argparse


def version():
    url = "https://gplayapi.cashlessconsumer.in/api/apps/com.kiloo.subwaysurf"
    response = requests.get(url)
    data = response.json()
    return data.get("version", "").replace(".", "-")


rm_file = [
    "*.apk",
    "*.ipa",
    "subwaysurfers-*.zip",
    "*_output.json",
    "*_data_old.json",
    "update.txt",
]

rm_dir = ["upload", "gamedata"]


def get_scripts(type, version):
    return [
        ["script/fetch_links.py"],
        ["script/fetch_profile.py"],
        ["script/fetch_outfits.py"],
        [f"script/down-{type}.py", version],
        [f"misc/unpack-{type}.py", version],
        ["script/fetch_characters.py"],
        ["script/fetch_boards.py"],
        ["script/playerprofile.py"],
        ["script/userstats.py"],
        ["script/collection.py"],
        ["script/calender.py"],
        ["script/mailbox.py"],
        ["misc/sort_characters.py"],
        ["misc/sort_boards.py"],
        ["misc/check.py"],
    ]


delay = 5


def cleanup():
    print("Starting cleanup")
    try:
        for pattern in rm_file:
            for file in glob.glob(pattern):
                if os.path.exists(file):
                    os.remove(file)

        for directory in rm_dir:
            if os.path.exists(directory):
                shutil.rmtree(directory)
        print("Finished cleanup\n")
    except KeyboardInterrupt:
        print("Cleanup interrupted by user.")
        raise


def run_scripts(type, version):
    scripts = get_scripts(type, version)
    try:
        print(f"Choosing type {type}")
        print(f"Choosing version {version}")
        os.makedirs("upload", exist_ok=True)
        for script in scripts:
            print(f"Running {script[0]}...")
            subprocess.run(["python"] + script, check=True)
            print(f"Finished running {script[0]}.\n")
            time.sleep(delay)
    except KeyboardInterrupt:
        print("Script execution interrupted by user.")
        raise


def extract(type, version):
    try:
        print(f"Choosing type {type}")
        print(f"Downloading {version}...")
        subprocess.run(["python", f"script/down-{type}.py", version], check=True)
        print(f"Extracting {type}...")
        subprocess.run(["python", f"misc/unpack-{type}.py", version], check=True)
    except KeyboardInterrupt:
        print("Script execution interrupted by user.")
        raise


def main():
    parser = argparse.ArgumentParser(description="Run Subway Surfers scripts.")
    parser.add_argument(
        "-c", "--cleanup", action="store_true", help="Run cleanup function only"
    )
    parser.add_argument(
        "-v", "--version", type=str, default=version(), help="Choose a specific version"
    )
    parser.add_argument(
        "-e",
        "--extract",
        action="store_true",
        help="Download and extract the latest apk/ipa",
    )
    parser.add_argument(
        "-t",
        "--type",
        choices=["apk", "ipa"],
        default="ipa",
        help="Choose between type apk and ipa",
    )

    args = parser.parse_args()

    if not re.match(r"^\d{1,2}-\d{1,2}-\d{1,2}$", args.version):
        print(
            "Error: Invalid version format. Please use the format 'X-Y-Z' (e.g., '3-12-2')."
        )
        exit(1)

    if args.cleanup:
        cleanup()
    if args.extract:
        cleanup()
        extract(args.type, args.version)
    else:
        try:
            cleanup()
            run_scripts(args.type, args.version)
        except KeyboardInterrupt:
            print("Script terminated by user.")


if __name__ == "__main__":
    main()
