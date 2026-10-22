import test from 'node:test';
import assert from 'node:assert/strict';
import {createCodexPrefixBatch} from '../lib/execution/codex-prefix-batch.mjs';
import {ownedMcpContext} from '../lib/execution/owned-tool-mcp.mjs';

const counters={inputTokens:100,cachedInputTokens:80,outputTokens:2,reasoningOutputTokens:0,totalTokens:102};
const options={effort:'high',outputSchema:{type:'object'}};
function fixture({fail=false,onTransition,command=false,invalidUsage=false}={}){
 const events=[],calls=[],totals=new Map(),pending=[];let engine,id=0;
 const emit=e=>{events.push(e);engine.observe(e);};
 const client={events,async call(method,params){
  calls.push({method,params});
  if(method==='thread/fork'){
   const threadId='child-'+id++;totals.set(threadId,{...counters});
   emit({method:'thread/tokenUsage/updated',params:{threadId,turnId:'source-turn',tokenUsage:{total:{...counters}}}});
   return {thread:{id:threadId,ephemeral:true,forkedFromId:'source'},model:'same-model'};
  }
  if(method==='turn/interrupt')return {};
  assert.equal(method,'turn/start');const turnId='turn-'+id++;
  emit({method:'turn/started',params:{threadId:params.threadId,turn:{id:turnId}}});
  pending.push(()=>{
   const value={...totals.get(params.threadId)};
   value.inputTokens+=10;value.cachedInputTokens+=8;value.outputTokens+=2;value.totalTokens+=12;
   if(invalidUsage)value.inputTokens=99;
   totals.set(params.threadId,value);
   emit({method:'thread/tokenUsage/updated',params:{threadId:params.threadId,turnId,tokenUsage:{total:value}}});
   if(command){
    emit({method:'item/completed',params:{threadId:'unrelated',turnId,item:{type:'commandExecution',id:'foreign'}}});
    emit({method:'item/completed',params:{threadId:params.threadId,turnId:'wrong-turn',item:{type:'commandExecution',id:'wrong-turn-command'}}});
    emit({method:'item/completed',params:{threadId:params.threadId,turnId,item:{type:'commandExecution',id:'own-command',command:'original help',exitCode:0}}});
    emit({method:'item/completed',params:{threadId:params.threadId,turnId,item:{type:'commandExecution',id:'own-command',command:'original help',exitCode:0}}});
   }
   emit({method:'item/completed',params:{threadId:params.threadId,turnId,item:{type:'agentMessage',text:'done'}}});
   emit({method:'turn/completed',params:{threadId:params.threadId,turn:{id:turnId,status:fail?'failed':'completed'}}});
  });
  return {turn:{id:turnId}};
 },async waitFor(predicate,{after=0}){
  let found=events.slice(after).find(predicate);
  if(!found){await new Promise(resolve=>setImmediate(resolve));for(const complete of pending.splice(0))complete();found=events.slice(after).find(predicate);}
  assert.ok(found,'fixture missing expected event');return found;
 }};
 engine=createCodexPrefixBatch({client,onTransition});
 engine.adoptSource({thread_id:'source',turn_id:'source-turn',model:'same-model',total:counters,turnOptions:options});
 return {engine,client,calls};
}

test('batch forks share only dedicated source; all branch submissions precede completions and inherited usage is excluded',async()=>{
 const {engine,calls,client}=fixture();
 const result=await engine.launch([0,1,2].map(index=>({input:[{type:'text',text:'own-'+index}]})),{turnOptions:options});
 assert.equal(calls.filter(c=>c.method==='thread/fork').length,3);
 for(const call of calls.filter(c=>c.method==='thread/fork'))assert.deepEqual(call.params,{threadId:'source',experimentalPredictionMode:true,ephemeral:true,excludeTurns:false});
 const starts=client.events.map((e,i)=>e.method==='turn/started'?i:-1).filter(i=>i>=0);
 const firstEnd=client.events.findIndex(e=>e.method==='turn/completed');assert.ok(Math.max(...starts)<firstEnd);
 for(const branch of result.branches)assert.deepEqual(branch.usage,{inputTokens:10,cachedInputTokens:8,outputTokens:2,reasoningOutputTokens:0,totalTokens:12});
 const child=result.branches[0].thread_id;
 const next=await engine.turnBranch(child,[{type:'text',text:'repair'}],options);
 assert.equal(next.usage.inputTokens,10);assert.equal(next.total.inputTokens,120);
 await assert.rejects(engine.turnBranch(child,[],{effort:null}),{code:'CODEX_BATCH_PREFIX_CHANGED'});
 await assert.rejects(engine.turnBranch(child,[],{cwd:'another-directory'}),{code:'CODEX_BATCH_PREFIX_CHANGED'});
 engine.closeBranch(child);await assert.rejects(engine.turnBranch(child,[],options),{code:'CODEX_BATCH_STATE'});
});

