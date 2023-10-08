import subprocess
import time
import requests
import os
import shutil


def version():
    # get version from gplayapi
    response = requests.get(
        "https://gplayapi.cashlessconsumer.in/api/apps/com.kiloo.subwaysurf"
    )
    data = response.json()
    version = data["version"].replace(".", "-")

    return version


# Check if the "gamedata" directory exists and delete it if it does
if os.path.exists("gamedata"):
    shutil.rmtree("gamedata")

# Create the "upload" directory if it doesn't exist
if not os.path.exists("upload"):
    os.mkdir("upload")

scripts = [
    #["script/fetch_links.py"],
    #["script/fetch_outfits.py"],
    #["script/down-apk.py", version()],
    #["misc/unpack.py", version(), "subwaysurfers"],
    #["script/fetch_characters.py"],
    #["script/fetch_boards.py"],
    #["script/collections.py"],
    ["misc/sort_characters.py"],
    ["misc/sort_boards.py"],
    ["misc/check.py"],
    # Add more script commands and arguments as needed
]

delay = 5


def run_scripts():
    start_time = time.time()  # Record the start time
    for script in scripts:
        print(f"Running {script}...")
        subprocess.run(["python"] + script, check=True)
        print(f"Finished running {script}.\n")
    time.sleep(delay)


run_scripts()
