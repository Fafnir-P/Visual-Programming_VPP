// ============================================================================
// AWS BEDROCK INTEGRATION
// ============================================================================
// This module manages Bedrock API configuration (credentials, region, model)
// and assembles the Converse API request. It does NOT execute network calls;
// that responsibility is deferred to a later phase.
// Model and region data, and the routing rules, live in models.js.
// The API key lives only in bedrockState.apiKey. When the user is signed in,
// auth.js also saves it (encrypted) through the main process.

const bedrockState = {
    apiKey: '',
    region: 'auto',          // 'auto' | 'custom' | region code
    customRegion: '',
    modelId: DEFAULT_MODEL_ID,   // catalog id or 'custom'
    customModel: ''
};

function currentBedrockTarget() {
    return resolveBedrockTarget({
        region: bedrockState.region,
        customRegion: bedrockState.customRegion,
        modelId: bedrockState.modelId,
        customModel: bedrockState.customModel
    });
}

function addOption(parent, value, text) {
    const opt = document.createElement('option');
    opt.value = value;
    opt.textContent = text;
    parent.appendChild(opt);
    return opt;
}

function populateRegionSelect(select) {
    select.textContent = '';
    addOption(select, 'auto', 'Auto (recommended)');
    REGION_GROUPS.forEach((group) => {
        const og = document.createElement('optgroup');
        og.label = group.label;
        group.regions.forEach((r) => addOption(og, r.value, r.label + ' \u00b7 ' + r.value));
        select.appendChild(og);
    });
    addOption(select, 'custom', 'Other region...');
    select.value = bedrockState.region;
}

function populateModelSelect(select) {
    select.textContent = '';
    const groups = new Map();
    MODEL_CATALOG.forEach((m) => {
        if (!groups.has(m.provider)) {
            const og = document.createElement('optgroup');
            og.label = m.provider;
            groups.set(m.provider, og);
            select.appendChild(og);
        }
        addOption(groups.get(m.provider), m.id, m.label);
    });
    addOption(select, 'custom', 'Custom model ID...');
    select.value = bedrockState.modelId;
}

function initBedrockUI() {
    const apiKeyInput = document.getElementById('bedrockApiKeyInput');
    const apiKeyToggle = document.getElementById('bedrockApiKeyToggle');
    const regionSelect = document.getElementById('regionSelect');
    const customRegionInput = document.getElementById('customRegionInput');
    const modelSelect = document.getElementById('modelSelect');
    const customModelInput = document.getElementById('customModelInput');

    populateRegionSelect(regionSelect);
    populateModelSelect(modelSelect);

    // API key input
    apiKeyInput.addEventListener('input', (e) => {
        bedrockState.apiKey = e.target.value;
        updateBedrockStatus();
    });

    // Show/Hide API key toggle
    apiKeyToggle.addEventListener('click', () => {
        const isPassword = apiKeyInput.type === 'password';
        apiKeyInput.type = isPassword ? 'text' : 'password';
        apiKeyToggle.textContent = isPassword ? 'Hide' : 'Show';
    });

    // Region select
    regionSelect.addEventListener('change', (e) => {
        bedrockState.region = e.target.value;
        customRegionInput.hidden = bedrockState.region !== 'custom';
        if (!customRegionInput.hidden) customRegionInput.focus();
        updateRouteInfo();
    });

    customRegionInput.addEventListener('input', (e) => {
        bedrockState.customRegion = e.target.value;
        updateRouteInfo();
    });

    // Model select
    modelSelect.addEventListener('change', (e) => {
        bedrockState.modelId = e.target.value;
        customModelInput.hidden = bedrockState.modelId !== 'custom';
        if (!customModelInput.hidden) customModelInput.focus();
        updateRouteInfo();
    });

    customModelInput.addEventListener('input', (e) => {
        bedrockState.customModel = e.target.value;
        updateRouteInfo();
    });

    updateBedrockStatus();
    updateRouteInfo();
}

// Shows where the request will go with the current choices.
function updateRouteInfo() {
    const info = document.getElementById('routeInfo');
    if (!info) return;
    const t = currentBedrockTarget();
    if (t.error) {
        info.textContent = t.error;
        return;
    }
    let text = 'Will call: ' + t.region + ' \u00b7 ' + t.modelId;
    if (t.note) text += '\n' + t.note;
    info.textContent = text;
}

