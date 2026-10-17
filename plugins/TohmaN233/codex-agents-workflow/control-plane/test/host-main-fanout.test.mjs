import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,mkdir,writeFile,readFile,rm} from 'node:fs/promises';
import {join,resolve} from 'node:path';
import {tmpdir} from './physical-tempdir.mjs';
import {WorkflowStore} from '../lib/workflow-store.mjs';
import {WorkflowRuntime} from '../lib/workflow-runtime.mjs';
import {HostMainManager} from '../lib/execution/host-main-manager.mjs';
import {createDraft} from '../lib/workflow-schema.mjs';
import {canonicalJSON,digest} from '../lib/workflow-revisions.mjs';
import {validateWorkflowGraph} from '../lib/workflow-validator.mjs';
import {createCodexCommandBroker} from '../lib/execution/codex-command-broker.mjs';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {HostToolRunner} from '../lib/execution/host-tool-runner.mjs';
import {workflowResourceProgramIdentity,workflowResourceProgramRegistry} from '../lib/execution/workflow-resource-program.mjs';
import {sharedPrefixInputProjection} from '../lib/execution/host-main-fanout.mjs';
import {prepareCodexNormalPrefix} from '../lib/execution/codex-session.mjs';
import {prepareCodexCommonBatch} from '../lib/execution/codex-common-batch-session.mjs';
import {ownedCommandDeclarations} from '../lib/execution/owned-command-declarations.mjs';
import {OWNED_MCP_NAMESPACE} from '../lib/execution/owned-tool-mcp.mjs';
import {createTypedBatchOutputTransport} from '../lib/execution/typed-batch-output-transport.mjs';
import {textAmendmentSchema} from '../lib/execution/native-text-amendment.mjs';

const object=properties=>({type:'object',properties,required:Object.keys(properties),additionalProperties:false});
const result=object({conclusion:{type:'string',minLength:1,maxLength:600}});
const jobsSchema={type:'array',minItems:1,maxItems:6,items:object({name:{type:'string'},workspace:{type:'string'},destinations:{type:'array',minItems:1,items:{type:'string'}}})};
const deferred=()=>{let resolve;const promise=new Promise(done=>{resolve=done;});return {promise,resolve};};
const edge=(source,target)=>({id:source+'-'+target,source,target});
test('shared prefix factors only explicitly equal common inputs and preserves item bytes',()=>{
 const items=[{name:'a'},{name:'b'}],envelope={inputs:{jobs:items,format:'CRLF\r\n𝄞',task:'common author task'},prompt_template:'{{task}}'};
 const projected=sharedPrefixInputProjection(envelope,items,{common_inputs:['format','task']});
 assert.deepEqual(projected.common,{format:'CRLF\r\n𝄞',task:'common author task'});
 assert.deepEqual(projected.items,[{jobs:[items[0]]},{jobs:[items[1]]}]);
 assert.throws(()=>sharedPrefixInputProjection(envelope,items,{common_inputs:['jobs']}),{code:'HOST_MAIN_PREFIX_INPUT'});
 assert.throws(()=>sharedPrefixInputProjection(envelope,items,{common_inputs:['format']}),{code:'HOST_MAIN_PREFIX_TEMPLATE'});
 assert.throws(()=>sharedPrefixInputProjection(envelope,items,{common_inputs:['absent']}),{code:'HOST_MAIN_PREFIX_INPUT'});
});
function workerCheckFixture({accept=()=>true,execute}={}){
 const contract={id:'worker-check',identity:{name:'worker-check-fixture',version:'1',sha256:digest('worker-check')},argv:['render'],input_schema:object({inputs:object({jobs:{...jobsSchema,minItems:1,maxItems:1}}),output:result}),output_schema:object({ok:{type:'boolean'},diagnostic:{type:'string'}}),env_allow:[],permissions:{network:false,read_paths:['.'],write_paths:['.']},output_cap_bytes:2048,deadline_ms:1000,idempotency:{mode:'safe'}};
 const calls=[],counts=new Map();const broker={identity:contract.identity,attestation:{qualified:true,cancellable:true,effect_observation:true,tool_identity:contract.identity,broker_id:'worker-check-broker',evidence_sha256:digest('qualification')},execute:async request=>{calls.push(request);const name=request.input.inputs.jobs[0].name,count=(counts.get(name)??0)+1;counts.set(name,count);if(execute)return execute(request,count);const ok=accept(request,count);await writeFile(join(request.context.workspace,'rendered.txt'),request.input.output.conclusion);return {exit_code:0,output:{ok,diagnostic:ok?'':'Revise this page conclusion.'},diagnostic:'',effects:{observed:true,changed_paths:['rendered.txt'],outside_paths:[],artifacts:[]}};},cancel:async()=>({termination_confirmed:true,evidence:[{kind:'terminated',sha256:digest('terminated')}],effects:{observed:true,changed_paths:[],outside_paths:[],artifacts:[]}})};
 return {contract,calls,broker,runner:new HostToolRunner({registry:{[contract.id]:broker},env:{}})};
}
function graph(){return {...createDraft('main-pool','Main item pool fixture'),status:'ready',skill_policy:{mode:'cooperative',implicit:'deny',ambient_allow:[],shadowed_skill_paths:[]},inputs_schema:object({jobs:jobsSchema}),outputs_schema:{},finalization:{required:true,node_id:'final'},nodes:[{id:'start',type:'start'},
 {id:'pages',type:'agent',role:'implementer',executor:{kind:'main',mode:'worker'},access:'bounded_write',path_scope:['pages'],approval:{required:false},retry:{max_attempts:3},input_bindings:{jobs:'/inputs/jobs'},prompt_template:'Create the assigned page(s).',outputs_schema:object({results:{type:'array',minItems:1,maxItems:6,items:result}}),subagent_count:'auto',fanout:{input:'jobs',item_name:'page',result_output:'results',distribution:'one_per_item',scheduling:'parallel',join:'all_required',result_mode:'per_item',max_concurrency:2,write_paths_field:'destinations',workspace_field:'workspace'}},
 {id:'final',type:'agent',role:'finalizer',executor:{kind:'main'},access:'read_only',path_scope:[],approval:{required:false},retry:{max_attempts:3},input_bindings:{},prompt_template:'Verify.',outputs_schema:object({verified:{type:'boolean'}})},{id:'end',type:'end'}],edges:[edge('start','pages'),edge('pages','final'),edge('final','end')]};}
async function fixture(t,{jobs=[{name:'a',workspace:'pages/a',destinations:['pages/a']},{name:'b',workspace:'pages/b',destinations:['pages/b']},{name:'c',workspace:'pages/c',destinations:['pages/c']}],turn=async()=>{},payloadForTurn,factory=async()=>{},close=async()=>{},prepare=async()=>{},partition=false,requireUsage=false,usage={available:true,input_tokens:10,output_tokens:2},requiredArtifacts=[],resources={},mainExecutionContext,hostCheck,single=false,sharedPrefix,prefixFactory,prefixCapability={complete_usage:true,reason:'simulated_complete_observer'},commonInputs={},inputAudit=(text)=>({input_sha256:digest(canonicalJSON([{type:'text',text}]))})}={}){
 const root=await mkdtemp(join(tmpdir(),'host-main-pool-')),workspace=join(root,'workspace');await mkdir(workspace);await mkdir(join(workspace,'pages'));
 for(const item of jobs)await mkdir(join(workspace,item.workspace),{recursive:true});
 const store=await new WorkflowStore(join(root,'workflows'),hostCheck?{validationContext:{host_tools:[hostCheck.contract.id]}}:undefined).initialize();const workflow=graph();workflow.nodes.find(item=>item.id==='pages').required_artifacts=requiredArtifacts;if(Object.keys(resources).length)workflow.nodes.find(item=>item.id==='pages').resources=Object.keys(resources);if(hostCheck){workflow.host_tools=[hostCheck.contract];const node=workflow.nodes.find(item=>item.id==='pages');node.retry.max_attempts=hostCheck.maxAttempts??3;node.completion_contract={on_missing:'block',outcome:'validated_artifact',host_check:{tool:hostCheck.contract.id,success_field:'ok',correction_field:'diagnostic',...(hostCheck.input_bindings?{input_bindings:hostCheck.input_bindings}:{}),...(hostCheck.text_amendment?{text_amendment:hostCheck.text_amendment}:{})}};if(hostCheck.inputSchemas){Object.assign(workflow.inputs_schema.properties,hostCheck.inputSchemas);workflow.inputs_schema.required.push(...Object.keys(hostCheck.inputSchemas));}}if(requireUsage)workflow.nodes.find(item=>item.id==='pages').cost={maximum_micros:1};if(partition){const node=workflow.nodes.find(item=>item.id==='pages');node.subagent_count=2;node.fanout.distribution='partition';}if(hostCheck?.resources)workflow.nodes.find(item=>item.id==='pages').runtime_requirements={executables:['node']};await store.create(workflow,{resources:{...resources,...(hostCheck?.resources??{})}});const runtime=await new WorkflowRuntime({workflowStore:store,runRoot:join(root,'runs'),context:hostCheck?{host_tools:[hostCheck.contract.id]}:{}}).initialize();
 if(single){const node=workflow.nodes.find(item=>item.id==='pages');delete node.fanout;delete node.subagent_count;node.outputs_schema=result;node.path_scope=['.'];workflow.inputs_schema.properties.jobs={...jobsSchema,maxItems:1};await store.save(workflow.id,workflow,{expected_revision:(await store.snapshot(workflow.id)).revision_hash});}
 if(sharedPrefix){const node=workflow.nodes.find(item=>item.id==='pages');node.fanout.shared_prefix=sharedPrefix;node.prompt_template='Common authoring format once.';for(const name of Object.keys(commonInputs)){workflow.inputs_schema.properties[name]={type:'string'};workflow.inputs_schema.required.push(name);node.input_bindings[name]='/inputs/'+name;}await store.save(workflow.id,workflow,{expected_revision:(await store.snapshot(workflow.id)).revision_hash});}
 const run=await runtime.start({workflow_id:'main-pool',workspace,access:'bounded_write',allowed_paths:single?['.']:['pages'],main_actor:'root',constraints:{require_usage_ledger:requireUsage,...(mainExecutionContext?{native_parent_thread_id:mainExecutionContext.parent_thread_id}:{})},inputs:{jobs,...(hostCheck?.inputs??{}),...commonInputs}});
 const settings={enabled:true,codex_binary:process.execPath,binary_sha256:'b'.repeat(64),authentication:{mode:'managed_chatgpt',api_key_env:''},main_model:'',main_reasoning_effort:'',inactivity_timeout_ms:0};
 const created=[],prompts=[],selections=[];let modelReads=0;
 if(prefixFactory)Object.defineProperty(prefixFactory,'usageCapability',{value:Object.freeze({...prefixCapability})});
 const manager=new HostMainManager({register:async({config})=>config,configPath:join(root,'control-plane.json'),...(prefixFactory?{prefixFactory}:{}),...(hostCheck?{hostToolRunner:hostCheck.runner}:{}),env:{},getConfig:async()=>({global:{enabled:true},strict_executor:settings,providers:[]}),qualify:async()=>settings,mainModelSelection:async()=>{modelReads++;return {model:'initiating-main',effort:'high',...(mainExecutionContext?{main_execution_context:structuredClone(mainExecutionContext)}:{})};},sessionFactory:async options=>{
   const index=options.owner.item_index??0;const selected=await options.resolveModelSelection({});selections.push(selected);assert.equal(options.ephemeral,true);assert.equal(options.hostWorker,true,'Host fixes worker execution policy; models never select a new OS sandbox');assert.equal(options.cwd,single?workspace:join(workspace,jobs[index].workspace));assert.deepEqual(options.allowedPaths,['.']);assert.equal(options.isolatedWorkspace,undefined,'Main fanout must not add an OS isolation probe');
   let closed=false,turnNumber=0;const gate=deferred(),session={prepareHostCompletion:async()=>prepare({index,options,session}),interrupt:async()=>gate.resolve(),close:async()=>{closed=true;gate.resolve();await close({index,options,session});options.toolBroker.revoke();},turn:async(text,turnOptions={})=>{
     const itemIndex=Number(/runtime item (\d+)/.exec(text)?.[1]??index);prompts.push({index:itemIndex,text});await turn({index:itemIndex,text,options,session,gate,closed:()=>closed});
     if(closed)throw Object.assign(new Error('interrupted fixture item'),{code:'HOST_MAIN_STOPPED'});
     await writeFile(join(workspace,jobs[itemIndex].workspace,'output.txt'),jobs[itemIndex].name);
     return {...(session.turnAudit?{command_audit:session.turnAudit()}:{}),thread_id:`fixture-thread-${index}`,turn_id:`fixture-turn-${++turnNumber}-${index}`,output:JSON.stringify(payloadForTurn?await payloadForTurn({index:itemIndex,turn:turnNumber,output_schema:turnOptions.output_schema}):{conclusion:jobs[itemIndex].name}),usage:structuredClone(usage),audit:inputAudit(text,turnOptions.output_schema)};
   }};session.continueTurn=session.turn;
   options.onSessionOwned(session);created.push({index,options,session,closed:()=>closed});await factory({index,options,session});return session;
 }});
 const claim=async suffix=>{const lease=await runtime.claimHostMain(run.run_id,{node_id:'pages',owner:'root',request_id:`claim-${suffix}`,control_token:run.control_token});const binding={...lease,control_token:run.control_token,owner:'root'};await runtime.recordHostMainDispatchIntent(run.run_id,{...binding,request_id:`dispatch-${lease.attempt_id}`,envelope_hash:'f'.repeat(64)});return binding;};
 const execute=async binding=>{const entry={runtime,runId:run.run_id,status:'running',stopping:false,handoff:{host_binding:binding}};manager.entries.set(run.run_id,entry);const job=manager.executeNode(entry,{host_binding:binding,agent_packet:{prompt:'fixture'}});entry.job=job.catch(()=>{});return {entry,job};};
 t.after(async()=>{await manager.close();assert(resolve(root).startsWith(resolve(tmpdir())));await rm(root,{recursive:true,maxRetries:3,retryDelay:100});});
 return {root,workspace,runtime,manager,run,created,prompts,selections,modelReads:()=>modelReads,claim,execute};
}

