import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,readFile,writeFile,appendFile,rm,rename,open} from 'node:fs/promises';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {join} from 'node:path';
import {tmpdir} from './physical-tempdir.mjs';
import {deferred} from './fixtures/deferred.mjs';
import {createCodexCommandBroker} from '../lib/execution/codex-command-broker.mjs';
import {runHostCommand} from '../lib/execution/codex-command-runner.mjs';
import {EventEmitter} from 'node:events';
import {PassThrough} from 'node:stream';
import {prepareCommandLifecycleDiagnostics,readCommandLifecycleDiagnostics,releaseCommandLifecycleDiagnostics} from '../lib/execution/command-lifecycle-diagnostics.mjs';

async function fixture(t,{beforeResponse,observer,mutateLifecycle,runnerOptions,program="process.stdout.write('terminal tail')"}={}){
  const root=await mkdtemp(join(tmpdir(),'command-diagnostics-'));let spec,receipt;
  t.after(()=>rm(root,{recursive:true,force:true}));
  const client={async call(_method,params){spec=JSON.parse(await readFile(params.command.at(-1),'utf8'));
    receipt=await runHostCommand({...spec,argv:[process.execPath,'-e',program]},runnerOptions);
    await mutateLifecycle?.(spec,receipt);await beforeResponse?.(spec,receipt);
    return {exitCode:receipt.exit_code,stdout:JSON.stringify(receipt),stderr:''};},async close(){}};
  const broker=createCodexCommandBroker({binary:'fixture',home:root,cwd:root,access:'read_only',spoolRoot:join(root,'spool'),getClient:()=>client,
    getOutputBudget:()=>({max_result_bytes:4096}),onOperation:observer??(async()=>{})});
  t.after(()=>broker.close());
  return {broker,root,spec:()=>spec,receipt:()=>receipt};
}
const result=reply=>JSON.parse(reply.contentItems[0].text);

for(const mode of ['close-before-exit','drain-before-exit'])test(`real runner reordered ${mode} with increasing UTC cannot become complete evidence`,async t=>{
  const f=await fixture(t,{mutateLifecycle:async spec=>{
    const events=(await readFile(spec.lifecycle_path,'utf8')).trim().split('\n').map(JSON.parse);
    const started=events.find(event=>event.phase==='started'),exit=events.find(event=>event.phase==='child_exit'),close=events.find(event=>event.phase==='child_close');
    const reordered=mode==='close-before-exit'?[started,...events.filter(event=>event.phase==='stream_close'),close,exit,events.at(-1)]
      :[started,{process_id:spec.process_id,phase:'stdio_drain_timeout',child_pid:started.child_pid},...events.filter(event=>event.phase==='stream_close'),exit,close,events.at(-1)];
    const origin=Date.parse(started.at);reordered.forEach((event,index)=>event.at=new Date(origin+index).toISOString());
    await writeFile(spec.lifecycle_path,reordered.map(event=>JSON.stringify(event)).join('\n')+'\n');
  }});
  const done=result(await f.broker.call('run_workspace_command',{cmd:'fixture'},mode));assert.equal(done.exit_code,0);
  assert.equal(f.broker.audit()[0].diagnostics.runner.status,'unknown');
  assert.equal(f.broker.audit()[0].diagnostics.runner.error_code,'CODEX_COMMAND_LIFECYCLE_PHASE_ORDER');
});

test('real regular file replacement after terminal receipt cannot replace the captured lifecycle identity',async t=>{
  const f=await fixture(t,{mutateLifecycle:async spec=>{
    const bytes=await readFile(spec.lifecycle_path);await rename(spec.lifecycle_path,spec.lifecycle_path+'.original');await writeFile(spec.lifecycle_path,bytes);
  }});
  const done=result(await f.broker.call('run_workspace_command',{cmd:'fixture'},'replaced'));assert.equal(done.exit_code,0);
  assert.equal(f.broker.audit()[0].diagnostics.runner.status,'unknown');
  assert.equal(f.broker.audit()[0].diagnostics.runner.error_code,'CODEX_COMMAND_LIFECYCLE_PATH_CHANGED');
});

