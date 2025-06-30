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
        except browser_cookie3.BrowserCookieError:
            print("Cookies do not exist or cannot be accessed.")
            sys.exit(1)
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
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


def app_version(type_, latest):
    try:
        if type_ == "ipa":
            version_num = version_ipa(latest)
        elif type_ == "apk":
            version_num = version_apk(latest)
        return version_num
    except requests.RequestException as e:
        print(f"Error retrieving app version: {e}")
        return None


def version_apk(latest):
    try:
        url = "https://gplayapi.herrerde.xyz/api/apps/com.kiloo.subwaysurf"
        response = requests.get(url)
        response.raise_for_status()
        version = response.json().get("version")
        if version:
            if not latest:
                parts = version.split(".")
                major, minor = parts[:2]  # Extract major and minor version
                version = f"{major}.{minor}.0"
            return version
        return None
    except requests.RequestException as e:
        print(f"Error retrieving app version: {e}")
        return None


def version_ipa(latest):
    appid = 512939461
    try:
        url = f"https://itunes.apple.com/lookup?id={appid}&country=us"
        response = requests.get(url)
        response.raise_for_status()
        results = response.json().get("results", [])
        if not results:
            return None
        version = results[0].get("version")
        if version:
            if not latest:
                parts = version.split(".")
                major = parts[0]
                minor = parts[1] if len(parts) > 1 else "0"
                version = f"{major}.{minor}.0"
            return version
        return None
    except requests.RequestException as e:
        print(f"Error retrieving app version: {e}")
        return None


def get_rm(runonly):
    rm_file = [
        "*.apk",
        "*.ipa",
        "*.zip",
        "*_output.json",
        "*_data_old.json",
        "update.txt",
    ]

    rm_dir = ["gamedata"]

    if not runonly:
        ipa_file = "*.ipa"
        rm_file.insert(0, ipa_file)
        tmp_dir = "temp"
        rm_dir.insert(0, tmp_dir)

    return rm_file, rm_dir


