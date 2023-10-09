import sys
import json
import asyncio
from playwright.async_api import async_playwright


async def extract_data(page, table_selector, json_file):
    # Wait for the table to load
    await page.wait_for_selector(table_selector)

    # Extract the "td" elements from each "tr" element
    tr_elements = await page.query_selector_all(f"{table_selector} tr")

    data = []

    # Extract data from each "tr" element
    for tr_element in tr_elements:
        td_elements = await tr_element.query_selector_all("td")
        if len(td_elements) >= 4:
            available_element = td_elements[4]
            status_text = (await available_element.text_content()).strip()

            img_element = await td_elements[5].query_selector("img")

            available = True

            if status_text in ["Yes", "No"]:
                available = True
            elif status_text == "Unavailable":
                available = False
            else:
                continue

            if img_element:
                alt_text = await img_element.get_attribute("alt")
                if alt_text == "TbaName":
                    available = False

            number = (await td_elements[0].text_content()).strip()
            name = (await td_elements[2].text_content()).strip()

            link_element = await td_elements[1].query_selector("a")
            img_url = ""

            # Check if the link_element exists
            if link_element:
                # Check if the class of the link_element is "new"
                link_class = await link_element.get_attribute("class")
                if "new" not in link_class:
                    img_url = (await link_element.get_attribute("href")).strip()

            # Check if img_url is empty, and set img_url to None
            if not img_url:
                available = False
                img_url = None
            else:
                # Remove everything after the .png extension in the image URL
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

    # Write the data to a JSON file
    with open(json_file, "w") as file:
        json.dump(data, file, indent=2)


async def fetch_data(url, table_selector, json_file):
    async with async_playwright() as playwright:
        # Launch a new browser instance
        browser = await playwright.chromium.launch()

        # Create a new browser context
        context = await browser.new_context()

        # Create a new page
        page = await context.new_page()

        # Fetch data
        await page.goto(url, timeout=1200000)
        await extract_data(page, table_selector, json_file)

        # Close the browser context
        await context.close()


async def main():
    tasks = []

    # Fetch characters data
    if len(sys.argv) == 1 or sys.argv[1] == "1":
        tasks.append(
            fetch_data(
                "https://subwaysurf.fandom.com/wiki/Characters",
                "table.article-table",
                "upload/characters_links.json",
            )
        )

    # Fetch boards data
    if len(sys.argv) == 1 or sys.argv[1] == "2":
        tasks.append(
            fetch_data(
                "https://subwaysurf.fandom.com/wiki/Hoverboard",
                "table.article-table",
                "upload/boards_links.json",
            )
        )

    await asyncio.gather(*tasks)


# Run the main function
asyncio.run(main())
