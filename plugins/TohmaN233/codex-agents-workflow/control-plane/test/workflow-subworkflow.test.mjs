import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, rm, readFile, writeFile } from 'node:fs/promises';
import { tmpdir } from './physical-tempdir.mjs';
import { join, resolve } from 'node:path';
import { WorkflowStore } from '../lib/workflow-store.mjs';
import { WorkflowRuntime } from '../lib/workflow-runtime.mjs';
import { createDraft } from '../lib/workflow-schema.mjs';
import { childIdentity, childPermissions } from '../lib/workflow-subworkflow.mjs';
import { validateWorkflowGraph } from '../lib/workflow-validator.mjs';
import { adoptRunTree, reattachAttempt } from '../lib/workflow-recovery.mjs';
import { hostResultProposalEnvelope } from '../lib/execution/host-main-automation.mjs';
import { AttemptAdmissionRegistry } from '../lib/execution/attempt-admission.mjs';
import { RunExecutionCoordinator } from '../lib/execution/run-execution-coordinator.mjs';
import { digest } from '../lib/workflow-revisions.mjs';
import { WORKSPACE_SOURCE_LOCATIONS, WORKSPACE_SOURCE_LOCATIONS_SCHEMA } from '../lib/workspace-source-locations.mjs';

const agent = id => ({ id, type: 'agent', executor: { kind: 'main' }, role: 'implementer', access: 'read_only', prompt_template: '{{task}}', approval: { required: false }, retry: { max_attempts: 2 }, input_bindings: {} });
const policy = { mode: 'cooperative', implicit: 'allow', ambient_allow: [], shadowed_skill_paths: [] };
function workflow(id, work = agent('work')) {
  return { ...createDraft(id, id), status: 'ready', skill_policy: structuredClone(policy),
    inputs_schema: { type: 'object', properties: { task: { type: 'string' } }, required: ['task'], additionalProperties: false },
    finalization: { required: true, node_id: 'final' },
    nodes: [{ id: 'start', type: 'start' }, work, { ...agent('final'), role: 'finalizer' }, { id: 'end', type: 'end' }],
    edges: [['start', work.id], [work.id, 'final'], ['final', 'end']].map(([source, target]) => ({ id: source + '-' + target, source, target })) };
}
const callNode = child => ({ ...agent('call'), type: 'subworkflow', executor: { kind: 'subworkflow' }, input_bindings: { task: '/inputs/task' },
  subworkflow: { workflow_id: child.workflow.id, revision_pin: child.revision_hash, output_bindings: { result: '/output' } } });
