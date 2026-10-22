import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, rm, writeFile, readFile } from 'node:fs/promises';
import { join } from 'node:path';
import { tmpdir } from './physical-tempdir.mjs';
import { readyWorkflow } from './fixtures/workflow-fixtures.mjs';
import { WorkflowStore } from '../lib/workflow-store.mjs';
import { WorkflowRuntime } from '../lib/workflow-runtime.mjs';
import { WorkflowDrive } from '../lib/workflow-drive.mjs';
import { WorkflowExecutor } from '../lib/workflow-executor.mjs';
import { digest } from '../lib/workflow-revisions.mjs';
import { leaseToken } from '../lib/workflow-execution-envelope.mjs';
import { HostToolRunner } from '../lib/execution/host-tool-runner.mjs';
import {assertOutsideHostRunTransaction} from '../lib/workflow-run-store.mjs';
import {RunExecutionCoordinator} from '../lib/execution/run-execution-coordinator.mjs';
import {prepareMainOrchestration,completeMainOrchestration} from '../lib/execution/main-orchestration.mjs';

for(const fault of ['pins','paths','controller','lease'])test(`dependency phase fresh admission rejects ${fault} tamper after external verifier`,async t=>{
  const f=await fixture(t,{environment:true}),record=await f.runtime.authorizedRun(f.run.run_id,f.args);
  let verified=0;f.runtime.environmentVerifier=async()=>{
    verified++;assertOutsideHostRunTransaction();
    if(fault==='pins')await writeFile(join(f.runtime.runs.directory(f.run.run_id),'pins.json'),'{}');
    else await f.runtime.runs.mutate(f.run.run_id,'control_recovery',state=>{
      if(fault==='controller')state.control_hash=digest('other-controller');
      if(fault==='lease')state.nodes.final.attempts[0].lease_hash=digest('other-lease');
      if(fault==='paths')state.nodes.final.runtime_environment_binding.environment.tools[0].path=join(f.root,'changed-path');
    });
  };
  const codes={pins:'RUN_PINS_CORRUPT',paths:'ENVIRONMENT_BINDING_STALE',controller:'RUN_AUTHORITY',lease:'LEASE_INVALID'};
  await assert.rejects(f.runtime.ensureNativeRuntimeEnvironmentFromAudit(f.run.run_id,{...f.lease,control_token:f.run.control_token},record),{code:codes[fault]});
  assert.equal(verified,1);assert.equal(f.effects(),0);
});

