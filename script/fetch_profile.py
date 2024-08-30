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


def get_id(h3_title):
    response = requests.get(url)
    response.raise_for_status()  # Check for request errors

    soup = BeautifulSoup(response.text, "html.parser")

    # Find <h3> tags and check their <span> children
    for h3_tag in soup.find_all("h3"):
        span_tag = h3_tag.find("span")
        if span_tag.get_text(strip=True) == h3_title:
            # Find the next <div> tag after the <h3> tag
            next_div = h3_tag.find_next_sibling("div")
            if next_div:
                # Return the 'id' attribute of the <div> tag if it exists
                return next_div.get(
                    "id", "The <div> tag does not have an id attribute."
                )
            else:
                return "No <div> tag found after the <h3> tag."

    return "No <h3> tag with the specified text found."


def fetch_profile(html):
    try:
        gallery_id = get_id("Profile Portraits")

        soup = BeautifulSoup(html, "html.parser")
        gallery_div = soup.find("div", id=gallery_id)

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
                    profile_name = item.find(
                        "div", class_="lightbox-caption"
                    ).text.strip()
                    profile_name = profile_name.split(" profile portrait")[0]
                    profile_name = profile_name.split(" outfit")[0]

                profiles.append({"name": profile_name, "img_url": img_src})
                print("Profile Name:", profile_name)

        return profiles

    except Exception as e:
        print("Error fetching profile:", e)
        return []


def fetch_frame(html):
    try:
        gallery_id = get_id("Frames")

        soup = BeautifulSoup(html, "html.parser")
        gallery_div = soup.find("div", id=gallery_id)

        items = gallery_div.find_all("div", class_="wikia-gallery-item")
        frames = []

        for item in items:
            img_tag = item.find("div", class_="gallery-image-wrapper").find("img")
            if img_tag:
                img_src = img_tag.get("data-src", "") or img_tag.get("src", "")
                img_src = img_src.split(".png")[0] + ".png"
                frame_name = item.find("div", class_="lightbox-caption").text.strip()
                frame_name = frame_name.split("frame (")[0].strip()
                frames.append({"name": frame_name, "img_url": img_src})
                print("Frame Name:", frame_name)

        return frames

    except Exception as e:
        print("Error fetching frame:", e)
        return []


def save_json(portraits, frames):
    data = {"Portraits": portraits, "Frames": frames}

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2,ensure_ascii=False)


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
