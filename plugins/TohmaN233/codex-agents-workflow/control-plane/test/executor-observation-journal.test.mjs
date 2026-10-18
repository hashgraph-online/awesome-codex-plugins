import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {syncBuiltinESMExports} from 'node:module';
import {join} from 'node:path';
import {tmpdir} from './physical-tempdir.mjs';
import {WorkflowRuntime} from '../lib/workflow-runtime.mjs';
import {WorkflowStore} from '../lib/workflow-store.mjs';
import {createDraft} from '../lib/workflow-schema.mjs';
import {canonicalJSON,digest} from '../lib/workflow-revisions.mjs';
import {readEvents,replayEvents} from '../lib/workflow-events.mjs';
import {createCodexToolBroker} from '../lib/execution/codex-tool-broker.mjs';
import {createCodexClient} from '../lib/execution/codex-app-server-client.mjs';
import {EventEmitter} from 'node:events';
import {PassThrough} from 'node:stream';

const native={...fs};
const methods=['item/started','item/completed','thread/tokenUsage/updated'];
const observation=(method=methods[0],index=0)=>({kind:'codex_event',metadata:{method,thread_id:'owned-thread',turn_id:'owned-turn',item_id:'item-'+index}});
async function patched(overrides,action){Object.assign(fs,overrides);syncBuiltinESMExports();try{return await action();}
  finally{for(const key of Object.keys(overrides))fs[key]=native[key];syncBuiltinESMExports();}}
async function fixture(t,count=1){
  const root=await native.mkdtemp(join(tmpdir(),'executor-observation-')),workspace=join(root,'workspace');await native.mkdir(workspace);
  t.after(()=>native.rm(root,{recursive:true,maxRetries:3,retryDelay:100}));
  const workflow={...createDraft('observation-test','Neutral observation test'),status:'ready',finalization:{required:true,node_id:'work'},
    skill_policy:{mode:'cooperative',implicit:'deny',ambient_allow:[],shadowed_skill_paths:[]},
    nodes:[{id:'start',type:'start'},{id:'work',type:'agent',executor:{kind:'main'},role:'finalizer',access:'read_only',
      prompt_template:'{{task}}',approval:{required:false},retry:{max_attempts:3},input_bindings:{}},{id:'end',type:'end'}],
    edges:[{id:'start-work',source:'start',target:'work'},{id:'work-end',source:'work',target:'end'}]};
  const packs=await new WorkflowStore(join(root,'packs')).initialize(),resources={};
  for(let i=0;i<count;i++)resources['resource-'+i+'.txt']='neutral pinned object '+i;
  await packs.create(workflow,{resources});
  const runtime=await new WorkflowRuntime({workflowStore:packs,runRoot:join(root,'runs')}).initialize();
  const run=await runtime.start({workflow_id:workflow.id,workspace,access:'read_only',main_actor:'root'});
  const lease=await runtime.claimHostMain(run.run_id,{node_id:'work',owner:'root',request_id:'claim-work',control_token:run.control_token});
  const binding={node_id:'work',attempt_id:lease.attempt_id,lease_token:lease.lease_token,control_token:run.control_token};
  const directory=runtime.runs.directory(run.run_id);
  const record=await runtime.runs.read(run.run_id);
  return {root,workspace,runtime,run,binding,directory,record,emit:event=>runtime.recordExecutorEvent(run.run_id,{...binding,event})};
}

test('observations and authority read fresh metadata without consuming 73 objects; explicit audit reads all',async t=>{
  const f=await fixture(t,73);assert.equal(f.record.pins.resources.length,73);
  let objectReads=0,journalReads=0,pinReads=0;
  await patched({readFile:async(path,...args)=>{if(String(path).startsWith(join(f.directory,'objects')))objectReads++;
    if(path===join(f.directory,'events.jsonl'))journalReads++;if(path===join(f.directory,'pins.json'))pinReads++;return native.readFile(path,...args);}},async()=>{
    for(const method of methods)assert.deepEqual(Object.keys(await f.emit(observation(method))),['sequence']);
    assert.equal(objectReads,0);assert.equal(journalReads,3);assert.equal(pinReads,3);
    await f.runtime.authorizedRun(f.run.run_id,f.binding);assert.equal(objectReads,0);
    await f.runtime.execution(f.run.run_id,f.binding);assert.equal(objectReads,0,'independent authority remains fresh');
    await f.runtime.runs.audit(f.run.run_id);assert.equal(objectReads,73);
  });
});

