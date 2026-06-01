import asyncio
import json
import re
import sys

import aiofiles
from bs4 import BeautifulSoup


def create_cf_session():
    from curl_cffi.requests import Session

    return Session(impersonate="chrome")


SESSION = create_cf_session()


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
        name = td_elements[name_col].get_text(strip=True)

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

    # Find the hoverboard-specific table by looking for specific headers
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

        # Name is in column 2 (index), Picture in column 1, Number in column 0
        name_col = 2
        name = td_elements[name_col].get_text(strip=True)

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


async def fetch_data(url, json_file, data_type):
    try:
        response = await asyncio.to_thread(SESSION.get, url, timeout=60)
        response.raise_for_status()
        html = response.text
        if data_type == 1:
            data = await extract_character_data(html)
        elif data_type == 2:
            data = await extract_board_data(html)
        else:
            data = []
    except Exception as e:
        print(f"An error occurred fetching data from {url}: {e}")
        data = []

    async with aiofiles.open(json_file, "w", encoding="utf-8") as file:
        await file.write(json.dumps(data, indent=2))


async def main():
    tasks = []

    tasks.append(
        fetch_data(
            "https://subwaysurf.fandom.com/wiki/Characters",
            "temp/upload/characters_links.json",
            1,
        )
    )
    tasks.append(
        fetch_data(
            "https://subwaysurf.fandom.com/wiki/Hoverboards",
            "temp/upload/boards_links.json",
            2,
        )
    )

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
