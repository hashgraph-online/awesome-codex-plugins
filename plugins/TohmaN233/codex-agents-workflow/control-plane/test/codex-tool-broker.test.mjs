import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, readFile, writeFile, rm, link, symlink } from 'node:fs/promises';
import { writeFileSync } from 'node:fs';
import { EventEmitter } from 'node:events';
import { PassThrough } from 'node:stream';
import { execFile } from 'node:child_process';
import { tmpdir } from './physical-tempdir.mjs';
import { tmpdir as osTmpdir } from 'node:os';
import { join, relative } from 'node:path';
import { boundProgramArgv, createCodexToolBroker, executeBoundProgram, executeNativeProgram, qualifiedExecutionBinding } from '../lib/execution/codex-tool-broker.mjs';
import { digest } from '../lib/workflow-revisions.mjs';

async function fixture(t) {
  const root = await mkdtemp(join(tmpdir(), 'codex-broker-'));
  t.after(() => rm(root, { recursive: true, maxRetries: 3, retryDelay: 100 }));
  await mkdir(join(root, 'src')); await writeFile(join(root, 'src', 'main.txt'), 'before');
  const operations = []; let active = true;
  const options = { workspace: root, access: 'bounded_write', allowedPaths: ['src'], authorize: async () => { assert(active, 'lease revoked'); }, onOperation: async event => operations.push(event) };
  return { root, options, operations, revoke: () => { active = false; } };
}
const output = result => JSON.parse(result.contentItems[0].text);
const delay=milliseconds=>new Promise(resolveDelay=>setTimeout(resolveDelay,milliseconds));
const executionBinding=()=>qualifiedExecutionBinding({kind:'wsl',launcher:'C:\\Windows\\System32\\wsl.exe',distribution:process.env.WORKFLOW_TEST_WSL_DISTRIBUTION??'Ubuntu',sandbox:'/usr/bin/bwrap',programs:{python:'/usr/bin/python3'},runtime_roots:['/lib','/lib64','/usr'],command_timeout_ms:300000});
async function waitForFile(path){for(let attempt=0;attempt<1000;attempt++){try{return await readFile(path,'utf8');}catch(error){if(error.code!=='ENOENT')throw error;}await delay(10);}throw new Error(`Timed out waiting for ${path}`);}

test('a Run execution binding grants program tools only to bounded-write nodes',async t=>{
  if(process.platform!=='win32'){
    assert.throws(executionBinding,{code:'CODEX_EXECUTION_BINDING'},'a Windows WSL launcher is not a host executable on this platform');
    return;
  }
  const f=await fixture(t),taskRoot=await mkdtemp(join(tmpdir(),'codex-task-root-'));
  t.after(()=>rm(taskRoot,{recursive:true,maxRetries:3,retryDelay:100}));
  const readOnly=await createCodexToolBroker({...f.options,access:'read_only',allowedPaths:[],executionBinding:executionBinding()});
  assert.equal(readOnly.tools().some(tool=>tool.name==='run_task_program'),false);
  const writable=await createCodexToolBroker({...f.options,executionBinding:executionBinding(),inputRoots:[{name:'task_root',path:taskRoot}]});
  assert.equal(writable.tools().some(tool=>tool.name==='run_task_program'),true);
  await assert.rejects(createCodexToolBroker({...f.options,executionBinding:executionBinding()}),{code:'CODEX_EXECUTION_BINDING'});
});

test('discovered Host programs reach read and write nodes without a separate WSL binding', async t => {
  const f = await fixture(t);
  const runtimeEnvironment = { status: 'ready', tools: [{ name: 'node', status: 'found', path: process.execPath }] };
  const readOnly = await createCodexToolBroker({ ...f.options, access: 'read_only', allowedPaths: [], runtimeEnvironment });
  assert(readOnly.tools().some(tool => tool.name === 'run_task_program'));
  assert(!readOnly.tools().some(tool => tool.name === 'write_workspace'));
  const result = output(await readOnly.call('run_task_program', { program: 'node', args: ['-p', '1+1'], cwd: 'workspace' }, 'native-read'));
  assert.equal(result.exit_code, 0);
  assert.equal(result.stdout.trim(), '2');
  const writable = await createCodexToolBroker({ ...f.options, runtimeEnvironment });
  assert(writable.tools().some(tool => tool.name === 'write_workspace'));
  assert(writable.tools().some(tool => tool.name === 'mkdir_workspace'));
  await writable.call('mkdir_workspace', { path: 'src/scenarios/new' }, 'mkdir');
  assert((await writable.call('list_workspace', { path: 'src/scenarios' }, 'list')).success);
  await writable.call('write_workspace', { path: 'src/scenarios/new/result.json', text: '{}', expected_sha256: null }, 'write');
  assert.equal(await readFile(join(f.root, 'src/scenarios/new/result.json'), 'utf8'), '{}');
});

