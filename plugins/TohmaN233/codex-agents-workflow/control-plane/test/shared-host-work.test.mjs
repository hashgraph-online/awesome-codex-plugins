import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,mkdir,writeFile,readFile,rm} from 'node:fs/promises';
import {join} from 'node:path';
import {tmpdir} from './physical-tempdir.mjs';
import {readyWorkflow,agent,edge} from './fixtures/workflow-fixtures.mjs';
import {WorkflowStore} from '../lib/workflow-store.mjs';
import {WorkflowRuntime} from '../lib/workflow-runtime.mjs';
import {WorkflowExecutor} from '../lib/workflow-executor.mjs';
import {WorkflowDrive} from '../lib/workflow-drive.mjs';
import {digest} from '../lib/workflow-revisions.mjs';
import {HostToolRunner,hostToolContracts} from '../lib/execution/host-tool-runner.mjs';
import {prepareMainOrchestration,completeMainOrchestration} from '../lib/execution/main-orchestration.mjs';
import {RunExecutionCoordinator} from '../lib/execution/run-execution-coordinator.mjs';
import {planParallelBranches} from '../lib/parallel/branch-planner.mjs';
import {ParallelWorktreeManager} from '../lib/parallel/worktree-manager.mjs';
import {validateWorkflowGraph} from '../lib/workflow-validator.mjs';
import {prepareSharedHostProjection,joinSharedHostWork,startSharedHostWork,sharedHostRegion,validateSharedHostPolicy,hasSharedHostWorkOwner,releaseSettledSharedHostOwners} from '../lib/execution/shared-host-work.mjs';
import {WorkflowService} from '../lib/workflow-service.mjs';
import {HostMainManager} from '../lib/execution/host-main-manager.mjs';
import {retainOwnedAuthority} from '../lib/execution/owned-workflow-authority.mjs';
import {DEFAULT_CONFIG_PATH} from '../server.mjs';

