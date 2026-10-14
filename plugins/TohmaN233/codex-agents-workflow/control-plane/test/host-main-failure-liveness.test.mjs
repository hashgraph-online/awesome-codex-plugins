import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,mkdir,rm,writeFile} from 'node:fs/promises';
import {join} from 'node:path';
import {tmpdir} from './physical-tempdir.mjs';
import {WorkflowService} from '../lib/workflow-service.mjs';
import {HostMainManager} from '../lib/execution/host-main-manager.mjs';
import {validateStrictConfig} from '../lib/execution/strict-config.mjs';
import {retainOwnedAuthority} from '../lib/execution/owned-workflow-authority.mjs';
import {readyWorkflow} from './fixtures/workflow-fixtures.mjs';
import {canonicalJSON,digest} from '../lib/workflow-revisions.mjs';
import {DEFAULT_CONFIG_PATH} from '../server.mjs';

const thread='00000000-0000-7000-8000-000000000001';
const model={model:true,modelThreadId:thread};
const original=()=>Object.assign(new Error('Neutral owned command RPC failed'),{code:'CODEX_RPC_ERROR'});
const cleanup=()=>Object.assign(new Error('Neutral helper retained pipes; Bearer secret-value'),{code:'CODEX_APP_SERVER_PIPE_HELD'});

async function fixture(t,{uncertain=true,journalFailure=false}={}){
 const root=await mkdtemp(join(tmpdir(),'main-failure-liveness-')),workspace=join(root,'workspace');await mkdir(workspace);
 let service,allowCleanup=false,starts=0,turns=0,advances=0,closes=0,quiesces=0,failCommits=0;
 const strict=validateStrictConfig({enabled:true,codex_binary:process.execPath,binary_sha256:'b'.repeat(64),
  authentication:{mode:'managed_chatgpt',api_key_env:''},main_model:'neutral-main',main_reasoning_effort:'high',inactivity_timeout_ms:0});
 const manager=new HostMainManager({configPath:join(root,'control-plane.json'),env:{},
  register:async({config})=>config,
  getConfig:async()=>({global:{enabled:true},strict_executor:strict,providers:[]}),qualify:async()=>strict,
  mainModelSelection:async()=>({model:'neutral-main',effort:'high'}),sessionFactory:async options=>{
   await options.resolveModelSelection({});starts++;
   const quiesce=options.toolBroker.quiesce.bind(options.toolBroker);
   options.toolBroker.quiesce=async()=>{quiesces++;return quiesce();};
   return {interrupt:async()=>{},close:async()=>{closes++;if(uncertain&&!allowCleanup)throw cleanup();},turn:async text=>{
    turns++;if(uncertain)throw new AggregateError([original(),cleanup()],'Neutral turn and cleanup failed');
    if(journalFailure)throw original();
    return {output:'{"value":"done"}',thread_id:'neutral-worker',turn_id:'neutral-turn',
     usage:{available:true,input_tokens:11,cached_input_tokens:0,cache_write_input_tokens:0,output_tokens:2,reasoning_output_tokens:0},
     audit:{input_sha256:digest(canonicalJSON([{type:'text',text}]))}};
   }};
  }});
 service=new WorkflowService({configPath:join(root,'control-plane.json'),defaultConfigPath:DEFAULT_CONFIG_PATH,env:{},
  capabilities:{hostMainManager:manager,nativeAgentObserver:null,nativeParentVerifier:async()=>({agent_path:'/root'})}});
 t.after(async()=>{allowCleanup=true;await manager.close();await service.historyMaintenance.settle();await service.historyMaintenance.close();await rm(root,{recursive:true,maxRetries:3,retryDelay:100});});
 await service.call('migrate_v6',{}, {human:true});
 const workflow=readyWorkflow('neutral-main-liveness');workflow.skill_policy.mode='cooperative';
 workflow.inputs_schema={type:'object',properties:{task:{type:'string'}},required:['task'],additionalProperties:false};
 const final=workflow.nodes.find(n=>n.id==='final');final.prompt_template='Return the neutral declared value.';
 final.outputs_schema={type:'object',properties:{value:{type:'string'}},required:['value'],additionalProperties:false};
 final.retry.max_attempts=1;
 const pack=await service.call('create',{workflow,resources:{}});
 const run=await service.call('start',{workflow_id:workflow.id,revision_hash:pack.revision_hash,workspace,access:'read_only',
  inputs:{task:'Neutral fixture'},main_actor:'codex',native_parent_thread_id:thread});
 const binding={run_id:run.run_id,control_token:run.control_token};
 const {runtime,drive}=await service.open();await retainOwnedAuthority(runtime,run);
 const open=service.open.bind(service);service.open=async(...args)=>{
  const value=await open(...args),advance=value.drive.advanceToMain.bind(value.drive);
  if(journalFailure)value.runtime.failNode=async()=>{failCommits++;throw Object.assign(new Error('Neutral failure journal write failed after confirmed cleanup'),{code:'EIO'});};
  value.drive.advanceToMain=async(...args)=>{
   advances++;if(advances>2)throw Object.assign(new Error('Settled failed job was recursively advanced'),{code:'FIXTURE_RECURSIVE_JOIN'});
   return advance(...args);
  };return value;
 };
 return {service,manager,runtime,drive,binding,starts:()=>starts,turns:()=>turns,advances:()=>advances,
  closes:()=>closes,quiesces:()=>quiesces,failCommits:()=>failCommits};
}