test('revoking a discovered native task program stops the owned process before a delayed write', async t => {
  const f = await fixture(t);
  const runtimeEnvironment = { status: 'ready', tools: [{ name: 'node', status: 'found', path: process.execPath }] };
  const broker = await createCodexToolBroker({ ...f.options, runtimeEnvironment });
  const program = "require('node:fs').writeFileSync('src/native.ready','ready'); setTimeout(()=>require('node:fs').writeFileSync('src/native-late.txt','late'),3000)";
  const pending = broker.call('run_task_program', { program: 'node', args: ['-e', program], cwd: 'workspace' }, 'native-revoke');
  assert.equal(await waitForFile(join(f.root, 'src', 'native.ready')), 'ready');
  broker.revoke();
  await assert.rejects(pending, { code: 'CODEX_EXECUTION_CANCELLED' });
  assert.equal((await broker.quiesce()).quiescent, true);
  await assert.rejects(readFile(join(f.root, 'src', 'native-late.txt'), 'utf8'), { code: 'ENOENT' });
});

async function nativeDescendantFixture(t, { mode, stdio }) {
  const f = await fixture(t), controller = new AbortController();
  const ready = join(f.root, 'src', 'descendant.ready'), release = join(f.root, 'src', 'release');
  const late = join(f.root, 'src', 'descendant-late.txt');
  const descendant = `const fs=require('node:fs'); fs.writeFileSync(${JSON.stringify(ready)},String(process.pid));
    setInterval(()=>{if(fs.existsSync(${JSON.stringify(release)}))fs.writeFileSync(${JSON.stringify(late)},'late');},10);`;
  const parent = `const fs=require('node:fs');require('node:child_process').spawn(process.execPath,['-e',${JSON.stringify(descendant)}],
    {stdio:${JSON.stringify(stdio)}});const timer=setInterval(()=>{if(fs.existsSync(${JSON.stringify(ready)})&&${mode === 'parent-exit'})process.exit(0);},10);`;
  let handle, pid;
  t.after(() => { if (pid) try { process.kill(pid, 'SIGKILL'); } catch (error) { if (error.code !== 'ESRCH') throw error; } });
  const pending = executeNativeProgram({ kind: 'native', programs: { node: process.execPath }, command_timeout_ms: mode === 'timeout' ? 1000 : 10000 },
    { program: 'node', args: ['-e', parent], cwd: 'workspace' }, { workspace: f.root },
    { signal: controller.signal, onHandle: value => { handle = value; } });
  // Attach the rejection handler before awaiting the readiness marker.
  const outcome = pending.then(value => ({ value }), error => ({ error }));
  pid = Number(await waitForFile(ready));
  if (mode === 'cancel') controller.abort(Object.assign(new Error('fixture cancellation'), { code: 'PROBE_CANCEL' }));
  const result = await outcome;
  if (mode === 'parent-exit') { assert.equal(result.error, undefined); assert.equal(result.value.exit_code, 0); }
  else assert.equal(result.error?.code, mode === 'cancel' ? 'PROBE_CANCEL' : 'CODEX_EXECUTION_TIMEOUT');
  assert.equal(handle.isQuiescent(), true);
  const state = await new Promise((resolveState, rejectState) => execFile('/bin/ps', ['-eo', 'pid=,stat='], (error, stdout) => {
    if (error) rejectState(error); else resolveState(stdout.split('\n').map(line => line.trim().split(/\s+/)).find(parts => Number(parts[0]) === pid)?.[1]);
  }));
  assert(!state || state.startsWith('Z'), `descendant ${pid} remains live: ${state}`);
  await writeFile(release, 'release'); await delay(100);
  await assert.rejects(readFile(late), { code: 'ENOENT' });
}

for (const mode of ['cancel', 'timeout', 'parent-exit']) for (const stdio of ['ignore', 'inherit']) {
  test(`POSIX native ${mode} confirms descendant termination with ${stdio} stdio`, { skip: process.platform === 'win32' },
    t => nativeDescendantFixture(t, { mode, stdio }));
}

test('POSIX native failed group stop retains ownership and an exact retry confirms cleanup', { skip: process.platform === 'win32' }, async t => {
  const f = await fixture(t), controller = new AbortController(), ready = join(f.root, 'src', 'stop.ready');
  let handle, failStop = true;
  const pending = executeNativeProgram({ kind: 'native', programs: { node: process.execPath }, command_timeout_ms: 10000 },
    { program: 'node', args: ['-e', `require('node:fs').writeFileSync(${JSON.stringify(ready)},'ready');setInterval(()=>{},1000);`], cwd: 'workspace' },
    { workspace: f.root }, { signal: controller.signal, onHandle: value => { handle = value; },
      processSignaler: (pid, signalName) => { if (failStop) throw Object.assign(new Error('synthetic group signal denied'), { code: 'EPERM' }); return process.kill(pid, signalName); } });
  const rejected = assert.rejects(pending, error => error.code === 'CODEX_EXECUTION_STOP_UNCONFIRMED'
    && error.details.cause_code === 'EPERM' && error.errors.some(cause => cause.code === 'PROBE_CANCEL'));
  t.after(async () => { failStop = false; await handle?.stop(); });
  await waitForFile(ready); controller.abort(Object.assign(new Error('fixture cancellation'), { code: 'PROBE_CANCEL' }));
  await rejected; assert.equal(handle.isQuiescent(), false);
  failStop = false; await handle.stop(); assert.equal(handle.isQuiescent(), true);
});

