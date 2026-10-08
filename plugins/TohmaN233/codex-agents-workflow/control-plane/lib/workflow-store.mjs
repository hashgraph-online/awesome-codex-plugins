import { open, readFile, lstat, readdir, mkdir, rename, unlink, rm, rmdir } from 'node:fs/promises';
import { randomUUID } from 'node:crypto';
import { dirname, join, resolve, isAbsolute } from 'node:path';
import { ensureDirectory, noSymlinks, packDirectory, insideRoot, requireValue, workflowId } from './workflow-paths.mjs';
import { canonicalJSON, digest, LIMITS, prepareResources, revisionHash, validateManifest } from './workflow-revisions.mjs';
import { validateWorkflowShape } from './workflow-schema.mjs';
import { validateWorkflowGraph } from './workflow-validator.mjs';
import { requireWorkflowSnapshotIntegrity } from './workflow-ready-validation.mjs';

export async function syncDirectory(path) {
  // Windows does not provide portable directory fsync through Node. File fsync and
  // atomic rename give process-crash consistency; power-loss durability is not claimed.
  if (process.platform === 'win32') return;
  const handle = await open(path, 'r');
  try { await handle.sync(); } finally { await handle.close(); }
}

async function writeExclusive(path, bytes) {
  await noSymlinks(dirname(path));
  const file = await open(path, 'wx', 0o600);
  try { await file.writeFile(bytes); await file.sync(); } finally { await file.close(); }
}

async function readBounded(path, max) {
  await noSymlinks(path);
  const info = await lstat(path);
  requireValue(info.isFile() && info.size <= max, 'WORKFLOW_FILE_LIMIT', `Invalid or oversized store file: ${path}`);
  const data = await readFile(path);
  requireValue(data.length <= max, 'WORKFLOW_FILE_LIMIT', 'Store file grew during read');
  return data;
}

async function purgePackHistory(pack, keepRevision, keepObjects) {
  const revisions = join(pack, 'revisions'); const objects = join(pack, 'objects');
  for (const entry of await readdir(revisions, { withFileTypes: true })) {
    requireValue(entry.isFile() && !entry.isSymbolicLink() && /^[a-f0-9]{64}\.json$/.test(entry.name), 'REVISION_HISTORY_ENTRY', 'Unexpected revision history entry during source purge');
    if (entry.name !== `${keepRevision}.json`) await unlink(join(revisions, entry.name));
  }
  for (const entry of await readdir(objects, { withFileTypes: true })) {
    requireValue(entry.isFile() && !entry.isSymbolicLink() && /^[a-f0-9]{64}$/.test(entry.name), 'RESOURCE_OBJECT_ENTRY', 'Unexpected resource object during source purge');
    if (!keepObjects.has(entry.name)) await unlink(join(objects, entry.name));
  }
  await syncDirectory(revisions); await syncDirectory(objects);
}

async function replaceJSON(path,value){
  const temporary=path+'.tmp-'+randomUUID();
  await writeExclusive(temporary,canonicalJSON(value));
  try{await rename(temporary,path);await syncDirectory(dirname(path));}
  catch(error){try{await unlink(temporary);}catch(cleanup){if(cleanup.code!=='ENOENT')throw new AggregateError([error,cleanup],'Durable record update and cleanup failed');}throw error;}
}

async function optionalJSON(path,max=1024*1024){
  try{return JSON.parse(await readBounded(path,max));}
  catch(error){if(error.code==='ENOENT')return null;throw error;}
}

async function finishHistoryPurge(pack,journal){
  const head=JSON.parse(await readBounded(join(pack,'workflow.json'),LIMITS.definition));
  requireValue(head.revision_hash===journal.revision_hash,'WORKFLOW_PURGE_IDENTITY','History purge belongs to a different Workflow head');
  if(journal.state==='complete')return journal;
  requireValue(journal.schema_version===1&&journal.state==='prepared'&&Array.isArray(journal.keep_objects),'WORKFLOW_PURGE_STATE','History purge record is invalid');
  await purgePackHistory(pack,journal.revision_hash,new Set(journal.keep_objects));
  const completed={schema_version:1,state:'complete',revision_hash:journal.revision_hash,completed_at:new Date().toISOString()};
  await replaceJSON(join(pack,'history-purge.json'),completed);
  return completed;
}

