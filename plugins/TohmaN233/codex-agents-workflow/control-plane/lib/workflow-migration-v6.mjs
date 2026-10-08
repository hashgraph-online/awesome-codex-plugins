import { open, readFile, rename, unlink, mkdir, rm, lstat } from 'node:fs/promises';
import { dirname, join, isAbsolute } from 'node:path';
import { randomUUID } from 'node:crypto';
import { validateConfig } from './config.mjs';
import { createDraft } from './workflow-schema.mjs';
import { canonicalJSON, digest } from './workflow-revisions.mjs';
import { WorkflowStore, syncDirectory } from './workflow-store.mjs';
import { insideRoot, noSymlinks, requireValue } from './workflow-paths.mjs';
import { validateWorkflowGraph } from './workflow-validator.mjs';

const MAX_CONFIG = 512 * 1024;
const edge = (source, target) => ({ id: `${source}-${target}`, source, target, on: 'success' });

export function migrateTaskType(taskType, providers) {
  const workflow = {
    ...createDraft(taskType.id, taskType.name), status: 'ready', enabled: taskType.enabled,
    description: taskType.description, tags: [...taskType.tags], template_kind:'workflow',
    // Legacy native/current-context operation was cooperative. Importing a Skill
    // is a separate operation and requires Strict qualification.
    skill_policy: { mode: 'cooperative', implicit: 'allow', ambient_allow: [], shadowed_skill_paths: [] },
  };
  const mainId = taskType.stages.length ? 'final-acceptance' : 'main-task';
  const commonBindings = {
    task: { path: '/inputs/task', default: '' },
    context: { path: '/inputs/context', default: '' },
    verification: { path: '/inputs/verification', default: '' },
  };
  const main = {
    id: mainId, type: 'agent', label: taskType.stages.length ? 'Final acceptance' : 'Main task',
    executor: { kind: 'main' }, role: 'finalizer',
    access: taskType.stages.length ? 'read_only' : { binding: 'run.access' },
    ...(taskType.stages.length ? {} : { path_scope: { binding: 'run.allowed_paths' } }),
    prompt_template: taskType.stages.length
      ? 'Verify the completed workflow results against the task and evidence, resolve acceptance, and report the final outcome.\nTask: {{task}}\nContext: {{context}}\nConstraints: {{constraints}}\nVerification: {{verification}}'
      : 'Complete the task within the current Run permissions and verify the result.\nTask: {{task}}\nContext: {{context}}\nConstraints: {{constraints}}\nVerification: {{verification}}',
    approval: { required: false }, retry: { max_attempts: 1 },
    input_bindings: { ...commonBindings, ...(taskType.stages.length ? { result: `/nodes/${taskType.stages.at(-1).id}/output` } : {}) },
  };
  workflow.nodes = [{ id: 'start', type: 'start' }, ...taskType.stages.map((stage, index) => ({
    id: stage.id, type: 'agent', label: stage.id, executor: { kind: 'provider', provider_id: stage.provider_id },
    role: stage.role, access: stage.access,
    ...(stage.access === 'bounded_write' ? { path_scope: { binding: 'run.allowed_paths' } } : {}),
    prompt_template: stage.template, approval: { required: stage.requires_user_approval },
    retry: { max_attempts: 1 }, input_bindings: {
      ...commonBindings,
      ...(index ? { previous_result: `/nodes/${taskType.stages[index - 1].id}/output` } : {}),
    },
  })), main, { id: 'end', type: 'end' }];
  workflow.edges = workflow.nodes.slice(0, -1).map((node, index) => edge(node.id, workflow.nodes[index + 1].id));
  workflow.finalization = { required: true, node_id: mainId };
  workflow.requirements.providers = [...new Set(taskType.stages.map(stage => stage.provider_id))].sort();
  const checked = validateWorkflowGraph(workflow, { providers });
  requireValue(checked.valid, 'MIGRATION_TASK_TYPE', `Task Type ${taskType.id} cannot be migrated`, { task_type_id: taskType.id, validation: checked });
  return workflow;
}

