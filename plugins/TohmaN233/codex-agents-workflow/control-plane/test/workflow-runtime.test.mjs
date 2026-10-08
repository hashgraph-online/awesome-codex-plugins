import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, rm, rmdir, writeFile, readFile, appendFile } from 'node:fs/promises';
import { tmpdir } from './physical-tempdir.mjs';
import { join, resolve } from 'node:path';
import { WorkflowStore } from '../lib/workflow-store.mjs';
import { WorkflowRuntime, resolvedSubagentPlan } from '../lib/workflow-runtime.mjs';
import { createDraft } from '../lib/workflow-schema.mjs';
import { canonicalJSON, digest } from '../lib/workflow-revisions.mjs';
import { decodeEvents } from '../lib/workflow-events.mjs';
import { compilePrompt } from '../lib/workflow-executor.mjs';
import { createCodexToolBroker } from '../lib/execution/codex-tool-broker.mjs';
import { WORKSPACE_SOURCE_LOCATIONS, WORKSPACE_SOURCE_LOCATIONS_SCHEMA, WORKSPACE_SOURCE_LOCATION_RULES } from '../lib/workspace-source-locations.mjs';
import { reattachAttempt } from '../lib/workflow-recovery.mjs';

const agent = id => ({ id, type: 'agent', executor: { kind: 'provider', provider_id: 'fixture-provider' }, role: 'implementer', access: 'read_only', prompt_template: '{{task}}', approval: { required: false }, retry: { max_attempts: 3 }, input_bindings: {} });
const edge = (source, target, label) => ({ id: source + '-' + target, source, target, ...(label ? { label } : {}) });
function definition(kind = 'sequential') {
  const workflow = { ...createDraft('example', 'Runtime test'), status: 'ready', finalization: { required: true, node_id: 'final' }, skill_policy: { mode: 'cooperative', implicit: 'allow', ambient_allow: [], shadowed_skill_paths: [] } };
  const controls = kind === 'sequential' ? [agent('work')] : [
    kind === 'parallel' ? { id: 'fork', type: 'parallel', join_id: 'join', failure_policy: 'collect' } : { id: 'fork', type: 'condition', cases: [{ label: 'yes', when: { op: 'eq', args: [{ path: '/inputs/choice' }, { value: true }] } }], default_label: 'no' },
    agent('a'), agent('b'), ...(kind === 'parallel' ? [{ id: 'join', type: 'join', parallel_id: 'fork' }] : []),
  ];
  workflow.nodes = [{ id: 'start', type: 'start' }, ...controls, { ...agent('final'), executor: { kind: 'main' }, role: 'finalizer' }, { id: 'end', type: 'end' }];
  workflow.edges = kind === 'sequential' ? [edge('start', 'work'), edge('work', 'final'), edge('final', 'end')] : [edge('start', 'fork'), edge('fork', 'a', 'yes'), edge('fork', 'b', 'no'), edge('a', kind === 'parallel' ? 'join' : 'final'), edge('b', kind === 'parallel' ? 'join' : 'final'), ...(kind === 'parallel' ? [edge('join', 'final')] : []), edge('final', 'end')];
  return workflow;
}
async function fixture(t, workflow = definition(), options = {}) {
  const root = await mkdtemp(join(tmpdir(), 'workflow-runtime-')); const workspace = join(root, 'workspace'); await mkdir(workspace);
  t.after(async () => { assert(resolve(root).startsWith(resolve(tmpdir()) + (process.platform === 'win32' ? '\\' : '/'))); await rm(root, { recursive: true, maxRetries: 3, retryDelay: 100 }); });
  const fixtureProvider = { id: 'fixture-provider', kind: 'openai_compatible', enabled: true, capabilities: { read: true, write: true }, config: { role: 'implementer' } };
  const context = { ...(options.context ?? {}), providers: [fixtureProvider, ...((options.context?.providers ?? []).filter(provider => provider.id !== fixtureProvider.id))] };
  const store = await new WorkflowStore(join(root, 'packs'), { validationContext: context }).initialize();
  await store.create(workflow, { resources: { 'instructions/task.md': 'Pinned synthetic task' } });
  const runtimeOptions = { workflowStore: store, runRoot: join(root, 'runs'), ...options, context };
  const runtime = await new WorkflowRuntime(runtimeOptions).initialize();
  return { root, workspace, store, runtime, runtimeOptions, start: extra => runtime.start({ workflow_id: workflow.id, workspace, access: 'read_only', main_actor: 'root', ...extra }) };
}
const payload = (output = {}, extra = {}) => ({ status: 'succeeded', summary: 'Verified by synthetic executor', structured_output: output, artifacts: [], evidence: [{ check: 'fake executor', passed: true }], changed_paths: [], outside_paths: [], ...extra });

async function hostReceiptFixture(t) {
  const output = { ok: true }, contract = {
    id: 'receipt-tool', identity: { name: 'receipt-tool', version: '1', sha256: 'a'.repeat(64) }, argv: ['receipt-tool'],
    input_schema: { type: 'object', additionalProperties: false },
    output_schema: { type: 'object', properties: { ok: { type: 'boolean' } }, required: ['ok'], additionalProperties: false },
    env_allow: [], permissions: { network: false, read_paths: [], write_paths: [] },
    output_cap_bytes: 1024, deadline_ms: 1000, idempotency: { mode: 'safe' },
  };
  const workflow = definition(); workflow.host_tools = [contract];
  workflow.nodes[1] = { id: 'work', type: 'tool', executor: { kind: 'tool', tool: contract.id },
    access: 'read_only', approval: { required: false }, retry: { max_attempts: 1 }, input_bindings: {}, outputs_schema: contract.output_schema };
  const f = await fixture(t, workflow, { context: { host_tools: [contract.id] },
    environmentResolver: async () => ({ status: 'ready', tools: [], missing: [] }) });
  const run = await f.start(), lease = await claim(f, run, 'work');
  const args = { node_id: 'work', attempt_id: lease.attempt_id, lease_token: lease.lease_token, control_token: run.control_token };
  const intent = (await f.runtime.recordHostToolIntent(run.run_id, { ...args, contract, input: {} })).receipt;
  const stored = { kind: 'host_tool_output', output }, saved = await f.runtime.runs.saveExecutorResult(run.run_id, lease.attempt_id, stored);
  const receipt = { run_id: run.run_id, node_id: 'work', attempt_id: lease.attempt_id, tool: contract.id,
    contract_sha256: intent.contract_sha256, input_sha256: intent.input_sha256,
    broker: { id: 'qualified-fixture', evidence_sha256: 'b'.repeat(64) },
    started_at: '2026-09-29T00:00:00.000Z', finished_at: '2026-09-29T00:00:00.010Z', duration_ms: 10,
    output_sha256: digest(canonicalJSON(output)), output_ref: { ...saved, bytes: Buffer.byteLength(canonicalJSON(stored)) },
    diagnostics: { message: 'Synthetic qualified receipt', sha256: digest('Synthetic qualified receipt') },
    status: 'succeeded', exit_code: 0, effects: { observed: true, changed_paths: [], outside_paths: [], artifacts: [] }, reconciliation: null };
  return { ...f, run, args, receipt };
}

test('exact Host tool receipt replay is idempotent and a conflicting qualified receipt is rejected', async t => {
  const f = await hostReceiptFixture(t);
  await f.runtime.recordHostToolReceipt(f.run.run_id, { ...f.args, receipt: f.receipt });
  const before = await f.runtime.runs.read(f.run.run_id);
  await f.runtime.recordHostToolReceipt(f.run.run_id, { ...f.args, receipt: structuredClone(f.receipt) });
  assert.deepEqual(await f.runtime.runs.read(f.run.run_id), before, 'Replay must not add a journal event or change state');
  await assert.rejects(f.runtime.recordHostToolReceipt(f.run.run_id, { ...f.args,
    receipt: { ...f.receipt, broker: { ...f.receipt.broker, id: 'different-qualified-broker' } } }), { code: 'HOST_TOOL_CONFLICT' });
  assert.deepEqual(await f.runtime.runs.read(f.run.run_id), before);
});

test('exact successful Host tool receipt replay detects corrupted stored executor output', async t => {
  const f = await hostReceiptFixture(t);
  await f.runtime.recordHostToolReceipt(f.run.run_id, { ...f.args, receipt: f.receipt });
  const before = await f.runtime.runs.read(f.run.run_id);
  await writeFile(join(f.runtime.runs.directory(f.run.run_id), f.receipt.output_ref.artifact),
    canonicalJSON({ kind: 'host_tool_output', output: { ok: false } }));
  await assert.rejects(f.runtime.recordHostToolReceipt(f.run.run_id, { ...f.args,
    receipt: { ...f.receipt, broker: { ...f.receipt.broker, id: 'different-qualified-broker' } } }),
  { code: 'HOST_TOOL_CONFLICT' });
  await assert.rejects(f.runtime.recordHostToolReceipt(f.run.run_id, { ...f.args, receipt: structuredClone(f.receipt) }),
    { code: 'EXECUTOR_RESULT_CORRUPT' });
  assert.deepEqual(await f.runtime.runs.read(f.run.run_id), before);
});

