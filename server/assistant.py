"""AI 助手服务：上下文感知 + 循证检索 + 确定性计算。

设计原则（对齐蚂蚁阿福产品思路）：
- 辅助角色：AI 只做综合与表述，最终结论由调查员在「证据与结论」中人工确认；
- 循证：回答引用规范/案例来源（sources），确定性指标用 core/ 计算，模型不口算；
- 透明可核查：注入模型的事件档案摘要（context）一并返回，前端可展开查看「AI 已知什么」。
"""
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from core.analyze import analyze
from core.constants import STAGE_BY_ID, STAGE_IDS, TOPIC_NAMES
from poc import config as poc_config, kb
from poc.agent import SYSTEM_PROMPT, _build_tools

from .deps import get_store


def _llm():
    if poc_config.LLM_PROVIDER == "ollama":
        return ChatOpenAI(model=poc_config.LLM_MODEL, base_url=poc_config.OLLAMA_HOST + "/v1",
                          api_key="ollama", temperature=0)
    return ChatOpenAI(model=poc_config.LLM_MODEL, base_url=poc_config.LLM_BASE_URL,
                      api_key=poc_config.LLM_API_KEY or "sk-placeholder", temperature=0)


_agent = None


def _get_agent():
    global _agent
    if _agent is None:
        _agent = create_react_agent(_llm(), _build_tools(), prompt=SYSTEM_PROMPT)
    return _agent


def _fmt_pct(v):
    return "—" if v is None else f"{v * 100:.1f}%"


def build_context(state):
    """由确定性计算结果构造事件档案摘要（dict）。模型据此作答，前端据此展示「AI 已知什么」。"""
    stats = analyze(state)
    event = state["event"]
    definition = state["definition"] or {}
    counts = stats["counts"]

    symptoms = "、".join(f"{s['symptom']} {_fmt_pct(s['value'])}" for s in stats["symptoms"]) or "无"

    associations = []
    for r in stats["associations"]:
        eff = r.get("effect")
        eff_txt = f"{r.get('measure', '效应')}={eff:.2f}" if isinstance(eff, (int, float)) else "无法计算"
        p = r.get("p_fisher_two_sided")
        p_txt = f"P={p:.4f}" if isinstance(p, (int, float)) else "P=—"
        associations.append(f"{r['food_id']} {eff_txt} {p_txt}")

    inc = stats["incubation"]
    incubation = (f"中位 {inc['median']:.1f} 小时，范围 {inc['minimum']:.1f}–{inc['maximum']:.1f} 小时"
                  if inc.get("n") else "现有资料不足以计算")

    conclusions = {r["topic"]: r for r in state["conclusions"]}
    samples = ["；".join(
        f"{s['id']}({s.get('source') or s.get('category') or '—'})："
        + "；".join(f"{t.get('item')} {t.get('result')}" for t in (s.get("tests") or []))
    ) for s in state["samples"]] or ["无"]

    stages = {sid: (state["stages"].get(sid) or {}).get("status", "pending") for sid in STAGE_IDS}

    return {
        "event": {k: event.get(k) for k in ("id", "title", "lead", "place_type", "region",
                                            "address", "received_at", "occurred_at",
                                            "exposure_at", "investigation_end", "source_place_type",
                                            "source_address", "population_size", "population_basis",
                                            "population_known", "study_design")},
        "definition": {"label": definition.get("label"), "text": definition.get("text"),
                       "start": definition.get("start"), "end": definition.get("end"),
                       "symptoms_any": definition.get("symptoms_any") or [],
                       "minimum_symptoms": definition.get("minimum_symptoms")},
        "counts": counts,
        "attack_rate": _fmt_pct(stats["attack_rate"].get("value")),
        "symptoms": symptoms,
        "associations": associations,
        "incubation": incubation,
        "stages": stages,
        "conclusions": conclusions,
        "samples": samples,
    }


def context_markdown(ctx):
    d = ctx["definition"]
    ev = ctx["event"]
    lines = [
        f"事件：{ev['title']}（编号 {ev['id']}，场所 {ev.get('place_type') or '—'}，"
        f"地区 {ev.get('region') or '—'}，负责人 {ev.get('lead') or '—'}，"
        f"接报 {ev.get('received_at') or '—'}）。",
        f"病例定义：{d.get('label') or '—'}——{d.get('text') or '—'}；时间 {d.get('start') or '—'} 至 "
        f"{d.get('end') or '—'}；纳入症状 {('、'.join(d.get('symptoms_any') or []) or '—')}；最低症状数 {d.get('minimum_symptoms')}。",
        f"判定统计：确诊 {ctx['counts'].get('确诊', 0)}、可能 {ctx['counts'].get('可能', 0)}、"
        f"疑似 {ctx['counts'].get('疑似', 0)}、未发病 {ctx['counts'].get('未发病', 0)}、"
        f"排除 {ctx['counts'].get('排除', 0)}、待定 {ctx['counts'].get('待定', 0)}；罹患率 {ctx['attack_rate']}。",
        f"症状谱：{ctx['symptoms']}。",
        f"暴露关联（效应量 + Fisher P）：{('；'.join(ctx['associations']) or '无')}。",
        f"潜伏期：{ctx['incubation']}。",
        f"阶段状态：{'；'.join(f'{STAGE_BY_ID[sid]["name"]}={st}' for sid, st in ctx['stages'].items())}。",
        f"样本：{'；'.join(ctx['samples'])}。",
    ]
    for topic, r in ctx["conclusions"].items():
        lines.append(f"调查结论[{TOPIC_NAMES.get(topic, topic)}]（{r.get('status')}）："
                     f"{r.get('statement') or '—'}。依据：{r.get('reason') or '—'}。")
    return "\n".join(lines)


def _to_lc(history):
    out = []
    for h in history or []:
        role = h.get("role")
        content = h.get("content", "")
        if role == "assistant":
            out.append(AIMessage(content=content))
        elif role == "user":
            out.append(HumanMessage(content=content))
    return out


def _last_content(result):
    msg = result["messages"][-1]
    return msg.content if isinstance(msg.content, str) else str(msg.content)


async def collect_sources(question):
    refs = []
    for rag in (kb.get_basis_rag(), kb.get_cases_rag()):
        try:
            await rag.initialize_storages()
            refs += await kb.query_sources(rag, question)
        except Exception:
            continue
    seen, out = set(), []
    for r in refs:
        key = r.get("doc_id", "")
        if key and key not in seen:
            seen.add(key)
            out.append(r)
    return out


async def answer(event_id, question, history=None):
    if poc_config.LLM_PROVIDER != "ollama" and not poc_config.LLM_API_KEY:
        raise RuntimeError("未配置 LLM_API_KEY，请在 poc/.env 填写 LLM key")

    ctx = None
    messages = []
    if event_id:
        store = get_store()
        try:
            state = store.load(event_id)
        except ValueError:
            raise ValueError(f"事件不存在：{event_id}")
        ctx = build_context(state)
        messages.append(SystemMessage(content=(
            "以下是当前调查事件的档案摘要（确定性计算所得，仅作上下文，不要编造其中的数字）：\n"
            + context_markdown(ctx))))

    messages += _to_lc(history)
    messages.append(HumanMessage(content=question))

    agent = _get_agent()
    result = await agent.ainvoke({"messages": messages})
    return {"answer": _last_content(result), "context": ctx,
            "context_md": context_markdown(ctx) if ctx else None,
            "sources": await collect_sources(question)}