test('observation writes preserve original state shape, order and tail64 without changing any authority',async t=>{
  const f=await fixture(t),before=structuredClone(f.record.state),sent=[];
  for(let index=0;index<70;index++){
    const event=observation(methods[index%3],index);sent.push({sequence:index+1,...event});await f.emit(event);
  }
  const record=await f.runtime.runs.read(f.run.run_id),expected=structuredClone(before);
  expected.updated_at=record.state.updated_at;
  const attempt=expected.nodes.work.attempts[0];attempt.executor_event_count=70;attempt.executor_events=sent.slice(-64);
  assert.deepEqual(record.state,expected);
  const committed=record.events.filter(event=>event.kind==='executor_event');assert.equal(committed.length,70);
  assert.deepEqual(committed.map(event=>event.payload.patch.nodes.work.attempts[0].executor_events.at(-1)),sent);
  assert(committed.every(event=>Object.keys(event.payload.patch.fields).every(key=>key==='updated_at')&&
    Object.keys(event.payload.patch.nodes).join()==='work'&&!Object.keys(event.payload.patch.edges).length&&!Object.keys(event.payload.patch.approvals).length));
});

test('internal observation contract denies semantic events, invalid authority, and raw metadata without writing',async t=>{
  const f=await fixture(t),before=await native.readFile(join(f.directory,'events.jsonl'));
  for(const [args,code]of [
    [{...f.binding,control_token:'wrong',event:observation()},'RUN_AUTHORITY'],
    [{...f.binding,lease_token:'wrong',event:observation()},'LEASE_INVALID'],
    [{...f.binding,attempt_id:'other',event:observation()},'LEASE_INVALID'],
    [{...f.binding,event:{kind:'session_state',metadata:{status:'closed'}}},'EXECUTOR_OBSERVATION_KIND'],
    [{...f.binding,event:observation('turn/completed')},'EXECUTOR_OBSERVATION_KIND'],
    [{...f.binding,event:{kind:'codex_event',metadata:{method:methods[0],secret:{body:'raw'}}}},'EXECUTOR_EVENT_SCHEMA'],
    [{...f.binding,event:{kind:'codex_event',metadata:{method:methods[0],diagnostic:'x'.repeat(4097)}}},'EXECUTOR_EVENT_SCHEMA'],
    [{...f.binding,event:{kind:'codex_event',metadata:{method:methods[0],web_terms_count:1}}},'EXECUTOR_EVENT_SCHEMA'],
  ])await assert.rejects(f.runtime.runs.appendExecutorObservation(f.run.run_id,args),{code});
  assert.deepEqual(await native.readFile(join(f.directory,'events.jsonl')),before);
});

test('input event is snapshotted before awaiting admission and cannot become a semantic mutation',async t=>{
  const f=await fixture(t),event=observation();let entered,release;
  const started=new Promise(resolve=>entered=resolve),held=new Promise(resolve=>release=resolve);
  const original=f.runtime.runs.withRunWriter.bind(f.runtime.runs);
  f.runtime.runs.withRunWriter=async(...args)=>{entered();await held;return original(...args);};
  const operation=f.emit(event);await started;event.kind='session_state';event.metadata={status:'closed'};release();await operation;
  const record=await f.runtime.runs.read(f.run.run_id);assert.deepEqual(record.state.nodes.work.attempts[0].executor_events[0],{sequence:1,...observation()});
});