async function fixture(t, { environment = false, active = true, tool = false, invalidToolInput = false } = {}) {
  const root = await mkdtemp(join(tmpdir(), 'main-drive-authorized-read-'));
  t.after(() => rm(root, { recursive: true, maxRetries: 3, retryDelay: 100 }));
  const workspace = join(root, 'workspace'); await mkdir(workspace);
  const workflow = readyWorkflow('main-drive-authorized-read');
  workflow.skill_policy.mode = 'cooperative';
  const node = workflow.nodes.find(item => item.id === 'final');
  node.executor = { kind: 'main', mode: 'orchestration' };
  node.resources = ['instructions/task.md'];
  if (environment) node.runtime_requirements = { executables: ['node'] };
  const contract = { id: 'fixture-read', identity: { name: 'fixture-read', version: '1', sha256: digest('fixture-read') }, argv: ['fixture-read'],
    input_schema: { type: 'object', additionalProperties: false }, output_schema: { type: 'object', properties: { text: { type: 'string' } }, required: ['text'], additionalProperties: false },
    env_allow: [], permissions: { network: false, read_paths: ['input.txt'], write_paths: [] }, output_cap_bytes: 1024, deadline_ms: 1000, idempotency: { mode: 'safe' } };
  if(invalidToolInput)contract.input_schema={type:'object',properties:{markdown:{type:'string'},conclusion:{type:'string'}},required:['markdown','conclusion'],additionalProperties:false};
  if (tool) {
    workflow.host_tools = [contract];
    workflow.nodes.splice(1, 0, { id: 'read', type: 'tool', executor: { kind: 'tool', tool: contract.id }, access: 'read_only',
      approval: { required: false }, retry: { max_attempts: 1 }, input_bindings: {}, outputs_schema: contract.output_schema });
    workflow.edges = [{ id: 'start-read', source: 'start', target: 'read' }, { id: 'read-final', source: 'read', target: 'final' }, { id: 'final-end', source: 'final', target: 'end' }];
    if(invalidToolInput){
      workflow.nodes.splice(1,0,{...structuredClone(node),id:'producer',role:'implementer',outputs_schema:{type:'object',properties:{markdown:{type:'string'}},required:['markdown'],additionalProperties:false}});
      workflow.nodes.find(item=>item.id==='read').input_bindings={markdown:'/nodes/producer/output/markdown'};
      workflow.edges.splice(0,1,{id:'start-producer',source:'start',target:'producer'},{id:'producer-read',source:'producer',target:'read'});
    }
    await writeFile(join(workspace, 'input.txt'), 'Observed filesystem input');
  }
  const context = tool ? { host_tools: [contract.id] } : {};
  const store = await new WorkflowStore(join(root, 'packs'), { validationContext: context }).initialize();
  await store.create(workflow, { resources: {
    'instructions/task.md': 'Synthetic declared reference',
    'instructions/unrelated.md': 'Synthetic undeclared pin still requires validation',
  } });
  const runtime = await new WorkflowRuntime({ workflowStore: store, runRoot: join(root, 'runs'), context,
    environmentResolver: async requirements => ({ status: 'ready', missing: [],
      tools: requirements.executables.map(tool => ({ name: tool.name, status: 'found', path: process.execPath })) }),
    environmentVerifier: async (_requirements, binding) => {
      if (!binding) throw Object.assign(new Error('Synthetic scoped preparation'), { code: 'ENVIRONMENT_BINDING_STALE' });
    },
  }).initialize();
  const run = await runtime.start({ workflow_id: workflow.id, workspace, access: 'read_only', main_actor: 'root',...(invalidToolInput?{constraints:{native_parent_thread_id:'12345678-1234-4234-8234-123456789abc'}}:{}) });
  const args = { control_token: run.control_token, node_id: 'final', owner: 'root', request_id: 'neutral-main-claim' };
  const lease = active ? await runtime.claimHostMain(run.run_id, args) : null;
  let effects = 0;
  const hostToolRunner = new HostToolRunner({ registry: { [contract.id]: {
    identity: contract.identity, attestation: { qualified: true, cancellable: true, effect_observation: true, tool_identity: contract.identity, broker_id: 'filesystem-fixture', evidence_sha256: digest('filesystem-fixture') },
    execute: async ({ context: execution }) => { effects++; return { exit_code: 0,
      output: { text: await readFile(join(execution.workspace, 'input.txt'), 'utf8') },
      effects: { observed: true, changed_paths: [], outside_paths: [], artifacts: [] } }; },
    cancel: async () => ({ termination_confirmed: true, evidence: [], effects: { observed: true, changed_paths: [], outside_paths: [], artifacts: [] } }),
  } } });
  const executor = new WorkflowExecutor({ runtime, env: {},
    hostToolRunner,
    getConfig: async () => ({ global: { enabled: true, max_prompt_chars: 64_000 }, providers: [] }) });
  const drive = new WorkflowDrive({ runtime, executor });
  return { root, runtime, drive, executor, run, args, lease, effects: () => effects };
}

