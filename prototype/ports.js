// ============================================================================
// PORT RULES: what may be linked to what
// ============================================================================
// Pure logic, no page access, so it can be tested on its own.
// The port classes (PORT_CLASSES), what each class links to (PORT_COMPAT) and the
// ports of every card come from catalog.js, which loads first.
//
// A card's ports live on the node:  node.ports.inputs / node.ports.outputs, each
//   { id, name, cls, optional, multi, implicit }
// An edge is { id, fromNodeID, fromPort, toNodeID, toPort }.
//
// Refusal codes, in the order they are checked (see "Connection rules" in Cards.md):
//   no_such_port  direction  same_card  type_mismatch  duplicate  input_taken  cycle

const LINK_ERROR_CODES = ['no_such_port', 'direction', 'same_card', 'type_mismatch', 'duplicate', 'input_taken', 'cycle'];

function classInfo(cls) {
    return PORT_CLASSES[cls] || { label: String(cls), color: '#6c757d', emoji: '' };
}

// Can an output of class outCls feed an input of class inCls?
// Same class always works; the wildcard class (any) works with every class.
function classesCompatible(outCls, inCls) {
    const allowed = PORT_COMPAT[outCls];
    return Array.isArray(allowed) && allowed.indexOf(inCls) !== -1;
}

function findPort(node, side, portID) {
    if (!node || !node.ports) return null;
    const list = side === 'input' ? node.ports.inputs : node.ports.outputs;
    return list.find(p => p.id === portID) || null;
}

function describeEnd(node, port) {
    const info = classInfo(port.cls);
    return {
        nodeID: node.id,
        card: node.title,
        portID: port.id,
        portName: port.name,
        cls: port.cls,
        clsLabel: info.label,
        color: info.color
    };
}

function endText(end) {
    return `\u201c${end.portName}\u201d of ${end.card} (${end.clsLabel})`;
}

// Is there a path of links from startNodeID to targetNodeID?
function hasPath(edges, startNodeID, targetNodeID) {
    const next = new Map();
    edges.forEach(e => {
        if (!next.has(e.fromNodeID)) next.set(e.fromNodeID, []);
        next.get(e.fromNodeID).push(e.toNodeID);
    });
    const seen = new Set();
    const stack = [startNodeID];
    while (stack.length) {
        const id = stack.pop();
        if (id === targetNodeID) return true;
        if (seen.has(id)) continue;
        seen.add(id);
        (next.get(id) || []).forEach(n => stack.push(n));
    }
    return false;
}

// Decide whether `from` (an output) may be linked to `to` (an input).
//   nodes: Map nodeID -> node      edges: Map edgeID -> edge
//   from, to: { nodeID, portID, side? }   side is 'input' or 'output'; give it when the end can be either
// Returns { ok: true, loose } when allowed (loose = one side is the Any wildcard),
// or { ok: false, code, message, details } when refused. `message` is written for the user.
function checkConnection(nodes, edges, from, to) {
    const fromNode = nodes.get(from.nodeID);
    const toNode = nodes.get(to.nodeID);
    const fail = (code, message, details) => ({ ok: false, code: code, message: message, details: details || {} });

    if (!fromNode || !toNode) {
        return fail('no_such_port', 'One of the cards no longer exists.', { from: from, to: to });
    }

    // Each end must be the right kind of port: an output on the "from" side, an input on the "to" side.
    // A port id can exist on both sides of one card (an input and an output both called "value"),
    // so the caller says which side it means with `side`. Without `side`, "from" means an output and
    // "to" means an input, and the other side is tried only to explain a wrong direction.
    const resolve = (node, end, wanted) => {
        const claimed = end.side || wanted;
        const port = findPort(node, claimed, end.portID);
        if (port) return { port: port, side: claimed };
        if (end.side) return null;
        const other = findPort(node, wanted === 'output' ? 'input' : 'output', end.portID);
        return other ? { port: other, side: wanted === 'output' ? 'input' : 'output' } : null;
    };
    const fromEnd = resolve(fromNode, from, 'output');
    const toEnd = resolve(toNode, to, 'input');
    if (!fromEnd || !toEnd) {
        return fail('no_such_port', 'That port does not exist on the card.', { from: from, to: to });
    }
    if (fromEnd.side !== 'output' || toEnd.side !== 'input') {
        const wa = describeEnd(fromNode, fromEnd.port);
        const wb = describeEnd(toNode, toEnd.port);
        const wrong = [];
        if (fromEnd.side !== 'output') wrong.push(`${endText(wa)} is an input`);
        if (toEnd.side !== 'input') wrong.push(`${endText(wb)} is an output`);
        return fail('direction', `A link must go from an output to an input, but ${wrong.join(' and ')}.`, { from: wa, to: wb });
    }
    const outPort = fromEnd.port;
    const inPort = toEnd.port;
    const a = describeEnd(fromNode, outPort);
    const b = describeEnd(toNode, inPort);
    const details = { from: a, to: b };

    if (from.nodeID === to.nodeID) {
        return fail('same_card', `A card cannot be linked to itself (${fromNode.title}).`, details);
    }

    if (!classesCompatible(outPort.cls, inPort.cls)) {
        const needs = classInfo(inPort.cls);
        const gives = classInfo(outPort.cls);
        return fail('type_mismatch',
            `These ports do not match. ${endText(a)} is ${gives.label} (${gives.colourName || 'colour'}); ` +
            `${endText(b)} needs ${needs.label} (${needs.colourName || 'colour'}). Only ports of the same colour can be linked.`,
            details);
    }

    const sameLink = Array.from(edges.values()).some(e =>
        e.fromNodeID === from.nodeID && e.fromPort === from.portID && e.toNodeID === to.nodeID && e.toPort === to.portID);
    if (sameLink) {
        return fail('duplicate', `${endText(a)} is already linked to ${endText(b)}.`, details);
    }

    if (!inPort.multi) {
        const taken = Array.from(edges.values()).find(e => e.toNodeID === to.nodeID && e.toPort === to.portID);
        if (taken) {
            const other = nodes.get(taken.fromNodeID);
            const otherPort = other ? findPort(other, 'output', taken.fromPort) : null;
            const by = other && otherPort ? ` by ${endText(describeEnd(other, otherPort))}` : '';
            return fail('input_taken',
                `${endText(b)} already has a link${by}. An input takes one link: remove the old link first.`,
                Object.assign({ existingEdgeID: taken.id }, details));
        }
    }

    // A link from "from" to "to" makes a loop if "to" already leads back to "from"
    if (hasPath(edges, to.nodeID, from.nodeID)) {
        return fail('cycle',
            `This link would make a loop: ${toNode.title} already leads to ${fromNode.title}. ` +
            'Cards may not feed themselves, even through other cards.', details);
    }

    return { ok: true, loose: outPort.cls === 'any' || inPort.cls === 'any', details: details };
}

