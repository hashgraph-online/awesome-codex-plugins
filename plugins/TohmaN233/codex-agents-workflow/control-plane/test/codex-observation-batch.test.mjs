import test from 'node:test';
import assert from 'node:assert/strict';
import {EventEmitter} from 'node:events';
import {PassThrough} from 'node:stream';
import {createCodexClient} from '../lib/execution/codex-app-server-client.mjs';
import {createCodexSession} from '../lib/execution/codex-session.mjs';
import {mkdtemp,mkdir,writeFile,rm} from 'node:fs/promises';
import {join} from 'node:path';
import {tmpdir} from './physical-tempdir.mjs';
import {digest} from '../lib/workflow-revisions.mjs';

const latch=()=>{let resolve;const promise=new Promise(done=>resolve=done);return {promise,resolve};};
const tick=()=>new Promise(resolve=>setImmediate(resolve));
function fixture(options){
  const child=new EventEmitter();child.stdin=new PassThrough();child.stdout=new PassThrough();child.stderr=new PassThrough();
  child.kill=()=>{child.emit('exit',0,null);child.emit('close');};
  child.stdin.on('finish',()=>child.kill());
  const client=createCodexClient('fake',{home:'fake',cwd:'.',spawnImpl:()=>child,...options});
  const emit=messages=>child.stdout.write(messages.map(JSON.stringify).join('\n')+'\n');
  return {child,client,emit};
}
const observations=Array.from({length:40},(_,index)=>({method:'item/completed',params:{item:{id:String(index),type:'reasoning'}}}));

test('controlled durable sink distinguishes provider response from serial notification backlog',async()=>{
  const gates=Array.from({length:41},latch);let calls=0,finished=false;
  const f=fixture({onEvent:async()=>{await gates[calls++].promise;}});
  const rpc=f.client.call('initialize',{});const turn=f.client.waitFor(e=>e.method==='turn/completed').then(()=>finished=true);
  f.emit([...observations,{method:'turn/completed',params:{}},{id:1,result:{provider:'already responded'}}]);
  assert.deepEqual(await rpc,{provider:'already responded'});await tick();assert.equal(calls,1);assert.equal(finished,false);
  for(let index=0;index<41;index++){assert.equal(calls,index+1);gates[index].resolve();await tick();}
  await turn;assert.equal(calls,41);await f.client.close();
});

test('forty observations use one ordered durable batch before terminal acceptance',async()=>{
  const entered=latch(),release=latch();const batches=[];let singles=0,finished=false;
  const f=fixture({onEvent:async()=>singles++,onEventBatch:async messages=>{batches.push(messages);entered.resolve();await release.promise;}});
  const rpc=f.client.call('initialize',{});const turn=f.client.waitFor(e=>e.method==='turn/completed').then(()=>finished=true);
  f.emit([...observations,{method:'turn/completed',params:{}},{id:1,result:{}}]);await rpc;await tick();
  assert.equal(batches.length,1,'notification persistence must aggregate, rather than silently ignore the batch sink');
  await entered.promise;assert.deepEqual(batches[0],observations);assert.equal(singles,0);assert.equal(finished,false);
  release.resolve();await turn;assert.equal(singles,1);assert.deepEqual(f.client.events,[...observations,{method:'turn/completed',params:{}}]);await f.client.close();
});

test('dynamic effect and explicit shutdown flush wait for the original durable batch',async()=>{
  const entered=latch(),release=latch();let effects=0,flushed=false,closed=false;
  const f=fixture({onEventBatch:async()=>{entered.resolve();await release.promise;},onToolCall:()=>{effects++;return {};}});
  f.emit(observations);await entered.promise;
  f.emit([{id:99,method:'item/tool/call',params:{}}]);
  const flush=f.client.flushEvents().then(()=>flushed=true);await tick();assert.equal(effects,0);assert.equal(flushed,false);
  const close=f.client.close().then(()=>closed=true);await tick();assert.equal(closed,false);
  release.resolve();await Promise.all([flush,close]);assert.equal(effects,1);assert.equal(closed,true);
});

test('batch cap and semantic separators retain complete ingress order without cross-boundary grouping',async()=>{
  const batches=[],order=[];
  const f=fixture({onEventBatch:async messages=>{batches.push(messages.length);order.push(...messages);},onEvent:async message=>order.push(message)});
  const messages=[...observations,...observations,{method:'turn/started',params:{}},...observations,{method:'turn/completed',params:{}}];
  const turn=f.client.waitFor(e=>e.method==='turn/completed');f.emit(messages);await turn;
  assert.deepEqual(batches,[64,16,40]);assert.deepEqual(order,messages);
  assert.equal(f.client.notificationStats().batched_events,120);assert.equal(f.client.notificationStats().queued_bytes,0);await f.client.close();
});

