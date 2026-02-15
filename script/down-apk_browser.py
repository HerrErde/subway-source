import os
import re
import sys
import hashlib
import argparse
from playwright.sync_api import sync_playwright


BASE = "https://www.apkmirror.com"


def sha256_verify(file_path, expected_hash):
    if not os.path.exists(file_path):
        return False
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest().lower() == expected_hash.lower()


def download_file(page, file_path, show_progress=True):
    with page.expect_download() as download_info:
        page.click("#download-link")

    download = download_info.value

    temp_path = download.path()
    total_size = os.path.getsize(temp_path)

    download.save_as(file_path)


def get_apk_download_page(page, apk_type):
    badge_text = "APK" if apk_type == "apk" else "BUNDLE"
    badge_class = "apkm-badge" if apk_type == "apk" else "apkm-badge success"

    rows = page.locator(
        "div.table-cell.rowheight.addseparator.expand.pad.dowrap-break-all"
    )

    count = rows.count()
    if count == 0:
        raise Exception("No download entries found.")

    for i in range(count):
        row = rows.nth(i)
        badge = row.locator(f"span.{badge_class}", has_text=badge_text)
        if badge.count() > 0:
            link = row.locator("a.accent_color").first
            href = link.get_attribute("href")
            if href:
                return href

    raise Exception(f"{apk_type} download URL not found.")


def get_download_links(page):
    download_btn = page.locator("a.downloadButton").first
    if download_btn.count() == 0:
        raise Exception("Download link not found.")

    url2 = download_btn.get_attribute("href")

    sha_spans = page.locator("#safeDownload span.wordbreak-all")
    if sha_spans.count() == 0:
        raise Exception("SHA-256 hash not found.")

    sha256 = sha_spans.nth(sha_spans.count() - 1).inner_text().strip()
    return url2, sha256


def detect_apk_type(page):
    if page.locator("span.apkm-badge", has_text="APK").count() > 0:
        return "apk"
    if page.locator("span.apkm-badge.success", has_text="BUNDLE").count() > 0:
        return "bundle"
    return None


def download(args):
    version_url = f"{BASE}/apk/{args.org}/{args.app}/{args.app}-{args.version}-release"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        page.goto(version_url, wait_until="domcontentloaded")

        apktype = detect_apk_type(page)
        if not apktype:
            raise Exception("No APK or bundle found on page.")

        url1 = get_apk_download_page(page, apktype)
        download_page_url = f"{BASE}{url1}"

        page.goto(download_page_url, wait_until="domcontentloaded")
        url2, sha256 = get_download_links(page)

        final_download_page = f"{BASE}{url2}"
        page.goto(final_download_page, wait_until="domcontentloaded")

        link_tag = page.locator("#download-link").first
        if link_tag.count() == 0:
            raise Exception("Final download link not found.")

        apk_url = f"{BASE}{link_tag.get_attribute('href')}"

        file_path = args.output or (
            f"{args.app}-{args.version}.apk"
            if apktype == "apk"
            else f"{args.app}-{args.version}.apkm"
        )

        if sha256_verify(file_path, sha256):
            print(f"File '{file_path}' already exists and SHA-256 verified.")
            browser.close()
            return

        download_file(page, file_path)

        if not sha256_verify(file_path, sha256):
            browser.close()
            raise Exception("SHA-256 mismatch! File may be corrupt.")

        browser.close()

    print(f"Download completed successfully: {file_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Download APK or bundle from APKMirror (Playwright version)"
    )
    parser.add_argument("--org", required=True)
    parser.add_argument("--app", required=True)
    parser.add_argument("-v", "--version", required=True)
    parser.add_argument("-o", "--output")

    args = parser.parse_args()

    if not re.match(r"^\d{1,2}-\d{1,2}-\d{1,2}$", args.version):
        print("Invalid version format. Use X-Y-Z (e.g., 3-57-0).", file=sys.stderr)
        sys.exit(1)

    try:
        download(args)
    except KeyboardInterrupt:
        print("Script terminated by user.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
