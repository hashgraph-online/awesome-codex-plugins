import test from 'node:test';
import assert from 'node:assert/strict';
import {randomUUID,randomBytes} from 'node:crypto';
import {WorkflowRuntime} from '../lib/workflow-runtime.mjs';
import {digest} from '../lib/workflow-revisions.mjs';

test('real item and rejection validators accept only the Host-persisted managed slot',async()=>{
 const control=randomBytes(32).toString('hex'),lease=randomBytes(32).toString('hex'),id=randomUUID(),dispatch=randomUUID();
 const attempt={id,status:'running',lease_hash:digest(lease),dispatch:{receipt:{executor:'codex-app-server-managed-native',subagent_dispatch_ids:[dispatch]}}};
 const definition={id:'worker',subagent_count:'auto',fanout:{input:'jobs',distribution:'partition',batch_size:2,scheduling:'parallel',max_concurrency:1,result_mode:'per_item',result_output:'results'},input_bindings:{jobs:'/inputs/jobs'},outputs_schema:{properties:{results:{items:{type:'string'}}}}};
 const state={control_hash:digest(control),inputs:{jobs:['a','b']},nodes:{worker:{status:'running',active_attempt_id:id,attempts:[attempt]}}};
 const pins={root:{workflow:{nodes:[definition]}}};
 const runtime={runs:{mutate:async(_run,_kind,change)=>({result:await change(state,pins,{state,events:[]})})}};
 const binding={node_id:'worker',attempt_id:id,control_token:control,lease_token:lease,index:0,agent_id:dispatch};
 const method=WorkflowRuntime.prototype.recordNativeItemResults;
 await assert.rejects(method.call(runtime,'run',{...binding,agent_id:dispatch.slice(1),target_indices:[0,1],result:{items:[]}}),{code:'NATIVE_ITEM_RESULT'});
 const first=await method.call(runtime,'run',{...binding,target_indices:[0,1],result:{items:[{outcome:'completed',result:'exact-成功'},{outcome:'blocked',block_reason:'repair only b'}]}});
 assert.deepEqual(first.accepted_item_indices,[0]);assert.deepEqual(first.unresolved_item_indices,[1]);
 await WorkflowRuntime.prototype.recordNativeRejectedTurn.call(runtime,'run',{...binding,turn_id:randomUUID(),category:'blocked',reason:'repair only b'});
 const second=await method.call(runtime,'run',{...binding,target_indices:[1],result:{items:[{outcome:'completed',result:'b'}]}});
 assert.deepEqual(second.result,['exact-成功','b']);assert.equal(attempt.native_rejected_turns[0].count,1);
});

test('filtered managed retry slots never accept a sibling compacted dispatch identity',async()=>{
 const control='control',lease='lease',attempt={id:'retry',status:'running',lease_hash:digest(lease),
   dispatch:{receipt:{executor:'codex-app-server-managed-native',subagent_dispatch_ids:['child-1','child-2'],
     subagent_plan:{assignments:[{assignment_index:1,dispatch_id:'child-1'},{assignment_index:2,dispatch_id:'child-2'}]}}},
   native_item_results:{0:{agent_id:'prior',result:'a'}},inherited_native_item_indices:[0]};
 const definition={id:'worker',subagent_count:'auto',fanout:{input:'jobs',distribution:'one_per_item',scheduling:'parallel',result_mode:'per_item',result_output:'results'},
   input_bindings:{jobs:'/inputs/jobs'},outputs_schema:{properties:{results:{items:{type:'string'}}}}};
 const state={control_hash:digest(control),inputs:{jobs:['a','b','c']},nodes:{worker:{status:'running',active_attempt_id:'retry',attempts:[attempt]}}};
 const pins={root:{workflow:{nodes:[definition]}}};
 const runtime={runs:{mutate:async(_run,_kind,change)=>({result:await change(state,pins,{state,events:[]})})}};
 const args={node_id:'worker',attempt_id:'retry',control_token:control,lease_token:lease,index:1,
   target_indices:[1],result:{items:[{outcome:'completed',result:'b'}]}};
 await assert.rejects(WorkflowRuntime.prototype.recordNativeItemResults.call(runtime,'run',{...args,agent_id:'child-2'}),{code:'NATIVE_ITEM_RESULT'});
 await assert.rejects(WorkflowRuntime.prototype.recordNativeRejectedTurn.call(runtime,'run',{...args,agent_id:'child-2',turn_id:'foreign',category:'blocked',reason:'wrong slot'}),{code:'NATIVE_AGENT_REJECTION'});
 const accepted=await WorkflowRuntime.prototype.recordNativeItemResults.call(runtime,'run',{...args,agent_id:'child-1'});
 assert.deepEqual(accepted.result,['b']);
});
