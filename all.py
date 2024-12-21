import argparse
import glob
import os
import re
import shutil
import subprocess
import sys
import time

import requests


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

        # Retrieve Firefox cookies for the domain
        try:
            cookies = browser_cookie3.firefox(domain_name="armconverter.com")
        except Exception as e:
            print("Cookies do not exist.")
            sys.exit(1)

        # Filter for session cookies (non-expiring cookies)
        session_cookies = [cookie for cookie in cookies if not cookie.expires]

        # If no session cookies are found, exit
        if not session_cookies:
            print("No session cookies found.")
            sys.exit(1)

        # Extract and print session cookie values
        session_cookie_values = [cookie.value for cookie in session_cookies]

        if devmode:
            for value in session_cookie_values:
                print(value)

        # Return the first session cookie value, or None if no cookies are present
        return session_cookie_values[0] if session_cookie_values else None

    except browser_cookie3.BrowserCookieError as e:
        print(f"Error occurred: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error occurred getting session: {e}")
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
    type,
    version,
    session,
    nodownload,
    onlydownload,
    dlprogress,
    limit,
    checkversion,
    extract,
    skip,
):
    skip_list = [script.strip() for script in skip.split(",") if script.strip()]

    if type == "apk":
        session = ""

    if extract:
        return [
            [
                f"script/down-{type}.py",
                version,
                session,
                str(dlprogress),
            ],
            [f"misc/unpack-{type}.py", version],
        ]

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
        ["script/achievements.py"],
        ["misc/sort_characters.py"],
        ["misc/sort_boards.py"],
        ["misc/sort_profile.py"],
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

    # Filter out skipped scripts
    script_list = [
        script
        for script in script_list
        if script[0].split("/")[-1].split(".")[0] not in skip_list
    ]

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
    extract,
    skip,
):
    limit = "0"
    if devmode:
        limit = "5"

    if not nodownload:
        if not session and not type == "apk":
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
        extract,
        skip,
    )

    try:
        print(f"Choosing type: {type}")
        print(f"Choosing version: {version}")
        for index, script in enumerate(scripts):
            print(f"Running {script[0]}...")
            subprocess.run(["python"] + script, check=True)
            print(f"Finished running {script[0]}.")
            # Sleep only if this is not the last script
            if index < len(scripts) - 1:
                time.sleep(delay)
                print(f"\n")
    except Exception as e:
        print(f"Error occurred while running script: {e}")
    except KeyboardInterrupt:
        print("Script execution interrupted by user.")


def main():
    parser = argparse.ArgumentParser(description="Run Subway Surfers scripts.")
    parser.add_argument(
        "-t",
        "--type",
        choices=["apk", "ipa"],
        default="ipa",
        help="Choose between type apk and ipa",
    )
    parser.add_argument(
        "-v", "--version", type=str, default=version(), help="Choose a specific version"
    )
    parser.add_argument(
        "-c", "--cleanup", action="store_true", help="Run cleanup function only"
    )
    parser.add_argument(
        "-nc", "--nocleanup", action="store_true", help="Prevents cleaning up any files"
    )
    parser.add_argument(
        "-e",
        "--extract",
        action="store_true",
        help="Download and extract the latest apk/ipa",
    )
    parser.add_argument(
        "-ndl",
        "--nodownload",
        action="store_true",
        help="Run scripts without downloading game file (game file has to be downloaded beforehand)",
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
        default="",
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
    parser.add_argument(
        "-skp",
        "--skip",
        type=str,
        default="",
        help="Write a list of scripts that should be skiped, with or without extension. (Like this 'collection.py,playerprofile,calender')",
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
            if not args.nocleanup:
                cleanup(args.nodownload, args.nocleanup)
            setup(True, args.onlydownload)
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
                args.extract,
                args.skip,
            )
        else:
            if not args.nocleanup:
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
                args.extract,
                args.skip,
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
