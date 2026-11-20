"""Writes prototype/templates.js: the Python template of every card, for the Generate request.

    python -m card_templates.templates_export          rewrite prototype/templates.js
    python -m card_templates.templates_export --check  exit 1 if the file is out of date

One entry per card title: the function name, its source (decorator, docstring and comments left out,
no examples), its settings with their defaults, inputs and outputs. Names the function takes from
card_templates/runtime.py are listed in `runtime` (names only, not the runtime code). Helpers that sit
in the card's own module are listed in `helpers` with their source, so the template can run as is.
"""
from __future__ import annotations

import ast
import builtins
import inspect
import json
import pathlib
import sys
import textwrap

from . import REGISTRY, load_all, runtime

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEMPLATES_JS = ROOT / "prototype" / "templates.js"


def _strip_docstring(node: ast.AST) -> None:
    body = node.body
    if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant) \
            and isinstance(body[0].value.value, str):
        node.body = body[1:] or [ast.Pass()]


def _source(fn) -> tuple[str, set[str]]:
    """Source of fn without decorator and docstring, and the global names it reads."""
    tree = ast.parse(textwrap.dedent(inspect.getsource(fn)))
    node = tree.body[0]
    node.decorator_list = []
    for sub in ast.walk(node):
        if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            _strip_docstring(sub)
    return ast.unparse(node), _free_names(node)


def _free_names(node: ast.AST) -> set[str]:
    """Global names the code reads (builtins left out)."""
    local = {a.arg for a in ast.walk(node) if isinstance(a, ast.arg)}
    for sub in ast.walk(node):
        if isinstance(sub, ast.Name) and isinstance(sub.ctx, (ast.Store, ast.Del)):
            local.add(sub.id)
        elif isinstance(sub, (ast.FunctionDef, ast.ClassDef)):
            local.add(sub.name)
        elif isinstance(sub, ast.ExceptHandler) and sub.name:
            local.add(sub.name)
        elif isinstance(sub, (ast.Import, ast.ImportFrom)):
            local.update((a.asname or a.name).split(".")[0] for a in sub.names)
    used = {n.id for n in ast.walk(node) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
    return {n for n in used - local if not hasattr(builtins, n)}


def _module_helpers(fn, names: set[str], seen: set[str]) -> list[dict]:
    """Source of the module-level functions and constants of the card's own module that `names` use."""
    module = inspect.getmodule(fn)
    out = []
    for name in sorted(names):
        if name in seen or name in runtime.__dict__ and getattr(module, name, None) is runtime.__dict__[name]:
            continue
        value = getattr(module, name, None)
        if value is None or inspect.ismodule(value):
            continue
        seen.add(name)
        if inspect.isfunction(value) and value.__module__ == module.__name__:
            src, deeper = _source(value)
            out += _module_helpers(fn, deeper, seen)
            out.append({"name": name, "source": src})
        elif not callable(value):
            out.append({"name": name, "source": f"{name} = {value!r}"})
    return out


def _default(value):
    try:
        json.dumps(value)
        return value
    except TypeError:
        return repr(value)


def build_entry(spec) -> dict:
    source, names = _source(spec.func)
    sig = inspect.signature(spec.func).parameters
    settings = []
    for name in spec.config:
        p = sig[name]
        item = {"name": name}
        if p.default is inspect.Parameter.empty:
            item["required"] = True
        else:
            item["default"] = _default(p.default)
        settings.append(item)
    seen: set[str] = set()
    helpers = _module_helpers(spec.func, names, seen)
    helper_names = {h["name"] for h in helpers}
    allnames = set(names)
    for h in helpers:
        allnames |= _free_names(ast.parse(h["source"]))
    allnames -= helper_names
    module = inspect.getmodule(spec.func)
    runtime_names = sorted(n for n in allnames if n in runtime.__dict__ and getattr(module, n, None) is runtime.__dict__[n])
    imports = []
    for n in sorted(allnames - set(runtime_names)):
        v = getattr(module, n, None)
        if inspect.ismodule(v):
            imports.append(f"import {v.__name__}" if v.__name__ == n else f"import {v.__name__} as {n}")
        elif v is not None and getattr(v, "__module__", "") not in ("", None, module.__name__) and hasattr(v, "__name__"):
            imports.append(f"from {v.__module__} import {v.__name__}" + ("" if v.__name__ == n else f" as {n}"))
    entry = {"function": spec.func.__name__, "source": source, "settings": settings,
             "inputs": list(spec.inputs), "outputs": list(spec.outputs), "runtime": runtime_names, "imports": imports}
    if helpers:
        entry["helpers"] = helpers
    return entry


def build_templates_js() -> str:
    load_all()
    data = {title: build_entry(REGISTRY[title]) for title in sorted(REGISTRY)}
    return ("// ============================================================================\n"
            "// CARD TEMPLATES  (GENERATED: do not edit by hand)\n"
            "// ============================================================================\n"
            "// Written by:  python -m card_templates.templates_export\n"
            "// One entry per card title: Python source of the template (no examples), its settings with\n"
            "// defaults, inputs, outputs, the names it uses from the shared runtime, and own-module helpers.\n"
            "// Loaded before bedrock.js, which sends only the templates of the cards on the canvas.\n"
            "const CARD_TEMPLATES = " + json.dumps(data, ensure_ascii=True, indent=1) + ";\n")


def main(argv: list[str]) -> int:
    new = build_templates_js()
    if "--check" in argv:
        if not TEMPLATES_JS.exists() or TEMPLATES_JS.read_text(encoding="utf8") != new:
            print("out of date: prototype/templates.js")
            return 1
        return 0
    TEMPLATES_JS.write_text(new, encoding="utf8", newline="\n")
    print(f"wrote {TEMPLATES_JS.name} ({len(REGISTRY)} cards, {len(new)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
