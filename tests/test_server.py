"""后端领域 API 集成测试：案例 CRUD、分析、报告、时间线、知识库浏览、助手上下文。"""
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


def _seed_event(client):
    client.post("/api/events", json={"event_id": "EV-001", "title": "某食堂聚集性呕吐",
                                     "lead": "调查一组"})
    client.patch("/api/events/EV-001", json={"place_type": "学校食堂", "region": "某区",
                                             "population_size": 30, "population_known": 1,
                                             "study_design": "cohort"})
    client.put("/api/events/EV-001/definition", json={
        "label": "测试定义", "text": "餐后呕吐者", "start": "2024-01-01T00:00:00",
        "end": "2024-01-07T23:59:59", "symptoms_any": ["呕吐"], "minimum_symptoms": 1,
        "probable": {"require_epi_link": True}, "confirmed": {"require_lab": True}})

    people = []
    for i in range(18):
        people.append({"id": f"p{i:02d}", "illness_status": "ill",
                       "onset": "2024-01-02T12:00:00", "sex": "男", "age": 30,
                       "location": "A食堂", "symptoms": {"呕吐": True, "发热": False}})
    for i in range(12):
        people.append({"id": f"n{i:02d}", "illness_status": "well", "sex": "女", "age": 40,
                       "location": "A食堂", "symptoms": {}})
    client.put("/api/events/EV-001/people", json=people)

    # 凉拌菜：15/18 病例进食、2/12 未发病进食 → RR≈3.82（非零单元格，可算效应量）
    exposures = []
    for p in people:
        idx = int(p["id"][1:])
        if p["illness_status"] == "ill":
            ate = 0 if idx % 6 == 0 else 1
        else:
            ate = 1 if idx % 6 == 0 else 0
        exposures.append({"id": f"e{p['id']}", "person_id": p["id"], "meal_id": "M1",
                          "food_id": "凉拌菜", "consumed": ate, "incubation_anchor": 1,
                          "ate_at": "2024-01-02T00:00:00"})
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
    assert stats["case_count"] == 18
    assert stats["counts"]["疑似"] == 18
    assert stats["counts"]["未发病"] == 12
    assert stats["attack_rate"]["value"] == pytest.approx(0.6)
    assert len(stats["associations"]) == 1
    assert stats["associations"][0]["food_id"] == "凉拌菜"
    assert stats["associations"][0]["effect"] == pytest.approx(3.82, abs=0.05)
    assert stats["associations"][0]["p_fisher_two_sided"] < 0.05
    # 每条登记的人都有可解释的判定，且附带校验清单（本事件无问题 → 空清单）
    assert len(stats["classified"]) == 30
    assert sum(1 for c in stats["classified"] if c["status"] == "疑似") == 18
    assert isinstance(body["checks"], list)


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
    assert ctx["counts"]["疑似"] == 18
    assert ctx["counts"]["未发病"] == 12
    assert ctx["attack_rate"] == "60.0%"
    assert any("凉拌菜" in a for a in ctx["associations"])

    md = context_markdown(ctx)
    assert "病例定义" in md
    assert "疑似 18" in md
    assert "罹患率 60.0%" in md
