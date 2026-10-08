import { requireValue } from '../workflow-paths.mjs';
import { digest, canonicalJSON } from '../workflow-revisions.mjs';
import { advanceRun } from '../workflow-state.mjs';
import { decodeGeneratedEnvelope, decodeGeneratedProposal } from './expansion-run.mjs';
import { applySemanticRepair, canonicalizeSemanticRepair, SEMANTIC_BLUEPRINT_CONTRACT, SEMANTIC_REPAIR_CONTRACT } from '../authoring/blueprint-contract.mjs';
import { MAX_AUTHORING_ATTEMPTS, MAX_PLANNER_ATTEMPTS } from './generation-retry-policy.mjs';
import { authoringDependencyAssessmentRequired, isAuthoringRunProvenance } from '../authoring/authoring-workflows.mjs';

function proposalForRepair(state,pins) {
  const output=state.nodes.expand.output,outputHash=output?digest(canonicalJSON(output)):null;
  const attempt=state.nodes.expand.attempts.find(item=>item.id===state.nodes.expand.active_attempt_id)??state.nodes.expand.attempts.at(-1);
  const binding=outputHash?{attempt_id:attempt?.id??null,output_hash:outputHash}:null;
  const projection=state.generation_projection,currentIsCanonical=outputHash&&projection?.projected_output_hash===outputHash;
  const retained=state.generation_repair?.latest_cumulative_plan,currentIsRetained=outputHash&&retained?.output_hash===outputHash;
  let proposal=null,decodeError=null,artifactKind=null;
  if(currentIsRetained&&retained?.proposal){proposal=structuredClone(retained.proposal);artifactKind='retained_cumulative_plan';}
  else if(output&&!currentIsCanonical)try{
    const payload=decodeGeneratedEnvelope(output);
    if(payload?.contract===SEMANTIC_BLUEPRINT_CONTRACT)proposal=payload;
    else if(payload?.contract===SEMANTIC_REPAIR_CONTRACT){
      const base=state.generation_repair?.previous_proposal??state.generation_repair?.latest_cumulative_plan?.proposal??projection?.authoring_plan;
      requireValue(base,'AUTHORING_REPAIR_STATE','A semantic patch has no exact cumulative base');
      proposal=applySemanticRepair(base,canonicalizeSemanticRepair(payload),{targets:state.generation_repair?.feedback?.findings});
    }else proposal=decodeGeneratedProposal(output,pins.root.provenance.source_revision,{requirePlanningAnalysis:pins.root.provenance.routing_rules?.selection_mode === 'automatic',requireSourceDispositions:(pins.root.provenance.review_contract_version ?? 1)>=8,requireRuntimeDependencies:authoringDependencyAssessmentRequired(pins.root.workflow.authoring?.contract)});
    artifactKind='planner_artifact';
  }catch(error){decodeError={code:error.code ?? 'GENERATION_PROPOSAL_INVALID',message:error.message,raw_output_hash:outputHash};}
  if(!output&&retained?.proposal){
    proposal=structuredClone(retained.proposal);artifactKind='retained_cumulative_plan';
  }else if(currentIsCanonical&&projection?.authoring_plan){
    proposal=structuredClone(projection.authoring_plan);artifactKind='canonical_projection';
  }else if(!output&&!proposal&&projection?.authoring_plan){
    proposal=structuredClone(projection.authoring_plan);artifactKind='canonical_projection';
  }
  return {proposal,decodeError,binding:binding?{...binding,artifact_kind:artifactKind}:retained?{attempt_id:retained.attempt_id,output_hash:retained.output_hash,artifact_kind:'retained_cumulative_plan'}:null};
}

function cumulativePlan(proposal,binding){return {proposal:structuredClone(proposal),attempt_id:binding?.attempt_id??null,output_hash:binding?.output_hash??digest(canonicalJSON(proposal)),artifact_kind:binding?.artifact_kind??'semantic_plan',at:new Date().toISOString()};}
function appendPlanLedger(previous,entry){
  const ledger=previous?.plan_ledger??[];
  if(!entry.attempt_id||!entry.output_hash)return ledger;
  const existing=ledger.find(item=>item.attempt_id===entry.attempt_id&&item.output_hash===entry.output_hash);
  if(existing){requireValue(canonicalJSON(existing.proposal)===canonicalJSON(entry.proposal),'AUTHORING_REPAIR_STATE','One planner artifact resolved to conflicting cumulative plans');return ledger;}
  return [...ledger,entry];
}

