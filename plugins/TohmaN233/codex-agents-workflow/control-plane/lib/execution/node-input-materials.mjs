import { open, readFile, link, unlink, lstat, realpath, stat } from 'node:fs/promises';
import { basename, dirname, extname, isAbsolute, join, resolve } from 'node:path';
import { randomUUID } from 'node:crypto';
import { compilePrompt } from '../workflow-executor.mjs';
import { canonicalJSON, digest } from '../workflow-revisions.mjs';
import { ensureDirectory, noSymlinks, requireValue } from '../workflow-paths.mjs';
import { syncDirectory } from '../workflow-store.mjs';

const NATIVE_FILE_LIMIT = 8 * 1024 * 1024;
const NATIVE_BUNDLE_LIMIT = 32 * 1024 * 1024;
// The child reads task.json through the ordinary native tool channel. Keep that
// index below one conservative response so the first read can never silently
// omit later assignments. Large values live in separate Host-written files.
const NATIVE_TASK_INDEX_LIMIT = 16 * 1024;

const inputReferenceText = ({ path, format }) =>
  `Read this bound input from the local file at ${canonicalJSON(path)} (format: ${format}).`;

function serializedInput(name, value) {
  if (typeof value === 'string') {
    if (name.endsWith('_json')) {
      try { return { format: 'json', bytes: Buffer.from(canonicalJSON(JSON.parse(value)), 'utf8') }; }
      catch (error) {
        if (error instanceof SyntaxError) return { format: 'text', bytes: Buffer.from(value, 'utf8') };
        throw error;
      }
    }
    return { format: 'text', bytes: Buffer.from(value, 'utf8') };
  }
  return { format: 'json', bytes: Buffer.from(canonicalJSON(value), 'utf8') };
}

async function existingBytes(path) {
  try {
    await noSymlinks(path);
    const info = await lstat(path);
    requireValue(info.isFile() && !info.isSymbolicLink(), 'NODE_INPUT_MATERIALS_CONFLICT', `Expected a regular Host input file: ${path}`);
    return await readFile(path);
  } catch (error) {
    if (error.code === 'ENOENT') return null;
    throw error;
  }
}

async function writeIdempotently(path, bytes) {
  const parent = dirname(path);
  await noSymlinks(parent);
  const current = await existingBytes(path);
  if (current) {
    requireValue(current.equals(bytes), 'NODE_INPUT_MATERIALS_CONFLICT', `A different Host input file already exists: ${path}`);
    return;
  }

  const temporary = join(parent, `.${basename(path)}.write-${randomUUID()}`);
  let file;
  let primary;
  try {
    file = await open(temporary, 'wx', 0o600);
    await file.writeFile(bytes);
    await file.sync();
    await file.close();
    file = undefined;
    try {
      await link(temporary, path);
    } catch (error) {
      if (error.code !== 'EEXIST') throw error;
      const raced = await existingBytes(path);
      requireValue(raced?.equals(bytes), 'NODE_INPUT_MATERIALS_CONFLICT', `A different Host input file already exists: ${path}`);
    }
    await syncDirectory(parent);
  } catch (error) {
    primary = error;
  }

  const cleanup = [];
  if (file) try { await file.close(); } catch (error) { cleanup.push(error); }
  try { await unlink(temporary); } catch (error) { if (error.code !== 'ENOENT') cleanup.push(error); }
  if (!primary && cleanup.length) primary = cleanup.shift();
  if (primary && cleanup.length) throw new AggregateError([primary, ...cleanup], 'Host input write and cleanup failed');
  if (primary) throw primary;
  if (cleanup.length) throw new AggregateError(cleanup, 'Host input cleanup failed');
  await syncDirectory(parent);
}

