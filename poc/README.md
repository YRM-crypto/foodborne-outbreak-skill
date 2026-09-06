# POC：食源性疾病暴发调查智能体

复用现成框架搭起来的可运行原型：

- **UI**：Open WebUI（现成聊天界面）
- **智能体**：LangGraph ReAct（`create_react_agent`），工具调用循环
- **知识库**：LightRAG（依据库 + 案例库）
- **LLM**：DeepSeek（OpenAI 兼容）
- **Embedding**：本地 `BAAI/bge-m3`（DeepSeek 无 embedding，且符合内网方向）

## 架构

```
Open WebUI（Docker，:3000）
   └─ POST /v1/chat/completions（OpenAI 兼容）
LangGraph ReAct Agent（poc/agent.py）
   ├─ search_basis           → LightRAG 依据库（规范指南 + 致病因子 + 调查清单）
   ├─ search_similar_cases   → LightRAG 案例库（结案报告 + 500 条监测数据）
   └─ attack_rate            → core.stats.proportion（确定性计算，复用）
LightRAG（poc/kb.py，本地 bge-m3 + DeepSeek）
```

## 快速开始

```bash
# 1. 配置 key（DeepSeek 无 embedding，故 embedding 走本地）
cp poc/.env.example poc/.env    # 填 LLM_API_KEY

# 2. 灌语料（首次会下载 bge-m3，约 2GB；需要 LLM key 做实体抽取）
uv run python -m poc.ingest

# 3. 起服务（:8000）
uv run python -m uvicorn poc.agent:app --port 8000

# 4. 起 Open WebUI（:3000）
docker run -d -p 3000:8080 --name open-webui \
  -e OPENAI_API_BASE_URLS="http://host.docker.internal:8000/v1" \
  -e OPENAI_API_KEYS="sk-placeholder" \
  -e ENABLE_OPENAI_API=true \
  ghcr.io/open-webui/open-webui:main
```

打开 http://localhost:3000，在 Open WebUI 的 OpenAI 连接里选 `deepseek-chat` 即可对话。

## 两个库

| 库 | 工作目录 | 语料 |
|---|---|---|
| 依据库 | `poc/rag_data/basis/` | 4 规范指南 + 10 致病因子 + 13 调查清单 |
| 案例库 | `poc/rag_data/cases/` | 20 结案报告 + 500 条监测数据 |

## 内网切换

- LLM：改 `poc/.env` 的 `LLM_BASE_URL` 指向内网模型（如 Ollama）。
- Embedding：已经走本地 `bge-m3`，无需改。
