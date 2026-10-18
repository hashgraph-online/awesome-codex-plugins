import { graphInfo } from './workflow-state.mjs';
import { requireValue } from './workflow-paths.mjs';
import { createMainAgentPacket, createMainHostBinding } from './execution/host-main-automation.mjs';
import { canonicalJSON, digest } from './workflow-revisions.mjs';
import { isAuthoringRunProvenance } from './authoring/authoring-workflows.mjs';
import {committedTerminalCompletion} from './execution/terminal-output.mjs';
import {nodeRuntimeScope,runtimeRequirementsForState} from './runtime-environment-state.mjs';
import {sharedHostRegion,prepareSharedHostProjection,startSharedHostWork,joinSharedHostWork,hasSharedHostWorkOwner,releaseSettledSharedHostOwners} from './execution/shared-host-work.mjs';

const semantic = new Set(['agent', 'skill_ref']);
const terminal = new Set(['succeeded', 'failed', 'cancelled']);

function activeMainHandoff(record) {
  if(record.state.status!=='running')return null;
  const graph=graphInfo(record.pins.root.workflow),matches=[];
  for(const id of graph.order){
    const definition=graph.nodes.get(id),node=record.state.nodes[id];
    if(definition?.executor?.kind!=='main'||!['claimed','running'].includes(node?.status))continue;
    const attempt=node.attempts.find(item=>item.id===node.active_attempt_id);
    if(attempt&&['claimed','running'].includes(attempt.status))matches.push({definition,attempt});
  }
  requireValue(matches.length<=1,'MAIN_DRIVE_AMBIGUOUS','More than one active main-agent handoff exists');
  return matches[0]??null;
}

/**
 * Advance Host/control/tool work. Semantic nodes stop for an explicit handoff;
 * advanceToMain may then dispatch native Providers through their exact Host
 * execution owner when the caller requested managed Providers.
 */
export class WorkflowDrive {
  constructor({ runtime, executor }) { this.runtime = runtime; this.executor = executor; }

  async executeTool(runId,binding,assertActive){
    try{return {outcome:await this.executor.executeHostTool(runId,binding,{assertActive})};}
    catch(error){return this.settleToolFailure(runId,binding,error);}
  }

  async settleToolFailure(runId,binding,error){
      const failure={code:typeof error.code==='string'?error.code:'HOST_TOOL_FAILED',message:String(error.message??error).slice(0,2000)};
      try{
        const latest=await this.runtime.authorizedPlanningRun(runId,{control_token:binding.control_token});
        if(terminal.has(latest.record.state.status))return {outcome:latest.record.state};
        await this.runtime.authorizedExecution(runId,binding,()=>binding);
        requireValue(typeof this.runtime.failAttemptAfterQuiescence==='function','EXECUTION_COORDINATOR_REQUIRED','Claimed Host tool failure requires exact cleanup coordination');
        return {outcome:await this.runtime.failAttemptAfterQuiescence(runId,binding,failure)};
      }catch(settlementError){return {error:failure,settlement_error:{code:settlementError.code??'HOST_TOOL_FAILURE_UNSETTLED',message:String(settlementError.message??settlementError).slice(0,2000)}};}
  }

