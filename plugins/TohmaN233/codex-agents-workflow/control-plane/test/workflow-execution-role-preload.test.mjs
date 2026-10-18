import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import { syncBuiltinESMExports } from 'node:module';
import { join, resolve } from 'node:path';
import { tmpdir } from './physical-tempdir.mjs';
import { WorkflowService } from '../lib/workflow-service.mjs';
import { createDraft } from '../lib/workflow-schema.mjs';
import { readyWorkflow, agent, edge } from './fixtures/workflow-fixtures.mjs';
import { DEFAULT_CONFIG_PATH } from '../server.mjs';
import { loadConfig, saveConfig } from '../lib/config.mjs';
import { packDirectory } from '../lib/workflow-paths.mjs';
import { retainOwnedAuthority } from '../lib/execution/owned-workflow-authority.mjs';
import { withForegroundOperationObservation } from '../lib/foreground-operation-observation.mjs';

const thread = '12345678-1234-4234-8234-123456789abc';
const model = { model: true, modelThreadId: thread };
const schema = { type: 'object', properties: { conclusion: { type: 'string' } }, required: ['conclusion'], additionalProperties: false };
const roleOperations = ['role_templates', 'customize_role', 'role_template', 'start_role_connector'];
const executionOperations = ['start', 'native_next', 'native_spawned_batch', 'native_followed_up', 'orchestration_complete'];

async function fixture(t, { nativeAgentObserver = null } = {}) {
  const root = await fs.mkdtemp(join(tmpdir(), 'workflow-role-preload-'));
  const workspace = join(root, 'workspace'); await fs.mkdir(workspace);
  const configPath = join(root, 'control-plane.json');
  let effects = 0;
  const service = new WorkflowService({ configPath, defaultConfigPath: DEFAULT_CONFIG_PATH, env: {},
    registry: { start: async () => { effects++; assert.fail('Unexpected connector effect'); } },
    capabilities: { nativeAgentObserver, nativeParentVerifier: async () => ({ agent_path: '/root' }),
      hostMainManager: { qualify: async () => { effects++; assert.fail('Unexpected executor qualification'); },
        launch: async () => { effects++; assert.fail('Unexpected executor session'); }, fenceRun() {}, fenceAttempt() {} } } });
  await service.call('migrate_v6', {}, { human: true });
  const { store, runtime } = await service.open();
  t.after(async () => {
    await Promise.allSettled([...service.attemptAdmission.drainJobs.values()]);
    await service.historyMaintenance.settle(); await service.historyMaintenance.close();
    assert(resolve(root).startsWith(resolve(tmpdir())));
    await fs.rm(root, { recursive: true, maxRetries: 3, retryDelay: 100 });
  });
  return { root, workspace, configPath, service, store, runtime, effects: () => effects };
}

function orchestration(id = 'selected-orchestration') {
  const workflow = readyWorkflow(id);
  workflow.skill_policy.mode = 'cooperative';
  const final = workflow.nodes.find(node => node.id === 'final');
  final.executor = { kind: 'main', mode: 'orchestration' };
  final.outputs_schema = schema; final.resources = ['reference.txt'];
  return workflow;
}

function nativeWorkflow() {
  const workflow = orchestration('selected-native');
  workflow.inputs_schema = { type: 'object', properties: { jobs: { type: 'array', items: { type: 'integer' } } }, required: ['jobs'], additionalProperties: false };
  const worker = { ...agent('worker'), executor: { kind: 'provider', provider_id: 'native-luna' },
    input_bindings: { jobs: '/inputs/jobs' }, resources: ['reference.txt'], subagent_count: 'auto',
    fanout: { input: 'jobs', item_name: 'job', distribution: 'partition', batch_size: 10, result_output: 'results',
      scheduling: 'parallel', max_concurrency: 1, join: 'all_required', result_mode: 'per_item', item_delivery: 'incremental' },
    outputs_schema: { type: 'object', properties: { results: { type: 'array', items: { type: 'array', items: { type: 'integer' } } } }, required: ['results'], additionalProperties: false } };
  workflow.nodes.splice(1, 0, worker);
  workflow.edges = [edge('start', 'worker'), edge('worker', 'final'), edge('final', 'end')];
  return workflow;
}