async function fixture(t, { childWorkflow = workflow('child'), callChanges = {}, parentChanges = {}, parentMutate = () => {} } = {}) {
  const root = await mkdtemp(join(tmpdir(), 'subworkflow-')); const workspace = join(root, 'workspace'); await mkdir(workspace);
  t.after(async () => { assert(resolve(root).startsWith(resolve(tmpdir()))); await rm(root, { recursive: true, maxRetries: 3, retryDelay: 100 }); });
  const store = await new WorkflowStore(join(root, 'packs')).initialize();
  const child = await store.create(childWorkflow, { resources: { 'reference.txt': 'Pinned child resource' } });
  const parentWorkflow = { ...workflow('parent', { ...callNode(child), ...callChanges }), ...parentChanges };
  parentMutate(parentWorkflow);
  store.validationContext = { workflows: { ['child@' + child.revision_hash]: child.workflow } };
  const parent = await store.create(parentWorkflow);
  const options = { workflowStore: store, runRoot: join(root, 'runs') }; const runtime = await new WorkflowRuntime(options).initialize();
  const start = args => runtime.start({ workflow_id: 'parent', inputs: { task: 'Synthetic child task' }, workspace, access: 'read_only', main_actor: 'root', ...args });
  return { root, workspace, store, child, parent, runtime, options, start };
}
const claim = async (runtime, run, nodeId) => {
  const record=await runtime.runs.read(run.run_id),claimArgs={node_id:nodeId,control_token:run.control_token,owner:'root',request_id:'claim-'+nodeId};
  return record.pins.root.workflow.nodes.find(node=>node.id===nodeId)?.executor?.kind==='main'
    ? runtime.claimHostMain(run.run_id,claimArgs)
    : runtime.claimNode(run.run_id,claimArgs);
};
const args = (run, lease) => ({ control_token: run.control_token, node_id: lease.node_id, attempt_id: lease.attempt_id, lease_token: lease.lease_token });
const completion = (output, extra = {}) => ({ status: 'succeeded', summary: 'Synthetic verified result', structured_output: output, artifacts: [], evidence: [{ checked: true }], changed_paths: [], outside_paths: [], ...extra });
async function prepareHost(runtime,run,lease){
  const binding=args(run,lease),record=await runtime.runs.read(run.run_id),attempt=record.state.nodes[lease.node_id].attempts.find(item=>item.id===lease.attempt_id);
  if(attempt.dispatch)return binding;
  const request_id=`dispatch-${lease.attempt_id}`;
  await runtime.recordHostMainDispatchIntent(run.run_id,{...binding,request_id,envelope_hash:'f'.repeat(64)});
  await runtime.recordHostMainDispatchReceipt(run.run_id,{...binding,request_id,receipt:{invocation_id:`host-main-${lease.attempt_id}`,executor:'codex-app-server-host-main',executable_sha256:'a'.repeat(64),model:'fixture-main',effort:'medium',main_actor:'root',session_id:`logical-main-${run.run_id}`,call_chain_id:`workflow-run-${run.run_id}`}});
  return binding;
}
const complete = async(runtime,run,lease,output={},extra)=>{
  const record=await runtime.runs.read(run.run_id),definition=record.pins.root.workflow.nodes.find(node=>node.id===lease.node_id);
  if(definition?.executor?.kind!=='main')return runtime.completeNode(run.run_id,{...args(run,lease),completion:completion(output,extra)});
  const binding=await prepareHost(runtime,run,lease),final=record.pins.root.workflow.finalization?.node_id===lease.node_id;
  const proposal=hostResultProposalEnvelope(definition,{output,summary:'Synthetic verified result',artifacts:[],evidence:[{checked:true}],changed_paths:[],outside_paths:[]},{finalAcceptance:final});
  const saved=await runtime.runs.saveExecutorResult(run.run_id,lease.attempt_id,proposal);
  await runtime.recordExecutorEvent(run.run_id,{...binding,event:{kind:'result_proposed',metadata:{...saved,final_acceptance_required:final}}});
  return runtime.completeHostMainResult(run.run_id,binding,{...(final?{accepted:extra?.acceptance?.accepted}:{})});
};

test('human tree adoption preserves pinned child identity, rotates all controllers and reconnects existing attempts', async t => {
  const f = await fixture(t); const parent = await f.start(); const call = await claim(f.runtime, parent, 'call');
  const child = (await f.runtime.startSubworkflow(parent.run_id, args(parent, call))).child; const work = await claim(f.runtime, child, 'work');
  await f.store.delete('child', f.child.revision_hash); await f.store.delete('parent', f.parent.revision_hash);
  const recovery = await adoptRunTree(f.runtime, parent.run_id, { expected_sequence: (await f.runtime.get(parent.run_id)).sequence, reason: 'Synthetic tree recovery', main_actor: 'root' });
  assert.deepEqual(recovery.errors, []); assert.equal(recovery.authorities.size, 2);
  await assert.rejects(f.runtime.pause(child.run_id, child), { code: 'RUN_AUTHORITY' });
  const newChild = { run_id: child.run_id, control_token: recovery.authorities.get(child.run_id).control_token };
  const dispatch = recovery.authorities.get(parent.run_id).state.nodes.call.attempts[0].dispatch;
  const reattached = await reattachAttempt(f.runtime, parent.run_id, args(recovery.run, call), { kind: 'subworkflow_exact_identity', attempt_id: call.attempt_id, dispatch_request_id: dispatch.request_id, receipt: dispatch.receipt });
  await f.runtime.resume(parent.run_id, recovery.run);
  const recoveredWork = await reattachAttempt(f.runtime, child.run_id, args(newChild, work), { kind: 'unsubmitted_claim' });
  await f.runtime.resume(child.run_id, newChild); await complete(f.runtime, newChild, recoveredWork.envelope, { value: 9 });
  await complete(f.runtime, newChild, await claim(f.runtime, newChild, 'final'), { value: 9 }, { acceptance: { accepted: true } });
  const accepted = await f.runtime.collectSubworkflow(parent.run_id, args(recovery.run, reattached.envelope)); assert.deepEqual(accepted.nodes.call.output, { result: { value: 9 } });
  assert.equal((await f.runtime.runs.list()).length, 2); assert.equal(accepted.nodes.call.attempts.length, 1);
});