test('first Host tool receipt still validates its exact intent and durable output', async t => {
  const f = await hostReceiptFixture(t), before = await f.runtime.runs.read(f.run.run_id);
  for (const receipt of [
    { ...f.receipt, input_sha256: 'e'.repeat(64) },
    { ...f.receipt, output_ref: { ...f.receipt.output_ref, artifact: 'different.json' } },
  ]) await assert.rejects(f.runtime.recordHostToolReceipt(f.run.run_id, { ...f.args, receipt }), { code: 'HOST_TOOL_RECEIPT' });
  await assert.rejects(f.runtime.recordHostToolReceipt(f.run.run_id, { ...f.args,
    receipt: { ...f.receipt, output_sha256: 'f'.repeat(64) } }), { code: 'HOST_TOOL_OUTPUT_CORRUPT' });
  assert.deepEqual(await f.runtime.runs.read(f.run.run_id), before);
  await f.runtime.recordHostToolReceipt(f.run.run_id, { ...f.args, receipt: f.receipt });
});

test('cancelled Run persists its exact Host tool termination receipt and replay adds no event', async t => {
  const f = await hostReceiptFixture(t);
  await f.runtime.cancel(f.run.run_id, { control_token: f.run.control_token });
  const receipt = { ...f.receipt, status: 'cancelled', exit_code: null, output_ref: null, output_sha256: null,
    reconciliation: { termination_confirmed: true, evidence: [{ kind: 'synthetic-termination', sha256: 'c'.repeat(64) }] } };
  await f.runtime.recordHostToolReceipt(f.run.run_id, { ...f.args, receipt });
  const before = await f.runtime.runs.read(f.run.run_id);
  assert.equal(before.state.status, 'cancelled');
  assert.deepEqual(before.state.nodes.work.attempts[0].host_tool.receipt, receipt);
  await f.runtime.recordHostToolReceipt(f.run.run_id, { ...f.args, receipt: structuredClone(receipt) });
  assert.deepEqual(await f.runtime.runs.read(f.run.run_id), before);
});

test('a declared project_root input inherits the exact Run workspace before node binding', async t => {
  const workflow = definition();
  workflow.inputs_schema = { type: 'object', properties: { project_root: { type: 'string' } }, required: ['project_root'], additionalProperties: true };
  workflow.nodes.find(node => node.id === 'work').input_bindings.project_root = '/inputs/project_root';
  const f = await fixture(t, workflow);
  const run = await f.start({ inputs: {} });
  assert.equal(run.inputs.project_root, f.workspace);
  assert.equal((await f.runtime.runs.read(run.run_id)).state.inputs.project_root, f.workspace);
});

test('Run creation rejects a required artifact outside the granted write scope', async t => {
  const workflow=definition(),work=workflow.nodes.find(node=>node.id==='work');
  work.access='bounded_write';work.path_scope={binding:'run.allowed_paths'};
  work.required_artifacts=[{requirement_id:'final_report',path:'results/final_report.json'}];
  const f=await fixture(t,workflow);
  await assert.rejects(f.start({access:'bounded_write',allowed_paths:['other']}),{code:'REQUIRED_ARTIFACT_SCOPE'});
  assert.deepEqual(await f.runtime.runs.list(),[]);
});

test('Run creation validates direct-input fan-out write paths before any Agent dispatch', async t => {
  const workflow=definition(),work=workflow.nodes.find(node=>node.id==='work');
  workflow.inputs_schema={type:'object',additionalProperties:false,required:['items'],properties:{items:{type:'array',minItems:1,maxItems:1,items:{type:'object',additionalProperties:false,required:['write_paths'],properties:{write_paths:{type:'array',minItems:1,items:{type:'string'}}}}}}};
  work.access='bounded_write';work.path_scope={binding:'run.allowed_paths'};work.input_bindings={items:'/inputs/items'};
  work.subagent_count='auto';work.fanout={input:'items',item_name:'item',result_output:'results',distribution:'one_per_item',scheduling:'parallel',join:'all_required',write_paths_field:'write_paths'};
  work.outputs_schema={type:'object',additionalProperties:false,required:['results'],properties:{results:{type:'array',items:{type:'string'}}}};
  workflow.nodes.find(node=>node.id==='final').input_bindings={results:'/nodes/work/output/results'};
  const f=await fixture(t,workflow);
  await assert.rejects(f.start({access:'bounded_write',allowed_paths:['allowed'],inputs:{items:[{write_paths:['outside/card.ts']}]}}),{code:'SUBAGENT_ITEM_WRITE_PATHS'});
  assert.deepEqual(await f.runtime.runs.list(),[]);
  const run=await f.start({access:'bounded_write',allowed_paths:['allowed'],inputs:{items:[{write_paths:['allowed/card.ts']}]}});
  assert.equal(run.status,'running');assert.equal(run.completion_satisfied,false);assert.equal(run.recovery_required,false);
});

test('marked source locations are checked at completion and before downstream claim', async t => {
  const workflow = definition();
  const work = workflow.nodes.find(node => node.id === 'work');
  work.outputs_schema = { type: 'object', properties: { locations: structuredClone(WORKSPACE_SOURCE_LOCATIONS_SCHEMA) }, required: ['locations'], additionalProperties: false };
  work.output_validators = { locations: WORKSPACE_SOURCE_LOCATIONS };
  workflow.nodes.find(node => node.id === 'final').input_bindings.locations = '/nodes/work/output/locations';
  const f = await fixture(t, workflow);
  const content = 'export function sourcePoint() { return 1; }\n';
  await writeFile(join(f.workspace, 'source.mjs'), content);
  const run = await f.start();
  const lease = await claim(f, run, 'work');
  assert.equal(lease.prompt_template.split(WORKSPACE_SOURCE_LOCATION_RULES).length,2);
  assert.equal(compilePrompt(lease,80000).split(WORKSPACE_SOURCE_LOCATION_RULES).length,2);
  const location = { path: join(f.workspace,'source.mjs'), file_sha256: digest(content), start_line: 1, end_line: 1,
    symbol: 'sourcePoint', usage: 'Call sourcePoint to obtain the result.' };
  await assert.rejects(complete(f, run, lease, { locations: [{ ...location, file_sha256: '0'.repeat(64) }] }),
    { code: 'SOURCE_LOCATION_INVALID', reason: 'file_sha256_mismatch' });
  assert.equal((await f.runtime.get(run.run_id)).nodes.work.output, null);
  await complete(f, run, lease, { locations: [location] });
  const committed=await f.runtime.get(run.run_id);
  assert.equal(committed.nodes.work.output.locations[0].path,'source.mjs');
  await writeFile(join(f.workspace, 'source.mjs'), content + '// later edit\n');
  await assert.rejects(claim(f, run, 'final'),
    { code: 'SOURCE_LOCATION_STALE', reason: 'file_sha256_mismatch', producer_node_id: 'work' });
  assert.equal((await f.runtime.get(run.run_id)).nodes.final.status, 'ready');
  await writeFile(join(f.workspace, 'source.mjs'), content);
  const final = await claim(f, run, 'final');
  await writeFile(join(f.workspace, 'source.mjs'), content + '// changed after claim\n');
  await assert.rejects(f.runtime.recordHostMainDispatchIntent(run.run_id, {
    node_id: 'final', attempt_id: final.attempt_id, lease_token: final.lease_token,
    request_id: 'dispatch-final-stale', envelope_hash: digest(canonicalJSON(final)), control_token: run.control_token,
  }), { code: 'SOURCE_LOCATION_STALE', reason: 'file_sha256_mismatch' });
  const record = await f.runtime.runs.read(run.run_id);
  assert.equal(record.state.nodes.final.attempts.at(-1).dispatch, null);
});

async function sourceEditingRun(t, editorKind = 'provider') {
  const workflow = definition();
  const source = workflow.nodes.find(node => node.id === 'work');
  source.outputs_schema = { type: 'object', properties: { locations: structuredClone(WORKSPACE_SOURCE_LOCATIONS_SCHEMA) }, required: ['locations'], additionalProperties: false };
  source.output_validators = { locations: WORKSPACE_SOURCE_LOCATIONS };
  const edit = { ...agent('edit'), ...(editorKind === 'main' ? { executor: { kind: 'main' } } : {}),
    access: 'bounded_write', path_scope: { binding: 'run.allowed_paths' }, input_bindings: { locations: '/nodes/work/output/locations' } };
  workflow.nodes.splice(2, 0, edit);
  workflow.edges = [edge('start', 'work'), edge('work', 'edit'), edge('edit', 'final'), edge('final', 'end')];
  const f = await fixture(t, workflow);
  const content = 'export function sourcePoint() { return 1; }\n';
  await writeFile(join(f.workspace, 'source.mjs'), content);
  const run = await f.start({ access: 'bounded_write', allowed_paths: ['.'] });
  const producer = await claim(f, run, 'work');
  await complete(f, run, producer, { locations: [{ path: join(f.workspace, 'source.mjs'), file_sha256: digest(content), start_line: 1, end_line: 1, symbol: 'sourcePoint', usage: 'Update sourcePoint.' }] });
  return { f, run, content };
}

