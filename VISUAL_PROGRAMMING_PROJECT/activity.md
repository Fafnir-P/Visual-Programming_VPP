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
