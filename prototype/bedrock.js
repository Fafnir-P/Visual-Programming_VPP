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

// Serialize the current graph state into the format expected by the prompt.
function serializeGraph() {
    const nodes = state.order.map(nodeID => {
        const node = state.nodes.get(nodeID);
        if (!node) return null;
        return {
            id: node.id,
            catalogID: node.catalogID,
            title: node.title,
            category: node.type,
            templateCode: '',  // Blank placeholder; real content in later phase
            config: {}
        };
    }).filter(n => n !== null);

    const edges = Array.from(state.edges.values()).map(edge => ({
        id: edge.id,
        from: {
            node: edge.fromNodeID,
            port: edge.fromPort
        },
        to: {
            node: edge.toNodeID,
            port: edge.toPort
        }
    }));

    return {
        nodes: nodes,
        edges: edges,
        order: state.order
    };
}

// Assemble a Bedrock Converse API request. Returns the structure but does NOT
// execute any network call. The caller is responsible for fetch/XHR.
// Throws if the region or model choice is not valid.
function assembleBedrockRequest() {
    const graph = serializeGraph();

    return {
        url: getBedrockEndpoint(),
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
            // Authorization header NOT included here; caller must add it
        },
        body: {
            system: [
                { text: SYSTEM_PROMPT }
            ],
            messages: [
                {
                    role: 'user',
                    content: [
                        { text: JSON.stringify(graph, null, 2) }
                    ]
                }
            ],
            inferenceConfig: {
                maxTokens: 8192,
                temperature: 0
            }
        }
    };
}
