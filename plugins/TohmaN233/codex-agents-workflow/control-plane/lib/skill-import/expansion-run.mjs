import { reviewSchema } from './review-checklist.mjs';
import { validateGenerationSettings } from './routing-rules.mjs';
import { requireValue } from '../workflow-paths.mjs';
import { canonicalJSON } from '../workflow-revisions.mjs';
import { expansionPacket } from './semantic-expander.mjs';
import { validateData } from '../workflow-data-schema.mjs';
import { bindingPointers } from '../workflow-bindings.mjs';
import { CONVERSION_CONTRACT } from './conversion-contract.mjs';
import { authoringSourcePath } from './authoring-source.mjs';
import { SEMANTIC_BLUEPRINT_SCHEMA, CURRENT_AUTHORING_SEMANTIC_BLUEPRINT_SCHEMA, SEMANTIC_REPAIR_SCHEMA, SEMANTIC_BLUEPRINT_CONTRACT, AUTHORING_NODE_PROMPT_MAX_LENGTH } from '../authoring/blueprint-contract.mjs';
import { AUTHORING_PLANNER_PROMPT_V27, AUTHORING_REVIEW_PROMPT_V22, authoringWorkflowForPack, instantiateAuthoringWorkflow, storedAuthoringBindings } from '../authoring/authoring-workflows.mjs';
import { LOOP_REGION_SCHEMA } from '../workflow-schema.mjs';
import { WORKSPACE_SOURCE_LOCATIONS } from '../workspace-source-locations.mjs';