test('POSIX native parent closure cannot hide a failed group inspection', { skip: process.platform === 'win32' }, async t => {
  const f = await fixture(t); let handle, failInspection = true;
  const pending = executeNativeProgram({ kind: 'native', programs: { node: process.execPath }, command_timeout_ms: 10000 },
    { program: 'node', args: ['-e', ''], cwd: 'workspace' }, { workspace: f.root },
    { onHandle: value => { handle = value; }, inspectProcessGroup: async () => {
      if (failInspection) throw Object.assign(new Error('synthetic ps failure'), { code: 'EACCES' }); return [];
    } });
  await assert.rejects(pending, error => error.code === 'CODEX_EXECUTION_STOP_UNCONFIRMED' && error.details.cause_code === 'EACCES');
  assert.equal(handle.isQuiescent(), false);
  failInspection = false; await handle.stop(); assert.equal(handle.isQuiescent(), true);
});

test('native program calls refresh a stale Host binding before effects and surface missing dependencies',async t=>{
  const f=await fixture(t);
  const stale={status:'ready',tools:[{name:'node',status:'found',path:join(f.root,'removed-node.exe')}]};
  let available=true,checks=0;
  const broker=await createCodexToolBroker({...f.options,runtimeEnvironment:stale,prepareRuntimeEnvironment:async()=>{
    checks++;
    if(!available)throw Object.assign(new Error('Re-register node before proceeding'),{code:'ENVIRONMENT_SETUP_REQUIRED'});
    return {environment:{status:'ready',tools:[{name:'node',status:'found',path:process.execPath}]}};
  }});
  const first=output(await broker.call('run_task_program',{program:'node',args:['-p','7*6'],cwd:'workspace'},'refreshed'));
  assert.equal(first.stdout.trim(),'42');assert.equal(checks,1);
  available=false;
  await assert.rejects(broker.call('run_task_program',{program:'node',args:['-e',"require('node:fs').writeFileSync('src/forbidden.txt','effect')"],cwd:'workspace'},'missing'),{code:'ENVIRONMENT_SETUP_REQUIRED'});
  assert.equal(checks,2);
  await assert.rejects(readFile(join(f.root,'src/forbidden.txt')),{code:'ENOENT'});
  assert.equal(f.operations.filter(event=>event.call_id==='missing'&&event.phase==='started').length,0);
});

test('bound WSL programs see only explicit runtime roots and task mounts, never the distribution root',()=>{
  const binding={kind:'wsl',launcher:'C:\\Windows\\System32\\wsl.exe',distribution:'Ubuntu',sandbox:'/usr/bin/bwrap',programs:{python:'/usr/bin/python3'},runtime_roots:['/lib','/lib64','/usr'],command_timeout_ms:300000};
  const argv=boundProgramArgv(binding,{program:'python',args:['-V'],cwd:'workspace'},{workspace:'C:\\fixture\\workspace',task_root:'C:\\fixture\\task'},{
    writable:['C:\\fixture\\workspace\\src'],masks:[{path:'/mnt/c/fixture/workspace/.git',type:'directory'},{path:'/mnt/c/fixture/task/SKILL.md',type:'file'}]});
  assert.equal(argv.some((value,index)=>value==='--ro-bind'&&argv[index+1]==='/'&&argv[index+2]==='/'),false);
  assert.equal(argv[2],'--exec');
  assert(argv.includes('--unshare-pid'));assert(argv.includes('--as-pid-1'));
  assert(argv.some((value,index)=>value==='--tmpfs'&&argv[index+1]==='/'));
  assert(argv.some((value,index)=>value==='--ro-bind-try'&&argv[index+1]==='/usr'&&argv[index+2]==='/usr'));
  assert(argv.some((value,index)=>value==='--tmpfs'&&argv[index+1].endsWith('/.git')));
  assert(argv.some((value,index)=>value==='--ro-bind'&&argv[index+1]==='/dev/null'&&argv[index+2].endsWith('/SKILL.md')));
  assert(argv.some((value,index)=>value==='--ro-bind'&&argv[index+1]==='/mnt/c/fixture/workspace'&&argv[index+2]==='/mnt/c/fixture/workspace'));
  assert(argv.some((value,index)=>value==='--bind'&&argv[index+1]==='/mnt/c/fixture/workspace/src'&&argv[index+2]==='/mnt/c/fixture/workspace/src'));
  assert.equal(argv.some((value,index)=>value==='--bind'&&argv[index+1]==='/mnt/c/fixture/workspace'&&argv[index+2]==='/mnt/c/fixture/workspace'),false);
  const resolved=boundProgramArgv(binding,{program:'python',args:['@TASK_ROOT@/environment/data/input_video.mp4','@WORKSPACE@/compressed_video.mp4'],cwd:'workspace'},
    {workspace:'C:\\fixture\\workspace',task_root:'C:\\fixture\\task'},{writable:['C:\\fixture\\workspace']});
  assert.deepEqual(resolved.slice(-2),['/mnt/c/fixture/task/environment/data/input_video.mp4','/mnt/c/fixture/workspace/compressed_video.mp4']);
  const readOnly=boundProgramArgv(binding,{program:'python',args:['-V'],cwd:'workspace'},
    {workspace:'C:\\fixture\\workspace',task_root:'C:\\fixture\\task'},{writable:[]});
  assert(readOnly.some((value,index)=>value==='--ro-bind'&&readOnly[index+1]==='/mnt/c/fixture/workspace'&&readOnly[index+2]==='/mnt/c/fixture/workspace'));
  assert.equal(readOnly.some((value,index)=>value==='--bind'&&readOnly[index+1]==='/mnt/c/fixture/workspace'),false);
  if(process.platform==='win32'){
    assert.throws(()=>qualifiedExecutionBinding({...binding,programs:{python:'/home/user/python'}}),{code:'CODEX_EXECUTION_BINDING'});
    assert.throws(()=>qualifiedExecutionBinding({...binding,runtime_roots:['/mnt/c']}),{code:'CODEX_EXECUTION_BINDING'});
  }
});

