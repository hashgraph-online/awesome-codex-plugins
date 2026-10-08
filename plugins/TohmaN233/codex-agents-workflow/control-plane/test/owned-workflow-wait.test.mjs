import test from 'node:test';
import assert from 'node:assert/strict';
import {randomUUID,randomBytes} from 'node:crypto';
import {waitForOwnedWorkflow} from '../lib/execution/owned-workflow-wait.mjs';

test('Host continues exact wait objects and returns the controller continuation only when work needs it',async()=>{
 const run_id=randomUUID(),secret=randomBytes(32).toString('hex');
 const continuation={run_id,control_token:secret,after_sequence:987,timeout_ms:3600000};
 const signal=new AbortController().signal;let n=0;
 const service={async call(operation,args,options){
  assert.equal(operation,'wait');assert.equal(options.signal,signal);assert.equal(args.control_token,secret);
  if(n++===0){assert.equal(args.run_id,run_id);return {run_id,wake_reason:'subagent_event',next_action:'workflow_wait',next_action_args:continuation};}
  assert.deepEqual(args,continuation);return {run_id,status:'failed',wake_reason:'host_failed',error:{code:'EXACT_FAILURE'}};
 }};
 const result=await waitForOwnedWorkflow(service,{run_id,control_token:secret},{signal});
 assert.equal(n,2);assert.equal(result.error.code,'EXACT_FAILURE');assert(!JSON.stringify(result).includes(secret));
});
test('Host rejects another Run instead of guessing or continuing',async()=>{
 await assert.rejects(waitForOwnedWorkflow({call:async()=>({run_id:randomUUID(),wake_reason:'timeout'})},
  {run_id:randomUUID(),control_token:'example-opaque-controller-token'}),{code:'RUN_IDENTITY'});
});

test('native handoff returns the exact Host-supplied controller continuation',async()=>{
 const started={run_id:'native-run',control_token:'example-exact-native-authority'};
 const service={async call(operation,args){
  assert.equal(operation,'wait');assert.deepEqual(args,{run_id:started.run_id,control_token:started.control_token,timeout_ms:3600000});
  return {run_id:started.run_id,status:'running',wake_reason:'native_handoff_required',next_action:'workflow_native_next',
   next_action_args:{run_id:started.run_id,control_token:started.control_token}};
 }};
 const result=await waitForOwnedWorkflow(service,started);
 assert.equal(result.control_token,started.control_token);
 assert.deepEqual(result.next_action_args,{run_id:started.run_id,control_token:started.control_token});
});

test('pre-aborted originating signal cancels with the exact Host token and propagates its reason',async()=>{
 const abortReason=Object.assign(new Error('start was cancelled'),{code:'START_ABORTED'});
 const controller=new AbortController();controller.abort(abortReason);
 const started={run_id:'opaque-run-73',control_token:'example-host-token::opaque/73'};let calls=0;
 const service={async call(operation,args,options){
  calls++;
  assert.equal(operation,'cancel');
  assert.deepEqual(args,{run_id:started.run_id,control_token:started.control_token});
  assert.equal(options,undefined);
 }};
 let caught;
 try{await waitForOwnedWorkflow(service,started,{signal:controller.signal});}catch(error){caught=error;}
 assert.strictEqual(caught,abortReason);assert.equal(calls,1);
});

test('abort racing an in-flight wait cancels once and propagates the original wait cancellation',async()=>{
 const run_id='opaque-run-race',control_token='example-exact-host-authority-race';
 const controller=new AbortController();
 const waitCancellation=Object.assign(new Error('wait observed abort'),{code:'WAIT_ABORT'});
 let cancelled=0;
 const service={async call(operation,args,options){
  if(operation==='wait'){
   assert.equal(args.run_id,run_id);assert.equal(args.control_token,control_token);assert.equal(options.signal,controller.signal);
   controller.abort(new Error('originating call aborted'));
   throw waitCancellation;
  }
  assert.equal(operation,'cancel');
  assert.deepEqual(args,{run_id,control_token});assert.equal(options,undefined);cancelled++;
 }};
 let caught;
 try{await waitForOwnedWorkflow(service,{run_id,control_token},{signal:controller.signal});}catch(error){caught=error;}
 assert.strictEqual(caught,waitCancellation);assert.equal(cancelled,1);
 assert.equal(caught.message.includes(control_token),false);
});

test('wait errors without an originating abort are propagated without cancellation',async()=>{
 const error=Object.assign(new Error('wait failed'),{code:'WAIT_FAILED'});
 const service={async call(operation){assert.equal(operation,'wait');throw error;}};
 let caught;
 try{await waitForOwnedWorkflow(service,{run_id:'run',control_token:'token'},{signal:new AbortController().signal});}catch(value){caught=value;}
 assert.strictEqual(caught,error);
});

test('preflight environment attention passes through before Run identity validation',async()=>{
 const started={status:'environment_attention',environment:{status:'missing',missing:['tool-x']}};
 const controller=new AbortController();controller.abort(new Error('no Run was created'));
 const result=await waitForOwnedWorkflow({call:async()=>assert.fail('preflight attention has no Run to wait for')},started,{signal:controller.signal});
 assert.strictEqual(result,started);
});

test('abort racing a completed wait takes precedence and cancels the owned Run',async()=>{
 const abortReason=Object.assign(new Error('start aborted as wait completed'),{code:'START_ABORTED'});
 const controller=new AbortController();const started={run_id:'race-run',control_token:'example-race-token'};let cancelled=0;
 const service={async call(operation,args,options){
  if(operation==='wait'){
   assert.equal(args.run_id,started.run_id);assert.equal(options.signal,controller.signal);
   controller.abort(abortReason);
   return {run_id:started.run_id,status:'succeeded',wake_reason:'succeeded'};
  }
  assert.equal(operation,'cancel');assert.deepEqual(args,{run_id:started.run_id,control_token:started.control_token});
  assert.equal(options,undefined);cancelled++;
 }};
 let caught;
 try{await waitForOwnedWorkflow(service,started,{signal:controller.signal});}catch(error){caught=error;}
 assert.strictEqual(caught,abortReason);assert.equal(cancelled,1);
});

test('cancellation failure remains explicit and retains both cancellation errors',async()=>{
 const abortReason=new Error('start aborted');
 const cancelFailure=Object.assign(new Error('Host cancellation failed'),{code:'CANCEL_FAILED'});
 const controller=new AbortController();controller.abort(abortReason);
 const service={async call(operation){assert.equal(operation,'cancel');throw cancelFailure;}};
 await assert.rejects(waitForOwnedWorkflow(service,{run_id:'run',control_token:'opaque'},{signal:controller.signal}),error=>{
  assert.equal(error.code,'OWNED_WORKFLOW_CANCEL_FAILED');
  assert.deepEqual(error.errors,[abortReason,cancelFailure]);
  return true;
 });
});
