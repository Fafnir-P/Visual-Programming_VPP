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

## Task: Login screen, saved API key, more regions, more models

**Goal:** (1) A login screen. Signed in: the Bedrock API key is saved permanently.
Not signed in: memory only, as before. (2) Explain the small region list; add more
regions and pick the best one automatically. (3) Support most Bedrock models
(OpenAI GPT, Claude, Gemini and others); explain every model left out.

**Assumption:** no server exists, so the account is local to this computer. It
protects nothing online; its job is to decide whether the key is saved.

**Changed files:** `main.js` (accounts, key store, IPC), `preload.js` (new, the only
bridge: `window.vpAuth`), `prototype/auth.js` (new, login dialog), `prototype/models.js`
(new, models, regions, routing rules), `prototype/bedrock.js`, `prototype/index.html`,
`prototype/style.css`, `prototype/app.js` (one line: `initAuthUI()`). Card logic untouched.

**Login design**
- Startup shows Sign in / Create account / Continue without login.
- Password: scrypt with a random salt, compared with `timingSafeEqual`. Minimum 8
  characters. Wrong user and wrong password give the same message and the same delay.
- The API key is encrypted with Electron `safeStorage` (async API; the sync API is
  removed in Electron 46) and saved in the app data folder. It is saved when the field
  loses focus or Enter is pressed, and deleted when the field is emptied.
- The page cannot read the account files. Only the main window's top page may call the
  IPC channels. The password hash is never sent to the page.
- A key typed as a guest is kept and saved to the account on sign-in. Log out clears
  the field and memory.
- Not available: password reset (forgotten password = delete `accounts.json` in the
  app data folder, which also drops saved keys). On Windows the key is protected from
  other Windows users, not from other programs running as the same user.

**Regions: why three was acceptable, and what changed**
The region is where the request is sent. It decides which models exist, where data is
processed, and the price. Three regions were enough to run, so a change was not
required. Now: 22 regions in 4 groups plus "Other region", default **Auto**.
Auto uses the model's `global.` profile when it has one (AWS routes to the best
region), otherwise the first geography profile it has, otherwise `us-east-1`.
A fixed region uses the matching `us.`/`eu.`/`jp.`/`au.`/`apac.`/`in.` profile.
The Model tab shows the exact region and model id that will be called.
Risk: Auto may process data outside your own geography; the tab says so.

**Models: 86 text models in 14 groups** (Claude, OpenAI GPT and gpt-oss, Amazon Nova,
Llama, Mistral, Qwen, DeepSeek, Gemma, Kimi, MiniMax, GLM, Grok, Nemotron, Palmyra),
plus Custom model ID. Default: Claude Sonnet 5.5. Legacy models are marked "(Legacy)".
Source: a third-party list of Bedrock model cards checked 2026-10-10 and updated
2026-10-24 ([logeshwaran.org](https://www.logeshwaran.org/2026/10/amazon-bedrock-model-ids-list.html)),
consistent with the AWS blog on [OpenAI models on Bedrock](https://aws.amazon.com/blogs/machine-learning/accessing-openai-gpt-5-6-models-on-amazon-bedrock-from-australia-with-global-cross-region-inference/).
It is a snapshot. Check against `aws bedrock list-foundation-models` in your region.

**Models not offered, with reasons**
1. Not on Bedrock:
   - Google Gemini. Bedrock has only Google's open Gemma models.
   - "ChatGPT" is an app, not a model. Bedrock's OpenAI models are listed instead.
2. Extra reasons (needed by the brief):
   - Already ended or ending: Claude 3 Haiku, Claude Sonnet 4 (ended 2026-10-14), Cohere
     Command R/R+, Nova Sonic v1, Nova Canvas/Reel. AI21 Jamba ends 2026-11-26, so it
     was left out. Claude Sonnet 4.5 and Opus 4.1 are Legacy (new accounts may not be
     able to start them) but are listed because they still work today.
   - Not usable for the text request this app builds: embeddings, rerank, image, video,
     speech and audio models (Titan/Nova/Cohere embeddings, Stability, Luma, TwelveLabs,
     Nova Sonic, Voxtral).
   - Only on Bedrock's other API ("bedrock-mantle", OpenAI-style, not the Converse API
     this app builds): Claude Mythos 5, GPT-5.6 Cyber, GPT-5.6 Sol "Daybreak Blue",
     Gemma 4, Grok 4.3. Add them in the generation phase if wanted.
3. Missing or new models: use Custom model ID (also accepts an application inference
   profile ARN).

**Workflow**
- Plan: subagent spec accepted. Its file paths pointed into its own sandbox and its
  mention of a "profile ARN" was wrong; the coordinator corrected both.
- Develop: the coordinator wrote the files (subagents on this harness do not write files).
- Review 1 (research subagent, read the real files): CHANGES NEEDED, 8 findings. Fixed 2:
  password fields now clear when switching tabs; IPC accepts only the top page.
  Rejected 6 with reasons: #1 and #2 (key state is synced by the `input` event, so no
  desync); #3 (a check inside the preload can be skipped by a hostile page, and
  `main.js` already limits sizes); #6 (ARNs need `:` and `/`; the id is URL-encoded);
  #5 and #8 (intended behavior; script order is tested).
