// ============================================================================
// DATA MODEL
// ============================================================================

const state = {
    nodes: new Map(),
    edges: new Map(),
    selectedNodeID: null,
    selectedEdgeID: null,
    nextNodeID: 1,
    nextEdgeID: 1,
    edgeDraft: null,  // { startNodeID, startPortID, startPortType, startCls, x, y, snapTarget: null|{nodeID, portID, portType}, check: null|result of checkConnection }
    order: [],        // node IDs in run order (explicit user order)
    messages: [],     // refused links and other notices: { time, level, code, message, details }
    buildConfirmed: false,  // true after user confirms build is complete
    ui: {
        sidebarOpen: true,
        tab: 'catalog',       // 'catalog' | 'order' | 'model'
        messagesOpen: false,
        category: 'all',      // category id or 'all'
        search: ''
    }
};

const SNAP_RADIUS = 40;
const MAX_MESSAGES = 50;
const PORT_ROW_H = 24;     // height of one port row in a card body (px)
const PORT_BODY_PAD = 8;   // space above and below the port rows (px)

// ============================================================================
// INITIALIZATION
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    initializeSidebar();
    initBedrockUI();
    initAuthUI();
    initializePortUI();
    initializeIssuesDialog();
    addStartCard();
    render();
});

function initializeEventListeners() {
    // Canvas background click (deselect)
    const canvas = document.getElementById('canvas');
    canvas.addEventListener('mousedown', handleCanvasMouseDown);

    // Accept cards dragged in from the sidebar catalog
    canvas.addEventListener('dragover', handleCanvasDragOver);
    canvas.addEventListener('drop', handleCanvasDrop);

    // Keyboard events
    document.addEventListener('keydown', handleKeyDown);

    // Mouse move for drag and edge draft
    document.addEventListener('mousemove', handleDocumentMouseMove);
    document.addEventListener('mouseup', handleDocumentMouseUp);

    // Generate button
    document.getElementById('generateBtn').addEventListener('click', handleGenerateClick);

    // Confirmation dialog
    document.getElementById('confirmCancelBtn').addEventListener('click', handleCancelDialog);
    document.getElementById('confirmGenerateBtn').addEventListener('click', handleConfirmGenerate);
}

// ============================================================================
// CARD MANAGEMENT
// ============================================================================

// Place a copy of a catalog card on the canvas. The node keeps a reference to
// its catalog card (catalogID) and is appended to the end of the run order.
// If x/y are not given, cards are staggered so they do not stack exactly.
function addCardFromCatalog(catalogID, x, y) {
    const source = getCatalogCard(catalogID);
    if (!source) return null;

    // There is exactly one Start card (it is on the canvas when the program opens)
    if (source.role === 'start') {
        const existing = findStartNode();
        if (existing) {
            selectNode(existing.id);
            reportNotice('one_start', 'There is already a Start card. An app has only one place where it begins.');
            return null;
        }
    }

    const id = `node_${state.nextNodeID++}`;
    // New cards go to the right of the Start card, each a little lower than the last
    const offset = (state.nodes.size * 30) % 240;

    const node = {
        id: id,
        catalogID: source.id,
        type: source.category,
        title: source.title,
        x: Math.max(0, x !== undefined ? x : 340 + offset),
        y: Math.max(0, y !== undefined ? y : 40 + offset),
        role: source.role,
        // Every node gets its own copy of the card's ports (from catalog.js)
        ports: {
            inputs: source.ports.inputs.map(p => Object.assign({}, p)),
            outputs: source.ports.outputs.map(p => Object.assign({}, p))
        }
    };

    state.nodes.set(id, node);
    state.order.push(id);
    render();
    return node;
}

function findStartNode() {
    return Array.from(state.nodes.values()).find(n => n.role === 'start') || null;
}

// The Start card is on the canvas when the program opens and stays there.
function addStartCard() {
    if (findStartNode()) return findStartNode();
    const source = CATALOG.find(c => c.role === 'start');
    return source ? addCardFromCatalog(source.id, 40, 40) : null;
}

function deleteNode(nodeID) {
    const target = state.nodes.get(nodeID);
    if (target && target.role === 'start') {
        reportNotice('start_required', 'The Start card cannot be deleted: every app begins there.');
        return;
    }

    // Delete all edges connected to this node
    const edgesToDelete = [];
    state.edges.forEach((edge, edgeID) => {
        if (edge.fromNodeID === nodeID || edge.toNodeID === nodeID) {
            edgesToDelete.push(edgeID);
        }
    });

    edgesToDelete.forEach(edgeID => state.edges.delete(edgeID));
    state.nodes.delete(nodeID);
    state.order = state.order.filter(id => id !== nodeID);

    if (state.selectedNodeID === nodeID) {
        state.selectedNodeID = null;
    }

    render();
}

// ============================================================================
// EDGE MANAGEMENT
// ============================================================================

// Convert a mouse event into canvas coordinates (same space getPortCenter
// returns), so draft lines and drag math line up with the rendered ports
// regardless of toolbar height or scroll position.
function mouseToCanvas(event) {
    const canvas = document.getElementById('canvas');
    const rect = canvas.getBoundingClientRect();
    return {
        x: event.clientX - rect.left,
        y: event.clientY - rect.top
    };
}

