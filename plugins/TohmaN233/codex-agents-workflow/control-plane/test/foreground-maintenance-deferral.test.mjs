import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,rm,mkdir,lstat,readFile,writeFile} from 'node:fs/promises';
import {join} from 'node:path';
import {spawn} from 'node:child_process';
import {tmpdir} from './physical-tempdir.mjs';
import {RunHistoryMaintenance,HISTORY_MAINTENANCE_INTERVAL_MS} from '../lib/run-history-maintenance.mjs';
import {withForegroundActivity,foregroundActivityCount,inForegroundActivity,onForegroundIdle} from '../lib/foreground-activity.mjs';
import {WorkflowRunStore} from '../lib/workflow-run-store.mjs';
import {WorkflowStore,withRunAdmissionObserver} from '../lib/workflow-store.mjs';
import {canonicalJSON,digest} from '../lib/workflow-revisions.mjs';
import {handleRpc} from '../server.mjs';
import {withForegroundOperationObservation} from '../lib/foreground-operation-observation.mjs';

const latch=()=>{let release;return {promise:new Promise(r=>release=r),release};};
const census={examined:0,deleted_count:0,preserved_count:0};
async function fixture(t,launch){
 const root=await mkdtemp(join(tmpdir(),'foreground-maintenance-')),store=await new WorkflowRunStore(join(root,'runs')).initialize();
 let launches=0;
 const manager=new RunHistoryMaintenance({runRoot:store.root,launchWorker:async options=>{
  launches++;await options.onReady(process.pid);return launch?launch(options):census;
 }});
 t.after(async()=>{try{if(!manager.closed)await manager.close();}finally{await rm(root,{recursive:true,maxRetries:3,retryDelay:100});}});
 return {root,store,manager,launches:()=>launches};
}
async function inspectScheduled(manager){if(manager.task)await manager.task;}

test('automatic opportunity defers only its unclaimed launch and flushes once outside successful request',async t=>{
 const f=await fixture(t);
 const result=await withForegroundActivity(f.store.root,async()=>{
  f.manager.hook(f.store);await inspectScheduled(f.manager);
  assert.equal(f.launches(),0);
  const status=await f.manager.status();assert.equal(status.automatic_deferred,true);assert.equal(status.foreground_active,1);
  await assert.rejects(lstat(f.manager.lockPath),{code:'ENOENT'});
  return 'original';
 });
 assert.equal(result,'original');assert.equal(foregroundActivityCount(f.store.root),0);
 await f.manager.settle();assert.equal(f.launches(),1);assert.equal((await f.manager.status()).automatic_deferred,false);
});

test('failure releases its original scope and still flushes exactly once',async t=>{
 const f=await fixture(t),failure=new Error('original failure');
 await assert.rejects(withForegroundActivity(f.store.root,async()=>{
  f.manager.hook(f.store);await inspectScheduled(f.manager);assert.equal(f.launches(),0);throw failure;
 }),error=>error===failure);
 await f.manager.settle();assert.equal(f.launches(),1);
});

test('overlapping requests flush only after last scope and stale descendants are inactive',async t=>{
 const f=await fixture(t),entered=latch(),release=latch(),descendantGate=latch();let descendant;
 const first=withForegroundActivity(f.store.root,async()=>{
  f.manager.hook(f.store);await inspectScheduled(f.manager);entered.release();await release.promise;
 });await entered.promise;
 await withForegroundActivity(f.store.root,async()=>{
  assert.equal(foregroundActivityCount(f.store.root),2);
  descendant=(async()=>{await descendantGate.promise;return inForegroundActivity(f.store.root);})();
  f.manager.hook(f.store);await inspectScheduled(f.manager);assert.equal(f.launches(),0);
 });descendantGate.release();assert.equal(foregroundActivityCount(f.store.root),1);assert.equal(await descendant,false);assert.equal(f.launches(),0);
 release.release();await first;await f.manager.settle();assert.equal(f.launches(),1);
});

test('explicit schedule and settle do not wait on a held foreground scope',async t=>{
 const f=await fixture(t);
 await withForegroundActivity(f.store.root,async()=>{
  f.manager.hook(f.store);await inspectScheduled(f.manager);assert.equal(f.launches(),0);
  await f.manager.settle();assert.equal(f.launches(),1);
 });
 const g=await fixture(t);
 await withForegroundActivity(g.store.root,async()=>{g.manager.schedule(g.store);await g.manager.settle();assert.equal(g.launches(),1);});
});