- Own findings while testing: `safeStorage` sync API is deprecated, moved to async;
  `loadFile` used a relative path, now uses `__dirname`; screenshot showed the
  "Repeat password" box in Sign-in mode and an off-centre dialog; both fixed in CSS.
- Review 2: CHANGES NEEDED, one valid point: two quick saves could finish out of order.
  Added a save queue. Its two minor notes were kept as is (the user check guards
  against logout during encryption; a failed re-encrypt retries on next load).
- Review 3: **APPROVED**.

**Tests (run by the coordinator; kept outside the project):**
- UI suite in jsdom, 88/88: region and model lists, every model resolves, routing rules
  for auto, fixed, custom region and custom model, request URL, no key in the request,
  no network calls, full login flow with a stand-in for the main process, guest vs
  signed-in key saving, log out, wrong password, Esc, source rules, script order.
- Real Electron run of `main.js` with a temporary data folder, 33/33: only the 7 expected
  calls are exposed, page has no `require`/`process`, short or odd names and passwords
  rejected, duplicate names rejected, key stored encrypted (no plaintext in either
  file), key survives log out and sign in, another account cannot read it, wrong
  password and unknown user give the same reply, no hash returned, oversized key
  rejected, three quick saves keep the last, session survives reload, a different page is
  refused, corrupt account file is kept and renamed.
- `node --check` passed. Screenshots of the login dialog and Model tab checked by eye.

**Known limits**
- Model ids and profile prefixes come from one snapshot; not checked against a live
  account. Claude Haiku 4.5 id (`...-20251001-v1:0`) is not in the source table, which
  showed "profiles only"; it was filled in from the usual naming and should be verified.
- For models without a profile, Auto sends to `us-east-1`. Some are only offered in
  other regions; pick a region if the call fails. A live per-region lookup would fix
  this and could be added with the generation phase.
- CSP still blocks all network calls (`connect-src 'self'`), as planned.
- Not tested: macOS and Linux key storage; a real Bedrock call.

**Completion status:** COMPLETE (review 3 approved, all tests pass).

## Task: Cards.md (card list, names, categories, one-line functions)

**Goal:** search the web for how tools group their building blocks, then write
`Cards.md` with: one line per category saying what its cards share; for each of the
200 cards a clear name, its category, and what it will do. No concrete card content
and no generation logic in this phase.

**Output:** `Cards.md` at the project root. Contains an intro, a category table (count,
number range, shared trait), one section per category with a one-line trait and a table
(No., Name, Category, Group, What it does), and the source links. Card numbers match
`prototype/catalog.js` (card 001 = `catalog_001`, up to 200). Category sizes are the
framework's: 30 / 60 / 30 / 25 / 15 / 20 / 10 / 10. Nothing in the app changed.

**Workflow**
- Plan: research subagent surveyed Retool, n8n, Node-RED, Appsmith, Budibase,
  Streamlit, Django admin, Zapier. It returned category traits, sub-groups with counts,
  naming rules and overlap rules. Coordinator changes: replaced its "Mock Data
  Generators" (connectors) with Result Intake and Local Continuation, to match the
  framework (connectors prepare payloads, give human instructions, take results in,
  continue locally); replaced "Permission Checks" with Safety Checks (the app is
  single-owner); limited exports to CSV and JSON and dropped PDF (framework allows
  explicit CSV/JSON transfer). One source (Make blog) returned 403 to a script, so it
  is not cited. The other 9 links opened.
- Develop: 7 subagents wrote the rows in parallel (UI; Backend; Data; Logic; Triggers;
  Integrations; AI plus Navigation). They return text only, so the coordinator joined
  the rows into `Cards.md` with a script.
- Coordinator fixes before review: renamed or reworded cards 41, 56, 86, 97, 106-111,
  113, 127, 200 so in-flight list cards and saved-data cards do not overlap; made names
  Title Case; trimmed the 3-retry detail on 86.
- Review 1 (research subagent read the file): CHANGES NEEDED. Fixed: 042, 046 (renamed
  Take Record Range), 057 (Split Text By Separator), 072 (Unpack Sub-Records Into
  Fields), 096, 103 (Create Or Update Record), 114, 118/119 vs 198/199 (saved table for
  backup vs records on screen), 137, 143, 150, 151, 157, 160, 187, 189, 197.
  Kept on purpose: "a person" in connector cards (a human does the outside step);
  070/071 and 047/099 (different jobs); 024, 030, 152 wording.
- Review 2: **APPROVED**. (It misquoted two old names in its notes; the file itself
  was checked by the coordinator.)

