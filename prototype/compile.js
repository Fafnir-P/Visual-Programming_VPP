// ============================================================================
// SETTINGS HELPERS AND THE MAIN.PY COMPILER (pure: no DOM, no network, no model)
// ============================================================================
// Loaded after templates.js. Used by app.js (settings panel, Generate) and bedrock.js (request).
//   settingKind / parseSettingValue / nodeSettings : card settings (text, number, yes/no, choice)
//   compileMainPy(graph) -> {ok, mainPy, gaps}     : the app writes main.py itself when it can
// `graph` is the full graph from serializeGraph() (bedrock.js): {cards, nodes, edges, order}.

// ---------------------------------------------------------------------------
// Settings
// ---------------------------------------------------------------------------

// What kind of field a setting is. From its template default: true/false -> 'bool', a number ->
// 'number', anything else -> 'text'. A setting that lists `choices` (array of text) -> 'choice'.
// shortcut: templates.js lists no choices today, so no setting is a 'choice' yet; add `choices` to the
// template export to turn on the select field.
function settingKind(def) {
    if (def && Array.isArray(def.choices) && def.choices.length) return 'choice';
    if (def && typeof def.default === 'boolean') return 'bool';
    if (def && typeof def.default === 'number') return 'number';
    return 'text';
}

const LIST_SETTING_NAME = /(labels|choices|options|fields|columns|keys)$/;