function updateBedrockStatus() {
    const statusLine = document.getElementById('bedrockStatus');
    const hint = document.getElementById('apiKeyHint');
    const hasKey = bedrockState.apiKey.length > 0;
    const signedIn = typeof authState !== 'undefined' && !!authState.username;
    let text = 'API key: ' + (hasKey ? 'set' : 'not set');
    if (hasKey) text += signedIn ? ' (saved for ' + authState.username + ')' : ' (not saved)';
    if (typeof authState !== 'undefined' && authState.keyMessage) text += '. ' + authState.keyMessage;
    statusLine.textContent = text;
    if (hint) {
        hint.textContent = signedIn
            ? 'Saved encrypted on this computer for ' + authState.username + '.'
            : 'Not signed in: kept in memory only. Sign in to save it.';
    }
}

function getBedrockEndpoint() {
    const t = currentBedrockTarget();
    if (t.error) throw new Error(t.error);
    return `https://bedrock-runtime.${t.region}.amazonaws.com/model/${encodeURIComponent(t.modelId)}/converse`;
}

// Largest request body (the JSON text sent to the model), in bytes. One template is about 1 KB, so
// this allows a few hundred cards; a bigger graph is refused before anything is sent.
let MAX_REQUEST_BYTES = 300000;

// Output tokens reserved for the reply (inferenceConfig.maxTokens). The model writes only main.py
// (glue, about 1 KB), so 4096 is a generous reserve. It is a ceiling, not a forecast of real use.
const RESERVED_MAX_OUTPUT_TOKENS = 4096;

// Start and End cards are not generated as functions (the model writes their part in main.py).
function isGeneratedCard(node) {
    return node.role !== 'start' && node.role !== 'end';
}

// What the model needs to call one card (from templates.js, made by card_templates/templates_export.py):
// inputs, settings (names), required settings (no default) and outputs. Not the source code.
function cardSignature(title) {
    const t = CARD_TEMPLATES[title];
    if (!t) throw new Error('No template for card "' + title + '". Run python -m card_templates.templates_export.');
    return {
        inputs: t.inputs,
        settings: t.settings.map(s => s.name),
        required: t.settings.filter(s => s.required).map(s => s.name),
        outputs: t.outputs
    };
}

// Build cards.py in the app, not in the model. Each used card's source appears once (per distinct
// card title), with its own-module helpers, the stdlib imports it needs and one import line for the
// shared runtime names. Start and End cards are skipped. Throws on a helper or function name that is
// defined twice with different code. `nodes` is any list of objects with a `title` (and `role`).
function assembleCardsModule(nodes) {
    const titles = [];
    for (const n of nodes) {
        if (isGeneratedCard(n) && !titles.includes(n.title)) titles.push(n.title);
    }
    const imports = new Set();
    const runtime = new Set();
    const defs = new Map();   // name -> source, in first-use order
    const define = (name, source) => {
        if (defs.has(name) && defs.get(name) !== source) {
            throw new Error('Two different definitions named "' + name + '" in the card templates.');
        }
        defs.set(name, source);
    };
    for (const title of titles) {
        const t = CARD_TEMPLATES[title];
        if (!t) throw new Error('No template for card "' + title + '". Run python -m card_templates.templates_export.');
        (t.imports || []).forEach(i => imports.add(i));
        (t.runtime || []).forEach(r => runtime.add(r));
        (t.helpers || []).forEach(h => define(h.name, h.source));
        define(t.function, t.source);
    }
    const parts = ['# cards.py: written by the app from the card templates. Do not edit by hand.'];
    const head = Array.from(imports).sort();
    if (runtime.size) head.push('from card_templates.runtime import ' + Array.from(runtime).sort().join(', '));
    if (head.length) parts.push(head.join('\n'));
    for (const src of defs.values()) parts.push(src);
    return parts.join('\n\n\n') + '\n';
}

