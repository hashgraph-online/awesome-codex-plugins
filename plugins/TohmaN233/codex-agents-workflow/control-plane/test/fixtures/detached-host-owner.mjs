import { HostMainManager } from '../../lib/execution/host-main-manager.mjs';
import { watchHostMainAuthority, writeHostMainWorker } from '../../lib/execution/host-main-worker.mjs';

const [configPath, directory, runId, controlToken, owner] = process.argv.slice(2);
const writeRecord = (phase, extra = {}) => writeHostMainWorker(configPath, runId, phase, extra);
let releaseDrive;
const driveGate = new Promise(resolve => { releaseDrive = resolve; });
const runtime = { runs: { directory: () => directory }, quiesceFailedOrigin: async () => {} };
const manager = new HostMainManager({ configPath, getConfig: async () => ({}), qualify: async () => ({}) });
let interrupted = 0, closed = 0;
try {
  await manager.launchRun({ runtime, runId, controlToken, owner, drive: { advanceToMain: () => driveGate } });
  manager.entries.get(runId).session = { interrupt: async () => { interrupted++; }, close: async () => { closed++; } };
  const observer = watchHostMainAuthority({ runtime, runId, controlToken, owner,
    stopRun: async id => { releaseDrive({ status: 'running', stop_reason: 'fixture_release' }); await manager.stopRun(id); } });
  await writeRecord('running');
  process.stdout.write('ready\n');
  const stop = await observer.done;
  await manager.wait(runId);
  if (interrupted < 1 || closed < 1) throw new Error('The detached manager did not interrupt and close its session');
  await writeRecord(stop.reason === 'cancelled' ? 'cancelled' : 'stopped', { termination: { confirmed: true, reason: stop.reason, interrupted, closed } });
} catch (error) {
  await writeRecord('failed', { error: { code: error.code ?? 'DETACHED_FIXTURE_FAILED', message: error.message } });
  process.stderr.write(`${error.stack ?? error}\n`);
  process.exitCode = 1;
}