async function pack(f, workflow = orchestration()) {
  return f.store.create(workflow, { resources: { 'reference.txt': 'Selected authoritative resource' } });
}
function launch(f, selected, extra = {}) {
  return { workflow_id: selected.workflow.id, revision_hash: selected.revision_hash, workspace: f.workspace,
    access: 'read_only', main_actor: 'fixture', native_parent_thread_id: thread, inputs: {}, ...extra };
}
async function corruptUnrelatedRole(f) {
  const role = await f.store.create(createDraft('unrelated-role-customization', 'Unrelated Role'), {
    resources: { 'role.txt': 'original' }, provenance: { kind: 'role_customization', builtin_role_id: 'builtin-role-repository-analysis' } });
  const object = join(packDirectory(f.store.root, role.workflow.id), 'objects', role.resources[0].sha256);
  await fs.writeFile(object, 'corrupt'); return object;
}

// Observe actual filesystem reads without substituting Store/runtime validation.
async function readTrace(action) {
  const read = fs.readFile, reads = [];
  fs.readFile = async (path, ...args) => { reads.push(resolve(String(path))); return read(path, ...args); };
  syncBuiltinESMExports();
  try { return { value: await action(), reads }; }
  finally { fs.readFile = read; syncBuiltinESMExports(); }
}
async function observed(action, roleObject, { reject } = {}) {
  const reports = [];
  const trace = await readTrace(() => withForegroundOperationObservation(async () => {
    if (reject) { await assert.rejects(action(), { code: reject }); return; }
    return action();
  }, report => reports.push(report)));
  assert.equal(trace.reads.filter(path => path === resolve(roleObject)).length, 0);
  assert.equal(reports.length, 1);
  assert.deepEqual(Object.keys(reports[0].f).sort(), ['hm', 'op', 'pm']);
  const opens = reports[0].f.op[0];
  assert.equal(reports[0].f.pm[0], opens); assert.equal(reports[0].f.hm[0], opens);
  assert.deepEqual(reports[0].fn, [3 * opens, 3 * opens, 0]);
  return trace.value;
}

test('exact five execution routes skip unrelated Role resource reads and rp while real selected execution succeeds', async t => {
  let observations = 0;
  const f = await fixture(t, { nativeAgentObserver: async ids => ({ status: 'completed', agent_id: ids[0],
    turn_id: `fixture-turn-${++observations}`, result: { items: [{ outcome: 'completed', result: [observations] }] } }) });
  const selected = await pack(f, nativeWorkflow());
  const roleObject = await corruptUnrelatedRole(f);
  const run = await observed(() => f.service.call('start', launch(f, selected, { inputs: { jobs: [1, 2] },
    skipRoleProfiles: false, roleProfiles: true }), { roleProfiles: true }), roleObject);
  await retainOwnedAuthority(f.runtime, run);
  const handoff = await observed(() => f.service.call('native_next', {}, model), roleObject);
  assert.equal(handoff.registration_tool, 'workflow_native_spawned_batch');
  const continued = await observed(() => f.service.call('native_spawned_batch', { batch_id: handoff.batch_id }, model), roleObject);
  assert.equal(continued.next_action, 'continue_recorded_agent');
  const binding = { run_id: run.run_id, control_token: run.control_token };
  const followed = await observed(() => f.service.call('native_followed_up', binding), roleObject);
  assert.equal(followed.recorded, true);
  const advanced = await observed(() => f.service.call('native_next', {}, model), roleObject);
  assert.equal(advanced.status, 'orchestration_handoff');
  assert.equal(advanced.completion_tool, 'workflow_orchestration_complete');
  assert.match(advanced.task_bundle.task, /Selected authoritative resource/);
  const completed = await observed(() => f.service.call('orchestration_complete', { output: { conclusion: 'accepted' } }, model), roleObject);
  assert.equal(completed.status, 'succeeded'); assert.equal(observations, 2);
  const record = await f.runtime.runs.read(run.run_id);
  assert.deepEqual(record.state.nodes.worker.output.results, [[1], [2]]);
  assert.equal(record.state.nodes.final.output.conclusion, 'accepted'); assert.equal(f.effects(), 0);
});

