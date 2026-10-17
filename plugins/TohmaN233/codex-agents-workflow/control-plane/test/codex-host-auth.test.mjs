import test from 'node:test';
import assert from 'node:assert/strict';
import { createHostAuthBroker, decodeHostAccess } from '../lib/execution/codex-host-auth.mjs';

function status(account = 'test-account', exp = 5000) {
  const payload = { exp, 'https://api.openai.com/auth': { chatgpt_account_id: account, chatgpt_plan_type: 'test-plan' } };
  return { authMethod: 'chatgpt', authToken: 'example-fixture.' + Buffer.from(JSON.stringify(payload)).toString('base64url') + '.not-real' };
}
test('host authentication reuses an official token concurrently without copying credentials or starting threads', async () => {
  let opened = 0; let closed = 0; const methods = []; let account = 'test-account';
  const broker = createHostAuthBroker({ binary: '/qualified-test-binary', cwd: '/owned-test-directory', env: { CODEX_HOME: '/existing-host-home' }, now: () => 1000000,
    clientFactory(_binary, options) {
      opened++; assert.equal(options.home.replaceAll('\\','/').endsWith('/existing-host-home'), true);
      assert.equal(options.credentialOnly, true); assert(options.overrides.includes('features.shell_tool = false'));
      return { initialized() {}, async call(method, args) { methods.push(method); if (method === 'initialize') return {}; assert.equal(method, 'getAuthStatus'); assert.deepEqual(args, { includeToken: true, refreshToken: true }); return status(account); }, async close() { closed++; } };
    }
  });
  const values = await Promise.all([broker.credentials(), broker.credentials()]);
  assert.deepEqual(values[0], values[1]); assert.equal(opened, 1); assert.equal(closed, 1);
  assert.deepEqual(methods, ['initialize', 'getAuthStatus']);
  await broker.credentials(); assert.equal(opened, 1);
  account = 'changed-account';
  await assert.rejects(broker.credentials({ force: true, previousAccountId: 'test-account' }), { code: 'HOST_AUTH_ACCOUNT_CHANGED' });
  assert.equal(closed, 2); broker.clear();
});
test('missing, expired and malformed host auth fail explicitly without browser or credential disclosure', async () => {
  assert.throws(() => decodeHostAccess({ authMethod: 'apikey', authToken: 'example-private-sentinel' }), { code: 'HOST_AUTH_UNAVAILABLE' });
  assert.throws(() => decodeHostAccess({ authMethod: 'chatgpt', authToken: 'example-private-sentinel' }), error => error.code === 'HOST_AUTH_SCHEMA' && !error.message.includes('example-private-sentinel'));
  assert.throws(() => decodeHostAccess(status('test-account', 1), { now: 1000000 }), { code: 'HOST_AUTH_EXPIRED' });
  let closed = false;
  const broker = createHostAuthBroker({ binary: '/test', cwd: '/test', clientFactory: () => ({ initialized() {}, async call(method) { return method === 'initialize' ? {} : { authMethod: null, authToken: null }; }, async close() { closed = true; } }) });
  await assert.rejects(broker.credentials(), { code: 'HOST_AUTH_UNAVAILABLE' }); assert.equal(closed, true);
});

test('separate brokers share one in-flight host auth startup', async () => {
  let opened = 0; let release;
  const gate = new Promise(resolve => { release = resolve; });
  const clientFactory = () => {
    opened++;
    return { initialized() {}, async call(method) { if (method === 'initialize') return {}; await gate; return status(); }, async close() {} };
  };
  const options = { binary: '/singleflight-binary', cwd: '/owned', env: { CODEX_HOME: '/singleflight-host-home' }, now: () => 1000000, clientFactory };
  const brokers = Array.from({ length: 16 }, () => createHostAuthBroker(options));
  const pending = Promise.all(brokers.map(broker => broker.credentials()));
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(opened, 1, 'parallel Runs must not start one global-state App Server each');
  release();
  assert.equal((await pending).length, 16);
});

test('host auth retries only transient sqlite startup failure', async () => {
  let opened = 0;
  const broker = createHostAuthBroker({ binary: '/sqlite-retry-binary', cwd: '/owned', env: { CODEX_HOME: '/sqlite-retry-home' }, now: () => 1000000,
    clientFactory() {
      opened++;
      if (opened < 3) throw Object.assign(new Error('sqlite startup unavailable'), { code: 'CODEX_STATE_RUNTIME_INIT' });
      return { initialized() {}, async call(method) { return method === 'initialize' ? {} : status(); }, async close() {} };
    }
  });
  assert.equal((await broker.credentials()).chatgptAccountId, 'test-account');
  assert.equal(opened, 3);
});