test('unsupported shared prefix pays no setup and reserves no model turns',async t=>{
 let setups=0;
 const f=await fixture(t,{sharedPrefix:{common_inputs:[]},prefixCapability:{complete_usage:false,reason:'complete_counter_witness_absent'},prefixFactory:async()=>{setups++;throw new Error('must not start setup');}});
 const execution=await f.execute(await f.claim('unsupported'));
 await assert.rejects(execution.job,{code:'HOST_MAIN_PREFIX_USAGE_UNSUPPORTED'});
 assert.equal(setups,0);assert.equal(f.created.length,0);assert.equal(f.modelReads(),0);
 const record=await f.runtime.runs.read(f.run.run_id),attempt=record.state.nodes.pages.attempts[0];
 assert.equal(attempt.main_shared_prefix_turns??0,0);assert.deepEqual(attempt.main_item_turns??{},{});
});

test('ordinary manager selects live common batch with complete restored counter capability',()=>{
 const manager=new HostMainManager({configPath:'unused-fixture-path'});
 assert.equal(manager.prefixFactory,prepareCodexCommonBatch);
 assert.equal(manager.prefixFactory.usageCapability.complete_usage,true);
 assert.equal(manager.prefixFactory.usageCapability.reason,'live_common_source_restored_counter_observed_before_branch_submit');
});

test('shared prefix declared-resource source and writable children preserve callable schemas without source effects',async t=>{
 let f,sourceTools,sourceCalls=0,sourceClosed=false;const children=[];
 const callableTools=options=>[...options.toolBroker.tools(),...createCodexCommandBroker({binary:process.execPath,home:tmpdir(),cwd:options.cwd,access:options.access,
   allowedPaths:options.allowedPaths,spoolRoot:tmpdir(),getOutputBudget:()=>10000}).tools()];
 f=await fixture(t,{sharedPrefix:{common_inputs:[]},resources:{'reference.txt':'Declared common reference.'},
  factory:async({options})=>{const tools=callableTools(options);assert.deepEqual(tools,sourceTools);children.push(tools);},
  prefixFactory:async(options,text)=>{
   await options.resolveModelSelection({});assert.equal(options.access,'read_only');assert.equal(options.hostWorker,true);assert.match(text,/Make no tool calls or workspace changes/);
   sourceTools=callableTools(options);assert(sourceTools.some(tool=>tool.name==='materialize_workflow_resource'));
   const call=options.toolBroker.call;options.toolBroker.call=(...args)=>{sourceCalls++;return call(...args);};
   assert.equal(await readFile(join(f.workspace,'pages','a','output.txt')).catch(error=>{assert.equal(error.code,'ENOENT');return null;}),null);
   const owner={interrupt:async()=>{},close:async()=>{options.toolBroker.revoke();assert.equal((await options.toolBroker.quiesce()).quiescent,true);sourceClosed=true;}};options.onPrefixOwned(owner);
   return {prefix:owner,setup:{thread_id:'source-catalog',turn_id:'source-ready',output:'{"ready":true}',usage:{available:true,input_tokens:7,output_tokens:1},audit:{input_sha256:digest(canonicalJSON([{type:'text',text}]))}},
     openSession:childOptions=>f.manager.sessionFactory(childOptions)};
  }});
 const execution=await f.execute(await f.claim('declared-resource-catalog'));await execution.job;
 assert.equal(children.length,3);assert(children.every(tools=>tools.some(tool=>tool.name==='materialize_workflow_resource')));
 assert.equal(sourceCalls,0);assert.equal(sourceClosed,true);
 const record=await f.runtime.runs.read(f.run.run_id);assert.equal(record.state.nodes.pages.attempts[0].main_shared_prefix_turns,1);
 assert.deepEqual(Object.keys(record.state.nodes.pages.attempts[0].main_item_results),['0','1','2']);
});

const responseTransport=prepareCodexNormalPrefix.usageCapability.responseTransport;
function transportedAudit(text,schema,source=false){
 const original=[{type:'text',text}],transported=[{type:'text',text:responseTransport.prepare(text,schema).text}];
 const declarations=source?ownedCommandDeclarations(OWNED_MCP_NAMESPACE,createCodexCommandBroker({binary:process.execPath,home:tmpdir(),cwd:tmpdir(),access:'read_only',spoolRoot:tmpdir(),getOutputBudget:()=>10000}).tools()):null;
 const actual=declarations?[...transported,declarations.input]:transported,actualHash=digest(canonicalJSON(actual));
 return {semantic_input_sha256:digest(canonicalJSON(original)),transported_semantic_input_sha256:digest(canonicalJSON(transported)),input_sha256:actualHash,submitted_input_sha256:actualHash,
  response_transport:{api_schema_sha256:responseTransport.api_schema_sha256,semantic_schema_sha256:digest(canonicalJSON(schema))},...(declarations?{owned_command_declarations:declarations.audit,native_shell_execution:'disabled',command_declaration_basis:'owned_mcp_broker_when_native_shell_disabled'}:{})};
}
for(const mode of ['valid','bad semantic','bad actual'])test(`trusted prefix transport verifies source and child ${mode} identity`,async t=>{
 for(const corruptSource of mode==='valid'?[false]:[true,false]){
  const corrupt=audit=>{if(mode==='bad semantic')audit.semantic_input_sha256='0'.repeat(64);if(mode==='bad actual')audit.input_sha256=audit.submitted_input_sha256='0'.repeat(64);return audit;};
  const f=await fixture(t,{sharedPrefix:{common_inputs:[]},prefixCapability:{complete_usage:true,reason:'simulated_complete_observer',responseTransport},
   inputAudit:(text,schema)=>corruptSource?transportedAudit(text,schema):corrupt(transportedAudit(text,schema)),
   prefixFactory:async(options,text,turnOptions)=>{
    assert.equal(turnOptions.output_schema,responseTransport.setup_schema);
    await options.resolveModelSelection({});options.onPrefixOwned({interrupt:async()=>{},close:async()=>{}});
    const audit=transportedAudit(text,turnOptions.output_schema,true);
    return {prefix:{},setup:{thread_id:'setup-thread',turn_id:'setup-turn',output:'{"ready":true}',usage:{available:true,input_tokens:7,output_tokens:1},audit:corruptSource?corrupt(audit):audit}};
   }});
  const execution=await f.execute(await f.claim('transport-'+mode+'-'+corruptSource));
  if(mode==='valid'){await execution.job;assert.equal(f.created.length,3);}
  else{await assert.rejects(execution.job,error=>error.code==='HOST_MAIN_POOL_FAILED'&&error.errors.some(item=>item.code==='HOST_MAIN_INPUT_MISMATCH'));if(corruptSource)assert.equal(f.created.length,0);}
 }
});

test('native-shell shared source uses its actual declaration-free wire at complete Host fanout seam',async t=>{
 const f=await fixture(t,{sharedPrefix:{common_inputs:[]},
  prefixCapability:{complete_usage:true,reason:'simulated_complete_observer',responseTransport},
  inputAudit:transportedAudit,prefixFactory:async(options,text,turnOptions)=>{
   await options.resolveModelSelection({});options.onPrefixOwned({interrupt:async()=>{},close:async()=>{}});
   const audit={...transportedAudit(text,turnOptions.output_schema),native_shell_execution:'unified_exec',command_declaration_basis:'inherited_native_shell'};
   return {prefix:{},setup:{thread_id:'native-source',turn_id:'native-ready',output:'{"ready":true}',usage:{available:true,input_tokens:7,output_tokens:1},audit}};
  }});
 const execution=await f.execute(await f.claim('native-source'));await execution.job;
 assert.equal(f.created.length,3);
});

