// ============================================================================
// AWS BEDROCK INTEGRATION
// ============================================================================
// This module manages Bedrock API configuration (credentials, region, model)
// and assembles the Converse API request. It does NOT execute network calls;
// that responsibility is deferred to a later phase.

const bedrockState = {
    apiKey: '',              // Bearer token API key (memory-only, never persisted)
    region: 'us-east-1',
    modelId: 'anthropic.claude-3-5-sonnet-20241022-v2:0'
};

const REGIONS = [
    { value: 'us-east-1', label: 'US East (N. Virginia)' },
    { value: 'us-west-2', label: 'US West (Oregon)' },
    { value: 'eu-west-1', label: 'EU (Ireland)' },
    { value: 'custom', label: 'Custom...' }
];

const MODELS = [
    { value: 'anthropic.claude-3-5-sonnet-20241022-v2:0', label: 'Claude 3.5 Sonnet (Oct 2024)' },
    { value: 'anthropic.claude-3-5-haiku-20241022-v1:0', label: 'Claude 3.5 Haiku (Oct 2024)' },
    { value: 'anthropic.claude-3-sonnet-20240229-v1:0', label: 'Claude 3 Sonnet (Feb 2024)' },
    { value: 'anthropic.claude-3-haiku-20240307-v1:0', label: 'Claude 3 Haiku (Mar 2024)' },
    { value: 'custom', label: 'Custom model ID...' }
];

function initBedrockUI() {
    const apiKeyInput = document.getElementById('bedrockApiKeyInput');
    const apiKeyToggle = document.getElementById('bedrockApiKeyToggle');
    const regionSelect = document.getElementById('regionSelect');
    const customRegionInput = document.getElementById('customRegionInput');
    const modelSelect = document.getElementById('modelSelect');
    const customModelInput = document.getElementById('customModelInput');
    const statusLine = document.getElementById('bedrockStatus');

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
        const value = e.target.value;
        if (value === 'custom') {
            customRegionInput.hidden = false;
            customRegionInput.focus();
            bedrockState.region = customRegionInput.value || 'us-east-1';
        } else {
            customRegionInput.hidden = true;
            bedrockState.region = value;
        }
    });

    customRegionInput.addEventListener('input', (e) => {
        bedrockState.region = e.target.value || 'us-east-1';
    });

    // Model select
    modelSelect.addEventListener('change', (e) => {
        const value = e.target.value;
        if (value === 'custom') {
            customModelInput.hidden = false;
            customModelInput.focus();
            bedrockState.modelId = customModelInput.value || bedrockState.modelId;
        } else {
            customModelInput.hidden = true;
            bedrockState.modelId = value;
        }
    });

    customModelInput.addEventListener('input', (e) => {
        bedrockState.modelId = e.target.value || 'anthropic.claude-3-5-sonnet-20241022-v2:0';
    });

    updateBedrockStatus();
}

function updateBedrockStatus() {
    const statusLine = document.getElementById('bedrockStatus');
    const hasKey = bedrockState.apiKey.length > 0;
    statusLine.textContent = `API key: ${hasKey ? 'set' : 'not set'}`;
}

function getBedrockEndpoint() {
    return `https://bedrock-runtime.${bedrockState.region}.amazonaws.com/model/${encodeURIComponent(bedrockState.modelId)}/converse`;
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
