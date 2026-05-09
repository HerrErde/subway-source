import json
import sys
from bs4 import BeautifulSoup
from multiprocessing import Pool, cpu_count

input_file_path = "temp/upload/characters_links.json"
output_file_path = "temp/upload/characters_outfit.json"


def create_cf_session():
    from curl_cffi.requests import Session

    return Session(impersonate="chrome")


def load_data(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_data(output, file_path):
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(output, file, indent=2)


def fetch_content(session, url):
    try:
        r = session.get(url, timeout=10)
        r.raise_for_status()
        return BeautifulSoup(r.content, "lxml")
    except Exception:
        return None


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


def extract_data(tabber_div, cleaned_names):
    tabs = tabber_div.find_all("div", class_="wds-tab__content")
    out = []

    for i, tab in enumerate(tabs):
        img = tab.select_one("img")
        if not img:
            continue

        url = img.get("src")
        if not url:
            continue

        if ".png" in url:
            url = url.split(".png")[0] + ".png"

        name = cleaned_names[i] if i < len(cleaned_names) else ""
        out.append({"name": name, "url": url})

    return out


def fetch_data(session, entry):
    if not entry.get("available"):
        return None

    name = entry["name"]
    url = f"https://subwaysurf.fandom.com/wiki/{name.replace(' ', '_')}"

    soup = fetch_content(session, url)
    if soup is None:
        return {"name": name, "outfits": None}

    toc = soup.find(id="toc")
    if not toc:
        return {"name": name, "outfits": None}

    names = extract_names(toc)

    infobox = soup.select_one("table.infobox")
    if not infobox:
        return {"name": name, "outfits": None}

    tabber = infobox.select_one("div.tabber.wds-tabber")
    if not tabber:
        return {"name": name, "outfits": None}

    outfits = extract_data(tabber, names)
    return {"name": name, "outfits": outfits}


def worker(entry):
    session = create_cf_session()
    return fetch_data(session, entry)


def process_entries(data, limit):
    entries = data[:limit]

    workers = min(cpu_count(), 12)
    print(f"Using {workers} parallel workers")

    with Pool(workers) as pool:
        results = pool.map(worker, entries)

    return [r for r in results if r is not None]


def main(limit):
    data = load_data(input_file_path)

    if limit is None or limit <= 0:
        limit = len(data)

    out = process_entries(data, limit)
    save_data(out, output_file_path)


if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    main(limit)
