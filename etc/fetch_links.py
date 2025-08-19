import asyncio
import logging
import time
import pandas as pd
from urllib.parse import urldefrag
from playwright.sync_api import sync_playwright

########################################################
# Configuration
########################################################

# Configure links to scrape
BASE_URL = [
    "https://langchain-ai.github.io/langgraph/",
]

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

########################################################
# Utility Functions
########################################################

def fetch_links(base_urls):
    all_links = set(base_urls)
    to_crawl = list(base_urls)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        while to_crawl:
            url = to_crawl.pop()
            logging.info(f"Crawling: {url}")
            try:
                page.goto(url)
            except Exception as e:
                logging.warning(f"Failed to load {url}: {e}")
                continue

            links = page.eval_on_selector_all('a', 'elements => elements.map(e => e.href)')
            child_links = [
                urldefrag(link).url
                for link in links
                if any(link.startswith(base) for base in base_urls)
            ]

            new_links = [link for link in child_links if link not in all_links]
            all_links.update(new_links)
            to_crawl.extend(new_links)

        browser.close()

    df = pd.DataFrame(list(all_links), columns=["Links"])
    df.to_csv("./etc/links.csv", index=False)
    logging.info(f"Total unique links saved: {len(all_links)}")
    
    return list(all_links)


def main():
    fetch_links(BASE_URL)

if __name__ == '__main__':
    main()