async function existingLocalAddress(value, workspace) {
  if (typeof value !== 'string') return null;
  if (!isAbsolute(value) && !(typeof workspace === 'string' && isAbsolute(workspace))) return null;
  const candidate = isAbsolute(value) ? value : resolve(workspace, value);
  let absolute;
  try { absolute = await realpath(candidate); }
  catch (error) {
    // This is optional address discovery for an arbitrary semantic value.
    // The filesystem can attest that no such name is representable; preserve
    // that value as content. Access, I/O and explicit verified-path errors fail.
    if (['ENOENT', 'ENOTDIR', 'ENAMETOOLONG'].includes(error.code)) return null;
    throw error;
  }
  const info = await stat(absolute);
  return info.isFile() || info.isDirectory() ? absolute : null;
}

async function verifiedInputFiles(inputs, workspace) {
  const found = new Map();
  let total = 0;
  const pointer = segments => segments.length ? '/' + segments.map(value => String(value).replaceAll('~','~0').replaceAll('/','~1')).join('/') : '';
  const visit = async (value, segments = []) => {
    if (Array.isArray(value)) {
      for (let index = 0; index < value.length; index++) await visit(value[index], [...segments,index]);
      return;
    }
    if (!value || typeof value !== 'object') return;
    const keys = Object.keys(value).sort();
    for (const name of keys) {
      const pathValue = value[name];
      if (name.endsWith('_path') && typeof pathValue === 'string') {
        const hashName = `${name.slice(0, -5)}_sha256`;
        if (Object.hasOwn(value, hashName)) {
          const expected = value[hashName];
          requireValue(/^[a-f0-9]{64}$/.test(expected), 'NATIVE_TASK_FILE_HASH', `Invalid SHA-256 beside ${pointer([...segments,name])}`);
          requireValue(typeof workspace === 'string' && isAbsolute(workspace), 'NATIVE_TASK_WORKSPACE', 'Verified relative task files require an absolute workspace');
          const candidate = isAbsolute(pathValue) ? resolve(pathValue) : resolve(workspace, pathValue);
          await noSymlinks(candidate);
          const absolute = await realpath(candidate);
          const info = await lstat(absolute);
          requireValue(info.isFile() && !info.isSymbolicLink() && info.size <= NATIVE_FILE_LIMIT,
            'NATIVE_TASK_FILE', `Verified task input must be a bounded regular file: ${pathValue}`);
          const bytes = await readFile(absolute);
          requireValue(bytes.length === info.size && digest(bytes) === expected,
            'NATIVE_TASK_FILE_CHANGED', `Verified task input hash does not match: ${pathValue}`);
          total += bytes.length;
          requireValue(total <= NATIVE_BUNDLE_LIMIT, 'NATIVE_TASK_BUNDLE_LIMIT', 'Verified task files exceed the native task bundle limit');
          const key = `${absolute}\u0000${expected}`;
          const referenceSegments=[...segments,name],reference=pointer(referenceSegments);
          if (found.has(key)) {
            found.get(key).references.push(reference);
            found.get(key).reference_segments.push(referenceSegments);
          }
          else found.set(key, { path: pathValue, resolved_path: absolute, sha256: expected, bytes: bytes.length,
            references: [reference], reference_segments:[referenceSegments], content:bytes });
        }
      }
      await visit(pathValue, [...segments,name]);
    }
  };
  await visit(inputs ?? {});
  return [...found.values()];
}

function localMaterialName(prefix, sha256, sourcePath) {
  const suffix=extname(sourcePath).toLowerCase();
  return `${prefix}-${sha256}${/^\.[a-z0-9]{1,12}$/.test(suffix)?suffix:'.bin'}`;
}

function replaceAt(root, segments, value) {
  let target=root;
  for(let index=0;index<segments.length-1;index++)target=target[segments[index]];
  target[segments.at(-1)]=value;
}

/**
 * Create one bounded index plus deterministic local materials for a visible
 * native subagent. Exact path/hash pairs are verified, copied once and replaced
 * in bound inputs with their Host-selected local paths. Large values never share
 * task.json, so an ordinary child read cannot truncate later assignments.
 */