// For highlighting while a link is dragged: could this input take a link from an
// output of class outCls, looking only at the classes (not at links already made)?
function portCanLink(startSide, startCls, otherSide, otherCls) {
    if (startSide === otherSide) return false;
    return startSide === 'output' ? classesCompatible(startCls, otherCls) : classesCompatible(otherCls, startCls);
}

// Inputs that need a link (or a value in the settings) and have none yet.
function findOpenInputs(nodes, edges) {
    const linked = new Set();
    edges.forEach(e => linked.add(e.toNodeID + '|' + e.toPort));
    const open = [];
    nodes.forEach(node => {
        node.ports.inputs.forEach(port => {
            if (port.implicit || port.optional) return;
            if (!linked.has(node.id + '|' + port.id)) {
                open.push({ nodeID: node.id, card: node.title, portID: port.id, portName: port.name, cls: port.cls });
            }
        });
    });
    return open;
}

// Re-check every link on the canvas (useful after loading a saved project). Returns refusals.
function recheckAllLinks(nodes, edges) {
    const accepted = new Map();
    const problems = [];
    edges.forEach(edge => {
        const result = checkConnection(nodes, accepted,
            { nodeID: edge.fromNodeID, portID: edge.fromPort }, { nodeID: edge.toNodeID, portID: edge.toPort });
        if (result.ok) accepted.set(edge.id, edge);
        else problems.push(Object.assign({ edgeID: edge.id }, result));
    });
    return problems;
}

// Everything that is missing before the app is generated, each with WHERE (which card, and its
// place in the run order) and WHAT (the missing thing). None of it blocks generating: the user is asked
// to confirm. `order` is the run order (a list of node ids); without it only the card name is shown.
//   kinds: no_start  start_unlinked  no_end  open_input
function findGenerationIssues(nodes, edges, order) {
    const issues = [];
    const list = Array.from(nodes.values());
    const place = (node) => {
        const step = order ? order.indexOf(node.id) + 1 : 0;
        return step > 0 ? `${node.title} (card ${step} in the run order)` : node.title;
    };

    const starts = list.filter(n => n.role === 'start');
    if (starts.length === 0) {
        issues.push({ kind: 'no_start', where: 'The canvas', message: 'There is no Start card, so nothing says where the app begins.' });
    }
    starts.forEach(node => {
        const leadsAnywhere = Array.from(edges.values()).some(e => e.fromNodeID === node.id);
        if (!leadsAnywhere) {
            issues.push({
                kind: 'start_unlinked', nodeID: node.id, where: place(node),
                message: 'Nothing is linked to the Start card, so nothing would run. Link its event output to the first card.'
            });
        }
    });

    if (!list.some(n => n.role === 'end')) {
        issues.push({ kind: 'no_end', where: 'The canvas', message: 'There is no End card to mark where the app finishes.' });
    }

    findOpenInputs(nodes, edges).forEach(open => {
        const node = nodes.get(open.nodeID);
        issues.push({
            kind: 'open_input', nodeID: open.nodeID, portID: open.portID, where: place(node),
            message: `The input \u201c${open.portName}\u201d (${classInfo(open.cls).label}) has no link. Link it, or give it a value in the card\u2019s settings.`
        });
    });
    return issues;
}
