"""集中读取环境变量。"""
import os
from pathlib import Path


def _flag(name, default=False):
    return os.environ.get(name, "true" if default else "false").strip().lower() in ("1", "true", "yes", "on")


class Config:
    def __init__(self):
        repo = Path(__file__).resolve().parents[1]
        self.db_path = os.environ.get("OUTBREAK_DB", str(repo / "data" / "outbreak.db"))
        self.xls_path = os.environ.get("OUTBREAK_XLS", str(repo / "assets" / "raw" / "2025-脱敏版本-500条.xls"))
        self.model_base_url = os.environ.get("MODEL_BASE_URL", "")
        self.model_api_key = os.environ.get("MODEL_API_KEY", "")
        self.model_name = os.environ.get("MODEL_NAME", "deepseek-chat")
        self.allow_external_llm = _flag("ALLOW_EXTERNAL_LLM", default=True)
        self.deidentify = _flag("DEIDENTIFY", default=False)
        self.embedding_mode = os.environ.get("EMBEDDING_MODE", "api")
        self.embedding_base_url = os.environ.get("EMBEDDING_BASE_URL", "")
        self.embedding_api_key = os.environ.get("EMBEDDING_API_KEY", "")
        self.embedding_model = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
        self.embedding_local_model = os.environ.get("EMBEDDING_LOCAL_MODEL", "BAAI/bge-small-zh-v1.5")


config = Config()
