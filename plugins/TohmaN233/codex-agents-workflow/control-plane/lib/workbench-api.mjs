import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { WorkflowService } from './workflow-service.mjs';
import { appendAuditEvent, configRevision, loadConfig, resolveConfigPath, saveConfig, validateConfig } from './config.mjs';
import { localCodexCatalog } from './execution/local-codex-catalog.mjs';

export const MAX_WORKBENCH_BODY = 8 * 1024 * 1024;
export const MAX_PACKAGE_BODY = 72 * 1024 * 1024;

export function workbenchErrorPayload(error) {
  return {
    error: error instanceof Error ? error.message : String(error),
    ...(typeof error?.code === 'string' ? { code: error.code } : {}),
    ...(error?.retryable === true ? { retryable: true } : {}),
    ...(error?.actionRequired ? { action_required: error.actionRequired } : {}),
    ...(error?.details && typeof error.details === 'object' ? { details: error.details } : {}),
    ...(error?.validation && typeof error.validation === 'object' ? { validation: error.validation } : {}),
    ...(error?.committed === true ? { committed: true, sequence: error.sequence } : {}),
  };
}

export function workbenchStorage(configPath, env) {
  const globalPath = resolveConfigPath({ ...env, CODEX_WORKFLOW_CONFIG: '', SOL_CONTROL_CONFIG: '' });
  const left = resolve(configPath), right = resolve(globalPath);
  const same = process.platform === 'win32' ? left.toLowerCase() === right.toLowerCase() : left === right;
  return { scope: env.CODEX_WORKFLOW_CONFIG || env.SOL_CONTROL_CONFIG || !same ? 'override' : 'global', config_path: configPath };
}

// Both authenticated HTTP and host-gated App interactions use this exact human
// API. Model-facing workflow_* tools remain a separate, narrower boundary.
export class WorkbenchApi {
  constructor({ configPath, defaultConfigPath, env = process.env, fetchImpl = globalThis.fetch, capabilities = {} }) {
    this.configPath = configPath;
    this.defaultConfigPath = defaultConfigPath;
    this.env = env;
    this.storage = workbenchStorage(configPath, env);
    this.service = new WorkflowService({ configPath, defaultConfigPath, env, fetchImpl, capabilities });
  }