test('real POSIX writerless FIFO replacement cannot stall an otherwise valid original command receipt',{skip:process.platform==='win32'},async t=>{
  const root=await mkdtemp(join(tmpdir(),'command-lifecycle-fifo-'));t.after(()=>rm(root,{recursive:true,force:true}));
  const brokerURL=new URL('../lib/execution/codex-command-broker.mjs',import.meta.url).href,runnerURL=new URL('../lib/execution/codex-command-runner.mjs',import.meta.url).href;
  const script=`import {createCodexCommandBroker} from ${JSON.stringify(brokerURL)};import {runHostCommand} from ${JSON.stringify(runnerURL)};
    import {readFile,rm} from 'node:fs/promises';import {execFile} from 'node:child_process';import {promisify} from 'node:util';
    const client={async call(_method,params){const spec=JSON.parse(await readFile(params.command.at(-1),'utf8'));const receipt=await runHostCommand({...spec,argv:[process.execPath,'-e',"process.stdout.write('FIFO tail')"]});await rm(spec.lifecycle_path);await promisify(execFile)('mkfifo',[spec.lifecycle_path]);return {exitCode:receipt.exit_code,stdout:JSON.stringify(receipt),stderr:''};},async close(){}};
    const broker=createCodexCommandBroker({binary:'fixture',home:${JSON.stringify(root)},cwd:${JSON.stringify(root)},access:'read_only',spoolRoot:${JSON.stringify(join(root,'spool'))},getClient:()=>client,getOutputBudget:()=>({max_result_bytes:4096})});
    const done=JSON.parse((await broker.call('run_workspace_command',{cmd:'fixture'},'fifo')).contentItems[0].text);const audit=broker.audit();await broker.close();process.stdout.write(JSON.stringify({done,audit}));`;
  // Only this fixture-owned child is bounded; production has no new timer.
  const output=await promisify(execFile)(process.execPath,['--input-type=module','-e',script],{timeout:3000,killSignal:'SIGKILL'});
  const observed=JSON.parse(output.stdout);assert.equal(observed.done.exit_code,0);assert.equal(observed.done.output,'FIFO tail');
  assert.equal(observed.audit[0].diagnostics.runner.status,'unknown');assert.equal(observed.audit[0].diagnostics.runner.error_code,'CODEX_COMMAND_LIFECYCLE_PATH_CHANGED');
});

test('exclusive capture failure and released/unknown ticket are explicit unknown without terminal path fallback',async t=>{
  const root=await mkdtemp(join(tmpdir(),'lifecycle-capability-'));t.after(()=>rm(root,{recursive:true,force:true}));
  const path=join(root,'lifecycle');await writeFile(path,'private existing evidence');
  const existing=await prepareCommandLifecycleDiagnostics(path,'owned');
  const failed=await readCommandLifecycleDiagnostics(existing,'owned');
  assert.equal(failed.status,'unknown');assert.equal(failed.error_code,'CODEX_COMMAND_LIFECYCLE_CAPTURE_FAILED');assert.equal(failed.filesystem_code,'EEXIST');
  assert(!JSON.stringify(failed).includes('private existing'));
  assert.equal((await readCommandLifecycleDiagnostics(existing,'owned')).error_code,'CODEX_COMMAND_LIFECYCLE_CAPABILITY_UNAVAILABLE');
  await rm(path);const ticket=await prepareCommandLifecycleDiagnostics(path,'owned');
  assert.equal((await readCommandLifecycleDiagnostics(ticket,'other')).error_code,'CODEX_COMMAND_LIFECYCLE_CAPABILITY_UNAVAILABLE');
  assert.equal(await releaseCommandLifecycleDiagnostics(ticket),null);
  assert.equal((await readCommandLifecycleDiagnostics(ticket,'owned')).error_code,'CODEX_COMMAND_LIFECYCLE_CAPABILITY_UNAVAILABLE');
  assert.equal(await releaseCommandLifecycleDiagnostics(ticket),null);
});

