import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,mkdir,writeFile,appendFile,open,readFile,rename,rm,lstat} from 'node:fs/promises';
import {join} from 'node:path';
import {tmpdir} from './physical-tempdir.mjs';
import {createNativeLifecycleReader} from '../lib/execution/native-agent-lifecycle.mjs';
import {withNativeAgentObserverDrive} from '../lib/execution/native-agent-observer.mjs';
const parent='00000000-0000-7000-8000-000000000099';
const row=(type,payload)=>JSON.stringify({type,payload})+'\n';
const deferred=()=>{let resolve;const promise=new Promise(r=>resolve=r);return {promise,resolve};};
async function fixture(t,count=1){
 const home=await mkdtemp(join(tmpdir(),'native-reader-race-'));await mkdir(join(home,'sessions'));
 t.after(()=>rm(home,{recursive:true,force:true}));
 const items=[];for(let i=0;i<count;i++){
  const id='00000000-0000-7000-8000-'+String(i).padStart(12,'0'),agent='/root/worker_'+i,path=join(home,'sessions','rollout-'+id+'.jsonl'),turn='turn-'+i;
  const meta={id,parent_thread_id:parent,agent_path:agent,source:{subagent:{thread_spawn:{parent_thread_id:parent,agent_path:agent}}}};
  await writeFile(path,row('session_meta',meta)+row('event_msg',{type:'task_started',turn_id:turn}));
  items.push({path,turn,args:{thread:{id,path},agentId:agent,parentThreadId:parent}});
 }
 return {home,items};
}
async function firstReadBarrier(path){
 const handle=await open(path,'r'),prototype=Object.getPrototypeOf(handle);await handle.close();
 const original=prototype.read,entered=deferred(),release=deferred(),second=deferred(),positions=[];let active=0,maxActive=0;
 prototype.read=async function(...args){
  positions.push(args[3]);active++;maxActive=Math.max(maxActive,active);
  try{const result=await original.apply(this,args);if(positions.length===1){entered.resolve();await release.promise;}else second.resolve();return result;}
  finally{active--;}
 };
 return {entered,release,second,positions,maxActive:()=>maxActive,restore:()=>{release.resolve();prototype.read=original;}};
}
async function completesBeforeRelease(promise){
 let timer;try{return await Promise.race([promise.then(()=>true),new Promise(resolve=>timer=setTimeout(()=>resolve(false),500))]);}finally{clearTimeout(timer);}
}
test('concurrent observations consume a legal append once without reporting a truncated rollout',async t=>{
 const f=await fixture(t),item=f.items[0],reader=createNativeLifecycleReader({home:f.home});await reader(item.args);
 const before=(await lstat(item.path)).size,append=row('event_msg',{type:'token_count'});await appendFile(item.path,append);
 const barrier=await firstReadBarrier(item.path);let first,second;
 try{
  first=reader(item.args);await barrier.entered.promise;second=reader(item.args);
  // The first real read has completed but cannot yet advance the parser. On
  // the old reader a second real read enters at the exact same byte offset.
  await completesBeforeRelease(barrier.second.promise);barrier.release.resolve();
  const outcomes=await Promise.all([first,second]);assert(outcomes.every(o=>o.status==='pending'));
  console.log(JSON.stringify({barrier_read_positions:barrier.positions,file_size:(await lstat(item.path)).size,initial_offset:before,append_bytes:Buffer.byteLength(append),reported_bytes:outcomes.map(o=>o.bytes_read),max_same_thread_reads:barrier.maxActive()}));
  const next=await reader(item.args);assert.equal(next.status,'pending');assert.equal(next.bytes_read,0);
  assert.deepEqual(barrier.positions,[before]);assert.equal(outcomes.reduce((n,o)=>n+o.bytes_read,0),Buffer.byteLength(append));
  console.log(JSON.stringify({read_positions:barrier.positions,file_size:(await lstat(item.path)).size,initial_offset:before,append_bytes:Buffer.byteLength(append),max_same_thread_reads:barrier.maxActive()}));
 }finally{barrier.restore();await Promise.allSettled([first,second].filter(Boolean));}
});
test('independent native child readers remain parallel while one thread read is blocked',async t=>{
 const f=await fixture(t,3),reader=createNativeLifecycleReader({home:f.home});for(const item of f.items)await reader(item.args);
 for(const item of f.items)await appendFile(item.path,row('event_msg',{type:'token_count'}));
 const barrier=await firstReadBarrier(f.items[0].path);let blocked,others;
 try{
  blocked=reader(f.items[0].args);await barrier.entered.promise;
  others=Promise.all(f.items.slice(1).map(item=>reader(item.args)));assert.equal(await completesBeforeRelease(others),true,'Other thread identities must not queue behind the blocked child');
  barrier.release.resolve();await blocked;assert.equal((await others).length,2);assert(barrier.maxActive()>=2);
 }finally{barrier.restore();await Promise.allSettled([blocked,others].filter(Boolean));}
});
test('replacement, truncation and rewrite to a shorter prefix keep exact guard diagnostics',async t=>{
 for(const mutation of ['replacement','truncation','shorter-rewrite']){
  const f=await fixture(t),item=f.items[0],reader=createNativeLifecycleReader({home:f.home});await reader(item.args);
  const old=await readFile(item.path),before=await lstat(item.path);
  if(mutation==='replacement'){await rename(item.path,item.path+'.old');await writeFile(item.path,old);}else await writeFile(item.path,mutation==='truncation'?'':old.subarray(0,20));
  await assert.rejects(reader(item.args),error=>{
   assert.equal(error.code,'NATIVE_AGENT_LIFECYCLE_CHANGED');assert.equal(error.diagnostic.thread_id,item.args.thread.id);
   assert.equal(error.diagnostic.guard,mutation==='replacement'?'retained_identity':'observed_size');
   assert.equal(error.diagnostic.observed_offset,before.size);assert.equal(typeof error.diagnostic.opened.size,'number');return true;
  });
 }
});
test('a queued observation retains exact parent and Agent-path identity checks after a prior failure',async t=>{
 const f=await fixture(t),item=f.items[0],reader=createNativeLifecycleReader({home:f.home});await reader(item.args);
 await assert.rejects(reader({...item.args,parentThreadId:'00000000-0000-7000-8000-000000000098'}),{code:'NATIVE_AGENT_LIFECYCLE_IDENTITY'});
 assert.equal((await reader(item.args)).status,'pending');
 await assert.rejects(reader({...item.args,agentId:'/root/foreign'}),{code:'NATIVE_AGENT_LIFECYCLE_IDENTITY'});
});
test('observer boundary retains the exact lifecycle guard diagnostic while still rejecting',async t=>{
 const f=await fixture(t),item=f.items[0],reader=createNativeLifecycleReader({home:f.home}),reports=[];await reader(item.args);await writeFile(item.path,'');
 await assert.rejects(withNativeAgentObserverDrive(()=>reader(item.args),{onObservation:async report=>reports.push(report)}),error=>{
  assert.equal(error.code,'NATIVE_AGENT_LIFECYCLE_CHANGED');assert.match(error.message,new RegExp(item.args.thread.id));assert.equal(error.diagnostic.guard,'observed_size');return true;
 });
 assert.equal(reports.length,1);assert.equal(reports[0].status,'failed');assert.deepEqual(reports[0].error_codes,['NATIVE_AGENT_LIFECYCLE_CHANGED']);
 assert.equal(reports[0].lifecycle_changes.length,1);assert.equal(reports[0].lifecycle_changes[0].thread_id,item.args.thread.id);assert.equal(reports[0].lifecycle_changes[0].opened.size,0);
 assert(!JSON.stringify(reports[0].lifecycle_changes).includes(item.path));
});
