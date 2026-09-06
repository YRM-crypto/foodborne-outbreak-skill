import unittest
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import create_app

class TestWeb(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.app = create_app(db_path=str(Path(self.dir) / "t.db"),
                              vector_db_path=str(Path(self.dir) / "v.db"),
                              xls_path="/nonexistent.xls")
        self.client = TestClient(self.app)

    def test_list_and_create(self):
        self.client.post("/investigations/new", data={
            "id": "EV-001", "title": "学校聚集性胃肠炎", "scenario": "closed-cohort", "lead": "张三"})
        r2 = self.client.get("/investigations")
        self.assertEqual(r2.status_code, 200)
        self.assertIn("EV-001", r2.text)
        self.assertIn("学校聚集性胃肠炎", r2.text)

    def test_event_page_timeline(self):
        self.client.post("/investigations/new", data={
            "id": "EV-001", "title": "学校聚集性胃肠炎", "scenario": "closed-cohort", "lead": "张三"})
        r = self.client.get("/investigations/EV-001")
        self.assertEqual(r.status_code, 200)
        self.assertIn("建立事件档案", r.text)

if __name__ == "__main__":
    unittest.main()