test('a dispatched source-location consumer may edit its input and continue tool authorization and completion', async t => {
  const { f, run, content } = await sourceEditingRun(t, 'main');
  const edit = await claim(f, run, 'edit');
  const binding = { node_id: edit.node_id, attempt_id: edit.attempt_id, lease_token: edit.lease_token, control_token: run.control_token };
  const request_id = `dispatch-${edit.attempt_id}`;
  const intent = { ...binding, request_id, envelope_hash: digest(canonicalJSON(edit)) };
  await f.runtime.recordHostMainDispatchIntent(run.run_id, intent);
  await f.runtime.recordHostMainDispatchReceipt(run.run_id, { ...binding, request_id, receipt: {
    invocation_id: `host-main-${edit.attempt_id}`, executor: 'codex-app-server-host-main', executable_sha256: 'a'.repeat(64),
    model: 'fixture-main', effort: 'medium', main_actor: 'root', session_id: `logical-main-${run.run_id}`, call_chain_id: `workflow-run-${run.run_id}`,
  } });
  await writeFile(join(f.workspace, 'source.mjs'), content + '// authorized edit\n');
  assert.equal((await claim(f, run, 'edit')).attempt_id, edit.attempt_id);
  assert.equal((await f.runtime.recordHostMainDispatchIntent(run.run_id, intent)).idempotent, true);
  assert.equal((await f.runtime.execution(run.run_id, binding)).attempt_id, edit.attempt_id);
  await mkdir(join(f.workspace, 'tools'));
  const broker = await createCodexToolBroker({ workspace: f.workspace, access: 'bounded_write', allowedPaths: ['.'],
    resources: [{ path: 'scripts/runner.py', bytes: 'print(1)\n', sha256: digest('print(1)\n') }],
    authorize: () => f.runtime.execution(run.run_id, binding),
    onOperation: metadata => f.runtime.recordExecutorEvent(run.run_id, { ...binding, event: { kind: 'tool_operation', metadata } }),
  });
  const result = await broker.call('materialize_workflow_resource', { path: 'scripts/runner.py', destination: 'tools/runner.py', expected_sha256: null }, 'copy-runner');
  assert.equal(JSON.parse(result.contentItems[0].text).sha256, digest('print(1)\n'));
  await broker.quiesce();
  assert.equal((await complete(f, run, edit, {}, { changed_paths: ['source.mjs', 'tools/runner.py'] })).nodes.edit.status, 'succeeded');
  assert.equal((await complete(f, run, await claim(f, run, 'final'), {}, { acceptance: { accepted: true } })).status, 'succeeded');
});

test('source-location admission rejects an edit made after claim but before dispatch', async t => {
  const { f, run, content } = await sourceEditingRun(t);
  const edit = await claim(f, run, 'edit');
  await writeFile(join(f.workspace, 'source.mjs'), content + '// external pre-dispatch edit\n');
  await assert.rejects(f.runtime.recordDispatchIntent(run.run_id, { ...edit, control_token: run.control_token,
    request_id: `dispatch-${edit.attempt_id}`, envelope_hash: digest(canonicalJSON(edit)) }),
  { code: 'SOURCE_LOCATION_STALE', reason: 'file_sha256_mismatch', producer_node_id: 'work' });
  assert.equal((await f.runtime.runs.read(run.run_id)).state.nodes.edit.attempts[0].dispatch, null);
  const restarted = await new WorkflowRuntime(f.runtimeOptions).initialize();
  await restarted.resume(run.run_id, { control_token: run.control_token, after_restart: true });
  await assert.rejects(reattachAttempt(restarted, run.run_id, { ...edit, control_token: run.control_token }, { kind: 'unsubmitted_claim' }),
    { code: 'SOURCE_LOCATION_STALE', reason: 'file_sha256_mismatch' });
});

test('a dispatched source-location consumer survives exact reattachment after its authorized edit', async t => {
  const { f, run, content } = await sourceEditingRun(t);
  const edit = await claim(f, run, 'edit');
  const binding = { node_id: edit.node_id, attempt_id: edit.attempt_id, lease_token: edit.lease_token, control_token: run.control_token };
  const request_id = `dispatch-${edit.attempt_id}`;
  await f.runtime.recordDispatchIntent(run.run_id, { ...binding, request_id, envelope_hash: digest(canonicalJSON(edit)) });
  const receipt = { task_id: `synthetic-${edit.attempt_id}` };
  await f.runtime.recordDispatchReceipt(run.run_id, { ...binding, request_id, receipt });
  await writeFile(join(f.workspace, 'source.mjs'), content + '// authorized edit before restart\n');
  const restarted = await new WorkflowRuntime(f.runtimeOptions).initialize();
  await restarted.resume(run.run_id, { control_token: run.control_token, after_restart: true });
  const reattached = await reattachAttempt(restarted, run.run_id, binding,
    { kind: 'exact_dispatch_identity', attempt_id: edit.attempt_id, dispatch_request_id: request_id, receipt });
  await restarted.resume(run.run_id, { control_token: run.control_token });
  assert.equal((await restarted.execution(run.run_id, { ...reattached.envelope, control_token: run.control_token })).attempt_id, edit.attempt_id);
  assert.equal((await complete({ ...f, runtime: restarted }, run, reattached.envelope, {}, { changed_paths: ['source.mjs'] })).nodes.edit.status, 'succeeded');
});

test('Host Main preserves its exact raw result receipt while handing off canonical source paths',async t=>{
  const workflow=definition(),work=workflow.nodes.find(node=>node.id==='work');
  work.executor={kind:'main'};
  work.outputs_schema={type:'object',properties:{locations:structuredClone(WORKSPACE_SOURCE_LOCATIONS_SCHEMA)},required:['locations'],additionalProperties:false};
  work.output_validators={locations:WORKSPACE_SOURCE_LOCATIONS};
  workflow.nodes.find(node=>node.id==='final').input_bindings.locations='/nodes/work/output/locations';
  const f=await fixture(t,workflow),content='export const identified = true;\n';
  await writeFile(join(f.workspace,'source.mjs'),content);
  const run=await f.start(),lease=await claim(f,run,'work');
  const raw={path:join(f.workspace,'source.mjs'),file_sha256:digest(content),start_line:1,end_line:1,symbol:'identified',usage:'Read the identified value.'};
  await complete(f,run,lease,{locations:[raw]});
  const record=await f.runtime.runs.read(run.run_id),attempt=record.state.nodes.work.attempts.at(-1);
  const saved=await f.runtime.runs.readExecutorResult(run.run_id,attempt.id,attempt.result_proposal.sha256);
  assert.deepEqual(saved.structured_output.locations,[raw]);
  assert.equal(record.state.nodes.work.output.locations[0].path,'source.mjs');
  assert.equal(attempt.completion.structured_output.locations[0].path,'source.mjs');
});

test('Main correction turns consume the pinned retry budget durably across retries and cancellation', async t => {
  const workflow = definition(); workflow.nodes.find(node => node.id === 'work').executor = { kind: 'main' };
  const f = await fixture(t, workflow); const run = await f.start();
  const first = await claim(f, run, 'work');
  const reserve = (runtime, lease) => runtime.reserveHostMainTurn(run.run_id, {
    node_id: 'work', attempt_id: lease.attempt_id, lease_token: lease.lease_token, control_token: run.control_token,
  });
  assert.deepEqual(await reserve(f.runtime, first), { completion_turns: 1, remaining: 2 });
  const restarted = await new WorkflowRuntime(f.runtimeOptions).initialize();
  assert.deepEqual(await reserve(restarted, first), { completion_turns: 2, remaining: 1 });
  assert.equal((await restarted.runs.read(run.run_id)).state.nodes.work.attempts[0].completion_turns, 2);
  await restarted.failNode(run.run_id, { ...first, error: { code: 'INVALID_OUTPUT', message: 'Bad source location' } });
  await restarted.retryNode(run.run_id, { ...control(run), node_id: 'work' });
  const second = await claim({ ...f, runtime: restarted }, run, 'work', { request_id: 'retry-work' });
  assert.deepEqual(await reserve(restarted, second), { completion_turns: 1, remaining: 0 });
  await restarted.failNode(run.run_id, { ...second, error: { code: 'INVALID_OUTPUT', message: 'Still invalid' } });
  await assert.rejects(restarted.retryNode(run.run_id, { ...control(run), node_id: 'work' }), { code: 'RETRY_LIMIT' });
  const setup = await fixture(t, workflow); const setupRun = await setup.start();
  for (let index = 0; index < 3; index++) {
    const lease = await claim(setup, setupRun, 'work', { request_id: `setup-${index}` });
    assert.equal((await setup.runtime.runs.read(setupRun.run_id)).state.nodes.work.attempts[index].completion_turns, 0);
    await setup.runtime.failNode(setupRun.run_id, { ...lease, error: { code: 'AUTH_REQUIRED', message: 'Failed before model dispatch' } });
    if (index < 2) await setup.runtime.retryNode(setupRun.run_id, { ...control(setupRun), node_id: 'work' });
  }
  await assert.rejects(setup.runtime.retryNode(setupRun.run_id, { ...control(setupRun), node_id: 'work' }), { code: 'RETRY_LIMIT' });
  const other = await fixture(t, workflow); const cancelled = await other.start(); const lease = await claim(other, cancelled, 'work');
  await other.runtime.cancel(cancelled.run_id, control(cancelled));
  await assert.rejects(other.runtime.reserveHostMainTurn(cancelled.run_id, { node_id: 'work', attempt_id: lease.attempt_id,
    lease_token: lease.lease_token, control_token: cancelled.control_token }), { code: 'RUN_TERMINAL' });
});

