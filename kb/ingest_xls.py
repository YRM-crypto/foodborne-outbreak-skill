"""读 500 条结构化监测数据（附表 1-8 扁平化 xls）→ 标准化事件 dict。"""
import os

SYMPTOM_COLS = ["恶心", "呕吐", "腹痛", "腹泻", "发热", "头晕", "头痛", "昏迷", "出汗", "面部潮红",
                "瘙痒", "吞咽困难", "呼吸困难", "视力模糊", "眼睑下垂", "抽搐", "发绀", "里急后重",
                "阵发性绞痛", "皮疹", "肌肉疼痛", "全身水肿", "肝疼痛或肿大", "癫痫发作",
                "手指或脚趾刺痛", "感觉麻木", "荨麻疹", "皮肤潮红", "唇舌指尖等麻木", "谵妄、幻觉", "口干", "其他"]


def _num(v):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def normalize_row(row):
    agent_cat = str(row.get("致病因素类别", "") or "").strip()
    agent_name = str(row.get("致病因素名称", "") or "").strip()
    food_name = str(row.get("原因食品名称", "") or "").strip()
    venue = str(row.get("疾病暴发场所类型", "") or "").strip()
    symptoms = {c: _num(row.get(c)) for c in SYMPTOM_COLS}
    symptoms = {k: v for k, v in symptoms.items() if v not in (None, 0)}
    return {
        "card": str(row.get("卡号", "") or "").strip(),
        "agent_category": agent_cat,
        "agent_name": agent_name,
        "food_name": food_name,
        "food_category": str(row.get("原因食品分类", "") or "").strip(),
        "venue": venue,
        "region": str(row.get("疾病暴发地区", "") or "").strip(),
        "occur_date": str(row.get("发生日期", "") or "").strip(),
        "case_count": _num(row.get("发病人数")),
        "exposed_count": _num(row.get("暴露人数")),
        "hospitalized": _num(row.get("住院人数")),
        "deaths": _num(row.get("死亡人数")),
        "symptoms": symptoms,
        "conclusion": str(row.get("报告结论", "") or "").strip(),
    }


def event_to_text(event):
    parts = []
    if event.get("agent_name"):
        parts.append("致病因素 " + event["agent_name"])
    if event.get("agent_category"):
        parts.append("分类 " + event["agent_category"])
    if event.get("food_name"):
        parts.append("食品 " + event["food_name"])
    if event.get("venue"):
        parts.append("场所 " + event["venue"])
    if event.get("region"):
        parts.append("地区 " + event["region"])
    if event.get("case_count"):
        parts.append(f"病例 {event['case_count']} 人")
    if event.get("symptoms"):
        parts.append("症状 " + "、".join(f"{k}{v}例" for k, v in sorted(event["symptoms"].items(), key=lambda x: -x[1])[:8]))
    if event.get("conclusion"):
        parts.append("结论 " + event["conclusion"])
    return "；".join(parts)


def load_xls_events(path):
    if not path or not os.path.exists(path):
        return []
    import xlrd
    wb = xlrd.open_workbook(path)
    sh = wb.sheet_by_index(0)
    hdr = [str(sh.cell_value(0, c)).strip() for c in range(sh.ncols)]
    events = []
    for r in range(1, sh.nrows):
        row = {hdr[c]: sh.cell_value(r, c) for c in range(sh.ncols)}
        events.append(normalize_row(row))
    return events
