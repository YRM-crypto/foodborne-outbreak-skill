import unittest
from core.classify import classify

DEF = {"version": 1, "start": "2026-09-01T00:00:00+08:00", "end": "2026-09-03T23:59:59+08:00",
       "symptoms_any": ["呕吐", "腹泻"], "minimum_symptoms": 1, "require_lab": False,
       "locations": [], "populations": []}

class TestClassify(unittest.TestCase):
    def test_case_meets_definition(self):
        p = {"id": "P1", "illness_status": "ill", "onset": "2026-09-01T18:00:00+08:00",
             "symptoms": {"呕吐": True, "腹泻": False}, "lab_eligible": None}
        self.assertEqual(classify(p, DEF)[0], "case")

    def test_well_person_noncase(self):
        p = {"id": "P2", "illness_status": "well", "onset": None, "symptoms": {}}
        self.assertEqual(classify(p, DEF)[0], "noncase")

    def test_no_definition_pending(self):
        self.assertEqual(classify({"id": "P1", "illness_status": "ill"}, None)[0], "pending")

if __name__ == "__main__":
    unittest.main()
