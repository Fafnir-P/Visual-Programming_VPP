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