// The finite runtime JSON-Schema vocabulary has no regular expressions; the
// compiler performs identifier and JSON-Pointer validation after this exact
// structural gate.
const id = { type: 'string', minLength: 1, maxLength: 128 };
const stringList = (max = 128) => ({ type: 'array', maxItems: max, items: { type: 'string', minLength: 1, maxLength: 1024 } });
const sourceSpan = { type: 'object', required: ['resource', 'start_line', 'end_line'], additionalProperties: false, properties: { resource: { type: 'string', minLength: 1, maxLength: 1024 }, start_line: { type: 'integer', minimum: 1 }, end_line: { type: 'integer', minimum: 1 } } };
const details = { type: 'object', additionalProperties: false, properties: { artifact_path: { type: 'string', minLength: 1, maxLength: 1024 }, interface_terms: stringList(32), rule_text: { type: 'string', minLength: 1, maxLength: 1000 }, executable: { type: 'string', minLength: 1, maxLength: 100 }, version:{type:'string',minLength:1,maxLength:256}, python_modules:stringList(128), phase: { type: 'string', enum: ['unconditional', 'conditional', 'artifact_only'] }, source_quote:{type:'string',minLength:1,maxLength:2000}, host_preparation_observation_ids:stringList(32), source_contract_ids:stringList(64) } };
const requirement = { type: 'object', required: ['requirement_id', 'requirement_kind', 'source_spans', 'trigger', 'required_result', 'resource_refs'], additionalProperties: false, properties: { requirement_id: id, requirement_kind: { type: 'string', enum: ['knowledge', 'agent_judgment', 'script_operation', 'registered_tool', 'approval', 'user_input', 'data_dependency', 'artifact_path', 'artifact_schema', 'canonicalization', 'method_rule', 'dependency'] }, source_spans: { type: 'array', minItems: 1, maxItems: 32, items: sourceSpan }, trigger: { type: 'string', minLength: 1, maxLength: 1000 }, required_result: { type: 'string', minLength: 1, maxLength: 2000 }, resource_refs: stringList(64), details } };
const mapping = { type: 'object', required: ['requirement_id', 'node_ids', 'binding_names', 'runtime_guards', 'resource_refs', 'status', 'rationale'], additionalProperties: false, properties: { requirement_id: id, node_ids: { type: 'array', maxItems: 64, items: id }, binding_names: { type: 'array', maxItems: 64, items: id }, runtime_guards: stringList(64), resource_refs: stringList(64), status: { type: 'string', enum: ['compiled', 'agent_assisted', 'unsupported'] }, rationale: { type: 'string', minLength: 1, maxLength: 2000 } } };
const disposition = { type: 'object', required: ['section_id', 'disposition', 'node_ids', 'requirement_ids', 'rationale'], additionalProperties: false, properties: { section_id: id, disposition: { type: 'string', enum: ['workflow', 'conditional', 'reference', 'omit'] }, node_ids: { type: 'array', maxItems: 64, items: id }, requirement_ids: { type: 'array', maxItems: 128, items: id }, trigger: { type: 'string', minLength: 1, maxLength: 1000 }, rationale: { type: 'string', minLength: 1, maxLength: 2000 } } };
// A finite recursive meta-schema: enough for nested artifact dictionaries,
// arrays and numeric report fields, without an untyped object escape hatch.
function outputSchemaAt(depth) {
  const child = depth > 0 ? outputSchemaAt(depth - 1) : { type: 'object', required: ['type'], additionalProperties: false, properties: {
    type: { type: 'string', enum: ['object','array','string','number','integer','boolean','null'] }, enum: {type:'array',minItems:1,maxItems:128,items:{}}, const: {},
    minimum:{type:'number'},exclusiveMinimum:{type:'number'},maximum:{type:'number'},exclusiveMaximum:{type:'number'},minLength:{type:'integer',minimum:0},maxLength:{type:'integer',minimum:0},pattern:{type:'string',minLength:1,maxLength:512}
  } };
  return { type: 'object', required: ['type'], additionalProperties: false, properties: {
    type: { type: 'string', enum: ['object', 'array', 'string', 'number', 'integer', 'boolean', 'null'] },
    // `additionalProperties` is the one union-valued JSON-Schema keyword: it
    // may be a boolean for closed objects or another schema for dynamic maps.
    // Leave only this slot open in the meta-schema; compileExpansion still
    // runs validateDataSchema over the emitted schema before review.
    properties: { type: 'object', additionalProperties: child }, required: stringList(64), additionalProperties: {}, items: child,
    enum: { type: 'array', minItems: 1, maxItems: 128, items: {} }, const: {},
    minimum: { type: 'number' }, exclusiveMinimum: { type: 'number' }, maximum: { type: 'number' }, exclusiveMaximum: {type:'number'}, minLength: { type: 'integer', minimum: 0 }, maxLength: { type: 'integer', minimum: 0 }, minItems: { type: 'integer', minimum: 0 }, maxItems: { type: 'integer', minimum: 0 }, uniqueItems: {type:'boolean'}, pattern: {type:'string',minLength:1,maxLength:512}
  } };
}
const outputSchema = outputSchemaAt(4);
const completionContract={type:'object',required:['on_missing','outcome'],additionalProperties:false,properties:{on_missing:{type:'string',enum:['block']},outcome:{type:'string',enum:['artifact','validated_artifact','decision','review','none']},fail_on_false:{type:'array',minItems:1,maxItems:128,items:id}}};
const subagentCount={enum:['auto',...Array.from({length:32},(_,index)=>index+1)]};
const fanout={type:'object',required:['input','item_name','result_output','distribution','scheduling','join'],additionalProperties:false,properties:{input:id,item_name:id,result_output:id,distribution:{type:'string',enum:['one_per_item','partition']},scheduling:{type:'string',const:'parallel'},join:{type:'string',const:'all_required'},batch_size:{type:'integer',minimum:1,maximum:32},max_concurrency:{type:'integer',minimum:1,maximum:32},result_mode:{type:'string',const:'per_item'},item_delivery:{type:'string',const:'incremental'},write_paths_field:id}};
const requiredArtifact={type:'object',required:['requirement_id','path'],additionalProperties:false,properties:{requirement_id:id,path:{type:'string',minLength:1,maxLength:1024}}};
const node = { type: 'object', required: ['id', 'type', 'confidence', 'source_span'], additionalProperties: false, properties: { id, semantic_key:id, name: { type: 'string', minLength: 1, maxLength: 256 }, type: { type: 'string', enum: ['agent', 'human_gate', 'condition', 'parallel', 'join', 'tool'] }, operation_mode: { type: 'string', enum: ['read', 'write'] }, task_type: { type: 'string', minLength: 1, maxLength: 128 }, routing_reason: { type: 'string', minLength: 1,maxLength:1000 }, execution_target: { type: 'string', enum: ['main', 'thread', 'subagent'] }, main_mode: {type:'string',enum:['worker','orchestration']}, provider_choice: id, thread_lifecycle: { type: 'string', enum: ['start', 'continue'] }, thread_source_node: id, prompt_template: { type: 'string', minLength: 1, maxLength: AUTHORING_NODE_PROMPT_MAX_LENGTH }, outputs_schema: outputSchema, output_validators:{type:'object',additionalProperties:{type:'string',const:WORKSPACE_SOURCE_LOCATIONS}}, completion_contract:completionContract, subagent_count:subagentCount, fanout, required_artifacts:{type:'array',maxItems:64,items:requiredArtifact}, cases: { type: 'array', maxItems: 64, items: { type: 'object', required: ['label', 'when'], additionalProperties: false, properties: { label: id, when: { type: 'object' } } } }, default_label: id, join_id: id, parallel_id: id, failure_policy: { type: 'string', enum: ['fail_fast', 'collect'] }, tool: id, input_bindings: { type: 'object' }, resource_refs: stringList(256), requirement_ids: { type: 'array', maxItems: 128, items: id }, retry_max_attempts:{type:'integer',minimum:1,maximum:5}, confidence: { type: 'number', minimum: 0, maximum: 1 }, source_span: sourceSpan, source_spans:{type:'array',minItems:1,maxItems:128,items:sourceSpan} } };
const edge = { type: 'object', required: ['id', 'source', 'target', 'confidence', 'source_span'], additionalProperties: false, properties: { id, source: id, target: id, on: { type: 'string', enum: ['success', 'failure'] }, label: id, confidence: { type: 'number', minimum: 0, maximum: 1 }, source_span: sourceSpan, source_spans:{type:'array',minItems:1,maxItems:128,items:sourceSpan} } };

