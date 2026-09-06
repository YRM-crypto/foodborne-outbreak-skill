"""一次性灌语料：`uv run python -m poc.ingest`（需 LLM key + 首次下载 embedding 模型）。"""
import asyncio

from . import kb


async def main():
    print("灌依据库（规范指南 + 致病因子 + 调查清单）...")
    await kb.ingest(kb.get_basis_rag(), kb.load_basis_docs())
    print("灌案例库（结案报告 + 500 条监测数据）...")
    await kb.ingest(kb.get_cases_rag(), kb.load_case_docs())
    print("完成。工作目录：", kb.get_basis_rag().working_dir)


if __name__ == "__main__":
    asyncio.run(main())
