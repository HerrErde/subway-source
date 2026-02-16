import json
import aiohttp
import sys
import asyncio
from bs4 import BeautifulSoup

FLARESOLVERR_URL = "http://localhost:8191/v1"


async def fetch_page(url):
    payload = {"cmd": "request.get", "url": url, "maxTimeout": 60000}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                FLARESOLVERR_URL, json=payload, timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                response.raise_for_status()
                data = await response.json()
                return data.get("solution", {}).get("response", "")
    except Exception as e:
        print("Error fetching:", e)
        return None


async def extract_character_data(html):
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

        tba_in_img = any(
            "TbaName.png"
            in (
                img.get("src", "")
                + img.get("data-src", "")
                + img.get("data-image-name", "")
            )
            for img in img_tags
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
    print("Table loaded!")

    data = []
    number = 1

    tr_elements = soup.select("table.article-table tr")

    for tr_element in tr_elements:
        td_elements = tr_element.select("td")
        if len(td_elements) < 8:
            continue

        removed = bool(td_elements[3].select_one("s"))

        link_element, name, img_tags = (
            td_elements[3].select_one("a"),
            td_elements[3],
            td_elements[2].select("img"),
        )

        name = (
            td_elements[3].select_one("a").text.strip()
            if td_elements[3].select_one("a")
            else (
                td_elements[3].select_one("b").text.strip()
                if td_elements[3].select_one("b")
                else (
                    re.search(r"\[+([^]]+)\]+", td_elements[3].text).group(1).strip()
                    if "[" in td_elements[3].text and "]" in td_elements[3].text
                    else None
                )
            )
        )

        img_url = (
            (
                (img_tags[0].get("data-src") or img_tags[0].get("src")).split(".png")[0]
                + ".png"
            )
            if img_tags and (img_tags[0].get("data-src") or img_tags[0].get("src"))
            else None
        )

        all_imgs = tr_element.select("img")
        tba_in_img = any(
            "TbaName.png"
            in (
                img.get("src", "")
                + img.get("data-src", "")
                + img.get("data-image-name", "")
            )
            for img in all_imgs
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

        # if removed:
        #    board_data["removed"] = True

        data.append(item_data)
        print(f"Scraped: {name}")

    return data


async def fetch_data(url, json_file, type_):
    html = await fetch_page(url)
    if not html:
        print("Failed to fetch:", url)
        return

    if type_ == 1:
        data = await extract_character_data(html)
    else:
        data = await extract_board_data(html)

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


async def main():
    tasks = []

    async with aiohttp.ClientSession() as session:
        tasks.append(
            fetch_data(
                "https://subwaysurf.fandom.com/wiki/Characters",
                "temp/upload/characters_links.json",
                1,
            )
        )
        tasks.append(
            fetch_data(
                "https://subwaysurf.fandom.com/wiki/Hoverboard",
                "temp/upload/boards_links.json",
                2,
            )
        )

        await asyncio.gather(*tasks)


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