test('public open and every explicit Role route retain original corrupt resource and invalid customization errors', async t => {
  const f = await fixture(t), roleObject = await corruptUnrelatedRole(f);
  const attempts = [() => f.service.open(), () => f.service.open({ skipRoleProfiles: true }),
    () => f.service.open(Symbol('Workflow execution without eager Role profiles')),
    ...roleOperations.map(operation => () => f.service.call(operation, {
      workflow_id: 'builtin-role-repository-analysis', task: 'fixture', skipRoleProfiles: true,
    }, { human: true, model: true, skipRoleProfiles: true }))];
  for (const attempt of attempts) {
    const trace = await readTrace(() => assert.rejects(attempt(), { code: 'RESOURCE_CORRUPT' }));
    assert(trace.reads.includes(resolve(roleObject)));
  }
  await fs.writeFile(roleObject, 'original');
  for (const attempt of attempts) await assert.rejects(attempt(), { code: 'ROLE_CUSTOMIZATION_KIND' });
  assert.equal(f.effects(), 0);
});

test('other operations keep eager profiles even with caller skip flags and direct opening preserves full fields', async t => {
  const f = await fixture(t);
  const opened = await f.service.open({ skipRoleProfiles: true, operation: 'start' });
  assert(opened.context.roles.length > 0);
  assert.equal(opened.store.validationContext, opened.context); assert.equal(opened.runtime.context, opened.context);
  const roleObject = await corruptUnrelatedRole(f);
  for (const operation of ['get', 'runs', 'read', 'begin_main', 'run_main', 'drive', 'dispatch', 'startup_contract', 'unknown']) {
    const reports = [];
    await withForegroundOperationObservation(() => assert.rejects(f.service.call(operation, {
      skipRoleProfiles: true, loadRoleProfiles: false, operation: 'start',
    }, { model: true, skipRoleProfiles: true }), { code: 'RESOURCE_CORRUPT' }), report => reports.push(report));
    assert.equal(reports[0].f.rp[0], 1);
  }
  assert.equal(f.effects(), 0); assert(roleObject);
});

test('public open and Role routes retain bounded instruction and duplicate profile errors', async t => {
  const f = await fixture(t), selected = await pack(f);
  for (const code of ['ROLE_PROFILE_INSTRUCTIONS', 'ROLE_PROFILE_DUPLICATE']) {
    const workflow = nativeWorkflow(); workflow.id = code === 'ROLE_PROFILE_DUPLICATE'
      ? 'builtin-role-repository-analysis' : 'oversized-role-profile'; workflow.template_kind = 'role';
    if (code === 'ROLE_PROFILE_INSTRUCTIONS') workflow.nodes.find(node => node.id === 'worker').prompt_template = 'x'.repeat(16001);
    const role = await f.store.create(workflow, { resources: { 'reference.txt': 'Valid Role resource' } });
    await assert.rejects(f.service.open(), { code });
    for (const operation of roleOperations)
      await assert.rejects(f.service.call(operation, { workflow_id: 'builtin-role-repository-analysis', task: 'fixture' }, { human: true }), { code });
    const run = await f.service.call('start', launch(f, selected));
    assert.equal((await f.runtime.runs.read(run.run_id)).state.status, 'running');
    await f.service.historyMaintenance.settle();
    await f.store.delete(role.workflow.id, role.revision_hash);
  }
  assert.equal(f.effects(), 0);
});

test('selected Workflow resource corruption still blocks start before Run publication or effects', async t => {
  const f = await fixture(t), selected = await pack(f), roleObject = await corruptUnrelatedRole(f);
  const selectedObject = join(packDirectory(f.store.root, selected.workflow.id), 'objects', selected.resources[0].sha256);
  await fs.writeFile(selectedObject, 'corrupt selected');
  const trace = await readTrace(() => observed(() => f.service.call('start', launch(f, selected)), roleObject, { reject: 'RESOURCE_CORRUPT' }));
  assert(trace.reads.includes(resolve(selectedObject)));
  assert.equal((await f.runtime.runs.list()).length, 0); assert.equal(f.effects(), 0);
});

