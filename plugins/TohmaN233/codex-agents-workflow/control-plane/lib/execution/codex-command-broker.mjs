import { randomUUID } from 'node:crypto';
import {prepareOwnedCommandTemp} from './owned-command-temp.mjs';
import { appendFile, mkdir, open, rm, stat, writeFile } from 'node:fs/promises';
import { isAbsolute, join, relative, resolve, sep } from 'node:path';
import { StringDecoder } from 'node:string_decoder';
import { fileURLToPath } from 'node:url';
import { createCodexClient } from './codex-app-server-client.mjs';
import { requireValue } from '../workflow-paths.mjs';
import { pathBoundaries } from '../workflow-bindings.mjs';
import { canonicalJSON,digest } from '../workflow-revisions.mjs';
import {serializedToolResultBytes} from './tool-output-delivery.mjs';
import {prepareCommandLifecycleDiagnostics,readCommandLifecycleDiagnostics,releaseCommandLifecycleDiagnostics} from './command-lifecycle-diagnostics.mjs';

const COMMAND_TIMEOUT_MS = 60 * 60 * 1000;
const DEFAULT_YIELD_MS = 10000;
const OUTPUT_CHUNK_BYTES = 120 * 1024;
const RUNNER_PATH = fileURLToPath(new URL('./codex-command-runner.mjs', import.meta.url));
const SHUTDOWN_GRACE_MS = 2000;
const bounded = async (operation, milliseconds, code) => {
  let timer;
  try { return await Promise.race([operation,new Promise((_,reject)=>{timer=setTimeout(()=>reject(Object.assign(new Error('Owned command shutdown exceeded its bound'),{code})),milliseconds);})]); }
  finally { clearTimeout(timer); }
};
const schema = properties => ({ type: 'object', properties, additionalProperties: false });
const string = { type: 'string' };
const outputBudget = { type: 'integer', minimum: 1, maximum: 200000 };
const yieldBudget = { type: 'integer', minimum: 0, maximum: 30000 };
const textResult = value => ({ success: true, contentItems: [{ type: 'inputText', text: JSON.stringify(value) }] });
const errorResult = (code,message) => ({ success: false, contentItems: [{ type: 'inputText', text: JSON.stringify({error:{code,message}}) }] });
const RECOVERABLE_COMMAND_ERRORS=new Set(['CODEX_COMMAND_ARGUMENTS','CODEX_COMMAND_SHELL','CODEX_COMMAND_TTY_UNAVAILABLE',
  'CODEX_COMMAND_SESSION','CODEX_COMMAND_SCOPE']);

const tools = Object.freeze([
  { name: 'run_workspace_program', description: 'Run an executable with a literal argument array in the node workspace. Optional stdin is delivered as exact UTF-8 bytes and then closed. No shell quoting, pipeline or helper script is needed. Uses the same command sandbox, capture, waiting and continuation as run_workspace_command.',
    inputSchema: {...schema({ program: string, args: {type:'array',items:string,maxItems:256}, stdin: string, workdir: string, yield_time_ms: {oneOf:[{const:0},{type:'integer',minimum:10000,maximum:30000}]}, max_output_tokens: outputBudget }),required:['program','args']} },
  { name: 'run_workspace_command', description: 'Run a command in the node workspace sandbox. Foreground waits default to 10000ms and cannot be shorter; 0 explicitly starts background work. Complete local capture is delivered in chunks within the inherited output budget; longer output remains available through continue_workspace_command.',
    inputSchema: schema({ cmd: string, workdir: string, shell: string, login: { type: 'boolean' }, tty: { type: 'boolean' }, yield_time_ms: {oneOf:[{const:0},{type:'integer',minimum:10000,maximum:30000}]}, max_output_tokens: outputBudget }) },
  { name: 'continue_workspace_command', description: 'Continue reading a run_workspace_command session, send text to its stdin, or send Ctrl-C to terminate it. Output is returned in lossless sequential chunks.',
    inputSchema: schema({ session_id: string, chars: string, yield_time_ms: yieldBudget, max_output_tokens: outputBudget }) },
]);

