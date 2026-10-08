import { canonicalJSON } from '../workflow-revisions.mjs';
import { WORKSPACE_SOURCE_LOCATIONS, WORKSPACE_SOURCE_LOCATION_RULES } from '../workspace-source-locations.mjs';
import { validateHostToolContract } from '../execution/host-tool-runner.mjs';
import {agentTranscriptionClauses,hostOwnedAgentField} from '../agent-transcription-policy.mjs';
import { SEMANTIC_LOOP_SCHEMA, semanticLoopReference, semanticLoopFindings } from './semantic-loops.mjs';

export const LEGACY_SEMANTIC_BLUEPRINT_CONTRACT='workflow-semantic-blueprint/v2';
export const PREVIOUS_SEMANTIC_BLUEPRINT_CONTRACT='workflow-semantic-blueprint/v3';
export const PREVIOUS_COMPACT_SEMANTIC_BLUEPRINT_CONTRACT='workflow-semantic-blueprint/v4';
export const PREVIOUS_FANOUT_SEMANTIC_BLUEPRINT_CONTRACT='workflow-semantic-blueprint/v5';
export const SEMANTIC_BLUEPRINT_CONTRACT='workflow-semantic-blueprint/v6';
export const SEMANTIC_REPAIR_CONTRACT='workflow-semantic-repair/v1';

const id={type:'string',minLength:1,maxLength:128};
const typeRef={...id,pattern:'^[A-Za-z][A-Za-z0-9_-]*$'};
const optionalId={type:'string',maxLength:128};
const text={type:'string',minLength:1,maxLength:2000};
const optionalText={type:'string',maxLength:2000};
// Activity instructions become a node prompt. Keep descriptive fields short;
// machine-owned interface data stays in pinned resources and typed metadata.
export const AUTHORING_ACTIVITY_INSTRUCTION_MAX_LENGTH=10000;
export const AUTHORING_NODE_PROMPT_MAX_LENGTH=12000;
const instructionText={type:'string',minLength:1,maxLength:AUTHORING_ACTIVITY_INSTRUCTION_MAX_LENGTH};
const ids=(max=128)=>({type:'array',maxItems:max,items:id});
const compactShape={type:'object',required:['name','kind','values','type_ref'],additionalProperties:false,properties:{name:id,kind:{type:'string',enum:['text','boolean','number','integer','object','list','enum']},values:{type:'array',maxItems:128,items:{type:'string',maxLength:1000}},type_ref:optionalId,contract_ref:optionalId,host_validation:{type:'string',const:WORKSPACE_SOURCE_LOCATIONS}}};
const compactInput={type:'object',required:['name','from'],additionalProperties:false,properties:{name:id,from:{type:'string',minLength:1,maxLength:260}}};
const repeatUntil={type:'object',required:['condition','max_attempts'],additionalProperties:false,properties:{condition:text,max_attempts:{type:'integer',minimum:1,maximum:5}}};
const fanout={type:'object',required:['input','item_name','result_output','count_mode','fixed_count'],additionalProperties:false,properties:{input:id,item_name:id,result_output:id,count_mode:{type:'string',enum:['auto','fixed']},fixed_count:{type:'integer',minimum:0,maximum:32},batch_size:{type:'integer',minimum:1,maximum:32},max_concurrency:{type:'integer',minimum:1,maximum:32},result_mode:{type:'string',const:'per_item'},item_delivery:{type:'string',const:'incremental'},write_paths_field:id,shared_change_field:id}};
const compactActivity={type:'object',required:['key','instructions','profile','source_sections','inputs','outputs','tool'],additionalProperties:false,properties:{
  key:id,instructions:instructionText,profile:{type:'string',enum:['main_read','main_write','orchestration_read','orchestration_write','worker_read','worker_write','worker_complex_read','worker_complex_write','review','decision']},source_sections:{type:'array',minItems:1,maxItems:128,items:id},inputs:{type:'array',maxItems:128,items:compactInput},outputs:{type:'array',maxItems:128,items:compactShape},tool:optionalId,task_continues:optionalId,contract_refs:ids(64),on_missing:{type:'string',enum:['block']},outcome:{type:'string',enum:['artifact','validated_artifact','decision','review','none']},fail_on_false:ids(128),repeat_until:repeatUntil,fanout,
}};
const compactDisposition={type:'object',required:['section_id','disposition','activity_keys','note'],additionalProperties:false,properties:{section_id:id,disposition:{type:'string',enum:['workflow','conditional','reference','omit']},activity_keys:ids(128),note:optionalText}};
const compactAssignment={type:'object',required:['requirement_id','activity_keys'],additionalProperties:false,properties:{requirement_id:id,activity_keys:{type:'array',minItems:1,maxItems:128,items:id}}};
const runtimeDependency={type:'object',required:['key','executable','phase','trigger','source_section','evidence','activity_keys'],additionalProperties:false,properties:{key:id,executable:{type:'object',required:['name'],additionalProperties:false,properties:{name:id,version:optionalId,python_modules:ids(128)}},phase:{type:'string',enum:['unconditional','conditional','artifact_only']},trigger:optionalText,source_section:id,evidence:{type:'object',required:['resource','quote'],additionalProperties:false,properties:{resource:{type:'string',minLength:1,maxLength:1024},quote:text}},activity_keys:{type:'array',minItems:1,maxItems:128,items:id},host_preparation_observation_ids:ids(32)}};
const dataField={type:'object',required:['name','type','required'],additionalProperties:false,properties:{name:id,type:typeRef,required:{type:'boolean'}}};
const recordType={type:'object',required:['key','fields','open'],additionalProperties:false,properties:{key:id,fields:{type:'array',maxItems:256,items:dataField},open:{type:'boolean'}}};
const listType={type:'object',required:['key','item_type'],additionalProperties:false,properties:{key:id,item_type:typeRef}};
const enumType={type:'object',required:['key','values'],additionalProperties:false,properties:{key:id,values:{type:'array',minItems:1,maxItems:128,items:{type:'string',maxLength:1000}}}};
const approval={type:'object',required:['key','question','source_sections'],additionalProperties:false,properties:{key:id,question:text,source_sections:{type:'array',minItems:1,maxItems:128,items:id},subject:optionalId,before:ids(128)}};
const group={type:'object',required:['key','members','failure_meaning'],additionalProperties:false,properties:{key:id,members:{type:'array',minItems:1,maxItems:128,items:id},failure_meaning:{type:'string',enum:['all_required','partial_evidence_allowed']}}};
// The finite schema vocabulary intentionally has no union types.  Keep this
// field schema-neutral here and let the Host compiler require a bounded scalar
// whose JSON type exactly matches the selected decision output.  This avoids
// lossy model-authored string encodings such as "true" for boolean true.
const choiceBranch={type:'object',required:['value','body'],additionalProperties:false,properties:{value:{description:'A string, boolean or finite number matching the decision output type.'},body:id}};
const choice={type:'object',required:['key','decision_activity','output','branches','default_body'],additionalProperties:false,properties:{key:id,decision_activity:id,output:id,branches:{type:'array',minItems:1,maxItems:128,items:choiceBranch},default_body:id}};

// The model describes meaning only. The Host derives root, graph, IDs, schemas,
// bindings, executors, permissions, source spans and package metadata.
export const SEMANTIC_BLUEPRINT_SCHEMA=Object.freeze({type:'object',required:['contract','purpose','source_dispositions','requirement_assignments','records','lists','enums','activities','approvals','sequences','parallels','choices'],additionalProperties:false,properties:{
  contract:{type:'string',const:SEMANTIC_BLUEPRINT_CONTRACT},purpose:text,source_dispositions:{type:'array',maxItems:200,items:compactDisposition},requirement_assignments:{type:'array',maxItems:500,items:compactAssignment},runtime_dependencies:{type:'array',maxItems:100,items:runtimeDependency},records:{type:'array',maxItems:128,items:recordType},lists:{type:'array',maxItems:128,items:listType},enums:{type:'array',maxItems:128,items:enumType},activities:{type:'array',minItems:1,maxItems:64,items:compactActivity},approvals:{type:'array',maxItems:64,items:approval},sequences:{type:'array',maxItems:64,items:group},parallels:{type:'array',maxItems:64,items:group},choices:{type:'array',maxItems:64,items:choice},loops:{type:'array',maxItems:32,items:SEMANTIC_LOOP_SCHEMA},
}});
// Historical v6 planner artifacts omitted this additive field. New v21
// authoring Runs must decide explicitly, including the empty case.
export const CURRENT_AUTHORING_SEMANTIC_BLUEPRINT_SCHEMA=Object.freeze({...SEMANTIC_BLUEPRINT_SCHEMA,required:[...SEMANTIC_BLUEPRINT_SCHEMA.required,'runtime_dependencies']});
const previousCompactActivity=structuredClone(compactActivity);delete previousCompactActivity.properties.fanout;delete previousCompactActivity.properties.task_continues;
delete previousCompactActivity.properties.outputs.items.properties.host_validation;
const previousCompactSchema=contract=>Object.freeze({...SEMANTIC_BLUEPRINT_SCHEMA,properties:{...SEMANTIC_BLUEPRINT_SCHEMA.properties,contract:{type:'string',const:contract},activities:{type:'array',minItems:1,maxItems:64,items:previousCompactActivity}}});
export const PREVIOUS_COMPACT_SEMANTIC_BLUEPRINT_SCHEMA=previousCompactSchema(PREVIOUS_COMPACT_SEMANTIC_BLUEPRINT_CONTRACT);
export const PREVIOUS_FANOUT_SEMANTIC_BLUEPRINT_SCHEMA=previousCompactSchema(PREVIOUS_FANOUT_SEMANTIC_BLUEPRINT_CONTRACT);

