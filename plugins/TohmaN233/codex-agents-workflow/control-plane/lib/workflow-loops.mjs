import { lstat, readFile, realpath } from 'node:fs/promises';
import { isAbsolute, relative, resolve, sep } from 'node:path';
import { bindingPointers, evaluateExpression, pointerParts, resolveBindings, validateExpression } from './workflow-bindings.mjs';
import { canonicalJSON, digest } from './workflow-revisions.mjs';
import { requireValue } from './workflow-paths.mjs';

const object = value => value && typeof value === 'object' && !Array.isArray(value);
const definitions = workflow => workflow.loops ?? [];
const finished = new Set(['succeeded', 'skipped', 'failed', 'cancelled']);
const own = (record, key, value) => Object.defineProperty(record, key, { value, enumerable: true, configurable: true, writable: true });
const publicLoop = loop => Object.fromEntries(['round', 'status', 'feedback', 'all_accepted', 'review_items', 'repair_items'].map(key => [key, loop[key]]));
function refreshContext(state, context) {
  context.loops = Object.fromEntries(Object.entries(state.loops ?? {}).map(([id, loop]) => [id, publicLoop(loop)]));
  return context;
}
function contextOf(state) {
  return refreshContext(state, { inputs: state.inputs, nodes: Object.fromEntries(Object.entries(state.nodes).map(([id, node]) => [id, { output: node.output }])) });
}
function loopGraph(workflow) {
  const nodes = new Map(workflow.nodes.map(node => [node.id, node]));
  const out = new Map([...nodes.keys()].map(id => [id, []]));
  const incoming = new Map([...nodes.keys()].map(id => [id, []]));
  for (const edge of workflow.edges) {
    requireValue(nodes.has(edge.source) && nodes.has(edge.target), 'LOOP_REGION_INVALID', 'Loop graph edge names an unknown node');
    out.get(edge.source).push(edge); incoming.get(edge.target).push(edge);
  }
  const degrees = new Map([...incoming].map(([id, edges]) => [id, edges.length]));
  const todo = [...nodes.keys()].filter(id => !degrees.get(id)); let count = 0;
  while (todo.length) { const id = todo.pop(); count++; for (const edge of out.get(id)) { degrees.set(edge.target, degrees.get(edge.target) - 1); if (!degrees.get(edge.target)) todo.push(edge.target); } }
  requireValue(count === nodes.size, 'GRAPH_CYCLE', 'Loops require an ordinary acyclic graph');
  return { nodes, out, incoming };
}

