#!/usr/bin/env node
import { randomBytes } from 'node:crypto';
import { spawn } from 'node:child_process';
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import readline from 'node:readline';
import { WorkflowService } from './lib/workflow-service.mjs';
import {waitForOwnedWorkflow} from './lib/execution/owned-workflow-wait.mjs';
import { closeStrictManagers } from './lib/execution/strict-session-manager.mjs';
import { closeManagedNativeManagers } from './lib/execution/managed-native-manager.mjs';
import { closeHostMainManagers } from './lib/execution/host-main-manager.mjs';
import { fenceAllAttemptAdmissions, closeAttemptAdmissions } from './lib/execution/attempt-admission.mjs';
import { workflowToolDefinitions, WORKFLOW_TOOL_OPERATIONS, HOST_ONLY_WORKFLOW_OPERATIONS } from './lib/workflow-tools.mjs';
import { validateData } from './lib/workflow-data-schema.mjs';
import { WorkbenchApi, workbenchStorage, workbenchErrorPayload as errorToolPayload, MAX_WORKBENCH_BODY, MAX_PACKAGE_BODY } from './lib/workbench-api.mjs';
import { appIcons, appToolDefinitions, appResourceDefinitions, readAppResource, readMentionResource, callAppTool } from './lib/mcp-app.mjs';

import {
  appendAuditEvent,
  loadConfig,
  resolveConfigPath,
} from './lib/config.mjs';
import {
  controlConnectorTask,
  getConnectorTask,
  getControlStatus,
  invokeSelection,
  probeConnector,
  resolveSelection,
  startConnectorSelection,
} from './lib/control.mjs';

const CONTROL_DIR = dirname(fileURLToPath(import.meta.url));
const DEFAULT_CONFIG_PATH = join(CONTROL_DIR, 'default-config.json');
const WEB_DIR = join(CONTROL_DIR, 'web');
const SERVER_VERSION = JSON.parse(await readFile(new URL('./package.json', import.meta.url), 'utf8')).version;
const DEFAULT_CONSOLE_PORT = 58712;
const MAX_HTTP_BODY = MAX_WORKBENCH_BODY;
const MODERN_PROTOCOL_VERSION = '2026-07-28';
const SUPPORTED_PROTOCOL_VERSIONS = new Set([MODERN_PROTOCOL_VERSION, '2025-11-25', '2025-06-18', '2025-03-26', '2024-11-05']);

let consoleState = null;
let activeStdioLifecycle = null;

const STDIO_MAX_GENERAL_IN_FLIGHT = 24;
const STDIO_MAX_CONTROL_IN_FLIGHT = 4;
const STDIO_MAX_PENDING = 128;
const STDIO_CONTROL_TOOLS = new Set([
  'codex_agents_workflow_status',
  'codex_agents_workflow_connector_status',
  'codex_agents_workflow_connector_control',
]);
const STDIO_CONTROL_OPERATIONS = new Set([
  'status', 'get', 'run_snapshot', 'next', 'events', 'pause', 'resume', 'cancel', 'approve', 'recover_control',
  'control_connector', 'reconcile_connector', 'strict_status',
]);

function textToolResult(value, isError = false) {
  const text = typeof value === 'string' ? value : JSON.stringify(value, null, 2);
  return {
    content: [{ type: 'text', text }],
    ...(isError ? { isError: true } : {}),
  };
}

function jsonResponse(res, status, value, extraHeaders = {}) {
  const body = Buffer.from(JSON.stringify(value), 'utf8');
  res.writeHead(status, {
    'content-type': 'application/json; charset=utf-8',
    'content-length': body.length,
    'cache-control': 'no-store',
    'x-content-type-options': 'nosniff',
    ...extraHeaders,
  });
  res.end(body);
}

function staticResponse(res, body, contentType) {
  const data = Buffer.isBuffer(body) ? body : Buffer.from(body, 'utf8');
  res.writeHead(200, {
    'content-type': contentType,
    'content-length': data.length,
    'cache-control': 'no-store',
    'x-content-type-options': 'nosniff',
    'content-security-policy': "default-src 'self'; script-src 'self'; style-src 'self'; style-src-attr 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'",
    'referrer-policy': 'no-referrer',
  });
  res.end(data);
}