const thread='12345678-1234-4234-8234-123456789abc';
const reviewSchema={type:'object',required:['accepted','assessment'],additionalProperties:false,properties:{accepted:{type:'boolean'},assessment:{type:'string',maxLength:600}}};
const toolSchema={type:'object',required:['file'],additionalProperties:false,properties:{file:{type:'string'}}};
function definition({sequential=false}={}){
  const workflow=readyWorkflow('shared-host-work');workflow.skill_policy.mode='cooperative';
  workflow.inputs_schema={type:'object',required:['product_source'],additionalProperties:false,properties:{product_source:{type:'object',required:['path','format'],additionalProperties:false,properties:{path:{type:'string'},format:{type:'string'},text:{type:'string'}}}}};
  const contract={id:'export',identity:{name:'original-export-fixture',version:'1',sha256:digest('original-export')},argv:['original-export'],
    input_schema:{type:'object',additionalProperties:false},output_schema:toolSchema,env_allow:[],permissions:{network:false,read_paths:['source.html'],write_paths:['source.html','output.mp4']},
    output_cap_bytes:1024,deadline_ms:5000,idempotency:{mode:'non_idempotent'}};
  workflow.host_tools=[contract];
  const tool={...agent('z_export'),type:'tool',executor:{kind:'tool',tool:contract.id},access:'bounded_write',path_scope:['source.html','output.mp4'],outputs_schema:toolSchema};
  const review={...agent('a_review'),executor:{kind:'main',mode:'orchestration'},outputs_schema:reviewSchema,input_bindings:{product_source:'/inputs/product_source'},prompt_template:'Review the supplied source.'};
  const final={...agent('final'),executor:{kind:'main',mode:'orchestration'},role:'finalizer',outputs_schema:reviewSchema};
  const region={id:'fork',type:'parallel',join_id:'join',failure_policy:'fail_fast',workspace_policy:{kind:'host_tool_overlap',tool_node_id:tool.id,main_node_id:review.id,read_inputs:['product_source']}};
  workflow.nodes=[{id:'start',type:'start'},...(sequential?[]:[region]),tool,...(sequential?[]:[review,{id:'join',type:'join',parallel_id:'fork'}]),final,{id:'end',type:'end'}];
  workflow.edges=sequential?[edge('start',tool.id),edge(tool.id,'final'),edge('final','end')]
    :[edge('start','fork'),edge('fork',review.id,'semantic'),edge('fork',tool.id,'tool'),edge(review.id,'join'),edge(tool.id,'join'),edge('join','final'),edge('final','end')];
  return {workflow,contract,region};
}
async function fixture(t,{failure=false,sequential=false,text}={}){
  const root=await mkdtemp(join(tmpdir(),'shared-host-work-')),workspace=join(root,'workspace');await mkdir(workspace);
  const source=join(workspace,'source.html');await writeFile(source,'Immutable source');
  const {workflow,contract,region}=definition({sequential}),context={host_tools:[contract.id]};
  const store=await new WorkflowStore(join(root,'packs'),{validationContext:context}).initialize();await store.create(workflow).catch(error=>{error.message+=' '+JSON.stringify(error.validation);throw error;});
  const runtime=await new WorkflowRuntime({workflowStore:store,runRoot:join(root,'runs'),context}).initialize();
  const run=await runtime.start({workflow_id:workflow.id,workspace,access:'bounded_write',allowed_paths:['source.html','output.mp4'],main_actor:'root',
    inputs:{product_source:{path:source,format:'html',...(text===undefined?{}:{text})}},constraints:{native_parent_thread_id:thread}});
  let release,startedResolve,finishedResolve;const pending=new Promise(resolve=>{release=resolve;}),started=new Promise(resolve=>{startedResolve=resolve;}),finished=new Promise(resolve=>{finishedResolve=resolve;});let calls=0,cancels=0,cancelled=false;
  const broker={identity:contract.identity,attestation:{qualified:true,cancellable:true,effect_observation:true,tool_identity:contract.identity,broker_id:'original-tool',evidence_sha256:digest('qualified')},
    async execute(){try{calls++;startedResolve();await writeFile(source,'Renderer source rewrite');await pending;
      if(!failure&&!cancelled)await writeFile(join(workspace,'output.mp4'),'Actual fixture MP4 bytes');
      return {exit_code:failure||cancelled?1:0,output:failure||cancelled?null:{file:join(workspace,'output.mp4')},diagnostic:failure?'Original exporter failed':'',
        effects:{observed:true,changed_paths:failure||cancelled?['source.html']:['source.html','output.mp4'],outside_paths:[],artifacts:[]}};}finally{finishedResolve();}},
    async cancel(){cancels++;cancelled=true;release();await finished;return {termination_confirmed:true,evidence:[{kind:'fixture_termination',sha256:digest('stopped')}],effects:{observed:true,changed_paths:['source.html'],outside_paths:[],artifacts:[]}};}};
  const executor=new WorkflowExecutor({runtime,env:{},hostToolRunner:new HostToolRunner({registry:{[contract.id]:broker}}),getConfig:async()=>({global:{enabled:true,max_prompt_chars:64000},providers:[]})});
  runtime.executionAdmission=executor.attemptAdmission;
  const manager=()=>({entries:new Map(),fenceRun(){},fenceAttempt(){},async stopRun(){},async stopAttempt(){}});
  const coordinator=new RunExecutionCoordinator({admission:executor.attemptAdmission,strictManager:manager(),managedNativeManager:manager(),hostMainManager:manager(),registry:{}});coordinator.bind(runtime);
  runtime.failAttemptAfterQuiescence=(...args)=>coordinator.failAttemptAfterQuiescence(...args);
  runtime.fenceRunExecution=(...args)=>coordinator.fenceRun(...args);runtime.scheduleRunDrain=(...args)=>coordinator.scheduleDrain(...args);
  const drive=new WorkflowDrive({runtime,executor}),args={control_token:run.control_token,owner:'root'};
  const current={run_id:run.run_id,control_token:run.control_token,thread_id:thread};
  t.after(async()=>{release();await Promise.all(runtime.executionAdmission.pending(run.run_id).map(entry=>entry.done));await Promise.all(runtime.executionAdmission.drainJobs.values());await rm(root,{recursive:true,maxRetries:3,retryDelay:100});});
  return {root,workspace,source,workflow,region,runtime,executor,drive,run,args,current,release,started,calls:()=>calls,cancels:()=>cancels};
}

