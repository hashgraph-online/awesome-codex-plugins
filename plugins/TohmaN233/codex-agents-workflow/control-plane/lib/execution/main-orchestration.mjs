import {readPinnedObject} from '../pinned-object-reader.mjs';
import { join,relative } from 'node:path';
import { requireValue } from '../workflow-paths.mjs';
import { canonicalJSON, digest } from '../workflow-revisions.mjs';
import { validateData } from '../workflow-data-schema.mjs';
import { leaseToken, bindingContext } from '../workflow-execution-envelope.mjs';
import { isOrchestrationMain } from './main-execution-mode.mjs';
import { semanticResultSchema, hostResultProposalEnvelope } from './host-main-automation.mjs';
import { materializeMainTaskBundle, readMainTaskProjection,readTerminalMainInputs,projectTerminalMainInputBindings,TERMINAL_MAIN_INPUT_BUDGET,MAIN_TASK_CURRENT_INLINE_LIMIT,MAIN_TASK_INLINE_LIMIT } from './node-input-materials.mjs';
import { snapshotWorkspace, changedWorkspacePaths } from './workspace-snapshot.mjs';
import { semanticTurnsConsumed } from './completion-turn-budget.mjs';
import { preflightSemanticOutput } from './completion-preflight.mjs';
import { rejectWorkspaceScope } from './workspace-scope-evidence.mjs';
import { hostToolContracts } from './host-tool-runner.mjs';
import { hostCompletionInputs, preflightHostCompletionInputs } from './main-host-check.mjs';
import {foregroundPriorityPreparation,retainForegroundPriority} from '../foreground-activity.mjs';
import {sharedHostRegion,sharedHostProjection,verifySharedHostProjection,requireSharedHostProjectionSnapshot} from './shared-host-work.mjs';
import {bindingPointers} from '../workflow-bindings.mjs';

export function terminalMainInputStage(graph,nodeId){
  const outgoing=graph.edges.filter(edge=>edge.source===nodeId);
  if(!outgoing.length)return false;
  if(graph.finalization?.node_id===nodeId)return outgoing.every(edge=>graph.nodes.find(node=>node.id===edge.target)?.type==='end');
  // A deterministic final recorder does not introduce another semantic stage.
  // Keep the existing bounded carrier when that exact finalizer consumes this
  // Main result and leads only to end; workers or intermediate tools do not qualify.
  const finalizer=graph.nodes.find(node=>node.id===graph.finalization?.node_id);
  if(finalizer?.type!=='tool'||finalizer.executor?.kind!=='tool'
    ||!outgoing.every(edge=>edge.target===finalizer.id&&(edge.on??'success')==='success'))return false;
  const terminal=graph.edges.filter(edge=>edge.source===finalizer.id);
  const result=`/nodes/${nodeId}/output`;
  return terminal.length>0&&terminal.every(edge=>graph.nodes.find(node=>node.id===edge.target)?.type==='end')
    &&Object.values(finalizer.input_bindings??{}).some(binding=>bindingPointers(binding).some(path=>path===result||path.startsWith(result+'/')));
}

const within = (path, boundary) => {
  const normalize = value => process.platform === 'win32' ? value.toLowerCase() : value;
  path = normalize(path); boundary = normalize(boundary.replace(/\/$/, ''));
  return boundary === '.' || path === boundary || path.startsWith(boundary + '/');
};

