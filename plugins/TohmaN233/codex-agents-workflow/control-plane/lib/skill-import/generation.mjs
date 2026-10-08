import { evaluateReview } from './review-checklist.mjs';
import { repairGeneration } from './generation-repair.mjs';
import { generationProgress } from './generation-progress.mjs';
import { leaseToken } from '../workflow-execution-envelope.mjs';
import { requireValue } from '../workflow-paths.mjs';
import { decodeGeneratedProposal } from './expansion-run.mjs';
import { canonicalJSON, digest } from '../workflow-revisions.mjs';
import { validateGenerationProposal } from './proposal-validation.mjs';
import { isGenerationContractFailure, semanticGenerationRepair } from './generation-retry-policy.mjs';
import { MAX_AUTHORING_REVIEW_RESOURCE_BYTES, authoringDependencyAssessmentRequired, authoringReviewIdentity, isAuthoringRunProvenance } from '../authoring/authoring-workflows.mjs';

const hasChecklistReview = version => Number.isInteger(version) && version >= 2;

async function persistCanonicalProposal(runtime,args,record,proposal,repairs=[],authoringPlan=null,pipelineTrace=null,workflowInputsSchema=null) {
  requireValue(Buffer.byteLength(canonicalJSON(proposal))<=MAX_AUTHORING_REVIEW_RESOURCE_BYTES,'AUTHORING_REVIEW_RESOURCE_LIMIT','Canonical proposal exceeds the bounded independent-review resource limit');
  const currentOutput=record.state.nodes.expand.output;
  if(currentOutput?.host_pipeline){
    requireValue(currentOutput.host_pipeline.proposal_hash===digest(canonicalJSON(proposal)) && canonicalJSON(currentOutput.proposal)===canonicalJSON(proposal),'GENERATION_PROJECTION_CONFLICT','Existing Host compiler stage evidence belongs to a different canonical proposal');
    return {idempotent:true,projection:record.state.generation_projection??null};
  }
  const retainedTrace=pipelineTrace??record.state.generation_projection?.pipeline_trace??null;
  requireValue(retainedTrace?.results,'GENERATION_HOST_PIPELINE','Canonical authoring output needs exact Host compiler stage evidence');
  const output={proposal:structuredClone(proposal),host_pipeline:{contract:retainedTrace.contract,proposal_hash:retainedTrace.proposal_hash,results:structuredClone(retainedTrace.results)}};
  const sourceOutputHash=digest(canonicalJSON(record.state.nodes.expand.output)),projectedOutputHash=digest(canonicalJSON(output));
  const existing=record.state.generation_projection;
  if(sourceOutputHash===projectedOutputHash){
    if(existing?.projected_output_hash)requireValue(existing.projected_output_hash===projectedOutputHash,'GENERATION_PROJECTION_CONFLICT','Canonical generation output disagrees with its persisted projection identity');
    return {idempotent:true,projection:existing??null};
  }
  await runtime.transition(args.run_id,'generation_projection',state=>{
    const projectionNode=state.nodes.graph_assembly??state.nodes.final,attempt=projectionNode.attempts.find(item=>item.id===projectionNode.active_attempt_id);
    const unsubmittedClaim=projectionNode.status==='claimed' && projectionNode.active_attempt_id===args.attempt_id && !attempt?.dispatch;
    requireValue(state.control_hash===digest(args.control_token) && state.nodes.expand.status==='succeeded' && (projectionNode.status==='ready' || unsubmittedClaim),'RUN_SEQUENCE_CONFLICT','Generation state changed before Host compilation');
    const previous=state.generation_projection??{},sameProjection=previous.projected_output_hash===projectedOutputHash;
    const retainedPlan=authoringPlan??(sameProjection?previous.authoring_plan:null);
    const projectedTrace=pipelineTrace??(sameProjection?previous.pipeline_trace:null);
    const expandAttemptId=state.nodes.expand.active_attempt_id;
    state.nodes.expand.output=structuredClone(output);
    const projection={...previous,source_output_hash:sourceOutputHash,source_attempt_id:expandAttemptId,projected_output_hash:projectedOutputHash,contract_version:record.pins.root.provenance.review_contract_version,repair_actions:structuredClone(repairs),at:new Date().toISOString()};
    requireValue(workflowInputsSchema&&typeof workflowInputsSchema==='object'&&!Array.isArray(workflowInputsSchema),'GENERATION_HOST_PROJECTION','Independent review needs the Host-projected future-Run input schema');
    projection.review_inputs_schema=structuredClone(workflowInputsSchema);
    if(retainedPlan)projection.authoring_plan=structuredClone(retainedPlan);else delete projection.authoring_plan;
    if(projectedTrace){projection.pipeline_trace=structuredClone(projectedTrace);if(pipelineTrace)projection.pipeline_trace_binding={attempt_id:expandAttemptId,source_output_hash:sourceOutputHash,projected_output_hash:projectedOutputHash};else if(previous.pipeline_trace_binding)projection.pipeline_trace_binding=structuredClone(previous.pipeline_trace_binding);else delete projection.pipeline_trace_binding;}
    else{delete projection.pipeline_trace;delete projection.pipeline_trace_binding;}
    state.generation_projection=projection;
    state.updated_at=state.generation_projection.at;
  },{expected_sequence:record.sequence});
  return {idempotent:false};
}

