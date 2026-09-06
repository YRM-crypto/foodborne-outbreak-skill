import unittest
from kb.corpus import load_checklist, load_pathogen_ref, load_meta, load_texts

class TestCorpus(unittest.TestCase):
    def test_checklist_13(self):
        items = load_checklist()
        self.assertEqual(len(items), 13)
        self.assertTrue(all(it.get(k) for it in items for k in ("id", "stage", "title", "why", "basis")))

    def test_pathogen_ref_structured(self):
        refs = load_pathogen_ref()
        self.assertTrue(any(r["name"] == "诺如病毒" for r in refs))
        nv = next(r for r in refs if r["name"] == "诺如病毒")
        self.assertIsInstance(nv["latency_min"], (int, float))
        self.assertIsInstance(nv["symptoms"], list)
        self.assertIsInstance(nv["foods"], list)

    def test_meta_has_version(self):
        meta = load_meta()
        self.assertIn("sources", meta)

    def test_load_texts_missing_dir_empty(self):
        self.assertEqual(load_texts("nonexistent"), [])

if __name__ == "__main__":
    unittest.main()
