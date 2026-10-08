import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, writeFile, rm } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import { tmpdir } from './physical-tempdir.mjs';
import { validateLoopRegions, initializeLoops, prepareLoops, settleLoops, loopBoundary, loopRoundSignature, observeLoopItems, validateLoopExitOutput, validateLoopItemSources, loopParallelArchives } from '../lib/workflow-loops.mjs';

const yes = { value: true }, eq = (path, value) => ({ op: 'eq', args: [{ path }, { value }] });
const agent = id => ({ id, type: 'agent', access: 'read_only', executor: { kind: 'main', mode: 'worker' } });
const edge = (source, target) => ({ id: `${source}-${target}`, source, target });
function workflow({ items = true, max = 4 } = {}) {
  return { nodes: [{ id: 'start', type: 'start' }, agent('repair'), agent('review'), agent('final')], edges: [edge('start', 'repair'), edge('repair', 'review'), edge('review', 'final')], finalization: { node_id: 'final' }, loops: [{ id: 'repair-loop', entry_node: 'repair', exit_node: 'review', node_ids: ['repair', 'review'], max_rounds: max, until: items ? eq('/loops/repair-loop/all_accepted', true) : eq('/nodes/review/output/passed', true), feedback_bindings: { review: '/nodes/review/output' }, ...(items ? { item_scope: { items: '/inputs/items', verdicts: '/nodes/review/output/verdicts', paths_field: 'files', dependencies_field: 'dependencies' } } : {}) }] };
}
function stateFor(definition, workspace, items = []) {
  const state = { status: 'running', error: null, permissions: { workspace }, inputs: { items }, parallel: {}, nodes: Object.fromEntries(definition.nodes.map(node => [node.id, { status: 'pending', attempts: [], active_attempt_id: null, output: null, error: null, approval_id: null, approval_round: 0 }])), edges: Object.fromEntries(definition.edges.map(edge => [edge.id, 'pending'])) };
  initializeLoops(state, definition); state.nodes.start.status = 'succeeded'; state.edges['start-repair'] = 'selected'; return state;
}
function context(state) { return { inputs: state.inputs, nodes: Object.fromEntries(Object.entries(state.nodes).map(([id, node]) => [id, { output: node.output }])) }; }
async function fixture(t, options = {}) {
  const workspace = await mkdtemp(join(tmpdir(), 'loop-engine-'));
  t.after(() => rm(workspace, { recursive: true, force: true }));
  const items = [1, 2, 3].map(index => ({ name: `item${index}`, files: [index === 1 ? join(workspace, `${index}.txt`) : `${index}.txt`], dependencies: index === 1 ? [] : ['shared.txt'] }));
  for (const path of ['1.txt', '2.txt', '3.txt', 'shared.txt']) await writeFile(join(workspace, path), 'original');
  const definition = workflow(options), state = stateFor(definition, workspace, items); prepareLoops(state, definition, context(state));
  return { workspace, items, definition, state, loop: state.loops['repair-loop'] };
}
async function claimReview(f) {
  const node = f.state.nodes.review;
  node.status = 'claimed'; node.active_attempt_id = `review-${node.attempts.length + 1}`;
  const attempt = { id: node.active_attempt_id, status: 'claimed', loop_rounds: loopRoundSignature(f.state, f.definition, 'review') }; node.attempts.push(attempt);
  attempt.loop_observation = { before: await observeLoopItems(f.state, f.definition, 'review', f.workspace) };
  return attempt;
}
async function completeReview(f, attempt, verdicts) {
  f.state.nodes.repair.status = 'succeeded'; f.state.nodes.repair.output = { repaired: true }; f.state.edges['repair-review'] = 'selected';
  f.state.nodes.review.output = { verdicts }; f.state.nodes.review.status = 'succeeded'; attempt.status = 'succeeded';
  attempt.loop_observation.after = await observeLoopItems(f.state, f.definition, 'review', f.workspace);
  return settleLoops(f.state, f.definition, undefined, context(f.state));
}

