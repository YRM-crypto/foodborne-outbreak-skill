from fastapi import FastAPI, Form, Request
from fastapi.responses import PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app.config import Config
from core.store import Store
from assistant.orchestrator import render_gaps

HERE = Path(__file__).resolve().parent


def compute_gaps(state):
    event = state["event"]
    gaps = []
    if not event.get("received_at"):
        gaps.append({"id": "intake", "stage": "接报与核实", "title": "补充接报时间",
                     "why": "建立时间基线", "table": "接报记录", "basis": "S2012 §3.1"})
    if not state["definition"]:
        gaps.append({"id": "case_def", "stage": "病例定义", "title": "尚无病例定义",
                     "why": "无法统一病例纳入标准", "table": "病例定义记录", "basis": "S2012 §4.2"})
    if not state["people"]:
        gaps.append({"id": "individual", "stage": "个案调查", "title": "尚无人员/病例资料",
                     "why": "无法开展描述性与分析性分析", "table": "附表3-2", "basis": "S2012 §4.3–4.4"})
    if not state["evidence"]:
        gaps.append({"id": "evidence", "stage": "证据整理", "title": "尚未录入任何材料",
                     "why": "结论需有材料依据", "table": "附表3-7", "basis": "S2012 §6"})
    return gaps


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

    @app.get("/investigations/{event_id}/check")
    def check(request: Request, event_id: str):
        state = app.state.store.load(event_id)
        gaps = compute_gaps(state)
        return templates.TemplateResponse(request, "check.html",
                                          {"event": state["event"], "gaps": gaps, "text": render_gaps(gaps)})

    return app


app = create_app()
