import { lstat, mkdir, realpath } from 'node:fs/promises';
import { homedir, tmpdir } from 'node:os';
import { dirname, isAbsolute, join, parse, relative, resolve, sep } from 'node:path';

export function requireValue(condition, code, message, details = {}) {
  if (!condition) throw Object.assign(new Error(message), { code, ...details });
}

export function workflowId(id) {
  requireValue(typeof id === 'string' && /^[a-z0-9][a-z0-9._-]{0,63}$/.test(id), 'INVALID_WORKFLOW_ID', 'Workflow ID must be 1-64 lowercase letters, digits, dots, underscores or hyphens');
  return id;
}

// Prefix and suffix preserve legacy v6 IDs such as "con" or "name." on Windows.
export function packDirectory(root, id) { return join(root, `wf-${workflowId(id)}.pack`); }

export function resourcePath(path) {
  requireValue(typeof path === 'string' && path.length > 0 && path.length <= 512 && !/[\\:*?<>|"\x00-\x1f]/.test(path), 'INVALID_RESOURCE_PATH', 'Resource path must use portable relative forward-slash segments');
  const parts = path.split('/');
  requireValue(parts.every(part => part && part !== '.' && part !== '..' && !/[. ]$/.test(part) && !/^(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$)/i.test(part)), 'INVALID_RESOURCE_PATH', `Unsafe resource path: ${path}`);
  return path;
}

function containsOrEquals(root,path){
  const rel=relative(root,path);
  return rel==='' || (!rel.startsWith('..'+sep) && rel!=='..' && !isAbsolute(rel));
}

// The runtime-selected home and temporary directories are trust boundaries,
// not descendants controlled by a Workflow. Their operating-system ancestors
// may be aliases (macOS commonly exposes /var through /private/var). Check the
// boundary itself and every owned descendant without treating those external
// ancestor aliases as an in-store link.
function runtimeBoundary(absolute){
  const candidates=[resolve(tmpdir()),resolve(homedir())].filter(root=>containsOrEquals(root,absolute)).sort((a,b)=>b.length-a.length);
  return candidates[0] ?? parse(absolute).root;
}

export async function noSymlinks(path) {
  requireValue(isAbsolute(path), 'ABSOLUTE_PATH_REQUIRED', 'Store path must be absolute');
  const absolute = resolve(path);
  const root = runtimeBoundary(absolute);
  const boundary=await lstat(root);
  requireValue(!boundary.isSymbolicLink(), 'WORKFLOW_SYMLINK', `Symlink/reparse path is not allowed: ${root}`);
  let current = root;
  for (const part of relative(root, absolute).split(sep).filter(Boolean)) {
    current = join(current, part);
    const entry = await lstat(current);
    requireValue(!entry.isSymbolicLink(), 'WORKFLOW_SYMLINK', `Symlink/reparse path is not allowed: ${current}`);
  }
  return absolute;
}

export async function ensureDirectory(path) {
  const absolute = resolve(path);
  try { await noSymlinks(absolute); }
  catch (error) {
    if (error.code !== 'ENOENT') throw error;
    const parent = dirname(absolute);
    requireValue(parent !== absolute, 'STORE_ROOT_MISSING', 'Filesystem root is unavailable');
    await ensureDirectory(parent);
    try { await mkdir(absolute); } catch (mkdirError) { if (mkdirError.code !== 'EEXIST') throw mkdirError; }
    await noSymlinks(absolute);
  }
  requireValue((await lstat(absolute)).isDirectory(), 'NOT_DIRECTORY', `Expected directory: ${absolute}`);
  return absolute;
}

// Canonicalize Windows short names/casing only after rejecting every link in the
// supplied path. Missing suffixes are allowed for denied state not yet created.
// This never turns a symlink alias into an authorized path.
export async function canonicalNoLinks(path) {
  const absolute = resolve(path);
  try { await noSymlinks(absolute); return await realpath(absolute); }
  catch (error) {
    if (error.code !== 'ENOENT') throw error;
    const parent = dirname(absolute); requireValue(parent !== absolute, 'STORE_ROOT_MISSING', 'Filesystem root is unavailable');
    return join(await canonicalNoLinks(parent), relative(parent, absolute));
  }
}

export function insideRoot(root, path) {
  const rel = relative(resolve(root), resolve(path));
  requireValue(rel && !rel.startsWith('..' + sep) && rel !== '..' && !isAbsolute(rel), 'PATH_ESCAPE', 'Path leaves owned store root');
  return resolve(path);
}
