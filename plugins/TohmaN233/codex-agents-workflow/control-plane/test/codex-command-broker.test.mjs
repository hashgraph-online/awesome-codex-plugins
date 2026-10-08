import { deferred } from './fixtures/deferred.mjs';
import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from './physical-tempdir.mjs';
import { join } from 'node:path';
import { createCodexCommandBroker } from '../lib/execution/codex-command-broker.mjs';

async function fixture(t, { output = 'complete output', exitCode = 0, access = 'read_only', allowedPaths = [],recoverToolErrors=false } = {}) {
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
        await writeFile(spec.output_path, output, { flag: 'wx' });
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
    access, allowedPaths,recoverToolErrors, env: {}, clientFactory: () => client, platform: 'win32', nodeBinary: process.execPath });
  return { broker, calls, spoolRoot, root };
}

test('Host command broker ignores a model-selected low output budget and returns the complete result', async t => {
  const expected = `${'source line\n'.repeat(9000)}END_MARKER`;
  const { broker, calls, spoolRoot } = await fixture(t, { output: expected });
  const toolNames = broker.tools().map(tool => tool.name);
  assert.deepEqual(toolNames, ['run_workspace_command', 'continue_workspace_command']);
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
  const completion=deferred(),execStarted=deferred(),spoolRoot=join(root,'spool');let spec;
  const client={initialized(){},async call(method,params){
    if(method==='initialize')return {};
    if(method==='command/exec'){spec=JSON.parse(await readFile(params.command.at(-1),'utf8'));execStarted.resolve();return completion.promise;}
    assert.fail(`Unexpected method ${method}`);
  },async close(){}};
  const broker=createCodexCommandBroker({binary:join(root,'codex'),home:root,cwd:root,spoolRoot,
    access:'read_only',env:{},clientFactory:()=>client,platform:'win32',nodeBinary:process.execPath});
  const started=JSON.parse((await broker.call('run_workspace_command',{cmd:'fixture',yield_time_ms:0},'call-1')).contentItems[0].text);
  assert.equal(started.status,'running');
  await execStarted.promise;
  const stopping=JSON.parse((await broker.call('continue_workspace_command',{session_id:started.session_id,chars:'\u0003',yield_time_ms:0},'call-2')).contentItems[0].text);
  assert.equal(stopping.status,'running');assert.deepEqual([...await readFile(spec.stdin_path)],[3]);
  const output='runner stopped its exact child tree';await writeFile(spec.output_path,output,{flag:'wx'});
  completion.resolve({exitCode:130,stdout:JSON.stringify({schema_version:1,exit_code:130,signal:'SIGINT',output_bytes:Buffer.byteLength(output)}),stderr:''});
  const stopped=JSON.parse((await broker.call('continue_workspace_command',{session_id:started.session_id,yield_time_ms:1000},'call-3')).contentItems[0].text);
  assert.equal(stopped.status,'completed');assert.equal(stopped.exit_code,130);assert.equal(stopped.output,output);
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
