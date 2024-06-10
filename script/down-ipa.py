import sys
import requests

if len(sys.argv) < 2:
    print(
        "Error: Invalid version format. Please use the format 'X-Y-Z' (e.g., '3-12-2')."
    )
    sys.exit(1)

userAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"

appVer = sys.argv[1].replace("-", ".")
appName = "subwaysurfers"

url = f"https://dl.iosvizor.net/subway-surfers/Subway-Surfers-v{appVer}-iosvizor.ipa"

response = requests.get(url, headers={"User-Agent": userAgent})

appVer = sys.argv[1].replace(".", "-")

if response.status_code == 200:
    with open(f"{appName}-{appVer}.ipa", "wb") as f:
        f.write(response.content)
    print(f"Downloaded {appName} version {appVer} successfully.")
else:
    print(
        f"Failed to download {appName} version {appVer}. HTTP status code: {response.status_code}"
    )