function requestHostIsLoopback(req) {
  const host = String(req.headers.host || '').toLowerCase();
  return /^127\.0\.0\.1:\d+$/.test(host)
    || /^localhost:\d+$/.test(host)
    || /^\[::1\]:\d+$/.test(host);
}

function bearerToken(req) {
  const header = String(req.headers.authorization || '');
  return header.startsWith('Bearer ') ? header.slice(7) : '';
}

async function readJsonBody(req, limit = MAX_HTTP_BODY) {
  const chunks = [];
  let size = 0;
  for await (const chunk of req) {
    size += chunk.length;
    if (size > limit) throw new Error(`request body exceeds ${limit} bytes`);
    chunks.push(chunk);
  }
  const text = Buffer.concat(chunks).toString('utf8');
  try {
    return JSON.parse(text || '{}');
  } catch (error) {
    throw new Error(`invalid JSON body: ${error.message}`);
  }
}

function openBrowser(url, platform = process.platform) {
  let command;
  let args;
  if (platform === 'win32') {
    command = 'cmd.exe';
    args = ['/d', '/s', '/c', 'start', '', url];
  } else if (platform === 'darwin') {
    command = 'open';
    args = [url];
  } else {
    command = 'xdg-open';
    args = [url];
  }
  return new Promise((resolve) => {
    let settled = false;
    try {
      const child = spawn(command, args, {
        detached: true,
        stdio: 'ignore',
        windowsHide: true,
      });
      child.once('error', (error) => {
        if (!settled) {
          settled = true;
          resolve({ opened: false, error: error.message });
        }
      });
      child.once('spawn', () => {
        child.unref();
        if (!settled) {
          settled = true;
          resolve({ opened: true, error: null });
        }
      });
    } catch (error) {
      resolve({ opened: false, error: error.message });
    }
  });
}

export async function startConsole({
  configPath: requestedConfigPath,
  defaultConfigPath = DEFAULT_CONFIG_PATH,
  port = 0,
  open = true,
  env = process.env,
} = {}) {
  if (consoleState) {
    const opened = open ? await openBrowser(consoleState.url) : { opened: false, error: null };
    return { ...consoleState, browser: opened };
  }
  const configPath = requestedConfigPath || resolveConfigPath(env);
  const storage = workbenchStorage(configPath, env);
  const api = new WorkbenchApi({ configPath, defaultConfigPath, env });
  await loadConfig({ configPath, defaultConfigPath });
  const token = randomBytes(32).toString('base64url');
  const staticFiles = {
    '/': ['index.html', 'text/html; charset=utf-8'],
    '/index.html': ['index.html', 'text/html; charset=utf-8'],
    '/app.js': ['app.js', 'text/javascript; charset=utf-8'],
    '/app-client.js': ['app-client.js', 'text/javascript; charset=utf-8'],
    '/settings-view-state.js': ['settings-view-state.js', 'text/javascript; charset=utf-8'],
    '/i18n.js': ['i18n.js', 'text/javascript; charset=utf-8'],
    '/styles.css': ['styles.css', 'text/css; charset=utf-8'],
    '/workflows': ['workflows.html', 'text/html; charset=utf-8'],
    '/workflows.js': ['workflows.js', 'text/javascript; charset=utf-8'],
    '/workflows.css': ['workflows.css', 'text/css; charset=utf-8'],
  };

  const server = createServer(async (req, res) => {
    try {
      if (!requestHostIsLoopback(req)) {
        jsonResponse(res, 403, { error: 'loopback Host header required' });
        return;
      }
      const url = new URL(req.url || '/', 'http://127.0.0.1');
      if (req.method === 'GET' && staticFiles[url.pathname]) {
        const [fileName, contentType] = staticFiles[url.pathname];
        staticResponse(res, await readFile(join(WEB_DIR, fileName)), contentType);
        return;
      }
      if (url.pathname === '/health' && req.method === 'GET') {
        jsonResponse(res, 200, { status: 'ok', version: SERVER_VERSION });
        return;
      }
      if (!url.pathname.startsWith('/api/')) {
        jsonResponse(res, 404, { error: 'not found' });
        return;
      }
      if (bearerToken(req) !== token) {
        jsonResponse(res, 401, { error: 'unauthorized' }, { 'www-authenticate': 'Bearer' });
        return;
      }
      const body = ['POST', 'PUT', 'PATCH'].includes(req.method)
        ? await readJsonBody(req, url.pathname === '/api/workflow/install_workflow_package' ? MAX_PACKAGE_BODY : MAX_HTTP_BODY) : {};
      const response = await api.request({ path: url.pathname, method: req.method, body });
      jsonResponse(res, response.status, response.body);
    } catch (error) {
      const status = /changed since/.test(error.message) ? 409 : 400;
      jsonResponse(res, status, errorToolPayload(error));
    }
  });

  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(port, '127.0.0.1', resolve);
  });
  const address = server.address();
  const actualPort = typeof address === 'object' && address ? address.port : port;
  const url = `http://127.0.0.1:${actualPort}/workflows#token=${encodeURIComponent(token)}`;
  consoleState = { server, token, url, port: actualPort, configPath, defaultConfigPath, storage, env };
  const browser = open ? await openBrowser(url) : { opened: false, error: null };
  try { await appendAuditEvent(configPath, {
    event: 'console-open',
    outcome: browser.opened || !open ? 'ok' : 'browser-error',
    detail: browser.error || '',
  }, { effectCommitted: true }); }
  catch (error) { await stopConsole(); throw error; }
  return { ...consoleState, browser };
}

