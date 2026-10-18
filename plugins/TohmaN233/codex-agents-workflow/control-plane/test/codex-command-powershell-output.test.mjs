import test from 'node:test';
import assert from 'node:assert/strict';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {mkdir,mkdtemp,readFile,rm,writeFile} from 'node:fs/promises';
import {join} from 'node:path';
import {tmpdir} from './physical-tempdir.mjs';
import {createCodexCommandBroker} from '../lib/execution/codex-command-broker.mjs';

const execute=promisify(execFile);
async function processResult(binary,args,cwd){
  try{const result=await execute(binary,args,{cwd,encoding:'utf8',windowsHide:true,maxBuffer:4*1024*1024});
    return {...result,exitCode:0};
  }catch(error){if(!Number.isInteger(error.code))throw error;return {stdout:error.stdout,stderr:error.stderr,exitCode:error.code};}
}
async function realBroker(t,{outputBudget=4096}={}){
  const root=await mkdtemp(join(tmpdir(),'broker-powershell-output-')),workspace=join(root,'workspace');
  await mkdir(workspace);await writeFile(join(workspace,'object-marker.txt'),'TEXT-MARKER');
  t.after(()=>rm(root,{recursive:true,force:true}));
  const captures=[];
  const client={async call(method,params){
    assert.equal(method,'command/exec');
    const spec=JSON.parse(await readFile(params.command.at(-1),'utf8'));
    const source=await readFile(join(root,'spool',spec.process_id,'command-source.ps1'));
    const result=await processResult(params.command[0],params.command.slice(1),params.cwd);
    captures.push({spec,source,lifecycle:(await readFile(spec.lifecycle_path,'utf8')).trim().split('\n').map(JSON.parse),
      bytes:await readFile(spec.output_path),control:JSON.parse(result.stdout)});
    return result;
  },async close(){}};
  const broker=createCodexCommandBroker({binary:process.execPath,home:root,cwd:workspace,access:'read_only',
    spoolRoot:join(root,'spool'),getClient:()=>client,getOutputBudget:()=>({max_result_bytes:outputBudget})});
  t.after(()=>broker.close());
  async function run(cmd,shell,options={}){
    let response=await broker.call('run_workspace_command',{cmd,shell,login:false,...options},'actual-shell-'+captures.length);
    const pieces=[];let current;
    do{
      assert(Buffer.byteLength(JSON.stringify(response))<=outputBudget);
      current=JSON.parse(response.contentItems[0].text);pieces.push(current.output);
      if(current.has_more)response=await broker.call('continue_workspace_command',{session_id:current.session_id},'drain-'+pieces.length);
    }while(current.has_more);
    assert.equal(current.status,'completed');assert.equal(broker.pending().length,0);
    const capture=captures.at(-1);
    assert.equal(capture.source.toString('utf8'),cmd);
    assert(capture.lifecycle.some(event=>event.phase==='child_close'));
    assert(capture.lifecycle.some(event=>event.phase==='stream_close'&&event.stream==='stdout'));
    assert(capture.lifecycle.some(event=>event.phase==='stream_close'&&event.stream==='stderr'));
    assert.equal(capture.control.error_code,undefined);
    assert.equal(Buffer.byteLength(pieces.join('')),capture.control.output_bytes);
    assert.equal(pieces.join(''),capture.bytes.toString('utf8'));
    return {...current,output:pieces.join(''),capture};
  }
  return {workspace,broker,captures,run};
}
async function availableShell(t,shell){
  try{const result=await processResult(shell,['-NoLogo','-NoProfile','-Command','$PSVersionTable.PSVersion.ToString()']);
    assert.equal(result.exitCode,0);t.diagnostic(shell+' version '+result.stdout.trim());return true;
  }catch(error){if(shell==='pwsh.exe'&&error.code==='ENOENT'){t.skip('Optional pwsh is unavailable');return false;}throw error;}
}
const native=program=>"& '"+process.execPath.replaceAll("'","''")+"' -e \""+program+"\"";
for(const shell of ['powershell.exe','pwsh.exe'])for(const [label,command,marker] of [
  ['pwd','pwd','Path'],
  ['object pipeline',"[PSCustomObject]@{ObjectMarker='OBJECT-MARKER';Kind='pipeline'} | Select-Object ObjectMarker,Kind",'OBJECT-MARKER'],
  ['mixed object and text',"'TEXT-BEGIN'; Get-ChildItem -Force | Select-Object Name,Mode; Get-Content -Raw object-marker.txt; 'TEXT-END'",'object-marker.txt'],
])test(`actual ${shell} broker preserves original ${label} stdout`,{skip:process.platform!=='win32'},async t=>{
  if(!await availableShell(t,shell))return;
  const f=await realBroker(t),baseline=await processResult(shell,['-NoLogo','-NoProfile','-Command',command],f.workspace);
  assert.equal(baseline.exitCode,0);assert.equal(baseline.stderr,'');assert(baseline.stdout.includes(marker));
  const actual=await f.run(command,shell);
  t.diagnostic(JSON.stringify({baseline_stdout_bytes:Buffer.byteLength(baseline.stdout),broker_output_bytes:actual.capture.bytes.length,
    baseline_exit:baseline.exitCode,broker_exit:actual.exit_code}));
  assert.equal(actual.exit_code,baseline.exitCode);
  assert.equal(actual.output,baseline.stdout);
});

