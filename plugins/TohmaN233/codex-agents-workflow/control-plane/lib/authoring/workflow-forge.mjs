import { compileSemanticLoops, sourceRepairLoopIntentFindings } from './semantic-loops.mjs';
import { requireValue } from '../workflow-paths.mjs';
import { compileExpansion } from '../skill-import/semantic-expander.mjs';
import { sourceSectionInventory } from '../skill-import/source-dispositions.mjs';
import { hostPreparationObservationEvidence, observedSourceRequirements } from '../skill-import/source-requirements.mjs';
import { sourceContractMap } from '../skill-import/source-contracts.mjs';
import { authoringSourcePath } from '../skill-import/authoring-source.mjs';
import { bindingPointers } from '../workflow-bindings.mjs';
import { WORKSPACE_SOURCE_LOCATIONS, WORKSPACE_SOURCE_LOCATIONS_SCHEMA } from '../workspace-source-locations.mjs';
import { isPythonRequirement, normalizeExecutableRequirements } from '../runtime-requirements.mjs';
import { validateHostToolContract } from '../execution/host-tool-runner.mjs';
import { assertSemanticBlueprint, normalizeSemanticBlueprint, PREVIOUS_SEMANTIC_BLUEPRINT_CONTRACT, SEMANTIC_BLUEPRINT_CONTRACT, AUTHORING_NODE_PROMPT_MAX_LENGTH } from './blueprint-contract.mjs';
export { SEMANTIC_BLUEPRINT_CONTRACT } from './blueprint-contract.mjs';

