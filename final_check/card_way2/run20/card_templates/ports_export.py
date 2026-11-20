"""Writes the files that carry the ports to the places that need them.

    python -m card_templates.ports_export          rewrite Cards.md and prototype/catalog.js
    python -m card_templates.ports_export --check  exit 1 if either file is out of date

Cards.md keeps its rows (name, category, group, what it does); this module adds the port classes,
the connection rules and the Inputs / Outputs columns. prototype/catalog.js is generated whole.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

from . import REGISTRY, load_all
from .cards_md import DEFAULT_PATH, read_cards_md
from .ports import CLASS_IDS, IMPLICIT_INPUT, IMPLICIT_OUTPUT, PORT_CLASSES, compat_table, port_text, ports_for_card

ROOT = pathlib.Path(__file__).resolve().parent.parent
CATALOG_JS = ROOT / "prototype" / "catalog.js"

CATEGORY_ORDER = [
    ("ui", "UI / Interface"), ("backend", "Backend Processing"), ("data", "Data Modeling / Storage"),
    ("logic", "Logic / Validation"), ("trigger", "Triggers / Orchestration"),
    ("integration", "Integrations / Connectors"), ("ai", "AI Capabilities"), ("output", "Navigation / Output"),
]

# The rules the app enforces when the user links two cards (prototype/ports.js). Same order as the error codes.
CONNECTION_RULES = [
    ("no_such_port", "Both ends must be real: the cards and the ports must exist."),
    ("direction", "A link goes from an output to an input. Two outputs, or two inputs, cannot be linked."),
    ("same_card", "A card cannot be linked to itself."),
    ("type_mismatch", "The classes must match: an output links only to an input of the same colour. "
                      "The grey Any class works both ways (an Any output links to any input, and an Any input accepts any output) "
                      "and is not type checked. "
                      "There are no silent conversions (Number to Text, Record to Record List, and so on)."),
    ("duplicate", "The same two ports cannot be linked twice."),
    ("input_taken", "An input takes one link. A source is replaced only by removing the old link first. "
                    "An input marked + (such as `children+`) takes several links; every linked source is used, "
                    "in the order the links were made. "
                    "An output may feed any number of inputs; each input gets its own copy of the value."),
    ("cycle", "Links may not form a loop. A card cannot, directly or through other cards, feed itself, "
              "because the order of work would then be undefined. "
              "Repeating work is done inside one card (for example Repeat For Each List Item)."),
]
REFUSED_LINK_TEXT = (
    "When a link is refused, nothing is created: the drag is cancelled and the canvas stays as it was. "
    "A red message names both ports, both classes and the rule that was broken. "
    "Both ports flash red, the reason is added to the message list (bottom right of the canvas) and is also written to the "
    "program's console, with the error code and the details. "
    "While you drag a link, the ports it could end on glow green, the others fade, and the line turns red over a port that would be refused.")
EXAMPLE_LINKS = [
    "**Allowed:** the 🟩 `value` output of Enter Text (Text) to the 🟩 `text` input of Trim Whitespace (Text): same colour.",
    "**Allowed:** the 🟫 `records` output of Filter Records By Condition to the 🟫 `records` input of Sort Records By Field: both Record List.",
    "**Allowed:** the 🟥 `view` output of Show Message Banner and the 🟥 `view` output of Show Status Badge, both to the 🟥 `children+` input of Arrange In Grid: an input marked + takes several links.",
    "**Refused (`type_mismatch`):** the 🟥 `view` output of Show Records Table to the 🟦 `value` input of Round Numeric Value: View is not Number.",
    "**Refused (`input_taken`):** a second link to the 🟦 `value` input of Round Numeric Value, which already has one.",
    "**Refused (`cycle`):** the 🟫 `records` output of Sort Records By Field back to the `records` input of the Filter Records By Condition that feeds it.",
]
EXTRA_RULES = [
    "An input marked ? is optional. An input with no mark must be linked, or given a value in the card's settings, "
    "before the project can be generated. When you press Generate, the app lists the open inputs (and a missing or unlinked "
    "App Start, or a missing App End), says where each one is, and asks you to confirm; you may still generate.",
    "Every card except triggers also has a black Start input and a black Done output (square ports, not repeated in the tables). "
    "Done of one card can feed Start of another to say which runs after which. "
    "A trigger card has no Start or Done. Its black `event` output (Control class) fires when the trigger fires: "
    "link it to the Start input of any card, or to the `steps+` or `branches+` input of a flow card, to begin work. "
    "The trigger's yes/no `fire` output is data and cannot be linked to a black Control port.",
    "Two special cards mark where a program begins and ends. App Start (Triggers / Orchestration) is on the canvas when the "
    "app opens; it cannot be deleted and only one is allowed. Its black `event` output starts the first card. App End takes "
    "several links into its black `finish` input, one from each card that ends a path. Neither has a Start or Done port. "
    "Run At App Start is a separate trigger that fires when the preview opens; use App Start as the beginning of the whole program.",
    "Record Lists, Value Lists and Views are separate classes, so a list cannot be linked where one record is expected. "
    "Use a card that turns one into the other (Find First Matching Record, Join Records Into List, Split Text By Separator).",
    "Settings that are typed into a card (a table name, a field name, a limit, a threshold) are not ports. "
    "Only data that comes from another card is a port.",
]


# ---------------------------------------------------------------------------
# Reading the current Cards.md
# ---------------------------------------------------------------------------

def _read_existing(path: pathlib.Path) -> tuple[list[dict], dict[str, str], str]:
    text = path.read_text(encoding="utf8")
    rows = read_cards_md(path)
    traits = {}
    for _, label in CATEGORY_ORDER:
        m = re.search(r"^## " + re.escape(label) + r" \(\d+ cards\)\n\n([^\n]+)\n", text, flags=re.M)
        if not m:
            raise ValueError(f"Cards.md: no section for {label}")
        traits[label] = m.group(1).strip()
    tail = text[text.index("## Where the ideas came from"):]
    return rows, traits, tail


# ---------------------------------------------------------------------------
# Cards.md
# ---------------------------------------------------------------------------

def _ports_cell(ports: list[dict], side: str) -> str:
    listed = [p for p in ports if not p["implicit"]]
    if not listed:
        return "none"
    return "<br>".join(port_text(p, side) for p in listed)


def _read_numbered(path: pathlib.Path) -> tuple[list[dict], dict[str, str], str]:
    """The rows of Cards.md, grouped by category in the usual order and numbered 1, 2, 3 ... in that order.
    A row may be added anywhere inside its category's table; the numbers are given here."""
    rows, traits, tail = _read_existing(path)
    ordered: list[dict] = []
    for _, label in CATEGORY_ORDER:
        ordered += [r for r in rows if r["category"] == label]
    if len(ordered) != len(rows):
        raise ValueError("Cards.md has a row with an unknown category")
    for i, r in enumerate(ordered, 1):
        r["number"] = i
    return ordered, traits, tail


