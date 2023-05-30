import json
from playwright.sync_api import sync_playwright


def extract_data(page, table_selector, json_file):
    # Wait for the table to load
    page.wait_for_selector(table_selector)

    # Extract the "td" elements from each "tr" element
    tr_elements = page.query_selector_all(f"{table_selector} tr")

    data = []

    # Extract data from each "tr" element
    for tr_element in tr_elements:
        td_elements = tr_element.query_selector_all("td")
        if len(td_elements) >= 3:
            number = td_elements[0].text_content().strip()

            name = td_elements[2].text_content().strip()

            link_element = td_elements[1].query_selector("a")
            img_url = link_element.get_attribute("href") if link_element else ""

            # Remove everything after the .png extension in the image URL
            img_url = (
                img_url.split(".png")[0] + ".png" if ".png" in img_url else img_url
            )

            board_data = {"number": number, "name": name, "img_url": img_url}

            data.append(board_data)

    # Write the data to a JSON file
    with open(json_file, "w") as file:
        json.dump(data, file, indent=2)


# Create a Playwright instance
with sync_playwright() as playwright:
    # Launch a new browser instance
    browser = playwright.chromium.launch()

    # Create a new browser context
    context = browser.new_context()

    # Create a new page
    page = context.new_page()

    # Extract data from the Characters page
    page.goto("https://subwaysurf.fandom.com/wiki/Characters", timeout=1200000)
    extract_data(page, "table.article-table", "characters_links.json")

    # Extract data from the Hoverboard page
    page.goto("https://subwaysurf.fandom.com/wiki/Hoverboard", timeout=1200000)
    extract_data(page, "table.article-table", "boards_links.json")

    # Close the browser context
    context.close()