test('three-item repair preserves accepted siblings and reviews shared dependants without repairing them', async t => {
  const f = await fixture(t);
  assert.deepEqual(f.loop.repair_items, []); assert.deepEqual(f.loop.review_items, f.items);
  const first = await claimReview(f);
  await completeReview(f, first, [{ accepted: true }, { accepted: true }, { accepted: false, findings: ['Fix behavior'] }]);
  assert.equal(f.loop.round, 2); assert.equal(f.state.edges['review-final'], 'pending');
  assert.deepEqual(f.loop.repair_items, [{ ...f.items[2], findings: ['Fix behavior'] }]);
  const firstSnapshot = structuredClone(f.loop.rounds[0]), priorAttempt = structuredClone(first);
  await writeFile(join(f.workspace, '3.txt'), 'repaired'); await writeFile(join(f.workspace, 'shared.txt'), 'shared repair');
  const second = await claimReview(f);
  assert.deepEqual(f.loop.review_items, f.items.slice(1)); assert.equal(f.loop.repair_items.length, 1);
  await completeReview(f, second, [{ accepted: true }, { accepted: true }]);
  assert.equal(f.loop.status, 'accepted'); assert.equal(f.state.edges['review-final'], 'selected');
  assert.deepEqual(f.loop.rounds[0], firstSnapshot); assert.deepEqual(first, priorAttempt);
  assert.equal(f.state.nodes.review.attempts.length, 2); assert.equal(f.loop.rounds.length, 2);
  assert.equal(settleLoops(f.state, f.definition, undefined, context(f.state)), false);
});

test('empty per-item review sources fail before launch or activation without restricting ordinary review', () => {
  const definition = workflow(), state = stateFor(definition, resolve(tmpdir()));
  const review = definition.nodes.find(node => node.id === 'review');
  review.input_bindings = { items: '/loops/repair-loop/review_items' };
  review.subagent_count = 'auto';
  review.fanout = { input: 'items', distribution: 'one_per_item' };
  assert.throws(() => validateLoopItemSources(state, definition, { allowUnavailable: true }), { code: 'LOOP_ITEM_EMPTY' });
  assert.throws(() => prepareLoops(state, definition), { code: 'LOOP_ITEM_EMPTY' });
  assert.equal(state.loops['repair-loop'].status, 'pending');
  assert.equal(state.loops['repair-loop'].round, 0);
  assert.deepEqual(state.nodes.review.attempts, []);
  // Sources produced later get the same check at their selected entry boundary.
  definition.nodes.unshift({ id: 'source', type: 'tool' });
  state.nodes.source = { status: 'pending', output: null };
  definition.loops[0].item_scope.items = '/nodes/source/output/items';
  assert.equal(validateLoopItemSources(state, definition, { allowUnavailable: true }), true);
  state.nodes.source = { status: 'succeeded', output: { items: [] } };
  assert.throws(() => prepareLoops(state, definition), { code: 'LOOP_ITEM_EMPTY' });
  delete review.fanout;
  assert.equal(validateLoopItemSources(state, definition), true);
  assert.equal(prepareLoops(state, definition), true);
});

test('SkillRef review exits also require independent execution context', () => {
  const definition = workflow();
  const review = definition.nodes.find(node => node.id === 'review');
  review.type = 'skill_ref';
  review.executor = { kind: 'main', mode: 'orchestration' };
  assert.throws(() => validateLoopRegions(definition), { code: 'LOOP_REVIEW_CONTEXT' });
  review.executor.mode = 'worker';
  assert.equal(validateLoopRegions(definition), true);
});

test('changes during review invalidate acceptance and schedule only a fresh review', async t => {
  const f = await fixture(t), attempt = await claimReview(f);
  await writeFile(join(f.workspace, '1.txt'), 'changed during review');
  await completeReview(f, attempt, [{ accepted: true }, { accepted: true }, { accepted: true }]);
  assert.deepEqual(f.loop.review_items, [f.items[0]]); assert.deepEqual(f.loop.repair_items, []);
  assert.equal(f.loop.ledger[0].status, 'invalidated'); assert.equal(f.loop.round, 2);
  await completeReview(f, await claimReview(f), [{ accepted: true }]); assert.equal(f.loop.status, 'accepted');
});