for(const shell of ['powershell.exe','pwsh.exe'])for(const [label,command,expectedExit,stdoutMarker,stderrMarker] of [
  ['native success',native("process.stdout.write('NATIVE-STDOUT')"),0,'NATIVE-STDOUT',''],
  ['native failure',native("process.stderr.write('NATIVE-FAILURE');process.exit(4)"),1,'','NATIVE-FAILURE'],
  ['native success with stderr',native("process.stderr.write('NATIVE-STDERR');process.stdout.write('NATIVE-SUCCESS')"),0,'NATIVE-SUCCESS','NATIVE-STDERR'],
  ['native failure followed by success',native('process.exit(4)')+"; 'RECOVERED-FINAL-SUCCESS'",0,'RECOVERED-FINAL-SUCCESS',''],
  ['object output before native failure',"[PSCustomObject]@{ObjectMarker='BEFORE-NATIVE-FAILURE'}; "+native('process.exit(4)'),1,'BEFORE-NATIVE-FAILURE',''],
  ['explicit exit',"'BEFORE-EXPLICIT-EXIT'; exit 7",7,'BEFORE-EXPLICIT-EXIT',''],
  ['terminating error',"'BEFORE-THROW'; throw 'TERMINATING-ERROR'; 'MUST-NOT-EXECUTE'",1,'BEFORE-THROW','TERMINATING-ERROR'],
  ['nonterminating error',"Write-Error 'NONTERMINATING-ERROR'",1,'','NONTERMINATING-ERROR'],
  ['nonterminating error followed by success',"Write-Error 'RECOVERED-ERROR'; 'RECOVERED-SUCCESS'",0,'RECOVERED-SUCCESS','RECOVERED-ERROR'],
  ['return',"'BEFORE-RETURN'; return; 'MUST-NOT-EXECUTE'",0,'BEFORE-RETURN',''],
  ['object output before return',"[PSCustomObject]@{ObjectMarker='BEFORE-RETURN-OBJECT'}; return",0,'BEFORE-RETURN-OBJECT',''],
  ['status variable collision',"$workflowCommandSucceeded=$false; 'USER-VARIABLE-RETAINED'",0,'USER-VARIABLE-RETAINED',''],
])test(`actual ${shell} shell boundary retains ${label} semantics`,{skip:process.platform!=='win32'},async t=>{
  if(!await availableShell(t,shell))return;
  const f=await realBroker(t),baseline=await processResult(shell,['-NoLogo','-NoProfile','-Command',command],f.workspace);
  assert.equal(baseline.exitCode,expectedExit,'The normal -Command reference establishes the status contract');
  const actual=await f.run(command,shell);
  assert.equal(actual.exit_code,baseline.exitCode);
  assert(actual.output.includes(stdoutMarker));assert(!/^MUST-NOT-EXECUTE\r?$/m.test(actual.output),
    'The error may quote source context, but the later statement must not execute');
  if(stderrMarker){assert(baseline.stderr.includes(stderrMarker));assert(actual.output.includes(stderrMarker));}
  else {assert.equal(baseline.stderr,'');assert.equal(actual.output,baseline.stdout);}
  const audit=f.broker.audit()[0];assert.equal(audit.exit_code,expectedExit);assert.equal(audit.output_bytes,actual.capture.bytes.length);
});

