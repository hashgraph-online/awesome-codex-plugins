import test from 'node:test';
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { mkdtemp, mkdir, rm, readFile, writeFile, unlink, lstat } from 'node:fs/promises';
import { join } from 'node:path';
import { tmpdir } from './physical-tempdir.mjs';
import { WorkflowRunStore,withRunStoreObservation } from '../lib/workflow-run-store.mjs';
import { WorkflowStore,withRunAdmissionObserver } from '../lib/workflow-store.mjs';
import { canonicalJSON, digest } from '../lib/workflow-revisions.mjs';
import { randomUUID } from 'node:crypto';

const runModule = new URL('../lib/workflow-run-store.mjs',import.meta.url).href;
const storeModule = new URL('../lib/workflow-store.mjs',import.meta.url).href;
const errorModule = new URL('../lib/workbench-api.mjs',import.meta.url).href;
async function fixture(t) {
  const root=await mkdtemp(join(tmpdir(),'run-store-admission-'));
  t.after(()=>rm(root,{recursive:true,maxRetries:3,retryDelay:100}));
  const store=await new WorkflowRunStore(root).initialize();
  const pins={resources:[],root:{workflow:{nodes:[]}}};
  for(const id of ['parent','child'])await store.create(id,pins,new Map(),{run_id:id,pins_hash:digest(canonicalJSON(pins)),status:'running',nodes:{}});
  return {root,store,admission:join(root,'.run-locks','.store-operation')};
}

test('Run observation and conversation lookup do not acquire abandoned writer admission',async t=>{
 const f=await fixture(t),thread='00000000-0000-7000-8000-000000000001';
 // The thread locator reads the immutable start identity.
 const located=await f.store.read('parent');
 const pins=located.pins,id='same-thread';
 await f.store.create(id,pins,new Map(),{run_id:id,pins_hash:digest(canonicalJSON(pins)),status:'cancelled',nodes:{},constraints:{native_parent_thread_id:thread}});
 const bytes=canonicalJSON({pid:process.pid,token:randomUUID(),created_at:new Date().toISOString()});
 const paths=[join(f.admission,'.writer.lock'),join(f.root,'.writer.lock'),join(f.store.directory(id),'.writer.lock')];
 for(const path of paths)await writeFile(path,bytes);
 assert.equal((await f.store.observe(id)).state.status,'cancelled');
 assert.equal((await f.store.list()).length,3);
 assert.deepEqual((await f.store.listForThread(thread)).map(r=>r.state.run_id),[id]);
 for(const path of paths)assert.equal(await readFile(path,'utf8'),bytes);
});

test('lock-free observation still rejects torn journals and mismatched immutable pins',async t=>{
 const f=await fixture(t),path=join(f.store.directory('parent'),'events.jsonl'),original=await readFile(path);
 await writeFile(path,Buffer.concat([original,Buffer.from('{"unfinished":')]));
 await assert.rejects(f.store.observe('parent'),{code:'RUN_JOURNAL_TORN'});
 await writeFile(path,original);
 await writeFile(join(f.store.directory('parent'),'pins.json'),canonicalJSON({resources:[],changed:true}));
 await assert.rejects(f.store.observe('parent'),{code:'RUN_PINS_CORRUPT'});
});

function childProcess(t,code,args) {
  const child=spawn(process.execPath,['--input-type=module','-e',code,...args],{windowsHide:true,stdio:['ignore','pipe','pipe','ipc']});
  let stderr='';child.stderr.on('data',data=>{stderr+=data;});
  const messages=[],waiters=[];
  child.on('message',message=>{const next=waiters.shift();if(next)next.resolve(message);else messages.push(message);});
  const closed=new Promise((resolve,reject)=>{
    child.once('error',reject);
    child.once('exit',(code,signal)=>{
      for(const waiter of waiters.splice(0))waiter.reject(new Error(`Child exited ${code}/${signal}: ${stderr}`));
      resolve({code,signal,stderr});
    });
  });
  t.after(async()=>{if(child.exitCode===null&&child.signalCode===null)child.kill();await closed;});
  return {child,closed,next:()=>messages.length?Promise.resolve(messages.shift()):new Promise((resolve,reject)=>waiters.push({resolve,reject}))};
}

