import { requireValue } from './workflow-paths.mjs';

// A continuation of a continuation still owns the original task's single turn lane.
export function threadLineage(nodes, nodeId) {
  const seen = new Set();
  while (!seen.has(nodeId)) {
    seen.add(nodeId);
    const executor = nodes.get(nodeId)?.executor;
    if (executor?.kind !== 'thread') return null;
    if (executor.lifecycle === 'start') return nodeId;
    nodeId = executor.source_node;
  }
  return null;
}

export function assertThreadDispatchAvailable(state, pins, nodeId, attemptId) {
  const nodes = new Map(pins.root.workflow.nodes.map(node => [node.id, node]));
  if (nodes.get(nodeId)?.executor?.kind !== 'thread') return;
  const lineage = threadLineage(nodes, nodeId);
  requireValue(lineage, 'THREAD_SOURCE', 'Task continuation has no valid start lineage');
  for (const [otherId, node] of Object.entries(state.nodes)) {
    if (threadLineage(nodes, otherId) !== lineage) continue;
    for (const attempt of node.attempts) {
      if (attempt.id === attemptId || !attempt.dispatch || attempt.completion_hash) continue;
      if (['not_started', 'terminated'].includes(attempt.reconciliation?.outcome)) continue;
      requireValue(false, 'THREAD_DISPATCH_BUSY', 'Another dispatch in this task lineage is unresolved; collect or reconcile its exact turn before sending another prompt', { node_id: otherId, attempt_id: attempt.id, dispatch_request_id: attempt.dispatch.request_id });
    }
  }
}

export function assertThreadStartIdentity(state, definition, attemptId, receipt) {
  if (definition.executor.lifecycle !== 'start') return;
  for (const node of Object.values(state.nodes)) for (const attempt of node.attempts) {
    requireValue(attempt.id === attemptId || attempt.dispatch?.receipt?.thread_id !== receipt.thread_id,
      'THREAD_IDENTITY_REUSED', 'A task start must record a new task identity, not another node or attempt\'s task');
  }
}

export function assertThreadCompletion(state, pins, attempt, payload) {
  const threadId = attempt.dispatch.receipt.thread_id;
  const observations = payload.evidence.filter(item => item?.kind === 'codex_thread' && item.thread_id === threadId && item.observed === 'completed');
  requireValue(observations.length, 'THREAD_COLLECTION_EVIDENCE', 'Codex task-thread completion requires evidence from the exact recorded task');
  if ((pins.thread_protocol_version ?? 1) < 2) return;
  const observation = observations.find(item => item.dispatch_request_id === attempt.dispatch.request_id && typeof item.turn_id === 'string' && item.turn_id.trim().length > 0 && item.turn_id.length <= 256);
  requireValue(observation, 'THREAD_TURN_EVIDENCE', 'Inspect the exact dispatch prompt and completed assistant turn; report its actual turn_id and this dispatch_request_id');
  // The host attests prompt/turn correlation. This local guard prevents reusing an
  // already collected turn; it cannot independently inspect host conversations.
  for (const node of Object.values(state.nodes)) for (const other of node.attempts) {
    if (other.id === attempt.id || !other.completion_hash) continue;
    requireValue(!other.completion.evidence.some(item => item?.kind === 'codex_thread' && item.thread_id === threadId && item.turn_id === observation.turn_id),
      'THREAD_TURN_REUSED', 'This task turn was already collected for another dispatch');
  }
}