test('residual notification byte overflow fails visibly without accepting terminal completion',{timeout:5000},async t=>{
  const release=latch();const f=fixture({onEventBatch:()=>release.promise});
  t.after(async()=>{release.resolve();await f.client.close();});
  const turn=f.client.waitFor(()=>true,{timeout:1000}).then(value=>({value}),error=>({error}));
  const payload='x'.repeat(128*1024);
  f.emit(Array.from({length:70},(_,index)=>({method:'item/completed',params:{item:{id:String(index),type:'reasoning'},payload}})));
  const result=await turn;
  assert.equal(result.error.code,'CODEX_NOTIFICATION_QUEUE_LIMIT');assert.match(result.error.message,/byte bound/);
  assert.equal(result.value,undefined);
});

test('actual normal session routes scrubbed metadata batches and shutdown flush through the owned client',async t=>{
  const root=await mkdtemp(join(tmpdir(),'session-observation-batch-')),home=join(root,'home'),binary=join(root,'binary');
  await mkdir(home);await writeFile(binary,'fixture');let session,f;const batches=[],events=[];
  const entered=latch(),release=latch();
  t.after(async()=>{release.resolve();await session?.close();await rm(root,{recursive:true,maxRetries:3,retryDelay:100});});
  session=await createCodexSession({parent:root,binary,expectedBinaryHash:digest('fixture'),cwd:root,model:'fake',effort:'high',
    access:'read_only',dynamicToolFormat:'untagged_function',env:{CODEX_HOME:home},
    onEvent:event=>events.push(event),onObservationBatch:async metadata=>{batches.push(metadata);entered.resolve();await release.promise;},
    clientFactory:(_binary,launch)=>{
      f=fixture(launch);
      f.child.stdin.on('data',bytes=>{
        const request=JSON.parse(bytes);if(!Object.hasOwn(request,'id'))return;
        const results={initialize:{},'account/read':{account:{type:'chatgpt'},requiresOpenaiAuth:true},
          'model/list':{data:[{model:'fake',supportedReasoningEfforts:[{reasoningEffort:'high'}]}]}};
        assert(Object.hasOwn(results,request.method));f.emit([{id:request.id,result:results[request.method]}]);
      });return f.client;
    }});
  f.emit([{method:'thread/tokenUsage/updated',params:{threadId:'thread',turnId:'turn',secret:'raw-body',
    tokenUsage:{last:{inputTokens:17,outputTokens:3},total:{inputTokens:117,outputTokens:13}}}},...observations]);
  await entered.promise;const closing=session.close();await tick();
  assert.equal(events.some(event=>event.method==='workflow/sessionShutdown'),false);
  assert.equal(batches.length,1);assert.equal(batches[0].length,41);assert(!JSON.stringify(batches).includes('raw-body'));
  assert.equal(batches[0][0].input_tokens,17);assert.equal(batches[0][0].total_input_tokens,117);
  release.resolve();await closing;
  const begin=events.find(event=>event.method==='workflow/sessionShutdown'&&event.phase==='begin');
  assert.equal(begin.notification_delivery.batches,1);assert.equal(begin.notification_delivery.batched_events,41);
});

test('stalled durable sink cannot prevent exact client EOF and bounded pending shutdown failure',async()=>{
  const entered=latch(),release=latch();const f=fixture({onEventBatch:async()=>{entered.resolve();await release.promise;}});
  f.emit([...observations,...observations]);await entered.promise;let settled=false;
  const closing=f.client.close({timeout:25}).then(value=>({value}),error=>({error})).finally(()=>settled=true);
  try{
    await new Promise(resolve=>setTimeout(resolve,100));
    assert.equal(f.child.stdin.writableEnded,true,'exact owned EOF must precede stalled durable drain');
    assert.equal(settled,true,'client drain must reject within its shutdown deadline');
    assert.equal((await closing).error.code,'CODEX_NOTIFICATION_DRAIN_PENDING');
  }finally{release.resolve();await closing;await f.client.flushEvents();}
  assert.equal(f.client.notificationStats().batched_events,80,'all accepted batches drain after intentional zero exit');
  assert.equal(f.client.events.length,80);
});

