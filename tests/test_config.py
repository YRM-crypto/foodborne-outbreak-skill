import unittest
from core.deidentify import scrub

class TestDeidentify(unittest.TestCase):
    def test_scrub_phone_and_id(self):
        t = "患者张三，电话13812345678，身份证110105199001011234"
        out = scrub(t)
        self.assertNotIn("13812345678", out)
        self.assertNotIn("199001011234", out)
        self.assertIn("[脱敏", out)

    def test_noop_when_clean(self):
        t = "本次事件涉及诺如病毒，潜伏期8到48小时。"
        self.assertEqual(scrub(t), t)

if __name__ == "__main__":
    unittest.main()
