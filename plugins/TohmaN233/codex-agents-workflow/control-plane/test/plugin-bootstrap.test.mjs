import test from 'node:test';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {mkdtemp,mkdir,readdir,writeFile,rm} from 'node:fs/promises';
import {join,resolve} from 'node:path';
import {tmpdir} from './physical-tempdir.mjs';
import {installLocal} from '../../scripts/install-local.mjs';
const {installationNamespace,registeredRoot}=createRequire(import.meta.url)('../../scripts/mcp-bootstrap.cjs');

test('bootstrap selects only the registry version, rejects disabled or ambiguous installation',()=>{
 const entry={pluginId:'codex-agents-workflow@codex-agents-workflow',installed:true,enabled:true,version:'0.8.0+current'};
 const namespace=resolve(tmpdir(),'codex-agents-workflow','codex-agents-workflow');
 assert.equal(registeredRoot({installed:[entry]},namespace).version,entry.version);
 assert.throws(()=>registeredRoot({installed:[entry,entry]},namespace),/REGISTRY/);
 assert.throws(()=>registeredRoot({installed:[{...entry,enabled:false}]},namespace),/REGISTRY/);
 assert.throws(()=>registeredRoot({installed:[{...entry,version:'../elsewhere'}]},namespace),/REGISTRY/);
 assert.throws(()=>registeredRoot({},namespace),/REGISTRY/);
 assert.throws(()=>installationNamespace(resolve(tmpdir(),'unrelated')),/NAMESPACE/);
});

test('bootstrap selects the launching namespace even when another source has a newer version',()=>{
 const namespace=resolve(tmpdir(),'awesome-codex-plugins','codex-agents-workflow');
 const entries=[
  {pluginId:'codex-agents-workflow@codex-agents-workflow',installed:true,enabled:true,version:'99.0.0'},
  {pluginId:'codex-agents-workflow@awesome-codex-plugins',installed:true,enabled:true,version:'1.1.0'},
 ];
 const selected=registeredRoot({installed:entries},namespace);
 assert.equal(selected.marketplace,'awesome-codex-plugins');
 assert.equal(selected.pluginId,entries[1].pluginId);
 assert.equal(selected.root,join(namespace,'1.1.0'));
 assert.throws(()=>registeredRoot({installed:[entries[0]]},namespace),/REGISTRY/);
 assert.throws(()=>registeredRoot({installed:[entries[0],{...entries[1],enabled:false}]},namespace),/REGISTRY/);
});

test('upgrade deletes obsolete plugin cache versions and creates no rollback store',async()=>{
 const home=await mkdtemp(join(tmpdir(),'direct-plugin-'));
 try{
  const old=join(home,'1.0.0-old'),current=join(home,'1.0.0-current');
  await mkdir(join(old,'.codex-plugin'),{recursive:true});await mkdir(join(current,'.codex-plugin'),{recursive:true});
  await writeFile(join(old,'.codex-plugin','plugin.json'),JSON.stringify({name:'codex-agents-workflow',version:'1.0.0-old'}));
  await writeFile(join(current,'.codex-plugin','plugin.json'),JSON.stringify({name:'codex-agents-workflow',version:'1.0.0-current'}));
  let calls=0;const released=[];
  const result=await installLocal({install:async()=>{calls++;},cacheRoot:home,currentVersion:'1.0.0-current',release:async version=>{
   released.push(version);return version==='1.0.0-current'?[201,202]:[101,102];
  }});
  assert.equal(calls,1);assert.deepEqual(result,{installed:true,retained_versions:[],removed_versions:['1.0.0-old'],released_processes:[{version:'1.0.0-current',count:2},{version:'1.0.0-old',count:2}]});
  assert.deepEqual(released,['1.0.0-current','1.0.0-old']);
  assert.deepEqual(await readdir(home),['1.0.0-current']);
 }finally{assert(home.startsWith(resolve(tmpdir())));await rm(home,{recursive:true});}
});

test('installation failure is exposed without automatic restore or retry',async()=>{
 const error=new Error('CLI failed');let calls=0;
 await assert.rejects(installLocal({install:async()=>{calls++;throw error;},release:async()=>[]}),e=>e===error);
 assert.equal(calls,1);
});
