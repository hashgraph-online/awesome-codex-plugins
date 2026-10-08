function workflowNodes(workflow) {
  return Array.isArray(workflow?.nodes)
    ? workflow.nodes.filter(node => node && typeof node.id === 'string' && node.id)
    : [];
}

function canReach(workflow, fromId, targetId) {
  if (fromId === targetId) return true;
  const validIds = new Set(workflowNodes(workflow).map(node => node.id));
  const outgoing = new Map();
  for (const edge of Array.isArray(workflow?.edges) ? workflow.edges : []) {
    if (!edge || typeof edge.source !== 'string' || typeof edge.target !== 'string') continue;
    if (!validIds.has(edge.source) || !validIds.has(edge.target)) continue;
    const targets = outgoing.get(edge.source) ?? new Set();
    targets.add(edge.target);
    outgoing.set(edge.source, targets);
  }
  const seen = new Set([fromId]);
  const queue = [fromId];
  for (let index = 0; index < queue.length; index += 1) {
    for (const next of outgoing.get(queue[index]) ?? []) {
      if (next === targetId) return true;
      if (seen.has(next)) continue;
      seen.add(next);
      queue.push(next);
    }
  }
  return false;
}

/**
 * Return the upstream Codex task nodes that can be used as a continuation
 * source. The traversal is breadth-first so distance is graph distance from
 * the selected node, and the visited-distance map makes malformed cycles
 * finite. Results are sorted by distance and id so graph array ordering does
 * not change the editor's choices.
 */
export function findUpstreamThreadSources(workflow, selectedNodeId) {
  if (typeof selectedNodeId !== 'string' || !selectedNodeId) return [];
  const nodes = workflowNodes(workflow);
  const nodesById = new Map(nodes.map(node => [node.id, node]));
  if (!nodesById.has(selectedNodeId)) return [];

  const incoming = new Map();
  for (const edge of Array.isArray(workflow?.edges) ? workflow.edges : []) {
    if (!edge || typeof edge.source !== 'string' || typeof edge.target !== 'string') continue;
    if (!nodesById.has(edge.source) || !nodesById.has(edge.target)) continue;
    const sources = incoming.get(edge.target) ?? new Set();
    sources.add(edge.source);
    incoming.set(edge.target, sources);
  }

  const distances = new Map([[selectedNodeId, 0]]);
  const queue = [selectedNodeId];
  for (let index = 0; index < queue.length; index += 1) {
    const target = queue[index];
    const nextDistance = distances.get(target) + 1;
    for (const source of incoming.get(target) ?? []) {
      const previousDistance = distances.get(source);
      if (previousDistance !== undefined && previousDistance <= nextDistance) continue;
      distances.set(source, nextDistance);
      queue.push(source);
    }
  }

  return [...distances.entries()]
    .filter(([id]) => id !== selectedNodeId)
    .map(([id, distance]) => ({ id, distance, providerId: nodesById.get(id)?.executor?.provider_id ?? '' }))
    .filter(option => nodesById.get(option.id)?.executor?.kind === 'thread')
    .sort((left, right) => left.distance - right.distance || left.id.localeCompare(right.id));
}

/**
 * Resolve the source to show when a thread node is changed to continue mode.
 * An existing valid source wins. Otherwise a unique nearest source using the
 * current provider is selected. Incomparable candidates remain empty so the
 * editor requires an intentional source choice instead of guessing from node
 * order.
 */
export function resolveThreadSource(workflow, selectedNodeId, { providerId = '', sourceNodeId = '' } = {}) {
  const options = findUpstreamThreadSources(workflow, selectedNodeId);
  const selected = options.find(option => option.id === sourceNodeId);
  const matching = options.filter(option => option.providerId === providerId && option.providerId);
  // A source is the closest valid continuation only when every other
  // same-provider candidate can reach it. This preserves an explicit choice
  // for branches that merely happen to have different path lengths.
  const nearest = matching.filter(candidate => matching.every(other => other.id === candidate.id || canReach(workflow, other.id, candidate.id)));
  const candidate = selected ?? (nearest.length === 1 ? nearest[0] : null);
  return {
    options,
    matching,
    sourceNodeId: candidate?.id ?? '',
    providerId: candidate?.providerId ?? providerId,
    needsSelection: !candidate,
    ambiguous: !selected && matching.length > 1 && nearest.length !== 1,
    noMatch: !selected && matching.length === 0,
  };
}
