import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,mkdir,readFile,writeFile,rm} from 'node:fs/promises';
import {join} from 'node:path';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {tmpdir} from './physical-tempdir.mjs';
import {createCodexCommandBroker} from '../lib/execution/codex-command-broker.mjs';

const execute=promisify(execFile);
async function fixture(t){
  const root=await mkdtemp(join(tmpdir(),'literal-workspace-program-')),cwd=join(root,'workspace');await mkdir(cwd);
  const calls=[],operations=[];
  const client={async call(method,params){
    assert.equal(method,'command/exec');const spec=JSON.parse(await readFile(params.command.at(-1),'utf8'));spec.observed_stdin=await readFile(spec.stdin_path,'utf8');calls.push(spec);
    let result;try{result=await execute(params.command[0],params.command.slice(1),{cwd:params.cwd,windowsHide:true,encoding:'utf8',timeout:5000});}
    catch(error){if(!Number.isInteger(error.code))throw error;result={stdout:error.stdout,stderr:error.stderr,exitCode:error.code};}
    return {...result,exitCode:result.exitCode??0};
  },async close(){}};
  const broker=createCodexCommandBroker({binary:process.execPath,home:root,cwd,access:'bounded_write',allowedPaths:['.'],spoolRoot:join(root,'spool'),
    getClient:()=>client,getOutputBudget:()=>({max_result_bytes:16384}),onOperation:event=>operations.push(event)});
  t.after(async()=>{await broker.close();await rm(root,{recursive:true,maxRetries:3,retryDelay:100});});
  return {root,cwd,calls,operations,broker};
}
test('literal argv and exact UTF-8 stdin reach a real process at EOF without shell or helper script',async t=>{
  const f=await fixture(t),script=join(f.cwd,'read literal input.mjs');
  await writeFile(script,"import {readFileSync} from 'node:fs';process.stdout.write(JSON.stringify({args:process.argv.slice(2),input:readFileSync(0,'utf8'),cwd:process.cwd()}));");
  const args=['quotes " \' $() ` ; & |','中文 😀','--literal'],stdin='first\n中文 😀\r\n$HOME `backtick` "quote"\n';
  const result=await f.broker.call('run_workspace_program',{program:process.execPath,args:[script,...args],stdin},'literal-program');
  const observed=JSON.parse(result.contentItems[0].text);assert.equal(observed.status,'completed');assert.equal(observed.exit_code,0);
  assert.deepEqual(JSON.parse(observed.output),{args,input:stdin,cwd:f.cwd});
  assert.deepEqual(f.calls[0].argv,[process.execPath,script,...args]);assert.equal(f.calls[0].stdin_closed,true);
  assert.equal(f.calls[0].observed_stdin,stdin);assert.equal(f.operations[0].tool,'run_workspace_program');
  assert.equal(f.broker.audit()[0].command,JSON.stringify([process.execPath,script,...args]));
  assert(!f.broker.audit()[0].command.includes(stdin));assert.equal(f.broker.pending().length,0);
});
test('direct program preserves a nonzero process exit and rejects shell-only arguments before execution',async t=>{
  const f=await fixture(t);
  const result=await f.broker.call('run_workspace_program',{program:process.execPath,args:['-e',"process.stderr.write('visible failure');process.exit(7)"]},'failing-program');
  const observed=JSON.parse(result.contentItems[0].text);assert.equal(observed.exit_code,7);assert.equal(observed.output,'visible failure');
  for(const extra of [{cmd:'unowned shell'},{shell:'powershell.exe'},{stdin:'x'.repeat(2*1024*1024+1)}])
    await assert.rejects(f.broker.call('run_workspace_program',{program:process.execPath,args:[],...extra},'invalid'),{code:'CODEX_COMMAND_ARGUMENTS'});
  assert.equal(f.calls.length,1);
});
test('closed program stdin still permits its exact continuation stop control',async t=>{
  const f=await fixture(t);
  const response=await f.broker.call('run_workspace_program',{program:process.execPath,args:['-e',"process.stdout.write('started');setInterval(()=>{},1000)"],yield_time_ms:0},'owned-long-program');
  const first=JSON.parse(response.contentItems[0].text);assert.equal(first.status,'running');
  await assert.rejects(f.broker.call('continue_workspace_command',{session_id:first.session_id,chars:'late input'},'late-input'),{code:'CODEX_COMMAND_ARGUMENTS'});
  let started=false;
  for(let index=0;index<100&&!started;index++){
    if(f.calls.length)try{started=(await readFile(f.calls[0].output_path,'utf8')).includes('started');}catch(error){if(error.code!=='ENOENT')throw error;}
    if(!started)await new Promise(resolve=>setTimeout(resolve,10));
  }
  assert(started,'actual process must start before the stop control');
  const stopped=await f.broker.call('continue_workspace_command',{session_id:first.session_id,chars:'\u0003',yield_time_ms:30000},'stop-program');
  const final=JSON.parse(stopped.contentItems[0].text);assert.equal(final.status,'completed');assert.equal(final.exit_code,130);assert.equal(f.broker.pending().length,0);
});
