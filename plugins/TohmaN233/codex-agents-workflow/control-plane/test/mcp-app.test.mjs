import assert from 'node:assert/strict';
import { mkdtemp, readFile } from 'node:fs/promises';
import { join } from 'node:path';
import test from 'node:test';
import { tmpdir } from './physical-tempdir.mjs';
import { buildToolDefinitions, createStdioRequestScheduler, DEFAULT_CONFIG_PATH, handleRpc, startConsole, stopConsole } from '../server.mjs';
import { APP_MIME_TYPE, WORKBENCH_URI, SETTINGS_URI } from '../lib/mcp-app.mjs';
import { WorkbenchApi } from '../lib/workbench-api.mjs';
import { HOST_ONLY_WORKFLOW_OPERATIONS, workflowToolDefinitions } from '../lib/workflow-tools.mjs';
import { createDraft } from '../lib/workflow-schema.mjs';

function readyWorkflow(id = 'app-api-fixture') {
  return { ...createDraft(id, 'App API fixture'), status: 'ready',
    skill_policy: { mode: 'cooperative', implicit: 'allow', ambient_allow: [], shadowed_skill_paths: [] },
    inputs_schema: { type: 'object', properties: { task: { type: 'string' } }, required: ['task'], additionalProperties: false },
    finalization: { required: true, node_id: 'final' },
    nodes: [{ id: 'start', type: 'start' }, { id: 'final', type: 'agent', executor: { kind: 'main' }, role: 'finalizer', access: 'read_only', approval: { required: false }, retry: { max_attempts: 1 }, input_bindings: { task: '/inputs/task' }, prompt_template: 'Return the task result.', outputs_schema: { type: 'object', properties: { result: { type: 'string' } }, required: ['result'], additionalProperties: false } }, { id: 'end', type: 'end' }],
    edges: [{ id: 'start-final', source: 'start', target: 'final' }, { id: 'final-end', source: 'final', target: 'end' }],
  };
}

async function fixture(t, { migrate = true } = {}) {
  const root = await mkdtemp(join(tmpdir(), 'workflow-mcp-app-'));
  const configPath = join(root, 'control-plane.json');
  const env = { ...process.env, CODEX_WORKFLOW_CONFIG: configPath, CODEX_WORKFLOW_DISABLED: '0', SOL_CONTROL_DISABLED: '0' };
  const options = { configPath, defaultConfigPath: DEFAULT_CONFIG_PATH, env };
  const state = await startConsole({ ...options, open: false });
  t.after(stopConsole);
  const api = new WorkbenchApi(options);
  if (migrate) {
    const migrated = await api.request({ path: '/api/workflow/migrate_v6', method: 'POST' });
    assert.equal(migrated.status, 200, JSON.stringify(migrated));
  }
  const rpc = async (method, params = {}) => handleRpc({ jsonrpc: '2.0', id: 1, method, params }, options);
  const call = async (name, args = {}) => (await rpc('tools/call', { name, arguments: args })).result;
  const appRequest = async (path, method = 'POST', body) => (await call('codex_agents_workflow_app_request', { path, method, ...(body === undefined ? {} : { body }) })).structuredContent;
  const http = async (path, method = 'POST', body) => {
    const response = await fetch(`http://127.0.0.1:${state.port}${path}`, {
      method, headers: { authorization: `Bearer ${state.token}`, ...(body === undefined ? {} : { 'content-type': 'application/json' }) },
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    });
    return { status: response.status, body: await response.json() };
  };
  return { api, rpc, call, appRequest, http, options, state };
}

test('standalone settings serves every local module import without MCP host privileges', async t => {
  const { state } = await fixture(t);
  const visited = new Set();
  async function checkModule(path) {
    if (visited.has(path)) return;
    visited.add(path);
    const response = await fetch(`http://127.0.0.1:${state.port}${path}`);
    assert.equal(response.status, 200, `Missing standalone module: ${path}`);
    assert.match(response.headers.get('content-type'), /javascript/);
    const source = await response.text();
    for (const match of source.matchAll(/(?:import|export)\s+(?:[^;]*?\sfrom\s*)?['"]([^'"]+)['"]/g)) {
      const specifier = match[1];
      if (specifier.startsWith('.')) await checkModule(new URL(specifier, `http://127.0.0.1${path}`).pathname);
    }
  }
  await checkModule('/app.js');
  assert.ok(visited.has('/app-client.js'));
  assert.ok(visited.has('/settings-view-state.js'));
});

