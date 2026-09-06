"""core/report.py：附表1-9 报告渲染。"""
from core.analyze import analyze
from core.report import render_markdown
from core.store import Store
from core.validate import validate


def _build():
    s = Store(":memory:")
    s.create_event("EV-1", "某学校食堂呕吐")
    s.update_event("EV-1", {"place_type": "学校食堂", "region": "某区", "population_size": 40,
                            "population_known": 1}, "web", "基本信息")
    s.set_definition("EV-1", {"label": "餐后呕吐者", "text": "食堂就餐后呕吐",
                              "start": "2024-01-01T00:00:00", "end": "2024-01-06T23:59:59",
                              "symptoms_any": ["呕吐"], "minimum_symptoms": 1,
                              "probable": {"require_epi_link": True}, "confirmed": {"require_lab": True}},
                     "web", "定义")
    people, exps = [], []
    for i in range(20):
        ill = i < 10
        people.append({"id": f"P{i:03d}", "illness_status": "ill" if ill else "well",
                       "onset": f"2024-01-03T12:00:00" if ill else None, "age": 15 + i,
                       "sex": "男" if i % 2 == 0 else "女", "location": "某中学",
                       "symptoms": {"呕吐": True} if ill else {}})
        exps.append({"id": f"E{i:03d}", "person_id": f"P{i:03d}", "food_id": "凉拌菜",
                     "consumed": 1 if ill else 0, "ate_at": "2024-01-02T12:00:00",
                     "incubation_anchor": 1})
    s.upsert_people("EV-1", people, "web", "个案")
    s.upsert_exposures("EV-1", exps, "web", "暴露")
    s.set_conclusion("EV-1", "agent", {"status": "confirmed", "statement": "副溶血性弧菌",
                                       "reason": "肛拭阳性", "limitations": ""}, "web", "结论")
    s.set_conclusion("EV-1", "food", {"status": "confirmed", "statement": "凉拌菜",
                                      "reason": "RR 显著", "limitations": ""}, "web", "结论")
    return s.load("EV-1")


def test_report_sections():
    st = _build()
    stats = analyze(st)
    md = render_markdown(st, stats, "final")
    for sec in ("一、背景与概述", "三、病例定义", "五、临床表现", "六、三间分布",
                "八、实验室检验", "九、结果分析与调查结论"):
        assert sec in md


def test_report_title_has_elements():
    st = _build()
    stats = analyze(st)
    md = render_markdown(st, stats, "final")
    assert "学校食堂" in md and "副溶血性弧菌" in md


def test_report_mentions_attack_rate():
    st = _build()
    stats = analyze(st)
    md = render_markdown(st, stats, "progress")
    assert "25.0%" in md  # 10/40
