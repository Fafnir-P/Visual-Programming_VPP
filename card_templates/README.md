# card_templates

Reusable Python templates for the 205 cards in `Cards.md`. Python 3.13, standard library only.
A later phase copies these into generated projects and writes the glue between cards.
Nothing here is app-specific: every card is generic and takes its table names, field names and limits as settings.

## Layout

```
card_templates/
  runtime.py      shared code: CardError, Context, Store (SQLite), conditions, value rules, view nodes, @card
  ui/ backend/ data/ logic/ triggers/ integrations/ ai/ output/     one module per group in Cards.md
  testing.py      runs every card's own examples      python -m card_templates.testing
  manifest.py     writes manifest.json (one contract per card)    python -m card_templates.manifest
  cards_md.py     reads Cards.md so tests can check that both lists agree
tests/            python -m unittest discover -s tests -v
```

## A card

```python
@card("Pick Date", category="UI / Interface", group="Form Inputs",
      inputs=["value"], outputs=["view", "value"], role="view", effects=["view"],
      examples=[...], invalid=[...])
def pick_date(ctx, *, value=None, name="date", label="Date", required=False) -> dict:
    """Shows a calendar date field and cleans the date the user picked."""
```

| Part | Meaning |
| --- | --- |
| `ctx` | `ctx.store` saved data, `ctx.now()` the app clock, `ctx.preview`, `ctx.event_id`, `ctx.settings` |
| `inputs` | keyword names that carry data from other cards |
| other keywords | settings the builder fills in; one without a default is a required setting (`required_config` in the manifest) |
| return value | a dict whose keys equal `outputs`; route cards return `{"route": port, "value": record}` |
| `phase` | `generation` (build time), `runtime`, or `human` (a person does a step) |
| `role` | `data`, `view`, `trigger`, `flow`, `route` |
| failures | `raise CardError(code, message)`; the engine rolls the event back and follows the error path |

## Rules the tests enforce

* The templates and `Cards.md` list exactly the same cards (name, category, group).
* Every card carries examples and invalid cases, and they all pass.
* Standard library only; a card imports nothing but `..runtime`.
* No `eval`, `exec`, `open`, network, file system, `random`, or wall clock (time comes from `ctx.now()`).
* UI cards return declarative view nodes (`view(...)`), never HTML.
* Trigger cards call `ctx.require_preview()` and refuse to run outside the preview.
* Connector cards only prepare text and data for a person and take a typed or file-text result back.
* AI cards never call an AI service; build-time cards hold a prompt text and check a proposal supplied by the generator.

## What is not here

Ports, the graph engine, scheduling, rendering of view nodes, file access, and the generator itself.
The engine is expected to wrap each event in `ctx.store.transaction()` and call `ctx.store.apply_once(event_id)`.
