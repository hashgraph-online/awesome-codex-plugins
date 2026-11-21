import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const helper = fileURLToPath(new URL('../helpers/gate-sandbox.cjs', import.meta.url));
for (const shape of ['bin directory symlink', 'ps file symlink', 'ps file hard link']) {
  test(`Gate shim creation preserves the target of a preexisting ${shape}`, t => {
    const temp = fs.realpathSync(fs.mkdtempSync('/tmp/ship-gate-safety-'));
    const repo = fs.realpathSync(fs.mkdtempSync('/tmp/suede-gate-safety-'));
    t.after(() => { fs.rmSync(temp, { recursive: true, force: true }); fs.rmSync(repo, { recursive: true, force: true }); });
    const git = spawnSync('git', ['init', '-q', repo], { encoding: 'utf8' });
    assert.equal(git.status, 0, git.stderr);
    const outside = path.join(repo, 'outside');
    fs.mkdirSync(outside);
    const target = path.join(outside, 'ps');
    fs.writeFileSync(target, 'PRESERVE');
    const originalMode = fs.statSync(target).mode;
    if (shape === 'bin directory symlink') fs.symlinkSync(outside, path.join(temp, 'bin'), 'dir');
    else {
      fs.mkdirSync(path.join(temp, 'bin'));
      if (shape === 'ps file symlink') fs.symlinkSync(target, path.join(temp, 'bin', 'ps'));
      else fs.linkSync(target, path.join(temp, 'bin', 'ps'));
    }
    // This regression checks the filesystem work before sandbox launch. Hosts
    // without macOS sandbox-exec may reject the final launch; that is separate.
    const result = spawnSync(process.execPath, [helper, repo, temp, 'true', 'W10='], { encoding: 'utf8' });
    assert.equal(result.error, undefined);
    assert.equal(fs.readFileSync(target, 'utf8'), 'PRESERVE', 'shim setup must not follow attacker-controlled paths');
    assert.equal(fs.statSync(target).mode, originalMode);
    const shimDirs = fs.readdirSync(temp).filter(name => name.startsWith('gate-bin-'));
    assert.equal(shimDirs.length, 1, result.stderr);
    const shimDir = path.join(temp, shimDirs[0]);
    assert.equal(fs.lstatSync(shimDir).isSymbolicLink(), false);
    assert.equal(fs.statSync(shimDir).mode & 0o777, 0o700);
    const shim = path.join(shimDir, 'ps');
    assert.equal(fs.lstatSync(shim).isFile(), true);
    assert.equal(fs.statSync(shim).nlink, 1);
    assert.equal(fs.statSync(shim).mode & 0o777, 0o755);
    assert.match(fs.readFileSync(shim, 'utf8'), /^#!\/usr\/bin\/env python3/);
  });
}
