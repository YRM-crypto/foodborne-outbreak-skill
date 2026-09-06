# 食源性疾病暴发调查助手

面向基层疾控流调人员的「以事件为中心」的暴发调查工作台。调查员接到一个事件后，把已有材料放进来，系统帮助**查依据、补资料、做分析、核证据、写报告**。目标不是大平台或聊天机器人，而是：**让经验不足的人少漏关键环节，让有经验的人少做重复劳动。**

> 核心产品问题：**「我手头已经有这些材料，接下来怎样把这次调查做得更完整、更有依据？」**

---

## 设计原则（对齐蚂蚁阿福）

参考蚂蚁阿福的 Agent 研发范式与产品设计，贯穿三条底线：

1. **确定性 vs 非确定性**：数值计算（罹患率、RR/OR、潜伏期、病程、Fisher 精确检验等）一律走 `core/` 确定性引擎；模型只做综合与表述，**不计算、不口算、不定性**。
2. **循证可追溯**：每个回答/结论锚定证据来源；append-only 审计日志记录「谁 / 何时 / 做了什么 / 依据哪份材料」，全程可核查。
3. **AI 只辅助**：7 个流程节点 + 「AI 建议 + 人工确认」，模型**永不写回事实**、不替调查员下结论。

---

## 已实现能力（四个阶段）

| 阶段 | 能力 | 落地 |
|---|---|---|
| **1 后端领域 API** | 案例 CRUD、确定性分析、报告、时间线 | `server/`（FastAPI + Pydantic） |
| **2 前端骨架 + 知识库** | 案例总览、知识库浏览/独立检索 | `web/`（Vite + React + TS + AntD）+ LightRAG |
| **3 调查工作区** | 流程视图、数据可视化、证据/结论 CRUD、审计溯源 | `web/src/views/workspace/` |
| **4 AI 助手 + 阿福式打磨** | 上下文感知对话、循证来源、下一步引导、上手引导 | `server/assistant.py` + `web/src/views/AssistantView.tsx` |

---

## 架构总览

```
web/（React SPA）  ──HTTP/proxy──▶  server/（FastAPI REST）  ──▶  core/（确定性：SQLite + 统计 + 分类 + 报告）
                                     │
                                     ├──▶  poc/（LangGraph ReAct 智能体 + LightRAG 知识库）
                                     │        └── LLM：Ollama（内网）或 DeepSeek（OpenAI 兼容，前期测试）
                                     │        └── Embedding：Ollama bge-m3
                                     └──▶  kb/ingest_xls（500 条结构化监测数据导入）
```

| 层 | 职责 | 目录 |
|---|---|---|
| **确定性计算** | SQLite 追加式审计存储、统计、病例三级判定、报告渲染。数值一律走这里，无网络依赖 | `core/` |
| **后端 REST** | 案例 CRUD + 分析 + 报告 + 时间线 + 知识库检索 + AI 助手 | `server/` |
| **智能体 / 知识库** | ReAct 智能体（查依据/查相似案例/算指标）、LightRAG 双库（依据库/案例库） | `poc/` |
| **前端** | 案例总览、知识库、调查工作区、报告、AI 助手 | `web/` |
| **数据导入** | 500 条 xls 监测数据 → 结构化事件文本 | `kb/ingest_xls.py` |

**数据流**：确定性表单录入 → `core` 确定性计算 → 结果渲染为自然语言（报告/问答/待办）。自然语言是结构化事实与计算结果的「视图」，不是事实来源。

---

## 快速开始

### 前置条件

