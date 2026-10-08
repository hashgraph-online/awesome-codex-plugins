import { randomBytes } from 'node:crypto';
import { requireValue, noSymlinks, workflowId } from './workflow-paths.mjs';
import { digest, canonicalJSON } from './workflow-revisions.mjs';
import { leaseToken, executionEnvelope, approvalBinding } from './workflow-execution-envelope.mjs';
import { childIdentity } from './workflow-subworkflow.mjs';
import { interruptActiveNodes, graphInfo } from './workflow-state.mjs';
import { revalidateBoundSourceLocations } from './workspace-source-locations.mjs';

const terminal = new Set(['succeeded', 'failed', 'cancelled']);
function rotateAttempt(state, nodeId, attempt, controlToken) {
  const generation = (attempt.lease_generation ?? 0) + 1;
  requireValue(Number.isSafeInteger(generation), 'LEASE_GENERATION_LIMIT', 'Lease generation exceeded its limit');
  attempt.lease_generation = generation;
  const token = leaseToken(controlToken, state.run_id, nodeId, attempt.id, generation); attempt.lease_hash = digest(token); return token;
}

const CONTROL_RECOVERY_FIELDS = ['run_id', 'expected_sequence', 'main_actor', 'reason', 'authorization'];
const USER_MESSAGE_AUTHORIZATION_FIELDS = ['confirmed', 'source', 'statement'];
function exactObject(value, fields) {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value)
    && Object.keys(value).length === fields.length && fields.every(field => Object.hasOwn(value, field));
}

export function conversationControlRecoveryRequest(args) {
  requireValue(exactObject(args, CONTROL_RECOVERY_FIELDS), 'CONTROL_RECOVERY_SCHEMA', 'Conversational recovery needs only the exact Run, observed sequence, main actor, reason and user authorization');
  const { run_id, expected_sequence, main_actor, reason, authorization } = args;
  workflowId(run_id);
  requireValue(Number.isSafeInteger(expected_sequence) && expected_sequence > 0 && typeof reason === 'string' && reason.trim() && reason.length <= 2000 && typeof main_actor === 'string' && main_actor.trim() && main_actor.length <= 256,
    'CONTROL_RECOVERY_SCHEMA', 'Conversational recovery needs the observed sequence, a reason and one main actor');
  requireValue(exactObject(authorization, USER_MESSAGE_AUTHORIZATION_FIELDS) && authorization.confirmed === true && authorization.source === 'user_message' && typeof authorization.statement === 'string' && authorization.statement.trim() && authorization.statement.length <= 2000,
    'CONTROL_RECOVERY_AUTHORIZATION', 'Conversational recovery requires an explicit bounded user-message authorization attestation');
  return { run_id, expected_sequence, main_actor, reason, authorization: { confirmed: true, source: 'user_message', statement: authorization.statement },
    recovery: { channel: 'conversation_mcp', authorization_source: 'user_message', authorization_statement: authorization.statement } };
}

function recoveryAudit(recovery) {
  if (recovery === undefined) return {};
  requireValue(exactObject(recovery, ['channel', 'authorization_source', 'authorization_statement']) && recovery.channel === 'conversation_mcp' && recovery.authorization_source === 'user_message' && typeof recovery.authorization_statement === 'string' && recovery.authorization_statement.trim() && recovery.authorization_statement.length <= 2000,
    'CONTROL_RECOVERY_SCHEMA', 'Conversational recovery audit data is invalid');
  return recovery;
}

