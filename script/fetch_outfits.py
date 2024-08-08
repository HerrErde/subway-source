import json
import sys
import requests
from bs4 import BeautifulSoup


def fetch_outfits(session, entry):
    if not entry["available"]:
        print(f"Skipping '{entry['name']}'")
        return None

    name = entry["name"].replace(" ", "_")
    url = f"https://subwaysurf.fandom.com/wiki/{name}"
    print(f"'{entry['name']}': {url}")

    try:
        response = session.get(url)
        response.raise_for_status()
        content = response.content
        soup = BeautifulSoup(content, "html.parser")
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        return {"name": entry["name"], "outfits": None}
    except Exception as err:
        print(f"Error occurred: {err}")
        return {"name": entry["name"], "outfits": None}

    toc = soup.find(id="toc")
    if toc is None:
        print("Error: toc element not found.")
        return {"name": entry["name"], "outfits": None}

    appearance_section = toc.find("a", {"href": "#Appearance"})
    if appearance_section is None:
        print("Error: Appearance section not found.")
        return {"name": entry["name"], "outfits": None}

    outfit_names = [
        (
            li.find("span", class_="toctext").get_text()
            if li.find("span", class_="toctext")
            else ""
        )
        for li in appearance_section.find_all_next("li")
    ]

    # Remove everything after "Outfit" and eliminate duplicates
    cleaned_outfit_names = []
    seen_names = set()
    for name in outfit_names:
        parts = name.split("Outfit")
        outfit_name = parts[0] + "Outfit" if len(parts) > 1 else name
        outfit_name = outfit_name.strip()
        if outfit_name and outfit_name not in seen_names:
            cleaned_outfit_names.append(outfit_name)
            seen_names.add(outfit_name)

    infobox_table = soup.find("table", class_="infobox")
    if infobox_table is None:
        print("Error: infobox table not found.")
        return {"name": entry["name"], "outfits": None}

    tabber_div = infobox_table.find("div", class_="tabber wds-tabber")
    if tabber_div is None:
        print("Error: tabber div not found in infobox table.")
        return {"name": entry["name"], "outfits": None}

    tab_content_divs = tabber_div.find_all("div", class_="wds-tab__content")
    outfits = []
    tab_labels = tabber_div.find_all("div", class_="wds-tabs__tab-label")

    for i, tab_content_div in enumerate(tab_content_divs):
        outfit_name = cleaned_outfit_names[i] if i < len(cleaned_outfit_names) else ""
        img_tag = tab_content_div.find("img")
        if img_tag:
            img_url = img_tag["src"]
            img_url = img_url.split(".png")[0] + ".png"
            outfits.append({"name": outfit_name, "url": img_url})

    return {"name": entry["name"], "outfits": outfits}


def main(limit=None):
    with open("upload/characters_links.json", "r") as file:
        data = json.load(file)

    output = []

    try:
        with requests.Session() as session:
            for entry in data[:limit]:
                outfits_data = fetch_outfits(session, entry)
                if outfits_data is not None:
                    output.append(outfits_data)
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received. Finishing current processing.")

    with open("upload/characters_outfit.json", "w", encoding="utf-8") as file:
        json.dump(output, file, indent=2, ensure_ascii=False)

    print("Exiting gracefully.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        limit = int(sys.argv[1])
        main(limit)
    else:
        main()