test('task dependencies reach the executor without a host inventory launch gate',async t=>{
  const workflow=definition();workflow.requirements.executables=['python'];workflow.requirements.environment=['VIDEO_TOOL_HOME'];
  const f=await fixture(t,workflow,{environmentResolver:async()=>({status:'ready',tools:[{name:'python',status:'found',path:join(t.name,'python')}],missing:[]}),environmentVerifier:async()=>[]});
  assert.equal((await f.store.snapshot(workflow.id)).workflow.status,'ready');
  const run=await f.start();assert.equal(run.status,'running');
  const envelope=await claim(f,run,'work');
  assert.match(envelope.prompt_template,/python/);assert.match(envelope.prompt_template,/VIDEO_TOOL_HOME/);
  assert.match(envelope.prompt_template,/Report unresolved dependencies with command\/error evidence/);
});
const claim = async (f, run, nodeId, extra = {}) => {
  const record = await f.runtime.runs.read(run.run_id);
  const args = { node_id: nodeId, owner: 'root', request_id: 'claim-' + nodeId, control_token: run.control_token, ...extra };
  return record.pins.root.workflow.nodes.find(node => node.id === nodeId)?.executor?.kind === 'main'
    ? f.runtime.claimHostMain(run.run_id, args)
    : f.runtime.claimNode(run.run_id, args);
};
const complete = async (f, run, envelope, output = {}, extra = {}) => {
  const record = await f.runtime.runs.read(run.run_id);
  const definition = record.pins.root.workflow.nodes.find(node => node.id === envelope.node_id);
  const completion = payload(output, extra);
  const args = { node_id: envelope.node_id, attempt_id: envelope.attempt_id, lease_token: envelope.lease_token, control_token: run.control_token };
  const current = record.state.nodes[envelope.node_id].attempts.find(item => item.id === envelope.attempt_id);
  if (definition?.executor?.kind !== 'main') {
    if (definition?.executor?.kind === 'provider' && !current.dispatch) {
      const request_id = `dispatch-${envelope.attempt_id}`;
      await f.runtime.recordDispatchIntent(run.run_id, { ...args, request_id, envelope_hash: digest(canonicalJSON(envelope)) });
      await f.runtime.recordDispatchReceipt(run.run_id, { ...args, request_id, receipt: { task_id: `fixture-${envelope.attempt_id}` } });
    }
    return f.runtime.completeNode(run.run_id, { ...args, completion });
  }
  if (!current.dispatch) {
    const request_id = `dispatch-${envelope.attempt_id}`;
    await f.runtime.recordHostMainDispatchIntent(run.run_id, { ...args, request_id, envelope_hash: digest(canonicalJSON(envelope)) });
    await f.runtime.recordHostMainDispatchReceipt(run.run_id, { ...args, request_id, receipt: {
      invocation_id: `host-main-${envelope.attempt_id}`, executor: 'codex-app-server-host-main', executable_sha256: 'a'.repeat(64),
      model: 'fixture-main', effort: 'medium', main_actor: 'root', session_id: `logical-main-${run.run_id}`, call_chain_id: `workflow-run-${run.run_id}`,
    } });
  }
  const proposal = structuredClone(completion); delete proposal.acceptance;
  const saved = await f.runtime.runs.saveExecutorResult(run.run_id, envelope.attempt_id, proposal);
  await f.runtime.recordExecutorEvent(run.run_id, { ...args, event: { kind: 'result_proposed', metadata: { ...saved, final_acceptance_required: true } } });
  return f.runtime.completeHostMainResult(run.run_id, args, { accepted: extra.acceptance?.accepted });
};

test('a per-item node retry inherits accepted item results into the new attempt',async t=>{
  const workflow=definition(),work=workflow.nodes.find(node=>node.id==='work');
  work.executor={kind:'provider',provider_id:'native-provider'};
  workflow.inputs_schema={type:'object',properties:{items:{type:'array',items:{type:'string'}}},required:['items'],additionalProperties:false};
  work.subagent_count='auto';work.fanout={input:'items',item_name:'item',result_output:'results',distribution:'one_per_item',scheduling:'parallel',max_concurrency:2,join:'all_required',result_mode:'per_item'};
  work.input_bindings={items:'/inputs/items'};work.outputs_schema={type:'object',properties:{results:{type:'array',items:{type:'string'}}},required:['results'],additionalProperties:false};
  const nativeProvider={id:'native-provider',kind:'native_agent',enabled:true,capabilities:{read:true,write:true},config:{role:'implementer',model:'gpt-test',reasoning_effort:'low',inactivity_timeout_ms:0}};
  const f=await fixture(t,workflow,{context:{providers:[nativeProvider]}}),run=await f.start({inputs:{items:['a','b','c']}}),first=await claim(f,run,'work');
  await f.runtime.runs.mutate(run.run_id,'fail',state=>{
    const node=state.nodes.work,attempt=node.attempts.find(item=>item.id===first.attempt_id);
    attempt.native_item_results={0:{agent_id:'first-child',result:'done-a'},2:{agent_id:'third-child',result:'done-c'}};
    attempt.status='failed';attempt.error={code:'ITEM_FAILED',message:'middle item failed'};attempt.finished_at=new Date().toISOString();
    node.status='failed';node.error=attempt.error;node.active_attempt_id=null;state.status='failed';state.error=attempt.error;
  });
  await f.runtime.retryNode(run.run_id,{node_id:'work',control_token:run.control_token});
  const second=await claim(f,run,'work',{request_id:'claim-work-retry'}),record=await f.runtime.runs.read(run.run_id);
  const retryAttempt=record.state.nodes.work.attempts.find(item=>item.id===second.attempt_id);
  assert.deepEqual(retryAttempt.inherited_native_item_indices,[0,2]);
  assert.deepEqual(retryAttempt.native_item_results,{0:{agent_id:'first-child',result:'done-a'},2:{agent_id:'third-child',result:'done-c'}});
});
const control = run => ({ control_token: run.control_token });

test('a required boolean validation result fails at the Host boundary',async t=>{
  const workflow=definition(),work=workflow.nodes.find(node=>node.id==='work');
  work.outputs_schema={type:'object',properties:{passed:{type:'boolean'}},required:['passed'],additionalProperties:false};
  work.completion_contract={on_missing:'block',outcome:'validated_artifact',fail_on_false:['passed']};
  const f=await fixture(t,workflow),run=await f.start(),lease=await claim(f,run,'work');
  const result=await complete(f,run,lease,{passed:false});
  assert.equal(result.status,'failed');
  assert.equal(result.nodes.work.error.code,'WORKFLOW_VALIDATION_FALSE');
  assert.notEqual(result.nodes.final.status,'ready');
});

test('whole-workspace dot scope accepts relative outputs but never parent traversal', async t => {
  const workflow = definition();
  Object.assign(workflow.nodes.find(node => node.id === 'work'), { access: 'bounded_write', path_scope: { binding: 'run.allowed_paths' } });
  const f = await fixture(t, workflow); const run = await f.start({ access: 'bounded_write', allowed_paths: ['.'] });
  const work = await claim(f, run, 'work');
  await assert.rejects(complete(f, run, work, {}, { changed_paths: ['../outside.txt'] }), { code: 'PATH_SCOPE' });
  await complete(f, run, work, {}, { changed_paths: ['nested/output.txt'] });
  assert.equal((await f.runtime.get(run.run_id)).nodes.work.status, 'succeeded');
});

