import ast
import builtins
import unittest

from card_templates import REGISTRY, load_all
from card_templates import templates_export


class TemplatesExportTest(unittest.TestCase):
    def test_templates_js_is_up_to_date(self):
        # fix with: python -m card_templates.templates_export
        self.assertEqual(templates_export.main(["--check"]), 0)

    def test_entry_is_small_and_complete(self):
        load_all()
        for title, spec in REGISTRY.items():
            entry = templates_export.build_entry(spec)
            self.assertTrue(entry["source"].startswith("def "), title)
            self.assertNotIn("@card", entry["source"], title)
            self.assertNotIn("examples=", entry["source"], title)
            self.assertEqual(entry["inputs"], list(spec.inputs), title)
            self.assertEqual([s["name"] for s in entry["settings"]], list(spec.config), title)

    def test_no_undefined_names_in_any_template(self):
        # helpers + source must compile and use only: builtins, own defs, runtime names, listed imports
        load_all()
        bad = {}
        for title, spec in REGISTRY.items():
            e = templates_export.build_entry(spec)
            code = "\n\n".join([i for i in e["imports"]] + [h["source"] for h in e.get("helpers", [])] + [e["source"]])
            tree = ast.parse(code)
            defined = set(dir(builtins)) | set(e["runtime"])
            used = set()
            for n in ast.walk(tree):
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    defined.add(n.name)
                elif isinstance(n, ast.arg):
                    defined.add(n.arg)
                elif isinstance(n, ast.Name):
                    (used if isinstance(n.ctx, ast.Load) else defined).add(n.id)
                elif isinstance(n, ast.ExceptHandler) and n.name:
                    defined.add(n.name)
                elif isinstance(n, (ast.Import, ast.ImportFrom)):
                    defined.update((a.asname or a.name).split(".")[0] for a in n.names)
            missing = sorted(used - defined)
            if missing:
                bad[title] = missing
        self.assertEqual(bad, {})

    def test_known_cross_names(self):
        load_all()
        self.assertIn("iso", templates_export.build_entry(REGISTRY["Shift Date By Time"])["runtime"])
        self.assertIn("check_identifier", templates_export.build_entry(REGISTRY["Define App Settings"])["runtime"])

    def test_start_and_end_have_templates(self):
        load_all()
        self.assertIn("App Start", REGISTRY)
        self.assertIn("App End", REGISTRY)


if __name__ == "__main__":
    unittest.main()