test('missing required files remain unaccepted and receive Host repair findings', async t => {
  const f = await fixture(t); await rm(join(f.workspace, '1.txt')); const attempt = await claimReview(f);
  await completeReview(f, attempt, [{ accepted: true }, { accepted: true }, { accepted: true }]);
  assert.equal(f.loop.ledger[0].status, 'failed'); assert.equal(f.loop.repair_items[0].findings.host.code, 'LOOP_ARTIFACT_MISSING');
  assert.deepEqual(f.loop.repair_items[0].findings.host.paths, ['1.txt']); assert.equal(f.loop.all_accepted, false);
});

test('round exhaustion fails explicitly, preserves history and holds outgoing edges', async t => {
  const f = await fixture(t, { max: 1 });
  await completeReview(f, await claimReview(f), [{ accepted: true }, { accepted: true }, { accepted: false, findings: 'repair' }]);
  assert.equal(f.state.status, 'failed'); assert.equal(f.state.error.code, 'LOOP_EXHAUSTED'); assert.equal(f.loop.status, 'exhausted');
  assert.equal(f.state.edges['review-final'], 'pending'); assert.equal(f.state.nodes.final.status, 'pending'); assert.equal(f.loop.rounds.length, 1);
});

test('malformed verdicts and unavailable observations fail visibly without resetting nodes', async t => {
  const f = await fixture(t), attempt = await claimReview(f);
  for (const verdicts of [[], [{ accepted: true }], [true, true, true], [{ accepted: true, id: 'copied' }, { accepted: true }, { accepted: true }], [{ accepted: 'true' }, { accepted: true }, { accepted: true }]]) assert.throws(() => validateLoopExitOutput(f.state, f.definition, 'review', { verdicts }), { code: 'LOOP_VERDICT_INVALID' });
  validateLoopExitOutput(f.state, f.definition, 'review', { verdicts: [{ accepted: true }, { accepted: true }, { accepted: true }] });
  f.state.nodes.review.status = 'succeeded'; f.state.nodes.repair.status = 'succeeded'; f.state.nodes.review.output = { verdicts: [{ accepted: true }, { accepted: true }, { accepted: true }] };
  assert.throws(() => settleLoops(f.state, f.definition), { code: 'LOOP_OBSERVATION_MISSING' }); assert.equal(f.loop.round, 1); assert.equal(attempt.status, 'claimed');
});

test('restoration is idempotent and retains original items and immutable prior outputs', async t => {
  const f = await fixture(t); await completeReview(f, await claimReview(f), [{ accepted: true }, { accepted: true }, { accepted: false, findings: 'repair' }]);
  const restored = structuredClone(f.state), prior = structuredClone(restored); initializeLoops(restored, f.definition);
  assert.equal(prepareLoops(restored, f.definition), false); assert.equal(settleLoops(restored, f.definition), false); assert.deepEqual(restored, prior);
  assert.deepEqual(restored.loops['repair-loop'].items, f.items); assert.deepEqual(restored.loops['repair-loop'].rounds[0].nodes.review.output.verdicts[2], { accepted: false, findings: 'repair' });
});

test('absolute and relative source paths map to the actual physical branch workspace', async t => {
  const f = await fixture(t), branch = join(f.workspace, 'branch'); await mkdir(branch);
  for (const path of ['1.txt', '2.txt', '3.txt', 'shared.txt']) await writeFile(join(branch, path), 'branch content');
  const observation = await observeLoopItems(f.state, f.definition, 'review', branch);
  assert.equal(observation['repair-loop'].items.every(item => !item.missing), true);
  assert.deepEqual(observation['repair-loop'].items[0].files.map(file => file.path), ['1.txt']);
  f.state.inputs.items[0].files = ['../escape.txt']; assert.throws(() => validateLoopItemSources(f.state, f.definition), { code: 'LOOP_ITEM_PATH' });
  f.state.inputs.items[0].files = [resolve(f.workspace, '..', 'escape.txt')]; assert.throws(() => validateLoopItemSources(f.state, f.definition), { code: 'LOOP_ITEM_PATH' });
});