for(const basis of [undefined,'owned_mcp_broker_when_native_shell_disabled'])test(`native shared source rejects missing or contradictory catalog basis ${basis}`,async t=>{
 const f=await fixture(t,{sharedPrefix:{common_inputs:[]},
  prefixCapability:{complete_usage:true,reason:'simulated_complete_observer',responseTransport},
  inputAudit:transportedAudit,prefixFactory:async(options,text,turnOptions)=>{
   await options.resolveModelSelection({});options.onPrefixOwned({interrupt:async()=>{},close:async()=>{}});
   const audit={...transportedAudit(text,turnOptions.output_schema),native_shell_execution:'unified_exec',...(basis?{command_declaration_basis:basis}:{})};
   return {prefix:{},setup:{thread_id:'native-source',turn_id:'native-ready',output:'{"ready":true}',usage:{available:true,input_tokens:7,output_tokens:1},audit}};
  }});
 const execution=await f.execute(await f.claim('invalid-native-basis'));
 await assert.rejects(execution.job,error=>error.code==='HOST_MAIN_POOL_FAILED'&&error.errors.some(item=>item.code==='HOST_MAIN_PREFIX_DECLARATION_BASIS'));
 assert.equal(f.created.length,0);
});

test('typed live common output crosses full Host fanout with one pinned API and original item semantics',async t=>{
 let transport,setupAPI;const childAPIs=[];
 const audit=(text,schema,source=false)=>{
  const prepared=source?transport.prepare_setup(text,schema):transport.prepare(text,schema);
  if(source)setupAPI=prepared.output_schema;else childAPIs.push(prepared.output_schema);
  const wire=digest(canonicalJSON([{type:'text',text:prepared.text}]));
  return {semantic_input_sha256:digest(canonicalJSON([{type:'text',text}])),
   transported_semantic_input_sha256:wire,input_sha256:wire,submitted_input_sha256:wire,
   response_transport:{api_schema_sha256:transport.api_schema_sha256,semantic_schema_sha256:digest(canonicalJSON(schema))},
   ...(source?{native_shell_execution:'unified_exec',command_declaration_basis:'inherited_native_shell'}:{})};
 };
 const f=await fixture(t,{sharedPrefix:{common_inputs:[]},
  prefixCapability:prepareCodexCommonBatch.usageCapability,inputAudit:(text,schema)=>audit(text,schema),
  prefixFactory:async(options,text,turnOptions)=>{
   assert.deepEqual(options.shared_output_schema,result);
   transport=createTypedBatchOutputTransport(options.shared_output_schema);
   assert(!text.includes('Return {"ready":true}'));assert(!text.includes('pages/a'));
   await options.resolveModelSelection({});options.onPrefixOwned({interrupt:async()=>{},close:async()=>{}});
   return {prefix:{},setup:{thread_id:'typed-source',turn_id:'typed-ready',output:transport.decode_setup('{"results":[]}',turnOptions.output_schema),usage:{available:true,input_tokens:7,output_tokens:1},audit:audit(text,turnOptions.output_schema,true)}};
  }});
 const execution=await f.execute(await f.claim('typed-source'));await execution.job;
 assert.equal(f.created.length,3);assert.equal(childAPIs.length,3);
 for(const api of childAPIs)assert.deepEqual(api,setupAPI);
 assert.equal(setupAPI.properties.results.items.properties.conclusion.type,'string');
 const state=(await f.runtime.runs.read(f.run.run_id)).state;
 assert.deepEqual(state.nodes.pages.output.results,[{conclusion:'a'},{conclusion:'b'},{conclusion:'c'}]);
 assert.equal(state.cost_ledger.calls[0].usage.input_tokens,37);
});

test('shared prefix Main public lifecycle prepares once, forks item-only inputs and meters setup',async t=>{
 let setupCalls=0,closed=0;const prefix={},setupUsage={available:true,input_tokens:7,output_tokens:1};
 const f=await fixture(t,{sharedPrefix:{common_inputs:['format']},commonInputs:{format:'shared exact format 𝄞'},prefixFactory:async(options,text)=>{
   setupCalls++;await options.resolveModelSelection({});assert.equal(options.access,'read_only');assert.equal(options.sourceExecutionAccess,'bounded_write');assert.deepEqual(options.allowedPaths,[]);
   assert(text.includes('Common authoring format once.'));assert(text.includes('shared exact format 𝄞'));assert(!text.includes('pages/a'));
   const owner={interrupt:async()=>{},close:async()=>{closed++;}};options.onPrefixOwned(owner);
   return {prefix,setup:{thread_id:'setup-thread',turn_id:'setup-turn',output:'{"ready":true}',usage:setupUsage,audit:{input_sha256:digest(canonicalJSON([{type:'text',text}]))}},close:owner.close};
 }});
 const binding=await f.claim('shared'),execution=await f.execute(binding);await execution.job;
 assert.equal(setupCalls,1);assert.equal(closed,1);assert(f.created.every(item=>item.options.prefix===prefix));
 assert(f.prompts.every(item=>!item.text.includes('Common authoring format once.')&&!item.text.includes('shared exact format')));
 for(const item of f.prompts){assert(item.text.includes(`pages/${['a','b','c'][item.index]}`));assert(!item.text.includes(`pages/${['b','c','a'][item.index]}`));}
 const record=await f.runtime.runs.read(f.run.run_id),attempt=record.state.nodes.pages.attempts[0];
 assert.equal(attempt.main_shared_prefix_turns,1);assert.deepEqual(attempt.main_item_turns,{0:1,1:1,2:1});
 assert.equal(record.state.cost_ledger.calls[0].usage.input_tokens,37);assert.equal(record.state.cost_ledger.calls[0].usage.output_tokens,7);
});

test('shared prefix setup failure retains billed usage and prevents every child launch',async t=>{
 let closed=0;const f=await fixture(t,{sharedPrefix:{common_inputs:[]},prefixFactory:async options=>{
  await options.resolveModelSelection({});options.onPrefixOwned({interrupt:async()=>{},close:async()=>{closed++;}});
  throw Object.assign(new Error('setup failed after billing'),{code:'SETUP_FAILED',setup:{usage:{available:true,input_tokens:9,output_tokens:3}}});
 }});
 const binding=await f.claim('setup-failure'),execution=await f.execute(binding);
 await assert.rejects(execution.job,error=>error.code==='HOST_MAIN_POOL_FAILED'&&error.errors.some(item=>item.code==='SETUP_FAILED'));
 assert.equal(f.created.length,0);assert.equal(closed,1);
 const record=await f.runtime.runs.read(f.run.run_id);assert.equal(record.state.cost_ledger.calls[0].usage.input_tokens,9);assert.equal(record.state.nodes.pages.attempts[0].main_shared_prefix_turns,1);
});

test('shared prefix read-only setup rejects product writes before any child',async t=>{
 let f;f=await fixture(t,{sharedPrefix:{common_inputs:[]},prefixFactory:async(options,text)=>{
  await options.resolveModelSelection({});options.onPrefixOwned({interrupt:async()=>{},close:async()=>{}});
  await writeFile(join(f.workspace,'pages/a/unexpected.txt'),'unexpected');
  return {prefix:{},setup:{thread_id:'setup-thread',turn_id:'setup-turn',output:'{"ready":true}',usage:{available:true,input_tokens:1,output_tokens:1},audit:{input_sha256:digest(canonicalJSON([{type:'text',text}]))}}};
 }});
 const binding=await f.claim('setup-write'),execution=await f.execute(binding);
 await assert.rejects(execution.job,error=>error.code==='HOST_MAIN_POOL_FAILED'&&error.errors.some(item=>item.code==='HOST_MAIN_SCOPE_VIOLATION'));
 assert.equal(f.created.length,0);
});

test('shared prefix cancellation owns setup before its wait and never starts children',async t=>{
 const entered=deferred(),released=deferred();let closed=false;
 const f=await fixture(t,{sharedPrefix:{common_inputs:[]},prefixFactory:async options=>{
  await options.resolveModelSelection({});options.onPrefixOwned({interrupt:async()=>released.resolve(),close:async()=>{closed=true;released.resolve();}});entered.resolve();
  await released.promise;options.assertActive();throw new Error('cancel should have revoked setup');
 }});
 const binding=await f.claim('setup-cancel'),execution=await f.execute(binding);await Promise.race([entered.promise,execution.job]);
 await f.manager.stopRun(f.run.run_id);await assert.rejects(execution.job);assert.equal(closed,true);assert.equal(f.created.length,0);
 const record=await f.runtime.runs.read(f.run.run_id);assert.equal(record.state.cost_ledger.calls[0].usage.input_tokens,undefined);assert.equal(record.state.cost_ledger.calls[0].usage.unknown,true);
});

test('shared prefix forks preserve same-child correction and exact item budget',async t=>{
 const check=workerCheckFixture({accept:(_request,count)=>count>1});check.maxAttempts=2;const prefix={};
 const f=await fixture(t,{hostCheck:check,sharedPrefix:{common_inputs:[]},prefixFactory:async(options,text)=>{
  await options.resolveModelSelection({});options.onPrefixOwned({interrupt:async()=>{},close:async()=>{}});
  return {prefix,setup:{thread_id:'setup-thread',turn_id:'setup-turn',output:'{"ready":true}',usage:{available:true,input_tokens:7,output_tokens:1},audit:{input_sha256:digest(canonicalJSON([{type:'text',text}]))}}};
 }});
 const binding=await f.claim('shared-correction'),execution=await f.execute(binding);await execution.job;
 assert.equal(f.created.length,3);assert.equal(f.prompts.length,6);assert(f.created.every(item=>item.options.prefix===prefix));
 const record=await f.runtime.runs.read(f.run.run_id);assert.deepEqual(record.state.nodes.pages.attempts[0].main_item_turns,{0:2,1:2,2:2});assert.equal(record.state.cost_ledger.calls[0].usage.input_tokens,67);
});

