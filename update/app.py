import sys
import os
import requests
import time
from playwright.sync_api import sync_playwright

# Colors for terminal output
class TerminalColors:
    RED = "\033[91m"
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    YELLOW = "\033[93m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"

delay = 300
start_time = time.time()
workflow_runs = 0

repo_owner = os.environ.get("REPO_OWNER", "HerrErde")
repo_name = os.environ.get("REPO_NAME", "subway-source")
github_token = os.environ.get("GITHUB_API_KEY")

def check_404(gplayapi_version):
    with async_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context()
        page = context.new_page()
        page.goto(f"https://www.apkmirror.com/apk/sybo-games/subwaysurfers/subwaysurfers-{gplayapi_version}-release/")
        page_content = page.content()

        if 'class="error404"' in page_content:
            browser.close()
            return False

    return True

def get_version():
    # get version gplayapi
    gplayapi_response = requests.get(
        "https://gplayapi.srik.me/api/apps/com.kiloo.subwaysurf"
    )
    gplayapi_data = gplayapi_response.json()
    gplayapi_version = gplayapi_data["version"]

    # get json appversion
    json_response = requests.get("https://raw.githubusercontent.com/HerrErde/SubwayBooster/master/Android/data/com.kiloo.subwaysurf/files/version.json")
    json_data = json_response.json()
    json_version = json_data["appversion"]

    return gplayapi_version, json_version

def trigger_github_workflow():
    # Trigger the GitHub workflow
    endpoint = f"https://api.github.com/repos/{repo_owner}/{repo_name}/dispatches"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.everest-preview+json",
    }
    payload = {"event_type": "update_event", "client_payload": {"ref": "main"}}
    response = requests.post(endpoint, headers=headers, json=payload)

    if response.status_code == 204:
        print(
            f"{TerminalColors.GREEN}GitHub workflow triggered successfully!{TerminalColors.END}"
        )
    else:
        print(
            f"{TerminalColors.RED}Failed to trigger the GitHub workflow.{TerminalColors.END}"
        )

def display_stuff():
    global start_time, workflow_runs
    current_time = time.time()
    elapsed_time = current_time - start_time
    gplayapi_version, json_version = get_version()

    # Convert elapsed_time to days, hours, minutes, and seconds
    elapsed_days = int(elapsed_time // (24 * 3600))
    elapsed_time %= (24 * 3600)
    elapsed_hours = int(elapsed_time // 3600)
    elapsed_time %= 3600
    elapsed_minutes = int(elapsed_time // 60)
    elapsed_seconds = int(elapsed_time % 60)

    print(
        {
            f"Start Time": time.ctime(start_time),
            f"Elapsed Time": f"{elapsed_days}d:{elapsed_hours}h:{elapsed_minutes}m:{elapsed_seconds}s",
            f"Workflow Runs": workflow_runs,
            f"Supported Version": json_version,
            f"Latest Version": gplayapi_version,
        }
    )


def main():
    global delay, workflow_runs

    while True:

        gplayapi_version, json_version = get_version()

        if gplayapi_version != json_version:
            print(f"{TerminalColors.YELLOW}Version is outdated!{TerminalColors.END}")
            if check_404(gplayapi_version):
                print("No Version available")
                display_stuff()
                continue
            else:
                trigger_github_workflow()
                workflow_runs += 1
                display_stuff()
        else:
            print(f"{TerminalColors.BLUE}Version is up to date!{TerminalColors.END}")
            display_stuff()

        time.sleep(delay)


if __name__ == "__main__":
    main()
