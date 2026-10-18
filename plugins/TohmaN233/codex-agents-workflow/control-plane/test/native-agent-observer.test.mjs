import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,mkdir,writeFile,appendFile,rm,rename,symlink,readFile,watch} from 'node:fs/promises';
import {writeFileSync} from 'node:fs';
import {join,resolve} from 'node:path';
import {tmpdir} from './physical-tempdir.mjs';
import {spawnSync} from 'node:child_process';
import { inspectNativeAgent as inspectImpl, inspectNativeAgents as inspectManyImpl, inspectNativeParent, nativeParentThreadId, waitForNativeSessionEvent } from '../lib/execution/native-agent-observer.mjs';
import {createNativeLifecycleReader} from '../lib/execution/native-agent-lifecycle.mjs';

// Older cases isolate RPC result/identity handling; lifecycle cases below use
// the real structural reader against an exact synthetic owner rollout.
const unitLifecycle=async({turn})=>({turn_id:turn?.id??null,status:turn?.status==='completed'?'completed':!turn||['pending','inProgress'].includes(turn.status)?'pending':'interrupted'});
const unitOptions=options=>Object.hasOwn(options,'lifecycleHome')||Object.hasOwn(options,'readLifecycle')?options:{readLifecycle:unitLifecycle,...options};
const inspectNativeAgent=(client,id,options={})=>inspectImpl(client,id,unitOptions(options));
const inspectNativeAgents=(client,ids,options={})=>inspectManyImpl(client,ids,unitOptions(options));

const thread=id=>({thread:{id,parentThreadId:'parent-task',status:{type:'notLoaded'}}});
const page=(status,text)=>({data:[{id:'turn-1',status,itemsView:'full',items:status==='completed'?[{type:'agentMessage',phase:'final_answer',text}]:[]}]});
const parentId='01a0db25-ad92-72a0-b6fa-2519a6cfa2f8',childId='01a0db6b-704a-7470-bef4-7da3175bb140',agentPath='/root/pilot_source';
const listedChild=(id=childId,parent=parentId,path=agentPath)=>({id,parentThreadId:parent,
  source:{subAgent:{thread_spawn:{parent_thread_id:parent,agent_path:path}}}});
const logRow=(type,payload)=>JSON.stringify({timestamp:'2026-09-26T02:24:37.658Z',type,payload})+'\n';

test('nonterminal journal progress does not repeat SDK group scans',async t=>{
  const f=await lifecycleFixture(t);let terminal=false,reads=0,wakes=0;
  const client={async call(method){if(method==='thread/read'){reads++;return {thread:f.thread};}
    return {data:[{id:f.turnId,status:terminal?'completed':'interrupted',itemsView:terminal?'full':'summary',items:terminal?[{type:'agentMessage',phase:'final_answer',text:'{"outcome":"completed","result":{"done":true}}'}]:[]}]};}};
  const result=await inspectNativeAgents(client,[childId],{parentThreadId:parentId,lifecycleHome:f.home,waitForTerminal:true,
    waitForChange:async()=>{wakes++;if(wakes<=5)await appendFile(f.path,logRow('event_msg',{type:'token_count'}));
      else{terminal=true;await appendFile(f.path,logRow('event_msg',{type:'task_complete',turn_id:f.turnId}));}
      return {filename:'rollout-'+childId+'.jsonl',event_type:'change'};}});
  assert.equal(result.status,'completed');assert.equal(wakes,6);assert(reads<=3,`Progress caused ${reads} repeated SDK scans`);
});

test('quiet child wait observes a Run journal authority fence',async t=>{
  const f=await lifecycleFixture(t),runJournal=join(f.home,'run-events.jsonl');await writeFile(runJournal,'initial\n');let active=true;
  const client={async call(method){if(method==='thread/read')return {thread:f.thread};return {data:[{id:f.turnId,status:'interrupted',itemsView:'summary',items:[]}]};}};
  const pending=inspectNativeAgents(client,[childId],{parentThreadId:parentId,lifecycleHome:f.home,waitForTerminal:true,waitTimeoutMs:1000,
    runJournalPath:runJournal,checkActive:async()=>{if(!active)throw Object.assign(new Error('Exact authority fenced'),{code:'NATIVE_AGENT_ATTEMPT_CHANGED'});}});
  const timer=setTimeout(async()=>{active=false;await appendFile(runJournal,'fenced\n');},30);
  try{await assert.rejects(pending,{code:'NATIVE_AGENT_ATTEMPT_CHANGED'});}finally{clearTimeout(timer);}
});

for(const fence of ['cancel','controller','lease'])test(`armed quiet Run journal race rechecks ${fence} authority`,async t=>{
  const f=await lifecycleFixture(t),runJournal=join(f.home,'run-events.jsonl');await writeFile(runJournal,'active');
  let armed=false,aborted=false,reads=0;
  const client={async call(method){if(method==='thread/read'){reads++;return {thread:f.thread};}
    return {data:[{id:f.turnId,status:'interrupted',itemsView:'summary',items:[]}]};}};
  await assert.rejects(inspectNativeAgents(client,[childId],{parentThreadId:parentId,lifecycleHome:f.home,
    runJournalPath:runJournal,waitForTerminal:true,waitTimeoutMs:120,
    checkActive:async()=>{if(await readFile(runJournal,'utf8')!=='active')throw Object.assign(new Error(`Exact ${fence} fence`),{code:'NATIVE_AGENT_ATTEMPT_CHANGED'});},
    waitForChange:options=>{
      options.signal.addEventListener('abort',()=>{aborted=true;},{once:true});
      return waitForNativeSessionEvent({...options,watchImpl:(target,config)=>{
        // Durable commit occurs after the last pre-arm authority read but
        // before either watcher can observe its notification.
        if(!armed){armed=true;writeFileSync(runJournal,fence);}
        return watch(target,config);
      }});
    }}),{code:'NATIVE_AGENT_ATTEMPT_CHANGED'});
  assert.equal(armed,true);assert.equal(aborted,true);assert.equal(reads,1,'Run fence must not trigger an SDK group sweep');
});