const object=value=>value!==null && typeof value==='object' && !Array.isArray(value);
const localKey=value=>typeof value==='string' && /^[A-Za-z][A-Za-z0-9_-]{0,127}$/.test(value);
const exactDependencyToken=(source,value,{ignoreCase=false}={})=>new RegExp(`(^|[^A-Za-z0-9_.+-])${value.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')}(?=$|[^A-Za-z0-9_.+-]|\\.(?=$|\\s|[,;!?]))`,ignoreCase?'i':'').test(source);
const exactVersionEvidence=(source,normalized)=>[...normalized.matchAll(/\d+(?:\.\d+){0,2}/g)].every(match=>{
  const candidates=[match[0]];let shorter=match[0];
  while(shorter.endsWith('.0')){shorter=shorter.slice(0,-2);candidates.push(shorter);}
  return candidates.some(value=>new RegExp(`(^|[^0-9.])${value.replaceAll('.','\\.')}(?=$|[^0-9.]|\\.(?=$|\\s|[,;!?]))`).test(source));
});
const dependencyFinding=(item,field,message,sourceSpan)=>({kind:'semantic',code:'runtime_dependency_source',message,source_refs:sourceSpan?[structuredClone(sourceSpan)]:[],semantic_keys:[item?.key].filter(Boolean),affected_semantic_fields:[`runtime_dependencies.${item?.key??'<unknown>'}.${field}`],blocked_by:[],minimal_change:message});
function compileRuntimeDependencyDecisions(blueprint,resources,inventory,resourceRefsForSections,stageIds,observed){
  const requirements=[],mappings=[],findings=[],dispositions=new Map(blueprint.source_dispositions.map(item=>[item.section_id,item]));
  const observedDependencies=[...observed.values()].filter(item=>item.requirement_kind==='dependency');
  for(const item of blueprint.runtime_dependencies??[]){
    const section=inventory.get(item.source_section),evidence=item.evidence??{},resource=evidence.resource;
    if(!section){findings.push(dependencyFinding(item,'source_section',`Unknown source section ${item.source_section}`));continue;}
    const finding=(field,message)=>dependencyFinding(item,field,message,section.source_span);
    const disposition=dispositions.get(item.source_section);
    if(!['workflow','conditional'].includes(disposition?.disposition)){findings.push(finding('source_section',`Dependency evidence section ${item.source_section} is not retained as workflow meaning`));continue;}
    if(item.phase==='unconditional'&&disposition.disposition==='conditional'){findings.push(finding('phase',`Unconditional dependency ${item.key} cannot come from a wholly conditional section`));continue;}
    if(item.phase!=='unconditional'&&!(typeof item.trigger==='string'&&item.trigger.trim())){findings.push(finding('trigger',`Dependency ${item.key} needs the source condition or produced-artifact timing`));continue;}
    const expected=`${section.source_span.resource} lines ${section.source_span.start_line}-${section.source_span.end_line}`;
    const allowedResources=[...new Set([section.source_span.resource,...resourceRefsForSections([item.source_section])])].filter(path=>Object.hasOwn(resources,path));
    const validResource=allowedResources.includes(resource);
    if(!validResource)findings.push(finding('evidence.resource',`Dependency ${item.key} evidence.resource must be the literal source path ${expected}, or a pinned resource explicitly named by that section: ${allowedResources.join(', ')}; received ${String(resource)}`));
    const quote=evidence.quote;
    const validQuote=typeof quote==='string'&&!!quote.trim()&&quote.length<=2000;
    if(!validQuote)findings.push(finding('evidence.quote',`Dependency ${item.key} needs one bounded exact source quote from ${expected}, without any display-only line-number prefix`));
    const sourceTextFor=path=>{
      const text=Buffer.from(resources[path]).toString('utf8');
      return path===section.source_span.resource?text.split('\n').slice(section.source_span.start_line-1,section.source_span.end_line).join('\n'):text;
    };
    const quoteResources=validResource?[resource]:allowedResources;
    const matchedResource=validQuote?quoteResources.find(path=>sourceTextFor(path).includes(quote)):undefined;
    if(validQuote&&!matchedResource)findings.push(finding('evidence.quote',`Dependency ${item.key} evidence.quote must occur verbatim in ${validResource?resource:allowedResources.join(' or ')} (source section ${expected}); omit the display-only N: line-number prefix`));
    if(!validResource||!validQuote||!matchedResource)continue;
    const sectionText=sourceTextFor(resource),sectionOffset=sectionText.indexOf(quote);
    let executable;
    try{[executable]=normalizeExecutableRequirements([item.executable]);}
    catch(error){findings.push(finding('executable',`Dependency ${item.key} has an invalid portable executable: ${error.message}`));continue;}
    const named=exactDependencyToken(quote,executable.name,{ignoreCase:true});
    const pythonScript=isPythonRequirement(executable.name)&&/\.py$/i.test(resource);
    if(!named&&!pythonScript){findings.push(finding('evidence.quote',`Dependency ${item.key} quote must name ${executable.name} or cite a Python source script`));continue;}
    if(executable.version&&!exactVersionEvidence(quote,executable.version)){findings.push(finding('executable.version',`Dependency ${item.key} version is not supported by its exact source quote`));continue;}
    if((executable.python_modules??[]).some(module=>!exactDependencyToken(quote,module))){findings.push(finding('executable.python_modules',`Dependency ${item.key} Python modules must occur with exact spelling in its source quote`));continue;}
    const firstLine=resource===section.source_span.resource?section.source_span.start_line:1;
    const startLine=firstLine+sectionText.slice(0,sectionOffset).split('\n').length-1;
    const source_span={resource,start_line:startLine,end_line:startLine+quote.split('\n').length-1};
    const alias=observedDependencies.find(requirement=>isPythonRequirement(requirement.details?.executable)&&isPythonRequirement(executable.name)&&requirement.details.executable!==executable.name&&(requirement.source_spans??[]).some(span=>span.resource===resource&&span.start_line<=source_span.end_line&&span.end_line>=source_span.start_line));
    if(alias){findings.push(finding('executable.name',`Dependency ${item.key} names ${executable.name}, while the same source names ${alias.details.executable}; choose the exact executable consistently`));continue;}
    const absorbed=[...new Set(item.host_preparation_observation_ids??[])];
    if(item.phase!=='unconditional'&&absorbed.length){findings.push(finding('host_preparation_observation_ids',`Only unconditional Host preparation may absorb availability or installation observations`));continue;}
    const hostDecision={requirement_kind:'dependency',source_spans:[source_span],details:{executable:executable.name,phase:item.phase,source_quote:quote}};
    const invalidAbsorbed=absorbed.find(id=>!hostPreparationObservationEvidence(observed.get(id),hostDecision,resources));
    if(invalidAbsorbed){findings.push(finding('host_preparation_observation_ids',`Observation ${invalidAbsorbed} is not a single availability or installation approval/input within the exact cited source clause`));continue;}
    const node_ids=[...new Set(item.activity_keys.map(key=>stageIds.get(key)).filter(Boolean))];
    if(node_ids.length!==new Set(item.activity_keys).size){findings.push(finding('activity_keys',`Dependency ${item.key} must map to existing responsible activities`));continue;}
    const requirement_id=`authoring_dependency_${item.key}`;
    requirements.push({requirement_id,requirement_kind:'dependency',source_spans:[source_span],trigger:item.phase==='unconditional'?'unconditional_source_dependency':item.trigger,required_result:item.phase==='unconditional'?`Prepare executable ${executable.name} before task execution.`:`Preserve ${executable.name} at its source-defined ${item.phase} phase.`,resource_refs:[resource],details:{executable:executable.name,...(executable.version?{version:executable.version}:{}),...(executable.python_modules?{python_modules:executable.python_modules}:{}),phase:item.phase,source_quote:quote,...(absorbed.length?{host_preparation_observation_ids:absorbed}:{})}});
    mappings.push({requirement_id,node_ids,binding_names:[],runtime_guards:item.phase==='unconditional'?[]:[item.trigger],resource_refs:[resource],status:item.phase==='unconditional'?'compiled':'agent_assisted',rationale:`Host projected source-grounded runtime dependency ${item.key} onto its responsible activities.`});
  }
  if(findings.length)throw Object.assign(new Error(findings.map(item=>item.message).join('; ')),{code:'AUTHORING_SEMANTIC',findings});
  return {requirements,mappings};
}
const primitiveSchema=kind=>{
  // `text` is the compact semantic vocabulary; `string` is the equivalent
  // JSON-Schema spelling models naturally use in record field references.
  // Treating that spelling difference as a semantic defect only creates a
  // pointless repair turn.
  if(kind==='text'||kind==='string')return {type:'string'};
  if(['boolean','number','integer'].includes(kind))return {type:kind};
  if(kind==='object')return {type:'object',additionalProperties:true};
  if(kind==='list')return {type:'array',items:{type:'string'}};
  return null;
};
const artifactReferenceSchema=contract=>({
  type:'object',
  properties:{
    path:{type:'string',minLength:1,maxLength:1024},
    sha256:{type:'string',minLength:64,maxLength:64,pattern:'^[a-f0-9]+$'},
    contract_id:{type:'string',const:contract.contract_id},
  },
  required:['path','sha256','contract_id'],
  additionalProperties:false,
});
function dataTypeResolver(definitions=[]){
  requireValue(Array.isArray(definitions)&&definitions.every(item=>object(item)&&Array.isArray(item.fields)&&Array.isArray(item.values)&&typeof item.item_type_ref==='string'&&['closed','open'].includes(item.openness)),'AUTHORING_FORMAT','Named data types must use the fixed v3 shape');
  const types=new Map(definitions.map(item=>[item.key,item])),cache=new Map(),visiting=new Set();
  requireValue(types.size===definitions.length&&definitions.every(item=>localKey(item.key)),'AUTHORING_FORMAT','Named data type keys must be unique local keys');
  const resolve=ref=>{
    const builtin=primitiveSchema(ref);if(builtin)return builtin;
    requireValue(types.has(ref),'AUTHORING_SEMANTIC',`Unknown semantic data type ${ref}`);
    if(cache.has(ref))return structuredClone(cache.get(ref));
    requireValue(!visiting.has(ref),'AUTHORING_FORMAT',`Semantic data types contain a cycle at ${ref}`);visiting.add(ref);
    const item=types.get(ref);let schema;
    if(item.kind==='object'){
      requireValue(Array.isArray(item.fields)&&new Set(item.fields.map(field=>field.name)).size===item.fields.length&&item.fields.every(field=>localKey(field.name))&&!item.item_type_ref&&item.values.length===0,'AUTHORING_FORMAT',`Object data type ${ref} needs unique fields and no list/enum payload`);
      const properties=Object.fromEntries(item.fields.map(field=>[field.name,resolve(field.type_ref)])),required=item.fields.filter(field=>field.required).map(field=>field.name);
      schema={type:'object',properties,required,additionalProperties:item.openness==='open'};
    } else if(item.kind==='list'){
      requireValue(typeof item.item_type_ref==='string'&&item.item_type_ref&&item.fields.length===0&&item.values.length===0&&item.openness==='closed','AUTHORING_FORMAT',`List data type ${ref} needs only an item type`);schema={type:'array',items:resolve(item.item_type_ref)};
    } else if(item.kind==='enum'){
      requireValue(Array.isArray(item.values)&&item.values.length>0&&new Set(item.values).size===item.values.length&&item.fields.length===0&&!item.item_type_ref&&item.openness==='closed','AUTHORING_FORMAT',`Enum data type ${ref} needs only unique values`);schema={type:'string',enum:[...item.values]};
    } else {schema=primitiveSchema(item.kind);requireValue(schema&&item.fields.length===0&&!item.item_type_ref&&item.values.length===0&&item.openness==='closed','AUTHORING_FORMAT',`Primitive data type ${ref} cannot carry object, list or enum payload`);}
    visiting.delete(ref);cache.set(ref,schema);return structuredClone(schema);
  };
  for(const key of types.keys())resolve(key);
  return resolve;
}
const shapeSchema=(shape,resolveType)=>{
  if(typeof shape==='string')shape={kind:shape,values:[],type_ref:''};
  if(shape?.type_ref){const schema=resolveType(shape.type_ref),expected=shape.kind==='text'||shape.kind==='enum'?'string':shape.kind==='list'?'array':shape.kind;requireValue(schema.type===expected,'AUTHORING_SEMANTIC',`Produced shape ${shape.kind} conflicts with named type ${shape.type_ref}`);return schema;}
  requireValue(object(shape) && ['text','boolean','number','integer','object','list','enum'].includes(shape.kind),'AUTHORING_FORMAT','Produced values need a supported semantic shape');
  const primitive=primitiveSchema(shape.kind);if(primitive)return primitive;
  requireValue(Array.isArray(shape.values) && shape.values.length>0 && shape.values.every(value=>['string','number','boolean'].includes(typeof value)),'AUTHORING_FORMAT','Enum shapes need bounded scalar values');
  return {type:typeof shape.values[0],enum:[...shape.values]};
};
const choiceValueKey=value=>`${typeof value}:${JSON.stringify(value)}`;
function choiceValueFailure(choiceKey,message){
  const error=Object.assign(new Error(message),{code:'AUTHORING_SEMANTIC'});
  error.findings=[{kind:'semantic',code:'choice_value_type',message,source_refs:[],semantic_keys:[choiceKey],affected_semantic_fields:['choices'],blocked_by:[],minimal_change:'Make the branch value match the declared scalar decision output.'}];
  throw error;
}
function requireChoiceValue(value,schema,choiceKey,outputName){
  const scalar=['string','boolean','number'].includes(typeof value)&&value!==null&&(typeof value!=='number'||Number.isFinite(value))&&(typeof value!=='string'||([...value].length>0&&[...value].length<=1000));
  requireValue(scalar,'AUTHORING_FORMAT',`Choice ${choiceKey} values must be bounded JSON scalars`);
  const matches=schema.type==='integer'?Number.isInteger(value):schema.type===typeof value;
  if(!matches)choiceValueFailure(choiceKey,`Choice ${choiceKey} value ${JSON.stringify(value)} does not match decision output ${outputName} type ${schema.type}`);
  if(schema.enum&&!schema.enum.some(item=>choiceValueKey(item)===choiceValueKey(value)))choiceValueFailure(choiceKey,`Choice ${choiceKey} value ${JSON.stringify(value)} is outside decision output ${outputName}`);
}

