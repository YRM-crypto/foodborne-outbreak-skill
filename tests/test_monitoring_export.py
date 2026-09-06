import unittest
from integration.monitoring_export import export_monitoring_json
from tests.test_analyze import _event

class TestMonitoringExport(unittest.TestCase):
    def test_export_maps_event_fields(self):
        state = _event()
        out = export_monitoring_json(state)
        self.assertEqual(out["事件编号"], "EV")
        self.assertEqual(out["发病人数"], 1)
        self.assertIn("症状", out)
        self.assertIn("致病因素", out)

if __name__ == "__main__":
    unittest.main()
