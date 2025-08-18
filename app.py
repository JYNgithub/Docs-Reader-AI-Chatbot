import os
import chromadb
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
from utils.components import _get_collection

######################################################
# Configuration
######################################################

# Load keys (local)
load_dotenv()

# Configure OpenAI client
OPENAI_KEY = os.getenv("OPENAI_KEY")
OPENAI_CLIENT = OpenAI(api_key=OPENAI_KEY)

# Configure basic information
LIBRARY_LIST = ["pyspark", "pillow", "chroma"]

# Configure ChromaDB client
if "CLIENT" not in st.session_state:
    st.session_state.CLIENT = chromadb.PersistentClient(path="./vectors")

# Initialize session state variables
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-5-nano"
if "history" not in st.session_state:
    st.session_state.history = []
if "selected_library" not in st.session_state:
    st.session_state.selected_library = LIBRARY_LIST[0]  # Default to first option
for message in st.session_state.history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

######################################################
# Utility Functions
######################################################      

def chat_with_rag(user_query, library_name):
    
    collection = _get_collection(st.session_state.CLIENT, library_name)
    
    result = collection.query(
        query_texts=[user_query],
        include=["documents","metadatas"],
        n_results = 5
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
        f"As a coding assistant, use the following context to answer the question in a concise, simple and straightforward manner. "
        f"For every code chunk, you must wrap them in code blocks using triple backticks.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {user_query}\nAnswer:"
    )
    
    print("---------------------------------------------------------")
    print(prompt)
    return prompt    

def chat_without_rag(user_query):
    
    prompt = (
        f"As a coding assistant, answer the question in a concise, simple and straightforward manner. " 
        f"For every code chunk, you must wrap them in code blocks using triple backticks.\n\n"
        f"Question: {user_query}\nAnswer:"
    )
    
    print("---------------------------------------------------------")
    print(prompt)
    return prompt 
        
######################################################
# App Layout
###################################################### 

st.title("DocsReader")  

selected_library = st.selectbox(
    "Search for library:",
    options=LIBRARY_LIST,
    index=LIBRARY_LIST.index(st.session_state.selected_library),
    key="library_selector"
)

# Toggle for RAG
use_rag = st.toggle("Use RAG", value=True, key="rag_toggle")

# ADDED: Handle library change and reset chat history
if selected_library != st.session_state.selected_library:
    st.session_state.selected_library = selected_library
    st.session_state.history = []  # Clear chat history when library changes
    st.rerun()  # Refresh the app to clear displayed messages

if prompt := st.chat_input(f"Ask about {st.session_state.selected_library.capitalize()}..."):
    
    # Choose function based on toggle
    if use_rag:
        model_prompt = chat_with_rag(prompt, st.session_state.selected_library)
    else:
        model_prompt = chat_without_rag(prompt)

    st.session_state.history.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        convo_for_model = st.session_state.history.copy()
        convo_for_model[-1] = {"role": "user", "content": model_prompt}

        stream = OPENAI_CLIENT.chat.completions.create(
            model=st.session_state["openai_model"],
            messages=convo_for_model,
            stream=True,
        )
        response = st.write_stream(
            part.choices[0].delta.content or ""
            for part in stream
            if part.choices[0].delta.content is not None
        )
    
    print(response)

    st.session_state.history.append({"role": "assistant", "content": response})
