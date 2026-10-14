import { automaticAuthoringCompletion } from './skill-import/completion-policy.mjs';
import {nativeSpawnBatchBinding} from './execution/native-spawn-batch.mjs';
import { observeForegroundPhase } from './foreground-operation-observation.mjs';
import { certificateForPublishedWorkflow, requireCurrentConversionCertificate } from './skill-import/conversion-certificate.mjs';
import {retainOwnedAuthority,replaceOwnedAuthority,readOwnedAuthority,readOwnedAuthorityForThread} from './execution/owned-workflow-authority.mjs';
import {discoverRuntimeEnvironment, verifyRuntimeEnvironment, registryPathForConfig, readHostRuntimeRegistry, updateRuntimeCandidate} from './runtime-environment.mjs';
import {workspaceRuntimeDirectories} from './runtime-environment-state.mjs';
import { evaluateReview } from './skill-import/review-checklist.mjs';
import { cleanupCaches } from './cache-cleanup.mjs';
import { homedir } from 'node:os';
import { randomUUID } from 'node:crypto';
import { AsyncLocalStorage } from 'node:async_hooks';
import { isProxy } from 'node:util/types';
import { prepareTaskInputs, generateTaskBrief } from './task-inputs.mjs';
import { localCodexCatalog } from './execution/local-codex-catalog.mjs';
import { refreshCodexRegistration } from './execution/codex-runtime-registration.mjs';
import { lstat, readFile, rm } from 'node:fs/promises';
import { advanceGeneration, acceptGeneration, loginGeneration, recheckGenerationProposal, acceptRecheckedGenerationReview, prepareAuthoringReview } from './skill-import/generation.mjs';
import { continueGenerationRepair } from './skill-import/generation-repair.mjs';
import { discoverAuthoringPreview } from './skill-import/generation-preview.mjs';
import { discoverFolderSkills } from './skill-import/folder-inventory.mjs';
import { loadRoutingSettings, saveRoutingSettings } from './skill-import/routing-settings.mjs';
import { dirname, join, resolve, isAbsolute, relative } from 'node:path';
import { loadConfig, isEnvironmentDisabled, appendAuditEvent } from './config.mjs';
import { WorkflowStore } from './workflow-store.mjs';
import { WorkflowRuntime, resolvedSubagentPlan, nativeRejectedTurnHistory } from './workflow-runtime.mjs';
import { WorkflowRunStore,withRunStoreObservation } from './workflow-run-store.mjs';
import {committedTerminalOutput} from './execution/terminal-output.mjs';
import { writeDurableJSON } from './workflow-events.mjs';
import { assignedFanoutIndices, activeFanoutAssignmentIndices } from './execution/fanout-input-projection.mjs';
import { nativeAgentHandoff, materializedNativeAgentHandoff, nativeAgentReceipt, nativeAgentCompletion, preflightNativeHostCompletion, nativeAgentResultSchema } from './execution/native-agent-bridge.mjs';
import { WorkflowExecutor } from './workflow-executor.mjs';
import { validateWorkflowGraph } from './workflow-validator.mjs';
import { migrateV6OnDisk, restoreV6Backup } from './workflow-migration-v6.mjs';
import { connectorRegistryFor } from '../connectors/registry.mjs';
import { requireValue, insideRoot, noSymlinks, ensureDirectory, workflowId } from './workflow-paths.mjs';
import { importCoarseSkill, verifyCoarseRelocation } from './skill-import/coarse-compiler.mjs';
import { expansionPacket, applyExpansion } from './skill-import/semantic-expander.mjs';
import { buildProviderAdapter } from './providers.mjs';
import { strictManagerFor } from './execution/strict-session-manager.mjs';
import { managedNativeManagerFor } from './execution/managed-native-manager.mjs';
import { hostMainManagerFor } from './execution/host-main-manager.mjs';
import { runHistoryMaintenanceFor } from './run-history-maintenance.mjs';
import { launchDetachedHostMain, readHostMainWorker, waitForDetachedHostMainStop } from './execution/host-main-worker.mjs';
import { waitForWorkflow, WORKFLOW_WAIT_MS } from './workflow-wait.mjs';
import { attemptAdmissionFor, executionAdmissionOpen, assertExecutionAttemptAdmission } from './execution/attempt-admission.mjs';
import { RunExecutionCoordinator } from './execution/run-execution-coordinator.mjs';
import { importReviewPacket, reviewImportedDraft } from './skill-import/review-import.mjs';
import { authoringRunPack } from './skill-import/expansion-run.mjs';
import { validateGenerationProposal } from './skill-import/proposal-validation.mjs';
import { SkillInventory } from './skill-import/inventory.mjs';
import { discoverCodexSkills } from './skill-import/codex-inventory.mjs';
import { resolveWorkflowPins } from './workflow-pins.mjs';
import { canonicalJSON, digest, prepareResources } from './workflow-revisions.mjs';
import { inlineSkillReference } from './skill-import/inline-skill.mjs';
import { parallelManagerFor } from './parallel/worktree-manager.mjs';
import { readEditorResource, writeEditorResource, publishEditorWorkflow, publishableEditorWorkflow } from './workflow-editor.mjs';
import { codexQualification, qualifiedStrictSettings } from './execution/strict-config.mjs';
import { adoptRunTree, conversationControlRecoveryRequest, controllerAttempt, reattachAttempt } from './workflow-recovery.mjs';
import { childIdentity } from './workflow-subworkflow.mjs';
import { nodePermissions, runPermissions, leaseToken } from './workflow-execution-envelope.mjs';
import { effectiveRunInputs } from './workflow-run-inputs.mjs';
import { intersectBoundaries, resolveBindings } from './workflow-bindings.mjs';
import { effectiveSkillPolicy } from './workflow-reference-schema.mjs';
import { nodeWorkspace } from './parallel/workspace.mjs';
import { skillSourceStatus } from './skill-import/source-status.mjs';
import { HostToolRunner, hostToolBindingIssues, requireHostToolBindings } from './execution/host-tool-runner.mjs';
import { authoringHostToolRegistry } from './execution/authoring-host-tools.mjs';
import { workflowResourceProgramRegistry } from './execution/workflow-resource-program.mjs';
import { inspectNativeAgents, inspectNativeParent, nativeParentThreadId, withNativeAgentObserver, withNativeAgentObserverDrive } from './execution/native-agent-observer.mjs';
import { resolveMainModelSelection } from './execution/main-model-selection.mjs';
import {workerHostCheckEffectPaths,nativeItemHasSemanticResult,nativeTextRepairSnapshot,readNativeTextRepair} from './execution/worker-host-check.mjs';
import {applyTextAmendment,textAmendmentSchema} from './execution/native-text-amendment.mjs';
import {prepareNativeSpan,materializeWithNativeSpan,reuseNativeSpanPublication,settleNativeSpan,releaseNativeSpanOwner} from './execution/native-dispatch-span.mjs';
import { WorkflowDrive } from './workflow-drive.mjs';
import { WorkflowAuthoringCompiler, compileWorkflowBrief } from './skill-import/workflow-authoring.mjs';
import { exportWorkflowPackage, installWorkflowPackage, validateWorkflowPackage } from './workflow-package.mjs';
import { AUTHORING_WORKFLOWS, authoringReviewIdentity, authoringWorkflow, authoringWorkflowForPack, ensureStoredAuthoringWorkflows, isAuthoringRunProvenance, storedAuthoringBindings, validateStoredAuthoringWorkflow } from './authoring/authoring-workflows.mjs';
import { CONVERSION_CONTRACT } from './skill-import/conversion-contract.mjs';
import { requireDeployableConvertedSnapshot } from './skill-import/conversion-deployment.mjs';
import { routeReadyWorkflows } from './workflow-routing.mjs';
import { templateKind, roleNode } from './template-kind.mjs';
import { renderTemplate } from './templates.mjs';
import { validateData } from './workflow-data-schema.mjs';
import { migrateStoredWorkflowProviderIds } from './workflow-provider-identity.mjs';
import { migrateStoredWorkflowHostToolIdentities } from './workflow-host-tool-identity.mjs';

const WORKFLOW_INPUT_FILE_LIMIT=1024*1024;

// The Host owns this lifetime, not a Run, model argument or global service cache.
// Detached async work inherits an inactive context after the request settles.
const executionRequests=new AsyncLocalStorage();
export async function withWorkflowExecutionRequest(action){
  if(executionRequests.getStore()?.active)return action();
  const request={active:true,services:new Map()};
  try{return await executionRequests.run(request,action);}
  finally{request.active=false;request.services.clear();}
}
const REQUEST_OPEN_OPERATIONS=new Set(['read','run_main','wait','get',
  'start','native_next','native_spawned_batch','native_followed_up','orchestration_complete']);

function runtimeInitializationSnapshot(value,references){
  // Runtime capability metadata is JavaScript state, not Workflow JSON. Encode
  // every supported type explicitly; retain callable/opaque/prototype identity
  // separately and inspect own enumerable state for in-place changes/cycles.
  const seen=new Map();let entries=0,characters=0,complete=true,reason=null;
  const identity=value=>{references.push(value);return references.length-1;};
  const visit=(item,depth)=>{
    // Exhausting this optimization's comparison budget cannot reject state
    // accepted by the original opening. It makes the whole basis non-reusable.
    if(!complete)return null;
    if(++entries>100000||depth>128){complete=false;reason='budget';return null;}
    if(item===null)return ['null'];
    const type=typeof item;
    if(type==='undefined')return ['undefined'];
    if(type==='string'){
      if((characters+=item.length)>8*1024*1024){complete=false;reason='budget';return null;}
      return [type,item];
    }
    if(type==='boolean')return [type,item];
    if(type==='number')return [type,Object.is(item,-0)?'-0':Number.isFinite(item)?item:String(item)];
    if(type==='bigint')return [type,identity(item)];
    if(type==='symbol')return [type,identity(item)];
    if(isProxy(item)){complete=false;reason='accessor';identity(item);return null;}
    if(seen.has(item))return ['reference',seen.get(item)];
    const index=seen.size;seen.set(item,index);
    const prototype=Object.getPrototypeOf(item),array=Array.isArray(item);
    const opaque=type==='function'||(!array&&prototype!==Object.prototype&&prototype!==null);
    const ownKeys=Reflect.ownKeys(item).filter(key=>Object.getOwnPropertyDescriptor(item,key).enumerable);
    if(ownKeys.length>100000-entries){complete=false;reason='budget';return null;}
    const keys=[...ownKeys.filter(key=>typeof key==='string').sort(),...ownKeys.filter(key=>typeof key==='symbol')];
    const properties=[];
    for(const key of keys){
      if(!complete)break;
      if(typeof key==='string'&&(characters+=key.length)>8*1024*1024){complete=false;reason='budget';break;}
      const descriptor=Object.getOwnPropertyDescriptor(item,key);
      if(!Object.hasOwn(descriptor,'value')){
        complete=false;reason='accessor';identity(descriptor.get);identity(descriptor.set);break;
      }
      properties.push([typeof key==='symbol'?['symbol',identity(key)]:['string',key],visit(descriptor.value,depth+1)]);
    }
    return [type,index,identity(prototype),opaque?identity(item):null,array?item.length:null,
      properties];
  };
  const snapshot=visit(value,0);return {snapshot,complete,reason};
}
function initializationBasis(service,config){
  const hash=digest(canonicalJSON(config));
  const ineligible=reason=>({hash,runtimeHash:null,reusable:false,reason,references:[]});
  // Guard capture-front containers and outer fields before retrieving values.
  // Post-construction accessors are valid original runtime state; comparison
  // must not add their callbacks, including on unused registry entries.
  const dataProperties=(source,keys)=>{
    const values={};
    for(const key of keys){
      let object=source==null?null:Object(source),depth=0,descriptor;
      while(object){
        if(isProxy(object))return {reason:'accessor'};
        if(++depth>128)return {reason:'budget'};
        descriptor=Object.getOwnPropertyDescriptor(object,key);
        if(descriptor)break;
        object=Object.getPrototypeOf(object);
      }
      if(descriptor&&!Object.hasOwn(descriptor,'value'))return {reason:'accessor'};
      values[key]=descriptor?.value;
    }
    return {values};
  };
  const capturedService=dataProperties(service,['capabilities','env','registry','strictManager','managedNativeManager','hostMainManager','parallelManager']);
  if(capturedService.reason)return ineligible(capturedService.reason);
  const owned=capturedService.values;
  const capturedCapabilities=dataProperties(owned.capabilities,['hostToolRegistry','parallelWriteCapability','strictCapability','hostToolRunner','context','host_tools']);
  if(capturedCapabilities.reason)return ineligible(capturedCapabilities.reason);
  const capabilities=capturedCapabilities.values,registry=capabilities.hostToolRegistry??{};
  if(isProxy(registry))return ineligible('accessor');
  const names=Object.keys(registry);
  if(names.length>100000)return ineligible('budget');
  const tools=[];
  for(const name of names){
    const descriptor=Object.getOwnPropertyDescriptor(registry,name);
    if(!Object.hasOwn(descriptor,'value'))return ineligible('accessor');
    tools.push([name,descriptor.value]);
  }
  const references=[owned.registry,owned.strictManager,owned.managedNativeManager,owned.hostMainManager,owned.parallelManager,
    capabilities.parallelWriteCapability,capabilities.strictCapability,capabilities.hostToolRunner,...tools.map(([,broker])=>broker)];
  let reason=null;
  const brokerMetadata=broker=>{
    const descriptors={};
    for(const key of ['identity','attestation','execute','cancel']){
      let descriptor={value:undefined,enumerable:true},object=broker==null?null:Object(broker),depth=0;
      while(object){
        if(isProxy(object)){reason='accessor';break;}
        if(++depth>128){reason='budget';break;}
        const found=Object.getOwnPropertyDescriptor(object,key);
        if(found){descriptor={...found,enumerable:true};break;}
        object=Object.getPrototypeOf(object);
      }
      descriptors[key]=descriptor;
    }
    return Object.defineProperties({},descriptors);
  };
  // process.env's special prototype is immaterial to original ENV consumers;
  // copy data descriptors exactly; never invoke accessors for fingerprinting.
  const environment=isProxy(owned.env)?owned.env:Object.defineProperties({},Object.getOwnPropertyDescriptors(owned.env));
  const state=runtimeInitializationSnapshot({env:environment,context:capabilities.context,
    host_tools:capabilities.host_tools,tools:tools.map(([name,broker])=>({name,metadata:brokerMetadata(broker)}))},references);
  const reusable=state.complete&&!reason;
  return {hash,runtimeHash:reusable?digest(JSON.stringify(state.snapshot)):null,
    reusable,reason:reason??state.reason,references};
}
function sameInitializationBasis(left,right){
  return left.reusable&&right.reusable&&left.hash===right.hash&&left.runtimeHash===right.runtimeHash&&left.references.length===right.references.length
    &&left.references.every((value,index)=>value===right.references[index]);
}

function hasNestedModelInput(value){
  if(!value||typeof value!=='object'||Array.isArray(value))return false;
  return Object.values(value).some(item=>item&&typeof item==='object'&&(Array.isArray(item)?item.some(entry=>entry&&typeof entry==='object'):true));
}

export async function loadWorkflowInputsFile(request,{model=false}={}){
  if(request?.inputs_path===undefined){
    requireValue(!model||!hasNestedModelInput(request?.inputs),'RUN_STRUCTURED_INPUT_SOURCE',
      'Nested Workflow inputs must come from inputs_path or a scalar local path consumed by a Host tool; do not transcribe structured files into the call');
    return request;
  }
  requireValue(request.inputs===undefined,'RUN_INPUT_SOURCE','Use inputs or inputs_path, never both');
  requireValue(typeof request.workspace==='string'&&isAbsolute(request.workspace),'RUN_WORKSPACE','inputs_path needs an absolute Run workspace');
  requireValue(typeof request.inputs_path==='string'&&request.inputs_path.trim(),'RUN_INPUT_FILE','inputs_path must name one JSON file');
  const workspace=resolve(request.workspace),path=isAbsolute(request.inputs_path)?resolve(request.inputs_path):resolve(workspace,request.inputs_path);
  insideRoot(workspace,path);await noSymlinks(path);
  const stat=await lstat(path);
  requireValue(stat.isFile()&&stat.nlink===1&&stat.size>0&&stat.size<=WORKFLOW_INPUT_FILE_LIMIT,'RUN_INPUT_FILE','Workflow input packet must be one bounded regular file');
  const bytes=await readFile(path);
  requireValue(bytes.length===stat.size,'RUN_INPUT_FILE','Workflow input packet changed while being read');
  let inputs;
  try{inputs=JSON.parse(bytes.toString('utf8'));}catch{requireValue(false,'RUN_INPUT_JSON','Workflow input packet is not valid JSON');}
  requireValue(inputs&&typeof inputs==='object'&&!Array.isArray(inputs),'RUN_INPUT_JSON','Workflow input packet must contain one JSON object');
  requireValue(request.constraints===undefined||(request.constraints&&typeof request.constraints==='object'&&!Array.isArray(request.constraints)),'RUN_CONSTRAINTS','Run constraints must be an object');
  const {inputs_path,...rest}=request;
  return {...rest,inputs,constraints:{...(request.constraints??{}),workflow_input_file:{path:relative(workspace,path).replaceAll('\\','/'),sha256:digest(bytes),bytes:bytes.length}}};
}

const REMOTE_PACKAGE_LIMIT=70*1024*1024;
const BUILTIN_ROLE_PREFIX='builtin-role-';
const nativeDriveOwners=new Map();
import { hasOrchestrationMain } from './execution/main-execution-mode.mjs';
import { prepareMainOrchestration, completeMainOrchestration } from './execution/main-orchestration.mjs';
import {startupSemanticContract,startupSemanticNode} from './execution/workflow-startup-semantic.mjs';
import { WORKFLOW_CALL_DEFAULTS, WORKFLOW_LONG_CALL_TOOLS, workflowCallArguments, workflowInvocationAdapters, workflowAuthoringControllerAdapterDescriptor, workflowControllerAdapterDescriptor } from './execution/workflow-call-adapter.mjs';
import { workflowMcpTransport } from './workflow-call-policy.mjs';
import { createPreparedStartup } from './execution/prepared-startup-record.mjs';
const MODEL_NATIVE_CONTINUATIONS=new Set(['native_next','native_spawned_batch','native_followed_up']);
const WORKFLOW_EXECUTION_OPEN=Symbol('Workflow execution without eager Role profiles');
const WORKFLOW_EXECUTION_OPERATIONS=new Set(['start','native_next','native_spawned_batch','native_followed_up','orchestration_complete']);
function authoringControllerContinuation(result, authority, operation='drive') {
  return {...result,next_action:`workflow_${operation}`,invocation_adapter:workflowAuthoringControllerAdapterDescriptor(operation,authority),
    ...(operation==='resume'?{cancellation_invocation_adapter:workflowAuthoringControllerAdapterDescriptor('cancel',authority)}:{})};
}
function modelNativeContinuationView(value,adapters){
  if(!value||typeof value!=='object')return value;
  const result=structuredClone(value);
  delete result.control_token;
  delete result.lease_token;
  if(['workflow_native_next','spawn_released_packets_then_journal_batch','continue_recorded_agent','repair_recorded_agent']
    .includes(result.next_action))result.next_action_args={};
  if(result.next_action_args?.continuation?.next_action==='workflow_native_next')
    result.next_action_args.continuation.next_action_args={};
  if(result.wait&&typeof result.wait==='object')delete result.wait.agent_ids;
  // The launching Host fixes the protocol family before this projection.
  // Caller data and tool failures cannot select or substitute a transport.
  const invocationTool = result.completion_tool ?? result.registration_tool
    ?? (['continue_recorded_agent','repair_recorded_agent'].includes(result.next_action)
      ? result.followup_config ? 'workflow_native_followed_up' : 'workflow_native_next'
      : result.next_action);
  if(WORKFLOW_LONG_CALL_TOOLS.includes(invocationTool))
    result.invocation_adapter=invocationTool==='workflow_native_spawned_batch'
      ?adapters.nativeSpawnBatch(result.batch_id):adapters.call(invocationTool);
  const continuation=result.next_action_args?.continuation;
  if(continuation?.next_action==='workflow_native_next')
    continuation.invocation_adapter=adapters.call('workflow_native_next');
  if(['native_agent_blocked','native_agent_invalid_result'].includes(result.status)&&result.followup_config){
    const visible={};
    for(const key of ['status','next_action','next_action_args','followup_config','invocation_adapter'])
      if(Object.hasOwn(result,key))visible[key]=result[key];
    return visible;
  }
  if(result.status==='native_handoff'){
    const spawn_calls=Array.isArray(result.packets)
      ?result.packets.map(packet=>({tool:'collaboration.spawn_agent',arguments:{...packet.spawn_config,message:packet.prompt}}))
      :result.spawn_calls;
    requireValue(Array.isArray(spawn_calls)&&spawn_calls.length>0&&spawn_calls.length<=32&&spawn_calls.every(call=>
      call.tool==='collaboration.spawn_agent'&&call.arguments&&typeof call.arguments.task_name==='string'
      &&typeof call.arguments.message==='string'&&call.arguments.message.length>0),
      'NATIVE_AGENT_HANDOFF','Model-facing native handoff requires exact Host-generated spawn arguments');
    const visible={spawn_calls};
    for(const key of ['status','node_id','next_action','next_action_args','registration_tool','batch_id','invocation_adapter',
      'acknowledged_batch_id','journaled_spawn_count'])if(Object.hasOwn(result,key))visible[key]=result[key];
    return visible;
  }
  return result;
}
function nativeContinuation(runId, controlToken) {
  return { next_action: 'workflow_native_next', next_action_args: { run_id: runId, control_token: controlToken } };
}
function nativeBatchToJournal(runId,controlToken,attemptId,indices){
  return {next_action:'spawn_released_packets_then_journal_batch',
    next_action_args:{run_id:runId,control_token:controlToken,attempt_id:attemptId},
    registration_tool:'workflow_native_spawned_batch',released_packet_indices:[...indices]};
}
async function nativeAttemptBinding(runtime, { run_id, control_token, attempt_id }) {
  const record=await runtime.authorizedRun(run_id,{control_token});
  const matches = record.pins.root.workflow.nodes.flatMap(definition => {
    const provider = record.pins.providers.find(item => item.id === definition.executor?.provider_id);
    const node=record.state.nodes[definition.id];
    const attempt = attempt_id ? node?.attempts.find(item => item.id === attempt_id)
      :['claimed','running'].includes(node?.status)
        ?node?.attempts.find(item=>item.id===node.active_attempt_id&&['claimed','running'].includes(item.status))
        :undefined;
    return definition.executor?.kind === 'provider' && provider?.kind === 'native_agent' && attempt
      ? [{ definition, attempt }] : [];
  });
  requireValue(matches.length === 1, 'NATIVE_AGENT_ATTEMPT', 'Attempt ID must identify one native Agent node in this Run');
  const { definition, attempt } = matches[0];
  return { record, definition, attempt, binding: { run_id, node_id: definition.id, attempt_id:attempt.id,
    lease_token: leaseToken(control_token, run_id, definition.id, attempt.id, attempt.lease_generation ?? 0), control_token } };
}
function unresolvedNativeItemTargets(record,definition,attempt,index){
  const assigned=assignedFanoutIndices(resolvedSubagentPlan(definition,record.state),definition.fanout,index);
  const unresolved=assigned.filter(itemIndex=>!attempt.native_item_results?.[itemIndex]);
  return definition.fanout.item_delivery==='incremental'?unresolved.slice(0,1):unresolved;
}
function activeNativeAssignmentSlots(record,definition,attempt){
  const plan=resolvedSubagentPlan(definition,record.state);
  return plan?activeFanoutAssignmentIndices(plan,definition.fanout,attempt.inherited_native_item_indices):[0];
}
async function bundledRoleDefinitions(providers){
  const {roles}=JSON.parse(await readFile(new URL('../builtin-role-definitions.json',import.meta.url),'utf8'));
  requireValue(Array.isArray(roles)&&roles.every(item=>item.stages?.length===1),'BUILTIN_ROLE_DEFINITIONS','Bundled Roles must each contain exactly one stage');
  return roles.map(item=>{
    const stage=item.stages[0],provider=providers.find(candidate=>candidate.id===stage.provider_id);
    return {item,stage,provider,id:BUILTIN_ROLE_PREFIX+item.id,revision_hash:digest(canonicalJSON(item))};
  });
}
function roleProviderSupports(provider,access='read_only'){
  return provider?.capabilities?.read===true
    &&(access!=='bounded_write'||provider.capabilities?.write===true);
}
function roleProviderAvailable(provider,access='read_only'){
  return provider?.enabled===true&&roleProviderSupports(provider,access);
}
function roleProviderModel(provider){
  return provider?.config?.model??provider?.config?.model_label??null;
}
function roleExecutionPolicy(node){
  return {access:node.access,approval:{required:node.approval?.required===true||node.requires_user_approval===true},
    path_scope:structuredClone(node.path_scope??null)};
}
function compiledRoleProvider(provider,policy,options={}){
  if(!provider)return {provider_kind:null,adapter:null,agent_type:'default',model:null,reasoning_effort:null};
  const adapter=buildProviderAdapter(provider,{access:policy.access,requires_user_approval:policy.approval.required},options);
  if(adapter.execution==='builtin_connector')adapter.operations.start='workflow_start_role_connector';
  return {provider_kind:provider.kind,adapter,agent_type:adapter.agent_type??null,
    model:roleProviderModel(provider),reasoning_effort:provider.config?.reasoning_effort??null};
}
function roleConnectorPermissions(profile,args){
  const permissions=runPermissions({workspace:args.workspace,access:profile.access,
    allowed_paths:profile.access==='read_only'?[]:args.allowed_paths??[]});
  if(profile.access==='bounded_write'&&Array.isArray(profile.path_scope)){
    const effective=intersectBoundaries(profile.path_scope,permissions.allowed_paths);
    const key=path=>process.platform==='win32'?path.toLowerCase():path;
    requireValue(permissions.allowed_paths.every(path=>effective.some(boundary=>key(boundary)===key(path))),
      'ROLE_PATH_SCOPE','Caller write boundaries must remain inside the published Role path scope');
    permissions.allowed_paths=effective;
  }
  return permissions;
}
async function bundledRoles(providers){
  return (await bundledRoleDefinitions(providers)).filter(entry=>roleProviderSupports(entry.provider,entry.stage.access));
}
function builtinRoleCustomizationId(pack){
  if(pack.provenance?.kind!=='role_customization')return null;
  const id=pack.provenance.builtin_role_id;
  requireValue(typeof id==='string'&&id.startsWith(BUILTIN_ROLE_PREFIX),'ROLE_CUSTOMIZATION_ID','Role customization must identify one built-in Role');
  requireValue(templateKind(pack)==='role','ROLE_CUSTOMIZATION_KIND','Role customization must remain a Role template');
  return id;
}
function builtinRoleCustomizations(packs){
  const result=new Map();
  for(const pack of packs){
    const id=builtinRoleCustomizationId(pack);if(!id)continue;
    requireValue(!result.has(id),'ROLE_CUSTOMIZATION_DUPLICATE',`Built-in Role ${id} has more than one customization Pack`);
    result.set(id,pack);
  }
  return result;
}
function storedRoleDescriptor(pack,providers){
  const node=roleNode(pack),provider=providers.find(item=>item.id===node.executor?.provider_id);
  return {node,provider,workflow_id:pack.workflow.id,revision_hash:pack.revision_hash,status:pack.workflow.status,enabled:pack.workflow.enabled!==false,
    available:roleProviderAvailable(provider,node.access),provider_id:provider?.id??node.executor?.provider_id??null,
    model:roleProviderModel(provider),reasoning_effort:provider?.config?.reasoning_effort??null};
}
function directRolePrompt(instructions,args){
  const constraints=args.constraints==null?'(not provided)':typeof args.constraints==='string'?args.constraints:canonicalJSON(args.constraints);
  const prompt=`${instructions}\n\nTASK\n${args.task}\n\nCONTEXT\n${args.context??'(not provided)'}\n\nCONSTRAINTS AND OWNERSHIP\n${constraints}\n\nVERIFICATION\n${args.verification??'(not provided)'}`;
  requireValue(prompt.length<=200000,'ROLE_TASK','Compiled role instructions are too long');
  return prompt;
}
function storedRoleProfile(pack,providers,args,{id=pack.workflow.id,instructions_override,providerOptions={}}={}){
  requireValue(pack.workflow.status==='ready'&&pack.workflow.enabled!==false,'ROLE_NOT_READY','Role template must be published and enabled');
  const {node,provider}=storedRoleDescriptor(pack,providers);
  if(node.executor?.provider_id)requireValue(roleProviderAvailable(provider,node.access),'ROLE_PROVIDER_UNAVAILABLE','Pinned Role needs an enabled compatible Provider');
  const instructions=pack.workflow.role_prompt_mode==='append_context'
    ?directRolePrompt(instructions_override??node.prompt_template,args)
    :renderTemplate(node.prompt_template,{task:args.task,context:args.context,constraints:args.constraints,verification:args.verification,task_type_id:id,stage_id:node.id,provider_name:provider?.name});
  const policy=roleExecutionPolicy(node);
  return {id,source_workflow_id:pack.workflow.id,revision_hash:pack.revision_hash,template_kind:'role',role:node.role,...policy,
    provider_id:provider?.id??null,...compiledRoleProvider(provider,policy,providerOptions),instructions};
}
async function storedRolePacks(store){
  const packs=[];
  for(const metadata of await store.listMetadata())if(templateKind(metadata)==='role'||metadata.provenance?.kind==='role_customization')
    packs.push(await store.snapshot(metadata.workflow.id,metadata.revision_hash));
  return packs;
}
async function activeRoleProfiles(providers,store){
  const packs=await storedRolePacks(store);
  const customizations=builtinRoleCustomizations(packs),profiles=[];
  for(const entry of await bundledRoles(providers)){
    const customization=customizations.get(entry.id);
    if(customization?.workflow.status==='ready'){
      const descriptor=storedRoleDescriptor(customization,providers);
      const unchanged=descriptor.node.prompt_template===entry.stage.template;
      profiles.push({id:entry.id,revision_hash:customization.revision_hash,source_workflow_id:customization.workflow.id,
        name:customization.workflow.name,role:descriptor.node.role,access:descriptor.node.access,provider_id:descriptor.provider_id,
        enabled:descriptor.enabled,available:descriptor.available,
        instructions:unchanged&&entry.item.role_instructions?entry.item.role_instructions:descriptor.node.prompt_template});
    }else profiles.push({id:entry.id,revision_hash:entry.revision_hash,name:entry.item.name,role:entry.stage.role,access:entry.stage.access,
      provider_id:entry.provider?.id??entry.stage.provider_id??null,enabled:entry.item.enabled!==false,
      available:roleProviderAvailable(entry.provider,entry.stage.access),
      instructions:entry.item.role_instructions||entry.stage.template});
  }
  for(const pack of packs)if(!builtinRoleCustomizationId(pack)&&templateKind(pack)==='role'&&pack.workflow.status==='ready'){
    const descriptor=storedRoleDescriptor(pack,providers);
    profiles.push({id:pack.workflow.id,revision_hash:pack.revision_hash,source_workflow_id:pack.workflow.id,name:pack.workflow.name,
      role:descriptor.node.role,access:descriptor.node.access,provider_id:descriptor.provider_id,enabled:descriptor.enabled,
      available:descriptor.available,instructions:descriptor.node.prompt_template});
  }
  requireValue(new Set(profiles.map(profile=>profile.id)).size===profiles.length,'ROLE_PROFILE_DUPLICATE','Role catalog contains duplicate active identities');
  for(const profile of profiles)requireValue(typeof profile.instructions==='string'&&profile.instructions.trim()&&profile.instructions.length<=16000,
    'ROLE_PROFILE_INSTRUCTIONS',`Role ${profile.id} needs concise bounded behavior instructions`);
  return profiles;
}
async function readBoundedResponse(response,limit){
  const declared=Number(response.headers?.get?.('content-length'));
  if(Number.isFinite(declared))requireValue(declared>=0&&declared<=limit,'WORKFLOW_PACKAGE_LIMIT','Remote Workflow package exceeds the bounded limit');
  if(!response.body?.getReader){const bytes=Buffer.from(await response.arrayBuffer());requireValue(bytes.length<=limit,'WORKFLOW_PACKAGE_LIMIT','Remote Workflow package exceeds the bounded limit');return bytes;}
  const reader=response.body.getReader(),chunks=[];let total=0;
  try{for(;;){const {done,value}=await reader.read();if(done)break;const chunk=Buffer.from(value);total+=chunk.length;if(total>limit){await reader.cancel();requireValue(false,'WORKFLOW_PACKAGE_LIMIT','Remote Workflow package exceeds the bounded limit');}chunks.push(chunk);}}
  finally{reader.releaseLock?.();}
  return Buffer.concat(chunks,total);
}