test('denied exclusive writer opening fails once with bounded exact evidence and never enters the transaction',async t=>{
  const f=await fixture(t);
  const child=childProcess(t,`
    import fs from 'node:fs/promises';
    import {syncBuiltinESMExports} from 'node:module';
    import {join} from 'node:path';
    const denied=join(process.argv[1],'.writer.lock'),original=fs.open;let opens=0,callbacks=0;const diagnostics=[];
    fs.open=async(path,flags,...rest)=>{
      if(path===denied&&flags==='wx'){opens++;throw Object.assign(new Error('neutral permission failure with a secret body'),{code:'EPERM',errno:-4048,syscall:'open',path:denied});}
      return original(path,flags,...rest);
    };
    syncBuiltinESMExports();
    const {WorkflowStore}=await import(${JSON.stringify(storeModule)});
    const {workbenchErrorPayload}=await import(${JSON.stringify(errorModule)});
    try{await new WorkflowStore(process.argv[1]).withRunAdmission(()=>callbacks++,{onWait:detail=>diagnostics.push(detail)});}
    catch(error){process.send({code:error.code,cause_code:error.cause?.code,lock_exists:error.lock_exists,opens,callbacks,diagnostics,public_error:workbenchErrorPayload(error)});}
    process.disconnect();
  `,[f.admission]);
  const result=await child.next();
  assert.equal(result.code,'RUN_STORE_ADMISSION_OPEN_FAILED');assert.equal(result.cause_code,'EPERM');
  assert.equal(result.lock_exists,false);assert.equal(result.opens,1);assert.equal(result.callbacks,0);
  const failed=result.diagnostics.find(item=>item.phase==='open_failed');assert.equal(failed.open_error_code,'EPERM');
  assert.equal(failed.lock_path,join(f.admission,'.writer.lock'));assert.equal(failed.lock_exists,false);
  const {waited_ms:writerWait,...publicObservation}=result.public_error.details.admission;
  const {waited_ms:wholeAdmissionWait,...traceObservation}=failed;
  assert.deepEqual(publicObservation,{...traceObservation,observation_basis:'after_failed_open',wait_basis:'exclusive_writer_acquisition'});
  assert(Number.isSafeInteger(writerWait)&&writerWait>=0&&writerWait<=wholeAdmissionWait);
  assert.equal(result.public_error.details.admission.open_errno,-4048);
  assert.equal(result.public_error.retryable,undefined);
  assert.equal(JSON.stringify(result.public_error).includes('secret body'),false);
  assert.equal((await child.closed).code,0);assert.equal(await new WorkflowStore(f.admission).inspectWriter(),null);
});

test('denied writer opening observes a live exact owner without exposing or changing its token',async t=>{
  const f=await fixture(t);
  const child=childProcess(t,`
    import fs from 'node:fs/promises';import {syncBuiltinESMExports} from 'node:module';import {join} from 'node:path';
    const denied=join(process.argv[1],'.writer.lock'),token='cccccccc-cccc-4ccc-8ccc-cccccccccccc';
    const bytes=JSON.stringify({pid:process.pid,token,created_at:new Date().toISOString()});await fs.writeFile(denied,bytes);
    const original=fs.open;let opens=0,callbacks=0;const diagnostics=[];
    fs.open=async(path,flags,...rest)=>{if(path===denied&&flags==='wx'){opens++;throw Object.assign(new Error('neutral denied owner'),{code:'EPERM',syscall:'open',path});}return original(path,flags,...rest);};
    syncBuiltinESMExports();const {WorkflowStore}=await import(${JSON.stringify(storeModule)});
    const {workbenchErrorPayload}=await import(${JSON.stringify(errorModule)});
    try{await new WorkflowStore(process.argv[1]).withRunAdmission(()=>callbacks++,{onWait:detail=>diagnostics.push(detail)});}
    catch(error){process.send({code:error.code,cause_code:error.cause?.code,opens,callbacks,diagnostics,public_error:workbenchErrorPayload(error),
      preserved:(await fs.readFile(denied,'utf8'))===bytes,token_leaked:JSON.stringify(diagnostics).includes(token)});}
    process.disconnect();
  `,[f.admission]);
  const result=await child.next();assert.equal(result.code,'RUN_STORE_ADMISSION_OPEN_FAILED');assert.equal(result.cause_code,'EPERM');
  assert.equal(result.opens,1);assert.equal(result.callbacks,0);assert.equal(result.preserved,true);assert.equal(result.token_leaked,false);
  const detail=result.diagnostics.find(item=>item.phase==='open_failed');
  assert.equal(detail.lock_exists,true);assert.equal(detail.lock_kind,'file');assert.equal(detail.owner_record_valid,true);
  assert.equal(detail.observed_owner_alive,true);assert(Number.isSafeInteger(detail.observed_owner_pid));
  assert.equal(result.public_error.details.admission.observed_owner_alive,true);
  assert.equal(result.public_error.details.admission.observed_owner_pid,detail.observed_owner_pid);
  assert.equal(JSON.stringify(result.public_error).includes('cccccccc-cccc-4ccc-8ccc-cccccccccccc'),false);
  assert.equal((await child.closed).code,0);
});

