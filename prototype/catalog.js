// ============================================================================
// CARD CATALOG: 200 blank cards
// ============================================================================
// Counts follow the framework's planning allocation (section 4). Every card is
// blank on purpose: only an ID, a primary category and a placeholder title.
// Real card contracts and content come in a later phase.

const CATEGORIES = [
    { id: 'ui',          label: 'UI / Interface',          count: 30 },
    { id: 'backend',     label: 'Backend Processing',      count: 60 },
    { id: 'data',        label: 'Data Modeling / Storage', count: 30 },
    { id: 'logic',       label: 'Logic / Validation',      count: 25 },
    { id: 'trigger',     label: 'Triggers / Orchestration', count: 15 },
    { id: 'integration', label: 'Integrations / Connectors', count: 20 },
    { id: 'ai',          label: 'AI Capabilities',         count: 10 },
    { id: 'output',      label: 'Navigation / Output',     count: 10 }
];

// Build the catalog once. IDs are stable: catalog_001 ... catalog_200.
const CATALOG = (function buildCatalog() {
    const cards = [];
    let n = 1;
    CATEGORIES.forEach(cat => {
        for (let i = 1; i <= cat.count; i++) {
            cards.push({
                id: 'catalog_' + String(n).padStart(3, '0'),
                category: cat.id,
                title: cat.label.split(' / ')[0] + ' ' + String(i).padStart(2, '0')
            });
            n++;
        }
    });
    return cards;
})();

function getCategory(categoryID) {
    return CATEGORIES.find(c => c.id === categoryID);
}

function getCatalogCard(catalogID) {
    return CATALOG.find(c => c.id === catalogID);
}
