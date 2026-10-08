import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, readFile, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from './physical-tempdir.mjs';
import { join, resolve } from 'node:path';
import { WorkflowStore } from '../lib/workflow-store.mjs';
import { WorkflowRuntime } from '../lib/workflow-runtime.mjs';
import { createDraft } from '../lib/workflow-schema.mjs';
import { ParallelWorktreeManager } from '../lib/parallel/worktree-manager.mjs';
import { createCodexToolBroker } from '../lib/execution/codex-tool-broker.mjs';
import { digest } from '../lib/workflow-revisions.mjs';
import { hostResultProposalEnvelope } from '../lib/execution/host-main-automation.mjs';

const worker = (id, paths = []) => ({ id, type: 'agent', role: 'implementer', executor: { kind: 'main' }, access: paths.length ? 'bounded_write' : 'read_only',
  path_scope: paths, approval: { required: false }, retry: { max_attempts: 1 }, input_bindings: {}, prompt_template: '{{task}}' });
const edge = (source, target, label) => ({ id: source + '-' + target, source, target, ...(label ? { label } : {}) });
function definition() {
  return { ...createDraft('parallel', 'Parallel integration test'), status: 'ready', finalization: { required: true, node_id: 'final' },
    nodes: [{ id: 'start', type: 'start' }, worker('prelude', ['src/seed.txt']), { id: 'fork', type: 'parallel', join_id: 'join' }, worker('a', ['src/a.txt']), worker('b', ['src/b.txt']), { id: 'join', type: 'join', parallel_id: 'fork' }, { ...worker('final'), role: 'finalizer' }, { id: 'end', type: 'end' }],
    edges: [edge('start', 'prelude'), edge('prelude', 'fork'), edge('fork', 'a', 'a'), edge('fork', 'b', 'b'), edge('a', 'join'), edge('b', 'join'), edge('join', 'final'), edge('final', 'end')] };
}
async function fixture(t, workflow = definition()) {
  const root = await mkdtemp(join(tmpdir(), 'parallel-runtime-')); const workspace = join(root, 'workspace'); await mkdir(workspace);
  const manager = new ParallelWorktreeManager(join(root, 'owned')); await manager.git.initialize();
  await manager.git.git(workspace, ['init', '-b', 'main']); await mkdir(join(workspace, 'src'));
  for (const file of ['a', 'b', 'seed']) await writeFile(join(workspace, 'src', file + '.txt'), 'Base ' + file + '\n');
  await manager.git.git(workspace, ['add', '--all']); await manager.git.git(workspace, ['commit', '-m', 'Synthetic base']);
  const initialIndex = digest(await readFile(join(workspace, '.git', 'index'))); const head = await manager.git.text(workspace, ['rev-parse', 'HEAD']);
  const store = await new WorkflowStore(join(root, 'packs')).initialize(); await store.create(workflow);
  const options = { workflowStore: store, runRoot: join(root, 'runs'), parallelManager: manager, strictCapability: () => true }; // Mechanical runtime tests use the actual bounded broker below.
  const runtime = await new WorkflowRuntime(options).initialize(); const run = await runtime.start({ workflow_id: workflow.id, workspace, access: 'bounded_write', allowed_paths: ['src'], main_actor: 'root' });
  t.after(async () => { assert(resolve(root).startsWith(resolve(tmpdir()))); await rm(root, { recursive: true, maxRetries: 3, retryDelay: 100 }); });
  const claim = async nodeId => { const lease = await runtime.claimHostMain(run.run_id, { node_id: nodeId, owner: 'root', request_id: 'claim-' + nodeId, control_token: run.control_token }); return { ...lease, control_token: run.control_token }; };
  const execute = async (nodeId, path, text) => {
    const args = await claim(nodeId); await manager.ensureNode(runtime, run.run_id, args); const envelope = await runtime.execution(run.run_id, args);
    if (path) {
      const broker = await createCodexToolBroker({ workspace: envelope.workspace, access: envelope.access, allowedPaths: envelope.effective_allowed_paths,
        authorize: () => runtime.execution(run.run_id, args, { allowPaused: true }),
        onOperation: metadata => runtime.recordExecutorEvent(run.run_id, { ...args, event: { kind: 'tool_operation', metadata } }) });
      const before = await readFile(join(envelope.workspace, path)); await broker.call('write_workspace', { path, text, expected_sha256: digest(before) }, 'write-' + nodeId); broker.revoke(); await broker.quiesce();
    }
    const request_id=`dispatch-${args.attempt_id}`;
    await runtime.recordHostMainDispatchIntent(run.run_id,{...args,request_id,envelope_hash:'f'.repeat(64)});
    await runtime.recordHostMainDispatchReceipt(run.run_id,{...args,request_id,receipt:{invocation_id:`host-main-${args.attempt_id}`,executor:'codex-app-server-host-main',executable_sha256:'a'.repeat(64),model:'fixture-main',effort:'medium',main_actor:'root',session_id:`logical-main-${run.run_id}`,call_chain_id:`workflow-run-${run.run_id}`}});
    const definition=(await runtime.runs.read(run.run_id)).pins.root.workflow.nodes.find(node=>node.id===nodeId);
    const proposal=hostResultProposalEnvelope(definition,{output:{verified:true},summary:'Actual broker execution',artifacts:[],evidence:[{broker:true}],changed_paths:path?[path]:[],outside_paths:[]},{finalAcceptance:nodeId==='final'});
    const saved=await runtime.runs.saveExecutorResult(run.run_id,args.attempt_id,proposal);
    await runtime.recordExecutorEvent(run.run_id,{...args,event:{kind:'result_proposed',metadata:{...saved,final_acceptance_required:nodeId==='final'}}});
    await runtime.completeHostMainResult(run.run_id,args,{...(nodeId==='final'?{accepted:true}:{})});
    return envelope;
  };
  return { root, workspace, manager, store, runtime, options, run, claim, execute, initialIndex, head };
}