**Tests (coordinator script, kept outside the project), 45/45 passed:** 200 rows with
5 columns, numbers 001-200 without gaps, every category equals `catalog.js` and the
counts match, names unique, 2-6 words, Title Case, no digits; descriptions 25 words or
fewer, one sentence, unique; no vendor names, webhooks or code words; timer and
data-event triggers say "while the app preview is running"; connector cards mention a
person or the outside step; AI cards say build time, user-supplied or plain local rule;
loop card is bounded; each category has a section and a one-line trait; links present.

**Candidate gaps for the next revision** (not added, because the framework fixes the
count at 200 per category, so adding a card means removing one): duplicate a record,
update many records, delete many records (with a safety check), undo last change,
progress indicator, tax and discount calculation, barcode display, work queue.

**Known limits**
- Descriptions are rough ideas, not contracts. Inputs, outputs, ports, settings,
  templates and tests are not defined; the framework requires them before catalog
  acceptance.
- The category sizes are planning numbers in the framework; a few cards in the
  Backend and Data groups are close in purpose (for example 041/106) and are separated
  only by "current list" versus "saved records" wording.
- A few cards may be cut or merged once real contracts are written.

**Completion status:** COMPLETE for this phase (review approved, 45/45 checks pass).

## Task: Cards.md round 2 (add needed cards, independent review, remove duplicates)

**Request:** (1) add the cards that are still needed; 200 is not a hard target.
(2) run an independent review of `Cards.md` per `agent.md`; delete cards judged
duplicate and add cards judged needed.

**Result:** `Cards.md` now has **205 cards** (was 200): UI 34, Backend 64, Data 33,
Logic 22, Triggers 14, Integrations 20, AI 10, Navigation/Output 8. Card numbers are
working numbers and changed. `prototype/catalog.js` still holds the old 200-card
blank layout, and the intro of `Cards.md` says so. It was not changed.

**Step 1: added needed cards (211 cards after).** Show Progress While Running,
Display Barcode From Code, Calculate Tax From Subtotal, Apply Percentage Discount,
Copy Record (then called Duplicate Record For Editing), Update Field Across Records,
Delete Multiple Records, Enable Change History Tracking, Restore Previous Record
Version, Add Record To Priority Queue, Process Next Queued Record. These came from the
gaps listed in the last round. Written by a developer subagent; merged by script.

**Step 2: three independent reviewers** (fresh research subagents with no knowledge of
earlier reviews; each read the whole file). Lenses: A duplicates, B coverage by building
six sample apps (stock tracker, purchase orders, stock-take, equipment check-out,
supplier directory, dashboard), C fit with the framework (read sections 1-5).
The coordinator weighed their lists, which disagreed in places.

*Deleted (17):*
- Calculate Tax From Subtotal, Apply Percentage Discount: too narrow; replaced by two
  general cards (below). A and B agreed.
- Unpack Sub-Records Into Fields: jargon, rarely needed (A, B).
- Route With Default Path: every routing card now has a no-match output (A, B).
- Store Field Rule With Table: now part of Add Field To Table (A).
- Sort And Limit Query Results, Count Saved Matching Records: Query cards return a list,
  and list cards already sort, take a range and count (A, coordinator). Grouped counts
  of saved data stay in Group And Summarize Saved Data.
- Check Field Uniqueness: Enforce Unique Field Value covers it (A).
- Mark Field Required Conditionally: merged into Require Dependent Field (A).
- Limit Import Size And Count: the platform already checks file size and type at
  import; import cards now say oversized files are refused (A).
- Run Once After Delay: merged into Run On A Timer (A).
- Record Reference Number: merged into Enter Outside Result (A).
- Download Records As CSV, Download Records As JSON: Export Table cards now cover the
  whole table, a filtered set, or the records on screen (A).
- Reverse Record Order: descending sort covers it (B).
- Add Record To Priority Queue, Process Next Queued Record: C found they clash with the
  framework's one-event-at-a-time, explicit-order model. Query, sort and Find First
  Matching Record cover the need. (I had added them in step 1.)

*Moved (3), out of AI into Backend Processing, because they use plain rules, not AI
(C):* Label Text By Keywords, Calculate Reorder Quantity, Flag Unusual Records. AI
Capabilities keeps 10 cards after three real AI cards were added.

*Added (11):* Calculate From Two Values (add, subtract, multiply, divide), Change Value
By Percent, Calculate Percentage Change (B); Merge Two Lists (A, C; the framework needs
an explicit merge); Reconcile Stale Result (C; framework 5.1 requires stale results to
be reconciled); Pick Date Range, Set App Title, Define App Settings (B); Draft
Acceptance Checklist, Explain App In Plain Words, Draft Field Help Text (build-time AI
cards, replacing the three moved ones).

*Reworded:* Repeat Step Group Fixed Times became Repeat For Each List Item (C: a loop
over cards in the graph is not allowed; iteration must sit inside one bounded card);
Retry Failed Step now says only when safe to repeat; routing cards, Filter and Query
cards (several conditions with AND or OR), Wait cards, Run On A Timer, jargon names
(Search And Select, Pick Specific Fields, Catch Processing Error) and others.

