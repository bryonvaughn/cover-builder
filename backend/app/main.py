from fastapi import FastAPI

from app.settings import get_settings
from app.routes.cover import router as cover_router
from app.routes.projects import router as projects_router

from pathlib import Path
from fastapi.staticfiles import StaticFiles

def create_app() -> FastAPI:
    settings = get_settings()

    storage_root = Path(settings.storage_dir)
    storage_root.mkdir(parents=True, exist_ok=True)

    app.mount("/static", StaticFiles(directory=str(storage_root)), name="static")

    app = FastAPI(title="Cover Builder API")

    # Routers
    app.include_router(cover_router)
    app.include_router(projects_router)

    # Health
    @app.get("/health")
    def health():
        return {"status": "ok", "environment": settings.app_env}

    return app


app = create_app()
