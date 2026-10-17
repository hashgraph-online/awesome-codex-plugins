const bootstrapPaths = new Set([
  '/api/config',
  '/api/workflow/list',
  '/api/workflow/capabilities',
  '/api/workflow/authoring_workflows',
  '/api/workflow/role_templates',
]);

// The Workbench API tunnels read operations through POST as well as mutations.
const workflowReadOperations = new Set([
  'list', 'capabilities', 'role_templates', 'authoring_workflows', 'read', 'runs',
  'run_snapshot', 'run_definition', 'node_details', 'current_main_pending', 'strict_status',
  'get', 'revisions', 'read_resource', 'source_status', 'import_review', 'routing_defaults',
  'local_clients', 'runtime_dependencies', 'skill_inventory', 'cache_cleanup_preview',
  'validate', 'export', 'export_workflow_package', 'verify_relocation',
]);

function canonical(value) {
  if (Array.isArray(value)) return value.map(canonical);
  if (!value || typeof value !== 'object') return value;
  return Object.fromEntries(Object.keys(value).sort().map(key => [key, canonical(value[key])]));
}

function bodyKey(value) {
  return JSON.stringify(canonical(value === undefined ? {} : value));
}

function responseError(body, status) {
  const message = body && typeof body === 'object' && typeof body.error === 'string'
    ? body.error
    : 'HTTP ' + status;
  return Object.assign(new Error(message), { detail: body, status });
}

function isMutation(path, method) {
  if (!['GET', 'HEAD', 'OPTIONS', 'POST'].includes(method)) return true;
  if (method !== 'POST' || !path.startsWith('/api/workflow/')) return false;
  return !workflowReadOperations.has(path.slice('/api/workflow/'.length));
}

export function createBootstrapInbox() {
  let resolveReady;
  const ready = new Promise(resolve => { resolveReady = resolve; });
  const entries = new Map();
  const consumed = new Set();
  let initialResultReceived = false;
  let captureError = null;

  function receive(result) {
    if (initialResultReceived) return;

    const meta = result && typeof result === 'object' ? result._meta : undefined;
    const bootstrap = meta && typeof meta === 'object' ? meta.bootstrap : undefined;
    const statuses = meta && typeof meta === 'object' ? meta.bootstrapStatus : undefined;
    const requests = meta && typeof meta === 'object' ? meta.bootstrapRequests : undefined;
    if (!bootstrap || typeof bootstrap !== 'object' || Array.isArray(bootstrap)) {
      captureError = new Error('The MCP App opener result is missing a valid _meta.bootstrap map.');
    } else if (!statuses || typeof statuses !== 'object' || Array.isArray(statuses)) {
      captureError = new Error('The MCP App opener result is missing a valid _meta.bootstrapStatus map.');
    } else if (!requests || typeof requests !== 'object' || Array.isArray(requests)) {
      captureError = new Error('The MCP App opener result is missing a valid _meta.bootstrapRequests map.');
    } else {
      const bodyPaths = Object.keys(bootstrap);
      const statusPaths = Object.keys(statuses);
      const requestPaths = Object.keys(requests);
      for (const path of bodyPaths) {
        const status = statuses[path];
        const request = requests[path];
        if (!bootstrapPaths.has(path) || bootstrap[path] === undefined) {
          captureError = new Error('The MCP App opener returned an invalid bootstrap entry for ' + path + '.');
          break;
        }
        if (!Number.isInteger(status) || status < 100 || status > 599) {
          captureError = new Error('The MCP App opener returned a missing or invalid bootstrap status for ' + path + '.');
          break;
        }
        if (!request || typeof request !== 'object' || !['GET', 'POST'].includes(request.method)) {
          captureError = new Error('The MCP App opener returned a missing or invalid bootstrap request descriptor for ' + path + '.');
          break;
        }
        entries.set(path, {
          body: bootstrap[path],
          status,
          method: request.method,
          requestBody: request.body === undefined ? {} : request.body,
        });
      }
      if (!captureError && (statusPaths.some(path => !bodyPaths.includes(path)) || requestPaths.some(path => !bodyPaths.includes(path)))) {
        captureError = new Error('The MCP App opener returned bootstrap metadata for a path without a response body.');
      }
    }

    initialResultReceived = true;
    resolveReady();
  }

  async function request(path, method, requestBody, fallback) {
    await ready;
    if (captureError) throw captureError;

    const normalizedMethod = method.toUpperCase();
    const entry = entries.get(path);
    const matchesBootstrap = entry
      && entry.method === normalizedMethod
      && bodyKey(entry.requestBody) === bodyKey(requestBody);
    if (matchesBootstrap && !consumed.has(path)) {
      consumed.add(path);
      if (entry.status < 200 || entry.status >= 300) throw responseError(entry.body, entry.status);
      return entry.body;
    }

    const response = await fallback(path, normalizedMethod, requestBody);
    if (!response || typeof response !== 'object' || !Number.isInteger(response.status) || !('body' in response)) {
      throw new Error('The MCP Workflow API tool returned an invalid response envelope.');
    }
    if (response.status < 200 || response.status >= 300) throw responseError(response.body, response.status);
    if (isMutation(path, normalizedMethod)) {
      entries.clear();
      consumed.clear();
    }
    return response.body;
  }

  return { receive, request, ready };
}
