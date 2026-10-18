import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,mkdir,rm,writeFile,readFile,lstat,unlink} from 'node:fs/promises';
import {join} from 'node:path';
import {tmpdir} from './physical-tempdir.mjs';
import {WorkflowRunStore} from '../lib/workflow-run-store.mjs';
import {WorkflowRuntime} from '../lib/workflow-runtime.mjs';
import {WorkflowStore,withRunAdmissionObserver,admissionTrace} from '../lib/workflow-store.mjs';
import {randomUUID} from 'node:crypto';
import {createDraft} from '../lib/workflow-schema.mjs';
import {canonicalJSON,digest} from '../lib/workflow-revisions.mjs';
import {spawn,execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {pathToFileURL} from 'node:url';

const latch=()=>{let release;return {promise:new Promise(r=>release=r),release:()=>release()};};
async function fixture(t){
 const root=await mkdtemp(join(tmpdir(),'history-maintenance-'));
 t.after(()=>rm(root,{recursive:true,maxRetries:3,retryDelay:100}));
 const store=await new WorkflowRunStore(join(root,'runs')).initialize();
 return {root,store};
}
async function addRun(store,id){
 const pins={resources:[],root:{workflow:{id:'flow',nodes:[],edges:[]}}};
 await store.create(id,pins,new Map(),{schema_version:1,run_id:id,workflow_id:'flow',status:'succeeded',
  pins_hash:digest(canonicalJSON(pins)),created_at:'2026-01-01T00:00:00.000Z',updated_at:'2026-01-01T00:00:00.000Z',nodes:{},parallel:{}});
}
async function runtimeFixture(t,historyMaintenance){
 const f=await fixture(t),workspace=join(f.root,'workspace');await mkdir(workspace);
 const workflow={...createDraft('selected','Selected'),status:'ready',enabled:true,
  finalization:{required:true,node_id:'final'},skill_policy:{mode:'cooperative',implicit:'allow',ambient_allow:[],shadowed_skill_paths:[]},
  nodes:[{id:'start',type:'start'},{id:'final',type:'agent',executor:{kind:'main'},role:'finalizer',access:'read_only',prompt_template:'Finish',approval:{required:false},retry:{max_attempts:1},input_bindings:{}},{id:'end',type:'end'}],
  edges:[{id:'a',source:'start',target:'final'},{id:'b',source:'final',target:'end'}]};
 const workflows=await new WorkflowStore(join(f.root,'workflows')).initialize();await workflows.create(workflow);
 const runtime=await new WorkflowRuntime({workflowStore:workflows,runRoot:f.store.root,historyMaintenance}).initialize();
 return {...f,runtime,start:()=>runtime.start({workflow_id:'selected',workspace,access:'read_only',main_actor:'root'})};
}

test('a supplied maintenance hook publishes selected startup without entering unrelated history',async t=>{
 let calls=0;const f=await runtimeFixture(t,()=>{calls++;});
 await addRun(f.store,'corrupt-unrelated');await writeFile(join(f.store.directory('corrupt-unrelated'),'pins.json'),'{}');
 const result=await f.start();assert.equal(result.workflow_id,'selected');assert.equal(calls,1);
});
test('standalone Runtime still awaits and reports full cleanup failure',async t=>{
 const f=await runtimeFixture(t);await addRun(f.store,'corrupt');await writeFile(join(f.store.directory('corrupt'),'pins.json'),'{}');
 await assert.rejects(f.start(),{code:'RUN_PINS_CORRUPT'});
});
test('cleanup cancellation admits no reads and retains history',async t=>{
 const {store}=await fixture(t);await addRun(store,'old');let reads=0;
 const original=store.readHistoryMetadata.bind(store);store.readHistoryMetadata=(...args)=>{reads++;return original(...args);};
 const controller=new AbortController();controller.abort();
 await assert.rejects(store.cleanupHistory({olderThanMs:0,signal:controller.signal}),{code:'RUN_HISTORY_CANCELLED'});
 assert.equal(reads,0);assert((await lstat(store.directory('old'))).isDirectory());
});
test('cleanup cancellation settles admitted reads and fences deletion',async t=>{
 const {store}=await fixture(t);for(let i=0;i<7;i++)await addRun(store,`old-${i}`);
 const entered=latch(),proceed=latch(),controller=new AbortController();let reads=0,settled=false;
 const original=store.readHistoryMetadata.bind(store);store.readHistoryMetadata=async(...args)=>{reads++;entered.release();await proceed.promise;return original(...args);};
 const cleanup=store.cleanupHistory({olderThanMs:0,signal:controller.signal}).finally(()=>settled=true);
 const rejection=assert.rejects(cleanup,{code:'RUN_HISTORY_CANCELLED'});
 await entered.promise;controller.abort();await new Promise(r=>setTimeout(r,20));assert.equal(settled,false);
 proceed.release();await rejection;assert.equal(reads,4);assert((await lstat(store.directory('old-0'))).isDirectory());
});

async function maintenance(){return import('../lib/run-history-maintenance.mjs');}
// Explicit lifecycle DI for paused/persistence fixtures. Production never
// executes a supplied store's audit in the request process.
const testWorker=store=>async({signal,onReady})=>{
 await onReady(process.pid);
 try{return await store.cleanupHistory({signal});}
 catch(error){error.worker_quiescent=true;error.worker_cancelled=signal.aborted&&error.code==='RUN_HISTORY_CANCELLED';throw error;}
};
test('a paused unrelated full-history read does not block selected startup publication', {timeout:5000},async t=>{
 const {RunHistoryMaintenance}=await maintenance();let manager;
 const f=await runtimeFixture(t,store=>manager.schedule(store));manager=new RunHistoryMaintenance({runRoot:f.store.root,launchWorker:testWorker(f.store)});
 await addRun(f.store,'unrelated');const entered=latch(),proceed=latch(),original=f.store.readHistoryMetadataBatch.bind(f.store);
 f.store.readHistoryMetadataBatch=async(...args)=>{entered.release();await proceed.promise;return original(...args);};
 manager.schedule(f.store);await entered.promise;
 try{const run=await f.start();assert(run.run_id);assert((await lstat(f.runtime.runs.directory(run.run_id))).isDirectory());}
 finally{proceed.release();await manager.settle();await manager.close();}
});
test('two processes coalesce requests under one live exact maintenance owner', {timeout:5000},async t=>{
 const {store}=await fixture(t),{RunHistoryMaintenance}=await maintenance();const entered=latch(),proceed=latch();let calls=0;
 store.cleanupHistory=async()=>{calls++;entered.release();await proceed.promise;return {examined:0,deleted_count:0,preserved_count:0};};
 const manager=new RunHistoryMaintenance({runRoot:store.root,launchWorker:testWorker(store)});manager.schedule(store);await entered.promise;
 const moduleURL=new URL('../lib/run-history-maintenance.mjs',import.meta.url).href;
 const child=spawn(process.execPath,['--input-type=module','--eval',`import {RunHistoryMaintenance} from ${JSON.stringify(moduleURL)};
  const manager=new RunHistoryMaintenance({runRoot:${JSON.stringify(store.root)}});let audits=0;
  manager.schedule({root:${JSON.stringify(store.root)},cleanupHistory:async()=>{audits++;throw new Error('foreign audit');}});
  await manager.settle();process.send({audits,status:await manager.status()});await manager.close();process.disconnect();`],{stdio:['ignore','pipe','pipe','ipc']});
 let stderr='';child.stderr.on('data',bytes=>stderr+=bytes);
 const exited=new Promise((resolve,reject)=>{child.once('error',reject);child.once('exit',code=>code===0?resolve():reject(new Error(stderr||`child exit ${code}`)));});
 try{
  const message=await new Promise((resolve,reject)=>{child.once('message',resolve);exited.then(()=>reject(new Error('child exited without status')),reject);});
  assert.equal(message.audits,0);assert.equal(message.status.owner_pid,process.pid);assert.equal(message.status.outcome,'pending');
  assert.equal(message.status.job_id,(await manager.status()).job_id);await exited;assert.equal(calls,1);
 }finally{proceed.release();await manager.settle();await manager.close();}
});
test('a second process recognizes bounded empty claim initialization without poisoning maintenance', {timeout:5000},async t=>{
 const {store}=await fixture(t),{RunHistoryMaintenance}=await maintenance();
 const directory=join(store.root,'.run-locks','.history-maintenance');await mkdir(directory);
 const child=spawn(process.execPath,['--input-type=module','--eval',`import {open,unlink} from 'node:fs/promises';
  const path=${JSON.stringify(join(directory,'.writer.lock'))};const handle=await open(path,'wx',0o600);
  process.send({phase:'initializing'});process.on('message',async message=>{
   if(message==='publish'){const now=Date.now();await handle.writeFile(JSON.stringify({schema_version:1,
    job_id:'00000000-0000-4000-8000-000000000003',owner_token:'00000000-0000-4000-8000-000000000004',owner_pid:process.pid,
    created_at:now,due_at:now+60000,phase:'claimed',outcome:'pending'}));await handle.sync();process.send({phase:'published'});}
   if(message==='close'){await handle.close();await unlink(path);process.disconnect();}
  });`],{stdio:['ignore','pipe','pipe','ipc']});
 let stderr='';child.stderr.on('data',bytes=>stderr+=bytes);
 const exited=new Promise((resolve,reject)=>{child.once('error',reject);child.once('exit',code=>code===0?resolve():reject(new Error(stderr||`child exit ${code}`)));});
 const initializing=await new Promise((resolve,reject)=>{child.once('message',resolve);exited.then(()=>reject(new Error('initializing child exited')),reject);});
 assert.equal(initializing.phase,'initializing');let audits=0;
 const manager=new RunHistoryMaintenance({runRoot:store.root});store.cleanupHistory=async()=>{audits++;};manager.schedule(store);
 await new Promise(r=>setTimeout(r,40));child.send('publish');
 try{await manager.settle();assert.equal(audits,0);assert.equal((await manager.status()).owner_pid,child.pid);
  await assert.rejects(lstat(join(directory,'diagnostic.json')),{code:'ENOENT'});await manager.close();}
 finally{child.send('close');await exited;}
});
test('bounded shutdown does not await a hung receipt write tail or clear the claim', {timeout:5000},async t=>{
 const {store}=await fixture(t),{RunHistoryMaintenance}=await maintenance();const entered=latch(),proceed=latch(),writes=latch();
 store.cleanupHistory=async({signal})=>{entered.release();await proceed.promise;
  if(signal.aborted)throw Object.assign(new Error('Fixture cancelled before commit'),{code:'RUN_HISTORY_CANCELLED'});
  return {examined:0,deleted_count:0,preserved_count:0};};
 const manager=new RunHistoryMaintenance({runRoot:store.root,settlementMs:25,launchWorker:testWorker(store)});manager.schedule(store);await entered.promise;
 manager.writes=writes.promise;const began=Date.now();
 try{await assert.rejects(manager.close(),error=>error.code==='RUN_HISTORY_MAINTENANCE_STOP_PENDING'&&error.persistence_error.code==='RUN_HISTORY_MAINTENANCE_RECEIPT_PENDING');
  assert(Date.now()-began<1000);assert((await lstat(join(store.root,'.run-locks','.history-maintenance','.writer.lock'))).isFile());
  assert.equal((await manager.status()).outcome,'pending');}
 finally{writes.release();proceed.release();await manager.settle();}
});
test('diagnostics bound large partial-family evidence and omit raw messages/details and public tokens',async t=>{
 const {store}=await fixture(t),{RunHistoryMaintenance}=await maintenance();
 const ids=Array.from({length:500},(_,i)=>`partial-${i}`),secret='Bearer SECRET_TOKEN api_key=SECRET_KEY';
 store.cleanupHistory=async()=>{throw Object.assign(new Error(secret),{code:'RUN_HISTORY_DELETE_FAILED',family_run_ids:ids,deleted_run_ids:ids.slice(0,400),details:{raw_output:secret}});};
 const manager=new RunHistoryMaintenance({runRoot:store.root,launchWorker:testWorker(store)});manager.schedule(store);
 await assert.rejects(manager.settle(),{code:'RUN_HISTORY_DELETE_FAILED'});const status=await manager.status();
 assert.equal(status.owner_token,undefined);assert.equal(status.error.family_run_ids_count,500);assert.equal(status.error.deleted_run_ids_count,400);
 assert.equal(status.error.family_run_ids_sha256,digest(canonicalJSON(ids)));assert.equal(status.error.message_sha256,digest(secret));
 const bytes=await readFile(join(store.root,'.run-locks','.history-maintenance','receipt.json'));
 assert(bytes.length<16384);assert(!bytes.toString().includes('SECRET'));assert.equal(status.error.details,undefined);
 await assert.rejects(manager.close(),{code:'RUN_HISTORY_DELETE_FAILED'});
});
test('root managers coalesce across recreated runtimes and record exact successful receipts',async t=>{
 const {store}=await fixture(t),{runHistoryMaintenanceFor}=await maintenance();
 const entered=latch(),proceed=latch();let calls=0;
 store.cleanupHistory=async()=>{calls++;entered.release();await proceed.promise;return {examined:0,deleted_count:0,preserved_count:0,deleted_run_ids:[],preserved_run_ids:[]};};
 const manager=runHistoryMaintenanceFor({runRoot:store.root,launchWorker:testWorker(store)});t.after(()=>manager.close());
 manager.schedule(store);await entered.promise;assert.equal(runHistoryMaintenanceFor({runRoot:store.root}),manager);
 manager.schedule(new WorkflowRunStore(store.root));proceed.release();await manager.settle();
 manager.schedule(store);await manager.settle();assert.equal(calls,1);
 const status=await manager.status();assert.equal(status.phase,'settled');assert.equal(status.outcome,'succeeded');assert(status.due_at>Date.now());
 const receipt=JSON.parse(await readFile(join(store.root,'.run-locks','.history-maintenance','receipt.json')));
 assert.equal(receipt.owner_pid,process.pid);assert(receipt.job_id);assert(receipt.owner_token);
});
test('corrupt history retains the original diagnostic and cannot pass or silently retry',async t=>{
 const {store}=await fixture(t),{RunHistoryMaintenance}=await maintenance();await addRun(store,'corrupt');
 await writeFile(join(store.directory('corrupt'),'pins.json'),'{}');const manager=new RunHistoryMaintenance({runRoot:store.root});
 manager.schedule(store);await assert.rejects(manager.settle(),{code:'RUN_PINS_CORRUPT'});
 const status=await manager.status();assert.equal(status.outcome,'failed');assert.equal(status.error.code,'RUN_PINS_CORRUPT');
 const peer=new RunHistoryMaintenance({runRoot:store.root});peer.schedule(store);
 await assert.rejects(peer.settle(),{code:'RUN_PINS_CORRUPT'});await assert.rejects(manager.close(),{code:'RUN_PINS_CORRUPT'});
});
test('bounded unconfirmed shutdown retains its live exact claim and records no success',async t=>{
 const {store}=await fixture(t),{RunHistoryMaintenance}=await maintenance();const entered=latch(),proceed=latch();
 store.cleanupHistory=async({signal})=>{entered.release();await proceed.promise;
  if(signal.aborted)throw Object.assign(new Error('Fixture cancelled before commit'),{code:'RUN_HISTORY_CANCELLED'});
  return {examined:0,deleted_count:0,preserved_count:0};};
 const manager=new RunHistoryMaintenance({runRoot:store.root,settlementMs:25,launchWorker:testWorker(store)});manager.schedule(store);await entered.promise;
 await assert.rejects(manager.close(),{code:'RUN_HISTORY_MAINTENANCE_STOP_PENDING'});
 const status=await manager.status();assert.equal(status.outcome,'stop_pending');
 assert((await lstat(join(store.root,'.run-locks','.history-maintenance','.writer.lock'))).isFile());
 proceed.release();await manager.settle();
 assert.equal((await manager.status()).outcome,'cancelled');
});
test('dead exact owners and malformed claims remain visible and are never replayed',async t=>{
 const {store}=await fixture(t),{RunHistoryMaintenance}=await maintenance();
 const directory=join(store.root,'.run-locks','.history-maintenance');await mkdir(directory);
 const claim={schema_version:1,job_id:'00000000-0000-4000-8000-000000000001',owner_token:'00000000-0000-4000-8000-000000000002',owner_pid:2147483647,created_at:Date.now(),due_at:Date.now()+60000,phase:'claimed',outcome:'pending'};
 await writeFile(join(directory,'.writer.lock'),canonicalJSON(claim));
 const manager=new RunHistoryMaintenance({runRoot:store.root});let calls=0;store.cleanupHistory=async()=>{calls++;};
 manager.schedule(store);await assert.rejects(manager.settle(),{code:'RUN_HISTORY_MAINTENANCE_ORPHANED'});assert.equal(calls,0);
 assert.deepEqual(JSON.parse(await readFile(join(directory,'.writer.lock'))),claim);
 const {store:other}=await fixture(t),otherDirectory=join(other.root,'.run-locks','.history-maintenance');await mkdir(otherDirectory);
 await writeFile(join(otherDirectory,'.writer.lock'),'{}');const peer=new RunHistoryMaintenance({runRoot:other.root});peer.schedule(other);
 await assert.rejects(peer.settle(),{code:'RUN_HISTORY_MAINTENANCE_OWNERSHIP'});assert.equal(calls,0);
});
test('conflicting live claim and unfinished receipt fail without altering either owner',async t=>{
 const {store}=await fixture(t),{RunHistoryMaintenance}=await maintenance();const directory=join(store.root,'.run-locks','.history-maintenance');await mkdir(directory);
 const now=Date.now(),claim={schema_version:1,job_id:'00000000-0000-4000-8000-000000000005',owner_token:'00000000-0000-4000-8000-000000000006',owner_pid:process.pid,created_at:now,due_at:now+60000,phase:'claimed',outcome:'pending'};
 const other={...claim,job_id:'00000000-0000-4000-8000-000000000007',phase:'auditing'};
 await writeFile(join(directory,'.writer.lock'),canonicalJSON(claim));await writeFile(join(directory,'receipt.json'),canonicalJSON(other));
 const manager=new RunHistoryMaintenance({runRoot:store.root});let calls=0;store.cleanupHistory=async()=>{calls++;};manager.schedule(store);
 await assert.rejects(manager.settle(),{code:'RUN_HISTORY_MAINTENANCE_CONFLICT'});assert.equal(calls,0);
 assert.deepEqual(JSON.parse(await readFile(join(directory,'.writer.lock'))),claim);assert.deepEqual(JSON.parse(await readFile(join(directory,'receipt.json'))),other);
 assert.equal((await manager.status()).error.code,'RUN_HISTORY_MAINTENANCE_CONFLICT');
});
test('recreated service runtimes share the hook and existing human bootstrap exposes compact status only',async t=>{
 const {root}=await fixture(t),{WorkflowService}=await import('../lib/workflow-service.mjs'),{WorkbenchApi}=await import('../lib/workbench-api.mjs');
 const {DEFAULT_CONFIG_PATH}=await import('../server.mjs');
 const options={configPath:join(root,'control-plane.json'),defaultConfigPath:DEFAULT_CONFIG_PATH,env:{...process.env,CODEX_WORKFLOW_DISABLED:'0',SOL_CONTROL_DISABLED:'0'}};
 const service=new WorkflowService(options);await service.call('migrate_v6',{}, {human:true});const peer=new WorkflowService(options);
 const [opened,reopened]=await Promise.all([service.open(),peer.open()]);
 assert.equal(service.historyMaintenance,peer.historyMaintenance);assert.equal(opened.runtime.historyMaintenance,reopened.runtime.historyMaintenance);
 const bootstrap=await new WorkbenchApi(options).bootstrap();
 assert.equal(bootstrap.bootstrap['/api/workflow/capabilities'].run_history_maintenance.phase,'idle');
 assert.equal((await service.call('capabilities',{}, {model:true})).run_history_maintenance,undefined);
});
async function metadataFixture(t,pausePath){
 const {store}=await fixture(t),{RunHistoryMaintenance}=await maintenance();const directory=join(store.root,'.run-locks','.history-maintenance');await mkdir(directory);
 const lockPath=join(directory,'.writer.lock'),receiptPath=join(directory,'receipt.json'),entered=latch(),proceed=latch();
 const now=Date.now(),claim={schema_version:1,job_id:'00000000-0000-4000-8000-000000000011',owner_token:'00000000-0000-4000-8000-000000000012',owner_pid:process.pid,created_at:now,due_at:now+60000,phase:'claimed',outcome:'pending'};
 let paused=false;
 const readRecord=async(path,{optional=false}={})=>{
  let value;try{value=JSON.parse(await readFile(path));}catch(error){if(optional&&error.code==='ENOENT')value=null;else throw error;}
  if(!paused&&path===(pausePath==='receipt'?receiptPath:lockPath)){paused=true;entered.release();await proceed.promise;}
  return value;
 };
 const manager=new RunHistoryMaintenance({runRoot:store.root,readRecord});let audits=0;
 store.cleanupHistory=async()=>{audits++;return {examined:0,deleted_count:0,preserved_count:0};};
 return {store,directory,lockPath,receiptPath,entered,proceed,claim,manager,audits:()=>audits};
}
test('a paused pending receipt read recaptures the same peer settlement after exact owner release',async t=>{
 const f=await metadataFixture(t,'receipt');await writeFile(f.lockPath,canonicalJSON(f.claim));
 await writeFile(f.receiptPath,canonicalJSON({...f.claim,phase:'auditing'}));f.manager.schedule(f.store);await f.entered.promise;
 await writeFile(f.receiptPath,canonicalJSON({...f.claim,phase:'settled',outcome:'succeeded'}));await unlink(f.lockPath);f.proceed.release();
 await f.manager.settle();assert.equal(f.audits(),0);assert.equal((await f.manager.status()).outcome,'succeeded');
 await assert.rejects(lstat(join(f.directory,'diagnostic.json')),{code:'ENOENT'});await f.manager.close();
});
test('a paused absent-owner read recaptures the exact peer claim matching its new pending receipt',async t=>{
 const f=await metadataFixture(t,'owner');f.manager.schedule(f.store);await f.entered.promise;
 await writeFile(f.lockPath,canonicalJSON(f.claim));await writeFile(f.receiptPath,canonicalJSON({...f.claim,phase:'auditing'}));f.proceed.release();
 await f.manager.settle();assert.equal(f.audits(),0);assert.equal((await f.manager.status()).owner_pid,process.pid);
 await assert.rejects(lstat(join(f.directory,'diagnostic.json')),{code:'ENOENT'});await f.manager.close();
});
test('released-owner evidence recapture refuses a foreign settled receipt without auditing',async t=>{
 const f=await metadataFixture(t,'receipt');await writeFile(f.lockPath,canonicalJSON(f.claim));await writeFile(f.receiptPath,canonicalJSON({...f.claim,phase:'auditing'}));
 f.manager.schedule(f.store);await f.entered.promise;
 await writeFile(f.receiptPath,canonicalJSON({...f.claim,owner_token:'00000000-0000-4000-8000-000000000013',phase:'settled',outcome:'succeeded'}));
 await unlink(f.lockPath);f.proceed.release();await assert.rejects(f.manager.settle(),{code:'RUN_HISTORY_MAINTENANCE_CONFLICT'});assert.equal(f.audits(),0);
});
for(const variant of ['foreign','malformed','dead'])test(`pending-receipt owner recapture rejects ${variant} ownership without auditing`,async t=>{
 const f=await metadataFixture(t,'owner');f.manager.schedule(f.store);await f.entered.promise;
 const current=variant==='malformed'?{}:variant==='dead'?{...f.claim,owner_pid:2147483647}:{...f.claim,owner_token:'00000000-0000-4000-8000-000000000013'};
 await writeFile(f.lockPath,canonicalJSON(current));await writeFile(f.receiptPath,canonicalJSON({...f.claim,...(variant==='dead'?{owner_pid:2147483647}:{}),phase:'auditing'}));
 f.proceed.release();await assert.rejects(f.manager.settle(),{code:variant==='malformed'?'RUN_HISTORY_MAINTENANCE_OWNERSHIP':variant==='dead'?'RUN_HISTORY_MAINTENANCE_ORPHANED':'RUN_HISTORY_MAINTENANCE_CONFLICT'});assert.equal(f.audits(),0);
 assert.deepEqual(JSON.parse(await readFile(f.lockPath)),current);
});

test('default maintenance audits in a real exact child, never the supplied parent store, and confirms child exit',async t=>{
 const {store}=await fixture(t),{RunHistoryMaintenance}=await maintenance();await addRun(store,'old');
 let parentAudits=0;store.cleanupHistory=async()=>{parentAudits++;throw new Error('parent audit must not execute');};
 const manager=new RunHistoryMaintenance({runRoot:store.root});manager.schedule(store);await manager.settle();
 const status=await manager.status();assert.equal(parentAudits,0);assert.equal(status.outcome,'succeeded');
 assert.equal(status.audit.examined,1);assert.equal(status.audit.deleted_count,1);
 assert(Number.isSafeInteger(status.worker_pid));assert.notEqual(status.worker_pid,process.pid);
 assert.throws(()=>process.kill(status.worker_pid,0),{code:'ESRCH'});assert.equal(status.owner_token,undefined);
 await assert.rejects(lstat(join(store.root,'.run-locks','.history-maintenance','.writer.lock')),{code:'ENOENT'});
 manager.schedule(store);await manager.settle();assert.equal((await manager.status()).job_id,status.job_id);await manager.close();
});

test('real child overlaps foreground Run progress and peer coalescing without weakening audit freshness',async t=>{
 const {root,store}=await fixture(t),{RunHistoryMaintenance,launchHistoryWorker}=await maintenance();
 await addRun(store,'foreground');let parentAudits=0;
 store.cleanupHistory=async()=>{parentAudits++;throw new Error('parent audit must not execute');};
 const entered=join(root,'read-entered'),gate=join(root,'read-release'),fixtureWorker=join(root,'fixture-worker.mjs');
 // Child-only test DI pauses before real read admission. The production worker
 // and full cleanup algorithm still execute; a foreground mutation invalidates
 // the captured epoch and must be revalidated before any deletion commit.
 await writeFile(fixtureWorker,`import {WorkflowRunStore} from ${JSON.stringify(new URL('../lib/workflow-run-store.mjs',import.meta.url).href)};
  import {writeFile,readFile} from 'node:fs/promises';
  const original=WorkflowRunStore.prototype.readHistoryMetadataBatch;let paused=false;
  WorkflowRunStore.prototype.readHistoryMetadataBatch=async function(...args){if(!paused){paused=true;await writeFile(${JSON.stringify(entered)},'entered');
   for(;;){try{await readFile(${JSON.stringify(gate)});break;}catch(error){if(error.code!=='ENOENT')throw error;await new Promise(r=>setTimeout(r,10));}}
  }return Reflect.apply(original,this,args);};
  await import(${JSON.stringify(new URL('../lib/run-history-maintenance-worker.mjs',import.meta.url).href)});`);
 const manager=new RunHistoryMaintenance({runRoot:store.root,launchWorker:options=>launchHistoryWorker({...options,workerURL:pathToFileURL(fixtureWorker)})});
 manager.schedule(store);
 for(let attempts=0;;attempts++){try{await readFile(entered);break;}catch(error){if(error.code!=='ENOENT')throw error;assert(attempts<500,'real child did not enter cleanup read');await new Promise(r=>setTimeout(r,10));}}
 const pending=await manager.status();assert.notEqual(pending.worker_pid,process.pid);
 assert.doesNotThrow(()=>process.kill(pending.worker_pid,0));
 const peer=new RunHistoryMaintenance({runRoot:store.root});peer.schedule(store);await peer.settle();
 assert.equal((await peer.status()).job_id,pending.job_id);
 try{
  await store.mutate('foreground','pause',state=>{state.status='interrupted';state.fixture_progress=true;});
  assert.equal((await store.read('foreground')).state.fixture_progress,true);
 }finally{await writeFile(gate,'release');await manager.settle();}
 assert.equal(parentAudits,0);
 assert.equal((await store.read('foreground')).state.status,'interrupted');
 assert.equal((await manager.status()).audit.preserved_count,1);await peer.close();await manager.close();
});

test('confirmed real worker abort leaves explicit cancellation without latching future audit failure',async t=>{
 const {store}=await fixture(t),{RunHistoryMaintenance,launchHistoryWorker}=await maintenance();let manager;
 manager=new RunHistoryMaintenance({runRoot:store.root,launchWorker:options=>launchHistoryWorker({...options,onReady:async pid=>{
  await options.onReady(pid);manager.controller.abort();
 }})});manager.schedule(store);await manager.settle();await manager.close();
 const status=await manager.status();assert.equal(status.outcome,'cancelled');assert.equal(status.error.code,'RUN_HISTORY_CANCELLED');
 assert.throws(()=>process.kill(status.worker_pid,0),{code:'ESRCH'});
 await assert.rejects(lstat(join(store.root,'.run-locks','.history-maintenance','diagnostic.json')),{code:'ENOENT'});
 const peer=new RunHistoryMaintenance({runRoot:store.root});peer.schedule(store);await peer.settle();
 assert.equal((await peer.status()).outcome,'succeeded');assert.notEqual((await peer.status()).job_id,status.job_id);await peer.close();
});

test('unexpected cancellation remains a durable failure rather than a verified shutdown',async t=>{
 const {store}=await fixture(t),{RunHistoryMaintenance}=await maintenance();
 const manager=new RunHistoryMaintenance({runRoot:store.root,launchWorker:async()=>{
  throw Object.assign(new Error('unexpected cancellation'),{code:'RUN_HISTORY_CANCELLED',worker_quiescent:true});
 }});manager.schedule(store);await assert.rejects(manager.settle(),{code:'RUN_HISTORY_CANCELLED'});
 assert.equal((await manager.status()).outcome,'failed');
 assert.equal(JSON.parse(await readFile(join(store.root,'.run-locks','.history-maintenance','diagnostic.json'))).error.code,'RUN_HISTORY_CANCELLED');
});

test('real maintenance worker retains corrupt resource evidence and original diagnostic',async t=>{
 const {store}=await fixture(t),{RunHistoryMaintenance}=await maintenance();const bytes=Buffer.from('exact pinned resource'),sha256=digest(bytes);
 const pins={resources:[{path:'resource.txt',sha256,bytes:bytes.length}],root:{workflow:{id:'flow',nodes:[],edges:[]}}};
 await store.create('corrupt-resource',pins,new Map([[sha256,bytes]]),{schema_version:1,run_id:'corrupt-resource',workflow_id:'flow',status:'succeeded',
  pins_hash:digest(canonicalJSON(pins)),created_at:'2026-01-01T00:00:00.000Z',updated_at:'2026-01-01T00:00:00.000Z',nodes:{},parallel:{}});
 await writeFile(join(store.directory('corrupt-resource'),'objects',sha256),'tampered');
 const manager=new RunHistoryMaintenance({runRoot:store.root});manager.schedule(store);
 await assert.rejects(manager.settle(),{code:'RUN_RESOURCE_CORRUPT'});assert.equal((await manager.status()).error.code,'RUN_RESOURCE_CORRUPT');
 assert((await lstat(store.directory('corrupt-resource'))).isDirectory());
 await assert.rejects(manager.close(),{code:'RUN_RESOURCE_CORRUPT'});
});

test('repeated real child handshake fails visibly and confirms exact process shutdown',async t=>{
 const {root,store}=await fixture(t),{RunHistoryMaintenance,launchHistoryWorker}=await maintenance();
 const worker=join(root,'duplicate-handshake.mjs');
 await writeFile(worker,`const send=process.send.bind(process);process.send=(message,callback)=>{
  if(message.type==='ready')send(message);return send(message,callback);};
  await import(${JSON.stringify(new URL('../lib/run-history-maintenance-worker.mjs',import.meta.url).href)});`);
 const manager=new RunHistoryMaintenance({runRoot:store.root,launchWorker:options=>launchHistoryWorker({...options,workerURL:pathToFileURL(worker)})});
 manager.schedule(store);await assert.rejects(manager.settle(),{code:'RUN_HISTORY_WORKER_PROTOCOL'});
 const status=await manager.status();assert.equal(status.outcome,'failed');assert.equal(status.error.code,'RUN_HISTORY_WORKER_PROTOCOL');
 assert.throws(()=>process.kill(status.worker_pid,0),{code:'ESRCH'});await assert.rejects(manager.close(),{code:'RUN_HISTORY_WORKER_PROTOCOL'});
});

test('real child stop pending retains exact identities until admitted checks settle',async t=>{
 const {root,store}=await fixture(t),{RunHistoryMaintenance,launchHistoryWorker}=await maintenance();await addRun(store,'preserve');
 const entered=join(root,'read-entered'),gate=join(root,'read-release'),worker=join(root,'paused-read.mjs');
 await writeFile(worker,`import {WorkflowRunStore} from ${JSON.stringify(new URL('../lib/workflow-run-store.mjs',import.meta.url).href)};
  import {writeFile,readFile} from 'node:fs/promises';const read=WorkflowRunStore.prototype.readHistoryMetadataBatch;
  WorkflowRunStore.prototype.readHistoryMetadataBatch=async function(...args){await writeFile(${JSON.stringify(entered)},'entered');
   for(;;){try{await readFile(${JSON.stringify(gate)});break;}catch(error){if(error.code!=='ENOENT')throw error;await new Promise(r=>setTimeout(r,10));}}
   return Reflect.apply(read,this,args);};await import(${JSON.stringify(new URL('../lib/run-history-maintenance-worker.mjs',import.meta.url).href)});`);
 const manager=new RunHistoryMaintenance({runRoot:store.root,settlementMs:25,launchWorker:options=>launchHistoryWorker({...options,workerURL:pathToFileURL(worker)})});
 manager.schedule(store);
 for(let attempts=0;;attempts++){try{await readFile(entered);break;}catch(error){if(error.code!=='ENOENT')throw error;assert(attempts<500);await new Promise(r=>setTimeout(r,10));}}
 try{
  await assert.rejects(manager.close(),{code:'RUN_HISTORY_MAINTENANCE_STOP_PENDING'});
  const pending=await manager.status();assert.equal(pending.outcome,'stop_pending');assert.notEqual(pending.worker_pid,process.pid);
  assert.doesNotThrow(()=>process.kill(pending.worker_pid,0));
  assert((await lstat(join(store.root,'.run-locks','.history-maintenance','.writer.lock'))).isFile());
 }finally{await writeFile(gate,'release');await manager.settle();}
 const cancelledStatus=await manager.status();assert.equal(cancelledStatus.outcome,'cancelled');
 assert.throws(()=>process.kill(cancelledStatus.worker_pid,0),{code:'ESRCH'});
 assert((await lstat(store.directory('preserve'))).isDirectory());
 await assert.rejects(lstat(join(store.root,'.run-locks','.history-maintenance','diagnostic.json')),{code:'ENOENT'});
});

async function legacyCancellation(t){
 const {store}=await fixture(t),directory=join(store.root,'.run-locks','.history-maintenance');await mkdir(directory);
 const saved={schema_version:1,job_id:'00000000-0000-4000-8000-000000000021',owner_token:'00000000-0000-4000-8000-000000000022',
  owner_pid:2147483647,created_at:1,due_at:60001,finished_at:2,phase:'settled',outcome:'cancelled',
  error:{code:'RUN_HISTORY_CANCELLED',message:'Known legacy cancellation'}};
 const observed={schema_version:1,at:3,error:{code:'RUN_HISTORY_CANCELLED',message:'Known legacy cancellation'}};
 const savedBytes=canonicalJSON(saved)+'\n',observedBytes=canonicalJSON(observed)+'\n';
 await writeFile(join(directory,'receipt.json'),savedBytes);await writeFile(join(directory,'diagnostic.json'),observedBytes);
 return {store,directory,saved,savedBytes,observedBytes,args:{runRoot:store.root,jobId:saved.job_id,ownerPid:saved.owner_pid,
  receiptSha256:digest(savedBytes),diagnosticSha256:digest(observedBytes)}};
}
test('explicit exact recovery archives legacy no-worker cancellation and preserves receipt bytes',async t=>{
 const f=await legacyCancellation(t),{archiveCancelledHistoryDiagnostic}=await maintenance();
 const result=await archiveCancelledHistoryDiagnostic(f.args);
 assert.equal((await readFile(result.archive_path)).toString(),f.observedBytes);
 assert.equal((await readFile(join(f.directory,'receipt.json'))).toString(),f.savedBytes);
 await assert.rejects(lstat(join(f.directory,'diagnostic.json')),{code:'ENOENT'});
 await assert.rejects(lstat(join(f.directory,'.writer.lock')),{code:'ENOENT'});
});
test('recovery refuses unknown fault, changed hash, live process and conflicting claim without clearing evidence',async t=>{
 const {archiveCancelledHistoryDiagnostic}=await maintenance();
 for(const variant of ['fault','hash','live','claim']){
  const f=await legacyCancellation(t);
  if(variant==='fault')await writeFile(join(f.directory,'diagnostic.json'),canonicalJSON({schema_version:1,error:{code:'RUN_PINS_CORRUPT',message:'Unknown fault'}}));
  if(variant==='hash')f.args.diagnosticSha256='0'.repeat(64);
  if(variant==='live'){
   f.saved.owner_pid=process.pid;f.args.ownerPid=process.pid;
   const bytes=canonicalJSON(f.saved);await writeFile(join(f.directory,'receipt.json'),bytes);f.args.receiptSha256=digest(bytes);
  }
  if(variant==='claim')await writeFile(join(f.directory,'.writer.lock'),'retain exact foreign claim');
  await assert.rejects(archiveCancelledHistoryDiagnostic(f.args),{code:variant==='fault'?'RUN_HISTORY_RECOVERY_IDENTITY':variant==='hash'?'RUN_HISTORY_RECOVERY_HASH':variant==='live'?'RUN_HISTORY_RECOVERY_OWNER_LIVE':'EEXIST'});
  assert((await lstat(join(f.directory,'diagnostic.json'))).isFile());
  if(variant==='claim')assert.equal((await readFile(join(f.directory,'.writer.lock'))).toString(),'retain exact foreign claim');
  else await assert.rejects(lstat(join(f.directory,'.writer.lock')),{code:'ENOENT'});
 }
});
test('concurrent explicit recoveries permit one exact archive and leave no recovery claim',async t=>{
 const f=await legacyCancellation(t),{archiveCancelledHistoryDiagnostic}=await maintenance();
 const outcomes=await Promise.allSettled([archiveCancelledHistoryDiagnostic(f.args),archiveCancelledHistoryDiagnostic(f.args)]);
 assert.equal(outcomes.filter(value=>value.status==='fulfilled').length,1);assert.equal(outcomes.filter(value=>value.status==='rejected').length,1);
 assert.equal((await readFile(join(f.directory,'receipt.json'))).toString(),f.savedBytes);
 await assert.rejects(lstat(join(f.directory,'.writer.lock')),{code:'ENOENT'});
});
test('a paused observer reports recovered legacy failure without resurrecting its stale diagnostic',async t=>{
 const f=await legacyCancellation(t),{archiveCancelledHistoryDiagnostic,RunHistoryMaintenance}=await maintenance();
 const entered=latch(),proceed=latch();let paused=false;
 const readRecord=async(path,{optional=false}={})=>{
  let value;try{value=JSON.parse(await readFile(path));}catch(error){if(optional&&error.code==='ENOENT')return null;throw error;}
  if(path===join(f.directory,'diagnostic.json')&&!paused){paused=true;entered.release();await proceed.promise;}return value;
 };
 const observer=new RunHistoryMaintenance({runRoot:f.store.root,readRecord});observer.schedule(f.store);await entered.promise;
 await archiveCancelledHistoryDiagnostic(f.args);proceed.release();
 await assert.rejects(observer.settle(),{code:'RUN_HISTORY_CANCELLED'});
 await assert.rejects(observer.close(),{code:'RUN_HISTORY_CANCELLED'});
 await assert.rejects(lstat(join(f.directory,'diagnostic.json')),{code:'ENOENT'});
 const fresh=new RunHistoryMaintenance({runRoot:f.store.root});fresh.schedule(f.store);await fresh.settle();
 assert.equal((await fresh.status()).outcome,'succeeded');await fresh.close();
});
test('observer recaptures exact recovery side receipt after its tagged claim is released',async t=>{
 const f=await legacyCancellation(t),{archiveCancelledHistoryDiagnostic,RunHistoryMaintenance}=await maintenance();
 const claimed=latch(),allowRecovery=latch(),captured=latch(),allowObserver=latch();let receiptReads=0,paused=false;
 const readJSON=async(path,{optional=false}={})=>{try{return JSON.parse(await readFile(path));}catch(error){if(optional&&error.code==='ENOENT')return null;throw error;}};
 const recovery=archiveCancelledHistoryDiagnostic({...f.args,readRecord:async(path,options)=>{
  const value=await readJSON(path,options);if(path===join(f.directory,'receipt.json')&&++receiptReads===2){claimed.release();await allowRecovery.promise;}return value;
 }});await claimed.promise;
 const observer=new RunHistoryMaintenance({runRoot:f.store.root,readRecord:async(path,options)=>{
  const value=await readJSON(path,options);if(path===join(f.directory,'.writer.lock')&&!paused){paused=true;captured.release();await allowObserver.promise;}return value;
 }});
 const status=observer.status();await captured.promise;allowRecovery.release();const recovered=await recovery;allowObserver.release();
 const observed=await status;assert.equal(observed.kind,'cancelled_diagnostic_recovery');assert.equal(observed.outcome,'succeeded');
 assert.equal(observed.error,undefined);assert.equal(observed.owner_token,undefined);
 assert.equal((await readFile(join(f.directory,'receipt.json'))).toString(),f.savedBytes);
 const side=JSON.parse(await readFile(recovered.recovery_receipt_path));assert.equal(side.job_id,observed.job_id);assert.equal(side.due_at,side.created_at);
 const fresh=new RunHistoryMaintenance({runRoot:f.store.root});fresh.schedule(f.store);await fresh.settle();
 assert.equal((await fresh.status()).audit.examined,0);await fresh.close();await observer.close();
});

test('Host abort after real child confirmed success preserves committed census and audit cooldown',async t=>{
 const {store}=await fixture(t),{RunHistoryMaintenance,launchHistoryWorker}=await maintenance();await addRun(store,'committed');let manager;
 manager=new RunHistoryMaintenance({runRoot:store.root,launchWorker:async options=>{
  const result=await launchHistoryWorker(options);manager.controller.abort();return result;
 }});manager.schedule(store);await manager.settle();await manager.close();
 const status=await manager.status();assert.equal(status.outcome,'succeeded');assert.equal(status.audit.deleted_count,1);assert(status.due_at>Date.now());
 assert.throws(()=>process.kill(status.worker_pid,0),{code:'ESRCH'});await assert.rejects(lstat(store.directory('committed')),{code:'ENOENT'});
 const peer=new RunHistoryMaintenance({runRoot:store.root});peer.schedule(store);await peer.settle();assert.equal((await peer.status()).job_id,status.job_id);await peer.close();
});

test('real child abort after cleanup commit preserves successful terminal instead of inventing cancellation',async t=>{
 const {root,store}=await fixture(t),{RunHistoryMaintenance,launchHistoryWorker}=await maintenance();await addRun(store,'committed');
 const committed=join(root,'committed'),cancelObserved=join(root,'cancel-observed'),release=join(root,'release'),worker=join(root,'committed-worker.mjs');
 await writeFile(worker,`import {WorkflowRunStore} from ${JSON.stringify(new URL('../lib/workflow-run-store.mjs',import.meta.url).href)};
  import {writeFile,readFile} from 'node:fs/promises';
  const cleanup=WorkflowRunStore.prototype.cleanupHistory;
  WorkflowRunStore.prototype.cleanupHistory=async function(...args){const result=await Reflect.apply(cleanup,this,args);
   await writeFile(${JSON.stringify(committed)},'commit succeeded');
   for(;;){try{await readFile(${JSON.stringify(release)});break;}catch(error){if(error.code!=='ENOENT')throw error;await new Promise(r=>setTimeout(r,10));}}
   return result;};await import(${JSON.stringify(new URL('../lib/run-history-maintenance-worker.mjs',import.meta.url).href)});
  process.on('message',message=>{if(message.type==='cancel')writeFile(${JSON.stringify(cancelObserved)},'cancel observed').catch(error=>{throw error;});});`);
 const manager=new RunHistoryMaintenance({runRoot:store.root,launchWorker:options=>launchHistoryWorker({...options,workerURL:pathToFileURL(worker)})});manager.schedule(store);
 const waitFile=async path=>{for(let count=0;;count++){try{await readFile(path);return;}catch(error){if(error.code!=='ENOENT')throw error;assert(count<500);await new Promise(r=>setTimeout(r,10));}}};
 try{
  await waitFile(committed);await assert.rejects(lstat(store.directory('committed')),{code:'ENOENT'});
  manager.controller.abort();await waitFile(cancelObserved);
 }finally{await writeFile(release,'release');await manager.settle();await manager.close();}
 const status=await manager.status();assert.equal(status.outcome,'succeeded');assert.equal(status.audit.deleted_count,1);assert(status.due_at>Date.now());
 assert.throws(()=>process.kill(status.worker_pid,0),{code:'ESRCH'});
 await assert.rejects(lstat(join(store.root,'.run-locks','.history-maintenance','diagnostic.json')),{code:'ENOENT'});
});

async function contendedChild(t,{onAdmission=admissionTrace,workerPrelude='',workerPostlude=''}={}){
 const {root,store}=await fixture(t),{launchHistoryWorker}=await maintenance();
 const acquired=latch(),release=latch(),observed=latch(),admission=new WorkflowStore(join(store.root,'.run-locks','.store-operation'));
 const held=admission.withRunAdmission(async()=>{acquired.release();await release.promise;},{onWait:()=>{}});await acquired.promise;
 let workerURL;
 if(workerPrelude||workerPostlude){const worker=join(root,'diagnostic-worker.mjs');await writeFile(worker,`${workerPrelude}\nawait import(${JSON.stringify(new URL('../lib/run-history-maintenance-worker.mjs',import.meta.url).href)});\n${workerPostlude}`);workerURL=pathToFileURL(worker);}
 const controller=new AbortController(),owner={job_id:randomUUID(),owner_token:randomUUID(),owner_pid:process.pid,created_at:Date.now()};
 const phases=[];let childPid;
 const task=launchHistoryWorker({runRoot:store.root,owner,signal:controller.signal,onReady:pid=>{childPid=pid;},workerURL,
  onAdmission:async detail=>{phases.push(detail.phase);observed.release();return onAdmission(detail);}});
 void task.catch(()=>{});
 void task.then(()=>observed.release(),()=>observed.release());
 try{await observed.promise;}finally{release.release();await held;}
 return {task,phases,childPid,store};
}

test('actual child source admission diagnostics retain default Host logs and successful terminal',async t=>{
 const logs=[],original=console.error;console.error=value=>logs.push(value);
 try{
  const f=await contendedChild(t);assert.deepEqual(await f.task,{examined:0,deleted_count:0,preserved_count:0});
  assert(f.childPid!==process.pid);assert.throws(()=>process.kill(f.childPid,0),{code:'ESRCH'});
  assert(f.phases.includes('waiting'));assert(f.phases.includes('acquired'));assert.equal(logs.length,f.phases.length);
  for(const line of logs){assert(line.startsWith('[workflow-run-admission] '));assert(!line.includes('owner_token'));}
 }finally{console.error=original;}
});

test('real child awaits asynchronous diagnostic observers before ACK and terminal',async t=>{
 const entered=latch(),release=latch();let settled=false;
 const pending=contendedChild(t,{onAdmission:async detail=>{if(detail.phase==='waiting'){entered.release();await release.promise;}}});
 await entered.promise;const f=await pending;const task=f.task.finally(()=>settled=true);void task.catch(()=>{});
 await new Promise(r=>setTimeout(r,30));assert.equal(settled,false);release.release();await task;
 assert(f.phases.includes('acquired'));
});

test('sync and async admission observer failures remain visible after exact child quiescence',async t=>{
 for(const onAdmission of [()=>{throw Object.assign(new Error('observer private body'),{code:'NEUTRAL_OBSERVER'});},async()=>{throw Object.assign(new Error('observer private body'),{code:'NEUTRAL_OBSERVER'});}]){
  const f=await contendedChild(t,{onAdmission});
  await assert.rejects(f.task,error=>error.code==='RUN_HISTORY_WORKER_OBSERVER'&&error.cause.code==='NEUTRAL_OBSERVER'&&error.worker_quiescent===true&&error.worker_cancelled===false);
  assert.throws(()=>process.kill(f.childPid,0),{code:'ESRCH'});
 }
});

test('real child diagnostic send failure and ACK channel loss cannot become successful audits',async t=>{
 for(const mode of ['send_failure','disconnect','disconnect_after_ack']){
  const workerPrelude=mode==='disconnect_after_ack'?`const originalSend=process.send.bind(process);let delivery;
   process.send=(message,callback)=>{
    if(message.type==='admission'){delivery=callback;return originalSend(message,error=>{if(error){delivery=null;callback(error);}});}
    return originalSend(message,callback);
   };
  `:`const originalSend=process.send.bind(process);process.send=(message,callback)=>{
   if(message.type==='admission'){
    ${mode==='send_failure'?"callback(Object.assign(new Error('neutral send failure'),{code:'NEUTRAL_SEND'}));return false;":"return originalSend(message,error=>{process.disconnect();callback(error);});"}
   }return originalSend(message,callback);
  };`;
  const workerPostlude=mode==='disconnect_after_ack'?`process.on('message',message=>{if(message.type==='admission_ack'&&delivery){const callback=delivery;delivery=null;process.disconnect();callback();}});`:'';
  const f=await contendedChild(t,{workerPrelude,workerPostlude,onAdmission:()=>{}});
  await assert.rejects(f.task,error=>error.code==='RUN_HISTORY_WORKER_IPC'&&error.worker_quiescent===true&&error.worker_cancelled===false);
  assert.throws(()=>process.kill(f.childPid,0),{code:'ESRCH'});
 }
});

test('unknown actual child stderr still fails despite supported diagnostic transport',async t=>{
 const f=await contendedChild(t,{workerPrelude:"process.stderr.write('unknown neutral stderr\\n');",onAdmission:()=>{}});
 await assert.rejects(f.task,error=>error.code==='RUN_HISTORY_WORKER_STDERR'&&error.stderr_bytes>0&&error.worker_quiescent===true&&error.worker_cancelled===false);
 assert.throws(()=>process.kill(f.childPid,0),{code:'ESRCH'});
});

async function admissionWithWait(t,observer){
 const {root}=await fixture(t),admissionRoot=join(root,'.run-locks','.store-operation');await mkdir(admissionRoot,{recursive:true});
 const lock=join(admissionRoot,'.writer.lock');
 await writeFile(lock,canonicalJSON({pid:process.pid,token:randomUUID(),created_at:new Date().toISOString()}));
 return {admissionRoot,run:options=>new WorkflowStore(admissionRoot).withRunAdmission(()=>true,options),observer:async detail=>{await observer(detail);if(detail.phase==='waiting')await unlink(lock);}};
}

test('scoped admission observers isolate concurrent roots and preserve explicit overrides',async t=>{
 const a=[],b=[],override=[];
 const first=await admissionWithWait(t,detail=>a.push(detail.phase)),second=await admissionWithWait(t,detail=>b.push(detail.phase));
 await Promise.all([withRunAdmissionObserver({admissionRoot:first.admissionRoot,onWait:first.observer},()=>first.run()),
  withRunAdmissionObserver({admissionRoot:second.admissionRoot,onWait:second.observer},()=>second.run())]);
 assert.deepEqual(a,['waiting','acquired']);assert.deepEqual(b,['waiting','acquired']);
 for(const asyncCallback of [false,true]){
  const explicit=await admissionWithWait(t,detail=>override.push(detail.phase));
  await withRunAdmissionObserver({admissionRoot:explicit.admissionRoot,onWait:()=>assert.fail('explicit override must win')},
   ()=>explicit.run({onWait:asyncCallback?explicit.observer:detail=>explicit.observer(detail)}));
 }
 assert.deepEqual(override,['waiting','acquired','waiting','acquired']);
});

test('different-root and detached expired admission scopes preserve ordinary default logging',async t=>{
 const logs=[],original=console.error;console.error=value=>logs.push(value);
 try{
  const first=await admissionWithWait(t,()=>{}),other=await admissionWithWait(t,()=>{});
  // The default observer still runs; release this exact fixture lock when it logs.
  const defaultRun=async fixture=>{
   const previous=console.error;console.error=value=>{previous(value);const detail=JSON.parse(value.slice('[workflow-run-admission] '.length));if(detail.phase==='waiting')return unlink(join(fixture.admissionRoot,'.writer.lock'));};
   try{return await fixture.run();}finally{console.error=previous;}
  };
  await withRunAdmissionObserver({admissionRoot:first.admissionRoot,onWait:()=>assert.fail('scope must match root')},()=>defaultRun(other));
  const release=latch();let detached;
  await withRunAdmissionObserver({admissionRoot:first.admissionRoot,onWait:()=>assert.fail('expired scope must not capture')},()=>{detached=release.promise.then(()=>defaultRun(first));});
  release.release();await detached;assert.equal(logs.length,4);
 }finally{console.error=original;}
});

test('actual child rejects a mismatched diagnostic ACK sequence without hiding the protocol failure',async t=>{
 const f=await contendedChild(t,{onAdmission:()=>{},workerPrelude:`const originalOn=process.on.bind(process);process.on=(event,listener)=>event==='message'
  ?originalOn(event,message=>listener(message.type==='admission_ack'?{...message,sequence:message.sequence+1}:message)):originalOn(event,listener);`});
 await assert.rejects(f.task,error=>error.code==='RUN_HISTORY_WORKER_PROTOCOL'&&error.worker_quiescent===true&&error.worker_cancelled===false);
 assert.throws(()=>process.kill(f.childPid,0),{code:'ESRCH'});
});

test('typed admission metadata requires bounded exact-root paths and never transports arbitrary bodies',async t=>{
 const {store}=await fixture(t),{requireHistoryAdmissionDiagnostic}=await maintenance();
 const valid={phase:'waiting',lock_path:join(store.root,'.run-locks','.store-operation','.writer.lock'),owner_pid:process.pid,created_at:new Date().toISOString(),waited_ms:0};
 assert.equal(requireHistoryAdmissionDiagnostic(valid,store.root),valid);
 for(const invalid of [{...valid,lock_path:join(store.root,'foreign','.writer.lock')},{...valid,output:'private body'},{...valid,owner_pid:0},{phase:'waiting'},{...valid,created_at:'x'.repeat(9000)}]){
  assert.throws(()=>requireHistoryAdmissionDiagnostic(invalid,store.root),{code:'RUN_HISTORY_WORKER_DIAGNOSTIC'});
 }
});

test('actual source admission telemetry has ACK backpressure without a cumulative diagnostic cap',async t=>{
 const {root,store}=await fixture(t),{launchHistoryWorker}=await maintenance(),worker=join(root,'many-diagnostics-worker.mjs');
 const admission=join(store.root,'.run-locks','.store-operation'),lock=join(admission,'.writer.lock');
 await mkdir(admission,{recursive:true});
 await writeFile(worker,`import {WorkflowRunStore} from ${JSON.stringify(new URL('../lib/workflow-run-store.mjs',import.meta.url).href)};
  import {WorkflowStore} from ${JSON.stringify(new URL('../lib/workflow-store.mjs',import.meta.url).href)};
  import {writeFile} from 'node:fs/promises';import {randomUUID} from 'node:crypto';
  const cleanup=WorkflowRunStore.prototype.cleanupHistory;WorkflowRunStore.prototype.cleanupHistory=async function(...args){
   for(let i=0;i<70;i++){
    await writeFile(${JSON.stringify(lock)},JSON.stringify({pid:process.pid,token:randomUUID(),created_at:new Date().toISOString()}),{flag:'wx'});
    await new WorkflowStore(${JSON.stringify(admission)}).withRunAdmission(()=>{});
   }return Reflect.apply(cleanup,this,args);
  };await import(${JSON.stringify(new URL('../lib/run-history-maintenance-worker.mjs',import.meta.url).href)});`);
 let count=0,inFlight=0,maxInFlight=0,childPid;
 const audit=await launchHistoryWorker({runRoot:store.root,owner:{job_id:randomUUID(),owner_token:randomUUID(),owner_pid:process.pid,created_at:Date.now()},
  signal:new AbortController().signal,onReady:pid=>{childPid=pid;},workerURL:pathToFileURL(worker),onAdmission:async detail=>{
   count++;maxInFlight=Math.max(maxInFlight,++inFlight);
   try{if(detail.phase==='waiting')await unlink(lock);}finally{inFlight--;}
  }});
 assert.deepEqual(audit,{examined:0,deleted_count:0,preserved_count:0});assert.equal(count,140);assert.equal(maxInFlight,1);
 assert.throws(()=>process.kill(childPid,0),{code:'ESRCH'});
});

test('actual worker open_failed admission diagnostic preserves denied-open cause through typed IPC',async t=>{
 const observed=[];
 const f=await contendedChild(t,{onAdmission:detail=>observed.push(detail),workerPrelude:`import fs from 'node:fs/promises';import {syncBuiltinESMExports} from 'node:module';
  const originalOpen=fs.open;fs.open=async(path,flags,...args)=>{
   if(flags==='wx'&&typeof path==='string'&&path.endsWith('.store-operation/.writer.lock')||flags==='wx'&&typeof path==='string'&&path.endsWith('.store-operation\\\\.writer.lock'))
    throw Object.assign(new Error('neutral denied-open private body'),{code:'EPERM',errno:-4048,syscall:'open',path});
   return originalOpen(path,flags,...args);
  };syncBuiltinESMExports();`});
 await assert.rejects(f.task,error=>error.code==='RUN_STORE_ADMISSION_OPEN_FAILED'&&error.cause.code==='EPERM'&&error.worker_quiescent===true&&error.worker_cancelled===false);
 assert.equal(observed.length,1);assert.equal(observed[0].phase,'open_failed');assert.equal(observed[0].open_error_code,'EPERM');assert.equal(observed[0].open_errno,-4048);
 assert(!Object.keys(observed[0]).some(key=>/token|body|prompt|output/.test(key)));assert.throws(()=>process.kill(f.childPid,0),{code:'ESRCH'});
});

test('real maintenance child retirement deletion faults persist exact bounded locators without touching successors',async t=>{
 const {RunHistoryMaintenance,launchHistoryWorker}=await maintenance();
 for(const kind of ['writer','ticket']){
  const {root,store}=await fixture(t),worker=join(root,'retirement-fault-worker.mjs'),stats=join(root,'stats.json');await addRun(store,'retained');
  await writeFile(worker,`import fs from 'node:fs/promises';import {syncBuiltinESMExports} from 'node:module';import {dirname,join} from 'node:path';import {randomUUID} from 'node:crypto';
   const originalUnlink=fs.unlink;let callbacks=0,attempts=0;
   fs.unlink=async path=>{
    const normalized=String(path).replaceAll('\\\\','/');
    if(normalized.includes('/.store-operation/')&&normalized.includes('/retired-owner-')&&normalized.endsWith('/record.json')&&normalized.includes('/.admission-queue/')===${kind==='ticket'}){
     attempts++;const canonical=${kind==='ticket'?"join(dirname(dirname(dirname(path))), 'ticket-'+randomUUID()+'.json')":"join(dirname(dirname(dirname(path))),'.writer.lock')"};
     await fs.writeFile(canonical,JSON.stringify({pid:process.pid,token:randomUUID(),created_at:new Date().toISOString()}),{flag:'wx'});
     await fs.writeFile(${JSON.stringify(stats)},JSON.stringify({callbacks,attempts,canonical}));
     throw Object.assign(new Error('private retirement failure body'),{code:'EPERM',errno:-4048,syscall:'unlink'});
    }return originalUnlink(path);
   };syncBuiltinESMExports();const {WorkflowStore}=await import(${JSON.stringify(new URL('../lib/workflow-store.mjs',import.meta.url).href)});
   const originalAdmission=WorkflowStore.prototype.withRunAdmission;WorkflowStore.prototype.withRunAdmission=function(action,...args){
    return Reflect.apply(originalAdmission,this,[(...a)=>{callbacks++;return action(...a);},...args]);
   };await import(${JSON.stringify(new URL('../lib/run-history-maintenance-worker.mjs',import.meta.url).href)});`);
  const manager=new RunHistoryMaintenance({runRoot:store.root,launchWorker:options=>launchHistoryWorker({...options,workerURL:pathToFileURL(worker)})});manager.schedule(store);
  await assert.rejects(manager.settle());await assert.rejects(manager.close());
  const status=await manager.status();assert.equal(status.outcome,'failed');assert.equal(status.error.retirements.length,1);
  const receipt=status.error.retirements[0],actual=JSON.parse(await readFile(stats));
  assert.equal(actual.attempts,1);assert.equal(actual.callbacks,kind==='ticket'?0:1);
  assert.equal(receipt.phase,'retirement_delete');assert.equal(receipt.retired,true);assert.equal(receipt.deleted,false);
  assert.equal(receipt.cause_code,'EPERM');assert.equal(receipt.cause_errno,-4048);assert.equal(receipt.owner_pid,status.worker_pid);
  assert(receipt.canonical_path.startsWith('.run-locks/.store-operation/'));assert(!receipt.retired_path.includes('..'));
  const retained=JSON.parse(await readFile(join(store.root,receipt.retired_path))),successor=JSON.parse(await readFile(actual.canonical));
  assert.equal(retained.pid,status.worker_pid);assert.equal(successor.pid,status.worker_pid);
  assert(!JSON.stringify(status).includes(retained.token));assert(!JSON.stringify(status).includes(successor.token));assert(!JSON.stringify(status).includes('private retirement failure body'));
  assert((await lstat(store.directory('retained'))).isDirectory());assert.throws(()=>process.kill(status.worker_pid,0),{code:'ESRCH'});
  const durable=JSON.parse(await readFile(join(store.root,'.run-locks','.history-maintenance','diagnostic.json')));
  assert.deepEqual(durable.error.retirements,status.error.retirements);
 }
});

async function genuineRetirementFault(store,{canonicalPath='.run-locks/.store-operation/.writer.lock',onRetired}={}){
 const {retireOwnedFile}=await import('../lib/owned-file-retirement.mjs');
 const canonical=join(store.root,canonicalPath),directory=canonical.slice(0,canonical.lastIndexOf(process.platform==='win32'?'\\':'/'));
 await mkdir(directory,{recursive:true});await writeFile(canonical,JSON.stringify({pid:process.pid,secret:'private ownership body'}));
 let error;try{await retireOwnedFile(canonical,{stagingRoot:join(directory,'.pending'),validate:bytes=>{assert.equal(JSON.parse(bytes).pid,process.pid);return process.pid;},
  onRetired:onRetired??(()=>{throw Object.assign(new Error('private failure body'),{code:'NEUTRAL_RETIREMENT',errno:-7});})});}catch(value){error=value;}
 assert(error);return error;
}

test('nested real retirement provenance retains every receipt while spoofed details and mutations cannot impersonate it',async t=>{
 const {store}=await fixture(t),{diagnostic}=await maintenance(),faults=[];
 for(let i=0;i<6;i++)faults.push(await genuineRetirementFault(store,{canonicalPath:`.run-locks/.store-operation/.admission-queue/ticket-${randomUUID()}.json`}));
 faults[0].details={retirement:{phase:'retirement_delete',original_path:'secret absolute path',retired_path:'secret path',owner_token:'secret authority'}};
 const nested=new AggregateError([new AggregateError([new AggregateError(faults.slice(0,3),'nested')],'nested again'),...faults.slice(3)],'all faults');
 const result=diagnostic(nested,0,store.root);assert.equal(result.retirements.length,6);
 for(const receipt of result.retirements){assert.equal(receipt.cause_code,'NEUTRAL_RETIREMENT');assert.equal(receipt.cause_errno,-7);assert.equal(receipt.owner_pid,process.pid);}
 assert(!JSON.stringify(result).includes('secret'));assert(!JSON.stringify(result).includes('private failure body'));
 const spoof=Object.assign(new Error('private spoof body'),{code:'NEUTRAL_SPOOF',details:{retirement:{...faults[1].details.retirement}},retirements:result.retirements});
 const sanitized=diagnostic(spoof,0,store.root);assert.equal(sanitized.retirements,undefined);assert(!JSON.stringify(sanitized).includes('private spoof body'));
});

test('retirement metadata validation rejects authority fields, escaped or mismatched identities and genuine outside-root provenance',async t=>{
 const {store}=await fixture(t),other=await fixture(t),{diagnostic,requireHistoryRetirementReceipts}=await maintenance();
 const genuine=await genuineRetirementFault(store),valid=diagnostic(genuine,0,store.root).retirements[0];assert.equal(requireHistoryRetirementReceipts([valid],store.root)[0],valid);
 const observed={...valid,cleanup_waited_ms:1000,cleanup_checks:40};assert.equal(requireHistoryRetirementReceipts([observed],store.root)[0],observed);
 for(const key of ['cleanup_waited_ms','cleanup_checks'])for(const value of [-1,1.5,2147483648,'1000',null])
  assert.throws(()=>requireHistoryRetirementReceipts([{...valid,[key]:value}],store.root),{code:'RUN_HISTORY_WORKER_RETIREMENT'});
 for(const value of [{...valid,owner_token:'secret'},{...valid,body:'secret'},{...valid,canonical_path:'../.writer.lock'},{...valid,canonical_path:join(store.root,'.writer.lock')},
  {...valid,retired_path:valid.retired_path.replace('retired-owner-','wrong-')},{...valid,retired_path:valid.retired_path.replace('.store-operation/','.different/')},{...valid,owner_pid:0}]){
  assert.throws(()=>requireHistoryRetirementReceipts([value],store.root),{code:'RUN_HISTORY_WORKER_RETIREMENT'});
 }
 const foreign=await genuineRetirementFault(other.store);assert.throws(()=>diagnostic(foreign,0,store.root),{code:'RUN_HISTORY_WORKER_RETIREMENT'});
});

test('real history child settlement timeout retains original fault and typed cleanup observations',
 {skip:process.platform!=='win32',timeout:5000},async t=>{
 const {root,store}=await fixture(t),{launchHistoryWorker}=await maintenance(),worker=join(root,'settlement-timeout-worker.mjs');
 const observations=join(root,'settlement-observations.json'),faultMessage='Injected exact history retired directory nonempty';
 await writeFile(worker,`import fs from 'node:fs/promises';import {syncBuiltinESMExports} from 'node:module';import {join,dirname} from 'node:path';import assert from 'node:assert/strict';
  import {retireOwnedFile} from ${JSON.stringify(new URL('../lib/owned-file-retirement.mjs',import.meta.url).href)};
  import {WorkflowRunStore} from ${JSON.stringify(new URL('../lib/workflow-run-store.mjs',import.meta.url).href)};
  const remove=fs.rmdir,unlink=fs.unlink,events=[];let pendingRoot,retiredDirectory,dirCalls=0,unlinks=0;
  const fault=Object.assign(new Error(${JSON.stringify(faultMessage)}),{code:'ENOTEMPTY',errno:-4051});
  fs.unlink=async path=>{const result=await unlink(path);if(pendingRoot&&dirname(dirname(path))===pendingRoot){retiredDirectory=dirname(path);unlinks++;}return result;};
  // Keep the real child and filesystem ownership path, but make its optional
  // Windows delete-pending rmdir failure deterministic on this exact directory.
  fs.rmdir=async path=>{if(path!==retiredDirectory)return remove(path);
   if(!dirCalls++)events.push('nonempty_fault');throw fault;};syncBuiltinESMExports();
  WorkflowRunStore.prototype.cleanupHistory=async function(){
   events.push('cleanup_entered');pendingRoot=join(this.root,'.pending');const path=join(this.root,'.writer.lock');await fs.writeFile(path,'exact owner',{flag:'wx'});
   const reader=await fs.open(path,'r'),identity=await reader.stat({bigint:true});let originalError=false;
   try{await retireOwnedFile(path,{stagingRoot:join(this.root,'.pending'),validate:()=>process.pid});assert.fail('Settlement must retain the injected fault');}
   catch(error){assert.equal(error,fault);originalError=true;events.push('settlement_rejected');throw error;}
   finally{assert.equal((await reader.stat({bigint:true})).ino,identity.ino);assert.equal((await reader.readFile()).toString(),'exact owner');
    await reader.close();events.push('reader_closed');await fs.writeFile(${JSON.stringify(observations)},JSON.stringify({events,originalError,dirCalls,unlinks,worker_pid:process.pid}));}
  };await import(${JSON.stringify(new URL('../lib/run-history-maintenance-worker.mjs',import.meta.url).href)});`);
 let childPid;
 await assert.rejects(launchHistoryWorker({runRoot:store.root,owner:{job_id:randomUUID(),owner_token:randomUUID(),owner_pid:process.pid,created_at:Date.now()},
  signal:new AbortController().signal,onReady:pid=>{childPid=pid;},workerURL:pathToFileURL(worker)}),error=>{
  assert.equal(error.code,'ENOTEMPTY');assert.equal(error.worker_quiescent,true);
  assert.equal(error.message_sha256,digest(faultMessage));assert.equal(error.message_bytes,Buffer.byteLength(faultMessage));
  assert.equal(error.retirements.length,1);const receipt=error.retirements[0];
  assert.equal(receipt.phase,'retirement_directory_cleanup');assert.equal(receipt.canonical_path,'.writer.lock');
  assert.equal(receipt.cause_code,'ENOTEMPTY');assert.equal(receipt.cause_errno,-4051);assert.equal(receipt.owner_pid,childPid);
  assert.equal(receipt.retired,true);assert.equal(receipt.deleted,true);assert(receipt.cleanup_waited_ms>=1000);assert(receipt.cleanup_checks>0);return true;
 });
 const observed=JSON.parse(await readFile(observations,'utf8'));
 assert.deepEqual(observed.events,['cleanup_entered','nonempty_fault','settlement_rejected','reader_closed']);
 assert.equal(observed.originalError,true);assert.equal(observed.unlinks,1);assert(observed.dirCalls>=1);assert.equal(observed.worker_pid,childPid);
 assert.throws(()=>process.kill(childPid,0),{code:'ESRCH'});
});

test('actual child rejects genuine outside-root retirement provenance with a failed terminal and hashed original fault',async t=>{
 const {root,store}=await fixture(t),{launchHistoryWorker}=await maintenance(),outside=join(root,'foreign','.writer.lock'),worker=join(root,'foreign-retirement-worker.mjs');
 await mkdir(join(root,'foreign'));await writeFile(outside,JSON.stringify({pid:process.pid}));
 await writeFile(worker,`import {retireOwnedFile} from ${JSON.stringify(new URL('../lib/owned-file-retirement.mjs',import.meta.url).href)};
  import {WorkflowRunStore} from ${JSON.stringify(new URL('../lib/workflow-run-store.mjs',import.meta.url).href)};
  WorkflowRunStore.prototype.cleanupHistory=async()=>retireOwnedFile(${JSON.stringify(outside)},{stagingRoot:${JSON.stringify(join(root,'foreign','.pending'))},validate:()=>process.pid,
   onRetired:()=>{throw Object.assign(new Error('private original fault'),{code:'NEUTRAL_RETIREMENT'});}});
  await import(${JSON.stringify(new URL('../lib/run-history-maintenance-worker.mjs',import.meta.url).href)});`);
 let childPid;const task=launchHistoryWorker({runRoot:store.root,owner:{job_id:randomUUID(),owner_token:randomUUID(),owner_pid:process.pid,created_at:Date.now()},
  signal:new AbortController().signal,onReady:pid=>{childPid=pid;},workerURL:pathToFileURL(worker)});
 await assert.rejects(task,error=>error.code==='RUN_HISTORY_WORKER_RETIREMENT'&&error.failure_count===2&&error.worker_quiescent===true&&!error.retirements&&!JSON.stringify(error).includes('private original fault')&&!JSON.stringify(error).includes(outside));
 assert.throws(()=>process.kill(childPid,0),{code:'ESRCH'});
});

test('Windows pending maintenance claim deletion leaves peers a settled exact receipt after real child quiescence',
 {skip:process.platform!=='win32',timeout:25000},async t=>{
 const {store}=await fixture(t),moduleURL=new URL('../lib/run-history-maintenance.mjs',import.meta.url).href;
 const script=`import fs from 'node:fs/promises';import {syncBuiltinESMExports} from 'node:module';import assert from 'node:assert/strict';import {join} from 'node:path';
  import {holdOwnedDeleteDisposition} from ${JSON.stringify(new URL('./fixtures/owned-retirement-disposition.mjs',import.meta.url).href)};
  const root=process.argv[1],original=fs.unlink;let entered,releaseDelete,closeNative,once=false;
  const pending=new Promise(r=>entered=r),gate=new Promise(r=>releaseDelete=r);
  fs.unlink=async path=>{if(!once&&String(path).includes('.history-maintenance')&&(String(path).endsWith('.writer.lock')||String(path).includes('retired-owner-'))){
   once=true;closeNative=await holdOwnedDeleteDisposition(path);entered();await gate;await closeNative();closeNative=null;return;
  }return original(path);};syncBuiltinESMExports();
  const {RunHistoryMaintenance}=await import(${JSON.stringify(moduleURL)}),{WorkflowRunStore}=await import(${JSON.stringify(new URL('../lib/workflow-run-store.mjs',import.meta.url).href)});
  const store=await new WorkflowRunStore(root).initialize(),manager=new RunHistoryMaintenance({runRoot:root});manager.schedule(store);
  try{
   await pending;const saved=JSON.parse(await fs.readFile(join(root,'.run-locks','.history-maintenance','receipt.json')));
   assert.equal(saved.outcome,'succeeded');assert.throws(()=>process.kill(saved.worker_pid,0),{code:'ESRCH'});
   await assert.rejects(fs.lstat(join(root,'.run-locks','.history-maintenance','.writer.lock')),{code:'ENOENT'});
   const peer=new RunHistoryMaintenance({runRoot:root});const status=await peer.status();assert.equal(status.job_id,saved.job_id);assert.equal(status.error,undefined);
   peer.schedule(store);await peer.settle();assert.equal((await peer.status()).job_id,saved.job_id);await peer.close();
   releaseDelete();await manager.settle();await manager.close();console.log(JSON.stringify({real_pending_delete:true,worker_quiescent:true,peer_coalesced:true}));
  }finally{releaseDelete();if(closeNative)await closeNative();await Promise.allSettled([manager.settle(),manager.close()]);}
 `;
 const result=await promisify(execFile)(process.execPath,['--input-type=module','-e',script,store.root],{windowsHide:true,timeout:20000});
 assert.deepEqual(JSON.parse(result.stdout),{real_pending_delete:true,worker_quiescent:true,peer_coalesced:true});
});

test('Windows pending recovery claim deletion permits exact peer status and later audit after recovery effects settle',
 {skip:process.platform!=='win32',timeout:25000},async t=>{
 const f=await legacyCancellation(t),moduleURL=new URL('../lib/run-history-maintenance.mjs',import.meta.url).href;
 const script=`import fs from 'node:fs/promises';import {syncBuiltinESMExports} from 'node:module';import assert from 'node:assert/strict';import {join} from 'node:path';
  import {holdOwnedDeleteDisposition} from ${JSON.stringify(new URL('./fixtures/owned-retirement-disposition.mjs',import.meta.url).href)};
  const args=JSON.parse(process.argv[1]),root=args.runRoot,original=fs.unlink;let entered,releaseDelete,closeNative,once=false;
  const pending=new Promise(r=>entered=r),gate=new Promise(r=>releaseDelete=r);
  fs.unlink=async path=>{if(!once&&String(path).includes('.history-maintenance')&&(String(path).endsWith('.writer.lock')||String(path).includes('retired-owner-'))){
   once=true;closeNative=await holdOwnedDeleteDisposition(path);entered();await gate;await closeNative();closeNative=null;return;
  }return original(path);};syncBuiltinESMExports();
  const {archiveCancelledHistoryDiagnostic,RunHistoryMaintenance}=await import(${JSON.stringify(moduleURL)}),{WorkflowRunStore}=await import(${JSON.stringify(new URL('../lib/workflow-run-store.mjs',import.meta.url).href)});
  const legacy=await fs.readFile(join(root,'.run-locks','.history-maintenance','receipt.json')),recovery=archiveCancelledHistoryDiagnostic(args);void recovery.catch(()=>{});
  try{
   await pending;assert.deepEqual(await fs.readFile(join(root,'.run-locks','.history-maintenance','receipt.json')),legacy);
   await assert.rejects(fs.lstat(join(root,'.run-locks','.history-maintenance','.writer.lock')),{code:'ENOENT'});
   const peer=new RunHistoryMaintenance({runRoot:root}),status=await peer.status();assert.equal(status.outcome,'cancelled');assert.equal(status.error.code,'RUN_HISTORY_CANCELLED');
   await assert.rejects(archiveCancelledHistoryDiagnostic(args),{code:'ENOENT'});
   peer.schedule(await new WorkflowRunStore(root).initialize());await peer.settle();assert.equal((await peer.status()).outcome,'succeeded');await peer.close();
   releaseDelete();const result=await recovery;assert.equal(JSON.parse(await fs.readFile(result.recovery_receipt_path)).outcome,'succeeded');
   console.log(JSON.stringify({real_pending_delete:true,legacy_preserved_before_new_audit:true,peer_audit_valid:true}));
  }finally{releaseDelete();if(closeNative)await closeNative();await Promise.allSettled([recovery]);}
 `;
 const result=await promisify(execFile)(process.execPath,['--input-type=module','-e',script,JSON.stringify(f.args)],{windowsHide:true,timeout:20000});
 assert.deepEqual(JSON.parse(result.stdout),{real_pending_delete:true,legacy_preserved_before_new_audit:true,peer_audit_valid:true});
});

test('real child audit failure and unknown maintenance retirement cleanup failure both persist without hiding either fault',async t=>{
 const {store}=await fixture(t);await addRun(store,'corrupt');await writeFile(join(store.directory('corrupt'),'pins.json'),'{}');
 const script=`import fs from 'node:fs/promises';import {syncBuiltinESMExports} from 'node:module';import assert from 'node:assert/strict';import {join} from 'node:path';
  const root=process.argv[1],original=fs.unlink;let attempts=0;
  fs.unlink=async path=>{if(String(path).includes('.history-maintenance')&&String(path).includes('retired-owner-')){
   attempts++;throw Object.assign(new Error('private maintenance cleanup body'),{code:'EPERM',errno:-4048});
  }return original(path);};syncBuiltinESMExports();
  const {RunHistoryMaintenance}=await import(${JSON.stringify(new URL('../lib/run-history-maintenance.mjs',import.meta.url).href)}),{WorkflowRunStore}=await import(${JSON.stringify(new URL('../lib/workflow-run-store.mjs',import.meta.url).href)});
  const manager=new RunHistoryMaintenance({runRoot:root});manager.schedule(await new WorkflowRunStore(root).initialize());
  let error;try{await manager.settle();}catch(value){error=value;}assert(error instanceof AggregateError);assert.deepEqual(error.errors.map(item=>item.code),['RUN_PINS_CORRUPT','EPERM']);
  await assert.rejects(manager.close());assert.equal(attempts,1);const status=await manager.status(),locator=status.error.retirements[0];
  assert.equal(locator.canonical_path,'.run-locks/.history-maintenance/.writer.lock');assert.equal(locator.phase,'retirement_delete');assert.equal(locator.owner_pid,process.pid);
  assert.equal(locator.cause_code,'EPERM');assert.equal(locator.cause_errno,-4048);assert.equal(locator.retired,true);
  assert.equal(JSON.parse(await fs.readFile(join(root,locator.retired_path))).owner_pid,process.pid);
  assert.equal(status.error.failures[0].code,'RUN_PINS_CORRUPT');assert.equal(status.error.failures[1].code,'EPERM');assert(!JSON.stringify(status).includes('private maintenance cleanup body'));
  console.log(JSON.stringify({attempts,both_original_codes_visible:true,exact_private_locator:true}));`;
 const result=await promisify(execFile)(process.execPath,['--input-type=module','-e',script,store.root],{windowsHide:true,timeout:10000});
 assert.deepEqual(JSON.parse(result.stdout),{attempts:1,both_original_codes_visible:true,exact_private_locator:true});
});

test('actual child retirement locator survives a later genuine Host cleanup aggregate without summary truncation',async t=>{
 const {diagnostic}=await maintenance();
 const f=await contendedChild(t,{onAdmission:()=>{},workerPrelude:`import fs from 'node:fs/promises';import {syncBuiltinESMExports} from 'node:module';
  const original=fs.unlink;fs.unlink=async path=>{const value=String(path).replaceAll('\\\\','/');
   if(value.includes('/.store-operation/.pending/retired-owner-'))throw Object.assign(new Error('private child retirement fault'),{code:'EPERM',errno:-4048});
   return original(path);
  };syncBuiltinESMExports();`});
 let child;try{await f.task;}catch(error){child=error;}assert.equal(child.retirements.length,1);
 const parent=await genuineRetirementFault(f.store,{canonicalPath:'.run-locks/.history-maintenance/.writer.lock'});
 const unrelated=Array.from({length:5},()=>Object.assign(new Error('private unrelated fault'),{code:'NEUTRAL_FAILURE'}));
 const combined=diagnostic(new AggregateError([...unrelated,new AggregateError([child,parent],'child and Host cleanup')],'all faults'),0,f.store.root);
 assert.equal(combined.retirements.length,2);assert.equal(combined.retirements[0].cause_code,'EPERM');assert.equal(combined.retirements[1].cause_code,'NEUTRAL_RETIREMENT');
 assert(!JSON.stringify(combined).includes('private child retirement fault'));assert(!JSON.stringify(combined).includes('private unrelated fault'));
});
