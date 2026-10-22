import { randomUUID, randomBytes, createHmac } from 'node:crypto';
import { open, lstat } from 'node:fs/promises';
import { constants } from 'node:fs';
import { dirname, join, resolve, relative, isAbsolute, sep } from 'node:path';
import { canonicalJSON } from '../workflow-revisions.mjs';
import { ensureDirectory, noSymlinks, canonicalNoLinks, requireValue } from '../workflow-paths.mjs';
import { validateWorkflowMcpTransport } from '../workflow-call-policy.mjs';

export const PREPARED_STARTUP_LIMIT = 1024 * 1024;
export const STARTUP_REFERENCE_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
const rootFor = configPath => join(dirname(resolve(configPath)), 'workflow-preparations');
// POSIX also rejects link substitution at open and cannot block on a raced FIFO.
// Windows Node exposes neither flag; the fresh descriptor/path checks remain
// authoritative and must pass before any stored data is consumed there.
const READ_FLAGS=process.platform==='win32'?constants.O_RDONLY:
  constants.O_RDONLY|constants.O_NOFOLLOW|constants.O_NONBLOCK;
const fail = message => requireValue(false, 'WORKFLOW_PREPARATION_RECORD', message);
const same = (a,b) => ['dev','ino','size','mtimeMs','ctimeMs','nlink'].every(key => a[key] === b[key]);
function regular(info, limit) {
  requireValue(info.isFile() && info.nlink === 1 && info.size > 0 && info.size <= limit,
    'WORKFLOW_PREPARATION_RECORD', 'Preparation storage must be one bounded regular file');
}