test('claimed tool invalid input fails its exact attempt after a completed producer without broker effects or stranded progress',async t=>{
  const f=await fixture(t,{active:false,tool:true,invalidToolInput:true}),manager=()=>({entries:new Map(),fenceRun(){},fenceAttempt(){},async stopRun(){},async stopAttempt(){}});
  f.runtime.executionAdmission=f.executor.attemptAdmission;
  const coordinator=new RunExecutionCoordinator({admission:f.executor.attemptAdmission,strictManager:manager(),managedNativeManager:manager(),hostMainManager:manager(),registry:{}});
  coordinator.bind(f.runtime);f.runtime.failAttemptAfterQuiescence=(...args)=>coordinator.failAttemptAfterQuiescence(...args);
  const first=await f.drive.advanceToMain(f.run.run_id,f.args);assert.equal(first.node_id,'producer');
  const currentMain={run_id:f.run.run_id,control_token:f.run.control_token,thread_id:'12345678-1234-4234-8234-123456789abc'};
  await prepareMainOrchestration(f.runtime,currentMain);
  await completeMainOrchestration(f.runtime,{...currentMain,output:{markdown:'Synthetic complete producer output'}},{executor:f.executor});
  const producer=structuredClone((await f.runtime.get(f.run.run_id)).nodes.producer);
  const outcome=await f.drive.advanceToMain(f.run.run_id,f.args),state=await f.runtime.get(f.run.run_id);
  assert.equal(outcome.stop_reason,'host_failure');assert.equal(outcome.node_id,'read');assert.equal(outcome.error.code,'DATA_INVALID');
  assert.equal(state.nodes.read.status,'failed');assert.equal(state.nodes.read.attempts[0].status,'failed');
  assert.equal(state.nodes.read.attempts[0].host_tool,undefined,'Pure rejection cannot publish an uncertain effect intent');
  assert.equal(f.effects(),0);assert.deepEqual(state.nodes.producer,producer,'Completed producer identity and events remain intact');
  assert.equal(state.nodes.final.attempts.length,0);assert.equal(f.executor.attemptAdmission.pending(f.run.run_id).length,0);
  assert.equal((await f.drive.advanceToMain(f.run.run_id,f.args)).stop_reason,'terminal');
});

test('claimed tool uncertain effects remain owned and expose recovery instead of empty progress',async t=>{
  const f=await fixture(t,{active:false,tool:true}),manager=()=>({entries:new Map(),fenceRun(){},fenceAttempt(){},async stopRun(){},async stopAttempt(){}});
  f.runtime.executionAdmission=f.executor.attemptAdmission;
  const coordinator=new RunExecutionCoordinator({admission:f.executor.attemptAdmission,strictManager:manager(),managedNativeManager:manager(),hostMainManager:manager(),registry:{}});
  coordinator.bind(f.runtime);f.runtime.failAttemptAfterQuiescence=(...args)=>coordinator.failAttemptAfterQuiescence(...args);
  const broker=f.executor.hostToolRunner.registry['fixture-read'];
  broker.execute=async()=>{throw Object.assign(new Error('Fixture effect outcome is uncertain'),{code:'FIXTURE_EFFECT_UNCERTAIN'});};
  broker.cancel=async()=>{throw Object.assign(new Error('Fixture termination cannot be confirmed'),{code:'FIXTURE_STOP_UNCONFIRMED'});};
  const outcome=await f.drive.advanceToMain(f.run.run_id,f.args),state=await f.runtime.get(f.run.run_id);
  assert.equal(outcome.stop_reason,'execution_recovery_required');assert.equal(outcome.node_id,'read');
  assert.equal(state.status,'running');assert.equal(state.nodes.read.status,'claimed');
  assert.equal(state.nodes.read.attempts[0].host_tool.phase,'intent');assert.equal(state.nodes.read.attempts[0].host_tool.receipt,null);
  assert.equal(f.executor.attemptAdmission.pending(f.run.run_id).length,1,'Unconfirmed effect owner cannot be released');
  const repeated=await f.drive.advanceToMain(f.run.run_id,f.args);
  assert.equal(repeated.stop_reason,'execution_recovery_required');assert.equal(repeated.attempt_id,state.nodes.read.active_attempt_id);
});

