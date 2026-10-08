import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, readFile, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from './physical-tempdir.mjs';
import { join, resolve } from 'node:path';
import { createDraft } from '../lib/workflow-schema.mjs';
import { WorkflowStore } from '../lib/workflow-store.mjs';
import { resolveWorkflowPins, validateSkillReference } from '../lib/workflow-pins.mjs';
import { digest } from '../lib/workflow-revisions.mjs';

async function fixture(t) {
  const root = await mkdtemp(join(tmpdir(), 'workflow-pins-'));
  t.after(async () => { assert(resolve(root).startsWith(resolve(tmpdir()))); await rm(root, { recursive: true, maxRetries: 3, retryDelay: 100 }); });
  const store = await new WorkflowStore(join(root, 'packs')).initialize();
  const source = join(root, 'skill'); await mkdir(source);
  const text = '---\nname: pinned\ndescription: Pinned test\nversion: "1"\n---\nApply the task.';
  await writeFile(join(source, 'SKILL.md'), text); await writeFile(join(source, 'guide.txt'), 'Stable resource');
  return { root, store, source, reference: { path: join(source, 'SKILL.md'), name: 'pinned', source_hash: digest(text), expected_version: '1', allowed_nested_skills: [] } };
}

test('closure pins entire child revisions, linked Skill resources and all Provider identities before a Run', async t => {
  const f = await fixture(t);
  const child = await f.store.create({ ...createDraft('child', 'Child'), nodes: [{ id: 'linked', type: 'skill_ref', skill_ref: f.reference, executor: { kind: 'provider', provider_id: 'child-provider' } }] }, { resources: { 'child.txt': 'Old child bytes' } });
  const root = await f.store.create({ ...createDraft('parent', 'Parent'), nodes: [{ id: 'nested', type: 'subworkflow', subworkflow: { workflow_id: 'child', revision_pin: child.revision_hash } }, { id: 'own', type: 'agent', executor: { kind: 'provider', provider_id: 'parent-provider' } }] });
  await f.store.save('child', { ...child.workflow, name: 'Changed child' }, { expected_revision: child.revision_hash, resources: { 'child.txt': 'Changed child bytes' } });
  const closure = await resolveWorkflowPins(f.store, root);
  assert.equal(closure.children['child@' + child.revision_hash].workflow.name, 'Child');
  assert.deepEqual(closure.provider_ids.sort(), ['child-provider', 'parent-provider']); assert.equal(closure.skills.length, 1);
  assert(closure.skills[0].resources.some(resource => resource.path === 'guide.txt' && resource.sha256 === digest('Stable resource')));
  await rm(f.source, { recursive: true }); assert.equal(closure.blobs.get(digest('Stable resource')).toString(), 'Stable resource');
  assert.equal(closure.blobs.get(digest('Old child bytes')).toString(), 'Old child bytes');
});

test('linked source changes, unpinned nested Skills and recursive Workflow identities fail before pin publication', async t => {
  const f = await fixture(t);
  const pack = await f.store.create({ ...createDraft('parent', 'Parent'), nodes: [{ id: 'linked', type: 'skill_ref', skill_ref: f.reference }] });
  await writeFile(f.reference.path, (await readFile(f.reference.path, 'utf8')) + '\nChanged');
  await assert.rejects(resolveWorkflowPins(f.store, pack), { code: 'SKILL_SOURCE_CHANGED' });
  assert.throws(() => validateSkillReference({ ...f.reference, allowed_nested_skills: [f.reference.path] }), { code: 'SKILL_NESTED_REFERENCE' });
  const recursive = await f.store.save('parent', { ...pack.workflow, nodes: [{ id: 'self', type: 'subworkflow', subworkflow: { workflow_id: 'parent', revision_pin: pack.revision_hash } }] }, { expected_revision: pack.revision_hash });
  await assert.rejects(resolveWorkflowPins(f.store, recursive), { code: 'SUBWORKFLOW_CYCLE' });
});

test('a cached child is rechecked when reached under a different ancestor revision', async t => {
  const f = await fixture(t);
  const call = (id, pack) => ({ id, type: 'subworkflow', subworkflow: { workflow_id: pack.workflow.id, revision_pin: pack.revision_hash } });
  const older = await f.store.create(createDraft('ancestor', 'Older ancestor'));
  const shared = await f.store.create({ ...createDraft('shared', 'Shared child'), nodes: [call('old-ancestor', older)] });
  const newer = await f.store.save('ancestor', { ...older.workflow, nodes: [call('shared', shared)] }, { expected_revision: older.revision_hash });
  const root = await f.store.create({ ...createDraft('root', 'Root'), nodes: [call('first-visit', shared), call('second-visit', newer)] });
  await assert.rejects(resolveWorkflowPins(f.store, root), { code: 'SUBWORKFLOW_CYCLE' });
});

test('legacy Role metadata is inert and never enters a Workflow Run closure',async t=>{
  const f=await fixture(t);
  const root=await f.store.create({...createDraft('role-parent','Role parent'),nodes:[{id:'worker',type:'agent',role_ref:{id:'builtin-role-bounded-code-change'},executor:{kind:'provider',provider_id:'native-luna'}}]});
  const closure=await resolveWorkflowPins(f.store,root);
  assert.equal(Object.hasOwn(closure,'roles'),false);
  assert.equal(Object.hasOwn(closure.context,'roles'),false);
});
