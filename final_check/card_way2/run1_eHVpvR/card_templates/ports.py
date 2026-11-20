"""Port classes and the ports of every card (single source for Cards.md and the app).

A *port* is a place on a card where a link starts (output) or ends (input).
Every port belongs to one *class*. The class decides which links are allowed and
the colour the app draws the port in:

    a link is allowed when the output class and the input class are the same class,
    or when either side is the wildcard class ``any``.

The colour only says what can be linked. It says nothing about the data that flows.

Where the names come from: the ports of a card are the ``inputs`` and ``outputs`` of its
template (``@card(inputs=[...], outputs=[...])``). This module adds the class of each port.
Names that mean the same thing everywhere have a default class below; the other
names are set per card in ``CARD_OVERRIDES``.

Two extra control ports exist on every card except triggers, App Start and App End. They are not listed per card:
``_start`` (in) says "run after" and ``_done`` (out) says "this has finished".
"""
from __future__ import annotations

import inspect
from typing import Any

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------

ANY = "any"

# id -> label, emoji (a rough match for the colour in Cards.md), colour for the app, what it carries
PORT_CLASSES: dict[str, dict[str, str]] = {
    "text": {"label": "Text", "emoji": "\U0001F7E9", "color": "#2e9e5b", "colour_name": "green",
             "carries": "Words and letters: names, e-mail, phone, prompts, file text, file names."},
    "number": {"label": "Number", "emoji": "\U0001F7E6", "color": "#2f6fdd", "colour_name": "blue",
               "carries": "Whole and decimal numbers: amounts, counts, ids, percentages."},
    "flag": {"label": "Yes/No", "emoji": "\U0001F7E8", "color": "#e0b100", "colour_name": "yellow",
             "carries": "One true or false answer."},
    "date": {"label": "Date/Time", "emoji": "\U0001F7E7", "color": "#ee7d1a", "colour_name": "orange",
             "carries": "A date, a time of day, or both."},
    "record": {"label": "Record", "emoji": "\U0001F7EA", "color": "#8f4fd0", "colour_name": "purple",
               "carries": "One set of named values: a saved record, a waiting item, an error, a rule, a setting."},
    "records": {"label": "Record List", "emoji": "\U0001F7EB", "color": "#8a5a3c", "colour_name": "brown",
                "carries": "A list of records."},
    "values": {"label": "Value List", "emoji": "\U0001FA75", "color": "#17a2b8", "colour_name": "teal",
               "carries": "A list of plain values: texts, numbers or ids."},
    "view": {"label": "View", "emoji": "\U0001F7E5", "color": "#d9363e", "colour_name": "red",
             "carries": "Something drawn on screen: a field, a table, a panel."},
    "control": {"label": "Control", "emoji": "\u2B1B", "color": "#2b2f36", "colour_name": "black (square)",
                "carries": "A signal that starts or orders work: it says only that a card should run, or has finished. It carries no data."},
    ANY: {"label": "Any", "emoji": "\u2B1C", "color": "#b0b7c3", "colour_name": "grey (striped)",
          "carries": "Wildcard: the data can be of any class. An Any output links to any input and an Any input accepts any output, "
                     "so the app does not check the data; the builder must make sure it fits."},
}

CLASS_IDS = tuple(PORT_CLASSES)


def classes_compatible(out_class: str, in_class: str) -> bool:
    """Can an output of ``out_class`` be linked to an input of ``in_class``?"""
    if out_class not in PORT_CLASSES or in_class not in PORT_CLASSES:
        return False
    return out_class == in_class or out_class == ANY or in_class == ANY


def compat_table() -> dict[str, list[str]]:
    """For each output class, the input classes it may link to."""
    return {o: [i for i in CLASS_IDS if classes_compatible(o, i)] for o in CLASS_IDS}


# Cards of these roles begin or end a flow themselves, so they get no Start/Done ports.
NO_IMPLICIT_PORT_ROLES = ("trigger", "start", "end")

# The two ports every other card has. Same names and classes everywhere.
IMPLICIT_INPUT = {"name": "_start", "label": "Start", "cls": "control", "optional": True, "multi": False, "implicit": True}
IMPLICIT_OUTPUT = {"name": "_done", "label": "Done", "cls": "control", "optional": True, "multi": True, "implicit": True}

# ---------------------------------------------------------------------------
# Default class of a port name (used when the name means the same thing on every card)
# ---------------------------------------------------------------------------

