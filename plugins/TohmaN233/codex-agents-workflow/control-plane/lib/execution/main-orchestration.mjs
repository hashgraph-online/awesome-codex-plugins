import { readFile } from 'node:fs/promises';
import { join } from 'node:path';
import { requireValue } from '../workflow-paths.mjs';
import { canonicalJSON, digest } from '../workflow-revisions.mjs';
import { validateData } from '../workflow-data-schema.mjs';
import { leaseToken } from '../workflow-execution-envelope.mjs';
import { isOrchestrationMain } from './main-execution-mode.mjs';
import { semanticResultSchema, hostResultProposalEnvelope } from './host-main-automation.mjs';
import { materializeNativeTaskBundle } from './node-input-materials.mjs';
import { snapshotWorkspace, changedWorkspacePaths } from './workspace-snapshot.mjs';
import { semanticTurnsConsumed } from './completion-turn-budget.mjs';
import { preflightSemanticOutput } from './completion-preflight.mjs';
import { rejectWorkspaceScope } from './workspace-scope-evidence.mjs';

const within = (path, boundary) => {
  const normalize = value => process.platform === 'win32' ? value.toLowerCase() : value;
  path = normalize(path); boundary = normalize(boundary.replace(/\/$/, ''));
  return boundary === '.' || path === boundary || path.startsWith(boundary + '/');
};

async function activeOrchestration(runtime, runId, controlToken, threadId) {
  await runtime.authorizeController(runId, { control_token: controlToken });
  const record = await runtime.runs.read(runId);
  requireValue(record.state.status === 'running' && record.state.constraints?.native_parent_thread_id === threadId,
    'MAIN_ORCHESTRATION_CONTEXT', 'Orchestration runs in the exact initiating conversation');
  const active = record.pins.root.workflow.nodes.filter(definition => isOrchestrationMain(definition)
    && ['claimed', 'running'].includes(record.state.nodes[definition.id]?.status));
  requireValue(active.length === 1, 'MAIN_ORCHESTRATION_NODE', 'No unique active orchestration node is awaiting this conversation');
  const definition = active[0], node = record.state.nodes[definition.id];
  const attempt = node.attempts.find(item => item.id === node.active_attempt_id);
  requireValue(attempt, 'ATTEMPT_MISSING', 'The active orchestration node lost its exact attempt');
  const binding = { run_id: runId, node_id: definition.id, attempt_id: attempt.id, control_token: controlToken,
    lease_token: leaseToken(controlToken, runId, definition.id, attempt.id, attempt.lease_generation ?? 0) };
  const envelope = await runtime.execution(runId, binding);
  const event = (kind, metadata) => runtime.recordExecutorEvent(runId, { ...binding, event: { kind, metadata } });
  const snapshot = () => snapshotWorkspace(envelope.workspace, { access: envelope.access,
    allowedPaths: envelope.effective_allowed_paths, requiredPaths: (definition.required_artifacts ?? []).map(item => item.path),
    onUnreadable: metadata => event('workspace_unreadable_authorized_path', { ...metadata, phase: 'orchestration' }) });
  return { record, definition, attempt, binding, envelope, event, snapshot };
}

/** The Host owns mechanics; the foreground Agent keeps its existing conversation. */
export async function prepareMainOrchestration(runtime, { run_id, control_token, thread_id }) {
  const { record, definition, attempt, binding, envelope, snapshot } = await activeOrchestration(runtime, run_id, control_token, thread_id);
  const schema = semanticResultSchema(definition);
  let receipt = attempt.dispatch?.receipt;
  if (!receipt) {
    const resources = [];
    for (const path of envelope.resources ?? []) {
      const pin = record.pins.root.resources.find(item => item.path === path);
      requireValue(pin, 'MAIN_ORCHESTRATION_RESOURCE', `Missing pinned resource: ${path}`);
      resources.push({ path, sha256: pin.sha256, size: pin.bytes, bytes: await readFile(join(runtime.runs.directory(run_id), 'objects', pin.sha256)) });
    }
    const bundle = await materializeNativeTaskBundle({ directory: join(envelope.workspace, 'work', '.workflow-runtime', 'orchestration', run_id, attempt.id),
      envelope, resources, resultSchema: schema, allowedPaths: envelope.effective_allowed_paths });
    const before = await snapshot();
    const reference = await runtime.runs.saveArtifact(run_id, `orchestration-before-${attempt.id}`,
      Buffer.from(canonicalJSON({ files: [...before], unreadable: [...before.unreadablePaths] })));
    receipt = { executor: 'codex-current-main-orchestration', thread_id, main_actor: record.state.main_actor,
      session_id: `logical-main-${run_id}`, call_chain_id: `workflow-run-${run_id}`,
      task_bundle_path: bundle.task_bundle_path, task_bundle_sha256: bundle.task_bundle_sha256, before_snapshot: reference };
    await runtime.recordHostMainDispatchReceipt(run_id, { ...binding, request_id: `dispatch-${attempt.id}`, receipt });
  }
  requireValue(receipt.executor === 'codex-current-main-orchestration' && receipt.thread_id === thread_id,
    'MAIN_ORCHESTRATION_IDENTITY', 'The orchestration receipt belongs to another execution mode or conversation');
  requireValue(digest(await readFile(receipt.task_bundle_path)) === receipt.task_bundle_sha256,
    'MAIN_ORCHESTRATION_BUNDLE', 'The Host task bundle changed after dispatch');
  return { status: 'orchestration_handoff', main_mode: 'orchestration', context: 'current_conversation',
    workspace: envelope.workspace, access: envelope.access, allowed_paths: envelope.effective_allowed_paths,
    task_bundle_path: receipt.task_bundle_path, response_schema: schema,
    completion_tool: 'workflow_orchestration_complete',
    instruction: 'Execute this node in the current conversation using its existing task context and the local task bundle. Submit only newly authored semantic output to workflow_orchestration_complete.' };
}

