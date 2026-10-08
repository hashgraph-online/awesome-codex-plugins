import { dirname, join, resolve } from 'node:path';
import { readFile } from 'node:fs/promises';
import { GitWorktrees } from './git-worktrees.mjs';
import { planParallelBranches, nodeBranchChain } from './branch-planner.mjs';
import { nodeWorkspace, regionBranchOwner } from './workspace.mjs';
import { digest, canonicalJSON } from '../workflow-revisions.mjs';
import { requireValue } from '../workflow-paths.mjs';
import { advanceRun } from '../workflow-state.mjs';
import { nodePermissions } from '../workflow-execution-envelope.mjs';
import { loopParallelArchives } from '../workflow-loops.mjs';

const managers = new Map();
const samePath = (a, b) => process.platform === 'win32' ? resolve(a).toLowerCase() === resolve(b).toLowerCase() : resolve(a) === resolve(b);
const metadata = ({ patch, ...item }) => item;
const artifactLabel = regionId => 'parallel-' + digest(regionId).slice(0, 40);
const touch = state => { state.updated_at = new Date().toISOString(); };
function active(state, { gate = false } = {}) {
  requireValue(state.status === 'running' || gate && state.status === 'blocked', 'RUN_NOT_RUNNING', 'Run cannot prepare or integrate parallel work in its current state');
}