test('auto fan-out resolves from runtime input and completion proves every dispatch plus the exact required artifact',async t=>{
  const workflow=definition(),worker=workflow.nodes.find(node=>node.id==='work');
  workflow.inputs_schema={type:'object',properties:{items:{type:'array',minItems:1,maxItems:32,items:{type:'string'}}},required:['items'],additionalProperties:false};
  Object.assign(worker,{executor:{kind:'provider',provider_id:'pool-provider'},access:'bounded_write',path_scope:['out'],subagent_count:'auto',input_bindings:{items:'/inputs/items'},outputs_schema:{type:'object',properties:{results:{type:'array',items:{type:'string'}}},required:['results'],additionalProperties:false},fanout:{input:'items',item_name:'item',result_output:'results',distribution:'one_per_item',scheduling:'parallel',max_concurrency:1,join:'all_required'},required_artifacts:[{requirement_id:'rendered_output',path:'out/result.json'}]});
  const provider={id:'pool-provider',kind:'native_agent',enabled:true,capabilities:{read:true,write:true},config:{role:'implementer'}};
  const f=await fixture(t,workflow,{context:{providers:[provider]}}),run=await f.start({inputs:{items:['first','second']},access:'bounded_write',allowed_paths:['out']}),work=await claim(f,run,'work');
  assert.deepEqual(work.subagents,{configured_count:'auto',resolved_count:2,fanout:worker.fanout,items:['first','second']});
  const dispatch={...work,...control(run),request_id:'dispatch-pool',envelope_hash:digest(canonicalJSON(work))};
  await f.runtime.recordDispatchIntent(run.run_id,dispatch);
  await assert.rejects(f.runtime.recordDispatchReceipt(run.run_id,{...dispatch,receipt:{task_id:'pool-task'}}),{code:'SUBAGENT_POOL_RECEIPT'});
  const dispatchIds=['task-first','task-second'],subagentPlan={resolved_count:2,input_sha256:digest(canonicalJSON(['first','second'])),assignments:[{dispatch_id:'task-first',items_sha256:digest(canonicalJSON(['first']))},{dispatch_id:'task-second',items_sha256:digest(canonicalJSON(['second']))}]};
  await assert.rejects(f.runtime.recordDispatchReceipt(run.run_id,{...dispatch,receipt:{task_id:'pool-task',subagent_dispatch_ids:dispatchIds,subagent_plan:{...subagentPlan,input_sha256:'0'.repeat(64)}}}),{code:'SUBAGENT_POOL_RECEIPT'});
  await f.runtime.recordDispatchReceipt(run.run_id,{...dispatch,receipt:{task_id:'pool-task',subagent_dispatch_ids:dispatchIds,subagent_plan:subagentPlan}});
  const poolEvidence={kind:'subagent_pool',resolved_count:2,dispatch_ids:['task-first','task-second']};
  await assert.rejects(complete(f,run,work,{results:['a','b']},{changed_paths:['out/other.json'],evidence:[poolEvidence]}),{code:'REQUIRED_ARTIFACT_MISSING'});
  await assert.rejects(complete(f,run,work,{results:['a','b']},{changed_paths:['out/result.json']}),{code:'SUBAGENT_POOL_EVIDENCE'});
  const childEvidence=dispatchIds.map((dispatch_id,result_index)=>({kind:'managed_native_result',dispatch_id,result_index,result_sha256:digest(canonicalJSON(result_index===0?'a':'b')),thread_id:`thread-${result_index}`,turn_id:`turn-${result_index}`}));
  await assert.rejects(complete(f,run,work,{results:['a','b']},{changed_paths:['out/result.json'],evidence:[poolEvidence,...childEvidence]}),{code:'SUBAGENT_POOL_EVIDENCE'});
  const trustedResults=childEvidence.map(({dispatch_id,result_index,result_sha256,thread_id,turn_id})=>({dispatch_id,result_index,result_sha256,thread_id,turn_id}));
  await assert.rejects(f.runtime.recordManagedNativeResults(run.run_id,{...work,...control(run),results:trustedResults.map((item,index)=>index?item:{...item,dispatch_id:'replacement-first'})}),{code:'MANAGED_NATIVE_RESULT_RECEIPT'});
  await f.runtime.recordManagedNativeResults(run.run_id,{...work,...control(run),results:trustedResults});
  await assert.rejects(complete(f,run,work,{results:['a','b']},{changed_paths:['out/result.json'],evidence:[{...poolEvidence,dispatch_ids:['replacement-first','replacement-second']},...childEvidence]}),{code:'SUBAGENT_POOL_EVIDENCE'});
  await assert.rejects(complete(f,run,work,{results:['a']},{changed_paths:['out/result.json'],evidence:[poolEvidence,...childEvidence]}),{code:'SUBAGENT_FANOUT_RESULT'});
  await assert.rejects(complete(f,run,work,{results:['a','b']},{changed_paths:['out/result.json'],evidence:[poolEvidence,childEvidence[0]]}),{code:'SUBAGENT_POOL_EVIDENCE'});
  await assert.rejects(complete(f,run,work,{results:['a','b']},{changed_paths:['out/result.json'],evidence:[poolEvidence,...childEvidence.map(({thread_id,turn_id,...item})=>item)]}),{code:'SUBAGENT_POOL_EVIDENCE'});
  await assert.rejects(complete(f,run,work,{results:['a','b']},{changed_paths:['out/result.json'],evidence:[poolEvidence,{...childEvidence[0],thread_id:'substituted-thread'},childEvidence[1]]}),{code:'SUBAGENT_POOL_EVIDENCE'});
  await assert.rejects(complete(f,run,work,{results:['a','b']},{changed_paths:['out/result.json'],evidence:[poolEvidence,{...childEvidence[0],turn_id:childEvidence[1].turn_id},{...childEvidence[1],turn_id:childEvidence[0].turn_id}]}),{code:'SUBAGENT_POOL_EVIDENCE'});
  const done=await complete(f,run,work,{results:['a','b']},{changed_paths:['out/result.json'],evidence:[poolEvidence,...childEvidence]});
  assert.equal(done.nodes.work.status,'succeeded');
});

test('fixed fan-out rejects more sub-Agents than runtime items before dispatch',async t=>{
  const workflow=definition(),worker=workflow.nodes.find(node=>node.id==='work');
  workflow.inputs_schema={type:'object',properties:{items:{}},required:['items'],additionalProperties:false};
  Object.assign(worker,{executor:{kind:'provider',provider_id:'pool-provider'},subagent_count:3,input_bindings:{items:'/inputs/items'},outputs_schema:{type:'object',properties:{results:{type:'array',items:{type:'string'}}},required:['results'],additionalProperties:false},fanout:{input:'items',item_name:'item',result_output:'results',distribution:'partition',scheduling:'parallel',join:'all_required'}});
  const provider={id:'pool-provider',kind:'openai_compatible',enabled:true,capabilities:{read:true,write:false},config:{role:'implementer'}};
  const f=await fixture(t,workflow,{context:{providers:[provider]}}),run=await f.start({inputs:{items:['first','second']}});
  await assert.rejects(claim(f,run,'work'),{code:'SUBAGENT_FANOUT_INPUT'});
});

test('automatic partition fan-out assigns at most the declared batch size per Agent', () => {
  const definition = { subagent_count: 'auto', input_bindings: { jobs: '/inputs/jobs' },
    fanout: { input: 'jobs', distribution: 'partition', batch_size: 20 } };
  for (const [size, expected] of [[1, [1]], [20, [20]], [21, [20, 1]], [31, [20, 11]]]) {
    const jobs = Array.from({ length: size }, (_, index) => index);
    const plan = resolvedSubagentPlan(definition, { inputs: { jobs }, nodes: {} });
    assert.equal(plan.count, expected.length);
    assert.deepEqual(plan.assignments.map(items => items.length), expected);
    assert.deepEqual(plan.assignments.flat(), jobs);
  }
});

test('a producer cannot report success with an empty list required by its direct fan-out consumer', async t => {
  const workflow = definition();
  const producer = workflow.nodes.find(node => node.id === 'work');
  producer.outputs_schema = { type: 'object', properties: { jobs: { type: 'array', items: { type: 'string' } } },
    required: ['jobs'], additionalProperties: false };
  const pool = { ...agent('pool'), subagent_count: 'auto', input_bindings: { items: '/nodes/work/output/jobs' },
    fanout: { input: 'items', item_name: 'item', result_output: 'results', distribution: 'one_per_item', scheduling: 'parallel', join: 'all_required' },
    outputs_schema: { type: 'object', properties: { results: { type: 'array', items: { type: 'string' } } }, required: ['results'], additionalProperties: false } };
  workflow.nodes.splice(workflow.nodes.findIndex(node => node.id === 'final'), 0, pool);
  workflow.edges = [edge('start', 'work'), edge('work', 'pool'), edge('pool', 'final'), edge('final', 'end')];
  const f = await fixture(t, workflow), run = await f.start(), lease = await claim(f, run, 'work');
  await assert.rejects(complete(f, run, lease, { jobs: [] }), { code: 'SUBAGENT_FANOUT_INPUT' });
  assert.equal((await f.runtime.get(run.run_id)).nodes.pool.status, 'pending');
});

