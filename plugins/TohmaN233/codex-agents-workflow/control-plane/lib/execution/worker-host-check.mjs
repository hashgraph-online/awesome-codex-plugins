import {readPinnedObject} from '../pinned-object-reader.mjs';
import {assertOutsideHostRunTransaction} from '../workflow-run-store.mjs';
import {resolve,relative,isAbsolute} from 'node:path';
import {join} from 'node:path';
import {canonicalJSON,digest} from '../workflow-revisions.mjs';
import {requireValue,noSymlinks} from '../workflow-paths.mjs';
import {validateData} from '../workflow-data-schema.mjs';
import {executionEnvelope,bindingContext} from '../workflow-execution-envelope.mjs';
import {resolvedSubagentPlan} from '../workflow-runtime.mjs';
import {projectFanoutInputs,assignedFanoutWritePaths,assignedFanoutIndices} from './fanout-input-projection.mjs';
import {hostToolContracts,requireHostToolExecutionScope,validateHostToolReceipt,requireHostToolInputCapacity} from './host-tool-runner.mjs';
import {hostCompletionInputs} from './main-host-check.mjs';
import {semanticResultSchema} from './host-main-automation.mjs';
import {hostCompletionResourcePaths} from './host-completion-resources.mjs';
import {saveWorkerArtifactSnapshot,readWorkerArtifactSnapshot,requireWorkerArtifactFreshness} from './worker-artifact-snapshot.mjs';
import {pathBoundaryContains} from '../workflow-bindings.mjs';
import {validateTextRepairScope} from './native-text-amendment.mjs';
import {runtimeEnvironmentForWorker} from '../runtime-environment-state.mjs';

export function requireWorkerHostCheckScope(contract,permissions){
  requireHostToolExecutionScope(contract,permissions);
  const paths=[...contract.permissions.write_paths,...(contract.identity.name==='workflow-resource-program'?[contract.argv[2]]:[])];
  requireValue(paths.every(path=>permissions.allowed_paths.some(root=>pathBoundaryContains(root,path))),
    'MAIN_WORKER_HOST_CHECK_SCOPE','Worker completion check requires its complete declared write grant');
}

export function preflightWorkerHostCompletionInputs(record,envelope,definition){
  if(!definition.completion_contract?.host_check)return;
  const contract=hostToolContracts(record.pins.root.workflow).get(definition.completion_contract.host_check.tool);
  const inputs=hostCompletionInputs(definition,bindingContext(record.state),envelope.inputs);
  if(definition.fanout){
    const plan=resolvedSubagentPlan(definition,record.state);
    for(const item of plan.items){validateData(projectFanoutInputs(inputs,plan.items,[item]),contract.input_schema.properties.inputs);
      requireWorkerHostCheckScope(contract,workerItemHostCheckScope(envelope,item,definition).permissions);}
  }else {validateData(inputs,contract.input_schema.properties.inputs);requireWorkerHostCheckScope(contract,{access:envelope.access,allowed_paths:envelope.effective_allowed_paths});}
}

function workerItemHostCheckScope(envelope,item,definition){
  const paths=assignedFanoutWritePaths({workspace:envelope.workspace,nodeAllowedPaths:envelope.effective_allowed_paths,assignedItems:[item],fanout:definition.fanout});
  const workspace=resolve(envelope.workspace,item[definition.fanout.workspace_field]),root=relative(envelope.workspace,workspace).replaceAll('\\','/');
  requireValue(root&&root!=='..'&&!root.startsWith('../')&&!isAbsolute(root)&&paths.some(path=>pathBoundaryContains(path,root))&&paths.every(path=>pathBoundaryContains(root,path)),
    'HOST_MAIN_WORKSPACE_ISOLATION','Worker check needs the complete isolated item workspace grant');
  return {workspace,permissions:{access:envelope.access,allowed_paths:['.']}};
}