test('bound programs reject hard links anywhere beneath a writable directory before process launch',{skip:process.platform!=='win32'},async t=>{
  const f=await fixture(t),taskRoot=await mkdtemp(join(tmpdir(),'codex-task-root-'));
  t.after(()=>rm(taskRoot,{recursive:true,maxRetries:3,retryDelay:100}));
  await link(join(f.root,'src','main.txt'),join(f.root,'outside.txt'));
  const executionBinding=qualifiedExecutionBinding({kind:'wsl',launcher:'C:\\Windows\\System32\\wsl.exe',distribution:'Ubuntu',sandbox:'/usr/bin/bwrap',programs:{python:'/usr/bin/python3'},runtime_roots:['/lib','/lib64','/usr'],command_timeout_ms:300000});
  const broker=await createCodexToolBroker({...f.options,executionBinding,inputRoots:[{name:'task_root',path:taskRoot}]});
  await assert.rejects(broker.call('run_task_program',{program:'python',args:['-c',"from pathlib import Path; Path('src/main.txt').write_text('changed')"],cwd:'workspace'},'hard-link-run'),{code:'CODEX_EXECUTION_SCOPE'});
  assert.equal(await readFile(join(f.root,'src','main.txt'),'utf8'),'before');
  assert.equal(await readFile(join(f.root,'outside.txt'),'utf8'),'before');
  assert.deepEqual(f.operations.map(item=>item.phase),['started']);
});

test('revocation during bound-program preflight prevents process launch',{skip:process.platform!=='win32'},async t=>{
  const f=await fixture(t),taskRoot=await mkdtemp(join(tmpdir(),'codex-task-root-'));t.after(()=>rm(taskRoot,{recursive:true,maxRetries:3,retryDelay:100}));
  let releaseStarted,notifyStarted;const started=new Promise(resolveStarted=>{notifyStarted=resolveStarted;}),release=new Promise(resolveRelease=>{releaseStarted=resolveRelease;});
  const broker=await createCodexToolBroker({...f.options,executionBinding:executionBinding(),inputRoots:[{name:'task_root',path:taskRoot}],onOperation:async event=>{f.operations.push(event);if(event.phase==='started'){notifyStarted();await release;}}});
  const late=join(f.root,'src','late.txt'),pending=broker.call('run_task_program',{program:'python',args:['-c',"from pathlib import Path; Path('src/late.txt').write_text('after revoke')"],cwd:'workspace'},'revoke-before-launch');
  await started;broker.revoke();releaseStarted();await assert.rejects(pending,{code:'CODEX_EXECUTION_CANCELLED'});
  await assert.rejects(readFile(late,'utf8'),{code:'ENOENT'});const drained=await broker.quiesce();assert.equal(drained.quiescent,true);
});

test('revocation stops the exact active Linux execution before it can write again',{skip:process.platform!=='win32'},async t=>{
  const f=await fixture(t),taskRoot=await mkdtemp(join(tmpdir(),'codex-task-root-'));t.after(()=>rm(taskRoot,{recursive:true,maxRetries:3,retryDelay:100}));
  const broker=await createCodexToolBroker({...f.options,executionBinding:executionBinding(),inputRoots:[{name:'task_root',path:taskRoot}]});
  const ready=join(f.root,'src','active.ready'),late=join(f.root,'src','active-late.txt');
  const program="import time\nfrom pathlib import Path\nroot=Path('src')\n(root/'active.ready').write_text('ready')\ntime.sleep(30)\n(root/'active-late.txt').write_text('late')";
  const pending=broker.call('run_task_program',{program:'python',args:['-c',program],cwd:'workspace'},'revoke-active');
  await Promise.race([waitForFile(ready),pending.then(value=>{throw new Error(`Bound program finished before ready marker: ${JSON.stringify(output(value))}`);})]);
  broker.revoke();await assert.rejects(pending,{code:'CODEX_EXECUTION_CANCELLED'});const drained=await broker.quiesce();assert.equal(drained.quiescent,true);
  await delay(100);await assert.rejects(readFile(late,'utf8'),{code:'ENOENT'});
});