DEFAULT_IN: dict[str, str] = {
    "record": "record", "records": "records", "text": "text", "id": "number", "item": "record",
    "items": "records", "proposal": "record", "result": "record", "content": "text", "table": "text",
    "start_date": "date", "end_date": "date", "date": "date", "first_date": "date", "second_date": "date",
    "total": "number", "current": "number", "starting": "number", "incoming": "number", "outgoing": "number",
    "average_use": "number", "lead_time": "number", "first": "number", "second": "number",
    "old_value": "number", "new_value": "number", "elapsed": "number", "record_id": "number",
    "ids": "values", "choices": "values", "email": "text", "phone": "text", "filename": "text",
    "message": "text", "query": "text", "field": "text",
    "list_a": "records", "list_b": "records", "left_records": "records", "sample_data": "records",
    "errors": "records", "record_a": "record", "record_b": "record", "record_1": "record",
    "record_2": "record", "error": "record", "settings": "record", "changes": "record", "where": "record",
    "order": "record", "shipment": "record", "old_item": "record", "current_item": "record",
    "pressed": "flag", "submitted": "flag", "opened": "flag", "selected": "flag", "started": "flag",
    "confirmed": "flag", "step": "control", "steps": "control", "branches": "control",
    "compare_date": "date",
}

DEFAULT_OUT: dict[str, str] = {
    "view": "view", "record": "record", "records": "records", "count": "number", "fire": "flag",
    "event": "control", "text": "text", "field_name": "text", "table_name": "text", "payload": "record",
    "instructions": "text", "filename": "text", "mime": "text", "content": "text", "valid": "flag",
    "reason": "text", "found": "flag", "match": "text", "error": "record", "logged": "flag",
    "proceed": "flag", "stopped": "flag", "groups": "records", "start_date": "date", "end_date": "date",
    "domain": "text", "total": "number", "page": "number", "page_size": "number", "total_pages": "number",
    "sum": "number", "average": "number", "percentage": "number", "minimum": "number", "maximum": "number",
    "stock": "number", "quantity": "number", "change": "number", "number": "number", "difference": "number",
    "working_days": "number", "attempts": "number", "last_seen_id": "number", "values": "values",
    "lines": "values", "comparison": "text", "date": "date", "time": "date", "datetime": "date",
    "next_due": "date", "ok": "flag", "success": "flag", "skipped": "flag", "created": "flag",
    "can_delete": "flag", "field_required": "flag", "flag": "flag", "requires_approval": "flag",
    "visible": "flag", "enabled": "flag", "all_done": "flag", "ready": "flag", "timeout": "flag",
    "wait_more": "flag", "resumed": "flag", "event_kind": "text", "before": "record", "after": "record",
    "crossed": "text", "matched_item": "record", "action": "text", "item": "record", "pending_items": "records",
    "schema": "record", "mappings": "record", "rules": "records", "checklist": "values",
    "explanation": "text", "help": "record", "prompt": "text", "context": "record", "format": "text",
    "errors": "records", "data": "record", "result": "record", "results": ANY,
    "rows": "records", "size": "number", "started_at": "date",
}

# ---------------------------------------------------------------------------
# Per-card settings: names that need a class here, and ports that take several links
#   "in":  {port name: class}      "out": {port name: class}
#   a class ending in "+" means "several links may end here" (all links are used, in order)
# ---------------------------------------------------------------------------