def build_cards_md(path: pathlib.Path = DEFAULT_PATH) -> str:
    load_all()
    rows, traits, tail = _read_numbered(path)
    by_cat: dict[str, list[dict]] = {label: [] for _, label in CATEGORY_ORDER}
    for r in rows:
        by_cat[r["category"]].append(r)
    n_total = len(rows)

    md = "# Cards\n\n"
    md += (f"The {n_total} launch cards of the Visual Programming Project, grouped into 8 categories. "
           "Each card has a name, a category, one sentence on what it does, and its ports. "
           "Ports are the places where a card takes data or a start signal in (inputs) or hands them on (outputs); "
           "cards are built by linking an output of one card to an input of another.\n\n")
    md += ("- Card numbers run in order through this file. They are working numbers and change when cards are added or removed.\n"
           "- Each card sits in exactly one category. The \"Group\" column is a sub-theme inside the category.\n"
           "- The ports come from the Python templates in `card_templates/` (the inputs and outputs of each card function). "
           "This file adds the class of each port. Both are kept in step by tests.\n"
           "- Rules from the framework that shape these cards: the app runs locally for one owner on test data; connectors never call outside services; "
           "AI cards help at build time or take an answer a person brings in; triggers run only while the preview runs; loops live inside one card and are bounded.\n\n")

    md += "## Port classes (colours)\n\n"
    md += ("Every port belongs to one class and is drawn in the colour of its class. "
           "**The colour says only what the port can be linked to. It says nothing about the data that flows through it.** "
           "Ports of the same colour can be linked; ports of different colours cannot. "
           "The emoji in the tables is a rough match; the app uses the exact colour in the Hex column.\n\n")
    md += "| Colour | Class | Hex | Carries | An output of this class links to inputs of |\n| --- | --- | --- | --- | --- |\n"
    compat = compat_table()
    for cid in CLASS_IDS:
        c = PORT_CLASSES[cid]
        targets = ", ".join(f"{PORT_CLASSES[t]['emoji']} {PORT_CLASSES[t]['label']}" for t in compat[cid])
        md += f"| {c['emoji']} {c['colour_name']} | **{c['label']}** (`{cid}`) | `{c['color']}` | {c['carries']} | {targets} |\n"
    md += "\n"

    md += "## Connection rules\n\n"
    md += "The app checks these when a link is made. A link that breaks one is refused, a red message says why, and the reason is also written to the app's message list.\n\n"
    for i, (code, text) in enumerate(CONNECTION_RULES, 1):
        md += f"{i}. {text} (error code `{code}`)\n"
    md += f"\n{REFUSED_LINK_TEXT}\n\nExamples:\n\n"
    for text in EXAMPLE_LINKS:
        md += f"- {text}\n"
    md += "\nMore about ports:\n\n"
    for text in EXTRA_RULES:
        md += f"- {text}\n"
    md += "\nHow ports are written in the tables: the colour emoji, then the port name. `?` after an input means it is optional; `+` means it takes several links. "
    md += "A card with no listed ports has none besides the Start and Done ports.\n\n"

    md += "## Categories\n\n| Category | Cards | Numbers | What the cards share |\n| --- | --- | --- | --- |\n"
    n = 0
    ranges = {}
    for _, label in CATEGORY_ORDER:
        count = len(by_cat[label])
        ranges[label] = (n + 1, n + count)
        md += f"| {label} | {count} | {n + 1:03d}-{n + count:03d} | {traits[label]} |\n"
        n += count
    md += f"| **Total** | **{n_total}** | 001-{n_total:03d} | |\n\n"

    for _, label in CATEGORY_ORDER:
        cards = by_cat[label]
        md += f"## {label} ({len(cards)} cards)\n\n{traits[label]}\n\n"
        md += "| No. | Name | Category | Group | What it does | Inputs | Outputs |\n| --- | --- | --- | --- | --- | --- | --- |\n"
        for c in cards:
            ports = ports_for_card(REGISTRY[c["name"]])
            md += (f"| {c['number']:03d} | {c['name']} | {c['category']} | {c['group']} | {c['description']} | "
                   f"{_ports_cell(ports['inputs'], 'in')} | {_ports_cell(ports['outputs'], 'out')} |\n")
        md += "\n"
    md += tail
    return md