// The full graph (used by the app itself: compileMainPy and the confirm dialog). Per node: id, title,
// role, function, settings (template defaults, then the values set in the settings panel) and ports.
// Each distinct card is described once in `cards` (function name -> inputs, settings, required, outputs).
function serializeGraph() {
    const cards = {};
    const nodes = state.order.map(nodeID => {
        const node = state.nodes.get(nodeID);
        if (!node) return null;
        const t = CARD_TEMPLATES[node.title];
        if (!t) throw new Error('No template for card "' + node.title + '". Run python -m card_templates.templates_export.');
        const out = {
            id: node.id,
            title: node.title,
            role: node.role,
            settings: nodeSettings(node, t),
            inputs: node.ports.inputs.filter(p => !p.implicit).map(p => ({ id: p.id, class: p.cls, optional: p.optional, multi: p.multi })),
            outputs: node.ports.outputs.filter(p => !p.implicit).map(p => ({ id: p.id, class: p.cls }))
        };
        if (isGeneratedCard(node)) {
            out.function = t.function;
            if (!cards[t.function]) cards[t.function] = cardSignature(node.title);
        }
        return out;
    }).filter(n => n !== null);

    const edges = Array.from(state.edges.values()).map(edge => ({
        from: { node: edge.fromNodeID, port: edge.fromPort },
        to: { node: edge.toNodeID, port: edge.toPort }
    }));

    return { cards: cards, nodes: nodes, edges: edges, order: state.order.slice() };
}

// The smaller graph for the model. Dropped: ports (the `cards` map has them), settings equal to the
// function's own default (the function applies them), empty fields, and Start/End details. Links are
// 'node.port>node.port' text. `gaps` (from compileMainPy) tell the model what the app could not wire.
function slimGraph(full, gaps) {
    const cards = {};
    for (const fn of Object.keys(full.cards)) {
        const c = full.cards[fn];
        const e = { in: c.inputs, set: c.settings, out: c.outputs };
        if (c.required.length) e.req = c.required;
        for (const k of Object.keys(e)) if (Array.isArray(e[k]) && !e[k].length) delete e[k];
        cards[fn] = e;
    }
    const nodes = full.nodes.map(n => {
        const o = { id: n.id, title: n.title };
        if (n.role === 'start' || n.role === 'end') { o.role = n.role; return o; }
        o.fn = n.function;
        const t = CARD_TEMPLATES[n.title];
        const set = {};
        for (const s of t.settings) {
            const v = n.settings[s.name];
            if (v === undefined) continue;
            if (!s.required && JSON.stringify(v) === JSON.stringify(s.default)) continue;
            set[s.name] = v;
        }
        if (Object.keys(set).length) o.set = set;
        return o;
    });
    const edges = full.edges.map(e => e.from.node + '.' + e.from.port + '>' + e.to.node + '.' + e.to.port);
    const out = { cards: cards, nodes: nodes, edges: edges, order: full.order };
    if (gaps && gaps.length) out.gaps = gaps.map(g => ({ card: g.card, missing: g.missing }));
    return out;
}

// Assemble a Bedrock Converse API request. Returns the structure but does NOT
// execute any network call. The caller is responsible for fetch/XHR.
// Throws if the region or model choice is not valid. `gaps` are the compileMainPy gaps (optional).
function assembleBedrockRequest(gaps) {
    const graph = slimGraph(serializeGraph(), gaps);
    const text = JSON.stringify(graph);   // compact: no indentation
    const body = {
        system: [
            { text: SYSTEM_PROMPT }
        ],
        messages: [
            {
                role: 'user',
                content: [
                    { text: text }
                ]
            }
        ],
        inferenceConfig: {
            maxTokens: RESERVED_MAX_OUTPUT_TOKENS,
            temperature: 0
        }
    };
    // The cap counts the whole body (system prompt + graph + JSON overhead).
    const bytes = new TextEncoder().encode(JSON.stringify(body)).length;
    if (bytes > MAX_REQUEST_BYTES) {
        throw new Error('The project is too large to send: ' + bytes + ' bytes in the request, the limit is ' +
            MAX_REQUEST_BYTES + '. Remove some cards and try again.');
    }

    return {
        url: getBedrockEndpoint(),
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
            // Authorization header NOT included here; caller must add it
        },
        body: body
    };
}

// The files the app writes without the model: cards.py and the compiled main.py.
// Returns {ok, files, gaps}; files is empty when compileMainPy reports gaps.
function buildDeterministicFiles() {
    const full = serializeGraph();
    const r = compileMainPy(full);
    if (!r.ok) return { ok: false, files: [], gaps: r.gaps };
    return { ok: true, files: [{ path: 'cards.py', content: assembleCardsModule(full.nodes) }, { path: 'main.py', content: r.mainPy }], gaps: [] };
}
// Estimated input tokens of a request (system prompt + graph text). An estimate, not a count.
function estimateRequestTokens(request) {
    return estimateTokens(request.body.system[0].text) + estimateTokens(request.body.messages[0].content[0].text);
}