test('Windows owner release with exact differently cased ENOENT re-enters acquisition once', {skip:process.platform!=='win32'},async t=>{
  const f=await fixture(t);
  const child=childProcess(t,`
    import fs from 'node:fs/promises';import {syncBuiltinESMExports} from 'node:module';import {join} from 'node:path';
    const lock=join(process.argv[1],'.writer.lock'),originalOpen=fs.open,originalStat=fs.lstat;
    let opens=0,releaseObserved=false,callbacks=0;
    fs.open=async(path,flags,...rest)=>{if(path===lock&&flags==='wx'&&++opens===1)throw Object.assign(new Error('neutral owner held'),{code:'EEXIST',path});return originalOpen(path,flags,...rest);};
    fs.lstat=async(path,...rest)=>{if(path===lock&&opens===1&&!releaseObserved){releaseObserved=true;throw Object.assign(new Error('neutral owner released'),{code:'ENOENT',path:lock.toUpperCase()});}return originalStat(path,...rest);};
    syncBuiltinESMExports();const {WorkflowStore}=await import(${JSON.stringify(storeModule)});
    const result=await new WorkflowStore(process.argv[1]).withRunAdmission(()=>{callbacks++;return 'acquired';},{onWait:()=>{}});
    process.send({result,opens,releaseObserved,callbacks});process.disconnect();
  `,[f.admission]);
  assert.deepEqual(await child.next(),{result:'acquired',opens:2,releaseObserved:true,callbacks:1});
  assert.equal((await child.closed).code,0);assert.equal(await new WorkflowStore(f.admission).inspectWriter(),null);
});
const holdTransaction = `
import {WorkflowRunStore} from ${JSON.stringify(runModule)};
const s=await new WorkflowRunStore(process.argv[1]).initialize(),mode=process.argv[2];
let callbacks=0;
const hold=async()=>{callbacks++;process.send({entered:true,pid:process.pid});await new Promise(resolve=>process.once('message',resolve));};
if(mode==='mutate')await s.mutate('parent','executor_event',async state=>{await hold();await s.read('parent');await s.read('child');state.checked=1;});
else if(mode==='list'){const writer=s.writer.withWriter.bind(s.writer);s.writer.withWriter=action=>writer(async()=>{await hold();return action();});await s.list();}
else {const guard=s.withRunGuard.bind(s);s.withRunGuard=(id,action)=>guard(id,async()=>{await hold();return action();});await s.read('parent');}
process.send({done:true,callbacks});process.disconnect();
`;

test('a native lifecycle observation never collides with cross-process history admission',async t=>{
 const f=await fixture(t);
 const holder=childProcess(t,`
  import fs from 'node:fs/promises';import {syncBuiltinESMExports} from 'node:module';import {join} from 'node:path';
  const original=fs.readFile,path=join(process.argv[1],'run-parent.run','events.jsonl');let held=false;
  fs.readFile=async(file,...args)=>{if(file===path&&!held){held=true;process.send({entered:true});await new Promise(resolve=>process.once('message',resolve));}return original(file,...args);};syncBuiltinESMExports();
  const {WorkflowRunStore}=await import(${JSON.stringify(runModule)});
  await new WorkflowRunStore(process.argv[1]).readNativeWaitState('parent');process.send({done:true});process.disconnect();
 `,[f.root]);
 await holder.next();let record;
 try{record=await f.store.readHistoryMetadata('parent');}
 finally{holder.child.send({release:true});await holder.next();await holder.closed;}
 assert.equal(record.state.run_id,'parent');
});

test('named Run admission proves the actual cross-PID writer operation without another lock file',async t=>{
  const f=await fixture(t),holder=childProcess(t,holdTransaction,[f.root,'mutate']);
  const held=await holder.next();let waiting,report;
  const observed=new Promise(resolve=>waiting=resolve);
  const reading=withRunStoreObservation(()=>withRunAdmissionObserver({admissionRoot:f.admission,onWait:detail=>{
    if(detail.phase==='waiting')waiting(detail);
  }},()=>f.store.read('child')),value=>report=value);
  let owner;
  try{owner=await observed;}finally{holder.child.send({release:true});await reading;}
  assert.equal(owner.owner_pid,held.pid);
  assert.equal(owner.owner_operation,'writer','exact owner record omitted the method holding global admission');
  assert.equal(report.resource_objects,0);assert.equal(JSON.stringify(report).includes('token'),false);
  assert.equal((await holder.next()).callbacks,1);assert.equal((await holder.closed).code,0);
  assert.equal(await new WorkflowStore(f.admission).inspectWriter(),null);
});

test('Run boundary observation reports actual resource audits once and preserves failures without private payloads',async t=>{
  const f=await fixture(t),reports=[];
  await withRunStoreObservation(async()=>{
    await f.store.read('parent');
    await withRunStoreObservation(()=>f.store.readNativeWaitState('child'),()=>assert.fail('nested report'));
  },report=>reports.push(report));
  assert.equal(reports.length,1);assert.equal(reports[0].methods.read,1);assert.equal(reports[0].methods.native_wait,1);
  assert.equal(reports[0].resource_audits,0);assert.equal(reports[0].resource_objects,0);
  assert(JSON.stringify(reports[0]).length<1000);
  await writeFile(join(f.store.directory('parent'),'pins.json'),'{}');
  await assert.rejects(withRunStoreObservation(()=>f.store.read('parent'),report=>reports.push(report)),{code:'RUN_PINS_CORRUPT'});
  assert.equal(reports[1].methods.read,1);assert.equal(reports[1].failures[0].method,'guard');assert.equal(reports[1].failures[0].code,'RUN_PINS_CORRUPT');
  assert.equal(JSON.stringify(reports).includes('pins.json'),false);
});

