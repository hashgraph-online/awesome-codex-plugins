import test from 'node:test';
import assert from 'node:assert/strict';
import { planParallelBranches, nodeBranchChain, branchOwner } from '../lib/parallel/branch-planner.mjs';
import { ParallelWorktreeManager } from '../lib/parallel/worktree-manager.mjs';
import { resolve } from 'node:path';

const worker = (id, paths = []) => ({ id, type: 'agent', access: paths.length ? 'bounded_write' : 'read_only', path_scope: paths });
const edges = pairs => pairs.map(([source, target], index) => ({ id: 'e' + index, source, target, label: target }));
const state = { permissions: { access: 'bounded_write', allowed_paths: ['src', 'docs'] } };

test('parallel planner keeps sequential branch context and reports overlap behind an isolated integration gate', () => {
  const workflow = { nodes: [{ id: 'fork', type: 'parallel', join_id: 'join' }, worker('a', ['src']), worker('a-review'), worker('b', ['src/part']), { id: 'join', type: 'join', parallel_id: 'fork' }],
    edges: edges([['fork', 'a'], ['a', 'a-review'], ['a-review', 'join'], ['fork', 'b'], ['b', 'join']]) };
  const plan = planParallelBranches(workflow, state); const region = plan.regions[0];
  assert.equal(region.isolated, true); assert.deepEqual(region.overlaps[0].paths, ['src/part']);
  assert.equal(nodeBranchChain(plan, 'a-review')[0].branch.id, nodeBranchChain(plan, 'a')[0].branch.id);
  assert.notEqual(nodeBranchChain(plan, 'a')[0].branch.id, nodeBranchChain(plan, 'b')[0].branch.id);
  assert.deepEqual(nodeBranchChain(plan, 'join'), []);
});

test('nested write forks derive an outer-to-inner workspace chain while their Join returns to the enclosing branch', () => {
  const workflow = { nodes: [{ id: 'outer', type: 'parallel', join_id: 'outer-join' }, { id: 'inner', type: 'parallel', join_id: 'inner-join' }, worker('a', ['src/a']), worker('b', ['src/b']),
    worker('c', ['docs']), { id: 'inner-join', type: 'join', parallel_id: 'inner' }, { id: 'outer-join', type: 'join', parallel_id: 'outer' }],
    edges: edges([['outer', 'inner'], ['outer', 'c'], ['inner', 'a'], ['inner', 'b'], ['a', 'inner-join'], ['b', 'inner-join'], ['inner-join', 'outer-join'], ['c', 'outer-join']]) };
  const plan = planParallelBranches(workflow, state);
  assert.deepEqual(nodeBranchChain(plan, 'a').map(item => item.region.id), ['outer', 'inner']);
  assert.deepEqual(nodeBranchChain(plan, 'inner-join').map(item => item.region.id), ['outer']);
  assert.equal(plan.regions.find(region => region.id === 'inner').parent_region_id, 'outer');
  assert(branchOwner('run', 'outer', 'branch').length <= 64);
  assert.notEqual(branchOwner('run', 'outer', 'branch'), branchOwner('run', 'inner', 'branch'));
});

test('cooperative handoffs cannot qualify parallel writes merely by requesting a worktree', async () => {
  const workflow = { skill_policy: { mode: 'cooperative', implicit: 'allow', ambient_allow: [], shadowed_skill_paths: [] },
    nodes: [{ id: 'fork', type: 'parallel', join_id: 'join' }, worker('a', ['src']), worker('b', ['docs']), { id: 'join', type: 'join', parallel_id: 'fork' }],
    edges: edges([['fork', 'a'], ['fork', 'b'], ['a', 'join'], ['b', 'join']]) };
  await assert.rejects(new ParallelWorktreeManager(resolve('unused-no-files-created')).preflight(workflow, state.permissions, [{ pack: { workflow }, state }]), { code: 'PARALLEL_EXECUTOR_UNQUALIFIED' });
});
