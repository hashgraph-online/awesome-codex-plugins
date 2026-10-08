import { spawn } from 'node:child_process';
import { createInterface } from 'node:readline';

// Version-qualified stdio client. Error bodies/auth events are never logged.
export function createCodexClient(binary, { home, cwd, overrides = [], env = process.env, onToolCall, onAuthRefresh, credentialOnly = false, catalogOnly = false, commandOnly = false, onEvent = () => {}, spawnImpl = spawn }) {
  const commandMethods = ['command/exec', 'command/exec/write', 'command/exec/terminate'];
  const methods = new Set(commandOnly ? ['initialize', ...commandMethods] : catalogOnly ? ['initialize','account/read','model/list'] : credentialOnly ? ['initialize', 'getAuthStatus', 'account/read'] : ['initialize', 'config/read', 'skills/list', 'skills/config/write', 'model/list', 'thread/list', 'thread/read', 'thread/turns/list', 'thread/start', 'turn/start', 'turn/interrupt', 'account/read', 'account/login/start', 'account/login/cancel', ...commandMethods]);
  const child = spawnImpl(binary, ['app-server', '--stdio', ...overrides.flatMap(value => ['-c', value])], {
    cwd, env: { ...env, CODEX_HOME: home }, windowsHide: true, shell: false,
    stdio: ['pipe', 'pipe', 'pipe'],
  });
  const pending = new Map();
  const events = [];
  const eventWaiters = new Set();
  let nextId = 1;
  let fatal;
  let closed = false;
  let stderrBytes = 0;
  let startupStderr = '';
  let exited = false;
  let closing;
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
    fatal ??= error;
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
    if (code !== 0 && startupStderr.includes('failed to initialize sqlite state runtime')) error.code = 'CODEX_STATE_RUNTIME_INIT';
    fail(error);
  });
  function write(message) { child.stdin.write(JSON.stringify(message) + '\n'); }
  // Serialize async host tool handlers; do not let their failures escape the RPC
  // lifecycle or dispatch an unobserved Promise as a tool result.
  let inbound = Promise.resolve();
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
    // A Host dynamic-tool handler may call the same App Server's sandboxed
    // command RPC. Resolve that response outside the serialized inbound handler
    // so the tool request can finish; command output itself is file-backed.
    if (!message.method && pending.get(message.id)?.method.startsWith('command/exec')) {
      try { settleResponse(message); } catch (error) { fail(error); child.kill(); }
      return;
    }
    inbound = inbound.then(async () => {
    if (fatal) return;
      if (message.method) {
        if (Object.hasOwn(message, 'id')) {
          if (message.method === 'account/chatgptAuthTokens/refresh' && onAuthRefresh) {
            const result = await onAuthRefresh(message.params);
            write({ id: message.id, result }); return;
          }
          if (message.method !== 'item/tool/call' || !onToolCall) {
            const error = new Error(`App Server interactive request requires attention: ${message.method}`);
            error.code = 'CODEX_INTERACTIVE_REQUEST_UNHANDLED';
            throw error;
          }
          // Interactive tool requests are agent activity even though request
          // bodies are deliberately kept out of the retained event log.
          for (const waiter of [...eventWaiters]) waiter.matches(message);
          const result = await onToolCall(message.params);
          write({ id: message.id, result });
          return;
        }
        if (!transientEvent(message.method)) events.push(message);
        await onEvent(message);
        for (const waiter of [...eventWaiters]) if (waiter.matches(message)) waiter.resolve(message);
        return;
      }
      settleResponse(message);
    }).catch(error => { fail(error); child.kill(); });
  });
  return {
    events,
    pid: child.pid,
    call(method, params, { timeout = 20000 } = {}) {
      if (!methods.has(method)) throw new Error(`Method outside qualified App Server contract: ${method}`);
      if (!Number.isSafeInteger(timeout) || timeout <= 0 || timeout > 2 * 60 * 60 * 1000) throw new Error('RPC timeout is outside the qualified bound');
      if (method === 'account/login/start' && !(['chatgpt', 'chatgptDeviceCode', 'apiKey'].includes(params?.type) || params?.type === 'chatgptAuthTokens' && typeof onAuthRefresh === 'function')) throw new Error('Unsupported authentication flow');
      if (fatal) throw fatal;
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
    async close() {
      if (closed) return;
      if (closing) return closing;
      const operation = (async () => {
        // EOF asks this exact stdio server to exit normally, letting its own
        // native tools and plugin helpers wind down before forced termination.
        if (!child.stdin.destroyed) child.stdin.end();
        if (await settledWithin(closedPromise, 1500)) return;
        if (exited) throw Object.assign(new Error('Owned App Server exited while a helper still holds its stdio pipes'), { code: 'CODEX_APP_SERVER_PIPE_HELD' });
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
        if (!await settledWithin(closedPromise, 1000)) throw Object.assign(new Error('Owned App Server or helper still holds stdio pipes'), { code: 'CODEX_APP_SERVER_PIPE_HELD' });
      })();
      closing = operation;
      try { return await operation; }
      finally { if (closing === operation) closing = null; }
    },
  };
}
