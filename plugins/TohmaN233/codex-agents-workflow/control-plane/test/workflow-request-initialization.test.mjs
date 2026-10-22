import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,mkdir,rm,writeFile,readFile} from 'node:fs/promises';
import {join} from 'node:path';
import {randomUUID} from 'node:crypto';
import {tmpdir} from './physical-tempdir.mjs';
import {readyWorkflow,edge} from './fixtures/workflow-fixtures.mjs';
import {WorkflowService,withWorkflowExecutionRequest} from '../lib/workflow-service.mjs';
import {DEFAULT_CONFIG_PATH,handleRpc} from '../server.mjs';
import {digest} from '../lib/workflow-revisions.mjs';
import {loadConfig,saveConfig,resolveAuditPath} from '../lib/config.mjs';
import {hostToolBindingIssues} from '../lib/execution/host-tool-runner.mjs';
import {withForegroundOperationObservation} from '../lib/foreground-operation-observation.mjs';

const schema={type:'object',properties:{value:{type:'string'}},required:['value'],additionalProperties:false};
async function fixture(t,{checker,wait,defaultEnvironment=false,extraBrokers={},capabilityContext,brokerTransform}={}){
 const root=await mkdtemp(join(tmpdir(),'request-init-')),workspace=join(root,'workspace');await mkdir(workspace);
 const configPath=join(root,'control-plane.json'),thread=randomUUID(),checks=[];let launches=0;
 const tool={id:'neutral-check',identity:{name:'neutral-check',version:'1',sha256:digest('neutral-check')},argv:['check'],
  input_schema:{type:'object',properties:{inputs:{},output:schema},required:['inputs','output'],additionalProperties:false},
  output_schema:{type:'object',properties:{verified:{type:'boolean'}},required:['verified'],additionalProperties:false},env_allow:[],
  permissions:{network:false,read_paths:['.'],write_paths:[]},output_cap_bytes:1024,deadline_ms:1000,idempotency:{mode:'safe'}};
 const broker={identity:tool.identity,attestation:{qualified:true,cancellable:true,effect_observation:true,tool_identity:tool.identity,broker_id:tool.id,evidence_sha256:digest('qualified')},
  execute:async request=>{checks.push(request.input);return checker?checker(request):{exit_code:0,output:{verified:true},effects:{observed:true,changed_paths:[],outside_paths:[],artifacts:[]}};},
  cancel:async()=>({termination_confirmed:true,effects:{observed:true,changed_paths:[],outside_paths:[],artifacts:[]}})};
 brokerTransform?.(broker);
 const capabilities={hostToolRegistry:{[tool.id]:broker,...extraBrokers},...(capabilityContext===undefined?{}:{context:capabilityContext}),nativeAgentObserver:null,
  launchDetachedHostMain:async args=>{launches++;return {run_id:args.runId,status:'starting'};},
  waitForOwnedWorkflow:async(service,started)=>{
   if(wait)await wait(service,started);
   // Actual public service transition, with all original Run/receipt checks.
   await service.call('native_next',{run_id:started.run_id,control_token:started.control_token});
   return {...started,status:'running',wake_reason:'native_handoff_required',next_action:'workflow_native_next'};
  }};
 const service=new WorkflowService({configPath,defaultConfigPath:DEFAULT_CONFIG_PATH,...(defaultEnvironment?{}:{env:{}}),capabilities});
 await service.call('migrate_v6',{}, {human:true});
 const workflow=readyWorkflow('neutral-request');workflow.skill_policy.mode='cooperative';workflow.host_tools=[tool];
 const final=workflow.nodes.find(node=>node.id==='final');final.executor={kind:'main',mode:'orchestration'};final.outputs_schema=schema;
 const first={...structuredClone(final),id:'initial',input_bindings:{task:'/inputs/task'},resources:[],access:'bounded_write',path_scope:['.'],
  completion_contract:{on_missing:'block',outcome:'decision',host_check:{tool:tool.id,success_field:'verified'}}};
 workflow.nodes.splice(1,0,first);workflow.edges=[edge('start','initial'),edge('initial','final'),edge('final','end')];
 await service.call('create',{workflow});
 const startArgs={workflow_id:workflow.id,workspace,access:'bounded_write',allowed_paths:['.'],inputs:{task:'Neutral fixture'}};
 const rpc=(name,args,signal)=>handleRpc({jsonrpc:'2.0',id:1,method:'tools/call',params:{name,_meta:{threadId:thread},arguments:args}},
  {configPath,defaultConfigPath:DEFAULT_CONFIG_PATH,...(defaultEnvironment?{}:{env:{}}),serviceCapabilities:capabilities,signal});
 const prepared=await rpc('workflow_startup_contract',{...startArgs,initial_output:{value:'accepted'}});
 assert.notEqual(prepared.result.isError,true,JSON.stringify(prepared));
 const submission={startup_reference:JSON.parse(prepared.result.content[0].text).startup_reference};
 t.after(async()=>{await Promise.allSettled([...service.attemptAdmission.drainJobs.values()]);await service.historyMaintenance.settle();await service.historyMaintenance.close();
  assert(root.startsWith(tmpdir()));await rm(root,{recursive:true,maxRetries:3,retryDelay:100});});
 return {service,configPath,checks,rpc,submission,thread,workflow,startArgs,launches:()=>launches};
}

