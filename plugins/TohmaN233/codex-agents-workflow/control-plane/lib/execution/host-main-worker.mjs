import { spawn } from 'node:child_process';
import { watch } from 'node:fs';
import { open, readFile, rename, stat, unlink, writeFile } from 'node:fs/promises';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { digest } from '../workflow-revisions.mjs';
import { readEvents, replayEvents } from '../workflow-events.mjs';

const workerFile = fileURLToPath(import.meta.url);
const handshakeMs = 15_000;
const heartbeatMs = 5_000;

// The detached process is the execution owner. A controller in another process
// can fence the journal, but cannot stop this process's in-memory session.
export function watchHostMainAuthority({ runtime, runId, controlToken, owner, stopRun, healthMs = heartbeatMs }) {
  const directory = runtime.runs.directory(runId);
  const journal = join(directory, 'events.jsonl');
  const expectedHash = digest(controlToken);
  let watcher, health, retry, resolveDone, rejectDone;
  let closed = false, checking = false, pending = false, stopping = false, tornSince = null, observedSize = -1, observedMtime = -1;
  const done = new Promise((resolve, reject) => { resolveDone = resolve; rejectDone = reject; });
  const cleanup = () => { closed = true; watcher?.close(); clearInterval(health); clearTimeout(retry); };
  const stop = async (reason, error) => {
    if (stopping || closed) return;
    stopping = true; cleanup();
    try {
      await stopRun(runId);
      if (error) rejectDone(error);
      else resolveDone({ reason });
    } catch (stopError) {
      rejectDone(error ? new AggregateError([error, stopError], 'Host Main authority check and local stop failed') : stopError);
    }
  };
  const check = async () => {
    pending = true;
    if (checking || stopping || closed) return;
    checking = true;
    try {
      while (pending && !stopping && !closed) {
        pending = false;
        let state;
        try {
          const metadata = await stat(journal);
          if (metadata.size === observedSize && metadata.mtimeMs === observedMtime) continue;
          state = replayEvents((await readEvents(journal)).events);
          observedSize = metadata.size; observedMtime = metadata.mtimeMs; tornSince = null;
        }
        catch (error) {
          if (error.code === 'RUN_JOURNAL_TORN' && (tornSince ??= Date.now()) + 1000 > Date.now()) {
            clearTimeout(retry); retry = setTimeout(() => void check(), 25); continue;
          }
          await stop('authority_read_failed', error); return;
        }
        if (state.run_id !== runId) {
          await stop('authority_invalid', workerError('HOST_MAIN_WORKER_IDENTITY', 'Host Main authority check observed a different Run')); return;
        }
        if (state.status === 'cancelled') { await stop('cancelled'); return; }
        if (state.control_hash !== expectedHash || state.main_actor !== owner || ['interrupted', 'failed'].includes(state.status)) {
          await stop('authority_revoked'); return;
        }
        // A normal pause retains the current owner so in-flight work may settle.
      }
    } finally { checking = false; }
  };
  try {
    watcher = watch(directory, (_event, name) => { if (!name || String(name) === 'events.jsonl') void check(); });
    watcher.on('error', error => { void stop('authority_watch_failed', error); });
    health = setInterval(() => void check(), healthMs);
    void check();
  } catch (error) { void stop('authority_watch_failed', error); }
  return { done, close: () => { if (!closed) { cleanup(); resolveDone(null); } return done; } };
}

function workerStatePath(configPath, runId) {
  return join(dirname(resolve(configPath)), 'workflow-runs', `run-${runId}.run`, 'host-main-worker.json');
}

export async function writeHostMainWorker(configPath, runId, phase, extra = {}) {
  const target = workerStatePath(configPath, runId), temporary = `${target}.${process.pid}.tmp`;
  await writeFile(temporary, JSON.stringify({ run_id: runId, pid: process.pid, phase, at: new Date().toISOString(), ...extra }));
  try {
    // Windows can deny replacement while a status reader briefly holds the
    // destination. Bound the retry; persistent publication failure is fatal.
    const deadline = Date.now() + 1000;
    for (;;) {
      try { await rename(temporary, target); return; }
      catch (error) {
        if (!['EPERM', 'EACCES'].includes(error.code) || Date.now() >= deadline) throw error;
        await new Promise(resolveDelay => setTimeout(resolveDelay, 10));
      }
    }
  } finally {
    try { await unlink(temporary); } catch (error) { if (error.code !== 'ENOENT') throw error; }
  }
}

