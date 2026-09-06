"""加载检索语料与版本元数据。文本语料由 scripts/extract_corpus.sh 生成。"""
import json
from pathlib import Path

CORPUS_ROOT = Path(__file__).resolve().parents[1] / "corpus"


def _read_json(name):
    return json.loads((CORPUS_ROOT / name).read_text(encoding="utf-8"))


def load_checklist():
    return _read_json("checklist.json")


def load_pathogen_ref():
    return _read_json("pathogen_ref.json")


def load_meta():
    return _read_json("meta.json")


def load_texts(subdir):
    base = CORPUS_ROOT / subdir
    if not base.is_dir():
        return []
    return [{"id": p.stem, "text": p.read_text(encoding="utf-8")}
            for p in sorted(base.glob("*.txt"))]