test('native amendment observation preserves exact edits only in Host-authorized repair mode',async()=>{
  const amendment={amendments:[{field:'summary',start_line:1,end_line:1,replacement:'new'}]};
  const client={async call(method){return method==='thread/read'?{thread:{id:'child-1'}}:page('completed',JSON.stringify(amendment));}};
  const observed=await inspectNativeAgent(client,'child-1',{textAmendment:true});
  assert.equal(observed.status,'amendment');assert.deepEqual(observed.amendment,amendment);
  assert.equal((await inspectNativeAgent(client,'child-1')).status,'invalid');
});

test('exact captured bare semantic final is accepted only under its strict declared schema',async()=>{
  const source={implementation_plan:'Inspect the pinned requirements once, implement the requested changes, and report concise evidence.',
    source_manifest:{requirements_path:'inputs/requirements.json',data_path:'inputs/data.json'}};
  const text=JSON.stringify(source);
  const field={type:'string'};
  const source_manifest={type:'object',additionalProperties:false,
    properties:{requirements_path:field,data_path:field},required:['requirements_path','data_path']};
  const resultSchema={type:'object',additionalProperties:false,
    properties:{implementation_plan:field,source_manifest},required:['implementation_plan','source_manifest']};
  const observe=async(value,options={})=>inspectNativeAgent({async call(method){
    return method==='thread/read'?{thread:{id:'child-1'}}:page('completed',typeof value==='string'?value:JSON.stringify(value));
  }},'child-1',{resultSchema,...options});
  const accepted=await observe(text);
  assert.equal(accepted.status,'completed');
  assert.equal(accepted.result_shape,'bare_semantic_result');
  assert.deepEqual(accepted.result,source);
  assert.equal((await observe(text,{resultSchema:undefined})).status,'invalid');
  const missing=structuredClone(source);delete missing.source_manifest.data_path;
  assert.match((await observe(missing)).reason,/required property is missing: data_path/);
  const invalid=structuredClone(source);invalid.source_manifest.requirements_path=42;
  assert.match((await observe(invalid)).reason,/expected string/);
  assert.equal((await observe({...source,outcome:'completed'})).status,'invalid');
  const blocked=await observe({outcome:'blocked',result:null,block_reason:'missing source'});
  assert.equal(blocked.status,'blocked');assert.equal(blocked.result_shape,'completion_envelope');
  const wrapped=await observe({outcome:'completed',result:source,block_reason:''});
  assert.equal(wrapped.status,'completed');assert.equal(wrapped.result_shape,'completion_envelope');
});

test('bare per-item final requires an items wrapper and keeps individual validation with the Host',async()=>{
  const resultSchema={type:'object',properties:{items:{type:'array',items:{type:'object',properties:{
    outcome:{type:'string'},result:{type:'string'}},required:['outcome'],additionalProperties:false}}},
    required:['items'],additionalProperties:false};
  const observe=async(value)=>inspectNativeAgent({async call(method){
    return method==='thread/read'?{thread:{id:'child-1'}}:page('completed',JSON.stringify(value));
  }},'child-1',{resultSchema,perItemResult:true});
  assert.equal((await observe({items:[{outcome:'completed',result:'valid'},
    {outcome:'completed',result:42}]})).status,'completed');
  assert.equal((await observe([{outcome:'completed',result:'valid'}])).status,'invalid');
  assert.equal((await observe({items:[],extra:true})).status,'invalid');
});
async function lifecycleFixture(t){
  const home=await mkdtemp(join(tmpdir(),'native-lifecycle-'));await mkdir(join(home,'sessions'));
  t.after(async()=>{assert(resolve(home).startsWith(resolve(tmpdir())));await rm(home,{recursive:true,force:true});});
  const path=join(home,'sessions',`rollout-${childId}.jsonl`),turnId='01a0db87-610b-77e1-a181-f4616d4206f3';
  const meta={id:childId,parent_thread_id:parentId,agent_path:agentPath,source:{subagent:{thread_spawn:{parent_thread_id:parentId,agent_path:agentPath}}}};
  await writeFile(path,logRow('session_meta',meta)+logRow('event_msg',{type:'task_started',turn_id:turnId}));
  return {home,path,turnId,meta,thread:{...listedChild(),path}};
}

test('foreign App Server interrupted projection stays pending until the exact owner writes a terminal event',async t=>{
  const f=await lifecycleFixture(t),events=[];
  const client={async call(method,args){if(method==='thread/read')return {thread:f.thread};
    return {data:[{id:f.turnId,status:'interrupted',items:[],itemsView:'summary'}]};}};
  const result=await inspectNativeAgent(client,childId,{parentThreadId:parentId,lifecycleHome:f.home,onIdentityEvent:async event=>events.push(event)});
  assert.deepEqual(result,{status:'pending',pending_phase:'running',agent_id:childId});
  assert.equal(events[0].code,'NATIVE_AGENT_TERMINAL_UNCONFIRMED');
  await appendFile(f.path,logRow('event_msg',{type:'turn_aborted',turn_id:f.turnId,reason:'interrupted'}));
  assert.equal((await inspectNativeAgent(client,childId,{parentThreadId:parentId,lifecycleHome:f.home})).status,'blocked');
});

test('upstream fork lifecycle excludes the explicit inherited ordinal prefix and accepts only owned turns',async t=>{
  const f=await lifecycleFixture(t),parentTurn='inherited-parent-turn',args={thread:{...f.thread,forkedFromId:parentId},agentId:agentPath,parentThreadId:parentId};
  const owner={...f.meta,forked_from_id:parentId,subagent_history_start_ordinal:3};
  await writeFile(f.path,logRow('session_meta',owner)+logRow('session_meta',{id:parentId,source:'vscode'})
    +logRow('event_msg',{type:'task_started',turn_id:parentTurn})+logRow('event_msg',{type:'task_complete',turn_id:parentTurn}));
  const reader=createNativeLifecycleReader({home:f.home});
  assert.equal((await reader(args)).turn_id,null,'A completed copied parent turn must never establish child termination');
  await appendFile(f.path,logRow('event_msg',{type:'task_started',turn_id:f.turnId}));
  assert.equal((await reader(args)).status,'pending');
  await appendFile(f.path,logRow('event_msg',{type:'task_complete',turn_id:f.turnId}));
  assert.equal((await reader(args)).turn_id,f.turnId);assert.equal((await reader(args)).status,'completed');
  await appendFile(f.path,logRow('event_msg',{type:'task_started',turn_id:'owned-correction'})+logRow('event_msg',{type:'task_complete',turn_id:'owned-correction'}));
  assert.equal((await reader(args)).turn_id,'owned-correction');
});

