"""Tests for the ports of the cards: classes, Cards.md, the generated catalog and the app's rules."""
import inspect
import json
import pathlib
import re
import shutil
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from card_templates import REGISTRY, load_all  # noqa: E402
from card_templates import ports as P  # noqa: E402
from card_templates import ports_export  # noqa: E402
from card_templates.cards_md import read_cards_md  # noqa: E402
from card_templates.manifest import build_manifest  # noqa: E402

load_all()
CARDS = read_cards_md()


def listed(ports):
    return [p for p in ports if not p["implicit"]]


class Classes(unittest.TestCase):
    def test_ten_classes_with_their_own_colours(self):
        self.assertEqual(len(P.PORT_CLASSES), 10)
        colours = [c["color"] for c in P.PORT_CLASSES.values()]
        self.assertEqual(len(set(colours)), len(colours))
        self.assertTrue(all(re.fullmatch(r"#[0-9a-f]{6}", c) for c in colours))
        emojis = [c["emoji"] for c in P.PORT_CLASSES.values()]
        self.assertEqual(len(set(emojis)), len(emojis))

    def test_compatibility_is_same_class_or_any(self):
        for o in P.CLASS_IDS:
            for i in P.CLASS_IDS:
                self.assertEqual(P.classes_compatible(o, i), o == i or P.ANY in (o, i), (o, i))
        self.assertFalse(P.classes_compatible("text", "nope"))
        self.assertFalse(P.classes_compatible("nope", "text"))

    def test_same_colour_means_compatible(self):
        """The rule the colours stand for: two ports with the same colour can always be linked."""
        for a in P.CLASS_IDS:
            self.assertTrue(P.classes_compatible(a, a))

    def test_compat_table_is_a_function_of_the_rule(self):
        table = P.compat_table()
        for o in P.CLASS_IDS:
            self.assertEqual(table[o], [i for i in P.CLASS_IDS if P.classes_compatible(o, i)])


class CardPorts(unittest.TestCase):
    def test_every_port_of_every_card_has_a_class(self):
        for name, spec in REGISTRY.items():
            ports = P.ports_for_card(spec)
            self.assertEqual([p["name"] for p in listed(ports["inputs"])], list(spec.inputs), name)
            self.assertEqual([p["name"] for p in listed(ports["outputs"])], list(spec.outputs), name)
            for p in ports["inputs"] + ports["outputs"]:
                self.assertIn(p["cls"], P.PORT_CLASSES, f"{name}.{p['name']}")

    def test_no_stale_overrides(self):
        self.assertEqual(P.stale_overrides(REGISTRY), [])

    def test_optional_inputs_follow_the_function_signature(self):
        for name, spec in REGISTRY.items():
            params = inspect.signature(spec.func).parameters
            for p in listed(P.ports_for_card(spec)["inputs"]):
                self.assertEqual(p["optional"], params[p["name"]].default is not inspect.Parameter.empty, f"{name}.{p['name']}")

    def test_implicit_control_ports(self):
        for name, spec in REGISTRY.items():
            ports = P.ports_for_card(spec)
            implicit_in = [p for p in ports["inputs"] if p["implicit"]]
            implicit_out = [p for p in ports["outputs"] if p["implicit"]]
            if spec.role in ("trigger", "start", "end"):
                self.assertEqual((implicit_in, implicit_out), ([], []), name)
                side = ports["inputs"] if spec.role == "end" else ports["outputs"]
                self.assertTrue(any(p["cls"] == "control" for p in side), f"{name}: needs a control port")
            else:
                self.assertEqual([p["name"] for p in implicit_in], ["_start"], name)
                self.assertEqual([p["name"] for p in implicit_out], ["_done"], name)
                self.assertTrue(all(p["cls"] == "control" for p in implicit_in + implicit_out), name)

    def test_meaning_of_the_classes(self):
        """Spot checks that the colours match what the ports carry."""
        for name, spec in REGISTRY.items():
            ports = P.ports_for_card(spec)
            for p in ports["outputs"]:
                if p["implicit"]:
                    continue
                if p["name"] == "view":
                    self.assertEqual(p["cls"], "view", name)
                is_yes_no_name = p["name"] in ("fire", "found", "valid", "ok", "success", "logged", "proceed", "stopped")
                if is_yes_no_name and name != "Collect Error Records":   # that card's "valid" is the list of good records
                    self.assertEqual(p["cls"], "flag", f"{name}.{p['name']}")
                if p["name"] == "event":
                    self.assertEqual(p["cls"], "control", name)
                if p["name"] in ("count", "total", "sum", "average", "minimum", "maximum"):
                    self.assertEqual(p["cls"], "number", f"{name}.{p['name']}")
                if spec.role == "route":   # the Yes/No branch passes on any class of value, the others a record
                    self.assertEqual(p["cls"], "any" if name == "Branch On Yes/No" else "record", f"{name}.{p['name']}")
            if spec.category == "UI / Interface":
                self.assertTrue(any(p["cls"] == "view" for p in ports["outputs"]), f"{name}: a UI card outputs a view")

    def test_ports_that_take_several_links(self):
        multi = {(n, p["name"]) for n, s in REGISTRY.items() for p in P.ports_for_card(s)["inputs"] if p["multi"] and not p["implicit"]}
        self.assertEqual(multi, {("Arrange In Grid", "children"), ("Stack In Panel", "children"), ("Split Into Columns", "children"),
                                 ("Collapse Section", "children"), ("Run Steps In Sequence", "steps"), ("App End", "finish"),
                                 ("Wait For All Steps To Complete", "branches")})

    def test_any_is_used_sparingly(self):
        """The wildcard switches type checking off, so it must stay rare and only where the data really varies."""
        used = [(n, p["name"]) for n, s in REGISTRY.items()
                for p in listed(P.ports_for_card(s)["inputs"] + P.ports_for_card(s)["outputs"]) if p["cls"] == "any"]
        self.assertLessEqual(len(used), 32, used)


