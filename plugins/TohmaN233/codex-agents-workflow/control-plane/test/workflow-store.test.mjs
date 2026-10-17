import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, readFile, writeFile, rm, symlink, readdir } from 'node:fs/promises';
import { tmpdir } from './physical-tempdir.mjs';
import { join, resolve } from 'node:path';
import { fork } from 'node:child_process';
import { WorkflowStore } from '../lib/workflow-store.mjs';
import { createDraft } from '../lib/workflow-schema.mjs';
import { canonicalJSON, digest, LIMITS } from '../lib/workflow-revisions.mjs';
import { packDirectory } from '../lib/workflow-paths.mjs';
import {migrateStoredWorkflowProviderIds} from '../lib/workflow-provider-identity.mjs';
import {migrateStoredWorkflowHostToolIdentities} from '../lib/workflow-host-tool-identity.mjs';
import {workflowResourceProgramIdentity} from '../lib/execution/workflow-resource-program.mjs';

async function fixture(t) {
  const parent = await mkdtemp(join(tmpdir(), 'sol-workflow-store-'));
  t.after(async () => { assert(resolve(parent).startsWith(resolve(tmpdir()) + '/'.replace('/', process.platform === 'win32' ? '\\' : '/'))); await rm(parent, { recursive: true, maxRetries: 3, retryDelay: 100 }); });
  const store = await new WorkflowStore(join(parent, 'workflows')).initialize();
  return { parent, store };
}

test('whole revision pins resource bytes and old revisions survive save, clone, rename and restore', async t => {
  const { store } = await fixture(t);
  const first = await store.create(createDraft('example', 'First'), { resources: { 'scripts/check.mjs': 'v1' }, provenance: { source: 'fixture' } });
  const second = await store.save('example', { ...first.workflow, name: 'Second' }, { expected_revision: first.revision_hash, resources: { 'scripts/check.mjs': 'v2' } });
  assert.notEqual(second.revision_hash, first.revision_hash);
  assert.equal((await store.resources('example', first.revision_hash))['scripts/check.mjs'].toString(), 'v1');
  assert.equal((await store.resources('example'))['scripts/check.mjs'].toString(), 'v2');
  const copy = await store.duplicate('example', 'con', 'Windows-reserved legacy ID', first.revision_hash);
  assert.equal(copy.workflow.id, 'con');
  assert.equal(copy.workflow.revision, 1);
  assert.equal((await store.resources('con'))['scripts/check.mjs'].toString(), 'v1');
  const renamed = await store.rename('example', 'Renamed', second.revision_hash);
  assert.equal(renamed.workflow.revision, 3);
  const restored = await store.restore('example', first.revision_hash, renamed.revision_hash);
  assert.equal(restored.workflow.name, 'First');
  assert.equal(restored.workflow.revision, 4);
  assert.equal((await store.resources('example'))['scripts/check.mjs'].toString(), 'v1');
  assert.deepEqual((await store.list()).map(item => item.workflow.id), ['con', 'example']);
});

test('competing creation and stale saves cannot clobber the winner', async t => {
  const { store } = await fixture(t);
  const other = new WorkflowStore(store.root);
  const results = await Promise.allSettled([store.create(createDraft('same', 'A')), other.create(createDraft('same', 'B'))]);
  assert.equal(results.filter(result => result.status === 'fulfilled').length, 1);
  assert.equal(results.filter(result => result.status === 'rejected').length, 1);
  const first = await store.snapshot('same');
  const next = await store.rename('same', 'Next', first.revision_hash);
  await assert.rejects(store.save('same', { ...first.workflow, name: 'Lost' }, { expected_revision: first.revision_hash }), { code: 'REVISION_CONFLICT' });
  assert.equal((await store.snapshot('same')).revision_hash, next.revision_hash);
});

test('corrupt heads, immutable revisions and resources fail closed', async t => {
  const { store } = await fixture(t);
  const created = await store.create(createDraft('bad', 'Original'), { resources: { 'readme.txt': 'original' } });
  const pack = packDirectory(store.root, 'bad');
  const head = join(pack, 'workflow.json');
  const bytes = await readFile(head);
  await writeFile(head, '{broken');
  await assert.rejects(store.snapshot('bad'), SyntaxError);
  await writeFile(head, bytes);
  await writeFile(join(pack, 'objects', created.resources[0].sha256), 'tampered');
  await assert.rejects(store.snapshot('bad'), { code: 'RESOURCE_CORRUPT' });
  await writeFile(join(pack, 'objects', created.resources[0].sha256), 'original');
  const altered = JSON.parse(bytes); altered.workflow.name = 'tampered';
  await writeFile(head, JSON.stringify(altered));
  await assert.rejects(store.snapshot('bad'), { code: 'REVISION_CORRUPT' });
  assert.equal((await store.snapshot('bad', created.revision_hash)).workflow.name, 'Original');
});