test('MCP Apps advertise exact pinned entrypoints, fullscreen resources, mentions and App-only API', async () => {
  const tools = buildToolDefinitions();
  const app = tools.find(tool => tool.name === 'codex_agents_workflow_app');
  const settings = tools.find(tool => tool.name === 'codex_agents_workflow_settings');
  assert.equal(app.title, 'Workflow Workbench');
  assert.equal(app._meta.ui.resourceUri, WORKBENCH_URI);
  assert.equal(app._meta['ui/resourceUri'], WORKBENCH_URI);
  assert.deepEqual(app._meta['openai/ui'], { entrypoints: [{ type: 'global' }, { type: 'thread' }], preferredModelDisplayMode: 'fullscreen' });
  assert.equal(settings._meta.ui.resourceUri, SETTINGS_URI);
  assert.equal(settings._meta['openai/ui'].entrypoints[0].type, 'settings');
  assert.ok(app.icons[0].src.startsWith('data:image/svg+xml;base64,'));
  const requests = tools.find(tool => tool.name === 'codex_agents_workflow_app_request');
  assert.deepEqual(requests._meta.ui.visibility, ['app']);
  assert.equal(requests.annotations.readOnlyHint, false);
  const mentions = tools.find(tool => tool.name === 'search_mentions');
  assert.deepEqual(mentions._meta['openai/extensions'], { 'mentions/search': {} });
  assert.deepEqual(mentions._meta.ui.visibility, ['app']);
  assert.equal(mentions.annotations.readOnlyHint, true);

  for (const method of ['server/discover', 'initialize']) {
    const response = await handleRpc({ id: 2, method, params: { protocolVersion: '2026-07-28' } });
    if (method === 'server/discover') assert.deepEqual(response.result.supportedVersions, ['2026-07-28']);
    else assert.equal(response.result.protocolVersion, '2026-07-28');
    assert.deepEqual(response.result.capabilities.resources, { subscribe: false, listChanged: false });
  }
  assert.equal((await handleRpc({ id: 2, method: 'initialize', params: { protocolVersion: '2024-11-05' } })).result.protocolVersion, '2024-11-05');
  const listed = await handleRpc({ id: 3, method: 'resources/list' });
  assert.deepEqual(listed.result.resources.map(resource => resource.uri), [WORKBENCH_URI, SETTINGS_URI]);
  for (const resource of listed.result.resources) {
    assert.equal(resource.mimeType, APP_MIME_TYPE);
    assert.deepEqual(resource._meta['openai/ui'], { availableDisplayModes: ['fullscreen'], preferredDisplayMode: 'fullscreen' });
    assert.deepEqual(resource._meta.ui.csp.connectDomains, []);
  }
});

test('modern discovery matches pinned Extensions spec and legacy initialization stays separate', async () => {
  // https://raw.githubusercontent.com/openai/mcp-extensions/node-v0.1.0/docs/spec.md
  // Icon Guidelines and Structured Settings capability-discovery example:
  // resultType + supportedVersions + result._meta server identity (not the
  // initialize-only protocolVersion/serverInfo body fields).
  const discovered = await handleRpc({ jsonrpc: '2.0', id: 'discover', method: 'server/discover', params: {} });
  assert.equal(discovered.result.resultType, 'complete');
  assert.deepEqual(discovered.result.supportedVersions, ['2026-07-28']);
  assert.equal('protocolVersion' in discovered.result, false);
  assert.equal('serverInfo' in discovered.result, false);
  const identity = discovered.result._meta['io.modelcontextprotocol/serverInfo'];
  assert.equal(identity.name, 'codex-agents-workflow');
  assert.equal(identity.title, 'Codex Agents Workflow');
  assert.equal(typeof identity.version, 'string');
  assert.ok(identity.icons[0].src.startsWith('data:image/svg+xml;base64,'));
  const modernList = await handleRpc({ id: 'list', method: 'tools/list', params: { _meta: { 'io.modelcontextprotocol/protocolVersion': '2026-07-28' } } });
  assert.equal(modernList.result.resultType, 'complete');
  assert.deepEqual(modernList.result._meta['io.modelcontextprotocol/serverInfo'], identity);
  for (const protocolVersion of ['2025-11-25', '2024-11-05']) {
    const initialized = await handleRpc({ id: 'initialize', method: 'initialize', params: { protocolVersion } });
    assert.equal(initialized.result.protocolVersion, protocolVersion);
    assert.deepEqual(initialized.result.serverInfo, identity);
    assert.equal('resultType' in initialized.result, false);
    assert.equal('supportedVersions' in initialized.result, false);
  }
  const legacyList = await handleRpc({ id: 'list', method: 'tools/list', params: {} });
  assert.equal('resultType' in legacyList.result, false);
  assert.equal('_meta' in legacyList.result, false);
});

