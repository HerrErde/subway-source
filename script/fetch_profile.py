import json

from bs4 import BeautifulSoup

url = "https://subwaysurf.fandom.com/wiki/Player_Profile"

filename = "temp/upload/playerprofile_links.json"


def create_cf_session():
    from curl_cffi.requests import Session

    return Session(impersonate="chrome")


SESSION = create_cf_session()


def fetch_data(url):
    try:
        response = SESSION.get(url)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except Exception as e:
        print("Error fetching HTML:", e)
        return None


def get_id(soup, h3_title):
    for h3_tag in soup.find_all("h3"):
        span_tag = h3_tag.find("span")
        if span_tag and span_tag.get_text(strip=True) == h3_title:
            next_div = h3_tag.find_next_sibling("div")
            if next_div:
                return next_div.get("id")

    return None


def fetch_profile(soup):
    try:
        gallery_id = get_id(soup, "Profile Portraits")
        if not gallery_id:
            return []

        gallery_div = soup.find("div", id=gallery_id)
        if gallery_div is None:
            return []

        items = gallery_div.find_all("div", class_="wikia-gallery-item")
        profiles = []

        for item in items:
            image_wrapper = item.find("div", class_="gallery-image-wrapper")
            img_tag = image_wrapper.find("img") if image_wrapper else None
            if img_tag:
                img_src = img_tag.get("data-src", "") or img_tag.get("src", "")
                img_src = img_src.split(".png")[0] + ".png"

                lightbox_caption_div = item.find("div", class_="lightbox-caption")
                if lightbox_caption_div is None:
                    continue

                profile_name = lightbox_caption_div.get_text(strip=True)
                if not profile_name:
                    continue

                profile_name = profile_name.split(" profile portrait")[0]
                profile_name = profile_name.split(" outfit")[0]

                profiles.append({"name": profile_name, "img_url": img_src})
                print("Profile Name:", profile_name)

        return profiles

    except Exception as e:
        print("Error fetching profile:", e)
        return []


def fetch_frame(soup):
    try:
        gallery_id = get_id(soup, "Frames")
        if not gallery_id:
            return []

        gallery_div = soup.find("div", id=gallery_id)
        if gallery_div is None:
            return []

        items = gallery_div.find_all("div", class_="wikia-gallery-item")
        frames = []

        for item in items:
            image_wrapper = item.find("div", class_="gallery-image-wrapper")
            img_tag = image_wrapper.find("img") if image_wrapper else None
            if not img_tag:
                continue

            img_src = img_tag.get("data-src", "") or img_tag.get("src", "")
            img_src = img_src.split(".png")[0] + ".png"

            caption = item.find("div", class_="lightbox-caption")
            if caption is None:
                continue

            name_link = caption.find("a")
            if name_link is None:
                continue

            frame_name = name_link.get_text(strip=True)

            if not frame_name:
                continue

            frames.append(
                {
                    "name": frame_name,
                    "img_url": img_src,
                }
            )

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
    soup = fetch_data(url)
    if soup:
        portraits = fetch_profile(soup)
        frames = fetch_frame(soup)
        save_json(portraits, frames)
    else:
        print("Failed to fetch HTML. Exiting...")


if __name__ == "__main__":
    main()
