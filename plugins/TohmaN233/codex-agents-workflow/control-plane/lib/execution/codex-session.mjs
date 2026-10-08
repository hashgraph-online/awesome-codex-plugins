import {prepareDirectToolCatalog} from './direct-tool-catalog.mjs';
import { mkdtemp, readFile, mkdir, open, realpath } from 'node:fs/promises';
import { homedir } from 'node:os';
import { join, resolve, dirname } from 'node:path';
import { createCodexClient } from './codex-app-server-client.mjs';
import { createCodexCommandBroker } from './codex-command-broker.mjs';
import { agentTurnActivity } from './agent-activity.mjs';
import { authenticatedModel } from './codex-model-catalog.mjs';
import { buildCodexProfile, cleanupCodexProfile, recordProfileChild, isolatedEnvironment, pinObservedModel, profileOverrides, STRICT_INSTRUCTIONS } from './codex-profile-builder.mjs';
import { createSkillPolicy } from './codex-skill-policy.mjs';
import { skillPathKey } from './codex-skill-policy.mjs';
import { canonicalJSON, digest, prepareResources } from '../workflow-revisions.mjs';
import { requireValue, noSymlinks } from '../workflow-paths.mjs';
import { ensureDirectory } from '../workflow-paths.mjs';
import { writeDurableJSON } from '../workflow-events.mjs';

function scrubTurnDiagnostic(value, limit = 1500) {
  return String(value ?? '')
    .replace(/\bBearer\s+\S+/ig, 'Bearer [redacted]')
    .replace(/((?:api[_-]?key|access[_-]?token|refresh[_-]?token|authorization|password|cookie|secret)\s*[:=]\s*)\S+/ig, '$1[redacted]')
    .replace(/https?:\/\/\S+/ig, '[redacted-url]')
    .slice(0, limit);
}

function safeTurnDiagnostic(events, threadId, turnId) {
  const raw = [...events].reverse().find(item => item.method === 'error'
    && (!item.params?.threadId || item.params.threadId === threadId)
    && (!item.params?.turnId || item.params.turnId === turnId));
  const error = raw?.params?.error ?? raw?.params;
  const message = typeof error?.message === 'string' ? error.message
    : typeof raw?.params?.message === 'string' ? raw.params.message : 'no error diagnostic emitted';
  const code = typeof error?.code === 'string' ? error.code
    : typeof error?.codexErrorInfo?.code === 'string' ? error.codexErrorInfo.code : null;
  return `${code ? `${code}: ` : ''}${scrubTurnDiagnostic(message)}`;
}

function usageFrom(events, threadId, turnId) {
  const event = [...events].reverse().find(item => item.method === 'thread/tokenUsage/updated'
    && item.params?.threadId === threadId && (!turnId || !item.params?.turnId || item.params.turnId === turnId));
  const usage = event?.params?.tokenUsage?.last;
  if (!usage) return { available: false };
  const result = { available: true };
  for (const [source, target] of [['inputTokens','input_tokens'],['cachedInputTokens','cached_input_tokens'],['cacheWriteInputTokens','cache_write_input_tokens'],['outputTokens','output_tokens'],['reasoningOutputTokens','reasoning_output_tokens']]) {
    if (Number.isSafeInteger(usage[source]) && usage[source] >= 0) result[target] = usage[source];
  }
  return result;
}

async function environmentKeyModel(client, model, effort, onCatalog = async () => {}) {
  const models = [], cursors = new Set(); let cursor;
  do {
    requireValue(cursors.size < 20, 'CODEX_MODEL_SCHEMA', 'Model pagination exceeded its bounded page count');
    const page = await client.call('model/list', { includeHidden: true, limit: 100, ...(cursor ? { cursor } : {}) });
    requireValue(Array.isArray(page.data) && models.length + page.data.length <= 1000, 'CODEX_MODEL_SCHEMA', 'Invalid model inventory');
    models.push(...page.data); cursor = page.nextCursor;
    requireValue(!cursor || typeof cursor === 'string' && !cursors.has(cursor), 'CODEX_MODEL_SCHEMA', 'Invalid model pagination cursor');
    if (cursor) cursors.add(cursor);
  } while (cursor);
  const matches = models.filter(item => item.model === model);
  const supported = matches.length === 1 && Boolean(matches[0].supportedReasoningEfforts?.some(item => item.reasoningEffort === effort));
  await onCatalog({ requested_model: model, requested_effort: effort, inventory_count: models.length,
    match_count: matches.length, effort_supported: supported,
    model_ids: models.map(item => item.model).filter(item => typeof item === 'string' && /^[A-Za-z0-9._:/-]{1,128}$/.test(item)).join(',').slice(0, 4096) });
  requireValue(supported, 'CODEX_MODEL_UNAVAILABLE', `Configured API-key model/effort is absent from App Server inventory: ${model}/${effort}`);
}

export function codexEventMetadata(event) {
  const p = event.params ?? {};
  const metadata = { method: event.method, thread_id: typeof p.threadId === 'string' ? p.threadId : null,
    turn_id: typeof p.turn?.id === 'string' ? p.turn.id : typeof p.turnId === 'string' ? p.turnId : null,
    item_type: typeof p.item?.type === 'string' ? p.item.type : null,
    status: typeof p.turn?.status === 'string' ? p.turn.status : null,
  };
  if (event.method === 'error') {
    const error = p.error ?? p;
    metadata.error_code = typeof error?.code === 'string' ? scrubTurnDiagnostic(error.code, 100) : null;
    metadata.diagnostic = safeTurnDiagnostic([event], metadata.thread_id, metadata.turn_id);
  }
  if (event.method === 'thread/tokenUsage/updated') {
    const usage=usageFrom([event], metadata.thread_id, metadata.turn_id);
    metadata.usage_available=usage.available;
    for(const field of ['input_tokens','cached_input_tokens','cache_write_input_tokens','output_tokens','reasoning_output_tokens'])if(Number.isSafeInteger(usage[field]))metadata[field]=usage[field];
  }
  return metadata;
}

