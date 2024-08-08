import requests
from bs4 import BeautifulSoup
import json

url = "https://subwaysurf.fandom.com/wiki/Player_Profile"

filename = "temp/upload/playerprofile_links.json"


def fetch_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.text
        return data
    except Exception as e:
        print("Error fetching HTML:", e)
        return None


def fetch_profile(html):
    try:
        soup = BeautifulSoup(html, "html.parser")
        gallery_div = soup.find("div", id="gallery-1")

        if not gallery_div:
            raise ValueError("Gallery div with id 'gallery-1' not found")

        items = gallery_div.find_all("div", class_="wikia-gallery-item")
        profiles = []

        for item in items:
            img_tag = item.find("div", class_="gallery-image-wrapper").find("img")
            if img_tag:
                img_src = img_tag.get("data-src", "") or img_tag.get("src", "")
                img_src = img_src.split(".png")[0] + ".png"

                # Fetch the title from the anchor tag within the lightbox-caption div
                lightbox_caption_div = item.find("div", class_="lightbox-caption")
                if lightbox_caption_div:
                    anchor_tag = lightbox_caption_div.find("a")
                    profile_name = (
                        anchor_tag.get("title", "").strip() if anchor_tag else ""
                    )

                profiles.append({"name": profile_name, "img_url": img_src})

        return profiles

    except Exception as e:
        print("Error fetching profile:", e)
        return []


def fetch_frame(html):
    try:
        soup = BeautifulSoup(html, "html.parser")
        gallery_div = soup.find("div", id="gallery-2")

        if not gallery_div:
            raise ValueError("Gallery div with id 'gallery-2' not found")

        items = gallery_div.find_all("div", class_="wikia-gallery-item")
        frames = []

        for item in items:
            img_tag = item.find("div", class_="gallery-image-wrapper").find("img")
            if img_tag:
                img_src = img_tag.get("data-src", "") or img_tag.get("src", "")
                img_src = img_src.split(".png")[0] + ".png"
                frame_name = item.find("div", class_="lightbox-caption").text.strip()
                frame_name = frame_name.split(" (from ")[
                    0
                ]  # Remove " (from " and everything after it
                frames.append({"name": frame_name, "img_url": img_src})

        return frames

    except Exception as e:
        print("Error fetching frame:", e)
        return []


def save_json(portraits, frames):
    data = {"Portraits": portraits, "Frames": frames}

    with open(filename, "w") as f:
        json.dump(data, f, indent=2)


def main():
    data = fetch_data(url)
    if data:
        portraits = fetch_profile(data)
        frames = fetch_frame(data)
        save_json(portraits, frames)
    else:
        print("Failed to fetch HTML. Exiting...")


if __name__ == "__main__":
    main()