test('upstream fork lifecycle rejects forged boundaries, parents and copied or repeated metadata',async t=>{
  const f=await lifecycleFixture(t),owner={...f.meta,forked_from_id:parentId,subagent_history_start_ordinal:3},parent={id:parentId,source:'vscode'},
    args={thread:{...f.thread,forkedFromId:parentId},agentId:agentPath,parentThreadId:parentId};
  const prefix=[parent,{type:'task_started',turn_id:'copied-parent'},{type:'task_complete',turn_id:'copied-parent'}];
  const rows=(header=owner,ancestor=parent)=>logRow('session_meta',header)+logRow('session_meta',ancestor)
    +logRow('event_msg',prefix[1])+logRow('event_msg',prefix[2])+logRow('event_msg',{type:'task_started',turn_id:f.turnId})+logRow('event_msg',{type:'task_complete',turn_id:f.turnId});
  for(const ordinal of [-1,1.5,'3',null]){
    await writeFile(f.path,rows({...owner,subagent_history_start_ordinal:ordinal}));
    await assert.rejects(createNativeLifecycleReader({home:f.home})(args),{code:'NATIVE_AGENT_LIFECYCLE_BOUNDARY'});
  }
  for(const ordinal of [2,4]){
    await writeFile(f.path,rows({...owner,subagent_history_start_ordinal:ordinal}));
    await assert.rejects(createNativeLifecycleReader({home:f.home})(args),{code:'NATIVE_AGENT_LIFECYCLE_SCHEMA'});
  }
  await writeFile(f.path,rows({...owner,forked_from_id:childId}));
  await assert.rejects(createNativeLifecycleReader({home:f.home})(args),{code:'NATIVE_AGENT_LIFECYCLE_BOUNDARY'});
  await writeFile(f.path,rows());
  await assert.rejects(createNativeLifecycleReader({home:f.home})({...args,thread:{...args.thread,forkedFromId:childId}}),{code:'NATIVE_AGENT_LIFECYCLE_BOUNDARY'});
  for(const ancestor of [{...parent,id:'foreign-ancestor'},{...parent,agent_path:'/root/foreign'},owner]){
    await writeFile(f.path,rows(owner,ancestor));
    await assert.rejects(createNativeLifecycleReader({home:f.home})(args),{code:'NATIVE_AGENT_LIFECYCLE_IDENTITY'});
  }
  await writeFile(f.path,rows(owner,{...parent,forked_from_id:'unsupported-fork'}));
  await assert.rejects(createNativeLifecycleReader({home:f.home})(args),{code:'NATIVE_AGENT_LIFECYCLE_IDENTITY'});
  const withoutBoundary={...owner};delete withoutBoundary.subagent_history_start_ordinal;
  await writeFile(f.path,rows(withoutBoundary));
  await assert.rejects(createNativeLifecycleReader({home:f.home})(args),{code:'NATIVE_AGENT_LIFECYCLE_BOUNDARY'});
  await writeFile(f.path,rows()+logRow('session_meta',parent));
  await assert.rejects(createNativeLifecycleReader({home:f.home})(args),{code:'NATIVE_AGENT_LIFECYCLE_IDENTITY'});
  await writeFile(f.path,rows()+logRow('session_meta',owner));
  await assert.rejects(createNativeLifecycleReader({home:f.home})(args),{code:'NATIVE_AGENT_LIFECYCLE_IDENTITY'});
});

test('upstream fork lifecycle validates a nested copied ancestor chain inside its typed prefix',async t=>{
  const f=await lifecycleFixture(t),path='/root/nested/page',grand='01a0db25-ad92-72a0-b6fa-2519a6cfa2f9';
  const owner={...f.meta,agent_path:path,forked_from_id:parentId,subagent_history_start_ordinal:4,
    source:{subagent:{thread_spawn:{parent_thread_id:parentId,agent_path:path}}}};
  const parent={id:parentId,parent_thread_id:grand,agent_path:'/root/nested',forked_from_id:grand,
    source:{subagent:{thread_spawn:{parent_thread_id:grand,agent_path:'/root/nested'}}}};
  await writeFile(f.path,logRow('session_meta',owner)+logRow('session_meta',parent)+logRow('session_meta',{id:grand,source:'vscode'})
    +logRow('event_msg',{type:'task_started',turn_id:'nested-parent'})+logRow('event_msg',{type:'task_complete',turn_id:'nested-parent'})
    +logRow('event_msg',{type:'task_started',turn_id:f.turnId})+logRow('event_msg',{type:'task_complete',turn_id:f.turnId}));
  const result=await createNativeLifecycleReader({home:f.home})({thread:{...f.thread,forkedFromId:parentId},agentId:path,parentThreadId:parentId});
  assert.equal(result.status,'completed');assert.equal(result.turn_id,f.turnId);assert.equal(result.inherited_records,4);
});

test('upstream fork ordinals count skipped large inherited records exactly across partial reads',async t=>{
  const f=await lifecycleFixture(t),args={thread:{...f.thread,forkedFromId:parentId},agentId:agentPath,parentThreadId:parentId};
  const large=logRow('response_item',{text:'PRIVATE_INHERITED_CONTENT_'.repeat(10000)});
  await writeFile(f.path,logRow('session_meta',{...f.meta,forked_from_id:parentId,subagent_history_start_ordinal:2})+logRow('session_meta',{id:parentId,source:'vscode'})+large.slice(0,-4));
  const reader=createNativeLifecycleReader({home:f.home,maxLineBytes:1024});const pending=await reader(args);
  assert.equal(pending.status,'pending');assert.equal(pending.turn_id,null);assert.equal(pending.retained_bytes,0);
  await appendFile(f.path,large.slice(-4)+logRow('event_msg',{type:'task_started',turn_id:f.turnId})+logRow('event_msg',{type:'task_complete',turn_id:f.turnId}));
  const completed=await reader(args);assert.equal(completed.status,'completed');assert.equal(completed.turn_id,f.turnId);assert.equal(completed.inherited_records,2);
});