test('child execution pins survive library deletion, reconcile exact identity and require main acceptance before namespaced collection', async t => {
  const f = await fixture(t); const parent = await f.start(); const call = await claim(f.runtime, parent, 'call');
  await f.store.delete('child', f.child.revision_hash); await f.store.delete('parent', f.parent.revision_hash);
  const started = await f.runtime.startSubworkflow(parent.run_id, args(parent, call)); const child = started.child;
  assert.equal(child.workflow_revision, f.child.revision_hash); assert.deepEqual(child.inputs, { task: 'Synthetic child task' });
  const restarted = await new WorkflowRuntime(f.options).initialize();
  assert.equal((await restarted.startSubworkflow(parent.run_id, args(parent, call))).child.run_id, child.run_id);
  assert.equal((await restarted.runs.list()).length, 2);
  const record = await restarted.runs.read(child.run_id); const resource = record.pins.root.resources[0];
  assert.equal(await readFile(join(restarted.runs.directory(child.run_id), 'objects', resource.sha256), 'utf8'), 'Pinned child resource');
  await assert.rejects(complete(restarted, parent, call, { forged: true }), { code: 'CHILD_ACCEPTANCE_REQUIRED' });
  await assert.rejects(restarted.collectSubworkflow(parent.run_id, args(parent, call)), { code: 'CHILD_ACCEPTANCE_REQUIRED' });
  await complete(restarted, child, await claim(restarted, child, 'work'), { value: 9 });
  const final = await claim(restarted, child, 'final');
  await assert.rejects(complete(restarted, child, final, { accepted_value: 9 }), { code: 'FINAL_ACCEPTANCE_REQUIRED' });
  await complete(restarted, child, final, { accepted_value: 9 }, { acceptance: { accepted: true } });
  const collected = await restarted.collectSubworkflow(parent.run_id, args(parent, call));
  assert.deepEqual(collected.nodes.call.output, { result: { accepted_value: 9 } }); assert.equal(collected.nodes.final.status, 'ready');
  assert.equal((await restarted.collectSubworkflow(parent.run_id, args(parent, call))).idempotent, true);
});

