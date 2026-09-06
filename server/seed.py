"""黄金演示事件：忠实复刻一份真实结案报告。

来源：corpus/reports/ 上海电力学院副溶血性弧菌食源性疾病暴发结案报告。
聚合数字（45/177=25.4%、症状占比、潜伏期 5–24h、副溶血阳性、凉拌豆芽交叉污染）
与报告一致；个案明细为确定性重建（非随机），可复现、可审计。
"""
from datetime import datetime, timedelta

EVENT_ID = "EV-DEMO-001"
ACTOR = "seed"

# (食品, 病例进食数, 未发病进食数)——未发病共 132，其中末 6 人为清真未食盒饭
FOODS = [
    ("红烧大排", 40, 118),
    ("盐水基围虾", 38, 112),
    ("熏鱼", 30, 88),
    ("毛豆茭白丁", 35, 104),
    ("凉拌金瓜丝", 28, 96),
    ("凉拌绿豆芽青椒丝", 36, 30),  # 元凶：豆芽检出副溶血
    ("米饭", 44, 128),
]


def _seed_people():
    people = []
    for i in range(45):  # 45 例病例：前 24 确诊（肛拭阳性）+ 21 疑似
        base = datetime(2018, 6, 29, 12, 0)
        # 幂次调整使潜伏期区间 5–24h、中位≈16h（对齐原始报告）
        onset = (base + timedelta(hours=5 + 19 * (i / 44) ** 0.789)).isoformat()
        people.append({
            "id": f"P{i + 1:03d}", "illness_status": "ill", "onset": onset,
            "age": 20 + i % 4, "sex": "男" if i < 26 else "女",
            "population": "电力学院师生", "location": "自动化仪表七厂",
            "symptoms": {
                "腹泻": True, "腹痛": i < 32, "恶心": i < 27,
                "呕吐": i < 22, "发热": i < 4,
            },
            "hospitalized": 1 if i % 6 == 0 else 0, "died": 0,
            "hospital": "杨浦区中心医院",
        })
    for j in range(132):  # 未发病
        people.append({
            "id": f"N{j + 1:03d}", "illness_status": "well", "onset": None,
            "age": 20 + j % 4, "sex": "女" if j % 2 == 0 else "男",
            "population": "电力学院师生", "location": "自动化仪表七厂",
            "symptoms": {},
        })
    return people


def _seed_exposures():
    exposures = []
    eid = 0
    for p in _seed_people():
        case_idx = int(p["id"][1:]) - 1 if p["id"].startswith("P") else None
        non_idx = int(p["id"][1:]) - 1 if p["id"].startswith("N") else None
        is_case = case_idx is not None
        for name, case_ate, non_ate in FOODS:
            if is_case:
                ate = 1 if case_idx < case_ate else 0
            elif non_idx >= 126:  # 末 6 名清真未食盒饭
                ate = 0
            else:
                ate = 1 if non_idx < non_ate else 0
            eid += 1
            exposures.append({
                "id": f"E{eid:04d}", "person_id": p["id"], "meal_id": "6月29日午餐",
                "meal_at": "2018-06-29T12:00:00", "food_id": name, "consumed": ate,
                "ate_at": "2018-06-29T12:00:00", "incubation_anchor": 1,
            })
    return exposures


