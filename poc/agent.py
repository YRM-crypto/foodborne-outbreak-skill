"""ReAct 智能体 + OpenAI 兼容端点（供 Open WebUI 对接）。"""
import json

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from . import config, kb


SYSTEM_PROMPT = """你是「食源性疾病暴发调查助手」，服务基层疾控流调人员。你的职责是帮用户把一次食源性疾病暴发调查做得更完整、更有依据：查依据、补资料、做分析、核证据、写报告。

铁律（必须遵守）：
1. 只基于工具返回的资料和明确的流行病学事实作答，不编造数据、不臆断病因。
2. 引用规范/指南或历史案例时，说明来源。
3. 确定性计算（罹患率、RR/OR、潜伏期等）必须用工具算，不口算。
4. 结论区分「明确」「可能」「证据不足」三种程度；证据不足就如实说，不硬下结论。
5. 涉及病人身份信息时提醒脱敏。

可用工具：
- search_basis：查规范/技术指南中的调查依据、病例定义、判定标准。
- search_similar_cases：查历史结案报告与监测数据中的相似暴发案例。
- attack_rate：计算罹患率及 95% 置信区间。

需要查依据、找相似案例或算指标时，先调用对应工具，再基于结果回答。"""


def _build_tools():
    @tool
    async def search_basis(question: str) -> str:
        """在食源性疾病调查规范/技术指南里查依据、病例定义、判定标准。question：一句话描述要查的问题。"""
        rag = kb.get_basis_rag()
        await rag.initialize_storages()
        return await kb.query(rag, question)

    @tool
    async def search_similar_cases(question: str) -> str:
        """在历史结案报告和 500 条监测数据里查相似暴发案例。question：描述致病因子/食品/场所/症状等特征。"""
        rag = kb.get_cases_rag()
        await rag.initialize_storages()
        return await kb.query(rag, question)

    @tool
    def attack_rate(cases: int, exposed: int) -> str:
        """计算罹患率（病例数/暴露人数）及 95% 置信区间（Wilson）。cases：发病数；exposed：暴露人数。"""
        from core.stats import proportion
        r = proportion(cases, exposed)
        if r["value"] is None:
            return f"罹患率无法计算：{r.get('reason', '')}"
        lo, hi = r["ci95"]
        return f"罹患率 {r['value'] * 100:.1f}%（95%CI {lo * 100:.1f}–{hi * 100:.1f}%）"

    return [search_basis, search_similar_cases, attack_rate]


def build_agent():
    if config.LLM_PROVIDER == "ollama":
        llm = ChatOpenAI(model=config.LLM_MODEL, base_url=config.OLLAMA_HOST + "/v1",
                         api_key="ollama", temperature=0)
    else:
        llm = ChatOpenAI(model=config.LLM_MODEL, base_url=config.LLM_BASE_URL,
                         api_key=config.LLM_API_KEY or "sk-placeholder", temperature=0)
    return create_react_agent(llm, _build_tools(), prompt=SYSTEM_PROMPT,
                              checkpointer=MemorySaver())


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str = ""
    messages: list[ChatMessage]
    stream: bool = False


def _to_lc(messages):
    out = []
    for m in messages:
        if m.role == "system":
            out.append(SystemMessage(content=m.content))
        elif m.role == "assistant":
            out.append(AIMessage(content=m.content))
        else:
            out.append(HumanMessage(content=m.content))
    return out


def _last_content(result):
    msg = result["messages"][-1]
    return msg.content if isinstance(msg.content, str) else str(msg.content)


def create_app():
    app = FastAPI(title="食源性疾病暴发调查智能体")
    agent = build_agent()

    @app.get("/v1/models")
    def models():
        return {"object": "list",
                "data": [{"id": config.LLM_MODEL, "object": "model", "owned_by": "deepseek"}]}

    @app.post("/v1/chat/completions")
    async def chat(req: ChatRequest):
        if config.LLM_PROVIDER != "ollama" and not config.LLM_API_KEY:
            from fastapi.responses import JSONResponse
            return JSONResponse({"error": {"message": "未配置 LLM_API_KEY，请在 poc/.env 填写 LLM key"}},
                                status_code=400)
        messages = _to_lc(req.messages)

        if req.stream:
            async def gen():
                result = await agent.ainvoke({"messages": messages})
                chunk = {"id": "chatcmpl-poc", "object": "chat.completion.chunk",
                         "model": config.LLM_MODEL,
                         "choices": [{"index": 0,
                                      "delta": {"role": "assistant", "content": _last_content(result)},
                                      "finish_reason": "stop"}]}
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
            return StreamingResponse(gen(), media_type="text/event-stream")

        result = await agent.ainvoke({"messages": messages})
        return {"id": "chatcmpl-poc", "object": "chat.completion", "created": 0,
                "model": config.LLM_MODEL,
                "choices": [{"index": 0,
                             "message": {"role": "assistant", "content": _last_content(result)},
                             "finish_reason": "stop"}]}

    return app


app = create_app()
