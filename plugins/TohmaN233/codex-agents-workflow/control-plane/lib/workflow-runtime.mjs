import {discoverRuntimeEnvironment, verifyRuntimeEnvironment} from './runtime-environment.mjs';
import {normalizeExecutableRequirements} from './runtime-requirements.mjs';
import {ensureRunRuntimeEnvironment,workspaceRuntimeDirectories} from './runtime-environment-state.mjs';
import { randomBytes, randomUUID, timingSafeEqual } from 'node:crypto';
import { HUMAN_GATE_OUTPUT } from './workflow-schema.mjs';
import { join } from 'node:path';
import { readFile } from 'node:fs/promises';
import { WorkflowRunStore } from './workflow-run-store.mjs';
import { validateWorkflowGraph } from './workflow-validator.mjs';
import { canonicalJSON, digest } from './workflow-revisions.mjs';
import { noSymlinks, requireValue } from './workflow-paths.mjs';
import { pathBoundaries, resolveBindings, bindingPointers } from './workflow-bindings.mjs';
import { validateData } from './workflow-data-schema.mjs';
import { runPermissions, nodePermissions, approvalBinding, leaseToken, executionEnvelope, bindingContext } from './workflow-execution-envelope.mjs';
import { assertThreadReceipt, isThreadExecutor, threadResourcePacketText } from './thread-handoff.mjs';
import { assertThreadDispatchAvailable, assertThreadStartIdentity, assertThreadCompletion } from './thread-protocol.mjs';
import { initialRunState, advanceRun, graphInfo, setOutcome, interruptActiveNodes, EXECUTOR_NODES } from './workflow-state.mjs';
import { resolveWorkflowPins } from './workflow-pins.mjs';
import { childIdentity, childPermissions, validateChildClosure } from './workflow-subworkflow.mjs';
import { planParallelBranches } from './parallel/branch-planner.mjs';
import { nodeWorkspace } from './parallel/workspace.mjs';
import { mainSessionIdentity, sameMainSession } from './execution/main-session-adapter.mjs';
import { hostToolContracts, requireHostToolExecutionScope, validateHostToolReceipt } from './execution/host-tool-runner.mjs';
import { recordUsage as commitUsage, reserveCost } from './workflow-cost-ledger.mjs';
import { authoringReviewIdentity, isAuthoringRunProvenance } from './authoring/authoring-workflows.mjs';
import { validateAuthoringAcceptance } from './skill-import/authoring-acceptance.mjs';
import { assignFanoutItems, assignedFanoutIndices, assignedFanoutWritePaths, activeFanoutAssignmentIndices } from './execution/fanout-input-projection.mjs';
import { semanticTurnsConsumed, currentRoundAttempts } from './execution/completion-turn-budget.mjs';
import { loopRoundSignature, observeLoopItems, validateLoopExitOutput, validateLoopItemSources } from './workflow-loops.mjs';
import { validateFanoutProducerOutput } from './execution/completion-preflight.mjs';
import { WORKSPACE_SOURCE_LOCATIONS, revalidateBoundSourceLocations, validateWorkspaceSourceLocations } from './workspace-source-locations.mjs';

const CHILD_COMPLETION = Symbol('verified child completion');
const AUTHORING_HUMAN_ACCEPTANCE = Symbol('verified authoring human acceptance');
const HOST_MAIN_LIFECYCLE = Symbol('verified Host Main lifecycle');

const TERMINAL = new Set(['succeeded', 'failed', 'cancelled']);
const MANAGED_NATIVE_RESULT_IDENTITY = Object.freeze(['dispatch_id','result_index','result_sha256','thread_id','turn_id']);
function ownsNativeSlot(attempt,index,agentId) {
  const receipt=attempt.dispatch?.receipt;
  if(attempt.native_agents?.[index]===agentId)return true;
  if(receipt?.executor!=='codex-app-server-managed-native')return false;
  const assignments=receipt.subagent_plan?.assignments;
  return assignments?.some(item=>Object.hasOwn(item,'assignment_index'))
    ? assignments.some(item=>item.assignment_index===index&&item.dispatch_id===agentId)
    : receipt.subagent_dispatch_ids?.[index]===agentId;
}
const sameManagedNativeResultIdentity = (observed, trusted) => trusted?.agent_id
  ? observed?.kind === 'native_agent_result' && ['dispatch_id','result_index','result_sha256','agent_id'].every(field => observed?.[field] === trusted?.[field])
  : MANAGED_NATIVE_RESULT_IDENTITY.every(field => observed?.[field] === trusted?.[field]);
function authorize(state, token) {
  requireValue(typeof state.control_hash === 'string' && /^[a-f0-9]{64}$/.test(state.control_hash), 'RUN_STATE_CORRUPT', 'Run authority digest is invalid');
  requireValue(typeof token === 'string' && token.length <= 256 && timingSafeEqual(Buffer.from(digest(token), 'hex'), Buffer.from(state.control_hash, 'hex')), 'RUN_AUTHORITY', 'This action requires the Run main-controller capability');
}
function attemptFor(state, nodeId, attemptId, token, { active = true } = {}) {
  const node = state.nodes[nodeId];
  const attempt = node?.attempts.find(item => item.id === attemptId);
  requireValue(attempt && typeof token === 'string' && token.length <= 256 && digest(token) === attempt.lease_hash, 'LEASE_INVALID', 'Execution lease is invalid');
  if (active) requireValue(node.active_attempt_id === attemptId && ['claimed', 'running'].includes(node.status) && ['claimed', 'running'].includes(attempt.status), 'STALE_LEASE', 'Execution lease is no longer active');
  return { node, attempt };
}
function touch(state) { state.updated_at = new Date().toISOString(); }
export function nativeRejectedTurnHistory(record,nodeId,attemptId) {
  const current=record.state.nodes[nodeId]?.attempts.find(item=>item.id===attemptId)?.native_rejected_turns??{};
  const history={};
  const collect=slots=>{for(const [index,slot] of Object.entries(slots??{})){
    const turns=history[index]??=[];
    for(const item of slot.turns??[slot]){
      const next={agent_id:slot.agent_id,turn_id:item.turn_id,category:item.category,reason:item.reason};
      const prior=turns.find(turn=>turn.turn_id===next.turn_id);
      requireValue(!prior||canonicalJSON(prior)===canonicalJSON(next),'NATIVE_AGENT_REJECTION_CONFLICT',
        'A native turn has conflicting persisted rejection evidence');
      if(!prior)turns.push(next);
    }
  }};
  // Old Runs kept only the latest rejection in state. Their hash-chained
  // transitions retain the earlier IDs; recover those without rewriting history.
  if(Object.values(current).some(slot=>!Array.isArray(slot.turns)))for(const event of record.events??[]){
    if(event.kind!=='native_agent_rejection')continue;
    collect(event.payload.patch?.nodes?.[nodeId]?.attempts.find(item=>item.id===attemptId)?.native_rejected_turns);
  }
  collect(current);return history;
}
function publicRun(record) {
  const state = structuredClone(record.state);
  delete state.control_hash;
  for (const node of Object.values(state.nodes)) for (const attempt of node.attempts) delete attempt.lease_hash;
  return { ...state, completion_satisfied: state.status === 'succeeded',
    recovery_required: state.status === 'failed', sequence: record.sequence };
}
function completionPayload(payload) {
  requireValue(payload && payload.status === 'succeeded' && typeof payload.summary === 'string' && payload.summary.length <= 20000, 'COMPLETION_SCHEMA', 'Completion needs succeeded status and a bounded summary');
  for (const key of ['artifacts', 'evidence', 'changed_paths', 'outside_paths']) requireValue(Array.isArray(payload[key]), 'COMPLETION_SCHEMA', `Completion requires ${key}`);
  requireValue(Object.hasOwn(payload, 'structured_output') && payload.evidence.length, 'COMPLETION_EVIDENCE', 'Completion needs structured output and verification evidence');
  requireValue(Buffer.byteLength(canonicalJSON(payload)) <= 256 * 1024, 'COMPLETION_LIMIT', 'Completion output is too large; store artifacts separately');
  return JSON.parse(canonicalJSON(payload));
}
export function resolvedSubagentPlan(definition,state){
  if(definition.subagent_count===undefined)return null;
  const inputs=resolveBindings(definition.input_bindings??{},bindingContext(state)),items=definition.fanout?inputs[definition.fanout.input]:null;
  if(definition.fanout)requireValue(Array.isArray(items)&&items.length>0,'SUBAGENT_FANOUT_INPUT','Fan-out input must resolve to a nonempty list');
  const batchSize=definition.fanout?.batch_size;
  const count=definition.subagent_count==='auto'?(definition.fanout?(batchSize?Math.ceil(items.length/batchSize):items.length):1):definition.subagent_count;
  requireValue(Number.isSafeInteger(count)&&count>0&&(definition.fanout?.scheduling==='serial'||definition.fanout?.max_concurrency||count<=32),'SUBAGENT_COUNT','Unbounded parallel fan-out may dispatch at most 32 concurrent sub-Agents');
  const assignments=definition.fanout?assignFanoutItems(items,definition.fanout,count):null;
  return {count,items,assignments};
}

export class WorkflowRuntime {
  constructor({ workflowStore, runRoot, generationPolicy = null, authoringReviewer = null, context = {}, beforeStart = async () => {}, strictCapability = () => false, parallelWriteCapability = () => false, parallelManager, executionAdmission = null, environmentResolver = discoverRuntimeEnvironment, environmentVerifier = verifyRuntimeEnvironment, supportedNodeTypes = ['agent', 'skill_ref', 'tool', 'human_gate', 'subworkflow'] }) {
    this.generationPolicy = generationPolicy; this.authoringReviewer = authoringReviewer; this.environmentResolver = environmentResolver; this.environmentVerifier = environmentVerifier;
    this.workflows = workflowStore; this.runs = new WorkflowRunStore(runRoot); this.context = context;
    this.beforeStart = beforeStart; this.strictCapability = strictCapability; this.parallelWriteCapability = parallelWriteCapability;
    this.parallelManager = parallelManager; this.executionAdmission = executionAdmission;
    this.supportedNodeTypes = new Set(supportedNodeTypes);
  }
  async initialize() { await this.runs.initialize(); return this; }

  async assertAncestors(pins, { allowPaused = false } = {}) {
    let current = pins; let depth = 0;
    while (current.parent) {
      requireValue(++depth <= 32, 'SUBWORKFLOW_DEPTH', 'Invalid Run ancestry');
      const link = current.parent; const parent = await this.runs.read(link.run_id);
      const node = parent.state.nodes[link.node_id]; const attempt = node?.attempts.find(item => item.id === link.attempt_id);
      requireValue(parent.state.pins_hash === link.pins_hash && attempt?.child_run_id && attempt.child_run_id === current.child_run_id && node.active_attempt_id === attempt.id && ['claimed', 'running'].includes(node.status) && ['claimed', 'running'].includes(attempt.status), 'PARENT_LEASE_INACTIVE', 'The parent node no longer authorizes this child Run');
      requireValue(parent.state.status === 'running' || allowPaused && parent.state.status === 'paused', 'PARENT_RUN_INACTIVE', 'The parent Run blocks this child operation', { parent_run_id: link.run_id, parent_status: parent.state.status });
      current = parent.pins;
    }
  }

  async transition(runId, kind, mutate, options = {}, { allowPaused = false } = {}) {
    let executionLost = false;
    const result = await this.runs.mutate(runId, kind, async (state, pins, current) => {
      await this.assertAncestors(pins, { allowPaused });
      const previousStatus = state.status;
      const value = await mutate(state, pins, current);
      if (state.status === 'failed' && previousStatus !== 'failed') {
        (this.fenceRunExecution ?? (id => this.executionAdmission?.fenceRun(id)))(runId);
        executionLost = true;
      }
      return value;
    }, options);
    if (executionLost) this.scheduleRunDrain?.(runId);
    return result;
  }

