import { resolvedSubagentPlan } from '../workflow-runtime.mjs';
import { canonicalJSON, digest } from '../workflow-revisions.mjs';
import { requireValue } from '../workflow-paths.mjs';
import { hostCompletionEnvelope } from './host-main-automation.mjs';
import { compilePrompt } from '../workflow-executor.mjs';
import { projectFanoutInputs, assignedFanoutIndices, assignedFanoutWritePaths, activeFanoutAssignmentIndices } from './fanout-input-projection.mjs';
import { materializeNativeTaskBundle } from './node-input-materials.mjs';
import { join } from 'node:path';
import { readFile } from 'node:fs/promises';

const agentId = value => typeof value === 'string' && value.length > 0 && value.length <= 256;
const nativeResourceReader = 'mcp__codex_agents_workflow__workflow_read_resource';
const resourceInstruction = 'Resources listed below are logical identifiers, not filesystem paths. Use read_workflow_resource; cite resource IDs.';

function nativeTaskName(record, definition, attemptId, index) {
  const suffix=digest(canonicalJSON({run_id:record.state.run_id,node_id:definition.id,attempt_id:attemptId,index})).slice(0,24);
  return `wf_${suffix}_${index}`;
}

export function nativeAgentResultSchema(definition, itemCount = null) {
  const semanticSchema = definition.fanout
    ? definition.outputs_schema?.properties?.[definition.fanout.result_output]?.items
    : definition.outputs_schema;
  return definition.fanout?.result_mode==='per_item'
    ? {type:'object',properties:{items:{type:'array',
      ...(Number.isSafeInteger(itemCount)?{minItems:itemCount,maxItems:itemCount}:{}),items:{type:'object',properties:{
      outcome:{type:'string',enum:definition.fanout.shared_change_field?['completed','delegated','blocked']:['completed','blocked']},
      result:semanticSchema,block_reason:{type:'string'},
    },required:['outcome'],additionalProperties:false}}},required:['items'],additionalProperties:false}
    : semanticSchema;
}

function nativeResourcePrompt(prompt, envelope) {
  if (!envelope.resource_access?.paths?.length) return prompt;
  const instruction = `For each required logical resource_path in Resources, call tools.${nativeResourceReader}(`
    + `{workflow_id:${canonicalJSON(envelope.workflow_id)},revision_hash:${canonicalJSON(envelope.workflow_revision)},resource_path}). `
    + `If schema discovery is needed, use ALL_TOOLS.find(tool => tool.name === "${nativeResourceReader}").`;
  // Replace only Host guidance; authored task text and Main's dynamic tool
  // contract retain their exact content.
  return prompt.replace(resourceInstruction, () => instruction);
}

export function nativeAgentHandoff(record, definition, lease, dispatched, maxPromptChars = 64000, selectedIndices = null) {
  requireValue(dispatched.handoff_required && dispatched.adapter?.execution === 'native_agent',
    'NATIVE_AGENT_HANDOFF', 'Only a real native Agent adapter can cross this bridge');
  const plan = resolvedSubagentPlan(definition, record.state);
  const assignments = plan?.assignments ?? [null];
  const resultSchema=nativeAgentResultSchema(definition);
  const scope = allowedPaths => `Workspace: ${dispatched.envelope.workspace}\nAccess: ${dispatched.envelope.access}\nWritable paths: ${canonicalJSON(allowedPaths)}`;
  const indices = selectedIndices === null ? assignments.map((_,index)=>index)
    : Array.isArray(selectedIndices) ? selectedIndices : [selectedIndices];
  const selected = indices.map(index=>({items:assignments[index],index}));
  const packets = selected.map(({items,index}) => {
    const material=dispatched.materialized_packets?.[index];
    const activeItems=material?.assigned_items??items;
    if(material?.item_positions==null && definition.fanout?.result_mode==='per_item')
      assignedFanoutIndices(plan,definition.fanout,index);
    const allowedPaths=material?.allowed_paths??(activeItems===null?dispatched.envelope.effective_allowed_paths:assignedFanoutWritePaths({
      workspace:dispatched.envelope.workspace,nodeAllowedPaths:dispatched.envelope.effective_allowed_paths,
      assignedItems:activeItems,fanout:definition.fanout}));
    const compiled = activeItems === null ? dispatched.compiled_prompt : compilePrompt({
      ...dispatched.envelope, inputs: projectFanoutInputs(dispatched.envelope.inputs, plan.items, activeItems),
    }, maxPromptChars);
    const perItem=definition.fanout?.result_mode==='per_item'
      ? '\nReturn items (or result.items inside a completion envelope) with one ordered entry per supplied item: '
        +'{"outcome":"completed","result":<one semantic item>} or '
        +(definition.fanout.shared_change_field
          ? `{"outcome":"delegated","result":<one semantic item>} when local work is complete and ${definition.fanout.shared_change_field} names work for the downstream shared-write owner, or `
          : '')
        +'{"outcome":"blocked","block_reason":"specific obstacle"}. '
        +'The Host binds entries to supplied items by order; do not add positions, IDs, paths, hashes, tokens, receipts, or other Host-owned fields. '
        +'A completed entry must satisfy the semantic item schema.' : '';
    const prompt = material
      ? scope(allowedPaths) + `\nTask bundle: ${canonicalJSON(material.task_bundle_path)}\nRead this Host-generated JSON file once, execute its task, and return its declared result_schema.`
      : scope(allowedPaths) + '\n\n' + nativeResourcePrompt(compiled, dispatched.envelope)
        + (activeItems === null ? '' : `\n\nHost dispatch index: ${index}. Process the assigned ${definition.fanout.item_name} partition.`)
        + perItem
        + (resultSchema === undefined ? '' : '\nResult schema:\n' + canonicalJSON(resultSchema));
    requireValue(prompt.length <= maxPromptChars, 'PROMPT_LIMIT', 'Native Agent packet exceeds the configured prompt limit');
    return { index, allowed_paths:allowedPaths, ...(material?{task_bundle_path:material.task_bundle_path,
      task_bundle_sha256:material.task_bundle_sha256}:{}),
      spawn_config: { ...structuredClone(dispatched.adapter.spawn_config), fork_turns: 'none',
        task_name:nativeTaskName(record,definition,lease.attempt_id,index) }, prompt };
  });
  return {
    run_id: record.state.run_id, node_id: definition.id, attempt_id: lease.attempt_id,
    workspace: dispatched.envelope.workspace, access: dispatched.envelope.access,
    allowed_paths: dispatched.envelope.effective_allowed_paths,
    packets,
    result_schema: resultSchema,
  };
}

