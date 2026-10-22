import { requireValue } from '../workflow-paths.mjs';

// In Codex 0.145.0 the managed flow emits login/completed BEFORE reloading the
// account manager. account/updated is the published readiness boundary. Do not
// replace it with a sleep, an assumed-success flag or repeated model submission.
export async function waitForManagedLogin(client, loginId, { after = 0, timeout = 600000 } = {}) {
  requireValue(typeof loginId === 'string' && loginId, 'CODEX_LOGIN_ID', 'Wait for an exact managed login identity');
  const completed = await client.waitFor(event => event.method === 'account/login/completed' && event.params.loginId === loginId, { after, timeout });
  requireValue(completed.params.success === true, 'CODEX_LOGIN_FAILED', 'Official managed login failed');
  const completionIndex = client.events.indexOf(completed);
  requireValue(completionIndex >= after, 'CODEX_LOGIN_EVENT', 'Login completion is not in this client event history');
  const updated = await client.waitFor(event => event.method === 'account/updated', { after: completionIndex + 1, timeout: 30000 });
  requireValue(updated.params.authMode === 'chatgpt', 'CODEX_LOGIN_NOT_READY', 'Managed login did not produce a ready ChatGPT account');
  return { authenticated: true, type: 'chatgpt' };
}