  async start({ environment_directories = [], workflow_id, revision_hash, inputs = {}, workspace, access, allowed_paths = [], constraints = {}, main_actor, require_approval = false, run_id = randomUUID() }, {preparedEnvironment} = {}) {
    await this.runs.cleanupHistory();
    this.executionAdmission?.assertRunActive(run_id);
    requireValue(typeof main_actor === 'string' && main_actor.length > 0 && main_actor.length <= 256, 'MAIN_ACTOR', 'Run requires one main actor');
    requireValue(typeof require_approval === 'boolean', 'RUN_APPROVAL', 'Run approval policy must be boolean');
    const root = await this.workflows.snapshot(workflow_id, revision_hash);
    const permissions = runPermissions({ workspace, access, allowed_paths }); await noSymlinks(permissions.workspace);
    // A declared project root is the task workspace unless the caller explicitly
    // supplies a different root. Never require the model to repeat this Host path.
    if (!Object.hasOwn(inputs, 'project_root') && root.workflow.inputs_schema?.properties?.project_root?.type === 'string')
      inputs = { ...inputs, project_root: permissions.workspace };
    validateData(inputs, root.workflow.inputs_schema);
    requireValue(root.workflow.status === 'ready' && root.workflow.enabled, 'WORKFLOW_LAUNCH_BLOCKED', 'Only enabled Ready Workflows may resolve execution dependencies', { validation: validateWorkflowGraph(root.workflow, this.context) });
    const closure = await resolveWorkflowPins(this.workflows, root);
    for(const pack of closure.packs)requireValue(!['skill_import','workflow_build'].includes(pack.provenance?.kind)
      &&!['coarse','authored'].includes(pack.workflow.import_status?.mode),'CONVERTED_DEPLOYMENT_REQUIRED','Private authoring seeds cannot enter normal runtime execution');
    const checked = validateWorkflowGraph(root.workflow, { ...this.context, ...closure.context, check_runtime_requirements: true });
    requireValue(checked.launch_ready, 'WORKFLOW_LAUNCH_BLOCKED', 'Workflow cannot start in the current environment', { validation: checked });
    for (const pack of closure.packs) for (const node of pack.workflow.nodes) if (EXECUTOR_NODES.has(node.type)) requireValue(this.supportedNodeTypes.has(node.type), 'EXECUTOR_UNSUPPORTED', `Node type has no qualified executor: ${node.type}`, { node_id: node.id });
    for (const skill of closure.skills) {
      requireValue(!skill.observations.length, 'SKILL_DEPENDENCY_UNRESOLVED', 'Linked Skill dependencies need review or inlining before execution', { path: skill.path, observations: skill.observations });
      for (const [kind, names] of Object.entries(skill.requirements)) if (['tools', 'mcp_servers'].includes(kind)) requireValue(names.every(name => (this.context[kind] ?? []).includes(name)), 'SKILL_REQUIREMENT_UNAVAILABLE', 'Linked Skill requires an unavailable executor capability', { path: skill.path, kind, requirements: names });
    }
    await this.beforeStart(closure);
    const requirements = {executables:normalizeExecutableRequirements([...closure.packs.flatMap(pack=>pack.workflow.requirements.executables??[]), ...closure.skills.flatMap(skill=>skill.requirements.executables??[])])};
    const environment = preparedEnvironment ?? await this.environmentResolver(requirements,{extraDirectories:environment_directories,knownDirectories:workspaceRuntimeDirectories(permissions.workspace)});
    requireValue(environment.status === 'ready','ENVIRONMENT_SETUP_REQUIRED','请先准备运行依赖：发现缺少的工具后询问用户是否安装，完成后重新检查。',{environment});
    constraints = {...constraints, runtime_requirements:requirements, runtime_environment:environment};
    const providerIds = new Set(closure.provider_ids);
    const providers = (this.context.providers ?? []).filter(provider => providerIds.has(provider.id));
    for (const pack of closure.packs) if (pack.workflow.skill_policy.mode === 'strict') requireValue(await this.strictCapability(pack, { skills: closure.skills, providers }), 'STRICT_UNAVAILABLE', 'No qualified Strict executor is available; imported Workflows cannot silently downgrade');
    const blobs = closure.blobs;
    const pins = { schema_version: 1, thread_protocol_version: 2, ...(this.generationPolicy ? {generation:structuredClone(this.generationPolicy)} : {}), ...(this.authoringReviewer ? {authoring_reviewer:structuredClone(this.authoringReviewer)} : {}), root, providers: structuredClone(providers), children: closure.children, skills: closure.skills, resources: closure.resources };
    const controlToken = randomBytes(32).toString('hex');
    const state = initialRunState({ runId: run_id, pinsHash: digest(canonicalJSON(pins)), pins, inputs: structuredClone(inputs), permissions, constraints: structuredClone(constraints), controlHash: digest(controlToken), mainActor: main_actor, requireApproval: require_approval });
    validateLoopItemSources(state, root.workflow, {allowUnavailable:true});
    const scopes = validateChildClosure(pins, state);
    for (const scope of scopes) {
      const graph = graphInfo(scope.pack.workflow);
      const toolContracts = hostToolContracts(scope.pack.workflow);
      for (const node of scope.pack.workflow.nodes) if (EXECUTOR_NODES.has(node.type)) {
        const effective = nodePermissions(node, scope.state);
        for(const required of node.required_artifacts??[]){
          const exact=pathBoundaries([required.path])[0];
          requireValue(effective.access==='bounded_write'&&effective.allowed_paths.some(boundary=>boundary==='.'||exact===boundary||exact.startsWith(boundary.replace(/\/$/,'')+'/')),
            'REQUIRED_ARTIFACT_SCOPE',`Required artifact is outside the node/Run write grant: ${required.path}`,{node_id:node.id,path:required.path});
        }
        if (node.executor?.kind === 'tool') requireHostToolExecutionScope(toolContracts.get(node.executor.tool), effective);
        if (effective.access === 'bounded_write' && graph.regions.some(region => region.members.has(node.id))) requireValue(this.parallelManager || await this.parallelWriteCapability(node, scope.pack), 'PARALLEL_WRITE_UNAVAILABLE', 'Parallel write nodes require isolated worktrees and an integration gate');
      }
    }
    // A fan-out list supplied directly by Run inputs is fully known before the
    // Run exists. Validate every Host-owned child write path now; tool-produced
    // lists receive the same check while their Host result is materialized,
    // before any Agent dispatch.
    for(const node of root.workflow.nodes)if(node.fanout?.write_paths_field){
      const sources=bindingPointers(node.input_bindings?.[node.fanout.input]);
      if(sources.length&&sources.every(pointer=>pointer.startsWith('/inputs/'))){
        const effective=nodePermissions(node,state),plan=resolvedSubagentPlan(node,state);
        for(const items of plan.assignments)assignedFanoutWritePaths({workspace:state.permissions.workspace,
          nodeAllowedPaths:effective.allowed_paths,assignedItems:items,fanout:node.fanout});
      }
    }
    if (this.parallelManager) {
      const parallel = await this.parallelManager.preflight(root.workflow, permissions, scopes);
      if (parallel) { pins.parallel = parallel; state.pins_hash = digest(canonicalJSON(pins)); }
    }
    advanceRun(state, pins);
    this.executionAdmission?.assertRunActive(run_id);
    const created = await this.runs.create(run_id, pins, blobs, state);
    return { ...publicRun(created), control_token: controlToken };
  }

  async get(runId) { return publicRun(await this.runs.read(runId)); }

  async ensureRuntimeEnvironment(runId, options) { return ensureRunRuntimeEnvironment(this, runId, options); }

  async startSubworkflow(runId, args) {
    this.executionAdmission?.assertAttemptActive(runId, args.node_id, args.attempt_id);
    const envelope = await this.execution(runId, args);
    requireValue(envelope.subworkflow && envelope.executor.kind === 'subworkflow', 'SUBWORKFLOW_NODE_REQUIRED', 'This node is not a SubWorkflow');
    const identity = childIdentity(runId, args.node_id, args.attempt_id, args.control_token);
    const requestId = 'subworkflow-' + args.attempt_id;
    // The stable child identity is journaled before creating its Run directory.
    // A crash between these writes is reconciled by reopening this exact ID.
    await this.transition(runId, 'child_intent', async (state, pins) => {
      this.executionAdmission?.assertAttemptActive(runId, args.node_id, args.attempt_id);
      authorize(state, args.control_token); const { attempt } = attemptFor(state, args.node_id, args.attempt_id, args.lease_token);
      requireValue(state.status === 'running', 'RUN_NOT_RUNNING', 'Parent must be running to start a child');
      requireValue(!attempt.dispatch || attempt.child_run_id === identity.run_id && attempt.dispatch.request_id === requestId, 'DISPATCH_CONFLICT', 'Parent attempt has a different dispatch');
      if (!attempt.dispatch) {
        await revalidateBoundSourceLocations(pins.root.workflow.nodes.find(item => item.id === args.node_id), state, pins);
        attempt.child_run_id = identity.run_id;
        attempt.dispatch = { request_id: requestId, envelope_hash: digest(canonicalJSON(envelope)), phase: 'intent', receipt: null, cancellation_pending: false }; touch(state);
      }
      this.executionAdmission?.registerChild(runId, identity.run_id, args.node_id, args.attempt_id);
    });
    const result = await this.transition(runId, 'child_started', async (state, pins) => {
      this.executionAdmission?.assertAttemptActive(runId, args.node_id, args.attempt_id);
      authorize(state, args.control_token); const { node, attempt } = attemptFor(state, args.node_id, args.attempt_id, args.lease_token);
      requireValue(state.status === 'running', 'RUN_NOT_RUNNING', 'Parent was paused or cancelled before child creation');
      const definition = pins.root.workflow.nodes.find(item => item.id === args.node_id);
      const child = pins.children[definition.subworkflow.workflow_id + '@' + definition.subworkflow.revision_pin];
      const inherited = childPermissions(definition, state, pins, child);
      inherited.permissions.workspace = envelope.workspace;
      validateData(envelope.inputs, child.workflow.inputs_schema);
      const childPins = { ...pins, root: child, inherited_policy: inherited.policy, child_run_id: identity.run_id,
        parent: { run_id: runId, node_id: args.node_id, attempt_id: args.attempt_id, pins_hash: state.pins_hash } };
      if (pins.parallel) childPins.parallel = { ...pins.parallel, ...planParallelBranches(child.workflow, { permissions: inherited.permissions }) };
      const childState = initialRunState({ runId: identity.run_id, pinsHash: digest(canonicalJSON(childPins)), pins: childPins,
        inputs: structuredClone(envelope.inputs), permissions: inherited.permissions, constraints: structuredClone({...state.constraints,...(state.runtime_environment?{runtime_environment:state.runtime_environment}:{})}),
        controlHash: digest(identity.control_token), mainActor: state.main_actor, requireApproval: inherited.require_approval });
      let existing;
      // Only absence of the directory is a creation signal. A damaged existing
      // child is never replaced or treated as a fresh execution.
      try { await noSymlinks(this.runs.directory(identity.run_id)); existing = await this.runs.read(identity.run_id); }
      catch (error) {
        if (error.code !== 'ENOENT' || error.path !== this.runs.directory(identity.run_id)) throw error;
      }
      if (existing) {
        requireValue(existing.state.pins_hash === childState.pins_hash && existing.state.control_hash === childState.control_hash && canonicalJSON(existing.state.inputs) === canonicalJSON(childState.inputs) && canonicalJSON(existing.state.permissions) === canonicalJSON(childState.permissions), 'CHILD_RUN_CONFLICT', 'Existing child Run differs from its exact parent dispatch');
      } else {
        const blobs = new Map();
        for (const resource of pins.resources) blobs.set(resource.sha256, await readFile(join(this.runs.directory(runId), 'objects', resource.sha256)));
        this.executionAdmission?.assertAttemptActive(runId, args.node_id, args.attempt_id);
        advanceRun(childState, childPins); existing = await this.runs.create(identity.run_id, childPins, blobs, childState);
      }
      const acknowledged = attempt.dispatch.phase === 'acknowledged';
      if (!acknowledged) {
        attempt.dispatch.phase = 'acknowledged'; attempt.dispatch.receipt = { task_id: identity.run_id, child_run_id: identity.run_id };
        node.status = 'running'; attempt.status = 'running'; touch(state);
      }
      return { child: { ...publicRun(existing), control_token: identity.control_token }, acknowledged };
    });
    return { dispatched: !result.result.acknowledged, idempotent: result.result.acknowledged, receipt: { task_id: identity.run_id, child_run_id: identity.run_id }, child: result.result.child };
  }

  async collectSubworkflow(runId, args) {
    const envelope = await this.execution(runId, args, { allowInactive: true });
    requireValue(envelope.subworkflow, 'SUBWORKFLOW_NODE_REQUIRED', 'This node is not a SubWorkflow');
    const identity = childIdentity(runId, args.node_id, args.attempt_id, args.control_token);
    const parent = await this.runs.read(runId); const attempt = parent.state.nodes[args.node_id].attempts.find(item => item.id === args.attempt_id);
    requireValue(attempt.child_run_id === identity.run_id && attempt.dispatch?.receipt?.child_run_id === identity.run_id, 'CHILD_DISPATCH_REQUIRED', 'Child collection requires its acknowledged exact identity');
    const child = await this.runs.read(identity.run_id);
    requireValue(child.pins.parent?.run_id === runId && child.pins.parent.attempt_id === args.attempt_id, 'CHILD_RUN_CONFLICT', 'Child ancestry does not match this parent attempt');
    if (['failed', 'cancelled'].includes(child.state.status)) {
      requireValue(typeof this.failAttemptAfterQuiescence === 'function', 'EXECUTION_COORDINATOR_REQUIRED',
        'Child failure requires execution-aware cleanup before releasing the parent failure edge');
      return this.failAttemptAfterQuiescence(runId, args, { code: 'CHILD_RUN_FAILED',
        message: `Child ${identity.run_id} is ${child.state.status}: ${child.state.error?.message ?? 'No accepted output'}` });
    }
    requireValue(child.state.status === 'succeeded', 'CHILD_ACCEPTANCE_REQUIRED', 'Child Run must finish with explicit main acceptance before collection');
    const completions = Object.values(child.state.nodes).flatMap(node => node.attempts.flatMap(attempt => attempt.completion ? [attempt.completion] : []));
    return this.completeNode(runId, { ...args, completion: { status: 'succeeded', summary: 'Collected accepted child Workflow output',
      structured_output: resolveBindings(envelope.subworkflow.output_bindings, { output: child.state.output }),
      artifacts: [{ kind: 'child_run', run_id: identity.run_id }], evidence: [{ kind: 'accepted_child_run', run_id: identity.run_id, sequence: child.sequence, event_hash: child.events.at(-1).hash, pins_hash: child.state.pins_hash }],
      changed_paths: [...new Set(completions.flatMap(item => item.changed_paths))], outside_paths: [...new Set(completions.flatMap(item => item.outside_paths))] } }, CHILD_COMPLETION);
  }

