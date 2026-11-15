// ============================================================================
// BEDROCK MODELS, REGIONS AND TARGET RESOLUTION (pure data + functions)
// ============================================================================
// Snapshot of text models that work with the Bedrock Converse API
// (bedrock-runtime endpoint), taken from public Bedrock model cards on
// 2026-10-10 / 2026-10-24. Bedrock changes often: use "Custom model ID" for
// anything missing. See activity.md for what was left out and why.
//
// Profile prefixes per model: g = global, us, eu, apac, jp, au, in.
// A model with profiles usually cannot be called by its bare ID, so the
// resolver adds a prefix.

const PROFILE_ORDER = ['global', 'us', 'eu', 'jp', 'au', 'apac', 'in'];

// Region that receives the request when a given profile prefix is used.
const PROFILE_ENTRY_REGION = {
    global: 'us-east-1',
    us: 'us-east-1',
    eu: 'eu-west-1',
    jp: 'ap-northeast-1',
    au: 'ap-southeast-2',
    apac: 'ap-southeast-1',
    in: 'ap-south-1'
};

// Region groups for the dropdown. geo = profile prefixes that match, best first.
const REGION_GROUPS = [
    {
        label: 'United States and Canada', regions: [
            { value: 'us-east-1', label: 'US East (N. Virginia)', geo: ['us'] },
            { value: 'us-east-2', label: 'US East (Ohio)', geo: ['us'] },
            { value: 'us-west-2', label: 'US West (Oregon)', geo: ['us'] },
            { value: 'ca-central-1', label: 'Canada (Central)', geo: ['us'] }
        ]
    },
    {
        label: 'Europe', regions: [
            { value: 'eu-west-1', label: 'Europe (Ireland)', geo: ['eu'] },
            { value: 'eu-west-2', label: 'Europe (London)', geo: ['eu'] },
            { value: 'eu-west-3', label: 'Europe (Paris)', geo: ['eu'] },
            { value: 'eu-central-1', label: 'Europe (Frankfurt)', geo: ['eu'] },
            { value: 'eu-central-2', label: 'Europe (Zurich)', geo: ['eu'] },
            { value: 'eu-north-1', label: 'Europe (Stockholm)', geo: ['eu'] },
            { value: 'eu-south-1', label: 'Europe (Milan)', geo: ['eu'] },
            { value: 'eu-south-2', label: 'Europe (Spain)', geo: ['eu'] }
        ]
    },
    {
        label: 'Asia Pacific', regions: [
            { value: 'ap-northeast-1', label: 'Asia Pacific (Tokyo)', geo: ['jp', 'apac'] },
            { value: 'ap-northeast-3', label: 'Asia Pacific (Osaka)', geo: ['jp', 'apac'] },
            { value: 'ap-northeast-2', label: 'Asia Pacific (Seoul)', geo: ['apac'] },
            { value: 'ap-southeast-1', label: 'Asia Pacific (Singapore)', geo: ['apac'] },
            { value: 'ap-southeast-2', label: 'Asia Pacific (Sydney)', geo: ['au', 'apac'] },
            { value: 'ap-southeast-4', label: 'Asia Pacific (Melbourne)', geo: ['au', 'apac'] },
            { value: 'ap-southeast-3', label: 'Asia Pacific (Jakarta)', geo: ['apac'] },
            { value: 'ap-south-1', label: 'Asia Pacific (Mumbai)', geo: ['in', 'apac'] },
            { value: 'ap-south-2', label: 'Asia Pacific (Hyderabad)', geo: ['in', 'apac'] }
        ]
    },
    {
        label: 'South America', regions: [
            { value: 'sa-east-1', label: 'South America (Sao Paulo)', geo: [] }
        ]
    }
];