test('PID-isolated bound programs cannot leave writable descendants after tool completion',{skip:process.platform!=='win32'},async t=>{
  const f=await fixture(t),taskRoot=await mkdtemp(join(tmpdir(),'codex-task-root-'));t.after(()=>rm(taskRoot,{recursive:true,maxRetries:3,retryDelay:100}));
  const broker=await createCodexToolBroker({...f.options,executionBinding:executionBinding(),inputRoots:[{name:'task_root',path:taskRoot}]});
  const ready=join(f.root,'src','child.ready'),release=join(f.root,'src','release'),late=join(f.root,'src','descendant-late.txt');
  const program="import os,time\nfrom pathlib import Path\nroot=Path('src');ready=root/'child.ready';release=root/'release'\npid=os.fork()\nif pid:\n while not ready.exists(): time.sleep(0.01)\n os._exit(0)\nos.setsid();os.closerange(0,3);ready.write_text(str(os.getpid()))\nwhile not release.exists(): time.sleep(0.01)\n(root/'descendant-late.txt').write_text('late');os._exit(0)";
  const result=output(await broker.call('run_task_program',{program:'python',args:['-c',program],cwd:'workspace'},'descendant'));assert.equal(result.exit_code,0);assert(await waitForFile(ready));
  await writeFile(release,'release');await delay(200);await assert.rejects(readFile(late,'utf8'),{code:'ENOENT'});broker.revoke();assert.equal((await broker.quiesce()).quiescent,true);
});

test('a failed exact stop rejects promptly, retains ownership, and a later exact retry quiesces it', { skip: process.platform !== 'win32' }, async t => {
  const root=await mkdtemp(join(tmpdir(),'codex-stop-retry-')),workspace=join(root,'workspace'),taskRoot=join(root,'task');
  await mkdir(join(workspace,'src'),{recursive:true});await mkdir(taskRoot);t.after(()=>rm(root,{recursive:true,maxRetries:3,retryDelay:100}));
  let primary,identityPath,stopCalls=0,handle;let handleReady;const observedHandle=new Promise(resolveHandle=>{handleReady=resolveHandle;});
  class FakeChild extends EventEmitter {
    constructor(kind){super();this.kind=kind;this.stdout=new PassThrough();this.stderr=new PassThrough();this.closed=false;}
    kill(){if(this.closed)return false;this.closed=true;setImmediate(()=>{this.emit('exit',null,'SIGTERM');this.stdout.end();this.stderr.end();this.emit('close',null,'SIGTERM');});return true;}
  }
  const fromWsl=path=>`${path[5].toUpperCase()}:\\${path.slice(7).replaceAll('/','\\')}`;
  const processLauncher=(_launcher,argv)=>{
    if(argv.includes('codex-bound-kill')){
      const child=new FakeChild('stop'),code=++stopCalls===1?1:0;setImmediate(()=>{child.closed=true;child.emit('exit',code,null);child.emit('close',code,null);});return child;
    }
    primary=new FakeChild('primary');identityPath=fromWsl(argv[8]);writeFileSync(identityPath,`4321 ${argv[9]}\n`);return primary;
  };
  const controller=new AbortController();
  const pending=executeBoundProgram(executionBinding(),{program:'python',args:['-c','pass'],cwd:'workspace'},{workspace,task_root:taskRoot},{
    signal:controller.signal,writable:[join(workspace,'src')],processLauncher,onHandle:value=>{handle=value;handleReady();},
  });
  await observedHandle;controller.abort(Object.assign(new Error('fixture cancellation'),{code:'CODEX_EXECUTION_CANCELLED'}));
  await assert.rejects(pending,{code:'CODEX_EXECUTION_STOP_UNCONFIRMED'});assert.equal(handle.isQuiescent(),false);assert.equal(primary.closed,false);
  await handle.stop();assert.equal(stopCalls,2);assert.equal(handle.isQuiescent(),true);assert.equal(primary.closed,true);
  await assert.rejects(readFile(identityPath,'utf8'),{code:'ENOENT'});
});

