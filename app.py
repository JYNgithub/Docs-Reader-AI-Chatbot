import os
import chromadb
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

######################################################
# Configuration
######################################################

# Load keys (local)
load_dotenv()

# Configure OpenAI client
OPENAI_KEY = os.getenv("OPENAI_KEY")
OPENAI_CLIENT = OpenAI(api_key=OPENAI_KEY)

# Configure basic information
LIBRARY_LIST = ["chroma", "pyspark", "pillow"]

# Configure ChromaDB client
if "client" not in st.session_state:
    st.session_state.client = chromadb.PersistentClient(path="./vectors")

# Initialize session state variables
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-5-nano"
if "history" not in st.session_state:
    st.session_state.history = []
if "selected_library" not in st.session_state:
    st.session_state.selected_library = LIBRARY_LIST[0]  # Default to first option

######################################################
# Utility Functions
######################################################      

def prompt_with_rag(user_query, library_name):
    
    collection = st.session_state.client.get_collection(name=f"{library_name}_docs")
    
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
        f"For every code chunk, wrap it in triple backticks and specify the language after the opening backticks.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {user_query}\nAnswer:"
    )
    
    print("---------------------------------------------------------")
    print(prompt)
    return prompt    

def prompt_without_rag(user_query):
    
    prompt = (
        f"As a coding assistant, answer the question in a concise, simple and straightforward manner. " 
        f"For every code chunk, wrap it in triple backticks and specify the language after the opening backticks.\n\n"
        f"Question: {user_query}\nAnswer:"
    )
    
    print("---------------------------------------------------------")
    print(prompt)
    return prompt 
        
######################################################
# App Layout
###################################################### 

# Page setup
st.set_page_config(
    page_title="DocsReader",
    layout="wide"
)

# Sidebar
with st.sidebar:
    st.title("DocsReader")  

    st.markdown('<div style="height: calc(100vh - 385px);"></div>', unsafe_allow_html=True)

    st.markdown('---')
    
    selected_library = st.selectbox(
        "Search for library:",
        options=LIBRARY_LIST,
        index=LIBRARY_LIST.index(st.session_state.selected_library),
        key="library_selector"
    )
    if selected_library != st.session_state.selected_library:
        st.session_state.selected_library = selected_library
        st.session_state.history = []  # Clear chat history when library changes
        st.rerun()  # Refresh

    st.markdown('<div style="height: 15px;"></div>', unsafe_allow_html=True)
    
    use_rag = st.toggle("Use RAG", value=True, key="rag_toggle")

# Chat messages
for message in st.session_state.history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input(
    placeholder=f"Ask about {st.session_state.selected_library.capitalize()}...",
    accept_file=False
    ):
    
    # Deliver prompt based on RAG toggle
    if use_rag:
        model_prompt = prompt_with_rag(prompt, st.session_state.selected_library)
    else:
        model_prompt = prompt_without_rag(prompt)

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
