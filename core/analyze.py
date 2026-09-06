"""对已结构化事实做确定性分析。数值一律由此计算，模型不参与。

派生视图（判定/症状表/三间分布/潜伏期/四格表/罹患率）永远是当前证据的函数：
任何个案/暴露/样本/定义变化后调用本函数即得最新结果，不落库、不手填。
"""
from collections import Counter
from zoneinfo import ZoneInfo

from core.classify import classify, _parse
from core.constants import AGE_GROUPS, SYMPTOMS, age_group
from core.stats import duration_summary, proportion, two_by_two

POSITIVE_RESULTS = {"检出", "阳性", "+"}
CASE_STATUSES = ("确诊", "可能", "疑似")


def _parse_dt(v, tz="Asia/Shanghai"):
    v = v.replace("Z", "+00:00")
    dt = _parse(v, tz)
    return dt


def _lab_positive(person_id, samples):
    for s in samples:
        if s.get("category") != "biological" or s.get("person_id") != person_id:
            continue
        for t in (s.get("tests") or []):
            if t.get("result") in POSITIVE_RESULTS:
                return True
    return False


def _epi_linked(person_id, exposures, confirmed_ids):
    if not confirmed_ids:
        return False
    mine = {e.get("food_id") for e in exposures
            if e.get("person_id") == person_id and e.get("consumed")}
    shared = {e.get("food_id") for e in exposures
              if e.get("person_id") in confirmed_ids and e.get("consumed")}
    return bool(mine & shared)


def _classify_all(state, tz):
    """两遍判定：先定确诊（实验室阳性），再依确诊算流行病学关联定「可能」。"""
    people = state["people"]
    definition = state["definition"]
    samples = state["samples"]
    exposures = state["exposures"]
    lab = {p["id"]: _lab_positive(p["id"], samples) for p in people}
    first = {p["id"]: classify(p, definition, tz, lab_positive=lab[p["id"]], epi_linked=False)
             for p in people}
    confirmed = {pid for pid, (st, _) in first.items() if st == "确诊"}
    epi = {p["id"]: _epi_linked(p["id"], exposures, confirmed) for p in people}
    return {p["id"]: classify(p, definition, tz, lab_positive=lab[p["id"]], epi_linked=epi[p["id"]])
            for p in people}


def analyze(state):
    event = state["event"]
    definition = state["definition"]
    tz = event.get("timezone", "Asia/Shanghai")
    people = state["people"]
    exposures = state["exposures"]

    judged = _classify_all(state, tz)
    statuses = {pid: st for pid, (st, _) in judged.items()}
    classified = [{"person_id": pid, "status": st, "reason": rs} for pid, (st, rs) in judged.items()]
    counts = dict(Counter(statuses.values()))
    case_ids = {pid for pid, st in statuses.items() if st in CASE_STATUSES}
    cases = [p for p in people if p["id"] in case_ids]

    # —— 症状表（附表 1-8 四，标准化清单 + 个案中的其他症状）——
    extra = sorted({k for p in cases for k in (p.get("symptoms") or {}) if k not in SYMPTOMS})
    symptom_names = SYMPTOMS + extra
    symptoms = []
    for name in symptom_names:
        yes = sum((p.get("symptoms") or {}).get(name) is True for p in cases)
        known = sum((p.get("symptoms") or {}).get(name) is not None for p in cases)
        symptoms.append({"symptom": name, **proportion(yes, known), "unknown": len(cases) - known})

    # —— 三间分布 ——
    by_date, by_sex, by_location = Counter(), Counter(), Counter()
    for p in cases:
        if p.get("onset"):
            by_date[p["onset"][:10]] += 1
        by_sex[p.get("sex") or "未知"] += 1
        by_location[p.get("location") or "未知"] += 1

    # —— 年龄段分组（附表 1-8 三：年龄段 × 发病/住院/死亡）——
    age_groups = []
    for lo, hi, label in AGE_GROUPS:
        group_cases = [p for p in cases if age_group(p.get("age")) == label]
        if not group_cases:
            continue
        age_groups.append({
            "label": label,
            "cases": len(group_cases),
            "hospitalized": sum(1 for p in group_cases if p.get("hospitalized")),
            "died": sum(1 for p in group_cases if p.get("died")),
        })

    # —— 潜伏期 / 病程 ——
    incubations, inc_excluded = [], []
    for p in cases:
        anchors = [e for e in exposures if e.get("person_id") == p["id"] and e.get("incubation_anchor")]
        times = {e.get("ate_at") for e in anchors if e.get("ate_at")}
        if len(times) != 1 or not p.get("onset"):
            inc_excluded.append({"person_id": p["id"], "reason": "缺少唯一暴露时间"})
            continue
        try:
            hours = (_parse_dt(p["onset"], tz) - _parse_dt(next(iter(times)), tz)).total_seconds() / 3600
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
                durations.append((_parse_dt(p["recovery"], tz) - _parse_dt(p["onset"], tz)).total_seconds() / 3600)
            except (ValueError, TypeError):
                dur_excluded.append({"person_id": p["id"], "reason": "时间无法解析"})
        else:
            dur_excluded.append({"person_id": p["id"], "reason": "尚未恢复或时间未知"})

    # —— 餐次 × 食品 四格表（队列 RR / 病例对照 OR，依研究设计）——
    design = "case-control" if event.get("study_design") == "case-control" else "cohort"
    associations = []
    for food in sorted({e["food_id"] for e in exposures if e.get("food_id")}):
        a = b = c = d = 0
        for p in people:
            e = next((x for x in exposures if x.get("person_id") == p["id"]
                      and x.get("food_id") == food), None)
            if not e or e.get("consumed") is None or statuses[p["id"]] not in CASE_STATUSES + ("未发病",):
                continue
            if statuses[p["id"]] in CASE_STATUSES and e["consumed"]:
                a += 1
            elif statuses[p["id"]] == "未发病" and e["consumed"]:
                b += 1
            elif statuses[p["id"]] in CASE_STATUSES:
                c += 1
            else:
                d += 1
        associations.append({"food_id": food, **two_by_two(a, b, c, d, design)})

    # —— 罹患率 = 发病人数 / 暴露人数 ——
    population_size = event.get("population_size") if event.get("population_known") else None
    attack_rate = proportion(len(cases), population_size)

    warnings = []
    if not definition:
        warnings.append("尚未制定病例定义，以下为工作统计")
    if not exposures:
        warnings.append("尚未录入暴露史，无法计算食品关联")
    if counts.get("待定", 0) > 0:
        warnings.append(f"有 {counts['待定']} 人待定（信息不足），判读可能随补充材料变化")

    return {
        "counts": counts,
        "case_count": len(cases),
        "confirmed_count": counts.get("确诊", 0),
        "probable_count": counts.get("可能", 0),
        "suspected_count": counts.get("疑似", 0),
        "classified": classified,
        "symptoms": symptoms,
        "by_date": dict(sorted(by_date.items())),
        "by_sex": dict(by_sex),
        "by_location": dict(by_location),
        "age_groups": age_groups,
        "incubation": {**duration_summary(incubations), "excluded": inc_excluded},
        "duration": {**duration_summary(durations), "excluded": dur_excluded},
        "associations": associations,
        "attack_rate": attack_rate,
        "study_design": design,
        "population": {"size": event.get("population_size"), "known": bool(event.get("population_known")),
                       "basis": event.get("population_basis")},
        "warnings": warnings,
    }
