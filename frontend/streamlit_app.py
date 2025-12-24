import requests
import streamlit as st

st.title("Cover Builder (v1)")

api = st.text_input("API Base URL", "http://127.0.0.1:8000")

if st.button("Check API health"):
    r = requests.get(f"{api}/health", timeout=5)
    st.json(r.json())