test('Run forks after serial writes, isolates real broker writes and blocks Join until exact reviewed integration', async t => {
  const f = await fixture(t); await f.execute('prelude', 'src/seed.txt', 'Serial context\n');
  const [a, b] = await Promise.all([f.execute('a', 'src/a.txt', 'Branch A\n'), f.execute('b', 'src/b.txt', 'Branch B\n')]);
  assert.notEqual(a.workspace, b.workspace); assert.equal(await readFile(join(a.workspace, 'src/seed.txt'), 'utf8'), 'Serial context\n');
  assert.equal(await readFile(join(f.workspace, 'src/a.txt'), 'utf8'), 'Base a\n');
  const next = await f.runtime.next(f.run.run_id); assert.equal(next.status, 'blocked'); assert.equal(next.integration_gates[0].region_id, 'fork');
  await assert.rejects(f.claim('final'), { code: 'NODE_NOT_READY' });
  const request = { ...f.run, region_id: 'fork' }; const proposal = await f.manager.prepareIntegration(f.runtime, f.run.run_id, request);
  assert((await f.manager.review(f.runtime, f.run.run_id, request)).patch.includes('Branch A'));
  await assert.rejects(f.manager.integrate(f.runtime, f.run.run_id, { ...request, accepted: true, patch_sha256: 'a'.repeat(64) }), { code: 'PARALLEL_PROPOSAL_CHANGED' });
  await f.manager.integrate(f.runtime, f.run.run_id, { ...request, accepted: true, patch_sha256: proposal.patch_sha256 });
  assert.equal(await readFile(join(f.workspace, 'src/a.txt'), 'utf8'), 'Branch A\n'); assert.equal(await readFile(join(f.workspace, 'src/b.txt'), 'utf8'), 'Branch B\n');
  assert.equal(await readFile(join(f.workspace, 'src/seed.txt'), 'utf8'), 'Serial context\n');
  assert.equal(await f.manager.git.text(f.workspace, ['rev-parse', 'HEAD']), f.head);
  assert.equal(digest(await readFile(join(f.workspace, '.git', 'index'))), f.initialIndex);
  await f.execute('final'); assert.equal((await f.runtime.get(f.run.run_id)).status, 'succeeded');
  const remove = f.manager.git.remove.bind(f.manager.git); let cleanups = 0;
  f.manager.git.remove = async (...values) => { const result = await remove(...values); if (++cleanups === 1) throw Object.assign(new Error('Synthetic crash after removal'), { code: 'CLEANUP_CRASH' }); return result; };
  await assert.rejects(f.manager.cleanup(f.runtime, f.run.run_id, f.run), { code: 'CLEANUP_CRASH' });
  const cleaned = await f.manager.cleanup(f.runtime, f.run.run_id, f.run); assert.equal(cleaned.removed.length, 2);
  assert.deepEqual((await f.manager.cleanup(f.runtime, f.run.run_id, f.run)).removed, []);
});

test('merge target edits and outside branch writes prevent integration without replacing user files', async t => {
  const f = await fixture(t); await f.execute('prelude', 'src/seed.txt', 'Serial context\n');
  const a = await f.execute('a', 'src/a.txt', 'Branch A\n'); await f.execute('b', 'src/b.txt', 'Branch B\n');
  await writeFile(join(a.workspace, 'unexpected.txt'), 'Outside branch scope');
  const request = { ...f.run, region_id: 'fork' };
  await assert.rejects(f.manager.prepareIntegration(f.runtime, f.run.run_id, request), { code: 'PARALLEL_SCOPE_VIOLATION' });
  await rm(join(a.workspace, 'unexpected.txt')); const proposal = await f.manager.prepareIntegration(f.runtime, f.run.run_id, request);
  await writeFile(join(f.workspace, 'src/a.txt'), 'Concurrent user edit\n');
  await assert.rejects(f.manager.integrate(f.runtime, f.run.run_id, { ...request, accepted: true, patch_sha256: proposal.patch_sha256 }), { code: 'PARALLEL_SOURCE_CHANGED' });
  assert.equal(await readFile(join(f.workspace, 'src/a.txt'), 'utf8'), 'Concurrent user edit\n'); assert.equal((await f.runtime.get(f.run.run_id)).nodes.join.status, 'blocked');
  assert.equal((await f.runtime.get(f.run.run_id)).parallel.fork.error.code, 'PARALLEL_SOURCE_CHANGED');
});