test('shared prefix partition retry preserves accepted siblings and prepares a fresh counted setup',async t=>{
 let setups=0,fail=true;const f=await fixture(t,{partition:true,sharedPrefix:{common_inputs:[]},turn:async({index})=>{if(index===1&&fail)throw new Error('one missing item');},prefixFactory:async(options,text)=>{
  setups++;await options.resolveModelSelection({});options.onPrefixOwned({interrupt:async()=>{},close:async()=>{}});
  return {prefix:{epoch:setups},setup:{thread_id:`setup-${setups}`,turn_id:'setup-turn',output:'{"ready":true}',usage:{available:true,input_tokens:7,output_tokens:1},audit:{input_sha256:digest(canonicalJSON([{type:'text',text}]))}}};
 }});
 let binding=await f.claim('shared-first'),execution=await f.execute(binding);await assert.rejects(execution.job,{code:'HOST_MAIN_POOL_FAILED'});
 const first=(await f.runtime.runs.read(f.run.run_id)).state.nodes.pages.attempts[0];assert.deepEqual(Object.keys(first.main_item_results),['0','2']);
 await f.runtime.failNode(f.run.run_id,{...binding,error:{code:'FIXTURE_FAILED',message:'one missing item'}});execution.entry.status='failed';await f.manager.stopRun(f.run.run_id);
 await f.runtime.retryNode(f.run.run_id,{node_id:'pages',control_token:f.run.control_token,reconciliation:{attempt_id:binding.attempt_id,dispatch_request_id:`dispatch-${binding.attempt_id}`,outcome:'terminated',evidence:[{fixture:true}]}});
 fail=false;const previous=f.created.length;binding=await f.claim('shared-retry');execution=await f.execute(binding);await execution.job;
 const record=await f.runtime.runs.read(f.run.run_id);assert.equal(setups,2);assert.deepEqual(f.created.slice(previous).map(item=>item.index),[1]);assert.equal(record.state.nodes.pages.attempts[1].main_item_results[0].turn_id,first.main_item_results[0].turn_id);
 assert.equal(record.state.cost_ledger.calls[1].usage.input_tokens,17);
});

test('shared prefix cleanup failure stays observable and owned for recovery',async t=>{
 let deny=true;const f=await fixture(t,{sharedPrefix:{common_inputs:[]},prefixFactory:async(options,text)=>{
  await options.resolveModelSelection({});options.onPrefixOwned({interrupt:async()=>{},close:async()=>{if(deny)throw Object.assign(new Error('owned prefix cleanup failed'),{code:'PREFIX_CLEANUP'});}});
  return {prefix:{},setup:{thread_id:'setup-thread',turn_id:'setup-turn',output:'{"ready":true}',usage:{available:true,input_tokens:7,output_tokens:1},audit:{input_sha256:digest(canonicalJSON([{type:'text',text}]))}}};
 }});
 const binding=await f.claim('cleanup-failure'),execution=await f.execute(binding);
 await assert.rejects(execution.job,error=>error.code==='HOST_MAIN_POOL_FAILED'&&error.errors.some(item=>item.code==='PREFIX_CLEANUP'));
 deny=false;assert(execution.entry.prefixOwner);assert.equal((await f.runtime.runs.read(f.run.run_id)).state.nodes.pages.status,'running');
});

test('Main worker fan-out preserves its graph contract and excludes orchestration multiplication',()=>{
 const ready=graph();assert.equal(validateWorkflowGraph(ready,{providers:[]}).valid,true);
 ready.nodes.find(node=>node.id==='pages').executor.mode='orchestration';assert.equal(validateWorkflowGraph(ready,{providers:[]}).valid,false);
});

test('fanout shares one exact authenticated parent policy across fresh item sessions and keeps item scopes',async t=>{
 const context={parent_thread_id:'01a0db25-ad92-72a0-b6fa-2519a6cfa2f8',sandbox_type:'danger-full-access'};
 const f=await fixture(t,{mainExecutionContext:context});
 const binding=await f.claim('inherited-policy'),execution=await f.execute(binding);await execution.job;
 assert.equal(f.modelReads(),1);assert.equal(f.selections.length,3);
 for(const selected of f.selections)assert.deepEqual(selected.main_execution_context,context);
 assert.notEqual(f.selections[0].main_execution_context,f.selections[1].main_execution_context);
 assert.equal(new Set(f.created.map(item=>item.options.cwd)).size,3);
 for(const item of f.created){assert.deepEqual(item.options.allowedPaths,['.']);assert.equal(item.options.isolatedWorkspace,undefined,'Main fanout must not add an OS isolation probe');}
});

test('fanout rejects a writable node contradicting its actual read-only initiating Main before any item turn',async t=>{
 const f=await fixture(t,{mainExecutionContext:{parent_thread_id:'01a0db25-ad92-72a0-b6fa-2519a6cfa2f8',sandbox_type:'read-only'}});
 const binding=await f.claim('read-only-parent'),execution=await f.execute(binding);
 await assert.rejects(execution.job,error=>error instanceof AggregateError&&error.errors.length>0
   &&error.errors.every(item=>item.code==='MAIN_EXECUTION_POLICY'));
 assert.equal(f.prompts.length,0);assert.equal(f.created.length,0);assert.equal(f.modelReads(),1);
});

test('Main writable fan-out requires typed Host-owned workspace directory records',()=>{
 const invalid=(workflow,code)=>assert(validateWorkflowGraph(workflow,{providers:[]}).errors.some(item=>item.code===code));
 let workflow=structuredClone(graph());delete workflow.nodes.find(node=>node.id==='pages').fanout.workspace_field;invalid(workflow,'HOST_MAIN_WORKSPACE_ISOLATION');
 workflow=structuredClone(graph());workflow.inputs_schema.properties.jobs.items.required=['name','destinations'];invalid(workflow,'HOST_MAIN_WORKSPACE_SCHEMA');
 workflow=structuredClone(graph());workflow.inputs_schema.properties.jobs.items.properties.workspace={type:'integer'};invalid(workflow,'HOST_MAIN_WORKSPACE_SCHEMA');
 workflow=structuredClone(graph());workflow.nodes.find(node=>node.id==='pages').input_bindings.jobs='/nodes/final/output/jobs';workflow.nodes.find(node=>node.id==='final').outputs_schema=object({jobs:jobsSchema});invalid(workflow,'SUBAGENT_ITEM_SOURCE');
});

for(const phase of ['qualification','shutdown'])test(`Main fanout journals real ${phase} session callback shapes before item acceptance`,async t=>{
 const pending=Array.from({length:70},(_,index)=>`owned-process-${index}`);
 const f=await fixture(t,{jobs:[{name:'a',workspace:'pages/a',destinations:['pages/a']}],
   factory:async({options})=>{if(phase==='qualification')await options.onEvent({method:'workflow/command',phase:'isolation_begin',process_id:'isolation-probe'});},
   close:async({options})=>{if(phase==='shutdown')await options.onEvent({method:'workflow/sessionShutdown',phase:'begin',pending_process_ids:pending});}});
 const binding=await f.claim(`callback-${phase}`),execution=await f.execute(binding);await execution.job;
 const attempt=(await f.runtime.runs.read(f.run.run_id)).state.nodes.pages.attempts[0];
 assert(attempt.main_item_results[0]);
 const metadata=attempt.executor_events.find(event=>event.kind==='codex_event'&&event.metadata.method===(phase==='qualification'?'workflow/command':'workflow/sessionShutdown'))?.metadata;
 assert.equal(metadata.status,phase==='qualification'?'isolation_begin':'begin');
 const detail=JSON.parse(metadata.diagnostic);
 if(phase==='qualification')assert.equal(detail.process_id,'isolation-probe');
 else{assert.equal(detail.pending_command_count,70);assert.equal(detail.pending_ids_complete,false);assert.deepEqual(detail.pending_process_ids,pending.slice(0,64));}
});

test('real Main Manager → Runtime overlaps bounded item sessions and joins in input order',async t=>{
 const entered=[deferred(),deferred(),deferred()],release=[deferred(),deferred()];let active=0,max=0;
 const f=await fixture(t,{turn:async({index})=>{active++;max=Math.max(max,active);entered[index].resolve();if(index<2)await release[index].promise;active--;}});
 const binding=await f.claim('initial'),execution=await f.execute(binding);await Promise.race([Promise.all(entered.slice(0,2).map(gate=>gate.promise)),execution.job]);assert.equal(active,2);assert.equal(f.created.length,2);
 release[1].resolve();await Promise.race([entered[2].promise,execution.job]);release[0].resolve();await execution.job;
 const record=await f.runtime.runs.read(f.run.run_id),node=record.state.nodes.pages;assert.equal(node.status,'succeeded');assert.deepEqual(node.output,{results:[{conclusion:'a'},{conclusion:'b'},{conclusion:'c'}]});assert.equal(max,2);assert.equal(f.modelReads(),1);assert(f.created.every(item=>item.closed()));assert(f.selections.every(selection=>selection.model==='initiating-main'));
 for(const prompt of f.prompts){const sibling=prompt.index===0?'b':'a';assert(!prompt.text.includes(JSON.stringify({name:sibling,destinations:[`pages/${sibling}.txt`]})));}
 assert.equal(Object.keys(node.attempts[0].main_item_results).length,3);
});

for(const inherited of [false,true])test(`Main full-plan overlap is rejected before session creation including accepted siblings (${inherited})`,async t=>{
 const f=await fixture(t);const binding=await f.claim('overlap');
 await f.runtime.runs.mutate(f.run.run_id,'executor_event',state=>{state.inputs.jobs=[{name:'a',workspace:'pages/a',destinations:['pages/a']},{name:'b',workspace:'pages/a/b',destinations:['pages/a/b.txt']}];});
 if(inherited)await f.runtime.runs.mutate(f.run.run_id,'executor_event',state=>{const attempt=state.nodes.pages.attempts[0];attempt.main_item_results={0:{result:{conclusion:'accepted'}}};attempt.inherited_main_item_indices=[0];});
 const execution=await f.execute(binding);await assert.rejects(execution.job,{code:'SUBAGENT_ITEM_WRITE_OVERLAP'});assert.equal(f.created.length,0);
 const record=await f.runtime.runs.read(f.run.run_id);assert.equal(record.state.nodes.pages.attempts[0].dispatch.receipt,null);execution.entry.status='failed';
});

test('Main failed-item recovery retains accepted siblings and starts only missing items',async t=>{
 let fail=true;const f=await fixture(t,{turn:async({index})=>{if(index===1&&fail)throw Object.assign(new Error('fixture item failed'),{code:'FIXTURE_ITEM_FAILED'});}});
 let binding=await f.claim('first'),execution=await f.execute(binding);await assert.rejects(execution.job,{code:'HOST_MAIN_POOL_FAILED'});
 const before=await f.runtime.runs.read(f.run.run_id),first=before.state.nodes.pages.attempts[0];assert.deepEqual(Object.keys(first.main_item_results),['0','2']);assert.equal(first.main_item_turns[1],1);
 await f.runtime.failNode(f.run.run_id,{...binding,error:{code:'FIXTURE_ITEM_FAILED',message:'Retained fixture failure'}});execution.entry.status='failed';await f.manager.stopRun(f.run.run_id);
 await f.runtime.retryNode(f.run.run_id,{node_id:'pages',control_token:f.run.control_token,reconciliation:{attempt_id:binding.attempt_id,dispatch_request_id:`dispatch-${binding.attempt_id}`,outcome:'terminated',evidence:[{fixture:true}]}});
 fail=false;binding=await f.claim('retry');const previous=f.created.length;execution=await f.execute(binding);await execution.job;assert.deepEqual(f.created.slice(previous).map(item=>item.index),[1]);
 const after=await f.runtime.runs.read(f.run.run_id);assert.equal(after.state.nodes.pages.status,'succeeded');assert.deepEqual(after.state.nodes.pages.output,{results:[{conclusion:'a'},{conclusion:'b'},{conclusion:'c'}]});assert.equal(after.state.nodes.pages.attempts[1].main_item_results[0].turn_id,first.main_item_results[0].turn_id);
});

