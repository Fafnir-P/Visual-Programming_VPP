// ============================================================================
// METER: token estimate and generation wait time
// ============================================================================
// Pure functions, no network, no DOM. Two things are kept apart:
//   - "generation wait": time between startGeneration() and endGeneration() (the model call).
//   - "task completion time": first card placed -> preview accepted. NOT measured here (out of scope);
//     only the field names are reserved in TASK_TIME_FIELDS.
// Token numbers are never invented: with no usage recorded the summary says 'uncertain' and
// the token fields are null, not 0.

const TASK_TIME_FIELDS = ['firstCardPlacedAt', 'previewAcceptedAt'];

let meterState = { usage: [], waits: [], startedAt: null };

function resetMeter() {
    meterState = { usage: [], waits: [], startedAt: null };
}

// Estimate only: about 4 characters per token. Real counts come from the model reply.
function estimateTokens(text) {
    return Math.ceil(String(text === undefined || text === null ? '' : text).length / 4);
}

function startGeneration(now) {
    meterState.startedAt = now === undefined ? Date.now() : now;
}

function endGeneration(now) {
    if (meterState.startedAt === null) return null;
    const end = now === undefined ? Date.now() : now;
    const ms = Math.max(0, end - meterState.startedAt);
    meterState.waits.push(ms);
    meterState.startedAt = null;
    return ms;
}

// usage: {input, output, estimated}. estimated true -> 'estimate'; otherwise 'reported' (numbers
// from the model reply). A missing or non-numeric count makes the record 'uncertain'.
function recordUsage(usage) {
    const u = usage || {};
    const good = (n) => typeof n === 'number' && isFinite(n) && n >= 0;
    if (!good(u.input) || !good(u.output)) {
        meterState.usage.push({ accounting: 'uncertain', input: null, output: null });
        return;
    }
    const rec = { accounting: u.estimated ? 'estimate' : 'reported', input: u.input, output: u.output };
    if (typeof u.note === 'string' && u.note) rec.note = u.note;
    meterState.usage.push(rec);
}

function summary() {
    const recs = meterState.usage;
    let accounting = 'uncertain';
    let input = null;
    let output = null;
    if (recs.length && recs.every((r) => r.accounting !== 'uncertain')) {
        accounting = recs.every((r) => r.accounting === 'reported') ? 'reported' : 'estimate';
        input = recs.reduce((a, r) => a + r.input, 0);
        output = recs.reduce((a, r) => a + r.output, 0);
    }
    return {
        inputTokens: input,
        outputTokens: output,
        totalTokens: input === null ? null : input + output,
        waitMs: meterState.waits.length ? meterState.waits.reduce((a, b) => a + b, 0) : null,
        accounting: accounting,
        note: recs.length && recs.every((r) => r.note) ? recs[0].note : null
    };
}