test('every continuation validates corrupt committed pins before observation, journal or semantic effects', async t => {
  let observations = 0;
  const f = await fixture(t, { nativeAgentObserver: async () => { observations++; assert.fail('Corrupt Run cannot observe an Agent'); } });
  const selected = await pack(f, nativeWorkflow());
  const run = await f.service.call('start', launch(f, selected, { inputs: { jobs: [1, 2] } }));
  await retainOwnedAuthority(f.runtime, run);
  const handoff = await f.service.call('native_next', {}, model);
  await f.service.historyMaintenance.settle();
  const journal = join(f.runtime.runs.directory(run.run_id), 'events.jsonl');
  const before = await fs.readFile(journal);
  const object = join(f.runtime.runs.directory(run.run_id), 'pins.json');
  const roleObject = await corruptUnrelatedRole(f); await fs.writeFile(object, '{}');
  for (const operation of executionOperations.slice(1)) {
    const args = operation === 'native_spawned_batch' ? { batch_id: handoff.batch_id }
      : operation === 'orchestration_complete' ? { output: { conclusion: 'invalid' } } : {};
    const trace = await readTrace(() => assert.rejects(f.service.call(operation, args, model), { code: 'RUN_PINS_CORRUPT' }));
    assert(trace.reads.includes(resolve(object))); assert(!trace.reads.includes(resolve(roleObject)));
    assert.deepEqual(await fs.readFile(journal), before);
  }
  assert.equal(observations, 0); assert.equal(f.effects(), 0);
});

test('fresh config and current controller authority still reject execution before effects', async t => {
  const f = await fixture(t), selected = await pack(f);
  const run = await f.service.call('start', launch(f, selected)); await retainOwnedAuthority(f.runtime, run);
  const roleObject = await corruptUnrelatedRole(f), journal = join(f.runtime.runs.directory(run.run_id), 'events.jsonl');
  const before = await fs.readFile(journal);
  for (const operation of executionOperations.slice(1)) {
    const args = operation === 'orchestration_complete' ? { output: { conclusion: 'wrong authority' } } : {};
    await assert.rejects(f.service.call(operation, args, { ...model,
      expectedRunAuthority: { run_id: run.run_id, control_token: 'obsolete-controller' } }), { code: 'RUN_AUTHORITY' });
    assert.deepEqual(await fs.readFile(journal), before);
  }
  for (const operation of ['native_next', 'native_followed_up'])
    await observed(() => f.service.call(operation, { run_id: run.run_id, control_token: 'obsolete-controller' }), roleObject, { reject: 'RUN_AUTHORITY' });
  const config = await loadConfig({ configPath: f.configPath, defaultConfigPath: DEFAULT_CONFIG_PATH });
  config.global.enabled = false; await saveConfig(config, { configPath: f.configPath });
  await observed(() => f.service.call('start', launch(f, selected)), roleObject, { reject: 'CONTROL_DISABLED' });
  assert.equal((await f.runtime.runs.list()).length, 1); assert.equal(f.effects(), 0);
  await fs.writeFile(f.configPath, '{');
  await assert.rejects(f.service.call('start', launch(f, selected)), /control-plane config is invalid JSON/);
});

test('model supplied preload flags cannot broaden or override Host route policy', async t => {
  const f = await fixture(t), selected = await pack(f), roleObject = await corruptUnrelatedRole(f);
  for (const operation of executionOperations.slice(1)) {
    const args = operation === 'orchestration_complete' ? { output: {}, skipRoleProfiles: true }
      : { skipRoleProfiles: true };
    await assert.rejects(f.service.call(operation, args, model), { code: 'MODEL_CONTINUATION_FIELDS' });
  }
  await assert.rejects(f.service.call('role_templates', { skipRoleProfiles: true }, { ...model, skipRoleProfiles: true }), { code: 'RESOURCE_CORRUPT' });
  await observed(() => f.service.call('start', launch(f, selected, { skipRoleProfiles: false }), { ...model,
    loadRoleProfiles: true }), roleObject, { reject: 'HOST_MAIN_BRIDGE_REQUIRED' });
  assert.equal((await f.runtime.runs.list()).length, 0); assert.equal(f.effects(), 0);
});
