import { randomUUID } from 'node:crypto';
import { appendFile, mkdir, open, rm, stat, writeFile } from 'node:fs/promises';
import { isAbsolute, join, relative, resolve, sep } from 'node:path';
import { StringDecoder } from 'node:string_decoder';
import { fileURLToPath } from 'node:url';
import { createCodexClient } from './codex-app-server-client.mjs';
import { requireValue } from '../workflow-paths.mjs';
import { pathBoundaries } from '../workflow-bindings.mjs';

const COMMAND_TIMEOUT_MS = 60 * 60 * 1000;
const DEFAULT_YIELD_MS = 10000;
const OUTPUT_CHUNK_BYTES = 120 * 1024;
const RUNNER_PATH = fileURLToPath(new URL('./codex-command-runner.mjs', import.meta.url));
const schema = properties => ({ type: 'object', properties, additionalProperties: false });
const string = { type: 'string' };
const outputBudget = { type: 'integer', minimum: 1, maximum: 200000 };
const yieldBudget = { type: 'integer', minimum: 0, maximum: 30000 };
const textResult = value => ({ success: true, contentItems: [{ type: 'inputText', text: JSON.stringify(value) }] });
const errorResult = (code,message) => ({ success: false, contentItems: [{ type: 'inputText', text: JSON.stringify({error:{code,message}}) }] });
const RECOVERABLE_COMMAND_ERRORS=new Set(['CODEX_COMMAND_ARGUMENTS','CODEX_COMMAND_SHELL','CODEX_COMMAND_TTY_UNAVAILABLE',
  'CODEX_COMMAND_SESSION','CODEX_COMMAND_SCOPE']);

const tools = Object.freeze([
  { name: 'run_workspace_command', description: 'Run a command in the node workspace sandbox. Host output delivery uses complete local capture; longer output remains available through continue_workspace_command.',
    inputSchema: schema({ cmd: string, workdir: string, shell: string, login: { type: 'boolean' }, tty: { type: 'boolean' }, yield_time_ms: yieldBudget, max_output_tokens: outputBudget }) },
  { name: 'continue_workspace_command', description: 'Continue reading a run_workspace_command session, send text to its stdin, or send Ctrl-C to terminate it. Output is returned in lossless sequential chunks.',
    inputSchema: schema({ session_id: string, chars: string, yield_time_ms: yieldBudget, max_output_tokens: outputBudget }) },
]);

function commandArgv(platform, shell, command, login) {
  requireValue(typeof command === 'string' && command.length > 0 && command.length <= 1024 * 1024 && !command.includes('\0'),
    'CODEX_COMMAND_ARGUMENTS', 'Command text must be a nonempty bounded string');
  if (platform === 'win32') {
    const selected = typeof shell === 'string' && shell.length ? shell : 'powershell.exe';
    const name = selected.replaceAll('\\', '/').split('/').at(-1).toLowerCase();
    if (['cmd', 'cmd.exe'].includes(name)) return [selected, '/d', '/s', '/c', command];
    if (['powershell', 'powershell.exe', 'pwsh', 'pwsh.exe'].includes(name))
      return [selected, '-NoLogo', ...(login ? [] : ['-NoProfile']), '-Command', command];
    requireValue(false, 'CODEX_COMMAND_SHELL', 'Windows command shell must be PowerShell, pwsh or cmd');
  }
  const selected = typeof shell === 'string' && shell.length ? shell : '/bin/bash';
  return [selected, login === false ? '-c' : '-lc', command];
}

const wait = milliseconds => new Promise(resolveWait => setTimeout(resolveWait, milliseconds));
const controlDiagnostic=value=>String(value??'').replace(/https?:\/\/\S+/ig,'[redacted-url]')
  .replace(/\bBearer\s+\S+/ig,'Bearer [redacted]').replace(/\b(?:sk|eyJ)[A-Za-z0-9_.-]{12,}\b/g,'[redacted-token]').slice(0,1000);

