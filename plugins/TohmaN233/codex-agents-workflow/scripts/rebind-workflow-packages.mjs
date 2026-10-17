import { readFile, readdir, writeFile } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import { canonicalJSON } from '../control-plane/lib/workflow-revisions.mjs';
import { rebindWorkflowPackageHostToolIdentities } from '../control-plane/lib/workflow-host-tool-identity.mjs';

const [directoryArg, ...flags] = process.argv.slice(2);
if (!directoryArg || directoryArg.startsWith('--') || flags.some(arg => arg !== '--check') || flags.length > 1)
  throw new Error('Usage: node rebind-workflow-packages.mjs <package-directory> [--check]');
const directory = resolve(directoryArg), check = flags.includes('--check');
const planned = [];
for (const name of (await readdir(directory)).filter(name => name.endsWith('.workflow-package.json')).sort()) {
  const path = join(directory, name), original = JSON.parse(await readFile(path, 'utf8'));
  planned.push({ name, path, ...rebindWorkflowPackageHostToolIdentities(original) });
}
if (check && planned.some(item => item.changes.length)) throw new Error('Selected packages require built-in Host tool identity rebinding');
for (const item of planned) {
  if (item.changes.length) await writeFile(item.path, canonicalJSON(item.bundle) + '\n');
  console.log(`${item.name}: ${item.changes.length} rebound Host contracts`);
}
