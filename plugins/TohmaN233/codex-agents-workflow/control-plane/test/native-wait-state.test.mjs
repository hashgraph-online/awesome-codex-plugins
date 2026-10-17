import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {syncBuiltinESMExports} from 'node:module';
import {spawn} from 'node:child_process';
import {join} from 'node:path';
import {tmpdir} from './physical-tempdir.mjs';
import {WorkflowRunStore} from '../lib/workflow-run-store.mjs';
import {canonicalJSON,digest} from '../lib/workflow-revisions.mjs';

const native={...fs};
test('single Run wait observation never acquires writer admission',async t=>{
  const f=await fixture(t),opened=[];
  fs.open=async(path,flags,...args)=>{if(flags==='wx')opened.push(String(path));return native.open(path,flags,...args);};syncBuiltinESMExports();
  try{await f.store.readNativeWaitState(f.id);}finally{fs.open=native.open;syncBuiltinESMExports();}
  assert.deepEqual(opened,[],'Pure single-Run observation acquired a writer lock');
});
async function fixture(t){
  const root=await fs.mkdtemp(join(tmpdir(),'native-wait-state-'));
  t.after(()=>native.rm(root,{recursive:true,force:true}));
  const store=await new WorkflowRunStore(root).initialize(),id='native-wait-fixture',blobs=new Map(),resources=[];
  for(let i=0;i<73;i++){const bytes=Buffer.from('immutable resource '+i),sha256=digest(bytes);blobs.set(sha256,bytes);resources.push({sha256,bytes:bytes.length});}
  const pins={resources,root:{workflow:{nodes:[]}}};
  await store.create(id,pins,blobs,{run_id:id,pins_hash:digest(canonicalJSON(pins)),status:'running',nodes:{},constraints:{},control_hash:'first'});
  return {root,store,id,resources};
}

test('native wait reads every current journal/pin but no unrelated resource object',async t=>{
  const f=await fixture(t),reads=[];
  fs.readFile=async(path,...args)=>{reads.push(String(path));return native.readFile(path,...args);};syncBuiltinESMExports();
  try{
    const result=await f.store.readNativeWaitState(f.id);
    assert.deepEqual(Object.keys(result).sort(),['events','sequence','state']);
    assert(reads.some(path=>path.endsWith('events.jsonl')));assert(reads.some(path=>path.endsWith('pins.json')));
    assert(!reads.some(path=>path.includes('objects')));
    await f.store.mutate(f.id,'control_recovery',state=>{state.control_hash='second';});
    reads.length=0;const fresh=await f.store.readNativeWaitState(f.id);
    assert.equal(fresh.state.control_hash,'second');assert.equal(fresh.sequence,result.sequence+1);
    assert(!reads.some(path=>path.includes('objects')));
  }finally{fs.readFile=native.readFile;syncBuiltinESMExports();}
});

test('unconsumed resource corruption permits state reads and cancellation but fails explicit audit',async t=>{
  const f=await fixture(t);
  await fs.writeFile(join(f.store.directory(f.id),'objects',f.resources[0].sha256),'corrupt inventory');
  assert.equal((await f.store.readNativeWaitState(f.id)).state.status,'running');
  assert.equal((await f.store.read(f.id)).state.status,'running');
  await f.store.mutate(f.id,'cancel',state=>{state.status='cancelled';});
  assert.equal((await f.store.read(f.id)).state.status,'cancelled');
  await assert.rejects(f.store.audit(f.id),{code:'RUN_RESOURCE_CORRUPT'});
});

test('native wait cannot hide corrupt journal or pin bytes',async t=>{
  for(const field of ['events.jsonl','pins.json'])await t.test(field,async t=>{
    const f=await fixture(t),path=join(f.store.directory(f.id),field);
    if(field==='pins.json'){const pins=JSON.parse(await fs.readFile(path));pins.resources=[];await fs.writeFile(path,canonicalJSON(pins));}
    else {const row=JSON.parse((await fs.readFile(path,'utf8')).trim());row.payload.state.control_hash='forged';await fs.writeFile(path,canonicalJSON(row)+'\n');}
    await assert.rejects(f.store.readNativeWaitState(f.id),{code:field==='pins.json'?'RUN_PINS_CORRUPT':'RUN_JOURNAL_CORRUPT'});
  });
});

