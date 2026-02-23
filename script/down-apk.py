import os
import re
import sys
import hashlib
import argparse
from bs4 import BeautifulSoup


def create_cf_session():
    from curl_cffi.requests import Session

    return Session(impersonate="chrome")


SESSION = create_cf_session()


def fetch_page(url):
    response = SESSION.get(url)
    if response.status_code == 429:
        print("Rate limited", file=sys.stderr)
        sys.exit(1)
    if response.status_code != 200:
        print(f"Failed to fetch {url} ({response.status_code})", file=sys.stderr)
        sys.exit(1)
    return BeautifulSoup(response.text, "html.parser")


def get_apk_download_page(soup, apk_type):
    table_divs = soup.find_all(
        "div", class_="table-cell rowheight addseparator expand pad dowrap-break-all"
    )
    if not table_divs:
        print("No download entries found.", file=sys.stderr)
        sys.exit(1)

    badge_text = "APK" if apk_type == "apk" else "BUNDLE"
    badge_class = "apkm-badge" if apk_type == "apk" else "apkm-badge success"

    for div in table_divs:
        badge = div.find(
            "span", class_=badge_class, string=lambda t: t and badge_text in t
        )
        if badge:
            a_tag = div.find("a", class_="accent_color")
            if a_tag and a_tag.get("href"):
                return a_tag["href"]

    print(f"{apk_type} download URL not found.", file=sys.stderr)
    sys.exit(1)


def get_download_links(download_page_url):
    soup = fetch_page(download_page_url)

    download_btn = soup.find("a", class_="downloadButton")
    if not download_btn or not download_btn.get("href"):
        print("Download link not found.", file=sys.stderr)
        sys.exit(1)

    url2 = download_btn["href"]

    # Find the correct <h4>
    target_h4 = None
    for h4 in soup.find_all("h4"):
        if h4.get_text(strip=True) in (
            "APK file hashes",
            "APK bundle file hashes",
        ):
            target_h4 = h4
            break

    if not target_h4:
        print("Hash section not found.", file=sys.stderr)
        sys.exit(1)

    sha256_hash = None

    # Traverse everything after the <h4>
    for element in target_h4.find_all_next():
        if element.name == "h4":
            break

        if element.name == "span" and "wordbreak-all" in element.get("class", []):
            text = element.get_text(strip=True)

            if re.fullmatch(r"[a-fA-F0-9]{64}", text):
                sha256_hash = text
                break

    if not sha256_hash:
        print("SHA-256 hash not found.", file=sys.stderr)
        sys.exit(1)

    return url2, sha256_hash


def sha256_verify(file_path, expected_hash):
    if not os.path.exists(file_path):
        return False
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest().lower() == expected_hash.lower()


def download_file(url, file_path):
    response = SESSION.get(url, stream=True)
    response.raise_for_status()

    with open(file_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=262144):
            if chunk:
                f.write(chunk)


def download(args):
    version_url = f"https://www.apkmirror.com/apk/{args.org}/{args.app}/{args.app}-{args.version}-release"
    soup = fetch_page(version_url)

    page = str(soup)

    if not args.apktype:
        apktype = (
            "apk"
            if 'class="apkm-badge">' in page
            else "bundle" if ">BUNDLE<" in page else None
        )
    else:
        apktype = args.apktype

    if not apktype:
        print("No APK or bundle found on page.", file=sys.stderr)
        sys.exit(1)

    url1 = get_apk_download_page(soup, apktype)
    download_page_url = f"https://www.apkmirror.com{url1}"

    url2, sha256 = get_download_links(download_page_url)
    final_download_page = f"https://www.apkmirror.com{url2}"

    soup = fetch_page(final_download_page)
    link_tag = soup.select_one("#download-link")
    if not link_tag or not link_tag.get("href"):
        print("Final download link not found.", file=sys.stderr)
        sys.exit(1)
    apk_url = f"https://www.apkmirror.com{link_tag['href']}"

    file_path = args.output or (
        f"{args.app}-{args.version}.apk"
        if apktype == "apk"
        else f"{args.app}-{args.version}.apkm"
    )

    if sha256_verify(file_path, sha256):
        print(f"File '{file_path}' already exists and SHA-256 verified.")
        return

    download_file(apk_url, file_path)

    if not sha256_verify(file_path, sha256):
        print("SHA-256 mismatch! File may be corrupt or tampered.", file=sys.stderr)
        sys.exit(1)

    print(f"Download completed successfully: {file_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Download APK or bundle from APKMirror"
    )
    parser.add_argument("--org", required=True, help="Organization (e.g., sybo-games)")
    parser.add_argument("--app", required=True, help="App name (e.g., subway-surfers)")
    parser.add_argument("-v", "--version", required=True, help="Version (X-Y-Z)")
    parser.add_argument("-o", "--output", help="Output file path")
    parser.add_argument(
        "--apktype",
        choices=["apk", "bundle"],
        help="The apk type",
    )
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