class Manifest(unittest.TestCase):
    def test_manifest_carries_the_ports(self):
        manifest = build_manifest()
        for entry in manifest["cards"]:
            self.assertEqual(entry["ports"], P.ports_for_card(REGISTRY[entry["name"]]), entry["name"])
        self.assertEqual(json.loads((ROOT / "card_templates" / "manifest.json").read_text(encoding="utf8")), manifest)


class CardsMd(unittest.TestCase):
    TEXT = (ROOT / "Cards.md").read_text(encoding="utf8")

    def test_file_is_up_to_date(self):
        self.assertEqual(self.TEXT, ports_export.build_cards_md(), "run: python -m card_templates.ports_export")

    def test_every_class_and_every_rule_is_described(self):
        for cid, c in P.PORT_CLASSES.items():
            self.assertIn(f"`{c['color']}`", self.TEXT, cid)
            self.assertIn(f"**{c['label']}** (`{cid}`)", self.TEXT, cid)
        for code, _ in ports_export.CONNECTION_RULES:
            self.assertIn(f"`{code}`", self.TEXT)
        self.assertIn("## Connection rules", self.TEXT)
        self.assertIn("## Port classes (colours)", self.TEXT)

    def test_every_card_row_lists_its_ports(self):
        rows = [l for l in self.TEXT.splitlines() if re.match(r"^\| \d{3} \|", l)]
        self.assertEqual(len(rows), len(REGISTRY))
        for line in rows:
            cells = [c.strip() for c in line.split("|")[1:-1]]
            self.assertEqual(len(cells), 7, line)
            spec = REGISTRY[cells[1]]
            ports = P.ports_for_card(spec)
            for cell, side in ((cells[5], "in"), (cells[6], "out")):
                expected = [P.port_text(p, side) for p in listed(ports["inputs" if side == "in" else "outputs"])]
                self.assertEqual(cell.split("<br>") if cell != "none" else [], expected, spec.name)

    def test_one_line_about_each_category_is_still_there(self):
        for _, label in ports_export.CATEGORY_ORDER:
            self.assertRegex(self.TEXT, r"## " + re.escape(label) + r" \(\d+ cards\)\n\n[^\n|]{20,}\n")

    def test_still_the_same_cards(self):
        self.assertEqual(sorted(c["name"] for c in CARDS), sorted(REGISTRY))


class GeneratedCatalog(unittest.TestCase):
    def test_catalog_js_is_up_to_date(self):
        self.assertEqual((ROOT / "prototype" / "catalog.js").read_text(encoding="utf8"), ports_export.build_catalog_js(),
                         "run: python -m card_templates.ports_export")

    def test_export_check_passes(self):
        self.assertEqual(ports_export.main(["--check"]), 0)


@unittest.skipUnless(shutil.which("node"), "node is not installed")
class AppRules(unittest.TestCase):
    def test_javascript_rules_pass(self):
        run = subprocess.run(["node", str(ROOT / "tests" / "ports_logic.test.js")], capture_output=True, text=True, timeout=120)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertRegex(run.stdout, r"\d+ passed, 0 failed")

    def test_javascript_agrees_with_python_on_every_class_pair(self):
        script = (
            "const vm=require('vm'),fs=require('fs');const c=vm.createContext({});"
            "for(const f of ['catalog.js','ports.js'])vm.runInContext(fs.readFileSync('prototype/'+f,'utf8'),c);"
            "const o=vm.runInContext('PORT_CLASS_ORDER',c);const out={};"
            "for(const a of o){out[a]=[];for(const b of o)if(vm.runInContext('classesCompatible',c)(a,b))out[a].push(b);}"
            "console.log(JSON.stringify(out));")
        run = subprocess.run(["node", "-e", script], capture_output=True, text=True, cwd=ROOT, timeout=60)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(json.loads(run.stdout), P.compat_table())


if __name__ == "__main__":
    unittest.main()