test('history read failure settles admitted cross-process callbacks without monopolizing admission',{timeout:15000},async t=>{
 const f=await fixture(t);await writeFile(join(f.store.directory('parent'),'pins.json'),'{}');
 const holder=childProcess(t,`
 import {WorkflowRunStore} from ${JSON.stringify(runModule)};
 import {WorkflowStore} from ${JSON.stringify(storeModule)};
 const s=new WorkflowRunStore(process.argv[1]),original=s.readHistoryMetadataBatch.bind(s);
 let release;const proceed=new Promise(r=>release=r);
 process.once('message',release);
 s.readHistoryMetadataBatch=async function(...args){
  process.send({entered:true});await proceed;return original(...args);
 };
 try{await s.cleanupHistory({olderThanMs:0});process.send({unexpected:true});}
 catch(error){process.send({failed:true,code:error.code});}
 process.disconnect();
 `,[f.root]);
 assert.equal((await holder.next()).entered,true);
 let completed=false;
 const mutation=f.store.mutate('child','executor_event',state=>{state.checked=1;}).finally(()=>completed=true);
 await mutation;assert.equal(completed,true);
 holder.child.send({release:true});assert.deepEqual(await holder.next(),{failed:true,code:'RUN_PINS_CORRUPT'});
 await mutation;assert.equal((await holder.closed).code,0);
 assert.equal((await f.store.read('child')).state.checked,1);assert.equal(await f.store.writer.inspectWriter(),null);
 assert(await readFile(join(f.store.directory('parent'),'pins.json')));
});

for(const mode of ['mutate','read'])test(`a second Node process waits for admitted ${mode} and runs history/read once`,{timeout:15000},async t=>{
  const f=await fixture(t),holder=childProcess(t,holdTransaction,[f.root,mode]);
  assert.equal((await holder.next()).entered,true);
  const waiting=f.store.cleanupHistory({olderThanMs:0}).then(result=>({result}),error=>({error}));
  const reading=f.store.read('child');
  setTimeout(()=>holder.child.send({release:true}),100);
  const [outcome,record,done]=await Promise.all([waiting,reading,holder.next()]);
  assert.equal(outcome.error,undefined,outcome.error?.message);assert.equal(outcome.result.examined,2);
  assert.equal(record.state.run_id,'child');assert.equal(done.callbacks,1);
  assert.equal((await holder.closed).code,0);assert.equal(await f.store.writer.inspectWriter(),null);
});

test('admission owner death is visible, never taken over, and exact maintenance remains available',async t=>{
  const f=await fixture(t),holder=childProcess(t,holdTransaction,[f.root,'read']);
  assert.equal((await holder.next()).entered,true);
  const admission=new WorkflowStore(f.admission),owner=await admission.inspectWriter();
  holder.child.kill();await holder.closed;
  const before=await readFile(join(f.admission,'.writer.lock'),'utf8');
  await assert.rejects(f.store.read('child'),error=>{
    assert.equal(error.code,'RUN_STORE_ADMISSION_ORPHANED');assert.equal(error.owner_pid,owner.pid);
    assert.equal(error.lock_path,join(f.admission,'.writer.lock'));assert(!error.message.includes(owner.token));return true;
  });
  assert.equal(await readFile(join(f.admission,'.writer.lock'),'utf8'),before);
  await assert.rejects(admission.recoverWriter('wrong'),{code:'LOCK_OWNERSHIP'});
  await admission.recoverWriter(owner.token);
  // The killed reader's inner Run guard is intentionally still unknown. The
  // caller must inspect/recover that exact orphan too; admission cannot bless it.
  await assert.rejects(f.store.read('parent'),{code:'WORKFLOW_STORE_BUSY'});
  assert.equal((await f.store.read('child')).state.run_id,'child');
});

test('malformed, unreadable, and recovery admission locks fail without callbacks or mutation',async t=>{
  const f=await fixture(t),admission=new WorkflowStore(f.admission),lock=join(f.admission,'.writer.lock');
  const cases=[['{bad-json-token-should-not-leak','RUN_STORE_ADMISSION_MALFORMED'],
    [canonicalJSON({pid:process.pid,token:'unknown-owner'}),'RUN_STORE_ADMISSION_MALFORMED']];
  for(const [text,code] of cases){
    await writeFile(lock,text);let calls=0;
    await assert.rejects(admission.withRunAdmission(()=>{calls++;}),error=>{
      assert.equal(error.code,code);assert.equal(error.lock_path,lock);assert(!JSON.stringify(error).includes('unknown-owner'));
      assert(!error.message.includes('should-not-leak'));return true;
    });
    assert.equal(calls,0);assert.equal(await readFile(lock,'utf8'),text);await unlink(lock);
  }
  await mkdir(lock);await assert.rejects(admission.withRunAdmission(()=>assert.fail('no callback')),{code:'RUN_STORE_ADMISSION_READ_FAILED'});
  await rm(lock,{recursive:true});
  const recovery=join(f.admission,'.recovery.lock');await mkdir(recovery);
  await assert.rejects(admission.withRunAdmission(()=>assert.fail('no callback')),error=>{
    assert.equal(error.code,'RUN_STORE_ADMISSION_RECOVERY_REQUIRED');assert.equal(error.lock_path,recovery);return true;
  });
  await rm(recovery,{recursive:true});
});

