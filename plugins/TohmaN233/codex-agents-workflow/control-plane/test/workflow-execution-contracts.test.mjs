import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, rm, writeFile } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import { tmpdir } from './physical-tempdir.mjs';
import { WorkflowStore } from '../lib/workflow-store.mjs';
import { WorkflowRuntime } from '../lib/workflow-runtime.mjs';
import { WorkflowExecutor } from '../lib/workflow-executor.mjs';
import { WorkflowDrive } from '../lib/workflow-drive.mjs';
import { createDraft } from '../lib/workflow-schema.mjs';
import { executionEnvelope } from '../lib/workflow-execution-envelope.mjs';
import { HostToolRunner, hostToolBindingIssues, requireHostToolBindings, validateHostToolContract, validateHostToolReceipt } from '../lib/execution/host-tool-runner.mjs';
import { initialCostLedger, recordUsage, reserveCost } from '../lib/workflow-cost-ledger.mjs';
import { validateWorkflowGraph } from '../lib/workflow-validator.mjs';
import { managedNativeResultSchema, semanticResultSchema, strictAgentOutputSchema, hostNodeTurnSchema, hostNodeTurnResult } from '../lib/execution/host-main-automation.mjs';
import { createManagedNativeSession } from '../lib/execution/managed-native-session.mjs';
import { createWorkflowResourceBroker } from '../lib/execution/workflow-resource-broker.mjs';
import { digest } from '../lib/workflow-revisions.mjs';

const identity = { name: 'fixture-tool', version: '1', sha256: 'a'.repeat(64) };
const fixtureProvider = { id: 'fixture-provider', name: 'Fixture', kind: 'openai_compatible', enabled: true, capabilities: { read: true, write: true }, requires_user_approval: false, config: { role: 'implementer' } };
const contract = { id: 'fixture-tool', identity, argv: ['fixture-tool', '--fixed'], input_schema: { type: 'object', properties: { value: { type: 'integer' } }, required: ['value'], additionalProperties: false }, output_schema: { type: 'object', properties: { doubled: { type: 'integer' } }, required: ['doubled'], additionalProperties: false }, env_allow: [], permissions: { network: false, read_paths: [], write_paths: [] }, output_cap_bytes: 1024, deadline_ms: 100, idempotency: { mode: 'safe' } };
const effects = (changed_paths = [], outside_paths = []) => ({ observed: true, changed_paths, outside_paths, artifacts: [] });
const broker = (execute, cancel = async () => ({ termination_confirmed: true, evidence: [{ kind: 'fixture-cancel', sha256: 'b'.repeat(64) }], effects: effects() })) => ({ identity, attestation: { qualified: true, cancellable: true, effect_observation: true, tool_identity: identity, broker_id: 'fixture-broker', evidence_sha256: 'c'.repeat(64) }, execute, cancel });
const edge = (source, target) => ({ id: `${source}-${target}`, source, target });
const agent = (id, role = 'implementer', output = {}) => ({ id, type: 'agent', executor: { kind: 'main' }, role, access: 'read_only', prompt_template: '{{task}}', outputs_schema: output, input_bindings: { task: '/inputs/task' }, approval: { required: false }, retry: { max_attempts: 1 } });
function hostWorkflow() {
  const tool = { id: 'double', type: 'tool', executor: { kind: 'tool', tool: 'fixture-tool' }, access: 'read_only', approval: { required: false }, retry: { max_attempts: 1 }, input_bindings: { value: '/inputs/value' }, outputs_schema: contract.output_schema };
  const workflow = { ...createDraft('execution-contract-fixture', 'Execution contract fixture'), status: 'ready', skill_policy: { mode: 'cooperative', implicit: 'allow', ambient_allow: [], shadowed_skill_paths: [] }, host_tools: [contract], inputs_schema: { type: 'object', properties: { task: { type: 'string' }, value: { type: 'integer' } }, required: ['task', 'value'], additionalProperties: false }, finalization: { required: true, node_id: 'final' } };
  workflow.nodes = [{ id: 'start', type: 'start' }, tool, agent('semantic'), agent('final', 'finalizer'), { id: 'end', type: 'end' }];
  workflow.edges = [edge('start', 'double'), edge('double', 'semantic'), edge('semantic', 'final'), edge('final', 'end')]; return workflow;
}
async function fixture(t, workflow = hostWorkflow(), { runner, managedNativeManager, context = { host_tools: ['fixture-tool'] }, inputs = { task: 'only declared task', value: 3 }, constraints = {}, resources = {}, environmentResolver = async () => ({ status: 'ready', tools: [], missing: [] }) } = {}) {
  const root = await mkdtemp(join(tmpdir(), 'workflow-execution-contracts-')); const workspace = join(root, 'workspace'); await mkdir(workspace);
  t.after(async () => { assert(resolve(root).startsWith(resolve(tmpdir()) + (process.platform === 'win32' ? '\\' : '/'))); await rm(root, { recursive: true, maxRetries: 3, retryDelay: 100 }); });
  const store = await new WorkflowStore(join(root, 'packs'), { validationContext: context }).initialize(); const pack = await store.create(workflow, { resources });
  const runtime = await new WorkflowRuntime({ workflowStore: store, runRoot: join(root, 'runs'), context, environmentResolver }).initialize();
  const executor = new WorkflowExecutor({ runtime, getConfig: async () => ({ global: { enabled: true, max_prompt_chars: 64000, allow_direct_api: false }, providers: context.providers ?? [] }), registry: {}, hostToolRunner: runner, managedNativeManager, env: {} });
  const run = await runtime.start({ workflow_id: workflow.id, revision_hash: pack.revision_hash, workspace, access: 'read_only', main_actor: 'main', inputs, constraints });
  return { runtime, executor, run, drive: new WorkflowDrive({ runtime, executor, store }) };
}
const completion = output => ({ status: 'succeeded', summary: 'synthetic', structured_output: output, artifacts: [], evidence: [{ kind: 'synthetic' }], changed_paths: [], outside_paths: [] });
const claim = async (f, node) => {
  const record = await f.runtime.runs.read(f.run.run_id);
  const args = { node_id: node, owner: 'main', request_id: `claim-${node}`, control_token: f.run.control_token };
  return record.pins.root.workflow.nodes.find(item => item.id === node)?.executor?.kind === 'main'
    ? f.runtime.claimHostMain(f.run.run_id, args)
    : f.runtime.claimNode(f.run.run_id, args);
};
async function acknowledgeProvider(runtime, run, lease) {
  const request_id = `dispatch-${lease.attempt_id}`;
  const args = { ...lease, control_token: run.control_token, request_id, envelope_hash: 'e'.repeat(64) };
  await runtime.recordDispatchIntent(run.run_id, args);
  await runtime.recordDispatchReceipt(run.run_id, { ...args, receipt: { task_id: `fixture-${lease.attempt_id}` } });
}
async function proposeHostResult(runtime, run, lease, result) {
  const saved = await runtime.runs.saveExecutorResult(run.run_id, lease.attempt_id, result);
  await runtime.recordExecutorEvent(run.run_id, { ...lease, control_token: run.control_token,
    event: { kind: 'result_proposed', metadata: { ...saved, final_acceptance_required: false } } });
}