  async cancelTree(runId, args, onFenced = () => {}) {
    const state = await this.cancel(runId, args, onFenced); const ids = [runId]; const errors = [];
    for (const [nodeId, node] of Object.entries(state.nodes)) for (const attempt of node.attempts) if (attempt.child_run_id) {
      try {
        const identity = childIdentity(runId, nodeId, attempt.id, args.control_token);
        requireValue(identity.run_id === attempt.child_run_id, 'CHILD_RUN_CONFLICT', 'Child identity does not match its parent'); ids.push(identity.run_id);
        let child;
        try { await noSymlinks(this.runs.directory(identity.run_id)); child = await this.get(identity.run_id); }
        catch (error) { if (error.code !== 'ENOENT' || error.path !== this.runs.directory(identity.run_id)) throw error; continue; }
        if (child.status !== 'succeeded') ids.push(...await this.cancelTree(identity.run_id, identity, onFenced));
      } catch (error) { ids.push(...(error.fenced_run_ids ?? [])); errors.push(error); }
    }
    const fenced = [...new Set(ids)];
    if (errors.length) throw Object.assign(new AggregateError(errors, 'Parent was fenced but some child cancellation journals could not be updated'), { code: 'CHILD_CANCELLATION_INCOMPLETE', fenced_run_ids: fenced });
    return fenced;
  }
  async authorizeController(runId, { control_token }) {
    const record = await this.runs.read(runId); authorize(record.state, control_token); return publicRun(record);
  }
  async recordExecutorEvent(runId, { node_id, attempt_id, lease_token, control_token, event }) {
    const fields = {
      codex_event: ['method', 'thread_id', 'turn_id', 'item_type', 'status', 'error_code', 'diagnostic', 'usage_available', 'input_tokens', 'cached_input_tokens', 'cache_write_input_tokens', 'output_tokens', 'reasoning_output_tokens'],
      tool_operation: ['call_id', 'tool', 'root', 'path', 'phase', 'sha256', 'before_sha256', 'after_sha256', 'source_sha256', 'entries', 'start_line', 'end_line', 'total_lines', 'start_byte', 'end_byte', 'total_bytes', 'complete', 'bytes', 'mime', 'code', 'diagnostic', 'program', 'cwd', 'args_sha256', 'arg_count', 'exit_code', 'signal', 'duration_ms'],
      profile_owned: ['home', 'receipt_home', 'executable_sha256', 'pid'],
      session_state: ['status', 'code', 'diagnostic'],
      model_catalog: ['requested_model', 'requested_effort', 'inventory_count', 'match_count', 'effort_supported', 'model_ids'],
      tool_capabilities: ['access', 'tools', 'allowed_paths_count', 'allowed_paths_sha256'],
      result_proposed: ['artifact', 'sha256', 'final_acceptance_required', 'proposal_hash', 'source_revision', 'expand_attempt_id'],
      skill_read: ['call_id', 'path'],
      output_progress: ['characters', 'retained_characters', 'truncated'],
      output_anomaly: ['artifact', 'sha256', 'bytes', 'streamed_bytes', 'budget_bytes'],
      scope_violation: ['artifact', 'sha256', 'bytes', 'changed_count', 'outside_count'],
      workspace_unreadable_authorized_path: ['path', 'kind', 'error_code', 'coverage', 'dev', 'ino', 'birthtime_ms', 'phase'],
      repair_context_prepared: ['path', 'sha256', 'bytes'],
      review_context_prepared: ['path', 'sha256', 'bytes', 'proposal_hash', 'source_revision', 'expand_attempt_id'],
      native_agent_spawn_intent: ['index', 'agent_id', 'task_name'],
      native_agent_spawn: ['index', 'agent_id'],
      node_input_materials: ['index','inputs_path','prompt_sha256','input_count','manifest_sha256'],
      native_prompt_delivery: ['dispatch_id','index','thread_id','turn_id','prompt_sha256','prompt_chars','input_sha256'],
      native_agent_followup_intent: ['index','agent_id','item_index','task_bundle_sha256','followup_kind','rejection_count'],
      native_agent_followup: [],
      semantic_blocked: ['correction', 'reason', 'thread_id', 'turn_id'],
      completion_invalid: ['correction', 'diagnostic', 'thread_id', 'turn_id'],
      required_artifacts_missing: ['correction', 'paths', 'thread_id', 'turn_id'],
    };
    requireValue(event && Object.hasOwn(fields, event.kind) && event.metadata && Object.keys(event.metadata).every(key => fields[event.kind].includes(key)) &&
      Object.values(event.metadata).every(value => value === null || typeof value === 'boolean' || typeof value === 'string' && value.length <= 4096 || Number.isSafeInteger(value)) &&
      Buffer.byteLength(canonicalJSON(event)) <= 32000,
      'EXECUTOR_EVENT_SCHEMA', 'Executor events accept bounded metadata only, never raw auth/model payloads');
    if(event.kind==='tool_operation' && event.metadata.tool==='read_workflow_resource_range' && event.metadata.phase==='read') {
      const {start_line:start,end_line:end,total_lines:total,bytes}=event.metadata;
      requireValue([start,end,total,bytes].every(Number.isSafeInteger)&&start>=1&&end>=start&&end-start<200&&total>=end&&bytes>=0&&bytes<=32768,'EXECUTOR_EVENT_SCHEMA','Resource range evidence must contain bounded valid coverage');
    }
    if(event.kind==='tool_operation' && event.metadata.tool==='read_workflow_resource_chunk' && event.metadata.phase==='read') {
      const {start_byte:start,end_byte:end,total_bytes:total,bytes,complete}=event.metadata;
      requireValue([start,end,total,bytes].every(Number.isSafeInteger)&&start>=0&&end>start&&total>=end&&bytes===end-start&&bytes<=12000&&typeof complete==='boolean'&&complete===(end===total),'EXECUTOR_EVENT_SCHEMA','Resource chunk evidence must contain contiguous bounded byte coverage');
    }
    const result = await this.runs.mutate(runId, 'executor_event', (state,pins) => {
      authorize(state, control_token);
      // Late shutdown metadata may document an already fenced attempt; it never
      // changes its lease or makes further execution permissible.
      const { attempt } = attemptFor(state, node_id, attempt_id, lease_token, { active: false });
      const authoringFinal=isAuthoringRunProvenance(pins.root.provenance)&&node_id===pins.root.workflow.finalization.node_id;
      if(authoringFinal && ['review_context_prepared','result_proposed'].includes(event.kind)){
        const expected=authoringReviewIdentity({state,pins}),observed={proposal_hash:event.metadata.proposal_hash,source_revision:event.metadata.source_revision,expand_attempt_id:event.metadata.expand_attempt_id};
        requireValue(canonicalJSON(observed)===canonicalJSON(expected),'AUTHORING_REVIEW_IDENTITY','Reviewer event is not bound to the current canonical proposal');
        if(event.kind==='review_context_prepared')requireValue(event.metadata.sha256===expected.proposal_hash,'AUTHORING_REVIEW_IDENTITY','Reviewer resource hash differs from the canonical proposal');
        if(event.kind==='result_proposed')requireValue(canonicalJSON(attempt.dispatch?.receipt?.authoring_review_context)===canonicalJSON(expected),'AUTHORING_REVIEW_IDENTITY','Reviewer result has no matching canonical dispatch receipt');
      }
      attempt.executor_event_count = (attempt.executor_event_count ?? 0) + 1;
      attempt.executor_events = [...(attempt.executor_events ?? []).slice(-63), { sequence: attempt.executor_event_count, ...structuredClone(event) }];
      if(event.kind==='native_agent_spawn_intent'){
        const definition=pins.root.workflow.nodes.find(item=>item.id===node_id);
        const provider=pins.providers.find(item=>item.id===definition?.executor?.provider_id);
        const count=resolvedSubagentPlan(definition,state)?.count??1;
        const {index,agent_id:id,task_name}=event.metadata;
        requireValue(provider?.kind==='native_agent'&&attempt.dispatch&&!attempt.dispatch.receipt&&
          Number.isInteger(index)&&index>=0&&index<count&&!attempt.native_agents?.[index]&&
          typeof task_name==='string'&&/^[a-z0-9_]{1,64}$/.test(task_name)&&
          typeof id==='string'&&id.endsWith('/'+task_name)&&id.length<=256,
        'NATIVE_AGENT_SPAWN_INTENT','Native spawn intent must bind one pending slot to a Host-generated task name and canonical Agent path');
        attempt.native_pending_spawns??={};
        const pending={agent_id:id,task_name};
        requireValue(!attempt.native_pending_spawns[index]||canonicalJSON(attempt.native_pending_spawns[index])===canonicalJSON(pending),
          'NATIVE_AGENT_SPAWN_INTENT_CONFLICT','Native slot already has a different Host spawn intent');
        requireValue(!Object.entries(attempt.native_pending_spawns).some(([slot,item])=>Number(slot)!==index&&item.agent_id===id),
          'NATIVE_AGENT_SPAWN_INTENT_CONFLICT','One Host-generated Agent path cannot occupy two native slots');
        attempt.native_pending_spawns[index]=pending;
      }
      if (event.kind === 'native_agent_spawn') {
        const definition = pins.root.workflow.nodes.find(item => item.id === node_id);
        const provider = pins.providers.find(item => item.id === definition?.executor?.provider_id);
        const plan = resolvedSubagentPlan(definition, state);
        const activeIndices=plan?activeFanoutAssignmentIndices(plan,definition.fanout,attempt.inherited_native_item_indices):[0];
        const { index, agent_id: id } = event.metadata;
        requireValue(provider?.kind === 'native_agent' && attempt.dispatch && !attempt.dispatch.receipt
          && Number.isInteger(index) && activeIndices.includes(index)
          && typeof id === 'string' && id.length > 0 && id.length <= 256,
        'NATIVE_AGENT_SPAWN', 'Native spawn must identify a pending exact Provider slot and real Agent ID');
        attempt.native_agents ??= {};
        requireValue(!attempt.native_agents[index] || attempt.native_agents[index] === id,
          'NATIVE_AGENT_SPAWN_CONFLICT', 'Native slot was already bound to another Agent');
        requireValue(!Object.entries(attempt.native_agents).some(([slot, existing]) => Number(slot) !== index && existing === id),
          'NATIVE_AGENT_SPAWN_CONFLICT', 'One native Agent cannot occupy two independent slots');
        if(attempt.native_pending_spawns){
          const pending=attempt.native_pending_spawns[index];
          requireValue(pending?.agent_id===id,'NATIVE_AGENT_SPAWN_CONFLICT','Native spawn acknowledgement differs from the Host-persisted spawn intent');
          delete attempt.native_pending_spawns[index];
          if(!Object.keys(attempt.native_pending_spawns).length)delete attempt.native_pending_spawns;
        }
        if(definition.fanout?.scheduling==='parallel'&&definition.fanout.max_concurrency&&!attempt.native_agents[index]){
          const spawned=Object.keys(attempt.native_agents).length;
          const completed=Object.keys(attempt.native_parallel_results??{}).length;
          requireValue(index===activeIndices[spawned]&&spawned-completed<definition.fanout.max_concurrency,
            'NATIVE_AGENT_PARALLEL_LIMIT','Capped parallel fan-out must spawn the next released slot without exceeding its active-Agent limit');
        }
        if(definition.fanout?.scheduling==='serial'){
          const position=activeIndices.indexOf(index),completed=attempt.native_serial_results?.length??0;
          requireValue(position===completed||position<completed&&attempt.native_serial_results[position]?.agent_id===id,
            'NATIVE_AGENT_SERIAL_ORDER','The previous serial sub-Agent must submit its result before the next may spawn');
        }
        attempt.native_agents[index] = id;
      }
      if(event.kind==='native_agent_followup_intent'){
        const definition=pins.root.workflow.nodes.find(item=>item.id===node_id);
        const {index,agent_id:itemAgent,item_index,task_bundle_sha256,followup_kind,rejection_count}=event.metadata;
        requireValue(definition?.fanout?.result_mode==='per_item'&&
          Number.isSafeInteger(index)&&attempt.native_agents?.[index]===itemAgent&&Number.isSafeInteger(item_index)&&item_index>=0&&
          /^[a-f0-9]{64}$/.test(task_bundle_sha256),'NATIVE_AGENT_FOLLOWUP','Per-item native follow-up needs an exact recorded Agent, item and task bundle');
        const assigned=assignedFanoutIndices(resolvedSubagentPlan(definition,state),definition.fanout,index);
        const unresolved=assigned.filter(itemIndex=>!attempt.native_item_results?.[itemIndex]);
        requireValue(unresolved[0]===item_index,'NATIVE_AGENT_FOLLOWUP','Per-item native follow-up must start with the next unresolved item');
        requireValue(followup_kind==='incremental'||followup_kind==='repair','NATIVE_AGENT_FOLLOWUP','Unknown native follow-up kind');
        if(followup_kind==='incremental')requireValue(definition.fanout.item_delivery==='incremental'&&rejection_count===0,
          'NATIVE_AGENT_FOLLOWUP','Incremental follow-up intent does not match this node');
        else requireValue(Number.isSafeInteger(rejection_count)&&rejection_count>0&&
          attempt.native_rejected_turns?.[index]?.count===rejection_count,
        'NATIVE_AGENT_FOLLOWUP','Repair follow-up intent does not match the persisted rejected turn');
        const pending={index,agent_id:itemAgent,item_index,task_bundle_sha256,followup_kind,rejection_count};
        requireValue(!attempt.native_pending_followup||canonicalJSON(attempt.native_pending_followup)===canonicalJSON(pending),
          'NATIVE_AGENT_FOLLOWUP_CONFLICT','Another native follow-up is already pending acknowledgement');
        attempt.native_pending_followup=pending;
      }
      if(event.kind==='native_agent_followup'){
        const definition=pins.root.workflow.nodes.find(item=>item.id===node_id);
        const pending=attempt.native_pending_followup;
        requireValue(definition?.fanout?.result_mode==='per_item'&&pending,
          'NATIVE_AGENT_FOLLOWUP','No Host-persisted native follow-up intent awaits acknowledgement');
        const {index,agent_id:itemAgent,item_index,task_bundle_sha256,followup_kind,rejection_count}=pending;
        const assigned=assignedFanoutIndices(resolvedSubagentPlan(definition,state),definition.fanout,index);
        const unresolved=assigned.filter(itemIndex=>!attempt.native_item_results?.[itemIndex]);
        requireValue(unresolved[0]===item_index,'NATIVE_AGENT_FOLLOWUP','Pending native follow-up no longer matches the next unresolved item');
        if(followup_kind==='incremental'){
          attempt.native_followups??={};
          const prior=attempt.native_followups[item_index];
          const next={agent_id:itemAgent,task_bundle_sha256};
          requireValue(!prior||canonicalJSON(prior)===canonicalJSON(next),'NATIVE_AGENT_FOLLOWUP_CONFLICT','Incremental native item already has a different follow-up receipt');
          attempt.native_followups[item_index]=next;
        }else{
          requireValue(attempt.native_rejected_turns?.[index]?.count===rejection_count,
            'NATIVE_AGENT_FOLLOWUP','Batch repair follow-up no longer matches its rejected turn');
          attempt.native_repair_followups??={};
          const key=`${index}:${rejection_count}`,prior=attempt.native_repair_followups[key];
          const next={agent_id:itemAgent,item_indices:unresolved,task_bundle_sha256};
          requireValue(!prior||canonicalJSON(prior)===canonicalJSON(next),'NATIVE_AGENT_FOLLOWUP_CONFLICT','Batch repair already has a different follow-up receipt');
          attempt.native_repair_followups[key]=next;
        }
        attempt.native_last_followup=pending;
        delete attempt.native_pending_followup;
      }
      if (event.kind === 'result_proposed') {
        requireValue(/^[a-f0-9]{64}$/.test(event.metadata.sha256) && event.metadata.artifact === `executor-${attempt_id}-${event.metadata.sha256}.json`, 'EXECUTOR_RESULT_ID', 'Result metadata must identify this exact attempt artifact');
        requireValue(!attempt.result_proposal || canonicalJSON(attempt.result_proposal) === canonicalJSON(event.metadata), 'EXECUTOR_RESULT_CONFLICT', 'Attempt already has a different result proposal');
        attempt.result_proposal = structuredClone(event.metadata);
      }
      if (event.kind === 'session_state' && event.metadata.status === 'closed' && attempt.dispatch) attempt.dispatch.cancellation_pending = false;
      touch(state);
    });
    return { sequence: result.sequence };
  }
  async recordNativeSerialResult(runId,{node_id,attempt_id,lease_token,control_token,index,agent_id,result}){
    const record=await this.runs.mutate(runId,'native_serial_result',(state,pins)=>{
      authorize(state,control_token);
      const {attempt}=attemptFor(state,node_id,attempt_id,lease_token);
      const definition=pins.root.workflow.nodes.find(item=>item.id===node_id);
      requireValue(definition?.fanout?.scheduling==='serial'&&attempt.dispatch&&!attempt.dispatch.receipt,
        'NATIVE_AGENT_SERIAL_RESULT','Only an active native serial fan-out accepts per-Agent results');
      const plan=resolvedSubagentPlan(definition,state);
      const activeIndices=activeFanoutAssignmentIndices(plan,definition.fanout,attempt.inherited_native_item_indices);
      const recorded=attempt.native_serial_results??[];
      const activePosition=activeIndices.indexOf(index);
      if(Number.isInteger(index)&&activePosition>=0&&activePosition<recorded.length){
        requireValue(recorded[activePosition].agent_id===agent_id&&canonicalJSON(recorded[activePosition].result)===canonicalJSON(result),
          'NATIVE_AGENT_SERIAL_RESULT_CONFLICT','A replayed serial result differs from the exact journaled Agent result');
        return;
      }
      requireValue(Number.isInteger(index)&&index===activeIndices[recorded.length]&&attempt.native_agents?.[index]===agent_id,
        'NATIVE_AGENT_SERIAL_ORDER','Serial result must match the next spawned Agent and index');
      if(definition.fanout.result_mode==='per_item'){
        const inherited=new Set(attempt.inherited_native_item_indices??[]);
        const assigned=assignedFanoutIndices(plan,definition.fanout,index);
        const expected=assigned.map(itemIndex=>attempt.native_item_results?.[itemIndex]);
        requireValue(expected.every((item,position)=>item&&(inherited.has(assigned[position])||item.agent_id===agent_id))&&canonicalJSON(expected.map(item=>item.result))===canonicalJSON(result),
          'NATIVE_ITEM_RESULT','Agent result must reproduce every journaled assigned item in order');
      }else validateData(result,definition.outputs_schema.properties[definition.fanout.result_output].items);
      attempt.native_serial_results=[...recorded,{agent_id,result:structuredClone(result)}];touch(state);
    });
    return {sequence:record.sequence};
  }
  async recordNativeRejectedTurn(runId,{node_id,attempt_id,lease_token,control_token,index,agent_id,turn_id,category,reason}){
    requireValue(Number.isInteger(index)&&index>=0&&typeof agent_id==='string'&&agent_id.length>0&&
      typeof turn_id==='string'&&turn_id.length>0&&turn_id.length<=256&&['blocked','invalid'].includes(category)&&
      typeof reason==='string'&&reason.length>0&&reason.length<=4096,
    'NATIVE_AGENT_REJECTION','Rejected native result needs an exact Agent, turn and bounded diagnostic');
    const record=await this.runs.mutate(runId,'native_agent_rejection',(state,pins,current)=>{
      authorize(state,control_token);
      const {attempt}=attemptFor(state,node_id,attempt_id,lease_token);
      const definition=pins.root.workflow.nodes.find(item=>item.id===node_id);
      const count=resolvedSubagentPlan(definition,state)?.count??1;
      requireValue(index<count&&ownsNativeSlot(attempt,index,agent_id)&&attempt.dispatch,
        'NATIVE_AGENT_REJECTION','Rejected turn does not belong to the active native Agent slot');
      const turns=nativeRejectedTurnHistory(current,node_id,attempt_id)[index]??[];
      const rejected=turns.find(item=>item.turn_id===turn_id);
      if(rejected){
        requireValue(rejected.agent_id===agent_id&&rejected.category===category&&rejected.reason===reason,
          'NATIVE_AGENT_REJECTION_CONFLICT','The same native turn has conflicting rejection evidence');
        return {new:false,count:turns.length};
      }
      const next={agent_id,turn_id,category,reason,count:turns.length+1,
        turns:[...turns.map(({turn_id,category,reason})=>({turn_id,category,reason})),{turn_id,category,reason}]};
      attempt.native_rejected_turns={...(attempt.native_rejected_turns??{}),[index]:next};touch(state);
      attempt.native_latest_turns={...(attempt.native_latest_turns??{}),[index]:{agent_id,turn_id}};
      return {new:true,count:next.count};
    });
    return record.result;
  }
  async recordNativeParallelResult(runId,{node_id,attempt_id,lease_token,control_token,index,agent_id,result}){
    const record=await this.runs.mutate(runId,'native_parallel_result',(state,pins)=>{
      authorize(state,control_token);
      const {attempt}=attemptFor(state,node_id,attempt_id,lease_token);
      const definition=pins.root.workflow.nodes.find(item=>item.id===node_id);
      requireValue(definition?.fanout?.scheduling==='parallel'&&attempt.dispatch&&(!attempt.dispatch.receipt||!definition.fanout.max_concurrency),
        'NATIVE_AGENT_PARALLEL_RESULT','Only an active parallel fan-out accepts per-Agent results');
      const count=resolvedSubagentPlan(definition,state).count;
      requireValue(Number.isInteger(index)&&index>=0&&index<count&&attempt.native_agents?.[index]===agent_id,
        'NATIVE_AGENT_PARALLEL_RESULT','Parallel result must match a spawned Agent and slot');
      const recorded=attempt.native_parallel_results??{};
      if(recorded[index]){
        requireValue(recorded[index].agent_id===agent_id&&canonicalJSON(recorded[index].result)===canonicalJSON(result),
          'NATIVE_AGENT_PARALLEL_RESULT_CONFLICT','A replayed parallel result differs from the journaled Agent result');
        return;
      }
      if(definition.fanout.result_mode==='per_item'){
        const plan=resolvedSubagentPlan(definition,state),inherited=new Set(attempt.inherited_native_item_indices??[]);
        const assigned=assignedFanoutIndices(plan,definition.fanout,index);
        const expected=assigned.map(itemIndex=>attempt.native_item_results?.[itemIndex]);
        requireValue(expected.every((item,position)=>item&&(inherited.has(assigned[position])||item.agent_id===agent_id))&&canonicalJSON(expected.map(item=>item.result))===canonicalJSON(result),
          'NATIVE_ITEM_RESULT','Agent result must reproduce every journaled assigned item in order');
      }else validateData(result,definition.outputs_schema.properties[definition.fanout.result_output].items);
      attempt.native_parallel_results={...recorded,[index]:{agent_id,result:structuredClone(result)}};touch(state);
    });
    return {sequence:record.sequence};
  }
  async recordManagedNativeResults(runId,{node_id,attempt_id,lease_token,control_token,results}){
    requireValue(Array.isArray(results)&&results.every((item,index)=>item&&Object.keys(item).every(key=>['dispatch_id','result_index','result_sha256','thread_id','turn_id','agent_id'].includes(key))&&item.result_index===index&&typeof item.dispatch_id==='string'&&item.dispatch_id.length>0&&item.dispatch_id.length<=256&&/^[a-f0-9]{64}$/.test(item.result_sha256)&&(
      typeof item.agent_id==='string'&&item.agent_id===item.dispatch_id&&!item.thread_id&&!item.turn_id ||
      typeof item.thread_id==='string'&&item.thread_id.length>0&&item.thread_id.length<=256&&typeof item.turn_id==='string'&&item.turn_id.length>0&&item.turn_id.length<=256&&!item.agent_id
    )),'MANAGED_NATIVE_RESULT_RECEIPT','Sub-Agent results need one bounded native Agent ID or managed session receipt per child');
    const serialized=canonicalJSON(results);
    const record=await this.runs.mutate(runId,'managed_native_results',(state,pins)=>{
      authorize(state,control_token);const {attempt}=attemptFor(state,node_id,attempt_id,lease_token);
      const definition=pins.root.workflow.nodes.find(item=>item.id===node_id);
      requireValue(definition?.fanout&&definition.subagent_count!==undefined,'MANAGED_NATIVE_RESULT_RECEIPT','Only a pinned managed fan-out node can record child results');
      const {count}=resolvedSubagentPlan(definition,state),dispatchIds=attempt.dispatch?.receipt?.subagent_dispatch_ids;
      const expectedCount=definition.fanout?.result_mode==='per_item'?attempt.dispatch?.receipt?.subagent_plan?.resolved_count:count;
      requireValue(Array.isArray(dispatchIds)&&dispatchIds.length===expectedCount&&results.length===expectedCount&&results.every((item,index)=>item.dispatch_id===dispatchIds[index]),'MANAGED_NATIVE_RESULT_RECEIPT','Managed child results must match the exact persisted dispatch identities and order');
      if(attempt.managed_native_results){requireValue(canonicalJSON(attempt.managed_native_results)===serialized,'MANAGED_NATIVE_RESULT_CONFLICT','Managed child results differ from the exact previously persisted receipts');return;}
      attempt.managed_native_results=structuredClone(results);touch(state);
    });
    return {sequence:record.sequence};
  }
  async execution(runId, { node_id, attempt_id, lease_token, control_token }, { allowInactive = false, allowPaused = false } = {}) {
    const { state, pins } = await this.runs.read(runId); authorize(state, control_token);
    if (pins.parent) this.executionAdmission?.registerChild(pins.parent.run_id, runId, pins.parent.node_id, pins.parent.attempt_id);
    if (!allowInactive) await this.assertAncestors(pins, { allowPaused });
    const { attempt } = attemptFor(state, node_id, attempt_id, lease_token, { active: !allowInactive });
    requireValue(allowInactive || state.status === 'running' || allowPaused && state.status === 'paused', 'RUN_NOT_RUNNING', 'Run must be running before dispatch');
    const node = pins.root.workflow.nodes.find(item => item.id === node_id);
    // Source hashes gate first claim/dispatch, not reads during an admitted attempt:
    // its authorized edits can legitimately change the referenced files.
    return executionEnvelope(node, state, pins, attempt, lease_token);
  }
  async threadResourcePacket(runId, args, { max_chars }) {
    requireValue(Number.isInteger(max_chars) && max_chars >= 0, 'THREAD_RESOURCE_LIMIT', 'Thread resource packet needs a nonnegative prompt budget');
    const envelope = await this.execution(runId, args);
    requireValue(isThreadExecutor(envelope.executor), 'THREAD_EXECUTOR', 'Only Codex task-thread nodes can prepare a task resource packet');
    const { pins } = await this.runs.read(runId);
    const manifest = new Map((pins.root.resources ?? []).map(resource => [resource.path, resource]));
    const resources = [];
    for (const path of envelope.resources) {
      const resource = manifest.get(path);
      requireValue(resource, 'THREAD_RESOURCE_MISSING', 'Thread node references a resource missing from its immutable Run closure', { path });
      const bytes = await readFile(join(this.runs.directory(runId), 'objects', resource.sha256));
      const text = bytes.toString('utf8');
      requireValue(Buffer.from(text, 'utf8').equals(bytes), 'THREAD_RESOURCE_BINARY', 'Codex task handoff cannot transport a binary pinned resource; pass it as an explicit task input or use a non-thread executor', { path });
      const candidate = [...resources, { path, sha256: resource.sha256, text }];
      requireValue(threadResourcePacketText(candidate).length <= max_chars, 'THREAD_RESOURCE_LIMIT', 'Pinned Workflow text is too large for this Codex task handoff; split the node or use a non-thread executor', { path, max_chars });
      resources.push(candidate.at(-1));
    }
    return resources;
  }
  async next(runId) {
    return this.#nextFromRecord(runId, await this.runs.read(runId));
  }