export function validateLoopRegions(workflow) {
  requireValue(workflow.loops === undefined || Array.isArray(workflow.loops), 'LOOP_SCHEMA', 'Workflow loops must be an array');
  if (!definitions(workflow).length) return true;
  const graph = loopGraph(workflow), ids = new Set();
  const checkPointer = pointer => {
    const parts = pointerParts(pointer);
    requireValue(parts[0] === 'inputs' || parts[0] === 'nodes' && graph.nodes.has(parts[1]) && parts[2] === 'output' || parts[0] === 'loops' && definitions(workflow).some(loop => loop.id === parts[1]) && ['round', 'status', 'feedback', 'all_accepted', 'review_items', 'repair_items'].includes(parts[2]), 'LOOP_BINDING_INVALID', 'Loop bindings may read Run inputs, node outputs or public loop fields', { pointer });
  };
  for (const loop of definitions(workflow)) {
    requireValue(object(loop) && Object.keys(loop).every(key => ['id', 'entry_node', 'exit_node', 'node_ids', 'max_rounds', 'until', 'feedback_bindings', 'item_scope'].includes(key)), 'LOOP_SCHEMA', 'Loop contains unsupported fields');
    requireValue(typeof loop.id === 'string' && /^[a-z0-9][a-z0-9._-]{0,63}$/.test(loop.id) && !ids.has(loop.id), 'LOOP_SCHEMA', 'Loop IDs must be unique portable identifiers'); ids.add(loop.id);
    requireValue(Number.isSafeInteger(loop.max_rounds) && loop.max_rounds >= 1, 'LOOP_SCHEMA', 'Loop max_rounds must be a positive integer', { loop_id: loop.id });
    requireValue(Array.isArray(loop.node_ids) && loop.node_ids.length > 0 && new Set(loop.node_ids).size === loop.node_ids.length && loop.node_ids.every(id => graph.nodes.has(id)), 'LOOP_REGION_INVALID', 'Loop node_ids must name unique existing nodes', { loop_id: loop.id });
    const members = new Set(loop.node_ids);
    requireValue(members.has(loop.entry_node) && members.has(loop.exit_node), 'LOOP_REGION_INVALID', 'Loop boundaries must belong to the region', { loop_id: loop.id });
    const ancestors = start => {
      const seen=new Set(), queue=[start];
      while(queue.length){const id=queue.pop();if(seen.has(id))continue;seen.add(id);for(const edge of graph.incoming.get(id))queue.push(edge.source);}
      return seen;
    };
    const atEntry=ancestors(loop.entry_node),atExit=ancestors(loop.exit_node);
    const checkAvailable=(pointer,phase)=>{
      checkPointer(pointer);const parts=pointerParts(pointer);
      if(parts[0]==='nodes')requireValue((phase==='entry'?atEntry:atExit).has(parts[1])&&(phase!=='entry'||!members.has(parts[1])),
        'LOOP_BINDING_UNAVAILABLE',`Loop ${phase} binding cannot depend on a future or reset body output`,{loop_id:loop.id,pointer});
      if(parts[0]==='loops'&&parts[1]===loop.id)requireValue(phase!=='entry','LOOP_BINDING_UNAVAILABLE','Loop items cannot depend on their own uninitialized projection',{loop_id:loop.id,pointer});
      else if(parts[0]==='loops'){
        const source=definitions(workflow).find(item=>item.id===parts[1]);
        const enclosing=source.node_ids.every(id=>members.has(id))===false&&loop.node_ids.every(id=>source.node_ids.includes(id));
        requireValue(enclosing||(phase==='entry'?atEntry:atExit).has(source.exit_node),'LOOP_BINDING_UNAVAILABLE','Loop binding depends on an unavailable region',{loop_id:loop.id,pointer});
      }
    };
    requireValue(!members.has(workflow.finalization?.node_id), 'LOOP_FINALIZATION', 'Final acceptance must remain outside repair loops', { loop_id: loop.id });
    for (const edge of workflow.edges) {
      if (!members.has(edge.source) && members.has(edge.target)) requireValue(edge.target === loop.entry_node, 'LOOP_REGION_INVALID', 'A loop has one external entry', { loop_id: loop.id, edge_id: edge.id });
      if (members.has(edge.source) && !members.has(edge.target)) requireValue(edge.source === loop.exit_node, 'LOOP_REGION_INVALID', 'A loop has one external exit', { loop_id: loop.id, edge_id: edge.id });
    }
    function reachable(start, reverse) {
      const visited = new Set(), queue = [start];
      while (queue.length) { const id = queue.pop(); if (visited.has(id)) continue; visited.add(id); for (const edge of (reverse ? graph.incoming : graph.out).get(id)) { const next = reverse ? edge.source : edge.target; if (members.has(next)) queue.push(next); } }
      return visited;
    }
    requireValue(reachable(loop.entry_node, false).size === members.size && reachable(loop.exit_node, true).size === members.size, 'LOOP_REGION_INVALID', 'Every loop member must lie on an entry-to-exit path', { loop_id: loop.id });
    for (const node of workflow.nodes.filter(node => node.type === 'parallel')) requireValue(members.has(node.id) === members.has(node.join_id), 'LOOP_PARALLEL_BOUNDARY', 'A parallel node and its join must belong to the same loop region', { loop_id: loop.id, node_id: node.id });
    const exit = graph.nodes.get(loop.exit_node);
    requireValue(!(exit.completion_contract?.fail_on_false?.length), 'LOOP_EXIT_GUARD', 'A loop review exit must return rejection as semantic data', { loop_id: loop.id });
    if (['agent', 'skill_ref'].includes(exit.type)) requireValue(exit.access === 'read_only' && (exit.executor?.kind === 'provider' || exit.executor?.kind === 'main' && (exit.executor.mode ?? 'worker') === 'worker' || exit.executor?.kind === 'thread' && exit.executor.lifecycle === 'start'), 'LOOP_REVIEW_CONTEXT', 'A loop Agent exit must be an independent read-only reviewer', { loop_id: loop.id });
    validateExpression(loop.until, { onPointer: pointer=>checkAvailable(pointer,'exit') });
    if (loop.feedback_bindings !== undefined) {
      requireValue(object(loop.feedback_bindings), 'LOOP_SCHEMA', 'Loop feedback_bindings must be named bindings');
      for (const binding of Object.values(loop.feedback_bindings)) for (const pointer of bindingPointers(binding)) checkAvailable(pointer,'exit');
    }
    if (loop.item_scope !== undefined) {
      const scope = loop.item_scope;
      requireValue(object(scope) && Object.keys(scope).every(key => ['items', 'verdicts', 'paths_field', 'dependencies_field'].includes(key)) && typeof scope.paths_field === 'string' && scope.paths_field.length > 0 && (scope.dependencies_field === undefined || typeof scope.dependencies_field === 'string' && scope.dependencies_field.length > 0), 'LOOP_SCHEMA', 'Loop item_scope needs item/verdict bindings and declared path fields');
      for (const pointer of bindingPointers(scope.items)) checkAvailable(pointer,'entry');
      for (const pointer of bindingPointers(scope.verdicts)) {
        checkAvailable(pointer,'exit');const parts=pointerParts(pointer);
        requireValue(parts[0]==='nodes'&&members.has(parts[1]),'LOOP_BINDING_UNAVAILABLE','Item verdicts must be produced inside the current review round',{loop_id:loop.id,pointer});
      }
      requireValue(['agent','skill_ref','tool'].includes(exit.type)&&exit.access==='read_only','LOOP_REVIEW_CONTEXT','Item acceptance needs an executed read-only review exit',{loop_id:loop.id});
      const repairNodes = new Set(loop.node_ids.filter(id => Object.values(graph.nodes.get(id).input_bindings ?? {}).some(binding => bindingPointers(binding).some(pointer => {
        const parts = pointerParts(pointer); return parts[0] === 'loops' && parts[1] === loop.id && parts[2] === 'repair_items';
      }))));
      for (const [name, binding] of Object.entries(exit.input_bindings ?? {})) {
        const pointers = bindingPointers(binding);
        const repairOnly = pointers.every(pointer => { const parts = pointerParts(pointer); return parts[0] === 'nodes' && repairNodes.has(parts[1]) && parts[2] === 'output'; });
        requireValue(!repairOnly || object(binding) && Object.hasOwn(binding, 'default'), 'LOOP_INITIAL_REVIEW_INPUT', 'First-round review cannot require output from a repair that runs only after rejection; bind an optional default or an available coalesced source', { loop_id: loop.id, binding: name });
      }
    }
  }
  for (let i = 0; i < definitions(workflow).length; i++) for (let j = i + 1; j < definitions(workflow).length; j++) {
    const a = new Set(definitions(workflow)[i].node_ids), b = new Set(definitions(workflow)[j].node_ids);
    const overlap = [...a].filter(id => b.has(id));
    requireValue(!overlap.length || a.size !== b.size && (overlap.length === a.size || overlap.length === b.size), 'LOOP_REGION_OVERLAP', 'Loop regions must be disjoint or strictly nested');
  }
  return true;
}