export class WorkflowStore {
  constructor(root, { validationContext = {} } = {}) {
    requireValue(isAbsolute(root), 'ABSOLUTE_PATH_REQUIRED', 'Workflow store root must be absolute');
    this.root = resolve(root);
    this.validationContext = validationContext;
  }

  async initialize() {
    await ensureDirectory(this.root);
    for (const name of ['.pending', '.trash']) await ensureDirectory(join(this.root, name));
    return this;
  }

  async withWriter(action) {
    await noSymlinks(this.root);
    try {
      await lstat(join(this.root, '.recovery.lock'));
      throw Object.assign(new Error('Writer recovery is in progress or requires inspection'), { code: 'WORKFLOW_STORE_BUSY' });
    } catch (error) { if (error.code !== 'ENOENT') throw error; }
    const lock = join(this.root, '.writer.lock');
    let handle;
    try { handle = await open(lock, 'wx', 0o600); }
    catch (error) {
      if (error.code === 'EEXIST') throw Object.assign(new Error('Workflow store has a writer or interrupted transaction; inspect the lock before recovery'), { code: 'WORKFLOW_STORE_BUSY' });
      throw error;
    }
    const token = randomUUID();
    let result; let failure;
    try {
      await handle.writeFile(canonicalJSON({ pid: process.pid, token, created_at: new Date().toISOString() }));
      await handle.sync();
      result = await action();
    } catch (error) { failure = error; }
    const cleanup = [];
    try { await handle.close(); } catch (error) { cleanup.push(error); }
    try {
      const owner = JSON.parse(await readBounded(lock, 4096));
      requireValue(owner.token === token, 'LOCK_OWNERSHIP', 'Writer lock ownership changed');
      await unlink(lock);
    } catch (error) { cleanup.push(error); }
    if (cleanup.length) throw new AggregateError([...(failure ? [failure] : []), ...cleanup], 'Store transaction/lock cleanup failed');
    if (failure) throw failure;
    return result;
  }

  async inspectWriter() {
    try { return JSON.parse(await readBounded(join(this.root, '.writer.lock'), 4096)); }
    catch (error) { if (error.code === 'ENOENT') return null; throw error; }
  }

  async recoverWriter(expectedToken) {
    const recovery = join(this.root, '.recovery.lock');
    await noSymlinks(this.root);
    await mkdir(recovery); // Only one recovery operation may move a stale lock.
    let result; let failure;
    try {
      const owner = await this.inspectWriter();
      requireValue(owner && owner.token === expectedToken && Number.isInteger(owner.pid) && owner.pid > 0, 'LOCK_OWNERSHIP', 'Recovery requires the inspected owner token');
      let absent = false;
      try { process.kill(owner.pid, 0); } catch (error) { if (error.code === 'ESRCH') absent = true; else throw error; }
      requireValue(absent, 'WRITER_ACTIVE', 'Lock owner is still alive; no automatic takeover');
      await ensureDirectory(join(this.root, '.trash'));
      const retained = join(this.root, '.trash', `writer-${randomUUID()}.json`);
      await rename(join(this.root, '.writer.lock'), retained);
      await syncDirectory(this.root);
      result = { recovered: true, retained_at: retained };
    } catch (error) { failure = error; }
    try { await rmdir(recovery); }
    catch (error) { throw new AggregateError([...(failure ? [failure] : []), error], 'Recovery cleanup failed'); }
    if (failure) throw failure;
    return result;
  }

  validate(workflow) {
    validateWorkflowShape(workflow);
    if (workflow.status === 'ready') {
      const result = validateWorkflowGraph(workflow, this.validationContext);
      requireValue(result.valid, 'WORKFLOW_NOT_READY', 'Workflow failed structural validation', { validation: result });
      requireValue(!result.blockers.some(item => ['IMPORT_UNRESOLVED', 'AI_INFERENCE_UNREVIEWED', 'INLINE_SKILL_UNREVIEWED'].includes(item.code)), 'WORKFLOW_REVIEW_REQUIRED', 'Imported observations and inferred instructions require review before Ready', { validation: result });
    }
  }