export async function stopConsole() {
  if (!consoleState) return;
  const state = consoleState;
  consoleState = null;
  await new Promise((resolve) => state.server.close(resolve));
}

export function buildToolDefinitions() {
  const sharedResolveProperties = {
    task_type_id: { type: 'string', description: 'Exact enabled Task Type id returned by codex_agents_workflow_status.' },
    task: { type: 'string', description: 'Task objective for the selected Task Type.' },
    context: { description: 'Relevant task context. String or JSON value.' },
    constraints: { description: 'Fixed decisions, scope boundaries, prohibited actions, and ownership.' },
    verification: { description: 'Concrete checks and acceptance evidence.' },
    user_approved: { type: 'boolean', default: false, description: 'Set true only after explicit current-task approval when the selected Provider or Stage approval gate is enabled.' },
  };
  return [
    ...workflowToolDefinitions(),
    ...appToolDefinitions(),
    {
      name: 'codex_agents_workflow_status',
      annotations: { readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: false },
      description: 'Read sanitized control-plane metadata only: enabled Providers, Task Type ids, routes, ordered Stage bindings, capabilities, and approval flags. Prompt templates, provider endpoints, credential variable names, and console tokens are never returned.',
      inputSchema: { type: 'object', properties: {}, additionalProperties: false },
    },
    {
      name: 'codex_agents_workflow_console',
      annotations: { readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: false },
      description: 'Open the human-owned loopback configuration console in the default browser. The normal result does not reveal the console token or prompt library to the model. Use reveal_url only after an explicit user request for the manual URL.',
      inputSchema: {
        type: 'object',
        properties: {
          port: { type: 'integer', minimum: 0, maximum: 65535, default: DEFAULT_CONSOLE_PORT },
          reveal_url: { type: 'boolean', default: false },
        },
        additionalProperties: false,
      },
    },
    {
      name: 'codex_agents_workflow_resolve',
      annotations: { readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: false },
      description: 'After the primary agent selects exactly one enabled Task Type, compile only its ordered Stages and return each user-pinned Provider adapter contract. The control plane must not substitute or fall back to another Provider. Native/MCP/web-review Providers are executed by Codex through their returned contracts; this tool does not invoke them.',
      inputSchema: {
        type: 'object',
        properties: sharedResolveProperties,
        required: ['task_type_id', 'task'],
        additionalProperties: false,
      },
    },
    {
      name: 'codex_agents_workflow_connector_probe',
      annotations: { readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: true },
      description: 'Probe one enabled built-in connector without sending a task. A successful probe means the local binary/configuration is available; it does not claim a live model session.',
      inputSchema: {
        type: 'object',
        properties: {
          provider_id: { type: 'string' },
          workspace: { type: 'string', description: 'Optional absolute workspace path to validate.' },
        },
        required: ['provider_id'],
        additionalProperties: false,
      },
    },
    {
      name: 'codex_agents_workflow_connector_start',
      annotations: { readOnlyHint: false, destructiveHint: true, idempotentHint: false, openWorldHint: true },
      description: 'Compile and internally deliver exactly one Stage from a selected Task Type to its pinned built-in connector. Bounded-write Stages require non-empty workspace-relative allowed_paths; extra confirmation is required only when the Provider or Stage approval gate is enabled.',
      inputSchema: {
        type: 'object',
        properties: {
          ...sharedResolveProperties,
          stage_id: { type: 'string', description: 'Exact Stage id returned for the selected Task Type.' },
          workspace: { type: 'string', description: 'Absolute existing Git repository root.' },
          allowed_paths: { type: 'array', items: { type: 'string' }, description: 'Required non-empty workspace-relative path boundaries for bounded-write Stages; omit for read-only Stages.' },
        },
        required: ['task_type_id', 'stage_id', 'task', 'workspace'],
        additionalProperties: false,
      },
    },
    {
      name: 'codex_agents_workflow_connector_status',
      annotations: { readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: false },
      description: 'Read one exact connector task by task_id, optionally waiting up to 25 seconds for a state change. Never infer identity from the visible UI or latest session.',
      inputSchema: {
        type: 'object',
        properties: {
          task_id: { type: 'string' },
          wait_ms: { type: 'integer', minimum: 0, maximum: 25000, default: 0 },
        },
        required: ['task_id'],
        additionalProperties: false,
      },
    },
    {
      name: 'codex_agents_workflow_connector_control',
      annotations: { readOnlyHint: false, destructiveHint: true, idempotentHint: false, openWorldHint: true },
      description: 'Control one exact connector task. Reconcile reattaches only persisted identities; Grok cancel requires exact session_id/run_id and Cursor cancel requires exact agent_id; abandon is explicitly risk-acknowledged.',
      inputSchema: {
        type: 'object',
        properties: {
          task_id: { type: 'string' },
          action: { type: 'string', enum: ['reconcile', 'respond_permission', 'respond_input', 'cancel', 'disconnect', 'abandon'] },
          request_id: { type: 'string' },
          decision: { type: 'string', enum: ['select', 'accept', 'decline', 'cancel'] },
          option_id: { type: 'string' },
          content: { type: 'object' },
          expected_session_id: { type: 'string' },
          expected_run_id: { type: 'string' },
          expected_agent_id: { type: 'string' },
          confirm: { type: 'boolean', default: false },
          acknowledge_may_still_run: { type: 'boolean', default: false },
          reason: { type: 'string' },
        },
        required: ['task_id', 'action'],
        additionalProperties: false,
      },
    },
    {
      name: 'codex_agents_workflow_invoke',
      annotations: { readOnlyHint: false, destructiveHint: false, idempotentHint: false, openWorldHint: true },
      description: 'Resolve and directly call one enabled OpenAI-compatible advisory Provider pinned to a read-only Stage. Direct API invocation must be enabled in the console, credentials must exist only in the configured environment variable, and approval gates still apply. This tool never grants file or host tools to the external model.',
      inputSchema: {
        type: 'object',
        properties: {
          ...sharedResolveProperties,
          stage_id: { type: 'string', description: 'Exact read-only Stage id to invoke.' },
        },
        required: ['task_type_id', 'stage_id', 'task'],
        additionalProperties: false,
      },
    },
  ];
}

