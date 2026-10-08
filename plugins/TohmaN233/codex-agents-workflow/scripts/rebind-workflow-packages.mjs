import { readFile, readdir, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { join } from 'node:path';
import { canonicalJSON } from '../control-plane/lib/workflow-revisions.mjs';
import { rebindWorkflowPackageHostToolIdentities } from '../control-plane/lib/workflow-host-tool-identity.mjs';

const directory = fileURLToPath(new URL('../examples/workflows/', import.meta.url));
const check = process.argv.slice(2);
if (check.some(arg => arg !== '--check') || check.length > 1) throw new Error('Usage: node rebind-workflow-packages.mjs [--check]');
const planned = [];
for (const name of (await readdir(directory)).filter(name => name.endsWith('.workflow-package.json')).sort()) {
  const path = join(directory, name), original = JSON.parse(await readFile(path, 'utf8'));
  planned.push({ name, path, ...rebindWorkflowPackageHostToolIdentities(original) });
}
if (check.length && planned.some(item => item.changes.length)) throw new Error('Shipped packages require built-in Host tool identity rebinding');
for (const item of planned) {
  if (item.changes.length) await writeFile(item.path, canonicalJSON(item.bundle) + '\n');
  console.log(`${item.name}: ${item.changes.length} rebound Host contracts`);
}