// Compact model table: [provider, label, id, profiles, legacy]
const MODEL_ROWS = [
    ['Anthropic Claude', 'Claude Haiku 5.5', 'anthropic.claude-haiku-5-5', 'global us eu au jp'],
    ['Anthropic Claude', 'Claude Sonnet 5.5', 'anthropic.claude-sonnet-5-5', 'global us eu au'],
    ['Anthropic Claude', 'Claude Opus 5.5', 'anthropic.claude-opus-5-5', 'global us eu au jp'],
    ['Anthropic Claude', 'Claude Fable 5.1', 'anthropic.claude-fable-5-1', 'global us'],
    ['Anthropic Claude', 'Claude Mythos 5.1', 'anthropic.claude-mythos-5-1', 'global us'],
    ['Anthropic Claude', 'Claude Opus 5', 'anthropic.claude-opus-5', 'global us eu au in'],
    ['Anthropic Claude', 'Claude Sonnet 5', 'anthropic.claude-sonnet-5', 'global us eu au in'],
    ['Anthropic Claude', 'Claude Fable 5', 'anthropic.claude-fable-5', 'global us'],
    ['Anthropic Claude', 'Claude Opus 4.8', 'anthropic.claude-opus-4-8', 'global us eu jp au'],
    ['Anthropic Claude', 'Claude Opus 4.7', 'anthropic.claude-opus-4-7', 'global us eu jp au'],
    ['Anthropic Claude', 'Claude Sonnet 4.6', 'anthropic.claude-sonnet-4-6', 'global us eu au jp'],
    ['Anthropic Claude', 'Claude Opus 4.6', 'anthropic.claude-opus-4-6-v1', 'global us eu au'],
    ['Anthropic Claude', 'Claude Opus 4.5', 'anthropic.claude-opus-4-5-20251101-v1:0', 'global us eu'],
    ['Anthropic Claude', 'Claude Haiku 4.5', 'anthropic.claude-haiku-4-5-20251001-v1:0', 'global us eu au jp in'],
    ['Anthropic Claude', 'Claude Sonnet 4.5', 'anthropic.claude-sonnet-4-5-20250929-v1:0', 'global us eu au jp', true],
    ['Anthropic Claude', 'Claude Opus 4.1', 'anthropic.claude-opus-4-1-20250805-v1:0', 'us', true],

    ['OpenAI', 'GPT-6.1 Sol', 'openai.gpt-6.1-sol', 'global us'],
    ['OpenAI', 'GPT-6 Sol', 'openai.gpt-6-sol', 'global us'],
    ['OpenAI', 'GPT-6 Luna', 'openai.gpt-6-luna', 'global us'],
    ['OpenAI', 'GPT-6 Astra', 'openai.gpt-6-astra', 'global us'],
    ['OpenAI', 'GPT-5.6 Sol', 'openai.gpt-5.6-sol', 'global us'],
    ['OpenAI', 'GPT-5.6 Luna', 'openai.gpt-5.6-luna', 'global us in'],
    ['OpenAI', 'GPT-5.6 Terra', 'openai.gpt-5.6-terra', 'global us in'],
    ['OpenAI', 'GPT-5.5', 'openai.gpt-5.5', 'global us'],
    ['OpenAI', 'GPT-5.4', 'openai.gpt-5.4', 'global us'],
    ['OpenAI', 'gpt-oss-120b', 'openai.gpt-oss-120b-1:0', ''],
    ['OpenAI', 'gpt-oss-20b', 'openai.gpt-oss-20b-1:0', ''],
    ['OpenAI', 'gpt-oss-safeguard-120b', 'openai.gpt-oss-safeguard-120b', ''],
    ['OpenAI', 'gpt-oss-safeguard-20b', 'openai.gpt-oss-safeguard-20b', ''],

    ['Amazon Nova', 'Nova 2 Lite', 'amazon.nova-2-lite-v1:0', 'global us eu jp'],
    ['Amazon Nova', 'Nova Pro', 'amazon.nova-pro-v1:0', 'us eu apac'],
    ['Amazon Nova', 'Nova Lite', 'amazon.nova-lite-v1:0', 'us eu apac'],
    ['Amazon Nova', 'Nova Micro', 'amazon.nova-micro-v1:0', 'us eu'],

    ['Meta Llama', 'Llama 4 Maverick 17B', 'meta.llama4-maverick-17b-instruct-v1:0', 'us'],
    ['Meta Llama', 'Llama 4 Scout 17B', 'meta.llama4-scout-17b-instruct-v1:0', 'us'],
    ['Meta Llama', 'Llama 3.3 70B', 'meta.llama3-3-70b-instruct-v1:0', 'us'],
    ['Meta Llama', 'Llama 3.2 90B', 'meta.llama3-2-90b-instruct-v1:0', 'us'],
    ['Meta Llama', 'Llama 3.2 11B', 'meta.llama3-2-11b-instruct-v1:0', 'us'],
    ['Meta Llama', 'Llama 3.2 3B', 'meta.llama3-2-3b-instruct-v1:0', 'us eu'],
    ['Meta Llama', 'Llama 3.2 1B', 'meta.llama3-2-1b-instruct-v1:0', 'us eu'],
    ['Meta Llama', 'Llama 3.1 405B', 'meta.llama3-1-405b-instruct-v1:0', 'us'],
    ['Meta Llama', 'Llama 3.1 70B', 'meta.llama3-1-70b-instruct-v1:0', 'us'],
    ['Meta Llama', 'Llama 3.1 8B', 'meta.llama3-1-8b-instruct-v1:0', 'us'],
    ['Meta Llama', 'Llama 3 70B', 'meta.llama3-70b-instruct-v1:0', ''],
    ['Meta Llama', 'Llama 3 8B', 'meta.llama3-8b-instruct-v1:0', ''],

    ['Mistral AI', 'Mistral Large 3 (675B)', 'mistral.mistral-large-3-675b-instruct', ''],
    ['Mistral AI', 'Devstral 2 123B', 'mistral.devstral-2-123b', ''],
    ['Mistral AI', 'Magistral Small 2509', 'mistral.magistral-small-2509', ''],
    ['Mistral AI', 'Ministral 3 14B', 'mistral.ministral-3-14b-instruct', ''],
    ['Mistral AI', 'Ministral 3 8B', 'mistral.ministral-3-8b-instruct', ''],
    ['Mistral AI', 'Ministral 3 3B', 'mistral.ministral-3-3b-instruct', ''],
    ['Mistral AI', 'Pixtral Large', 'mistral.pixtral-large-2502-v1:0', 'us eu'],
    ['Mistral AI', 'Mistral Large (2402)', 'mistral.mistral-large-2402-v1:0', ''],
    ['Mistral AI', 'Mistral Small (2402)', 'mistral.mistral-small-2402-v1:0', ''],
    ['Mistral AI', 'Mixtral 8x7B', 'mistral.mixtral-8x7b-instruct-v0:1', ''],
    ['Mistral AI', 'Mistral 7B', 'mistral.mistral-7b-instruct-v0:2', ''],

    ['Qwen', 'Qwen3 Coder Next', 'qwen.qwen3-coder-next', ''],
    ['Qwen', 'Qwen3 235B A22B 2507', 'qwen.qwen3-235b-a22b-2507-v1:0', ''],
    ['Qwen', 'Qwen3 Next 80B A3B', 'qwen.qwen3-next-80b-a3b', ''],
    ['Qwen', 'Qwen3 VL 235B A22B', 'qwen.qwen3-vl-235b-a22b', ''],
    ['Qwen', 'Qwen3 32B', 'qwen.qwen3-32b-v1:0', ''],
    ['Qwen', 'Qwen3 Coder 30B A3B', 'qwen.qwen3-coder-30b-a3b-v1:0', ''],
    ['Qwen', 'Qwen3 Coder 480B A35B', 'qwen.qwen3-coder-480b-a35b-v1:0', '', true],

    ['DeepSeek', 'DeepSeek V3.2', 'deepseek.v3.2', ''],
    ['DeepSeek', 'DeepSeek V3.1', 'deepseek.v3-v1:0', ''],
    ['DeepSeek', 'DeepSeek R1', 'deepseek.r1-v1:0', 'us'],

    ['Google Gemma', 'Gemma 3 27B', 'google.gemma-3-27b-it', ''],
    ['Google Gemma', 'Gemma 3 12B', 'google.gemma-3-12b-it', ''],
    ['Google Gemma', 'Gemma 3 4B', 'google.gemma-3-4b-it', ''],

    ['Moonshot Kimi', 'Kimi K3', 'moonshotai.kimi-k3', 'global us in'],
    ['Moonshot Kimi', 'Kimi K2.5', 'moonshotai.kimi-k2.5', ''],
    ['Moonshot Kimi', 'Kimi K2 Thinking', 'moonshot.kimi-k2-thinking', ''],

    ['MiniMax', 'MiniMax M2.5', 'minimax.minimax-m2.5', ''],
    ['MiniMax', 'MiniMax M2.1', 'minimax.minimax-m2.1', ''],
    ['MiniMax', 'MiniMax M2', 'minimax.minimax-m2', ''],

    ['Z.AI GLM', 'GLM 5.3', 'zai.glm-5.3', 'global us'],
    ['Z.AI GLM', 'GLM 5', 'zai.glm-5', ''],
    ['Z.AI GLM', 'GLM 4.7', 'zai.glm-4.7', ''],
    ['Z.AI GLM', 'GLM 4.7 Flash', 'zai.glm-4.7-flash', ''],

    ['xAI Grok', 'Grok 4.7', 'xai.grok-4.7', 'global us'],
    ['xAI Grok', 'Grok 4.6', 'xai.grok-4.6', 'global us'],

    ['NVIDIA Nemotron', 'Nemotron 3 Super 120B', 'nvidia.nemotron-super-3-120b', ''],
    ['NVIDIA Nemotron', 'Nemotron Nano 3 30B', 'nvidia.nemotron-nano-3-30b', ''],
    ['NVIDIA Nemotron', 'Nemotron Nano 12B v2', 'nvidia.nemotron-nano-12b-v2', ''],
    ['NVIDIA Nemotron', 'Nemotron Nano 9B v2', 'nvidia.nemotron-nano-9b-v2', ''],

    ['Writer Palmyra', 'Palmyra X5', 'writer.palmyra-x5-v1:0', 'us'],
    ['Writer Palmyra', 'Palmyra X4', 'writer.palmyra-x4-v1:0', 'us'],
    ['Writer Palmyra', 'Palmyra Vision 7B', 'writer.palmyra-vision-7b', '']
];

