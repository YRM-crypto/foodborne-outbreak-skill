# 食源性疾病暴发调查助手

面向基层疾控流调人员的「以事件为中心」的暴发调查工作台。调查员接到一个事件后，把已有材料放进来，系统帮助**查依据、补资料、做分析、核证据、写报告**。目标不是大平台或聊天机器人，而是：**让经验不足的人少漏关键环节，让有经验的人少做重复劳动。**

> 核心产品问题：**「我手头已经有这些材料，接下来怎样把这次调查做得更完整、更有依据？」**

---

## 设计原则（对齐蚂蚁阿福）

参考蚂蚁阿福的 Agent 研发范式与产品设计，贯穿三条底线：

1. **确定性 vs 非确定性**：数值计算（罹患率、RR/OR、潜伏期、病程、Fisher 精确检验等）一律走 `core/` 确定性引擎；模型只做综合与表述，**不计算、不口算、不定性**。
2. **循证可追溯**：每个回答/结论锚定证据来源；append-only 审计日志记录「谁 / 何时 / 做了什么 / 依据哪份材料」，全程可核查。
3. **AI 只辅助**：13 个调查阶段 + 「AI 建议 + 人工确认」，模型**永不写回事实**、不替调查员下结论。

> 业务对齐《食品安全事故流行病学调查技术指南（2012 年版）》，以附表 1-8 为数据骨架、附表 1-9 为报告提纲。13 个调查阶段是「引导清单」而非强制门禁——**工作流并非单向**，任何环节都可补充新调查材料并随时重算。

---

## 架构总览

```
web/（React SPA）  ──HTTP/proxy──▶  server/（FastAPI REST）  ──▶  core/（确定性引擎）
                                     │
                                     ├──▶  poc/（LangGraph ReAct 智能体 + LightRAG 知识库，可选）
                                     │        └── LLM：Ollama（内网）或 DeepSeek（OpenAI 兼容，前期测试）
                                     └──▶  kb/（BM25/向量检索，可选知识库）
```

| 层 | 职责 | 目录 |
|---|---|---|
| **确定性核心** | SQLite 追加式审计存储、三级病例判定、派生指标重算、§7.1 校验、附表1-9 报告渲染。数值一律走这里，无网络依赖 | `core/` |
| **后端 REST** | 案例 CRUD + 录入 + 分析 + 报告 + 时间线 + 知识库检索 + AI 助手 | `server/` |
| **智能体 / 知识库** | ReAct 智能体（查依据/查相似案例/算指标）、LightRAG 双库（依据库/案例库），可选 | `poc/` |
| **前端** | 案例总览、13 阶段工作区、混合录入、分析可视化、报告、AI 助手 | `web/` |
| **检索** | BM25 + 向量检索（依据/案例库），可选 | `kb/` |

**数据流**：原始材料（个案/暴露/食品/样本/卫生学/控制措施/证据）构成「证据底座」→ `core` 确定性计算 → 派生视图（判定/症状谱/三间分布/潜伏期/四格表/结论/报告）**随时从当前证据重算** → 渲染为自然语言。自然语言是结构化事实与计算结果的「视图」，不是事实来源。

---

## 快速开始

### 前置条件

