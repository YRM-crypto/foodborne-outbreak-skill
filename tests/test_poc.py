import unittest
from fastapi.testclient import TestClient
from poc import config
from poc.agent import app, _build_tools


class TestPoc(unittest.TestCase):
    def test_tool_names(self):
        self.assertEqual([t.name for t in _build_tools()],
                         ["search_basis", "search_similar_cases", "attack_rate"])

    def test_models_endpoint(self):
        c = TestClient(app)
        r = c.get("/v1/models")
        self.assertEqual(r.status_code, 200)
        self.assertIn("deepseek", r.text)

    def test_chat_requires_key(self):
        if config.LLM_API_KEY:
            self.skipTest("已配置真实 key，跳过空 key 保护测试")
        c = TestClient(app)
        r = c.post("/v1/chat/completions",
                   json={"messages": [{"role": "user", "content": "你好"}]})
        self.assertEqual(r.status_code, 400)
        self.assertIn("LLM_API_KEY", r.text)


if __name__ == "__main__":
    unittest.main()