// Current planners emit semantic choices only. The Host expands these into the
// strict persisted proposal below; old full proposals remain readable for
// durable recheck and migration.
const slimRule={type:'object',required:['section_id','statement','node_ids'],additionalProperties:false,properties:{section_id:id,statement:{type:'string',minLength:1,maxLength:2000},applies_when:{type:'string',minLength:1,maxLength:1000},node_ids:{type:'array',minItems:1,maxItems:64,items:id},rationale:{type:'string',minLength:1,maxLength:2000}}};
const slimMapping={type:'object',required:['requirement_id','node_ids'],additionalProperties:false,properties:{requirement_id:id,node_ids:{type:'array',minItems:1,maxItems:64,items:id},binding_names:{type:'array',maxItems:64,items:id},runtime_guards:stringList(64),rationale:{type:'string',minLength:1,maxLength:2000}}};
const slimDisposition={type:'object',required:['section_id','disposition','node_ids'],additionalProperties:false,properties:{section_id:id,disposition:{type:'string',enum:['workflow','conditional','reference','omit']},node_ids:{type:'array',maxItems:64,items:id},trigger:{type:'string',minLength:1,maxLength:1000},rationale:{type:'string',minLength:1,maxLength:2000}}};
const slimNode=structuredClone(node);for(const field of ['semantic_key','retry_max_attempts','confidence','source_span','source_spans','input_bindings','resource_refs','requirement_ids','required_artifacts','output_validators'])delete slimNode.properties[field];slimNode.required=['id','type','section_ids'];slimNode.properties.section_ids={type:'array',minItems:1,maxItems:32,items:id};
const slimEdge={type:'object',required:['source','target'],additionalProperties:false,properties:{source:id,target:id,on:{type:'string',enum:['success','failure']},label:id,section_id:id}};
export const SLIM_EXPANSION_PROPOSAL_SCHEMA={type:'object',required:['semantic_rules','observed_requirement_mappings','source_dispositions','nodes','edges'],additionalProperties:false,properties:{semantic_rules:{type:'array',maxItems:500,items:slimRule},observed_requirement_mappings:{type:'array',maxItems:500,items:slimMapping},source_dispositions:{type:'array',maxItems:200,items:slimDisposition},nodes:{type:'array',minItems:1,maxItems:200,items:slimNode},edges:{type:'array',maxItems:800,items:slimEdge}}};

