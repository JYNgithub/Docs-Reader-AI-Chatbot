import asyncio
import logging
import time
import pandas as pd
from urllib.parse import urldefrag
from playwright.async_api import async_playwright
from langchain_community.document_loaders import WebBaseLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

########################################################
# Configuration
########################################################

# Configure links to scrape
BASE_URL = [
    "https://python.langchain.com/docs/tutorials/",
    "https://python.langchain.com/docs/how_to/",
    "https://python.langchain.com/docs/concepts/",
    # "https://python.langchain.com/docs/integrations/providers/",
    "https://python.langchain.com/docs/integrations/chat/",
    # "https://python.langchain.com/docs/integrations/retrievers/",
    # "https://python.langchain.com/docs/integrations/tools/",
    "https://python.langchain.com/docs/integrations/document_loaders/",
    "https://python.langchain.com/docs/integrations/vectorstores/",
    "https://python.langchain.com/docs/integrations/text_embedding/",
    "https://python.langchain.com/docs/integrations/llms/",
    # "https://python.langchain.com/docs/integrations/stores/",
    # "https://python.langchain.com/docs/integrations/document_transformers/",
    # "https://python.langchain.com/docs/integrations/llm_caching/",
    # "https://python.langchain.com/docs/integrations/graphs/",
    # "https://python.langchain.com/docs/integrations/memory/",
    # "https://python.langchain.com/docs/integrations/callbacks/",
    # "https://python.langchain.com/docs/integrations/chat_loaders/",
    # "https://python.langchain.com/docs/integrations/adapters/",
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
    
def build_vector_db_from_links(csv_path: str, max_links=None):

    df = pd.read_csv(csv_path)
    links = df['Links'].drop_duplicates()
    if max_links is not None:
        links = links.head(max_links)
    links = links.tolist()
    logging.info(f"Loaded {len(links)} unique links...")

    all_docs = []
    for i, link in enumerate(links, 1):
        logging.info(f"Loading documents from ({i}/{len(links)})...")
        loader = WebBaseLoader(link)
        docs = loader.load()
        logging.info(f"Loaded {len(docs)} documents...")
        all_docs.extend(docs)
        time.sleep(1)
        
    logging.info("Initializing embeddings and vector store...")
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
    vector_store = Chroma(
        collection_name="langchain_collection",
        embedding_function=embeddings,
        persist_directory="./chroma_langchain_db",
    )

    logging.info(f"Adding {len(all_docs)} documents to vector store...")
    vector_store.add_documents(all_docs)
    logging.info("Vector store persisted successfully")
    
def similarity_search(prompt: str, k=3):
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
    vector_store = Chroma(
        collection_name="langchain_collection",
        embedding_function=embeddings,
        persist_directory="./chroma_langchain_db",
    )
    retriever = vector_store.as_retriever(search_type="mmr", search_kwargs={"k": 3, "fetch_k": 10})
    docs = retriever.invoke(prompt)
    for i, doc in enumerate(docs, 1):
        print(f"Document {i} URL: {doc.metadata.get('source')}")
        # print(f"Content:\n{doc.page_content}\n")

        
def main():
    
    # asyncio.run(fetch_links(BASE_URL))
    
    # build_vector_db_from_links("links.csv")
    
    query = "RecursiveURLLoader"
    similarity_search(query)

if __name__ == '__main__':
    main()
