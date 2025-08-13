import re
import time
import uuid
import asyncio
import logging
import chromadb
import pandas as pd
from datetime import datetime
from urllib.parse import urldefrag
from playwright.sync_api import sync_playwright

########################################################
# Configuration
########################################################

# Configure links to scrape
BASE_URL = [
    "https://docs.trychroma.com/integrations",
    "https://docs.trychroma.com/docs",
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
    df["Scraped"] = True
    df.to_csv("./scrapers/chroma_links.csv", index=False)
    logging.info(f"Total unique links saved: {len(all_links)}")
    
    return list(all_links)

def scrape_page(urls):
    
    collection = _get_collection()
    
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for url in urls:
            page = browser.new_page()
            
            try:
                page.goto(url, wait_until="domcontentloaded")
                content = page.inner_text("article")
                
                if not page.query_selector("article"):
                    raise ValueError
                if not content.strip():  
                    raise ValueError
                    
                content = _data_preprocessing(content)
                
                uid = str(uuid.uuid4())
                collection.add(
                    ids=[uid],
                    documents=[content],
                    metadatas=[{"url": url}]
                )
                logging.info(f"Added page content from {url} with ID {uid}")
                time.sleep(1)
                
            except:
                logging.warning(f"Scraping failed for {url}")
                df = pd.read_csv("./scrapers/chroma_links.csv")
                if url in df['Links'].values:
                    df.loc[df['Links'] == url, 'Scraped'] = False
                    df.to_csv("./scrapers/chroma_links.csv", index=False)
                    
            finally:
                page.close()
        
        browser.close()

def _data_preprocessing(content):
    
    # Remove excessive whiteline but preserve code formatting
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    return content

def _get_collection():
    
    client = chromadb.PersistentClient(path="./vectors")

    collection = client.get_or_create_collection(
        name="chroma_docs",
        # embedding_function=
        metadata={
            "description": "Documentation for chroma",
            "created": str(datetime.now())
        }   
    )
    
    return collection

def main():
    
    all_links = fetch_links(BASE_URL)
    
    scrape_page(all_links)

if __name__ == '__main__':
    main()
