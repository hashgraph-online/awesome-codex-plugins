import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { readFile, readlink, readdir } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import { noSymlinks, requireValue } from '../workflow-paths.mjs';

const exec = promisify(execFile);
export async function processIdentity(pid) {
  requireValue(Number.isSafeInteger(pid) && pid > 0, 'PROCESS_IDENTITY_PID', 'Process identity requires a positive PID');
  let executable; let started;
  if (process.platform === 'win32') {
    // Get-Process uses the OS process handle and creation time. It does not
    // require the WMI service or expose unrelated process command lines.
    const script = `$ErrorActionPreference = 'Stop'; try { $p = Get-Process -Id ${pid}; @{ executable = $p.Path; started = $p.StartTime.ToUniversalTime().Ticks.ToString() } | ConvertTo-Json -Compress } catch { if ($_.FullyQualifiedErrorId -like 'NoProcessFoundForGivenId*') { 'null' } else { throw } }`;
    const { stdout } = await exec(join(process.env.SystemRoot ?? 'C:\\Windows', 'System32', 'WindowsPowerShell', 'v1.0', 'powershell.exe'), ['-NoProfile', '-NonInteractive', '-Command', script], { windowsHide: true, timeout: 10000, maxBuffer: 65536 });
    const row = JSON.parse(stdout.trim()); if (row === null) return null;
    ({ executable, started } = row);
  } else if (process.platform === 'linux') {
    try {
      const stat = await readFile(`/proc/${pid}/stat`, 'utf8'); started = stat.slice(stat.lastIndexOf(')') + 2).split(' ')[19];
      executable = await readlink(`/proc/${pid}/exe`);
    } catch (error) { if (error.code === 'ENOENT' || error.code === 'ESRCH') return null; throw error; }
  } else {
    throw Object.assign(new Error('Process ownership inspection has not been qualified on this platform'), { code: 'PROCESS_IDENTITY_UNSUPPORTED' });
  }
  requireValue(typeof executable === 'string' && executable && typeof started === 'string' && started, 'PROCESS_IDENTITY_UNAVAILABLE', 'The operating system did not return complete process ownership evidence');
  return { pid, executable: resolve(executable), started };
}

export function sameProcess(expected, actual) {
  return actual && expected && expected.pid === actual.pid && expected.started === actual.started &&
    expected.executable === actual.executable;
}

// A PID alone never authorizes termination. The profile's original parent must
// be gone, and the directly spawned child must match its creation time/binary.
export async function inspectOrphanProfiles(parent) {
  await noSymlinks(parent); const results = [];
  for (const entry of await readdir(parent, { withFileTypes: true })) {
    if (!entry.name.startsWith('strict-node-')) continue;
    const home = join(parent, entry.name);
    try {
      requireValue(entry.isDirectory() && !entry.isSymbolicLink(), 'PROFILE_OWNER', 'Owned profile must be a real directory');
      await noSymlinks(join(home, 'owner.json')); const owner = JSON.parse(await readFile(join(home, 'owner.json'), 'utf8'));
      requireValue(owner.schema_version === 1 && /^[a-f0-9-]{36}$/.test(owner.token) && owner.parent_identity && owner.parent_pid === owner.parent_identity.pid, 'PROFILE_OWNER', 'Incomplete process ownership record');
      const parentIdentity = await processIdentity(owner.parent_pid);
      if (sameProcess(owner.parent_identity, parentIdentity)) { results.push({ home, status: 'active' }); continue; }
      let childIdentity = null;
      if (owner.child_pid) {
        childIdentity = await processIdentity(owner.child_pid);
        requireValue(!childIdentity || sameProcess(owner.child_identity, childIdentity), 'PROFILE_CHILD_IDENTITY_CHANGED', 'Child PID is alive but no longer has the recorded profile ownership');
      }
      results.push({ home, status: 'orphan', token: owner.token, child_identity: childIdentity });
    } catch (error) { results.push({ home, status: 'blocked', code: error.code ?? 'PROFILE_INSPECTION_FAILED', message: error.message }); }
  }
  return results;
}

export async function stopVerifiedOrphan(record) {
  requireValue(record.status === 'orphan', 'PROFILE_NOT_ORPHAN', 'Only a verified orphan can be stopped');
  if (!record.child_identity) return;
  const actual = await processIdentity(record.child_identity.pid);
  if (!actual) return;
  requireValue(sameProcess(record.child_identity, actual), 'PROFILE_CHILD_IDENTITY_CHANGED', 'Child identity changed before orphan termination');
  process.kill(actual.pid);
  const deadline = Date.now() + 5000;
  while (Date.now() < deadline) {
    let alive = true; try { process.kill(actual.pid, 0); } catch (error) { if (error.code === 'ESRCH') alive = false; else throw error; }
    if (!alive) return;
    await new Promise(resolve => setTimeout(resolve, 50));
  }
  throw Object.assign(new Error('Orphan child did not close; retain its profile'), { code: 'PROFILE_CHILD_ALIVE' });
}
