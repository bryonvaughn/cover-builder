from fastapi import FastAPI
from app.routes.cover import router as cover_router

app = FastAPI(title="Cover Builder API")
app.include_router(cover_router)