test('metadata candidate scans validate complete definitions without auditing unrelated object bytes', async t => {
  const {store}=await fixture(t);
  const created=await store.create(createDraft('metadata','Metadata'),{resources:{'source.txt':'original'}});
  const pack=packDirectory(store.root,'metadata');
  await writeFile(join(pack,'objects',created.resources[0].sha256),'corrupt');
  assert.deepEqual(await store.metadata('metadata'),created);
  assert.deepEqual(await store.listMetadata(),[created]);
  assert.deepEqual(await store.metadata('metadata',created.revision_hash),created);
  await assert.rejects(store.snapshot('metadata'),{code:'RESOURCE_CORRUPT'});
  await assert.rejects(store.list(),{code:'RESOURCE_CORRUPT'});
  const altered=structuredClone(created);altered.workflow.name='changed';
  await writeFile(join(pack,'workflow.json'),JSON.stringify(altered));
  await assert.rejects(store.listMetadata(),{code:'REVISION_CORRUPT'});
  await writeFile(join(pack,'workflow.json'),'{invalid');
  await assert.rejects(store.metadata('metadata'),SyntaxError);
});

test('startup snapshot returns the same verified object bytes from one observable read',async t=>{
  const {store}=await fixture(t);
  const created=await store.create(createDraft('startup-scan','Startup scan'),{resources:{'source.txt':'trusted bytes'}});
  const load=store.snapshotWithResources.bind(store),snapshot=store.snapshot.bind(store),resources=store.resources.bind(store);
  let legacyReads=0;
  store.snapshot=async(...args)=>{legacyReads++;return snapshot(...args);};
  store.resources=async(...args)=>{legacyReads++;return resources(...args);};
  const result=await load('startup-scan',created.revision_hash);
  assert.deepEqual(result.snapshot,created);
  assert.equal(result.resources['source.txt'].toString(),'trusted bytes');
  assert.equal(result.resource_scan.resource_count,1);
  assert.equal(result.resource_scan.object_read_count,1);
  assert.equal(result.resource_scan.verified_resource_bytes,Buffer.byteLength('trusted bytes'));
  assert(Number.isFinite(result.resource_scan.elapsed_ms)&&result.resource_scan.elapsed_ms>=0);
  assert.equal(legacyReads,0);

  await writeFile(join(packDirectory(store.root,'startup-scan'),'objects',created.resources[0].sha256),'changed bytes');
  const diagnostics=[],writeLog=console.error;
  console.error=message=>diagnostics.push(String(message));
  try{await assert.rejects(load('startup-scan',created.revision_hash),{code:'RESOURCE_CORRUPT'});}
  finally{console.error=writeLog;}
  const failure=JSON.parse(diagnostics.at(-1).replace(/^\[workflow-resource-scan\] /,''));
  assert.equal(failure.status,'failed');
  assert.equal(failure.error_code,'RESOURCE_CORRUPT');
  assert.equal(failure.resource_count,1);
  assert.equal(failure.object_read_count,1);
});

test('metadata scans refuse linked packs, invalid manifests and unknown store entries',async t=>{
  const {parent,store}=await fixture(t);
  const outside=join(parent,'outside');await mkdir(outside);
  await symlink(outside,packDirectory(store.root,'linked'),process.platform==='win32'?'junction':'dir');
  await assert.rejects(store.listMetadata(),{code:'UNKNOWN_STORE_ENTRY'});
  await assert.rejects(store.metadata('linked'),{code:'WORKFLOW_SYMLINK'});
  await rm(packDirectory(store.root,'linked'));
  const created=await store.create(createDraft('invalid-manifest','Manifest'));
  const document=structuredClone(created);document.resources=[{path:'../escape',sha256:'a'.repeat(64),bytes:1}];
  const {revision_hash,...snapshot}=document;document.revision_hash=digest(canonicalJSON(snapshot));
  await writeFile(join(packDirectory(store.root,'invalid-manifest'),'workflow.json'),JSON.stringify(document));
  await assert.rejects(store.listMetadata());
  await writeFile(join(store.root,'unexpected.txt'),'x');
  await assert.rejects(store.listMetadata());
});