// Called only after authenticated human-console adoption or validated host-attested
// user-message recovery. The root CAS and ancestor fence precede all descendant
// writes. A partial recovery stays paused; repeating it repairs its exact tree.
export async function adoptRunTree(runtime, runId, { expected_sequence, reason, main_actor, recovery }, onFenced = () => {}) {
  requireValue(Number.isSafeInteger(expected_sequence) && expected_sequence > 0 && typeof reason === 'string' && reason.trim() && reason.length <= 2000 && typeof main_actor === 'string' && main_actor.trim() && main_actor.length <= 256,
    'CONTROL_RECOVERY_SCHEMA', 'Control recovery needs the observed sequence, a reason and one main actor');
  const audit = recoveryAudit(recovery);
  const authorities = new Map(); const errors = []; const seen = new Set();
  async function visit(id, controlToken, parent = null, depth = 0) {
    requireValue(depth <= 32 && seen.size < 4096 && !seen.has(id), 'CONTROL_RECOVERY_TREE', 'Invalid or oversized recovery ancestry'); seen.add(id);
    const record = await runtime.runs.recover(id, (state, pins, current) => {
      if (!parent) { requireValue(!pins.parent, 'CONTROL_RECOVERY_ROOT', 'Adopt the top-level Run so child authority remains attached to its parent', { parent_run_id: pins.parent?.run_id }); requireValue(current.sequence === expected_sequence, 'RUN_SEQUENCE_CONFLICT', 'Run changed since recovery was requested'); }
      else requireValue(pins.parent?.run_id === parent.run_id && pins.parent.node_id === parent.node_id && pins.parent.attempt_id === parent.attempt_id && pins.parent.pins_hash === parent.pins_hash, 'CHILD_RUN_CONFLICT', 'Recovered child ancestry differs from the exact parent dispatch');
      onFenced(id, state);
      interruptActiveNodes(state, 'Human controller recovery fenced the previous executor');
      if (!terminal.has(state.status)) { state.status = 'paused'; state.pause_reason = reason; }
      state.control_hash = digest(controlToken); state.main_actor = main_actor;
      for (const [nodeId, node] of Object.entries(state.nodes)) for (const attempt of node.attempts) rotateAttempt(state, nodeId, attempt, controlToken);
      state.control_recovery = { actor: 'user', root_run_id: runId, reason, previous_sequence: current.sequence, generation: (state.control_recovery?.generation ?? 0) + 1, ...audit, at: new Date().toISOString() };
      state.updated_at = state.control_recovery.at;
    });
    authorities.set(id, { control_token: controlToken, state: record.state });
    for (const [nodeId, node] of Object.entries(record.state.nodes)) for (const attempt of node.attempts) if (attempt.child_run_id) {
      try {
        const child = childIdentity(id, nodeId, attempt.id, controlToken);
        requireValue(child.run_id === attempt.child_run_id, 'CHILD_RUN_CONFLICT', 'Recorded child ID differs from the exact parent attempt');
        try { await noSymlinks(runtime.runs.directory(child.run_id)); }
        catch (error) { if (error.code === 'ENOENT' && error.path === runtime.runs.directory(child.run_id)) continue; throw error; }
        await visit(child.run_id, child.control_token, { run_id: id, node_id: nodeId, attempt_id: attempt.id, pins_hash: record.state.pins_hash }, depth + 1);
      } catch (error) { errors.push({ run_id: attempt.child_run_id, code: error.code ?? 'CONTROL_RECOVERY_FAILED', message: error.message }); }
    }
  }
  const controlToken = randomBytes(32).toString('hex'); await visit(runId, controlToken);
  return { run: { ...await runtime.get(runId), control_token: controlToken }, authorities, errors };
}

export async function controllerAttempt(runtime, runId, { control_token, node_id, attempt_id }) {
  await runtime.authorizeController(runId, { control_token }); const record = await runtime.runs.read(runId);
  const definition = record.pins.root.workflow.nodes.find(node => node.id === node_id); const node = record.state.nodes[node_id];
  const attempt = node?.attempts.find(item => item.id === attempt_id);
  requireValue(definition && attempt && node.active_attempt_id === attempt_id, 'RECOVERY_ATTEMPT', 'Recovery requires the exact current attempt');
  return { ...record, definition, node, attempt };
}