function validateBlueprint(blueprint,resources){
  requireValue(object(blueprint) && blueprint.contract===PREVIOUS_SEMANTIC_BLUEPRINT_CONTRACT && typeof blueprint.purpose==='string' && blueprint.purpose.trim() && object(blueprint.program),'AUTHORING_FORMAT','Authoring requires a normalized semantic blueprint');
  const sections=new Set(sourceSectionInventory(resources).map(item=>item.section_id));
  requireValue(Array.isArray(blueprint.source_dispositions) && blueprint.source_dispositions.length===sections.size,'AUTHORING_SEMANTIC','Blueprint must classify every source section exactly once');
  requireValue(blueprint.source_dispositions.every(item=>object(item)&&sections.has(item.section_id)&&['workflow','conditional','reference','omit'].includes(item.disposition)),'AUTHORING_SEMANTIC','Blueprint has an invalid source disposition');
  requireValue(new Set(blueprint.source_dispositions.map(item=>item.section_id)).size===sections.size,'AUTHORING_FORMAT','Blueprint source dispositions must be unique');
  requireValue(Array.isArray(blueprint.semantic_rules ?? []) && Array.isArray(blueprint.requirement_assignments ?? []),'AUTHORING_FORMAT','Blueprint semantic rule and requirement assignment lists must be arrays');
  return blueprint;
}

function inflateBlueprint(raw){
  requireValue(object(raw)&&raw.contract===PREVIOUS_SEMANTIC_BLUEPRINT_CONTRACT,'AUTHORING_FORMAT','Authoring requires a normalized semantic blueprint');
  const keyedCollections=[
    ['activities',raw.activities ?? []],['approvals',raw.approvals ?? []],['sequences',raw.sequences ?? []],
    ['parallels',raw.parallels ?? []],['choices',raw.choices ?? []],
  ];
  for(const [name,items] of keyedCollections){
    requireValue(Array.isArray(items),'AUTHORING_FORMAT',`Blueprint ${name} must be an array`);
    requireValue(new Set(items.map(item=>item?.key)).size===items.length,'AUTHORING_FORMAT',`Blueprint ${name} keys must be unique before compilation`);
  }
  const activities=new Map((raw.activities ?? []).map(item=>[item.key,{...structuredClone(item),continues:item.continues || undefined,consumes:item.consumes.map(consume=>({name:consume.name,from:consume.source_kind==='input'?{input:consume.input}:consume.source_kind==='loop'?{loop:consume.loop,output:consume.output}:{activity:consume.activity,output:consume.output}}))}]));
  const approvals=new Map((raw.approvals ?? []).map(item=>[item.key,structuredClone(item)]));
  const sequences=new Map((raw.sequences ?? []).map(item=>[item.key,structuredClone(item)]));
  const parallels=new Map((raw.parallels ?? []).map(item=>[item.key,structuredClone(item)]));
  const choices=new Map((raw.choices ?? []).map(item=>[item.key,structuredClone(item)]));
  const all=[...activities.keys(),...approvals.keys(),...sequences.keys(),...parallels.keys(),...choices.keys()];
  requireValue(new Set(all).size===all.length,'AUTHORING_FORMAT','Semantic keys must be unique across activities and control groups');
  const visiting=new Set(),reachable=new Set();
  const resolve=key=>{
    requireValue(!visiting.has(key),'AUTHORING_SEMANTIC',`Semantic control groups contain a cycle at ${key}`);
    reachable.add(key);
    if(activities.has(key))return {kind:'activity',key,activity:activities.get(key)};
    if(approvals.has(key)){const item=approvals.get(key);return {kind:'approval',...item};}
    visiting.add(key);
    let block;
    if(sequences.has(key)){const item=sequences.get(key);block={kind:'sequence',key,steps:item.members.map(resolve)};}
    else if(parallels.has(key)){const item=parallels.get(key);requireValue(item.members.length>=2,'AUTHORING_SEMANTIC','Parallel groups need at least two members');block={kind:'parallel',key,failure_meaning:item.failure_meaning,branches:item.members.map(resolve)};}
    else if(choices.has(key)){
      const item=choices.get(key),decision=resolve(item.decision_activity);
      requireValue(decision.kind==='activity','AUTHORING_SEMANTIC',`Choice ${key} must reference an activity with a scalar decision output`);
      block={kind:'choice',key,decision:decision.activity,output:item.output,branches:item.branches.map(branch=>({value:branch.value,body:resolve(branch.body)})),default:resolve(item.default_body)};
    } else requireValue(false,'AUTHORING_SEMANTIC',`Unknown semantic component ${key}`);
    visiting.delete(key);return block;
  };
  const program=resolve(raw.root);
  requireValue(reachable.size===all.length,'AUTHORING_SEMANTIC',`Blueprint has unreachable semantic components: ${all.filter(key=>!reachable.has(key)).join(', ')}`);
  return {...structuredClone(raw),program};
}

