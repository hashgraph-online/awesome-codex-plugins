import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,mkdir,writeFile,readFile,rm,lstat} from 'node:fs/promises';
import {join,resolve} from 'node:path';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {tmpdir} from './physical-tempdir.mjs';
import {WorkflowStore} from '../lib/workflow-store.mjs';
import {createDraft} from '../lib/workflow-schema.mjs';
import {cleanupCaches,pluginCachePlan,pluginInventory} from '../lib/cache-cleanup.mjs';
async function fixture(t) {
  const root=await mkdtemp(join(tmpdir(),'workflow-cache-'));
  t.after(async()=>{assert(resolve(root).startsWith(resolve(tmpdir())));await rm(root,{recursive:true,force:true});});
  const store=await new WorkflowStore(join(root,'workflows')).initialize();
  const writer=await new WorkflowStore(join(root,'runs')).initialize();
  const pins=[];
  const runs={writer,list:async()=>pins.map((_,i)=>({run_id:String(i)})),read:async id=>({pins:pins[Number(id)]})};
  const home=join(root,'home');await mkdir(home);await writeFile(join(home,'config.toml'),'');
  const pluginRoot=join(home,'plugins/cache/codex-agents-workflow/codex-agents-workflow');
  for(const version of ['0.8.0+old','0.8.0+active','0.8.0+current']) {
    await mkdir(join(pluginRoot,version,'.codex-plugin'),{recursive:true});
    await writeFile(join(pluginRoot,version,'.codex-plugin/plugin.json'),JSON.stringify({name:'codex-agents-workflow',version}));
    await writeFile(join(pluginRoot,version,'source.txt'),'plugin source');
  }
  return {store,runs,pins,home,auditRoot:root,pluginRoot,inventory:async()=>({installed:['0.8.0+current'],active:['0.8.0+active']})};
}
test('cleanup removes only unreferenced history/blobs and inactive plugin versions, with durable evidence',async t=>{
  const f=await fixture(t);
  const old=await f.store.create(createDraft('sample','old'),{resources:{'a.txt':'unused'}});
  const pinned=await f.store.save('sample',{...old.workflow,name:'pinned'},{expected_revision:old.revision_hash,resources:{'a.txt':'run resource'}});
  const current=await f.store.save('sample',{...old.workflow,name:'current'},{expected_revision:pinned.revision_hash,resources:{'a.txt':'current resource'}});
  f.pins.push({root:pinned});
  const preview=await cleanupCaches({...f,preview:true});
  assert.equal(preview.workflow_revisions,1);assert.equal(preview.workflow_resources,1);assert.equal(preview.plugin_versions,1);
  await f.store.snapshot('sample',old.revision_hash);
  const result=await cleanupCaches(f);
  assert.equal(result.bytes,preview.bytes);
  await assert.rejects(f.store.snapshot('sample',old.revision_hash),{code:'ENOENT'});
  assert.equal((await f.store.snapshot('sample')).revision_hash,current.revision_hash);
  assert.equal((await f.store.resources('sample',pinned.revision_hash))['a.txt'].toString(),'run resource');
  await assert.rejects(lstat(join(f.pluginRoot,'0.8.0+old')),{code:'ENOENT'});
  await lstat(join(f.pluginRoot,'0.8.0+active'));await lstat(join(f.pluginRoot,'0.8.0+current'));
  const audit=JSON.parse(await readFile(result.audit_file,'utf8'));assert.equal(audit.status,'complete');assert.equal(audit.deleted.length,3);
  assert.equal((await cleanupCaches({...f,preview:true})).bytes,0);
});
test('retained provenance pins preserve referenced historical revisions transitively',async t=>{
  const f=await fixture(t);
  const child=await f.store.create(createDraft('child','child'),{resources:{'a':'child'}});
  const middle=await f.store.create(createDraft('middle','middle'),{provenance:{source_revision:child.revision_hash}});
  await f.store.save('child',{...child.workflow,name:'new child'},{expected_revision:child.revision_hash});
  await f.store.save('middle',{...middle.workflow,name:'new middle'},{expected_revision:middle.revision_hash,provenance:{}});
  await f.store.create(createDraft('parent','parent'),{provenance:{source_revision:middle.revision_hash}});
  assert.equal((await cleanupCaches({...f,preview:true})).workflow_revisions,0);
});
test('plugin identity and changing active-process protections fail visibly before deleting the protected version',async t=>{
  const f=await fixture(t);let count=0;
  await assert.rejects(cleanupCaches({...f,inventory:async()=>({installed:['0.8.0+current'],active:++count===1?['0.8.0+active']:['0.8.0+active','0.8.0+old']})}),{code:'CACHE_CHANGED'});
  await lstat(join(f.pluginRoot,'0.8.0+old'));
  await writeFile(join(f.pluginRoot,'0.8.0+old/.codex-plugin/plugin.json'),JSON.stringify({name:'another-plugin',version:'0.8.0+old'}));
  await assert.rejects(pluginCachePlan(f.home,{inventory:f.inventory}),{code:'CACHE_PLUGIN_ID'});
});
test('cleanup handles orphaned plugin-cache revisions without manifests while retaining active revisions',async t=>{
  const f=await fixture(t);
  const empty=join(f.pluginRoot,'0.8.0+empty');
  const partial=join(f.pluginRoot,'0.8.0+partial');
  await mkdir(empty);
  await mkdir(partial);
  await writeFile(join(partial,'partial.txt'),'interrupted install');
  await rm(join(f.pluginRoot,'0.8.0+active/.codex-plugin/plugin.json'));
  const preview=await cleanupCaches({...f,preview:true});
  assert.equal(preview.plugin_versions,3);
  assert.deepEqual(preview.incomplete_plugin_versions,['0.8.0+empty','0.8.0+partial']);
  const result=await cleanupCaches(f);
  assert.equal(result.plugin_versions,preview.plugin_versions);
  await assert.rejects(lstat(empty),{code:'ENOENT'});
  await assert.rejects(lstat(partial),{code:'ENOENT'});
  await lstat(join(f.pluginRoot,'0.8.0+active'));
  await lstat(join(f.pluginRoot,'0.8.0+current'));
});
test('busy plugin cache is reported as deferred after other history is cleaned',async t=>{
  const f=await fixture(t);
  const old=await f.store.create(createDraft('sample','old'));
  await f.store.save('sample',{...old.workflow,name:'current'},{expected_revision:old.revision_hash});
  const busy=join(f.pluginRoot,'0.8.0+old');
  const result=await cleanupCaches({...f,removePluginDirectory:async(path,options)=>{
    if(path===busy)throw Object.assign(new Error('directory in use'),{code:'EBUSY'});
    return rm(path,options);
  }});
  assert.equal(result.workflow_revisions,1);
  assert.equal(result.plugin_versions,0);
  assert.deepEqual(result.deferred_plugin_versions,['0.8.0+old']);
  assert(result.retained_plugin_versions.includes('0.8.0+old'));
  await assert.rejects(f.store.snapshot('sample',old.revision_hash),{code:'ENOENT'});
  await lstat(busy);
  const audit=JSON.parse(await readFile(result.audit_file,'utf8'));
  assert.equal(audit.status,'partial');
  assert.equal(audit.deleted.length,1);
  assert.deepEqual(audit.deferred.map(item=>item.version),['0.8.0+old']);
});

