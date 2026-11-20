"""Flow Control (Triggers / Orchestration). Coordinates multi-step flows."""
from __future__ import annotations

from typing import Callable

from ..runtime import MAX_LOOP_ITEMS, CardError, bounded, card

CATEGORY = "Triggers / Orchestration"
GROUP = "Flow Control"


@card(
    "Run Steps In Sequence", category=CATEGORY, group=GROUP,
    inputs=["steps"], outputs=["results"],
    role="flow",
    examples=[
        {"label": "three steps in order",
         "args": {"steps": [lambda: {"a": 1}, lambda: {"b": 2}, lambda: {"c": 3}]},
         "expect": {"results": [{"a": 1}, {"b": 2}, {"c": 3}]}},
        {"label": "empty list",
         "args": {"steps": []},
         "expect": {"results": []}},
    ],
    invalid=[
        {"label": "not a list",
         "args": {"steps": "wrong"}, "code": "invalid_input"},
        {"label": "too many steps",
         "args": {"steps": [lambda: {} for _ in range(10001)]}, "code": "limit_exceeded"},
    ],
)
def run_steps_in_sequence(ctx, *, steps: list[Callable[[], dict]]) -> dict:
    """Runs the connected steps one after another, in the order the user set."""
    if not isinstance(steps, list):
        raise CardError("invalid_input", "Steps must be a list.")
    bounded(steps, MAX_LOOP_ITEMS, "steps")
    
    results = []
    for step in steps:
        if not callable(step):
            raise CardError("invalid_input", "Each step must be callable.")
        result = step()
        results.append(result)
    
    return {"results": results}


@card(
    "Wait For All Steps To Complete", category=CATEGORY, group=GROUP,
    inputs=["branches"], outputs=["results", "all_done"],
    role="flow",
    examples=[
        {"label": "all branches complete",
         "args": {"branches": [{"done": True, "result": {"x": 1}}, {"done": True, "result": {"y": 2}}]},
         "expect": {"all_done": True, "results": [{"x": 1}, {"y": 2}]}},
        {"label": "one branch pending",
         "args": {"branches": [{"done": True, "result": {"x": 1}}, {"done": False}]},
         "expect": {"all_done": False, "results": []}},
    ],
    invalid=[
        {"label": "not a list",
         "args": {"branches": "wrong"}, "code": "invalid_input"},
        {"label": "too many branches",
         "args": {"branches": [{"done": True} for _ in range(10001)]}, "code": "limit_exceeded"},
    ],
)
def wait_for_all_steps_to_complete(ctx, *, branches: list[dict]) -> dict:
    """Waits until every branch the flow actually took has finished, then carries on."""
    if not isinstance(branches, list):
        raise CardError("invalid_input", "Branches must be a list.")
    bounded(branches, MAX_LOOP_ITEMS, "branches")
    
    results = []
    all_done = True
    for branch in branches:
        if not isinstance(branch, dict):
            raise CardError("invalid_input", "Each branch must be a record.")
        if not branch.get("done", False):
            all_done = False
            break
        results.append(branch.get("result", {}))
    
    return {"all_done": all_done, "results": results if all_done else []}


@card(
    "Wait For Condition With Timeout", category=CATEGORY, group=GROUP,
    inputs=["condition", "elapsed"], outputs=["ready", "timeout", "wait_more"],
    role="flow",
    examples=[
        {"label": "condition met",
         "args": {"condition": True, "timeout_seconds": 60, "elapsed": 10},
         "expect": {"ready": True, "timeout": False, "wait_more": False}},
        {"label": "timeout reached",
         "args": {"condition": False, "timeout_seconds": 30, "elapsed": 35},
         "expect": {"ready": False, "timeout": True, "wait_more": False}},
        {"label": "still waiting",
         "args": {"condition": False, "timeout_seconds": 60, "elapsed": 20},
         "expect": {"ready": False, "timeout": False, "wait_more": True}},
        {"label": "zero elapsed",
         "args": {"condition": False, "timeout_seconds": 10, "elapsed": 0},
         "expect": {"ready": False, "timeout": False, "wait_more": True}},
    ],
    invalid=[
        {"label": "negative timeout",
         "args": {"condition": False, "timeout_seconds": -5}, "code": "invalid_input"},
        {"label": "negative elapsed",
         "args": {"condition": False, "timeout_seconds": 10, "elapsed": -1}, "code": "invalid_input"},
    ],
)
def wait_for_condition_with_timeout(ctx, *, condition: bool, timeout_seconds: int = 60,
                                   elapsed: int = 0) -> dict:
    """Pauses until a condition becomes true or the required time limit runs out, whichever comes first."""
    if timeout_seconds < 0:
        raise CardError("invalid_input", "Timeout must be a positive number of seconds.")
    if elapsed < 0:
        raise CardError("invalid_input", "Elapsed time cannot be negative.")
    
    if condition:
        return {"ready": True, "timeout": False, "wait_more": False}
    
    if elapsed >= timeout_seconds:
        return {"ready": False, "timeout": True, "wait_more": False}
    
    return {"ready": False, "timeout": False, "wait_more": True}


@card(
    "Repeat For Each List Item", category=CATEGORY, group=GROUP,
    inputs=["items", "step"], outputs=["results", "count"],
    role="flow",
    examples=[
        {"label": "three items",
         "args": {"items": [{"x": 1}, {"x": 2}, {"x": 3}], "step": lambda item: {"y": item["x"] * 2}},
         "expect": {"results": [{"y": 2}, {"y": 4}, {"y": 6}], "count": 3}},
        {"label": "empty list",
         "args": {"items": [], "step": lambda item: item},
         "expect": {"results": [], "count": 0}},
    ],
    invalid=[
        {"label": "not a list",
         "args": {"items": "wrong", "step": lambda x: x}, "code": "invalid_input"},
        {"label": "too many items",
         "args": {"items": [{"i": i} for i in range(10001)], "step": lambda x: x, "limit": 10000},
         "code": "limit_exceeded"},
    ],
)
def repeat_for_each_list_item(ctx, *, items: list, step: Callable[[dict], dict],
                              limit: int = MAX_LOOP_ITEMS) -> dict:
    """Runs the connected steps once for each record in a list, up to a limit set when building."""
    if not isinstance(items, list):
        raise CardError("invalid_input", "Items must be a list.")
    if limit < 1 or limit > MAX_LOOP_ITEMS:
        raise CardError("invalid_input", f"Limit must be between 1 and {MAX_LOOP_ITEMS}.")
    
    bounded(items, limit, "items")
    
    if not callable(step):
        raise CardError("invalid_input", "Step must be callable.")
    
    results = []
    for item in items:
        result = step(item)
        results.append(result)
    
    return {"results": results, "count": len(results)}