const MODEL_CATALOG = MODEL_ROWS.map((row) => ({
    provider: row[0],
    label: row[1] + (row[4] ? ' (Legacy)' : ''),
    id: row[2],
    profiles: row[3] ? row[3].split(' ') : [],
    legacy: !!row[4]
}));

const DEFAULT_MODEL_ID = 'anthropic.claude-sonnet-5-5';

function findModel(modelId) {
    return MODEL_CATALOG.find((m) => m.id === modelId) || null;
}

function findRegion(regionCode) {
    for (const group of REGION_GROUPS) {
        const hit = group.regions.find((r) => r.value === regionCode);
        if (hit) return hit;
    }
    return null;
}

// Guess the geography prefixes for a region typed by the user.
function guessGeo(regionCode) {
    if (/^(us|ca)-/.test(regionCode)) return ['us'];
    if (/^eu-/.test(regionCode)) return ['eu'];
    if (/^ap-northeast-[13]$/.test(regionCode)) return ['jp', 'apac'];
    if (/^ap-southeast-[24]$/.test(regionCode)) return ['au', 'apac'];
    if (/^ap-south-[12]$/.test(regionCode)) return ['in', 'apac'];
    if (/^ap-/.test(regionCode)) return ['apac'];
    return [];
}

const REGION_PATTERN = /^[a-z]{2}(-[a-z]+)+-\d$/;
const MODEL_ID_PATTERN = /^[A-Za-z0-9][A-Za-z0-9._:\/-]{2,200}$/;