const repairCollections=['source_dispositions','requirement_assignments','runtime_dependencies','records','lists','enums','activities','approvals','sequences','parallels','choices','loops'];
const repairChanges={type:'object',required:repairCollections.filter(name=>!['runtime_dependencies','loops'].includes(name)),additionalProperties:false,properties:{
  source_dispositions:{type:'array',maxItems:200,items:compactDisposition},requirement_assignments:{type:'array',maxItems:500,items:compactAssignment},runtime_dependencies:{type:'array',maxItems:100,items:runtimeDependency},records:{type:'array',maxItems:128,items:recordType},lists:{type:'array',maxItems:128,items:listType},enums:{type:'array',maxItems:128,items:enumType},activities:{type:'array',maxItems:64,items:compactActivity},approvals:{type:'array',maxItems:64,items:approval},sequences:{type:'array',maxItems:64,items:group},parallels:{type:'array',maxItems:64,items:group},choices:{type:'array',maxItems:64,items:choice},loops:{type:'array',maxItems:32,items:SEMANTIC_LOOP_SCHEMA},
}};
const repairRemovals={type:'object',required:repairCollections.filter(name=>!['runtime_dependencies','loops'].includes(name)),additionalProperties:false,properties:Object.fromEntries(repairCollections.map(name=>[name,ids(name==='requirement_assignments'?500:200)]))};
export const SEMANTIC_REPAIR_SCHEMA=Object.freeze({type:'object',required:['contract','purpose','upsert','remove'],additionalProperties:false,properties:{contract:{type:'string',const:SEMANTIC_REPAIR_CONTRACT},purpose:{type:'string',const:''},upsert:repairChanges,remove:repairRemovals}});

// The persisted repair contract remains stable; only the model-facing array
// cardinalities are specialized to the exact plan and findings of this attempt.
// A three-key repair must not receive a schema inviting 500 assignments.
export function targetedSemanticRepairSchema(previous,feedback){
  if(previous?.contract!==SEMANTIC_BLUEPRINT_CONTRACT||!Array.isArray(feedback?.findings)||!feedback.findings.length)throw Object.assign(new Error('Targeted repair needs the exact prior semantic plan and findings'),{code:'AUTHORING_REPAIR_STATE'});
  const keys=new Set(feedback.findings.flatMap(item=>item.semantic_keys??[]));
  if(!keys.size)throw Object.assign(new Error('Targeted repair findings name no semantic keys'),{code:'AUTHORING_REPAIR_STATE'});
  const schema=structuredClone(SEMANTIC_REPAIR_SCHEMA),allowance=4*feedback.findings.length+keys.size;
  for(const collection of repairCollections){
    const existing=previous[collection]?.length??0;
    const upsert=schema.properties.upsert.properties[collection],remove=schema.properties.remove.properties[collection];
    upsert.maxItems=Math.min(upsert.maxItems,existing+allowance);
    remove.maxItems=Math.min(remove.maxItems,existing);
  }
  return schema;
}

// v3 is an internal lowering form and remains readable for durable historical
// Runs. New planners never see or emit it.
const internalShape={type:'object',required:['kind','values','type_ref'],additionalProperties:false,properties:{kind:{type:'string',enum:['text','boolean','number','integer','object','list','enum']},values:{type:'array',maxItems:128,items:{type:'string',maxLength:1000}},type_ref:optionalId}};
const consumption={type:'object',required:['name','source_kind','input','activity','output'],additionalProperties:false,properties:{name:id,source_kind:{type:'string',enum:['input','activity','loop']},input:optionalId,activity:optionalId,loop:optionalId,output:optionalId}};
const production={type:'object',required:['name','shape'],additionalProperties:false,properties:{name:id,shape:internalShape,contract_ref:optionalId,host_validation:{type:'string',const:WORKSPACE_SOURCE_LOCATIONS}}};
const capability={type:'object',required:['kind','semantic_name'],additionalProperties:false,properties:{kind:{type:'string',enum:['none','registered_tool']},semantic_name:optionalId}};
const internalActivity={type:'object',required:['key','purpose','kind','instructions','ownership','operation','complexity','source_sections','continues','consumes','produces','capability'],additionalProperties:false,properties:{key:id,purpose:text,kind:{type:'string',enum:['work','review','decision']},instructions:instructionText,ownership:{type:'string',enum:['main','isolated_worker']},main_mode:{type:'string',enum:['worker','orchestration']},operation:{type:'string',enum:['read','write']},complexity:{type:'string',enum:['routine','complex']},source_sections:{type:'array',minItems:1,maxItems:128,items:id},continues:optionalId,consumes:{type:'array',maxItems:128,items:consumption},produces:{type:'array',maxItems:128,items:production},capability,contract_refs:ids(64),on_missing:{type:'string',enum:['block']},outcome:{type:'string',enum:['artifact','validated_artifact','decision','review','none']},fail_on_false:ids(128),repeat_until:repeatUntil,fanout}};
const internalDisposition={type:'object',required:['section_id','disposition','activity_keys','trigger','reason'],additionalProperties:false,properties:{section_id:id,disposition:{type:'string',enum:['workflow','conditional','reference','omit']},activity_keys:ids(128),trigger:optionalText,reason:optionalText}};
const internalRule={type:'object',required:['section_id','statement','activity_keys','applies_when'],additionalProperties:false,properties:{section_id:id,statement:text,activity_keys:{type:'array',minItems:1,maxItems:128,items:id},applies_when:optionalText}};
const internalAssignment={type:'object',required:['requirement_id','activity_keys','binding_names','runtime_guards'],additionalProperties:false,properties:{requirement_id:id,activity_keys:{type:'array',minItems:1,maxItems:128,items:id},binding_names:ids(128),runtime_guards:{type:'array',maxItems:128,items:{type:'string',minLength:1,maxLength:2000}}}};
const internalDataType={type:'object',required:['key','kind','fields','item_type_ref','values','openness'],additionalProperties:false,properties:{key:id,kind:{type:'string',enum:['text','boolean','number','integer','object','list','enum']},fields:{type:'array',maxItems:256,items:{type:'object',required:['name','type_ref','required'],additionalProperties:false,properties:{name:id,type_ref:id,required:{type:'boolean'}}}},item_type_ref:optionalId,values:{type:'array',maxItems:128,items:{type:'string',maxLength:1000}},openness:{type:'string',enum:['closed','open']}}};
export const INTERNAL_SEMANTIC_BLUEPRINT_SCHEMA=Object.freeze({type:'object',required:['contract','purpose','source_dispositions','semantic_rules','requirement_assignments','data_types','activities','approvals','sequences','parallels','choices','root'],additionalProperties:false,properties:{contract:{type:'string',const:PREVIOUS_SEMANTIC_BLUEPRINT_CONTRACT},purpose:text,source_dispositions:{type:'array',maxItems:500,items:internalDisposition},semantic_rules:{type:'array',maxItems:500,items:internalRule},requirement_assignments:{type:'array',maxItems:500,items:internalAssignment},runtime_dependencies:{type:'array',maxItems:100,items:runtimeDependency},data_types:{type:'array',maxItems:500,items:internalDataType},activities:{type:'array',minItems:1,maxItems:500,items:internalActivity},approvals:{type:'array',maxItems:128,items:approval},sequences:{type:'array',maxItems:256,items:group},parallels:{type:'array',maxItems:256,items:group},choices:{type:'array',maxItems:256,items:choice},loops:{type:'array',maxItems:32,items:SEMANTIC_LOOP_SCHEMA},root:id}});

const fail=(code,message)=>{throw Object.assign(new Error(message),{code});};
const formatFail=message=>fail('AUTHORING_FORMAT',message);
const semanticFail=message=>fail('AUTHORING_SEMANTIC',message);
const keyOf=(collection,item)=>collection==='source_dispositions'?item.section_id:collection==='requirement_assignments'?item.requirement_id:item.key;
const requireUniqueActivityInputs=blueprint=>{
  for(const activity of blueprint?.activities ?? []){
    const inputs=blueprint.contract===SEMANTIC_BLUEPRINT_CONTRACT?activity.inputs:activity.consumes;
    if(!Array.isArray(inputs))continue;
    const names=inputs.map(item=>item?.name);
    if(new Set(names).size!==names.length)formatFail(`Activity ${activity.key ?? '<unknown>'} input names must be unique`);
  }
  return blueprint;
};
const upsert=(items,changes,collection)=>{
  const currentKeys=items.map(item=>keyOf(collection,item)),changeKeys=changes.map(item=>keyOf(collection,item));
  if(new Set(currentKeys).size!==currentKeys.length)formatFail(`Semantic repair base has duplicate ${collection} keys`);
  if(new Set(changeKeys).size!==changeKeys.length)formatFail(`Semantic repair contains duplicate ${collection} upserts`);
  const next=new Map(items.map(item=>[keyOf(collection,item),structuredClone(item)]));
  for(const item of changes)next.set(keyOf(collection,item),structuredClone(item));
  return [...next.values()];
};

const referencedKeys=(collection,item)=>{
  if(!item)return [];
  if(collection==='runtime_dependencies')return [item.source_section,...(item.activity_keys??[])];
  if(collection==='source_dispositions'||collection==='requirement_assignments')return item.activity_keys ?? [];
  if(collection==='activities')return [...(item.inputs ?? []).flatMap(input=>typeof input.from==='string'&&!input.from.startsWith('input:')?[semanticLoopReference(input.from)?.key??input.from.split('.')[0]]:[]),...(item.outputs??[]).map(output=>output.type_ref).filter(Boolean)];
  if(collection==='records')return (item.fields??[]).map(field=>field.type).filter(Boolean);
  if(collection==='lists')return item.item_type?[item.item_type]:[];
  if(collection==='approvals')return [...(item.before ?? []),...(typeof item.subject==='string'?[item.subject.split('.')[0]]:[])];
  if(collection==='sequences'||collection==='parallels')return item.members ?? [];
  if(collection==='choices')return [item.decision_activity,item.default_body,...(item.branches ?? []).map(branch=>branch.body)].filter(Boolean);
  if(collection==='loops')return [...(item.activity_keys??[]),...(item.feedback_inputs??[]).map(input=>input.from.split('.')[0])];
  return [];
};
const repairScope=(targets)=>{
  if(!Array.isArray(targets)||!targets.length)fail('AUTHORING_REPAIR_SCOPE','Semantic repair requires the exact current stable-key findings');
  const keys=new Set(targets.flatMap(target=>target?.semantic_keys??[]));
  if(!keys.size)fail('AUTHORING_REPAIR_SCOPE','Semantic repair findings must identify stable keys');
  return {keys};
};
const removalAllows=(scope,collection,key,item)=>scope.keys.has(key)
  ||['sequences','parallels','choices','loops'].includes(collection)
    &&referencedKeys(collection,item).some(reference=>scope.keys.has(reference));
