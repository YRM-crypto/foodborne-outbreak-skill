"""病例三级判定：确诊/疑似级纳入口径，非病因确诊。依据 S2012 §4.2。"""
from datetime import datetime
from zoneinfo import ZoneInfo

DEFINITION_ELEMENTS = ("time", "location", "population", "symptoms", "lab")
TIERS = ("case", "noncase", "excluded", "pending")


def _parse(v, tz="Asia/Shanghai"):
    v = v.replace("Z", "+00:00")
    dt = datetime.fromisoformat(v)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo(tz))
    return dt


def classify(person, definition, tz="Asia/Shanghai"):
    if not definition:
        return "pending", "尚无病例定义"
    adj = person.get("adjudication")
    if adj:
        if adj.get("definition_version") == definition.get("version"):
            return adj["status"], "人工判读：" + adj.get("reason", "")
        return "pending", "人工判读版本已过期"
    for key, field in (("locations", "location"), ("populations", "population")):
        limits = definition.get(key) or []
        if limits:
            if person.get(field) is None:
                return "pending", field + "未知"
            if person[field] not in limits:
                return "excluded", field + "不属于调查范围"
    if person.get("illness_status") == "well":
        return "noncase", "明确未发病"
    if person.get("illness_status") != "ill" or not person.get("onset"):
        return "pending", "发病状态或起病时间未知"
    try:
        onset = _parse(person["onset"], tz)
        start, end = _parse(definition["start"], tz), _parse(definition["end"], tz)
    except (ValueError, KeyError, TypeError):
        return "pending", "起病时间无法解析"
    if onset < start or onset > end:
        return "excluded", "起病时间不在定义范围"
    ss = person.get("symptoms") or {}
    minimum = definition.get("minimum_symptoms", 1)
    positive = sum(ss.get(k) is True for k in definition.get("symptoms_any", []))
    unknown = sum(ss.get(k) is None for k in definition.get("symptoms_any", []))
    if positive + unknown < minimum:
        return "excluded", "已知症状不符合定义"
    if positive < minimum:
        return "pending", "症状信息不足"
    if definition.get("require_lab"):
        if person.get("lab_eligible") is None:
            return "pending", "检验条件待判读"
        if not person["lab_eligible"]:
            return "excluded", "不符合检验条件"
    return "case", "符合当前调查病例定义，非病因确诊"
