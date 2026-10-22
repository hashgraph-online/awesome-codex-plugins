import test from 'node:test';
import assert from 'node:assert/strict';
import {withNativeAgentObserver,withNativeAgentObserverDrive} from '../lib/execution/native-agent-observer.mjs';

function fixture(){
  const calls=[],clients=[],reports=[],env={CODEX_HOME:'test-home'};
  const discoverImpl=async()=>{calls.push('discover');return {binary:'test-codex'};};
  const clientFactory=()=>{
    const client={async call(method){calls.push(method);return {sequence:calls.length};},
      initialized(){calls.push('initialized');},async close(){calls.push('close');}};
    clients.push(client);return client;
  };
  return {calls,clients,reports,options:{env,clientFactory,discoverImpl,onObservation:async report=>reports.push(report)}};
}

test('one collection reuses one lazy connection but rereads current SDK results',async()=>{
  const f=fixture();let first,second;
  await withNativeAgentObserverDrive(async()=>{
    first=await withNativeAgentObserver(client=>client.call('thread/read'),f.options);
    second=await withNativeAgentObserver(client=>client.call('thread/read'),f.options);
  },f.options);
  assert.notDeepEqual(first,second);
  assert.deepEqual(f.calls,['discover','initialize','initialized','thread/read','thread/read','close']);
  assert.equal(f.reports[0].connections,1);assert.equal(f.reports[0].actions,2);
  assert.equal(f.reports[0].rpc['thread/read'].calls,2);
  await withNativeAgentObserver(client=>client.call('thread/read'),f.options);
  assert.equal(f.clients.length,2);assert.equal(f.reports.length,2);
});

test('a drive with no observer starts no process',async()=>{
  const f=fixture();assert.equal(await withNativeAgentObserverDrive(async()=>42,f.options),42);
  assert.deepEqual(f.calls,[]);assert.equal(f.reports[0].connections,0);
});

test('started concurrent actions settle before shutdown and failures cannot be swallowed',async()=>{
  const f=fixture();let release;
  const gate=new Promise(resolve=>release=resolve),boom=new Error('observation failed');
  const drive=withNativeAgentObserverDrive(async()=>{
    await withNativeAgentObserver(async()=>{
      void withNativeAgentObserver(async()=>{await gate;f.calls.push('settled');throw boom;},f.options);
    },f.options);
  },f.options);
  await new Promise(resolve=>setImmediate(resolve));assert(!f.calls.includes('close'));
  release();await assert.rejects(drive,error=>error===boom);
  assert(f.calls.indexOf('close')>f.calls.indexOf('settled'));
});

test('initialization failure still closes the exact client; shutdown failure preserves both causes',async()=>{
  const f=fixture(),initialize=new Error('initialize failed'),close=new Error('close failed');
  f.options.clientFactory=()=>({async call(){throw initialize;},initialized(){assert.fail();},async close(){throw close;}});
  await assert.rejects(withNativeAgentObserver(async()=>assert.fail(),f.options),error=>
    error instanceof AggregateError&&error.errors.includes(initialize)&&error.errors.includes(close));
});

test('incompatible and detached observer use fails rather than reopening an expired drive',async()=>{
  const f=fixture();let detached;
  await withNativeAgentObserverDrive(async()=>{
    await assert.rejects(withNativeAgentObserver(async()=>{}, {...f.options,env:{}}),{code:'NATIVE_AGENT_OBSERVER_SCOPE'});
    detached=new Promise(resolve=>setTimeout(async()=>{
      try{await withNativeAgentObserver(async()=>{},f.options);resolve(null);}catch(error){resolve(error);}
    },20));
  },f.options);
  assert.equal((await detached).code,'NATIVE_AGENT_OBSERVER_SCOPE_EXPIRED');assert.deepEqual(f.calls,[]);
});