test('real POSIX exclusive capture of a writerless FIFO fails without opening it',{skip:process.platform==='win32'},async t=>{
  const root=await mkdtemp(join(tmpdir(),'lifecycle-exclusive-fifo-'));t.after(()=>rm(root,{recursive:true,force:true}));
  const path=join(root,'fifo');await promisify(execFile)('mkfifo',[path]);
  const ticket=await prepareCommandLifecycleDiagnostics(path,'owned');
  const observed=await readCommandLifecycleDiagnostics(ticket,'owned');
  assert.equal(observed.status,'unknown');assert.equal(observed.error_code,'CODEX_COMMAND_LIFECYCLE_CAPTURE_FAILED');assert.equal(observed.filesystem_code,'EEXIST');
});

for(const mode of ['success','synchronous-rpc-error','started-observer-error','completed-observer-error','cancel','diagnostic-close-error','startup-close-error'])
test(`actual FileHandle lifecycle capability closes exactly once for ${mode} and preserves original errors`,async t=>{
  const root=await mkdtemp(join(tmpdir(),'lifecycle-fd-close-'));t.after(()=>rm(root,{recursive:true,force:true}));
  const probe=await open(join(root,'probe'),'wx+'),prototype=Object.getPrototypeOf(probe),originalStat=prototype.stat;await probe.close();
  const handles=new Set(),closed=new Map();
  t.mock.method(prototype,'stat',async function(options){
    if(options?.bigint&&!handles.has(this)){
      handles.add(this);const originalClose=this.close;
      t.mock.method(this,'close',async function(){closed.set(this,(closed.get(this)??0)+1);const result=await originalClose.call(this);
        if(['diagnostic-close-error','startup-close-error'].includes(mode))throw Object.assign(new Error('private close evidence'),{code:'EIO'});return result;});
    }
    return originalStat.call(this,options);
  });
  const failure=Object.assign(new Error('original exact owned failure'),{code:'EXACT_OWNED_FAILURE'});
  const client={call(_method,params){
    if(['synchronous-rpc-error','startup-close-error'].includes(mode))throw failure;
    return (async()=>{const spec=JSON.parse(await readFile(params.command.at(-1),'utf8'));
      const receipt=await runHostCommand({...spec,argv:[process.execPath,'-e',mode==='cancel'?'setInterval(()=>{},1000)':"process.stdout.write('close tail')"]});
      return {exitCode:receipt.exit_code,stdout:JSON.stringify(receipt),stderr:''};})();
  },async close(){}};
  const broker=createCodexCommandBroker({binary:'fixture',home:root,cwd:root,access:'read_only',spoolRoot:join(root,'spool'),getClient:()=>client,getOutputBudget:()=>({max_result_bytes:4096}),
    onOperation:async event=>{if(mode==='started-observer-error'&&event.phase==='started'||mode==='completed-observer-error'&&event.phase==='completed')throw failure;}});
  if(mode==='cancel'){
    const started=result(await broker.call('run_workspace_command',{cmd:'fixture',yield_time_ms:0},mode));await broker.interrupt();
    assert.equal(result(await broker.call('continue_workspace_command',{session_id:started.session_id,yield_time_ms:1000},'cancelled')).exit_code,130);
  }else if(['success','diagnostic-close-error'].includes(mode))assert.equal(result(await broker.call('run_workspace_command',{cmd:'fixture'},mode)).exit_code,0);
  else await assert.rejects(broker.call('run_workspace_command',{cmd:'fixture'},mode),error=>error===failure);
  if(mode==='completed-observer-error')await assert.rejects(broker.close(),error=>error===failure);else await broker.close();
  await broker.close();
  if(mode==='diagnostic-close-error'){
    const diagnostic=broker.audit()[0].diagnostics.runner;assert.equal(diagnostic.status,'unknown');assert.equal(diagnostic.error_code,'CODEX_COMMAND_LIFECYCLE_CLOSE_FAILED');assert.equal(diagnostic.filesystem_code,'EIO');
  }
  if(mode==='startup-close-error')assert.equal(failure.command_lifecycle_diagnostic.error_code,'CODEX_COMMAND_LIFECYCLE_CLOSE_FAILED');
  assert.equal(handles.size,mode==='started-observer-error'?0:1);
  for(const handle of handles){assert.equal(closed.get(handle),1);assert.equal(handle.fd,-1);}
});

