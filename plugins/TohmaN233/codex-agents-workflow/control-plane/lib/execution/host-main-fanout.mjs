import {join,resolve,relative,isAbsolute,sep} from 'node:path';
import {mkdir,lstat,realpath,writeFile} from 'node:fs/promises';
import {randomUUID} from 'node:crypto';
import {requireValue} from '../workflow-paths.mjs';
import {canonicalJSON,digest} from '../workflow-revisions.mjs';
import {validateData} from '../workflow-data-schema.mjs';
import {resolvedSubagentPlan} from '../workflow-runtime.mjs';
import {assignedFanoutIndices,assignedFanoutWritePaths,projectFanoutInputs} from './fanout-input-projection.mjs';
import {prepareHostMainContext} from './node-input-materials.mjs';
import {createWorkflowResourceBroker,loadNodeSkillSnapshots} from './workflow-resource-broker.mjs';
import {snapshotWorkspace,changedWorkspacePaths} from './workspace-snapshot.mjs';
import {rejectWorkspaceScope} from './workspace-scope-evidence.mjs';
import {strictAgentOutputSchema,hostResultProposalEnvelope} from './host-main-automation.mjs';
import {createHostAuthBroker} from './codex-host-auth.mjs';
import {codexQualification} from './strict-config.mjs';
import {augmentedRuntimeEnvironment} from '../runtime-environment-state.mjs';
import {currentRoundAttempts} from './completion-turn-budget.mjs';
import {persistCodexCommandAudits} from './codex-result-evidence.mjs';
import {normalizeHostMainCodexEvent} from './host-main-codex-events.mjs';
import {executeWorkerHostCheck,requireWorkerHostCheckScope,workerHostCheckCorrectionPrompt} from './worker-host-check.mjs';
import {hostToolContracts} from './host-tool-runner.mjs';
import {prepareCodexNormalPrefix} from './codex-session.mjs';
import {createCodexCommandBroker} from './codex-command-broker.mjs';
import {ownedCommandDeclarations} from './owned-command-declarations.mjs';
import {OWNED_MCP_NAMESPACE} from './owned-tool-mcp.mjs';
import {createTypedBatchOutputTransport} from './typed-batch-output-transport.mjs';
import {applyTextAmendment,textAmendmentSchema} from './native-text-amendment.mjs';

const within=(path,root)=>{const key=value=>process.platform==='win32'?value.toLowerCase():value;path=key(path);root=key(root);return root==='.'||path===root||path.startsWith(root+'/');};
async function settleAll(values,action,label){
  const settled=await Promise.allSettled(values.map(action)),errors=settled.filter(item=>item.status==='rejected').map(item=>item.reason);
  if(errors.length)throw new AggregateError(errors,label);
}
async function quiesceBroker(broker){
  broker.revoke();
  const outcome=await broker.quiesce();
  if(outcome?.error)throw outcome.error;
  requireValue(outcome?.quiescent===true&&broker.isQuiescent()===true,
    'CODEX_BROKER_STOP_UNCONFIRMED','Main item broker effects have not settled');
}

function requireInputIdentity(audit,text,schema,transport,declarations=null){
  const original=[{type:'text',text}],originalHash=digest(canonicalJSON(original));
  if(!transport){requireValue(audit?.input_sha256===originalHash,'HOST_MAIN_INPUT_MISMATCH','Main input differs from exact Host task');return;}
  const prepared=transport.prepare(text,schema),transported=[{type:'text',text:prepared.text}],wire=declarations?[...transported,declarations.input]:transported;
  requireValue(prepared.schema_sha256===transport.api_schema_sha256&&audit?.semantic_input_sha256===originalHash
    &&audit.transported_semantic_input_sha256===digest(canonicalJSON(transported))
    &&audit.response_transport?.api_schema_sha256===transport.api_schema_sha256
    &&audit.response_transport.semantic_schema_sha256===digest(canonicalJSON(schema))
    &&audit.input_sha256===digest(canonicalJSON(wire))&&audit.submitted_input_sha256===audit.input_sha256
    &&(declarations?audit.owned_command_declarations&&canonicalJSON(audit.owned_command_declarations)===canonicalJSON(declarations.audit):!Object.hasOwn(audit,'owned_command_declarations')),
    'HOST_MAIN_INPUT_MISMATCH','Shared-prefix semantic, transport or actual submitted input differs from exact Host task');
}

