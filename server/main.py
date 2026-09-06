"""暴发调查工作台 FastAPI 应用。前端（Vite dev）跨域调用本服务。"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import assistant, events, kb


def create_app() -> FastAPI:
    app = FastAPI(title="食源性疾病暴发调查工作台", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(events.router, prefix="/api/events", tags=["events"])
    app.include_router(kb.router, prefix="/api/kb", tags=["kb"])
    app.include_router(assistant.router, prefix="/api/assistant", tags=["assistant"])
    return app


app = create_app()
