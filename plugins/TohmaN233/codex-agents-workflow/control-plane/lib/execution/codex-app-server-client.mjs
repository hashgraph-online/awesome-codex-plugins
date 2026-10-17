import { spawn } from 'node:child_process';
import { createInterface } from 'node:readline';

const rawMethods = new Set(['rawResponseItem/completed', 'rawResponse/completed']);
const rawItemTypes = new Set(['message', 'agent_message', 'reasoning', 'local_shell_call', 'function_call',
  'tool_search_call', 'function_call_output', 'custom_tool_call', 'custom_tool_call_output', 'tool_search_output',
  'web_search_call', 'image_generation_call', 'compaction', 'configuration_update', 'compaction_trigger', 'context_compaction', 'other']);
const rawStatuses = new Set(['in_progress', 'completed', 'incomplete', 'failed']);
const rawUsageFields = ['inputTokens', 'cachedInputTokens', 'cacheWriteInputTokens', 'outputTokens', 'reasoningOutputTokens', 'totalTokens'];
const rawToolTypes = new Set(['function_call', 'function_call_output', 'custom_tool_call', 'custom_tool_call_output']);
// Private provenance preserves derived counts when the owned session validates
// an ingress-scrubbed item again. Wire-supplied byte fields are never trusted.
const scrubbedToolShapes = new WeakMap();
const rawInspectionBytes = 65_536;
const lexicalReferences = [['ALL_TOOLS', /\bALL_TOOLS\b/], ['tools.web__run', /\btools\.web__run\b/], ['tools.exec_command', /\btools\.exec_command\b/]];
function inputObservation(input, bytes) {
  if (typeof input !== 'string') return Object.freeze({ status: 'unknown' });
  if (bytes > rawInspectionBytes) return Object.freeze({ status: 'oversize' });
  // These are lexical references only. Comments and strings can match; this
  // observation never establishes that a referenced tool was actually called.
  return Object.freeze({ status: 'known', lexical_references: Object.freeze(lexicalReferences.filter(([, pattern]) => pattern.test(input)).map(([label]) => label)) });
}
function outputObservation(output, shape) {
  const text = typeof output === 'string' ? output
    : shape.output_kind === 'content_items' && output.length === 1 && output[0].type === 'input_text' ? output[0].text : null;
  if (text === null) return Object.freeze({ status: 'unknown' });
  if (Buffer.byteLength(text, 'utf8') > rawInspectionBytes) return Object.freeze({ status: 'oversize' });
  let descriptors;
  try { descriptors = JSON.parse(text); } catch { return Object.freeze({ status: 'unknown' }); }
  if (!Array.isArray(descriptors) || !descriptors.length || descriptors.length > 4096 || !descriptors.every(value =>
    value && typeof value === 'object' && !Array.isArray(value) && Object.keys(value).length === 2
    && Object.keys(value).every(key => ['name', 'description'].includes(key))
    && typeof value.name === 'string' && /^[A-Za-z_][A-Za-z0-9_.:-]{0,127}$/.test(value.name)
    && typeof value.description === 'string')) return Object.freeze({ status: 'unknown' });
  // The complete strict array is structural evidence only. Retain neither
  // names/descriptions nor source fragments, hashes, queries or result bodies.
  return Object.freeze({ status: 'known', structural_kind: 'tool_descriptor_array', descriptor_count: descriptors.length });
}
function rawToolShape(source) {
  const previous = scrubbedToolShapes.get(source);
  if (previous) return previous;
  const name = typeof source.name === 'string' && /^[A-Za-z_][A-Za-z0-9_.:-]{0,127}$/.test(source.name)
    ? source.name : null;
  const input = source.type === 'function_call' ? source.arguments : source.type === 'custom_tool_call' ? source.input : undefined;
  const shape = { name, input_bytes: typeof input === 'string' ? Buffer.byteLength(input, 'utf8') : null,
    output_bytes: null, output_kind: null };
  if (source.type.endsWith('_output')) {
    const output = source.output;
    if (typeof output === 'string') { shape.output_bytes = Buffer.byteLength(output, 'utf8'); shape.output_kind = 'string'; }
    else if (Array.isArray(output) && output.length <= 4096 && output.every(item => {
      if (!item || typeof item !== 'object' || Array.isArray(item) || typeof item.type !== 'string') return false;
      const fields = { input_text: ['type', 'text'], input_image: ['type', 'image_url', 'file_id', 'detail'],
        input_audio: ['type', 'audio_url'], encrypted_content: ['type', 'encrypted_content'] };
      const allowed = Object.hasOwn(fields, item.type) ? fields[item.type] : null;
      if (!allowed || !Object.keys(item).every(key => allowed.includes(key))) return false;
      if (item.type === 'input_text') return typeof item.text === 'string';
      if (item.type === 'input_audio') return typeof item.audio_url === 'string';
      if (item.type === 'encrypted_content') return typeof item.encrypted_content === 'string';
      return (typeof item.image_url === 'string' || typeof item.file_id === 'string')
        && (item.image_url === undefined || typeof item.image_url === 'string')
        && (item.file_id === undefined || typeof item.file_id === 'string')
        && (item.detail == null || ['auto', 'low', 'high', 'original'].includes(item.detail));
    })) {
      // Only the generated FunctionCallOutputContentItem representation is
      // measured. Its serialized bytes are temporary, never retained or hashed.
      shape.output_bytes = Buffer.byteLength(JSON.stringify(output), 'utf8'); shape.output_kind = 'content_items';
    }
    shape.output_observation = outputObservation(output, shape);
  } else {
    shape.input_observation = inputObservation(input, shape.input_bytes);
  }
  return Object.freeze(shape);
}
export const isCodexRawNotification = event => rawMethods.has(event?.method);
// Scrub before retention, callback dispatch or waiter matching. Never include
// rejected values in diagnostics: these envelopes contain arbitrary secrets.
export function scrubCodexRawNotification(event) {
  const valid = condition => {
    if (!condition) throw Object.assign(new Error('Malformed bounded Codex raw notification'), { code: 'CODEX_RAW_NOTIFICATION_INVALID' });
  };
  const identifier = value => typeof value === 'string' && value.length > 0 && value.length <= 256
    && /^[A-Za-z0-9][A-Za-z0-9._:/-]*$/.test(value);
  const p = event?.params;
  valid(isCodexRawNotification(event) && p && typeof p === 'object' && !Array.isArray(p));
  valid(identifier(p.threadId) && identifier(p.turnId));
  const params = { threadId: p.threadId, turnId: p.turnId };
  if (event.method === 'rawResponseItem/completed') {
    const source = p.item;
    valid(source && typeof source === 'object' && !Array.isArray(source) && typeof source.type === 'string' && source.type.length > 0);
    // Future unrelated item variants cannot expand retained data or break an
    // ordinary turn. Classify them as unobserved without keeping the type text.
    if (!rawItemTypes.has(source.type)) return { method: event.method, params: { ...params, item: { type: 'other' } } };
    const item = { type: source.type };
    for (const field of ['id', 'call_id']) if (source[field] != null) {
      valid(identifier(source[field])); item[field] = source[field];
    }
    if (source.type === 'tool_search_call') {
      valid(['server', 'client'].includes(source.execution));
      item.execution = source.execution;
      if (source.status != null) { valid(rawStatuses.has(source.status)); item.status = source.status; }
    }
    if (rawToolTypes.has(source.type)) {
      const shape = rawToolShape(source);
      Object.assign(item, shape); scrubbedToolShapes.set(item, shape);
    }
    params.item = item;
  } else {
    valid(identifier(p.responseId));
    params.responseId = p.responseId;
    if (p.usage != null) {
      valid(typeof p.usage === 'object' && !Array.isArray(p.usage));
      params.usage = {};
      for (const field of rawUsageFields) {
        if (field === 'cacheWriteInputTokens' && p.usage[field] === undefined) continue;
        valid(Number.isSafeInteger(p.usage[field]) && p.usage[field] >= 0);
        params.usage[field] = p.usage[field];
      }
    }
  }
  return { method: event.method, params };
}

