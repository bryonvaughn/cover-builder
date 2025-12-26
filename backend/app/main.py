from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.settings import get_settings
from app.routes.cover import router as cover_router
from app.routes.projects import router as projects_router


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(title="Cover Builder API")

    # --- storage + static files ---
    storage_root = Path(settings.storage_dir)
    storage_root.mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=str(storage_root)), name="static")

    # --- routers ---
    app.include_router(projects_router)
    app.include_router(cover_router)

    @app.get("/health")
    def health():
        return {"status": "ok", "environment": settings.app_env}

    return app


app = create_app()
