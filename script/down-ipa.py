import os
import re
import sys

import requests

appid = 512939461
appackage = "com.kiloo.subwaysurfers"
userAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"
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

session = sys.argv[2]

dlprogress = False
if len(sys.argv) >= 4:
    dlprogress = sys.argv[3]


version_url = (
    f"https://armconverter.com/decryptedappstore/versions/{appid}/{appver}?country=us"
)
download_base_url = (
    f"https://armconverter.com/decryptedappstore/download/{appid}/{appackage}/{appver}"
)


headers = {
    "User-Agent": userAgent,
    "Referer": "https://armconverter.com/decryptedappstore/us",
    "Cookie": f"session={session}",
}


"""
def user(session):
    # Set up the URLs and headers
    url = f"https://armconverter.com/decryptedappstore/user/info"

    headers = {
        "User-Agent": userAgent,
        "Cookie": f"session={session}",
    }
    # Initial POST request to check state and versions
    response = requests.post(url, headers=headers)
    data = response.json()

    # Check if the versions list is present and get the last version
    quota = data.get("quota", [])
    lastLogin = data.get("lastLogin", [])
"""


def check_session(session):
    user_url = "https://armconverter.com/decryptedappstore/user/info"

    try:
        response = requests.get(user_url, headers=headers)
        if response.status_code == 403:
            raise requests.exceptions.HTTPError("Unauthorized access")
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"Error: {e}, Status Code: {response.status_code}")
        sys.exit(1)


def check_version(version, session):
    try:
        try:
            response = requests.get(version_url, headers=headers)
            response.raise_for_status()
        except requests.exceptions.HTTPError:
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
    except Exception as e:
        print(f"Error occurred: {e}")
        sys.exit(1)


def check_quota(session):
    try:
        response = requests.post(f"{download_base_url}/prepare", headers=headers)

        data = response.json()

        error = data.get("error", None)

        if response.status_code == 400 and error == "QUOTA_EXCEEDED":
            return False

        return True

    except Exception as e:
        print(f"Unexpected error occurred: {e}")
        sys.exit(1)


def download(version, session, dlprogress):
    try:
        # POST request to prepare download
        response = requests.post(f"{download_base_url}/prepare", headers=headers)
        response.raise_for_status()
        data = response.json()

        if data.get("loginRequired"):
            raise ValueError("Session cookie is invalid or expired.")

        if data.get("state") != "ready":
            raise Exception("State is not ready.")

        token = data.get("token")
        if not token:
            raise Exception("Token not found.")

        # Final download URL with token
        download_url = f"{download_base_url}?token={token}"
        with requests.get(
            download_url, headers=headers, stream=True
        ) as download_response:
            download_response.raise_for_status()
            total_size = int(download_response.headers.get("content-length", 0))

            with open(f"temp/{appName}-{version}.ipa", "wb") as file:
                if dlprogress is True:
                    from tqdm import tqdm

                    with tqdm(
                        total=total_size,
                        unit="B",
                        unit_scale=True,
                        unit_divisor=1024,
                        desc="Downloading",
                    ) as progress_bar:
                        for chunk in download_response.iter_content(chunk_size=8192):
                            if chunk:  # Filter out keep-alive new chunks
                                file.write(chunk)
                                progress_bar.update(len(chunk))
                else:
                    print("Downloading...")
                    file.write(download_response.content)

        # Verify file size if content-length header is available
        if total_size > 0:
            actual_size = os.path.getsize(f"temp/{appName}-{version}.ipa")
            if actual_size != total_size:
                print("File download incomplete. Size mismatch.")
                sys.exit(1)

            print("Download successful.")
        else:
            print("Failed to download the file.")

    except requests.RequestException as e:
        print(f"An HTTP error occurred: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)


def main():
    if not re.match(r"^\.[A-Za-z0-9._-]", session):
        raise Exception("Session cookie is not valid")
    if session:
        check_session(session)
        check_version(version, session)
        quota = check_quota(session)
        if quota:
            download(version, session, dlprogress)
        else:
            print("Quota exceeded. Please try again later.")
    else:
        print("No session cookie found.")
        sys.exit(1)


if __name__ == "__main__":
    main()
