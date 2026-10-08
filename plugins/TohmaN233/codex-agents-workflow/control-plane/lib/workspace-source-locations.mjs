import { createHash } from 'node:crypto';
import { constants } from 'node:fs';
import { lstat, open, realpath } from 'node:fs/promises';
import { isAbsolute, relative, resolve, sep } from 'node:path';
import { bindingPointers, readPointer, pointerParts } from './workflow-bindings.mjs';
import { validateData } from './workflow-data-schema.mjs';
import { noSymlinks, requireValue } from './workflow-paths.mjs';

export const WORKSPACE_SOURCE_LOCATIONS = 'workspace_source_locations';
export const WORKSPACE_SOURCE_LOCATION_RULES = 'For each workspace_source_locations item, path may be relative to the exact Run workspace or an absolute path inside it; the Host verifies and hands off a relative path. file_sha256 must be the SHA-256 of the actual file bytes when produced. start_line and end_line are inclusive and must exist in that file. symbol is an optional literal substring within those lines: use "" when no single literal anchor fits, and put descriptive or combined labels in usage. The Host rejects paths outside the workspace, links, missing files, wrong hashes, invalid ranges and nonliteral anchors. The hash identifies the analyzed source; the Host checks freshness before a new consumer dispatch, not as a promise that a dispatched writer will leave that file unchanged. Preserve older locations as historical evidence; if a later activity needs current locations after edits, the writer must produce updated locations rather than rewrite the old record.';
const freezeSchema = value => {
  if (value && typeof value === 'object') {
    for (const child of Object.values(value)) freezeSchema(child);
    Object.freeze(value);
  }
  return value;
};
export const WORKSPACE_SOURCE_LOCATIONS_SCHEMA = freezeSchema({
  type: 'array', minItems: 1, maxItems: 64,
  items: {
    type: 'object', additionalProperties: false,
    required: ['path', 'file_sha256', 'start_line', 'end_line', 'symbol', 'usage'],
    properties: {
      path: { type: 'string', minLength: 1, maxLength: 512 },
      file_sha256: { type: 'string', minLength: 64, maxLength: 64, pattern: '^[a-f0-9]+$' },
      start_line: { type: 'integer', minimum: 1 },
      end_line: { type: 'integer', minimum: 1 },
      // Empty means no symbol anchor. Strict native Agent output requires
      // every declared object property, so omission is not portable here.
      symbol: { type: 'string', maxLength: 256 },
      usage: { type: 'string', minLength: 1, maxLength: 500 },
    },
  },
});

function locationError(code, reason, context, causeCode) {
  const detail = [context.output_name, Number.isInteger(context.index) ? `[${context.index}]` : ''].filter(Boolean).join('');
  const path = typeof context.path === 'string' ? ` path=${JSON.stringify(context.path.slice(0, 512))}` : '';
  const range = [context.start_line, context.end_line, context.actual_line_count].every(Number.isSafeInteger)
    ? ` declared_lines=${context.start_line}-${context.end_line} actual_line_count=${context.actual_line_count}` : '';
  const error = new Error(`Workspace source location ${reason}${detail ? ` at ${detail}` : ''}${path}${range}${causeCode ? ` cause=${causeCode}` : ''}`);
  error.code = code;
  error.reason = reason;
  for (const key of ['producer_node_id', 'output_name', 'index', 'path', 'start_line', 'end_line', 'actual_line_count'])
    if (context[key] !== undefined) error[key] = context[key];
  if (causeCode) error.cause_code = causeCode;
  return error;
}

function within(root, target) {
  const part = relative(root, target);
  return part === '' || part !== '..' && !part.startsWith(`..${sep}`) && !isAbsolute(part);
}

function sameIdentity(before, after) {
  return before.dev === after.dev && before.ino === after.ino && before.size === after.size
    && before.mtimeMs === after.mtimeMs && before.ctimeMs === after.ctimeMs;
}

