import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile, writeFile, mkdtemp, rm, readdir } from 'node:fs/promises';
import { join, relative, isAbsolute } from 'node:path';
import { tmpdir } from './physical-tempdir.mjs';
import { fileURLToPath } from 'node:url';
import { prepareV6Migration, migrateV6OnDisk, restoreV6Backup } from '../lib/workflow-migration-v6.mjs';
import { digest } from '../lib/workflow-revisions.mjs';
import { WorkflowStore } from '../lib/workflow-store.mjs';
import { validateWorkflowGraph } from '../lib/workflow-validator.mjs';

const bundled = JSON.parse(await readFile(fileURLToPath(new URL('../default-config.json', import.meta.url)), 'utf8'));
async function fixture(t, raw = structuredClone(bundled)) {
  const root = await mkdtemp(join(tmpdir(), 'sol-workflow-migration-'));
  t.after(async () => { const rel = relative(tmpdir(), root); assert(rel && !rel.startsWith('..') && !isAbsolute(rel)); await rm(root, { recursive: true, maxRetries: 3, retryDelay: 100 }); });
  const configPath = join(root, 'control-plane.json');
  const bytes = JSON.stringify(raw, null, 2) + '\n'; await writeFile(configPath, bytes);
  return { root, configPath, bytes, raw };
}

test('every builtin Task Type keeps its ID, route semantics, templates, bindings and approval', () => {
  const { config, workflows, mappings } = prepareV6Migration(bundled);
  assert.equal(workflows.length, bundled.task_types.length);
  for (const taskType of config.task_types) {
    const workflow = workflows.find(item => item.id === taskType.id);
    assert.equal(workflow.name, taskType.name); assert.equal(workflow.enabled, taskType.enabled);
    assert.deepEqual(workflow.tags, taskType.tags); assert.equal(workflow.description, taskType.description);
    assert.equal(mappings[taskType.id].route, taskType.route);
    const checked = validateWorkflowGraph(workflow, { providers: config.providers }); assert.equal(checked.valid, true, JSON.stringify(checked.errors));
    for (const stage of taskType.stages) {
      const node = workflow.nodes.find(item => item.id === stage.id);
      assert.equal(node.executor.provider_id, stage.provider_id); assert.equal(node.role, stage.role);
      assert.equal(node.access, stage.access); assert.equal(node.approval.required, stage.requires_user_approval);
      assert.equal(node.prompt_template, bundled.task_types.find(item => item.id === taskType.id).stages.find(item => item.id === stage.id).template);
      if (stage.access === 'bounded_write') assert.deepEqual(node.path_scope, { binding: 'run.allowed_paths' });
    }
    if (!taskType.stages.length) assert.deepEqual(workflow.nodes.find(n => n.id === 'main-task').access, { binding: 'run.access' });
  }
});

test('disk migration commits one config pointer, preserves exact backup and Provider data, and is idempotent', async t => {
  const fixtureData = await fixture(t); const { root, configPath, bytes, raw } = fixtureData;
  const result = await migrateV6OnDisk({ configPath }); assert.equal(result.workflows, raw.task_types.length);
  assert.equal(await readFile(join(root, 'control-plane.v6.backup.json'), 'utf8'), bytes);
  const migrated = JSON.parse(await readFile(configPath, 'utf8')); assert.equal(migrated.version, 7);
  assert.deepEqual(migrated.providers, raw.providers); assert.deepEqual(migrated.global, raw.global); assert(!Object.hasOwn(migrated, 'task_types'));
  assert.equal((await new WorkflowStore(result.store_root).list()).length, raw.task_types.length);
  const second = await migrateV6OnDisk({ configPath }); assert.equal(second.migrated, false);
  assert.equal(second.store_root, result.store_root);
});

test('mid-pack failure exposes no partial set and retains v6 bytes', async t => {
  const { root, configPath, bytes } = await fixture(t); let count = 0;
  await assert.rejects(migrateV6OnDisk({ configPath, onProgress(event) { if (event.phase === 'pack-staged' && ++count === 3) throw new Error('Injected staging interruption'); } }), /Injected staging/);
  assert.equal(await readFile(configPath, 'utf8'), bytes);
  assert.equal((await readdir(root)).filter(name => name.startsWith('workflows-v6-') || name.startsWith('.migration-')).length, 0);
  assert.equal((await migrateV6OnDisk({ configPath })).migrated, true);
});