  async snapshot(id, revision) {
    const pack = packDirectory(this.root, id);
    await noSymlinks(pack);
    let document;
    if (revision !== undefined) {
      requireValue(/^[a-f0-9]{64}$/.test(revision), 'INVALID_REVISION', 'Revision must be a SHA-256 digest');
      document = { ...JSON.parse(await readBounded(join(pack, 'revisions', revision + '.json'), LIMITS.definition * 2)), revision_hash: revision };
    } else document = JSON.parse(await readBounded(join(pack, 'workflow.json'), LIMITS.definition * 2));
    const { revision_hash, ...snapshot } = document;
    validateWorkflowShape(snapshot.workflow);
    requireValue(snapshot.workflow.id === id && Number.isSafeInteger(snapshot.workflow.revision) && snapshot.workflow.revision > 0, 'WORKFLOW_ID_MISMATCH', 'Pack identity or revision number is invalid');
    validateManifest(snapshot.resources);
    requireValue(revisionHash(snapshot) === revision_hash, 'REVISION_CORRUPT', 'Workflow revision hash mismatch');
    for (const resource of snapshot.resources) {
      const bytes = await readBounded(join(pack, 'objects', resource.sha256), LIMITS.resource);
      requireValue(bytes.length === resource.bytes && digest(bytes) === resource.sha256, 'RESOURCE_CORRUPT', `Resource content hash mismatch: ${resource.path}`);
    }
    return document;
  }

  async resources(id, revision) {
    const snapshot = await this.snapshot(id, revision);
    const resources = Object.create(null);
    for (const item of snapshot.resources) {
      const bytes = await readBounded(join(packDirectory(this.root, id), 'objects', item.sha256), LIMITS.resource);
      requireValue(bytes.length === item.bytes && digest(bytes) === item.sha256, 'RESOURCE_CORRUPT', 'Resource changed during export');
      resources[item.path] = bytes;
    }
    return resources;
  }

  async revisions(id) {
    const directory = join(packDirectory(this.root, id), 'revisions'); await noSymlinks(directory);
    const entries = await readdir(directory, { withFileTypes: true }); requireValue(entries.length <= 10000, 'REVISION_HISTORY_LIMIT', 'Revision history exceeds its bounded listing limit');
    const history = [];
    for (const entry of entries) {
      requireValue(entry.isFile() && !entry.isSymbolicLink() && /^[a-f0-9]{64}\.json$/.test(entry.name), 'REVISION_HISTORY_ENTRY', 'Unexpected revision history entry');
      const hash = entry.name.slice(0, -5); const snapshot = JSON.parse(await readBounded(join(directory, entry.name), LIMITS.definition * 2));
      requireValue(revisionHash(snapshot) === hash && snapshot.workflow.id === id, 'REVISION_CORRUPT', 'Revision history identity differs');
      validateWorkflowShape(snapshot.workflow);
      history.push({ revision_hash: hash, revision: snapshot.workflow.revision, name: snapshot.workflow.name, status: snapshot.workflow.status, resources: snapshot.resources.length });
    }
    return history.sort((a, b) => b.revision - a.revision || a.revision_hash.localeCompare(b.revision_hash));
  }

  async list() {
    await noSymlinks(this.root);
    const result = [];
    for (const entry of await readdir(this.root, { withFileTypes: true })) {
      if (['.writer.lock', '.recovery.lock', '.pending', '.trash'].includes(entry.name)) { await noSymlinks(join(this.root, entry.name)); continue; }
      requireValue(entry.isDirectory() && !entry.isSymbolicLink() && /^wf-.+\.pack$/.test(entry.name), 'UNKNOWN_STORE_ENTRY', `Unexpected store entry: ${entry.name}`);
      const id = workflowId(entry.name.slice(3, -5));
      result.push(await this.snapshot(id));
    }
    return result.sort((a, b) => a.workflow.id < b.workflow.id ? -1 : 1);
  }

  async persistSnapshot(pack, snapshot, blobs) {
    const revision_hash = revisionHash(snapshot);
    for (const [hash, bytes] of blobs) {
      const path = join(pack, 'objects', hash);
      try { await writeExclusive(path, bytes); }
      catch (error) {
        if (error.code !== 'EEXIST') throw error;
        requireValue(digest(await readBounded(path, LIMITS.resource)) === hash, 'RESOURCE_CORRUPT', 'Existing object is corrupt');
      }
    }
    const revisionPath = join(pack, 'revisions', revision_hash + '.json');
    const encoded = canonicalJSON(snapshot);
    requireValue(Buffer.byteLength(encoded) <= LIMITS.definition * 2, 'WORKFLOW_SIZE', 'Workflow snapshot exceeds size limit');
    try { await writeExclusive(revisionPath, encoded); }
    catch (error) {
      if (error.code !== 'EEXIST') throw error;
      requireValue((await readBounded(revisionPath, LIMITS.definition * 2)).toString() === encoded, 'REVISION_CORRUPT', 'Existing immutable revision differs');
    }
    await syncDirectory(join(pack, 'objects'));
    await syncDirectory(join(pack, 'revisions'));
    return { ...snapshot, revision_hash };
  }

