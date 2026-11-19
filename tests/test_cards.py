"""Tests for the card templates (run:  python -m unittest discover -s tests -v)

* the templates and Cards.md list exactly the same cards
* every card runs its own examples and invalid cases (card_templates.testing)
* house rules, checked by reading the source: standard library only, no outside calls,
  no file access, no dynamic code, no clock or random outside ctx
"""
import ast
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from card_templates import REGISTRY, load_all, testing  # noqa: E402
from card_templates.cards_md import read_cards_md  # noqa: E402
from card_templates.manifest import build_manifest  # noqa: E402
from card_templates.runtime import snake  # noqa: E402

load_all()
CARDS_MD = read_cards_md()
PACKAGE = ROOT / "card_templates"
CARD_FILES = sorted(p for d in PACKAGE.iterdir() if d.is_dir() and d.name != "__pycache__"
                    for p in d.glob("*.py") if p.name != "__init__.py")

ALLOWED_IMPORTS = {"__future__", "re", "json", "csv", "io", "math", "datetime", "decimal", "itertools", "collections",
                   "statistics", "textwrap", "string", "typing", "dataclasses", "functools", "operator", "calendar",
                   "unicodedata", "difflib", "fractions", "heapq", "bisect", "copy", "uuid_not_allowed"}
FORBIDDEN_NAMES = {"eval", "exec", "compile", "open", "__import__", "input", "globals", "locals", "getattr", "setattr",
                   "delattr", "breakpoint", "exit", "quit"}
FORBIDDEN_ATTRS = {"now", "today", "utcnow", "random", "randint", "choice", "shuffle", "sleep", "system", "popen",
                   "urlopen", "connect", "listdir", "mkdir", "remove", "unlink", "rmtree", "walk"}


class SyncWithCardsMd(unittest.TestCase):
    def test_same_cards(self):
        md = {c["name"]: c for c in CARDS_MD}
        self.assertEqual(len(CARDS_MD), len(md), "Cards.md has repeated names")
        self.assertEqual(sorted(REGISTRY), sorted(md), "templates and Cards.md list different cards")

    def test_category_and_group_match(self):
        for c in CARDS_MD:
            spec = REGISTRY[c["name"]]
            self.assertEqual((spec.category, spec.group), (c["category"], c["group"]), c["name"])

    def test_function_name_is_the_card_name(self):
        for name, spec in REGISTRY.items():
            self.assertEqual(spec.func.__name__, snake(name), name)

    def test_module_path_follows_category_and_group(self):
        folder = {"UI / Interface": "ui", "Backend Processing": "backend", "Data Modeling / Storage": "data",
                  "Logic / Validation": "logic", "Triggers / Orchestration": "triggers",
                  "Integrations / Connectors": "integrations", "AI Capabilities": "ai", "Navigation / Output": "output"}
        for name, spec in REGISTRY.items():
            self.assertEqual(spec.module, f"card_templates.{folder[spec.category]}.{snake(spec.group)}", name)

    def test_manifest_lists_every_card_in_card_order(self):
        manifest = build_manifest()
        self.assertEqual(manifest["count"], len(CARDS_MD))
        self.assertEqual([c["name"] for c in manifest["cards"]], [c["name"] for c in CARDS_MD])
        json.dumps(manifest)

    def test_committed_manifest_is_current(self):
        committed = json.loads((PACKAGE / "manifest.json").read_text(encoding="utf8"))
        self.assertEqual(committed, build_manifest(), "run: python -m card_templates.manifest")


