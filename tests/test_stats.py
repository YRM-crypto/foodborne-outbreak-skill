import unittest
from core.stats import proportion, duration_summary, two_by_two

class TestStats(unittest.TestCase):
    def test_proportion_wilson(self):
        r = proportion(2, 4)
        self.assertAlmostEqual(r["value"], 0.5)
        self.assertIsNotNone(r["ci95"])

    def test_duration_median(self):
        r = duration_summary([8, 12, 24])
        self.assertEqual(r["median"], 12)
        self.assertEqual(r["n"], 3)

    def test_two_by_two_rr(self):
        r = two_by_two(10, 5, 1, 20, design="cohort")
        self.assertEqual(r["measure"], "RR")
        self.assertGreater(r["effect"], 1)

if __name__ == "__main__":
    unittest.main()
