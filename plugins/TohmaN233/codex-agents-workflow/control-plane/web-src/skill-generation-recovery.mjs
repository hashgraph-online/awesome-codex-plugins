const authoringKinds=new Set(['authoring_workflow_run','skill_expansion_job']);
const waitingPhases=new Set(['review_required','ready_to_apply','user_input_required','attention','approval','authentication_required']);

function recoveryError(code,message){return Object.assign(new Error(message),{code,detail:{code}});}

export function shouldPollAuthoring({run,pollEnabled,stopping,error,phase}){
  return !!run&&pollEnabled===true&&!stopping&&!error&&!waitingPhases.has(phase);
}

export function mountedAuthoringSession(sessions,controllers,sessionKey){
  const saved=sessions.get(sessionKey);
  return saved && typeof saved.control_token==='string' && saved.control_token && controllers.get(saved.run_id)===saved.control_token ? saved : null;
}

export function assessAuthoringRecovery(pack,definition,state){
  const provenance=definition?.provenance;
  if(!authoringKinds.has(provenance?.kind))throw recoveryError('AUTHORING_RECOVERY_RUN','The selected Run is not a pinned authoring Run');
  if(provenance.source_workflow_id!==pack?.workflow?.id||provenance.source_revision!==pack?.revision_hash)
    throw recoveryError('AUTHORING_RECOVERY_SOURCE','The authoring Run belongs to a different source Workflow or revision; open its exact source Draft');
  if(!Number.isSafeInteger(state?.sequence)||state.sequence<1||typeof state.run_id!=='string')
    throw recoveryError('AUTHORING_RECOVERY_STATE','The authoring Run has no valid journal state');
  if(['failed','cancelled'].includes(state.status))
    throw recoveryError('AUTHORING_RECOVERY_TERMINAL','This authoring Run is terminal and cannot resume; inspect its detailed Run or use a supported recheck of its saved proposal');
  const completedExpand=state.nodes?.expand?.status==='succeeded'&&!!state.nodes.expand.output;
  const retained=completedExpand||state.nodes?.expand?.attempts?.some(attempt=>attempt.status==='succeeded'&&attempt.result_proposal?.sha256)||
    !!state.generation_repair?.previous_proposal||!!state.generation_repair?.latest_cumulative_plan?.proposal;
  if(!retained)throw recoveryError('AUTHORING_RECOVERY_PROPOSAL','This Run has no retained planner proposal; it cannot resume from an existing plan');
  const waiting=state.generation_repair?.awaiting_user_input===true;
  const interrupted=Object.values(state.nodes??{}).some(node=>node.status==='interrupted');
  const continuation=state.status==='succeeded'?'accepted':interrupted?'reconcile':waiting?'guidance':completedExpand?'advance':'reconcile';
  return {run_id:state.run_id,provenance:{kind:provenance.kind,source_workflow_id:provenance.source_workflow_id,source_revision:provenance.source_revision},state,continuation};
}

export async function inspectAuthoringRun(api,pack,runId){
  if(typeof runId!=='string'||!runId.trim())throw recoveryError('AUTHORING_RECOVERY_RUN','Enter an existing authoring Run ID');
  const id=runId.trim();
  const [definition,state]=await Promise.all([api('run_definition',{run_id:id}),api('get',{run_id:id})]);
  if(state?.run_id!==id)throw recoveryError('AUTHORING_RECOVERY_STATE','The returned Run identity differs from the requested Run ID');
  return assessAuthoringRecovery(pack,definition,state);
}

export async function inspectControlledAuthoringRun(api,pack,runId,controllers){
  const inspected=await inspectAuthoringRun(api,pack,runId);
  const controlToken=controllers.get(inspected.run_id);
  if(controlToken===undefined)return {inspected,controlToken:''};
  if(typeof controlToken!=='string'||!controlToken)throw recoveryError('AUTHORING_RECOVERY_CONTROL','The saved controller token is invalid');
  // A read-only snapshot authenticates the reused token without changing the Run.
  let snapshot;
  try{snapshot=await api('run_snapshot',{run_id:inspected.run_id,control_token:controlToken,after_sequence:inspected.state.sequence});}
  catch(cause){
    if(cause?.code!=='RUN_AUTHORITY')throw cause;
    if(controllers.get(inspected.run_id)===controlToken)controllers.delete(inspected.run_id);
    throw Object.assign(recoveryError('AUTHORING_RECOVERY_CONTROL_STALE','The saved controller token is no longer valid; explicitly take control of the verified Run again'),{inspected,cause});
  }
  if(snapshot?.state?.run_id!==inspected.run_id)throw recoveryError('AUTHORING_RECOVERY_STATE','The authenticated snapshot belongs to a different Run');
  return {inspected:assessAuthoringRecovery(pack,{provenance:inspected.provenance},snapshot.state),controlToken};
}

export async function continueControlledAuthoringRun(api,pack,runId,controllers){
  const {inspected,controlToken}=await inspectControlledAuthoringRun(api,pack,runId,controllers);
  if(!controlToken)throw recoveryError('AUTHORING_RECOVERY_CONTROL','Take control of the exact authoring Run first');
  if(inspected.state.control_recovery?.errors?.length)throw recoveryError('AUTHORING_RECOVERY_RECONCILIATION','Controller cleanup needs reconciliation in the detailed Run before resuming');
  if(inspected.continuation==='reconcile')throw recoveryError('AUTHORING_RECOVERY_RECONCILIATION','This Run needs explicit node reconciliation in the detailed Run before authoring can continue');
  const resumed=['running','succeeded'].includes(inspected.state.status)
    ? inspected.state
    : await api('resume',{run_id:inspected.run_id,control_token:controlToken});
  return {checked:assessAuthoringRecovery(pack,{provenance:inspected.provenance},resumed),controlToken};
}

export async function adoptAuthoringRun(api,pack,runId){
  const inspected=await inspectAuthoringRun(api,pack,runId);
  const adopted=await api('adopt_run',{run_id:inspected.run_id,expected_sequence:inspected.state.sequence,reason:'User explicitly resumed the pinned authoring Run in the local console',main_actor:'human-console'});
  return {inspected,adopted};
}