test('actual pending Host tool overlaps initiating Main, whose independent whole projection audit commits, then join waits for success',async t=>{
  const f=await fixture(t),handoff=await f.drive.advanceToMain(f.run.run_id,f.args);await f.started;
  assert.equal(handoff.node_id,'a_review');assert.equal(handoff.stop_reason,'main_orchestration');assert.equal(f.calls(),1);
  let state=await f.runtime.get(f.run.run_id);assert(['claimed','running'].includes(state.nodes.z_export.status));assert.equal(state.nodes.join.status,'pending');
  const main=await prepareMainOrchestration(f.runtime,f.current);assert.notEqual(main.workspace,f.workspace);assert.equal(main.context,'current_conversation');
  const record=await f.runtime.runs.read(f.run.run_id),projection=record.state.nodes.z_export.attempts[0].shared_host_projection;
  assert.equal(await readFile(projection.sources[0].path,'utf8'),'Immutable source');assert.equal(await readFile(f.source,'utf8'),'Renderer source rewrite');
  assert.equal(projection.sources[0].sha256,digest('Immutable source'));
  assert(main.task_bundle.task.includes(projection.sources[0].path.replaceAll('\\','\\\\')));assert(!main.task_bundle.task.includes(f.source.replaceAll('\\','\\\\')));
  await completeMainOrchestration(f.runtime,{...f.current,output:{accepted:true,assessment:'Source accepted'}},{executor:f.executor});
  state=await f.runtime.get(f.run.run_id);assert.equal(state.nodes.a_review.status,'succeeded');assert.deepEqual(state.nodes.a_review.attempts[0].completion.changed_paths,[]);
  let resolved=false;const join=f.drive.advanceToMain(f.run.run_id,f.args).then(value=>{resolved=true;return value;});
  await new Promise(resolve=>setImmediate(resolve));assert.equal(resolved,false);assert.equal((await f.runtime.get(f.run.run_id)).nodes.final.attempts.length,0);
  f.release();const final=await join;assert.equal(final.node_id,'final');assert.equal(f.calls(),1);assert.equal((await f.runtime.get(f.run.run_id)).nodes.join.status,'succeeded');
  await prepareMainOrchestration(f.runtime,f.current);await completeMainOrchestration(f.runtime,{...f.current,output:{accepted:true,assessment:'Final artifact accepted'}},{executor:f.executor});
  assert.equal((await f.runtime.get(f.run.run_id)).status,'succeeded');
});

test('projection edits fail read-only Main instead of being hidden as exporter effects',async t=>{
  const f=await fixture(t);await f.drive.advanceToMain(f.run.run_id,f.args);await f.started;const main=await prepareMainOrchestration(f.runtime,f.current);
  await writeFile(join(main.workspace,'unexpected.txt'),'Main unauthorized write');
  await assert.rejects(completeMainOrchestration(f.runtime,{...f.current,output:{accepted:true,assessment:'Rejected edit'}},{executor:f.executor}),{code:'MAIN_ORCHESTRATION_SCOPE_VIOLATION'});
  assert.equal((await f.runtime.get(f.run.run_id)).status,'failed');await f.runtime.executionAdmission.wait(f.run.run_id);assert.equal(f.cancels(),1);
});

test('fresh request Runtime and Drive retain one pending owner, current Main identity and durable join',async t=>{
  const f=await fixture(t);await f.drive.advanceToMain(f.run.run_id,f.args);await f.started;
  const reopened=await new WorkflowRuntime({workflowStore:f.runtime.workflows,runRoot:f.runtime.runs.root,context:{host_tools:['export']}}).initialize();
  reopened.executionAdmission=f.runtime.executionAdmission;
  const drive=new WorkflowDrive({runtime:reopened,executor:f.executor}),again=await drive.advanceToMain(f.run.run_id,f.args);
  assert.equal(again.node_id,'a_review');assert.equal(f.calls(),1);const main=await prepareMainOrchestration(reopened,f.current);assert.equal(main.context,'current_conversation');
  await completeMainOrchestration(reopened,{...f.current,output:{accepted:true,assessment:'Same source accepted'}},{executor:f.executor});
  const joined=drive.advanceToMain(f.run.run_id,f.args);f.release();assert.equal((await joined).node_id,'final');assert.equal(f.calls(),1);
  assert.equal((await reopened.get(f.run.run_id)).nodes.z_export.attempts.length,1);
});