const relationshipProperties={source_dispositions:new Set(['activity_keys']),requirement_assignments:new Set(['activity_keys']),runtime_dependencies:new Set(['activity_keys']),activities:new Set(['inputs']),approvals:new Set(['before','subject']),sequences:new Set(['members']),parallels:new Set(['members']),choices:new Set(['decision_activity','default_body','branches']),loops:new Set(['entry_activity','exit_activity','activity_keys','feedback_inputs','item_scope','until'])};
const propertyAllows=(scope,collection,item,prior,property,createdKeys)=>{
  const key=keyOf(collection,item);
  if(scope.keys.has(key))return true;
  return relationshipProperties[collection]?.has(property)
    &&[...referencedKeys(collection,item),...referencedKeys(collection,prior)].some(reference=>scope.keys.has(reference)||createdKeys.has(reference));
};
const sameJSON=(left,right)=>left===undefined||right===undefined?left===right:canonicalJSON(left)===canonicalJSON(right);
function repairReachability(previous,patch,scope){
  const reachable=new Set(scope.keys);
  const entries=[previous,patch.upsert].flatMap(plan=>[...repairCollections].flatMap(collection=>(plan?.[collection]??[]).map(item=>({key:keyOf(collection,item),refs:referencedKeys(collection,item)}))));
  let changed=true;
  while(changed){
    changed=false;
    for(const entry of entries)if(reachable.has(entry.key)||entry.refs.some(ref=>reachable.has(ref))){
      for(const key of [entry.key,...entry.refs])if(!reachable.has(key)){reachable.add(key);changed=true;}
    }
  }
  return reachable;
}

// The repair envelope keeps this legacy field for durable artifacts, but the
// cumulative Workflow purpose is immutable during a stable-key repair.
export function canonicalizeSemanticRepair(patch){
  if(patch?.contract!==SEMANTIC_REPAIR_CONTRACT)formatFail('Semantic repair uses workflow-semantic-repair/v1');
  if(patch.purpose!==undefined&&typeof patch.purpose!=='string')formatFail('Semantic repair purpose must be text');
  return {...patch,purpose:''};
}

export function applySemanticRepair(previous,patch,{targets=[],allowPurpose=false,corrections=[]}={}){
  if(previous?.contract!==SEMANTIC_BLUEPRINT_CONTRACT)formatFail('Semantic repair requires the current compact blueprint');
  if(patch?.contract!==SEMANTIC_REPAIR_CONTRACT)formatFail('Semantic repair uses workflow-semantic-repair/v1');
  const scope=repairScope(targets);
  const next=structuredClone(previous);
  if(patch.purpose&&patch.purpose!==previous.purpose){if(!allowPurpose)fail('AUTHORING_REPAIR_SCOPE','Targeted semantic repair cannot rewrite the Workflow purpose');next.purpose=patch.purpose;}
  const reachable=repairReachability(previous,patch,scope);
  const existingKeys=new Set(repairCollections.flatMap(collection=>(previous[collection]??[]).map(item=>keyOf(collection,item))));
  const createdKeys=new Set(repairCollections.flatMap(collection=>(patch.upsert?.[collection]??[]).map(item=>keyOf(collection,item))).filter(key=>!existingKeys.has(key)&&reachable.has(key)));
  for(const collection of repairCollections){
    const removed=new Set(patch.remove?.[collection] ?? []);
    const current=next[collection] ?? [],byKey=new Map(current.map(item=>[keyOf(collection,item),item]));
    for(const key of removed){const item=byKey.get(key);if(item&&!removalAllows(scope,collection,key,item))
      fail('AUTHORING_REPAIR_SCOPE',`Semantic repair cannot remove unrelated ${collection} item ${key}`);}
    const accepted=[];
    for(const item of patch.upsert?.[collection] ?? []){
      const key=keyOf(collection,item),prior=byKey.get(key);
      if(prior&&canonicalJSON(prior)===canonicalJSON(item)){accepted.push(item);continue;}
      if(!prior){
        if(!reachable.has(key))fail('AUTHORING_REPAIR_SCOPE',`Semantic repair cannot create unrelated ${collection} item ${key}`);
        accepted.push(item);continue;
      }
      const bounded=structuredClone(item);
      const properties=new Set([...Object.keys(prior ?? {}),...Object.keys(item)]);properties.delete(collection==='source_dispositions'?'section_id':collection==='requirement_assignments'?'requirement_id':'key');
      let allowedChange=false;
      for(const property of properties)if(!sameJSON(prior?.[property],item[property])){
        if(propertyAllows(scope,collection,item,prior,property,createdKeys)){allowedChange=true;continue;}
        if(Object.hasOwn(prior,property))bounded[property]=structuredClone(prior[property]);else delete bounded[property];
        corrections.push({collection,key,property});
      }
      if(!allowedChange)continue;
      accepted.push(bounded);
    }
    next[collection]=upsert(current.filter(item=>!removed.has(keyOf(collection,item))),accepted,collection);
  }
  return requireUniqueActivityInputs(next);
}

const diagnostic=(code,message,semanticKeys=[],fields=[],blockedBy=[])=>({kind:'semantic',code,message,source_refs:[],semantic_keys:[...new Set(semanticKeys)],affected_semantic_fields:[...new Set(fields)],blocked_by:[...new Set(blockedBy)],minimal_change:message});

function unavailableExecutionReferences(value){
  if(typeof value!=='string')return [];
  const text=value.replaceAll('\\','/'),references=[];
  for(const pattern of [
    /(?:^|[^A-Za-z0-9_./-])(?:\.\/)?(analysis\/(?:request|review-request)\.txt)(?=$|[^A-Za-z0-9_./-])/gi,
    /(?:^|[^A-Za-z0-9_./-])(?:\.\/)?(__authoring__\/[A-Za-z0-9_./-]+)/gi,
    /(?:^|[^A-Za-z0-9_./-])(?:\.\/)?(source\/(?:SKILL|WORKFLOW)\.md)(?=$|[^A-Za-z0-9_./-])/gi,
  ])for(const match of text.matchAll(pattern))references.push(match[1]);
  return [...new Set(references)];
}

