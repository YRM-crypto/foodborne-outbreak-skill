"""从结构化事实与计算结果渲染 Markdown；自然语言锚定证据来源，非事实来源。"""
TOPICS = ("event_nature", "scope", "agent", "food", "contamination")
TOPIC_NAMES = {"event_nature": "事件性质", "scope": "范围与病例数", "agent": "致病因素",
               "food": "原因食品", "contamination": "污染环节与原因"}
STATUS_LABELS = {"hypothesis": "待验证假设", "supported": "有证据支持的意见",
                 "undetermined": "尚不能判定", "excluded": "排除意见"}


def _cell(v):
    return str(v).replace("|", "／").replace("\n", " ")


def _table(headers, rows):
    return (["| " + " | ".join(map(_cell, headers)) + " |",
             "| " + " | ".join("---" for _ in headers) + " |"]
            + ["| " + " | ".join(map(_cell, r)) + " |" for r in rows])


def render_markdown(state, stats, kind):
    event = state["event"]
    kind_label = {"initial": "初步调查报告", "progress": "阶段调查报告", "final": "流行病学结案报告"}[kind]
    c = stats["counts"]
    lines = [f"# {event['title']} {kind_label}", "",
             f"事件编号：{event['id']}。资料截止：{event.get('data_cutoff') or '待明确'}。", ""]
    lines += ["## 事件概况", "",
              f"当前登记 {sum(c.values())} 人，符合调查病例定义 {c.get('case', 0)} 人，"
              f"明确未发病 {c.get('noncase', 0)} 人，待核实 {c.get('pending', 0)} 人，"
              f"定义范围外或不符合 {c.get('excluded', 0)} 人。", ""]
    if state["definition"]:
        d = state["definition"]
        lines += [f"病例定义（第 {d.get('version')} 版）：{d.get('text')}",
                  f"时间 {d.get('start')} 至 {d.get('end')}；症状阈值 {d.get('minimum_symptoms')}。", ""]
    lines += ["## 临床表现", ""]
    if stats["symptoms"]:
        lines += _table(["症状/体征", "人数", "已知状态人数", "比例", "未知"],
                        [[r["symptom"], r["numerator"], r["denominator"],
                          f"{100 * r['value']:.2f}%" if r["value"] is not None else "未计算", r["unknown"]]
                         for r in stats["symptoms"]]) + [""]
    lines += ["## 三间分布", ""]
    for field, label in (("by_date", "起病日期"), ("by_location", "地区/地点"),
                         ("by_age", "年龄组"), ("by_sex", "性别")):
        lines += _table([label, "病例数"], list(stats[field].items())) + [""]
    for field, label in (("incubation", "潜伏期"), ("duration", "病程")):
        r = stats[field]
        if not r["n"]:
            lines += [f"现有资料不足以计算{label}。", ""]
        else:
            lines += [f"{label}可计算 {r['n']} 人，中位数 {r['median']:.1f} 小时，"
                      f"范围 {r['minimum']:.1f} 至 {r['maximum']:.1f} 小时。", ""]
    if stats["associations"]:
        lines += ["## 餐次与食品关联分析", ""]
        for r in stats["associations"]:
            lines += [f"餐次 {r['meal_id']}，食品 {r['food_id']}：",
                      *_table(["暴露", "病例", "未发病"], [["进食", *r["table"][0]], ["未进食", *r["table"][1]]]),
                      f"{r.get('measure', '效应量')}={r.get('effect')}；双侧 Fisher P={r.get('p_fisher_two_sided')}。", ""]
        lines += ["上述比较反映统计关联，尚需结合人群选择与混杂解释。", ""]
    lines += ["## 调查结论", ""]
    for topic in TOPICS:
        row = next((x for x in state["conclusions"] if x["topic"] == topic), None)
        if row:
            lines += [f"**{TOPIC_NAMES[topic]}**（{STATUS_LABELS.get(row['status'], row['status'])}）：{row['statement']}",
                      f"依据与理由：{row['reason']}。局限：{row['limitations']}。"
                      f"引用材料：{'、'.join(row.get('evidence_ids') or []) or '尚未关联'}。", ""]
        else:
            lines += [f"{TOPIC_NAMES[topic]}：尚待综合研判。", ""]
    lines += ["## 附件目录", ""]
    lines += _table(["材料编号", "名称", "取得状态", "定位"],
                    [[e["id"], e["title"], e["status"], e.get("locator") or e.get("uri") or "档案内文本"]
                     for e in state["evidence"]]) + [""]
    if not state["evidence"]:
        lines += ["尚未录入材料。", ""]
    return "\n".join(lines)
