import { App, applyDocumentTheme, applyHostStyleVariables } from '@modelcontextprotocol/ext-apps';
import { OpenAIExtensions } from '@openai/mcp-extensions/app';
export { confirmWorkbench } from './mcp-app-dialog';
import { createBootstrapInbox, type BootstrapInbox } from './mcp-app-bootstrap.js';

declare const __CODEX_WORKFLOW_VERSION__: string;
export type AppView = 'workflows' | 'settings';
type AppRequestResult = { body: any; status: number };
type AppRequestArgs = { path: string; method: string; body?: unknown };
type AppState = {
  markerPresent: boolean;
  markerValue: string;
  view: AppView;
  clientReady: Promise<void>;
  bootstrapInbox: BootstrapInbox;
  client: App | null;
  extensions: OpenAIExtensions | null;
  clientError: Error | null;
  viewListeners: Set<(view: AppView) => void>;
  fullscreenRequested: boolean;
};

const globalState = globalThis as typeof globalThis & { __codexWorkflowAppState?: AppState };
const marker = document.querySelector<HTMLMetaElement>('meta[name="codex-agents-workflow-app"]');
const markerPresent = marker !== null;
const markerValue = marker?.content ?? '';
const viewMarker = document.querySelector<HTMLMetaElement>('meta[name="codex-agents-workflow-view"]')?.content;
const initialView: AppView = viewMarker === 'settings' ? 'settings' : 'workflows';
function applyTheme(app: App, context = app.getHostContext()) {
  if (context?.theme) applyDocumentTheme(context.theme);
  if (context?.styles?.variables) applyHostStyleVariables(context.styles.variables);
}

function createState(): AppState {
  const state: AppState = {
    markerPresent,
    markerValue,
    view: initialView,
    clientReady: Promise.resolve(),
    bootstrapInbox: createBootstrapInbox(),
    client: null,
    extensions: null,
    clientError: null,
    viewListeners: new Set(),
    fullscreenRequested: false,
  };
  state.clientReady = (async () => {
    if (!state.markerPresent) return;
    if (state.markerValue !== 'mcp') throw new Error(`Unsupported MCP App marker value: ${state.markerValue || '(empty)'}`);

    const app = new App({ name: 'Codex Agents Workflow', version: __CODEX_WORKFLOW_VERSION__ }, { availableDisplayModes: ['fullscreen'] });
    const extensions = new OpenAIExtensions(app);
    state.client = app;
    state.extensions = extensions;
    app.ontoolresult = result => state.bootstrapInbox.receive(result);
    app.addEventListener('hostcontextchanged', context => applyTheme(app, context));
    await app.connect();
    applyTheme(app);

    const hostContext = app.getHostContext();
    if (!state.fullscreenRequested && hostContext?.displayMode !== 'fullscreen' && hostContext?.availableDisplayModes?.includes('fullscreen')) {
      state.fullscreenRequested = true;
      try {
        const response = await app.requestDisplayMode({ mode: 'fullscreen' });
        if (response.mode !== 'fullscreen') console.warn(`The MCP host selected ${response.mode} after a fullscreen request.`);
      } catch (cause) {
        console.error('The MCP host advertised fullscreen support but rejected the display-mode request.', cause);
      }
    }
  })().catch(cause => {
    state.clientError = cause instanceof Error ? cause : new Error(String(cause));
  });
  return state;
}

const appState = globalState.__codexWorkflowAppState ??= createState();

export const isMcpAppContext = appState.markerPresent;
export const isMcpAppResource = appState.markerPresent && appState.markerValue === 'mcp';
export const hasInvalidMcpAppMarker = appState.markerPresent && appState.markerValue !== 'mcp';
export const token = isMcpAppContext ? '' : new URLSearchParams(location.hash.slice(1)).get('token') ?? '';
if (!isMcpAppContext) history.replaceState(null, '', location.pathname);

export function getAppView(): AppView { return appState.view; }

function syncView(view: AppView) {
  appState.view = view;
  const workflows = document.getElementById('workflow-shell');
  const settings = document.getElementById('settings-shell');
  if (workflows) workflows.hidden = view !== 'workflows';
  if (settings) settings.hidden = view !== 'settings';
  document.documentElement.dataset.codexWorkflowAppView = view;
  const styleTemplate = document.getElementById('settings-style-template') as HTMLTemplateElement | null;
  const styleId = 'codex-workflow-settings-styles';
  const currentStyles = document.getElementById(styleId);
  if (view === 'settings' && styleTemplate && !currentStyles) {
    document.head.append(styleTemplate.content.cloneNode(true));
    const inserted = document.head.lastElementChild;
    if (inserted) inserted.id = styleId;
  } else if (view === 'workflows') currentStyles?.remove();
  for (const listener of appState.viewListeners) listener(view);
}

export function setAppView(view: AppView) {
  if (!isMcpAppResource) throw new Error('Embedded view navigation is available only in the MCP App resource.');
  syncView(view);
}