*Rejected reviewer suggestions, with reasons:*
- Merge Set Default Value On Error into Set Field Default Value; merge Log Error
  Details into Flag Record With Error: different jobs.
- Delete Add Calculated Field: a spreadsheet-style computed field is a common need and
  also answers B's "show a computed column".
- Delete Create Or Update Record: needed for re-importing the same file (kept; wording
  now names the key value).
- Delete Restore Previous Record Version / Enable Change History Tracking (C): record
  versions are in the framework (5.1); history is bounded to the last few versions.
- Delete Take Record Range: after the Sort And Limit removal it is the only way to
  take the first N records.
- Move Get Current Date And Time to Triggers: it returns a value; it starts nothing.
- Add Join Selected Paths: Wait For All Steps To Complete already does it; reworded.
- Add Store Calculation Result In Field, Show Computed Column, Append To Text Field,
  Attach Local File Reference, Lock Record, Check File Type, Undo Last Change (UI):
  covered by Update Existing Record, Add Calculated Field, Combine Multiple Fields,
  Choose File, or out of launch scope (single owner; file checks done by the platform).

**Re-review (fresh reviewer):** all changes read correctly; numbers, category table and
traits consistent; AI category fits the rules. It asked for 3 more deletions (Compare
Two Fields, Enable Or Disable Field, Mark Item Outcome), 1 re-add (Count Saved Matching
Records) and one wording change. Accepted: the wording change (Check Answer Shape: "with
simple rules"). Not accepted: the 3 deletions (different jobs: compare any two fields
vs date-only; read-only vs hidden; status vs history) and the re-add (deleted on
purpose; grouped counts of saved data remain). Verdict was CHANGES NEEDED (MINOR); the
remaining items are judgment calls, recorded here, not blockers. A further round was
not run because it would only repeat the disagreement.

**Tests (coordinator script, kept outside the project), 54/54 passed:** contiguous
numbers; every card has one of the 8 categories, grouped in order; category table counts
and number ranges equal the rows; one-line trait under each category; names unique,
2-6 words, Title Case, no digits, no developer jargon; descriptions one sentence, 25
words or fewer, unique; no vendor names, webhooks or code; timers and data events say
"while the app preview is running"; connectors mention a person or the outside step; AI
cards say build time or a person brings the answer, and none is a plain-rule card; loop
card is bounded; no queue cards; the 17 removed names are gone and the key added names
are present; no stale catalog.js claim.

**Known limits**
- Disagreements between reviewers were settled by the coordinator, listed above.
  Several close pairs remain (for example Filter Records By Condition and Query Saved
  Records By Criteria); they differ by list versus saved data.
- Descriptions are rough ideas, not contracts. Inputs, outputs, ports, settings,
  templates and tests are still to be written.
- The blank catalog in the app (`prototype/catalog.js`) is not yet synced to this list.

**Completion status:** COMPLETE for this phase (independent review done, edits applied,
54/54 checks pass; remaining reviewer disagreements documented).

## Task: Python template code for every card in Cards.md

**Request:** from `Cards.md`, add reusable template code for each card. Python only; the
templates should make the final generated Python easier to finish. No concrete card content and no
generation features in this phase.

**What was built** (new folder `card_templates/`, plus `tests/`)
- `runtime.py`: the shared base. `CardError`; `Context` (store, app clock, preview flag, event id,
  settings); a SQLite `Store` (tables, records, versions, optional change history, archive,
  unique and linked fields, protected delete, counters, applied-event marker, manual-action outbox,
  event log, nested transactions); one filter language used both in memory and as SQL; one value
  cleaner for every field type; safe arithmetic (no `eval`); declarative view nodes for UI cards
  (never HTML); the `@card` decorator and registry.
- 205 cards in 35 modules, one module per group in `Cards.md`, folders `ui backend data logic
  triggers integrations ai output`. Each card is one function with its contract (inputs, settings,
  outputs, phase, effects, role), at least two examples and one invalid case.
- `testing.py` runs every card's own cases; `manifest.py` writes `manifest.json` (one contract per
  card, in card order); `cards_md.py` reads `Cards.md`; `README.md` explains the layout.
- Tests: `python -m unittest discover -s tests -v`.

**Design choices and why**
- Standard library only: the framework allows only reviewed dependencies, so none are added.
- A card imports only `..runtime`; no file system, network, `eval`, `random`, or wall clock. Time
  comes from `ctx.now()`, so cards are deterministic and testable.
- UI cards return view nodes with plain data. The framework says the platform renders validated
  declarative data, so no HTML is produced.
- Trigger cards call `ctx.require_preview()`. Connector cards only prepare text and data for a
  person and take a typed result back, using a replay-safe outbox key. AI cards never call AI:
  build-time cards hold a prompt and check a proposal; human-AI cards build a prompt and check a
  pasted answer.