test('real runner receipt precedes gated RPC response and remains identifiable after successful cleanup',async t=>{
  const ready=deferred(),response=deferred();
  const f=await fixture(t,{beforeResponse:async()=>{ready.resolve();await response.promise;}});
  const started=result(await f.broker.call('run_workspace_command',{cmd:'fixture',yield_time_ms:0},'late-rpc'));
  await ready.promise;assert.equal(f.broker.audit().length,0);
  assert.match(await readFile(f.spec().lifecycle_path,'utf8'),/"phase":"receipt"/);
  await new Promise(resolve=>setTimeout(resolve,30));response.resolve();
  const done=result(await f.broker.call('continue_workspace_command',{session_id:started.session_id,yield_time_ms:1000},'finish'));
  assert.equal(done.output,'terminal tail');assert.equal(done.status,'completed');
  await assert.rejects(readFile(f.spec().lifecycle_path),{code:'ENOENT'});
  const diagnostic=f.broker.audit()[0].diagnostics;
  assert.equal(diagnostic.runner.status,'complete');
  assert.equal(diagnostic.runner.boundaries.receipt.at,new Date(Date.parse(diagnostic.runner.boundaries.receipt.at)).toISOString());
  assert(Date.parse(diagnostic.parent.rpc_response_at)-Date.parse(diagnostic.runner.boundaries.receipt.at)>=25);
  assert(diagnostic.parent.settlement_ms>=diagnostic.parent.observation_end_ms);
  assert(!JSON.stringify(diagnostic).includes('terminal tail'));
});

test('delayed original completed observer retains running semantics and final settlement only after release',async t=>{
  const observed=deferred(),release=deferred();
  const f=await fixture(t,{observer:async event=>{if(event.phase==='completed'){observed.resolve();await release.promise;}}});
  const started=result(await f.broker.call('run_workspace_command',{cmd:'fixture',yield_time_ms:0},'observer'));
  await observed.promise;
  const before=f.broker.audit()[0].diagnostics;
  assert.equal(before.parent.settlement_ms,null);assert.equal(before.parent.observation_end_ms,null);
  assert.equal(before.runner.status,'complete');
  assert.equal(result(await f.broker.call('continue_workspace_command',{session_id:started.session_id,yield_time_ms:0},'pending')).status,'running');
  await new Promise(resolve=>setTimeout(resolve,30));release.resolve();
  assert.equal(result(await f.broker.call('continue_workspace_command',{session_id:started.session_id,yield_time_ms:1000},'settled')).status,'completed');
  const after=f.broker.audit()[0].diagnostics;
  assert(after.parent.observation_end_ms-after.parent.observation_begin_ms>=25);
  assert.equal(after.parent.settlement,'fulfilled');
  assert(after.parent.settlement_ms>=after.parent.observation_end_ms);
});