function beginDraft(nodeID, portID, portType, event) {
    const pt = mouseToCanvas(event);
    const node = state.nodes.get(nodeID);
    const startPort = findPort(node, portType, portID);
    state.edgeDraft = {
        startNodeID: nodeID,
        startPortID: portID,
        startPortType: portType,
        startCls: startPort ? startPort.cls : null,
        x: pt.x,
        y: pt.y,
        snapTarget: null,
        check: null
    };
    render();
}

// The two ends of a link being drawn, in the order checkConnection wants them:
// the end that should be an output first, then the end that should be an input.
function draftEnds(draft, target) {
    // `side` says which side of its card each port is on: the same name may exist on both
    const start = { nodeID: draft.startNodeID, portID: draft.startPortID, side: draft.startPortType };
    const other = { nodeID: target.nodeID, portID: target.portID, side: target.portType };
    return draft.startPortType === 'output' ? { from: start, to: other } : { from: other, to: start };
}

function updateEdgeDraft(event) {
    if (!state.edgeDraft) return;

    const pt = mouseToCanvas(event);
    state.edgeDraft.x = pt.x;
    state.edgeDraft.y = pt.y;

    // Nearest port of another card within the snap radius. Ports of every kind count,
    // so a wrong pick (an output on an output, a mismatched colour) is reported, not ignored.
    let closestPort = null;
    let closestDistance = SNAP_RADIUS;

    state.nodes.forEach(node => {
        if (node.id === state.edgeDraft.startNodeID) return; // Skip same node

        [['input', node.ports.inputs], ['output', node.ports.outputs]].forEach(([side, ports]) => {
            ports.forEach(port => {
                const center = getPortCenter(node.id, side, port.id);
                if (!center) return;

                const dx = pt.x - center.x;
                const dy = pt.y - center.y;
                const dist = Math.sqrt(dx * dx + dy * dy);

                if (dist < closestDistance) {
                    closestDistance = dist;
                    closestPort = { nodeID: node.id, portID: port.id, portType: side };
                }
            });
        });
    });

    // Clear previous snap-target styling
    document.querySelectorAll('.port.snap-target, .port.snap-bad').forEach(el => {
        el.classList.remove('snap-target', 'snap-bad');
    });

    // Update snap target and check it now, so the line can show a mismatch before release
    state.edgeDraft.snapTarget = closestPort;
    state.edgeDraft.check = null;
    if (closestPort) {
        const ends = draftEnds(state.edgeDraft, closestPort);
        state.edgeDraft.check = checkConnection(state.nodes, state.edges, ends.from, ends.to);
        const cardEl = document.querySelector(`[data-node-id="${closestPort.nodeID}"]`);
        if (cardEl) {
            const portEl = cardEl.querySelector(
                `.port.${closestPort.portType}-port[data-port-id="${closestPort.portID}"]`
            );
            if (portEl) {
                portEl.classList.add(state.edgeDraft.check.ok ? 'snap-target' : 'snap-bad');
            }
        }
    }

    renderEdgeDraft();
}

function commitEdge() {
    if (!state.edgeDraft || !state.edgeDraft.snapTarget) {
        cancelEdgeDraft();
        return;
    }

    const draft = state.edgeDraft;
    const ends = draftEnds(draft, draft.snapTarget);

    // One place decides whether the link is allowed (ports.js)
    const result = checkConnection(state.nodes, state.edges, ends.from, ends.to);
    if (!result.ok) {
        const target = draft.snapTarget;
        cancelEdgeDraft();
        reportConnectionError(result, target);
        return;
    }

    const edgeID = `edge_${state.nextEdgeID++}`;
    state.edges.set(edgeID, {
        id: edgeID,
        fromNodeID: ends.from.nodeID,
        fromPort: ends.from.portID,
        toNodeID: ends.to.nodeID,
        toPort: ends.to.portID,
        loose: !!result.loose
    });

    cancelEdgeDraft();
    render();
}
function cancelEdgeDraft() {
    // Clear snap styling (green for a match, red for a refusal)
    document.querySelectorAll('.port.snap-target, .port.snap-bad').forEach(el => {
        el.classList.remove('snap-target', 'snap-bad');
    });
    state.edgeDraft = null;
    render();
}

function deleteEdge(edgeID) {
    state.edges.delete(edgeID);
    if (state.selectedEdgeID === edgeID) {
        state.selectedEdgeID = null;
    }
    render();
}

// ============================================================================
// SELECTION
// ============================================================================

function selectNode(nodeID) {
    state.selectedNodeID = nodeID;
    state.selectedEdgeID = null;
    render();
}

function selectEdge(edgeID) {
    state.selectedEdgeID = edgeID;
    state.selectedNodeID = null;
    render();
}

function deselectAll() {
    state.selectedNodeID = null;
    state.selectedEdgeID = null;
    cancelEdgeDraft();
    render();
}

// ============================================================================
// DRAG STATE
// ============================================================================