export const EXPANSION_PROPOSAL_SCHEMA = { type: 'object', required: ['source_revision', 'source_requirements', 'requirement_mappings', 'source_dispositions', 'nodes', 'edges'], additionalProperties: false,
  properties: { source_requirements:{type:'array',maxItems:500,items:requirement},requirement_mappings:{type:'array',maxItems:500,items:mapping},source_dispositions:{type:'array',maxItems:200,items:disposition},required_executables:{type:'array',maxItems:100,items:{type:'object',required:['name','confidence','source_span'],additionalProperties:false,properties:{name:{type:'string',minLength:1,maxLength:100},version:{type:'string',minLength:1,maxLength:256},python_modules:stringList(128),confidence:{type:'number',minimum:0,maximum:1},source_span:sourceSpan}}}, planning_analysis: {type:'object',required:['parallelism','main_responsibilities','human_intervention'],additionalProperties:false,properties:Object.fromEntries(['parallelism','main_responsibilities','human_intervention'].map(k=>[k,{type:'string',minLength:1,maxLength:4000}]))}, source_revision: { type: 'string' }, nodes: { type: 'array', minItems: 1, maxItems: 200, items: node }, edges: { type: 'array', maxItems: 800, items: edge } } };

export const GENERATED_PROPOSAL_ENVELOPE_SCHEMA = Object.freeze({
  type: 'object',
  required: ['proposal'],
  additionalProperties: false,
  properties: { proposal: SEMANTIC_BLUEPRINT_SCHEMA },
});
export const GENERATED_PROPOSAL_ENVELOPE_SCHEMA_V21 = Object.freeze({type:'object',required:['proposal'],additionalProperties:false,properties:{proposal:CURRENT_AUTHORING_SEMANTIC_BLUEPRINT_SCHEMA}});
EXPANSION_PROPOSAL_SCHEMA.properties.loops = {type:'array',maxItems:200,items:LOOP_REGION_SCHEMA};
export const GENERATED_REPAIR_ENVELOPE_SCHEMA = Object.freeze({type:'object',required:['proposal'],additionalProperties:false,properties:{proposal:SEMANTIC_REPAIR_SCHEMA}});
// Runtime persistence accepts either attempt contract. The Strict session picks
// the exact initial/repair schema before each turn, so this union boundary never
// weakens model output validation.
export const AUTHORING_RUNTIME_ENVELOPE_SCHEMA = Object.freeze({});

export function decodeGeneratedEnvelope(output){
  requireValue(output && typeof output==='object' && !Array.isArray(output),'GENERATION_PROPOSAL_ENVELOPE','Generated proposal must use the host JSON envelope');
  const direct=Object.keys(output).length===1 && output.proposal && typeof output.proposal==='object' && !Array.isArray(output.proposal);
  const legacy=Object.keys(output).length===1 && typeof output.proposal_json==='string';
  requireValue(direct || legacy,'GENERATION_PROPOSAL_ENVELOPE','Generated proposal envelope must contain only proposal');
  if(direct)return structuredClone(output.proposal);
  try{return JSON.parse(output.proposal_json);}catch{requireValue(false,'GENERATION_PROPOSAL_JSON','proposal_json must contain one valid JSON object');}
}

function valueType(value) {
  if (value===null) return 'null';
  if (Array.isArray(value)) return 'array';
  if (Number.isInteger(value)) return 'integer';
  return typeof value;
}

