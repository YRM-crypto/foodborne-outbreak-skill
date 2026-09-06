"""知识库：文档浏览 + 独立检索（含来源溯源）。复用 poc/kb.py 的 LightRAG。"""
from fastapi import APIRouter, HTTPException, Query
from lightrag import QueryParam

from poc import kb

router = APIRouter()


def _rag(lib: str):
    if lib not in ("basis", "cases"):
        raise HTTPException(400, "lib 需为 basis/cases")
    return kb.get_basis_rag() if lib == "basis" else kb.get_cases_rag()


@router.get("/docs")
def list_docs(lib: str = Query("basis")):
    docs = kb.load_basis_docs() if lib == "basis" else kb.load_case_docs()
    return [{"id": d[0], "chars": len(d[1]), "preview": d[1][:200]} for d in docs]


@router.get("/docs/{doc_id}")
def get_doc(doc_id: str, lib: str = Query("basis")):
    docs = kb.load_basis_docs() if lib == "basis" else kb.load_case_docs()
    for d in docs:
        if d[0] == doc_id:
            return {"id": d[0], "content": d[1]}
    raise HTTPException(404, "文档不存在")


@router.get("/search")
async def search(q: str, lib: str = Query("basis")):
    rag = _rag(lib)
    await rag.initialize_storages()
    param = QueryParam(mode="hybrid", enable_rerank=False)
    if hasattr(rag, "aquery_data"):
        result = await rag.aquery_data(q, param=param)
    else:
        result = await rag.aquery(q, param=param)
    return {"query": q, "lib": lib, "result": result}
