import unittest
from kb.bm25 import BM25Index

class TestBM25(unittest.TestCase):
    def test_search_ranks(self):
        idx = BM25Index(["集体用餐后多名学生出现呕吐和腹泻", "诺如病毒潜伏期8到48小时", "副溶血性弧菌见于海产品"])
        hits = idx.search("呕吐 腹泻 学生")
        self.assertTrue(hits)
        self.assertEqual(hits[0]["index"], 0)

    def test_empty_query(self):
        self.assertEqual(BM25Index(["a b c"]).search(""), [])

if __name__ == "__main__":
    unittest.main()
