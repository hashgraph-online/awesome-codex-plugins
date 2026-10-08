// Domain objects remain authoritative. React Flow's measurements and selection
// state never become workflow fields. Layout changes are explicit user edits.
import { t } from '../web/i18n.js';
export function canvasIssues(workflow) {
  const issues = []; const nodes = new Set(); const edges = new Set();
  if (!Array.isArray(workflow?.nodes) || !Array.isArray(workflow?.edges)) return [t('nodes 和 edges 必须是数组', 'nodes and edges must be arrays')];
  for (const [index, node] of workflow.nodes.entries()) {
    if (!node || typeof node.id !== 'string' || !node.id || typeof node.type !== 'string' || nodes.has(node.id)) { issues.push(`nodes[${index}] ${t('缺少唯一 ID 或类型', 'is missing a unique ID or type')}`); continue; }
    nodes.add(node.id);
    if (node.ui?.position && (!Number.isFinite(node.ui.position.x) || !Number.isFinite(node.ui.position.y))) issues.push(`nodes[${index}] ${t('的坐标必须是有限数字', 'coordinates must be finite numbers')}`);
  }
  for (const [index, edge] of workflow.edges.entries()) {
    if (!edge || typeof edge.id !== 'string' || !edge.id || edges.has(edge.id) || !nodes.has(edge.source) || !nodes.has(edge.target)) { issues.push(`edges[${index}] ${t('缺少唯一 ID 或有效端点', 'is missing a unique ID or valid endpoints')}`); continue; }
    edges.add(edge.id);
  }
  if (workflow.loops !== undefined && !Array.isArray(workflow.loops)) issues.push(t('loops 必须是数组', 'loops must be an array'));
  else for (const [index, loop] of (workflow.loops ?? []).entries()) {
    if (!loop || typeof loop.id !== 'string' || !Array.isArray(loop.node_ids) || loop.node_ids.some(id => !nodes.has(id))) issues.push(`loops[${index}] ${t('缺少有效 ID 或节点引用', 'is missing a valid ID or node reference')}`);
  }
  return issues;
}

function pointerTokens(pointer) {
  if (typeof pointer !== 'string' || (pointer !== '' && !pointer.startsWith('/')) || /~(?![01])/.test(pointer)) {
    throw Object.assign(new Error('Loop rename found an invalid JSON Pointer in a binding field'), { code: 'INVALID_POINTER' });
  }
  return pointer === '' ? [] : pointer.slice(1).split('/').map(token => token.replaceAll('~1', '/').replaceAll('~0', '~'));
}
function encodePointerToken(token) { return token.replaceAll('~', '~0').replaceAll('/', '~1'); }
function renameLoopPointer(pointer, oldId, newId) {
  const tokens = pointerTokens(pointer);
  if (tokens[0] !== 'loops' || tokens[1] !== oldId) return pointer;
  tokens[1] = newId;
  return '/' + tokens.map(encodePointerToken).join('/');
}
function renameBinding(binding, oldId, newId) {
  if (typeof binding === 'string') return renameLoopPointer(binding, oldId, newId);
  if (!binding || typeof binding !== 'object' || Array.isArray(binding)) return binding;
  const result = { ...binding };
  if (typeof result.path === 'string') result.path = renameLoopPointer(result.path, oldId, newId);
  if (Array.isArray(result.coalesce)) result.coalesce = result.coalesce.map(pointer => typeof pointer === 'string' ? renameLoopPointer(pointer, oldId, newId) : pointer);
  if (typeof result.zip === 'string') result.zip = renameLoopPointer(result.zip, oldId, newId);
  return result;
}
function renameBindingMap(bindings, oldId, newId) {
  if (!bindings || typeof bindings !== 'object' || Array.isArray(bindings)) return bindings;
  return Object.fromEntries(Object.entries(bindings).map(([name, binding]) => [name, renameBinding(binding, oldId, newId)]));
}
function renameExpression(expression, oldId, newId) {
  if (Array.isArray(expression)) return expression.map(item => renameExpression(item, oldId, newId));
  if (!expression || typeof expression !== 'object') return expression;
  const result = { ...expression };
  if (typeof expression.path === 'string') result.path = renameLoopPointer(expression.path, oldId, newId);
  else if (typeof expression.op === 'string' && Array.isArray(expression.args)) result.args = expression.args.map(item => renameExpression(item, oldId, newId));
  return result;
}

/** Rename one Workflow loop ID and only its exact JSON Pointer references. */
export function renameLoopId(workflow, oldId, newId) {
  if (!Array.isArray(workflow?.loops)) throw new Error('Workflow loops must be an array before renaming a loop');
  if (workflow.loops.filter(loop => loop?.id === oldId).length !== 1) throw new Error(`Expected exactly one loop with ID ${oldId}`);
  const next = structuredClone(workflow);
  for (const node of next.nodes ?? []) {
    if (node?.input_bindings !== undefined) node.input_bindings = renameBindingMap(node.input_bindings, oldId, newId);
    for (const item of node?.cases ?? []) if (item?.when !== undefined) item.when = renameExpression(item.when, oldId, newId);
  }
  for (const loop of next.loops) {
    if (loop?.until !== undefined) loop.until = renameExpression(loop.until, oldId, newId);
    if (loop?.feedback_bindings !== undefined) loop.feedback_bindings = renameBindingMap(loop.feedback_bindings, oldId, newId);
    if (loop?.item_scope) {
      loop.item_scope.items = renameBinding(loop.item_scope.items, oldId, newId);
      loop.item_scope.verdicts = renameBinding(loop.item_scope.verdicts, oldId, newId);
    }
  }
  next.loops.find(loop => loop?.id === oldId).id = newId;
  if (next.output_bindings !== undefined) next.output_bindings = renameBindingMap(next.output_bindings, oldId, newId);
  return next;
}