/** Collects independent semantic defects before lowering so one patch can address them together. */
export function collectSemanticBlueprintFindings(blueprint,{sectionIds=null,sectionInventory=null,contractIds=null,hostToolContracts=[]}={}){
  const findings=semanticLoopFindings(blueprint),collections=['activities','approvals','sequences','parallels','choices'];
  const entries=collections.flatMap(collection=>(blueprint?.[collection]??[]).map(item=>({collection,key:item?.key,item})));
  const keys=new Map();for(const entry of entries){const prior=keys.get(entry.key);if(prior)findings.push(diagnostic('duplicate_key',`Semantic key ${entry.key} is duplicated in ${prior.collection} and ${entry.collection}`,[entry.key],[`${prior.collection}.key`,`${entry.collection}.key`]));else keys.set(entry.key,entry);}
  const known=new Set(entries.map(entry=>entry.key));
  const activityMap=new Map((blueprint?.activities??[]).map(item=>[item.key,item]));
  const inventoryById=sectionInventory?new Map(sectionInventory.map(item=>[item.section_id,item])):null;
  for(const [collection,items,field] of [['activities',blueprint?.activities??[],'instructions'],['approvals',blueprint?.approvals??[],'question']])for(const item of items){
    for(const reference of unavailableExecutionReferences(item?.[field])){
      const message=`${collection==='activities'?'Activity':'Approval'} ${item.key} ${field} references ${reference}, which is unavailable in a deployed Workflow; preserve the required source meaning in complete instructions and use declared pinned supporting resources only`;
      const finding=diagnostic('authoring_only_execution_reference',message,[item.key],[`${collection}.${item.key}.${field}`]);
      finding.source_refs=[...new Map((item.source_sections??[]).map(id=>inventoryById?.get(id)?.source_span).filter(Boolean).map(span=>[`${span.resource}:${span.start_line}:${span.end_line}`,structuredClone(span)])).values()];
      findings.push(finding);
    }
  }
  const dependencyKeys=new Set();
  for(const dependency of blueprint?.runtime_dependencies??[]){
    const field=`runtime_dependencies.${dependency?.key??'<unknown>'}`;
    if(dependencyKeys.has(dependency.key))findings.push(diagnostic('runtime_dependency_duplicate',`Runtime dependency key ${dependency.key} is duplicated`,[dependency.key],[`${field}.key`]));
    dependencyKeys.add(dependency.key);
    if(inventoryById&&!inventoryById.has(dependency.source_section))findings.push(diagnostic('runtime_dependency_section',`Runtime dependency ${dependency.key} cites unknown source section ${dependency.source_section}`,[dependency.key],[`${field}.source_section`]));
    if(dependency.phase!=='unconditional'&&!(typeof dependency.trigger==='string'&&dependency.trigger.trim()))findings.push(diagnostic('runtime_dependency_trigger',`Runtime dependency ${dependency.key} needs its source trigger`,[dependency.key],[`${field}.trigger`]));
    for(const key of dependency.activity_keys??[])if(!activityMap.has(key))findings.push(diagnostic('runtime_dependency_activity',`Runtime dependency ${dependency.key} names unknown activity ${key}`,[dependency.key,key],[`${field}.activity_keys`]));
  }
  if(inventoryById){
    const seen=new Set();
    for(const item of blueprint?.source_dispositions??[]){
      const section=inventoryById.get(item?.section_id);
      if(!section)findings.push(diagnostic('source_disposition_unknown',`Source disposition names unknown section ${item?.section_id}`,[item?.section_id],['source_dispositions']));
      else if(seen.has(item.section_id))findings.push(diagnostic('source_disposition_duplicate',`Source section ${item.section_id} is classified more than once`,[item.section_id],[`source_dispositions.${item.section_id}`]));
      else {
        seen.add(item.section_id);
        if(section.authority==='required'&&!['workflow','conditional'].includes(item.disposition))findings.push(diagnostic('source_disposition_required',`Required source section ${item.section_id} must be workflow or conditional, not ${item.disposition}`,[item.section_id],[`source_dispositions.${item.section_id}.disposition`]));
        if(['workflow','conditional','reference'].includes(item.disposition)&&!(item.activity_keys??[]).length)findings.push(diagnostic('source_disposition_unmapped',`Retained source section ${item.section_id} must name at least one responsible activity`,[item.section_id],[`source_dispositions.${item.section_id}.activity_keys`]));
        for(const key of item.activity_keys??[])if(!known.has(key))findings.push(diagnostic('source_disposition_activity_unknown',`Source section ${item.section_id} names unknown semantic component ${key}`,[item.section_id,key],[`source_dispositions.${item.section_id}.activity_keys`]));
        if(item.disposition==='conditional'&&!(typeof item.note==='string'&&item.note.trim()))findings.push(diagnostic('source_disposition_trigger_missing',`Conditional source section ${item.section_id} needs its exact source trigger in note`,[item.section_id],[`source_dispositions.${item.section_id}.note`]));
      }
    }
    for(const section of sectionInventory)if(!seen.has(section.section_id))findings.push(diagnostic('source_disposition_unclassified',`Source section ${section.section_id} has no disposition`,[section.section_id],['source_dispositions']));
  }
  const outputs=new Map((blueprint?.activities??[]).map(item=>[item.key,new Set((item.outputs??[]).map(output=>output.name))]));
  const availableHostTools=new Map();
  for(const raw of hostToolContracts??[]){const contract=validateHostToolContract(raw);availableHostTools.set(contract.id,contract);}
  const hostOwnedPacketProducer=(key,outputName='',requiredFields=[],visiting=new Set())=>{
    const activity=activityMap.get(key);
    if(!activity?.tool||visiting.has(key))return false;
    const next=new Set(visiting);next.add(key);
    const contract=availableHostTools.get(activity.tool),declared=(contract?.host_owned_item_fields??[]).find(item=>item.output===outputName);
    const inputs=declared&&requiredFields.length&&requiredFields.every(field=>declared.fields.includes(field))
      ? declared.from_inputs.map(name=>(activity.inputs??[]).find(input=>input.name===name)).filter(Boolean)
      : activity.inputs??[];
    if(declared&&requiredFields.length&&requiredFields.every(field=>declared.fields.includes(field))&&inputs.length!==declared.from_inputs.length)return false;
    return inputs.every(input=>{
      if(typeof input.from!=='string')return false;
      if(input.from.startsWith('input:'))return true;
      const separator=input.from.indexOf('.');
      return separator>0&&hostOwnedPacketProducer(input.from.slice(0,separator),input.from.slice(separator+1),[],next);
    });
  };
  const consumedOutputs=new Set((blueprint?.activities??[]).flatMap(item=>(item.inputs??[]).map(input=>input.from).filter(from=>typeof from==='string'&&!from.startsWith('input:'))));
  const typeEntries=[...(blueprint?.records??[]).map(item=>({kind:'object',item})),...(blueprint?.lists??[]).map(item=>({kind:'list',item})),...(blueprint?.enums??[]).map(item=>({kind:'enum',item}))];
  const typeKeys=typeEntries.map(entry=>entry.item?.key),typeMap=new Map(typeEntries.map(entry=>[entry.item?.key,entry]));
const primitiveRefs=new Set(['text','string','boolean','number','integer','object','list']);
  if(new Set(typeKeys).size!==typeKeys.length)findings.push(diagnostic('duplicate_data_type',`Named semantic data type keys must be unique`,typeKeys,['records','lists','enums']));
  const knownType=ref=>primitiveRefs.has(ref)||typeMap.has(ref);
  const hostOwnedOutputFields=output=>{
    const found=new Set(),visiting=new Set();
    const visit=(name,ref,prefix)=>{
      // A decision output named "path" means a semantic branch, not a file
      // location. Nested/string path fields remain Host-owned coordinates.
      if(hostOwnedAgentField(name)&&!(prefix===''&&name==='path'&&output.kind==='enum'))found.add(prefix+name);
      if(!ref||visiting.has(ref))return;
      const entry=typeMap.get(ref);if(!entry)return;
      visiting.add(ref);
      if(entry.kind==='object')for(const field of entry.item.fields??[])visit(field.name,field.type,`${prefix}${name}.`);
      else if(entry.kind==='list')visit('item',entry.item.item_type,`${prefix}${name}.`);
      visiting.delete(ref);
    };
    visit(output.name,output.type_ref,'');return [...found];
  };
  for(const {kind,item} of typeEntries){
    if(kind==='object')for(const field of item?.fields??[])if(!knownType(field.type))findings.push(diagnostic('unknown_data_type',`Record ${item.key} field ${field.name} references unknown semantic data type ${field.type}`,[item.key],[`records.${item.key}.fields.${field.name}.type`]));
    if(kind==='list'&&!knownType(item?.item_type))findings.push(diagnostic('unknown_data_type',`List ${item.key} references unknown semantic item type ${item?.item_type}`,[item.key],[`lists.${item.key}.item_type`]));
  }
  for(const activity of blueprint?.activities??[]){
    const copiedClauses=activity.tool?[]:agentTranscriptionClauses(activity.instructions);
    if(copiedClauses.length)findings.push(diagnostic('agent_deterministic_transcription',`Activity ${activity.key} instructions require an Agent to reproduce pre-existing values. Bind the original input alongside the Agent's newly created semantic result, or copy/join it with a registered Host tool.`,[activity.key],[`activities.${activity.key}.instructions`,'activities.inputs']));
    for(const output of activity.outputs??[]){
      if(output.type_ref&&!output.contract_ref&&!knownType(output.type_ref))findings.push(diagnostic('unknown_data_type',`Activity ${activity.key} output ${output.name} references unknown semantic data type ${output.type_ref}`,[activity.key],[`activities.${activity.key}.outputs.${output.name}.type_ref`]));
      if(Object.hasOwn(output,'host_validation')&&output.host_validation!==WORKSPACE_SOURCE_LOCATIONS)findings.push(diagnostic('unknown_output_host_validation',`Activity ${activity.key} output ${output.name} has unsupported Host validation ${String(output.host_validation)}`,[activity.key],[`activities.${activity.key}.outputs.${output.name}.host_validation`]));
      if(output.host_validation===WORKSPACE_SOURCE_LOCATIONS&&(output.kind!=='list'||output.type_ref||output.contract_ref||output.values?.length||activity.tool||(activity.fanout&&activity.fanout.result_output!==output.name)))findings.push(diagnostic('workspace_source_locations_shape',`Activity ${activity.key} output ${output.name} must be a plain Agent-produced list retained as the joined output`,[activity.key],[`activities.${activity.key}.outputs.${output.name}.host_validation`,`activities.${activity.key}.outputs.${output.name}.kind`,`activities.${activity.key}.outputs.${output.name}.type_ref`,`activities.${activity.key}.outputs.${output.name}.contract_ref`]));
      if(output.host_validation===WORKSPACE_SOURCE_LOCATIONS&&!consumedOutputs.has(`${activity.key}.${output.name}`))findings.push(diagnostic('workspace_source_locations_handoff',`Activity ${activity.key} output ${output.name} needs an explicit successor input binding`,[activity.key],[`activities.${activity.key}.outputs.${output.name}.host_validation`,`activities.inputs`]));
      const copied=activity.tool?[]:hostOwnedOutputFields(output);
      if(copied.length&&output.host_validation!==WORKSPACE_SOURCE_LOCATIONS)findings.push(diagnostic('agent_deterministic_transcription',`Activity ${activity.key} asks an Agent to transcribe Host-owned identity or location fields: ${copied.join(', ')}. Bind these values directly from Workflow inputs or a registered Host tool; keep only new semantic content in the Agent output.`,[activity.key],[`activities.${activity.key}.outputs.${output.name}`,'activities.inputs']));
    }
  }
  const typeChildren=new Map(typeEntries.map(({kind,item})=>[item.key,kind==='object'?(item.fields??[]).map(field=>field.type).filter(ref=>typeMap.has(ref)):kind==='list'&&typeMap.has(item.item_type)?[item.item_type]:[]]));
  const typeVisiting=new Set(),typeVisited=new Set();
  const visitType=key=>{if(typeVisiting.has(key)){findings.push(diagnostic('data_type_cycle',`Semantic data types contain a cycle at ${key}`,[key],['records','lists']));return;}if(typeVisited.has(key))return;typeVisiting.add(key);for(const child of typeChildren.get(key)??[])visitType(child);typeVisiting.delete(key);typeVisited.add(key);};
  for(const key of typeMap.keys())visitType(key);
  const references=[];
  for(const item of blueprint?.sequences??[])for(const member of item.members??[])references.push({owner:item.key,value:member,field:'sequences.members'});
  for(const item of blueprint?.parallels??[])for(const member of item.members??[])references.push({owner:item.key,value:member,field:'parallels.members'});
  for(const item of blueprint?.choices??[]){references.push({owner:item.key,value:item.decision_activity,field:'choices.decision_activity'},{owner:item.key,value:item.default_body,field:'choices.default_body'});for(const branch of item.branches??[])references.push({owner:item.key,value:branch.body,field:'choices.branches.body'});}
  for(const ref of references)if(!known.has(ref.value))findings.push(diagnostic('unknown_component',`Unknown semantic component ${ref.value}`,[ref.owner,ref.value],[ref.field]));
  for(const activity of blueprint?.activities??[]){
    for(const input of activity.inputs??[]){
      if(typeof input.from!=='string'||input.from.startsWith('input:')||semanticLoopReference(input.from))continue;
      const separator=input.from.indexOf('.'),producer=input.from.slice(0,separator),output=input.from.slice(separator+1);
      if(separator<1||!activityMap.has(producer))findings.push(diagnostic('unknown_input_producer',`Activity ${activity.key} input ${input.name} references unknown producer ${producer||input.from}`,[activity.key,producer],[`activities.${activity.key}.inputs`]));
      else if(!outputs.get(producer)?.has(output))findings.push(diagnostic('unknown_input_output',`Activity ${activity.key} input ${input.name} references unknown output ${input.from}`,[activity.key,producer],[`activities.${activity.key}.inputs`,`activities.${producer}.outputs`]));
    }
    if(sectionIds)for(const section of activity.source_sections??[])if(!sectionIds.has(section))findings.push(diagnostic('unknown_source_section',`Activity ${activity.key} cites unknown source section ${section}`,[activity.key],[`activities.${activity.key}.source_sections`]));
    if(contractIds){for(const contract of activity.contract_refs??[])if(!contractIds.has(contract))findings.push(diagnostic('unknown_source_contract',`Activity ${activity.key} selects unknown source contract ${contract}`,[activity.key],[`activities.${activity.key}.contract_refs`]));for(const output of activity.outputs??[])if(output.contract_ref&&!contractIds.has(output.contract_ref))findings.push(diagnostic('unknown_output_contract',`Activity ${activity.key} output ${output.name} selects unknown source contract ${output.contract_ref}`,[activity.key],[`activities.${activity.key}.outputs`]));}
    const outputCount=(activity.outputs??[]).length,review=activity.profile==='review',decision=activity.profile==='decision';
    const outcome=activity.outcome??(decision?'decision':review?'review':outputCount?'artifact':'none');
    // Profile owns execution authority; outcome describes a result. Whether
    // that result really constitutes review or a decision is source semantics
    // for independent review, not a mechanical reason to reject a plan.
    if(outcome==='none'&&outputCount)findings.push(diagnostic('activity_none_with_outputs',`Activity ${activity.key} declares outcome none but also declares outputs`,[activity.key],[`activities.${activity.key}.outcome`,`activities.${activity.key}.outputs`]));
    if(['artifact','validated_artifact','decision'].includes(outcome)&&!outputCount)findings.push(diagnostic('activity_output_missing',`Activity ${activity.key} outcome ${outcome} needs at least one declared output`,[activity.key],[`activities.${activity.key}.outcome`,`activities.${activity.key}.outputs`]));
    if(new Set(activity.fail_on_false??[]).size!==(activity.fail_on_false??[]).length)findings.push(diagnostic('duplicate_false_guard',`Activity ${activity.key} repeats a false-result guard`,[activity.key],[`activities.${activity.key}.fail_on_false`]));
    for(const name of activity.fail_on_false??[])if((activity.outputs??[]).find(output=>output.name===name)?.kind!=='boolean')findings.push(diagnostic('invalid_false_guard',`Activity ${activity.key} false-result guard ${name} must name a declared boolean output`,[activity.key],[`activities.${activity.key}.fail_on_false`,`activities.${activity.key}.outputs`]));
    if(activity.fanout){
      const input=(activity.inputs??[]).find(item=>item.name===activity.fanout.input),output=(activity.outputs??[]).find(item=>item.name===activity.fanout.result_output);
      if((activity.fail_on_false??[]).length)findings.push(diagnostic('fanout_false_guard',`Activity ${activity.key} fan-out has only the joined list as a top-level output; validate all item results in a following aggregate activity with a boolean output and fail_on_false`,[activity.key],[`activities.${activity.key}.fanout`,`activities.${activity.key}.fail_on_false`,`activities.${activity.key}.outputs`]));
      if(!String(activity.profile??'').startsWith('worker_'))findings.push(diagnostic('fanout_owner',`Activity ${activity.key} fan-out must use an isolated worker profile; Main activities cannot configure sub-Agent quantity`,[activity.key],[`activities.${activity.key}.profile`,`activities.${activity.key}.fanout`]));
      if(activity.tool||review||decision)findings.push(diagnostic('fanout_activity_kind',`Activity ${activity.key} fan-out applies only to ordinary Agent work`,[activity.key],[`activities.${activity.key}.tool`,`activities.${activity.key}.profile`,`activities.${activity.key}.fanout`]));
      if(!input)findings.push(diagnostic('fanout_input_missing',`Activity ${activity.key} fan-out input ${activity.fanout.input} is not a declared activity input`,[activity.key],[`activities.${activity.key}.fanout.input`,`activities.${activity.key}.inputs`]));
      else if(!input.from.startsWith('input:')){const separator=input.from.indexOf('.'),producer=activityMap.get(input.from.slice(0,separator)),produced=producer?.outputs?.find(item=>item.name===input.from.slice(separator+1));if(produced&&produced.kind!=='list')findings.push(diagnostic('fanout_input_type',`Activity ${activity.key} fan-out input ${activity.fanout.input} must consume a list output`,[activity.key,producer.key],[`activities.${activity.key}.fanout.input`,`activities.${producer.key}.outputs`]));}
      if(!output||output.kind!=='list')findings.push(diagnostic('fanout_result_type',`Activity ${activity.key} fan-out result ${activity.fanout.result_output} must be a declared list output`,[activity.key],[`activities.${activity.key}.fanout.result_output`,`activities.${activity.key}.outputs`]));
      if(activity.fanout.count_mode==='auto'&&activity.fanout.fixed_count!==0)findings.push(diagnostic('fanout_auto_count',`Activity ${activity.key} automatic fan-out must use fixed_count 0`,[activity.key],[`activities.${activity.key}.fanout.fixed_count`]));
      if(activity.fanout.count_mode==='fixed'&&activity.fanout.fixed_count<1)findings.push(diagnostic('fanout_fixed_count',`Activity ${activity.key} fixed fan-out must use a count from 1 to 32`,[activity.key],[`activities.${activity.key}.fanout.fixed_count`]));
      if(activity.fanout.batch_size!==undefined&&(activity.fanout.count_mode!=='auto'||activity.fanout.fixed_count!==0))findings.push(diagnostic('fanout_batch_count',`Activity ${activity.key} batch_size requires automatic count with fixed_count 0; the Host derives the number of batches from the input list`,[activity.key],[`activities.${activity.key}.fanout.batch_size`,`activities.${activity.key}.fanout.count_mode`,`activities.${activity.key}.fanout.fixed_count`]));
      if(activity.fanout.item_delivery!==undefined&&(activity.fanout.item_delivery!=='incremental'||activity.fanout.result_mode!=='per_item'||!Number.isInteger(activity.fanout.batch_size)||activity.fanout.batch_size<2))findings.push(diagnostic('fanout_item_delivery',`Activity ${activity.key} incremental item delivery requires per_item admission and a batch_size of at least 2`,[activity.key],[`activities.${activity.key}.fanout.item_delivery`,`activities.${activity.key}.fanout.result_mode`,`activities.${activity.key}.fanout.batch_size`]));
      if(activity.fanout.write_paths_field!==undefined&&!String(activity.profile??'').endsWith('_write'))findings.push(diagnostic('fanout_write_paths_profile',`Activity ${activity.key} write_paths_field requires a write-capable worker profile`,[activity.key],[`activities.${activity.key}.fanout.write_paths_field`,`activities.${activity.key}.profile`]));
      if(String(activity.profile??'').endsWith('_write')&&activity.fanout.max_concurrency!==1&&activity.fanout.write_paths_field===undefined)findings.push(diagnostic('fanout_write_isolation',`Activity ${activity.key} can run concurrent writers but has no Host-owned per-item write paths. Add write_paths_field backed by a Workflow input or Host tool, or set max_concurrency to 1.`,[activity.key],[`activities.${activity.key}.fanout.write_paths_field`,`activities.${activity.key}.max_concurrency`,`activities.${activity.key}.profile`]));
      if(activity.fanout.write_paths_field!==undefined&&input){
        const separator=input.from.indexOf('.'),producerKey=separator>0?input.from.slice(0,separator):'';
        const loopRef=semanticLoopReference(input.from),loop=loopRef&&(blueprint.loops??[]).find(item=>item.key===loopRef.key),original=loop?.item_scope?.items;
        const loopOwned=loop&&['repair_items','review_items'].includes(loopRef.output)&&loop.item_scope.paths_field===activity.fanout.write_paths_field&&typeof original==='string'&&(original.startsWith('input:')||hostOwnedPacketProducer(original.split('.')[0],original.slice(original.indexOf('.')+1),[activity.fanout.write_paths_field]));
        const hostOwned=loopOwned||input.from.startsWith('input:')||producerKey&&hostOwnedPacketProducer(producerKey,input.from.slice(separator+1),[activity.fanout.write_paths_field]);
        if(!hostOwned)findings.push(diagnostic('fanout_host_item_source',`Activity ${activity.key} uses Host-owned per-item write paths, but ${producerKey||input.name} depends on Agent output. Bind the fan-out list directly from a Workflow input or from Host tools whose inputs are themselves Host-owned.`,[activity.key,...(producerKey?[producerKey]:[])],[`activities.${activity.key}.inputs.${activity.fanout.input}`,`activities.${activity.key}.fanout.write_paths_field`]));
      }
      if(activity.fanout.shared_change_field!==undefined){
        if(activity.fanout.result_mode!=='per_item'||activity.fanout.write_paths_field===undefined)findings.push(diagnostic('fanout_shared_change_contract',`Activity ${activity.key} shared_change_field requires path-isolated per-item results`,[activity.key],[`activities.${activity.key}.fanout.shared_change_field`,`activities.${activity.key}.fanout.result_mode`,`activities.${activity.key}.fanout.write_paths_field`]));
        const consumers=(blueprint.activities??[]).filter(candidate=>String(candidate.profile??'').endsWith('_write')&&(candidate.inputs??[]).some(input=>input.from===`${activity.key}.${activity.fanout.result_output}`));
        if(consumers.length!==1)findings.push(diagnostic('fanout_shared_change_handoff',`Activity ${activity.key} declares shared changes but does not have exactly one later write activity consuming its joined result`,[activity.key,...consumers.map(candidate=>candidate.key)],[`activities.${activity.key}.fanout.shared_change_field`,`activities.inputs`]));
        else{
          const consumer=consumers[0],guarded=(consumer.fail_on_false??[]).some(name=>(consumer.outputs??[]).some(output=>output.name===name&&output.kind==='boolean'));
          if(!guarded)findings.push(diagnostic('fanout_shared_change_completion',`Shared-change owner ${consumer.key} must expose a required boolean success output and name it in fail_on_false`,[activity.key,consumer.key],[`activities.${consumer.key}.outputs`,`activities.${consumer.key}.fail_on_false`]));
        }
      }
    }
  }
  for(const gate of blueprint?.approvals??[]){
    if(!gate.subject)findings.push(diagnostic('approval_subject_missing',`Approval ${gate.key} must name the exact activity.output being approved`,[gate.key],[`approvals.${gate.key}.subject`]));
    else {const separator=gate.subject.indexOf('.'),producer=gate.subject.slice(0,separator),output=gate.subject.slice(separator+1);if(separator<1||!outputs.get(producer)?.has(output))findings.push(diagnostic('approval_subject_unknown',`Approval ${gate.key} references unknown subject ${gate.subject}`,[gate.key,producer],[`approvals.${gate.key}.subject`]));}
    if(!Array.isArray(gate.before)||!gate.before.length)findings.push(diagnostic('approval_boundary_missing',`Approval ${gate.key} must name at least one activity it authorizes`,[gate.key],[`approvals.${gate.key}.before`]));
    else for(const target of gate.before)if(!activityMap.has(target))findings.push(diagnostic('approval_boundary_unknown',`Approval ${gate.key} names unknown authorized activity ${target}`,[gate.key,target],[`approvals.${gate.key}.before`]));
  }
  const children=new Map([...(blueprint?.sequences??[]).map(item=>[item.key,[...new Set(item.members??[])]]),...(blueprint?.parallels??[]).map(item=>[item.key,[...new Set(item.members??[])]]),...(blueprint?.choices??[]).map(item=>[item.key,[...new Set([item.decision_activity,item.default_body,...(item.branches??[]).map(branch=>branch.body)].filter(Boolean))]])]);
  const referenced=new Set([...children.values()].flat()),roots=[...known].filter(key=>!referenced.has(key));
  const closure=root=>{const found=new Set(),queue=[root];while(queue.length){const key=queue.shift();if(found.has(key)||!known.has(key))continue;found.add(key);queue.push(...(children.get(key)??[]));}return found;};
  const closures=new Map(roots.map(root=>[root,closure(root)]));
  for(let left=0;left<roots.length;left++)for(let right=left+1;right<roots.length;right++){const overlap=[...closures.get(roots[left])].filter(key=>closures.get(roots[right]).has(key));if(overlap.length)findings.push(diagnostic('top_level_overlap',`Top-level semantic groups overlap: ${roots[left]} and ${roots[right]} through ${overlap.join(', ')}. Nest each owning group instead of repeating its members`,[roots[left],roots[right],...overlap],['sequences','parallels','choices']));}
  const visiting=new Set(),visited=new Set();
  const visit=key=>{if(visiting.has(key)){findings.push(diagnostic('control_cycle',`Semantic control groups contain a cycle at ${key}`,[key],['sequences','parallels','choices']));return;}if(visited.has(key)||!known.has(key))return;visiting.add(key);for(const child of children.get(key)??[])visit(child);visiting.delete(key);visited.add(key);};
  for(const key of known)visit(key);
  // Approval topology is semantic author intent. Validate every gate together
  // before lowering so independent ordering omissions consume one targeted
  // repair instead of one model round per fail-fast reachability assertion.
  if(!findings.some(item=>['unknown_component','control_cycle','duplicate_key'].includes(item.code))){
    const sequences=new Map((blueprint?.sequences??[]).map(item=>[item.key,item])),parallels=new Map((blueprint?.parallels??[]).map(item=>[item.key,item])),choices=new Map((blueprint?.choices??[]).map(item=>[item.key,item]));
    const approvals=new Map((blueprint?.approvals??[]).map(item=>[item.key,item])),edges=new Map(),resolved=new Map(),resolving=new Set();
    const connect=(sources,targets)=>{for(const source of sources)for(const target of targets){const outgoing=edges.get(source)??new Set();outgoing.add(target);edges.set(source,outgoing);}};
    const resolveComponent=key=>{
      if(resolved.has(key))return resolved.get(key);
      if(resolving.has(key)||!known.has(key))return null;
      if(activityMap.has(key)||approvals.has(key)){const leaf={entries:[key],exits:[key]};resolved.set(key,leaf);return leaf;}
      resolving.add(key);let result=null;
      if(sequences.has(key)){
        const parts=(sequences.get(key).members??[]).map(resolveComponent);
        if(parts.length&&parts.every(Boolean)){for(let index=1;index<parts.length;index++)connect(parts[index-1].exits,parts[index].entries);result={entries:parts[0].entries,exits:parts.at(-1).exits};}
      }else if(parallels.has(key)){
        const parts=(parallels.get(key).members??[]).map(resolveComponent);
        if(parts.length&&parts.every(Boolean))result={entries:parts.flatMap(item=>item.entries),exits:parts.flatMap(item=>item.exits)};
      }else if(choices.has(key)){
        const choice=choices.get(key),decision=resolveComponent(choice.decision_activity),bodies=[...(choice.branches??[]).map(item=>item.body),choice.default_body].filter((item,index,all)=>item&&all.indexOf(item)===index).map(resolveComponent);
        if(decision&&bodies.length&&bodies.every(Boolean)){for(const body of bodies)connect(decision.exits,body.entries);result={entries:decision.entries,exits:bodies.flatMap(item=>item.exits)};}
      }
      resolving.delete(key);if(result)resolved.set(key,result);return result;
    };
    for(const root of roots)resolveComponent(root);
    const reaches=(source,target)=>{const seen=new Set(),queue=[source];while(queue.length){const current=queue.shift();if(current===target)return true;if(seen.has(current))continue;seen.add(current);queue.push(...(edges.get(current)??[]));}return false;};
    for(const gate of blueprint?.approvals??[]){
      const separator=gate.subject?.indexOf('.')??-1,producer=separator>0?gate.subject.slice(0,separator):null;
      if(producer&&outputs.get(producer)?.has(gate.subject.slice(separator+1))&&!reaches(producer,gate.key))findings.push(diagnostic('approval_subject_order',`Approval ${gate.key} must occur after its subject ${gate.subject}; place ${producer} and ${gate.key} on one explicit forward control path`,[producer,gate.key],[`sequences`,`parallels`,`choices`,`approvals.${gate.key}`]));
      for(const target of gate.before??[])if(activityMap.has(target)&&!reaches(gate.key,target))findings.push(diagnostic('approval_boundary_order',`Approval ${gate.key} must occur before ${target}; place ${gate.key} and ${target} on one explicit forward control path`,[gate.key,target],[`sequences`,`parallels`,`choices`,`approvals.${gate.key}`]));
    }
  }
  return [...new Map(findings.map(item=>[`${item.code}:${item.message}`,item])).values()];
}

