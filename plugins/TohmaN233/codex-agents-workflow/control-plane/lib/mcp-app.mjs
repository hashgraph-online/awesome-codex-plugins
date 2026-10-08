import { readFileSync } from 'node:fs';
import { readFile } from 'node:fs/promises';
import { validateData } from './workflow-data-schema.mjs';

// Protocol adapter for pinned @openai/mcp-extensions 0.1.0 and ext-apps 1.7.5.
// Keep server runtime dependency-free and compatible with Node >=20. Official
// browser SDKs are bundled into the resource HTML by the frontend build.
export const APP_MIME_TYPE = 'text/html;profile=mcp-app';
export const WORKBENCH_URI = 'ui://codex-agents-workflow/workbench';
export const SETTINGS_URI = 'ui://codex-agents-workflow/settings';
const MENTION_PREFIX = 'codex-agents-workflow://mention/';
const emptySchema = { type: 'object', properties: {}, additionalProperties: false };
const readOnly = { readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: false };
const resourceUi = {
  ui: { csp: { connectDomains: [], resourceDomains: [], frameDomains: [] } },
  'openai/ui': { availableDisplayModes: ['fullscreen'], preferredDisplayMode: 'fullscreen' },
};
const resources = [
  { uri: WORKBENCH_URI, name: 'workbench', title: 'Workflow Workbench', file: 'workflows-app.html', view: 'workflows' },
  { uri: SETTINGS_URI, name: 'settings', title: 'Workflow Settings', file: 'settings-app.html', view: 'settings' },
];

export function appIcons() {
  const svg = readFileSync(new URL('../../assets/sidebar-icon.svg', import.meta.url), 'utf8');
  return [{ src: `data:image/svg+xml;base64,${Buffer.from(svg).toString('base64')}`, mimeType: 'image/svg+xml', sizes: ['any'] }];
}

