import json
import os
import sys

import httpx
from bs4 import BeautifulSoup

API_URL = "https://subwaysurf.fandom.com/api.php"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
}


def fetch_page_html(page_title):
    params = {
        "action": "parse",
        "page": page_title,
        "format": "json",
        "prop": "text",
    }
    resp = httpx.get(API_URL, params=params, headers=HEADERS, timeout=60)
    resp.raise_for_status()
    return resp.json()["parse"]["text"]["*"]


def save_json(data, file_path):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def extract_character_data(html):
    soup = BeautifulSoup(html, "html.parser")

    data = []
    number = 1

    tables = soup.select("table.article-table")
    char_table = None

    for table in tables:
        header_row = table.select("tr th, tr td:first-child")
        headers = [h.get_text(strip=True).lower() for h in header_row[:5]]
        if any(h in headers for h in ["character", "name", "image", "color"]):
            char_table = table
            break

    if not char_table:
        char_table = tables[0] if tables else None

    tr_elements = char_table.select("tr") if char_table else []

    for tr_element in tr_elements:
        td_elements = tr_element.select("td")
        if len(td_elements) < 6:
            continue

        name_col = 2
        name_cell = td_elements[name_col]

        a_tag = name_cell.find("a")
        if a_tag and a_tag.has_attr("title"):
            name = a_tag["title"]
        else:
            name = name_cell.get_text(strip=True)

        if not name:
            continue

        removed = bool(td_elements[name_col].select_one("s"))

        img_tags = td_elements[1].select("img") if len(td_elements) > 1 else []
        img_url = None
        if img_tags:
            img_elem = img_tags[0]
            img_url = img_elem.get("data-src") or img_elem.get("src") or ""
            if img_url:
                img_url = img_url.split(".png")[0] + ".png"

        tba_in_img = any(
            "TbaName.png" in (img.get("src", "") + img.get("data-src", ""))
            for img in tr_element.select("img")
        )

        available = not tba_in_img and img_url is not None

        if removed:
            continue

        item_data = {
            "number": int(number),
            "name": name,
            "img_url": img_url,
            "available": available,
        }
        number += 1

        data.append(item_data)
        print(f"Scraped: {name}")

    return data


def extract_board_data(html):
    soup = BeautifulSoup(html, "html.parser")

    data = []
    number = 1

    tables = soup.select("table.article-table")
    board_table = None

    for table in tables:
        header_row = table.select("tr th, tr td:first-child")
        headers = [h.get_text(strip=True).lower() for h in header_row[:5]]
        if any(h in headers for h in ["hoverboard", "board", "name", "image"]):
            board_table = table
            break

    if not board_table:
        board_table = tables[0] if tables else None

    tr_elements = board_table.select("tr") if board_table else []

    for tr_element in tr_elements:
        td_elements = tr_element.select("td")
        if len(td_elements) < 6:
            continue

        name_col = 2
        name_cell = td_elements[name_col]

        a_tag = name_cell.find("a")
        if a_tag and a_tag.has_attr("title"):
            name = a_tag["title"]
        else:
            name = name_cell.get_text(strip=True)

        if not name:
            continue

        removed = bool(td_elements[name_col].select_one("s"))

        img_tags = td_elements[1].select("img") if len(td_elements) > 1 else []
        img_url = None
        if img_tags:
            img_elem = img_tags[0]
            img_url = img_elem.get("data-src") or img_elem.get("src") or ""
            if img_url:
                img_url = img_url.split(".png")[0] + ".png"

        tba_in_img = any(
            "TbaName.png" in (img.get("src", "") + img.get("data-src", ""))
            for img in tr_element.select("img")
        )

        available = not tba_in_img and img_url is not None

        if removed:
            continue

        item_data = {
            "number": int(number),
            "name": name,
            "img_url": img_url,
            "available": available,
        }
        number += 1

        data.append(item_data)
        print(f"Scraped: {name}")

    return data


def main():
    try:
        characters_html = fetch_page_html("Characters")
        characters = extract_character_data(characters_html)
        save_json(characters, "temp/upload/characters_links.json")

        boards_html = fetch_page_html("Hoverboards")
        boards = extract_board_data(boards_html)
        save_json(boards, "temp/upload/boards_links.json")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
