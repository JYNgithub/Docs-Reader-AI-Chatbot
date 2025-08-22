import yaml
import logging
import chromadb
import asyncio
from components import setup_collection, fetch_links, fetch_sitemap, scrape_page

########################################################
# Configuration
########################################################

# Configure library name
LIBRARY_NAME = "nicegui" 

# Configure basic information
with open("./utils/libraries.yaml") as f:
    data = yaml.safe_load(f)
library = data[LIBRARY_NAME]
ROOT_URL = library.get("root_url", [])
BASE_URL = library["base_url"]
EXCLUDE_URL = library.get("exclude_url", [])
TAG_TO_SCRAPE = library["tag_to_scrape"]

# Configure ChromaDB client
CLIENT = chromadb.PersistentClient(path="./vectors")

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

########################################################
# Main Execution
########################################################

async def main():
    setup_collection(
        CLIENT,
        LIBRARY_NAME
    )

    if not ROOT_URL:
        all_links = await fetch_links(
            BASE_URL,
            LIBRARY_NAME,
            EXCLUDE_URL,
            max_links=None,
            concurrency=5,
            sleep=1
        )
    else:
        all_links = fetch_sitemap(
            ROOT_URL,
            BASE_URL,
            LIBRARY_NAME,
            EXCLUDE_URL
        )
    await asyncio.sleep(10)
    await scrape_page(
        all_links,
        CLIENT,
        TAG_TO_SCRAPE,
        LIBRARY_NAME,
        timeout=20000,
        concurrency=3,
        sleep=3
    )

if __name__ == "__main__":
    asyncio.run(main())

