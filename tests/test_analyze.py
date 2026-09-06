"""core/analyze.py：派生指标（症状/三间/年龄段/潜伏期/四格表/罹患率）。"""
from core.analyze import analyze
from core.store import Store


def _state():
    s = Store(":memory:")
    s.create_event("EV-1", "某学校食堂呕吐")
    s.update_event("EV-1", {"place_type": "学校食堂", "population_size": 40,
                            "population_known": 1}, "web", "基本信息")
    s.set_definition("EV-1", {
        "label": "餐后呕吐者", "text": "1月2-5日食堂就餐后呕吐",
        "start": "2024-01-01T00:00:00", "end": "2024-01-06T23:59:59",
        "locations": ["某中学"], "symptoms_any": ["呕吐"], "minimum_symptoms": 1,
        "probable": {"require_epi_link": True}, "confirmed": {"require_lab": True},
    }, "web", "定义")
    people, exps = [], []
    for i in range(40):
        ill = i < 20
        people.append({"id": f"P{i:03d}", "illness_status": "ill" if ill else "well",
                       "onset": f"2024-01-03T{10 + i % 10:02d}:00:00" if ill else None,
                       "age": 15 + i % 5, "sex": "男" if i % 2 == 0 else "女",
                       "location": "某中学", "symptoms": {"呕吐": True, "腹泻": i % 3 == 0} if ill else {}})
        exps.append({"id": f"E{i:03d}", "person_id": f"P{i:03d}", "meal_id": "午餐",
                     "food_id": "凉拌菜", "consumed": (1 if i % 4 != 0 else 0) if ill else (1 if i % 7 == 0 else 0),
                     "ate_at": "2024-01-02T12:00:00", "incubation_anchor": 1})
    s.upsert_people("EV-1", people, "web", "个案")
    s.upsert_exposures("EV-1", exps, "web", "暴露")
    s.upsert_samples("EV-1", [{"id": "S1", "category": "biological", "person_id": "P000",
                               "source": "肛拭", "tests": [{"item": "金葡菌", "result": "检出"}]}], "web", "样本")
    return s.load("EV-1")


def test_counts_and_attack_rate():
    stats = analyze(_state())
    assert stats["case_count"] == 20
    assert stats["confirmed_count"] == 1
    assert stats["attack_rate"]["value"] == 0.5  # 20/40


def test_symptoms_standardized():
    stats = analyze(_state())
    by_name = {r["symptom"]: r for r in stats["symptoms"]}
    assert by_name["呕吐"]["numerator"] == 20
    assert by_name["腹泻"]["numerator"] > 0


def test_age_groups():
    stats = analyze(_state())
    total = sum(g["cases"] for g in stats["age_groups"])
    assert total == 20
    assert all(g["label"] in ("7–19岁", "20–59岁") for g in stats["age_groups"])


def test_incubation_computed():
    stats = analyze(_state())
    assert stats["incubation"]["n"] == 20
    assert stats["incubation"]["minimum"] >= 0


def test_association_significant():
    stats = analyze(_state())
    assoc = next(a for a in stats["associations"] if a["food_id"] == "凉拌菜")
    assert assoc["measure"] == "RR"
    assert assoc["effect"] > 1
    assert assoc["p_fisher_two_sided"] < 0.05


def test_epi_link_excludes_universal_food():
    """米饭人人皆吃，不应作为「可能」的流行病学关联依据。"""
    s = Store(":memory:")
    s.create_event("EV-1", "x")
    s.update_event("EV-1", {"population_size": 10, "population_known": 1}, "web", "x")
    s.set_definition("EV-1", {
        "start": "2024-01-01T00:00:00", "end": "2024-01-06T23:59:59",
        "symptoms_any": ["呕吐"], "minimum_symptoms": 1,
        "probable": {"require_epi_link": True}, "confirmed": {"require_lab": True},
    }, "web", "x")
    people, exps = [], []
    for i in range(10):
        ill = i < 2
        people.append({"id": f"P{i:03d}", "illness_status": "ill" if ill else "well",
                       "onset": "2024-01-03T12:00:00" if ill else None,
                       "symptoms": {"呕吐": True} if ill else {}})
        exps.append({"id": f"E{i:03d}a", "person_id": f"P{i:03d}", "food_id": "米饭",
                     "consumed": 1, "ate_at": "2024-01-02T12:00:00", "incubation_anchor": 1})
        exps.append({"id": f"E{i:03d}b", "person_id": f"P{i:03d}", "food_id": "凉拌菜",
                     "consumed": 1 if i == 5 else 0, "ate_at": "2024-01-02T12:00:00",
                     "incubation_anchor": 1})
    s.upsert_people("EV-1", people, "web", "x")
    s.upsert_exposures("EV-1", exps, "web", "x")
    s.upsert_samples("EV-1", [{"id": "S1", "category": "biological", "person_id": "P000",
                               "tests": [{"item": "金葡菌", "result": "检出"}]}], "web", "x")
    stats = analyze(s.load("EV-1"))
    assert stats["counts"]["确诊"] == 1
    assert stats["counts"].get("可能", 0) == 0  # P001 与确诊 P000 仅共享米饭（通用食品），不判可能
    assert stats["counts"]["疑似"] == 1