  async snapshot(runId, { control_token, after_sequence = 0 } = {}) {
    const record = await this.runs.read(runId);
    return { state: publicRun(record), next: await this.#nextFromRecord(runId, record),
      events: control_token === undefined ? [] : this.#eventsFromRecord(record, { control_token, after_sequence }) };
  }

  async #nextFromRecord(runId, { state, pins, sequence }) {
    let parentBlock = null;
    try { await this.assertAncestors(pins); } catch (error) { if (!['PARENT_RUN_INACTIVE', 'PARENT_LEASE_INACTIVE'].includes(error.code)) throw error; parentBlock = { code: error.code, message: error.message }; }
    return {
      run_id: runId, status: state.status, sequence,
      parent_block: parentBlock,
      ready: state.status === 'running' && !parentBlock ? graphInfo(pins.root.workflow).order.filter(id => state.nodes[id].status === 'ready') : [],
      approvals: Object.values(state.approvals).filter(approval => approval.status === 'pending'),
      integration_gates: (pins.parallel?.regions ?? []).filter(region => region.isolated && state.nodes[region.join_id].status === 'blocked').map(region => ({ region_id: region.id, join_id: region.join_id, phase: state.parallel?.[region.id]?.phase ?? 'not_prepared', proposal: state.parallel?.[region.id]?.proposal ?? null, error: state.parallel?.[region.id]?.error ?? null })),
    };
  }