export function workerHostCheckCorrectionPrompt(diagnostic,subject){
  requireValue(typeof diagnostic==='string','MAIN_WORKER_HOST_CHECK_CORRECTION','Worker check correction must preserve its declared string diagnostic');
  const prompt=`The Host completion check rejected the prior result: ${diagnostic}. Correct ${subject} and return its complete semantic JSON result. The Host automatically checks it again.`;
  requireValue(prompt.length<=200000,'CODEX_INPUT_LIMIT','Complete worker Host correction diagnostic exceeds the actual 200000-character turn input bound');
  return prompt;
}

/** Derive each slot and its mechanical inputs from the pinned Run, never model arguments. */
export function nativeHostCheckSlot(observation,item_index=null){
  return `native-${digest(canonicalJSON({observation,item_index})).slice(0,40)}`;
}

export function nativeItemHasSemanticResult(definition,item){
  return item?.outcome==='completed'||item?.outcome==='delegated'||item?.outcome==='blocked'&&definition.fanout?.shared_change_field&&Object.hasOwn(item,'result');
}

export function workerHostCheckContext(record,binding,{item_index=null,output,model_turn,native_observation}={}){
  const {state,pins}=record,definition=pins.root.workflow.nodes.find(node=>node.id===binding.node_id);
  const native=definition?.executor?.kind==='provider'&&pins.providers?.find(provider=>provider.id===definition.executor.provider_id)?.kind==='native_agent';
  requireValue((native||definition?.executor?.kind==='main'&&definition.executor.mode!=='orchestration')&&definition.completion_contract?.host_check,
    'MAIN_WORKER_HOST_CHECK_MODE','Worker check requires a pinned Main or Cooperative native worker');
  const attempt=state.nodes[definition.id].attempts.find(item=>item.id===binding.attempt_id);
  requireValue(attempt,'ATTEMPT_MISSING','Worker check lost its exact attempt');
  const envelope=executionEnvelope(definition,state,pins,attempt,binding.lease_token),check=definition.completion_contract.host_check;
  const contract=hostToolContracts(pins.root.workflow).get(check.tool);
  let inputs=hostCompletionInputs(definition,bindingContext(state),envelope.inputs),workspace=envelope.workspace,permissions={access:envelope.access,allowed_paths:envelope.effective_allowed_paths};
  let schema=semanticResultSchema(definition),turn=attempt.completion_turns;
  if(definition.fanout){
    const plan=resolvedSubagentPlan(definition,state);
    requireValue(Number.isSafeInteger(item_index)&&item_index>=0&&item_index<plan.items.length,'HOST_MAIN_ITEM','Worker check needs its exact pinned item index');
    const item=plan.items[item_index],scoped=workerItemHostCheckScope(envelope,item,definition);
    workspace=scoped.workspace;permissions=scoped.permissions;
    inputs=projectFanoutInputs(inputs,plan.items,[item]);
    schema=definition.outputs_schema.properties[definition.fanout.result_output].items;turn=attempt.main_item_turns?.[item_index];
  }else requireValue(item_index===null,'HOST_MAIN_ITEM','Single worker check cannot select an item');
  const selectedTurn=model_turn??turn;
  if(native){
    requireValue(envelope.skill_policy.mode==='cooperative'&&native_observation&&Number.isSafeInteger(native_observation.index)
      &&attempt.native_agents?.[native_observation.index]===native_observation.agent_id&&typeof native_observation.turn_id==='string'&&native_observation.turn_id.length>0,
      'NATIVE_HOST_CHECK_IDENTITY','Native check requires its exact recorded child and terminal turn');
    if(definition.fanout)requireValue(assignedFanoutIndices(resolvedSubagentPlan(definition,state),definition.fanout,native_observation.index).includes(item_index),
      'NATIVE_HOST_CHECK_IDENTITY','Native check item belongs to another recorded child');
    const proposal=attempt.native_host_proposals?.[nativeHostCheckSlot(native_observation,item_index)];
    requireValue(proposal&&canonicalJSON(proposal.native_observation)===canonicalJSON(native_observation)&&proposal.item_index===item_index&&proposal.output_sha256===digest(canonicalJSON(output)),
      'NATIVE_HOST_CHECK_PROPOSAL','Native check needs its exact durable Host-observed semantic proposal');
  }else requireValue(Number.isSafeInteger(selectedTurn)&&selectedTurn>=1&&selectedTurn<=turn,'MAIN_WORKER_HOST_CHECK_TURN','Worker check needs a durably reserved model turn');
  validateData(output,schema);const input={inputs,output};validateData(input,contract.input_schema);requireHostToolInputCapacity(contract,input);requireWorkerHostCheckScope(contract,permissions);
  const slot_id=native?nativeHostCheckSlot(native_observation,item_index):`${item_index===null?'main':`item-${item_index}`}-turn-${selectedTurn}`;
  const identity={run_id:state.run_id,node_id:definition.id,attempt_id:attempt.id,slot_id,item_index,...(native?{native_observation:structuredClone(native_observation)}:{model_turn:selectedTurn}),tool:contract.id,
    contract_sha256:digest(canonicalJSON(contract)),input_sha256:digest(canonicalJSON(input)),workspace,permissions_sha256:digest(canonicalJSON(permissions))};
  const product_paths=[...new Set((definition.required_artifacts??[]).map(item=>relative(workspace,resolve(envelope.workspace,item.path)).replaceAll('\\','/'))
    .filter(path=>path&&path!=='..'&&!path.startsWith('../')&&!isAbsolute(path)))].sort();
  return {identity,input,contract,workspace,permissions,check,envelope,attempt,definition,product_paths};
}