export function appToolDefinitions() {
  const icons = appIcons();
  return [
    {
      name: 'codex_agents_workflow_app', title: 'Workflow Workbench', icons,
      description: 'Open Workflow Workbench to manage Workflows, Roles, packages, Runs, and recovery. The human App receives its private configuration separately from model context.',
      inputSchema: emptySchema, annotations: readOnly,
      _meta: { ui: { resourceUri: WORKBENCH_URI }, 'ui/resourceUri': WORKBENCH_URI,
        'openai/ui': { entrypoints: [{ type: 'global' }, { type: 'thread' }], preferredModelDisplayMode: 'fullscreen' } },
    },
    {
      name: 'codex_agents_workflow_settings', title: 'Workflow Settings', icons,
      description: 'Open human-owned Workflow settings for Providers, Roles, approval defaults, and routing.',
      inputSchema: emptySchema, annotations: readOnly,
      _meta: { ui: { resourceUri: SETTINGS_URI }, 'ui/resourceUri': SETTINGS_URI,
        'openai/ui': { entrypoints: [{ type: 'settings', searchTerms: ['workflows', 'agents', 'providers', 'roles', 'approval', 'routing'] }], preferredModelDisplayMode: 'fullscreen' } },
    },
    {
      name: 'codex_agents_workflow_app_request', title: 'Workbench request', icons,
      description: 'Human App transport for the authenticated Workbench API, including configuration edits, package installation, execution and recovery. Host App visibility gates this transport; it is not a model tool.',
      inputSchema: { type: 'object', properties: { path: { type: 'string', minLength: 1 }, method: { type: 'string', enum: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'] }, body: { type: 'object' } }, required: ['path', 'method'], additionalProperties: false },
      outputSchema: { type: 'object', properties: { body: {}, status: { type: 'integer' } }, required: ['body', 'status'], additionalProperties: false },
      annotations: { readOnlyHint: false, destructiveHint: true, idempotentHint: false, openWorldHint: true },
      _meta: { ui: { visibility: ['app'] } },
    },
    {
      name: 'search_mentions', title: 'Search Workflows and Roles', icons,
      description: 'Search saved Workflows and Workbench Roles for composer mentions. References contain only compact metadata for the selected revision.',
      inputSchema: { type: 'object', properties: { query: { type: 'string' } }, required: ['query'] },
      outputSchema: { type: 'object', properties: { items: { type: 'array', items: {
        type: 'object', properties: { type: { type: 'string', const: 'resource' }, resourceUri: { type: 'string' }, title: { type: 'string' }, subtitle: { type: 'string' }, icons: { type: 'array', items: { type: 'object' } } }, required: ['type', 'resourceUri', 'title'], additionalProperties: false,
      } } }, required: ['items'], additionalProperties: false },
      annotations: readOnly, _meta: { 'openai/extensions': { 'mentions/search': {} }, ui: { visibility: ['app'] } },
    },
  ];
}

export function appResourceDefinitions() {
  return resources.map(({ file, view, ...resource }) => ({ ...resource, mimeType: APP_MIME_TYPE, icons: appIcons(), _meta: resourceUi }));
}

export async function readAppResource(uri) {
  const resource = resources.find(item => item.uri === uri);
  if (!resource) return null;
  const text = await readFile(new URL(`../web/${resource.file}`, import.meta.url), 'utf8');
  if (!text.includes('<meta name="codex-agents-workflow-app" content="mcp">') || !text.includes(`<meta name="codex-agents-workflow-view" content="${resource.view}">`)) {
    throw Object.assign(new Error(`Invalid Workbench App resource: ${resource.file}`), { code: 'APP_RESOURCE_INVALID' });
  }
  return { contents: [{ uri, mimeType: APP_MIME_TYPE, text, _meta: resourceUi }] };
}

export async function callAppTool(name, args, api) {
  const definition = appToolDefinitions().find(tool => tool.name === name);
  if (!definition) return null;
  validateData(args, definition.inputSchema);
  if (name === 'codex_agents_workflow_app_request') return { content: [], structuredContent: await api.request(args) };
  if (name === 'search_mentions') return { content: [], structuredContent: await searchMentions(args, api.service) };
  const view = name === 'codex_agents_workflow_settings' ? 'settings' : 'workflows';
  return {
    content: [{ type: 'text', text: view === 'settings' ? 'Workflow Settings opened.' : 'Workflow Workbench opened.' }],
    structuredContent: { view },
    _meta: await api.bootstrap(),
  };
}

function mentionUri(kind, entry) {
  return `${MENTION_PREFIX}${kind}/${encodeURIComponent(entry.id)}/${encodeURIComponent(entry.revision_hash)}`;
}

export async function searchMentions({ query }, service) {
  const workflows = await service.call('list', {}, { human: true });
  const roles = await service.call('role_templates', {}, { human: true });
  const search = query.trim().toLocaleLowerCase();
  const icons = appIcons();
  const items = [];
  for (const [kind, entries] of [['workflow', workflows.filter(item => item.template_kind !== 'role')], ['role', roles]]) {
    for (const entry of entries) {
      if (search && ![entry.name, entry.id, entry.description, ...(entry.tags ?? [])].join(' ').toLocaleLowerCase().includes(search)) continue;
      items.push({ type: 'resource', resourceUri: mentionUri(kind, entry), title: entry.name,
        subtitle: `${kind === 'role' ? 'Role' : 'Workflow'} · ${entry.enabled === false ? 'disabled' : entry.status ?? 'ready'}`, icons });
    }
  }
  return { items };
}

function compactMention(kind, entry) {
  const result = { kind, workflow_id: entry.id, revision_hash: entry.revision_hash, name: entry.name };
  for (const key of ['description', 'status', 'enabled', 'template_kind', 'role', 'access', 'provider_id', 'provider_kind', 'model', 'reasoning_effort']) {
    if (entry[key] !== undefined) result[key] = entry[key];
  }
  return result;
}

export async function readMentionResource(uri, service) {
  if (!uri.startsWith(MENTION_PREFIX)) return null;
  const segments = uri.slice(MENTION_PREFIX.length).split('/');
  if (segments.length !== 3 || !['workflow', 'role'].includes(segments[0])) throw Object.assign(new Error('Invalid Workbench mention URI'), { code: 'MENTION_URI' });
  const [kind, encodedId, encodedRevision] = segments;
  const id = decodeURIComponent(encodedId), revision = decodeURIComponent(encodedRevision);
  let entry;
  if (kind === 'workflow') {
    const pack = await service.call('read', { workflow_id: id, revision_hash: revision }, { human: true });
    entry = { ...pack.workflow, revision_hash: pack.revision_hash };
  } else {
    const roles = await service.call('role_templates', {}, { human: true });
    entry = roles.find(item => item.id === id && item.revision_hash === revision);
    if (!entry) throw Object.assign(new Error('Selected Role revision is no longer available; select the Role again'), { code: 'MENTION_ROLE_REVISION' });
  }
  return { contents: [{ uri, mimeType: 'application/json', text: JSON.stringify(compactMention(kind, entry)) }] };
}
