import {prepareInheritedToolCatalog} from './direct-tool-catalog.mjs';
import {createOwnedToolMcp,assertOwnedMcpNamespaceAvailable} from './owned-tool-mcp.mjs';
import {ownedCommandDeclarations} from './owned-command-declarations.mjs';
import {inheritedToolOutputBudget} from './tool-output-delivery.mjs';
import {prepareCodexWebResponseDefault} from './codex-web-response-default.mjs';
import { mkdtemp, readFile, mkdir, open, realpath } from 'node:fs/promises';
import { homedir } from 'node:os';
import { join, resolve, dirname } from 'node:path';
import { createCodexClient, isCodexRawNotification, scrubCodexRawNotification } from './codex-app-server-client.mjs';
import { createCodexCommandBroker } from './codex-command-broker.mjs';
import { cooperativeExecutionPolicy } from './main-execution-policy.mjs';
import { agentTurnActivity } from './agent-activity.mjs';
import { authenticatedModel } from './codex-model-catalog.mjs';
import { buildCodexProfile, cleanupCodexProfile, recordProfileChild, isolatedEnvironment, pinObservedModel, profileOverrides, STRICT_INSTRUCTIONS } from './codex-profile-builder.mjs';
import { createSkillPolicy } from './codex-skill-policy.mjs';
import { skillPathKey } from './codex-skill-policy.mjs';
import { canonicalJSON, digest, prepareResources } from '../workflow-revisions.mjs';
import { requireValue, noSymlinks } from '../workflow-paths.mjs';
import { ensureDirectory } from '../workflow-paths.mjs';
import { writeDurableJSON } from '../workflow-events.mjs';
import {createRunOwnedNormalHome,normalPrefixHome,qualifyNormalPrefixHome,sealNormalPrefix,normalPrefixReceipt,acquireNormalPrefix,closeNormalPrefixHome} from './run-owned-normal-prefix.mjs';
import {prepareSharedPrefixOutputTransport,decodeSharedPrefixOutputTransport,SHARED_PREFIX_OUTPUT_SCHEMA_SHA256} from './shared-prefix-output-transport.mjs';

const SOURCE_DISCOVERY=Symbol('authenticated-common-source-discovery'),SOURCE_HOME=Symbol('run-owned-normal-prefix-source'),SOURCE_EXECUTION_ACCESS=Symbol('run-owned-normal-prefix-execution-access'),SOURCE_COMMON_ONLY=Symbol('live-common-only-preparation'),sourceResults=new WeakMap();

// Normal Host dispatch must check this before paying for prefix setup. The
// trusted neutral interface-qualification API remains separate from admission.
export const CODEX_NORMAL_PREFIX_SETUP_SCHEMA=Object.freeze({type:'object',
  properties:Object.freeze({ready:Object.freeze({const:true})}),required:Object.freeze(['ready']),additionalProperties:false});
export const CODEX_NORMAL_PREFIX_USAGE_CAPABILITY=Object.freeze({complete_usage:false,
  reason:'fork_protocol_has_no_qualified_independent_response_usage_witness',
  responseTransport:Object.freeze({prepare:prepareSharedPrefixOutputTransport,api_schema_sha256:SHARED_PREFIX_OUTPUT_SCHEMA_SHA256,
    setup_schema:CODEX_NORMAL_PREFIX_SETUP_SCHEMA})});

async function closeOwnedClient(client,milliseconds=8000) {
  requireValue(Number.isSafeInteger(milliseconds)&&milliseconds>0&&milliseconds<=8000,'CODEX_SESSION_ARGUMENTS','Host client close bound is outside 1..8000ms');
  if(!client)return;
  let timer;
  try{await Promise.race([client.close({timeout:milliseconds}),new Promise((_,reject)=>{timer=setTimeout(()=>reject(Object.assign(new Error('Owned App Server close was not confirmed'),{code:'CODEX_SESSION_SHUTDOWN_TIMEOUT'})),milliseconds);})]);}
  finally{clearTimeout(timer);}
}

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

const TOKEN_FIELDS = [['inputTokens','input_tokens'],['cachedInputTokens','cached_input_tokens'],['cacheWriteInputTokens','cache_write_input_tokens'],['outputTokens','output_tokens'],['reasoningOutputTokens','reasoning_output_tokens']];

function lastUsageFrom(events, threadId, turnId) {
  const event = [...events].reverse().find(item => item.method === 'thread/tokenUsage/updated'
    && item.params?.threadId === threadId && (!turnId || !item.params?.turnId || item.params.turnId === turnId));
  const usage = event?.params?.tokenUsage?.last;
  if (!usage) return { available: false };
  const result = { available: true };
  for (const [source, target] of TOKEN_FIELDS) {
    if (Number.isSafeInteger(usage[source]) && usage[source] >= 0) result[target] = usage[source];
  }
  return result;
}

function validTotal(total) {
  return total && typeof total === 'object' && !Array.isArray(total)
    && TOKEN_FIELDS.every(([field]) => field === 'cacheWriteInputTokens' && total[field] === undefined
      || Number.isSafeInteger(total[field]) && total[field] >= 0);
}

function usageBaseline(events, threadId, fresh, previousTurnId) {
  // A thread/start we own is fresh. Continuations need the actual most recent
  // thread counter, including an invalid/missing counter rather than an older one.
  if (fresh) return Object.fromEntries(TOKEN_FIELDS.map(([field]) => [field, 0]));
  const prior = [...events].reverse().find(event => event.method === 'thread/tokenUsage/updated' && event.params?.threadId === threadId);
  if (prior?.params?.turnId && prior.params.turnId !== previousTurnId) return null;
  return validTotal(prior?.params?.tokenUsage?.total) ? structuredClone(prior.params.tokenUsage.total) : null;
}

function turnUsageFrom(events, threadId, turnId, baseline) {
  const updates = events.filter(event => event.method === 'thread/tokenUsage/updated' && event.params?.threadId === threadId);
  const unknown = unavailable_reason => ({ available: false, unavailable_reason });
  if (!baseline) return unknown('baseline_missing');
  if (!updates.length) return unknown('total_missing');
  let previous = baseline;
  for (const event of updates) {
    // Unlabelled notifications belong to the sole turn of this owned thread.
    // A labelled different turn makes the window ambiguous; never charge it here.
    if (event.params.turnId && event.params.turnId !== turnId) return unknown('turn_scope_conflict');
    const total = event.params.tokenUsage?.total;
    if (total === undefined || total === null) return unknown('total_missing');
    if (!validTotal(total)) return unknown('total_invalid');
    for (const [field] of TOKEN_FIELDS) {
      if (field === 'cacheWriteInputTokens' && total[field] === undefined && previous[field] === undefined) continue;
      if (field === 'cacheWriteInputTokens' && total[field] === undefined && previous === baseline && baseline[field] === 0) continue;
      if (previous[field] === undefined || total[field] === undefined) return unknown('total_fields_changed');
      if (total[field] < previous[field]) return unknown('total_decreased');
    }
    previous = total;
  }
  const usage = { available: true };
  for (const [source, target] of TOKEN_FIELDS) if (previous[source] !== undefined) {
    if (baseline[source] === undefined) return unknown('baseline_fields_missing');
    usage[target] = previous[source] - baseline[source];
  }
  // Reasoning is a component of outputTokens, not an additional output charge.
  return usage;
}

function turnUsageMetadata(events, threadId, turnId, baseline, usage) {
  const updates = events.filter(event => event.method === 'thread/tokenUsage/updated' && event.params?.threadId === threadId);
  const finalTotal = updates.at(-1)?.params?.tokenUsage?.total;
  const metadata = { method: 'workflow/turnUsage', thread_id: threadId, turn_id: turnId,
    usage_available: usage.available, usage_basis: 'thread_total_delta', usage_update_count: updates.length };
  if (!usage.available) metadata.usage_unavailable_reason = usage.unavailable_reason;
  for (const [source, target] of TOKEN_FIELDS) {
    if (Number.isSafeInteger(baseline?.[source]) && baseline[source] >= 0) metadata[`usage_baseline_${target}`] = baseline[source];
    if (Number.isSafeInteger(finalTotal?.[source]) && finalTotal[source] >= 0) metadata[`usage_total_${target}`] = finalTotal[source];
    if (Number.isSafeInteger(usage[target])) metadata[target] = usage[target];
  }
  return metadata;
}