async function countOpen(action){
 const original=WorkflowService.prototype.open,opens=[];
 WorkflowService.prototype.open=async function(...args){opens.push(this);return original.apply(this,args);};
 try{return {value:await action(),opens};}finally{WorkflowService.prototype.open=original;}
}
const decode=response=>{assert.notEqual(response.result.isError,true,JSON.stringify(response));return JSON.parse(response.result.content[0].text);};

test('actual public typed prepared startup initializes once through original checker and final recursive handoff',async t=>{
 const f=await fixture(t),measured=await countOpen(()=>f.rpc('workflow_start_prepared',f.submission));
 assert.equal(decode(measured.value).status,'orchestration_handoff');assert.equal(f.checks.length,1);assert.equal(f.launches(),1);
 const [run]=await f.service.call('runs'),state=await f.service.call('get',{run_id:run.run_id});
 assert.equal(state.nodes.initial.status,'succeeded');assert.equal(state.nodes.final.status,'running');
 assert.equal(measured.opens.length,1,'one exact request must initialize once across all service transitions');
 const audits=(await readFile(resolveAuditPath(f.configPath),'utf8')).trim().split('\n').map(JSON.parse);
 const report=audits.filter(row=>row.event==='workflow-foreground-operation').at(-1);
 assert(report);
 const detail=JSON.parse(report.detail);assert.equal(detail.f.op[0],1);assert.equal(detail.f.pm[0],1);assert.equal(detail.f.hm[0],1);
 assert.equal(detail.f.rp[0],1);assert.equal(detail.f.ir[0],5);
});

test('actual default process.env public typed prepared startup preserves ordinary Host capability shape',async t=>{
 const f=await fixture(t,{defaultEnvironment:true});
 assert.equal(f.service.env,process.env);
 // R1 gave INVALID_JSON here before any Run; the caller packet is unchanged.
 const measured=await countOpen(()=>f.rpc('workflow_start_prepared',f.submission));
 assert.equal(decode(measured.value).status,'orchestration_handoff');
 assert.equal(measured.opens.length,1);assert.equal(measured.opens[0].env,process.env);
 assert.equal(f.checks.length,1);assert.equal(f.launches(),1);
});

test('unselected ordinary broker entries may omit optional identity and attestation',async t=>{
 for(const extraBrokers of [
  {'unselected-broker':{execute:async()=>assert.fail('unselected broker cannot execute')}},
  {'unselected-broker':{identity:{name:'neutral-unselected',version:'1',sha256:digest('unselected')},execute:async()=>assert.fail('unselected broker cannot execute')}},
 ]){
  const f=await fixture(t,{extraBrokers});
  // The original direct opening admits this unselected registry shape.
  const direct=await f.service.open();assert(direct.context.host_tools.includes('unselected-broker'));
  const measured=await countOpen(()=>f.rpc('workflow_start_prepared',f.submission));
  assert.equal(decode(measured.value).status,'orchestration_handoff');assert.equal(measured.opens.length,1);
  assert.equal(f.checks.length,1);
 }
});