for(const boundary of ['authorize','execution','owned-tool','usage','result','accept','cancel'])
test(`committed pins tamper fails the next ${boundary} boundary before effect`,async t=>{
  const f=await fixture(t);
  await f.emit(observation());await f.emit(observation(methods[1]));
  await native.writeFile(join(f.directory,'pins.json'),'{}');
  const journal=await native.readFile(join(f.directory,'events.jsonl'));let effects=0,operations=0;
  const actions={
    authorize:()=>f.runtime.authorizedRun(f.run.run_id,f.binding),
    execution:()=>f.runtime.execution(f.run.run_id,f.binding),
    'owned-tool':async()=>{const broker=await createCodexToolBroker({workspace:f.workspace,access:'read_only',allowedPaths:[],resources:[],
      authorize:async()=>{await f.runtime.execution(f.run.run_id,f.binding);effects++;},onOperation:()=>operations++});
      await broker.call('list_workspace',{path:'.'},'call-one');},
    usage:()=>f.runtime.recordHostMainUsage(f.run.run_id,{...f.binding,request_id:'dispatch',usage:{}}),
    result:()=>f.emit({kind:'result_proposed',metadata:{artifact:'executor-'+f.binding.attempt_id+'-'+digest('result')+'.json',sha256:digest('result')}}),
    accept:()=>f.runtime.completeHostMainResult(f.run.run_id,f.binding,{accepted:true}),
    cancel:()=>f.runtime.cancel(f.run.run_id,f.binding,()=>effects++),
  };
  await assert.rejects(actions[boundary](),{code:'RUN_PINS_CORRUPT'});
  assert.equal(effects,0);assert.equal(operations,0);assert.deepEqual(await native.readFile(join(f.directory,'events.jsonl')),journal);
  assert.equal((replayEvents((await readEvents(join(f.directory,'events.jsonl'))).events)).status,'running');
});

test('retention preserves a live corrupt noncandidate; resource corruption remains visible to explicit audit',async t=>{
  const f=await fixture(t);await native.writeFile(join(f.directory,'objects',f.record.pins.resources[0].sha256),'tampered noncandidate');
  const journal=await native.readFile(join(f.directory,'events.jsonl'));
  const result=await f.runtime.runs.cleanupHistory({olderThanMs:0});
  assert.deepEqual(result.deleted_run_ids,[]);assert.deepEqual(result.preserved_run_ids,[f.run.run_id]);
  assert.deepEqual(await native.readFile(join(f.directory,'events.jsonl')),journal);
  await f.runtime.authorizedRun(f.run.run_id,f.binding);
  await assert.rejects(f.runtime.runs.audit(f.run.run_id),{code:'RUN_RESOURCE_CORRUPT'});
});

test('unknown and semantic executor events retain committed pins validation including cancellation settlement',async t=>{
  const f=await fixture(t);await native.writeFile(join(f.directory,'pins.json'),'{}');
  const events=[observation('future/notification'),observation('item/tool/call'),observation('workflow/command'),observation('workflow/sessionShutdown'),
    {kind:'session_state',metadata:{status:'closed'}},{kind:'result_proposed',metadata:{sha256:digest('proposal'),artifact:'proposal'}},
    {kind:'native_agent_spawn_intent',metadata:{index:0,agent_id:'root/child',task_name:'child'}},
    {kind:'native_agent_spawn',metadata:{index:0,agent_id:'root/child'}},{kind:'native_agent_followup_intent',metadata:{}},
    {kind:'native_agent_followup',metadata:{}},{kind:'tool_operation',metadata:{tool:'write_workspace',phase:'intent',path:'out'}}];
  for(const event of events)await assert.rejects(f.emit(event),{code:'RUN_PINS_CORRUPT'});
});