test('a live admission owner causes a bounded timeout with small token-free diagnostics',async t=>{
  const f=await fixture(t),holder=childProcess(t,holdTransaction,[f.root,'read']);
  assert.equal((await holder.next()).entered,true);
  const admission=new WorkflowStore(f.admission),lock=join(f.admission,'.writer.lock');
  const owner=await admission.inspectWriter(),traces=[],before=await readFile(lock,'utf8');let calls=0;
  const started=performance.now();
  await assert.rejects(admission.withRunAdmission(()=>{calls++;},{timeoutMs:60,onWait:trace=>traces.push(trace)}),error=>{
    const elapsed=performance.now()-started;
    assert.equal(error.code,'RUN_STORE_ADMISSION_TIMEOUT');assert.equal(error.owner_pid,holder.child.pid);
    assert.equal(error.created_at,owner.created_at);assert(elapsed>=60&&elapsed<1000);
    // The queue floors its remaining writer budget; writer and outer-call
    // elapsed values have different origins, and diagnostics round down.
    assert(Number.isSafeInteger(error.waited_ms)&&error.waited_ms>=0&&error.waited_ms<=elapsed&&error.waited_ms<1000);
    assert.equal(error.lock_path,lock);assert(!JSON.stringify(error).includes(owner.token));return true;
  });
  assert.equal(calls,0);assert.equal(traces.length,1);assert.equal(traces[0].phase,'waiting');
  assert(!JSON.stringify(traces).includes(owner.token));assert.equal(await readFile(lock,'utf8'),before);
  holder.child.send({release:true});assert.equal((await holder.next()).done,true);assert.equal((await holder.closed).code,0);
});

test('an unverified owner PID fails explicitly instead of receiving wait or takeover authority',async t=>{
  const f=await fixture(t),admission=new WorkflowStore(f.admission),lock=join(f.admission,'.writer.lock');
  const owner={pid:process.pid,token:randomUUID(),created_at:new Date().toISOString()};await writeFile(lock,canonicalJSON(owner));
  const kill=process.kill;let calls=0;
  process.kill=(pid,signal)=>{if(pid===owner.pid&&signal===0)throw Object.assign(new Error('fixture permission denial'),{code:'EPERM'});return kill(pid,signal);};
  try {
    await assert.rejects(admission.withRunAdmission(()=>{calls++;}),error=>{
      assert.equal(error.code,'RUN_STORE_ADMISSION_OWNER_UNVERIFIED');assert.equal(error.owner_pid,owner.pid);assert.equal(error.cause.code,'EPERM');return true;
    });
  }finally{process.kill=kill;}
  assert.equal(calls,0);assert.equal(await readFile(lock,'utf8'),canonicalJSON(owner));await unlink(lock);
});

test('a recent empty admission owner gets only a bounded initialization window',async t=>{
  const f=await fixture(t),admission=new WorkflowStore(f.admission),lock=join(f.admission,'.writer.lock');
  await writeFile(lock,'');let calls=0;
  await assert.rejects(admission.withRunAdmission(()=>{calls++;},{initializationMs:60}),{code:'RUN_STORE_ADMISSION_INITIALIZATION_TIMEOUT'});
  assert.equal(calls,0);assert.equal(await readFile(lock,'utf8'),'');await unlink(lock);
  const owner={pid:process.pid,token:randomUUID(),created_at:new Date().toISOString()},traces=[];
  // Publish fully before admission; release only after the real live-owner wait
  // is observed, so slow fixture writes cannot exhaust empty-owner grace.
  await writeFile(lock,canonicalJSON(owner),{flag:'wx'});let released=false;
  const result=await admission.withRunAdmission(()=>{calls++;assert.equal(released,true);return 'once';},{onWait:async trace=>{
    traces.push(trace);
    if(trace.phase==='waiting'){
      assert.equal(calls,0);assert.equal(trace.owner_pid,owner.pid);assert.equal(trace.created_at,owner.created_at);
      assert.equal(await readFile(lock,'utf8'),canonicalJSON(owner));await unlink(lock);released=true;
    }
  }});
  assert.equal(result,'once');assert.equal(calls,1);assert.deepEqual(traces.map(trace=>trace.phase),['waiting','acquired']);
  assert(!JSON.stringify(traces).includes(owner.token));
});

test('outer admission does not wait for unknown inner guards or permit ordinary store waiting',async t=>{
  const f=await fixture(t),guard=join(f.store.runLockDirectory('parent'),'.writer.lock');
  await mkdir(f.store.runLockDirectory('parent'),{recursive:true});
  for(const owner of [{pid:process.pid,token:'external-owner'},{pid:2147483647,token:'stale-owner'}]){
    await writeFile(guard,canonicalJSON(owner));
    await assert.rejects(f.store.read('parent'),error=>{
      assert.equal(error.code,'WORKFLOW_STORE_BUSY');assert.equal(error.lock_path,guard);assert(error.message.includes(guard));return true;
    });
    assert.equal(await readFile(guard,'utf8'),canonicalJSON(owner));await unlink(guard);
  }
  assert.throws(()=>f.store.writer.withRunAdmission(()=>{}),{code:'RUN_STORE_ADMISSION_SCOPE'});
  const rootLock=join(f.root,'.writer.lock');await writeFile(rootLock,canonicalJSON({pid:process.pid,token:'external'}));
  assert.equal((await f.store.list()).length,2);
  await unlink(rootLock);
});

test('admitted callback failure releases ownership and never re-executes the callback',async t=>{
  const f=await fixture(t),admission=new WorkflowStore(f.admission);let calls=0;
  await assert.rejects(admission.withRunAdmission(()=>{calls++;throw new Error('transaction failed once');}),/transaction failed once/);
  assert.equal(calls,1);assert.equal(await admission.inspectWriter(),null);
  assert.equal(await admission.withRunAdmission(()=>{calls++;return 'next';}),'next');assert.equal(calls,2);
});