  async create(workflow, { resources = {}, provenance = {}, import_report = {} } = {}) {
    // New packs opt into declared-only context.  Absent is deliberately
    // retained as the versioned marker for immutable pre-Plan-1 revisions.
    const next = JSON.parse(canonicalJSON({ ...workflow, context_projection_version: workflow.context_projection_version ?? 2, revision: 1 }));
    const { manifest, blobs } = prepareResources(resources);
    const snapshot = JSON.parse(canonicalJSON({ workflow: next, resources: manifest, provenance, import_report }));
    this.validate(next);
    requireWorkflowSnapshotIntegrity(snapshot);
    return this.withWriter(async () => {
      const destination = packDirectory(this.root, next.id);
      try { await lstat(destination); throw Object.assign(new Error('Workflow already exists'), { code: 'WORKFLOW_EXISTS' }); }
      catch (error) { if (error.code !== 'ENOENT') throw error; }
      const temporary = insideRoot(this.root, join(this.root, '.pending', randomUUID()));
      await noSymlinks(dirname(temporary));
      await mkdir(temporary);
      try {
        await mkdir(join(temporary, 'objects')); await mkdir(join(temporary, 'revisions'));
        const document = await this.persistSnapshot(temporary, snapshot, blobs);
        await writeExclusive(join(temporary, 'workflow.json'), canonicalJSON(document));
        await syncDirectory(temporary);
        await rename(temporary, destination);
        await syncDirectory(this.root);
        return document;
      } catch (error) {
        try {
          await noSymlinks(temporary);
          await rm(insideRoot(this.root, temporary), { recursive: true, maxRetries: 3, retryDelay: 50 });
        } catch (cleanupError) {
          if (cleanupError.code !== 'ENOENT') throw new AggregateError([error, cleanupError], 'Create and staging cleanup failed');
        }
        throw error;
      }
    });
  }

  async install(document, { resources = {}, installation } = {}) {
    document = JSON.parse(canonicalJSON(document));
    const { revision_hash, ...snapshot } = document;
    requireValue(/^[a-f0-9]{64}$/.test(revision_hash) && revisionHash(snapshot) === revision_hash,
      'WORKFLOW_PACKAGE_REVISION', 'Installed Workflow snapshot must retain its exact immutable revision identity');
    const prepared = prepareResources(resources);
    requireValue(canonicalJSON(prepared.manifest) === canonicalJSON(snapshot.resources),
      'WORKFLOW_PACKAGE_MANIFEST', 'Installed Workflow resources differ from the immutable snapshot manifest');
    requireValue(installation && typeof installation === 'object' && !Array.isArray(installation)
      && Object.keys(installation).every(key => ['source', 'package_version', 'package_sha256', 'installed_at'].includes(key))
      && (installation.source === null || typeof installation.source === 'string' && installation.source.length <= 8192)
      && typeof installation.package_version === 'string' && /^[a-f0-9]{64}$/.test(installation.package_sha256)
      && typeof installation.installed_at === 'string', 'WORKFLOW_INSTALLATION', 'Local installation metadata is invalid');
    this.validate(snapshot.workflow);
    requireWorkflowSnapshotIntegrity(snapshot);
    return this.withWriter(async () => {
      const destination = packDirectory(this.root, snapshot.workflow.id);
      try { await lstat(destination); throw Object.assign(new Error('Workflow already exists'), { code: 'WORKFLOW_EXISTS' }); }
      catch (error) { if (error.code !== 'ENOENT') throw error; }
      const temporary = insideRoot(this.root, join(this.root, '.pending', randomUUID()));
      await noSymlinks(dirname(temporary)); await mkdir(temporary);
      try {
        await mkdir(join(temporary, 'objects')); await mkdir(join(temporary, 'revisions'));
        const installed = await this.persistSnapshot(temporary, snapshot, prepared.blobs);
        requireValue(installed.revision_hash === revision_hash, 'WORKFLOW_PACKAGE_REVISION', 'Installed Workflow revision changed while staging');
        await writeExclusive(join(temporary, 'workflow.json'), canonicalJSON(installed));
        await writeExclusive(join(temporary, 'installation.json'), canonicalJSON(installation));
        await syncDirectory(temporary); await rename(temporary, destination); await syncDirectory(this.root);
        return {...installed,installation:JSON.parse(canonicalJSON(installation))};
      } catch (error) {
        try { await noSymlinks(temporary); await rm(insideRoot(this.root, temporary), { recursive: true, maxRetries: 3, retryDelay: 50 }); }
        catch (cleanupError) { if (cleanupError.code !== 'ENOENT') throw new AggregateError([error, cleanupError], 'Install and staging cleanup failed'); }
        throw error;
      }
    });
  }