// Compile and persist the exact reviewer input before any authoring finalizer
// can run. Both automatic advancement and the low-level claim/dispatch path use
// this gate, so manual driving cannot review a raw semantic envelope.
export async function prepareAuthoringReview(runtime,args,{store,context}) {
  if(args.node_id && !['graph_assembly','final'].includes(args.node_id))return null;
  const record=await runtime.runs.read(args.run_id),provenance=record.pins.root.provenance;
  if(!isAuthoringRunProvenance(provenance))return null;
  const pack=await store.snapshot(provenance.source_workflow_id,provenance.source_revision);
  const resources=await store.resources(provenance.source_workflow_id,provenance.source_revision);
  const validated=validateGenerationProposal(record.state.nodes.expand.output,{pack,resources,provenance,context,previousPlan:record.state.generation_repair?.previous_proposal ?? null,repairFeedback:record.state.generation_repair?.feedback ?? null});
  await persistCanonicalProposal(runtime,args,record,validated.proposal,validated.repairs,validated.authoring_plan,validated.pipeline_trace,validated.compiled.workflow.inputs_schema);
  return validated;
}

// One bounded transition per request. Only pinned read-only generation repairs
// may retry; human final acceptance remains explicit.
export async function advanceGeneration(service, runtime, executor, args, {store,context}) {
  await runtime.authorizeController(args.run_id,args);
  let record = await runtime.runs.read(args.run_id);
  let {state,pins} = record;
  requireValue(isAuthoringRunProvenance(pins.root.provenance), 'GENERATION_RUN', 'Generation requires a pinned authoring Workflow Run');
  const source = {workflow_id:pins.root.provenance.source_workflow_id,expected_revision:pins.root.provenance.source_revision};
  const proposal = () => decodeGeneratedProposal(state.nodes.expand.output?.host_pipeline?{proposal:state.nodes.expand.output.proposal}:state.nodes.expand.output, source.expected_revision, {requirePlanningAnalysis:pins.root.provenance.routing_rules?.selection_mode === 'automatic',requireSourceDispositions:(pins.root.provenance.review_contract_version ?? 1)>=8,requireRuntimeDependencies:authoringDependencyAssessmentRequired(pins.root.workflow.authoring?.contract)});
  for (const nodeId of ['expand','graph_assembly','execution_binding','deterministic_validation','final']) {
    record=await runtime.runs.read(args.run_id);({state,pins}=record);
    if (state.status === 'succeeded') return {phase:'ready_to_apply',source};
    if (state.status==='blocked') {const blocked=await runtime.next(args.run_id);if(blocked.approvals.length) return {phase:'approval',approvals:blocked.approvals};}
    if (state.status !== 'running') {
      const failed = Object.values(state.nodes).find(n=>n.status==='failed');
      const error=failed?.error ?? state.error;
      return {phase:'attention',status:state.status,error:{...error,retry_class:'mechanical',automatic_retry:false},models:pins.generation?.settings,diagnostics:failed?.attempts.at(-1)?.executor_events?.filter(e=>['model_catalog','session_state'].includes(e.kind))};
    }
    const next=await runtime.next(args.run_id);if(next.approvals.length)return {phase:'approval',approvals:next.approvals};
    const node = state.nodes[nodeId];
    requireValue(node, 'GENERATION_RUN', 'Expansion Run is missing a required stage');
    if (node.status === 'succeeded') continue;
    if (node.status === 'ready') {
      if(nodeId==='graph_assembly' || nodeId==='final') {
        try {
          await prepareAuthoringReview(runtime,{...args,node_id:'final'},{store,context});
        }
        catch(error){
          if(!isGenerationContractFailure(error)) throw error;
          const feedback={code:error.code,message:error.message,findings:error.findings ?? [],validation:error.validation ?? null};
          const semantic=semanticGenerationRepair(feedback);
          if(semantic && feedback.findings.length===0)return {phase:'attention',status:'semantic_diagnostic_error',error:{...feedback,message:`${feedback.message} Host semantic validation did not provide stable-key repair targets; automatic retry was stopped.`,retry_class:'mechanical',automatic_retry:false}};
          if(pins.generation?.settings && semantic)return repairGeneration(runtime,args,record,feedback);
          return {phase:'attention',status:semantic?'semantic_contract_error':'mechanical_contract_error',error:{...feedback,retry_class:semantic?'semantic':'mechanical',automatic_retry:false}};
        }
      }
      const claim={...args,node_id:nodeId,owner:state.main_actor,request_id:'generation-'+nodeId+'-'+node.attempts.length};
      const lease = pins.root.workflow.nodes.find(item=>item.id===nodeId)?.executor?.kind==='main'
        ? await runtime.claimHostMain(args.run_id,claim)
        : await runtime.claimNode(args.run_id,claim);
      await executor.dispatch(args.run_id,{...args,node_id:nodeId,attempt_id:lease.attempt_id,lease_token:lease.lease_token});
      if(['graph_assembly','execution_binding','deterministic_validation'].includes(nodeId))continue;
      return {phase:nodeId==='expand'?'generating':nodeId==='final'?'reviewing':'host_compiling',stage:nodeId,progress:generationProgress(await runtime.runs.read(args.run_id),nodeId)};
    }
    const attempt = node.attempts.find(a=>a.id===node.active_attempt_id);
    if (!attempt || !['claimed','running'].includes(node.status)) return {phase:'attention',status:node.status,error:node.error};
    const lease = {...args,node_id:nodeId,attempt_id:attempt.id,lease_token:leaseToken(args.control_token,args.run_id,nodeId,attempt.id,attempt.lease_generation ?? 0)};
    if (!attempt.dispatch) {
      await executor.dispatch(args.run_id,lease);
      if(['graph_assembly','execution_binding','deterministic_validation'].includes(nodeId))continue;
      return {phase:nodeId==='expand'?'generating':nodeId==='final'?'reviewing':'host_compiling',stage:nodeId,progress:generationProgress(await runtime.runs.read(args.run_id),nodeId)};
    }
    if (nodeId==='final' && attempt.result_proposal) {
      const result = await service.strictManager.collect(runtime,args.run_id,{...lease,accepted:false});
      const pack = await store.snapshot(source.workflow_id,source.expected_revision);
      const resources = await store.resources(source.workflow_id,pack.revision_hash);
      let review;
      const decoded=proposal();
      try {review=hasChecklistReview(pins.root.provenance.review_contract_version)?evaluateReview(result.completion.structured_output,decoded,resources,{version:pins.root.provenance.review_contract_version}):result.completion.structured_output;}
      catch(error){if(error.code!=='GENERATION_CHECKLIST_INVALID')throw error;return {phase:'attention',status:'review_protocol_error',error:{code:error.code,message:error.message,retry_class:'mechanical',automatic_retry:false}};}
      if(pins.generation?.settings && (review.approved!==true || review.findings.length)) {
        if(review.semantic_findings.length) return repairGeneration(runtime,args,record,{code:'GENERATION_REVIEW_FINDINGS',findings:review.semantic_repair_targets?.length?review.semantic_repair_targets:review.semantic_findings});
        return {phase:'attention',status:'host_review_findings',error:{code:'GENERATION_HOST_REVIEW_FINDINGS',message:'Reviewer found only Host-owned projection, routing or evidence problems. Another semantic planner attempt cannot repair them.',findings:review.host_findings,retry_class:'mechanical',automatic_retry:false}};
      }
      const validated=validateGenerationProposal(state.nodes.expand.output,{pack,resources,provenance:pins.root.provenance,context});
      return {phase:'review_required',source,proposal:validated.proposal,workflow:validated.compiled.workflow,validation:validated.compiled.validation,review:{...result.completion,structured_output:review}};
    }
    const live = await service.strictManager.status(runtime,args.run_id,lease);
    return {phase:['auth_required','auth_pending'].includes(live.status)?'authentication_required':nodeId==='expand'?'generating':nodeId==='final'?'reviewing':'host_compiling',stage:nodeId,live,progress:generationProgress(record,nodeId)};
  }
  return {phase:'attention',status:state.status};
}

