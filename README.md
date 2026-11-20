# Visual-Programming_VPP

A card-based visual programming app (Electron). Build a program by placing and linking cards; Python templates for every card are in `card_templates/`.

## Run

```
npm install
npm start
```

## Test

```
python -m unittest discover -s tests
python -m card_templates.testing
python -m card_templates.ports_export --check
python -m card_templates.templates_export --check
node tests/ports_logic.test.js
node tests/request.test.js
node tests/meter.test.js
node tests/main_pure.test.js
```

Python 3.10+ (tested on 3.13), Node with Electron 45, no other packages.

## Folders

| Path | What |
| --- | --- |
| `main.js`, `preload.js`, `lockout.js` | Electron shell, local accounts, key storage |
| `prototype/` | the app page (`app.js`, `ports.js`, `catalog.js`, `templates.js`, ...) |
| `card_templates/` | Python template for each card, manifest, exporters |
| `tests/` | Python and Node tests |
| `Cards.md` | the card list and port rules (generated part: `python -m card_templates.ports_export`) |
| `final_check/` | audit reports, notes and archived trial builds |