export function loopBoundary(workflow, nodeId) {
  return definitions(workflow).filter(loop => loop.node_ids.includes(nodeId)).sort((a, b) => a.node_ids.length - b.node_ids.length);
}
export function loopRoundSignature(state, workflow, nodeId) {
  return Object.fromEntries(loopBoundary(workflow, nodeId).map(loop => [loop.id, { round: state.loops?.[loop.id]?.round ?? 0, lineage: structuredClone(state.loops?.[loop.id]?.lineage ?? []) }]));
}
export const currentRoundSignature = loopRoundSignature;

function emptyIteration() {
  return { round: 0, status: 'pending', feedback: {}, all_accepted: false, review_items: [], repair_items: [], lineage: [], items: [], ledger: [], review_indices: [], repair_indices: [], observed_revisions: [] };
}
export function initializeLoops(state, workflow) {
  state.loops ??= {};
  for (const definition of definitions(workflow)) if (!Object.hasOwn(state.loops, definition.id)) own(state.loops, definition.id, { ...emptyIteration(), rounds: [] });
  return state.loops;
}
function parentLoops(workflow, definition) {
  return definitions(workflow).filter(loop => loop.id !== definition.id && definition.node_ids.every(id => loop.node_ids.includes(id))).sort((a, b) => b.node_ids.length - a.node_ids.length);
}
function projectItems(loop) {
  loop.review_items = loop.review_indices.map(index => structuredClone(loop.items[index]));
  // Current findings supersede source findings in the repair packet. The original
  // item remains unchanged in loop.items and the immutable round snapshots.
  loop.repair_items = loop.repair_indices.map(index => ({ ...structuredClone(loop.items[index]), findings: structuredClone(loop.ledger[index].findings ?? null) }));
  loop.all_accepted = loop.ledger.every(item => item.status === 'accepted');
}
function within(root, target) { const rel = relative(root, target); return rel === '' || rel !== '..' && !rel.startsWith('..' + sep) && !isAbsolute(rel); }
function itemPaths(item, scope, logicalWorkspace, physicalWorkspace = logicalWorkspace) {
  requireValue(object(item), 'LOOP_ITEM_INVALID', 'Loop source items must be records');
  const paths = item[scope.paths_field], dependencies = scope.dependencies_field === undefined ? [] : item[scope.dependencies_field] ?? [];
  requireValue(Array.isArray(paths) && paths.length > 0 && Array.isArray(dependencies), 'LOOP_ITEM_INVALID', 'Each loop item needs artifact paths and an optional dependency path array');
  const logical = resolve(logicalWorkspace), physical = resolve(physicalWorkspace);
  return [...new Set([...paths, ...dependencies].map(path => {
    requireValue(typeof path === 'string' && path.trim() && !/[\x00-\x1f*?\[\]{}!]/.test(path), 'LOOP_ITEM_PATH', 'Loop file paths must be concrete nonempty paths');
    const declared = resolve(logical, path.trim());
    requireValue(within(logical, declared) && declared !== logical, 'LOOP_ITEM_PATH', 'Loop file path must stay inside the Run workspace', { path });
    const local = resolve(physical, relative(logical, declared));
    requireValue(within(physical, local), 'LOOP_ITEM_PATH', 'Loop file path must stay inside the physical workspace', { path });
    return relative(physical, local).split(sep).join('/');
  }))].sort();
}
function sourceAvailable(binding, state) {
  return bindingPointers(binding).some(pointer => {
    const parts = pointerParts(pointer);
    return parts[0] === 'nodes' && state.nodes[parts[1]]?.output === null && !finished.has(state.nodes[parts[1]]?.status);
  });
}
function validateItemPool(items, definition, workflow, workspace) {
  requireValue(Array.isArray(items), 'LOOP_ITEM_INVALID', 'Loop item binding must resolve to an array', { loop_id: definition.id });
  const exit = workflow.nodes.find(node => node.id === definition.exit_node);
  const fanoutBinding = exit.fanout && exit.input_bindings?.[exit.fanout.input];
  const fansOutReviewItems = fanoutBinding && bindingPointers(fanoutBinding).some(pointer => {
    const parts = pointerParts(pointer);
    return parts[0] === 'loops' && parts[1] === definition.id && parts[2] === 'review_items';
  });
  requireValue(!fansOutReviewItems || items.length > 0, 'LOOP_ITEM_EMPTY', 'An item review fan-out requires a nonempty source list', { loop_id: definition.id, node_id: exit.id });
  for (const item of items) itemPaths(item, definition.item_scope, workspace);
}
export function validateLoopItemSources(state, workflow, { allowUnavailable = false } = {}) {
  if (!definitions(workflow).some(loop => loop.item_scope)) return true;
  const context = contextOf(state);
  for (const definition of definitions(workflow).filter(loop => loop.item_scope)) {
    let items;
    try { items = resolveBindings({ items: definition.item_scope.items }, context).items; }
    catch (error) {
      // A missing optional source is enforced only when its region is selected.
      // Available items still receive path checks before any executor effect.
      const entryEdges=workflow.edges.filter(edge=>edge.target===definition.entry_node&&!definition.node_ids.includes(edge.source));
      const selected=entryEdges.length===0||entryEdges.every(edge=>state.edges[edge.id]!=='pending')&&entryEdges.some(edge=>state.edges[edge.id]==='selected');
      if (allowUnavailable && error.code === 'BINDING_MISSING' && state.loops?.[definition.id]?.status !== 'running' && (!selected||sourceAvailable(definition.item_scope.items,state))) continue;
      throw error;
    }
    if (items === null && allowUnavailable && sourceAvailable(definition.item_scope.items, state)) continue;
    validateItemPool(items, definition, workflow, state.permissions.workspace);
  }
  return true;
}