// Work out which region and which model id the request will use.
// sel = { region: 'auto' | 'custom' | <region code>, customRegion, modelId: <id> | 'custom', customModel }
// Returns { region, modelId, route, note, error }.
//   route: 'global' | 'geo' | 'in-region' | 'custom'
function resolveBedrockTarget(sel) {
    const result = { region: 'us-east-1', modelId: '', route: 'in-region', note: '', error: '' };

    // Custom model id: used exactly as typed (the user may add a prefix already).
    if (sel.modelId === 'custom') {
        const typed = (sel.customModel || '').trim();
        if (!MODEL_ID_PATTERN.test(typed)) {
            result.error = 'Enter a model id, for example anthropic.claude-sonnet-5-5.';
        }
        result.modelId = typed;
        result.route = 'custom';
        const reg = resolveRegionOnly(sel, result);
        result.region = reg;
        return result;
    }

    const model = findModel(sel.modelId);
    if (!model) {
        result.error = 'Unknown model.';
        return result;
    }

    // Auto: best route for the model, no region needed from the user.
    if (sel.region === 'auto') {
        const prefix = PROFILE_ORDER.find((p) => model.profiles.includes(p));
        if (prefix) {
            result.region = PROFILE_ENTRY_REGION[prefix];
            result.modelId = prefix + '.' + model.id;
            result.route = prefix === 'global' ? 'global' : 'geo';
            result.note = prefix === 'global'
                ? 'AWS picks the best region. Data may be processed outside your own geography.'
                : 'Only a ' + prefix + '. profile exists for this model.';
        } else {
            result.region = 'us-east-1';
            result.modelId = model.id;
            result.route = 'in-region';
            result.note = 'No routing profile for this model. Sent to us-east-1; if it is not offered there, pick a region.';
        }
        return result;
    }

    // Fixed region (listed or custom).
    const region = resolveRegionOnly(sel, result);
    result.region = region;
    if (result.error) return result;

    const known = findRegion(region);
    const geo = known ? known.geo : guessGeo(region);
    const geoPrefix = geo.find((g) => model.profiles.includes(g));

    if (geoPrefix) {
        result.modelId = geoPrefix + '.' + model.id;
        result.route = 'geo';
    } else if (model.profiles.length === 0) {
        result.modelId = model.id;
        result.route = 'in-region';
        result.note = 'Called in ' + region + ' directly. Check this model is offered there.';
    } else if (model.profiles.includes('global')) {
        result.modelId = 'global.' + model.id;
        result.route = 'global';
        result.note = 'No profile for ' + region + ' exists for this model, so it goes through the global profile.';
    } else {
        result.modelId = model.id;
        result.route = 'in-region';
        result.note = 'This model has no profile for ' + region + '. The call may fail; try Auto or another region.';
    }
    return result;
}

function resolveRegionOnly(sel, result) {
    if (sel.region === 'custom') {
        const typed = (sel.customRegion || '').trim();
        if (!REGION_PATTERN.test(typed)) {
            result.error = result.error || 'Enter a region code, for example ap-southeast-1.';
            return 'us-east-1';
        }
        return typed;
    }
    if (sel.region === 'auto') return 'us-east-1';
    return sel.region;
}