export function prepareV6Migration(raw) {
  requireValue(raw?.version === 6, 'MIGRATION_VERSION', 'This migration only accepts v6 input');
  const config = validateConfig(raw);
  const workflows = config.task_types.map((taskType, index) => migrateTaskType({
    ...taskType,
    stages: taskType.stages.map((stage, stageIndex) => ({ ...stage, template: raw.task_types[index].stages[stageIndex].template })),
  }, config.providers));
  const mappings = Object.fromEntries(config.task_types.map(taskType => [taskType.id, {
    workflow_id: taskType.id, route: taskType.route,
    stage_nodes: Object.fromEntries(taskType.stages.map(stage => [stage.id, stage.id])),
  }]));
  return { config, workflows, mappings };
}

async function readConfigBytes(path) {
  await noSymlinks(path);
  const info = await lstat(path);
  requireValue(info.isFile() && info.size <= MAX_CONFIG, 'CONFIG_SIZE', 'Configuration is not a bounded regular file');
  const bytes = await readFile(path);
  requireValue(bytes.length <= MAX_CONFIG, 'CONFIG_SIZE', 'Configuration grew during read');
  return bytes;
}

async function exclusiveFile(path, bytes) {
  await noSymlinks(dirname(path));
  const file = await open(path, 'wx', 0o600);
  try { await file.writeFile(bytes); await file.sync(); } finally { await file.close(); }
}

function decodeJournal(bytes) {
    requireValue(bytes === '' || bytes.endsWith('\n'), 'MIGRATION_JOURNAL_TORN', 'Migration journal has an incomplete tail');
    const events = bytes === '' ? [] : bytes.slice(0, -1).split('\n').map(line => JSON.parse(line));
    let previous = null;
    for (const [index, event] of events.entries()) {
      const { hash, ...content } = event;
      requireValue(content.sequence === index + 1 && content.previous === previous && digest(canonicalJSON(content)) === hash, 'MIGRATION_JOURNAL_CORRUPT', 'Migration journal chain is corrupt');
      previous = hash;
    }
    return events;
}

async function readJournal(path) {
  try {
    await noSymlinks(path);
    requireValue((await lstat(path)).size <= 16 * 1024 * 1024, 'MIGRATION_JOURNAL_SIZE', 'Migration journal exceeds inspection limit');
    return decodeJournal(await readFile(path, 'utf8'));
  } catch (error) { if (error.code === 'ENOENT') return []; throw error; }
}

async function recoverJournalTail(path) {
  let bytes;
  try {
    await noSymlinks(path);
    const info = await lstat(path);
    requireValue(info.isFile() && info.size <= 16 * 1024 * 1024, 'MIGRATION_JOURNAL_SIZE', 'Migration journal exceeds inspection limit');
    bytes = await readFile(path);
  }
  catch (error) { if (error.code === 'ENOENT') return; throw error; }
  requireValue(bytes.length <= 16 * 1024 * 1024, 'MIGRATION_JOURNAL_SIZE', 'Migration journal exceeds inspection limit');
  if (!bytes.length || bytes.at(-1) === 10) return;
  const prefix = bytes.subarray(0, bytes.lastIndexOf(10) + 1);
  decodeJournal(prefix.toString()); // Never discard a corrupt complete record.
  const quarantine = path + '.torn-' + randomUUID();
  const temporary = path + '.repair-' + randomUUID();
  await exclusiveFile(quarantine, bytes);
  try {
    await exclusiveFile(temporary, prefix);
    requireValue(digest(await readFile(path)) === digest(bytes), 'MIGRATION_JOURNAL_CHANGED', 'Journal changed during tail recovery');
    await rename(temporary, path); await syncDirectory(dirname(path));
    await appendJournal(path, { phase: 'journal_tail_recovered', retained_file: quarantine.slice(dirname(path).length + 1), retained_sha256: digest(bytes), discarded_tail_bytes: bytes.length - prefix.length });
  } finally { try { await unlink(temporary); } catch (error) { if (error.code !== 'ENOENT') throw error; } }
}