export function lowerSemanticBlueprint(pack,resources,rawBlueprint,context={}){
  const sectionInventory=sourceSectionInventory(resources),sectionIds=new Set(sectionInventory.map(item=>item.section_id)),sourceContracts=sourceContractMap(resources);
  const availableHostToolContracts=[...(pack.workflow.host_tools??[]),...(context.host_tool_contracts??[])];
  const blueprintOptions={sectionIds,sectionInventory,contractIds:new Set(sourceContracts.keys()),hostToolContracts:availableHostToolContracts};
  if(rawBlueprint?.contract===SEMANTIC_BLUEPRINT_CONTRACT)rawBlueprint=assertSemanticBlueprint(rawBlueprint,blueprintOptions);
  const blueprint=validateBlueprint(inflateBlueprint(normalizeSemanticBlueprint(rawBlueprint,blueprintOptions)),resources),resolveType=dataTypeResolver(blueprint.data_types ?? []);
  const inventory=new Map(sourceSectionInventory(resources).map(item=>[item.section_id,item]));
  const observed=new Map(observedSourceRequirements(resources).map(item=>[item.requirement_id,item]));
  const entrypoint=authoringSourcePath(resources),entryLines=Buffer.from(resources[entrypoint] ?? '').toString('utf8').split('\n');
  const supporting=Object.keys(resources).filter(path=>path!==entrypoint);
  const resourceRefsForSections=ids=>[...new Set(ids.flatMap(id=>{const section=inventory.get(id);if(!section||section.source_span.resource!==entrypoint)return [];const text=entryLines.slice(section.source_span.start_line-1,section.source_span.end_line).join('\n').replaceAll('\\','/');return supporting.filter(path=>{const relative=path.startsWith('source/')?path.slice(7):path;return text.includes(path)||text.includes(relative);});}))];
  const routing=context.routing_rules;
  const loopIds=new Map((blueprint.loops??[]).map((item,index)=>[item.key,`loop_${String(index+1).padStart(3,'0')}`]));
  const nodes=[],edges=[],stageIds=new Map(),activityIds=new Map(),activityOutputs=new Map(),compiledBlocks=new Map(),compilingBlocks=new Set(),edgeKeys=new Set(),approvalBindings=[];
  let nodeOrdinal=0,edgeOrdinal=0,parallelOrdinal=0;
  const nodeId=prefix=>`${prefix}_${String(++nodeOrdinal).padStart(3,'0')}`;
  const addEdge=(source,target,extra={})=>{
    if(source===target)return;
    const {section_ids=[],...semantic}=extra,key=`${source}\u0000${target}\u0000${semantic.label ?? ''}`;
    if(edgeKeys.has(key))return;
    // A transition is justified by both the producing and consuming phases.
    // Keeping only the target section loses source ordering rules at phase
    // boundaries, even though the planner classified both phases correctly.
    const endpointSpans=[source,target].flatMap(id=>nodes.find(node=>node.id===id)?.source_spans??[]);
    const source_spans=[...new Map([...(section_ids.length?spansFor(section_ids):[]),...endpointSpans].map(span=>[`${span.resource}:${span.start_line}:${span.end_line}`,structuredClone(span)])).values()];
    edgeKeys.add(key);edges.push({id:`edge_${String(++edgeOrdinal).padStart(3,'0')}`,source,target,...semantic,confidence:1,source_span:source_spans[0],source_spans});
  };
  const spansFor=ids=>{
    const selected=(ids.length?ids:[...inventory.keys()].slice(0,1)).map(id=>{const item=inventory.get(id);requireValue(item,'AUTHORING_SEMANTIC',`Unknown source section ${id}`);return item.source_span;});
    return [...new Map(selected.map(item=>[`${item.resource}:${item.start_line}:${item.end_line}`,structuredClone(item)])).values()];
  };
  const evidence=(ids,selectedContracts=[])=>{
    // A general resource reference grants access but is not itself evidence.
    // An explicitly selected source contract does identify the exact interface
    // lines this activity uses, so project those spans without asking the
    // planner to copy Host-owned source coordinates.
    const source_spans=[...new Map([...spansFor(ids),...selectedContracts.filter(contract=>contract.status==='resolved'&&contract.authority==='interface').flatMap(contract=>contract.source_spans??[])].map(span=>[`${span.resource}:${span.start_line}:${span.end_line}`,structuredClone(span)])).values()];
    return {source_span:source_spans[0],source_spans};
  };
  const providerFor=taskType=>routing?.routes?.[taskType]?.provider_id;
  const semanticKeyOf=block=>block.kind==='activity'?block.activity.key:block.key;
  const activityByKey=new Map((blueprint.activities??[]).map(item=>[item.key,item]));
  const availableHostTools=new Map();
  for(const raw of availableHostToolContracts){const contract=validateHostToolContract(raw);availableHostTools.set(contract.id,contract);}
  const consumptionSource=input=>input?.from??(input?.source_kind==='input'?{input:input.input}:input?.source_kind==='activity'?{activity:input.activity,output:input.output}:{});
  const hostOwnedPacketProducer=(key,outputName='',requiredFields=[],visiting=new Set())=>{
    const activity=activityByKey.get(key);
    if(activity?.capability?.kind!=='registered_tool'||visiting.has(key))return false;
    const next=new Set(visiting);next.add(key);
    const contract=availableHostTools.get(activity.capability.semantic_name),declared=(contract?.host_owned_item_fields??[]).find(item=>item.output===outputName);
    const inputs=declared&&requiredFields.length&&requiredFields.every(field=>declared.fields.includes(field))
      ? declared.from_inputs.map(name=>(activity.consumes??[]).find(input=>input.name===name)).filter(Boolean)
      : activity.consumes??[];
    if(declared&&requiredFields.length&&requiredFields.every(field=>declared.fields.includes(field))&&inputs.length!==declared.from_inputs.length)return false;
    return inputs.every(input=>{const from=consumptionSource(input);return typeof from.input==='string'||typeof from.activity==='string'&&hostOwnedPacketProducer(from.activity,from.output,[],next);});
  };
  const normalizeActivity=(activity,{decision=false}={})=>{
    requireValue(object(activity)&&localKey(activity.key)&&typeof activity.instructions==='string'&&activity.instructions.trim()&&['main','isolated_worker'].includes(activity.ownership)&&['read','write'].includes(activity.operation)&&Array.isArray(activity.source_sections)&&activity.source_sections.length>0,'AUTHORING_FORMAT','Activity needs key, instructions, ownership, operation and source sections');
    requireValue(!stageIds.has(activity.key),'AUTHORING_FORMAT',`Duplicate stage key ${activity.key}`);
    activity.source_sections.forEach(id=>requireValue(inventory.has(id),'AUTHORING_SEMANTIC',`Unknown source section ${id}`));
    // Semantic keys are source-level references, never runtime identifiers.
    // The Host allocates every concrete node ID, so perfectly valid semantic
    // names such as `start`, `final` and `end` cannot collide with control
    // nodes or trigger a model retry.
    const id=nodeId('activity');stageIds.set(activity.key,id);activityIds.set(activity.key,id);
    const produces=activity.produces ?? [];
    requireValue(Array.isArray(produces)&&new Set(produces.map(item=>item.name)).size===produces.length&&produces.every(item=>object(item)&&localKey(item.name)),'AUTHORING_FORMAT','Activity outputs need unique local names');
    for(const item of produces)if(item.host_validation!==undefined)requireValue(item.host_validation===WORKSPACE_SOURCE_LOCATIONS&&item.shape?.kind==='list'&&!item.shape.type_ref&&!item.shape.values?.length&&!item.contract_ref&&activity.capability?.kind!=='registered_tool'&&(!activity.fanout||activity.fanout.result_output===item.name),'AUTHORING_SEMANTIC',`Activity ${activity.key} output ${item.name} host_validation needs an Agent-produced plain list retained as the joined output`,{findings:[{kind:'semantic',code:'workspace_source_locations_shape',message:`Output ${item.name} must be an Agent-produced plain source-location list retained as the joined output`,semantic_keys:[activity.key],affected_semantic_fields:[`activities.${activity.key}.outputs.${item.name}.host_validation`],source_refs:[],blocked_by:[],minimal_change:'Use kind list, empty type_ref and values, no contract_ref or tool, and the fanout result output if applicable; or remove host_validation.'}]});
    const selectedContracts=[...new Set([...(activity.contract_refs??[]),...produces.map(item=>item.contract_ref).filter(Boolean)])].map(ref=>{const contract=sourceContracts.get(ref);requireValue(contract,'AUTHORING_SEMANTIC',`Activity ${activity.key} selects unknown source contract ${ref}`);return contract;});
    const resource_refs=[...new Set([...resourceRefsForSections(activity.source_sections),...selectedContracts.map(contract=>contract.resource),...produces.map(item=>item.contract_ref&&sourceContracts.get(item.contract_ref)?.resource).filter(Boolean)])];
    const properties=Object.fromEntries(produces.map(item=>{
      if(item.contract_ref){
        const contract=sourceContracts.get(item.contract_ref);
        requireValue(['json_artifact','python_cli'].includes(contract?.kind),'AUTHORING_SEMANTIC',`Activity ${activity.key} output ${item.name} selects an unsupported source contract`);
        if(contract.kind==='json_artifact'&&contract.status==='resolved'){
          requireValue(object(contract.artifact_schema),'AUTHORING_SEMANTIC',`Activity ${activity.key} output ${item.name} needs a JSON artifact source contract`);
          // A file contract describes the workspace artifact, not the Agent
          // response. Pass a small immutable reference between nodes.
          return [item.name,artifactReferenceSchema(contract)];
        }
        // An interface contract describes how the result is produced. Its
        // source remains a pinned node resource; the Agent reads that source
        // when needed instead of receiving a copied JSON interface appendix.
        return [item.name,shapeSchema(item.shape,resolveType)];
      }
      return [item.name,item.host_validation===WORKSPACE_SOURCE_LOCATIONS?structuredClone(WORKSPACE_SOURCE_LOCATIONS_SCHEMA):shapeSchema(item.shape,resolveType)];
    }));
    // The runtime joins one result per worker into a single list. Other
    // semantic outputs are per-item intermediates, not parallel top-level
    // result fields; keep their source contracts in the worker instructions.
    const joinedProperties=activity.fanout?Object.fromEntries(Object.entries(properties).filter(([name])=>name===activity.fanout.result_output)):properties;
    const outputs_schema=Object.keys(joinedProperties).length?{type:'object',properties:joinedProperties,required:Object.keys(joinedProperties),additionalProperties:false}:undefined;
    const output_validators=Object.fromEntries(produces.filter(item=>item.host_validation&&Object.hasOwn(joinedProperties,item.name)).map(item=>[item.name,item.host_validation]));
    activityOutputs.set(activity.key,joinedProperties);
    let fanoutContract=null;
    if(activity.fanout){
      const spec=activity.fanout,consume=(activity.consumes??[]).find(item=>item.name===spec.input),resultSchema=properties[spec.result_output];
      requireValue(activity.ownership==='isolated_worker'&&activity.kind==='work'&&activity.capability?.kind!=='registered_tool','AUTHORING_SEMANTIC',`Activity ${activity.key} sub-Agent count is available only for isolated Agent work; Main activities cannot configure it`);
      requireValue(consume&&object(resultSchema)&&resultSchema.type==='array','AUTHORING_SEMANTIC',`Activity ${activity.key} fan-out needs one declared list input and one declared list result output`);
      requireValue(spec.count_mode==='auto'&&spec.fixed_count===0||spec.count_mode==='fixed'&&Number.isInteger(spec.fixed_count)&&spec.fixed_count>=1&&spec.fixed_count<=32,'AUTHORING_SEMANTIC',`Activity ${activity.key} fan-out count must be auto or a fixed integer from 1 to 32`);
      requireValue(spec.batch_size===undefined||(Number.isInteger(spec.batch_size)&&spec.batch_size>=1&&spec.batch_size<=32&&spec.count_mode==='auto'&&spec.fixed_count===0),'AUTHORING_SEMANTIC',`Activity ${activity.key} batch_size must be 1 to 32 with automatic count and fixed_count 0`);
      requireValue(spec.max_concurrency===undefined||(Number.isInteger(spec.max_concurrency)&&spec.max_concurrency>=1&&spec.max_concurrency<=32),'AUTHORING_SEMANTIC',`Activity ${activity.key} max_concurrency must be 1 to 32`);
      requireValue(spec.write_paths_field===undefined||activity.operation==='write'&&localKey(spec.write_paths_field),'AUTHORING_SEMANTIC',`Activity ${activity.key} write_paths_field needs a write activity and a portable Host item field name`);
      if(spec.write_paths_field!==undefined){
        const producerKey=consume?.from?.activity,producer=producerKey?activityByKey.get(producerKey):null;
        const loop=(blueprint.loops??[]).find(item=>item.key===consume?.from?.loop),original=loop?.item_scope?.items;
        const loopOwned=loop&&['repair_items','review_items'].includes(consume.from.output)&&loop.item_scope.paths_field===spec.write_paths_field&&typeof original==='string'&&(original.startsWith('input:')||hostOwnedPacketProducer(original.split('.')[0],original.slice(original.indexOf('.')+1),[spec.write_paths_field]));
        const hostOwnedSource=loopOwned||typeof consume?.from?.input==='string'||producerKey&&hostOwnedPacketProducer(producerKey,consume?.from?.output,[spec.write_paths_field]);
        requireValue(hostOwnedSource,'AUTHORING_SEMANTIC',`Activity ${activity.key} per-item write packet must come from Host-owned data`,{findings:[{kind:'semantic',code:'fanout_host_item_source',message:`Activity ${activity.key} uses Host-owned per-item write paths, but ${producerKey||consume?.name||spec.input} depends on Agent output. Bind the fan-out list directly from a Workflow input or from Host tools whose inputs are themselves Host-owned.`,source_refs:spansFor(activity.source_sections),semantic_keys:[activity.key,...(producer?.key?[producer.key]:[])],affected_semantic_fields:[`activities.${activity.key}.inputs.${spec.input}`,`activities.${activity.key}.fanout.write_paths_field`],blocked_by:[],minimal_change:'Use the original Workflow input or a transitively Host-owned tool output as the fan-out input; keep Agent-produced semantic findings separate.'}]});
      }
      requireValue(spec.item_delivery===undefined||spec.item_delivery==='incremental'&&spec.result_mode==='per_item'&&Number.isInteger(spec.batch_size)&&spec.batch_size>=2,
        'AUTHORING_SEMANTIC',`Activity ${activity.key} incremental item_delivery needs per_item result mode and batch_size at least 2`);
      // Batch ownership is a semantic execution choice. Never invent a batch
      // size from per-item result admission; the source/planner must declare it.
      const batchSize=spec.batch_size;
      fanoutContract={input:spec.input,item_name:spec.item_name,result_output:spec.result_output,distribution:spec.count_mode==='auto'&&batchSize===undefined?'one_per_item':'partition',scheduling:'parallel',join:'all_required',...(batchSize!==undefined?{batch_size:batchSize}:{}),...(spec.max_concurrency!==undefined?{max_concurrency:spec.max_concurrency}:{}),...(spec.result_mode?{result_mode:spec.result_mode}:{}),...(spec.item_delivery?{item_delivery:spec.item_delivery}:{}),...(spec.write_paths_field?{write_paths_field:spec.write_paths_field}:{}),...(spec.shared_change_field?{shared_change_field:spec.shared_change_field}:{})};
    }
    const review=activity.kind==='review';
    const semanticOutcome=activity.outcome ?? (activity.kind==='decision'?'decision':review?'review':produces.length?'artifact':'none');
    const onMissing=activity.on_missing ?? 'block';
    requireValue(onMissing==='block','AUTHORING_SEMANTIC',`Activity ${activity.key} uses unsupported on_missing ${onMissing}; this runtime supports block only`);
    requireValue(semanticOutcome!=='none'||produces.length===0,'AUTHORING_SEMANTIC',`Activity ${activity.key} declares outcome none but also declares outputs`);
    requireValue(!['artifact','validated_artifact','decision'].includes(semanticOutcome)||produces.length>0,'AUTHORING_SEMANTIC',`Activity ${activity.key} outcome ${semanticOutcome} needs a declared output`);
    // Outcome does not grant executor authority. A writing activity may return
    // a review verdict, and an ordinary read activity may return one too.
    const failOnFalse=activity.fail_on_false??[];
    requireValue(new Set(failOnFalse).size===failOnFalse.length&&failOnFalse.every(name=>joinedProperties[name]?.type==='boolean'),'AUTHORING_SEMANTIC',`Activity ${activity.key} false-result guards must name unique declared boolean outputs`);
    const completion_contract={on_missing:onMissing,outcome:semanticOutcome,...(failOnFalse.length?{fail_on_false:failOnFalse}:{})};
    const task_type=review?'review':activity.complexity==='complex'?'complex_implementation':activity.operation==='write'?'implementation':'planning';
    const tool=activity.capability?.kind==='registered_tool';
    requireValue(activity.main_mode === undefined || activity.ownership === 'main' && !tool, 'MAIN_EXECUTION_MODE', 'Main context modes belong only to semantic Main activities');
    requireValue(!tool || localKey(activity.capability.semantic_name),'AUTHORING_FORMAT','Registered-tool activities need one exact semantic tool name');
    const fanoutAppendix=fanoutContract?(fanoutContract.result_mode==='per_item'
      ?`\n\nProcess only the supplied batch. Return one completed${fanoutContract.shared_change_field?', delegated':''} or blocked entry per supplied item in Host order as the Host packet specifies. Preserve accepted item work during targeted repair.`
      :'\n\nProcess only the supplied batch. Return one batch result matching the supplied schema, with per-item evidence in input order or artifact references.') : '';
    const retryAppendix=activity.repeat_until?`\n\nHost-bounded correction contract: validate "${activity.repeat_until.condition}". If it is unmet, fail this Workflow node visibly so the runtime can retry; never report a blocker as successful delivery. Maximum attempts: ${activity.repeat_until.max_attempts}.`:'';
    const prompt=activity.instructions+fanoutAppendix+retryAppendix;
    requireValue(tool || prompt.length<=AUTHORING_NODE_PROMPT_MAX_LENGTH,'AUTHORING_PROMPT_LIMIT',`Activity ${activity.key} prompt exceeds the ${AUTHORING_NODE_PROMPT_MAX_LENGTH}-character node limit after Host appendices`,{activity_key:activity.key,instructions_chars:activity.instructions.length,appendix_chars:prompt.length-activity.instructions.length,prompt_chars:prompt.length});
    const node=tool
      ? {id,type:'tool',semantic_key:activity.key,name:activity.purpose ?? activity.key,tool:activity.capability.semantic_name,...(outputs_schema?{outputs_schema}:{}),completion_contract,resource_refs,confidence:1,...evidence(activity.source_sections,selectedContracts)}
      : {id,type:'agent',semantic_key:activity.key,name:activity.purpose ?? activity.key,operation_mode:activity.operation,task_type,routing_reason:`Host classified ${activity.key} from semantic kind, operation and complexity.`,prompt_template:prompt,...(outputs_schema?{outputs_schema}:{}),...(Object.keys(output_validators).length?{output_validators}:{}),completion_contract,...(activity.ownership==='isolated_worker'?{subagent_count:activity.fanout?.count_mode==='fixed'?activity.fanout.fixed_count:'auto'}:{}),...(fanoutContract?{fanout:fanoutContract}:{}),...(activity.repeat_until?{retry_max_attempts:activity.repeat_until.max_attempts}:{}),resource_refs,confidence:1,...evidence(activity.source_sections,selectedContracts)};
    if(!tool && activity.ownership === 'main' && (activity.main_mode !== undefined || routing?.selection_mode !== 'automatic')) node.main_mode=activity.main_mode ?? 'worker';
    if(!tool && routing?.selection_mode==='automatic'){
      node.execution_target=activity.ownership==='main'?'main':'subagent';
      if(node.execution_target==='subagent')node.provider_choice=providerFor(task_type);
    }
    nodes.push(node);
    return {entries:[id],exits:[id],sections:activity.source_sections,decision};
  };
  const compileBlock=block=>{
    requireValue(object(block)&&['sequence','parallel','choice','approval','activity'].includes(block.kind),'AUTHORING_FORMAT','Program block kind is invalid');
    const semanticKey=semanticKeyOf(block);
    requireValue(localKey(semanticKey),'AUTHORING_FORMAT','Program blocks need stable semantic keys');
    if(compiledBlocks.has(semanticKey))return compiledBlocks.get(semanticKey);
    requireValue(!compilingBlocks.has(semanticKey),'AUTHORING_SEMANTIC',`Semantic control groups contain a cycle at ${semanticKey}`);
    compilingBlocks.add(semanticKey);
    let result;
    if(block.kind==='activity')result=normalizeActivity(block.activity);
    else if(block.kind==='approval'){
      requireValue(localKey(block.key)&&!stageIds.has(block.key)&&typeof block.question==='string'&&block.question.trim()&&Array.isArray(block.source_sections)&&block.source_sections.length>0,'AUTHORING_FORMAT','Approval needs a unique key, question and source sections');
      const id=nodeId('approval');stageIds.set(block.key,id);nodes.push({id,type:'human_gate',semantic_key:block.key,name:'Human approval',prompt_template:block.question,confidence:1,...evidence(block.source_sections)});approvalBindings.push({gate_id:id,key:block.key,subject:block.subject,before:block.before??[]});result={entries:[id],exits:[id],sections:block.source_sections};
    }
    else if(block.kind==='sequence'){
      requireValue(Array.isArray(block.steps)&&block.steps.length>0,'AUTHORING_FORMAT','Sequence needs at least one step');
      const parts=block.steps.map(compileBlock);for(let index=1;index<parts.length;index++)for(const source of parts[index-1].exits)for(const target of parts[index].entries)addEdge(source,target,{section_ids:parts[index].sections});
      result={entries:parts[0].entries,exits:parts.at(-1).exits,sections:[...new Set(parts.flatMap(item=>item.sections))]};
    }
    else if(block.kind==='parallel'){
      requireValue(Array.isArray(block.branches)&&block.branches.length>=2,'AUTHORING_FORMAT','Parallel needs at least two branches');
      ++parallelOrdinal;
      const fork=nodeId('parallel'),join=nodeId('join');
      const parts=block.branches.map(compileBlock),sections=[...new Set(parts.flatMap(item=>item.sections))];
      nodes.push({id:fork,type:'parallel',semantic_key:block.key,join_id:join,failure_policy:block.failure_meaning==='partial_evidence_allowed'?'collect':'fail_fast',confidence:1,...evidence(sections)});
      nodes.push({id:join,type:'join',semantic_key:block.key,parallel_id:fork,confidence:1,...evidence(sections)});
      parts.forEach((part,index)=>{for(const target of part.entries)addEdge(fork,target,{label:`branch_${index+1}`,section_ids:part.sections});for(const source of part.exits)addEdge(source,join,{section_ids:part.sections});});
      result={entries:[fork],exits:[join],sections};
    }
    else {
      requireValue(object(block.decision)&&Array.isArray(block.branches)&&block.branches.length>0&&object(block.default),'AUTHORING_FORMAT','Choice needs a decision, branches and default block');
      const decisionPrecompiled=compiledBlocks.has(block.decision.key),decision=compileBlock({kind:'activity',key:block.decision.key,activity:block.decision});
      const outputName=block.output,outputSchemas=activityOutputs.get(block.decision.key);requireValue(localKey(outputName)&&Object.hasOwn(outputSchemas??{},outputName),'AUTHORING_SEMANTIC','Choice output must name one declared decision output');
      const outputSchema=outputSchemas[outputName];requireValue(['string','boolean','number','integer'].includes(outputSchema.type),'AUTHORING_SEMANTIC',`Choice ${block.key} decision output ${outputName} must be scalar`);
      const branchValues=new Set();
      for(const branch of block.branches){requireChoiceValue(branch.value,outputSchema,block.key,outputName);const key=choiceValueKey(branch.value);requireValue(!branchValues.has(key),'AUTHORING_SEMANTIC',`Choice ${block.key} contains duplicate branch value ${JSON.stringify(branch.value)}`);branchValues.add(key);}
      const fallbackKey=semanticKeyOf(block.default),fallback=compileBlock(block.default),groups=new Map();
      for(const item of block.branches){
        const key=semanticKeyOf(item.body);
        if(key===fallbackKey)continue;
        const group=groups.get(key) ?? {body:item.body,values:[]};group.values.push(item.value);groups.set(key,group);
      }
      const parts=[...groups.values()].map(item=>({...item,part:compileBlock(item.body)})),sections=[...new Set([...decision.sections,...parts.flatMap(item=>item.part.sections),...fallback.sections])];
      if(parts.length===0){
        for(const source of decision.exits)for(const target of fallback.entries)addEdge(source,target,{section_ids:fallback.sections});
        result={entries:decisionPrecompiled?fallback.entries:decision.entries,exits:fallback.exits,sections};
      } else {
        const route=nodeId('condition'),path={path:`/nodes/${decision.entries[0]}/output/${outputName}`},labels=parts.map((_,index)=>`case_${index+1}`);
        nodes.push({id:route,type:'condition',semantic_key:block.key,cases:parts.map((item,index)=>({label:labels[index],when:item.values.length===1?{op:'eq',args:[path,{value:item.values[0]}]}:{op:'or',args:item.values.map(value=>({op:'eq',args:[path,{value}]}))}})),default_label:'default',confidence:1,...evidence(decision.sections)});
        // A precompiled producer may live inside a parallel branch. The
        // enclosing sequence connects its Join to this route; a direct edge
        // from the producer would bypass the Join and duplicate execution.
        if(!decisionPrecompiled)addEdge(decision.exits[0],route,{section_ids:decision.sections});parts.forEach(({part},index)=>part.entries.forEach(target=>addEdge(route,target,{label:labels[index],section_ids:part.sections})));fallback.entries.forEach(target=>addEdge(route,target,{label:'default',section_ids:fallback.sections}));
        result={entries:decisionPrecompiled?[route]:decision.entries,exits:[...new Set([...parts.flatMap(item=>item.part.exits),...fallback.exits])],sections};
      }
    }
    compilingBlocks.delete(semanticKey);compiledBlocks.set(semanticKey,result);return result;
  };
  const program=compileBlock(blueprint.program);
  for(const approval of approvalBindings){
    if(!approval.subject)continue;
    const separator=approval.subject.indexOf('.'),producerKey=approval.subject.slice(0,separator),output=approval.subject.slice(separator+1),producer=activityIds.get(producerKey);
    requireValue(separator>0&&producer&&Object.hasOwn(activityOutputs.get(producerKey)??{},output),'AUTHORING_SEMANTIC',`Approval ${approval.key} references unknown subject ${approval.subject}`);
    nodes.find(node=>node.id===approval.gate_id).input_bindings={subject:`/nodes/${producer}/output/${output}`};
  }
  for(const [key,id] of activityIds){
    const activity=findActivity(blueprint.program,key);const bindings={};
    for(const consume of activity?.consumes ?? []){
      requireValue(object(consume)&&localKey(consume.name)&&object(consume.from),'AUTHORING_FORMAT','Activity consumption needs a named source');
      if(consume.from.input)bindings[consume.name]=`/inputs/${consume.from.input}`;
      else if(consume.from.loop){const loopId=loopIds.get(consume.from.loop);requireValue(loopId,'AUTHORING_SEMANTIC','Consumed loop is unknown');bindings[consume.name]=`/loops/${loopId}/${consume.from.output}`;}
      else {const producer=activityIds.get(consume.from.activity),outputs=activityOutputs.get(consume.from.activity);requireValue(producer&&Object.hasOwn(outputs??{},consume.from.output),'AUTHORING_SEMANTIC','Consumed activity output is unknown');bindings[consume.name]=`/nodes/${producer}/output/${consume.from.output}`;}
    }
    nodes.find(item=>item.id===id).input_bindings=bindings;
  }
  for(const activity of blueprint.activities ?? [])if(activity.continues){
    const source=nodes.find(node=>node.id===activityIds.get(activity.key)),target=nodes.find(node=>node.id===activityIds.get(activity.continues));
    const direct=source&&target&&edges.some(edge=>edge.source===source.id&&edge.target===target.id&&(edge.on ?? 'success')==='success');
    const valid=direct&&['subagent','thread'].includes(source.execution_target)&&target.execution_target==='subagent'&&source.provider_choice&&source.provider_choice===target.provider_choice&&!source.fanout&&!target.fanout;
    requireValue(valid,'AUTHORING_SEMANTIC',`Task continuation ${activity.key} → ${activity.continues} needs direct one-to-one worker successors using the same Provider`,{findings:[{kind:'semantic',code:'task_continuation_invalid',message:`Task continuation ${activity.key} → ${activity.continues} needs direct one-to-one worker successors using the same Provider`,source_refs:source?.source_spans??[],semantic_keys:[activity.key,activity.continues],affected_semantic_fields:[`activities.${activity.key}.task_continues`,`activities.${activity.key}.profile`,`activities.${activity.continues}.profile`],blocked_by:[],minimal_change:'Use one-off worker activities unless the source requires a durable task; otherwise make these workers direct successors with one Provider and no fan-out.'}]});
    source.execution_target='thread';source.thread_lifecycle ??= 'start';
    target.execution_target='thread';target.thread_lifecycle='continue';target.thread_source_node=source.id;
  }
  addEdge('start',program.entries[0]);for(const source of program.exits)addEdge(source,'final');
  const loops=compileSemanticLoops({blueprint,nodes,edges,activityIds,activityOutputs,loopIds,nodeId,addEdge,evidence});
  const rules=(blueprint.semantic_rules ?? []).map((item,index)=>{
    requireValue(inventory.has(item.section_id)&&typeof item.statement==='string'&&item.statement.trim()&&Array.isArray(item.activity_keys)&&item.activity_keys.length>0,'AUTHORING_FORMAT','Semantic rules need source evidence, statement and responsible activities');
    return {requirement_id:`semantic_rule_${String(index+1).padStart(3,'0')}`,requirement_kind:'agent_judgment',source_spans:[inventory.get(item.section_id).source_span],trigger:item.applies_when || 'source_semantic_rule',required_result:item.statement,resource_refs:resourceRefsForSections([item.section_id]),details:{},activity_keys:item.activity_keys};
  });
  const mappings=rules.map(item=>({requirement_id:item.requirement_id,node_ids:item.activity_keys.map(key=>{const id=stageIds.get(key);requireValue(id,'AUTHORING_SEMANTIC',`Unknown stage ${key}`);return id;}),binding_names:[],runtime_guards:[],resource_refs:[...item.resource_refs],status:'agent_assisted',rationale:'Mapped from the semantic blueprint.'})),assignmentIds=new Set(),successEdges=edges.filter(edge=>(edge.on ?? 'success')==='success');
  const reaches=(source,target)=>{const seen=new Set(),queue=[source];while(queue.length){const current=queue.shift();if(current===target)return true;if(seen.has(current))continue;seen.add(current);queue.push(...successEdges.filter(edge=>edge.source===current).map(edge=>edge.target));}return false;};
  const missingUpstream=new Map();
  for(const consumer of nodes.filter(node=>node.type==='agent'||node.type==='tool'))for(const [input,binding] of Object.entries(consumer.input_bindings??{})){
    const producerId=typeof binding==='string'?/^\/nodes\/([^/]+)\/output(?:\/|$)/.exec(binding)?.[1]:null;
    if(!producerId||reaches(producerId,consumer.id))continue;
    const producer=nodes.find(node=>node.id===producerId);
    const pair=`${consumer.id}\u0000${producerId}`,entry=missingUpstream.get(pair)??{consumer,producer,producerId,inputs:[]};
    entry.inputs.push(input);missingUpstream.set(pair,entry);
  }
  const upstreamFindings=[...missingUpstream.values()].map(({consumer,producer,producerId,inputs})=>({kind:'semantic',code:'input_not_upstream',message:`Activity ${consumer.semantic_key} inputs ${inputs.join(', ')} need output from ${producer?.semantic_key??producerId}, but the declared control flow runs its producer later or on an exclusive route`,source_refs:structuredClone(consumer.source_spans??[]),semantic_keys:[consumer.semantic_key,producer?.semantic_key].filter(Boolean),affected_semantic_fields:[`activities.${consumer.semantic_key}.inputs`,'sequences','choices','parallels'],blocked_by:[],minimal_change:`Place ${producer?.semantic_key??producerId} before ${consumer.semantic_key} on every route that runs the consumer, or remove the dependency if it is not required.`}));
  requireValue(upstreamFindings.length===0,'AUTHORING_SEMANTIC','Declared data inputs are not produced upstream in the semantic control flow',{findings:upstreamFindings});
  const branchFindings=[];
  for(const consumer of nodes.filter(node=>node.type==='agent'||node.type==='tool'))for(const [input,binding] of Object.entries(consumer.input_bindings??{})){
    const producerId=typeof binding==='string'?/^\/nodes\/([^/]+)\/output(?:\/|$)/.exec(binding)?.[1]:null;
    if(!producerId)continue;
    const producer=nodes.find(node=>node.id===producerId);
    for(const condition of nodes.filter(node=>node.type==='condition')){
      const routes=successEdges.filter(edge=>edge.source===condition.id&&reaches(edge.target,consumer.id));
      if(routes.length<2||reaches(producerId,condition.id))continue;
      const missing=routes.filter(edge=>!reaches(edge.target,producerId));
      if(!missing.length)continue;
      branchFindings.push({kind:'semantic',code:'branch_input_missing',message:`Activity ${consumer.semantic_key} input ${input} reads ${producer?.semantic_key??producerId} on only some routes of choice ${condition.semantic_key}; missing routes: ${missing.map(edge=>edge.label).join(', ')}`,source_refs:structuredClone(consumer.source_spans??[]),semantic_keys:[consumer.semantic_key,producer?.semantic_key,condition.semantic_key].filter(Boolean),affected_semantic_fields:[`activities.${consumer.semantic_key}.inputs`,`choices.${condition.semantic_key}`,'sequences'],blocked_by:[],minimal_change:'Make this input available on every route, split downstream work by route, or terminate the route that does not produce it.'});
    }
  }
  requireValue(branchFindings.length===0,'AUTHORING_SEMANTIC','A downstream activity binds a branch-only output on an exclusive route',{findings:branchFindings});
  for(const approval of approvalBindings){
    if(!approval.subject)continue;
    const producer=activityIds.get(approval.subject.slice(0,approval.subject.indexOf('.')));
    requireValue(reaches(producer,approval.gate_id),'AUTHORING_SEMANTIC',`Approval ${approval.key} must occur after its subject ${approval.subject}`);
    for(const targetKey of approval.before){const target=activityIds.get(targetKey);requireValue(target&&reaches(approval.gate_id,target),'AUTHORING_SEMANTIC',`Approval ${approval.key} must occur before ${targetKey}`);}
  }
  rules.forEach(item=>delete item.activity_keys);
  for(const item of blueprint.requirement_assignments ?? []){
    requireValue(!assignmentIds.has(item.requirement_id)&&Array.isArray(item.activity_keys)&&item.activity_keys.length>0,'AUTHORING_FORMAT','Requirement assignments must be unique and name responsible semantic activities');assignmentIds.add(item.requirement_id);
    if(/^semantic_rule_\d+$/.test(item.requirement_id))continue;
    const requirement=observed.get(item.requirement_id);requireValue(requirement,'AUTHORING_SEMANTIC','Observed requirement assignments must name a known requirement');
    let keys=[...new Set(item.activity_keys)];
    if(requirement.requirement_kind==='approval'){
      const sectionIds=[...inventory].filter(([,section])=>(requirement.source_spans ?? []).some(span=>span.resource===section.source_span.resource&&span.start_line<=section.source_span.end_line&&span.end_line>=section.source_span.start_line)).map(([id])=>id);
      const explicit=(blueprint.approvals ?? []).filter(approval=>keys.includes(approval.key));
      const assignedActivities=new Set(keys.filter(key=>activityIds.has(key)));
      const sourceCandidates=(blueprint.approvals ?? []).filter(approval=>approval.source_sections.some(id=>sectionIds.includes(id)));
      const structuralCandidates=sourceCandidates.filter(approval=>{
        const subjectProducer=approval.subject?.split('.',1)[0];
        return (approval.before??[]).some(key=>assignedActivities.has(key))||(subjectProducer&&assignedActivities.has(subjectProducer));
      });
      const candidates=explicit.length?explicit:structuralCandidates.length?structuralCandidates:sourceCandidates;
      if(candidates.length){
        keys=[...new Set(candidates.flatMap(approval=>{
          const gateId=stageIds.get(approval.key);
          let protectedKeys=[...assignedActivities].filter(key=>reaches(gateId,activityIds.get(key)));
          if(!protectedKeys.length)protectedKeys=(approval.before??[]).filter(key=>activityIds.has(key)&&reaches(gateId,activityIds.get(key)));
          return [...protectedKeys,approval.key];
        }))];
      }
    }
    const node_ids=keys.map(key=>{const id=stageIds.get(key);requireValue(id,'AUTHORING_SEMANTIC',`Unknown stage ${key}`);return id;});
    const assignedNodes=node_ids.map(id=>nodes.find(node=>node.id===id)).filter(Boolean);
    const derivedBindings=[...new Set(assignedNodes.flatMap(node=>Object.entries(node.input_bindings ?? {}).filter(([,binding])=>requirement.requirement_kind!=='user_input' || bindingPointers(binding).some(pointer=>pointer.startsWith('/inputs/'))).map(([name])=>name)))];
    const binding_names=(item.binding_names ?? []).length ? [...new Set(item.binding_names)] : ['user_input','data_dependency'].includes(requirement.requirement_kind) ? derivedBindings : [];
    mappings.push({requirement_id:item.requirement_id,node_ids,binding_names,runtime_guards:item.runtime_guards ?? [],resource_refs:[...(requirement.resource_refs ?? [])],status:'agent_assisted',rationale:'Mapped from the semantic blueprint; Host projected concrete binding names from the assigned activities.'});
  }
  const source_dispositions=blueprint.source_dispositions.map(item=>({section_id:item.section_id,disposition:item.disposition,node_ids:(item.activity_keys ?? []).map(key=>{const id=stageIds.get(key);requireValue(id,'AUTHORING_SEMANTIC',`Unknown stage ${key}`);return id;}),requirement_ids:[],...(item.trigger?{trigger:item.trigger}:{}),rationale:item.reason || `Classified ${item.section_id} as ${item.disposition}.`}));
  const runtimeDependencies=compileRuntimeDependencyDecisions(blueprint,resources,inventory,resourceRefsForSections,stageIds,observed);
  for(const [index,item] of (blueprint.runtime_dependencies??[]).entries()){
    const disposition=source_dispositions.find(entry=>entry.section_id===item.source_section);
    if(disposition)disposition.requirement_ids=[...new Set([...disposition.requirement_ids,runtimeDependencies.requirements[index].requirement_id])];
  }
  const proposal={source_revision:pack.revision_hash,source_requirements:[...rules,...runtimeDependencies.requirements],requirement_mappings:[...mappings,...runtimeDependencies.mappings],source_dispositions,required_executables:[],planning_analysis:{parallelism:'Host-derived from nested semantic blocks.',main_responsibilities:'Host-derived from activity ownership.',human_intervention:'Host-derived from approval blocks.'},nodes,edges,...(loops.length?{loops}:{})};
  const loopIntentFindings=sourceRepairLoopIntentFindings(proposal,resources);
  requireValue(loopIntentFindings.length===0,'AUTHORING_SEMANTIC','The graph does not preserve the explicit source repair-loop contract',{findings:loopIntentFindings});
  return proposal;
}