for (const mode of ['list', 'cleanupHistory']) test(`cross-process ${mode} exceeding five seconds leaves short Run admission available`, { timeout: 25000 }, async t => {
  const f = await fixture(t), pins = { resources: [], root: { workflow: { nodes: [] } } };
  for (let index = 0; index < 48; index++) {
    const id = `retained-${String(index).padStart(2, '0')}`;
    await f.store.create(id, pins, new Map(), { run_id: id, pins_hash: digest(canonicalJSON(pins)), status: 'running', nodes: {} });
  }
  const holder = childProcess(t, `
    import { WorkflowRunStore } from ${JSON.stringify(runModule)};
    import { WorkflowStore } from ${JSON.stringify(storeModule)};
    const s = new WorkflowRunStore(process.argv[1]), original = WorkflowStore.prototype.withWriter;
    if(process.argv[2]==='cleanupHistory'){
      const batch=s.readHistoryMetadataBatch.bind(s);
      s.readHistoryMetadataBatch=async(...args)=>{await new Promise(resolve=>setTimeout(resolve,500));return batch(...args);};
    }
    let reads = 0;
    if(process.argv[2]==='list'){
      const observe=s.observe.bind(s);
      s.observe=async id=>{if(++reads===1)process.send({reading:true});await new Promise(resolve=>setTimeout(resolve,500));return observe(id);};
    }
    WorkflowStore.prototype.withWriter = function(action) {
      if (process.argv[2]!=='list'&&this.root.startsWith(s.root) && this.root.endsWith('.run')) return original.call(this, async () => {
        if (++reads === 1) process.send({ reading: true });
        await new Promise(resolve => setTimeout(resolve, 120));
        return action();
      });
      return original.call(this, action);
    };
    const started = performance.now();
    const result = await s[process.argv[2]]();
    process.send({ done: true, reads, duration_ms: performance.now() - started, count: Array.isArray(result) ? result.length : result.examined });
    process.disconnect();
  `, [f.root, mode]);
  assert.equal((await holder.next()).reading, true);
  const started = performance.now();
  assert.equal((await f.store.read('parent')).state.run_id, 'parent');
  assert(performance.now() - started < 5000, 'an unrelated short read exceeded the unchanged admission timeout');
  const result = await holder.next();
  assert.equal(result.done, true); assert.equal(result.reads, 50); assert.equal(result.count, 50);
  assert(result.duration_ms > 5000, 'fixture must exercise history slower than the admission deadline');
  assert.equal((await holder.closed).code, 0);
});

const pausedAudit = `
  import { WorkflowRunStore } from ${JSON.stringify(runModule)};
  const s = new WorkflowRunStore(process.argv[1]), method=process.argv[4]==='cleanupHistory'?'readHistoryMetadataBatch':'observe',original=s[method].bind(s);
  let paused = false, reads = 0;
  s[method] = async (id, options) => {
    reads+=Array.isArray(id)?id.length:1;
    const pause = !paused && (Array.isArray(id)?id.includes(process.argv[2]):id===process.argv[2]);
    if (pause && process.argv[3] === 'before') {
      paused = true; process.send({ paused: true }); await new Promise(resolve => process.once('message', resolve));
    }
    const record = await original(id, options);
    if (pause && process.argv[3] === 'after') {
      paused = true; process.send({ paused: true }); await new Promise(resolve => process.once('message', resolve));
    }
    return record;
  };
  try { const result = await s[process.argv[4]]({ olderThanMs: 0 }); process.send({ result, reads }); }
  catch (error) { process.send({ failed: true, code: error.code, path: error.path, ticket_path: error.ticket_path, lock_path: error.lock_path, message: error.message, stack: error.stack }); }
  process.disconnect();
`;

test('cross-process child publication and acknowledgement restart before interpreting a mixed family', { timeout: 15000 }, async t => {
  const f = await fixture(t), parentId = 'family-parent', attemptId = 'family-attempt';
  const childId = `child-${digest([parentId, 'child', attemptId].join('\0')).slice(0, 58)}`;
  const pins = { resources: [], root: { workflow: { nodes: [{ id: 'child', type: 'subworkflow' }] } } };
  const parentState = { run_id: parentId, pins_hash: digest(canonicalJSON(pins)), status: 'failed', updated_at: '2020-01-01T00:00:00.000Z', nodes: {
    child: { status: 'failed', attempts: [{ id: attemptId, status: 'failed', child_run_id: childId,
      dispatch: { phase: 'intent', request_id: `subworkflow-${attemptId}`, receipt: null } }] },
  } };
  await f.store.create(parentId, pins, new Map(), parentState);
  const holder = childProcess(t, pausedAudit, [f.root, parentId, 'before', 'cleanupHistory']);
  assert.equal((await holder.next()).paused, true);
  const childPins = { ...pins, parent: { run_id: parentId, node_id: 'child', attempt_id: attemptId, pins_hash: parentState.pins_hash }, child_run_id: childId };
  await f.store.create(childId, childPins, new Map(), { run_id: childId, pins_hash: digest(canonicalJSON(childPins)), status: 'running', nodes: {} });
  await f.store.mutate(parentId, 'executor_event', state => {
    state.nodes.child.attempts[0].dispatch = { phase: 'acknowledged', receipt: { child_run_id: childId } };
  });
  holder.child.send({ release: true });
  const done = await holder.next(); assert.equal(done.failed, undefined, JSON.stringify(done));
  assert.equal(done.result.examined, 4); assert.deepEqual(done.result.deleted_run_ids, []);
  assert.equal(done.reads, 4); assert.equal((await holder.closed).code, 0);
});

