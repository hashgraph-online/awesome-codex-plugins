import assert from 'node:assert/strict';
import { once } from 'node:events';
import { after, before, test } from 'node:test';
import { createServer } from '../server.mjs';

let server;
let base;

before(async () => {
  server = createServer().listen(0, '127.0.0.1');
  await once(server, 'listening');
  base = `http://127.0.0.1:${server.address().port}`;
});

after(() => server.close());

test('lists uploaded files', async () => {
  const r = await fetch(`${base}/`);
  assert.equal(r.status, 200);
  const { files } = await r.json();
  assert.deepEqual(files, ['meeting notes.txt', 'roadmap.txt']);
});

test('downloads a file by name', async () => {
  const r = await fetch(`${base}/files/roadmap.txt`);
  assert.equal(r.status, 200);
  assert.match(await r.text(), /Export to CSV/);
});

test('returns 404 for a file that does not exist', async () => {
  const r = await fetch(`${base}/files/missing.txt`);
  assert.equal(r.status, 404);
});

test('rejects names that try to leave the uploads folder', async () => {
  const r = await fetch(`${base}/files/..secret.txt`);
  assert.equal(r.status, 400);
});
