import { resolve } from 'node:path';
import { canonicalNoLinks } from '../workflow-paths.mjs';

// Windows namespace prefixes change spelling, not filesystem identity. Strip
// them before ancestor validation, preserving an extended UNC path's server.
function localPath(path) {
  if (process.platform !== 'win32' || !path.startsWith('\\\\?\\')) return path;
  return path.slice(4, 8).toUpperCase() === 'UNC\\' ? '\\\\' + path.slice(8) : path.slice(4);
}

export async function canonicalSessionPath(path, home) {
  return {
    root: await canonicalNoLinks(resolve(localPath(home), 'sessions')),
    path: await canonicalNoLinks(localPath(path)),
  };
}
