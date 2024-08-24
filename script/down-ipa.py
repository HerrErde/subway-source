import sys
import re
import requests

appid = 512939461
apppackage = "com.kiloo.subwaysurfers"
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"
appName = "subwaysurfers"


if len(sys.argv) < 2:
    print("Error: No version set. Please use the format 'X-Y-Z' (e.g., '3-12-2').")
    sys.exit(1)

version = sys.argv[1]
if not re.match(r"^\d{1,2}-\d{1,2}-\d{1,2}$", version):
    print(
        "Error: Invalid version format. Please use the format 'X-Y-Z' (e.g., '3-12-2')."
    )
    sys.exit(1)

appver = version.replace("-", ".")

version_url = (
    f"https://armconverter.com/decryptedappstore/versions/{appid}/{appver}?country=us"
)
prepare_url = f"https://armconverter.com/decryptedappstore/download/{appid}/{apppackage}/{appver}/prepare"
download_base_url = (
    f"https://armconverter.com/decryptedappstore/download/{appid}/{apppackage}/{appver}"
)
info_url = f"https://armconverter.com/decryptedappstore/download/{appid}/{apppackage}/{appver}/info"


session = sys.argv[2]


def user(session):
    # Set up the URLs and headers
    url = f"https://armconverter.com/decryptedappstore/user/info"

    headers = {
        "User-Agent": user_agent,
        "Cookie": f"session={session}",
    }
    # Initial POST request to check state and versions
    response = requests.post(url, headers=headers)
    data = response.json()

    # Check if the versions list is present and get the last version
    # quota = data.get("quota", [])
    # lastLogin = data.get("lastLogin", [])


def check_version(session, version):
    headers = {"Cookie": f"session={session}", "User-Agent": user_agent}

    # Initial GET request to check state and versions
    response = requests.get(version_url, headers=headers)

    if response.status_code != 200:
        print(f"Error fetching version information: {response.status_code}")
        return

    data = response.json()

    # Check if the versions list is present and get the last version
    versions = data.get("versions", [])

    if not versions:
        print("No versions found.")
        return

    # Extract the version number from the last version dictionary
    last_version = versions[-1].get("ver").replace(".", "-")

    # Compare the last version with the provided version
    if last_version != version:
        print(f"The last version {last_version} does not match version {version}.")
    else:
        print(f"You are using the latest version {version}.")


def download(session, version):
    headers = {
        "User-Agent": user_agent,
        "Referer": "https://armconverter.com/decryptedappstore/us/Subway",
        "Cookie": f"session={session}",
    }

    try:
        # POST request to prepare download
        response = requests.post(f"{download_base_url}/prepare", headers=headers)
        data = response.json()

        if data.get("state") == "ready":
            token = data.get("token")

            if not token:
                print("Token not found.")
                return

            # Final download URL with token
            download_url = f"{download_base_url}?token={token}"
            download_response = requests.get(download_url, headers=headers)

            if download_response.status_code == 200:
                with open(f"temp/{appName}-{version}.ipa", "wb") as file:
                    file.write(download_response.content)
                print("Download successful.")
            else:
                print("Failed to download the file.")
        else:
            print("State is not ready.")
            sys.exit(1)

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")


def main():

    if session:
        check_version(session, version)
        download(session, version)
    else:
        print("No session cookies found.")
        sys.exit(1)


if __name__ == "__main__":
    main()