function serverIdentity() {
  return { name: 'codex-agents-workflow', title: 'Codex Agents Workflow', version: SERVER_VERSION, icons: appIcons() };
}

export async function handleRpc(request, options = {}) {
  const response = await handleRpcRequest(request, options);
  // node-v0.1.0/docs/spec.md discovery example uses the modern MCP result
  // envelope and reserved identity metadata. Keep the legacy initialize
  // handshake separate; new-era requests negotiate via per-request metadata.
  const modern = request?.method === 'server/discover'
    || (request?.method !== 'initialize' && request?.params?._meta?.['io.modelcontextprotocol/protocolVersion'] === MODERN_PROTOCOL_VERSION);
  if (modern && response?.result) {
    return { ...response, result: { ...response.result, resultType: 'complete',
      _meta: { ...response.result._meta, 'io.modelcontextprotocol/serverInfo': serverIdentity() } } };
  }
  return response;
}

async function handleRpcRequest(request, {
  configPath = resolveConfigPath(),
  defaultConfigPath = DEFAULT_CONFIG_PATH,
  env = process.env,
  fetchImpl = globalThis.fetch,
  serviceCapabilities = {},
  signal,
} = {}) {
  const method = String(request?.method || '');
  const id = request?.id;
  if (method === 'server/discover') {
    return {
      jsonrpc: '2.0',
      id,
      result: {
        supportedVersions: [MODERN_PROTOCOL_VERSION],
        capabilities: { tools: { listChanged: false }, resources: { subscribe: false, listChanged: false } },
      },
    };
  }
  if (method === 'initialize') {
    const requestedVersion = String(request?.params?.protocolVersion || '');
    return {
      jsonrpc: '2.0',
      id,
      result: {
        protocolVersion: SUPPORTED_PROTOCOL_VERSIONS.has(requestedVersion) ? requestedVersion : '2025-11-25',
        capabilities: { tools: { listChanged: false }, resources: { subscribe: false, listChanged: false } },
        serverInfo: serverIdentity(),
      },
    };
  }
  if (method === 'notifications/initialized') return null;
  if (method === 'ping') return { jsonrpc: '2.0', id, result: {} };
  if (method === 'resources/list') {
    return { jsonrpc: '2.0', id, result: { resources: appResourceDefinitions() } };
  }
  if (method === 'resources/templates/list') return { jsonrpc: '2.0', id, result: { resourceTemplates: [] } };
  if (method === 'resources/read') {
    try {
      const uri = String(request?.params?.uri || '');
      let result = await readAppResource(uri);
      if (!result) {
        const api = new WorkbenchApi({ configPath, defaultConfigPath, env, fetchImpl, capabilities: serviceCapabilities });
        result = await readMentionResource(uri, api.service);
      }
      if (!result) throw Object.assign(new Error('Resource not found'), { code: 'RESOURCE_NOT_FOUND' });
      return { jsonrpc: '2.0', id, result };
    } catch (error) {
      return { jsonrpc: '2.0', id, error: { code: -32602, message: error.message, data: errorToolPayload(error) } };
    }
  }
  if (method === 'tools/list') {
    return { jsonrpc: '2.0', id, result: { tools: buildToolDefinitions() } };
  }
  if (method === 'tools/call') {
    const params = request.params && typeof request.params === 'object' ? request.params : {};
    const name = String(params.name || '');
    const suppliedArgs = params.arguments && typeof params.arguments === 'object' ? params.arguments : {};
    const args=suppliedArgs;
    try {
      if (['codex_agents_workflow_app', 'codex_agents_workflow_settings', 'codex_agents_workflow_app_request', 'search_mentions'].includes(name)) {
        // The host honors ui.visibility:['app'] for the human App transport.
        // No caller-supplied origin field can attest human authority. The
        // direct workflow_* model gate below stays unchanged.
        const api = new WorkbenchApi({ configPath, defaultConfigPath, env, fetchImpl, capabilities: serviceCapabilities });
        return { jsonrpc: '2.0', id, result: await callAppTool(name, suppliedArgs, api) };
      }
      if (name.startsWith('workflow_') && HOST_ONLY_WORKFLOW_OPERATIONS.has(name.slice('workflow_'.length))) {
        throw Object.assign(new Error('Host-only Workflow operations are unavailable through the model MCP boundary'), { code: 'HOST_OPERATION_REQUIRED' });
      }
      if (name.startsWith('workflow_') && WORKFLOW_TOOL_OPERATIONS.has(name.slice('workflow_'.length))) {
        const operation = name.slice('workflow_'.length);
        const definition = workflowToolDefinitions().find(tool => tool.name === name);
        validateData(suppliedArgs, definition.inputSchema);
        const modelThreadId=typeof params._meta?.threadId==='string'?params._meta.threadId:'';
        const needsModelThread=name==='workflow_start'||['workflow_native_next','workflow_native_spawned_batch','workflow_native_followed_up','workflow_orchestration_complete'].includes(name);
        if(needsModelThread&& !/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(modelThreadId))
          throw Object.assign(new Error('Workflow execution requires authenticated Codex thread metadata'),{code:'MODEL_THREAD_ID'});
        const workflowArgs=name==='workflow_start'?{...suppliedArgs,main_actor:'codex',native_parent_thread_id:modelThreadId}:suppliedArgs;
        const service = new WorkflowService({ configPath, defaultConfigPath, env, fetchImpl, capabilities: serviceCapabilities });
        if (name === 'workflow_start') {
          const pack = await service.call('read', { workflow_id: workflowArgs.workflow_id });
          const configuration = await service.config();
          const nativeIds = new Set(configuration.providers.filter(provider => provider.enabled && provider.kind === 'native_agent').map(provider => provider.id));
          const hasNativeNodes = pack.workflow.skill_policy?.mode === 'cooperative' && pack.workflow.nodes.some(node =>
            node.executor?.kind === 'provider' && nativeIds.has(node.executor.provider_id) && node.skill_policy?.mode !== 'strict');
          if (pack.provenance?.kind !== 'bundled_authoring_workflow' && (hasNativeNodes || pack.workflow.nodes.some(node => node.executor?.kind === 'main'))) {
            const started = await service.call('run_main', { ...workflowArgs, revision_hash: pack.revision_hash, return_after_start: true, detached_host: true });
            const result=await (serviceCapabilities.waitForOwnedWorkflow??waitForOwnedWorkflow)(service,started,{signal});
            return { jsonrpc: '2.0', id, result: textToolResult(service.modelResult(result)) };
          }
        }
        const result = await service.call(operation, workflowArgs, { model: true, modelThreadId, signal });
        return { jsonrpc: '2.0', id, result: textToolResult(result) };
      }
      if (name === 'codex_agents_workflow_status') {
        const status = await getControlStatus({ configPath, defaultConfigPath, env });
        return { jsonrpc: '2.0', id, result: textToolResult(status) };
      }
      if (name === 'codex_agents_workflow_console') {
        const revealUrl = args.reveal_url === true;
        const state = await startConsole({
          configPath,
          defaultConfigPath,
          port: Number.isInteger(args.port) ? args.port : DEFAULT_CONSOLE_PORT,
          open: true,
          env,
        });
        const result = {
          console_opened: state.browser.opened,
          port: state.port,
          config_location: 'user state outside the plugin cache',
          message: state.browser.opened
            ? 'The Codex Agents Workflow console was opened in the default browser.'
            : `The console is running, but the browser could not be opened automatically: ${state.browser.error || 'unknown error'}`,
          ...(revealUrl ? { console_url: state.url } : {}),
        };
        return { jsonrpc: '2.0', id, result: textToolResult(result) };
      }
      if (name === 'codex_agents_workflow_resolve') {
        const { result } = await resolveSelection(args, {
          configPath,
          defaultConfigPath,
          env,
        });
        return { jsonrpc: '2.0', id, result: textToolResult(result) };
      }
      if (name === 'codex_agents_workflow_connector_probe') {
        const result = await probeConnector(args, { configPath, defaultConfigPath, env });
        return { jsonrpc: '2.0', id, result: textToolResult(result) };
      }
      if (name === 'codex_agents_workflow_connector_start') {
        const result = await startConnectorSelection(args, { configPath, defaultConfigPath, env });
        return { jsonrpc: '2.0', id, result: textToolResult(result) };
      }
      if (name === 'codex_agents_workflow_connector_status') {
        const result = await getConnectorTask(args, { configPath, env });
        return { jsonrpc: '2.0', id, result: textToolResult(result) };
      }
      if (name === 'codex_agents_workflow_connector_control') {
        const result = await controlConnectorTask(args, { configPath, env });
        return { jsonrpc: '2.0', id, result: textToolResult(result) };
      }
      if (name === 'codex_agents_workflow_invoke') {
        const result = await invokeSelection(args, {
          configPath,
          defaultConfigPath,
          env,
          fetchImpl,
        });
        return { jsonrpc: '2.0', id, result: textToolResult(result) };
      }
      throw new Error(`unknown tool: ${name}`);
    } catch (error) {
      return { jsonrpc: '2.0', id, result: textToolResult(errorToolPayload(error), true) };
    }
  }
  if (id === undefined || id === null) return null;
  return {
    jsonrpc: '2.0',
    id,
    error: { code: -32601, message: `method not found: ${method}` },
  };
}

