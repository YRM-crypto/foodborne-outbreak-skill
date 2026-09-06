"""按附表 1-9《食源性疾病暴发流行病学调查报告提纲》渲染 Markdown 报告。

正文与表格数字一律来自确定性计算结果，自然语言只是结构化事实的「视图」。
"""
from core.constants import CONCLUSION_STATUS, TOPIC_NAMES
from core.validate import validate

KIND_LABELS = {"initial": "初步调查报告", "progress": "阶段调查报告", "final": "流行病学结案报告"}


def _cell(v):
    return str(v if v is not None else "").replace("|", "／").replace("\n", " ")


def _table(headers, rows):
    return (["| " + " | ".join(map(_cell, headers)) + " |",
             "| " + " | ".join("---" for _ in headers) + " |"]
            + ["| " + " | ".join(map(_cell, r)) + " |" for r in rows])


def _pct(v):
    return f"{v * 100:.1f}%" if v is not None else "—"


def _conclusion(state, topic):
    return next((c for c in state["conclusions"] if c["topic"] == topic), None)


def _title(state):
    """标题三要素：发生场所 + 原因食品 + 致病因子。"""
    event = state["event"]
    food = (_conclusion(state, "food") or {}).get("statement", "")
    agent = (_conclusion(state, "agent") or {}).get("statement", "")
    place = event.get("place_type") or event.get("region") or ""
    if food or agent:
        return f"关于{place}{food}（{agent}）食源性疾病暴发的流行病学调查报告"
    return event.get("title", "食源性疾病暴发流行病学调查报告")