export class ParallelWorktreeManager {
  constructor(root, options) { this.git = new GitWorktrees(root, options); this.root = this.git.root; }
  async withDiagnostic(runtime, runId, args, operation, action) {
    await runtime.authorizeController(runId, args);
    try { return await action(); }
    catch (error) {
      const diagnostic = { operation, region_id: typeof args.region_id === 'string' ? args.region_id.slice(0, 64) : null, code: error.code ?? 'PARALLEL_OPERATION_FAILED', message: String(error.message).slice(0, 2000),
        ...(error.outside_paths ? { outside_paths: error.outside_paths.slice(0, 512) } : {}) };
      try {
        await runtime.runs.mutate(runId, 'parallel_error', state => {
          if (diagnostic.region_id && state.parallel?.[diagnostic.region_id]) state.parallel[diagnostic.region_id].error = diagnostic;
          state.parallel_errors = [...(state.parallel_errors ?? []), diagnostic].slice(-64); touch(state);
        });
      } catch (auditError) { throw Object.assign(new AggregateError([error, auditError], 'Parallel operation failed and its diagnostic could not be committed'), { code: 'PARALLEL_AUDIT_FAILED' }); }
      throw error;
    }
  }
  async preflight(workflow, permissions, contexts) {
    const plan = planParallelBranches(workflow, { permissions });
    let isolated = false;
    for (const scope of contexts) {
      const nested = planParallelBranches(scope.pack.workflow, scope.state); const regions = nested.regions.filter(region => region.isolated); isolated ||= regions.length > 0;
      for (const node of scope.pack.workflow.nodes) if (node.type !== 'subworkflow' && regions.some(region => region.node_ids.includes(node.id)) && ['agent', 'skill_ref', 'tool'].includes(node.type) && nodePermissions(node, scope.state).access === 'bounded_write') {
        requireValue(scope.pack.workflow.skill_policy.mode === 'strict', 'PARALLEL_EXECUTOR_UNQUALIFIED', 'Parallel writes require the qualified Strict broker; a cooperative handoff cannot enforce its worktree assignment');
      }
    }
    if (!isolated) return null;
    await this.git.initialize();
    return { ...plan, worktree_root: this.root, repository: await this.git.inspect(permissions.workspace) };
  }
  async sourceIdentity(workspace, plan) {
    const actual = await this.git.inspect(workspace, { clean: false });
    requireValue(samePath(actual.common_directory, plan.repository.common_directory), 'PARALLEL_REPOSITORY_CHANGED', 'Parallel source moved to another repository');
    if (samePath(workspace, plan.repository.workspace)) requireValue(actual.base_commit === plan.repository.base_commit, 'PARALLEL_BASE_CHANGED', 'Source HEAD changed since Run creation');
    else {
      const relative = resolve(workspace).slice(this.root.length + 1);
      requireValue(samePath(join(this.root, relative), workspace) && /^tree-parallel-[a-f0-9]+$/.test(relative), 'PARALLEL_SOURCE_UNOWNED', 'Nested forks require an exact owned parent workspace');
      const owner = JSON.parse(await readFile(this.git.manifest(relative.slice(5)), 'utf8')); await this.git.verify(owner);
      requireValue(samePath(owner.workspace, workspace), 'PARALLEL_SOURCE_UNOWNED', 'Nested workspace owner differs from its path');
    }
    return actual;
  }
  previousPaths(state, pins, workspace) {
    const executions = Object.entries(state.nodes).filter(([id]) => samePath(nodeWorkspace(id, state, pins), workspace))
      .flatMap(([, node]) => node.attempts.flatMap(attempt => attempt.completion?.changed_paths ?? []));
    const integrations = [state.parallel ?? {}, ...loopParallelArchives(state).map(item=>item.parallel)].flatMap(records=>Object.values(records)).filter(record => record.phase === 'merged' && samePath(record.base.workspace, workspace)).flatMap(record => record.proposal.changed_paths);
    return [...new Set([...executions, ...integrations])];
  }
  async ensureNode(runtime, runId, args) {
    await runtime.execution(runId, args);
    const { pins } = await runtime.runs.read(runId);
    if (!pins.parallel) return;
    await this.git.initialize();
    for (const { region } of nodeBranchChain(pins.parallel, args.node_id)) await this.withDiagnostic(runtime, runId, { ...args, region_id: region.id }, 'provision', () => this.ensureRegion(runtime, runId, args, region.id));
  }
  async ensureRegion(runtime, runId, args, regionId, { gate = false } = {}) {
    await runtime.authorizeController(runId, args);
    await runtime.transition(runId, 'parallel_intent', (state, pins) => {
      active(state, { gate }); const region = pins.parallel?.regions.find(item => item.id === regionId && item.isolated);
      requireValue(region && state.nodes[region.id].status === 'succeeded', 'PARALLEL_REGION_NOT_ACTIVE', 'Parallel region has not been reached');
      state.parallel ??= {};
      if (!state.parallel[regionId]) { state.parallel[regionId] = { phase: 'intent', base: null, branches: {}, proposal: null }; touch(state); }
    });
    await runtime.transition(runId, 'parallel_base', async (state, pins) => {
      active(state, { gate }); const record = state.parallel[regionId]; if (record.base) return;
      const region = pins.parallel.regions.find(item => item.id === regionId); const workspace = nodeWorkspace(region.id, state, pins);
      const actual = await this.sourceIdentity(workspace, pins.parallel);
      const snapshot = await this.git.snapshot(workspace, actual.base_commit, state.permissions.allowed_paths, { includeIgnored: false, extraPaths: this.previousPaths(state, pins, workspace) });
      record.base = { workspace, common_directory: actual.common_directory, base_commit: snapshot.commit, source_head: actual.base_commit, source_tree: snapshot.tree, existing_paths: snapshot.changed_paths };
      record.phase = 'provisioning'; touch(state);
    });
    const { pins } = await runtime.runs.read(runId); const region = pins.parallel.regions.find(item => item.id === regionId);
    for (const branch of region.branches) await runtime.transition(runId, 'parallel_branch', async (state, currentPins) => {
      active(state, { gate }); const record = state.parallel[regionId];
      if (record.branches[branch.id]) { await this.git.verify(record.branches[branch.id]); return; }
      record.branches[branch.id] = await this.git.create(record.base, regionBranchOwner(state, currentPins, regionId, branch.id)); touch(state);
    });
    await runtime.transition(runId, 'parallel_ready', state => {
      active(state, { gate }); const record = state.parallel[regionId];
      if (record.phase === 'provisioning') { record.phase = 'active'; touch(state); }
    });
  }
  async prepareIntegration(runtime, runId, args) {
    return this.withDiagnostic(runtime, runId, args, 'prepare_integration', () => this.prepareProposal(runtime, runId, args));
  }
  async prepareProposal(runtime, runId, args) {
    await runtime.authorizeController(runId, args);
    const { pins, state } = await runtime.runs.read(runId); const region = pins.parallel?.regions.find(item => item.id === args.region_id && item.isolated);
    requireValue(region && state.nodes[region.join_id].status === 'blocked', 'PARALLEL_GATE_NOT_READY', 'Join has not reached its integration gate');
    await this.ensureRegion(runtime, runId, args, region.id, { gate: true });
    const result = await runtime.transition(runId, 'parallel_proposal', async (current, _currentPins) => {
      active(current, { gate: true }); const record = current.parallel[region.id];
      requireValue(region.node_ids.every(id => ['succeeded', 'skipped'].includes(current.nodes[id].status)), 'PARALLEL_BRANCH_FAILED', 'A failed or unfinished branch cannot enter successful integration');
      if (record.proposal) { await runtime.runs.readArtifact(runId, record.proposal.artifact); return record.proposal; }
      const snapshots = [];
      for (const branch of region.branches) {
        const owned = record.branches[branch.id]; await this.git.verify(owned);
        snapshots.push({ branch_id: branch.id, ...await this.git.snapshot(owned.workspace, record.base.base_commit, branch.write_paths) });
      }
      const merged = await this.git.merge(record.base.workspace, record.base.base_commit, snapshots);
      const artifact = await runtime.runs.saveArtifact(runId, artifactLabel(region.id), merged.patch);
      record.proposal = { ...metadata(merged), artifact, branches: snapshots.map(metadata), changed_paths: [...new Set(snapshots.flatMap(item => item.changed_paths))].sort() };
      record.phase = 'review_required'; record.error = null; touch(current); return record.proposal;
    });
    return { region_id: region.id, review_required: true, ...result.result };
  }
  async review(runtime, runId, args) {
    await runtime.authorizeController(runId, args); const { state } = await runtime.runs.read(runId);
    const proposal = state.parallel?.[args.region_id]?.proposal; requireValue(proposal, 'PARALLEL_PROPOSAL_MISSING', 'Prepare an exact integration proposal first');
    const patch = await runtime.runs.readArtifact(runId, proposal.artifact);
    return { region_id: args.region_id, ...proposal, patch: patch.toString('utf8') };
  }
  async integrate(runtime, runId, args) {
    return this.withDiagnostic(runtime, runId, args, 'integrate', () => this.applyProposal(runtime, runId, args));
  }
  async applyProposal(runtime, runId, args) {
    await runtime.authorizeController(runId, args);
    requireValue(args.accepted === true && /^[a-f0-9]{64}$/.test(args.patch_sha256), 'PARALLEL_REVIEW_REQUIRED', 'Integration requires explicit main-controller acceptance of the exact patch hash');
    await runtime.transition(runId, 'parallel_apply_intent', (state, pins) => {
      active(state, { gate: true }); const record = state.parallel?.[args.region_id]; const region = pins.parallel?.regions.find(item => item.id === args.region_id);
      requireValue(record?.proposal?.patch_sha256 === args.patch_sha256 && region, 'PARALLEL_PROPOSAL_CHANGED', 'Reviewed integration proposal is absent or changed');
      if (record.phase === 'merged') return;
      requireValue(['review_required', 'applying'].includes(record.phase) && state.nodes[region.join_id].status === 'blocked', 'PARALLEL_GATE_NOT_READY', 'Integration gate is not waiting for this proposal');
      if (record.phase !== 'applying') { record.phase = 'applying'; record.accepted_by = state.main_actor; touch(state); }
    });
    const result = await runtime.transition(runId, 'parallel_integrated', async (state, pins) => {
      active(state, { gate: true }); const record = state.parallel[args.region_id]; if (record.phase === 'merged') return record.proposal;
      const region = pins.parallel.regions.find(item => item.id === args.region_id); const proposal = record.proposal;
      const workspace = record.base.workspace; const actual = await this.sourceIdentity(workspace, pins.parallel);
      requireValue(actual.base_commit === record.base.source_head, 'PARALLEL_BASE_CHANGED', 'Integration target HEAD changed');
      const paths = [...new Set([...record.base.existing_paths, ...proposal.changed_paths])];
      const current = await this.git.snapshot(workspace, actual.base_commit, state.permissions.allowed_paths, { includeIgnored: false, extraPaths: paths });
      requireValue([record.base.source_tree, proposal.tree].includes(current.tree), 'PARALLEL_SOURCE_CHANGED', 'Integration target differs from both the recorded base and accepted result; inspect partial or concurrent changes');
      const patch = await runtime.runs.readArtifact(runId, proposal.artifact);
      if (current.tree !== proposal.tree) await this.git.apply(workspace, patch, proposal.patch_sha256, () => runtime.assertAncestors(pins));
      const after = await this.git.snapshot(workspace, actual.base_commit, state.permissions.allowed_paths, { includeIgnored: false, extraPaths: paths });
      requireValue(after.tree === proposal.tree, 'PARALLEL_APPLY_UNCERTAIN', 'Integration side effect differs from the accepted tree; preserve files for inspection');
      record.phase = 'merged'; record.error = null; record.integration = { tree: after.tree, patch_sha256: proposal.patch_sha256, reconciled_existing_result: current.tree === proposal.tree };
      state.nodes[region.join_id].status = 'pending'; state.status = 'running'; advanceRun(state, pins); touch(state);
      return record.proposal;
    });
    return { region_id: args.region_id, integrated: true, proposal: result.result, state: await runtime.get(runId) };
  }
  async cleanup(runtime, runId, args) {
    return this.withDiagnostic(runtime, runId, args, 'cleanup', async () => {
      const record = await runtime.runs.read(runId);
      requireValue(['succeeded', 'failed', 'cancelled'].includes(record.state.status), 'PARALLEL_CLEANUP_ACTIVE', 'Active Runs retain their worktrees');
      const regions = (record.pins.parallel?.regions ?? []).filter(region => region.isolated).sort((a, b) => a.node_ids.length - b.node_ids.length);
      const removed = [];
      const maps=[{path:['parallel'],parallel:record.state.parallel??{}},...loopParallelArchives(record.state)];
      const at=(state,path)=>path.reduce((value,key)=>value[key],state);
      for (const region of regions) {
        const scopes=maps.filter(item=>item.parallel[region.id]).map(item=>({path:[...item.path,region.id],scope:item.parallel[region.id]}));
        for(const {scope} of scopes)requireValue(scope.phase === 'merged', 'PARALLEL_UNMERGED_RETAINED', 'Unaccepted branch changes remain available for inspection', { region_id: region.id });
        for (const branch of region.branches) {
          const groups=new Map();
          for(const reference of scopes){const ownership=reference.scope.branches[branch.id];requireValue(ownership,'PARALLEL_OWNER_MISSING','Archived branch ownership is missing');
            const group=groups.get(ownership.owner)??[];group.push(reference);groups.set(ownership.owner,group);}
          for(const references of groups.values()){
          const state=references[0].scope,ownership=state.branches[branch.id],ownerHash=digest(canonicalJSON(ownership));
          const tree=state.proposal.branches.find(item=>item.branch_id===branch.id)?.tree;
          requireValue(tree&&references.every(({scope})=>digest(canonicalJSON(scope.branches[branch.id]))===ownerHash&&scope.proposal.branches.find(item=>item.branch_id===branch.id)?.tree===tree),'PARALLEL_OWNER_CONFLICT','Archived ownership or accepted tree differs across loop histories');
          await runtime.runs.mutate(runId, 'parallel_cleanup', async current => {
            const targets=references.map(item=>at(current,item.path));
            for(const scope of targets){scope.cleaned_branches??=[];scope.cleanup_intents??={};}
            if(targets.every(scope=>scope.cleaned_branches.includes(branch.id)||scope.cleanup_intents[branch.id]))return;
            requireValue(region.node_ids.every(id => current.nodes[id].attempts.every(attempt => !attempt.dispatch?.cancellation_pending && !['claimed', 'running'].includes(attempt.status))), 'PARALLEL_CLEANUP_PENDING', 'Branch executor shutdown has not been confirmed');
            const prior=targets.map(scope=>scope.cleanup_intents[branch.id]).find(Boolean);
            if(prior)requireValue(prior.owner_sha256===ownerHash&&prior.tree===tree,'PARALLEL_CLEANUP_INTENT','Archived cleanup intent differs from exact ownership');
            else await this.git.verify(ownership);
            for(const scope of targets)scope.cleanup_intents[branch.id]={owner_sha256:ownerHash,tree};touch(current);
          });
          await runtime.runs.mutate(runId, 'parallel_cleanup', async current => {
            const targets=references.map(item=>at(current,item.path));
            if(targets.every(scope=>scope.cleaned_branches.includes(branch.id)))return;
            requireValue(targets.every(scope=>scope.cleanup_intents?.[branch.id]?.owner_sha256===ownerHash&&scope.cleanup_intents[branch.id].tree===tree),'PARALLEL_CLEANUP_INTENT','Cleanup needs exact journaled ownership');
            if(!targets.some(scope=>scope.cleaned_branches.includes(branch.id)))
            await this.git.remove(ownership, { reconcile: true, beforeRemove: async () => {
              const snapshot = await this.git.snapshot(ownership.workspace, state.base.base_commit, branch.write_paths);
              requireValue(snapshot.tree === tree, 'PARALLEL_BRANCH_CHANGED', 'A branch changed after its accepted snapshot; retain it for inspection');
            } });
            for(const scope of targets)if(!scope.cleaned_branches.includes(branch.id))scope.cleaned_branches.push(branch.id);
            touch(current);removed.push(ownership.workspace);
          });
          }
        }
      }
      return { removed };
    });
  }
}

export function parallelManagerFor({ configPath, env = process.env }) {
  const key = resolve(configPath); if (!managers.has(key)) managers.set(key, new ParallelWorktreeManager(join(dirname(key), 'workflow-worktrees'), { env })); return managers.get(key);
}