test('migration scans skip unrelated object bytes but fully audit selected candidates and preserve CAS',async t=>{
  const {store}=await fixture(t);
  const unrelated=await store.create(createDraft('unrelated','Unrelated'),{resources:{'source.txt':'original'}});
  await writeFile(join(packDirectory(store.root,'unrelated'),'objects',unrelated.resources[0].sha256),'corrupt');
  const workflow=createDraft('old-provider','Old provider');workflow.requirements.providers=['native-terra'];
  const candidate=await store.create(workflow,{resources:{'candidate.txt':'candidate'}});
  assert.equal((await migrateStoredWorkflowProviderIds(store)).length,1);
  const migrated=await store.snapshot(candidate.workflow.id);
  assert.deepEqual(migrated.workflow.requirements.providers,['native-sol']);
  await assert.rejects(store.list(),{code:'RESOURCE_CORRUPT'});
  const bad=createDraft('bad-provider','Bad provider');bad.requirements.providers=['native-terra'];
  const badPack=await store.create(bad,{resources:{'candidate.txt':'candidate'}});
  await writeFile(join(packDirectory(store.root,bad.id),'objects',badPack.resources[0].sha256),'corrupt');
  await assert.rejects(migrateStoredWorkflowProviderIds(store),{code:'RESOURCE_CORRUPT'});
  await writeFile(join(packDirectory(store.root,bad.id),'objects',badPack.resources[0].sha256),'candidate');
  const originalSave=store.save.bind(store);
  store.save=async(id,next,options)=>{
    const current=await store.snapshot(id);
    await originalSave(id,{...current.workflow,name:'Concurrent change'},{expected_revision:options.expected_revision});
    return originalSave(id,next,options);
  };
  await assert.rejects(migrateStoredWorkflowProviderIds(store),{code:'REVISION_CONFLICT'});
});

test('Host migration candidates retain full resource validation even for unsupported identities',async t=>{
  const {store}=await fixture(t);
  const unrelated=await store.create(createDraft('unrelated-host','Unrelated'),{resources:{'source.txt':'original'}});
  await writeFile(join(packDirectory(store.root,unrelated.workflow.id),'objects',unrelated.resources[0].sha256),'corrupt');
  assert.deepEqual(await migrateStoredWorkflowHostToolIdentities(store),[]);
  const workflow=createDraft('unknown-host','Unknown Host');
  workflow.host_tools=[{id:'unknown',identity:{...workflowResourceProgramIdentity(),sha256:'f'.repeat(64)},argv:['node','scripts/check.mjs','work'],
    input_schema:{type:'object'},output_schema:{type:'object'},env_allow:[],permissions:{network:false,read_paths:[],write_paths:['work']},
    output_cap_bytes:4096,deadline_ms:10000,idempotency:{mode:'safe'}}];
  const candidate=await store.create(workflow,{resources:{'scripts/check.mjs':'original'}});
  await writeFile(join(packDirectory(store.root,workflow.id),'objects',candidate.resources[0].sha256),'corrupt');
  await assert.rejects(migrateStoredWorkflowHostToolIdentities(store),{code:'RESOURCE_CORRUPT'});
});

test('unsafe resource paths, collision and size limit fail before any pack is published', async t => {
  const { store } = await fixture(t);
  for (const resources of [
    { '../escape': 'x' }, { '/absolute': 'x' }, { 'a\\b': 'x' }, { 'NUL.txt': 'x' },
    { 'a.txt': 'x', 'A.txt': 'y' }, { a: 'x', 'a/b': 'y' }, { huge: Buffer.alloc(LIMITS.resource + 1) },
  ]) await assert.rejects(store.create(createDraft('invalid', 'Invalid'), { resources }));
  await assert.rejects(store.create({ ...createDraft('valid', 'Valid'), id: '../bad' }), { code: 'INVALID_WORKFLOW_ID' });
  assert.deepEqual(await store.list(), []);
  assert.deepEqual(await readdir(join(store.root, '.pending')), []);
});

