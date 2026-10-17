// Generation policy is separate from stored/manual executor choices. It changes
// no permissions and never introduces Providers or Workbench Role instructions.
export const GENERATION_EXECUTOR_POLICY='provider-subagents/v2';
export const GENERATION_RESPONSIBILITY_GUIDE='Choose responsibility before model strength. Main O is the actual initiating conversation: use decision or orchestration profiles for user intent and route decisions, live clarification, conversation-owned coordination and final semantic acceptance. Excluding default Main worker never excludes Main O. Keep Main lightweight; independent repository scanning, production and audit belong to workers when explicit inputs suffice. worker_read and worker_write cover routine bounded inspection and production; read-only work is not automatically planning. worker_complex_read and worker_complex_write require concrete cross-module complexity or difficult implementation. review is a genuinely independent critique; an audit request or local self-check does not by itself require a separate reviewer. worker_reasoning is reserved for difficult planning, novel causal diagnosis or unresolved design tradeoffs; explain that difficulty in the activity instructions, and do not select it merely because a task is called analysis, scan, audit or planning. Use the configured Provider and its model suitability description for these profiles. Main worker and thread are explicit user edits. Registered deterministic tools own mechanical work. A semantic profile is not a Workbench Role; generated nodes never inject Role templates.';

export function generatedActivityTaskType(activity,{historical=false}={}){
  if(activity.kind==='review')return 'review';
  if(!historical&&activity.kind==='planning')return 'planning';
  if(activity.complexity==='complex')return 'complex_implementation';
  return historical&&activity.operation!=='write'?'planning':'implementation';
}

export const GENERATION_EXECUTOR_OPTIONS=Object.freeze({
  provider:Object.freeze({default_for:'independent_workers',selection:'configured_provider',description:'Ordinary production and independent review use an enabled existing writable Provider subagent.'}),
  main_orchestration:Object.freeze({default_for:'initiating_main_context',selection:'semantic_orchestration_or_decision',description:'Orchestration and decisions that belong to the initiating conversation use Main orchestration.'}),
  main_worker:Object.freeze({selection:'explicit_user_edit',description:'Main worker is available as an explicit node edit and starts a fresh Host-owned session using the calling model.'}),
  thread:Object.freeze({selection:'explicit_user_edit',description:'A persistent user-visible Codex task is available as an explicit node edit with qualified task lineage.'}),
});

export function generatedTaskLineageError(activity,successor,field,sourceRefs=[]){
  const key=activity.semantic_key??activity.key??activity.id??'<unknown>';
  const message=`Activity ${key} requires task lineage that ordinary generated Provider workers cannot establish from this declaration.`;
  return Object.assign(new Error(message),{code:'AUTHORING_SEMANTIC',findings:[{
    kind:'semantic',code:'generated_task_lineage',message,source_refs:structuredClone(sourceRefs),
    semantic_keys:[key,...(typeof successor==='string'&&successor?[successor]:[])],
    affected_semantic_fields:[`activities.${key}.${field}`],blocked_by:[],
    minimal_change:'Preserve the required temporal work in one live worker activity or a qualified semantic repair loop; consolidate activities when their continuation cannot be represented.',
  }]});
}

export function normalizeGeneratedActivity(activity,{sectionInventory=[]}={}){
  const result=structuredClone(activity);
  if(!result||typeof result!=='object'||result.tool||result.capability?.kind==='registered_tool')return result;
  const lineage=result.task_continues||result.continues;
  if(lineage){
    const sourceRefs=(sectionInventory??[]).filter(item=>(result.source_sections??[]).includes(item.section_id)).map(item=>item.source_span).filter(Boolean);
    throw generatedTaskLineageError(result,lineage,result.task_continues?'task_continues':'continues',sourceRefs);
  }
  if(typeof result.profile==='string'){
    if(result.profile==='main_read')result.profile='worker_read';
    if(result.profile==='main_write')result.profile='worker_write';
    if(result.profile.startsWith('worker_')&&result.fanout)delete result.fanout.workspace_field;
    return result;
  }
  if(result.kind==='decision'&&['main','isolated_worker'].includes(result.ownership)&&[undefined,'worker','orchestration'].includes(result.main_mode)){
    result.ownership='main';result.main_mode='orchestration';
  }else if(['main','isolated_worker'].includes(result.ownership)&&[undefined,'worker'].includes(result.main_mode)){
    result.ownership='isolated_worker';delete result.main_mode;
    // This directory field belongs to Main's per-item sessions. Provider
    // workers retain the same declared Host write-path isolation instead.
    if(result.fanout)delete result.fanout.workspace_field;
  }
  return result;
}
