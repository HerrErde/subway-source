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
    "INFO2": "\033[93m[INFO] ",
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
github_token = str(os.environ.get("GITHUB_API_KEY"))


def check_404(gplayapi_version):
    url = f"https://www.apkmirror.com/apk/sybo-games/subwaysurfers/subwaysurfers-{gplayapi_version}-release/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    if soup.find(class_="error404"):
        return True


def get_version():
    tag_version = None
    # get version from gplayapi
    if debug:
        file_path = "debug/gplay_version.json"
        with open(file_path) as file:
            gplayapi_data = json.load(file)
    else:
        gplayapi_response = requests.get(
            "https://gplayapi.herrerde.xyz/api/apps/com.kiloo.subwaysurf"
        )
        gplayapi_data = gplayapi_response.json()
    gplayapi_version = gplayapi_data["version"]
    if debug:
        print("gplay")

    # get json appversion
    if debug:
        file_path = "debug/json_version.json"
        with open(file_path) as file:
            json_data = json.load(file)
    else:
        json_response = requests.get(
            "https://raw.githubusercontent.com/HerrErde/SubwayBooster/master/src/version.json"
        )
        json_data = json_response.json()
    json_version = json_data["appversion"]
    if debug:
        print("json")

    # get latest repo tag
    if tag_version == None:
        if debug:
            file_path = "debug/tag_version.json"
            with open(file_path) as file:
                tag_data = json.load(file)
        else:
            endpoint = (
                f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
            )
            headers = {
                "Authorization": f"token {github_token}",
                "Accept": "application/json",
            }
            tag_response = requests.get(endpoint, headers=headers)
            tag_data = tag_response.json()
        tag_version = tag_data["tag_name"]
    if debug:
        print("tag")

    return gplayapi_version, json_version, tag_version


# trigger subway-source workflow
def trigger_github_workflow():
    global workflow_runs
    if debug_workflow:
        print(
            f"{LOG['DEBUG']}Would have Triggered Workflow in Repo subway-source successfully!{LOG['END']}"
        )
        workflow_runs += 1
    else:
        endpoint = f"https://api.github.com/repos/{repo_owner}/{repo_name}/dispatches"
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/json",
        }
        payload = {"event_type": "update_event", "client_ payload": {"ref": "master"}}
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
    sup_version = ".".join(json_part[:2]) + ".*"

    # Convert elapsed_time to days, hours, minutes, and seconds
    elapsed_time = current_time - start_time
    elapsed_days, elapsed_time = divmod(elapsed_time, 24 * 3600)
    elapsed_hours, elapsed_time = divmod(elapsed_time, 3600)
    elapsed_minutes, elapsed_seconds = divmod(elapsed_time, 60)

    if minimal:
        output = {"Supported": sup_version, "Latest": gplayapi_version}
    else:
        output = {
            "Start Time": time.ctime(time.time()),
            "Elapsed Time": f"{int(elapsed_days)}d:{int(elapsed_hours)}h:{int(elapsed_minutes)}m:{int(elapsed_seconds)}s",
            "Workflow Runs": workflow_runs,
            "Supported": sup_version,
            "Latest": gplayapi_version,
        }

    print(output)


def main():
    try:
        gplayapi_version, json_version, tag_version = get_version()
        gplayapi_part = gplayapi_version.split(".")
        json_part = json_version.split(".")
        tag_part = tag_version.split("-")

        while True:
            if int(gplayapi_part[1]) == int(tag_part[1]):
                print(f"{LOG['INFO']}Version is up to date!{LOG['END']}")
                display_stuff(gplayapi_version, json_version)
                if gplayapi_part[1] != json_part[1]:
                    trigger_subwaybooster_workflow()
            else:
                print(f"{LOG['INFO2']}Version is outdated!{LOG['END']}")
                if check_404(gplayapi_version):
                    print("No Version available")
                else:
                    trigger_github_workflow()
                display_stuff(gplayapi_version, json_version)

            time.sleep(delay)
    except KeyboardInterrupt:
        print("\nProgram interrupted. Exiting...")
        sys.exit(0)


if __name__ == "__main__":
    main()