/** Explicit factoring only: canonical equality is checked after item projection. */
export function sharedPrefixInputProjection(envelope,items,declaration){
  const names=declaration?.common_inputs;
  requireValue(Array.isArray(names)&&names.length<=32&&new Set(names).size===names.length
    &&names.every(name=>typeof name==='string'&&Object.hasOwn(envelope.inputs,name)),
    'HOST_MAIN_PREFIX_INPUT','Shared prefix common inputs must name unique bound inputs');
  const projected=items.map(item=>projectFanoutInputs(envelope.inputs,items,[item])),common={};
  for(const name of names){
    requireValue(projected.every(input=>canonicalJSON(input[name])===canonicalJSON(projected[0][name])),
      'HOST_MAIN_PREFIX_INPUT',`Shared input ${name} differs between item projections`);
    common[name]=structuredClone(projected[0][name]);
  }
  for(const name of ['task','context','verification'])if(Object.hasOwn(envelope.inputs,name)&&new RegExp(`\\{\\{\\s*${name}\\s*\\}\\}`).test(envelope.prompt_template??''))
    requireValue(names.includes(name),'HOST_MAIN_PREFIX_TEMPLATE',`Shared template input ${name} must be explicitly common`);
  return {common,items:projected.map(input=>Object.fromEntries(Object.entries(input).filter(([name])=>!names.includes(name))))};
}

