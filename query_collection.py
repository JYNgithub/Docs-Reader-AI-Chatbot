import chromadb

client = chromadb.PersistentClient(path="./vectors")

collection = client.get_collection(name="chroma_docs")

results = collection.query(
    query_texts=["what is chroma db"],
    n_results=2
)
print(f"Number of existing data: {len(collection.get()['ids'])}\n")

for i, doc_list in enumerate(results['documents'], 1):
    for doc in doc_list:
        print(f"Document{i}: {doc}")