export function prepareLoops(state, workflow, context) {
  if (!definitions(workflow).length) return false;
  context ??= contextOf(state);
  initializeLoops(state, workflow); const graph = loopGraph(workflow); let changed = false;
  for (const definition of [...definitions(workflow)].sort((a, b) => b.node_ids.length - a.node_ids.length)) {
    const loop = state.loops[definition.id]; if (loop.status !== 'pending') continue;
    const parents = parentLoops(workflow, definition);
    if (parents.some(parent => state.loops[parent.id].status !== 'running')) continue;
    const external = graph.incoming.get(definition.entry_node).filter(edge => !definition.node_ids.includes(edge.source));
    if (external.some(edge => state.edges[edge.id] === 'pending') || external.length && !external.some(edge => state.edges[edge.id] === 'selected')) continue;
    refreshContext(state, context);
    if (definition.item_scope) {
      const items = resolveBindings({ items: definition.item_scope.items }, context).items;
      validateItemPool(items, definition, workflow, state.permissions.workspace);
      loop.items = structuredClone(items); loop.ledger = items.map(() => ({ status: 'pending', findings: null, revision: null }));
      loop.review_indices = items.map((_, index) => index); loop.repair_indices = []; projectItems(loop);
    }
    loop.round = 1; loop.status = 'running'; loop.lineage = parents.map(parent => ({ id: parent.id, round: state.loops[parent.id].round }));
    for (const id of definition.node_ids) state.nodes[id].current_loop_rounds = loopRoundSignature(state, workflow, id);
    changed = true;
  }
  refreshContext(state, context); return changed;
}

