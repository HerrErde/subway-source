import json
import sys
import requests
from bs4 import BeautifulSoup


def fetch_outfits(session, entry):
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

    exclude = {
        "Appearance",
        "History",
        "Trivia",
        "Gallery",
        "Video",
        "Videos",
        "Old Outfit",
        "Old Default",
        "Reappearance",
        "Re-sale",
        "Re-sales",
        "References",
    }

    toctext_spans = toc.find_all("span", class_="toctext")
    outfits = [
        {
            "name": span.get_text(strip=True),
            "url": "",
        }
        for span in toctext_spans
        if span.get_text(strip=True) not in exclude
    ]

    tabber_div = soup.find("div", class_="tabber wds-tabber")

    if tabber_div is None:
        print("Error: tabber div not found.")
        return {"name": entry["name"], "outfits": None}

    tab_content_divs = tabber_div.find_all("div", class_="wds-tab__content")

    if len(outfits) != len(tab_content_divs):
        print(
            f"Error: Number of outfits ({len(outfits)}) doesn't match the number of tab content divs ({len(tab_content_divs)})."
        )
        return {"name": entry["name"], "outfits": None}

    for i, tab_content_div in enumerate(tab_content_divs):
        outfit_name = tab_content_div.find("a").get_text(strip=True)
        img_tag = tab_content_div.find("img")
        if img_tag:
            img_url = img_tag["src"]
            img_url = img_url.replace(".png", "_hd.png")
            img_url = (
                img_url.split(".png")[0] + ".png" if ".png" in img_url else img_url
            )
            outfits[i]["url"] = img_url

    return {"name": entry["name"], "outfits": outfits}


def main(limit=None):
    with open("upload/characters_links.json", "r") as file:
        data = json.load(file)

    output = []

    try:
        with requests.Session() as session:
            for entry in data[:limit]:
                output.append(fetch_outfits(session, entry))

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