- Python 3.12 + [uv](https://docs.astral.sh/uv/)
- Node.js 18+ / npm
- Ollama（本地 LLM + Embedding，内网部署）**或** DeepSeek API key（前期测试）

### 1. 配置 LLM / Embedding

复制 `poc/.env.example` 为 `poc/.env` 并按需填写：

```bash
LLM_PROVIDER=ollama            # ollama（本地）| openai（DeepSeek 等）
LLM_MODEL=qwen3:30b...         # 或 deepseek-chat
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_API_KEY=sk-...
EMBEDDING_PROVIDER=ollama      # 默认 bge-m3
EMBEDDING_MODEL=bge-m3:latest
```

> 依据库/案例库向量与图谱在 `poc/rag_data/`（首次需灌库，见 `poc/ingest.py`）。

### 2. 启动后端

```bash
uv run uvicorn server.main:app --reload --port 8000
```

（可选）若需对接 Open WebUI，另起智能体端点：`uv run uvicorn poc.agent:app --port 8001`

### 3. 启动前端

```bash
cd web
npm install --registry=https://registry.npmmirror.com   # 国内镜像，快
npm run dev                                             # http://localhost:5173，/api 自动代理到 :8000
```

### 4. 生成演示数据

命令行：`uv run python scripts/seed_demo.py`；或打开前端「案例总览」空态点 **「生成演示数据」**，一键生成一条完整演示事件（28 病例 + 12 未发病、流行曲线、四格表、证据、结论、节点确认）。

---

## AI 助手（Phase 4）

入口：左侧「AI 助手」，或工作区头部「问 AI」按钮（自动带入当前事件）。

- **上下文感知**：选择事件后，`POST /api/assistant/chat` 会把该事件的确定性档案摘要（病例定义、判定统计、症状谱、暴露关联 RR/P、潜伏期、已确认节点、结论、样本）注入模型，模型据此针对「本次调查」作答。
- **循证来源**：回答下方列出检索到的依据来源（规范/致病因子/结案报告/监测数据），可核查。
- **透明可核查**：顶部折叠「AI 已知上下文」，展示注入模型的事实，杜绝黑箱。
- **快捷提问（标签即意图）**：一键触发「最可疑食品是什么？」「该查哪些规范依据？」等，降低上手门槛。
- **信任边界**：顶部常驻「AI 仅作辅助，最终结论请人工确认」；确定性指标用工具计算、不口算。

实测示例（DeepSeek）：结合演示事件回答「最可疑食品」，正确判定凉拌菜（RR=5.57, P=0.0000 + 留样金葡菌检出），并**主动指出潜伏期偏长（48.5h vs 典型 1–9h）的矛盾**，符合「如实说明局限」的要求。

---

## API 一览

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/events` | 新建事件 |
| GET | `/api/events` | 事件列表 |
| GET/PATCH | `/api/events/{id}` | 读取 / 更新事件 |
| GET | `/api/events/{id}/load` | 完整档案（定义/人员/暴露/样本/证据/结论/确认） |
| GET | `/api/events/{id}/timeline` | 审计时间线 |
| GET | `/api/events/{id}/analyze` | 确定性分析（流行曲线/三间分布/四格表/潜伏期） |
| GET | `/api/events/{id}/report?kind=` | 初步/阶段/结案报告 |
| PUT | `/api/events/{id}/definition\|people\|exposures\|samples` | 录入病例定义与数据 |
| POST | `/api/events/{id}/evidence\|conclusions\|confirm` | 证据 / 结论 / 节点确认 |
| POST | `/api/events/seed-demo` | 生成演示事件 |
| GET | `/api/kb/docs` `/api/kb/search` | 知识库浏览 / 检索 |
| POST | `/api/assistant/chat` | 上下文感知问答 + 循证来源 |

---

## 目录结构

```
core/                # 确定性：store(SQLite) / stats / classify / analyze / report / deidentify
server/              # FastAPI：routers/(events|kb|assistant) + assistant.py + seed.py
poc/                 # LangGraph ReAct 智能体 + LightRAG 知识库（agent.py / kb.py / config.py / ingest.py）
web/                 # Vite + React + TS + AntD 前端（src/views/…）
kb/                  # 500 条 xls 结构化监测数据导入（ingest_xls.py）
scripts/             # seed_demo.py（演示事件）、extract_corpus.sh（抽取语料）
corpus/              # checklist.json / pathogen_ref.json / meta.json（进 git）
tests/               # 17 个测试文件（确定性 / 检索 / 路由 / 智能体）
data/                # SQLite 运行时（不进 git）
assets/raw/          # 原始报告 + 500 条 xls + 规范 PDF（不进 git）
```

> `app/`（FastAPI+Jinja2 原型）、`assistant/`（早期编排）、`integration/`（报送 stub）为早期方案，保留作参考。

---

## 测试

```bash
uv run python -m pytest tests/ -q
```

覆盖确定性层（store/stats/classify/analyze/report）、检索（BM25/向量/xls 导入）、智能体脚手架、FastAPI 路由（TestClient）。当前 **45 passed, 1 skipped**。

---

## 数据与 git 边界

- **进 git**：代码、`corpus/` 中不涉敏的清单/参考表/版本元数据、`pyproject.toml`、`uv.lock`、`.gitignore`。
- **不进 git**（`.gitignore`）：`docs/`、`data/`、`assets/raw/`（真实报告 + xls + 规范 PDF）、`corpus/standards/`、`corpus/reports/`、`poc/rag_data/`、`poc/.env`、`.venv/`。

---

## 范围外（v1 不做）

案例训练平台、多人协作、供应链可视化、高级统计（匹配/多因素）、病因自动定论、概率排行榜、大屏驾驶舱、自动报送正式监测系统。
