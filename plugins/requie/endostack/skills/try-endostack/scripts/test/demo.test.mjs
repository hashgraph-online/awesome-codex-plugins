// Keeps the try-endostack demo honest. The shipped app must show the bug with the
// traversal guard intact, the bundled naive fix must close the bug and open the
// hole, and a careful fix must do both jobs.
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { cpSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { after, test } from 'node:test';
import { fileURLToPath } from 'node:url';

const demo = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', '..', 'demo');
const scratch = mkdtempSync(path.join(tmpdir(), 'try-endostack-'));
after(() => rmSync(scratch, { recursive: true, force: true }));

function copyApp(label) {
  const dir = path.join(scratch, label);
  cpSync(path.join(demo, 'app'), dir, { recursive: true });
  return dir;
}

function applyPatch(dir, patchText) {
  const minus = patchText.split('\n').filter((l) => l.startsWith('-') && !l.startsWith('---')).map((l) => l.slice(1));
  const plus = patchText.split('\n').filter((l) => l.startsWith('+') && !l.startsWith('+++')).map((l) => l.slice(1));
  const file = path.join(dir, 'server.mjs');
  const src = readFileSync(file, 'utf8');
  assert.ok(src.includes(minus.join('\n')), 'naive-fix.patch no longer applies to server.mjs');
  writeFileSync(file, src.replace(minus.join('\n'), plus.join('\n')));
}

function run(dir, args) {
  const r = spawnSync(process.execPath, args, { cwd: dir, encoding: 'utf8' });
  return { code: r.status, out: r.stdout + r.stderr };
}

test('shipped app: bug present, traversal blocked, tests pass', () => {
  const dir = copyApp('baseline');
  const check = run(dir, [path.join(demo, 'check.mjs'), dir]);
  assert.equal(check.code, 0, check.out);
  assert.match(check.out, /Spaces bug .*present \(404\)/);
  assert.match(check.out, /Path traversal: blocked/);
  assert.equal(run(dir, ['--test']).code, 0);
});

test('naive fix: closes the bug, passes the existing tests, and leaks .env', () => {
  const dir = copyApp('naive');
  applyPatch(dir, readFileSync(path.join(demo, 'naive-fix.patch'), 'utf8'));
  const check = run(dir, [path.join(demo, 'check.mjs'), dir]);
  assert.equal(check.code, 1, check.out);
  assert.match(check.out, /Spaces bug .*fixed \(200\)/);
  assert.match(check.out, /Path traversal: VULNERABLE/);
  assert.equal(run(dir, ['--test']).code, 0, 'the naive fix must pass the shipped tests, or the demo shows nothing');
});

test('careful fix: closes the bug and keeps traversal blocked', () => {
  const dir = copyApp('careful');
  const file = path.join(dir, 'server.mjs');
  const src = readFileSync(file, 'utf8');
  const guarded = `    let name;
    try {
      name = decodeURIComponent(url.pathname.slice('/files/'.length));
    } catch {
      return send(res, 400, 'bad file name\\n');
    }
    const target = path.resolve(UPLOADS, name);
    if (name === '' || name.includes('\\0') || path.dirname(target) !== UPLOADS) {
      return send(res, 400, 'bad file name\\n');
    }
    try {
      const body = await readFile(target);`;
  const start = src.indexOf("    const name = url.pathname.slice('/files/'.length);");
  const end = src.indexOf('      const body = await readFile(path.join(UPLOADS, name));');
  assert.ok(start > 0 && end > start, 'server.mjs changed shape; update this test');
  const endLine = end + '      const body = await readFile(path.join(UPLOADS, name));'.length;
  writeFileSync(file, src.slice(0, start) + guarded + src.slice(endLine));
  const check = run(dir, [path.join(demo, 'check.mjs'), dir]);
  assert.equal(check.code, 0, check.out);
  assert.match(check.out, /Spaces bug .*fixed \(200\)/);
  assert.match(check.out, /Path traversal: blocked/);
});