async function appendJournal(path, event) {
  const events = await readJournal(path);
  const content = { ...event, sequence: events.length + 1, previous: events.at(-1)?.hash ?? null };
  const handle = await open(path, 'a', 0o600);
  try { await handle.writeFile(canonicalJSON({ ...content, hash: digest(canonicalJSON(content)) }) + '\n'); await handle.sync(); }
  finally { await handle.close(); }
}

export async function migrateV6OnDisk({ configPath, onProgress = async () => {} }) {
  requireValue(isAbsolute(configPath), 'ABSOLUTE_PATH_REQUIRED', 'Migration requires an absolute configuration path');
  const root = dirname(configPath);
  const writer = new WorkflowStore(root);
  return writer.withWriter(async () => {
    const original = await readConfigBytes(configPath);
    const raw = JSON.parse(original);
    const journal = join(root, 'migration-v6-to-v7.jsonl');
    await recoverJournalTail(journal);
    const events = await readJournal(journal);
    if (raw.version === 7) {
      const source = raw.workflow_store?.migration_source_sha256;
      requireValue(/^[a-f0-9]{64}$/.test(source), 'MIGRATION_STATE', 'Missing migration source identity');
      requireValue(typeof raw.workflow_store.relative_path === 'string' && !isAbsolute(raw.workflow_store.relative_path), 'MIGRATION_STATE', 'Store pointer must be relative to configuration root');
      const storeRoot = insideRoot(root, join(root, raw.workflow_store.relative_path));
      await new WorkflowStore(storeRoot).list();
      if (!events.some(event => event.source_sha256 === source && ['committed', 'committed_recovered'].includes(event.phase))) {
        requireValue(events.some(event => event.source_sha256 === source && event.phase === 'prepared' && event.config_sha256 === digest(original)), 'MIGRATION_STATE', 'Committed configuration has no matching prepared journal record');
        await appendJournal(journal, { phase: 'committed_recovered', source_sha256: source });
      }
      return { migrated: false, version: 7, store_root: storeRoot };
    }
    const prepared = prepareV6Migration(raw);
    const source = digest(original);
    const backup = join(root, 'control-plane.v6.backup.json');
    try { await exclusiveFile(backup, original); }
    catch (error) {
      if (error.code !== 'EEXIST') throw error;
      requireValue(digest(await readConfigBytes(backup)) === source, 'MIGRATION_BACKUP_CONFLICT', 'Existing v6 backup belongs to different source bytes; preserve and inspect it');
    }
    const relativeStore = `workflows-v6-${source}`;
    const storeRoot = insideRoot(root, join(root, relativeStore));
    const temporary = insideRoot(root, join(root, '.migration-' + randomUUID()));
    let stagingExists = false;
    let committed = false;
    try {
      await appendJournal(journal, { phase: 'started', source_sha256: source, workflow_ids: prepared.workflows.map(workflow => workflow.id) });
      await mkdir(temporary); stagingExists = true;
      const staging = await new WorkflowStore(temporary, { validationContext: { providers: prepared.config.providers } }).initialize();
      const expected = [];
      for (const workflow of prepared.workflows) {
        try {
          const document = await staging.create(workflow, { provenance: { kind: 'v6-migration', source_sha256: source, task_type_id: workflow.id } });
          expected.push([workflow.id, document.revision_hash]);
          await onProgress({ phase: 'pack-staged', task_type_id: workflow.id });
        } catch (error) {
          throw Object.assign(new Error(`Migration of Task Type ${workflow.id} failed: ${error.message}`), { code: error.code ?? 'MIGRATION_TASK_TYPE', task_type_id: workflow.id, cause: error });
        }
      }
      let existing = false;
      try { await lstat(storeRoot); existing = true; } catch (error) { if (error.code !== 'ENOENT') throw error; }
      if (existing) {
        const documents = await new WorkflowStore(storeRoot).list();
        requireValue(canonicalJSON(documents.map(document => [document.workflow.id, document.revision_hash]).sort()) === canonicalJSON([...expected].sort()), 'MIGRATION_STORE_CONFLICT', 'Unpublished migration store differs from the complete prepared set');
        await noSymlinks(temporary); await rm(insideRoot(root, temporary), { recursive: true, maxRetries: 3, retryDelay: 100 }); stagingExists = false;
      } else { await rename(temporary, storeRoot); stagingExists = false; }
      await syncDirectory(root);
      const { task_types, ...retained } = raw;
      const next = {
        ...retained, version: 7,
        workflow_store: { schema_version: 1, relative_path: relativeStore, migration_source_sha256: source },
        legacy_mapping: prepared.mappings,
      };
      const bytes = Buffer.from(JSON.stringify(next, null, 2) + '\n');
      requireValue(bytes.length <= MAX_CONFIG, 'CONFIG_SIZE', 'Migrated configuration exceeds size limit');
      await appendJournal(journal, { phase: 'prepared', source_sha256: source, config_sha256: digest(bytes), store_relative_path: relativeStore });
      await onProgress({ phase: 'prepared', workflow_count: expected.length });
      requireValue(digest(await readConfigBytes(configPath)) === source, 'MIGRATION_CONFIG_CHANGED', 'v6 configuration changed during migration');
      const tempConfig = configPath + '.migration-' + randomUUID();
      try { await exclusiveFile(tempConfig, bytes); await rename(tempConfig, configPath); committed = true; await syncDirectory(root); }
      finally { try { await unlink(tempConfig); } catch (error) { if (error.code !== 'ENOENT') throw error; } }
      await appendJournal(journal, { phase: 'committed', source_sha256: source });
      await onProgress({ phase: 'committed', workflow_count: expected.length });
      return { migrated: true, version: 7, store_root: storeRoot, workflows: expected.length, backup_path: backup };
    } catch (error) {
      if (stagingExists) {
        try { await noSymlinks(temporary); await rm(insideRoot(root, temporary), { recursive: true, maxRetries: 3, retryDelay: 100 }); }
        catch (cleanupError) { throw new AggregateError([error, cleanupError], 'Migration and staging cleanup failed'); }
      }
      if (committed) throw Object.assign(new Error(`Migration configuration committed; audit/reconciliation is required: ${error.message}`), { code: 'MIGRATION_COMMITTED_AUDIT_FAILED', cause: error, config_committed: true });
      throw error;
    }
  });
}