test('filesystem errors and unsafe source shapes are never treated as missing files', async t => {
  const f = await fixture(t); await rm(join(f.workspace, '1.txt')); await mkdir(join(f.workspace, '1.txt'));
  await assert.rejects(observeLoopItems(f.state, f.definition, 'review', f.workspace), { code: 'LOOP_ITEM_FILE' });
  f.state.inputs.items[0].files = []; assert.throws(() => validateLoopItemSources(f.state, f.definition), { code: 'LOOP_ITEM_INVALID' });
  f.state.inputs.items[0].files = ['2.txt']; f.state.inputs.items[0].dependencies = 'shared.txt'; assert.throws(() => validateLoopItemSources(f.state, f.definition), { code: 'LOOP_ITEM_INVALID' });
  // Windows may report ENOENT beneath a regular file, so verify each ancestor.
  f.loop.items[0].files = ['2.txt/child']; await assert.rejects(observeLoopItems(f.state, f.definition, 'review', f.workspace), { code: 'LOOP_ITEM_FILE' });
});

test('unavailable upstream item binding is deferred until its source completes', () => {
  const definition = workflow(); definition.loops[0].item_scope.items = '/nodes/start/output/items';
  const state = stateFor(definition, tmpdir()); state.nodes.start.status = 'pending';
  assert.equal(validateLoopItemSources(state, definition, { allowUnavailable: true }), true);
  state.nodes.start.status = 'succeeded'; assert.throws(() => validateLoopItemSources(state, definition, { allowUnavailable: true }), { code: 'BINDING_MISSING' });
});

test('inactive branches never resolve missing bindings or hold skipped successors', () => {
  const definition = workflow(); const state = stateFor(definition, tmpdir()); state.inputs = {}; state.edges['start-repair'] = 'skipped';
  assert.equal(prepareLoops(state, definition), false);
  state.nodes.repair.status = 'skipped'; state.nodes.review.status = 'skipped';
  assert.equal(settleLoops(state, definition), true); assert.equal(state.loops['repair-loop'].status, 'skipped'); assert.equal(state.edges['review-final'], 'skipped');
});

test('generic feedback loops reset only the owned region and retain attempts', () => {
  const definition = workflow({ items: false }), state = stateFor(definition, tmpdir()); prepareLoops(state, definition);
  state.nodes.repair.status = state.nodes.review.status = 'succeeded'; state.nodes.review.output = { passed: false, findings: 'Try again' }; state.nodes.review.attempts.push({ id: 'first', status: 'succeeded' }); state.nodes.review.active_attempt_id = 'first';
  assert.equal(settleLoops(state, definition), true); assert.equal(state.loops['repair-loop'].round, 2); assert.deepEqual(state.loops['repair-loop'].feedback.review, { passed: false, findings: 'Try again' });
  assert.equal(state.nodes.start.status, 'succeeded'); assert.equal(state.nodes.review.active_attempt_id, null); assert.equal(state.nodes.review.output, null); assert.equal(state.nodes.review.attempts.length, 1);
  state.nodes.repair.status = state.nodes.review.status = 'succeeded'; state.nodes.review.output = { passed: true }; settleLoops(state, definition); assert.equal(state.edges['review-final'], 'selected');
});

