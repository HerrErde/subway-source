import json
import sys

import requests
from bs4 import BeautifulSoup

input_file_path = "temp/upload/characters_links.json"
output_file_path = "temp/upload/characters_outfit.json"


def load_data(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
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


def extract_names(appearance_section):
    names = [
        (
            li.find("span", class_="toctext").get_text()
            if li.find("span", class_="toctext")
            else ""
        )
        for li in appearance_section.find_all_next("li")
    ]

    """
    # Clean outfit names and remove duplicates
    cleaned_names = []
    seen_names = set()
    for name in names:
        parts = name.split("Outfit")
        outfit_name = parts[0] + "Outfit" if len(parts) > 2 else parts[0]
        outfit_name = outfit_name.strip()
        if outfit_name and outfit_name not in seen_names:
            cleaned_names.append(outfit_name)
            seen_names.add(outfit_name)
    """

    return names


def extract_data(tabber_div, cleaned_names):
    tab_content_divs = tabber_div.find_all("div", class_="wds-tab__content")
    data = []

    for i, tab_content_div in enumerate(tab_content_divs):
        name = cleaned_names[i] if i < len(cleaned_names) else ""
        img_tag = tab_content_div.find("img")
        if img_tag:
            img_url = img_tag["src"].split(".png")[0] + ".png"
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
        return {"name": entry["name"], "outfits": None}

    toc = soup.find(id="toc")
    if toc is None:
        print("Error: toc element not found.")
        return {"name": entry["name"], "outfits": None}

    appearance_section = toc.find("a", {"href": "#Appearance"})
    if appearance_section is None:
        print("Error: Appearance section not found.")
        return {"name": entry["name"], "outfits": None}

    names = extract_names(appearance_section)

    infobox_table = soup.find("table", class_="infobox")
    if infobox_table is None:
        print("Error: infobox table not found.")
        return {"name": entry["name"], "outfits": None}

    tabber_div = infobox_table.find("div", class_="tabber wds-tabber")
    if tabber_div is None:
        print("Error: tabber div not found in infobox table.")
        return {"name": entry["name"], "outfits": None}

    outfits = extract_data(tabber_div, names)
    return {"name": entry["name"], "outfits": outfits}


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
