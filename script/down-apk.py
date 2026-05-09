import re
import sys
import hashlib
import argparse
from pathlib import Path
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
    if response.status_code == 404:
        print("App dosn't exist", file=sys.stderr)
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


def get_download_links(download_page_url, apkm):
    soup = fetch_page(download_page_url)

    download_btn = soup.select_one("a.downloadButton[href]")
    if not download_btn:
        raise RuntimeError("Download link not found")

    url2 = download_btn["href"]

    safe_div = soup.select_one("#safeDownload")
    if not safe_div:
        raise RuntimeError("safeDownload modal not found")

    # Find the correct hash section header
    header_text = "APK bundle file hashes" if apkm else "APK file hashes"
    header = safe_div.find(lambda t: t.name == "h4" and header_text in t.get_text())

    if not header:
        raise RuntimeError("Hash section not found")

    # SHA-256 is the span after the line containing 'SHA-256:'
    sha256_line = header.find_next(string=lambda s: s and "SHA-256:" in s)
    sha256 = sha256_line.find_next("span", class_="wordbreak-all").get_text(strip=True)

    return url2, sha256


def sha256_verify(file_path, expected_hash):
    file_path = Path(file_path)
    if not file_path.exists():
        return False
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest().lower() == expected_hash.lower()


def download_file(url, file_path):
    file_path = Path(file_path)
    response = SESSION.get(url, stream=True)
    response.raise_for_status()

    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("wb") as f:
        for chunk in response.iter_content(chunk_size=262144):
            if chunk:
                f.write(chunk)


def resolve_package_search(soup):
    row = soup.select_one(".listWidget .appRow h5.appRowTitle a[href]")
    if not row:
        raise RuntimeError("No app found in package search")

    return row["href"]


def resolve_latest_version(soup):
    # find the main listWidget container
    widget = soup.select_one("div.listWidget.p-relative")
    if not widget:
        raise RuntimeError("No listWidget found on app page")

    # get the first appRow link inside this widget
    row = widget.select_one(".appRow h5.appRowTitle a[href]")
    if row:
        return row["href"]

    raise RuntimeError("No latest version found in listWidget")


def download(args):
    if args.org and args.app and args.version:
        version_url = (
            f"https://www.apkmirror.com/apk/{args.org}/{args.app}/"
            f"{args.app}-{args.version}-release"
        )

    elif args.package:
        search_url = (
            f"https://www.apkmirror.com/"
            f"?post_type=app_release&searchtype=app&s={args.package}"
        )
        soup = fetch_page(search_url)

        app_rel = resolve_package_search(soup)
        app_url = f"https://www.apkmirror.com{app_rel}"

        app_soup = fetch_page(app_url)

        latest_rel = resolve_latest_version(app_soup)

        if args.version:
            parts = latest_rel.rstrip("/").split("/")
            last = parts[-1].split("-")

            prefix = "-".join(last[:-4])

            new_last = f"{prefix}-{args.version}-release"
            parts[-1] = new_last
            version_url = "https://www.apkmirror.com" + "/".join(parts) + "/"
        else:
            version_url = f"https://www.apkmirror.com{latest_rel}"

    soup = fetch_page(version_url)

    badges = [b.get_text(strip=True) for b in soup.select(".apkm-badge")]

    if args.apkm:
        apktype = "bundle"
    elif "APK" in badges:
        apktype = "apk"
    elif "BUNDLE" in badges:
        apktype = "bundle"
    else:
        apktype = None

    if not apktype:
        print("No APK or bundle found on page.", file=sys.stderr)
        sys.exit(1)

    url1 = get_apk_download_page(soup, apktype)
    download_page_url = f"https://www.apkmirror.com{url1}"

    apkm = True if args.apkm or apktype == "bundle" else False

    url2, sha256 = get_download_links(download_page_url, apkm)
    final_download_page = f"https://www.apkmirror.com{url2}"

    soup = fetch_page(final_download_page)
    link_tag = soup.select_one("#download-link")
    if not link_tag or not link_tag.get("href"):
        print("Final download link not found.", file=sys.stderr)
        sys.exit(1)
    apk_url = f"https://www.apkmirror.com{link_tag['href']}"

    if args.output:
        file_path = args.output
    else:
        last_component = version_url.rstrip("/").split("/")[-1]
        if last_component.endswith("-release"):
            last_component = last_component[: -len("-release")]
        ext = ".apkm" if apktype == "bundle" else ".apk"
        file_path = f"{last_component}{ext}"

    if sha256_verify(file_path, sha256) and not args.force:
        print(f"File '{file_path}' already exists and SHA-256 verified.")
        return

    print(f"Downloading {file_path}")
    download_file(apk_url, file_path)

    if not sha256_verify(file_path, sha256):
        print("SHA-256 mismatch! File may be corrupt or tampered.", file=sys.stderr)
        sys.exit(1)

    print(f"Download completed successfully: {file_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Download APK or bundle from APKMirror"
    )
    parser.add_argument("-p", "--package", help="The app package name")
    parser.add_argument("--org", help="Organization (e.g., sybo-games)")
    parser.add_argument("--app", help="App name (e.g., subway-surfers)")
    parser.add_argument("-v", "--version", default=None, help="Version (X-Y-Z)")
    parser.add_argument("-o", "--output", help="Output file path")
    parser.add_argument("--apkm", action="store_true", help="Download the Apkm file")
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Force downloading file, even when it already exists",
    )
    args = parser.parse_args()

    if args.version and not re.match(r"^\d{1,2}-\d{1,2}-\d{1,2}$", args.version):
        print("Invalid version format. Use X-Y-Z (e.g., 3-57-0).", file=sys.stderr)
        sys.exit(1)

    if args.package:
        pass
    elif args.org and args.app and args.version:
        pass
    else:
        print(
            "Invalid arguments. Use either:\n"
            "  --package <package.name>\n"
            "or:\n"
            "  --org <org> --app <app> --version X-Y-Z",
            file=sys.stderr,
        )
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
