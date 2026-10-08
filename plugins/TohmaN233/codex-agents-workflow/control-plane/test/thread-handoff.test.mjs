import test from 'node:test';
import assert from 'node:assert/strict';
import { resolve } from 'node:path';
import { executionEnvelope } from '../lib/workflow-execution-envelope.mjs';
import { threadHandoff } from '../lib/thread-handoff.mjs';
import { WorkflowExecutor } from '../lib/workflow-executor.mjs';

const workspace = resolve('thread-handoff-fixture');
const provider = {
  id: 'native-luna',
  name: 'Native Luna',
  kind: 'native_agent',
  enabled: true,
  capabilities: { read: true, write: true },
  requires_user_approval: false,
  config: { agent_type: 'default', model: 'gpt-6-luna', reasoning_effort: 'max', role: 'implementer' },
};
const adapter = { execution: 'codex_thread', expected_model: provider.config.model, expected_reasoning_effort: provider.config.reasoning_effort };

function handoffEnvelope(overrides = {}) {
  return {
    run_id: 'run-thread-fixture', workflow_id: 'fixture', workflow_name: 'Thread fixture', node_id: 'work', node_name: 'Work',
    attempt_id: 'attempt-thread-fixture', executor: { kind: 'thread', provider_id: provider.id }, provider,
    role: 'implementer', access: 'bounded_write', workspace, effective_allowed_paths: ['output'],
    inputs: {}, workflow_inputs: { task: 'Do the fixture task.' }, upstream_results: {}, prompt_template: 'Do the fixture task.',
    outputs_schema: { type: 'object', properties: { answer: { type: 'string' } }, required: ['answer'] },
    skill_policy: { mode: 'cooperative', implicit: 'allow', ambient_allow: [], shadowed_skill_paths: [] },
    thread: { lifecycle: 'start', protocol_version: 2 },
    ...overrides,
  };
}

function envelopeFor(node, overrides = {}) {
  const state = {
    run_id: 'run-envelope-fixture', workflow_id: 'fixture', workflow_revision: 1, inputs: { task: 'Fixture' }, constraints: {},
    permissions: { workspace, access: 'read_only', allowed_paths: [] },
    nodes: { [node.id]: { status: 'claimed', output: null } },
  };
  const pins = {
    thread_protocol_version: 2,
    root: { workflow: { name: 'Fixture', skill_policy: { mode: 'cooperative', implicit: 'allow', ambient_allow: [], shadowed_skill_paths: [] }, edges: [], requirements: {} } },
    providers: [provider], skills: [],
  };
  return executionEnvelope(node, { ...state, ...overrides }, pins, { id: 'attempt-envelope' }, 'lease');
}

test('thread handoffs carry resolved scope on starts and permission updates on continuations', () => {
  const start = threadHandoff(adapter, handoffEnvelope({ access: 'read_only', effective_allowed_paths: [], thread: { lifecycle: 'start', protocol_version: 1 } }), 'Start task');
  assert.deepEqual(start.task_context, { workspace, access: 'read_only', effective_allowed_paths: [], role: 'implementer' });
  for (const value of [workspace, 'read_only', 'implementer']) assert.equal(start.prompt.includes(value), true);

  const continuation = threadHandoff(adapter, handoffEnvelope({ access: 'bounded_write', effective_allowed_paths: ['output'], thread: { lifecycle: 'continue', protocol_version: 1, source: { thread_id: 'source-thread' } } }), 'Continue task');
  assert.equal(continuation.operation, 'send_message_to_thread');
  assert.deepEqual(continuation.task_context, { workspace, access: 'bounded_write', effective_allowed_paths: ['output'], role: 'implementer' });
  for (const value of [workspace, 'bounded_write', 'output', 'implementer']) assert.equal(continuation.prompt.includes(value), true);
  assert.equal('target' in continuation, false);
});

test('execution envelopes distinguish thread/main snapshots from the managed Provider resource broker', () => {
  const thread = envelopeFor({ id: 'work', type: 'agent', executor: { kind: 'thread', provider_id: provider.id, lifecycle: 'start' }, access: 'read_only', resources: ['source/SKILL.md'] });
  assert.deepEqual(thread.resource_access, { reader: 'thread_snapshot', paths: ['source/SKILL.md'] });
  assert.match(thread.prompt_template, /immutable UTF-8 snapshots/);
  assert.doesNotMatch(thread.prompt_template, /read_workflow_resource/);
  assert.equal(thread.thread.protocol_version, 2);

  const main = envelopeFor({ id: 'work', type: 'agent', executor: { kind: 'main' }, access: 'read_only', resources: ['source/SKILL.md'] });
  assert.deepEqual(main.resource_access, { reader: 'read_workflow_resource', paths: ['source/SKILL.md'] });
  assert.match(main.prompt_template, /read_workflow_resource/);

  const managed = envelopeFor({ id: 'work', type: 'agent', executor: { kind: 'provider', provider_id: provider.id }, access: 'read_only', resources: ['source/SKILL.md'] });
  assert.deepEqual(managed.resource_access, { reader: 'read_workflow_resource', paths: ['source/SKILL.md'] });
  assert.match(managed.prompt_template, /read_workflow_resource/);
});