def seed_demo_event(store):
    try:
        store.get_event(EVENT_ID)
        return None
    except ValueError:
        pass

    store.create_event(EVENT_ID, "上海电力学院副溶血性弧菌食源性疾病暴发", lead="崇明区疾控应急办", actor=ACTOR)
    store.update_event(EVENT_ID, {
        "place_type": "集体用餐配送单位", "region": "上海市崇明区",
        "address": "上海市自动化仪表有限公司七厂职工食堂",
        "occurred_at": "2018-06-29T17:00:00", "received_at": "2018-06-30T10:27:00",
        "exposure_at": "2018-06-29T12:00:00", "investigation_end": "2018-07-03T12:00:00",
        "is_foodborne": "yes", "source_place_type": "餐馆", "source_address": "崇明县欣宫饭店",
        "population_size": 177, "population_known": 1, "population_basis": "6月29日午餐177名就餐人员",
        "study_design": "cohort", "urgent_flags": ["聚集性呕吐腹泻"],
    }, ACTOR, "补充事件基本信息")

    store.set_definition(EVENT_ID, {
        "label": "疑似病例", "text": "6月29日12时聚餐后，24小时排便3次及以上且粪便性状异常，或腹泻伴发热、呕吐者",
        "start": "2018-06-29T12:00:00", "end": "2018-07-01T12:00:00",
        "locations": ["自动化仪表七厂"], "populations": ["电力学院师生"],
        "symptoms_any": ["腹泻"], "minimum_symptoms": 1,
        # 原始报告为二级判定（疑似/确诊），无「可能」档；probable 留空以忠实对齐
        "probable": {}, "confirmed": {"require_lab": True},
    }, ACTOR, "制定病例定义")

    store.upsert_people(EVENT_ID, _seed_people(), ACTOR, "个案调查")
    store.upsert_exposures(EVENT_ID, _seed_exposures(), ACTOR, "饮食史")
    store.upsert_foods(EVENT_ID, [
        {"id": name, "category": "蔬菜及蔬菜制品" if "凉拌" in name or "毛豆" in name
         else ("水产及水产制品" if "虾" in name or "鱼" in name
               else ("肉及肉制品" if "排" in name else "粮食及粮食制品")),
         "meal_id": "6月29日午餐", "source": "崇明县欣宫饭店"} for name, _, _ in FOODS
    ], ACTOR, "食品清单")

    samples = [{"id": "S-FOOD-1", "category": "food", "source": "凉拌绿豆芽青椒丝",
                "laboratory": "崇明区疾控", "collected_at": "2018-06-30T09:00:00",
                "tests": [{"item": "副溶血性弧菌", "result": "检出"}]},
               {"id": "S-ENV-1", "category": "environmental", "source": "环节样（36件）",
                "laboratory": "崇明区疾控", "tests": [{"item": "副溶血性弧菌", "result": "未检出"}]}]
    for i in range(24):  # 24 例确诊：肛拭副溶血阳性
        samples.append({"id": f"S-BIO-{i + 1:03d}", "category": "biological",
                        "person_id": f"P{i + 1:03d}", "source": "病例肛拭",
                        "laboratory": "杨浦区疾控", "collected_at": "2018-06-30T08:00:00",
                        "tests": [{"item": "副溶血性弧菌", "result": "检出"}]})
    store.upsert_samples(EVENT_ID, samples, ACTOR, "采样检验")

    store.add_hygiene(EVENT_ID, [
        {"id": "H1", "aspect": "加工过程", "item": "生熟分开", "finding": "容器具无明显生熟标记", "problem": 1},
        {"id": "H2", "aspect": "加工过程", "item": "餐具消毒", "finding": "洗碗间未配置消毒液", "problem": 1},
        {"id": "H3", "aspect": "运输", "item": "冷藏保温", "finding": "运输无冷藏和保温措施", "problem": 1},
        {"id": "H4", "aspect": "成品储存", "item": "温度控制", "finding": "当天最高气温34℃，未冷藏", "problem": 1},
        {"id": "H5", "aspect": "从业人员", "item": "健康证", "finding": "8人持有效健康证，近期无腹泻", "problem": 0},
    ], ACTOR, "食品卫生学调查")

    store.add_control(EVENT_ID, [
        {"id": "C1", "measure": "封存", "target": "欣宫饭店剩余食品", "implemented": "已封存",
         "date": "2018-06-30"},
        {"id": "C2", "measure": "卫生处理", "target": "加工场所与工用具", "implemented": "已消毒",
         "date": "2018-06-30"},
    ], ACTOR, "控制措施")

    store.add_evidence(EVENT_ID, {"id": "EVID-001", "title": "盒饭供应与就餐名单",
                                  "status": "已取得", "locator": "档案卷1", "text": "6月29日盒饭180份，就餐177人。"}, ACTOR, "登记名单")
    store.add_evidence(EVENT_ID, {"id": "EVID-002", "title": "食品样检验报告",
                                  "status": "已取得", "locator": "档案卷2", "text": "凉拌绿豆芽检出副溶血性弧菌。"}, ACTOR, "登记检验报告")
    store.add_evidence(EVENT_ID, {"id": "EVID-003", "title": "肛拭检验报告",
                                  "status": "已取得", "locator": "档案卷3", "text": "42件肛拭中29件检出副溶血性弧菌。"}, ACTOR, "登记检验报告")

    store.set_conclusion(EVENT_ID, "event_nature", {"status": "confirmed",
        "statement": "一起由副溶血性弧菌引起的食源性疾病暴发事件",
        "reason": "流调、卫生学、实验室三方结果相互支持。", "limitations": "未做剂量-反应分析。",
        "evidence_ids": ["EVID-002", "EVID-003"]}, ACTOR, "研判事件性质")
    store.set_conclusion(EVENT_ID, "scope", {"status": "confirmed",
        "statement": "符合病例定义45例（疑似21例、确诊24例），罹患率25.4%（45/177）",
        "reason": "病例搜索与个案调查汇总。", "limitations": "", "evidence_ids": ["EVID-001"]}, ACTOR, "研判范围")
    store.set_conclusion(EVENT_ID, "agent", {"status": "confirmed",
        "statement": "副溶血性弧菌", "reason": "食品样与24例肛拭均检出副溶血性弧菌，与临床表现及潜伏期相符。",
        "limitations": "", "evidence_ids": ["EVID-002", "EVID-003"]}, ACTOR, "研判致病因素")
    store.set_conclusion(EVENT_ID, "food", {"status": "confirmed",
        "statement": "凉拌绿豆芽青椒丝（凉拌菜）", "reason": "食品样检出副溶血性弧菌，病例进食率显著高于未发病者。",
        "limitations": "", "evidence_ids": ["EVID-002"]}, ACTOR, "研判原因食品")
    store.set_conclusion(EVENT_ID, "contamination", {"status": "confirmed",
        "statement": "交叉污染", "reason": "生熟不分、运输无冷藏保温、高温下长时间存放。",
        "limitations": "", "link": "生产加工", "factor": "交叉污染",
        "evidence_ids": ["EVID-002"]}, ACTOR, "研判污染环节")

    for stage in ("intake", "verify_dx", "case_def", "case_find", "individual",
                  "descriptive", "analytic", "food_hygiene", "sampling", "control",
                  "conclusion", "report"):
        store.set_stage(EVENT_ID, stage, "done", ACTOR, "演示：已按规范完成")

    return store.get_event(EVENT_ID)