function isStdioControlRequest(request) {
  const method = String(request?.method || '');
  if (method !== 'tools/call') return true;
  const name = String(request?.params?.name || '');
  if (STDIO_CONTROL_TOOLS.has(name)) return true;
  if (name === 'codex_agents_workflow_app_request') {
    const args = request?.params?.arguments;
    if (args?.method !== 'POST' || typeof args.path !== 'string' || !args.path.startsWith('/api/workflow/')) return false;
    const operation = args.path.slice('/api/workflow/'.length);
    return STDIO_CONTROL_OPERATIONS.has(operation)
      || ['current_main_pending', 'current_main_accept', 'current_main_approve', 'current_main_cancel'].includes(operation);
  }
  return name.startsWith('workflow_') && STDIO_CONTROL_OPERATIONS.has(name.slice('workflow_'.length));
}

export function createStdioRequestScheduler({
  handle,
  write,
  onUnexpectedError = () => {},
  maxGeneral = STDIO_MAX_GENERAL_IN_FLIGHT,
  maxControl = STDIO_MAX_CONTROL_IN_FLIGHT,
  maxPending = STDIO_MAX_PENDING,
} = {}) {
  if (typeof handle !== 'function' || typeof write !== 'function') {
    throw new TypeError('stdio scheduler requires handle and write functions');
  }
  const queues = { control: [], general: [] };
  const inFlight = new Set();
  let active = { control: 0, general: 0 };
  let accepting = true;
  let shutdownPromise = null;

  const sendError = (request, code, message) => {
    if (request?.id === undefined || request?.id === null) return;
    write({ jsonrpc: '2.0', id: request.id, error: { code: code === 'SERVER_BUSY' ? -32000 : -32001, message, data: { code } } });
  };

  const pump = () => {
    while (active.control < maxControl && queues.control.length > 0) start(queues.control.shift(), 'control');
    while (active.general < maxGeneral && queues.general.length > 0) start(queues.general.shift(), 'general');
  };

  const start = (request, lane) => {
    active[lane] += 1;
    const task = Promise.resolve()
      .then(() => handle(request))
      .catch((error) => {
        onUnexpectedError(error, request);
        if (request?.id === undefined || request?.id === null) return undefined;
        return { jsonrpc: '2.0', id: request.id, error: {
          code: -32603,
          message: `Internal error handling ${String(request?.method || '(unknown method)')}: ${error instanceof Error ? error.message : String(error)}`,
          data: { code: 'INTERNAL_SERVER_ERROR', ...errorToolPayload(error), method: String(request?.method || '') },
        } };
      })
      .then((response) => response ? write(response) : undefined)
      .catch((error) => {
        onUnexpectedError(error, request);
      });
    inFlight.add(task);
    task.finally(() => {
      inFlight.delete(task);
      active[lane] -= 1;
      pump();
    }).catch(() => {});
  };

  const submit = (request) => {
    if (!accepting) {
      sendError(request, 'SERVER_SHUTTING_DOWN', 'server is shutting down');
      return false;
    }
    const lane = isStdioControlRequest(request) ? 'control' : 'general';
    const limit = lane === 'control' ? maxControl : maxGeneral;
    if (active[lane] < limit) {
      start(request, lane);
      return true;
    }
    if (queues.control.length + queues.general.length >= maxPending) {
      sendError(request, 'SERVER_BUSY', 'server request queue is full; retry later');
      return false;
    }
    queues[lane].push(request);
    return true;
  };

  const shutdown = () => {
    if (shutdownPromise) return shutdownPromise;
    accepting = false;
    for (const lane of ['control', 'general']) {
      for (const request of queues[lane]) sendError(request, 'SERVER_SHUTTING_DOWN', 'server is shutting down');
      queues[lane].length = 0;
    }
    shutdownPromise = Promise.allSettled([...inFlight]).then(() => undefined);
    return shutdownPromise;
  };

  return {
    submit,
    shutdown,
    isAccepting: () => accepting,
    snapshot: () => ({
      accepting,
      active: { ...active },
      pending: queues.control.length + queues.general.length,
      in_flight: inFlight.size,
    }),
  };
}