/** Bounded Main item sessions retain the same logical Main authority and lifecycle. */
export async function executeHostMainFanout(manager,entry,{record,envelope,binding,definition,settings,resources,authorize,assertActive,resolveModelSelection}){
  const {runtime,runId}=entry,fanout=definition.fanout,plan=resolvedSubagentPlan(definition,record.state);
  requireValue(envelope.skill_policy.mode==='cooperative'&&fanout.result_mode==='per_item','HOST_MAIN_FANOUT','Main fan-out requires Cooperative per-item execution');
  const attempt=record.state.nodes[definition.id].attempts.find(item=>item.id===binding.attempt_id);
  const accepted=structuredClone(attempt.main_item_results??{}),usages=[],turns=[],writes=new Set();
  const assignments=plan.assignments.map((_items,index)=>{
    const indices=assignedFanoutIndices(plan,fanout,index).filter(itemIndex=>!accepted[itemIndex]);
    return {index,indices,items:indices.map(itemIndex=>plan.items[itemIndex]),dispatch_id:`host-main-${binding.attempt_id}-${index}`};
  }).filter(item=>item.indices.length);
  if(fanout.shared_prefix&&assignments.length)requireValue(manager.prefixFactory.usageCapability?.complete_usage===true,
    'HOST_MAIN_PREFIX_USAGE_UNSUPPORTED',`Shared-prefix execution requires complete usage observation before setup: ${manager.prefixFactory.usageCapability?.reason??'prefix_factory_has_no_qualified_usage_capability'}`);
  const capability=manager.prefixFactory.usageCapability,hasTransport=Boolean(fanout.shared_prefix&&capability&&Object.hasOwn(capability,'responseTransport'));
  const itemOutputSchema=strictAgentOutputSchema(definition.outputs_schema.properties[fanout.result_output].items);
  const amendmentConfig=definition.completion_contract?.host_check?.text_amendment;
  const repairSchema=amendmentConfig?strictAgentOutputSchema(textAmendmentSchema(amendmentConfig)):undefined;
  let responseTransport=hasTransport?capability.responseTransport:null;
  const setupSchema=prepareCodexNormalPrefix.usageCapability.responseTransport.setup_schema;
  const typedTransport=Boolean(responseTransport&&Object.hasOwn(responseTransport,'create_for_schema'));
  if(typedTransport){
    requireValue(responseTransport.create_for_schema===createTypedBatchOutputTransport,
      'HOST_MAIN_PREFIX_TRANSPORT','Live common batch must use the registered typed result transport');
    responseTransport=responseTransport.create_for_schema(itemOutputSchema,{repair_schema:repairSchema});
  }else if(hasTransport)requireValue(responseTransport&&typeof responseTransport.prepare==='function'
    &&responseTransport.api_schema_sha256===prepareCodexNormalPrefix.usageCapability.responseTransport.api_schema_sha256
    &&responseTransport.setup_schema===setupSchema,'HOST_MAIN_PREFIX_TRANSPORT','Shared-prefix transport must declare the fixed API and canonical setup schema');
  // Resolve and guard the complete original plan before any session factory.
  const event=(kind,metadata)=>runtime.recordExecutorEvent(runId,{...binding,event:{kind,metadata}});
  const itemScopes=new Map();
  // Validate every original item, including inherited results. A command sandbox
  // grants an entire cwd directory, so a narrower file/subdirectory grant cannot
  // safely be promoted to a worker root.
  for(const [itemIndex,item] of plan.items.entries()){
    const itemPaths=assignedFanoutWritePaths({workspace:envelope.workspace,nodeAllowedPaths:envelope.effective_allowed_paths,assignedItems:[item],fanout});
    let cwd=envelope.workspace,rootPath='.';
    if(envelope.access==='bounded_write'){
      requireValue(typeof fanout.workspace_field==='string'&&typeof item[fanout.workspace_field]==='string'&&item[fanout.workspace_field].trim(),
        'HOST_MAIN_WORKSPACE_ISOLATION','Writable Main fan-out requires a Host-owned per-item workspace directory');
      cwd=resolve(envelope.workspace,item[fanout.workspace_field]);rootPath=relative(envelope.workspace,cwd).replaceAll('\\','/');
      requireValue(rootPath&&rootPath!=='..'&&!rootPath.startsWith('../')&&!isAbsolute(rootPath)&&itemPaths.some(path=>within(rootPath,path))&&itemPaths.every(path=>within(path,rootPath)),
        'HOST_MAIN_WORKSPACE_ISOLATION','Each Main worker must own exactly its complete isolated workspace directory');
      const actual=await realpath(cwd),same=(a,b)=>process.platform==='win32'?a.toLowerCase()===b.toLowerCase():a===b;
      requireValue((await lstat(cwd)).isDirectory()&&same(actual,cwd),'HOST_MAIN_WORKSPACE_ISOLATION','Main worker workspace must be an existing physical directory');
      let ancestor=cwd;
      while(!same(ancestor,resolve(envelope.workspace))){requireValue(!(await lstat(ancestor)).isSymbolicLink(),'HOST_MAIN_WORKSPACE_ISOLATION','Main worker workspace cannot traverse links');ancestor=resolve(ancestor,'..');}
    }
    itemScopes.set(itemIndex,{cwd,rootPath,itemPaths});
  }
  if(definition.completion_contract?.host_check)requireWorkerHostCheckScope(hostToolContracts(record.pins.root.workflow).get(definition.completion_contract.host_check.tool),{access:envelope.access,allowed_paths:['.']});
  // Item roots must be disjoint even within a partition, since a previously
  // accepted item is an immutable sibling on retry.
  const roots=[...itemScopes.values()];
  if(envelope.access==='bounded_write')for(let i=0;i<roots.length;i++)for(let j=i+1;j<roots.length;j++)requireValue(!within(roots[i].rootPath,roots[j].rootPath)&&!within(roots[j].rootPath,roots[i].rootPath),'HOST_MAIN_WORKSPACE_ISOLATION','Main fan-out item workspace directories overlap');
  const shared=fanout.shared_prefix?sharedPrefixInputProjection(envelope,plan.items,fanout.shared_prefix):null;
  const commonDirectory=join(envelope.workspace,'work','.workflow-runtime','host-main',runId,binding.attempt_id,'shared-prefix');
  const commonMaterial=shared&&assignments.length?await prepareHostMainContext({directory:commonDirectory,
    envelope:{...envelope,inputs:shared.common,subagents:null},resources}):null;
  const materials=new Map();
  for(const assignment of assignments)for(const itemIndex of assignment.indices){
    const scope=itemScopes.get(itemIndex),itemEnvelope={...envelope,inputs:shared?shared.items[itemIndex]:projectFanoutInputs(envelope.inputs,plan.items,[plan.items[itemIndex]]),effective_allowed_paths:scope.itemPaths,subagents:null,
      ...(shared?{prompt_template:'',resources:[],context_projection:{references:[]},completion_contract:undefined}:{})};
    const directory=envelope.access==='bounded_write'?join(scope.cwd,'.workflow-main-inputs',runId,binding.attempt_id):join(envelope.workspace,'work','.workflow-runtime','host-main',runId,binding.attempt_id,`item-${itemIndex}`);
    const material=await prepareHostMainContext({directory,envelope:itemEnvelope,resources:shared?[]:resources});materials.set(itemIndex,material);
    await event('node_input_materials',{index:itemIndex,inputs_path:material.preparation_path,manifest_sha256:material.preparation_sha256,prompt_sha256:material.prompt_sha256,input_count:material.audit.bound_input_count});
  }
  const snapshot=()=>snapshotWorkspace(envelope.workspace,{access:envelope.access,allowedPaths:envelope.effective_allowed_paths,requiredPaths:(definition.required_artifacts??[]).map(item=>item.path),codePrefix:'HOST_MAIN',onUnreadable:metadata=>event('workspace_unreadable_authorized_path',{...metadata,phase:'fanout'})});
  const before=await snapshot(),allowedSkills=await loadNodeSkillSnapshots(runtime,runId,envelope);
  entry.sessions=[];entry.brokers=[];entry.poolResourceVersion=0;
  // Existing Main cancellation and coordinator paths own every pool resource.
  entry.prefixOwner=null;
  entry.session={interrupt:()=>settleAll([...entry.sessions,...(entry.prefixOwner?[entry.prefixOwner]:[])],session=>session.interrupt?.(),'Main item interruption failed'),close:async()=>{
    await settleAll(entry.sessions,session=>session.close(),'Main item closure failed');
    if(entry.prefixOwner)await entry.prefixOwner.close();
  }};
  entry.broker={revoke:()=>{for(const broker of entry.brokers)broker.revoke();},isQuiescent:()=>entry.brokers.every(broker=>broker.isQuiescent()===true),quiesce:async()=>{await settleAll(entry.brokers,quiesceBroker,'Main item broker cleanup failed');return {quiescent:entry.broker.isQuiescent()};}};
  if((settings.authentication.mode==='host_chatgpt'||shared)&&manager.hostAuthBinary!==settings.codex_binary){manager.hostAuth?.clear();manager.hostAuth=createHostAuthBroker({binary:settings.codex_binary,cwd:manager.parent,env:manager.env});manager.hostAuthBinary=settings.codex_binary;}
  const receipt={invocation_id:`host-main-${binding.attempt_id}`,executor:'codex-app-server-host-main',executable_sha256:settings.binary_sha256,main_actor:record.state.main_actor,session_id:`logical-main-${runId}`,call_chain_id:`workflow-run-${runId}`,
    subagent_dispatch_ids:assignments.map(item=>item.dispatch_id),subagent_plan:{resolved_count:assignments.length,input_sha256:digest(canonicalJSON(plan.items)),assignments:assignments.map(item=>({assignment_index:item.index,dispatch_id:item.dispatch_id,items_sha256:digest(canonicalJSON(item.items))}))}};
  await runtime.recordHostMainDispatchReceipt(runId,{...binding,request_id:`dispatch-${binding.attempt_id}`,receipt});
  await event('session_state',{status:'running'});
  // The first owned discovery session selects the initiating Main model; every
  // sibling waits for that exact selection rather than opening an observer.
  let selection;
  const select=client=>{selection??=Promise.resolve().then(()=>resolveModelSelection(client)).then(value=>{requireValue(typeof value?.model==='string'&&value.model.trim()&&typeof value?.effort==='string'&&value.effort.trim(),'HOST_MAIN_MODEL_SELECTION_UNRESOLVED','Main item sessions require the resolved initiating model and reasoning selection');return structuredClone(value);});return selection.then(value=>structuredClone(value));};
  const schema=definition.outputs_schema.properties[fanout.result_output].items;
  let next=0,attemptedTurns=0;const failures=[];
  let preparedPrefix;
  if(commonMaterial){
    let setup,sourceBroker;
    try{
      await authorize();assertActive();await runtime.reserveHostMainPrefixTurn(runId,binding);attemptedTurns++;
      // Prepare the original node's callable catalog, including materialization
      // for writable items. The dedicated source phase rejects every tool call
      // before dispatch; changing this catalog to read_only removes an API tool
      // and makes the completed common prefix incompatible with its children.
      sourceBroker=await createWorkflowResourceBroker({workspace:envelope.workspace,access:envelope.access,allowedPaths:envelope.effective_allowed_paths,resources,authorize,onOperation:metadata=>event('tool_operation',metadata)});
      entry.brokers.push(sourceBroker);entry.poolResourceVersion++;
      const text=commonMaterial.prompt+'\n\nShared preparation phase: retain the declared common instructions and references for later independently assigned items. No item is assigned in this phase. Make no tool calls or workspace changes. '
        +(typedTransport?'Return readiness once through the declared API output contract.':'Return {"ready":true} once.');
      preparedPrefix=await manager.prefixFactory({parent:manager.parent,owner:{run_id:runId,node_id:binding.node_id,attempt_id:binding.attempt_id,phase:'shared-prefix'},
        hostAuth:manager.hostAuth,binary:settings.codex_binary,expectedBinaryHash:settings.binary_sha256,expectedBinaryPath:codexQualification(settings)?.resolved_path,dynamicToolFormat:codexQualification(settings)?.dynamic_tool_format,authentication:settings.authentication,rawObservation:codexQualification(settings)?.raw_observation,
        cwd:commonDirectory,access:'read_only',sourceExecutionAccess:envelope.access,allowedPaths:[],env:augmentedRuntimeEnvironment(manager.env,envelope.constraints?.runtime_environment??record.state.runtime_environment??record.state.constraints?.runtime_environment,{workspace:envelope.workspace}),
        toolBroker:sourceBroker,authorize,assertActive,resolveModelSelection:select,shared_output_schema:itemOutputSchema,shared_repair_schema:repairSchema,skillPolicy:{...envelope.skill_policy,implicit:'deny'},allowedSkills,
        onPrefixOwned:owner=>{requireValue(!entry.prefixOwner&&typeof owner?.close==='function'&&typeof owner?.interrupt==='function','HOST_MAIN_PREFIX_OWNER','Shared prefix must have one explicit cleanup and interruption owner');entry.prefixOwner=owner;entry.poolResourceVersion++;},
        onProfilePrepared:profile=>event('profile_owned',{home:profile.home,...(profile.receipt_home?{receipt_home:profile.receipt_home}:{}),executable_sha256:profile.binary_sha256}),onModelCatalog:metadata=>event('model_catalog',metadata),
        onObservationBatch:metadata=>runtime.recordExecutorObservations(runId,{...binding,events:metadata.map(item=>({kind:'codex_event',metadata:normalizeHostMainCodexEvent(item)}))}),
        onEvent:metadata=>{const normalized=normalizeHostMainCodexEvent(metadata);if(normalized)return event('codex_event',normalized);}},text,
        {output_schema:setupSchema,timeout_ms:settings.inactivity_timeout_ms});
      setup=preparedPrefix.setup;
      requireValue(entry.prefixOwner&&preparedPrefix.prefix,'HOST_MAIN_PREFIX_OWNER','Shared setup must publish its trusted lifecycle owner');
      requireValue(typeof setup.thread_id==='string'&&setup.thread_id&&typeof setup.turn_id==='string'&&setup.turn_id&&setup.usage?.available===true,
        'HOST_MAIN_PREFIX_RESULT','Shared setup requires exact completed identity and actual available usage');
      // The authenticated source catalog determines whether declarations were
      // actually appended. Native commands require no second prompt catalog.
      let declarations=null;
      if(responseTransport){
        const shell=setup.audit?.native_shell_execution,basis=setup.audit?.command_declaration_basis;
        requireValue(typeof shell==='string'&&shell.length>0
          &&basis===(shell==='disabled'?'owned_mcp_broker_when_native_shell_disabled':'inherited_native_shell'),
          'HOST_MAIN_PREFIX_DECLARATION_BASIS','Shared source must retain its authenticated shell/declaration basis');
        if(shell==='disabled')declarations=ownedCommandDeclarations(OWNED_MCP_NAMESPACE,createCodexCommandBroker({binary:settings.codex_binary,home:manager.parent,cwd:commonDirectory,access:'read_only',spoolRoot:resolve(manager.parent),getOutputBudget:()=>10000}).tools());
      }
      const setupTransport=responseTransport?.prepare_setup?{...responseTransport,prepare:responseTransport.prepare_setup}:responseTransport;
      requireInputIdentity(setup.audit,text,setupSchema,setupTransport,declarations);
      validateData(JSON.parse(setup.output),setupSchema);
      assertActive();await authorize();
      const sourceAfter=await snapshot(),sourceChanges=changedWorkspacePaths(before,sourceAfter);
      if(sourceChanges.length)await rejectWorkspaceScope({runtime,runId,attemptId:binding.attempt_id,code:'HOST_MAIN_SCOPE_VIOLATION',changed:sourceChanges,outside:sourceChanges,before,after:sourceAfter,event});
    }catch(error){setup??=error.setup;failures.push(error);}
    // A failed setup is metered too; unavailable usage remains unknown.
    setup??={usage:{available:false}};usages.push(setup.usage);
    turns.push({result:setup,identity:{phase:'shared-prefix',...(setup.thread_id?{thread_id:setup.thread_id}:{}),...(setup.turn_id?{turn_id:setup.turn_id}:{})}});
    try{
      const ref=await runtime.runs.saveArtifact(runId,`shared-prefix-${binding.attempt_id}`,Buffer.from(canonicalJSON({schema_version:1,phase:'shared-prefix',node_id:binding.node_id,attempt_id:binding.attempt_id,
        ...Object.fromEntries(['thread_id','turn_id','usage','audit','output','receipt_home','item_types'].filter(key=>setup[key]!==undefined).map(key=>[key,setup[key]])),preparation_path:commonMaterial.preparation_path,preparation_sha256:commonMaterial.preparation_sha256})));
      await event('shared_prefix_prepared',{...ref,...(setup.thread_id?{thread_id:setup.thread_id}:{}),...(setup.turn_id?{turn_id:setup.turn_id}:{})});
    }catch(error){failures.push(error);}
    // The live source owns the inherited MCP endpoint until every child drains.
    if(sourceBroker&&!preparedPrefix?.openSession)try{await quiesceBroker(sourceBroker);entry.brokers=entry.brokers.filter(item=>item!==sourceBroker);}catch(error){failures.push(error);}
  }
  const executeAssignment=async assignment=>{
    // Partitions reserve bounded scheduler slots; each item receives a fresh
    // session so cwd permissions and command drain cannot cross item boundaries.
    for(const itemIndex of assignment.indices){
      await authorize();assertActive();
      const scope=itemScopes.get(itemIndex),itemBefore=await snapshotWorkspace(scope.cwd,{access:envelope.access,allowedPaths:envelope.access==='bounded_write'?['.']:[],codePrefix:'HOST_MAIN'});
      const broker=await createWorkflowResourceBroker({workspace:envelope.workspace,access:envelope.access,allowedPaths:scope.itemPaths,resources,authorize,onOperation:metadata=>event('tool_operation',metadata)});
      entry.brokers.push(broker);entry.poolResourceVersion++;assertActive();
      let session;
      const own=owned=>{session=owned;if(!entry.sessions.includes(owned)){entry.sessions.push(owned);entry.poolResourceVersion++;}};
      try{
      const createSession=preparedPrefix?.openSession?options=>preparedPrefix.openSession(options):manager.sessionFactory;
      const created=await createSession({parent:manager.parent,owner:{run_id:runId,node_id:binding.node_id,attempt_id:binding.attempt_id,assignment_index:assignment.index,item_index:itemIndex},
        hostAuth:preparedPrefix||settings.authentication.mode==='host_chatgpt'?manager.hostAuth:undefined,binary:settings.codex_binary,expectedBinaryHash:settings.binary_sha256,expectedBinaryPath:codexQualification(settings)?.resolved_path,dynamicToolFormat:codexQualification(settings)?.dynamic_tool_format,authentication:settings.authentication,rawObservation:codexQualification(settings)?.raw_observation,
        resolveModelSelection:select,...(preparedPrefix?{prefix:preparedPrefix.prefix}:{}),ephemeral:true,cwd:scope.cwd,access:envelope.access,allowedPaths:envelope.access==='bounded_write'?['.']:scope.itemPaths,
        ...(envelope.access==='bounded_write'?{ownedCommandTemp:true}:{}),
        env:augmentedRuntimeEnvironment(manager.env,envelope.constraints?.runtime_environment??record.state.runtime_environment??record.state.constraints?.runtime_environment,{workspace:scope.cwd}),toolBroker:broker,authorize,assertActive,skillPolicy:{...envelope.skill_policy,implicit:'deny'},allowedSkills,maxTurns:definition.retry.max_attempts,onSessionOwned:own,
        onProfilePrepared:profile=>event('profile_owned',{home:profile.home,...(profile.receipt_home?{receipt_home:profile.receipt_home}:{}),executable_sha256:profile.binary_sha256}),onModelCatalog:metadata=>event('model_catalog',metadata),
        onObservationBatch:metadata=>runtime.recordExecutorObservations(runId,{...binding,
          events:metadata.map(item=>({kind:'codex_event',metadata:normalizeHostMainCodexEvent(item)}))}),
        onEvent:metadata=>{const normalized=normalizeHostMainCodexEvent(metadata);if(normalized)return event('codex_event',normalized);}});
      own(created);assertActive();requireValue(selection,'HOST_MAIN_MODEL_SELECTION_UNRESOLVED','Owned Main item session must resolve its model before dispatch');await selection;
      }catch(error){
        if(session)try{await session.close();entry.sessions=entry.sessions.filter(item=>item!==session);}catch(closeError){throw new AggregateError([error,closeError],'Main item setup and closure failed');}
        throw error;
      }
      let failure,result,value,workerHostCheck,textRepair;
      try{
        const consumed=currentRoundAttempts(record.state.nodes[definition.id]).reduce((sum,prior)=>sum+(prior.main_item_turns?.[itemIndex]??0),0),remaining=definition.retry.max_attempts-consumed;
        requireValue(remaining>0,'RETRY_LIMIT','Main item exhausted its pinned semantic attempts');
        let prompt=materials.get(itemIndex).prompt+`\n\nProcess assigned runtime item ${itemIndex} (position 0 in the supplied assigned list). Return only this item's semantic JSON result. Task file-change scope: ${JSON.stringify(scope.itemPaths)}.`
          +(preparedPrefix?.openSession?` Task workspace: ${JSON.stringify(scope.cwd)}. Ordinary command and resource tools use this assigned workspace.`:'');
        for(let correction=0;correction<remaining;correction++){
          await authorize();await runtime.reserveHostMainItemTurn(runId,{...binding,item_index:itemIndex});
          attemptedTurns++;
          const turnSchema=textRepair?repairSchema:itemOutputSchema;
          result=await (correction?session.continueTurn(prompt,{output_schema:turnSchema,timeout_ms:settings.inactivity_timeout_ms}):session.turn(prompt,{output_schema:turnSchema,timeout_ms:settings.inactivity_timeout_ms}));
          usages.push(result.usage);turns.push({session,result,identity:{item_index:itemIndex,thread_id:result.thread_id,turn_id:result.turn_id}});
          requireInputIdentity(result.audit,prompt,turnSchema,preparedPrefix?responseTransport:null);
          try{
            const payload=JSON.parse(result.output);
            if(textRepair){
              value=applyTextAmendment(textRepair.baseline,textRepair.scope,amendmentConfig,payload);validateData(value,schema);
              const raw=await runtime.runs.saveExecutorResult(runId,binding.attempt_id,{kind:'host_main_text_amendment',item_index:itemIndex,
                thread_id:result.thread_id,turn_id:result.turn_id,baseline_check:textRepair.reference,payload,merged_output_sha256:digest(canonicalJSON(value))});
              await event('text_amendment_proposed',{item_index:itemIndex,...raw,baseline_check_slot:textRepair.reference.slot_id});
            }else{value=payload;validateData(value,schema);}
          }
          catch(error){if(!['DATA_INVALID','NATIVE_TEXT_AMENDMENT'].includes(error.code)&&!(error instanceof SyntaxError))throw error;
            await event('completion_invalid',{correction,diagnostic:String(error.message).slice(0,900),thread_id:result.thread_id,turn_id:result.turn_id});if(correction+1===remaining)throw error;
            prompt=`Correct the prior JSON ${textRepair?'amendment':'result'}: ${String(error.message).slice(0,900)}. `+(textRepair
              ?`Return only the requested amendment within the same sealed scope: ${canonicalJSON(textRepair.scope)}.`
              :`Return the complete semantic result for assigned item ${itemIndex}.`);value=null;continue;}
          if(definition.completion_contract?.host_check){
          requireValue(typeof session.prepareHostCompletion==='function','CODEX_HOST_COMPLETION_BOUNDARY','Worker session has no command completion boundary');
          await session.prepareHostCompletion();
          assertActive();
            workerHostCheck=await executeWorkerHostCheck(manager,entry,binding,value,{item_index:itemIndex,authorize,assertActive});
            if(!workerHostCheck.accepted){
              const diagnostic=workerHostCheck.diagnostic;
              await event('completion_invalid',{correction,diagnostic:diagnostic.slice(0,900),thread_id:result.thread_id,turn_id:result.turn_id});
              requireValue(correction+1<remaining,'MAIN_WORKER_HOST_CHECK_FALSE',`Worker Host completion rejected item ${itemIndex}: ${diagnostic.slice(0,900)}`);
              if(amendmentConfig){
                textRepair={baseline:structuredClone(value),scope:structuredClone(workerHostCheck.repair_scope),reference:structuredClone(workerHostCheck.reference)};
                prompt=`Original CLI correction for this same item ${itemIndex}: ${diagnostic}\nReturn only physical-line amendments for the prior manuscript. Use 1-based inclusive lines; each line includes its separator. Nonempty non-EOF replacement must end with CRLF, LF or CR. Preserve unrelated content. Allowed scope: ${canonicalJSON(textRepair.scope)}.`;
              }else prompt=workerHostCheckCorrectionPrompt(diagnostic,`this same item ${itemIndex}`);
              value=null;continue;
            }
          }
          break;
        }
      }catch(error){
        if(error.branch_result){result=error.branch_result;usages.push(result.usage);turns.push({session,result,identity:{item_index:itemIndex,thread_id:result.thread_id,turn_id:result.turn_id}});}
        failure=error;
      }
      try{await session.close();entry.sessions=entry.sessions.filter(item=>item!==session);}catch(error){failure=failure?new AggregateError([failure,error],'Main item result and closure failed'):error;}
      // Session shutdown fences model commands; resource calls have their own
      // asynchronous queue. Drain that exact owner before reading item effects.
      // Retain failed owners for coordinator recovery and surface drain errors.
      try{await quiesceBroker(broker);entry.brokers=entry.brokers.filter(item=>item!==broker);}catch(error){failure=failure?new AggregateError([failure,error],'Main item closure and broker drain failed'):error;}
      // Capture settled command evidence even when drain fails. The semantic
      // result remains unaccepted until every owned effect is quiescent.
      try{
        const settled=session.commandAudit?.();
        if(settled?.length&&result){const keys=new Set(settled.map(item=>item.process_id));result.command_audit=[...(result.command_audit??[]).filter(item=>!keys.has(item.process_id)),...settled];}
      }catch(error){failure=failure?new AggregateError([failure,error],'Main item closure and audit failed'):error;}
      if(failure)throw failure;
      await authorize();assertActive();
      const itemAfter=await snapshotWorkspace(scope.cwd,{access:envelope.access,allowedPaths:envelope.access==='bounded_write'?['.']:[],codePrefix:'HOST_MAIN'});
      const itemChanged=changedWorkspacePaths(itemBefore,itemAfter).map(path=>scope.rootPath==='.'?path:scope.rootPath+'/'+path);
      const outside=envelope.access==='read_only'?itemChanged:itemChanged.filter(path=>!scope.itemPaths.some(root=>within(path,root)));
      if(outside.length)await rejectWorkspaceScope({runtime,runId,attemptId:binding.attempt_id,code:'HOST_MAIN_SCOPE_VIOLATION',changed:itemChanged,outside,before:itemBefore,after:itemAfter,event});
      itemChanged.forEach(path=>writes.add(path));
      accepted[itemIndex]=await runtime.recordHostMainItemResult(runId,{...binding,item_index:itemIndex,dispatch_id:assignment.dispatch_id,thread_id:result.thread_id,turn_id:result.turn_id,result:value,changed_paths:itemChanged,...(workerHostCheck?{host_check:workerHostCheck.reference}:{})});
    }
  };
  const setupReady=!commonMaterial||failures.length===0;
  const workers=Array.from({length:Math.min(assignments.length,fanout.scheduling==='serial'?1:fanout.max_concurrency??32)},async()=>{
    while(next<assignments.length&&!entry.stopping&&setupReady){const assignment=assignments[next++];try{await executeAssignment(assignment);}catch(error){failures.push(error);}}
  });
  await Promise.all(workers);
  if(entry.prefixOwner)try{await entry.prefixOwner.close();entry.prefixOwner=null;}catch(error){failures.push(error);}
  try{
    requireValue(usages.every(item=>typeof item?.available==='boolean'),'CODEX_USAGE_SCHEMA','Main item sessions require metering availability signals');
    const usage={unknown:attemptedTurns>0,...(attemptedTurns===0?{cost_micros:0}:{})};
    for(const field of ['input_tokens','cached_input_tokens','cache_write_input_tokens','output_tokens','reasoning_output_tokens'])
      if(usages.length===attemptedTurns&&usages.every(item=>Number.isSafeInteger(item?.[field])&&item[field]>=0))usage[field]=usages.reduce((sum,item)=>sum+item[field],0);
    await runtime.recordHostMainUsage(runId,{...binding,request_id:`dispatch-${binding.attempt_id}`,usage});
  }catch(error){failures.push(error);}
  let commandAudit;
  try{commandAudit=await persistCodexCommandAudits(runtime,runId,`command-audit-${binding.attempt_id}`,turns.map(({identity,result})=>({identity,result})));}
  catch(error){failures.push(error);}
  if(failures.length)throw Object.assign(new AggregateError(failures,'Main fan-out item execution failed'),{code:'HOST_MAIN_POOL_FAILED'});
  assertActive();requireValue(plan.items.every((_item,index)=>accepted[index]),'HOST_MAIN_ITEM_JOIN','Main fan-out requires every item before join');
  const output={[fanout.result_output]:plan.items.map((_item,index)=>accepted[index].result)},evidence=plan.items.map((_item,index)=>({kind:'host_main_item_result',item_index:index,...accepted[index]}));
  const after=await snapshot(),changed=changedWorkspacePaths(before,after),outside=envelope.access==='read_only'?changed:changed.filter(path=>!envelope.effective_allowed_paths.some(root=>within(path,root)));
  if(outside.length)await rejectWorkspaceScope({runtime,runId,attemptId:binding.attempt_id,code:'HOST_MAIN_SCOPE_VIOLATION',changed,outside,before,after,event});
  for(const item of Object.values(accepted))item.changed_paths.forEach(path=>writes.add(path));
  for(const required of definition.required_artifacts??[])requireValue([...writes].some(path=>within(path,required.path)&&within(required.path,path))&&[...after.keys()].some(path=>within(path,required.path)&&within(required.path,path)),'REQUIRED_ARTIFACT_MISSING',`Main pool did not produce ${required.path}`);
  const completion=hostResultProposalEnvelope(definition,{output,summary:`Main completed ${definition.id}`,changed_paths:[...writes],artifacts:[...writes],outside_paths:[],evidence:[...evidence,...(commandAudit?[{kind:'command_audit',...commandAudit}]:[])]});
  const saved=await runtime.runs.saveExecutorResult(runId,binding.attempt_id,completion);await event('result_proposed',{...saved,final_acceptance_required:false});await event('session_state',{status:'closed'});
  await runtime.completeHostMainResult(runId,binding,record.pins.root.workflow.finalization?.node_id===definition.id?{accepted:true}:{});entry.session=null;entry.broker=null;entry.sessions=[];entry.brokers=[];
  return {final_acceptance_required:false};
}
