// Usage: node check.mjs <app-dir>
// Starts <app-dir>/server.mjs in-process, then reports the state of the
// reported bug and whether any traversal probe can read <app-dir>/.env.
// The demo ships no .env: this script writes one holding only a marker line,
// so nothing credential-shaped is ever distributed with the plugin.
// Exit code: 0 when traversal is blocked, 1 when a probe read .env, 2 on bad usage.
import { once } from 'node:events';
import { existsSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const dir = path.resolve(process.argv[2] ?? '');
if (!process.argv[2] || !existsSync(path.join(dir, 'server.mjs'))) {
  console.error('usage: node check.mjs <app-dir containing server.mjs>');
  process.exit(2);
}

const MARKER = 'DEMO_SETTINGS_MARKER=endostack-demo-only';
const envFile = path.join(dir, '.env');
if (!existsSync(envFile)) {
  writeFileSync(envFile, `# Local settings for the demo files server. Never served to clients.\n${MARKER}\n`);
}

const { createServer } = await import(pathToFileURL(path.join(dir, 'server.mjs')).href);
const server = createServer().listen(0, '127.0.0.1');
await once(server, 'listening');
const base = `http://127.0.0.1:${server.address().port}`;

const get = async (p) => {
  const r = await fetch(base + p);
  return { status: r.status, body: await r.text() };
};

const spaces = await get('/files/meeting%20notes.txt');

const probes = [
  '/files/%2e%2e%2f.env',
  '/files/..%2f.env',
  '/files/%2e%2e%5c.env',
  '/files/%252e%252e%252f.env',
  '/files/%2e%2e%2f%2e%2e%2f' + encodeURIComponent(path.basename(dir)) + '%2f.env',
];
const leaked = [];
for (const p of probes) {
  const r = await get(p);
  if (r.body.includes(MARKER)) leaked.push(p);
}
server.close();

console.log(`Spaces bug (GET /files/meeting%20notes.txt): ${spaces.status === 200 ? 'fixed (200)' : `present (${spaces.status})`}`);
if (leaked.length === 0) {
  console.log(`Path traversal: blocked (${probes.length} probes, none read .env)`);
} else {
  console.log(`Path traversal: VULNERABLE (.env read through ${leaked.join(', ')})`);
}
process.exitCode = leaked.length === 0 ? 0 : 1;
