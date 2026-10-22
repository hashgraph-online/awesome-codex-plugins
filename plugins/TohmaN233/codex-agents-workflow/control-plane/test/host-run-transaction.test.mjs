import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {join} from 'node:path';
import {tmpdir} from './physical-tempdir.mjs';
import {WorkflowRunStore,withRunStoreObservation,assertOutsideHostRunTransaction,withRunStorePurpose} from '../lib/workflow-run-store.mjs';
import {canonicalJSON,digest} from '../lib/workflow-revisions.mjs';

async function fixture(t){
 const root=await fs.mkdtemp(join(tmpdir(),'host-run-transaction-'));t.after(()=>fs.rm(root,{recursive:true}));
 const runs=await new WorkflowRunStore(root).initialize(),id='neutral-run',bytes=Buffer.from('neutral sealed resource'),sha256=digest(bytes),pins={resources:[{sha256,bytes:bytes.length}],root:{workflow:{nodes:[]}}};
 await runs.create(id,pins,new Map([[sha256,bytes]]),{run_id:id,pins_hash:digest(canonicalJSON(pins)),status:'running',nodes:{},constraints:{},control_hash:'exact'});
 return {runs,id,root,sha256};
}
test('Host fixed read-purpose counters partition explicit audits',async t=>{
  const f=await fixture(t);let report;
  await withRunStoreObservation(async()=>{
    await withRunStorePurpose('dependency_post',()=>f.runs.audit(f.id));
    await f.runs.mutate(f.id,'control_recovery',state=>{state.control_hash='next';});
    await f.runs.audit(f.id);
  },value=>report=value);
  assert.equal(report.resource_audits,2);assert.equal(report.read_purposes.dependency_post.audits,1);
  assert.equal(report.read_purposes.ordinary.audits,1);assert.equal(Object.values(report.read_purposes).reduce((n,item)=>n+item.objects,0),report.resource_objects);
  assert.throws(()=>withRunStorePurpose('caller_skip_audit',()=>{}),{code:'RUN_STORE_PURPOSE'});
});
test('Host Run transaction reads fresh metadata and advances exact journal projections',async t=>{
 const f=await fixture(t);let report;
 await withRunStoreObservation(()=>f.runs.withHostTransaction(f.id,'claim',async()=>{
  const before=await f.runs.read(f.id);before.state.control_hash='local-mutated-copy';
  assert.equal((await f.runs.read(f.id)).state.control_hash,'exact');
  await f.runs.mutate(f.id,'control_recovery',state=>{state.control_hash='next';});
  const current=await f.runs.read(f.id);assert.equal(current.sequence,2);assert.equal(current.state.control_hash,'next');
 }),value=>report=value);
 assert.equal(report.resource_audits,0);assert(report.methods.transaction_read>=3);
 assert.equal((await f.runs.read(f.id)).state.control_hash,'next');
});
test('Host Run transaction cannot hide tamper at its next fresh boundary or outside calls',async t=>{
 const f=await fixture(t);await f.runs.withHostTransaction(f.id,'main_commit',async()=>{await f.runs.read(f.id);});
 await fs.writeFile(join(f.runs.directory(f.id),'pins.json'),'{}');
 await assert.rejects(f.runs.withHostTransaction(f.id,'main_commit',()=>{}),{code:'RUN_PINS_CORRUPT'});
 await assert.rejects(f.runs.read(f.id),{code:'RUN_PINS_CORRUPT'});
 await assert.rejects(f.runs.mutate(f.id,'cancel',state=>{state.status='cancelled';}),{code:'RUN_PINS_CORRUPT'});
});
test('Host Run transactions reject unknown phases and expire after the owning call',async t=>{
 const f=await fixture(t);await assert.rejects(f.runs.withHostTransaction(f.id,'caller_skip_audit',()=>{}),{code:'HOST_RUN_TRANSACTION_PHASE'});
 let release,late;const gate=new Promise(resolve=>release=resolve);let report;
 await withRunStoreObservation(()=>f.runs.withHostTransaction(f.id,'claim',async()=>{
  late=(async()=>{await gate;return f.runs.read(f.id);})();
 }),value=>report=value);release();await late;
 assert.equal(report.resource_audits,0);
 let next;await withRunStoreObservation(()=>f.runs.read(f.id),value=>next=value);assert.equal(next.resource_audits,0);
});

test('Host Run transaction rejects effect callbacks and cannot reuse another Run',async t=>{
 const f=await fixture(t);
 await f.runs.withHostTransaction(f.id,'main_dispatch',async()=>{
  assert.throws(()=>assertOutsideHostRunTransaction(),{code:'HOST_RUN_TRANSACTION_EXTERNAL'});
  await assert.rejects(f.runs.withHostTransaction('different-run','claim',()=>{}),{code:'HOST_RUN_TRANSACTION_SCOPE'});
 });
 assert.doesNotThrow(()=>assertOutsideHostRunTransaction());
});
