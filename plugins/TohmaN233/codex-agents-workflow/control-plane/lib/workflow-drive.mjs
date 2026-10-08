import { graphInfo } from './workflow-state.mjs';
import { requireValue } from './workflow-paths.mjs';
import { createMainAgentPacket, createMainHostBinding } from './execution/host-main-automation.mjs';
import { canonicalJSON, digest } from './workflow-revisions.mjs';
import { isAuthoringRunProvenance } from './authoring/authoring-workflows.mjs';

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

  async advance(runId, { control_token, owner = 'workflow-drive', request_prefix = 'drive', assertActive = () => {} } = {}) {
    requireValue(typeof owner === 'string' && owner.length > 0 && owner.length <= 256, 'DRIVE_OWNER', 'Drive needs a bounded controller owner');
    assertActive();
    await this.runtime.authorizeController(runId, { control_token });
    assertActive();
    for (let step = 0; step < 1024; step++) {
      assertActive();
      const record = await this.runtime.runs.read(runId); assertActive();
      const state = record.state; const next = await this.runtime.next(runId); assertActive();
      if (terminal.has(state.status)) return { status: state.status, stop_reason: 'terminal', steps: step };
      if (next.parent_block) return { status: state.status, stop_reason: 'parent_block', details: next.parent_block, steps: step };
      if (next.approvals.length) return { status: state.status, stop_reason: 'approval', approvals: next.approvals, steps: step };
      if (!next.ready.length) return { status: state.status, stop_reason: state.status === 'blocked' ? 'input_or_ambiguity' : 'no_deterministic_progress', steps: step };
      try { await this.runtime.ensureRuntimeEnvironment(runId, {control_token}); }
      catch(error) {
        if(error.code !== 'ENVIRONMENT_SETUP_REQUIRED') throw error;
        return {status:state.status,stop_reason:'environment_attention',environment:error.details?.environment,steps:step};
      }
      const graph = graphInfo(record.pins.root.workflow); const nodeId = graph.order.find(id => next.ready.includes(id)); const definition = graph.nodes.get(nodeId);
      if (semantic.has(definition.type)) {
        const maximum = definition.cost?.maximum_micros ?? definition.decision?.budget?.maximum_micros ?? null;
        const budget = state.cost_ledger?.budget;
        if (budget && (maximum === null || state.cost_ledger.spent_micros + state.cost_ledger.reserved_micros + maximum > budget.limit_micros)) return { status: state.status, stop_reason: 'budget', node_id: nodeId, steps: step };
        return { status: state.status, stop_reason: 'semantic_node', node_id: nodeId, steps: step };
      }
      if (definition.type === 'human_gate') return { status: state.status, stop_reason: 'approval', node_id: nodeId, steps: step };
      if (definition.type === 'tool') {
        let lease;
        try { assertActive(); lease = await this.runtime.claimNode(runId, { node_id: nodeId, owner, request_id: `${request_prefix}-${nodeId}-${record.sequence}`, control_token }); }
        catch (error) {
          if (['BINDING_MISSING', 'APPROVAL_REQUIRED'].includes(error.code)) return { status: state.status, stop_reason: error.code === 'BINDING_MISSING' ? 'missing_input' : 'approval', node_id: nodeId, error: { code: error.code, message: error.message }, steps: step };
          throw error;
        }
        assertActive();
        const outcome = await this.executor.executeHostTool(runId, { node_id: nodeId, attempt_id: lease.attempt_id, lease_token: lease.lease_token, control_token }, { assertActive });
        assertActive();
        if (outcome.status === 'failed') return { status: 'failed', stop_reason: 'host_failure', node_id: nodeId, error: outcome.nodes?.[nodeId]?.error ?? null, steps: step + 1 };
        if (outcome.status === 'cancelled') return { status: 'cancelled', stop_reason: 'terminal', steps: step + 1 };
        continue;
      }
      if (definition.type === 'subworkflow') return { status: state.status, stop_reason: 'child_control', node_id: nodeId, steps: step };
      return { status: state.status, stop_reason: 'ambiguity', node_id: nodeId, steps: step };
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
    assertActive();
    await this.runtime.authorizeController(runId,{control_token});
    assertActive();
    let record=await this.runtime.runs.read(runId); assertActive();
    let active=activeMainHandoff(record),progress;
    if(active){
      requireValue(active.attempt.owner===owner,'FINALIZER_AUTHORITY','The active main-agent handoff belongs to a different main actor');
      progress={status:record.state.status,stop_reason:'semantic_node',node_id:active.definition.id,steps:0};
    }else{
      progress=await this.advance(runId,{control_token,owner,request_prefix,assertActive});
      assertActive();
      if(progress.stop_reason!=='semantic_node')return {run_id:runId,control_token,...progress};
      record=await this.runtime.runs.read(runId);
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
    const lease=await this.runtime.claimHostMain(runId,{node_id:definition.id,owner,request_id:requestId,control_token});
    assertActive();
    const current=await this.runtime.runs.read(runId); assertActive();
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

    record=await this.runtime.runs.read(runId);
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