test('SubWorkflow checks source locations before its first child intent but not after admitted child edits', async t => {
  const childWorkflow = workflow('child');
  childWorkflow.inputs_schema = { type: 'object', properties: { task: { type: 'string' }, locations: structuredClone(WORKSPACE_SOURCE_LOCATIONS_SCHEMA) },
    required: ['task', 'locations'], additionalProperties: false };
  Object.assign(childWorkflow.nodes.find(node => node.id === 'work'), {
    access: 'bounded_write', path_scope: { binding: 'run.allowed_paths' }, input_bindings: { locations: '/inputs/locations' },
  });
  const f = await fixture(t, { childWorkflow,
    callChanges: { access: 'bounded_write', path_scope: { binding: 'run.allowed_paths' },
      input_bindings: { task: '/inputs/task', locations: '/nodes/source/output/locations' } },
    parentMutate: parent => {
      const source = agent('source');
      source.outputs_schema = { type: 'object', properties: { locations: structuredClone(WORKSPACE_SOURCE_LOCATIONS_SCHEMA) },
        required: ['locations'], additionalProperties: false };
      source.output_validators = { locations: WORKSPACE_SOURCE_LOCATIONS };
      parent.nodes.splice(1, 0, source);
      parent.edges = [['start', 'source'], ['source', 'call'], ['call', 'final'], ['final', 'end']]
        .map(([from, to]) => ({ id: `${from}-${to}`, source: from, target: to }));
    },
  });
  const original = 'export function item() { return 1; }\n';
  await writeFile(join(f.workspace, 'source.mjs'), original);
  const parent = await f.start({ access: 'bounded_write', allowed_paths: ['.'] });
  const source = await claim(f.runtime, parent, 'source');
  await complete(f.runtime, parent, source, { locations: [{ path: join(f.workspace, 'source.mjs'), file_sha256: digest(original),
    start_line: 1, end_line: 1, symbol: 'item', usage: 'Edit item.' }] });
  const call = await claim(f.runtime, parent, 'call');
  await writeFile(join(f.workspace, 'source.mjs'), original + '// external edit before dispatch\n');
  await assert.rejects(f.runtime.startSubworkflow(parent.run_id, args(parent, call)),
    { code: 'SOURCE_LOCATION_STALE', reason: 'file_sha256_mismatch' });
  assert.equal((await f.runtime.runs.read(parent.run_id)).state.nodes.call.attempts[0].dispatch, null);
  assert.equal((await f.runtime.runs.list()).length, 1);
  await writeFile(join(f.workspace, 'source.mjs'), original);
  const started = await f.runtime.startSubworkflow(parent.run_id, args(parent, call));
  const child = started.child;
  const edit = await claim(f.runtime, child, 'work');
  await prepareHost(f.runtime, child, edit);
  await writeFile(join(f.workspace, 'source.mjs'), original + '// authorized child edit\n');
  const replay = await f.runtime.startSubworkflow(parent.run_id, args(parent, call));
  assert.equal(replay.idempotent, true);
  assert.equal(replay.child.run_id, child.run_id);
  assert.equal((await f.runtime.runs.list()).length, 2);
});

test('child failure cannot release the parent until sibling execution has drained', async t => {
  const childWorkflow = workflow('child');
  childWorkflow.nodes = [childWorkflow.nodes[0], { id: 'fork', type: 'parallel', join_id: 'join' }, childWorkflow.nodes[1], agent('sibling'),
    { id: 'join', type: 'join', parallel_id: 'fork' }, childWorkflow.nodes[2], childWorkflow.nodes[3]];
  childWorkflow.edges = [['start', 'fork'], ['fork', 'work'], ['fork', 'sibling'], ['work', 'join'], ['sibling', 'join'],
    ['join', 'final'], ['final', 'end']].map(([source, target]) => ({ id: source + '-' + target, source, target,
      ...(source === 'fork' ? { label: target } : {}) }));
  const childValidation = validateWorkflowGraph(childWorkflow);
  assert(childValidation.valid, JSON.stringify(childValidation.errors));
  const f = await fixture(t, { childWorkflow });
  const admission = new AttemptAdmissionRegistry();
  const manager = () => ({ entries: new Map(), fenceRun() {}, fenceAttempt() {}, async stopRun() {}, async stopAttempt() {} });
  const coordinator = new RunExecutionCoordinator({ admission, strictManager: manager(), managedNativeManager: manager(), hostMainManager: manager(), registry: {} });
  coordinator.bind(f.runtime);
  f.runtime.executionAdmission = admission;
  f.runtime.fenceRunExecution = id => coordinator.fenceRun(id);
  f.runtime.fenceAttemptExecution = (runId, nodeId, attemptId) => coordinator.fenceAttempt(runId, nodeId, attemptId);
  f.runtime.scheduleRunDrain = id => coordinator.scheduleDrain(id);
  f.runtime.failAttemptAfterQuiescence = (runId, binding, error) => coordinator.failAttemptAfterQuiescence(runId, binding, error);
  const parent = await f.start(); const call = await claim(f.runtime, parent, 'call');
  const child = (await f.runtime.startSubworkflow(parent.run_id, args(parent, call))).child;
  const work = await claim(f.runtime, child, 'work'); const sibling = await claim(f.runtime, child, 'sibling');
  const owner = admission.begin(child.run_id, 'sibling', sibling.attempt_id, 'host_tool');
  await f.runtime.failNode(child.run_id, { ...args(child, work), error: { code: 'FIXTURE_FAILURE', message: 'Child failed' } });
  const failureBoundary = f.runtime.failAttemptAfterQuiescence;
  f.runtime.failAttemptAfterQuiescence = null;
  await assert.rejects(f.runtime.collectSubworkflow(parent.run_id, args(parent, call)), { code: 'EXECUTION_COORDINATOR_REQUIRED' });
  f.runtime.failAttemptAfterQuiescence = failureBoundary;
  const collecting = f.runtime.collectSubworkflow(parent.run_id, args(parent, call));
  await new Promise(resolve => setTimeout(resolve, 25));
  assert.equal((await f.runtime.get(parent.run_id)).nodes.call.status, 'running');
  owner.settle();
  assert.equal((await collecting).nodes.call.status, 'failed');
  await coordinator.waitDrain(child.run_id); await coordinator.waitDrain(parent.run_id);
});