test('normal process exit retains a retryable handle until host control-state cleanup succeeds', { skip: process.platform !== 'win32' }, async t => {
  const root=await mkdtemp(join(tmpdir(),'codex-control-cleanup-retry-')),workspace=join(root,'workspace'),taskRoot=join(root,'task');
  await mkdir(join(workspace,'src'),{recursive:true});await mkdir(taskRoot);t.after(()=>rm(root,{recursive:true,maxRetries:3,retryDelay:100}));
  let handle,removeCalls=0;
  class FakeChild extends EventEmitter {
    constructor(){super();this.stdout=new PassThrough();this.stderr=new PassThrough();}
    kill(){return false;}
  }
  const processLauncher=()=>{
    const child=new FakeChild();
    setImmediate(()=>{child.emit('exit',0,null);child.stdout.end();child.stderr.end();child.emit('close',0,null);});
    return child;
  };
  const removeControl=async(path,options)=>{
    removeCalls++;
    if(removeCalls===1)throw Object.assign(new Error('Synthetic control cleanup failure'),{code:'EACCES'});
    return rm(path,options);
  };
  const pending=executeBoundProgram(executionBinding(),{program:'python',args:['-c','pass'],cwd:'workspace'},{workspace,task_root:taskRoot},{
    writable:[join(workspace,'src')],processLauncher,removeControl,onHandle:value=>{handle=value;},
  });
  await assert.rejects(pending,{code:'CODEX_EXECUTION_CLEANUP'});
  assert.equal(handle.isQuiescent(),false,'process exit alone is not complete ownership cleanup');
  await handle.stop();
  assert.equal(removeCalls,2);
  assert.equal(handle.isQuiescent(),true);
});

test('whole-project write scope allows new task files but still rejects workspace escapes',async t=>{
  const f=await fixture(t);const broker=await createCodexToolBroker({...f.options,allowedPaths:['.']});
  await broker.call('write_workspace',{path:'result.txt',expected_sha256:null,text:'result'},'new-result');
  assert.equal(await readFile(join(f.root,'result.txt'),'utf8'),'result');
  await assert.rejects(broker.call('write_workspace',{path:'../outside.txt',expected_sha256:null,text:'outside'},'escape'),{code:'INVALID_RESOURCE_PATH'});
});

test('bounded resource reads preserve pin identity and report actual numbered coverage',async t=>{
  const f=await fixture(t);const bytes='first\nsecond\nthird';
  const options={...f.options,resources:[{path:'source/file.md',bytes,sha256:digest(bytes)}]};
  const broker=await createCodexToolBroker(options);
  const result=output(await broker.call('read_workflow_resource_range',{path:'source/file.md',start_line:2,end_line:10},'slice'));
  assert.equal(result.text,'2: second\n3: third');assert.equal(result.total_lines,3);assert.equal(result.end_line,3);assert.equal(result.sha256,digest(bytes));
  assert.equal(f.operations[0].start_line,2);
  await assert.rejects(broker.call('read_workflow_resource_range',{path:'source/file.md',start_line:1,end_line:201},'too-large'),{code:'CODEX_RESOURCE_RANGE'});
  const other=await createCodexToolBroker(options);
  await assert.rejects(other.call('read_workflow_resource_range',{path:'unowned',start_line:1,end_line:2},'unowned'),{code:'CODEX_RESOURCE_DENIED'});
});

test('pinned Workflow resource materializes by hash without entering model output', async t => {
  const f = await fixture(t); const bytes = 'print("pinned")\n'.repeat(2500);
  const options = { ...f.options, resources: [{ path: 'scripts/runner.py', bytes, sha256: digest(bytes) }] };
  const broker = await createCodexToolBroker(options);
  assert(broker.tools().some(tool => tool.name === 'materialize_workflow_resource'));
  const result = output(await broker.call('materialize_workflow_resource',
    { path: 'scripts/runner.py', destination: 'src/runner.py', expected_sha256: null }, 'copy'));
  assert.equal(result.sha256, digest(bytes));
  assert.equal(result.text, undefined);
  assert.equal(await readFile(join(f.root, 'src', 'runner.py'), 'utf8'), bytes);
  assert.equal(f.operations[0].source_sha256, digest(bytes));
  const again = output(await broker.call('materialize_workflow_resource',
    { path: 'scripts/runner.py', destination: 'src/runner.py', expected_sha256: null }, 'copy-again'));
  assert.equal(again.unchanged, true);
  const readOnly = await createCodexToolBroker({ ...options, access: 'read_only', allowedPaths: [] });
  assert(!readOnly.tools().some(tool => tool.name === 'materialize_workflow_resource'));
  const outside = await createCodexToolBroker(options);
  await assert.rejects(outside.call('materialize_workflow_resource',
    { path: 'scripts/runner.py', destination: 'other/runner.py', expected_sha256: null }, 'outside'),
  { code: 'CODEX_TOOL_WRITE_DENIED' });
});

test('workspace broker performs audited CAS writes and rejects stale observations', async t => {
  const f = await fixture(t); const broker = await createCodexToolBroker(f.options);
  const read = output(await broker.call('read_workspace', { path: 'src/main.txt' }, 'read-1'));
  assert.equal(read.sha256, digest('before'));
  await broker.call('write_workspace', { path: 'src/main.txt', expected_sha256: read.sha256, text: 'after' }, 'write-1');
  assert.equal(await readFile(join(f.root, 'src', 'main.txt'), 'utf8'), 'after');
  assert.deepEqual(f.operations.map(event => event.phase), ['read', 'intent', 'committed']);
  await assert.rejects(broker.call('write_workspace', { path: 'src/main.txt', expected_sha256: read.sha256, text: 'stale' }, 'write-2'), { code: 'CODEX_TOOL_WRITE_CONFLICT' });
});