// Fork hydration is deliberately omitted. Infer only the actual owned response
// window: Core appends each response's `last` to `total`; zero estimates and
// repeated rate-limit notifications are not additional responses. This chain
// alone cannot fence a missing leading or trailing response notification.
function forkTurnUsage(events, threadId, turnId) {
  const updates=events.filter(event=>event.method==='thread/tokenUsage/updated'&&event.params?.threadId===threadId);
  const evidence={basis:'first_owned_total_minus_last',update_count:updates.length,response_update_count:0,zero_update_count:0,duplicate_update_count:0};
  const unknown=reason=>({usage:{available:false,unavailable_reason:reason},evidence});
  let previous,previousLast,baseline;
  for(const event of updates){
    if(event.params.turnId!==turnId)return unknown('turn_scope_conflict');
    const {total,last}=event.params.tokenUsage??{};
    if(!validTotal(total)||!validTotal(last))return unknown('total_or_last_invalid');
    const fields=TOKEN_FIELDS.map(([field])=>field).filter(field=>total[field]!==undefined||last[field]!==undefined||previous?.[field]!==undefined);
    if(fields.some(field=>total[field]===undefined||last[field]===undefined
      ||previous&&previous[field]===undefined))return unknown('total_fields_changed');
    const zero=fields.every(field=>last[field]===0);
    if(previous&&fields.every(field=>total[field]===previous[field])){
      if(zero){evidence.zero_update_count++;previousLast=structuredClone(last);continue;}
      if(previousLast&&fields.every(field=>last[field]===previousLast[field])){evidence.duplicate_update_count++;continue;}
      return unknown('unchanged_total_conflicting_last');
    }
    if(zero){
      if(previous)return unknown('zero_update_changed_total');
      evidence.zero_update_count++;previous=structuredClone(total);previousLast=structuredClone(last);continue;
    }
    if(!baseline){
      baseline=Object.fromEntries(fields.map(field=>[field,total[field]-last[field]]));
      if(fields.some(field=>baseline[field]<0))return unknown('last_exceeds_total');
      if(previous&&fields.some(field=>baseline[field]!==previous[field]))return unknown('first_update_delta_conflict');
      evidence.baseline=structuredClone(baseline);evidence.first_owned_update={total:structuredClone(total),last:structuredClone(last)};
    }else if(fields.some(field=>total[field]-previous[field]!==last[field]))return unknown('response_delta_conflict');
    evidence.response_update_count++;previous=structuredClone(total);previousLast=structuredClone(last);
  }
  if(!baseline)return unknown('owned_response_usage_missing');
  evidence.final_total=structuredClone(previous);
  const usage={};
  for(const [field,target] of TOKEN_FIELDS)if(previous[field]!==undefined)usage[target]=previous[field]-baseline[field];
  evidence.observed_usage=usage;
  evidence.completeness={available:false,reason:'fork_protocol_has_no_independent_start_or_terminal_usage_witness'};
  return unknown('fork_response_completeness_unavailable');
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
  const item=['item/started','item/completed'].includes(event.method)?p.item:null;
  if(item){
    if(typeof item.id==='string')metadata.item_id=item.id;
    if(typeof item.status==='string')metadata.status=item.status;
    if(typeof item.tool==='string')metadata.tool_name=scrubTurnDiagnostic(item.tool,256);
    if(typeof item.server==='string'&&item.type==='mcpToolCall')metadata.tool_server=scrubTurnDiagnostic(item.server,256);
    if(typeof item.processId==='string'&&item.type==='commandExecution')metadata.process_id=item.processId;
    if(Number.isSafeInteger(item.durationMs)&&item.durationMs>=0)metadata.duration_ms=item.durationMs;
    if(Object.hasOwn(item,'arguments'))metadata.arguments_sha256=digest(canonicalJSON(item.arguments));
    else if(item.type==='webSearch')metadata.arguments_sha256=digest(canonicalJSON({
      ...(Object.hasOwn(item,'query')&&item.query!==undefined?{query:item.query}:{}),action:item.action??null}));
    else if(item.type==='commandExecution')metadata.arguments_sha256=digest(canonicalJSON({command:item.command,cwd:item.cwd}));
    if(item.type==='webSearch'){
      const action=item.action;
      if(['search','openPage','findInPage'].includes(action?.type))metadata.web_operation=action.type;
      if(action?.type==='search'){
        if(Array.isArray(action.queries)&&action.queries.every(value=>typeof value==='string'))metadata.web_terms_count=action.queries.length;
        else if(typeof action.query==='string')metadata.web_terms_count=1;
      }
    }
  }
  if(event.method==='item/tool/call'){
    if(typeof p.callId==='string')metadata.call_id=p.callId;
    if(typeof p.tool==='string')metadata.tool_name=scrubTurnDiagnostic(p.tool,256);
    if(Object.hasOwn(p,'arguments'))metadata.arguments_sha256=digest(canonicalJSON(p.arguments));
  }
  if (event.method === 'error') {
    const error = p.error ?? p;
    metadata.error_code = typeof error?.code === 'string' ? scrubTurnDiagnostic(error.code, 100) : null;
    metadata.diagnostic = safeTurnDiagnostic([event], metadata.thread_id, metadata.turn_id);
  }
  if (event.method === 'thread/tokenUsage/updated') {
    const usage=lastUsageFrom([event], metadata.thread_id, metadata.turn_id);
    metadata.usage_available=usage.available;
    for(const field of ['input_tokens','cached_input_tokens','cache_write_input_tokens','output_tokens','reasoning_output_tokens'])if(Number.isSafeInteger(usage[field]))metadata[field]=usage[field];
    for (const [source, target] of TOKEN_FIELDS) {
      const value = p.tokenUsage?.total?.[source];
      if (Number.isSafeInteger(value) && value >= 0) metadata[`total_${target}`] = value;
    }
  }
  return metadata;
}

