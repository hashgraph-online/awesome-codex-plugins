import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {syncBuiltinESMExports} from 'node:module';
import {join} from 'node:path';
import {tmpdir} from './physical-tempdir.mjs';
import {WorkflowRunStore} from '../lib/workflow-run-store.mjs';
import {canonicalJSON,digest,LIMITS} from '../lib/workflow-revisions.mjs';
import {readStartedEvent} from '../lib/workflow-events.mjs';
import {noSymlinks,statNoSymlinks} from '../lib/workflow-paths.mjs';

const native={...fs};
const thread='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa';
const other='bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb';
function latch(){let resolve;const promise=new Promise(done=>resolve=done);return {promise,resolve};}
const fileProxy=(file,overrides)=>new Proxy(file,{get(target,key){if(key in overrides)return overrides[key];const value=Reflect.get(target,key);return typeof value==='function'?value.bind(target):value;}});
async function bounded(promise){let timer;try{return await Promise.race([promise,new Promise((_,reject)=>{
  timer=setTimeout(()=>reject(new Error('Expected mechanical latch did not enter')),1500);
})]);}finally{clearTimeout(timer);}}
async function patched(overrides,action){Object.assign(fs,overrides);syncBuiltinESMExports();
  try{return await action();}finally{for(const key of Object.keys(overrides))fs[key]=native[key];syncBuiltinESMExports();}}
async function fixture(t,{count=1,resources=0,matches=[]}={}){
  const root=await native.mkdtemp(join(tmpdir(),'io-audit-prefetch-'));t.after(()=>native.rm(root,{recursive:true,force:true}));
  const store=await new WorkflowRunStore(root).initialize(),ids=[];
  for(let i=0;i<count;i++){
    const id='record-'+String(i).padStart(2,'0'),blobs=new Map(),manifest=[];ids.push(id);
    for(let j=0;j<resources;j++){const bytes=Buffer.from('pinned resource '+j),sha256=digest(bytes);blobs.set(sha256,bytes);manifest.push({sha256,bytes:bytes.length});}
    const pins={resources:manifest,root:{workflow:{nodes:[]}}};
    await store.create(id,pins,blobs,{run_id:id,pins_hash:digest(canonicalJSON(pins)),status:'running',nodes:{},constraints:{native_parent_thread_id:matches.includes(i)?thread:other}});
  }
  return {root,store,ids};
}
test('one full 67-resource audit uses each walked leaf stat once and a second audit stays fresh',async t=>{
  const f=await fixture(t,{resources:67}),directory=f.store.directory(f.ids[0]);
  const files=[join(directory,'events.jsonl'),join(directory,'pins.json'),...(await native.readdir(join(directory,'objects'))).map(name=>join(directory,'objects',name))];
  const counts=new Map();
  await patched({lstat:async(path,...args)=>{if(files.includes(path))counts.set(path,(counts.get(path)??0)+1);return native.lstat(path,...args);}},async()=>{
    await f.store.audit(f.ids[0]);assert.equal([...counts.values()].reduce((a,b)=>a+b,0),69);
    assert(files.every(path=>counts.get(path)===1));
    counts.clear();await f.store.audit(f.ids[0]);assert.equal([...counts.values()].reduce((a,b)=>a+b,0),69);
    await native.writeFile(files[2],'tampered second fresh audit');
    await assert.rejects(f.store.audit(f.ids[0]),{code:'RUN_RESOURCE_CORRUPT'});
  });
});
test('locator metadata holds at most four slots until ordered consumption and serial candidate validation advance',async t=>{
  const f=await fixture(t,{count:8,matches:[0,1,6]}),release=latch(),four=latch(),candidateEntered=latch(),candidateRelease=latch();
  let active=0,max=0;const started=[],full=[];
  const originalRead=f.store.observe.bind(f.store);f.store.observe=async id=>{full.push(id);if(id===f.ids[0]){candidateEntered.resolve();await candidateRelease.promise;}return originalRead(id);};
  let lookup;
  await patched({open:async(path,flags,...args)=>{
    if(flags==='r'&&path.endsWith('events.jsonl')){
      const id=f.ids.find(id=>path===join(f.store.directory(id),'events.jsonl'));
      started.push(id);active++;max=Math.max(max,active);if(started.length===4)four.resolve();
      try{await release.promise;const file=await native.open(path,flags,...args);
        return fileProxy(file,{close:async()=>{try{return await file.close();}finally{active--;}}});
      }catch(error){active--;throw error;}
    }return native.open(path,flags,...args);
  }},async()=>{
    const pending=f.store.listForThread(thread,{onLookup:detail=>lookup=detail});
    let latchError;
    try{await bounded(four.promise);assert.equal(started.length,4);assert.equal(full.length,0);assert.equal(max,4);}
    catch(error){latchError=error;}
    finally{release.resolve();}
    try{await bounded(candidateEntered.promise);assert.equal(started.length,4,'settled later locators cannot replenish before the ordered candidate finishes');}
    catch(error){latchError??=error;}
    finally{candidateRelease.resolve();}
    const results=await pending;
    if(latchError)throw latchError;
    assert.deepEqual(results.map(item=>item.state.run_id),[f.ids[0],f.ids[1],f.ids[6]]);
    assert.deepEqual(full,[f.ids[0],f.ids[1],f.ids[6]]);assert.equal(max,4);
    assert.equal(lookup.inspected_start_records,8);assert.equal(lookup.fully_validated_candidates,3);
  });
});

