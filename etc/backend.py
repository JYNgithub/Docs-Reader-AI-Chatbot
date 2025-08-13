import chromadb
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

def chat_with_rag(user_query):
    
    collection = _get_collection()
    
    result = collection.query(
        query_texts=[user_query],
        include=["documents","metadatas"],
        n_results = 3
    )
    
    docs = result.get("documents", [])
    if docs:
        docs = docs[0]
    context = "\n\n".join(docs) if docs else ""
    
    metas = result.get("metadatas", [])
    metadata_list = metas[0] if metas else []  
    for m in metadata_list:
        print(m)  

    prompt = (
        f"Use the following context to answer the question.\n\n"
        f"Be concise. Only provide answers relevant to the question."
        f"Context:\n{context}\n\n"
        f"Question: {user_query}\nAnswer:"
    )
    
    client = OpenAI(api_key=os.getenv("OPENAI_KEY"))
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=512
    )
    return response.choices[0].message.content
    
def _get_collection():
    
    client = chromadb.PersistentClient(path="./vectors")

    collection = client.get_collection(name="chroma_docs")
    
    return collection

print(chat_with_rag("How to even initiate a vector db?"))