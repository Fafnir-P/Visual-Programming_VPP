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
    edgeDraft: null  // { fromNodeID, fromPort, x, y }
};

// ============================================================================
// INITIALIZATION
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    render();
});

function initializeEventListeners() {
    // Add Card button
    document.getElementById('addCardBtn').addEventListener('click', addCard);

    // Canvas background click (deselect)
    const canvas = document.getElementById('canvas');
    canvas.addEventListener('mousedown', handleCanvasMouseDown);

    // Keyboard events
    document.addEventListener('keydown', handleKeyDown);

    // Mouse move for drag and edge draft
    document.addEventListener('mousemove', handleDocumentMouseMove);
    document.addEventListener('mouseup', handleDocumentMouseUp);
}

// ============================================================================
// CARD MANAGEMENT
// ============================================================================

function addCard() {
    const id = `node_${state.nextNodeID++}`;
    const offset = (state.nodes.size * 30) % 200;

    const node = {
        id: id,
        type: 'generic',
        title: `Card ${state.nodes.size + 1}`,
        x: 100 + offset,
        y: 100 + offset,
        ports: {
            inputs: [{ id: 'in', name: 'Input' }],
            outputs: [{ id: 'out', name: 'Output' }]
        }
    };

    state.nodes.set(id, node);
    render();
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

function startEdgeDraft(fromNodeID, fromPort, event) {
    const pt = mouseToCanvas(event);
    state.edgeDraft = {
        fromNodeID: fromNodeID,
        fromPort: fromPort,
        x: pt.x,
        y: pt.y
    };
    render();
}

function updateEdgeDraft(x, y) {
    if (state.edgeDraft) {
        state.edgeDraft.x = x;
        state.edgeDraft.y = y;
        renderEdgeDraft();
    }
}

function completeEdgeDraft(toNodeID, toPort) {
    if (!state.edgeDraft) return;

    const { fromNodeID, fromPort } = state.edgeDraft;

    // Reject self-connection
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
        return;  // Port click handlers will handle this
    }

    event.stopPropagation();
    startDrag(nodeID, event);
}

function handleOutputPortClick(nodeID, portID, event) {
    event.stopPropagation();
    startEdgeDraft(nodeID, portID, event);
}

function handleInputPortClick(nodeID, portID, event) {
    event.stopPropagation();

    if (state.edgeDraft) {
        completeEdgeDraft(nodeID, portID);
    }
}

function handleEdgeClick(edgeID, event) {
    event.stopPropagation();
    selectEdge(edgeID);
}

function handleDocumentMouseMove(event) {
    if (dragState) {
        updateDrag(event);
    } else if (state.edgeDraft) {
        const pt = mouseToCanvas(event);
        updateEdgeDraft(pt.x, pt.y);
    }
}

function handleDocumentMouseUp(event) {
    if (dragState) {
        endDrag();
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
        // Prevent default backspace navigation
        if (event.key === 'Backspace' &&
            !['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) {
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

    // Header
    const header = document.createElement('div');
    header.className = 'card-header';
    header.textContent = node.title;
    card.appendChild(header);

    // Body
    const body = document.createElement('div');
    body.className = 'card-body';
    card.appendChild(body);

    // Input ports
    node.ports.inputs.forEach((port, index) => {
        const portEl = document.createElement('div');
        portEl.className = 'port input-port';
        portEl.setAttribute('data-port-id', port.id);
        portEl.setAttribute('title', port.name);
        portEl.setAttribute('aria-label', port.name);
        portEl.style.top = `${30 + index * 25}px`;

        // Always attach the handler; the handler itself checks for an active
        // draft. This avoids a fragile dependency on render ordering.
        portEl.addEventListener('click', (e) => handleInputPortClick(node.id, port.id, e));

        body.appendChild(portEl);
    });

    // Output ports
    node.ports.outputs.forEach((port, index) => {
        const portEl = document.createElement('div');
        portEl.className = 'port output-port';
        portEl.setAttribute('data-port-id', port.id);
        portEl.setAttribute('title', port.name);
        portEl.setAttribute('aria-label', port.name);
        portEl.style.top = `${30 + index * 25}px`;

        if (state.edgeDraft && state.edgeDraft.fromNodeID === node.id && state.edgeDraft.fromPort === port.id) {
            portEl.classList.add('active');
        }

        portEl.addEventListener('click', (e) => handleOutputPortClick(node.id, port.id, e));

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

    // Source endpoint = the output port's real center; target = the cursor.
    const from = getPortCenter(
        state.edgeDraft.fromNodeID, 'output', state.edgeDraft.fromPort
    );
    if (!from) return;

    const x1 = from.x;
    const y1 = from.y;
    const x2 = state.edgeDraft.x;
    const y2 = state.edgeDraft.y;

    const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    line.setAttribute('x1', x1);
    line.setAttribute('y1', y1);
    line.setAttribute('x2', x2);
    line.setAttribute('y2', y2);
    line.setAttribute('class', 'edge-draft');

    svg.appendChild(line);
}
