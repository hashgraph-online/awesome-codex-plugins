import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,mkdir,writeFile,rm,chmod} from 'node:fs/promises';
import {join,dirname} from 'node:path';
import {tmpdir} from './physical-tempdir.mjs';
import {execFileSync} from 'node:child_process';
import {normalizeRuntimeRequirements,normalizeExecutableRequirements} from '../lib/runtime-requirements.mjs';
import {prepareRuntimeEnvironment,verifyRuntimeEnvironment,readHostRuntimeRegistry,updateRuntimeCandidate,registryPathForConfig} from '../lib/runtime-environment.mjs';

async function fixture(fn){
 const root=await mkdtemp(join(tmpdir(),'runtime-registry-'));
 try{return await fn(root);}finally{await rm(root,{recursive:true,force:true});}
}
async function versionTool(folder,name,version){
 await mkdir(folder,{recursive:true});
 const path=join(folder,name+(process.platform==='win32'?'.cmd':''));
 await writeFile(path,process.platform==='win32'?'@echo off\r\necho '+name+' '+version+'\r\n':'#!/bin/sh\necho '+name+' '+version+'\n');
 if(process.platform!=='win32')await chmod(path,0o755);
 return path;
}
const envFor=root=>({USERPROFILE:join(root,'home'),HOME:join(root,'home'),PATH:''});

test('portable requirement normalization rejects paths and conflicting versions',()=>{
 assert.deepEqual(normalizeExecutableRequirements(['tool',{name:'tool',version:'>=1,<3'}]),[{name:'tool',version:'>=1.0.0,<3.0.0'}]);
 assert.throws(()=>normalizeExecutableRequirements([{name:'python',version:'>=3.12,<3.11'}]),{code:'ENVIRONMENT_REQUIREMENT_CONFLICT'});
 assert.throws(()=>normalizeExecutableRequirements([{name:'C:\\tools\\python.exe'}]),{code:'ENVIRONMENT_DEPENDENCY_NAME'});
 const portable=normalizeRuntimeRequirements({executables:[{name:'python',version:'>=3',python_modules:['json']}]});
 assert.equal(JSON.stringify(portable).includes('C:\\'),false);
});

test('version mismatch selects the second candidate and persists a reusable host binding',async()=>fixture(async root=>{
 const first=join(root,'first'),second=join(root,'second'),registryPath=join(root,'host-runtime-registry.json');
 await versionTool(first,'media-tool','1.0.0');const selected=await versionTool(second,'media-tool','2.1.0');
 const requirements={executables:[{name:'media-tool',version:'>=2,<3'}]};
 const ready=await prepareRuntimeEnvironment(requirements,{registryPath,env:envFor(root),extraDirectories:[first,second]});
 assert.equal(ready.status,'ready');assert.equal(ready.tools[0].path,selected);
 assert.equal(ready.tools[0].evidence.observed_version,'2.1.0');
 const registry=await readHostRuntimeRegistry(registryPath);
 assert.equal(Object.values(registry.candidates)[0].path,selected);
 const reused=await prepareRuntimeEnvironment(requirements,{registryPath,env:envFor(root)});
 assert.equal(reused.status,'ready');assert.equal(reused.tools[0].path,selected);
 assert.equal((await readHostRuntimeRegistry(registryPath)).generation,registry.generation);
 assert.equal((await verifyRuntimeEnvironment(requirements,ready,{registryPath,env:envFor(root)}))[0].path,selected);
 const legacy={tools:[{name:'media-tool',status:'found',path:selected}]};
 const verifiedLegacy=await verifyRuntimeEnvironment(requirements,legacy,{registryPath,env:envFor(root)});
 assert.equal(verifiedLegacy[0].evidence.observed_version,'2.1.0');
 assert.equal(verifiedLegacy[0].requirement_key,ready.tools[0].requirement_key);
 assert.equal(registryPathForConfig(join(root,'config.json')),registryPath);
}));

test('hidden registered tool is reused across compatible declarations but rejects incompatible versions',async()=>fixture(async root=>{
 const hidden=join(root,'outside-default-search'),registryPath=join(root,'host-runtime-registry.json');
 const path=await versionTool(hidden,'media-tool','2.1.0');
 const env=envFor(root);
 const initial=await prepareRuntimeEnvironment({executables:[{name:'media-tool',version:'>=1'}]},{registryPath,env,extraDirectories:[hidden]});
 assert.equal(initial.status,'ready');
 const narrowed=await prepareRuntimeEnvironment({executables:[{name:'media-tool',version:'>=1.2'}]},{registryPath,env});
 assert.equal(narrowed.status,'ready');assert.equal(narrowed.tools[0].path,path);
 assert.equal(narrowed.searched_directories.includes(hidden),false);
 const legacy=await prepareRuntimeEnvironment({executables:['media-tool']},{registryPath,env});
 assert.equal(legacy.status,'ready');assert.equal(legacy.tools[0].path,path);
 const incompatible=await prepareRuntimeEnvironment({executables:[{name:'media-tool',version:'>=3'}]},{registryPath,env});
 assert.equal(incompatible.status,'installation_approval_required');
 assert.deepEqual(incompatible.missing,['media-tool']);
 assert.equal(incompatible.tools[0].rejections.length,1);
 assert.equal(incompatible.tools[0].rejections[0].path,path);
 assert.equal(incompatible.tools[0].rejections[0].cause_code,'ENVIRONMENT_VERSION_MISMATCH');
 assert.equal(incompatible.tools[0].rejections[0].observed_version,'2.1.0');
 const registry=await readHostRuntimeRegistry(registryPath);
 assert.equal(Object.keys(registry.candidates).length,3);
}));

