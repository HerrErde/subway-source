import sys
import json
import asyncio
import os
from playwright.async_api import async_playwright


async def extract_data(page, table_selector, json_file):
    print(f"Fetching data from URL: {page.url}")
    await page.wait_for_selector(table_selector)
    print("Table loaded!")

    data = []
    seen_names = set()

    tr_elements = await page.query_selector_all(f"{table_selector} tr")

    for tr_element in tr_elements:
        td_elements = await tr_element.query_selector_all("td")
        if len(td_elements) < 6:
            continue

        number = (await td_elements[0].text_content()).strip()
        name = (await td_elements[2].text_content()).strip()

        if name in seen_names:
            continue

        seen_names.add(name)

        status_text = (await td_elements[4].text_content()).strip()
        img_element = await td_elements[5].query_selector("img")

        available = status_text in ["Yes", "No"] and not img_element

        img_url = None
        link_element = await td_elements[1].query_selector("a")
        if link_element:
            link_class = await link_element.get_attribute("class")
            if "new" not in link_class:
                img_url = (await link_element.get_attribute("href")).strip()
                img_url = (
                    img_url.split(".png")[0] + ".png" if ".png" in img_url else img_url
                )

        board_data = {
            "number": int(number),
            "name": name,
            "available": available,
            "img_url": img_url,
        }

        data.append(board_data)
        print(f"Scraped: {name}")


async def fetch_data(url, table_selector, json_file):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-gpu",
                "--disable-software-rasterizer",
                "--disable-dev-shm-usage",
                "--user-agent=subway-source",
            ],
            channel="chromium",
        )
        context = await browser.new_context()

        try:
            page = await context.new_page()
            await page.goto(url, timeout=1200000)
            await extract_data(page, table_selector, json_file)
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            await context.close()
            await browser.close()

    with open(json_file, "w") as file:
        json.dump([], file, indent=2)


async def main():
    tasks = []


async def main():
    tasks = []

    if len(sys.argv) == 1 or sys.argv[1] in {"1", "2"}:
        tasks.append(
            fetch_data(
                "https://subwaysurf.fandom.com/wiki/Characters",
                "table.article-table",
                "upload/characters_links.json",
            )
        )
        tasks.append(
            fetch_data(
                "https://subwaysurf.fandom.com/wiki/Hoverboard",
                "table.article-table",
                "upload/boards_links.json",
            )
        )

    await asyncio.gather(*tasks)


asyncio.run(main())