test('nested parallel forks integrate into their enclosing branch before the outer main gate', async t => {
  const workflow = definition();
  workflow.nodes = [workflow.nodes[0], workflow.nodes[1], { id: 'outer', type: 'parallel', join_id: 'outer-join' }, { id: 'inner', type: 'parallel', join_id: 'inner-join' }, worker('a', ['src/a.txt']), worker('b', ['src/b.txt']), worker('c', ['src/seed.txt']),
    { id: 'inner-join', type: 'join', parallel_id: 'inner' }, { id: 'outer-join', type: 'join', parallel_id: 'outer' }, workflow.nodes.at(-2), workflow.nodes.at(-1)];
  workflow.edges = [edge('start', 'prelude'), edge('prelude', 'outer'), edge('outer', 'inner', 'inner'), edge('outer', 'c', 'c'), edge('inner', 'a', 'a'), edge('inner', 'b', 'b'), edge('a', 'inner-join'), edge('b', 'inner-join'), edge('inner-join', 'outer-join'), edge('c', 'outer-join'), edge('outer-join', 'final'), edge('final', 'end')];
  const f = await fixture(t, workflow); await f.execute('prelude', 'src/seed.txt', 'Serial context\n');
  await f.execute('a', 'src/a.txt', 'Inner A\n'); await f.execute('b', 'src/b.txt', 'Inner B\n'); await f.execute('c', 'src/seed.txt', 'Outer sibling\n');
  assert.equal((await f.runtime.next(f.run.run_id)).integration_gates[0].region_id, 'inner');
  for (const region_id of ['inner', 'outer']) {
    const request = { ...f.run, region_id }; const proposal = await f.manager.prepareIntegration(f.runtime, f.run.run_id, request);
    await f.manager.integrate(f.runtime, f.run.run_id, { ...request, accepted: true, patch_sha256: proposal.patch_sha256 });
    if (region_id === 'inner') assert.equal(await readFile(join(f.workspace, 'src/a.txt'), 'utf8'), 'Base a\n');
  }
  assert.equal(await readFile(join(f.workspace, 'src/a.txt'), 'utf8'), 'Inner A\n'); assert.equal(await readFile(join(f.workspace, 'src/seed.txt'), 'utf8'), 'Outer sibling\n');
  await f.execute('final'); assert.equal((await f.manager.cleanup(f.runtime, f.run.run_id, f.run)).removed.length, 4);
});

test('an apply that finished before its journal acknowledgement reconciles the exact tree without applying twice', async t => {
  const f = await fixture(t); await f.execute('prelude', 'src/seed.txt', 'Serial context\n');
  await f.execute('a', 'src/a.txt', 'Branch A\n'); await f.execute('b', 'src/b.txt', 'Branch B\n');
  const request = { ...f.run, region_id: 'fork' }; const proposal = await f.manager.prepareIntegration(f.runtime, f.run.run_id, request);
  const original = f.manager.git.apply.bind(f.manager.git); let applied = 0;
  f.manager.git.apply = async (...values) => { await original(...values); applied++; throw Object.assign(new Error('Synthetic crash after apply'), { code: 'INJECTED_CRASH' }); };
  const accepted = { ...request, accepted: true, patch_sha256: proposal.patch_sha256 };
  await assert.rejects(f.manager.integrate(f.runtime, f.run.run_id, accepted), { code: 'INJECTED_CRASH' });
  assert.equal((await f.runtime.get(f.run.run_id)).parallel.fork.phase, 'applying');
  const restarted = await new WorkflowRuntime(f.options).initialize(); await f.manager.integrate(restarted, f.run.run_id, accepted);
  assert.equal(applied, 1); assert.equal((await restarted.get(f.run.run_id)).parallel.fork.integration.reconciled_existing_result, true);
  assert.equal(await readFile(join(f.workspace, 'src/a.txt'), 'utf8'), 'Branch A\n');
});

test('a failed collected branch cannot pass the write integration gate and its unmerged files are retained', async t => {
  const workflow = definition(); workflow.nodes.find(node => node.id === 'fork').failure_policy = 'collect';
  const f = await fixture(t, workflow); await f.execute('prelude', 'src/seed.txt', 'Serial context\n');
  const a = await f.execute('a', 'src/a.txt', 'Branch A\n'); const b = await f.claim('b');
  await f.runtime.failNode(f.run.run_id, { ...b, error: { code: 'SYNTHETIC_FAILURE', message: 'Branch failed' } });
  await assert.rejects(f.manager.prepareIntegration(f.runtime, f.run.run_id, { ...f.run, region_id: 'fork' }), { code: 'PARALLEL_BRANCH_FAILED' });
  await f.runtime.cancelTree(f.run.run_id, f.run);
  await assert.rejects(f.manager.cleanup(f.runtime, f.run.run_id, f.run), { code: 'PARALLEL_UNMERGED_RETAINED' });
  assert.equal(await readFile(join(a.workspace, 'src/a.txt'), 'utf8'), 'Branch A\n');
});
