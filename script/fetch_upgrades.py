import json
import sys

import requests
from bs4 import BeautifulSoup

input_file_path = "temp/upload/boards_links.json"
output_file_path = "temp/upload/boards_upgrades.json"


def load_data(file_path):
    with open(file_path, "r") as file:
        return json.load(file)


def save_data(output, file_path):
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(output, file, indent=2, ensure_ascii=False)


def fetch_content(session, url):
    try:
        response = session.get(url, allow_redirects=True)
        response.raise_for_status()
        return BeautifulSoup(response.content, "html.parser")
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except Exception as e:
        print(f"Error occurred: {e}")
    return None


def extract_data(tabber_div, names):
    # Find all tab content divs within the tabber_div
    tab_content_divs = tabber_div.find_all("div", class_="wds-tab__content")
    data = []

    for i, tab_content_div in enumerate(tab_content_divs):
        name = names[i] if i < len(names) else ""
        a_tag = tab_content_div.find("a")
        img_url = None

        # Extract the href URL from the <a> tag, if it exists
        if (
            a_tag
            and not "File:" in a_tag.get("title", "")
            and not "/wiki/" in a_tag.get("href", "")
        ):
            img_url = a_tag.get("href")
        else:
            img_url = None

        if img_url:
            img_url = img_url.split(".png")[0] + ".png"

        data.append({"name": name, "url": img_url})

    return data


def fetch_data(session, entry):
    if not entry["available"]:
        print(f"Skipping '{entry['name']}'")
        return None

    url = f"https://subwaysurf.fandom.com/wiki/{entry['name'].replace(' ', '_')}"
    print(f"{entry['name']}: {url}")

    soup = fetch_content(session, url)
    if soup is None:
        print(f"Error: Unable to fetch content for {entry['name']}")
        return {"name": entry["name"], "upgrades": None}

    infobox_table = soup.find("table", class_="infobox")
    if infobox_table is None:
        print("Error: Infobox table not found.")
        return {"name": entry["name"], "upgrades": None}

    tabber_div = infobox_table.find("div", class_="tabber wds-tabber")
    if tabber_div is None:
        print("Error: Tabber div not found in infobox table.")
        return {"name": entry["name"], "upgrades": None}

    tbody_elements = infobox_table.select("tbody")

    tr_elements = tbody_elements[0].select("tr")

    if len(tr_elements) > 9:
        names = []

        target_tr = tr_elements[9]
        second_td = target_tr.find_all("td")[1]

        a_tags = target_tr.select("a")
        for a in a_tags:
            title = a.get("title")
            content = a.get_text(strip=True)
            if title and title not in ["Key", "Event Coin", "Shells"]:
                names.append(content)
            else:
                continue

        process = not a_tags or any(
            a.get_text(strip=True) not in ["Key", "Event Coin", "Shells"]
            for a in a_tags
        )

        if process:
            td_content = second_td.get_text(separator="\n", strip=True).split("\n")

            for line in td_content:
                line = line.strip()
                if line and not line.isdigit():
                    names.append(line)

    else:
        names = []

    names.insert(0, "Original")
    if len(names) >= 3:
        names.insert(len(names), "Fully upgraded")

    upgrades = extract_data(tabber_div, names)

    return {"name": entry["name"], "upgrades": upgrades}


def process_entries(data, limit):
    output = []
    try:
        with requests.Session() as session:
            for entry in data[:limit]:
                data = fetch_data(session, entry)
                if data is not None:
                    output.append(data)
    except Exception as e:
        print("Error:", e)
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received. Finishing current processing.")

    return output


def main(limit):
    data = load_data(input_file_path)

    # Handle cases where limit is None or 0
    if limit is None or limit == 0:
        limit = len(data)

    output = process_entries(data, limit)
    save_data(output, output_file_path)


if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    main(limit)
