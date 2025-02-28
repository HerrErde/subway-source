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
    number = 1

    tr_elements = soup.select("table.article-table tr")

    for tr_element in tr_elements:
        td_elements = tr_element.select("td")
        if len(td_elements) < 6:
            continue

        link_element, name, img_tags = (
            td_elements[1].select_one("a"),
            td_elements[2],
            td_elements[3].select("img"),
        )

        name = (
            td_elements[2].select_one("a").text.strip()
            if td_elements[2].select_one("a")
            else (
                td_elements[2].select_one("b").text.strip()
                if td_elements[2].select_one("b")
                else (
                    re.search(r"\[+([^]]+)\]+", td_elements[2].text)
                    .group(1)
                    .strip()  # Broken wiki link [[Name]
                    if "[" in td_elements[2].text and "]" in td_elements[2].text
                    else None
                )
            )
        )

        removed = bool(td_elements[2].select_one("s"))

        img_url = (
            link_element.get("href", "").split(".png")[0] + ".png"
            if link_element and "new" not in link_element.get("class", [])
            else None
        )

        tba_pattern = re.compile(r"TbaName\w*", re.IGNORECASE)

        tba_in_img = any(tba_pattern.search(img.get("alt", "")) for img in img_tags)

        available = not tba_in_img and img_url is not None

        if removed:
            continue

        board_data = {
            "number": int(number),
            "name": name,
            "img_url": img_url,
            "available": available,
        }
        number += 1

        # if removed:
        #    board_data["removed"] = True

        data.append(board_data)
        print(f"Scraped: {name}")

    return data


async def fetch_data(session, url, json_file):
    try:
        async with session.get(url) as response:
            response.raise_for_status()
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
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
