import {readPinnedObject} from '../pinned-object-reader.mjs';
import { open, readFile, link, unlink, lstat, realpath, stat } from 'node:fs/promises';
import { basename, dirname, extname, isAbsolute, join, resolve } from 'node:path';
import { randomUUID } from 'node:crypto';
import { constants as filesystemConstants } from 'node:fs';
import { compilePrompt } from '../workflow-executor.mjs';
import { canonicalJSON, digest, LIMITS } from '../workflow-revisions.mjs';
import { ensureDirectory, noSymlinks, requireValue } from '../workflow-paths.mjs';
import { syncDirectory } from '../workflow-store.mjs';

const NATIVE_FILE_LIMIT = 8 * 1024 * 1024;
const NATIVE_BUNDLE_LIMIT = 32 * 1024 * 1024;
// Canonical and large semantic indices stay below one conservative response.
// Small semantic projections are delivered directly; large values live in
// separate Host-written files without truncating later assignments.
const NATIVE_TASK_INDEX_LIMIT = 16 * 1024;

export const HOST_MAIN_INLINE_BUDGETS = Object.freeze({ item_bytes: 8192, resource_bytes: 8192, input_bytes: 8192, total_bytes: 12000 });

export const MAIN_TASK_INLINE_LIMIT = 12000;
export const NATIVE_TASK_INLINE_LIMIT = 1024;
export const TERMINAL_MAIN_INPUT_BUDGET=Object.freeze({item_bytes:32*1024,total_bytes:64*1024,reply_bytes:96*1024});
// Generous metadata-only ceiling matching the pinned Run resource-byte budget.
// Public/canonical task indices retain their much smaller 16KiB bound.
const MAIN_PREPARATION_METADATA_LIMIT = 64 * 1024 * 1024;

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

// Both native packets and Main preparation use the same exact-byte resource
// validation and content-addressed local names, then writeIdempotently below.
function pinnedResourcePlan(resources, directory) {
  const seen = new Set();
  return resources.map(item => {
    const bytes = Buffer.from(item.bytes);
    requireValue(typeof item.path === 'string' && !seen.has(item.path) && /^[a-f0-9]{64}$/.test(item.sha256)
      && Number.isSafeInteger(item.size) && item.size === bytes.length && digest(bytes) === item.sha256,
    'NATIVE_TASK_RESOURCE', `Pinned task resource is invalid: ${item.path ?? '<unknown>'}`);
    seen.add(item.path);
    return { path: item.path, sha256: item.sha256, bytes: bytes.length,
      local_path: join(directory, localMaterialName('resource', item.sha256, item.path)), content: bytes };
  });
}

/** Read only declared Run objects, rejecting changed bytes and linked objects. */
export async function readPinnedNodeResources({ objectDirectory, pins, paths }) {
  requireValue(Array.isArray(paths) && paths.every(path => typeof path === 'string') && new Set(paths).size === paths.length,
    'NODE_RESOURCE_DECLARATION', 'Node resource declarations must be unique logical paths');
  const resources = [];
  for (const path of [...paths].sort()) {
    const pin = pins.find(item => item.path === path);
    requireValue(pin && /^[a-f0-9]{64}$/.test(pin.sha256) && Number.isSafeInteger(pin.bytes) && pin.bytes >= 0,
      'NODE_RESOURCE_PIN', `Pinned resource is unavailable: ${path}`);
    const bytes = await readPinnedObject(objectDirectory,pin);
    resources.push({ path, sha256: pin.sha256, size: pin.bytes, bytes });
  }
  return resources;
}

function replaceAt(root, segments, value) {
  let target=root;
  for(let index=0;index<segments.length-1;index++)target=target[segments[index]];
  target[segments.at(-1)]=value;
}

/**
 * Create one bounded index plus deterministic local materials for a visible
 * native subagent. Exact path/hash pairs are verified, copied once and replaced
 * in bound inputs with their Host-selected local paths. Shared Main preparation
 * admits small semantic bodies once and keeps large values in exact sidecars.
 */