// After the model replied: the project files. cards.py is made by the app from the request's nodes;
// the model writes only main.py. A reply that holds cards.py is refused (a gap). Returns an array of
// {path, content} (empty when there are gaps); the array's `gaps` property holds the gaps.
// `reply` is the raw reply text.
function buildProjectFiles(request, reply) {
    const parsed = parseGenerationReply(reply);
    const gaps = parsed.gaps.slice();
    const files = [];
    for (const f of parsed.files) {
        if (f.path.replace(/\\/g, '/').toLowerCase() === 'cards.py') {
            gaps.push({ card: '(reply)', missing: 'Refused file "cards.py": the app writes it' });
        } else {
            files.push(f);
        }
    }
    if (!gaps.length && !files.some(f => f.path === 'main.py')) gaps.push({ card: '(reply)', missing: 'no main.py in reply' });
    let result = [];
    if (!gaps.length) {
        const graph = JSON.parse(request.body.messages[0].content[0].text);
        result = [{ path: 'cards.py', content: assembleCardsModule(graph.nodes) }].concat(files);
    }
    result.gaps = gaps;
    return result;
}

// Split the model's reply into files and gaps (format is defined in prompt.js).
//   === FILE: <relative path> ===  ...content...  === END FILE ===
//   === GAP: <card> | <what is missing> ===
// A refused file is not returned and a gap entry names it. Refused: empty, absolute, '~' start, ':' anywhere,
// control characters, '.', '..' or empty segments, segments ending in '.' or space, Windows device names
// (CON, PRN, AUX, NUL, COM1-9, LPT1-9, also with an extension), a repeated path, more than MAX_REPLY_FILES
// files, a file over MAX_FILE_BYTES. A malformed GAP line becomes a gap for "(reply)". A reply with
// nothing in it is one gap "(reply) | no files in reply". Text outside the blocks is ignored.
const MAX_REPLY_FILES = 20;
const MAX_FILE_BYTES = 200000;

function badReplyPath(p) {
    if (!p) return 'empty';
    if (/[\x00-\x1f\x7f]/.test(p)) return 'control character';
    if (/^[\\/~]/.test(p)) return 'absolute or ~ path';
    if (p.includes(':')) return "':' in path";
    for (const seg of p.split(/[\\/]/)) {
        if (seg === '' || seg === '.' || seg === '..') return "'.', '..' or empty segment";
        if (/[. ]$/.test(seg)) return 'segment ends with dot or space';
        if (/^(con|prn|aux|nul|com[1-9]|lpt[1-9])$/i.test(seg.split('.')[0].trimEnd())) return 'Windows device name';
    }
    return '';
}

function parseGenerationReply(text) {
    const files = [];
    const gaps = [];
    const seen = new Set();
    let current = null;
    for (const line of String(text).split(/\r?\n/)) {
        if (current) {
            if (/^=== END FILE ===\s*$/.test(line)) {
                const content = current.lines.join('\n');
                let why = current.why;
                if (!why && files.length >= MAX_REPLY_FILES) why = 'more than ' + MAX_REPLY_FILES + ' files';
                if (!why && new TextEncoder().encode(content).length > MAX_FILE_BYTES) why = 'file over ' + MAX_FILE_BYTES + ' bytes';
                if (why) gaps.push({ card: '(reply)', missing: 'Refused file ' + JSON.stringify(current.path) + ': ' + why });
                else files.push({ path: current.path, content: content });
                current = null;
            } else {
                current.lines.push(line);
            }
            continue;
        }
        let m = /^=== FILE: (.+?) ===\s*$/.exec(line);
        if (m) {
            const p = m[1].trim();
            let why = badReplyPath(p);
            if (!why) {
                const key = p.replace(/\\/g, '/').toLowerCase();
                if (seen.has(key)) why = 'repeated path';
                seen.add(key);
            }
            current = { path: p, lines: [], why: why };
            continue;
        }
        m = /^=== GAP: (.+?) \| (.+?) ===\s*$/.exec(line);
        if (m) { gaps.push({ card: m[1].trim(), missing: m[2].trim() }); continue; }
        if (/^=== GAP:/.test(line)) gaps.push({ card: '(reply)', missing: 'Malformed GAP line: ' + line.slice(0, 200) });
    }
    if (current) gaps.push({ card: '(reply)', missing: 'File block not closed: ' + current.path });
    if (!files.length && !gaps.length) gaps.push({ card: '(reply)', missing: 'no files in reply' });
    return { files: files, gaps: gaps };
}