test('executor event journal accepts narrow metadata under controller authority and never revives a cancelled lease', async t => {
  const f = await fixture(t); const run = await f.start(); const work = await claim(f, run, 'work');
  const args = { node_id: work.node_id, attempt_id: work.attempt_id, lease_token: work.lease_token, control_token: run.control_token,
    event: { kind: 'session_state', metadata: { status: 'auth_required' } } };
  await assert.rejects(f.runtime.recordExecutorEvent(run.run_id, { ...args, control_token: 'wrong' }), { code: 'RUN_AUTHORITY' });
  await assert.rejects(f.runtime.recordExecutorEvent(run.run_id, { ...args, event: { kind: 'codex_event', metadata: { authUrl: 'sensitive' } } }), { code: 'EXECUTOR_EVENT_SCHEMA' });
  await assert.rejects(f.runtime.recordExecutorEvent(run.run_id, { ...args, event: { kind: 'session_state', metadata: { status: { authUrl: 'sensitive' } } } }), { code: 'EXECUTOR_EVENT_SCHEMA' });
  await f.runtime.recordExecutorEvent(run.run_id, { ...args, event: { kind: 'tool_operation', metadata: { call_id: 'bad-range', tool: 'read_workflow_resource_range', path: 'source/SKILL.md', phase: 'rejected', code: 'CODEX_RESOURCE_RANGE', diagnostic: 'Requested range exceeds the host bound' } } });
  await f.runtime.recordExecutorEvent(run.run_id, { ...args, event: { kind: 'tool_operation', metadata: { call_id: 'materialize', tool: 'materialize_workflow_resource', path: 'tools/runner.py', phase: 'intent', before_sha256: null, after_sha256: digest('runner'), source_sha256: digest('runner') } } });
  await assert.rejects(f.runtime.recordExecutorEvent(run.run_id, { ...args, event: { kind: 'tool_operation', metadata: { call_id: 'bad-evidence', tool: 'read_workflow_resource_range', path: 'source/SKILL.md', phase: 'read' } } }), { code: 'EXECUTOR_EVENT_SCHEMA' });
  await f.runtime.recordExecutorEvent(run.run_id, { ...args, event: { kind: 'semantic_blocked', metadata: { correction: 0, reason: 'recoverable tool error', thread_id: 'thread-1', turn_id: 'turn-1' } } });
  await f.runtime.recordExecutorEvent(run.run_id, { ...args, event: { kind: 'required_artifacts_missing', metadata: { correction: 0, paths: 'compressed_video.mp4, compression_report.json', thread_id: 'thread-1', turn_id: 'turn-1' } } });
  await f.runtime.recordExecutorEvent(run.run_id, args);
  await f.runtime.recordExecutorEvent(run.run_id,{...args,event:{kind:'tool_operation',metadata:{call_id:'image',tool:'view_workspace_image',path:'card.png',phase:'read',sha256:'a'.repeat(64),mime:'image/png',bytes:123}}});
  await f.runtime.recordExecutorEvent(run.run_id,{...args,event:{kind:'scope_violation',metadata:{artifact:'artifact-scope.bin',sha256:'b'.repeat(64),bytes:100,changed_count:2,outside_count:1}}});
  await f.runtime.recordExecutorEvent(run.run_id,{...args,event:{kind:'workspace_unreadable_authorized_path',metadata:{path:'work/tmp/private',kind:'directory',error_code:'EPERM',coverage:'authorized_boundary_only',dev:'3392694177',ino:'1688849860430969',birthtime_ms:'1790457251294.8755',phase:'completion'}}});
  await f.runtime.cancel(run.run_id, control(run));
  await f.runtime.recordExecutorEvent(run.run_id, { ...args, event: { kind: 'session_state', metadata: { status: 'cancelled' } } });
  const state = await f.runtime.get(run.run_id); assert.equal(state.status, 'cancelled'); assert.equal(state.nodes.work.attempts[0].executor_event_count, 9);
  await assert.rejects(f.runtime.execution(run.run_id, args), { code: 'STALE_LEASE' });
});

test('concurrent local executors serialize one Run journal across runtime instances without losing events', async t => {
  const f = await fixture(t, definition('parallel')); const run = await f.start();
  const other = await new WorkflowRuntime(f.runtimeOptions).initialize();
  const [a, b] = await Promise.all(['a', 'b'].map(node => claim(f, run, node)));
  const calls = Array.from({ length: 24 }, (_, index) => {
    const lease = index % 2 ? a : b; const runtime = index % 2 ? f.runtime : other;
    return runtime.recordExecutorEvent(run.run_id, { node_id: lease.node_id, attempt_id: lease.attempt_id, lease_token: lease.lease_token, control_token: run.control_token,
      event: { kind: 'session_state', metadata: { status: 'synthetic-' + index } } });
  });
  await Promise.all(calls);
  const state = await other.get(run.run_id); assert.equal(state.nodes.a.attempts[0].executor_event_count, 12); assert.equal(state.nodes.b.attempts[0].executor_event_count, 12);
  const events = await other.events(run.run_id, control(run)); assert.equal(events.filter(event => event.kind === 'executor_event').length, 24);
});

test('journal releases sequential nodes, binds leases, rejects conflicting duplicates and requires main acceptance', async t => {
  const f = await fixture(t); const run = await f.start();
  assert.deepEqual((await f.runtime.next(run.run_id)).ready, ['work']);
  await assert.rejects(claim(f, run, 'final'), { code: 'NODE_NOT_READY' });
  await assert.rejects(claim(f, run, 'work', { control_token: 'wrong' }), { code: 'RUN_AUTHORITY' });
  const work = await claim(f, run, 'work');
  const same = await claim(f, run, 'work'); assert.equal(same.idempotent, true); assert.equal(same.lease_token, work.lease_token);
  await assert.rejects(complete(f, run, { ...work, lease_token: 'wrong' }), { code: 'LEASE_INVALID' });
  const done = await complete(f, run, work, { value: 42 });
  assert.equal(done.nodes.work.status, 'succeeded'); assert.equal(done.nodes.final.status, 'ready');
  assert.equal((await complete(f, run, work, { value: 42 })).sequence, done.sequence);
  await assert.rejects(complete(f, run, work, { value: 43 }), { code: 'COMPLETION_CONFLICT' });
  await assert.rejects(f.runtime.claimNode(run.run_id, { node_id: 'final', owner: 'root', request_id: 'generic-main-claim', control_token: run.control_token }), { code: 'HOST_MAIN_LIFECYCLE_REQUIRED' });
  await assert.rejects(claim(f, run, 'final', { owner: 'worker' }), { code: 'FINALIZER_AUTHORITY' });
  const final = await claim(f, run, 'final');
  await assert.rejects(f.runtime.completeNode(run.run_id, { node_id: final.node_id, attempt_id: final.attempt_id, lease_token: final.lease_token, completion: payload({}, { acceptance: { accepted: true } }) }), { code: 'HOST_MAIN_LIFECYCLE_REQUIRED' });
  await assert.rejects(complete(f, run, final), { code: 'FINAL_ACCEPTANCE_REQUIRED' });
  assert.equal((await complete(f, run, final, {}, { acceptance: { accepted: true } })).status, 'succeeded');
  const publicState = await f.runtime.get(run.run_id); assert.equal(publicState.control_hash, undefined); assert.equal(publicState.nodes.work.attempts[0].lease_hash, undefined);
  const events = await f.runtime.events(run.run_id, { ...control(run), after_sequence: 1 }); assert.deepEqual(events.map(e => e.kind), ['claim', 'dispatch_intent', 'dispatch_receipt', 'complete', 'claim', 'dispatch_intent', 'dispatch_receipt', 'executor_event', 'executor_event', 'complete']);
});

test('conditional skip and control failures persist without losing upstream completion', async t => {
  const f = await fixture(t, definition('condition')); const run = await f.start({ inputs: { choice: false } });
  assert.equal(run.nodes.a.status, 'skipped'); assert.deepEqual((await f.runtime.next(run.run_id)).ready, ['b']);
  await complete(f, run, await claim(f, run, 'b')); assert.deepEqual((await f.runtime.next(run.run_id)).ready, ['final']);
  const w = definition('condition'); w.nodes.splice(1, 0, agent('work')); w.edges = w.edges.filter(e => e.source !== 'start'); w.edges.push(edge('start', 'work'), edge('work', 'fork'));
  w.nodes.find(n => n.id === 'fork').cases[0].when = { op: 'eq', args: [{ path: '/nodes/work/output/missing' }, { value: true }] };
  const f2 = await fixture(t, w); const r2 = await f2.start();
  const result = await complete(f2, r2, await claim(f2, r2, 'work'));
  assert.equal(result.status, 'failed'); assert.equal(result.nodes.work.status, 'succeeded'); assert.equal(result.nodes.fork.status, 'failed'); assert.equal(result.nodes.fork.error.code, 'CONDITION_INPUT_MISSING');
  const restarted = await new WorkflowRuntime(f2.runtimeOptions).initialize(); assert.equal((await restarted.get(r2.run_id)).nodes.work.status, 'succeeded');
});

test('parallel collect waits for all branches and exposes failure at main acceptance', async t => {
  const f = await fixture(t, definition('parallel')); const run = await f.start();
  assert.deepEqual((await f.runtime.next(run.run_id)).ready, ['a', 'b']);
  const a = await claim(f, run, 'a'); const b = await claim(f, run, 'b');
  await f.runtime.failNode(run.run_id, { ...a, error: { code: 'SYNTHETIC', message: 'Expected failure' } });
  assert.equal((await f.runtime.get(run.run_id)).nodes.join.status, 'pending');
  const result = await complete(f, run, b);
  assert.deepEqual(result.nodes.join.output.failures, ['a']); assert.equal(result.nodes.final.status, 'ready');
  assert.equal((await complete(f, run, await claim(f, run, 'final'), {}, { acceptance: { accepted: true } })).status, 'succeeded');
});

test('parallel fail-fast fences peers, retry is explicit, old leases cannot finish', async t => {
  const w = definition('parallel'); w.nodes.find(n => n.id === 'fork').failure_policy = 'fail_fast';
  const f = await fixture(t, w); const run = await f.start(); const a = await claim(f, run, 'a'); const b = await claim(f, run, 'b');
  const result = await f.runtime.failNode(run.run_id, { ...a, error: { message: 'Failed branch' } });
  assert.equal(result.status, 'failed'); assert.equal(result.nodes.b.status, 'interrupted');
  await assert.rejects(complete(f, run, b), { code: 'STALE_LEASE' });
  await f.runtime.retryNode(run.run_id, { ...control(run), node_id: 'a' });
  await f.runtime.retryNode(run.run_id, { ...control(run), node_id: 'b' });
  const retryA = await claim(f, run, 'a', { request_id: 'retry-a' });
  assert.notEqual(retryA.attempt_id, a.attempt_id);
  await assert.rejects(complete(f, run, a), { code: 'STALE_LEASE' });
});

