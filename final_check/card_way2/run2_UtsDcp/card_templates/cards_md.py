"""Reads Cards.md so tests can check that templates and the card list agree."""
from __future__ import annotations

import pathlib
import re

DEFAULT_PATH = pathlib.Path(__file__).resolve().parent.parent / "Cards.md"


def read_cards_md(path: str | pathlib.Path = DEFAULT_PATH) -> list[dict]:
    """Return ``[{"number", "name", "category", "group", "description"}, ...]`` in file order."""
    cards = []
    for line in pathlib.Path(path).read_text(encoding="utf8").splitlines():
        if re.match(r"^\| \d{3} \|", line):
            cell = [c.strip() for c in line.split("|")[1:-1]]
            cards.append({"number": int(cell[0]), "name": cell[1], "category": cell[2],
                          "group": cell[3], "description": cell[4]})
    return cards