export async function readHostMainWorker(configPath, runId) {
  let record;
  try { record = JSON.parse(await readFile(workerStatePath(configPath, runId), 'utf8')); }
  catch (error) { if (error.code === 'ENOENT') return null; throw error; }
  if (record.run_id !== runId) throw workerError('HOST_MAIN_WORKER_IDENTITY', 'Host Main worker record belongs to a different Run');
  const age = Date.now() - Date.parse(record.at);
  if(record.phase==='running'&&age>heartbeatMs*3)
    return {...record,phase:'stale',error:{code:'HOST_MAIN_WORKER_STALE',message:'The detached Host worker stopped reporting progress; inspect its Run log before recovery.'}};
  if(record.phase==='running'){
    if(!Number.isSafeInteger(record.pid)||record.pid<1)throw workerError('HOST_MAIN_WORKER_IDENTITY','Host worker record has no valid process identity');
    try{process.kill(record.pid,0);}catch(error){
      if(error.code==='ESRCH'){
        // The worker may publish its terminal receipt and exit between the
        // first read and this liveness probe. Re-read that exact identity.
        const latest=JSON.parse(await readFile(workerStatePath(configPath,runId),'utf8'));
        if(latest.run_id!==runId||latest.pid!==record.pid)throw workerError('HOST_MAIN_WORKER_IDENTITY','Host worker identity changed during exit confirmation');
        if(latest.phase!=='running')return latest;
        return {...record,phase:'failed',error:{code:'HOST_MAIN_WORKER_EXIT',message:'The detached Host worker exited without a terminal record; inspect the Run before retrying.'}};
      }
      if(error.code!=='EPERM')throw error;
    }
  }
  return record;
}

function workerError(code, message) {
  return Object.assign(new Error(message), { code });
}

export function buildHostMainWorkerTerminal(outcome, authorityStop) {
  if (!outcome || typeof outcome.status !== 'string')
    throw workerError('HOST_MAIN_WORKER_OUTCOME', 'Host Main execution returned no terminal status');
  const stop = outcome.outcome;
  const termination = authorityStop
    ? { confirmed: true, reason: authorityStop?.reason ?? 'execution_settled' }
    : null;
  const confirmedCancellation = termination?.confirmed === true && termination.reason === 'cancelled';
  const confirmedAuthorityRevocation = termination?.confirmed === true && termination.reason === 'authority_revoked';
  const expectedAuthorityStop = (confirmedCancellation || confirmedAuthorityRevocation)
    && outcome.status === 'failed'
    && outcome.error?.code === 'HOST_MAIN_STOPPED'
    && Array.isArray(outcome.error.secondary_codes)
    && outcome.error.secondary_codes.length === 0;
  const failedOutcome = ['failed', 'audit_or_cleanup_failed'].includes(outcome.status);
  const phase = failedOutcome && !expectedAuthorityStop
    ? outcome.status
    : confirmedCancellation ? 'cancelled' : authorityStop ? 'stopped' : outcome.status;
  const record = {
    ...(termination ? { termination: {
      ...termination,
      ...(expectedAuthorityStop ? { host_main_error: structuredClone(outcome.error) } : {}),
    } } : {}),
    ...(stop ? { outcome: { status: stop.status, stop_reason: stop.stop_reason, node_id: stop.node_id,
      ...(stop.error ? { error: stop.error } : {}) } } : {}),
    ...(outcome.error && !expectedAuthorityStop ? { error: structuredClone(outcome.error) } : {}),
  };
  const exitCode = failedOutcome && !expectedAuthorityStop ? 1 : 0;
  return { phase, record, exitCode };
}