test('nested rounds keep inner histories with lineage and disjoint loops retain independent state', () => {
  const nodes = ['start', 'outer-entry', 'inner-entry', 'inner-exit', 'outer-exit', 'side-entry', 'side-exit', 'final'].map(agent);
  const definition = { nodes, edges: [edge('start', 'outer-entry'), edge('outer-entry', 'inner-entry'), edge('inner-entry', 'inner-exit'), edge('inner-exit', 'outer-exit'), edge('outer-exit', 'final'), edge('start', 'side-entry'), edge('side-entry', 'side-exit'), edge('side-exit', 'final')], finalization: { node_id: 'final' }, loops: [
    { id: 'outer', entry_node: 'outer-entry', exit_node: 'outer-exit', node_ids: ['outer-entry', 'inner-entry', 'inner-exit', 'outer-exit'], max_rounds: 2, until: eq('/nodes/outer-exit/output/passed', true) },
    { id: 'inner', entry_node: 'inner-entry', exit_node: 'inner-exit', node_ids: ['inner-entry', 'inner-exit'], max_rounds: 2, until: yes },
    { id: 'side', entry_node: 'side-entry', exit_node: 'side-exit', node_ids: ['side-entry', 'side-exit'], max_rounds: 2, until: yes },
  ] };
  assert.equal(validateLoopRegions(definition), true); const state = stateFor(definition, tmpdir()); state.edges['start-outer-entry'] = state.edges['start-side-entry'] = 'selected'; prepareLoops(state, definition);
  assert.equal(state.loops.inner.round, 0); state.nodes['outer-entry'].status = 'succeeded'; state.edges['outer-entry-inner-entry'] = 'selected'; prepareLoops(state, definition);
  assert.deepEqual(state.loops.inner.lineage, [{ id: 'outer', round: 1 }]);
  state.nodes['inner-entry'].status = state.nodes['inner-exit'].status = 'succeeded'; state.nodes['inner-exit'].output = {}; settleLoops(state, definition);
  state.nodes['outer-exit'].status = 'succeeded'; state.nodes['outer-exit'].output = { passed: false }; settleLoops(state, definition);
  assert.equal(state.loops.inner.round, 0); assert.equal(state.loops.inner.rounds.length, 1); assert.equal(state.loops.side.round, 1);
  state.nodes['outer-entry'].status = 'succeeded'; state.edges['outer-entry-inner-entry'] = 'selected'; prepareLoops(state, definition);
  assert.deepEqual(state.loops.inner.lineage, [{ id: 'outer', round: 2 }]);
  state.nodes['inner-entry'].status = state.nodes['inner-exit'].status = 'succeeded'; state.nodes['inner-exit'].output = {}; settleLoops(state, definition);
  assert.equal(state.loops.inner.rounds.length, 2); assert.equal(state.loops.inner.rounds[0].lineage[0].round, 1); assert.equal(state.loops.inner.rounds[1].lineage[0].round, 2);
  assert.deepEqual(loopBoundary(definition, 'inner-exit').map(loop => loop.id), ['inner', 'outer']);
});

test('parallel ownership is archived before reset and unresolved merge prevents reset', () => {
  const definition = workflow({ items: false }); definition.nodes.splice(1, 0, { id: 'fork', type: 'parallel', join_id: 'join' }, { id: 'join', type: 'join', parallel_id: 'fork' });
  definition.loops[0].node_ids.push('fork', 'join'); const state = stateFor(definition, tmpdir()); prepareLoops(state, definition);
  for (const id of definition.loops[0].node_ids) state.nodes[id].status = 'succeeded'; state.nodes.review.output = { passed: false };
  state.parallel.fork = { phase: 'running', branches: [{ owner: 'first-round' }] };
  assert.throws(() => settleLoops(state, definition), { code: 'LOOP_PARALLEL_UNMERGED' }); assert.equal(state.parallel.fork.branches[0].owner, 'first-round');
  state.parallel.fork.phase = 'merged'; state.loops['repair-loop'].status = 'running'; settleLoops(state, definition);
  assert.equal(state.parallel.fork, undefined); assert.equal(state.loops['repair-loop'].rounds[0].parallel.fork.branches[0].owner, 'first-round');
  assert.deepEqual(loopParallelArchives(state)[0].path, ['loops', 'repair-loop', 'rounds', 0, 'parallel']);
});

test('region validation rejects malformed structure, overlapping ownership and unsafe review boundaries', () => {
  assert.equal(validateLoopRegions(workflow()), true);
  for (const mutate of [d => { d.loops = {}; }, d => { d.loops[0].max_rounds = 0; }, d => { d.loops[0].node_ids.push('unknown'); }, d => { d.loops[0].entry_node = 'start'; }, d => { d.loops[0].node_ids.push('final'); }, d => { d.nodes[2].access = 'bounded_write'; }, d => { d.nodes[2].executor.mode = 'orchestration'; }, d => { d.nodes[2].completion_contract = { fail_on_false: ['passed'] }; }, d => { d.edges.push(edge('start', 'review')); }, d => { d.edges.push(edge('repair', 'final')); }, d => { d.loops.push({ ...d.loops[0], id: 'same-region' }); }, d => { d.loops[0].until = { op: 'unsupported', args: [] }; }, d => { d.loops[0].item_scope.items = '/nodes/unknown/output/items'; }]) { const definition = workflow(); mutate(definition); assert.throws(() => validateLoopRegions(definition)); }
});