test('workspace broker blocks traversal, runtime and Skill paths, links and write scope escape', async t => {
  const f = await fixture(t); await mkdir(join(f.root, 'private')); await writeFile(join(f.root, 'private', 'secret'), 'secret');
  await link(join(f.root, 'private', 'secret'), join(f.root, 'src', 'hardlink'));
  await symlink(join(f.root, 'private'), join(f.root, 'src', 'linked-directory'), 'junction');
  for (const [name, args, code] of [
    ['read_workspace', { path: '../outside' }, 'INVALID_RESOURCE_PATH'],
    ['read_workspace', { path: '.codex/config.toml' }, 'CODEX_TOOL_PATH_DENIED'],
    ['read_workspace', { path: 'src/SKILL.md' }, 'CODEX_TOOL_PATH_DENIED'],
    ['read_workspace', { path: 'private/secret' }, 'CODEX_TOOL_PATH_DENIED'],
    ['read_workspace', { path: 'src/hardlink' }, 'CODEX_TOOL_FILE'],
    ['read_workspace', { path: 'src/linked-directory/secret' }, 'WORKFLOW_SYMLINK'],
    ['write_workspace', { path: 'out.txt', expected_sha256: null, text: 'no' }, 'CODEX_TOOL_WRITE_DENIED'],
  ]) {
    const broker = await createCodexToolBroker({ ...f.options, deniedPaths: [join(f.root, 'private')] });
    await assert.rejects(broker.call(name, args, 'denied'), { code });
  }
  const readonly = await createCodexToolBroker({ ...f.options, access: 'read_only' });
  assert(!readonly.tools().some(tool => tool.name === 'write_workspace'));
  await assert.rejects(readonly.call('write_workspace', { path: 'src/main.txt', text: 'no', expected_sha256: digest('before') }, 'denied'), { code: 'CODEX_TOOL_DENIED' });
});

test('transport-safe resource chunks cover exact UTF-8 bytes without gaps or truncation',async t=>{
  const f=await fixture(t);const bytes='alpha🙂beta\n'+('x'.repeat(25000));
  const broker=await createCodexToolBroker({...f.options,resources:[{path:'analysis/request.txt',bytes,sha256:digest(bytes)}]});
  const pieces=[];let start=0,complete=false;
  while(!complete){const item=output(await broker.call('read_workflow_resource_chunk',{path:'analysis/request.txt',start_byte:start,max_bytes:12000},`chunk-${start}`));assert.equal(item.start_byte,start);pieces.push(item.text);start=item.next_byte;complete=item.complete;}
  assert.equal(pieces.join(''),bytes);assert.equal(start,Buffer.byteLength(bytes));
  assert(f.operations.every((item,index)=>item.start_byte===(index?f.operations[index-1].end_byte:0)&&item.bytes<=12000));
  await assert.rejects(broker.call('read_workflow_resource_chunk',{path:'analysis/request.txt',start_byte:7,max_bytes:12000},'bad-boundary'),{code:'CODEX_RESOURCE_CHUNK'});
});

test('managed broker returns audited recoverable tool errors so the model can correct its request', async t => {
  const f = await fixture(t); const operations = [];
  const broker = await createCodexToolBroker({ ...f.options, recoverToolErrors: true, onOperation: async event => operations.push(event) });
  const rejected = await broker.call('read_workspace', { path: 'missing.txt' }, 'missing');
  assert.equal(rejected.success, false);
  assert.deepEqual(JSON.parse(rejected.contentItems[0].text), { error: { code: 'CODEX_TOOL_FILE', message: 'Only bounded regular files without hard links are supported' } });
  assert.deepEqual(operations, [{ call_id: 'missing', tool: 'read_workspace', path: 'missing.txt', phase: 'rejected', code: 'CODEX_TOOL_FILE', diagnostic: 'Only bounded regular files without hard links are supported' }]);
  const missingDirectory = await broker.call('list_workspace', { path: 'environment' }, 'missing-directory');
  assert.deepEqual(JSON.parse(missingDirectory.contentItems[0].text), { error: { code: 'CODEX_TOOL_DIRECTORY', message: 'Expected an existing workspace directory' } });
  assert.equal(operations.at(-1).phase, 'rejected');
  assert.equal(operations.at(-1).code, 'CODEX_TOOL_DIRECTORY');
  assert.equal(output(await broker.call('read_workspace', { path: 'src/main.txt' }, 'corrected')).text, 'before');
});

test('output limit is an explicit audited tool failure after termination and permits a narrower query', async t => {
  const f=await fixture(t);const operations=[];
  const runtimeEnvironment={status:'ready',tools:[{name:'node',status:'found',path:process.execPath}]};
  const broker=await createCodexToolBroker({...f.options,runtimeEnvironment,recoverToolErrors:true,onOperation:async event=>operations.push(event)});
  const failed=await broker.call('run_task_program',{program:'node',args:['-e',"process.stdout.write('x'.repeat(2*1024*1024));setTimeout(()=>{},10000)"],cwd:'workspace'},'too-large');
  assert.equal(failed.success,false);
  assert.equal(JSON.parse(failed.contentItems[0].text).error.code,'CODEX_EXECUTION_OUTPUT');
  assert.equal(broker.isQuiescent(),true);
  assert.equal(operations.at(-1).phase,'rejected');
  assert.equal(output(await broker.call('run_task_program',{program:'node',args:['-p','1+1'],cwd:'workspace'},'narrow')).stdout.trim(),'2');
  assert.deepEqual(await broker.quiesce(),{quiescent:true,error:null});
});

