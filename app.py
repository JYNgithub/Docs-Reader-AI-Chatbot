import os
import chromadb
import streamlit as st
import yaml
from openai import OpenAI
from dotenv import load_dotenv
    
######################################################
# Configuration
######################################################

# Configure list of libraries
with open("./utils/libraries.yaml", "r") as f:
    data = yaml.safe_load(f)
LIBRARY_LIST = sorted(list(data.keys()))

# Configure ChromaDB client
if "client" not in st.session_state:
    st.session_state.client = chromadb.PersistentClient(path="./vectors")

# Initialize session state variables
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4o-mini"
if "history" not in st.session_state:
    st.session_state.history = []
if "library_name" not in st.session_state:
    st.session_state.library_name = LIBRARY_LIST[0]  # Default to first option

# Load environment variables (if any)
load_dotenv()
    
######################################################
# Utility Functions
###################################################### 

def prompt_expansion(query, library_name):
    
    response = OPENAI_CLIENT.chat.completions.create(
        model=st.session_state["openai_model"],
        messages=[
            {"role": "system", "content": f"You are a knowledgeable developer in a Python library/tool called {library_name}. First, paraphrase the user query twice, then followed by answering in 2 short and concise sentences without any code."},
            {"role": "user", "content": query}
        ],
    )
    
    ai_response = response.choices[0].message.content.strip()

    expanded_prompt = f"{query} {ai_response}"
    
    return expanded_prompt
         
def prompt_with_rag(query, library_name):
    
    try:
        collection = st.session_state.client.get_collection(name=f"{library_name}_docs")
    except Exception:
        st.error(f"No data on {library_name}.")
        st.stop()
    
    result = collection.query(
        query_texts=[query],
        include=["documents","metadatas"],
        n_results = 4
    )
    
    docs = result.get("documents", [])
    if docs:
        docs = docs[0]
    context = "\n\n".join(docs) if docs else ""
    
    metas = result.get("metadatas", [])
    metadata_list = metas[0] if metas else []

    prompt = (
        f"As a beginner-friendly coding assistant, use the following context to answer the question concisely and shortly. Provide short, simple and easy to understand Python code. Prevent using custom functions. "
        f"For any code chunk, wrap it in triple backticks and specify the language after the opening backticks. For plain text, the triple backticks are not needed. \n\n"
        f"Context:\n{context}\n\n"
        f"Question: {query}\nAnswer:"
    )
    
    print("---------------------------------------------------------")
    # print(prompt)
    return prompt, metadata_list    

def prompt_without_rag(query):
    
    prompt = (
        f"As a beginner-friendly coding assistant, answer the question concisely and shortly. Provide short, simple and easy to understand Python code. Prevent using custom functions. " 
        f"For any code chunk, wrap it in triple backticks and specify the language after the opening backticks. For plain text, the triple backticks are not needed. \n\n"
        f"Question: {query}\nAnswer:"
    )
    
    print("---------------------------------------------------------")
    # print(prompt)
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
    
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    
    st.markdown('<h1 style="font-size:38px; margin-bottom:0;">DocsReader</h1>', unsafe_allow_html=True) 
    st.markdown(
        '<p style="font-size:16px; color:#A9A9A9;">Your learning partner for <br>Python libraries.</p>',
        unsafe_allow_html=True
    )
    
    st.markdown('<div style="height: calc(100vh - 595px);"></div>', unsafe_allow_html=True)
    
    placeholder = "Configured" if os.getenv("OPENAI_KEY") else " "
    user_openai_key = st.text_input(
        "Enter OpenAI API Key", 
        type="password", 
        key="user_openai_key",
        placeholder=placeholder
    )
    
    library_name = st.selectbox(
        "Select a library",
        options=LIBRARY_LIST,
        index=LIBRARY_LIST.index(st.session_state.library_name),
        key="library_selector"
    )
    if library_name != st.session_state.library_name:
        st.session_state.library_name = library_name
        st.session_state.history = []  # Clear chat history when library changes
        st.rerun()  # Refresh

    st.markdown('<div style="height: 15px;"></div>', unsafe_allow_html=True)
    
    st.session_state.use_rag = st.toggle("Toggle RAG", value=True, key="rag_toggle")
    
    st.markdown(
        '<p style="font-size:14px; color:#A9A9A9;">Enable to query new information.<br>Disable to proceed with conversation.</p>',
        unsafe_allow_html=True
    )

# Landing page 
with st.container():
    OPENAI_KEY = os.getenv("OPENAI_KEY")
    if not OPENAI_KEY and "user_openai_key" in st.session_state:
        OPENAI_KEY = st.session_state["user_openai_key"]
    if not OPENAI_KEY:
        st.title("👋 Welcome to DocsReader")
        st.markdown("<div style='height:80px'></div>", unsafe_allow_html=True)
        st.markdown(
            """
            <p style='font-size:18px'>
                To get started, please enter your <b>OpenAI API key</b> in the sidebar.
            </p>
            <p style='font-size:18px'>
                If you don’t have one yet, you can create it by logging into the
                <a href='https://openai.com/api/' target='_blank'>OpenAI API Platform</a>
            </p>
            <p style='font-size:18px'>
                Open-source code at
                <a href='https://github.com/JYNgithub/Docs-Reader-AI-Chatbot' target='_blank'>GitHub</a>
            </p>
            """,
            unsafe_allow_html=True
        )
        st.stop()
    OPENAI_CLIENT = OpenAI(api_key=OPENAI_KEY)
    
# Chat messages
for message in st.session_state.history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
# print(st.session_state.history)

# Chat input
if prompt := st.chat_input(placeholder=f"Ask about {st.session_state.library_name.capitalize()}...", accept_file=False):
    
    with st.chat_message("user"):
        st.text(prompt)
        
    # Deliver prompt based on RAG toggle
    if st.session_state.use_rag:
        # Expand prompt for improved RAG
        expanded_prompt = prompt_expansion(prompt, st.session_state.library_name)
        print(expanded_prompt)
        model_prompt, metadata_list = prompt_with_rag(expanded_prompt, st.session_state.library_name)
    else:
        model_prompt = prompt_without_rag(prompt)
        metadata_list = []
    
    st.session_state.history.append({"role": "user", "content": prompt})
        
    with st.chat_message("assistant"):
        
        final_prompt = st.session_state.history.copy()
        final_prompt[-1] = {"role": "user", "content": model_prompt}
        
        # The final prompt sent should contain
        # 1. chat history without context and expansion
        # 2. instructions + overall directions
        # 3. user prompt (currently the expanded version, may change later, depends)
        # print(final_prompt)
        # print(st.session_state.history)

        stream = OPENAI_CLIENT.chat.completions.create(
            model=st.session_state["openai_model"],
            messages=final_prompt,
            stream=True,
        )
        response = st.write_stream(
            part.choices[0].delta.content or ""
            for part in stream
            if part.choices[0].delta.content is not None
        )
        
        if metadata_list:
            with st.expander("Sources"):
                links = [m["url"] for m in metadata_list if "url" in m]
                st.markdown("\n".join(f"- {link}" for link in links))
            
    # print(response)
    
    st.session_state.history.append({"role": "assistant", "content": response})
    
    # Limit chat history memory to only 15 dialogues 
    # Since chose to not also add after appending "user", 
    # it might reach 16 dialogues temporarily, with the last message being from "user" before it gets filtered here.
    st.session_state.history = st.session_state.history[-15:]