export function toCanvas(workflow, runtime = {}) {
  const issues = canvasIssues(workflow); if (issues.length) throw new Error(issues.join('\n'));
  const displayLayout = layoutGraph(workflow);
  const runtimeNodes = runtime.nodes ?? runtime;
  const runtimeLoops = runtime.loops ?? {};
  const nodes = workflow.nodes.map((node, index) => ({ id: node.id, type: 'workflow',
      position: node.ui?.position ?? displayLayout.nodes[index].ui.position,
      data: { definition: structuredClone(node), status: runtimeNodes[node.id]?.status ?? null,
        loopMembership: (workflow.loops ?? []).filter(loop => loop.node_ids?.includes(node.id)).map(loop => ({
          id: loop.id, max_rounds: loop.max_rounds, round: runtimeLoops[loop.id]?.round ?? null,
          status: runtimeLoops[loop.id]?.status ?? null,
        })) } }));
  const occupiedIds = new Set(nodes.map(node => node.id));
  const regions = (workflow.loops ?? []).map(loop => {
    const memberNodes = nodes.filter(node => loop.node_ids?.includes(node.id));
    if (!memberNodes.length) return null;
    const left = Math.min(...memberNodes.map(node => node.position.x));
    const top = Math.min(...memberNodes.map(node => node.position.y));
    const right = Math.max(...memberNodes.map(node => node.position.x + (node.width ?? 250)));
    const bottom = Math.max(...memberNodes.map(node => node.position.y + (node.height ?? 142)));
    let id = `__loop-region__:${loop.id}`;
    while (occupiedIds.has(id)) id += ':visual';
    occupiedIds.add(id);
    return {
      id, type: 'loopRegion', position: { x: left - 36, y: top - 54 },
      style: { width: right - left + 72, height: bottom - top + 92, pointerEvents: 'none' },
      zIndex: -2, draggable: false, selectable: false, connectable: false, focusable: false, deletable: false,
      data: { definition: structuredClone(loop), runtime: structuredClone(runtimeLoops[loop.id] ?? null) },
    };
  }).filter(Boolean);
  return {
    nodes: [...nodes, ...regions],
    edges: workflow.edges.map(edge => ({ id: edge.id, source: edge.source, target: edge.target,
      label: [edge.label, edge.on && edge.on !== 'success' ? ({ failure: t('失败', 'Failure'), always: t('始终', 'Always') }[edge.on] ?? edge.on) : ''].filter(Boolean).join(' · '),
      data: { definition: structuredClone(edge) } })),
  };
}
export function moveNode(workflow, id, position) {
  if (!Number.isFinite(position.x) || !Number.isFinite(position.y)) throw new Error(t('画布坐标无效', 'Invalid canvas position'));
  return { ...workflow, nodes: workflow.nodes.map(node => node.id === id ? { ...node, ui: { ...node.ui, position: { x: position.x, y: position.y } } } : node) };
}
export function removeElements(workflow, nodeIds, edgeIds = []) {
  return { ...workflow, nodes: workflow.nodes.filter(node => !nodeIds.includes(node.id)),
    edges: workflow.edges.filter(edge => !edgeIds.includes(edge.id) && !nodeIds.includes(edge.source) && !nodeIds.includes(edge.target)) };
}
export function connectNodes(workflow, source, target, id) {
  if (!workflow.nodes.some(node => node.id === source) || !workflow.nodes.some(node => node.id === target)) throw new Error(t('连接端点缺失', 'Connection endpoint missing'));
  return { ...workflow, edges: [...workflow.edges, { id, source, target, on: 'success' }] };
}
export function layoutGraph(workflow) {
  const ranks = new Map(workflow.nodes.map(node => [node.id, 0]));
  // Bounded even for an invalid cyclic Draft; the backend supplies diagnostics.
  for (let i = 0; i < workflow.nodes.length; i++) {
    let changed = false;
    for (const edge of workflow.edges) if (ranks.has(edge.source) && ranks.has(edge.target)) {
      const rank = Math.min(workflow.nodes.length, ranks.get(edge.source) + 1);
      if (rank > ranks.get(edge.target)) { ranks.set(edge.target, rank); changed = true; }
    }
    if (!changed) break;
  }
  const rows = new Map();
  return { ...workflow, nodes: workflow.nodes.map(node => {
    const rank = ranks.get(node.id); const row = rows.get(rank) ?? 0; rows.set(rank, row + 1);
    return { ...node, ui: { ...node.ui, position: { x: 50 + rank * 270, y: 70 + row * 160 } } };
  }) };
}