// A planner may name an approval-plus-target sequence yet point a choice at
// the bare target. When that wrapper is unique and otherwise unreferenced,
// the Host can connect the declared gate without inventing a new decision.
function connectUniqueApprovalWrappers(value){
  const blueprint=structuredClone(value),activities=new Set((blueprint.activities??[]).map(item=>item.key));
  for(const wrapper of blueprint.sequences??[]){
    if(wrapper.members?.length!==2)continue;
    const [gateKey,target]=wrapper.members,gate=(blueprint.approvals??[]).find(item=>item.key===gateKey);
    if(!gate?.before?.includes(target)||!activities.has(target))continue;
    const otherGroupReferences=[...(blueprint.sequences??[]).filter(item=>item.key!==wrapper.key),...(blueprint.parallels??[])].flatMap(item=>item.members??[]);
    if(otherGroupReferences.includes(wrapper.key)||otherGroupReferences.includes(gateKey)||otherGroupReferences.includes(target))continue;
    const matchingChoices=(blueprint.choices??[]).filter(item=>item.default_body===target||item.branches?.some(branch=>branch.body===target));
    if(matchingChoices.length!==1||matchingChoices[0].decision_activity===target)continue;
    const choice=matchingChoices[0];
    choice.branches=choice.branches.map(branch=>branch.body===target?{...branch,body:wrapper.key}:branch);
    if(choice.default_body===target)choice.default_body=wrapper.key;
  }
  return blueprint;
}