for(const shell of ['powershell.exe','pwsh.exe'])test(`actual ${shell} keeps UTF8 using/param source and native stdin`,{skip:process.platform!=='win32'},async t=>{
  if(!await availableShell(t,shell))return;
  const f=await realBroker(t),value='中文 × → 😀';
  const command="using namespace System.Text\nparam([string]$value='"+value+"')\n[Encoding]::UTF8.GetString([Encoding]::UTF8.GetBytes($value))\n"+
    '$value | '+native("process.stdin.on('data',b=>process.stdout.write(b))");
  const actual=await f.run(command,shell);
  assert.equal(actual.exit_code,0);assert.equal(actual.output.trim(),value+'\r\n'+value);
  assert(actual.capture.spec.argv.at(-1).length<2000);
});

for(const shell of ['powershell.exe','pwsh.exe'])test(`actual ${shell} drains long Unicode source within inherited chunk budget`,{skip:process.platform!=='win32'},async t=>{
  if(!await availableShell(t,shell))return;
  const f=await realBroker(t,{outputBudget:512}),value='中 × 😀'.repeat(6000)+'END-MANUSCRIPT';
  const command="using namespace System.Text\nparam([string]$unused='original')\nWrite-Output '"+value+"'";
  assert(Buffer.byteLength(command)>32768);
  assert(command.length>32768,'The original source exceeds the Windows UTF16 argv limit too');
  const actual=await f.run(command,shell);
  assert.equal(actual.exit_code,0);assert.equal(actual.output,value+'\r\n');
  assert(actual.capture.spec.argv.at(-1).length<2000);
  assert.equal(f.broker.audit()[0].output_bytes,Buffer.byteLength(value+'\r\n'));
});

for(const login of [undefined,false,true])test(`PowerShell invocation retains profile selection for login ${String(login)}`,async t=>{
  const root=await mkdtemp(join(tmpdir(),'broker-powershell-login-'));t.after(()=>rm(root,{recursive:true,force:true}));
  let spec;
  const client={async call(_method,params){spec=JSON.parse(await readFile(params.command.at(-1),'utf8'));
    await writeFile(spec.output_path,'');return {exitCode:0,stdout:JSON.stringify({schema_version:1,exit_code:0,output_bytes:0}),stderr:''};},async close(){}};
  const broker=createCodexCommandBroker({binary:process.execPath,home:root,cwd:root,access:'read_only',spoolRoot:join(root,'spool'),platform:'win32',
    getClient:()=>client,getOutputBudget:()=>({max_result_bytes:4096})});t.after(()=>broker.close());
  await broker.call('run_workspace_command',{cmd:'pwd',shell:'pwsh.exe',...(login===undefined?{}:{login})},'login-selection');
  assert.equal(spec.argv[0],'pwsh.exe');assert(spec.argv.includes('-NoLogo'));
  assert.equal(spec.argv.includes('-NoProfile'),login!==true);assert(spec.argv.includes('-Command'));
  // Do not execute the user's real profile to qualify argument selection.
});
