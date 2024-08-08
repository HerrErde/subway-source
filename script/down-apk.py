import sys
import requests
from bs4 import BeautifulSoup

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
    exit(1)

userAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"
orgName = "sybo-games"
appName = "subwaysurfers"


url = f"https://www.apkmirror.com/apk/{orgName}/{appName}/{appName}-{appVer}-release"

response = requests.get(url, headers={"User-Agent": userAgent})
page = response.text

if 'class="error404"' in page:
    print("noversion", file=sys.stderr)
    sys.exit(1)

if 'class="apkm-badge">' not in page:
    print("noapk", file=sys.stderr)
    sys.exit(1)


# Parse HTML content using BeautifulSoup
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


response = requests.get(
    f"https://www.apkmirror.com{url1}", headers={"User-Agent": userAgent}
)
page2 = response.text
url2 = BeautifulSoup(page2, "html.parser").select_one(
    'a:-soup-contains("Download APK")'
)["href"]

if not url2:
    print("error", file=sys.stderr)
    sys.exit(1)

response = requests.get(
    f"https://www.apkmirror.com{url2}", headers={"User-Agent": userAgent}
)
page3 = response.text
url3 = BeautifulSoup(page3, "html.parser").select_one(
    'a[data-google-vignette="false"][rel="nofollow"]'
)["href"]

if not url3:
    print("error", file=sys.stderr)
    sys.exit(1)

apk_url = f"https://www.apkmirror.com{url3}"
print(apk_url, file=sys.stderr)

response = requests.get(apk_url, headers={"User-Agent": userAgent})
with open(f"temp/{appName}-{appVer}.apk", "wb") as f:
    f.write(response.content)
