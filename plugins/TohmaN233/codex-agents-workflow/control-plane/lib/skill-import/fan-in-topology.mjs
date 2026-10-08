const activeEdge = edge => (edge.on ?? 'success') !== 'failure';

function graphParts(nodes, edges) {
  const nodeById = new Map((nodes ?? []).map(node => [node.id, node]));
  const incoming = new Map([...nodeById.keys()].map(id => [id, []]));
  const outgoing = new Map([...nodeById.keys()].map(id => [id, []]));
  for (const edge of edges ?? []) if (activeEdge(edge) && nodeById.has(edge.source) && nodeById.has(edge.target)) {
    incoming.get(edge.target).push(edge);
    outgoing.get(edge.source).push(edge);
  }
  return { nodeById, incoming, outgoing };
}

function reachable(outgoing, start, destination, blocked) {
  const seen = new Set(), queue = [start];
  while (queue.length) {
    const current = queue.shift();
    if (current === destination) return true;
    if (current === blocked || seen.has(current)) continue;
    seen.add(current);
    for (const edge of outgoing.get(current) ?? []) queue.push(edge.target);
  }
  return false;
}

/**
 * Identify a fan-in whose incoming routes are distinct labels of one condition.
 * Such routes are mutually exclusive at runtime and must not be validated as a
 * parallel aggregate where every input is simultaneously present.
 */
export function exclusiveConditionFanIn(nodes, edges, targetId) {
  const { nodeById, incoming, outgoing } = graphParts(nodes, edges);
  const targetInputs = incoming.get(targetId) ?? [];
  if (targetInputs.length < 2) return null;
  const conditions=[...nodeById.values()].filter(node=>node.type==='condition').map(condition=>({
    id:condition.id,
    branches:(outgoing.get(condition.id) ?? []).filter(edge=>typeof edge.label==='string'),
  })).filter(condition=>condition.branches.length>=2);
  const assignments=targetInputs.map(input=>({edge_id:input.id,source:input.source,conditions:Object.fromEntries(conditions.map(condition=>[
    condition.id,
    [...new Set(condition.branches.filter(branch=>(input.source===condition.id&&input.id===branch.id)||reachable(outgoing,branch.target,input.source,targetId)).map(branch=>branch.label))],
  ]))}));
  for(let left=0;left<assignments.length;left++)for(let right=left+1;right<assignments.length;right++){
    const separated=conditions.some(condition=>{
      const a=assignments[left].conditions[condition.id],b=assignments[right].conditions[condition.id];
      return a.length===1&&b.length===1&&a[0]!==b[0];
    });
    if(!separated)return null;
  }
  return {condition_ids:conditions.map(item=>item.id),assignments};
}

/** Return the closest semantic producers behind transparent control nodes. */
export function nearestDataProducerIds(nodes, edges, targetId) {
  const { nodeById, incoming, outgoing } = graphParts(nodes, edges);
  const found = new Set(), seen = new Set(), queue = (incoming.get(targetId) ?? []).map(edge => edge.source);
  while (queue.length) {
    const current = queue.shift();
    if (seen.has(current)) continue;
    seen.add(current);
    const node = nodeById.get(current);
    if (['agent', 'tool'].includes(node?.type)) found.add(current);
    else for (const edge of incoming.get(current) ?? []) queue.push(edge.source);
  }
  const ids = [...found];
  // Prefer a later producer when both it and an ancestor are available (for
  // example a remediation review over the initial review), then stay stable.
  ids.sort((left, right) => {
    if (reachable(outgoing, left, right)) return 1;
    if (reachable(outgoing, right, left)) return -1;
    return left.localeCompare(right);
  });
  return ids;
}

export function selectedUpstreamBinding(nodes, edges, targetId) {
  const pointers = nearestDataProducerIds(nodes, edges, targetId).map(id => `/nodes/${id}/output`);
  if (pointers.length === 0) return null;
  return pointers.length === 1 ? pointers[0] : { coalesce: pointers };
}