async function normalModelMetadata({client,home,cwd,model}) {
  const configuration=await client.call('config/read',{cwd,includeLayers:false});
  const configured=configuration.config?.model_catalog_json;
  requireValue(configured===undefined||configured===null||typeof configured==='string',
    'CODEX_MODEL_METADATA','Configured model catalog path is invalid');
  const source=configured?resolve(cwd,configured):join(home,'models_cache.json');
  const catalog=JSON.parse(await readFile(source,'utf8'));
  const candidates=catalog.models?.filter(item=>item.slug===model)??[];
  requireValue(candidates.length===1,'CODEX_MODEL_METADATA','Exact selected model metadata is unavailable for normal tool routing');
  return candidates[0];
}

// Production nodes use the user's ordinary Codex home and tool configuration.
// The Run's read_only/bounded_write authorization selects the native read-only/
// workspace-write sandbox; App Server keeps the user's approval policy. The
// separate receipt records this attempt without becoming a CODEX_HOME or
// changing model capabilities or instructions. A per-session catalog snapshot
// changes only tool routing to bypass the separate Code Mode output cap.
export async function createCodexSession(options) {
  const { cwd, model, effort, access, env = process.env, onEvent = () => {}, onToolRead = () => {} } = options;
  requireValue(['read_only', 'bounded_write'].includes(access), 'CODEX_ACCESS_MODE', 'Normal Codex node requires its exact Run access mode');
  requireValue(['tagged_function', 'untagged_function'].includes(options.dynamicToolFormat),
    'CODEX_CAPABILITY_UNSUPPORTED', 'Normal Codex session requires the selected executable dynamic-tool capability evidence');
  const sandbox = access === 'read_only' ? 'read-only' : 'workspace-write';
  const authenticationMode = options.authentication?.mode ?? (options.hostAuth ? 'host_chatgpt' : 'managed_chatgpt');
  requireValue(['host_chatgpt', 'managed_chatgpt', 'environment_api_key'].includes(authenticationMode),
    'CODEX_AUTH_MODE', 'Unsupported normal Codex authentication mode');
  const apiKeyEnv = options.authentication?.api_key_env;
  if (authenticationMode === 'environment_api_key') requireValue(typeof apiKeyEnv === 'string' && /^[A-Z_][A-Z0-9_]{0,127}$/.test(apiKeyEnv)
    && typeof env[apiKeyEnv] === 'string' && env[apiKeyEnv].length > 0, 'CODEX_CREDENTIAL_MISSING', 'Configured API key environment variable is unavailable');
  const apiKeyProvider = 'workflow_environment_api_key';
  const apiKeyOverrides = authenticationMode === 'environment_api_key' ? [
    `model_providers.${apiKeyProvider}.name="Workflow API key"`,
    `model_providers.${apiKeyProvider}.base_url="https://api.openai.com/v1"`,
    `model_providers.${apiKeyProvider}.env_key=${JSON.stringify(apiKeyEnv)}`,
    `model_providers.${apiKeyProvider}.wire_api="responses"`,
    `model_providers.${apiKeyProvider}.requires_openai_auth=false`,
  ] : [];
  requireValue(typeof cwd === 'string' && typeof model === 'string' && typeof effort === 'string',
    'CODEX_SESSION_ARGUMENTS', 'Normal Codex session requires a workspace, model and effort');
  const binary = await realpath(options.binary);
  await noSymlinks(binary);
  requireValue(!options.expectedBinaryPath || binary === options.expectedBinaryPath, 'CODEX_BINARY_CHANGED', 'Selected Codex executable alias changed its verified target before process launch');
  const binaryHash = digest(await readFile(binary));
  requireValue(binaryHash === options.expectedBinaryHash, 'CODEX_BINARY_CHANGED', 'Codex executable changed before process launch');
  const home = resolve(env.CODEX_HOME || join(homedir(), '.codex'));
  await ensureDirectory(options.parent);
  const receiptHome = await mkdtemp(join(options.parent, 'codex-attempt-'));
  const profile = { home, receipt_home: receiptHome, binary_sha256: binaryHash, user_owned_home: true };
  const receipt = { schema_version: 1, owner: options.owner ?? {}, model, effort,
    executable_sha256: binaryHash, user_codex_home: home, created_at: new Date().toISOString(),
    access, sandbox, thread_ids: [], turn_ids: [], status: 'preparing' };
  const record = async fields => { Object.assign(receipt, fields); await writeDurableJSON(join(receiptHome, 'attempt.json'), receipt); };
  await record({});
  const clientFactory = options.clientFactory ?? createCodexClient;
  let client, activeThread = null, activeTurn = null, continuationThread = null, closed = false, turns = 0, closing, catalogChecked = false, skillPins, toolCatalog;
  const commandBroker = createCodexCommandBroker({ binary, home, cwd, access, env,
    spoolRoot: join(receiptHome, 'command-output'), getClient: () => client,
    allowedPaths: options.allowedPaths ?? [],
    recoverToolErrors:true,
    networkAccess: options.commandNetworkAccess ?? false,
    onOperation: operation => onEvent({ method: 'workflow/command', ...operation }) });
  async function pinnedSkills() {
    if (!skillPins) {
      const allowed = options.allowedSkills ?? [];
      requireValue(Array.isArray(allowed) && allowed.length <= 64, 'CODEX_SKILL_PIN', 'Node Skill snapshot list is invalid');
      const next = new Map();
      for (const skill of allowed) {
        const key = skillPathKey(skill.source_path);
        requireValue(!next.has(key) && typeof skill.name === 'string' && skill.name.length > 0
          && /^[a-f0-9]{64}$/.test(skill.source_hash), 'CODEX_SKILL_PIN', 'Node Skill snapshot identity is invalid');
        const prepared = prepareResources(skill.files);
        const main = prepared.manifest.find(file => file.path === 'SKILL.md');
        requireValue(main?.sha256 === skill.source_hash, 'CODEX_SKILL_PIN_CHANGED', 'Pinned Skill instructions differ from the Run snapshot');
        const directory = join(receiptHome, 'skills', digest(key + '\0' + skill.source_hash));
        for (const file of prepared.manifest) {
          const path = join(directory, ...file.path.split('/'));
          await mkdir(dirname(path), { recursive: true });
          await noSymlinks(dirname(path));
          const handle = await open(path, 'wx', 0o400);
          try { await handle.writeFile(prepared.blobs.get(file.sha256)); await handle.sync(); }
          finally { await handle.close(); }
        }
        next.set(key, { name: skill.name, source_path: skill.source_path,
          path: join(directory, 'SKILL.md'), files: prepared.manifest.map(file => ({ path: join(directory, ...file.path.split('/')), sha256: file.sha256 })) });
      }
      skillPins = next;
      await record({ pinned_skill_count: next.size });
    }
    for (const pin of skillPins.values()) for (const file of pin.files) {
      await noSymlinks(file.path);
      requireValue(digest(await readFile(file.path)) === file.sha256, 'CODEX_SKILL_PIN_CHANGED', 'Materialized Skill snapshot changed');
    }
    return skillPins;
  }
  const requireOpen = () => {
    requireValue(!closed, 'CODEX_SESSION_CLOSED', 'Codex session execution was revoked');
    options.assertActive?.();
  };
  const session = {
    profile,
    get client() { return client; },
    async authentication() {
      if (authenticationMode === 'environment_api_key') return { authenticated: typeof env[apiKeyEnv] === 'string' && env[apiKeyEnv].length > 0, type: 'environment_api_key' };
      const result = await client.call('account/read', { refreshToken: false });
      requireValue(result && typeof result.requiresOpenaiAuth === 'boolean', 'CODEX_AUTH_SCHEMA', 'Unsupported account metadata response');
      return { authenticated: Boolean(result.account) || result.requiresOpenaiAuth === false, type: result.account?.type ?? null };
    },
    async login({ apiKeyEnv } = {}) {
      requireValue(authenticationMode !== 'host_chatgpt', 'CODEX_AUTH_MODE', 'Host ChatGPT does not start another login flow');
      if (authenticationMode === 'environment_api_key') {
        requireValue(apiKeyEnv === options.authentication?.api_key_env && typeof env[apiKeyEnv] === 'string' && env[apiKeyEnv].length > 0,
        'CODEX_CREDENTIAL_MISSING', 'Configured API key environment variable is unavailable');
        return session.authentication();
      }
      requireValue(apiKeyEnv === undefined, 'CODEX_AUTH_MODE', 'Managed ChatGPT login does not accept an API key');
      const result = await client.call('account/login/start', { type: 'chatgpt' });
      requireValue(typeof result.authUrl === 'string' && typeof result.loginId === 'string', 'CODEX_AUTH_SCHEMA', 'Managed login returned no browser flow');
      const url = new URL(result.authUrl);
      requireValue(url.protocol === 'https:' && url.hostname === 'auth.openai.com', 'CODEX_AUTH_ORIGIN', 'Managed login returned an unexpected origin');
      return { authenticated: false, login_id: result.loginId, auth_url: result.authUrl };
    },
    async cancelLogin(loginId) { await client.call('account/login/cancel', { loginId }); },
    async interrupt() {
      await commandBroker.interrupt();
      if (activeThread && activeTurn) await client.call('turn/interrupt', { threadId: activeThread, turnId: activeTurn });
    },
    async close() {
      if (closing) return closing;
      closed = true; options.toolBroker?.revoke();
      const operation = (async () => {
        let commandError;
        try { await commandBroker.close(); } catch (error) { commandError = error; }
        try { await client?.close(); }
        catch (error) { if (commandError) throw new AggregateError([commandError, error], 'Codex command and model clients failed during shutdown'); throw error; }
        if (commandError) throw commandError;
        if (options.toolBroker) {
          let timer; let outcome;
          try { outcome = await Promise.race([options.toolBroker.quiesce(), new Promise((_, reject) => {
            timer = setTimeout(() => reject(Object.assign(new Error('Workflow resource tool shutdown timed out'), { code: 'CODEX_BROKER_SHUTDOWN_TIMEOUT' })), 5000);
          })]); } finally { clearTimeout(timer); }
          requireValue(outcome.quiescent, 'CODEX_BROKER_STOP_UNCONFIRMED', 'Workspace tool did not confirm quiescence');
          if (outcome.error) throw Object.assign(new Error('Workspace tool failed during shutdown'), { code: 'CODEX_BROKER_SHUTDOWN_FAILURE', cause: outcome.error });
        }
        await record({ closed_at: new Date().toISOString() });
      })();
      closing = operation;
      try { return await operation; }
      finally { if (closing === operation) closing = null; }
    },
  };
  function openClient(overrides) {
    return clientFactory(binary, { home, cwd, overrides, env,
      onEvent: async event => {
        await onEvent(codexEventMetadata(event));
        if (event.method === 'item/agentMessage/delta' && options.onOutput) {
          const params = event.params;
          requireValue(params && activeThread && params.threadId === activeThread && typeof params.turnId === 'string'
            && (!activeTurn || params.turnId === activeTurn) && typeof params.delta === 'string' && params.delta.length <= 65536,
          'CODEX_OUTPUT_IDENTITY', 'Streaming output is outside this exact node thread/turn or exceeds its event bound');
          await options.onOutput({ delta: params.delta, thread_id: params.threadId, turn_id: params.turnId });
        }
      },
      async onToolCall(params) {
        requireValue(!closed && params.threadId === activeThread && !params.namespace,
          'CODEX_TOOL_DENIED', 'Dynamic tool call is outside this node execution envelope');
        if (options.authorize) await options.authorize();
        requireOpen();
        const result = commandBroker.handles(params.tool)
          ? await commandBroker.call(params.tool, params.arguments, params.callId)
          : await (async () => {
            requireValue(options.toolBroker, 'CODEX_TOOL_DENIED', 'No Workflow resource tool was authorized');
            return options.toolBroker.call(params.tool, params.arguments, params.callId);
          })();
        if (params.tool === 'read_allowed_skill') await onToolRead({ call_id: params.callId, path: params.arguments?.path });
        return result;
      },
    });
  }
  try {
    if (options.onProfilePrepared) await options.onProfilePrepared(structuredClone(profile));
    if (options.authorize) await options.authorize();
    requireOpen();
    client = openClient(apiKeyOverrides);
    if (options.onSessionOwned) await options.onSessionOwned(session);
    requireOpen();
    await client.call('initialize', { clientInfo: { name: 'codex_agents_workflow', version: '1.0.0' }, capabilities: { experimentalApi: true } });
    client.initialized();
    const authentication = await session.authentication();
    if (authenticationMode === 'host_chatgpt') requireValue(authentication.authenticated && authentication.type === 'chatgpt',
      'CODEX_AUTH_REQUIRED', 'Host ChatGPT selection requires an authenticated ChatGPT user profile');
    if (authenticationMode === 'managed_chatgpt' && authentication.authenticated) requireValue(authentication.type === 'chatgpt',
      'CODEX_AUTH_MODE', 'Managed ChatGPT selection cannot use another account type');
    if (authentication.authenticated) {
      if (authenticationMode === 'environment_api_key') await environmentKeyModel(client, model, effort, options.onModelCatalog);
      else await authenticatedModel(client, model, effort, options.onModelCatalog);
      catalogChecked = true;
    }
  } catch (error) {
    if (client) try { await session.close(); } catch (cleanupError) { throw new AggregateError([error, cleanupError], 'Codex session setup and shutdown failed'); }
    throw error;
  }
  async function executeTurn(text, { explicit_sources = [], output_schema, timeout_ms = 0 } = {}, continuation = false) {
    requireOpen();
    requireValue(!activeThread && turns < (options.maxTurns ?? 1), 'CODEX_SESSION_BUSY', 'Codex session exhausted its fresh turns for this node');
    requireValue(typeof text === 'string' && text.length > 0 && text.length <= 200000, 'CODEX_PROMPT_LIMIT', 'Node prompt must be bounded text');
    requireValue(Array.isArray(explicit_sources) && explicit_sources.length <= 64, 'CODEX_SKILL_INPUT', 'Explicit Skill input list is invalid');
    requireValue(!continuation || (continuationThread && explicit_sources.length === 0), 'CODEX_CONTINUATION', 'Correction needs the existing node thread and no new Skill inputs');
    const pins = continuation ? null : await pinnedSkills();
    const currentAuth = await session.authentication();
    requireValue(currentAuth.authenticated, 'CODEX_AUTH_REQUIRED', 'Normal Codex user profile is not authenticated');
    if (authenticationMode !== 'environment_api_key') requireValue(currentAuth.type === 'chatgpt', 'CODEX_AUTH_MODE', 'ChatGPT node selected another account type');
    if (!catalogChecked) {
      if (authenticationMode === 'environment_api_key') await environmentKeyModel(client, model, effort, options.onModelCatalog);
      else await authenticatedModel(client, model, effort, options.onModelCatalog);
      catalogChecked = true;
    }
    if(!toolCatalog){
      const metadata=await (options.modelMetadataReader??normalModelMetadata)({client,home,cwd,model});
      toolCatalog=await prepareDirectToolCatalog({metadata,model,directory:receiptHome});
      // Model metadata is loaded by the App Server process, not refreshed by
      // thread/start.config. Finish discovery before opening the execution client.
      await client.close();
      requireOpen();
      client=openClient([...apiKeyOverrides,`model_catalog_json=${JSON.stringify(toolCatalog.path)}`]);
      await client.call('initialize',{clientInfo:{name:'codex_agents_workflow',version:'1.0.0'},capabilities:{experimentalApi:true}});
      client.initialized();
      const routedAuth=await session.authentication();
      requireValue(routedAuth.authenticated && routedAuth.type===currentAuth.type,'CODEX_AUTH_MODE','Tool routing changed the authenticated account mode');
      if(authenticationMode==='environment_api_key')await environmentKeyModel(client,model,effort,options.onModelCatalog);
      else await authenticatedModel(client,model,effort,options.onModelCatalog);
      await record({tool_routing:'direct',tool_catalog_sha256:toolCatalog.sha256,source_model_metadata_sha256:toolCatalog.source_sha256});
    }
    if (options.authorize) await options.authorize();
    requireOpen();
    requireValue(['deny', 'allow'].includes(options.skillPolicy?.implicit) && Array.isArray(options.skillPolicy.ambient_allow)
      && Array.isArray(options.skillPolicy.shadowed_skill_paths), 'CODEX_SKILL_POLICY', 'Node Skill content policy is missing');
    const shadowed = new Set(options.skillPolicy.shadowed_skill_paths.map(skillPathKey));
    const ambient = new Set(options.skillPolicy.ambient_allow.map(skillPathKey));
    const explicit = new Set(explicit_sources.map(skillPathKey));
    const included = continuation ? new Set() : new Set([...ambient, ...explicit]);
    const skillInputs = [];
    for (const key of included) {
      requireValue(!shadowed.has(key) && pins.has(key), 'CODEX_SKILL_INPUT', 'Included Skill is not an unshadowed pinned node input');
      const pin = pins.get(key);
      skillInputs.push({ type: 'skill', name: pin.name, path: pin.path });
    }
    let skillConfig = [];
    if (!continuation) {
    const discovered = await client.call('skills/list', { cwds: [cwd], forceReload: true });
    requireValue(Array.isArray(discovered?.data) && discovered.data.length === 1
      && skillPathKey(discovered.data[0].cwd) === skillPathKey(cwd)
      && Array.isArray(discovered.data[0].skills) && discovered.data[0].skills.length <= 1000
      && Array.isArray(discovered.data[0].errors) && discovered.data[0].errors.length === 0,
    'CODEX_SKILL_INVENTORY', 'Normal Codex Skill inventory is incomplete');
    const seenSkills = new Set();
    skillConfig = discovered.data[0].skills.map(skill => {
      const key = skillPathKey(skill.path);
      requireValue(!seenSkills.has(key) && typeof skill.enabled === 'boolean' && typeof skill.name === 'string',
        'CODEX_SKILL_INVENTORY', 'Normal Codex Skill inventory contains invalid or duplicate entries');
      seenSkills.add(key);
      return { path: skill.path, enabled: skill.enabled && !shadowed.has(key)
        && options.skillPolicy.implicit === 'allow' && !included.has(key) };
    });
    await record({ skill_inventory_count: skillConfig.length, implicit_skill_count: skillConfig.filter(item => item.enabled).length });
    }
    turns++;
    const provider = authenticationMode === 'environment_api_key' ? apiKeyProvider : 'openai';
    const dynamicTools = [...(options.toolBroker?.tools() ?? []), ...commandBroker.tools()]
      .map(tool => options.dynamicToolFormat === 'tagged_function' ? { ...tool, type: 'function' } : tool);
    requireValue(new Set(dynamicTools.map(tool => tool.name)).size === dynamicTools.length,
      'CODEX_TOOL_DUPLICATE', 'Normal node dynamic tool names must be unique');
    const commandAuditStart = commandBroker.audit().length;
    const started = continuation ? null : await client.call('thread/start', { cwd, model, ...(provider ? { modelProvider: provider } : {}),
      allowProviderModelFallback: false, ephemeral: false,
      sandbox,
      config: { model_catalog_json:toolCatalog.path, tool_output_token_limit:64000, skills: { config: skillConfig } },
      dynamicTools });
    requireValue(continuation || started?.model === model && (!provider || started.modelProvider === provider) && typeof started.thread?.id === 'string',
      'CODEX_THREAD_UNCONTROLLED', 'Codex thread substituted its model/provider or returned no identity');
    requireValue(continuation || started.sandbox?.type === (access === 'read_only' ? 'readOnly' : 'workspaceWrite'),
      'CODEX_SANDBOX_UNCONTROLLED', 'Codex thread did not activate the exact authorized access mode');
    activeThread = continuation ? continuationThread : started.thread.id;
    if (!continuation) await record({ thread_id: activeThread, thread_ids: [...receipt.thread_ids, activeThread], status: 'thread_started' });
    const input = [{ type: 'text', text }, ...skillInputs], after = client.events.length;
    try {
      if (options.authorize) await options.authorize();
      requireOpen();
      const begun = await client.call('turn/start', { threadId: activeThread, effort, input,
        ...(output_schema ? { outputSchema: output_schema } : {}) });
      requireValue(typeof begun.turn?.id === 'string', 'CODEX_TURN_SCHEMA', 'Codex turn returned no identity');
      activeTurn = begun.turn.id;
      await record({ turn_id: activeTurn, turn_ids: [...receipt.turn_ids, activeTurn], status: 'turn_started' });
      const completed = await client.waitFor(event => event.method === 'turn/completed'
        && event.params?.threadId === activeThread && event.params?.turn?.id === activeTurn,
      { after, timeout: timeout_ms, activity: event => agentTurnActivity(event, activeThread, activeTurn) });
      const events = client.events.slice(after), usage = usageFrom(events, activeThread, activeTurn);
      requireValue(completed.params.turn.status === 'completed', 'CODEX_TURN_FAILED',
        `Codex turn ended with status ${completed.params.turn.status}: ${safeTurnDiagnostic(events, activeThread, activeTurn)}; usage=${canonicalJSON(usage)}`);
      const items = events.filter(event => event.method === 'item/completed' && event.params?.threadId === activeThread
        && event.params?.turnId === activeTurn).map(event => event.params.item);
      const messages = items.filter(item => item.type === 'agentMessage' && typeof item.text === 'string');
      const finals = messages.filter(item => item.phase === 'final_answer');
      const output = (finals.length ? finals : messages.filter(item => item.phase == null)).map(item => item.text).join('\n').trim();
      requireValue(output.length > 0, 'CODEX_OUTPUT_EMPTY', 'Codex node returned no result');
      const command_audit = items.filter(item => item.type === 'commandExecution').map(item => ({
        status: item.status ?? null, exit_code: Number.isInteger(item.exitCode) ? item.exitCode : null,
        cwd: scrubTurnDiagnostic(item.cwd, 1000), command: scrubTurnDiagnostic(item.command, 1000),
        output: scrubTurnDiagnostic(item.aggregatedOutput, 2000),
      })).concat(commandBroker.audit().slice(commandAuditStart).map(item => ({
        status: item.status, exit_code: item.exit_code,
        cwd: scrubTurnDiagnostic(item.cwd, 1000), command: scrubTurnDiagnostic(item.command, 1000),
        output: scrubTurnDiagnostic(item.output, 2000),
      })));
      await record({ status: 'completed' });
      continuationThread = activeThread;
      return { output, thread_id: activeThread, turn_id: activeTurn, usage, item_types: items.map(item => item.type), command_audit,
        audit: { session_mode: 'user_codex', executable_sha256: binaryHash, input_sha256: digest(canonicalJSON(input)),
          instruction_source_count: continuation ? null : Array.isArray(started.instructionSources) ? started.instructionSources.length : null } };
    } catch (error) {
      try { await record({ status: 'failed', error_code: typeof error?.code === 'string' ? error.code : 'CODEX_TURN_ERROR' }); }
      catch (receiptError) { error = new AggregateError([error, receiptError], 'Codex turn and receipt recording failed'); }
      try { await session.close(); } catch (cleanupError) { throw new AggregateError([error, cleanupError], 'Codex turn and shutdown failed'); }
      throw error;
    } finally { activeThread = null; activeTurn = null; }
  }
  session.turn = (text, turnOptions) => executeTurn(text, turnOptions, false);
  session.continueTurn = (text, turnOptions) => executeTurn(text, turnOptions, true);
  return session;
}