test('prepared-but-uncommitted store is reconciled without partial publication or duplicate migration', async t => {
  const { root, configPath, bytes } = await fixture(t);
  await assert.rejects(migrateV6OnDisk({ configPath, onProgress(event) { if (event.phase === 'prepared') throw new Error('Injected pre-commit interruption'); } }), /pre-commit/);
  assert.equal(await readFile(configPath, 'utf8'), bytes);
  assert.equal((await readdir(root)).filter(name => name.startsWith('workflows-v6-')).length, 1);
  const result = await migrateV6OnDisk({ configPath }); assert.equal(result.migrated, true);
  assert.equal((await readdir(root)).filter(name => name.startsWith('workflows-v6-')).length, 1);
});

test('configuration edit during migration is preserved and prevents commit', async t => {
  const { configPath, raw } = await fixture(t); let edited;
  await assert.rejects(migrateV6OnDisk({ configPath, async onProgress(event) {
    if (event.phase === 'prepared') { raw.global.console_title = 'User edit'; edited = JSON.stringify(raw); await writeFile(configPath, edited); }
  } }), { code: 'MIGRATION_CONFIG_CHANGED' });
  assert.equal(await readFile(configPath, 'utf8'), edited);
});

test('custom templates preserve whitespace; disabled bindings remain blocked, not replaced', async t => {
  const raw = structuredClone(bundled); const custom = structuredClone(raw.task_types.find(item => item.stages.length));
  custom.id = 'custom'; custom.name = 'Custom'; custom.stages[0].template = '\n  {{task}}\nCustom context: {{context}}\n'; custom.stages[0].requires_user_approval = true;
  raw.task_types.push(custom); raw.providers.find(item => item.id === custom.stages[0].provider_id).enabled = false;
  const { configPath } = await fixture(t, raw); const result = await migrateV6OnDisk({ configPath });
  const { workflow } = await new WorkflowStore(result.store_root).snapshot('custom');
  const node = workflow.nodes.find(item => item.id === custom.stages[0].id);
  assert.equal(node.prompt_template, custom.stages[0].template); assert.equal(node.approval.required, true);
  assert.equal(node.executor.provider_id, custom.stages[0].provider_id);
  const checked = validateWorkflowGraph(workflow, { providers: raw.providers });
  assert.equal(checked.valid, true); assert.equal(checked.launch_ready, false);
});

test('v6 backup restores exact bytes under CAS and retains v7 stores', async t => {
  const { configPath, bytes } = await fixture(t);
  const migrated = await migrateV6OnDisk({ configPath });
  await assert.rejects(restoreV6Backup({ configPath, expected_current_sha256: 'stale' }), { code: 'RESTORE_CONFIG_CHANGED' });
  const result = await restoreV6Backup({ configPath, expected_current_sha256: digest(await readFile(configPath)) });
  assert.equal(result.version, 6); assert.equal(await readFile(configPath, 'utf8'), bytes);
  assert.equal((await new WorkflowStore(migrated.store_root).list()).length, bundled.task_types.length);
});

test('a torn uncommitted journal tail is retained and repaired; complete-record corruption is never skipped', async t => {
  const { root, configPath } = await fixture(t);
  await migrateV6OnDisk({ configPath });
  const journal = join(root, 'migration-v6-to-v7.jsonl');
  const events = (await readFile(journal, 'utf8')).trimEnd().split('\n');
  assert.equal(JSON.parse(events.at(-1)).phase, 'committed');
  const torn = events.slice(0, -1).join('\n') + '\n{"phase":"committ';
  await writeFile(journal, torn);
  const result = await migrateV6OnDisk({ configPath }); assert.equal(result.migrated, false);
  const quarantine = (await readdir(root)).find(name => name.startsWith('migration-v6-to-v7.jsonl.torn-'));
  assert.equal(await readFile(join(root, quarantine), 'utf8'), torn);
  assert((await readFile(journal, 'utf8')).includes('committed_recovered'));
  await writeFile(journal, '{"sequence":1}\n');
  await assert.rejects(migrateV6OnDisk({ configPath }), { code: 'MIGRATION_JOURNAL_CORRUPT' });
  assert.equal(await readFile(journal, 'utf8'), '{"sequence":1}\n');
});