test('claimed tool cancellation retains the terminal Run without invoking failure cleanup or broker effects',async t=>{
  const f=await fixture(t,{active:false,tool:true}),execute=f.executor.executeHostTool.bind(f.executor);
  f.runtime.failAttemptAfterQuiescence=()=>assert.fail('Cancelled Run cannot use a stale failure authorization');
  f.executor.executeHostTool=async(...args)=>{await f.runtime.cancel(f.run.run_id,f.args);return execute(...args);};
  const outcome=await f.drive.advanceToMain(f.run.run_id,f.args),state=await f.runtime.get(f.run.run_id);
  assert.equal(outcome.status,'cancelled',`${outcome.error?.code}/${outcome.settlement_error?.code}`);assert.equal(outcome.stop_reason,'terminal');
  assert.equal(state.nodes.read.status,'cancelled');assert.equal(f.effects(),0);assert.equal(f.executor.attemptAdmission.pending(f.run.run_id).length,0);
});

test('inactive Main planning uses one actual audited read before dependency preparation', async t => {
  const f = await fixture(t, { active: false }), read = f.runtime.runs.read.bind(f.runtime.runs);
  let reads = 0; f.runtime.runs.read = (...args) => { reads++; return read(...args); };
  const planning=f.runtime.authorizedPlanningRun.bind(f.runtime);
  f.runtime.authorizedPlanningRun=async(...args)=>{const result=await planning(...args);assert.equal(reads,1,'Planning owns one exact authorization');return result;};
  const result = await f.drive.advanceToMain(f.run.run_id, f.args);
  assert.equal(result.stop_reason, 'main_orchestration');
  assert.equal((await read(f.run.run_id)).state.nodes.final.attempts.length, 1);
});

test('tool completion starts a new one-read planning operation before the semantic successor', async t => {
  const f = await fixture(t, { active: false, tool: true }), read = f.runtime.runs.read.bind(f.runtime.runs);
  let reads = 0; f.runtime.runs.read = (...args) => { reads++; return read(...args); };
  const execute = f.executor.executeHostTool.bind(f.executor), planning=f.runtime.authorizedPlanningRun.bind(f.runtime);
  let afterTool = false;
  f.executor.executeHostTool = async (...args) => { const result = await execute(...args); afterTool = true; reads = 0; return result; };
  f.runtime.authorizedPlanningRun=async(...args)=>{const result=await planning(...args);
    if(afterTool){assert.equal(reads,1,'Completion starts a fresh single-read planning boundary');afterTool=false;}return result;};
  const result = await f.drive.advanceToMain(f.run.run_id, f.args), current = await read(f.run.run_id);
  assert.equal(result.stop_reason, 'main_orchestration'); assert.equal(result.steps, 1);
  assert.equal(f.effects(), 1); assert.equal(current.state.nodes.read.status, 'succeeded');
  assert.deepEqual(current.state.nodes.read.output, { text: 'Observed filesystem input' });
});

test('empty dependency preparation authorizes with one actual fresh read', async t => {
  const f = await fixture(t, { active: false }), read = f.runtime.runs.read.bind(f.runtime.runs);
  let reads = 0; f.runtime.runs.read = (...args) => { reads++; return read(...args); };
  const result = await f.runtime.ensureRuntimeEnvironment(f.run.run_id, f.args);
  assert.equal(reads, 1); assert.equal(result.sequence, (await read(f.run.run_id)).sequence);
});

test('scoped dependency verifier retains one fresh authorized audit after its initial audit', async t => {
  const f = await fixture(t, { environment: true }), read = f.runtime.runs.read.bind(f.runtime.runs);
  let reads = 0; f.runtime.runs.read = (...args) => { reads++; return read(...args); };
  await f.runtime.ensureRuntimeEnvironment(f.run.run_id, { ...f.args, attempt_id: f.lease.attempt_id, lease_token: f.lease.lease_token });
  assert.equal(reads, 2, 'The verifier is a real boundary; both fresh metadata checks remain, without duplicate authorization reads');
});