export async function validateWorkerHostCheckReceipt(runtime,runId,slot,context){
  const receipt=slot.receipt;validateHostToolReceipt(receipt);
  requireValue(canonicalJSON(slot.identity)===canonicalJSON(context.identity)&&['run_id','node_id','attempt_id','tool','contract_sha256','input_sha256'].every(key=>receipt[key]===slot.identity[key]),
    'HOST_TOOL_RECEIPT','Worker check receipt differs from its exact slot, input, workspace or contract');
  requireValue(Date.parse(receipt.finished_at)>=Date.parse(receipt.started_at),'HOST_TOOL_RECEIPT','Worker check timestamps are inconsistent');
  requireValue(slot.input_ref?.artifact===`executor-${receipt.attempt_id}-${slot.input_ref.sha256}.json`,'HOST_TOOL_RECEIPT','Worker input must use its exact executor artifact identity');
  const savedInput=await runtime.runs.readExecutorResult(runId,receipt.attempt_id,slot.input_ref.sha256);
  requireValue(savedInput?.kind==='worker_host_check_input'&&canonicalJSON(savedInput.identity)===canonicalJSON(slot.identity)
    &&canonicalJSON(savedInput.input)===canonicalJSON(context.input),'HOST_TOOL_OUTPUT_CORRUPT','Worker input artifact differs from its exact pinned inputs and semantic result');
  if(receipt.status!=='succeeded')return null;
  requireValue(receipt.output_ref.artifact===`executor-${receipt.attempt_id}-${receipt.output_ref.sha256}.json`,'HOST_TOOL_RECEIPT','Worker output must use its exact executor artifact identity');
  const stored=await runtime.runs.readExecutorResult(runId,receipt.attempt_id,receipt.output_ref.sha256);
  requireValue(stored?.kind==='worker_host_check_output'&&canonicalJSON(stored.identity)===canonicalJSON(slot.identity)
    &&digest(canonicalJSON(stored.output))===receipt.output_sha256&&Buffer.byteLength(canonicalJSON(stored))===receipt.output_ref.bytes,
    'HOST_TOOL_OUTPUT_CORRUPT','Worker check durable output differs from its exact receipt');
  validateData(stored.output,context.contract.output_schema);
  requireValue(!receipt.effects.outside_paths.length,'HOST_TOOL_SCOPE','Worker check wrote outside its grant');
  if(context.product_paths.length&&stored.output[context.check.success_field]===true)await readWorkerArtifactSnapshot(runtime,runId,context.workspace,context.product_paths,stored.completion_snapshot);
  return stored;
}

