import test from 'node:test';
import assert from 'node:assert/strict';
import { authenticatedModel } from '../lib/execution/codex-model-catalog.mjs';

const target = { model: 'future-model', supportedReasoningEfforts: [{ reasoningEffort: 'medium' }] };
test('anonymous catalog cannot reject an account-specific model before official login', async () => {
  let loggedIn = false; let reads = 0;
  const client = { async call(method) {
    if (method === 'account/read') return { requiresOpenaiAuth: true, account: loggedIn ? { type: 'chatgpt' } : null };
    assert.equal(method, 'model/list'); reads++; return { data: loggedIn ? [target] : [] };
  } };
  await assert.rejects(authenticatedModel(client, 'future-model', 'medium'), { code: 'CODEX_AUTH_REQUIRED' });
  assert.equal(reads, 0);
  loggedIn = true;
  assert.deepEqual(await authenticatedModel(client, 'future-model', 'medium'), target);
  assert.equal(reads, 1);
});
test('authenticated inventory rejects substitution, unsupported effort and duplicate identities across pages', async () => {
  const client = { async call(method, args) {
    if (method === 'account/read') return { requiresOpenaiAuth: false };
    return { data: [target], nextCursor: args.cursor ? null : 'page-2' };
  } };
  await assert.rejects(authenticatedModel(client, 'future-model', 'medium'), /matches: 2/);
  const single = { async call(method) { return method === 'account/read' ? { requiresOpenaiAuth: false } : { data: [target] }; } };
  await assert.rejects(authenticatedModel(single, 'different-model', 'medium'), { code: 'CODEX_MODEL_UNAVAILABLE' });
  await assert.rejects(authenticatedModel(single, 'future-model', 'ultra'), { code: 'CODEX_MODEL_UNAVAILABLE' });
});
