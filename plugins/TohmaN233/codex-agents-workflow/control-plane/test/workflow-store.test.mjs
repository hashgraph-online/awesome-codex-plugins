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
