"""校验规则：把「串联」变成可报告、可核查的检查清单。

返回 check 列表：{code, level(error/warn/info), title, detail}。
派生指标的一致性在这里校验——任何阶段补充材料后重跑即可发现断链。
"""
from core.constants import TOPIC_NAMES


def _check(code, level, title, detail):
    return {"code": code, "level": level, "title": title, "detail": detail}


def _has_lab_positive(samples):
    return any(t.get("result") in ("检出", "阳性", "+")
               for s in samples for t in (s.get("tests") or []))


def _support_grade(state, stats):
    """§7.1：现场流调 / 卫生学 / 实验室三方面支持程度。"""
    has_epi = stats["case_count"] > 0 and len(state["exposures"]) > 0
    has_hygiene = len(state["hygiene"]) > 0
    has_lab = _has_lab_positive(state["samples"])
    aspects = [a for a, ok in (("流调", has_epi), ("卫生学", has_hygiene), ("实验室", has_lab)) if ok]
    n = len(aspects)
    if n == 3:
        return "三方相互支持，可作调查结论", aspects
    if n == 2 and has_epi:
        return "流调得到单一支持，结果合理可作结论", aspects
    if n == 1 and has_epi:
        return "仅流调结果，需专家组审定后作结论", aspects
    return "现有证据不足以下结论，需说明原因", aspects


def validate(state, stats, pathogens=None):
    checks = []
    d = state["definition"]

    # 1. 病例定义
    if not d:
        checks.append(_check("no_definition", "warn", "尚未制定病例定义",
                             "无法判定病例，先进入「病例定义」阶段"))
    else:
        missing = []
        if not d.get("start") or not d.get("end"):
            missing.append("时间范围")
        if not d.get("symptoms_any"):
            missing.append("症状标准")
        if missing:
            checks.append(_check("definition_incomplete", "warn", "病例定义不完整",
                                 f"缺少：{'、'.join(missing)}"))

    # 2. 病例数 / 罹患率
    if stats["case_count"] == 0:
        checks.append(_check("no_cases", "warn", "尚无符合定义的病例",
                             "病例定义或个案调查尚未完成，先补个案"))
    if stats["counts"].get("待定", 0):
        checks.append(_check("pending_cases", "info", f"{stats['counts']['待定']} 人待定",
                             "信息不足，随补充材料会重判（病例人数/分类可能变化）"))
    if not stats["population"]["known"]:
        checks.append(_check("population_missing", "info", "暴露人数未确定",
                             "无法计算罹患率；暴露人群确定后自动改用队列研究(RR)"))

    # 3. 实验室阳性 ↔ 确诊
    if _has_lab_positive(state["samples"]) and stats["confirmed_count"] == 0:
        checks.append(_check("lab_unconfirmed", "warn", "存在阳性检验但无确诊病例",
                             "生物标本检出致病因子，但无「确诊」病例：检查病例定义的确诊标准或标本关联"))

    # 4. 结论支持度（§7.1）
    if any(c.get("statement") for c in state["conclusions"]):
        grade, aspects = _support_grade(state, stats)
        checks.append(_check("conclusion_support", "info", "结论支持度",
                             f"现有{'、'.join(aspects) or '无'}方面证据——{grade}"))

    # 5. 原因食品结论 vs 四格表
    food_concl = next((c for c in state["conclusions"] if c["topic"] == "food"), None)
    if food_concl and food_concl.get("statement"):
        sig = [a for a in stats["associations"]
               if a.get("effect") and a.get("effect") > 1
               and (a.get("p_fisher_two_sided") or 1) < 0.05]
        if sig:
            named = next((a for a in sig if a["food_id"] in food_concl["statement"]), None)
            if not named:
                checks.append(_check("food_not_sig", "warn", "原因食品结论与关联分析不一致",
                                     f"统计上显著的食品是 {'、'.join(a['food_id'] for a in sig)}，"
                                     f"但结论未指向其中任一，请核对"))

    # 6. 潜伏期 vs 致病因子典型范围
    agent = next((c for c in state["conclusions"] if c["topic"] == "agent"), None)
    if agent and agent.get("statement") and pathogens and stats["incubation"]["n"]:
        pname = next((p["name"] for p in pathogens if p["name"] in agent["statement"]), None)
        if pname:
            p = next(x for x in pathogens if x["name"] == pname)
            med = stats["incubation"]["median"]
            lo, hi = p.get("latency_min"), p.get("latency_max")
            if lo is not None and hi is not None and (med < lo or med > hi):
                checks.append(_check("incubation_mismatch", "warn", "潜伏期与致病因子不符",
                                     f"结论致病因子 {pname} 潜伏期典型 {lo}–{hi} 小时，"
                                     f"本次中位潜伏期 {med:.1f} 小时，超出范围，请核实暴露时间或致病因子"))

    return checks