async function fileRevision(workspace, path) {
  requireValue(!(await lstat(resolve(workspace))).isSymbolicLink(), 'LOOP_ITEM_PATH', 'The physical loop workspace must not be a symbolic link');
  const root = await realpath(resolve(workspace)), target = resolve(workspace, path);
  requireValue(within(resolve(workspace), target), 'LOOP_ITEM_PATH', 'Observed file escapes the workspace');
  // Reject links at each owned component, including broken links. ENOENT alone
  // represents a missing file; permission and I/O failures remain visible.
  let current = resolve(workspace);
  try {
    const parts = relative(current, target).split(sep);
    for (let index = 0; index < parts.length; index++) {
      current = resolve(current, parts[index]); const entry = await lstat(current);
      requireValue(!entry.isSymbolicLink(), 'LOOP_ITEM_PATH', 'Loop observations do not follow symlink or reparse paths', { path });
      if (index < parts.length - 1) requireValue(entry.isDirectory(), 'LOOP_ITEM_FILE', 'Loop file ancestors must be directories', { path });
    }
    const canonical = await realpath(target);
    requireValue(within(root, canonical), 'LOOP_ITEM_PATH', 'Observed file resolves outside the physical workspace', { path });
    requireValue((await lstat(target)).isFile(), 'LOOP_ITEM_FILE', 'Loop item paths must name regular files', { path });
    return { path, hash: digest(await readFile(target)), missing: false };
  } catch (error) { if (error.code !== 'ENOENT') throw error; return { path, hash: null, missing: true }; }
}
function invalidateAcceptedItems(loop,observed) {
  for(let index=0;index<loop.ledger.length;index++){
    const item=loop.ledger[index],current=observed[index];if(item.status!=='accepted')continue;
    if(current.missing){
      item.status='failed';item.revision=null;
      item.findings={semantic:structuredClone(item.findings??null),host:{code:'LOOP_ARTIFACT_MISSING',message:'Required artifact or dependency files are missing',paths:current.files.filter(file=>file.missing).map(file=>file.path)}};
    }else if(item.revision!==current.revision)item.status='invalidated';
  }
}
export async function observeLoopItems(state, workflow, nodeId, workspace) {
  const result = {};
  for (const definition of loopBoundary(workflow, nodeId).filter(loop => loop.exit_node === nodeId && loop.item_scope)) {
    const loop = state.loops[definition.id]; if (loop?.status !== 'running') continue;
    const items = [];
    for (let index = 0; index < loop.items.length; index++) {
      const files = [];
      for (const path of itemPaths(loop.items[index], definition.item_scope, state.permissions.workspace, workspace)) files.push(await fileRevision(workspace, path));
      items.push({ index, revision: digest(canonicalJSON(files)), missing: files.some(file => file.missing), files });
    }
    const node = state.nodes[nodeId], attempt = node.attempts.find(item => item.id === node.active_attempt_id);
    if (!attempt?.loop_observation?.before) {
      invalidateAcceptedItems(loop,items);
      loop.review_indices = loop.ledger.flatMap((item, index) => item.status === 'accepted' ? [] : [index]); projectItems(loop);
    }
    loop.observed_revisions = structuredClone(items);
    own(result, definition.id, { round: loop.round, lineage: structuredClone(loop.lineage), review_indices: [...loop.review_indices], items });
  }
  return result;
}

