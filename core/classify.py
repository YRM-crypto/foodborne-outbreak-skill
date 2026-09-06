"""病例三级判定：确诊 / 可能 / 疑似 / 未发病 / 排除 / 待定。依据 S2012 §4.2。

- 疑似：符合时间/地区/人群范围 + 症状达标。
- 可能：疑似 + 与确诊病例有共同可疑暴露（流行病学关联）。
- 确诊：疑似/可能 + 致病因子检验阳性（生物标本）。
- 排除：时间/地区/人群范围外，或已知症状不符，或明确未发病。
- 待定：信息不足，无法判定。

判定是派生视图：任何个案/暴露/样本/定义变化后重算，不落库。
"""
from datetime import datetime
from zoneinfo import ZoneInfo

CLASS_STATUSES = ("确诊", "可能", "疑似", "未发病", "排除", "待定")


def _parse(v, tz="Asia/Shanghai"):
    v = v.replace("Z", "+00:00")
    dt = datetime.fromisoformat(v)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo(tz))
    return dt


def classify(person, definition, tz="Asia/Shanghai", lab_positive=False, epi_linked=False):
    """返回 (状态, 理由)。lab_positive / epi_linked 由 analyze() 预计算。"""
    if not definition:
        return "待定", "尚无病例定义"
    adj = person.get("adjudication")
    if adj and adj.get("definition_version") == definition.get("version"):
        return adj.get("status", "待定"), "人工判读：" + adj.get("reason", "")

    # 地区 / 人群范围
    for key, field in (("locations", "location"), ("populations", "population")):
        limits = definition.get(key) or []
        if limits and person.get(field) is None:
            return "待定", field + "未知"
        if limits and person[field] not in limits:
            return "排除", field + "不属于调查范围"

    if person.get("illness_status") == "well":
        return "未发病", "明确未发病"
    if person.get("illness_status") != "ill" or not person.get("onset"):
        return "待定", "发病状态或起病时间未知"

    # 时间范围
    try:
        onset = _parse(person["onset"], tz)
        start, end = _parse(definition["start"], tz), _parse(definition["end"], tz)
    except (ValueError, KeyError, TypeError):
        return "待定", "起病时间无法解析"
    if onset < start or onset > end:
        return "排除", "起病时间不在定义范围"

    # 症状（疑似标准）
    ss = person.get("symptoms") or {}
    minimum = definition.get("minimum_symptoms", 1)
    positive = sum(ss.get(k) is True for k in definition.get("symptoms_any", []))
    unknown = sum(ss.get(k) is None for k in definition.get("symptoms_any", []))
    if positive + unknown < minimum:
        return "排除", "已知症状不符合定义"
    if positive < minimum:
        return "待定", "症状信息不足"

    # 已符合疑似；再看确诊 / 可能
    confirmed = definition.get("confirmed") or {}
    if confirmed.get("require_lab") and lab_positive:
        return "确诊", "符合病例定义且致病因子检验阳性"
    probable = definition.get("probable") or {}
    if probable.get("require_epi_link") and epi_linked:
        return "可能", "符合病例定义且与确诊病例有共同暴露"
    return "疑似", "符合当前调查病例定义"