export async function acceptGeneration(service, runtime, args) {
  requireValue(args.accepted === true,'GENERATION_ACCEPTANCE','Review and explicitly accept the proposed graph first');
  await runtime.authorizeController(args.run_id,args);
  const record = await runtime.runs.read(args.run_id);
  const provenance = record.pins.root.provenance;
  requireValue(isAuthoringRunProvenance(provenance),'GENERATION_RUN','Not an authoring Workflow Run');
  const pending = record.state.nodes.final?.attempts.find(a=>a.id===record.state.nodes.final.active_attempt_id);
  requireValue(record.state.status === 'succeeded' || (record.state.status === 'running' && pending?.result_proposal), 'GENERATION_NOT_READY', 'Generation is not ready for acceptance');
  const observation = {phase:record.state.status==='succeeded'?'ready_to_apply':'review_required', source:{workflow_id:provenance.source_workflow_id,expected_revision:provenance.source_revision}};
  if (observation.phase==='review_required') {
    const {state} = await runtime.runs.read(args.run_id);
    const attempt = state.nodes.final.attempts.find(a=>a.id===state.nodes.final.active_attempt_id);
    await service.strictManager.acceptAuthoring(runtime,args.run_id,{...args,node_id:'final',attempt_id:attempt.id,lease_token:leaseToken(args.control_token,args.run_id,'final',attempt.id,attempt.lease_generation ?? 0),accepted:true});
  }
  return service.call('apply_authoring_result',{...args,...observation.source},{human:true});
}

