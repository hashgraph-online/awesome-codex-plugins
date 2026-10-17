import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, writeFile, rm } from 'node:fs/promises';
import { join } from 'node:path';
import { tmpdir } from './physical-tempdir.mjs';
import { WorkflowStore } from '../lib/workflow-store.mjs';
import { importCoarseSkill } from '../lib/skill-import/coarse-compiler.mjs';
import { compileExpansion } from '../lib/skill-import/semantic-expander.mjs';
import { observedSourceRequirements } from '../lib/skill-import/source-requirements.mjs';
import { createDraft } from '../lib/workflow-schema.mjs';
import { WorkflowRuntime } from '../lib/workflow-runtime.mjs';
import { WorkflowExecutor } from '../lib/workflow-executor.mjs';
import { HostToolRunner } from '../lib/execution/host-tool-runner.mjs';
import { approvalBinding } from '../lib/workflow-execution-envelope.mjs';

const identity = { name: 'approval-fixture', version: '1', sha256: 'a'.repeat(64) };
const contract = { id: 'approval-fixture', identity, argv: ['approval-fixture'],
  input_schema: { type: 'object', properties: {}, additionalProperties: false },
  output_schema: { type: 'object', properties: { checked: { type: 'boolean' } }, required: ['checked'], additionalProperties: false },
  env_allow: [], permissions: { network: false, read_paths: [], write_paths: [] }, output_cap_bytes: 1024,
  deadline_ms: 1000, idempotency: { mode: 'safe' } };
const edge = (source, target) => ({ id: `${source}-${target}`, source, target });

async function compiledFixture(t, { gate = false } = {}) {
  const root = await mkdtemp(join(tmpdir(), 'approval-compiler-'));
  t.after(() => rm(root, { recursive: true, maxRetries: 3, retryDelay: 100 }));
  const source = join(root, 'SKILL.md');
  await writeFile(source, '---\nname: Approval fixture\ndescription: Check a result.\n---\n\n'
    + (gate ? 'You must obtain approval before checking.\n' : 'Check the requested result.\n'));
  const store = await new WorkflowStore(join(root, 'source-packs')).initialize();
  const provider = { id: 'fixture-provider', enabled: true, capabilities: { read: true, write: true } };
  const pack = await importCoarseSkill(store, source, { id: 'approval-source', providerId: provider.id });
  const resources = await store.resources(pack.workflow.id);
  const origin = { confidence: 1, source_span: { resource: 'source/SKILL.md', start_line: 6, end_line: 6 } };
  const approval = observedSourceRequirements(resources).find(item => item.requirement_kind === 'approval');
  const proposal = { source_revision: pack.revision_hash, source_requirements: [],
    requirement_mappings: gate ? [{ requirement_id: approval.requirement_id, node_ids: ['approve', 'check'],
      binding_names: [], runtime_guards: [], resource_refs: ['source/SKILL.md'], status: 'compiled', rationale: 'The explicit human gate precedes checking.' }] : [],
    nodes: [ ...(gate ? [{ id: 'approve', semantic_key: 'approve', type: 'human_gate', prompt_template: 'Approve checking?', input_bindings: {}, resource_refs: ['source/SKILL.md'], ...origin }] : []),
      { id: 'check', semantic_key: 'check', type: 'tool', tool: contract.id, input_bindings: {}, resource_refs: [], ...origin } ],
    edges: (gate ? [edge('start', 'approve'), edge('approve', 'check'), edge('check', 'final')]
      : [edge('start', 'check'), edge('check', 'final')]).map(item => ({ ...item, ...origin })) };
  const context = { providers: [provider], host_tools: [contract.id], host_tool_contracts: [contract] };
  const compiled = compileExpansion(pack, resources, proposal, context);
  assert.equal(compiled.validation.valid, true, JSON.stringify(compiled.validation));
  return { root, pack, resources, proposal, context, compiled };
}