function commandArgv(platform, shell, command, login, sourcePath) {
  requireValue(typeof command === 'string' && command.length > 0 && command.length <= 1024 * 1024 && !command.includes('\0'),
    'CODEX_COMMAND_ARGUMENTS', 'Command text must be a nonempty bounded string');
  if (platform === 'win32') {
    const selected = typeof shell === 'string' && shell.length ? shell : 'powershell.exe';
    const name = selected.replaceAll('\\', '/').split('/').at(-1).toLowerCase();
    if (['cmd', 'cmd.exe'].includes(name)) return [selected, '/d', '/s', '/c', command];
    if (['powershell', 'powershell.exe', 'pwsh', 'pwsh.exe'].includes(name)) {
      const statusName = 'workflowCommandSucceeded' + randomUUID().replaceAll('-', '');
      return [selected, '-NoLogo', ...(login ? [] : ['-NoProfile']), '-Command',
        '$OutputEncoding = [Console]::InputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false);\n' +
        // Parse the original UTF-8 file as its own script: executable prefixes
        // break using/param prologues. Keep manuscript bytes out of Windows
        // argv, whose length limit is much smaller than our command boundary.
        "$workflowCommandSource = [Text.Encoding]::UTF8.GetString([IO.File]::ReadAllBytes('" +
        sourcePath.replaceAll("'","''") + "'));\n" +
        // Capture final source status before script invocation resets a native
        // failure. Exit only after the normal object formatter finishes: exit
        // inside this pipeline discards deferred objects and following text.
        // A unique parent-scope variable avoids collisions with source locals;
        // return keeps normal success, while terminating errors fail the pipe.
        "$null = [ScriptBlock]::Create($workflowCommandSource);\n" +
        '$' + statusName + ' = $true;\n' +
        "& ([ScriptBlock]::Create($workflowCommandSource + [Environment]::NewLine + '$script:" + statusName + " = $?')) | Out-Default;\n" +
        'exit $(if ($? -and $' + statusName + ') { 0 } else { 1 })'];
    }
    requireValue(false, 'CODEX_COMMAND_SHELL', 'Windows command shell must be PowerShell, pwsh or cmd');
  }
  const selected = typeof shell === 'string' && shell.length ? shell : '/bin/bash';
  return [selected, login === false ? '-c' : '-lc', command];
}

const controlDiagnostic=value=>String(value??'').replace(/https?:\/\/\S+/ig,'[redacted-url]')
  .replace(/\bBearer\s+\S+/ig,'Bearer [redacted]').replace(/\b(?:sk|eyJ)[A-Za-z0-9_.-]{12,}\b/g,'[redacted-token]').slice(0,1000);