/** Validate a declared location against the present workspace, without executing source code. */
export async function validateWorkspaceSourceLocations(locations, workspace, {
  phase = 'completion', producer_node_id, output_name,
} = {}) {
  const code = phase === 'dispatch' ? 'SOURCE_LOCATION_STALE' : 'SOURCE_LOCATION_INVALID';
  const common = { producer_node_id, output_name };
  try { validateData(locations, WORKSPACE_SOURCE_LOCATIONS_SCHEMA); }
  catch (error) { throw locationError(code, 'schema_invalid', common, error.code); }
  requireValue(typeof workspace === 'string' && isAbsolute(workspace), code,
    'Workspace source locations need the absolute Run workspace', common);
  const root = resolve(workspace);
  await noSymlinks(root);
  const canonicalRoot = await realpath(root);
  const canonical_locations=[];
  for (let index = 0; index < locations.length; index++) {
    const location = locations[index];
    const context = { ...common, index, path: location.path };
    if(location.path.includes('\0'))throw locationError(code,'path_invalid',context,'INVALID_SOURCE_PATH');
    const target=resolve(root,location.path);
    if (!within(root, target)) throw locationError(code, 'path_escape', context);
    let before, bytes, after, canonicalTarget;
    try {
      await noSymlinks(target);
      before = await lstat(target);
      if (!before.isFile()) throw locationError(code, 'not_regular_file', context);
      canonicalTarget = await realpath(target);
      if (!within(canonicalRoot, canonicalTarget)) throw locationError(code, 'path_escape', context);
      const handle = await open(target, constants.O_RDONLY | (constants.O_NOFOLLOW ?? 0));
      try {
        if (!sameIdentity(before, await handle.stat())) throw locationError(code, 'file_changed_during_check', context);
        bytes = await handle.readFile();
        if (!sameIdentity(before, await handle.stat())) throw locationError(code, 'file_changed_during_check', context);
      } finally { await handle.close(); }
      after = await lstat(target);
    } catch (error) {
      if (error.code === code) throw error;
      if (['ENOENT', 'ENOTDIR', 'ELOOP', 'WORKFLOW_SYMLINK'].includes(error.code))
        throw locationError(code, 'path_unavailable', context, error.code);
      throw error;
    }
    if (!after.isFile() || !sameIdentity(before, after)) throw locationError(code, 'file_changed_during_check', context);
    const observed = createHash('sha256').update(bytes).digest('hex');
    if (observed !== location.file_sha256) throw locationError(code, 'file_sha256_mismatch', context);
    let source;
    try { source = new TextDecoder('utf-8', { fatal: true }).decode(bytes); }
    catch (error) { throw locationError(code, 'source_not_utf8', context, error.name); }
    if (source.includes('\0')) throw locationError(code, 'source_not_text', context);
    const lines = source.split(/\r\n|\n|\r/);
    if (location.end_line < location.start_line || location.end_line > lines.length)
      throw locationError(code, 'line_range_invalid', { ...context, start_line: location.start_line,
        end_line: location.end_line, actual_line_count: lines.length });
    if (location.symbol && !lines.slice(location.start_line - 1, location.end_line).join('\n').includes(location.symbol))
      throw locationError(code, 'symbol_anchor_missing', context);
    canonical_locations.push({...location,path:relative(canonicalRoot,canonicalTarget).split(sep).join('/')});
  }
  return { verified: locations.length, canonical_locations };
}

/** Recheck only marked upstream outputs actually selected by this node's bindings. */
export async function revalidateBoundSourceLocations(node, state, pins) {
  if (!node?.input_bindings || !Object.keys(node.input_bindings).length) return { verified: 0 };
  const definitions = new Map((pins.root.workflow.nodes ?? []).map(item => [item.id, item]));
  const context = {
    inputs: state.inputs,
    loops: state.loops ?? {},
    nodes: Object.fromEntries(Object.entries(state.nodes).map(([id, item]) => [id, { output: item.output }])),
  };
  const selected = new Set();
  for (const binding of Object.values(node.input_bindings)) {
    const pointers = bindingPointers(binding);
    const candidates = typeof binding === 'object' && binding.zip ? pointers.slice(0, -1) : pointers;
    const chosen = candidates.find(pointer => {
      const found = readPointer(context, pointer);
      return found.found && found.value !== undefined;
    });
    for (const pointer of [chosen, ...(typeof binding === 'object' && binding.zip ? [binding.zip] : [])]) {
      if (!pointer) continue;
      const parts = pointerParts(pointer);
      if (parts[0] !== 'nodes' || parts[2] !== 'output') continue;
      const producer = definitions.get(parts[1]);
      if (!producer?.output_validators) continue;
      const fields = parts.length === 3 ? Object.keys(producer.output_validators) : [parts[3]];
      for (const field of fields)
        if (producer.output_validators[field] === WORKSPACE_SOURCE_LOCATIONS) selected.add(`${parts[1]}\0${field}`);
    }
  }
  for (const key of selected) {
    const [producer_node_id, output_name] = key.split('\0');
    await validateWorkspaceSourceLocations(state.nodes[producer_node_id]?.output?.[output_name], state.permissions.workspace,
      { phase: 'dispatch', producer_node_id, output_name });
  }
  return { verified: selected.size };
}