for(const target of ['journal','pins'])for(const fault of ['missing','directory','oversize','symlink','hash'])
test(`observation retains fresh ${target} ${fault} checks`,async t=>{
  const f=await fixture(t),path=join(f.directory,target==='journal'?'events.jsonl':'pins.json');
  if(fault==='oversize')await native.truncate(path,target==='journal'?128*1024*1024+1:16*1024*1024+1);
  else if(fault==='hash'){
    if(target==='journal'){const lines=(await native.readFile(path,'utf8')).trim().split('\n');const event=JSON.parse(lines[0]);event.hash='0'.repeat(64);lines[0]=canonicalJSON(event);await native.writeFile(path,lines.join('\n')+'\n');}
    else await native.writeFile(path,'{}');
  }else {await native.unlink(path);if(fault==='directory')await native.mkdir(path);
    if(fault==='symlink'){const outside=join(f.root,'outside');await native.mkdir(outside);await native.symlink(outside,path,process.platform==='win32'?'junction':'dir');}}
  const codes={missing:'ENOENT',directory:target==='journal'?'RUN_JOURNAL_LIMIT':'RUN_PINS_LIMIT',oversize:target==='journal'?'RUN_JOURNAL_LIMIT':'RUN_PINS_LIMIT',
    symlink:'WORKFLOW_SYMLINK',hash:target==='journal'?'RUN_JOURNAL_CORRUPT':'RUN_PINS_CORRUPT'};
  await assert.rejects(f.emit(observation()),{code:codes[fault]});
});

test('observation retains torn journal, Run identity and ancestor path failures',async t=>{
  for(const fault of ['torn','identity','ancestor']){
    const f=await fixture(t),path=join(f.directory,'events.jsonl');
    if(fault==='torn')await native.appendFile(path,'uncommitted');
    if(fault==='identity'){
      const lines=(await native.readFile(path,'utf8')).trim().split('\n').map(JSON.parse);let previous=null;
      lines[0].payload.state.run_id='other';for(const event of lines){event.previous=previous;const {hash,...content}=event;event.hash=digest(canonicalJSON(content));previous=event.hash;}
      await native.writeFile(path,lines.map(canonicalJSON).join('\n')+'\n');
    }
    if(fault==='ancestor'){const outside=join(f.root,'outside-run');await native.rename(f.directory,outside);await native.symlink(outside,f.directory,process.platform==='win32'?'junction':'dir');}
    await assert.rejects(f.emit(observation()),{code:{torn:'RUN_JOURNAL_TORN',identity:'RUN_IDENTITY',ancestor:'WORKFLOW_SYMLINK'}[fault]});
  }
});

function latch(){let resolve;const promise=new Promise(done=>resolve=done);return {promise,resolve};}
async function bounded(promise){let timer;try{return await Promise.race([promise,new Promise((_,reject)=>{timer=setTimeout(()=>reject(new Error('Expected latch did not enter')),2000);})]);}finally{clearTimeout(timer);}}
const fileProxy=(file,overrides)=>new Proxy(file,{get(target,key){if(key in overrides)return overrides[key];const value=Reflect.get(target,key);return typeof value==='function'?value.bind(target):value;}});

test('concurrent cancellation follows durable observation, and late metadata never revives or settles dispatch',async t=>{
  const f=await fixture(t);
  await f.runtime.recordHostMainDispatchIntent(f.run.run_id,{...f.binding,request_id:'dispatch',envelope_hash:digest('neutral')});
  const entered=latch(),release=latch();let cancelled=false,fenced=0;
  await patched({open:async(path,flags,...args)=>{const file=await native.open(path,flags,...args);
    if(path===join(f.directory,'events.jsonl')&&flags==='a')return fileProxy(file,{sync:async()=>{entered.resolve();await release.promise;return file.sync();}});return file;}},async()=>{
    const writing=f.emit(observation());await bounded(entered.promise);
    const cancelling=f.runtime.cancel(f.run.run_id,f.binding,()=>fenced++).then(()=>{cancelled=true;});
    try{assert.equal(cancelled,false);assert.equal(fenced,0);}finally{release.resolve();}
    await writing;await cancelling;
  });
  await f.emit(observation(methods[1]));const record=await f.runtime.runs.read(f.run.run_id),attempt=record.state.nodes.work.attempts[0];
  assert.equal(record.state.status,'cancelled');assert.equal(attempt.status,'cancelled');assert.equal(attempt.dispatch.cancellation_pending,true);
  assert.deepEqual(record.events.slice(-3).map(event=>event.kind),['executor_event','cancel','executor_event']);
  await assert.rejects(f.runtime.execution(f.run.run_id,f.binding),{code:'STALE_LEASE'});
});