test('Main cancellation closes every admitted item session and never starts queued items',async t=>{
 const entered=[deferred(),deferred()];const f=await fixture(t,{turn:async({index,gate})=>{entered[index].resolve();await gate.promise;}});
 const binding=await f.claim('cancel'),execution=await f.execute(binding);await Promise.race([Promise.all(entered.map(gate=>gate.promise)),execution.job]);await f.manager.stopRun(f.run.run_id);await assert.rejects(execution.job,error=>['HOST_MAIN_POOL_FAILED','HOST_MAIN_STOPPED'].includes(error.code));assert.equal(f.created.length,2);assert(f.created.every(item=>item.closed()));
});



test('Main partitions close each isolated item session before its next item and join every item',async t=>{
 const f=await fixture(t,{partition:true});const binding=await f.claim('partition'),execution=await f.execute(binding);await execution.job;
 assert.equal(f.created.length,3);assert.equal(f.prompts.length,3);assert.equal(f.modelReads(),1);
 const record=await f.runtime.runs.read(f.run.run_id);assert.deepEqual(record.state.nodes.pages.output,{results:[{conclusion:'a'},{conclusion:'b'},{conclusion:'c'}]});
});

test('Main pool retains item failures alongside usage persistence failures',async t=>{
 const f=await fixture(t,{turn:async({index})=>{if(index===1)throw Object.assign(new Error('original item failure'),{code:'FIXTURE_ITEM_FAILED'});}});
 f.runtime.recordHostMainUsage=async()=>{throw Object.assign(new Error('usage persistence failed'),{code:'FIXTURE_USAGE_FAILED'});};
 const binding=await f.claim('failure-evidence'),execution=await f.execute(binding);
 await assert.rejects(execution.job,error=>error.code==='HOST_MAIN_POOL_FAILED'&&error.errors.some(item=>item.code==='FIXTURE_ITEM_FAILED')&&error.errors.some(item=>item.code==='FIXTURE_USAGE_FAILED'));
});

async function actualRunnerBroker(options){
 const execute=promisify(execFile),client={async call(_method,params){
   try{const result=await execute(params.command[0],params.command.slice(1),{cwd:params.cwd,env:{...process.env,...params.env},windowsHide:true,maxBuffer:4*1024*1024});return {...result,exitCode:0};}
   catch(error){if(!Number.isInteger(error.code))throw error;return {exitCode:error.code,stdout:error.stdout,stderr:error.stderr};}
 },async close(){}};
 return createCodexCommandBroker({binary:process.execPath,home:options.cwd,cwd:options.cwd,access:'bounded_write',allowedPaths:['.'],spoolRoot:join(options.cwd,'.fixture-command-spool'),getClient:()=>client,getOutputBudget:()=>({max_result_bytes:4096})});
}

test('Main accepts item effects only after actual background runner completion and final command evidence', {skip:process.platform!=='win32'},async t=>{
 let commands,background;const enteredClose=deferred(),releaseClose=deferred();
 const f=await fixture(t,{jobs:[{name:'a',workspace:'pages/a',destinations:['pages/a']}],turn:async({options,session})=>{
   commands=await actualRunnerBroker(options);session.commandAudit=()=>commands.audit();
   const response=await commands.call('run_workspace_command',{cmd:"Start-Sleep -Milliseconds 80; [IO.File]::WriteAllText('late.txt','late effect')",yield_time_ms:0,login:false},'late-command');background=JSON.parse(response.contentItems[0].text);assert.equal(background.status,'running');
 },close:async()=>{enteredClose.resolve();await releaseClose.promise;await commands.call('continue_workspace_command',{session_id:background.session_id},'late-drain');await commands.close();}});
 const binding=await f.claim('late-write'),execution=await f.execute(binding);await Promise.race([enteredClose.promise,execution.job]);
 const pending=await f.runtime.runs.read(f.run.run_id);assert.equal(Object.keys(pending.state.nodes.pages.attempts[0].main_item_results??{}).length,0);
 releaseClose.resolve();await execution.job;
 const accepted=(await f.runtime.runs.read(f.run.run_id)).state.nodes.pages.attempts[0].main_item_results[0];assert(accepted.changed_paths.includes('pages/a/late.txt'));assert.equal(await readFile(join(f.workspace,'pages/a/late.txt'),'utf8'),'late effect');
 const proposalPin=(await f.runtime.runs.read(f.run.run_id)).state.nodes.pages.attempts[0].result_proposal.sha256;
 const proposal=await f.runtime.runs.readExecutorResult(f.run.run_id,binding.attempt_id,proposalPin);assert(proposal.evidence.some(item=>item.kind==='command_audit'&&item.command_count===1));
});

test('Main never inherits semantic output when actual unfinished background command drain is cancelled', {skip:process.platform!=='win32'},async t=>{
 let commands;const f=await fixture(t,{jobs:[{name:'a',workspace:'pages/a',destinations:['pages/a']}],turn:async({options,session})=>{
   commands=await actualRunnerBroker(options);session.commandAudit=()=>commands.audit();
   await commands.call('run_workspace_command',{cmd:"Start-Sleep -Seconds 10; [IO.File]::WriteAllText('too-late.txt','unaccepted')",yield_time_ms:0,login:false},'unfinished-command');
 },close:async()=>commands.close()});
 const binding=await f.claim('drain-failure'),execution=await f.execute(binding);await assert.rejects(execution.job,error=>error.code==='HOST_MAIN_POOL_FAILED'&&error.errors.some(item=>item.code==='CODEX_COMMAND_SHUTDOWN_CANCELLED'));
 const record=await f.runtime.runs.read(f.run.run_id);assert.equal(Object.keys(record.state.nodes.pages.attempts[0].main_item_results??{}).length,0);assert.equal(commands.audit()[0].status,'cancelled');execution.entry.status='failed';await f.manager.stopRun(f.run.run_id);
});

for(const metered of [true,false])test(`all inherited Main retry records explicit zero-call usage and preserves previous accounting (${metered})`,async t=>{
 const f=await fixture(t,{requireUsage:true,...(!metered?{usage:{available:false}}:{})}),save=f.runtime.runs.saveExecutorResult.bind(f.runtime.runs);let fail=true;
 f.runtime.runs.saveExecutorResult=async(...args)=>{if(fail){fail=false;throw Object.assign(new Error('post-item proposal persistence failed'),{code:'FIXTURE_PROPOSAL_FAILED'});}return save(...args);};
 let binding=await f.claim('all-accepted'),execution=await f.execute(binding);await assert.rejects(execution.job,{code:'FIXTURE_PROPOSAL_FAILED'});
 const first=await f.runtime.runs.read(f.run.run_id);assert.equal(Object.keys(first.state.nodes.pages.attempts[0].main_item_results).length,3);const priorUsage=structuredClone(first.state.cost_ledger.calls[0].usage);assert.equal(priorUsage.input_tokens,metered?30:undefined);assert.equal(first.state.cost_ledger.uncertain_micros,1);
 await f.runtime.failNode(f.run.run_id,{...binding,error:{code:'FIXTURE_PROPOSAL_FAILED',message:'Retained post-item failure'}});execution.entry.status='failed';await f.manager.stopRun(f.run.run_id);
 await f.runtime.retryNode(f.run.run_id,{node_id:'pages',control_token:f.run.control_token,reconciliation:{attempt_id:binding.attempt_id,dispatch_request_id:`dispatch-${binding.attempt_id}`,outcome:'terminated',evidence:[{fixture:true}]}});
 const created=f.created.length;binding=await f.claim('all-inherited');execution=await f.execute(binding);await execution.job;
 const after=await f.runtime.runs.read(f.run.run_id);assert.equal(f.created.length,created);assert.equal(after.state.nodes.pages.status,'succeeded');assert.deepEqual(after.state.cost_ledger.calls[0].usage,priorUsage);assert.deepEqual(after.state.cost_ledger.calls[1].usage,{unknown:false,cost_micros:0,input_tokens:0,cached_input_tokens:0,cache_write_input_tokens:0,output_tokens:0,reasoning_output_tokens:0});
 assert.equal(after.state.cost_ledger.uncertain_micros,1);assert.equal(after.state.cost_ledger.unknown_usage_count,1);
});

test('Main rejects file-only workspace grants before creating any item session',async t=>{
 const f=await fixture(t);const binding=await f.claim('file-only');
 await f.runtime.runs.mutate(f.run.run_id,'executor_event',state=>{state.inputs.jobs[0].destinations=['pages/a/output.txt'];});
 const execution=await f.execute(binding);await assert.rejects(execution.job,{code:'HOST_MAIN_WORKSPACE_ISOLATION'});assert.equal(f.created.length,0);execution.entry.status='failed';
});

test('Main waits for the exact item resource broker drain before accepting its effects',async t=>{
 const entered=deferred(),release=deferred();let drains=0;
 const f=await fixture(t,{jobs:[{name:'a',workspace:'pages/a',destinations:['pages/a']}],factory:async({options})=>{
   const drain=options.toolBroker.quiesce.bind(options.toolBroker);
   options.toolBroker.quiesce=async()=>{drains++;entered.resolve();await release.promise;await writeFile(join(options.cwd,'resource-drain.txt'),'settled resource effect');return drain();};
 }});
 const binding=await f.claim('resource-drain'),execution=await f.execute(binding);await Promise.race([entered.promise,execution.job]);
 assert.equal(Object.keys((await f.runtime.runs.read(f.run.run_id)).state.nodes.pages.attempts[0].main_item_results??{}).length,0);
 release.resolve();await execution.job;assert.equal(drains,1);
 assert((await f.runtime.runs.read(f.run.run_id)).state.nodes.pages.attempts[0].main_item_results[0].changed_paths.includes('pages/a/resource-drain.txt'));
});

