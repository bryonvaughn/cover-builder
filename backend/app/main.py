from fastapi import FastAPI

app = FastAPI(title="Cover Builder API")

@app.get("/health")
def health():
    return {"status": "ok"}
