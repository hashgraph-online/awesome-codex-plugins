import { dirname, isAbsolute, join, resolve } from 'node:path';
import { lstat, readFile, realpath, mkdtemp, rm } from 'node:fs/promises';
import { homedir, tmpdir } from 'node:os';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { createCodexClient } from './codex-app-server-client.mjs';
import { requireValue, noSymlinks } from '../workflow-paths.mjs';
import { canonicalJSON, digest } from '../workflow-revisions.mjs';

// These are adapter capabilities, not a release/platform allowlist. The selected
// executable supplies its own protocol schema and proves its read-only surface.
export const CODEX_EXECUTION_REQUIREMENTS = Object.freeze({
  initialize: ['clientInfo', 'capabilities'], 'account/read': ['refreshToken'], 'config/read': ['includeLayers'],
  'model/list': ['includeHidden', 'limit'], 'skills/list': ['cwds', 'forceReload'],
  'thread/start': ['cwd', 'model', 'modelProvider', 'sandbox', 'config', 'dynamicTools', 'ephemeral', 'allowProviderModelFallback'],
  'turn/start': ['threadId', 'input', 'effort', 'outputSchema'], 'turn/interrupt': ['threadId', 'turnId'],
  'command/exec': ['command', 'cwd', 'env', 'disableOutputCap', 'disableTimeout', 'sandboxPolicy', 'processId', 'streamStdin', 'streamStdoutStderr', 'timeoutMs'],
  'command/exec/write': ['deltaBase64', 'closeStdin', 'processId'], 'command/exec/terminate': ['processId'],
});
const discoveryRequirements = { initialize: CODEX_EXECUTION_REQUIREMENTS.initialize, 'skills/list': CODEX_EXECUTION_REQUIREMENTS['skills/list'] };
function requirementsFor(scope) {
  requireValue(['main', 'managed_native', 'discovery'].includes(scope), 'CODEX_QUALIFICATION_SCOPE', 'Unknown Codex capability qualification scope');
  return scope === 'discovery' ? discoveryRequirements : CODEX_EXECUTION_REQUIREMENTS;
}
const qualificationCache = new Map(), qualifications = new WeakMap(), exec = promisify(execFile);
export const codexQualification = settings => structuredClone(qualifications.get(settings) ?? null);

function keys(value, allowed, label) {
  requireValue(value && typeof value === 'object' && !Array.isArray(value) && Object.keys(value).every(key => allowed.includes(key)), 'STRICT_CONFIG', `${label} contains unknown fields`);
}
export function validateStrictConfig(raw = {}) {
  keys(raw, ['enabled', 'codex_binary', 'binary_sha256', 'authentication', 'main_model', 'main_reasoning_effort', 'inactivity_timeout_ms'], 'Strict executor');
  const auth = raw.authentication ?? {}; keys(auth, ['mode', 'api_key_env'], 'Strict authentication');
  const result = { enabled: raw.enabled ?? false, codex_binary: raw.codex_binary ?? '', binary_sha256: raw.binary_sha256 ?? '',
    authentication: { mode: auth.mode ?? 'host_chatgpt', api_key_env: auth.api_key_env ?? '' },
    main_model: raw.main_model ?? '', main_reasoning_effort: raw.main_reasoning_effort ?? '',
    inactivity_timeout_ms: raw.inactivity_timeout_ms ?? 0 };
  requireValue(typeof result.enabled === 'boolean' && typeof result.codex_binary === 'string' && result.codex_binary.length <= 4096 &&
    (!result.codex_binary || isAbsolute(result.codex_binary)) && typeof result.binary_sha256 === 'string' &&
    (!result.binary_sha256 || /^[a-f0-9]{64}$/.test(result.binary_sha256)), 'STRICT_CONFIG', 'Strict executor needs an absolute executable and its SHA-256');
  requireValue(['host_chatgpt', 'managed_chatgpt', 'environment_api_key'].includes(result.authentication.mode) && typeof result.authentication.api_key_env === 'string' &&
    (!result.authentication.api_key_env || /^[A-Z_][A-Z0-9_]{0,127}$/.test(result.authentication.api_key_env)), 'STRICT_CONFIG', 'Authentication stores only a supported mode and environment variable name');
  requireValue(typeof result.main_model === 'string' && (!result.main_model || /^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$/.test(result.main_model)) &&
    typeof result.main_reasoning_effort === 'string' && (!result.main_reasoning_effort || /^[a-z][a-z0-9_-]{0,31}$/.test(result.main_reasoning_effort)), 'STRICT_CONFIG', 'Main inherits the calling chat model and reasoning selection; explicit experiment identifiers must be valid');
  requireValue(Number.isSafeInteger(result.inactivity_timeout_ms) && result.inactivity_timeout_ms >= 0 && result.inactivity_timeout_ms <= 86_400_000,
    'STRICT_CONFIG', 'Strict inactivity_timeout_ms must be an integer from 0 through 86400000; 0 disables inactivity termination');
  requireValue(!result.enabled || result.codex_binary && result.binary_sha256 && (result.authentication.mode !== 'environment_api_key' || result.authentication.api_key_env), 'STRICT_CONFIG', 'Enabled Strict executor requires complete binary and authentication settings');
  return result;
}