test('runtime capability shapes admitted by original contracts retain their public prepared startup behavior',async t=>{
 class Context{constructor(){this.host_tools=[];this.optional=undefined;}}
 const variants=[
  {extraBrokers:{'unselected-broker':null}},
  {brokerTransform:broker=>{broker.attestation.optional=undefined;}},
  {capabilityContext:new Context()},
  {capabilityContext:{optional:undefined}},
 ];
 for(const options of variants){
  const f=await fixture(t,options);assert.deepEqual(hostToolBindingIssues(f.workflow,f.service.capabilities.hostToolRegistry),[]);
  await f.service.open();
  const measured=await countOpen(()=>f.rpc('workflow_start_prepared',f.submission));
  assert.equal(decode(measured.value).status,'orchestration_handoff');assert.equal(measured.opens.length,1);assert.equal(f.checks.length,1);
 }
});

test('runtime comparison preserves omission, in-place data and callable or opaque identity changes',async t=>{
 const context={optional:undefined,policy:{enabled:true},callback:()=>1};context.self=context;
 const f=await fixture(t,{capabilityContext:context}),read=()=>f.service.call('read',{workflow_id:'neutral-request'});
 const measured=await countOpen(()=>withWorkflowExecutionRequest(async()=>{
  await read();await read();
  delete context.optional;await read();
  context.policy.enabled=false;await read();
  context.callback=()=>1;await read();
  context.symbol=Symbol('neutral');await read();
  context.symbol=Symbol('neutral');await read();
  context.opaque=new Date(0);await read();
  context.opaque=new Date(0);await read();
  context.rows=[,1];await read();context.rows[0]=undefined;await read();
 }));
 assert.equal(measured.opens.length,10);
});

test('runtime comparison budget exhaustion preserves original acceptance through fresh opening',async t=>{
 const context={};let tail=context;
 for(let index=0;index<140;index++){tail.next={};tail=tail.next;}
 for(const capabilityContext of [context,{unused:'x'.repeat(8*1024*1024+1)}]){
  const f=await fixture(t,{capabilityContext});await f.service.open();
  const reports=[];
  const measured=await countOpen(()=>withForegroundOperationObservation(()=>withWorkflowExecutionRequest(async()=>{
   for(let index=0;index<2;index++)assert.equal((await f.service.call('read',{workflow_id:'neutral-request'})).workflow.id,'neutral-request');
  }),report=>reports.push(report)));
  assert.equal(measured.opens.length,2);assert.equal(reports[0].f.ib[0],2);
 }
});

test('irrelevant nested accessors and opaque proxy brokers are never invoked merely for comparison',async t=>{
 let accessed=0;
 const metadata=Object.defineProperty({},'irrelevant',{enumerable:true,get(){accessed++;throw new Error('irrelevant accessor must not execute');}});
 const broker=Object.defineProperty({},'identity',{enumerable:true,get(){accessed++;throw new Error('unselected broker accessor must not execute');}});
 const proxy=new Proxy({}, {get(){accessed++;throw new Error('unselected proxy must not execute');}});
 for(const options of [{capabilityContext:{metadata}},{extraBrokers:{'unselected-broker':broker}},{extraBrokers:{'unselected-broker':proxy}}]){
  const f=await fixture(t,options);await f.service.open();const reports=[];
  const measured=await countOpen(()=>withForegroundOperationObservation(()=>withWorkflowExecutionRequest(async()=>{
   await f.service.call('read',{workflow_id:'neutral-request'});await f.service.call('read',{workflow_id:'neutral-request'});
  }),report=>reports.push(report)));
  assert.equal(measured.opens.length,2);assert.equal(reports[0].f.ia[0],2);assert.equal(accessed,0);
 }
});