async function normalModelMetadata({client,home,cwd,model,configuration}) {
  configuration??=await client.call('config/read',{cwd,includeLayers:false});
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
// access-derived sandbox, or the authenticated writable caller's existing
// unrestricted policy; App Server keeps the user's approval policy. The
// separate receipt records this attempt without becoming a CODEX_HOME or
// changing model capabilities or instructions. A per-session catalog snapshot
// preserves authenticated native tool routing, including ordinary commands.
// Workflow program/resource interfaces retain their separate qualified broker;
// native commands use the ordinary caller-derived Codex policy and lifecycle.
export async function createCodexSession(options) {
  if(options.prefix)requireValue(options.hostAuth&&options.authentication?.mode!=='environment_api_key',
    'CODEX_PREFIX_SOURCE','Private prefix children require the existing Host credential broker');
  const prefixLease=options.prefix?await acquireNormalPrefix(options.prefix):null;
  let transferred=false;
  try{return await createNormalSession(prefixLease?{...options,authentication:{mode:'host_chatgpt'},env:{...(options.env??process.env),CODEX_HOME:prefixLease.home,CODEX_SQLITE_HOME:prefixLease.sqlite_home}}:options,
    prefixLease,()=>{transferred=true;});}
  catch(error){if(!transferred)prefixLease?.release();throw error;}
}
async function createNormalSession(options,prefixLease,onLeaseTransferred){
  const { cwd, access, env = process.env, onEvent = () => {}, onToolRead = () => {} } = options;
  let {model,effort} = options;
  requireValue(['read_only', 'bounded_write'].includes(access), 'CODEX_ACCESS_MODE', 'Normal Codex node requires its exact Run access mode');
  requireValue(['tagged_function', 'untagged_function'].includes(options.dynamicToolFormat),
    'CODEX_CAPABILITY_UNSUPPORTED', 'Normal Codex session requires the selected executable dynamic-tool capability evidence');
  const executionAccess=options[SOURCE_EXECUTION_ACCESS]??access;
  let executionPolicy = cooperativeExecutionPolicy(executionAccess);
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
  requireValue(typeof cwd === 'string' && (typeof options.resolveModelSelection === 'function'
    ? model === undefined && effort === undefined : typeof model === 'string' && typeof effort === 'string'),
    'CODEX_SESSION_ARGUMENTS', 'Normal Codex session requires a workspace, model and effort');
  const binary = await realpath(options.binary);
  await noSymlinks(binary);
  requireValue(!options.expectedBinaryPath || binary === options.expectedBinaryPath, 'CODEX_BINARY_CHANGED', 'Selected Codex executable alias changed its verified target before process launch');
  const binaryHash = digest(await readFile(binary));
  requireValue(binaryHash === options.expectedBinaryHash, 'CODEX_BINARY_CHANGED', 'Codex executable changed before process launch');
  const home = resolve(env.CODEX_HOME || join(homedir(), '.codex'));
  const sourceHome=options[SOURCE_HOME],preparedDiscovery=options[SOURCE_DISCOVERY];
  const privateLibrary=Boolean(sourceHome||prefixLease);
  if(privateLibrary)requireValue(authenticationMode==='host_chatgpt'&&options.hostAuth,'CODEX_PREFIX_SOURCE','Private normal-library clients require the Host credential broker');
  if(sourceHome)requireValue(access==='read_only'&&authenticationMode==='host_chatgpt'&&options.hostAuth,
    'CODEX_PREFIX_SOURCE','Private setup requires read-only access and the Host credential broker');
  await ensureDirectory(options.parent);
  const receiptHome = await mkdtemp(join(options.parent, 'codex-attempt-'));
  const profile = { home, receipt_home: receiptHome, binary_sha256: binaryHash, user_owned_home: !privateLibrary };
  const receipt = { schema_version: 1, owner: options.owner ?? {}, model:model??null, effort:effort??null,
    executable_sha256: binaryHash, user_codex_home: home, user_owned_home:!privateLibrary,receipt_home:receiptHome,created_at: new Date().toISOString(),
    access, sandbox:executionPolicy.thread_sandbox, ephemeral: !sourceHome, thread_ids: [], turn_ids: [], status: 'preparing',
    ...(sourceHome?{prefix_source:true}:{}),...(options.prefix?{prefix_fork:true}:{} ) };
  let recordTail=Promise.resolve();
  const record = fields => {
    const write=async()=>{Object.assign(receipt,fields);await writeDurableJSON(join(receiptHome,'attempt.json'),receipt);};
    // Every failed write rejects its own caller. A later explicit write still
    // gets an attempt after the prior operation settles, including recovery.
    recordTail=recordTail.then(write,write);return recordTail;
  };
  await record({});
  const clientFactory = options.clientFactory ?? createCodexClient;
  let client, activeThread = null, activeTurn = null, continuationThread = null, closed = false, turns = 0, closing, catalogChecked = false, skillPins, toolCatalog,toolOutputBudget,ownedMcp,commandDeclarations;
  let shutdownTail,shutdownCausallyBlocked=false,closeConfirmed=false;
  let authAccountId=null,forkOwnedConfig,resolvedSelection,webResponseDefault;
  const shutdownObservations=new Map(),shutdownPending=new Set(),shutdownFailures=new Map();
  // Retain each admitted shutdown observation once. A timed-out wait cannot
  // cancel its durable write, replay it, or let a later phase overtake it.
  function shutdownObservation(key,action){
    if(!shutdownObservations.has(key)){
      shutdownPending.add(key);
      const original=(shutdownTail??Promise.resolve()).then(action,action);
      const tracked=original.then(value=>{shutdownPending.delete(key);return value;},error=>{
        shutdownPending.delete(key);shutdownFailures.set(key,{error,reported:false});throw error;
      });
      // Blocked shutdown waits retain these tasks. Their late failures remain
      // in shutdownFailures and on the exact promise for explicit recovery.
      tracked.catch(()=>{});
      shutdownObservations.set(key,tracked);shutdownTail=tracked;
    }
    return shutdownObservations.get(key);
  }
  const shutdownPendingError=()=>Object.assign(
    new Error('Owned session notification drain still blocks shutdown observations'),{code:'CODEX_SESSION_SHUTDOWN_PENDING',
      details:{observation_pending:shutdownPending.size>0,pending_phases:[...shutdownPending].slice(0,16)}});
  async function waitForShutdownDrain(promise,budget){
    let timer;
    try{return await Promise.race([promise,new Promise((_,reject)=>{timer=setTimeout(()=>reject(shutdownPendingError()),budget);})]);}
    finally{clearTimeout(timer);}
  }
  function awaitShutdownObservation(key,action){
    const task=shutdownObservation(key,action);
    // Only the introduced unresolved/failed drain permits bypassing a wait.
    // Healthy observers, receipt writes and broker cleanup keep their original
    // contracts, independent of the client-only shutdown timeout.
    if(shutdownCausallyBlocked)return Promise.reject(shutdownPendingError());
    return task;
  }
  function reportShutdownFailure(error){
    for(const receipt of shutdownFailures.values())if(receipt.error===error)receipt.reported=true;
    if(error instanceof AggregateError)for(const cause of error.errors)reportShutdownFailure(cause);
  }
  const rawObservation = options.prefix ? {supported:false,diagnostic:'thread/fork has no qualified raw-event opt-in'}
    :options.rawObservation ?? { supported: false, diagnostic: 'optional raw capability evidence unavailable' };
  let turnSubmitting = false;
  const pendingRaw = [];
  let rawTurn;
  const rawCount = (object, key) => {
    const next = (object[key] ?? 0) + 1;
    if (Number.isSafeInteger(next)) object[key] = next;
    else rawTurn.counterSaturated = true;
  };
  function observeToolShape(item, elapsed) {
    if (!['function_call', 'custom_tool_call', 'function_call_output', 'custom_tool_call_output'].includes(item.type)) return;
    if (!item.call_id) { rawCount(rawTurn, 'unattributedToolShapes'); return; }
    const output = item.type.endsWith('_output'), type = output ? item.type.slice(0, -7) : item.type;
    const key = `${type}\0${item.call_id}`;
    let shape = rawTurn.toolShapes.get(key);
    if (!shape) {
      if (rawTurn.toolShapes.size >= 128) { rawCount(rawTurn, 'unretainedToolShapes'); return; }
      shape = { call_id: item.call_id, type, name: null, name_source: null, name_conflict: false,
        call_seen: false, output_seen: false, input_bytes: null, output_bytes: null, output_kind: null,
        first_ms: elapsed, last_ms: elapsed };
      rawTurn.toolShapes.set(key, shape);
    }
    // Exact call/type correlation also deduplicates nullable item IDs. Missing
    // call identity never falls back to name, order, last item or another turn.
    if (output ? shape.output_seen : shape.call_seen) return;
    shape.last_ms = elapsed;
    if (item.name != null) {
      if (shape.name != null && shape.name !== item.name) { shape.name = null; shape.name_source = null; shape.name_conflict = true; }
      else if (!shape.name_conflict && (shape.name == null || !output)) { shape.name = item.name; shape.name_source = output ? 'output' : 'call'; }
    }
    if (output) { shape.output_seen = true; shape.output_bytes = item.output_bytes; shape.output_kind = item.output_kind; shape.output_observation = item.output_observation; }
    else { shape.call_seen = true; shape.input_bytes = item.input_bytes; shape.input_observation = item.input_observation; }
  }
  function toolShapeSummary() {
    const stats = { call_count: 0, output_count: 0, known_input_bytes: 0, known_output_bytes: 0,
      unknown_input_count: 0, unknown_output_count: 0 };
    const add = (key, value) => {
      if (Number.isSafeInteger(stats[key] + value)) stats[key] += value;
      else rawTurn.counterSaturated = true;
    };
    for (const shape of rawTurn.toolShapes.values()) {
      if (shape.call_seen) { stats.call_count++; if (shape.input_bytes == null) stats.unknown_input_count++; else add('known_input_bytes', shape.input_bytes); }
      if (shape.output_seen) { stats.output_count++; if (shape.output_bytes == null) stats.unknown_output_count++; else add('known_output_bytes', shape.output_bytes); }
    }
    return { ...stats, identity_limit: 128, identity_complete: rawTurn.unretainedToolShapes === 0,
      unattributed_notifications: rawTurn.unattributedToolShapes, unretained_notifications: rawTurn.unretainedToolShapes,
      byte_basis: 'input/string:utf8;content_items:json_utf8', observation_basis: 'whole_string_lexical_references;strict_tool_descriptor_array',
      inspection_limit_bytes: 65536, detail_complete: true, unreported_call_count: 0, calls: [] };
  }
  const ordinaryToolTypes = ['webSearch', 'mcpToolCall', 'commandExecution', 'dynamicToolCall'];
  function observeOrdinaryToolTime(event) {
    const p = event.params, type = p?.item?.type;
    if (rawObservation.supported !== true || !rawTurn || !activeTurn || !['item/started', 'item/completed'].includes(event.method)
      || p?.threadId !== activeThread || p?.turnId !== activeTurn || !ordinaryToolTypes.includes(type)) return;
    const elapsed = Number((process.hrtime.bigint() - rawTurn.began) / 1000000n);
    if (!Number.isSafeInteger(elapsed) || elapsed < 0) return;
    const timing = rawTurn.ordinaryTimes.get(type) ?? { first_ms: elapsed, last_ms: elapsed };
    timing.last_ms = elapsed; rawTurn.ordinaryTimes.set(type, timing);
  }
  function ordinaryToolSummary() {
    // Count the same exact completed notifications that produce item_types;
    // timing is known only for exact callbacks after turn acknowledgement.
    const events = client.events.slice(rawTurn.after).filter(event => event.method === 'item/completed'
      && event.params?.threadId === activeThread && event.params?.turnId === activeTurn);
    return ordinaryToolTypes.map(type => ({ type, completed_count: events.filter(event => event.params?.item?.type === type).length,
      ...(rawTurn.ordinaryTimes.get(type) ?? { first_ms: null, last_ms: null }) }));
  }
  async function retainRawSummary() {
    if (!activeTurn || !rawTurn || rawTurn.retained) return;
    // Mark before persistence: a failed observer must never replay callbacks.
    rawTurn.retained = true;
    const shapes = rawObservation.supported === true ? toolShapeSummary() : null;
    const summary = { supported: rawObservation.supported === true,
      ...(rawObservation.supported === true ? { item_type_counts: { ...rawTurn.counts },
        response_completion_count: rawTurn.responses.size,
        identity_census_complete: rawTurn.unretainedItems === 0 && rawTurn.unretainedResponses === 0,
        identity_limit: 4096, unretained_item_notifications: rawTurn.unretainedItems,
        unretained_response_notifications: rawTurn.unretainedResponses, counter_saturated: rawTurn.counterSaturated,
        unobserved_item_notifications: rawTurn.unobserved,
        unattributed_item_notifications: rawTurn.unattributed,
        first_observation_ms: rawTurn.first, last_observation_ms: rawTurn.last, tool_shapes: shapes,
        ordinary_tool_count_basis: 'exact_item_completed_notifications', ordinary_tool_time_basis: 'exact_post_ack_callbacks',
        ordinary_tools: ordinaryToolSummary() } : {}) };
    if (shapes) {
      for (const shape of rawTurn.toolShapes.values()) {
        shapes.calls.push({ ...shape });
        if (Buffer.byteLength(canonicalJSON(summary), 'utf8') > 4000) { shapes.calls.pop(); break; }
      }
      for (;;) {
        shapes.unreported_call_count = rawTurn.toolShapes.size - shapes.calls.length;
        shapes.detail_complete = shapes.unreported_call_count === 0;
        if (Buffer.byteLength(canonicalJSON(summary), 'utf8') <= 4000 || !shapes.calls.length) break;
        shapes.calls.pop();
      }
    }
    await record({ raw_observation_summary: { thread_id: activeThread, turn_id: activeTurn, ...summary } });
    await onEvent({ method: 'workflow/rawObservation', thread_id: activeThread, turn_id: activeTurn,
      status: 'turn_summary', diagnostic: canonicalJSON(summary) });
  }
  async function observeRaw(event) {
    if (rawObservation.supported !== true) return;
    const safe = scrubCodexRawNotification(event), p = safe.params;
    requireValue(activeThread && p.threadId === activeThread && (activeTurn || turnSubmitting),
      'CODEX_RAW_IDENTITY', 'Raw observation is outside the exact owned thread and active turn');
    if (!activeTurn) {
      requireValue(pendingRaw.length < 256, 'CODEX_RAW_PENDING_LIMIT', 'Raw observation before turn acknowledgement exceeded its bounded queue');
      pendingRaw.push(safe);
      return;
    }
    requireValue(p.turnId === activeTurn, 'CODEX_RAW_IDENTITY', 'Raw observation does not match the exact owned turn');
    const elapsed = Number((process.hrtime.bigint() - rawTurn.began) / 1000000n);
    requireValue(Number.isSafeInteger(elapsed) && elapsed >= 0, 'CODEX_RAW_TIME_LIMIT', 'Raw observation elapsed time exceeded its integer bound');
    rawTurn.first ??= elapsed; rawTurn.last = elapsed;
    if (safe.method === 'rawResponse/completed') {
      if (!rawTurn.responses.has(p.responseId)) {
        if (rawTurn.items.size + rawTurn.responses.size < 4096) rawTurn.responses.add(p.responseId);
        // Saturation makes exact counts a visible lower bound, never a new
        // model execution limit or an eviction that could double-count.
        else rawCount(rawTurn, 'unretainedResponses');
      }
      return;
    }
    if (p.item.type === 'other') rawCount(rawTurn, 'unobserved');
    else if (!p.item.id) rawCount(rawTurn, 'unattributed');
    else {
      const prior = rawTurn.items.get(p.item.id);
      requireValue(!prior || prior === p.item.type, 'CODEX_RAW_ITEM_CONFLICT', 'Raw item identity changed its observed type');
      if (prior) return;
      if (rawTurn.items.size + rawTurn.responses.size < 4096) {
        rawTurn.items.set(p.item.id, p.item.type);
        rawCount(rawTurn.counts, p.item.type);
      } else rawCount(rawTurn, 'unretainedItems');
    }
    observeToolShape(p.item, elapsed);
    if (safe.method === 'rawResponseItem/completed' && p.item.type === 'other') {
      await onEvent({ method: 'workflow/rawObservation', thread_id: activeThread, turn_id: activeTurn,
        status: 'unobserved_item', diagnostic: 'Unrecognized raw item content discarded' });
    } else if (safe.method === 'rawResponseItem/completed' && p.item.type === 'tool_search_call' && !p.item.id) {
      await onEvent({ method: 'workflow/rawObservation', thread_id: activeThread, turn_id: activeTurn,
        status: 'unattributed_item', diagnostic: 'Raw tool_search_call has no item identity; not counted' });
    } else if (safe.method === 'rawResponseItem/completed' && p.item.type === 'tool_search_call') {
      await onEvent({ method: 'workflow/toolSearch', thread_id: activeThread, turn_id: activeTurn,
        item_type: p.item.type, item_id: p.item.id, ...(p.item.call_id ? { call_id: p.item.call_id } : {}),
        ...(p.item.status ? { status: p.item.status } : {}), diagnostic: `execution=${p.item.execution}` });
    }
    // Per-response raw usage is deliberately never part of authoritative turn
    // counters. Those continue to use thread/tokenUsage/updated total deltas.
  }
  const makeCommandBroker = () => createCodexCommandBroker({ binary, home, cwd, access, env,
    getExecutionPolicy:()=>executionPolicy,
    spoolRoot: options.ownedCommandTemp?join(cwd,'.workflow-command-output',digest(receiptHome)):join(receiptHome, 'command-output'), getClient: () => client,
    allowedPaths: options.allowedPaths ?? [],
    ownedCommandTemp: options.ownedCommandTemp,
    recoverToolErrors:true,
    getOutputBudget:()=>toolOutputBudget,
    shutdownGraceMs:options.commandShutdownGraceMs,
    networkAccess: options.commandNetworkAccess ?? false,
    onOperation: async operation => {
      const safe=Object.fromEntries(['call_id','process_id','tool','args_sha256','phase','pending_process_ids','pending_preparations','forced','error_code','exit_code','output_bytes','duration_ms','runtime_temp']
        .filter(key=>Object.hasOwn(operation,key)).map(key=>[key,operation[key]]));
      if(typeof operation.diagnostic==='string')safe.diagnostic=scrubTurnDiagnostic(operation.diagnostic,1000);
      const observe=async()=>{
        if(operation.phase.startsWith('close_'))await record({command_shutdown:safe});
        await onEvent({method:'workflow/command',...safe});
      };
      if(closed)await awaitShutdownObservation('command-'+digest(canonicalJSON(safe)),observe);
      else await observe();
    } });
  let commandBroker=makeCommandBroker(), commandGeneration=1, commandSettled=false, commandSettlement=null, completedTurn=null;
  const settledCommandAudits=[],nativeCommandAudits=[],nativeCommandIds=new Set(),commandTurnIds=new Map();
  const commandTurnKey=(threadId,index)=>JSON.stringify([threadId,index]);
  const commandAudits=()=>nativeCommandAudits.concat(settledCommandAudits,commandSettled?[]:commandBroker.audit());
  function retainNativeCommands(items,threadId,turnId){
    for(const item of items.filter(item=>item?.type==='commandExecution')){
      const key=typeof item.id==='string'?threadId+'\0'+turnId+'\0'+item.id:null;
      if(key&&nativeCommandIds.has(key))continue;
      if(key)nativeCommandIds.add(key);
      nativeCommandAudits.push({
        thread_id:threadId,turn_id:turnId,
        ...(typeof item.id==='string'?{item_id:item.id}:{}),
        ...(typeof item.processId==='string'?{process_id:item.processId}:{}),
        ...(Number.isSafeInteger(item.durationMs)?{duration_ms:item.durationMs}:{}),
        status:item.status??null,exit_code:Number.isInteger(item.exitCode)?item.exitCode:null,
        cwd:scrubTurnDiagnostic(item.cwd,1000),command:scrubTurnDiagnostic(item.command,1000),
        output:scrubTurnDiagnostic(item.aggregatedOutput,2000),
      });
    }
  }
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
    commandAudit:()=>commandAudits().map(item=>({...item,
      ...(Number.isSafeInteger(item.turn_index)&&commandTurnIds.has(commandTurnKey(item.thread_id,item.turn_index))
        ?{turn_id:commandTurnIds.get(commandTurnKey(item.thread_id,item.turn_index))}:{}),
      cwd:scrubTurnDiagnostic(item.cwd,1000),command:scrubTurnDiagnostic(item.command,1000),output:scrubTurnDiagnostic(item.output,2000)})),
    commandAuditForTurn:(threadId,turnId)=>session.commandAudit().filter(item=>item.thread_id===threadId&&item.turn_id===turnId),
    profile,
    get client() { return client; },
    shutdownState:()=>({observation_pending:shutdownPending.size>0,pending_phases:[...shutdownPending].slice(0,16),
      failures:[...shutdownFailures].slice(0,16).map(([phase,receipt])=>({phase,code:receipt.error?.code??'CODEX_SHUTDOWN_FAILED',reported:receipt.reported})),close_confirmed:closeConfirmed}),
    async prepareHostCompletion() {
      requireOpen();
      requireValue(!activeThread&&!activeTurn&&!turnSubmitting&&continuationThread&&completedTurn,
        'CODEX_HOST_COMPLETION_BOUNDARY','Host completion requires the terminal result of this exact session turn');
      if(commandSettlement)return commandSettlement;
      if(commandSettled)return;
      // Close only the command transport. The model thread stays alive for a
      // checker-driven correction; no workspace cleanup may follow its snapshot.
      commandSettlement=(async()=>{
        if(options.authorize)await options.authorize();
        requireOpen();
        await commandBroker.close();
        requireOpen();
        await record({command_completion_boundary:{phase:'settled',generation:commandGeneration,
          thread_id:continuationThread,turn_id:completedTurn}});
        requireOpen();
        settledCommandAudits.push(...commandBroker.audit());
        commandSettled=true;
      })();
      // A failed boundary remains poisoned. Retrying must not turn an earlier
      // cleanup/receipt failure into a successful acceptance or a new transport.
      await commandSettlement;
      commandSettlement=null;
    },
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
      const unreported=[...shutdownFailures.values()].filter(receipt=>!receipt.reported);
      if(unreported.length){
        const failures=[...new Set(unreported.map(receipt=>receipt.error))];
        unreported.forEach(receipt=>receipt.reported=true);
        if(failures.length===1)throw failures[0];
        throw new AggregateError(failures,'Deferred shutdown observations failed after the previous close returned');
      }
      if(closeConfirmed)return;
      const budget=options.clientShutdownTimeoutMs??8000;
      requireValue(Number.isSafeInteger(budget)&&budget>0&&budget<=8000,'CODEX_SESSION_ARGUMENTS','Host client close bound is outside 1..8000ms');
      // An explicit retry may start fresh shutdown diagnostics after every
      // prior admitted observer settled. Pending work retains its exact task.
      if(!shutdownPending.size){shutdownObservations.clear();shutdownTail=undefined;}
      shutdownCausallyBlocked=false;
      closed = true;
      const operation = (async () => {
        const errors=[];
        const attempt=async action=>{try{await action();}catch(error){reportShutdownFailure(error);errors.push(error);}};
        const observe=async(key,action)=>attempt(()=>awaitShutdownObservation(key,action));
        ownedMcp?.revoke();
        await attempt(()=>options.toolBroker?.revoke());
        await attempt(async()=>{
          try{await waitForShutdownDrain(shutdownObservation('drain',()=>client?.flushEvents?.()),budget);}
          catch(error){shutdownCausallyBlocked=true;throw error;}
        });
        await observe('begin_receipt',()=>record({close_phase:'begin',close_started_at:new Date().toISOString(),pending_command_ids:commandBroker.pending()}));
        await observe('begin_event',()=>onEvent({method:'workflow/sessionShutdown',phase:'begin',pending_process_ids:commandBroker.pending(),
          ...(client?.notificationStats ? {notification_delivery:client.notificationStats()} : {})}));
        await attempt(()=>commandBroker.close());
        await observe('model_receipt',()=>record({close_phase:'model_client'}));
        await observe('model_event',()=>onEvent({method:'workflow/sessionShutdown',phase:'model_client'}));
        await attempt(()=>closeOwnedClient(client,options.clientShutdownTimeoutMs));
        if (options.toolBroker) await attempt(async()=>{
          let timer; let outcome;
          try { outcome = await Promise.race([options.toolBroker.quiesce(), new Promise((_, reject) => {
            timer = setTimeout(() => reject(Object.assign(new Error('Workflow resource tool shutdown timed out'), { code: 'CODEX_BROKER_SHUTDOWN_TIMEOUT' })), 5000);
          })]); } finally { clearTimeout(timer); }
          requireValue(outcome.quiescent, 'CODEX_BROKER_STOP_UNCONFIRMED', 'Workspace tool did not confirm quiescence');
          if (outcome.error) throw Object.assign(new Error('Workspace tool failed during shutdown'), { code: 'CODEX_BROKER_SHUTDOWN_FAILURE', cause: outcome.error });
        });
        if(ownedMcp)await attempt(()=>ownedMcp.close());
        if(!errors.length){
          await observe('closed_receipt',()=>record({ close_phase:'closed', closed_at: new Date().toISOString() }));
          await observe('closed_event',()=>onEvent({method:'workflow/sessionShutdown',phase:'closed'}));
        }
        if(errors.length){
          const code=errors[0].code??'CODEX_SHUTDOWN_FAILED';
          await observe('failed_receipt',()=>record({close_phase:'failed',close_error_code:code,close_error_codes:errors.map(error=>error.code??'CODEX_SHUTDOWN_FAILED')}));
          await observe('failed_event',()=>onEvent({method:'workflow/sessionShutdown',phase:'failed',error_code:code}));
          if(errors.length===1)throw errors[0];
          throw new AggregateError(errors,'Owned cleanup and shutdown observations failed');
        }
        closeConfirmed=true;
        prefixLease?.release();prefixLease=null;
      })();
      closing = operation;
      try { return await operation; }
      finally { if (closing === operation) closing = null; }
    },
  };
  onLeaseTransferred();
  async function executeOwnedTool(params){
    requireValue(!options[SOURCE_COMMON_ONLY],'CODEX_BATCH_SOURCE_TOOLS','Common-only preparation cannot execute tools');
    requireValue(!closed&&activeThread&&params.threadId===activeThread&&!params.namespace,
      'CODEX_TOOL_DENIED','Tool call is outside this node execution envelope');
    if(params.context)requireValue(params.context.thread_id===activeThread&&params.context.session_id===activeThread
      &&params.context.turn_id===activeTurn&&params.context.call_id===params.callId,
      'CODEX_TOOL_DENIED','Owned MCP context differs from this exact source thread, turn or call');
    await client.flushEvents?.();
    if(options.authorize)await options.authorize();requireOpen();
    await onEvent(codexEventMetadata({method:'item/tool/call',params}));
    const result=commandBroker.handles(params.tool)?await commandBroker.call(params.tool,params.arguments,params.callId,
      {thread_id:activeThread,turn_index:turns}):await (async()=>{
      requireValue(options.toolBroker,'CODEX_TOOL_DENIED','No Workflow resource tool was authorized');
      return options.toolBroker.call(params.tool,params.arguments,params.callId);
    })();
    if(params.tool==='read_allowed_skill')await onToolRead({call_id:params.callId,path:params.arguments?.path});
    return result;
  }
  function openClient(overrides) {
    return clientFactory(binary, { home, cwd, overrides, env:{...env,...webResponseDefault?.environment_overlay}, rawObservation,
      ...(privateLibrary?{onAuthRefresh:async params=>{
        requireValue(!params?.previousAccountId||params.previousAccountId===authAccountId,'HOST_AUTH_ACCOUNT_CHANGED','Private source refresh requested another account');
        return options.hostAuth.credentials({force:true,previousAccountId:authAccountId});
      }}:{}),
      ...(options.onObservationBatch ? {onEventBatch: async events => {
        for(const event of events)await options.sharedEventObserver?.(event);
        const metadata=events.map(event=>{observeOrdinaryToolTime(event);return codexEventMetadata(event);});
        await options.onObservationBatch(metadata);
      }} : {}),
      onEvent: async event => {
        await options.sharedEventObserver?.(event);
        // Shared children have their own identity/metering observer. Their raw
        // notifications must not enter the source turn's observation state.
        if(options.sharedEventObserver&&event.params?.threadId&&event.params.threadId!==(activeThread??continuationThread)){
          if(!isCodexRawNotification(event))await onEvent(codexEventMetadata(event));
          return;
        }
        if (isCodexRawNotification(event)) { await observeRaw(event); return; }
        observeOrdinaryToolTime(event);
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
        requireValue(!ownedMcp,'CODEX_TOOL_DENIED','Unexpected dynamic callback in an owned MCP session');
        return executeOwnedTool(params);
      },
    });
  }
  async function initializeClient(){
    await client.call('initialize', { clientInfo: { name: 'codex_agents_workflow', version: '1.0.0' }, capabilities: { experimentalApi: true } });
    client.initialized();
    if(privateLibrary){
      const credentials=await options.hostAuth.credentials({previousAccountId:authAccountId});
      requireValue(typeof credentials.chatgptAccountId==='string'&&credentials.chatgptAccountId.length>0,'HOST_AUTH_SCHEMA','Private source needs exact authenticated account');
      requireValue(!authAccountId||authAccountId===credentials.chatgptAccountId,'HOST_AUTH_ACCOUNT_CHANGED','Private source account changed');
      authAccountId=credentials.chatgptAccountId;
      await client.call('account/login/start',{type:'chatgptAuthTokens',...credentials});
    }
  }
  try {
    if (options.onProfilePrepared) await options.onProfilePrepared(structuredClone(profile));
    if (options.authorize) await options.authorize();
    requireOpen();
    if(preparedDiscovery){
      requireValue(sourceHome&&options[SOURCE_COMMON_ONLY]&&preparedDiscovery.selection&&preparedDiscovery.authentication?.type==='chatgpt',
        'CODEX_PREFIX_SOURCE','Prepared discovery belongs only to an authenticated common-only source');
      ({model,effort}=preparedDiscovery.selection);resolvedSelection=structuredClone(preparedDiscovery.selection);
      executionPolicy=cooperativeExecutionPolicy(executionAccess,resolvedSelection.main_execution_context);
      authAccountId=preparedDiscovery.account_id;
      await record({model,effort,sandbox:executionPolicy.thread_sandbox,execution_policy:executionPolicy});
      if(options.onSessionOwned)await options.onSessionOwned(session);requireOpen();
      await prepareToolRouting(preparedDiscovery.configuration,preparedDiscovery.metadata,preparedDiscovery.authentication);
    }else{
    client = openClient(apiKeyOverrides);
    if (options.onSessionOwned) await options.onSessionOwned(session);
    requireOpen();
    await initializeClient();
    if(sourceHome)await qualifyNormalPrefixHome(sourceHome,await client.call('config/read',{cwd,includeLayers:false}));
    const authentication = await session.authentication();
    if (authenticationMode === 'host_chatgpt') requireValue(authentication.authenticated && authentication.type === 'chatgpt',
      'CODEX_AUTH_REQUIRED', 'Host ChatGPT selection requires an authenticated ChatGPT user profile');
    if (authenticationMode === 'managed_chatgpt' && authentication.authenticated) requireValue(authentication.type === 'chatgpt',
      'CODEX_AUTH_MODE', 'Managed ChatGPT selection cannot use another account type');
    if (options.resolveModelSelection||prefixLease) {
      const selection = prefixLease?structuredClone(prefixLease.selection):await options.resolveModelSelection(client);
      requireOpen();
      if (options.assertActive) options.assertActive();
      requireValue(typeof selection?.model === 'string' && selection.model.length > 0
        && typeof selection?.effort === 'string' && selection.effort.length > 0,
        'CODEX_SESSION_ARGUMENTS', 'The owned discovery client did not resolve Main model and effort');
      ({model,effort}=selection);
      resolvedSelection=structuredClone(selection);
      executionPolicy=cooperativeExecutionPolicy(executionAccess,selection.main_execution_context);
      await record({model,effort,sandbox:executionPolicy.thread_sandbox,execution_policy:executionPolicy});
    }
    if (authentication.authenticated) {
      if (authenticationMode === 'environment_api_key') await environmentKeyModel(client, model, effort, options.onModelCatalog);
      else await authenticatedModel(client, model, effort, options.onModelCatalog);
      catalogChecked = true;
    }
    }
  } catch (error) {
    if (client||prefixLease) try { await session.close(); } catch (cleanupError) { throw Object.assign(new AggregateError([error, cleanupError], 'Codex session setup and shutdown failed'),{prefix_child:session}); }
    throw error;
  }
  async function prepareToolRouting(discoveryConfiguration,metadata,currentAuth){
    try{
      discoveryConfiguration??=await client.call('config/read',{cwd,includeLayers:false});
      metadata??=await (options.modelMetadataReader??normalModelMetadata)({client,home,cwd,model,configuration:discoveryConfiguration});
      toolCatalog=await prepareInheritedToolCatalog({metadata,model,directory:receiptHome});
      if(toolCatalog.interface.javascript_aggregation===true){
        assertOwnedMcpNamespaceAvailable(discoveryConfiguration?.config);
        requireOpen();
        ownedMcp=await createOwnedToolMcp({tools:[...(options.toolBroker?.tools()??[]),...commandBroker.tools()],
          configuration:discoveryConfiguration.config,
          call:params=>{
            if(params.context&&params.context.thread_id!==(activeThread??continuationThread)){
              requireValue(typeof options.sharedToolRouter==='function','CODEX_TOOL_DENIED','No admitted shared child owns this MCP context');
              return options.sharedToolRouter(params);
            }
            return executeOwnedTool({...params,threadId:params.context?.thread_id??activeThread,turnId:params.context?.turn_id??activeTurn});
          }});
      }
      // Model metadata is loaded by the App Server process, not refreshed by
      // thread/start.config. Finish discovery before opening the execution client.
      if(client)await client.close();
      requireOpen();
      const executionOverrides=[...apiKeyOverrides,`model_catalog_json=${JSON.stringify(toolCatalog.path)}`,...toolCatalog.execution_overrides,
        ...(ownedMcp?['features.code_mode_host=true',...ownedMcp.overrides]:[])];
      if(toolCatalog.interface.standalone_web_search){
        webResponseDefault=await prepareCodexWebResponseDefault({binary,home,cwd,auditPath:join(receiptHome,'web-queries.jsonl'),
          clientFactory,clientOptions:{env},overrides:executionOverrides});
      }
      client=openClient(webResponseDefault?.overrides??executionOverrides);
      await initializeClient();
      const routedAuth=await session.authentication();
      requireValue(routedAuth.authenticated && routedAuth.type===currentAuth.type,'CODEX_AUTH_MODE','Tool routing changed the authenticated account mode');
      // Qualify the actual execution client's effective configuration. Reading
      // the earlier discovery process permits a changed user limit to truncate
      // a result whose last local chunk was already consumed and deleted.
      const executionConfiguration=await client.call('config/read',{cwd,includeLayers:false});
      if(toolCatalog.interface.standalone_web_search){
        requireValue(executionConfiguration?.config?.features?.standalone_web_search===true,
          'CODEX_STANDALONE_WEB_SEARCH_CONFIG','Execution client did not activate metadata-derived standalone web search');
        toolCatalog.interface.standalone_web_search.effective_enabled=true;
        const inventory=await client.call('hooks/list',{cwds:[cwd]});
        const own=inventory?.data?.find(item=>resolve(item.cwd)===resolve(cwd))?.hooks?.find(item=>item.key===webResponseDefault.own_hook.key);
        requireValue(own?.enabled===true&&own.trustStatus==='trusted'&&own.currentHash===webResponseDefault.own_hook.current_hash,
          'CODEX_WEB_RESPONSE_DEFAULT','Execution client did not trust the prepared web response default');
        toolCatalog.interface.standalone_web_search.response_default={response_length:'short',scope:['search_query','open','find'],
          explicit_values:'preserved',mixed_operations:'preserved',audit_path:webResponseDefault.audit_path,
          normal_hook_count:webResponseDefault.normal_hooks_preserved.length};
        const {overrides:unusedOverrides,environment_overlay:unusedEnvironment,configuration_overlay:unusedConfiguration,...webDefaultProof}=webResponseDefault;
        await record({web_response_default:{...webDefaultProof,qualification:'actual_execution_client_trusted'}});
      }
      const ownedBinding=ownedMcp?.qualifyConfiguration(executionConfiguration?.config);
      if(preparedDiscovery){
        requireValue(ownedMcp,'CODEX_BATCH_TOOL_SURFACE','Common source requires the qualified ordinary owned MCP route');
        await qualifyNormalPrefixHome(sourceHome,executionConfiguration,{overlay:{
          model_catalog_json:toolCatalog.path,features:{...ownedMcp.configuration_overlay.features,code_mode_host:true,
            ...(toolCatalog.interface.standalone_web_search?{standalone_web_search:true}:{}),...webResponseDefault?.configuration_overlay.features},
          mcp_servers:ownedMcp.configuration_overlay.mcp_servers,
          ...(webResponseDefault?{hooks:webResponseDefault.configuration_overlay.hooks}:{})}});
      }
      // config/read includes nullable optional defaults. JSON null is not an
      // absent TOML override; carry the qualified binding's actual values only.
      if(ownedMcp)forkOwnedConfig={features:{code_mode_host:true,code_mode:structuredClone(executionConfiguration.config.features.code_mode),
        ...(toolCatalog.interface.standalone_web_search?{standalone_web_search:executionConfiguration.config.features.standalone_web_search}:{})},mcp_servers:{[ownedMcp.namespace]:
        structuredClone(Object.fromEntries(Object.entries(executionConfiguration.config.mcp_servers[ownedMcp.namespace]).filter(([,value])=>value!==null)))}};
      // A native command interface needs no Host-written command declarations
      // in the shared prompt. Keep the legacy broker-only prefix contract for
      // metadata that explicitly disables or omits a native shell.
      if(ownedMcp&&toolCatalog.interface.native_shell.execution==='disabled')
        commandDeclarations=ownedCommandDeclarations(ownedMcp.namespace,commandBroker.tools());
      const toolConfiguration=options.toolOutputConfigurationReader
        ?await options.toolOutputConfigurationReader():executionConfiguration?.config;
      requireValue(toolConfiguration&&typeof toolConfiguration==='object'&&!Array.isArray(toolConfiguration),
        'CODEX_TOOL_OUTPUT_BUDGET','Effective tool-output configuration is unavailable');
      toolOutputBudget=inheritedToolOutputBudget(metadata,toolConfiguration);
      if(authenticationMode==='environment_api_key')await environmentKeyModel(client,model,effort,options.onModelCatalog);
      else await authenticatedModel(client,model,effort,options.onModelCatalog);
      catalogChecked=true;
      await record({tool_routing:toolCatalog.interface.execution_tool_mode,tool_catalog_sha256:toolCatalog.sha256,source_model_metadata_sha256:toolCatalog.source_sha256,
        tool_interface:{...toolCatalog.interface,broker_transport:ownedMcp?'native_mcp':'dynamic_tools',
          ...(ownedMcp?{...ownedBinding,native_parallel_tools:true,native_code_mode_host:true}:{})},tool_output_delivery:toolOutputBudget});
      // The ephemeral profile is removed after execution. Retain its qualified
      // interface in the owning Run, without instructions or endpoint authority.
      await onEvent({method:'workflow/toolInterface',diagnostic:canonicalJSON({
        ...toolCatalog.interface,broker_transport:ownedMcp?'native_mcp':'dynamic_tools',
        tool_catalog_sha256:toolCatalog.sha256,source_model_metadata_sha256:toolCatalog.source_sha256,
        output_delivery:toolOutputBudget,
        ...(ownedBinding??{}),
        native_code_mode_host:Boolean(ownedMcp),native_parallel_tools:Boolean(ownedMcp),
      })});
      await record({ raw_observation: { supported: rawObservation.supported === true,
        diagnostic: scrubTurnDiagnostic(rawObservation.diagnostic, 256) } });
      await onEvent({ method: 'workflow/rawObservation', status: rawObservation.supported === true ? 'supported' : 'unsupported',
        diagnostic: scrubTurnDiagnostic(rawObservation.diagnostic, 256) });
      }catch(error){
        const errors=[error];
        try{await record({status:'failed',error_code:typeof error?.code==='string'?error.code:'CODEX_TOOL_ROUTING_ERROR'});}catch(receiptError){errors.push(receiptError);}
        try{await session.close();}catch(cleanupError){errors.push(cleanupError);}
        if(errors.length>1)throw new AggregateError(errors,'Codex tool routing preparation and shutdown failed');
        throw error;
      }
    }
  async function executeTurn(text, { explicit_sources = [], output_schema, timeout_ms = 0 } = {}, continuation = false) {
    requireOpen();
    requireValue(!activeThread && turns < (options.maxTurns ?? 1), 'CODEX_SESSION_BUSY', 'Codex session exhausted its fresh turns for this node');
    requireValue(!options.prefix||continuation||turns===0,'CODEX_PREFIX_FORK_REUSED','A prefix child must continue its exact fork rather than start another fork');
    requireValue(typeof text === 'string' && text.length > 0 && text.length <= 200000, 'CODEX_PROMPT_LIMIT', 'Node prompt must be bounded text');
    requireValue(Array.isArray(explicit_sources) && explicit_sources.length <= 64, 'CODEX_SKILL_INPUT', 'Explicit Skill input list is invalid');
    requireValue(!continuation || (continuationThread && explicit_sources.length === 0), 'CODEX_CONTINUATION', 'Correction needs the existing node thread and no new Skill inputs');
    requireValue(!commandSettlement,'CODEX_HOST_COMPLETION_BOUNDARY','Command settlement is pending or failed');
    completedTurn=null; // A new turn invalidates the preceding terminal boundary before any asynchronous preparation.
    if(commandSettled){
      requireValue(continuation,'CODEX_HOST_COMPLETION_BOUNDARY','A settled command generation requires the same-thread correction');
      if(options.authorize)await options.authorize();
      requireOpen();
      commandBroker=makeCommandBroker();commandGeneration++;commandSettled=false;
      requireOpen();
    }
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
      await prepareToolRouting(undefined,undefined,currentAuth);
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
    requireValue(!sourceHome||ownedMcp,'CODEX_PREFIX_TOOL_MODE','Stored setup requires rebindable code-mode MCP tools');
    const startArguments={ cwd, model, ...(provider ? { modelProvider: provider } : {}),
      // Node sessions live only in this owned process; explicit persistent
      // Workflow thread executors use the separate Codex task handoff.
      allowProviderModelFallback: false, ephemeral: !sourceHome,
      ...(sourceHome&&options.sharedEventObserver?{historyMode:'legacy'}:{}),
      ...(rawObservation.supported === true ? { experimentalRawEvents: true } : {}),
      sandbox:executionPolicy.thread_sandbox,
      config: { model_catalog_json:toolCatalog.path, skills: { config: skillConfig } },
      dynamicTools:ownedMcp?[]:dynamicTools };
    let started=null;
    if(!continuation){
      if(options.prefix){
        requireValue(ownedMcp,'CODEX_PREFIX_TOOL_MODE','Fork requires independently rebound code-mode MCP tools; dynamic-tool replacement is unsupported');
        await prefixLease.verify(model,effort);
        requireValue(commandDeclarations?.audit.sha256===prefixLease.command_declarations_sha256,
          'CODEX_PREFIX_DECLARATIONS_CHANGED','Worker command declarations differ from its exact completed prefix');
        const {dynamicTools:unusedTools,allowProviderModelFallback:unusedFallback,experimentalRawEvents:unusedRaw,...forkArguments}=startArguments;
        started=await client.call('thread/fork',{...forkArguments,config:{...forkArguments.config,...forkOwnedConfig},ephemeral:true,path:prefixLease.source_path,
          threadId:prefixLease.source_thread_id,lastTurnId:prefixLease.last_turn_id,cwd,runtimeWorkspaceRoots:[cwd],excludeTurns:true});
        requireValue(started?.cwd===cwd&&canonicalJSON(started.runtimeWorkspaceRoots)===canonicalJSON([cwd])
          &&started.thread?.ephemeral===true&&started.thread?.forkedFromId===prefixLease.source_thread_id,
          'CODEX_PREFIX_FORK_UNCONTROLLED','Fork did not retain exact source identity and independent ephemeral workspace');
        await record({prefix_fork:{source_thread_id:prefixLease.source_thread_id,last_turn_id:prefixLease.last_turn_id,
          source_path:prefixLease.source_path,rollout_sha256:prefixLease.rollout_sha256,rollout_bytes:prefixLease.rollout_bytes,
          forked_from_id:started.thread.forkedFromId,exclude_turns:true,usage_baseline_basis:'first_owned_total_minus_last',
          raw_observation_supported:false,backing_store:'run_owned_temporary_normal_library',
          command_declarations_sha256:prefixLease.command_declarations_sha256,command_declarations_inherited:true}});
      }else started=await client.call('thread/start',startArguments);
    }
    requireValue(continuation || started?.model === model && (!provider || started.modelProvider === provider) && typeof started.thread?.id === 'string',
      'CODEX_THREAD_UNCONTROLLED', 'Codex thread substituted its model/provider or returned no identity');
    if(!continuation){
      const actual={...executionPolicy,actual_thread_type:started.sandbox?.type??null,
        thread_policy_verified:started.sandbox?.type===executionPolicy.thread_type,command_policy_observation:'request_only'};
      await record({execution_policy:actual});
      await onEvent({method:'workflow/toolInterface',diagnostic:canonicalJSON({execution_policy:actual})});
    }
    requireValue(continuation || started.sandbox?.type === executionPolicy.thread_type,
      'CODEX_SANDBOX_UNCONTROLLED', 'Codex thread did not activate the exact authorized access mode');
    activeThread = continuation ? continuationThread : started.thread.id;
    const semanticInput = [{ type: 'text', text }, ...skillInputs];
    const sharedTransport=sourceHome&&options[SOURCE_COMMON_ONLY]?options.sharedResponseTransport:null;
    if(sharedTransport)requireValue(typeof sharedTransport.prepare_setup==='function'&&typeof sharedTransport.decode_setup==='function'
      &&sharedTransport.api_schema&&digest(canonicalJSON(sharedTransport.api_schema))===sharedTransport.api_schema_sha256,
      'CODEX_BATCH_OUTPUT_TRANSPORT','Live source needs an exact qualified shared response transport');
    const prefixTransport=sharedTransport?sharedTransport.prepare_setup(text,output_schema)
      :sourceHome||options.prefix?prepareSharedPrefixOutputTransport(text,output_schema):null;
    if(sharedTransport)requireValue(typeof prefixTransport?.text==='string'&&prefixTransport.schema_sha256===sharedTransport.api_schema_sha256
      &&canonicalJSON(prefixTransport.output_schema)===canonicalJSON(sharedTransport.api_schema),
      'CODEX_BATCH_OUTPUT_TRANSPORT','Live source preparation changed its fixed shared API schema');
    const transportedInput=prefixTransport?[{type:'text',text:prefixTransport.text},...skillInputs]:semanticInput;
    // Normal owned tools arrive as direct native schema, so their declarations
    // do not also belong in ordinary task prose. The blocked prefix contract
    // retains its sealed once-only declaration identity.
    const declarations = !continuation&&!options.prefix&&sourceHome ? commandDeclarations : null;
    const input = declarations ? [...transportedInput,declarations.input] : transportedInput;
    // Ordinary consumers retain their existing semantic input identity. Prefix
    // transport has an explicit actual wire identity and separate semantic pins.
    const semanticInputHash = digest(canonicalJSON(semanticInput));
    const submittedInputHash=digest(canonicalJSON(input));
    const nativeShellExecution=toolCatalog.interface.native_shell.execution;
    if(sourceHome)requireValue(typeof nativeShellExecution==='string'&&nativeShellExecution.length>0
      &&(nativeShellExecution!=='disabled'||Boolean(declarations)),
      'CODEX_PREFIX_DECLARATIONS','Source must mechanically establish its inherited shell or exact broker declarations');
    const inputAudit = {thread_id:activeThread,semantic_input_sha256:semanticInputHash,
      input_sha256:prefixTransport?submittedInputHash:semanticInputHash,submitted_input_sha256:submittedInputHash,
      ...(prefixTransport?{response_transport:{api_schema_sha256:prefixTransport.schema_sha256,
        semantic_schema_sha256:digest(canonicalJSON(output_schema))},
        transported_semantic_input_sha256:digest(canonicalJSON(transportedInput))}:{}),
      ...(declarations?{owned_command_declarations:declarations.audit}:{}),
      ...(sourceHome?{native_shell_execution:nativeShellExecution,command_declaration_basis:declarations
        ?'owned_mcp_broker_when_native_shell_disabled':'inherited_native_shell'}:{})};
    try {
      if (options.authorize) await options.authorize();
      requireOpen();
      ownedMcp?.throwIfFailed();
      // Persist the exact planned submission hashes before any model call.
      // A failed write is a turn failure, never an unaudited submission.
      await record({
        ...(!continuation?{thread_id:activeThread,thread_ids:[...receipt.thread_ids,activeThread],status:'thread_started'}:{}),
        turn_input_receipts:[...(receipt.turn_input_receipts??[]),inputAudit]});
      requireOpen();
      ownedMcp?.throwIfFailed();
      const after = client.events.length, baseline = options.prefix?null:usageBaseline(client.events, activeThread, !continuation, receipt.turn_ids.at(-1));
      rawTurn = { began: process.hrtime.bigint(), items: new Map(), responses: new Set(), counts: {},
        unobserved: 0, unattributed: 0, unretainedItems: 0, unretainedResponses: 0, counterSaturated: false,
        first: null, last: null, retained: false, toolShapes: new Map(), unattributedToolShapes: 0, unretainedToolShapes: 0,
        after, ordinaryTimes: new Map() };
      turnSubmitting = true;
      const begun = await client.call('turn/start', { threadId: activeThread, effort, input,
        ...(prefixTransport?{outputSchema:prefixTransport.output_schema}:output_schema ? { outputSchema: output_schema } : {}) });
      requireValue(typeof begun.turn?.id === 'string', 'CODEX_TURN_SCHEMA', 'Codex turn returned no identity');
      activeTurn = begun.turn.id;
      // A command can arrive while turn/start is still returning. The Host's
      // submission index already owns it; bind that index to the returned ID.
      commandTurnIds.set(commandTurnKey(activeThread,turns),activeTurn);
      turnSubmitting = false;
      for (const event of pendingRaw.splice(0)) await observeRaw(event);
      await record({ turn_id: activeTurn, turn_ids: [...receipt.turn_ids, activeTurn], status: 'turn_started',
        turn_input_receipts:[...receipt.turn_input_receipts.slice(0,-1),{...inputAudit,turn_id:activeTurn}] });
      ownedMcp?.throwIfFailed();
      const completionWait = client.waitFor(event => event.method === 'turn/completed'
        && event.params?.threadId === activeThread && event.params?.turn?.id === activeTurn,
      { after, timeout: timeout_ms, activity: event => agentTurnActivity(event, activeThread, activeTurn) });
      const completed=await (ownedMcp?Promise.race([completionWait,ownedMcp.failed]):completionWait);
      const items = client.events.slice(after).filter(event => event.method === 'item/completed' && event.params?.threadId === activeThread
        && event.params?.turnId === activeTurn).map(event => event.params.item);
      // Retain commands before any metering or semantic-success requirement.
      retainNativeCommands(items,activeThread,activeTurn);
      const events = client.events.slice(after), forkMetering=options.prefix?forkTurnUsage(events,activeThread,activeTurn):null,
        metering = forkMetering?.usage??turnUsageFrom(events, activeThread, activeTurn, baseline);
      const { unavailable_reason, ...usage } = metering;
      await onEvent({...turnUsageMetadata(events, activeThread, activeTurn, forkMetering?.evidence.baseline??baseline, metering),
        ...(forkMetering?{usage_basis:forkMetering.evidence.basis,response_usage_update_count:forkMetering.evidence.response_update_count}: {})});
      if(forkMetering){
        await record({usage,usage_basis:forkMetering.evidence.basis,usage_unavailable_reason:unavailable_reason??null,
          prefix_fork:{...receipt.prefix_fork,inherited_counter_baseline:forkMetering.evidence.baseline??null,usage_evidence:forkMetering.evidence}});
        requireValue(metering.available,'CODEX_PREFIX_USAGE_UNAVAILABLE',`Fork usage cannot be reconciled: ${unavailable_reason}`);
      }
      requireValue(completed.params.turn.status === 'completed', 'CODEX_TURN_FAILED',
        `Codex turn ended with status ${completed.params.turn.status}: ${safeTurnDiagnostic(events, activeThread, activeTurn)}; usage=${canonicalJSON(usage)}`);
      const messages = items.filter(item => item.type === 'agentMessage' && typeof item.text === 'string');
      const finals = messages.filter(item => item.phase === 'final_answer');
      const rawOutput = (finals.length ? finals : messages.filter(item => item.phase == null)).map(item => item.text).join('\n').trim();
      const output=sharedTransport?sharedTransport.decode_setup(rawOutput,output_schema)
        :prefixTransport?decodeSharedPrefixOutputTransport(rawOutput,output_schema):rawOutput;
      requireValue(output.length > 0, 'CODEX_OUTPUT_EMPTY', 'Codex node returned no result');
      const command_audit = session.commandAuditForTurn(activeThread,activeTurn);
      const commandAuditPath=join(receiptHome,`command-audit-${digest(activeTurn)}.json`);
      const commandAudit={schema_version:1,owner:receipt.owner,thread_id:activeThread,turn_id:activeTurn,command_audit,pending_command_ids:commandBroker.pending()};
      await writeDurableJSON(commandAuditPath,commandAudit);
      await retainRawSummary();
      await record({ status: 'completed', usage, usage_basis: forkMetering?.evidence.basis??'thread_total_delta', usage_unavailable_reason: unavailable_reason ?? null,
        item_type_counts:items.reduce((counts,item)=>{if(typeof item.type==='string')counts[item.type]=(counts[item.type]??0)+1;return counts;},{}),
        command_audit_path:commandAuditPath,command_audit_sha256:digest(await readFile(commandAuditPath)),command_audit_count:command_audit.length,
        pending_command_ids:commandAudit.pending_command_ids });
      continuationThread = activeThread; completedTurn=activeTurn;
      if(sourceHome)sourceResults.set(session,{path:started.thread.path,thread_id:activeThread,turn_id:activeTurn,model,effort,usage,
        selection:resolvedSelection??{model,effort},command_declarations_sha256:commandDeclarations?.audit.sha256});
      return { output, thread_id: activeThread, turn_id: activeTurn, usage, item_types: items.map(item => item.type), command_audit,
        audit: { session_mode: 'user_codex', executable_sha256: binaryHash, ...inputAudit,
          instruction_source_count: continuation ? null : Array.isArray(started.instructionSources) ? started.instructionSources.length : null } };
    } catch (error) {
      try { await retainRawSummary(); }
      catch (observationError) { error = new AggregateError([error, observationError], 'Codex turn and raw observation recording failed'); }
      try { await record({ status: 'failed', error_code: typeof error?.code === 'string' ? error.code : 'CODEX_TURN_ERROR' }); }
      catch (receiptError) { error = new AggregateError([error, receiptError], 'Codex turn and receipt recording failed'); }
      try { await session.close(); } catch (cleanupError) { throw new AggregateError([error, cleanupError], 'Codex turn and shutdown failed'); }
      throw error;
    } finally { activeThread = null; activeTurn = null; turnSubmitting = false; pendingRaw.length = 0; rawTurn = null; }
  }
  session.turn = (text, turnOptions) => executeTurn(text, turnOptions, false);
  session.continueTurn = (text, turnOptions) => executeTurn(text, turnOptions, true);
  if(sourceHome)session.sharedSource=()=>{
    requireValue(!closed&&continuationThread&&completedTurn&&ownedMcp,'CODEX_BATCH_SOURCE','Live source is not completed and open');
    return {...structuredClone(sourceResults.get(session)),tool_output_budget:structuredClone(toolOutputBudget),
      tool_interface:structuredClone(toolCatalog.interface),
      execution_policy:structuredClone(executionPolicy),tools:[...(options.toolBroker?.tools()??[]),...commandBroker.tools()],
      tool_transport:{assertHealthy:()=>ownedMcp.throwIfFailed(),failed:ownedMcp.failed},
      command_audit_metadata:item=>({...item,cwd:scrubTurnDiagnostic(item.cwd,1000),command:scrubTurnDiagnostic(item.command,1000),output:scrubTurnDiagnostic(item.output,2000)})};
  };
  return session;
}