for(const mode of ['reported_error','unconfirmed'])test(`Main does not accept output when broker drain returns ${mode}`,async t=>{
 let attempts=0;
 const f=await fixture(t,{jobs:[{name:'a',workspace:'pages/a',destinations:['pages/a']}],factory:async({options})=>{
   const drain=options.toolBroker.quiesce.bind(options.toolBroker);
   options.toolBroker.quiesce=async()=>{if(attempts++===0)return mode==='reported_error'?{quiescent:true,error:Object.assign(new Error('resource queue failed'),{code:'FIXTURE_RESOURCE_DRAIN'})}:{quiescent:false};return drain();};
 }});
 const binding=await f.claim(mode),execution=await f.execute(binding);
 await assert.rejects(execution.job,error=>error.code==='HOST_MAIN_POOL_FAILED'&&error.errors.some(item=>item.code===(mode==='reported_error'?'FIXTURE_RESOURCE_DRAIN':'CODEX_BROKER_STOP_UNCONFIRMED')));
 assert.equal(Object.keys((await f.runtime.runs.read(f.run.run_id)).state.nodes.pages.attempts[0].main_item_results??{}).length,0);
 assert.equal(execution.entry.brokers.length,1);execution.entry.status='failed';await f.manager.stopRun(f.run.run_id);assert.equal(attempts,2);
});

test('Main never inherits output when item session close fails after a late effect',async t=>{
 let closes=0;
 const f=await fixture(t,{jobs:[{name:'a',workspace:'pages/a',destinations:['pages/a']}],close:async({options})=>{
   if(closes++===0){await writeFile(join(options.cwd,'late-before-failed-close.txt'),'unaccepted');throw Object.assign(new Error('item close failed'),{code:'FIXTURE_CLOSE_FAILED'});}
 }});
 const binding=await f.claim('failed-close'),execution=await f.execute(binding);
 await assert.rejects(execution.job,error=>error.code==='HOST_MAIN_POOL_FAILED'&&error.errors.some(item=>item.code==='FIXTURE_CLOSE_FAILED'));
 assert.equal(Object.keys((await f.runtime.runs.read(f.run.run_id)).state.nodes.pages.attempts[0].main_item_results??{}).length,0);
 assert.equal(execution.entry.sessions.length,1);execution.entry.status='failed';await f.manager.stopRun(f.run.run_id);
});

test('Main required artifact checks use Windows path case at item join and runtime acceptance',{skip:process.platform!=='win32'},async t=>{
 const f=await fixture(t,{jobs:[{name:'a',workspace:'pages/a',destinations:['pages/a']}],requiredArtifacts:[{requirement_id:'page_output',path:'PAGES/A/OUTPUT.TXT'}]});
 const binding=await f.claim('artifact-case'),execution=await f.execute(binding);await execution.job;
 assert.equal((await f.runtime.runs.read(f.run.run_id)).state.nodes.pages.status,'succeeded');
});

test('worker Host check renders each exact item before acceptance with one model turn',async t=>{
 const check=workerCheckFixture(),f=await fixture(t,{hostCheck:check,requiredArtifacts:[{path:'pages/a/rendered.txt',requirement_id:'rendered'}]});
 const binding=await f.claim('host-check'),execution=await f.execute(binding);await execution.job;
 assert.equal(f.created.length,3);assert.equal(f.prompts.length,3);assert.equal(check.calls.length,3);
 for(const call of check.calls){assert.equal(call.input.inputs.jobs.length,1);const item=call.input.inputs.jobs[0];assert.equal(call.input.output.conclusion,item.name);assert.equal(call.context.workspace,join(f.workspace,item.workspace));assert.deepEqual(call.permissions.write_paths,['.']);}
 const state=(await f.runtime.runs.read(f.run.run_id)).state;assert.equal(state.nodes.pages.status,'succeeded');assert.equal(Object.keys(state.nodes.pages.attempts[0].worker_host_checks).length,3);
});

test('false worker Host verdict corrects the same ephemeral item session and meters every turn',async t=>{
 const check=workerCheckFixture({accept:(_request,count)=>count===2}),f=await fixture(t,{hostCheck:check,requireUsage:true});
 const binding=await f.claim('host-correction'),execution=await f.execute(binding);await execution.job;
 assert.equal(f.created.length,3);assert.equal(f.prompts.length,6);assert.equal(check.calls.length,6);
 assert(f.prompts.filter(item=>item.text.includes('Revise this page conclusion.')).length===3);
 const attempt=(await f.runtime.runs.read(f.run.run_id)).state.nodes.pages.attempts[0];assert.deepEqual(attempt.main_item_turns,{0:2,1:2,2:2});assert.equal(Object.keys(attempt.worker_host_checks).length,6);
 assert.equal((await f.runtime.runs.read(f.run.run_id)).state.cost_ledger.calls[0].usage.input_tokens,60);
});

test('worker Host false exhaustion is explicit and never accepts a rendered item',async t=>{
 const check=workerCheckFixture({accept:()=>false}),f=await fixture(t,{hostCheck:check,jobs:[{name:'a',workspace:'pages/a',destinations:['pages/a']}]});
 const binding=await f.claim('exhausted'),execution=await f.execute(binding);await assert.rejects(execution.job,error=>error.code==='HOST_MAIN_POOL_FAILED'&&error.errors.some(item=>item.code==='MAIN_WORKER_HOST_CHECK_FALSE'));
 const attempt=(await f.runtime.runs.read(f.run.run_id)).state.nodes.pages.attempts[0];assert.equal(attempt.main_item_turns[0],3);assert.equal(check.calls.length,3);assert.deepEqual(attempt.main_item_results,{});execution.entry.status='failed';
});

test('worker Host component correction budget supports six same-session turns independent of a style budget',async t=>{
 const check=workerCheckFixture({accept:(_request,count)=>count===6});check.maxAttempts=10;
 const f=await fixture(t,{hostCheck:check,jobs:[{name:'a',workspace:'pages/a',destinations:['pages/a']}]});
 const binding=await f.claim('six-component-turns'),execution=await f.execute(binding);await execution.job;
 assert.equal(f.created.length,1);assert.equal(f.prompts.length,6);assert.equal(check.calls.length,6);assert.equal((await f.runtime.runs.read(f.run.run_id)).state.nodes.pages.attempts[0].main_item_turns[0],6);
});

for(const mode of ['throw','invalid_output'])test(`worker Host ${mode} records exact confirmed termination and accepts no item`,async t=>{
 const check=workerCheckFixture({execute:async()=>{if(mode==='throw')throw Object.assign(new Error('renderer failed'),{code:'FIXTURE_RENDER_THROW'});return {exit_code:0,output:{ok:'invalid',diagnostic:''},diagnostic:'',effects:{observed:true,changed_paths:[],outside_paths:[],artifacts:[]}};}});
 const f=await fixture(t,{hostCheck:check,jobs:[{name:'a',workspace:'pages/a',destinations:['pages/a']}]});
 const binding=await f.claim(mode),execution=await f.execute(binding);await assert.rejects(execution.job,{code:'HOST_MAIN_POOL_FAILED'});
 const attempt=(await f.runtime.runs.read(f.run.run_id)).state.nodes.pages.attempts[0],slot=Object.values(attempt.worker_host_checks)[0];assert.equal(slot.receipt.status,'cancelled');assert.equal(slot.receipt.reconciliation.termination_confirmed,true);assert.deepEqual(attempt.main_item_results,{});assert.equal(f.prompts.length,1);assert.equal(execution.entry.workerChecks.size,0);execution.entry.status='failed';
});

test('worker Host checks keep mechanical baseline inputs outside model context and project the exact page singleton',async t=>{
 const check=workerCheckFixture();check.inputSchemas={mechanical_manifest:{type:'string'}};check.inputs={mechanical_manifest:'mechanical_secret_original_baseline'};check.input_bindings={jobs:'/inputs/jobs',manifest:'/inputs/mechanical_manifest'};
 check.contract.input_schema.properties.inputs.properties.manifest={type:'string'};check.contract.input_schema.properties.inputs.required.push('manifest');
 const f=await fixture(t,{hostCheck:check}),binding=await f.claim('host-only'),execution=await f.execute(binding);await execution.job;
 for(const call of check.calls){assert.equal(call.input.inputs.manifest,check.inputs.mechanical_manifest);assert.equal(call.input.inputs.jobs.length,1);}
 assert(f.prompts.every(item=>!item.text.includes(check.inputs.mechanical_manifest)));assert(f.prompts.every(item=>!item.text.includes('mechanical_manifest')));
});

test('worker Host receipt exact replay validates artifacts, rejects conflicts and tampered output',async t=>{
 const check=workerCheckFixture(),f=await fixture(t,{hostCheck:check,jobs:[{name:'a',workspace:'pages/a',destinations:['pages/a']}]});
 const binding=await f.claim('receipt-replay'),execution=await f.execute(binding);await execution.job;
 const slot=Object.values((await f.runtime.runs.read(f.run.run_id)).state.nodes.pages.attempts[0].worker_host_checks)[0];
 await f.runtime.recordWorkerHostCheckReceipt(f.run.run_id,{...binding,slot_id:slot.identity.slot_id,receipt:slot.receipt});assert.equal(check.calls.length,1);
 await assert.rejects(f.runtime.recordWorkerHostCheckReceipt(f.run.run_id,{...binding,slot_id:slot.identity.slot_id,receipt:{...slot.receipt,duration_ms:slot.receipt.duration_ms+1}}),{code:'HOST_TOOL_CONFLICT'});
 const stored=await f.runtime.runs.readExecutorResult(f.run.run_id,binding.attempt_id,slot.receipt.output_ref.sha256);stored.output.ok=false;await writeFile(join(f.runtime.runs.directory(f.run.run_id),slot.receipt.output_ref.artifact),canonicalJSON(stored));
 await assert.rejects(f.runtime.recordWorkerHostCheckReceipt(f.run.run_id,{...binding,slot_id:slot.identity.slot_id,receipt:slot.receipt}),{code:'EXECUTOR_RESULT_CORRUPT'});
});

test('worker Host check rejects a narrowed item directory grant before model or renderer effects',async t=>{
 const check=workerCheckFixture(),f=await fixture(t,{hostCheck:check});const binding=await f.claim('checker-file-only');
 await f.runtime.runs.mutate(f.run.run_id,'executor_event',state=>{state.inputs.jobs[0].destinations=['pages/a/rendered.txt'];});
 const execution=await f.execute(binding);await assert.rejects(execution.job,{code:'HOST_MAIN_WORKSPACE_ISOLATION'});assert.equal(f.created.length,0);assert.equal(check.calls.length,0);execution.entry.status='failed';
});