  async advance(runId, { control_token, owner = 'workflow-drive', request_prefix = 'drive', assertActive = () => {} } = {}) {
    return (await this.#advance(runId, { control_token, owner, request_prefix, assertActive })).progress;
  }

  async #advance(runId, { control_token, owner, request_prefix, assertActive }, findActiveMain = false) {
    requireValue(typeof owner === 'string' && owner.length > 0 && owner.length <= 256, 'DRIVE_OWNER', 'Drive needs a bounded controller owner');
    for (let step = 0; step < 1024; step++) {
      assertActive();
      const { record, next } = await this.runtime.authorizedPlanningRun(runId, { control_token }); assertActive();
      const state = record.state;
      releaseSettledSharedHostOwners(this.runtime,runId,state);
      let externalEnvironment=false;
      const stop = (progress,committedState=state) => ({ ...(!externalEnvironment?{record}:{}),progress:{...progress,...committedTerminalCompletion(committedState)}, active: null });
      const concurrent=record.pins.root.workflow.nodes.find(definition=>definition.type==='tool'
        &&sharedHostRegion(record.pins.root.workflow,definition.id)&&['claimed','running'].includes(state.nodes[definition.id]?.status));
      if(concurrent&&!hasSharedHostWorkOwner(this.runtime,runId,state.nodes[concurrent.id].active_attempt_id))
        return stop({status:state.status,stop_reason:'execution_recovery_required',node_id:concurrent.id,
          attempt_id:state.nodes[concurrent.id].active_attempt_id,error:{code:'HOST_TOOL_RECONCILIATION_REQUIRED',message:'The exact concurrent Host attempt has no live owner; reconcile its durable effect without replay'},steps:step});
      if (findActiveMain) {
        const active = activeMainHandoff(record);
        if (active) {
          requireValue(active.attempt.owner===owner,'FINALIZER_AUTHORITY','The active main-agent handoff belongs to a different main actor');
          return { record, active, progress: {status:state.status,stop_reason:'semantic_node',node_id:active.definition.id,steps:step} };
        }
      }
      if (terminal.has(state.status)) return stop({ status: state.status, stop_reason: 'terminal', steps: step });
      if (next.parent_block) return stop({ status: state.status, stop_reason: 'parent_block', details: next.parent_block, steps: step });
      if (next.approvals.length) return stop({ status: state.status, stop_reason: 'approval', approvals: next.approvals, steps: step });
      if (!next.ready.length) {
        if(concurrent){
          const node=state.nodes[concurrent.id],attempt=node.attempts.find(item=>item.id===node.active_attempt_id);
          const settled=await joinSharedHostWork(this.runtime,runId,{node_id:concurrent.id,attempt_id:attempt.id});assertActive();
          if(settled.error)return stop({status:state.status,stop_reason:'execution_recovery_required',node_id:concurrent.id,attempt_id:attempt.id,...settled,steps:step+1});
          continue;
        }
        const tool=record.pins.root.workflow.nodes.find(definition=>definition.type==='tool'&&['claimed','running'].includes(state.nodes[definition.id]?.status));
        if(tool)return stop({status:state.status,stop_reason:'execution_recovery_required',node_id:tool.id,
          attempt_id:state.nodes[tool.id].active_attempt_id,error:{code:'HOST_TOOL_RECONCILIATION_REQUIRED',message:'The claimed Host tool has no settled outcome; reconcile its exact execution owner before continuing'},steps:step});
        return stop({ status: state.status, stop_reason: state.status === 'blocked' ? 'input_or_ambiguity' : 'no_deterministic_progress', steps: step });
      }
      const graph = graphInfo(record.pins.root.workflow);
      // Launch the qualified writer before exposing its sibling Main, even
      // when the Main ID sorts before the tool ID in the graph order.
      const overlapTool=graph.order.find(id=>next.ready.includes(id)&&graph.nodes.get(id).type==='tool'&&sharedHostRegion(record.pins.root.workflow,id));
      const nodeId = overlapTool??graph.order.find(id => next.ready.includes(id)); const definition = graph.nodes.get(nodeId);
      const requirements=nodeRuntimeScope(state,record.pins,nodeId)?.requirements??runtimeRequirementsForState(state);
      // Semantic/tool claims own dependency admission. Preparing here then
      // preparing again during claim discarded an otherwise usable plan.
      try { if(requirements.executables.length&&((!findActiveMain&&semantic.has(definition.type))||!semantic.has(definition.type)&&definition.type!=='tool')){externalEnvironment=true;assertActive(); await this.runtime.ensureRuntimeEnvironment(runId, {control_token,node_id:nodeId}); assertActive();} }
      catch(error) {
        if(error.code !== 'ENVIRONMENT_SETUP_REQUIRED') throw error;
        return stop({status:state.status,stop_reason:'environment_attention',environment:error.environment??error.details?.environment,steps:step});
      }
      if (semantic.has(definition.type)) {
        const maximum = definition.cost?.maximum_micros ?? definition.decision?.budget?.maximum_micros ?? null;
        const budget = state.cost_ledger?.budget;
        if (budget && (maximum === null || state.cost_ledger.spent_micros + state.cost_ledger.reserved_micros + maximum > budget.limit_micros)) return stop({ status: state.status, stop_reason: 'budget', node_id: nodeId, steps: step });
        return stop({ status: state.status, stop_reason: 'semantic_node', node_id: nodeId, steps: step });
      }
      if (definition.type === 'human_gate') return stop({ status: state.status, stop_reason: 'approval', node_id: nodeId, steps: step });
      if (definition.type === 'tool') {
        let lease;
        try { assertActive(); lease = await this.runtime.claimNode(runId, { node_id: nodeId, owner, request_id: `${request_prefix}-${nodeId}-${record.sequence}`, control_token }); }
        catch (error) {
          if (['BINDING_MISSING', 'APPROVAL_REQUIRED'].includes(error.code)) return stop({ status: state.status, stop_reason: error.code === 'BINDING_MISSING' ? 'missing_input' : 'approval', node_id: nodeId, error: { code: error.code, message: error.message }, steps: step });
          throw error;
        }
        const binding={node_id:nodeId,attempt_id:lease.attempt_id,lease_token:lease.lease_token,control_token};
        const region=sharedHostRegion(record.pins.root.workflow,nodeId);
        if(region){
          try{await prepareSharedHostProjection(this.runtime,runId,binding,region);assertActive();}
          catch(error){
            const settled=await this.settleToolFailure(runId,binding,error);
            if(settled.error)return stop({status:state.status,stop_reason:'execution_recovery_required',node_id:nodeId,attempt_id:lease.attempt_id,...settled,steps:step+1});
            return stop({status:settled.outcome.status,stop_reason:terminal.has(settled.outcome.status)&&settled.outcome.status!=='failed'?'terminal':'host_failure',
              node_id:nodeId,error:settled.outcome.nodes?.[nodeId]?.error??{code:error.code??'SHARED_HOST_PROJECTION_FAILED',message:String(error.message).slice(0,2000)},steps:step+1},settled.outcome);
          }
          // The ordinary tool executor owns admission/cancellation. An RPC
          // return must not revoke its long-lived attempt through that request's
          // signal; Run/attempt fences still cancel the real broker normally.
          startSharedHostWork(this.runtime,runId,binding,()=>this.executeTool(runId,binding,()=>{}));
          continue;
        }
        assertActive();const settled=await this.executeTool(runId,binding,assertActive);assertActive();
        if(settled.error)return stop({status:state.status,stop_reason:'execution_recovery_required',node_id:nodeId,attempt_id:lease.attempt_id,...settled,steps:step+1});
        const outcome=settled.outcome;
        if (outcome.status === 'failed') return stop({ status: 'failed', stop_reason: 'host_failure', node_id: nodeId, error: outcome.nodes?.[nodeId]?.error ?? null, steps: step + 1 },outcome);
        if (outcome.status === 'cancelled') return stop({ status: 'cancelled', stop_reason: 'terminal', steps: step + 1 },outcome);
        assertActive();
        continue;
      }
      if (definition.type === 'subworkflow') return stop({ status: state.status, stop_reason: 'child_control', node_id: nodeId, steps: step });
      return stop({ status: state.status, stop_reason: 'ambiguity', node_id: nodeId, steps: step });
    }
    throw Object.assign(new Error('Deterministic drive exceeded its bounded transition limit'), { code: 'DRIVE_LIMIT' });
  }