test('parent pause blocks child release and dispatch while active completion survives; cancellation fences and records the tree', async t => {
  const f = await fixture(t); const parent = await f.start(); const call = await claim(f.runtime, parent, 'call');
  const child = (await f.runtime.startSubworkflow(parent.run_id, args(parent, call))).child;
  const work = await claim(f.runtime, child, 'work'); await prepareHost(f.runtime,child,work); await f.runtime.pause(parent.run_id, parent);
  await assert.rejects(f.runtime.execution(child.run_id, args(child, work)), { code: 'PARENT_RUN_INACTIVE' });
  await complete(f.runtime, child, work); assert.deepEqual((await f.runtime.next(child.run_id)).ready, []);
  await assert.rejects(claim(f.runtime, child, 'final'), { code: 'PARENT_RUN_INACTIVE' });
  await f.runtime.resume(parent.run_id, parent); const final = await claim(f.runtime, child, 'final');
  assert.deepEqual((await f.runtime.cancelTree(parent.run_id, parent)).sort(), [parent.run_id, child.run_id].sort());
  assert.equal((await f.runtime.get(child.run_id)).status, 'cancelled');
  await assert.rejects(f.runtime.execution(child.run_id, args(child, final), { allowPaused: true }), { code: 'PARENT_LEASE_INACTIVE' });
});

test('child permissions intersect paths, preserve parent approval and reject write or Skill escalation before launch', async t => {
  const writing = workflow('child'); writing.nodes[1].access = 'bounded_write'; writing.nodes[1].path_scope = ['src'];
  const f = await fixture(t, { childWorkflow: writing, callChanges: { access: 'bounded_write', path_scope: ['src/narrow'], approval: { required: true } } });
  await assert.rejects(f.start(), { code: 'NODE_WRITE_UNAUTHORIZED' });
  const parent = await f.start({ access: 'bounded_write', allowed_paths: ['src', 'docs'] });
  assert.equal(parent.nodes.call.status, 'blocked'); await f.runtime.approve(parent.run_id, { ...parent, approval_id: parent.nodes.call.approval_id, decision: true });
  const call = await claim(f.runtime, parent, 'call'); const child = (await f.runtime.startSubworkflow(parent.run_id, args(parent, call))).child;
  assert.deepEqual(child.permissions.allowed_paths, ['src/narrow']); assert.equal(child.require_approval, true); assert.equal(child.nodes.work.status, 'blocked');
  await f.runtime.approve(child.run_id, { ...child, approval_id: child.nodes.work.approval_id, decision: true });
  assert.deepEqual((await claim(f.runtime, child, 'work')).effective_allowed_paths, ['src/narrow']);
  const strict = { mode: 'strict', implicit: 'deny', ambient_allow: [], shadowed_skill_paths: [] };
  const source = join(f.root, 'denied', 'SKILL.md'); const linked = workflow('linked'); linked.skill_policy = strict;
  linked.nodes[1].type = 'skill_ref'; linked.nodes[1].skill_ref = { path: source, allowed_nested_skills: [] };
  assert.throws(() => childPermissions({ ...callNode(f.child), skill_policy: strict }, { permissions: { workspace: f.workspace, access: 'read_only', allowed_paths: [] } }, { root: { workflow: { skill_policy: strict } } }, { workflow: linked }), { code: 'CHILD_SKILL_ESCALATION' });
  const wider = { ...linked, nodes: [], skill_policy: { ...strict, ambient_allow: [source] } };
  assert.throws(() => childPermissions(callNode(f.child), { permissions: { workspace: f.workspace, access: 'read_only', allowed_paths: [] } }, { root: { workflow: { skill_policy: strict } } }, { workflow: wider }), { code: 'SKILL_POLICY_ESCALATION' });
});