test('projection exposes declared bindings and references only', () => {
  const node = { ...agent('review'), resources: ['source/task.md'], input_bindings: { task: '/inputs/task' } };
  const state = { run_id: 'r', workflow_id: 'w', workflow_revision: 'x', inputs: { task: 'visible', secret: 'hidden' }, constraints: {}, permissions: { workspace: 'C:/fixture', access: 'read_only', allowed_paths: [] }, nodes: { review: { status: 'claimed', output: null }, upstream: { status: 'succeeded', output: { secret: 'not copied' }, error: null } } };
  const pins = { root: { workflow: { name: 'w', edges: [{ id: 'upstream-review', source: 'upstream', target: 'review' }], requirements: {}, skill_policy: { mode: 'cooperative', implicit: 'allow', ambient_allow: [], shadowed_skill_paths: [] } }, resources: [{ path: 'source/task.md', sha256: 'b'.repeat(64), bytes: 1 }] }, providers: [], skills: [] };
  const envelope = executionEnvelope(node, state, pins, { id: 'a' }, 'lease');
  assert.deepEqual({ ...envelope.inputs }, { task: 'visible' }); assert.equal('workflow_inputs' in envelope, false); assert.equal('upstream_results' in envelope, false); assert.deepEqual(envelope.context_projection.references, ['source/task.md']);
});

test('old provenance cannot widen declared node context', () => {
  const node = { ...agent('review'), input_bindings: { task: '/inputs/task' } };
  const state = { run_id: 'r', workflow_id: 'w', workflow_revision: 'old', inputs: { task: 'visible', prior: 'legacy-only' }, constraints: {}, permissions: { workspace: 'C:/fixture', access: 'read_only', allowed_paths: [] }, nodes: { review: { status: 'claimed', output: null }, prior: { status: 'succeeded', output: { retained: true }, error: null } } };
  const workflow = { name: 'w', edges: [{ id: 'prior-review', source: 'prior', target: 'review' }], requirements: {}, skill_policy: { mode: 'cooperative', implicit: 'allow', ambient_allow: [], shadowed_skill_paths: [] } };
  const envelope = executionEnvelope(node, state, { root: { workflow, provenance: { kind: 'v6-migration' }, resources: [] }, providers: [], skills: [] }, { id: 'a' }, 'lease');
  assert.deepEqual({ ...envelope.inputs }, { task: 'visible' });
  assert.equal(envelope.context_projection.legacy_ancestor_results, undefined);
});

test('schema rejects an unpinned host tool and malformed finite decision contract', () => {
  const workflow = hostWorkflow(); workflow.host_tools = [{ ...contract, deadline_ms: 0 }];
  assert(validateWorkflowGraph(workflow, { host_tools: ['fixture-tool'] }).errors.some(error => error.code === 'HOST_TOOL_CONTRACT'));
  workflow.host_tools = [contract]; const semantic = workflow.nodes.find(node => node.id === 'semantic'); semantic.decision = { id: 'route', options: ['a', 'a'], required_references: [] };
  assert(validateWorkflowGraph(workflow, { host_tools: ['fixture-tool'] }).errors.some(error => error.code === 'DECISION_CONTRACT'));
});

test('agent output schemas fail before launch when an open model-authored map cannot satisfy App Server strict output', () => {
  const definition = agent('candidate', 'implementer', {
    type: 'object',
    properties: { candidate_manifest: { type: 'object', additionalProperties: true } },
    required: ['candidate_manifest'],
    additionalProperties: false,
  });
  definition.executor = { kind: 'provider', provider_id: 'native-luna' };
  assert.throws(() => managedNativeResultSchema(definition), { code: 'AGENT_OUTPUT_SCHEMA' });
  const workflow = hostWorkflow();
  const semantic = workflow.nodes.find(node => node.id === 'semantic');
  semantic.executor = definition.executor;
  semantic.outputs_schema = definition.outputs_schema;
  const checked = validateWorkflowGraph(workflow, { host_tools: ['fixture-tool'], providers: [{ id: 'native-luna', kind: 'native_agent', enabled: true, capabilities: { read: true, write: true }, config: { role: 'implementer' } }] });
  assert.equal(checked.valid, false);
  assert(checked.errors.some(error => error.code === 'AGENT_OUTPUT_SCHEMA' && error.node_id === 'semantic'));
});

test('host automation emits an App Server strict empty schema when a node declares no semantic fields', () => {
  assert.deepEqual(strictAgentOutputSchema({}), { type: 'object', properties: {}, required: [], additionalProperties: false });
  const final = agent('final', 'finalizer', { type: 'object', properties: { accepted: { type: 'boolean' } }, required: ['accepted'], additionalProperties: false });
  assert.deepEqual(semanticResultSchema(final, { finalAcceptance: true }), { type: 'object', properties: {}, required: [], additionalProperties: false });
});

