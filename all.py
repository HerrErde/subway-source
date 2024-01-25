import subprocess
import requests
import os
import shutil
import time
import glob


def version():
    url = "https://gplayapi.cashlessconsumer.in/api/apps/com.kiloo.subwaysurf"
    response = requests.get(url)
    data = response.json()
    return data.get("version", "").replace(".", "-")


rm_file = [
    "*.apk",
    "subwaysurfers-*.zip",
    "*_output.json",
    "*_data_old.json",
    "update.txt",
]

rm_dir = ["upload", "gamedata"]

scripts = [
    ["script/fetch_links.py"],
    ["script/fetch_outfits.py"],
    ["script/down-apk.py", version()],
    ["misc/unpack.py", version()],
    ["script/fetch_characters.py"],
    ["script/fetch_boards.py"],
    ["script/collection.py"],
    ["script/calender.py"],
    ["misc/sort_characters.py"],
    ["misc/sort_boards.py"],
    ["misc/check.py"],
]

delay = 5


def cleanup():
    print(f"Starting cleanup\n")
    try:
        for pattern in rm_file:
            for file in glob.glob(pattern):
                if os.path.exists(file):
                    os.remove(file)

        for directory in rm_dir:
            if os.path.exists(directory):
                shutil.rmtree(directory)
        print(f"Finished cleanup\n")
    except KeyboardInterrupt:
        print("Cleanup interrupted by user.")
        raise


def run_scripts():
    try:
        os.makedirs("upload", exist_ok=True)
        for script in scripts:
            print(f"Running {script[0]}...")
            subprocess.run(["python"] + script, check=True)
            print(f"Finished running {script[0]}.\n")
            time.sleep(delay)
    except KeyboardInterrupt:
        print("Script execution interrupted by user.")
        raise


try:
    cleanup()
    run_scripts()
except KeyboardInterrupt:
    print("Script terminated by user.")