test('real service join returns settled uncertain worker failure without advancing or redispatching',async t=>{
 const f=await fixture(t),result=await f.service.call('native_next',{},model);
 assert.equal(result.status,'running');assert.equal(result.wake_reason,'host_failed');
 assert.equal(result.completion_satisfied,false);assert.equal(result.host_worker.phase,'audit_or_cleanup_failed');
 assert.equal(result.host_worker.cleanup_pending,true);assert.equal(result.host_worker.node_id,'final');assert(result.host_worker.attempt_id);
 assert.match(result.host_worker.error.diagnostic,/CODEX_RPC_ERROR/);assert.match(result.host_worker.error.diagnostic,/CODEX_APP_SERVER_PIPE_HELD/);
 assert.equal(JSON.stringify(result).includes('secret-value'),false);assert.equal(JSON.stringify(result).includes(f.binding.control_token),false);
 const state=await f.runtime.get(f.binding.run_id),entry=f.manager.entries.get(f.binding.run_id);
 assert.equal(state.status,'running');assert.equal(state.nodes.final.status,'running');
 assert.equal(state.nodes.final.active_attempt_id,result.host_worker.attempt_id);assert.equal(state.nodes.final.attempts.length,1);
 assert.equal(entry.cleanupPending,true);assert(entry.session);assert(entry.broker);
 assert.equal(f.starts(),1);assert.equal(f.turns(),1);assert.equal(f.advances(),1);
 const again=await f.service.call('native_next',{},model);assert.equal(again.wake_reason,'host_failed');
 assert.equal(f.starts(),1);assert.equal(f.turns(),1);assert.equal(f.advances(),2);
});

test('public wait prefers exact local settled failure over an older detached semantic heartbeat',async t=>{
 const f=await fixture(t),handoff=await f.drive.advanceToMain(f.binding.run_id,{control_token:f.binding.control_token,owner:'codex',request_prefix:'neutral'});
 await f.manager.launch({runtime:f.runtime,drive:f.drive,handoff});await f.manager.wait(f.binding.run_id);
 await writeFile(join(f.runtime.runs.directory(f.binding.run_id),'host-main-worker.json'),JSON.stringify({run_id:f.binding.run_id,pid:process.pid,
  phase:'attention',at:new Date().toISOString(),outcome:{status:'running',stop_reason:'main_orchestration',node_id:'old-node'}}));
 const result=await f.service.call('wait',{...f.binding,timeout_ms:100});
 assert.equal(result.wake_reason,'host_failed');assert.equal(result.status,'running');assert.equal(result.host_worker.phase,'audit_or_cleanup_failed');
 assert.equal(result.host_worker.node_id,'final');assert.equal(result.host_worker.attempt_id,handoff.host_binding.attempt_id);
 assert.equal(result.host_worker.cleanup_pending,true);assert.equal(result.next_action,undefined);assert.equal(result.control_token,undefined);
 assert.match(result.host_worker.error.secondary_diagnostic,/CODEX_APP_SERVER_PIPE_HELD/);
 assert(result.host_worker.error.diagnostic.length<=2000);assert(result.host_worker.error.secondary_diagnostic.length<=2000);
 const record=await f.runtime.runs.read(f.binding.run_id);assert(f.manager.failureWorker(record));
 for(const change of [
  state=>{state.status='paused';},state=>{state.status='cancelled';},state=>{state.status='succeeded';},state=>{state.status='failed';},
  state=>{state.nodes.final.active_attempt_id='successor';},state=>{state.nodes.final.status='succeeded';},
  state=>{state.nodes.final.attempts[0].status='failed';},state=>{state.nodes.final.attempts[0].owner='other';},
  state=>{state.control_hash=digest('new-controller');},state=>{state.nodes.final.attempts[0].lease_hash=digest('new-lease');},
  state=>{state.main_actor='other';}
 ]){const changed=structuredClone(record);change(changed.state);assert.equal(f.manager.failureWorker(changed),null);}
});

