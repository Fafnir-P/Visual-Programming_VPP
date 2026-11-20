"""cards.py written by the app (prototype/bedrock.js assembleCardsModule) is valid Python."""
import importlib.util
import json
import pathlib
import py_compile
import shutil
import subprocess
import sys
import tempfile
import unittest

from card_templates import REGISTRY, load_all

ROOT = pathlib.Path(__file__).resolve().parent.parent


@unittest.skipUnless(shutil.which("node"), "node not installed")
class AssembledCardsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        r = subprocess.run(["node", str(ROOT / "tests" / "assemble_cards.js"), cls.tmp.name],
                           capture_output=True, text=True, check=True)
        cls.info = json.loads(r.stdout)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def _load(self, name):
        path = pathlib.Path(self.tmp.name) / name
        py_compile.compile(str(path), doraise=True)
        sys.path.insert(0, str(ROOT))
        try:
            spec = importlib.util.spec_from_file_location("assembled_" + path.stem, path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
        finally:
            sys.path.remove(str(ROOT))
        return path.read_text(encoding="utf8"), mod

    def test_seven_card_module_compiles_and_runs(self):
        text, mod = self._load("cards_7.py")
        for fn in self.info["functions7"]:
            self.assertEqual(text.count(f"def {fn}("), 1, fn)
        self.assertNotIn("def app_start", text)
        self.assertNotIn("def app_end", text)
        from card_templates.runtime import Context, Store
        ctx = Context(store=Store())
        self.assertEqual(mod.trim_whitespace(ctx, text="  hi ")["text"], "hi")
        self.assertEqual(mod.change_text_case(ctx, text="hi", case="upper")["text"], "HI")

    def test_every_card_assembles_once_and_compiles(self):
        load_all()
        text, mod = self._load("cards_all.py")
        for title, spec in REGISTRY.items():
            if title in ("App Start", "App End"):
                continue
            fn = spec.func.__name__
            self.assertEqual(text.count(f"\ndef {fn}("), 1, title)
            self.assertTrue(callable(getattr(mod, fn)), title)


if __name__ == "__main__":
    unittest.main()