test('fresh WorkflowService request reopens the real pending owner and current initiating Main, then joins after semantic completion',async t=>{
  const root=await mkdtemp(join(tmpdir(),'shared-host-service-')),workspace=join(root,'workspace');await mkdir(workspace);
  const source=join(workspace,'source.html');await writeFile(source,'Service source');
  const {workflow,contract}=definition();let calls=0,sessions=0,release,finish;const pending=new Promise(resolve=>{release=resolve;}),finished=new Promise(resolve=>{finish=resolve;});
  const broker={identity:contract.identity,attestation:{qualified:true,cancellable:true,effect_observation:true,tool_identity:contract.identity,broker_id:'service-original-tool',evidence_sha256:digest('service-qualified')},
    async execute(){try{calls++;await writeFile(source,'Service renderer source rewrite');await pending;await writeFile(join(workspace,'output.mp4'),'Service MP4');
      return {exit_code:0,output:{file:join(workspace,'output.mp4')},effects:{observed:true,changed_paths:['source.html','output.mp4'],outside_paths:[],artifacts:[]}};}finally{finish();}},
    async cancel(){release();await finished;return {termination_confirmed:true,evidence:[{kind:'settled_fixture',sha256:digest('settled')}],effects:{observed:true,changed_paths:['source.html'],outside_paths:[],artifacts:[]}};}};
  const configPath=join(root,'control-plane.json'),manager=new HostMainManager({configPath,getConfig:async()=>({}),qualify:async()=>{throw new Error('Current Main must not qualify a worker');},sessionFactory:async()=>{sessions++;throw new Error('Current Main must not create a worker');}});
  const capabilities={hostMainManager:manager,hostToolRegistry:{[contract.id]:broker},nativeAgentObserver:null,nativeParentVerifier:async()=>({agent_path:'/root'})};
  const service=new WorkflowService({configPath,defaultConfigPath:DEFAULT_CONFIG_PATH,env:{},capabilities});let reopened;
  t.after(async()=>{release();for(const item of [service,reopened].filter(Boolean)){await Promise.all(item.attemptAdmission.drainJobs.values());await item.historyMaintenance.settle();await item.historyMaintenance.close();}await manager.close();await rm(root,{recursive:true,maxRetries:3,retryDelay:100});});
  await service.call('migrate_v6',{}, {human:true});const pack=await service.call('create',{workflow,resources:{}});
  const handoff=await service.call('begin_main',{workflow_id:workflow.id,revision_hash:pack.revision_hash,workspace,access:'bounded_write',allowed_paths:['source.html','output.mp4'],
    inputs:{product_source:{path:source,format:'html'}},main_actor:'codex',native_parent_thread_id:thread});
  const {runtime}=await service.open(),{run_id,control_token}=handoff.host_binding;await retainOwnedAuthority(runtime,{run_id,control_token});
  assert.equal(calls,1,'The actual broker has started before current Main is handed off');
  const first=await service.call('native_next',{}, {model:true,modelThreadId:thread});
  reopened=new WorkflowService({configPath,defaultConfigPath:DEFAULT_CONFIG_PATH,env:{},capabilities});
  const again=await reopened.call('native_next',{}, {model:true,modelThreadId:thread});assert.deepEqual(again,first);assert.equal(again.context,'current_conversation');assert.notEqual(again.workspace,workspace);assert.equal(calls,1);assert.equal(sessions,0);
  let resolved=false;const complete=reopened.call('orchestration_complete',{output:{accepted:true,assessment:'Source accepted'}},{model:true,modelThreadId:thread}).then(value=>{resolved=true;return value;});
  await new Promise(resolve=>setImmediate(resolve));assert.equal(resolved,false);release();const final=await complete;assert.equal(final.status,'orchestration_handoff');
  assert.equal((await runtime.get(run_id)).nodes.join.status,'succeeded');assert.equal(calls,1);assert.equal(sessions,0);
});

test('export failure prevents deterministic join and final Main release',async t=>{
  const f=await fixture(t,{failure:true});await f.drive.advanceToMain(f.run.run_id,f.args);await f.started;
  await prepareMainOrchestration(f.runtime,f.current);await completeMainOrchestration(f.runtime,{...f.current,output:{accepted:true,assessment:'Source accepted'}},{executor:f.executor});
  const joined=f.drive.advanceToMain(f.run.run_id,f.args);f.release();const result=await joined;
  assert.equal(result.status,'failed');assert.equal(result.stop_reason,'terminal');const state=await f.runtime.get(f.run.run_id);assert.equal(state.nodes.final.attempts.length,0);assert.equal(state.nodes.z_export.error.code,'HOST_TOOL_FAILED');assert.equal(f.calls(),1);
});