async function fetchWorkflowPackage(fetchImpl,url){
  const controller=new AbortController();let timedOut=false;
  const timer=setTimeout(()=>{timedOut=true;controller.abort();},30000);
  try{
    const response=await fetchImpl(url,{redirect:'error',signal:controller.signal});requireValue(response.ok,'WORKFLOW_PACKAGE_FETCH',`Workflow package fetch failed with HTTP ${response.status}`);
    return await readBoundedResponse(response,REMOTE_PACKAGE_LIMIT);
  }catch(error){if(timedOut)throw Object.assign(new Error('Remote Workflow package fetch exceeded the Host deadline'),{code:'WORKFLOW_PACKAGE_FETCH_TIMEOUT',cause:error});throw error;}
  finally{clearTimeout(timer);}
}

async function readWorkflowPackageFile(args){
  requireValue(typeof args.package_path==='string'&&args.package_path.trim(),'WORKFLOW_PACKAGE_FILE','package_path must name one local Workflow package JSON file');
  let path;
  if(isAbsolute(args.package_path))path=resolve(args.package_path);
  else{
    requireValue(typeof args.workspace==='string'&&isAbsolute(args.workspace),'WORKFLOW_PACKAGE_WORKSPACE','A relative package_path requires an absolute workspace');
    const workspace=resolve(args.workspace);path=resolve(workspace,args.package_path);insideRoot(workspace,path);
  }
  await noSymlinks(path);
  const before=await lstat(path);
  requireValue(before.isFile()&&before.nlink===1&&before.size>0&&before.size<=REMOTE_PACKAGE_LIMIT,'WORKFLOW_PACKAGE_FILE','Local Workflow package must be one bounded regular file');
  const bytes=await readFile(path),after=await lstat(path);
  requireValue(bytes.length===before.size&&after.size===before.size&&after.mtimeMs===before.mtimeMs,'WORKFLOW_PACKAGE_FILE_CHANGED','Local Workflow package changed while being read');
  if(args.expected_sha256)requireValue(digest(bytes)===args.expected_sha256,'WORKFLOW_PACKAGE_FETCH_INTEGRITY','Local Workflow package differs from the expected digest');
  return {bytes,path};
}

function inventorySelection(service, args) {
  requireValue(args.discovery === undefined || ['folders','host'].includes(args.discovery), 'SKILL_DISCOVERY_MODE', 'Discovery mode must be folders or host');
  const mode = args.discovery ?? (args.workspace ? 'host' : 'folders');
  if (mode === 'host') {
    requireValue(typeof args.workspace === 'string' && isAbsolute(args.workspace), 'SKILL_DISCOVERY_WORKSPACE', 'Host discovery requires an absolute workspace');
    return {inventory:service.skillInventory, path:args.workspace};
  }
  return {inventory:service.folderInventory,path:args.folder};
}

async function recoverControllerTree(coordinator, strictManager, runtime, args, { configPath }) {
  const recovered = await adoptRunTree(runtime, args.run_id, args, (id, state) => {
    for (const [nodeId, node] of Object.entries(state.nodes)) for (const attempt of node.attempts)
      if (attempt.child_run_id) coordinator.admission.registerChild(id, attempt.child_run_id, nodeId, attempt.id);
    coordinator.fenceRun(id);
  });
  await replaceOwnedAuthority(runtime,recovered.run);
  const errors = [...recovered.errors];
  const recoveredAuthorities = [...recovered.authorities];
  const stopped = await Promise.allSettled(recoveredAuthorities.map(async ([id, authority]) => {
    await Promise.all([
      strictManager.stopRecovered(id, authority),
      waitForDetachedHostMainStop(configPath, id),
    ]);
    return id;
  }));
  stopped.forEach((result, index) => { if (result.status === 'rejected') errors.push({ run_id: recoveredAuthorities[index][0], code: result.reason.code ?? 'RECOVERY_CLEANUP_FAILED', message: result.reason.message }); });
  try {
    try { await coordinator.waitDrain(args.run_id); } catch { /* The exact recovery drain retries a failed cleanup. */ }
    await coordinator.drainRun(args.run_id, new Set(), { cancelChildren: false });
    for (const [id] of recoveredAuthorities) { coordinator.jobs.delete(id); coordinator.errors.delete(id); }
  } catch (error) { errors.push({ run_id: args.run_id, code: error.code ?? 'RUN_EXECUTION_STOP_INCOMPLETE', message: error.message }); }
  await runtime.runs.mutate(args.run_id, 'control_recovery', state => { requireValue(state.control_hash === digest(recovered.run.control_token), 'RUN_AUTHORITY', 'Another controller recovery replaced this controller during cleanup'); state.control_recovery.errors = errors; });
  return { ...await runtime.get(args.run_id), control_token: recovered.run.control_token, recovery_errors: errors,
    stopped_run_ids: stopped.filter(result => result.status === 'fulfilled').map(result => result.value) };
}

async function resumeDetachedHostMain(service, runtime, args, state) {
  const worker = await readHostMainWorker(service.configPath, args.run_id);
  if (!worker || state.status !== 'running') return state;
  if (['running', 'starting'].includes(worker.phase)) {
    return { ...state, execution_owner: 'host_main_worker', host_worker: worker,
      next_action: 'workflow_wait', next_action_args: { run_id: args.run_id, control_token: args.control_token, timeout_ms: WORKFLOW_WAIT_MS } };
  }
  const confirmedAuthorityRevocation = worker.termination?.confirmed === true
    && worker.termination.reason === 'authority_revoked';
  requireValue(confirmedAuthorityRevocation && worker.phase === 'stopped',
  'HOST_MAIN_RESTART_UNSAFE',
  `Detached Host Main cannot restart from ${worker.phase}: inspect its terminal evidence first`);
  await runtime.authorizeController(args.run_id, { control_token: args.control_token });
  const launched = await (service.capabilities.launchDetachedHostMain ?? launchDetachedHostMain)({
    configPath: service.configPath, defaultConfigPath: service.defaultConfigPath,
    runId: args.run_id, controlToken: args.control_token, owner: state.main_actor, env: service.env,
  });
  return { ...state, execution_owner: 'host_main_worker', host_worker: launched,
    next_action: 'workflow_wait', next_action_args: { run_id: args.run_id, control_token: args.control_token, timeout_ms: WORKFLOW_WAIT_MS } };
}

async function purgeManagedAuthoringWorkspace(configPath, runId, actualWorkspace, { allowMissing = false } = {}) {
  const root=resolve(join(dirname(configPath),'skill-generation-workspaces'));
  const expected=insideRoot(root,join(root,'job-'+workflowId(runId)));
  requireValue(resolve(actualWorkspace)===expected,'AUTHORING_WORKSPACE_OWNERSHIP','Accepted authoring cleanup only removes its exact Host-owned workspace');
  try {
    await noSymlinks(expected);const info=await lstat(expected);
    requireValue(info.isDirectory()&&!info.isSymbolicLink(),'AUTHORING_WORKSPACE_OWNERSHIP','Authoring workspace must be one exact owned directory');
    await rm(expected,{recursive:true,maxRetries:3,retryDelay:100});
    return {purged:true};
  } catch(error) {
    if(allowMissing&&error.code==='ENOENT')return {purged:false,missing:true};
    throw error;
  }
}

function authoringCleanupRecord(record,deployed,controlToken){
  requireDeployableConvertedSnapshot(deployed);
  const provenance=record.pins.root.provenance,runId=record.state.run_id,finalId=record.pins.root.workflow.finalization?.node_id;
  const node=record.state.nodes[finalId],attempt=node?.attempts.find(item=>item.id===node.active_attempt_id)??node?.attempts.at(-1),acceptance=attempt?.automatic_completion??attempt?.human_acceptance;
  requireValue(record.state.status==='succeeded'&&isAuthoringRunProvenance(provenance)&&attempt?.status==='succeeded','RUN_PURGE_STATE','Cleanup requires one succeeded accepted authoring Run');
  requireValue(acceptance?.review_result_sha256===attempt.result_proposal?.sha256
    &&acceptance.proposal_hash===deployed.provenance?.conversion?.proposal_hash
    &&acceptance.source_revision===provenance.source_revision
    &&deployed.workflow.id===provenance.source_workflow_id
    &&deployed.provenance?.kind==='workflow_conversion'
    &&deployed.provenance.conversion?.source_revision===provenance.source_revision,
  'AUTHORING_PURGE_DEPLOYMENT','Cleanup requires the exact accepted proposal, reviewer result and source-free deployment identity');
  requireValue(record.state.control_hash===digest(controlToken),'RUN_AUTHORITY','Cleanup authority differs from the accepted authoring Run');
  return {identity:{run_id:runId,control_hash:record.state.control_hash,source_workflow_id:provenance.source_workflow_id,source_revision:provenance.source_revision,
    proposal_hash:acceptance.proposal_hash,review_result_sha256:acceptance.review_result_sha256,deployed_revision:deployed.revision_hash,
    ...(attempt.automatic_completion?{completion_policy:structuredClone(provenance.completion_policy)}:{}),
    authoring_workflow_id:record.pins.root.workflow.id,authoring_revision:record.pins.root.revision_hash},
    targets:{workspace:record.state.permissions.workspace,job_workflow_id:record.pins.root.workflow.id,job_revision:record.pins.root.revision_hash}};
}

async function requireNoActiveSiblingAuthoringRun(runtime,identity){
  const terminal=new Set(['succeeded','failed','cancelled']);
  for(const item of await runtime.runs.list()){
    if(item.run_id===identity.run_id||terminal.has(item.status))continue;
    const sibling=await runtime.runs.read(item.run_id),provenance=sibling.pins.root.provenance;
    requireValue(!(isAuthoringRunProvenance(provenance)&&provenance.source_workflow_id===identity.source_workflow_id),
      'AUTHORING_CLEANUP_CONFLICT','Another unfinished authoring Run still owns history in the private source Workflow Pack',{conflicting_run_id:item.run_id,conflicting_source_revision:provenance?.source_revision});
  }
}

async function continueAcceptedAuthoringCleanup({configPath,store,runtime,context,journal,deployed,service}){
  requireDeployableConvertedSnapshot({...deployed,resourceBytes:await store.resources(deployed.workflow.id,deployed.revision_hash)});const {identity,targets}=journal;
  requireValue(deployed.workflow.id===identity.source_workflow_id&&deployed.revision_hash===identity.deployed_revision
    &&deployed.provenance?.conversion?.proposal_hash===identity.proposal_hash,'AUTHORING_CLEANUP_IDENTITY','Deployed Workflow changed after cleanup intent was recorded');
  const jobs=await new WorkflowStore(join(dirname(configPath),'workflow-expansion-jobs'),{validationContext:context}).initialize();
  try{
    await requireNoActiveSiblingAuthoringRun(runtime,identity);
    if(!journal.steps.siblings&&(targets.siblings??[]).length){
      requireValue(service,'AUTHORING_CLEANUP_OWNER','Sibling cleanup requires its Host manager owner');
      for(const sibling of targets.siblings){
        await Promise.all([service.strictManager.stopRun(sibling.run_id),service.managedNativeManager.stopRun(sibling.run_id),service.hostMainManager.stopRun(sibling.run_id)]);
        await runtime.runs.purge(sibling.run_id,{expected_workflow_id:sibling.job_workflow_id,expected_revision:sibling.job_revision,
          expected_source_workflow_id:identity.source_workflow_id,expected_source_revision:identity.source_revision,allow_missing:true,terminal_authoring:true});
        await purgeManagedAuthoringWorkspace(configPath,sibling.run_id,sibling.workspace,{allowMissing:true});
        await jobs.purge(sibling.job_workflow_id,sibling.job_revision,{expected_provenance_kind:'authoring_workflow_run',allow_missing:true});
      }
      journal=await store.markAuthoringCleanup(identity.source_workflow_id,identity.run_id,identity,'siblings');
    }
    if(!journal.steps.library){await store.resumeHistoryPurge(identity.source_workflow_id,identity.deployed_revision,
      {beforePurge:()=>requireNoActiveSiblingAuthoringRun(runtime,identity)});journal=await store.markAuthoringCleanup(identity.source_workflow_id,identity.run_id,identity,'library');}
    if(!journal.steps.workspace){await purgeManagedAuthoringWorkspace(configPath,identity.run_id,targets.workspace,{allowMissing:true});journal=await store.markAuthoringCleanup(identity.source_workflow_id,identity.run_id,identity,'workspace');}
    if(!journal.steps.job){await jobs.purge(targets.job_workflow_id,targets.job_revision,{expected_provenance_kind:'authoring_workflow_run',allow_missing:true});journal=await store.markAuthoringCleanup(identity.source_workflow_id,identity.run_id,identity,'job');}
    if(!journal.steps.run){await runtime.runs.purge(identity.run_id,{expected_workflow_id:identity.authoring_workflow_id,expected_revision:identity.authoring_revision,
      expected_source_workflow_id:identity.source_workflow_id,expected_source_revision:identity.source_revision,allow_missing:true});journal=await store.markAuthoringCleanup(identity.source_workflow_id,identity.run_id,identity,'run');}
    return {private_authoring_artifacts_purged:journal.status==='complete',cleanup_transaction:{run_id:identity.run_id,status:journal.status,steps:journal.steps}};
  }catch(cause){
    throw Object.assign(new Error(`Source-free Workflow ${deployed.workflow.id}@${deployed.revision_hash} was committed, but exact private authoring cleanup did not finish: ${cause.message}`),{
      code:'AUTHORING_PURGE_INCOMPLETE',deployed_workflow_id:deployed.workflow.id,deployed_revision:deployed.revision_hash,cause_code:cause.code ?? 'UNKNOWN',cause,
    });
  }
}

async function beginAcceptedAuthoringCleanup(options){
  requireDeployableConvertedSnapshot({...options.deployed,resourceBytes:await options.store.resources(options.deployed.workflow.id,options.deployed.revision_hash)});
  const prepared=authoringCleanupRecord(options.record,options.deployed,options.controlToken);
  prepared.targets.siblings=[];
  for(const item of await options.runtime.runs.list()){
    if(item.run_id===prepared.identity.run_id)continue;
    const sibling=await options.runtime.runs.read(item.run_id),provenance=sibling.pins.root.provenance;
    if(!isAuthoringRunProvenance(provenance)||provenance.source_workflow_id!==prepared.identity.source_workflow_id||provenance.source_revision!==prepared.identity.source_revision)continue;
    prepared.targets.siblings.push({run_id:item.run_id,workspace:sibling.state.permissions.workspace,job_workflow_id:sibling.pins.root.workflow.id,job_revision:sibling.pins.root.revision_hash});
  }
  const journal=await options.store.beginAuthoringCleanup(prepared.identity.source_workflow_id,prepared);
  return continueAcceptedAuthoringCleanup({...options,journal});
}

