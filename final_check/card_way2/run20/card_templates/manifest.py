"""Writes manifest.json: one contract summary per card.

    python -m card_templates.manifest
"""
from __future__ import annotations

import json
import pathlib

from . import REGISTRY, load_all
from .cards_md import read_cards_md
from .ports import ports_for_card

MANIFEST_PATH = pathlib.Path(__file__).resolve().parent / "manifest.json"


def build_manifest() -> dict:
    load_all()
    order = {c["name"]: c["number"] for c in read_cards_md()}
    cards = []
    for name, spec in sorted(REGISTRY.items(), key=lambda kv: order.get(kv[0], 10_000)):
        entry = spec.contract()
        entry["number"] = order.get(name)
        entry["ports"] = ports_for_card(spec)
        cards.append(entry)
    return {"format": 1, "count": len(cards), "cards": cards}


def write_manifest(path: pathlib.Path = MANIFEST_PATH) -> dict:
    manifest = build_manifest()
    path.write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf8")
    return manifest


if __name__ == "__main__":
    print(f"wrote {write_manifest()['count']} cards to {MANIFEST_PATH}")
