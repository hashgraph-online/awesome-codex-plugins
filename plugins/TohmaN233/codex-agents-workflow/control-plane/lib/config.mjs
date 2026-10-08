import { createHash, randomUUID } from 'node:crypto';
import { constants as fsConstants } from 'node:fs';
import { access, chmod, lstat, mkdir, open, readFile, readdir, rename, stat, writeFile } from 'node:fs/promises';
import { homedir } from 'node:os';
import { basename, dirname, isAbsolute, join, resolve } from 'node:path';
import { resourcePath } from './workflow-paths.mjs';
import { canonicalJSON } from './workflow-revisions.mjs';
import { validateStrictConfig } from './execution/strict-config.mjs';
import {
  BUILTIN_NATIVE_AGENT_PROFILES,
  BUILTIN_NATIVE_PROVIDER_METADATA,
  RETIRED_NATIVE_PROVIDER_IDS,
  canonicalNativeProviderId,
} from './native-provider-identity.mjs';

export const CONFIG_VERSION = 6;
export const PROVIDER_KINDS = new Set(['native_agent', 'builtin_connector', 'external_mcp', 'mcp_tool', 'web_review', 'openai_compatible']);
export const STAGE_ROLES = new Set(['implementer', 'reviewer']);
export const STAGE_ACCESS = new Set(['read_only', 'bounded_write']);
export const ALLOWED_TEMPLATE_FIELDS = new Set([
  'task', 'context', 'constraints', 'verification', 'task_type_id', 'stage_id', 'provider_name',
]);

