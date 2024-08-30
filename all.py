import argparse
import glob
import os
import re
import shutil
import subprocess
import time
import requests
import sys


def setup(extract, onlydownload):
    if extract:
        os.makedirs("temp", exist_ok=True)
    if onlydownload:
        os.makedirs("temp", exist_ok=True)
    else:
        os.makedirs("temp/output", exist_ok=True)
        os.makedirs("temp/upload", exist_ok=True)


def get_session(devmode):
    try:
        import browser_cookie3

        # Retrieve Firefox cookies
        cookies = browser_cookie3.firefox(domain_name="armconverter.com")

        # Filter for session cookies
        session_cookies = [cookie for cookie in cookies if not cookie.expires]

        # Return the session cookies values
        session_cookie_values = [cookie.value for cookie in session_cookies]

        # Print the session cookies values
        for value in session_cookie_values:
            if devmode:
                print(value)

            # Return the first session cookie value (or handle differently if needed)
            if session_cookie_values:
                return session_cookie_values[0]
            else:
                return None  # or handle no session cookies found case
    except browser_cookie3.BrowserCookieError as e:
        print(f"Error occurred: {e}")
        sys.exit(1)


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

    rm_dir = ["gamedata"]

    if not nodownload:
        ipa_file = "*.ipa"
        rm_file.insert(0, ipa_file)
        tmp_dir = "temp"
        rm_dir.insert(0, tmp_dir)

    return rm_file, rm_dir


def get_scripts(
    type, version, session, nodownload, onlydownload, dlprogress, limit, checkversion
):
    if type == "apk":
        session = ""

    if onlydownload:
        return [
            [
                f"script/down-{type}.py",
                version,
                session,
                str(dlprogress),
            ]
        ]

    script_list = [
        [f"misc/unpack-{type}.py", version],
        ["script/fetch_links.py"],
        ["script/fetch_profile.py"],
        ["script/fetch_outfits.py", limit],
        ["script/fetch_characters.py"],
        ["script/fetch_boards.py"],
        ["script/playerprofile.py"],
        ["script/userstats.py"],
        ["script/collection.py"],
        ["script/calender.py"],
        ["script/mailbox.py"],
        ["misc/sort_characters.py"],
        ["misc/sort_boards.py"],
        ["misc/check.py", checkversion],
    ]

    if not nodownload:
        download_script = [
            f"script/down-{type}.py",
            version,
            session,
            str(dlprogress),
        ]
        script_list.insert(0, download_script)

    return script_list


def cleanup(nodownload, nocleanup):
    if nocleanup:
        return

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
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred during cleanup: {e}")
        sys.exit(1)

def run_scripts(
    type,
    version,
    nodownload,
    onlydownload,
    dlprogress,
    delay,
    session,
    devmode,
    checkversion,
):
    limit = "0"
    if devmode:
        limit = "5"

    if not nodownload:
        if not session:
            session = get_session(devmode)

    scripts = get_scripts(
        type,
        version,
        session,
        nodownload,
        onlydownload,
        dlprogress,
        limit,
        checkversion,
    )

    try:
        print(f"Choosing type: {type}")
        print(f"Choosing version: {version}")
        for script in scripts:
            print(f"Running {script[0]}...")
            subprocess.run(["python"] + script, check=True)
            print(f"Finished running {script[0]}.\n")
            time.sleep(delay)
    except Exception as e:
        print(f"Error occurred: {e}")
    except KeyboardInterrupt:
        print("Script execution interrupted by user.")


def extract(type, version, session, devmode, nodownload, dlprogress):
    try:
        if type == "apk":
            session = ""
        else:
            session = get_session(devmode)
        print(f"Choosing type {type}")
        if not nodownload:
            print(f"Downloading {version}...")
            subprocess.run(
                [
                    "python",
                    f"script/down-{type}.py",
                    version,
                    session,
                    str(bool(dlprogress)),
                ],
                check=True,
            )
        print(f"Extracting {type}...")
        subprocess.run(["python", f"misc/unpack-{type}.py", version], check=True)
    except KeyboardInterrupt:
        print("Script execution interrupted by user.")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Run Subway Surfers scripts.")
    parser.add_argument(
        "-c", "--cleanup", action="store_true", help="Run cleanup function only"
    )
    parser.add_argument(
        "-nc", "--nocleanup", action="store_true", help="Prevents cleaning up any files"
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
        "-ndl",
        "--nodownload",
        action="store_true",
        help="Run scripts without downloading game file (Game has to be downloaded beforehand)",
    )
    parser.add_argument(
        "-odl",
        "--onlydownload",
        action="store_true",
        help="Only downloads the gamefile",
    )
    parser.add_argument(
        "-dlp",
        "--dlprogress",
        action="store_true",
        help="Enables the download progress bar",
    )
    parser.add_argument(
        "-dly",
        "--delay",
        type=int,
        default=5,
        help="Change the delay between the running scripts",
    )
    parser.add_argument(
        "-s",
        "--session",
        type=str,
        default=None,
        help="Set the iosGods session cookie",
    )
    parser.add_argument(
        "-dev",
        "--devmode",
        action="store_true",
        help="Enables dev mode, will e.g limit outfit fetch",
    )
    parser.add_argument(
        "-cv",
        "--checkversion",
        type=str,
        default="",
        help="Check the updated items against an older version than just the last one",
    )

    args = parser.parse_args()

    # Regex pattern
    pattern = r"^\d{1,2}-\d{1,2}-\d{1,2}$"

    # Validate 'version'
    if args.version and not re.match(pattern, args.version):
        print(
            "Error: 'version' has the wrong format. Please use the format 'X-Y-Z' (e.g., '3-12-2')."
        )
        sys.exit(1)

    # Validate 'checkversion'
    if args.checkversion and not re.match(pattern, args.checkversion):
        print(
            "Error: 'checkversion' has the wrong format. Please use the format 'X-Y-Z' (e.g., '3-12-2')."
        )
        sys.exit(1)

    try:
        if args.cleanup:
            cleanup(args.nodownload, args.nocleanup)
        elif args.extract:
            cleanup(args.nodownload, args.nocleanup)
            setup(True, args.onlydownload)
            extract(
                args.type,
                args.version,
                args.session,
                args.devmode,
                args.nodownload,
                args.dlprogress,
            )
        else:
            cleanup(args.nodownload, args.nocleanup)
            setup(False, args.onlydownload)
            run_scripts(
                args.type,
                args.version,
                args.nodownload,
                args.onlydownload,
                args.dlprogress,
                args.delay,
                args.session,
                args.devmode,
                args.checkversion,
            )
    except Exception as e:
        print("Error:", e)
        sys.exit(1)
    except KeyboardInterrupt:
        print("Script terminated by user.")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Script terminated by user.")
        sys.exit(1)