export async function launchDetachedHostMain({ configPath, defaultConfigPath, runId, controlToken, owner, env = process.env }) {
  const runDirectory = join(dirname(resolve(configPath)), 'workflow-runs', `run-${runId}.run`);
  const log = await open(join(runDirectory, 'host-main-worker.log'), 'a');
  let child;
  try {
    child = spawn(process.execPath, [workerFile, resolve(configPath), resolve(defaultConfigPath), runId], {
      cwd: dirname(resolve(configPath)), env, detached: true, windowsHide: true,
      stdio: ['ignore', log.fd, log.fd, 'ipc'],
    });
  } finally { await log.close(); }
  try {
    await new Promise((accept, reject) => {
      const timeout = setTimeout(() => reject(workerError('HOST_MAIN_WORKER_START_TIMEOUT', 'Detached Host Main worker did not acknowledge startup')), handshakeMs);
      const cleanup = () => { clearTimeout(timeout); child.off('message', onMessage); child.off('error', onError); child.off('exit', onExit); };
      const onMessage = message => {
        if (message?.type === 'ready' && message.run_id === runId) { cleanup(); accept(); }
        else if (message?.type === 'error') { cleanup(); reject(workerError(message.code ?? 'HOST_MAIN_WORKER_START', message.message ?? 'Detached Host Main worker failed')); }
      };
      const onError = error => { cleanup(); reject(error); };
      const onExit = code => { cleanup(); reject(workerError('HOST_MAIN_WORKER_EXIT', `Detached Host Main worker exited before startup acknowledgment (${code})`)); };
      child.on('message', onMessage); child.once('error', onError); child.once('exit', onExit);
      child.send({ type: 'launch', run_id: runId, control_token: controlToken, owner }, error => { if (error) onError(error); });
    });
    if (child.connected) child.disconnect();
    child.unref();
    return { run_id: runId, status: 'starting', host_worker_pid: child.pid };
  } catch (error) {
    if (child.connected) child.disconnect();
    // A failed handshake must not leave an unowned child running.
    try { child.kill(); } catch {}
    throw error;
  }
}

export async function stopOwnedSessions(service, runId) {
  service.hostMainManager.fenceRun(runId);
  const stopped=await Promise.allSettled([service.managedNativeManager.stopRun(runId),service.strictManager.stopRun(runId),service.hostMainManager.stopRun(runId)]);
  const failures=stopped.filter(item=>item.status==='rejected').map(item=>item.reason);
  if(failures.length)throw new AggregateError(failures,'Host-owned sessions did not all confirm cancellation');
}

async function workerMain() {
  const [configPath, defaultConfigPath, runId] = process.argv.slice(2);
  if (!configPath || !defaultConfigPath || !runId || !process.send) throw workerError('HOST_MAIN_WORKER_ARGS', 'Detached Host Main worker requires exact launch identity over IPC');
  const launch = await new Promise(resolve => process.once('message', resolve));
  if (launch?.type !== 'launch' || launch.run_id !== runId || typeof launch.control_token !== 'string' || typeof launch.owner !== 'string')
    throw workerError('HOST_MAIN_WORKER_IDENTITY', 'Detached Host Main launch identity is invalid');
  const { WorkflowService } = await import(pathToFileURL(join(dirname(workerFile), '..', 'workflow-service.mjs')).href);
  const service = new WorkflowService({ configPath, defaultConfigPath, env: process.env });
  const { runtime, drive, hostMainManager } = await service.open();
  const record = await runtime.runs.read(runId);
  if (record.state.main_actor !== launch.owner || record.state.status !== 'running') throw workerError('HOST_MAIN_WORKER_STATE', 'Detached Host Main launch no longer matches the running task');
  await runtime.authorizeController(runId, { control_token: launch.control_token });
  const recordWorker = (phase, extra = {}) => writeHostMainWorker(configPath, runId, phase, extra);
  await recordWorker('running');
  let heartbeatWrite = Promise.resolve();
  const heartbeat = setInterval(() => { heartbeatWrite = heartbeatWrite.then(() => recordWorker('running')).catch(error => process.stderr.write(`Host Main heartbeat failed: ${error.stack ?? error}\n`)); }, heartbeatMs);
  let outcome, failure, authorityStop, authorityWatch;
  try {
    await hostMainManager.launchRun({ runtime, drive, runId, controlToken: launch.control_token, owner: launch.owner });
    authorityWatch = watchHostMainAuthority({ runtime, runId, controlToken: launch.control_token, owner: launch.owner,
      stopRun: id => stopOwnedSessions(service,id) });
    process.send({ type: 'ready', run_id: runId });
    process.disconnect();
    const execution = hostMainManager.wait(runId).then(value => ({ kind: 'execution', value }));
    const authority = authorityWatch.done.then(value => ({ kind: 'authority', value }));
    const first = await Promise.race([execution, authority]);
    if (first.kind === 'authority') authorityStop = first.value;
    outcome = first.kind === 'execution' ? first.value : await execution.then(value => value.value);
  } catch (error) { failure = error; }
  finally {
    if (authorityWatch) {
      try { authorityStop ??= await authorityWatch.close(); }
      catch (error) { failure = failure ? new AggregateError([failure, error], 'Host Main execution and authority watch failed') : error; }
    }
    clearInterval(heartbeat);
    await heartbeatWrite;
  }
  if (failure) {
    await recordWorker('failed', { error: { code: failure.code ?? 'HOST_MAIN_WORKER_FAILED', message: failure.message } });
    throw failure;
  }
  const terminal = buildHostMainWorkerTerminal(outcome, authorityStop);
  await recordWorker(terminal.phase, terminal.record);
  if (terminal.exitCode !== 0) {
    process.stderr.write(`Host Main worker failed for Run ${runId}: ${JSON.stringify(outcome.error)}\n`);
    process.exitCode = terminal.exitCode;
  }
}