function verdictsFor(state, definition, context) {
  let verdicts;
  try { verdicts = resolveBindings({ verdicts: definition.item_scope.verdicts }, context).verdicts; }
  catch (error) { if (error.code === 'BINDING_MISSING') throw Object.assign(new Error('Loop review verdict binding is unavailable'), { code: 'LOOP_VERDICT_INVALID', loop_id: definition.id }); throw error; }
  const loop = state.loops[definition.id];
  requireValue(Array.isArray(verdicts) && verdicts.length === loop.review_indices.length && verdicts.every(verdict => object(verdict) && typeof verdict.accepted === 'boolean' && Object.keys(verdict).every(key => ['accepted', 'findings'].includes(key))), 'LOOP_VERDICT_INVALID', 'Loop verdicts must contain one semantic accepted/findings record per current review item', { loop_id: definition.id });
  canonicalJSON(verdicts); return verdicts;
}
export function validateLoopExitOutput(state, workflow, nodeId, output) {
  const exits = loopBoundary(workflow, nodeId).filter(loop => loop.exit_node === nodeId);
  if (!exits.length) return true;
  const context = contextOf(state); context.nodes[nodeId] = { output };
  for (const definition of exits) {
    if (state.loops?.[definition.id]?.status !== 'running') continue;
    if (definition.item_scope) verdictsFor(state, definition, context);
    if (definition.feedback_bindings) resolveBindings(definition.feedback_bindings, context);
  }
  return true;
}

