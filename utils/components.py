import re
import time
import uuid
import logging
import asyncio
import requests
import pandas as pd
from datetime import datetime
from urllib.parse import urldefrag, urlparse, parse_qs
import xml.etree.ElementTree as ET
from playwright.async_api import async_playwright

########################################################
# Utility Functions
########################################################

def setup_collection(CLIENT, LIBRARY_NAME):

    collections = CLIENT.list_collections()

    if any(c.name == f"{LIBRARY_NAME}_docs" for c in collections):
        # Note: deleting before creating is risky behaviour, fix later
        logging.info(f"Replacing existing '{LIBRARY_NAME}_docs' collection...")
        CLIENT.delete_collection(name=f"{LIBRARY_NAME}_docs")
        time.sleep(5)
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

async def fetch_links(BASE_URL, LIBRARY_NAME, EXCLUDE_URL=None, max_links=None):
    
    if EXCLUDE_URL is None:
        EXCLUDE_URL = []

    all_links = set()
    to_crawl = []

    # Initialize with defragmented + no query BASE_URL
    for url in BASE_URL:
        url_no_frag = urldefrag(url).url
        if urlparse(url_no_frag).query: 
            continue
        all_links.add(url_no_frag)
        to_crawl.append(url_no_frag)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()

        concurrency = 5
        semaphore = asyncio.Semaphore(concurrency)

        async def crawl(url):
            async with semaphore:
                page = await context.new_page()
                try:
                    logging.info(f"Crawling: {url}")
                    await page.goto(url)
                    links = await page.eval_on_selector_all('a', 'els => els.map(e => e.href)')

                    # Ensure defragmented + no query links only
                    for link in links:
                        if any(link.startswith(base) for base in BASE_URL) and link not in EXCLUDE_URL:
                            url_no_frag = urldefrag(link).url
                            if urlparse(url_no_frag).query:  # skip query links
                                continue
                            if url_no_frag not in all_links:
                                all_links.add(url_no_frag)
                                to_crawl.append(url_no_frag)   # only defragmented URL added

                except Exception as e:
                    logging.warning(f"Failed to load {url}: {e}")
                finally:
                    await page.close()

        while to_crawl:
            tasks = [crawl(to_crawl.pop()) for _ in range(min(concurrency, len(to_crawl)))]
            await asyncio.gather(*tasks)

            if max_links is not None and len(all_links) >= max_links:
                logging.info(f"Reached max_links={max_links}, stopping crawl.")
                break

        await browser.close()

    filtered_links = [
        link for link in all_links 
        if not any(link.startswith(prefix) for prefix in EXCLUDE_URL)
    ]
    df = pd.DataFrame(filtered_links, columns=["Links"])
    df["Scraped"] = False
    df.to_csv(f"./logging/{LIBRARY_NAME}_links.csv", index=False)
    logging.info(f"Total unique links saved: {len(filtered_links)}")
    
    return list(filtered_links)

def fetch_sitemap(ROOT_URL, BASE_URL, LIBRARY_NAME,  EXCLUDE_URL=None):
    def _parse_sitemap(url):
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        # Collect URLs
        urls = [loc.text for loc in root.findall(".//sm:loc", namespace)]
        return urls

    # Start with the root sitemap
    sitemap_url = ROOT_URL.rstrip("/") + "/sitemap.xml"
    urls = _parse_sitemap(sitemap_url)
    all_links = []

    # If it's a sitemap index → fetch each sub-sitemap
    if all(u.endswith(".xml") for u in urls):
        for sm in urls:
            all_links.extend(_parse_sitemap(sm))
    else:
        all_links.extend(urls)

    # Filter by BASE_URL
    filtered = [u for u in all_links if any(u.startswith(base) for base in BASE_URL)]
    # Exclude by EXCLUDE_URL
    if EXCLUDE_URL is None:
        EXCLUDE_URL = []
    filtered_links = [u for u in filtered if not any(u.startswith(prefix) for prefix in EXCLUDE_URL)]

    df = pd.DataFrame(filtered_links, columns=["Links"])
    df["Scraped"] = False
    df.to_csv(f"./logging/{LIBRARY_NAME}_links.csv", index=False)
    logging.info(f"Total unique links saved: {len(filtered_links)}")

    return sorted(set(filtered_links))

async def scrape_page(urls, CLIENT, TAG_TO_SCRAPE, LIBRARY_NAME, timeout = 20000):
    collection = CLIENT.get_collection(name=f"{LIBRARY_NAME}_docs")
    total_count = len(urls)
    scraped_count = 0

    df = pd.read_csv(f"./logging/{LIBRARY_NAME}_links.csv")
    
    # Limit number of concurrent pages
    concurrency = 5
    semaphore = asyncio.Semaphore(concurrency)

    async with async_playwright() as p:
        browser = await p.chromium.launch()

        async def scrape(url):
            nonlocal scraped_count
            async with semaphore:
                page = await browser.new_page()
                try:
                    logging.info(f"Loading page: {url}")
                    await page.goto(url, wait_until="domcontentloaded")
                    
                    logging.info("Scraping data...")
                    await page.wait_for_selector(TAG_TO_SCRAPE, timeout=timeout)
                    element = await page.query_selector(TAG_TO_SCRAPE)
                    if not element:
                        raise ValueError(f"No element found for selector: {TAG_TO_SCRAPE}")

                    content = await element.inner_text()
                    if not content.strip():
                        raise ValueError(f"Element found for selector {TAG_TO_SCRAPE} is empty")
                    
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

                    if url in df['Links'].values:
                        df.loc[df['Links'] == url, 'Scraped'] = True
                        
                except Exception as e:
                    logging.warning(f"Failed to add content from {url}: {e}")
                    
                finally:
                    await page.close()
                    scraped_count += 1
                    logging.info(f"Done with {scraped_count}/{total_count} links...")

        tasks = [scrape(url) for url in urls]
        await asyncio.gather(*tasks)

        await browser.close()
        
    df.to_csv(f"./logging/{LIBRARY_NAME}_links.csv", index=False)

def _data_preprocessing(content):
    
    # Remove excessive whiteline but preserve code formatting
    content = re.sub(r'\n{2,}', '\n', content)
    
    return content