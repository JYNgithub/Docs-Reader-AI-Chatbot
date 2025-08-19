import yaml
import logging
import chromadb
import asyncio
from components import setup_collection, fetch_links, scrape_page

########################################################
# Configuration
########################################################

# Configure library name
LIBRARY_NAME = "chroma"

# Configure basic information
with open("./utils/libraries.yaml") as f:
    data = yaml.safe_load(f)
conf = data[LIBRARY_NAME]
BASE_URL = conf["base_url"]
EXCLUDE_URL = conf["exclude_url"]
TAG_TO_SCRAPE = conf["tag_to_scrape"]

# Configure ChromaDB client
CLIENT = chromadb.PersistentClient(path="./vectors")

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

########################################################
# Main Execution
########################################################

def main():
    
    setup_collection(CLIENT, LIBRARY_NAME)

    all_links = asyncio.run(fetch_links(BASE_URL, LIBRARY_NAME))

    asyncio.run(scrape_page(all_links, CLIENT, TAG_TO_SCRAPE, LIBRARY_NAME))

if __name__ == '__main__':
    main()