export function createCodexCommandBroker({ binary, home, cwd, access, spoolRoot, env = process.env,
  clientFactory = createCodexClient, getClient, platform = process.platform, nodeBinary = process.execPath,
  onOperation = async () => {}, networkAccess = false, allowedPaths = [],recoverToolErrors=false, shutdownGraceMs=SHUTDOWN_GRACE_MS,
  getOutputBudget,ownedCommandTemp:useOwnedTemp,getExecutionPolicy }) {
  requireValue(typeof binary === 'string' && typeof home === 'string' && typeof cwd === 'string'
    && typeof spoolRoot === 'string' && isAbsolute(spoolRoot) && ['read_only', 'bounded_write'].includes(access),
  'CODEX_COMMAND_BROKER', 'Command broker requires the exact node binary, home, workspace, spool root and access mode');
  requireValue(Number.isSafeInteger(shutdownGraceMs)&&shutdownGraceMs>0&&shutdownGraceMs<=SHUTDOWN_GRACE_MS,
    'CODEX_COMMAND_BROKER','Host shutdown grace is outside its fixed upper bound');
  requireValue(typeof nodeBinary === 'string' && isAbsolute(nodeBinary) && typeof onOperation === 'function'
    && typeof networkAccess === 'boolean' && Array.isArray(allowedPaths), 'CODEX_COMMAND_BROKER', 'Command broker callbacks or runtime are invalid');
  requireValue(typeof getOutputBudget==='function','CODEX_TOOL_OUTPUT_BUDGET','Command broker requires an explicit qualified output-budget source');
  const sessions = new Map(), audit = [], closedClients=new Set();
  let client, opening, revoked = false, closing, closeConfirmed=false, forcedCommandShutdown=false;
  // RPC completion and settlement observations are different boundaries. Only
  // the final promise wrapper changes settlement, on either success or failure.
  const settlementPending=session=>session.settlement==='pending';
  const commandPending=session=>!session.commandFinished;
  async function closeOwnedClient(owned) {
    if(!owned||closedClients.has(owned))return;
    requireValue(typeof owned.close==='function','CODEX_COMMAND_STOP_UNCONFIRMED','Owned commands have no client shutdown boundary');
    await bounded(owned.close(),8000,'CODEX_COMMAND_STOP_UNCONFIRMED');
    closedClients.add(owned);
  }
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
  let boundExecutionPolicy;
  function executionPolicy() {
    const policy = getExecutionPolicy?.();
    requireValue(!getExecutionPolicy || policy && ['workspaceWrite','dangerFullAccess'].includes(policy.command_type),
      'CODEX_COMMAND_POLICY', 'Command execution requires resolved Host permissions');
    requireValue(access === 'bounded_write' || policy?.command_type !== 'dangerFullAccess',
      'CODEX_COMMAND_POLICY', 'Read-only capture cannot inherit unrestricted commands');
    if(policy){
      requireValue(policy.command_type===(policy.thread_type==='dangerFullAccess'?'dangerFullAccess':'workspaceWrite')
        &&(access==='read_only'?policy.thread_type==='readOnly':['workspaceWrite','dangerFullAccess'].includes(policy.thread_type)),
        'CODEX_COMMAND_POLICY','Host thread and command permissions contradict one another');
      const identity=canonicalJSON(policy);
      requireValue(boundExecutionPolicy===undefined||boundExecutionPolicy===identity,
        'CODEX_COMMAND_POLICY','Host execution permissions changed during the owned session');
      boundExecutionPolicy=identity;
    }
    return policy;
  }
  const commandSandbox = () => executionPolicy()?.command_type === 'dangerFullAccess'
    ? {type:'dangerFullAccess'}
    : { type: 'workspaceWrite', writableRoots:[...writableRoots,...(ownedTemp?[ownedTemp.path]:[])], networkAccess, excludeTmpdirEnvVar: Boolean(useOwnedTemp), excludeSlashTmp: Boolean(useOwnedTemp) };
  let ownedTemp,preparingTemp,commandEnvironment;const preparationPhases=new Set();
  const assertActive=()=>requireValue(!revoked,'CODEX_COMMAND_REVOKED','Command broker was revoked during command preparation');
  function preparation(kind,action){
    assertActive();
    const phase={id:randomUUID(),kind,promise:null};
    preparationPhases.add(phase);
    phase.promise=(async()=>{assertActive();const result=await action();assertActive();return result;})();
    // Keep the exact promise observable by both its caller and close; never let
    // a rejected background preparation escape or erase its failure.
    void phase.promise.then(()=>preparationPhases.delete(phase),()=>preparationPhases.delete(phase));
    return phase.promise;
  }
  async function prepareTemp(){
    if(!useOwnedTemp)return;
    assertActive();
    if(!preparingTemp)preparingTemp=(async()=>{ownedTemp=await prepareOwnedCommandTemp({workspace,spool});assertActive();commandEnvironment={TEMP:ownedTemp.path,TMP:ownedTemp.path,...(platform==='win32'?{}:{TMPDIR:ownedTemp.path})};await onOperation({phase:'temp_prepared',process_id:ownedTemp.summary.broker_id,runtime_temp:ownedTemp.summary});})();
    await preparingTemp;assertActive();await ownedTemp.assertOwned();assertActive();
  }
  requireValue(!useOwnedTemp||access==='bounded_write'&&relativeAllowed.length===1&&relativeAllowed[0]==='.',
    'CODEX_COMMAND_ISOLATION','Owned command temp requires the complete worker workspace');
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
      if (error.code === 'ENOENT' && settlementPending(session)) return 0;
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
    if (!remaining) return !settlementPending(session) ? session.decoder.end() : '';
    const count = Math.min(remaining, OUTPUT_CHUNK_BYTES), buffer = Buffer.allocUnsafe(count);
    const handle = await open(session.outputPath, 'r');
    let bytesRead;
    try { ({ bytesRead } = await handle.read(buffer, 0, count, session.offset)); }
    finally { await handle.close(); }
    requireValue(bytesRead > 0, 'CODEX_COMMAND_OUTPUT_READ', 'Command output did not advance at its recorded byte offset');
    session.offset += bytesRead;
    const decoded = session.decoder.write(buffer.subarray(0, bytesRead));
    return !settlementPending(session) && session.offset === size ? decoded + session.decoder.end() : decoded;
  }

  async function cleanupSession(session) {
    const lifecycleError=await releaseCommandLifecycleDiagnostics(session.lifecycleCapability);
    sessions.delete(session.id);
    await rm(session.directory, { recursive: true, force: true });
    return lifecycleError;
  }

  async function resultFor(session) {
    if (session.error) throw session.error;
    if(!session.pendingText)session.pendingText=await readChunk(session);
    const size = await outputSize(session), budget=getOutputBudget();
    requireValue(Number.isSafeInteger(budget?.max_result_bytes)&&budget.max_result_bytes>=512,
      'CODEX_TOOL_OUTPUT_BUDGET','Command delivery requires its qualified inherited output budget');
    const envelope=output=>textResult({status:settlementPending(session)?'running':'completed',
      exit_code:settlementPending(session)?null:session.exitCode,output,has_more:true,session_id:session.id});
    let end=session.pendingText.length;
    if(serializedToolResultBytes(envelope(session.pendingText))>budget.max_result_bytes){
      let lo=0,hi=end;
      while(lo<hi){const mid=Math.ceil((lo+hi)/2);
        if(serializedToolResultBytes(envelope(session.pendingText.slice(0,mid)))<=budget.max_result_bytes)lo=mid;else hi=mid-1;
      }
      end=lo;
      if(end>0&&/^[\uDC00-\uDFFF]$/.test(session.pendingText[end]??'')&&/^[\uD800-\uDBFF]$/.test(session.pendingText[end-1]))end--;
      requireValue(end>0,'CODEX_TOOL_OUTPUT_BUDGET','Command result envelope leaves no room for the next UTF-8 character');
    }
    const output=session.pendingText.slice(0,end);session.pendingText=session.pendingText.slice(end);
    const hasMore = session.pendingText.length>0 || session.offset < size || settlementPending(session);
    const value = { status: settlementPending(session) ? 'running' : 'completed', exit_code: settlementPending(session) ? null : session.exitCode,
      output, has_more: hasMore, ...(hasMore ? { session_id: session.id } : {}) };
    const delivered=textResult(value);
    requireValue(serializedToolResultBytes(delivered)<=budget.max_result_bytes,'CODEX_TOOL_OUTPUT_BUDGET','Command result exceeds its inherited delivery budget');
    if (!hasMore) await cleanupSession(session);
    return delivered;
  }

  async function awaitProgress(session, milliseconds) {
    if (settlementPending(session) && !session.error && milliseconds > 0) {
      try{await bounded(session.completion,milliseconds,'CODEX_COMMAND_YIELD');}
      catch(error){if(error.code!=='CODEX_COMMAND_YIELD')throw error;}
    }
    return resultFor(session);
  }

  async function requestStop(session) {
    if (!commandPending(session) || session.stopRequested) return;
    session.stopRequested = true;
    // Windows sandboxed command/exec is buffered and rejects its streaming
    // terminate RPC. The Host-owned runner already polls this exact control
    // file, so deliver Ctrl-C through that channel and let the runner stop its
    // owned child tree while command/exec remains a normal buffered request.
    await appendFile(session.stdinPath, Buffer.from([3]));
    await onOperation({process_id:session.id,phase:'stop_control_written'});
  }

  async function start(args, callId, directProgram=false, owner=null) {
    const tool=directProgram?'run_workspace_program':'run_workspace_command';
    requireValue(args && typeof args === 'object' && !Array.isArray(args)
      && Object.keys(args).every(key => (directProgram?['program','args','stdin','workdir','yield_time_ms','max_output_tokens']:['cmd', 'workdir', 'shell', 'login', 'tty', 'yield_time_ms', 'max_output_tokens']).includes(key)),
    'CODEX_COMMAND_ARGUMENTS', `${tool} arguments do not match its contract`);
    if(directProgram)requireValue(typeof args.program==='string'&&args.program.length>0&&args.program.length<=32768&&!args.program.includes('\0')
      &&Array.isArray(args.args)&&args.args.length<=256&&args.args.every(value=>typeof value==='string'&&!value.includes('\0'))
      &&Buffer.byteLength(canonicalJSON(args.args))<=1024*1024
      &&(args.stdin===undefined||typeof args.stdin==='string'&&Buffer.byteLength(args.stdin)<=2*1024*1024),
      'CODEX_COMMAND_ARGUMENTS','Program requires literal bounded arguments and optional bounded UTF-8 stdin');
    requireValue(args.tty !== true, 'CODEX_COMMAND_TTY_UNAVAILABLE', 'Sandboxed Host capture does not expose a PTY');
    const id = randomUUID(), directory = join(spoolRoot, id), outputPath = join(directory, 'output.bin'), stdinPath = join(directory, 'stdin.bin');
    const sourcePath=join(directory,'command-source.ps1');
    const command = directProgram?[args.program,...args.args]:commandArgv(platform, args.shell, args.cmd, args.login,sourcePath);
    const commandText=directProgram?canonicalJSON(command):args.cmd;
    const workdir = args.workdir ? resolve(cwd, args.workdir) : resolve(cwd);
    const workdirPath=relative(workspace,workdir);
    requireValue(workdirPath===''||!isAbsolute(workdirPath)&&workdirPath!=='..'&&!workdirPath.startsWith('..'+sep),
      'CODEX_COMMAND_SCOPE','Command working directory leaves the node workspace',{workspace,workdir});
    const yieldMs = args.yield_time_ms ?? DEFAULT_YIELD_MS;
    requireValue(Number.isInteger(yieldMs) && (yieldMs===0||yieldMs>=10000&&yieldMs<=30000), 'CODEX_COMMAND_ARGUMENTS', 'Foreground yield_time_ms must be 10000..30000; 0 explicitly starts background work');
    if (args.max_output_tokens !== undefined) requireValue(Number.isInteger(args.max_output_tokens) && args.max_output_tokens >= 1 && args.max_output_tokens <= 200000,
      'CODEX_COMMAND_ARGUMENTS', 'max_output_tokens is outside its compatibility range');
    await mkdir(spoolRoot, { recursive: true });
    await mkdir(directory, { recursive: false });
    if(!directProgram&&platform==='win32'&&/^(?:powershell|pwsh)(?:\.exe)?$/i.test(command[0].replaceAll('\\','/').split('/').at(-1)))
      await writeFile(sourcePath,args.cmd,{flag:'wx',mode:0o600,encoding:'utf8'});
    await writeFile(stdinPath, directProgram?args.stdin??'':'', { flag: 'wx' });
    const specPath = join(directory, 'command.json'),lifecyclePath=join(directory,'lifecycle.jsonl');
    await writeFile(specPath, JSON.stringify({ schema_version: 1, process_id:id, argv: command, cwd: workdir, output_path: outputPath, stdin_path: stdinPath,
      lifecycle_path:lifecyclePath,...(directProgram?{stdin_closed:true}:{}) }), { flag: 'wx' });
    const session = { id, directory, outputPath, stdinPath, offset: 0, pendingText:'', decoder: new StringDecoder('utf8'),
      commandFinished: false, settlement: 'pending', exitCode: null, error: null,stdinClosed:directProgram };
    sessions.set(id, session);
    const started = Date.now();
    const origin=performance.now(),elapsed=()=>Math.round(performance.now()-origin);
    const diagnostics={schema_version:1,parent:{started_at:new Date(started).toISOString(),clock:'performance.now',
      started_observation_begin_ms:0,started_observation_end_ms:null,rpc_begin_ms:null,rpc_response_ms:null,rpc_response_at:null,rpc_outcome:'pending',wall_clock_status:'consistent',validation_end_ms:null,
      lifecycle_read_begin_ms:null,lifecycle_read_end_ms:null,
      observation_begin_ms:null,observation_end_ms:null,observations:[],settlement:'pending',settlement_ms:null},
      runner:{status:'unknown',error_code:'CODEX_COMMAND_LIFECYCLE_NOT_OBSERVED',boundaries:null,phase_counts:null}};
    let lifecycleRead=false;
    const captureLifecycle=async receipt=>{if(lifecycleRead)return;lifecycleRead=true;diagnostics.parent.lifecycle_read_begin_ms=elapsed();
      diagnostics.runner=await readCommandLifecycleDiagnostics(session.lifecycleCapability,id,receipt);diagnostics.parent.lifecycle_read_end_ms=elapsed();
      if(diagnostics.runner.boundaries?.started?.at&&Date.parse(diagnostics.runner.boundaries.started.at)<started
        ||receipt&&diagnostics.runner.boundaries?.receipt?.at&&Date.parse(diagnostics.runner.boundaries.receipt.at)>Date.parse(diagnostics.parent.rpc_response_at)){
        diagnostics.parent.wall_clock_status='unknown';diagnostics.runner={status:'unknown',error_code:'CODEX_COMMAND_LIFECYCLE_CLOCK_ANOMALY',boundaries:null,phase_counts:null};
      }
    };
    const observeTerminal=async event=>{
      const item={phase:event.phase,begin_ms:elapsed(),end_ms:null,status:'pending'};diagnostics.parent.observations.push(item);
      diagnostics.parent.observation_begin_ms??=item.begin_ms;
      try{await onOperation(event);item.status='fulfilled';}
      catch(error){item.status='rejected';item.error_code=typeof error.code==='string'&&/^[A-Z0-9_]{1,96}$/.test(error.code)?error.code:'CODEX_COMMAND_OBSERVATION_FAILED';throw error;}
      finally{item.end_ms=elapsed();diagnostics.parent.observation_end_ms=item.end_ms;}
    };
    await onOperation({ call_id: callId, process_id: id,tool,args_sha256:digest(canonicalJSON(args)), phase: 'started', cwd: workdir });
    diagnostics.parent.started_observation_end_ms=elapsed();
    try {
      const commandClient = await openClient();
      await preparation('command_temp',prepareTemp);
      if(ownedTemp){
        diagnostics.runtime_temp=structuredClone(ownedTemp.summary);
      }
      session.client=commandClient;
      session.lifecycleCapability=await prepareCommandLifecycleDiagnostics(lifecyclePath,id);
      const sandboxPolicy=commandSandbox();
      diagnostics.execution_policy={...(executionPolicy()??{basis:'node_access',command_boundary:access==='read_only'?'capture_spool_only':'host_allowed_paths_and_workspace_audit'}),
        requested_command_policy:structuredClone(sandboxPolicy),command_policy_observation:'request_only'};
      diagnostics.parent.rpc_begin_ms=elapsed();
      session.completion = commandClient.call('command/exec', { command: [nodeBinary,RUNNER_PATH,specPath], processId: id,
        timeoutMs: COMMAND_TIMEOUT_MS, cwd: workdir, sandboxPolicy,...(commandEnvironment?{env:commandEnvironment}:{}) }, { timeout: COMMAND_TIMEOUT_MS + 30000 })
        .then(async response => {
          diagnostics.parent.rpc_response_ms=elapsed();diagnostics.parent.rpc_response_at=new Date().toISOString();
          diagnostics.parent.rpc_outcome='fulfilled';
          if(Date.parse(diagnostics.parent.rpc_response_at)<started)diagnostics.parent.wall_clock_status='unknown';
          session.commandFinished = true;
          requireValue(typeof response.stdout === 'string' && response.stderr === '', 'CODEX_COMMAND_RUNNER',
            `Host command runner emitted an invalid control response: exit=${String(response.exitCode)}, stderr=${controlDiagnostic(response.stderr)}`);
          let receipt;
          try { receipt = JSON.parse(response.stdout.trim()); }
          catch { requireValue(false, 'CODEX_COMMAND_RUNNER', 'Host command runner returned malformed control JSON'); }
          await captureLifecycle(receipt);
          const size = await outputSize(session);
          requireValue(receipt?.schema_version === 1 && Number.isSafeInteger(receipt.exit_code) && receipt.exit_code === response.exitCode
            && Number.isSafeInteger(receipt.output_bytes) && receipt.output_bytes === size,
          'CODEX_COMMAND_RUNNER', 'Host command runner receipt does not match the captured output');
          requireValue(!receipt.error_code,receipt.error_code??'CODEX_COMMAND_RUNNER','Owned command runner could not confirm complete stdio drain');
          session.exitCode = receipt.exit_code;
          diagnostics.parent.validation_end_ms=elapsed();
          const preview = await outputPreview(session.outputPath);
          audit.push({...owner,call_id:callId,process_id:id,status: receipt.signal==='SIGINT'?'cancelled':'completed', exit_code: receipt.exit_code, cwd: workdir, command: commandText, output: preview,
            output_bytes: size, duration_ms: Date.now() - started,diagnostics });
          await observeTerminal({ call_id: callId, process_id: id, phase: 'completed', exit_code: receipt.exit_code,
            output_bytes: size, output_cap_reached: false, duration_ms: Date.now() - started });
        }).catch(async error => {
          if(diagnostics.parent.rpc_response_ms===null){diagnostics.parent.rpc_response_ms=elapsed();diagnostics.parent.rpc_response_at=new Date().toISOString();diagnostics.parent.rpc_outcome='rejected';
            if(Date.parse(diagnostics.parent.rpc_response_at)<started)diagnostics.parent.wall_clock_status='unknown';}
          diagnostics.parent.terminal_error_code=typeof error.code==='string'&&/^[A-Z0-9_]{1,96}$/.test(error.code)?error.code:'CODEX_COMMAND_ERROR';
          session.commandFinished = true; session.error = error;
          await captureLifecycle();
          audit.push({...owner,call_id:callId,process_id:id,status: 'failed', exit_code: null, cwd: workdir, command: commandText, output: '',
            ...(error?.rpc_diagnostic?{diagnostic:error.rpc_diagnostic}:{}),duration_ms: Date.now() - started,diagnostics });
          await observeTerminal({ call_id: callId, process_id: id, phase: 'failed', error_code: error?.code ?? 'CODEX_COMMAND_ERROR',
            ...(error?.rpc_diagnostic?{diagnostic:error.rpc_diagnostic}:{}),duration_ms: Date.now() - started });
        }).then(()=>{
          session.settlement='fulfilled';
          diagnostics.parent.settlement='fulfilled';diagnostics.parent.settlement_ms=elapsed();
        },error=>{
          session.settlement='rejected';
          diagnostics.parent.settlement='rejected';diagnostics.parent.settlement_ms=elapsed();
          throw error;
        });
      // A zero-wait call can return before settlement. Observe rejection now;
      // retain the original promise for explicit progress/close error reporting.
      void session.completion.catch(()=>{});
    } catch (error) {
      session.error = error; session.commandFinished = true; session.settlement='rejected';
      const lifecycleError=await cleanupSession(session);if(lifecycleError)error.command_lifecycle_diagnostic=lifecycleError;
      throw error;
    }
    return awaitProgress(session, yieldMs);
  }

  async function continueSession(args,callId) {
    requireValue(args && typeof args === 'object' && !Array.isArray(args)
      && Object.keys(args).every(key => ['session_id', 'chars', 'yield_time_ms', 'max_output_tokens'].includes(key))
      && typeof args.session_id === 'string', 'CODEX_COMMAND_ARGUMENTS', 'continue_workspace_command arguments do not match its contract');
    const session = sessions.get(args.session_id);
    requireValue(session, 'CODEX_COMMAND_SESSION', 'Unknown or exhausted command session');
    await onOperation({call_id:callId,process_id:session.id,tool:'continue_workspace_command',args_sha256:digest(canonicalJSON(args)),phase:'continued'});
    const yieldMs = args.yield_time_ms ?? (args.chars ? 250 : 5000);
    requireValue(Number.isInteger(yieldMs) && yieldMs >= 0 && yieldMs <= 30000, 'CODEX_COMMAND_ARGUMENTS', 'yield_time_ms is outside 0..30000');
    if (args.max_output_tokens !== undefined) requireValue(Number.isInteger(args.max_output_tokens) && args.max_output_tokens >= 1 && args.max_output_tokens <= 200000,
      'CODEX_COMMAND_ARGUMENTS', 'max_output_tokens is outside its compatibility range');
    if (args.chars) {
      requireValue(typeof args.chars === 'string' && args.chars.length <= 1024 * 1024, 'CODEX_COMMAND_ARGUMENTS', 'stdin text is too large');
      if (args.chars === '\u0003') await requestStop(session);
      else {requireValue(!session.stdinClosed,'CODEX_COMMAND_ARGUMENTS','Program stdin was already closed after its exact initial input');await appendFile(session.stdinPath, Buffer.from(args.chars));}
    }
    return awaitProgress(session, yieldMs);
  }

  return {
    tools: () => tools.map(tool => structuredClone(tool)),
    handles: name => tools.some(tool => tool.name === name),
    async call(name, args, callId, owner=null) {
      requireValue(!revoked && typeof callId === 'string' && callId.length <= 256, 'CODEX_COMMAND_REVOKED', 'Command broker call is unauthorized');
      // This owner comes from the Host's authenticated execution context, never
      // from model tool arguments. Keep it fixed across background settlement.
      requireValue(owner===null||owner&&typeof owner==='object'&&!Array.isArray(owner)
        &&Object.keys(owner).length===2&&typeof owner.thread_id==='string'&&owner.thread_id.length>0&&owner.thread_id.length<=256
        &&Number.isSafeInteger(owner.turn_index)&&owner.turn_index>0,
        'CODEX_COMMAND_OWNER','Command owner must identify one exact Host thread and turn');
      const fixedOwner=owner===null?null:{thread_id:owner.thread_id,turn_index:owner.turn_index};
      try {
        if (name === 'run_workspace_command') return await start(args, callId,false,fixedOwner);
        if (name === 'run_workspace_program') return await start(args,callId,true,fixedOwner);
        if (name === 'continue_workspace_command') return await continueSession(args,callId);
        throw Object.assign(new Error(`Unknown command tool ${name}`), { code: 'CODEX_COMMAND_TOOL' });
      } catch(error) {
        if(!recoverToolErrors||!RECOVERABLE_COMMAND_ERRORS.has(error?.code))throw error;
        const diagnostic=controlDiagnostic(error.message);
        await onOperation({call_id:callId,tool:name,phase:'rejected',error_code:error.code,diagnostic});
        return errorResult(error.code,diagnostic);
      }
    },
    audit: () => audit.map(item => structuredClone(item)),
    pending: () => [...sessions.values()].filter(settlementPending).map(session=>session.id).sort(),
    async interrupt() {
      const settled=await Promise.allSettled([...sessions.values()].filter(commandPending).map(requestStop));
      const failures=settled.filter(item=>item.status==='rejected').map(item=>item.reason);
      if(failures.length)throw new AggregateError(failures,'Command broker could not deliver stop controls');
    },
    async close() {
      if (closing) return closing;
      if(closeConfirmed)return;
      revoked = true;
      const notificationErrors=[];let observationsIncluded=false;
      closing = (async () => {
        const pendingIds=()=>[...sessions.values()].filter(settlementPending).map(session=>session.id).sort();
        const observe=async fields=>{try{await onOperation(fields);}catch(error){notificationErrors.push(error);}};
        const hostStopped=[...sessions.values()].filter(session=>commandPending(session)&&!session.stopRequested);
        const preparations=[...preparationPhases];
        await observe({phase:'close_begin',pending_process_ids:pendingIds(),pending_preparations:preparations.map(({id,kind})=>({id,kind}))});
        try{await this.interrupt();}catch(error){notificationErrors.push(error);}
        // Allocation can publish its sealed leaf only after asynchronous I/O.
        // Revocation forbids new work, but cleanup must wait for every already
        // owned preparation (including shell RPC and probe-file cleanup).
        const prepared=await bounded(Promise.allSettled(preparations.map(phase=>phase.promise)),shutdownGraceMs,'CODEX_COMMAND_PREPARATION_UNSETTLED');
        const preparationErrors=[...new Set(prepared.filter(item=>item.status==='rejected'&&item.reason?.code!=='CODEX_COMMAND_REVOKED').map(item=>item.reason))];
        if(preparationErrors.length)throw Object.assign(new AggregateError(preparationErrors,'Owned command preparation failed during close'),{code:'CODEX_COMMAND_PREPARATION_FAILED'});
        const completions=Promise.allSettled([...sessions.values()].map(session => session.completion).filter(Boolean));
        let forced=false,settlements;
        try { settlements=await bounded(completions,shutdownGraceMs,'CODEX_COMMAND_DRAIN_TIMEOUT'); }
        catch(error) {
          if(error.code!=='CODEX_COMMAND_DRAIN_TIMEOUT')throw error;
          forced=true;
          await observe({phase:'close_forced',pending_process_ids:pendingIds(),error_code:error.code});
          const ownedSessions=[...sessions.values()].filter(settlementPending);
          const ownedClients=[...new Set(ownedSessions.map(session=>session.client))];
          requireValue(ownedClients.length===1&&(!getClient||getClient()===ownedClients[0]),'CODEX_COMMAND_CLIENT_IDENTITY','Pending command shutdown must target its exact original client');
          const owned=ownedClients[0];
          requireValue(owned&&typeof owned.close==='function','CODEX_COMMAND_STOP_UNCONFIRMED','Pending commands have no owned client shutdown boundary');
          // A later normal receipt cannot erase an earlier forced execution
          // shutdown attempt, even when confirmation only arrives on retry.
          if(ownedSessions.some(commandPending))forcedCommandShutdown=true;
          await closeOwnedClient(owned);
          settlements=await bounded(completions,1000,'CODEX_COMMAND_STOP_UNCONFIRMED');
        }
        const failed=[...sessions.values()].find(session=>session.error);
        await observe({phase:'close_settled',pending_process_ids:pendingIds(),forced,error_code:failed?.error?.code??null});
        if(!getClient&&!forced)await closeOwnedClient(client);
        const settlementErrors=settlements.filter(item=>item.status==='rejected').map(item=>item.reason);
        const observationErrors=[...new Set([...notificationErrors,...settlementErrors,
          ...(settlementErrors.length?[...sessions.values()].map(session=>session.error).filter(Boolean):[])])];
        if(observationErrors.length){closeConfirmed=true;observationsIncluded=true;throw Object.assign(new AggregateError(observationErrors,'Command settlement observation failed'),{code:'CODEX_COMMAND_OBSERVATION_FAILED'});}
        if(forced||forcedCommandShutdown){closeConfirmed=true;throw Object.assign(new Error('Completed turn required forced owned command shutdown; preserve evidence'),{code:'CODEX_COMMAND_SHUTDOWN_FORCED'});}
        if(failed){closeConfirmed=true;throw failed.error;}
        if(hostStopped.some(session=>session.exitCode===130)){closeConfirmed=true;throw Object.assign(new Error('Host completion cancelled an unfinished command'),{code:'CODEX_COMMAND_SHUTDOWN_CANCELLED'});}
        for(const session of sessions.values()){
          const lifecycleError=await releaseCommandLifecycleDiagnostics(session.lifecycleCapability);
          if(lifecycleError)throw Object.assign(new Error('Owned lifecycle diagnostic close failed'),{code:lifecycleError.error_code,command_lifecycle_diagnostic:lifecycleError});
        }
        if(ownedTemp)await ownedTemp.close();
        sessions.clear();
        await rm(spoolRoot, { recursive: true, force: true });
        closeConfirmed=true;
      })();
      try{return await closing;}
      catch(error){
        const errors=observationsIncluded?[error]:[error,...notificationErrors];
        try{await onOperation({phase:'close_failed',pending_process_ids:[...sessions.values()].filter(settlementPending).map(session=>session.id).sort(),error_code:error.code??'CODEX_COMMAND_SHUTDOWN_FAILED'});}
        catch(observationError){errors.push(observationError);}
        if(errors.length===1)throw error;
        throw new AggregateError(errors,'Command shutdown and its observations failed');
      }finally{closing=null;}
    },
  };
}