test('upstream fork observer accepts the exact owned SDK turn and never a copied parent completion',async t=>{
  const f=await lifecycleFixture(t),thread={...f.thread,forkedFromId:parentId},copied='copied-completed-parent';
  await writeFile(f.path,logRow('session_meta',{...f.meta,forked_from_id:parentId,subagent_history_start_ordinal:3})+logRow('session_meta',{id:parentId,source:'vscode'})
    +logRow('event_msg',{type:'task_started',turn_id:copied})+logRow('event_msg',{type:'task_complete',turn_id:copied}));
  let sdkTurn=copied;const client={async call(method){return method==='thread/read'?{thread}:{data:[{id:sdkTurn,status:'completed',itemsView:'full',items:[{type:'agentMessage',phase:'final_answer',text:'{"outcome":"completed","result":{"summary":"neutral owned proposal"}}'}]}]};}};
  assert.equal((await inspectNativeAgent(client,childId,{parentThreadId:parentId,lifecycleHome:f.home})).status,'pending');
  await appendFile(f.path,logRow('event_msg',{type:'task_started',turn_id:f.turnId})+logRow('event_msg',{type:'task_complete',turn_id:f.turnId}));sdkTurn=f.turnId;
  const accepted=await inspectNativeAgent(client,childId,{parentThreadId:parentId,lifecycleHome:f.home});assert.equal(accepted.status,'completed');assert.equal(accepted.turn_id,f.turnId);
});

test('one-shot native inspection returns a running child without polling',async()=>{
  let threadReads=0,turnReads=0;
  const client={async call(method,args){
    assert.notEqual(method,'thread/list');assert.equal(args.threadId,childId);
    if(method==='thread/read'){threadReads++;return {thread:listedChild()};}
    turnReads++;return page('inProgress');
  }};
  const result=await inspectNativeAgents(client,[childId],{parentThreadId:parentId});
  assert.deepEqual(result,{status:'pending',pending_phase:'running',agent_ids:[childId]});
  assert.equal(threadReads,1);assert.equal(turnReads,1);
});

test('owner lifecycle reads only appended bytes and holds a partial terminal line until it is complete',async t=>{
  const f=await lifecycleFixture(t),reader=createNativeLifecycleReader({home:f.home,maxPartialReads:3});
  const args={thread:f.thread,agentId:agentPath,parentThreadId:parentId};
  const first=await reader(args);assert.equal(first.status,'pending');assert(first.bytes_read>0);
  assert.equal((await reader(args)).bytes_read,0);
  const end=logRow('event_msg',{type:'turn_aborted',turn_id:f.turnId});
  await appendFile(f.path,end.slice(0,-4));const partial=await reader(args);
  assert.equal(partial.status,'pending');assert(partial.retained_bytes>0);
  await appendFile(f.path,end.slice(-4));const done=await reader(args);
  assert.equal(done.status,'interrupted');assert.equal(done.bytes_read,4);assert.equal(done.retained_bytes,0);
});

test('lifecycle keeps one exact rollout identity across Windows case and extended path spellings',async t=>{
  const f=await lifecycleFixture(t),reader=createNativeLifecycleReader({home:f.home});
  const args={thread:f.thread,agentId:agentPath,parentThreadId:parentId};
  assert.equal((await reader(args)).status,'pending');
  const path=process.platform==='win32'?'\\\\?\\'+f.path.toUpperCase():f.path;
  await appendFile(f.path,logRow('event_msg',{type:'task_complete',turn_id:f.turnId}));
  assert.equal((await reader({...args,thread:{...f.thread,path}})).status,'completed');
});

test('lifecycle reader rejects missing paths, other sessions, unsupported terminal fields and replaced files',async t=>{
  const f=await lifecycleFixture(t),args={thread:f.thread,agentId:agentPath,parentThreadId:parentId};
  await assert.rejects(createNativeLifecycleReader({home:f.home})({...args,thread:{...f.thread,path:null}}),{code:'NATIVE_AGENT_LIFECYCLE_PATH'});
  await assert.rejects(createNativeLifecycleReader({home:f.home})({...args,thread:{...f.thread,path:join(f.home,'outside.jsonl')}}),{code:'NATIVE_AGENT_LIFECYCLE_PATH'});
  for(const meta of [{...f.meta,id:parentId},{...f.meta,parent_thread_id:childId},{...f.meta,agent_path:'/root/other'}]){
    await writeFile(f.path,logRow('session_meta',meta));
    await assert.rejects(createNativeLifecycleReader({home:f.home})(args),{code:'NATIVE_AGENT_LIFECYCLE_IDENTITY'});
  }
  await writeFile(f.path,logRow('session_meta',f.meta)+logRow('event_msg',{type:'task_complete'}));
  await assert.rejects(createNativeLifecycleReader({home:f.home})(args),{code:'NATIVE_AGENT_LIFECYCLE_SCHEMA'});
  await writeFile(f.path,logRow('session_meta',f.meta)+logRow('event_msg',{unexpected_header:true,type:'task_complete',turn_id:f.turnId}));
  await assert.rejects(createNativeLifecycleReader({home:f.home})(args),{code:'NATIVE_AGENT_LIFECYCLE_SCHEMA'});
  await writeFile(f.path,logRow('session_meta',f.meta)+logRow('event_msg',{type:'task_started',turn_id:f.turnId}));
  const reader=createNativeLifecycleReader({home:f.home});await reader(args);
  await rename(f.path,f.path+'.old');await writeFile(f.path,logRow('session_meta',f.meta));
  await assert.rejects(reader(args),{code:'NATIVE_AGENT_LIFECYCLE_CHANGED'});
  await rm(f.path);await assert.rejects(createNativeLifecycleReader({home:f.home})(args),{code:'NATIVE_AGENT_LIFECYCLE_READ'});
});

test('lifecycle reader refuses a reparse path even when its target has matching session metadata',async t=>{
  const f=await lifecycleFixture(t);await mkdir(join(f.home,'real'));await writeFile(join(f.home,'real','child.jsonl'),logRow('session_meta',f.meta));
  try{await symlink(join(f.home,'real'),join(f.home,'sessions','linked'),process.platform==='win32'?'junction':'dir');}
  catch(error){if(error.code==='EPERM'){t.skip('Symlink creation unavailable');return;}throw error;}
  await assert.rejects(createNativeLifecycleReader({home:f.home})({thread:{...f.thread,path:join(f.home,'sessions','linked','child.jsonl')},agentId:agentPath,parentThreadId:parentId}),{code:'NATIVE_AGENT_LIFECYCLE_READ'});
});