// Candidate session engine, not a qualification grant. The host must require an
// executor certificate before allowing production Strict dispatch through it.
export async function createStrictSession(options) {
  const { cwd, model, effort, allowedSkills = [], skillPolicy, env = process.env, onEvent = () => {}, onToolRead = () => {} } = options;
  const profile = await buildCodexProfile(options); const clientFactory = options.clientFactory ?? createCodexClient;
  const recordChild = options.recordProfileChildImpl ?? recordProfileChild;
  const cleanupProfile = options.cleanupCodexProfileImpl ?? cleanupCodexProfile;
  let client; let policy; let launch; let authAccountId = null; let activeThread = null; let activeTurn = null; let closed = false; let turns = 0; let closing; let profileCleaned = false; let ownershipTransferred = false;
  let ownershipPhase = Promise.resolve(); const clientClosures = new WeakMap();
  const requireOpen = () => {
    requireValue(!closed, 'CODEX_SESSION_CLOSED', 'Strict session execution was revoked');
    options.assertActive?.();
  };
  const closeClient = async target => {
    if (!target) return;
    let state = clientClosures.get(target);
    if (!state) { state = { closed: false, closing: null }; clientClosures.set(target, state); }
    if (state.closed) return;
    if (state.closing) return state.closing;
    const operation = (async () => { await target.close(); state.closed = true; })();
    state.closing = operation;
    try { return await operation; }
    finally { if (state.closing === operation) state.closing = null; }
  };
  const session = {
    profile,
    get client() { return client; },
    async interrupt() { if (activeThread && activeTurn) await client.call('turn/interrupt', { threadId: activeThread, turnId: activeTurn }); },
    async close() {
      if (profileCleaned) return;
      if (closing) return closing;
      closed = true; options.toolBroker?.revoke();
      const operation = (async () => {
        // A launch that already passed its preflight owns the client handoff.
        // Wait only for that ownership phase, then close the exact current
        // client instance.  No later launch is permitted once closed is set.
        await ownershipPhase.catch(() => {});
        await closeClient(client);
        let timer; let outcome;
        try {
          outcome = options.toolBroker ? await Promise.race([options.toolBroker.quiesce(), new Promise((_, reject) => {
            timer = setTimeout(() => reject(Object.assign(new Error('Workspace tool did not quiesce; retain profile'), { code: 'CODEX_BROKER_SHUTDOWN_TIMEOUT' })), 5000);
          })]) : null;
        } finally { clearTimeout(timer); }
        requireValue(outcome?.quiescent!==false,'CODEX_BROKER_STOP_UNCONFIRMED','Bound execution did not confirm quiescence; retain profile and execution ownership');
        await cleanupProfile(profile);
        profileCleaned = true;
        if (outcome?.error) throw Object.assign(new Error('Workspace tool failed during shutdown'), { code: 'CODEX_BROKER_SHUTDOWN_FAILURE', cause: outcome.error, profile_cleaned: true });
      })();
      closing = operation;
      try { return await operation; }
      finally { if (closing === operation) closing = null; }
    },
  };
  try {
    policy = await createSkillPolicy({ home: profile.home, cwd, skillPolicy, allowed: allowedSkills, hostExecutionOnly: options.hostExecutionOnly === true });
    // Trusted in-process lifecycle hook for the host ownership journal. This is
    // never a Workflow/MCP argument and is not serialized to an executor.
    if (options.onProfilePrepared) await options.onProfilePrepared(structuredClone(profile));
    launch = async function () {
    requireOpen();
    const phase = (async () => {
    await noSymlinks(options.binary);
    requireValue(digest(await readFile(options.binary)) === profile.binary_sha256, 'CODEX_BINARY_CHANGED', 'Codex executable changed before process launch');
    if (options.authorize) await options.authorize();
    requireOpen();
    const next = clientFactory(options.binary, { home: profile.home, cwd: profile.model_catalog_sha256 ? cwd : profile.home,
      overrides: profileOverrides(profile), env: isolatedEnvironment(env, profile.home),
      onAuthRefresh: options.hostAuth ? async params => {
        requireValue(!params?.previousAccountId || params.previousAccountId === authAccountId, 'HOST_AUTH_ACCOUNT_CHANGED', 'Node requested another account during refresh');
        return options.hostAuth.credentials({ force: true, previousAccountId: authAccountId });
      } : undefined,
      onEvent: async event => {
        await onEvent(codexEventMetadata(event));
        if (event.method === 'item/agentMessage/delta' && options.onOutput) {
          const params = event.params;
          requireValue(params && activeThread && params.threadId === activeThread && typeof params.turnId === 'string' && (!activeTurn || params.turnId === activeTurn) && typeof params.delta === 'string' && params.delta.length <= 65536,
            'CODEX_OUTPUT_IDENTITY', 'Streaming output is outside this exact node thread/turn or exceeds its event bound');
          await options.onOutput({ delta: params.delta, thread_id: params.threadId, turn_id: params.turnId });
        }
      },
      async onToolCall(params) {
        requireValue(!closed && params.threadId === activeThread && !params.namespace, 'CODEX_TOOL_DENIED', 'Tool call is outside this node execution envelope');
        if (params.tool === 'read_allowed_skill') {
          if (options.authorize) await options.authorize();
          requireOpen();
          const result = policy.read(params.arguments); await onToolRead({ call_id: params.callId, path: params.arguments.path }); return result;
        }
        requireValue(options.toolBroker, 'CODEX_TOOL_DENIED', 'No workspace/resource broker was authorized');
        return options.toolBroker.call(params.tool, params.arguments, params.callId);
      },
    });
    client = next; clientClosures.set(next, { closed: false, closing: null });
    if (!ownershipTransferred && options.onSessionOwned) { await options.onSessionOwned(session); ownershipTransferred = true; }
    requireOpen();
    await recordChild(profile, next.pid);
    return next;
    })();
    ownershipPhase = phase.then(() => undefined, () => undefined);
    const next = await phase;
    requireOpen();
    await next.call('initialize', { clientInfo: { name: 'codex_agents_workflow_strict', version: '0.1.0' }, capabilities: { experimentalApi: true } }); next.initialized();
    requireOpen();
    if (options.hostAuth) {
      const credentials = await options.hostAuth.credentials({ previousAccountId: authAccountId });
      authAccountId = credentials.chatgptAccountId;
      await next.call('account/login/start', { type: 'chatgptAuthTokens', ...credentials });
    }
    if (options.authorize) await options.authorize();
    requireOpen();
    return next;
    }
    await launch();
    await policy.apply(client);
    requireOpen();
  } catch (error) {
    const errors = [error]; if (client) try { await session.close(); } catch (e) { errors.push(e); }
    else try { await cleanupProfile(profile); } catch (e) { errors.push(e); }
    if (errors.length > 1) throw Object.assign(new AggregateError(errors, 'Strict session setup/cleanup failed'), { retained_at: profile.home });
    throw error;
  }
  Object.assign(session, {
    async authentication() {
      const result = await client.call('account/read', { refreshToken: false });
      requireValue(result && typeof result.requiresOpenaiAuth === 'boolean', 'CODEX_AUTH_SCHEMA', 'Unsupported account metadata response');
      return { authenticated: Boolean(result.account) || result.requiresOpenaiAuth === false, type: result.account?.type ?? null };
    },
    async login({ apiKeyEnv } = {}) {
      requireValue(!options.hostAuth, 'STRICT_LOGIN_MODE', 'Existing host authentication cannot start another login flow');
      requireValue(!options.endpoint, 'CODEX_AUTH_FLOW', 'Local qualification never requests credentials');
      if (apiKeyEnv !== undefined) {
        requireValue(/^[A-Z_][A-Z0-9_]{0,127}$/.test(apiKeyEnv) && env[apiKeyEnv], 'CODEX_CREDENTIAL_MISSING', 'Configured authentication environment variable is unavailable');
        await client.call('account/login/start', { type: 'apiKey', apiKey: env[apiKeyEnv] });
        return session.authentication();
      }
      const result = await client.call('account/login/start', { type: 'chatgpt' });
      requireValue(typeof result.authUrl === 'string' && typeof result.loginId === 'string', 'CODEX_AUTH_SCHEMA', 'Managed login returned no supported browser flow');
      const url = new URL(result.authUrl);
      requireValue(url.protocol === 'https:' && url.hostname === 'auth.openai.com', 'CODEX_AUTH_ORIGIN', 'Managed login returned an unexpected authentication origin');
      // The authenticated human console may display this transient URL; never
      // append it to the Run journal, diagnostics or worker tool results.
      return { authenticated: false, login_id: result.loginId, auth_url: result.authUrl };
    },
    async cancelLogin(loginId) { await client.call('account/login/cancel', { loginId }); },
    async turn(text, { explicit_sources = [], output_schema, timeout_ms = 0 } = {}) {
      requireValue(!activeThread && !closed && turns < (options.maxTurns ?? 1), 'CODEX_SESSION_BUSY', 'Strict profile exhausted its fresh turns for this node');
      requireValue(typeof text === 'string' && text.length > 0 && text.length <= 200000, 'CODEX_PROMPT_LIMIT', 'Node prompt must be bounded text');
      requireValue((await session.authentication()).authenticated, 'CODEX_AUTH_REQUIRED', 'Strict node is waiting for supported authentication');
      if (options.authorize) await options.authorize();
      requireOpen();
      if (!profile.model_catalog_sha256) {
        // Recreate the catalog-owning process with the now-authenticated owned
        // profile. Its anonymous startup cache must not survive this boundary.
        await closeClient(client); requireOpen(); await launch();
        const observed = await authenticatedModel(client, model, effort, options.onModelCatalog);
        await closeClient(client); requireOpen(); await pinObservedModel(profile, observed); requireOpen(); await launch();
        await policy.apply(client);
        requireValue((await session.authentication()).authenticated, 'CODEX_AUTH_REQUIRED', 'Authentication was not retained in the owned profile after catalog pinning');
      }
      await policy.verify(client);
      const skillInputs = policy.explicitInputs(explicit_sources);
      if (options.authorize) await options.authorize();
      requireOpen();
      turns++;
      const started = await client.call('thread/start', { cwd, model, ...(options.endpoint ? { modelProvider: 'qualification' } : {}), approvalPolicy: 'never', sandbox: 'read-only', ephemeral: false,
        environments: [], baseInstructions: STRICT_INSTRUCTIONS, dynamicTools: [...policy.tools(), ...(options.toolBroker?.tools() ?? [])],
      });
      requireValue(Array.isArray(started.instructionSources) && !started.instructionSources.length && started.model === model && typeof started.thread?.id === 'string', 'CODEX_THREAD_UNCONTROLLED', 'Fresh thread has unexpected instruction sources, model substitution or schema');
      activeThread = started.thread.id;
      try {
        await policy.verify(client);
        const input = [{ type: 'text', text }, ...skillInputs];
        const profileHash = digest(await readFile(join(profile.home, 'config.toml')));
        const after = client.events.length;
        if (options.authorize) await options.authorize();
        requireOpen();
        const begun = await client.call('turn/start', { threadId: activeThread, effort, input, ...(output_schema ? { outputSchema: output_schema } : {}) }); activeTurn = begun.turn.id;
        const completed = await client.waitFor(event => event.method === 'turn/completed' && event.params.threadId === activeThread && event.params.turn.id === activeTurn, {
          after, timeout: timeout_ms, activity: event => agentTurnActivity(event, activeThread, activeTurn),
        });
        const turnEvents=client.events.slice(after);
        const usage=usageFrom(turnEvents,activeThread,activeTurn);
        requireValue(completed.params.turn.status === 'completed', 'CODEX_TURN_FAILED', `Strict turn ended with status ${completed.params.turn.status}: ${safeTurnDiagnostic(turnEvents,activeThread,activeTurn)}; usage=${canonicalJSON(usage)}`);
        await policy.verify(client);
        requireValue(digest(await readFile(join(profile.home, 'config.toml'))) === profileHash && digest(await readFile(join(profile.home, 'models.json'))) === profile.model_catalog_sha256, 'CODEX_PROFILE_CHANGED', 'Strict profile policy/model metadata changed during execution');
        const items = client.events.slice(after).filter(event => event.method === 'item/completed' && event.params.threadId === activeThread).map(event => event.params.item);
        requireValue(items.every(item => ['userMessage', 'agentMessage', 'reasoning', 'dynamicToolCall', 'plan', 'contextCompaction'].includes(item.type)), 'CODEX_ITEM_UNCONTROLLED', `Strict turn used unqualified execution items: ${items.map(item => item.type).join(', ')}`);
        const output = items.filter(item => item.type === 'agentMessage').map(item => item.text).join('\n').trim();
        requireValue(output.length > 0, 'CODEX_OUTPUT_EMPTY', 'Strict node returned no result');
        return { output, thread_id: activeThread, turn_id: activeTurn, usage, item_types: items.map(item => item.type), audit: { ...policy.audit(), profile_hash: profileHash,
          executable_sha256: profile.binary_sha256, schema: 'codex-0.155.0-stdio-v2-experimental', skill_input_items: skillInputs.map(item => ({ name: item.name, path: item.path })), input_sha256: digest(canonicalJSON(input)) } };
      } catch (error) {
        // A failed/deadline turn must not keep executing after its lease fails.
        // Closing the owned subprocess is the definitive local stop boundary.
        try { await session.close(); } catch (cleanupError) { throw new AggregateError([error, cleanupError], 'Strict turn and shutdown failed; profile retained'); }
        throw error;
      } finally { activeThread = null; activeTurn = null; }
    },
  });
  return session;
}