export class WorkflowService {
  constructor({ configPath, defaultConfigPath, env = process.env, fetchImpl = globalThis.fetch, registry, capabilities = {} }) {
    const invocationTransport=workflowMcpTransport(env);
    Object.defineProperties(this,{
      invocationTransport:{value:invocationTransport,enumerable:true},
      invocationAdapters:{value:workflowInvocationAdapters(invocationTransport)},
    });
    this.configPath = resolve(configPath); this.defaultConfigPath = defaultConfigPath; this.env = env; this.fetchImpl = fetchImpl;
    this.registry = registry ?? connectorRegistryFor({ configPath: this.configPath, env });
    // Built-in host contracts are part of the control plane, not an optional
    // server decoration. CLI helpers, validation scripts and the web console
    // must therefore observe the same launch/validation context.
    this.capabilities = { ...capabilities, hostToolRegistry: {...authoringHostToolRegistry(),...workflowResourceProgramRegistry(),...(capabilities.hostToolRegistry ?? {})} };
    this.attemptAdmission = capabilities.attemptAdmission ?? attemptAdmissionFor(this.configPath);
    this.strictManager = capabilities.strictManager ?? strictManagerFor({ configPath: this.configPath, getConfig: () => this.config(), env });
    this.managedNativeManager = capabilities.managedNativeManager ?? managedNativeManagerFor({ configPath: this.configPath, getConfig: () => this.config(), env });
    this.hostMainManager = capabilities.hostMainManager ?? hostMainManagerFor({ configPath: this.configPath, getConfig: () => this.config(), env,
      hostToolRunner:capabilities.hostToolRunner??new HostToolRunner({registry:this.capabilities.hostToolRegistry,env}) });
    this.historyMaintenance = runHistoryMaintenanceFor({ runRoot: join(dirname(this.configPath), 'workflow-runs') });
    this.parallelManager = capabilities.parallelManager ?? parallelManagerFor({ configPath: this.configPath, env });
    const nativeAgentObserverSession=capabilities.nativeAgentObserverSession
      ?? (action=>withNativeAgentObserver(action,{env:this.env}));
    this.nativeAgentObserver = Object.hasOwn(capabilities,'nativeAgentObserver') ? capabilities.nativeAgentObserver
      : (agentIds,options)=>nativeAgentObserverSession(client=>inspectNativeAgents(client,agentIds,{...options,waitForTerminal:true}));
    this.nativeMainSelection=capabilities.nativeMainSelection??(record=>resolveMainModelSelection(record,{}, {env:this.env,observe:nativeAgentObserverSession}));
    this.nativeParentVerifier=capabilities.nativeParentVerifier??(parent=>withNativeAgentObserver(client=>inspectNativeParent(client,parent),{env:this.env}));
    this.nativeParentAgentPaths=new Map();
    this.folderInventory = new SkillInventory(folder => discoverFolderSkills(folder, {env}));
    this.skillInventory = capabilities.skillInventory ?? new SkillInventory(async workspace => discoverCodexSkills(workspace, { config: await this.config(), env }));
  }
  async nativeParentAgentPath(record){
    const parent=nativeParentThreadId(record.state);
    if(this.nativeParentAgentPaths.has(parent))return this.nativeParentAgentPaths.get(parent);
    const verified=await this.nativeParentVerifier(parent);
    const path=verified?.agent_path??'/root';
    requireValue(path==='/root'||path.startsWith('/root/'),'NATIVE_AGENT_IDENTITY_SCHEMA','Verified native parent has no canonical Agent path');
    this.nativeParentAgentPaths.set(parent,path);return path;
  }
  async persistModelSpawnWindow(runtime,args,record,binding,packet){
    const parentPath=await this.nativeParentAgentPath(record);
    const spawns=[];
    for(const item of packet.packets){
      const taskName=item.spawn_config?.task_name;
      requireValue(typeof taskName==='string'&&/^[a-z0-9_]{1,64}$/.test(taskName),
        'NATIVE_AGENT_SPAWN_INTENT','Native packet needs a Host-generated task name');
      await runtime.recordNativeExecutorEvent(args.run_id,{...binding,control_token:args.control_token,
        event:{kind:'native_agent_spawn_intent',metadata:{index:item.index,task_name:taskName,
          agent_id:`${parentPath}/${taskName}`}}});
      spawns.push({index:item.index,task_name:taskName,agent_id:`${parentPath}/${taskName}`});
    }
    packet.batch_id=await runtime.publishNativeSpawnBatch(args.run_id,{...binding,control_token:args.control_token,
      spawns:spawns.sort((a,b)=>a.index-b.index)});
    return packet;
  }
  async config() { return loadConfig({ configPath: this.configPath, defaultConfigPath: this.defaultConfigPath }); }
  async prepareCodexRegistration(closure) {
    const config = await this.config();
    const strict = closure.packs.some(pack => pack.workflow.skill_policy.mode === 'strict');
    // Strict qualification is a launch policy. Cooperative SDK registration
    // belongs to the exact manager execution route, after preceding native,
    // tool or conversation work has actually reached that worker.
    if (!strict || this.capabilities.strictManager) return;
    await refreshCodexRegistration({ configPath: this.configPath, defaultConfigPath: this.defaultConfigPath, config,
      env: this.env, strict, qualify: this.capabilities.codexRegistrationQualifier,
      discover: this.capabilities.codexRegistrationDiscovery });
  }
  async inspectNativeAgents(runtime,args,definition,attempt,agentIds,{signal,beforeWait}={}) {
    const afterTurnIds={},rejectedTurnIds={},textAmendments={};let parentThreadId;
    const checkActive=async()=>{
      if(signal?.aborted)throw Object.assign(new Error('Native Agent wait was cancelled by its caller'),{code:'NATIVE_AGENT_WAIT_CANCELLED'});
      assertExecutionAttemptAdmission(this.configPath,args.run_id,definition.id,attempt.id);
      const fresh=await runtime.runs.readNativeWaitState(args.run_id),node=fresh.state.nodes[definition.id];
      const current=node?.attempts.find(item=>item.id===attempt.id);
      requireValue(fresh.state.status==='running'&&node?.active_attempt_id===attempt.id&&
        ['claimed','running'].includes(node.status)&&['claimed','running'].includes(current?.status)&&
        (current.lease_generation??0)===(attempt.lease_generation??0)&&fresh.state.control_hash===digest(args.control_token),
      'NATIVE_AGENT_ATTEMPT_CHANGED','Native Agent authority changed while Host waited for a child');
      const currentParent=nativeParentThreadId(fresh.state);
      requireValue(parentThreadId===undefined||parentThreadId===currentParent,'NATIVE_AGENT_ATTEMPT_CHANGED','Native parent identity changed while Host waited for a child');
      parentThreadId=currentParent;
      if(definition.fanout?.item_delivery==='incremental')for(const item of Object.values(current.native_latest_turns??{}))
        if(typeof item.turn_id==='string'&&item.turn_id)afterTurnIds[item.agent_id]=item.turn_id;
      for(const turns of Object.values(nativeRejectedTurnHistory(fresh,definition.id,attempt.id))){
        const last=turns.at(-1);if(!afterTurnIds[last.agent_id])afterTurnIds[last.agent_id]=last.turn_id;
        rejectedTurnIds[last.agent_id]=turns.map(item=>item.turn_id);
      }
      for(const [index,rejection]of Object.entries(current.native_rejected_turns??{})){
        const followup=current.native_repair_followups?.[`${index}:${rejection.count}`];
        if(followup?.text_repair_ref&&(!definition.fanout||!current.native_item_results?.[followup.item_indices[0]]))textAmendments[followup.agent_id]=true;
      }
    };
    const onIdentityEvent=async metadata=>{
      // Terminal siblings are inspected without waiting for their checkers.
      // Before the observer enters a lifecycle wait, publish every already
      // admitted result so a repairing child cannot hide a ready sibling.
      if(metadata.status==='waiting_native_event')await beforeWait?.();
      signal?.throwIfAborted();
      await runtime.recordNativeExecutorEvent(args.run_id,{node_id:definition.id,attempt_id:attempt.id,control_token:args.control_token,
        lease_token:leaseToken(args.control_token,args.run_id,definition.id,attempt.id,attempt.lease_generation??0),
        event:{kind:'session_state',metadata}});
    };
    // One duplicate terminal projection can race the rejected-turn journal. A
    // second one-shot inspection is bounded and never waits for a running turn.
    for(let inspection=0;inspection<2;inspection++){
      await checkActive();
      const observed=await this.nativeAgentObserver(agentIds,{parentThreadId,afterTurnIds,rejectedTurnIds,checkActive,onIdentityEvent,
        resultSchema:nativeAgentResultSchema(definition),perItemResult:definition.fanout?.result_mode==='per_item',textAmendments,signal,
        runJournalPath:join(runtime.runs.directory(args.run_id),'events.jsonl')});
      await checkActive();
      requireValue(observed?.status!=='pending','NATIVE_AGENT_OBSERVER_PROTOCOL',
        'Native Agent observer returned a polling continuation instead of holding the Host event wait');
      requireValue(agentIds.includes(observed?.agent_id),'NATIVE_AGENT_IDENTITY','Observed native Agent is not in this dispatch');
      requireValue(typeof observed.turn_id==='string'&&observed.turn_id.length>0,
        'NATIVE_AGENT_OBSERVATION','Host observer must identify the exact terminal native turn');
      if(textAmendments[observed.agent_id])requireValue(observed.status==='amendment','NATIVE_TEXT_AMENDMENT','The acknowledged text repair requires an exact amendment payload; a full result or invalid/blocked turn cannot replace it');
      if(definition.completion_contract?.host_check)await runtime.recordNativeUsage(args.run_id,{node_id:definition.id,attempt_id:attempt.id,control_token:args.control_token,
        lease_token:leaseToken(args.control_token,args.run_id,definition.id,attempt.id,attempt.lease_generation??0),request_id:attempt.dispatch.request_id,usage:{unknown:true}});
      if(['completed','blocked'].includes(observed.status)&&observed.result_shape)await onIdentityEvent({status:'native_result_shape',
        code:'NATIVE_AGENT_RESULT_SHAPE',
        diagnostic:`Native Agent ${observed.agent_id} turn ${observed.turn_id} returned ${observed.result_shape}`+
          (observed.normalization?`; Host removed ${observed.normalization.syntax_repairs} impossible closing delimiter(s)`+
            (observed.normalization.host_projected?' and projected the declared per-item result from its envelope':''):'' )});
      if(!rejectedTurnIds[observed.agent_id]?.includes(observed.turn_id))return observed;
    }
    requireValue(false,'NATIVE_AGENT_OBSERVER_REPLAY','Native Agent observer repeated only already rejected terminal turns');
  }
  async mergeObservedNativeAmendment(runtime,args,{definition,attempt,binding,index,observed}){
    const {record}=await runtime.authorizedExecution(args.run_id,{...binding,control_token:args.control_token},()=>binding);
    const current=record.state.nodes[definition.id].attempts.find(item=>item.id===attempt.id),rejection=current.native_rejected_turns?.[index];
    const followup=current.native_repair_followups?.[`${index}:${rejection?.count}`],ref=followup?.text_repair_ref;
    requireValue(ref&&rejection.agent_id===observed.agent_id&&followup.agent_id===observed.agent_id
      &&current.native_agents?.[index]===observed.agent_id&&observed.turn_id!==rejection.turn_id,
      'NATIVE_TEXT_AMENDMENT_BINDING','Amendment needs the acknowledged repair for its exact child and a new terminal turn');
    const repair=await readNativeTextRepair(runtime,args.run_id,{...binding,control_token:args.control_token},ref);
    requireValue(repair.snapshot.native_observation.turn_id===rejection.turn_id&&repair.snapshot.native_observation.index===index
      &&repair.snapshot.native_observation.agent_id===observed.agent_id&&(!definition.fanout||unresolvedNativeItemTargets(record,definition,current,index).length===1
        &&unresolvedNativeItemTargets(record,definition,current,index)[0]===repair.snapshot.item_index),
      'NATIVE_TEXT_AMENDMENT_BINDING','Amendment baseline differs from the rejected turn or current unresolved item');
    const {raw_ref,merged_ref,merged,mergeError}=await runtime.runs.withHostTransaction(args.run_id,'native_prepare',async()=>{
      const raw_ref=await runtime.runs.saveExecutorResult(args.run_id,attempt.id,{kind:'native_text_amendment',native_observation:{index,agent_id:observed.agent_id,turn_id:observed.turn_id},text_repair_ref:ref,payload:observed.amendment});
      let merged,mergeError;
      try{merged=applyTextAmendment(repair.baseline,repair.snapshot.scope,repair.config,observed.amendment);validateData(merged,definition.fanout?definition.outputs_schema.properties[definition.fanout.result_output].items:definition.outputs_schema);}
      catch(error){mergeError=error;}
      const merged_ref=mergeError?null:await runtime.runs.saveExecutorResult(args.run_id,attempt.id,{kind:'native_text_merged_proposal',raw_ref,text_repair_ref:ref,output:merged});
      // Keep the error as data until the existing failed raw trace is committed.
      return {raw_ref,merged_ref,merged,mergeError};
    });
    await runtime.recordNativeTextAmendment(args.run_id,{...binding,control_token:args.control_token,index,agent_id:observed.agent_id,turn_id:observed.turn_id,text_repair_ref:ref,raw_ref,merged_ref,
      ...(mergeError?{error:{code:mergeError.code??'NATIVE_TEXT_AMENDMENT',message:mergeError.message.slice(0,3900)}}:{})});
    if(mergeError)throw mergeError;
    return {...observed,status:'completed',result:definition.fanout?{items:[{outcome:'completed',result:merged}]}:merged,result_shape:'host_merged_text_amendment'};
  }
  async #nativeSpanHandoff(runtime,args,record,definition,lease,dispatched,maxPromptChars,indices,options){
    const plan=resolvedSubagentPlan(definition,record.state);
    const attempt=record.state.nodes[definition.id].attempts.find(item=>item.id===lease.attempt_id),pending=attempt?.native_pending_followup;
    if(record.pins.native_dispatch_span_version===1&&pending){
      const selectedIndices=Array.isArray(indices)?indices:[indices],index=selectedIndices[0];
      requireValue(selectedIndices.length===1&&index===pending.index,'NATIVE_AGENT_FOLLOWUP_CHANGED',
        'Published follow-up reuse requires its exact single recorded partition');
      const inherited=new Set(attempt.inherited_native_item_indices??[]);
      const unresolved=definition.fanout?assignedFanoutIndices(plan,definition.fanout,index)
        .filter(item=>!inherited.has(item)&&!attempt.native_item_results?.[item]):null;
      let selected=null,directory;
      const root=join(dispatched.envelope.workspace,'work','.workflow-runtime','native-agent',args.run_id,attempt.id,`partition-${index}`);
      if(pending.followup_kind==='repair'){
        requireValue(options?.bundleSegment===`repair-${pending.rejection_count}`&&(!definition.fanout||
          canonicalJSON(options?.itemPositionOverrides?.[index])===canonicalJSON(unresolved)),
          'NATIVE_AGENT_FOLLOWUP_CHANGED','Published repair reuse differs from its exact unresolved-item selection');
        selected=definition.fanout?.item_delivery==='incremental'?unresolved.slice(0,1):unresolved;
        directory=join(root,options.bundleSegment);
      }else{
        requireValue(pending.followup_kind==='incremental'&&definition.fanout?.item_delivery==='incremental'
          &&options?.bundleSegment==null&&unresolved.length>0,'NATIVE_AGENT_FOLLOWUP_CHANGED',
          'Published continuation reuse requires its exact incremental delivery route');
        selected=unresolved.slice(0,1);directory=join(root,`item-${selected[0]}`);
      }
      requireValue((selected?.[0]??null)===pending.item_index,'NATIVE_AGENT_FOLLOWUP_CHANGED',
        'Published follow-up reuse differs from its exact first unresolved item');
      const packet=await reuseNativeSpanPublication(runtime,record,definition,{...lease,control_token:args.control_token},dispatched,plan,
        {pending,task_bundle_path:join(directory,'task.json')});
      return nativeAgentHandoff(record,definition,lease,{...dispatched,materialized_packets:{[index]:{
        ...packet,item_positions:selected,assigned_items:selected?.map(item=>plan.items[item])??null}}},maxPromptChars,index);
    }
    return materializeWithNativeSpan(runtime,record,definition,{...lease,control_token:args.control_token},dispatched,
      plan,()=>materializedNativeAgentHandoff(record,definition,lease,dispatched,maxPromptChars,indices,options));
  }
  async #nativeRepairFollowup(runtime,args,{record,definition,attempt,binding,index,agentId,turnId,category,reason,
    rejectionCount,executor,maxPromptChars}) {
    const assigned=definition.fanout?.result_mode==='per_item'
      ?assignedFanoutIndices(resolvedSubagentPlan(definition,record.state),definition.fanout,index):[];
    const stored=attempt.native_item_results??{};
    const acceptedItemIndices=assigned.filter(itemIndex=>stored[itemIndex]?.agent_id===agentId);
    const unresolvedItemIndices=assigned.filter(itemIndex=>!stored[itemIndex]);
    if(attempt.native_pending_followup)requireValue((!definition.fanout||unresolvedItemIndices.length>0)&&executor,'NATIVE_AGENT_FOLLOWUP_CHANGED',
    'Pending repair follow-up lost its exact unresolved item or native executor');
    const repairRemaining=definition.retry.max_attempts-rejectionCount;
    requireValue(repairRemaining>0,'NATIVE_AGENT_REPAIR_EXHAUSTED',
      `Native Agent ${agentId} exhausted the pinned ${definition.retry.max_attempts}-turn limit: ${reason}`);
    const diagnosticRef=attempt.native_rejected_turns?.[index]?.diagnostic_ref;
    if(diagnosticRef){const stored=await runtime.runs.readExecutorResult(args.run_id,attempt.id,diagnosticRef.sha256);
      requireValue(stored?.kind==='native_rejection_diagnostic'&&stored.agent_id===agentId&&stored.turn_id===turnId,'NATIVE_AGENT_REJECTION_CONFLICT','Full repair diagnostic differs from its exact rejected child turn');reason=stored.reason;}
    let repairPrompt=`Rejected result: ${reason}. Return the Result schema from the initial packet.`,repairPacket=null;
    const textRepairRef=attempt.native_rejected_turns?.[index]?.text_repair_ref;
    const textRepair=textRepairRef?await readNativeTextRepair(runtime,args.run_id,{...binding,control_token:args.control_token},textRepairRef):null;
    if((!definition.fanout&&definition.completion_contract?.host_check||definition.fanout?.result_mode==='per_item'&&unresolvedItemIndices.length)&&executor){
      const prepared=await executor.prepare(args.run_id,{...binding,control_token:args.control_token});
      requireValue(digest(canonicalJSON(prepared))===attempt.dispatch.envelope_hash,
        'NATIVE_AGENT_HANDOFF_CHANGED','The repair handoff no longer matches its pinned dispatch intent');
      const config=maxPromptChars===undefined?await this.config():null;
      const dispatched={...prepared,handoff_required:true,compiled_prompt:prepared.prompt,request_id:attempt.dispatch.request_id};
      const handoff=await this.#nativeSpanHandoff(runtime,args,record,definition,binding,dispatched,
        maxPromptChars??config.global.max_prompt_chars,index,{resourceRoot:join(runtime.runs.directory(args.run_id),'objects'),
          ...(definition.fanout?{itemPositionOverrides:{[index]:unresolvedItemIndices}}:{}),bundleSegment:`repair-${rejectionCount}`});
      requireValue(handoff.packets.length===1&&handoff.packets[0].index===index,
        'NATIVE_AGENT_FOLLOWUP','Per-item repair must materialize exactly one recorded Agent packet');
      repairPacket=handoff.packets[0];
      // This exact child already owns its original task and every delivered
      // incremental item. Keep the full repair bundle and intent Host-side;
      // resend only the diagnostic and the changed ordered return selection.
      if(definition.fanout?.result_mode==='per_item'){
        const incremental=definition.fanout.item_delivery==='incremental';
        const inherited=new Set(attempt.inherited_native_item_indices??[]);
        const originalAssigned=assigned.filter(itemIndex=>!inherited.has(itemIndex));
        const selected=incremental?unresolvedItemIndices.slice(0,1):unresolvedItemIndices;
        const selection=incremental?'the current supplied item'
          :`initial assignment positions ${canonicalJSON(selected.map(itemIndex=>originalAssigned.indexOf(itemIndex)+1))} (one-based)`;
        repairPrompt=`Rejected result: ${reason}\nReturn exactly ${selected.length} ordered items for ${selection}. `
          +'Use the original semantic item schema with this return envelope: {"items":[{"outcome":"completed","result":<semantic item>}]} '
          +'or a blocked entry with block_reason. '
          +(definition.fanout.shared_change_field?`A delegated entry remains allowed for ${definition.fanout.shared_change_field} work owned by the downstream shared-write owner. `:'')
          +'The Host retained accepted siblings. Return only the selected entries without IDs, positions, paths, hashes, tokens or receipts.';
      }
      if(textRepair)repairPrompt=`Rejected result: ${reason}\nRevise only the sealed prior text using 1-based inclusive physical-line edits. Each selected line includes its separator. Replacement is exact text; nonempty non-EOF replacement must end in CRLF, LF or CR. Empty replacement deletes selected lines. Preserve all unrelated content. Return only this amendment JSON, without a full result, hashes or receipts.\nAllowed field/line scope: ${canonicalJSON(textRepair.snapshot.scope)}\nAmendment schema: ${canonicalJSON(textAmendmentSchema(textRepair.config))}`;
      requireValue(repairPrompt.length<=200000,'CODEX_INPUT_LIMIT','Full native Host correction exceeds the actual 200000-character turn input bound');
      const intent={index,agent_id:agentId,item_index:unresolvedItemIndices[0]??null,task_bundle_sha256:repairPacket.task_bundle_sha256,
        followup_kind:'repair',rejection_count:rejectionCount,...(textRepairRef?{text_repair_ref:textRepairRef}:{})};
      if(attempt.native_pending_followup){
        requireValue(canonicalJSON(attempt.native_pending_followup)===canonicalJSON(intent),
          'NATIVE_AGENT_FOLLOWUP_CHANGED','Pending repair follow-up no longer matches its exact rejected turn and packet');
      }else {const metadata={...intent};delete metadata.text_repair_ref;if(textRepairRef)metadata.text_repair_sha256=textRepairRef.sha256;
        await runtime.recordNativeExecutorEvent(args.run_id,{...binding,control_token:args.control_token,
        event:{kind:'native_agent_followup_intent',metadata}});}
    }else if(definition.fanout?.result_mode==='per_item')repairPrompt+=unresolvedItemIndices.length
      ?' Repair only the unresolved entries from the prior turn, in original partition order; the Host retained every accepted sibling.'
      :' return {"items":[]}.';
    requireValue(repairPrompt.length<=200000,'CODEX_INPUT_LIMIT','Full native Host correction exceeds the actual 200000-character turn input bound');
    return {status:category==='blocked'?'native_agent_blocked':'native_agent_invalid_result',run_id:args.run_id,
      node_id:definition.id,attempt_id:attempt.id,index,agent_id:agentId,turn_id:turnId,reason,repair_remaining:repairRemaining,
      repair_prompt:repairPrompt,...(repairPacket&&definition.fanout?{item_index:unresolvedItemIndices[0]}:{}),
      ...(definition.fanout?.result_mode==='per_item'?{unresolved_item_indices:unresolvedItemIndices,accepted_item_indices:acceptedItemIndices}:{}),
      ...(repairPacket?{followup_config:{target:agentId,message:repairPrompt},
        next_action_args:{run_id:args.run_id,control_token:args.control_token}}:{}),next_action:'repair_recorded_agent'};
  }
  async rejectedNativeOutcome(runtime,args,{definition,attempt,binding,index,observed,category,reason,executor,textCheck}) {
    await runtime.recordNativeUsage(args.run_id,{...binding,control_token:args.control_token,request_id:attempt.dispatch.request_id,usage:{unknown:true}});
    let text_repair_ref;
    if(textCheck&&definition.completion_contract.host_check.text_amendment){
      const repair=await nativeTextRepairSnapshot(runtime,args.run_id,{...binding,control_token:args.control_token},textCheck.reference);
      text_repair_ref=await runtime.runs.saveExecutorResult(args.run_id,attempt.id,repair.snapshot);
    }
    const recorded=await runtime.recordNativeRejectedTurn(args.run_id,{...binding,control_token:args.control_token,
      index,agent_id:observed.agent_id,turn_id:observed.turn_id,category,reason,...(text_repair_ref?{text_repair_ref}:{})});
    if(!recorded.new)return null;
    const fresh=await runtime.runs.read(args.run_id);
    const node=fresh.state.nodes[definition.id];
    const currentAttempt=node.attempts.find(item=>item.id===attempt.id);
    let unresolvedItemIndices=[],acceptedItemIndices=[];
    if(definition.fanout?.result_mode==='per_item'){
      const assigned=assignedFanoutIndices(resolvedSubagentPlan(definition,fresh.state),definition.fanout,index);
      const stored=currentAttempt.native_item_results??{};
      acceptedItemIndices=assigned.filter(itemIndex=>stored[itemIndex]?.agent_id===observed.agent_id);
      unresolvedItemIndices=assigned.filter(itemIndex=>!stored[itemIndex]);
    }
    const rejected=nativeRejectedTurnHistory(fresh,definition.id,attempt.id);
    // Explicit node retries have their own budget and inherit already accepted
    // per-item results. A closed attempt must not consume the fresh attempt's
    // same-Agent correction allowance.
    const consumed=Math.max(1,rejected[index]?.length??0);
    if(definition.retry.max_attempts-consumed<=0){
      const error={code:'NATIVE_AGENT_REPAIR_EXHAUSTED',message:`Native Agent ${observed.agent_id} exhausted the pinned ${definition.retry.max_attempts}-turn limit: ${reason.slice(0,3900)}`};
      const completedIds=new Set([
        ...(currentAttempt.native_serial_results??[]).map(item=>item.agent_id),
        ...Object.values(currentAttempt.native_parallel_results??{}).map(item=>item.agent_id),
      ]);
      const outstandingAgentIds=Object.values(currentAttempt.native_agents??{}).filter(id=>id!==observed.agent_id&&!completedIds.has(id));
      await runtime.failNode(args.run_id,{...binding,error});
      return {status:'native_agent_repair_exhausted',run_id:args.run_id,node_id:definition.id,attempt_id:attempt.id,
        index,agent_id:observed.agent_id,turn_id:observed.turn_id,reason,error,
        completion_satisfied:false,recovery_required:true,
        ...(definition.fanout?.result_mode==='per_item'?{unresolved_item_indices:unresolvedItemIndices,accepted_item_indices:acceptedItemIndices}:{}),
        outstanding_agent_ids:outstandingAgentIds,
        ...(outstandingAgentIds.length?{controller_cleanup:{tool:'collaboration.interrupt_agent',agent_ids:outstandingAgentIds}}:{}),
        next_action:null};
    }
    return this.#nativeRepairFollowup(runtime,args,{record:fresh,definition,attempt:currentAttempt,binding,index,
      agentId:observed.agent_id,turnId:observed.turn_id,category,reason,rejectionCount:recorded.count,executor});
  }
  async preflightObservedNativeCompletion(runtime,args,{record,definition,attempt,binding,index,observed,target_indices=[]}) {
    const native_observation={index,agent_id:observed.agent_id,turn_id:observed.turn_id};
    preflightNativeHostCompletion(record,definition,attempt,{result:observed.result,target_indices,native_observation});
    await runtime.recordNativeExecutorEvent(args.run_id,{...binding,control_token:args.control_token,event:{kind:'session_state',metadata:{
      status:'native_render_preflight',code:'NATIVE_RENDER_PREFLIGHT',
      diagnostic:`Size preflight validated durable native_agents slot ${index}, Agent ${observed.agent_id}, observed turn ${observed.turn_id}; dispatch receipt ${attempt.dispatch.receipt?'sealed':'not yet sealed'}`}}});
  }
  async prepareObservedNativeItems(runtime,args,{definition,attempt,binding,index,observed,size_reservations={}}) {
    return runtime.runs.withHostTransaction(args.run_id,'native_prepare',async()=>{
      const fresh=await runtime.runs.read(args.run_id);
      const current=fresh.state.nodes[definition.id].attempts.find(item=>item.id===attempt.id);
      const targets=unresolvedNativeItemTargets(fresh,definition,current,index);
      if(definition.completion_contract?.host_check){
        validateData(observed.result,nativeAgentResultSchema(definition,targets.length));
        // These extra products reserve size only. Live authority and unresolved
        // targets still come from the original guarded Run projection.
        const sizing={...current,native_item_results:{...size_reservations,...current.native_item_results}};
        await this.preflightObservedNativeCompletion(runtime,args,{record:fresh,definition,attempt:sizing,binding,index,observed,target_indices:targets});
      }
      return targets;
    });
  }
  async recordObservedNativeItems(runtime,args,{definition,attempt,binding,index,observed,executor,record_terminal_turn=false,prepared_targets,defer_admission=false}) {
    let recorded;const hostRejections=new Map(),textChecks=new Map();
    const rejected=async error=>{
      if(error.native_host_check_failure||!['DATA_INVALID','NATIVE_ITEM_INDEX','NATIVE_ITEM_DUPLICATE','NATIVE_ITEM_RESULT_CONFLICT','NATIVE_ITEM_RESULT'].includes(error.code))throw error;
      const rejection=await this.rejectedNativeOutcome(runtime,args,{definition,attempt,binding,index,observed,executor,
        category:'invalid',reason:error.message});return rejection?{rejection}:{retry:true};
    };
    let targets,host_checks,admissionResult;
    try{
      targets=prepared_targets??await this.prepareObservedNativeItems(runtime,args,{definition,attempt,binding,index,observed});
      host_checks={};admissionResult=structuredClone(observed.result);
      if(definition.completion_contract?.host_check){
        for(const [local,item_index]of targets.entries()){
          const item=observed.result.items[local];
          if(!nativeItemHasSemanticResult(definition,item))continue;
          validateData(item.result,definition.outputs_schema.properties[definition.fanout.result_output].items);
          const checked=await executor.executeNativeHostCheck(args.run_id,{...binding,control_token:args.control_token},item.result,
            {item_index,native_observation:{index,agent_id:observed.agent_id,turn_id:observed.turn_id}});
          if(!checked.accepted){
            const diagnostic=`Host completion check rejected this proposal.\n${checked.diagnostic}`;
            hostRejections.set(item_index,diagnostic);
            textChecks.set(item_index,checked);
            // Preserve accepted siblings while this exact item remains unaccepted.
            // Journal summaries are bounded; the repair below uses the full typed diagnostic.
            admissionResult.items[local]={outcome:'blocked',block_reason:diagnostic.slice(0,3900)};
            continue;
          }
          host_checks[item_index]=checked.reference;
        }
      }
    }catch(error){return rejected(error);}
    const admit=async()=>{
    try{
      recorded=await runtime.runs.withHostTransaction(args.run_id,'native_prepare',async()=>{
        const accepted=await runtime.recordNativeItemResults(args.run_id,{...binding,control_token:args.control_token,
          index,agent_id:observed.agent_id,turn_id:observed.turn_id,
          target_indices:targets,result:admissionResult,host_checks});
        if(!accepted.unresolved_item_indices.length&&!accepted.issues.length){
          const resultArgs={...binding,control_token:args.control_token,index,agent_id:observed.agent_id,result:accepted.result,
            ...(record_terminal_turn?{turn_id:observed.turn_id}:{})};
          if(definition.fanout.scheduling==='serial')await runtime.recordNativeSerialResult(args.run_id,resultArgs);
          else await runtime.recordNativeParallelResult(args.run_id,resultArgs);
        }
        return accepted;
      });
    }
    catch(error){return rejected(error);}
    if(definition.fanout?.item_delivery==='incremental'&&!recorded.issues.length&&recorded.unresolved_item_indices.length)
      return {continuation:true,accepted_item_indices:recorded.accepted_item_indices,
        unresolved_item_indices:recorded.unresolved_item_indices};
    if(recorded.unresolved_item_indices.length||recorded.issues.length){
      const reason=recorded.issues.map(issue=>`item ${issue.item_index}: ${hostRejections.get(issue.item_index)??issue.reason}`).join('; ');
      const rejection=await this.rejectedNativeOutcome(runtime,args,{definition,attempt,binding,index,observed,executor,
        category:hostRejections.size||recorded.issues.some(issue=>issue.category==='invalid')?'invalid':'blocked',reason,
        ...(textChecks.size===1?{textCheck:[...textChecks.values()][0]}:{})});return rejection?{rejection}:{retry:true};
    }
    return {result:recorded.result};
    };
    return defer_admission?{admit,rejected:hostRejections.size>0||admissionResult.items.some(item=>!nativeItemHasSemanticResult(definition,item))}:admit();
  }
  parallelNativeItemCollection(record,definition,pending) {
    if(pending.length<2||definition.fanout?.scheduling!=='parallel'||definition.fanout.result_mode!=='per_item'
      ||definition.fanout.item_delivery==='incremental'||definition.fanout.shared_change_field
      ||!definition.fanout.workspace_field||!definition.completion_contract?.host_check)return false;
    const plan=resolvedSubagentPlan(definition,record.state),roots=pending.flatMap(([index])=>
      assignedFanoutIndices(plan,definition.fanout,Number(index)).map(item=>resolve(nodeWorkspace(definition.id,record.state,record.pins),plan.items[item][definition.fanout.workspace_field])));
    const contains=(a,b)=>{const path=relative(a,b);return !path||path!=='..'&&!path.startsWith(`..${process.platform==='win32'?'\\':'/'}`)&&!isAbsolute(path);};
    return roots.every((root,index)=>roots.every((other,position)=>index===position||!contains(root,other)&&!contains(other,root)));
  }
  async collectObservedNativeItems(runtime,args,{record,definition,attempt,binding,pending,executor,signal,record_terminal_turn=false}) {
    const waiting=new AbortController(),jobs=[],completed=[],size_reservations={};
    let stopped=false,originalError,inspectionError,admissionError,admissionOutcome,terminal,commits=Promise.resolve();
    const abort=()=>waiting.abort(signal.reason);
    if(signal?.aborted)abort();else signal?.addEventListener('abort',abort,{once:true});
    const stop=()=>{stopped=true;waiting.abort();};
    const remaining=new Map(pending.slice(0,definition.fanout.max_concurrency??32));
    try{
      // One observer connection belongs to the public drive. Inspect it in
      // order while independent item-local checker operations run outside
      // every Host transaction; only admission/repair publication is deferred.
      while(remaining.size&&!stopped){
        let observed;
        try{observed=await this.inspectNativeAgents(runtime,args,definition,attempt,[...remaining.values()],{
          signal:waiting.signal,beforeWait:()=>commits});}
        catch(error){if(stopped&&!signal?.aborted)break;throw error;}
        if(stopped)break;
        const found=[...remaining].find(([,id])=>id===observed.agent_id);
        requireValue(found,'NATIVE_AGENT_IDENTITY','Observed native Agent is not in this active dispatch');
        const index=Number(found[0]);remaining.delete(found[0]);
        if(observed.status==='amendment')observed=await this.mergeObservedNativeAmendment(runtime,args,{definition,attempt,binding,index,observed});
        if(observed.status==='blocked'||observed.status==='invalid'){terminal={index,observed};stop();break;}
        requireValue(observed.status==='completed','NATIVE_AGENT_OBSERVATION','Host observer did not return a completed Agent');
        let prepared_targets;
        try{prepared_targets=await this.prepareObservedNativeItems(runtime,args,{definition,attempt,binding,index,observed,size_reservations});}
        catch(error){if(error.code!=='DATA_INVALID')throw error;
          terminal={index,observed:{...observed,status:'invalid',reason:error.message}};stop();break;}
        if(stopped)break;
        for(const [local,item_index]of prepared_targets.entries())if(nativeItemHasSemanticResult(definition,observed.result.items[local]))
          size_reservations[item_index]={result:observed.result.items[local].result};
        const job={index,observed};jobs.push(job);
        job.promise=this.recordObservedNativeItems(runtime,args,{definition,attempt,binding,index,observed,executor,record_terminal_turn,
          prepared_targets,defer_admission:true}).then(value=>{job.value=value;if(value.rejected||value.rejection||value.retry)stop();},error=>{
          originalError??=error;stop();});
        // Keep publication in admission order, but do not hold a ready
        // sibling's durable result behind another child's lifecycle wait.
        commits=commits.then(async()=>{
          await job.promise;
          if(originalError||admissionError||job.value?.rejected)return;
          const accepted=job.value.admit?await job.value.admit():job.value;
          if(accepted.rejection||accepted.retry){admissionOutcome??=accepted.rejection??{native_continue:true};stop();return;}
          completed.push({agent_id:job.observed.agent_id,result:accepted.result});
        }).catch(error=>{admissionError??=error;stop();});
      }
    }catch(error){inspectionError=error;stop();}
    finally{
      // No observer/checker operation may outlive the public connection owner,
      // including a failure arriving during the next sibling inspection.
      await Promise.all(jobs.map(job=>job.promise));
      await commits;
      signal?.removeEventListener('abort',abort);
    }
    if(originalError)throw originalError;
    if(admissionError)throw admissionError;
    signal?.throwIfAborted();
    if(inspectionError)throw inspectionError;
    if(admissionOutcome)return {outcome:admissionOutcome,completed};
    // All admitted checks have settled before one exact-child correction is
    // published. A second rejection keeps its receipt for the next drive.
    const rejected=jobs.find(job=>job.value.rejected);
    if(rejected){const accepted=await rejected.value.admit();return {outcome:accepted.rejection??{native_continue:true},completed};}
    if(terminal){const outcome=await this.rejectedNativeOutcome(runtime,args,{definition,attempt,binding,executor,...terminal,
      category:terminal.observed.status,reason:terminal.observed.reason});return {outcome:outcome??{native_continue:true},completed};}
    return {outcome:{native_continue:true},completed};
  }
  async #incrementalNativeContinuation(runtime,args,{record,definition,attempt,binding,index,agentId,turnId,
    status='native_item_accepted',maxPromptChars,executor}) {
    const lease={run_id:args.run_id,node_id:definition.id,attempt_id:attempt.id,lease_token:binding.lease_token};
    const assigned=assignedFanoutIndices(resolvedSubagentPlan(definition,record.state),definition.fanout,index);
    const acceptedIndices=assigned.filter(itemIndex=>Boolean(attempt.native_item_results?.[itemIndex]));
    const unresolvedIndices=assigned.filter(itemIndex=>!attempt.native_item_results?.[itemIndex]);
    const nextItem=unresolvedIndices[0];
    requireValue(Number.isSafeInteger(nextItem),'NATIVE_AGENT_FOLLOWUP','Incremental native continuation needs one unresolved item');
    const nextPrepared=await executor.prepare(args.run_id,{...lease,control_token:args.control_token});
    requireValue(digest(canonicalJSON(nextPrepared))===attempt.dispatch.envelope_hash,
      'NATIVE_AGENT_HANDOFF_CHANGED','The incremental native handoff no longer matches its pinned dispatch intent');
    const nextPacket=await this.#nativeSpanHandoff(runtime,args,record,definition,lease,{...nextPrepared,
      handoff_required:true,compiled_prompt:nextPrepared.prompt,request_id:attempt.dispatch.request_id},
      maxPromptChars,index,{resourceRoot:join(runtime.runs.directory(args.run_id),'objects')});
    requireValue(nextPacket.packets.length===1&&nextPacket.packets[0].index===index,
      'NATIVE_AGENT_FOLLOWUP','Incremental native continuation must materialize exactly one recorded Agent packet');
    const packet=nextPacket.packets[0];
    const intent={index,agent_id:agentId,item_index:nextItem,task_bundle_sha256:packet.task_bundle_sha256,
      followup_kind:'incremental',rejection_count:0};
    if(attempt.native_pending_followup){
      requireValue(canonicalJSON(attempt.native_pending_followup)===canonicalJSON(intent),
        'NATIVE_AGENT_FOLLOWUP_CHANGED','Pending incremental follow-up no longer matches its exact recorded packet');
    }else await runtime.recordNativeExecutorEvent(args.run_id,{...lease,control_token:args.control_token,
      event:{kind:'native_agent_followup_intent',metadata:intent}});
    return {status,run_id:args.run_id,node_id:definition.id,attempt_id:attempt.id,index,item_index:nextItem,agent_id:agentId,
      ...(turnId?{turn_id:turnId}:{}),accepted_item_indices:acceptedIndices,unresolved_item_indices:unresolvedIndices,
      next_action:'continue_recorded_agent',followup_config:{target:agentId,message:packet.prompt},
      next_action_args:{run_id:args.run_id,control_token:args.control_token}};
  }
  async #resumeNativeFollowup(runtime,args,{record,definition,attempt,binding,executor,maxPromptChars}){
    const pending=attempt.native_pending_followup;
    if(pending){
      if(pending.followup_kind==='incremental')return this.#incrementalNativeContinuation(runtime,args,{
        record,definition,attempt,binding,index:pending.index,agentId:pending.agent_id,
        turnId:attempt.native_latest_turns?.[pending.index]?.turn_id,
        status:'native_item_continuation_pending',maxPromptChars,executor});
      requireValue(pending.followup_kind==='repair','NATIVE_AGENT_FOLLOWUP','Unknown pending native follow-up kind');
      const rejection=attempt.native_rejected_turns?.[pending.index];
      const turns=nativeRejectedTurnHistory(record,definition.id,attempt.id)[pending.index]??[];
      const rejectedTurn=turns.at(-1);
      requireValue(rejection?.agent_id===pending.agent_id&&rejection.count===pending.rejection_count&&
        turns.length===pending.rejection_count&&rejectedTurn&&rejectedTurn.agent_id===pending.agent_id&&
        rejection.turn_id===rejectedTurn.turn_id&&rejection.category===rejectedTurn.category&&rejection.reason===rejectedTurn.reason,
      'NATIVE_AGENT_FOLLOWUP_CHANGED','Pending repair follow-up no longer matches the persisted rejected turn history');
      return this.#nativeRepairFollowup(runtime,args,{record,definition,attempt,binding,index:pending.index,
        agentId:pending.agent_id,turnId:rejectedTurn.turn_id,category:rejectedTurn.category,reason:rejectedTurn.reason,
        rejectionCount:pending.rejection_count,executor,maxPromptChars});
    }
    if(definition.fanout?.item_delivery!=='incremental')return null;
    const plan=resolvedSubagentPlan(definition,record.state);
    for(const [slot,agentId]of Object.entries(attempt.native_agents??{})){
      const index=Number(slot),assigned=assignedFanoutIndices(plan,definition.fanout,index);
      const accepted=assigned.filter(itemIndex=>Boolean(attempt.native_item_results?.[itemIndex]));
      const nextItem=assigned.find(itemIndex=>!attempt.native_item_results?.[itemIndex]);
      // Repair receipts snapshot the full unresolved tail; incremental packets deliver only its first item.
      const rejectionCount=attempt.native_rejected_turns?.[index]?.count;
      const repairReceipt=Number.isSafeInteger(rejectionCount)
        ?attempt.native_repair_followups?.[`${index}:${rejectionCount}`]:null;
      const repairAwaitingObservation=Number.isSafeInteger(nextItem)&&repairReceipt?.agent_id===agentId&&
        repairReceipt.item_indices?.[0]===nextItem;
      if(accepted.length&&Number.isSafeInteger(nextItem)&&!attempt.native_followups?.[nextItem]&&!repairAwaitingObservation)
        return this.#incrementalNativeContinuation(runtime,args,{record,definition,attempt,binding,index,agentId,
          turnId:attempt.native_latest_turns?.[index]?.turn_id,status:'native_item_continuation_pending',maxPromptChars,executor});
    }
    return null;
  }
  async completeObservedNative(runtime,args,{record,definition,attempt,binding,executor,signal,maxPromptChars}) {
    requireValue(this.nativeAgentObserver,'NATIVE_AGENT_OBSERVER_REQUIRED','Native Agent execution requires the Host lifecycle observer');
    const continuation=await this.#resumeNativeFollowup(runtime,args,{record,definition,attempt,binding,executor,maxPromptChars});
    if(continuation)return continuation;
    const activeSlots=activeNativeAssignmentSlots(record,definition,attempt);
    const agentIds=activeSlots.map(index=>attempt.native_agents?.[index]);
    const recorded=definition.fanout?.scheduling==='serial'?(attempt.native_serial_results??[])
      :definition.fanout?.max_concurrency
        ?activeSlots.map(index=>attempt.native_parallel_results?.[index]):null;
    let results=recorded;
    if(!results){
      const completed=new Map(Object.values(attempt.native_parallel_results??{}).map(item=>[item.agent_id,item]));
      const pending=new Set(agentIds.filter(id=>!completed.has(id)));
      while(pending.size){
        const assignments=activeSlots.map((index,position)=>[String(index),agentIds[position]]).filter(([,id])=>pending.has(id));
        if(this.parallelNativeItemCollection(record,definition,assignments)){
          const collected=await this.collectObservedNativeItems(runtime,args,{record,definition,attempt,binding,pending:assignments,executor,signal});
          for(const item of collected.completed){completed.set(item.agent_id,item);pending.delete(item.agent_id);}
          if(!collected.outcome.native_continue)return collected.outcome;
          continue;
        }
        let observed=await this.inspectNativeAgents(runtime,args,definition,attempt,[...pending],{signal});
        requireValue(pending.has(observed.agent_id),'NATIVE_AGENT_IDENTITY','Observed native Agent is not in this dispatch');
        if(observed.status==='amendment')observed=await this.mergeObservedNativeAmendment(runtime,args,{definition,attempt,binding,index:activeSlots[agentIds.indexOf(observed.agent_id)],observed});
        if(observed.status==='blocked'||observed.status==='invalid'){
          const activePosition=agentIds.indexOf(observed.agent_id);
          const rejection=await this.rejectedNativeOutcome(runtime,args,{definition,attempt,binding,executor,
            index:activeSlots[activePosition],observed,category:observed.status,reason:observed.reason});
          if(rejection)return rejection;continue;
        }
        requireValue(observed.status==='completed','NATIVE_AGENT_OBSERVATION','Host observer did not return a completed Agent');
        if(definition.fanout?.result_mode==='per_item'){
          const index=activeSlots[agentIds.indexOf(observed.agent_id)];
          const accepted=await this.recordObservedNativeItems(runtime,args,{definition,attempt,binding,index,observed,executor});
          if(accepted.rejection)return accepted.rejection;
          if(accepted.retry)continue;
          if(accepted.continuation){
            const fresh=await runtime.runs.read(args.run_id);
            const currentAttempt=fresh.state.nodes[definition.id].attempts.find(item=>item.id===attempt.id);
            return this.#incrementalNativeContinuation(runtime,args,{record:fresh,definition,attempt:currentAttempt,binding,
              index,agentId:observed.agent_id,turnId:observed.turn_id,maxPromptChars,executor});
          }
          completed.set(observed.agent_id,{agent_id:observed.agent_id,result:accepted.result});pending.delete(observed.agent_id);
          continue;
        }
        try { validateData(observed.result,definition.fanout
          ?definition.outputs_schema.properties[definition.fanout.result_output].items:definition.outputs_schema); }
        catch(error){if(error.code!=='DATA_INVALID')throw error;
          const rejection=await this.rejectedNativeOutcome(runtime,args,{definition,attempt,binding,executor,index:activeSlots[agentIds.indexOf(observed.agent_id)],
            observed,category:'invalid',reason:error.message});if(rejection)return rejection;continue;}
        let host_check;
        if(definition.completion_contract?.host_check){
          const index=activeSlots[agentIds.indexOf(observed.agent_id)];
          const fresh=await runtime.runs.read(args.run_id),current=fresh.state.nodes[definition.id].attempts.find(item=>item.id===attempt.id);
          await this.preflightObservedNativeCompletion(runtime,args,{record:fresh,definition,attempt:current,binding,index,observed});
          const checked=await executor.executeNativeHostCheck(args.run_id,{...binding,control_token:args.control_token},observed.result,
            {native_observation:{index,agent_id:observed.agent_id,turn_id:observed.turn_id}});
          if(!checked.accepted){const rejection=await this.rejectedNativeOutcome(runtime,args,{definition,attempt,binding,index,observed,executor,category:'invalid',reason:`Host completion check rejected this proposal.\n${checked.diagnostic}`,textCheck:checked});
            if(rejection)return rejection;continue;}
          host_check=checked.reference;
        }
        if(definition.fanout)await runtime.recordNativeParallelResult(args.run_id,{...binding,control_token:args.control_token,
          index:activeSlots[agentIds.indexOf(observed.agent_id)],agent_id:observed.agent_id,result:observed.result});
        completed.set(observed.agent_id,{agent_id:observed.agent_id,result:observed.result,...(host_check?{host_check}:{})});pending.delete(observed.agent_id);
      }
      results=agentIds.map(id=>completed.get(id));
    }
    return this.#completeNativeDispatch(runtime,{...args,attempt_id:attempt.id,results,usage:{unknown:true}});
  }
  async #completeNativeDispatch(runtime,args){
    const {record,definition,attempt,binding}=await nativeAttemptBinding(runtime,args);
    const receipt=attempt?.dispatch?.receipt;
    requireValue(receipt?.executor==='codex-native-subagent','NATIVE_AGENT_RECEIPT',
      'The Host must seal the exact observed native Agent identities before completion');
    const activeSlots=activeNativeAssignmentSlots(record,definition,attempt);
    const results=definition.fanout?.scheduling==='serial'?(attempt.native_serial_results??[]):definition.fanout?.max_concurrency
      ?activeSlots.map(index=>attempt.native_parallel_results?.[index]):args.results;
    requireValue(Array.isArray(results)&&results.length===receipt.agent_ids.length&&
      results.every((item,index)=>item?.agent_id===receipt.agent_ids[index]),
      'NATIVE_AGENT_RESULT','Native results must match the recorded Agent IDs in dispatch order');
    let itemResults;
    if(definition.fanout?.result_mode==='per_item'){
      const plan=resolvedSubagentPlan(definition,record.state);
      itemResults=Array.from({length:plan.items.length},(_,index)=>{
        const accepted=attempt.native_item_results?.[index];
        requireValue(accepted,'NATIVE_ITEM_RESULT',`Input item ${index} has no journaled accepted result`);
        return accepted.result;
      });
    }
    let checkedChanges=[];
    if(definition.completion_contract?.host_check){
      const refs=definition.fanout?Object.values(attempt.native_item_results).map(item=>item.host_check):[results[0].host_check];
      checkedChanges=[...new Set(refs.flatMap(ref=>workerHostCheckEffectPaths(record,definition.id,ref,nodeWorkspace(definition.id,record.state,record.pins))))].sort();
    }
    const span=await settleNativeSpan(runtime,record,definition,attempt,binding,resolvedSubagentPlan(definition,record.state));
    if(span)checkedChanges=[...new Set([...checkedChanges,...span.changed_paths])].sort();
    const completion=nativeAgentCompletion(definition,receipt,results,{...args,item_results:itemResults,
      ...(definition.completion_contract?.host_check||span?{changed_paths:checkedChanges,artifacts:checkedChanges}:{})});
    if(span)completion.evidence.push({kind:'native_dispatch_span',reference:span.reference});
    if(definition.completion_contract?.host_check&&!definition.fanout)completion.evidence.push({kind:'worker_host_check',reference:results[0].host_check});
    if(definition.fanout)await runtime.recordCooperativeNativeResults(args.run_id,{...binding,
      results:results.map((item,index)=>({dispatch_id:item.agent_id,agent_id:item.agent_id,
        result_index:index,result_sha256:digest(canonicalJSON(item.result))}))});
    await runtime.recordNativeUsage(args.run_id,{...binding,request_id:attempt.dispatch.request_id,usage:args.usage??{unknown:true}});
    const state=await runtime.completeNode(args.run_id,{...binding,completion});
    if(span)await releaseNativeSpanOwner(runtime,record,definition,{...attempt,native_dispatch_span:{...attempt.native_dispatch_span,settled_ref:span.reference}});
    return {run_id:args.run_id,node_id:binding.node_id,status:state.status,
      ...(state.status==='running'?nativeContinuation(args.run_id,args.control_token):{next_action:null})};
  }
  async #sealNativeDispatch(runtime,args,{executor,signal,maxPromptChars}){
    const sealed=await runtime.runs.withHostTransaction(args.run_id,'native_prepare',async()=>{
    const {record,definition,attempt,binding}=await nativeAttemptBinding(runtime,args);
    const activeSlots=activeNativeAssignmentSlots(record,definition,attempt),count=activeSlots.length;
    const agentIds=activeSlots.map(index=>attempt.native_agents?.[index]);
    requireValue(agentIds.every(id=>typeof id==='string'&&id.length>0),'NATIVE_AGENT_SPAWN_MISSING',
      'Every Host-planned native Agent must be journaled before sealing its dispatch');
    if(definition.fanout?.scheduling==='serial')requireValue((attempt.native_serial_results??[]).length===count,
      'NATIVE_AGENT_SERIAL_RESULT','Every serial sub-Agent must have a Host-observed validated result before sealing');
    if(definition.fanout?.max_concurrency)requireValue(Object.keys(attempt.native_parallel_results??{}).length===count,
      'NATIVE_AGENT_PARALLEL_RESULT','Every capped parallel sub-Agent must have a Host-observed validated result before sealing');
    const receipt=nativeAgentReceipt(definition,record.state,args.attempt_id,agentIds);
    requireValue(attempt?.dispatch?.request_id,'DISPATCH_INTENT_MISSING','Native Agent completion requires the Host-persisted dispatch intent');
    await runtime.recordNativeDispatchReceipt(args.run_id,{...binding,request_id:attempt.dispatch.request_id,receipt});
    const fresh=await runtime.runs.read(args.run_id);
    const current=fresh.state.nodes[definition.id].attempts.find(item=>item.id===attempt.id);
    return {record:fresh,definition,attempt:current,binding};
    });
    return this.completeObservedNative(runtime,args,{...sealed,executor,signal,maxPromptChars});
  }
  async ensureAuthoringWorkflows(store,config,routingRules=null){
    routingRules??=await loadRoutingSettings(dirname(this.configPath),config.providers);
    return ensureStoredAuthoringWorkflows(store,{providers:config.providers,routingRules});
  }
  async resumeAutomaticAuthoring(args,{store,runtime,context}) {
    // The Run can already be purged when Ready persistence or journal writing
    // fails. Locate only this exact Run's durable receipt, never a name match.
    let journal,workflowId=args.workflow_id;
    if(workflowId)journal=await store.readAuthoringCleanup(workflowId,args.run_id);
    else for(const pack of await store.list()){
      const candidate=await store.readAuthoringCleanup(pack.workflow.id,args.run_id);
      if(candidate){requireValue(!journal,'AUTHORING_COMPLETION_CONFLICT','Multiple completion journals claim this exact Run');journal=candidate;workflowId=pack.workflow.id;}
    }
    if(journal?.identity.completion_policy?.mode!=='automatic')return null;
    requireValue(journal.identity.control_hash===digest(args.control_token),'RUN_AUTHORITY','Automatic completion retry requires its retained exact controller authority');
    if(args.preview_identity)requireValue(args.preview_identity.proposal_hash===journal.identity.proposal_hash
      &&args.preview_identity.source_revision===journal.identity.source_revision
      &&args.preview_identity.review_result_sha256===journal.identity.review_result_sha256,'AUTHORING_PREVIEW_CHANGED',
      'Displayed proposal or reviewer result differs from the exact retained completion receipt');
    const retryArgs={...args,workflow_id:workflowId};
    if(journal.status!=='complete'){
      const deployed=await store.snapshot(workflowId,journal.identity.deployed_revision);
      await this.preflightAutomaticAuthoring(retryArgs,{store,context,deployed});
      await Promise.all([this.strictManager.stopRun(args.run_id),this.managedNativeManager.stopRun(args.run_id),this.hostMainManager.stopRun(args.run_id)]);
      await continueAcceptedAuthoringCleanup({configPath:this.configPath,store,runtime,context,journal,deployed,service:this});
    }
    return this.finishAutomaticAuthoring(retryArgs,{store,runtime,context});
  }

  async preflightAutomaticAuthoring(args,{store,context,deployed}) {
    requireDeployableConvertedSnapshot({...deployed,resourceBytes:await store.resources(deployed.workflow.id,deployed.revision_hash)});
    requireCurrentConversionCertificate(deployed.workflow,deployed.resources,deployed.import_report,{required:true,provenance:deployed.provenance});
    const workflow={...publishableEditorWorkflow(deployed.workflow),status:'ready',enabled:true};
    const checked=await this.validationContext(store,workflow,context);
    requireValue(checked.validation.launch_ready===true,'WORKFLOW_NOT_READY','Automatic authoring completion did not pass launch readiness',
      {validation:checked.validation,workflow_id:deployed.workflow.id,run_id:args.run_id,deployed_revision:deployed.revision_hash,stage:'automatic_completion_preflight'});
    return {workflow,checked};
  }

  async finishAutomaticAuthoring(args,{store,runtime,context}) {
    const journal=await store.readAuthoringCleanup(args.workflow_id,args.run_id);
    requireValue(journal?.status==='complete'&&journal.identity.control_hash===digest(args.control_token)
      &&journal.identity.completion_policy?.mode==='automatic','AUTHORING_COMPLETION_REQUIRED','Ready completion requires exact finished cleanup and pinned automatic authority');
    const identity=journal.identity;
    let deployed=await store.snapshot(args.workflow_id);
    const alreadyReady=deployed.workflow.status==='ready'&&deployed.workflow.enabled===true
      &&deployed.provenance?.authoring_completion?.receipt_hash===digest(canonicalJSON(identity))
      &&deployed.provenance.authoring_completion.workflow_sha256===digest(canonicalJSON(deployed.workflow))
      &&deployed.provenance.authoring_completion.resources_sha256===digest(canonicalJSON(deployed.resources));
    requireValue(alreadyReady||deployed.revision_hash===identity.deployed_revision,'AUTHORING_CLEANUP_IDENTITY','Deployed Workflow changed before Ready completion');
    const {workflow,checked}=await this.preflightAutomaticAuthoring(args,{store,context,deployed});
    if(!alreadyReady){
      store.validationContext=checked.context;
      deployed=await store.save(args.workflow_id,workflow,{expected_revision:identity.deployed_revision,
        import_report:certificateForPublishedWorkflow({...deployed,workflow}),
        provenance:{...deployed.provenance,authoring_completion:{kind:'host_automatic_completion',receipt_hash:digest(canonicalJSON(identity)),completion_policy:structuredClone(identity.completion_policy),review_result_sha256:identity.review_result_sha256,workflow_sha256:digest(canonicalJSON({...workflow,revision:deployed.workflow.revision+1})),resources_sha256:digest(canonicalJSON(deployed.resources)),completed_at:new Date().toISOString()}}});
    }
    requireValue(!journal.ready_revision||journal.ready_revision===deployed.revision_hash,'AUTHORING_COMPLETION_CONFLICT','Completed authoring journal identifies a different Ready revision');
    await store.markAuthoringCompletion(args.workflow_id,args.run_id,identity,deployed.revision_hash);
    return {...deployed,phase:'completed',status:'succeeded',validation:checked.validation,
      authoring_cleanup:{private_authoring_artifacts_purged:true,cleanup_transaction:{run_id:args.run_id,status:'complete',steps:journal.steps}}};
  }

  async completeAuthoringResult(args,{store,runtime,context}) {
    const resumed=await this.resumeAutomaticAuthoring(args,{store,runtime,context});if(resumed)return resumed;
    const record=await runtime.runs.read(args.run_id),provenance=record.pins.root.provenance;
    requireValue(automaticAuthoringCompletion(provenance),'AUTHORING_AUTOMATIC_COMPLETION_REQUIRED','Automatic completion was not pinned for this authoring Run');
    const nodeId=record.pins.root.workflow.finalization.node_id,node=record.state.nodes[nodeId],attempt=node?.attempts.find(item=>item.id===node.active_attempt_id);
    await runtime.completeAuthoringAutomatically(args.run_id,{...args,node_id:nodeId,attempt_id:attempt?.id,
      lease_token:leaseToken(args.control_token,args.run_id,nodeId,attempt?.id,attempt?.lease_generation??0)});
    return this.applyAcceptedAuthoringResult({...args,workflow_id:provenance.source_workflow_id,expected_revision:provenance.source_revision},{store,runtime,context,automatic:true});
  }

  async applyAcceptedAuthoringResult(args,{store,runtime,context,automatic=false}) {
        const state = await runtime.authorizeController(args.run_id, args);
        requireValue(state.status === 'succeeded', 'EXPANSION_ACCEPTANCE_REQUIRED', 'Expansion Run needs main-controller acceptance before applying its proposal');
        const record = await runtime.runs.read(args.run_id); const {pins}=record,provenance = pins.root.provenance;
        requireValue(isAuthoringRunProvenance(provenance) && provenance.source_workflow_id === args.workflow_id && provenance.source_revision === args.expected_revision,
          'EXPANSION_RESULT_IDENTITY', 'Expansion result belongs to a different source Workflow revision');
        if(!automatic)requireValue(!automaticAuthoringCompletion(provenance),'AUTHORING_AUTOMATIC_COMPLETION_REQUIRED','Run-pinned automatic completion cannot be applied through the human Draft route');
        requireValue(provenance.review_contract_version===CONVERSION_CONTRACT.version,'CONVERSION_REVIEW_CONTRACT_STALE','Historical authoring Runs remain readable but must be rerun under the current conversion contract before mutation');
        const final=state.nodes.final;const attempt=final.attempts.find(a=>a.id===final.active_attempt_id);
        const acceptance=automatic?attempt?.automatic_completion:attempt?.human_acceptance;
        if(automatic)requireValue(automaticAuthoringCompletion(provenance)&&acceptance?.actor==='host'&&canonicalJSON(acceptance?.completion_policy)===canonicalJSON(provenance.completion_policy),'AUTHORING_COMPLETION_POLICY','Host completion receipt must match the pinned automatic policy');
        const reviewIdentity=authoringReviewIdentity(record),acceptedIdentity=acceptance?{proposal_hash:acceptance.proposal_hash,source_revision:acceptance.source_revision,expand_attempt_id:acceptance.expand_attempt_id}:null;
        requireValue(attempt?.result_proposal && acceptance?.review_result_sha256===attempt.result_proposal.sha256 && canonicalJSON(acceptedIdentity)===canonicalJSON(reviewIdentity),'GENERATION_REVIEW_BLOCKED','A durable authorized receipt for this exact proposal and checklist review is required');
        let deployed=await store.snapshot(args.workflow_id);
        const alreadyCommitted=deployed.provenance?.kind==='workflow_conversion'
          &&deployed.provenance.conversion?.source_revision===args.expected_revision
          &&deployed.provenance.conversion?.proposal_hash===reviewIdentity.proposal_hash;
        if(!alreadyCommitted){
          requireValue(deployed.revision_hash===args.expected_revision,'REVISION_CONFLICT','Source Workflow changed before accepted conversion deployment');
          const resources=await store.resources(args.workflow_id,args.expected_revision);
          const expansionContext={...context,routing_rules:provenance.routing_rules,routing_catalog:provenance.routing_catalog};
          const validated=validateGenerationProposal(state.nodes.expand.output,{pack:deployed,resources,provenance,context:expansionContext,previousPlan:record.state.generation_repair?.previous_proposal ?? null,repairFeedback:record.state.generation_repair?.feedback ?? null});
          requireValue(validated.compiled.workflow.import_status.conversion_level!=='unsupported','CONVERSION_UNSUPPORTED','Unsupported source semantics cannot cross the deployable Workflow boundary');
          const completion=await runtime.runs.readExecutorResult(args.run_id,attempt.id,attempt.result_proposal.sha256);
          const review=evaluateReview(completion.structured_output,validated.proposal,resources,{version:CONVERSION_CONTRACT.version});
          requireValue(review.approved&&review.findings.length===0,'GENERATION_REVIEW_BLOCKED','Checklist findings remain unresolved');
          deployed=await applyExpansion(store,args.workflow_id,validated.proposal,{expected_revision:args.expected_revision,
            context:expansionContext,inference_confirmation:automatic?'The Host completion policy and independent review receipt authorize this exact proposal.':'The authenticated Workbench acceptance is bound to this exact proposal and checklist review.',
            conversion_review_contract_version:CONVERSION_CONTRACT.version,...(automatic?{inference_authority:'host',inference_receipt:acceptance}:{})});
        } else if(automatic&&deployed.workflow.status==='draft') {
          // A preflight can fail after committing the reviewed Draft but before
          // cleanup starts. Reproject the same accepted artifact under corrected
          // Host observation rules, without invoking models or overwriting edits.
          const sourcePack=await store.snapshot(args.workflow_id,args.expected_revision);
          const resources=await store.resources(args.workflow_id,args.expected_revision);
          const expansionContext={...context,routing_rules:provenance.routing_rules,routing_catalog:provenance.routing_catalog};
          const validated=validateGenerationProposal(state.nodes.expand.output,{pack:sourcePack,resources,provenance,context:expansionContext});
          requireValue(validated.compiled.proposal_hash===reviewIdentity.proposal_hash,'AUTHORING_REVIEW_IDENTITY','Host reprojection changed the independently reviewed proposal');
          const previousRevision=deployed.revision_hash;
          deployed=await applyExpansion(store,args.workflow_id,validated.proposal,{expected_revision:previousRevision,source_revision:args.expected_revision,
            context:expansionContext,inference_confirmation:'The Host completion policy and independent review receipt authorize this exact proposal.',
            inference_authority:'host',inference_receipt:acceptance,conversion_review_contract_version:CONVERSION_CONTRACT.version});
          if(deployed.revision_hash!==previousRevision)await appendAuditEvent(this.configPath,{event:'workflow-authoring-deployment-reproject',
            run_id:args.run_id,workflow_id:args.workflow_id,source_revision:args.expected_revision,proposal_hash:reviewIdentity.proposal_hash,
            previous_revision:previousRevision,deployed_revision:deployed.revision_hash});
        }
        if(automatic)await this.preflightAutomaticAuthoring(args,{store,context,deployed});
        await Promise.all([this.strictManager.stopRun(args.run_id),this.managedNativeManager.stopRun(args.run_id),this.hostMainManager.stopRun(args.run_id)]);
        const authoring_cleanup=await beginAcceptedAuthoringCleanup({configPath:this.configPath,store,runtime,context,record,deployed,service:this,controlToken:args.control_token});
        if(automatic)return this.finishAutomaticAuthoring(args,{store,runtime,context});
        return {...deployed,authoring_cleanup};
  }

  async validationContext(store, workflow, context) {
    const addHostBindingErrors = (validation, packs = [{workflow}]) => {
      const errors = packs.flatMap(pack => hostToolBindingIssues(pack.workflow, this.capabilities.hostToolRegistry ?? {})
        .map(error => ({...error, workflow_id:pack.workflow.id})));
      if (!errors.length) return validation;
      return { ...validation, valid: false, launch_ready: false, errors: [...validation.errors, ...errors] };
    };
    const initial = addHostBindingErrors(validateWorkflowGraph(workflow, context));
    const deferred = new Set(['SKILL_MISSING', 'SKILL_STALE', 'SUBWORKFLOW_MISSING', 'SUBWORKFLOW_INVALID']);
    if (initial.errors.some(error => !deferred.has(error.code))) return { context, validation: initial };
    try {
      const root = { workflow, resources: [], revision_hash: digest(canonicalJSON(workflow)) };
      const closure = await resolveWorkflowPins(store, root, { rootResources: {} });
      const resolved = { ...context, ...closure.context };
      return { context: resolved, validation: addHostBindingErrors(validateWorkflowGraph(workflow, resolved), closure.packs) };
    } catch (error) {
      return { context, validation: { valid: false, launch_ready: false, errors: [{ code: error.code ?? 'DEPENDENCY_RESOLUTION_FAILED', message: error.message }], blockers: [], order: [] } };
    }
  }
  async open(policy=undefined) {
    const config = await this.config();
    requireValue(config.version === 7, 'WORKFLOW_MIGRATION_REQUIRED', 'The user-owned configuration must migrate to v7 before Workflow execution');
    const context = { providers: config.providers, ...(this.capabilities.context ?? {}), check_runtime_requirements: true };
    // Provider authority always comes from the actual user config, never probes.
    context.providers = config.providers;
    context.environment = Object.keys(this.env).filter(key => Boolean(this.env[key]));
    // A host tool is one capability with one stable name.  Expose registered
    // broker IDs in both places: `host_tools` validates executable pinned
    // contracts while `tools` satisfies the Workflow requirement declaration.
    // Keeping two unrelated lists previously let a fixture validate under one
    // spelling but fail launch-readiness under the other.
    const registeredHostTools = Object.keys(this.capabilities.hostToolRegistry ?? {});
    const availableHostTools = [...new Set([...(context.host_tools ?? []), ...(this.capabilities.host_tools ?? []), ...registeredHostTools])];
    context.host_tools = availableHostTools;
    context.tools = [...new Set([...(context.tools ?? []), 'read_workflow_resource', ...availableHostTools])];
    const storeRoot = insideRoot(dirname(this.configPath), join(dirname(this.configPath), config.workflow_store.relative_path));
    await noSymlinks(storeRoot); // A missing migrated generation is corruption, not an empty new library.
    const store = await new WorkflowStore(storeRoot, { validationContext: context }).initialize();
    const providerIdentityMigrations = await observeForegroundPhase('pm', () => migrateStoredWorkflowProviderIds(store));
    const hostToolIdentityMigrations = await observeForegroundPhase('hm', () => migrateStoredWorkflowHostToolIdentities(store));
    // Only the Host's fixed execution routes can select this module-private
    // policy. Public/direct opening and Role operations retain full validation.
    if(policy!==WORKFLOW_EXECUTION_OPEN)
      context.roles=await observeForegroundPhase('rp', () => activeRoleProfiles(config.providers,store));
    store.validationContext=context;
    const runtime = await new WorkflowRuntime({ workflowStore: store, runRoot: join(dirname(this.configPath), 'workflow-runs'), historyMaintenance: this.historyMaintenance.hook, context, executionAdmission: this.attemptAdmission,
      parallelManager: this.parallelManager, beforeStart: closure => this.prepareCodexRegistration(closure),
      environmentResolver:(requirements,options)=>discoverRuntimeEnvironment(requirements,{...options,env:this.env,registryPath:registryPathForConfig(this.configPath)}),
      environmentVerifier:(requirements,pinned)=>verifyRuntimeEnvironment(requirements,pinned,{env:this.env,registryPath:registryPathForConfig(this.configPath)}),
      strictCapability: this.capabilities.strictCapability ?? (async (pack, closure) => { await this.strictManager.capability(pack, config.providers, closure?.skills); return true; }),
      ...(this.capabilities.parallelWriteCapability ? { parallelWriteCapability: this.capabilities.parallelWriteCapability } : {}),
    }).initialize();
    const executor = new WorkflowExecutor({ runtime, getConfig: () => this.config(), registry: this.registry, strictManager: this.strictManager, managedNativeManager: this.managedNativeManager,
      hostToolRunner: this.capabilities.hostToolRunner ?? new HostToolRunner({ registry: this.capabilities.hostToolRegistry ?? {}, env: this.env }), attemptAdmission: this.attemptAdmission, nativeMainSelection:this.nativeMainSelection, env: this.env, fetchImpl: this.fetchImpl });
    const coordinator = new RunExecutionCoordinator({ admission: this.attemptAdmission, strictManager: this.strictManager,
      managedNativeManager: this.managedNativeManager, hostMainManager: this.hostMainManager, registry: this.registry });
    coordinator.bind(runtime);
    runtime.fenceRunExecution = (id,foregroundFence) => coordinator.fenceRun(id,foregroundFence);
    runtime.fenceAttemptExecution = (runId,nodeId,attemptId,foregroundFence) => coordinator.fenceAttempt(runId,nodeId,attemptId,foregroundFence);
    runtime.scheduleRunDrain = id => coordinator.scheduleDrain(id);
    runtime.failAttemptAfterQuiescence = (runId, args, error, options) => coordinator.failAttemptAfterQuiescence(runId, args, error, options);
    runtime.quiesceFailedOrigin = entry => coordinator.quiesceOrigin(entry);
    executor.coordinator = coordinator;
    return { config, context, store, runtime, executor, coordinator, drive: new WorkflowDrive({ runtime, executor }), hostMainManager: this.hostMainManager,
      provider_identity_migrations: providerIdentityMigrations,
      host_tool_identity_migrations: hostToolIdentityMigrations.filter(item => item.status !== 'blocked'),
      host_tool_identity_issues: hostToolIdentityMigrations.filter(item => item.status === 'blocked') };
  }
  async #requestOpen(operation){
    const request=executionRequests.getStore();
    const execution=WORKFLOW_EXECUTION_OPERATIONS.has(operation);
    const open=()=>observeForegroundPhase('op',()=>this.open(execution?WORKFLOW_EXECUTION_OPEN:undefined));
    // Role and all other public operations preserve their original full opening.
    if(!request?.active||!REQUEST_OPEN_OPERATIONS.has(operation))return open();
    let entry;
    try{
      // Every transition still validates the actual current user configuration.
      entry=request.services.get(this);
      // Only initialization is shared; never serialize execution/authority work.
      if(entry)await entry.pending;
      if(!request.active)return open();
      const config=await this.config(),basis=initializationBasis(this,config);
      if(!request.active)return open();
      // A sibling may have admitted initialization while this fresh read was
      // pending. Re-enter against that exact entry rather than opening twice.
      if(request.services.get(this)!==entry)return this.#requestOpen(operation);
      if(!basis.reusable){request.services.delete(this);return observeForegroundPhase(basis.reason==='budget'?'ib':'ia',open);}
      if(entry){
        if(!sameInitializationBasis(entry.basis,basis)||(!execution&&!entry.full)){
          request.services.delete(this);entry=null;
        }
      }
      if(!entry){
        entry={full:!execution,pending:null,basis:null,value:null};
        request.services.set(this,entry);
        entry.pending=(async()=>{
          const value=await open();
          const openedBasis=initializationBasis(this,value.config);
          requireValue(sameInitializationBasis(basis,openedBasis),'WORKFLOW_REQUEST_INITIALIZATION_CHANGED',
            'Workflow configuration, environment or capabilities changed during request initialization');
          entry.basis=openedBasis;entry.value=value;
          return value;
        })();
        return await entry.pending;
      }
      return await observeForegroundPhase('ir',async()=>{
        // Retain original directory/link checks on every transition; no cached
        // filesystem grant, Run, pins, authority, receipt or validation result.
        await entry.value.store.initialize();await entry.value.runtime.initialize();
        return {...entry.value,config};
      });
    }catch(error){if(request.services.get(this)===entry)request.services.delete(this);throw error;}
  }
  modelResult(value){return modelNativeContinuationView(value,this.invocationAdapters);}
  async authorityReader(){
    const config=await this.config();
    requireValue(config.version===7,'WORKFLOW_MIGRATION_REQUIRED','The user-owned configuration must migrate to v7 before Workflow execution');
    // Live authority reads do not need library migration or Role construction.
    // The subsequent execution call still validates the current configuration.
    return {runs:new WorkflowRunStore(join(dirname(this.configPath),'workflow-runs'))};
  }
  async withModelStartup(modelThreadId, startup, launch) {
    requireValue(typeof modelThreadId === 'string' && /^[0-9a-f-]{36}$/i.test(modelThreadId),
      'MODEL_THREAD_ID', 'Startup requires its authenticated initiating conversation');
    requireValue(!['host_startup_sha256','host_startup_key'].some(key => Object.hasOwn(startup.args.constraints ?? {}, key)),
      'WORKFLOW_STARTUP_FIELDS', 'Startup identity is Host-owned');
    const identity = digest(canonicalJSON(startup));
    // This gate is per initiating chat and independent of Run-store admission.
    // Never hold the global store lock while launching or waiting for an Agent.
    const gate = new WorkflowStore(join(dirname(this.configPath), 'workflow-startups', modelThreadId));
    await gate.initialize();
    return gate.withWriter(async () => {
      const runtime = await this.authorityReader();
      const records = await runtime.runs.listForThread(modelThreadId);
      const active = records.filter(record =>
        !['succeeded','failed','cancelled','interrupted'].includes(record.state.status));
      requireValue(active.length <= 1, 'MODEL_RUN_AUTHORITY', 'More than one active Run is bound to this conversation');
      let intent;
      const key = startup.args.launch_key;
      if (key) {
        requireValue(/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.test(key),
          'WORKFLOW_STARTUP_FIELDS', 'Startup invocation identity must be a UUID');
        const path = join(gate.root, `launch-${key}.json`);
        try { await noSymlinks(path);const info=await lstat(path);
          requireValue(info.isFile()&&info.nlink===1&&info.size<=4096,'WORKFLOW_STARTUP_INTENT','Startup intent must be one bounded regular file');
          const bytes=await readFile(path);requireValue(bytes.length<=4096,'WORKFLOW_STARTUP_INTENT','Startup intent grew beyond its limit');
          intent=JSON.parse(bytes.toString('utf8')); }
        catch (error) { if (error.code !== 'ENOENT' || error.path !== path) throw error; }
        if (intent) requireValue(intent.thread_id === modelThreadId && intent.sha256 === identity
          && typeof intent.run_id === 'string' && /^[0-9a-f-]{36}$/.test(intent.run_id),
          'WORKFLOW_STARTUP_CONFLICT', 'The retained invocation belongs to a different exact startup request');
        else {
          requireValue(!active.length, 'WORKFLOW_STARTUP_CONFLICT', 'This conversation already has a different active invocation');
          intent = {thread_id:modelThreadId,sha256:identity,run_id:randomUUID(),published:false};
          await writeDurableJSON(path, intent);
        }
      }
      const record = intent ? records.find(record => record.state.run_id === intent.run_id) : active[0];
      if (!record) {
        requireValue(!active.length, 'WORKFLOW_STARTUP_CONFLICT', 'This conversation already has a different active invocation');
        const publication=intent?await runtime.runs.startupPublication(intent.run_id):null;
        if(publication)requireValue(publication.thread_id===modelThreadId&&publication.launch_key===key&&publication.sha256===identity,
          'WORKFLOW_STARTUP_CONFLICT','The durable Run publication belongs to a different invocation');
        requireValue(!publication,'WORKFLOW_STARTUP_HISTORY_REMOVED',
          'This invocation committed publication but its Run is missing; inspect the outcome and generate a new invocation');
        requireValue(!intent?.published,'WORKFLOW_STARTUP_HISTORY_REMOVED',
          'This exact invocation was published and its history was removed; generate a new startup invocation');
        try {
          const launched=await launch(identity, intent?.run_id, key);
          if(intent){requireValue(launched.run_id===intent.run_id,'WORKFLOW_STARTUP_IDENTITY','Launch returned a different reserved Run');
            await writeDurableJSON(join(gate.root,`launch-${key}.json`),{...intent,published:true});}
          return launched;
        }catch(error){
          if(intent)try{
            // A tool failure after publication must not make the retry allocate
            // another invocation or resurrect an already-removed outcome.
            await runtime.runs.read(intent.run_id);
            await writeDurableJSON(join(gate.root,`launch-${key}.json`),{...intent,published:true});
          }catch(checkError){if(checkError.code!=='ENOENT'||checkError.path!==runtime.runs.directory(intent.run_id))
            throw new AggregateError([error,checkError],'Startup failure and publication reconciliation failed');}
          throw error;
        }
      }
      requireValue(record.state.constraints?.host_startup_sha256 === identity,
        'WORKFLOW_STARTUP_CONFLICT', 'An active Run in this conversation belongs to a different startup request');
      const authority = await readOwnedAuthority(runtime, record.state.run_id);
      if(intent&&!intent.published)await writeDurableJSON(join(gate.root,`launch-${key}.json`),{...intent,published:true});
      return { ...await this.call('get',{run_id:record.state.run_id}), control_token: authority.control_token,
        startup_rejoined: true, wake_reason: 'native_handoff_required', next_action: 'workflow_native_next' };
    });
  }
  async modelStartedResult(value,{modelThreadId,signal,initialSemantic}={}){
    return withRunStoreObservation(()=>this.#modelStartedResult(value,{modelThreadId,signal,initialSemantic}),report=>appendAuditEvent(this.configPath,
      {event:'workflow-run-store-boundary',detail:canonicalJSON({operation:'startup_handoff',...report})}));
  }
  async #modelStartedResult(value,{modelThreadId,signal,initialSemantic}={}){
    // A startup wait can end at a semantic boundary without having prepared
    // its model packet. Resolve that relay inside this same authenticated call.
    // Attention, terminal outcomes and Host failures retain their exact result.
    if(value?.status!=='running' || value.wake_reason!=='native_handoff_required' || value.next_action!=='workflow_native_next'
      || value.pending_approvals?.length || value.attention?.length
      || ['failed','stale','audit_or_cleanup_failed'].includes(value.host_worker?.phase))return this.modelResult(value);
    signal?.throwIfAborted();
    const runtime=await this.authorityReader();
    const authority=await readOwnedAuthorityForThread(runtime,modelThreadId,{onLookup:diagnostic=>appendAuditEvent(this.configPath,
      {event:'workflow-model-authority-lookup',detail:canonicalJSON({thread_id:modelThreadId,...diagnostic})})});
    requireValue(value.run_id===authority.run_id && (!value.next_action_args?.run_id || value.next_action_args.run_id===authority.run_id),
      'RUN_IDENTITY','Startup handoff differs from the exact Run bound to this conversation');
    requireValue((!value.control_token || value.control_token===authority.control_token)
      && (!value.next_action_args?.control_token || value.next_action_args.control_token===authority.control_token),
      'RUN_AUTHORITY','Startup handoff differs from its retained Host authority');
    const expectedRunAuthority={run_id:authority.run_id,control_token:authority.control_token};
    // This Host continuation already resolved the exact thread-bound authority.
    // Reuse its identity, never its mutable state, through the private dispatch
    // seam. Each operation still authorizes its current Run/attempt normally.
    const options={model:true,modelThreadId,signal};
    const next=()=>this.#nativeDrive(expectedRunAuthority,options,async()=>modelNativeContinuationView(
      await this.#call('native_next',expectedRunAuthority,options),this.invocationAdapters));
    if(initialSemantic){
      const record=await runtime.runs.read(authority.run_id),node=startupSemanticNode(record.pins.root);
      requireValue(record.state.workflow_revision===initialSemantic.revision_hash&&node.id===initialSemantic.node_id,
        'WORKFLOW_STARTUP_IDENTITY','The actual startup node or pinned revision differs from its semantic contract');
      if (value.startup_rejoined && record.state.nodes[node.id]?.status === 'succeeded')
        return next();
      const prepared=await next();
      requireValue(prepared?.status==='orchestration_handoff','WORKFLOW_STARTUP_BOUNDARY','Initial semantics cannot skip another execution boundary');
      const current=await runtime.runs.read(authority.run_id);
      requireValue(current.state.nodes[node.id]?.status==='running'&&current.state.nodes[node.id].attempts.length===1,
        'WORKFLOW_STARTUP_IDENTITY','The initial semantic submission requires its exact first active attempt');
      // This is the same current-Main semantic completion, within the caller's
      // start call. Its original checker, scope audit and metering stay intact.
      return modelNativeContinuationView(await this.#call('orchestration_complete',{...expectedRunAuthority,output:initialSemantic.output}, {...options,
        expectedOrchestration:{node_id:node.id,attempt_id:current.state.nodes[node.id].active_attempt_id}}),this.invocationAdapters);
    }
    return next();
  }
  async call(operation,args={},options={}) {
    return withRunStoreObservation(()=>this.#publicCall(operation,args,options),report=>appendAuditEvent(this.configPath,
      {event:'workflow-run-store-boundary',detail:canonicalJSON({operation,...report})}));
  }
  async #publicCall(operation,args={},options={}) {
    if(options.model&&(MODEL_NATIVE_CONTINUATIONS.has(operation) || operation === 'orchestration_complete')){
      requireValue(args&& (operation === 'orchestration_complete' ? Object.keys(args).length === 1 && Object.hasOwn(args,'output')
        :operation==='native_spawned_batch'?Object.keys(args).every(key=>key==='batch_id')&&
          (args.batch_id===undefined||typeof args.batch_id==='string'&&/^[a-f0-9]{64}$/.test(args.batch_id))
          :Object.keys(args).length===0),'MODEL_CONTINUATION_FIELDS',
        'The Host owns every Run and receipt field; native acknowledgement accepts only its fixed adapter batch identity');
      const runtime=await this.authorityReader();
      const authority=await readOwnedAuthorityForThread(runtime,options.modelThreadId,{onLookup:diagnostic=>appendAuditEvent(this.configPath,
        {event:'workflow-model-authority-lookup',detail:canonicalJSON({thread_id:options.modelThreadId,...diagnostic})})});
      // A Host startup continuation is pinned before this second lookup. A
      // newer Run or recovered token must never inherit that earlier call.
      if(options.expectedRunAuthority){
        requireValue(authority.run_id===options.expectedRunAuthority.run_id,'RUN_IDENTITY','Workflow continuation resolved another Run after startup');
        requireValue(authority.control_token===options.expectedRunAuthority.control_token,'RUN_AUTHORITY','Workflow continuation authority changed after startup');
      }
      args={...args,run_id:authority.run_id,control_token:authority.control_token};
    }
    const invoke=async()=>{
      try{
        const result=await this.#call(operation,args,options);
        return options.model?modelNativeContinuationView(result,this.invocationAdapters):result;
      }catch(error){executionRequests.getStore()?.services.delete(this);throw error;}
    };
    if(operation!=='native_next')return invoke();
    return this.#nativeDrive(args,options,invoke);
  }
  async #nativeDrive(args,options,invoke){
    const operation='native_next';
    const configKey=process.platform==='win32'?this.configPath.toLowerCase():this.configPath;
    const key=JSON.stringify([configKey,args.run_id]);
    requireValue(!nativeDriveOwners.has(key),'NATIVE_AGENT_WAIT_ACTIVE',
      'This Run already has an active native collection call; await its bounded result without dispatching replacement Agents');
    const owner={operation};nativeDriveOwners.set(key,owner);
    try {return await withNativeAgentObserverDrive(invoke,{env:this.env,
      onObservation:report=>appendAuditEvent(this.configPath,{event:'workflow-native-observer-drive',
        detail:canonicalJSON({run_id:args.run_id,operation,...report})})});}
    finally {if(nativeDriveOwners.get(key)===owner)nativeDriveOwners.delete(key);}
  }
  async #call(operation, args = {}, { human = false, model = false, modelThreadId, bridgeHooks = null, signal, expectedOrchestration, expectedNativeSpawnBatch } = {}) {
    if (operation === 'migrate_v6') { requireValue(human, 'HUMAN_CONFIGURATION_REQUIRED', 'Migration is a user-owned console action'); await this.config(); return migrateV6OnDisk({ configPath: this.configPath }); }
    if (operation === 'restore_v6') { requireValue(human, 'HUMAN_CONFIGURATION_REQUIRED', 'Backup restoration is a user-owned console action'); return restoreV6Backup({ configPath: this.configPath, expected_current_sha256: args.expected_current_sha256 }); }
    const conversationalRecovery = operation === 'recover_control' ? conversationControlRecoveryRequest(args) : null;
    const { config, context, store, runtime, executor, coordinator, drive, hostMainManager } = await this.#requestOpen(operation);
    if(human && !args.control_token && ['approve','cancel','continue_main','accept_main'].includes(operation)) {
      const authority=await readOwnedAuthority(runtime,args.run_id);
      args={...args,control_token:authority.control_token,...(operation==='continue_main'?{owner:authority.owner,host_owned:true}:{})};
    }
    if (['start', 'begin_main', 'run_main', 'continue_main', 'accept_main', 'claim_node', 'dispatch', 'drive', 'native_next', 'native_followed_up', 'orchestration_complete', 'retry_node', 'resume', 'recover_claim', 'recover_strict_result', 'reattach_connector', 'reattach_subworkflow', 'prepare_integration', 'integrate_parallel'].includes(operation)) requireValue(config.global.enabled && !isEnvironmentDisabled(this.env) && executionAdmissionOpen(this.configPath), 'CONTROL_DISABLED', 'Workflow execution is disabled');
    if(model&&args.run_id&&args.node_id&&['claim_node','dispatch','dispatch_receipt','record_usage','complete_node','fail_node','recover_claim','recover_strict_result','collect_strict','cleanup_strict_orphans','reattach_handoff'].includes(operation)){
      const record=await runtime.runs.read(args.run_id),definition=record.pins.root.workflow.nodes.find(node=>node.id===args.node_id);
      requireValue(definition?.executor?.kind!=='main','HOST_MAIN_LIFECYCLE_REQUIRED','Main lifecycle is owned by its Host execution mode');
    }
    switch (operation) {
      case 'startup_contract': {
        const pack=await store.snapshot(args.workflow_id);
        const contract=startupSemanticContract(pack);
        const typed=Object.hasOwn(args,'initial_output'),{initial_output,...startupArgs}=args;
        workflowCallArguments('workflow_start',startupArgs);
        if(typed)validateData(initial_output,contract.response_schema);
        const resources=await store.resources(args.workflow_id,pack.revision_hash);
        const request=await loadWorkflowInputsFile(startupArgs,{model});
        const permissions=runPermissions(request);await noSymlinks(permissions.workspace);
        const effectiveInputs=effectiveRunInputs(request.inputs??{},pack.workflow.inputs_schema,permissions);
        const inputs=resolveBindings(contract.input_bindings,{inputs:effectiveInputs});
        let inlineBytes=0;
        contract.resources=contract.resources.map(resource=>{
          const bytes=resources[resource.path];requireValue(bytes&&bytes.length===resource.bytes&&digest(bytes)===resource.sha256,'WORKFLOW_STARTUP_RESOURCE','Initial semantic resource bytes changed');
          if(!/\.(?:md|txt|rst)$/i.test(resource.path)||bytes.length>8192||inlineBytes+bytes.length>8192)return resource;
          inlineBytes+=bytes.length;return {...resource,content:new TextDecoder('utf-8',{fatal:true}).decode(bytes)};
        });
        const startup_reference=await createPreparedStartup(this.configPath,
          {...startupArgs,startup_inputs_sha256:digest(canonicalJSON(request.inputs??{})),revision_hash:pack.revision_hash,launch_key:randomUUID()},
          {typed,invocationTransport:this.invocationTransport,...(typed?{initialOutput:initial_output}:{})});
        return {...contract,inputs,startup_reference,model_invocations:0,runs_started:0,
          startup_binding:'exact_revision_and_inputs',
          invocation_adapter:this.invocationAdapters.startupReference(startup_reference,typed)};
      }
      case 'role_templates': {
        const packs=await storedRolePacks(store),customizations=builtinRoleCustomizations(packs);
        const roles=(await bundledRoles(config.providers)).map(({item,stage,provider,id,revision_hash})=>{
          const pack=customizations.get(id),customization=pack?storedRoleDescriptor(pack,config.providers):null;
          const active=customization?.status==='ready'?customization:null;
          return {id,name:active?pack.workflow.name:item.name,description:active?pack.workflow.description:item.description,tags:active?pack.workflow.tags:item.tags,role:active?active.node.role:stage.role,
            template_kind:'role',revision_hash:active?active.revision_hash:revision_hash,access:active?active.node.access:stage.access,
            provider_id:active?active.provider_id:provider.id,provider_kind:active?active.provider?.kind:provider.kind,
            provider_description:(active?active.provider:provider)?.description??null,
            model:active?active.model:roleProviderModel(provider),
            reasoning_effort:active?active.reasoning_effort:provider.config?.reasoning_effort??null,
            enabled:active?active.enabled:item.enabled!==false,default_enabled:item.enabled!==false,
            provider_enabled:active?active.available:roleProviderAvailable(provider,stage.access),builtin:true,customized:!!customization,
            ...(customization?{customization:{workflow_id:customization.workflow_id,revision_hash:customization.revision_hash,status:customization.status,enabled:customization.enabled,
              provider_id:customization.provider_id,model:customization.model,reasoning_effort:customization.reasoning_effort}}:{})};
        });
        for(const pack of packs) if(!builtinRoleCustomizationId(pack)&&templateKind(pack)==='role'&&pack.workflow.status==='ready'){
          const node=roleNode(pack);
          const provider=config.providers.find(item=>item.id===node.executor?.provider_id);
          roles.push({id:pack.workflow.id,name:pack.workflow.name,description:pack.workflow.description,tags:pack.workflow.tags,revision_hash:pack.revision_hash,role:node.role,access:node.access,
            enabled:pack.workflow.enabled!==false,provider_enabled:roleProviderAvailable(provider,node.access),provider_id:provider?.id??node.executor?.provider_id??null,
            provider_kind:provider?.kind??null,provider_description:provider?.description??null,model:roleProviderModel(provider),reasoning_effort:provider?.config?.reasoning_effort??null,builtin:false});
        }
        return roles;
      }
      case 'customize_role': {
        requireValue(human,'HUMAN_CONFIGURATION_REQUIRED','Built-in Role customization belongs to the human console');
        requireValue(typeof args.workflow_id==='string'&&args.workflow_id.startsWith(BUILTIN_ROLE_PREFIX),'ROLE_TEMPLATE_MISSING','Select a built-in Role to customize');
        const entry=(await bundledRoles(config.providers)).find(item=>item.id===args.workflow_id);
        requireValue(entry,'ROLE_TEMPLATE_MISSING','Built-in role is unavailable');
        const customization=builtinRoleCustomizations(await storedRolePacks(store)).get(entry.id);
        if(customization)return store.snapshot(customization.workflow.id);
        const workflowId=`role-${entry.item.id}`;
        const compiled=compileWorkflowBrief({kind:'brief',template_kind:'role',workflow_id:workflowId,
          name:entry.item.name,brief:entry.item.role_instructions||entry.stage.template,provider_id:entry.provider.id,role:entry.stage.role,access:entry.stage.access});
        compiled.workflow.enabled=entry.item.enabled!==false;
        compiled.workflow.description=entry.item.description;
        compiled.workflow.tags=[...new Set([...(entry.item.tags??[]),'role'])];
        compiled.provenance={...compiled.provenance,kind:'role_customization',builtin_role_id:entry.id,builtin_role_revision:entry.revision_hash};
        return store.create(compiled.workflow,compiled);
      }
      case 'start_role_connector':
      case 'role_template': {
        const deliver=async profile=>{
          if(operation==='role_template')return profile;
          requireValue(args.revision_hash===profile.revision_hash,'ROLE_REVISION','Role launch must pin the compiled Role revision');
          requireValue(config.global.enabled&&!isEnvironmentDisabled(this.env)&&executionAdmissionOpen(this.configPath),
            'CONTROL_DISABLED','Role execution is disabled');
          requireValue(profile.adapter?.execution==='builtin_connector','ROLE_CONNECTOR_REQUIRED','Selected Role must use a built-in connector');
          const provider=config.providers.find(item=>item.id===profile.provider_id);
          requireValue(typeof args.workspace==='string'&&isAbsolute(args.workspace),'ROLE_WORKSPACE','Role connector needs an absolute existing Git workspace');
          const permissions=roleConnectorPermissions(profile,args);
          const result=await this.registry.start({provider,stage:{id:'role',read_only:profile.access==='read_only',requires_user_approval:profile.approval.required},
            prompt:profile.instructions,workspace:permissions.workspace,taskTypeId:profile.id,stageId:'role',allowedPaths:permissions.allowed_paths,
            userApproved:args.user_approved===true,assertActive:()=>{requireValue(!signal?.aborted,'ROLE_START_CANCELLED','Role launch was cancelled');}});
          await appendAuditEvent(this.configPath,{event:'role-connector-start',role_id:profile.id,revision_hash:profile.revision_hash,
            provider_id:profile.provider_id,access:profile.access,task_id:result.task_id,outcome:'ok'},{effectCommitted:true});
          return result;
        };
        requireValue(typeof args.task==='string'&&args.task.trim()&&args.task.length<=30000,'ROLE_TASK','Role task must be nonempty and bounded');
        if(args.workflow_id.startsWith(BUILTIN_ROLE_PREFIX)){
          const entry=(await bundledRoles(config.providers)).find(item=>item.id===args.workflow_id);
          requireValue(entry,'ROLE_TEMPLATE_MISSING','Built-in role is unavailable');
          const customization=builtinRoleCustomizations(await storedRolePacks(store)).get(entry.id);
          if(customization?.workflow.status==='ready'){
            requireValue(!args.revision_hash||args.revision_hash===customization.revision_hash,'ROLE_REVISION','Built-in Role customization revision has changed');
            const node=roleNode(customization),unchanged=node.prompt_template===entry.stage.template;
            return deliver(storedRoleProfile(customization,config.providers,args,{id:entry.id,providerOptions:{env:this.env,allowDirectApi:config.global.allow_direct_api},
              ...(unchanged&&entry.item.role_instructions?{instructions_override:entry.item.role_instructions}:{})}));
          }
          requireValue(entry.item.enabled!==false,'ROLE_NOT_READY','Built-in Role is disabled');
          requireValue(!args.revision_hash||args.revision_hash===entry.revision_hash,'ROLE_REVISION','Built-in role revision has changed');
          const {item,stage,provider,id,revision_hash}=entry;
          requireValue(roleProviderAvailable(provider,stage.access),'ROLE_PROVIDER_UNAVAILABLE','Pinned Role needs an enabled compatible Provider');
          const policy=roleExecutionPolicy(stage);
          return deliver({id,revision_hash,template_kind:'role',role:stage.role,...policy,provider_id:provider.id,
            ...compiledRoleProvider(provider,policy,{env:this.env,allowDirectApi:config.global.allow_direct_api}),
            instructions:directRolePrompt(item.role_instructions||stage.template,args)});
        }
        const pack=await store.snapshot(args.workflow_id,args.revision_hash);
        return deliver(storedRoleProfile(pack,config.providers,args,{providerOptions:{env:this.env,allowDirectApi:config.global.allow_direct_api}}));
      }
      case 'authoring_workflows': {
        const packs=await this.ensureAuthoringWorkflows(store,config);
        return AUTHORING_WORKFLOWS.map(definition=>{const pack=packs.find(item=>item.workflow.id===definition.id);return {...structuredClone(definition),revision_hash:pack.revision_hash,status:pack.workflow.status,enabled:pack.workflow.enabled,workflow:pack.workflow};});
      }
      case 'export_workflow_package': {
        const pack=await store.snapshot(args.workflow_id,args.revision_hash);
        return exportWorkflowPackage(pack,await store.resources(pack.workflow.id,pack.revision_hash),{packageVersion:args.package_version ?? '1.0.0'});
      }
      case 'install_workflow_package': {
        const sources=[args.package!==undefined,args.package_path!==undefined,args.source_url!==undefined].filter(Boolean).length;
        requireValue(sources===1,'WORKFLOW_PACKAGE_SOURCE','Choose exactly one Workflow package source: package_path, source_url, or package');
        let bundle=args.package,source='inline-package';
        if(args.source_url){
          const url=new URL(args.source_url);requireValue(url.protocol==='https:','WORKFLOW_PACKAGE_URL','Remote Workflow packages require HTTPS');
          const bytes=await fetchWorkflowPackage(this.fetchImpl,url);
          if(args.expected_sha256)requireValue(digest(bytes)===args.expected_sha256,'WORKFLOW_PACKAGE_FETCH_INTEGRITY','Downloaded Workflow package differs from the expected digest');
          try{bundle=JSON.parse(bytes.toString('utf8'));}catch{requireValue(false,'WORKFLOW_PACKAGE_JSON','Remote Workflow package is not valid JSON');}
          source=args.source_url;
        }else if(args.package_path){
          const local=await readWorkflowPackageFile(args);
          try{bundle=JSON.parse(local.bytes.toString('utf8'));}catch{requireValue(false,'WORKFLOW_PACKAGE_JSON','Local Workflow package is not valid JSON');}
          source=local.path;
        }
        const checked=validateWorkflowPackage(bundle);
        const validation=await this.validationContext(store,checked.snapshot.workflow,context);
        requireValue(validation.validation.valid,'WORKFLOW_NOT_READY','Workflow package dependencies or structure are invalid',{validation:validation.validation});
        store.validationContext=validation.context;
        return installWorkflowPackage(store,bundle,{source});
      }
      case 'generate_task_brief': {
        requireValue(human,'HUMAN_TASK_BRIEF','Task description generation belongs to the human console');
        const pack=args.workflow_id?await store.snapshot(args.workflow_id,args.revision_hash):null;
        const workflow=args.workflow ?? pack?.workflow;
        requireValue(workflow && typeof workflow.name==='string','TASK_BRIEF_WORKFLOW','Select a Workflow first');
        requireValue(typeof (args.existing ?? '')==='string','TASK_BRIEF_INPUT','Existing task description must be text');
        return generateTaskBrief({workflow,source:workflow.description ?? '',existing:args.existing ?? '',config,directory:dirname(this.configPath),env:this.env});
      }
      case 'cache_cleanup_preview':
      case 'cleanup_caches': {
        requireValue(human,'HUMAN_CACHE_CLEANUP','Cache cleanup belongs to the human console');
        return cleanupCaches({store,runs:runtime.runs,home:this.env.CODEX_HOME || join(homedir(),'.codex'),auditRoot:dirname(this.configPath),env:this.env,preview:operation==='cache_cleanup_preview'});
      }
      case 'authoring_prompt_preview': {
        requireValue(human,'HUMAN_GENERATION','Prompt preview belongs to the console');
        const rules=args.routing_rules ?? await loadRoutingSettings(dirname(this.configPath),config.providers);
        const pack=await store.snapshot(args.workflow_id,args.revision_hash);
        const definition=args.authoring_workflow_id?authoringWorkflow(args.authoring_workflow_id):authoringWorkflowForPack(pack);
        requireValue(authoringWorkflowForPack(pack).id===definition.id,'AUTHORING_WORKFLOW_SOURCE','Selected authoring Workflow does not accept this source kind');
        let template;
        if(args.authoring_workflow_id){
          template=await store.snapshot(definition.id,args.authoring_workflow_revision);
          requireValue(template.provenance?.kind==='bundled_authoring_workflow' && template.provenance.authoring_workflow_id===definition.id,'AUTHORING_WORKFLOW_ID_CONFLICT','Selected system Workflow identity is invalid');
        }else{
          const definitions=await this.ensureAuthoringWorkflows(store,config,rules);template=definitions.find(item=>item.workflow.id===definition.id);
        }
        const bindings=storedAuthoringBindings(template.workflow,config.providers);
        if(args.provider_id)requireValue(args.provider_id===bindings.planner.id,'AUTHORING_WORKFLOW_PROVIDER','Prompt preview Provider must match the stored authoring Workflow');
        const pinnedRules={...rules,generation:{...(rules.generation ?? {}),planner_provider_id:bindings.planner.id,review_provider_id:bindings.reviewer.id,max_rounds:bindings.maxRounds}};
        const job=authoringRunPack(pack,await store.resources(args.workflow_id,pack.revision_hash),bindings.planner,'generation-preview',pinnedRules,true,bindings.reviewer,config.providers,template);
        return {invoked:false,source_revision:pack.revision_hash,authoring_pipeline:structuredClone(template.workflow.authoring.pipeline),generator:job.workflow.nodes.find(n=>n.id==='expand').prompt_template,reviewer:job.workflow.nodes.find(n=>n.id==='final').prompt_template,model_resource_paths:job.workflow.nodes.filter(n=>n.type==='agent').map(n=>({node_id:n.id,paths:n.resources})),shared_request:job.resources['analysis/request.txt'],review_request:job.resources['analysis/review-request.txt'],output_schemas:Object.fromEntries(job.workflow.nodes.filter(n=>n.outputs_schema).map(n=>[n.id,n.outputs_schema])),runtime_context:'The planner fills only semantic inventory fields from its concise role packet. The Host then assembles the graph, binds schemas/executors/permissions, validates cycles/reachability/contracts, and records a pipeline trace before the reviewer receives its separate exhaustive packet. Execution additionally supplies actual upstream results, output schema and any previous repair feedback. This preview does not invoke a model.'};
      }
      case 'authoring_preview': {
        requireValue(human,'HUMAN_GENERATION','Saved authoring evidence belongs to the human Workbench');
        return discoverAuthoringPreview(runtime,args,{store,context});
      }
      case 'start_authoring': {
        requireValue(human,'HUMAN_GENERATION','Start automatic generation from the console');
        requireValue(config.global.enabled && !isEnvironmentDisabled(this.env),'CONTROL_DISABLED','Workflow execution is disabled');
        const rules = args.routing_rules ?? await loadRoutingSettings(dirname(this.configPath),config.providers);
        const runId = workflowId(args.run_id);
        const workspace = await ensureDirectory(join(dirname(this.configPath),'skill-generation-workspaces','job-'+runId));
        return this.call('create_authoring_run',{...args,run_id:runId,workspace,routing_rules:rules,automatic_generation:true,main_actor:'human-console'});
      }
      case 'advance_authoring': {
        requireValue(human,'HUMAN_GENERATION','Automatic generation belongs to its console controller');
        requireValue(config.global.enabled && !isEnvironmentDisabled(this.env),'CONTROL_DISABLED','Workflow execution is disabled');
        return advanceGeneration(this,runtime,executor,args,{store,context});
      }
      case 'continue_authoring': {
        requireValue(human,'HUMAN_GENERATION','User-guided authoring repair belongs to its console controller');
        requireValue(config.global.enabled && !isEnvironmentDisabled(this.env),'CONTROL_DISABLED','Workflow execution is disabled');
        return continueGenerationRepair(runtime,args);
      }
      case 'recheck_authoring': {
        requireValue(human,'HUMAN_GENERATION','Generation recheck belongs to its console controller');
        requireValue(config.global.enabled && !isEnvironmentDisabled(this.env),'CONTROL_DISABLED','Workflow execution is disabled');
        return recheckGenerationProposal(this,runtime,args,{store,context});
      }
      case 'accept_rechecked_authoring_review': {
        requireValue(human,'HUMAN_GENERATION','Rechecked generation acceptance belongs to the human console');
        return acceptRecheckedGenerationReview(this,runtime,args);
      }
      case 'login_authoring': {
        requireValue(human,'HUMAN_AUTHENTICATION_REQUIRED','Generation login belongs to the authenticated human console');
        return loginGeneration(this,runtime,args);
      }
      case 'accept_authoring': {
        requireValue(human,'HUMAN_GENERATION','Generation acceptance belongs to the human console');
        return acceptGeneration(this,runtime,args);
      }
      case 'local_clients': {
        requireValue(human,'HUMAN_CLIENT_DISCOVERY','Local client discovery belongs to the console');
        const codex=await localCodexCatalog({env:this.env,extra:[config.strict_executor.codex_binary].filter(Boolean)});
        const connectors=await Promise.all(config.providers.filter(p=>p.kind==='builtin_connector').map(async provider=>{try{return {provider_id:provider.id,...await this.registry.probe(provider,{}),models:{source:'client_managed',available:null,message:'模型由客户端管理；当前接口未提供完整模型目录。'}};}catch(error){return {provider_id:provider.id,error:{code:error.code,message:error.message}};}}));
        let qualification, qualification_error;
        try { qualification=codexQualification(await qualifiedStrictSettings(config,this.env)); }
        catch(error){ qualification_error={code:error.code??'CODEX_QUALIFICATION_FAILED',message:error.message,...(error.capability?{capability:error.capability}:{})}; }
        return {codex,connectors,execution_runtime:{binary:config.strict_executor.codex_binary,qualification:qualification??null,...(qualification_error?{qualification_error}:{})}};
      }
      case 'capabilities': {
        let strict;
        try { strict = { available: true, qualification: codexQualification(await qualifiedStrictSettings(config, this.env)) }; }
        catch (error) { strict = { available: false, code: error.code ?? 'STRICT_UNAVAILABLE', message: error.message, ...(error.capability?{capability:error.capability}:{}) }; }
        return { strict: { ...strict, authentication: config.strict_executor.authentication.mode },
          ...(human ? { run_history_maintenance: await this.historyMaintenance.status() } : {}),
          invocation_transport:this.invocationTransport,
          ...(this.invocationTransport==='code_mode'?{legacy_code_mode_invocation_defaults:{...WORKFLOW_CALL_DEFAULTS}}:{}),
          startup_invocation_adapter: this.invocationAdapters.call('workflow_start'),
          tools: context.tools, mcp_servers: context.mcp_servers ?? [], executables: context.executables ?? [], parallel_write: 'qualified Strict broker with Git worktrees', boundary: 'application catalog, explicit Skill input and broker; not an OS ACL' };
      }
      case 'routing_defaults': return loadRoutingSettings(dirname(this.configPath),config.providers);
      case 'save_routing_rules': {
        requireValue(human, 'HUMAN_CONFIGURATION_REQUIRED', 'Shared routing rules are edited in the human console');
        return saveRoutingSettings(dirname(this.configPath),config.providers,store,args.routing_rules,args.expected_rules);
      }
      case 'skill_inventory': {
        const selection = inventorySelection(this,args);
        return selection.inventory.list(selection.path);
      }
      case 'import_skill': {
        const selection = inventorySelection(this,args);
        const selected = await selection.inventory.select(selection.path, args.skill_id);
        const provider = config.providers.find(provider => provider.id === args.provider_id);
        if (args.provider_id) requireValue(provider, 'PROVIDER_MISSING', 'Selected instruction Provider does not exist');
        return importCoarseSkill(store, selected.path, { id: args.workflow_id, name: args.name, providerId: args.provider_id, role: 'implementer', expectedSourceHash: selected.source_hash });
      }
      case 'build_workflow': {
        requireValue(args.template_kind===undefined||['role','workflow'].includes(args.template_kind),'TEMPLATE_KIND','build_workflow template_kind must be role or workflow');
        const provider=config.providers.find(item=>item.id===args.provider_id);
        if(args.provider_id)requireValue(provider,'PROVIDER_MISSING','Selected instruction Provider does not exist');
        if(args.template_kind==='role'&&provider)requireValue(provider.enabled&&provider.capabilities?.read,'ROLE_PROVIDER_UNAVAILABLE','A Workbench Role needs an enabled readable Provider');
        if(args.template_kind==='role'&&(args.access??'bounded_write')==='bounded_write'&&provider)requireValue(provider.capabilities?.write,'ROLE_PROVIDER_WRITE','Workbench Role Provider cannot write');
        const authoring=new WorkflowAuthoringCompiler({store});
        return authoring.seed({kind:'brief',workflow_id:args.workflow_id,name:args.name,brief:args.brief,provider_id:args.provider_id,role:'implementer',template_kind:args.template_kind??'workflow',access:args.access});
      }
      case 'verify_relocation': {
        const pack = await store.snapshot(args.workflow_id, args.revision_hash);
        return verifyCoarseRelocation(pack, await store.resources(args.workflow_id, pack.revision_hash));
      }
      case 'import_review': return importReviewPacket(await store.snapshot(args.workflow_id, args.revision_hash));
      case 'inline_skill': return inlineSkillReference(store, args.workflow_id, args);
      case 'review_import': {
        requireValue(human, 'HUMAN_REVIEW_REQUIRED', 'Import and inference confirmation belongs to the human editor');
        const guard=()=>requireNoActiveSiblingAuthoringRun(runtime,{run_id:'direct-import-review',source_workflow_id:args.workflow_id,source_revision:args.expected_revision});
        const current=await store.snapshot(args.workflow_id);
        if(current.provenance?.kind==='workflow_conversion'&&current.provenance.conversion?.source_revision===args.expected_revision){
          await store.resumeHistoryPurge(args.workflow_id,current.revision_hash,{beforePurge:guard});return current;
        }
        return reviewImportedDraft(store,args.workflow_id,args,{beforeHistoryPurge:guard});
      }
      case 'prepare_expansion': {
        requireValue(config.global.enabled && !isEnvironmentDisabled(this.env), 'CONTROL_DISABLED', 'Workflow expansion is disabled');
        const provider = config.providers.find(item => item.id === args.provider_id);
        const pack = await store.snapshot(args.workflow_id, args.revision_hash);
        const packet = expansionPacket(pack, await store.resources(args.workflow_id, pack.revision_hash), provider, args.routing_rules ?? await loadRoutingSettings(dirname(this.configPath),config.providers), config.providers);
        const adapter = buildProviderAdapter(provider, { access: 'read_only' }, { env: this.env, allowDirectApi: config.global.allow_direct_api });
        // A packet is not an invocation. Native/MCP/Strict host integration must
        // preserve this selected Provider and record actual dispatch separately.
        return { ...packet, adapter, handoff_required: true, invoked: false, approval_required: provider.requires_user_approval };
      }
      case 'create_authoring_run': {
        requireValue(config.global.enabled && !isEnvironmentDisabled(this.env), 'CONTROL_DISABLED', 'Workflow expansion is disabled');
        const pack = await store.snapshot(args.workflow_id, args.revision_hash);
        const rules=args.routing_rules ?? await loadRoutingSettings(dirname(this.configPath),config.providers);
        const definition=authoringWorkflowForPack(pack);
        let template;
        if(args.authoring_workflow_id){
          requireValue(args.authoring_workflow_id===definition.id,'AUTHORING_WORKFLOW_SOURCE','Selected authoring Workflow does not accept this source kind');
          template=await store.snapshot(args.authoring_workflow_id,args.authoring_workflow_revision);
          requireValue(template.provenance?.kind==='bundled_authoring_workflow' && template.provenance.authoring_workflow_id===definition.id,'AUTHORING_WORKFLOW_ID_CONFLICT','Selected system Workflow identity is invalid');
        }else{
          const definitions=await this.ensureAuthoringWorkflows(store,config,rules);
          template=definitions.find(item=>item.workflow.id===definition.id);
        }
        const bindings=storedAuthoringBindings(template.workflow,config.providers);
        if(args.provider_id)requireValue(args.provider_id===bindings.planner.id,'AUTHORING_WORKFLOW_PROVIDER','Planner Provider must match the stored authoring Workflow');
        const pinnedRules={...rules,generation:{...(rules.generation ?? {}),planner_provider_id:bindings.planner.id,review_provider_id:bindings.reviewer.id,max_rounds:bindings.maxRounds}};
        const job = authoringRunPack(pack, await store.resources(args.workflow_id, pack.revision_hash), bindings.planner, args.run_id, pinnedRules, args.automatic_generation === true, bindings.reviewer,config.providers,template,args.completion_policy);
        await this.prepareCodexRegistration({packs:[job],provider_ids:job.workflow.requirements.providers});
        await this.strictManager.capability({ ...job, resources: prepareResources(job.resources).manifest }, config.providers);
        const jobs = await new WorkflowStore(join(dirname(this.configPath), 'workflow-expansion-jobs'), { validationContext: context }).initialize();
        // The reviewer binding is part of every authoring Run.  The automatic
        // flag controls bounded Host advancement/repair only; it must not make
        // a manually driven Run silently fall back to the generic main model.
        const planning = await new WorkflowRuntime({ generationPolicy:args.automatic_generation === true ? {settings:job.provenance.generation,reviewer:bindings.reviewer} : null, authoringReviewer:bindings.reviewer, workflowStore: jobs, runRoot: runtime.runs.root, historyMaintenance: this.historyMaintenance.hook, context, beforeStart: closure => this.prepareCodexRegistration(closure), strictCapability: async definition => { await this.strictManager.capability(definition, config.providers); return true; } }).initialize();
        return store.withWriter(async()=>{
          const current=await store.snapshot(args.workflow_id);
          requireValue(current.revision_hash===pack.revision_hash,'REVISION_CONFLICT','Private authoring source changed before its Run was registered');
          const saved = await jobs.create(job.workflow, job);
          const run=await planning.start({ workflow_id: saved.workflow.id, revision_hash: saved.revision_hash, run_id: args.run_id,
            workspace: args.workspace, main_actor: args.main_actor, access: 'read_only', inputs: { task: 'Analyze this pinned Skill into an editable Draft' } });
          return model?authoringControllerContinuation(run,run):run;
        });
      }
      case 'apply_authoring_result': {
        requireValue(human,'HUMAN_GENERATION','Applying an accepted authoring result belongs to the authenticated human console');
        return this.applyAcceptedAuthoringResult(args,{store,runtime,context});
      }
      case 'purge_authoring_artifacts': {
        requireValue(human,'HUMAN_GENERATION','Private authoring cleanup belongs to the authenticated human console');
        requireValue(typeof args.workflow_id==='string','AUTHORING_CLEANUP_IDENTITY','Cleanup retry needs the deployed Workflow ID');
        const journal=await store.readAuthoringCleanup(args.workflow_id,args.run_id);
        requireValue(journal&&journal.identity?.control_hash===digest(args.control_token),'RUN_AUTHORITY','Cleanup retry needs the exact retained transaction authority');
        const deployed=await store.snapshot(args.workflow_id,journal.identity.deployed_revision);
        if(journal.identity.completion_policy?.mode==='automatic')await this.preflightAutomaticAuthoring(args,{store,context,deployed});
        await Promise.all([this.strictManager.stopRun(args.run_id),this.managedNativeManager.stopRun(args.run_id),this.hostMainManager.stopRun(args.run_id)]);
        const cleanup=await continueAcceptedAuthoringCleanup({configPath:this.configPath,store,runtime,context,journal,deployed,service:this});
        if(journal.identity.completion_policy?.mode==='automatic')return this.finishAutomaticAuthoring(args,{store,runtime,context});
        return cleanup;
      }
      case 'list': {
        await this.ensureAuthoringWorkflows(store,config);
        const packs=(await store.list()).filter(pack=>args.include_legacy===true || pack.provenance?.kind!=='v6-migration');
        return Promise.all(packs.map(async pack => ({ id: pack.workflow.id, name: pack.workflow.name, status: pack.workflow.status, enabled: pack.workflow.enabled, revision_hash: pack.revision_hash, description: pack.workflow.description, template_kind:templateKind(pack), system_managed:pack.provenance?.kind==='bundled_authoring_workflow', legacy_task_type:pack.provenance?.kind==='v6-migration', role_builtin_id:builtinRoleCustomizationId(pack), import_mode:pack.workflow.import_status?.mode ?? null, skill_policy: pack.workflow.skill_policy, validation: (await this.validationContext(store, pack.workflow, context)).validation })));
      }
      case 'route': {
        await this.ensureAuthoringWorkflows(store,config);
        const eligible=[];
        for(const pack of await store.list()){
          if(pack.workflow.status!=='ready'||pack.workflow.enabled===false||pack.provenance?.kind==='bundled_authoring_workflow')continue;
          const checked=await this.validationContext(store,pack.workflow,context);
          if(checked.validation.launch_ready)eligible.push(pack);
        }
        return routeReadyWorkflows(eligible,args.task,{limit:args.limit ?? 5});
      }
      case 'read': {
        const pack = await store.snapshot(args.workflow_id, args.revision_hash);
        return { ...pack, validation: (await this.validationContext(store, pack.workflow, context)).validation };
      }
      case 'source_status': return skillSourceStatus(await store.snapshot(args.workflow_id, args.revision_hash));
      case 'revisions': return store.revisions(args.workflow_id);
      case 'read_resource': return readEditorResource(store, args);
      case 'write_resource': return writeEditorResource(store, args);
      case 'publish': {
        const pack = await store.snapshot(args.workflow_id, args.expected_revision);
        if(AUTHORING_WORKFLOWS.some(item=>item.id===args.workflow_id))validateStoredAuthoringWorkflow({...pack.workflow,status:'ready'},config.providers,{requireReady:false});
        certificateForPublishedWorkflow({...pack,workflow:publishableEditorWorkflow(pack.workflow)});
        const checked = await this.validationContext(store, { ...publishableEditorWorkflow(pack.workflow), status: 'ready' }, context);
        requireValue(checked.validation.launch_ready, 'WORKFLOW_NOT_READY', 'Workflow is not launch ready', { validation: checked.validation }); store.validationContext = checked.context;
        return publishEditorWorkflow(store, args);
      }
      case 'validate': return (await this.validationContext(store, args.workflow, context)).validation;
      case 'create': {
        if (args.workflow.status === 'ready') {
          const checked = await this.validationContext(store, args.workflow, context);
          requireValue(checked.validation.launch_ready, 'WORKFLOW_NOT_READY', 'Workflow dependencies or structure are invalid', { validation: checked.validation }); store.validationContext = checked.context;
        }
        return store.create(args.workflow, { resources: args.resources, provenance: args.provenance, import_report: args.import_report });
      }
      case 'save': {
        if(AUTHORING_WORKFLOWS.some(item=>item.id===args.workflow_id))validateStoredAuthoringWorkflow(args.workflow,config.providers,{requireReady:false});
        if (args.workflow.status === 'ready') {
          const checked = await this.validationContext(store, args.workflow, context);
          requireValue(checked.validation.valid, 'WORKFLOW_NOT_READY', 'Workflow dependencies or structure are invalid', { validation: checked.validation }); store.validationContext = checked.context;
        }
        requireValue(!['resources','provenance','import_report','purge_history','history_purge'].some(key=>Object.hasOwn(args,key)),
          'WORKFLOW_EDITOR_METADATA','Ordinary editor save cannot mutate immutable Pack metadata, resources or history policy');
        return store.save(args.workflow_id, args.workflow, {expected_revision:args.expected_revision});
      }
      case 'duplicate': return store.duplicate(args.workflow_id, args.new_id, args.name, args.revision_hash);
      case 'rename': return store.rename(args.workflow_id, args.name, args.expected_revision);
      case 'delete': {
        const pack=await store.snapshot(args.workflow_id);
        requireValue(pack.provenance?.kind!=='bundled_authoring_workflow','WORKFLOW_SYSTEM_MANAGED','Built-in authoring Workflows are managed by the plugin and cannot be deleted');
        return store.delete(args.workflow_id,args.expected_revision);
      }
      case 'restore_revision': return store.restore(args.workflow_id, args.revision_hash, args.expected_revision);
      case 'export': {
        const pack = await store.snapshot(args.workflow_id, args.revision_hash); const resources = await store.resources(args.workflow_id, pack.revision_hash);
        return { format: 'codex-agents-workflow-pack-v1', ...pack, resource_data: Object.fromEntries(Object.entries(resources).map(([path, bytes]) => [path, Buffer.from(bytes).toString('base64')])) };
      }
      case 'prepare_environment': {
        const pack=await store.snapshot(args.workflow_id,args.revision_hash);
        const closure=await resolveWorkflowPins(store,pack);
        const environment=await runtime.environmentResolver({executables:[...closure.packs.flatMap(item=>item.workflow.requirements.executables??[]), ...closure.skills.flatMap(skill=>skill.requirements.executables??[])]},{extraDirectories:args.environment_directories??[]});
        if(environment.status==='ready')await this.prepareCodexRegistration(closure);
        if(model)return {status:environment.status,requirements:environment.requirements,
          tools:environment.tools.map(tool=>({name:tool.name,status:tool.status,path:tool.path,
            ...(tool.status==='missing'&&tool.rejections?{rejections:tool.rejections}:{})})),
          missing:environment.missing,installation_performed:environment.installation_performed,
          searched_directory_count:environment.searched_directories.length,
          next_action:environment.status==='ready'?'Start the Workflow directly; startup owns dependency verification and registration.':environment.next_action};
        return environment;
      }
      case 'runtime_dependencies': return readHostRuntimeRegistry(registryPathForConfig(this.configPath));
      case 'register_runtime_dependency': {
        requireValue(human, 'HUMAN_CONFIGURATION_REQUIRED', 'Local dependency locations are registered in the authenticated console');
        return updateRuntimeCandidate(args.requirement,args.path,{registryPath:registryPathForConfig(this.configPath),env:this.env});
      }
      case 'discover_runtime_dependencies': {
        requireValue(human, 'HUMAN_CONFIGURATION_REQUIRED', 'Local dependency discovery belongs to the authenticated console');
        return runtime.environmentResolver({executables:args.executables??[]},{extraDirectories:args.environment_directories??[]});
      }
      case 'recheck_runtime_environment': {const record=await runtime.runs.read(args.run_id);
        return runtime.ensureRuntimeEnvironment(args.run_id,{control_token:args.control_token,expected_sequence:record.sequence,
          node_id:record.state.environment_attention?.node_id,extraDirectories:args.environment_directories??[]});}
      case 'start': {
        let request = { ...args };
        request=await loadWorkflowInputsFile(request,{model});
        const launchPack = await store.snapshot(request.workflow_id, request.revision_hash);
        requireValue(templateKind(launchPack)==='workflow','ROLE_NOT_RUNNABLE','Role templates are assigned to one agent, not started as Workflow Runs');
        const systemAuthoring=AUTHORING_WORKFLOWS.find(item=>item.id===launchPack.workflow.id);
        if(systemAuthoring){
          const sourceId=request.inputs?.source_workflow_id,sourceRevision=request.inputs?.source_revision;
          requireValue(typeof sourceId==='string' && typeof sourceRevision==='string','AUTHORING_SOURCE_REQUIRED','Starting a system authoring Workflow requires source_workflow_id and source_revision inputs');
          const sourcePack=await store.snapshot(sourceId,sourceRevision);
          requireValue(authoringWorkflowForPack(sourcePack).id===systemAuthoring.id,'AUTHORING_WORKFLOW_SOURCE','Selected system authoring Workflow does not accept this source kind');
          const runId=workflowId(request.run_id ?? randomUUID());
          const workspace=await ensureDirectory(join(dirname(this.configPath),'skill-generation-workspaces','job-'+runId));
          return this.call('create_authoring_run',{workflow_id:sourceId,revision_hash:sourcePack.revision_hash,authoring_workflow_id:systemAuthoring.id,authoring_workflow_revision:launchPack.revision_hash,run_id:runId,workspace,routing_rules:await loadRoutingSettings(dirname(this.configPath),config.providers),automatic_generation:true,completion_policy:args.completion_policy,main_actor:request.main_actor ?? 'workflow-authoring-controller'},{human,model});
        }
        if (model && launchPack.workflow.nodes.some(node => node.executor?.kind === 'main')) {
          requireValue(false, 'HOST_MAIN_BRIDGE_REQUIRED', 'This Workflow contains current-main semantic nodes, but the model MCP boundary has no trusted Host delivery/return bridge. No Run was started.');
        }
        const launchClosure=await resolveWorkflowPins(store,launchPack);
        for(const pack of launchClosure.packs)requireHostToolBindings(pack.workflow, this.capabilities.hostToolRegistry ?? {});
        const environment=await runtime.environmentResolver({executables:[...launchClosure.packs.flatMap(item=>item.workflow.requirements.executables??[]),...launchClosure.skills.flatMap(skill=>skill.requirements.executables??[])]},{extraDirectories:request.environment_directories??[],knownDirectories:workspaceRuntimeDirectories(request.workspace)});
        requireValue(environment.status==='ready','ENVIRONMENT_SETUP_REQUIRED','请先准备运行依赖；安装前需要用户同意。',{environment});
        request.revision_hash=launchPack.revision_hash;
        if (request.launch_mode === 'task') {
          requireValue(human,'HUMAN_TASK_LAUNCH','Task launch defaults belong to the human console');
          const pack=await store.snapshot(request.workflow_id,request.revision_hash);
          request.inputs=await prepareTaskInputs({inputs:request.inputs ?? {},schema:pack.workflow.inputs_schema,source:pack.workflow.description,config,directory:dirname(this.configPath),env:this.env});
          request.revision_hash=pack.revision_hash;
          request.run_id = workflowId(request.run_id ?? randomUUID());
          const project = request.workspace || await ensureDirectory(join(dirname(this.configPath),'workflow-workspaces','run-'+request.run_id));
          requireValue(isAbsolute(project) && dirname(resolve(project)) !== resolve(project),'RUN_WORKSPACE','Task project must be an absolute folder, not a drive root');
          await noSymlinks(project);
          request.workspace = resolve(project);
          request.access = 'bounded_write';
          request.allowed_paths = ['.'];
          request.constraints = {...request.constraints,task_workspace:resolve(project)};
          delete request.launch_mode;
        }
        if (human && !request.workspace) {
          request.run_id = workflowId(request.run_id ?? randomUUID());
          request.workspace = await ensureDirectory(join(dirname(this.configPath),'workflow-workspaces','run-'+request.run_id));
          request.access ??= 'read_only';
        }
        const parent=nativeParentThreadId(request,{required:false});
        if(parent)request.constraints={...request.constraints,native_parent_thread_id:parent};
        requireValue(!launchClosure.packs.some(item => hasOrchestrationMain(item.workflow)) || parent, 'MAIN_ORCHESTRATION_CONTEXT', 'Orchestration requires the initiating Codex conversation. No Run was started.');
        return runtime.start(request,{preparedEnvironment:environment});
      }
      case 'begin_main':
      case 'run_main': {
        const {snapshot:pack,resources:rootResources}=await store.snapshotWithResources(args.workflow_id,args.revision_hash);
        requireValue(templateKind(pack)==='workflow','ROLE_NOT_RUNNABLE','Role templates are assigned to one agent, not started as Workflow Runs');
        const closure = await resolveWorkflowPins(store, pack, {rootResources});
        for(const pinned of closure.packs)requireHostToolBindings(pinned.workflow, this.capabilities.hostToolRegistry ?? {});
        const environment = await runtime.environmentResolver({ executables: [...closure.packs.flatMap(item => item.workflow.requirements.executables ?? []), ...closure.skills.flatMap(skill => skill.requirements.executables ?? [])] }, { extraDirectories: args.environment_directories ?? [],knownDirectories:workspaceRuntimeDirectories(args.workspace) });
        if (environment.status !== 'ready') return { status: 'environment_attention', environment: { status: environment.status, tools: environment.tools, missing: environment.missing, next_action: environment.next_action } };
        const { detached_host, ...launchArgs } = args;
        const request = await loadWorkflowInputsFile({ ...launchArgs },{model});
        request.revision_hash=pack.revision_hash;
        const parent=nativeParentThreadId(request,{required:args.native_bridge===true});
        if(parent)request.constraints={...request.constraints,native_parent_thread_id:parent};
        requireValue(!closure.packs.some(item => hasOrchestrationMain(item.workflow)) || parent, 'MAIN_ORCHESTRATION_CONTEXT', 'Start this Workflow from the current Codex conversation: orchestration needs its existing working context. No Run was started.');
        if(args.native_bridge===true)await this.nativeParentVerifier(parent);
        const run = await runtime.start(request,{preparedEnvironment:environment,retainHostAuthority:Boolean(parent)});
        if (parent) await retainOwnedAuthority(runtime, run);
        if (bridgeHooks?.runStarted) await bridgeHooks.runStarted({ run_id: run.run_id, control_token: run.control_token });
        if (operation === 'run_main' && args.return_after_start === true) {
          if(run.status!=='running')return {...run,execution_owner:'workflow_controller',next_action:'workflow_wait',
            next_action_args:{run_id:run.run_id,control_token:run.control_token,timeout_ms:WORKFLOW_WAIT_MS},
            status_check:{tool:'workflow_get',arguments:{run_id:run.run_id}}};
          if (detached_host === true) {
            try {
              if(!parent)await retainOwnedAuthority(runtime,run);
              return await (this.capabilities.launchDetachedHostMain ?? launchDetachedHostMain)({
                configPath: this.configPath, defaultConfigPath: this.defaultConfigPath,
                runId: run.run_id, controlToken: run.control_token, owner: request.main_actor, env: this.env,
              }).then(launched => ({ ...launched, run_id: run.run_id, control_token: run.control_token,
                execution_owner: 'host_main_worker', next_action: 'workflow_wait',
                next_action_args: {run_id:run.run_id,control_token:run.control_token,timeout_ms:WORKFLOW_WAIT_MS},
                status_check: { tool: 'workflow_get', arguments: { run_id: run.run_id } } }));
            } catch (error) {
              await runtime.runs.mutate(run.run_id, 'host_main_worker_start_failed', state => {
                if (state.status === 'running') {
                  state.status = 'failed'; state.error = { code: error.code ?? 'HOST_MAIN_WORKER_START', message: error.message };
                  state.updated_at = new Date().toISOString();
                }
              });
              throw error;
            }
          }
          const launched = await hostMainManager.launchRun({ runtime, drive, runId: run.run_id, controlToken: run.control_token, owner: request.main_actor });
          return { ...launched, run_id: run.run_id, control_token: run.control_token };
        }
        const result=await drive.advanceToMain(run.run_id, { control_token: run.control_token, owner: args.main_actor, request_prefix: `begin-${run.run_id}` });
        if(result.stop_reason==='main_node' && bridgeHooks?.handoffPrepared)await bridgeHooks.handoffPrepared(result);
        if(operation!=='run_main')return result;
        const launched=await hostMainManager.launch({ runtime, drive, handoff: result });
        return {...launched,run_id:run.run_id,control_token:run.control_token};
      }
      case 'main_status': return await hostMainManager.pending(runtime,args.run_id) ?? await readHostMainWorker(this.configPath,args.run_id);
      case 'accept_main': {
        requireValue(human,'HUMAN_MAIN_ACCEPTANCE_REQUIRED','Final Main acceptance belongs to the authenticated human Workbench');
        return hostMainManager.accept({runtime,drive,runId:args.run_id,controlToken:args.control_token,accepted:args.accepted});
      }
      case 'continue_main': {
        if(args.host_owned===true && human) return (this.capabilities.launchDetachedHostMain ?? launchDetachedHostMain)({
          configPath:this.configPath,defaultConfigPath:this.defaultConfigPath,runId:args.run_id,
          controlToken:args.control_token,owner:args.owner,env:this.env});
        const result=await drive.advanceToMain(args.run_id,{control_token:args.control_token,owner:args.owner,request_prefix:args.request_prefix ?? `host-continue-${args.run_id}`});
        return hostMainManager.launch({runtime,drive,handoff:result});
      }
      case 'cleanup_run_history': {
        requireValue(human, 'WORKBENCH_HISTORY_ACTION', 'Use the Workbench to clear completed and failed Run history');
        const result = await runtime.runs.cleanupHistory({ olderThanMs: 0 });
        await appendAuditEvent(this.configPath, { event: 'run-history-cleanup', outcome: 'ok', deleted_count: result.deleted_count }, { effectCommitted: true });
        return result;
      }
      case 'runs': return runtime.runs.list();
      case 'wait': return waitForWorkflow({runId:args.run_id,controlToken:args.control_token,directory:runtime.runs.directory(args.run_id),
        readState:()=>runtime.runs.read(args.run_id),readWorker:record=>hostMainManager.failureWorker(record) ?? readHostMainWorker(this.configPath,args.run_id),
        afterSequence:args.after_sequence,timeoutMs:args.timeout_ms,signal});
      case 'get': {
        const state = await runtime.get(args.run_id);
        const host_worker = await readHostMainWorker(this.configPath,args.run_id);
        return host_worker ? { ...state, host_worker } : state;
      }
      case 'run_snapshot': return runtime.snapshot(args.run_id, args);
      case 'run_definition': return (await runtime.runs.read(args.run_id)).pins.root;
      case 'node_details': {
        const { state, pins } = await runtime.runs.read(args.run_id); const node = pins.root.workflow.nodes.find(item => item.id === args.node_id);
        requireValue(node, 'NODE_MISSING', 'The selected node is not in this Run');
        return { node: structuredClone(node), provider: pins.providers.find(item => item.id === node.executor?.provider_id) ?? null,
          ...(node.executor ? { permissions: nodePermissions(node, state), workspace: nodeWorkspace(node.id, state, pins) } : {}),
          skill_policy: effectiveSkillPolicy(pins.inherited_policy ?? pins.root.workflow.skill_policy, node.skill_policy), pins_hash: state.pins_hash };
      }
      case 'adopt_run': {
        requireValue(human, 'HUMAN_CONTROL_RECOVERY_REQUIRED', 'Only the authenticated local human console can replace a lost main controller');
        return recoverControllerTree(coordinator, this.strictManager, runtime, args, { configPath: this.configPath });
      }
      case 'recover_control': {
        const record=await runtime.runs.read(args.run_id);
        const result=await recoverControllerTree(coordinator,this.strictManager,runtime,conversationalRecovery,{configPath:this.configPath});
        if (!model) return result;
        const authority={run_id:args.run_id,control_token:result.control_token};
        if (isAuthoringRunProvenance(record.pins.root.provenance)) return result.recovery_errors.length
          ?result:authoringControllerContinuation(result,authority,'resume');
        const cancellation=workflowControllerAdapterDescriptor('cancel',authority);
        // Incomplete cleanup offers only shutdown. Runtime resume retains its
        // independent cleanup fence if an earlier adapter is invoked.
        if (result.recovery_errors.length) return {...result,next_action:'workflow_cancel',invocation_adapter:cancellation,
          cancellation_invocation_adapter:cancellation};
        return {...result,next_action:'workflow_resume',invocation_adapter:workflowControllerAdapterDescriptor('resume',authority),
          cancellation_invocation_adapter:cancellation};
      }
      case 'recover_claim': {
        const record = await executor.recoveryPreparation(args.run_id, args);
        requireValue(!record.attempt.dispatch, 'DISPATCH_UNCERTAIN', 'This attempt has dispatch intent; inspect its exact executor instead');
        return reattachAttempt(runtime, args.run_id, args, { kind: 'unsubmitted_claim' });
      }
      case 'reattach_connector': return executor.reattachConnector(args.run_id, args);
      case 'reattach_handoff': {
        const record = await executor.recoveryPreparation(args.run_id, args); const observation = args.reconciliation;
        requireValue(record.pins.root.workflow.skill_policy.mode === 'cooperative' && (record.definition.executor.kind === 'main' || ['native_agent','external_mcp','mcp_tool'].includes(record.provider?.kind)), 'HANDOFF_RECOVERY_UNSUPPORTED', 'This executor requires its dedicated recovery adapter');
        requireValue(record.attempt.dispatch?.receipt && observation && ['active','completed'].includes(observation.outcome) && Array.isArray(observation.evidence) && observation.evidence.length && canonicalJSON(observation.receipt) === canonicalJSON(record.attempt.dispatch.receipt), 'HANDOFF_RECONCILIATION_REQUIRED', 'The main host must inspect the exact original task and attest its unchanged receipt with evidence');
        return reattachAttempt(runtime, args.run_id, args, { kind: 'host_identity_attestation', attempt_id: args.attempt_id, dispatch_request_id: record.attempt.dispatch.request_id,
          receipt: observation.receipt, evidence: observation.evidence, outcome: observation.outcome, independently_verified: false });
      }
      case 'control_connector': return executor.controlConnector(args.run_id, args);
      case 'recover_strict_result': {
        const record = await executor.recoveryPreparation(args.run_id, args);
        requireValue(record.pins.root.workflow.skill_policy.mode === 'strict' && record.attempt.result_proposal && record.attempt.dispatch?.receipt?.executor === 'codex-app-server', 'STRICT_RESULT_PENDING', 'No exact durable Strict proposal exists; an interrupted model turn cannot be resubmitted by recovery');
        const result = await runtime.runs.readExecutorResult(args.run_id, args.attempt_id, record.attempt.result_proposal.sha256);
        requireValue(result.status === 'succeeded' && record.attempt.executor_events?.some(event => event.kind === 'session_state' && event.metadata.status === 'closed'), 'STRICT_SHUTDOWN_UNCONFIRMED', 'Durable proposal needs recorded session shutdown');
        return reattachAttempt(runtime, args.run_id, args, { kind: 'strict_durable_result', attempt_id: args.attempt_id, dispatch_request_id: record.attempt.dispatch.request_id, result_sha256: record.attempt.result_proposal.sha256 });
      }
      case 'reattach_subworkflow':
      case 'child_control': {
        const record = await controllerAttempt(runtime, args.run_id, args);
        requireValue(record.definition.executor?.kind === 'subworkflow', 'SUBWORKFLOW_NODE_REQUIRED', 'This attempt is not a SubWorkflow');
        const identity = childIdentity(args.run_id, args.node_id, args.attempt_id, args.control_token);
        requireValue(record.attempt.child_run_id === identity.run_id, 'CHILD_DISPATCH_REQUIRED', 'No exact child dispatch exists');
        const child = await runtime.runs.read(identity.run_id);
        requireValue(child.pins.parent?.run_id === args.run_id && child.pins.parent.node_id === args.node_id && child.pins.parent.attempt_id === args.attempt_id && child.state.control_hash === digest(identity.control_token), 'CHILD_RUN_CONFLICT', 'Child identity or recovered authority differs');
        if (operation === 'child_control') return { ...await runtime.get(identity.run_id), control_token: identity.control_token };
        const attached = await reattachAttempt(runtime, args.run_id, args, { kind: 'subworkflow_exact_identity', attempt_id: args.attempt_id, dispatch_request_id: record.attempt.dispatch.request_id,
          receipt: { task_id: identity.run_id, child_run_id: identity.run_id }, child_sequence: child.sequence, child_event_hash: child.events.at(-1).hash });
        return { ...attached, child: { ...await runtime.get(identity.run_id), control_token: identity.control_token } };
      }
      case 'next': return runtime.next(args.run_id);
      case 'orchestration_complete': {
        requireValue(model, 'MAIN_ORCHESTRATION_CONTEXT', 'Orchestration completion belongs to the initiating Codex conversation');
        const completed = await completeMainOrchestration(runtime, { ...args, thread_id: modelThreadId }, { executor,signal,expectedOrchestration });
        signal?.throwIfAborted();
        if (['succeeded','failed','cancelled'].includes(completed.status)) return { status: completed.status, completion_satisfied: completed.status === 'succeeded', recovery_required: completed.status === 'failed',...committedTerminalOutput(completed) };
        return this.#call('native_next', { run_id: args.run_id, control_token: args.control_token }, { model, modelThreadId, signal });
      }
      case 'native_next': {
        signal?.throwIfAborted();
        let existing=await runtime.authorizedRun(args.run_id,{control_token:args.control_token});
        const completedHandoff=async pending=>{
          const completed=await pending;
          // Current-Main orchestration already owns the next semantic turn.
          // Keep the exact native drive owner until deterministic Host work
          // reaches that handoff, instead of asking Main for a polling turn.
          if(model&&hasOrchestrationMain(existing.pins.root.workflow)&&completed.status==='running'
            &&completed.next_action==='workflow_native_next')
            return this.#call('native_next',args,{model,modelThreadId,signal});
          return completed;
        };
        if(expectedNativeSpawnBatch)nativeSpawnBatchBinding(existing,{batch_id:expectedNativeSpawnBatch,
          control_token:args.control_token,parent_thread_id:modelThreadId});
        // One public drive owns the sibling loop. Every external checker gets
        // fresh authority; pure journal advancement does not re-enter #call or
        // recompile/reselect the unchanged sealed native dispatch.
        for(let nativeStep=0;nativeStep<1024;nativeStep++){
        const active = existing.pins.root.workflow.nodes.find(node => {
          const provider = existing.pins.providers.find(item => item.id === node.executor?.provider_id);
          const current = existing.state.nodes[node.id];
          return provider?.kind === 'native_agent' && ['claimed','running'].includes(current?.status)
            && current.active_attempt_id && current.attempts.some(item => item.id === current.active_attempt_id && item.dispatch);
        });
        const needsNativeParent=this.nativeAgentObserver&&existing.pins.root.workflow.nodes.some(node=>
          existing.pins.providers.some(provider=>provider.id===node.executor?.provider_id&&provider.kind==='native_agent')&&
          !['succeeded','skipped','cancelled','failed'].includes(existing.state.nodes[node.id]?.status));
        if(needsNativeParent){
          const parent=nativeParentThreadId(existing.state);
          if(!active)await this.nativeParentVerifier(parent);
        }
        if (active) {
          const current = existing.state.nodes[active.id];
          const attempt = current.attempts.find(item => item.id === current.active_attempt_id);
          const lease = { run_id: args.run_id, node_id: active.id, attempt_id: attempt.id,
            lease_token: leaseToken(args.control_token, args.run_id, active.id, attempt.id, attempt.lease_generation ?? 0) };
          const incrementalContinuation=await this.#resumeNativeFollowup(runtime,args,{record:existing,definition:active,
            attempt,binding:lease,executor,maxPromptChars:config.global.max_prompt_chars});
          if(incrementalContinuation)return incrementalContinuation;
          if (attempt.dispatch.receipt) {
            return completedHandoff(this.completeObservedNative(runtime,args,{record:existing,definition:active,attempt,binding:lease,executor,signal,
              maxPromptChars:config.global.max_prompt_chars}));
          }
          const observedProjection=await executor.prepareNativeObservation(args.run_id,{...lease,control_token:args.control_token},existing,config);
          requireValue(digest(canonicalJSON(observedProjection))===attempt.dispatch.envelope_hash,
            'NATIVE_AGENT_HANDOFF_CHANGED','Observed native projection differs from its sealed dispatch');
          const serial = active.fanout?.scheduling === 'serial';
          const capped = active.fanout?.scheduling === 'parallel' && active.fanout.max_concurrency;
          const activeSlots=activeNativeAssignmentSlots(existing,active,attempt);
          const completedSerial=attempt.native_serial_results?.length??0;
          const nextIndex = activeSlots[completedSerial];
          const count = activeSlots.length;
          // An all-inherited retry has no runnable packet to materialize. It
          // still owns a fresh completion interval, before sealing any receipt.
          // Reuse the ordinary baseline guards; never synthesize after a spawn.
          if(count===0&&existing.pins.native_dispatch_span_version===1&&!attempt.native_dispatch_span)
            await prepareNativeSpan(runtime,existing,active,{...lease,control_token:args.control_token},observedProjection,
              resolvedSubagentPlan(active,existing.state));
          const seal=()=>completedHandoff(this.#sealNativeDispatch(runtime,{...args,attempt_id:attempt.id},{executor,signal,
            maxPromptChars:config.global.max_prompt_chars}));
          if (serial && completedSerial === count) return seal();
          const parallelResults=attempt.native_parallel_results??{};
          const observe=async pending=>{
            if(!this.nativeAgentObserver)return null;
            let observed=await this.inspectNativeAgents(runtime,args,active,attempt,pending.map(([,id])=>id),{signal});
            if(!observed)return null;
            const found=pending.find(([,id])=>id===observed.agent_id);
            requireValue(found,'NATIVE_AGENT_IDENTITY','Observed native Agent is not in this active dispatch');
            if(observed.status==='amendment')observed=await this.mergeObservedNativeAmendment(runtime,args,{definition:active,attempt,binding:lease,index:Number(found[0]),observed});
            if(observed.status==='blocked'||observed.status==='invalid')return await this.rejectedNativeOutcome(runtime,args,
              {definition:active,attempt,binding:lease,index:Number(found[0]),observed,executor,
                category:observed.status,reason:observed.reason})??this.#call('native_next',args,{model,signal});
            requireValue(observed.status==='completed','NATIVE_AGENT_OBSERVATION','Host observer did not return a completed Agent');
            if(active.fanout?.result_mode==='per_item'){
              const accepted=await this.recordObservedNativeItems(runtime,args,{definition:active,attempt,binding:lease,
                index:Number(found[0]),observed,executor,record_terminal_turn:true});
              if(accepted.rejection)return accepted.rejection;
              if(accepted.retry)return this.#call('native_next',args,{model,signal});
              if(accepted.continuation){
                const fresh=await runtime.runs.read(args.run_id);
                const currentAttempt=fresh.state.nodes[active.id].attempts.find(item=>item.id===attempt.id);
                return this.#incrementalNativeContinuation(runtime,args,{record:fresh,definition:active,attempt:currentAttempt,
                  binding:lease,index:Number(found[0]),agentId:observed.agent_id,turnId:observed.turn_id,
                  maxPromptChars:config.global.max_prompt_chars,executor});
              }
              return {native_continue:true};
            }
            const resultArgs={...lease,control_token:args.control_token,index:Number(found[0]),
              agent_id:observed.agent_id,turn_id:observed.turn_id,result:observed.result};
            try{
              if(serial)await runtime.recordNativeSerialResult(args.run_id,resultArgs);
              else await runtime.recordNativeParallelResult(args.run_id,resultArgs);
            }catch(error){if(error.code!=='DATA_INVALID')throw error;
              return await this.rejectedNativeOutcome(runtime,args,{definition:active,attempt,binding:lease,index:Number(found[0]),
                observed,executor,category:'invalid',reason:error.message})??this.#call('native_next',args,{model,signal});}
            return {native_continue:true};
          };
          if(capped&&Object.keys(parallelResults).length===count)return seal();
          if (serial && attempt.native_agents?.[nextIndex]) {
            const outcome=await observe([[String(nextIndex),attempt.native_agents[nextIndex]]]);
            if(outcome?.native_continue){requireValue(nativeStep<1023,'NATIVE_DRIVE_LIMIT','Native sibling drive exceeded its bound');existing=await runtime.authorizedRun(args.run_id,{control_token:args.control_token});continue;}
            return outcome;
          }
          const spawned=Object.keys(attempt.native_agents??{}).length;
          const activeCount=spawned-Object.keys(parallelResults).length;
          if(!serial&&!capped&&spawned===count)return seal();
          if(capped&&(activeCount>=active.fanout.max_concurrency||spawned===count)){
            const pending=Object.entries(attempt.native_agents??{}).filter(([index])=>!parallelResults[index]);
            const outcome=this.parallelNativeItemCollection(existing,active,pending)
              ?(await this.collectObservedNativeItems(runtime,args,{record:existing,definition:active,attempt,binding:lease,pending,executor,signal,record_terminal_turn:true})).outcome
              :await observe(pending);
            if(outcome?.native_continue){requireValue(nativeStep<1023,'NATIVE_DRIVE_LIMIT','Native sibling drive exceeded its bound');existing=await runtime.authorizedRun(args.run_id,{control_token:args.control_token});continue;}
            return outcome;
          }
          const releasedIndices=serial ? nextIndex : capped
            ?activeSlots.filter(index=>!attempt.native_agents?.[index]).slice(0,active.fanout.max_concurrency-activeCount)
            :active.fanout?.result_mode==='per_item'?activeSlots.filter(index=>!attempt.native_agents?.[index]):null;
          const prepared = await executor.prepare(args.run_id, { ...lease, control_token: args.control_token });
          requireValue(digest(canonicalJSON(prepared)) === attempt.dispatch.envelope_hash,
            'NATIVE_AGENT_HANDOFF_CHANGED', 'The active native handoff no longer matches its pinned dispatch intent');
          const packet = await this.#nativeSpanHandoff(runtime,args,existing, active, lease, { ...prepared,
            handoff_required: true, compiled_prompt: prepared.prompt, request_id: attempt.dispatch.request_id }, config.global.max_prompt_chars,
            releasedIndices,
            {resourceRoot:join(runtime.runs.directory(args.run_id),'objects')});
          packet.packets = packet.packets.filter(item => !attempt.native_agents?.[item.index]);
          if(model)await this.persistModelSpawnWindow(runtime,args,existing,lease,packet);
          return { status: 'native_handoff', ...packet,
            ...(model?nativeBatchToJournal(args.run_id,args.control_token,attempt.id,packet.packets.map(item=>item.index)):{}),
            recorded_agent_ids: attempt.native_agents ?? {},
            recovery: 'Inspect the current task for any spawn_agent call not yet journaled before spawning a remaining slot.' };
        }
        break;
        }
        const progress = await drive.advanceToMain(args.run_id, { control_token: args.control_token,
          owner: existing.state.main_actor, request_prefix: `native-${args.run_id}` });
        const joinHostMain=async()=>{
          const settled = await hostMainManager.wait(args.run_id);
          if (['failed', 'audit_or_cleanup_failed'].includes(settled.status))
            return this.#call('wait', { ...args, timeout_ms: WORKFLOW_WAIT_MS }, { model, signal });
          return this.#call('native_next',args,{model,signal});
        };
        if(progress.stop_reason==='main_execution_pending')return model?joinHostMain():progress;
        if (progress.stop_reason === 'main_orchestration') return prepareMainOrchestration(runtime, { ...args, thread_id: existing.state.constraints.native_parent_thread_id });
        if (progress.stop_reason === 'main_node') {
          const launched=await hostMainManager.launch({ runtime, drive, handoff: progress });
          // A model-facing continuation remains suspended inside the Host until
          // this exact Main job settles.  This prevents a second model turn from
          // colliding with its durable receipt or polling Run state.
          return model?joinHostMain():launched;
        }
        if (progress.stop_reason !== 'non_main_semantic') return progress;
        const record = await runtime.runs.read(args.run_id);
        const definition = record.pins.root.workflow.nodes.find(node => node.id === progress.node_id);
        const provider = record.pins.providers.find(item => item.id === definition?.executor?.provider_id);
        requireValue(definition?.executor?.kind === 'provider' && provider?.kind === 'native_agent',
          'NATIVE_AGENT_REQUIRED', 'The next semantic node is not a native Agent handoff');
        requireValue(effectiveSkillPolicy(record.pins.inherited_policy ?? record.pins.root.workflow.skill_policy, definition.skill_policy).mode === 'cooperative',
          'NATIVE_AGENT_POLICY', 'Strict nodes require their existing isolated executor, not a cooperative native subagent');
        const lease = await runtime.claimNode(args.run_id, { node_id: definition.id, owner: record.state.main_actor,
          request_id: `native-${definition.id}-${record.sequence}`, control_token: args.control_token });
        const dispatched = await executor.dispatch(args.run_id, { ...lease, control_token: args.control_token });
        const claimed = await runtime.runs.read(args.run_id);
        const claimedAttempt=claimed.state.nodes[definition.id].attempts.find(item=>item.id===lease.attempt_id);
        const activeSlots=activeNativeAssignmentSlots(claimed,definition,claimedAttempt);
        if(!activeSlots.length){
          await prepareNativeSpan(runtime,claimed,definition,{...lease,control_token:args.control_token},dispatched,
            resolvedSubagentPlan(definition,claimed.state));
          return completedHandoff(this.#sealNativeDispatch(runtime,{...args,attempt_id:lease.attempt_id},{executor,signal,
            maxPromptChars:config.global.max_prompt_chars}));
        }
        const initialIndices=definition.fanout?.scheduling === 'serial' ? activeSlots[0] : definition.fanout?.max_concurrency
          ? activeSlots.slice(0,definition.fanout.max_concurrency)
          : definition.fanout?.result_mode==='per_item'?activeSlots:null;
        const packet=await this.#nativeSpanHandoff(runtime,args,claimed, definition, lease, dispatched, config.global.max_prompt_chars,
          initialIndices,{resourceRoot:join(runtime.runs.directory(args.run_id),'objects')});
        if(model)await this.persistModelSpawnWindow(runtime,args,claimed,lease,packet);
        return { status: 'native_handoff', ...packet,
          ...(model?nativeBatchToJournal(args.run_id,args.control_token,lease.attempt_id,packet.packets.map(item=>item.index)):{} ) };
      }
      case 'native_spawned_batch': {
        requireValue(model,'NATIVE_MODEL_BRIDGE_REQUIRED','Native spawn acknowledgement is owned by the authenticated model bridge');
        const initial=nativeSpawnBatchBinding(await runtime.runs.read(args.run_id),{batch_id:args.batch_id,
          control_token:args.control_token,parent_thread_id:modelThreadId});
        for(const spawn of initial.receipt.identity.spawns){
          if(initial.receipt.acknowledged_indices.includes(spawn.index))continue;
          await runtime.recordNativeExecutorEvent(args.run_id,{...initial.binding,event:{kind:'native_agent_spawn',
            metadata:{index:spawn.index,agent_id:spawn.agent_id,batch_id:initial.receipt.batch_id}}});
        }
        // The public call already resolved this exact thread's authority.
        // Continue its drive directly; #call performs fresh execution checks
        // and validates the batch, without rescanning unrelated histories.
        const next=await this.#nativeDrive(args,{model,modelThreadId,signal},()=>this.#call('native_next',args,
          {model,modelThreadId,signal,expectedNativeSpawnBatch:initial.receipt.batch_id}));
        return {...next,journaled_spawn_count:initial.receipt.identity.spawns.length,
          acknowledged_batch_id:initial.receipt.batch_id};
      }
      case 'native_followed_up': {
        const { attempt,binding }=await nativeAttemptBinding(runtime,args);
        const pending=structuredClone(attempt.native_pending_followup);
        requireValue(pending,'NATIVE_AGENT_FOLLOWUP','No Host-persisted follow-up intent awaits acknowledgement');
        await runtime.recordNativeExecutorEvent(args.run_id,{...binding,event:{kind:'native_agent_followup',metadata:{}}});
        if(model){
          const next=await this.#nativeDrive(args,{model,modelThreadId,signal},()=>this.#call('native_next',args,
            {model,modelThreadId,signal}));
          return {...next,journaled_followup:{index:pending.index,agent_id:pending.agent_id,item_index:pending.item_index}};
        }
        return {run_id:args.run_id,node_id:binding.node_id,attempt_id:binding.attempt_id,index:pending.index,
          agent_id:pending.agent_id,item_index:pending.item_index,recorded:true,
          ...nativeContinuation(args.run_id,args.control_token)};
      }
      case 'drive': {
        const resumed=await this.resumeAutomaticAuthoring(args,{store,runtime,context});if(resumed)return resumed;
        const record = await runtime.runs.read(args.run_id);
        if (isAuthoringRunProvenance(record.pins.root.provenance)) {
          const result=await advanceGeneration(this,runtime,executor,args,{store,context});
          return model&&['generating','reviewing','host_compiling','repairing'].includes(result.phase)
            ?authoringControllerContinuation(result,args):result;
        }
        if (model && record.pins.root.workflow.nodes.some(node => node.executor?.kind === 'main')) {
          requireValue(false, 'HOST_MAIN_BRIDGE_REQUIRED', 'This Run requires a trusted current-main Host bridge; model-driven lifecycle transcription is forbidden. This workflow_drive call did not claim or dispatch a node; inspect workflow_get.host_worker for the detached Host worker.');
        }
        return drive.advance(args.run_id, args);
      }
      case 'claim_node': {
        if(['graph_assembly','final'].includes(args.node_id))await prepareAuthoringReview(runtime,args,{store,context});
        return runtime.claimNode(args.run_id, args);
      }
      case 'complete_node': return runtime.completeNode(args.run_id, args);
      case 'fail_node': {
        await runtime.execution(args.run_id, args, { allowPaused: true });
        WorkflowRuntime.assertNodeFailure(args.error);
        await coordinator.drainAttempt(args.run_id,args.node_id,args.attempt_id,{authorization:args});
        const result = await runtime.failNode(args.run_id, args, (runId, nodeId, attemptId) => coordinator.fenceAttempt(runId, nodeId, attemptId));
        await coordinator.waitDrain(args.run_id);
        return result;
      }
      case 'retry_node': {
        const record = await runtime.authorizedRetryRun(args.run_id,args);
        const previous = record.state.nodes[args.node_id]?.attempts.at(-1);
        if (previous) try { await coordinator.drainAttempt(args.run_id,args.node_id,previous.id,{authorization:{control_token:args.control_token},retry:true}); }
        catch (error) { if (['EXECUTION_OWNER_ACTIVE', 'FAIL_NODE_STOP_INCOMPLETE'].includes(error.code)) error.code = 'RETRY_OWNER_ACTIVE'; throw error; }
        if (record.state.status !== 'failed') return runtime.retryNode(args.run_id, args);
        await coordinator.waitDrain(args.run_id);
        await coordinator.assertRunQuiescent(record);
        const result = await runtime.retryNode(args.run_id, args);
        this.attemptAdmission.releaseRun(args.run_id);
        return result;
      }
      case 'approve': return runtime.approve(args.run_id, args);
      case 'pause': return runtime.pause(args.run_id, args);
      case 'resume': {
        const record = await runtime.runs.read(args.run_id);
        let result;
        if (!this.attemptAdmission.fencedRuns.has(args.run_id)) {
          if (record.state.status === 'running' && args.after_restart !== true) {
            await runtime.authorizeController(args.run_id, { control_token: args.control_token });
            result = await runtime.get(args.run_id);
          } else result = await runtime.resume(args.run_id, args);
        } else {
          requireValue(record.state.control_recovery && !record.state.control_recovery.errors?.length,
            'CONTROL_RECOVERY_INCOMPLETE', 'Recovered execution cannot resume with unresolved cleanup errors');
          await coordinator.assertRunQuiescent(record, { allowPausedChildren: true });
          result = await runtime.resume(args.run_id, args);
          this.attemptAdmission.releaseRun(args.run_id);
        }
        if(model&&isAuthoringRunProvenance(record.pins.root.provenance)&&result.status==='running')
          return authoringControllerContinuation(result,args);
        return resumeDetachedHostMain(this, runtime, args, result);
      }
      case 'cancel': {
        let ids; const errors = []; const authorities = new Map();
        try { ids = await runtime.cancelTree(args.run_id, args, (id, token) => { authorities.set(id, token); coordinator.fenceRun(id); }); }
        catch (error) { if (!error.fenced_run_ids) throw error; ids = error.fenced_run_ids; errors.push(error); }
        // An unreadable child journal cannot prevent shutdown of its exact
        // already-fenced owned session or the other independently known children.
        const stopped = await Promise.allSettled([...ids.flatMap(id => [this.strictManager.stopRun(id), this.managedNativeManager.stopRun(id), this.hostMainManager.stopRun(id), waitForDetachedHostMainStop(this.configPath, id)]), ...[...authorities].flatMap(([id, token]) => [executor.cancelPendingConnectors(id, token), executor.cancelPendingHostTools(id, token), executor.cancelPendingDirectApi(id, token)])]);
        errors.push(...stopped.filter(item => item.status === 'rejected').map(item => item.reason));
        if (errors.length) throw Object.assign(new AggregateError(errors, 'Run tree was fenced but some executors have unconfirmed cancellation'), { code: 'RUN_CANCEL_INCOMPLETE', details: { failures: errors.map(error => ({ code: error.code ?? 'EXECUTOR_STOP_FAILED', message: error.message })) } });
        return runtime.get(args.run_id);
      }
      case 'events': return runtime.events(args.run_id, args);
      case 'dispatch': {
        if(['graph_assembly','final'].includes(args.node_id))await prepareAuthoringReview(runtime,args,{store,context});
        return executor.dispatch(args.run_id, args);
      }
      case 'strict_status': return this.strictManager.status(runtime, args.run_id, args);
      case 'strict_login': {
        requireValue(human, 'HUMAN_AUTHENTICATION_REQUIRED', 'Managed login URLs are available only to the authenticated human console');
        return this.strictManager.login(runtime, args.run_id, args);
      }
      case 'collect_strict': return this.strictManager.collect(runtime, args.run_id, args);
      case 'cleanup_strict_orphans': return this.strictManager.cleanupOrphans(runtime, args.run_id, args);
      case 'dispatch_receipt': return runtime.recordDispatchReceipt(args.run_id, args);
      case 'record_usage': return runtime.recordUsage(args.run_id, args);
      case 'reconcile_connector': return executor.reconcileConnector(args.run_id, args);
      case 'collect_connector': return executor.collectConnector(args.run_id, args);
      case 'collect_subworkflow': return runtime.collectSubworkflow(args.run_id, args);
      case 'prepare_integration': return this.parallelManager.prepareIntegration(runtime, args.run_id, args);
      case 'review_integration': return this.parallelManager.review(runtime, args.run_id, args);
      case 'integrate_parallel': return this.parallelManager.integrate(runtime, args.run_id, args);
      case 'cleanup_parallel': return this.parallelManager.cleanup(runtime, args.run_id, args);
      default: throw Object.assign(new Error(`Unknown Workflow operation: ${operation}`), { code: 'WORKFLOW_OPERATION' });
    }
  }
}
