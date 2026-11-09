# Activity

## 2026-11-08 — Frontend prototype: card select / drag / compose

**Task:** Build the VISUAL_PROGRAMMING_PROJECT frontend covering three card
functions only — 选择 (select), 拖拽 (drag), 组建 (compose/connect). No card
content and no software-generation features this phase.

**Workflow (per `agent.md`):** plan → develop → review → revise → test →
completion gate. Subagents used `claude-sonnet-4.5` (sonnet/haiku preference).
Note: subagents on this harness emit code as text and do not write to disk, so
the coordinating agent wrote all files and ran all verification itself.

**Files changed:**
- `prototype/index.html` — toolbar (Add Card), canvas container, SVG edge layer, canvas.
- `prototype/style.css` — card, ports, selection highlight, edge and draft-edge styles.
- `prototype/app.js` — in-memory state (nodes/edges Maps with stable string IDs), selection, drag, port-based edge composition, edge/node deletion, rendering.

**Stack:** single-page vanilla HTML/CSS/JS, no build step, no dependencies,
opens via `file://` with zero setup (matches a somewhat-technical user).

**Scope / constraints honored:** empty cards only; drag/select/connect update
in-memory state only (grep confirmed no fetch/storage/WebSocket/timers/network);
canvas x/y presentation-only; nodes and edges carry stable `node_N` / `edge_N` IDs.

**Review decision:** CHANGES NEEDED → revised → effectively approved after fixes.
- MAJOR: edge endpoints used a wrong hardcoded header-height constant (41px),
  so lines started ~11px above the port. Fixed by deriving endpoints from the
  live DOM (`getBoundingClientRect`) instead of constants.
- MINOR: input-port click handler was attached only while a draft existed.
  Fixed to always attach and gate inside the handler.
- Also unified all mouse→canvas coordinate conversion into one helper, removing
  the hardcoded toolbar offset.

**Tests:** `node --check` on `app.js` passed. jsdom harness (run in scratch,
removed afterward) exercised all three functions plus edge cases: 21/21 passed
— add, select, background-deselect, in-memory drag, click-vs-drag, connect,
duplicate rejection, self-connection rejection, Escape cancel, edge select,
edge delete, node delete cascading to incident edges.

**Not auto-verified:** pixel-level visual alignment of edges (jsdom has no
layout engine). Mitigated by DOM-derived coordinates; recommend one manual
browser check by opening `prototype/index.html`.

**Completion status:** COMPLETE for this phase. Reviewer issues resolved; tests
pass.

## 2026-11-09 — App shell: sidebar, 200 blank cards, categories, run order

**Task:** Turn the prototype into an app: a sidebar that opens and closes, to
choose cards from; 200 blank cards; pick cards by category; arrange cards in a
run order.

**Workflow note:** Subagents on this harness do not write files, so the
coordinating agent wrote the code and ran the tests directly. No separate
reviewer pass was run this round; the jsdom suite was the only check. Reviewer
sign-off under `agent.md` is still open.

**Files changed (all under `prototype/`):**
- `catalog.js` (new) — 200 blank cards, IDs `catalog_001`..`catalog_200`, titles unique. Category counts follow framework section 4: UI 30, Backend 60, Data 30, Logic 25, Triggers 15, Integrations 20, AI 10, Navigation/Output 10.
- `index.html` — toolbar toggle, sidebar (Cards tab, Order tab), stage wrapper.
- `style.css` — sidebar, chips, order list, order badge, conflict outline.
- `app.js` — sidebar open/close, category chips (with counts), search, Add button and drag-to-canvas, run order (`state.order`), reorder by arrows or drag, order badge on each card, order-conflict warning, status line.

**Behavior:**
- Sidebar hides and shows; the canvas widens to fill the space.
- Category chips and a search box filter the list. Each card can be added many times.
- Order tab lists cards top to bottom; new cards go last. Drag a row or use arrows. Click a row to select the card.
- A link whose source runs after its target is flagged (framework 4.1: dependencies come first). It warns only; it does not block.
- Fixed: the line layer used to be as big as the window, so lines could clip when scrolled. Lines and cards now share one large stage.
- Fixed: Backspace in the search box no longer deletes a selected card.

**Scope kept:** cards stay blank; no network, storage, or timers (grep clean); no generation.

**Tests:** `node --check` passed on both scripts. jsdom suite, 39/39 passed:
catalog size/IDs/counts, sidebar toggle, filters and search, Add and drop,
order moves (arrows and drag), conflict flags, plus select/drag/delete still
working. jsdom has no layout, so look and feel are not checked.

**Not verified:** real-browser look, native drag-and-drop feel, and edge
alignment. Open `prototype/index.html` to check.

**Completion status:** BUILT AND TESTED; reviewer approval pending.

## 2026-11-09 — Connect by press-drag-release

**Task:** Replace click-then-click linking with press on a port, drag, and release.
On release the line joins the nearest port of the opposite type (output finds
input; input finds output) on another card, within 40px.

**Workflow (per `agent.md`):** plan → develop → review → re-review → minor fix → test → gate.
Subagents used `claude-sonnet-4.5`. The developer subagent wrote files to disk this time.

**Files changed (under `prototype/`):**
- `app.js` — ports use mousedown; `beginDraft`, snap search (`SNAP_RADIUS` 40), `commitEdge`
  (stores edge output→input, reversed when started from an input), snap highlight on the
  live port, Escape cancel. Old click-click code removed.
- `style.css` — `.port.snap-target` highlight, crosshair cursor on ports.