def render_markdown(state, stats, kind, checks=None):
    event = state["event"]
    d = state["definition"]
    kind_label = KIND_LABELS[kind]
    checks = checks if checks is not None else validate(state, stats)
    lines = [f"# {_title(state)}", "", f"（{kind_label}）", "",
             f"事件编号：{event['id']}；资料截止：{event.get('investigation_end') or '待明确'}。", ""]

    # 一、背景与概述
    lines += ["## 一、背景与概述", ""]
    lines.append(f"发生场所：{event.get('place_type') or '待明确'}；地区：{event.get('region') or '待明确'}。"
                 f"接报日期 {event.get('received_at') or '待明确'}，发生日期 {event.get('occurred_at') or '待明确'}。")
    pop = stats["population"]
    if pop["known"]:
        lines.append(f"暴露人数 {pop['size']}，界定：{pop.get('basis') or '未说明'}；"
                     f"罹患率 {_pct(stats['attack_rate']['value'])}（{stats['attack_rate']['numerator']}/{stats['attack_rate']['denominator']}）。")
    else:
        lines.append("暴露人数尚未确定（研究设计为病例对照，使用 OR）。")
    lines.append("")

    # 二、基本情况
    lines += ["## 二、基本情况", ""]
    lines.append(f"地点/单位：{event.get('address') or event.get('region') or '待明确'}。"
                 f"跨区域：{'是' if event.get('cross_region') else '否'}。")
    if event.get("source_place_type") or event.get("source_address"):
        lines.append(f"原因食品来源：{event.get('source_place_type') or ''} {event.get('source_address') or ''}。")
    lines.append("")

    # 三、病例定义
    lines += ["## 三、病例定义", ""]
    if d:
        lines.append(f"病例定义（第 {d.get('version', 1)} 版）：{d.get('text') or d.get('label') or '（未填写文字）'}")
        lines.append(f"时间范围 {d.get('start') or '?'} 至 {d.get('end') or '?'}；"
                     f"地区 {('、'.join(d.get('locations') or []) or '不限')}；"
                     f"人群 {('、'.join(d.get('populations') or []) or '不限')}。")
        lines.append(f"疑似：{('、'.join(d.get('symptoms_any') or []) or '未定')}"
                     f" 中至少 {d.get('minimum_symptoms', 1)} 项；"
                     f"可能：与确诊病例有共同暴露；确诊：符合病例定义且致病因子检验阳性。")
    else:
        lines.append("尚未制定病例定义。")
    lines.append("")

    # 四、病例搜索与个案
    lines += ["## 四、病例搜索与个案调查", ""]
    lines.append(f"登记 {sum(stats['counts'].values())} 人："
                 f"确诊 {stats['counts'].get('确诊', 0)}、可能 {stats['counts'].get('可能', 0)}、"
                 f"疑似 {stats['counts'].get('疑似', 0)}、未发病 {stats['counts'].get('未发病', 0)}、"
                 f"排除 {stats['counts'].get('排除', 0)}、待定 {stats['counts'].get('待定', 0)}。")
    lines.append("")

    # 五、临床表现
    lines += ["## 五、临床表现", ""]
    if stats["symptoms"]:
        lines += _table(["症状/体征", "人数", "比例", "未知"],
                        [[r["symptom"], r["numerator"], _pct(r["value"]), r["unknown"]]
                         for r in stats["symptoms"]]) + [""]
    else:
        lines += ["现有资料不足以统计临床表现。", ""]

    # 六、三间分布
    lines += ["## 六、三间分布", ""]
    if stats["by_date"]:
        lines += ["**时间分布**"] + _table(["起病日期", "病例数"], list(stats["by_date"].items())) + [""]
    if stats["age_groups"]:
        lines += ["**人群分布（年龄段）**"]
        lines += _table(["年龄段", "发病人数", "住院", "死亡"],
                        [[g["label"], g["cases"], g["hospitalized"], g["died"]]
                         for g in stats["age_groups"]]) + [""]
    if stats["by_sex"]:
        lines += ["**性别分布**"] + _table(["性别", "病例数"], list(stats["by_sex"].items())) + [""]
    if stats["by_location"]:
        lines += ["**地区/地点分布**"] + _table(["地点", "病例数"], list(stats["by_location"].items())) + [""]
    r = stats["incubation"]
    if r["n"]:
        lines += [f"潜伏期：可计算 {r['n']} 人，最短 {r['minimum']:.1f} 小时、最长 {r['maximum']:.1f} 小时、"
                  f"中位 {r['median']:.1f} 小时。", ""]
    r = stats["duration"]
    if r["n"]:
        lines += [f"病程：可计算 {r['n']} 人，最短 {r['minimum']:.1f} 小时、最长 {r['maximum']:.1f} 小时、"
                  f"中位 {r['median']:.1f} 小时。", ""]

    # 七、食品卫生学调查
    lines += ["## 七、食品卫生学调查", ""]
    if state["hygiene"]:
        lines += _table(["环节", "检查项", "检查所见", "风险"],
                        [[h.get("aspect", ""), h.get("item", ""), h.get("finding", ""),
                          "是" if h.get("problem") else ""] for h in state["hygiene"]]) + [""]
    else:
        lines += ["尚未录入食品卫生学调查记录。", ""]

    # 八、实验室检验
    lines += ["## 八、实验室检验", ""]
    if state["samples"]:
        rows = []
        for s in state["samples"]:
            tests = "；".join(f"{t.get('item','')} {t.get('result','')}" for t in (s.get("tests") or []))
            rows.append([s.get("category", ""), s.get("source", ""), s.get("laboratory", ""), tests])
        lines += _table(["类别", "标本来源", "实验室", "检测项目与结果"], rows) + [""]
    else:
        lines += ["尚未录入采样检验记录。", ""]

    # 九、关联分析与结论
    lines += ["## 九、结果分析与调查结论", ""]
    if stats["associations"]:
        lines += _table(["食品", "效应", "RR/OR", "95%CI", "Fisher P"],
                        [[a["food_id"], a.get("measure", ""),
                          f"{a.get('effect'):.2f}" if a.get("effect") else "—",
                          "–".join(f"{x:.2f}" for x in a["ci95"]) if a.get("ci95") else "—",
                          f"{a.get('p_fisher_two_sided'):.4g}" if a.get("p_fisher_two_sided") is not None else "—"]
                         for a in stats["associations"]]) + [""]
    for topic in ("event_nature", "scope", "agent", "food", "contamination"):
        c = _conclusion(state, topic)
        if c:
            lines.append(f"**{TOPIC_NAMES[topic]}**（{CONCLUSION_STATUS.get(c['status'], c['status'])}）：{c['statement']}")
            if c.get("reason"):
                lines.append(f"　依据：{c['reason']}")
            if c.get("limitations"):
                lines.append(f"　局限：{c['limitations']}")
            if topic == "contamination" and (c.get("link") or c.get("factor")):
                lines.append(f"　环节：{c.get('link') or '未定'}；因素：{c.get('factor') or '未定'}")
            lines.append("")
        else:
            lines.append(f"**{TOPIC_NAMES[topic]}**：尚待综合研判。")

    # 十、控制措施与建议
    lines += ["## 十、控制措施与建议", ""]
    if state["controls"]:
        lines += _table(["措施", "对象", "落实情况", "日期"],
                        [[c.get("measure", ""), c.get("target", ""), c.get("implemented", ""), c.get("date", "")]
                         for c in state["controls"]]) + [""]
    else:
        lines += ["尚未录入控制措施。", ""]

    # 问题与不足（校验结果）
    warns = [c for c in checks if c["level"] in ("warn", "error")]
    if warns:
        lines += ["## 问题与待核实", ""]
        for c in warns:
            lines.append(f"- {c['title']}：{c['detail']}")
        lines.append("")

    # 附件
    lines += ["## 附件目录", ""]
    if state["evidence"]:
        lines += _table(["材料编号", "名称", "取得状态", "定位"],
                        [[e["id"], e["title"], e["status"], e.get("locator") or e.get("uri") or "档案内文本"]
                         for e in state["evidence"]]) + [""]
    else:
        lines += ["尚未录入材料。", ""]
    return "\n".join(lines)
