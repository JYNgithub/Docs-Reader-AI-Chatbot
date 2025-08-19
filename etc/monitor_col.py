import chromadb

CLIENT = chromadb.PersistentClient(path="./vectors")

collection = CLIENT.get_collection(
    name = "langgraph_docs"
)

# Get IDs
all_docs = collection.get()
print(all_docs['ids'][:5])

# Check content
results = collection.get(ids=["7925a51e-691a-4f4d-9d0b-33fa46fa0ebe"])
print(results['documents'])
print(results['metadatas'])


