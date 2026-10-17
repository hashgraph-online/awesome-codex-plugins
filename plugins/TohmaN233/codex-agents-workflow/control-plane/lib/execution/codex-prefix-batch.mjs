import {requireValue} from '../workflow-paths.mjs';
import {canonicalJSON} from '../workflow-revisions.mjs';

const fields=['inputTokens','cachedInputTokens','cacheWriteInputTokens','outputTokens','reasoningOutputTokens','totalTokens'];
function total(value){
 requireValue(value&&fields.every(k=>k==='cacheWriteInputTokens'&&value[k]===undefined
   ||Number.isSafeInteger(value[k])&&value[k]>=0),'CODEX_BATCH_USAGE','Incomplete batch usage');
 return {...value};
}
function difference(end,start){
 const result={};
 for(const k of fields){
  if(end[k]===undefined&&start[k]===undefined)continue;
  requireValue(end[k]!==undefined&&start[k]!==undefined&&end[k]>=start[k],
    'CODEX_BATCH_USAGE','Batch usage counters changed or decreased');
  result[k]=end[k]-start[k];
 }
 return result;
}

/** One initialized, privately owned App Server; its caller owns authentication,
 * ordinary tool declarations, durable Run authority, and process cleanup.
 * Only a dedicated common-only source is accepted. No Main transcript enters
 * this interface. A completed source is preparation evidence, not a cache-hit
 * guarantee; the returned usage always includes it. */