test('partial records are bounded and long nonstructural bodies are skipped without retaining their content',async t=>{
  const f=await lifecycleFixture(t),args={thread:f.thread,agentId:agentPath,parentThreadId:parentId};
  const reader=createNativeLifecycleReader({home:f.home,maxLineBytes:1024,maxPartialReads:2});
  await appendFile(f.path,JSON.stringify({type:'response_item',payload:{text:'PRIVATE_BODY_'.repeat(20000)}}).slice(0,-2));
  const pending=await reader(args);assert.equal(pending.status,'pending');assert.equal(pending.retained_bytes,0);
  await assert.rejects(reader(args),{code:'NATIVE_AGENT_LIFECYCLE_PARTIAL'});
  await appendFile(f.path,'}}\n'+logRow('event_msg',{type:'task_complete',turn_id:f.turnId}));
  assert.equal((await reader(args)).status,'completed');
  await writeFile(f.path,logRow('session_meta',{...f.meta,unsupported:'x'.repeat(2048)}).slice(0,-1));
  await assert.rejects(createNativeLifecycleReader({home:f.home,maxLineBytes:1024})(args),{code:'NATIVE_AGENT_LIFECYCLE_LINE_LIMIT'});
  await appendFile(f.path,'\n');
  await assert.rejects(createNativeLifecycleReader({home:f.home,maxLineBytes:1024})(args),{code:'NATIVE_AGENT_LIFECYCLE_LINE_LIMIT'});
});

test('completion refreshes full items after an empty summary and never accepts an older final',async t=>{
  const f=await lifecycleFixture(t),result={evidence:'x'.repeat(12000)+'TAIL'},views=[];
  const client={async call(method,args){if(method==='thread/read')return {thread:f.thread};
    views.push(args.itemsView);
    if(args.itemsView==='summary'){await appendFile(f.path,logRow('event_msg',{type:'task_complete',turn_id:f.turnId}));
      return {data:[{id:f.turnId,status:'interrupted',itemsView:'summary',items:[]}]};}
    return {data:[{id:f.turnId,status:'completed',itemsView:'full',items:[{type:'agentMessage',phase:'final_answer',text:JSON.stringify({outcome:'completed',result})}]}]};
  }};
  assert.deepEqual((await inspectNativeAgent(client,childId,{parentThreadId:parentId,lifecycleHome:f.home})).result,result);
  assert.deepEqual(views,['summary','full']);
  const next='01a0db87-610b-77e1-a181-f4616d4206f4';await appendFile(f.path,logRow('event_msg',{type:'task_started',turn_id:next}));
  const old={async call(method){return method==='thread/read'?{thread:f.thread}:{data:[{id:f.turnId,status:'completed',itemsView:'full',items:[{type:'agentMessage',phase:'final_answer',text:'{"outcome":"completed","result":{"stale":true}}'}]}]};}};
  assert.equal((await inspectNativeAgent(old,childId,{parentThreadId:parentId,lifecycleHome:f.home})).status,'pending');
});

test('a delayed full terminal snapshot stays in one pending call and missing final data fails within its retry bound',async t=>{
  const f=await lifecycleFixture(t);await appendFile(f.path,logRow('event_msg',{type:'task_complete',turn_id:f.turnId}));
  let fullReads=0;const events=[];
  const client={async call(method,args){if(method==='thread/read')return {thread:f.thread};
    const ready=args.itemsView==='full'&&++fullReads>=2;
    return {data:[{id:f.turnId,status:'completed',itemsView:args.itemsView,items:ready?[{type:'agentMessage',phase:'final_answer',text:'{"outcome":"completed","result":{"done":true}}'}]:[]}]};}};
  const result=await inspectNativeAgents(client,[childId],{parentThreadId:parentId,lifecycleHome:f.home,pollIntervalMs:1,
    onIdentityEvent:async event=>events.push(event)});
  assert.deepEqual(result.result,{done:true});assert.equal(fullReads,2);
  assert.deepEqual(events.map(event=>event.code),['NATIVE_AGENT_FINAL_PENDING']);
  let missingReads=0;
  const missing={async call(method,args){if(method==='thread/read')return {thread:f.thread};
    if(args.itemsView==='full')missingReads++;
    return {data:[{id:f.turnId,status:'completed',itemsView:args.itemsView,items:[]}]};}};
  await assert.rejects(inspectNativeAgents(missing,[childId],{parentThreadId:parentId,lifecycleHome:f.home,pollIntervalMs:1,terminalAttempts:2}),{code:'NATIVE_AGENT_FINAL_UNAVAILABLE'});
  assert.equal(missingReads,2);
});

test('live interrupted projection emits one diagnostic and releases the MCP call',async t=>{
  const f=await lifecycleFixture(t);let reads=0;const events=[];
  const client={async call(method){if(method==='thread/read')return {thread:f.thread};
    reads++;return {data:[{id:f.turnId,status:'interrupted',itemsView:'summary',items:[]}]};}};
  const result=await inspectNativeAgents(client,[childId],{parentThreadId:parentId,lifecycleHome:f.home,
    onIdentityEvent:async event=>events.push(event)});
  assert.deepEqual(result,{status:'pending',pending_phase:'running',agent_ids:[childId]});
  assert.equal(reads,1);assert.deepEqual(events.map(event=>event.code),['NATIVE_AGENT_TERMINAL_UNCONFIRMED']);
});

test('lifecycle rejects truncated files and a session that never supplies its supported start schema',async t=>{
  const f=await lifecycleFixture(t),args={thread:f.thread,agentId:agentPath,parentThreadId:parentId};
  const reader=createNativeLifecycleReader({home:f.home});await reader(args);await writeFile(f.path,'');
  await assert.rejects(reader(args),{code:'NATIVE_AGENT_LIFECYCLE_CHANGED'});
  await writeFile(f.path,logRow('session_meta',f.meta));
  const incomplete=createNativeLifecycleReader({home:f.home,maxPartialReads:2});assert.equal((await incomplete(args)).status,'pending');
  await assert.rejects(incomplete(args),{code:'NATIVE_AGENT_LIFECYCLE_SCHEMA'});
});

