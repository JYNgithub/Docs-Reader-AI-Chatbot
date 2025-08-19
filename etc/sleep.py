import time
import streamlit as st

def sleepy():
    for i in range(5):
        st.text("Hello world")
        time.sleep(1)