function materializeUniqueApprovalBoundaries(value){
  const blueprint=structuredClone(value),activities=new Set((blueprint.activities??[]).map(item=>item.key));
  const used=new Set([...(blueprint.activities??[]),...(blueprint.approvals??[]),...(blueprint.sequences??[]),...(blueprint.parallels??[]),...(blueprint.choices??[])].map(item=>item.key));
  const groups=[...(blueprint.sequences??[]),...(blueprint.parallels??[])];
  for(const gate of blueprint.approvals??[]){
    if(gate.before?.length!==1||!activities.has(gate.before[0]))continue;
    const target=gate.before[0];
    if((blueprint.approvals??[]).filter(item=>item.before?.includes(target)).length!==1)continue;
    const gateReferenced=groups.some(group=>group.members?.includes(gate.key))||(blueprint.choices??[]).some(choice=>choice.default_body===gate.key||choice.branches?.some(branch=>branch.body===gate.key));
    if(gateReferenced)continue;
    const references=[...groups.filter(group=>group.members?.includes(target)).map(group=>({kind:'group',group})),...(blueprint.choices??[]).flatMap(choice=>[...(choice.default_body===target?[{kind:'default',choice}]:[]),...(choice.branches??[]).filter(branch=>branch.body===target).map(branch=>({kind:'branch',branch}))])];
    if(references.length>1||(blueprint.choices??[]).some(choice=>choice.decision_activity===target))continue;
    let key=`host_gate_${blueprint.sequences.length+1}`;
    while(used.has(key))key+='_';used.add(key);
    blueprint.sequences.push({key,members:[gate.key,target],failure_meaning:'all_required'});
    for(const ref of references){if(ref.kind==='group')ref.group.members=ref.group.members.map(member=>member===target?key:member);else if(ref.kind==='default')ref.choice.default_body=key;else ref.branch.body=key;}
  }
  return blueprint;
}

export function assertSemanticBlueprint(blueprint,options={}){
  if(blueprint?.contract===SEMANTIC_BLUEPRINT_CONTRACT)blueprint=connectUniqueApprovalWrappers(materializeUniqueApprovalBoundaries(blueprint));
  // A write fan-out without Host-derived per-item paths cannot run multiple
  // writers safely. This is an execution mechanic, so the Host serializes it
  // instead of spending another model turn on a protocol-only repair.
  for(const activity of blueprint?.activities??[])if(
    activity?.fanout
    &&String(activity.profile??'').endsWith('_write')
    &&activity.fanout.write_paths_field===undefined
  )activity.fanout.max_concurrency=1;
  if(options.sectionInventory){
    const required=new Set(options.sectionInventory.filter(item=>item.authority==='required').map(item=>item.section_id));
    blueprint.source_dispositions=(blueprint.source_dispositions??[]).map(item=>required.has(item.section_id)&&item.disposition==='reference'&&item.activity_keys?.length?{...item,disposition:'workflow'}:item);
  }
  const initial=collectSemanticBlueprintFindings(blueprint,options);
  const structural=new Set(['unknown_component','unknown_input_producer','top_level_overlap','control_cycle','duplicate_key']);
  let findings=initial;
  if(!initial.some(item=>structural.has(item.code))){
    blueprint.sequences=derivedRoot(blueprint).sequences;
    findings=collectSemanticBlueprintFindings(blueprint,options);
  }
  if(findings.length)throw Object.assign(new Error(findings.map(item=>item.message).join('; ')),{code:'AUTHORING_SEMANTIC',findings});
  return blueprint;
}

