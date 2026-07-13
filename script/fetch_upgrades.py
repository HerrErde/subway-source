import json
import os
import sys
from multiprocessing import Pool, cpu_count

import httpx
from bs4 import BeautifulSoup

API_URL = "https://subwaysurf.fandom.com/api.php"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
}

input_file_path = "temp/upload/boards_links.json"
output_file_path = "temp/upload/boards_upgrades.json"


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


def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data, file_path):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def extract_upgrades(html):
    soup = BeautifulSoup(html, "html.parser")

    infobox = soup.select_one("table.infobox")
    if not infobox:
        return []

    tabber = infobox.select_one("div.tabber.wds-tabber")
    if not tabber:
        return []

    tbody = infobox.find("tbody")
    tr_elements = tbody.find_all("tr") if tbody else []

    names = []
    if len(tr_elements) > 9:
        target_tr = tr_elements[9]
        a_tags = target_tr.select("a")
        for a in a_tags:
            title = a.get("title")
            content = a.get_text(strip=True)
            if title and title not in ["Key", "Event Coin", "Shells"]:
                names.append(content)

        process = not a_tags or any(
            a.get_text(strip=True) not in ["Key", "Event Coin", "Shells"]
            for a in a_tags
        )

        if process:
            td_cells = target_tr.find_all("td")
            if len(td_cells) >= 2:
                td_content = (
                    td_cells[1].get_text(separator="\n", strip=True).split("\n")
                )
                for line in td_content:
                    line = line.strip()
                    if line and not line.isdigit():
                        names.append(line)

    names.insert(0, "Original")
    if len(names) >= 3:
        names.append("Fully upgraded")

    tabs = tabber.find_all("div", class_="wds-tab__content")
    upgrades = []

    for i, tab in enumerate(tabs):
        name = names[i] if i < len(names) else ""
        a_tag = tab.find("a")
        img_url = None

        if (
            a_tag
            and "File:" not in a_tag.get("title", "")
            and "/wiki/" not in a_tag.get("href", "")
        ):
            img_url = a_tag.get("href")
            img_url = img_url.split(".png")[0] + ".png"

        upgrades.append({"name": name, "url": img_url})

    return upgrades


def worker(entry):
    name = entry["name"]
    try:
        html = fetch_page_html(name)
        if not html:
            return {"name": name, "upgrades": []}

        upgrades = extract_upgrades(html)
        print(f"Extracted {len(upgrades)} upgrades for '{name}'")
        return {"name": name, "upgrades": upgrades}
    except Exception as e:
        print(f"Error processing '{name}': {e}")
        return {"name": name, "upgrades": []}


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
    data = load_json(input_file_path)

    if limit is None or limit <= 0:
        limit = len(data)

    out = process_entries(data, limit)
    save_json(out, output_file_path)


if __name__ == "__main__":
    try:
        limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
        main(limit)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