async function main() {
  const configPath = resolveConfigPath();
  const reader = readline.createInterface({ input: process.stdin, crlfDelay: Infinity });
  const requestAborts=new Map();
  const failures = [];
  const pendingWrites = new Set();
  let outputFailure = null;
  process.stdout.on('error', error => { outputFailure ||= error; });
  const writeResponse = response => {
    const pending = new Promise((resolve, reject) => {
      process.stdout.write(`${JSON.stringify(response)}\n`, error => error ? reject(error) : resolve());
    });
    pendingWrites.add(pending);
    pending.then(() => pendingWrites.delete(pending), error => {
      outputFailure ||= error;
      pendingWrites.delete(pending);
    });
    return pending;
  };
  let shutdownPromise = null;
  let scheduler;
  const requestShutdown = () => {
    if (shutdownPromise) return shutdownPromise;
    fenceAllAttemptAdmissions();
    reader.close();
    for(const abort of requestAborts.values())abort.abort();
    shutdownPromise = (async () => {
      await scheduler.shutdown();
      await Promise.allSettled([...pendingWrites]);
      await stopConsole();
      const stopped = await Promise.allSettled([closeStrictManagers(), closeManagedNativeManagers(), closeHostMainManagers()]);
      const admission = await Promise.allSettled([closeAttemptAdmissions()]);
      const cleanupErrors = [...stopped, ...admission].filter(item => item.status === 'rejected').map(item => item.reason);
      if (cleanupErrors.length) throw new AggregateError(cleanupErrors, 'Workflow shutdown retained unconfirmed execution ownership');
      if (outputFailure) throw outputFailure;
      if (failures.length) throw failures[0];
    })();
    return shutdownPromise;
  };
  scheduler = createStdioRequestScheduler({
    handle: async(request) => {
      const abort=new AbortController();requestAborts.set(request.id,abort);
      if(shutdownPromise)abort.abort();
      try{return await handleRpc(request,{configPath,defaultConfigPath:DEFAULT_CONFIG_PATH,signal:abort.signal});}
      finally{if(requestAborts.get(request.id)===abort)requestAborts.delete(request.id);}
    },
    write: writeResponse,
    onUnexpectedError: (error, request) => {
      process.stderr.write(`codex-agents-workflow request failed (id=${String(request?.id ?? 'notification')}, method=${String(request?.method || '')}): ${error?.stack || error?.message || String(error)}\n`);
      failures.push(error);
    },
  });
  activeStdioLifecycle = { requestShutdown };
  try {
    for await (const line of reader) {
      if (!scheduler.isAccepting()) break;
      if (!line.trim()) continue;
      let request;
      try {
        request = JSON.parse(line);
      } catch (error) {
        process.stderr.write(`codex-agents-workflow invalid JSON-RPC input: ${error.message}\n`);
        continue;
      }
      if(request.method==='notifications/cancelled'){
        requestAborts.get(request.params?.requestId)?.abort();
        continue;
      }
      scheduler.submit(request);
    }
    await requestShutdown();
    if (failures.length) throw failures[0];
  } finally {
    if (activeStdioLifecycle?.requestShutdown === requestShutdown) activeStdioLifecycle = null;
  }
}