# ---------------------------------------------------------------------------
# prototype/catalog.js
# ---------------------------------------------------------------------------

def _js(value) -> str:
    return json.dumps(value, ensure_ascii=True, indent=None, separators=(", ", ": "))


def build_catalog_js(path: pathlib.Path = DEFAULT_PATH) -> str:
    load_all()
    rows = _read_numbered(path)[0]
    cat_id = {label: cid for cid, label in CATEGORY_ORDER}
    counts = {label: 0 for _, label in CATEGORY_ORDER}
    for r in rows:
        counts[r["category"]] += 1

    out = []
    out.append("// ============================================================================")
    out.append("// CARD CATALOG AND PORT CLASSES  (GENERATED: do not edit by hand)")
    out.append("// ============================================================================")
    out.append("// Written by:  python -m card_templates.ports_export")
    out.append("// Source: Cards.md (names, groups) and card_templates/ (the inputs and outputs of each card).")
    out.append("// Loaded before ports.js and app.js, so the port classes are known when the app starts.")
    out.append("")
    out.append("// Port classes: the colour of a port says what it can be linked to, nothing else.")
    classes = {cid: {"label": c["label"], "color": c["color"], "emoji": c["emoji"], "colourName": c["colour_name"],
                     "carries": c["carries"]} for cid, c in PORT_CLASSES.items()}
    out.append("const PORT_CLASSES = " + json.dumps(classes, ensure_ascii=True, indent=4) + ";")
    out.append("")
    out.append("// Order used for legends and menus.")
    out.append("const PORT_CLASS_ORDER = " + _js(list(CLASS_IDS)) + ";")
    out.append("")
    out.append("// For each output class, the input classes it may link to.")
    out.append("const PORT_COMPAT = " + json.dumps(compat_table(), indent=4) + ";")
    out.append("")
    out.append("// Ports every card except triggers has (not listed in the card's own ports).")
    implicit = {"input": {"id": IMPLICIT_INPUT["name"], "name": IMPLICIT_INPUT["label"], "cls": "control",
                          "optional": True, "multi": False, "implicit": True},
                "output": {"id": IMPLICIT_OUTPUT["name"], "name": IMPLICIT_OUTPUT["label"], "cls": "control",
                           "optional": True, "multi": True, "implicit": True}}
    out.append("const IMPLICIT_PORTS = " + json.dumps(implicit, indent=4) + ";")
    out.append("")
    out.append("const CATEGORIES = [")
    for cid, label in CATEGORY_ORDER:
        out.append("    " + _js({"id": cid, "label": label, "count": counts[label]}) + ",")
    out[-1] = out[-1].rstrip(",")
    out.append("];")
    out.append("")
    out.append("// One entry per card in Cards.md. ids are stable per number: catalog_001 ...")
    out.append("const CATALOG = [")
    for i, r in enumerate(rows):
        spec = REGISTRY[r["name"]]
        ports = ports_for_card(spec)

        def conv(p):
            return {"id": p["name"], "name": p["label"], "cls": p["cls"], "optional": p["optional"],
                    "multi": p["multi"], "implicit": p["implicit"]}

        entry = {"id": f"catalog_{r['number']:03d}", "number": r["number"], "category": cat_id[r["category"]],
                 "group": r["group"], "title": r["name"], "description": r["description"], "role": spec.role,
                 "ports": {"inputs": [conv(p) for p in ports["inputs"]], "outputs": [conv(p) for p in ports["outputs"]]}}
        out.append("    " + _js(entry) + ("," if i < len(rows) - 1 else ""))
    out.append("];")
    out.append("")
    out.append("function getCategory(categoryID) {")
    out.append("    return CATEGORIES.find(c => c.id === categoryID);")
    out.append("}")
    out.append("")
    out.append("function getCatalogCard(catalogID) {")
    out.append("    return CATALOG.find(c => c.id === catalogID);")
    out.append("}")
    out.append("")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    new_md, new_js = build_cards_md(), build_catalog_js()
    if "--check" in argv:
        stale = []
        if DEFAULT_PATH.read_text(encoding="utf8") != new_md:
            stale.append("Cards.md")
        if CATALOG_JS.read_text(encoding="utf8") != new_js:
            stale.append("prototype/catalog.js")
        for name in stale:
            print("out of date:", name)
        return 1 if stale else 0
    DEFAULT_PATH.write_text(new_md, encoding="utf8", newline="\n")
    CATALOG_JS.write_text(new_js, encoding="utf8", newline="\n")
    print(f"wrote {DEFAULT_PATH.name} and {CATALOG_JS.name} ({len(REGISTRY)} cards)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