  async claimNode(runId, { node_id, owner, request_id, control_token, expected_sequence }, authority = null) {
    requireValue(typeof request_id === 'string' && request_id.length > 0 && request_id.length <= 128, 'CLAIM_REQUEST_ID', 'Claim needs a stable request ID');
    requireValue(typeof owner === 'string' && owner.length > 0 && owner.length <= 256, 'CLAIM_OWNER', 'Claim needs an executor owner');
    const prepared = await this.ensureRuntimeEnvironment(runId, {control_token, expected_sequence});
    if (expected_sequence !== undefined) expected_sequence = prepared.sequence;
    const result = await this.transition(runId, 'claim', async (state, pins) => {
      authorize(state, control_token);
      const definition = pins.root.workflow.nodes.find(node => node.id === node_id); const node = state.nodes[node_id];
      requireValue(definition && node, 'NODE_MISSING', 'Workflow node does not exist');
      if (definition.executor?.kind === 'main') {
        requireValue(authority === HOST_MAIN_LIFECYCLE, 'HOST_MAIN_LIFECYCLE_REQUIRED', 'Logical Main claims belong to the Host execution lane');
        requireValue(owner === state.main_actor, 'FINALIZER_AUTHORITY', 'Main-agent nodes cannot be claimed by a worker');
      }
      const existing = node.attempts.find(attempt => attempt.claim_request_id === request_id);
      if (existing) {
        requireValue(existing.owner === owner && node.active_attempt_id === existing.id && ['claimed', 'running'].includes(existing.status), 'CLAIM_CONFLICT', 'Claim request refers to a different or closed executor');
        return executionEnvelope(definition, state, pins, existing, leaseToken(control_token, runId, node_id, existing.id, existing.lease_generation ?? 0));
      }
      requireValue(state.status === 'running' && node.status === 'ready', 'NODE_NOT_READY', 'Only a ready node in an active Run may be claimed');
      await revalidateBoundSourceLocations(definition, state, pins);
      const approval = approvalBinding(definition, state, pins);
      if (approval.required) requireValue(state.approvals[node.approval_id]?.status === 'approved' && state.approvals[node.approval_id].binding_hash === approval.hash, 'APPROVAL_REQUIRED', 'Exact node approval is required before claim');
      const id = randomUUID(); const token = leaseToken(control_token, runId, node_id, id);
      const attempt = { id, owner, started_at: new Date().toISOString(), claim_request_id: request_id, lease_hash: digest(token), status: 'claimed', dispatch: null, completion_hash: null, reconciliation: null,
        ...(definition.executor?.kind === 'main' ? { completion_turns: 0 } : {}) };
      const signature = loopRoundSignature(state, pins.root.workflow, node_id);
      if (Object.keys(signature).length) { attempt.loop_rounds = signature; node.current_loop_rounds = signature; }
      if(definition.fanout?.result_mode==='per_item'){
        const inherited={};
        for(const prior of currentRoundAttempts(node))for(const [itemIndex,item] of Object.entries(prior.native_item_results??{})){
          requireValue(!inherited[itemIndex]||canonicalJSON(inherited[itemIndex].result)===canonicalJSON(item.result),
            'NATIVE_ITEM_RESULT_CONFLICT',`Previously accepted item ${itemIndex} differs across attempts`);
          inherited[itemIndex]=structuredClone(item);
        }
        if(Object.keys(inherited).length){attempt.native_item_results=inherited;
          attempt.inherited_native_item_indices=Object.keys(inherited).map(Number).sort((a,b)=>a-b);}
      }
      node.attempts.push(attempt); node.active_attempt_id = id; node.status = 'claimed';
      const observation = await observeLoopItems(state, pins.root.workflow, node_id, nodeWorkspace(node_id, state, pins));
      if (Object.keys(observation).length) attempt.loop_observation = { before: observation };
      const envelope = executionEnvelope(definition, state, pins, attempt, token);
      touch(state);
      return envelope;
    }, { expected_sequence });
    return { ...result.result, sequence: result.sequence, idempotent: result.idempotent ?? false };
  }

  claimHostMain(runId,args){return this.claimNode(runId,args,HOST_MAIN_LIFECYCLE);}

  /** Durably reserve one model response before dispatch so retries cannot reset its budget. */
  async reserveHostMainTurn(runId, { node_id, attempt_id, lease_token, control_token }) {
    const result = await this.transition(runId, 'completion_turn', (state, pins) => {
      authorize(state, control_token);
      requireValue(state.status === 'running', 'RUN_TERMINAL', 'Run cannot start a completion turn');
      const { node, attempt } = attemptFor(state, node_id, attempt_id, lease_token);
      const definition = pins.root.workflow.nodes.find(item => item.id === node_id);
      requireValue(definition?.executor?.kind === 'main', 'HOST_MAIN_NODE', 'Only a Main node reserves completion turns');
      requireValue(semanticTurnsConsumed(node) < definition.retry.max_attempts, 'RETRY_LIMIT', 'Node exhausted its pinned semantic attempt limit');
      attempt.completion_turns = (attempt.completion_turns ?? 1) + 1;
      touch(state);
      return { completion_turns: attempt.completion_turns, remaining: definition.retry.max_attempts - semanticTurnsConsumed(node) };
    });
    return result.result;
  }
  async recordNativeItemResults(runId,{node_id,attempt_id,lease_token,control_token,index,agent_id,turn_id,target_indices,result}){
    const record=await this.runs.mutate(runId,'native_item_results',(state,pins)=>{
      authorize(state,control_token);
      const {attempt}=attemptFor(state,node_id,attempt_id,lease_token);
      const definition=pins.root.workflow.nodes.find(item=>item.id===node_id);
      requireValue(definition?.fanout?.result_mode==='per_item'&&attempt.dispatch&&ownsNativeSlot(attempt,index,agent_id),
        'NATIVE_ITEM_RESULT','Per-item results require the exact active native Agent assignment');
      const plan=resolvedSubagentPlan(definition,state),assigned=assignedFanoutIndices(plan,definition.fanout,index);
      const incremental=definition.fanout.item_delivery==='incremental';
      if(incremental)requireValue(typeof turn_id==='string'&&turn_id.length>0&&turn_id.length<=256,
        'NATIVE_ITEM_RESULT','Incremental per-item results need the exact completed Agent turn');
      requireValue(result&&typeof result==='object'&&!Array.isArray(result)&&Object.keys(result).length===1&&Array.isArray(result.items),
        'NATIVE_ITEM_RESULT','Per-item Agent result must contain only an items array');
      const stored=attempt.native_item_results??{};
      const unresolvedBefore=assigned.filter(itemIndex=>!stored[itemIndex]);
      requireValue(Array.isArray(target_indices)&&target_indices.every(Number.isSafeInteger)&&
        canonicalJSON(target_indices)===canonicalJSON(incremental?unresolvedBefore.slice(0,1):unresolvedBefore),
      'NATIVE_ITEM_RESULT','Per-item Host targets must equal the exact unresolved assignment in deterministic order');
      if(!incremental&&result.items.length!==target_indices.length){
        const reason=`Native Agent ${agent_id} returned ${result.items.length} entries for ${target_indices.length} Host-selected items; no positional result was accepted`;
        return {accepted_item_indices:assigned.filter(itemIndex=>Boolean(stored[itemIndex])),
          unresolved_item_indices:unresolvedBefore,issues:[{item_index:null,category:'invalid',reason}]};
      }
      const issues=[];
      if(result.items.length>target_indices.length)issues.push({item_index:null,category:'invalid',
        reason:`Native Agent ${agent_id} returned ${result.items.length} entries for ${target_indices.length} Host-selected items`});
      const schema=definition.outputs_schema.properties[definition.fanout.result_output].items;
      let changed=false;
      for(let localIndex=0;localIndex<Math.min(result.items.length,target_indices.length);localIndex++){
        const item=result.items[localIndex],itemIndex=target_indices[localIndex];
        if(!item||typeof item!=='object'||Array.isArray(item)){
          issues.push({item_index:itemIndex,category:'invalid',reason:`Host-selected item ${itemIndex} needs one object result`});continue;
        }
        const keys=Object.keys(item);
        const sharedChangeField=definition.fanout.shared_change_field;
        const delegated=item.outcome==='delegated'||item.outcome==='blocked'&&Object.hasOwn(item,'result')&&sharedChangeField;
        if(delegated){
          const allowedKeys=['outcome','result','block_reason'];
          const hasValidReason=typeof item.block_reason==='string'&&item.block_reason.trim()&&item.block_reason.length<=4096;
          if(keys.some(key=>!allowedKeys.includes(key))||!Object.hasOwn(item,'result')||
            item.outcome==='blocked'&&!hasValidReason||Object.hasOwn(item,'block_reason')&&!hasValidReason){
            issues.push({item_index:itemIndex,category:'invalid',reason:`Item ${itemIndex} has an invalid delegated shared-change result`});continue;
          }
          try{validateData(item.result,schema);}catch(error){if(error.code!=='DATA_INVALID')throw error;
            issues.push({item_index:itemIndex,category:'invalid',reason:error.message});continue;}
          const shared=item.result?.[sharedChangeField];
          const present=typeof shared==='string'?Boolean(shared.trim()):Array.isArray(shared)?shared.length>0:
            shared&&typeof shared==='object'?Object.keys(shared).length>0:shared!==undefined&&shared!==null&&shared!==false;
          if(!sharedChangeField||!present){issues.push({item_index:itemIndex,category:'invalid',
            reason:`Item ${itemIndex} delegated without a nonempty ${sharedChangeField ?? 'shared change'} result`});continue;}
          const prior=stored[itemIndex];
          if(prior&&!(prior.agent_id===agent_id&&canonicalJSON(prior.result)===canonicalJSON(item.result))){
            issues.push({item_index:itemIndex,category:'invalid',reason:`Accepted item ${itemIndex} differs from its journaled result`});continue;
          }
          if(!prior){stored[itemIndex]={agent_id,result:structuredClone(item.result),delegated:true,
            ...(item.block_reason?{delegation_reason:item.block_reason}:{}),...(incremental?{turn_id}:{})};changed=true;}
          continue;
        }
        if(item.outcome==='blocked'&&keys.length===2&&keys.every(key=>['outcome','block_reason'].includes(key))&&typeof item.block_reason==='string'&&item.block_reason.trim()&&item.block_reason.length<=4096){
          if(!stored[itemIndex])issues.push({item_index:itemIndex,category:'blocked',reason:item.block_reason});
          continue;
        }
        if(item.outcome!=='completed'||keys.length!==2||!keys.every(key=>['outcome','result'].includes(key))){
          issues.push({item_index:itemIndex,category:'invalid',reason:`Item ${itemIndex} needs completed result or specific blocked reason`});continue;
        }
        try{validateData(item.result,schema);}catch(error){if(error.code!=='DATA_INVALID')throw error;
          issues.push({item_index:itemIndex,category:'invalid',reason:error.message});continue;}
        const prior=stored[itemIndex];
        if(prior&&!(prior.agent_id===agent_id&&canonicalJSON(prior.result)===canonicalJSON(item.result))){
          issues.push({item_index:itemIndex,category:'invalid',reason:`Accepted item ${itemIndex} differs from its journaled result`});
          continue;
        }
        if(!prior){stored[itemIndex]={agent_id,result:structuredClone(item.result),...(incremental?{turn_id}: {})};changed=true;}
      }
      if(changed){attempt.native_item_results=stored;
        if(incremental)attempt.native_latest_turns={...(attempt.native_latest_turns??{}),[index]:{agent_id,turn_id}};
        touch(state);}
      const unresolved=assigned.filter(itemIndex=>!stored[itemIndex]);
      for(const itemIndex of target_indices.slice(result.items.length))issues.push({item_index:itemIndex,category:'invalid',reason:`Item ${itemIndex} is missing from the ordered result`});
      if(!incremental)for(const itemIndex of unresolved)if(!issues.some(issue=>issue.item_index===itemIndex))issues.push({item_index:itemIndex,category:'invalid',reason:`Item ${itemIndex} is missing from the completed result`});
      return {accepted_item_indices:assigned.filter(itemIndex=>Boolean(stored[itemIndex])),unresolved_item_indices:unresolved,issues,
        ...(unresolved.length?{}:{result:assigned.map(itemIndex=>stored[itemIndex].result)})};
    });
    return record.result;
  }

