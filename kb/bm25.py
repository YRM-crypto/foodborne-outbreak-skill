"""纯 Python BM25 + jieba 分词。离线可跑，无嵌入依赖。"""
import math
from collections import Counter
import jieba

K1, B = 1.5, 0.75


def tokenize(text):
    return [t for t in jieba.cut(text or "") if t.strip()]


class BM25Index:
    def __init__(self, docs):
        self.docs = list(docs)
        self.toks = [Counter(tokenize(d)) for d in self.docs]
        self.avgdl = sum(sum(c.values()) for c in self.toks) / max(1, len(self.toks))
        self.df = Counter()
        for c in self.toks:
            self.df.update(c.keys())
        self.n = len(self.docs)

    def _idf(self, term):
        return math.log(1 + (self.n - self.df.get(term, 0) + 0.5) / (self.df.get(term, 0) + 0.5))

    def search(self, query, top_k=10):
        qt = Counter(tokenize(query))
        if not qt:
            return []
        scores = []
        for i, c in enumerate(self.toks):
            dl = sum(c.values())
            s = sum(self._idf(t) * (tf := c[t]) * (K1 + 1) / (tf + K1 * (1 - B + B * dl / max(1, self.avgdl))) * qf
                    for t, qf in qt.items() if t in c)
            if s > 0:
                scores.append((s, i))
        scores.sort(reverse=True)
        return [{"index": i, "score": s, "text": self.docs[i]} for s, i in scores[:top_k]]
