import unittest
from assistant.client import ChatClient, LLMUnavailable
from assistant.orchestrator import Orchestrator, render_gaps, render_similar

class FakeClient:
    def __init__(self, reply="", enabled=True):
        self.reply = reply; self.enabled = enabled; self.calls = []
    def complete(self, messages, **kw):
        self.calls.append(messages); return self.reply

class TestAssistant(unittest.TestCase):
    def test_disabled_client_raises(self):
        c = ChatClient("", "", "x", enabled=False)
        with self.assertRaises(LLMUnavailable):
            c.complete([{"role": "user", "content": "hi"}])

    def test_render_gaps_anchors_basis(self):
        out = render_gaps([{"title": "制定病例定义", "why": "统一纳入标准", "table": "病例定义记录", "basis": "S2012 §4.2"}])
        self.assertIn("S2012 §4.2", out)

    def test_similar_offline_fallback(self):
        o = Orchestrator(FakeClient(enabled=False))
        hits = [{"text": "集体用餐后呕吐腹泻"}]
        self.assertIn("集体用餐后呕吐腹泻", o.similar("学校聚集", hits))
        self.assertFalse(o.client.calls)

if __name__ == "__main__":
    unittest.main()