- Python 3.12 + [uv](https://docs.astral.sh/uv/)
- Node.js 18+ / npm
- Ollama（本地 LLM + Embedding，内网部署）**或** DeepSeek API key（前期测试）——仅 AI 助手需要

### 1. 启动后端（核心工作台无需 LLM）

```bash
uv run uvicorn server.main:app --reload --port 8000
```

### 2. 启动前端

```bash
cd web
npm install --registry=https://registry.npmmirror.com   # 国内镜像，快
npm run dev                                             # http://localhost:5173，/api 自动代理到 :8000
```

### 3. 生成演示数据

打开前端「案例总览」点 **「生成演示数据」**，或命令行：

```bash
uv run python scripts/seed_demo.py
```

生成一条完整演示事件（对齐真实结案报告「上海电力学院副溶血弧菌暴发」）：**177 名暴露（45 病例 = 24 确诊 + 21 疑似 + 132 未发病）**、流行曲线、潜伏期（中位 16h）、四格表（原因食品「凉拌绿豆芽」RR 6.73）、样本、卫生学、控制措施、结论与审计日志。

### 4.（可选）配置 AI 助手

复制 `poc/.env.example` 为 `poc/.env` 并填写 `LLM_*` / `EMBEDDING_*`；依据库/案例库首次需灌库（见 `poc/ingest.py`）。

---

## 已实现能力

| 能力 | 说明 |
|---|---|
| **13 阶段调查工作区** | 接报核实 / 病例确定 / 描述与分析 / 现场与检验 / 处置与结论 / 报告归档，六组 13 阶段引导清单；阶段状态仅记录完成度，不限制录入 |
| **病例三级判定** | 疑似（时间/地区/人群 + 症状）/ 可能（+ 流行病学关联）/ 确诊（+ 实验室阳性），随病例定义版本重判 |
| **混合录入** | 个案/暴露/食品/样本支持**表格批量粘贴（TSV）**，其余走**表单**；全部写入 append-only 审计 |
| **确定性分析** | 罹患率（Wilson CI）、流行曲线、三间分布、症状谱、潜伏期（min/median/max/mean）、食品关联（RR/OR + 95%CI + Fisher P）、个案判定 |
| **§7.1 校验** | 流调/卫生学/实验室三方面结论支持度 + 数据完整性校验（warn/info），随录入实时提示 |
| **证据与结论** | 五类结论（事件性质/范围/致病因素/原因食品/污染环节），污染环节 + 污染原因枚举 |
| **报告** | 初步/阶段/结案三档报告，按附表 1-9 提纲渲染 Markdown |
| **溯源审计** | 每次修改登记操作人/操作/说明，全程可核查 |
| **AI 助手** | 上下文感知问答 + 循证来源 + 「AI 已知上下文」透明展示（可选，需 LLM） |

---

## AI 助手（可选，Phase 4）

入口：左侧「AI 助手」，或工作区头部「问 AI」按钮（自动带入当前事件）。

- **上下文感知**：选择事件后，`POST /api/assistant/chat` 把该事件的确定性档案摘要（病例定义、判定统计、症状谱、暴露关联 RR/P、潜伏期、阶段、结论、样本）注入模型，模型据此针对「本次调查」作答。
- **循证来源**：回答下方列出检索到的依据来源（规范/致病因子/结案报告），可核查。
- **透明可核查**：顶部折叠「AI 已知上下文」，展示注入模型的事实，杜绝黑箱。
- **信任边界**：顶部常驻「AI 仅作辅助，最终结论请人工确认」；确定性指标用工具计算、不口算。

---

## API 一览

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/events` | 新建事件（编号/标题/负责人） |
| GET | `/api/events` | 事件列表 |
| GET/PATCH | `/api/events/{id}` | 读取 / 更新事件（场所类型/地区/时间/暴露人数/研究设计等） |
| GET | `/api/events/{id}/load` | 完整档案（定义/人员/暴露/食品/样本/卫生学/控制措施/证据/结论/阶段） |
| GET | `/api/events/{id}/timeline` | 审计时间线 |
| GET | `/api/events/{id}/analyze` | 确定性分析（流行曲线/三间分布/四格表/潜伏期） |
| GET | `/api/events/{id}/report?kind=` | 初步/阶段/结案报告 |
| PUT | `/api/events/{id}/definition` | 病例定义（版本化） |
| PUT | `/api/events/{id}/people\|exposures\|foods\|samples\|hygiene\|controls` | 录入原始材料 |
| POST | `/api/events/{id}/evidence\|conclusions\|stages` | 证据 / 结论 / 阶段状态 |
| POST | `/api/events/seed-demo` | 生成演示事件 |
| GET | `/api/kb/docs` `/api/kb/search` | 知识库浏览 / 检索（可选） |
| POST | `/api/assistant/chat` | 上下文感知问答 + 循证来源（可选） |

---

## 目录结构

```
core/                # 确定性：store(SQLite 审计) / classify / validate / analyze / report / constants
server/              # FastAPI：routers/(events|kb|assistant) + schemas + seed + assistant + config
web/                 # Vite + React + TS + AntD 前端（src/views/… + src/constants.ts 领域词汇表）
poc/                 # LangGraph ReAct 智能体 + LightRAG 知识库（可选）
kb/                  # BM25 / 向量检索 + ingest_xls（结构化监测数据导入知识库，可选）
scripts/             # seed_demo.py（演示事件）、extract_corpus.sh（抽取语料）
corpus/              # checklist.json / pathogen_ref.json / meta.json（进 git）
tests/               # 确定性 / 检索 / 路由 / 智能体测试
data/                # SQLite 运行时（不进 git）
assets/raw/          # 原始报告 + 规范 PDF（不进 git）
```

---

## 测试

```bash
uv run python -m pytest tests/ -q
```

覆盖确定性层（store/classify/validate/analyze/report）、检索（BM25/向量/xls 导入）、智能体脚手架、FastAPI 路由（TestClient）。当前 **52 passed, 1 skipped**。

---

## 数据与 git 边界

- **进 git**：代码、`corpus/` 中不涉敏的清单/参考表/版本元数据、`pyproject.toml`、`uv.lock`、`.gitignore`。
- **不进 git**（`.gitignore`）：`docs/`、`data/`、`assets/raw/`（真实报告 + 规范 PDF）、`corpus/standards/`、`corpus/reports/`、`poc/rag_data/`、`poc/.env`、`.venv/`。

---

## 范围外（v1 不做）

案例训练平台、多人协作、供应链可视化、高级统计（匹配/多因素）、病因自动定论、概率排行榜、大屏驾驶舱、自动报送正式监测系统。
