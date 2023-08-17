import subprocess
import time
import requests


def version():
    # get version from gplayapi
    response = requests.get("https://gplayapi.herrerde.xyz/api/apps/com.kiloo.subwaysurf")
    data = response.json()
    version = data["version"].replace(".", "-")

    return version


scripts = [
    #["misc/fetch_links.py"],
    ["script/down-apk.py", version()],
    ["misc/unpack.py", version(), "subwaysurfers"],
    ["script/fetch_characters.py"],
    ["script/fetch_boards.py"],
    ["misc/sort_characters.py"],
    ["misc/sort_boards.py"],
    #["misc/check.py"],
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
