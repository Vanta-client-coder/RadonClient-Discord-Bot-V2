import unittest
from pathlib import Path

class DeploySafetyTests(unittest.TestCase):
    def test_render_unbuffered_and_no_auto_deploy(self):
        content = Path(__file__).with_name("render.yaml").read_text()
        self.assertIn("startCommand: python -u bot.py", content)
        self.assertIn("autoDeploy: false", content)

    def test_no_secret_in_gitignore(self):
        content = Path(__file__).with_name(".gitignore").read_text()
        self.assertIn(".env", content)
        self.assertIn("data/*.db", content)

if __name__ == "__main__":
    unittest.main()