test('scoped dependency verification separates unrelated progress from exact execution binding changes',async t=>{
 for(const change of ['unrelated progress','explicit sequence','lease generation','permissions'])await t.test(change,async t=>{
  const f=await fixture(t,{environment:true}),before=await f.runtime.runs.read(f.run.run_id);
  const binding={...f.args,attempt_id:f.lease.attempt_id,lease_token:f.lease.lease_token,
   ...(change==='explicit sequence'?{expected_sequence:before.sequence}:{})};
  let enter,release;const entered=new Promise(resolve=>{enter=resolve;}),blocked=new Promise(resolve=>{release=resolve;});
  f.runtime.environmentVerifier=async()=>{enter();await blocked;};
  const pending=f.runtime.ensureRuntimeEnvironment(f.run.run_id,binding);await entered;
  await f.runtime.recordExecutorEvent(f.run.run_id,{...binding,event:{kind:'output_progress',metadata:{characters:1,retained_characters:1,truncated:false}}});
  if(change==='lease generation')await f.runtime.runs.mutate(f.run.run_id,'runtime_environment_rebound',state=>{
   const attempt=state.nodes.final.attempts.find(item=>item.id===f.lease.attempt_id);attempt.lease_generation=(attempt.lease_generation??0)+1;
  });
  if(change==='permissions')await f.runtime.runs.mutate(f.run.run_id,'runtime_environment_rebound',state=>{state.permissions.allowed_paths.push('different-scope');});
  release();
  if(change==='unrelated progress'){
   const result=await pending;assert(result.sequence>before.sequence);
   assert.deepEqual(result.environment,before.state.nodes.final.runtime_environment_binding.environment);
  }else await assert.rejects(pending,{code:change==='explicit sequence'?'RUN_SEQUENCE_CONFLICT':'ENVIRONMENT_BINDING_STALE'});
  assert.equal(f.effects(),0,'Dependency checks do not dispatch model or Host effects');
 });
});

for (const change of ['authority', 'cancel', 'binding', 'committed pins']) test(`scoped verifier mutation of ${change} fails at the retained fresh audit`, async t => {
  const f = await fixture(t, { environment: true });
  const initial = await f.runtime.runs.read(f.run.run_id), pin = initial.pins.root.resources.find(resource => resource.path === 'instructions/unrelated.md');
  f.runtime.environmentVerifier = async () => {
    if (change === 'committed pins') return writeFile(join(f.runtime.runs.directory(f.run.run_id), 'pins.json'), '{}');
    if (change === 'cancel') return f.runtime.cancel(f.run.run_id, f.args);
    return f.runtime.runs.mutate(f.run.run_id, 'runtime_environment_rebound', state => {
      if (change === 'authority') state.control_hash = digest('revoked-during-verifier');
      else state.nodes.final.runtime_environment_binding.scope_sha256 = 'f'.repeat(64);
    });
  };
  f.executor.dispatch = () => assert.fail('Verifier invalidation must prevent dispatch');
  await assert.rejects(f.drive.advanceToMain(f.run.run_id, f.args), {
    code: change === 'authority' ? 'RUN_AUTHORITY' : change === 'committed pins' ? 'RUN_PINS_CORRUPT' : change === 'cancel' ? 'RUN_NOT_RUNNING' : 'ENVIRONMENT_BINDING_STALE',
  });
  assert.equal(f.effects(), 0);
});

for (const phase of ['before', 'after']) test(`inactive planning checks activity ${phase} its owned read and derivation`, async t => {
  const f = await fixture(t, { active: false, tool: true }), read = f.runtime.runs.read.bind(f.runtime.runs);
  const marker = Object.assign(new Error('Drive operation fenced'), { code: 'DRIVE_FENCED' });
  let completed = false, reads = 0;
  f.runtime.runs.read = async (...args) => { reads++; const record = await read(...args); completed = true; return record; };
  const assertActive = () => { if (phase === 'before' || completed) throw marker; };
  await assert.rejects(f.drive.advanceToMain(f.run.run_id, { ...f.args, assertActive }), error => error === marker);
  assert.equal(reads, phase === 'before' ? 0 : 1); assert.equal(f.effects(), 0);
  assert.equal((await read(f.run.run_id)).state.nodes.read.attempts.length, 0);
});

