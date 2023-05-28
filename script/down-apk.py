import requests
from playwright.sync_api import sync_playwright

userAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"
packageId = "com.kiloo.subwaysurf"
orgName = "sybo-games"
appName = "subwaysurfers"
appName2 = "subway-surfers"

response = requests.get(f"https://gplayapi.srik.me/api/apps/{packageId}")
data = response.json()
version = data["version"]
appVer = version.replace(".", "-")


with sync_playwright() as playwright:
    browser = playwright.chromium.launch()
    context = browser.new_context(user_agent=userAgent)
    page = context.new_page()

    page1_response = page.goto(
        f"https://www.apkmirror.com/apk/{orgName}/{appName}/{appName}-{appVer}-release"
    )
    page1 = page1_response.text()

    if 'class="error404"' in page1:
        print("noversion", file=sys.stderr)
        browser.close()
        exit(1)

    page2 = page1.query_selector("span:contains('APK')").parent().parent().outer_html()

    url1 = page2.query_selector_all(f"div:contains('{arch}')").map(
        lambda element: element.parent_element.query_selector(
            "a.accent_color"
        ).get_attribute("href")
    )

    if len(url1) == 0:
        print("noapk", file=sys.stderr)
        browser.close()
        exit(1)

    url2_response = page.goto(f"https://www.apkmirror.com{url1[-1]}")
    url2 = url2_response.query_selector("a:contains('Download APK')").get_attribute(
        "href"
    )
    print(url2)

    if not url2:
        print("error", file=sys.stderr)
        browser.close()
        exit(1)

    url3_response = page.goto(f"https://www.apkmirror.com{url2}")
    url3 = url3_response.query_selector(
        "a[data-google-vignette='false'][rel='nofollow']"
    ).get_attribute("href")

    if not url3:
        print("error", file=sys.stderr)
        browser.close()
        exit(1)

    print(f"https://www.apkmirror.com{url3}", file=sys.stderr)

    page.goto(f"https://www.apkmirror.com{url3}")
    page.wait_for_load_state("networkidle")
    page.screenshot(path=f"{app_name}-{app_ver}.apk")

    browser.close()
