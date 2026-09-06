import unittest
from core.report import render_markdown
from tests.test_analyze import _event

class TestReport(unittest.TestCase):
    def test_render_includes_counts_and_conclusions(self):
        state = _event()
        state["conclusions"] = [{"topic": "agent", "status": "supported",
            "statement": "疑似诺如病毒感染", "reason": "潜伏期与临床表现符合",
            "limitations": "无实验室确认", "evidence_ids": ["E1"]}]
        from core.analyze import analyze
        md = render_markdown(state, analyze(state), "progress")
        self.assertIn("符合调查病例定义 1 人", md)
        self.assertIn("疑似诺如病毒感染", md)
        self.assertIn("E1", md)

if __name__ == "__main__":
    unittest.main()