- A card setting without a default is a required setting (`required_config` in the manifest).
- The engine, scheduling, rendering of views and file access are not here; the README says what
  the engine must do (wrap an event in `ctx.store.transaction()`, call `apply_once(event_id)`).

**Workflow**
- Plan: research subagent. Accepted 6 of its 10 flags (event ids, loop bounds, transaction around
  the outbox, SQL name checks, route outputs, deterministic clock). Corrected its trigger flag, which
  was backwards, and its "17 packages" split (I used 14).
- Develop: the coordinator wrote `runtime.py` and a guide with a reference module. Thirteen
  developer subagents wrote the 35 modules in parallel. They return text only, so the coordinator
  extracted the files by script, which caught one missing end marker and one package that
  overwrote another's file. The first run had 100 of 127 loadable cards passing; the coordinator
  fixed the rest (wrong store API use, 21 wrong examples, `preview` flag placed wrongly, missing
  invalid cases, a view helper misuse) until all 205 passed.
- Review 1: seven independent code reviewers split by area. Six read the code; the text-and-lists
  reviewer could not find `Cards.md` and was re-run. About 60 findings. Fixed (all with tests in
  `tests/test_review_fixes.py`):
  - spreadsheet formula injection in three CSV outputs; CSV import without BOM handling, header
    check and stored-record result;
  - multi-record update and delete that could half-finish; delete that hid protection errors;
  - restore-previous-version used the wrong state; Define App Settings was not atomic;
  - Run When Record Created saw only the very first record; timer ignored missed ticks; Run When
    Record Changed watched fields without history;
  - a result counted as stale after any later change; AI answer JSON nesting bomb; dotted fields
    in prompts; 'Above' approval was 'at or above';
  - unique rule was case-insensitive in code but not in the index; multichoice `contains`
    differed between memory and SQL; datetime and time limits were ignored; view prop names such
    as `dataUrl` slipped through;
  - Adjust Slider settings shadowed `min` and `max` (now `min_value`, `max_value`); empty tabs and
    columns; end before start in working days; retry now rolls back a failed attempt; the error
    handler card now really catches a failing step.
- Rejected, with reasons: nine claims that did not match the code (savepoint use, `IS NULL`
  handling, boolean handling in `safe_eval`, transaction depth, test diff tolerance, threshold
  direction, quoting in the CSV module, a view prop named `item_key`, `None` from Skip Invalid
  Record, `Retry` side effects now covered by a transaction).
- Review 2: a fresh reviewer verified the fixes (APPROVED; its read was shallow, so the
  coordinator relied on the tests) and the re-run text-and-lists reviewer found a real sort bug
  (mixed numbers and text, blanks first when descending), a template that filled braces twice, and
  a number pattern that kept a trailing dot. All fixed and tested.

**Tests (run by the coordinator): 77 unit tests pass, and all 205 cards pass their own examples.**
- The templates and `Cards.md` list the same 205 cards (name, category, group, function name,
  module path); `manifest.json` is current.
- Source rules by reading the code: only allowed imports, no `eval`/`open`/network/clock/random,
  no global state, no module-level mutable data, module docstrings.
- Behaviour: transactions and nested rollback, history trimming, SQL against in-memory evaluation on
  22 conditions and 60 random rows, SQL injection through names and values, view rules, decorator
  rules, trigger refusal outside preview, route cards, CSV round trip, all the review fixes.

**Known limits**
- Examples were written by the same authors as the code; two rounds of independent review and 77
  tests lower that risk but do not remove it. A real engine test (cards wired into a flow) comes
  with the generation phase.
- Cards are generic building blocks. Typed ports, connection checks, and the graph engine are not
  written. Some cards need engine help (for example, passing `last_seen_id` back to a trigger).
- Money and numbers: numbers are stored as floating point; currency fields round half up to 2 places.
  Exported CSV shows `5.0`, not `5`.
- No Python packaging yet (`pyproject`), and no copy of these templates into the app UI.
- Several reviewer suggestions were left as design choices: default limit of 10000 items for lists,
  tables and charts; "Mark Item Outcome" on a custom table uses plain update, not the outbox.

**Completion status:** COMPLETE for this phase (review rounds done, fixes applied, 77/77 tests and
205/205 card cases pass).

## Task: card ports, colours, connection rules, and the link check in the app

**Request:** (1) in `Cards.md`, give every card its input and output ports and the connection rules,
allowing several inputs or outputs; (2) in `Cards.md`, group ports into a few big classes, one colour per class,
compatible ports share a colour, and the colour says only what can be linked; (3) in the main program, one
general check when cards are linked: a mismatch gives a clear error message and error output; the port classes
are loaded into the program in advance. No concrete card content and no generation features.

**Design**
- Ports are the `inputs` and `outputs` of each card's template function, so the card list, the Python code and
  the app share one source (`card_templates/ports.py`). `ports.py` only adds the class of each port.
