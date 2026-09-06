"""Embedding 客户端：api（OpenAI 兼容）或 local（sentence-transformers）。可配、可禁用。"""
import httpx


class EmbeddingUnavailable(RuntimeError):
    pass


class Embedder:
    def __init__(self, mode="api", base_url="", api_key="", model="", local_model="BAAI/bge-small-zh-v1.5"):
        self.mode = mode
        self.base_url = (base_url or "").rstrip("/")
        self.api_key = api_key
        self.model = model
        self.local_model = local_model
        self._local = None

    @property
    def available(self):
        if self.mode == "api":
            return bool(self.base_url)
        return self.mode == "local"

    def _ensure_local(self):
        if self._local is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._local = SentenceTransformer(self.local_model)
            except Exception as e:  # noqa: BLE001
                raise EmbeddingUnavailable(f"本地 embedding 模型加载失败：{e}")
        return self._local

    def embed(self, texts):
        if not self.available:
            raise EmbeddingUnavailable("embedding 未配置或已禁用")
        if self.mode == "api":
            try:
                r = httpx.post(f"{self.base_url}/embeddings",
                               headers={"Authorization": f"Bearer {self.api_key}"},
                               json={"model": self.model, "input": texts}, timeout=120.0)
                r.raise_for_status()
                data = r.json()["data"]
                return [d["embedding"] for d in sorted(data, key=lambda x: x["index"])]
            except (httpx.HTTPError, KeyError, IndexError, TypeError) as e:
                raise EmbeddingUnavailable(f"embedding 调用失败：{e}")
        model = self._ensure_local()
        vecs = model.encode(list(texts), normalize_embeddings=True)
        return [list(v) for v in vecs]