// Trusted Host-only setup; no user thread/history is used as the source.
export async function prepareCodexNormalPrefix(options,text,turnOptions={}){
  return prepareNormalPrefix(options,text,turnOptions,false);
}

// Trusted internal factory seam: a dedicated common-only private source stays
// open until its batch owner has drained every child. No Main history is read.
export async function prepareCodexLiveCommonSource(options,text,turnOptions={}){
  return prepareNormalPrefix(options,text,turnOptions,true);
}
async function prepareNormalPrefix(options,text,turnOptions,liveSource){
  requireValue(options.access==='read_only'&&options.hostAuth&&options.authentication?.mode!=='environment_api_key',
    'CODEX_PREFIX_SOURCE','Shared setup requires read-only Host-authenticated normal execution');
  const sourceExecutionAccess=options.sourceExecutionAccess??options.access;
  requireValue(['read_only','bounded_write'].includes(sourceExecutionAccess),'CODEX_PREFIX_SOURCE','Shared setup requires its parent node execution access');
  const env=options.env??process.env,normalHome=resolve(env.CODEX_HOME||join(homedir(),'.codex'));
  let session,setup,homeHandle,revoked=false,finish,sourceCloseAttempted=false;
  const settled=new Promise(resolve=>finish=resolve);
  const owner={async interrupt(){revoked=true;await session?.interrupt();},async close(){
    revoked=true;await session?.close();await settled;await session?.close();if(homeHandle)await closeNormalPrefixHome(homeHandle);
  }};
  const open=()=>requireValue(!revoked,'CODEX_PREFIX_CANCELLED','Shared setup owner was revoked');
  try{
    await options.onPrefixOwned?.(owner);open();
    const binary=await realpath(options.binary);await noSymlinks(binary);
    requireValue(digest(await readFile(binary))===options.expectedBinaryHash,'CODEX_BINARY_CHANGED','Prefix discovery executable changed');open();
    let configuration,selection,primary,discoverySeed,accountId;
    const discovery=(options.clientFactory??createCodexClient)(binary,{home:normalHome,cwd:options.cwd,env,
      ...(liveSource?{onAuthRefresh:async params=>{
        requireValue(!params?.previousAccountId||params.previousAccountId===accountId,'HOST_AUTH_ACCOUNT_CHANGED','Common discovery refresh requested another account');
        return options.hostAuth.credentials({force:true,previousAccountId:accountId});
      }}:{})});
    try{await discovery.call('initialize',{clientInfo:{name:'codex_workflow_prefix_config',version:'1.0.0'},capabilities:{experimentalApi:true}});
      discovery.initialized();
      let authentication;
      if(liveSource){
        const credentials=await options.hostAuth.credentials({previousAccountId:null});
        requireValue(typeof credentials.chatgptAccountId==='string'&&credentials.chatgptAccountId.length>0,'HOST_AUTH_SCHEMA','Common discovery needs exact authenticated account');
        accountId=credentials.chatgptAccountId;
        await discovery.call('account/login/start',{type:'chatgptAuthTokens',...credentials});
        const result=await discovery.call('account/read',{refreshToken:false});
        requireValue(result&&typeof result.requiresOpenaiAuth==='boolean','CODEX_AUTH_SCHEMA','Unsupported common discovery account metadata');
        authentication={authenticated:Boolean(result.account)||result.requiresOpenaiAuth===false,type:result.account?.type??null};
        requireValue(authentication.authenticated&&authentication.type==='chatgpt','CODEX_AUTH_REQUIRED','Common discovery requires authenticated Host ChatGPT');
      }
      configuration=await discovery.call('config/read',{cwd:options.cwd,includeLayers:false});
      selection=structuredClone(options.resolveModelSelection?await options.resolveModelSelection(discovery):{model:options.model,effort:options.effort});
      requireValue(typeof selection?.model==='string'&&selection.model.length>0&&typeof selection?.effort==='string'&&selection.effort.length>0,
        'CODEX_SESSION_ARGUMENTS','Prefix discovery did not resolve the initiating model and effort');
      if(liveSource){
        await authenticatedModel(discovery,selection.model,selection.effort,options.onModelCatalog);
        const metadata=await (options.modelMetadataReader??normalModelMetadata)({client:discovery,home:normalHome,cwd:options.cwd,model:selection.model,configuration});
        discoverySeed={configuration:structuredClone(configuration),selection:structuredClone(selection),metadata:structuredClone(metadata),authentication,account_id:accountId};
      }
    }
    catch(error){primary=error;}
    try{await closeOwnedClient(discovery,options.clientShutdownTimeoutMs);}catch(error){throw primary?new AggregateError([primary,error],'Normal config discovery and shutdown failed'):error;}
    if(primary)throw primary;open();
    homeHandle=await createRunOwnedNormalHome({parent:options.parent,owner:options.owner,cwd:options.cwd,normalHome,configuration,
      onOwned:handle=>{homeHandle=handle;}});open();
    const privateHome=normalPrefixHome(homeHandle);
    session=await createCodexSession({...options,binary,[SOURCE_HOME]:homeHandle,[SOURCE_EXECUTION_ACCESS]:sourceExecutionAccess,[SOURCE_COMMON_ONLY]:liveSource,prefix:undefined,maxTurns:1,
      ...(discoverySeed?{[SOURCE_DISCOVERY]:discoverySeed}:{}),
      model:undefined,effort:undefined,resolveModelSelection:async()=>structuredClone(selection),
      authentication:{mode:'host_chatgpt'},env:{...env,CODEX_HOME:privateHome.home,CODEX_SQLITE_HOME:privateHome.sqlite_home},
      onSessionOwned:async owned=>{session=owned;await options.onSessionOwned?.(owned);open();}});open();
    setup=await session.turn(text,{...turnOptions,output_schema:CODEX_NORMAL_PREFIX_SETUP_SCHEMA});
    if(!liveSource){await session.prepareHostCompletion();sourceCloseAttempted=true;await session.close();open();}
    requireValue(setup.usage.available,'CODEX_PREFIX_USAGE','Setup requires complete actual turn metering');
    requireValue(canonicalJSON(JSON.parse(setup.output))==='{"ready":true}','CODEX_PREFIX_SETUP','Shared setup did not confirm its exact ready contract');
    if(liveSource){open();return {session,setup,source:session.sharedSource(),close:owner.close,interrupt:owner.interrupt};}
    const prefix=await sealNormalPrefix(homeHandle,sourceResults.get(session));
    open();
    setup={...setup,prefix_source:normalPrefixReceipt(prefix)};
    return {prefix,setup,close:owner.close,interrupt:owner.interrupt};
  }catch(error){
    error.setup=setup??{usage:{available:false},...(session?{receipt_home:session.profile.receipt_home}:{})};error.prefix_owner=owner;
    const failures=[error];
    // A failed definitive close remains visible and retains its owner. The
    // cleanup catch must not silently repeat that same shutdown attempt.
    if(session&&!sourceCloseAttempted)try{await session.close();}catch(closeError){failures.push(closeError);}
    if(homeHandle&&(!session||session.shutdownState().close_confirmed))try{await closeNormalPrefixHome(homeHandle);}catch(closeError){failures.push(closeError);}
    if(failures.length>1){const combined=new AggregateError(failures,'Prefix preparation and owned cleanup failed');combined.setup=error.setup;combined.prefix_owner=owner;throw combined;}
    throw error;
  }finally{finish();}
}