def get_scripts(
    type_,
    version,
    session,
    runonly,
    onlydownload,
    dlprogress,
    limit,
    checkversion,
    extract,
    skip,
):
    skip_list = [script.strip() for script in skip.split(",") if script.strip()]

    scripts = []

    if extract:
        if type_ == "ipa" and not session:
            scripts.append(["script/down-ipa.py", version, session, str(dlprogress)])
        elif type_ == "apk":
            scripts.append(["script/down-apk.py", version, str(dlprogress)])
        scripts.append(["misc/unpack-{type_}.py", version])
        return scripts

    if onlydownload:
        if type_ == "ipa" and not session:
            return [["script/down-ipa.py", version, session, str(dlprogress)]]
        if type_ == "apk":
            return [["script/down-apk.py", version, str(dlprogress)]]

    script_list = [
        # [f"misc/unpack-{type_}.py", version],
        [f"misc/get_gamedata.py", f"subway-surfers-{version}.{type_}"],
        ["script/fetch_links.py"],
        ["script/fetch_profile.py"],
        ["script/fetch_outfits.py", limit],
        ["script/fetch_characters.py"],
        ["script/fetch_boards.py"],
        ["script/playerprofile.py"],
        ["script/userstats.py"],
        ["script/collection.py"],
        ["script/challenges.py"],
        ["script/calender.py"],
        ["script/mailbox.py"],
        ["script/achievements.py"],
        ["script/chainoffers.py"],
        ["script/promotions.py"],
        ["script/citytours.py"],
        ["misc/sort_characters.py"],
        ["misc/sort_boards.py"],
        ["misc/sort_profile.py"],
        ["misc/check.py", checkversion],
    ]

    if not runonly:
        download_script = [
            f"script/down-{type_}.py",
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


def cleanup(runonly, nocleanup):
    if nocleanup:
        print("No cleanup")
        return

    print("Starting cleanup")
    rm_file, rm_dir = get_rm(runonly)

    try:
        for pattern in rm_file:
            for file in glob.glob(pattern):
                if os.path.exists(file):
                    os.remove(file)

        for directory in rm_dir:
            if os.path.exists(directory):
                shutil.rmtree(directory)
        print("Finished cleanup")
    except KeyboardInterrupt:
        print("Cleanup interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred during cleanup: {e}")
        sys.exit(1)


def run_scripts(
    type_,
    version,
    runonly,
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

    if not runonly:
        if not session and not type_ == "apk":
            session = get_session(devmode)

    scripts = get_scripts(
        type_,
        version,
        session,
        runonly,
        onlydownload,
        dlprogress,
        limit,
        checkversion,
        extract,
        skip,
    )

    try:
        print(f"Choosing type: {type_}")
        print(f"Choosing version: {version}\n")
        for index, script in enumerate(scripts):
            print(f"Running {script[0]}...")
            if script[0].startswith("script/down-ipa.py"):
                result = subprocess.run(
                    ["python"] + script,
                    capture_output=True,
                    text=True,
                    check=True,
                )

                output = result.stdout.strip()
                print(output)
                if "quota" in output.lower():
                    sys.exit(1)

            else:
                subprocess.run(["python"] + script, check=True)
                print(f"Finished running {script[0]}.")

            # Sleep only if this is not the last script
            if index < len(scripts) - 1:
                time.sleep(delay)
                print("\n")
    except Exception as e:
        print(f"Error occurred while running script: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("Script execution interrupted by user.")
        sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="Run Subway Surfers scripts.")
    parser.add_argument(
        "-t",
        "--type",
        choices=["apk", "ipa"],
        default="apk",
        help="Choose between type apk and ipa",
    )
    parser.add_argument(
        "-gv",
        "--getversion",
        action="store_true",
        help="Get the latest version of the game type",
    )
    parser.add_argument(
        "-v", "--version", type=str, default=None, help="Choose a specific version"
    )
    parser.add_argument(
        "-l",
        "--latest",
        action="store_true",
        help="Get the latest version of the app (e.g. 4.42.4), or get the latest major and minor (e.g. 4.42.0)",
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
        "-run",
        "--runonly",
        action="store_true",
        help="Run the scripts without downloading the game file (requires pre-downloaded file)",
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
        help="Shows the download progress bar",
    )
    parser.add_argument(
        "-dly",
        "--delay",
        type=int,
        default=5,
        help="Change the delay between the running scripts",
    )
    parser.add_argument(
        "-sess",
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
        help="Compare updates to a version older than the latest",
    )
    parser.add_argument(
        "-skp",
        "--skip",
        type=str,
        default="",
        help="Write a list of scripts that should be skipped, with or without extension. (Like this 'collection.py,playerprofile,calender')",
    )

    args = parser.parse_args()

    if args.version is None:
        args.version = app_version(args.type, args.latest).replace(".", "-")

    # Regex pattern
    version_pattern = r"^\d{1,2}-\d{1,2}-\d{1,2}$"

    # Validate 'version'
    if args.version and not re.match(version_pattern, args.version):
        print(
            "Error: 'version' has the wrong format. Please use the format 'X-Y-Z' (e.g., '3-12-2')."
        )
        sys.exit(1)

    # Validate 'checkversion'
    if args.checkversion and not re.match(version_pattern, args.checkversion):
        print(
            "Error: 'checkversion' has the wrong format. Please use the format 'X-Y-Z' (e.g., '3-12-2')."
        )
        sys.exit(1)

    try:
        if args.getversion:
            version = app_version(args.type, args.latest)
            print(f"Game Type: {args.type}\n{version}")
            return
        if args.cleanup:
            cleanup(args.runonly, args.nocleanup)
            return
        setup(args.extract, args.onlydownload)
        run_scripts(
            args.type,
            args.version,
            args.runonly,
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
