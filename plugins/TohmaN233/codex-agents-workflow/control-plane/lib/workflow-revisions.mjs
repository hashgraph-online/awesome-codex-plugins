import { createHash } from 'node:crypto';
import { requireValue, resourcePath } from './workflow-paths.mjs';

export const LIMITS = Object.freeze({ definition: 1024 * 1024, resource: 8 * 1024 * 1024, resources: 64 * 1024 * 1024, files: 2048 });
export const digest = bytes => createHash('sha256').update(bytes).digest('hex');

export function canonicalJSON(value, depth = 0) {
  requireValue(depth < 100, 'JSON_DEPTH', 'Workflow JSON is too deeply nested');
  if (value === null || typeof value === 'boolean' || typeof value === 'string') return JSON.stringify(value);
  if (typeof value === 'number') { requireValue(Number.isFinite(value), 'INVALID_JSON', 'Numbers must be finite'); return JSON.stringify(value); }
  if (Array.isArray(value)) return '[' + Array.from({ length: value.length }, (_, index) => {
    requireValue(Object.hasOwn(value, index), 'INVALID_JSON', 'Sparse arrays are not JSON values');
    return canonicalJSON(value[index], depth + 1);
  }).join(',') + ']';
  requireValue(value && typeof value === 'object' && [Object.prototype, null].includes(Object.getPrototypeOf(value)), 'INVALID_JSON', 'Workflow data must contain only JSON values');
  return '{' + Object.keys(value).sort().map(key => JSON.stringify(key) + ':' + canonicalJSON(value[key], depth + 1)).join(',') + '}';
}

export function revisionHash(snapshot) { return digest(canonicalJSON(snapshot)); }

export function prepareResources(resources = {}) {
  requireValue(resources && typeof resources === 'object' && !Array.isArray(resources), 'INVALID_RESOURCES', 'Resources must map relative paths to bytes');
  const entries = Object.entries(resources).sort(([a], [b]) => a < b ? -1 : a > b ? 1 : 0);
  requireValue(entries.length <= LIMITS.files, 'RESOURCE_LIMIT', 'Too many resource files');
  const seen = new Set(); const blobs = new Map(); const manifest = [];
  let total = 0;
  for (const [path, value] of entries) {
    resourcePath(path);
    const key = path.normalize('NFC').toLowerCase();
    requireValue(!seen.has(key), 'RESOURCE_COLLISION', `Resource paths collide across platforms: ${path}`);
    requireValue(![...seen].some(name => name.startsWith(key + '/') || key.startsWith(name + '/')), 'RESOURCE_COLLISION', `Resource file/directory paths collide: ${path}`);
    seen.add(key);
    requireValue(typeof value === 'string' || value instanceof Uint8Array, 'INVALID_RESOURCE', `Resource must be text or bytes: ${path}`);
    const bytes = Buffer.from(value);
    total += bytes.length;
    requireValue(bytes.length <= LIMITS.resource && total <= LIMITS.resources, 'RESOURCE_LIMIT', `Resource size limit exceeded: ${path}`);
    const sha256 = digest(bytes);
    blobs.set(sha256, bytes);
    manifest.push({ path, sha256, bytes: bytes.length });
  }
  return { manifest, blobs };
}

export function validateManifest(manifest) {
  requireValue(Array.isArray(manifest) && manifest.length <= LIMITS.files, 'INVALID_MANIFEST', 'Invalid resource manifest');
  const names = new Set(); let total = 0;
  for (const item of manifest) {
    resourcePath(item.path);
    const key = item.path.normalize('NFC').toLowerCase();
    requireValue(!names.has(key) && ![...names].some(name => name.startsWith(key + '/') || key.startsWith(name + '/')), 'RESOURCE_COLLISION', 'Duplicate or overlapping resource path'); names.add(key);
    requireValue(/^[a-f0-9]{64}$/.test(item.sha256) && Number.isSafeInteger(item.bytes) && item.bytes >= 0 && item.bytes <= LIMITS.resource, 'INVALID_MANIFEST', 'Invalid resource digest or size');
    total += item.bytes;
  }
  requireValue(total <= LIMITS.resources, 'RESOURCE_LIMIT', 'Total resource limit exceeded');
}