export function subscribeAppView(listener: (view: AppView) => void) {
  appState.viewListeners.add(listener);
  return () => { appState.viewListeners.delete(listener); };
}

function errorFromToolResult(result: any): Error {
  const text = Array.isArray(result?.content) ? result.content.filter((block: any) => block?.type === 'text').map((block: any) => block.text).join('\n') : '';
  return Object.assign(new Error(text || 'The MCP host rejected the Workflow API request.'), { detail: result?.structuredContent ?? result, status: 502 });
}

export async function requestMcpApp(args: AppRequestArgs): Promise<unknown> {
  if (!isMcpAppResource) throw new Error(hasInvalidMcpAppMarker ? `Unsupported MCP App marker value: ${appState.markerValue || '(empty)'}` : 'The MCP App bridge is unavailable.');
  await appState.clientReady;
  if (appState.clientError) throw Object.assign(new Error(`Could not connect to the MCP App host: ${appState.clientError.message}`), { cause: appState.clientError });
  if (!appState.client) throw new Error('The MCP App host connection completed without an App client.');

  const method = args.method.toUpperCase();
  return appState.bootstrapInbox.request(args.path, method, args.body, async (path, requestMethod, requestBody) => {
    const toolArgs: Record<string, unknown> = { path, method: requestMethod };
    if (requestBody !== undefined) toolArgs.body = requestBody;
    const result = await appState.client!.callServerTool({ name: 'codex_agents_workflow_app_request', arguments: toolArgs }, { timeout: 120_000 });
    if (result.isError) throw errorFromToolResult(result);
    const response = result.structuredContent as AppRequestResult | undefined;
    if (!response || typeof response !== 'object' || !Number.isInteger(response.status) || !('body' in response)) {
      throw Object.assign(new Error('The MCP Workflow API tool returned an invalid response envelope.'), { detail: result, status: 502 });
    }
    return response;
  });
}

export async function launchWorkflowInConversation({ workflow_id, task, workspace }: { workflow_id: string; task: string; workspace?: string }) {
  if (!isMcpAppResource) throw new Error('Main (orchestration) needs an existing Codex conversation. Start this Workflow from that conversation.');
  await appState.clientReady;
  if (appState.clientError) throw appState.clientError;
  if (!appState.client) throw new Error('The MCP App host is unavailable.');
  const result = await appState.client.sendMessage({ role: 'user', content: [{type:'text', text: `Run the current published Workflow ${workflow_id} in this conversation. Task: ${task}${workspace ? `\nWorkspace: ${workspace}` : ''}. Main (orchestration) nodes must execute here using the existing working context.`}] });
  if (result.isError) throw new Error('The host declined the Workflow launch message. No Run was started.');
}

export async function downloadMcpAppFile(name: string, text: string, mimeType = 'application/json'): Promise<boolean> {
  if (hasInvalidMcpAppMarker) throw new Error('Unsupported MCP App marker value: ' + (appState.markerValue || '(empty)'));
  if (!isMcpAppResource) return false;
  await appState.clientReady;
  if (appState.clientError) throw Object.assign(new Error('Could not connect to the MCP App host: ' + appState.clientError.message), { cause: appState.clientError });
  if (!appState.client) throw new Error('The MCP App host connection completed without an App client.');
  if (!appState.client.getHostCapabilities()?.downloadFile) return false;
  const result = await appState.client.downloadFile({
    contents: [{ type: 'resource', resource: { uri: 'file:///' + encodeURIComponent(name), mimeType, text } }],
  });
  if (result.isError) throw new Error('The MCP host declined the requested file download.');
  return true;
}

function deepLinkUrl(): string | null {
  const fromHost = appState.extensions?.deepLink.getCurrent()?.url;
  if (fromHost) return fromHost;
  return isMcpAppContext && location.hash.length > 1 ? location.hash.slice(1) : null;
}

export function getInitialAppRoute(): { workflowId?: string; runId?: string } {
  const route = deepLinkUrl();
  if (!route) return {};
  let parsed: URL;
  try { parsed = new URL(route, location.href); }
  catch (cause) { throw new Error(`The MCP App deep link is invalid: ${String(cause)}`); }
  const workflowId = parsed.searchParams.get('workflow_id') ?? parsed.searchParams.get('workflowId')
    ?? (/^\/?(?:workflow|workflows)\/([^/]+)\/?$/.exec(parsed.pathname)?.[1] ? decodeURIComponent(/^\/?(?:workflow|workflows)\/([^/]+)\/?$/.exec(parsed.pathname)![1]) : undefined);
  const runId = parsed.searchParams.get('run_id') ?? parsed.searchParams.get('runId')
    ?? (/^\/?(?:run|runs)\/([^/]+)\/?$/.exec(parsed.pathname)?.[1] ? decodeURIComponent(/^\/?(?:run|runs)\/([^/]+)\/?$/.exec(parsed.pathname)![1]) : undefined);
  return { ...(workflowId ? { workflowId } : {}), ...(runId ? { runId } : {}) };
}

export function initializeAppView() {
  if (isMcpAppResource) syncView(appState.view);
}