function findActivity(block,key){
  if(block.kind==='activity'&&block.activity?.key===key)return block.activity;
  if(block.kind==='choice'&&block.decision?.key===key)return block.decision;
  const children=block.kind==='sequence'?block.steps:block.kind==='parallel'?block.branches:block.kind==='choice'?[...block.branches.map(item=>item.body),block.default]:[];
  for(const child of children){const found=findActivity(child,key);if(found)return found;}return null;
}

// Preflight supplies precise typed findings. A lowering error without one is a
// Host diagnostic gap, not permission to guess an ACL or send an unlocalized
// planner repair.
export function actionableSemanticError(error,_blueprint){
  if(error?.code!=='AUTHORING_SEMANTIC'||Array.isArray(error.findings)&&error.findings.length)return error;
  error.code='AUTHORING_DIAGNOSTIC_GAP';
  error.message=`Host lowering did not localize a semantic contradiction: ${String(error.message??'unknown')}`;
  return error;
}

export class WorkflowForge{
  compile({pack,resources,blueprint,context={}}){
    try{
      const proposal=lowerSemanticBlueprint(pack,resources,blueprint,context);
      const compiled=compileExpansion(pack,resources,proposal,context);
      return {proposal:compiled.canonical_proposal,compiled};
    }catch(error){throw actionableSemanticError(error,blueprint);}
  }
}
