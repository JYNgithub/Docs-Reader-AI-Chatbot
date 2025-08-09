import asyncio
from playwright.async_api import async_playwright

async def scrape_links():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://nicegui.io/documentation")
        await page.wait_for_timeout(5000)  # wait 5 seconds

        anchors = await page.query_selector_all("a[href]")
        links = set()
        for a in anchors:
            href = await a.get_attribute("href")
            if href and href.startswith("https://nicegui.io/documentation"):
                links.add(href)

        await browser.close()

        with open("nicegui_links_playwright.txt", "w") as f:
            for link in sorted(links):
                f.write(link + "\n")
        print("Links saved to nicegui_links_playwright.txt")

asyncio.run(scrape_links())
