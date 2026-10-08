import { graphInfo, EXECUTOR_NODES } from '../workflow-state.mjs';
import { nodePermissions } from '../workflow-execution-envelope.mjs';
import { intersectBoundaries, pathBoundaries } from '../workflow-bindings.mjs';
import { digest } from '../workflow-revisions.mjs';
import { requireValue } from '../workflow-paths.mjs';

// A branch workspace belongs to a graph region, not an individual worker. This
// lets sequential nodes share their own branch results while sibling branches
// remain isolated. Nested regions fork from their enclosing branch at entry.
export function planParallelBranches(workflow, state) {
  const graph = graphInfo(workflow);
  const regions = graph.regions.map(region => {
    const branches = graph.out.get(region.parallel.id).map(edge => {
      const members = graph.visit(edge.target, region.parallel.join_id);
      const scopes = [...members].filter(id => EXECUTOR_NODES.has(graph.nodes.get(id).type)).map(id => ({ node_id: id, ...nodePermissions(graph.nodes.get(id), state) }));
      return { id: edge.id, label: edge.label, entry_node_id: edge.target, node_ids: [...members].sort(),
        write_paths: pathBoundaries(scopes.filter(scope => scope.access === 'bounded_write').flatMap(scope => scope.allowed_paths)) };
    });
    const writePaths = pathBoundaries(branches.flatMap(branch => branch.write_paths));
    const overlaps = [];
    for (let left = 0; left < branches.length; left++) for (let right = left + 1; right < branches.length; right++) {
      const paths = intersectBoundaries(branches[left].write_paths, branches[right].write_paths);
      if (paths.length) overlaps.push({ left_branch: branches[left].id, right_branch: branches[right].id, paths });
    }
    return { id: region.parallel.id, join_id: region.parallel.join_id, node_ids: [...region.members].sort(), branches,
      write_paths: writePaths, isolated: writePaths.length > 0, overlaps };
  });
  requireValue(regions.filter(region => region.isolated).reduce((count, region) => count + region.branches.length, 0) <= 64, 'PARALLEL_BRANCH_LIMIT', 'Run contains too many isolated branch workspaces');
  for (const region of regions) {
    const parent = regions.filter(candidate => candidate.id !== region.id && candidate.node_ids.includes(region.id)).sort((a, b) => a.node_ids.length - b.node_ids.length)[0];
    region.parent_region_id = parent?.id ?? null;
    region.parent_branch_id = parent?.branches.find(branch => branch.node_ids.includes(region.id))?.id ?? null;
    if (region.isolated) requireValue(region.branches.every(branch => branch.node_ids.length > 0), 'PARALLEL_BRANCH_EMPTY', 'An isolated branch cannot be empty');
  }
  return { schema_version: 1, regions };
}

export function nodeBranchChain(plan, nodeId) {
  return plan.regions.filter(region => region.isolated && region.node_ids.includes(nodeId))
    .sort((a, b) => b.node_ids.length - a.node_ids.length)
    .map(region => ({ region, branch: region.branches.find(branch => branch.node_ids.includes(nodeId)) }));
}

export function branchOwner(runId, regionId, branchId) {
  return 'parallel-' + digest([runId, regionId, branchId].join('\0')).slice(0, 55);
}