test('native parent preflight verifies the exact UUID without creating any thread or turn',async()=>{
  const calls=[];const client={async call(method,args){calls.push([method,args]);return {thread:{id:args.threadId}};}};
  assert.deepEqual(await inspectNativeParent(client,parentId),{thread_id:parentId,agent_path:'/root'});
  assert.deepEqual(calls,[['thread/read',{threadId:parentId,includeTurns:false}]]);
  await assert.rejects(inspectNativeParent(client,'codex'),{code:'NATIVE_AGENT_IDENTITY_PARENT'});assert.equal(calls.length,1);
  await assert.rejects(inspectNativeParent({async call(){return {thread:{id:childId}};}},parentId),{code:'NATIVE_AGENT_IDENTITY_PARENT'});
  assert.equal(nativeParentThreadId({main_actor:'codex',constraints:{native_parent_thread_id:parentId}}),parentId);
  assert.throws(()=>nativeParentThreadId({main_actor:parentId}),{code:'NATIVE_AGENT_IDENTITY_PARENT'});
  assert.throws(()=>nativeParentThreadId({main_actor:parentId,native_parent_thread_id:'codex'}),{code:'NATIVE_AGENT_IDENTITY_PARENT'});
  assert.throws(()=>nativeParentThreadId({main_actor:parentId,native_parent_thread_id:null}),{code:'NATIVE_AGENT_IDENTITY_PARENT'});
  assert.throws(()=>nativeParentThreadId({native_parent_thread_id:parentId,constraints:{native_parent_thread_id:childId}}),{code:'NATIVE_AGENT_IDENTITY_PARENT'});
});

test('canonical native path resolves under its exact parent once and preserves the recorded receipt identity',async()=>{
  let lists=0,turnReads=0;const calls=[],events=[];
  const client={async call(method,args){calls.push([method,args]);
    if(method==='thread/list'){lists++;assert.deepEqual(args,{parentThreadId:parentId,sourceKinds:['subAgentThreadSpawn'],modelProviders:[],limit:100,useStateDbOnly:true});return {data:[listedChild()],nextCursor:null};}
    assert.equal(args.threadId,childId);
    if(method==='thread/read')return {thread:listedChild()};
    turnReads++;return page('interrupted');
  }};
  const result=await inspectNativeAgents(client,[agentPath],{parentThreadId:parentId,onIdentityEvent:async event=>events.push(event)});
  assert.equal(lists,1);assert.equal(turnReads,1);
  assert.equal(result.agent_id,agentPath);assert.equal(result.status,'blocked');assert.match(result.reason,/interrupted/);
  assert.deepEqual(events.map(event=>event.code),['NATIVE_AGENT_IDENTITY_RESOLVED']);
  assert.match(events[0].diagnostic,new RegExp(childId));
});

test('native UUID observation does not invoke identity discovery',async()=>{
  const client={async call(method,args){assert.notEqual(method,'thread/list');assert.equal(args.threadId,childId);
    return method==='thread/read'?{thread:listedChild()}:page('interrupted');}};
  assert.equal((await inspectNativeAgent(client,childId,{parentThreadId:parentId})).agent_id,childId);
});

test('canonical path requires a parent and rejects missing, wrong-parent and ambiguous identities before reading a turn',async()=>{
  let calls=0;const client={async call(){calls++;throw new Error('unexpected RPC');}};
  await assert.rejects(inspectNativeAgent(client,agentPath),{code:'NATIVE_AGENT_IDENTITY_PARENT'});assert.equal(calls,0);
  await assert.rejects(inspectNativeAgent(client,agentPath,{parentThreadId:'codex'}),{code:'NATIVE_AGENT_IDENTITY_PARENT'});assert.equal(calls,0);
  for(const [data,code] of [
    [[], 'NATIVE_AGENT_IDENTITY_NOT_FOUND'],
    [[listedChild(childId,'different-parent')], 'NATIVE_AGENT_IDENTITY_PARENT'],
    [[listedChild(),listedChild('01a0db6b-704a-7470-bef4-7da3175bb141')], 'NATIVE_AGENT_IDENTITY_AMBIGUOUS'],
  ]){
    await assert.rejects(inspectNativeAgent({async call(method){assert.equal(method,'thread/list');return {data,nextCursor:null};}},agentPath,{parentThreadId:parentId}),{code});
  }
});

test('identity discovery checks every filtered page and never selects the newest duplicate',async()=>{
  const cursors=[];
  await assert.rejects(inspectNativeAgent({async call(method,args){assert.equal(method,'thread/list');cursors.push(args.cursor);
    return args.cursor?{data:[listedChild('01a0db6b-704a-7470-bef4-7da3175bb141')],nextCursor:null}:{data:[listedChild()],nextCursor:'page-2'};
  }},agentPath,{parentThreadId:parentId}),{code:'NATIVE_AGENT_IDENTITY_AMBIGUOUS'});
  assert.deepEqual(cursors,[undefined,'page-2']);
});

test('just-spawned registration returns pending once and resolves after the native event',async()=>{
  let lists=0,registered=false;const events=[];
  const client={async call(method){
    if(method==='thread/list'){lists++;return {data:registered?[listedChild()]:[],nextCursor:null};}
    return method==='thread/read'?{thread:listedChild()}:page('interrupted');
  }};
  const first=await inspectNativeAgents(client,[agentPath],{parentThreadId:parentId,onIdentityEvent:async event=>events.push(event)});
  assert.deepEqual(first,{status:'pending',pending_phase:'registration',agent_ids:[agentPath]});assert.equal(lists,1);
  registered=true;
  const second=await inspectNativeAgents(client,[agentPath],{parentThreadId:parentId,onIdentityEvent:async event=>events.push(event)});
  assert.equal(second.status,'blocked');assert.equal(lists,2);
  assert.deepEqual(events.map(event=>event.code),['NATIVE_AGENT_IDENTITY_PENDING','NATIVE_AGENT_IDENTITY_RESOLVED']);
});

