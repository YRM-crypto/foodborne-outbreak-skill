"""工作台后端配置：SQLite 存储路径，可被环境变量覆盖。"""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / "poc" / ".env")

DATA_DIR = Path(os.environ.get("DATA_DIR", str(ROOT / "data")))
STORE_PATH = Path(os.environ.get("STORE_PATH", str(DATA_DIR / "cases.db")))
