// One execution plan shared by the CLI and generated dashboard.
export function priorityPlan(graphs, meta) {
    const byId = new Map(graphs.map(g => [g.id, g]));
    const order = meta.buildOrder || graphs.map(g => g.id);
    const issues = [];
    if (byId.size !== graphs.length) issues.push('Duplicate map ids');
    for (const g of graphs.filter(g => g.status === 'building')) if (!order.includes(g.id)) issues.push(`${g.id}: building map is missing from build order`);
    if (new Set(order).size !== order.length) issues.push('Build order contains duplicates');
    for (const id of order) if (!byId.has(id)) issues.push(`Build order: unknown map ${id}`);
    for (const g of graphs.filter(g => g.group === (meta.featureGroup || 'Features') || g.id === 'release')) if (!order.includes(g.id)) issues.push(`${g.id}: missing from build order`);
    const dependencies = g => g.id === 'release' ? [...new Set([...(Array.isArray(g.dependsOn) ? g.dependsOn : []), ...graphs.filter(x => x.group === (meta.featureGroup || 'Features')).map(x => x.id)])] : (Array.isArray(g.dependsOn) ? g.dependsOn : []);
    const visiting = new Set(), visited = new Set();
    function visit(g) {
        if (visiting.has(g.id)) { issues.push(`Dependency cycle at ${g.id}`); return; }
        if (visited.has(g.id)) return;
        visiting.add(g.id);
        if (g.dependsOn !== undefined && !Array.isArray(g.dependsOn)) issues.push(`${g.id}: dependsOn must be an array`);
        if (g.blockedBy !== undefined && typeof g.blockedBy !== 'string') issues.push(`${g.id}: blockedBy must be a string`);
        if (!['planned', 'building', 'delivered'].includes(g.status || 'delivered')) issues.push(`${g.id}: invalid status`);
        const deps = dependencies(g);
        if (!Array.isArray(deps)) issues.push(`${g.id}: dependsOn must be an array`);
        else for (const id of deps) {
            if (!byId.has(id)) issues.push(`${g.id}: unknown dependency ${id}`);
            else {
                const dep = byId.get(id);
                if ((dep.status || 'delivered') !== 'delivered' && !order.includes(id)) issues.push(`${g.id}: unfinished dependency ${id} is missing from build order`);
                if ((g.status || 'delivered') === 'delivered' && (dep.status || 'delivered') !== 'delivered') issues.push(`${g.id}: delivered before dependency ${id}`);
                visit(dep); if (order.includes(g.id) && order.includes(id) && order.indexOf(id) >= order.indexOf(g.id)) issues.push(`${g.id}: dependency ${id} must come first`); }
        }
        visiting.delete(g.id); visited.add(g.id);
        const p = g.priority;
        if (g.priority !== undefined && g.priority !== null && (typeof p !== 'object' || !['big', 'small'].includes(p.rock) || typeof p.important !== 'boolean' || typeof p.urgent !== 'boolean' || typeof p.reason !== 'string' || !p.reason.trim())) issues.push(`${g.id}: priority needs rock, important, urgent and reason`);
    }
    graphs.forEach(visit);
    const queue = order.map(id => byId.get(id)).filter(g => g && (g.status || 'delivered') !== 'delivered').map(g => ({
        id: g.id, title: g.title, status: g.status, priority: g.priority || null,
        blockers: [g.blockedBy, ...dependencies(g).filter(id => !byId.has(id) || (byId.get(id).status || 'delivered') !== 'delivered').map(id => `Needs ${id}`)].filter(Boolean)
    }));
    const active = queue.filter(g => g.status === 'building');
    if (active.length > 1) issues.push('Multiple building maps: retain one active map; checkpoint other maps as planned with a reason.');
    const focus = active.find(g => !g.blockers.length);
    const next = active.length ? focus : queue.find(g => !g.blockers.length);
    return { next: issues.length ? null : next?.id || null, queue, active: active.map(g => g.id), warnings: active.some(g => g.blockers.length) ? ['Active map is blocked: record a checkpoint and return it to planned before selecting unrelated work.'] : [], issues };
}