const ID_RE = /^[a-z0-9][a-z0-9._-]{0,63}$/;
const ENV_RE = /^[A-Z_][A-Z0-9_]{0,127}$/;
const SECRET_RE = /(authorization|proxy-authorization|cookie|set-cookie|api[-_]?key|token|secret|password)/i;
const MAX_CONFIG_BYTES = 512 * 1024;

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function object(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function text(value, field, { required = false, max = 20_000 } = {}) {
  if (value === undefined || value === null) {
    if (required) throw new Error(`${field} is required`);
    return '';
  }
  assert(typeof value === 'string', `${field} must be a string`);
  const result = value.trim();
  if (required) assert(result.length > 0, `${field} must not be empty`);
  assert(result.length <= max, `${field} exceeds ${max} characters`);
  return result;
}

function bool(value, fallback = false) {
  if (value === undefined) return fallback;
  assert(typeof value === 'boolean', 'expected boolean');
  return value;
}

function integer(value, fallback, min, max, field) {
  if (value === undefined) return fallback;
  assert(Number.isInteger(value) && value >= min && value <= max,
    `${field} must be an integer between ${min} and ${max}`);
  return value;
}

function id(value, field) {
  const result = text(value, field, { required: true, max: 64 });
  assert(ID_RE.test(result), `${field} must match ${ID_RE}`);
  return result;
}

function jsonClone(value, field) {
  try {
    return JSON.parse(JSON.stringify(value));
  } catch (error) {
    throw new Error(`${field} must be JSON-serializable: ${error.message}`);
  }
}

function rejectSecretKeys(value, path = 'provider.config') {
  if (Array.isArray(value)) {
    value.forEach((item, index) => rejectSecretKeys(item, `${path}[${index}]`));
    return;
  }
  if (!object(value)) return;
  for (const [key, child] of Object.entries(value)) {
    assert(!SECRET_RE.test(key), `${path}.${key} looks like a stored secret; use an environment-variable name instead`);
    rejectSecretKeys(child, `${path}.${key}`);
  }
}

export function isEnvironmentDisabled(env = process.env) {
  return /^(1|true|yes|on)$/i.test(String(env.CODEX_WORKFLOW_DISABLED || env.SOL_CONTROL_DISABLED || '').trim());
}

export function resolveConfigPath(env = process.env, userHome = homedir()) {
  const explicit = env.CODEX_WORKFLOW_CONFIG || env.SOL_CONTROL_CONFIG;
  if (explicit) {
    const variable = env.CODEX_WORKFLOW_CONFIG ? 'CODEX_WORKFLOW_CONFIG' : 'SOL_CONTROL_CONFIG';
    assert(isAbsolute(explicit), `${variable} must be an absolute path`);
    const resolved = resolve(explicit);
    // Keep the old variable as an input-only compatibility alias. A path in
    // the retired sol-advisor store is translated to the canonical store so it
    // cannot silently select a second active configuration.
    const legacyStore = isLegacyStoreDirectory(dirname(resolved));
    assert(env.CODEX_WORKFLOW_CONFIG ? !legacyStore : true,
      'CODEX_WORKFLOW_CONFIG cannot target the retired sol-advisor store; use the canonical codex-agents-workflow path');
    if (!env.CODEX_WORKFLOW_CONFIG && legacyStore) {
      return join(dirname(dirname(resolved)), 'codex-agents-workflow', basename(resolved));
    }
    return resolved;
  }
  const codexHome = env.CODEX_HOME
    ? (isAbsolute(env.CODEX_HOME) ? resolve(env.CODEX_HOME) : resolve(userHome, env.CODEX_HOME))
    : join(userHome, '.codex');
  return join(codexHome, 'codex-agents-workflow', 'control-plane.json');
}

function isLegacyStoreDirectory(path) {
  const name = basename(path);
  return process.platform === 'win32' ? name.toLowerCase() === 'sol-advisor' : name === 'sol-advisor';
}

function legacyStorePathFor(configPath) {
  const workflowStore = dirname(configPath);
  if (basename(workflowStore) === 'codex-agents-workflow') {
    return join(dirname(workflowStore), 'sol-advisor');
  }
  return null;
}

export function resolveAuditPath(configPath) {
  return join(dirname(configPath), 'control-plane-audit.jsonl');
}

export function validateEndpoint(value) {
  let endpoint;
  try {
    endpoint = new URL(text(value, 'provider.config.endpoint', { required: true, max: 2048 }));
  } catch (error) {
    throw new Error(`provider.config.endpoint is not a valid URL: ${error.message}`);
  }
  assert(!endpoint.username && !endpoint.password, 'provider endpoint must not contain credentials');
  assert(!endpoint.search && !endpoint.hash, 'provider endpoint must not contain a query or fragment');
  const loopback = ['localhost', '127.0.0.1', '::1', '[::1]'].includes(endpoint.hostname);
  assert(endpoint.protocol === 'https:' || (endpoint.protocol === 'http:' && loopback),
    'provider endpoint must use HTTPS, except HTTP loopback endpoints');
  return endpoint.toString();
}

function capabilities(raw, kind) {
  const value = object(raw) ? raw : {};
  return {
    read: bool(value.read, true),
    write: bool(value.write, kind === 'native_agent' || kind === 'external_mcp' || kind === 'mcp_tool'),
    background: bool(value.background, kind === 'builtin_connector' || kind === 'external_mcp' || kind === 'mcp_tool'),
  };
}

function validateNative(raw) {
  assert(object(raw), 'native provider config must be an object');
  const role = text(raw.role, 'provider.config.role', { required: true, max: 32 });
  assert(['implementer', 'reviewer', 'advisor'].includes(role),
    'native provider role must be implementer, reviewer, or advisor');
  return {
    agent_type: text(raw.agent_type, 'provider.config.agent_type', { required: true, max: 128 }),
    model: text(raw.model, 'provider.config.model', { required: true, max: 128 }),
    reasoning_effort: text(raw.reasoning_effort, 'provider.config.reasoning_effort', { required: true, max: 32 }),
    role,
    fresh_context: bool(raw.fresh_context, true),
    requested_sandbox: text(raw.requested_sandbox, 'provider.config.requested_sandbox', { max: 64 }),
    inactivity_timeout_ms: integer(raw.inactivity_timeout_ms, 0, 0, 86_400_000,
      'provider.config.inactivity_timeout_ms'),
  };
}

export function migrateBuiltinNativeAgentRoles(raw) {
  assert(object(raw), 'config must be an object');
  const migrated = jsonClone(raw, 'native Provider role migration');
  const sourceProviders = Array.isArray(migrated.providers) ? migrated.providers : [];
  const currentIds = new Set(sourceProviders.map((provider) => provider?.id)
    .filter((providerId) => BUILTIN_NATIVE_AGENT_PROFILES[providerId]));
  const emittedBuiltinIds = new Set();
  const providers = [];
  for (const provider of sourceProviders) {
    const retiredId = Object.hasOwn(RETIRED_NATIVE_PROVIDER_IDS, provider?.id);
    const canonicalId = canonicalNativeProviderId(provider?.id);
    if (retiredId && (currentIds.has(canonicalId) || emittedBuiltinIds.has(canonicalId))) continue;
    provider.id = canonicalId;
    const expected = BUILTIN_NATIVE_AGENT_PROFILES[canonicalId];
    if (expected) {
      Object.assign(provider, BUILTIN_NATIVE_PROVIDER_METADATA[canonicalId], {
        kind: 'native_agent',
        requires_user_approval: typeof provider.requires_user_approval === 'boolean'
          ? provider.requires_user_approval : false,
        capabilities: { read: true, write: true, background: false },
      });
      provider.config = {
        ...expected,
        fresh_context: true,
        requested_sandbox: 'workspace-write',
        inactivity_timeout_ms: 0,
      };
      emittedBuiltinIds.add(canonicalId);
    }
    if (provider?.kind === 'native_agent' && provider.config) provider.config.agent_type = 'default';
    providers.push(provider);
  }
  const builtinTemplate = sourceProviders.find((provider) => provider?.kind === 'native_agent');
  for (const [providerId, profile] of Object.entries(BUILTIN_NATIVE_AGENT_PROFILES)) {
    if (emittedBuiltinIds.has(providerId)) continue;
    const provider = {
      id: providerId,
      ...BUILTIN_NATIVE_PROVIDER_METADATA[providerId],
      kind: 'native_agent',
      enabled: true,
      requires_user_approval: false,
      capabilities: { read: true, write: true, background: false },
      config: {
        ...profile,
        fresh_context: true,
        requested_sandbox: 'workspace-write',
        inactivity_timeout_ms: 0,
      },
    };
    if (builtinTemplate?.capabilities && object(builtinTemplate.capabilities)) {
      provider.capabilities = { ...provider.capabilities, ...builtinTemplate.capabilities, read: true, write: true, background: false };
    }
    providers.push(provider);
  }
  migrated.providers = providers;
  if (migrated.strict_executor?.main_model === 'gpt-6-sol'
    && migrated.strict_executor.main_reasoning_effort === 'medium') {
    delete migrated.strict_executor.main_model;
    delete migrated.strict_executor.main_reasoning_effort;
  }
  for (const taskType of Array.isArray(migrated.task_types) ? migrated.task_types : []) {
    for (const stage of Array.isArray(taskType?.stages) ? taskType.stages : []) {
      if (typeof stage?.provider_id === 'string') stage.provider_id = canonicalNativeProviderId(stage.provider_id);
    }
  }
  return { config: migrated, changed: canonicalJSON(migrated) !== canonicalJSON(raw) };
}

function validateBuiltinConnector(raw) {
  assert(object(raw), 'built-in connector config must be an object');
  rejectSecretKeys(raw);
  const connector = text(raw.connector, 'provider.config.connector', { required: true, max: 64 });
  assert(['grok_acp', 'cursor_cdp'].includes(connector),
    'provider.config.connector must be grok_acp or cursor_cdp');
  const taskTimeoutMax = 86_400_000;
  const common = {
    connector,
    environment_mode: 'inherit',
    startup_timeout_ms: integer(raw.startup_timeout_ms, 15_000, 1_000, 120_000,
      'provider.config.startup_timeout_ms'),
    task_timeout_ms: integer(raw.task_timeout_ms, 0, 0, taskTimeoutMax,
      'provider.config.task_timeout_ms'),
    max_result_chars: integer(raw.max_result_chars, 131_072, 1_024, 524_288,
      'provider.config.max_result_chars'),
    single_active_run: true,
  };
  if (connector === 'grok_acp') {
    const binaryEnv = text(raw.binary_env ?? 'GROK_BIN',
      'provider.config.binary_env', { required: true, max: 128 });
    assert(ENV_RE.test(binaryEnv),
      'provider.config.binary_env must name an uppercase environment variable');
    const transport = text(raw.transport ?? 'leader_acp_stdio',
      'provider.config.transport', { required: true, max: 64 });
    assert(transport === 'leader_acp_stdio',
      'provider.config.transport must be leader_acp_stdio for grok_acp');
    return {
      ...common,
      max_task_duration_ms: integer(raw.max_task_duration_ms, 21_600_000,
        Math.max(common.task_timeout_ms, 1_000), 86_400_000, 'provider.config.max_task_duration_ms'),
      binary_env: binaryEnv,
      transport,
    };
  }
  const executableEnv = text(raw.executable_env ?? 'CURSOR_EXE',
    'provider.config.executable_env', { required: true, max: 128 });
  assert(ENV_RE.test(executableEnv),
    'provider.config.executable_env must name an uppercase environment variable');
  const transport = text(raw.transport ?? 'cdp_ui',
    'provider.config.transport', { required: true, max: 64 });
  assert(transport === 'cdp_ui',
    'provider.config.transport must be cdp_ui for cursor_cdp');
  const uiProfile = text(raw.ui_profile ?? 'agents_v2_2026_08',
    'provider.config.ui_profile', { required: true, max: 64 });
  assert(uiProfile === 'agents_v2_2026_08',
    'provider.config.ui_profile must be agents_v2_2026_08 in this release');
  return {
    ...common,
    executable_env: executableEnv,
    transport,
    cdp_port: integer(raw.cdp_port, 9223, 1024, 65535, 'provider.config.cdp_port'),
    command_timeout_ms: integer(raw.command_timeout_ms, 30_000, 1_000, 120_000,
      'provider.config.command_timeout_ms'),
    launch_if_closed: bool(raw.launch_if_closed, true),
    ui_profile: uiProfile,
  };
}

function validateMcp(raw) {
  assert(object(raw), 'MCP provider config must be an object');
  rejectSecretKeys(raw);
  assert(object(raw.tools) && Object.keys(raw.tools).length > 0,
    'MCP provider must declare at least one tool operation');
  const tools = {};
  for (const [operation, toolName] of Object.entries(raw.tools)) {
    tools[id(operation, 'provider.config.tools operation')] = text(
      toolName, `provider.config.tools.${operation}`, { required: true, max: 128 },
    );
  }
  return {
    protocol: text(raw.protocol, 'provider.config.protocol', { required: true, max: 128 }),
    model_label: text(raw.model_label, 'provider.config.model_label', { required: true, max: 128 }),
    tools,
    defaults: object(raw.defaults) ? jsonClone(raw.defaults, 'provider.config.defaults') : {},
    notes: text(raw.notes, 'provider.config.notes', { max: 4000 }),
  };
}

function validateWeb(raw) {
  assert(object(raw), 'web-review provider config must be an object');
  rejectSecretKeys(raw);
  const path = text(raw.path, 'provider.config.path', { required: true, max: 32 });
  assert(path === 'packet', 'web-review provider path must be packet');
  return {
    skill: text(raw.skill, 'provider.config.skill', { required: true, max: 256 }),
    source_repository: text(raw.source_repository, 'provider.config.source_repository', { max: 512 }),
    path,
    reviewer: text(raw.reviewer, 'provider.config.reviewer', { required: true, max: 128 }),
    model_label: text(raw.model_label, 'provider.config.model_label', { max: 128 }),
  };
}

function validateHeaders(raw) {
  if (raw === undefined) return {};
  assert(object(raw), 'provider.config.headers must be an object');
  const result = {};
  for (const [name, value] of Object.entries(raw)) {
    assert(!SECRET_RE.test(name), `provider.config.headers must not store sensitive header ${name}`);
    result[text(name, 'provider.config.headers name', { required: true, max: 128 })] =
      text(value, `provider.config.headers.${name}`, { required: true, max: 2048 });
  }
  return result;
}

function validateOpenAI(raw) {
  assert(object(raw), 'OpenAI-compatible provider config must be an object');
  const authType = text(raw.auth_type ?? 'bearer', 'provider.config.auth_type', { required: true, max: 32 });
  assert(['bearer', 'x-api-key', 'none'].includes(authType),
    'provider.config.auth_type must be bearer, x-api-key, or none');
  const apiKeyEnv = text(raw.api_key_env, 'provider.config.api_key_env', { max: 128 });
  if (authType !== 'none') {
    assert(ENV_RE.test(apiKeyEnv),
      'provider.config.api_key_env must name an uppercase environment variable');
  }
  const maxTokensField = text(raw.max_tokens_field ?? 'max_tokens',
    'provider.config.max_tokens_field', { required: true, max: 64 });
  assert(['max_tokens', 'max_completion_tokens'].includes(maxTokensField),
    'provider.config.max_tokens_field must be max_tokens or max_completion_tokens');
  const temperature = raw.temperature === undefined ? 0.2 : Number(raw.temperature);
  assert(Number.isFinite(temperature) && temperature >= 0 && temperature <= 2,
    'provider.config.temperature must be between 0 and 2');
  return {
    endpoint: validateEndpoint(raw.endpoint),
    model: text(raw.model, 'provider.config.model', { required: true, max: 256 }),
    api_key_env: apiKeyEnv,
    auth_type: authType,
    timeout_ms: integer(raw.timeout_ms, 120_000, 5_000, 900_000, 'provider.config.timeout_ms'),
    max_output_tokens: integer(raw.max_output_tokens, 4096, 1, 100_000, 'provider.config.max_output_tokens'),
    max_tokens_field: maxTokensField,
    temperature,
    system_prompt: text(raw.system_prompt, 'provider.config.system_prompt', { max: 20_000 }),
    headers: validateHeaders(raw.headers),
  };
}

function validateProvider(raw, index) {
  assert(object(raw), `providers[${index}] must be an object`);
  const kind = text(raw.kind, `providers[${index}].kind`, { required: true, max: 64 });
  assert(PROVIDER_KINDS.has(kind), `providers[${index}].kind is unsupported`);
  const validators = {
    native_agent: validateNative,
    builtin_connector: validateBuiltinConnector,
    external_mcp: validateMcp,
    mcp_tool: validateMcp,
    web_review: validateWeb,
    openai_compatible: validateOpenAI,
  };
  const normalizedKind = kind === 'mcp_tool' ? 'external_mcp' : kind;
  return {
    id: id(raw.id, `providers[${index}].id`),
    name: text(raw.name, `providers[${index}].name`, { required: true, max: 128 }),
    kind: normalizedKind,
    enabled: bool(raw.enabled, false),
    description: text(raw.description, `providers[${index}].description`, { max: 4000 }),
    requires_user_approval: bool(raw.requires_user_approval, false),
    capabilities: capabilities(raw.capabilities, normalizedKind),
    config: validators[kind](raw.config),
  };
}

function validateTemplate(value, field) {
  const template = text(value, field, { required: true, max: 60_000 });
  assert(template.includes('{{task}}'), `${field} must include {{task}}`);
  for (const match of template.matchAll(/{{\s*([a-zA-Z0-9_]+)\s*}}/g)) {
    assert(ALLOWED_TEMPLATE_FIELDS.has(match[1]),
      `${field} contains unsupported placeholder {{${match[1]}}}`);
  }
  const stripped = template.replace(/{{\s*[a-zA-Z0-9_]+\s*}}/g, '');
  assert(!stripped.includes('{{') && !stripped.includes('}}'),
    `${field} contains malformed template braces`);
  return template;
}

function validateStage(raw, taskTypeIndex, stageIndex) {
  const field = `task_types[${taskTypeIndex}].stages[${stageIndex}]`;
  assert(object(raw), `${field} must be an object`);
  const role = text(raw.role, `${field}.role`, { required: true, max: 32 });
  const access = text(raw.access, `${field}.access`, { required: true, max: 32 });
  assert(STAGE_ROLES.has(role), `${field}.role is unsupported`);
  assert(STAGE_ACCESS.has(access), `${field}.access is unsupported`);
  return {
    id: id(raw.id, `${field}.id`),
    role,
    provider_id: id(raw.provider_id, `${field}.provider_id`),
    access,
    requires_user_approval: bool(raw.requires_user_approval, false),
    template: validateTemplate(raw.template, `${field}.template`),
  };
}

const ROUTE_STAGE_SHAPES = {
  solo: [],
  delegate: [['implementation', 'implementer']],
  audit: [['review', 'reviewer']],
  full: [['implementation', 'implementer'], ['review', 'reviewer']],
};

export function deriveRouteFromStages(stages) {
  const signature = stages.map((stage) => `${stage.id}/${stage.role}`).join(',');
  for (const [route, shape] of Object.entries(ROUTE_STAGE_SHAPES)) {
    if (signature === shape.map(([stageId, role]) => `${stageId}/${role}`).join(',')) return route;
  }
  throw new Error('task type stages must be empty, implementation, review, or implementation then review');
}

function validateTaskType(raw, index) {
  assert(object(raw), `task_types[${index}] must be an object`);
  const stagesRaw = Array.isArray(raw.stages) ? raw.stages : [];
  const stages = stagesRaw.map((stage, stageIndex) => validateStage(stage, index, stageIndex));
  const route = deriveRouteFromStages(stages);
  return {
    id: id(raw.id, `task_types[${index}].id`),
    name: text(raw.name, `task_types[${index}].name`, { required: true, max: 128 }),
    enabled: bool(raw.enabled, true),
    description: text(raw.description, `task_types[${index}].description`, { max: 4000 }),
    role_instructions: text(raw.role_instructions, `task_types[${index}].role_instructions`, { max: 16000 }),
    route,
    stages,
    tags: Array.isArray(raw.tags)
      ? raw.tags.map((tag, tagIndex) => text(tag, `task_types[${index}].tags[${tagIndex}]`, { required: true, max: 64 }))
      : [],
  };
}

export function migrateConfigV1(raw, bundledDefaults) {
  assert(object(raw), 'config must be an object');
  assert(raw.version === 1, 'migrateConfigV1 accepts only config.version=1');
  const migrated = jsonClone(raw, 'legacy config');
  migrated.version = 2;
  migrated.providers = Array.isArray(migrated.providers) ? migrated.providers : [];
  migrated.scenarios = Array.isArray(migrated.scenarios) ? migrated.scenarios : [];

  const providerIds = new Set(migrated.providers.map((provider) => provider && provider.id));
  for (const providerId of ['cursor-local', 'grok-local']) {
    if (providerIds.has(providerId)) continue;
    const bundled = bundledDefaults.providers.find((provider) => provider.id === providerId);
    assert(bundled, `bundled migration provider is missing: ${providerId}`);
    migrated.providers.push(jsonClone(bundled, `bundled provider ${providerId}`));
    providerIds.add(providerId);
  }

  return migrated;
}

function migrateLegacyTemplate(template) {
  return String(template || '').replaceAll('{{scenario_id}}', '{{task_type_id}}');
}

function migratedStage(scenario, id, role, template = scenario.template) {
  return {
    id,
    role,
    provider_id: scenario.provider_id,
    access: scenario.read_only ? 'read_only' : 'bounded_write',
    requires_user_approval: Boolean(scenario.requires_user_approval),
    template: migrateLegacyTemplate(template),
  };
}

export function migrateConfigV2(raw) {
  assert(object(raw), 'config must be an object');
  assert(raw.version === 2, 'migrateConfigV2 accepts only config.version=2');
  const migrated = jsonClone(raw, 'version-2 config');
  const obsoleteBundledIds = new Set([
    'grok-readonly-advice', 'grok-bounded-change',
    'cursor-readonly-advice', 'cursor-bounded-change',
  ]);
  const migrationReviewer = migrated.providers.find((provider) =>
    ['native-sol', 'native-reviewer'].includes(provider?.id) && provider?.kind === 'native_agent'
      && provider?.capabilities?.read !== false)
    || migrated.providers.find((provider) =>
      provider?.kind === 'native_agent' && provider?.config?.role === 'reviewer'
        && provider?.capabilities?.read !== false)
    || migrated.providers.find((provider) =>
      provider?.capabilities?.read !== false && provider?.capabilities?.write === false);
  const taskTypes = (Array.isArray(migrated.scenarios) ? migrated.scenarios : [])
    .filter((scenario) => !(obsoleteBundledIds.has(scenario?.id) && scenario?.enabled === false))
    .map((scenario) => {
    const route = scenario.route;
    let stages;
    if (route === 'solo') stages = [];
    else if (route === 'delegate') stages = [migratedStage(scenario, 'implementation', 'implementer')];
    else if (route === 'audit') stages = [migratedStage(scenario, 'review', 'reviewer')];
    else if (route === 'full') {
      assert(migrationReviewer,
        `cannot migrate full scenario ${scenario.id}: no read-only reviewer Provider is configured`);
      stages = [
        migratedStage(scenario, 'implementation', 'implementer'),
        {
          id: 'review', role: 'reviewer', provider_id: migrationReviewer.id,
          access: 'read_only', requires_user_approval: false,
          template: 'Review the completed work for {{task}} using {{context}}. Respect {{constraints}} and verify with {{verification}}.',
        },
      ];
    } else {
      throw new Error(`cannot migrate scenario ${scenario.id}: unsupported route ${route}`);
    }
    return {
      id: scenario.id,
      name: scenario.name,
      enabled: route === 'full' ? false : scenario.enabled,
      description: route === 'full'
        ? `[Migration review required: choose separate implementation and review providers.] ${scenario.description || ''}`.trim()
        : scenario.description,
      route,
      tags: Array.isArray(scenario.tags) ? scenario.tags : [],
      stages,
    };
    });
  return {
    version: 3,
    global: migrated.global,
    providers: migrated.providers,
    task_types: taskTypes,
  };
}

export function migrateConfigV3(raw, bundledDefaults) {
  assert(object(raw), 'config must be an object');
  assert(raw.version === 3, 'migrateConfigV3 accepts only config.version=3');
  assert(object(bundledDefaults) && bundledDefaults.version === CONFIG_VERSION,
    `bundled defaults must use config.version=${CONFIG_VERSION}`);
  const migrated = jsonClone(raw, 'version-3 config');
  migrated.version = 4;
  return migrated;
}

export function migrateConfigV4(raw, bundledDefaults) {
  assert(object(raw), 'config must be an object');
  assert(raw.version === 4, 'migrateConfigV4 accepts only config.version=4');
  assert(object(bundledDefaults) && bundledDefaults.version === CONFIG_VERSION,
    `bundled defaults must use config.version=${CONFIG_VERSION}`);
  const migrated = jsonClone(raw, 'version-4 config');
  migrated.version = 5;
  return migrated;
}

export function migrateConfigV5(raw) {
  assert(object(raw), 'config must be an object');
  assert(raw.version === 5, 'migrateConfigV5 accepts only config.version=5');
  const migrated = jsonClone(raw, 'version-5 config');
  migrated.version = CONFIG_VERSION;
  // Approval booleans are policy, not derived metadata. A v5 file cannot tell
  // whether a bundled-looking value was inherited or explicitly chosen, so
  // migration must preserve the persisted value and leave any relaxation to an
  // explicit human config edit.
  return migrated;
}

export function validateConfig(raw) {
  assert(object(raw), 'config must be an object');
  assert([CONFIG_VERSION, 7].includes(raw.version), `config.version must be ${CONFIG_VERSION} or 7`);
  const providersRaw = Array.isArray(raw.providers) ? raw.providers : [];
  const taskTypesRaw = Array.isArray(raw.task_types) ? raw.task_types : [];
  assert(providersRaw.length > 0 && providersRaw.length <= 100,
    'config must contain between 1 and 100 providers');
  assert(raw.version === 7 ? taskTypesRaw.length === 0 : taskTypesRaw.length > 0 && taskTypesRaw.length <= 200,
    'config must contain between 1 and 200 task types');
  if (raw.version === 7) {
    assert(object(raw.workflow_store) && raw.workflow_store.schema_version === 1, 'config needs a v7 workflow store pointer');
    const relativePath = resourcePath(raw.workflow_store.relative_path);
    assert(!relativePath.includes('/') && !relativePath.startsWith('.'), 'config workflow store must be a direct named child');
    assert(object(raw.legacy_mapping), 'config legacy mapping must be an object');
    jsonClone(raw.legacy_mapping, 'config legacy mapping');
  }
  const providers = providersRaw.map(validateProvider);
  const taskTypes = taskTypesRaw.map(validateTaskType);
  const providerIds = new Set();
  for (const provider of providers) {
    assert(canonicalNativeProviderId(provider.id) === provider.id,
      `retired native provider id is not accepted in current config: ${provider.id}`);
    assert(!providerIds.has(provider.id), `duplicate provider id: ${provider.id}`);
    providerIds.add(provider.id);
  }
  const taskTypeIds = new Set();
  for (const taskType of taskTypes) {
    assert(!taskTypeIds.has(taskType.id), `duplicate task type id: ${taskType.id}`);
    taskTypeIds.add(taskType.id);
    for (const stage of taskType.stages) {
      assert(providerIds.has(stage.provider_id),
        `task type ${taskType.id} stage ${stage.id} references missing provider ${stage.provider_id}`);
      const provider = providers.find((item) => item.id === stage.provider_id);
      assert(provider.capabilities.read,
        `task type ${taskType.id} stage ${stage.id} requires provider read capability`);
      if (stage.access === 'bounded_write') {
        assert(provider.capabilities.write,
          `task type ${taskType.id} stage ${stage.id} requires provider write capability`);
      }
      if (provider.kind === 'native_agent') {
        assert(provider.config.role === stage.role || provider.config.role === 'advisor',
          `task type ${taskType.id} stage ${stage.id} role is incompatible with provider ${provider.id}`);
      }
    }
  }
  const global = object(raw.global) ? raw.global : {};
  return {
    version: raw.version,
    global: {
      enabled: bool(global.enabled, true),
      allow_direct_api: bool(global.allow_direct_api, false),
      console_title: text(global.console_title ?? 'Codex Agents Workflow',
        'global.console_title', { required: true, max: 128 }),
      max_prompt_chars: integer(global.max_prompt_chars, 80_000, 1000, 200_000,
        'global.max_prompt_chars'),
    },
    providers,
    ...(raw.version === 7 ? { workflow_store: jsonClone(raw.workflow_store, 'config workflow store'), legacy_mapping: jsonClone(raw.legacy_mapping, 'config legacy mapping'), strict_executor: validateStrictConfig(raw.strict_executor) } : { task_types: taskTypes }),
  };
}

async function exists(path) {
  try {
    await access(path, fsConstants.F_OK);
    return true;
  } catch (error) {
    if (error.code === 'ENOENT') return false;
    throw error;
  }
}

async function assertRegularNoSymlink(path, label) {
  const link = await lstat(path);
  assert(!link.isSymbolicLink(), `${label} must not be a symbolic link`);
  const file = await stat(path);
  assert(file.isFile(), `${label} is not a regular file`);
  return file;
}

async function assertLegacyStoreRelocatable(legacyStore) {
  const worktreeRoot = join(legacyStore, 'workflow-worktrees');
  if (!(await exists(worktreeRoot))) return;
  const entries = await readdir(worktreeRoot);
  const owned = entries.filter((name) => name.startsWith('owner-') || name.startsWith('tree-'));
  assert(!owned.length,
    `cannot migrate legacy Codex Agents Workflow store while owned Git worktrees exist (${owned.join(', ')}); reconcile or clean those worktrees first`);
}

export async function ensureConfigFile({ configPath, defaultConfigPath }) {
  if (await exists(configPath)) return;
  const legacyStore = legacyStorePathFor(configPath);
  if (legacyStore && await exists(legacyStore)) {
    await assertLegacyStoreRelocatable(legacyStore);
    const targetStore = dirname(configPath);
    await mkdir(dirname(targetStore), { recursive: true, mode: 0o700 });
    if (await exists(targetStore)) {
      throw new Error(`cannot migrate legacy Codex Agents Workflow store from ${legacyStore}: canonical store already exists without its configuration; reconcile the two stores before retrying`);
    }
    try {
      await rename(legacyStore, targetStore);
    } catch (error) {
      throw new Error(`cannot migrate legacy Codex Agents Workflow store from ${legacyStore}: ${error.message}`);
    }
    if (await exists(configPath)) return;
  }
  await mkdir(dirname(configPath), { recursive: true, mode: 0o700 });
  const body = await readFile(defaultConfigPath);
  try {
    await writeFile(configPath, body, { mode: 0o600, flag: 'wx' });
    await chmod(configPath, 0o600).catch(() => {});
  } catch (error) {
    if (error?.code !== 'EEXIST' || !(await exists(configPath))) throw error;
  }
}

async function writeConfigAtomic(validated, configPath) {
  await mkdir(dirname(configPath), { recursive: true, mode: 0o700 });
  const temporary = `${configPath}.write-${process.pid}-${randomUUID()}`;
  await writeFile(temporary, `${JSON.stringify(validated, null, 2)}\n`,
    { encoding: 'utf8', mode: 0o600, flag: 'wx' });
  await chmod(temporary, 0o600).catch(() => {});
  await rename(temporary, configPath);
}

async function finalizeLoadedConfig(candidate, configPath, forceWrite = false) {
  const migrated = migrateBuiltinNativeAgentRoles(candidate);
  const validated = validateConfig(migrated.config);
  if (forceWrite || migrated.changed) await writeConfigAtomic(validated, configPath);
  return validated;
}

export async function loadConfig({ configPath, defaultConfigPath }) {
  await ensureConfigFile({ configPath, defaultConfigPath });
  const file = await assertRegularNoSymlink(configPath, 'control-plane config path');
  assert(file.size <= MAX_CONFIG_BYTES, `control-plane config exceeds ${MAX_CONFIG_BYTES} bytes`);
  try {
    const raw = JSON.parse(await readFile(configPath, 'utf8'));
    if (raw?.version === 1) {
      const bundled = JSON.parse(await readFile(defaultConfigPath, 'utf8'));
      const migrated = migrateConfigV5(migrateConfigV4(
        migrateConfigV3(migrateConfigV2(migrateConfigV1(raw, bundled)), bundled), bundled));
      return finalizeLoadedConfig(migrated, configPath, true);
    }
    if (raw?.version === 2) {
      const bundled = JSON.parse(await readFile(defaultConfigPath, 'utf8'));
      const migrated = migrateConfigV5(migrateConfigV4(
        migrateConfigV3(migrateConfigV2(raw), bundled), bundled));
      return finalizeLoadedConfig(migrated, configPath, true);
    }
    if (raw?.version === 3) {
      const bundled = JSON.parse(await readFile(defaultConfigPath, 'utf8'));
      const migrated = migrateConfigV5(
        migrateConfigV4(migrateConfigV3(raw, bundled), bundled));
      return finalizeLoadedConfig(migrated, configPath, true);
    }
    if (raw?.version === 4) {
      const bundled = JSON.parse(await readFile(defaultConfigPath, 'utf8'));
      const migrated = migrateConfigV5(migrateConfigV4(raw, bundled));
      return finalizeLoadedConfig(migrated, configPath, true);
    }
    if (raw?.version === 5) {
      const migrated = migrateConfigV5(raw);
      return finalizeLoadedConfig(migrated, configPath, true);
    }
    return finalizeLoadedConfig(raw, configPath);
  } catch (error) {
    if (/config|provider|scenario|task type|stage|control-plane|migration/.test(error.message)) throw error;
    throw new Error(`control-plane config is invalid JSON: ${error.message}`);
  }
}

export function configRevision(config) {
  return createHash('sha256').update(canonicalJSON(config)).digest('hex');
}

export async function saveConfig(config, { configPath, expectedRevision = '' } = {}) {
  const validated = validateConfig(config);
  const { WorkflowStore } = await import('./workflow-store.mjs');
  const { writeDurableJSON } = await import('./workflow-events.mjs');
  return new WorkflowStore(dirname(resolve(configPath))).withWriter(async () => {
  if (await exists(configPath)) await assertRegularNoSymlink(configPath, 'control-plane config path');
  if (expectedRevision) {
    const current = validateConfig(JSON.parse(await readFile(configPath, 'utf8')));
    assert(configRevision(current) === expectedRevision,
      'configuration changed since it was loaded');
  }
  const current = await exists(configPath) ? validateConfig(JSON.parse(await readFile(configPath, 'utf8'))) : null;
  assert(current ? current.version === validated.version : validated.version === 6, 'configuration version changes require the transactional migration/restore API');
  if (current?.version === 7) assert(canonicalJSON(current.workflow_store) === canonicalJSON(validated.workflow_store) && canonicalJSON(current.legacy_mapping) === canonicalJSON(validated.legacy_mapping), 'config save cannot replace the workflow store pointer or legacy mapping');
  await writeDurableJSON(configPath, validated);
  return { config: validated, revision: configRevision(validated) };
  });
}

function modelLabel(provider) {
  if (provider.kind === 'native_agent') return provider.config.model;
  if (provider.kind === 'openai_compatible') return provider.config.model;
  if (provider.kind === 'builtin_connector' && provider.config.connector === 'grok_acp') {
    return 'Grok Build via ACP (user installation)';
  }
  if (provider.kind === 'builtin_connector' && provider.config.connector === 'cursor_cdp') {
    return 'Cursor user-selected model via local CDP';
  }
  return provider.config.model_label || null;
}

export function sanitizeConfig(config, { env = process.env } = {}) {
  const environmentDisabled = isEnvironmentDisabled(env);
  const providerMap = new Map(config.providers.map((provider) => [provider.id, provider]));
  return {
    version: config.version,
    effective_enabled: config.global.enabled && !environmentDisabled,
    environment_disabled: environmentDisabled,
    global: {
      enabled: config.global.enabled,
      allow_direct_api: config.global.allow_direct_api,
      console_title: config.global.console_title,
    },
    providers: config.providers.map((provider) => ({
      id: provider.id,
      name: provider.name,
      kind: provider.kind,
      enabled: provider.enabled,
      effective_enabled: provider.enabled && config.global.enabled && !environmentDisabled,
      description: provider.description,
      requires_user_approval: provider.requires_user_approval,
      capabilities: provider.capabilities,
      model_label: modelLabel(provider),
    })),
    task_types: (config.task_types ?? []).map((taskType) => {
      const stages = taskType.stages.map((stage) => {
        const provider = providerMap.get(stage.provider_id);
        return {
          id: stage.id,
          role: stage.role,
          provider_id: stage.provider_id,
          provider_kind: provider?.kind || 'missing',
          access: stage.access,
          requires_user_approval: Boolean(
            stage.requires_user_approval || provider?.requires_user_approval,
          ),
          effective_enabled: Boolean(provider?.enabled && config.global.enabled && !environmentDisabled),
          template_revision: createHash('sha256').update(stage.template).digest('hex').slice(0, 12),
        };
      });
      return {
        id: taskType.id,
        name: taskType.name,
        enabled: taskType.enabled,
        effective_enabled: Boolean(
          taskType.enabled && stages.every((stage) => stage.effective_enabled)
            && config.global.enabled && !environmentDisabled,
        ),
        description: taskType.description,
        route: taskType.route,
        tags: taskType.tags,
        stages,
      };
    }),
  };
}

export function findTaskType(config, taskTypeId) {
  assert(config.version !== 7, 'v7 legacy selection requires an authoritative Workflow Run; use workflow_start with the migrated workflow_id');
  return config.task_types.find((taskType) => taskType.id === taskTypeId) || null;
}

export function findProvider(config, providerId) {
  return config.providers.find((provider) => provider.id === providerId) || null;
}

export async function appendAuditEvent(configPath, event, { effectCommitted = false } = {}) {
  const revisionHash=event.revision_hash==null?null:text(event.revision_hash,'audit.revision_hash',{required:true,max:64});
  assert(revisionHash===null||/^[a-f0-9]{64}$/.test(revisionHash),'audit.revision_hash must be a SHA-256 revision');
  const roleAccess=event.access==null?null:text(event.access,'audit.access',{required:true,max:32});
  assert(roleAccess===null||STAGE_ACCESS.has(roleAccess),'audit.access must be read_only or bounded_write');
  const safe = {
    at: new Date().toISOString(),
    event: text(event.event, 'audit.event', { required: true, max: 64 }),
    task_type_id: event.task_type_id ? id(event.task_type_id, 'audit.task_type_id') : null,
    stage_id: event.stage_id ? id(event.stage_id, 'audit.stage_id') : null,
    provider_id: event.provider_id ? id(event.provider_id, 'audit.provider_id') : null,
    role_id: event.role_id ? id(event.role_id, 'audit.role_id') : null,
    revision_hash: revisionHash,
    access: roleAccess,
    outcome: text(event.outcome ?? 'ok', 'audit.outcome', { required: true, max: 64 }),
    detail: text(event.detail, 'audit.detail', { max: 1000 }),
    task_id: event.task_id ? id(event.task_id, 'audit.task_id') : null,
    action: text(event.action, 'audit.action', { max: 64 }),
    connector: text(event.connector, 'audit.connector', { max: 64 }),
    state: text(event.state, 'audit.state', { max: 64 }),
    error_code: text(event.error_code, 'audit.error_code', { max: 128 }),
  };
  const auditPath = resolveAuditPath(configPath);
  try {
    const { WorkflowStore } = await import('./workflow-store.mjs');
    await new WorkflowStore(dirname(resolve(configPath))).withWriter(async () => {
      if (await exists(auditPath)) await assertRegularNoSymlink(auditPath, 'control-plane audit path');
      const file = await open(auditPath, 'a', 0o600);
      try { await file.writeFile(`${JSON.stringify(safe)}\n`); await file.sync(); } finally { await file.close(); }
    });
  } catch (cause) { throw Object.assign(new Error(`Audit persistence failed: ${cause.message}`), { code: 'AUDIT_WRITE_FAILED', committed: effectCommitted, cause }); }
}