function derivedRoot(blueprint){
  const components=[...(blueprint.activities ?? []),...(blueprint.approvals ?? []),...(blueprint.sequences ?? []),...(blueprint.parallels ?? []),...(blueprint.choices ?? [])].map(item=>item.key);
  const children=new Map([
    ...(blueprint.sequences ?? []).map(item=>[item.key,[...new Set(item.members)]]),
    ...(blueprint.parallels ?? []).map(item=>[item.key,[...new Set(item.members)]]),
    ...(blueprint.choices ?? []).map(item=>[item.key,[...new Set([item.decision_activity,item.default_body,...item.branches.map(branch=>branch.body)])]]),
  ]);
  const referenced=new Set([...children.values()].flat());
  const roots=components.filter(key=>!referenced.has(key));
  if(roots.length===1)return {root:roots[0],sequences:blueprint.sequences};
  if(roots.length>1){
    const closure=root=>{const found=new Set(),queue=[root];while(queue.length){const key=queue.shift();if(found.has(key))continue;found.add(key);queue.push(...(children.get(key) ?? []));}return found;};
    const closures=new Map(roots.map(root=>[root,closure(root)]));
    const overlaps=[];
    for(let left=0;left<roots.length;left++)for(let right=left+1;right<roots.length;right++){
      const overlap=[...closures.get(roots[left])].filter(key=>closures.get(roots[right]).has(key));
      if(overlap.length)overlaps.push(`${roots[left]} and ${roots[right]} through ${overlap.join(', ')}`);
    }
    if(overlaps.length)semanticFail(`Top-level semantic groups overlap: ${overlaps.join('; ')}. Nest each owning group instead of repeating its members`);
    const owner=new Map();for(const root of roots)for(const component of closures.get(root))owner.set(component,root);
    const successors=new Map(roots.map(root=>[root,new Set()])),indegree=new Map(roots.map(root=>[root,0])),reasons=new Map();
    const orderBefore=(from,to,field)=>{
      const producer=owner.get(from),consumer=owner.get(to);
      if(!producer||!consumer||producer===consumer)return;
      const relation=`${producer}\u0000${consumer}`;
      if(!reasons.has(relation))reasons.set(relation,[]);
      reasons.get(relation).push({from,to,field});
      if(successors.get(producer).has(consumer))return;
      successors.get(producer).add(consumer);indegree.set(consumer,indegree.get(consumer)+1);
    };
    for(const activity of blueprint.activities ?? [])for(const input of activity.inputs ?? []){
      if(typeof input.from!=='string'||input.from.startsWith('input:')||semanticLoopReference(input.from))continue;
      const separator=input.from.indexOf('.');if(separator<1)continue;
      orderBefore(input.from.slice(0,separator),activity.key,`activities.${activity.key}.inputs`);
    }
    for(const gate of blueprint.approvals??[]){
      if(typeof gate.subject==='string'&&gate.subject.includes('.'))orderBefore(gate.subject.split('.')[0],gate.key,`approvals.${gate.key}.subject`);
      for(const target of gate.before??[])orderBefore(gate.key,target,`approvals.${gate.key}.before`);
    }
    const ordinal=new Map(roots.map((root,index)=>[root,index])),ready=roots.filter(root=>indegree.get(root)===0),ordered=[];
    while(ready.length){ready.sort((left,right)=>ordinal.get(left)-ordinal.get(right));const root=ready.shift();ordered.push(root);for(const next of successors.get(root)){indegree.set(next,indegree.get(next)-1);if(indegree.get(next)===0)ready.push(next);}}
    if(ordered.length!==roots.length){
      const remaining=new Set(roots.filter(root=>indegree.get(root)>0)),visited=new Set(),active=new Map(),path=[];
      const cycleFrom=root=>{
        visited.add(root);active.set(root,path.length);path.push(root);
        for(const next of successors.get(root)){
          if(!remaining.has(next))continue;
          if(active.has(next))return [...path.slice(active.get(next)),next];
          if(!visited.has(next)){const cycle=cycleFrom(next);if(cycle)return cycle;}
        }
        path.pop();active.delete(root);return null;
      };
      let cycle=null;for(const root of remaining){if(!visited.has(root))cycle=cycleFrom(root);if(cycle)break;}
      const relations=cycle.slice(0,-1).flatMap((root,index)=>reasons.get(`${root}\u0000${cycle[index+1]}`)??[]);
      const message=`Top-level semantic groups contain a data-dependency cycle (${cycle.join(' -> ')}); revise the named input or approval relations`;
      throw Object.assign(new Error(message),{code:'AUTHORING_SEMANTIC',findings:[diagnostic('top_level_dependency_cycle',message,[...cycle,...relations.flatMap(({from,to})=>[from,to])],relations.map(({field})=>field))]});
    }
    let key='host_root_sequence';while(components.includes(key))key='host_'+key;return {root:key,sequences:[...blueprint.sequences,{key,members:ordered,failure_meaning:'all_required'}]};
  }
  semanticFail('Semantic components do not have an acyclic root');
}

// A one-member parallel group carries no concurrency or failure semantics. It
// is a representational redundancy, not a semantic defect worth another model
// call. Collapse it before root derivation and rewrite every group/choice
// reference to the sole member; the compiler still rejects real cycles and
// malformed multi-member parallel regions.
function collapseSingletonParallels(blueprint){
  const replacements=new Map((blueprint.parallels ?? []).filter(item=>item.members.length===1).map(item=>[item.key,item.members[0]]));
  if(!replacements.size)return blueprint;
  const resolve=key=>{
    const seen=new Set();
    while(replacements.has(key)){
      if(seen.has(key))semanticFail('Semantic components do not have an acyclic root');
      seen.add(key);key=replacements.get(key);
    }
    return key;
  };
  const rewriteMembers=items=>items.map(item=>({...item,members:[...new Set(item.members.map(resolve))]}));
  blueprint.sequences=rewriteMembers(blueprint.sequences ?? []);
  blueprint.parallels=rewriteMembers((blueprint.parallels ?? []).filter(item=>!replacements.has(item.key)));
  blueprint.choices=(blueprint.choices ?? []).map(item=>({...item,decision_activity:resolve(item.decision_activity),default_body:resolve(item.default_body),branches:item.branches.map(branch=>({...branch,body:resolve(branch.body)}))}));
  return blueprint;
}

function compactToInternal(value){
  value=collapseSingletonParallels(structuredClone(value));
  const profiles={orchestration_read:{ownership:'main',main_mode:'orchestration',operation:'read',complexity:'routine',kind:'work'},orchestration_write:{ownership:'main',main_mode:'orchestration',operation:'write',complexity:'routine',kind:'work'},main_read:{ownership:'main',operation:'read',complexity:'routine',kind:'work'},main_write:{ownership:'main',operation:'write',complexity:'routine',kind:'work'},worker_read:{ownership:'isolated_worker',operation:'read',complexity:'routine',kind:'work'},worker_write:{ownership:'isolated_worker',operation:'write',complexity:'routine',kind:'work'},worker_complex_read:{ownership:'isolated_worker',operation:'read',complexity:'complex',kind:'work'},worker_complex_write:{ownership:'isolated_worker',operation:'write',complexity:'complex',kind:'work'},review:{ownership:'isolated_worker',operation:'read',complexity:'routine',kind:'review'},decision:{ownership:'main',operation:'read',complexity:'routine',kind:'decision'}};
  const parseInput=item=>{
    if(item.from.startsWith('input:'))return {name:item.name,source_kind:'input',input:item.from.slice(6),activity:'',output:''};
    const loop=semanticLoopReference(item.from);if(loop)return {name:item.name,source_kind:'loop',input:'',activity:'',loop:loop.key,output:loop.output};
    const separator=item.from.indexOf('.');if(separator<1 || separator===item.from.length-1)formatFail(`Activity input ${item.name} must use input:name or activity.output`);
    return {name:item.name,source_kind:'activity',input:'',activity:item.from.slice(0,separator),output:item.from.slice(separator+1)};
  };
  const activities=value.activities.map(item=>{const selected=profiles[item.profile];if(!selected)formatFail(`Unknown activity profile ${item.profile}`);return {key:item.key,purpose:item.key.replaceAll('_',' '),kind:selected.kind,instructions:item.instructions,ownership:selected.ownership,...(selected.main_mode ? {main_mode:selected.main_mode} : {}),operation:selected.operation,complexity:selected.complexity,source_sections:item.source_sections,continues:item.task_continues??'',consumes:item.inputs.map(parseInput),produces:item.outputs.map(output=>({name:output.name,shape:{kind:output.kind,values:output.values,type_ref:output.type_ref},...(output.contract_ref?{contract_ref:output.contract_ref}:{}),...(output.host_validation?{host_validation:output.host_validation}:{})})),capability:{kind:item.tool?'registered_tool':'none',semantic_name:item.tool},...(item.contract_refs?{contract_refs:[...item.contract_refs]}:{}),...(item.on_missing?{on_missing:item.on_missing}:{}),...(item.outcome?{outcome:item.outcome}:{}),...(item.fail_on_false?{fail_on_false:[...item.fail_on_false]}:{}),...(item.repeat_until?{repeat_until:structuredClone(item.repeat_until)}:{}),...(item.fanout?{fanout:structuredClone(item.fanout)}:{})};});
  const root=derivedRoot(value);
  return {contract:PREVIOUS_SEMANTIC_BLUEPRINT_CONTRACT,purpose:value.purpose,source_dispositions:value.source_dispositions.map(item=>({section_id:item.section_id,disposition:item.disposition,activity_keys:item.activity_keys,trigger:item.disposition==='conditional'?item.note:'',reason:item.note})),semantic_rules:[],requirement_assignments:value.requirement_assignments.map(item=>({...item,binding_names:[],runtime_guards:[]})),runtime_dependencies:structuredClone(value.runtime_dependencies??[]),data_types:[
    ...value.records.map(item=>({key:item.key,kind:'object',fields:item.fields.map(field=>({name:field.name,type_ref:field.type,required:field.required})),item_type_ref:'',values:[],openness:item.open?'open':'closed'})),
    ...value.lists.map(item=>({key:item.key,kind:'list',fields:[],item_type_ref:item.item_type,values:[],openness:'closed'})),
    ...value.enums.map(item=>({key:item.key,kind:'enum',fields:[],item_type_ref:'',values:item.values,openness:'closed'})),
  ],activities,loops:structuredClone(value.loops??[]),approvals:structuredClone(value.approvals),sequences:structuredClone(root.sequences),parallels:structuredClone(value.parallels),choices:structuredClone(value.choices),root:root.root};
}