async function nativeTaskResources(record, envelope, resourceRoot) {
  const paths=envelope.resource_access?.paths??[];
  if(!paths.length)return [];
  requireValue(typeof resourceRoot==='string'&&resourceRoot.length,'NATIVE_TASK_RESOURCE_ROOT','Native task resources need the exact Run object root');
  const resources=[];
  for(const path of paths){
    const pin=record.pins?.root?.resources?.find(item=>item.path===path);
    requireValue(pin&&Number.isSafeInteger(pin.bytes)&&pin.bytes>=0,'NATIVE_TASK_RESOURCE',`Pinned resource is unavailable: ${path}`);
    const bytes=await readFile(join(resourceRoot,pin.sha256));
    requireValue(bytes.length===pin.bytes&&digest(bytes)===pin.sha256,'NATIVE_TASK_RESOURCE_CHANGED',`Pinned resource is missing or modified: ${path}`);
    resources.push({path,sha256:pin.sha256,size:pin.bytes,bytes});
  }
  return resources;
}

export async function materializedNativeAgentHandoff(record, definition, lease, dispatched, maxPromptChars = 64000, selectedIndices = null,
  {resourceRoot,itemPositionOverrides={},bundleSegment=null} = {}) {
  requireValue(/^[A-Za-z0-9-]{1,128}$/.test(record.state.run_id)&&/^[A-Za-z0-9-]{1,128}$/.test(lease.attempt_id),
    'NATIVE_AGENT_INPUT_PATH','Native input material identity is not a safe Run/attempt path');
  const plan=resolvedSubagentPlan(definition,record.state),assignments=plan?.assignments??[null];
  const attempt=record.state.nodes?.[definition.id]?.attempts?.find(item=>item.id===lease.attempt_id);
  const inherited=new Set(attempt?.inherited_native_item_indices??[]);
  const indices=selectedIndices===null?assignments.map((_,index)=>index)
    :Array.isArray(selectedIndices)?selectedIndices:[selectedIndices];
  const root=join(dispatched.envelope.workspace,'work','.workflow-runtime','native-agent',record.state.run_id,lease.attempt_id);
  const resources=await nativeTaskResources(record,dispatched.envelope,resourceRoot);
  const materialized=await Promise.all(indices.map(async index=>{
    let items=assignments[index],itemPositions=definition.fanout?.result_mode==='per_item'
      ?assignedFanoutIndices(plan,definition.fanout,index):null;
    if(itemPositions)itemPositions=itemPositions.filter(itemIndex=>!inherited.has(itemIndex));
    if(itemPositions)items=itemPositions.map(itemIndex=>plan.items[itemIndex]);
    const override=itemPositionOverrides[index];
    if(override!==undefined){
      requireValue(definition.fanout?.result_mode==='per_item'&&Array.isArray(override)&&override.every(itemIndex=>itemPositions.includes(itemIndex)),
        'NATIVE_ITEM_INDEX','Repair item positions must be a subset of the Host-assigned partition');
      itemPositions=[...override];items=itemPositions.map(itemIndex=>plan.items[itemIndex]);
    }
    if(definition.fanout?.item_delivery==='incremental'){
      const next=itemPositions.find(itemIndex=>!attempt?.native_item_results?.[itemIndex]);
      requireValue(Number.isSafeInteger(next),'NATIVE_ITEM_RESULT','Incremental native delivery has no unresolved item to materialize');
      itemPositions=[next];items=[plan.items[next]];
    }
    const inputs=items===null?dispatched.envelope.inputs:projectFanoutInputs(dispatched.envelope.inputs,plan.items,items);
    const packetResultSchema=nativeAgentResultSchema(definition,
      definition.fanout?.result_mode==='per_item'?itemPositions.length:null);
    const allowedPaths=items===null?dispatched.envelope.effective_allowed_paths:assignedFanoutWritePaths({
      workspace:dispatched.envelope.workspace,nodeAllowedPaths:dispatched.envelope.effective_allowed_paths,
      assignedItems:items,fanout:definition.fanout});
    const directory=bundleSegment!==null?join(root,`partition-${index}`,bundleSegment)
      :definition.fanout?.item_delivery==='incremental'
        ?join(root,`partition-${index}`,`item-${itemPositions[0]}`):join(root,`partition-${index}`);
    const material=await materializeNativeTaskBundle({directory,
      envelope:{...dispatched.envelope,inputs},resources,resultSchema:packetResultSchema,allowedPaths,
      itemPositions,maxPromptChars});
    return [index,{...material,assigned_items:items}];
  }));
  return nativeAgentHandoff(record,definition,lease,
    {...dispatched,materialized_packets:Object.fromEntries(materialized)},maxPromptChars,selectedIndices);
}

