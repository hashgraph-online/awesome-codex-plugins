import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {syncBuiltinESMExports} from 'node:module';
import {join} from 'node:path';
import {tmpdir} from './physical-tempdir.mjs';
import {WorkflowRunStore} from '../lib/workflow-run-store.mjs';
import {canonicalJSON,digest} from '../lib/workflow-revisions.mjs';
import {appendEvent} from '../lib/workflow-events.mjs';

async function fixture(t,count=147,{candidate=true}={}){
  const root=await fs.mkdtemp(join(tmpdir(),'history-lock-boundary-'));
  t.after(()=>fs.rm(root,{recursive:true,maxRetries:3,retryDelay:100}));
  const runs=await new WorkflowRunStore(root).initialize(),bytes=Buffer.from('neutral historical resource\n');
  const sha256=digest(bytes),pins={resources:[{sha256,bytes:bytes.length}],root:{workflow:{nodes:[]}}};
  // Exact pre-upgrade history shape, published before any concurrent activity.
  // Avoid 147 unnecessary writer claims merely to construct neutral fixtures.
  for(let i=0;i<count;i++){
    const directory=runs.directory(`history-${i}`);await fs.mkdir(join(directory,'objects'),{recursive:true});
    await fs.writeFile(join(directory,'pins.json'),canonicalJSON(pins));
    await fs.writeFile(join(directory,'objects',sha256),bytes);
    await appendEvent(join(directory,'events.jsonl'),[],'started',{state:{run_id:`history-${i}`,
      pins_hash:digest(canonicalJSON(pins)),status:candidate&&i===0?'succeeded':'running',
      updated_at:'2026-01-01T00:00:00.000Z',nodes:{},permissions:{workspace:root}}});
  }
  return {root,runs,sha256};
}

test('147-history complete resource audit never holds foreground admission across resource IO',async t=>{
  const f=await fixture(t);let resourceEntered,releaseResource;
  const entered=new Promise(resolve=>resourceEntered=resolve),release=new Promise(resolve=>releaseResource=resolve);
  const original=fs.readFile;let intercepted=false;
  fs.readFile=async(path,...args)=>{
    if(!intercepted&&String(path)===join(f.runs.directory('history-0'),'objects',f.sha256)){
      intercepted=true;resourceEntered();await release;
    }
    return original(path,...args);
  };syncBuiltinESMExports();
  const audit=f.runs.cleanupHistory({olderThanMs:0});void audit.catch(()=>{});
  let foreground,completedBeforeRelease=false;
  try{
    await entered;
    foreground=f.runs.readNativeWaitState('history-146').then(record=>{completedBeforeRelease=true;return record;});
    const result=await Promise.race([foreground.then(()=>true),new Promise(resolve=>setTimeout(()=>resolve(false),500))]);
    completedBeforeRelease=result;
  }finally{
    releaseResource();fs.readFile=original;syncBuiltinESMExports();
    // Capture the verdict before releasing the blocked historical read.
    const verdict=completedBeforeRelease;await foreground;await audit;completedBeforeRelease=verdict;
  }
  assert.equal(completedBeforeRelease,true,'non-executing historical resource IO blocked the fresh foreground journal transaction');
});

test('147 ineligible histories require journal and pin integrity but zero resource or tree audits',async t=>{
  const f=await fixture(t,147,{candidate:false}),original=fs.readFile;let resourceReads=0;
  fs.readFile=async(path,...args)=>{if(String(path).includes(`${join('objects',f.sha256)}`))resourceReads++;return original(path,...args);};
  syncBuiltinESMExports();let result;
  try{result=await f.runs.cleanupHistory({olderThanMs:0});}finally{fs.readFile=original;syncBuiltinESMExports();}
  assert.equal(result.examined,147);assert.equal(result.deleted_count,0);assert.equal(result.preserved_count,147);
  assert.equal(resourceReads,0,'non-candidate executable resources were audited despite no deletion authority being requested');
});

test('history resource corruption remains a visible complete audit failure',async t=>{
  const f=await fixture(t,2);
  await fs.writeFile(join(f.runs.directory('history-0'),'objects',f.sha256),'modified');
  await assert.rejects(f.runs.cleanupHistory({olderThanMs:0}),error=>error.code==='RUN_RESOURCE_CORRUPT'
    ||error instanceof AggregateError&&error.errors.some(item=>item.code==='RUN_RESOURCE_CORRUPT'));
  assert.equal((await f.runs.readNativeWaitState('history-1')).state.status,'running');
});

test('candidate audit invalidated by a foreground mutation must reclassify before deletion',async t=>{
  const f=await fixture(t,2),original=fs.readFile;let changed=false;
  fs.readFile=async(path,...args)=>{
    if(!changed&&String(path)===join(f.runs.directory('history-0'),'objects',f.sha256)){
      changed=true;await f.runs.mutate('history-0','pause',state=>{state.status='interrupted';});
    }
    return original(path,...args);
  };syncBuiltinESMExports();let result;
  try{result=await f.runs.cleanupHistory({olderThanMs:0});}finally{fs.readFile=original;syncBuiltinESMExports();}
  assert.equal(changed,true);assert.equal(result.deleted_count,0);assert.equal(result.preserved_count,2);
  assert.equal((await f.runs.readNativeWaitState('history-0')).state.status,'interrupted');
});