  async request({ path, method, body = {} }) {
    try {
      if (typeof path !== 'string' || !path.startsWith('/api/')) return { status: 404, body: { error: 'not found' } };
      // Match the HTTP adapter's URL pathname parsing. This never opens a
      // network connection; App authority comes from the host visibility gate.
      path = new URL(path, 'http://workbench.invalid').pathname;
      const limit = path === '/api/workflow/install_workflow_package' ? MAX_PACKAGE_BODY : MAX_WORKBENCH_BODY;
      if (Buffer.byteLength(JSON.stringify(body), 'utf8') > limit) throw new Error(`request body exceeds ${limit} bytes`);
      return { status: 200, body: await this.#dispatch(path, method, body) };
    } catch (error) {
      if (error.code === 'WORKBENCH_ROUTE') return { status: 404, body: { error: 'not found' } };
      return { status: /changed since/.test(error.message) ? 409 : 400, body: workbenchErrorPayload(error) };
    }
  }

  async #dispatch(path, method, body) {
    const { configPath, defaultConfigPath, env, service } = this;
    if (path.startsWith('/api/workflow/') && method === 'POST') {
      const operation = path.slice('/api/workflow/'.length);
      if (operation === 'current_main_pending') return service.call('main_status', { run_id: String(body.run_id || '') }, { human: true });
      if (operation === 'current_main_accept') return service.call('accept_main', { run_id: String(body.run_id || ''), control_token: String(body.control_token || ''), accepted: body.accepted }, { human: true });
      if (operation === 'current_main_approve') {
        const run_id = String(body.run_id || ''), control_token = String(body.control_token || ''), owner = String(body.owner || 'human-console');
        await service.call('approve', { run_id, control_token, approval_id: String(body.approval_id || ''), decision: body.decision }, { human: true });
        return service.call('continue_main', { run_id, control_token, owner }, { human: true });
      }
      if (operation === 'current_main_cancel') return service.call('cancel', { run_id: String(body.run_id || ''), control_token: String(body.control_token || '') }, { human: true });
      return service.call(operation, body, { human: true });
    }
    if (path === '/api/config' && method === 'GET') {
      const config = await loadConfig({ configPath, defaultConfigPath });
      return { config, revision: configRevision(config), storage: this.storage };
    }
    if (path === '/api/config' && method === 'PUT') {
      const saved = await saveConfig(body.config, { configPath, expectedRevision: String(body.expected_revision || '') });
      await appendAuditEvent(configPath, { event: 'console-save', outcome: 'ok' }, { effectCommitted: true });
      return saved;
    }
    if (path === '/api/models' && method === 'GET') {
      const config = await loadConfig({ configPath, defaultConfigPath });
      const catalog = await localCodexCatalog({ env, extra: [config.strict_executor?.codex_binary].filter(Boolean) });
      return { models: catalog.models, source: catalog.source };
    }
    if (path === '/api/provider-secrets' && method === 'GET') {
      const config = await loadConfig({ configPath, defaultConfigPath });
      return { providers: config.providers.filter(provider => provider.kind === 'openai_compatible').map(provider => ({
        provider_id: provider.id, api_key_env: provider.config.api_key_env,
        required: provider.config.auth_type !== 'none', ready: provider.config.auth_type === 'none' || Boolean(env[provider.config.api_key_env]),
      })) };
    }
    if (path === '/api/provider-secret' && method === 'PUT') {
      const config = await loadConfig({ configPath, defaultConfigPath });
      const provider = config.providers.find(item => item.id === body.provider_id);
      if (!provider || provider.kind !== 'openai_compatible') throw Object.assign(new Error('Select a saved OpenAI-compatible Provider'), { code: 'PROVIDER_SECRET_TARGET' });
      if (provider.config.auth_type === 'none') throw Object.assign(new Error('This Provider does not use an API key'), { code: 'PROVIDER_SECRET_NOT_REQUIRED' });
      if (body.clear === true) delete env[provider.config.api_key_env];
      else {
        if (typeof body.api_key !== 'string' || !body.api_key || body.api_key.length > 4096 || /[\r\n\0]/.test(body.api_key)) throw Object.assign(new Error('API key must contain 1–4096 characters without line breaks'), { code: 'PROVIDER_SECRET_VALUE' });
        env[provider.config.api_key_env] = body.api_key;
      }
      await appendAuditEvent(configPath, { event: 'provider-secret-session-update', outcome: 'ok', provider_id: provider.id, cleared: body.clear === true }, { effectCommitted: true });
      return { provider_id: provider.id, api_key_env: provider.config.api_key_env, ready: body.clear !== true };
    }
    if (path === '/api/defaults' && method === 'GET') {
      const defaults = validateConfig(JSON.parse(await readFile(defaultConfigPath, 'utf8')));
      return { config: defaults, revision: configRevision(defaults) };
    }
    throw Object.assign(new Error('not found'), { code: 'WORKBENCH_ROUTE' });
  }

  async bootstrap() {
    const bootstrap = {};
    const bootstrapStatus = {};
    const bootstrapRequests = {};
    for (const path of ['/api/config', '/api/workflow/list', '/api/workflow/capabilities', '/api/workflow/authoring_workflows', '/api/workflow/role_templates']) {
      const descriptor = { method: path === '/api/config' ? 'GET' : 'POST', body: path === '/api/workflow/list' ? { include_legacy: true } : {} };
      const response = await this.request({ path, ...descriptor });
      bootstrap[path] = response.body;
      bootstrapStatus[path] = response.status;
      bootstrapRequests[path] = descriptor;
    }
    // Preserve actual failures as well as successful reads. The App needs to
    // render configuration/migration controls even when execution is blocked.
    return { bootstrap, bootstrapStatus, bootstrapRequests };
  }
}