async function activeOrchestration(runtime, runId, controlToken, threadId, expectedOrchestration) {
  const { record, binding, envelope } = await runtime.authorizedHostMainPlanning(runId, { control_token: controlToken }, record => {
    requireValue(record.state.status === 'running' && record.state.constraints?.native_parent_thread_id === threadId,
      'MAIN_ORCHESTRATION_CONTEXT', 'Orchestration runs in the exact initiating conversation');
    const active = record.pins.root.workflow.nodes.filter(definition => isOrchestrationMain(definition)
      && ['claimed', 'running'].includes(record.state.nodes[definition.id]?.status));
    requireValue(active.length === 1, 'MAIN_ORCHESTRATION_NODE', 'No unique active orchestration node is awaiting this conversation');
    const definition = active[0], node = record.state.nodes[definition.id];
    const attempt = node.attempts.find(item => item.id === node.active_attempt_id);
    requireValue(attempt, 'ATTEMPT_MISSING', 'The active orchestration node lost its exact attempt');
    requireValue(!expectedOrchestration || definition.id===expectedOrchestration.node_id && attempt.id===expectedOrchestration.attempt_id,
      'WORKFLOW_STARTUP_IDENTITY', 'The initial semantic result cannot complete another node or attempt');
    return { node_id: definition.id, attempt_id: attempt.id,
      lease_token: leaseToken(controlToken, runId, definition.id, attempt.id, attempt.lease_generation ?? 0) };
  });
  const definition = record.pins.root.workflow.nodes.find(node => node.id === binding.node_id);
  const attempt = record.state.nodes[binding.node_id].attempts.find(item => item.id === binding.attempt_id);
  const event = (kind, metadata) => runtime.recordExecutorEvent(runId, { ...binding, event: { kind, metadata } });
  const contentPaths=(sharedHostProjection(record.state,record.pins.root.workflow,definition.id)?.sources??[])
    .map(source=>relative(envelope.workspace,source.path).replaceAll('\\','/'));
  const snapshot = (hashPaths=contentPaths) => snapshotWorkspace(envelope.workspace, { access: envelope.access,hashPaths,
    allowedPaths: envelope.effective_allowed_paths, requiredPaths: (definition.required_artifacts ?? []).map(item => item.path),
    onUnreadable: metadata => event('workspace_unreadable_authorized_path', { ...metadata, phase: 'orchestration' }) });
  return { record, definition, attempt, binding, envelope, event, snapshot };
}