// observation is supplied by the trusted executor after exact remote/pinned
// artifact inspection, never from a JSON capability flag in the public API.
export async function reattachAttempt(runtime, runId, args, observation) {
  const before = await controllerAttempt(runtime, runId, args);
  requireValue(before.node.status === 'interrupted' && before.attempt.status === 'interrupted', 'RECOVERY_ATTEMPT_STATE', 'Only an interrupted existing attempt can be reattached');
  const result = await runtime.transition(runId, 'reattach', async (state, pins) => {
    const node = state.nodes[args.node_id]; const attempt = node.attempts.find(item => item.id === args.attempt_id);
    requireValue(state.control_hash === before.state.control_hash && node.status === 'interrupted' && attempt?.status === 'interrupted' && node.active_attempt_id === attempt.id, 'RECOVERY_ATTEMPT_CHANGED', 'Attempt or controller changed during reconciliation');
    requireValue(['interrupted','paused','running','blocked'].includes(state.status), 'RUN_TERMINAL', 'Terminal Runs cannot reconnect executors');
    requireValue(canonicalJSON(attempt.dispatch) === canonicalJSON(before.attempt.dispatch), 'DISPATCH_CONFLICT', 'Dispatch identity changed during reconciliation');
    const definition = pins.root.workflow.nodes.find(item => item.id === args.node_id); const graph = graphInfo(pins.root.workflow);
    for (const id of graph.visit(args.node_id)) if (id !== args.node_id) requireValue(!['claimed','running','succeeded','failed'].includes(state.nodes[id].status), 'RECOVERY_DOWNSTREAM_STARTED', 'Downstream execution prevents reattachment');
    const approval = approvalBinding(definition, state, pins, node.attempts.indexOf(attempt) + 1);
    if (approval.required) requireValue(state.approvals[node.approval_id]?.status === 'approved' && state.approvals[node.approval_id].binding_hash === approval.hash, 'APPROVAL_REQUIRED', 'The exact pinned approval must still hold');
    requireValue(observation && typeof observation.kind === 'string' && Buffer.byteLength(canonicalJSON(observation)) <= 64000, 'RECOVERY_EVIDENCE', 'Reattachment needs bounded observed identity evidence');
    if (observation.kind === 'unsubmitted_claim') {
      requireValue(!attempt.dispatch && !attempt.host_tool, 'DISPATCH_UNCERTAIN', 'An existing dispatch cannot be recovered as unsubmitted');
      // No work was admitted, so the original source-location preflight still applies.
      await revalidateBoundSourceLocations(definition, state, pins);
    }
    else requireValue(attempt.dispatch && observation.dispatch_request_id === attempt.dispatch.request_id && observation.attempt_id === attempt.id, 'RECOVERY_IDENTITY', 'Evidence must match the existing dispatch');
    if (observation.receipt) {
      requireValue(!attempt.dispatch.receipt || canonicalJSON(attempt.dispatch.receipt) === canonicalJSON(observation.receipt), 'DISPATCH_CONFLICT', 'Remote receipt differs from the recorded identity');
      attempt.dispatch.receipt = structuredClone(observation.receipt); attempt.dispatch.phase = 'acknowledged'; attempt.dispatch.cancellation_pending = false;
    }
    const token = rotateAttempt(state, args.node_id, attempt, args.control_token);
    const previousOwner = attempt.owner;
    delete attempt.finished_at;
    if (definition.executor?.kind === 'main') attempt.owner = state.main_actor;
    attempt.status = attempt.dispatch ? 'running' : 'claimed'; attempt.reconciliation = { ...observation, previous_owner: previousOwner, owner: attempt.owner, at: new Date().toISOString(), resubmitted: false };
    node.status = attempt.status; node.error = null; state.updated_at = new Date().toISOString();
    return executionEnvelope(definition, state, pins, attempt, token);
  }, { expected_sequence: before.sequence }, { allowPaused: true });
  return { envelope: result.result, state: await runtime.get(runId), reattached: true, resubmitted: false, retry_charged: false };
}