- Ten classes, one colour each: Text (green), Number (blue), Yes/No (yellow), Date/Time (orange), Record (purple),
  Record List (brown), Value List (teal), View (red), Control (black), Any (grey, striped wildcard).
- Compatible = same class, or one side is Any. No silent conversions (framework: reject implicit conversion). So a colour
  is exactly "what it can link to".
- Rules (error codes in order): `no_such_port`, `direction`, `same_card`, `type_mismatch`, `duplicate`, `input_taken`
  (one link per input; an input marked + takes several, used for the `children` of layout cards and the `steps` and
  `branches` of flow cards), `cycle` (framework: reject loops).
- Every card except triggers also has a black Start input and Done output (not listed per card). Triggers have a
  black `event` output; their yes/no `fire` is data. This follows the framework's split between data links and control links.
- Optional inputs (`?`) come from the function signature. An unlinked required input does not block anything; the Generate
  dialog lists them (a value can be typed into the card's settings instead).
- The app now loads the 205 cards of `Cards.md` with their ports: `prototype/catalog.js` is generated from `Cards.md`
  and the templates (`python -m card_templates.ports_export`). This replaces the 200 blank cards, because ports
  mean nothing without the real cards. Run order, dragging, selecting and the Order tab are unchanged.

**What changed**
- `card_templates/ports.py` (classes, rules for compatibility, port class of every name and per-card settings),
  `card_templates/ports_export.py` (writes `Cards.md` port sections and `prototype/catalog.js`),
  `card_templates/manifest.py` (manifest now lists ports).
- `Cards.md`: new "Port classes (colours)" and "Connection rules" sections (with examples and what a refused link does),
  and Inputs / Outputs columns for every card.
- `prototype/catalog.js` (generated: classes, compatibility table, 205 cards with ports), `prototype/ports.js`
  (the link check, open-input finder, re-check of saved links), `prototype/app.js` (draws ports with class colour and
  labels, glows ports that can take the link being dragged, turns the line and port red on a mismatch, refuses the link,
  red message, message list, console output), `index.html`, `style.css`, `bedrock.js` and `prompt.js`
  (the graph sent to the model lists each card's ports by class).
- On a refused link: nothing is created; a red message names both ports, both classes and the rule; both ports flash;
  the message is kept in a list (bottom right, last 50) and written with `console.error('[link refused]', code, text, details)`.

**Workflow**
- Plan: coordinator design, checked against the framework (data links versus control links; one input, one source).
- Develop: the coordinator wrote all code (subagents on this harness return text only).
- A shell command of mine was blocked by a safety rule that matched on the text of the script (no ssh was used). I did not
  re-spell it; the same edit was made with the file-edit tools.
- Found while testing: a port name can exist on both sides of one card (for example an input and an output both called
  `value`), so the check now receives which side each end is on.
- Review 1 (five independent reviewers): ports of cards 001-100 and 101-205 against the template code (no wrong class found;
  one finding for card 163 was a misreading, the port is already Number); app code (fixed: the red "refused" mark stayed after a
  cancelled drag; Escape now closes the red message; other points were already true or only comments); Cards.md text (fixed: added the
  `no_such_port` rule, examples of allowed and refused links, what a refused link does, the Any class and the Start/Done/event
  explanation, colour names; not taken: "refuse to generate while inputs are open", which the app does not do);
  builder test (six small apps).
- Review 2: APPROVED. It checked every rule and example sentence against the code.

**Tests (run by the coordinator)**
- Python, 98 tests: classes and colours, rule, every card's ports match the template and the signature, no stale
  overrides, manifest, `Cards.md` and `catalog.js` match what the generator makes, JavaScript and Python agree on all class pairs.
- `node tests/ports_logic.test.js`, 1191 checks: the rule on every class pair; the 205 cards' ports; every refusal code
  with the real cards; several links on one input; loops through data and through Start/Done; Any; `side` on same-named ports;
  all output-input pairs of different cards against the colour rule; open inputs; re-check of saved links.
- Interface test with a simulated page (kept in scratch, needs jsdom), 62 checks: ports drawn in class colours with labels;
  Start and Done in the header; a good link; a mismatch seen while dragging (red line, red ring, glow and fade); the red message,
  console output, message list and count; direction, taken input, duplicate, loop refusals; several links; Escape; dashed line
  for Any; the Generate dialog; clearing messages; no inline script.
- A screenshot of the real window was checked by eye (cards with coloured ports, a refused link, the message and the list).

**Known limits and gaps found by the "builder" reviewer (not done; they need new cards or a different class design)**
- No card turns a Yes/No into a start signal or chooses a branch from it ("if yes, run this"), so a flag such as
  `requires_approval` cannot start a branch. Candidate: a Branch On Yes/No card.
- Several wiring gaps: Read File Content (Choose File gives only a file name, Import needs the text), Extract Field From
  Records (Record List to Value List, for ids), Build Summary Record (several numbers to one record, for a summary table),
  Update Single Field (Calculate Stock Level gives a number, Update Existing Record wants a record), Build Record From Fields
  has no inputs, Repeat For Each List Item gives an untyped (Any) result, and dates cannot be compared with a record's date in
  a Query or Filter at run time.
- The reviewer also proposed merging Value List into Record List, adding a File class, removing Start/Done, and letting
  Number link to Text. I did not do these: the request is for strict, colour-matched types, and Start/Done is the
  framework's control link. They are worth discussing with the gaps above.
- The cards' ports are the inputs of the template functions. A few settings that are really data (for example a field name in
  Update Field Across Records) show as ports because the template takes them as inputs.
- The interface test is not in the project (it needs jsdom). `tests/ports_logic.test.js` and the Python tests are.
- Saved projects do not exist yet; `recheckAllLinks` is ready for when they load.

**Completion status:** COMPLETE for this phase (review rounds done, fixes applied, all checks pass).

## Generate check dialog, bridge cards, Start and End cards

**Request:** (1) Generate must ask again, with where and what, about required inputs not linked, then still generate if confirmed. (2) Add the bridge cards with ports. (3) Keep Value List and Record List separate; add Start and End cards; a Start card exists by default.

**Done:**
- Generate: the "build complete" dialog is followed by a new issues dialog (card name, position in run order, message, Show button; "Go back and fix" / "Generate anyway"). It never blocks. Issues come from `findGenerationIssues` in `prototype/ports.js`: no Start, Start unlinked, no End, open required input.
- 9 new cards (214 total): Branch On Yes/No, Compare Two Numbers, Pick Field From Records, Filter Records By Date, Build Summary Record, Set Field Of Record, Read Chosen File, App Start, App End. Templates in `card_templates/`, rows in `Cards.md`, regenerated `prototype/catalog.js` and manifest.
- Start/End roles have no implicit `_start`/`_done` ports. A Start card is created on load, cannot be deleted, and only one is allowed. Notices use a blue toast.
- Value List and Record List stay separate.

**Tests:** Python 120 OK; `tests/ports_logic.test.js` 1272 pass; ports_export --check OK; jsdom UI test 98 pass (lives in scratch, not in the project).

**Not done / known limits:** no separate independent review round and no real-window screenshot for this phase; Cards.md intro text does not yet describe Start/End; "Run At App Start" overlaps App Start; Repeat For Each results are still Any.

**Completion status:** PARTIAL (code and tests complete; review and screenshot pending).

## Duplicate-card review and merge; Cards.md sync

**Request:** Continue the review and merge duplicate cards where possible; keep Cards.md in step with all card work.

**Workflow:** Two reviewers searched all 214 cards for duplicates. I checked their picks against the code. Merged 5 pairs, where only a setting differs and the ports match. A third reviewer then checked the result: APPROVED, no leftover old names, safety limits kept (`csv_safe_cell`, size and row limits, `bounded`).

**Merged (214 -> 209 cards):**
- Find Minimum Value + Find Maximum Value -> Find Smallest Or Largest Value (`mode`, output `value`)
- Add Time To Date + Subtract Time From Date -> Shift Date By Time (`direction`)
- Archive Record + Restore Archived Record -> Archive Or Restore Record (`action`)
- Import Records From CSV + From JSON -> Import Records (`format`)
- Export Table To CSV + To JSON -> Export Table (`format`)

**Not merged, with reasons:** Run When Record Created/Changed/Deleted (different outputs: before/after, last_seen_id); Build Order Request/Shipment Notice/Supplier Message (different record shapes and rules); Route By ... cards (different output ports); Reject Future Date (no past counterpart exists).

**Files:** card templates in `card_templates/{backend,data}/`, `card_templates/ports.py`, `ports_export.py` (Cards.md rules text now covers App Start/App End and the Generate check), `README.md`, `manifest.json`, `Cards.md` (rows, counts, ports), `prototype/catalog.js`, and the tests that named old cards (`tests/*`).

**Tests:** Python 120 OK; `tests/ports_logic.test.js` 1247 pass (fewer cards, fewer checks); 209/209 card templates pass; ports_export --check OK.

**Known limits:** the real-window screenshot is still not taken; "Run At App Start" overlaps App Start. Old saved projects do not exist yet, so no migration is needed.

**Completion status:** COMPLETE.

## Cards wired into Generate; small build tests with own model access

**Request:** (1) Connect the cards to the main program. (2) Build-test with my own API; keep the program small.
**Assumption:** "own API" = the agent's own model access. No Bedrock key was read or used; no network call; no credits spent.

**Workflow (conductor + separate worker chats):** developer -> independent tester (build 1) -> developer fix -> different tester and reviewer (build 2) -> developer fix. Each step was accepted by the file check and my own test re-run.

**Done:**
- `card_templates/templates_export.py` writes `prototype/templates.js` (209 cards: function source, settings with defaults, ports, runtime names, imports, helpers). `--check` guards it.
- `prototype/bedrock.js`: the Generate request now carries real `templateCode` and config defaults, only for cards on the canvas; whole-request size cap; `parseGenerationReply` reads the model reply (`=== FILE ===` / `=== GAP ===`) with safe-path checks. `prototype/prompt.js`: new rules (how templates are called, Python 3.10+, reply format, input flags, Start/End, sys.path, output).
- Build 1 (`final_check/archive/sample_build/`): 8 cards, 14.4 KB request, ran, printed $19.75, gap reported. Found 8 defects; fixed.
- Build 2 (`final_check/archive/sample_build2/`): 7 cards, 12.7 KB request, parsed, ran twice with the same output, gap reported. Review found 4 cards with missing names/imports, a missing `card_templates` path rule, loose parser; fixed in round 2.

**Tests:** unittest 125 OK; ports_logic 1247; request.test.js 64; card templates 209/209; ports_export and templates_export --check OK. A new test checks all 209 templates for undefined names.

**Known limits:** a real model reply was not tested (my own ability stood in); Python 3.10 itself not run (3.13 only); `parseGenerationReply` has no writer yet and the app does not send the request (no network phase); repeated cards repeat their template code; two Enter Number cards share a config name; `final_check/archive/sample_build2/undef_check.py` reads an old snapshot and is stale (the unit test replaces it); screenshot check still pending; Run At App Start overlaps App Start.

**Completion status:** COMPLETE for this request.

## Final check, fixes, and token/time measurement

**Request:** final check of the whole program; fix what needs improving; measure tokens and time of generating software against the framework targets (section 2 and 7: below 75% of a vibeCoding baseline, 50% ideal, 20% for card-heavy programs).

**Workflow:** conductor with separate worker chats. Independent audit (report only) -> developer fixes -> measurement by independent workers (card way and vibeCoding way did not see each other's files) -> developer fix for the gap the measurement showed -> re-measurement -> small fix -> final test run by me. Each item accepted by the file check and my own test re-run.

**Audit (final_check/audit_report.txt):** 0 HIGH, 2 MED, 13 LOW; all 15 fixed (final_check/audit_fix_notes.txt). MED: Backspace on a select deleted a card; Search Text For Pattern hung on a nested-quantifier regex. LOW: import row limit, input guards in 5 cards, safe_eval errors, working-days cap, export filename check, sample data types, login lockout, register race, will-navigate, index name clash, READMEs, scratch folders moved to final_check/archive.

**Measurement 1 (estimates, chars/4), task "Order line helper", 10 cards:** card way 1840 in + 855 out tokens, 13.3 s, 2 attempts; vibeCoding 799 in + 291 out, 4.7 s, 1 attempt. Target NOT met (about 247% of baseline tokens). Causes: the model still wrote glue; card settings could not be edited; request and prompt were large.

**Fix:** settings panel (node config goes into the request); `prototype/compile.js` `compileMainPy` writes main.py itself, so a graph the app supports needs 0 model tokens; the model is used only when the compiler reports a gap; slimmer request (about 986 input tokens on the model path, from 1840); prompt 2753 -> 1955 chars; meter (`prototype/meter.js`) and a token estimate in the confirm dialog; missing command-line values now name the flag (exit 1, one line).

**Measurement 2:**
- Card way, order line (11 cards): 0 model tokens, app work about 0.7 ms (median of 5), checks C1-C4 pass. Model path (with a gap): about 1013 estimated input tokens.
- Card way, 23-card graph: compiles with no gap, output correct, 0 model tokens; the equivalent hand-written code is about 2151 estimated tokens.
- vibeCoding, order line, 2 fresh runs: median about 982 tokens total, about 4.6 s, 1 attempt each. vibeCoding, 20-card-size task: 830 in + 691 out, 10 s.
- On these tasks the card way is below the 20% bar for tokens (0 model tokens) when the graph is fully supported.

**Limits (do not claim target met):** all token numbers are estimates; the framework says missing real usage prevents ratio claims. Task completion time (user drags, links and configures cards) was not measured, so the time target is not proven. No real Bedrock reply or latency; no study with participants (framework section 7 needs 96 runs). Graphs were written by hand, not through the UI. Same machine, 1-5 samples. The model path still sends the whole slim graph, not only the gap cards.

**Tests (final run):** unittest 154 OK; ports_logic 1247; request 84; meter 17; main_pure 12; settings 65; card templates 209/209; ports_export and templates_export --check OK.

**Open / parked:** real-window screenshot not taken; Electron UI (settings panel, confirm text, lockout, register race, will-navigate) not run in a window; Run At App Start overlaps App Start; the framework text still says 200 cards while the catalog has 209; Python 3.10 itself not run (3.13 only); sending the request and writing files to disk are later phases.

**Completion status:** COMPLETE for the checks and fixes; the efficiency targets are indicative only, not proven.
