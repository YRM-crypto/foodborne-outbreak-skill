"""把事件状态序列化为《食源性疾病暴发事件监测信息表（附表 1-8）》形状的 JSON。

v1 只做序列化 + 报送适配器占位；真正报送系统 API 后接 submit()。
"""
from core.classify import classify


def export_monitoring_json(state):
    event = state["event"]
    definition = state["definition"]
    tz = event.get("timezone", "Asia/Shanghai")
    statuses = {p["id"]: classify(p, definition, tz)[0] for p in state["people"]}
    cases = [p for p in state["people"] if statuses[p["id"]] == "case"]
    symptom_names = sorted({k for p in cases for k in p.get("symptoms", {}) if p["symptoms"].get(k) is True})
    symptom_counts = {n: sum(p["symptoms"].get(n) is True for p in cases) for n in symptom_names}

    return {
        "事件编号": event.get("id"),
        "发生日期": event.get("received_at"),
        "疾病暴发地区": event.get("location"),
        "发病人数": len(cases),
        "住院人数": sum(p.get("hospitalized") is True for p in cases),
        "死亡人数": sum(p.get("died") is True for p in cases),
        "症状": symptom_counts,
        "致病因素": (state["conclusions"][0]["statement"]
                     if state["conclusions"] and state["conclusions"][0].get("statement") else None),
        "原因食品": None,
        "是否食源性疾病": True,
    }


def submit(payload, config=None):
    """报送适配器占位：v1 不实现，抛 NotImplementedError。"""
    raise NotImplementedError("报送系统 API 待接入")
