import chromadb

CLIENT = chromadb.PersistentClient(path="./vectors")

name = input("Enter collection name: ")
collection = CLIENT.get_collection(name=name)

# Get IDs
all_docs = collection.get()
first_id = all_docs['ids'][0]

# Print first document and metadata
results = collection.get(ids=[first_id])
print(results['documents'][0])
print(results['metadatas'][0])