test('post-construction registry accessors and container proxies retain original fresh reads without fingerprint callbacks',async t=>{
 for(const mode of ['throwing-entry','counted-entry','proxy-container']){
  const f=await fixture(t);let accessed=0;const registry=f.service.capabilities.hostToolRegistry;
  if(mode==='proxy-container'){
   registry['unselected-broker']={};
   f.service.capabilities.hostToolRegistry=new Proxy(registry,{get(target,key,receiver){
    if(key==='unselected-broker'){accessed++;throw new Error('unused container value must not be read');}
    return Reflect.get(target,key,receiver);
   }});
  }else Object.defineProperty(registry,'unselected-broker',{enumerable:true,get(){
   accessed++;if(mode==='throwing-entry')throw new Error('unused entry must not be read');return {};
  }});
  assert.deepEqual(hostToolBindingIssues(f.workflow,f.service.capabilities.hostToolRegistry),[]);
  await f.service.call('read',{workflow_id:f.workflow.id});assert.equal(accessed,0);
  const reports=[];
  const measured=await countOpen(()=>withForegroundOperationObservation(()=>withWorkflowExecutionRequest(async()=>{
   await f.service.call('read',{workflow_id:f.workflow.id});await f.service.call('read',{workflow_id:f.workflow.id});
  }),report=>reports.push(report)));
  assert.equal(accessed,0);assert.equal(measured.opens.length,2);assert.equal(reports[0].f.ia[0],2);
 }
});

test('post-construction outer capability getters retain precisely original getter invocation counts and errors',async t=>{
 for(const mode of ['context','hostToolRegistry','proxy-capabilities']){
  const f=await fixture(t);let accessed=0;
  if(mode==='proxy-capabilities')f.service.capabilities=new Proxy(f.service.capabilities,{get(target,key,receiver){accessed++;return Reflect.get(target,key,receiver);}});
  else{
   const value=mode==='context'?{}:f.service.capabilities.hostToolRegistry;
   Object.defineProperty(f.service.capabilities,mode,{get(){accessed++;return value;}});
  }
  await f.service.call('read',{workflow_id:f.workflow.id});const perRead=accessed;assert(perRead>0);
  const reports=[];accessed=0;
  const measured=await countOpen(()=>withForegroundOperationObservation(()=>withWorkflowExecutionRequest(async()=>{
   await f.service.call('read',{workflow_id:f.workflow.id});await f.service.call('read',{workflow_id:f.workflow.id});
  }),report=>reports.push(report)));
  assert.equal(accessed,2*perRead);assert.equal(measured.opens.length,2);assert.equal(reports[0].f.ia[0],2);
 }
 const f=await fixture(t),fault=new Error('original capability getter failure');let accessed=0;
 Object.defineProperty(f.service.capabilities,'host_tools',{configurable:true,get(){accessed++;throw fault;}});
 await assert.rejects(f.service.open(),error=>error===fault);const originalCount=accessed;accessed=0;
 await withWorkflowExecutionRequest(()=>assert.rejects(f.service.call('read',{workflow_id:f.workflow.id}),error=>error===fault));
 assert.equal(accessed,originalCount);
});

test('invalid selected broker retains original precise binding failures rather than fingerprint failures',async t=>{
 for(const mutate of [broker=>{delete broker.identity;},broker=>{delete broker.attestation;},broker=>{broker.attestation.qualified=false;}]){
  const f=await fixture(t);
  const broker=f.service.capabilities.hostToolRegistry['neutral-check'];mutate(broker);
  const issues=hostToolBindingIssues(f.workflow,f.service.capabilities.hostToolRegistry);
  assert.equal(issues.length,1);
  const capture=async action=>{let failure;await assert.rejects(action(),error=>{failure=error;return true;});return failure;};
  const launch=()=>f.service.call('run_main',{...f.startArgs,native_parent_thread_id:f.thread});
  const original=await capture(launch),cached=await capture(()=>withWorkflowExecutionRequest(launch));
  assert.equal(cached.code,original.code);assert.deepEqual(cached.details,original.details);
  assert(['HOST_TOOL_BINDING_STALE','WORKFLOW_LAUNCH_BLOCKED'].includes(cached.code));
  assert.equal(f.launches(),0);assert.equal(f.checks.length,0);
 }
});

