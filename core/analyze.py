"""对已结构化事实做确定性分析。数值一律由此计算，模型不参与。"""
from collections import Counter
from zoneinfo import ZoneInfo

from core.classify import classify, _parse
from core.stats import proportion, duration_summary, two_by_two

AGES = ((0, 1, "<1"), (1, 7, "1–6"), (7, 20, "7–19"), (20, 60, "20–59"), (60, 131, "60+"))


def analyze(state):
    event = state["event"]
    definition = state["definition"]
    tz = event.get("timezone", "Asia/Shanghai")
    classified = [{"person_id": p["id"], "status": (r := classify(p, definition, tz))[0], "reason": r[1]}
                  for p in state["people"]]
    statuses = {r["person_id"]: r["status"] for r in classified}
    counts = dict(Counter(statuses.values()))
    cases = [p for p in state["people"] if statuses[p["id"]] == "case"]

    symptom_names = sorted({k for p in cases for k in p.get("symptoms", {})})
    symptoms = []
    for name in symptom_names:
        yes = sum(p["symptoms"].get(name) is True for p in cases)
        known = sum(p["symptoms"].get(name) is not None for p in cases)
        symptoms.append({"symptom": name, **proportion(yes, known), "unknown": len(cases) - known})

    by_date, by_sex, by_location, by_age = Counter(), Counter(), Counter(), Counter()
    for p in cases:
        by_date[p.get("onset", "未知")[:10]] += 1 if p.get("onset") else 0
        by_sex[p.get("sex") or "未知"] += 1
        by_location[p.get("location") or "未知"] += 1
        age = p.get("age")
        by_age[next((lab for lo, hi, lab in AGES if age is not None and lo <= age < hi), "未知")] += 1

    incubations, inc_excluded = [], []
    for p in cases:
        anchors = [e for e in state["exposures"] if e["person_id"] == p["id"] and e.get("incubation_anchor")]
        times = {e.get("ate_at") for e in anchors if e.get("ate_at")}
        if len(times) != 1 or not p.get("onset"):
            inc_excluded.append({"person_id": p["id"], "reason": "缺少唯一暴露时间"})
            continue
        try:
            hours = (_parse(p["onset"], tz) - _parse(next(iter(times)), tz)).total_seconds() / 3600
        except (ValueError, TypeError):
            inc_excluded.append({"person_id": p["id"], "reason": "时间无法解析"})
            continue
        if hours >= 0:
            incubations.append(hours)
        else:
            inc_excluded.append({"person_id": p["id"], "reason": "暴露晚于起病"})

    durations, dur_excluded = [], []
    for p in cases:
        if p.get("recovery") and p.get("onset"):
            try:
                durations.append((_parse(p["recovery"], tz) - _parse(p["onset"], tz)).total_seconds() / 3600)
            except (ValueError, TypeError):
                dur_excluded.append({"person_id": p["id"], "reason": "时间无法解析"})
        else:
            dur_excluded.append({"person_id": p["id"], "reason": "尚未恢复或时间未知"})

    associations = []
    for meal, food in sorted({(e["meal_id"], e["food_id"]) for e in state["exposures"] if e.get("meal_id")}):
        a = b = c = d = 0
        for p in state["people"]:
            e = next((x for x in state["exposures"] if x["person_id"] == p["id"]
                      and x.get("meal_id") == meal and x.get("food_id") == food), None)
            if not e or e.get("consumed") is None or statuses[p["id"]] not in ("case", "noncase"):
                continue
            if statuses[p["id"]] == "case" and e["consumed"]:
                a += 1
            elif statuses[p["id"]] == "noncase" and e["consumed"]:
                b += 1
            elif statuses[p["id"]] == "case":
                c += 1
            else:
                d += 1
        associations.append({"meal_id": meal, "food_id": food, **two_by_two(a, b, c, d, "cohort")})

    return {"counts": counts, "symptoms": symptoms,
            "by_date": dict(sorted(by_date.items())), "by_sex": dict(by_sex),
            "by_location": dict(by_location), "by_age": dict(by_age),
            "incubation": {**duration_summary(incubations), "excluded": inc_excluded},
            "duration": {**duration_summary(durations), "excluded": dur_excluded},
            "associations": associations,
            "attack_rate": proportion(len(cases), event.get("population_size") if event.get("population_complete") else None),
            "warnings": ["病例定义未确认，以下为工作统计"]}