  async completeNode(runId, { node_id, attempt_id, lease_token, completion }, authority) {
    const payload = completionPayload(completion); const fingerprint = digest(canonicalJSON(payload));
    const result = await this.transition(runId, 'complete', async (state, pins) => {
      const found = attemptFor(state, node_id, attempt_id, lease_token, { active: false });
      if (found.attempt.completion_hash) {
        requireValue(found.attempt.completion_hash === fingerprint, 'COMPLETION_CONFLICT', 'Duplicate completion differs from committed output'); return;
      }
      const { node, attempt } = attemptFor(state, node_id, attempt_id, lease_token);
      requireValue(!['cancelled', 'succeeded'].includes(state.status), 'RUN_TERMINAL', 'Run cannot accept this completion');
      const definition = pins.root.workflow.nodes.find(item => item.id === node_id);
      if(definition.executor?.kind==='main'){
        requireValue([HOST_MAIN_LIFECYCLE,AUTHORING_HUMAN_ACCEPTANCE].includes(authority?.kind),'HOST_MAIN_LIFECYCLE_REQUIRED','Logical Main completion requires the Host-persisted result lane');
        const orchestration = definition.executor.mode === 'orchestration';
        const receipt = attempt.dispatch?.receipt;
        requireValue(orchestration ? receipt?.executor === 'codex-current-main-orchestration' && receipt.thread_id === state.constraints.native_parent_thread_id : ['codex-app-server-host-main','codex-app-server'].includes(receipt?.executor), 'HOST_MAIN_RECEIPT_REQUIRED', 'Main completion requires its exact execution-mode receipt');
        requireValue(attempt.result_proposal?.sha256,'HOST_MAIN_RESULT_REQUIRED','Logical Main completion requires one Host-persisted result proposal');
        const persisted=await this.runs.readExecutorResult(runId,attempt.id,attempt.result_proposal.sha256);
        const proposed=structuredClone(payload);delete proposed.acceptance;
        if(node_id===pins.root.workflow.finalization.node_id&&definition.outputs_schema?.properties?.accepted
          && !Object.hasOwn(persisted.structured_output,'accepted'))delete proposed.structured_output.accepted;
        requireValue(digest(canonicalJSON(persisted))===attempt.result_proposal.sha256&&canonicalJSON(proposed)===canonicalJSON(persisted),'HOST_MAIN_RESULT_REQUIRED','Completion differs from the exact Host-persisted Main result');
      }
      requireValue(definition.type !== 'subworkflow' || authority === CHILD_COMPLETION, 'CHILD_ACCEPTANCE_REQUIRED', 'SubWorkflow output must be collected from its exact accepted child Run');
      validateData(payload.structured_output, definition.outputs_schema);
      validateLoopExitOutput(state, pins.root.workflow, node_id, payload.structured_output);
      for (const [output_name, kind] of Object.entries(definition.output_validators ?? {}))
        if (kind === WORKSPACE_SOURCE_LOCATIONS)
          payload.structured_output[output_name] = (await validateWorkspaceSourceLocations(payload.structured_output[output_name], state.permissions.workspace,
            { producer_node_id: node_id, output_name })).canonical_locations;
      validateFanoutProducerOutput(definition, payload.structured_output, state, pins);
      if (['provider', 'thread'].includes(definition.executor?.kind) || definition.executor?.kind === 'main' && (state.constraints.require_main_session_identity === true || state.cost_ledger.budget || state.constraints.require_usage_ledger === true)) {
        requireValue(attempt.dispatch?.receipt, 'DISPATCH_RECEIPT_REQUIRED', 'Semantic completion requires a persisted exact task identity');
        if (state.cost_ledger.budget || state.constraints.require_usage_ledger === true) requireValue(state.cost_ledger.calls.find(item => item.call_id === attempt.dispatch.request_id)?.usage, 'USAGE_REQUIRED', 'Plan 1 semantic work needs recorded actual or explicitly unknown usage before completion');
      }
      if (definition.type === 'tool') requireValue(attempt.host_tool?.receipt?.status === 'succeeded', 'HOST_TOOL_RECEIPT_REQUIRED', 'Tool completion requires a successful exact host receipt');
      if (definition.decision) {
        const decision = definition.decision; const output = payload.structured_output;
        requireValue(output && output.decision_id === decision.id && decision.options.includes(output.decision) && Array.isArray(output.references) && decision.required_references.every(reference => output.references.includes(reference)), 'DECISION_OUTPUT_INVALID', 'Semantic output does not satisfy its finite decision contract');
      }
      if (definition.executor?.kind === 'thread') assertThreadCompletion(state, pins, attempt, payload);
      const permission = nodePermissions(definition, state);
      requireValue(!payload.outside_paths.length, 'SCOPE_VIOLATION', 'Completion reports writes outside the permitted scope');
      const changed = pathBoundaries(payload.changed_paths);
      requireValue(permission.access === 'bounded_write' || !changed.length, 'SCOPE_VIOLATION', 'Read-only node reports filesystem changes');
      const key = value => process.platform === 'win32' ? value.toLowerCase() : value;
      requireValue(changed.every(path => permission.allowed_paths.some(root => root === '.' || key(path) === key(root) || key(path).startsWith(key(root) + '/'))), 'SCOPE_VIOLATION', 'Changed paths exceed the exact execution envelope');
      for(const required of definition.required_artifacts??[]){
        const exact=pathBoundaries([required.path])[0];
        requireValue(changed.some(path=>key(path)===key(exact)),'REQUIRED_ARTIFACT_MISSING',`Completion did not observe the exact required artifact path ${required.path}`,{requirement_id:required.requirement_id,path:required.path});
      }
      if(definition.subagent_count!==undefined){
        const {count,items,assignments}=resolvedSubagentPlan(definition,state);
        if(count>1||definition.fanout){
          const proof=payload.evidence.find(item=>item?.kind==='subagent_pool');
          const dispatched=attempt.dispatch?.receipt?.subagent_dispatch_ids,persistedPlan=attempt.dispatch?.receipt?.subagent_plan;
          const childEvidence=payload.evidence.filter(item=>['managed_native_result','native_agent_result'].includes(item?.kind)),trustedResults=attempt.managed_native_results,joined=definition.fanout?payload.structured_output?.[definition.fanout.result_output]:null;
          const perItem=definition.fanout?.result_mode==='per_item';
          const inherited=new Set(attempt.inherited_native_item_indices??[]);
          const activeAssignments=perItem?assignments.map((_assigned,assignmentIndex)=>{
            const indices=assignedFanoutIndices({count,items,assignments},definition.fanout,assignmentIndex).filter(itemIndex=>!inherited.has(itemIndex));
            return {assignmentIndex,indices,items:indices.map(itemIndex=>items[itemIndex])};
          }).filter(item=>item.indices.length):assignments.map((assigned,assignmentIndex)=>({assignmentIndex,items:assigned}));
          requireValue(Array.isArray(dispatched)&&dispatched.length===activeAssignments.length&&new Set(dispatched).size===activeAssignments.length,'SUBAGENT_POOL_RECEIPT','Completion requires the exact Host-persisted active sub-Agent dispatch plan');
          const expectedPlan={resolved_count:activeAssignments.length,input_sha256:digest(canonicalJSON(items)),assignments:activeAssignments.map((item,index)=>({
            ...(perItem?{assignment_index:item.assignmentIndex}:{}),dispatch_id:dispatched[index],items_sha256:digest(canonicalJSON(item.items))}))};
          requireValue(canonicalJSON(persistedPlan)===canonicalJSON(expectedPlan),'SUBAGENT_POOL_RECEIPT','Persisted sub-Agent assignments differ from the current pinned runtime inputs');
          requireValue(proof&&proof.resolved_count===activeAssignments.length&&Array.isArray(proof.dispatch_ids)&&canonicalJSON(proof.dispatch_ids)===canonicalJSON(dispatched),'SUBAGENT_POOL_EVIDENCE','Completion pool identities must exactly match the persisted Host dispatch plan');
          if(definition.fanout)requireValue(Array.isArray(joined)&&joined.length===(perItem?items.length:count),'SUBAGENT_FANOUT_RESULT',
            perItem?'Per-item completion must join exactly one result per runtime input item':'Fan-out completion must join exactly one result per resolved sub-Agent');
          if(perItem)requireValue(joined.every((value,itemIndex)=>{
            const accepted=attempt.native_item_results?.[itemIndex];
            return accepted&&canonicalJSON(accepted.result)===canonicalJSON(value);
          }),'NATIVE_ITEM_RESULT','Per-item completion must reproduce every journaled accepted item');
          requireValue(Array.isArray(trustedResults)&&trustedResults.length===activeAssignments.length&&trustedResults.every((item,index)=>
            item.dispatch_id===dispatched[index]&&item.result_index===index&&item.result_sha256===digest(canonicalJSON(perItem
              ?assignedFanoutIndices({count,items,assignments},definition.fanout,activeAssignments[index].assignmentIndex).map(itemIndex=>joined[itemIndex]):joined[index]))),
            'SUBAGENT_POOL_EVIDENCE','Completion needs one Host-persisted successful child result for every dispatch identity');
          requireValue(childEvidence.length===activeAssignments.length&&childEvidence.every((item,index)=>sameManagedNativeResultIdentity(item,trustedResults[index])),'SUBAGENT_POOL_EVIDENCE','Completion evidence must reproduce the exact Host-persisted child result identities, including thread and turn');
        }
      }
      const falseGuard=definition.completion_contract?.fail_on_false?.find(name=>payload.structured_output[name]===false);
      if ((definition.decision && payload.structured_output.decision === 'blocked') || falseGuard) {
        node.output = payload.structured_output;
        node.error = falseGuard
          ? {code:'WORKFLOW_VALIDATION_FALSE',message:`Node ${definition.id} returned false for required validation output ${falseGuard}`}
          : { code: 'WORKFLOW_NODE_BLOCKED', message: `Node ${definition.id} reported a blocked decision` };
        attempt.status = 'failed'; attempt.finished_at = new Date().toISOString(); attempt.completion_hash = fingerprint; attempt.completion = payload; attempt.error = node.error;
        setOutcome(state, graphInfo(pins.root.workflow), node_id, 'failed');
        if (state.status === 'failed') interruptActiveNodes(state, 'Another node failed without a recovery edge');
        else advanceRun(state, pins);
        touch(state); return;
      }
      if (node_id === pins.root.workflow.finalization.node_id) {
        const deterministicTool=definition.type==='tool'&&definition.executor?.kind==='tool';
        if(deterministicTool){
          const guards=definition.completion_contract?.fail_on_false??[];
          requireValue(guards.length>0&&guards.every(name=>payload.structured_output[name]===true),'FINAL_ACCEPTANCE_REQUIRED','Deterministic Host finalization requires every declared boolean completion guard to pass');
          requireValue(payload.acceptance===undefined,'FINAL_ACCEPTANCE_REQUIRED','Deterministic Host finalization cannot carry model acceptance');
        }else requireValue(definition.executor.kind === 'main' && attempt.owner === state.main_actor && payload.acceptance?.accepted === true, 'FINAL_ACCEPTANCE_REQUIRED', 'Agent finalization requires explicit main-agent acceptance');
        if(isAuthoringRunProvenance(pins.root.provenance)){
          const expected=authoringReviewIdentity({state,pins}),reviewIdentity={proposal_hash:attempt.result_proposal?.proposal_hash,source_revision:attempt.result_proposal?.source_revision,expand_attempt_id:attempt.result_proposal?.expand_attempt_id};
          requireValue(authority?.kind===AUTHORING_HUMAN_ACCEPTANCE && canonicalJSON(authority.review_identity)===canonicalJSON(expected),'AUTHORING_HUMAN_ACCEPTANCE_REQUIRED','Authoring finalization requires an authenticated human acceptance bound to the current proposal');
          requireValue(canonicalJSON(attempt.dispatch?.receipt?.authoring_review_context)===canonicalJSON(expected) && canonicalJSON(reviewIdentity)===canonicalJSON(expected),'AUTHORING_REVIEW_IDENTITY','Authoring reviewer dispatch and result must identify the same current proposal');
          attempt.human_acceptance=structuredClone(authority.receipt);
        }
      }
      node.output = payload.structured_output; node.error = null;
      if (attempt.loop_observation) attempt.loop_observation.after = await observeLoopItems(state, pins.root.workflow, node_id, nodeWorkspace(node_id, state, pins));
      attempt.status = 'succeeded'; attempt.finished_at = new Date().toISOString(); attempt.completion_hash = fingerprint; attempt.completion = payload;
      setOutcome(state, graphInfo(pins.root.workflow), node_id, 'succeeded');
      advanceRun(state, pins); touch(state);
    }, {}, { allowPaused: true });
    return { ...publicRun(result), idempotent: result.idempotent ?? false };
  }

