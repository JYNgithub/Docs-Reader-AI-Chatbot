import os
import chromadb
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

st.title("DocsReader")

######################################################
# Initialization
######################################################

OPENAI_KEY = os.getenv("OPENAI_KEY")
client = OpenAI(api_key=OPENAI_KEY)

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-5-nano"
if "history" not in st.session_state:
    st.session_state.history = []
for message in st.session_state.history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
######################################################
# Utility Functions
######################################################      

def _get_collection():
    
    client = chromadb.PersistentClient(path="./vectors")

    collection = client.get_collection(name="chroma_docs")
    
    return collection

def chat_with_rag(user_query):
    
    collection = _get_collection()
    
    result = collection.query(
        query_texts=[user_query],
        include=["documents","metadatas"],
        n_results = 2
    )
    
    docs = result.get("documents", [])
    if docs:
        docs = docs[0]
    context = "\n\n".join(docs) if docs else ""
    
    metas = result.get("metadatas", [])
    metadata_list = metas[0] if metas else []
    if metadata_list:
        links = [m["url"] for m in metadata_list if "url" in m]
        st.markdown("**Sources:**\n" + "\n".join(f"- {link}" for link in links))

    prompt = (
        f"Be as concise as possible.\n"
        f"Use the following context to answer the question, if relevant.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {user_query}\nAnswer:"
    )
    
    print("---------------------------------------------------------")
    print(prompt)
    return prompt    
        
######################################################
# App Layout
######################################################   

if prompt := st.chat_input("What is up?"):
    
    rag_prompt = chat_with_rag(prompt)

    st.session_state.history.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        convo_for_model = st.session_state.history.copy()
        convo_for_model[-1] = {"role": "user", "content": rag_prompt}

        stream = client.chat.completions.create(
            model=st.session_state["openai_model"],
            messages=convo_for_model,
            stream=True,
        )
        response = st.write_stream(
            part.choices[0].delta.content or ""
            for part in stream
            if part.choices[0].delta.content is not None
        )

    st.session_state.history.append({"role": "assistant", "content": response})
