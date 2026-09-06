"""LightRAG 知识层：默认走本地 Ollama（LLM=qwen、embedding=bge-m3），两个库（依据/案例）。"""
import asyncio
import json
from pathlib import Path

from lightrag import LightRAG, QueryParam
from lightrag.llm.openai import openai_complete_if_cache
from lightrag.utils import EmbeddingFunc

from kb.ingest_xls import load_xls_events, event_to_text
from . import config


def make_llm_func():
    if config.LLM_PROVIDER == "ollama":
        from lightrag.llm.ollama import ollama_model_complete
        return ollama_model_complete

    async def llm_func(prompt, system_prompt=None, history_messages=None, **kwargs):
        if history_messages is None:
            history_messages = []
        kwargs.setdefault("timeout", 150)
        return await openai_complete_if_cache(
            config.LLM_MODEL, prompt, system_prompt=system_prompt,
            history_messages=history_messages,
            base_url=config.LLM_BASE_URL, api_key=config.LLM_API_KEY, **kwargs)

    return llm_func


_embed_model = None


def _get_embed_model():
    global _embed_model
    if _embed_model is None:
        from sentence_transformers import SentenceTransformer
        _embed_model = SentenceTransformer(config.EMBEDDING_MODEL)
    return _embed_model


def make_embedding_func():
    if config.EMBEDDING_PROVIDER == "ollama":
        from lightrag.llm.ollama import ollama_embed
        return ollama_embed

    model = _get_embed_model()

    async def embed_func(texts, context="document", **kwargs):
        return await asyncio.to_thread(model.encode, texts, normalize_embeddings=True)

    return EmbeddingFunc(
        embedding_dim=model.get_sentence_embedding_dimension(),
        max_token_size=8192,
        func=embed_func,
        model_name=config.EMBEDDING_MODEL,
    )


def build_rag(working_dir: Path) -> LightRAG:
    working_dir = Path(working_dir)
    working_dir.mkdir(parents=True, exist_ok=True)
    return LightRAG(
        working_dir=str(working_dir),
        llm_model_func=make_llm_func(),
        llm_model_name=config.LLM_MODEL,
        embedding_func=make_embedding_func(),
    )


_basis = None
_cases = None


def get_basis_rag() -> LightRAG:
    global _basis
    if _basis is None:
        _basis = build_rag(config.RAG_DIR / "basis")
    return _basis


def get_cases_rag() -> LightRAG:
    global _cases
    if _cases is None:
        _cases = build_rag(config.RAG_DIR / "cases")
    return _cases


def _pathogen_text(r):
    return " ".join(filter(None, [
        r.get("name", ""),
        "分类" + str(r.get("category", "")),
        "潜伏期" + str(r.get("latency_min", "")) + "-" + str(r.get("latency_max", "")) + "小时",
        "症状" + "、".join(r.get("symptoms", [])),
        "常见食品" + "、".join(r.get("foods", [])),
        "标本" + str(r.get("specimen", "")),
        "判定" + str(r.get("criterion", "")),
    ]))


def load_basis_docs():
    """依据库：规范指南 + 致病因子参考 + 调查清单。"""
    docs = []
    for p in sorted(config.STANDARDS_DIR.glob("*.txt")):
        docs.append((f"standard:{p.stem}", p.read_text(encoding="utf-8")))
    if config.PATHOGEN_REF.exists():
        refs = json.loads(config.PATHOGEN_REF.read_text(encoding="utf-8"))
        docs.extend((f"pathogen:{r['name']}", _pathogen_text(r)) for r in refs)
    if config.CHECKLIST.exists():
        items = json.loads(config.CHECKLIST.read_text(encoding="utf-8"))
        text = "\n".join(
            f"{i.get('id')} [{i.get('stage')}] {i.get('title')}；{i.get('why')}；依据 {i.get('basis')}"
            for i in items)
        docs.append(("checklist", text))
    return docs


def load_case_docs(batch_size=50):
    """案例库：结案报告 + 500 条监测数据（监测数据按 batch_size 打包，避免数百次串行抽取）。"""
    docs = []
    for p in sorted(config.REPORTS_DIR.glob("*.txt")):
        t = p.read_text(encoding="utf-8").strip()
        if t:
            docs.append((f"report:{p.stem}", t))
    events = [e for e in load_xls_events(str(config.XLS_PATH)) if event_to_text(e).strip()]
    for i in range(0, len(events), batch_size):
        batch = events[i:i + batch_size]
        docs.append((f"monitoring:{i // batch_size:03d}", "\n".join(event_to_text(e) for e in batch)))
    return docs


async def ingest(rag, docs):
    await rag.initialize_storages()
    n = len(docs)
    for idx, (doc_id, text) in enumerate(docs, 1):
        print(f"  [{idx}/{n}] {doc_id}（{len(text)} 字）", flush=True)
        await rag.ainsert(text, ids=[doc_id])
    await rag.finalize_storages()


async def query(rag, question, mode="hybrid"):
    return await rag.aquery(question, param=QueryParam(mode=mode, enable_rerank=False))


def _source_label(doc_id):
    """把灌库时的 doc_id 映射成可读的中文来源名。"""
    if ":" in doc_id:
        kind, name = doc_id.split(":", 1)
        if kind == "standard":
            return f"规范《{name}》"
        if kind == "pathogen":
            return f"致病因子·{name}"
        if kind == "report":
            return f"结案报告·{name}"
        if kind == "monitoring":
            return f"监测数据·第{name}批"
    if doc_id == "checklist":
        return "调查清单"
    return doc_id


async def query_sources(rag, question):
    """返回循证来源（去重后的 doc_id / 中文名），供前端展示引用依据。

    LightRAG 的 aquery_data 把来源挂在 chunks 的 chunk_id 上（file_path 多为
    "unknown_source"、references 常为空），因此从 chunk_id 解析 doc_id。
    """
    if not hasattr(rag, "aquery_data"):
        return []
    param = QueryParam(mode="hybrid", enable_rerank=False)
    result = await rag.aquery_data(question, param=param)
    data = (result or {}).get("data") or {}
    seen, out = set(), []
    for c in (data.get("chunks") or []):
        if not isinstance(c, dict):
            continue
        cid = c.get("chunk_id", "")
        doc_id = cid.split("-chunk-")[0] if "-chunk-" in cid else cid
        if not doc_id or doc_id in seen:
            continue
        seen.add(doc_id)
        out.append({"doc_id": doc_id, "label": _source_label(doc_id)})
    return out