  async acceptAuthoringFinal(runId,{node_id,attempt_id,lease_token,control_token}){
    const record=await this.runs.read(runId);authorize(record.state,control_token);
    requireValue(isAuthoringRunProvenance(record.pins.root.provenance) && node_id===record.pins.root.workflow.finalization.node_id,'AUTHORING_HUMAN_ACCEPTANCE_REQUIRED','Human authoring acceptance applies only to the exact authoring finalizer');
    const attempt=record.state.nodes[node_id]?.attempts.find(item=>item.id===attempt_id);
    const {expected,completion}=await validateAuthoringAcceptance(this,record,attempt);
    const receipt={...expected,review_result_sha256:attempt.result_proposal.sha256,accepted_at:new Date().toISOString()};
    if(attempt.completion_hash){
      requireValue(canonicalJSON({...attempt.human_acceptance,accepted_at:receipt.accepted_at})===canonicalJSON(receipt),'AUTHORING_HUMAN_ACCEPTANCE_REQUIRED','Completed authoring finalizer lacks the exact durable human acceptance receipt');
      return {...publicRun(record),idempotent:true};
    }
    return this.completeNode(runId,{node_id,attempt_id,lease_token,completion:{...completion,acceptance:{accepted:true}}},{kind:AUTHORING_HUMAN_ACCEPTANCE,review_identity:expected,receipt});
  }

  async completeHostMainResult(runId,args,{accepted}={}){
    const record=await this.runs.read(runId),definition=record.pins.root.workflow.nodes.find(item=>item.id===args.node_id);
    requireValue(definition?.executor?.kind==='main','HOST_MAIN_NODE','Host Main completion requires a logical Main node');
    const attempt=record.state.nodes[args.node_id]?.attempts.find(item=>item.id===args.attempt_id);
    requireValue(attempt?.result_proposal?.sha256,'HOST_MAIN_RESULT_REQUIRED','No Host Main result proposal is available');
    const completion=await this.runs.readExecutorResult(runId,args.attempt_id,attempt.result_proposal.sha256);
    const final=record.pins.root.workflow.finalization?.node_id===definition.id;
    if(final){
      requireValue(!isAuthoringRunProvenance(record.pins.root.provenance),'AUTHORING_HUMAN_ACCEPTANCE_REQUIRED','Authoring finalization requires the authenticated human acceptance route');
      requireValue(accepted===true || (accepted===undefined && completion.structured_output?.accepted===true),'FINAL_ACCEPTANCE_REQUIRED','Final logical Main completion requires explicit Main acceptance');
      completion.acceptance={accepted:true};
      if(definition.outputs_schema?.properties?.accepted)completion.structured_output.accepted=true;
    }else requireValue(accepted===undefined,'FINAL_ACCEPTANCE_REQUIRED','Non-final logical Main nodes do not accept a human finalization flag');
    return this.completeNode(runId,{...args,completion},{kind:HOST_MAIN_LIFECYCLE});
  }

  async failNode(runId, { node_id, attempt_id, lease_token, error }, onFenced = () => {}) {
    requireValue(error && typeof error.message === 'string' && error.message.length <= 20000, 'FAILURE_SCHEMA', 'Failure needs a bounded diagnostic message');
    const result = await this.transition(runId, 'fail', (state, pins) => {
      const { node, attempt } = attemptFor(state, node_id, attempt_id, lease_token);
      (this.fenceAttemptExecution ?? ((id, node, attempt) => this.executionAdmission?.fenceAttempt(id, node, attempt)))(runId, node_id, attempt_id);
      onFenced(runId, node_id, attempt_id);
      node.error = { code: typeof error.code === 'string' ? error.code : 'EXECUTOR_FAILED', message: error.message };
      attempt.status = 'failed'; attempt.finished_at = new Date().toISOString(); attempt.error = node.error;
      setOutcome(state, graphInfo(pins.root.workflow), node_id, 'failed');
      if (state.status === 'failed') interruptActiveNodes(state, 'Another node failed without a recovery edge');
      else advanceRun(state, pins);
      touch(state);
    }, {}, { allowPaused: true });
    return publicRun(result);
  }

  async retryNode(runId, { node_id, control_token, reconciliation }) {
    const result = await this.transition(runId, 'retry', async (state, pins) => {
      authorize(state, control_token);
      requireValue(!['cancelled', 'succeeded', 'paused'].includes(state.status), 'RUN_TERMINAL', 'Run cannot release a retry in its current state');
      const node = state.nodes[node_id]; const graph = graphInfo(pins.root.workflow); const definition = graph.nodes.get(node_id);
      requireValue(node && ['failed', 'interrupted', 'blocked'].includes(node.status), 'NODE_RETRY_STATE', 'Only a failed, interrupted or blocked node can be retried');
      // Native same-Agent correction turns are bounded while that attempt is
      // active. They must not also consume every explicit node-attempt slot:
      // otherwise a protocol/format failure permanently prevents a clean
      // retry after the Host or parser is repaired.
      requireValue((definition.executor?.kind === 'main' ? semanticTurnsConsumed(node) : currentRoundAttempts(node).length) < definition.retry.max_attempts,
        'RETRY_LIMIT', 'Node exhausted its pinned attempt limit');
      const previous = node.attempts.at(-1);
      if (previous?.child_run_id) {
        const child = await this.runs.read(previous.child_run_id);
        requireValue(TERMINAL.has(child.state.status), 'CHILD_RECONCILIATION_REQUIRED', 'The previous child Run must be terminal before a new attempt can start');
      }
      if (previous?.dispatch) {
        requireValue(reconciliation?.attempt_id === previous.id && reconciliation.dispatch_request_id === previous.dispatch.request_id && ['not_started', 'terminated', 'explicit_retry'].includes(reconciliation.outcome) && Array.isArray(reconciliation.evidence) && reconciliation.evidence.length, 'DISPATCH_RECONCILIATION_REQUIRED', 'Uncertain external work must be reconciled or explicitly retried with evidence');
        if (definition.executor?.kind === 'thread') requireValue(['not_started', 'terminated'].includes(reconciliation.outcome), 'THREAD_RECONCILIATION_REQUIRED', 'A task turn must be observed not started or terminated before retry; explicit retry cannot release a shared task lane');
        previous.reconciliation = structuredClone(reconciliation);
      }
      if (previous?.host_tool && (!previous.host_tool.receipt || previous.host_tool.receipt.status === 'timed_out')) {
        requireValue(reconciliation?.attempt_id === previous.id && reconciliation.host_tool === previous.host_tool.tool && Array.isArray(reconciliation.evidence) && reconciliation.evidence.length, 'HOST_TOOL_RECONCILIATION_REQUIRED', 'A host tool with no durable receipt must be reconciled before retry');
        requireValue(previous.host_tool.idempotency === 'safe' && reconciliation.outcome === 'safe_replay' || ['reconcile_required', 'non_idempotent'].includes(previous.host_tool.idempotency) && reconciliation.outcome === 'not_started', 'HOST_TOOL_RECONCILIATION_REQUIRED', 'Only the pinned host-tool idempotency mode may release a retry');
        previous.host_tool.reconciliation = structuredClone(reconciliation);
      }
      for (const descendant of graph.visit(node_id)) {
        if (descendant === node_id) continue;
        requireValue(!['claimed', 'running', 'succeeded'].includes(state.nodes[descendant].status), 'RETRY_DOWNSTREAM_STARTED', 'Cannot replay an ancestor after downstream execution started');
        state.nodes[descendant].status = 'pending'; state.nodes[descendant].approval_id = null;
        for (const edge of graph.out.get(descendant)) state.edges[edge.id] = 'pending';
      }
      node.status = 'pending'; node.output = null; node.error = null; node.failure_handled = false; node.approval_id = null; node.active_attempt_id = null;
      for (const edge of graph.out.get(node_id)) state.edges[edge.id] = 'pending';
      state.status = 'running'; state.error = null; advanceRun(state, pins); touch(state);
    });
    return publicRun(result);
  }

  async approve(runId, { approval_id, decision, control_token }) {
    requireValue(typeof decision === 'boolean', 'APPROVAL_DECISION', 'Approval decision must be boolean');
    const result = await this.transition(runId, 'approve', (state, pins) => {
      authorize(state, control_token); requireValue(!TERMINAL.has(state.status), 'RUN_TERMINAL', 'Terminal Run approvals cannot change');
      const approval = Object.hasOwn(state.approvals, approval_id) ? state.approvals[approval_id] : undefined;
      requireValue(approval, 'APPROVAL_MISSING', 'Approval request does not exist');
      if (approval.status !== 'pending') { requireValue(approval.decision === decision, 'APPROVAL_CONFLICT', 'Approval already has a different decision'); return; }
      approval.decision = decision; approval.status = decision ? 'approved' : 'denied';
      const node = state.nodes[approval.node_id]; const definition = pins.root.workflow.nodes.find(item => item.id === approval.node_id);
      requireValue(approval.binding_hash === approvalBinding(definition, state, pins).hash, 'APPROVAL_BINDING_CHANGED', 'Approval scope changed');
      if (decision) {
        if (state.status === 'blocked') state.status = 'running';
        if (definition.type === 'human_gate') { node.output = structuredClone(HUMAN_GATE_OUTPUT); setOutcome(state, graphInfo(pins.root.workflow), approval.node_id, 'succeeded'); }
        else node.status = 'pending';
        advanceRun(state, pins);
      }
      touch(state);
    });
    return publicRun(result);
  }

  async pause(runId, { control_token, reason = 'Paused by main controller' }) {
    const result = await this.runs.mutate(runId, 'pause', state => {
      authorize(state, control_token); requireValue(!TERMINAL.has(state.status), 'RUN_TERMINAL', 'Terminal Run cannot pause');
      state.status = 'paused'; state.pause_reason = String(reason).slice(0, 2000); touch(state);
    });
    return publicRun(result);
  }

  async resume(runId, { control_token, after_restart = false }) {
    if (after_restart) {
      const result = await this.runs.recover(runId, state => {
        authorize(state, control_token);
        if (!TERMINAL.has(state.status)) { interruptActiveNodes(state, 'Executor ownership must be reconciled after restart'); state.status = 'interrupted'; touch(state); }
      }, state => authorize(state, control_token));
      return publicRun(result);
    }
    const result = await this.transition(runId, 'resume', (state, pins) => {
      authorize(state, control_token);
      requireValue(['paused', 'blocked', 'interrupted'].includes(state.status), 'RUN_RESUME_STATE', 'Run is not paused, blocked or interrupted');
      requireValue(!state.control_recovery?.errors?.length, 'CONTROL_RECOVERY_INCOMPLETE', 'Resolve the recorded recovery/cleanup errors before resuming');
      requireValue(!Object.values(state.nodes).some(node => node.status === 'interrupted'), 'INTERRUPTED_NODES', 'Interrupted nodes require explicit reconciliation/retry');
      state.status = 'running'; state.pause_reason = null; advanceRun(state, pins); touch(state);
    });
    return publicRun(result);
  }

  async cancel(runId, { control_token }, onFenced = () => {}) {
    const result = await this.runs.mutate(runId, 'cancel', state => {
      authorize(state, control_token);
      requireValue(state.status !== 'succeeded', 'RUN_TERMINAL', 'Completed Run cannot be cancelled');
      (this.fenceRunExecution ?? (id => this.executionAdmission?.fenceRun(id)))(runId);
      onFenced(runId, control_token);
      if (state.status === 'cancelled') return;
      state.status = 'cancelled';
      for (const node of Object.values(state.nodes)) if (!['succeeded', 'failed', 'skipped'].includes(node.status)) {
        node.status = 'cancelled';
        const attempt = node.attempts.find(item => item.id === node.active_attempt_id);
        if (attempt) { attempt.status = 'cancelled'; if (attempt.dispatch) attempt.dispatch.cancellation_pending = true; }
      }
      for (const id of Object.keys(state.edges)) if (state.edges[id] === 'pending') state.edges[id] = 'skipped';
      touch(state);
    });
    return publicRun(result);
  }

