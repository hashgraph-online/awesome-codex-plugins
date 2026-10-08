import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,mkdir,writeFile,rm,realpath,chmod,symlink} from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import {tmpdir as osTmpdir} from 'node:os';
import {join} from 'node:path';
import {tmpdir} from './physical-tempdir.mjs';
import {discoverRuntimeEnvironment} from '../lib/runtime-environment.mjs';

test('fixture temporary directories canonicalize real environment aliases through the native filesystem',async t=>{
 const root=await mkdtemp(join(tmpdir(),'workflow-physical-tempdir-'));
 t.after(()=>rm(root,{recursive:true,force:true}));
 let alias;
 if(process.platform==='win32'){
  // Existing system folders retain 8.3 aliases even when the host no longer
  // generates short names for new fixture directories. This child only reads.
  const command="$taskFso=New-Object -ComObject Scripting.FileSystemObject; @($env:WORKFLOW_TEST_TEMP_ROOT,$env:ProgramFiles,${env:ProgramFiles(x86)}) | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | ForEach-Object { $taskFso.GetFolder($_).ShortPath } | ConvertTo-Json -Compress";
  const paths=JSON.parse(execFileSync('powershell.exe',['-NoProfile','-NonInteractive','-Command',command],{encoding:'utf8',env:{...process.env,WORKFLOW_TEST_TEMP_ROOT:osTmpdir()},windowsHide:true}));
  const candidates=Array.isArray(paths)?paths:[paths];
  const {realpathSync}=await import('node:fs');
  alias=candidates.find(path=>realpathSync(path)!==realpathSync.native(path))??candidates[0];
 }else{
  alias=join(root,'alias');
  await symlink(root,alias,'dir');
 }
 const code=`import assert from 'node:assert/strict';import {realpathSync} from 'node:fs';import {tmpdir as osTmpdir} from 'node:os';import {tmpdir} from ${JSON.stringify(new URL('./physical-tempdir.mjs',import.meta.url).href)};assert.equal(tmpdir(),realpathSync.native(osTmpdir()));`;
 execFileSync(process.execPath,['--input-type=module','-e',code],{env:{...process.env,TMP:alias,TEMP:alias,TMPDIR:alias},windowsHide:true});
});

test('dependency discovery searches host installations and supplied directories without installing',async()=>{
 const root=await mkdtemp(join(tmpdir(),'workflow-environment-'));
 try {
  const home=join(root,'home'),bin=join(home,'Miniconda3'),custom=join(root,'tools');
  await mkdir(bin,{recursive:true});await mkdir(custom);
  const suffix=process.platform==='win32'?'.exe':'';
  await writeFile(join(bin,'python'+suffix),'fixture');await writeFile(join(custom,'media-tool'+suffix),'fixture');
  if(process.platform!=='win32')await Promise.all([chmod(join(bin,'python'+suffix),0o755),chmod(join(custom,'media-tool'+suffix),0o755)]);
  const env={USERPROFILE:home,HOME:home,PATH:''};
  const missing=await discoverRuntimeEnvironment({executables:['python','media-tool']},{env});
  assert.equal(missing.status,'installation_approval_required');assert.deepEqual(missing.missing,['media-tool']);
  assert.equal(missing.installation_performed,false);assert.equal(missing.tools[0].status,'found');
  const ready=await discoverRuntimeEnvironment({executables:['python','media-tool','python']},{env,extraDirectories:[custom]});
  assert.equal(ready.status,'ready');assert.equal(ready.tools.length,2);assert.equal(ready.tools[1].path,await realpath(join(custom,'media-tool'+suffix)));
 } finally {await rm(root,{recursive:true,force:true});}
});

test('dependency discovery rejects command strings and relative search directories',async()=>{
 await assert.rejects(discoverRuntimeEnvironment({executables:['python --version']}),{code:'ENVIRONMENT_DEPENDENCY_NAME'});
 await assert.rejects(discoverRuntimeEnvironment({executables:[]},{extraDirectories:['relative']}),{code:'ENVIRONMENT_DIRECTORIES'});
});
