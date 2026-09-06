"""可选的 MCP 服务入口：把知识库暴露为 MCP tools，供外部工具（付费）调用。

依赖 optional 组的 mcp；未安装时本模块的 build 函数会抛 RuntimeError。
"""
from kb.retriever import Retriever


def build_tools(retriever, pathogen_ref, checklist):
    """返回 [(name, description, callable)]，供 MCP server 注册。"""
    def search_cases(query: str, top_k: int = 10):
        hits = retriever.search(query, top_k)
        return [{"text": h["text"], "locator": h["locator"], "score": h.get("score")} for h in hits]

    def match_pathogens(incubation_hours=None, symptoms=None):
        refs = pathogen_ref
        if incubation_hours is not None:
            refs = [r for r in refs if r["latency_min"] <= incubation_hours <= r["latency_max"]]
        if symptoms:
            refs = [r for r in refs if any(s in r["symptoms"] for s in symptoms)]
        return [{"name": r["name"], "category": r["category"], "specimen": r["specimen"]} for r in refs]

    def search_standards(keyword: str):
        return [{"id": c["id"], "title": c["title"], "basis": c["basis"]}
                for c in checklist if keyword in c["title"] + c["basis"]]

    return [("search_cases", "相似案例检索", search_cases),
            ("match_pathogens", "按潜伏期/症状匹配致病因子范围", match_pathogens),
            ("search_standards", "检索规范清单条目", search_standards)]


def build_server(retriever, pathogen_ref, checklist):
    try:
        from mcp.server import Server
    except ImportError as e:
        raise RuntimeError("mcp 未安装（optional 依赖）") from e
    server = Server("outbreak-kb")
    for name, desc, fn in build_tools(retriever, pathogen_ref, checklist):
        server.add_tool(name, desc, fn)
    return server
