import { homedir } from 'node:os';
import { join, resolve } from 'node:path';
import { createCodexClient } from './codex-app-server-client.mjs';
import { isolatedEnvironment, STRICT_SETTINGS } from './codex-profile-builder.mjs';
import { requireValue } from '../workflow-paths.mjs';

const inFlightByFactory = new WeakMap();
function sharedInFlight(factory) {
  let pending = inFlightByFactory.get(factory);
  if (!pending) { pending = new Map(); inFlightByFactory.set(factory, pending); }
  return pending;
}

// The official host App Server owns login/refresh. Never read or copy auth.json,
// refresh tokens, account configuration or cookies into a node profile. This
// broker passes only short-lived access tokens over private stdio RPCs.
export function decodeHostAccess(status, { now = Date.now() } = {}) {
  requireValue(['chatgpt', 'chatgptAuthTokens'].includes(status?.authMethod) && typeof status.authToken === 'string' && status.authToken.length <= 32768,
    'HOST_AUTH_UNAVAILABLE', 'Existing Codex ChatGPT login is unavailable; no browser login was started');
  let payload;
  try { payload = JSON.parse(Buffer.from(status.authToken.split('.')[1], 'base64url').toString('utf8')); }
  catch { throw Object.assign(new Error('Official host returned unsupported access-token metadata'), { code: 'HOST_AUTH_SCHEMA' }); }
  const claims = payload?.['https://api.openai.com/auth'];
  requireValue(typeof claims?.chatgpt_account_id === 'string' && claims.chatgpt_account_id.length > 0 && claims.chatgpt_account_id.length <= 256 && Number.isFinite(payload.exp),
    'HOST_AUTH_SCHEMA', 'Official host access token lacks account identity or expiry');
  requireValue(payload.exp * 1000 > now + 30000, 'HOST_AUTH_EXPIRED', 'Existing Codex access token is expired; no browser login was started');
  return { accessToken: status.authToken, chatgptAccountId: claims.chatgpt_account_id,
    chatgptPlanType: typeof claims.chatgpt_plan_type === 'string' ? claims.chatgpt_plan_type : null, expiresAt: payload.exp * 1000 };
}

export function createHostAuthBroker({ binary, cwd, env = process.env, clientFactory = createCodexClient, now = Date.now }) {
  const home = resolve(env.CODEX_HOME || join(homedir(), '.codex'));
  const shared = sharedInFlight(clientFactory);
  const key = `${home}\0${resolve(binary)}`;
  let cached;
  async function obtainOnce() {
    const overrides = Object.entries({ ...STRICT_SETTINGS, model_provider: 'openai', openai_base_url: '', chatgpt_base_url: 'https://chatgpt.com/backend-api/' })
      .filter(([key]) => key !== 'cli_auth_credentials_store') // Honor the host's official credential store.
      .map(([key, value]) => `${key} = ${JSON.stringify(value)}`);
    const client = clientFactory(binary, { home, cwd, env: isolatedEnvironment(env, home), overrides, credentialOnly: true });
    try {
      await client.call('initialize', { clientInfo: { name: 'codex_workflow_host_auth', version: '1.0.0' }, capabilities: { experimentalApi: true } }); client.initialized();
      return decodeHostAccess(await client.call('getAuthStatus', { includeToken: true, refreshToken: true }), { now: now() });
    } finally { await client.close(); }
  }
  async function obtain() {
    for (let attempt = 0; attempt < 3; attempt++) {
      try { return await obtainOnce(); }
      catch (error) {
        if (!['CODEX_STATE_RUNTIME_INIT', 'HOST_AUTH_UNAVAILABLE'].includes(error?.code) || attempt === 2) throw error;
        await new Promise(resolve => setTimeout(resolve, 100 * (attempt + 1)));
      }
    }
  }
  return {
    async credentials({ force = false, previousAccountId = null } = {}) {
      if (force || !cached || cached.expiresAt <= now() + 120000) {
        if (!shared.has(key)) {
          const pending = obtain().finally(() => { if (shared.get(key) === pending) shared.delete(key); });
          shared.set(key, pending);
        }
        cached = await shared.get(key);
      }
      requireValue(!previousAccountId || previousAccountId === cached.chatgptAccountId, 'HOST_AUTH_ACCOUNT_CHANGED', 'Host account changed during a pinned node; start a new Run');
      return { accessToken: cached.accessToken, chatgptAccountId: cached.chatgptAccountId, chatgptPlanType: cached.chatgptPlanType };
    },
    clear() { cached = null; }
  };
}
