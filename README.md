```markdown
# Cover Builder

An AI-driven book cover generator for self-published authors.

Cover Builder is designed to help authors create professional, market-appropriate book covers without the cost of a full-time cover designer. The project is being built first as a personal author tool, with a clear path toward a self-service SaaS product.

---

## Tech Stack

- **Backend:** FastAPI (Python)
- **Frontend:** Streamlit
- **AI Platform:** OpenAI API
- **Dependency Management:** uv
- **Environment Management:** Python virtual environments + `.env`
- **OS:** macOS (development)

Docker support will be added later for production deployment.

---

## Repository Structure

```text
cover-builder/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI application entrypoint
│   │   └── settings.py      # Centralized configuration & secrets
│   ├── tests/
│   ├── pyproject.toml
│   └── uv.lock
├── frontend/
│   └── streamlit_app.py     # Streamlit UI
├── .env.example             # Example environment variables
├── .gitignore
└── README.md
```

---

## Requirements

- macOS
- Python **3.11+**
- Git
- VS Code (recommended)
- Homebrew (recommended)

---

## Local Development Setup

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/cover-builder.git
cd cover-builder
```

---

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

Confirm activation:

```bash
which python
```

You should see `.venv` in the path.

---

### 3. Install uv (dependency manager)

If not already installed:

```bash
brew install uv
```

---

### 4. Install backend dependencies

```bash
cd backend
uv sync --active
cd ..
```

This installs all dependencies into the active virtual environment.

---

### 5. Create environment variables

Copy the example file:

```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:

```env
APP_ENV=development
OPENAI_API_KEY=sk-your-key-here
API_HOST=127.0.0.1
API_PORT=8000
```

> **Important:**  
> `.env` is ignored by Git and should never be committed.

---

## Running the Application Locally

### 1. Start the FastAPI backend

From the repository root:

```bash
source .venv/bin/activate
cd backend
uv run uvicorn app.main:app --reload --port 8000
```

The API will be available at:
- http://127.0.0.1:8000
- Swagger UI: http://127.0.0.1:8000/docs

---

### 2. Start the Streamlit UI (new terminal)

Open a **second terminal**, then:

```bash
source .venv/bin/activate
python -m streamlit run frontend/streamlit_app.py
```

The UI will open automatically in your browser.

---

## Environment Configuration

All configuration is centralized and typed using **Pydantic Settings**.

- Local development uses `.env`
- Production will use real environment variables
- Secrets are never hardcoded

The configuration object is shared across FastAPI and Streamlit to avoid duplication.

---

## Development Notes

- Core business logic lives in the backend API
- Streamlit acts as a client UI, not a logic container
- The project is intentionally structured to support:
  - background workers
  - Docker deployment
  - multi-tenant SaaS features later

---

## Roadmap (High-Level)

- OpenAI client service with cost tracking
- Cover brief generation from book metadata
- Image generation and iteration pipeline
- Typography and layout system
- Series consistency tools
- Export to KDP-ready formats
- Docker + production deployment
- Authentication and billing (SaaS)

---

## License

TBD
```