test('caller planning snapshots and callbacks cannot substitute a fresh audit', async t => {
  const f = await fixture(t, { active: false }), record = await f.runtime.authorizedRun(f.run.run_id, f.args);
  await f.runtime.runs.mutate(f.run.run_id, 'runtime_environment_rebound', state => { state.control_hash = digest('revoked-controller'); });
  await assert.rejects(f.runtime.authorizedPlanningRun(f.run.run_id, { ...f.args, record, next: {}, select: () => assert.fail('No caller derivation runs') }), { code: 'RUN_AUTHORITY' });
  await assert.rejects(f.runtime.ensureRuntimeEnvironment(f.run.run_id, { ...f.args, record }), { code: 'RUN_AUTHORITY' });
});

test('public deterministic advance preserves its result shape with one initial planning audit', async t => {
  const f = await fixture(t, { active: false }), read = f.runtime.runs.read.bind(f.runtime.runs), ensure = f.runtime.ensureRuntimeEnvironment.bind(f.runtime);
  let reads = 0; f.runtime.runs.read = (...args) => { reads++; return read(...args); };
  f.runtime.ensureRuntimeEnvironment = (...args) => { assert.equal(reads, 1); return ensure(...args); };
  assert.deepEqual(await f.drive.advance(f.run.run_id, f.args), { status: 'running', stop_reason: 'semantic_node', node_id: 'final', steps: 0 });
  assert.equal((await read(f.run.run_id)).state.nodes.final.attempts.length, 0);
});

for (const change of ['authority', 'cancel']) test(`tool claim refreshes after planning observes concurrent ${change}`, async t => {
  const f = await fixture(t, { active: false, tool: true }), claim = f.runtime.claimNode.bind(f.runtime);
  f.runtime.claimNode = async (...args) => {
    f.runtime.claimNode = claim;
    if (change === 'cancel') await f.runtime.cancel(f.run.run_id, f.args);
    else await f.runtime.runs.mutate(f.run.run_id, 'runtime_environment_rebound', state => { state.control_hash = digest('concurrent-controller'); });
    return claim(...args);
  };
  await assert.rejects(f.drive.advanceToMain(f.run.run_id, f.args), { code: change === 'cancel' ? 'NODE_NOT_READY' : 'RUN_AUTHORITY' });
  assert.equal(f.effects(), 0);
  assert.equal((await f.runtime.runs.read(f.run.run_id)).state.nodes.read.attempts.length, 0);
});

test('Main drive performs one full initial authorization read before its unchanged claim boundary', async t => {
  const f = await fixture(t), read = f.runtime.runs.read.bind(f.runtime.runs);
  let reads = 0; f.runtime.runs.read = (...args) => { reads++; return read(...args); };
  const marker = new Error('Stop at the existing fresh claim boundary');
  f.runtime.claimHostMain = () => {
    assert.equal(reads, 1, 'The old adjacent authorization and selection path performed two complete reads');
    throw marker;
  };
  await assert.rejects(f.drive.advanceToMain(f.run.run_id, f.args), error => error === marker);
  assert.equal(reads, 1);
});

test('Host authorized Run projection is fresh and keeps public controller results unchanged', async t => {
  const f = await fixture(t), expected = await f.runtime.authorizeController(f.run.run_id, f.args);
  const read = f.runtime.runs.read.bind(f.runtime.runs); let reads = 0;
  f.runtime.runs.read = (...args) => { reads++; return read(...args); };
  const record = await f.runtime.authorizedRun(f.run.run_id, f.args);
  assert.equal(reads, 1); assert.equal(record.state.run_id, f.run.run_id);
  assert.equal(record.pins.root.resources.length, 2);
  assert.deepEqual(await f.runtime.authorizeController(f.run.run_id, f.args), expected);
  assert.equal(reads, 2);
  await f.runtime.runs.mutate(f.run.run_id, 'runtime_environment_rebound', state => { state.control_hash = digest('revoked'); });
  await assert.rejects(f.runtime.authorizedRun(f.run.run_id, { ...f.args, record }), { code: 'RUN_AUTHORITY' });
});