let dragState = null;  // { nodeID, startX, startY, nodeStartX, nodeStartY, hasMoved }

function startDrag(nodeID, event) {
    const node = state.nodes.get(nodeID);
    if (!node) return;

    const start = mouseToCanvas(event);
    dragState = {
        nodeID: nodeID,
        startX: start.x,
        startY: start.y,
        nodeStartX: node.x,
        nodeStartY: node.y,
        hasMoved: false
    };
}

function updateDrag(event) {
    if (!dragState) return;

    const current = mouseToCanvas(event);
    const dx = current.x - dragState.startX;
    const dy = current.y - dragState.startY;

    // Movement threshold to distinguish click from drag
    if (Math.abs(dx) > 3 || Math.abs(dy) > 3) {
        dragState.hasMoved = true;
    }

    if (dragState.hasMoved) {
        const node = state.nodes.get(dragState.nodeID);
        if (node) {
            node.x = dragState.nodeStartX + dx;
            node.y = dragState.nodeStartY + dy;

            // Update card position (in-memory + DOM only, no I/O)
            const cardEl = document.querySelector(`[data-node-id="${node.id}"]`);
            if (cardEl) {
                cardEl.style.left = `${node.x}px`;
                cardEl.style.top = `${node.y}px`;
            }

            // Update connected edges live
            renderEdges();
        }
    }
}

function endDrag() {
    if (dragState && !dragState.hasMoved) {
        // It was a click, not a drag - handle selection
        selectNode(dragState.nodeID);
    }
    dragState = null;
}

// ============================================================================
// EVENT HANDLERS
// ============================================================================

function handleCanvasMouseDown(event) {
    if (event.target.id === 'canvas') {
        deselectAll();
    }
}

function handleCardMouseDown(nodeID, event) {
    // Check if clicking on a port
    if (event.target.classList.contains('port')) {
        return;  // Port mousedown handlers will handle this
    }

    event.stopPropagation();
    startDrag(nodeID, event);
}

function handlePortMouseDown(nodeID, portID, portType, event) {
    event.stopPropagation();
    beginDraft(nodeID, portID, portType, event);
}

function handleEdgeClick(edgeID, event) {
    event.stopPropagation();
    selectEdge(edgeID);
}

function handleDocumentMouseMove(event) {
    if (dragState) {
        updateDrag(event);
    } else if (state.edgeDraft) {
        updateEdgeDraft(event);
    }
}

function handleDocumentMouseUp(event) {
    if (dragState) {
        endDrag();
    } else if (state.edgeDraft) {
        commitEdge();
    }
}

function handleKeyDown(event) {
    if (event.key === 'Escape') {
        if (!document.getElementById('toast').hidden) {
            hideToast();   // Escape closes a refusal message first
            return;
        }
        if (state.edgeDraft) {
            cancelEdgeDraft();
        } else {
            deselectAll();
        }
    } else if (event.key === 'Delete' || event.key === 'Backspace') {
        // Typing in the search box must never delete cards.
        const tag = document.activeElement ? document.activeElement.tagName : '';
        if (tag === 'INPUT' || tag === 'TEXTAREA') return;

        // Prevent default backspace navigation
        if (event.key === 'Backspace') {
            event.preventDefault();
        }

        if (state.selectedEdgeID) {
            deleteEdge(state.selectedEdgeID);
        } else if (state.selectedNodeID) {
            deleteNode(state.selectedNodeID);
        }
    }
}

// ============================================================================
// RENDERING
// ============================================================================

function render() {
    renderCards();
    renderEdges();
    renderEdgeDraft();
    renderOrderList();
    renderStatus();
}

function renderCards() {
    const canvas = document.getElementById('canvas');

    // Clear existing cards
    canvas.innerHTML = '';

    // Render each node
    state.nodes.forEach(node => {
        const cardEl = createCardElement(node);
        canvas.appendChild(cardEl);
    });
}

