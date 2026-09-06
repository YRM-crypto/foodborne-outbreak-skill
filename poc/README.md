# POC：食源性疾病暴发调查智能体

复用现成框架搭起来的可运行原型：

- **UI**：Open WebUI（现成聊天界面）
- **智能体**：LangGraph ReAct（`create_react_agent`），工具调用循环
- **知识库**：LightRAG（依据库 + 案例库）
- **LLM**：本地 Ollama `qwen3:30b`（默认，支持工具调用）/ 可切 DeepSeek（OpenAI 兼容）
- **Embedding**：本地 Ollama `bge-m3`（1024 维，符合内网方向）

## 架构

```
Open WebUI（Docker，:3000）
   └─ POST /v1/chat/completions（OpenAI 兼容）
LangGraph ReAct Agent（poc/agent.py）
   ├─ search_basis           → LightRAG 依据库（规范指南 + 致病因子 + 调查清单）
   ├─ search_similar_cases   → LightRAG 案例库（结案报告 + 500 条监测数据）
   └─ attack_rate            → core.stats.proportion（确定性计算，复用）
LightRAG（poc/kb.py，本地 Ollama bge-m3 + qwen3:30b）
```

## 快速开始

```bash
# 0. 确保 Ollama 已拉起模型（本地无需任何 key）
ollama pull qwen3:30b-a3b-instruct-2507-q4_K_M
ollama pull bge-m3

# 1. 配置（默认就是本地 Ollama，通常无需 .env；要切 DeepSeek 才复制改 key）
cp poc/.env.example poc/.env

# 2. 灌语料（qwen3:30b 做实体抽取较慢，500 条数据 + 24 篇文档约需数十分钟到数小时）
uv run python -m poc.ingest

# 3. 起服务（:8000）
uv run python -m uvicorn poc.agent:app --port 8000

# 4. 起 Open WebUI（:3000）
#    Apple Silicon + colima(VZ) 上需用修复版镜像（cryptography 48 会 SIGILL，见 Dockerfile.openwebui）
docker build -f poc/Dockerfile.openwebui -t open-webui-arm64 .
docker run -d -p 3000:8080 --name open-webui \
  -v open-webui:/app/backend/data \
  -e OPENAI_API_BASE_URLS="http://host.docker.internal:8000/v1" \
  -e OPENAI_API_KEYS="ollama" \
  -e ENABLE_OPENAI_API=true \
  open-webui-arm64
```

打开 http://localhost:3000，在 Open WebUI 的 OpenAI 连接里选 `qwen3:30b-a3b-instruct-2507-q4_K_M` 即可对话。

## 两个库

| 库 | 工作目录 | 语料 |
|---|---|---|
| 依据库 | `poc/rag_data/basis/` | 4 规范指南 + 10 致病因子 + 13 调查清单 |
| 案例库 | `poc/rag_data/cases/` | 20 结案报告 + 500 条监测数据 |

## 内网切换

- 默认即本地 Ollama，已符合内网方向。
- 测试期如需外网 DeepSeek：`poc/.env` 里 `LLM_PROVIDER=openai` + `LLM_API_KEY`；embedding 仍走本地 `bge-m3`。