export function nativeAgentReceipt(definition, state, attemptId, ids) {
  const plan = resolvedSubagentPlan(definition, state);
  const perItem=definition.fanout?.result_mode==='per_item';
  const attempt=state.nodes?.[definition.id]?.attempts?.find(item=>item.id===attemptId);
  const inherited=new Set(attempt?.inherited_native_item_indices??[]);
  const activeIndices=plan?activeFanoutAssignmentIndices(plan,definition.fanout,inherited):[];
  const assignments=plan?.assignments&&(perItem?activeIndices.map(assignmentIndex=>{
    const indices=assignedFanoutIndices(plan,definition.fanout,assignmentIndex).filter(itemIndex=>!inherited.has(itemIndex));
    return {assignmentIndex,items:indices.map(itemIndex=>plan.items[itemIndex])};
  }):plan.assignments.map((items,assignmentIndex)=>({assignmentIndex,items})));
  requireValue(Array.isArray(ids) && ids.length === (assignments?.length ?? 1) && ids.every(agentId)
    && new Set(ids).size === ids.length, 'NATIVE_AGENT_IDENTITY', 'Provide one distinct real native Agent ID per dispatched packet');
  const receipt = { invocation_id: `native-${attemptId}`, executor: 'codex-native-subagent', agent_ids: [...ids] };
  if (assignments) {
    receipt.subagent_dispatch_ids = [...ids];
    receipt.subagent_plan = { resolved_count: assignments.length, input_sha256: digest(canonicalJSON(plan.items)),
      assignments: assignments.map((assignment, index) => ({ ...(perItem?{assignment_index:assignment.assignmentIndex}:{}),
        dispatch_id: ids[index], items_sha256: digest(canonicalJSON(assignment.items)) })) };
  } else receipt.agent_id = ids[0];
  return receipt;
}

export function nativeAgentCompletion(definition, receipt, results, { summary, changed_paths = [], artifacts, evidence = [], item_results } = {}) {
  requireValue(Array.isArray(results) && results.length === receipt.agent_ids.length,
    'NATIVE_AGENT_RESULT', 'Provide one completed semantic result for every recorded native Agent');
  if(definition.fanout?.result_mode==='per_item')requireValue(Array.isArray(item_results),
    'NATIVE_ITEM_RESULT','Per-item native completion requires the ordered accepted input results');
  const output = definition.fanout
    ? { [definition.fanout.result_output]: definition.fanout.result_mode==='per_item'?item_results:results.map(item => item.result) }
    : results[0].result;
  const resultEvidence = results.map((item, index) => ({ kind: 'native_agent_result',
    agent_id: receipt.agent_ids[index], dispatch_id: receipt.agent_ids[index], result_index: index,
    result_sha256: digest(canonicalJSON(item.result)) }));
  return hostCompletionEnvelope(definition, {
    output, summary: summary || `Native Agents completed ${definition.id}`,
    changed_paths, artifacts: artifacts ?? changed_paths,
    evidence: [...(definition.fanout ? [{ kind: 'subagent_pool', resolved_count: results.length, dispatch_ids: receipt.agent_ids }] : []), ...resultEvidence, ...evidence],
    outside_paths: [],
  }, false);
}