test('worker Host cancellation stops the exact checker slot before item acceptance',async t=>{
 const started=deferred(),release=deferred();let cancelled;
 const check=workerCheckFixture({execute:async request=>{started.resolve();await release.promise;return {exit_code:0,output:{ok:true,diagnostic:''},diagnostic:'',effects:{observed:true,changed_paths:[],outside_paths:[],artifacts:[]}};}});
 const originalCancel=check.broker.cancel;check.broker.cancel=async request=>{cancelled=request.context;release.resolve();return originalCancel(request);};
 const f=await fixture(t,{hostCheck:check,jobs:[{name:'a',workspace:'pages/a',destinations:['pages/a']}]});
 const binding=await f.claim('checker-cancel'),execution=await f.execute(binding);await started.promise;f.manager.fenceRun(f.run.run_id);await assert.rejects(execution.job,{code:'HOST_MAIN_POOL_FAILED'});
 const attempt=(await f.runtime.runs.read(f.run.run_id)).state.nodes.pages.attempts[0];assert.equal(cancelled.execution_slot,'item-0-turn-1');assert.deepEqual(attempt.main_item_results,{});assert.equal(Object.values(attempt.worker_host_checks)[0].receipt.reconciliation.termination_confirmed,true);execution.entry.status='failed';
});

for(const falseTurns of [0,1])test(`single worker Host check uses its existing same-session lifecycle (${falseTurns} correction)`,async t=>{
 const check=workerCheckFixture({accept:(_request,count)=>count>falseTurns}),f=await fixture(t,{hostCheck:check,single:true,jobs:[{name:'a',workspace:'pages/a',destinations:['pages/a']}],requiredArtifacts:[{path:'rendered.txt',requirement_id:'rendered'}]});
 const binding=await f.claim('single-check'),execution=await f.execute(binding);await execution.job;
 assert.equal(f.created.length,1);assert.equal(f.prompts.length,1+falseTurns);assert.equal(check.calls.length,1+falseTurns);assert.equal(check.calls[0].context.workspace,f.workspace);assert.equal((await f.runtime.runs.read(f.run.run_id)).state.nodes.pages.status,'succeeded');
});

test('worker Host checks execute pinned resource programs in isolated item cwd without model code resources',async t=>{
 const check=workerCheckFixture();check.contract.identity=workflowResourceProgramIdentity();check.contract.argv=['node','host/render.mjs','.host-check','@INPUT@'];check.contract.deadline_ms=10000;
 check.resources={'host/render.mjs':'import {readFileSync,writeFileSync} from "node:fs";const input=JSON.parse(readFileSync(process.argv[2],"utf8"));if(input.inputs.jobs.length!==1||input.inputs.jobs[0].name!==input.output.conclusion)throw new Error("item routing mismatch");writeFileSync("rendered.txt",input.output.conclusion);console.log(JSON.stringify({ok:true,diagnostic:""}));'};
 check.runner=new HostToolRunner({registry:workflowResourceProgramRegistry(),env:process.env});
 const f=await fixture(t,{hostCheck:check}),binding=await f.claim('actual-resource'),execution=await f.execute(binding);await execution.job;
 for(const item of f.created){assert.deepEqual(item.options.toolBroker.tools(),[]);assert(!f.prompts.find(prompt=>prompt.index===item.index).text.includes('host/render.mjs'));assert.equal(await readFile(join(item.options.cwd,'rendered.txt'),'utf8'),['a','b','c'][item.index]);}
 const attempt=(await f.runtime.runs.read(f.run.run_id)).state.nodes.pages.attempts[0];assert.equal(Object.keys(attempt.worker_host_checks).length,3);assert(Object.values(attempt.worker_host_checks).every(slot=>slot.receipt.status==='succeeded'));
});

for(const single of [false,true])test(`worker Host same-session correction preserves all diagnostics beyond 900 characters (${single?'single':'fanout'})`,async t=>{
 const diagnostic='First finding. '.repeat(100)+'DECISIVE_END_FINDING: repair the final table.',check=workerCheckFixture({execute:async(_request,count)=>({exit_code:0,output:{ok:count===2,diagnostic:count===2?'':diagnostic},diagnostic:'',effects:{observed:true,changed_paths:[],outside_paths:[],artifacts:[]}})});check.contract.output_cap_bytes=8192;
 const f=await fixture(t,{hostCheck:check,single,jobs:[{name:'a',workspace:'pages/a',destinations:['pages/a']}]});
 const binding=await f.claim('full-diagnostics'),execution=await f.execute(binding);await execution.job;
 assert.equal(f.created.length,1);assert.equal(f.prompts.length,2);assert(f.prompts[1].text.includes(diagnostic));assert(f.prompts[1].text.includes('DECISIVE_END_FINDING'));
});

for(const failedTurn of [1,2])test(`single worker Host meters reserved dispatch failure at turn ${failedTurn} as unknown with known partial evidence`,async t=>{
 let calls=0;const check=workerCheckFixture({accept:(_request,count)=>count===2});
 const f=await fixture(t,{hostCheck:check,single:true,requireUsage:true,jobs:[{name:'a',workspace:'pages/a',destinations:['pages/a']}],turn:async()=>{if(++calls===failedTurn)throw Object.assign(new Error('paid dispatch failed'),{code:'FIXTURE_PAID_DISPATCH'});}});
 const binding=await f.claim('failed-dispatch-meter'),execution=await f.execute(binding);await assert.rejects(execution.job,{code:'FIXTURE_PAID_DISPATCH'});
 const record=await f.runtime.runs.read(f.run.run_id),usage=record.state.cost_ledger.calls[0].usage;assert.equal(usage.unknown,true);assert.equal(usage.input_tokens,undefined);assert.equal(usage.output_tokens,undefined);assert.equal(record.state.nodes.pages.attempts[0].completion_turns,failedTurn);
 const serialized=canonicalJSON(record.events);assert(serialized.includes('HOST_MAIN_USAGE_PARTIAL'));assert(serialized.includes('partial_tokens'));
 execution.entry.status='failed';
});

test('worker Host retry inherits successful sibling receipts and renders only the failed item',async t=>{
 const check=workerCheckFixture({execute:async(request,count)=>{if(request.input.inputs.jobs[0].name==='b'&&count===1)throw Object.assign(new Error('b renderer fault'),{code:'FIXTURE_RENDER_THROW'});await writeFile(join(request.context.workspace,'rendered.txt'),request.input.output.conclusion);return {exit_code:0,output:{ok:true,diagnostic:''},diagnostic:'',effects:{observed:true,changed_paths:['rendered.txt'],outside_paths:[],artifacts:[]}};}});
 const f=await fixture(t,{hostCheck:check});let binding=await f.claim('failed-checker'),execution=await f.execute(binding);await assert.rejects(execution.job,{code:'HOST_MAIN_POOL_FAILED'});
 const first=(await f.runtime.runs.read(f.run.run_id)).state.nodes.pages.attempts[0];assert.deepEqual(Object.keys(first.main_item_results),['0','2']);
 await f.runtime.failNode(f.run.run_id,{...binding,error:{code:'FIXTURE_RENDER_THROW',message:'Retain renderer fault'}});execution.entry.status='failed';await f.manager.stopRun(f.run.run_id);
 await f.runtime.retryNode(f.run.run_id,{node_id:'pages',control_token:f.run.control_token,reconciliation:{attempt_id:binding.attempt_id,dispatch_request_id:`dispatch-${binding.attempt_id}`,outcome:'terminated',evidence:[{fixture:true}]}});
 binding=await f.claim('checker-retry');execution=await f.execute(binding);await execution.job;
 assert.deepEqual(f.created.map(item=>item.index),[0,1,2,1]);assert.deepEqual(check.calls.map(call=>call.input.inputs.jobs[0].name),['a','b','c','b']);
 const state=(await f.runtime.runs.read(f.run.run_id)).state;assert.equal(state.nodes.pages.status,'succeeded');assert.deepEqual(state.nodes.pages.attempts[1].main_item_results[0],first.main_item_results[0]);
});

test('worker Host correction exceeding the actual input bound fails explicitly without dropping diagnostics',async t=>{
 const check=workerCheckFixture({execute:async()=>({exit_code:0,output:{ok:false,diagnostic:'Full finding. '.repeat(16000)},diagnostic:'',effects:{observed:true,changed_paths:[],outside_paths:[],artifacts:[]}})});check.contract.output_cap_bytes=512*1024;
 const f=await fixture(t,{hostCheck:check,jobs:[{name:'a',workspace:'pages/a',destinations:['pages/a']}]}),binding=await f.claim('diagnostic-overflow'),execution=await f.execute(binding);
 await assert.rejects(execution.job,error=>error.code==='HOST_MAIN_POOL_FAILED'&&error.errors.some(item=>item.code==='CODEX_INPUT_LIMIT'));assert.equal(f.prompts.length,1);assert.equal(check.calls.length,1);execution.entry.status='failed';
});

for(const single of [false,true])test(`command completion boundary precedes real Host checker (${single?'single':'fanout'})`,{skip:process.platform!=='win32'},async t=>{
 const check=workerCheckFixture();check.contract.identity=workflowResourceProgramIdentity();check.contract.argv=['node','host/render.mjs','.host-check','@INPUT@'];check.contract.deadline_ms=10000;
 check.resources={'host/render.mjs':'import {writeFileSync} from "node:fs";writeFileSync("rendered.txt","qualified");console.log(JSON.stringify({ok:true,diagnostic:""}));'};
 check.runner=new HostToolRunner({registry:workflowResourceProgramRegistry(),env:process.env});
 let commands,settled=0;
 const f=await fixture(t,{single,hostCheck:check,jobs:[{name:'a',workspace:'pages/a',destinations:['pages/a']}],turn:async({options,session})=>{
   commands=await actualRunnerBroker(options);session.commandAudit=()=>commands.audit();
   await commands.call('run_workspace_command',{cmd:"[IO.File]::WriteAllText('source.txt','neutral source')",yield_time_ms:10000,login:false},'real-source');
   await mkdir(join(options.cwd,'.fixture-command-spool','runtime-temp'),{recursive:true});
 },prepare:async()=>{await commands.close();settled++;},close:async()=>commands.close()});
 const binding=await f.claim('settled-real-check'),execution=await f.execute(binding);await execution.job;
 assert.equal(settled,1);assert.equal((await f.runtime.runs.read(f.run.run_id)).state.nodes.pages.status,'succeeded');
 assert.equal(commands.audit().length,1);assert.equal(commands.audit()[0].status,'completed');
});