  async recordDispatchIntent(runId, { node_id, attempt_id, lease_token, request_id, envelope_hash, control_token }, authority = null) {
    requireValue(typeof request_id === 'string' && request_id && request_id.length <= 128 && /^[a-f0-9]{64}$/.test(envelope_hash), 'DISPATCH_INTENT', 'Dispatch requires a stable request ID and envelope fingerprint');
    const result = await this.transition(runId, 'dispatch_intent', async (state, pins) => {
      authorize(state, control_token); const { attempt } = attemptFor(state, node_id, attempt_id, lease_token);
      const definition = pins.root.workflow.nodes.find(item => item.id === node_id);
      if (attempt.dispatch) { requireValue(attempt.dispatch.request_id === request_id && attempt.dispatch.envelope_hash === envelope_hash, 'DISPATCH_CONFLICT', 'Attempt already has a different dispatch intent'); return; }
      requireValue(state.status === 'running', 'RUN_NOT_RUNNING', 'Paused or terminal Runs cannot dispatch new external work');
      if(definition?.executor?.kind==='main')requireValue(authority===HOST_MAIN_LIFECYCLE,'HOST_MAIN_LIFECYCLE_REQUIRED','Logical Main dispatch belongs to the Host execution lane');
      await revalidateBoundSourceLocations(definition, state, pins);
      if (['main', 'provider', 'thread'].includes(definition?.executor?.kind)) {
        const maximum = definition.cost?.maximum_micros ?? definition.decision?.budget?.maximum_micros ?? null;
        if (state.constraints.require_usage_ledger === true) requireValue(maximum !== null, 'COST_RESERVATION_REQUIRED', 'Plan 1 usage accounting requires each semantic call to declare a worst-case cost');
        reserveCost(state.cost_ledger, { call_id: request_id, node_id, attempt_id, maximum_micros: maximum });
      }
      assertThreadDispatchAvailable(state, pins, node_id, attempt_id);
      attempt.dispatch = { request_id, envelope_hash, phase: 'intent', receipt: null, cancellation_pending: false }; touch(state);
    });
    return { ...publicRun(result), idempotent: result.idempotent ?? false };
  }

  recordHostMainDispatchIntent(runId,args){return this.recordDispatchIntent(runId,args,HOST_MAIN_LIFECYCLE);}

  async recordDispatchReceipt(runId, { node_id, attempt_id, lease_token, request_id, receipt, control_token }, authority = null) {
    const serialized = canonicalJSON(receipt);
    requireValue(receipt && typeof receipt === 'object' && !Array.isArray(receipt) && Buffer.byteLength(serialized) <= 16000 && !/"[^"\n]*(?:password|cookie|authorization|api_key|access_token|refresh_token)[^"\n]*"\s*:/i.test(serialized), 'DISPATCH_RECEIPT', 'Receipt must contain bounded task identity metadata without credentials');
    requireValue(['task_id', 'thread_id', 'agent_id', 'invocation_id', 'main_actor', 'tool_call_id'].some(key => typeof receipt[key] === 'string' && receipt[key].length > 0 && receipt[key].length <= 256), 'DISPATCH_IDENTITY_REQUIRED', 'Receipt requires a concrete task, agent, invocation or tool-call identity');
    const result = await this.runs.mutate(runId, 'dispatch_receipt', (state, pins) => {
      authorize(state, control_token); const { node, attempt } = attemptFor(state, node_id, attempt_id, lease_token, { active: false });
      requireValue(attempt.dispatch?.request_id === request_id, 'DISPATCH_INTENT_MISSING', 'Receipt does not match a persisted dispatch intent');
      if (attempt.dispatch.receipt) { requireValue(canonicalJSON(attempt.dispatch.receipt) === serialized, 'DISPATCH_CONFLICT', 'Receipt differs from the exact previously recorded task'); return; }
      const definition = pins.root.workflow.nodes.find(item => item.id === node_id);
      if(definition?.executor?.kind==='main')requireValue(authority===HOST_MAIN_LIFECYCLE,'HOST_MAIN_LIFECYCLE_REQUIRED','Logical Main receipts belong to the Host execution lane');
      if(definition?.subagent_count!==undefined){
        const {count,items,assignments}=resolvedSubagentPlan(definition,state);
        if(count>1||definition.fanout){
          const perItem=definition.fanout?.result_mode==='per_item',inherited=new Set(attempt.inherited_native_item_indices??[]);
          const activeAssignments=perItem?assignments.map((_assigned,assignmentIndex)=>{
            const indices=assignedFanoutIndices({count,items,assignments},definition.fanout,assignmentIndex).filter(itemIndex=>!inherited.has(itemIndex));
            return {assignmentIndex,items:indices.map(itemIndex=>items[itemIndex])};
          }).filter(item=>item.items.length):assignments.map((assigned,assignmentIndex)=>({assignmentIndex,items:assigned}));
          const ids=receipt.subagent_dispatch_ids;requireValue(Array.isArray(ids)&&ids.length===activeAssignments.length&&ids.every(id=>typeof id==='string'&&id.length>0&&id.length<=256)&&new Set(ids).size===activeAssignments.length,'SUBAGENT_POOL_RECEIPT','Dispatch receipt must persist one unique Host-assigned identity per active sub-Agent');
          const expectedPlan={resolved_count:activeAssignments.length,input_sha256:digest(canonicalJSON(items)),assignments:activeAssignments.map((item,index)=>({
            ...(perItem?{assignment_index:item.assignmentIndex}:{}),dispatch_id:ids[index],items_sha256:digest(canonicalJSON(item.items))}))};
          requireValue(canonicalJSON(receipt.subagent_plan)===canonicalJSON(expectedPlan),'SUBAGENT_POOL_RECEIPT','Dispatch receipt must persist the exact Host-resolved fan-out assignments');
        }
      }
      if(isAuthoringRunProvenance(pins.root.provenance) && node_id===pins.root.workflow.finalization.node_id){
        const expected=authoringReviewIdentity({state,pins});
        requireValue(canonicalJSON(receipt.authoring_review_context)===canonicalJSON(expected),'AUTHORING_REVIEW_IDENTITY','Reviewer dispatch receipt must bind the current proposal hash, source revision and planner attempt');
      }
      if (definition?.executor?.kind === 'main' && (state.constraints.require_main_session_identity === true || state.cost_ledger.budget || state.constraints.require_usage_ledger === true)) {
        const identity = mainSessionIdentity(receipt, state.main_actor);
        if (state.main_session_identity) requireValue(sameMainSession(state.main_session_identity, identity), 'MAIN_SESSION_CHANGED', 'Main semantic work cannot implicitly start a new session or call chain');
        else state.main_session_identity = identity;
      }
      if (definition?.executor?.kind === 'thread') {
        assertThreadReceipt(state, definition.executor, receipt);
        assertThreadStartIdentity(state, definition, attempt_id, receipt);
      }
      attempt.dispatch.receipt = structuredClone(receipt); attempt.dispatch.phase = 'acknowledged';
      if (node.active_attempt_id === attempt_id && node.status === 'claimed') { node.status = 'running'; attempt.status = 'running'; }
      else attempt.dispatch.cancellation_pending = true;
      touch(state);
    });
    return publicRun(result);
  }

  recordHostMainDispatchReceipt(runId,args){return this.recordDispatchReceipt(runId,args,HOST_MAIN_LIFECYCLE);}

  async recordUsage(runId, { node_id, attempt_id, lease_token, request_id, usage, control_token }, authority = null) {
    const result = await this.transition(runId, 'usage', (state,pins) => {
      authorize(state, control_token); const { attempt } = attemptFor(state, node_id, attempt_id, lease_token, { active: false });
      const definition=pins.root.workflow.nodes.find(item=>item.id===node_id);
      if(definition?.executor?.kind==='main')requireValue(authority===HOST_MAIN_LIFECYCLE,'HOST_MAIN_LIFECYCLE_REQUIRED','Logical Main usage belongs to the Host execution lane');
      requireValue(attempt.dispatch?.request_id === request_id, 'USAGE_CALL_MISSING', 'Usage must attach to an exact dispatched model call');
      commitUsage(state.cost_ledger, request_id, usage); touch(state);
    });
    return publicRun(result);
  }

  recordHostMainUsage(runId,args){return this.recordUsage(runId,args,HOST_MAIN_LIFECYCLE);}

  async recordHostToolIntent(runId, { node_id, attempt_id, lease_token, control_token, contract, input }) {
    const result = await this.transition(runId, 'host_tool_intent', async (state, pins) => {
      authorize(state, control_token); const { attempt } = attemptFor(state, node_id, attempt_id, lease_token);
      requireValue(state.status === 'running', 'RUN_NOT_RUNNING', 'A stopped Run cannot start a host tool');
      const definition = pins.root.workflow.nodes.find(item => item.id === node_id);
      requireValue(definition?.type === 'tool' && definition.executor?.kind === 'tool', 'HOST_TOOL_NODE', 'Only a pinned tool node may execute a host tool');
      const expected = hostToolContracts(pins.root.workflow).get(definition.executor.tool);
      requireValue(expected && canonicalJSON(expected) === canonicalJSON(contract), 'HOST_TOOL_CONTRACT', 'Host execution differs from the pinned tool contract');
      const inputHash = digest(canonicalJSON(input));
      if (attempt.host_tool) {
        requireValue(attempt.host_tool.contract_sha256 === digest(canonicalJSON(contract)) && attempt.host_tool.input_sha256 === inputHash, 'HOST_TOOL_CONFLICT', 'Host tool attempt has different pinned input or contract'); return structuredClone(attempt.host_tool);
      }
      await revalidateBoundSourceLocations(definition, state, pins);
      attempt.host_tool = { run_id: runId, node_id, attempt_id, tool: contract.id, contract_sha256: digest(canonicalJSON(contract)), input_sha256: inputHash,
        input_summary: { keys: Object.keys(input ?? {}).sort(), bytes: Buffer.byteLength(canonicalJSON(input)) }, phase: 'intent', receipt: null, idempotency: contract.idempotency.mode }; touch(state);
      return structuredClone(attempt.host_tool);
    });
    return { receipt: result.result, idempotent: result.idempotent ?? false, sequence: result.sequence };
  }

  async recordHostToolReceipt(runId, { node_id, attempt_id, lease_token, control_token, receipt }) {
    validateHostToolReceipt(receipt);
    const result = await this.transition(runId, 'host_tool_receipt', async state => {
      // Run cancellation fences completion but must still durably journal the
      // qualified broker's exact termination receipt for the owned attempt.
      authorize(state, control_token); const { attempt } = attemptFor(state, node_id, attempt_id, lease_token, { active: false });
      const host = attempt.host_tool; requireValue(host, 'HOST_TOOL_INTENT_MISSING', 'Host receipt needs an exact prior intent');
      requireValue(receipt.run_id === runId && receipt.node_id === node_id && receipt.attempt_id === attempt_id && receipt.tool === host.tool && receipt.contract_sha256 === host.contract_sha256 && receipt.input_sha256 === host.input_sha256, 'HOST_TOOL_RECEIPT', 'Host receipt differs from the exact Run/node/attempt/tool/input intent');
      requireValue(Number.isFinite(Date.parse(receipt.started_at)) && Number.isFinite(Date.parse(receipt.finished_at)) && Date.parse(receipt.finished_at) >= Date.parse(receipt.started_at) && receipt.duration_ms >= 0, 'HOST_TOOL_RECEIPT', 'Host receipt timestamps are inconsistent');
      // Reject conflicting replay before reading its artifact. Exact replay
      // still verifies durable output integrity before leaving state unchanged.
      if (host.receipt) requireValue(canonicalJSON(host.receipt) === canonicalJSON(receipt), 'HOST_TOOL_CONFLICT', 'Host tool receipt differs from the prior exact receipt');
      else requireValue(host.phase === 'intent', 'HOST_TOOL_INTENT_MISSING', 'Host receipt needs an exact prior intent');
      if (receipt.status === 'succeeded') {
        requireValue(receipt.output_ref.artifact === `executor-${attempt_id}-${receipt.output_ref.sha256}.json`, 'HOST_TOOL_RECEIPT', 'Host output reference must use the exact executor-result artifact identity');
        const stored = await this.runs.readExecutorResult(runId, attempt_id, receipt.output_ref.sha256);
        requireValue(stored?.kind === 'host_tool_output' && digest(canonicalJSON(stored.output)) === receipt.output_sha256, 'HOST_TOOL_OUTPUT_CORRUPT', 'Durable host output differs from its receipt digest');
      }
      if (host.receipt) return;
      host.receipt = structuredClone(receipt); host.phase = 'received'; touch(state);
    });
    return publicRun(result);
  }

  async events(runId, { after_sequence = 0, control_token }) {
    return this.#eventsFromRecord(await this.runs.read(runId), { after_sequence, control_token });
  }

  #eventsFromRecord(record, { after_sequence = 0, control_token }) {
    authorize(record.state, control_token);
    requireValue(Number.isInteger(after_sequence) && after_sequence >= 0, 'EVENT_CURSOR', 'Event cursor must be a nonnegative sequence');
    return record.events.filter(event => event.sequence > after_sequence).map(event => ({ sequence: event.sequence, kind: event.kind, at: event.at, hash: event.hash, node_ids: Object.keys(event.payload.patch?.nodes ?? {}), run_status: event.payload.patch?.fields.status ?? event.payload.state?.status ?? null }));
  }
}
