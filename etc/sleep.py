import time
import streamlit as st
import random

def sleepy():
    with st.expander("Show Text"):
        for _ in range(20):
            st.text(f"Random number: {random.randint(1, 100)}")
            time.sleep(1)

sleepy()