test('cross-process recovery changing eligibility cannot commit an old terminal snapshot', { timeout: 15000 }, async t => {
  const f = await fixture(t), pins = { resources: [], root: { workflow: { nodes: [] } } }, id = 'recovering-terminal';
  await f.store.create(id, pins, new Map(), { run_id: id, pins_hash: digest(canonicalJSON(pins)), status: 'failed', updated_at: '2020-01-01T00:00:00.000Z', nodes: {} });
  const holder = childProcess(t, pausedAudit, [f.root, id, 'after', 'cleanupHistory']);
  assert.equal((await holder.next()).paused, true);
  await f.store.recover(id, state => { state.status = 'interrupted'; });
  holder.child.send({ release: true });
  const done = await holder.next(); assert.equal(done.failed, undefined);
  assert.deepEqual(done.result.deleted_run_ids, []); assert(done.result.preserved_run_ids.includes(id));
  assert(done.reads > 3); assert((await lstat(f.store.directory(id))).isDirectory());
  assert.equal((await holder.closed).code, 0);
});

for (const mode of ['list', 'cleanupHistory']) test(`cross-process purge during captured ${mode} is explicit or audited afresh`, { timeout: 15000 }, async t => {
  const f = await fixture(t), id = 'purged-authoring', pins = { resources: [], root: { workflow: { id: 'flow', nodes: [] }, revision_hash: 'revision',
    provenance: { kind: 'authoring_workflow_run', source_workflow_id: 'source', source_revision: 'source-revision' } } };
  await f.store.create(id, pins, new Map(), { run_id: id, pins_hash: digest(canonicalJSON(pins)), status: 'succeeded', updated_at: '2020-01-01T00:00:00.000Z', nodes: {} });
  const holder = childProcess(t, pausedAudit, [f.root, id, 'before', mode]);
  assert.equal((await holder.next()).paused, true);
  await f.store.purge(id, { expected_workflow_id: 'flow', expected_revision: 'revision', expected_source_workflow_id: 'source', expected_source_revision: 'source-revision' });
  holder.child.send({ release: true });
  const done = await holder.next();
  if (mode === 'list') { assert.equal(done.failed, true); assert.equal(done.code, 'ENOENT'); assert.equal(done.path, f.store.directory(id)); }
  else { assert.equal(done.failed, undefined); assert.equal(done.result.examined, 2); assert.deepEqual(done.result.deleted_run_ids, []); }
  assert.equal((await holder.closed).code, 0);
});

