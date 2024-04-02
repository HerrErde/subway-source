import sys
import os
import requests
import time
import colorama
import json
from dotenv import load_dotenv
from bs4 import BeautifulSoup

# Colors for terminal output
LOG = {
    "ERROR": "\033[91m[ERROR] ",
    "SUCCESS": "\033[92m[SUCCESS]\033[94m ",
    "INFO": "\033[94m[INFO] ",
    "WARN": "\033[93m[INFO] ",
    "DEBUG": "\033[35m[DEBUG] ",
    "END": "\033[0m",
}


load_dotenv()
colorama.init()
start_time = time.time()
workflow_runs = 0
delay = int(os.environ.get("DELAY", 300))  # 5 mins
minimal = bool(os.environ.get("MINIMAL", False))
debug = bool(os.environ.get("DEBUG", False))
debug_workflow = bool(os.environ.get("DEBUG_RUN", False))

repo_owner = str(os.environ.get("REPO_OWNER", "HerrErde"))
repo_name = str(os.environ.get("REPO_NAME", "subway-source"))
repo2_name = str(os.environ.get("REPO2_NAME", "SubwayBooster"))
github_token = str(os.environ.get("GITHUB_API_KEY"))


def check_404(gplayapi_version):
    url = f"https://www.apkmirror.com/apk/sybo-games/subwaysurfers/subwaysurfers-{gplayapi_version}-release/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    if soup.find(class_="error404"):
        return True


def get_version():
    # get version from gplayapi
    if debug_workflow:
        file_path = "debug/gplay_version.json"
        with open(file_path) as file:
            gplayapi_data = json.load(file)
        print("debug: gplay")
    else:
        if debug:
            print("prod: gplay")
        endpoint = "https://gplayapi.herrerde.xyz/api/apps/com.kiloo.subwaysurf"
        gplayapi_response = requests.get(endpoint)
        gplayapi_data = gplayapi_response.json()  # Extract JSON data from response
    gplayapi_version = gplayapi_data.get("version")

    # get json appversion
    if debug_workflow:
        file_path = "debug/json_version.json"
        with open(file_path) as file:
            json_data = json.load(file)
            print("debug: json")
    else:
        if debug:
            print("prod: json")
        endpoint = f"https://raw.githubusercontent.com/{repo_owner}/{repo2_name}/master/src/version.json"
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/json",
        }
        json_response = requests.get(endpoint, headers=headers)
        json_data = json_response.json()  # Extract JSON data from response
    json_version = json_data.get("appversion")

    # get latest repo tag
    if debug_workflow:
        file_path = "debug/tag_version.json"
        with open(file_path) as file:
            tag_data = json.load(file)
        print("debug: tag")
    else:
        if debug:
            print("prod: tag")
        endpoint = (
            f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
        )
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/json",
        }
        tag_response = requests.get(endpoint, headers=headers)
        tag_data = tag_response.json()
    tag_version = tag_data.get("tag_name")

    return gplayapi_version, json_version, tag_version


def check_workflow_runs(repo_owner, repo_name, github_token):
    endpoint = f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/runs"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
    }
    params = {"status": "in_progress"}

    response = requests.get(endpoint, headers=headers, params=params)

    if response.ok:
        workflow_runs = response.json().get("total_count", 0)
        if workflow_runs > 0:
            print(
                f"{LOG['INFO']}A workflow is already running. Skipping trigger.{LOG['END']}"
            )
    else:
        print(f"{LOG['ERROR']}Failed to retrieve workflow runs.{LOG['END']}")
        return False


def trigger_subwaysource_workflow():
    global workflow_runs
    if debug_workflow:
        print(
            f"{LOG['DEBUG']}Would have Triggered Workflow in Repo subway-source successfully!{LOG['END']}"
        )
        workflow_runs += 1
    else:
        if check_workflow_runs(repo_owner, repo_name, github_token):
            return

        endpoint = f"https://api.github.com/repos/{repo_owner}/{repo_name}/dispatches"
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/json",
        }
        payload = {"event_type": "update_event", "client_payload": {"ref": "master"}}
        response = requests.post(endpoint, headers=headers, json=payload)
        if response.ok:
            print(f"{LOG['SUCCESS']}Triggered workflow successfully!{LOG['END']}")
            workflow_runs += 1
            tag_version = None
        else:
            print(f"{LOG['ERROR']}Failed to trigger the workflow.{LOG['END']}")


# trigger subwaybooster workflow
def trigger_subwaybooster_workflow():
    global workflow_runs
    if debug_workflow:
        print(
            f"{LOG['DEBUG']}Would have Triggered Workflow in Repo SubwayBooster successfully!{LOG['END']}"
        )
        workflow_runs += 1
    else:
        if check_workflow_runs(repo_owner, repo2_name, github_token):
            return

        endpoint = f"https://api.github.com/repos/{repo_owner}/{repo2_name}/dispatches"
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/json",
        }
        payload = {"event_type": "update_event", "client_payload": {"ref": "master"}}
        response = requests.post(endpoint, headers=headers, json=payload)

        if response.ok:
            print(
                f"{LOG['SUCCESS']}Triggered GitHub workflow successfully!{LOG['END']}"
            )
            workflow_runs += 1
        else:
            print(f"{LOG['ERROR']}Failed to trigger the GitHub workflow.{LOG['END']}")


def display_stuff(gplayapi_version, json_version):
    global start_time, workflow_runs
    current_time = time.time()

    json_part = json_version.split(".")
    cur_version = ".".join(json_part)

    # Convert elapsed_time to days, hours, minutes, and seconds
    elapsed_time = current_time - start_time
    elapsed_days, elapsed_time = divmod(elapsed_time, 24 * 3600)
    elapsed_hours, elapsed_time = divmod(elapsed_time, 3600)
    elapsed_minutes, elapsed_seconds = divmod(elapsed_time, 60)

    if minimal:
        output = {"Current": cur_version, "Latest": gplayapi_version}
    else:
        output = {
            "Start Time": time.ctime(start_time),
            "Elapsed Time": f"{int(elapsed_days)}d:{int(elapsed_hours)}h:{int(elapsed_minutes)}m:{int(elapsed_seconds)}s",
            "Workflow Runs": workflow_runs,
            "Current": cur_version,
            "Latest": gplayapi_version,
        }

    print(output)


def main():
    try:
        while True:
            gplayapi_version, json_version, tag_version = get_version()
            gplayapi_part = int(gplayapi_version.split(".")[1])
            json_part = int(json_version.split(".")[1])
            tag_part = int(tag_version.split("-")[1])

            if debug:
                print(
                    f"gplayapi_part {gplayapi_part}, json {json_part}, tag {tag_part}"
                )

            if gplayapi_part == tag_part and gplayapi_part != json_part:
                print(f"{LOG['WARN']}SubwayBooster version is outdated!{LOG['END']}")
                trigger_subwaybooster_workflow()
                print("Waiting for 6 minutes before making a new version request...")
                time.sleep(6 * 60)  # Github Cache fix
            elif gplayapi_part != tag_part:
                print(f"{LOG['WARN']}subway-source version is outdated!{LOG['END']}")
                if check_404(gplayapi_version):
                    print("No Version available")
                else:
                    trigger_subwaysource_workflow()
            else:
                print(f"{LOG['INFO']}All Versions are up to date!{LOG['END']}")
            display_stuff(gplayapi_version, json_version)
            time.sleep(delay)

    except KeyboardInterrupt:
        print("\nProgram interrupted. Exiting...")
        sys.exit(0)


if __name__ == "__main__":
    main()
