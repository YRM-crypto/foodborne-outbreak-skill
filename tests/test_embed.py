import unittest
from kb.embed import Embedder, EmbeddingUnavailable

class TestEmbedder(unittest.TestCase):
    def test_unavailable_when_disabled(self):
        e = Embedder(mode="api", base_url="", api_key="", model="")
        self.assertFalse(e.available)
        with self.assertRaises(EmbeddingUnavailable):
            e.embed(["hello"])

    def test_available_when_configured(self):
        e = Embedder(mode="api", base_url="https://x", api_key="k", model="m")
        self.assertTrue(e.available)

if __name__ == "__main__":
    unittest.main()
