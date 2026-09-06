import unittest
import tempfile
from pathlib import Path
from kb.vector_store import VectorStore

class TestVectorStore(unittest.TestCase):
    def test_upsert_and_search(self):
        p = Path(tempfile.mkdtemp()) / "v.db"
        vs = VectorStore(str(p))
        vs.upsert("a", "src", "苹果", "loc-a", [1.0, 0.0])
        vs.upsert("b", "src", "橙子", "loc-b", [0.9, 0.1])
        vs.upsert("c", "src", "火车", "loc-c", [0.0, 1.0])
        hits = vs.search([1.0, 0.0], top_k=2)
        self.assertEqual(hits[0]["id"], "a")
        self.assertEqual(len(hits), 2)

    def test_has(self):
        p = Path(tempfile.mkdtemp()) / "v.db"
        vs = VectorStore(str(p))
        self.assertFalse(vs.has("x"))
        vs.upsert("x", "s", "t", "l", [0.0])
        self.assertTrue(vs.has("x"))

if __name__ == "__main__":
    unittest.main()