test('cross-process history refreshes only fully revalidated changed Runs during sustained publication', { timeout: 45000 }, async t => {
  const f = await fixture(t), pins = { resources: [], root: { workflow: { nodes: [] } } };
  for (let index = 0; index < 48; index++) {
    const id = `retained-${String(index).padStart(2, '0')}`;
    await f.store.create(id, pins, new Map(), { run_id: id, pins_hash: digest(canonicalJSON(pins)), status: 'running', nodes: {} });
  }
  const holder = childProcess(t, `
    import { WorkflowRunStore } from ${JSON.stringify(runModule)};
    import { WorkflowStore } from ${JSON.stringify(storeModule)};
    const s = new WorkflowRunStore(process.argv[1]), original = WorkflowStore.prototype.withWriter, read = s.readHistoryMetadataBatch.bind(s);
    const reads = {};
    s.readHistoryMetadataBatch = async (ids, options) => {
      for(const id of ids)reads[id]=(reads[id]??0)+1;
      if(ids.some(id=>reads[id]===1))await new Promise(resolve=>setTimeout(resolve,500));
      return read(ids,options);
    };
    let entered = false;
    WorkflowStore.prototype.withWriter = function(action) {
      if (this.root.startsWith(s.root) && this.root.endsWith('.run')) return original.call(this, async () => {
        if (!entered) { entered = true; process.send({ reading: true }); }
        await new Promise(resolve => setTimeout(resolve, 120)); return action();
      });
      return original.call(this, action);
    };
    const started = performance.now(), result = await s.cleanupHistory();
    process.send({ result, reads, duration_ms: performance.now() - started }); process.disconnect();
  `, [f.root]);
  assert.equal((await holder.next()).reading, true);
  let stopped = false, publications = 0;
  t.after(() => { stopped = true; });
  const publishing = (async () => {
    while (!stopped) {
      await f.store.mutate('child', 'executor_event', state => { state.heartbeat = ++publications; });
      // Model the real five-second worker receipt heartbeat with a faster
      // fixture cadence; this delay is only the external publisher's clock.
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  })();
  const done = await holder.next(); stopped = true; await publishing;
  assert.equal(done.result.examined, 50); assert.deepEqual(done.result.deleted_run_ids, []);
  assert(done.duration_ms > 5000); assert(publications >= 2);
  assert(done.reads.child > 1);
  for (const [id, count] of Object.entries(done.reads)) if (id !== 'child') assert.equal(count, 1, `${id} was unnecessarily revalidated`);
  assert.equal((await holder.closed).code, 0);
});

test('artifact, result and public authority writers invalidate only their exact audited Run', { timeout: 15000 }, async t => {
  const f = await fixture(t), holder = childProcess(t, pausedAudit, [f.root, 'child', 'after', 'cleanupHistory']);
  assert.equal((await holder.next()).paused, true);
  const witnessPath = join(f.root, '.run-locks', 'history-revision.json');
  const initial = JSON.parse(await readFile(witnessPath, 'utf8'));
  await f.store.saveArtifact('child', 'audit', Buffer.from('exact publication'));
  await f.store.saveExecutorResult('child', 'attempt', { accepted: true });
  await f.store.withRunWriter('child', () => writeFile(join(f.store.directory('child'), 'host-authority.json'), '{}'));
  const changed = JSON.parse(await readFile(witnessPath, 'utf8'));
  assert(changed.revision >= initial.revision + 3);
  assert.equal(changed.runs.parent, initial.runs.parent); assert(changed.runs.child > initial.runs.child);
  holder.child.send({ release: true });
  const done = await holder.next(); assert.equal(done.failed, undefined); assert.equal(done.reads, 3);
  assert.equal(done.result.preserved_count, 2); assert.equal((await holder.closed).code, 0);
});

test('complete candidate resource checks settle before failure while foreground admission remains available', { timeout: 15000 }, async t => {
  const f = await fixture(t), first = Buffer.from('first resource'), second = Buffer.from('second resource');
  const firstHash = digest(first), secondHash = digest(second), id = 'resource-failure';
  const pins = { resources: [{ sha256: firstHash, bytes: first.length }, { sha256: secondHash, bytes: second.length }], root: { workflow: { nodes: [] } } };
  await f.store.create(id, pins, new Map([[firstHash, first], [secondHash, second]]), { run_id: id, pins_hash: digest(canonicalJSON(pins)), status: 'succeeded',updated_at:'2020-01-01T00:00:00.000Z',nodes: {} });
  await writeFile(join(f.store.directory(id), 'objects', firstHash), 'corrupted');
  const holder = childProcess(t, `
    import fs from 'node:fs/promises';
    import { syncBuiltinESMExports } from 'node:module';
    import { join } from 'node:path';
    import { WorkflowRunStore } from ${JSON.stringify(runModule)};
    const s = new WorkflowRunStore(process.argv[1]), readFile = fs.readFile;
    const first = join(s.directory(process.argv[2]), 'objects', process.argv[3]), second = join(s.directory(process.argv[2]), 'objects', process.argv[4]);
    let entered, release;
    const ready = new Promise(resolve => entered = resolve), proceed = new Promise(resolve => release = resolve);
    process.once('message', release);
    fs.readFile = async (path, ...args) => {
      if (path === second) { entered(); process.send({ checking: true }); await proceed; }
      if (path === first) await ready;
      return readFile(path, ...args);
    };
    syncBuiltinESMExports();
    try { await s.cleanupHistory({olderThanMs:0}); process.send({ unexpected: true }); }
    catch (error) { process.send({ failed: true, code: error.code }); }
    process.disconnect();
  `, [f.root, id, firstHash, secondHash]);
  assert.equal((await holder.next()).checking, true);
  let settled = false;
  const waiting = f.store.read('parent').finally(() => { settled = true; });
  try{await Promise.race([waiting,new Promise(resolve=>setTimeout(resolve,500))]);assert.equal(settled,true);}
  finally{holder.child.send({ release: true });}
  assert.deepEqual(await holder.next(), { failed: true, code: 'RUN_RESOURCE_CORRUPT' });
  await waiting; assert.equal((await holder.closed).code, 0);
  assert.equal(await f.store.writer.inspectWriter(), null);
  await assert.rejects(lstat(join(f.store.directory(id), '.writer.lock')), { code: 'ENOENT' });
});

test('malformed or exhausted durable history revisions fence every subsequent writer', async t => {
  const f = await fixture(t), path = join(f.root, '.run-locks', 'history-revision.json');
  const original = await readFile(path, 'utf8'), journal = await readFile(join(f.store.directory('child'), 'events.jsonl'), 'utf8');
  for (const value of [{ schema_version: 1, revision: 1, runs: { child: 2 } },
    { schema_version: 1, revision: Number.MAX_SAFE_INTEGER, runs: { child: 1 } }]) {
    const text = canonicalJSON(value); await writeFile(path, text); let callbacks = 0;
    await assert.rejects(f.store.mutate('child', 'executor_event', () => { callbacks++; }),
      { code: value.revision === Number.MAX_SAFE_INTEGER ? 'RUN_HISTORY_REVISION_EXHAUSTED' : 'RUN_HISTORY_REVISION' });
    assert.equal(callbacks, 0); assert.equal(await readFile(path, 'utf8'), text);
    assert.equal(await readFile(join(f.store.directory('child'), 'events.jsonl'), 'utf8'), journal);
  }
  await writeFile(path, original); await f.store.read('child');
});