for(const phase of ['sync','close'])test(`observation journal ${phase} failure remains visible and ownership releases`,async t=>{
  const f=await fixture(t),original=Object.assign(new Error('actual journal '+phase+' fault'),{code:'OBSERVATION_'+phase.toUpperCase()});
  await patched({open:async(path,flags,...args)=>{const file=await native.open(path,flags,...args);
    if(path===join(f.directory,'events.jsonl')&&flags==='a')return fileProxy(file,{[phase]:async()=>{if(phase==='close')await file.close();throw original;}});return file;}},async()=>{
    await assert.rejects(f.emit(observation()),error=>error===original);
  });
  await assert.rejects(native.lstat(join(f.directory,'.writer.lock')),{code:'ENOENT'});
  // A completed write with failed fsync/close is uncertain, not claimed absent.
  assert.equal((await f.runtime.runs.read(f.run.run_id)).state.nodes.work.attempts[0].executor_event_count,1);
});

test('awaited real App Server observation failure rejects pending turn waiter before completion can resolve',async t=>{
  const f=await fixture(t),entered=latch(),release=latch(),original=Object.assign(new Error('observation fsync failed'),{code:'OBSERVATION_SYNC'});
  const child=new EventEmitter();child.stdin=new PassThrough();child.stdout=new PassThrough();child.stderr=new PassThrough();let killed=0;
  child.kill=()=>{killed++;child.emit('exit',0,null);child.emit('close');};
  const client=createCodexClient('/neutral',{home:f.root,cwd:f.workspace,spawnImpl:()=>child,onEvent:async event=>{
    if(event.method===methods[0]){entered.resolve();await release.promise;await f.emit(observation());}
  }});
  let settled=false;
  const wait=client.waitFor(event=>event.method==='turn/completed',{timeout:2000}).then(value=>({value}),error=>({error})).finally(()=>settled=true);
  await patched({open:async(path,flags,...args)=>{const file=await native.open(path,flags,...args);
    if(path===join(f.directory,'events.jsonl')&&flags==='a')return fileProxy(file,{sync:async()=>{throw original;}});return file;}},async()=>{
    child.stdout.write(JSON.stringify({method:methods[0],params:{}})+'\n');await bounded(entered.promise);
    child.stdout.write(JSON.stringify({method:'turn/completed',params:{turn:{id:'neutral',status:'completed'}}})+'\n');
    try{assert.equal(settled,false);}finally{release.resolve();}
    const result=await wait;assert.equal(result.error,original);assert.equal(result.value,undefined);assert.equal(killed,1);
  });
  await client.close();
});

test('observation ownership cleanup failure retains its real error and never reports successful append',async t=>{
  const f=await fixture(t),original=Object.assign(new Error('actual retired owner deletion denied'),{code:'EIO'});let deletes=0;
  await patched({unlink:async(path,...args)=>{
    if(String(path).startsWith(join(f.directory,'.pending'))&&String(path).endsWith('record.json')){deletes++;throw original;}
    return native.unlink(path,...args);
  }},async()=>{
    await assert.rejects(f.emit(observation()),error=>{
      assert(error instanceof AggregateError);assert(error.errors.includes(original));
      assert.equal(error.details.retirement_failures[0].cause_code,'EIO');return true;
    });
  });
  assert.equal(deletes,1);await assert.rejects(native.lstat(join(f.directory,'.writer.lock')),{code:'ENOENT'});
  // The journal committed before cleanup failed. Preserve that uncertainty;
  // neither swallow the cleanup error nor describe the record as rolled back.
  assert.equal((await f.runtime.runs.read(f.run.run_id)).state.nodes.work.attempts[0].executor_event_count,1);
});

