import os
import requests
import streamlit as st
from dotenv import load_dotenv

# Load .env
load_dotenv()

API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = os.getenv("API_PORT", "8000")
API_BASE = f"http://{API_HOST}:{API_PORT}"

st.title("Cover Builder (v1)")

st.caption(f"Environment: {os.getenv('APP_ENV', 'unknown')}")

if st.button("Check API health"):
    r = requests.get(f"{API_BASE}/health", timeout=5)
    st.json(r.json())