export function normalizeSemanticBlueprint(value,options={}){
  const blueprint=requireUniqueActivityInputs(structuredClone(value));
  if(blueprint?.contract===SEMANTIC_BLUEPRINT_CONTRACT)return compactToInternal(assertSemanticBlueprint(blueprint,options));
  if([PREVIOUS_COMPACT_SEMANTIC_BLUEPRINT_CONTRACT,PREVIOUS_FANOUT_SEMANTIC_BLUEPRINT_CONTRACT].includes(blueprint?.contract)){blueprint.contract=SEMANTIC_BLUEPRINT_CONTRACT;return compactToInternal(blueprint);}
  if(blueprint?.contract===LEGACY_SEMANTIC_BLUEPRINT_CONTRACT){blueprint.contract=PREVIOUS_SEMANTIC_BLUEPRINT_CONTRACT;blueprint.data_types??=[];for(const activity of blueprint.activities ?? [])for(const output of activity.produces ?? [])output.shape.type_ref??='';}
  return collapseSingletonParallels(blueprint);
}

export const SEMANTIC_BLUEPRINT_GUIDE=Object.freeze({
  contract:SEMANTIC_BLUEPRINT_CONTRACT,
  purpose:'Describe only preserved task meaning. The Host compiles every Workflow mechanic.',
  activities:'Each activity has concise, complete operational instructions, one semantic execution profile, cited source sections, compact inputs (input:name or activity.output), outputs and an optional exact registered tool name. Project-memory, progress, decision-log, open-question and checkpoint documents are executor bookkeeping; never create a product artifact, completion gate or standalone activity for them. Root inputs carry human semantic requirements or a local material address. Existing JSON, manifests, record lists and other structured machine data are read from that address by a registered Host tool; never design a launch contract that makes the calling Agent open a file and transcribe its fields. Preserve the necessary source meaning in each execution instruction and approval question: the generated analysis/request.txt and analysis/review-request.txt packets, __authoring__ resources, and source/SKILL.md or source/WORKFLOW.md entrypoint are unavailable after deployment. Do not tell a future executor to reread them instead of stating the task. Named pinned supporting scripts remain available. main_read/main_write activities use Main (worker): fresh Host-owned sessions with declared inputs and pinned resources. orchestration_read/orchestration_write use Main (orchestration): the initiating conversation and its existing working context, only when that context is required. Integration alone does not require orchestration if its needed conclusions can be handed off explicitly. Worker and review profiles use one-off Provider sub-Agents. A Codex task is a separate durable task/thread and must not be inferred from a worker profile, fan-out, or project-memory artifact. Select only resolved Host source-contract IDs as exact contract_refs or output contract_ref; candidate observations are reading evidence, not output schemas. Use a write-capable profile for ordinary work by default, including planning or validation that may create evidence, update files or repair defects; choose read only when this activity is truly inspection-only and can finish its own output without any file mutation. The overall task may require writing in a later activity, which is not itself a blocker for an inspection-only activity. Use on_missing block when explicit inputs exist and name the semantic outcome. Independent read-only review uses profile review; review-and-repair keeps a write-capable profile even when its outcome is review. Use repeat_until {condition,max_attempts} only for a local activity or transport retry when exhausting the source-bounded retry is itself failure; downstream semantic review rejection requires a real structured loop, never repeat_until; if the source requires delivering a partial result after exhaustion, expose that outcome and branch to delivery instead. If a declared boolean validation output must be true for success, list its name in fail_on_false; the Host enforces this deterministically. For runtime-cardinality work, add fanout {input,item_name,result_output,count_mode,fixed_count}, optionally batch_size and max_concurrency (each 1-32). auto uses fixed_count 0: without batch_size it assigns one item per Agent; an explicit batch_size partitions consecutive items without inventing a batch size. fixed uses 1-32 Agents and cannot specify batch_size. max_concurrency bounds active Agents independently of the total item or batch count; specify it when the total can exceed 32. Choose batch size from the task contract, never activity names. result_mode per_item gives one worker the whole batch on its first turn, journals every valid entry, and sends only unresolved entries on repair turns. Add item_delivery incremental only when the source explicitly requires Host acceptance of each item before the worker starts the next item; it releases one item per turn to the same recorded Agent. For independent writing items whose Host-produced input record contains an exact path list, set write_paths_field to that record field; its fan-out input must come directly from a Workflow input or an exact registered Host tool. When those isolated workers can discover required shared-file changes, set shared_change_field to the required per-item result field and bind the joined result to exactly one later write activity that owns shared integration, returns a required boolean success output and guards it with fail_on_false. The compiler rejects an Agent-produced task packet, an ambiguous or unconsumed shared-change handoff, and an unguarded shared-write owner before publication. The Host gives each child only those destinations and accepts absolute or workspace-relative entries. Fan-out is valid only on worker profiles. Its single joined structured result output is a list; put per-item evidence inside each list item or referenced artifacts, not in separate top-level outputs. Agent outputs contain only newly produced semantic values. They never repeat any unchanged input or resource value, regardless of field name or representation, inside structured fields or free text. This includes IDs, paths, hashes, labels, names, source text, tokens, indices, revisions, receipts and timestamps. Return batched findings in input order; bind the original items alongside those findings for a later consumer, or use a registered Host tool to copy, transform or join pre-existing values. Cite source sections instead of repeating interface prose.',
  execution_binding:'Default ordinary sequential activities to Main. Main is a fresh Host-owned isolated session, not the controlling conversation; it receives only declared inputs and pinned resources. Choose workers for source-required independent responsibility, parallel work, an explicit registered Provider/model, or a durable task identity. Use an available registered tool for mechanical aggregation or validation when its exact contract fits. A separate Codex task is appropriate only when source meaning requires a durable task identity continued across nodes: put task_continues on the source worker activity naming its direct successor. The Host verifies same-Provider direct lineage and compiles start/continue; otherwise it gives a precise semantic diagnostic. Never use task_continues for fan-out, ordinary stages, or a file used for project memory. The Host maps routine read to the planning Provider, routine write to implementation, complex work to complex_implementation, and independent review to review. The actual model is the selected Provider configuration, visible and editable on the compiled node; Provider selection does not create a Codex task.',
  loops:'Use loops only when the source requires downstream semantic review to repair upstream work. Each has key, entry_activity, exit_activity, complete activity_keys, finite max_rounds, until {activity or loop,output,optional op and typed value}, optional feedback_inputs {name,from:activity.output} and optional item_scope {items:input:name or Host activity.output,verdicts:exit.output,paths_field,optional dependencies_field}. Loop inputs use loop:key.field. Exit must be a fresh read-only review Provider with no semantic fail_on_false guard or repeat_until. Until normally compares an exit boolean to true; item loops may use loop:key all_accepted. Preserve closed single-entry/single-exit acyclic regions and keep final acceptance outside; nested or disjoint regions are valid. Host owns runtime node and loop IDs, feedback, immutable rounds, item positions, artifact revision snapshots and failed-item materialization. Original items are never recopied by Agents. Item verdicts are {accepted:boolean,findings:new semantic data} in supplied order. Initial review checks all originals while an empty repair pool skips repair, so exit must not require repair output. Exhaustion fails. Return [] when the source needs no semantic repair.',
  controls:'Use named sequence, parallel, choice and approval groups only for statically known control not already implied by data consumption. Runtime-cardinality parallel work belongs in an activity fanout, never in prose. Every approval names subject as activity.output and before as the activities it authorizes. A choice may branch on a scalar output from any activity; do not create a separate decision activity merely to relay an existing result. Choice values are typed JSON scalars matching that output; never stringify booleans or numbers. A consumer after a choice may require only outputs available on every route that reaches it; otherwise split the consumer by route or make the input explicitly optional. Do not choose a root; the Host derives it and conservatively sequences otherwise independent roots.',
  fanout_validation:'A fanout activity exposes only its joined list as a top-level result. If success requires every item to pass, use a downstream agent or registered-tool validator (reuse an existing suitable consumer) that consumes that list, emits a boolean all_passed output, and names it in fail_on_false. Never put a per-item boolean in the fanout activity fail_on_false.',
  continuation:'For source-defined repeatable feedback, the Workflow may be started again with persisted prior artifact/state and new future-Run feedback. Preserve the revision mode, revalidation and renewed approval without imposing a source-absent revision cap. One Run remains acyclic.',
  source_dispositions:'Classify every supplied section once. A section mixing unconditional and optional clauses stays workflow; model the optional clauses with their own conditions. Use conditional for a section whose whole actionable content shares a trigger. note is the exact trigger for conditional sections and a concise reason otherwise.',
  runtime_dependencies:'Return runtime_dependencies explicitly, using [] when the source requires no executable for Workflow execution. Each item has a stable key, executable {name, optional version, optional python_modules}, phase unconditional, conditional or artifact_only, trigger (empty only for unconditional), one source_section, evidence {resource,quote}, and responsible activity_keys. source_section is the stable section ID; evidence.resource is the literal source_span.resource path from the source inventory, not the section ID or generated analysis/request.txt. Cite a different pinned script resource only when that section explicitly names it. evidence.quote is copied verbatim from the cited source within that section (or named script), without the display-only N: line-number prefix shown in the request packet. Classify required execution needs separately from optional features and libraries needed only when generated artifacts run later. Keep names and constraints portable; the Host prepares unconditional dependencies before task work. If the same exact quoted source clause yields Host-observed approval or user-input IDs only for availability or installation, name those IDs in host_preparation_observation_ids; do not absorb task approvals. Do not create an activity solely for availability checks, installation or relaying Host status. Project initialization with real file changes remains semantic work.',
  workspace_source_locations:`When code analysis must hand exact source locations to a later implementation or review activity, declare one output {name,kind:"list",values:[],type_ref:"",host_validation:"workspace_source_locations"}. Bind the successor input to that exact activity.output and instruct it to use the locations. ${WORKSPACE_SOURCE_LOCATION_RULES} The Host compiles the standard schema and applies the shared production and new-dispatch checks. Select this only when a downstream activity needs source locations; ordinary type_ref outputs remain available. Do not add a model stage merely to collect locations.`,
  data:'Declare only the inputs each activity needs; inputs may be empty. Task text and whole predecessor outputs are not implicit inputs. For an aggregate, declare the necessary field from every incoming parallel branch. Declare records, lists and enums when structured outputs need them; the Host emits JSON Schema.',
  repair:'A later semantic repair emits only stable-key upserts/removals, never the whole blueprint.',
  host_owned:['root','Workflow/node/edge IDs','start/end and finalization designation (the Host may use a guarded terminal Main activity instead of a separate default finalizer)','static parallel/join mechanics','fan-out dispatch identities and completion evidence','condition DSL','JSON Schema including selected source contracts','JSON Pointer and bindings including approval subjects','executor/provider/model/role/access/retry','source spans/confidence/resources/requirement kinds and status','revision/certificate/package fields'],
});
