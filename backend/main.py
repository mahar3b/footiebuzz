from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.routes import router

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"


def create_app() -> FastAPI:
    app = FastAPI(
        title="FootieBuzz",
        description="Real-time match sentiment from live tweets",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)

    if FRONTEND.exists():
        app.mount("/static", StaticFiles(directory=FRONTEND), name="static")

        @app.get("/")
        def serve_index():
            return FileResponse(FRONTEND / "index.html")

    return app