test('Host node result distinguishes a concrete blocker from a completed semantic value', () => {
  const semantic = { type: 'object', properties: { changes: { type: 'string' }, scenario_jobs: { type: 'array', items: { type: 'string' } } },
    required: ['changes', 'scenario_jobs'], additionalProperties: false };
  const schema = hostNodeTurnSchema(semantic);
  assert.deepEqual(schema.properties.outcome.enum, ['completed', 'blocked']);
  assert.deepEqual(hostNodeTurnResult({ outcome: 'completed', result: { changes: 'one card', scenario_jobs: ['card-a'] }, block_reason: '' }, semantic),
    { changes: 'one card', scenario_jobs: ['card-a'] });
  assert.throws(() => hostNodeTurnResult({ outcome: 'blocked', result: null, block_reason: 'required command tool unavailable' }, semantic),
    { code: 'WORKFLOW_NODE_BLOCKED' });
  assert.throws(() => hostNodeTurnResult({ outcome: 'completed', result: null, block_reason: '' }, semantic), { code: 'DATA_INVALID' });
});

test('managed thread/start activates exact Run access and retains normal permissions and Workflow resource tools', async t => {
  const root = await mkdtemp(join(tmpdir(), 'managed-thread-contract-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  const binary = join(root, 'fixture-binary'), cwd = join(root, 'workspace'), home = join(root, 'home');
  await writeFile(binary, 'fixture'); await mkdir(cwd); await mkdir(home);
  const model = 'fixture-model', resource = { path: 'source/task.md', bytes: Buffer.from('task'), sha256: digest('task') };
  for (const { access, returnedSandbox } of [
    { access: 'read_only', returnedSandbox: 'readOnly' },
    { access: 'bounded_write', returnedSandbox: 'workspaceWrite' },
    { access: 'read_only', returnedSandbox: 'workspaceWrite' },
  ]) {
    const resourceBroker = await createWorkflowResourceBroker({ workspace: cwd, access,
      allowedPaths: access === 'bounded_write' ? ['.'] : [], resources: [resource], authorize: async () => {}, onOperation: async () => {} });
    let params, turnStarts = 0;
    const client = {
      events: [], initialized() {}, async close() {},
      async call(method, arguments_) {
        if (method === 'initialize') return {};
        if (method === 'account/read') return { account: { type: 'chatgpt' }, requiresOpenaiAuth: true };
        if (method === 'model/list') return { data: [{ model, supportedReasoningEfforts: [{ reasoningEffort: 'high' }] }] };
        if (method === 'skills/list') return { data: [{ cwd, skills: [], errors: [] }] };
        if (method === 'thread/start') {
          params = arguments_;
          return { model, modelProvider: 'openai', sandbox: { type: returnedSandbox }, thread: { id: 'fixture-thread' } };
        }
        if (method === 'turn/start') {
          turnStarts++;
          this.events.push({ method: 'item/completed', params: { threadId: 'fixture-thread', turnId: 'fixture-turn',
            item: { type: 'agentMessage', phase: 'final_answer', text: '{"done":true}' } } });
          return { turn: { id: 'fixture-turn' } };
        }
        assert.fail(`Unexpected App Server method: ${method}`);
      },
      async waitFor() { return { method: 'turn/completed', params: { threadId: 'fixture-thread', turn: { id: 'fixture-turn', status: 'completed' } } }; },
    };
    const session = await createManagedNativeSession({ parent: root, binary, expectedBinaryHash: digest('fixture'),
      cwd, model, effort: 'high', access, allowedPaths: access === 'bounded_write' ? ['.'] : [], env: { CODEX_HOME: home },
      skillPolicy: { implicit: 'deny', ambient_allow: [], shadowed_skill_paths: [] }, toolBroker: resourceBroker,
      dynamicToolFormat: 'tagged_function', clientFactory: () => client, modelMetadataReader: async () => ({ slug: model, tool_mode: 'code_mode_only',
        base_instructions: 'Normal instructions', input_modalities: ['text'], supports_parallel_tool_calls: true }) });
    try {
      if (access === 'read_only' && returnedSandbox === 'workspaceWrite')
        await assert.rejects(session.turn('Perform the supplied task'), { code: 'CODEX_SANDBOX_UNCONTROLLED' });
      else assert.equal((await session.turn('Perform the supplied task')).output, '{"done":true}');
      assert.equal(turnStarts, access === 'read_only' && returnedSandbox === 'workspaceWrite' ? 0 : 1);
      assert.equal(params.cwd, cwd); assert.equal(params.model, model);
      assert.equal(params.sandbox, access === 'read_only' ? 'read-only' : 'workspace-write');
      assert.equal(params.approvalPolicy, undefined); assert.equal(params.baseInstructions, undefined);
      assert.equal(params.environments, undefined); assert.equal(params.ephemeral, false);
      assert.equal(params.allowProviderModelFallback, false);
      const resourceTools = resourceBroker.tools();
      assert.deepEqual(params.dynamicTools.slice(0, resourceTools.length), resourceTools.map(tool => ({ ...tool, type: 'function' })));
      assert(params.dynamicTools.some(tool => tool.name === 'run_workspace_command'));
      assert(!params.dynamicTools.some(tool => tool.name === 'write_workspace'));
    } finally { await session.close(); }
  }
});

test('host tool binding preflight rejects stale implementation identity before a run starts', () => {
  const implementation = broker(async () => ({ exit_code: 0, diagnostic: '', effects: effects(), output: { doubled: 2 } }));
  implementation.identity = { ...identity, sha256: 'f'.repeat(64) };
  implementation.attestation = { ...implementation.attestation, tool_identity: implementation.identity };
  const workflow = { host_tools: [contract] };
  const issues = hostToolBindingIssues(workflow, { [contract.id]: implementation });
  assert.equal(issues.length, 1);
  assert.equal(issues[0].code, 'HOST_TOOL_UNAVAILABLE');
  assert.throws(() => requireHostToolBindings(workflow, { [contract.id]: implementation }), { code: 'HOST_TOOL_BINDING_STALE' });
});

test('host tool contract is pinned, deterministic drive executes it without a model turn, and journals an exact receipt', async t => {
  let calls = 0; const runner = new HostToolRunner({ registry: { 'fixture-tool': broker(async ({ input, argv, permissions }) => { calls++; assert.deepEqual(argv, ['fixture-tool', '--fixed']); assert.equal(permissions.network, false); return { exit_code: 0, diagnostic: 'ok', effects: effects(), output: { doubled: input.value * 2 } }; }) }, env: {} });
  const f = await fixture(t, hostWorkflow(), { runner }); const result = await f.drive.advance(f.run.run_id, { control_token: f.run.control_token });
  assert.deepEqual(result, { status: 'running', stop_reason: 'semantic_node', node_id: 'semantic', steps: 1 }); assert.equal(calls, 1);
  const state = await f.runtime.get(f.run.run_id); const receipt = state.nodes.double.attempts[0].host_tool.receipt;
  assert.equal(state.nodes.double.output.doubled, 6); assert.equal(receipt.run_id, f.run.run_id); assert.equal(receipt.node_id, 'double'); assert.equal(receipt.status, 'succeeded'); assert.equal(receipt.input, undefined); assert.equal(receipt.output, undefined); assert.equal(receipt.output_ref !== null, true);
  assert.throws(() => validateHostToolReceipt({ ...receipt, input: { value: 3 } }), { code: 'HOST_TOOL_RECEIPT' });
  assert.throws(() => validateHostToolReceipt({ ...receipt, diagnostics: { ...receipt.diagnostics, sha256: '0'.repeat(64) } }), { code: 'HOST_TOOL_RECEIPT' });
});

test('a guarded Host tool finalizes a Run without a model relay', async t => {
  const finalContract = {
    ...contract,
    output_schema: {
      type: 'object',
      properties: { doubled: { type: 'integer' }, all_passed: { type: 'boolean' } },
      required: ['doubled', 'all_passed'],
      additionalProperties: false,
    },
  };
  const workflow = hostWorkflow();
  const tool = workflow.nodes.find(node => node.id === 'double');
  tool.outputs_schema = finalContract.output_schema;
  tool.completion_contract = { on_missing: 'block', outcome: 'validated_artifact', fail_on_false: ['all_passed'] };
  workflow.host_tools = [finalContract];
  workflow.nodes = [workflow.nodes.find(node => node.id === 'start'), tool, workflow.nodes.find(node => node.id === 'end')];
  workflow.edges = [edge('start', 'double'), edge('double', 'end')];
  workflow.finalization = { required: true, node_id: 'double' };
  assert.equal(validateWorkflowGraph(workflow, { host_tools: ['fixture-tool'] }).valid, true);

  let calls = 0;
  const runner = new HostToolRunner({ registry: { 'fixture-tool': broker(async ({ input }) => {
    calls++;
    return { exit_code: 0, diagnostic: 'all checks passed', effects: effects(), output: { doubled: input.value * 2, all_passed: true } };
  }) }, env: {} });
  const f = await fixture(t, workflow, { runner });
  const result = await f.drive.advance(f.run.run_id, { control_token: f.run.control_token });
  assert.deepEqual(result, { status: 'succeeded', stop_reason: 'terminal', steps: 1 });
  assert.equal(calls, 1);
  const state = await f.runtime.get(f.run.run_id);
  assert.deepEqual(state.nodes.double.output, { doubled: 6, all_passed: true });
  assert.equal(state.status, 'succeeded');
});

test('host tools receive the exact Run-resolved executable paths instead of rediscovering global PATH', async t => {
  const resolved = { status: 'ready', tools: [{ name: 'media-tool', status: 'found', path: 'C:\\portable\\media-tool.exe' }], missing: [], searched_directories: ['C:\\portable'], installation_performed: false };
  let observed;
  const runner = new HostToolRunner({ registry: { 'fixture-tool': broker(async ({ context, input }) => {
    observed = context.runtime_environment;
    return { exit_code: 0, diagnostic: 'ok', effects: effects(), output: { doubled: input.value * 2 } };
  }) }, env: { PATH: '' } });
  const f = await fixture(t, hostWorkflow(), { runner, environmentResolver: async () => resolved });
  await f.drive.advance(f.run.run_id, { control_token: f.run.control_token });
  assert.deepEqual(observed, resolved);
});

test('host execution cleanup settles after durable output storage fails so cancellation cannot hang', async t => {
  const runner = new HostToolRunner({ registry: { 'fixture-tool': broker(async ({ input }) => ({ exit_code: 0, diagnostic: 'ok', effects: effects(), output: { doubled: input.value * 2 } })) }, env: {} });
  const f = await fixture(t, hostWorkflow(), { runner }); const lease = await claim(f, 'double');
  f.runtime.runs.saveExecutorResult = async () => { throw Object.assign(new Error('Synthetic output persistence failure'), { code: 'SYNTHETIC_SAVE_FAILURE' }); };
  await assert.rejects(f.executor.executeHostTool(f.run.run_id, { ...lease, control_token: f.run.control_token }), { code: 'SYNTHETIC_SAVE_FAILURE' });
  const cleanup = f.executor.cancelPendingHostTools(f.run.run_id, f.run.control_token);
  await Promise.race([cleanup, new Promise((_resolve, reject) => setTimeout(() => reject(new Error('Host cleanup hung after saveExecutorResult failure')), 250))]);
  assert.equal(f.executor.hostExecutions.size, 0);
});

test('cancellation fences a host attempt suspended in Run I/O before it can write intent or launch broker work', async t => {
  let calls = 0;
  const runner = new HostToolRunner({ registry: { 'fixture-tool': broker(async () => { calls++; return { exit_code: 0, diagnostic: '', effects: effects(), output: { doubled: 6 } }; }) }, env: {} });
  const f = await fixture(t, hostWorkflow(), { runner }); const lease = await claim(f, 'double');
  const originalRead = f.runtime.runs.read.bind(f.runtime.runs);
  let reads = 0; let enterRead; let releaseRead;
  const entered = new Promise(resolve => { enterRead = resolve; });
  const held = new Promise(resolve => { releaseRead = resolve; });
  f.runtime.runs.read = async (...args) => {
    const record = await originalRead(...args);
    if (++reads === 2) { enterRead(); await held; }
    return record;
  };
  const dispatch = f.executor.executeHostTool(f.run.run_id, { ...lease, control_token: f.run.control_token });
  await entered;
  assert.equal(f.executor.hostExecutions.size, 1);
  await f.runtime.cancel(f.run.run_id, { control_token: f.run.control_token });
  const cleanup = f.executor.cancelPendingHostTools(f.run.run_id, f.run.control_token);
  releaseRead();
  await assert.rejects(dispatch, error => ['HOST_TOOL_STOPPED', 'STALE_LEASE', 'ATTEMPT_STOPPED'].includes(error.code));
  await cleanup;
  assert.equal(calls, 0);
  assert.equal(f.executor.hostExecutions.size, 0);
  const state = await f.runtime.get(f.run.run_id);
  assert.equal(state.nodes.double.attempts[0].host_tool, undefined);
});

test('a pre-aborted host signal produces a cancellation receipt without scheduling broker execution', async () => {
  let calls = 0; let cancellations = 0;
  const runner = new HostToolRunner({ registry: { 'fixture-tool': broker(async () => { calls++; return { exit_code: 0, diagnostic: '', effects: effects(), output: { doubled: 6 } }; }, async () => { cancellations++; return { termination_confirmed: true, evidence: [{ kind: 'fixture-cancel', sha256: 'b'.repeat(64) }], effects: effects() }; }) }, env: {} });
  const controller = new AbortController(); controller.abort(new Error('cancelled before launch'));
  const result = await runner.execute(contract, { value: 3 }, { run_id: 'r', node_id: 'double', attempt_id: 'a', permissions: { access: 'read_only', allowed_paths: [] } }, { signal: controller.signal });
  assert.equal(result.receipt.status, 'cancelled');
  assert.equal(calls, 0);
  assert.equal(cancellations, 1);
});

test('revoking the drive gate after a durable host intent yields a receipt but no broker launch', async t => {
  let calls = 0; let active = true;
  const runner = new HostToolRunner({ registry: { 'fixture-tool': broker(async () => { calls++; return { exit_code: 0, diagnostic: '', effects: effects(), output: { doubled: 6 } }; }) }, env: {} });
  const f = await fixture(t, hostWorkflow(), { runner });
  const originalIntent = f.runtime.recordHostToolIntent.bind(f.runtime);
  f.runtime.recordHostToolIntent = async (...args) => { const result = await originalIntent(...args); active = false; return result; };
  await assert.rejects(f.drive.advance(f.run.run_id, { control_token: f.run.control_token,
    assertActive: () => { if (!active) throw Object.assign(new Error('Main stopped'), { code: 'HOST_MAIN_STOPPED' }); } }), { code: 'HOST_MAIN_STOPPED' });
  assert.equal(calls, 0);
  const state = await f.runtime.get(f.run.run_id);
  assert.equal(state.nodes.double.attempts[0].host_tool.receipt.status, 'cancelled');
});

test('host tools bind a declared physical workspace to the exact Run/node workspace', async t => {
  const f = await fixture(t); const workspace = (await f.runtime.runs.read(f.run.run_id)).state.permissions.workspace;
  const workspaceContract = { ...contract, input_schema: { type: 'object', properties: { workspace: { type: 'string' } }, required: ['workspace'], additionalProperties: false } };
  const runner = new HostToolRunner({ registry: { 'fixture-tool': broker(async () => ({ exit_code: 0, diagnostic: '', effects: effects(), output: { doubled: 2 } })) }, env: {} });
  const context = { run_id: 'r', node_id: 'n', attempt_id: 'a', workspace, permissions: { access: 'read_only', allowed_paths: [] } };
  assert.equal((await runner.execute(workspaceContract, { workspace }, context)).receipt.status, 'succeeded');
  await assert.rejects(runner.execute(workspaceContract, { workspace: resolve(workspace, '..') }, context), { code: 'HOST_TOOL_WORKSPACE_MISMATCH' });
  await assert.rejects(runner.execute(workspaceContract, { workspace }, { ...context, workspace: undefined }), { code: 'HOST_TOOL_WORKSPACE_REQUIRED' });
});

test('compact main-session drive claims, dispatches and projects only the current node resources', async t => {
  const workflow = hostWorkflow();
  const semantic = workflow.nodes.find(node => node.id === 'semantic');
  semantic.resources = ['workflow/current.md'];
  semantic.outputs_schema = { type: 'object', properties: { decision_id: { type: 'string' }, decision: { type: 'string' }, references: { type: 'array', items: { type: 'string' } } }, required: ['decision_id', 'decision', 'references'], additionalProperties: false };
  semantic.decision = { id: 'semantic-disposition', options: ['continue', 'blocked'], required_references: ['workflow/current.md'] };
  const runner = new HostToolRunner({ registry: { 'fixture-tool': broker(async ({ input }) => ({ exit_code: 0, diagnostic: '', effects: effects(), output: { doubled: input.value * 2 } })) }, env: {} });
  const f = await fixture(t, workflow, { runner, resources: { 'workflow/current.md': 'current-only' } });
  const handoff = await f.drive.advanceToMain(f.run.run_id, { control_token: f.run.control_token, owner: 'main', request_prefix: 'compact' });
  assert.equal(handoff.stop_reason, 'main_node');
  assert.equal(handoff.host_binding.node_id, 'semantic');
  assert.deepEqual(handoff.agent_packet.resources, [{ path: 'workflow/current.md' }]);
  assert.equal(handoff.agent_packet.prompt.includes('only declared task'), true);
  assert.equal(handoff.agent_packet.response_form.schema.properties.decision_id, undefined);
  assert.equal(handoff.agent_packet.response_form.schema.properties.references, undefined);
  assert.deepEqual(handoff.agent_packet.response_form.schema.properties.decision.enum, ['continue', 'blocked']);
  assert.deepEqual(handoff.agent_packet.response_form.decision.options, ['continue', 'blocked']);
  for (const field of ['run_id','control_token','node_id','attempt_id','lease_token','owner','status','structured_output','decision_id','references','acceptance']) assert.equal(Object.hasOwn(handoff.agent_packet, field), false);
  const state = await f.runtime.get(f.run.run_id);
  assert.equal(state.nodes.double.status, 'succeeded');
  assert.equal(state.nodes.semantic.status, 'claimed');
  assert.equal(state.nodes.semantic.attempts[0].dispatch.request_id.startsWith('dispatch-'), true);
  assert.equal(state.nodes.final.status, 'pending');
});

test('compact drive stops at native Provider without launching an invisible App Server child', async t => {
  const workflow = hostWorkflow();
  const child = workflow.nodes.find(node => node.id === 'semantic');
  child.executor = { kind: 'provider', provider_id: 'native-luna' };
  child.resources = ['workflow/current.md'];
  child.outputs_schema = { type: 'object', properties: { answer: { type: 'string' } }, required: ['answer'], additionalProperties: false };
  const provider = { id: 'native-luna', name: 'Luna', kind: 'native_agent', enabled: true, capabilities: { read: true, write: true }, requires_user_approval: false, config: { model: 'gpt-5.6-luna', reasoning_effort: 'max', role: 'implementer', fresh_context: true } };
  const calls = [];
  const managedNativeManager = {
    async prepare(_runtime, _runId, _args, envelope) {
      calls.push({ phase: 'prepare', node_id: envelope.node_id, model: envelope.provider.config.model, effort: envelope.provider.config.reasoning_effort, resource_reader: envelope.resource_access.reader });
      return { execution: 'managed_native_codex', model: envelope.provider.config.model, effort: envelope.provider.config.reasoning_effort };
    },
    async launch(runtime, runId, args, prepared) {
      calls.push({ phase: 'launch', run_id: runId, node_id: args.node_id, prompt: prepared.prompt });
      const request_id = `dispatch-${args.attempt_id}`;
      const receipt = { invocation_id: `managed-${args.attempt_id}`, executor: 'codex-app-server', model: prepared.adapter.model, effort: prepared.adapter.effort };
      await runtime.recordDispatchReceipt(runId, { ...args, request_id, receipt });
      await runtime.recordUsage(runId, { ...args, request_id, usage: { unknown: false, input_tokens: 10, output_tokens: 2, cached_input_tokens: 0, cost_micros: 1 } });
      await runtime.completeNode(runId, { ...args, completion: completion({ answer: 'host-owned child result' }) });
      return { dispatched: true, receipt, completed: true };
    },
  };
  const runner = new HostToolRunner({ registry: { 'fixture-tool': broker(async ({ input }) => ({ exit_code: 0, diagnostic: '', effects: effects(), output: { doubled: input.value * 2 } })) }, env: {} });
  const f = await fixture(t, workflow, { runner, managedNativeManager, context: { host_tools: ['fixture-tool'], providers: [provider] }, resources: { 'workflow/current.md': 'current-only' } });
  const handoff = await f.drive.advanceToMain(f.run.run_id, { control_token: f.run.control_token, owner: 'main', request_prefix: 'compact-native' });
  assert.equal(handoff.stop_reason, 'non_main_semantic');
  assert.equal(handoff.node_id, 'semantic');
  assert.deepEqual(calls, []);
  const state = await f.runtime.get(f.run.run_id);
  assert.equal(state.nodes.semantic.status, 'ready');
  assert.equal(state.nodes.final.status, 'pending');
});

test('generic drive never claims or dispatches a Strict native node through the cooperative managed-native manager', async t => {
  const workflow=hostWorkflow(),semantic=workflow.nodes.find(node=>node.id==='semantic');
  semantic.executor={kind:'provider',provider_id:'native-luna'};
  semantic.skill_policy={mode:'strict',implicit:'deny',ambient_allow:[],shadowed_skill_paths:[]};
  const provider={id:'native-luna',name:'Luna',kind:'native_agent',enabled:true,capabilities:{read:true,write:true},requires_user_approval:false,config:{model:'gpt-5.6-luna',reasoning_effort:'max',role:'implementer',fresh_context:true}};
  let managedCalls=0;
  const managedNativeManager={prepare:async()=>{managedCalls++;throw new Error('must not prepare');},launch:async()=>{managedCalls++;throw new Error('must not launch');},wait:async()=>{managedCalls++;throw new Error('must not wait');}};
  const runner=new HostToolRunner({registry:{'fixture-tool':broker(async({input})=>({exit_code:0,diagnostic:'ok',effects:effects(),output:{doubled:input.value*2}}))},env:{}});
  const f=await fixture(t,workflow,{runner,managedNativeManager,context:{host_tools:['fixture-tool'],providers:[provider]}});
  const result=await f.drive.advance(f.run.run_id,{control_token:f.run.control_token});
  assert.deepEqual(result,{status:'running',stop_reason:'semantic_node',node_id:'semantic',steps:1});
  assert.equal(managedCalls,0);
  const state=await f.runtime.get(f.run.run_id);
  assert.equal(state.nodes.semantic.attempts.length,0);
});

test('Host-owned drive waits for the actual Strict native owner before continuing to Main',async t=>{
  const workflow=hostWorkflow(),semantic=workflow.nodes.find(node=>node.id==='semantic');
  semantic.executor={kind:'provider',provider_id:'native-luna'};
  semantic.skill_policy={mode:'strict',implicit:'deny',ambient_allow:[],shadowed_skill_paths:[]};
  semantic.outputs_schema={type:'object',properties:{answer:{type:'string'}},required:['answer'],additionalProperties:false};
  const provider={id:'native-luna',name:'Luna',kind:'native_agent',enabled:true,capabilities:{read:true,write:true},
    requires_user_approval:false,config:{model:'gpt-5.6-luna',reasoning_effort:'max',role:'implementer',fresh_context:true}};
  let launched,waited=0,managedWaited=0;
  const strictManager={
    prepare:async()=>({execution:'strict_codex',model:provider.config.model,effort:provider.config.reasoning_effort,final_acceptance_required:false}),
    launch:async(runtime,runId,args)=>{
      launched={runtime,runId,args};
      const receipt={invocation_id:`strict-${args.attempt_id}`,executor:'codex-app-server'};
      await runtime.recordDispatchReceipt(runId,{...args,request_id:`dispatch-${args.attempt_id}`,receipt});
      return {dispatched:true,receipt,execution_owner:'strict_codex',session:{status:'running'}};
    },
    wait:async(runId,attemptId)=>{
      waited++;assert.equal(runId,launched.runId);assert.equal(attemptId,launched.args.attempt_id);
      const {runtime,args}=launched,request_id=`dispatch-${args.attempt_id}`;
      await runtime.recordUsage(runId,{...args,request_id,usage:{unknown:false,input_tokens:1,output_tokens:1,cached_input_tokens:0,cost_micros:1}});
      await runtime.completeNode(runId,{...args,completion:completion({answer:'strict completed'})});
      return {status:'succeeded'};
    },
  };
  const managedNativeManager={wait:async()=>{managedWaited++;throw new Error('wrong manager waited');}};
  const runner=new HostToolRunner({registry:{'fixture-tool':broker(async({input})=>({exit_code:0,diagnostic:'ok',effects:effects(),output:{doubled:input.value*2}}))},env:{}});
  const f=await fixture(t,workflow,{runner,managedNativeManager,context:{host_tools:['fixture-tool'],providers:[provider]}});
  f.executor.strictManager=strictManager;
  const handoff=await f.drive.advanceToMain(f.run.run_id,{control_token:f.run.control_token,owner:'main',managedProviders:true});
  assert.equal(handoff.stop_reason,'main_node');assert.equal(handoff.host_binding.node_id,'final');
  assert.equal(waited,1);assert.equal(managedWaited,0);
  const state=await f.runtime.get(f.run.run_id);assert.equal(state.nodes.semantic.status,'succeeded');
  const replay=await f.executor.dispatch(f.run.run_id,{...launched.args,host_managed_native:true});
  assert.equal(replay.idempotent,true);assert.equal(replay.execution_owner,'strict_codex');
});

test('drive stops before unavailable bindings or unaffordable semantic work and never dispatches either as a model call', async t => {
  const missing = hostWorkflow(); missing.inputs_schema.required = ['task'];
  const noInput = await fixture(t, missing, { inputs: { task: 'declared only' } });
  assert.deepEqual(await noInput.drive.advance(noInput.run.run_id, { control_token: noInput.run.control_token }), { status: 'running', stop_reason: 'missing_input', node_id: 'double', error: { code: 'BINDING_MISSING', message: 'Required binding value is unavailable' }, steps: 0 });
  const budgeted = hostWorkflow(); budgeted.nodes.find(node => node.id === 'semantic').cost = { maximum_micros: 5 };
  const runner = new HostToolRunner({ registry: { 'fixture-tool': broker(async ({ input }) => ({ exit_code: 0, diagnostic: '', effects: effects(), output: { doubled: input.value * 2 } })) }, env: {} });
  const noBudget = await fixture(t, budgeted, { runner, constraints: { cost_budget: { approval_id: 'approved', currency: 'USD', limit_micros: 4 } } });
  assert.deepEqual(await noBudget.drive.advance(noBudget.run.run_id, { control_token: noBudget.run.control_token }), { status: 'running', stop_reason: 'budget', node_id: 'semantic', steps: 1 });
});

test('host tool failure and timeout are explicit receipts; only the pinned safe mode can replay an unreceipted intent', async t => {
  const failed = new HostToolRunner({ registry: { 'fixture-tool': broker(async () => ({ exit_code: 7, diagnostic: 'bad', effects: effects(), output: null })) }, env: {} });
  const failedResult = await failed.execute(validateHostToolContract(contract), { value: 1 }, { run_id: 'r', node_id: 'n', attempt_id: 'a', permissions: { access: 'read_only', allowed_paths: [] } }); assert.equal(failedResult.receipt.status, 'failed'); assert.equal(failedResult.receipt.exit_code, 7);
  const f = await fixture(t, hostWorkflow(), { runner: failed }); const lease = await claim(f, 'double');
  await f.runtime.recordHostToolIntent(f.run.run_id, { ...lease, control_token: f.run.control_token, contract, input: { value: 3 } });
  const recovered = await f.executor.executeHostTool(f.run.run_id, { ...lease, control_token: f.run.control_token }); assert.equal(recovered.nodes.double.status, 'failed');
  let aborted = false; const timed = new HostToolRunner({ registry: { 'fixture-tool': broker(async ({ signal }) => new Promise(resolve => signal.addEventListener('abort', () => { aborted = true; resolve({ exit_code: 143, diagnostic: 'terminated', effects: effects(['out/partial.txt']), output: null }); }, { once: true })), async () => ({ termination_confirmed: true, evidence: [{ kind: 'fixture-process-exit', sha256: 'd'.repeat(64) }], effects: effects(['out/partial.txt']) })) }, env: {} });
  const timeoutResult = await timed.execute({ ...contract, permissions: { ...contract.permissions, write_paths: ['out'] }, deadline_ms: 1 }, { value: 1 }, { run_id: 'r', node_id: 'n', attempt_id: 'a', permissions: { access: 'bounded_write', allowed_paths: ['out'] } }); assert.equal(timeoutResult.receipt.status, 'timed_out'); assert.equal(timeoutResult.receipt.reconciliation.termination_confirmed, true); assert.equal(aborted, true); assert.deepEqual(timeoutResult.receipt.effects.changed_paths, ['out/partial.txt']);
  const permissive = { ...contract, input_schema: { type: 'object', additionalProperties: true }, output_schema: { type: 'object', additionalProperties: true } };
  const secure = new HostToolRunner({ registry: { 'fixture-tool': broker(async () => ({ exit_code: 7, diagnostic: '{"nested":{"api_key":"synthetic-secret"}}', effects: effects(), output: null })) }, env: {} });
  await assert.rejects(secure.execute(permissive, { nested: { authorization: 'Bearer synthetic-secret' } }, { run_id: 'r', node_id: 'n', attempt_id: 'a', permissions: { access: 'read_only', allowed_paths: [] } }), { code: 'HOST_TOOL_SECRET' });
  const redacted = await secure.execute(permissive, { value: 1 }, { run_id: 'r', node_id: 'n', attempt_id: 'a', permissions: { access: 'read_only', allowed_paths: [] } }); assert.equal(redacted.receipt.diagnostics.message.includes('synthetic-secret'), false); assert(redacted.receipt.diagnostics.message.includes('[redacted]'));
});

test('cost ledger reserves atomically, treats unknown use as nonzero uncertainty, and main receipts must stay in one attested session', async t => {
  const ledger = initialCostLedger({ approval_id: 'approved', currency: 'USD', limit_micros: 10 }); reserveCost(ledger, { call_id: 'first', node_id: 'n', attempt_id: 'a', maximum_micros: 10 });
  assert.throws(() => reserveCost(ledger, { call_id: 'second', node_id: 'n', attempt_id: 'b', maximum_micros: 1 }), { code: 'COST_BUDGET_EXCEEDED' }); recordUsage(ledger, 'first', { unknown: true, input_tokens: 4 }); assert.equal(ledger.reserved_micros, 0); assert.equal(ledger.uncertain_micros, 10); assert.equal(ledger.unknown_usage_count, 1);
  const workflow = hostWorkflow(); workflow.nodes = [{ id: 'start', type: 'start' }, { ...agent('work', 'implementer', { type: 'object', properties: { ok: { type: 'boolean' } }, required: ['ok'], additionalProperties: false }), cost: { maximum_micros: 5 } }, { ...agent('final', 'finalizer'), cost: { maximum_micros: 5 } }, { id: 'end', type: 'end' }]; workflow.edges = [edge('start', 'work'), edge('work', 'final'), edge('final', 'end')]; workflow.host_tools = [];
  const f = await fixture(t, workflow, { context: {} }); const run = await f.runtime.start({ workflow_id: workflow.id, workspace: (await f.runtime.runs.read(f.run.run_id)).state.permissions.workspace, access: 'read_only', main_actor: 'main', inputs: { task: 't', value: 1 }, constraints: { cost_budget: { approval_id: 'approved', currency: 'USD', limit_micros: 10 }, require_main_session_identity: true } });
  const work = await f.runtime.claimHostMain(run.run_id, { node_id: 'work', owner: 'main', request_id: 'work', control_token: run.control_token }); const dispatch = { ...work, control_token: run.control_token, request_id: 'dispatch-work', envelope_hash: 'c'.repeat(64) };
  const receipt = { invocation_id: 'work-invocation', executor: 'codex-app-server-host-main', executable_sha256: 'a'.repeat(64), model: 'fixture-main', effort: 'medium', session_id: 'session-1', call_chain_id: 'chain-1', main_actor: 'main' };
  await f.runtime.recordHostMainDispatchIntent(run.run_id, dispatch); await f.runtime.recordHostMainDispatchReceipt(run.run_id, { ...dispatch, receipt }); await f.runtime.recordHostMainUsage(run.run_id, { ...dispatch, usage: { unknown: true, input_tokens: 1 } });
  await proposeHostResult(f.runtime, run, work, completion({ ok: true })); await f.runtime.completeHostMainResult(run.run_id, { ...work, control_token: run.control_token });
  const final = await f.runtime.claimHostMain(run.run_id, { node_id: 'final', owner: 'main', request_id: 'final', control_token: run.control_token }); const finalDispatch = { ...final, control_token: run.control_token, request_id: 'dispatch-final', envelope_hash: 'd'.repeat(64) };
  await f.runtime.recordHostMainDispatchIntent(run.run_id, finalDispatch); await assert.rejects(f.runtime.recordHostMainDispatchReceipt(run.run_id, { ...finalDispatch, receipt: { ...receipt, invocation_id: 'final-invocation', session_id: 'session-2' } }), { code: 'MAIN_SESSION_CHANGED' });
});

test('finite decision contracts reject undeclared option/reference output', async t => {
  const workflow = hostWorkflow(); const work = workflow.nodes.find(node => node.id === 'semantic'); work.executor = { kind: 'provider', provider_id: fixtureProvider.id }; work.outputs_schema = { type: 'object', properties: { decision_id: { type: 'string' }, decision: { type: 'string' }, references: { type: 'array', items: { type: 'string' } } }, required: ['decision_id', 'decision', 'references'], additionalProperties: false }; work.resources = ['source/rules.md']; work.decision = { id: 'route', options: ['continue', 'stop'], required_references: ['source/rules.md'], budget: { maximum_micros: 1 } };
  workflow.nodes = workflow.nodes.filter(node => node.id !== 'double'); workflow.edges = [edge('start', 'semantic'), edge('semantic', 'final'), edge('final', 'end')]; workflow.host_tools = [];
  const f = await fixture(t, workflow, { context: { providers: [fixtureProvider] }, resources: { 'source/rules.md': 'Pinned decision rules.' } }); const lease = await claim(f, 'semantic'); await acknowledgeProvider(f.runtime, f.run, lease);
  await assert.rejects(f.runtime.completeNode(f.run.run_id, { ...lease, completion: completion({ decision_id: 'route', decision: 'invalid', references: [] }) }), { code: 'DECISION_OUTPUT_INVALID' });
});

test('provider blocked decisions fail in runtime and cannot advance to downstream tools', async t => {
  const workflow = hostWorkflow(); const work = workflow.nodes.find(node => node.id === 'semantic');
  work.executor = { kind: 'provider', provider_id: fixtureProvider.id };
  work.outputs_schema = { type: 'object', properties: { decision_id: { type: 'string' }, decision: { type: 'string' }, references: { type: 'array', items: { type: 'string' } } }, required: ['decision_id', 'decision', 'references'], additionalProperties: false };
  work.decision = { id: 'route', options: ['continue', 'blocked'], required_references: [] };
  workflow.nodes = workflow.nodes.filter(node => node.id !== 'double'); workflow.edges = [edge('start', 'semantic'), edge('semantic', 'final'), edge('final', 'end')]; workflow.host_tools = [];
  const f = await fixture(t, workflow, { context: { providers: [fixtureProvider] } });
  const lease = await claim(f, 'semantic'); await acknowledgeProvider(f.runtime, f.run, lease);
  const settled = await f.runtime.completeNode(f.run.run_id, { ...lease, completion: completion({ decision_id: 'route', decision: 'blocked', references: [] }) });
  assert.equal(settled.status, 'failed');
  assert.equal(settled.nodes.semantic.status, 'failed');
  assert.equal(settled.nodes.semantic.error.code, 'WORKFLOW_NODE_BLOCKED');
  assert.equal(settled.nodes.final.status, 'pending');
});