export async function materializeNativeTaskBundle({ directory, envelope, resources = [], resultSchema,
  allowedPaths = [], itemPositions = null, maxPromptChars = 64_000 }) {
  requireValue(typeof directory === 'string' && isAbsolute(directory), 'NATIVE_TASK_BUNDLE_PATH', 'Native task bundle directory must be an absolute Host-selected path');
  requireValue(envelope && typeof envelope === 'object' && !Array.isArray(envelope), 'NATIVE_TASK_BUNDLE_ENVELOPE', 'Native task bundle needs one projected execution envelope');
  const absoluteDirectory = resolve(directory);
  const path = join(absoluteDirectory, 'task.json');
  const retained=await projectionBytes(path,NATIVE_TASK_INDEX_LIMIT);
  if(retained){
    const prior=JSON.parse(retained.toString('utf8'));
    requireValue(prior&&[1,2].includes(prior.schema_version),'NATIVE_TASK_BUNDLE','Existing native task has an unsupported canonical schema');
    if(prior.schema_version===1)return await retainLegacyNativeTask({directory:absoluteDirectory,envelope,resources,resultSchema,
      allowedPaths,itemPositions,maxPromptChars,path,retained});
  }
  const nativeScope={workspace:envelope.workspace,access:envelope.access,writable_paths:structuredClone(allowedPaths),
    ...(resultSchema===undefined?{}:{result_schema:structuredClone(resultSchema)})};
  const references=(envelope.context_projection?.references??resources.map(item=>item.path)).map(item=>typeof item==='string'?item:item.path);
  const prepared=await prepareHostMainContext({directory:absoluteDirectory,
    envelope:{...envelope,resources:envelope.resources??resources.map(item=>item.path),
      context_projection:{...envelope.context_projection,references}},resources,maxPromptChars,semanticVerifiedFiles:true,nativeScope,
    taskIndexBytes:prompt=>Buffer.byteLength(canonicalJSON({schema_version:2,task:prompt,...nativeScope,
      context_preparation:{path:join(absoluteDirectory,'context-preparation.json'),sha256:'0'.repeat(64)}}))});
  const bundle = { schema_version: 2, task:prepared.prompt, workspace: envelope.workspace, access: envelope.access,
    writable_paths: structuredClone(allowedPaths),
    context_preparation:{path:prepared.preparation_path,sha256:prepared.preparation_sha256},
    ...(resultSchema === undefined ? {} : { result_schema: structuredClone(resultSchema) }) };
  const bytes = Buffer.from(canonicalJSON(bundle), 'utf8');
  requireValue(bytes.length <= NATIVE_TASK_INDEX_LIMIT, 'NATIVE_TASK_INDEX_LIMIT',
    `Native task index exceeds ${NATIVE_TASK_INDEX_LIMIT} bytes; large inputs or schemas must be materialized separately`);
  await writeIdempotently(path, bytes);
  return { task_bundle_path: path, task_bundle_sha256: digest(bytes), task_sha256: prepared.prompt_sha256,
    task_bundle_bytes:bytes.length,verified_file_count: prepared.audit.verified_file_count, resource_count: prepared.audit.resource_count,
    bound_input_count:prepared.audit.bound_input_count,
    ...(itemPositions === null ? {} : { item_positions: structuredClone(itemPositions) }),
    allowed_paths: structuredClone(allowedPaths) };
}

// A pre-upgrade handoff may have published schema1 before its spawn was
// acknowledged. Rebuild its exact original plan to attest the current pinned
// envelope; replay never migrates the canonical file or recreates missing data.
async function retainLegacyNativeTask({directory,envelope,resources,resultSchema,allowedPaths,itemPositions,maxPromptChars,path,retained}) {
  const verifiedFiles=await verifiedInputFiles(envelope.inputs,envelope.workspace),rewrittenInputs=structuredClone(envelope.inputs??{});
  const verifiedItems=verifiedFiles.map(item=>{
    const local_path=join(directory,'verified',localMaterialName('input',item.sha256,item.resolved_path));
    for(const segments of item.reference_segments)replaceAt(rewrittenInputs,segments,local_path);
    return {...item,local_path};
  });
  const {entries,localAddresses}=await materializationPlan(rewrittenInputs,join(directory,'inputs'),envelope.workspace,
    {localFiles:verifiedItems.map(item=>item.local_path)});
  const compileEnvelope=structuredClone({...envelope,inputs:rewrittenInputs});
  for(const [name,address] of Object.entries(localAddresses))compileEnvelope.inputs[name]=address;
  for(const item of entries)compileEnvelope.inputs[item.name]=inputReferenceText(item);
  compileEnvelope.prompt_template=String(compileEnvelope.prompt_template??'').replace(
    'Resources listed below are logical identifiers, not filesystem paths. Use read_workflow_resource; cite resource IDs.',
    'Pinned resources are Host-materialized local files listed in this task bundle; read those exact local paths.');
  const task=compilePrompt(compileEnvelope,maxPromptChars),resourceItems=pinnedResourcePlan(resources,join(directory,'resources'));
  const expected={schema_version:1,task,workspace:envelope.workspace,access:envelope.access,writable_paths:structuredClone(allowedPaths),
    resources:resourceItems.map(({content,...item})=>item),
    verified_files:verifiedItems.map(({content,resolved_path,reference_segments,...item})=>item),
    ...(resultSchema===undefined?{}:{result_schema:structuredClone(resultSchema)})};
  requireValue(retained.equals(Buffer.from(canonicalJSON(expected))),'NODE_INPUT_MATERIALS_CONFLICT',
    'Historical native task differs from its exact pinned inputs, resources, scope or ordered result schema');
  const receipt={task_bundle_path:path,task_bundle_sha256:digest(retained),task_sha256:digest(Buffer.from(task)),
    task_bundle_bytes:retained.length,verified_file_count:verifiedFiles.length,resource_count:resourceItems.length,bound_input_count:entries.length,
    ...(itemPositions===null?{}:{item_positions:structuredClone(itemPositions)}),allowed_paths:structuredClone(allowedPaths)};
  await nativeTaskSemantic(receipt);
  for(const item of entries){
    const bytes=await projectionBytes(item.path,NATIVE_BUNDLE_LIMIT);
    requireValue(bytes?.equals(item.content),'NATIVE_TASK_FILE_CHANGED','Historical native bound input changed or is missing');
  }
  return receipt;
}

