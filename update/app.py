import sys
import os
import requests
import time
import json
from playwright.sync_api import sync_playwright


# Colors for terminal output
class TerminalColors:
    RED = "\033[91m"
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    YELLOW = "\033[93m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"


delay = os.environ.get("DELAY", 5)  # 5 mins
start_time = time.time()
workflow_runs = 0
debug = os.environ.get("DEBUG", True)

repo_owner = os.environ.get("REPO_OWNER", "HerrErde")
repo_name = os.environ.get("REPO_NAME", "subway-source")
github_token = os.environ.get("GITHUB_API_KEY")


def check_404(gplayapi_version):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context()
        page = context.new_page()
        page.goto(
            f"https://www.apkmirror.com/apk/sybo-games/subwaysurfers/subwaysurfers-{gplayapi_version}-release/"
        )
        page_content = page.content()

        if 'class="error404"' in page_content:
            browser.close()
            return True


def get_version():
    # get version from gplayapi
    if debug:
        file_path = "debug/gplay_version.json"  # Replace with the actual file path on your system
        with open(file_path) as file:
            gplayapi_data = json.load(file)
    else:
        gplayapi_response = requests.get(
            "https://gplayapi.srik.me/api/apps/com.kiloo.subwaysurf"
        )
        gplayapi_data = gplayapi_response.json()
    gplayapi_version = gplayapi_data["version"]

    # get json appversion
    if debug:
        file_path = "debug/json_version.json"  # Replace with the actual file path on your system
        with open(file_path) as file:
            json_data = json.load(file)
    else:
        json_response = requests.get(
            "https://raw.githubusercontent.com/HerrErde/SubwayBooster/master/Android/data/com.kiloo.subwaysurf/files/version.json"
        )
        json_data = json_response.json()
    json_version = json_data["appversion"]

    # get latest repo tag
    tag_response = requests.get(
        f"https://api.github.com/repos/HerrErde/{repo_name}/releases/latest"
    )
    if tag_response.status_code == 200:
        release_data = tag_response.json()
        tag_version = release_data["tag_name"]
    else:
        tag_version = None

    return gplayapi_version, json_version, tag_version


# trigger subway-source workflow
def trigger_github_workflow():
    global workflow_runs
    endpoint = f"https://api.github.com/repos/{repo_owner}/{repo_name}/dispatches"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.everest-preview+json",
    }
    payload = {"event_type": "update_event", "client_payload": {"ref": "master"}}
    response = requests.post(endpoint, headers=headers, json=payload)

    if response.ok:
        print(
            f"{TerminalColors.BLUE}Triggered GitHub workflow successfully!{TerminalColors.END}"
        )
        workflow_runs += 1
    else:
        print(
            f"{TerminalColors.RED}Failed to trigger the GitHub workflow.{TerminalColors.END}"
        )


# trigger subwaybooster workflow
def trigger_subwaybooster_workflow():
    endpoint = f"https://api.github.com/repos/{repo_owner}/{repo2_name}/dispatches"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.everest-preview+json",
    }
    payload = {"event_type": "update_event", "client_payload": {"ref": "master"}}
    response = requests.post(endpoint, headers=headers, json=payload)

    if response.ok:
        print(
            f"{TerminalColors.BLUE}Triggered GitHub workflow successfully!{TerminalColors.END}"
        )
        workflow_runs += 1
    else:
        print(
            f"{TerminalColors.RED}Failed to trigger the GitHub workflow.{TerminalColors.END}"
        )


def display_stuff():
    global start_time, workflow_runs
    current_time = time.time()
    elapsed_time = current_time - start_time
    gplayapi_version, json_version, tag_version = get_version()

    json_part = json_version.split(".")
    sup_version = ".".join(json_part[:2]) + ".*"

    # Convert elapsed_time to days, hours, minutes, and seconds
    elapsed_days, elapsed_time = divmod(elapsed_time, 24 * 3600)
    elapsed_hours, elapsed_time = divmod(elapsed_time, 3600)
    elapsed_minutes, elapsed_seconds = divmod(elapsed_time, 60)

    output = {
        "Start Time": time.ctime(start_time),
        "Elapsed Time": f"{int(elapsed_days)}d:{int(elapsed_hours)}h:{int(elapsed_minutes)}m:{int(elapsed_seconds)}s",
        "Workflow Runs": workflow_runs,
        "Supported Version": sup_version,
        "Latest Version": gplayapi_version,
    }

    print(output)


def main():
    global delay, workflow_runs

    try:
        while True:
            gplayapi_version, json_version, tag_version = get_version()

            gplayapi_part = gplayapi_version.split(".")
            json_part = json_version.split(".")
            tag_part = tag_version.split("-")

            if gplayapi_part[1] == tag_part[1]:
                print(
                    f"{TerminalColors.BLUE}Version is up to date!{TerminalColors.END}"
                )
                display_stuff()
                if gplayapi_part[1] != json_part[1]:
                    trigger_subwaybooster_workflow()
            else:
                print(
                    f"{TerminalColors.YELLOW}Version is outdated!{TerminalColors.END}"
                )
                if check_404(gplayapi_version):
                    print("No Version available")
                else:
                    trigger_github_workflow()
                display_stuff()

            time.sleep(delay)
    except KeyboardInterrupt:
        print("\nProgram interrupted. Exiting...")
        sys.exit(0)


if __name__ == "__main__":
    main()
