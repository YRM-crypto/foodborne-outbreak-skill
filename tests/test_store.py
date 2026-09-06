"""core/store.py：新数据模型（附表1-8 字段 + 版本化定义 + 阶段状态）。"""
import pytest

from core.store import Store


@pytest.fixture()
def store():
    s = Store(":memory:")
    yield s
    s.close()


def test_create_and_update_event(store):
    store.create_event("EV-1", "某学校食堂呕吐", lead="一组")
    store.update_event("EV-1", {"place_type": "学校食堂", "population_size": 100,
                                "population_known": 1, "is_foodborne": "yes"}, "web", "补基本信息")
    ev = store.get_event("EV-1")
    assert ev["place_type"] == "学校食堂"
    assert ev["population_size"] == 100
    assert ev["population_known"] == 1


def test_update_event_rejects_unknown_field(store):
    store.create_event("EV-1", "x")
    with pytest.raises(ValueError):
        store.update_event("EV-1", {"bogus": 1}, "web", "x")


def test_definition_versioning(store):
    store.create_event("EV-1", "x")
    v1 = store.set_definition("EV-1", {"text": "v1", "symptoms_any": ["呕吐"]}, "web", "初版")
    v2 = store.set_definition("EV-1", {"text": "v2", "symptoms_any": ["呕吐", "腹泻"]}, "web", "调整")
    assert v1 == 1 and v2 == 2
    assert store.load("EV-1")["definition"]["version"] == 2


def test_upsert_tables_and_load(store):
    store.create_event("EV-1", "x")
    store.upsert_people("EV-1", [{"id": "P1", "illness_status": "ill", "symptoms": {"呕吐": True}}], "web", "个案")
    store.upsert_exposures("EV-1", [{"id": "E1", "person_id": "P1", "food_id": "凉拌菜", "consumed": 1}], "web", "暴露")
    store.upsert_foods("EV-1", [{"id": "凉拌菜", "category": "蔬菜及蔬菜制品"}], "web", "食品清单")
    store.upsert_samples("EV-1", [{"id": "S1", "category": "biological", "person_id": "P1",
                                   "tests": [{"item": "副溶血性弧菌", "result": "检出"}]}], "web", "样本")
    store.add_hygiene("EV-1", [{"id": "H1", "aspect": "加工过程", "item": "生熟分开", "finding": "无明显生熟标记", "problem": 1}], "web", "卫生学")
    store.add_control("EV-1", [{"id": "C1", "measure": "封存", "target": "凉拌菜", "implemented": "已封存"}], "web", "控制")
    state = store.load("EV-1")
    assert len(state["people"]) == 1
    assert state["foods"][0]["category"] == "蔬菜及蔬菜制品"
    assert state["samples"][0]["tests"][0]["result"] == "检出"
    assert state["hygiene"][0]["problem"] == 1
    assert state["controls"][0]["measure"] == "封存"


def test_set_stage_valid_and_invalid(store):
    store.create_event("EV-1", "x")
    store.set_stage("EV-1", "case_def", "done", "web", "已定定义")
    assert store.load("EV-1")["stages"]["case_def"]["status"] == "done"
    with pytest.raises(ValueError):
        store.set_stage("EV-1", "bogus", "done", "web")
    with pytest.raises(ValueError):
        store.set_stage("EV-1", "case_def", "bogus", "web")


def test_timeline_audit(store):
    store.create_event("EV-1", "x")
    store.set_stage("EV-1", "intake", "done", "web", "接报完成")
    t = store.timeline("EV-1")
    assert any(r["action"].startswith("stage:") for r in t)