test('managed broker exposes declared task inputs as read-only logical mounts', async t => {
  const f = await fixture(t); const input = join(f.root, 'task-input');
  await mkdir(join(input, 'environment'), { recursive: true }); await writeFile(join(input, 'environment', 'data.json'), '{"value":7}');
  const operations = [];
  const broker = await createCodexToolBroker({ ...f.options, inputRoots: [{ name: 'task_root', path: input }], onOperation: async event => operations.push(event) });
  assert.deepEqual(output(await broker.call('list_input', { root: 'task_root', path: 'environment' }, 'list')).entries, [{ name: 'data.json', type: 'file' }]);
  assert.equal(output(await broker.call('read_input', { root: 'task_root', path: 'environment/data.json' }, 'read')).text, '{"value":7}');
  await assert.rejects(broker.call('read_input', { root: 'task_root', path: '../src/main.txt' }, 'escape'), { code: 'INVALID_RESOURCE_PATH' });
  assert.equal(operations[0].root, 'task_root');
  assert.equal(broker.tools().some(tool => tool.name === 'write_input'), false);
});

test('pinned resources ignore mutable source files and do not permit arbitrary reads', async t => {
  const f = await fixture(t); const broker = await createCodexToolBroker({ ...f.options, resources: [{ path: 'references/guide.txt', bytes: 'Pinned text', sha256: digest('Pinned text') }] });
  assert.equal(output(await broker.call('read_workflow_resource', { path: 'references/guide.txt' }, 'resource')).text, 'Pinned text');
  await assert.rejects(broker.call('read_workflow_resource', { path: 'src/main.txt' }, 'denied'), { code: 'CODEX_RESOURCE_DENIED' });
});

test('Windows environment short paths retain denied-directory identity after workspace canonicalization', { skip: process.platform !== 'win32' }, async t => {
  const f = await fixture(t); await mkdir(join(f.root, 'private')); await writeFile(join(f.root, 'private', 'secret'), 'do not expose');
  const alias = join(osTmpdir(), relative(tmpdir(), f.root));
  const broker = await createCodexToolBroker({ ...f.options, workspace: alias, deniedPaths: [join(alias, 'private'), join(alias, 'not-created')] });
  for (const path of ['private/secret', 'not-created/file']) await assert.rejects(broker.call('read_workspace', { path }, path), { code: 'CODEX_TOOL_PATH_DENIED' });
});

test('revoked lease and failed audit prevent writes; a post-commit audit error reports its side effect', async t => {
  const f = await fixture(t); const args = { path: 'src/main.txt', expected_sha256: digest('before'), text: 'after' };
  const rejected = await createCodexToolBroker({ ...f.options, onOperation: async () => { throw new Error('journal unavailable'); } });
  await assert.rejects(rejected.call('write_workspace', args, 'intent'), /journal unavailable/);
  assert.equal(await readFile(join(f.root, 'src', 'main.txt'), 'utf8'), 'before');
  const committed = await createCodexToolBroker({ ...f.options, onOperation: async event => { if (event.phase === 'committed') throw new Error('journal unavailable'); } });
  await assert.rejects(committed.call('write_workspace', args, 'commit'), error => error.committed === true && error.operation.after_sha256 === digest('after'));
  assert.equal(await readFile(join(f.root, 'src', 'main.txt'), 'utf8'), 'after');
  const revoked = await createCodexToolBroker(f.options); f.revoke();
  await assert.rejects(revoked.call('read_workspace', { path: 'src/main.txt' }, 'revoked'), /lease revoked/);
});

test('shutdown revokes a write waiting on its durable intent and waits for its explicit failure outcome', async t => {
  const f = await fixture(t); let releaseIntent; let observedIntent;
  const intentSeen = new Promise(resolve => { observedIntent = resolve; });
  const intentGate = new Promise(resolve => { releaseIntent = resolve; });
  const broker = await createCodexToolBroker({ ...f.options, onOperation: async event => {
    if (event.phase === 'intent') { observedIntent(); await intentGate; }
  } });
  const pending = broker.call('write_workspace', { path: 'src/main.txt', text: 'must-not-write', expected_sha256: digest('before') }, 'shutdown-write');
  const rejected = assert.rejects(pending, { code: 'CODEX_BROKER_REVOKED' });
  await intentSeen; broker.revoke(); const drained = broker.quiesce(); releaseIntent(); await rejected;
  const outcome = await drained; assert.equal(outcome.quiescent, true); assert.equal(outcome.error.code, 'CODEX_BROKER_REVOKED');
  assert.equal(await readFile(join(f.root, 'src', 'main.txt'), 'utf8'), 'before');
});
