"""领域词汇表：对齐《食品安全事故流行病学调查技术指南（2012 年版）》与
《食源性疾病暴发事件监测信息表》（附表 1-8）。

只放常量与枚举，不做计算。作为 core 确定性层与前端/服务端的共同约定。
"""

# —— 场所类型（附表 1-8 填表说明 §1.1–1.11）——
PLACE_TYPES = [
    "学校食堂", "单位食堂", "餐馆", "农村宴席", "街头摊点",
    "集体用餐配送单位", "社会用餐配送单位", "中央厨房", "校园", "门店",
]

# —— 症状清单（附表 1-8 四 核心子集 + 其他）——
SYMPTOMS = [
    "恶心", "呕吐", "腹泻", "腹痛", "发热", "头痛", "头晕", "乏力",
    "里急后重", "发绀", "抽搐", "呼吸困难", "视觉模糊", "皮疹",
]

# —— 年龄段（附表 1-8 三：<1 / 1–6 / 7–19 / 20–59 / 60+）——
# (lo, hi, label)，lo 含、hi 不含；None 表示无下/上界。
AGE_GROUPS = [
    (None, 1, "<1岁"),
    (1, 7, "1–6岁"),
    (7, 20, "7–19岁"),
    (20, 60, "20–59岁"),
    (60, None, "60岁以上"),
]


def age_group(age):
    """把实际年龄映射到附表 1-8 年龄段标签；未知返回 None。"""
    if age is None or (isinstance(age, float) and age != age):  # NaN 保护
        return None
    for lo, hi, label in AGE_GROUPS:
        if (lo is None or age >= lo) and (hi is None or age < hi):
            return label
    return None


# —— 病例三级（S2012 §4.2）与判定状态 ——
CASE_TIERS = ["疑似", "可能", "确诊"]

# classify() 输出的判定状态（含非病例/排除/待定）
CLASS_STATUSES = ["确诊", "可能", "疑似", "未发病", "排除", "待定"]


# —— 研究设计（S2012 §4.6：暴露人群确定→队列 RR；不确定→病例对照 OR）——
STUDY_DESIGNS = {"cohort": "队列研究（RR）", "case-control": "病例对照（OR）"}


# —— 13 阶段（S2012，group 用于前端 6 组视觉分组）——
STAGES = [
    {"id": "intake", "name": "接报与核实", "group": "接报核实", "table": "接报记录"},
    {"id": "verify_dx", "name": "核实诊断", "group": "接报核实", "table": "附表3-1 病例访谈提纲"},
    {"id": "case_def", "name": "病例定义", "group": "病例确定", "table": "病例定义记录"},
    {"id": "case_find", "name": "病例搜索", "group": "病例确定", "table": "附表3-2 临床信息一览表"},
    {"id": "individual", "name": "个案调查", "group": "病例确定", "table": "附表3-4/3-5/3-6 个案调查表"},
    {"id": "descriptive", "name": "描述性分析", "group": "描述与分析", "table": "附表3-8 信息整理表"},
    {"id": "analytic", "name": "分析性研究", "group": "描述与分析", "table": "回顾性队列/病例对照分析表"},
    {"id": "food_hygiene", "name": "食品卫生学调查", "group": "现场与检验", "table": "采样记录表"},
    {"id": "sampling", "name": "采样检验", "group": "现场与检验", "table": "附表3-7 采样记录表"},
    {"id": "control", "name": "控制措施", "group": "处置与结论", "table": "措施记录"},
    {"id": "conclusion", "name": "调查结论", "group": "处置与结论", "table": "结论记录"},
    {"id": "report", "name": "报告", "group": "报告归档", "table": "附表3-9 报告提纲"},
    {"id": "archive", "name": "结案归档", "group": "报告归档", "table": "归档清单"},
]

STAGE_IDS = [s["id"] for s in STAGES]
STAGE_BY_ID = {s["id"]: s for s in STAGES}
STAGE_GROUPS = ["接报核实", "病例确定", "描述与分析", "现场与检验", "处置与结论", "报告归档"]


# —— 结论主题（S2012 §7.1 / 附表 1-8 十）——
CONCLUSION_TOPICS = ["event_nature", "scope", "agent", "food", "contamination"]
TOPIC_NAMES = {
    "event_nature": "事件性质",
    "scope": "范围与病例数",
    "agent": "致病因素",
    "food": "原因食品",
    "contamination": "污染环节与原因",
}
CONCLUSION_STATUS = {
    "confirmed": "确定",
    "probable": "可能",
    "unknown": "尚不能判定",
    "excluded": "排除",
}


# —— 污染环节 × 因素（附表 1-8 十 枚举）——
CONTAMINATION_LINKS = ["种养殖", "生产加工", "流通（运输和销售）", "其他"]
CONTAMINATION_FACTORS = [
    "原料（辅料）污染或变质", "加工不当", "存储不当", "误食误用", "交叉污染",
    "投入品滥用或超范围使用", "非法使用", "环境污染", "添加剂滥用或非法添加",
    "产品过期（变质）", "人员污染", "设备（操作用具、器皿等）污染",
    "原因不明", "投毒", "其他",
]


# —— 食品分类（附表 1-8 填表说明 §3.1）——
FOOD_CATEGORIES = [
    "肉及肉制品", "水产及水产制品", "蛋及蛋制品", "乳及乳制品",
    "粮食及粮食制品", "蔬菜及蔬菜制品", "水果及水果制品",
    "豆及豆制品", "饮料及冷冻饮品", "糕点及饼干", "调味品", "混合食品", "其他",
]


# —— 样品类别（附表 1-8 七/八/九）——
SAMPLE_CATEGORIES = {"food": "食品样", "biological": "生物标本", "environmental": "环境标本"}


# —— 控制措施（S2012 §3.3.2 / 判定指南 §5）——
CONTROL_MEASURES = ["停售", "封存", "召回", "无害化处理", "卫生处理", "调离从业人员", "其他"]


# —— 卫生学调查重点环节（S2012 §5.1.3）——
HYGIENE_ASPECTS = ["现场检查", "原料", "配方", "加工用水", "加工过程", "成品储存", "运输", "从业人员"]