// Version-qualified stdio client. Error bodies/auth events are never logged.
export function createCodexClient(binary, { home, cwd, overrides = [], env = process.env, onToolCall, onAuthRefresh, credentialOnly = false, catalogOnly = false, commandOnly = false, rawObservation, onEvent = () => {}, onEventBatch, spawnImpl = spawn }) {
  const commandMethods = ['command/exec', 'command/exec/write', 'command/exec/terminate'];
  const methods = new Set(commandOnly ? ['initialize', ...commandMethods] : catalogOnly ? ['initialize','account/read','model/list'] : credentialOnly ? ['initialize', 'getAuthStatus', 'account/read'] : ['initialize', 'config/read', 'hooks/list', 'skills/list', 'skills/config/write', 'model/list', 'thread/list', 'thread/read', 'thread/turns/list', 'thread/start', 'thread/fork', 'turn/start', 'turn/interrupt', 'account/read', 'account/login/start', 'account/login/cancel', ...commandMethods]);
  const child = spawnImpl(binary, ['app-server', '--stdio', ...overrides.flatMap(value => ['-c', value])], {
    cwd, env: { ...env, CODEX_HOME: home }, windowsHide: true, shell: false,
    stdio: ['pipe', 'pipe', 'pipe'],
  });
  const pending = new Map();
  const events = [];
  const eventWaiters = new Set();
  let nextId = 1;
  let fatal;
  let shutdownExit;
  let observationFailure;
  let closed = false;
  let stderrBytes = 0;
  let startupStderr = '';
  let exited = false;
  let closing;
  const pipeFailure=message=>{
    const details={pid:child.pid??null,exit_seen:exited,transport_closed:closed,stdout_paused:child.stdout.isPaused(),
      stdout_buffered_bytes:child.stdout.readableLength,stderr_buffered_bytes:child.stderr.readableLength,
      notification_queue:notifications.length,notification_bytes:notificationBytes,notification_drain_pending:draining};
    return Object.assign(new Error(message+'; transport='+JSON.stringify(details)),{code:'CODEX_APP_SERVER_PIPE_HELD',details});
  };
  // Streaming deltas are activity signals, not replayable turn artifacts.
  // Retaining every token delta (or imposing a lifetime byte/event ceiling)
  // makes an otherwise healthy long turn fail while it is still active.
  const transientEvent = method => /(?:\/delta|\/outputDelta)$/i.test(method);
  const closedPromise = new Promise(resolve => child.once('close', () => { closed = true; resolve(); }));
  const exitedPromise = new Promise(resolve => child.once('exit', () => { exited = true; resolve(); }));
  async function settledWithin(promise, timeout) {
    let timer;
    try { return await Promise.race([promise.then(() => true), new Promise(resolve => { timer = setTimeout(() => resolve(false), timeout); })]); }
    finally { clearTimeout(timer); }
  }
  function fail(error) {
    if (!fatal || fatal === shutdownExit) fatal = error;
    for (const waiter of pending.values()) waiter.reject(fatal);
    pending.clear();
    for (const waiter of eventWaiters) waiter.reject(fatal);
    eventWaiters.clear();
  }
  child.on('error', fail);
  child.stdin.on('error', fail);
  child.stdout.on('error', fail);
  child.stderr.on('data', data => {
    stderrBytes += data.length;
    if (startupStderr.length < 2048)
      startupStderr += data.toString('utf8').slice(0, 2048 - startupStderr.length);
  });
  child.on('exit', (code, signal) => {
    const diagnostic = process.env.CODEX_WORKFLOW_DIAGNOSTIC_STDERR === '1' && code !== 0
      ? startupStderr.replace(/https?:\/\/\S+/ig, '[redacted-url]')
        .replace(/\bBearer\s+\S+/ig, 'Bearer [redacted]')
        .replace(/\b(?:sk|eyJ)[A-Za-z0-9_.-]{12,}\b/g, '[redacted-token]')
        .replace(/((?:api[_-]?key|access[_-]?token|refresh[_-]?token|authorization|password|cookie|secret)\s*[:=]\s*)\S+/ig, '$1[redacted]')
        .slice(0, 512) : '';
    const error = new Error(`App Server exited: code=${code}, signal=${signal}, stderr_bytes=${stderrBytes}${diagnostic ? `, diagnostic=${diagnostic}` : ''}`);
    if (closing && code === 0 && !fatal) shutdownExit = error;
    if (code !== 0 && startupStderr.includes('failed to initialize sqlite state runtime')) error.code = 'CODEX_STATE_RUNTIME_INIT';
    fail(error);
  });
  function write(message) {
    if (fatal || closed || closing) throw fatal ?? Object.assign(new Error('Owned App Server is closing'), { code: 'CODEX_APP_SERVER_CLOSED' });
    child.stdin.write(JSON.stringify(message) + '\n');
  }
  // Keep notification ordering, but independent model tool requests must not
  // serialize one another or block their own RPC responses and cancellation.
  let inbound = Promise.resolve();
  const notifications = [];
  let draining = false, notificationBytes = 0;
  const pureObservation = message => ['item/started','item/completed','thread/tokenUsage/updated'].includes(message.method);
  const notificationStats = {received:0,batches:0,batched_events:0,peak_queued:0,peak_bytes:0};
  const flushEvents = async () => {
    let tail; do { tail=inbound; await tail; } while (tail!==inbound);
    if (fatal && fatal !== shutdownExit) throw fatal;
  };
  function scheduleDrain() {
    if (draining) return;
    draining=true;
    inbound=inbound.then(drainNotifications).catch(error=>{observationFailure=error;fail(error);child.kill();}).finally(()=>{
      draining=false;
      if((!fatal||fatal===shutdownExit)&&notifications.length) scheduleDrain();
      else if(!fatal&&!closed&&!closing) child.stdout.resume();
    });
  }
  async function drainNotifications() {
    while (notifications.length && (!fatal || fatal === shutdownExit)) {
      const batch = [notifications.shift()];
      if (onEventBatch && pureObservation(batch[0].message)) {
        while (batch.length < 64 && notifications.length && pureObservation(notifications[0].message)) batch.push(notifications.shift());
      }
      const messages = batch.map(item => item.message);
      if (onEventBatch && pureObservation(messages[0])) {
        await onEventBatch(messages);notificationStats.batches++;notificationStats.batched_events+=messages.length;
      }
      else await onEvent(messages[0]);
      for (const message of messages) {
        if (!transientEvent(message.method)) events.push(message);
        for (const waiter of [...eventWaiters]) if (waiter.matches(message)) waiter.resolve(message);
      }
      notificationBytes -= batch.reduce((sum,item) => sum + item.bytes,0);
    }
  }
  let authentication = Promise.resolve();
  const interactive = new Map();
  function handleRequest(message) {
    if (interactive.has(message.id)) throw new Error('Duplicate App Server interactive request identity');
    const operation = (async () => {
      if (message.method === 'account/chatgptAuthTokens/refresh' && onAuthRefresh) {
        const refresh = authentication.then(() => onAuthRefresh(message.params));
        authentication = refresh.catch(() => {}); // The tracked operation below reports the original failure.
        const result = await refresh;
        if (!fatal && !closed && !closing) write({ id: message.id, result });
        return;
      }
      if (message.method !== 'item/tool/call' || !onToolCall) {
        const error = new Error(`App Server interactive request requires attention: ${message.method}`);
        error.code = 'CODEX_INTERACTIVE_REQUEST_UNHANDLED';
        throw error;
      }
      await flushEvents();
      for (const waiter of [...eventWaiters]) waiter.matches(message);
      const result = await onToolCall(message.params);
      if (!fatal && !closed && !closing) write({ id: message.id, result });
    })();
    interactive.set(message.id, operation);
    operation.then(() => interactive.delete(message.id), error => {
      interactive.delete(message.id); fail(error); child.kill();
    });
  }
  function safeRpcDiagnostic(method,rpcError){
    if(method!=='command/exec')return null;
    const message=typeof rpcError?.message==='string'?rpcError.message.toLowerCase():'';
    if(message.includes('windows sandbox')&&message.includes('setup refresh had errors'))return 'windows_sandbox_setup_refresh';
    return null;
  }
  function settleResponse(message) {
    const waiter = pending.get(message.id);
    if (!waiter) throw new Error('Uncorrelated App Server response');
    pending.delete(message.id);
    // Server error bodies and stderr may contain credential URLs. Record metadata only.
    if (message.error) {
      const diagnostic=safeRpcDiagnostic(waiter.method,message.error);
      const error=new Error(`RPC ${waiter.method} failed: code=${message.error.code}${diagnostic?`, diagnostic=${diagnostic}`:''}`);
      error.code='CODEX_RPC_ERROR'; error.rpc_code=message.error.code;
      if(diagnostic)error.rpc_diagnostic=diagnostic;
      waiter.reject(error);
    }
    else waiter.resolve(message.result);
  }
  createInterface({ input: child.stdout }).on('line', line => {
    let message;
    try { message = JSON.parse(line); }
    catch (error) { fail(error); child.kill(); return; }
    if (fatal || closed || closing) return;
    if (isCodexRawNotification(message)) {
      try {
        // Unrequested raw bodies must not leak into ordinary client logs.
        if (rawObservation?.supported !== true) return;
        if (Object.hasOwn(message, 'id')) throw Object.assign(new Error('Raw notification has an RPC request identity'), { code: 'CODEX_RAW_NOTIFICATION_INVALID' });
        message = scrubCodexRawNotification(message);
      } catch (error) { fail(error); child.kill(); return; }
    }
    if (!message.method || Object.hasOwn(message, 'id')) {
      try { if (message.method) handleRequest(message); else settleResponse(message); }
      catch (error) { fail(error); child.kill(); }
      return;
    }
    const bytes = Buffer.byteLength(JSON.stringify(message));
    // Pause transport while durable callbacks drain. readline can emit many
    // small lines already decoded from the same chunk after stdout.pause().
    // Bound actual bytes rather than rejecting that valid residual by count.
    if (notificationBytes + bytes > 8 * 1024 * 1024) {
      fail(Object.assign(new Error(`App Server notification queue exceeded its byte bound: queued=${notificationBytes}, incoming=${bytes}, limit=${8*1024*1024}`), {code:'CODEX_NOTIFICATION_QUEUE_LIMIT'})); child.kill(); return;
    }
    notifications.push({message,bytes}); notificationBytes += bytes;
    notificationStats.received++;notificationStats.peak_queued=Math.max(notificationStats.peak_queued,notifications.length);
    notificationStats.peak_bytes=Math.max(notificationStats.peak_bytes,notificationBytes);
    if (notifications.length >= 128 || notificationBytes >= 4 * 1024 * 1024) child.stdout.pause();
    scheduleDrain();
  });
  return {
    events,
    pid: child.pid,
    flushEvents,
    notificationStats: () => ({...notificationStats,queued:notifications.length,queued_bytes:notificationBytes,
      drain_pending:draining,...(observationFailure?{error_code:observationFailure.code??'CODEX_NOTIFICATION_SINK_FAILED'}:{})}),
    call(method, params, { timeout = 20000 } = {}) {
      if (!methods.has(method)) throw new Error(`Method outside qualified App Server contract: ${method}`);
      if (!Number.isSafeInteger(timeout) || timeout <= 0 || timeout > 2 * 60 * 60 * 1000) throw new Error('RPC timeout is outside the qualified bound');
      if (method === 'account/login/start' && !(['chatgpt', 'chatgptDeviceCode', 'apiKey'].includes(params?.type) || params?.type === 'chatgptAuthTokens' && typeof onAuthRefresh === 'function')) throw new Error('Unsupported authentication flow');
      if (fatal) throw fatal;
      if (closed || closing) throw Object.assign(new Error('Owned App Server is closing'), { code: 'CODEX_APP_SERVER_CLOSED' });
      const id = nextId++;
      return new Promise((resolve, reject) => {
        const timer = setTimeout(() => { fail(new Error(`RPC deadline: ${method}`)); child.kill(); }, timeout);
        pending.set(id, {
          method,
          resolve: value => { clearTimeout(timer); resolve(value); },
          reject: error => { clearTimeout(timer); reject(error); },
        });
        write({ id, method, params });
      });
    },
    initialized() { if (fatal) throw fatal; write({ method: 'initialized' }); },
    waitFor(matches, { after = 0, timeout = 0, activity } = {}) {
      if (!Number.isSafeInteger(timeout) || timeout < 0) throw new Error('App Server event timeout must be a nonnegative integer');
      if (fatal) return Promise.reject(fatal);
      const found = events.slice(after).find(matches);
      if (found) return Promise.resolve(found);
      return new Promise((resolve, reject) => {
        let timer;
        const arm = () => {
          clearTimeout(timer);
          if (timeout === 0) return;
          timer = setTimeout(() => {
            const error = new Error(activity ? 'App Server event inactivity deadline' : 'App Server event deadline');
            if (activity) error.code = 'APP_SERVER_INACTIVITY_TIMEOUT';
            waiter.reject(error);
          }, timeout);
        };
        const waiter = {
          matches: message => {
            if (matches(message)) return true;
            if (activity?.(message)) arm();
            return false;
          },
          resolve: value => { clearTimeout(timer); eventWaiters.delete(waiter); resolve(value); },
          reject: error => { clearTimeout(timer); eventWaiters.delete(waiter); reject(error); },
        };
        eventWaiters.add(waiter);
        arm();
      });
    },
    async close({timeout=8000}={}) {
      if(!Number.isSafeInteger(timeout)||timeout<=0||timeout>8000)throw Object.assign(new Error('Owned App Server close bound is outside 1..8000ms'),{code:'CODEX_SESSION_ARGUMENTS'});
      if (closing) return closing;
      const alreadyFailed=Boolean(fatal&&fatal!==shutdownExit);
      let drainSettled=false,timer;
      const drain=inbound.then(()=>{
        drainSettled=true;
        if(observationFailure&&!alreadyFailed)throw observationFailure;
      });
      const deadline=new Promise((_,reject)=>{timer=setTimeout(()=>reject(Object.assign(new Error('Owned App Server shutdown remains unconfirmed'),
        {code:drainSettled?'CODEX_APP_SERVER_STOP_TIMEOUT':'CODEX_NOTIFICATION_DRAIN_PENDING',
          details:{transport_closed:closed,notification_drain_pending:!drainSettled}})),timeout);});
      const transport = (async () => {
        if(closed)return;
        // EOF asks this exact stdio server to exit normally, letting its own
        // native tools and plugin helpers wind down before forced termination.
        if (!child.stdin.destroyed) child.stdin.end();
        if (await settledWithin(closedPromise, 1500)) return;
        if (exited) throw pipeFailure('Owned App Server exited while a helper still holds its stdio pipes');
        if (process.platform === 'win32' && Number.isInteger(child.pid)) {
          // The PID belongs to the child spawned by this client. Never target
          // a shared Codex process or a process discovered by name.
          const killer = spawn('taskkill', ['/PID', String(child.pid), '/T', '/F'], { windowsHide: true, stdio: 'ignore', shell: false });
          const termination = new Promise((resolve, reject) => { killer.once('error', reject); killer.once('close', code => code === 0 ? resolve() : reject(new Error(`Owned App Server tree termination failed: ${code}`))); });
          if (!await settledWithin(termination, 2000)) {
            killer.kill();
            throw Object.assign(new Error('Owned App Server tree termination timed out'), { code: 'CODEX_APP_SERVER_TREE_STOP_TIMEOUT' });
          }
        } else child.kill();
        if (!await settledWithin(exitedPromise, 2500)) throw Object.assign(new Error('Owned App Server did not exit after shutdown'), { code: 'CODEX_APP_SERVER_STOP_TIMEOUT' });
        if (!await settledWithin(closedPromise, 1000)) throw pipeFailure('Owned App Server or helper still holds stdio pipes');
      })();
      const settlement=Promise.allSettled([transport,drain]).then(results=>{
        const failures=results.filter(result=>result.status==='rejected').map(result=>result.reason);
        if(failures.length===1)throw failures[0];
        if(failures.length)throw new AggregateError(failures,'Owned App Server transport and durable drain failed');
      });
      const operation=Promise.race([settlement,deadline]);
      closing = operation;
      try { return await operation; }
      finally { clearTimeout(timer);if (closing === operation) closing = null; }
    },
  };
}
