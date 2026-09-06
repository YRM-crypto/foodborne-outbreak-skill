import unittest
import tempfile
from pathlib import Path
from core.store import Store

class TestStore(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.store = Store(Path(self.dir) / "t.db")

    def tearDown(self):
        self.store.close()

    def test_create_and_list_events(self):
        self.store.create_event("EV-001", "学校聚集性胃肠炎", "closed-cohort", "张三")
        events = self.store.list_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["id"], "EV-001")

    def test_audit_timeline_appends(self):
        self.store.create_event("EV-001", "学校聚集性胃肠炎", "closed-cohort", "张三")
        self.store.add_evidence("EV-001", {"id": "E1", "title": "接报记录", "status": "available",
            "text": "接报：多人呕吐腹泻", "locator": "原始记录"}, "张三", "接收材料")
        tl = self.store.timeline("EV-001")
        self.assertGreaterEqual(len(tl), 2)
        self.assertEqual(tl[0]["actor"], "张三")

    def test_bump_revision(self):
        self.store.create_event("EV-001", "学校聚集性胃肠炎", "closed-cohort", "张三")
        rev1 = self.store.get_event("EV-001")["revision"]
        self.store.set_definition("EV-001", {"label": "v1", "text": "定义", "start": "2026-09-01T00:00:00+08:00",
            "end": "2026-09-03T23:59:59+08:00", "symptoms_any": ["呕吐"], "minimum_symptoms": 1}, "张三", "制定定义")
        rev2 = self.store.get_event("EV-001")["revision"]
        self.assertGreater(rev2, rev1)

if __name__ == "__main__":
    unittest.main()