export function createCodexCommandBroker({ binary, home, cwd, access, spoolRoot, env = process.env,
  clientFactory = createCodexClient, getClient, platform = process.platform, nodeBinary = process.execPath,
  onOperation = async () => {}, networkAccess = false, allowedPaths = [],recoverToolErrors=false }) {
  requireValue(typeof binary === 'string' && typeof home === 'string' && typeof cwd === 'string'
    && typeof spoolRoot === 'string' && isAbsolute(spoolRoot) && ['read_only', 'bounded_write'].includes(access),
  'CODEX_COMMAND_BROKER', 'Command broker requires the exact node binary, home, workspace, spool root and access mode');
  requireValue(typeof nodeBinary === 'string' && isAbsolute(nodeBinary) && typeof onOperation === 'function'
    && typeof networkAccess === 'boolean' && Array.isArray(allowedPaths), 'CODEX_COMMAND_BROKER', 'Command broker callbacks or runtime are invalid');
  const sessions = new Map(), audit = [];
  let client, opening, revoked = false, closing;
  const workspace=resolve(cwd);
  const relativeAllowed=pathBoundaries(allowedPaths.map(value=>{
    if(typeof value!=='string'||!isAbsolute(value.trim()))return value;
    const target=resolve(value.trim()),path=relative(workspace,target);
    requireValue(path===''||!isAbsolute(path)&&path!=='..'&&!path.startsWith('..'+sep),'CODEX_COMMAND_SCOPE',
      'Command write boundary leaves the node workspace',{workspace,target});
    return path||'.';
  }));
  requireValue(access!=='bounded_write'||relativeAllowed.length>0,'CODEX_COMMAND_SCOPE','Writable command sessions need concrete Host path boundaries');
  const spool=resolve(spoolRoot),spoolPath=relative(workspace,spool);
  const spoolInsideWorkspace=spoolPath===''||!isAbsolute(spoolPath)&&spoolPath!=='..'&&!spoolPath.startsWith('..'+sep);
  // Windows App Server cannot initialize its workspace-write sandbox from
  // file or subdirectory roots. Keep the exact Host-normalized item scopes in
  // relativeAllowed for admission and post-run workspace auditing, while the
  // OS sandbox receives the workspace root it requires to start reliably.
  const writableRoots = access === 'bounded_write'
    ? [workspace,...(spoolInsideWorkspace?[]:[spool])] : [spool];
  const sandboxPolicy = { type: 'workspaceWrite', writableRoots, networkAccess, excludeTmpdirEnvVar: false, excludeSlashTmp: false };

  async function openClient() {
    requireValue(!revoked, 'CODEX_COMMAND_REVOKED', 'Command broker was revoked');
    if (getClient) {
      const owned = getClient();
      requireValue(owned && typeof owned.call === 'function', 'CODEX_COMMAND_CLIENT', 'Node App Server client is unavailable for command execution');
      return owned;
    }
    if (client) return client;
    if (!opening) opening = (async () => {
      const next = clientFactory(binary, { home, cwd, env, commandOnly: true });
      try {
        await next.call('initialize', { clientInfo: { name: 'codex_agents_workflow_commands', version: '1.0.0' }, capabilities: { experimentalApi: true } });
        next.initialized();
        requireValue(!revoked, 'CODEX_COMMAND_REVOKED', 'Command broker was revoked during startup');
        client = next;
        return next;
      } catch (error) { await next.close().catch(() => {}); throw error; }
    })();
    try { return await opening; }
    finally { opening = null; }
  }

  async function outputSize(session) {
    try { return (await stat(session.outputPath)).size; }
    catch (error) {
      if (error.code === 'ENOENT' && !session.completed) return 0;
      throw error;
    }
  }

  async function outputPreview(path, limit = 2000) {
    const size = (await stat(path)).size;
    if (!size) return '';
    const count = Math.min(size, limit), buffer = Buffer.allocUnsafe(count), handle = await open(path, 'r');
    let bytesRead;
    try { ({ bytesRead } = await handle.read(buffer, 0, count, 0)); }
    finally { await handle.close(); }
    return buffer.subarray(0, bytesRead).toString('utf8');
  }

  async function readChunk(session) {
    const size = await outputSize(session), remaining = Math.max(0, size - session.offset);
    if (!remaining) return session.completed ? session.decoder.end() : '';
    const count = Math.min(remaining, OUTPUT_CHUNK_BYTES), buffer = Buffer.allocUnsafe(count);
    const handle = await open(session.outputPath, 'r');
    let bytesRead;
    try { ({ bytesRead } = await handle.read(buffer, 0, count, session.offset)); }
    finally { await handle.close(); }
    requireValue(bytesRead > 0, 'CODEX_COMMAND_OUTPUT_READ', 'Command output did not advance at its recorded byte offset');
    session.offset += bytesRead;
    const decoded = session.decoder.write(buffer.subarray(0, bytesRead));
    return session.completed && session.offset === size ? decoded + session.decoder.end() : decoded;
  }

  async function cleanupSession(session) {
    sessions.delete(session.id);
    await rm(session.directory, { recursive: true, force: true });
  }

  async function resultFor(session) {
    if (session.error) throw session.error;
    const output = await readChunk(session), size = await outputSize(session);
    const hasMore = session.offset < size || !session.completed;
    const value = { status: session.completed ? 'completed' : 'running', exit_code: session.completed ? session.exitCode : null,
      output, has_more: hasMore, ...(hasMore ? { session_id: session.id } : {}) };
    if (!hasMore) await cleanupSession(session);
    return textResult(value);
  }

  async function awaitProgress(session, milliseconds) {
    if (!session.completed && !session.error && milliseconds > 0) await Promise.race([session.completion, wait(milliseconds)]);
    return resultFor(session);
  }

  async function requestStop(session) {
    if (session.completed || session.stopRequested) return;
    session.stopRequested = true;
    // Windows sandboxed command/exec is buffered and rejects its streaming
    // terminate RPC. The Host-owned runner already polls this exact control
    // file, so deliver Ctrl-C through that channel and let the runner stop its
    // owned child tree while command/exec remains a normal buffered request.
    await appendFile(session.stdinPath, Buffer.from([3]));
  }

  async function start(args, callId) {
    requireValue(args && typeof args === 'object' && !Array.isArray(args)
      && Object.keys(args).every(key => ['cmd', 'workdir', 'shell', 'login', 'tty', 'yield_time_ms', 'max_output_tokens'].includes(key)),
    'CODEX_COMMAND_ARGUMENTS', 'run_workspace_command arguments do not match its contract');
    requireValue(args.tty !== true, 'CODEX_COMMAND_TTY_UNAVAILABLE', 'Sandboxed Host capture does not expose a PTY');
    const command = commandArgv(platform, args.shell, args.cmd, args.login);
    const workdir = args.workdir ? resolve(cwd, args.workdir) : resolve(cwd);
    const workdirPath=relative(workspace,workdir);
    requireValue(workdirPath===''||!isAbsolute(workdirPath)&&workdirPath!=='..'&&!workdirPath.startsWith('..'+sep),
      'CODEX_COMMAND_SCOPE','Command working directory leaves the node workspace',{workspace,workdir});
    const yieldMs = args.yield_time_ms ?? DEFAULT_YIELD_MS;
    requireValue(Number.isInteger(yieldMs) && yieldMs >= 0 && yieldMs <= 30000, 'CODEX_COMMAND_ARGUMENTS', 'yield_time_ms is outside 0..30000');
    if (args.max_output_tokens !== undefined) requireValue(Number.isInteger(args.max_output_tokens) && args.max_output_tokens >= 1 && args.max_output_tokens <= 200000,
      'CODEX_COMMAND_ARGUMENTS', 'max_output_tokens is outside its compatibility range');
    const id = randomUUID(), directory = join(spoolRoot, id), outputPath = join(directory, 'output.bin'), stdinPath = join(directory, 'stdin.bin');
    await mkdir(spoolRoot, { recursive: true });
    await mkdir(directory, { recursive: false });
    await writeFile(stdinPath, '', { flag: 'wx' });
    const specPath = join(directory, 'command.json');
    await writeFile(specPath, JSON.stringify({ schema_version: 1, argv: command, cwd: workdir, output_path: outputPath, stdin_path: stdinPath }), { flag: 'wx' });
    const session = { id, directory, outputPath, stdinPath, offset: 0, decoder: new StringDecoder('utf8'),
      completed: false, exitCode: null, error: null };
    sessions.set(id, session);
    const started = Date.now();
    await onOperation({ call_id: callId, process_id: id, phase: 'started', cwd: workdir, command: args.cmd });
    try {
      const commandClient = await openClient();
      session.completion = commandClient.call('command/exec', { command: [nodeBinary, RUNNER_PATH, specPath], processId: id,
        timeoutMs: COMMAND_TIMEOUT_MS, cwd: workdir, sandboxPolicy }, { timeout: COMMAND_TIMEOUT_MS + 30000 })
        .then(async response => {
          requireValue(typeof response.stdout === 'string' && response.stderr === '', 'CODEX_COMMAND_RUNNER',
            `Host command runner emitted an invalid control response: exit=${String(response.exitCode)}, stderr=${controlDiagnostic(response.stderr)}`);
          let receipt;
          try { receipt = JSON.parse(response.stdout.trim()); }
          catch { requireValue(false, 'CODEX_COMMAND_RUNNER', 'Host command runner returned malformed control JSON'); }
          const size = await outputSize(session);
          requireValue(receipt?.schema_version === 1 && Number.isSafeInteger(receipt.exit_code) && receipt.exit_code === response.exitCode
            && Number.isSafeInteger(receipt.output_bytes) && receipt.output_bytes === size,
          'CODEX_COMMAND_RUNNER', 'Host command runner receipt does not match the captured output');
          session.exitCode = receipt.exit_code; session.completed = true;
          const preview = await outputPreview(session.outputPath);
          audit.push({ status: 'completed', exit_code: receipt.exit_code, cwd: workdir, command: args.cmd, output: preview,
            output_bytes: size, duration_ms: Date.now() - started });
          await onOperation({ call_id: callId, process_id: id, phase: 'completed', exit_code: receipt.exit_code,
            output_bytes: size, output_cap_reached: false, duration_ms: Date.now() - started });
        }, async error => {
          session.error = error; session.completed = true;
          audit.push({ status: 'failed', exit_code: null, cwd: workdir, command: args.cmd, output: '',
            ...(error?.rpc_diagnostic?{diagnostic:error.rpc_diagnostic}:{}),duration_ms: Date.now() - started });
          await onOperation({ call_id: callId, process_id: id, phase: 'failed', error_code: error?.code ?? 'CODEX_COMMAND_ERROR',
            ...(error?.rpc_diagnostic?{diagnostic:error.rpc_diagnostic}:{}),duration_ms: Date.now() - started });
        });
    } catch (error) {
      session.error = error; session.completed = true;
      await cleanupSession(session);
      throw error;
    }
    return awaitProgress(session, yieldMs);
  }

  async function continueSession(args) {
    requireValue(args && typeof args === 'object' && !Array.isArray(args)
      && Object.keys(args).every(key => ['session_id', 'chars', 'yield_time_ms', 'max_output_tokens'].includes(key))
      && typeof args.session_id === 'string', 'CODEX_COMMAND_ARGUMENTS', 'continue_workspace_command arguments do not match its contract');
    const session = sessions.get(args.session_id);
    requireValue(session, 'CODEX_COMMAND_SESSION', 'Unknown or exhausted command session');
    const yieldMs = args.yield_time_ms ?? (args.chars ? 250 : 5000);
    requireValue(Number.isInteger(yieldMs) && yieldMs >= 0 && yieldMs <= 30000, 'CODEX_COMMAND_ARGUMENTS', 'yield_time_ms is outside 0..30000');
    if (args.max_output_tokens !== undefined) requireValue(Number.isInteger(args.max_output_tokens) && args.max_output_tokens >= 1 && args.max_output_tokens <= 200000,
      'CODEX_COMMAND_ARGUMENTS', 'max_output_tokens is outside its compatibility range');
    if (args.chars) {
      requireValue(typeof args.chars === 'string' && args.chars.length <= 1024 * 1024, 'CODEX_COMMAND_ARGUMENTS', 'stdin text is too large');
      if (args.chars === '\u0003') await requestStop(session);
      else await appendFile(session.stdinPath, Buffer.from(args.chars));
    }
    return awaitProgress(session, yieldMs);
  }

  return {
    tools: () => tools.map(tool => structuredClone(tool)),
    handles: name => tools.some(tool => tool.name === name),
    async call(name, args, callId) {
      requireValue(!revoked && typeof callId === 'string' && callId.length <= 256, 'CODEX_COMMAND_REVOKED', 'Command broker call is unauthorized');
      try {
        if (name === 'run_workspace_command') return await start(args, callId);
        if (name === 'continue_workspace_command') return await continueSession(args);
        throw Object.assign(new Error(`Unknown command tool ${name}`), { code: 'CODEX_COMMAND_TOOL' });
      } catch(error) {
        if(!recoverToolErrors||!RECOVERABLE_COMMAND_ERRORS.has(error?.code))throw error;
        const diagnostic=controlDiagnostic(error.message);
        await onOperation({call_id:callId,tool:name,phase:'rejected',error_code:error.code,diagnostic});
        return errorResult(error.code,diagnostic);
      }
    },
    audit: () => audit.map(item => structuredClone(item)),
    async interrupt() {
      const settled=await Promise.allSettled([...sessions.values()].filter(session => !session.completed).map(requestStop));
      const failures=settled.filter(item=>item.status==='rejected').map(item=>item.reason);
      if(failures.length)throw new AggregateError(failures,'Command broker could not deliver stop controls');
    },
    async close() {
      if (closing) return closing;
      revoked = true;
      closing = (async () => {
        await this.interrupt();
        await Promise.allSettled([...sessions.values()].map(session => session.completion).filter(Boolean));
        if (!getClient) await client?.close();
        sessions.clear();
        await rm(spoolRoot, { recursive: true, force: true });
      })();
      return closing;
    },
  };
}
