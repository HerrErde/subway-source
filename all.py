import subprocess
import time

scripts = [
    ["misc/fetch_links.py"],
    ["script/down-apk.py", "3-13-2"],
    ["misc/unpack.py", "3-13-2", "subwaysurfers"],
    ["script/fetch_characters.py"],
    ["script/fetch_boards.py"],
    ["misc/sort_characters.py"],
    ["misc/sort_boards.py"],
    # ["misc/check.py"],
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
