import json
import requests
from bs4 import BeautifulSoup
import sys


def fetch_outfits(session, entry):
    name = entry["name"].replace(" ", "_")
    url = f"https://subwaysurf.fandom.com/wiki/{name}"
    print(f"'{entry['name']}': {url}")

    response = session.get(url)
    content = response.content
    soup = BeautifulSoup(content, "html.parser")
    toc = soup.find(id="toc")

    if toc is None:
        print("Error: toc element not found.")
        return {"name": entry["name"], "outfits": None}

    toctext_spans = toc.find_all("span", class_="toctext")
    exclude = [
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
    ]
    outfits = [
        {"name": span.get_text(strip=True), "url": ""}
        for span in toctext_spans
        if span.get_text(strip=True) not in exclude
    ]
    tabber_div = soup.find("div", class_="tabber wds-tabber")

    if tabber_div is None:
        print("Error: tabber div not found.")
        return {"name": entry["name"], "outfits": None}

    for i, tab_content_div in enumerate(
        tabber_div.find_all("div", class_="wds-tab__content")
    ):
        outfit_name = tab_content_div.find("a").get_text(strip=True)
        img_tag = tab_content_div.find("img")
        img_url = img_tag["src"]
        img_url = img_url.split(".png")[0] + ".png"
        outfits[i]["url"] = img_url

    return {"name": entry["name"], "outfits": outfits}


def main(limit=None):
    with open("characters_links.json", "r") as file:
        data = json.load(file)

    output = []

    try:
        with requests.Session() as session:
            for entry in data[:limit]:
                output.append(fetch_outfits(session, entry))

    except KeyboardInterrupt:
        print("\nKeyboard interrupt received. Finishing current processing.")

    with open("characters_outfit.json", "w", encoding="utf-8") as file:
        json.dump(output, file, indent=2, ensure_ascii=False)

    print("Exiting gracefully.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        limit = int(sys.argv[1])
        main(limit)
    else:
        main()
