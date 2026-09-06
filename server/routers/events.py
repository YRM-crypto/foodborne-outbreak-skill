"""案例 CRUD + 分析 + 报告 + 时间线。复用 core/store.py、core/analyze.py、core/report.py。"""
from fastapi import APIRouter, Depends, HTTPException, Query

from core.analyze import analyze
from core.classify import classify
from core.report import render_markdown
from core.store import Store

from ..deps import get_store
from ..schemas import (
    ConfirmIn,
    ConclusionIn,
    CreateEvent,
    DefinitionIn,
    EventUpdate,
    EvidenceIn,
    ExposureIn,
    PersonIn,
    SampleIn,
)

router = APIRouter()


def _http(e: ValueError) -> HTTPException:
    return HTTPException(404 if "事件不存在" in str(e) else 400, str(e))


@router.post("", status_code=201)
def create_event(body: CreateEvent, store: Store = Depends(get_store),
                 actor: str = Query("web")):
    try:
        return store.create_event(body.event_id, body.title, body.scenario, body.lead, actor)
    except ValueError as e:
        raise _http(e)


@router.get("")
def list_events(store: Store = Depends(get_store)):
    return store.list_events()


@router.get("/{event_id}")
def get_event(event_id: str, store: Store = Depends(get_store)):
    try:
        return store.get_event(event_id)
    except ValueError as e:
        raise _http(e)


@router.patch("/{event_id}")
def update_event(event_id: str, body: EventUpdate, store: Store = Depends(get_store),
                 actor: str = Query("web"), reason: str = Query("")):
    try:
        fields = body.model_dump(exclude_unset=True)
        store.update_event(event_id, fields, actor, reason)
        return store.get_event(event_id)
    except ValueError as e:
        raise _http(e)


@router.get("/{event_id}/load")
def load_event(event_id: str, store: Store = Depends(get_store)):
    try:
        return store.load(event_id)
    except ValueError as e:
        raise _http(e)


@router.get("/{event_id}/timeline")
def timeline(event_id: str, store: Store = Depends(get_store)):
    try:
        store.get_event(event_id)
    except ValueError as e:
        raise _http(e)
    return store.timeline(event_id)


@router.put("/{event_id}/definition")
def set_definition(event_id: str, body: DefinitionIn, store: Store = Depends(get_store),
                   actor: str = Query("web"), reason: str = Query("")):
    try:
        store.set_definition(event_id, body.model_dump(), actor, reason)
        return store.load(event_id)["definition"]
    except ValueError as e:
        raise _http(e)


@router.put("/{event_id}/people")
def upsert_people(event_id: str, body: list[PersonIn], store: Store = Depends(get_store),
                  actor: str = Query("web"), reason: str = Query("")):
    try:
        store.upsert_people(event_id, [p.model_dump() for p in body], actor, reason)
        return {"count": len(body), "revision": store.get_event(event_id)["revision"]}
    except ValueError as e:
        raise _http(e)


@router.put("/{event_id}/exposures")
def upsert_exposures(event_id: str, body: list[ExposureIn], store: Store = Depends(get_store),
                     actor: str = Query("web"), reason: str = Query("")):
    try:
        store.upsert_exposures(event_id, [e.model_dump() for e in body], actor, reason)
        return {"count": len(body), "revision": store.get_event(event_id)["revision"]}
    except ValueError as e:
        raise _http(e)


@router.put("/{event_id}/samples")
def upsert_samples(event_id: str, body: list[SampleIn], store: Store = Depends(get_store),
                   actor: str = Query("web"), reason: str = Query("")):
    try:
        store.upsert_samples(event_id, [s.model_dump() for s in body], actor, reason)
        return {"count": len(body), "revision": store.get_event(event_id)["revision"]}
    except ValueError as e:
        raise _http(e)


@router.post("/{event_id}/evidence", status_code=201)
def add_evidence(event_id: str, body: EvidenceIn, store: Store = Depends(get_store),
                 actor: str = Query("web"), reason: str = Query("")):
    try:
        store.add_evidence(event_id, body.model_dump(), actor, reason)
        return body.model_dump()
    except ValueError as e:
        raise _http(e)


@router.post("/{event_id}/conclusions")
def set_conclusion(event_id: str, body: ConclusionIn, store: Store = Depends(get_store),
                   actor: str = Query("web"), reason: str = Query("")):
    try:
        store.set_conclusion(event_id, body.topic, body.model_dump(exclude={"topic"}), actor, reason)
        return store.load(event_id)["conclusions"]
    except ValueError as e:
        raise _http(e)


@router.post("/{event_id}/confirm")
def confirm(event_id: str, body: ConfirmIn, store: Store = Depends(get_store),
            actor: str = Query("web")):
    try:
        store.confirm(event_id, body.node, actor, body.role, body.note,
                      body.evidence_ids, body.disposition)
        return store.load(event_id)["confirmations"]
    except ValueError as e:
        raise _http(e)


@router.get("/{event_id}/analyze")
def analyze_event(event_id: str, store: Store = Depends(get_store)):
    try:
        state = store.load(event_id)
    except ValueError as e:
        raise _http(e)
    stats = analyze(state)
    tz = state["event"].get("timezone", "Asia/Shanghai")
    classified = [{"person_id": p["id"], "status": classify(p, state["definition"], tz)[0],
                   "reason": classify(p, state["definition"], tz)[1]} for p in state["people"]]
    return {"stats": stats, "classified": classified}


@router.get("/{event_id}/report")
def report(event_id: str, kind: str = Query("progress"), store: Store = Depends(get_store)):
    if kind not in ("initial", "progress", "final"):
        raise HTTPException(400, "kind 需为 initial/progress/final")
    try:
        state = store.load(event_id)
    except ValueError as e:
        raise _http(e)
    stats = analyze(state)
    return {"kind": kind, "markdown": render_markdown(state, stats, kind)}
