import os
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = os.getenv("API_PORT", "8000")
API_BASE = f"http://{API_HOST}:{API_PORT}"

st.set_page_config(page_title="Cover Builder", layout="wide")
st.title("Cover Builder")

# ---- Helpers ---------------------------------------------------------------

def api_get(path: str, *, timeout: int = 30):
    return requests.get(f"{API_BASE}{path}", timeout=timeout)

def api_post(path: str, payload: dict, *, timeout: int = 30):
    return requests.post(f"{API_BASE}{path}", json=payload, timeout=timeout)

@st.cache_data(ttl=5)
def fetch_projects():
    r = api_get("/projects")
    if r.status_code != 200:
        raise RuntimeError(f"GET /projects failed ({r.status_code}): {r.text}")
    return r.json()

def refresh_projects_cache():
    fetch_projects.clear()

def safe_ts(s: str | None) -> str:
    if not s:
        return ""
    return s.replace("T", " ").replace("Z", "")

# ---- Sidebar: API Status ---------------------------------------------------

with st.sidebar:
    st.subheader("API")
    try:
        r = api_get("/health", timeout=10)
        if r.status_code == 200:
            st.success(f"Connected: {API_BASE}")
        else:
            st.error(f"Health check failed ({r.status_code})")
    except Exception as e:
        st.error(f"Cannot reach API: {e}")

# ---- Main: Projects --------------------------------------------------------

st.header("Projects")

col_a, col_b = st.columns([1, 2], gap="large")

with col_a:
    st.subheader("Create a new project")

    with st.form("create_project_form", clear_on_submit=False):
        title = st.text_input("Book Title", placeholder="Diving Deep")
        author = st.text_input("Author", placeholder="Tani Hanes")
        genre = st.text_input("Genre", placeholder="Romance")
        subgenre = st.text_input("Subgenre (optional)", placeholder="Rock Star Romance")

        submitted = st.form_submit_button("Create Project")

    if submitted:
        if not title.strip() or not author.strip() or not genre.strip():
            st.error("Title, Author, and Genre are required.")
        else:
            payload = {
                "title": title.strip(),
                "author": author.strip(),
                "genre": genre.strip(),
                "subgenre": subgenre.strip() or None,
            }
            try:
                r = api_post("/projects", payload, timeout=30)
                if r.status_code != 200:
                    st.error(f"Create failed ({r.status_code}): {r.text}")
                else:
                    st.success("Project created.")
                    refresh_projects_cache()
                    st.rerun()
            except Exception as e:
                st.error(f"Create failed: {e}")

with col_b:
    st.subheader("Select a project")

    try:
        projects = fetch_projects()
    except Exception as e:
        st.error(str(e))
        projects = []

    if not projects:
        st.info("No projects yet. Create one on the left.")
        st.session_state.pop("project_id", None)
        st.session_state.pop("selected_project", None)
    else:
        labels = [f"{p['title']} — {p['author']} ({p['genre']})" for p in projects]

        if "project_id" not in st.session_state:
            st.session_state.project_id = projects[0]["id"]

        current_id = st.session_state.project_id
        try:
            current_idx = next(i for i, p in enumerate(projects) if p["id"] == current_id)
        except StopIteration:
            current_idx = 0
            st.session_state.project_id = projects[0]["id"]

        selected_idx = st.selectbox(
            "Projects",
            range(len(projects)),
            index=current_idx,
            format_func=lambda i: labels[i],
        )
        selected_project = projects[selected_idx]
        st.session_state.project_id = selected_project["id"]
        st.session_state.selected_project = selected_project

        st.markdown("### Selected Project")
        st.write(
            {
                "id": selected_project["id"],
                "title": selected_project["title"],
                "author": selected_project["author"],
                "genre": selected_project["genre"],
                "subgenre": selected_project.get("subgenre"),
                "created_at": selected_project.get("created_at"),
            }
        )

        if st.button("Refresh projects list"):
            refresh_projects_cache()
            st.rerun()

# ---- Generate Brief --------------------------------------------------------

st.header("Generate brief")

project_id = st.session_state.get("project_id")
proj = st.session_state.get("selected_project", {})

if not project_id:
    st.info("Create or select a project first.")
