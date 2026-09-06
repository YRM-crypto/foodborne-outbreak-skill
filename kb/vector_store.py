"""SQLite 存向量（BLOB/JSON）+ 查询时暴力余弦。语料小，无需向量数据库。"""
import json
import math
import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS vectors (
    id TEXT PRIMARY KEY, source TEXT, text TEXT, locator TEXT, vector TEXT NOT NULL
);
"""


def _cosine(a, b):
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return sum(x * y for x, y in zip(a, b)) / (na * nb)


class VectorStore:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.path))
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)

    def close(self):
        self.conn.close()

    def has(self, id_):
        return self.conn.execute("SELECT 1 FROM vectors WHERE id=?", (id_,)).fetchone() is not None

    def upsert(self, id_, source, text, locator, vector):
        self.conn.execute(
            "INSERT INTO vectors(id,source,text,locator,vector) VALUES(?,?,?,?,?) "
            "ON CONFLICT(id) DO UPDATE SET source=excluded.source, text=excluded.text,"
            " locator=excluded.locator, vector=excluded.vector",
            (id_, source, text, locator, json.dumps(vector)))
        self.conn.commit()

    def search(self, query_vector, top_k=10):
        rows = self.conn.execute("SELECT id,source,text,locator,vector FROM vectors").fetchall()
        scored = []
        for r in rows:
            v = json.loads(r["vector"])
            scored.append((_cosine(query_vector, v), dict(r)))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [{"id": r["id"], "source": r["source"], "text": r["text"],
                 "locator": r["locator"], "score": s} for s, r in scored[:top_k]]