test('actual session cleanup budget bounds stalled durability and retains pending ownership',async t=>{
  const root=await mkdtemp(join(tmpdir(),'session-stalled-durability-')),home=join(root,'home'),binary=join(root,'binary');
  await mkdir(home);await writeFile(binary,'fixture');let session,f;const events=[];
  const entered=latch(),release=latch();
  const causalError=Object.assign(new Error('late causal shutdown observer failed'),{code:'CAUSAL_OBSERVER_FAILED'});let rejectBegin=true;
  const deferredDone=latch();
  t.after(async()=>{release.resolve();await session?.close().catch(()=>{});await rm(root,{recursive:true,maxRetries:3,retryDelay:100});});
  session=await createCodexSession({parent:root,binary,expectedBinaryHash:digest('fixture'),cwd:root,model:'fake',effort:'high',
    access:'read_only',dynamicToolFormat:'untagged_function',env:{CODEX_HOME:home},clientShutdownTimeoutMs:25,
    onEvent:event=>{events.push(event);
      if(rejectBegin&&event.method==='workflow/sessionShutdown'&&event.phase==='begin'){rejectBegin=false;throw causalError;}
      if(event.method==='workflow/sessionShutdown'&&event.phase==='failed')deferredDone.resolve();},
    onObservationBatch:async()=>{entered.resolve();await release.promise;},
    clientFactory:(_binary,launch)=>{
      f=fixture(launch);f.child.stdin.on('data',bytes=>{const request=JSON.parse(bytes);if(!Object.hasOwn(request,'id'))return;
        const results={initialize:{},'account/read':{account:{type:'chatgpt'},requiresOpenaiAuth:true},
          'model/list':{data:[{model:'fake',supportedReasoningEfforts:[{reasoningEffort:'high'}]}]}};
        assert(Object.hasOwn(results,request.method));f.emit([{id:request.id,result:results[request.method]}]);});return f.client;
    }});
  f.emit(observations);await entered.promise;let settled=false;
  const closing=session.close().then(value=>({value}),error=>({error})).finally(()=>settled=true);
  try{
    await new Promise(resolve=>setTimeout(resolve,150));
    assert.equal(settled,true,'25ms existing cleanup budget cannot wait indefinitely before cleanup');
    assert.equal(f.child.stdin.writableEnded,true);assert((await closing).error);
    assert.equal(session.shutdownState().observation_pending,true);
    assert.equal(events.some(event=>event.method==='workflow/sessionShutdown'&&event.phase==='closed'),false);
  }finally{release.resolve();await closing;}
  await deferredDone.promise;await tick();
  assert.equal(session.shutdownState().observation_pending,false,'late failure must have settled before explicit retry');
  await assert.rejects(session.close(),error=>error===causalError,'next close must report the exact previously unreported late failure');
  assert(session.shutdownState().failures.some(failure=>failure.code==='CAUSAL_OBSERVER_FAILED'));
  await session.close();assert.equal(session.shutdownState().close_confirmed,true);
});

test('late durable rejection replaces intentional zero-exit sentinel and remains the original failure',async()=>{
  const entered=latch(),release=latch(),original=Object.assign(new Error('controlled late sink failure'),{code:'LATE_DURABLE_ERROR'});
  const f=fixture({onEventBatch:async()=>{entered.resolve();await release.promise;throw original;}});
  f.emit(observations);await entered.promise;
  const closing=f.client.close({timeout:1000}).then(value=>({value}),error=>({error}));
  await tick();assert.equal(f.child.stdin.writableEnded,true);release.resolve();
  assert.equal((await closing).error,original);await assert.rejects(f.client.flushEvents(),error=>error===original);
  assert.equal(f.client.notificationStats().error_code,'LATE_DURABLE_ERROR');assert.equal(f.client.events.length,0);
});

test('healthy forty-ms shutdown observer preserves the original twenty-five-ms client-only deadline',async t=>{
  const root=await mkdtemp(join(tmpdir(),'session-healthy-slow-observer-')),home=join(root,'home'),binary=join(root,'binary');
  await mkdir(home);await writeFile(binary,'fixture');let session,f;const events=[];
  t.after(async()=>{await session?.close().catch(()=>{});await rm(root,{recursive:true,maxRetries:3,retryDelay:100});});
  session=await createCodexSession({parent:root,binary,expectedBinaryHash:digest('fixture'),cwd:root,model:'fake',effort:'high',
    access:'read_only',dynamicToolFormat:'untagged_function',env:{CODEX_HOME:home},clientShutdownTimeoutMs:25,
    onEvent:async event=>{events.push(event);if(event.method==='workflow/sessionShutdown'&&event.phase==='begin')await new Promise(resolve=>setTimeout(resolve,40));},
    clientFactory:(_binary,launch)=>{
      f=fixture(launch);f.child.stdin.on('data',bytes=>{const request=JSON.parse(bytes);if(!Object.hasOwn(request,'id'))return;
        const results={initialize:{},'account/read':{account:{type:'chatgpt'},requiresOpenaiAuth:true},
          'model/list':{data:[{model:'fake',supportedReasoningEfforts:[{reasoningEffort:'high'}]}]}};
        assert(Object.hasOwn(results,request.method));f.emit([{id:request.id,result:results[request.method]}]);});return f.client;
    }});
  await session.close();assert.equal(f.child.stdin.writableEnded,true);
  assert.equal(session.shutdownState().close_confirmed,true);
  assert.equal(events.some(event=>event.method==='workflow/sessionShutdown'&&event.phase==='closed'),true);
});
