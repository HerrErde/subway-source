import os
import re
import sys

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

if len(sys.argv) < 2:
    print(
        "Error: Invalid version format. Please use the format 'X-Y-Z' (e.g., '3-12-2')."
    )
    sys.exit(1)


appVer = sys.argv[1]

if not re.match(r"^\d{1,2}-\d{1,2}-\d{1,2}$", appVer):
    print(
        "Error: Invalid version format. Please use the format 'X-Y-Z' (e.g., '3-12-2')."
    )
    sys.exit(1)

dlprogress = sys.argv[2]


userAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"
orgName = "sybo-games"
appName = "subwaysurfers"
headers = {
    "User-Agent": userAgent,
}

url = f"https://www.apkmirror.com/apk/{orgName}/{appName}/{appName}-{appVer}-release"

response = requests.get(url, headers=headers)
page = response.text

if 'class="error404"' in page:
    print("noversion", file=sys.stderr)
    sys.exit(1)

if 'class="apkm-badge">' not in page:
    print("noapk", file=sys.stderr)
    sys.exit(1)


soup = BeautifulSoup(page, "html.parser")

# Find all <div> elements with class "table-cell rowheight addseparator expand pad dowrap"
table_cell_divs = soup.find_all(
    "div", class_="table-cell rowheight addseparator expand pad dowrap"
)

if not table_cell_divs:
    print(
        "Error: Required div 'table-cell rowheight addseparator expand pad dowrap' not found.",
        file=sys.stderr,
    )
    sys.exit(1)

# print(f"Found {len(table_cell_divs)} 'table-cell rowheight addseparator expand pad dowrap' div(s) on the page.")

# Iterate through each found div
for table_cell_div in table_cell_divs:
    # Find <span class="apkm-badge"> with text containing "APK" inside the current div
    span_apkm_badge = table_cell_div.find(
        "span", class_="apkm-badge", string=lambda text: text and "APK" in text
    )

    # Find <a class="accent_color"> inside the current div if the required span is found
    if span_apkm_badge:
        a_accent_color = table_cell_div.find("a", class_="accent_color")
        if a_accent_color and "href" in a_accent_color.attrs:
            url1 = a_accent_color["href"]
            print("APK Download URL:", url1)
            break  # Stop after finding the first valid APK URL
else:
    print("Error: APK download URL not found.", file=sys.stderr)
    sys.exit(1)


response = requests.get(f"https://www.apkmirror.com{url1}", headers=headers)
page2 = response.text
url2 = BeautifulSoup(page2, "html.parser").select_one(
    'a:-soup-contains("Download APK")'
)["href"]

if not url2:
    print("error", file=sys.stderr)
    sys.exit(1)

response = requests.get(f"https://www.apkmirror.com{url2}", headers=headers)
page3 = response.text
url3 = BeautifulSoup(page3, "html.parser").select_one("#download-link")["href"]

if not url3:
    print("error", file=sys.stderr)
    sys.exit(1)

apk_url = f"https://www.apkmirror.com{url3}"
print(apk_url, file=sys.stderr)

try:
    download_response = requests.get(apk_url, headers=headers)
    download_response.raise_for_status()

    if download_response.status_code == 200:

        # Get total file size from headers
        total_size = int(download_response.headers.get("content-length", 0))

        file_path = f"temp/{appName}-{appVer}.apk"

        # Open file for writing in binary mode
        with open(file_path, "wb") as file:
            if dlprogress is True:

                # Initialize tqdm progress bar
                progress_bar = tqdm(
                    total=total_size,
                    unit="B",
                    unit_scale=True,
                    unit_divisor=1024,
                    desc="Downloading",
                )

                # Write file in chunks and update progress bar
                for chunk in download_response.iter_content(chunk_size=8192):
                    if chunk:  # Filter out keep-alive new chunks
                        file.write(chunk)
                        progress_bar.update(len(chunk))

                progress_bar.close()
            else:
                print("Downloading...")
                file.write(download_response.content)

    # Verify file size if content-length header is available
    if total_size > 0:
        actual_size = os.path.getsize(file_path)
        if actual_size != total_size:
            print("File download incomplete. Size mismatch.")
            sys.exit(1)

        print("Download successful.")
    else:
        print("Failed to download the file.")

except requests.exceptions.HTTPError:
    print(f"Error fetching version information: {response.status_code}")
    sys.exit(1)