for(const platform of ['linux','darwin'])test(`${platform} plugin inventory retains installed, active and host-pinned versions without exposing commands`,async t=>{
  const f=await fixture(t),calls=[];
  const started='Tue Sep 29 10:00:00 2026',stamp=new Date(started).toISOString();
  await mkdir(join(f.home,'codex-agents-workflow'));
  await writeFile(join(f.home,'codex-agents-workflow/runtime-retention.json'),JSON.stringify({versions:{'0.8.0+old':[{pid:987,started_at:stamp}]}}));
  const state=await pluginInventory(f.pluginRoot,process.env,{platform,execImpl:async(program,args)=>{
    calls.push({program,args});
    if(program==='codex')return {stdout:JSON.stringify({installed:[{pluginId:'codex-agents-workflow@codex-agents-workflow',version:'0.8.0+current'}]})};
    assert.equal(program,'ps');
    return {stdout:`123 ${started} node ${join(f.pluginRoot,'0.8.0+active')}/control-plane/server.mjs --secret=never-return\n987 ${started} /usr/local/bin/codex app-server --stdio\n`};
  }});
  assert.deepEqual(state.installed,['0.8.0+current']);
  assert.deepEqual(state.active,['0.8.0+active','0.8.0+old']);
  assert.deepEqual(state.hosts,[{pid:987,started_at:stamp}]);
  assert.equal(JSON.stringify(state).includes('secret'),false);
  assert.deepEqual(calls.map(row=>row.program),['codex','ps']);
});

test('portable inventory refuses malformed process evidence and validates real POSIX ps output',async t=>{
  const f=await fixture(t),registry={stdout:JSON.stringify({installed:[{pluginId:'codex-agents-workflow@codex-agents-workflow',version:'0.8.0+current'}]})};
  await assert.rejects(pluginInventory(f.pluginRoot,process.env,{platform:'linux',execImpl:async program=>program==='codex'?registry:{stdout:'123 incomplete process row'}}),{code:'CACHE_PROCESS_SCHEMA'});
  if(process.platform==='win32')return;
  const exec=promisify(execFile);
  const state=await pluginInventory(f.pluginRoot,process.env,{execImpl:(program,args,options)=>program==='codex'?Promise.resolve(registry):exec(program,args,options)});
  assert.deepEqual(state.installed,['0.8.0+current']);
  assert(Array.isArray(state.active)&&Array.isArray(state.hosts));
});