test('every later request and concurrent authenticated request initializes independently',async t=>{
 const left=await fixture(t),right=await fixture(t);
 const first=await countOpen(()=>Promise.all([left.rpc('workflow_start_prepared',left.submission),right.rpc('workflow_start_prepared',right.submission)]));
 first.value.forEach(value=>assert.equal(decode(value).status,'orchestration_handoff'));
 assert.equal(first.opens.length,2);assert.notEqual(first.opens[0],first.opens[1]);
 const retry=await countOpen(()=>left.rpc('workflow_start_prepared',left.submission));
 assert.equal(decode(retry.value).status,'orchestration_handoff');assert.equal(retry.opens.length,1);
 assert.equal(left.launches(),1);assert.equal(left.checks.length,1);
});

test('configuration revocation during startup reopens and rejects before checker or successor release',async t=>{
 const f=await fixture(t,{wait:async service=>{
  const config=await loadConfig({configPath:service.configPath,defaultConfigPath:DEFAULT_CONFIG_PATH});
  config.global.enabled=false;await saveConfig(config,{configPath:service.configPath});
 }});
 const result=await countOpen(()=>f.rpc('workflow_start_prepared',f.submission));
 assert.equal(result.value.result.isError,true);assert.match(result.value.result.content[0].text,/CONTROL_DISABLED/);
 assert.equal(result.opens.length,2);assert.equal(f.checks.length,0);
 const [run]=await f.service.call('runs'),state=await f.service.call('get',{run_id:run.run_id});
 assert.notEqual(state.nodes.initial.status,'succeeded');assert.equal(state.nodes.final.status,'pending');
});

test('fresh configuration, environment and Host capability changes invalidate only their service entry',async t=>{
 const f=await fixture(t),other=new WorkflowService({configPath:f.configPath,defaultConfigPath:DEFAULT_CONFIG_PATH,env:{},capabilities:f.service.capabilities});
 const read=service=>service.call('read',{workflow_id:'neutral-request'});
 const measured=await countOpen(()=>withWorkflowExecutionRequest(async()=>{
  await Promise.all([read(f.service),read(f.service)]);
  await read(other);
  const config=await loadConfig({configPath:f.configPath,defaultConfigPath:DEFAULT_CONFIG_PATH});
  config.providers[0].enabled=!config.providers[0].enabled;await saveConfig(config,{configPath:f.configPath});await read(f.service);
  f.service.env.NEUTRAL_VISIBLE='1';await read(f.service);
  f.service.capabilities.host_tools=['neutral-capability'];await read(f.service);
 }));
 assert.equal(measured.opens.length,5);assert.equal(measured.opens.filter(value=>value===other).length,1);
});

test('failed initialization is visible and never retained after repaired config',async t=>{
 const f=await fixture(t),bytes=await readFile(f.configPath);
 const measured=await countOpen(()=>withWorkflowExecutionRequest(async()=>{
  await f.service.call('read',{workflow_id:'neutral-request'});
  await writeFile(f.configPath,'{');
  await assert.rejects(f.service.call('read',{workflow_id:'neutral-request'}),/invalid JSON/);
  await writeFile(f.configPath,bytes);
  await f.service.call('read',{workflow_id:'neutral-request'});
 }));
 assert.equal(measured.opens.length,2);
 const original=f.service.open.bind(f.service),fault=new Error('neutral open failure');let fail=true;
 f.service.open=async(...args)=>{if(fail){fail=false;throw fault;}return original(...args);};
 await withWorkflowExecutionRequest(async()=>{
  await assert.rejects(f.service.call('read',{workflow_id:'neutral-request'}),error=>error===fault);
  assert.equal((await f.service.call('read',{workflow_id:'neutral-request'})).workflow.id,'neutral-request');
 });
});

test('public direct opens and Role routes retain full independent validation inside request scope',async t=>{
 const f=await fixture(t);
 const measured=await countOpen(()=>withWorkflowExecutionRequest(async()=>{
  await f.service.call('read',{workflow_id:'neutral-request'});
  await f.service.open();await f.service.open();
  await f.service.call('role_templates');await f.service.call('role_templates');
  await f.service.call('read',{workflow_id:'neutral-request'});
 }));
 assert.equal(measured.opens.length,5);
 const outside=await countOpen(async()=>{await f.service.call('read',{workflow_id:'neutral-request'});await f.service.call('read',{workflow_id:'neutral-request'});});
 assert.equal(outside.opens.length,2);
});