function createCardElement(node) {
    const card = document.createElement('div');
    card.className = 'card';
    if (state.selectedNodeID === node.id) {
        card.classList.add('selected');
    }
    card.setAttribute('data-node-id', node.id);
    card.style.left = `${node.x}px`;
    card.style.top = `${node.y}px`;

    if (getOrderConflicts().has(node.id)) {
        card.classList.add('order-conflict');
        card.setAttribute('title', 'Order conflict: a connected card runs in the wrong order');
    }

    // Header: title plus the card's place in the run order
    const header = document.createElement('div');
    header.className = 'card-header';

    const title = document.createElement('span');
    title.className = 'card-title';
    title.textContent = node.title;
    header.appendChild(title);

    const badge = document.createElement('span');
    badge.className = 'order-badge';
    badge.textContent = String(state.order.indexOf(node.id) + 1);
    badge.setAttribute('aria-label', 'Run order ' + badge.textContent);
    header.appendChild(badge);
    card.appendChild(header);

    // Category label (blank cards: no other content yet)
    const cat = getCategory(node.type);
    const catEl = document.createElement('div');
    catEl.className = 'card-cat';
    catEl.textContent = cat ? cat.label : '';
    card.appendChild(catEl);

    // Header ports: Start (in) and Done (out) control ports, on every card except triggers
    const headerPorts = { input: [], output: [] };
    const listedPorts = { input: [], output: [] };
    node.ports.inputs.forEach(port => (port.implicit ? headerPorts.input : listedPorts.input).push(port));
    node.ports.outputs.forEach(port => (port.implicit ? headerPorts.output : listedPorts.output).push(port));
    headerPorts.input.forEach(port => header.appendChild(createPortElement(node, port, 'input', null)));
    headerPorts.output.forEach(port => header.appendChild(createPortElement(node, port, 'output', null)));

    // Body: one label per listed port; the coloured dots sit on the card edge, level with the labels
    const body = document.createElement('div');
    body.className = 'card-body';
    const rows = Math.max(listedPorts.input.length, listedPorts.output.length, 1);
    body.style.height = `${PORT_BODY_PAD * 2 + rows * PORT_ROW_H}px`;
    card.appendChild(body);

    ['input', 'output'].forEach(side => {
        const col = document.createElement('div');
        col.className = `port-labels ${side}-labels`;
        listedPorts[side].forEach((port, index) => {
            const label = document.createElement('div');
            label.className = 'port-label';
            label.style.color = classInfo(port.cls).color;
            label.textContent = port.name + (side === 'input' ? (port.multi ? ' +' : (port.optional ? ' ?' : '')) : '');
            label.setAttribute('title', portTooltip(port, side));
            col.appendChild(label);
            body.appendChild(createPortElement(node, port, side, PORT_BODY_PAD + index * PORT_ROW_H + PORT_ROW_H / 2));
        });
        body.appendChild(col);
    });

    // Card mousedown for drag/select
    card.addEventListener('mousedown', (e) => handleCardMouseDown(node.id, e));

    return card;
}

function portTooltip(port, side) {
    const info = classInfo(port.cls);
    let text = `${port.name}: ${info.label} (${info.colourName || ''} ${side})`.replace('  ', ' ');
    if (side === 'input' && port.multi) text += '. Takes several links.';
    else if (side === 'input' && port.optional) text += '. Optional.';
    else if (side === 'input') text += '. Needs a link or a setting.';
    return text;
}

// One port dot. topPx places it in the body; null leaves it to the CSS (header ports).
function createPortElement(node, port, side, topPx) {
    const portEl = document.createElement('div');
    portEl.className = `port ${side}-port cls-${port.cls}`;
    portEl.setAttribute('data-port-id', port.id);
    portEl.setAttribute('data-port-type', side);
    portEl.setAttribute('data-port-class', port.cls);
    portEl.setAttribute('title', portTooltip(port, side));
    portEl.setAttribute('aria-label', portTooltip(port, side));
    portEl.style.setProperty('--port-color', classInfo(port.cls).color);
    if (topPx !== null && topPx !== undefined) portEl.style.top = `${topPx}px`;

    const draft = state.edgeDraft;
    if (draft) {
        if (draft.startNodeID === node.id && draft.startPortID === port.id && draft.startPortType === side) {
            portEl.classList.add('active');
        } else if (draft.startNodeID !== node.id) {
            // While a link is dragged: ports it could end on glow, the rest fade
            const ok = portCanLink(draft.startPortType, draft.startCls, side, port.cls);
            portEl.classList.add(ok ? 'can-link' : 'cannot-link');
        }
    }

    portEl.addEventListener('mousedown', (e) => handlePortMouseDown(node.id, port.id, side, e));
    return portEl;
}

// ============================================================================
// PORT UI: legend, refused-link messages
// ============================================================================

function initializePortUI() {
    renderLegend();
    document.getElementById('messagesToggle').addEventListener('click', () => {
        state.ui.messagesOpen = !state.ui.messagesOpen;
        renderMessages();
    });
    document.getElementById('messagesClear').addEventListener('click', () => {
        state.messages = [];
        renderMessages();
    });
    document.getElementById('toastClose').addEventListener('click', hideToast);
    renderMessages();
}

function renderLegend() {
    const legend = document.getElementById('legend');
    legend.innerHTML = '';
    const title = document.createElement('span');
    title.className = 'legend-title';
    title.textContent = 'Ports: same colour links';
    legend.appendChild(title);
    PORT_CLASS_ORDER.forEach(cls => {
        const info = classInfo(cls);
        const item = document.createElement('span');
        item.className = 'legend-item';
        item.setAttribute('title', info.carries);
        const dot = document.createElement('span');
        dot.className = `legend-dot cls-${cls}`;
        dot.style.setProperty('--port-color', info.color);
        item.appendChild(dot);
        item.appendChild(document.createTextNode(info.label));
        legend.appendChild(item);
    });
}

let toastTimer = null;

// kind: 'error' (red, a refused link) or 'notice' (blue, a plain notice)
function showToast(text, kind) {
    const toast = document.getElementById('toast');
    document.getElementById('toastText').textContent = text;
    toast.className = kind === 'notice' ? 'notice' : '';
    toast.hidden = false;
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(hideToast, 9000);
}

