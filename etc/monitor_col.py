import chromadb

CLIENT = chromadb.PersistentClient(path="./vectors")

collection = CLIENT.get_collection(
    name = "nicegui_docs"
)

# Get IDs
all_docs = collection.get()
print(all_docs['ids'][:5])

# Check content
results = collection.get(ids=["23d2dc99-0858-43a9-9520-40426a858c21"])
print(results['documents'])
print(results['metadatas'])


