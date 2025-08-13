from openai import OpenAI
import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()  # load .env variables

st.title("DocsReader")

OPENAI_KEY = os.getenv("OPENAI_KEY")
client = OpenAI(api_key=OPENAI_KEY)

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-5-nano"
if "messages" not in st.session_state:
    st.session_state.messages = []
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model=st.session_state["openai_model"],
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
            stream=True,
        )
        response = st.write_stream(
            part.choices[0].delta.content or ""
            for part in stream
            if part.choices[0].delta.content is not None
        )

    st.session_state.messages.append({"role": "assistant", "content": response})