test('registration wait rechecks cancellation and RPC failures identify their phase',async()=>{
  let active=true;
  await assert.rejects(inspectNativeAgents({async call(){active=false;return {data:[],nextCursor:null};}},[agentPath],
    {parentThreadId:parentId,pollIntervalMs:1,checkActive:async()=>{if(!active)throw Object.assign(new Error('cancelled'),{code:'CANCELLED'});}}),{code:'CANCELLED'});
  const fail={async call(){throw new Error('RPC failed: code=-32600');}};
  await assert.rejects(inspectNativeAgent(fail,agentPath,{parentThreadId:parentId}),error=>error.code==='NATIVE_AGENT_IDENTITY_RPC'&&/thread\/list/.test(error.message));
  await assert.rejects(inspectNativeAgent(fail,childId,{parentThreadId:parentId}),error=>error.code==='NATIVE_AGENT_OBSERVATION_RPC'&&/thread\/read/.test(error.message));
  await assert.rejects(inspectNativeAgent({async call(method){return method==='thread/read'?{thread:listedChild()}:{unsupported:[]};}},childId,
    {parentThreadId:parentId}),{code:'NATIVE_AGENT_OBSERVATION_SCHEMA'});
});

test('Host reads a real native child final result without a Main model polling turn',async()=>{
  const calls=[];
  const client={async call(method,args){calls.push([method,args]);return method==='thread/read'?thread(args.threadId):page('completed',
    JSON.stringify({outcome:'completed',result:{done:true},block_reason:''}));}};
  const result=await inspectNativeAgent(client,'child-1');
  assert.deepEqual(result,{status:'completed',agent_id:'child-1',turn_id:'turn-1',result:{done:true},result_shape:'completion_envelope'});
  assert.deepEqual(calls.map(item=>item[0]),['thread/read','thread/turns/list']);
});

test('event-triggered second inspection completes a child without a Host polling loop',async()=>{
  let reads=0,complete=false;
  const client={async call(method,args){assert(['thread/read','thread/turns/list'].includes(method));if(method==='thread/read')return thread(args.threadId);
    reads++;return complete?page('completed',JSON.stringify({outcome:'completed',result:['one'],block_reason:''})):page('inProgress');}};
  const first=await inspectNativeAgents(client,['child-1']);
  assert.deepEqual(first,{status:'pending',pending_phase:'running',agent_ids:['child-1']});
  complete=true;
  const second=await inspectNativeAgents(client,['child-1']);
  assert.equal(reads,2);assert.deepEqual(second.result,['one']);
});

test('Host-owned terminal wait stays in one observation call until the lifecycle event',async()=>{
  let complete=false,releaseEvent,settled=false,waits=0;
  const client={async call(method,args){
    if(method==='thread/read')return thread(args.threadId);
    return complete?page('completed',JSON.stringify({outcome:'completed',result:['one'],block_reason:''})):page('inProgress');
  }};
  const observed=inspectNativeAgents(client,['child-1'],{
    waitForTerminal:true,
    waitForChange:async()=>{waits++;await new Promise(resolve=>{releaseEvent=()=>{complete=true;resolve();};});},
  }).finally(()=>{settled=true;});
  await new Promise(resolve=>setTimeout(resolve,20));
  assert.equal(settled,false,'A model-facing Host wait must not return a pending continuation');
  assert.equal(waits,1);
  releaseEvent();
  const result=await observed;
  assert.equal(result.status,'completed');
  assert.deepEqual(result.result,['one']);
  assert.equal(waits,1,'One child lifecycle event must cause one continuation, not a polling loop');
});

test('production lifecycle watcher wakes the held Host call on the exact child journal',async t=>{
  const f=await lifecycleFixture(t);let complete=false;
  const client={nativeObserverHome:f.home,async call(method){
    if(method==='thread/read')return {thread:f.thread};
    return {data:[{id:f.turnId,status:complete?'completed':'inProgress',itemsView:complete?'full':'summary',
      items:complete?[{type:'agentMessage',phase:'final_answer',text:JSON.stringify({outcome:'completed',result:{done:true},block_reason:''})}]:[]}]};
  }};
  setTimeout(async()=>{
    complete=true;
    await appendFile(f.path,logRow('event_msg',{type:'task_complete',turn_id:f.turnId}));
  },20);
  const result=await inspectNativeAgents(client,[childId],{parentThreadId:parentId,lifecycleHome:f.home,
    waitForTerminal:true,waitTimeoutMs:2000});
  assert.equal(result.status,'completed');assert.deepEqual(result.result,{done:true});
});

test('production lifecycle watcher fails visibly on its one-hour bound and caller cancellation',async t=>{
  const home=await mkdtemp(join(tmpdir(),'native-watch-stop-'));await mkdir(join(home,'sessions'));
  t.after(async()=>{assert(resolve(home).startsWith(resolve(tmpdir())));await rm(home,{recursive:true,force:true});});
  await assert.rejects(waitForNativeSessionEvent({home,timeoutMs:20}),{code:'NATIVE_AGENT_WAIT_TIMEOUT'});
  const controller=new AbortController(),pending=waitForNativeSessionEvent({home,timeoutMs:2000,signal:controller.signal});
  controller.abort(Object.assign(new Error('Run cancelled'),{code:'NATIVE_AGENT_WAIT_CANCELLED'}));
  await assert.rejects(pending,{code:'NATIVE_AGENT_WAIT_CANCELLED'});
});

test('native event wait retains its deadline when no other event-loop handle exists',()=>{
  const moduleUrl=new URL('../lib/execution/native-agent-observer.mjs',import.meta.url).href;
  const script=`import {waitForNativeSessionEvent} from ${JSON.stringify(moduleUrl)};
    const watchImpl=(_path,{signal})=>({async *[Symbol.asyncIterator](){
      await new Promise((_resolve,reject)=>signal.addEventListener('abort',()=>reject(signal.reason),{once:true}));
    }});
    try { await waitForNativeSessionEvent({home:process.cwd(),timeoutMs:20,watchImpl});process.exitCode=1; }
    catch(error) { if(error.code!=='NATIVE_AGENT_WAIT_TIMEOUT')throw error;process.stdout.write(error.code); }`;
  const result=spawnSync(process.execPath,['--input-type=module','--eval',script],{encoding:'utf8',timeout:5000});
  assert.ifError(result.error);
  assert.equal(result.status,0,result.stderr);
  assert.equal(result.stdout,'NATIVE_AGENT_WAIT_TIMEOUT','The owning Host wait must remain alive until its explicit deadline');
});





