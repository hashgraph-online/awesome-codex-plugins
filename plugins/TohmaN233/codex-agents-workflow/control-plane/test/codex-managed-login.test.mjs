import test from 'node:test';
import assert from 'node:assert/strict';
import { waitForManagedLogin } from '../lib/execution/codex-managed-login.mjs';

test('managed login waits for post-completion account readiness, ignoring a stale account update', async () => {
  const completion = { method: 'account/login/completed', params: { loginId: 'fixture-login', success: true } };
  const stale = { method: 'account/updated', params: { authMode: null } };
  const ready = { method: 'account/updated', params: { authMode: 'chatgpt' } };
  const events = [stale, completion]; let observedAccountReload = false;
  const client = { events, async waitFor(matches, options) {
    const existing = events.slice(options.after).find(matches); if (existing) return existing;
    assert.equal(options.after, 2); observedAccountReload = true; events.push(ready); return ready;
  } };
  assert.deepEqual(await waitForManagedLogin(client, 'fixture-login'), { authenticated: true, type: 'chatgpt' });
  assert.equal(observedAccountReload, true);
});

test('a successful callback without a usable managed account is not authentication', async () => {
  const events = [{ method: 'account/login/completed', params: { loginId: 'fixture-login', success: true } }, { method: 'account/updated', params: { authMode: null } }];
  const client = { events, async waitFor(matches, options) { return events.slice(options.after).find(matches); } };
  await assert.rejects(waitForManagedLogin(client, 'fixture-login'), { code: 'CODEX_LOGIN_NOT_READY' });
});
