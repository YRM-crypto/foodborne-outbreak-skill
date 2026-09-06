"""后端领域 API 集成测试：案例 CRUD、分析、报告、时间线、知识库浏览。"""
import os
import tempfile

import pytest
from fastapi.testclient import TestClient

from core.store import Store
from server.deps import get_store
from server.main import app


@pytest.fixture()
def client():
    tmp = tempfile.mkdtemp()
    store = Store(os.path.join(tmp, "test.db"))
    app.dependency_overrides[get_store] = lambda: store
    yield TestClient(app)
    app.dependency_overrides.pop(get_store, None)
    store.close()


def _make_case(i):
    return {"id": f"p{i:02d}", "illness_status": "ill",
            "onset": "2024-01-02T12:00:00", "sex": "男", "age": 30,
            "location": "A食堂", "symptoms": {"呕吐": True, "发热": False}}


def _make_noncase(i):
    return {"id": f"n{i:02d}", "illness_status": "well", "sex": "女", "age": 40,
            "location": "A食堂", "symptoms": {}}


def _seed_event(client):
    client.post("/api/events", json={"event_id": "EV-001", "title": "某食堂聚集性呕吐",
                                     "scenario": "closed-cohort", "lead": "调查一组"})
    client.put("/api/events/EV-001/definition", json={
        "label": "测试定义", "text": "餐后呕吐者", "start": "2024-01-01T00:00:00",
        "end": "2024-01-07T23:59:59", "symptoms_any": ["呕吐"], "minimum_symptoms": 1,
        "require_lab": 0})
    client.patch("/api/events/EV-001", json={"population_size": 30, "population_complete": 1})
    people = [_make_case(i) for i in range(18)] + [_make_noncase(i) for i in range(12)]
    client.put("/api/events/EV-001/people", json=people)
    exposures = [{"id": f"e{p['id']}", "person_id": p["id"], "meal_id": "M1",
                  "food_id": "F1", "consumed": 1, "incubation_anchor": 1,
                  "ate_at": "2024-01-02T00:00:00"} for p in people if p["illness_status"] == "ill"]
    exposures += [{"id": f"e{p['id']}", "person_id": p["id"], "meal_id": "M1",
                   "food_id": "F1", "consumed": 0} for p in people if p["illness_status"] == "well"]
    client.put("/api/events/EV-001/exposures", json=exposures)
    return people


def test_event_crud(client):
    r = client.post("/api/events", json={"event_id": "EV-002", "title": "测试事件"})
    assert r.status_code == 201
    assert r.json()["id"] == "EV-002"

    assert any(e["id"] == "EV-002" for e in client.get("/api/events").json())

    got = client.get("/api/events/EV-002").json()
    assert got["title"] == "测试事件"

    r = client.patch("/api/events/EV-002", json={"title": "改名"})
    assert r.status_code == 200
    assert r.json()["title"] == "改名"
    assert r.json()["revision"] > got["revision"]


def test_analysis_flow(client):
    _seed_event(client)
    r = client.get("/api/events/EV-001/analyze")
    assert r.status_code == 200
    body = r.json()
    stats = body["stats"]
    assert stats["counts"]["case"] == 18
    assert stats["counts"]["noncase"] == 12
    assert stats["attack_rate"]["value"] == pytest.approx(0.6)
    assert len(stats["associations"]) == 1
    assert stats["associations"][0]["meal_id"] == "M1"
    # 每条病例都有可解释的判定
    assert len(body["classified"]) == 30
    assert sum(1 for c in body["classified"] if c["status"] == "case") == 18


def test_report_and_timeline(client):
    _seed_event(client)
    r = client.get("/api/events/EV-001/report", params={"kind": "progress"})
    assert r.status_code == 200
    md = r.json()["markdown"]
    assert "某食堂聚集性呕吐" in md
    assert "三间分布" in md

    tl = client.get("/api/events/EV-001/timeline").json()
    actions = {row["action"] for row in tl}
    assert {"init", "set_definition", "upsert_people", "upsert_exposures", "update_event"} <= actions


def test_kb_basis_docs(client):
    r = client.get("/api/kb/docs", params={"lib": "basis"})
    assert r.status_code == 200
    docs = r.json()
    assert docs, "依据库应有文档"
    assert all("id" in d and "preview" in d for d in docs)


def test_assistant_context(client):
    _seed_event(client)
    state = client.get("/api/events/EV-001/load").json()
    from server.assistant import build_context, context_markdown

    ctx = build_context(state)
    assert ctx["counts"]["case"] == 18
    assert ctx["counts"]["noncase"] == 12
    assert ctx["attack_rate"] == "60.0%"
    assert any("F1" in a for a in ctx["associations"])

    md = context_markdown(ctx)
    assert "病例定义" in md
    assert "符合病例定义 18" in md
    assert "罹患率 60.0%" in md
