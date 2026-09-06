import unittest
import tempfile
from pathlib import Path
from kb.retriever import Retriever

class FakeEmbedder:
    available = True
    def __init__(self):
        self.calls = []
    def embed(self, texts):
        self.calls.append(texts)
        vocab = list("副溶血性弧菌海产品诺如病毒学校呕吐")
        return [[1.0 if ch in t else 0.0 for ch in vocab] for t in texts]

class FakeUnavailable:
    available = False
    def embed(self, texts):
        raise RuntimeError("unavailable")

class TestRetriever(unittest.TestCase):
    def test_vector_search(self):
        r = Retriever(str(Path(tempfile.mkdtemp()) / "v.db"), FakeEmbedder())
        r.index([{"id": "a", "source": "s", "text": "副溶血性弧菌 海产品", "locator": "L1"},
                 {"id": "b", "source": "s", "text": "诺如病毒 学校 呕吐", "locator": "L2"}])
        hits = r.search("海产品 副溶血性弧菌")
        self.assertEqual(hits[0]["id"], "a")
        self.assertEqual(hits[0]["locator"], "L1")

    def test_bm25_fallback(self):
        r = Retriever(str(Path(tempfile.mkdtemp()) / "v.db"), FakeUnavailable())
        r.index([{"id": "a", "source": "s", "text": "副溶血性弧菌 海产品", "locator": "L1"},
                 {"id": "b", "source": "s", "text": "诺如病毒 学校 呕吐", "locator": "L2"}])
        hits = r.search("海产品")
        self.assertTrue(hits)
        self.assertEqual(hits[0]["index"], 0)

if __name__ == "__main__":
    unittest.main()
