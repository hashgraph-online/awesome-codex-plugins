import test from 'node:test';
import {spawn} from 'node:child_process';
import {once} from 'node:events';
import assert from 'node:assert/strict';
import { mkdir, mkdtemp, rm, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { tmpdir } from './physical-tempdir.mjs';
import { HostMainManager, closeHostMainManagers, hostMainManagerFor } from '../lib/execution/host-main-manager.mjs';
import { buildHostMainWorkerTerminal, readHostMainWorker, waitForDetachedHostMainStop, stopOwnedSessions, writeHostMainWorker } from '../lib/execution/host-main-worker.mjs';
import { canonicalJSON, digest } from '../lib/workflow-revisions.mjs';
import { WORKSPACE_SOURCE_LOCATIONS, WORKSPACE_SOURCE_LOCATIONS_SCHEMA } from '../lib/workspace-source-locations.mjs';
import {rejectWorkspaceScope} from '../lib/execution/workspace-scope-evidence.mjs';

const deferred = () => { let resolve; const promise = new Promise(done => { resolve = done; }); return { promise, resolve }; };

test('scope rejection preserves exact paths and hashes before releasing snapshots',async()=>{
  let saved,observed;
  const args={runId:'trial',attemptId:'attempt',code:'HOST_MAIN_SCOPE_VIOLATION',changed:['allowed.txt','.pytest_cache/nodeids'],outside:['.pytest_cache/nodeids'],
    before:new Map([['allowed.txt','a'.repeat(64)]]),after:new Map([['allowed.txt','b'.repeat(64)],['.pytest_cache/nodeids','c'.repeat(64)]]),
    runtime:{runs:{saveArtifact:async(id,label,bytes)=>{saved={id,label,report:JSON.parse(bytes)};return {artifact:'artifact-scope-attempt-hash.bin',sha256:'d'.repeat(64),bytes:bytes.length};}}},
    event:async(kind,metadata)=>{observed={kind,metadata};}};
  await assert.rejects(rejectWorkspaceScope(args),error=>error.code===args.code&&error.message.includes('.pytest_cache/nodeids')&&error.message.includes('artifact-scope-attempt-hash.bin'));
  assert.deepEqual(saved.report.outside_paths,args.outside);assert.equal(saved.report.changes[1].before_sha256,null);assert.equal(saved.report.changes[1].after_sha256,'c'.repeat(64));
  assert.equal(observed.kind,'scope_violation');assert.equal(observed.metadata.outside_count,1);
  args.runtime.runs.saveArtifact=async()=>{throw new Error('disk failed');};
  await assert.rejects(rejectWorkspaceScope(args),error=>error instanceof AggregateError&&error.errors[1].message==='disk failed');
});

test('a dead detached worker is detected before its fresh heartbeat expires',async t=>{
  const root=await mkdtemp(join(tmpdir(),'host-main-exit-'));
  t.after(()=>rm(root,{recursive:true,maxRetries:3,retryDelay:100}));
  const child=spawn(process.execPath,['-e',''],{windowsHide:true});const pid=child.pid;await once(child,'exit');
  const runDir=join(root,'workflow-runs','run-example.run');await mkdir(runDir,{recursive:true});
  await writeFile(join(runDir,'host-main-worker.json'),JSON.stringify({run_id:'example',pid,phase:'running',at:new Date().toISOString()}));
  const health=await readHostMainWorker(join(root,'control-plane.json'),'example');
  assert.equal(health.phase,'failed');assert.equal(health.error.code,'HOST_MAIN_WORKER_EXIT');
});

test('an absent detached Host heartbeat is reported as stale instead of looking like idle progress', async t => {
  const root = await mkdtemp(join(tmpdir(), 'host-main-heartbeat-'));
  t.after(() => rm(root, { recursive: true, maxRetries: 3, retryDelay: 100 }));
  const runDir = join(root, 'workflow-runs', 'run-example.run'); await mkdir(runDir, { recursive: true });
  await writeFile(join(runDir, 'host-main-worker.json'), JSON.stringify({ run_id: 'example', pid: 1, phase: 'running', at: new Date(Date.now() - 60_000).toISOString() }));
  const health = await readHostMainWorker(join(root, 'control-plane.json'), 'example');
  assert.equal(health.phase, 'stale'); assert.equal(health.error.code, 'HOST_MAIN_WORKER_STALE');
});

test('unknown detached worker phase cannot confirm Run cancellation', async t => {
  const root = await mkdtemp(join(tmpdir(), 'host-main-phase-'));
  t.after(() => rm(root, { recursive: true, maxRetries: 3, retryDelay: 100 }));
  const runDir = join(root, 'workflow-runs', 'run-example.run'); await mkdir(runDir, { recursive: true });
  await writeFile(join(runDir, 'host-main-worker.json'), JSON.stringify({ run_id: 'example', pid: process.pid,
    phase: 'unknown_phase', at: new Date().toISOString() }));
  await assert.rejects(waitForDetachedHostMainStop(join(root, 'control-plane.json'), 'example'), { code: 'HOST_MAIN_WORKER_PHASE' });
});

test('confirmed Run cancellation records HOST_MAIN_STOPPED as internal diagnostic and exits successfully', async t => {
  const root = await mkdtemp(join(tmpdir(), 'host-main-cancel-terminal-'));
  t.after(() => rm(root, { recursive: true, maxRetries: 3, retryDelay: 100 }));
  const configPath = join(root, 'control-plane.json'), runId = 'cancelled-run';
  const runDirectory = join(root, 'workflow-runs', `run-${runId}.run`);
  await mkdir(runDirectory, { recursive: true });
  const expectedError = { code: 'HOST_MAIN_STOPPED', diagnostic: 'Host Main permission was revoked', secondary_codes: [] };
  const terminal = buildHostMainWorkerTerminal({ status: 'failed', error: expectedError }, { reason: 'cancelled' });

  assert.equal(terminal.phase, 'cancelled');
  assert.equal(terminal.exitCode, 0);
  assert.equal(terminal.record.error, undefined);
  assert.deepEqual(terminal.record.termination, { confirmed: true, reason: 'cancelled', host_main_error: expectedError });
  await writeHostMainWorker(configPath, runId, terminal.phase, terminal.record);
  const persisted = await readHostMainWorker(configPath, runId);
  assert.equal(persisted.phase, 'cancelled');
  assert.equal(persisted.error, undefined);
  assert.deepEqual(persisted.termination, terminal.record.termination);
});

test('secondary cleanup errors and audit failures remain failed and cannot confirm detached stop', async t => {
  const root = await mkdtemp(join(tmpdir(), 'host-main-cleanup-terminal-'));
  t.after(() => rm(root, { recursive: true, maxRetries: 3, retryDelay: 100 }));
  const configPath = join(root, 'control-plane.json');
  const withSecondary = buildHostMainWorkerTerminal({ status: 'failed', error: {
    code: 'HOST_MAIN_STOPPED', diagnostic: 'permission was revoked', secondary_codes: ['SESSION_CLEANUP_FAILED'],
  } }, { reason: 'cancelled' });
  assert.equal(withSecondary.phase, 'failed');
  assert.equal(withSecondary.exitCode, 1);
  assert.deepEqual(withSecondary.record.error.secondary_codes, ['SESSION_CLEANUP_FAILED']);

  const secondaryRunId = 'cleanup-failed-run';
  await mkdir(join(root, 'workflow-runs', `run-${secondaryRunId}.run`), { recursive: true });
  await writeHostMainWorker(configPath, secondaryRunId, withSecondary.phase, withSecondary.record);
  await assert.rejects(waitForDetachedHostMainStop(configPath, secondaryRunId), { code: 'HOST_MAIN_STOPPED' });

  const authorityRevoked = buildHostMainWorkerTerminal({ status: 'failed', error: {
    code: 'HOST_MAIN_STOPPED', diagnostic: 'permission was revoked', secondary_codes: [],
  } }, { reason: 'authority_revoked' });
  assert.equal(authorityRevoked.phase, 'stopped');
  assert.equal(authorityRevoked.exitCode, 0);
  assert.equal(authorityRevoked.record.error, undefined);
  assert.equal(authorityRevoked.record.termination.host_main_error.code, 'HOST_MAIN_STOPPED');

  const cleanupFailure = buildHostMainWorkerTerminal({ status: 'audit_or_cleanup_failed', error: {
    code: 'HOST_MAIN_STOPPED', diagnostic: 'permission was revoked', secondary_codes: [],
  } }, { reason: 'cancelled' });
  assert.equal(cleanupFailure.phase, 'audit_or_cleanup_failed');
  assert.equal(cleanupFailure.exitCode, 1);
  assert.deepEqual(cleanupFailure.record.error.secondary_codes, []);

  const cleanupRunId = 'audit-cleanup-failed-run';
  await mkdir(join(root, 'workflow-runs', `run-${cleanupRunId}.run`), { recursive: true });
  await writeHostMainWorker(configPath, cleanupRunId, cleanupFailure.phase, cleanupFailure.record);
  await assert.rejects(waitForDetachedHostMainStop(configPath, cleanupRunId), { code: 'HOST_MAIN_STOPPED' });
});

test('Host Main schedules pre-Main work without making launch wait for it', async () => {
  const gate = deferred(); let advances = 0;
  const manager = new HostMainManager({ configPath: 'C:\\fixture\\host-main-background.json', getConfig: async () => ({}), qualify: async () => ({}) });
  const launched = await manager.launchRun({ runId: 'run-background', controlToken: 'private', owner: 'root', runtime: {},
    drive: { async advanceToMain(_runId,options) { advances++; assert.equal(Object.hasOwn(options,'managedProviders'),false); return gate.promise; } } });
  assert.equal(launched.run_id, 'run-background');
  assert(['starting', 'running'].includes(launched.status));
  gate.resolve({ status: 'running', stop_reason: 'no_deterministic_progress' });
  const settled = await manager.wait('run-background');
  assert.equal(advances, 1); assert.equal(settled.status, 'attention');
  await manager.close();
});

test('background pre-Main failure remains visible in the Run journal and Main status', async () => {
  const state = { status: 'running', error: null };
  const runtime = { quiesceFailedOrigin: async () => {}, runs: {
    read: async () => ({ state, pins: { root: { workflow: { finalization: null } } } }),
    mutate: async (_id, _kind, update) => update(state),
  }, next: async () => ({ approvals: [], parent_block: null }) };
  const manager = new HostMainManager({ configPath: 'C:\\fixture\\host-main-background-failure.json', getConfig: async () => ({}), qualify: async () => ({}) });
  await manager.launchRun({ runId: 'run-background-failure', controlToken: 'private', owner: 'root', runtime,
    drive: { async advanceToMain() { throw Object.assign(new Error('Drive could not advance'), { code: 'DRIVE_FAILED' }); } } });
  const settled = await manager.wait('run-background-failure');
  assert.equal(settled.status, 'failed');
  assert.equal(state.status, 'failed');
  assert.equal(state.error.code, 'HOST_MAIN_ADVANCE_FAILED');
  assert.match(state.error.message, /DRIVE_FAILED/);
  const pending = await manager.pending(runtime, 'run-background-failure');
  assert.equal(pending.kind, 'host_main'); assert.equal(pending.error.code, 'DRIVE_FAILED');
  await manager.close();
});

test('stopping a background Run prevents its delayed pre-Main handoff from launching', async () => {
  const gate = deferred(), entered = deferred();
  const manager = new HostMainManager({ configPath: 'C:\\fixture\\host-main-background-stop.json', getConfig: async () => ({}), qualify: async () => ({}) });
  manager.executeNode = async () => assert.fail('stopped Run must not launch its Main node');
  await manager.launchRun({ runId: 'run-background-stop', controlToken: 'private', owner: 'root',
    runtime: { quiesceFailedOrigin: async () => {} }, drive: { async advanceToMain() {
      entered.resolve(); return gate.promise;
    } } });
  await entered.promise;
  const stopping = manager.stopRun('run-background-stop');
  gate.resolve({ stop_reason: 'main_node', host_binding: { run_id: 'run-background-stop', node_id: 'main', attempt_id: 'attempt' } });
  await stopping;
  assert.equal(manager.entries.get('run-background-stop').status, 'failed');
  await manager.close();
});

const output = final => ({ type: 'object', properties: {
  value: { type: 'string' }, ...(final ? { accepted: { type: 'boolean' } } : {}),
}, required: final ? ['value', 'accepted'] : ['value'], additionalProperties: false });

for (const finalDeclaresAcceptance of [true, false]) test(`ordinary logical Main finalizes without a human gate (${finalDeclaresAcceptance ? 'declared' : 'implicit'} acceptance)`, async t => {
  const root = await mkdtemp(join(tmpdir(), 'host-main-manager-')); const workspace = join(root, 'workspace'); await mkdir(workspace);
  t.after(() => rm(root, { recursive: true, maxRetries: 3, retryDelay: 100 }));
  const definitions = [
    { id: 'work', type: 'agent', executor: { kind: 'main' }, role: 'implementer', outputs_schema: output(false) },
    { id: 'final', type: 'agent', executor: { kind: 'main' }, role: 'finalizer', outputs_schema: output(finalDeclaresAcceptance) },
  ];
  const state = { status: 'running', main_actor: 'logical-main', constraints: {}, nodes: {
    work: { status: 'running', active_attempt_id: 'attempt-work', attempts: [{ id: 'attempt-work', status: 'running' }] },
    final: { status: 'pending', active_attempt_id: null, attempts: [] },
  } };
  const record = { pins: { root: { workflow: { nodes: definitions, finalization: { required: true, node_id: 'final' } }, resources: [], provenance: { kind: 'fixture' } } }, state };
  const envelopes = {
    work: { executor: { kind: 'main' }, skill_ref: null, allowed_skills: [], resources: [], inputs: {}, access: 'read_only', workspace,
      effective_allowed_paths: [], constraints: {}, prompt_template: 'FIRST-NODE-ONLY', outputs_schema: output(false) },
    final: { executor: { kind: 'main' }, skill_ref: null, allowed_skills: [], resources: [], inputs: { prior: { value: 'first' } }, access: 'read_only', workspace,
      effective_allowed_paths: [], constraints: {}, prompt_template: 'SECOND-NODE-ONLY with declared prior first', outputs_schema: output(finalDeclaresAcceptance) },
  };
  const receipts = [], usages = [], completions = [], completionChoices = [], proposals = [], sessions = [], savedArtifacts = [];
  const runtime = {
    workflows: { root: join(root, 'workflows') },
    runs: {
      root: join(root, 'runs'), directory: () => join(root, 'runs', 'run-1'), read: async () => record,
      saveArtifact: async (_run, label, bytes) => { savedArtifacts.push({ label, bytes }); return { artifact: `artifact-${label}-${'c'.repeat(64)}.bin`, sha256: 'c'.repeat(64), bytes: bytes.length }; },
      saveExecutorResult: async (_run, attempt, completion) => { assert(Buffer.byteLength(canonicalJSON(completion)) < 256 * 1024); proposals.push({ attempt, completion }); return { artifact: `executor-${attempt}-${'a'.repeat(64)}.json`, sha256: 'a'.repeat(64) }; },
    },
    execution: async (_run, binding) => envelopes[binding.node_id],
    recordHostMainDispatchReceipt: async (_run, args) => receipts.push(args.receipt),
    reserveHostMainTurn: async () => {},
    recordExecutorEvent: async (_run, args) => {
      if (args.event.kind !== 'result_proposed') return;
      const attempt = state.nodes[args.node_id].attempts.find(item => item.id === args.attempt_id);
      attempt.result_proposal = args.event.metadata;
    },
    recordHostMainUsage: async (_run, args) => usages.push(args.usage),
    completeHostMainResult: async (_run, args, choice) => {
      completionChoices.push(choice);
      const proposal = proposals.find(item => item.attempt === args.attempt_id)?.completion;
      assert(proposal, 'fixture must retain the exact Host result proposal');
      completions.push(proposal); state.nodes[args.node_id].status = 'succeeded';
      if (args.node_id === 'final') state.status = 'succeeded';
      return state;
    },
    failNode: async () => assert.fail('compact Main fixture must not fail'),
    get: async () => state,
  };
  const binding = node => ({ protocol: 'host-main-v1', run_id: 'run-1', control_token: 'control', node_id: node,
    attempt_id: `attempt-${node}`, lease_token: `lease-${node}`, owner: 'logical-main', final_acceptance: false });
  const handoff = node => ({ status: 'running', stop_reason: 'main_node', host_binding: binding(node),
    agent_packet: { prompt: envelopes[node].prompt_template, response_form: { schema: output(node === 'final') } } });
  const drive = { advanceToMain: async () => {
    state.nodes.final = { status: 'running', active_attempt_id: 'attempt-final', attempts: [{ id: 'attempt-final', status: 'running' }] };
    return handoff('final');
  } };
  const strict = { enabled: true, codex_binary: process.execPath, binary_sha256: 'b'.repeat(64), authentication: { mode: 'managed_chatgpt', api_key_env: '' }, main_model: 'gpt-5.6-terra', main_reasoning_effort: 'medium', inactivity_timeout_ms: 0 };
  const manager = new HostMainManager({ configPath: join(root, 'control-plane.json'), env: {}, getConfig: async () => ({ global: { enabled: true }, strict_executor: strict, providers: [] }), qualify: async () => strict,
    mainModelSelection: async current => {
      assert.equal(current, record);
      return { model: 'current-user-model', effort: 'xhigh' };
    },
    sessionFactory: async options => {
      const index = sessions.length; sessions.push(options);
      assert.equal(options.model, 'current-user-model');
      assert.equal(options.effort, 'xhigh');
      assert.equal(options.skillPolicy.implicit, "deny");
      assert.equal(options.hostExecutionOnly, undefined);
      const expected = index === 0 ? 'FIRST-NODE-ONLY' : 'SECOND-NODE-ONLY';
      return { async turn(prompt, turnOptions) {
        assert.match(prompt, new RegExp(expected));
        assert.doesNotMatch(prompt, /control|lease|workflow_(?:start|resume|submit|complete)/i);
        assert.equal(turnOptions.output_schema.additionalProperties, false);
        return { output: JSON.stringify(index === 0 ? { value: 'first' } : { value: 'final', ...(finalDeclaresAcceptance ? { accepted: true } : {}) }), thread_id: `thread-${index + 1}`, turn_id: `turn-${index + 1}`,
          usage: { available: true, input_tokens: 10 + index, output_tokens: 2 }, audit: { instruction_sources: [], input_sha256: digest(canonicalJSON([{type:'text',text:prompt}])) }, item_types: ['agentMessage'],
          command_audit: [{ status: 'completed', output: 'x'.repeat(300000) }] };
      }, async close() { options.toolBroker.revoke(); }, async interrupt() {} };
    } });
  const launched = await manager.launch({ runtime, drive, handoff: handoff('work') });
  assert(['starting','running'].includes(launched.status));
  const settled = await manager.wait('run-1');
  assert.equal(settled.status, 'succeeded', JSON.stringify(settled));
  assert.equal(sessions.length, 2); assert.notEqual(sessions[0], sessions[1]);
  assert.deepEqual(sessions.map(item => [item.model, item.effort]), [['current-user-model', 'xhigh'], ['current-user-model', 'xhigh']]);
  for (const session of sessions) {
    const names = session.toolBroker.tools().map(tool => tool.name);
    assert.deepEqual(names, []);
    assert.equal(names.some(name => name.startsWith('workflow_')), false);
  }
  assert.equal(completions.length, 2, 'both ordinary Main nodes are committed automatically');
  assert.deepEqual(completionChoices[1], finalDeclaresAcceptance ? {} : { accepted: true });
  assert.equal(proposals.length, 2); assert.equal(proposals[1].completion.acceptance, undefined);
  assert.deepEqual(receipts.map(item => item.session_id), ['logical-main-run-1', 'logical-main-run-1']);
  assert.equal(receipts[0].invocation_id === receipts[1].invocation_id, false);
  assert.deepEqual(usages.map(item => item.input_tokens), [10, 11]);
  assert(usages.every(item => item.unknown === true && item.available === undefined));
  assert(proposals.every(item => !Object.hasOwn(item.completion.evidence[0], 'command_audit')));
  assert.equal(savedArtifacts.length,2);assert(savedArtifacts.every(item=>item.bytes.length>256*1024));
  await manager.close();
});

test('recoverable blocked Main result gets one correction turn and accounts for both turns', async t => {
  const root = await mkdtemp(join(tmpdir(), 'host-main-correction-')); const workspace = join(root, 'workspace'); await mkdir(workspace);
  t.after(() => rm(root, { recursive: true, maxRetries: 3, retryDelay: 100 }));
  const schema = { type: 'object', properties: { decision: { enum: ['candidate_ready', 'blocked'] } }, required: ['decision'], additionalProperties: false };
  const definition = { id: 'work', type: 'agent', executor: { kind: 'main' }, role: 'implementer',
    decision: { id: 'work-decision', options: ['candidate_ready', 'blocked'], required_references: [] }, outputs_schema: schema };
  const state = { status: 'running', main_actor: 'logical-main', constraints: {}, nodes: { work: { status: 'running', active_attempt_id: 'attempt-1', attempts: [{ id: 'attempt-1', status: 'running' }] } } };
  const record = { pins: { root: { workflow: { nodes: [definition] }, resources: [], provenance: { kind: 'fixture' } } }, state };
  const envelope = { executor: { kind: 'main' }, skill_ref: null, allowed_skills: [], resources: [], inputs: {}, access: 'bounded_write', workspace,
    effective_allowed_paths: ['.'], constraints: {}, prompt_template: 'Create the artifact', outputs_schema: schema };
  const events = []; const usages = []; let turns = 0; let completed = false; let recover = true; let initialBlock = true; let requireArtifacts = false; let failure;
  const runtime = {
    workflows: { root: join(root, 'workflows') }, runs: { root: join(root, 'runs'), read: async () => record,
      saveExecutorResult: async () => ({ artifact: `executor-${'a'.repeat(64)}.json`, sha256: 'a'.repeat(64) }) },
    execution: async () => envelope, recordExecutorEvent: async (_id, args) => events.push(args.event),
    reserveHostMainTurn: async () => {},
    recordHostMainDispatchReceipt: async () => {}, recordHostMainUsage: async (_id, args) => usages.push(args.usage),
    completeHostMainResult: async () => { completed = true; }, failNode: async (_id, args) => { failure = args.error; },
  };
  const binding = { protocol: 'host-main-v1', run_id: 'run-1', control_token: 'control', node_id: 'work', attempt_id: 'attempt-1', lease_token: 'lease', owner: 'logical-main', final_acceptance: false };
  const handoff = { host_binding: binding, agent_packet: { prompt: 'Create the artifact', response_form: { schema } } };
  const strict = { enabled: true, codex_binary: process.execPath, binary_sha256: 'b'.repeat(64), authentication: { mode: 'managed_chatgpt', api_key_env: '' }, main_model: 'gpt-5.6-terra', main_reasoning_effort: 'medium', inactivity_timeout_ms: 0 };
  const manager = new HostMainManager({ configPath: join(root, 'control-plane.json'), env: {}, getConfig: async () => ({ global: { enabled: true }, strict_executor: strict, providers: [] }), qualify: async () => strict,
    sessionFactory: async options => {
      assert.equal(options.maxTurns, 2);
      const runTurn = async (prompt, args) => {
        turns++; assert(args.output_schema.properties.block_reason);
        if (turns === 2) { assert.match(prompt, requireArtifacts ? /compressed_video\.mp4/ : /prior result reported blocked/); assert.doesNotMatch(prompt, /Create the artifact/); }
        if (requireArtifacts && turns === 2 && recover) await writeFile(join(workspace, 'compressed_video.mp4'), 'video');
        return { output: JSON.stringify(initialBlock && (turns === 1 || !recover) ? { decision: 'blocked', block_reason: 'Python invocation failed; correct arguments' }
          : { decision: 'candidate_ready', block_reason: '' }), thread_id: 'thread-1', turn_id: `turn-${turns}`,
          usage: { available: true, input_tokens: 10, output_tokens: 2 }, audit: {input_sha256:digest(canonicalJSON([{type:'text',text:prompt}]))}, item_types: ['agentMessage'] };
      };
      return { turn: runTurn, continueTurn: runTurn, async close() { options.toolBroker.revoke(); }, async interrupt() {} };
    } });
  const entry = { runtime, runId: 'run-1', status: 'running', stopping: false, session: null, broker: null };
  await manager.executeNode(entry, handoff);
  assert.equal(turns, 2); assert.equal(completed, true);
  assert.equal(usages.length, 1); assert.equal(usages[0].input_tokens, 20); assert.equal(usages[0].output_tokens, 4);
  assert.equal(events.filter(item => item.kind === 'semantic_blocked').length, 1);
  recover = false; turns = 0; completed = false; usages.length = 0; events.length = 0;
  await manager.executeNode({ ...entry, session: null, broker: null }, handoff);
  assert.equal(completed, false); assert.equal(turns, 2); assert.equal(usages[0].input_tokens, 20);
  assert.match(failure.message, /Python invocation failed/);
  assert.equal(events.filter(item => item.kind === 'semantic_blocked').length, 2);
  initialBlock = false; turns = 0; completed = false; usages.length = 0; events.length = 0;
  await manager.executeNode({ ...entry, session: null, broker: null }, handoff);
  assert.equal(completed, true); assert.equal(turns, 1); assert.equal(usages[0].input_tokens, 10);
  assert.equal(events.filter(item => item.kind === 'semantic_blocked').length, 0);
  definition.required_artifacts = [{ requirement_id: 'video', path: 'compressed_video.mp4' }];
  requireArtifacts = true; recover = true; turns = 0; completed = false; usages.length = 0; events.length = 0;
  await manager.executeNode({ ...entry, session: null, broker: null }, handoff);
  assert.equal(completed, true); assert.equal(turns, 2, 'false-ready must get one targeted correction turn');
  assert.equal(usages[0].input_tokens, 20);
  assert.equal(events.filter(item => item.kind === 'required_artifacts_missing').length, 1);
  await rm(join(workspace, 'compressed_video.mp4'));
  recover = false; turns = 0; completed = false; usages.length = 0; events.length = 0; failure = null;
  await manager.executeNode({ ...entry, session: null, broker: null }, handoff);
  assert.equal(completed, false); assert.equal(turns, 2);
  assert.equal(failure.code, 'REQUIRED_ARTIFACT_MISSING');
  assert.match(failure.message, /compressed_video\.mp4/);
  assert.equal(events.filter(item => item.kind === 'required_artifacts_missing').length, 2);
  await manager.close();
});

test('Main preflight corrects schema and real source locations in one thread before completion', async t => {
  const root = await mkdtemp(join(tmpdir(), 'host-main-preflight-')), workspace = join(root, 'workspace');
  await mkdir(workspace); t.after(() => rm(root, { recursive: true, maxRetries: 3, retryDelay: 100 }));
  const source = 'export const anchor = true;\n'; await writeFile(join(workspace, 'source.mjs'), source);
  const location = { path: 'source.mjs', file_sha256: digest(source), start_line: 1, end_line: 1, symbol: 'anchor', usage: 'Implement this source' };
  const schema = { type: 'object', properties: { locations: structuredClone(WORKSPACE_SOURCE_LOCATIONS_SCHEMA) }, required: ['locations'], additionalProperties: false };
  const definition = { id: 'work', type: 'agent', executor: { kind: 'main' }, role: 'analyst', retry: { max_attempts: 3 }, outputs_schema: schema,
    output_validators: { locations: WORKSPACE_SOURCE_LOCATIONS } };
  const state = { status: 'running', main_actor: 'logical-main', constraints: {}, nodes: { work: { status: 'running', active_attempt_id: 'attempt-1', attempts: [{ id: 'attempt-1', status: 'running', completion_turns: 0 }] } } };
  const record = { pins: { root: { workflow: { nodes: [definition], finalization: { node_id: 'final' } }, resources: [], provenance: { kind: 'fixture' } } }, state };
  const envelope = { executor: { kind: 'main' }, skill_ref: null, allowed_skills: [], resources: [], inputs: {}, access: 'read_only', workspace,
    effective_allowed_paths: [], constraints: {}, prompt_template: 'Analyze source', outputs_schema: schema };
  const events = [], prompts = []; let completed = false, saved = false, failAll = false;
  const runtime = { workflows: { root: join(root, 'workflows') }, runs: { root: join(root, 'runs'), read: async () => record,
      saveExecutorResult: async () => { saved = true; return { artifact: `executor-${'a'.repeat(64)}.json`, sha256: 'a'.repeat(64) }; } },
    execution: async () => envelope, recordExecutorEvent: async (_id, args) => events.push(args.event), recordHostMainDispatchReceipt: async () => {},
    reserveHostMainTurn: async () => { state.nodes.work.attempts[0].completion_turns++; }, recordHostMainUsage: async () => {},
    completeHostMainResult: async () => { completed = true; }, failNode: async () => assert.fail('Completion should be corrected') };
  const binding = { run_id: 'run-1', control_token: 'control', node_id: 'work', attempt_id: 'attempt-1', lease_token: 'lease' };
  const strict = { enabled: true, codex_binary: process.execPath, binary_sha256: 'b'.repeat(64), authentication: { mode: 'managed_chatgpt', api_key_env: '' }, main_model: 'gpt-5.6-terra', main_reasoning_effort: 'medium', inactivity_timeout_ms: 0 };
  const manager = new HostMainManager({ configPath: join(root, 'control-plane.json'), env: {}, getConfig: async () => ({ global: { enabled: true }, strict_executor: strict, providers: [] }), qualify: async () => strict,
    sessionFactory: async options => {
      assert.equal(options.maxTurns, 3);
      const respond = async (prompt, args) => { prompts.push(prompt); assert(args.output_schema.properties.locations);
        return { output: JSON.stringify(failAll ? { locations: [{ ...location, end_line: 3 }] }
          : prompts.length === 1 ? { locations: 'wrong type' } : prompts.length === 2
          ? { locations: [{ ...location, end_line: 3 }] } : { locations: [location] }),
          thread_id: 'same-thread', turn_id: `turn-${prompts.length}`, usage: { available: true, input_tokens: 10, output_tokens: 2 }, audit: {input_sha256:digest(canonicalJSON([{type:'text',text:prompt}]))}, item_types: ['agentMessage'] }; };
      return { turn: respond, continueTurn: respond, async close() { options.toolBroker.revoke(); }, async interrupt() {} };
    } });
  await manager.executeNode({ runtime, runId: 'run-1', status: 'running', stopping: false }, { host_binding: binding, agent_packet: { prompt: 'Analyze source' } });
  assert.equal(completed, true); assert.equal(saved, true); assert.equal(prompts.length, 3);
  assert.match(prompts[1], /DATA_INVALID/); assert.match(prompts[2], /line_range_invalid/);
  assert.doesNotMatch(prompts[1], /Analyze source/); assert.doesNotMatch(prompts[2], /Analyze source/);
  assert.equal(events.filter(item => item.kind === 'completion_invalid').length, 2);
  failAll = true; prompts.length = 0; events.length = 0; completed = false; saved = false; state.nodes.work.attempts[0].completion_turns = 0;
  await assert.rejects(manager.executeNode({ runtime, runId: 'run-1', status: 'running', stopping: false },
    { host_binding: binding, agent_packet: { prompt: 'Analyze source' } }), { code: 'SOURCE_LOCATION_INVALID', reason: 'line_range_invalid' });
  assert.equal(prompts.length, 3); assert.equal(events.filter(item => item.kind === 'completion_invalid').length, 3);
  assert.equal(completed, false); assert.equal(saved, false);
  await manager.close();
});

test('Host Main retains a session handed off before factory initialization fails', async t => {
  const root = await mkdtemp(join(tmpdir(), 'host-main-factory-failure-')); const workspace = join(root, 'workspace'); await mkdir(workspace);
  t.after(() => rm(root, { recursive: true, maxRetries: 3, retryDelay: 100 }));
  const definition = { id: 'work', type: 'agent', executor: { kind: 'main' }, role: 'implementer', outputs_schema: output(false) };
  const state = { status: 'running', main_actor: 'logical-main', constraints: {}, nodes: {
    work: { status: 'running', active_attempt_id: 'attempt-work', attempts: [{ id: 'attempt-work', status: 'running' }] },
  } };
  const record = { pins: { root: { workflow: { nodes: [definition] }, resources: [], provenance: { kind: 'fixture' } } }, state };
  const envelope = { executor: { kind: 'main' }, skill_ref: null, allowed_skills: [], resources: [], inputs: {}, access: 'read_only', workspace,
    effective_allowed_paths: [], constraints: {}, prompt_template: 'UNREACHED', outputs_schema: output(false) };
  const runtime = {
    workflows: { root: join(root, 'workflows') },
    runs: { root: join(root, 'runs'), directory: () => join(root, 'runs', 'run-factory'), read: async () => record },
    execution: async () => envelope,
    recordExecutorEvent: async () => {},
    failNode: async () => { state.nodes.work.status = 'failed'; },
    failAttemptAfterQuiescence: async (_runId, _args, _error, { originEntry }) => {
      try { await originEntry.session.close(); }
      catch (error) { originEntry.cleanupPending = true; throw error; }
      originEntry.session = null;
      state.nodes.work.status = 'failed';
    },
    get: async () => state,
  };
  const binding = { protocol: 'host-main-v1', run_id: 'run-factory', control_token: 'control', node_id: 'work',
    attempt_id: 'attempt-work', lease_token: 'example-lease-work', owner: 'logical-main', final_acceptance: false };
  const handoff = { status: 'running', stop_reason: 'main_node', host_binding: binding,
    agent_packet: { prompt: envelope.prompt_template, response_form: { schema: output(false) } } };
  const strict = { enabled: true, codex_binary: process.execPath, binary_sha256: 'b'.repeat(64), authentication: { mode: 'managed_chatgpt', api_key_env: '' }, main_model: 'gpt-5.6-terra', main_reasoning_effort: 'medium', inactivity_timeout_ms: 0 };
  let allowClose = false; let closeCalls = 0; let owned;
  const manager = new HostMainManager({ configPath: join(root, 'control-plane.json'), env: {},
    getConfig: async () => ({ global: { enabled: true }, strict_executor: strict, providers: [] }), qualify: async () => strict,
    sessionFactory: async options => {
      owned = { async interrupt() {}, async close() {
        closeCalls++;
        if (!allowClose) throw Object.assign(new Error('Synthetic profile cleanup failure'), { code: 'SYNTHETIC_PROFILE_RETAINED' });
        options.toolBroker.revoke();
      } };
      await options.onSessionOwned(owned);
      const setupError = Object.assign(new Error('Synthetic initialization failure'), { code: 'SYNTHETIC_SESSION_SETUP' });
      try { await owned.close(); }
      catch (cleanupError) {
        throw Object.assign(new AggregateError([setupError, cleanupError], 'Synthetic setup/cleanup failure'), {
          code: 'MANAGED_NATIVE_SETUP_FAILED', retained_at: join(root, 'fake-profile'),
        });
      }
      throw setupError;
    },
  });
  await manager.launch({ runtime, drive: { advanceToMain: async () => assert.fail('factory failure cannot advance') }, handoff });
  const settled = await manager.wait('run-factory');
  const entry = manager.entries.get('run-factory');
  assert.equal(settled.status, 'audit_or_cleanup_failed');
  assert.equal(entry.cleanupPending, true);
  assert.equal(entry.session, owned, 'manager must retain the exact pre-initialization owner');
  assert(closeCalls >= 2, 'factory rollback and manager failure cleanup both reached the owner');
  allowClose = true;
  await manager.stopRun('run-factory');
  assert.equal(entry.cleanupPending, false);
  assert.equal(entry.session, null);
  await manager.close();
});

test('Host Main stop returns with retained ownership when close fails instead of awaiting a pending job', { timeout: 1000 }, async () => {
  const manager = new HostMainManager({ configPath: 'C:\\fixture\\host-main-pending.json', getConfig: async () => ({}), qualify: async () => ({}) });
  let allowClose = false; let settleJob; const job = new Promise(resolve => { settleJob = resolve; });
  const broker = { revoke() {}, isQuiescent() { return true; }, async quiesce() { return { quiescent: true }; } };
  const session = { async interrupt() {}, async close() {
    if (!allowClose) throw Object.assign(new Error('Synthetic close failure'), { code: 'SYNTHETIC_CLOSE_RETAINED' });
    settleJob();
  } };
  const entry = { runId: 'run-pending', status: 'running', stopping: false, cleanupPending: false, broker, session, job, runtime: {}, drive: {}, handoff: {} };
  manager.entries.set('run-pending', entry);
  await assert.rejects(manager.stopRun('run-pending'), error => error instanceof AggregateError && error.code === 'CODEX_EXECUTION_STOP_UNCONFIRMED');
  assert.equal(entry.cleanupPending, true);
  assert.equal(entry.session, session);
  allowClose = true;
  await manager.stopRun('run-pending');
  assert.equal(entry.cleanupPending, false);
  assert.equal(entry.session, null);
});

test('Host Main stop rechecks a cleanup owner published while its job settles', async () => {
  const manager = new HostMainManager({ configPath: 'C:\\fixture\\host-main-late-owner.json', getConfig: async () => ({}), qualify: async () => ({}) });
  const releaseOwner = deferred(); const quiesceEntered = deferred(); let allowClose = false; let closeCalls = 0; let entry;
  const broker = { revoke() {}, isQuiescent() { return true; }, async quiesce() { quiesceEntered.resolve(); return { quiescent: true }; } };
  const session = { async interrupt() {}, async close() {
    closeCalls++; if (!allowClose) throw Object.assign(new Error('Synthetic late profile cleanup failure'), { code: 'SYNTHETIC_PROFILE_RETAINED' });
  } };
  const job = (async () => { await releaseOwner.promise; entry.session = session; entry.cleanupPending = true; })();
  entry = { runId: 'run-late-owner', status: 'running', stopping: false, cleanupPending: false,
    broker, session: null, job, runtime: {}, drive: {}, handoff: {} };
  manager.entries.set('run-late-owner', entry);
  const stopping = manager.stopRun('run-late-owner'); await quiesceEntered.promise; releaseOwner.resolve();
  await assert.rejects(stopping, error => error instanceof AggregateError && error.code === 'CODEX_EXECUTION_STOP_UNCONFIRMED');
  assert.equal(entry.cleanupPending, true); assert.equal(entry.session, session); assert(closeCalls >= 1);
  allowClose = true; await manager.stopRun('run-late-owner');
  assert.equal(entry.cleanupPending, false); assert.equal(entry.session, null);
});

test('Host Main cannot overwrite failed cleanup ownership and a later stop retries it',async()=>{
  const manager=new HostMainManager({configPath:'C:\\fixture\\host-main-retry.json',getConfig:async()=>({}),qualify:async()=>({})});
  let quiescent=false,quiesceCalls=0,closeCalls=0;
  const broker={revoke(){},isQuiescent(){return quiescent;},async quiesce(){quiesceCalls++;if(quiesceCalls===1)return {quiescent:false,error:Object.assign(new Error('stop helper failed'),{code:'CODEX_EXECUTION_STOP_UNCONFIRMED'})};quiescent=true;return {quiescent:true};}};
  const session={async interrupt(){},async close(){closeCalls++;if(closeCalls===1)throw Object.assign(new Error('first close retained profile'),{code:'CODEX_BROKER_STOP_UNCONFIRMED'});}};
  const entry={runId:'run-retry',status:'audit_or_cleanup_failed',stopping:false,cleanupPending:true,broker,session,job:Promise.resolve(),runtime:{},drive:{},handoff:{}};
  manager.entries.set('run-retry',entry);
  await assert.rejects(manager.stopRun('run-retry'),error=>error instanceof AggregateError&&error.code==='CODEX_EXECUTION_STOP_UNCONFIRMED');
  await assert.rejects(manager.launch({runtime:{},drive:{},handoff:{stop_reason:'main_node',host_binding:{run_id:'run-retry',node_id:'next'}}}),{code:'HOST_MAIN_RECOVERY_PENDING'});
  assert.equal(entry.broker,broker);assert.equal(entry.cleanupPending,true);assert.equal(quiesceCalls,1);
  await manager.stopRun('run-retry');
  assert.equal(quiesceCalls,2);assert.equal(quiescent,true);assert.equal(entry.cleanupPending,false);assert.equal(entry.broker,null);assert.equal(entry.session,null);
});

test('global Host Main shutdown keeps a manager registered until retained ownership is recovered',async()=>{
  const options={configPath:'C:\\fixture\\host-global-retry.json',getConfig:async()=>({}),qualify:async()=>({})};
  const manager=hostMainManagerFor(options);let quiescent=false,calls=0;
  const broker={revoke(){},isQuiescent(){return quiescent;},async quiesce(){if(++calls===1)return {quiescent:false};quiescent=true;return {quiescent:true};}};
  manager.entries.set('run-global',{runId:'run-global',status:'failed',stopping:false,cleanupPending:true,broker,session:null,job:Promise.resolve(),runtime:{},drive:{},handoff:{}});
  await assert.rejects(closeHostMainManagers(),AggregateError);assert.equal(hostMainManagerFor(options),manager);
  await closeHostMainManagers();const replacement=hostMainManagerFor(options);assert.notEqual(replacement,manager);await closeHostMainManagers();
});

test('stopping Main cannot advance to a successor after an in-flight Run read', { timeout: 1000 }, async () => {
  const readEntered = deferred(), releaseRead = deferred(); let advances = 0;
  const manager = new HostMainManager({ configPath: 'C:\\fixture\\host-main-stopped-drive.json', getConfig: async () => ({}), qualify: async () => ({}) });
  manager.executeNode = async () => ({ final_acceptance_required: false });
  const entry = { runId: 'run-stopped-drive', status: 'running', stopping: false, cleanupPending: false, broker: null, session: null,
    handoff: { stop_reason: 'main_node', host_binding: { node_id: 'main' } },
    runtime: { async get() { readEntered.resolve(); await releaseRead.promise; return { status: 'running' }; } },
    drive: { async advanceToMain() { advances++; return { stop_reason: 'no_deterministic_progress' }; } } };
  manager.entries.set(entry.runId, entry);
  const loop = manager.executeLoop(entry); entry.job = loop.catch(() => {});
  await readEntered.promise;
  const stopping = manager.stopRun(entry.runId); releaseRead.resolve();
  await Promise.allSettled([loop, stopping]);
  assert.equal(advances, 0, 'a stopped Main must not claim or dispatch its successor');
});

test('terminal node failure is reported before its expected permission revocation', async () => {
  const manager = new HostMainManager({ configPath: 'C:\\fixture\\host-main-terminal.json', getConfig: async () => ({}), qualify: async () => ({}) });
  let advances = 0;
  const entry = { runId: 'run-terminal', status: 'running', stopping: false, cleanupPending: false, broker: null, session: null,
    handoff: { stop_reason: 'main_node', host_binding: { node_id: 'main' } },
    runtime: { async get() { return { status: 'failed' }; } },
    drive: { async advanceToMain() { advances++; throw new Error('terminal Run cannot advance'); } } };
  manager.executeNode = async () => {
    entry.stopping = true; // failNode fences the completed attempt before the loop observes terminal state.
    return { final_acceptance_required: false };
  };
  manager.entries.set(entry.runId, entry);
  const result = await manager.executeLoop(entry);
  assert.equal(result.status, 'failed');
  assert.equal(result.error, undefined);
  assert.equal(advances, 0);
});


test('detached owner cancels native and strict sessions while fencing Main before waiting',async()=>{
 const calls=[];const mainDone=deferred();
 const service={hostMainManager:{fenceRun:id=>calls.push(['fence',id]),stopRun:async id=>{calls.push(['main',id]);await mainDone.promise;}},
 managedNativeManager:{stopRun:async id=>{calls.push(['native',id]);mainDone.resolve();}},
 strictManager:{stopRun:async id=>{calls.push(['strict',id]);}}};
 await stopOwnedSessions(service,'exact-run');
 assert.deepEqual(calls,[['fence','exact-run'],['native','exact-run'],['strict','exact-run'],['main','exact-run']]);
 service.managedNativeManager.stopRun=async()=>{throw new Error('native stop failed');};
 await assert.rejects(stopOwnedSessions(service,'exact-run'),error=>error instanceof AggregateError && error.errors[0].message==='native stop failed');
});