function recordRound(state, workflow, definition, loop, observations) {
  const members = new Set(definition.node_ids);
  const parallel = Object.fromEntries(Object.entries(state.parallel ?? {}).filter(([id]) => members.has(id)).map(([id, value]) => [id, structuredClone(value)]));
  for (const [id, value] of Object.entries(parallel)) requireValue(value.phase === 'merged' || value.phase === 'failed' || value.phase === 'cancelled', 'LOOP_PARALLEL_UNMERGED', 'A loop cannot reset an unmerged isolated parallel region', { loop_id: definition.id, node_id: id });
  const snapshot = { round: loop.round, lineage: structuredClone(loop.lineage), status: loop.status, feedback: structuredClone(loop.feedback), all_accepted: loop.all_accepted, items: structuredClone(loop.items), review_indices: [...loop.review_indices], repair_indices: [...loop.repair_indices], ledger: structuredClone(loop.ledger), observations: structuredClone(observations ?? null), parallel,
    nodes: Object.fromEntries(definition.node_ids.map(id => [id, { status: state.nodes[id].status, output: structuredClone(state.nodes[id].output), error: structuredClone(state.nodes[id].error), active_attempt_id: state.nodes[id].active_attempt_id, attempt_ids: state.nodes[id].attempts.map(attempt => attempt.id) }])),
    edges: Object.fromEntries(workflow.edges.filter(edge => members.has(edge.source) && members.has(edge.target)).map(edge => [edge.id, state.edges[edge.id]])) };
  loop.rounds.push(snapshot);
}
function releaseEdges(state, graph, definition, status) {
  const selectedLabel=graph.nodes.get(definition.exit_node).type==='condition'?state.nodes[definition.exit_node].output?.selected_label:undefined;
  for (const edge of graph.out.get(definition.exit_node).filter(edge => !definition.node_ids.includes(edge.target))) {
    const containing = loopBoundary(graph.workflow, definition.exit_node).filter(loop => !loop.node_ids.includes(edge.target));
    if (status === 'succeeded' && containing.some(loop => state.loops[loop.id].status !== 'accepted')) { state.edges[edge.id] = 'pending'; continue; }
    state.edges[edge.id] = status === 'succeeded' && ['success', 'always'].includes(edge.on ?? 'success') && (selectedLabel===undefined||edge.label===selectedLabel) ? 'selected' : 'skipped';
  }
}
function resetRegion(state, workflow, definition) {
  const members = new Set(definition.node_ids);
  for (const id of definition.node_ids) {
    const node = state.nodes[id];
    requireValue(!['claimed', 'running', 'interrupted'].includes(node.status), 'LOOP_REGION_BUSY', 'Loop reset cannot discard active or unresolved node ownership', { node_id: id });
    node.status = 'pending'; node.active_attempt_id = null; node.output = null; node.error = null; node.failure_handled = false; node.approval_id = null;
  }
  for (const edge of workflow.edges) if (members.has(edge.source)) state.edges[edge.id] = 'pending';
  for (const id of Object.keys(state.parallel ?? {})) if (members.has(id)) delete state.parallel[id];
  for (const nested of definitions(workflow).filter(loop => loop.id !== definition.id && loop.node_ids.every(id => members.has(id)))) {
    const previous = state.loops[nested.id]; Object.assign(previous, emptyIteration()); // Histories retain their original outer lineage.
  }
}
function settleItems(state, definition, context, observations) {
  const loop = state.loops[definition.id], before = observations?.before?.[definition.id], after = observations?.after?.[definition.id];
  requireValue(before && after && before.round === loop.round && after.round === loop.round && canonicalJSON(before.lineage) === canonicalJSON(loop.lineage) && canonicalJSON(after.lineage) === canonicalJSON(loop.lineage) && before.items.length === loop.items.length && after.items.length === loop.items.length && canonicalJSON(before.review_indices) === canonicalJSON(loop.review_indices) && canonicalJSON(after.items) === canonicalJSON(loop.observed_revisions), 'LOOP_OBSERVATION_MISSING', 'Loop item acceptance requires exact Host observations before and after the review', { loop_id: definition.id });
  const verdicts = verdictsFor(state, definition, context);
  invalidateAcceptedItems(loop,after.items);
  for (let position = 0; position < loop.review_indices.length; position++) {
    const index = loop.review_indices[position], verdict = verdicts[position], old = before.items[index], current = after.items[index];
    const stable = !old.missing && !current.missing && old.revision === current.revision;
    const missing = current.files.filter(file => file.missing).map(file => file.path);
    const findings = missing.length ? { semantic: structuredClone(verdict.findings ?? null), host: { code: 'LOOP_ARTIFACT_MISSING', message: 'Required artifact or dependency files are missing', paths: missing } } : structuredClone(verdict.findings ?? null);
    loop.ledger[index] = { status: !verdict.accepted || missing.length ? 'failed' : stable ? 'accepted' : 'invalidated', findings, revision: verdict.accepted && stable ? current.revision : null };
  }
  loop.observed_revisions = structuredClone(after.items); loop.all_accepted = loop.ledger.every(item => item.status === 'accepted');
}