function hideToast() {
    document.getElementById('toast').hidden = true;
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = null;
}

// Record a notice in the message list (newest last, at most MAX_MESSAGES kept)
function addMessage(level, code, message, details) {
    state.messages.push({ time: new Date().toLocaleTimeString(), level: level, code: code, message: message, details: details || {} });
    if (state.messages.length > MAX_MESSAGES) state.messages.shift();
    renderMessages();
}

// A plain notice (not an error): shown in blue and kept in the message list
function reportNotice(code, text) {
    addMessage('notice', code, text, {});
    showToast(text, 'notice');
}

// A link was refused: show it clearly, write it to the message list and to the console,
// and flash the ports involved.
function reportConnectionError(result, target) {
    const text = `Link refused (${result.code}): ${result.message}`;
    console.error('[link refused]', result.code, result.message, result.details);
    addMessage('error', result.code, result.message, result.details);
    showToast(text);

    const d = result.details || {};
    [d.from, d.to].forEach(end => {
        if (!end || !end.nodeID) return;
        const cardEl = document.querySelector(`[data-node-id="${end.nodeID}"]`);
        if (!cardEl) return;
        const portEl = cardEl.querySelector(`.port[data-port-id="${end.portID}"]`);
        if (!portEl) return;
        portEl.classList.add('port-error');
        setTimeout(() => portEl.classList.remove('port-error'), 1800);
    });
}

function renderMessages() {
    const count = state.messages.length;
    const toggle = document.getElementById('messagesToggle');
    toggle.textContent = `Messages (${count})`;
    toggle.classList.toggle('has-errors', state.messages.some(m => m.level === 'error'));
    toggle.setAttribute('aria-expanded', String(state.ui.messagesOpen));
    const panel = document.getElementById('messagesPanel');
    panel.hidden = !state.ui.messagesOpen;
    const list = document.getElementById('messagesList');
    list.innerHTML = '';
    if (count === 0) {
        const empty = document.createElement('li');
        empty.className = 'empty-note';
        empty.textContent = 'No messages. Refused links and notices are listed here.';
        list.appendChild(empty);
        return;
    }
    state.messages.slice().reverse().forEach(m => {
        const li = document.createElement('li');
        li.className = `message ${m.level}`;
        const head = document.createElement('div');
        head.className = 'message-head';
        head.textContent = `${m.time}  ${m.code}`;
        const body = document.createElement('div');
        body.textContent = m.message;
        li.appendChild(head);
        li.appendChild(body);
        list.appendChild(li);
    });
}

function renderEdges() {
    const svg = document.getElementById('edgeLayer');

    // Clear existing edges (except draft)
    const existingEdges = svg.querySelectorAll('.edge');
    existingEdges.forEach(el => el.remove());

    // Render each edge
    state.edges.forEach(edge => {
        const line = createEdgeLine(edge);
        if (line) {
            svg.appendChild(line);
        }
    });
}

// Return the center point of a port, in canvas coordinates, read directly from
// the live DOM. Deriving the point from layout (instead of hard-coded header /
// padding constants) keeps edges aligned with the port circles even if the CSS
// changes. Falls back to null if the elements are not rendered yet.
function getPortCenter(nodeID, portType, portID) {
    const cardEl = document.querySelector(`[data-node-id="${nodeID}"]`);
    if (!cardEl) return null;
    const portEl = cardEl.querySelector(
        `.port.${portType}-port[data-port-id="${portID}"]`
    );
    if (!portEl) return null;

    const canvas = document.getElementById('canvas');
    const canvasRect = canvas.getBoundingClientRect();
    const portRect = portEl.getBoundingClientRect();

    return {
        x: portRect.left + portRect.width / 2 - canvasRect.left,
        y: portRect.top + portRect.height / 2 - canvasRect.top
    };
}

function createEdgeLine(edge) {
    const fromNode = state.nodes.get(edge.fromNodeID);
    const toNode = state.nodes.get(edge.toNodeID);

    if (!fromNode || !toNode) return null;

    // Endpoints are the real port centers, read from the DOM.
    const from = getPortCenter(edge.fromNodeID, 'output', edge.fromPort);
    const to = getPortCenter(edge.toNodeID, 'input', edge.toPort);

    if (!from || !to) return null;

    const x1 = from.x;
    const y1 = from.y;
    const x2 = to.x;
    const y2 = to.y;

    const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    line.setAttribute('x1', x1);
    line.setAttribute('y1', y1);
    line.setAttribute('x2', x2);
    line.setAttribute('y2', y2);
    line.setAttribute('class', 'edge');
    line.setAttribute('data-edge-id', edge.id);
    // The line takes the colour of the output it starts from; a link to or from an Any port is dashed
    const startPort = findPort(fromNode, 'output', edge.fromPort);
    if (startPort) line.style.setProperty('--edge-color', classInfo(startPort.cls).color);
    if (edge.loose) line.classList.add('loose');

    if (state.selectedEdgeID === edge.id) {
        line.classList.add('selected');
    }

    line.addEventListener('click', (e) => handleEdgeClick(edge.id, e));

    return line;
}

