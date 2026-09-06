from fastapi import FastAPI, Form, Request
from fastapi.responses import PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app.config import Config
from core.store import Store

HERE = Path(__file__).resolve().parent


def create_app(db_path=None, vector_db_path=None, xls_path=None):
    cfg = Config()
    if db_path:
        cfg.db_path = db_path
    if vector_db_path:
        cfg.vector_db_path = vector_db_path
    if xls_path:
        cfg.xls_path = xls_path
    app = FastAPI(title="食源性疾病暴发调查助手")
    app.mount("/static", StaticFiles(directory=str(HERE / "static")), name="static")
    templates = Jinja2Templates(directory=str(HERE / "templates"))
    app.state.cfg = cfg
    app.state.store = Store(cfg.db_path)

    @app.get("/")
    def root():
        return RedirectResponse("/investigations")

    @app.get("/investigations")
    def investigations(request: Request):
        return templates.TemplateResponse(request, "investigations.html",
                                          {"events": app.state.store.list_events()})

    @app.get("/investigations/new")
    def new_form(request: Request):
        return templates.TemplateResponse(request, "new.html", {})

    @app.post("/investigations/new")
    def create(request: Request, id: str = Form(...), title: str = Form(...),
               scenario: str = Form(...), lead: str = Form("")):
        try:
            app.state.store.create_event(id, title, scenario, lead, "调查员")
        except ValueError as e:
            return templates.TemplateResponse(request, "new.html", {"error": str(e)}, status_code=400)
        return RedirectResponse("/investigations", status_code=303)

    @app.get("/investigations/{event_id}")
    def detail(request: Request, event_id: str):
        try:
            state = app.state.store.load(event_id)
        except ValueError as e:
            return PlainTextResponse(str(e), status_code=404)
        timeline = app.state.store.timeline(event_id)
        return templates.TemplateResponse(request, "investigation.html",
                                          {"state": state, "timeline": timeline})

    return app


app = create_app()
