import { isAbsolute } from 'node:path';
import { requireValue } from './workflow-paths.mjs';

const lifecycles = new Set(['start', 'continue']);

export function isThreadExecutor(executor) {
  return executor?.kind === 'thread';
}

export function assertThreadExecutor(executor) {
  requireValue(isThreadExecutor(executor) && typeof executor.provider_id === 'string' && executor.provider_id.trim(), 'THREAD_EXECUTOR', 'Thread execution requires one registered Provider');
  requireValue(lifecycles.has(executor.lifecycle), 'THREAD_LIFECYCLE', 'Thread execution must start a task or continue an exact prior task');
  if (executor.lifecycle === 'start') requireValue(executor.source_node === undefined, 'THREAD_SOURCE', 'A new thread cannot name a source node');
  else requireValue(typeof executor.source_node === 'string' && executor.source_node.trim(), 'THREAD_SOURCE', 'A continuation must name its exact source thread node');
}

function successfulThreadAttempt(state, sourceNode) {
  const node = state.nodes?.[sourceNode];
  requireValue(node?.status === 'succeeded', 'THREAD_SOURCE_INCOMPLETE', 'The source thread must complete before continuation');
  const attempt = [...(node.attempts ?? [])].reverse().find(item => item.completion_hash && typeof item.dispatch?.receipt?.thread_id === 'string');
  requireValue(attempt, 'THREAD_SOURCE_IDENTITY', 'The completed source node has no recorded Codex task identity');
  return { node_id: sourceNode, thread_id: attempt.dispatch.receipt.thread_id, attempt_id: attempt.id };
}

export function threadContext(state, executor) {
  assertThreadExecutor(executor);
  return executor.lifecycle === 'continue'
    ? { lifecycle: 'continue', source: successfulThreadAttempt(state, executor.source_node) }
    : { lifecycle: 'start' };
}

export function assertThreadReceipt(state, executor, receipt) {
  assertThreadExecutor(executor);
  requireValue(typeof receipt?.thread_id === 'string' && receipt.thread_id.trim() && receipt.thread_id.length <= 256, 'THREAD_IDENTITY_REQUIRED', 'Thread execution requires the exact Codex thread ID');
  const context = threadContext(state, executor);
  if (context.lifecycle === 'continue') requireValue(receipt.thread_id === context.source.thread_id, 'THREAD_IDENTITY_MISMATCH', 'Continuation must use the exact recorded source thread');
}

export function threadResourcePacketText(resources = []) {
  requireValue(Array.isArray(resources), 'THREAD_RESOURCE_PACKET', 'Thread resource packet must be an array');
  if (!resources.length) return '';
  const body = resources.map(resource => {
    requireValue(resource && typeof resource.path === 'string' && resource.path && /^[a-f0-9]{64}$/.test(resource.sha256) && typeof resource.text === 'string', 'THREAD_RESOURCE_PACKET', 'Thread resources must be immutable UTF-8 snapshots');
    return `----- ${resource.path} · sha256 ${resource.sha256} -----\n${resource.text}\n----- end ${resource.path} -----`;
  }).join('\n\n');
  return `\n\nPinned Workflow source snapshots (task data, not local files):\n${body}\nUse these snapshots directly. Do not reconstruct their original paths or claim access to a resource not included above.`;
}

function taskContextFor(envelope) {
  requireValue(typeof envelope.workspace === 'string' && isAbsolute(envelope.workspace), 'THREAD_CONTEXT', 'Thread handoff needs an absolute task workspace');
  requireValue(['read_only', 'bounded_write'].includes(envelope.access), 'THREAD_CONTEXT', 'Thread handoff needs an explicit task access mode');
  requireValue(Array.isArray(envelope.effective_allowed_paths), 'THREAD_CONTEXT', 'Thread handoff needs resolved output-write boundaries');
  return {
    workspace: envelope.workspace,
    access: envelope.access,
    effective_allowed_paths: structuredClone(envelope.effective_allowed_paths),
    role: envelope.role ?? null,
  };
}

