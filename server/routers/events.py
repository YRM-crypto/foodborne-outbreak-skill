"""案例 CRUD + 录入 + 分析 + 报告 + 时间线。复用 core/ 确定性引擎。

派生指标（判定/汇总/报告）一律由 core.analyze/validate/report 从当前证据重算，
服务端只负责读写原始材料。
"""
from fastapi import APIRouter, Depends, HTTPException, Query

from core.analyze import analyze
from core.report import render_markdown
from core.validate import validate

from ..deps import get_store
from ..schemas import (
    ConclusionIn,
    ControlIn,
    CreateEvent,
    DefinitionIn,
    EventUpdate,
    EvidenceIn,
    ExposureIn,
    FoodIn,
    HygieneIn,
    PersonIn,
    SampleIn,
    StageIn,
)

router = APIRouter()


def _http(e: ValueError) -> HTTPException:
    return HTTPException(404 if "事件不存在" in str(e) else 400, str(e))


@router.post("", status_code=201)
def create_event(body: CreateEvent, store=Depends(get_store)):
    try:
        return store.create_event(body.event_id, body.title, body.lead, actor="web")
    except ValueError as e:
        raise _http(e)


@router.post("/seed-demo")
def seed_demo(store=Depends(get_store)):
    from ..seed import EVENT_ID, seed_demo_event

    ev = seed_demo_event(store)
    return {"created": ev is not None, "event_id": EVENT_ID}


@router.get("")
def list_events(store=Depends(get_store)):
    return store.list_events()


@router.get("/{event_id}")
def get_event(event_id: str, store=Depends(get_store)):
    try:
        return store.get_event(event_id)
    except ValueError as e:
        raise _http(e)


@router.patch("/{event_id}")
def update_event(event_id: str, body: EventUpdate, store=Depends(get_store), reason: str = Query("")):
    try:
        fields = body.model_dump(exclude_unset=True)
        store.update_event(event_id, fields, "web", reason)
        return store.get_event(event_id)
    except ValueError as e:
        raise _http(e)


@router.get("/{event_id}/load")
def load_event(event_id: str, store=Depends(get_store)):
    try:
        return store.load(event_id)
    except ValueError as e:
        raise _http(e)


@router.get("/{event_id}/timeline")
def timeline(event_id: str, store=Depends(get_store)):
    try:
        store.get_event(event_id)
    except ValueError as e:
        raise _http(e)
    return store.timeline(event_id)


@router.put("/{event_id}/definition")
def set_definition(event_id: str, body: DefinitionIn, store=Depends(get_store), reason: str = Query("")):
    try:
        version = store.set_definition(event_id, body.model_dump(), "web", reason)
        return {**store.load(event_id)["definition"], "version": version}
    except ValueError as e:
        raise _http(e)


@router.put("/{event_id}/people")
def upsert_people(event_id: str, body: list[PersonIn], store=Depends(get_store), reason: str = Query("")):
    try:
        store.upsert_people(event_id, [p.model_dump() for p in body], "web", reason)
        return {"count": len(body), "revision": store.get_event(event_id)["revision"]}
    except ValueError as e:
        raise _http(e)


@router.put("/{event_id}/exposures")
def upsert_exposures(event_id: str, body: list[ExposureIn], store=Depends(get_store), reason: str = Query("")):
    try:
        store.upsert_exposures(event_id, [e.model_dump() for e in body], "web", reason)
        return {"count": len(body), "revision": store.get_event(event_id)["revision"]}
    except ValueError as e:
        raise _http(e)


@router.put("/{event_id}/foods")
def upsert_foods(event_id: str, body: list[FoodIn], store=Depends(get_store), reason: str = Query("")):
    try:
        store.upsert_foods(event_id, [f.model_dump() for f in body], "web", reason)
        return {"count": len(body), "revision": store.get_event(event_id)["revision"]}
    except ValueError as e:
        raise _http(e)


@router.put("/{event_id}/samples")
def upsert_samples(event_id: str, body: list[SampleIn], store=Depends(get_store), reason: str = Query("")):
    try:
        store.upsert_samples(event_id, [s.model_dump() for s in body], "web", reason)
        return {"count": len(body), "revision": store.get_event(event_id)["revision"]}
    except ValueError as e:
        raise _http(e)


@router.put("/{event_id}/hygiene")
def add_hygiene(event_id: str, body: list[HygieneIn], store=Depends(get_store), reason: str = Query("")):
    try:
        store.add_hygiene(event_id, [h.model_dump() for h in body], "web", reason)
        return {"count": len(body), "revision": store.get_event(event_id)["revision"]}
    except ValueError as e:
        raise _http(e)


@router.put("/{event_id}/controls")
def add_control(event_id: str, body: list[ControlIn], store=Depends(get_store), reason: str = Query("")):
    try:
        store.add_control(event_id, [c.model_dump() for c in body], "web", reason)
        return {"count": len(body), "revision": store.get_event(event_id)["revision"]}
    except ValueError as e:
        raise _http(e)


@router.post("/{event_id}/evidence", status_code=201)
def add_evidence(event_id: str, body: EvidenceIn, store=Depends(get_store), reason: str = Query("")):
    try:
        store.add_evidence(event_id, body.model_dump(), "web", reason)
        return body.model_dump()
    except ValueError as e:
        raise _http(e)


@router.post("/{event_id}/conclusions")
def set_conclusion(event_id: str, body: ConclusionIn, store=Depends(get_store), reason: str = Query("")):
    try:
        store.set_conclusion(event_id, body.topic, body.model_dump(exclude={"topic"}), "web", reason)
        return store.load(event_id)["conclusions"]
    except ValueError as e:
        raise _http(e)


@router.post("/{event_id}/stages")
def set_stage(event_id: str, body: StageIn, store=Depends(get_store)):
    try:
        store.set_stage(event_id, body.stage, body.status, "web", body.note, body.evidence_ids)
        return store.load(event_id)["stages"]
    except ValueError as e:
        raise _http(e)


@router.get("/{event_id}/analyze")
def analyze_event(event_id: str, store=Depends(get_store)):
    try:
        state = store.load(event_id)
    except ValueError as e:
        raise _http(e)
    stats = analyze(state)
    checks = validate(state, stats)
    return {"stats": stats, "checks": checks}


@router.get("/{event_id}/report")
def report(event_id: str, kind: str = Query("progress"), store=Depends(get_store)):
    if kind not in ("initial", "progress", "final"):
        raise HTTPException(400, "kind 需为 initial/progress/final")
    try:
        state = store.load(event_id)
    except ValueError as e:
        raise _http(e)
    stats = analyze(state)
    checks = validate(state, stats)
    return {"kind": kind, "markdown": render_markdown(state, stats, kind, checks)}
