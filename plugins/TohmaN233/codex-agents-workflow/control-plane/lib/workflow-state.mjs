import { evaluateExpression, resolveBindings } from './workflow-bindings.mjs';
import { validateData } from './workflow-data-schema.mjs';
import { approvalBinding, bindingContext } from './workflow-execution-envelope.mjs';
import { requireValue } from './workflow-paths.mjs';
import { initialCostLedger } from './workflow-cost-ledger.mjs';
import { initializeLoops, prepareLoops, settleLoops, loopBoundary } from './workflow-loops.mjs';

export const FINISHED_NODES = new Set(['succeeded', 'failed', 'skipped', 'cancelled']);
export const EXECUTOR_NODES = new Set(['agent', 'skill_ref', 'tool', 'human_gate', 'subworkflow']);

export function graphInfo(workflow) {
  const nodes = new Map(workflow.nodes.map(node => [node.id, node]));
  const out = new Map(workflow.nodes.map(node => [node.id, []]));
  const incoming = new Map(workflow.nodes.map(node => [node.id, []]));
  for (const edge of workflow.edges) { out.get(edge.source).push(edge); incoming.get(edge.target).push(edge); }
  const visit = (start, stop) => {
    const seen = new Set(); const queue = [start];
    while (queue.length) { const id = queue.pop(); if (id === stop || seen.has(id)) continue; seen.add(id); for (const edge of out.get(id)) queue.push(edge.target); }
    return seen;
  };
  const degrees = new Map([...incoming].map(([id, edges]) => [id, edges.length]));
  const todo = [...nodes.keys()].filter(id => !degrees.get(id)).sort(); const order = [];
  while (todo.length) { const id = todo.shift(); order.push(id); for (const edge of out.get(id)) { degrees.set(edge.target, degrees.get(edge.target) - 1); if (!degrees.get(edge.target)) { todo.push(edge.target); todo.sort(); } } }
  requireValue(order.length === nodes.size, 'GRAPH_CYCLE', 'Pinned Workflow has a cycle');
  const regions = workflow.nodes.filter(node => node.type === 'parallel').map(node => ({ parallel: node, members: new Set(out.get(node.id).flatMap(edge => [...visit(edge.target, node.join_id)])) }));
  return { workflow, nodes, out, incoming, visit, order, regions };
}

export function initialRunState({ runId, pinsHash, pins, inputs, permissions, constraints, controlHash, mainActor, requireApproval }) {
  const now = new Date().toISOString();
  const state = {
    schema_version: 1, run_id: runId, workflow_id: pins.root.workflow.id, workflow_revision: pins.root.revision_hash,
    pins_hash: pinsHash, control_hash: controlHash, main_actor: mainActor, status: 'running',
    created_at: now, updated_at: now, inputs, permissions, constraints, require_approval: requireApproval,
    pause_reason: null, error: null, approvals: {}, output: null, main_session_identity: null,
    cost_ledger: initialCostLedger(constraints.cost_budget ?? null),
    parallel: {},
    nodes: Object.fromEntries(pins.root.workflow.nodes.map(node => [node.id, {
      status: 'pending', attempts: [], active_attempt_id: null, output: null, error: null,
      approval_id: null, approval_round: 0, failure_handled: false,
    }])),
    edges: Object.fromEntries(pins.root.workflow.edges.map(edge => [edge.id, 'pending'])),
  };
  initializeLoops(state, pins.root.workflow);
  return state;
}

export function setOutcome(state, graph, id, status, { selectedLabel } = {}) {
  const node = state.nodes[id]; node.status = status;
  const outgoing = graph.out.get(id);
  for (const edge of outgoing) {
    if (['succeeded','failed'].includes(status) && loopBoundary(graph.workflow, id).some(loop => !loop.node_ids.includes(edge.target) && state.loops?.[loop.id]?.status !== 'accepted')) {
      state.edges[edge.id] = 'pending'; continue;
    }
    const matches = status === 'succeeded'
      ? ['success', 'always'].includes(edge.on ?? 'success') && (selectedLabel === undefined || edge.label === selectedLabel)
      : status === 'failed' && ['failure', 'always'].includes(edge.on ?? 'success');
    state.edges[edge.id] = matches ? 'selected' : 'skipped';
  }
  if (status === 'failed') {
    node.failure_handled = outgoing.some(edge => state.edges[edge.id] === 'selected');
    // Explicit collect policy turns branch failure into data for main acceptance.
    const nearest = graph.regions.filter(region => region.members.has(id)).sort((a, b) => a.members.size - b.members.size)[0];
    if (nearest?.parallel.failure_policy === 'collect') node.failure_handled = true;
    if (!node.failure_handled) { state.status = 'failed'; state.error = { code: 'NODE_FAILED', node_id: id, message: node.error?.message ?? 'Node failed' }; }
  }
}