export function createCodexPrefixBatch({client,onTransition=async()=>{},timeoutMs=3600000}){
 const slots=new Map();let source,prepared=false,running=false;
 const transition=(phase,data={})=>onTransition({phase,...data});
 const zero=value=>Object.fromEntries(fields.filter(k=>value[k]!==undefined).map(k=>[k,0]));
 function observe(event){
  if(!['turn/started','turn/completed'].includes(event.method))return;
  const slot=slots.get(event.params?.threadId);
  if(!slot)return;
  if(event.method==='turn/completed'){
   requireValue(slot.starting&&slot.turn_id===event.params.turn?.id,
     'CODEX_BATCH_TURN','Unexpected batch terminal identity');
   slot.starting=false;slot.completed=true;return;
  }
  requireValue(slot.starting&&typeof event.params.turn?.id==='string'
    &&(!slot.turn_id||slot.turn_id===event.params.turn.id),
    'CODEX_BATCH_TURN','Unexpected batch turn');
  slot.turn_id=event.params.turn.id;
 }
 async function turn(slot,input,options,baseline){
  requireValue(!slot.starting&&!slot.closed,'CODEX_BATCH_STATE','Branch is active or closed');
  const after=client.events.length;slot.starting=true;slot.completed=false;slot.turn_id=undefined;
  await transition('turn_submit',{thread_id:slot.thread_id,index:slot.index});
  const started=await client.call('turn/start',{...options,threadId:slot.thread_id,input},{timeout:timeoutMs});
  slot.turn_id??=started.turn?.id;
  requireValue(slot.turn_id===started.turn?.id,'CODEX_BATCH_TURN','Turn acknowledgement changed identity');
  const completed=await client.waitFor(event=>event.method==='turn/completed'
    &&event.params?.threadId===slot.thread_id&&event.params.turn?.id===slot.turn_id,
    {after,timeout:timeoutMs});
  slot.starting=false;
  // App Server sends cumulative usage before turn completion. A restored
  // source counter, observed BEFORE submit, excludes inherited preparation.
  const updates=client.events.slice(after).filter(e=>e.method==='thread/tokenUsage/updated'
    &&e.params?.threadId===slot.thread_id&&e.params.turnId===slot.turn_id);
  const items=client.events.slice(after).filter(e=>e.method==='item/completed'
    &&e.params?.threadId===slot.thread_id&&e.params.turnId===slot.turn_id).map(e=>e.params.item);
  const messages=items.filter(item=>item?.type==='agentMessage').map(item=>item.text);
  const commandIds=new Set(),commandItems=items.filter(item=>{
    if(item?.type!=='commandExecution')return false;
    if(typeof item.id!=='string')return true;
    if(commandIds.has(item.id))return false;
    commandIds.add(item.id);return true;
  });
  slot.completed=true;
  let previous=baseline,usage=null;
  try{
   for(const update of updates){const next=total(update.params.tokenUsage.total);previous??=zero(next);baseline??=previous;difference(next,previous);previous=next;}
   usage=updates.length?difference(previous,baseline):null;
  }catch(error){
   error.branch_result={thread_id:slot.thread_id,turn_id:slot.turn_id,usage:null,
    output:messages.at(-1),status:completed.params.turn.status,command_items:commandItems,
    usage_unavailable_reason:'Invalid cumulative usage; original error retained'};
   throw error;
  }
  const result={thread_id:slot.thread_id,turn_id:slot.turn_id,usage,total:previous,
    output:messages.at(-1),status:completed.params.turn.status,
    command_items:commandItems,
    ...(usage?{}:{usage_unavailable_reason:'No usage event for completed turn'})};
  slot.result=result;
  try{await transition('turn_complete',{thread_id:slot.thread_id,index:slot.index,turn_id:slot.turn_id,usage,status:result.status});}
  catch(error){error.branch_result=result;throw error;}
  if(result.status!=='completed'||!usage){
   const error=new Error(result.status==='completed'?'Completed turn has no usage':'Batch turn did not complete');
   error.code=result.status==='completed'?'CODEX_BATCH_USAGE':'CODEX_BATCH_TURN_FAILED';
   error.branch_result=result;throw error;
  }
  return result;
 }
 function preserveOptions(options={}){
  const commonKeys=Object.keys(source.turnOptions??{});
  requireValue(Object.keys(options).every(k=>commonKeys.includes(k))
    &&commonKeys.every(k=>!Object.hasOwn(options,k)||canonicalJSON(options[k])===canonicalJSON(source.turnOptions[k])),
    'CODEX_BATCH_PREFIX_CHANGED','Branches must preserve common effort, output schema and tool surface');
  return {...source.turnOptions,...options};
 }
 async function fork(index){
  requireValue(prepared&&Number.isSafeInteger(index)&&index>=0
    &&![...slots.values()].some(s=>s.index===index),'CODEX_BATCH_STATE','Branch index is invalid or already owned');
  // Reserve the index before awaiting RPC, excluding simultaneous duplicate opens.
  const reservation={index};slots.set('pending:'+index,reservation);
  const after=client.events.length;
  const response=await client.call('thread/fork',{threadId:source.thread_id,
    experimentalPredictionMode:true,ephemeral:true,excludeTurns:false},{timeout:timeoutMs});
  requireValue(response.thread?.ephemeral===true&&response.thread.forkedFromId===source.thread_id
    &&typeof response.thread.id==='string'&&response.model===source.model,
    'CODEX_BATCH_FORK','Fork changed source or ephemeral ownership');
  const slot={thread_id:response.thread.id,index};slots.delete('pending:'+index);slots.set(slot.thread_id,slot);
  const restored=await client.waitFor(e=>e.method==='thread/tokenUsage/updated'
    &&e.params?.threadId===slot.thread_id&&e.params.turnId===source.result.turn_id,{after,timeout:timeoutMs});
  const baseline=total(restored.params.tokenUsage.total);
  requireValue(fields.every(k=>baseline[k]===source.result.total[k]),
    'CODEX_BATCH_USAGE','Fork did not restore its exact source usage');
  slot.baseline=baseline;
  await transition('fork_ready',{index,thread_id:slot.thread_id,source_thread_id:source.thread_id});
  return {thread_id:slot.thread_id,index};
 }
 async function interruptBranch(thread_id){
  const slot=slots.get(thread_id);
  requireValue(slot&&slot.index!==null,'CODEX_BATCH_STATE','Unknown batch branch');
  if(slot.starting){
   requireValue(typeof slot.turn_id==='string','CODEX_BATCH_TURN','Cannot interrupt an unacknowledged turn');
   const after=client.events.length,turn_id=slot.turn_id;
   await client.call('turn/interrupt',{threadId:slot.thread_id,turnId:turn_id});
   await client.waitFor(event=>event.method==='turn/completed'&&event.params?.threadId===slot.thread_id
     &&event.params.turn?.id===turn_id,{after,timeout:Math.min(timeoutMs,8000)});
  }
 }
 return {
  observe,
  adoptSource({thread_id,turn_id,model,total:usageTotal,output,turnOptions}){
   requireValue(!source&&!running&&typeof thread_id==='string'&&typeof turn_id==='string'
     &&typeof model==='string','CODEX_BATCH_SOURCE','Source must be a completed dedicated private session');
   const result={thread_id,turn_id,total:total(usageTotal),output};
   source={thread_id,turn_id,index:null,model,turnOptions,result,completed:true};
   slots.set(thread_id,source);prepared=true;return result;
  },
  fork,
  async turnBranch(thread_id,input,turnOptions={}){
   const slot=slots.get(thread_id);
   requireValue(prepared&&slot&&slot.index!==null&&slot.baseline&&Array.isArray(input),
     'CODEX_BATCH_STATE','Branch must have its restored source before submission');
   return turn(slot,input,preserveOptions(turnOptions),slot.result?.total??slot.baseline);
  },
  closeBranch(thread_id){
   const slot=slots.get(thread_id);
   requireValue(slot&&slot.index!==null&&!slot.starting,'CODEX_BATCH_STATE','Cannot close an unknown or active branch');
   slot.closed=true;
  },
  interruptBranch,
  async callTool(params,resolve){
   const context=params.context,slot=slots.get(context?.thread_id);
   requireValue(context&&slot&&slot.starting&&!slot.completed&&slot.turn_id===context.turn_id
     &&context.session_id===slot.thread_id&&params.callId===context.call_id,
     'CODEX_BATCH_TOOL_CONTEXT','Tool call lacks an admitted exact branch identity');
   return resolve(slot.index,params);
  },
  async prepare({start,input,turnOptions}){
   requireValue(!source&&!running&&start.ephemeral===false&&start.historyMode==='legacy'
     &&typeof start.cwd==='string','CODEX_BATCH_SOURCE','Common source must be new and privately persisted');
   const started=await client.call('thread/start',start,{timeout:timeoutMs});
   requireValue(started.thread?.ephemeral===false&&typeof started.thread.id==='string'
     &&started.model===start.model,'CODEX_BATCH_SOURCE','Common source configuration changed');
   source={thread_id:started.thread.id,index:null,model:start.model,turnOptions};slots.set(source.thread_id,source);
   source.result=await turn(source,input,turnOptions,null);prepared=true;
   return source.result;
  },
  async launch(items,{turnOptions}={}){
   requireValue(prepared&&!running&&Array.isArray(items)&&items.length>0&&items.length<=32,
     'CODEX_BATCH_STATE','Batch needs its completed common-only source and one launch');
   running=true;
   requireValue(canonicalJSON(turnOptions??{})===canonicalJSON(source.turnOptions??{})
     &&items.every(item=>Array.isArray(item.input)&&Object.keys(item.turnOptions??{})
       .every(k=>Object.hasOwn(source.turnOptions??{},k))),
     'CODEX_BATCH_PREFIX_CHANGED','Branches must preserve the common model, effort, output schema and tool surface');
   // Submit every fork in this Host turn. The server serializes source snapshot
   // creation internally; branch model turns use distinct queues and overlap.
   const forks=await Promise.allSettled(items.map((_,index)=>fork(index)));
   const failed=forks.filter(x=>x.status==='rejected');
   if(failed.length)throw new AggregateError(failed.map(x=>x.reason),'Batch fork failed before branch submission');
   const results=await Promise.allSettled(forks.map(({value},index)=>
    turn(slots.get(value.thread_id),items[index].input,preserveOptions({...turnOptions,...items[index].turnOptions}),slots.get(value.thread_id).baseline)));
   const errors=results.filter(x=>x.status==='rejected');
   if(errors.length)throw new AggregateError(errors.map(x=>x.reason),'Batch branch failed; all started branches drained');
   return {preparation:source.result,branches:results.map(x=>x.value)};
  },
  async interrupt(){
   const result=await Promise.allSettled([...slots.values()].filter(s=>s.starting&&s.turn_id)
     .map(s=>client.call('turn/interrupt',{threadId:s.thread_id,turnId:s.turn_id})));
   const failures=result.filter(x=>x.status==='rejected');
   if(failures.length)throw new AggregateError(failures.map(x=>x.reason),'Batch interruption failed');
  },
 };
}
