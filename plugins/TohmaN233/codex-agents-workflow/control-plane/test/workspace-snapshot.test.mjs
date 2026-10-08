import test from 'node:test';
import assert from 'node:assert/strict';
import * as fs from 'node:fs/promises';
import {join,resolve} from 'node:path';
import {tmpdir} from './physical-tempdir.mjs';
import {snapshotWorkspace,changedWorkspacePaths} from '../lib/execution/workspace-snapshot.mjs';

async function fixture(t,kind='directory') {
  const root=await fs.mkdtemp(join(tmpdir(),'scope-private-'));
  t.after(()=>fs.rm(root,{recursive:true,force:true}));
  await fs.mkdir(join(root,'allowed'));
  const target=join(root,'allowed','private');
  if(kind==='directory')await fs.mkdir(target);else await fs.writeFile(target,'private data');
  await fs.writeFile(join(root,'allowed','result.txt'),'result');
  const error=Object.assign(new Error('private ACL'),{code:'EPERM'});
  const method=kind==='directory'?'readdir':'readFile';
  const fileSystem={...fs,[method]:async(path,...args)=>{
    if(resolve(path)===resolve(target))throw error;
    return fs[method](path,...args);
  }};
  return {root,error,fileSystem};
}

for(const kind of ['directory','file']) {
  test(`authorized unreadable ${kind} has explicit boundary evidence, never a fabricated hash`,async t=>{
    const f=await fixture(t,kind),events=[];
    const before=await snapshotWorkspace(f.root);
    const after=await snapshotWorkspace(f.root,{fileSystem:f.fileSystem,access:'bounded_write',allowedPaths:['allowed'],onUnreadable:e=>events.push(e)});
    assert.equal(events.length,1);assert.equal(events[0].path,'allowed/private');
    assert.equal(events[0].coverage,'authorized_boundary_only');assert.equal(events[0].kind,kind);
    assert(!after.has('allowed/private'));assert(after.has('allowed/result.txt'));
    assert.deepEqual(changedWorkspacePaths(before,after),['allowed/private']);
    assert.equal(after.unreadablePaths.get('allowed/private').error_code,'EPERM');
  });
  test(`unreadable ${kind} is fatal for read-only, outside scope, or required artifacts`,async t=>{
    const f=await fixture(t,kind);
    for(const options of [
      {access:'read_only',allowedPaths:['allowed']},
      {access:'bounded_write',allowedPaths:['another']},
      {access:'bounded_write',allowedPaths:['allowed'],requiredPaths:[kind==='directory'?'allowed/private/result.json':'allowed/private']},
    ])await assert.rejects(snapshotWorkspace(f.root,{fileSystem:f.fileSystem,onUnreadable:()=>assert.fail('must not exempt required evidence'),...options}),error=>error===f.error);
  });
}
test('unreadable scope evidence must be persisted; no callback or failed persistence fails',async t=>{
  const f=await fixture(t);
  const options={fileSystem:f.fileSystem,access:'bounded_write',allowedPaths:['allowed']};
  await assert.rejects(snapshotWorkspace(f.root,options),error=>error===f.error);
  await assert.rejects(snapshotWorkspace(f.root,{...options,onUnreadable:()=>{throw new Error('audit unavailable');}}),/audit unavailable/);
});
test('unrelated IO errors remain fatal inside an authorized directory',async t=>{
  const f=await fixture(t);f.error.code='EIO';
  await assert.rejects(snapshotWorkspace(f.root,{fileSystem:f.fileSystem,access:'bounded_write',allowedPaths:['allowed'],onUnreadable:()=>assert.fail('not a permission observation')}),error=>error===f.error);
});
test('root directory failure cannot become an authorized opaque subtree',async t=>{
  const f=await fixture(t);
  await assert.rejects(snapshotWorkspace(f.root,{fileSystem:{...fs,readdir:async()=>{throw f.error;}},access:'bounded_write',allowedPaths:['.'],onUnreadable:()=>assert.fail('root must remain inspectable')}),error=>error===f.error);
});