test('runtime observation schema retains original scalar/byte bounds and leaves invalid input uncommitted',async t=>{
  const f=await fixture(t),before=await native.readFile(join(f.directory,'events.jsonl'));
  const tooManyBytes={method:methods[0]};
  for(const key of ['thread_id','turn_id','item_id','call_id','process_id','tool_name','tool_server','diagnostic'])tooManyBytes[key]='x'.repeat(4096);
  for(const metadata of [tooManyBytes,{method:methods[0],input_tokens:1.5},{method:methods[0],status:{raw:'body'}},
    {method:methods[0],web_operation:'unknown'},{method:methods[0],web_operation:'search',web_terms_count:-1}])
    await assert.rejects(f.emit({kind:'codex_event',metadata}),{code:'EXECUTOR_EVENT_SCHEMA'});
  assert.deepEqual(await native.readFile(join(f.directory,'events.jsonl')),before);
});

test('actual forty-event batch reads journal/pins and syncs once, retaining every sealed record and authority',async t=>{
  const f=await fixture(t),events=Array.from({length:40},(_,i)=>observation(methods[i%3],i));
  let reads=0,pins=0,syncs=0,objects=0;
  const before=structuredClone(f.record.state);
  await patched({readFile:async(path,...args)=>{if(path===join(f.directory,'events.jsonl'))reads++;
    if(path===join(f.directory,'pins.json'))pins++;if(String(path).startsWith(join(f.directory,'objects')))objects++;
    return native.readFile(path,...args);},open:async(path,flags,...args)=>{const file=await native.open(path,flags,...args);
      if(path===join(f.directory,'events.jsonl')&&flags==='a')return fileProxy(file,{sync:async()=>{syncs++;await file.sync();}});return file;}},async()=>{
    const result=await f.runtime.recordExecutorObservations(f.run.run_id,{...f.binding,events});
    assert.equal(result.sequence,f.record.sequence+40);
  });
  assert.deepEqual({reads,pins,syncs,objects},{reads:1,pins:1,syncs:1,objects:0});
  const record=await f.runtime.runs.read(f.run.run_id),added=record.events.slice(f.record.sequence);
  assert.equal(added.length,40);
  for(let index=0;index<40;index++){
    assert.equal(added[index].kind,'executor_event');assert.equal(added[index].sequence,f.record.sequence+index+1);
    assert.equal(added[index].at,new Date(added[index].at).toISOString());
    const state=replayEvents(record.events.slice(0,f.record.sequence+index+1));
    assert.deepEqual(state.nodes.work.attempts[0].executor_events.at(-1),{sequence:index+1,...events[index]});
  }
  before.updated_at=record.state.updated_at;before.nodes.work.attempts[0].executor_event_count=40;
  before.nodes.work.attempts[0].executor_events=events.map((event,index)=>({sequence:index+1,...event}));
  assert.deepEqual(record.state,before,'batch cannot alter lease, usage, dispatch or semantic state');
});

test('batch rejects every invalid member before admission and freshly checks authority/lease/pins/journal',async t=>{
  const f=await fixture(t),before=await native.readFile(join(f.directory,'events.jsonl'));
  const batch=extras=>f.runtime.recordExecutorObservations(f.run.run_id,{...f.binding,events:[observation(),observation(methods[1])],...extras});
  for(const extras of [{control_token:'wrong'},{lease_token:'wrong'},
    {events:[observation(),observation('turn/completed')]},{events:[]},{events:Array.from({length:65},()=>observation())}])await assert.rejects(batch(extras));
  assert.deepEqual(await native.readFile(join(f.directory,'events.jsonl')),before);
  await native.writeFile(join(f.directory,'pins.json'),'{}');await assert.rejects(batch({}),{code:'RUN_PINS_CORRUPT'});
  await native.writeFile(join(f.directory,'pins.json'),canonicalJSON(f.record.pins));
  await native.appendFile(join(f.directory,'events.jsonl'),'torn');await assert.rejects(batch({}),{code:'RUN_JOURNAL_TORN'});
});

