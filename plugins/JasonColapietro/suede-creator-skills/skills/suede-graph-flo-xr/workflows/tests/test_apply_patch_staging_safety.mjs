import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const helper = fileURLToPath(new URL('../helpers/apply-patch.cjs', import.meta.url));
const checksum = text => {
  let hash = 0x811c9dc5;
  for (let i = 0; i < text.length; i++) hash = Math.imul(hash ^ text.charCodeAt(i), 0x01000193);
  return (hash >>> 0).toString(16).padStart(8, '0');
};
const patch = 'diff --git a/example.txt b/example.txt\n--- a/example.txt\n+++ b/example.txt\n@@ -1 +1 @@\n-before\n+after\n';
function fixture(t) {
  const stagingRoot = fs.mkdtempSync('/tmp/ship-staging-safety-');
  const root = fs.mkdtempSync('/tmp/suede-patch-safety-');
  t.after(() => { fs.rmSync(stagingRoot, { recursive: true, force: true }); fs.rmSync(root, { recursive: true, force: true }); });
  const git = spawnSync('git', ['init', '-q', root], { encoding: 'utf8' });
  assert.equal(git.status, 0, git.stderr);
  fs.writeFileSync(path.join(root, 'example.txt'), 'before\n');
  const staging = path.join(stagingRoot, 'apply-patch.b64');
  const encoded = Buffer.from(patch).toString('base64');
  const run = (...args) => spawnSync(process.execPath, [helper, root, ...args], { encoding: 'utf8' });
  return { root, stagingRoot, staging, encoded, run };
}
for (const linkType of ['symbolic', 'hard']) {
  for (const mode of ['--start', '--append', '--apply']) {
    test(`${mode} rejects a ${linkType}-linked staging file before touching its target or applying its bytes`, t => {
      const f = fixture(t);
      const target = path.join(f.root, 'outside-staging.txt');
      fs.writeFileSync(target, f.encoded);
      if (linkType === 'symbolic') fs.symlinkSync(target, f.staging); else fs.linkSync(target, f.staging);
      const args = mode === '--start' ? [mode, f.stagingRoot] : mode === '--append'
        ? [mode, f.stagingRoot, String(f.encoded.length), checksum('YQ=='), 'YQ==']
        : [mode, f.stagingRoot, String(f.encoded.length), checksum(f.encoded)];
      const result = f.run(...args);
      assert.notEqual(result.status, 0, 'linked staging must be refused');
      assert.match(result.stderr, /staging.*(?:regular|link|safe)|(?:regular|link|safe).*staging/i);
      assert.equal(fs.readFileSync(target, 'utf8'), f.encoded);
      assert.equal(fs.readFileSync(path.join(f.root, 'example.txt'), 'utf8'), 'before\n');
    });
  }
}
test('chunk staging still checks offsets/checksums and applies the exact completed patch', t => {
  const f = fixture(t);
  assert.equal(f.run('--start', f.stagingRoot).status, 0);
  assert.equal(fs.statSync(f.staging).mode & 0o777, 0o600);
  const split = Math.floor(f.encoded.length / 2);
  const first = f.encoded.slice(0, split), second = f.encoded.slice(split);
  assert.equal(f.run('--append', f.stagingRoot, '0', checksum(first), first).status, 0);
  assert.notEqual(f.run('--append', f.stagingRoot, '0', checksum(second), second).status, 0);
  assert.notEqual(f.run('--append', f.stagingRoot, String(split), '00000000', second).status, 0);
  assert.equal(fs.readFileSync(f.staging, 'utf8'), first);
  assert.equal(f.run('--append', f.stagingRoot, String(split), checksum(second), second).status, 0);
  assert.notEqual(f.run('--apply', f.stagingRoot, String(f.encoded.length + 1), checksum(f.encoded)).status, 0);
  const applied = f.run('--apply', f.stagingRoot, String(f.encoded.length), checksum(f.encoded));
  assert.equal(applied.status, 0, applied.stderr);
  assert.equal(fs.readFileSync(path.join(f.root, 'example.txt'), 'utf8'), 'after\n');
  assert.equal(fs.existsSync(f.staging), false);
});
test('legacy one-shot application and resetting a regular staging file remain supported', t => {
  const f = fixture(t);
  fs.writeFileSync(f.staging, 'obsolete');
  assert.equal(f.run('--start', f.stagingRoot).status, 0);
  assert.equal(fs.readFileSync(f.staging, 'utf8'), '');
  const applied = f.run(f.encoded);
  assert.equal(applied.status, 0, applied.stderr);
  assert.equal(fs.readFileSync(path.join(f.root, 'example.txt'), 'utf8'), 'after\n');
});
