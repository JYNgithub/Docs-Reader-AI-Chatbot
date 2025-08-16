import logging
import chromadb
from components import confirm_collection, fetch_links, scrape_page

########################################################
# Configuration
########################################################

# Configure links to scrape
BASE_URL = [
    "https://pillow.readthedocs.io/en/stable/installation",
]

# Configure basic information
LIBRARY_NAME = "pillow"
TAG_TO_SCRAPE = ".article-container"

# Configure ChromaDB client
CLIENT = chromadb.PersistentClient(path="./vectors")

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

########################################################
# Main Execution
########################################################

def main():
    
    confirm_collection(CLIENT, LIBRARY_NAME)
    
    all_links = fetch_links(BASE_URL, LIBRARY_NAME)
    
    scrape_page(all_links, CLIENT, TAG_TO_SCRAPE, LIBRARY_NAME)

if __name__ == '__main__':
    main()
