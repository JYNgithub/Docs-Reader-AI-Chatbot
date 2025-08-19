import re
import sys
import time
import uuid
import logging
import pandas as pd
from datetime import datetime
from urllib.parse import urldefrag
from playwright.sync_api import sync_playwright

########################################################
# Utility Functions
########################################################

def setup_collection(CLIENT, LIBRARY_NAME):

    collections = CLIENT.list_collections()

    if any(c.name == f"{LIBRARY_NAME}_docs" for c in collections):
        # Note: deleting before creating is risky behaviour, fix later
        logging.info(f"Replacing existing '{LIBRARY_NAME}_docs' collection...")
        CLIENT.delete_collection(name=f"{LIBRARY_NAME}_docs")
        time.sleep(3)
        CLIENT.create_collection(
            name=f"{LIBRARY_NAME}_docs",
            metadata={
                "description": f"Documentation for {LIBRARY_NAME}",
                "created": str(datetime.now())
            }  
        )
    else:
        logging.info(f"A new collection will be created...")
        CLIENT.create_collection(
            name=f"{LIBRARY_NAME}_docs",
            metadata={
                "description": f"Documentation for {LIBRARY_NAME}",
                "created": str(datetime.now())
            }  
        )

def fetch_links(BASE_URL, LIBRARY_NAME, EXCLUDE_URL = None, max_links=None):
    
    if EXCLUDE_URL is None:
        EXCLUDE_URL = []
        
    all_links = set(BASE_URL)
    to_crawl = list(BASE_URL)

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
                if any(link.startswith(base) for base in BASE_URL)
            ]

            new_links = [link for link in child_links if link not in all_links]
            all_links.update(new_links)
            to_crawl.extend(new_links)
        
            if max_links is not None and len(all_links) >= max_links:
                logging.info(f"Reached max_links={max_links}, stopping crawl.")
                break

        browser.close()

    filtered_links = [link for link in all_links if link not in EXCLUDE_URL]
    df = pd.DataFrame(filtered_links, columns=["Links"])
    df["Scraped"] = False
    df.to_csv(f"./logging/{LIBRARY_NAME}_links.csv", index=False)
    logging.info(f"Total unique links saved: {len(filtered_links)}")
    
    return filtered_links

def scrape_page(urls, CLIENT, TAG_TO_SCRAPE, LIBRARY_NAME):
    
    collection = CLIENT.get_collection(name=f"{LIBRARY_NAME}_docs")
    total_count = len(urls)
    scraped_count = 0
    
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for url in urls:
            page = browser.new_page()
            
            try:
                logging.info("Loading into page...")
                page.goto(url, wait_until="domcontentloaded")
                
                logging.info("Scraping data...")
                content = page.inner_text(TAG_TO_SCRAPE)
                
                if not page.query_selector(TAG_TO_SCRAPE):
                    raise ValueError
                if not content.strip():  
                    raise ValueError
                
                logging.info("Processing data...")
                content = _data_preprocessing(content)
                
                logging.info("Adding data...")
                uid = str(uuid.uuid4())
                collection.add(
                    ids=[uid],
                    documents=[content],
                    metadatas=[{"url": url}]
                )
                logging.info(f"Added page content from {url}")
                time.sleep(1)
                
                df = pd.read_csv(f"./logging/{LIBRARY_NAME}_links.csv")
                if url in df['Links'].values:
                    df.loc[df['Links'] == url, 'Scraped'] = True
                    df.to_csv(f"./logging/{LIBRARY_NAME}_links.csv", index=False)
                
            except:
                logging.warning(f"Failed to add content from {url}")

            finally:
                page.close()
                scraped_count += 1
                logging.info(f"Done with {scraped_count}/{total_count} links...")
        
        browser.close()

def _data_preprocessing(content):
    
    # Remove excessive whiteline but preserve code formatting
    content = re.sub(r'\n{2,}', '\n', content)
    
    return content