for(const mode of ['missing','identity','clock','oversize','schema','future','receipt','read-error'])test(`successful original receipt retains explicit unknown ${mode} lifecycle without replay`,async t=>{
  let calls=0,readFaults=0;
  const f=await fixture(t,{mutateLifecycle:async spec=>{
    calls++;if(mode==='missing')return rm(spec.lifecycle_path);
    if(mode==='read-error'){
      // Windows can retain the deleted name while the captured handle is open.
      // Fail the exact descriptor read instead of replacing it with a directory.
      const probe=await open(spec.lifecycle_path,'r'),prototype=Object.getPrototypeOf(probe),expected=await probe.stat({bigint:true});
      const originalRead=prototype.read;await probe.close();
      t.mock.method(prototype,'read',async function(...args){
        const info=await this.stat({bigint:true});
        if(info.dev===expected.dev&&info.ino===expected.ino){readFaults++;throw Object.assign(new Error('Exact lifecycle read failed'),{code:'EIO'});}
        return originalRead.apply(this,args);
      });
      return;
    }
    const lines=(await readFile(spec.lifecycle_path,'utf8')).trim().split('\n').map(JSON.parse);
    if(mode==='identity')lines[0].process_id='another-attempt';
    if(mode==='clock')lines.at(-1).at='2000-01-01T00:00:00.000Z';
    if(mode==='schema')lines.find(event=>event.phase==='child_exit').exit_code='0';
    if(mode==='future')for(const event of lines)event.at='2100-01-01T00:00:00.000Z';
    if(mode==='receipt')lines.at(-1).output_bytes++;
    await writeFile(spec.lifecycle_path,mode==='oversize'?'x'.repeat(20000):lines.map(line=>JSON.stringify(line)).join('\n')+'\n');
  }});
  const done=result(await f.broker.call('run_workspace_command',{cmd:'fixture'},mode));
  assert.equal(done.status,'completed');assert.equal(done.exit_code,0);assert.equal(calls,1);
  const diagnostic=f.broker.audit()[0].diagnostics;
  assert.equal(diagnostic.runner.status,'unknown');assert.match(diagnostic.runner.error_code,/^CODEX_COMMAND_LIFECYCLE_/);
  assert.equal(diagnostic.parent.settlement,'fulfilled');
  if(mode==='read-error'){
    assert.equal(readFaults,1);assert.equal(diagnostic.runner.error_code,'CODEX_COMMAND_LIFECYCLE_READ_FAILED');
    assert.equal(diagnostic.runner.filesystem_code,'EIO');
  }
});

test('original cancelled control receipt retains real lifecycle and cancellation outcome',async t=>{
  const f=await fixture(t,{program:"process.stdout.write('cancel tail');setInterval(()=>{},1000)"});
  const started=result(await f.broker.call('run_workspace_command',{cmd:'fixture',yield_time_ms:0},'cancel'));
  while(!f.spec())await new Promise(resolve=>setImmediate(resolve));
  await f.broker.interrupt();
  const done=result(await f.broker.call('continue_workspace_command',{session_id:started.session_id,yield_time_ms:1000},'cancelled'));
  assert.equal(done.exit_code,130);assert.equal(f.broker.audit()[0].status,'cancelled');
  const diagnostic=f.broker.audit()[0].diagnostics;
  assert.equal(diagnostic.runner.status,'complete');assert(diagnostic.runner.phase_counts.stop_control_consumed>=1);
  assert.equal(diagnostic.parent.settlement,'fulfilled');
});

for(const closeAfterDrain of [false,true])test(`real runner held-pipe failure retains verified drain phase${closeAfterDrain?' with legal later child close':''}`,async t=>{
  const child=new EventEmitter();Object.assign(child,{pid:123,stdin:new PassThrough(),stdout:new PassThrough(),stderr:new PassThrough(),kill:()=>true});
  if(closeAfterDrain)child.stderr.once('close',()=>child.emit('close',0,null));
  const f=await fixture(t,{runnerOptions:{drainTimeoutMs:10,spawnImpl:()=>{
    setImmediate(()=>{child.stdout.write('held tail');child.emit('exit',0,null);});return child;
  }}});
  await assert.rejects(f.broker.call('run_workspace_command',{cmd:'fixture'},'held'),{code:'CODEX_COMMAND_PIPE_HELD'});
  const audit=f.broker.audit()[0];assert.equal(audit.status,'failed');
  assert.equal(audit.diagnostics.runner.status,'complete');
  assert.equal(audit.diagnostics.runner.phase_counts.stdio_drain_timeout,1);
  assert.equal(audit.diagnostics.runner.boundaries.receipt.error_code,'CODEX_COMMAND_PIPE_HELD');
  assert.equal(audit.diagnostics.parent.terminal_error_code,'CODEX_COMMAND_PIPE_HELD');
  await assert.rejects(f.broker.close(),{code:'CODEX_COMMAND_PIPE_HELD'});
});