test('approval binding, denial/reapproval, human gate and pause do not release unauthorized work', async t => {
  const w = definition(); w.nodes.find(n => n.id === 'work').approval.required = true;
  const f = await fixture(t, w); const run = await f.start(); assert.equal(run.status, 'blocked');
  await assert.rejects(claim(f, run, 'work'), { code: 'NODE_NOT_READY' });
  await f.runtime.approve(run.run_id, { ...control(run), approval_id: 'work:1', decision: false });
  await assert.rejects(f.runtime.approve(run.run_id, { ...control(run), approval_id: 'work:1', decision: true }), { code: 'APPROVAL_CONFLICT' });
  await f.runtime.retryNode(run.run_id, { ...control(run), node_id: 'work' });
  await f.runtime.pause(run.run_id, control(run));
  await f.runtime.approve(run.run_id, { ...control(run), approval_id: 'work:2', decision: true });
  assert.deepEqual((await f.runtime.next(run.run_id)).ready, []);
  await f.runtime.resume(run.run_id, control(run));
  const lease = await claim(f, run, 'work');
  const request_id = `dispatch-${lease.attempt_id}`;
  await f.runtime.recordDispatchIntent(run.run_id, { ...lease, ...control(run), request_id, envelope_hash: digest(canonicalJSON(lease)) });
  await f.runtime.recordDispatchReceipt(run.run_id, { ...lease, ...control(run), request_id, receipt: { task_id: `fixture-${lease.attempt_id}` } });
  await f.runtime.pause(run.run_id, control(run));
  const result = await complete(f, run, lease); assert.equal(result.status, 'paused'); assert.equal(result.nodes.final.status, 'pending');
  await f.runtime.resume(run.run_id, control(run)); assert.deepEqual((await f.runtime.next(run.run_id)).ready, ['final']);
  const h = definition(); Object.assign(h.nodes.find(n => n.id === 'work'), { type: 'human_gate', executor: { kind: 'human' } });
  const f2 = await fixture(t, h); const r2 = await f2.start();
  const approved = await f2.runtime.approve(r2.run_id, { ...control(r2), approval_id: 'work:1', decision: true });
  assert.equal(approved.nodes.work.status, 'succeeded'); assert.equal(approved.nodes.work.attempts.length, 0);
});

test('restart fences dispatched work; reconciliation required; cancel records pending external cancellation', async t => {
  const f = await fixture(t); const run = await f.start(); const work = await claim(f, run, 'work');
  const dispatch = { ...work, ...control(run), request_id: 'dispatch-1', envelope_hash: digest(canonicalJSON(work)) };
  await f.runtime.recordDispatchIntent(run.run_id, dispatch);
  await f.runtime.resume(run.run_id, { ...control(run), after_restart: true });
  await assert.rejects(f.runtime.resume(run.run_id, control(run)), { code: 'INTERRUPTED_NODES' });
  await assert.rejects(f.runtime.retryNode(run.run_id, { ...control(run), node_id: 'work' }), { code: 'DISPATCH_RECONCILIATION_REQUIRED' });
  const late = await f.runtime.recordDispatchReceipt(run.run_id, { ...dispatch, receipt: { task_id: 'task-1' } });
  assert.equal(late.nodes.work.attempts[0].dispatch.cancellation_pending, true);
  await assert.rejects(f.runtime.recordDispatchReceipt(run.run_id, { ...dispatch, receipt: { task_id: 'task-2' } }), { code: 'DISPATCH_CONFLICT' });
  await f.runtime.retryNode(run.run_id, { ...control(run), node_id: 'work', reconciliation: { attempt_id: work.attempt_id, dispatch_request_id: 'dispatch-1', outcome: 'terminated', evidence: ['executor confirmed task-1 terminated'] } });
  const second = await claim(f, run, 'work', { request_id: 'claim-2' });
  await f.runtime.recordDispatchIntent(run.run_id, { ...second, ...control(run), request_id: 'dispatch-2', envelope_hash: digest(canonicalJSON(second)) });
  const cancelled = await f.runtime.cancel(run.run_id, control(run)); assert.equal(cancelled.status, 'cancelled'); assert.equal(cancelled.nodes.work.attempts[1].dispatch.cancellation_pending, true);
  await assert.rejects(complete(f, run, second), { code: 'STALE_LEASE' });
});

test('Run pins survive preset edit/delete and reject tampered resources', async t => {
  const f = await fixture(t); const run = await f.start();
  const head = await f.store.snapshot('example'); await f.store.rename('example', 'Changed preset', head.revision_hash);
  const edited = await f.store.snapshot('example'); await f.store.delete('example', edited.revision_hash);
  const work = await claim(f, run, 'work'); assert.equal(work.workflow_revision, run.workflow_revision);
  const record = await f.runtime.runs.read(run.run_id); const object = join(f.runtime.runs.directory(run.run_id), 'objects', record.pins.resources[0].sha256);
  await writeFile(object, 'tampered'); await assert.rejects(f.runtime.get(run.run_id), { code: 'RUN_RESOURCE_CORRUPT' });
});

test('journal-only transitions ignore legacy cache; stale CAS and torn/corrupt journal fail closed', async t => {
  const f = await fixture(t); const run = await f.start(); const directory = f.runtime.runs.directory(run.run_id); const cache = join(directory, 'run.json');
  await mkdir(cache); // An unusable legacy cache cannot break authoritative commits.
  await claim(f, run, 'work');
  const repeated = await claim(f, run, 'work'); assert.equal(repeated.idempotent, true); assert.equal((await f.runtime.get(run.run_id)).nodes.work.status, 'claimed');
  await rmdir(cache);
  await assert.rejects(claim(f, run, 'work', { expected_sequence: 1 }), { code: 'RUN_SEQUENCE_CONFLICT' });
  const journal = join(directory, 'events.jsonl'); await appendFile(journal, '{"uncommitted":');
  await assert.rejects(f.runtime.get(run.run_id), { code: 'RUN_JOURNAL_TORN' });
  const beforeUnauthorizedRecovery = await readFile(journal);
  await assert.rejects(f.runtime.resume(run.run_id, { control_token: 'wrong', after_restart: true }), { code: 'RUN_AUTHORITY' });
  assert.deepEqual(await readFile(journal), beforeUnauthorizedRecovery);
  const recovered = await f.runtime.resume(run.run_id, { ...control(run), after_restart: true }); assert.equal(recovered.nodes.work.status, 'interrupted');
  const validBytes = await readFile(journal); const decoded = decodeEvents(validBytes); assert.equal(decoded.events.at(-1).kind, 'recover');
  await writeFile(journal, validBytes.toString().replace('"kind":"claim"', '"kind":"pause"'));
  await assert.rejects(f.runtime.resume(run.run_id, { ...control(run), after_restart: true }), { code: 'RUN_JOURNAL_CORRUPT' });
});

test('Strict and parallel writes fail closed; serial write scope narrows Run authorization', async t => {
  const w = definition(); w.skill_policy.mode = 'strict'; w.skill_policy.implicit = 'deny';
  const f = await fixture(t, w); await assert.rejects(f.start(), { code: 'STRICT_UNAVAILABLE' });
  const parallel = definition('parallel'); Object.assign(parallel.nodes.find(n => n.id === 'a'), { access: 'bounded_write', path_scope: ['src'] });
  const f2 = await fixture(t, parallel); await assert.rejects(f2.start({ access: 'bounded_write', allowed_paths: ['src'] }), { code: 'PARALLEL_WRITE_UNAVAILABLE' });
  const serial = definition(); Object.assign(serial.nodes.find(n => n.id === 'work'), { access: 'bounded_write', path_scope: ['src'] });
  const f3 = await fixture(t, serial); await assert.rejects(f3.start(), { code: 'NODE_WRITE_UNAUTHORIZED' });
  const r3 = await f3.start({ access: 'bounded_write', allowed_paths: ['src/lib'] }); const lease = await claim(f3, r3, 'work'); assert.deepEqual(lease.effective_allowed_paths, ['src/lib']);
  await assert.rejects(complete(f3, r3, lease, {}, { changed_paths: ['src/other.js'] }), { code: 'SCOPE_VIOLATION' });
  assert.equal((await complete(f3, r3, lease, {}, { changed_paths: ['src/lib/a.js'] })).nodes.work.status, 'succeeded');
});