test('loop pointers expose only public fields and first review does not require skipped repair output', () => {
  for (const pointer of ['/run/status', '/loops/repair-loop/ledger', '/nodes/review/attempts', '/loops/unknown/round', '']) {
    const definition = workflow(); definition.loops[0].until = eq(pointer, true); assert.throws(() => validateLoopRegions(definition), { code: 'LOOP_BINDING_INVALID' });
  }
  const definition = workflow(); definition.nodes[1].input_bindings = { items: '/loops/repair-loop/repair_items' }; definition.nodes[2].input_bindings = { repaired: '/nodes/repair/output/repaired' };
  assert.throws(() => validateLoopRegions(definition), { code: 'LOOP_INITIAL_REVIEW_INPUT' });
  definition.nodes[2].input_bindings.repaired = { path: '/nodes/repair/output/repaired', default: [] }; assert.equal(validateLoopRegions(definition), true);
  definition.nodes[2].input_bindings.repaired = { coalesce: ['/nodes/repair/output/repaired', '/inputs/items'] }; assert.equal(validateLoopRegions(definition), true);
});

test('current review findings replace prior source findings only in the repair projection', async t => {
  const f = await fixture(t); f.items[2].findings = 'prior source findings'; f.loop.items[2].findings = 'prior source findings';
  await completeReview(f, await claimReview(f), [{ accepted: true }, { accepted: true }, { accepted: false, findings: 'current review findings' }]);
  assert.equal(f.loop.repair_items[0].findings, 'current review findings');
  assert.equal(f.loop.items[2].findings, 'prior source findings'); assert.equal(f.loop.rounds[0].items[2].findings, 'prior source findings');
});

test('conditional loop exit retains the selected outside branch',()=>{
  const definition={nodes:[{id:'start',type:'start'},agent('repair'),{id:'choice',type:'condition'},agent('yes'),agent('no'),agent('final')],edges:[edge('start','repair'),edge('repair','choice'),{...edge('choice','yes'),label:'yes'},{...edge('choice','no'),label:'no'},edge('yes','final'),edge('no','final')],finalization:{node_id:'final'},loops:[{id:'loop',entry_node:'repair',exit_node:'choice',node_ids:['repair','choice'],max_rounds:3,until:yes}]};
  validateLoopRegions(definition);const state=stateFor(definition,resolve(tmpdir()));prepareLoops(state,definition);
  state.nodes.repair.status='succeeded';state.nodes.choice.status='succeeded';state.nodes.choice.output={selected_label:'yes'};
  settleLoops(state,definition);assert.equal(state.edges['choice-yes'],'selected');assert.equal(state.edges['choice-no'],'skipped');
});

test('future control sources and reset-body item sources reject before execution',()=>{
  for(const field of ['until','feedback_bindings']){
    const definition=workflow({items:false});definition.loops[0][field]=field==='until'?eq('/nodes/final/output/passed',true):{late:'/nodes/final/output'};
    assert.throws(()=>validateLoopRegions(definition),{code:'LOOP_BINDING_UNAVAILABLE'});
  }
  const definition=workflow();definition.loops[0].item_scope.items='/nodes/repair/output/items';
  assert.throws(()=>validateLoopRegions(definition),{code:'LOOP_BINDING_UNAVAILABLE'});
  definition.loops[0].item_scope.items='/inputs/items';definition.loops[0].item_scope.verdicts='/inputs/old_verdicts';
  assert.throws(()=>validateLoopRegions(definition),{code:'LOOP_BINDING_UNAVAILABLE'});
});

test('accepted sibling disappearing during targeted review becomes immediate repair work',async t=>{
  const f=await fixture(t,{max:3});await completeReview(f,await claimReview(f),[{accepted:true},{accepted:true},{accepted:false,findings:'Fix item3'}]);
  const second=await claimReview(f);await rm(join(f.workspace,'1.txt'));
  await completeReview(f,second,[{accepted:true}]);
  assert.equal(f.loop.round,3);assert.deepEqual(f.loop.repair_items.map(item=>item.name),['item1']);
  assert.equal(f.loop.repair_items[0].findings.host.code,'LOOP_ARTIFACT_MISSING');
  await writeFile(join(f.workspace,'1.txt'),'restored');await completeReview(f,await claimReview(f),[{accepted:true}]);
  assert.equal(f.loop.status,'accepted');
});