test('batch snapshots before admission, serializes cancellation and retains late dispatch/usage identity',async t=>{
  const f=await fixture(t),events=[observation(),observation(methods[2])],expected=structuredClone(events),entered=latch(),release=latch();
  await f.runtime.recordHostMainDispatchIntent(f.run.run_id,{...f.binding,request_id:'dispatch',envelope_hash:digest('neutral')});
  const original=f.runtime.runs.withRunWriter.bind(f.runtime.runs);
  f.runtime.runs.withRunWriter=async(...args)=>{entered.resolve();await release.promise;return original(...args);};
  const writing=f.runtime.recordExecutorObservations(f.run.run_id,{...f.binding,events});await entered.promise;
  events[0].kind='session_state';events[0].metadata={status:'closed'};events.length=1;release.resolve();await writing;
  const syncEntered=latch(),syncRelease=latch();let cancelled=false;
  await patched({open:async(path,flags,...args)=>{const file=await native.open(path,flags,...args);
    if(path===join(f.directory,'events.jsonl')&&flags==='a')return fileProxy(file,{sync:async()=>{syncEntered.resolve();await syncRelease.promise;await file.sync();}});return file;}},async()=>{
    const batch=f.runtime.recordExecutorObservations(f.run.run_id,{...f.binding,events:expected});await bounded(syncEntered.promise);
    const cancel=f.runtime.cancel(f.run.run_id,f.binding).then(()=>cancelled=true);
    assert.equal(cancelled,false);syncRelease.resolve();await batch;await cancel;
  });
  await f.runtime.recordExecutorObservations(f.run.run_id,{...f.binding,events:expected});
  const record=await f.runtime.runs.read(f.run.run_id),attempt=record.state.nodes.work.attempts[0];
  assert.equal(record.state.status,'cancelled');assert.equal(attempt.status,'cancelled');assert.equal(attempt.dispatch.cancellation_pending,true);
  assert.equal(attempt.executor_event_count,6);
  assert.deepEqual(attempt.executor_events.map(({sequence,...event})=>event),[...expected,...expected,...expected]);
  await assert.rejects(f.runtime.execution(f.run.run_id,f.binding),{code:'STALE_LEASE'});
});

test('actual batch sync failure rejects the turn and tool barrier, with committed records retained as uncertain',async t=>{
  const f=await fixture(t),entered=latch(),release=latch(),original=Object.assign(new Error('controlled durable sink failed'),{code:'CONTROLLED_SYNC'});
  const child=new EventEmitter();child.stdin=new PassThrough();child.stdout=new PassThrough();child.stderr=new PassThrough();
  child.kill=()=>{child.emit('exit',0,null);child.emit('close');};let effects=0;
  const client=createCodexClient('fake',{home:f.root,cwd:f.workspace,spawnImpl:()=>child,
    onToolCall:()=>effects++,onEventBatch:async messages=>{entered.resolve();await release.promise;
      await f.runtime.recordExecutorObservations(f.run.run_id,{...f.binding,events:messages.map((message,index)=>observation(message.method,index))});}});
  const wait=client.waitFor(event=>event.method==='turn/completed').then(value=>({value}),error=>({error}));
  await patched({open:async(path,flags,...args)=>{const file=await native.open(path,flags,...args);
    if(path===join(f.directory,'events.jsonl')&&flags==='a')return fileProxy(file,{sync:async()=>{throw original;}});return file;}},async()=>{
    child.stdout.write(Array.from({length:40},()=>JSON.stringify({method:'item/completed',params:{}})).join('\n')+'\n');
    await bounded(entered.promise);
    child.stdout.write(JSON.stringify({id:99,method:'item/tool/call',params:{}})+'\n'+JSON.stringify({method:'turn/completed',params:{}})+'\n');
    const flush=client.flushEvents().then(()=>({}),error=>({error}));release.resolve();
    assert.equal((await wait).error,original);assert.equal((await flush).error,original);assert.equal(effects,0);
  });
  await client.close();assert.equal((await f.runtime.runs.read(f.run.run_id)).state.nodes.work.attempts[0].executor_event_count,40);
});