test('input and output contracts validate actual data, bind final output and reject unsupported schemas', async t => {
  const w = definition();
  w.inputs_schema = { type: 'object', properties: { task: { type: 'string', minLength: 1 } }, required: ['task'], additionalProperties: false };
  w.nodes.find(n => n.id === 'work').outputs_schema = { type: 'object', required: ['count'], properties: { count: { type: 'integer', minimum: 1 } } };
  w.output_bindings = { count: '/nodes/work/output/count' }; w.outputs_schema = { type: 'object', required: ['count'], properties: { count: { type: 'integer' } } };
  const f = await fixture(t, w); await assert.rejects(f.start(), { code: 'DATA_INVALID' });
  const run = await f.start({ inputs: { task: 'Synthetic task' } }); const work = await claim(f, run, 'work');
  await assert.rejects(complete(f, run, work, { count: 0.5 }), { code: 'DATA_INVALID' });
  await complete(f, run, work, { count: 3 });
  const result = await complete(f, run, await claim(f, run, 'final'), {}, { acceptance: { accepted: true } }); assert.deepEqual(result.output, { count: 3 });
  const bad = definition(); bad.inputs_schema = { type: 'object', patternProperties: {} };
  await assert.rejects(f.store.save('example', bad, { expected_revision: (await f.store.snapshot('example')).revision_hash }), error => error.code === 'WORKFLOW_NOT_READY');
});

test('pinned resource materialization journals through the real Run event contract', async t => {
  const workflow = definition(); Object.assign(workflow.nodes.find(node => node.id === 'work'), { access: 'bounded_write', path_scope: { binding: 'run.allowed_paths' } });
  const f = await fixture(t, workflow); await mkdir(join(f.workspace, 'tools'));
  const run = await f.start({ access: 'bounded_write', allowed_paths: ['tools'] });
  const work = await claim(f, run, 'work');
  const binding = { node_id: work.node_id, attempt_id: work.attempt_id, lease_token: work.lease_token, control_token: run.control_token };
  const bytes = 'print("runner")\n';
  const broker = await createCodexToolBroker({ workspace: f.workspace, access: 'bounded_write', allowedPaths: ['tools'],
    resources: [{ path: 'scripts/runner.py', bytes, sha256: digest(bytes) }],
    authorize: () => f.runtime.execution(run.run_id, binding),
    onOperation: metadata => f.runtime.recordExecutorEvent(run.run_id, { ...binding, event: { kind: 'tool_operation', metadata } }),
  });
  const result = await broker.call('materialize_workflow_resource', { path: 'scripts/runner.py', destination: 'tools/runner.py', expected_sha256: null }, 'copy-runner');
  assert.equal(JSON.parse(result.contentItems[0].text).sha256, digest(bytes));
  assert.equal(await readFile(join(f.workspace, 'tools', 'runner.py'), 'utf8'), bytes);
  assert.equal((await f.runtime.get(run.run_id)).nodes.work.attempts[0].executor_event_count, 2);
  await broker.quiesce();
});

test('ordinary finalizer commits its own persisted accepted=true output without a human gate', async t => {
  const workflow = definition();
  workflow.nodes.find(node => node.id === 'final').outputs_schema = { type: 'object', properties: { accepted: { type: 'boolean' } }, required: ['accepted'], additionalProperties: false };
  const f = await fixture(t, workflow); const run = await f.start();
  await complete(f, run, await claim(f, run, 'work'));
  const final = await claim(f, run, 'final');
  const args = { node_id: final.node_id, attempt_id: final.attempt_id, lease_token: final.lease_token, control_token: run.control_token };
  const request_id = `dispatch-${final.attempt_id}`;
  await f.runtime.recordHostMainDispatchIntent(run.run_id, { ...args, request_id, envelope_hash: digest(canonicalJSON(final)) });
  await f.runtime.recordHostMainDispatchReceipt(run.run_id, { ...args, request_id, receipt: {
    invocation_id: `host-main-${final.attempt_id}`, executor: 'codex-app-server-host-main', executable_sha256: 'a'.repeat(64),
    model: 'fixture-main', effort: 'medium', main_actor: 'root', session_id: `logical-main-${run.run_id}`, call_chain_id: `workflow-run-${run.run_id}`,
  } });
  const saved = await f.runtime.runs.saveExecutorResult(run.run_id, final.attempt_id, payload({ accepted: true }));
  await f.runtime.recordExecutorEvent(run.run_id, { ...args, event: { kind: 'result_proposed', metadata: { ...saved, final_acceptance_required: false } } });
  assert.equal((await f.runtime.completeHostMainResult(run.run_id, args)).status, 'succeeded');
});

test('finite output contracts enforce safe patterns, exclusive minima and unique items', async t => {
  const w=definition();w.nodes.find(n=>n.id==='work').outputs_schema={type:'object',required:['paths','duration'],properties:{paths:{type:'array',uniqueItems:true,items:{type:'string',pattern:'^edit/[^/]+[.]json$'}},duration:{type:'number',exclusiveMinimum:0}},additionalProperties:false};
  const f=await fixture(t,w);const run=await f.start();const work=await claim(f,run,'work');
  await assert.rejects(complete(f,run,work,{paths:['edit/a.json','edit/a.json'],duration:1}),{code:'DATA_INVALID'});
  await assert.rejects(complete(f,run,work,{paths:['outside/a.json'],duration:1}),{code:'DATA_INVALID'});
  await assert.rejects(complete(f,run,work,{paths:['edit/a.json'],duration:0}),{code:'DATA_INVALID'});
  assert.equal((await complete(f,run,work,{paths:['edit/a.json'],duration:0.1})).nodes.work.status,'succeeded');
  const unsafe=definition();unsafe.inputs_schema={type:'string',pattern:'^(a+)+$'};
  await assert.rejects(f.store.save('example',unsafe,{expected_revision:(await f.store.snapshot('example')).revision_hash}),error=>error.code==='WORKFLOW_NOT_READY');
});

test('prompt compilation decodes serialized JSON bindings once instead of double escaping them', () => {
  const proposal_json=JSON.stringify({items:Array.from({length:200},(_,index)=>({id:index,path:`edit/${index}.json`}))});
  const envelope={prompt_template:'Review proposal_json.',inputs:{proposal_json},context_projection:{references:['analysis/request.txt']},constraints:{},completion_contract:{on_missing:'block',outcome:'review'}};
  const oldSize=envelope.prompt_template.length+canonicalJSON(envelope.inputs).length;
  const prompt=compilePrompt(envelope,oldSize-100);
  assert.match(prompt,/"proposal_json":\{"items":/);assert(!prompt.includes('\\"items\\"'));assert.match(prompt,/"on_missing":"block","outcome":"review"/);
  assert.match(prompt,/bound task may describe downstream work/);
});

test('independent authoring review keeps a large canonical proposal out of the prompt',()=>{
  const proposal={nodes:[{id:'work',prompt_template:'x'.repeat(90000)}]};
  const inline={prompt_template:'Review.',inputs:{proposal},context_projection:{references:['analysis/review-request.txt']},constraints:{}};
  assert.throws(()=>compilePrompt(inline,80000),{code:'PROMPT_LIMIT'});
  const resourceBacked={...inline,inputs:{},context_projection:{references:['analysis/review-request.txt','__authoring__/review-proposal.json']}};
  const prompt=compilePrompt(resourceBacked,80000);
  assert.match(prompt,/"__authoring__\/review-proposal\.json"/);
  assert.doesNotMatch(prompt,/x{100}/);
});


test('Run snapshot shares one validated read and preserves event authorization', async t => {
  const f = await fixture(t); const run = await f.start();
  const read = f.runtime.runs.read.bind(f.runtime.runs); let reads = 0;
  f.runtime.runs.read = async id => { reads++; return read(id); };
  const snapshot = await f.runtime.snapshot(run.run_id, control(run));
  assert.equal(reads, 1);
  assert.equal(snapshot.state.sequence, snapshot.next.sequence);
  assert.equal(snapshot.events.at(-1).sequence, snapshot.state.sequence);
  assert.deepEqual((await f.runtime.snapshot(run.run_id, { ...control(run), after_sequence: snapshot.state.sequence })).events, []);
  assert.deepEqual((await f.runtime.snapshot(run.run_id)).events, []);
  await assert.rejects(f.runtime.snapshot(run.run_id, { control_token: 'wrong' }), { code: 'RUN_AUTHORITY' });
  const record = await read(run.run_id);
  await writeFile(join(f.runtime.runs.directory(run.run_id), 'objects', record.pins.resources[0].sha256), 'tampered');
  await assert.rejects(f.runtime.snapshot(run.run_id, control(run)), { code: 'RUN_RESOURCE_CORRUPT' });
});

test('absolute Run targets are persisted and leased relative to the chosen project',async t=>{
 const workflow=definition();workflow.nodes.find(n=>n.id==='work').access='bounded_write';workflow.nodes.find(n=>n.id==='work').path_scope={binding:'run.allowed_paths'};
 const f=await fixture(t,workflow);const run=await f.start({access:'bounded_write',allowed_paths:[join(f.workspace,'edit')]});
 const envelope=await claim(f,run,'work');assert.equal(envelope.workspace,f.workspace);assert.deepEqual(envelope.effective_allowed_paths,['edit']);
});

test('environment gate prevents Run creation until host dependencies are ready',async t=>{
 let ready=false;const workflow=definition();workflow.requirements.executables=['fixture-program'];
 const f=await fixture(t,workflow,{environmentResolver:async()=>({status:ready?'ready':'installation_approval_required',missing:ready?[]:['fixture-program']})});
 await assert.rejects(f.start(),{code:'ENVIRONMENT_SETUP_REQUIRED'});assert.equal((await f.runtime.runs.list()).length,0);
 ready=true;assert.equal((await f.start()).status,'running');
});
