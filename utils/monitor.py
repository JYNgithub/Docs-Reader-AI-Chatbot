import chromadb
from itertools import zip_longest
import shutil
import sqlite3
import os

VECTOR_PATH = "./vectors"
CLIENT = chromadb.PersistentClient(path=VECTOR_PATH)

def show_collections():
    collections = CLIENT.list_collections()
    print(f"\nExpected number of collections: {len(collections)}")
    print("\nExpected collection names:")
    print("\n".join(sorted([c.name for c in collections])))

def compare_ids():
    def get_ids(path):
        database = sqlite3.connect(path)
        cursor = database.cursor()
        cursor.execute("SELECT id FROM segments WHERE scope = 'VECTOR'")
        ids = cursor.fetchall()
        return [id[0] for id in ids]

    ids = sorted(get_ids(os.path.join(VECTOR_PATH, "chroma.sqlite3")))
    files = sorted([f for f in os.listdir(VECTOR_PATH) if not f.endswith(".sqlite3")])
    print("\nExpected VS Actual collection names:")
    for expected, actual in zip_longest(ids, files, fillvalue="MISSING"):
        print(f"[{expected}, {actual}]")

def prune_unexisting():
    def delete_unexisting_files(path, ids):
        elements = os.listdir(path)
        for el in [".DS_Store", "chroma.sqlite3"]:
            if el in elements:
                elements.remove(el)
        for el in elements:
            full_path = os.path.join(path, el)
            if el not in ids and os.path.isdir(full_path):
                shutil.rmtree(full_path)

    def get_ids(path):
        database = sqlite3.connect(path)
        cursor = database.cursor()
        cursor.execute("SELECT id FROM segments WHERE scope = 'VECTOR'")
        ids = cursor.fetchall()
        return [id[0] for id in ids]

    ids = sorted(get_ids(os.path.join(VECTOR_PATH, "chroma.sqlite3")))
    confirm = input("Prune? (y/n): ")
    if confirm.lower() == "y":
        delete_unexisting_files(VECTOR_PATH, ids)
        print("Deletion completed.")
    else:
        print("Operation cancelled.")

def inspect_collection():
    name = input("Enter collection name: ")
    collection = CLIENT.get_collection(name=name)
    all_docs = collection.get()
    first_id = all_docs['ids'][0]
    results = collection.get(ids=[first_id])
    print(results['documents'][0])
    print(results['metadatas'][0])

def delete_collection():
    name = input("Enter collection name to delete: ")
    confirm = input(f"Are you sure you want to delete '{name}'? (y/n): ")
    if confirm.lower() == "y":
        CLIENT.delete_collection(name)
        print(f"Collection '{name}' deleted.")
    else:
        print("Operation cancelled.")

menu = """
Choose an option:
1. Show all collections
2. Compare expected vs actual collection IDs
3. Prune unexisting collections
4. Inspect a collection
5. Delete a collection

Enter choice: """

choice = input(menu)

if choice == "1":
    show_collections()
elif choice == "2":
    compare_ids()
elif choice == "3":
    prune_unexisting()
elif choice == "4":
    inspect_collection()
elif choice == "5":
    delete_collection()
else:
    print("Invalid choice.")
    
print(" ")