// Cancellation in a different service instance cannot access the detached
// manager. Its durable terminal receipt is the cross-process stop evidence.
export async function waitForDetachedHostMainStop(configPath, runId, { timeoutMs = 30_000, healthMs = 1000 } = {}) {
  const initial = await readHostMainWorker(configPath, runId);
  if (!initial) return null; // This Run has no detached Host Main owner.
  const pid = initial.pid;
  return new Promise((resolveWait, rejectWait) => {
    let watcher, timeout, health, checking = false, pending = false, settled = false;
    const cleanup = () => { watcher?.close(); clearTimeout(timeout); clearInterval(health); };
    const finish = (value, error) => { if (settled) return; settled = true; cleanup(); error ? rejectWait(error) : resolveWait(value); };
    const check = async () => {
      pending = true; if (checking || settled) return; checking = true;
      try {
        while (pending && !settled) {
          pending = false;
          const record = await readHostMainWorker(configPath, runId);
          if (!record || record.pid !== pid) throw workerError('HOST_MAIN_WORKER_IDENTITY', 'Detached Host Main stop changed process identity before confirmation');
          if (['failed', 'stale', 'audit_or_cleanup_failed'].includes(record.phase))
            throw workerError(record.error?.code ?? 'HOST_MAIN_WORKER_STOP_FAILED', record.error?.message ?? 'Detached Host Main did not confirm cleanup');
          if (['cancelled', 'stopped'].includes(record.phase) && record.termination?.confirmed !== true)
            throw workerError('HOST_MAIN_WORKER_STOP_UNCONFIRMED', 'Detached Host Main terminal record lacks confirmed local cleanup');
          if (['succeeded', 'attention', 'awaiting_human_acceptance', 'cancelled', 'stopped'].includes(record.phase)) { finish(record); return; }
          if (!['running', 'starting'].includes(record.phase))
            throw workerError('HOST_MAIN_WORKER_PHASE', `Detached Host Main reported an unknown phase: ${String(record.phase)}`);
        }
      } catch (error) { finish(null, error); }
      finally { checking = false; }
    };
    try {
      watcher = watch(dirname(workerStatePath(configPath, runId)), (_event, name) => {
        if (!name || String(name) === 'host-main-worker.json') void check();
      });
      watcher.on('error', error => finish(null, error));
      health = setInterval(() => void check(), healthMs);
      timeout = setTimeout(() => finish(null, workerError('HOST_MAIN_WORKER_STOP_TIMEOUT', 'Detached Host Main did not confirm session closure after Run cancellation')), timeoutMs);
      void check();
    } catch (error) { finish(null, error); }
  });
}

if (process.argv[1] && resolve(process.argv[1]) === workerFile) {
  workerMain().catch(async error => {
    try { process.send?.({ type: 'error', code: error.code ?? 'HOST_MAIN_WORKER_FAILED', message: error.message }); } catch {}
    process.stderr.write(`Host Main worker startup failed: ${error.stack ?? error}\n`);
    process.exitCode = 1;
  });
}
