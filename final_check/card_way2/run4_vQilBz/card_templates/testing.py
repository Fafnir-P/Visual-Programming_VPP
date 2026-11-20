"""Runs the examples that every card carries. Standard library only.

    python -m card_templates.testing          run every example of every card
    python -m card_templates.testing "Pick Date"   run one card
"""
from __future__ import annotations

import copy
import json
import math
import sys
from typing import Any

from .runtime import REGISTRY, CardError, CardSpec, Context, Store


def diff(expected: Any, actual: Any, path: str = "result") -> list[str]:
    """List the differences. Dicts: every expected key must match (extra keys are fine).
    Lists: same length, each item matches. Numbers: equal within 1e-9."""
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return [f"{path}: expected a record, got {type(actual).__name__}"]
        out: list[str] = []
        for key, value in expected.items():
            if key not in actual:
                out.append(f"{path}.{key}: missing")
            else:
                out += diff(value, actual[key], f"{path}.{key}")
        return out
    if isinstance(expected, (list, tuple)):
        if not isinstance(actual, (list, tuple)):
            return [f"{path}: expected a list, got {type(actual).__name__}"]
        if len(expected) != len(actual):
            return [f"{path}: expected {len(expected)} items, got {len(actual)}"]
        out = []
        for i, (e, a) in enumerate(zip(expected, actual)):
            out += diff(e, a, f"{path}[{i}]")
        return out
    if isinstance(expected, bool) or isinstance(actual, bool):
        same = type(expected) is type(actual) and expected == actual
    elif isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        same = math.isclose(expected, actual, rel_tol=1e-9, abs_tol=1e-9)
    else:
        same = expected == actual
    return [] if same else [f"{path}: expected {expected!r}, got {actual!r}"]


def build_context(case: dict) -> Context:
    ctx = Context.for_tests(now=case.get("now", "2026-01-15T09:30:00"), preview=case.get("preview", True),
                            event_id=case.get("event_id"), store=Store(), settings=case.get("settings"))
    for table, fields in (case.get("tables") or {}).items():
        ctx.store.define_table(table, copy.deepcopy(fields))
    for table, keep in (case.get("history") or {}).items():
        ctx.store.enable_history(table, keep)
    for table, rows in (case.get("rows") or {}).items():
        for row in rows:
            ctx.store.insert(table, copy.deepcopy(row))
    return ctx


def check_result(spec: CardSpec, result: Any) -> list[str]:
    if not isinstance(result, dict):
        return [f"card returned {type(result).__name__}, expected a dict"]
    problems: list[str] = []
    if spec.role == "route":
        if set(result) != {"route", "value"}:
            problems.append(f"route card must return exactly route and value, got {sorted(result)}")
        elif result["route"] not in spec.outputs:
            problems.append(f"route {result['route']!r} is not one of the declared outputs {list(spec.outputs)}")
    elif set(result) != set(spec.outputs):
        problems.append(f"returned keys {sorted(result)} differ from declared outputs {sorted(spec.outputs)}")
    try:
        json.dumps(result)
    except (TypeError, ValueError) as err:
        problems.append(f"result is not plain data (JSON): {err}")
    return problems


def run_example(spec: CardSpec, case: dict) -> list[str]:
    label = case.get("label", "example")
    try:
        ctx = build_context(case)
    except Exception as err:  # noqa: BLE001
        return [f"[{label}] test setup failed: {type(err).__name__}: {err}"]
    try:
        result = spec.func(ctx, **copy.deepcopy(case.get("args", {})))
    except CardError as err:
        return [f"[{label}] unexpected CardError {err.code}: {err.message}"]
    except Exception as err:  # noqa: BLE001 - report any crash as a failure
        return [f"[{label}] crashed: {type(err).__name__}: {err}"]
    problems = check_result(spec, result)
    problems += diff(case.get("expect", {}), result)
    for table, expected_rows in (case.get("expect_rows") or {}).items():
        actual_rows = ctx.store.find(table, include_archived=True)
        problems += diff(expected_rows, actual_rows, f"rows[{table}]")
    if ctx.store.in_transaction:
        problems.append("a transaction was left open")
    return [f"[{label}] {p}" for p in problems]


def run_invalid(spec: CardSpec, case: dict) -> list[str]:
    label = case.get("label", "invalid")
    try:
        ctx = build_context(case)
    except Exception as err:  # noqa: BLE001
        return [f"[{label}] test setup failed: {type(err).__name__}: {err}"]
    try:
        spec.func(ctx, **copy.deepcopy(case.get("args", {})))
    except CardError as err:
        problems = [] if err.code == case["code"] else [f"expected code {case['code']!r}, got {err.code!r}"]
        if ctx.store.in_transaction:
            problems.append("a transaction was left open")
        if "rows" in case or "expect_rows" in case:
            for table, expected_rows in (case.get("expect_rows") or {}).items():
                problems += diff(expected_rows, ctx.store.find(table, include_archived=True), f"rows[{table}]")
        return [f"[{label}] {p}" for p in problems]
    except Exception as err:  # noqa: BLE001
        return [f"[{label}] crashed instead of raising CardError: {type(err).__name__}: {err}"]
    return [f"[{label}] expected CardError {case['code']!r} but the card succeeded"]


def run_spec(spec: CardSpec) -> list[str]:
    problems: list[str] = []
    for case in spec.examples:
        problems += run_example(spec, case)
    for case in spec.invalid:
        problems += run_invalid(spec, case)
    return problems


def run_all(names: list[str] | None = None) -> dict[str, list[str]]:
    from . import load_all
    load_all()
    chosen = names or list(REGISTRY)
    return {name: run_spec(REGISTRY[name]) for name in chosen}


def main(argv: list[str]) -> int:
    results = run_all(argv or None)
    bad = {k: v for k, v in results.items() if v}
    for name, problems in bad.items():
        print(f"FAIL {name}")
        for p in problems:
            print("   ", p)
    print(f"{len(results) - len(bad)} of {len(results)} cards pass")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