test('real runner lifecycle-write failure preserves execution failure and explicit partial diagnostic evidence',async t=>{
  let calls=0;
  const f=await fixture(t,{runnerOptions:{appendLifecycleImpl:async(path,text)=>{
    if(++calls===1)throw Object.assign(new Error('private lifecycle error body'),{code:'EACCES'});
    const {appendFile}=await import('node:fs/promises');await appendFile(path,text);
  }}});
  await assert.rejects(f.broker.call('run_workspace_command',{cmd:'fixture'},'write-failure'),{code:'CODEX_COMMAND_LIFECYCLE_FAILED'});
  const diagnostic=f.broker.audit()[0].diagnostics;
  assert.equal(diagnostic.runner.status,'partial');assert.equal(diagnostic.runner.error_code,'CODEX_COMMAND_LIFECYCLE_FAILED');
  assert.equal(diagnostic.runner.boundaries.started,null);assert(!JSON.stringify(diagnostic).includes('private lifecycle'));
  await assert.rejects(f.broker.close(),{code:'CODEX_COMMAND_LIFECYCLE_FAILED'});
});

test('original observation rejection remains visible without erasing genuine successful runner effects',async t=>{
  const f=await fixture(t,{observer:async event=>{if(['completed','failed'].includes(event.phase))throw Object.assign(new Error('private observer body'),{code:'OBSERVATION_DISK'});}});
  await assert.rejects(f.broker.call('run_workspace_command',{cmd:'fixture'},'observer-error'),{code:'OBSERVATION_DISK'});
  const audits=f.broker.audit();assert.equal(audits[0].status,'completed');assert.equal(audits[0].exit_code,0);assert.equal(audits[1].status,'failed');
  assert.equal(audits[0].diagnostics.parent.settlement,'rejected');assert.equal(audits[0].diagnostics.runner.status,'complete');
  assert.equal(audits[0].diagnostics.parent.observations.length,2);assert(audits[0].diagnostics.parent.observations.every(event=>event.error_code==='OBSERVATION_DISK'));
  assert(!JSON.stringify(audits[0].diagnostics).includes('private observer'));
  await assert.rejects(f.broker.close(),{code:'CODEX_COMMAND_OBSERVATION_FAILED'});
});

test('terminal RPC rejection retains exact partial runner evidence and original error',async t=>{
  const root=await mkdtemp(join(tmpdir(),'partial-command-diagnostics-'));let spec,running;
  t.after(()=>rm(root,{recursive:true,force:true}));
  const started=deferred();
  const client={async call(_method,params){
    spec=JSON.parse(await readFile(params.command.at(-1),'utf8'));
    running=runHostCommand({...spec,argv:[process.execPath,'-e','setInterval(()=>{},1000)']},{appendLifecycleImpl:async(path,text)=>{
      await appendFile(path,text);if(JSON.parse(text).phase==='started')started.resolve();
    }});await started.promise;
    throw Object.assign(new Error('private RPC body'),{code:'CODEX_RPC_ERROR'});
  },async close(){}};
  const broker=createCodexCommandBroker({binary:'fixture',home:root,cwd:root,access:'read_only',spoolRoot:join(root,'spool'),getClient:()=>client,getOutputBudget:()=>({max_result_bytes:4096})});
  try{
    await assert.rejects(broker.call('run_workspace_command',{cmd:'fixture'},'partial'),{code:'CODEX_RPC_ERROR'});
    const audit=broker.audit()[0];assert.equal(audit.status,'failed');
    assert.equal(audit.diagnostics.runner.status,'partial');assert.equal(audit.diagnostics.runner.boundaries.receipt,null);
    assert.equal(audit.diagnostics.runner.phase_counts.started,1);assert.equal(audit.diagnostics.parent.rpc_outcome,'rejected');
    assert.equal(audit.diagnostics.parent.terminal_error_code,'CODEX_RPC_ERROR');assert(!JSON.stringify(audit.diagnostics).includes('private RPC'));
    await assert.rejects(broker.close(),{code:'CODEX_RPC_ERROR'});
  }finally{
    // This runner belongs to the fixture; original rejected-RPC semantics are
    // unchanged. Reap it through its exact original control file, never a PID.
    if(spec)await appendFile(spec.stdin_path,'\u0003');if(running)await running;await broker.close();
  }
});
