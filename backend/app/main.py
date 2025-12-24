from fastapi import FastAPI
from app.settings import get_settings

settings = get_settings()

app = FastAPI(
    title="Cover Builder API",
    environment=settings.app_env,
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "environment": settings.app_env,
    }