async function verifiedDistributionFile(path, expectedHash, label) {
  try { await noSymlinks(path); }
  catch (error) {
    if (error.code === 'ENOENT') requireValue(false, label === 'Codex executable' ? 'CODEX_BINARY_MISSING' : 'CODEX_COMPANION_MISSING', `${label} is missing from the selected distribution: ${path}`);
    throw error;
  }
  const stat = await lstat(path);
  requireValue(stat.isFile() && stat.size > 0 && stat.size <= 512 * 1024 * 1024,
    label === 'Codex executable' ? 'CODEX_BINARY_CHANGED' : 'CODEX_COMPANION_CHANGED', `${label} is not a bounded regular file: ${path}`);
  requireValue(digest(await readFile(path)) === expectedHash,
    label === 'Codex executable' ? 'CODEX_BINARY_CHANGED' : 'CODEX_COMPANION_CHANGED', `${label} differs from the qualified distribution: ${path}`);
}

export async function verifyCodexDistribution(binary, expected) {
  let target;
  try { target = await realpath(binary); }
  catch (error) { if (error.code === 'ENOENT') requireValue(false, 'CODEX_BINARY_MISSING', `Selected Codex executable is missing: ${binary}`); throw error; }
  await verifiedDistributionFile(target, expected.sha256, 'Codex executable');
  for (const [name, hash] of Object.entries(expected.companions ?? {}))
    await verifiedDistributionFile(join(dirname(target), name), hash, name);
  return target;
}