test('Host returns a precise blocked result instead of journaling success',async()=>{
  const client={async call(method,args){return method==='thread/read'?thread(args.threadId):page('completed',
    JSON.stringify({outcome:'blocked',result:null,block_reason:'Missing card source row'}));}};
  const result=await inspectNativeAgent(client,'child-1');
  assert.deepEqual(result,{status:'blocked',agent_id:'child-1',turn_id:'turn-1',reason:'Missing card source row',result_shape:'completion_envelope'});
});

test('Host reports malformed terminal JSON once and accepts the event-triggered correction turn',async()=>{
  let reads=0;
  const client={async call(method,args){if(method==='thread/read')return thread(args.threadId);
    reads++;
    if(reads===1)return page('completed','not JSON');
    return {data:[{id:'turn-2',status:'completed',itemsView:'full',items:[{type:'agentMessage',phase:'final_answer',
      text:JSON.stringify({outcome:'completed',result:{done:true},block_reason:''})}]}]};}};
  const first=await inspectNativeAgent(client,'child-1');
  assert.equal(first.status,'invalid');assert.equal(first.turn_id,'turn-1');
  const second=await inspectNativeAgents(client,['child-1'],{afterTurnIds:{'child-1':'turn-1'}});
  assert.equal(second.turn_id,'turn-2');assert.equal(second.status,'completed');assert.equal(reads,2);
});

test('Host mechanically removes only impossible JSON closers and projects Host-owned per-item envelope fields',async()=>{
  const resultSchema={type:'object',properties:{items:{type:'array'}},required:['items'],additionalProperties:false};
  const malformed='{"item_id":"host-owned","items":[{"outcome":"blocked","block_reason":"needs repair"}},{"outcome":"completed","result":{"evidence":"passed"}}]}';
  const client={async call(method,args){return method==='thread/read'?thread(args.threadId):page('completed',malformed);}};
  const result=await inspectNativeAgent(client,'child-1',{resultSchema,perItemResult:true});
  assert.equal(result.status,'completed');
  assert.equal(result.result_shape,'bare_semantic_result_host_normalized');
  assert.deepEqual(result.normalization,{syntax_repairs:1,host_projected:true});
  assert.deepEqual(result.result,{items:[
    {outcome:'blocked',block_reason:'needs repair'},
    {outcome:'completed',result:{evidence:'passed'}},
  ]});
});

test('Host does not invent missing JSON delimiters or values during native result normalization',async()=>{
  const client={async call(method,args){return method==='thread/read'?thread(args.threadId):page('completed','{"items":[{"outcome":"completed"}');}};
  const result=await inspectNativeAgent(client,'child-1',{resultSchema:{type:'object'},perItemResult:true});
  assert.equal(result.status,'invalid');assert.match(result.reason,/not JSON/);
});

test('Host leaves a rejected latest turn pending and accepts only an event-triggered newer turn',async()=>{
  let reads=0,turnId='bad-newer';
  const client={async call(method,args){if(method==='thread/read')return thread(args.threadId);
    reads++;return {data:[{id:turnId,status:'completed',itemsView:'full',items:[{type:'agentMessage',phase:'final_answer',
      text:JSON.stringify({outcome:'completed',result:{done:true},block_reason:''})}]}]};}};
  const options={afterTurnIds:{'child-1':'bad-newer'},rejectedTurnIds:{'child-1':['bad-older','bad-newer']}};
  const first=await inspectNativeAgents(client,['child-1'],options);
  assert.deepEqual(first,{status:'pending',pending_phase:'running',agent_ids:['child-1']});
  turnId='fixed';const second=await inspectNativeAgents(client,['child-1'],options);
  assert.equal(second.turn_id,'fixed');assert.equal(second.status,'completed');assert.equal(reads,2);
});

test('Host rechecks authority after an in-flight observation before releasing a result',async()=>{
  let active=true;
  const client={async call(method,args){if(method==='thread/read')return thread(args.threadId);
    active=false;return page('completed',JSON.stringify({outcome:'completed',result:{done:true},block_reason:''}));}};
  await assert.rejects(inspectNativeAgents(client,['child-1'],{checkActive:async()=>{
    if(!active)throw Object.assign(new Error('Run cancelled'),{code:'NATIVE_AGENT_ATTEMPT_CHANGED'});
  }}),{code:'NATIVE_AGENT_ATTEMPT_CHANGED'});
});

test('armed native watcher is cancelled when the race recheck fails',async()=>{
 let lifecycleReads=0,aborted=false;
 const client={call:async method=>method==='thread/read'?thread('child-1'):page('inProgress','')};
 await assert.rejects(inspectNativeAgents(client,['child-1'],{waitForTerminal:true,
  readLifecycle:async()=>{if(++lifecycleReads>1)throw Object.assign(new Error('Exact lifecycle corrupt'),{code:'NATIVE_AGENT_LIFECYCLE_SCHEMA'});return {status:'pending',turn_id:'turn-1'};},
  waitForChange:async({signal})=>new Promise((_resolve,reject)=>{signal.addEventListener('abort',()=>{aborted=true;reject(signal.reason);},{once:true});})}),{code:'NATIVE_AGENT_LIFECYCLE_SCHEMA'});
 assert.equal(aborted,true);
});
test('pending progress retains the original deadline across notifications',async()=>{
 const timeouts=[];let turn='turn-1';
 const client={call:async method=>method==='thread/read'?thread('child-1'):{data:[{id:turn,status:'inProgress',itemsView:'summary',items:[]}]}};
 await assert.rejects(inspectNativeAgents(client,['child-1'],{waitForTerminal:true,waitTimeoutMs:55,
  waitForChange:async({timeoutMs})=>{timeouts.push(timeoutMs);await new Promise(resolve=>setTimeout(resolve,20));turn='next-'+timeouts.length;}}),{code:'NATIVE_AGENT_WAIT_TIMEOUT'});
 assert(timeouts.length>=2);assert(timeouts[1]<timeouts[0]);
});
