import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,readFile,writeFile,rm} from 'node:fs/promises';
import {join} from 'node:path';
import {tmpdir} from './physical-tempdir.mjs';
import {randomUUID,randomBytes} from 'node:crypto';
import {digest} from '../lib/workflow-revisions.mjs';
import {canonicalJSON} from '../lib/workflow-revisions.mjs';
import {WorkflowRunStore} from '../lib/workflow-run-store.mjs';
import {decodeEvents,replayEvents,readStartedEvent,appendEvent} from '../lib/workflow-events.mjs';
import {retainOwnedAuthority,readOwnedAuthority,readOwnedAuthorityForThread} from '../lib/execution/owned-workflow-authority.mjs';
test('Host retains exact authority for authenticated human cancellation and rejects stale or cross-Run data',async t=>{
 const directory=await mkdtemp(join(tmpdir(),'owned-authority-'));t.after(()=>rm(directory,{recursive:true,force:true}));
 const run={run_id:randomUUID(),control_token:randomBytes(32).toString('hex')};
 let hash=digest(run.control_token);
 const runtime={runs:{directory:()=>directory,withRunWriter:async(id,action)=>{assert.equal(id,run.run_id);return action();},read:async()=>({state:{run_id:run.run_id,control_hash:hash,main_actor:'exact-owner'}})},
  authorizeController:async(id,args)=>{assert.equal(id,run.run_id);assert.equal(args.control_token,run.control_token);}};
 await retainOwnedAuthority(runtime,run);
 await retainOwnedAuthority(runtime,run);
 assert.deepEqual(await readOwnedAuthority(runtime,run.run_id),{...run,owner:'exact-owner'});
 hash=digest('rotated');await assert.rejects(readOwnedAuthority(runtime,run.run_id),{code:'RUN_AUTHORITY'});
 hash=digest(run.control_token);
 await writeFile(join(directory,'host-authority.json'),JSON.stringify({...run,run_id:randomUUID()}));
 await assert.rejects(readOwnedAuthority(runtime,run.run_id),{code:'RUN_AUTHORITY'});
});

test('thread lookup validates candidate metadata while explicit audits verify resource contents',async t=>{
 const directory=await mkdtemp(join(tmpdir(),'owned-thread-locator-'));t.after(()=>rm(directory,{recursive:true,force:true}));
 const runs=await new WorkflowRunStore(directory).initialize(),thread=randomUUID(),foreign=randomUUID(),ids=[];
 async function create(parent,status='running'){
  const id=randomUUID(),bytes=Buffer.from('pinned '+id),sha256=digest(bytes),pins={resources:[{path:'rule.md',sha256,bytes:bytes.length}]};
  await runs.create(id,pins,new Map([[sha256,bytes]]),{run_id:id,pins_hash:digest(canonicalJSON(pins)),status,constraints:{native_parent_thread_id:parent},nodes:{},edges:{},approvals:{}});
  return {id,sha256,bytes};
 }
 const active=await create(thread),done=await create(thread,'succeeded');
 for(let i=0;i<8;i++)ids.push(await create(foreign));
 const reads=[],observe=runs.observe.bind(runs);runs.observe=async id=>{reads.push(id);return observe(id);};
 await writeFile(join(runs.directory(ids[0].id),'objects',ids[0].sha256),'broken');
 assert.deepEqual((await runs.listForThread(thread)).map(r=>r.state.run_id).sort(),[active.id,done.id].sort());
 assert.deepEqual(reads.sort(),[active.id,done.id].sort());
 assert.equal((await runs.list()).length,10);
 await assert.rejects(runs.audit(ids[0].id),{code:'RUN_RESOURCE_CORRUPT'});
 await writeFile(join(runs.directory(active.id),'objects',active.sha256),'broken');
 assert.equal((await runs.listForThread(thread)).length,2);
 await assert.rejects(runs.audit(active.id),{code:'RUN_RESOURCE_CORRUPT'});
 await writeFile(join(runs.directory(active.id),'objects',active.sha256),active.bytes);
 const journal=join(runs.directory(ids[1].id),'events.jsonl'),original=await readFile(journal),event=JSON.parse(original.toString().trim());
 event.hash='0'.repeat(64);await writeFile(journal,canonicalJSON(event)+'\n');
 await assert.rejects(runs.listForThread(thread),{code:'RUN_JOURNAL_CORRUPT'});await writeFile(journal,original);
 await assert.rejects(runs.mutate(active.id,'pause',state=>{state.constraints.native_parent_thread_id=foreign;}),{code:'RUN_THREAD_IDENTITY'});
 await assert.rejects(runs.mutate(active.id,'pause',state=>{delete state.constraints.native_parent_thread_id;}),{code:'RUN_THREAD_IDENTITY'});
 await assert.rejects(runs.recover(active.id,state=>{state.constraints.native_parent_thread_id=foreign;}),{code:'RUN_THREAD_IDENTITY'});
 await runs.mutate(active.id,'pause',state=>{state.constraints.network=false;});
 assert.equal((await runs.read(active.id)).state.constraints.network,false);
 const activePath=join(runs.directory(active.id),'events.jsonl'),activeBytes=await readFile(activePath),events=decodeEvents(activeBytes).events;
 const content={sequence:events.length+1,previous:events.at(-1).hash,kind:'pause',at:new Date().toISOString(),payload:{patch:{fields:{constraints:{native_parent_thread_id:foreign}},nodes:{},edges:{},approvals:{}}}};
 assert.throws(()=>replayEvents([...events,{...content,hash:digest(canonicalJSON(content))}]),{code:'RUN_THREAD_IDENTITY'});
 await writeFile(activePath,Buffer.concat([activeBytes,Buffer.from(canonicalJSON({...content,hash:digest(canonicalJSON(content))})+'\n')]));
 await assert.rejects(runs.listForThread(thread),{code:'RUN_THREAD_IDENTITY'});
});

