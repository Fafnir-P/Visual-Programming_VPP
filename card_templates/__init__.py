"""Reusable Python templates for every card listed in Cards.md.

    from card_templates import load_all, REGISTRY
    load_all()                       # imports every card module
    REGISTRY["Enter Text"].func(ctx, ...)

See README.md in this folder for the card contract.
"""
from __future__ import annotations

import importlib
import pkgutil

from .runtime import REGISTRY, CardError, CardSpec, Context, Store, card, view  # noqa: F401

CATEGORY_PACKAGES = ("ui", "backend", "data", "logic", "triggers", "integrations", "ai", "output")


def load_all() -> dict:
    """Import every card module so that REGISTRY is complete. Safe to call twice."""
    for package_name in CATEGORY_PACKAGES:
        try:
            package = importlib.import_module(f"{__name__}.{package_name}")
        except ModuleNotFoundError as err:
            if err.name == f"{__name__}.{package_name}":
                continue
            raise
        for info in sorted(pkgutil.iter_modules(package.__path__), key=lambda m: m.name):
            importlib.import_module(f"{package.__name__}.{info.name}")
    return REGISTRY
