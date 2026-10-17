import { deferred } from './fixtures/deferred.mjs';
import test from 'node:test';
import assert from 'node:assert/strict';
import { appendFile,mkdir,mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from './physical-tempdir.mjs';
import { dirname,join } from 'node:path';
import { createCodexCommandBroker as createCodexCommandBrokerImpl } from '../lib/execution/codex-command-broker.mjs';
const createCodexCommandBroker=options=>createCodexCommandBrokerImpl({getOutputBudget:()=>({max_result_bytes:1024*1024}),...options});
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { fileURLToPath } from 'node:url';
import { EventEmitter } from 'node:events';
import { PassThrough } from 'node:stream';
import { runHostCommand } from '../lib/execution/codex-command-runner.mjs';

for(const stalled of [false,true,'all'])test(`runner lifecycle ${stalled==='all'?'all stalled':stalled?'first stalled':'first failed'} append preserves bounded cleanup and subsequent evidence`,async t=>{
  const root=await mkdtemp(join(tmpdir(),'runner-observation-'));t.after(()=>rm(root,{recursive:true,force:true}));
  const spec={schema_version:1,process_id:'owned-observation-session',argv:[process.execPath],cwd:root,
    output_path:join(root,'output'),stdin_path:join(root,'stdin'),lifecycle_path:join(root,'lifecycle')};
  await writeFile(spec.stdin_path,'');let calls=0;
  const child=new EventEmitter();Object.assign(child,{pid:123,stdin:new PassThrough(),stdout:new PassThrough(),stderr:new PassThrough(),kill:()=>true});
  let timeout;
  const running=runHostCommand(spec,{drainTimeoutMs:10,observationTimeoutMs:20,appendLifecycleImpl:async(path,text)=>{
    if(++calls===1||stalled==='all'){if(stalled)return new Promise(()=>{});throw Object.assign(new Error('sensitive diagnostic'),{code:'EACCES'});}
    await appendFile(path,text);
  },spawnImpl:()=>{setImmediate(()=>{child.stdout.write('tail retained');child.stderr.write('stderr retained');child.emit('exit',7,null);});return child;}});
  let receipt;try{receipt=await Promise.race([running,new Promise((_,reject)=>{timeout=setTimeout(()=>reject(new Error('Lifecycle evidence blocked bounded cleanup')),500);})]);}
  finally{clearTimeout(timeout);}
  assert.equal(receipt.error_code,'CODEX_COMMAND_LIFECYCLE_FAILED');
  assert.equal(receipt.command_exit_code,7);assert.equal(receipt.execution_error_code,'CODEX_COMMAND_PIPE_HELD');
  assert(receipt.lifecycle_errors.some(error=>error.phase==='started'&&error.code===(stalled?'CODEX_COMMAND_LIFECYCLE_TIMEOUT':'EACCES')));
  assert(child.stdout.destroyed&&child.stderr.destroyed&&child.stdin.writableEnded);
  assert.equal(await readFile(spec.output_path,'utf8'),'tail retainedstderr retained');
  if(stalled==='all'){
    assert(receipt.lifecycle_errors.some(error=>error.phase==='lifecycle_flush'));
    assert(receipt.lifecycle_errors.some(error=>error.phase==='receipt'));return;
  }
  const events=(await readFile(spec.lifecycle_path,'utf8')).trim().split('\n').map(JSON.parse);
  assert(events.some(event=>event.phase==='receipt'&&event.error_code==='CODEX_COMMAND_LIFECYCLE_FAILED'));
  if(!stalled)assert(events.some(event=>event.phase==='child_exit'));
  assert(!JSON.stringify(events).includes('sensitive diagnostic'));
});

test('real runner lifecycle filesystem rejection retains control receipt and normal child tail',async t=>{
  const root=await mkdtemp(join(tmpdir(),'runner-filesystem-observation-'));t.after(()=>rm(root,{recursive:true,force:true}));
  const specPath=join(root,'spec'),outputPath=join(root,'output'),stdinPath=join(root,'stdin');await writeFile(stdinPath,'');
  await writeFile(specPath,JSON.stringify({schema_version:1,process_id:'owned-filesystem-session',argv:[process.execPath,'-e',`process.stdout.write('normal tail');setTimeout(()=>process.exit(7),30)`],
    cwd:root,output_path:outputPath,stdin_path:stdinPath,lifecycle_path:root}));
  let result;try{result=await promisify(execFile)(process.execPath,[fileURLToPath(new URL('../lib/execution/codex-command-runner.mjs',import.meta.url)),specPath]);}
  catch(error){result=error;}
  const receipt=JSON.parse(result.stdout);assert.equal(receipt.error_code,'CODEX_COMMAND_LIFECYCLE_FAILED');
  assert.equal(receipt.exit_code,1);assert.equal(receipt.command_exit_code,7);
  assert(receipt.lifecycle_errors.some(error=>error.phase==='started'));
  assert(receipt.lifecycle_errors.some(error=>error.phase==='child_exit'));
  assert(receipt.lifecycle_errors.some(error=>error.phase==='receipt'));
  assert.equal(await readFile(outputPath,'utf8'),'normal tail');assert.equal(result.stderr,'');
});

test('yield zero settlement notifications have an immediate rejection handler and retain cleanup errors',async t=>{
  const root=await mkdtemp(join(tmpdir(),'broker-background-rejection-'));t.after(()=>rm(root,{recursive:true,force:true}));
  const moduleURL=new URL('../lib/execution/codex-command-broker.mjs',import.meta.url).href;
  const script=`import {createCodexCommandBroker} from ${JSON.stringify(moduleURL)};
    import {readFile,writeFile} from 'node:fs/promises';
    const unhandled=[],events=[];process.on('unhandledRejection',error=>unhandled.push(error.code));
    let settle,closed=0,notificationStarted,releaseNotification;
    const pending=new Promise(done=>settle=done),notificationReady=new Promise(done=>notificationStarted=done),notificationHold=new Promise(done=>releaseNotification=done);
    const client={initialized(){},async call(method,args){if(method==='initialize')return {};const spec=JSON.parse(await readFile(args.command.at(-1),'utf8'));await writeFile(spec.output_path,'tail');await pending;return {exitCode:0,stdout:JSON.stringify({schema_version:1,exit_code:0,output_bytes:4}),stderr:''};},async close(){closed++;}};
    const broker=createCodexCommandBroker({binary:'fixture',home:${JSON.stringify(root)},cwd:${JSON.stringify(root)},spoolRoot:${JSON.stringify(join(root,'spool'))},access:'read_only',env:{},clientFactory:()=>client,getOutputBudget:()=>({max_result_bytes:10000}),
      onOperation:async event=>{events.push(event.phase);if(event.phase==='completed'){notificationStarted();await notificationHold;}if(['completed','failed'].includes(event.phase))throw Object.assign(new Error('authority rotated'),{code:event.phase==='completed'?'RUN_AUTHORITY':'FAILED_NOTIFICATION'});}});
    const started=JSON.parse((await broker.call('run_workspace_command',{cmd:'fixture',yield_time_ms:0},'background-call')).contentItems[0].text);settle();await notificationReady;
    const progress=JSON.parse((await broker.call('continue_workspace_command',{session_id:started.session_id,yield_time_ms:0},'progress-call')).contentItems[0].text);
    releaseNotification();await new Promise(done=>setTimeout(done,40));
    let failure;try{await broker.close();}catch(error){failure={code:error.code,errors:error.errors?.map(item=>item.code)};}
    process.stdout.write(JSON.stringify({unhandled,closed,events,failure,progress}));`;
  const result=JSON.parse((await promisify(execFile)(process.execPath,['--input-type=module','-e',script])).stdout);
  assert.deepEqual(result.unhandled,[]);assert.equal(result.closed,1);
  assert.equal(result.progress.status,'running');assert.equal(typeof result.progress.session_id,'string');
  assert(result.events.includes('completed')&&result.events.includes('failed')&&result.events.includes('close_settled'));
  assert.equal(result.failure.code,'CODEX_COMMAND_OBSERVATION_FAILED');
  assert(result.failure.errors.includes('RUN_AUTHORITY')&&result.failure.errors.includes('FAILED_NOTIFICATION'));
});

for(const held of [false,true])test(`${held?'runner child-event seam fails visibly when an exited child leaves stdio held':'real runner preserves normal tail output and exit code'}`,async t=>{
  const root=await mkdtemp(join(tmpdir(),'runner-drain-'));
  t.after(()=>rm(root,{recursive:true,force:true}));
  const output=join(root,'output'),stdin=join(root,'stdin'),lifecycle=join(root,'lifecycle'),spec=join(root,'spec');
  await writeFile(stdin,'');
  const program=held?`require('node:child_process').spawn(process.execPath,['-e','setTimeout(()=>{},3500)'],{stdio:'inherit'});process.stdout.write('captured tail');process.exit(0)`:
    `process.stdout.write('tail marker');process.exitCode=7`;
  await writeFile(spec,JSON.stringify({schema_version:1,process_id:'exact-runner-session',argv:[process.execPath,'-e',program],cwd:root,
    output_path:output,stdin_path:stdin,lifecycle_path:lifecycle}));
  let result;
  try{
    if(held){
      const child=new EventEmitter();Object.assign(child,{pid:123,stdin:new PassThrough(),stdout:new PassThrough(),stderr:new PassThrough(),kill:()=>true});
      const receipt=await runHostCommand(JSON.parse(await readFile(spec,'utf8')),{drainTimeoutMs:10,spawnImpl:()=>{
        setImmediate(()=>{child.stdout.write('captured tail');child.emit('exit',0,null);});return child;
      }});result={stdout:JSON.stringify(receipt)};
    }else result=await promisify(execFile)(process.execPath,[fileURLToPath(new URL('../lib/execution/codex-command-runner.mjs',import.meta.url)),spec]);
  }
  catch(error){result=error;}
  const receipt=JSON.parse(result.stdout);
  assert.equal(receipt.exit_code,held?1:7);
  assert.equal(receipt.error_code,held?'CODEX_COMMAND_PIPE_HELD':undefined);
  assert.equal(await readFile(output,'utf8'),held?'captured tail':'tail marker');
  const events=(await readFile(lifecycle,'utf8')).trim().split('\n').map(JSON.parse);
  assert(events.some(event=>event.phase==='child_exit'));
  assert(events.some(event=>event.phase==='receipt'));
  assert.equal(events.some(event=>event.phase==='stdio_drain_timeout'),held);
  assert(events.every(event=>event.process_id==='exact-runner-session'&&!('command'in event)&&!('output'in event)));
});

test('real platform runner consumes stop control and preserves stdout stderr tail',async t=>{
  const root=await mkdtemp(join(tmpdir(),'runner-platform-stop-'));t.after(()=>rm(root,{recursive:true,force:true}));
  const output=join(root,'output'),stdin=join(root,'stdin'),lifecycle=join(root,'lifecycle'),spec=join(root,'spec');await writeFile(stdin,'');
  await writeFile(spec,JSON.stringify({schema_version:1,process_id:'owned-platform-session',cwd:root,output_path:output,stdin_path:stdin,lifecycle_path:lifecycle,
    argv:[process.execPath,'-e',`process.stdout.write('stdout-tail');process.stderr.write('stderr-tail');setInterval(()=>{},1000)`]}));
  const running=promisify(execFile)(process.execPath,[fileURLToPath(new URL('../lib/execution/codex-command-runner.mjs',import.meta.url)),spec]);
  let readable=false;
  for(let attempt=0;attempt<100&&!readable;attempt++){
    try{readable=(await readFile(output,'utf8')).includes('stderr-tail');}catch(error){if(error.code!=='ENOENT')throw error;}
    if(!readable)await new Promise(done=>setTimeout(done,20));
  }
  await appendFile(stdin,Buffer.from([3]));
  let result;try{result=await running;}catch(error){result=error;}
  assert(readable,'actual owned command produced both streams before its stop control');
  assert.equal(JSON.parse(result.stdout).exit_code,130);
  const captured=await readFile(output,'utf8');assert(captured.includes('stdout-tail'));assert(captured.includes('stderr-tail'));
  const phases=(await readFile(lifecycle,'utf8')).trim().split('\n').map(JSON.parse);
  assert(phases.some(event=>event.phase==='started'&&event.platform===process.platform));
  assert(phases.some(event=>event.phase==='stop_signal_sent'&&event.signal===(process.platform==='win32'?'SIGTERM':'SIGINT')&&event.accepted));
  assert(phases.some(event=>event.phase==='child_close'));
});

test('real POSIX exited child with descendant-held stdout stderr fails boundedly',{skip:process.platform==='win32'},async t=>{
  const root=await mkdtemp(join(tmpdir(),'runner-posix-held-pipes-'));t.after(()=>rm(root,{recursive:true,force:true}));
  const output=join(root,'output'),stdin=join(root,'stdin'),lifecycle=join(root,'lifecycle'),spec=join(root,'spec');await writeFile(stdin,'');
  const program=`require('node:child_process').spawn(process.execPath,['-e','setTimeout(()=>{},3500)'],{stdio:'inherit'});process.stdout.write('stdout-before-exit');process.stderr.write('stderr-before-exit');process.exit(0)`;
  await writeFile(spec,JSON.stringify({schema_version:1,process_id:'owned-posix-held-session',argv:[process.execPath,'-e',program],cwd:root,
    output_path:output,stdin_path:stdin,lifecycle_path:lifecycle}));
  let result;try{result=await promisify(execFile)(process.execPath,[fileURLToPath(new URL('../lib/execution/codex-command-runner.mjs',import.meta.url)),spec],{timeout:5000});}
  catch(error){result=error;}
  const receipt=JSON.parse(result.stdout);assert.equal(receipt.exit_code,1);assert.equal(receipt.error_code,'CODEX_COMMAND_PIPE_HELD');
  const captured=await readFile(output,'utf8');assert(captured.includes('stdout-before-exit'));assert(captured.includes('stderr-before-exit'));
  const events=(await readFile(lifecycle,'utf8')).trim().split('\n').map(JSON.parse);
  assert(events.some(event=>event.phase==='child_exit'&&event.exit_code===0));assert(events.some(event=>event.phase==='stdio_drain_timeout'));
});

for(const ownership of ['shared','broker-owned'])for(const mode of ['runner failure','RPC rejection','success'])test(`pending ${mode} ${ownership} notification retains exact shutdown ownership and late settlement`,async t=>{
  const root=await mkdtemp(join(tmpdir(),'broker-notification-ownership-'));t.after(()=>rm(root,{recursive:true,force:true}));
  const command=deferred(),notificationStarted=deferred(),notification=deferred(),notificationReturned=deferred();
  const events=[];let closes=0,spec;
  const originalCode=mode==='runner failure'?'CODEX_COMMAND_PIPE_HELD':'RPC_FAILURE';
  const client={initialized(){},async call(method,params){
    if(method==='initialize')return {};
    spec=JSON.parse(await readFile(params.command.at(-1),'utf8'));await writeFile(spec.output_path,'tail');await command.promise;
    if(mode==='RPC rejection')throw Object.assign(new Error('owned RPC failed'),{code:originalCode});
    return {exitCode:0,stdout:JSON.stringify({schema_version:1,exit_code:0,output_bytes:4,
      ...(mode==='runner failure'?{error_code:originalCode}:{})}),stderr:''};
  },async close(){closes++;}};
  const broker=createCodexCommandBroker({binary:join(root,'codex'),home:root,cwd:root,access:'read_only',spoolRoot:join(root,'spool'),
    ...(ownership==='shared'?{getClient:()=>client}:{clientFactory:()=>client}),shutdownGraceMs:5,onOperation:async event=>{
      events.push(event);
      if(event.phase===(mode==='success'?'completed':'failed')){notificationStarted.resolve();await notification.promise;notificationReturned.resolve();}
    }});
  const owner={thread_id:'original-thread',turn_index:1};
  const started=JSON.parse((await broker.call('run_workspace_command',{cmd:'fixture',yield_time_ms:0},'ownership-call',owner)).contentItems[0].text);
  owner.thread_id='later-thread';owner.turn_index=2;
  command.resolve();await notificationStarted.promise;
  assert.deepEqual(broker.pending(),[started.session_id]);
  await assert.rejects(broker.close(),{code:'CODEX_COMMAND_STOP_UNCONFIRMED'});
  assert.equal(closes,1,'the exact original client is closed before releasing its notification');
  assert.deepEqual(broker.pending(),[started.session_id]);
  assert.equal(await readFile(spec.stdin_path,'utf8'),'','finished commands must not receive a late stop control');
  assert(events.some(event=>event.phase==='close_forced'&&event.pending_process_ids.includes(started.session_id)));
  assert(events.some(event=>event.phase==='close_failed'&&event.error_code==='CODEX_COMMAND_STOP_UNCONFIRMED'&&event.pending_process_ids.includes(started.session_id)));
  assert.equal(broker.audit().at(-1).status,mode==='success'?'completed':'failed');
  assert.equal(broker.audit().at(-1).process_id,started.session_id);
  assert.equal(broker.audit().at(-1).thread_id,'original-thread');
  assert.equal(broker.audit().at(-1).turn_index,1);
  if(mode!=='success')assert(events.some(event=>event.phase==='failed'&&event.error_code===originalCode&&event.process_id===started.session_id));
  notification.resolve();await notificationReturned.promise;await new Promise(setImmediate);
  assert.deepEqual(broker.pending(),[]);
  if(mode==='success')await broker.close();else await assert.rejects(broker.close(),{code:originalCode});
  assert.equal(closes,1,'confirmed owned cleanup is not repeated by late-settlement recovery');
});

test('late normal command receipt cannot turn unconfirmed forced execution cleanup into normal completion',async t=>{
  const root=await mkdtemp(join(tmpdir(),'broker-forced-late-receipt-'));t.after(()=>rm(root,{recursive:true,force:true}));
  const command=deferred(),completed=deferred();let closes=0,spec;
  const client={async call(_method,params){spec=JSON.parse(await readFile(params.command.at(-1),'utf8'));await writeFile(spec.output_path,'tail');await command.promise;
    return {exitCode:0,stdout:JSON.stringify({schema_version:1,exit_code:0,output_bytes:4}),stderr:''};},async close(){closes++;}};
  const broker=createCodexCommandBroker({binary:join(root,'codex'),home:root,cwd:root,access:'read_only',spoolRoot:join(root,'spool'),getClient:()=>client,
    shutdownGraceMs:5,onOperation:async event=>{if(event.phase==='completed')completed.resolve();}});
  await broker.call('run_workspace_command',{cmd:'fixture',yield_time_ms:0},'late-receipt-call');
  await assert.rejects(broker.close(),{code:'CODEX_COMMAND_STOP_UNCONFIRMED'});
  assert.equal(closes,1);command.resolve();await completed.promise;await new Promise(setImmediate);
  assert.deepEqual(broker.pending(),[]);
  await assert.rejects(broker.close(),{code:'CODEX_COMMAND_SHUTDOWN_FORCED'});
  assert.equal(closes,1);assert.equal(await readFile(spec.output_path,'utf8'),'tail');
});

test('Host cancellation of unfinished command is recorded and cannot pass completion',async t=>{
  const root=await mkdtemp(join(tmpdir(),'command-close-cancelled-'));t.after(()=>rm(root,{recursive:true,force:true}));
  const completion=deferred();let spec;
  const client={async call(_method,params){spec=JSON.parse(await readFile(params.command.at(-1),'utf8'));await writeFile(spec.output_path,'final tail');return completion.promise;},async close(){}};
  const broker=createCodexCommandBroker({binary:join(root,'codex'),home:root,cwd:root,access:'read_only',spoolRoot:join(root,'spool'),getClient:()=>client,
    onOperation:async event=>{if(event.phase==='stop_control_written')completion.resolve({exitCode:130,stdout:JSON.stringify({schema_version:1,exit_code:130,signal:'SIGINT',output_bytes:10}),stderr:''});}});
  await broker.call('run_workspace_command',{cmd:'fixture',yield_time_ms:0},'cancelled-call');
  await assert.rejects(broker.close(),{code:'CODEX_COMMAND_SHUTDOWN_CANCELLED'});
  assert.equal(broker.audit()[0].status,'cancelled');assert.equal(broker.audit()[0].output,'final tail');
  await broker.close();
});

test('completed-turn shutdown bounds a pending command and closes only its owned client', async t => {
  const root=await mkdtemp(join(tmpdir(),'command-close-held-pipe-'));
  t.after(()=>rm(root,{recursive:true,force:true}));
  const pending=deferred(), events=[]; let closeCalls=0;
  const client={async call(method,params){
    assert.equal(method,'command/exec');
    const spec=JSON.parse(await readFile(params.command.at(-1),'utf8'));
    await writeFile(spec.output_path,'tail already captured');
    return pending.promise;
  },async close(){closeCalls++;pending.reject(Object.assign(new Error('owned server stopped'),{code:'OWNED_STOP'}));}};
  const broker=createCodexCommandBroker({binary:join(root,'codex'),home:root,cwd:root,
    access:'read_only',spoolRoot:join(root,'spool'),getClient:()=>client,shutdownGraceMs:10,
    onOperation:async event=>events.push(event)});
  const started=JSON.parse((await broker.call('run_workspace_command',{cmd:'fixture',yield_time_ms:0},'exact-call')).contentItems[0].text);
  let timer;
  try {
    await assert.rejects(Promise.race([broker.close(),new Promise((_,reject)=>{timer=setTimeout(()=>reject(new Error('unbounded shutdown')),500);})]),
      {code:'CODEX_COMMAND_SHUTDOWN_FORCED'});
  } finally {clearTimeout(timer);pending.resolve({});}
  assert.equal(closeCalls,1);
  assert(events.some(event=>event.phase==='close_begin'&&event.pending_process_ids.includes(started.session_id)));
  assert(events.some(event=>event.phase==='close_forced'&&event.pending_process_ids.includes(started.session_id)));
});

test('pending shutdown refuses a replacement client instead of closing an unrelated session',async t=>{
  const root=await mkdtemp(join(tmpdir(),'command-close-identity-'));t.after(()=>rm(root,{recursive:true,force:true}));
  const pending=deferred();let spec,closes=0;
  const original={async call(_method,params){spec=JSON.parse(await readFile(params.command.at(-1),'utf8'));await writeFile(spec.output_path,'');return pending.promise;},async close(){closes++;}};
  const replacement={async close(){closes++;}};let current=original;
  const broker=createCodexCommandBroker({binary:join(root,'codex'),home:root,cwd:root,access:'read_only',spoolRoot:join(root,'spool'),getClient:()=>current,shutdownGraceMs:10});
  await broker.call('run_workspace_command',{cmd:'fixture',yield_time_ms:0},'identity-call');current=replacement;
  await assert.rejects(broker.close(),{code:'CODEX_COMMAND_CLIENT_IDENTITY'});assert.equal(closes,0);
  pending.resolve({exitCode:0,stdout:JSON.stringify({schema_version:1,exit_code:0,output_bytes:0}),stderr:''});
  await broker.close();
});

test('owned-client close without command settlement remains unconfirmed and preserves exact evidence',async t=>{
  const root=await mkdtemp(join(tmpdir(),'command-close-unconfirmed-'));t.after(()=>rm(root,{recursive:true,force:true}));
  const pending=deferred(),events=[];let closeCalls=0;
  const client={async call(_method,params){const spec=JSON.parse(await readFile(params.command.at(-1),'utf8'));await writeFile(spec.output_path,'');return pending.promise;},async close(){closeCalls++;}};
  const broker=createCodexCommandBroker({binary:join(root,'codex'),home:root,cwd:root,access:'read_only',spoolRoot:join(root,'spool'),getClient:()=>client,
    shutdownGraceMs:10,onOperation:event=>events.push(event)});
  const started=JSON.parse((await broker.call('run_workspace_command',{cmd:'fixture',yield_time_ms:0},'unconfirmed-call')).contentItems[0].text);
  await assert.rejects(broker.close(),{code:'CODEX_COMMAND_STOP_UNCONFIRMED'});assert.equal(closeCalls,1);
  assert(events.some(event=>event.phase==='close_failed'&&event.error_code==='CODEX_COMMAND_STOP_UNCONFIRMED'&&event.pending_process_ids[0]===started.session_id));
  assert.deepEqual([...await readFile(join(root,'spool',started.session_id,'stdin.bin'))],[3]);
  pending.resolve({exitCode:0,stdout:JSON.stringify({schema_version:1,exit_code:0,output_bytes:0}),stderr:''});
  await assert.rejects(broker.close(),{code:'CODEX_COMMAND_SHUTDOWN_FORCED'});
  assert.equal(closeCalls,1);
});

test('command settlement observation errors cannot pass silently through allSettled',async t=>{
  const root=await mkdtemp(join(tmpdir(),'command-close-observation-'));t.after(()=>rm(root,{recursive:true,force:true}));
  const client={async call(_method,params){const spec=JSON.parse(await readFile(params.command.at(-1),'utf8'));await writeFile(spec.output_path,'');
    return {exitCode:0,stdout:JSON.stringify({schema_version:1,exit_code:0,output_bytes:0}),stderr:''};},async close(){}};
  const broker=createCodexCommandBroker({binary:join(root,'codex'),home:root,cwd:root,access:'read_only',spoolRoot:join(root,'spool'),getClient:()=>client,
    onOperation:event=>{if(['completed','failed'].includes(event.phase))throw Object.assign(new Error('durable observation unavailable'),{code:'OBSERVATION_DISK'});}});
  await assert.rejects(broker.call('run_workspace_command',{cmd:'fixture'},'observation-call'),{code:'OBSERVATION_DISK'});
  await assert.rejects(broker.close(),error=>error.code==='CODEX_COMMAND_OBSERVATION_FAILED'&&error.errors[0].code==='OBSERVATION_DISK');
  await broker.close();
});

async function fixture(t, { output = 'complete output', exitCode = 0, access = 'read_only', allowedPaths = [],recoverToolErrors=false,outputBudgetBytes,delayMs=0 } = {}) {
  const root = await mkdtemp(join(tmpdir(), 'command-broker-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  const spoolRoot = join(root, 'spool');
  const calls = [];
  const client = {
    initialized() {},
    async call(method, params) {
      calls.push({ method, params });
      if (method === 'initialize') return {};
      if (method === 'command/exec') {
        const spec = JSON.parse(await readFile(params.command.at(-1), 'utf8'));
        calls.at(-1).command_spec=spec;
        const sourcePath=join(dirname(params.command.at(-1)),'command-source.ps1');
        calls.at(-1).command_source={path:sourcePath,bytes:await readFile(sourcePath)};
        await writeFile(spec.output_path, output, { flag: 'wx' });
        if(delayMs)await new Promise(done=>setTimeout(done,delayMs));
        return { exitCode, stdout: JSON.stringify({ schema_version: 1, exit_code: exitCode,
          signal: null, output_bytes: Buffer.byteLength(output) }), stderr: '' };
      }
      if (method === 'command/exec/write') return {};
      if (method === 'command/exec/terminate') return {};
      assert.fail(`Unexpected method ${method}`);
    },
    async close() {},
  };
  const broker = createCodexCommandBroker({ binary: join(root, 'codex'), home: root, cwd: root, spoolRoot,
    access, allowedPaths,recoverToolErrors, env: {}, clientFactory: () => client, platform: 'win32', nodeBinary: process.execPath,
    ...(outputBudgetBytes?{getOutputBudget:()=>({max_result_bytes:outputBudgetBytes})}:{}) });
  return { broker, calls, spoolRoot, root };
}

test('standalone broker cannot invent an output budget',async t=>{
  const root=await mkdtemp(join(tmpdir(),'unknown-command-budget-'));t.after(()=>rm(root,{recursive:true,force:true}));
  assert.throws(()=>createCodexCommandBrokerImpl({binary:join(root,'binary'),home:root,cwd:root,spoolRoot:join(root,'spool'),access:'read_only'}),{code:'CODEX_TOOL_OUTPUT_BUDGET'});
});

test('foreground command cannot select a short timer; default waits for a 1.1s completion',async t=>{
  const {broker,calls}=await fixture(t,{delayMs:1100});
  await assert.rejects(broker.call('run_workspace_command',{cmd:'fixture',yield_time_ms:1000},'short'),{code:'CODEX_COMMAND_ARGUMENTS'});
  assert.equal(calls.length,0);
  const result=JSON.parse((await broker.call('run_workspace_command',{cmd:'fixture'},'foreground')).contentItems[0].text);
  assert.equal(result.status,'completed');assert.equal(result.has_more,false);assert.equal(result.session_id,undefined);
  await broker.close();
});

for(const text of ['ASCII-'.repeat(60000)+'END_MARKER','中文 × → 😀\\\n\t\"'.repeat(10000)+'END_MARKER'])
test('inherited small output budget preserves every byte through bounded serialized chunks '+(text.startsWith('ASCII')?'ASCII':'Unicode/escaping'),async t=>{
  const budget=4096,{broker,spoolRoot}=await fixture(t,{output:text,outputBudgetBytes:budget});
  let response=await broker.call('run_workspace_command',{cmd:'fixture'},'first'),value=JSON.parse(response.contentItems[0].text),joined='',round=0;
  const id=value.session_id;assert(id);assert.equal(value.has_more,true);
  while(true){
    assert(Buffer.byteLength(JSON.stringify(response))<=budget);assert(!/^[\uDC00-\uDFFF]/.test(value.output));assert(!/[\uD800-\uDBFF]$/.test(value.output));
    joined+=value.output;if(!value.has_more)break;
    assert(round++<1000);assert.equal(await readFile(join(spoolRoot,id,'output.bin'),'utf8'),text);
    response=await broker.call('continue_workspace_command',{session_id:id},'read-'+round);value=JSON.parse(response.contentItems[0].text);
  }
  assert(Buffer.from(joined).equals(Buffer.from(text)));assert(joined.endsWith('END_MARKER'));
  await assert.rejects(readFile(join(spoolRoot,id,'output.bin')),{code:'ENOENT'});await broker.close();
});

test('Host command broker ignores a model-selected low output budget and returns the complete result', async t => {
  const expected = `${'source line\n'.repeat(9000)}END_MARKER`;
  const { broker, calls, spoolRoot } = await fixture(t, { output: expected });
  const toolNames = broker.tools().map(tool => tool.name);
  assert.deepEqual(toolNames, ['run_workspace_program','run_workspace_command', 'continue_workspace_command']);
  const response = await broker.call('run_workspace_command', { cmd: 'fixture', max_output_tokens: 1000, yield_time_ms: 10000 }, 'call-1');
  const result = JSON.parse(response.contentItems[0].text);
  assert.equal(result.output, expected);
  assert.equal(result.status, 'completed');
  assert.equal(result.has_more, false);
  const command = calls.find(item => item.method === 'command/exec').params;
  assert.equal(command.outputBytesCap, undefined);
  assert.deepEqual(command.sandboxPolicy, { type: 'workspaceWrite', writableRoots: [spoolRoot],
    networkAccess: false, excludeTmpdirEnvVar: false, excludeSlashTmp: false });
  await broker.close();
});

test('Windows PowerShell commands use UTF-8 for console and native stdin without model configuration',async t=>{
  const {broker,calls}=await fixture(t);
  const command="'中文 × →' | & '"+process.execPath.replaceAll("'","''")+"' -e \"process.stdin.on('data',b=>process.stdout.write(b))\"";
  await broker.call('run_workspace_command',{cmd:command},'unicode-call');
  const spec=calls.find(c=>c.method==='command/exec').command_spec;
  assert.equal(spec.argv[0],'powershell.exe');
  assert(spec.argv.at(-1).startsWith('$OutputEncoding = [Console]::InputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false);'));
  assert.equal(calls.find(c=>c.method==='command/exec').command_source.bytes.toString('utf8'),command);
  if(process.platform==='win32'){
    const source=calls.find(c=>c.method==='command/exec').command_source;
    await mkdir(dirname(source.path),{recursive:true});await writeFile(source.path,source.bytes);
    const result=await promisify(execFile)(spec.argv[0],spec.argv.slice(1),{encoding:'utf8',windowsHide:true});
    assert.equal(result.stdout.trim(),'中文 × →');
  }
  await broker.close();
});

for(const [label,command,expected,exitCode] of [
  ['using and param',"using namespace System.Text\nparam([string]$value='中文 × →')\n[Encoding]::UTF8.GetString([Encoding]::UTF8.GetBytes($value))",'中文 × →',0],
  ['explicit exit',"param([int]$value=7)\nWrite-Output 'before exit'\nexit $value",'before exit',7],
  ['native failure',"& '"+process.execPath.replaceAll("'","''")+"' -e \"process.exit(4)\"",'',1],
])test(`UTF-8 shell preserves original PowerShell ${label}`,{skip:process.platform!=='win32'},async t=>{
  const {broker,calls}=await fixture(t);
  await broker.call('run_workspace_command',{cmd:command,login:false},'prologue-call');
  const spec=calls.find(c=>c.method==='command/exec').command_spec;
  const source=calls.find(c=>c.method==='command/exec').command_source;
  await mkdir(dirname(source.path),{recursive:true});await writeFile(source.path,source.bytes);
  let result;try{result=await promisify(execFile)(spec.argv[0],spec.argv.slice(1),{encoding:'utf8',windowsHide:true});}
  catch(error){result=error;}
  assert.equal(result.code??0,exitCode);assert.equal(result.stdout.trim(),expected);assert.equal(result.stderr,'');
  await broker.close();
});

test('long Unicode manuscripts use a short Windows bootstrap without changing source bytes',{skip:process.platform!=='win32'},async t=>{
  const {broker,calls}=await fixture(t),value='中'.repeat(10000),command="Write-Output '"+value+"'";
  await broker.call('run_workspace_command',{cmd:command,login:false},'long-unicode-call');
  const {command_spec:spec,command_source:source}=calls.find(c=>c.method==='command/exec');
  assert(spec.argv.at(-1).length<2000);assert.equal(source.bytes.toString('utf8'),command);
  await mkdir(dirname(source.path),{recursive:true});await writeFile(source.path,source.bytes);
  const result=await promisify(execFile)(spec.argv[0],spec.argv.slice(1),{encoding:'utf8',windowsHide:true});
  assert.equal(result.stdout.trim(),value);assert.equal(result.stderr,'');await broker.close();
});

test('large completed output is chunked without loss and remains readable through write_stdin', async t => {
  const expected = `${'0123456789abcdef'.repeat(20000)}END_MARKER`;
  const { broker } = await fixture(t, { output: expected });
  const first = JSON.parse((await broker.call('run_workspace_command', { cmd: 'fixture', max_output_tokens: 1 }, 'call-1')).contentItems[0].text);
  assert.equal(first.status, 'completed');
  assert.equal(first.has_more, true);
  assert.equal(typeof first.session_id, 'string');
  let reconstructed = first.output;
  let current = first;
  while (current.has_more) {
    current = JSON.parse((await broker.call('continue_workspace_command', { session_id: first.session_id, max_output_tokens: 1 }, `drain-${reconstructed.length}`)).contentItems[0].text);
    reconstructed += current.output;
  }
  assert.equal(reconstructed, expected);
  assert.match(reconstructed, /END_MARKER$/);
  await broker.close();
});

test('Windows command sandbox receives its workspace root while Host retains exact item paths',async t=>{
  const {broker,calls,spoolRoot,root}=await fixture(t,{access:'bounded_write',allowedPaths:['cards/a.py']});
  await broker.call('run_workspace_command',{cmd:'fixture'},'call-relative');
  const command=calls.find(item=>item.method==='command/exec').params;
  assert.deepEqual(command.sandboxPolicy.writableRoots,[root]);
  await broker.close();

  assert.throws(()=>createCodexCommandBroker({binary:join(root,'codex'),home:root,cwd:root,
    spoolRoot:join(root,'another-spool'),access:'bounded_write',allowedPaths:[],platform:'win32',nodeBinary:process.execPath}),
  {code:'CODEX_COMMAND_SCOPE'});
});

test('command working directory cannot escape the Host workspace',async t=>{
  const {broker,root}=await fixture(t);
  await assert.rejects(broker.call('run_workspace_command',{cmd:'fixture',workdir:join(root,'..','outside')},'call-escape'),
    {code:'CODEX_COMMAND_SCOPE'});
  await broker.close();
});

test('model can recover from an exhausted command session without losing its Agent turn',async t=>{
  const {broker}=await fixture(t,{recoverToolErrors:true});
  const rejected=await broker.call('continue_workspace_command',{session_id:'already-exhausted'},'call-expired');
  assert.equal(rejected.success,false);
  assert.deepEqual(JSON.parse(rejected.contentItems[0].text),{error:{code:'CODEX_COMMAND_SESSION',message:'Unknown or exhausted command session'}});
  const next=JSON.parse((await broker.call('run_workspace_command',{cmd:'fixture'},'call-after-rejection')).contentItems[0].text);
  assert.equal(next.status,'completed');
  await broker.close();
});

test('Ctrl-C is delivered through the Host runner control file without an unsupported terminate RPC',async t=>{
  const root=await mkdtemp(join(tmpdir(),'command-broker-runner-stop-'));
  t.after(()=>rm(root,{recursive:true,force:true}));
  const completion=deferred(),execStarted=deferred(),spoolRoot=join(root,'spool'),events=[];let spec;
  const client={initialized(){},async call(method,params){
    if(method==='initialize')return {};
    if(method==='command/exec'){spec=JSON.parse(await readFile(params.command.at(-1),'utf8'));execStarted.resolve();return completion.promise;}
    assert.fail(`Unexpected method ${method}`);
  },async close(){}};
  const broker=createCodexCommandBroker({binary:join(root,'codex'),home:root,cwd:root,spoolRoot,
    access:'read_only',env:{},clientFactory:()=>client,platform:'win32',nodeBinary:process.execPath,onOperation:event=>events.push(event)});
  const started=JSON.parse((await broker.call('run_workspace_command',{cmd:'fixture',yield_time_ms:0},'call-1')).contentItems[0].text);
  assert.equal(started.status,'running');
  await execStarted.promise;
  const stopping=JSON.parse((await broker.call('continue_workspace_command',{session_id:started.session_id,chars:'\u0003',yield_time_ms:0},'call-2')).contentItems[0].text);
  assert.equal(stopping.status,'running');assert.deepEqual([...await readFile(spec.stdin_path)],[3]);
  const output='runner stopped its exact child tree';await writeFile(spec.output_path,output,{flag:'wx'});
  completion.resolve({exitCode:130,stdout:JSON.stringify({schema_version:1,exit_code:130,signal:'SIGINT',output_bytes:Buffer.byteLength(output)}),stderr:''});
  const stopped=JSON.parse((await broker.call('continue_workspace_command',{session_id:started.session_id,yield_time_ms:1000},'call-3')).contentItems[0].text);
  assert.equal(stopped.status,'completed');assert.equal(stopped.exit_code,130);assert.equal(stopped.output,output);
  assert(events.some(event=>event.phase==='started'&&event.call_id==='call-1'&&event.process_id===started.session_id&&/^[a-f0-9]{64}$/.test(event.args_sha256)));
  assert(events.some(event=>event.phase==='continued'&&event.call_id==='call-2'&&event.process_id===started.session_id&&event.tool==='continue_workspace_command'));
  assert.equal(broker.audit()[0].call_id,'call-1');assert.equal(broker.audit()[0].process_id,started.session_id);
  assert(events.every(event=>!('command'in event)&&!('arguments'in event)&&!('output'in event)));
  await broker.close();
});

test('repeated Ctrl-C does not enqueue duplicate stop controls',async t=>{
  const root=await mkdtemp(join(tmpdir(),'command-broker-runner-stop-once-'));
  t.after(()=>rm(root,{recursive:true,force:true}));
  const completion=deferred(),execStarted=deferred(),spoolRoot=join(root,'spool');let spec;
  const client={initialized(){},async call(method,params){
    if(method==='initialize')return {};
    if(method==='command/exec'){spec=JSON.parse(await readFile(params.command.at(-1),'utf8'));execStarted.resolve();return completion.promise;}
    assert.fail(`Unexpected method ${method}`);
  },async close(){}};
  const broker=createCodexCommandBroker({binary:join(root,'codex'),home:root,cwd:root,spoolRoot,
    access:'read_only',env:{},clientFactory:()=>client,platform:'win32',nodeBinary:process.execPath});
  const started=JSON.parse((await broker.call('run_workspace_command',{cmd:'fixture',yield_time_ms:0},'call-1')).contentItems[0].text);
  await execStarted.promise;
  await broker.call('continue_workspace_command',{session_id:started.session_id,chars:'\u0003',yield_time_ms:0},'call-2');
  await broker.call('continue_workspace_command',{session_id:started.session_id,chars:'\u0003',yield_time_ms:0},'call-3');
  assert.deepEqual([...await readFile(spec.stdin_path)],[3]);
  await writeFile(spec.output_path,'',{flag:'wx'});
  completion.resolve({exitCode:130,stdout:JSON.stringify({schema_version:1,exit_code:130,signal:'SIGINT',output_bytes:0}),stderr:''});
  await broker.close();
});
