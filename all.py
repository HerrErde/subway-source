import argparse
import glob
import os
import re
import shutil
import subprocess
import time
import requests


def setup(extract):
    if extract:
        os.makedirs("temp", exist_ok=True)
    else:
        os.makedirs("temp/output", exist_ok=True)
        os.makedirs("temp/upload", exist_ok=True)


def get_session():
    import browser_cookie3

    # Retrieve Firefox cookies
    cookies = browser_cookie3.firefox(domain_name="armconverter.com")

    # Filter for session cookies
    session_cookies = [cookie for cookie in cookies if not cookie.expires]

    # Return the session cookies values
    session_cookie_values = [cookie.value for cookie in session_cookies]

    # Print the session cookies values
    for value in session_cookie_values:
        print(value)

    # Return the first session cookie value (or handle differently if needed)
    if session_cookie_values:
        return session_cookie_values[0]
    else:
        return None  # or handle no session cookies found case


def version():
    url = "https://gplayapi.cashlessconsumer.in/api/apps/com.kiloo.subwaysurf"
    response = requests.get(url)
    data = response.json()
    return data.get("version", "").replace(".", "-")


def get_rm(nodownload):
    rm_file = [
        "*.apk",
        "subwaysurfers-*.zip",
        "*_output.json",
        "*_data_old.json",
        "update.txt",
    ]

    rm_dir = []

    if not nodownload:
        ipa_file = "*.ipa"
        rm_file.insert(0, ipa_file)
        tmp_dir = "temp"
        rm_dir.insert(0, tmp_dir)

    return rm_file, rm_dir


def get_scripts(type, version, session, nodownload):
    if type == "apk":
        session = ""
    return [
        [f"script/down-{type}.py", version, session],
        [f"misc/unpack-{type}.py", version],
        ["script/fetch_links.py"],
        ["script/fetch_profile.py"],
        ["script/fetch_outfits.py"],
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

    if not nodownload:
        download_script = [f"script/down-{type}.py", version, session[0]]
        script_list.insert(0, download_script)

    return script_list


def cleanup(nodownload):
    print("Starting cleanup")
    rm_file, rm_dir = get_rm(nodownload)

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


def run_scripts(type, version, nodownload, delay):
    session = ""
    if nodownload:
        pass
    else:
        session = get_session()
    scripts = get_scripts(type, version, session, nodownload)
    try:
        print(f"Choosing typ: {type}")
        print(f"Choosing version: {version}")

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
        if type == "apk":
            session = ""
        else:
            session = get_session()
        print(f"Choosing type {type}")
        print(f"Downloading {version}...")
        subprocess.run(
            ["python", f"script/down-{type}.py", version, session], check=True
        )
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
    parser.add_argument(
        "-nd",
        "--nodownload",
        action="store_true",
        help="Run scripts without downloading game file (Game has to be downloaded beforehand)",
    )
    parser.add_argument(
        "-dly",
        "--delay",
        type=int,
        default=5,
        help="Change the delay between the running scripts",
    )

    args = parser.parse_args()

    if not re.match(r"^\d{1,2}-\d{1,2}-\d{1,2}$", args.version):
        print(
            "Error: Invalid version format. Please use the format 'X-Y-Z' (e.g., '3-12-2')."
        )
        exit(1)

    try:
        if args.cleanup:
            cleanup(args.nodownload)
        elif args.extract:
            cleanup(args.nodownload)
            setup(True)
            extract(args.type, args.version)
        else:
            cleanup(args.nodownload)
            setup(False)
            run_scripts(args.type, args.version, args.nodownload, args.delay)
    except Exception as e:
        print("Error:", e)
        raise
    except KeyboardInterrupt:
        print("Script terminated by user.")
        raise


if __name__ == "__main__":
    main()