/** The Host owns mechanics; the foreground Agent keeps its existing conversation. */
export async function prepareMainOrchestration(runtime, { run_id, control_token, thread_id }) {
  const preparation=foregroundPriorityPreparation(runtime.runs.root,run_id);
  const { record, definition, attempt, binding, envelope, snapshot,event } = await activeOrchestration(runtime, run_id, control_token, thread_id);
  preflightHostCompletionInputs(definition,bindingContext(record.state),envelope.inputs,hostToolContracts(record.pins.root.workflow));
  const schema = semanticResultSchema(definition);
  let receipt = attempt.dispatch?.receipt;
  if (!receipt) {
    const projection=sharedHostProjection(record.state,record.pins.root.workflow,definition.id);
    if(projection)try{await verifySharedHostProjection(projection);}
    catch(error){
      try{await event('completion_invalid',{diagnostic:`Immutable source preparation failed: ${String(error.message)}`.slice(0,900),thread_id});}
      catch(auditError){throw Object.assign(new AggregateError([error,auditError],'Immutable source preparation failed and its exact diagnostic could not be committed'),{code:'SHARED_HOST_PROJECTION_AUDIT_FAILED'});}
      throw error;
    }
    const resources = [];
    for (const path of envelope.resources ?? []) {
      const pin = record.pins.root.resources.find(item => item.path === path);
      requireValue(pin, 'MAIN_ORCHESTRATION_RESOURCE', `Missing pinned resource: ${path}`);
      resources.push({ path, sha256: pin.sha256, size: pin.bytes, bytes: await readPinnedObject(join(runtime.runs.directory(run_id),'objects'),pin) });
    }
    const bundle = await materializeMainTaskBundle({ directory: join(envelope.workspace, 'work', '.workflow-runtime', 'orchestration', run_id, attempt.id),
      envelope, resources });
    const before = await snapshot();
    if(projection)requireSharedHostProjectionSnapshot(projection,before);
    const reference = await runtime.runs.saveArtifact(run_id, `orchestration-before-${attempt.id}`,
      Buffer.from(canonicalJSON({ files: [...before], unreadable: [...before.unreadablePaths],hash_paths:before.hashPaths })));
    receipt = { executor: 'codex-current-main-orchestration', thread_id, main_actor: record.state.main_actor,
      session_id: `logical-main-${run_id}`, call_chain_id: `workflow-run-${run_id}`,
      task_bundle_path: bundle.task_bundle_path, task_bundle_sha256: bundle.task_bundle_sha256,
      task_inline_limit: MAIN_TASK_CURRENT_INLINE_LIMIT, before_snapshot: reference };
    if(projection)receipt.source_projection={region_id:projection.region_id,tool_attempt_id:projection.tool_attempt_id,
      sources:projection.sources.map(({input,sha256,bytes})=>({input,sha256,bytes}))};
    await runtime.recordHostMainDispatchReceipt(run_id, { ...binding, request_id: `dispatch-${attempt.id}`, receipt });
  }
  requireValue(receipt.executor === 'codex-current-main-orchestration' && receipt.thread_id === thread_id,
    'MAIN_ORCHESTRATION_IDENTITY', 'The orchestration receipt belongs to another execution mode or conversation');
  const { inline, ...publicTask } = await readMainTaskProjection(receipt,
    { materialize: true, artifactStore: runtime.runs, runId: run_id, attemptId: attempt.id });
  const handoff = { status: 'orchestration_handoff', main_mode: 'orchestration', context: 'current_conversation',
    workspace: envelope.workspace, access: envelope.access, allowed_paths: envelope.effective_allowed_paths,
    ...publicTask, response_schema: schema,
    task_delivery: inline ? 'inline' : 'file',
    completion_tool: 'workflow_orchestration_complete',
    instruction: (inline ? 'Execute this node in the current conversation using the supplied task_bundle; do not reread its index file. Read only needed materialized sidecars at their exact addresses.'
      : `Execute this node in the current conversation using its existing task context and the local task bundle; task_delivery=file because its index exceeds the ${receipt.task_inline_limit??MAIN_TASK_INLINE_LIMIT}-byte inline limit.`)
      + ' Submit only newly authored semantic output to workflow_orchestration_complete.' };
  const repairLoop=record.pins.root.workflow.loops?.find(loop=>loop.review_context==='current_main'&&loop.exit_node===definition.id);
  if(repairLoop)handoff.rejection_route={kind:'loop_feedback',loop_id:repairLoop.id,round:record.state.loops[repairLoop.id].round,
    instruction:'When rejected, return accepted=false with concrete correction feedback. The Host sends it to the declared producer and refreshes the product before your next review.'};
  const graph=record.pins.root.workflow;
  const terminalSemantic=terminalMainInputStage(graph,definition.id);
  if(terminalSemantic){
    const carrier=await readTerminalMainInputs(receipt);
    const task=carrier.semantic_inputs&&publicTask.task_bundle?await projectTerminalMainInputBindings(receipt,publicTask,carrier):publicTask;
    if((!carrier.semantic_inputs||publicTask.task_bundle)&&Buffer.byteLength(canonicalJSON({...handoff,...task,...carrier}))<=TERMINAL_MAIN_INPUT_BUDGET.reply_bytes)Object.assign(handoff,task,carrier);
    else if(carrier.semantic_inputs){
      // No truncation: the original receipt-bound public task/file addresses
      // remain usable when the complete reply would exceed its fixed budget.
      handoff.semantic_input_delivery='file';
    }
  }
  runtime.executionAdmission?.assertAttemptActive(run_id,definition.id,attempt.id);
  retainForegroundPriority(runtime.runs.root,{run_id,node_id:definition.id,attempt_id:attempt.id,
    lease_generation:attempt.lease_generation??0,controller_binding_hash:runtime.mainForegroundControllerBinding(record.state)},preparation);
  return handoff;
}

