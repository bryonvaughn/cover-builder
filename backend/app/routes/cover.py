from fastapi import FastAPI
from app.settings import get_settings
from app.routes.cover import router as cover_router

settings = get_settings()

app = FastAPI(title="Cover Builder API")

app.include_router(cover_router)


@app.get("/health")
def health():
    return {"status": "ok", "environment": settings.app_env}
