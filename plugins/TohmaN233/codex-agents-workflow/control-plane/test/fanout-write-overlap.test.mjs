import test from 'node:test';
import assert from 'node:assert/strict';
import {resolve,join} from 'node:path';
import {mkdtemp,rm} from 'node:fs/promises';
import {tmpdir} from './physical-tempdir.mjs';
import {resolvedSubagentPlan,WorkflowRuntime} from '../lib/workflow-runtime.mjs';
import {ManagedNativeManager} from '../lib/execution/managed-native-manager.mjs';
import {digest} from '../lib/workflow-revisions.mjs';

function plan(paths,{scheduling='parallel',max_concurrency=2,batch_size}={}){
 const definition={id:'pages',access:'bounded_write',path_scope:['pages'],subagent_count:'auto',
  input_bindings:{jobs:'/inputs/jobs'},fanout:{input:'jobs',write_paths_field:'destinations',
   distribution:batch_size?'partition':'one_per_item',scheduling,max_concurrency,...(batch_size?{batch_size}:{})}};
 const state={permissions:{workspace:resolve('.'),access:'bounded_write',allowed_paths:['pages']},
  inputs:{jobs:paths.map(destinations=>({destinations}))},nodes:{}};
 return resolvedSubagentPlan(definition,state);
}

test('runtime refuses equal parallel destinations before any worker is dispatched',()=>{
 assert.throws(()=>plan([['pages/a'],['pages/a']]),{code:'SUBAGENT_ITEM_WRITE_OVERLAP'});
});
test('runtime refuses ancestor write scopes, including normalized absolute destinations',()=>{
 assert.throws(()=>plan([['pages/a'],[resolve('pages/a/out.html')]]),{code:'SUBAGENT_ITEM_WRITE_OVERLAP'});
 assert.throws(()=>plan([['pages'],['pages/a']]),{code:'SUBAGENT_ITEM_WRITE_OVERLAP'});
});
test('overlap detection retains ancestor ownership across unrelated lexical neighbours',()=>{
 assert.throws(()=>plan([['pages/a','pages/a-b'],['pages/a/c']]),{code:'SUBAGENT_ITEM_WRITE_OVERLAP'});
});
test('distinct whole-page scopes remain concurrent and assignments remain unchanged',()=>{
 const result=plan([['pages/a'],['pages/a-b'],['pages/b/out.html']]);
 assert.equal(result.count,3);assert.deepEqual(result.assignments.map(items=>items[0].destinations),[['pages/a'],['pages/a-b'],['pages/b/out.html']]);
});
test('overlap within one batch belongs to one worker and may be used together',()=>{
 assert.equal(plan([['pages/a'],['pages/a/out.html'],['pages/b']],{batch_size:2}).count,2);
});
test('serial or capped-to-one assignments retain the existing sequential contract',()=>{
 assert.equal(plan([['pages/a'],['pages/a']],{scheduling:'serial'}).count,2);
 assert.equal(plan([['pages/a'],['pages/a']],{max_concurrency:1}).count,2);
});
test('Windows case aliases cannot become two concurrent owners', {skip:process.platform!=='win32'},()=>{
 assert.throws(()=>plan([['pages/A'],['pages/a/out.html']]),{code:'SUBAGENT_ITEM_WRITE_OVERLAP'});
});

for(const inherited of [false,true])test(`managed dispatch uses the real runtime receipt guard before session creation (inherited=${inherited})`,async t=>{
 const root=await mkdtemp(join(tmpdir(),'fanout-write-receipt-'));
 const jobs=[{destinations:['pages/a']},{destinations:['pages/a/out.html']}];
 const fanout={input:'jobs',write_paths_field:'destinations',distribution:'one_per_item',scheduling:'parallel',
  max_concurrency:2,result_mode:'per_item',result_output:'results'};
 const definition={id:'pages',access:'bounded_write',path_scope:['pages'],subagent_count:'auto',fanout,
  executor:{kind:'provider',provider_id:'native'},input_bindings:{jobs:'/nodes/prepare/output/jobs'}};
 const attempt={id:'attempt-1',status:'claimed',lease_hash:digest('lease'),dispatch:{request_id:'dispatch-attempt-1',receipt:null},
  ...(inherited?{inherited_native_item_indices:[0],native_item_results:{0:{result:'accepted earlier'}}}:{})};
 const state={status:'running',control_hash:digest('control'),permissions:{workspace:root,access:'bounded_write',allowed_paths:['pages']},
  inputs:{},nodes:{prepare:{status:'succeeded',output:{jobs}},pages:{status:'claimed',active_attempt_id:attempt.id,attempts:[attempt]}}};
 const record={state,pins:{root:{workflow:{nodes:[definition]}}}};
 let factories=0,failed;
 const runtime=Object.assign(new WorkflowRuntime({runRoot:join(root,'runs')}),{runs:{read:async()=>record,mutate:async(_run,_kind,change)=>({result:await change(state,record.pins)})},
  recordDispatchReceipt:WorkflowRuntime.prototype.recordDispatchReceipt,
  failAttemptAfterQuiescence:async(_run,_args,error)=>{failed=error;},recordExecutorEvent:async()=>{}});
 const manager=new ManagedNativeManager({configPath:join(root,'control-plane.json'),getConfig:async()=>{throw new Error('Must reject before config');},
  sessionFactory:async()=>{factories++;throw new Error('Must reject before session creation');}});
 t.after(async()=>{await manager.close();assert(resolve(root).startsWith(resolve(tmpdir())+'/')||resolve(root).startsWith(resolve(tmpdir())+'\\'));await rm(root,{recursive:true,maxRetries:3,retryDelay:100});});
 const args={node_id:'pages',attempt_id:attempt.id,lease_token:'lease',control_token:'control'};
 const prepared={envelope:{subagents:{resolved_count:2,items:jobs,fanout}},adapter:{model:'gpt-test',effort:'low',executable_sha256:'b'.repeat(64)}};
 await assert.rejects(manager.launch(runtime,'run-1',args,prepared),{code:'SUBAGENT_ITEM_WRITE_OVERLAP'});
 const outcome=await manager.wait('run-1',attempt.id);
 assert.equal(outcome.status,'failed');assert.equal(failed.code,'SUBAGENT_ITEM_WRITE_OVERLAP');
 assert.equal(factories,0);assert.equal(attempt.dispatch.receipt,null);
});