test('stat walk keeps noSymlinks path contract and returns fresh leaf Stats including boundary itself',async t=>{
  const f=await fixture(t),path=join(f.root,'probe');await native.writeFile(path,'a');
  const first=await statNoSymlinks(path);assert.equal(first.path,path);assert.equal(first.stat.size,1);
  assert.equal(await noSymlinks(path),path);
  await native.writeFile(path,'longer');assert.equal((await statNoSymlinks(path)).stat.size,6);assert.equal(first.stat.size,1);
  assert((await statNoSymlinks(tmpdir())).stat.isDirectory());
});

for(const target of ['events.jsonl','pins.json','resource'])for(const fault of ['missing','directory','oversize','symlink'])
test(`${target} ${fault} still fences the complete fresh audit before reading invalid bytes`,async t=>{
  const f=await fixture(t,{resources:1}),directory=f.store.directory(f.ids[0]);
  const path=target==='resource'?join(directory,'objects',(await native.readdir(join(directory,'objects')))[0]):join(directory,target);
  if(fault==='oversize'){await native.truncate(path,target==='events.jsonl'?128*1024*1024+1:target==='pins.json'?16*1024*1024+1:LIMITS.resource+1);}
  else {await native.unlink(path);if(fault==='directory')await native.mkdir(path);
    if(fault==='symlink'){const external=join(f.root,'external-target');await native.mkdir(external);await native.symlink(external,path,process.platform==='win32'?'junction':'dir');}}
  let reads=0;
  await patched({readFile:async(p,...args)=>{if(p===path)reads++;return native.readFile(p,...args);}},async()=>{
    await assert.rejects(f.store.audit(f.ids[0]),{code:fault==='missing'?'ENOENT':fault==='symlink'?'WORKFLOW_SYMLINK':target==='events.jsonl'?'RUN_JOURNAL_LIMIT':target==='pins.json'?'RUN_PINS_LIMIT':'RUN_RESOURCE'});
    assert.equal(reads,0);
  });
});

test('fresh full audits retain journal/pins/resource hash and ancestor symlink fences',async t=>{
  for(const target of ['journal','pins','resource','ancestor']){
    const f=await fixture(t,{resources:1}),directory=f.store.directory(f.ids[0]);
    if(target==='journal'){const path=join(directory,'events.jsonl'),value=JSON.parse(await native.readFile(path,'utf8'));value.hash='0'.repeat(64);await native.writeFile(path,canonicalJSON(value)+'\n');}
    if(target==='pins')await native.writeFile(join(directory,'pins.json'),'{}');
    if(target==='resource')await native.writeFile(join(directory,'objects',(await native.readdir(join(directory,'objects')))[0]),'different bytes');
    if(target==='ancestor'){const objects=join(directory,'objects'),external=join(f.root,'outside-objects');await native.rename(objects,external);await native.symlink(external,objects,process.platform==='win32'?'junction':'dir');}
    await assert.rejects(f.store.audit(f.ids[0]),{code:{journal:'RUN_JOURNAL_CORRUPT',pins:'RUN_PINS_CORRUPT',resource:'RUN_RESOURCE_CORRUPT',ancestor:'WORKFLOW_SYMLINK'}[target]});
  }
});

test('locator keeps the actual opened handle stat and always closes it on rejection',async t=>{
  const f=await fixture(t),path=join(f.store.directory(f.ids[0]),'events.jsonl');let stats=0,reads=0,closes=0;
  await patched({open:async(p,...args)=>{
    const file=await native.open(p,...args);if(p!==path)return file;
    return fileProxy(file,{stat:async()=>{stats++;return {isFile:()=>true,size:128*1024*1024+1};},
      read:async(...values)=>{reads++;return file.read(...values);},close:async()=>{closes++;return file.close();}});
  }},async()=>{await assert.rejects(readStartedEvent(path),{code:'RUN_JOURNAL_LIMIT'});});
  assert.equal(stats,1);assert.equal(reads,0);assert.equal(closes,1);
});