test('child creation crash after publication reopens its journal instead of duplicating or resetting execution', async t => {
  const f = await fixture(t); const parent = await f.start(); const call = await claim(f.runtime, parent, 'call');
  const original = f.runtime.runs.create.bind(f.runtime.runs); let publications = 0;
  f.runtime.runs.create = async (...values) => { await original(...values); publications++; throw Object.assign(new Error('Synthetic crash after child publication'), { code: 'INJECTED_CRASH' }); };
  await assert.rejects(f.runtime.startSubworkflow(parent.run_id, args(parent, call)), { code: 'INJECTED_CRASH' });
  assert.equal((await f.runtime.get(parent.run_id)).nodes.call.attempts[0].dispatch.phase, 'intent');
  const restarted = await new WorkflowRuntime(f.options).initialize(); const child = (await restarted.startSubworkflow(parent.run_id, args(parent, call))).child;
  assert.equal(publications, 1); assert.equal((await restarted.runs.list()).length, 2); assert.equal(child.sequence, 1);
  await writeFile(join(restarted.runs.directory(child.run_id), 'events.jsonl'), 'corrupt\n');
  await assert.rejects(restarted.startSubworkflow(parent.run_id, args(parent, call)), /JSON|journal|event/i);
});

test('child validation rejects unbound required inputs and output pointers outside the child namespace', async t => {
  const f = await fixture(t); const broken = structuredClone(f.parent.workflow); const call = broken.nodes[1];
  call.input_bindings = {}; call.subworkflow.output_bindings = { stolen: '/inputs/task' };
  const result = validateWorkflowGraph(broken, { workflows: { ['child@' + f.child.revision_hash]: f.child.workflow } });
  assert(result.errors.some(item => item.code === 'SUBWORKFLOW_INPUT_BINDINGS')); assert(result.errors.some(item => item.code === 'SUBWORKFLOW_OUTPUT_BINDINGS'));
  assert.equal(childIdentity('a', 'b', 'c', 'secret').run_id.length, 64);
});

test('grandchildren inherit ancestor fencing and journal corruption still reports every known session for shutdown', async t => {
  const f = await fixture(t); const grandPack = await f.store.create(workflow('grand'));
  f.store.validationContext.workflows['grand@' + grandPack.revision_hash] = grandPack.workflow;
  const nestedDefinition = workflow('child', { ...callNode(grandPack), id: 'work' });
  const nested = await f.store.save('child', nestedDefinition, { expected_revision: f.child.revision_hash });
  f.store.validationContext.workflows['child@' + nested.revision_hash] = nested.workflow;
  await f.store.save('parent', workflow('parent', callNode(nested)), { expected_revision: f.parent.revision_hash });
  const parent = await f.start(); const child = (await f.runtime.startSubworkflow(parent.run_id, args(parent, await claim(f.runtime, parent, 'call')))).child;
  const grand = (await f.runtime.startSubworkflow(child.run_id, args(child, await claim(f.runtime, child, 'work')))).child;
  await f.runtime.pause(parent.run_id, parent);
  await assert.rejects(claim(f.runtime, grand, 'work'), { code: 'PARENT_RUN_INACTIVE' });
  await f.runtime.resume(parent.run_id, parent); const lease = await claim(f.runtime, grand, 'work');
  await writeFile(join(f.runtime.runs.directory(grand.run_id), 'events.jsonl'), 'corrupt\n');
  await assert.rejects(f.runtime.cancelTree(parent.run_id, parent), error => error.code === 'CHILD_CANCELLATION_INCOMPLETE' && [parent.run_id, child.run_id, grand.run_id].every(id => error.fenced_run_ids.includes(id)));
  assert.equal((await f.runtime.get(parent.run_id)).status, 'cancelled'); assert.equal((await f.runtime.get(child.run_id)).status, 'cancelled');
  assert.equal(lease.access, 'read_only');
});
