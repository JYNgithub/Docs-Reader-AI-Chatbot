import asyncio
import logging
import time
import pandas as pd
from urllib.parse import urldefrag
from playwright.async_api import async_playwright

########################################################
# Configuration
########################################################

# Configure links to scrape
BASE_URL = [
    "https://docs.trychroma.com/docs",
]

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

########################################################
# Utility Functions
########################################################

async def fetch_links(base_urls: list):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        all_links = set()

        for root_url in base_urls:
            await page.goto(root_url)
            links = await page.eval_on_selector_all('a', 'elements => elements.map(e => e.href)')
            child_links = [
                urldefrag(link).url
                for link in links
                if any(link.startswith(base) for base in base_urls)
            ]
            logging.info(f"Found {len(child_links)} links on {root_url}...")
            all_links.update(child_links)
            await asyncio.sleep(1)

        await browser.close()

        all_links = list(all_links)
        df = pd.DataFrame(all_links, columns=["Links"])
        df.drop_duplicates(inplace=True)
        df.to_csv("links.csv", index=False)


        logging.info(f"Total unique links saved: {len(all_links)}...")
        return all_links

        
def main():
    
    asyncio.run(fetch_links(BASE_URL))
    

if __name__ == '__main__':
    main()