function renderEdgeDraft() {
    const svg = document.getElementById('edgeLayer');

    // Remove existing draft line
    const existingDraft = svg.querySelector('.edge-draft');
    if (existingDraft) {
        existingDraft.remove();
    }

    if (!state.edgeDraft) return;

    // Source endpoint = the start port's real center
    const from = getPortCenter(
        state.edgeDraft.startNodeID, 
        state.edgeDraft.startPortType, 
        state.edgeDraft.startPortID
    );
    if (!from) return;

    const x1 = from.x;
    const y1 = from.y;
    
    // Target endpoint = snap target center if available, else cursor
    let x2, y2;
    if (state.edgeDraft.snapTarget) {
        const to = getPortCenter(
            state.edgeDraft.snapTarget.nodeID,
            state.edgeDraft.snapTarget.portType,
            state.edgeDraft.snapTarget.portID
        );
        if (to) {
            x2 = to.x;
            y2 = to.y;
        } else {
            x2 = state.edgeDraft.x;
            y2 = state.edgeDraft.y;
        }
    } else {
        x2 = state.edgeDraft.x;
        y2 = state.edgeDraft.y;
    }

    const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    line.setAttribute('x1', x1);
    line.setAttribute('y1', y1);
    line.setAttribute('x2', x2);
    line.setAttribute('y2', y2);
    line.setAttribute('class', 'edge-draft');
    // Red while the port under the cursor would be refused
    if (state.edgeDraft.check && !state.edgeDraft.check.ok) line.classList.add('invalid');

    svg.appendChild(line);
}

// ============================================================================
// SIDEBAR: open/close, tabs, catalog, category filter
// ============================================================================

function initializeSidebar() {
    document.getElementById('sidebarToggle').addEventListener('click', () => {
        setSidebarOpen(!state.ui.sidebarOpen);
    });

    document.querySelectorAll('#sidebarTabs .tab').forEach(btn => {
        btn.addEventListener('click', () => setTab(btn.getAttribute('data-tab')));
    });

    document.getElementById('searchInput').addEventListener('input', (e) => {
        state.ui.search = e.target.value.trim().toLowerCase();
        renderCatalog();
    });

    renderCategoryFilters();
    renderCatalog();
}

function setSidebarOpen(open) {
    state.ui.sidebarOpen = open;
    document.body.classList.toggle('sidebar-open', open);
    const btn = document.getElementById('sidebarToggle');
    btn.textContent = open ? 'Hide Sidebar' : 'Show Sidebar';
    btn.setAttribute('aria-expanded', String(open));
}

function setTab(tab) {
    state.ui.tab = tab;
    document.querySelectorAll('#sidebarTabs .tab').forEach(btn => {
        const active = btn.getAttribute('data-tab') === tab;
        btn.classList.toggle('active', active);
        btn.setAttribute('aria-selected', String(active));
    });
    document.getElementById('panelCatalog').hidden = tab !== 'catalog';
    document.getElementById('panelOrder').hidden = tab !== 'order';
    document.getElementById('panelModel').hidden = tab !== 'model';
}

function setCategory(categoryID) {
    state.ui.category = categoryID;
    renderCategoryFilters();
    renderCatalog();
}

function renderCategoryFilters() {
    const box = document.getElementById('categoryFilters');
    box.innerHTML = '';

    const entries = [{ id: 'all', label: 'All', count: CATALOG.length }]
        .concat(CATEGORIES.map(c => ({ id: c.id, label: c.label.split(' / ')[0], count: c.count })));

    entries.forEach(entry => {
        const chip = document.createElement('button');
        chip.type = 'button';
        chip.className = 'chip' + (state.ui.category === entry.id ? ' active' : '');
        chip.textContent = `${entry.label} (${entry.count})`;
        chip.setAttribute('aria-pressed', String(state.ui.category === entry.id));
        chip.setAttribute('data-category', entry.id);
        chip.addEventListener('click', () => setCategory(entry.id));
        box.appendChild(chip);
    });
}

// Cards that match the current category filter and search text.
function getVisibleCatalog() {
    return CATALOG.filter(card => {
        if (state.ui.category !== 'all' && card.category !== state.ui.category) return false;
        if (state.ui.search && !card.title.toLowerCase().includes(state.ui.search)) return false;
        return true;
    });
}

function renderCatalog() {
    const list = document.getElementById('catalogList');
    const summary = document.getElementById('catalogSummary');
    list.innerHTML = '';

    const visible = getVisibleCatalog();
    summary.textContent = `Showing ${visible.length} of ${CATALOG.length} cards. Click Add or drag onto the canvas.`;

    if (visible.length === 0) {
        const empty = document.createElement('li');
        empty.className = 'empty-note';
        empty.textContent = 'No cards match.';
        list.appendChild(empty);
        return;
    }

    visible.forEach(card => {
        const li = document.createElement('li');
        li.className = 'catalog-item';
        li.draggable = true;
        li.setAttribute('data-catalog-id', card.id);

        const title = document.createElement('span');
        title.className = 'item-title';
        title.textContent = card.title;
        li.appendChild(title);

        const cat = document.createElement('span');
        cat.className = 'item-cat';
        cat.textContent = card.id.replace('catalog_', '#');
        li.appendChild(cat);

        const add = document.createElement('button');
        add.type = 'button';
        add.className = 'mini-btn';
        add.textContent = 'Add';
        add.setAttribute('aria-label', 'Add ' + card.title + ' to canvas');
        add.addEventListener('click', () => addCardFromCatalog(card.id));
        li.appendChild(add);

        li.addEventListener('dragstart', (e) => {
            e.dataTransfer.setData('application/x-catalog-id', card.id);
            e.dataTransfer.setData('text/plain', card.id);
            e.dataTransfer.effectAllowed = 'copy';
        });

        list.appendChild(li);
    });
}