test('native command observations belong to the exact branch and survive a failed paid turn',async()=>{
 for(const fail of [false,true]){
  const {engine}=fixture({command:true,fail}),child=await engine.fork(0);
  let result;
  try{result=await engine.turnBranch(child.thread_id,[],options);assert.equal(fail,false);}
  catch(error){assert.equal(fail,true);assert.equal(error.code,'CODEX_BATCH_TURN_FAILED');result=error.branch_result;}
  assert.deepEqual(result.command_items,[{type:'commandExecution',id:'own-command',command:'original help',exitCode:0}]);
  assert.equal(result.usage.inputTokens,10);
  engine.closeBranch(child.thread_id);
 }
});

test('invalid usage remains an error while exact terminal native commands stay observable',async()=>{
 const {engine}=fixture({command:true,invalidUsage:true}),child=await engine.fork(0);
 await assert.rejects(engine.turnBranch(child.thread_id,[],options),error=>{
  assert.equal(error.code,'CODEX_BATCH_USAGE');
  assert.equal(error.branch_result.usage,null);
  assert.equal(error.branch_result.command_items.length,1);
  assert.equal(error.branch_result.command_items[0].id,'own-command');return true;
 });
 engine.closeBranch(child.thread_id);
});

test('core supplied MCP identity admits only the running exact branch and malformed identity fails',async()=>{
 const {engine,calls}=fixture();const child=await engine.fork(0);
 const pending=engine.turnBranch(child.thread_id,[],options);
 await new Promise(resolve=>queueMicrotask(resolve));
 const turnId=calls.find(c=>c.method==='turn/start')&&'turn-1';
 const context=ownedMcpContext({threadId:child.thread_id,sessionId:child.thread_id,callId:'call', 'x-codex-turn-metadata':{turn_id:turnId}});
 assert.equal(await engine.callTool({context,callId:'call'},index=>index),0);
 await assert.rejects(engine.callTool({context:{...context,thread_id:'source'},callId:'call'},()=>assert.fail('wrong branch admitted')),{code:'CODEX_BATCH_TOOL_CONTEXT'});
 assert.throws(()=>ownedMcpContext({threadId:child.thread_id}),{code:'CODEX_MCP_CONTEXT'});
 await engine.interruptBranch(child.thread_id);await pending;
 await assert.rejects(engine.callTool({context,callId:'call'},()=>assert.fail('terminal admitted')),{code:'CODEX_BATCH_TOOL_CONTEXT'});
});

test('failed completed turn retains actual usage rather than pretending a free failed attempt',async()=>{
 const {engine}=fixture({fail:true});const child=await engine.fork(0);
 await assert.rejects(engine.turnBranch(child.thread_id,[],options),error=>{
  assert.equal(error.code,'CODEX_BATCH_TURN_FAILED');assert.equal(error.branch_result.usage.inputTokens,10);
  assert.equal(error.branch_result.status,'failed');return true;
 });
 engine.closeBranch(child.thread_id);
});

test('terminal journal failure preserves known paid usage for Host failure metering',async()=>{
 const {engine}=fixture({onTransition:async event=>{if(event.phase==='turn_complete')throw Error('journal unavailable');}});
 const child=await engine.fork(0);
 await assert.rejects(engine.turnBranch(child.thread_id,[],options),error=>{
  assert.equal(error.message,'journal unavailable');assert.equal(error.branch_result.usage.inputTokens,10);return true;
 });
 engine.closeBranch(child.thread_id);
});
