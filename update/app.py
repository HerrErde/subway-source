import requests
import time
import os


# Colors for terminal output
class TerminalColors:
    RED = "\033[91m"
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"


delay = 300
start_time = time.time()
workflow_runs = 0


def get_numbers_from_sources():
    # Make a request to gplayapi to retrieve the version
    gplayapi_response = requests.get(
        "https://gplayapi.srik.me/api/apps/com.kiloo.subwaysurf"
    )
    gplayapi_data = gplayapi_response.json()
    gplayapi_version = gplayapi_data["version"]

    # Read the appversion from your own JSON file
    json_response = requests.get(
        "https://raw.githubusercontent.com/HerrErde/SubwayBooster/master/Android/data/com.kiloo.subwaysurf/files/version.json"
    )
    json_data = json_response.json()
    json_version = json_data["appversion"]

    return gplayapi_version, json_version


def trigger_github_workflow():
    # Set the necessary environment variables for triggering the GitHub workflow
    repo_owner = "HerrErde"
    repo_name = "subway-source"
    github_token = os.environ.get("GITHUB_API_KEY")

    # Trigger the GitHub workflow using the GitHub REST API v3
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
    gplayapi_version, json_version = get_numbers_from_sources()
    workflow_runs += 1
    print(
        {
            f"Start Time": time.ctime(start_time),
            f"Workflow Runs": workflow_runs,
            f"JSON Version": json_version,
            f"API Version": gplayapi_version,
        }
    )


def main():
    global delay

    while True:
        gplayapi_version, json_version = get_numbers_from_sources()

        if gplayapi_version != json_version:
            print(f"{TerminalColors.YELLOW}Numbers are different!{TerminalColors.END}")
            trigger_github_workflow()
        else:
            print(f"{TerminalColors.BLUE}Numbers are the same!{TerminalColors.END}")
            display_stuff()

        time.sleep(delay)


if __name__ == "__main__":
    main()