test('cancellation drains the original pending broker and cannot restart it',async t=>{
  const f=await fixture(t);await f.drive.advanceToMain(f.run.run_id,f.args);await f.started;
  await f.runtime.cancel(f.run.run_id,{control_token:f.run.control_token},()=>coordinatorCancel());
  function coordinatorCancel(){f.runtime.executionAdmission.fenceRun(f.run.run_id);}
  await f.runtime.executionAdmission.wait(f.run.run_id);const result=await f.drive.advanceToMain(f.run.run_id,f.args);
  assert.equal(result.status,'cancelled');assert.equal(f.calls(),1);assert.equal(f.cancels(),1);assert.equal((await f.runtime.get(f.run.run_id)).nodes.final.attempts.length,0);
});

test('durable claimed overlap without a live owner is visible after restart and never replayed',async t=>{
  const f=await fixture(t),lease=await f.runtime.claimNode(f.run.run_id,{node_id:'z_export',request_id:'pre-crash',...f.args});
  const binding={...lease,control_token:f.run.control_token};await prepareSharedHostProjection(f.runtime,f.run.run_id,binding,f.region);
  await f.runtime.recordHostToolIntent(f.run.run_id,{...binding,contract:hostToolContracts(f.workflow).get('export'),input:{}});
  const restarted=await new WorkflowRuntime({workflowStore:f.runtime.workflows,runRoot:f.runtime.runs.root,context:{host_tools:['export']}}).initialize();
  const drive=new WorkflowDrive({runtime:restarted,executor:f.executor}),result=await drive.advanceToMain(f.run.run_id,f.args);
  assert.equal(result.stop_reason,'execution_recovery_required');assert.equal(result.error.code,'HOST_TOOL_RECONCILIATION_REQUIRED');assert.equal(f.calls(),0);assert.equal((await restarted.get(f.run.run_id)).nodes.z_export.attempts.length,1);
});

test('source text mismatch fails before exporter launch',async t=>{
  const f=await fixture(t,{text:'Wrong text'}),result=await f.drive.advanceToMain(f.run.run_id,f.args);
  assert.equal(result.stop_reason,'host_failure');assert.equal(result.error.code,'SHARED_HOST_SOURCE_TEXT');assert.equal(f.calls(),0);
  assert.equal((await f.runtime.get(f.run.run_id)).nodes.z_export.status,'failed');
});

test('Main semantic rejection without a Host check fails its attempt and cancels pending export',async t=>{
  const f=await fixture(t);await f.drive.advanceToMain(f.run.run_id,f.args);await f.started;await prepareMainOrchestration(f.runtime,f.current);
  await assert.rejects(completeMainOrchestration(f.runtime,{...f.current,output:{accepted:false,assessment:'Source rejected'}},{executor:f.executor}),{code:'NODE_SUCCESS_REQUIRED'});
  await f.runtime.executionAdmission.wait(f.run.run_id);const state=await f.runtime.get(f.run.run_id);
  assert.equal(state.status,'failed');assert.equal(state.nodes.a_review.error.code,'NODE_SUCCESS_REQUIRED');assert.equal(state.nodes.final.attempts.length,0);assert.equal(f.cancels(),1);
});

test('copied source corruption before the first handoff is rejected against its Host identity',async t=>{
  const f=await fixture(t);await f.drive.advanceToMain(f.run.run_id,f.args);await f.started;
  const record=await f.runtime.runs.read(f.run.run_id),projection=record.state.nodes.z_export.attempts[0].shared_host_projection;
  await writeFile(projection.sources[0].path,'Wrong immutable bytes');
  await assert.rejects(prepareMainOrchestration(f.runtime,f.current),{code:'SHARED_HOST_SOURCE_CORRUPT'});f.release();
});

test('sequential tool retains its blocking behavior and original workspace',async t=>{
  const f=await fixture(t,{sequential:true});let resolved=false;const advancing=f.drive.advanceToMain(f.run.run_id,f.args).then(value=>{resolved=true;return value;});await f.started;
  assert.equal(resolved,false);assert.equal((await f.runtime.get(f.run.run_id)).nodes.final.attempts.length,0);f.release();const handoff=await advancing;
  assert.equal(handoff.node_id,'final');const main=await prepareMainOrchestration(f.runtime,f.current);assert.equal(main.workspace,f.workspace);assert.equal(f.calls(),1);
});