// The amendment baseline is the exact semantic proposal already rendered by
// the rejected checker. No worker-supplied digest or baseline is admitted.
export async function nativeTextRepairSnapshot(runtime,runId,binding,reference){
  const {record}=await runtime.authorizedExecution(runId,binding,()=>binding);
  const attempt=record.state.nodes[binding.node_id].attempts.find(item=>item.id===binding.attempt_id);
  const slot=attempt?.worker_host_checks?.[reference?.slot_id];
  requireValue(reference?.attempt_id===attempt?.id&&slot?.phase==='received'&&slot.identity.native_observation,
    'NATIVE_TEXT_AMENDMENT_BINDING','Text repair needs its exact durable native checker slot');
  const saved=await runtime.runs.readExecutorResult(runId,attempt.id,slot.input_ref.sha256);
  const context=workerHostCheckContext(record,binding,{output:saved.input?.output,item_index:slot.identity.item_index,native_observation:slot.identity.native_observation});
  const stored=await validateWorkerHostCheckReceipt(runtime,runId,slot,context),config=context.check.text_amendment;
  requireValue(config&&stored&&stored.output[context.check.success_field]===false,'NATIVE_TEXT_AMENDMENT_BINDING','Only a schema-valid rejected native proposal can become a text baseline');
  const scope=stored.output[config.repair_scope_field];validateTextRepairScope(saved.input.output,scope,config);
  return {snapshot:{kind:'native_text_repair',run_id:runId,node_id:binding.node_id,attempt_id:attempt.id,lease_generation:attempt.lease_generation??0,
    native_observation:structuredClone(slot.identity.native_observation),item_index:slot.identity.item_index,
    reference:structuredClone(reference),input_ref:structuredClone(slot.input_ref),scope:structuredClone(scope),config_sha256:digest(canonicalJSON(config))},
    baseline:saved.input.output,config};
}

export async function readNativeTextRepair(runtime,runId,binding,ref){
  requireValue(ref?.artifact===`executor-${binding.attempt_id}-${ref.sha256}.json`,'NATIVE_TEXT_AMENDMENT_BINDING','Text repair requires its exact executor artifact reference');
  const snapshot=await runtime.runs.readExecutorResult(runId,binding.attempt_id,ref.sha256);
  requireValue(snapshot?.kind==='native_text_repair'&&snapshot.run_id===runId&&snapshot.node_id===binding.node_id&&snapshot.attempt_id===binding.attempt_id,
    'NATIVE_TEXT_AMENDMENT_BINDING','Text repair artifact belongs to another execution');
  const current=await nativeTextRepairSnapshot(runtime,runId,binding,snapshot.reference);
  requireValue(canonicalJSON(current.snapshot)===canonicalJSON(snapshot),'NATIVE_TEXT_AMENDMENT_BINDING','Text repair baseline, scope, child, turn, lease or checker contract changed');
  return {...current,snapshot};
}

export async function requireWorkerHostCheckAccepted(runtime,runId,record,binding,output,reference){
  requireValue(reference&&typeof reference.attempt_id==='string'&&typeof reference.slot_id==='string','HOST_TOOL_RECEIPT_REQUIRED','Worker acceptance needs its exact Host check slot');
  const attempt=record.state.nodes[binding.node_id].attempts.find(item=>item.id===reference.attempt_id),slot=attempt?.worker_host_checks?.[reference.slot_id];
  requireValue(slot?.phase==='received'&&slot.receipt?.status==='succeeded','HOST_TOOL_RECEIPT_REQUIRED','Worker acceptance needs a successful durable Host check');
  const context=workerHostCheckContext(record,{...binding,attempt_id:reference.attempt_id},{output,item_index:slot.identity.item_index,model_turn:slot.identity.model_turn,native_observation:slot.identity.native_observation});
  const stored=await validateWorkerHostCheckReceipt(runtime,runId,slot,context);
  requireValue(stored.output[context.check.success_field]===true,'MAIN_WORKER_HOST_CHECK_FALSE','Worker completion check rejected the semantic result');
  // Both SDK and native replay retain exact receipt identity. Freshness applies
  // to explicit products; downstream consumers own any other artifact checks.
  if(context.product_paths.length)await requireWorkerArtifactFreshness(runtime,runId,context.workspace,context.product_paths,stored.completion_snapshot);
  return slot;
}

