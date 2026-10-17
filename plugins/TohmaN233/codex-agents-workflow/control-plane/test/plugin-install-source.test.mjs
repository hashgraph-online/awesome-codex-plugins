import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,mkdir,readFile,writeFile,rm,cp} from 'node:fs/promises';
import {join,resolve} from 'node:path';
import {tmpdir} from './physical-tempdir.mjs';
import {installLocal} from '../../scripts/install-local.mjs';
import {readNativeContextProfileTemplate} from '../../scripts/native-context-profile.mjs';

async function fixture(run){
 const home=await mkdtemp(join(tmpdir(),'plugin-install-source-'));
 try{
  const sourceRoot=join(home,'source','plugins','codex-agents-workflow'),version='1.2.2';
  const cacheRoot=join(home,'cache','codex-agents-workflow','codex-agents-workflow'),deployed=join(cacheRoot,version),codexHome=join(home,'codex-home');
  await mkdir(join(sourceRoot,'.codex-plugin'),{recursive:true});await mkdir(join(sourceRoot,'agent-profiles'));await mkdir(join(sourceRoot,'control-plane'));
  await writeFile(join(sourceRoot,'.codex-plugin','plugin.json'),JSON.stringify({name:'codex-agents-workflow',version}));
  await writeFile(join(sourceRoot,'agent-profiles','caw-native-builtins.toml'),readNativeContextProfileTemplate());
  await writeFile(join(sourceRoot,'control-plane','server.mjs'),'export const fixed = true;\n');
  await mkdir(join(home,'source','.agents','plugins'),{recursive:true});
  await writeFile(join(home,'source','.agents','plugins','marketplace.json'),JSON.stringify({name:'codex-agents-workflow',plugins:[{name:'codex-agents-workflow',source:{source:'local',path:'./plugins/codex-agents-workflow'}}]}));
  await cp(sourceRoot,deployed,{recursive:true});
  await run({home,sourceRoot,cacheRoot,deployed,codexHome,currentVersion:version});
 }finally{assert(home.startsWith(resolve(tmpdir())));await rm(home,{recursive:true});}
}

test('same-version stale installation cannot report success or install profile',async()=>fixture(async options=>{
 await writeFile(join(options.deployed,'control-plane','server.mjs'),'export const fixed = false;\n');
 let installs=0;
 await assert.rejects(installLocal({...options,install:async()=>{installs++;}}),error=>error.code==='PLUGIN_SOURCE_MISMATCH');
 assert.equal(installs,1);
 await assert.rejects(readFile(join(options.codexHome,'agents','caw-native-builtins.toml')),error=>error.code==='ENOENT');
}));

test('local installer registers its own source before add and verifies that installed source',async()=>fixture(async options=>{
 const calls=[];
 const runCli=(command,args)=>{
  calls.push({command,args});
  return '';
 };
 const result=await installLocal({...options,runCli});
 assert.deepEqual(calls.map(c=>c.args),[
  ['plugin','marketplace','add',join(options.home,'source')],
  ['plugin','add','codex-agents-workflow@codex-agents-workflow'],
 ]);
 assert.equal(result.installed,true);assert.equal(result.source.source_root,options.sourceRoot);
 assert.equal(result.source.installed_root,options.deployed);assert.equal(result.source.file_count,3);
 assert.match(result.source.sha256,/^[a-f0-9]{64}$/);
}));

test('source registration failure is exposed before install without retry',async()=>fixture(async options=>{
 const expected=new Error('source registration failed'),calls=[];
 await assert.rejects(installLocal({...options,runCli:(command,args)=>{calls.push(args);throw expected;}}),error=>error===expected);
 assert.equal(calls.length,1);
}));

for(const path of ['AGENTS.md','control-plane/agent.md','control-plane/aGeNtS.Md']){
 test('private maintainer instructions are rejected before installation: '+path,async()=>fixture(async options=>{
  await writeFile(join(options.sourceRoot,path),'Private maintenance rules.\n');
  let calls=0;
  await assert.rejects(installLocal({...options,runCli:()=>{calls++;}}),error=>error.code==='PLUGIN_PRIVATE_INSTRUCTIONS');
  assert.equal(calls,0);
  await assert.rejects(readFile(join(options.codexHome,'agents','caw-native-builtins.toml')),error=>error.code==='ENOENT');
 }));
}