test('cancelled and recovered authority state is immediately visible to the next held-wait check',async t=>{
  const f=await fixture(t);
  await f.store.mutate(f.id,'cancel',state=>{state.status='cancelled';});
  assert.equal((await f.store.readNativeWaitState(f.id)).state.status,'cancelled');
  await f.store.mutate(f.id,'control_recovery',state=>{state.control_hash='recovered';});
  assert.equal((await f.store.readNativeWaitState(f.id)).state.control_hash,'recovered');
});

test('native wait rereads inside its already-owned Run writer without nesting another lock',async t=>{
  const f=await fixture(t);let timer;
  try{
    const result=await Promise.race([f.store.withRunWriter(f.id,()=>f.store.readNativeWaitState(f.id)),
      new Promise((_,reject)=>timer=setTimeout(()=>reject(new Error('Native state read deadlocked inside its owned writer')),3000))]);
    assert.equal(result.state.run_id,f.id);assert.equal(result.state.control_hash,'first');
  }finally{clearTimeout(timer);}
});

test('native wait observes committed state without blocking a real other-process writer',{timeout:15000},async t=>{
  const f=await fixture(t),module=new URL('../lib/workflow-run-store.mjs',import.meta.url).href,
    eventModule=new URL('../lib/workflow-events.mjs',import.meta.url).href;
  const code=`const {WorkflowRunStore}=await import(${JSON.stringify(module)});
    const {readEvents,replayEvents,statePatch,appendEvent}=await import(${JSON.stringify(eventModule)});
    const {join}=await import('node:path');
    const store=new WorkflowRunStore(process.argv[1]);
    await store.withRunWriter('native-wait-fixture',async()=>{
      process.send({phase:'owned'});await new Promise(resolve=>process.once('message',resolve));
      const path=join(store.directory('native-wait-fixture'),'events.jsonl'),{events}=await readEvents(path);
      const before=replayEvents(events),after={...before,control_hash:'cross-process'};
      await appendEvent(path,events,'control_recovery',{patch:statePatch(before,after)});
    });
    process.send({phase:'committed'});process.disconnect();`;
  const child=spawn(process.execPath,['--input-type=module','-e',code,f.root],{windowsHide:true,stdio:['ignore','ignore','pipe','ipc']});
  let stderr='';child.stderr.on('data',chunk=>stderr+=chunk);
  const messages=[],waiters=[];
  child.on('message',message=>{const waiter=waiters.shift();if(waiter)waiter(message);else messages.push(message);});
  const next=()=>messages.length?Promise.resolve(messages.shift()):new Promise(resolve=>waiters.push(resolve));
  const closed=new Promise((resolve,reject)=>{child.once('error',reject);child.once('exit',(code,signal)=>resolve({code,signal}));});
  t.after(async()=>{if(child.exitCode===null&&child.signalCode===null)child.kill();await closed;});
  assert.equal((await next()).phase,'owned');
  assert.equal((await f.store.readNativeWaitState(f.id)).state.control_hash,'first');
  child.send({release:true});
  assert.equal((await next()).phase,'committed');
  assert.deepEqual(await closed,{code:0,signal:null},stderr);
  assert.equal((await f.store.readNativeWaitState(f.id)).state.control_hash,'cross-process');
});

for(const kind of ['malformed','orphan','recovery'])test('native observation bypasses '+kind+' ownership while writers remain fenced',async t=>{
 const f=await fixture(t),directory=f.store.runLockDirectory(f.id);await fs.mkdir(directory,{recursive:true});
 const path=join(directory,kind==='recovery'?'.recovery.lock':'.writer.lock');
 await fs.writeFile(path,kind==='malformed'?'not-json':JSON.stringify({pid:99999999,token:'11111111-1111-4111-8111-111111111111',created_at:new Date().toISOString()}));
 const marker=await fs.readFile(path,'utf8');
 assert.equal((await f.store.readNativeWaitState(f.id)).state.control_hash,'first');
 let entered=false;
 await assert.rejects(f.store.withRunWriter(f.id,()=>{entered=true;}),{code:'WORKFLOW_STORE_BUSY'});
 assert.equal(entered,false);assert.equal(await fs.readFile(path,'utf8'),marker);
});
