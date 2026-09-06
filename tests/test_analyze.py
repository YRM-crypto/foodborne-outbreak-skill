import unittest
from core.analyze import analyze

def _event():
    return {
        "event": {"id": "EV", "title": "学校聚集性胃肠炎", "timezone": "Asia/Shanghai", "population_complete": 0,
                  "population_size": None, "data_cutoff": None},
        "definition": {"version": 1, "text": "本次事件病例定义",
                       "start": "2026-09-01T00:00:00+08:00", "end": "2026-09-03T23:59:59+08:00",
                       "symptoms_any": ["呕吐", "腹泻"], "minimum_symptoms": 1, "require_lab": False,
                       "locations": [], "populations": []},
        "people": [
            {"id": "P1", "illness_status": "ill", "onset": "2026-09-01T18:00:00+08:00",
             "symptoms": {"呕吐": True, "腹泻": True}, "sex": "male", "age": 12,
             "recovery": "2026-09-02T12:00:00+08:00"},
            {"id": "P2", "illness_status": "well", "onset": None, "symptoms": {}, "sex": "female", "age": 13},
        ],
        "exposures": [{"id": "X1", "person_id": "P1", "meal_id": "M1", "food_id": "F1",
                       "consumed": True, "ate_at": "2026-09-01T12:00:00+08:00", "incubation_anchor": True},
                      {"id": "X2", "person_id": "P2", "meal_id": "M1", "food_id": "F1",
                       "consumed": False, "ate_at": None, "incubation_anchor": False}],
        "samples": [], "evidence": [], "conclusions": [], "confirmations": {},
    }

class TestAnalyze(unittest.TestCase):
    def test_counts_and_incubation(self):
        r = analyze(_event())
        self.assertEqual(r["counts"]["case"], 1)
        self.assertEqual(r["counts"]["noncase"], 1)
        self.assertEqual(r["incubation"]["n"], 1)
        self.assertAlmostEqual(r["incubation"]["median"], 6.0)

if __name__ == "__main__":
    unittest.main()