else:
    brief_title = st.text_input("Title (for this brief)", proj.get("title", ""))
    brief_author = st.text_input("Author (for this brief)", proj.get("author", ""))
    brief_genre = st.text_input("Genre (for this brief)", proj.get("genre", ""))
    brief_subgenre = st.text_input("Subgenre (optional)", proj.get("subgenre") or "")

    tone = st.text_input("Tone words (comma-separated)", "dark, moody, intimate")
    comps = st.text_input("Comparable titles (comma-separated)", "")
    constraints = st.text_input("Constraints (comma-separated)", "thumbnail readable, genre-appropriate")
    blurb = st.text_area("Blurb (optional)", "")

    if st.button("Generate cover directions"):
        payload = {
            "project_id": project_id,
            "title": brief_title.strip(),
            "author": brief_author.strip(),
            "genre": brief_genre.strip(),
            "subgenre": brief_subgenre.strip() or None,
            "blurb": blurb.strip() or None,
            "tone_words": [t.strip() for t in tone.split(",") if t.strip()],
            "comps": [c.strip() for c in comps.split(",") if c.strip()],
            "constraints": [c.strip() for c in constraints.split(",") if c.strip()],
        }

        missing = [k for k in ("title", "author", "genre") if not payload[k]]
        if missing:
            st.error(f"Missing required fields: {', '.join(missing)}")
        else:
            r = requests.post(f"{API_BASE}/cover/brief", json=payload, timeout=180)
            if r.status_code != 200:
                st.error(f"API error {r.status_code}: {r.text}")
            else:
                data = r.json()
                st.caption(f"Model: {data.get('model')}")
                st.success("Brief generated (and saved to history).")
                st.rerun()

# ---- Brief History + Generate Images --------------------------------------

st.header("Brief history")

project_id = st.session_state.get("project_id")

if not project_id:
    st.info("Select a project to view brief history.")
else:
    r = requests.get(f"{API_BASE}/projects/{project_id}/brief-runs", timeout=30)
    if r.status_code != 200:
        st.error(f"Failed to load brief runs ({r.status_code}): {r.text}")
    else:
        runs = r.json()
        if not runs:
            st.info("No brief runs yet. Generate a brief to start history.")
        else:
            st.caption(f"{len(runs)} run(s)")

            for run in runs:
                run_id = run["id"]
                created_at = safe_ts(run.get("created_at"))
                run_title = f"{created_at} — {run.get('status')} — {run.get('model')}"

                with st.expander(run_title, expanded=False):
                    if run.get("error_message"):
                        st.error(run["error_message"])

                    directions = run.get("response_json", {}).get("directions", [])
                    if not directions:
                        st.write("No directions stored in this run.")
                        continue

                    st.subheader("Directions")

                    # Per-run controls
                    top_cols = st.columns([1, 1, 2])
                    with top_cols[0]:
                        n_images = st.selectbox(
                            "Images per direction",
                            [1, 2, 3, 4],
                            index=1,
                            key=f"n_{run_id}",
                        )
                    with top_cols[1]:
                        size = st.selectbox(
                            "Size",
                            ["1024x1536", "1024x1024", "1536x1024"],
                            index=0,
                            key=f"size_{run_id}",
                        )
                    with top_cols[2]:
                        st.caption("Tip: 1024x1536 is a good portrait starting point for cover-ish backgrounds.")

                    for i, d in enumerate(directions):
                        st.markdown(f"### {i + 1}. {d.get('name','(untitled)')}")
                        st.write(d.get("one_liner", ""))

                        prompt = d.get("image_prompt", "").strip()
                        if prompt:
                            st.markdown("**Image prompt (background only)**")
                            st.code(prompt)

                        btn_cols = st.columns([1, 3])
                        with btn_cols[0]:
                            clicked = st.button(
                                "Generate images",
                                key=f"gen_{run_id}_{i}",
                                disabled=not bool(prompt),
                            )
                        with btn_cols[1]:
                            st.caption("Generates background art and saves it to this project.")

                        if clicked:
                            payload = {
                                "project_id": project_id,
                                "brief_run_id": run_id,
                                "direction_index": i,
                                "prompt": prompt,
                                "n": n_images,
                                "size": size,
                            }
                            resp = requests.post(f"{API_BASE}/cover/image", json=payload, timeout=300)
                            if resp.status_code != 200:
                                st.error(f"API error {resp.status_code}: {resp.text}")
                            else:
                                data = resp.json()
                                imgs = data.get("images", [])
                                if not imgs:
                                    st.warning("No images returned.")
                                else:
                                    urls = [f"{API_BASE}{img['image_url']}" for img in imgs]
                                    st.image(urls, width=220)
                                    st.success("Saved. (Images are now in Postgres + local storage.)")

                        st.divider()

# ---- Optional: simple gallery (shows files you just generated) -------------

st.header("Project image gallery (v1)")

project_id = st.session_state.get("project_id")
if not project_id:
    st.info("Select a project to see its images.")
else:
    st.caption("For v1, this section just tells you where the static images live. Next we’ll add a real gallery endpoint.")
    st.code(f"{API_BASE}/static/images/{project_id}/")
    st.write("Open that URL to browse the folder listing (if your server allows it) or click images from the history above.")