function canonicalizeOutputSchema(schema, repairs, path) {
  if (!schema || typeof schema!=='object' || Array.isArray(schema)) return;
  if (schema.type===undefined) {
    if (Object.hasOwn(schema,'const')) schema.type=valueType(schema.const);
    else if (Array.isArray(schema.enum) && schema.enum.length) {
      const types=[...new Set(schema.enum.map(valueType))];
      if (types.length===1) schema.type=types[0];
    } else if (schema.properties!==undefined) schema.type='object';
    else if (schema.items!==undefined) schema.type='array';
    if (schema.type!==undefined) repairs.push({kind:'schema_type_inferred',path,type:schema.type});
  }
  if (schema.properties && typeof schema.properties==='object' && !Array.isArray(schema.properties)) for (const [name,child] of Object.entries(schema.properties)) canonicalizeOutputSchema(child,repairs,`${path}/properties/${name}`);
  if (schema.type==='object' && schema.properties && schema.required===undefined) {schema.required=Object.keys(schema.properties);repairs.push({kind:'schema_required_derived',path});}
  if (schema.type==='object' && schema.additionalProperties===undefined) {schema.additionalProperties=false;repairs.push({kind:'schema_closed_by_host',path});}
  if (schema.items) canonicalizeOutputSchema(schema.items,repairs,`${path}/items`);
  if (schema.additionalProperties && typeof schema.additionalProperties==='object' && !Array.isArray(schema.additionalProperties)) canonicalizeOutputSchema(schema.additionalProperties,repairs,`${path}/additionalProperties`);
}

