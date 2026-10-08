import { informationalImportObservation } from './workflow-import-observations.mjs';
import { nativeBindingIssue } from './native-binding.mjs';
import { NODE_TYPES, HUMAN_GATE_OUTPUT, validateWorkflowShape } from './workflow-schema.mjs';
import { workflowId } from './workflow-paths.mjs';
import { bindingPointers, pathBoundaries, pointerParts, validateExpression } from './workflow-bindings.mjs';
import { validateDataSchema, validateData } from './workflow-data-schema.mjs';
import { validateSkillReference, effectiveSkillPolicy } from './workflow-reference-schema.mjs';
import { skillPathKey } from './execution/codex-skill-policy.mjs';
import { assertThreadExecutor } from './thread-handoff.mjs';
import { threadLineage } from './thread-protocol.mjs';
import { hostToolContracts } from './execution/host-tool-runner.mjs';
import { validateNodeCost } from './workflow-cost-ledger.mjs';
import { managedNativeResultSchema } from './execution/host-main-automation.mjs';
import { normalizeExecutableRequirements } from './runtime-requirements.mjs';
import { isOperationalMemoryArtifactPath } from './artifact-policy.mjs';
import { WORKSPACE_SOURCE_LOCATIONS } from './workspace-source-locations.mjs';
import {firstAgentTranscriptionClause,hostOwnedAgentField} from './agent-transcription-policy.mjs';
import { validateLoopRegions } from './workflow-loops.mjs';

const EXECUTED = new Set(['agent', 'skill_ref', 'tool', 'human_gate', 'subworkflow']);
const SHA = /^[a-f0-9]{64}$/;
const object = value => value !== null && typeof value === 'object' && !Array.isArray(value);
function requiredHostOwnedAgentFields(schema,prefix='',found=[]){
  if(!object(schema))return found;
  if(schema.type==='array')return requiredHostOwnedAgentFields(schema.items,prefix+'[]',found);
  if(schema.type!=='object'||!object(schema.properties))return found;
  for(const name of schema.required??[]){
    const path=prefix?`${prefix}.${name}`:name;
    if(hostOwnedAgentField(name))found.push(path);
    requiredHostOwnedAgentFields(schema.properties[name],path,found);
  }
  return found;
}
function schemaAtPointer(pointer,workflow,nodes,visiting=new Set()){
  const parts=pointerParts(pointer);let schema,index;
  if(parts[0]==='inputs'){schema=workflow.inputs_schema??{};index=1;}
  else if(parts[0]==='nodes'&&nodes.has(parts[1])&&parts[2]==='output'){schema=nodes.get(parts[1]).outputs_schema??{};index=3;}
  else if(parts[0]==='loops'){
    const loop=(workflow.loops??[]).find(item=>item.id===parts[1]);
    if(!loop||visiting.has(loop.id))return null;
    const next=new Set(visiting);next.add(loop.id);
    if(['review_items','repair_items'].includes(parts[2])&&loop.item_scope){
      const binding=loop.item_scope.items,pointers=bindingPointers(binding);
      schema=pointers.length===1?schemaAtPointer(pointers[0],workflow,nodes,next):null;
      if(!schema)return null;
      schema=structuredClone(schema);
      if(parts[2]==='repair_items'&&schema.items?.type==='object'){
        schema.items.properties={...schema.items.properties,findings:{}};
        schema.items.required=[...new Set([...(schema.items.required??[]),'findings'])];
      }
      index=3;
    } else if(parts[2]==='feedback'&&parts[3]&&Object.hasOwn(loop.feedback_bindings??{},parts[3])){
      const pointers=bindingPointers(loop.feedback_bindings[parts[3]]);
      schema=pointers.length===1?schemaAtPointer(pointers[0],workflow,nodes,next):null;index=4;
    }else if(['round','status','all_accepted'].includes(parts[2])){schema={type:parts[2]==='round'?'integer':parts[2]==='status'?'string':'boolean'};index=3;}
    else return null;
  }
  else return null;
  for(;index<parts.length;index++){
    const part=parts[index];
    if(schema?.type==='array'&&/^\d+$/.test(part)){schema=schema.items;continue;}
    if(object(schema?.properties)&&Object.hasOwn(schema.properties,part)){schema=schema.properties[part];continue;}
    if(object(schema?.additionalProperties)){schema=schema.additionalProperties;continue;}
    return null;
  }
  return schema;
}
function arrayRange(schema){
  if(!object(schema))return {known:false};
  if(schema.type!==undefined&&schema.type!=='array')return {known:true,array:false};
  const literal=[];
  if(Object.hasOwn(schema,'const'))literal.push(schema.const);
  if(Array.isArray(schema.enum))literal.push(...schema.enum);
  if(literal.length){
    if(literal.some(value=>!Array.isArray(value)))return {known:true,array:false};
    const lengths=literal.map(value=>value.length);return {known:true,array:true,min:Math.min(...lengths),max:Math.max(...lengths)};
  }
  if(schema.type==='array')return {known:true,array:true,min:schema.minItems??0,max:schema.maxItems??Infinity};
  return {known:false};
}
function fanoutInputRange(binding,workflow,nodes){
  if(object(binding)&&Object.hasOwn(binding,'flat_map')){
    const outer=schemaAtPointer(binding.path,workflow,nodes);
    const inner=outer?.items?.properties?.[binding.flat_map];
    if(outer?.type!=='array'||inner?.type!=='array')return {invalid:true};
    return {known:false,unknown:true};
  }
  const ranges=[];let unknown=false;
  for(const pointer of bindingPointers(binding)){
    const range=arrayRange(schemaAtPointer(pointer,workflow,nodes));
    if(range.known&&!range.array)return {invalid:true};
    if(range.known)ranges.push(range);else unknown=true;
  }
  if(object(binding)&&Object.hasOwn(binding,'default')){
    if(!Array.isArray(binding.default))return {invalid:true};
    ranges.push({known:true,array:true,min:binding.default.length,max:binding.default.length});
  }
  if(!ranges.length)return {known:false,unknown:true};
  return {known:true,unknown,min:Math.min(...ranges.map(item=>item.min)),max:Math.max(...ranges.map(item=>item.max))};
}

