import logging
import time
import uuid
from urllib.parse import urldefrag
from playwright.sync_api import sync_playwright
import chromadb

########################################################
# Configuration
########################################################

# Configure links to scrape
BASE_URL = [
    # "https://docs.trychroma.com/docs/overview/getting-started",
    # "https://docs.trychroma.com/docs/run-chroma/persistent-client",
    "https://docs.trychroma.com/integrations/embedding-models/openai",
    
]

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

########################################################
# Utility Functions
########################################################

def scrape_page(urls):
    
    client = chromadb.PersistentClient(path="./vectors")
    
    collection = client.get_collection(name="chroma_docs")
    
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for url in urls:
            page = browser.new_page()
            page.goto(url, wait_until="networkidle")
            content = page.inner_text("article")
            page.close()
            
            uid = str(uuid.uuid4())
            collection.add(
                ids=[uid],
                documents=[content],
                metadatas=[{"url": url}]
            )
            logging.info(f"Added page content from {url} with ID {uid}")
        browser.close()

def main():
    scrape_page(BASE_URL)

if __name__ == '__main__':
    main()

