"""POC 配置：环境变量 + 缺省值，`poc/.env` 可覆盖。默认走本地 Ollama（无需 key）。"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name(".env"))

ROOT = Path(__file__).resolve().parent.parent

# LLM 提供商：ollama（本地，默认）| openai（DeepSeek 等 OpenAI 兼容）
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "ollama")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.deepseek.com/v1")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_MODEL = os.environ.get("LLM_MODEL", "qwen3:30b-a3b-instruct-2507-q4_K_M")

# Embedding 提供商：ollama（默认）| local（sentence-transformers）
EMBEDDING_PROVIDER = os.environ.get("EMBEDDING_PROVIDER", "ollama")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "bge-m3:latest")

# LightRAG 两个库的工作目录（依据库 / 案例库）
RAG_DIR = Path(os.environ.get("RAG_DIR", str(Path(__file__).parent / "rag_data")))

# 语料（项目内固定路径，可覆盖）
STANDARDS_DIR = ROOT / "corpus" / "standards"
REPORTS_DIR = ROOT / "corpus" / "reports"
XLS_PATH = Path(os.environ.get("XLS_PATH", str(ROOT / "assets" / "raw" / "2025-脱敏版本-500条.xls")))
PATHOGEN_REF = ROOT / "corpus" / "pathogen_ref.json"
CHECKLIST = ROOT / "corpus" / "checklist.json"
