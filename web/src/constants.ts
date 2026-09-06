// 领域词汇表：镜像 core/constants.py（S2012 / 附表 1-8 的枚举常量）。
// 与后端保持单一事实来源；如后端常量变更，需同步此处。

export const PLACE_TYPES = [
  "学校食堂", "单位食堂", "餐馆", "农村宴席", "街头摊点",
  "集体用餐配送单位", "社会用餐配送单位", "中央厨房", "校园", "门店",
];

export const SYMPTOMS = [
  "恶心", "呕吐", "腹泻", "腹痛", "发热", "头痛", "头晕", "乏力",
  "里急后重", "发绀", "抽搐", "呼吸困难", "视觉模糊", "皮疹",
];

export const CLASS_STATUSES = ["确诊", "可能", "疑似", "未发病", "排除", "待定"];

export const STUDY_DESIGNS: Record<string, string> = {
  cohort: "队列研究（RR）",
  "case-control": "病例对照（OR）",
};

export interface Stage {
  id: string;
  name: string;
  group: string;
  table: string;
}

export const STAGES: Stage[] = [
  { id: "intake", name: "接报与核实", group: "接报核实", table: "接报记录" },
  { id: "verify_dx", name: "核实诊断", group: "接报核实", table: "附表3-1 病例访谈提纲" },
  { id: "case_def", name: "病例定义", group: "病例确定", table: "病例定义记录" },
  { id: "case_find", name: "病例搜索", group: "病例确定", table: "附表3-2 临床信息一览表" },
  { id: "individual", name: "个案调查", group: "病例确定", table: "附表3-4/3-5/3-6 个案调查表" },
  { id: "descriptive", name: "描述性分析", group: "描述与分析", table: "附表3-8 信息整理表" },
  { id: "analytic", name: "分析性研究", group: "描述与分析", table: "回顾性队列/病例对照分析表" },
  { id: "food_hygiene", name: "食品卫生学调查", group: "现场与检验", table: "采样记录表" },
  { id: "sampling", name: "采样检验", group: "现场与检验", table: "附表3-7 采样记录表" },
  { id: "control", name: "控制措施", group: "处置与结论", table: "措施记录" },
  { id: "conclusion", name: "调查结论", group: "处置与结论", table: "结论记录" },
  { id: "report", name: "报告", group: "报告归档", table: "附表3-9 报告提纲" },
  { id: "archive", name: "结案归档", group: "报告归档", table: "归档清单" },
];

export const STAGE_GROUPS = ["接报核实", "病例确定", "描述与分析", "现场与检验", "处置与结论", "报告归档"];

export const STAGE_STATUS_LABEL: Record<string, string> = {
  pending: "待办",
  in_progress: "进行中",
  done: "已完成",
  na: "不适用",
};

export const CONCLUSION_TOPICS: { key: string; name: string }[] = [
  { key: "event_nature", name: "事件性质" },
  { key: "scope", name: "范围与病例数" },
  { key: "agent", name: "致病因素" },
  { key: "food", name: "原因食品" },
  { key: "contamination", name: "污染环节与原因" },
];

export const CONCLUSION_STATUS: Record<string, string> = {
  confirmed: "确定",
  probable: "可能",
  unknown: "尚不能判定",
  excluded: "排除",
};

export const CONTAMINATION_LINKS = ["种养殖", "生产加工", "流通（运输和销售）", "其他"];

export const CONTAMINATION_FACTORS = [
  "原料（辅料）污染或变质", "加工不当", "存储不当", "误食误用", "交叉污染",
  "投入品滥用或超范围使用", "非法使用", "环境污染", "添加剂滥用或非法添加",
  "产品过期（变质）", "人员污染", "设备（操作用具、器皿等）污染",
  "原因不明", "投毒", "其他",
];

export const FOOD_CATEGORIES = [
  "肉及肉制品", "水产及水产制品", "蛋及蛋制品", "乳及乳制品",
  "粮食及粮食制品", "蔬菜及蔬菜制品", "水果及水果制品",
  "豆及豆制品", "饮料及冷冻饮品", "糕点及饼干", "调味品", "混合食品", "其他",
];

export const SAMPLE_CATEGORIES: Record<string, string> = {
  food: "食品样",
  biological: "生物标本",
  environmental: "环境标本",
};

export const CONTROL_MEASURES = ["停售", "封存", "召回", "无害化处理", "卫生处理", "调离从业人员", "其他"];

export const HYGIENE_ASPECTS = ["现场检查", "原料", "配方", "加工用水", "加工过程", "成品储存", "运输", "从业人员"];