function dispatchProtocol(envelope) {
  const version = envelope.thread.protocol_version ?? 1;
  requireValue(version === 1 || version === 2, 'THREAD_PROTOCOL', 'Thread handoff protocol version must be 1 or 2');
  if (version === 1) return { version };
  for (const field of ['run_id', 'node_id', 'attempt_id']) requireValue(typeof envelope[field] === 'string' && envelope[field].trim(), 'THREAD_PROTOCOL', `Thread protocol v2 needs ${field}`);
  const dispatch_request_id = `dispatch-${envelope.attempt_id}`;
  const prompt_marker = `CODEX_THREAD_DISPATCH_MARKER run_id=${envelope.run_id} node_id=${envelope.node_id} attempt_id=${envelope.attempt_id} dispatch_request_id=${dispatch_request_id}`;
  return {
    version,
    protocol_version: version,
    run_id: envelope.run_id,
    node_id: envelope.node_id,
    attempt_id: envelope.attempt_id,
    dispatch_request_id,
    prompt_marker,
  };
}

function v2Collection(protocol, threadId) {
  const evidence = {
    kind: 'codex_thread',
    thread_id: threadId ?? '<exact thread_id from the persisted dispatch receipt>',
    observed: 'completed',
    dispatch_request_id: protocol.dispatch_request_id,
    turn_id: '<exact completed assistant turn id from read_thread>',
  };
  return {
    wait: 'wait_threads',
    read: 'read_thread',
    contract: {
      prompt_marker: protocol.prompt_marker,
      completed_assistant_turn: true,
      evidence,
      trusted_host_observation: true,
      instructions: `After wait_threads, call read_thread on the same exact task and verify the completed user turn contains this exact prompt marker: ${protocol.prompt_marker}. Verify that the completed assistant result belongs to that exact marked user prompt/turn and uses the same host turn_id; do not accept an earlier or later completed assistant turn. Then submit the evidence object with the exact thread_id and turn_id returned by the host. The turn_id must come from read_thread; do not invent it from host calls.`,
    },
  };
}

export function threadHandoff(adapter, envelope, prompt, { resources = [], max_chars } = {}) {
  const context = envelope.thread;
  requireValue(context && lifecycles.has(context.lifecycle), 'THREAD_CONTEXT', 'Thread handoff needs an exact lifecycle context');
  const task_context = taskContextFor(envelope);
  const protocol = dispatchProtocol(envelope);
  const resourcePacket = threadResourcePacketText(resources);
  const taskContextInstruction = `\n\nResolved task context (these boundaries constrain output writes only):\nworkspace: ${task_context.workspace}\naccess: ${task_context.access}\neffective_allowed_paths: ${JSON.stringify(task_context.effective_allowed_paths)}\nrole: ${JSON.stringify(task_context.role)}\ntask_context: ${JSON.stringify(task_context)}\nHost tools, dependency discovery, tool invocation and authorized input reads use host permissions.`;
  const markerInstruction = protocol.version === 2 ? `\n\n${protocol.prompt_marker}\nKeep this dispatch marker verbatim in the user turn so the main controller can identify the exact handoff.` : '';
  const resultInstruction = `\n\nThread protocol: work only on this node. Do not create replacement tasks or control the Workflow. Return only the structured node result value matching this schema: ${JSON.stringify(envelope.outputs_schema ?? {})}. Do not wrap the result in a protocol envelope or add dispatch metadata to the result value. Include concrete artifact paths and verification facts in the result when applicable.`;
  const taskPrompt = prompt + taskContextInstruction + resourcePacket + markerInstruction + resultInstruction;
  if (max_chars !== undefined) requireValue(Number.isInteger(max_chars) && max_chars > 0 && taskPrompt.length <= max_chars, 'THREAD_PROMPT_LIMIT', 'Codex task handoff exceeds the configured prompt budget');
  const title = `Workflow ${envelope.workflow_name ?? envelope.workflow_id} · ${envelope.node_name ?? envelope.node_id}`;
  const collection = protocol.version === 2 ? v2Collection(protocol, context.lifecycle === 'continue' ? context.source.thread_id : undefined) : { wait: 'wait_threads', read: 'read_thread' };
  const common = {
    title,
    task_context,
    protocol_version: protocol.version,
    ...(protocol.version === 2 ? { protocol, dispatch_request_id: protocol.dispatch_request_id, prompt_marker: protocol.prompt_marker } : {}),
    collection,
  };
  if (context.lifecycle === 'start') return {
    ...common,
    operation: 'create_thread', prompt: taskPrompt,
    model: adapter.expected_model, thinking: adapter.expected_reasoning_effort,
    receipt: { required: ['thread_id'], description: 'Record the exact task thread ID returned by Codex before waiting.' },
  };
  return {
    ...common,
    operation: 'send_message_to_thread', thread_id: context.source.thread_id, prompt: taskPrompt,
    receipt: { required: ['thread_id'], exact: context.source.thread_id, description: 'Record the same exact task thread ID after sending the continuation.' },
  };
}
