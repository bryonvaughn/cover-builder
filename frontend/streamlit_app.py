import os
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = os.getenv("API_PORT", "8000")
API_BASE = f"http://{API_HOST}:{API_PORT}"

st.title("Cover Builder (v1)")

st.subheader("Generate cover brief")

title = st.text_input("Title", "Diving Deep")
subtitle = st.text_input("Subtitle (optional)", "")
author = st.text_input("Author", "Tani Hanes")
genre = st.text_input("Genre", "Romance")
subgenre = st.text_input("Subgenre (optional)", "Rock Star Romance")
tone = st.text_input("Tone words (comma-separated)", "dark, moody, intimate, London nights")
blurb = st.text_area("Blurb (optional)", "")

if st.button("Generate cover directions"):
    payload = {
        "title": title,
        "subtitle": subtitle or None,
        "author": author,
        "genre": genre,
        "subgenre": subgenre or None,
        "blurb": blurb or None,
        "tone_words": [t.strip() for t in tone.split(",") if t.strip()],
        "comps": [],
        "constraints": [],
    }

    r = requests.post(f"{API_BASE}/cover/brief", json=payload, timeout=60)
    if r.status_code != 200:
        st.error(f"API error {r.status_code}: {r.text}")
    else:
        data = r.json()
        st.caption(f"Model: {data['model']}")
        for i, d in enumerate(data["directions"], start=1):
            st.markdown(f"### {i}. {d['name']}")
            st.write(d["one_liner"])
            st.markdown("**Imagery**")
            st.write(d["imagery"])
            st.markdown("**Typography**")
            st.write(d["typography"])
            st.markdown("**Palette**")
            st.write(d["color_palette"])
            st.markdown("**Layout notes**")
            st.write(d["layout_notes"])
            st.markdown("**Avoid**")
            st.write(d["avoid"])
            st.markdown("**Image prompt (background only)**")
            st.code(d["image_prompt"])