test('async work inherited after original request settlement cannot retain its initialization',async t=>{
 const f=await fixture(t);let release,late;
 const gate=new Promise(resolve=>{release=resolve;});
 const measured=await countOpen(async()=>{
  await withWorkflowExecutionRequest(async()=>{
   await f.service.call('read',{workflow_id:'neutral-request'});
   late=(async()=>{await gate;await f.service.call('read',{workflow_id:'neutral-request'});await f.service.call('read',{workflow_id:'neutral-request'});})();
  });
  release();await late;
 });
 assert.equal(measured.opens.length,3);
});

test('changed initialization basis fails visibly and a later same-request call initializes cleanly',async t=>{
 const f=await fixture(t),original=f.service.open.bind(f.service);let change=true;
 f.service.open=async(...args)=>{const value=await original(...args);if(change){change=false;f.service.env.NEUTRAL_CHANGE='1';}return value;};
 await withWorkflowExecutionRequest(async()=>{
  await assert.rejects(f.service.call('read',{workflow_id:'neutral-request'}),{code:'WORKFLOW_REQUEST_INITIALIZATION_CHANGED'});
  assert.equal((await f.service.call('read',{workflow_id:'neutral-request'})).workflow.id,'neutral-request');
 });
});

test('request settlement during a pending configuration read cannot publish a retained initialization',async t=>{
 const f=await fixture(t),original=f.service.config.bind(f.service);let release,entered,late,block=true;
 const ready=new Promise(resolve=>{entered=resolve;}),gate=new Promise(resolve=>{release=resolve;});
 f.service.config=async()=>{if(block){block=false;entered();await gate;}return original();};
 const measured=await countOpen(async()=>{
  await withWorkflowExecutionRequest(async()=>{
   late=(async()=>{await f.service.call('read',{workflow_id:'neutral-request'});await f.service.call('read',{workflow_id:'neutral-request'});})();
   await ready;
  });
  release();await late;
 });
 assert.equal(measured.opens.length,2);
});

test('revoked controller and cancelled startup retain original failures and cannot release final node',async t=>{
 const fault=new Error('neutral request cancelled'),controller=new AbortController();
 const cancelled=await fixture(t,{wait:async()=>{controller.abort(fault);}});
 const response=await cancelled.rpc('workflow_start_prepared',cancelled.submission,controller.signal);
 assert.equal(response.result.isError,true);assert.match(response.result.content[0].text,/neutral request cancelled/);
 assert.equal(cancelled.checks.length,0);
 const f=await fixture(t);decode(await f.rpc('workflow_start_prepared',f.submission));
 const [run]=await f.service.call('runs');
 await withWorkflowExecutionRequest(async()=>{
  await f.service.call('read',{workflow_id:'neutral-request'});
  await assert.rejects(f.service.call('native_next',{run_id:run.run_id,control_token:'revoked'}),{code:'RUN_AUTHORITY'});
 });
 assert.equal((await f.service.call('get',{run_id:run.run_id})).nodes.final.attempts[0].completion_turns??0,0);
});

test('original rejected checker and scope audit still block folded semantic completion',async t=>{
 for(const invalid of ['checker','scope']){
  const f=await fixture(t,{checker:async()=>({exit_code:0,output:{verified:invalid!=='checker'},
   effects:{observed:true,changed_paths:[],outside_paths:invalid==='scope'?['outside-fixture']:[],artifacts:[]}})});
  const response=await f.rpc('workflow_start_prepared',f.submission);
  assert(response.result.isError||decode(response).status!=='orchestration_handoff');
  const [run]=await f.service.call('runs'),state=await f.service.call('get',{run_id:run.run_id});
  assert.notEqual(state.nodes.initial.status,'succeeded');assert.equal(state.nodes.final.status,'pending');assert.equal(f.checks.length,1);
 }
});