class EveryCardRuns(unittest.TestCase):
    def test_all_examples_and_invalid_cases(self):
        results = testing.run_all()
        bad = {k: v for k, v in results.items() if v}
        self.assertEqual(bad, {}, "\n" + "\n".join(f"{k}: {v[:3]}" for k, v in bad.items()))

    def test_every_card_has_enough_cases(self):
        for name, spec in REGISTRY.items():
            self.assertGreaterEqual(len(spec.examples), 2, f"{name}: needs 2 examples")
            if spec.inputs or spec.config:
                self.assertGreaterEqual(len(spec.invalid), 1, f"{name}: needs an invalid case")

    def test_cases_are_labelled_and_distinct(self):
        for name, spec in REGISTRY.items():
            labels = [c.get("label") for c in spec.examples + spec.invalid]
            self.assertTrue(all(labels), f"{name}: every case needs a label")
            self.assertEqual(len(labels), len(set(labels)), f"{name}: two cases share a label")

    def test_trigger_cards_refuse_to_run_outside_preview(self):
        triggers = [s for s in REGISTRY.values() if s.role == "trigger"]
        self.assertGreaterEqual(len(triggers), 10)
        for spec in triggers:
            self.assertTrue(any(c.get("preview") is False and c["code"] == "preview_only" for c in spec.invalid),
                            f"{spec.name}: needs an invalid case with preview False")

    def test_phase_rules(self):
        for name, spec in REGISTRY.items():
            if spec.category == "AI Capabilities":
                self.assertIn(spec.phase, ("generation", "human"), name)
            if spec.category == "Integrations / Connectors":
                self.assertEqual(spec.phase, "human", name)

    def test_ui_cards_return_views(self):
        for name, spec in REGISTRY.items():
            if spec.category == "UI / Interface":
                self.assertIn("view", spec.outputs, name)
                self.assertEqual(spec.role, "view", name)

    def test_route_cards_declare_a_no_match_port(self):
        routes = [s for s in REGISTRY.values() if s.role == "route"]
        self.assertGreaterEqual(len(routes), 6)
        two_way = {"Route By Field Presence", "Route By List Membership", "Route By Date Comparison", "Branch On Yes/No"}  # every record fits one port
        for spec in routes:
            if spec.name not in two_way:
                self.assertIn("no_match", spec.outputs, spec.name)


class SourceRules(unittest.TestCase):
    def test_source_rules(self):
        problems = []
        for path in CARD_FILES:
            rel = path.relative_to(PACKAGE).as_posix()
            tree = ast.parse(path.read_text(encoding="utf8"), filename=rel)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.split(".")[0] not in ALLOWED_IMPORTS:
                            problems.append(f"{rel}:{node.lineno}: import {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    if node.level == 0 and (node.module or "").split(".")[0] not in ALLOWED_IMPORTS:
                        problems.append(f"{rel}:{node.lineno}: from {node.module} import ...")
                    if node.level == 1 and node.module is not None:
                        problems.append(f"{rel}:{node.lineno}: cards may not import sibling modules ({node.module})")
                    if node.level == 2 and node.module != "runtime":
                        problems.append(f"{rel}:{node.lineno}: only ..runtime may be imported")
                elif isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
                    problems.append(f"{rel}:{node.lineno}: uses {node.id}")
                elif isinstance(node, ast.Attribute) and node.attr in FORBIDDEN_ATTRS:
                    # ctx.now() / ctx.today() are the only clocks; datetime.now etc. are not allowed
                    base = node.value.id if isinstance(node.value, ast.Name) else ""
                    if not (base == "ctx" and node.attr in ("now", "today")):
                        problems.append(f"{rel}:{node.lineno}: uses .{node.attr}")
                elif isinstance(node, (ast.Global, ast.Nonlocal)):
                    problems.append(f"{rel}:{node.lineno}: global state")
        self.assertEqual(problems, [], "\n" + "\n".join(problems))

    def test_every_module_has_a_docstring_and_constants(self):
        for path in CARD_FILES:
            tree = ast.parse(path.read_text(encoding="utf8"))
            self.assertTrue(ast.get_docstring(tree), f"{path.name}: module docstring")
            names = {t.id for n in tree.body if isinstance(n, ast.Assign) for t in n.targets if isinstance(t, ast.Name)}
            self.assertTrue({"CATEGORY", "GROUP"} <= names, f"{path.name}: CATEGORY and GROUP constants")

    def test_no_card_module_keeps_mutable_state(self):
        for path in CARD_FILES:
            tree = ast.parse(path.read_text(encoding="utf8"))
            for n in tree.body:
                if isinstance(n, ast.Assign) and isinstance(n.value, (ast.List, ast.Dict, ast.Set)):
                    names = [t.id for t in n.targets if isinstance(t, ast.Name)]
                    self.assertTrue(all(x.isupper() for x in names), f"{path.name}: module-level {names}")

    def test_line_length_is_readable(self):
        for path in CARD_FILES:
            for i, line in enumerate(path.read_text(encoding="utf8").splitlines(), 1):
                self.assertLessEqual(len(line), 300, f"{path.name}:{i}")


if __name__ == "__main__":
    unittest.main()
