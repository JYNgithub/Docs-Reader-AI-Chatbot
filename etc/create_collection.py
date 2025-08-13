import chromadb
from datetime import datetime

client = chromadb.PersistentClient(path="./vectors")

collection = client.create_collection(
    name="chroma_docs",
    # embedding_function=
    metadata={
        "description": "Documentation for chroma",
        "created": str(datetime.now())
    }
)

collection = client.get_collection(name="chroma_docs")

full_list = client.list_collections()
print("Available collections:")
for i, col in enumerate(full_list, start=1):
    print(f"{i}. {col.name}")