export async function materializeNativeTaskBundle({ directory, envelope, resources = [], resultSchema,
  allowedPaths = [], itemPositions = null, maxPromptChars = 64_000 }) {
  requireValue(typeof directory === 'string' && isAbsolute(directory), 'NATIVE_TASK_BUNDLE_PATH', 'Native task bundle directory must be an absolute Host-selected path');
  requireValue(envelope && typeof envelope === 'object' && !Array.isArray(envelope), 'NATIVE_TASK_BUNDLE_ENVELOPE', 'Native task bundle needs one projected execution envelope');
  const absoluteDirectory = resolve(directory);
  const verifiedDirectory=join(absoluteDirectory,'verified'),resourceDirectory=join(absoluteDirectory,'resources'),inputDirectory=join(absoluteDirectory,'inputs');
  const verifiedFiles = await verifiedInputFiles(envelope.inputs, envelope.workspace);
  const rewrittenInputs=structuredClone(envelope.inputs??{});
  const verifiedItems=verifiedFiles.map(item=>{
    const localPath=join(verifiedDirectory,localMaterialName('input',item.sha256,item.resolved_path));
    for(const segments of item.reference_segments)replaceAt(rewrittenInputs,segments,localPath);
    return {...item,local_path:localPath};
  });
  const {entries:inputEntries,localAddresses}=await materializationPlan(rewrittenInputs,inputDirectory,envelope.workspace);
  const compileEnvelope = structuredClone({...envelope,inputs:rewrittenInputs});
  compileEnvelope.inputs={...compileEnvelope.inputs};
  for(const [name,path] of Object.entries(localAddresses))compileEnvelope.inputs[name]=path;
  for(const item of inputEntries)compileEnvelope.inputs[item.name]=inputReferenceText(item);
  compileEnvelope.prompt_template = String(compileEnvelope.prompt_template ?? '').replace(
    'Resources listed below are logical identifiers, not filesystem paths. Use read_workflow_resource; cite resource IDs.',
    'Pinned resources are Host-materialized local files listed in this task bundle; read those exact local paths.');
  const task = compilePrompt(compileEnvelope, maxPromptChars);
  const resourceItems = resources.map(item => {
    const bytes = Buffer.from(item.bytes);
    requireValue(typeof item.path === 'string' && /^[a-f0-9]{64}$/.test(item.sha256)
      && Number.isSafeInteger(item.size) && item.size === bytes.length && digest(bytes) === item.sha256,
    'NATIVE_TASK_RESOURCE', `Pinned native task resource is invalid: ${item.path ?? '<unknown>'}`);
    const localPath=join(resourceDirectory,localMaterialName('resource',item.sha256,item.path));
    return { path: item.path, sha256: item.sha256, bytes: bytes.length, local_path:localPath, content:bytes };
  });
  const bundle = { schema_version: 1, task, workspace: envelope.workspace, access: envelope.access,
    writable_paths: structuredClone(allowedPaths),
    resources: resourceItems.map(({content:_content,...item})=>item),
    verified_files: verifiedItems.map(({content:_content,resolved_path:_resolved,reference_segments:_segments,...item})=>item),
    ...(resultSchema === undefined ? {} : { result_schema: structuredClone(resultSchema) }) };
  const bytes = Buffer.from(canonicalJSON(bundle), 'utf8');
  requireValue(bytes.length <= NATIVE_TASK_INDEX_LIMIT, 'NATIVE_TASK_INDEX_LIMIT',
    `Native task index exceeds ${NATIVE_TASK_INDEX_LIMIT} bytes; large inputs or schemas must be materialized separately`);
  const path = join(absoluteDirectory, 'task.json');
  await ensureDirectory(absoluteDirectory);
  if(verifiedItems.length)await ensureDirectory(verifiedDirectory);
  if(resourceItems.length)await ensureDirectory(resourceDirectory);
  if(inputEntries.length)await ensureDirectory(inputDirectory);
  for(const item of verifiedItems)await writeIdempotently(item.local_path,item.content);
  for(const item of resourceItems)await writeIdempotently(item.local_path,item.content);
  for(const item of inputEntries)await writeIdempotently(item.path,item.content);
  await writeIdempotently(path, bytes);
  return { task_bundle_path: path, task_bundle_sha256: digest(bytes), task_sha256: digest(Buffer.from(task, 'utf8')),
    task_bundle_bytes:bytes.length,verified_file_count: verifiedFiles.length, resource_count: resourceItems.length,
    bound_input_count:inputEntries.length,
    ...(itemPositions === null ? {} : { item_positions: structuredClone(itemPositions) }),
    allowed_paths: structuredClone(allowedPaths) };
}