// Bound actual bytes at the opened handle, then freshly compare both pathname
// and handle. No readFile allocation can grow with a concurrent file append.
async function readBounded(path, limit) {
  await noSymlinks(path); const before = await lstat(path); regular(before,limit);
  const handle = await open(path,READ_FLAGS);
  let failure;
  try {
    const opened = await handle.stat(); regular(opened,limit);
    requireValue(same(before,opened),'WORKFLOW_PREPARATION_RECORD','Preparation file changed before open');
    const buffer = Buffer.alloc(limit+1); let length = 0;
    while(length < buffer.length) {
      const read = await handle.read(buffer,length,buffer.length-length,length);
      if (!read.bytesRead) break;
      length += read.bytesRead;
    }
    const after = await handle.stat(); await noSymlinks(path); const named = await lstat(path);
    regular(after,limit); regular(named,limit);
    requireValue(length===before.size && length<=limit && same(before,after) && same(after,named),
      'WORKFLOW_PREPARATION_RECORD','Preparation file changed while reading');
    return buffer.subarray(0,length);
  } catch(error) { failure=error; throw error; }
  finally { try { await handle.close(); } catch(error) {
    if(failure)throw new AggregateError([failure,error],'Preparation read and handle close failed');
    throw error;
  } }
}
async function writeExclusive(path, bytes) {
  await noSymlinks(dirname(path));
  const handle = await open(path,'wx',0o600);
  let failure;
  try { await handle.writeFile(bytes); await handle.sync(); }
  catch(error) { failure=error; throw error; }
  finally { try { await handle.close(); } catch(error) {
    if(failure)throw new AggregateError([failure,error],'Preparation write and handle close failed');
    throw error;
  } }
  const actual=await readBounded(path,bytes.length);
  requireValue(actual.equals(bytes),'WORKFLOW_PREPARATION_RECORD','Preparation write changed before publication');
}
async function sealKey(root, create) {
  const path=join(root,'seal-key');
  if(create) {
    try { await writeExclusive(path,randomBytes(32)); }
    catch(error) { if(error.code!=='EEXIST'||error.path!==path)throw error; }
  }
  const bytes=await readBounded(path,32);
  requireValue(bytes.length===32,'WORKFLOW_PREPARATION_RECORD','Preparation seal key has an invalid size');
  return bytes;
}
const seal = (key,payload) => createHmac('sha256',key).update(canonicalJSON(payload)).digest('hex');
async function outsideWorkspace(root,args) {
  if(args.workspace===undefined)return;
  requireValue(typeof args.workspace==='string'&&isAbsolute(args.workspace),'WORKFLOW_PREPARATION_WORKSPACE',
    'Preparation requires an absolute business workspace');
  const workspace=await canonicalNoLinks(args.workspace),owned=await canonicalNoLinks(root),rel=relative(workspace,owned);
  requireValue(rel!==''&&(rel==='..'||rel.startsWith('..'+sep)||isAbsolute(rel)),
    'WORKFLOW_PREPARATION_WORKSPACE','Host preparation storage must lie outside the business workspace');
}
export async function createPreparedStartup(configPath,args,{typed=false,initialOutput,invocationTransport='code_mode'}={}) {
  validateWorkflowMcpTransport(invocationTransport);
  const startup_reference=randomUUID();
  const payload=JSON.parse(canonicalJSON({schema_version:2,startup_reference,args,typed,invocation_transport:invocationTransport,...(typed?{initial_output:initialOutput}:{})}));
  await outsideWorkspace(rootFor(configPath),payload.args);
  const root=await ensureDirectory(rootFor(configPath));
  await outsideWorkspace(root,payload.args);
  const key=await sealKey(root,true);
  const bytes=Buffer.from(canonicalJSON({payload,seal:seal(key,payload)}));
  requireValue(bytes.length<=PREPARED_STARTUP_LIMIT,'WORKFLOW_PREPARATION_RECORD','Preparation exceeds its bounded storage limit');
  await writeExclusive(join(root,`${startup_reference}.json`),bytes);
  return startup_reference;
}
export async function resolvePreparedStartup(configPath,{startup_reference,...submission},{invocationTransport='code_mode'}={}) {
  validateWorkflowMcpTransport(invocationTransport);
  requireValue(typeof startup_reference==='string' && STARTUP_REFERENCE_PATTERN.test(startup_reference),
    'WORKFLOW_PREPARATION_REFERENCE','Startup reference must be an exact Host UUID');
  const root=rootFor(configPath),bytes=await readBounded(join(root,`${startup_reference}.json`),PREPARED_STARTUP_LIMIT);
  let record;
  try { record=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes)); }
  catch { fail('Preparation record is not valid UTF-8 JSON'); }
  requireValue(record && canonicalJSON(record)===bytes.toString('utf8') && typeof record.seal==='string'
    && /^[a-f0-9]{64}$/.test(record.seal) && Object.keys(record).sort().join(',')==='payload,seal',
    'WORKFLOW_PREPARATION_RECORD','Preparation record is not an exact canonical sealed envelope');
  const payload=record.payload;
  requireValue(payload && [1,2].includes(payload.schema_version) && payload.startup_reference===startup_reference
    && typeof payload.typed==='boolean' && payload.args && typeof payload.args==='object'
    && Object.keys(payload).sort().join(',')===['args',...(payload.typed?['initial_output']:[]),...(payload.schema_version===2?['invocation_transport']:[]),'schema_version','startup_reference','typed'].join(',')
    && record.seal===seal(await sealKey(root,false),payload),
    'WORKFLOW_PREPARATION_RECORD','Preparation identity or exact data seal is invalid');
  const retainedTransport=payload.schema_version===1?'code_mode':validateWorkflowMcpTransport(payload.invocation_transport);
  requireValue(retainedTransport===invocationTransport,'WORKFLOW_PREPARATION_TRANSPORT',
    'Prepared startup belongs to a different launcher-bound invocation transport');
  await outsideWorkspace(root,payload.args);
  requireValue(Object.keys(submission).every(key=>key==='initial_output'),
    'WORKFLOW_PREPARATION_FIELDS','Prepared startup accepts semantic output only');
  requireValue(payload.typed ? !Object.hasOwn(submission,'initial_output') : Object.hasOwn(submission,'initial_output'),
    'WORKFLOW_PREPARATION_SEMANTIC','Typed preparation already owns its semantic output; untyped preparation requires one fresh output');
  return {...payload.args,initial_output:payload.typed?payload.initial_output:submission.initial_output};
}