const isMain = import.meta.url === pathToFileURL(process.argv[1] || '').href;
if (isMain) {
  let shuttingDown = false;
  const shutdown = () => {
    if (shuttingDown) return; shuttingDown = true;
    fenceAllAttemptAdmissions();
    const cleanup = activeStdioLifecycle?.requestShutdown?.()
      || (async () => {
        const owners = await Promise.allSettled([stopConsole(), closeStrictManagers(), closeManagedNativeManagers(), closeHostMainManagers()]);
        const admission = await Promise.allSettled([closeAttemptAdmissions()]);
        return [...owners, ...admission];
      })();
    cleanup.then((result) => {
      const failures = Array.isArray(result)
        ? result.filter(item => item.status === 'rejected')
        : [];
      if (failures.length) process.stderr.write('codex-agents-workflow shutdown failed; retained executor ownership requires reconciliation\n');
      process.exit(failures.length ? 1 : 0);
    }).catch((error) => {
      process.stderr.write(`codex-agents-workflow shutdown failed: ${error.stack || error.message}\n`);
      process.exit(1);
    });
  };
  process.on('SIGINT', shutdown);
  process.on('SIGTERM', shutdown);
  main().catch((error) => {
      process.stderr.write(`codex-agents-workflow fatal error: ${error.stack || error.message}\n`);
    process.exit(1);
  });
}

export { CONTROL_DIR, DEFAULT_CONFIG_PATH, DEFAULT_CONSOLE_PORT, SERVER_VERSION };
