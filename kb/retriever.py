"""检索器：向量主通道 + BM25 兜底。返回带来源定位的命中。"""
from kb.bm25 import BM25Index
from kb.vector_store import VectorStore


class Retriever:
    def __init__(self, vector_db_path, embedder):
        self.embedder = embedder
        self.vector_store = VectorStore(vector_db_path)
        self.bm25 = None
        self.docs = []

    def index(self, docs, force=False):
        self.docs = list(docs)
        self.bm25 = BM25Index([d["text"] for d in self.docs])
        if not getattr(self.embedder, "available", False):
            return
        missing = [d for d in self.docs if force or not self.vector_store.has(d["id"])]
        if not missing:
            return
        vectors = self.embedder.embed([d["text"] for d in missing])
        for d, v in zip(missing, vectors):
            self.vector_store.upsert(d["id"], d.get("source", ""), d["text"], d.get("locator", ""), v)

    def search(self, query, top_k=10):
        if getattr(self.embedder, "available", False):
            qv = self.embedder.embed([query])[0]
            return self.vector_store.search(qv, top_k)
        return self.bm25.search(query, top_k) if self.bm25 else []