for (const barrier of ['wrong token', 'wrong owner', 'committed pins']) test(`Main drive retains the real ${barrier} rejection before claim or dispatch`, async t => {
  const f = await fixture(t), args = { ...f.args };
  if (barrier === 'wrong token') args.control_token = 'wrong';
  if (barrier === 'wrong owner') args.owner = 'another-owner';
  if (barrier === 'committed pins') {
    const record = await f.runtime.runs.read(f.run.run_id);
    const pin = record.pins.root.resources.find(item => item.path === 'instructions/unrelated.md');
    await writeFile(join(f.runtime.runs.directory(f.run.run_id), 'pins.json'), '{}');
  }
  f.runtime.claimHostMain = () => assert.fail('Rejected initial authorization must not reach claim');
  f.executor.dispatch = () => assert.fail('Rejected initial authorization must not dispatch');
  await assert.rejects(f.drive.advanceToMain(f.run.run_id, args), {
    code: barrier === 'wrong token' ? 'RUN_AUTHORITY' : barrier === 'wrong owner' ? 'FINALIZER_AUTHORITY' : 'RUN_PINS_CORRUPT',
  });
});

test('Main drive observes a cancelled Run without claiming or dispatching more work', async t => {
  const f = await fixture(t); await f.runtime.cancel(f.run.run_id, f.args);
  f.runtime.claimHostMain = () => assert.fail('A cancelled Run cannot claim another Main attempt');
  f.executor.dispatch = () => assert.fail('A cancelled Run cannot dispatch');
  const result = await f.drive.advanceToMain(f.run.run_id, f.args);
  assert.equal(result.status, 'cancelled'); assert.equal(result.stop_reason, 'terminal');
});

test('Main drive retains fresh authorization at claim after its initial projection', async t => {
  const f = await fixture(t), claim = f.runtime.claimHostMain.bind(f.runtime);
  f.runtime.claimHostMain = async (...args) => {
    await f.runtime.runs.mutate(f.run.run_id, 'runtime_environment_rebound', state => { state.control_hash = digest('new-controller'); });
    return claim(...args);
  };
  f.executor.dispatch = () => assert.fail('Revoked authority at the claim boundary cannot dispatch');
  await assert.rejects(f.drive.advanceToMain(f.run.run_id, f.args), { code: 'RUN_AUTHORITY' });
});

test('execution selection rejects a changed lease at the actual scoped environment verifier boundary', async t => {
  const f = await fixture(t, { environment: true });
  const binding = { control_token: f.run.control_token, node_id: 'final', attempt_id: f.lease.attempt_id, lease_token: f.lease.lease_token };
  let selections = 0;
  const select = record => {
    selections++;
    const node = record.state.nodes.final, attempt = node.attempts.find(item => item.id === node.active_attempt_id);
    return { node_id: 'final', attempt_id: attempt.id,
      lease_token: leaseToken(f.run.control_token, f.run.run_id, 'final', attempt.id, attempt.lease_generation ?? 0) };
  };
  f.runtime.environmentVerifier = () => f.runtime.runs.mutate(f.run.run_id, 'runtime_environment_rebound', state => {
    const attempt = state.nodes.final.attempts.find(item => item.id === f.lease.attempt_id);
    attempt.lease_generation = (attempt.lease_generation ?? 0) + 1;
  });
  await assert.rejects(f.runtime.authorizedExecution(f.run.run_id, binding, select), { code: 'ENVIRONMENT_BINDING_STALE' });
  assert.equal(selections, 1, 'Fresh scoped verification rejects the changed lease before a stale execution reselection');
});

test('Main drive still prepares and dispatches its exact synthetic Main claim', async t => {
  const f = await fixture(t), result = await f.drive.advanceToMain(f.run.run_id, f.args);
  assert.equal(result.stop_reason, 'main_orchestration');
  assert.equal(result.host_binding.attempt_id, f.lease.attempt_id);
  const current = await f.runtime.runs.read(f.run.run_id);
  assert.equal(current.state.nodes.final.active_attempt_id, f.lease.attempt_id);
  assert.equal(current.state.nodes.final.attempts.length, 1);
  assert(current.state.nodes.final.attempts[0].dispatch, 'Dispatch remains a fresh persisted transition');
});