export async function loginGeneration(service,runtime,args) {
  await runtime.authorizeController(args.run_id,args);
  const {state,pins}=await runtime.runs.read(args.run_id);
  requireValue(isAuthoringRunProvenance(pins.root.provenance) && state.status==='running','GENERATION_RUN','Login requires an active authoring Workflow Run');
  const nodeId=['expand','final'].find(id=>state.nodes[id] && ['claimed','running'].includes(state.nodes[id].status));
  const node=state.nodes[nodeId];
  const attempt=node?.attempts.find(a=>a.id===node.active_attempt_id);
  requireValue(attempt?.dispatch,'GENERATION_NOT_READY','No active generation session');
  return service.strictManager.login(runtime,args.run_id,{...args,node_id:nodeId,attempt_id:attempt.id,lease_token:leaseToken(args.control_token,args.run_id,nodeId,attempt.id,attempt.lease_generation ?? 0)});
}

// Re-run the current deterministic compiler and independent reviewer against a
// proposal that already completed in an exact earlier generation attempt. This
// is deliberately not a model retry: the prior artifact identity is persisted
// as the dispatch receipt, so host/compiler fixes do not spend another planner
// call or masquerade as newly generated semantic work.
export async function recheckGenerationProposal(service,runtime,args,{store,context}) {
  requireValue(typeof args.source_run_id === 'string' && args.source_run_id.length > 0, 'GENERATION_RECHECK_SOURCE', 'Generation recheck needs a source Run');
  const prior=await runtime.runs.read(args.source_run_id);
  const provenance=prior.pins.root.provenance;
  requireValue(isAuthoringRunProvenance(provenance),'GENERATION_RECHECK_SOURCE','Source Run is not an authoring Workflow Run');
  const priorAttempt=[...(prior.state.nodes.expand?.attempts ?? [])].reverse().find(attempt=>attempt.status==='succeeded' && attempt.result_proposal);
  requireValue(priorAttempt?.result_proposal?.sha256,'GENERATION_RECHECK_SOURCE','Source Run has no completed durable planner proposal');
  const priorResult=await runtime.runs.readExecutorResult(args.source_run_id,priorAttempt.id,priorAttempt.result_proposal.sha256);
  requireValue(priorResult?.status==='succeeded' && priorResult.structured_output,'GENERATION_RECHECK_SOURCE','Source planner artifact is not a successful structured completion');
  const rawOutputHash=digest(canonicalJSON(priorResult.structured_output));
  const recordedPlan=prior.state.generation_repair?.plan_ledger?.find(item=>item.attempt_id===priorAttempt.id&&item.output_hash===rawOutputHash);
  const isCurrentAttempt=prior.state.nodes.expand.active_attempt_id===priorAttempt.id;

  const pack=await store.snapshot(provenance.source_workflow_id,provenance.source_revision);
  const resources=await store.resources(provenance.source_workflow_id,provenance.source_revision);
  const sourceOutput=recordedPlan?{proposal:recordedPlan.proposal}:priorResult.structured_output;
  const validated=validateGenerationProposal(sourceOutput,{pack,resources,provenance,context,previousPlan:isCurrentAttempt?prior.state.generation_repair?.previous_proposal??null:null,repairFeedback:isCurrentAttempt?prior.state.generation_repair?.feedback??null:null});
  // A completed planner attempt may be a semantic delta. Recheck validates
  // that delta against its pinned base, then replays the resulting full plan:
  // the new Run must not depend on repair state from the old Run.
  const replayOutput=validated.authoring_plan?{proposal:validated.authoring_plan}:sourceOutput;

  const started=await service.call('start_authoring',{
    workflow_id:provenance.source_workflow_id,
    revision_hash:provenance.source_revision,
    run_id:args.run_id,
    routing_rules:provenance.routing_rules,
  },{human:true});
  const control={run_id:started.run_id,control_token:started.control_token};
  const state=await runtime.get(started.run_id);
  const lease=await runtime.claimNode(started.run_id,{...control,node_id:'expand',owner:state.main_actor,request_id:`generation-recheck-${digest(args.source_run_id).slice(0,16)}`});
  const replayIdentity={source_run_id:args.source_run_id,source_attempt_id:priorAttempt.id,result_sha256:priorAttempt.result_proposal.sha256,materialized_sha256:digest(canonicalJSON(replayOutput)),source_revision:provenance.source_revision};
  const request_id=`replay-${digest(canonicalJSON(replayIdentity)).slice(0,32)}`;
  const dispatch={...control,...lease,request_id,envelope_hash:digest(canonicalJSON(replayIdentity))};
  await runtime.recordDispatchIntent(started.run_id,dispatch);
  await runtime.recordDispatchReceipt(started.run_id,{...dispatch,receipt:{task_id:args.source_run_id,invocation_id:priorAttempt.id,executor:'host-generation-replay',result_sha256:replayIdentity.materialized_sha256,source_result_sha256:priorAttempt.result_proposal.sha256}});
  await runtime.completeNode(started.run_id,{...lease,completion:{
    status:'succeeded',
    summary:`Reused the completed proposal from ${args.source_run_id} after deterministic host projection was upgraded; no planner model was invoked.`,
    structured_output:replayOutput,
    artifacts:[],changed_paths:[],outside_paths:[],
    evidence:[{kind:'host_generation_recheck',...replayIdentity}],
  }});
  return {...started,recheck:{...replayIdentity,planner_invoked:false,conversion_level:validated.compiled.workflow.import_status.conversion_level}};
}