test('one existing interval of deferred age permits fresh launch at later automatic opportunity',async t=>{
 const f=await fixture(t);const realNow=Date.now;let now=realNow();t.mock.method(Date,'now',()=>now);
 await withForegroundActivity(f.store.root,async()=>{
  f.manager.hook(f.store);await inspectScheduled(f.manager);assert.equal(f.launches(),0);
  now+=HISTORY_MAINTENANCE_INTERVAL_MS-1;f.manager.hook(f.store);await inspectScheduled(f.manager);assert.equal(f.launches(),0);
  now++;f.manager.hook(f.store);await inspectScheduled(f.manager);assert.equal(f.launches(),1);
 });await f.manager.settle();assert.equal(f.launches(),1);
});

test('original durable failure inspection stays immediate and owns its error',async t=>{
 const f=await fixture(t);await mkdir(f.manager.directory,{recursive:true});
 await writeFile(f.manager.diagnosticPath,JSON.stringify({schema_version:1,error:{code:'EXACT_HISTORY_FAILURE',message:'bounded failure'}}));
 await withForegroundActivity(f.store.root,async()=>{
  f.manager.hook(f.store);await inspectScheduled(f.manager);
  assert.equal(f.manager.error.code,'EXACT_HISTORY_FAILURE');assert.equal(f.launches(),0);
  assert.equal((await f.manager.status()).error.code,'EXACT_HISTORY_FAILURE');
 });await assert.rejects(f.manager.settle(),{code:'EXACT_HISTORY_FAILURE'});
 await assert.rejects(f.manager.close(),{code:'EXACT_HISTORY_FAILURE'});
});

test('flush rechecks due receipts and diagnostics rather than retaining an inspection',async t=>{
 for(const kind of ['due','failure']){
  const f=await fixture(t);
  await withForegroundActivity(f.store.root,async()=>{
   f.manager.hook(f.store);await inspectScheduled(f.manager);assert.equal(f.launches(),0);
   if(kind==='failure')await writeFile(f.manager.diagnosticPath,JSON.stringify({schema_version:1,error:{code:'FLUSH_FAILURE',message:'bounded failure'}}));
   else {
    const now=Date.now();await writeFile(f.manager.receiptPath,JSON.stringify({schema_version:1,job_id:'11111111-1111-4111-8111-111111111111',owner_token:'22222222-2222-4222-8222-222222222222',owner_pid:process.pid,created_at:now,due_at:now+60000,phase:'settled',outcome:'succeeded'}));
   }
  });
  if(kind==='failure'){await assert.rejects(f.manager.settle(),{code:'FLUSH_FAILURE'});await assert.rejects(f.manager.close(),{code:'FLUSH_FAILURE'});}
  else await f.manager.settle();
  assert.equal(f.launches(),0);assert.equal((await f.manager.status()).automatic_deferred,false);
 }
});

test('close cancels unclaimed deferral without publishing a fabricated receipt or job',async t=>{
 const f=await fixture(t);
 await withForegroundActivity(f.store.root,async()=>{
  f.manager.hook(f.store);await inspectScheduled(f.manager);assert.equal(f.launches(),0);
  await f.manager.close();assert.equal((await f.manager.status()).automatic_deferred,false);
 });assert.equal(f.launches(),0);await assert.rejects(readFile(f.manager.receiptPath),{code:'ENOENT'});
});

test('real public admission proves original competing audit blocks and deferred audit admits foreground first',{timeout:10000},async t=>{
 for(const deferred of [false,true]){
  const entered=latch(),release=latch(),order=[];let f;
  f=await fixture(t,async()=>new WorkflowStore(join(f.store.root,'.run-locks','.store-operation')).withRunAdmission(async()=>{
   entered.release();order.push('audit');await release.promise;return census;
  },{onWait:()=>{}}));
  const pins={resources:[],root:{workflow:{nodes:[]}}};
  await f.store.create('selected',pins,new Map(),{run_id:'selected',pins_hash:digest(canonicalJSON(pins)),status:'running',nodes:{}});
  let finished=false,foreground;const waiting=latch();
  try{
   await withForegroundActivity(f.store.root,async()=>{
    if(deferred){f.manager.hook(f.store);await inspectScheduled(f.manager);assert.equal(f.launches(),0);}
    else {f.manager.schedule(f.store);await entered.promise;}
    foreground=withRunAdmissionObserver({admissionRoot:join(f.store.root,'.run-locks','.store-operation'),
     onWait:detail=>{if(['queued','waiting'].includes(detail.phase))waiting.release();}},()=>f.store.read('selected'))
     .then(()=>{finished=true;order.push('foreground');});
    if(deferred){await foreground;assert.equal(finished,true);assert.deepEqual(order,['foreground']);}
    else {await waiting.promise;assert.equal(finished,false);release.release();await foreground;assert.deepEqual(order,['audit','foreground']);}
   });
   if(deferred){await entered.promise;release.release();}
   await f.manager.settle();assert.equal(f.launches(),1);
  }finally{release.release();await foreground;}
 }
});