export function workerHostCheckEffectPaths(record,node_id,reference,workspace){
  requireValue(reference&&typeof reference.attempt_id==='string'&&typeof reference.slot_id==='string','HOST_TOOL_RECEIPT_REQUIRED','Rendered effects need an exact Host check reference');
  const attempt=record.state.nodes[node_id].attempts.find(item=>item.id===reference.attempt_id),accepted=attempt?.worker_host_checks?.[reference.slot_id];
  requireValue(accepted?.receipt?.status==='succeeded','HOST_TOOL_RECEIPT_REQUIRED','Rendered effects need the exact accepted check');
  const root=relative(workspace,accepted.identity.workspace).replaceAll('\\','/');
  requireValue(root!=='..'&&!root.startsWith('../')&&!isAbsolute(root),'HOST_TOOL_SCOPE','Checked workspace differs from its node grant');
  const paths=[];
  for(const slot of Object.values(attempt.worker_host_checks))if(slot.identity.item_index===accepted.identity.item_index&&slot.identity.workspace===accepted.identity.workspace&&slot.receipt){
    validateHostToolReceipt(slot.receipt);requireValue(!slot.receipt.effects.outside_paths.length,'HOST_TOOL_SCOPE','Prior check reported out-of-scope effects');
    for(const path of slot.receipt.effects.changed_paths)paths.push(root?root+'/'+path:path);
  }
  return [...new Set(paths)].sort();
}

