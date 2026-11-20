"""The order-line project written by the app (no model) meets the four checks.

Node writes cards.py and main.py from final_check/orderline/graph.json (tests/write_orderline.js).
The project is copied next to a copy of card_templates, so main.py finds it the way a user's folder would.
"""
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent


@unittest.skipUnless(shutil.which("node"), "node not installed")
class OrderLineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.dir = pathlib.Path(cls.tmp.name)
        shutil.copytree(ROOT / "card_templates", cls.dir / "card_templates",
                        ignore=shutil.ignore_patterns("__pycache__"))
        r = subprocess.run(["node", str(ROOT / "tests" / "write_orderline.js"), str(cls.dir)],
                           capture_output=True, text=True, check=True)
        cls.info = json.loads(r.stdout)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def run_main(self, *args):
        return subprocess.run([sys.executable, str(self.dir / "main.py"), *args], capture_output=True, text=True)

    def test_compiled_without_gaps(self):
        self.assertTrue(self.info["ok"], self.info["gaps"])
        self.assertEqual(self.info["files"], ["cards.py", "main.py"])

    def test_c1_output(self):
        p = self.run_main("--customer", "  ada lovelace ", "--qty", "3", "--price", "2.5")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout.strip(), '{"customer": "Ada Lovelace", "total": "$7.50"}')

    def test_c2_blank_customer(self):
        p = self.run_main("--customer", "   ", "--qty", "1", "--price", "1")
        self.assertEqual(p.returncode, 1)
        self.assertEqual(p.stdout, "")
        self.assertEqual(len(p.stderr.strip().splitlines()), 1, p.stderr)
        self.assertNotIn("Traceback", p.stderr)

    def test_c3_repeatable(self):
        a = self.run_main("--customer", "bob", "--qty", "2", "--price", "1.25")
        b = self.run_main("--customer", "bob", "--qty", "2", "--price", "1.25")
        self.assertEqual((a.returncode, a.stdout), (0, b.stdout))
        self.assertEqual(a.stdout, b.stdout)

    def test_c4_bad_number(self):
        p = self.run_main("--customer", "x", "--qty", "abc", "--price", "1")
        self.assertEqual(p.returncode, 1)
        self.assertEqual(p.stdout, "")
        self.assertEqual(len(p.stderr.strip().splitlines()), 1, p.stderr)
        self.assertNotIn("Traceback", p.stderr)

    def test_missing_flag_named(self):
        p = self.run_main("--customer", "bob")
        self.assertEqual(p.returncode, 1)
        self.assertEqual(p.stdout, "")
        lines = p.stderr.strip().splitlines()
        self.assertEqual(len(lines), 1, p.stderr)
        self.assertIn("--qty", lines[0])
        self.assertIn("--price", lines[0])

    def test_missing_qty_only(self):
        p = self.run_main("--customer", "bob", "--price", "1")
        self.assertEqual(p.returncode, 1)
        self.assertEqual(p.stdout, "")
        self.assertEqual(len(p.stderr.strip().splitlines()), 1, p.stderr)
        self.assertIn("--qty", p.stderr)
        self.assertNotIn("--price", p.stderr)

    def test_bad_number_names_flag(self):
        p = self.run_main("--customer", "x", "--qty", "abc", "--price", "1")
        self.assertEqual(p.stderr.strip(), "--qty must be a number")


if __name__ == "__main__":
    unittest.main()