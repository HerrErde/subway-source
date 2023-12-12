import sys
import requests
from bs4 import BeautifulSoup

if len(sys.argv) < 2:
    print(
        "Error: Invalid version format. Please use the format 'X-Y-Z' (e.g., '3-12-2')."
    )
    sys.exit(1)

userAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"
orgName = "sybo-games"
appName = "subwaysurfers"
appName2 = "subway-surfers"

appVer = sys.argv[1]

url = f"https://www.apkmirror.com/apk/{orgName}/{appName}/{appName}-{appVer}-release"

response = requests.get(url, headers={"User-Agent": userAgent})
page = response.text

if 'class="error404"' in page:
    print("noversion", file=sys.stderr)
    sys.exit(1)

if 'class="apkm-badge">' not in page:
    print("noapk", file=sys.stderr)
    sys.exit(1)

# Temp fix
url1 = f"/apk/{orgName}/{appName}/{appName}-{appVer}-release/{appName2}-{appVer}-android-apk-download/"

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
with open(f"{appName}-{appVer}.apk", "wb") as f:
    f.write(response.content)