function capability(condition, name) {
  requireValue(condition, 'CODEX_CAPABILITY_UNSUPPORTED', `Selected Codex App Server lacks required capability: ${name}`, { capability: name });
}
function dereference(schema, value) {
  if (!value?.$ref) return value;
  capability(value.$ref.startsWith('#/'), 'local protocol references');
  return value.$ref.slice(2).split('/').reduce((item, key) => item?.[key.replaceAll('~1', '/').replaceAll('~0', '~')], schema);
}
function methodParams(schema, method) {
  const variants = schema?.oneOf ?? schema?.anyOf ?? [];
  const entry = variants.find(item => item.properties?.method?.enum?.includes(method) || item.properties?.method?.const === method);
  capability(entry, method);
  return dereference(schema, entry.properties.params);
}
export function validateCodexProtocol(schemas, { scope = 'main' } = {}) {
  const schema = schemas.ClientRequest;
  const requirements = requirementsFor(scope);
  for (const [method, fields] of Object.entries(requirements)) {
    const params = methodParams(schema, method);
    for (const field of fields) capability(Object.hasOwn(params?.properties ?? {}, field), `${method}.${field}`);
    for (const field of params?.required ?? []) capability(fields.includes(field), `${method}.required:${field}`);
  }
  if (scope === 'discovery') return { scope, methods: Object.keys(requirements) };
  const call = methodParams(schemas.ServerRequest, 'item/tool/call');
  for (const field of ['threadId', 'turnId', 'callId', 'tool', 'arguments']) capability(Object.hasOwn(call?.properties ?? {}, field), `item/tool/call.${field}`);
  for (const method of ['turn/completed', 'item/completed', 'thread/tokenUsage/updated']) methodParams(schemas.ServerNotification, method);
  const dynamic = schema?.definitions?.DynamicToolSpec ?? schema?.$defs?.DynamicToolSpec;
  const variants = dynamic?.oneOf ?? dynamic?.anyOf ?? [dynamic];
  const functionTool = variants.find(item => ['name', 'description', 'inputSchema'].every(field => Object.hasOwn(item?.properties ?? {}, field))
    && (item.properties.type === undefined || item.properties.type.enum?.includes('function') || item.properties.type.const === 'function'));
  capability(functionTool, 'thread/start.dynamicTools:function');
  const tagged = Boolean(functionTool.properties.type);
  for (const field of functionTool.required ?? []) capability(['name', 'description', 'inputSchema', ...(tagged ? ['type'] : [])].includes(field), `dynamicTools.required:${field}`);
  return { scope, methods: Object.keys(requirements), dynamic_tool_format: tagged ? 'tagged_function' : 'untagged_function' };
}

async function readCodexProtocol(binary, env, { scope = 'main' } = {}) {
  const directory = await mkdtemp(join(tmpdir(), 'workflow-codex-protocol-'));
  let result, primary;
  try {
    try { await exec(binary, ['app-server', 'generate-json-schema', '--experimental', '--out', directory], { env, windowsHide: true, timeout: 10000, maxBuffer: 65536 }); }
    catch (cause) { throw Object.assign(new Error('Selected Codex cannot export its experimental App Server protocol', { cause }), { code: 'CODEX_CAPABILITY_UNSUPPORTED', capability: 'app-server.generate-json-schema' }); }
    result = {};
    for (const name of scope === 'discovery' ? ['ClientRequest'] : ['ClientRequest', 'ServerRequest', 'ServerNotification']) {
      const file = join(directory, `${name}.json`), info = await lstat(file);
      capability(info.isFile() && info.size <= 16 * 1024 * 1024, `protocol schema:${name}`);
      result[name] = JSON.parse(await readFile(file, 'utf8'));
    }
  } catch (error) { primary = error; }
  try { await rm(directory, { recursive: true }); }
  catch (error) { if (primary) throw Object.assign(new AggregateError([primary, error], 'Protocol discovery and cleanup failed'), { code: 'CODEX_QUALIFICATION_INCOMPLETE' }); throw error; }
  if (primary) throw primary;
  return result;
}
async function profileFileHash(path) {
  try { await noSymlinks(path); return digest(await readFile(path)); }
  catch (error) { if (error.code === 'ENOENT') return null; throw error; }
}
async function probeReadOnly(binary, home, env, settings, clientFactory, scope) {
  const client = clientFactory(binary, { home, cwd: home, env });
  let result, primary;
  try {
    let current;
    const read = async (method, params) => {
      current = method;
      try { return await client.call(method, params); }
      catch (cause) { throw Object.assign(new Error(`Selected Codex App Server read-only probe failed: ${method}`, { cause }),
        { code: 'CODEX_CAPABILITY_PROBE_FAILED', capability: method, ...(cause.rpc_code === undefined ? {} : { rpc_code: cause.rpc_code }) }); }
    };
    const initialized = await read('initialize', { clientInfo: { name: 'codex_workflow_qualification', version: '1.0.0' }, capabilities: { experimentalApi: true } });
    client.initialized();
    if (scope !== 'discovery') {
      const account = await read('account/read', { refreshToken: false });
      capability(account && (Object.hasOwn(account, 'account') || typeof account.requiresOpenaiAuth === 'boolean'), current);
      if (settings.authentication.mode === 'host_chatgpt') requireValue(account.account?.type === 'chatgpt', 'CODEX_AUTH_REQUIRED', 'Selected Codex profile has no authenticated ChatGPT account');
      if (settings.authentication.mode === 'managed_chatgpt' && account.account) requireValue(account.account.type === 'chatgpt', 'CODEX_AUTH_MODE', 'Selected managed ChatGPT profile uses another authentication type');
      const config = await read('config/read', { includeLayers: false }); capability(config?.config && typeof config.config === 'object', current);
      const models = await read('model/list', { includeHidden: true, limit: 1 }); capability(Array.isArray(models?.data), current);
    }
    const skills = await read('skills/list', { cwds: [home], forceReload: false });
    capability(Array.isArray(skills?.data) && skills.data.length === 1 && Array.isArray(skills.data[0]?.skills) && Array.isArray(skills.data[0]?.errors), current);
    result = { user_agent: typeof initialized?.userAgent === 'string' ? initialized.userAgent : null,
      read_only_methods: scope === 'discovery' ? ['initialize', 'skills/list'] : ['initialize', 'account/read', 'config/read', 'model/list', 'skills/list'] };
  } catch (error) { primary = error; }
  try { await client.close(); }
  catch (error) { if (primary) throw Object.assign(new AggregateError([primary, error], 'Codex qualification and owned process shutdown failed'), { code: 'CODEX_QUALIFICATION_INCOMPLETE' }); throw error; }
  if (primary) throw primary;
  return result;
}