const repairCollections=new Set(['source_dispositions','requirement_assignments','runtime_dependencies','records','lists','enums','activities','approvals','sequences','parallels','choices']);
export function validateRepairTargets(previousPlan,feedback,{canonicalProposal=null}={}){
  const known=new Set();
  for(const collection of repairCollections)for(const item of previousPlan?.[collection]??[])known.add(collection==='source_dispositions'?item.section_id:collection==='requirement_assignments'?item.requirement_id:item.key);
  for(const node of canonicalProposal?.nodes??[]){known.add(node.id);if(node.semantic_key)known.add(node.semantic_key);}
  for(const requirement of canonicalProposal?.source_requirements??[])known.add(requirement.requirement_id);
  for(const disposition of canonicalProposal?.source_dispositions??[])known.add(disposition.section_id);
  const targets=feedback?.findings;
  if(!Array.isArray(targets)||!targets.length)return {valid:false,diagnostic:'Semantic feedback contains no repair target.'};
  for(const [index,target] of targets.entries()){
    if(!target||typeof target!=='object'||Array.isArray(target))return {valid:false,diagnostic:`Repair target ${index+1} is not a structured stable-key target.`};
    const keys=target.semantic_keys,fields=target.affected_semantic_fields;
    if(!Array.isArray(keys)||!keys.length||keys.some(key=>typeof key!=='string'||!known.has(key)))return {valid:false,diagnostic:`Repair target ${target.target_id??index+1} does not map to a current activity, approval, control, requirement or source disposition.`};
    if(!Array.isArray(fields)||!fields.length||fields.some(field=>typeof field!=='string'||!repairCollections.has(field.split('.')[0])))return {valid:false,diagnostic:`Repair target ${target.target_id??index+1} does not identify an editable semantic field.`};
  }
  return {valid:true};
}

async function waitForUserRepair(runtime,args,record,feedback,{reason='automatic_limit',message='Automatic semantic repairs are exhausted. The exact current plan and findings were retained; add focused guidance to continue with another targeted patch.'}={}) {
  const {state,pins,sequence}=record,{proposal,decodeError,binding}=proposalForRepair(state,pins);
  requireValue(proposal,'AUTHORING_REPAIR_STATE','The current semantic plan cannot be recovered for a targeted repair',{decode_error:decodeError});
  await runtime.transition(args.run_id,'generation_repair',(current)=>{
    requireValue(current.control_hash===digest(args.control_token),'RUN_AUTHORITY','Invalid generation controller');
    requireValue(current.status==='running','GENERATION_REPAIR_STATE','Only an active authoring Run can wait for user guidance');
    const entry=cumulativePlan(proposal,binding),previous=current.generation_repair;
    current.generation_repair={...(previous ?? {}),round:current.nodes.expand.attempts.length,feedback,previous_proposal:proposal,latest_cumulative_plan:entry,plan_ledger:appendPlanLedger(previous,entry),awaiting_user_input:true,wait_reason:reason,...(decodeError?{previous_decode_error:decodeError}:{})};
    current.updated_at=new Date().toISOString();
  },{expected_sequence:sequence});
  return {phase:'user_input_required',status:reason,error:{code:'GENERATION_REPAIR_LIMIT',message},feedback,continuation:{operation:'continue_authoring',mode:'targeted_semantic_patch',preserves_current_plan:true,max_guidance_characters:4000}};
}

