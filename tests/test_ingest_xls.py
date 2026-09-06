import unittest
from kb.ingest_xls import normalize_row, event_to_text, load_xls_events

SAMPLE = {"卡号": "CARD001", "致病因素类别": "生物性_细菌性_副溶血性弧菌", "致病因素名称": "副溶血性弧菌",
          "原因食品名称": "海产品", "疾病暴发场所类型": "家庭", "发病人数": 12, "暴露人数": 20,
          "恶心": 5, "呕吐": 8, "腹痛": 10, "腹泻": 11, "发生日期": "2025-01-01", "疾病暴发地区": "某市"}

class TestIngestXls(unittest.TestCase):
    def test_normalize_extracts_agent_food_venue(self):
        e = normalize_row(SAMPLE)
        self.assertEqual(e["agent_name"], "副溶血性弧菌")
        self.assertEqual(e["food_name"], "海产品")
        self.assertEqual(e["venue"], "家庭")
        self.assertEqual(e["case_count"], 12)

    def test_event_to_text_has_keywords(self):
        e = normalize_row(SAMPLE)
        t = event_to_text(e)
        self.assertIn("副溶血性弧菌", t)
        self.assertIn("海产品", t)
        self.assertIn("家庭", t)

    def test_load_missing_returns_empty(self):
        self.assertEqual(load_xls_events("/nonexistent.xls"), [])

if __name__ == "__main__":
    unittest.main()
