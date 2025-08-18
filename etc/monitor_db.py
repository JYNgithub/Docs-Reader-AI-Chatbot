import chromadb

CLIENT = chromadb.PersistentClient(path="./vectors")

collections = CLIENT.list_collections()

print(collections[0].count())