  async save(id, workflow, options = {}) {
    requireValue(options && typeof options==='object' && !Array.isArray(options)
      && Object.keys(options).every(key=>['expected_revision','resources','provenance','import_report','history_purge'].includes(key)),
    'WORKFLOW_SAVE_OPTIONS','Workflow save options contain an unknown or retired field');
    const { expected_revision, resources, history_purge = 'none' }=options;
    let { provenance, import_report }=options;
    workflow = JSON.parse(canonicalJSON(workflow));
    if (provenance !== undefined) provenance = JSON.parse(canonicalJSON(provenance));
    if (import_report !== undefined) import_report = JSON.parse(canonicalJSON(import_report));
    const preparedResources = resources === undefined ? undefined : prepareResources(resources);
    requireValue(['none', 'deferred'].includes(history_purge), 'WORKFLOW_PURGE_HISTORY', 'History purge must be absent or deferred to the guarded cleanup coordinator');
    requireValue(expected_revision, 'REVISION_REQUIRED', 'Save requires the previously read revision hash');
    requireValue(workflow.id === id, 'WORKFLOW_ID_MISMATCH', 'Save cannot change Workflow ID');
    return this.withWriter(async () => {
      const previous = await this.snapshot(id);
      requireValue(previous.revision_hash === expected_revision, 'REVISION_CONFLICT', 'Workflow changed since it was read');
      const resourceData = preparedResources ?? { manifest: previous.resources, blobs: new Map() };
      const snapshot = {
        workflow: { ...workflow, revision: previous.workflow.revision + 1 }, resources: resourceData.manifest,
        provenance: provenance ?? previous.provenance, import_report: import_report ?? previous.import_report,
      };
      this.validate(snapshot.workflow);
      requireWorkflowSnapshotIntegrity(snapshot, { previous });
      const pack = packDirectory(this.root, id);
      const document = await this.persistSnapshot(pack, snapshot, resourceData.blobs);
      const temporary = join(pack, 'workflow.json.tmp-' + randomUUID());
      try {
        await writeExclusive(temporary, canonicalJSON(document));
        let purgeRecord=null;
        if(history_purge!=='none'){
          purgeRecord={schema_version:1,state:'prepared',revision_hash:document.revision_hash,keep_objects:document.resources.map(item=>item.sha256).sort(),prepared_at:new Date().toISOString()};
          await replaceJSON(join(pack,'history-purge.json'),purgeRecord);
        }
        await noSymlinks(join(pack, 'workflow.json'));
        await rename(temporary, join(pack, 'workflow.json'));
        await syncDirectory(pack);
        return document;
      } catch (error) {
        try { await unlink(temporary); } catch (cleanupError) { if (cleanupError.code !== 'ENOENT') throw new AggregateError([error, cleanupError], 'Save and temporary-file cleanup failed'); }
        throw error;
      }
    });
  }

  async resumeHistoryPurge(id,expectedRevision,{beforePurge=async()=>{}}={}){
    requireValue(typeof beforePurge==='function','WORKFLOW_PURGE_GUARD','History purge requires a callable guard');
    return this.withWriter(async()=>{
      const pack=packDirectory(this.root,id),journal=await optionalJSON(join(pack,'history-purge.json'));
      requireValue(journal&&journal.revision_hash===expectedRevision,'WORKFLOW_PURGE_IDENTITY','No matching source-history purge transaction exists');
      await beforePurge();
      return finishHistoryPurge(pack,journal);
    });
  }

  async readAuthoringCleanup(id,runId){
    workflowId(runId);return optionalJSON(join(packDirectory(this.root,id),'authoring-cleanup',`${runId}.json`));
  }

