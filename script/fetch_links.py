import asyncio
import json
import sys

import aiofiles
import httpx
from bs4 import BeautifulSoup

API_URL = "https://subwaysurf.fandom.com/api.php"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
}


async def fetch_page_html(client, page_title):
    params = {
        "action": "parse",
        "page": page_title,
        "format": "json",
        "prop": "text",
    }
    resp = await client.get(API_URL, params=params, headers=HEADERS, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    return data["parse"]["text"]["*"]


async def extract_character_data(html):
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


async def extract_board_data(html):
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


async def fetch_data(client, page_title, json_file, data_type):
    try:
        html = await fetch_page_html(client, page_title)
        if data_type == 1:
            data = await extract_character_data(html)
        elif data_type == 2:
            data = await extract_board_data(html)
        else:
            data = []
    except Exception as e:
        print(f"An error occurred fetching data from {page_title}: {e}")
        data = []

    async with aiofiles.open(json_file, "w", encoding="utf-8") as file:
        await file.write(json.dumps(data, indent=2))


async def main():
    async with httpx.AsyncClient() as client:
        tasks = [
            fetch_data(client, "Characters", "temp/upload/characters_links.json", 1),
            fetch_data(client, "Hoverboards", "temp/upload/boards_links.json", 2),
        ]
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