test('policy admits only one qualified semantic/tool region without Git while ordinary parallel writes retain isolation',async()=>{
  const {workflow,region}=definition(),state={permissions:{access:'bounded_write',allowed_paths:['source.html','output.mp4']}};
  assert.equal(planParallelBranches(workflow,state).regions[0].isolated,false);
  const manager=new ParallelWorktreeManager(join(tmpdir(),'unused-shared-host-policy'));manager.git.initialize=()=>{throw new Error('Overlap must not initialize Git');};
  assert.equal(await manager.preflight(workflow,state.permissions,[{pack:{workflow},state}]),null);
  for(const change of [(value)=>value.nodes.find(node=>node.id==='fork').failure_policy='collect',value=>value.nodes.find(node=>node.id==='fork').workspace_policy.kind='ignore_writes',value=>value.nodes.find(node=>node.id==='fork').workspace_policy.read_inputs=[],value=>value.nodes.find(node=>node.id==='a_review').access='bounded_write']){
    const candidate=structuredClone(workflow);change(candidate);assert(validateWorkflowGraph(candidate,{host_tools:['export']}).errors.some(error=>error.code==='SHARED_HOST_POLICY'));
  }
  const ordinary=definition().workflow;delete ordinary.nodes.find(node=>node.id==='fork').workspace_policy;assert.equal(planParallelBranches(ordinary,state).regions[0].isolated,true);
});

test('shared join keeps exact failure and rejects duplicate start or missing owner',async()=>{
  const runtime={runs:{root:join(tmpdir(),'shared-owner-unit')}},binding={node_id:'tool',attempt_id:'exact-owner'};
  startSharedHostWork(runtime,'run',binding,async()=>{throw Object.assign(new Error('Owned failure'),{code:'OWNED_FAILURE'});});
  assert.throws(()=>startSharedHostWork(runtime,'run',binding,async()=>{}),{code:'SHARED_HOST_DUPLICATE'});
  await assert.rejects(joinSharedHostWork(runtime,'run',binding),{code:'OWNED_FAILURE'});
  await assert.rejects(joinSharedHostWork(runtime,'run',{...binding,attempt_id:'absent'}),{code:'HOST_TOOL_RECONCILIATION_REQUIRED'});
});


test('shared Host discovery preserves partial descriptors and rejects declared malformed graphs and policies',()=>{
 assert.equal(sharedHostRegion({name:'partial execution descriptor'},'review'),null);
 assert.equal(sharedHostRegion({nodes:[]},'review'),undefined);
 for(const nodes of [undefined,null,{},'not-an-array'])assert.throws(()=>sharedHostRegion({nodes},'review'),{code:'SHARED_HOST_POLICY'});
 const parallel={id:'overlap',type:'parallel',workspace_policy:{kind:'host_tool_overlap',tool_node_id:'export',main_node_id:'review'}};
 const workflow={nodes:[parallel],edges:[]};
 assert.equal(sharedHostRegion(workflow,'review'),parallel);
 assert.throws(()=>validateSharedHostPolicy(workflow,parallel),{code:'SHARED_HOST_POLICY'});
});

test('shared join preserves falsy rejections and retains their unresolved owners',async()=>{
 const runtime={runs:{root:join(tmpdir(),'shared-falsy-owner-unit')}};
 for(const [index,value] of [null,undefined,false,0,''].entries()){
  const binding={node_id:'tool',attempt_id:'falsy-owner-'+index};
  const entry=startSharedHostWork(runtime,'run',binding,async()=>{throw value;});
  let caught=false;
  try{await joinSharedHostWork(runtime,'run',binding);}catch(error){caught=true;assert.equal(error,value);}
  assert.equal(caught,true);assert.equal(entry.failed,true);assert.equal(entry.settled,true);
  releaseSettledSharedHostOwners(runtime,'run',{nodes:{tool:{attempts:[{id:binding.attempt_id,status:'failed'}]}}});
  assert.equal(hasSharedHostWorkOwner(runtime,'run',binding.attempt_id),true);
 }
 const binding={node_id:'tool',attempt_id:'successful-null'};
 startSharedHostWork(runtime,'run',binding,async()=>null);
 assert.equal(await joinSharedHostWork(runtime,'run',binding),null);
 releaseSettledSharedHostOwners(runtime,'run',{nodes:{tool:{attempts:[{id:binding.attempt_id,status:'succeeded'}]}}});
 assert.equal(hasSharedHostWorkOwner(runtime,'run',binding.attempt_id),false);
});