test('started-event locator refuses incomplete, oversized and invalid starts',async t=>{
 const directory=await mkdtemp(join(tmpdir(),'owned-start-prefix-'));t.after(()=>rm(directory,{recursive:true,force:true}));const path=join(directory,'events.jsonl');
 for(const bytes of ['', '{}', '{}\n', 'x'.repeat(4*1024*1024+1)]){await writeFile(path,bytes);await assert.rejects(readStartedEvent(path));}
 await rm(path);const event=await appendEvent(path,[],'started',{state:{run_id:randomUUID(),note:'你'.repeat(2800)}});
 assert.deepEqual(await readStartedEvent(path),event);
});

test('real thread authority rejects ambiguity, excludes current terminal Runs and forbids adding a binding',async t=>{
 const directory=await mkdtemp(join(tmpdir(),'owned-thread-ambiguity-'));t.after(()=>rm(directory,{recursive:true,force:true}));
 const runs=await new WorkflowRunStore(directory).initialize(),thread=randomUUID(),runtime={runs,authorizeController:async()=>{}};
 async function create(constraints){const run={run_id:randomUUID(),control_token:randomBytes(32).toString('hex')},pins={resources:[]};
  await runs.create(run.run_id,pins,new Map(),{run_id:run.run_id,pins_hash:digest(canonicalJSON(pins)),control_hash:digest(run.control_token),main_actor:'codex',status:'running',constraints,nodes:{},edges:{},approvals:{}});
  await retainOwnedAuthority(runtime,run);return run;
 }
 await assert.rejects(readOwnedAuthorityForThread(runtime,thread),{code:'MODEL_RUN_AUTHORITY'});
 const unbound=await create({});
 await assert.rejects(runs.mutate(unbound.run_id,'pause',state=>{state.constraints.native_parent_thread_id=thread;}),{code:'RUN_THREAD_IDENTITY'});
 await assert.rejects(runs.recover(unbound.run_id,state=>{state.constraints.native_parent_thread_id=thread;}),{code:'RUN_THREAD_IDENTITY'});
 const first=await create({native_parent_thread_id:thread}),second=await create({native_parent_thread_id:thread});
 await assert.rejects(readOwnedAuthorityForThread(runtime,thread),{code:'MODEL_RUN_AUTHORITY'});
 await runs.mutate(first.run_id,'complete',state=>{state.status='succeeded';});
 assert.equal((await readOwnedAuthorityForThread(runtime,thread)).run_id,second.run_id);
 const path=join(runs.directory(unbound.run_id),'events.jsonl'),event=JSON.parse((await readFile(path,'utf8')).trim());
 event.payload.state.run_id=randomUUID();const {hash,...content}=event;event.hash=digest(canonicalJSON(content));await writeFile(path,canonicalJSON(event)+'\n');
 await assert.rejects(runs.listForThread(thread),{code:'RUN_IDENTITY'});
});

test('fresh Host requests recover one active Run from authenticated thread metadata without model fields',async t=>{
 const directory=await mkdtemp(join(tmpdir(),'owned-thread-authority-'));t.after(()=>rm(directory,{recursive:true,force:true}));
 const threadId=randomUUID(),run={run_id:randomUUID(),control_token:randomBytes(32).toString('hex')};
 const state={run_id:run.run_id,status:'running',control_hash:digest(run.control_token),main_actor:'codex',constraints:{native_parent_thread_id:threadId}};
 const runtime={runs:{directory:()=>directory,withRunWriter:async(id,action)=>{assert.equal(id,run.run_id);return action();},listForThread:async id=>id===threadId?[{state}]:[],read:async()=>({state})},
  authorizeController:async()=>{}};
 await retainOwnedAuthority(runtime,run);
 assert.deepEqual(await readOwnedAuthorityForThread(runtime,threadId),{...run,owner:'codex'});
 await assert.rejects(readOwnedAuthorityForThread(runtime,randomUUID()),{code:'MODEL_RUN_AUTHORITY'});
 await assert.rejects(readOwnedAuthorityForThread(runtime,'copied-by-model'),{code:'MODEL_THREAD_ID'});
});