test('real service join continues a successfully closed worker to actual terminal completion',async t=>{
 const f=await fixture(t,{uncertain:false}),result=await f.service.call('native_next',{},model);
 assert.equal(result.status,'succeeded');
 const state=await f.runtime.get(f.binding.run_id);assert.equal(state.nodes.final.status,'succeeded');assert.equal(state.nodes.final.attempts.length,1);
 assert.equal(f.starts(),1);assert.equal(f.turns(),1);assert.equal(f.advances(),2);
});

for(const heartbeat of ['old','absent'])test(`confirmed cleanup then failure-journal EIO stays visible with ${heartbeat} detached heartbeat`,async t=>{
 const f=await fixture(t,{uncertain:false,journalFailure:true});
 if(heartbeat==='old')await writeFile(join(f.runtime.runs.directory(f.binding.run_id),'host-main-worker.json'),JSON.stringify({run_id:f.binding.run_id,pid:process.pid,
  phase:'attention',at:new Date().toISOString(),outcome:{status:'running',stop_reason:'main_orchestration',node_id:'old-node'}}));
 let result;
 if(heartbeat==='old')result=await f.service.call('native_next',{},model);
 else{
  const {runtime,drive}=await f.service.open();
  const handoff=await drive.advanceToMain(f.binding.run_id,{control_token:f.binding.control_token,owner:'codex',request_prefix:'neutral-audit'});
  await f.manager.launch({runtime,drive,handoff});await f.manager.wait(f.binding.run_id);
  result=await f.service.call('wait',{...f.binding,timeout_ms:100});
 }
 assert.equal(result.wake_reason,'host_failed');assert.equal(result.status,'running');assert.equal(result.next_action,undefined);
 assert.equal(result.host_worker.cleanup_pending,false);assert.equal(result.host_worker.phase,'audit_or_cleanup_failed');
 assert.match(result.host_worker.error.diagnostic,/CODEX_RPC_ERROR/);assert.deepEqual(result.host_worker.error.secondary_codes,['EIO']);
 assert.match(result.host_worker.error.secondary_diagnostic,/EIO/);assert.doesNotMatch(result.host_worker.error.secondary_diagnostic,/cleanup remains unconfirmed/);
 assert(result.host_worker.error.secondary_diagnostic.length<=2000);
 const entry=f.manager.entries.get(f.binding.run_id),record=await f.runtime.runs.read(f.binding.run_id);
 assert.equal(entry.cleanupPending,false);assert.equal(entry.handoff,null);assert.equal(entry.session,null);assert.equal(entry.broker,null);
 assert.equal(entry.controlToken,null);assert.equal(entry.owner,null);assert(Object.isFrozen(entry.failureIdentity));
 assert.equal(JSON.stringify(entry.failureIdentity).includes(f.binding.control_token),false);
 const attempt=record.state.nodes.final.attempts[0];
 assert.equal(entry.failureIdentity.control_hash,record.state.control_hash);assert.equal(entry.failureIdentity.lease_hash,attempt.lease_hash);
 assert.equal(result.host_worker.attempt_id,attempt.id);assert.equal(record.state.nodes.final.active_attempt_id,attempt.id);
 assert.equal(record.state.status,'running');assert.equal(record.state.nodes.final.status,'running');assert.equal(record.state.nodes.final.attempts.length,1);
 assert.equal(f.starts(),1);assert.equal(f.turns(),1);assert.equal(f.closes(),1);assert.equal(f.quiesces(),1);assert.equal(f.failCommits(),1);
 const repeat=await f.service.call('wait',{...f.binding,timeout_ms:100});assert.equal(repeat.wake_reason,'host_failed');
 assert.equal(f.starts(),1);assert.equal(f.turns(),1);assert.equal(f.failCommits(),1);
 for(const change of [state=>{state.status='succeeded';},state=>{state.status='paused';},state=>{state.status='cancelled';},
  state=>{state.nodes.final.active_attempt_id='successor';},state=>{state.control_hash=digest('recovered-controller');},
  state=>{state.nodes.final.attempts[0].lease_hash=digest('recovered-lease');},state=>{state.nodes.final.attempts[0].owner='other';}]){
  const changed=structuredClone(record);change(changed.state);assert.equal(f.manager.failureWorker(changed),null);
 }
});