// Turn what the user typed (or a checkbox state) into the value stored in node.config.
// Returns {ok:true, value} or {ok:false, error}.
function parseSettingValue(def, raw) {
    const kind = settingKind(def);
    if (kind === 'bool') return { ok: true, value: raw === true || raw === 'true' };
    if (kind === 'choice') {
        return def.choices.includes(raw) ? { ok: true, value: raw } : { ok: false, error: 'Pick one of the listed choices.' };
    }
    const text = String(raw === undefined || raw === null ? '' : raw);
    if (kind === 'number') {
        if (text.trim() === '') return { ok: false, error: 'Enter a number.' };
        const n = Number(text);
        if (!isFinite(n)) return { ok: false, error: '"' + text.trim().slice(0, 30) + '" is not a number.' };
        return { ok: true, value: n };
    }
    if (def && def.default === null) {      // optional, no default: empty means "not set"
        const t = text.trim();
        if (t === '') return { ok: true, value: null };
        if (/^[\[{]|^(-?\d+(\.\d+)?|true|false|null)$/.test(t)) {
            try { return { ok: true, value: JSON.parse(t) }; } catch (e) {
                return { ok: false, error: 'Not valid list/JSON text. Example: ["a","b"]' };
            }
        }
        if (LIST_SETTING_NAME.test(def.name)) return { ok: true, value: t.split(',').map((s) => s.trim()).filter((s) => s) };
        return { ok: true, value: text };
    }
    return { ok: true, value: text };
}

// How a stored value is shown in its field.
function settingDisplay(def, value) {
    if (value === null || value === undefined) return '';
    if (typeof value === 'object') return JSON.stringify(value);
    return String(value);
}

// Effective settings of a node: template defaults (settings without a default are left out), then the
// values the user set in the settings panel (node.config).
function nodeSettings(node, template) {
    const t = template || CARD_TEMPLATES[node.title];
    const out = {};
    if (!t) return out;
    for (const s of t.settings) {
        if (s.required) {
            if (node.config && Object.prototype.hasOwnProperty.call(node.config, s.name)) out[s.name] = node.config[s.name];
        } else {
            out[s.name] = (node.config && Object.prototype.hasOwnProperty.call(node.config, s.name)) ? node.config[s.name] : s.default;
        }
    }
    return out;
}

// ---------------------------------------------------------------------------
// Python text
// ---------------------------------------------------------------------------

function pyStr(s) {
    let out = "'";
    for (const ch of String(s)) {
        const c = ch.codePointAt(0);
        if (ch === '\\') out += '\\\\';
        else if (ch === "'") out += "\\'";
        else if (ch === '\n') out += '\\n';
        else if (ch === '\r') out += '\\r';
        else if (ch === '\t') out += '\\t';
        else if (c < 32 || c === 127) out += '\\x' + c.toString(16).padStart(2, '0');
        else if (c < 127) out += ch;
        else if (c <= 0xffff) out += '\\u' + c.toString(16).padStart(4, '0');
        else out += '\\U' + c.toString(16).padStart(8, '0');
    }
    return out + "'";
}

function pyLiteral(v) {
    if (v === null || v === undefined) return 'None';
    if (v === true) return 'True';
    if (v === false) return 'False';
    if (typeof v === 'number') return String(v);
    if (typeof v === 'string') return pyStr(v);
    if (Array.isArray(v)) return '[' + v.map(pyLiteral).join(', ') + ']';
    return '{' + Object.keys(v).map((k) => pyStr(k) + ': ' + pyLiteral(v[k])).join(', ') + '}';
}

// ---------------------------------------------------------------------------
// compileMainPy
// ---------------------------------------------------------------------------

// Cards whose value comes from the command line when their `value` input has no link.
// 'text' flags take a string (the card checks it); 'flag' cards are yes/no switches.
const CLI_CARDS = {
    'Enter Text': 'text', 'Enter Paragraph': 'text', 'Enter Number': 'text', 'Enter Email Address': 'text',
    'Enter Phone Number': 'text', 'Enter Currency Amount': 'text', 'Pick Date': 'text', 'Pick Time': 'text',
    'Choose From Dropdown': 'text', 'Choose One Option': 'text', 'Adjust Slider': 'text', 'Rate With Stars': 'text',
    'Toggle Checkbox': 'flag', 'Switch Toggle': 'flag'
};
// Number cards: the flag value is checked on the command line so the message can name the flag.
const NUMBER_CARDS = new Set(['Enter Number', 'Adjust Slider', 'Rate With Stars', 'Enter Currency Amount']);
const NOT_PRINTED = new Set(['view', 'control']);
const RISKY_SOURCE = /ctx\.(?!now\b)|\bopen\(|urllib|socket|sqlite3|subprocess|requests|http\.client/;

function pyId(id) { return String(id).replace(/[^A-Za-z0-9_]/g, '_'); }

function compileMainPy(graph) {
    const gaps = [];
    const gap = (card, missing, nodeIDs) => gaps.push({ card: card, missing: missing, nodeIDs: nodeIDs || [] });
    const nodes = new Map((graph.nodes || []).map((n) => [n.id, n]));
    const label = (n) => n.title + ' (' + n.id + ')';
    const run = (graph.order || []).map((id) => nodes.get(id)).filter((n) => n && n.role !== 'start' && n.role !== 'end');
    const pos = new Map(run.map((n, i) => [n.id, i]));
    if (!run.length) gap('(graph)', 'no cards to run');

    // Edges: data links only. Links to or from implicit (Start/Done) ports only set the order.
    const incoming = new Map();   // nodeID -> portID -> [edge]
    const outgoing = new Map();   // nodeID -> count of data links
    const needed = new Set();     // nodeIDs whose value feeds a required input
    const portOf = (n, side, id) => ((side === 'in' ? n.inputs : n.outputs) || []).find((p) => p.id === id);
    for (const e of graph.edges || []) {
        const a = nodes.get(e.from.node);
        const b = nodes.get(e.to.node);
        if (!a || !b) { gap('(edge)', 'a link points at a card that is not in the graph'); continue; }
        if (b.role === 'end') continue;
        if (a.role === 'start') {
            if (!/^_/.test(e.to.port)) gap(label(b), 'input "' + e.to.port + '" is linked to the Start card; the app cannot wire that', [b.id]);
            continue;
        }
        if (/^_/.test(e.from.port) || /^_/.test(e.to.port)) continue;
        const po = portOf(a, 'out', e.from.port);
        const pi = portOf(b, 'in', e.to.port);
        if (!po || !pi) { gap(label(b), 'link ' + a.id + '.' + e.from.port + ' > ' + b.id + '.' + e.to.port + ' uses an unknown port', [a.id, b.id]); continue; }
        if (!pos.has(a.id) || pos.get(a.id) >= pos.get(b.id)) {
            gap(label(b), 'runs before or without its source ' + label(a), [a.id, b.id]);
            continue;
        }
        if (!incoming.has(b.id)) incoming.set(b.id, new Map());
        const byPort = incoming.get(b.id);
        if (!byPort.has(e.to.port)) byPort.set(e.to.port, []);
        byPort.get(e.to.port).push(e);
        outgoing.set(a.id, (outgoing.get(a.id) || 0) + 1);
        if (pi.optional === false) needed.add(a.id);
    }

    // Per card checks and call lines.
    const flags = new Map();    // flag name -> card label
    const argLines = [];
    let usesNum = false;
    const calls = [];
    const functions = [];
    for (const n of run) {
        const t = CARD_TEMPLATES[n.title];
        if (!t) { gap(label(n), 'no template for this card', [n.id]); continue; }
        const src = t.source + (t.helpers || []).map((h) => h.source).join('\n');
        if (RISKY_SOURCE.test(src)) { gap(label(n), 'this card needs a table, store or outside service; the model must wire it', [n.id]); continue; }
        const ports = (n.inputs || []).concat(n.outputs || []);
        if (ports.some((p) => p.class === 'control')) { gap(label(n), 'route, loop or flow card; the model must wire it', [n.id]); continue; }
        const byPort = incoming.get(n.id) || new Map();
        const args = [];
        let bad = false;
        for (const [port, list] of byPort) {
            if (list.length > 1) { gap(label(n), 'input "' + port + '" has ' + list.length + ' links', [n.id]); bad = true; }
        }
        const settings = n.settings || {};
        const missingReq = (t.settings || []).filter((s) => s.required && settings[s.name] === undefined).map((s) => s.name);
        if (missingReq.length) { gap(label(n), 'required setting ' + missingReq.join(', ') + ' has no value (set it in the settings panel)', [n.id]); bad = true; }
        const cli = CLI_CARDS[n.title];
        const v = 'n_' + pyId(n.id);
        for (const port of t.inputs) {
            const links = byPort.get(port);
            if (links && links.length === 1) {
                args.push(port + '=n_' + pyId(links[0].from.node) + '[' + pyStr(links[0].from.port) + ']');
            } else if (!links) {
                const p = portOf(n, 'in', port);
                if (port === 'value' && cli) {
                    const flag = settings.name;
                    if (typeof flag !== 'string' || !/^[A-Za-z][A-Za-z0-9_-]*$/.test(flag) || flag === 'help') {
                        gap(label(n), 'its name setting "' + flag + '" cannot be a command line flag (letters, digits, - and _; not "help")', [n.id]);
                        bad = true;
                    } else if (flags.has(flag)) {
                        gap(label(n), 'the name "' + flag + '" is already used by ' + flags.get(flag) + '; give each card its own name', [n.id]);
                        bad = true;
                    } else {
                        flags.set(flag, label(n));
                        const dest = 'f_' + pyId(n.id);
                        // A flag is required when the card says so or its value feeds a required input.
                        const req = cli === 'text' && (settings.required === true || needed.has(n.id));
                        if (NUMBER_CARDS.has(n.title)) usesNum = true;
                        argLines.push("    ap.add_argument('--" + flag + "', dest='" + dest + "', " +
                            (cli === 'flag' ? "action='store_true'" : 'default=None') +
                            (NUMBER_CARDS.has(n.title) ? ", type=num_flag('" + flag + "')" : '') + (req ? ', required=True' : '') + ')');
                        args.push('value=args.' + dest);
                    }
                } else if (p && p.optional === false) {
                    gap(label(n), 'required input "' + port + '" has no link', [n.id]);
                    bad = true;
                }
            }
        }
        if (cli === undefined && !byPort.has('value') && t.inputs.includes('value') && t.outputs.includes('value') &&
            (t.settings || []).some((s) => s.name === 'name') && (t.settings || []).some((s) => s.name === 'label')) {
            gap(label(n), 'an input card of this kind is not supported by the app; the model must wire it', [n.id]);
            bad = true;
        }
        for (const s of t.settings || []) {
            const val = settings[s.name];
            if (val !== undefined && val !== null) args.push(s.name + '=' + pyLiteral(val));
        }
        if (bad) continue;
        if (!functions.includes(t.function)) functions.push(t.function);
        calls.push({ node: n, line: v + ' = ' + t.function + '(' + ['ctx'].concat(args).join(', ') + ')', template: t });
    }

    // Result: the terminal data cards (no outgoing data link).
    const terminals = calls.filter((c) => !outgoing.get(c.node.id));
    const titles = terminals.map((c) => c.node.title);
    if (terminals.length > 1 && new Set(titles).size !== titles.length) {
        gap('(result)', 'two result cards share a title (' + titles.join(', ') + '); cannot key the output', terminals.map((c) => c.node.id));
    }
    const printable = (c) => (c.node.outputs || []).filter((p) => !/^_/.test(p.id) && !NOT_PRINTED.has(p.class));
    const resultOf = (c) => {
        const v = 'n_' + pyId(c.node.id);
        if (c.node.title === 'Build Summary Record') return v + "['record']";
        const outs = printable(c);
        if (outs.some((p) => p.class === 'any')) { gap(label(c.node), 'its result has no clear type; the model must choose what to print', [c.node.id]); return null; }
        if (!outs.length) { gap(label(c.node), 'it has nothing to print', [c.node.id]); return null; }
        return '{' + outs.map((p) => pyStr(p.id) + ': ' + v + '[' + pyStr(p.id) + ']').join(', ') + '}';
    };
    let resultExpr = null;
    if (terminals.length === 1) resultExpr = resultOf(terminals[0]);
    else if (terminals.length > 1) {
        const parts = terminals.map((c) => ({ c: c, e: resultOf(c) }));
        if (parts.every((p) => p.e !== null)) resultExpr = '{' + parts.map((p) => pyStr(p.c.node.title) + ': ' + p.e).join(', ') + '}';
    } else if (run.length && !gaps.length) gap('(result)', 'no card produces a result');

    if (gaps.length) return { ok: false, mainPy: '', gaps: gaps };

    const L = [];
    L.push('import os, sys');
    L.push('d = os.path.dirname(os.path.abspath(__file__))');
    L.push("while not os.path.isdir(os.path.join(d, 'card_templates')) and os.path.dirname(d) != d: d = os.path.dirname(d)");
    L.push('sys.path.insert(0, d)');
    L.push('import argparse');
    L.push('import json');
    L.push('');
    L.push('from card_templates.runtime import Context, Store, CardError' + (usesNum ? ', to_number' : ''));
    L.push('from cards import ' + functions.join(', '));
    L.push('');
    L.push('');
    L.push('def die(message):');
    L.push('    print(message, file=sys.stderr)');
    L.push('    sys.exit(1)');
    L.push('');
    if (usesNum) {
        L.push('');
        L.push('def num_flag(flag):');
        L.push('    def check(text):');
        L.push('        try:');
        L.push('            to_number(text)');
        L.push('        except CardError:');
        L.push("            die('--' + flag + ' must be a number')");
        L.push('        return text');
        L.push('    return check');
        L.push('');
    }
    L.push('');
    L.push('def main():');
    L.push('    ap = argparse.ArgumentParser()');
    L.push('    ap.error = die');
    argLines.forEach((l) => L.push(l));
    L.push('    args = ap.parse_args()');
    L.push('    ctx = Context(store=Store())');
    L.push('    try:');
    calls.forEach((c) => L.push('        ' + c.line));
    L.push('        result = ' + resultExpr);
    L.push('    except (CardError, ValueError, ArithmeticError) as e:');
    L.push("        print((str(e).splitlines() or [type(e).__name__])[0], file=sys.stderr)");
    L.push('        sys.exit(1)');
    L.push('    print(json.dumps(result, default=str))');
    L.push('');
    L.push('');
    L.push("if __name__ == '__main__':");
    L.push('    main()');
    return { ok: true, mainPy: L.join('\n') + '\n', gaps: [] };
}