export function advanceRun(state, pins) {
  if (state.status !== 'running') return;
  const workflow = pins.root.workflow; const graph = graphInfo(workflow);
  const context = bindingContext(state);
  prepareLoops(state, workflow, context);
  settleLoops(state, workflow, graph, context);
  if (state.status !== 'running') { interruptActiveNodes(state, 'Repair loop stopped without acceptance'); return; }
  for (const id of graph.order) {
    prepareLoops(state, workflow, bindingContext(state));
    const definition = graph.nodes.get(id); const node = state.nodes[id];
    if (node.status !== 'pending') continue;
    const incoming = graph.incoming.get(id);
    if (incoming.some(edge => state.edges[edge.id] === 'pending')) continue;
    const joinActive = definition.type === 'join' && state.nodes[definition.parallel_id].status === 'succeeded';
    const active = definition.type === 'start' || joinActive || incoming.some(edge => state.edges[edge.id] === 'selected');
    if (!active) { setOutcome(state, graph, id, 'skipped'); continue; }
    if (EXECUTOR_NODES.has(definition.type)) {
      const approval = approvalBinding(definition, state, pins);
      if (approval.required || definition.type === 'human_gate') {
        let request = node.approval_id && state.approvals[node.approval_id];
        if (!request) {
          node.approval_round++;
          node.approval_id = `${id}:${node.approval_round}`;
          request = { id: node.approval_id, node_id: id, binding_hash: approval.hash, status: 'pending', decision: null };
          Object.defineProperty(state.approvals, request.id, { value: request, enumerable: true, writable: true, configurable: true });
        }
        if (request.status !== 'approved') { node.status = 'blocked'; continue; }
        requireValue(request.binding_hash === approval.hash, 'APPROVAL_BINDING_CHANGED', 'Approval no longer matches the exact execution scope');
      }
      node.status = 'ready';
      continue;
    }
    if (definition.type === 'condition') {
      try {
        const selected = definition.cases.find(entry => evaluateExpression(entry.when, bindingContext(state)))?.label ?? definition.default_label;
        node.output = { selected_label: selected };
        setOutcome(state, graph, id, 'succeeded', { selectedLabel: selected });
      } catch (error) {
        // Evaluation belongs to the same transaction as the upstream completion.
        // Keep that completion and persist the control failure instead of losing both.
        node.error = { code: error.code ?? 'CONDITION_FAILED', message: error.message };
        setOutcome(state, graph, id, 'failed');
        if (state.status === 'failed') { interruptActiveNodes(state, 'Condition evaluation failed'); return; }
      }
    } else if (definition.type === 'join') {
      const region = graph.regions.find(item => item.parallel.join_id === id);
      if (pins.parallel?.regions.some(item => item.id === region.parallel.id && item.isolated) && state.parallel?.[region.parallel.id]?.phase !== 'merged') {
        node.status = 'blocked'; continue;
      }
      const failures = [...region.members].filter(member => state.nodes[member].status === 'failed');
      node.output = { parallel_id: definition.parallel_id, failures, branch_results: Object.fromEntries(graph.out.get(definition.parallel_id).map(edge => [edge.label, { entry_node: edge.target }])) };
      setOutcome(state, graph, id, 'succeeded');
    } else {
      node.output = definition.type === 'start' ? state.inputs : {};
      setOutcome(state, graph, id, 'succeeded');
    }
  }
  // Control-only exits can finish during this pass. Reset/release a region
  // before exposing its downstream nodes; the next pass sees the new round.
  if (settleLoops(state, workflow, graph, bindingContext(state))) { advanceRun(state, pins); return; }
  const values = Object.values(state.nodes);
  if (values.every(node => FINISHED_NODES.has(node.status))) {
    const finalizer = state.nodes[workflow.finalization.node_id];
    const completedEnd = workflow.nodes.some(node => node.type === 'end' && state.nodes[node.id].status === 'succeeded');
    const loopsAccepted=(workflow.loops??[]).every(loop=>['accepted','skipped'].includes(state.loops?.[loop.id]?.status));
    if (finalizer.status === 'succeeded' && completedEnd && loopsAccepted && !values.some(node => node.status === 'failed' && !node.failure_handled)) {
      try {
        const output = workflow.output_bindings ? resolveBindings(workflow.output_bindings, bindingContext(state)) : finalizer.output;
        validateData(output, workflow.outputs_schema); state.output = output; state.status = 'succeeded';
      } catch (error) { state.status = 'failed'; state.error = { code: error.code ?? 'OUTPUT_FAILED', message: error.message }; }
    }
    else { state.status = 'failed'; state.error = { code: 'FINALIZATION_INCOMPLETE', message: 'No accepted successful path reached termination' }; }
  } else if (!values.some(node => ['ready', 'claimed', 'running'].includes(node.status)) && values.some(node => node.status === 'blocked')) state.status = 'blocked';
}

export function interruptActiveNodes(state, reason) {
  for (const node of Object.values(state.nodes)) if (['claimed', 'running'].includes(node.status)) {
    const attempt = node.attempts.find(item => item.id === node.active_attempt_id);
    attempt.status = 'interrupted'; attempt.finished_at = new Date().toISOString(); attempt.interruption = reason;
    node.status = 'interrupted'; node.error = { code: 'INTERRUPTED', message: reason };
  }
}