// ============================================================================
// DROP FROM SIDEBAR ONTO CANVAS (in-memory only)
// ============================================================================

function handleCanvasDragOver(event) {
    if (event.dataTransfer && event.dataTransfer.types.includes('application/x-catalog-id')) {
        event.preventDefault();
        event.dataTransfer.dropEffect = 'copy';
    }
}

function handleCanvasDrop(event) {
    const catalogID = event.dataTransfer.getData('application/x-catalog-id');
    if (!catalogID) return;
    event.preventDefault();
    const pt = mouseToCanvas(event);
    // Center the new card (about 180 x 110) under the cursor.
    addCardFromCatalog(catalogID, pt.x - 90, pt.y - 30);
}

// ============================================================================
// ORDER: explicit run order of the cards on the canvas
// ============================================================================

// Move a node to a new index in the run order.
function moveOrder(nodeID, toIndex) {
    const from = state.order.indexOf(nodeID);
    if (from === -1) return;
    const clamped = Math.max(0, Math.min(state.order.length - 1, toIndex));
    if (clamped === from) return;
    state.order.splice(from, 1);
    state.order.splice(clamped, 0, nodeID);
    render();
}

// Node IDs whose order contradicts a link: a card that feeds another card must
// come earlier in the order than the card it feeds.
function getOrderConflicts() {
    const conflicts = new Set();
    state.edges.forEach(edge => {
        const a = state.order.indexOf(edge.fromNodeID);
        const b = state.order.indexOf(edge.toNodeID);
        if (a !== -1 && b !== -1 && a > b) {
            conflicts.add(edge.fromNodeID);
            conflicts.add(edge.toNodeID);
        }
    });
    return conflicts;
}

let draggingOrderID = null;

function renderOrderList() {
    const list = document.getElementById('orderList');
    document.getElementById('orderCount').textContent = String(state.order.length);
    list.innerHTML = '';

    if (state.order.length === 0) {
        const empty = document.createElement('li');
        empty.className = 'empty-note';
        empty.textContent = 'No cards yet. Add some from the Cards tab.';
        list.appendChild(empty);
        return;
    }

    const conflicts = getOrderConflicts();

    state.order.forEach((nodeID, index) => {
        const node = state.nodes.get(nodeID);
        if (!node) return;

        const li = document.createElement('li');
        li.className = 'order-item' + (state.selectedNodeID === nodeID ? ' selected' : '');
        li.draggable = true;
        li.setAttribute('data-order-id', nodeID);

        const num = document.createElement('span');
        num.className = 'order-num';
        num.textContent = String(index + 1);
        li.appendChild(num);

        const title = document.createElement('span');
        title.className = 'item-title';
        title.textContent = node.title;
        li.appendChild(title);

        if (conflicts.has(nodeID)) {
            const warn = document.createElement('span');
            warn.className = 'order-warn';
            warn.textContent = '!';
            warn.setAttribute('title', 'Order conflict with a connected card');
            warn.setAttribute('aria-label', 'Order conflict with a connected card');
            li.appendChild(warn);
        }

        const up = document.createElement('button');
        up.type = 'button';
        up.className = 'mini-btn';
        up.textContent = '\u2191';
        up.disabled = index === 0;
        up.setAttribute('aria-label', 'Move ' + node.title + ' up');
        up.addEventListener('click', (e) => { e.stopPropagation(); moveOrder(nodeID, index - 1); });
        li.appendChild(up);

        const down = document.createElement('button');
        down.type = 'button';
        down.className = 'mini-btn';
        down.textContent = '\u2193';
        down.disabled = index === state.order.length - 1;
        down.setAttribute('aria-label', 'Move ' + node.title + ' down');
        down.addEventListener('click', (e) => { e.stopPropagation(); moveOrder(nodeID, index + 1); });
        li.appendChild(down);

        // Click a row to select that card on the canvas
        li.addEventListener('click', () => selectNode(nodeID));

        // Drag a row to reorder
        li.addEventListener('dragstart', (e) => {
            draggingOrderID = nodeID;
            e.dataTransfer.setData('application/x-order-id', nodeID);
            e.dataTransfer.effectAllowed = 'move';
            li.classList.add('dragging');
        });
        li.addEventListener('dragend', () => {
            draggingOrderID = null;
            li.classList.remove('dragging');
        });
        li.addEventListener('dragover', (e) => {
            if (!draggingOrderID) return;
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
            li.classList.add('drag-over');
        });
        li.addEventListener('dragleave', () => li.classList.remove('drag-over'));
        li.addEventListener('drop', (e) => {
            e.preventDefault();
            li.classList.remove('drag-over');
            if (draggingOrderID && draggingOrderID !== nodeID) {
                // The dragged card takes the place of the row it is dropped on.
                moveOrder(draggingOrderID, index);
            }
            draggingOrderID = null;
        });

        list.appendChild(li);
    });
}