  async beginAuthoringCleanup(id,record){
    workflowId(record?.identity?.run_id);
    return this.withWriter(async()=>{
      const directory=join(packDirectory(this.root,id),'authoring-cleanup');await ensureDirectory(directory);
      const path=join(directory,`${record.identity.run_id}.json`),existing=await optionalJSON(path);
      if(existing){requireValue(canonicalJSON(existing.identity)===canonicalJSON(record.identity),'AUTHORING_CLEANUP_IDENTITY','Cleanup retry belongs to a different accepted deployment');return existing;}
      const created={schema_version:1,status:'pending',identity:structuredClone(record.identity),targets:structuredClone(record.targets),steps:{library:false,workspace:false,job:false,run:false},created_at:new Date().toISOString(),updated_at:new Date().toISOString()};
      await replaceJSON(path,created);return created;
    });
  }

  async markAuthoringCleanup(id,runId,identity,step){
    requireValue(['library','workspace','job','run'].includes(step),'AUTHORING_CLEANUP_STEP','Unknown authoring cleanup step');
    return this.withWriter(async()=>{
      const path=join(packDirectory(this.root,id),'authoring-cleanup',`${workflowId(runId)}.json`),current=await optionalJSON(path);
      requireValue(current&&canonicalJSON(current.identity)===canonicalJSON(identity),'AUTHORING_CLEANUP_IDENTITY','Cleanup record identity changed');
      current.steps[step]=true;current.updated_at=new Date().toISOString();
      if(Object.values(current.steps).every(Boolean)){current.status='complete';current.completed_at=current.updated_at;}
      await replaceJSON(path,current);return current;
    });
  }

  async rename(id, name, expected_revision) {
    const previous = await this.snapshot(id);
    return this.save(id, { ...previous.workflow, name }, { expected_revision });
  }

  async duplicate(id, nextId, name, revision) {
    const source = await this.snapshot(id, revision);
    return this.create({ ...source.workflow, id: workflowId(nextId), name }, {
      resources: await this.resources(id, source.revision_hash), provenance: source.provenance, import_report: source.import_report,
    });
  }

  async restore(id, revision, expected_revision) {
    const previous = await this.snapshot(id, revision);
    return this.save(id, previous.workflow, {
      expected_revision, resources: await this.resources(id, revision),
      provenance: previous.provenance, import_report: previous.import_report,
    });
  }

  async delete(id, expected_revision) {
    return this.withWriter(async () => {
      const previous = await this.snapshot(id);
      requireValue(expected_revision === previous.revision_hash, 'REVISION_CONFLICT', 'Delete requires the current revision hash');
      const trash = join(this.root, '.trash', `${workflowId(id)}-${randomUUID()}`);
      await noSymlinks(dirname(trash));
      await rename(packDirectory(this.root, id), trash);
      await syncDirectory(this.root); await syncDirectory(dirname(trash));
      return { id, deleted: true, retained_at: trash };
    });
  }

  // Authoring job Packs contain private conversion inputs and therefore cannot
  // use the recoverable library delete path.  Callers must pin both the exact
  // revision and provenance class before this irreversible removal is allowed.
  async purge(id, expected_revision, { expected_provenance_kind, allow_missing = false } = {}) {
    requireValue(typeof allow_missing === 'boolean', 'WORKFLOW_PURGE_POLICY', 'Purge missing policy must be explicit');
    return this.withWriter(async () => {
      let previous;
      try { previous = await this.snapshot(id); }
      catch (error) {
        if (allow_missing && error.code === 'ENOENT') return { id, purged: false, missing: true };
        throw error;
      }
      requireValue(expected_revision === previous.revision_hash, 'REVISION_CONFLICT', 'Permanent purge requires the current revision hash');
      if (expected_provenance_kind !== undefined) requireValue(previous.provenance?.kind === expected_provenance_kind,
        'WORKFLOW_PURGE_PROVENANCE', 'Permanent purge provenance does not match the authorized artifact class');
      const pack = packDirectory(this.root, id); await noSymlinks(pack);
      const info = await lstat(pack);
      requireValue(info.isDirectory() && !info.isSymbolicLink(), 'WORKFLOW_PURGE_TARGET', 'Permanent purge target must be one exact Pack directory');
      await rm(insideRoot(this.root, pack), { recursive: true, maxRetries: 3, retryDelay: 100 });
      await syncDirectory(this.root);
      return { id, purged: true, revision_hash: previous.revision_hash };
    });
  }
}