export async function qualifiedCodexBinary(settings, { env = process.env, schemaReader = readCodexProtocol, clientFactory = createCodexClient, cache = qualificationCache, scope = 'main' } = {}) {
  requirementsFor(scope);
  const binary = await verifyCodexDistribution(settings.codex_binary, { sha256: settings.binary_sha256 });
  const home = resolve(env.CODEX_HOME || join(homedir(), '.codex'));
  const profile = { config: await profileFileHash(join(home, 'config.toml')), auth: await profileFileHash(join(home, 'auth.json')) };
  const key = digest(canonicalJSON({ binary, sha256: settings.binary_sha256, home, profile, scope, authentication: settings.authentication,
    environment: digest(canonicalJSON({ path: env.PATH ?? env.Path ?? '', api_key: settings.authentication.api_key_env ? env[settings.authentication.api_key_env] ?? null : null })) }));
  if (!cache.has(key)) {
    const pending = (async () => {
      const schemas = await schemaReader(binary, env, { scope }), capabilities = validateCodexProtocol(schemas, { scope });
      const runtime = await probeReadOnly(binary, home, env, settings, clientFactory, scope);
      requireValue(await verifyCodexDistribution(settings.codex_binary, { sha256: settings.binary_sha256 }) === binary,
        'CODEX_BINARY_CHANGED', 'Selected Codex executable alias changed during qualification');
      return { boundary: 'selected-app-server-protocol', selected_path: settings.codex_binary, resolved_path: binary,
        executable_sha256: settings.binary_sha256, protocol_sha256: digest(canonicalJSON(schemas)), platform: process.platform, architecture: process.arch,
        ...capabilities, ...runtime, model_calls: 0 };
    })();
    cache.set(key, pending);
    try { await pending; } catch (error) { cache.delete(key); throw error; }
  }
  qualifications.set(settings, await cache.get(key));
  return settings;
}

export async function qualifiedStrictSettings(config, env = process.env, options = {}) {
  const settings = validateStrictConfig(config.strict_executor);
  requireValue(settings.enabled, 'STRICT_DISABLED', 'The user has not enabled the Codex executor');
  requireValue(settings.authentication.mode !== 'environment_api_key' || Boolean(env[settings.authentication.api_key_env]), 'CODEX_CREDENTIAL_MISSING', 'Configured authentication environment variable is unavailable');
  await qualifiedCodexBinary(settings, { ...options, env });
  return settings;
}