export function settleLoops(state, workflow, graph, context) {
  if (!definitions(workflow).length) return false;
  context ??= contextOf(state);
  initializeLoops(state, workflow); graph ??= loopGraph(workflow); graph.workflow ??= workflow; let changed = false;
  for (const definition of [...definitions(workflow)].sort((a, b) => a.node_ids.length - b.node_ids.length)) {
    const loop = state.loops[definition.id];
    if (loop.status === 'pending' && definition.node_ids.every(id => state.nodes[id].status === 'skipped')) { loop.status = 'skipped'; releaseEdges(state, graph, definition, 'skipped'); changed = true; continue; }
    if (loop.status === 'running' && state.nodes[definition.exit_node].status === 'skipped' && definition.node_ids.every(id => finished.has(state.nodes[id].status))) {
      loop.status = 'skipped'; recordRound(state, workflow, definition, loop); releaseEdges(state, graph, definition, 'skipped'); changed = true; continue;
    }
    if (loop.status !== 'running' || state.nodes[definition.exit_node].status !== 'succeeded' || definition.node_ids.some(id => !finished.has(state.nodes[id].status))) continue;
    if (definitions(workflow).some(nested => nested.id !== definition.id && nested.node_ids.every(id => definition.node_ids.includes(id)) && !['accepted', 'skipped'].includes(state.loops[nested.id].status))) continue;
    refreshContext(state, context);
    const exit = state.nodes[definition.exit_node], attempt = exit.attempts.find(item => item.id === exit.active_attempt_id);
    const observations = attempt?.loop_observation;
    if (definition.item_scope) settleItems(state, definition, context, observations);
    loop.feedback = definition.feedback_bindings ? structuredClone(resolveBindings(definition.feedback_bindings, context)) : {};
    refreshContext(state, context);
    const accepted = evaluateExpression(definition.until, context) && (!definition.item_scope || loop.all_accepted);
    loop.status = accepted ? 'accepted' : loop.round >= definition.max_rounds ? 'exhausted' : 'rejected';
    recordRound(state, workflow, definition, loop, observations); changed = true;
    if (accepted) { releaseEdges(state, graph, definition, 'succeeded'); continue; }
    if (loop.status === 'exhausted') {
      state.status = 'failed'; state.error = { code: 'LOOP_EXHAUSTED', loop_id: definition.id, node_id: definition.exit_node, round: loop.round, max_rounds: definition.max_rounds, message: `Loop ${definition.id} exhausted ${definition.max_rounds} review rounds without acceptance` };
      for (const edge of graph.out.get(definition.exit_node).filter(edge => !definition.node_ids.includes(edge.target))) state.edges[edge.id] = 'pending';
      continue;
    }
    resetRegion(state, workflow, definition); loop.round++; loop.status = 'running';
    for (const id of definition.node_ids) state.nodes[id].current_loop_rounds = loopRoundSignature(state, workflow, id);
    if (definition.item_scope) { loop.review_indices = loop.ledger.flatMap((item, index) => item.status === 'accepted' ? [] : [index]); loop.repair_indices = loop.ledger.flatMap((item, index) => item.status === 'failed' ? [index] : []); projectItems(loop); }
  }
  refreshContext(state, context); return changed;
}

/** Exact Host-owned locations let cleanup update archives without searching arbitrary data. */
export function loopParallelArchives(state) {
  return Object.entries(state.loops ?? {}).flatMap(([id, loop]) => (loop.rounds ?? []).map((round, index) => ({ path: ['loops', id, 'rounds', index, 'parallel'], parallel: round.parallel })).filter(entry => entry.parallel && Object.keys(entry.parallel).length));
}