for(const single of [false,true])test(`SDK worker completion accepts settled renderer metadata without a second whole-workspace check (${single?'single':'three parallel items'})`,async t=>{
 const check=workerCheckFixture();let prepared=0;
 const jobs=single?[{name:'a',workspace:'pages/a',destinations:['pages/a']}]:undefined;
 const f=await fixture(t,{single,hostCheck:check,...(jobs?{jobs}:{}),prepare:async()=>{prepared++;},close:async({options})=>writeFile(join(options.cwd,'runtime-state.json'),'renderer completed background bookkeeping')});
 let snapshotCalls=0;const saveArtifact=f.runtime.runs.saveArtifact.bind(f.runtime.runs);
 f.runtime.runs.saveArtifact=async(id,name,...args)=>{if(name.startsWith('completion-snapshot-'))snapshotCalls++;return saveArtifact(id,name,...args);};
 const binding=await f.claim('settled-renderer-metadata'),execution=await f.execute(binding);await execution.job;
 const record=await f.runtime.runs.read(f.run.run_id),count=single?1:3;
 assert.equal(prepared,count);assert.equal(check.calls.length,count);assert.equal(record.state.nodes.pages.status,'succeeded');assert.equal(snapshotCalls,0);
 for(const call of check.calls)assert.equal(await readFile(join(call.context.workspace,'rendered.txt'),'utf8'),call.input.output.conclusion);
 for(const slot of Object.values(record.state.nodes.pages.attempts[0].worker_host_checks)){
  const stored=await f.runtime.runs.readExecutorResult(f.run.run_id,binding.attempt_id,slot.receipt.output_ref.sha256);
  assert.equal(stored.completion_snapshot,undefined);assert.equal(slot.receipt.status,'succeeded');
 }
});

for(const single of [false,true])test(`command completion boundary failure prevents checker effects (${single?'single':'fanout'})`,async t=>{
 const check=workerCheckFixture();
 const f=await fixture(t,{single,hostCheck:check,jobs:[{name:'a',workspace:'pages/a',destinations:['pages/a']}],prepare:async()=>{throw Object.assign(new Error('owned command cleanup failed'),{code:'FIXTURE_CLEANUP_FAILED'});}});
 const binding=await f.claim('cleanup-failure'),execution=await f.execute(binding);
 await assert.rejects(execution.job,error=>single?error.code==='FIXTURE_CLEANUP_FAILED':error.errors?.some(item=>item.code==='FIXTURE_CLEANUP_FAILED'));
 assert.equal(check.calls.length,0);execution.entry.status='failed';
});

for(const single of [false,true])test(`command completion boundary is mandatory for checker sessions (${single?'single':'fanout'})`,async t=>{
 const check=workerCheckFixture();
 const f=await fixture(t,{single,hostCheck:check,jobs:[{name:'a',workspace:'pages/a',destinations:['pages/a']}],factory:async({session})=>{delete session.prepareHostCompletion;}});
 const binding=await f.claim('missing-command-boundary'),execution=await f.execute(binding);
 await assert.rejects(execution.job,error=>single?error.code==='CODEX_HOST_COMPLETION_BOUNDARY':error.errors?.some(item=>item.code==='CODEX_HOST_COMPLETION_BOUNDARY'));
 assert.equal(check.calls.length,0);execution.entry.status='failed';
});

for(const closeFails of [false,true])test(`ordinary correction retains every settled command generation in durable Run audit (${closeFails?'close failure':'success'})`,{skip:process.platform!=='win32'},async t=>{
 const audits=[];let commands,turns=0,prepared=0;
 const check=workerCheckFixture({accept:(_request,count)=>count===2});
 const f=await fixture(t,{single:true,hostCheck:check,jobs:[{name:'a',workspace:'pages/a',destinations:['pages/a']}],turn:async({options,session})=>{
   turns++;commands=await actualRunnerBroker(options);
   await commands.call('run_workspace_command',{cmd:"[IO.File]::WriteAllText('source.txt','generation "+turns+"')",yield_time_ms:10000,login:false},'source-generation-'+turns);
   session.turnAudit=()=>commands.audit();session.commandAudit=()=>audits.concat(commands.audit().filter(item=>!audits.some(prior=>prior.process_id===item.process_id)));
 },prepare:async()=>{await commands.close();audits.push(...commands.audit());prepared++;},close:async()=>{await commands.close();if(closeFails)throw Object.assign(new Error('visible final model close failure'),{code:'FIXTURE_MODEL_CLOSE_FAILED'});}});
 const binding=await f.claim('generation-audit'),execution=await f.execute(binding);
 if(closeFails){await assert.rejects(execution.job,{code:'FIXTURE_MODEL_CLOSE_FAILED'});execution.entry.status='failed';}
 else await execution.job;
 assert.equal(f.created.length,1);assert.equal(prepared,2);assert.equal(check.calls.length,2);assert.equal(f.prompts.length,2);
 const record=await f.runtime.runs.read(f.run.run_id),attempt=record.state.nodes.pages.attempts[0];
 const event=attempt.executor_events.findLast(item=>item.kind==='session_state'&&item.metadata.diagnostic?.includes('command_audit_artifact'));
 assert(event,'durable command audit reference is visible even when closure fails');const diagnostic=JSON.parse(event.metadata.diagnostic);
 const artifact=JSON.parse(await f.runtime.runs.readArtifact(f.run.run_id,{artifact:diagnostic.command_audit_artifact,sha256:diagnostic.command_audit_sha256,bytes:diagnostic.command_audit_bytes}));
 assert.deepEqual(artifact.records[0].command_audit.map(item=>item.process_id),audits.map(item=>item.process_id));assert.equal(new Set(artifact.records[0].command_audit.map(item=>item.process_id)).size,2);
 if(closeFails){assert.notEqual(record.state.nodes.pages.status,'succeeded');f.created[0].session.close=async()=>{};}
});

for(const shared of [false,true])for(const addressing of [undefined,'host_ranges'])for(const invalid of [null,'outside_scope','full_result'])test('Main fanout seals scoped text repair and rechecks merged content (shared='+shared+', addressing='+addressing+', invalid='+invalid+')',async t=>{
 const config={fields:['conclusion'],repair_scope_field:'repair_scope',max_edits:8,max_replacement_bytes:8192,...(addressing?{addressing}:{})};
 const edit=addressing?{replacements:[['start']]}:{amendments:[{field:'conclusion',start_line:2,end_line:2,replacement:'start\n'}]};
 const line={type:'integer',minimum:1},scopeSchema={type:'object',additionalProperties:false,properties:{conclusion:{type:'array',items:object({start_line:line,end_line:line})}}};
 const check=workerCheckFixture({execute:async(request,count)=>{
   assert.equal(request.input.output.conclusion,count===1?'keep\ninitiate\ntail':'keep\nstart\ntail');
   await writeFile(join(request.context.workspace,'rendered.txt'),request.input.output.conclusion);
   return {exit_code:0,output:{ok:count>1,diagnostic:count===1?'L2 [word] initiate -> start':'',repair_scope:count===1?{conclusion:[{start_line:2,end_line:2}]}:{}},diagnostic:'',effects:{observed:true,changed_paths:['rendered.txt'],outside_paths:[],artifacts:[]}};
 }});
 check.text_amendment=config;check.contract.output_schema.properties.repair_scope=scopeSchema;check.contract.output_schema.required.push('repair_scope');
 let f;const args={hostCheck:check,jobs:[{name:'a',workspace:'pages/a',destinations:['pages/a']}],payloadForTurn:({turn})=>turn===1?{conclusion:'keep\ninitiate\ntail'}:
  turn===2&&invalid?invalid==='full_result'?{conclusion:'unrequested full rewrite'}:addressing?{replacements:[['start'],['extra block']]}:{amendments:[{...edit.amendments[0],start_line:1,end_line:1}]}:edit};
 if(shared){
  const capability={complete_usage:true,reason:'fixture',responseTransport:{create_for_schema:createTypedBatchOutputTransport}};
  args.sharedPrefix={common_inputs:[]};args.prefixCapability=capability;
  args.prefixFactory=async(options,text,turnOptions)=>{
   const transport=createTypedBatchOutputTransport(options.shared_output_schema,{repair_schema:options.shared_repair_schema});
   await options.resolveModelSelection({});options.onPrefixOwned({interrupt:async()=>{},close:async()=>{}});
   const original=[{type:'text',text}],wire=[{type:'text',text:transport.prepare_setup(text,turnOptions.output_schema).text}];
   return {prefix:{},setup:{thread_id:'source-thread',turn_id:'source-ready',output:'{"ready":true}',usage:{available:true,input_tokens:7,output_tokens:1},audit:{
    semantic_input_sha256:digest(canonicalJSON(original)),transported_semantic_input_sha256:digest(canonicalJSON(wire)),input_sha256:digest(canonicalJSON(wire)),submitted_input_sha256:digest(canonicalJSON(wire)),
    response_transport:{api_schema_sha256:transport.api_schema_sha256,semantic_schema_sha256:digest(canonicalJSON(turnOptions.output_schema))},native_shell_execution:'unified_exec',command_declaration_basis:'inherited_native_shell'}},
    openSession:opts=>f.manager.sessionFactory(opts)};
  };
  args.inputAudit=(text,schema)=>{
   const transport=createTypedBatchOutputTransport(result,{repair_schema:textAmendmentSchema(config)});
   const original=[{type:'text',text}],wire=[{type:'text',text:transport.prepare(text,schema).text}];
   return {semantic_input_sha256:digest(canonicalJSON(original)),transported_semantic_input_sha256:digest(canonicalJSON(wire)),input_sha256:digest(canonicalJSON(wire)),submitted_input_sha256:digest(canonicalJSON(wire)),response_transport:{api_schema_sha256:transport.api_schema_sha256,semantic_schema_sha256:digest(canonicalJSON(schema))}};
  };
 }
 f=await fixture(t,args);const execution=await f.execute(await f.claim('scoped-'+shared));await execution.job;
 assert.equal(check.calls.length,2);assert.equal(f.created.length,1);assert.equal(f.prompts.length,invalid?3:2);
 assert.match(f.prompts[1].text,addressing?/Host owns/:/physical-line amendments/);assert.ok(!f.prompts[1].text.includes('keep\ninitiate\ntail'));
 if(addressing){assert.match(f.prompts[1].text,/initiate/);assert(!f.prompts[1].text.includes('start_line'));assert(!f.prompts[1].text.includes('end_line'));}
 const record=await f.runtime.runs.read(f.run.run_id),attempt=record.state.nodes.pages.attempts[0];
 assert.equal(attempt.main_item_results[0].result.conclusion,'keep\nstart\ntail');assert.equal(attempt.main_item_turns[0],invalid?3:2);
 const files=await import('node:fs/promises').then(fs=>fs.readdir(f.runtime.runs.directory(f.run.run_id)));
 const artifacts=await Promise.all(files.filter(name=>name.startsWith('executor-')).map(name=>readFile(join(f.runtime.runs.directory(f.run.run_id),name),'utf8').then(JSON.parse)));
 const amendment=artifacts.find(artifact=>artifact.kind==='host_main_text_amendment');
 assert.ok(amendment);assert.deepEqual(amendment.payload,edit);assert.equal(amendment.baseline_check.attempt_id,attempt.id);
 assert.equal(amendment.merged_output_sha256,digest(canonicalJSON({conclusion:'keep\nstart\ntail'})));
});