function canonicalizeConditionCases(proposal, repairs) {
  if (!Array.isArray(proposal.nodes) || !Array.isArray(proposal.edges)) return;
  const pointer=path=>path.split('.').map(part=>part.replaceAll('~','~0').replaceAll('/','~1')).join('/');
  for (const node of proposal.nodes) {
    if (node?.type!=='condition' || !Array.isArray(node.cases)) continue;
    const predecessors=[...new Set(proposal.edges.filter(edge=>edge?.target===node.id && edge.source!=='start').map(edge=>edge.source))];
    if (predecessors.length!==1) continue;
    for (const item of node.cases) if (typeof item?.when==='string') {
      const match=/^([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*)\s*&&\s*!\s*([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*)$/.exec(item.when.trim());
      if (!match) continue;
      const base=`/nodes/${predecessors[0]}/output/`;
      item.when={op:'and',args:[
        {op:'eq',args:[{path:base+pointer(match[1])},{value:true}]},
        {op:'eq',args:[{path:base+pointer(match[2])},{value:false}]},
      ]};
      repairs.push({kind:'condition_expression_canonicalized',node_id:node.id,label:item.label});
    }
  }
  const conditionIds=new Set(proposal.nodes.filter(node=>node?.type==='condition').map(node=>node.id));
  for (const edge of proposal.edges) if (conditionIds.has(edge?.source) && typeof edge.on==='string' && !['success','failure'].includes(edge.on) && edge.label===undefined) {
    repairs.push({kind:'condition_edge_label_canonicalized',edge_id:edge.id,label:edge.on});edge.label=edge.on;delete edge.on;
  }
}

function derivePlanningAnalysis(nodes,_edges){
  const parallel=nodes.filter(item=>item.type==='parallel').map(item=>item.id);
  const main=nodes.filter(item=>item.type==='agent' && item.execution_target==='main').map(item=>item.id);
  const subagents=nodes.filter(item=>item.type==='agent' && item.execution_target==='subagent').map(item=>item.id);
  const threads=nodes.filter(item=>item.type==='agent' && item.execution_target==='thread').map(item=>item.id);
  const gates=nodes.filter(item=>item.type==='human_gate').map(item=>item.id);
  return {
    parallelism:parallel.length?`The graph declares ${parallel.length} explicit parallel region(s): ${parallel.join(', ')}; all other ordering is defined by the accepted edges.`:'The graph declares no parallel region; ordering is defined by the accepted dependency edges.',
    main_responsibilities:`Main nodes: ${main.length?main.join(', '):'none'}. One-off Provider sub-Agents: ${subagents.length?subagents.join(', '):'none'}. Persistent Codex tasks: ${threads.length?threads.join(', '):'none'}.`,
    human_intervention:gates.length?`Explicit human approval gates: ${gates.join(', ')}. Future Run parameters are supplied through the workflow input contract.`:'No in-Run human approval gate is declared. Future Run parameters are supplied through the workflow input contract.',
  };
}

function expandSemanticProposal(proposal,sourceInventory,expectedRevision,repairs){
  if(!Object.hasOwn(proposal,'semantic_rules'))return proposal;
  proposal=structuredClone(proposal);
  for(const item of proposal.nodes ?? [])canonicalizeOutputSchema(item?.outputs_schema,repairs,`/nodes/${item?.id ?? 'unknown'}/outputs_schema`);
  canonicalizeConditionCases(proposal,repairs);
  validateData(proposal,SLIM_EXPANSION_PROPOSAL_SCHEMA);
  const sections=new Map((sourceInventory ?? []).map(section=>[section.section_id,section]));
  const span=id=>{const section=sections.get(id);requireValue(section,'GENERATION_PROPOSAL_CONTRACT',`Unknown source section ${id}`);return structuredClone(section.source_span);};
  const coveringSpan=ids=>{
    const spans=ids.map(span),resources=[...new Set(spans.map(item=>item.resource))];
    requireValue(resources.length===1,'GENERATION_PROPOSAL_CONTRACT','One node cannot cite source sections from different resources');
    return {resource:resources[0],start_line:Math.min(...spans.map(item=>item.start_line)),end_line:Math.max(...spans.map(item=>item.end_line))};
  };
  const nodeIds=new Set(proposal.nodes.map(item=>item.id));
  const nodes=proposal.nodes.map(item=>{
    const section_ids=[...new Set(item.section_ids)];const source_span=coveringSpan(section_ids);
    const result={...structuredClone(item),confidence:1,source_span};delete result.section_ids;return result;
  });
  const semanticRequirements=proposal.semantic_rules.map((item,index)=>({requirement_id:`semantic_rule_${String(index+1).padStart(3,'0')}`,requirement_kind:'agent_judgment',source_spans:[span(item.section_id)],trigger:item.applies_when ?? 'source_semantic_rule',required_result:item.statement,resource_refs:[],details:{}}));
  const semanticMappings=proposal.semantic_rules.map((item,index)=>({requirement_id:`semantic_rule_${String(index+1).padStart(3,'0')}`,node_ids:item.node_ids,binding_names:[],runtime_guards:[],resource_refs:[],status:'agent_assisted',rationale:item.rationale ?? `Retained semantic rule from ${item.section_id}.`}));
  for(const item of [...proposal.semantic_rules,...proposal.observed_requirement_mappings])requireValue(item.node_ids.every(nodeId=>nodeIds.has(nodeId)),'GENERATION_PROPOSAL_CONTRACT','Semantic mappings must name generated nodes');
  const observedMappings=proposal.observed_requirement_mappings.map(item=>({requirement_id:item.requirement_id,node_ids:item.node_ids,binding_names:item.binding_names ?? [],runtime_guards:item.runtime_guards ?? [],resource_refs:[],status:'agent_assisted',rationale:item.rationale ?? `Mapped host-observed requirement ${item.requirement_id} to its selected responsible nodes.`}));
  const nodeSpan=new Map(nodes.map(item=>[item.id,item.source_span]));
  const edges=proposal.edges.map((item,index)=>({id:`edge_${String(index+1).padStart(3,'0')}`,...structuredClone(item),confidence:1,source_span:item.section_id?span(item.section_id):structuredClone(nodeSpan.get(item.target) ?? nodeSpan.get(item.source) ?? (sourceInventory?.[0]?.source_span))}));
  for(const item of edges)delete item.section_id;
  const source_dispositions=proposal.source_dispositions.map(item=>({...structuredClone(item),requirement_ids:[],rationale:item.rationale ?? `Classified ${item.section_id} as ${item.disposition}.`}));
  const planning_analysis=derivePlanningAnalysis(nodes,edges);
  repairs.push({kind:'host_semantic_proposal_compiled',fields:['source_revision','typed_requirements','mapping_status','source_spans','confidence','workflow_bindings','planning_analysis','rationales']});
  return {source_revision:expectedRevision ?? '',source_requirements:semanticRequirements,requirement_mappings:[...semanticMappings,...observedMappings],source_dispositions,nodes,edges,planning_analysis};
}

export function decodeGeneratedProposalDetailed(output, expectedRevision = null, { requirePlanningAnalysis = false, requireSourceDispositions = false, requireRuntimeDependencies = false, sourceInventory = null } = {}) {
  let proposal=decodeGeneratedEnvelope(output);
  requireValue(proposal && typeof proposal === 'object' && !Array.isArray(proposal), 'GENERATION_PROPOSAL_JSON', 'proposal_json must decode to one JSON object');
  if(requireRuntimeDependencies&&proposal.contract===SEMANTIC_BLUEPRINT_CONTRACT)requireValue(Array.isArray(proposal.runtime_dependencies),'GENERATION_DEPENDENCY_ASSESSMENT','Current authoring plans must explicitly decide runtime_dependencies, including []');
  const repairs=[];
  try{proposal=expandSemanticProposal(proposal,sourceInventory,expectedRevision,repairs);}catch(error){requireValue(false,'GENERATION_PROPOSAL_CONTRACT',error.message);}
  // `details` is a typed extension bag, not a semantic decision. Keep the
  // planner contract minimal and canonicalize its absent representation here.
  if (Array.isArray(proposal.source_requirements)) for (const requirement of proposal.source_requirements) {
    if (requirement && typeof requirement==='object' && !Array.isArray(requirement) && requirement.details===undefined) { requirement.details={}; repairs.push({kind:'requirement_details_defaulted',requirement_id:requirement.requirement_id}); }
  }
  if (Array.isArray(proposal.nodes)) for (const node of proposal.nodes) {
    if (['tool','human_gate'].includes(node?.type) && node.outputs_schema!==undefined) { delete node.outputs_schema; repairs.push({kind:'host_output_schema_removed',node_id:node.id}); }
    else canonicalizeOutputSchema(node?.outputs_schema,repairs,`/nodes/${node?.id ?? 'unknown'}/outputs_schema`);
  }
  canonicalizeConditionCases(proposal,repairs);
  // The immutable source revision is pinned by the host that created this
  // generation Run. It is not a semantic planner decision and must never fail
  // because a model copied a long digest incorrectly (or tried to replace it).
  if (expectedRevision !== null && proposal.source_revision !== expectedRevision) { proposal.source_revision = expectedRevision; repairs.push({kind:'source_revision_injected'}); }
  const schema = structuredClone(EXPANSION_PROPOSAL_SCHEMA);
  if (!requireSourceDispositions) schema.required = schema.required.filter(field => field !== 'source_dispositions');
  if (expectedRevision !== null) schema.properties.source_revision.const = expectedRevision;
  if (requirePlanningAnalysis && !schema.required.includes('planning_analysis')) schema.required.push('planning_analysis');
  try { validateData(proposal, schema); }
  catch (error) { requireValue(false, 'GENERATION_PROPOSAL_CONTRACT', error.message); }
  for(const item of proposal.nodes ?? [])for(const binding of Object.values(item.input_bindings ?? {}))try{bindingPointers(binding);}catch(error){requireValue(false,'GENERATION_PROPOSAL_CONTRACT',error.message);}
  return {proposal,repairs};
}

export function decodeGeneratedProposal(output, expectedRevision = null, options = {}) {
  return decodeGeneratedProposalDetailed(output,expectedRevision,options).proposal;
}

export function authoringRunPack(pack, resources, provider, id, routingRules, _automatic = false, reviewer = null, providers = [], authoringTemplate = null) {
  // Every authoring Run carries the same review contract. The service-level
  // automatic flag controls Host advancement/repair only; it cannot weaken the
  // pinned Workflow or turn checklist review into an optional execution mode.
  const generation = validateGenerationSettings(routingRules?.generation);
  requireValue(reviewer?.id===generation.review_provider_id && reviewer.enabled && reviewer.kind==='native_agent' && reviewer.capabilities.read,'GENERATION_REVIEW_PROVIDER','Choose an enabled native Provider with read capability for review');
  const packet = expansionPacket(pack, resources, provider, routingRules, providers, {audience:'planner'});
  const reviewPacket = expansionPacket(pack, resources, provider, routingRules, providers, {audience:'reviewer'});
  const authoring=authoringWorkflowForPack(pack);
  if(authoringTemplate){
    requireValue(authoringTemplate.workflow?.id===authoring.id,'AUTHORING_WORKFLOW_SOURCE','Source kind selected a different stored authoring Workflow');
    const bindings=storedAuthoringBindings(authoringTemplate.workflow,providers);
    requireValue(bindings.planner.id===provider?.id,'AUTHORING_WORKFLOW_PROVIDER','Planner Provider must come from the stored authoring Workflow');
    requireValue(bindings.reviewer.id===reviewer?.id,'AUTHORING_WORKFLOW_PROVIDER','Reviewer Provider must come from the stored authoring Workflow');
  }
  requireValue(provider.kind === 'native_agent', 'EXPANSION_EXECUTOR_UNAVAILABLE', 'Managed expansion currently requires a user-selected native Provider with qualified Strict execution');
  requireValue(!Object.hasOwn(resources, 'analysis/request.txt') && !Object.hasOwn(resources, 'analysis/review-request.txt'), 'EXPANSION_RESOURCE_CONFLICT', 'Source resources collide with an authoring request');
  const observations={observed_dependencies:pack.import_report?.observed_dependencies ?? [],problems:pack.import_report?.problems ?? []};
  const suffix='\nAdditional static observations (data):\n'+canonicalJSON(observations);
  const planningResources = { ...resources, 'analysis/request.txt': packet.prompt + suffix, 'analysis/review-request.txt':reviewPacket.prompt+suffix };
  // analysis/request.txt already embeds the complete numbered entrypoint. Keep
  // the immutable source in the Pack, but omit the duplicate path from both
  // model resource manifests so a planner/reviewer cannot spend another full
  // read on identical text. Referenced sibling files remain available.
  const plannerResources = Object.keys(planningResources).filter(path => path !== authoringSourcePath(resources) && path!=='analysis/review-request.txt').sort();
  const reviewResources = Object.keys(planningResources).filter(path => path !== authoringSourcePath(resources) && path!=='analysis/request.txt').sort();
  const plannerPrompt=AUTHORING_PLANNER_PROMPT_V27;
  const reviewPrompt=AUTHORING_REVIEW_PROMPT_V22;
  const workflow=instantiateAuthoringWorkflow({definition:authoring,templateWorkflow:authoringTemplate?.workflow,id,sourceName:pack.workflow.name,planner:provider,reviewer,generation,planningResources,plannerResources,reviewResources,plannerSchema:AUTHORING_RUNTIME_ENVELOPE_SCHEMA,plannerPrompt,reviewSchema:generation?reviewSchema(CONVERSION_CONTRACT.version):null,reviewPrompt});
  return { workflow, resources: planningResources,
    provenance: { kind: 'authoring_workflow_run', legacy_kind:'skill_expansion_job', authoring_workflow_id:authoring.id, authoring_contract:authoringTemplate?.workflow.authoring?.contract??authoring.contract, ...(authoringTemplate?{authoring_workflow_revision:authoringTemplate.revision_hash}:{}), source_kind:authoring.source_kind, ...(generation ? {generation,review_contract_version:CONVERSION_CONTRACT.version} : {}), source_workflow_id: pack.workflow.id, source_revision: pack.revision_hash, selected_provider_id: provider.id, review_provider_id:reviewer.id, ...(routingRules ? { routing_rules: structuredClone(routingRules), routing_catalog:packet.routing_catalog } : {}) },
    import_report: null };
}

// Persisted v2/v3 callers use the historical name. New code enters through
// authoringRunPack so the public architecture no longer describes authoring as
// an expansion side effect.
export const expansionRunPack=authoringRunPack;
