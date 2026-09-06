"""FastAPI 依赖：SQLite 审计存储单例（测试可覆盖）。"""
from core.store import Store

from . import config

_store: Store | None = None


def get_store() -> Store:
    global _store
    if _store is None:
        _store = Store(config.STORE_PATH)
    return _store