test('flush recognizes a fresh foreign claim without touching it or launching a replacement',async t=>{
 const f=await fixture(t);let bytes;
 await withForegroundActivity(f.store.root,async()=>{
  f.manager.hook(f.store);await inspectScheduled(f.manager);assert.equal(f.launches(),0);
  const now=Date.now();bytes=JSON.stringify({schema_version:1,job_id:'11111111-1111-4111-8111-111111111111',owner_token:'22222222-2222-4222-8222-222222222222',owner_pid:process.pid,created_at:now,due_at:now+60000,phase:'claimed',outcome:'pending'});
  await writeFile(f.manager.lockPath,bytes);
 });await f.manager.settle();assert.equal(f.launches(),0);assert.equal(await readFile(f.manager.lockPath,'utf8'),bytes);
 const status=await f.manager.status();assert.equal(status.automatic_deferred,false);assert.equal(status.phase,'claimed');assert.equal(status.owner_token,undefined);
});

test('an already active job keeps its exact owner and is not deferred or restarted',async t=>{
 const entered=latch(),release=latch();const f=await fixture(t,async()=>{entered.release();await release.promise;return census;});
 f.manager.schedule(f.store);await entered.promise;const owner=f.manager.owner.job_id;
 try{await withForegroundActivity(f.store.root,async()=>{
  f.manager.hook(f.store);assert.equal(f.manager.owner.job_id,owner);assert.equal((await f.manager.status()).automatic_deferred,false);
 });}finally{release.release();}
 await f.manager.settle();assert.equal(f.launches(),1);
});

test('manual full cleanup and list are immediate and another root does not inherit deferral',async t=>{
 const f=await fixture(t),g=await fixture(t);
 await withForegroundActivity(f.store.root,async()=>{
  f.manager.hook(f.store);await inspectScheduled(f.manager);assert.equal(f.launches(),0);
  assert.deepEqual(await f.store.list(),[]);assert.equal((await f.store.cleanupHistory()).examined,0);assert.equal(f.launches(),0);
  g.manager.hook(g.store);await g.manager.settle();assert.equal(g.launches(),1);
 });await f.manager.settle();assert.equal(f.launches(),1);
});

test('close racing initial inspection owns every promise and launches no unclaimed child',async t=>{
 const f=await fixture(t),entered=latch(),release=latch(),read=f.manager.readRecord;
 f.manager.readRecord=async(path,options)=>{if(path===f.manager.diagnosticPath){entered.release();await release.promise;}return read(path,options);};
 await withForegroundActivity(f.store.root,async()=>{
  f.manager.hook(f.store);await entered.promise;const closing=f.manager.close();release.release();await closing;
 });assert.equal(f.launches(),0);assert.equal(f.manager.task,null);await assert.rejects(lstat(f.manager.lockPath),{code:'ENOENT'});
});

test('close after idle flush preserves confirmed child cancellation and exact receipt',async t=>{
 const entered=latch();const f=await fixture(t,async({signal})=>{
  entered.release();await new Promise(resolve=>{if(signal.aborted)resolve();else signal.addEventListener('abort',resolve,{once:true});});
  throw Object.assign(new Error('confirmed stopped child'),{code:'RUN_HISTORY_CANCELLED',worker_quiescent:true,worker_cancelled:true});
 });
 await withForegroundActivity(f.store.root,async()=>{f.manager.hook(f.store);await inspectScheduled(f.manager);assert.equal(f.launches(),0);});
 await entered.promise;await f.manager.close();assert.equal(f.launches(),1);assert.equal((await f.manager.status()).outcome,'cancelled');
 await assert.rejects(lstat(f.manager.lockPath),{code:'ENOENT'});
});

