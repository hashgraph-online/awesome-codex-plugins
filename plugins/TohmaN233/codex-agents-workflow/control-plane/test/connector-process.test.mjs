import assert from 'node:assert/strict';
import { fork, spawn } from 'node:child_process';
import { once } from 'node:events';
import { mkdtemp, readFile, writeFile, utimes } from 'node:fs/promises';
import { join } from 'node:path';
import test from 'node:test';
import { tmpdir } from './physical-tempdir.mjs';

async function compete(t, fields) {
  const root = await mkdtemp(join(tmpdir(), 'workflow-process-lock-'));
  const statePath = join(root, 'tasks.json');
  const children = fields.map(() => fork(new URL('./fixtures/store-process.mjs', import.meta.url), [statePath], { silent: true, windowsHide: true }));
  t.after(() => { for (const child of children) if (child.exitCode === null) child.kill(); });
  const ready = await Promise.all(children.map(child => once(child, 'message').then(([m]) => m)));
  assert.equal(new Set(ready.map(m => m.pid)).size, fields.length);
  assert(ready.every(m => m.ready));
  // All independent processes initialized the same empty snapshot before release.
  const results = children.map(child => once(child, 'message').then(([m]) => m));
  const exits = children.map(child => once(child, 'exit'));
  children.forEach((child, index) => child.send(fields[index]));
  const replies = await Promise.all(results);
  for (const [code] of await Promise.all(exits)) assert.equal(code, 0);
  const stored = JSON.parse(await readFile(statePath, 'utf8'));
  return { replies, stored };
}

test('independent OS processes preserve every acknowledged record after simultaneous creation', { timeout: 10000 }, async t => {
  const { replies, stored } = await compete(t, [
    { task_id: 'a', state: 'completed', workspace: 'a' },
    { task_id: 'b', state: 'completed', workspace: 'b' },
  ]);
  assert(replies.every(r => r.ok), JSON.stringify(replies));
  assert.deepEqual(stored.tasks.map(t => t.task_id).sort(), ['a', 'b']);
});
for (const pair of [['grok_acp', 'grok_acp'], ['cursor_cdp', 'cursor_cdp'], ['grok_acp', 'cursor_cdp']]) {
  test(`OS process reservation competition ${pair.join('/')} has one winner and no partial loser`, { timeout: 10000 }, async t => {
    const { replies, stored } = await compete(t, pair.map((connector, index) => ({ task_id: 'task-' + index, connector, workspace: 'same-canonical-workspace' })));
    assert.equal(replies.filter(r => r.ok).length, 1, JSON.stringify(replies));
    assert.equal(replies.find(r => !r.ok).code, 'CONNECTOR_BUSY');
    assert.equal(stored.tasks.length, 1);
    assert.equal(stored.tasks[0].task_id, replies.find(r => r.ok).task.task_id);
  });
}


test('independent contenders preserve an orphan lock instead of stealing a replacement', { timeout: 10000 }, async t => {
  const root = await mkdtemp(join(tmpdir(), 'workflow-orphan-lock-'));
  const statePath = join(root, 'tasks.json');
  const owner = spawn(process.execPath, ['-e', 'process.exit(0)'], { windowsHide: true });
  await once(owner, 'exit');
  const lock = `${owner.pid}\n${Date.now() - 120000}\n`;
  await writeFile(statePath + '.lock', lock);
  const old = new Date(Date.now() - 120000);
  await utimes(statePath + '.lock', old, old);
  const children = [0, 1].map(() => fork(new URL('./fixtures/store-process.mjs', import.meta.url), [statePath], { silent: true, windowsHide: true }));
  t.after(() => { for (const child of children) if (child.exitCode === null) child.kill(); });
  const exits = children.map(child => once(child, 'exit'));
  const replies = await Promise.all(children.map(child => once(child, 'message').then(([m]) => m)));
  assert(replies.every(reply => reply.code === 'CONNECTOR_STORE_ORPHANED_LOCK'), JSON.stringify(replies));
  for (const [code] of await Promise.all(exits)) assert.equal(code, 0);
  assert.equal(await readFile(statePath + '.lock', 'utf8'), lock);
  await assert.rejects(readFile(statePath), { code: 'ENOENT' });
});