async function materializationPlan(inputs, directory, workspace, { includeTask = false, localFiles = [] } = {}) {
  const entries = [];
  const localAddresses = {};
  for (const [name, value] of Object.entries(inputs ?? {}).sort(([left], [right]) => left < right ? -1 : left > right ? 1 : 0)) {
    if (name === 'task' && !includeTask) continue;
    // *_json is a serialized input binding, never a local address. Decide its
    // representation before filesystem lookup; large JSON is not a pathname.
    const address = name.endsWith('_json') ? null : localFiles.includes(value) ? value : await existingLocalAddress(value, workspace);
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
 * @typedef {Object} HostMainContextPreparation
 * @property {string} prompt Exact projected first-turn context.
 * @property {string} preparation_path Durable schema_version:1 host_main_context contract.
 * @property {string} preparation_sha256 Digest of that contract's exact canonical bytes.
 * @property {Object} audit Counts, byte sizes, budgets and declared-only selection basis.
 */

/**
 * Prepare a fresh Main worker before any session exists. Small declared text
 * references and values appear once; executable and large bodies remain local.
 * @returns {Promise<HostMainContextPreparation>}
 */
export async function prepareHostMainContext({ directory, envelope, resources = [], maxPromptChars = 64_000, semanticVerifiedFiles = false, nativeScope, taskIndexBytes }) {
  requireValue(typeof directory === 'string' && isAbsolute(directory), 'NODE_INPUT_MATERIALS_PATH', 'Main context directory must be an absolute Host-selected path');
  requireValue(envelope && typeof envelope === 'object' && !Array.isArray(envelope), 'NODE_INPUT_MATERIALS_ENVELOPE', 'Projected Main envelope is required');
  const declared = envelope.resources ?? [];
  requireValue(Array.isArray(declared) && declared.every(path => typeof path === 'string') && new Set(declared).size === declared.length,
    'NODE_RESOURCE_DECLARATION', 'Main resources must be unique logical paths');
  requireValue(canonicalJSON([...declared].sort()) === canonicalJSON(resources.map(item => item.path).sort())
    && canonicalJSON([...(envelope.context_projection?.references ?? declared)].sort()) === canonicalJSON([...declared].sort()),
    'NODE_RESOURCE_DECLARATION', 'Main context must contain all and only declared resources');
  const root = resolve(directory), resourceDirectory = join(root, 'resources'), inputDirectory = join(root, 'inputs'), verifiedDirectory = join(root, 'verified');
  const resourceItems = pinnedResourcePlan([...resources].sort((a, b) => a.path < b.path ? -1 : a.path > b.path ? 1 : 0), resourceDirectory);
  const verified = await verifiedInputFiles(envelope.inputs, envelope.workspace);
  const rewrittenInputs = structuredClone(envelope.inputs ?? {});
  const verifiedItems = verified.map(item => {
    const local_path = join(verifiedDirectory, localMaterialName('input', item.sha256, item.resolved_path));
    for (const segments of item.reference_segments) replaceAt(rewrittenInputs, segments, local_path);
    return { ...item, local_path };
  });
  const { entries, localAddresses } = await materializationPlan(rewrittenInputs, inputDirectory, envelope.workspace,
    { includeTask: true, localFiles: verifiedItems.map(item => item.local_path) });
  let resourceBytes = 0, inputBytes = 0;
  const inline = (bytes, kind) => {
    const used = kind === 'resource' ? resourceBytes : inputBytes;
    if (bytes > HOST_MAIN_INLINE_BUDGETS.item_bytes || used + bytes > HOST_MAIN_INLINE_BUDGETS[`${kind}_bytes`]
      || resourceBytes + inputBytes + bytes > HOST_MAIN_INLINE_BUDGETS.total_bytes) return false;
    if (kind === 'resource') resourceBytes += bytes; else inputBytes += bytes;
    return true;
  };
  // Text-document suffixes are the bounded behavioral-reference lane. Never
  // inline executable bodies, binary data, or implicitly activate a Skill.
  const resourceManifest = resourceItems.map(({ content, ...item }) => ({ ...item,
    delivery: /\.(?:md|txt|rst)$/i.test(item.path) && inline(item.bytes, 'resource') ? 'inline' : 'file' }));
  const inputManifest = entries.map(({ content, path, ...item }) => inline(item.bytes, 'input')
    ? { ...item, delivery: 'inline' } : { ...item, path, delivery: 'file' });
  const verifiedManifest = verifiedItems.map(({content,resolved_path,reference_segments,...item}) => ({...item,
    delivery:/\.(?:md|txt|rst)$/i.test(item.path)&&inline(item.bytes,'input')?'inline':'file'}));
  const compileEnvelope = structuredClone(envelope);
  compileEnvelope.inputs = { ...rewrittenInputs, ...localAddresses };
  const compileCurrentProjection=()=>{
  for (let index = 0; index < entries.length; index++) {
    const item = entries[index];
    compileEnvelope.inputs[item.name] = inputManifest[index].delivery === 'file' ? inputReferenceText(item) : rewrittenInputs[item.name];
  }
  // Models need declared identifiers, usable addresses and admitted document
  // bodies. Integrity, byte counts and delivery diagnostics belong to the
  // committed preparation manifest; do not repeat them in every Main prompt.
  compileEnvelope.context_projection = { ...(compileEnvelope.context_projection ?? {}), references: resourceManifest.map((item, index) => ({ path:item.path,
    ...(item.delivery === 'inline' ? { content: new TextDecoder('utf-8', { fatal: true }).decode(resourceItems[index].content) } : {local_path:item.local_path}) })),
    verified_files:verifiedManifest.flatMap((item,index)=>item.delivery==='inline'?[{local_path:item.local_path,...(semanticVerifiedFiles?{}:{sha256:item.sha256,bytes:item.bytes}),
      content:new TextDecoder('utf-8',{fatal:true}).decode(verifiedItems[index].content)}]:[]) };
  compileEnvelope.prompt_template = String(compileEnvelope.prompt_template ?? '').replace(
    'Resources listed below are logical identifiers, not filesystem paths. Use read_workflow_resource; cite resource IDs.',
    'Declared pinned resources below contain complete text or an exact Host-prepared local file address.');
  return compilePrompt(compileEnvelope, maxPromptChars);
  };
  let prompt=compileCurrentProjection(),indexSpillCount=0;
  // Count the serialized whole index, including instructions, scope, schema
  // and JSON escapes. Inline body budgets alone do not bound that carrier.
  // Choose delivery before committing its manifest; never truncate content.
  if(taskIndexBytes){
    const candidates=[
      ...inputManifest.map((item,index)=>({item,bytes:item.bytes,path:entries[index].path,kind:'input'})),
      ...resourceManifest.map(item=>({item,bytes:item.bytes,kind:'resource'})),
      ...verifiedManifest.map(item=>({item,bytes:item.bytes,kind:'input'})),
    ].filter(({item})=>item.delivery==='inline').sort((a,b)=>b.bytes-a.bytes);
    while(taskIndexBytes(prompt)>NATIVE_TASK_INDEX_LIMIT){
      const candidate=candidates.shift();
      requireValue(candidate,'NATIVE_TASK_INDEX_LIMIT','Task instructions, scope and schema exceed the index limit even with all bound content in files');
      candidate.item.delivery='file';
      if(candidate.path)candidate.item.path=candidate.path;
      if(candidate.kind==='resource')resourceBytes-=candidate.bytes;else inputBytes-=candidate.bytes;
      indexSpillCount++;
      prompt=compileCurrentProjection();
    }
  }
  const audit = { basis: 'declared_bindings_and_pinned_resources', resource_count: resourceItems.length,
    resource_bytes: resourceItems.reduce((sum, item) => sum + item.bytes, 0),
    inline_resource_count: resourceManifest.filter(item => item.delivery === 'inline').length, inline_resource_bytes: resourceBytes,
    bound_input_count: entries.length + Object.keys(localAddresses).length,
    bound_input_bytes: entries.reduce((sum, item) => sum + item.bytes, 0),
    inline_input_count: inputManifest.filter(item => item.delivery === 'inline').length, inline_input_bytes: inputBytes,
    file_input_count: inputManifest.filter(item => item.delivery === 'file').length, local_address_count: Object.keys(localAddresses).length,
    verified_file_count: verifiedItems.length, verified_file_bytes: verifiedItems.reduce((sum, item) => sum + item.bytes, 0),
    inline_verified_file_count:verifiedManifest.filter(item=>item.delivery==='inline').length,
    inline_verified_file_bytes:verifiedManifest.filter(item=>item.delivery==='inline').reduce((sum,item)=>sum+item.bytes,0),
    prompt_bytes: Buffer.byteLength(prompt), inline_total_bytes: resourceBytes + inputBytes, budgets: HOST_MAIN_INLINE_BUDGETS,
    ...(indexSpillCount?{index_spill_count:indexSpillCount}:{}) };
  const contract = { schema_version: 1, kind: 'host_main_context', resources: resourceManifest, inputs: inputManifest,
    local_addresses: localAddresses, verified_files: verifiedManifest,
    prompt_sha256: digest(Buffer.from(prompt)), audit,...(nativeScope===undefined?{}:{native_scope:nativeScope}) };
  const preparation_path = join(root, 'context-preparation.json'), bytes = Buffer.from(canonicalJSON(contract));
  await ensureDirectory(root);
  const prior = await existingBytes(preparation_path);
  if (prior) requireValue(prior.equals(bytes), 'NODE_INPUT_MATERIALS_CONFLICT', `A different Main context preparation already exists: ${preparation_path}`);
  if (resourceItems.length) await ensureDirectory(resourceDirectory);
  if (inputManifest.some(item => item.delivery === 'file')) await ensureDirectory(inputDirectory);
  if (verifiedItems.length) await ensureDirectory(verifiedDirectory);
  for (const item of resourceItems) await writeIdempotently(item.local_path, item.content);
  for (const item of verifiedItems) await writeIdempotently(item.local_path, item.content);
  for (let index = 0; index < entries.length; index++) if (inputManifest[index].delivery === 'file') await writeIdempotently(entries[index].path, entries[index].content);
  await writeIdempotently(preparation_path, bytes);
  return { prompt, preparation_path, preparation_sha256: digest(bytes), prompt_sha256: contract.prompt_sha256, audit };
}

/** Current Main uses the same bounded declared context as an isolated Main worker.
 * The handoff owns scope and response schema; the prompt already owns resources.
 * Full preparation diagnostics remain in their committed hash-bound manifest.
 */
export async function materializeMainTaskBundle({directory,envelope,resources=[],maxPromptChars=64_000}) {
  const prepared=await prepareHostMainContext({directory,envelope,resources,maxPromptChars,
    taskIndexBytes:prompt=>Buffer.byteLength(canonicalJSON({schema_version:2,task:prompt,
      context_preparation:{path:join(resolve(directory),'context-preparation.json'),sha256:'0'.repeat(64)}}))});
  const contractBytes=await existingBytes(prepared.preparation_path);
  requireValue(contractBytes&&digest(contractBytes)===prepared.preparation_sha256,'NODE_INPUT_MATERIALS_CONFLICT',
    'Committed Main context metadata changed before task-bundle consumption');
  const bundle={schema_version:2,task:prepared.prompt,
    context_preparation:{path:prepared.preparation_path,sha256:prepared.preparation_sha256}};
  const bytes=Buffer.from(canonicalJSON(bundle));
  requireValue(bytes.length<=NATIVE_TASK_INDEX_LIMIT,'NATIVE_TASK_INDEX_LIMIT',
    `Main task index exceeds ${NATIVE_TASK_INDEX_LIMIT} bytes; large inputs or schemas must be materialized separately`);
  const path=join(resolve(directory),'task.json');
  await writeIdempotently(path,bytes);
  return {task_bundle_path:path,task_bundle_sha256:digest(bytes),task_sha256:prepared.prompt_sha256,
    task_bundle_bytes:bytes.length,verified_file_count:prepared.audit.verified_file_count,resource_count:prepared.audit.resource_count,
    bound_input_count:prepared.audit.bound_input_count};
}

/**
 * The dispatch receipt binds the original canonical index, including Host-only
 * diagnostics. Derive public bytes from that exact receipt, never from a model
 * digest or a regenerated envelope. Old receipts need no migration or rewrite.
 */
async function readTaskSemanticProjection(receipt) {
  const canonicalBytes = await projectionBytes(receipt.task_bundle_path, NATIVE_TASK_INDEX_LIMIT);
  requireValue(canonicalBytes && canonicalBytes.length <= NATIVE_TASK_INDEX_LIMIT
    && digest(canonicalBytes) === receipt.task_bundle_sha256,
  'MAIN_ORCHESTRATION_BUNDLE', 'The Host task bundle changed after dispatch');
  const bundle = JSON.parse(canonicalBytes.toString('utf8'));
  requireValue(bundle && [1, 2].includes(bundle.schema_version) && typeof bundle.task === 'string',
    'MAIN_ORCHESTRATION_BUNDLE', 'The Host task bundle has an unsupported semantic shape');
  let projection,metadata;
  if (bundle.schema_version === 2) {
    const preparation = bundle.context_preparation;
    requireValue(preparation && preparation.path === join(dirname(receipt.task_bundle_path), 'context-preparation.json')
      && /^[a-f0-9]{64}$/.test(preparation.sha256),
    'MAIN_ORCHESTRATION_BUNDLE', 'The Host task bundle lost its exact preparation binding');
    const metadataBytes = await projectionBytes(preparation.path, MAIN_PREPARATION_METADATA_LIMIT);
    requireValue(metadataBytes && digest(metadataBytes) === preparation.sha256,
      'MAIN_ORCHESTRATION_BUNDLE', 'The Host context preparation changed after dispatch');
    metadata = JSON.parse(metadataBytes.toString('utf8'));
    requireValue(metadata.schema_version === 1 && metadata.kind === 'host_main_context'
      && metadata.prompt_sha256 === digest(Buffer.from(bundle.task)),
    'MAIN_ORCHESTRATION_BUNDLE', 'The Host context preparation differs from its dispatched task');
    projection = { schema_version: 2, task: bundle.task };
  } else {
    // Historical schema1 Main receipts kept resource addresses beside the task.
    // Preserve those semantic addresses without exporting their integrity index.
    requireValue(Array.isArray(bundle.resources) && Array.isArray(bundle.verified_files),
      'MAIN_ORCHESTRATION_BUNDLE', 'The historical Main task bundle lost its declared materials');
    const addresses = items => items.map(item => {
      requireValue(typeof item.path === 'string' && typeof item.local_path === 'string',
        'MAIN_ORCHESTRATION_BUNDLE', 'The historical Main task bundle has an invalid material address');
      return { path: item.path, local_path: item.local_path };
    });
    projection = { schema_version: 1, task: bundle.task,
      resources: addresses(bundle.resources), verified_files: addresses(bundle.verified_files) };
  }
  return {bundle,projection,metadata};
}

export async function readMainTaskProjection(receipt, { materialize = false, artifactStore, runId, attemptId } = {}) {
  const {projection}=await readTaskSemanticProjection(receipt);
  const bytes = Buffer.from(canonicalJSON(projection));
  requireValue(bytes.length <= NATIVE_TASK_INDEX_LIMIT, 'NATIVE_TASK_INDEX_LIMIT',
    `Main semantic task index exceeds ${NATIVE_TASK_INDEX_LIMIT} bytes`);
  const inline = bytes.length <= MAIN_TASK_INLINE_LIMIT;
  if (inline) return { inline, task_bundle: projection };
  requireValue(artifactStore && typeof artifactStore.directory === 'function' && typeof artifactStore.saveArtifact === 'function'
    && typeof runId === 'string' && typeof attemptId === 'string',
  'MAIN_ORCHESTRATION_BUNDLE', 'The public Main task projection requires its Host-owned artifact store');
  const sha256 = digest(bytes), label = `orchestration-task-${attemptId}`;
  const path = join(artifactStore.directory(runId), `artifact-${label}-${sha256}.bin`);
  let publicBytes = await projectionBytes(path, NATIVE_TASK_INDEX_LIMIT);
  if (!publicBytes && materialize) {
    const saved = await artifactStore.saveArtifact(runId, label, bytes);
    requireValue(saved.artifact === basename(path) && saved.sha256 === sha256 && saved.bytes === bytes.length,
      'MAIN_ORCHESTRATION_BUNDLE', 'The public Main task projection was not published at its exact Host artifact address');
    publicBytes = await projectionBytes(path, NATIVE_TASK_INDEX_LIMIT);
  }
  requireValue(publicBytes?.equals(bytes), 'MAIN_ORCHESTRATION_BUNDLE',
    'The public Main task projection differs from its dispatched semantic bytes');
  return { inline, task_bundle_path: path, task_bundle_sha256: sha256 };
}

/** Complete declared semantic input bodies for a terminal Main handoff only.
 * Canonical task/preparation metadata stays private. No executable resources,
 * binary verified files or Host receipts are added to this public carrier. */
export async function readTerminalMainInputs(receipt){
  const {metadata}=await readTaskSemanticProjection(receipt);
  if(!metadata)return {};
  const semantic_inputs=Object.create(null),semantic_input_files=Object.create(null);let total=0;
  const root=resolve(dirname(receipt.task_bundle_path),'inputs');
  for(const item of metadata.inputs.filter(item=>item.delivery==='file')){
    requireValue(typeof item.name==='string'&&['json','text'].includes(item.format)&&typeof item.path==='string'
      &&Number.isSafeInteger(item.bytes)&&item.bytes>=0&&/^[a-f0-9]{64}$/.test(item.sha256),
      'MAIN_ORCHESTRATION_BUNDLE','Terminal semantic input lost its preparation binding');
    const path=resolve(item.path),prefix=root+(process.platform==='win32'?'\\':'/');
    const normalized=value=>process.platform==='win32'?value.toLowerCase():value;
    requireValue(normalized(path).startsWith(normalized(prefix)),'MAIN_ORCHESTRATION_BUNDLE','Terminal semantic input is outside its prepared input scope');
    const bytes=await projectionBytes(path,NATIVE_BUNDLE_LIMIT);
    requireValue(bytes&&bytes.length===item.bytes&&digest(bytes)===item.sha256,'MAIN_ORCHESTRATION_BUNDLE','Terminal semantic input changed after preparation');
    // The existing exact public file remains the explicit unsupported-size carrier.
    if(item.bytes>TERMINAL_MAIN_INPUT_BUDGET.item_bytes||total+item.bytes>TERMINAL_MAIN_INPUT_BUDGET.total_bytes){
      semantic_input_files[item.name]={path:item.path,format:item.format};continue;
    }
    const content=new TextDecoder('utf-8',{fatal:true}).decode(bytes);
    // Host delivers JSON as JSON, without making Main decode a JSON string
    // inside its JSON handoff. The exact canonical file/pin remains unchanged.
    semantic_inputs[item.name]={format:item.format,content:item.format==='json'?JSON.parse(content):content};total+=bytes.length;
  }
  return {...(Object.keys(semantic_inputs).length?{semantic_inputs}:{}),...(Object.keys(semantic_input_files).length?{semantic_input_files}:{})};
}

/** Rebind only Host-generated file descriptors in an inline public task.
 * The sealed canonical task and its sidecars remain unchanged. A file-delivered
 * index cannot be rewritten by attaching an unrelated inline value to a reply. */
export async function projectTerminalMainInputBindings(receipt,publicTask,carrier){
  requireValue(publicTask?.task_bundle&&carrier.semantic_inputs,'MAIN_ORCHESTRATION_BUNDLE','Terminal inline bindings need their public inline task and complete values');
  const {projection,metadata}=await readTaskSemanticProjection(receipt);
  requireValue(canonicalJSON(publicTask.task_bundle)===canonicalJSON(projection),'MAIN_ORCHESTRATION_BUNDLE','Terminal task differs from its verified public projection');
  let task=projection.task;
  for(const [name,value]of Object.entries(carrier.semantic_inputs)){
    const item=metadata?.inputs.find(item=>item.name===name&&item.delivery==='file');
    requireValue(item&&item.format===value.format,'MAIN_ORCHESTRATION_BUNDLE','Terminal inline input lost its exact declared descriptor');
    const reference=inputReferenceText(item),binding={delivery:'inline',value_path:['semantic_inputs',name,'content'],format:item.format};
    const quoted=canonicalJSON(reference);
    if(task.includes(quoted))task=task.split(quoted).join(canonicalJSON(binding));
    else {
      requireValue(task.includes(reference),'MAIN_ORCHESTRATION_BUNDLE','Terminal task lost its declared file descriptor');
      task=task.split(reference).join(canonicalJSON(binding));
    }
  }
  return {...publicTask,task_bundle:{...projection,task}};
}

/** Native scope and output schema come from the receipt-bound canonical index.
 * Legacy schema1 indices retain their semantic resource/file addresses. */
async function nativeTaskSemantic(receipt) {
  const {bundle,projection,metadata}=await readTaskSemanticProjection(receipt);
  requireValue(typeof bundle.workspace==='string'&&isAbsolute(bundle.workspace)&&typeof bundle.access==='string'
    &&Array.isArray(bundle.writable_paths)&&bundle.writable_paths.every(path=>typeof path==='string'),
    'NATIVE_TASK_BUNDLE','Native task bundle lost its exact scope');
  const semantic={...projection,workspace:bundle.workspace,access:bundle.access,writable_paths:bundle.writable_paths,
    ...(Object.hasOwn(bundle,'result_schema')?{result_schema:bundle.result_schema}:{})};
  const scope={workspace:bundle.workspace,access:bundle.access,writable_paths:bundle.writable_paths,
    ...(Object.hasOwn(bundle,'result_schema')?{result_schema:bundle.result_schema}:{})};
  if(metadata)requireValue(canonicalJSON(metadata.native_scope??null)===canonicalJSON(scope),'NATIVE_TASK_BUNDLE',
    'Native scope or ordered result schema differs from its committed context preparation');
  const materials=[
    {items:metadata?.resources??bundle.resources,itemLimit:LIMITS.resource,totalLimit:LIMITS.resources},
    {items:metadata?.verified_files??bundle.verified_files,itemLimit:NATIVE_FILE_LIMIT,totalLimit:NATIVE_BUNDLE_LIMIT},
    {items:metadata?.inputs.filter(item=>item.delivery==='file')??[],itemLimit:NATIVE_BUNDLE_LIMIT,totalLimit:NATIVE_BUNDLE_LIMIT},
  ];
  for(const group of materials){
    let materialBytes=0;
    for(const item of group.items){
    const path=item.local_path??item.path;
    requireValue(typeof path==='string'&&isAbsolute(path)&&Number.isSafeInteger(item.bytes)&&item.bytes>=0&&/^[a-f0-9]{64}$/.test(item.sha256),
      'NATIVE_TASK_BUNDLE','Native declared material lost its exact byte identity');
    // Resource and verified-file categories retain their existing bounds.
    requireValue(item.bytes<=group.itemLimit&&(materialBytes+=item.bytes)<=group.totalLimit,'NATIVE_TASK_BUNDLE_LIMIT',
      'Native declared materials exceed their bounded receipt limit');
    const retained=await projectionBytes(path,group.itemLimit);
    requireValue(retained&&retained.length===item.bytes&&digest(retained)===item.sha256,'NATIVE_TASK_FILE_CHANGED',
      'Native declared material changed after preparation');
    }
  }
  return semantic;
}

export async function readNativeTaskProjection(receipt,{materialize=false}={}) {
  const semantic=await nativeTaskSemantic(receipt);
  const bytes=Buffer.from(canonicalJSON(semantic));
  requireValue(bytes.length<=NATIVE_TASK_INDEX_LIMIT,'NATIVE_TASK_INDEX_LIMIT',`Native semantic task index exceeds ${NATIVE_TASK_INDEX_LIMIT} bytes`);
  if(bytes.length<=NATIVE_TASK_INLINE_LIMIT)return {inline:true,task_bundle:semantic};
  const path=join(dirname(receipt.task_bundle_path),'semantic-task.json');
  if(materialize)await writeIdempotently(path,bytes);
  const retained=await projectionBytes(path,NATIVE_TASK_INDEX_LIMIT);
  requireValue(retained?.equals(bytes),'NATIVE_TASK_BUNDLE','Native public task projection differs from its exact canonical semantic bytes');
  return {inline:false,task_bundle_path:path,task_bundle_sha256:digest(bytes)};
}

// Only projection consumption uses this reader. Keep unrelated materializer
// behavior unchanged. POSIX flags prevent a raced FIFO/link from blocking open;
// Windows lacks equivalent Node flags, so its guarantee is observed descriptor
// and pre/post path validation, not atomic no-reparse or nonblocking pipe open.
async function projectionBytes(path, limit) {
  let before;
  try {
    await noSymlinks(path);
    before = await lstat(path, { bigint: true });
  } catch (error) {
    if (error.code === 'ENOENT') return null;
    throw error;
  }
  const regular = info => info.isFile() && !info.isSymbolicLink() && info.size >= 0n && info.size <= BigInt(limit);
  const identical = (left, right) => ['dev', 'ino', 'mode', 'nlink', 'size', 'mtimeNs', 'ctimeNs', 'birthtimeNs']
    .every(key => left[key] === right[key]);
  requireValue(regular(before), 'MAIN_ORCHESTRATION_BUNDLE', 'Host task material is not a bounded regular file');
  let file, bytes, primary;
  try {
    const flags = filesystemConstants.O_RDONLY | (process.platform === 'win32' ? 0
      : filesystemConstants.O_NONBLOCK | filesystemConstants.O_NOFOLLOW);
    file = await open(path, flags);
    const opened = await file.stat({ bigint: true });
    requireValue(regular(opened) && identical(before, opened), 'MAIN_ORCHESTRATION_BUNDLE',
      'Host task material changed while opening its descriptor');
    const buffer = Buffer.alloc(Number(opened.size) + 1);
    let length = 0;
    while (length < buffer.length) {
      const { bytesRead } = await file.read(buffer, length, buffer.length - length, null);
      if (bytesRead === 0) break;
      length += bytesRead;
    }
    const after = await file.stat({ bigint: true });
    await noSymlinks(path);
    const retained = await lstat(path, { bigint: true }), settled = await file.stat({ bigint: true });
    requireValue(length === Number(opened.size) && regular(after) && regular(retained) && regular(settled)
      && identical(opened, after) && identical(after, retained) && identical(retained, settled),
    'MAIN_ORCHESTRATION_BUNDLE', 'Host task material changed during its bounded descriptor read');
    bytes = buffer.subarray(0, length);
  } catch (error) {
    primary = ['ENOENT', 'ELOOP'].includes(error.code)
      ? Object.assign(new Error('Host task material changed after its initial path check', { cause: error }),
        { code: 'MAIN_ORCHESTRATION_BUNDLE', details: { read_error_code: error.code } }) : error;
  }
  if (file) try { await file.close(); } catch (error) {
    primary = primary ? Object.assign(new AggregateError([primary, error], 'Host task material read and descriptor close failed'),
      { code: primary.code }) : error;
  }
  if (primary) throw primary;
  return bytes;
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