test('report failure releases activity and scheduling registrations without replacing original error',async t=>{
 const f=await fixture(t),failure=new Error('report persistence failure');let flushes=0;
 await assert.rejects(withForegroundActivity(f.store.root,()=>withForegroundOperationObservation(async()=>{
  onForegroundIdle(f.store.root,()=>flushes++);return 'original';
 },()=>{throw failure;})),error=>error===failure);
 assert.equal(flushes,1);assert.equal(foregroundActivityCount(f.store.root),0);
});

test('server original execution error and audit failure release their scope; discovery stays outside it',async t=>{
 const f=await fixture(t),configPath=join(f.root,'config.json'),runRoot=join(f.root,'workflow-runs');
 const request={jsonrpc:'2.0',id:1,method:'tools/call',params:{name:'workflow_native_next',arguments:{}}};
 const response=await handleRpc(request,{configPath});assert.equal(response.result.isError,true);assert.equal(foregroundActivityCount(runRoot),0);
 const audit=join(f.root,'control-plane-audit.jsonl');await rm(audit);await mkdir(audit);
 await assert.rejects(handleRpc(request,{configPath}));assert.equal(foregroundActivityCount(runRoot),0);
 const discovery=await handleRpc({jsonrpc:'2.0',id:2,method:'tools/list'},{configPath});assert(discovery.result.tools.length);assert.equal(foregroundActivityCount(runRoot),0);
});

test('real child full audit contention is removed from originating foreground scope',{timeout:10000},async t=>{
 for(const deferred of [false,true]){
  const f=await fixture(t),held=latch(),waiting=latch();let child,launches=0;
  const pins={resources:[],root:{workflow:{nodes:[]}}};
  for(const id of ['historical','selected'])await f.store.create(id,pins,new Map(),{run_id:id,pins_hash:digest(canonicalJSON(pins)),status:'running',nodes:{}});
  f.manager.launchWorker=async options=>{
   launches++;
   const code=`import fs from 'node:fs/promises';import {syncBuiltinESMExports} from 'node:module';import {join} from 'node:path';
    const root=${JSON.stringify(f.store.root)},target=join(root,'run-historical.run','pins.json'),read=fs.readFile;
    let release;const gate=new Promise(r=>release=r);process.on('message',m=>{if(m==='release')release();});
    fs.readFile=async(path,...args)=>{if(String(path)===target){process.send({phase:'held'});await gate;}return read(path,...args);};
    syncBuiltinESMExports();
    const {WorkflowRunStore}=await import(${JSON.stringify(new URL('../lib/workflow-run-store.mjs',import.meta.url).href)});
    const {withRunAdmissionObserver}=await import(${JSON.stringify(new URL('../lib/workflow-store.mjs',import.meta.url).href)});
    const store=await new WorkflowRunStore(root).initialize();
    const result=await withRunAdmissionObserver({admissionRoot:join(root,'.run-locks','.store-operation'),onWait:()=>{}},()=>store.cleanupHistory());
    process.send({phase:'result',result});process.disconnect();`;
   child=spawn(process.execPath,['--input-type=module','-e',code],{windowsHide:true,stdio:['ignore','ignore','pipe','ipc']});
   let result,stderr='';child.stderr.on('data',bytes=>stderr+=bytes);
   const closed=new Promise((resolve,reject)=>{child.once('error',reject);child.once('close',exit=>exit===0?resolve():reject(new Error(`Audit fixture child failed: ${stderr}`)));});
   child.on('message',message=>{if(message.phase==='held')held.release();if(message.phase==='result')result=message.result;});
   await options.onReady(child.pid);await closed;assert(result);return result;
  };
  try{
   let complete=false;
   if(!deferred){f.manager.hook(f.store);await held.promise;}
   await withForegroundActivity(f.store.root,async()=>{
    if(deferred){f.manager.hook(f.store);await inspectScheduled(f.manager);assert.equal(launches,0);}
    const foreground=withRunAdmissionObserver({admissionRoot:join(f.store.root,'.run-locks','.store-operation'),
     onWait:detail=>{if(['queued','waiting'].includes(detail.phase))waiting.release();}},()=>f.store.read('selected')).then(()=>complete=true);
    if(!deferred){await waiting.promise;assert.equal(complete,false);child.send('release');}
    await foreground;assert.equal(complete,true);
   });
   if(deferred){await held.promise;child.send('release');}
   await f.manager.settle();assert.equal(launches,1);assert.equal((await f.manager.status()).audit.examined,2);
  }finally{if(child?.connected)child.send('release');if(child?.exitCode===null)await f.manager.settle();}
 }
});