export async function completeMainOrchestration(runtime, { run_id, control_token, thread_id, output }, { executor,signal,expectedOrchestration } = {}) {
  signal?.throwIfAborted();
  const { record, definition, attempt, binding, envelope, event, snapshot,turn_reserved } = await runtime.runs.withHostTransaction(run_id,'main_prepare',async()=>{
    const current=await activeOrchestration(runtime, run_id, control_token, thread_id, expectedOrchestration);
    const checked=current.definition.completion_contract?.host_check&&current.attempt.host_tool;
    const receipt=current.attempt.dispatch?.receipt;
    requireValue(receipt?.executor==='codex-current-main-orchestration'&&receipt.thread_id===thread_id,
      'MAIN_ORCHESTRATION_IDENTITY','This conversation has no dispatched orchestration task');
    await readMainTaskProjection(receipt,{artifactStore:runtime.runs,runId:run_id,attemptId:current.attempt.id});
    if(!checked)await runtime.reserveHostMainTurn(run_id,current.binding);
    return {...current,turn_reserved:!checked};
  });
  signal?.throwIfAborted();
  const receipt = attempt.dispatch?.receipt;
  requireValue(receipt?.executor === 'codex-current-main-orchestration' && receipt.thread_id === thread_id,
    'MAIN_ORCHESTRATION_IDENTITY', 'This conversation has no dispatched orchestration task');
  let semanticRejected = false;
  try {
    const checked = definition.completion_contract?.host_check && attempt.host_tool;
    if (checked) requireValue(checked.input_sha256 === digest(canonicalJSON({ inputs: hostCompletionInputs(definition,bindingContext(record.state),envelope.inputs), output })),
      'HOST_TOOL_CONFLICT', 'Completion check is pinned to a different semantic output');
    if(!turn_reserved&&checked?.receipt?.status!=='succeeded')await runtime.reserveHostMainTurn(run_id,binding);
    // A successful check awaiting semantic commit is reconciliation of the same
    // response, not a new semantic turn. Its receipt must never spend another
    // model attempt or permit a changed response to reset mechanical effects.
    validateData(output, semanticResultSchema(definition));
    if(sharedHostProjection(record.state,record.pins.root.workflow,definition.id)
      &&sharedHostRegion(record.pins.root.workflow,definition.id).workspace_policy.semantic_rejection!=='defer_to_join'){
      semanticRejected=output.accepted===false;
      requireValue(output.accepted===true,'NODE_SUCCESS_REQUIRED','The current Main rejected the immutable source review');
    }
    await preflightSemanticOutput(definition, output, envelope.workspace, record);
    if (record.pins.root.workflow.finalization?.node_id === definition.id && Object.hasOwn(definition.outputs_schema?.properties ?? {}, 'accepted')) {
      semanticRejected = output.accepted === false;
      requireValue(output.accepted === true, 'FINAL_ACCEPTANCE_REQUIRED', 'The current Main did not accept the final result');
    }
    for (const field of definition.completion_contract?.host_check ? definition.completion_contract.fail_on_false ?? [] : []) {
      semanticRejected = output[field] === false;
      requireValue(output[field] === true, 'NODE_SUCCESS_REQUIRED', `The current Main rejected the declared success field: ${field}`);
    }
    const savedBefore = JSON.parse((await runtime.runs.readArtifact(run_id, receipt.before_snapshot)).toString('utf8'));
    const before = new Map(savedBefore.files); before.unreadablePaths = new Map(savedBefore.unreadable);
    const auditScope = async () => {
      const after = await snapshot(savedBefore.hash_paths??null), changed = changedWorkspacePaths(before, after);
      const outside = envelope.access === 'read_only' ? changed : changed.filter(path => !envelope.effective_allowed_paths.some(boundary => within(path, boundary)));
      if (outside.length) await rejectWorkspaceScope({ runtime, runId: run_id, attemptId: attempt.id,
        code: 'MAIN_ORCHESTRATION_SCOPE_VIOLATION', changed, outside, before, after, event });
      return { after, changed };
    };
    let check = null;
    if (definition.completion_contract?.host_check) {
      await auditScope();
      requireValue(executor && typeof executor.executeHostTool === 'function', 'MAIN_ORCHESTRATION_HOST_CHECK_UNAVAILABLE', 'Completion requires its existing qualified Host executor');
      requireValue(hostToolContracts(record.pins.root.workflow).has(definition.completion_contract.host_check.tool),
        'HOST_TOOL_CONTRACT', 'Completion requires an exact pinned Host check');
      check = await executor.executeHostTool(run_id, binding, { completionOutput: output,assertActive:()=>signal?.throwIfAborted() });
    }
    signal?.throwIfAborted();
    const { after, changed } = await auditScope();
    const pathKey = value => process.platform === 'win32' ? value.toLowerCase() : value;
    const changedKeys = new Set(changed.map(pathKey)), afterKeys = new Set([...after.keys()].map(pathKey));
    const missing = (definition.required_artifacts ?? []).filter(item => !changedKeys.has(pathKey(item.path)) || !afterKeys.has(pathKey(item.path)));
    requireValue(!missing.length, 'REQUIRED_ARTIFACT_MISSING', `Produce the required output paths before completing: ${missing.map(item => item.path).join(', ')}`);
    const completion = hostResultProposalEnvelope(definition, { output, changed_paths: changed, artifacts: changed,
      evidence: [{ kind: 'current_main_orchestration', thread_id }, ...(check ? [{ kind: 'host_tool_receipt', receipt: check.receipt }] : [])] });
    signal?.throwIfAborted();
    // The external checker and both scope snapshots have settled. One fresh
    // acceptance audit owns the durable proposal/usage/semantic commit; its
    // journal projections advance together under the exact Run guard.
    return await runtime.runs.withHostTransaction(run_id,'main_commit',async()=>{
      const saved = await runtime.runs.saveExecutorResult(run_id, attempt.id, completion);
      await event('result_proposed', { ...saved, final_acceptance_required: false });
      await event('session_state', { status: 'closed' });
      await runtime.recordHostMainUsage(run_id, { ...binding, request_id: `dispatch-${attempt.id}`, usage: { unknown: true } });
      signal?.throwIfAborted();
      const final = record.pins.root.workflow.finalization?.node_id === definition.id;
      return runtime.completeHostMainResult(run_id, binding,
        final && !Object.hasOwn(definition.outputs_schema?.properties ?? {}, 'accepted') ? { accepted: true } : {});
    });
  } catch (error) {
    const rejection = semanticRejected ? await runtime.runs.saveArtifact(run_id, `main-rejection-${attempt.id}`, canonicalJSON(output)) : null;
    await event('completion_invalid', { diagnostic: String(error.message).slice(0,900), thread_id,
      ...(rejection ? { rejection_artifact: rejection.artifact, rejection_sha256: rejection.sha256, rejection_bytes: rejection.bytes } : {}) });
    const current = await runtime.runs.read(run_id);
    const exhausted = semanticTurnsConsumed(current.state.nodes[definition.id]) >= definition.retry.max_attempts;
    if (current.state.status === 'running' && (semanticRejected || exhausted || ['MAIN_ORCHESTRATION_SCOPE_VIOLATION', 'MAIN_ORCHESTRATION_HOST_CHECK_FALSE', 'HOST_TOOL_FAILED', 'HOST_TOOL_TIMEOUT', 'HOST_TOOL_CANCELLED', 'HOST_TOOL_SCOPE'].includes(error.code))) {
      await event('session_state', {status:'closed'});
      await runtime.failNode(run_id, {...binding,error:{code:error.code ?? 'MAIN_ORCHESTRATION_FAILED',message:String(error.message).slice(0,2000)}});
    }
    throw error;
  }
}