  /**
   * Advance deterministic work, then atomically claim and dispatch the next
   * main-agent node.  The response deliberately omits the full Run state and
   * returns only the current node prompt, completion schema and its declared
   * resource texts.  This keeps node-scoped projection while avoiding the
   * repeated next -> claim -> dispatch -> read_resource model round trips.
   */
  async advanceToMain(runId, { control_token, owner, request_prefix = 'main', assertActive = () => {}, managedProviders = false } = {}) {
    requireValue(typeof owner === 'string' && owner.length > 0 && owner.length <= 256, 'DRIVE_OWNER', 'Main-session drive needs the exact main actor');
    const planning=await this.#advance(runId,{control_token,owner,request_prefix,assertActive},true);
    let { record, active, progress } = planning;
    if(!active){
      assertActive();
      if(progress.stop_reason!=='semantic_node')return {run_id:runId,control_token,...progress};
      record??=await this.runtime.runs.read(runId);
      assertActive();
    }

    const definition=active?.definition??record.pins.root.workflow.nodes.find(node=>node.id===progress.node_id);
    requireValue(definition,'NODE_MISSING','Drive selected a node absent from the pinned Workflow');
    if(definition.executor?.kind!=='main'){
      const provider=record.pins.providers.find(item=>item.id===definition.executor?.provider_id);
      if(!managedProviders||definition.executor?.kind!=='provider'||provider?.kind!=='native_agent')
        return {run_id:runId,control_token,...progress,stop_reason:'non_main_semantic'};
      // Opaque identities and task data stay in the Host. No model reconstructs
      // a spawn call or relays a child's completion back into the graph.
      const lease=await this.runtime.claimNode(runId,{node_id:definition.id,owner,
        request_id:`${request_prefix}-${definition.id}-${record.sequence}`,control_token});
      assertActive();
      const args={...lease,control_token,host_managed_native:true};
      const dispatched=await this.executor.dispatch(runId,args);assertActive();
      const manager=dispatched.execution_owner==='strict_codex'?this.executor.strictManager
        :dispatched.execution_owner==='managed_native_codex'?this.executor.managedNativeManager:null;
      requireValue(manager&&typeof manager.wait==='function','NATIVE_EXECUTION_OWNER',
        'Host native dispatch did not identify a waitable exact execution owner');
      const settled=await manager.wait(runId,lease.attempt_id);assertActive();
      if(settled.status!=='succeeded'){
        const current=await this.runtime.get(runId);assertActive();
        requireValue(terminal.has(current.status),'NATIVE_EXECUTION_UNSETTLED',
          `Host native ${dispatched.execution_owner} stopped at ${settled.status} while the Run remains active`);
      }
      return this.advanceToMain(runId,{control_token,owner,request_prefix,assertActive,managedProviders});
    }

    const requestId=active?.attempt.claim_request_id??`${request_prefix}-${definition.id}-${record.sequence}`;
    assertActive();
    let lease,current;
    const claim=async()=>{
      lease=await this.runtime.claimHostMain(runId,{node_id:definition.id,owner,request_id:requestId,control_token});
      current=await this.runtime.runs.read(runId);
    };
    const requirements=nodeRuntimeScope(record.state,record.pins,definition.id)?.requirements??runtimeRequirementsForState(record.state);
    if(requirements.executables.length)await claim();
    else await this.runtime.runs.withHostTransaction(runId,'claim',claim);
    assertActive();
    const attempt=current.state.nodes[definition.id].attempts.find(item=>item.id===lease.attempt_id);
    let dispatched;
    if(!attempt.dispatch){ assertActive(); dispatched=await this.executor.dispatch(runId,{...lease,control_token,host_managed_main:true}); assertActive(); }
    else{
      // A Host Main receipt means the semantic node already has one exact
      // execution owner.  The caller must join that owner instead of rebuilding
      // the handoff or returning control to the model to poll the Run.
      if(attempt.dispatch.receipt && definition.executor.mode !== 'orchestration')return {run_id:runId,control_token,status:current.state.status,
        stop_reason:'main_execution_pending',node_id:definition.id,attempt_id:attempt.id,steps:progress.steps};
      assertActive();
      const prepared=await this.executor.prepare(runId,{...lease,control_token,host_managed_main:true});
      assertActive();
      requireValue(attempt.dispatch.request_id===`dispatch-${lease.attempt_id}`&&attempt.dispatch.envelope_hash===digest(canonicalJSON(prepared)),'MAIN_DRIVE_IDENTITY_CHANGED','The persisted main-agent dispatch identity no longer matches its Run-pinned packet');
      dispatched={...prepared,compiled_prompt:prepared.prompt,handoff_required:true,request_id:attempt.dispatch.request_id,dispatched:false,idempotent:true};
    }
    requireValue(dispatched.adapter?.execution === (definition.executor.mode === 'orchestration' ? 'current_main_orchestration' : 'host_isolated_main') && dispatched.handoff_required === true, 'MAIN_DRIVE_ADAPTER', 'Main drive must return the declared Host-owned context handoff');

    // The remaining packet derivation reads immutable pins only. Its exact
    // claim record already verified them; dispatch independently authorized
    // its intent after configuration/environment callbacks. Acceptance and
    // the actual Main execution will still perform their fresh audits.
    record=current;
    assertActive();
    // The Host Main manager reads exact Run-pinned objects through its scoped
    // broker. Handoffs carry only logical resource IDs, never duplicate bytes.
    const resources = (definition.resources ?? []).map(path => ({ path }));

    const finalAcceptance = record.pins.root.workflow.finalization?.node_id === definition.id
      && isAuthoringRunProvenance(record.pins.root.provenance);
    return {
      status: 'running',
      stop_reason: definition.executor.mode === 'orchestration' ? 'main_orchestration' : 'main_node',
      node_id: definition.id,
      steps: progress.steps,
      host_binding: createMainHostBinding({ runId, controlToken: control_token, owner, definition, lease, finalAcceptance }),
      agent_packet: createMainAgentPacket({ definition, dispatched, resources, finalAcceptance }),
    };
  }
}