async function runtimeFixture(t, options = {}) {
  const f = await compiledFixture(t, options);
  // Exercise the emitted activities in a reviewed runtime fixture. Import promotion/review is
  // covered separately; the emitted approval and ordering fields remain exactly as compiled.
  const workflow = { ...createDraft('approval-runtime', 'Approval runtime fixture'), status: 'ready', host_tools: [contract],
    skill_policy: { mode: 'cooperative', implicit: 'allow', ambient_allow: [], shadowed_skill_paths: [] },
    inputs_schema: { type: 'object', properties: {}, additionalProperties: false }, finalization: { required: true, node_id: 'final' } };
  const activities = f.compiled.workflow.nodes.filter(node => ['check', 'approve'].includes(node.id)).map(node => ({ ...structuredClone(node), origin: { ...node.origin, reviewed: true } }));
  workflow.nodes = [{ id: 'start', type: 'start' }, ...activities,
    { id: 'final', type: 'agent', executor: { kind: 'main' }, access: 'read_only', approval: { required: false }, retry: { max_attempts: 1 },
      prompt_template: 'Accept the check.', outputs_schema: {}, input_bindings: {} }, { id: 'end', type: 'end' }];
  workflow.edges = f.compiled.workflow.edges.map(({ origin, ...item }) => item);
  const context = { host_tools: [contract.id] };
  const store = await new WorkflowStore(join(f.root, 'runtime-packs'), { validationContext: context }).initialize();
  const pack = await store.create(workflow, { resources: f.resources });
  const workspace = join(f.root, 'workspace'); await mkdir(workspace);
  const runtime = await new WorkflowRuntime({ workflowStore: store, runRoot: join(f.root, 'runs'), context,
    environmentResolver: async () => ({ status: 'ready', tools: [], missing: [] }) }).initialize();
  let calls = 0;
  const runner = new HostToolRunner({ registry: { [contract.id]: { identity,
    attestation: { qualified: true, cancellable: true, effect_observation: true, tool_identity: identity, broker_id: 'approval-fixture', evidence_sha256: 'b'.repeat(64) },
    async execute() { calls++; return { exit_code: 0, diagnostic: 'checked', output: { checked: true }, effects: { observed: true, changed_paths: [], outside_paths: [], artifacts: [] } }; },
    async cancel() { throw new Error('Unexpected cancellation'); } } }, env: {} });
  const executor = new WorkflowExecutor({ runtime, registry: {}, hostToolRunner: runner, env: {},
    getConfig: async () => ({ global: { enabled: true }, providers: [] }) });
  const run = await runtime.start({ workflow_id: workflow.id, revision_hash: pack.revision_hash, workspace, access: 'read_only', main_actor: 'main', inputs: {}, require_approval: options.requireApproval ?? false });
  const claim = () => runtime.claimNode(run.run_id, { node_id: 'check', owner: 'main', request_id: 'check-once', control_token: run.control_token });
  return { ...f, runtime, executor, run, claim, calls: () => calls };
}

test('Host compilation emits an authorized tool with no extra node approval and executes once', async t => {
  const f = await runtimeFixture(t);
  assert.equal(f.compiled.workflow.nodes.find(node => node.id === 'check').approval.required, false);
  assert.deepEqual((await f.runtime.next(f.run.run_id)).approvals, []);
  const lease = await f.claim();
  await f.executor.executeHostTool(f.run.run_id, { ...lease, control_token: f.run.control_token });
  assert.equal(f.calls(), 1);
  assert.equal((await f.runtime.get(f.run.run_id)).nodes.check.status, 'succeeded');
});

test('source approval remains a required human gate before tool effects, with no second tool approval', async t => {
  const f = await runtimeFixture(t, { gate: true });
  assert.equal(f.compiled.workflow.nodes.find(node => node.id === 'approve').approval.required, true);
  const next = await f.runtime.next(f.run.run_id);
  assert.deepEqual(next.approvals.map(item => item.node_id), ['approve']);
  assert.equal(next.ready.includes('check'), false);
  await assert.rejects(f.claim(), { code: 'NODE_NOT_READY' });
  assert.equal(f.calls(), 0);
  await f.runtime.approve(f.run.run_id, { approval_id: next.approvals[0].id, decision: true, control_token: f.run.control_token });
  const released = await f.runtime.next(f.run.run_id);
  assert.deepEqual(released.approvals, []);
  assert.equal(released.ready.includes('check'), true);
  const lease = await f.claim();
  await f.executor.executeHostTool(f.run.run_id, { ...lease, control_token: f.run.control_token });
  assert.equal(f.calls(), 1);
});

test('denied source human approval prevents tool effects', async t => {
  const f = await runtimeFixture(t, { gate: true });
  const next = await f.runtime.next(f.run.run_id);
  await f.runtime.approve(f.run.run_id, { approval_id: next.approvals[0].id, decision: false, control_token: f.run.control_token });
  await assert.rejects(f.claim(), { code: 'NODE_NOT_READY' });
  assert.equal(f.calls(), 0);
});

test('Run-wide approval still requires approval for a compiled tool', async t => {
  const f = await runtimeFixture(t, { requireApproval: true });
  const next = await f.runtime.next(f.run.run_id);
  assert.deepEqual(next.approvals.map(item => item.node_id), ['check']);
  await assert.rejects(f.claim(), { code: 'NODE_NOT_READY' });
  assert.equal(f.calls(), 0);
});

test('Provider approval remains independent of generated node approval', () => {
  const node = { id: 'worker', executor: { kind: 'provider', provider_id: 'approved-provider' }, access: 'read_only', approval: { required: false } };
  const state = { nodes: { worker: { attempts: [] } }, permissions: { workspace: 'fixture', access: 'read_only', allowed_paths: [] }, workflow_revision: 'r', require_approval: false };
  const pins = { providers: [{ id: 'approved-provider', requires_user_approval: true }], root: { workflow: { skill_policy: { mode: 'cooperative', implicit: 'allow', ambient_allow: [], shadowed_skill_paths: [] } } } };
  assert.equal(approvalBinding(node, state, pins).required, true);
});

test('the model cannot choose node approvals or bypass an explicit source human gate', async t => {
  const f = await compiledFixture(t, { gate: true });
  const authority = structuredClone(f.proposal); authority.nodes.find(node => node.id === 'check').approval = { required: false };
  assert.throws(() => compileExpansion(f.pack, f.resources, authority, f.context), { code: 'EXPANSION_AUTHORITY' });
  const bypass = structuredClone(f.proposal); bypass.edges.push({ ...edge('start', 'check'), confidence: 1, source_span: bypass.nodes[0].source_span });
  assert.throws(() => compileExpansion(f.pack, f.resources, bypass, f.context), { code: 'EXPANSION_REQUIREMENT_COVERAGE' });
});
