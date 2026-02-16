import json
from bs4 import BeautifulSoup
import requests

url = "https://subwaysurf.fandom.com/wiki/Player_Profile"
filename = "temp/upload/playerprofile_links.json"

FLARESOLVERR_URL = "http://localhost:8191/v1"


def fetch_data(url):
    """Fetch fully rendered HTML via FlareSolverr"""
    try:
        payload = {"cmd": "request.get", "url": url, "maxTimeout": 60000}
        response = requests.post(FLARESOLVERR_URL, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        html = data.get("solution", {}).get("response", "")
        return html
    except Exception as e:
        print("Error fetching HTML:", e)
        return None


def get_id(html, h3_title):
    """Get the id of the div following the <h3> with the specified title"""
    soup = BeautifulSoup(html, "html.parser")
    for h3_tag in soup.find_all("h3"):
        span_tag = h3_tag.find("span")
        if span_tag and span_tag.get_text(strip=True) == h3_title:
            next_div = h3_tag.find_next_sibling("div")
            if next_div:
                return next_div.get("id", None)
    return None


def fetch_profile(html):
    try:
        gallery_id = get_id(html, "Profile Portraits")
        if not gallery_id:
            print("Profile gallery not found")
            return []

        soup = BeautifulSoup(html, "html.parser")
        gallery_div = soup.find("div", id=gallery_id)
        items = gallery_div.find_all("div", class_="wikia-gallery-item")
        profiles = []

        for item in items:
            img_tag = item.find("div", class_="gallery-image-wrapper").find("img")
            if img_tag:
                img_src = img_tag.get("data-src", "") or img_tag.get("src", "")
                img_src = img_src.split(".png")[0] + ".png"

                lightbox_caption_div = item.find("div", class_="lightbox-caption")
                profile_name = (
                    lightbox_caption_div.text.strip()
                    if lightbox_caption_div
                    else "Unknown"
                )
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
        gallery_id = get_id(html, "Frames")
        if not gallery_id:
            print("Frames gallery not found")
            return []

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
        json.dump(data, f, indent=2, ensure_ascii=False)


def main():
    html = fetch_data(url)
    if html:
        portraits = fetch_profile(html)
        frames = fetch_frame(html)
        save_json(portraits, frames)
    else:
        print("Failed to fetch HTML. Exiting...")


if __name__ == "__main__":
    main()