export async function restoreV6Backup({ configPath, expected_current_sha256 }) {
  requireValue(isAbsolute(configPath), 'ABSOLUTE_PATH_REQUIRED', 'Restore requires an absolute configuration path');
  const root = dirname(configPath);
  return new WorkflowStore(root).withWriter(async () => {
    const current = await readConfigBytes(configPath);
    requireValue(digest(current) === expected_current_sha256, 'RESTORE_CONFIG_CHANGED', 'Configuration changed since restore was requested');
    const backup = await readConfigBytes(join(root, 'control-plane.v6.backup.json'));
    validateConfig(JSON.parse(backup));
    const journal = join(root, 'migration-v6-to-v7.jsonl');
    await recoverJournalTail(journal);
    await appendJournal(journal, { phase: 'rollback_prepared', source_sha256: digest(backup), previous_config_sha256: digest(current) });
    const temporary = configPath + '.restore-' + randomUUID();
    let committed = false;
    try {
      await exclusiveFile(temporary, backup);
      requireValue(digest(await readConfigBytes(configPath)) === expected_current_sha256, 'RESTORE_CONFIG_CHANGED', 'Configuration changed during restore');
      await rename(temporary, configPath); committed = true;
      await syncDirectory(root);
      await appendJournal(journal, { phase: 'rolled_back', source_sha256: digest(backup) });
      return { restored: true, version: 6, workflow_stores_retained: true };
    } catch (error) {
      if (committed) throw Object.assign(new Error(`Backup restored; audit reconciliation required: ${error.message}`), { code: 'RESTORE_COMMITTED_AUDIT_FAILED', config_committed: true, cause: error });
      throw error;
    } finally { try { await unlink(temporary); } catch (error) { if (error.code !== 'ENOENT') throw error; } }
  });
}