Object.defineProperty(prepareCodexNormalPrefix,'usageCapability',{value:CODEX_NORMAL_PREFIX_USAGE_CAPABILITY});

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
    const operation = (async () => { await closeOwnedClient(target,options.clientShutdownTimeoutMs); state.closed = true; })();
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
      closed = true;
      const operation = (async () => {
        const errors=[];
        const attempt=async action=>{try{await action();}catch(error){errors.push(error);}};
        await attempt(()=>options.toolBroker?.revoke());
        // A launch that already passed its preflight owns the client handoff.
        // Wait only for that ownership phase, then close the exact current
        // client instance.  No later launch is permitted once closed is set.
        await attempt(()=>onEvent({method:'workflow/sessionShutdown',phase:'begin',session_mode:'strict'}));
        await ownershipPhase.catch(() => {});
        await attempt(()=>onEvent({method:'workflow/sessionShutdown',phase:'model_client',session_mode:'strict'}));
        await attempt(()=>closeClient(client));
        await attempt(async()=>{
        let timer; let outcome;
        try {
          outcome = options.toolBroker ? await Promise.race([options.toolBroker.quiesce(), new Promise((_, reject) => {
            timer = setTimeout(() => reject(Object.assign(new Error('Workspace tool did not quiesce; retain profile'), { code: 'CODEX_BROKER_SHUTDOWN_TIMEOUT' })), 5000);
          })]) : null;
        } finally { clearTimeout(timer); }
        requireValue(outcome?.quiescent!==false,'CODEX_BROKER_STOP_UNCONFIRMED','Bound execution did not confirm quiescence; retain profile and execution ownership');
        if (outcome?.error) throw Object.assign(new Error('Workspace tool failed during shutdown'), { code: 'CODEX_BROKER_SHUTDOWN_FAILURE', cause: outcome.error });
        });
        if(!errors.length)await attempt(()=>onEvent({method:'workflow/sessionShutdown',phase:'closed',session_mode:'strict'}));
        if(!errors.length)await attempt(async()=>{await cleanupProfile(profile);profileCleaned=true;});
        if(errors.length){
          await attempt(()=>onEvent({method:'workflow/sessionShutdown',phase:'failed',session_mode:'strict',error_code:errors[0].code??'CODEX_SHUTDOWN_FAILED'}));
          if(errors.length===1)throw errors[0];
          throw new AggregateError(errors,'Strict owned cleanup and shutdown observations failed');
        }
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
        await onEvent(codexEventMetadata({method:'item/tool/call',params}));
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
      const started = await client.call('thread/start', { cwd, model, ...(options.endpoint ? { modelProvider: 'qualification' } : {}), approvalPolicy: 'never', sandbox: 'read-only', ephemeral: true,
        environments: [], baseInstructions: STRICT_INSTRUCTIONS, dynamicTools: [...policy.tools(), ...(options.toolBroker?.tools() ?? [])],
      });
      requireValue(Array.isArray(started.instructionSources) && !started.instructionSources.length && started.model === model && typeof started.thread?.id === 'string', 'CODEX_THREAD_UNCONTROLLED', 'Fresh thread has unexpected instruction sources, model substitution or schema');
      activeThread = started.thread.id;
      try {
        await policy.verify(client);
        const input = [{ type: 'text', text }, ...skillInputs];
        const profileHash = digest(await readFile(join(profile.home, 'config.toml')));
        if (options.authorize) await options.authorize();
        requireOpen();
        const after = client.events.length, baseline = usageBaseline(client.events, activeThread, true);
        const begun = await client.call('turn/start', { threadId: activeThread, effort, input, ...(output_schema ? { outputSchema: output_schema } : {}) }); activeTurn = begun.turn.id;
        const completed = await client.waitFor(event => event.method === 'turn/completed' && event.params.threadId === activeThread && event.params.turn.id === activeTurn, {
          after, timeout: timeout_ms, activity: event => agentTurnActivity(event, activeThread, activeTurn),
        });
        const turnEvents=client.events.slice(after);
        const metering=turnUsageFrom(turnEvents,activeThread,activeTurn,baseline);
        const { unavailable_reason, ...usage } = metering;
        await onEvent(turnUsageMetadata(turnEvents,activeThread,activeTurn,baseline,metering));
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
