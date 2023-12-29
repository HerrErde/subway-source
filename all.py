import subprocess
import requests
import os
import shutil
import time


def version():
    url = "https://gplayapi.cashlessconsumer.in/api/apps/com.kiloo.subwaysurf"
    response = requests.get(url)
    data = response.json()
    return data.get("version", "").replace(".", "-")


rm_file = [
    "base.apk",
    f"subwaysurfers-{version()}.zip",
    "boards_output.json",
    "boards_data_old.json",
    "characters_output.json",
    "characters_data_old.json",
    "update.txt",
]

rm_dir = ["upload", "gamedata"]


for file in rm_file:
    if os.path.exists(file):
        os.remove(file)


for directory in rm_dir:
    if os.path.exists(directory):
        shutil.rmtree(directory)

if not os.path.exists("upload"):
    os.mkdir("upload")

scripts = [
    ["script/fetch_links.py"],
    ["script/fetch_outfits.py"],
    ["script/down-apk.py", version()],
    ["misc/unpack.py", version()],
    ["script/fetch_characters.py"],
    ["script/fetch_boards.py"],
    ["script/collections.py"],
    ["script/calender.py"],
    ["misc/sort_characters.py"],
    ["misc/sort_boards.py"],
    ["misc/check.py"],
]

delay = 5


def run_scripts():
    for script in scripts:
        print(f"Running {script[0]}...")
        subprocess.run(["python"] + script, check=True)
        print(f"Finished running {script[0]}.\n")
    time.sleep(delay)


run_scripts()