CARD_OVERRIDES: dict[str, dict[str, dict[str, str]]] = {
    # UI / Interface
    "Enter Text": {"in": {"value": "text"}, "out": {"value": "text"}},
    "Enter Paragraph": {"in": {"value": "text"}, "out": {"value": "text"}},
    "Enter Number": {"in": {"value": "number"}, "out": {"value": "number"}},
    "Pick Date": {"in": {"value": "date"}, "out": {"value": "date"}},
    "Pick Time": {"in": {"value": "date"}, "out": {"value": "date"}},
    "Enter Email Address": {"in": {"value": "text"}, "out": {"value": "text"}},
    "Enter Phone Number": {"in": {"value": "text"}, "out": {"value": "text"}},
    "Enter Currency Amount": {"in": {"value": "number"}, "out": {"value": "number"}},
    "Choose From Dropdown": {"in": {"value": "text"}, "out": {"value": "text"}},
    "Select Multiple Options": {"in": {"value": "values"}, "out": {"value": "values"}},
    "Choose One Option": {"in": {"value": "text"}, "out": {"value": "text"}},
    "Toggle Checkbox": {"in": {"value": "flag"}, "out": {"value": "flag"}},
    "Pick From Searchable List": {"in": {"value": "text"}, "out": {"value": "text"}},
    "Rate With Stars": {"in": {"value": "number"}, "out": {"value": "number"}},
    "Arrange In Grid": {"in": {"children": "view+"}},
    "Stack In Panel": {"in": {"children": "view+"}},
    "Organize In Tabs": {"in": {"tabs": "records"}},
    "Split Into Columns": {"in": {"children": "view+"}},
    "Collapse Section": {"in": {"children": "view+"}},
    "Show Status Badge": {"in": {"value": "text"}},
    "Display Barcode From Code": {"in": {"value": "text"}},
    "Switch Toggle": {"in": {"value": "flag"}, "out": {"value": "flag"}},
    "Adjust Slider": {"in": {"value": "number"}, "out": {"value": "number"}},
    "Choose File": {"out": {"filename": "text"}},
    # Backend Processing
    "Format Currency Value": {"in": {"value": "number"}},
    "Round Numeric Value": {"in": {"value": "number"}, "out": {"value": "number"}},
    "Combine Multiple Fields": {"out": {"text": "text"}},
    "Calculate Percentage Of Total": {"in": {"value": "number"}},
    "Calculate From Two Values": {"out": {"result": "number"}},
    "Change Value By Percent": {"in": {"value": "number"}, "out": {"result": "number"}},
    "Shift Date By Time": {"out": {"result": "date"}},
    "Find Smallest Or Largest Value": {"out": {"value": "number"}},
    "Branch On Yes/No": {"in": {"condition": "flag", "value": ANY}, "out": {"yes": ANY, "no": ANY}},
    "Compare Two Numbers": {"out": {"result": "flag"}},
    "Build Summary Record": {"in": {"value_1": ANY, "value_2": ANY, "value_3": ANY, "value_4": ANY}},
    "Set Field Of Record": {"in": {"value": ANY}},
    "App End": {"in": {"finish": "control+"}},
    "Handle Error Without Stopping": {"in": {"value": ANY}, "out": {"value": ANY}},
    "Set Default Value On Error": {"in": {"value": ANY}, "out": {"value": ANY}},
    "Retry Failed Step": {"in": {"step": "control"}, "out": {"result": ANY}},
    "Collect Error Records": {"out": {"valid": "records", "errors": "records"}},
    "Skip Invalid Record": {"out": {"skipped": "flag"}},
    # Data Modeling / Storage
    "Set Field Default Value": {"in": {"default_value": ANY}},
    "Create New Record": {"in": {"values": "record"}},
    "Create Or Update Record": {"in": {"values": "record"}},
    "Update Field Across Records": {"in": {"ids": "values", "field": "text", "value": ANY}},
    "Delete Multiple Records": {"in": {"ids": "values"}},
    # Logic / Validation: the card passes the checked value on unchanged
    "Check Field Is Required": {"in": {"value": ANY}, "out": {"value": ANY}},
    "Validate Field Type": {"in": {"value": ANY}, "out": {"value": ANY}},
    "Match Format Pattern": {"in": {"value": ANY}, "out": {"value": ANY}},
    "Validate Number Range": {"in": {"value": "number"}, "out": {"value": "number"}},
    "Check Text Length": {"in": {"value": "text"}, "out": {"value": "text"}},
    "Validate Against Allowed List": {"in": {"value": ANY}, "out": {"value": ANY}},
    "Reject Future Date": {"in": {"value": "date"}, "out": {"value": "date"}},
    "Compare Two Fields": {"in": {"value": "record"}, "out": {"value": "record"}},
    "Verify Sum Equals Total": {"in": {"value": "record"}, "out": {"value": "record"}},
    "Require Either Or Field": {"in": {"value": "record"}, "out": {"value": "record"}},
    "Require Dependent Field": {"in": {"value": "record"}, "out": {"value": "record"}},
    "Validate Date Order": {"in": {"value": "record"}, "out": {"value": "record"}},
    # Triggers / Orchestration
    "Run When Form Submitted": {"in": {"values": "record"}},
    "Run When Value Crosses Threshold": {"out": {"value": "number"}},
    "Run Steps In Sequence": {"in": {"steps": "control+"}},
    "Wait For All Steps To Complete": {"in": {"branches": "control+"}},
    "Wait For Condition With Timeout": {"in": {"condition": "flag"}},
    "Repeat For Each List Item": {"in": {"items": "records", "step": "control"}},
    # Integrations / Connectors
    "Build Supplier Message": {"in": {"message": "record"}},
    "Build Email Text": {"in": {"data": "record"}},
    "Show Manual Steps": {"in": {"steps": "values"}},
    "Show Action Checklist": {"in": {"items": "values"}},
    "Enter Outside Result": {"out": {"value": ANY}},
    "Resume After Result": {"out": {"data": "record"}},
    # AI Capabilities
    "Accept AI Answer": {"out": {"answer": ANY}},
    "Check Answer Shape": {"in": {"answer": ANY}, "out": {"value": ANY}},
    # Navigation / Output
    "Open Pop-Up Panel": {"in": {"content": "view"}},
    "Print-Friendly Page": {"in": {"content": "view"}},
    "Summary Table": {"in": {"data": "records"}},
    "Chart Over Time": {"in": {"data": "records"}},
    "Grouped Totals View": {"in": {"data": "records"}},
}