export async function executeWorkerHostCheck(manager,entry,binding,output,{item_index=null,native_observation,controller,markIntent=()=>{},markQuiescent=()=>{},authorize,assertActive}={}){
  assertOutsideHostRunTransaction();
  const authorized=await authorize();assertActive();
  // Native authorization returns the fully audited record. Main's existing
  // authorization also checks live configuration and has no record contract.
  // Preserve that declared lane; never substitute a native missing record.
  requireValue(!native_observation||authorized?.record,'EXECUTION_SELECTOR','Native checker authorization must return its exact audited record');
  const record=native_observation?authorized.record:await entry.runtime.runs.read(entry.runId);
  const context=workerHostCheckContext(record,binding,{output,item_index,native_observation});
  await noSymlinks(context.workspace);
  const {identity,input,contract,workspace,permissions}=context;
  const persistIntent=native_observation?entry.runtime.recordNativeWorkerHostCheckIntent.bind(entry.runtime):entry.runtime.recordWorkerHostCheckIntent.bind(entry.runtime);
  const persistReceipt=native_observation?entry.runtime.recordNativeWorkerHostCheckReceipt.bind(entry.runtime):entry.runtime.recordWorkerHostCheckReceipt.bind(entry.runtime);
  const resources=await Promise.all(hostCompletionResourcePaths(contract,context.definition.resources??[]).map(async path=>{
    const pin=record.pins.root.resources.find(item=>item.path===path);requireValue(pin,'WORKFLOW_RESOURCE_PIN',`Host check resource missing: ${path}`);
    const bytes=await readPinnedObject(join(entry.runtime.runs.directory(entry.runId),'objects'),pin);return {path,sha256:pin.sha256,bytes};
  }));
  const reuse=async prior=>{
    requireValue(canonicalJSON(prior.identity)===canonicalJSON(identity),'HOST_TOOL_CONFLICT','Worker completion slot has different semantic input');
    requireValue(prior.receipt,'HOST_TOOL_RECONCILIATION_REQUIRED','Worker check has an uncertain durable intent and cannot automatically replay');
    const stored=await validateWorkerHostCheckReceipt(entry.runtime,entry.runId,prior,context);
    requireValue(stored,'HOST_TOOL_FAILED','Worker check replay requires a successful receipt');
    if(context.product_paths.length&&stored.output[context.check.success_field]===true)await requireWorkerArtifactFreshness(entry.runtime,entry.runId,workspace,context.product_paths,stored.completion_snapshot);
    if(context.check.text_amendment&&stored.output[context.check.success_field]===false)validateTextRepairScope(context.input.output,stored.output[context.check.text_amendment.repair_scope_field],context.check.text_amendment);
    return {accepted:stored.output[context.check.success_field],diagnostic:stored.output[context.check.correction_field],reference:{attempt_id:binding.attempt_id,slot_id:identity.slot_id},
      ...(context.check.text_amendment?{repair_scope:structuredClone(stored.output[context.check.text_amendment.repair_scope_field])}:{})};
  };
  const prior=context.attempt.worker_host_checks?.[identity.slot_id];
  if(prior)return reuse(prior);
  const owner={controller:controller??new AbortController(),settled:false};(entry.workerChecks??=new Set()).add(owner);let intent=false,quiescent=false;
  try{
    const prepared=record.state.constraints?.execution_binding?.kind!=='wsl'&&manager.hostToolRunner.hasProgramEnvironmentAdmission?.(contract)
      ?{environment:runtimeEnvironmentForWorker(record.state,context.definition,record.pins),record}
      :native_observation?await entry.runtime.ensureNativeRuntimeEnvironmentFromAudit(entry.runId,binding,record):await entry.runtime.ensureRuntimeEnvironment(entry.runId,binding);
    const admission=await persistIntent(entry.runId,{...binding,identity,input},native_observation?prepared.record:undefined);
    if(!admission.created)return reuse(admission.slot);
    intent=true;markIntent();
    let executed;
    try{executed=await manager.hostToolRunner.execute(contract,input,{run_id:entry.runId,node_id:binding.node_id,attempt_id:binding.attempt_id,execution_slot:identity.slot_id,
      workspace,task_root:record.state.constraints?.task_workspace??context.envelope.workspace,resources,permissions,runtime_environment:structuredClone(prepared.environment),
      prepareRuntimeEnvironment:()=>entry.runtime.ensureRuntimeEnvironment(entry.runId,binding),execution_binding:structuredClone(record.state.constraints?.execution_binding??null)},
      {signal:owner.controller.signal,assertActive,receiptOnError:true});}
    catch(error){if(error.host_tool_receipt){quiescent=true;markQuiescent();await persistReceipt(entry.runId,{...binding,slot_id:identity.slot_id,receipt:error.host_tool_receipt});}throw error;}
    quiescent=true;markQuiescent();
    let receipt=executed.receipt,stored=null;
    if(receipt.status==='succeeded'){
      stored={kind:'worker_host_check_output',identity,output:executed.output,
        ...(context.product_paths.length&&executed.output[context.check.success_field]===true?{completion_snapshot:await saveWorkerArtifactSnapshot(entry.runtime,entry.runId,digest(canonicalJSON(identity)).slice(0,32),workspace,context.product_paths)}:{})};
    }
    const publish=async()=>{
      if(stored){const saved=await entry.runtime.runs.saveExecutorResult(entry.runId,binding.attempt_id,stored);
        receipt={...receipt,output_ref:{...saved,bytes:Buffer.byteLength(canonicalJSON(stored))}};}
      await persistReceipt(entry.runId,{...binding,slot_id:identity.slot_id,receipt});
    };
    if(native_observation&&stored)await entry.runtime.runs.withHostTransaction(entry.runId,'native_prepare',publish);
    else await publish();
    requireValue(receipt.status==='succeeded',receipt.status==='cancelled'?'HOST_TOOL_CANCELLED':receipt.status==='timed_out'?'HOST_TOOL_TIMEOUT':'HOST_TOOL_FAILED',receipt.diagnostics.message||'Worker Host check failed');
    await authorize();assertActive();
    if(context.check.text_amendment&&executed.output[context.check.success_field]===false)validateTextRepairScope(context.input.output,executed.output[context.check.text_amendment.repair_scope_field],context.check.text_amendment);
    return {accepted:executed.output[context.check.success_field],diagnostic:executed.output[context.check.correction_field],reference:{attempt_id:binding.attempt_id,slot_id:identity.slot_id},
      ...(context.check.text_amendment?{repair_scope:structuredClone(executed.output[context.check.text_amendment.repair_scope_field])}:{})};
  }finally{if(!intent||quiescent){owner.settled=true;entry.workerChecks.delete(owner);}}
}
