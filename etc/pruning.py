import shutil
import sqlite3
import os

def get_ids(path):
    database = sqlite3.connect(path)
    cursor = database.cursor()
    cursor.execute("SELECT id FROM segments WHERE scope = 'VECTOR'")
    ids = cursor.fetchall()
    return [id[0] for id in ids]


def delete_unexisting_files(path, ids):
    elements = os.listdir(path)
    for el in [".DS_Store", "chroma.sqlite3"]:
        if el in elements:
            elements.remove(el)
    for el in elements:
        full_path = os.path.join(path, el)
        if el not in ids and os.path.isdir(full_path):
            shutil.rmtree(full_path)

ids = get_ids(os.path.join("./vectors", "chroma.sqlite3"))
for id in ids:
    print(id)

confirm = input(f"Prune? (y/n): ")
if confirm.lower() == "y":
    delete_unexisting_files("./vectors", ids)
    print("Deletion completed.")
else:
    print("Operation cancelled.")