import logging
import chromadb
from components import setup_collection, fetch_links, scrape_page

########################################################
# Configuration
########################################################

# Configure links to scrape
BASE_URL = [
    "https://docs.trychroma.com/integrations",
    "https://docs.trychroma.com/docs",
]

EXCLUDE_URL = [
    "https://docs.trychroma.com/docs/overview/contributing",
    "https://docs.trychroma.com/docs/overview/telemetry",
    "https://docs.trychroma.com/docs/cli/sample-apps"
]

# Configure basic information
LIBRARY_NAME = "chroma"
TAG_TO_SCRAPE = "article"

# Configure ChromaDB client
CLIENT = chromadb.PersistentClient(path="./vectors")

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

########################################################
# Main Execution
########################################################

def main():
    
    setup_collection(CLIENT, LIBRARY_NAME)
    
    all_links = fetch_links(BASE_URL, LIBRARY_NAME)
    
    scrape_page(all_links, CLIENT, TAG_TO_SCRAPE, LIBRARY_NAME)

if __name__ == '__main__':
    main()
