import json
import os
import re
import sys
from itertools import zip_longest
from multiprocessing import Pool, cpu_count

import httpx
from bs4 import BeautifulSoup

API_URL = "https://subwaysurf.fandom.com/api.php"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
}

input_file_path = "temp/upload/characters_links.json"
output_file_path = "temp/upload/characters_outfit.json"


def fetch_page_html(page_title):
    params = {
        "action": "parse",
        "page": page_title,
        "format": "json",
        "prop": "text",
    }
    resp = httpx.get(API_URL, params=params, headers=HEADERS, timeout=60)
    resp.raise_for_status()
    return resp.json()["parse"]["text"]["*"]


_BLANK_LINE = re.compile(r"(?:\s*<br[^>]*>\s*){2,}")


def _outfit_names(infobox):
    th = next(filter(lambda t: "outfit" in t.get_text(strip=True).lower(), infobox.find_all("th")), None)
    if th is None:
        return ["Default Outfit"]
    dtr = th.find_parent("tr").find_next_sibling("tr")
    tds = dtr.find_all("td", recursive=False) if dtr else []
    if not tds:
        return ["Default Outfit"]
    groups = _BLANK_LINE.split(tds[-1].decode_contents())
    extra = list(
        filter(
            None,
            map(
                lambda g: BeautifulSoup(g, "html.parser").get_text("\n", strip=True).split("\n")[0].strip(),
                groups,
            ),
        )
    )
    return ["Default Outfit"] + extra


def _tab_url(tab):
    tbl = tab.find("table")
    rows = ((tbl.find("tbody") or tbl).find_all("tr", recursive=False) or tbl.find_all("tr")) if tbl else []
    img = rows[1].select_one("img") if len(rows) >= 2 else None
    if img is None:
        img = next(
            filter(
                lambda im: not (
                    "logo" in str(im.get("data-src") or im.get("src") or "").lower()
                    or "logo" in str(im.get("alt") or "").lower()
                    or "name.png" in str(im.get("data-src") or im.get("src") or "").lower()
                ),
                tab.select("img"),
            ),
            tab.select_one("img"),
        )
    url = img.get("data-src") or img.get("src") if img is not None else None
    return str(url).split(".png")[0] + ".png" if url else None


def extract_outfits(html):
    soup = BeautifulSoup(html, "html.parser")

    infobox = soup.select_one("table.infobox")
    if not infobox:
        return []

    tabber = infobox.select_one("div.tabber.wds-tabber")
    if tabber:
        tabs = tabber.find_all("div", class_="wds-tab__content")
        pairs = filter(lambda p: p[1], zip_longest(_outfit_names(infobox), list(map(_tab_url, tabs)), fillvalue=""))
        return list(map(lambda p: {"name": p[0], "url": p[1]}, pairs))

    rows = (infobox.find("tbody") or infobox).find_all("tr", recursive=False)
    img = rows[1].select_one("img") if len(rows) > 1 else None
    if img is None:
        tbl = infobox.find("table")
        inner_rows = ((tbl.find("tbody") or tbl).find_all("tr", recursive=False) or tbl.find_all("tr")) if tbl else []
        img = inner_rows[1].select_one("img") if len(inner_rows) >= 2 else None
    if img is None:
        img = next(
            filter(
                lambda im: not (
                    "logo" in str(im.get("data-src") or im.get("src") or "").lower()
                    or "logo" in str(im.get("alt") or "").lower()
                    or "name.png" in str(im.get("data-src") or im.get("src") or "").lower()
                ),
                infobox.select("img"),
            ),
            infobox.select_one("img"),
        )
    url = img.get("data-src") or img.get("src") if img is not None else None
    if url:
        return [{"name": "Default Outfit", "url": str(url).split(".png")[0] + ".png"}]

    return []


def worker(entry):
    name = entry["name"]
    try:
        html = fetch_page_html(name)
        if not html:
            return {"name": name, "outfits": []}

        outfits = extract_outfits(html)
        print(f"Extracted {len(outfits)} outfits for '{name}'")
        return {"name": name, "outfits": outfits}
    except Exception as e:
        print(f"Error processing '{name}': {e}")
        return {"name": name, "outfits": []}


def process_entries(data, limit):
    entries = list(filter(lambda entry: entry.get("available"), data))
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
    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
    with open(output_file_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)


if __name__ == "__main__":
    try:
        limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
        main(limit)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