function renderStatus() {
    const conflicts = getOrderConflicts().size;
    let text = `${state.nodes.size} cards \u00b7 ${state.edges.size} links`;
    if (conflicts > 0) text += ` \u00b7 ${conflicts} order conflicts`;
    
    if (state.buildConfirmed) {
        text += ' \u00b7 Build confirmed. Generation is not enabled yet.';
    }
    
    document.getElementById('status').textContent = text;
    
    // Update Generate button enabled state
    const generateBtn = document.getElementById('generateBtn');
    // Nothing to generate while only the Start card is on the canvas
    generateBtn.disabled = !Array.from(state.nodes.values()).some(n => n.role !== 'start');
}

// ============================================================================
// GENERATE & CONFIRMATION DIALOG
// ============================================================================

function handleGenerateClick() {
    const dialog = document.getElementById('confirmDialog');
    const content = document.getElementById('confirmDialogContent');
    
    const conflicts = getOrderConflicts();
    let message = `You have ${state.nodes.size} card${state.nodes.size !== 1 ? 's' : ''} and ${state.edges.size} link${state.edges.size !== 1 ? 's' : ''}.`;
    
    if (conflicts.size > 0) {
        message += `\n\nWarning: ${conflicts.size} card${conflicts.size !== 1 ? 's have' : ' has'} order conflicts with connected cards.`;
    }
    
    content.textContent = message;
    content.style.whiteSpace = 'pre-wrap';
    
    dialog.showModal();
}

function handleCancelDialog() {
    const dialog = document.getElementById('confirmDialog');
    dialog.close();
}

// Step 1 of generating: the user said the build is complete. If something is missing
// (inputs with no link, a Start card that leads nowhere, no End card), a second window
// says where and what, and asks again. Without problems the generation runs at once.
function handleConfirmGenerate() {
    document.getElementById('confirmDialog').close();
    const issues = findGenerationIssues(state.nodes, state.edges, state.order);
    if (issues.length > 0) {
        showIssuesDialog(issues);
        return;
    }
    runGeneration();
}

function initializeIssuesDialog() {
    document.getElementById('issuesBackBtn').addEventListener('click', () => {
        document.getElementById('issuesDialog').close();
    });
    document.getElementById('issuesGenerateBtn').addEventListener('click', () => {
        document.getElementById('issuesDialog').close();
        runGeneration();   // the user has seen what is missing and still wants to generate
    });
}

function showIssuesDialog(issues) {
    const list = document.getElementById('issuesList');
    list.innerHTML = '';
    document.getElementById('issuesIntro').textContent =
        `${issues.length} thing${issues.length !== 1 ? 's are' : ' is'} missing. You can go back and fix ` +
        `${issues.length !== 1 ? 'them' : 'it'}, or generate anyway.`;
    issues.forEach(issue => {
        const li = document.createElement('li');
        li.className = 'issue';
        const where = document.createElement('div');
        where.className = 'issue-where';
        where.textContent = issue.where;
        const what = document.createElement('div');
        what.className = 'issue-what';
        what.textContent = issue.message;
        const text = document.createElement('div');
        text.className = 'issue-text';
        text.appendChild(where);
        text.appendChild(what);
        li.appendChild(text);
        if (issue.nodeID && state.nodes.has(issue.nodeID)) {
            const show = document.createElement('button');
            show.type = 'button';
            show.className = 'mini-btn';
            show.textContent = 'Show';
            show.setAttribute('aria-label', 'Show ' + issue.where + ' on the canvas');
            show.addEventListener('click', () => {
                document.getElementById('issuesDialog').close();
                focusNode(issue.nodeID);
            });
            li.appendChild(show);
        }
        list.appendChild(li);
    });
    document.getElementById('issuesDialog').showModal();
}

// Select a card and scroll the canvas so that it is in view
function focusNode(nodeID) {
    const node = state.nodes.get(nodeID);
    if (!node) return;
    selectNode(nodeID);
    const container = document.getElementById('canvasContainer');
    container.scrollLeft = Math.max(0, node.x - 60);
    container.scrollTop = Math.max(0, node.y - 60);
}

function runGeneration() {
    // Set build confirmed flag
    state.buildConfirmed = true;
    
    // Validate that assembleBedrockRequest can build without error (but don't send)
    try {
        const request = assembleBedrockRequest();
        // Successfully assembled; we could validate structure here if needed
    } catch (error) {
        // If assembly fails, show error (shouldn't happen with current implementation)
        alert('Error assembling request: ' + error.message);
    }
    
    renderStatus();
}
