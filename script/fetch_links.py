import asyncio
import json
import re
import sys

import aiofiles
import aiohttp
from bs4 import BeautifulSoup


async def extract_data(html):
    soup = BeautifulSoup(html, "html.parser")
    print("Table loaded!")

    data = []
    seen_names = set()

    tr_elements = soup.select("table.article-table tr")

    for tr_element in tr_elements:
        td_elements = tr_element.select("td")
        if len(td_elements) < 6:
            continue

        number, link_element, name, status_text, img_element = (
            td_elements[0].text.strip(),
            td_elements[1].select_one("a"),
            td_elements[2].text.strip(),
            td_elements[4].text.strip(),
            td_elements[5].select_one("img"),
        )

        if name in seen_names:
            continue

        seen_names.add(name)

        removed = bool(td_elements[2].select_one("s"))

        img_url = None
        if link_element:
            link_class = link_element.get("class", [])
            if "new" not in link_class:
                img_url = link_element.get("href", "").strip()
                img_url = img_url.split(".png")[0] + ".png"

        # Use regex to check for "Tba"
        tba_pattern = re.compile(r"TbaName\w*", re.IGNORECASE)
        if tba_pattern.search(status_text) or tba_pattern.search(str(td_elements[3])):
            available = False
        else:
            # Set availability to True if the first 4 letters of status_text are "Yes" or "No"
            available = (
                status_text[:3].lower() in ["yes", "no"]
                and not img_element
                and img_url is not None
            )

        board_data = {
            "number": int(number),
            "name": name,
            "available": available,
            "img_url": img_url,
        }

        if removed:
            board_data["removed"] = True

        data.append(board_data)
        print(f"Scraped: {name}")

    return data


async def fetch_data(session, url, json_file):
    try:
        async with session.get(url) as response:
            response.raise_for_status()
            # Ensure correct encoding
            html = await response.text(encoding="utf-8")
            data = await extract_data(html)
    except aiohttp.ClientError as e:
        print(f"An error occurred fetching data from {url}: {e}")
        data = []

    async with aiofiles.open(json_file, "w", encoding="utf-8") as file:
        await file.write(json.dumps(data, indent=2, ensure_ascii=False))


async def main():
    tasks = []

    async with aiohttp.ClientSession() as session:
        if len(sys.argv) == 1 or sys.argv[1] == "1":
            tasks.append(
                fetch_data(
                    session,
                    "https://subwaysurf.fandom.com/wiki/Characters",
                    "temp/upload/characters_links.json",
                )
            )
            tasks.append(
                fetch_data(
                    session,
                    "https://subwaysurf.fandom.com/wiki/Hoverboard",
                    "temp/upload/boards_links.json",
                )
            )

        await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