**Review:** first pass CHANGES NEEDED with 3 MAJOR findings. The coordinator checked
them against the code and they were wrong (no render during drag; port handler stops
bubbling first; draft line is correct for both start types). The reviewer re-read the
code and withdrew all three: APPROVED. One real MINOR (no active highlight when
starting from an input port) was fixed by the developer.

**Tests:** the tester subagent made no tool calls and its script never ran. The
coordinator wrote and ran a jsdom suite in scratch (removed after): 16/16 passed —
output→input, input→output reversed, far release cancels, same card blocked,
duplicate blocked, Escape cancels, snap highlight on and off, nearest port wins,
card drag and select still work, port press does not drag the card, plain click makes
no edge, start-port highlight. `node --check` passed.

**Not verified:** real-browser feel and pixel alignment (jsdom has no layout; port
positions were stubbed).

**Completion status:** COMPLETE (reviewer approved, tests passed).

## 2026-11-09 — Bedrock settings, system prompt, Generate button

**Task:** Add a place for the Bedrock API key and a model picker, a ready-written
system prompt for the model that will later build the project from cards, and a
Generate button that opens a "build is complete?" confirmation window. No card
content and no real generation this phase.

**Workflow (per `agent.md`):** plan → develop → review → test → gate. Subagents used
`claude-sonnet-4.5`.

**Coordinator decisions on the plan:**
- Planner proposed three AWS access fields. Overridden: one Bedrock API key field
  (bearer token), as the user asked for an API key.
- Planner used `export` in `prompt.js`. Overridden: plain scripts, so `file://` works.
- Prompt targets Python (framework section 1: launch language is Python).

**Files changed (under `prototype/`):**
- `prompt.js` (new) — `SYSTEM_PROMPT`: follow cards strictly, reuse card template code
  as much as possible, no invented features, report gaps and stop, file manifest output.
- `bedrock.js` (new) — `bedrockState` (key, region, model), region and model lists
  (Claude Sonnet/Haiku, plus custom), `serializeGraph()`, `assembleBedrockRequest()`
  (builds the Converse request; sends nothing; leaves the key out).
- `index.html` — Model tab (key with Show/Hide, region, model), Generate button,
  confirmation `<dialog>`, script order.
- `style.css` — Model panel, Generate button, dialog.
- `app.js` — Model tab in `setTab`, Generate click, dialog cancel/confirm, button
  disabled with 0 cards.

**Behavior:** Generate opens a dialog with card and link counts and an order-conflict
warning. "Yes, the build is complete" sets `state.buildConfirmed` and shows
"Build confirmed. Generation is not enabled yet." Nothing is sent.

**Review:** first pass CHANGES NEEDED. Both MAJOR items were checked against the code
and rejected (the key is not in the request body; an unreviewed `catalog.js` is not a
defect). One MINOR claim (blank dialog text) was wrong: the text is filled in
`handleGenerateClick`. Requirements (b), (d), (e) approved by the reviewer. Accepted
as complete.

**Tests:** the tester step was run by the coordinator (subagents on this harness do
not run commands). jsdom suite, 28/28 passed: tab switching and aria, key is a
password field and stays in memory, status never shows the key, region and model
selects and custom inputs, request URL and body, key absent from request, graph in
run order with blank templates, prompt content, dialog open/cancel/confirm, no fetch
calls, no fetch/XHR/storage/console/module syntax in source. `node --check` passed.

**Known limits:**
- Real calls from a browser page to Bedrock will likely be blocked by CORS; a small
  local proxy will probably be needed in the generation phase.
- The "build confirmed" flag is not cleared when cards change afterwards.
- Look and dialog feel not checked in a real browser.

**Completion status:** COMPLETE for this phase.

## Task: Desktop app (Electron shell)

**Goal:** run the prototype as a desktop app, not in a browser. The Bedrock settings
tab, system prompt, Generate button and confirm dialog already existed from the
previous phase, so they were not rebuilt.

**Changed files:** `package.json` (Electron pinned to 45.2.3), `main.js` (1280x800
window, contextIsolation on, nodeIntegration off, sandbox on, non-file navigation
blocked, new windows denied), `.gitignore` (`node_modules/`), `package-lock.json`,
`prototype/index.html` (CSP meta tag only). Card logic untouched.

**Run:** `npm install` once, then `npm start`.

**Plan:** subagent spec accepted. One correction: CSP is set by a meta tag, because
header-based CSP is unreliable for `file://` pages.

**Develop:** the developer subagent printed code but made no tool calls, so the
coordinator wrote the files from its output.

**Review:** the reviewer subagent made no tool calls, and its report contained wrong
facts (Electron 33.2.0, a `dist/` entry). It is NOT counted as an approval. The
coordinator checked the files directly: pinned version, security flags and CSP are
as specified. A separate reviewer pass is still open.

**Test:** the tester step was run by the coordinator. `node --check main.js` passed.
`npm install` succeeded with 0 vulnerabilities. The app launched, opened a window
titled "Visual Programming Prototype", and printed no errors on stderr. No jsdom
suite was re-run this phase; no card code changed.

**Known limits:**
- CSP `connect-src 'self'` blocks Bedrock calls on purpose. Widen it, or use a main
  process proxy, in the generation phase (this also avoids CORS).
- No installer or packaged .exe yet; the app starts with `npm start`.
- Look and feel in the window not checked by eye.

**Completion status:** OPEN. Implementation and smoke test pass; the independent
reviewer approval required by agent.md is missing.
