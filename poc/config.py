"""POC 配置：环境变量 + 缺省值，`poc/.env` 可覆盖。"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name(".env"))

ROOT = Path(__file__).resolve().parent.parent

# LLM（DeepSeek，OpenAI 兼容；DeepSeek 无 embedding，见 README）
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.deepseek.com/v1")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_MODEL = os.environ.get("LLM_MODEL", "deepseek-chat")

# Embedding（本地 sentence-transformers，避免额外 key、符合内网方向）
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "BAAI/bge-m3")

# LightRAG 两个库的工作目录（依据库 / 案例库）
RAG_DIR = Path(os.environ.get("RAG_DIR", str(Path(__file__).parent / "rag_data")))

# 语料（项目内固定路径，可覆盖）
STANDARDS_DIR = ROOT / "corpus" / "standards"
REPORTS_DIR = ROOT / "corpus" / "reports"
XLS_PATH = Path(os.environ.get("XLS_PATH", str(ROOT / "assets" / "raw" / "2025-脱敏版本-500条.xls")))
PATHOGEN_REF = ROOT / "corpus" / "pathogen_ref.json"
CHECKLIST = ROOT / "corpus" / "checklist.json"