test('App resources are self-contained built HTML without console credentials or network asset fetches', async t => {
  const { state, options } = await fixture(t);
  for (const [uri, view, file] of [[WORKBENCH_URI, 'workflows', 'workflows-app.html'], [SETTINGS_URI, 'settings', 'settings-app.html']]) {
    const response = await handleRpc({ id: 1, method: 'resources/read', params: { uri } }, options);
    assert.equal(response.error, undefined, response.error?.message);
    const resource = response.result.contents[0];
    assert.equal(resource.mimeType, APP_MIME_TYPE);
    assert.match(resource.text, /<meta name="codex-agents-workflow-app" content="mcp">/);
    assert.ok(resource.text.includes(`<meta name="codex-agents-workflow-view" content="${view}">`));
    assert.equal(resource.text === await readFile(new URL(`../web/${file}`, import.meta.url), 'utf8'), true, `Resource differs from packaged ${file}`);
    assert.equal(/<(?:script|link)[^>]*(?:src|href)\s*=/i.test(resource.text), false, 'App assets must be self-contained');
    // Standalone transport code legitimately contains the literal "Bearer ".
    // Actual session credentials and loopback links must never be baked in.
    assert.equal(resource.text.includes(state.token), false, 'Resource contains a live console credential');
    assert.equal(resource.text.includes(options.configPath), false, 'Resource contains private installation configuration');
    assert.equal(/(?:href|src)=["'][^"']*(?:#token=|127\.0\.0\.1:\d+)/i.test(resource.text), false, 'Resource links to a credentialed console');
    const embeddedCss = /<style id="workflow-styles">([\s\S]*?)<\/style>/.exec(resource.text)?.[1];
    assert.equal(embeddedCss === await readFile(new URL('../web/workflows.css', import.meta.url), 'utf8'), true, 'Embedded CSS differs from the packaged bundle');
    assert.deepEqual(resource._meta['openai/ui'].availableDisplayModes, ['fullscreen']);
  }
  const unknown = await handleRpc({ id: 1, method: 'resources/read', params: { uri: 'ui://codex-agents-workflow/missing' } });
  assert.equal(unknown.error.data.code, 'RESOURCE_NOT_FOUND');
});

test('HTTP and App share exact read, mutation, revision conflict and error bodies', async t => {
  const f = await fixture(t);
  for (const [path, method] of [['/api/config', 'GET'], ['/api/defaults', 'GET'], ['/api/provider-secrets', 'GET'], ['/api/workflow/list', 'POST'], ['/api/workflow/role_templates', 'POST'], ['/api/workflow/authoring_workflows', 'POST']]) {
    assert.deepEqual(await f.appRequest(path, method), await f.http(path, method), path);
  }
  const initial = (await f.appRequest('/api/config', 'GET')).body;
  const changed = structuredClone(initial.config);
  changed.global.enabled = !initial.config.global.enabled;
  const request = { config: changed, expected_revision: initial.revision };
  const saved = await f.appRequest('/api/config', 'PUT', request);
  assert.equal(saved.status, 200);
  assert.equal(saved.body.config.global.enabled, changed.global.enabled);
  assert.deepEqual(await f.appRequest('/api/config', 'GET'), await f.http('/api/config', 'GET'));
  const conflict = await f.appRequest('/api/config', 'PUT', request);
  assert.equal(conflict.status, 409);
  assert.deepEqual(conflict, await f.http('/api/config', 'PUT', request));
  for (const [path, method, body] of [['/api/missing', 'GET'], ['/api/provider-secret', 'PUT', { provider_id: 'missing', api_key: 'secret' }], ['/api/workflow/not_an_operation', 'POST'], ['/api/workflow/install_workflow_package', 'POST', { package: {} }], ['/api/workflow/read', 'POST', { workflow_id: 'missing' }]]) {
    const app = await f.appRequest(path, method, body);
    assert.ok(app.status >= 400, path);
    assert.deepEqual(app, await f.http(path, method, body), path);
  }
  assert.equal((await f.appRequest('https://localhost/api/config', 'GET')).status, 404);
  assert.deepEqual(await f.appRequest('/api/config?view=settings', 'GET'), await f.http('/api/config?view=settings', 'GET'));
  assert.equal((await f.call('codex_agents_workflow_app_request', { path: '/api/config', method: 'GET', token: 'guess' })).isError, true);
});

test('opener bootstrap includes actual initial reads only in UI metadata', async t => {
  const f = await fixture(t);
  for (const name of ['codex_agents_workflow_app', 'codex_agents_workflow_settings']) {
    const result = await f.call(name);
    assert.equal(result.isError, undefined, JSON.stringify(result));
    assert.deepEqual(Object.keys(result._meta.bootstrap), ['/api/config', '/api/workflow/list', '/api/workflow/capabilities', '/api/workflow/authoring_workflows', '/api/workflow/role_templates']);
    const bootstrap = result._meta.bootstrap;
    assert.ok(bootstrap['/api/config'].config.providers[0].config.model);
    assert.ok(bootstrap['/api/workflow/authoring_workflows'][0].workflow.nodes.length);
    const modelVisible = JSON.stringify({ content: result.content, structuredContent: result.structuredContent });
    assert.doesNotMatch(modelVisible, /template|providers|config_path|Bearer|token/);
    assert.equal(JSON.stringify(result).includes(f.state.token), false);
    for (const [path, body] of Object.entries(bootstrap)) {
      const descriptor = result._meta.bootstrapRequests[path];
      assert.deepEqual(descriptor, { method: path === '/api/config' ? 'GET' : 'POST', body: path === '/api/workflow/list' ? { include_legacy: true } : {} });
      const current = await f.api.request({ path, ...descriptor });
      assert.deepEqual(body, current.body, path);
      assert.equal(result._meta.bootstrapStatus[path], current.status);
    }
  }
});

test('bootstrap records exact initial request arguments and retains legacy entries only for that list request', async t => {
  const f = await fixture(t);
  const result = await f.call('codex_agents_workflow_app');
  const { bootstrap, bootstrapRequests } = result._meta;
  assert.deepEqual(bootstrapRequests['/api/workflow/list'], { method: 'POST', body: { include_legacy: true } });
  assert.deepEqual(bootstrapRequests['/api/config'], { method: 'GET', body: {} });
  for (const path of ['/api/workflow/capabilities', '/api/workflow/authoring_workflows', '/api/workflow/role_templates']) {
    assert.deepEqual(bootstrapRequests[path], { method: 'POST', body: {} });
  }
  assert.ok(bootstrap['/api/workflow/list'].some(item => item.legacy_task_type === true));
  const regularList = await f.appRequest('/api/workflow/list', 'POST', {});
  assert.equal(regularList.body.some(item => item.legacy_task_type === true), false);
  assert.equal(JSON.stringify(result.structuredContent).includes('include_legacy'), false);
});

test('blocked migration remains an explicit bootstrap API error while the settings App can open', async t => {
  const f = await fixture(t, { migrate: false });
  const result = await f.call('codex_agents_workflow_settings');
  assert.equal(result.isError, undefined);
  assert.equal(result._meta.bootstrapStatus['/api/config'], 200);
  assert.equal(result._meta.bootstrap['/api/config'].config.version, 6);
  assert.equal(result._meta.bootstrapStatus['/api/workflow/list'], 400);
  assert.equal(result._meta.bootstrap['/api/workflow/list'].code, 'WORKFLOW_MIGRATION_REQUIRED');
});

test('composer mentions search stored names and resolve compact pinned metadata without prompt libraries', async t => {
  const f = await fixture(t);
  const search = await f.call('search_mentions', { query: '' });
  assert.equal(search.isError, undefined);
  assert.ok(search.structuredContent.items.length > 0);
  const items = search.structuredContent.items;
  for (const kind of ['workflow', 'role']) {
    const item = items.find(value => value.resourceUri.includes(`/mention/${kind}/`));
    assert.ok(item, kind);
    assert.equal(item.type, 'resource');
    const selected = await f.rpc('resources/read', { uri: item.resourceUri });
    assert.equal(selected.error, undefined, JSON.stringify(selected));
    const data = JSON.parse(selected.result.contents[0].text);
    assert.equal(data.kind, kind);
    assert.equal(data.name, item.title);
    assert.ok(data.workflow_id);
    assert.ok(data.revision_hash);
    assert.doesNotMatch(selected.result.contents[0].text, /prompt_template|role_instructions|nodes|task_types|control_token/);
    const matching = await f.call('search_mentions', { query: item.title });
    assert.ok(matching.structuredContent.items.some(value => value.resourceUri === item.resourceUri));
  }
  assert.deepEqual((await f.call('search_mentions', { query: 'unique-no-saved-match-2039581' })).structuredContent, { items: [] });
  const bad = await f.rpc('resources/read', { uri: 'codex-agents-workflow://mention/role/not-found/not-current' });
  assert.equal(bad.error.data.code, 'MENTION_ROLE_REVISION');
});

test('App support leaves direct model catalog and Host-only operations unchanged', async t => {
  const f = await fixture(t);
  const modelTools = new Set(workflowToolDefinitions().map(tool => tool.name));
  assert.ok(modelTools.has('workflow_start'));
  for (const operation of HOST_ONLY_WORKFLOW_OPERATIONS) {
    assert.equal(modelTools.has(`workflow_${operation}`), false);
    const denied = await f.call(`workflow_${operation}`, {});
    assert.equal(denied.isError, true);
    assert.equal(JSON.parse(denied.content[0].text).code, 'HOST_OPERATION_REQUIRED');
  }
  const status = await f.call('codex_agents_workflow_status');
  assert.doesNotMatch(JSON.stringify(status), /prompt_template|role_instructions|#token=/);
});

test('shared API keeps human authority and exact current Main alias arguments', async t => {
  const f = await fixture(t);
  const calls = [];
  f.api.service.call = async (operation, args, options) => {
    calls.push({ operation, args, options });
    return { operation, args };
  };
  for (const [alias, operation, expected] of [
    ['current_main_pending', 'main_status', { run_id: 'run' }],
    ['current_main_accept', 'accept_main', { run_id: 'run', control_token: '', accepted: true }],
    ['current_main_cancel', 'cancel', { run_id: 'run', control_token: '' }],
  ]) {
    const response = await f.api.request({ path: `/api/workflow/${alias}`, method: 'POST', body: { run_id: 'run', accepted: true } });
    assert.equal(response.status, 200);
    assert.deepEqual(calls.pop(), { operation, args: expected, options: { human: true } });
  }
  const approval = await f.api.request({ path: '/api/workflow/current_main_approve', method: 'POST', body: { run_id: 'run', approval_id: 'approval', decision: true } });
  assert.equal(approval.status, 200);
  assert.deepEqual(calls.splice(0), [
    { operation: 'approve', args: { run_id: 'run', control_token: '', approval_id: 'approval', decision: true }, options: { human: true } },
    { operation: 'continue_main', args: { run_id: 'run', control_token: '', owner: 'human-console' }, options: { human: true } },
  ]);
  for (const operation of ['save', 'export_workflow_package', 'install_workflow_package', 'import_skill', 'start', 'recover_control']) {
    const body = { workflow_id: 'selected', expected_revision: 'current' };
    await f.api.request({ path: `/api/workflow/${operation}`, method: 'POST', body });
    assert.deepEqual(calls.pop(), { operation, args: body, options: { human: true } });
  }
});

test('App create/save/export/install preserve the shared immutable package and CAS behavior', async t => {
  const f = await fixture(t);
  const workflow = readyWorkflow();
  const created = await f.appRequest('/api/workflow/create', 'POST', { workflow });
  assert.equal(created.status, 200, JSON.stringify(created));
  const edited = structuredClone(created.body.workflow);
  edited.description = 'Edited in the App';
  const saved = await f.appRequest('/api/workflow/save', 'POST', { workflow_id: workflow.id, expected_revision: created.body.revision_hash, workflow: edited });
  assert.equal(saved.status, 200, JSON.stringify(saved));
  assert.equal(saved.body.workflow.description, edited.description);
  const staleArgs = { workflow_id: workflow.id, expected_revision: created.body.revision_hash, workflow: edited };
  const conflict = await f.appRequest('/api/workflow/save', 'POST', staleArgs);
  assert.ok(conflict.status >= 400);
  assert.deepEqual(conflict, await f.http('/api/workflow/save', 'POST', staleArgs));
  const bundle = await f.appRequest('/api/workflow/export_workflow_package', 'POST', { workflow_id: workflow.id });
  assert.equal(bundle.status, 200);
  assert.deepEqual(bundle, await f.http('/api/workflow/export_workflow_package', 'POST', { workflow_id: workflow.id }));
  const deleted = await f.appRequest('/api/workflow/delete', 'POST', { workflow_id: workflow.id, expected_revision: saved.body.revision_hash });
  assert.equal(deleted.status, 200);
  const installed = await f.appRequest('/api/workflow/install_workflow_package', 'POST', { package: bundle.body });
  assert.equal(installed.status, 200, JSON.stringify(installed));
  assert.equal(installed.body.revision_hash, saved.body.revision_hash);
  assert.deepEqual(await f.appRequest('/api/workflow/read', 'POST', { workflow_id: workflow.id }), await f.http('/api/workflow/read', 'POST', { workflow_id: workflow.id }));
});

test('App cancellation and status use the reserved stdio lane while general work is blocked', { timeout: 10000 }, async t => {
  const f = await fixture(t);
  const workflow = readyWorkflow('app-control-fixture');
  assert.equal((await f.appRequest('/api/workflow/create', 'POST', { workflow })).status, 200);
  // Start only the deterministic journal. No Agent dispatch or model call.
  const started = await f.appRequest('/api/workflow/start', 'POST', { workflow_id: workflow.id, main_actor: 'human-console', inputs: { task: 'Fixture' } });
  assert.equal(started.status, 200, JSON.stringify(started));
  const { run_id, control_token } = started.body;
  assert.ok(run_id); assert.ok(control_token);
  let release;
  const blocked = new Promise(resolve => { release = resolve; });
  const writes = new Map();
  let controlsComplete;
  const completed = new Promise(resolve => { controlsComplete = resolve; });
  const scheduler = createStdioRequestScheduler({ maxGeneral: 1, maxControl: 1,
    handle: async request => {
      if ([1, 2].includes(request.id)) { await blocked; return { id: request.id, result: {} }; }
      return handleRpc(request, f.options);
    },
    write: response => { writes.set(response.id, response); if (writes.has(3) && writes.has(4)) controlsComplete(); },
  });
  t.after(async () => { release(); await scheduler.shutdown(); });
  scheduler.submit({ id: 1, method: 'tools/call', params: { name: 'workflow_wait', arguments: {} } });
  const appCall = (id, path, body = {}) => ({ id, method: 'tools/call', params: { name: 'codex_agents_workflow_app_request', arguments: { path, method: 'POST', body } } });
  scheduler.submit(appCall(2, '/api/workflow/build_workflow'));
  scheduler.submit(appCall(3, '/api/workflow/cancel', { run_id, control_token }));
  scheduler.submit(appCall(4, '/api/workflow/get', { run_id }));
  await completed;
  assert.equal(writes.has(1), false);
  assert.equal(writes.has(2), false);
  assert.equal(writes.get(3).result.structuredContent.status, 200, JSON.stringify(writes.get(3)));
  assert.equal(writes.get(4).result.structuredContent.status, 200, JSON.stringify(writes.get(4)));
  assert.equal(writes.get(4).result.structuredContent.body.status, 'cancelled');
  assert.equal(scheduler.snapshot().active.general, 1);
  release(); await scheduler.shutdown();
});