# Route cards: every output port carries the routed record
ROUTE_OUTPUT_CLASS = "record"


# ---------------------------------------------------------------------------
# Building the ports of one card
# ---------------------------------------------------------------------------

def _label(name: str) -> str:
    return name.replace("_", " ")


def _resolve(name: str, side: str, card_name: str, role: str) -> str:
    table = CARD_OVERRIDES.get(card_name, {}).get(side, {})
    if name in table:
        return table[name]
    if side == "out" and role == "route":
        return ROUTE_OUTPUT_CLASS
    default = (DEFAULT_IN if side == "in" else DEFAULT_OUT).get(name)
    if default is None:
        raise KeyError(f"{card_name}: no class for {side}put port '{name}'")
    return default


def ports_for_card(spec: Any) -> dict[str, list[dict]]:
    """The listed ports of one registered card, plus its implicit control ports.

    Each port: ``name`` (the template's input/output name), ``label``, ``cls``, ``optional``,
    ``multi`` (several links may end here), ``implicit``.
    """
    params = inspect.signature(spec.func).parameters
    inputs, outputs = [], []
    for name in spec.inputs:
        cls = _resolve(name, "in", spec.name, spec.role)
        multi = cls.endswith("+")
        cls = cls.rstrip("+")
        _check_class(spec.name, name, cls)
        optional = params[name].default is not inspect.Parameter.empty
        inputs.append({"name": name, "label": _label(name), "cls": cls, "optional": optional,
                       "multi": multi, "implicit": False})
    for name in spec.outputs:
        cls = _resolve(name, "out", spec.name, spec.role)
        _check_class(spec.name, name, cls.rstrip("+"))
        outputs.append({"name": name, "label": _label(name), "cls": cls.rstrip("+"), "optional": True,
                        "multi": True, "implicit": False})
    if spec.role not in NO_IMPLICIT_PORT_ROLES:
        inputs.append(dict(IMPLICIT_INPUT))
        outputs.append(dict(IMPLICIT_OUTPUT))
    return {"inputs": inputs, "outputs": outputs}


def _check_class(card_name: str, port: str, cls: str) -> None:
    if cls not in PORT_CLASSES:
        raise ValueError(f"{card_name}: port '{port}' has unknown class '{cls}'")


def stale_overrides(registry: dict) -> list[str]:
    """Overrides that name a card or a port that does not exist (a sign of a rename)."""
    problems = []
    for card_name, sides in CARD_OVERRIDES.items():
        spec = registry.get(card_name)
        if spec is None:
            problems.append(f"unknown card: {card_name}")
            continue
        for side, table in sides.items():
            names = spec.inputs if side == "in" else spec.outputs
            for port in table:
                if port not in names:
                    problems.append(f"{card_name}: no {side}put port '{port}'")
    return problems


def port_text(port: dict, side: str) -> str:
    """How a port is written in Cards.md: emoji, name, then ``?`` (an optional input)
    or ``+`` (an input that takes several links). Outputs carry no mark: an output may feed any number of inputs."""
    mark = ""
    if side == "in" and not port["implicit"]:
        if port["multi"]:
            mark = "+"
        elif port["optional"]:
            mark = "?"
    return f"{PORT_CLASSES[port['cls']]['emoji']} {port['name']}{mark}"