// A host validation upgrade may make a previously rejected, already persisted
// reviewer artifact acceptable. Revalidate that exact artifact and apply it
// under explicit human acceptance without invoking either model again.
export async function acceptRecheckedGenerationReview(service,runtime,args) {
  requireValue(args.accepted===true,'GENERATION_ACCEPTANCE','Rechecked review acceptance must be explicit');
  await runtime.authorizeController(args.run_id,args);
  const record=await runtime.runs.read(args.run_id);const provenance=record.pins.root.provenance;
  requireValue(isAuthoringRunProvenance(provenance) && record.state.nodes.expand?.status==='succeeded','GENERATION_RECHECK_REVIEW','Review recheck needs a completed proposal');
  requireValue(record.state.generation_repair?.feedback?.code==='GENERATION_CHECKLIST_INVALID' && record.state.nodes.final?.status==='ready','GENERATION_RECHECK_REVIEW','Run is not waiting after a host-checklist rejection');
  const attempt=[...record.state.nodes.final.attempts].reverse().find(item=>item.status==='failed' && item.result_proposal && item.error?.code==='GENERATION_REVIEW_REJECTED');
  requireValue(attempt?.dispatch?.receipt && attempt.executor_events?.some(event=>event.kind==='session_state' && event.metadata.status==='closed'),'GENERATION_RECHECK_REVIEW','No closed durable reviewer artifact is available');
  const expectedIdentity=authoringReviewIdentity(record),artifactIdentity={proposal_hash:attempt.result_proposal.proposal_hash,source_revision:attempt.result_proposal.source_revision,expand_attempt_id:attempt.result_proposal.expand_attempt_id};
  requireValue(canonicalJSON(artifactIdentity)===canonicalJSON(expectedIdentity)&&canonicalJSON(attempt.dispatch.receipt.authoring_review_context)===canonicalJSON(expectedIdentity),'AUTHORING_REVIEW_IDENTITY','Persisted reviewer artifact is not bound to the current canonical proposal');
  const completion=await runtime.runs.readExecutorResult(args.run_id,attempt.id,attempt.result_proposal.sha256);
  const {store,context}=await service.open();const pack=await store.snapshot(provenance.source_workflow_id,provenance.source_revision);const resources=await store.resources(provenance.source_workflow_id,provenance.source_revision);
  const validated=validateGenerationProposal(record.state.nodes.expand.output,{pack,resources,provenance,context});
  let review;
  try { review=hasChecklistReview(provenance.review_contract_version)?evaluateReview(completion.structured_output,validated.proposal,resources,{version:provenance.review_contract_version}):completion.structured_output; }
  catch(error){requireValue(false,'GENERATION_REVIEW_BLOCKED',error.message);}
  requireValue(review.approved===true && review.findings.length===0,'GENERATION_REVIEW_BLOCKED','The persisted reviewer artifact still has material findings');
  await runtime.transition(args.run_id,'generation_review_recheck',(state,pins)=>{
    requireValue(state.control_hash===digest(args.control_token) && state.nodes.final.status==='ready','RUN_SEQUENCE_CONFLICT','Generation review state changed before recheck acceptance');
    const current=state.nodes.final.attempts.find(item=>item.id===attempt.id);
    requireValue(current?.result_proposal?.sha256===attempt.result_proposal.sha256 && current.status==='failed','GENERATION_RECHECK_REVIEW','Reviewer artifact identity changed');
    const liveIdentity=authoringReviewIdentity({state,pins}),liveArtifactIdentity={proposal_hash:current.result_proposal.proposal_hash,source_revision:current.result_proposal.source_revision,expand_attempt_id:current.result_proposal.expand_attempt_id};
    requireValue(canonicalJSON(liveIdentity)===canonicalJSON(expectedIdentity)&&canonicalJSON(liveArtifactIdentity)===canonicalJSON(expectedIdentity)&&canonicalJSON(current.dispatch?.receipt?.authoring_review_context)===canonicalJSON(expectedIdentity),'AUTHORING_REVIEW_IDENTITY','Reviewer identity changed before recheck acceptance');
    state.nodes.final.active_attempt_id=current.id;state.nodes.final.status='running';state.nodes.final.error=null;
    current.status='running';delete current.error;delete current.finished_at;
    current.reconciliation={kind:'host_review_recheck',result_sha256:current.result_proposal.sha256,previous_feedback:state.generation_repair.feedback,at:new Date().toISOString(),resubmitted:false};
    state.status='running';state.updated_at=new Date().toISOString();
  },{expected_sequence:record.sequence});
  const fresh=await runtime.runs.read(args.run_id);const current=fresh.state.nodes.final.attempts.find(item=>item.id===attempt.id);
  await service.strictManager.acceptAuthoring(runtime,args.run_id,{node_id:'final',attempt_id:current.id,lease_token:leaseToken(args.control_token,args.run_id,'final',current.id,current.lease_generation ?? 0),control_token:args.control_token,accepted:true});
  return service.call('apply_authoring_result',{...args,workflow_id:provenance.source_workflow_id,expected_revision:provenance.source_revision},{human:true});
}
