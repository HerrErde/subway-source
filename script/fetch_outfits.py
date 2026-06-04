import json
import sys
from multiprocessing import Pool, cpu_count

import httpx
from bs4 import BeautifulSoup

input_file_path = "temp/upload/characters_links.json"
output_file_path = "temp/upload/characters_outfit.json"

API_URL = "https://subwaysurf.fandom.com/api.php"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
}


def fetch_page_html(session, page_title):
    params = {
        "action": "parse",
        "page": page_title,
        "format": "json",
        "prop": "text",
    }
    try:
        resp = session.get(API_URL, params=params, headers=HEADERS, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        return data["parse"]["text"]["*"]
    except Exception as e:
        print(f"Error fetching page '{page_title}': {e}")
        return ""


def extract_names(toc):
    a = toc.select_one('a[href="#Appearance"]')
    if not a:
        return []

    section = a.find_parent("li")
    if not section:
        return []

    ul = section.find_next("ul")
    if not ul:
        return []

    names = []
    for li in ul.find_all("li", recursive=False):
        span = li.find("span", class_="toctext")
        if span:
            names.append(span.get_text(strip=True))

    return names


def normalize_url(url):
    if not url:
        return None
    if ".png" in url:
        return url.split(".png")[0] + ".png"
    return url


def extract_outfits(html):
    soup = BeautifulSoup(html, "html.parser")

    infobox = soup.select_one("table.infobox")
    if not infobox:
        return []

    tabber = infobox.select_one("div.tabber.wds-tabber")
    if tabber:
        toc = soup.find(id="toc")
        names = ["Default Outfit"] + extract_names(toc) if toc else []
        tabs = tabber.find_all("div", class_="wds-tab__content")
        outfits = []
        for i, tab in enumerate(tabs):
            img = tab.select_one("img")
            if not img:
                continue
            url = img.get("data-src") or img.get("src")
            if not url:
                continue
            url = normalize_url(url)
            name = names[i] if i < len(names) else ""
            outfits.append({"name": name, "url": url})
        return outfits

    img = infobox.select_one("img")
    if img:
        url = img.get("data-src") or img.get("src")
        if url:
            return [{"name": "Default Outfit", "url": normalize_url(url)}]

    return []


def worker(entry):
    name = entry["name"]
    session = httpx.Client()
    try:
        html = fetch_page_html(session, name)
        if not html:
            return {"name": name, "outfits": []}

        outfits = extract_outfits(html)
        print(f"Extracted {len(outfits)} outfits for '{name}'")
        return {"name": name, "outfits": outfits}
    except Exception as e:
        print(f"Error processing '{name}': {e}")
        return {"name": name, "outfits": []}
    finally:
        session.close()


def process_entries(data, limit):
    entries = [entry for entry in data if entry.get("available")]
    if limit and limit > 0:
        entries = entries[:limit]

    workers = min(cpu_count(), 12)
    print(f"Using {workers} parallel workers")

    with Pool(workers) as pool:
        results = pool.map(worker, entries)

    return results


def main(limit):
    with open(input_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if limit is None or limit <= 0:
        limit = len(data)

    out = process_entries(data, limit)

    with open(output_file_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)


if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    main(limit)
