from fastapi import FastAPI, Form, Request
from fastapi.responses import PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app.config import Config
from core.store import Store
from core.analyze import analyze
from assistant.orchestrator import render_gaps, Orchestrator
from assistant.client import ChatClient
from kb.embed import Embedder
from kb.retriever import Retriever
from kb.corpus import load_pathogen_ref, load_texts
from kb.ingest_xls import load_xls_events, event_to_text

HERE = Path(__file__).resolve().parent


def build_retriever(cfg, vector_db_path):
    embedder = Embedder(mode=cfg.embedding_mode, base_url=cfg.embedding_base_url,
                        api_key=cfg.embedding_api_key, model=cfg.embedding_model,
                        local_model=cfg.embedding_local_model)
    retriever = Retriever(vector_db_path, embedder)
    docs = []
    for p in load_pathogen_ref():
        docs.append({"id": "pathogen:" + p["name"], "source": "pathogen_ref",
                     "text": p["name"] + " " + " ".join(p["symptoms"]) + " " + " ".join(p["foods"]),
                     "locator": "致病因子参考：" + p["name"]})
    for e in load_xls_events(cfg.xls_path):
        if e.get("card"):
            docs.append({"id": "event:" + e["card"], "source": "monitoring_xls",
                         "text": event_to_text(e), "locator": "监测卡号：" + e["card"]})
    for t in load_texts("standards") + load_texts("reports"):
        docs.append({"id": "report:" + t["id"], "source": "report", "text": t["text"], "locator": t["id"]})
    retriever.index(docs)
    return retriever


def render_analysis(stats):
    c = stats["counts"]
    lines = [f"当前登记 {sum(c.values())} 人，符合病例定义 {c.get('case', 0)} 人，"
             f"明确未发病 {c.get('noncase', 0)} 人，待核实 {c.get('pending', 0)} 人，"
             f"定义范围外/不符合 {c.get('excluded', 0)} 人。"]
    for w in stats.get("warnings", []):
        lines.append(f"注意：{w}")
    return "\n".join(lines)


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
    retriever = build_retriever(cfg, getattr(cfg, "vector_db_path", None) or str(Path(cfg.db_path).with_name("vectors.db")))
    orchestrator = Orchestrator(ChatClient(cfg.model_base_url, cfg.model_api_key,
                                           cfg.model_name, enabled=cfg.allow_external_llm))

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

    @app.get("/investigations/{event_id}/analyze")
    def analyze_route(request: Request, event_id: str):
        state = app.state.store.load(event_id)
        stats = analyze(state)
        return templates.TemplateResponse(request, "analyze.html",
                                          {"event": state["event"], "stats": stats, "text": render_analysis(stats)})

    @app.get("/references")
    def references(request: Request):
        return templates.TemplateResponse(request, "references.html", {})

    @app.post("/references/search")
    def ref_search(request: Request, q: str = Form("")):
        hits = retriever.search(q)[:5]
        summary = orchestrator.similar(q, hits)
        return templates.TemplateResponse(request, "references.html",
                                          {"query": q, "hits": hits, "summary": summary})

    @app.get("/investigations/{event_id}/similar")
    def similar(request: Request, event_id: str):
        state = app.state.store.load(event_id)
        q = state["event"].get("title", "")
        hits = retriever.search(q)[:5]
        return templates.TemplateResponse(request, "similar.html",
                                          {"event": state["event"], "hits": hits,
                                           "summary": orchestrator.similar(q, hits)})

    return app


app = create_app()
