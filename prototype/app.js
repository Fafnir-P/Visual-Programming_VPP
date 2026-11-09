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
    edgeDraft: null,  // { startNodeID, startPortID, startPortType, x, y, snapTarget: null|{nodeID, portID, portType} }
    order: [],        // node IDs in run order (explicit user order)
    buildConfirmed: false,  // true after user confirms build is complete
    ui: {
        sidebarOpen: true,
        tab: 'catalog',       // 'catalog' | 'order' | 'model'
        category: 'all',      // category id or 'all'
        search: ''
    }
};

const SNAP_RADIUS = 40;

// ============================================================================
// INITIALIZATION
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    initializeSidebar();
    initBedrockUI();
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

    const id = `node_${state.nextNodeID++}`;
    const offset = (state.nodes.size * 30) % 240;

    const node = {
        id: id,
        catalogID: source.id,
        type: source.category,
        title: source.title,
        x: Math.max(0, x !== undefined ? x : 40 + offset),
        y: Math.max(0, y !== undefined ? y : 40 + offset),
        ports: {
            inputs: [{ id: 'in', name: 'Input' }],
            outputs: [{ id: 'out', name: 'Output' }]
        }
    };

    state.nodes.set(id, node);
    state.order.push(id);
    render();
    return node;
}

function deleteNode(nodeID) {
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
    state.edgeDraft = {
        startNodeID: nodeID,
        startPortID: portID,
        startPortType: portType,
        x: pt.x,
        y: pt.y,
        snapTarget: null
    };
    render();
}

function updateEdgeDraft(event) {
    if (!state.edgeDraft) return;

    const pt = mouseToCanvas(event);
    state.edgeDraft.x = pt.x;
    state.edgeDraft.y = pt.y;

    // Find nearest opposite port within snap radius
    const oppositeType = state.edgeDraft.startPortType === 'output' ? 'input' : 'output';
    let closestPort = null;
    let closestDistance = SNAP_RADIUS;

    state.nodes.forEach(node => {
        if (node.id === state.edgeDraft.startNodeID) return; // Skip same node
        
        const ports = oppositeType === 'input' ? node.ports.inputs : node.ports.outputs;
        ports.forEach(port => {
            const center = getPortCenter(node.id, oppositeType, port.id);
            if (!center) return;

            const dx = pt.x - center.x;
            const dy = pt.y - center.y;
            const dist = Math.sqrt(dx * dx + dy * dy);

            if (dist < closestDistance) {
                closestDistance = dist;
                closestPort = {
                    nodeID: node.id,
                    portID: port.id,
                    portType: oppositeType
                };
            }
        });
    });

    // Clear previous snap-target styling
    document.querySelectorAll('.port.snap-target').forEach(el => {
        el.classList.remove('snap-target');
    });

    // Update snap target
    state.edgeDraft.snapTarget = closestPort;

    // Apply snap-target class to the port DOM element
    if (closestPort) {
        const cardEl = document.querySelector(`[data-node-id="${closestPort.nodeID}"]`);
        if (cardEl) {
            const portEl = cardEl.querySelector(
                `.port.${closestPort.portType}-port[data-port-id="${closestPort.portID}"]`
            );
            if (portEl) {
                portEl.classList.add('snap-target');
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

    const { startNodeID, startPortID, startPortType, snapTarget } = state.edgeDraft;

    // Determine output and input sides
    let fromNodeID, fromPort, toNodeID, toPort;
    if (startPortType === 'output') {
        fromNodeID = startNodeID;
        fromPort = startPortID;
        toNodeID = snapTarget.nodeID;
        toPort = snapTarget.portID;
    } else {
        fromNodeID = snapTarget.nodeID;
        fromPort = snapTarget.portID;
        toNodeID = startNodeID;
        toPort = startPortID;
    }

    // Reject self-connection (already prevented by node filter, but double-check)
    if (fromNodeID === toNodeID) {
        cancelEdgeDraft();
        return;
    }

    // Check for duplicate edge
    const isDuplicate = Array.from(state.edges.values()).some(edge =>
        edge.fromNodeID === fromNodeID &&
        edge.fromPort === fromPort &&
        edge.toNodeID === toNodeID &&
        edge.toPort === toPort
    );

    if (isDuplicate) {
        cancelEdgeDraft();
        return;
    }

    // Create edge
    const edgeID = `edge_${state.nextEdgeID++}`;
    state.edges.set(edgeID, {
        id: edgeID,
        fromNodeID: fromNodeID,
        fromPort: fromPort,
        toNodeID: toNodeID,
        toPort: toPort
    });

    cancelEdgeDraft();
    render();
}

function cancelEdgeDraft() {
    // Clear snap-target styling
    document.querySelectorAll('.port.snap-target').forEach(el => {
        el.classList.remove('snap-target');
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

    // Body
    const body = document.createElement('div');
    body.className = 'card-body';
    card.appendChild(body);

    // Input ports
    node.ports.inputs.forEach((port, index) => {
        const portEl = document.createElement('div');
        portEl.className = 'port input-port';
        portEl.setAttribute('data-port-id', port.id);
        portEl.setAttribute('data-port-type', 'input');
        portEl.setAttribute('title', port.name);
        portEl.setAttribute('aria-label', port.name);
        portEl.style.top = `${30 + index * 25}px`;

        if (state.edgeDraft && 
            state.edgeDraft.startNodeID === node.id && 
            state.edgeDraft.startPortID === port.id &&
            state.edgeDraft.startPortType === 'input') {
            portEl.classList.add('active');
        }

        portEl.addEventListener('mousedown', (e) => handlePortMouseDown(node.id, port.id, 'input', e));

        body.appendChild(portEl);
    });

    // Output ports
    node.ports.outputs.forEach((port, index) => {
        const portEl = document.createElement('div');
        portEl.className = 'port output-port';
        portEl.setAttribute('data-port-id', port.id);
        portEl.setAttribute('data-port-type', 'output');
        portEl.setAttribute('title', port.name);
        portEl.setAttribute('aria-label', port.name);
        portEl.style.top = `${30 + index * 25}px`;

        if (state.edgeDraft && 
            state.edgeDraft.startNodeID === node.id && 
            state.edgeDraft.startPortID === port.id &&
            state.edgeDraft.startPortType === 'output') {
            portEl.classList.add('active');
        }

        portEl.addEventListener('mousedown', (e) => handlePortMouseDown(node.id, port.id, 'output', e));

        body.appendChild(portEl);
    });

    // Card mousedown for drag/select
    card.addEventListener('mousedown', (e) => handleCardMouseDown(node.id, e));

    return card;
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
    generateBtn.disabled = state.nodes.size === 0;
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

function handleConfirmGenerate() {
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
    
    // Close dialog and update status
    const dialog = document.getElementById('confirmDialog');
    dialog.close();
    
    renderStatus();
}