for(const early of ['candidate','locator'])test(`ordered ${early} failure drains its handles while independent writes remain available`,async t=>{
  const f=await fixture(t,{count:8,matches:[0,1]}),laterOpened=latch(),closeEntered=latch(),releaseClose=latch(),primarySeen=latch();
  await native.writeFile(join(f.store.directory(early==='candidate'?f.ids[0]:f.ids[1]),'pins.json'),'{}');
  const badStart=join(f.store.directory(early==='candidate'?f.ids[2]:f.ids[0]),'events.jsonl');
  const start=JSON.parse(await native.readFile(badStart,'utf8'));start.hash='0'.repeat(64);await native.writeFile(badStart,canonicalJSON(start)+'\n');
  const full=[],locatorIds=[],originalRead=f.store.observe.bind(f.store);let callbacks=0,settled=false,mutationEntered=false;
  f.store.observe=async id=>{full.push(id);try{return await originalRead(id);}catch(error){primarySeen.resolve();throw error;}};
  await patched({open:async(path,flags,...args)=>{
    const index=f.ids.findIndex(id=>path===join(f.store.directory(id),'events.jsonl'));
    if(flags!=='r'||index<0)return native.open(path,flags,...args);
    locatorIds.push(f.ids[index]);
    const file=await native.open(path,flags,...args);
    if(index===0&&early==='locator')return fileProxy(file,{close:async()=>{await laterOpened.promise;primarySeen.resolve();return file.close();}});
    if(index===3){laterOpened.resolve();return fileProxy(file,{close:async()=>{closeEntered.resolve();await releaseClose.promise;return file.close();}});}
    return file;
  }},async()=>{
    const outcome=f.store.listForThread(thread,{onLookup:()=>callbacks++}).then(value=>({value}),error=>({error})).finally(()=>settled=true);
    let mutation;
    try{
      await bounded(primarySeen.promise);await bounded(closeEntered.promise);
      assert.equal(settled,false);
      await assert.rejects(native.lstat(join(f.root,'.writer.lock')),{code:'ENOENT'});
      await assert.rejects(native.lstat(join(f.root,'.run-locks','.store-operation','.writer.lock')),{code:'ENOENT'});
      mutation=f.store.mutate(f.ids[7],'pause',state=>{mutationEntered=true;state.fixture_changed=true;});
      await bounded(mutation);assert.equal(mutationEntered,true);assert.equal(settled,false);
    }finally{releaseClose.resolve();}
    const result=await outcome;if(mutation)await mutation;
    assert.equal(callbacks,0);assert.equal(mutationEntered,true);
    assert.deepEqual([...locatorIds].sort(),f.ids.slice(0,4),'no later metadata is admitted after the ordered fault');
    if(early==='candidate'){
      assert(result.error instanceof AggregateError);assert.equal(result.error.code,'RUN_PINS_CORRUPT');
      assert.equal(result.error.errors[0].code,'RUN_PINS_CORRUPT');assert.equal(result.error.errors[1].code,'RUN_JOURNAL_CORRUPT');assert.equal(result.error.cause,result.error.errors[0]);
      assert.deepEqual(full,[f.ids[0]],'only the first candidate enters observation');
    }else {assert(!(result.error instanceof AggregateError));assert.equal(result.error.code,'RUN_JOURNAL_CORRUPT');assert.deepEqual(full,[],'later corrupt candidate is never fully read');}
    await assert.rejects(native.lstat(join(f.root,'.writer.lock')),{code:'ENOENT'});
  });
});

test('controller filtering ignores noncandidate pins, and diagnostic callback remains once after ownership release',async t=>{
  const f=await fixture(t,{count:3,matches:[1]});await native.writeFile(join(f.store.directory(f.ids[0]),'pins.json'),'corrupt unrelated pins');
  let calls=0;
  const result=await f.store.listForThread(thread,{onLookup:async detail=>{
    calls++;assert.equal(detail.inspected_start_records,3);assert.equal(detail.fully_validated_candidates,1);
    await assert.rejects(native.lstat(join(f.root,'.writer.lock')),{code:'ENOENT'});
  }});
  assert.equal(calls,1);assert.deepEqual(result.map(item=>item.state.run_id),[f.ids[1]]);
  const original=Object.assign(new Error('original callback rejected'),{code:'LOOKUP_CALLBACK'});
  await assert.rejects(f.store.listForThread(thread,{onLookup:()=>{throw original;}}),error=>error===original);
  await assert.rejects(f.store.listForThread('unauthenticated'),{code:'MODEL_THREAD_ID'});
});

test('a falsy original locator rejection is preserved ahead of additional admitted IO failure',async t=>{
  const f=await fixture(t,{count:4}),later=Object.assign(new Error('later real IO failure'),{code:'LATER_IO'});
  await patched({open:async(path,flags,...args)=>{
    if(flags==='r'&&path===join(f.store.directory(f.ids[0]),'events.jsonl'))throw null;
    if(flags==='r'&&path===join(f.store.directory(f.ids[2]),'events.jsonl'))throw later;
    return native.open(path,flags,...args);
  }},async()=>{
    await assert.rejects(f.store.listForThread(thread),error=>{
      assert(error instanceof AggregateError);assert.deepEqual(error.errors,[null,later]);assert.equal(error.cause,null);return true;
    });
    await assert.rejects(native.lstat(join(f.root,'.writer.lock')),{code:'ENOENT'});
  });
});