// Only closed, read-only Skill planning rounds may be rewound. This is not a
// general Workflow retry: all previous attempts and their artifacts stay intact.
export async function repairGeneration(runtime,args,record,feedback,{reviewOnly=false,manual=false,userGuidance=null}={}) {
  const {state,pins,sequence}=record;
  const policy=pins.generation?.settings;
  requireValue(policy && isAuthoringRunProvenance(pins.root.provenance),'GENERATION_REPAIR_DISABLED','This Run has no pinned automatic repair policy');
  requireValue(Buffer.byteLength(canonicalJSON(feedback))<=100000,'GENERATION_FEEDBACK_LIMIT','Repair feedback exceeds its bounded limit');
  if(reviewOnly)return {phase:'attention',status:'review_protocol_error',error:{code:'GENERATION_REVIEW_PROTOCOL',message:'Review output does not match its protocol; a mechanical protocol error never spends a semantic repair.'},feedback};
  const {proposal:previousProposal,decodeError:previousDecodeError,binding:previousBinding}=proposalForRepair(state,pins);
  requireValue(previousProposal,'AUTHORING_REPAIR_STATE','The current semantic plan cannot be recovered for a targeted repair',{decode_error:previousDecodeError});
  const targetValidation=validateRepairTargets(previousProposal,feedback,{canonicalProposal:state.nodes.expand.output?.proposal});
  if(!targetValidation.valid)return {phase:'attention',status:'semantic_diagnostic_error',error:{code:'GENERATION_REPAIR_TARGETS',message:`${targetValidation.diagnostic} No planner call was released.`,retry_class:'mechanical',automatic_retry:false},feedback};
  if(!manual && state.generation_repair?.feedback && canonicalJSON(state.generation_repair.feedback)===canonicalJSON(feedback))return waitForUserRepair(runtime,args,record,feedback,{reason:'non_improving_feedback',message:'The exact same stable-key findings remained after the targeted patch. The Host stopped before spending another model attempt and retained the current plan for focused guidance.'});
  if(!manual && state.nodes.expand.attempts.length>=Math.min(policy.max_rounds,MAX_PLANNER_ATTEMPTS))return waitForUserRepair(runtime,args,record,feedback);
  requireValue(!manual || typeof userGuidance==='string' && userGuidance.trim() && userGuidance.length<=4000,'GENERATION_USER_GUIDANCE','User-guided repair needs nonempty guidance of at most 4000 characters');
  if(manual && state.nodes.expand.attempts.length>=MAX_AUTHORING_ATTEMPTS)return {phase:'attention',status:'authoring_attempt_limit',error:{code:'GENERATION_REPAIR_LIMIT',message:`This authoring Run reached its pinned ${MAX_AUTHORING_ATTEMPTS}-attempt safety limit; start a new conversion to continue.`},feedback};
  await runtime.transition(args.run_id,'generation_repair',(current,definition)=>{
    requireValue(current.control_hash===digest(args.control_token),'RUN_AUTHORITY','Invalid generation controller');
    requireValue(['running','failed'].includes(current.status),'GENERATION_REPAIR_STATE','Stopped or paused generation cannot restart');
    requireValue(current.permissions.access==='read_only' && definition.root.workflow.nodes.filter(n=>n.executor).every(n=>n.access==='read_only'),'GENERATION_REPAIR_SCOPE','Only read-only planning can repair automatically');
    for (const id of ['expand','graph_assembly','execution_binding','deterministic_validation','final']) {
      const node=current.nodes[id];
      const attempt=node.attempts.find(a=>a.id===node.active_attempt_id);
      if(attempt?.dispatch) {
        const definitionNode=definition.root.workflow.nodes.find(item=>item.id===id);
        const modelClosed=attempt.executor_events?.some(e=>e.kind==='session_state' && e.metadata.status==='closed');
        const hostReplayClosed=attempt.status==='succeeded' && attempt.dispatch.receipt?.executor==='host-generation-replay';
        const hostToolClosed=definitionNode?.executor?.kind==='tool' && ['succeeded','failed','cancelled'].includes(attempt.status) && attempt.host_tool?.receipt;
        requireValue((modelClosed || hostReplayClosed || hostToolClosed) && !attempt.dispatch.cancellation_pending,'GENERATION_REPAIR_ACTIVE','Previous model session, Host replay or Host tool must be settled before repair');
      }
      if(attempt && ['claimed','running'].includes(attempt.status)) {attempt.status='failed';attempt.error={code:'GENERATION_REVIEW_REJECTED',message:'Review requested a corrected proposal'};attempt.finished_at=new Date().toISOString();}
      node.status='pending';node.active_attempt_id=null;node.output=null;node.error=null;node.failure_handled=false;node.approval_id=null;node.approval_round++;
    }
    current.nodes.end.status='pending';current.output=null;current.error=null;current.status='running';
    current.edges=Object.fromEntries(definition.root.workflow.edges.map(e=>[e.id,e.source==='start'?'selected':'pending']));
    const manualContinuations=(state.generation_repair?.manual_continuations ?? 0)+(manual?1:0);
    const entry=cumulativePlan(previousProposal,previousBinding),previous=current.generation_repair;
    current.generation_repair={round:current.nodes.expand.attempts.length+1,semantic_repair_index:current.nodes.expand.attempts.length,feedback,previous_proposal:previousProposal,latest_cumulative_plan:entry,plan_ledger:appendPlanLedger(previous,entry),awaiting_user_input:false,manual_continuations:manualContinuations,...(manual?{user_guidance:userGuidance.trim()}:{}),...(previousDecodeError?{previous_decode_error:previousDecodeError}:{})};
    advanceRun(current,definition);current.updated_at=new Date().toISOString();
  },{expected_sequence:sequence});
  return {phase:'repairing',review_only:false,manual,round:state.nodes.expand.attempts.length+1,semantic_repair_index:state.nodes.expand.attempts.length,feedback};
}

export async function continueGenerationRepair(runtime,args) {
  await runtime.authorizeController(args.run_id,args);
  const record=await runtime.runs.read(args.run_id);
  const waiting=record.state.generation_repair;
  requireValue(isAuthoringRunProvenance(record.pins.root.provenance) && record.state.status==='running','GENERATION_RUN','User-guided repair needs an active authoring Run');
  requireValue(waiting?.awaiting_user_input===true && waiting.feedback,'GENERATION_USER_GUIDANCE','This authoring Run is not waiting for user repair guidance');
  return repairGeneration(runtime,args,record,waiting.feedback,{manual:true,userGuidance:args.guidance});
}