test('linked store packs and linked object files are refused', async t => {
  const { parent, store } = await fixture(t);
  const outside = join(parent, 'outside'); await mkdir(outside);
  await symlink(outside, packDirectory(store.root, 'linked'), process.platform === 'win32' ? 'junction' : 'dir');
  await assert.rejects(store.snapshot('linked'), { code: 'WORKFLOW_SYMLINK' });
  const created = await store.create(createDraft('regular', 'Regular'), { resources: { 'source.txt': 'value' } });
  const objects = join(packDirectory(store.root, 'regular'), 'objects');
  const object = join(objects, created.resources[0].sha256);
  await rm(object);
  // Directory junctions need no Windows Developer Mode and are still invalid objects.
  await symlink(outside, object, process.platform === 'win32' ? 'junction' : 'dir');
  await assert.rejects(store.snapshot('regular'), { code: 'WORKFLOW_SYMLINK' });
});

test('failed save leaves the head intact and an interrupted immutable write can be retried', async t => {
  const { store } = await fixture(t);
  const first = await store.create(createDraft('safe', 'Before'));
  const pack = packDirectory(store.root, 'safe');
  const snapshot = { workflow: { ...first.workflow, name: 'After', revision: 2 }, resources: [], provenance: {}, import_report: {} };
  const hash = digest(canonicalJSON(snapshot));
  // Simulate a process stopping after its immutable revision was fsynced but before head publication.
  await writeFile(join(pack, 'revisions', hash + '.json'), canonicalJSON(snapshot));
  const next = await store.save('safe', { ...first.workflow, name: 'After' }, { expected_revision: first.revision_hash });
  assert.equal(next.revision_hash, hash);
  await assert.rejects(store.save('safe', { ...next.workflow, name: '' }, { expected_revision: next.revision_hash }), { code: 'WORKFLOW_NAME' });
  assert.equal((await store.snapshot('safe')).revision_hash, hash);
});

test('delete is compare-and-swap and retains the full pack for recovery', async t => {
  const { store } = await fixture(t);
  const created = await store.create(createDraft('remove', 'Remove'));
  await assert.rejects(store.delete('remove', 'stale'), { code: 'REVISION_CONFLICT' });
  const removed = await store.delete('remove', created.revision_hash);
  assert(removed.retained_at.startsWith(join(store.root, '.trash')));
  assert.equal(JSON.parse(await readFile(join(removed.retained_at, 'workflow.json'))).revision_hash, created.revision_hash);
  assert.deepEqual(await store.list(), []);
});

test('Draft can be incomplete; Ready cannot bypass validator; JSON rejects sparse or non-JSON values', async t => {
  const { store } = await fixture(t);
  await store.create(createDraft('draft', 'Draft'));
  await assert.rejects(store.create({ ...createDraft('ready', 'Ready'), status: 'ready' }), { code: 'WORKFLOW_NOT_READY' });
  assert.throws(() => canonicalJSON([, 1]), { code: 'INVALID_JSON' });
  assert.throws(() => canonicalJSON({ n: NaN }), { code: 'INVALID_JSON' });
  assert.throws(() => canonicalJSON({ n: undefined }), { code: 'INVALID_JSON' });
});

test('crashed writer requires inspected identity; live writers cannot be taken over', async t => {
  const { store } = await fixture(t);
  const child = fork(new URL('./fixtures/hold-workflow-lock.mjs', import.meta.url), [store.root], { stdio: ['ignore', 'ignore', 'ignore', 'ipc'], windowsHide: true });
  const closed = new Promise(ok => child.once('close', ok));
  let timer;
  try {
    await Promise.race([
      new Promise((ok, no) => { child.once('message', message => message.locked ? ok() : no(new Error('Unexpected child message'))); child.once('error', no); }),
      new Promise((_, no) => { timer = setTimeout(() => no(new Error('Child lock deadline')), 5000); }),
    ]);
    clearTimeout(timer);
    const owner = await store.inspectWriter(); assert.equal(owner.pid, child.pid);
    await assert.rejects(store.recoverWriter('wrong-token'), { code: 'LOCK_OWNERSHIP' });
    await assert.rejects(store.recoverWriter(owner.token), { code: 'WRITER_ACTIVE' });
    child.kill(); await closed;
    const recoveries = await Promise.allSettled([store.recoverWriter(owner.token), store.recoverWriter(owner.token)]);
    assert.equal(recoveries.filter(result => result.status === 'fulfilled').length, 1);
    await store.create(createDraft('after-crash', 'Recovered'));
    assert.equal(await store.inspectWriter(), null);
  } finally { clearTimeout(timer); if (child.exitCode === null && child.signalCode === null) child.kill(); await closed; }
});