export async function completeMainOrchestration(runtime, { run_id, control_token, thread_id, output }) {
  const { record, definition, attempt, binding, envelope, event, snapshot } = await activeOrchestration(runtime, run_id, control_token, thread_id);
  const receipt = attempt.dispatch?.receipt;
  requireValue(receipt?.executor === 'codex-current-main-orchestration' && receipt.thread_id === thread_id,
    'MAIN_ORCHESTRATION_IDENTITY', 'This conversation has no dispatched orchestration task');
  await runtime.reserveHostMainTurn(run_id, binding);
  try {
    validateData(output, semanticResultSchema(definition));
    await preflightSemanticOutput(definition, output, envelope.workspace, record);
    const savedBefore = JSON.parse((await runtime.runs.readArtifact(run_id, receipt.before_snapshot)).toString('utf8'));
    const before = new Map(savedBefore.files); before.unreadablePaths = new Map(savedBefore.unreadable);
    const after = await snapshot(), changed = changedWorkspacePaths(before, after);
    const outside = envelope.access === 'read_only' ? changed : changed.filter(path => !envelope.effective_allowed_paths.some(boundary => within(path, boundary)));
    if (outside.length) await rejectWorkspaceScope({ runtime, runId: run_id, attemptId: attempt.id,
      code: 'MAIN_ORCHESTRATION_SCOPE_VIOLATION', changed, outside, before, after, event });
    const pathKey = value => process.platform === 'win32' ? value.toLowerCase() : value;
    const changedKeys = new Set(changed.map(pathKey)), afterKeys = new Set([...after.keys()].map(pathKey));
    const missing = (definition.required_artifacts ?? []).filter(item => !changedKeys.has(pathKey(item.path)) || !afterKeys.has(pathKey(item.path)));
    requireValue(!missing.length, 'REQUIRED_ARTIFACT_MISSING', `Produce the required output paths before completing: ${missing.map(item => item.path).join(', ')}`);
    if (record.pins.root.workflow.finalization?.node_id === definition.id && Object.hasOwn(definition.outputs_schema?.properties ?? {}, 'accepted')) requireValue(output.accepted === true, 'FINAL_ACCEPTANCE_REQUIRED', 'Correct the outstanding work before accepting the final result');
    const completion = hostResultProposalEnvelope(definition, { output, changed_paths: changed, artifacts: changed,
      evidence: [{ kind: 'current_main_orchestration', thread_id }] });
    const saved = await runtime.runs.saveExecutorResult(run_id, attempt.id, completion);
    await event('result_proposed', { ...saved, final_acceptance_required: false });
    await event('session_state', { status: 'closed' });
    await runtime.recordHostMainUsage(run_id, { ...binding, request_id: `dispatch-${attempt.id}`, usage: { unknown: true } });
    const final = record.pins.root.workflow.finalization?.node_id === definition.id;
    return await runtime.completeHostMainResult(run_id, binding,
      final && !Object.hasOwn(definition.outputs_schema?.properties ?? {}, 'accepted') ? { accepted: true } : {});
  } catch (error) {
    await event('completion_invalid', { diagnostic: String(error.message).slice(0,900), thread_id });
    const current = await runtime.runs.read(run_id);
    const exhausted = semanticTurnsConsumed(current.state.nodes[definition.id]) >= definition.retry.max_attempts;
    if (exhausted || error.code === 'MAIN_ORCHESTRATION_SCOPE_VIOLATION') {
      await event('session_state', {status:'closed'});
      await runtime.failNode(run_id, {...binding,error:{code:error.code ?? 'MAIN_ORCHESTRATION_FAILED',message:String(error.message).slice(0,2000)}});
    }
    throw error;
  }
}
