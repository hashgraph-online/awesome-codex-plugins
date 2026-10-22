import test from 'node:test';
import assert from 'node:assert/strict';
import {spawn,execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {mkdtemp,rm,readFile,writeFile,rename,mkdir,unlink} from 'node:fs/promises';
import {join} from 'node:path';
import {tmpdir} from './physical-tempdir.mjs';
import {WorkflowStore} from '../lib/workflow-store.mjs';
import {inspectRunAdmissionQueue,recoverRunAdmissionTicket,commitAdmissionChoice} from '../lib/run-admission-queue.mjs';
import {randomUUID} from 'node:crypto';
const storeModule=new URL('../lib/workflow-store.mjs',import.meta.url).href;
test('peer lookup accepts the actual atomic choosing-to-numbered publication after a retired metadata snapshot',async t=>{
 const f=await fixture(t),directory=join(f.path,'.admission-queue'),pending=join(directory,'.pending');
 await mkdir(directory);await mkdir(pending);
 const ticket={id:randomUUID(),pid:process.pid,token:randomUUID(),created_at:new Date().toISOString(),number:1};
 const path=join(directory,`ticket-${ticket.id}.json`),temporary=join(pending,`ticket-${ticket.id}.json`);
 await writeFile(path,JSON.stringify({...ticket,number:0}));await writeFile(temporary,JSON.stringify(ticket));
 const queueModule=new URL('../lib/run-admission-queue.mjs',import.meta.url).href;
 const script=`import assert from 'node:assert/strict';import fs from 'node:fs/promises';import {syncBuiltinESMExports} from 'node:module';
  const path=process.argv[2],temporary=process.argv[3],ticket=JSON.parse(process.argv[4]),original=fs.lstat;let reads=0,publications=0,queue;
  fs.lstat=async(p,...args)=>{
   if(p===path&&++reads===2){
    const before=await original(p,...args);
    await queue.commitAdmissionChoice(path,temporary,ticket,{remaining:()=>1000,renameFile:async(a,b)=>{publications++;await fs.rename(a,b);}});
    // Complete the old lookup after the real atomic publication; the old inode
    // is retired, while its unique mutable name now holds the numbered ticket.
    before.nlink=0;return before;
   }return original(p,...args);
  };
  syncBuiltinESMExports();queue=await import(${JSON.stringify(queueModule)});
  const entries=await queue.inspectRunAdmissionQueue(process.argv[1]);
  assert.deepEqual(entries,[ticket]);assert.equal(publications,1);console.log('NUMBERED_PUBLICATION_OBSERVED');`;
 const result=await promisify(execFile)(process.execPath,['--input-type=module','-e',script,f.path,path,temporary,JSON.stringify(ticket)],{windowsHide:true});
 assert.equal(result.stdout.trim(),'NUMBERED_PUBLICATION_OBSERVED');
});

test('retired peer metadata refresh remains bounded and rejects invalid current tickets',async t=>{
 const f=await fixture(t),directory=join(f.path,'.admission-queue');await mkdir(directory);
 const ticket={id:randomUUID(),pid:process.pid,token:randomUUID(),created_at:new Date().toISOString(),number:1};
 const path=join(directory,`ticket-${ticket.id}.json`),queueModule=new URL('../lib/run-admission-queue.mjs',import.meta.url).href;
 for(const kind of ['directory','oversize','malformed','retired-again']){
  await rm(path,{recursive:true,force:true});await writeFile(path,JSON.stringify(ticket));
  const script=`import assert from 'node:assert/strict';import fs from 'node:fs/promises';import {syncBuiltinESMExports} from 'node:module';
   const path=process.argv[2],kind=process.argv[3],original=fs.lstat;let reads=0;
   fs.lstat=async(p,...args)=>{
    if(p===path){reads++;const info=await original(p,...args);
     if(reads===2){await fs.unlink(path);
      if(kind==='directory')await fs.mkdir(path);else await fs.writeFile(path,kind==='oversize'?'x'.repeat(4097):kind==='malformed'?'{bad':process.argv[4]);
      info.nlink=0;return info;}
     if(reads===3&&kind==='retired-again')info.nlink=0;
     return info;
    }return original(p,...args);
   };
   syncBuiltinESMExports();const {inspectRunAdmissionQueue}=await import(${JSON.stringify(queueModule)});
   await assert.rejects(inspectRunAdmissionQueue(process.argv[1]),{code:kind==='malformed'?'RUN_ADMISSION_QUEUE_MALFORMED':'RUN_ADMISSION_QUEUE_FILE'});
   assert.equal(reads,3);console.log('INVALID_CURRENT_TICKET_REJECTED');`;
  const result=await promisify(execFile)(process.execPath,['--input-type=module','-e',script,f.path,path,kind,JSON.stringify(ticket)],{windowsHide:true});
  assert.equal(result.stdout.trim(),'INVALID_CURRENT_TICKET_REJECTED');
 }
});

test('POSIX peer lookup observes a valid current ticket or confirms the retired path is gone',{skip:process.platform==='win32'},async t=>{
 const f=await fixture(t),directory=join(f.path,'.admission-queue');await mkdir(directory);
 const ticket={id:randomUUID(),pid:process.pid,token:randomUUID(),created_at:new Date().toISOString(),number:1};
 const path=join(directory,`ticket-${ticket.id}.json`),retired=join(f.path,'retired-ticket.json');
 const queueModule=new URL('../lib/run-admission-queue.mjs',import.meta.url).href;
 for(const replace of [false,true]){
  await writeFile(path,JSON.stringify(ticket));
  const script=`import fs from 'node:fs/promises';import {syncBuiltinESMExports} from 'node:module';
   const path=process.argv[2],retired=process.argv[3],original=fs.lstat;let reads=0;
   fs.lstat=async(p,...args)=>{
    if(p===path&&++reads===2){
     const file=await fs.open(path,'r');try{
      await fs.rename(path,retired);await fs.unlink(retired);const info=await file.stat();
      if(info.nlink!==0)throw new Error('Retired POSIX inode must have zero names');
      ${replace?'await fs.writeFile(path,process.argv[4]);':''}return info;
     }finally{await file.close();}
    }return original(p,...args);
   };
   syncBuiltinESMExports();const {inspectRunAdmissionQueue}=await import(${JSON.stringify(queueModule)});
   ${replace?`const entries=await inspectRunAdmissionQueue(process.argv[1]);if(JSON.stringify(entries)!==JSON.stringify([JSON.parse(process.argv[4])]))throw new Error('Current valid ticket was not observed');console.log('CURRENT_TICKET_OBSERVED');`:`const entries=await inspectRunAdmissionQueue(process.argv[1]);if(entries.length)throw new Error('Retired ticket survived');console.log('RETIRED_PATH_CONFIRMED');`}`;
  const result=await promisify(execFile)(process.execPath,['--input-type=module','-e',script,f.path,path,retired,JSON.stringify(ticket)],{windowsHide:true});
  assert.equal(result.stdout.trim(),replace?'CURRENT_TICKET_OBSERVED':'RETIRED_PATH_CONFIRMED');
 }
});

test('a denied ticket read preserves its original error with bounded presence evidence and no retry',async t=>{
 const f=await fixture(t),directory=join(f.path,'.admission-queue');await mkdir(directory);
 const ticket={id:randomUUID(),pid:process.pid,token:randomUUID(),created_at:new Date().toISOString(),number:1};
 const path=join(directory,`ticket-${ticket.id}.json`);await writeFile(path,JSON.stringify(ticket));
 const queueModule=new URL('../lib/run-admission-queue.mjs',import.meta.url).href;
 for(const removed of [false,true]){
  if(removed)await writeFile(path,JSON.stringify(ticket));
  const script=`import fs from 'node:fs/promises';import {syncBuiltinESMExports} from 'node:module';
   const path=process.argv[2],original=fs.readFile;let reads=0;
   const denied=Object.assign(new Error('Neutral ticket denial'),{code:'EPERM',path,syscall:'open'});
   fs.readFile=async(p,...args)=>{if(p===path){reads++;${removed?'await fs.unlink(path);':''}throw denied;}return original(p,...args);};
   syncBuiltinESMExports();const {inspectRunAdmissionQueue}=await import(${JSON.stringify(queueModule)});
   try{await inspectRunAdmissionQueue(process.argv[1]);throw new Error('Denied read was accepted');}
   catch(error){if(error!==denied)throw error;console.log(JSON.stringify({reads,code:error.code,details:error.details}));}`;
  const result=await promisify(execFile)(process.execPath,['--input-type=module','-e',script,f.path,path],{windowsHide:true});
  const actual=JSON.parse(result.stdout.trim());assert.equal(actual.reads,1);assert.equal(actual.code,'EPERM');
  assert.equal(actual.details?.phase,'ticket_read_failed');assert.equal(actual.details.ticket_exists,!removed);
  assert.equal(JSON.stringify(actual).includes(ticket.token),false);
 }
});
test('failed choice publication preserves staging whose ownership was changed',{timeout:15000},async t=>{
 const f=await fixture(t);
 const script=`import fs from 'node:fs/promises';import {syncBuiltinESMExports} from 'node:module';
 const rename=fs.rename;let staged;
 fs.rename=async(source,destination)=>{if(source.includes('.admission-queue')&&source.includes('.pending')){
  const value=JSON.parse(await fs.readFile(source,'utf8'));value.token='ffffffff-ffff-ffff-ffff-ffffffffffff';
  await fs.writeFile(source,JSON.stringify(value));staged=source;
  throw Object.assign(new Error('Neutral publication contention'),{code:'EPERM'});
 }return rename(source,destination);};syncBuiltinESMExports();
 const {WorkflowStore}=await import(${JSON.stringify(storeModule)});let callbacks=0,error;
 try{await new WorkflowStore(process.argv[1]).withRunAdmission(()=>callbacks++);}catch(cause){error=cause;}
 const value=JSON.parse(await fs.readFile(staged,'utf8'));
 console.log(JSON.stringify({callbacks,code:error?.code,causes:error?.errors?.map(e=>e.code),preserved:value.token==='ffffffff-ffff-ffff-ffff-ffffffffffff'}));`;
 const result=await promisify(execFile)(process.execPath,['--input-type=module','-e',script,f.path],{windowsHide:true});
 const actual=JSON.parse(result.stdout.trim());assert.equal(actual.callbacks,0);assert.equal(actual.preserved,true);
 assert.equal(actual.code,'RUN_ADMISSION_QUEUE_CLEANUP');assert(actual.causes.includes('RUN_ADMISSION_QUEUE_OWNERSHIP'));
});
async function choiceFixture(t){
 const root=await mkdtemp(join(tmpdir(),'admission-choice-'));t.after(()=>rm(root,{recursive:true,maxRetries:3,retryDelay:100}));
 const pending=join(root,'.pending');await mkdir(pending);
 const ticket={id:randomUUID(),pid:process.pid,token:randomUUID(),created_at:new Date().toISOString(),number:1};
 const path=join(root,`ticket-${ticket.id}.json`),temporary=join(pending,`ticket-${ticket.id}.json`);
 await writeFile(path,JSON.stringify({...ticket,number:0}));await writeFile(temporary,JSON.stringify(ticket));
 return {path,temporary,ticket};
}
test('Windows publication contention retries only the exact owned choice within admission deadline',async t=>{
 const f=await choiceFixture(t);let attempts=0,waits=0;
 await commitAdmissionChoice(f.path,f.temporary,f.ticket,{platform:'win32',remaining:()=>1000,
  onWait:trace=>{assert.equal(trace.phase,'publication_blocked');assert.equal(trace.cause_code,'EPERM');waits++;},
  renameFile:async(...args)=>{if(++attempts<3)throw Object.assign(new Error('Neutral reader-held destination'),{code:'EPERM'});return rename(...args);}});
 assert.equal(attempts,3);assert.equal(waits,1);assert.equal(JSON.parse(await readFile(f.path,'utf8')).number,1);
});
test('publication contention cannot replace a ticket after its owner changes',async t=>{
 const f=await choiceFixture(t);let attempts=0;
 await assert.rejects(commitAdmissionChoice(f.path,f.temporary,f.ticket,{platform:'win32',remaining:()=>1000,
  renameFile:async()=>{attempts++;await writeFile(f.path,JSON.stringify({...f.ticket,token:randomUUID(),number:0}));
   throw Object.assign(new Error('Neutral contention'),{code:'EPERM'});}}),{code:'RUN_ADMISSION_QUEUE_OWNERSHIP'});
 assert.equal(attempts,1);assert.notEqual(JSON.parse(await readFile(f.path,'utf8')).token,f.ticket.token);
});
test('publication contention reports deadline failure and never retries permission errors on other platforms',async t=>{
 const f=await choiceFixture(t),blocked=Object.assign(new Error('Neutral permission error'),{code:'EPERM'});let attempts=0;
 await assert.rejects(commitAdmissionChoice(f.path,f.temporary,f.ticket,{platform:'linux',remaining:()=>1000,
  renameFile:async()=>{attempts++;throw blocked;}}),error=>error===blocked);assert.equal(attempts,1);
 await assert.rejects(commitAdmissionChoice(f.path,f.temporary,f.ticket,{platform:'win32',
  remaining:()=>{if(attempts>1)throw Object.assign(new Error('Neutral expired deadline'),{code:'RUN_STORE_ADMISSION_TIMEOUT'});return 10;},
  renameFile:async()=>{attempts++;throw blocked;}}),error=>{
    assert.equal(error.code,'RUN_ADMISSION_QUEUE_PUBLICATION_TIMEOUT');assert.equal(error.errors[0],blocked);return true;});
 assert.equal(JSON.parse(await readFile(f.path,'utf8')).number,0);
});
async function fixture(t){const root=await mkdtemp(join(tmpdir(),'fair-run-admission-'));
 t.after(()=>rm(root,{recursive:true,maxRetries:3,retryDelay:100}));
 const path=join(root,'.run-locks','.store-operation');return {path,store:await new WorkflowStore(path).initialize()};}
function child(t,path,label){
 const worker=spawn(process.execPath,['--input-type=module','-e',`
 import {WorkflowStore} from ${JSON.stringify(storeModule)};
 const store=new WorkflowStore(process.argv[1]),label=process.argv[2];let reported=false;
 try {await store.withRunAdmission(async()=>{
  process.send({entered:true,label});await new Promise(resolve=>process.once('message',resolve));
 },{onWait:trace=>{if(!reported){reported=true;process.send({queued:true,label});}}});
 process.send({done:true,label});}catch(error){process.send({failed:true,code:error.code,message:error.message,path:error.path,ticket_path:error.ticket_path,lock_path:error.lock_path,stack:error.stack});}
 process.disconnect();`,path,label],{windowsHide:true,stdio:['ignore','pipe','pipe','ipc']});
 let stderr='';worker.stderr.on('data',data=>stderr+=data);
 const inbox=[],waiters=[];worker.on('message',message=>{const waiter=waiters.shift();if(waiter)waiter.resolve(message);else inbox.push(message);});
 const closed=new Promise(resolve=>worker.once('exit',(code,signal)=>{for(const waiter of waiters.splice(0))waiter.reject(new Error(`Child exited ${code}/${signal}: ${stderr}`));resolve({code,signal});}));
 t.after(async()=>{if(worker.exitCode===null&&worker.signalCode===null)worker.kill();await closed;});
 return {worker,closed,next:()=>inbox.length?Promise.resolve(inbox.shift()):new Promise((resolve,reject)=>waiters.push({resolve,reject}))};
}
test('ordered cross-process waiters enter once in queue order without replacement callbacks',{timeout:15000},async t=>{
 const f=await fixture(t),holder=child(t,f.path,'holder');assert.equal((await holder.next()).entered,true);
 const workers=[];
 for(const label of ['first','second','third']){const worker=child(t,f.path,label);const message=await worker.next();assert.equal(message.queued,true,JSON.stringify(message));workers.push(worker);}
 holder.worker.send({release:true});assert.equal((await holder.next()).done,true);
 for(let i=0;i<workers.length;i++){
  assert.deepEqual(await workers[i].next(),{entered:true,label:['first','second','third'][i]});
  workers[i].worker.send({release:true});assert.equal((await workers[i].next()).done,true);
 }
 for(const worker of [holder,...workers])assert.equal((await worker.closed).code,0);
 assert.deepEqual(await inspectRunAdmissionQueue(f.path),[]);assert.equal(await f.store.inspectWriter(),null);
});

test('a peer waits for a live chooser blocked beyond empty-file initialization without replaying its callback',{timeout:15000},async t=>{
 const f=await fixture(t),directory=join(f.path,'.admission-queue');await mkdir(join(directory,'.pending'),{recursive:true});
 const ticket={id:'00000000-0000-0000-0000-000000000000',pid:process.pid,token:randomUUID(),created_at:new Date().toISOString(),number:1};
 const path=join(directory,`ticket-${ticket.id}.json`),temporary=join(directory,'.pending',`ticket-${ticket.id}.json`);
 await writeFile(path,JSON.stringify({...ticket,number:0}));await writeFile(temporary,JSON.stringify(ticket));
 const peer=child(t,f.path,'peer');const queued=await peer.next();assert.equal(queued.queued,true,JSON.stringify(queued));
 let attempts=0;await commitAdmissionChoice(path,temporary,ticket,{platform:'win32',remaining:()=>1000,
  renameFile:async(...args)=>{if(++attempts===1){await new Promise(resolve=>setTimeout(resolve,350));
    throw Object.assign(new Error('Neutral reader contention'),{code:'EPERM'});}return rename(...args);}});
 await unlink(path);const entered=await peer.next();assert.equal(entered.entered,true,JSON.stringify(entered));
 peer.worker.send({release:true});assert.equal((await peer.next()).done,true);assert.equal((await peer.closed).code,0);
 assert.deepEqual(await inspectRunAdmissionQueue(f.path),[]);
});
test('dead queued owner fences callbacks until exact token recovery and never recovers the active writer',{timeout:15000},async t=>{
 const f=await fixture(t),holder=child(t,f.path,'holder');assert.equal((await holder.next()).entered,true);
 const waiter=child(t,f.path,'doomed');assert.equal((await waiter.next()).queued,true);
 const queued=await inspectRunAdmissionQueue(f.path),owned=queued.find(q=>q.pid===waiter.worker.pid);assert(owned);
 waiter.worker.kill();await waiter.closed;let callbacks=0;
 await assert.rejects(f.store.withRunAdmission(()=>callbacks++),error=>{
  assert.equal(error.code,'RUN_ADMISSION_QUEUE_ORPHANED');assert.equal(error.owner_pid,owned.pid);
  assert(!JSON.stringify(error).includes(owned.token));assert(!error.ticket_path.includes(owned.token));return true;
 });
 assert.equal(callbacks,0);
 await assert.rejects(recoverRunAdmissionTicket(f.path,owned.id,'wrong'),{code:'RUN_ADMISSION_QUEUE_OWNERSHIP'});
 await recoverRunAdmissionTicket(f.path,owned.id,owned.token);
 assert.equal((await f.store.inspectWriter()).pid,holder.worker.pid);
 holder.worker.send({release:true});assert.equal((await holder.next()).done,true);await holder.closed;
 assert.equal(await f.store.withRunAdmission(()=>++callbacks),1);assert.deepEqual(await inspectRunAdmissionQueue(f.path),[]);
});
test('queued ticket corruption stays visible and only the callers own ticket is cleaned',{timeout:15000},async t=>{
 const f=await fixture(t),holder=child(t,f.path,'holder');assert.equal((await holder.next()).entered,true);
 const waiter=child(t,f.path,'tampered');assert.equal((await waiter.next()).queued,true);
 const own=(await inspectRunAdmissionQueue(f.path)).find(q=>q.pid===waiter.worker.pid);
 const path=join(f.path,'.admission-queue',`ticket-${own.id}.json`);await writeFile(path,'{bad');let callbacks=0;
 await assert.rejects(f.store.withRunAdmission(()=>callbacks++),{code:'RUN_ADMISSION_QUEUE_MALFORMED'});
 assert.equal(callbacks,0);assert.equal(await readFile(path,'utf8'),'{bad');
 waiter.worker.kill();await waiter.closed;holder.worker.send({release:true});assert.equal((await holder.next()).done,true);await holder.closed;
});