async function materializationPlan(inputs, directory, workspace) {
  const entries = [];
  const localAddresses = {};
  for (const [name, value] of Object.entries(inputs ?? {}).sort(([left], [right]) => left < right ? -1 : left > right ? 1 : 0)) {
    if (name === 'task') continue;
    // *_json is a serialized input binding, never a local address. Decide its
    // representation before filesystem lookup; large JSON is not a pathname.
    const address = name.endsWith('_json') ? null : await existingLocalAddress(value, workspace);
    if (address) {
      localAddresses[name] = address;
      continue;
    }
    const { format, bytes } = serializedInput(name, value);
    const fileName = `input-${digest(Buffer.from(name, 'utf8'))}.${format === 'json' ? 'json' : 'txt'}`;
    entries.push({ name, path: join(directory, fileName), format, sha256: digest(bytes), bytes: bytes.length, content: bytes });
  }
  return { entries, localAddresses };
}

/**
 * Durably materialize one already-projected node envelope's non-task inputs.
 * The caller owns partition projection and chooses an absolute per-attempt
 * directory that is readable by the child session.
 */
export async function materializeNodeInputs({ directory, envelope, maxPromptChars = 64_000 }) {
  requireValue(typeof directory === 'string' && isAbsolute(directory), 'NODE_INPUT_MATERIALS_PATH', 'Node input material directory must be an absolute Host-selected path');
  requireValue(envelope && typeof envelope === 'object' && !Array.isArray(envelope), 'NODE_INPUT_MATERIALS_ENVELOPE', 'Node execution envelope is required');
  requireValue(Number.isSafeInteger(maxPromptChars) && maxPromptChars > 0, 'NODE_INPUT_MATERIALS_PROMPT_LIMIT', 'Prompt limit must be a positive safe integer');
  requireValue(envelope.inputs === undefined || (envelope.inputs && typeof envelope.inputs === 'object' && !Array.isArray(envelope.inputs)), 'NODE_INPUT_MATERIALS_INPUTS', 'Projected node inputs must be an object');

  const absoluteDirectory = resolve(directory);
  const { entries, localAddresses } = await materializationPlan(envelope.inputs, absoluteDirectory, envelope.workspace);
  const publicManifest = entries.map(({ content: _content, ...item }) => item);
  const compileEnvelope = structuredClone(envelope);
  compileEnvelope.inputs = { ...(compileEnvelope.inputs ?? {}) };
  for (const [name, path] of Object.entries(localAddresses)) compileEnvelope.inputs[name] = path;
  for (const item of publicManifest) {
    compileEnvelope.inputs[item.name] = item.name === 'context' || item.name === 'verification'
      ? inputReferenceText(item)
      : { path: item.path, format: item.format };
  }

  const prompt = compilePrompt(compileEnvelope, maxPromptChars);
  const promptBytes = Buffer.from(prompt, 'utf8');
  const indexPath = join(absoluteDirectory, 'inputs.json');
  const indexBytes = Buffer.from(canonicalJSON({ schema_version: 1, inputs: publicManifest }), 'utf8');

  await ensureDirectory(absoluteDirectory);
  const priorIndex = await existingBytes(indexPath);
  if (priorIndex) requireValue(priorIndex.equals(indexBytes), 'NODE_INPUT_MATERIALS_CONFLICT', `A different Host input manifest already exists: ${indexPath}`);
  for (const item of entries) await writeIdempotently(item.path, item.content);
  await writeIdempotently(indexPath, indexBytes);

  return { prompt, inputs_path: indexPath, manifest: publicManifest, prompt_sha256: digest(promptBytes) };
}
