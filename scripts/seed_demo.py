"""生成演示事件（病例定义、人员、暴露、样本、证据、结论、流程确认）。

首次打开工作台时运行一次，即可在「案例总览 → 调查工作区」看到完整的
流行曲线、三间分布、四格表、证据与审计日志，便于演示与上手。

用法：  uv run python scripts/seed_demo.py
"""
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.store import Store
from server.config import STORE_PATH

EVENT_ID = "EV-DEMO-001"
ACTOR = "seed"


def _symptom(i):
    return {
        "呕吐": True,
        "腹泻": i % 3 == 0,
        "腹痛": i % 2 == 0,
        "发热": i % 7 == 0,
    }


def main():
    store = Store(STORE_PATH)
    try:
        store.get_event(EVENT_ID)
        print(f"事件 {EVENT_ID} 已存在，跳过。如需重建请先删除 {STORE_PATH}")
        return
    except ValueError:
        pass

    store.create_event(EVENT_ID, "某学校食堂聚集性呕吐", "closed-cohort", lead="调查一组", actor=ACTOR)
    store.update_event(EVENT_ID, {
        "received_at": "2024-01-05T09:00:00", "location": "某中学食堂",
        "data_cutoff": "2024-01-06T18:00:00", "population_size": 40,
        "population_complete": 1, "population_basis": "全体就餐学生",
        "urgent_flags": ["聚集性呕吐"],
    }, ACTOR, "补充事件基本信息")

    store.set_definition(EVENT_ID, {
        "label": "餐后呕吐者", "text": "2024-01-02 至 01-05 期间，在某中学食堂就餐后出现呕吐者",
        "start": "2024-01-01T00:00:00", "end": "2024-01-06T23:59:59",
        "locations": [], "populations": [], "symptoms_any": ["呕吐"],
        "minimum_symptoms": 1, "require_lab": 0, "evidence_ids": [],
    }, ACTOR, "设定病例定义")

    # 28 病例 + 12 未发病
    people = []
    case_onsets = ([(2, 8), (3, 14), (4, 6)])
    idx = 0
    for day, count in case_onsets:
        for k in range(count):
            onset = f"2024-01-0{day}T{10 + (k % 10):02d}:00:00"
            people.append({
                "id": f"P{idx + 1:03d}", "illness_status": "ill", "onset": onset,
                "sex": "男" if idx % 2 == 0 else "女", "age": 15 + (idx % 4),
                "location": "某中学", "symptoms": _symptom(idx),
                "hospitalized": 1 if idx % 5 == 0 else 0, "died": 0,
            })
            idx += 1
    for k in range(12):
        people.append({
            "id": f"N{k + 1:03d}", "illness_status": "well",
            "sex": "女" if k % 2 == 0 else "男", "age": 16 + (k % 3),
            "location": "某中学", "symptoms": {},
        })
    store.upsert_people(EVENT_ID, people, ACTOR, "录入调查名单")

    # 暴露：病例多进食凉拌菜，对照少进食；米饭为共同食品
    exposures = []
    for i, p in enumerate(people):
        is_case = p["illness_status"] == "ill"
        # 凉拌菜（可疑食品）：病例几乎都吃、对照几乎不吃，但保留交叉以构成四格表
        liang_ate = (0 if i % 14 == 0 else 1) if is_case else (1 if i % 6 == 0 else 0)
        # 米饭（无关食品）：两组进食比例接近
        rice_ate = 1 if i % 5 != 0 else 0
        exposures.append({
            "id": f"E{i + 1:03d}", "person_id": p["id"], "meal_id": "午餐",
            "food_id": "凉拌菜", "consumed": liang_ate,
            "ate_at": "2024-01-01T12:00:00", "incubation_anchor": 1,
        })
        exposures.append({
            "id": f"E{i + 1:03d}b", "person_id": p["id"], "meal_id": "午餐",
            "food_id": "米饭", "consumed": rice_ate, "ate_at": "2024-01-01T12:00:00",
        })
    store.upsert_exposures(EVENT_ID, exposures, ACTOR, "录入暴露史")

    store.upsert_samples(EVENT_ID, [
        {"id": "S001", "kind": "粪便", "person_id": "P001", "source": "病例", "laboratory": "区疾控", "tests": [{"item": "沙门氏菌", "result": "未检出"}]},
        {"id": "S002", "kind": "食品", "person_id": None, "source": "凉拌菜留样", "laboratory": "区疾控", "tests": [{"item": "金黄色葡萄球菌", "result": "检出"}]},
    ], ACTOR, "录入样本")

    store.add_evidence(EVENT_ID, {
        "id": "EVID-001", "title": "就餐名单与座位表", "status": "已核验", "locator": "档案卷1",
        "text": "当日午餐 40 人就餐名单。",
    }, ACTOR, "登记就餐名单")
    store.add_evidence(EVENT_ID, {
        "id": "EVID-002", "title": "凉拌菜留样检验报告", "status": "已取得", "locator": "档案卷2",
        "text": "检出金黄色葡萄球菌。",
    }, ACTOR, "登记检验报告")

    store.set_conclusion(EVENT_ID, "event_nature", {
        "status": "supported", "statement": "一起金黄色葡萄球菌肠毒素引起的点源暴发",
        "reason": "潜伏期集中在 24 小时左右，症状以呕吐为主，留样检出金葡菌。",
        "limitations": "未做肠毒素定量。", "evidence_ids": ["EVID-001", "EVID-002"],
    }, ACTOR, "研判事件性质")
    store.set_conclusion(EVENT_ID, "food", {
        "status": "supported", "statement": "可疑食品为凉拌菜",
        "reason": "病例进食率显著高于对照，留样阳性。", "limitations": "需结合剂量-反应。",
        "evidence_ids": ["EVID-002"],
    }, ACTOR, "研判原因食品")

    for node in ("intake", "definition", "plan", "analysis", "evidence"):
        store.confirm(EVENT_ID, node, ACTOR, "调查员", "演示流程确认", [], "confirmed")

    print("已生成演示事件：")
    for row in store.list_events():
        if row["id"] == EVENT_ID:
            print(f"  {row['id']} · {row['title']} · 修订 {row['revision']}")
    print("打开前端「案例总览」即可进入工作区查看可视化。")
    store.close()


if __name__ == "__main__":
    main()