export function validateWorkflowGraph(workflow, context = {}, stack = []) {
  const errors = []; const blockers = [];
  const issue = (code, message, location = {}, target = errors) => target.push({ code, message, workflow_id: workflow?.id ?? null, ...location });
  if (stack.length > 32) { issue('SUBWORKFLOW_DEPTH', 'SubWorkflow nesting limit exceeded'); return { valid: false, launch_ready: false, errors, blockers, order: [] }; }
  try { validateWorkflowShape(workflow); } catch (error) { issue(error.code ?? 'WORKFLOW_SCHEMA', error.message); return { valid: false, launch_ready: false, errors, blockers, order: [] }; }
  try { effectiveSkillPolicy(workflow.skill_policy); } catch (error) { issue(error.code, error.message); return { valid: false, launch_ready: false, errors, blockers, order: [] }; }
  if (workflow.context_projection_version !== 2) issue('CONTEXT_PROJECTION_VERSION', 'Current Workflows must use declared-only context projection version 2');
  let toolContracts = new Map();
  try { toolContracts = hostToolContracts(workflow); } catch (error) { issue(error.code, error.message); }
  for (const key of ['inputs_schema', 'outputs_schema']) try { validateDataSchema(workflow[key] ?? {}); } catch (error) { issue(error.code, error.message, { field: key }); }
  const providers = new Map((context.providers ?? []).map(provider => [provider.id, provider]));
  const nodes = new Map(); const edges = new Map();
  for (const node of workflow.nodes) {
    if (!object(node)) { issue('NODE_SCHEMA', 'Node must be an object'); continue; }
    try { workflowId(node.id); } catch { issue('NODE_ID', 'Invalid node ID', { node_id: node.id }); continue; }
    if (nodes.has(node.id)) issue('NODE_DUPLICATE', 'Duplicate node ID', { node_id: node.id });
    else nodes.set(node.id, node);
    if (!NODE_TYPES.has(node.type)) issue('NODE_TYPE', 'Unsupported node type', { node_id: node.id });
    if (node.outputs_schema !== undefined) try { validateDataSchema(node.outputs_schema); } catch (error) { issue(error.code, error.message, { node_id: node.id }); }
    if(['agent','skill_ref'].includes(node.type)){
      const transcription=firstAgentTranscriptionClause(node.prompt_template);
      if(transcription)issue('AGENT_DETERMINISTIC_TRANSCRIPTION',
        'Agent instructions require copying pre-existing or Host-owned fields; bind them directly or use a registered Host tool',
        {node_id:node.id,instruction_clause:transcription.trim().slice(0,512)});
      for(const [name,schema] of Object.entries(node.outputs_schema?.properties??{})){
        if(node.output_validators?.[name]===WORKSPACE_SOURCE_LOCATIONS)continue;
        const copied=requiredHostOwnedAgentFields(schema,name);
        if((node.outputs_schema.required??[]).includes(name)&&hostOwnedAgentField(name))copied.unshift(name);
        const inputs=new Set(Object.keys(node.input_bindings??{}));
        const repeated=copied.filter(path=>path.split(/[.\[\]]+/).some(part=>inputs.has(part)));
        if(repeated.length)issue('AGENT_DETERMINISTIC_TRANSCRIPTION',
          `Agent output repeats Host-owned input fields: ${repeated.join(', ')}`,{node_id:node.id,field:`outputs_schema.properties.${name}`});
      }
    }
    if (node.completion_contract !== undefined) {
      const contract=node.completion_contract,outcome=contract?.outcome,hasOutputs=object(node.outputs_schema)&&Object.keys(node.outputs_schema).length>0;
      if (!object(contract)||Object.keys(contract).some(key=>!['on_missing','outcome','fail_on_false'].includes(key))||contract.on_missing!=='block'||!['artifact','validated_artifact','decision','review','none'].includes(outcome)) issue('COMPLETION_CONTRACT','Completion contract must declare supported missing-input and outcome semantics',{node_id:node.id});
      else if (outcome==='none'&&hasOutputs||['artifact','validated_artifact','decision'].includes(outcome)&&!hasOutputs) issue('COMPLETION_CONTRACT','Completion outcome and declared output schema disagree',{node_id:node.id});
      else if(contract.fail_on_false!==undefined&&(!Array.isArray(contract.fail_on_false)||!contract.fail_on_false.length||new Set(contract.fail_on_false).size!==contract.fail_on_false.length||contract.fail_on_false.some(name=>typeof name!=='string'||node.outputs_schema?.properties?.[name]?.type!=='boolean'||!(node.outputs_schema?.required??[]).includes(name)))) issue('COMPLETION_CONTRACT','False-result guards must name unique required boolean node outputs',{node_id:node.id});
    }
    if(node.subagent_count!==undefined){
      if(node.type!=='agent'||node.executor?.kind==='main'||!(node.subagent_count==='auto'||Number.isInteger(node.subagent_count)&&node.subagent_count>=1&&node.subagent_count<=32))issue('SUBAGENT_COUNT','Sub-Agent count is available only on non-Main Agent nodes and must be auto or an integer from 1 to 32',{node_id:node.id});
      if(node.executor?.kind==='thread'&&node.executor.lifecycle==='continue'&&(node.subagent_count!=='auto'||node.fanout))issue('SUBAGENT_COUNT','A continued Codex task is one exact conversation and cannot be multiplied',{node_id:node.id});
      if(Number.isInteger(node.subagent_count)&&node.subagent_count>1&&!node.fanout)issue('SUBAGENT_FANOUT','More than one sub-Agent needs an explicit runtime list fan-out and all-required join contract',{node_id:node.id});
    }
    if(node.fanout!==undefined){
      const contract=node.fanout,properties=node.outputs_schema?.properties??{},result=properties[contract?.result_output],required=node.outputs_schema?.required??[];
      if(node.type!=='agent'||node.executor?.kind==='main'||node.subagent_count===undefined||!object(contract)||Object.keys(contract).some(key=>!['input','item_name','result_output','distribution','scheduling','join','batch_size','max_concurrency','result_mode','write_paths_field','shared_change_field','item_delivery'].includes(key))||contract.result_mode!==undefined&&contract.result_mode!=='per_item'||contract.result_mode==='per_item'&&(node.executor?.kind!=='provider'||providers.get(node.executor?.provider_id)?.kind!=='native_agent')||contract.item_delivery!==undefined&&contract.item_delivery!=='incremental'||contract.item_delivery==='incremental'&&(contract.result_mode!=='per_item'||contract.distribution!=='partition'||!Number.isInteger(contract.batch_size)||contract.batch_size<2)||contract.write_paths_field!==undefined&&(node.access!=='bounded_write'||typeof contract.write_paths_field!=='string'||!/^[A-Za-z][A-Za-z0-9_-]{0,127}$/.test(contract.write_paths_field))||contract.shared_change_field!==undefined&&(contract.result_mode!=='per_item'||contract.write_paths_field===undefined||typeof contract.shared_change_field!=='string'||!/^[A-Za-z][A-Za-z0-9_-]{0,127}$/.test(contract.shared_change_field))||typeof contract.input!=='string'||!Object.hasOwn(node.input_bindings??{},contract.input)||typeof contract.item_name!=='string'||!contract.item_name||typeof contract.result_output!=='string'||result?.type!=='array'||!result.items||Object.keys(properties).length!==1||required.length!==1||required[0]!==contract.result_output||!['one_per_item','partition'].includes(contract.distribution)||!['parallel','serial'].includes(contract.scheduling)||contract.max_concurrency!==undefined&&(!Number.isInteger(contract.max_concurrency)||contract.max_concurrency<1||contract.max_concurrency>32||contract.scheduling!=='parallel'||providers.get(node.executor?.provider_id)?.kind!=='native_agent')||contract.scheduling==='serial'&&providers.get(node.executor?.provider_id)?.kind!=='native_agent'||contract.join!=='all_required'||contract.distribution==='one_per_item'&&(node.subagent_count!=='auto'||contract.batch_size!==undefined)||contract.distribution==='partition'&&!(Number.isInteger(node.subagent_count)&&contract.batch_size===undefined||node.subagent_count==='auto'&&Number.isInteger(contract.batch_size)&&contract.batch_size>=1&&contract.batch_size<=32))issue('SUBAGENT_FANOUT','Fan-out needs a non-Main Agent, one declared list result output, native serial or parallel scheduling, auto one-per-item, fixed partition count, or auto partition with a 1–32 item batch size; incremental item delivery requires per-item admission and a partition batch of at least two items; a capped parallel fan-out needs a native Agent and max_concurrency 1–32; per-item write paths need a bounded-write node and a portable item field name; shared-change handoff requires path-isolated per-item results',{node_id:node.id});
      if(node.access==='bounded_write'&&contract?.scheduling==='parallel'&&contract.max_concurrency!==1&&contract.write_paths_field===undefined)issue('SUBAGENT_WRITE_ISOLATION','Concurrent write fan-out requires Host-owned per-item write paths; use write_paths_field or cap the node at one active writer',{node_id:node.id});
    }
    if(node.required_artifacts!==undefined){
      const entries=node.required_artifacts;
      if(!Array.isArray(entries)||entries.length>64||new Set(entries.map(item=>item?.requirement_id)).size!==entries.length||entries.some(item=>!object(item)||Object.keys(item).some(key=>!['requirement_id','path'].includes(key))||typeof item.requirement_id!=='string'||!/^[A-Za-z][A-Za-z0-9_-]{0,127}$/.test(item.requirement_id)||typeof item.path!=='string'||!item.path||item.path.length>1024||/^(?:[A-Za-z]:[\\/]|[\\/])/.test(item.path)||item.path.split(/[\\/]/).some(part=>part==='..')))issue('REQUIRED_ARTIFACTS','Required artifacts need unique requirement IDs and safe relative exact paths',{node_id:node.id});
      else if(entries.some(item=>isOperationalMemoryArtifactPath(item.path)))issue('OPERATIONAL_MEMORY_ARTIFACT','Project-memory and checkpoint documents cannot be product artifacts or completion gates',{node_id:node.id});
      else if(entries.length&&node.access!=='bounded_write')issue('REQUIRED_ARTIFACT_ACCESS','A node responsible for required artifact paths needs bounded write access',{node_id:node.id});
    }
    if (['agent', 'skill_ref'].includes(node.type) && node.executor?.kind === 'provider' && providers.get(node.executor.provider_id)?.kind === 'native_agent') try {
      managedNativeResultSchema(node);
    } catch (error) { issue(error.code ?? 'AGENT_OUTPUT_SCHEMA', error.message, { node_id: node.id }); }
    if (node.type === 'human_gate' && node.outputs_schema !== undefined) {
      try { validateData(HUMAN_GATE_OUTPUT, node.outputs_schema); }
      catch { issue('HUMAN_GATE_OUTPUT', 'Human gates produce only {approved:true}; they do not collect custom response fields', { node_id: node.id }); }
    }
  }
  const out = new Map([...nodes.keys()].map(id => [id, []]));
  const incoming = new Map([...nodes.keys()].map(id => [id, []]));
  for (const edge of workflow.edges) {
    if (!object(edge)) { issue('EDGE_SCHEMA', 'Edge must be an object'); continue; }
    try { workflowId(edge.id); } catch { issue('EDGE_ID', 'Invalid edge ID', { edge_id: edge.id }); continue; }
    if (edges.has(edge.id)) { issue('EDGE_DUPLICATE', 'Duplicate edge ID', { edge_id: edge.id }); continue; }
    edges.set(edge.id, edge);
    if (!nodes.has(edge.source) || !nodes.has(edge.target)) { issue('EDGE_ENDPOINT', 'Edge endpoint does not exist', { edge_id: edge.id }); continue; }
    if (!['success', 'failure', 'always'].includes(edge.on ?? 'success')) issue('EDGE_POLICY', 'Unknown edge outcome policy', { edge_id: edge.id });
    out.get(edge.source).push(edge); incoming.get(edge.target).push(edge);
  }
  const visit = (start, links = out, stop) => {
    const seen = new Set(); const todo = [start];
    while (todo.length) {
      const id = todo.pop(); if (id === stop || seen.has(id) || !nodes.has(id)) continue;
      seen.add(id);
      for (const edge of links.get(id)) todo.push(links === out ? edge.target : edge.source);
    }
    return seen;
  };
  const starts = [...nodes.values()].filter(node => node.type === 'start');
  const ends = [...nodes.values()].filter(node => node.type === 'end');
  if (starts.length !== 1) issue('START_COUNT', 'Exactly one start node is required');
  if (!ends.length) issue('END_COUNT', 'At least one end node is required');
  const indegree = new Map([...nodes].map(([id]) => [id, incoming.get(id).length]));
  const ready = [...nodes.keys()].filter(id => !indegree.get(id)).sort(); const order = [];
  while (ready.length) {
    const id = ready.shift(); order.push(id);
    for (const edge of out.get(id)) { indegree.set(edge.target, indegree.get(edge.target) - 1); if (!indegree.get(edge.target)) { ready.push(edge.target); ready.sort(); } }
  }
  if (order.length !== nodes.size) issue('GRAPH_CYCLE', 'Workflow graphs must be acyclic');
  if (order.length === nodes.size && edges.size === workflow.edges.length && nodes.size === workflow.nodes.length) {
    try { validateLoopRegions(workflow); } catch (error) { issue(error.code ?? 'LOOP_SCHEMA', error.message); }
  }
  const reachable = starts.length === 1 ? visit(starts[0].id) : new Set();
  const toEnd = new Set(ends.flatMap(node => [...visit(node.id, incoming)]));
  const hostOwnedIdentityField=name=>typeof name==='string'&&/(?:^|_)(?:id|ids|path|paths|sha256|hash|hashes|checksum|checksums|token|tokens|index|indices|revision|receipt|receipts|timestamp|timestamps|uuid|uuids|nonce|nonces|seed|seeds|encoding|encoded)$/.test(name);
  const hostOwnedPacketPointer=(pointer,requiredFields=[],visiting=new Set())=>{
    const parts=pointerParts(pointer);
    if(parts[0]==='inputs')return true;
    if(parts[0]==='loops'&&['review_items','repair_items'].includes(parts[2])){
      const loop=(workflow.loops??[]).find(item=>item.id===parts[1]);
      if(!loop?.item_scope||visiting.has('loop:'+loop.id))return false;
      const next=new Set(visiting);next.add('loop:'+loop.id);
      return bindingPointers(loop.item_scope.items).every(source=>hostOwnedPacketPointer(source,requiredFields,next));
    }
    if(parts[0]!=='nodes'||parts[2]!=='output')return false;
    const producer=nodes.get(parts[1]);
    if(producer?.type!=='tool'||producer.executor?.kind!=='tool'||visiting.has(producer.id))return false;
    const next=new Set(visiting);next.add(producer.id);
    const contract=toolContracts.get(producer.executor.tool),outputName=parts[3];
    const declared=(contract?.host_owned_item_fields??[]).find(item=>item.output===outputName);
    if(requiredFields.length&&declared&&requiredFields.every(field=>declared.fields.includes(field))){
      return declared.from_inputs.every(name=>{
        const binding=producer.input_bindings?.[name],sources=bindingPointers(binding);
        return sources.length>0&&sources.every(source=>hostOwnedPacketPointer(source,[],next));
      });
    }
    return Object.values(producer.input_bindings??{}).every(binding=>bindingPointers(binding).every(source=>hostOwnedPacketPointer(source,[],next)));
  };
  for(const loop of workflow.loops??[]){
    try{
      const check=pointer=>{
        const parts=pointerParts(pointer);
        if(parts[0]==='inputs')return;
        if(parts[0]==='nodes'&&nodes.has(parts[1])&&parts[2]==='output'){
          if(!schemaAtPointer(pointer,workflow,nodes)&&nodes.get(parts[1]).outputs_schema?.additionalProperties===false)throw new Error('Loop binding refers to an undeclared producer output');
          return;
        }
        if(parts[0]==='loops'&&['round','status','feedback','all_accepted','review_items','repair_items'].includes(parts[2])&&(workflow.loops??[]).some(item=>item.id===parts[1]))return;
        throw new Error('Unknown repair-region binding source');
      };
      validateExpression(loop.until,{onPointer:check});
      for(const binding of Object.values(loop.feedback_bindings??{}))for(const pointer of bindingPointers(binding))check(pointer);
      if(loop.item_scope){
        for(const binding of [loop.item_scope.items,loop.item_scope.verdicts])for(const pointer of bindingPointers(binding))check(pointer);
        if(!bindingPointers(loop.item_scope.items).every(pointer=>hostOwnedPacketPointer(pointer,[loop.item_scope.paths_field,...(loop.item_scope.dependencies_field?[loop.item_scope.dependencies_field]:[])])))
          issue('LOOP_ITEM_SOURCE','Repair items and their artifact paths must originate from Run inputs or deterministic Host tools',{loop_id:loop.id});
      }
    }catch(error){issue(error.code??'LOOP_BINDING_INVALID',error.message,{loop_id:loop.id});}
  }
  for (const node of nodes.values()) {
    const location = { node_id: node.id };
    if (node.skill_policy !== undefined) try { effectiveSkillPolicy(workflow.skill_policy, node.skill_policy); } catch (error) { issue(error.code, error.message, location); }
    if (!reachable.has(node.id)) issue('UNREACHABLE', 'Node is unreachable from start', location);
    if (!toEnd.has(node.id)) issue('NO_END_PATH', 'Node has no path to an end', location);
    if (node.type === 'start' && (incoming.get(node.id).length || out.get(node.id).length !== 1)) issue('START_EDGES', 'Start requires exactly one outgoing and no incoming edge', location);
    if (node.type === 'end' && out.get(node.id).length) issue('END_EDGES', 'End cannot have outgoing edges', location);
    if (!['condition', 'parallel', 'end'].includes(node.type)) {
      const successes = out.get(node.id).filter(edge => ['success', 'always'].includes(edge.on ?? 'success'));
      const failures = out.get(node.id).filter(edge => ['failure', 'always'].includes(edge.on ?? 'success'));
      if (successes.length !== 1 || failures.length > 1) issue('NODE_OUTCOMES', 'Use explicit condition/parallel nodes for branching', location);
    }
    if (EXECUTED.has(node.type)) {
      const runBoundAccess = object(node.access) && node.access.binding === 'run.access' && Object.keys(node.access).length === 1 && ['main', 'subworkflow'].includes(node.executor?.kind);
      if (!['read_only', 'bounded_write'].includes(node.access) && !runBoundAccess) issue('NODE_ACCESS', 'Executed nodes need a fixed access mode or main-agent Run access binding', location);
      if (node.access === 'bounded_write' || runBoundAccess) {
        try {
          if (!(object(node.path_scope) && node.path_scope.binding === 'run.allowed_paths' && Object.keys(node.path_scope).length === 1)) {
            if (!pathBoundaries(node.path_scope).length) throw new Error('Empty path scope');
          }
        } catch { issue('PATH_SCOPE', 'Bounded writes require non-glob path boundaries or an explicit Run scope binding', location); }
      }
      if (!object(node.approval) || typeof node.approval.required !== 'boolean') issue('NODE_APPROVAL', 'Node approval policy must be explicit', location);
      if (!object(node.retry) || !Number.isInteger(node.retry.max_attempts) || node.retry.max_attempts < 1 || node.retry.max_attempts > 10) issue('NODE_RETRY', 'Retry limit must be between 1 and 10', location);
      const executor = node.executor;
      if (['agent', 'skill_ref'].includes(node.type) && (typeof node.role !== 'string' || !node.role.trim() || node.role.length > 64)) issue('NODE_ROLE', 'Agent role must be explicit', location);
      if (!object(executor) || !['main', 'provider', 'thread', 'tool', 'human', 'subworkflow'].includes(executor.kind)) issue('EXECUTOR', 'Executed node needs a known executor', location);
      else if (['provider', 'thread'].includes(executor.kind)) {
        const provider = providers.get(executor.provider_id);
        if (!provider) issue('PROVIDER_MISSING', 'Pinned Provider does not exist', location);
        else {
          const bindingIssue = nativeBindingIssue(provider);
          if (bindingIssue && (node.skill_policy?.mode ?? workflow.skill_policy.mode) === 'cooperative') issue(bindingIssue.code, bindingIssue.message, { ...location, provider_id: provider.id, expected: bindingIssue.expected, actual: bindingIssue.actual });
          if (!provider.enabled) issue('PROVIDER_DISABLED', 'Pinned Provider is disabled', location, blockers);
          if (!provider.capabilities?.read || (node.access === 'bounded_write' && !provider.capabilities?.write)) issue('PROVIDER_CAPABILITY', 'Provider capabilities do not match access', location);
          if (provider.kind === 'native_agent' && provider.config?.role && !['advisor', node.role].includes(provider.config.role)) issue('PROVIDER_ROLE', 'Native Provider role does not match node role', location);
        }
      }
      if (executor?.kind === 'main') {
        if (Object.keys(executor).some(key => !['kind','mode'].includes(key)) || executor.mode !== undefined && !['worker','orchestration'].includes(executor.mode)) issue('MAIN_EXECUTION_MODE', 'Main execution mode must be worker or orchestration without Provider or thread fields', location);
        if (executor.mode === 'orchestration' && (node.skill_policy?.mode ?? workflow.skill_policy.mode) !== 'cooperative') issue('MAIN_ORCHESTRATION_POLICY', 'The current conversation requires Cooperative execution; it cannot provide a Strict isolated context', location);
      }
      if (executor?.kind === 'thread') {
        try { assertThreadExecutor(executor); } catch (error) { issue(error.code ?? 'THREAD_EXECUTOR', error.message, location); }
        if (node.type !== 'agent') issue('THREAD_NODE_TYPE', 'Codex task threads execute Agent nodes only', location);
        if ((node.skill_policy?.mode ?? workflow.skill_policy.mode) !== 'cooperative') issue('THREAD_STRICT_UNSUPPORTED', 'Codex task thread execution requires Cooperative mode', location);
        if (providers.get(executor.provider_id)?.kind !== 'native_agent') issue('THREAD_PROVIDER_UNSUPPORTED', 'Codex task threads require a registered native Codex Provider', location);
        if (executor.lifecycle === 'continue') {
          const source = nodes.get(executor.source_node);
          if (!source || source.executor?.kind !== 'thread') issue('THREAD_SOURCE', 'Continuation requires a source node that started a Codex task thread', location);
          else {
            if (source.id === node.id || !visit(source.id).has(node.id)) issue('THREAD_SOURCE_ORDER', 'Continuation source must be strictly upstream of its target node', location);
            if (source.executor.provider_id !== executor.provider_id) issue('THREAD_PROVIDER_CONTINUITY', 'Continuation must retain the exact source task Provider and model configuration', location);
          }
        }
      }
      if (node.type === 'tool' && executor?.kind !== 'tool') issue('TOOL_EXECUTOR', 'Tool nodes require a tool executor', location);
      if (node.type === 'tool' && executor?.kind === 'tool') {
        if (typeof executor.tool !== 'string' || !executor.tool.trim() || executor.tool.length > 256) issue('TOOL_ID', 'Tool nodes must name an exact host tool', location);
        else if (!toolContracts.has(executor.tool)) issue('TOOL_CONTRACT', 'Tool node needs an exact pinned host-tool contract', location);
        else if (!(context.host_tools ?? []).includes(executor.tool)
          && !(context.host_tools ?? []).includes(toolContracts.get(executor.tool).identity.name))
          issue('TOOL_UNAVAILABLE', 'Named host tool is unavailable', location, blockers);
      }
      if (node.type === 'human_gate' && executor?.kind !== 'human') issue('HUMAN_EXECUTOR', 'Human gates require a human executor', location);
      if ((node.type === 'subworkflow') !== (executor?.kind === 'subworkflow')) issue('SUBWORKFLOW_EXECUTOR', 'SubWorkflow nodes require their dedicated executor', location);
      if (node.type === 'agent' && !['main', 'provider', 'thread'].includes(executor?.kind)) issue('AGENT_EXECUTOR', 'Agent nodes require main, Provider or Codex task-thread execution', location);
      if (node.type === 'skill_ref' && !['main', 'provider'].includes(executor?.kind)) issue('AGENT_EXECUTOR', 'SkillRef nodes require main or Provider execution', location);
      if (node.type === 'agent' && (typeof node.prompt_template !== 'string' || !node.prompt_template.trim())) issue('NODE_PROMPT', 'Agent requires instructions', location);
    }
    function checkSchemaPath(schema, parts) {
      let current = schema;
      for (const part of parts) {
        if (!object(current) || Object.keys(current).length === 0) return;
        if (current.type === 'array') {
          if (!/^\d+$/.test(part) || !current.items) throw new Error('Binding path is not declared by the producer output schema');
          current = current.items; continue;
        }
        if (object(current.properties) && Object.hasOwn(current.properties, part)) { current = current.properties[part]; continue; }
        if (object(current.additionalProperties)) { current = current.additionalProperties; continue; }
        if (current.additionalProperties === false) throw new Error('Binding path is not declared by the producer output schema');
        return;
      }
    }
    function checkPointer(pointer) {
      try {
        const parts = pointerParts(pointer);
        if (parts[0] === 'inputs') { checkSchemaPath(workflow.inputs_schema ?? {}, parts.slice(1)); return; }
        if (parts[0] === 'loops') {
          const loop=(workflow.loops??[]).find(item=>item.id===parts[1]);
          if(!loop||!['round','status','feedback','all_accepted','review_items','repair_items'].includes(parts[2]))throw new Error('Unknown repair-region binding');
          if(!loop.node_ids.includes(node.id)&&!visit(loop.exit_node).has(node.id))throw new Error('Repair-region context is available only within its body or after its exit');
          const schema=schemaAtPointer(pointer,workflow,nodes);
          if(!schema&&parts[2]!=='feedback')throw new Error('Repair-region binding has no declared item scope or field');
          return;
        }
        if (parts[0] !== 'nodes' || !nodes.has(parts[1]) || parts[2] !== 'output') throw new Error('Unknown binding source');
        if (parts[1] === node.id || !visit(parts[1]).has(node.id)) throw new Error('Binding must refer to an upstream producer');
        if (nodes.get(parts[1]).type === 'human_gate' && parts.length > 3 && !(parts.length === 4 && Object.hasOwn(HUMAN_GATE_OUTPUT, parts[3]))) throw new Error('Human gate output has only the approved field');
        checkSchemaPath(nodes.get(parts[1]).outputs_schema ?? {}, parts.slice(3));
      } catch (error) { issue('BINDING_SOURCE', error.message, location); }
    }
    if (node.input_bindings !== undefined && !object(node.input_bindings)) issue('BINDING_SCHEMA', 'Input bindings must be a map of JSON Pointers or bounded selectors', location);
    else for (const binding of Object.values(node.input_bindings ?? {})) {
      try {
        for (const pointer of bindingPointers(binding)) checkPointer(pointer);
        if(object(binding)&&(binding.flat_map||binding.pluck)){
          const source=schemaAtPointer(binding.path,workflow,nodes);
          const field=binding.flat_map??binding.pluck;
          if(source?.type!=='array'||!object(source.items?.properties?.[field])||binding.flat_map&&source.items.properties[field].type!=='array')
            issue('BINDING_PROJECTION_SCHEMA','Projected binding needs an array of records with the declared field'+(binding.flat_map?' containing arrays':''),location);
        }
        if(object(binding)&&binding.every_true){
          const source=schemaAtPointer(binding.path,workflow,nodes);
          if(source?.type!=='array'||source.items?.properties?.[binding.every_true]?.type!=='boolean')
            issue('BINDING_PROJECTION_SCHEMA','every_true needs an array of records with the declared boolean field',location);
        }
        if(object(binding)&&binding.zip){
          const source=schemaAtPointer(binding.path,workflow,nodes),paired=schemaAtPointer(binding.zip,workflow,nodes);
          if(source?.type!=='array'||paired?.type!=='array'||binding.count_field&&source.items?.properties?.[binding.count_field]?.type!=='array'||binding.count_field&&paired.items?.type!=='array')
            issue('BINDING_PROJECTION_SCHEMA','zip needs two arrays and matching declared partition schemas',location);
        }
      }
      catch (error) { issue(error.code ?? 'BINDING_SCHEMA', error.message, location); }
    }
    if(node.fanout!==undefined){
      let policy=null;try{policy=effectiveSkillPolicy(workflow.skill_policy,node.skill_policy);}catch{}
      if(policy?.mode==='strict')issue('STRICT_FANOUT_UNSUPPORTED','Strict execution cannot run native sub-Agent fan-out; select a Cooperative native Provider',location);
      const binding=node.input_bindings?.[node.fanout.input];
      if(binding!==undefined){
        if(node.fanout.write_paths_field){
          const pointers=bindingPointers(binding),source=pointers.length===1?schemaAtPointer(pointers[0],workflow,nodes):null;
          const paths=source?.items?.properties?.[node.fanout.write_paths_field];
          if(source&&source.type==='array'&&(paths?.type!=='array'||paths.items?.type!=='string'||!(source.items.required??[]).includes(node.fanout.write_paths_field)))
            issue('SUBAGENT_ITEM_WRITE_PATHS_SCHEMA','write_paths_field must name a required string-list field on every declared fan-out item',location);
          const identityFields=[...new Set([node.fanout.write_paths_field,...((source?.items?.required??[]).filter(hostOwnedIdentityField))])];
          if(!pointers.length||!pointers.every(pointer=>hostOwnedPacketPointer(pointer,identityFields)))
            issue('SUBAGENT_ITEM_SOURCE','Per-item write packets must come from Workflow inputs or Host tools that do not depend on Agent output',location);
        }
        let range;try{range=fanoutInputRange(binding,workflow,nodes);}catch{range={unknown:true};}
        if(range.invalid)issue('SUBAGENT_FANOUT_INPUT_SCHEMA','Fan-out input binding can resolve to a declared non-array value',location);
        else{
          const result=node.outputs_schema?.properties?.[node.fanout.result_output],resultMin=result?.minItems??0,resultMax=result?.maxItems??Infinity;
          const runnableMin=range.known?Math.max(range.min,1):1,runnableMax=range.known?range.max:Infinity;
          if(range.known&&runnableMin>runnableMax)issue('SUBAGENT_FANOUT_CARDINALITY','The declared fan-out input cannot produce a nonempty runtime list',location);
          if(Number.isInteger(node.subagent_count)){
            const count=node.subagent_count;
            if(range.known&&(count<runnableMin||count>runnableMax))issue('SUBAGENT_FANOUT_CARDINALITY',`Fixed fan-out count ${count} cannot match any declared runtime input cardinality`,location);
            if(count<resultMin||count>resultMax)issue('SUBAGENT_FANOUT_CARDINALITY',`Fixed fan-out count ${count} cannot satisfy the declared result-list bounds`,location);
          }else if(node.subagent_count==='auto'&&range.known){
            const batchSize=node.fanout.batch_size??1;
            if(node.fanout.scheduling==='parallel'&&!node.fanout.max_concurrency&&Math.ceil(runnableMin/batchSize)>32)issue('SUBAGENT_FANOUT_CARDINALITY','The declared input requires more than 32 concurrent sub-Agents; cap concurrency or use larger partitions',location);
            if(Math.max(Math.ceil(runnableMin/batchSize),resultMin)>Math.min(Math.ceil(runnableMax/batchSize),resultMax))issue('SUBAGENT_FANOUT_CARDINALITY','Automatic fan-out input and result schemas have no common runtime Agent count',location);
          }
        }
        if(node.fanout.shared_change_field){
          const result=node.outputs_schema?.properties?.[node.fanout.result_output],field=node.fanout.shared_change_field,item=result?.items;
          if(item?.type!=='object'||!object(item.properties?.[field])||!(item.required??[]).includes(field))
            issue('SUBAGENT_SHARED_CHANGE_SCHEMA','shared_change_field must name a required field on every per-item result',location);
          const base=`/nodes/${node.id}/output/${node.fanout.result_output}`;
          const consumesShared=binding=>typeof binding==='string'?binding===base:object(binding)&&binding.path===base&&(!binding.pluck||binding.pluck===field);
          const consumers=[...nodes.values()].filter(candidate=>candidate.id!==node.id&&candidate.access==='bounded_write'&&Object.values(candidate.input_bindings??{}).some(consumesShared));
          const descendants=visit(node.id);
          if(consumers.length!==1||!descendants.has(consumers[0]?.id))
            issue('SUBAGENT_SHARED_CHANGE_HANDOFF','Path-isolated workers that declare shared changes need exactly one downstream bounded-write owner of the joined results or shared field',location);
          else{
            const consumer=consumers[0],guards=consumer.completion_contract?.fail_on_false??[];
            const guarded=guards.some(name=>consumer.outputs_schema?.properties?.[name]?.type==='boolean'&&(consumer.outputs_schema?.required??[]).includes(name));
            if(!guarded)issue('SUBAGENT_SHARED_CHANGE_COMPLETION','The downstream shared-write owner must expose a required boolean success result guarded by completion_contract.fail_on_false',location);
          }
        }
      }
    }
    if (node.context_projection !== undefined) {
      issue('LEGACY_CONTEXT_PROJECTION', 'Node-level broad context projection is retired; declare exact input_bindings and resources', location);
    }
    if (node.cost !== undefined) {
      try { validateNodeCost(node.cost); } catch (error) { issue(error.code, error.message, location); }
    }
    if (node.decision !== undefined) {
      const decision = node.decision;
      if (!['agent', 'skill_ref'].includes(node.type) || !object(decision) || Object.keys(decision).some(key => !['id', 'options', 'required_references', 'budget'].includes(key)) || typeof decision.id !== 'string' || !/^[a-z][a-z0-9_-]{0,127}$/.test(decision.id) || !Array.isArray(decision.options) || decision.options.length < 1 || decision.options.length > 64 || decision.options.some(option => typeof option !== 'string' || !option || option.length > 128) || new Set(decision.options).size !== decision.options.length || !Array.isArray(decision.required_references) || decision.required_references.some(path => typeof path !== 'string' || !(node.resources ?? []).includes(path)) || new Set(decision.required_references).size !== decision.required_references.length) issue('DECISION_CONTRACT', 'Decision needs finite ID/options and references declared by this node', location);
      else if (decision.budget !== undefined) try { validateNodeCost(decision.budget); } catch (error) { issue('DECISION_CONTRACT', error.message, location); }
    }
    if (node.type === 'condition') {
      const labels = new Set();
      if (!Array.isArray(node.cases) || !node.cases.length) issue('CONDITION_CASES', 'Condition needs ordered cases', location);
      for (const entry of Array.isArray(node.cases) ? node.cases : []) {
        if (!object(entry) || typeof entry.label !== 'string' || !entry.label || labels.has(entry.label)) { issue('CONDITION_LABEL', 'Case labels must be unique and nonempty', location); continue; }
        labels.add(entry.label);
        try { validateExpression(entry.when, { onPointer: checkPointer }); } catch (error) { issue('CONDITION_DSL', error.message, location); }
      }
      if (typeof node.default_label !== 'string' || !node.default_label || labels.has(node.default_label)) issue('CONDITION_DEFAULT', 'Condition needs a distinct default label', location);
      labels.add(node.default_label);
      const outgoing = out.get(node.id);
      if (outgoing.length !== labels.size || new Set(outgoing.map(edge => edge.label)).size !== labels.size || outgoing.some(edge => !labels.has(edge.label) || (edge.on ?? 'success') !== 'success')) issue('CONDITION_EDGES', 'Each condition label needs exactly one success edge', location);
    }
    if (node.type === 'skill_ref') {
      if (workflow.skill_policy?.mode !== 'strict') issue('SKILL_REF_STRICT_REQUIRED', 'Linked SkillRef execution requires Strict isolation', location);
      const reference = node.skill_ref;
      let validReference = true;
      try { validateSkillReference(reference); } catch (error) { validReference = false; issue(error.code, error.message, location); }
      if (validReference) for (const pin of [reference, ...reference.allowed_nested_skills]) {
        if ([...workflow.skill_policy.shadowed_skill_paths, ...(node.skill_policy?.shadowed_skill_paths ?? [])].some(path => skillPathKey(path) === skillPathKey(pin.path))) issue('SKILL_POLICY_CONFLICT', 'SkillRef conflicts with a shadowed source', location);
        const skill = (context.skills ?? []).find(item => skillPathKey(item.path) === skillPathKey(pin.path));
        if (!skill) issue('SKILL_MISSING', 'Referenced Skill does not exist', location);
        else if (skill.source_hash !== pin.source_hash || (skill.name !== undefined && skill.name !== pin.name) || (pin.expected_version !== undefined && skill.version !== pin.expected_version)) issue('SKILL_STALE', 'Skill name/content/version differs from the pin', location);
      }
    }
    if (node.type === 'subworkflow') {
      const reference = node.subworkflow;
      if (!object(reference) || !reference.workflow_id || !SHA.test(reference.revision_pin)) issue('SUBWORKFLOW_REFERENCE', 'SubWorkflow requires an immutable revision pin', location);
      else {
        const key = reference.workflow_id + '@' + reference.revision_pin;
        if (reference.workflow_id === workflow.id || stack.some(item => item.split('@')[0] === reference.workflow_id)) issue('SUBWORKFLOW_CYCLE', 'Recursive SubWorkflows are not supported', location);
        else {
          const child = context.workflows?.[key];
          if (!child) issue('SUBWORKFLOW_MISSING', 'Pinned SubWorkflow revision does not exist', location);
          else {
            try { effectiveSkillPolicy(effectiveSkillPolicy(workflow.skill_policy, node.skill_policy), child.skill_policy); } catch (error) { issue(error.code, error.message, location); }
            if (!object(node.input_bindings)) issue('SUBWORKFLOW_INPUT_BINDINGS', 'Child inputs require an explicit binding map', location);
            else for (const name of child.inputs_schema?.required ?? []) if (!Object.hasOwn(node.input_bindings, name)) issue('SUBWORKFLOW_INPUT_BINDINGS', 'A required child input is not bound', { ...location, binding: name });
            if (!object(reference.output_bindings)) issue('SUBWORKFLOW_OUTPUT_BINDINGS', 'Child outputs require an explicit namespace binding map', location);
            else for (const pointer of Object.values(reference.output_bindings)) {
              try { if (pointerParts(pointer)[0] !== 'output') throw new Error('Child output bindings must start at /output'); } catch (error) { issue('SUBWORKFLOW_OUTPUT_BINDINGS', error.message, location); }
            }
            const checked = validateWorkflowGraph(child, context, [...stack, workflow.id + '@current']);
            if (!checked.valid) issue('SUBWORKFLOW_INVALID', 'Pinned SubWorkflow is invalid', { ...location, child_errors: checked.errors });
            for (const blocker of checked.blockers) issue('SUBWORKFLOW_BLOCKED', blocker.message, { ...location, child: key }, blockers);
          }
        }
      }
    }
  }
  for (const parallel of [...nodes.values()].filter(node => node.type === 'parallel')) {
    const location = { node_id: parallel.id };
    if (parallel.failure_policy !== undefined && !['fail_fast', 'collect'].includes(parallel.failure_policy)) issue('PARALLEL_FAILURE_POLICY', 'Parallel failure policy must be fail_fast or collect', location);
    const join = nodes.get(parallel.join_id);
    if (join?.type !== 'join' || join.parallel_id !== parallel.id) { issue('PARALLEL_JOIN', 'Parallel requires a matching Join', location); continue; }
    const branches = out.get(parallel.id);
    if (branches.length < 2 || branches.some(edge => !edge.label || edge.target === join.id || (edge.on ?? 'success') !== 'success') || new Set(branches.map(edge => edge.label)).size !== branches.length) issue('PARALLEL_BRANCHES', 'Parallel needs at least two distinct labeled branches', location);
    const sets = branches.map(edge => visit(edge.target, out, join.id));
    const lineages = sets.map(set => new Set([...set].map(id => threadLineage(nodes, id)).filter(Boolean)));
    for (let index = 0; index < lineages.length; index++) for (const lineage of lineages[index]) {
      if (lineages.slice(index + 1).some(set => set.has(lineage))) issue('THREAD_CONCURRENT_CONTINUATION', 'Parallel branches cannot send prompts to the same task lineage; serialize its continuations', { ...location, source_node: lineage });
    }
    const all = new Set(sets.flatMap(set => [...set]));
    for (let index = 0; index < sets.length; index++) for (const id of sets[index]) {
      if (!visit(id).has(join.id) || visit(id, out, join.id).size && [...visit(id, out, join.id)].some(next => nodes.get(next).type === 'end')) issue('JOIN_BYPASS', 'Every parallel branch path must pass through its Join', { node_id: id });
      if (sets.some((set, other) => other !== index && set.has(id))) issue('BRANCH_OVERLAP', 'Branches cannot merge before their Join', { node_id: id });
      if (incoming.get(id).some(edge => !sets[index].has(edge.source) && !(edge.source === parallel.id && edge.target === branches[index].target))) issue('FOREIGN_BRANCH_ENTRY', 'An unrelated path enters this branch', { node_id: id });
    }
    if (incoming.get(join.id).some(edge => !all.has(edge.source)) || incoming.get(join.id).length < 2) issue('JOIN_FOREIGN_BRANCH', 'Join has missing or unrelated incoming branches', { node_id: join.id });
  }
  for (const join of [...nodes.values()].filter(node => node.type === 'join')) if (nodes.get(join.parallel_id)?.join_id !== join.id) issue('JOIN_PARALLEL', 'Join must belong to exactly one Parallel', { node_id: join.id });
  const finalizer = nodes.get(workflow.finalization?.node_id);
  for (const kind of ['nodes', 'edges']) for (const item of workflow[kind]) if (item?.origin?.kind === 'inferred' && item.origin.reviewed !== true)
    issue('AI_INFERENCE_UNREVIEWED', 'Inferred control flow requires explicit per-item review', { item_kind: kind, item_id: item.id }, blockers);
  for (const node of workflow.nodes) if (node?.origin?.kind === 'inlined_skill' && node.origin.reviewed !== true)
    issue('INLINE_SKILL_UNREVIEWED', 'Inline conversion requires review against its copied source', { node_id: node.id }, blockers);
  if (workflow.finalization?.required !== true || !finalizer || !['agent','tool'].includes(finalizer.type)) issue('FINALIZER_MISSING', 'A final acceptance Agent or deterministic Host tool is required');
  else {
    if (finalizer.type==='agent'&&finalizer.executor?.kind !== 'main') issue('FINALIZER_AUTHORITY', 'Agent final acceptance belongs to the main agent', { node_id: finalizer.id });
    if (finalizer.type==='tool'&&!(finalizer.executor?.kind==='tool'&&Array.isArray(finalizer.completion_contract?.fail_on_false)&&finalizer.completion_contract.fail_on_false.length))
      issue('FINALIZER_DETERMINISTIC','A Host-tool finalizer must have a nonempty required-boolean fail_on_false contract',{node_id:finalizer.id});
    if (starts.length === 1 && ends.some(node => visit(starts[0].id, out, finalizer.id).has(node.id))) issue('FINALIZER_BYPASS', 'Every path to an end must pass final acceptance', { node_id: finalizer.id });
    if (out.get(finalizer.id).some(edge => nodes.get(edge.target)?.type !== 'end')) issue('FINALIZER_ORDER', 'Only termination may follow final acceptance', { node_id: finalizer.id });
  }
  if (workflow.output_bindings !== undefined && !object(workflow.output_bindings)) issue('OUTPUT_BINDINGS', 'Workflow output bindings must be a JSON Pointer map');
  else for (const [binding, pointer] of Object.entries(workflow.output_bindings ?? {})) {
    try {
      const parts = pointerParts(pointer);
      if (parts[0] !== 'inputs' && !(parts[0] === 'nodes' && nodes.has(parts[1]) && parts[2] === 'output') && !(parts[0]==='loops' && schemaAtPointer(pointer,workflow,nodes))) throw new Error('Unknown workflow output source');
      if (parts[0] === 'nodes' && nodes.get(parts[1]).type === 'human_gate' && parts.length > 3 && !(parts.length === 4 && Object.hasOwn(HUMAN_GATE_OUTPUT, parts[3]))) throw new Error('Human gate output has only the approved field');
    } catch (error) { issue('OUTPUT_BINDINGS', error.message, { binding }); }
  }
  if (!object(workflow.skill_policy) || !['strict', 'cooperative'].includes(workflow.skill_policy.mode) || (workflow.skill_policy.mode === 'strict' && workflow.skill_policy.implicit !== 'deny')) issue('SKILL_POLICY', 'Workflow must declare a valid Skill policy');
  if (!object(workflow.requirements)) issue('REQUIREMENTS_SCHEMA', 'Requirements must be an object');
  else for (const kind of ['providers', 'tools', 'mcp_servers', 'executables', ...(workflow.requirements.environment !== undefined ? ['environment'] : [])]) {
    const required = workflow.requirements[kind];
    if (kind === 'executables') {
      if (!Array.isArray(required)) { issue('REQUIREMENTS_SCHEMA', 'Requirements executables must be an array'); continue; }
      try { normalizeExecutableRequirements(required); }
      catch (error) { issue(error.code ?? 'REQUIREMENTS_SCHEMA', error.message); }
      continue;
    }
    if (!Array.isArray(required) || required.some(id => typeof id !== 'string' || !id)) { issue('REQUIREMENTS_SCHEMA', `Requirements ${kind} must be a string array`); continue; }
    for (const id of required) {
      if (kind === 'providers') {
        if (!providers.has(id)) issue('PROVIDER_MISSING', `Required Provider does not exist: ${id}`);
        else if (!providers.get(id).enabled) issue('PROVIDER_DISABLED', `Required Provider is disabled: ${id}`, {}, blockers);
      } else if (context.check_runtime_requirements === true && ['tools', 'mcp_servers'].includes(kind) && !(context[kind] ?? []).includes(id)) issue('REQUIREMENT_UNAVAILABLE', `Required ${kind} entry is unavailable: ${id}`, { requirement: id }, blockers);
    }
  }
  if (workflow.import_status !== undefined) {
    const imported = workflow.import_status;
    if (!object(imported) || !['coarse', 'authored', 'ai_expanded'].includes(imported.mode) || !Array.isArray(imported.unresolved)) issue('IMPORT_STATUS', 'Source-backed Workflow needs explicit dependency observations');
    else {
      if (imported.unresolved.some(i=>!informationalImportObservation(i))) issue('IMPORT_UNRESOLVED', 'Imported Workflow has unresolved resource, dependency or credential observations', { unresolved: imported.unresolved.filter(i=>!informationalImportObservation(i)) }, blockers);
      if (imported.mode === 'ai_expanded') {
        if (!['fully_compiled','agent_assisted','unsupported'].includes(imported.conversion_level) || imported.conversion_contract_version !== 3 || !Array.isArray(imported.requirement_coverage)) issue('CONVERSION_STATUS', 'Expanded imports need the current versioned conversion level and requirement coverage');
        else if (imported.conversion_level === 'unsupported') issue('CONVERSION_UNSUPPORTED', 'Required source behavior has no faithful runtime representation', { requirement_coverage: imported.requirement_coverage.filter(item => item.status === 'unsupported') }, blockers);
      }
      for (const [field, entries] of [['requirement_coverage', imported.requirement_coverage], ['source_dispositions', imported.source_dispositions]]) {
        if (entries === undefined) continue;
        if (!Array.isArray(entries)) { issue('IMPORT_NODE_REFERENCE', `${field} must be an array when present`, { field }); continue; }
        for (const [index, entry] of entries.entries()) {
          const missing = Array.isArray(entry?.node_ids) ? entry.node_ids.filter(id => !nodes.has(id)) : [];
          if (missing.length) issue('IMPORT_NODE_REFERENCE', `${field} references nodes absent from the Workflow graph`, { field, index, missing_node_ids: missing });
        }
      }
    }
  }
  if (!workflow.enabled) issue('WORKFLOW_DISABLED', 'Workflow is disabled', {}, blockers);
  if (workflow.status !== 'ready') issue('WORKFLOW_DRAFT', 'Draft Workflow cannot start', {}, blockers);
  return { valid: errors.length === 0, launch_ready: errors.length === 0 && blockers.length === 0, errors, blockers, order };
}