test('v2 handoffs expose the dispatch marker and preserve the user result schema', () => {
  const envelope = handoffEnvelope({ outputs_schema: { type: 'object', additionalProperties: false, properties: { answer: { type: 'string' } }, required: ['answer'] } });
  const handoff = threadHandoff(adapter, envelope, 'Task prompt', { max_chars: 100_000 });
  assert.equal(handoff.protocol_version, 2);
  assert.equal(handoff.protocol.dispatch_request_id, 'dispatch-attempt-thread-fixture');
  assert.equal(handoff.protocol.prompt_marker, 'CODEX_THREAD_DISPATCH_MARKER run_id=run-thread-fixture node_id=work attempt_id=attempt-thread-fixture dispatch_request_id=dispatch-attempt-thread-fixture');
  assert.match(handoff.prompt, new RegExp(handoff.protocol.prompt_marker));
  assert.match(handoff.prompt, /"additionalProperties":false/);
  assert.match(handoff.prompt, /Do not wrap the result in a protocol envelope/);
  assert.match(handoff.collection.contract.instructions, /read_thread/);
  assert.equal(handoff.collection.contract.evidence.dispatch_request_id, handoff.protocol.dispatch_request_id);
  assert.equal(handoff.collection.contract.evidence.observed, 'completed');
  assert.equal('turn_id' in handoff.collection.contract.evidence, true);

  const legacy = threadHandoff(adapter, handoffEnvelope({ thread: { lifecycle: 'start' } }), 'Legacy task');
  assert.deepEqual(legacy.collection, { wait: 'wait_threads', read: 'read_thread' });
  assert.equal('protocol' in legacy, false);
  assert.doesNotMatch(legacy.prompt, /CODEX_THREAD_DISPATCH_MARKER/);
});

function executorFixture({ max_prompt_chars = 100_000, schema = undefined } = {}) {
  const config = { global: { enabled: true, allow_direct_api: false, max_prompt_chars }, providers: [provider] };
  const envelope = handoffEnvelope({ ...(schema === undefined ? {} : { outputs_schema: schema }) });
  const state = { nodes: { work: { attempts: [{ id: envelope.attempt_id, dispatch: null }] } } };
  let intents = 0;
  const runtime = {
    execution: async () => envelope,
    get: async () => structuredClone(state),
    threadResourcePacket: async () => [],
    recordDispatchIntent: async () => { intents += 1; return { idempotent: false }; },
  };
  const executor = new WorkflowExecutor({ runtime, getConfig: async () => config, env: {} });
  const args = { node_id: envelope.node_id, attempt_id: envelope.attempt_id, lease_token: 'lease', control_token: 'control' };
  return { config, envelope, executor, args, intents: () => intents };
}

test('a handoff succeeds at the exact compiled prompt budget', async () => {
  const fixture = executorFixture();
  const prepared = await fixture.executor.prepare('run-thread-fixture', fixture.args);
  fixture.config.global.max_prompt_chars = prepared.thread_handoff.prompt.length;
  const result = await fixture.executor.dispatch('run-thread-fixture', fixture.args);
  assert.equal(result.thread_handoff.prompt.length, fixture.config.global.max_prompt_chars);
  assert.equal(fixture.intents(), 1);
});

test('full-schema overflow is rejected before intent and remains retryable', async () => {
  const fixture = executorFixture({ schema: { type: 'object', description: 'x'.repeat(1600) } });
  const prepared = await fixture.executor.prepare('run-thread-fixture', fixture.args);
  fixture.config.global.max_prompt_chars = prepared.thread_handoff.prompt.length - 1;
  await assert.rejects(fixture.executor.dispatch('run-thread-fixture', fixture.args), { code: 'THREAD_PROMPT_LIMIT' });
  await assert.rejects(fixture.executor.dispatch('run-thread-fixture', fixture.args), { code: 'THREAD_PROMPT_LIMIT' });
  assert.equal(fixture.intents(), 0);
});