test('missing module rejects a Python candidate; changed file stales pinned binding',async()=>fixture(async root=>{
 let python;try{python=execFileSync(process.platform==='win32'?'where':'which',['python'],{encoding:'utf8'}).trim().split(/\r?\n/)[0];}catch{return;}
 const missing={executables:[{name:'python',python_modules:['codex_test_module_that_cannot_exist_abcxyz']}]};
 const rejected=await prepareRuntimeEnvironment(missing,{env:envFor(root),extraDirectories:[dirname(python)]});
 assert.deepEqual(rejected.missing,['python']);assert.equal(rejected.tools[0].rejections[0].cause_code,'ENVIRONMENT_PYTHON_MODULE_MISSING');
 const requirements={executables:[{name:'python',python_modules:['json']}]};
 const ready=await prepareRuntimeEnvironment(requirements,{env:envFor(root),extraDirectories:[dirname(python)]});
 assert.equal(ready.status,'ready');assert.equal(ready.tools[0].evidence.probe_kind,'python');
 const tool=await versionTool(root,'mutable','1.0.0'),mutable={executables:[{name:'mutable',version:'>=1'}]};
 const pinned=await prepareRuntimeEnvironment(mutable,{env:envFor(root),extraDirectories:[root]});
 await writeFile(tool,process.platform==='win32'?'@echo off\r\necho mutable 1.1.0\r\n':'#!/bin/sh\necho mutable 1.1.0\n');
 await assert.rejects(verifyRuntimeEnvironment(mutable,pinned,{env:envFor(root)}),{code:'ENVIRONMENT_BINDING_STALE',dependency:'mutable',cause_code:'FILE_CHANGED'});
}));

test('malformed registry fails visibly and concurrent writers merge distinct keys',async()=>fixture(async root=>{
 const registryPath=join(root,'host-runtime-registry.json');
 await writeFile(registryPath,'{bad');
 await assert.rejects(readHostRuntimeRegistry(registryPath),{code:'ENVIRONMENT_REGISTRY_INVALID'});
 await rm(registryPath);
 const first=await versionTool(root,'alpha','1.0.0'),second=await versionTool(root,'beta','1.0.0');
 await Promise.all([
  updateRuntimeCandidate({name:'alpha',version:'>=1'},first,{registryPath}),
  updateRuntimeCandidate({name:'beta',version:'>=1'},second,{registryPath})
 ]);
 const registry=await readHostRuntimeRegistry(registryPath);
 assert.equal(Object.keys(registry.candidates).length,2);assert.equal(registry.generation,2);
 assert.deepEqual(Object.values(registry.candidates).map(value=>value.requirement.name).sort(),['alpha','beta']);
}));

test('stale registered candidate is re-probed and replaced by a valid host candidate',async()=>fixture(async root=>{
 const first=join(root,'first'),second=join(root,'second'),registryPath=join(root,'host-runtime-registry.json');
 const oldPath=await versionTool(first,'encoder','2.0.0');
 const requirements={executables:[{name:'encoder',version:'>=2'}]};
 const initial=await prepareRuntimeEnvironment(requirements,{registryPath,env:envFor(root),extraDirectories:[first]});
 assert.equal(initial.status,'ready');
 await rm(oldPath);
 const newPath=await versionTool(second,'encoder','3.0.0');
 const rebound=await prepareRuntimeEnvironment(requirements,{registryPath,env:envFor(root),extraDirectories:[second]});
 assert.equal(rebound.status,'ready');assert.equal(rebound.tools[0].path,newPath);
 assert.equal(Object.values((await readHostRuntimeRegistry(registryPath)).candidates)[0].path,newPath);
 await assert.rejects(verifyRuntimeEnvironment(requirements,initial,{registryPath,env:envFor(root)}),{code:'ENVIRONMENT_BINDING_STALE',dependency:'encoder'});
}));

test('named Conda environment supplies Python after an invalid base candidate',async()=>fixture(async root=>{
 const home=join(root,'home'),base=join(home,'Miniconda3'),named=join(base,'envs','analysis');
 await mkdir(join(base,process.platform==='win32'?'python.exe':'python'),{recursive:true});
 const candidate=join(named,process.platform==='win32'?'python.exe':'python');
 await mkdir(named,{recursive:true});await writeFile(candidate,'fixture');
 if(process.platform!=='win32')await chmod(candidate,0o755);
 const prepared=await prepareRuntimeEnvironment({executables:['python']},{env:envFor(root)});
 assert.equal(prepared.status,'ready');assert.equal(prepared.tools[0].path,candidate);
 assert(prepared.searched_directories.includes(named));
}));

test('a non-executable version candidate is reported and the next candidate is tried',{skip:process.platform!=='win32'},async()=>fixture(async root=>{
 const folder=join(root,'tools');
 await mkdir(folder,{recursive:true});await writeFile(join(folder,'encoder.exe'),'not an executable');
 const candidate=await versionTool(folder,'encoder','2.0.0');
 const result=await prepareRuntimeEnvironment({executables:[{name:'encoder',version:'>=2'}]},{env:envFor(root),extraDirectories:[folder]});
 assert.equal(result.status,'ready');assert.equal(result.tools[0].path,candidate);
 assert.equal(result.tools[0].rejections[0].cause_code,'UNKNOWN');
 assert.equal(result.tools[0].rejections[0].path,join(folder,'encoder.exe'));
}));
