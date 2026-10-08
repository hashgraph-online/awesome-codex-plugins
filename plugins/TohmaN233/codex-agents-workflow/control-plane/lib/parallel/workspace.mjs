import { join } from 'node:path';
import { nodeBranchChain, branchOwner } from './branch-planner.mjs';
import { loopRoundSignature } from '../workflow-loops.mjs';
import { canonicalJSON, digest } from '../workflow-revisions.mjs';

export function regionBranchOwner(state, pins, regionId, branchId) {
  const signature = loopRoundSignature(state, pins.root.workflow, regionId);
  const runIdentity = Object.keys(signature).length ? state.run_id + ':' + digest(canonicalJSON(signature)) : state.run_id;
  return branchOwner(runIdentity, regionId, branchId);
}

export function nodeWorkspace(nodeId, state, pins) {
  const scope = pins.parallel && nodeBranchChain(pins.parallel, nodeId).at(-1);
  return scope ? join(pins.parallel.worktree_root, 'tree-' + regionBranchOwner(state, pins, scope.region.id, scope.branch.id)) : state.permissions.workspace;
}
