import test from 'node:test';
import assert from 'node:assert/strict';
import {boundedRead} from '../lib/bounded-read.mjs';
import {workbenchErrorPayload} from '../lib/workbench-api.mjs';
const latch=()=>{let release;const promise=new Promise(resolve=>release=resolve);return {promise,release};};

test('independent reads overlap within the bound and retain input order',async()=>{
 let active=0,max=0;const barrier=latch();
 const job=boundedRead([0,1,2,3,4,5],3,async value=>{
  max=Math.max(max,++active);if(active===3)barrier.release();await barrier.promise;
  await new Promise(resolve=>setTimeout(resolve,(5-value)*2));active--;return value*2;
 });
 assert.deepEqual(await job,[0,2,4,6,8,10]);assert.equal(max,3);assert.equal(active,0);
});

test('a failed read stops new admission and waits for admitted cleanup before rejecting',async()=>{
 const admitted=latch(),proceed=latch(),failure=Object.assign(new Error('corrupt read'),{code:'CORRUPT'});
 const calls=[];let settled=false,cleaned=false;
 const job=boundedRead([0,1,2,3],2,async value=>{
  calls.push(value);
  if(value===0){await admitted.promise;throw failure;}
  admitted.release();try{await proceed.promise;}finally{cleaned=true;}
 }).finally(()=>settled=true);
 const rejection=assert.rejects(job,error=>error===failure);
 await admitted.promise;await new Promise(resolve=>setImmediate(resolve));
 assert.equal(settled,false);assert.equal(cleaned,false);assert.deepEqual(calls,[0,1]);
 proceed.release();await rejection;assert.equal(cleaned,true);assert.equal(settled,true);
});

test('multiple admitted failures remain observable after all reads settle',async()=>{
 const barrier=latch();let active=0;
 await assert.rejects(boundedRead([0,1,2],2,async value=>{
  if(++active===2)barrier.release();await barrier.promise;
  throw Object.assign(new Error('failure '+value),{code:'READ_'+value});
 }),error=>{
  assert(error instanceof AggregateError);assert.equal(error.errors.length,2);
  assert.deepEqual(workbenchErrorPayload(error),{error:'Independent read checks failed',code:'READ_0',
   details:{failed_read_count:2,failures:[{index:0,code:'READ_0',type:'Error'},{index:1,code:'READ_1',type:'Error'}]}});
  return true;
 });
});
