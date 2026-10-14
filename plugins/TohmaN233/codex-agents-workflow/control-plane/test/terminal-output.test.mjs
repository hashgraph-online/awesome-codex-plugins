import test from 'node:test';
import assert from 'node:assert/strict';
import {committedTerminalOutput} from '../lib/execution/terminal-output.mjs';
import {WorkflowDrive} from '../lib/workflow-drive.mjs';
import {HostMainManager} from '../lib/execution/host-main-manager.mjs';

test('successful aggregate terminal output preserves large exact semantic data without truncation',async()=>{
 const output={first:{links:'x'.repeat(200000)+'FIRST'},second:{links:'y'.repeat(200000)+'SECOND'},semantic_result:'[neutral](G:/neutral/output.html) 😀'};
 const state={status:'succeeded',output,nodes:{}},record={state,pins:{root:{workflow:{nodes:[]}}}};
 const drive=new WorkflowDrive({runtime:{authorizedPlanningRun:async()=>({record,next:{}})}});
 const result=await drive.advanceToMain('neutral-run',{control_token:'neutral',owner:'main'});
 assert.equal(result.completion_satisfied,true);assert.equal(result.recovery_required,false);
 assert.deepEqual(result.output,output);result.output.first.links='changed';assert.equal(state.output.first.links.length,200005);
 assert.deepEqual(committedTerminalOutput({status:'succeeded',output:null}),{output:null});
});
test('terminal non-success keeps failure semantics and never exposes a stale successful output',async()=>{
 for(const status of ['failed','cancelled','blocked','running'])assert.deepEqual(committedTerminalOutput({status,output:{accepted:true}}),{});
 assert.deepEqual(committedTerminalOutput({status:'succeeded'}),{});
});
test('Host Main public terminal outcome returns committed semantic output',async()=>{
 const manager=new HostMainManager({configPath:'neutral-terminal',getConfig:async()=>({}),qualify:async()=>({})});
 const output={accepted:true,semantic_result:'[neutral](G:/neutral/output.html)'},entry={runId:'neutral-terminal-run',status:'running',stopping:false,cleanupPending:false,broker:null,session:null,
  handoff:{stop_reason:'main_node',host_binding:{node_id:'main'}},runtime:{get:async()=>({status:'succeeded',output})}};
 manager.executeNode=async()=>({final_acceptance_required:false});manager.entries.set(entry.runId,entry);
 const result=await manager.executeLoop(entry);assert.equal(result.status,'succeeded');assert.deepEqual(result.outcome.output,output);
 assert.equal(result.outcome.completion_satisfied,true);assert.equal(result.outcome.recovery_required,false);
});

test('public drive terminal completion facts distinguish failure and cancellation without stale output',async()=>{
 for(const status of ['failed','cancelled']){
  const state={status,output:{accepted:true},nodes:{}},record={state,pins:{root:{workflow:{nodes:[]}}}};
  const drive=new WorkflowDrive({runtime:{authorizedPlanningRun:async()=>({record,next:{}})}});
  const result=await drive.advanceToMain('neutral-run',{control_token:'neutral',owner:'main'});
  assert.equal(result.status,status);assert.equal(result.completion_satisfied,false);
  assert.equal(result.recovery_required,status==='failed');assert.equal(Object.hasOwn(result,'output'),false);
 }
});

test('public drive uses the settled Host tool state for terminal facts without a status reread',async()=>{
 for(const status of ['failed','cancelled']){
  const state={status:'running',nodes:{host:{status:'pending',attempts:[]}},cost_ledger:{spent_micros:0,reserved_micros:0}},
    record={state,pins:{root:{workflow:{nodes:[{id:'host',type:'tool',tool_name:'neutral',input_bindings:{}}],edges:[]}}}},
    outcome={status,nodes:{host:{error:{code:'NEUTRAL_FAILURE',message:'neutral'}}}};
  let reads=0;
  const drive=new WorkflowDrive({runtime:{authorizedPlanningRun:async()=>{reads++;return {record,next:{ready:['host'],approvals:[]}};},
    claimNode:async()=>({attempt_id:'neutral-attempt',lease_token:'neutral-lease'})},
    executor:{executeHostTool:async()=>outcome}});
  const result=await drive.advance('neutral-run',{control_token:'neutral',owner:'main'});
  assert.equal(result.status,status);assert.equal(result.completion_satisfied,false);
  assert.equal(result.recovery_required,status==='failed');assert.equal(reads,1);
 }
});
