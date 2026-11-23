// Purpose: P3-2 — lifecycle of the engine (the local proxy): one instance per machine, `ensure` starts it in the
// background when it is not running, and it exits by itself once no Codex process is left (v0.11: and no plugin service
// of any platform checks in).
// v0.1-3 — an engine reports which code it runs (build and version). After a plugin update, the new plugin's `ensure`
// asks the older engine still running to retire: it stops listening at once, finishes what is in flight, then exits,
// and an engine of the new code takes the port.
// Input: the port; the plugin's own source folder; process lists from `tasklist` on Windows and `ps` on macOS and
// Linux. Output: health checks, a detached engine process.

import { execFile, spawn } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdirSync, readdirSync, readFileSync, statSync, unlinkSync, writeFileSync } from "node:fs";
import net from "node:net";
import { tmpdir } from "node:os";
import { dirname, join, posix } from "node:path";
import { fileURLToPath } from "node:url";
import { dataDir, proxyLogDirOf } from "./core/paths.ts";

export const ENGINE_SERVICE = "codex-attachment-manager";
export const DEFAULT_PORT = 17891;
const here = dirname(fileURLToPath(import.meta.url));

// build and version are missing on engines from before v0.1-3.
export type Health = { ok: true; service: string; pid: number; startedAt: string; port: number; build?: string | null; version?: string | null; routingVersion?: number; routingPort?: number };
// v0.12: "busy", an engine holds the port but did not answer in time; it is left alone (see probeEngine).
export type EngineState = "running" | "started" | "replaced" | "failed" | "busy";
export type EngineBindFailure = { port: number; host: string; code: string };

export function isEngineHealth(value: unknown): value is Health {
  const health = value as Partial<Health> | null;
  return !!health && health.ok === true && health.service === ENGINE_SERVICE && typeof health.pid === "number";
}

// Loopback only, and never through a system proxy: plain http.get on 127.0.0.1. v0.11: `client`, the platform whose
// plugin service is asking (ensureEngine): the engine stays while such checks keep coming (watchForClients).
export async function engineHealth(port = DEFAULT_PORT, timeoutMs = 800, client?: string): Promise<Health | null> {
  try {
    const response = await fetch(`http://127.0.0.1:${port}/__cam/health`, { signal: AbortSignal.timeout(timeoutMs), ...(client ? { headers: { "x-cam-client": client } } : {}) });
    const body = await response.json();
    return isEngineHealth(body) ? body : null;
  } catch {
    return null;
  }
}

// v0.12: what answers on the port. A health check that times out does not prove the engine is gone: one busy for a
// second (a large request being rewritten, a machine under load, or the asking process itself busy) answers late.
// Starting another engine then only fails to bind (2026-11-22: about 1,800 such starts in a month, 574 of them ending
// "port unavailable", several at once each time). "busy": the port takes connections (the system accepts them even
// while the engine's own work holds it up) but no answer came in time, or the engine is still starting; "other":
// something else answers there; "free": nothing listens.
export type Probe = { kind: "engine"; health: Health } | { kind: "busy" } | { kind: "other" } | { kind: "free" };
export async function probeEngine(port = DEFAULT_PORT, timeoutMs = 800, client?: string): Promise<Probe> {
  try {
    const response = await fetch(`http://127.0.0.1:${port}/__cam/health`, { signal: AbortSignal.timeout(timeoutMs), ...(client ? { headers: { "x-cam-client": client } } : {}) });
    // An engine answers 503 until both its ports are bound.
    if (response.status === 503) return { kind: "busy" };
    const body = await response.json().catch(() => null);
    return isEngineHealth(body) ? { kind: "engine", health: body } : { kind: "other" };
  } catch {
    return (await portOpen(port, 300)) ? { kind: "busy" } : { kind: "free" };
  }
}

export function portOpen(port: number, timeoutMs = 300): Promise<boolean> {
  return new Promise((resolve) => {
    const socket = net.connect({ host: "127.0.0.1", port });
    const done = (open: boolean) => { clearTimeout(timer); socket.destroy(); resolve(open); };
    const timer = setTimeout(() => done(false), timeoutMs);
    socket.once("connect", () => done(true));
    socket.once("error", () => done(false));
  });
}

// Which code a runtime folder holds: a hash of its .ts files, subfolders included (v0.11), line endings normalised (a
// copy made from a Windows checkout has CRLF). A flat folder hashes as before. null when the folder is gone, e.g. a
// plugin version Codex has removed.
export function buildOf(dir = here): string | null {
  try {
    const hash = createHash("sha256");
    const names = readdirSync(dir, { recursive: true, encoding: "utf8" }).map((name) => name.replaceAll("\\", "/"));
    for (const name of names.filter((file) => file.endsWith(".ts")).sort()) {
      hash.update(`${name}\0${readFileSync(join(dir, name), "utf8").replaceAll("\r\n", "\n")}\0`);
    }
    return hash.digest("hex").slice(0, 12);
  } catch {
    return null;
  }
}

// The plugin's version, from the manifest next to the runtime folder.
export function versionOf(dir = here): string | null {
  try {
    return JSON.parse(readFileSync(join(dir, "..", ".codex-plugin", "plugin.json"), "utf8")).version ?? null;
  } catch {
    return null;
  }
}

// x.y.z order; anything after the numbers (a pre-release tag) is ignored.
export function compareVersions(a: string, b: string): number {
  const parts = (version: string) => version.split(/[^0-9.]/)[0].split(".").map((part) => Number(part) || 0);
  const [x, y] = [parts(a), parts(b)];
  for (let i = 0; i < Math.max(x.length, y.length); i++) if ((x[i] ?? 0) !== (y[i] ?? 0)) return (x[i] ?? 0) - (y[i] ?? 0);
  return 0;
}

// Only different code of a newer version replaces a running engine on its own; the same version with other code only
// when installing (`force`, cam install). A plugin server left over from before an update either finds its folder
// replaced (then it reads the new code, the same as the new engine's) or gone (no build), or it is an older version:
// none of them pushes the new engine out.
// v0.4: Codex and Claude Code each keep their own copy of the plugin, and both start this engine. Two copies of the
// same version with different code (one updated, the other not yet) would otherwise push each other's engine out over
// and over; until both are the same, the engine already running stays.
export function shouldReplace(running: Health, own: { build: string | null; version: string | null }, force = false): boolean {
  if (!own.build || running.build === own.build) return false;
  const newer = compareVersions(own.version ?? "0.0.0", running.version ?? "0.0.0");
  return newer > 0 || (force && newer === 0) || !running.build;
}

// v0.12: Node's diagnostic report when the engine dies of something no handler can catch (out of memory, a native
// crash), so such an end leaves a trace: in <data>/proxy/reports, without the environment (it may hold keys) and
// network details. Only flags this Node knows, so an older one still starts the engine.
export function reportFlags(root = dataDir()): string[] {
  const known = process.allowedNodeEnvironmentFlags;
  const wanted = ["--report-on-fatalerror", "--report-compact", "--report-exclude-env", "--report-exclude-network"];
  if (!wanted.every((flag) => known.has(flag)) || !known.has("--report-directory")) return [];
  return [...wanted, `--report-directory=${join(proxyLogDirOf(root), "reports")}`];
}

// A Windows command line from arguments (the rules CommandLineToArgvW reads back).
export const windowsCommandLine = (args: string[]): string => args.map((arg) => (arg && !/[\s"]/.test(arg) ? arg : `"${arg.replace(/(\\*)"/g, "$1$1\\\"").replace(/(\\+)$/, "$1$1")}"`)).join(" ");

// A started engine: its process id when known, whether it has already failed to start, and why it could not bind.
type Started = { pid: number | null; failed: () => boolean; bindFailure: () => EngineBindFailure | undefined; release: () => void };

// Hidden, and its working folder is not the plugin's: Windows will not delete a folder a running process works in, and
// Codex replaces the plugin's folder on every update and removes it on uninstall.
// v0.12, Windows: started through WMI (Win32_Process.Create), so the engine is not in the job of the process that
// asked for it. Codex and Claude run each plugin service in a job that ends everything in it with the service, and the
// engine one service started ended with it, cutting the requests in flight of every task and session (2026-11-22: 238
// engines in a month ended that way or crashed, median life 4 minutes; the running one was in a job, its parent a
// Codex plugin service). Outside the job, the engine ends as designed: when no Codex or Claude Code is left
// (watchForClients). Where WMI cannot start it (no PowerShell, a security policy), it starts as before.
// CAM_ENGINE_START=child: always as before. Elsewhere: detached, so it outlives whoever asked for it.
async function startEngine(port: number, extraArgs: string[] = [], dir = here): Promise<Started> {
  const args = [...reportFlags(), join(dir, "proxy.ts"), "--port", String(port), ...extraArgs];
  if (process.platform === "win32" && process.env.CAM_ENGINE_START !== "child" && !wmiFailed) {
    const pid = await startOutsideJob([process.execPath, ...args], tmpdir());
    if (pid !== null) {
      const alive = () => { try { process.kill(pid, 0); return true; } catch { return false; } };
      return { pid, failed: () => !alive(), bindFailure: () => readStartFailure(pid), release: () => {} };
    }
  }
  const child = spawn(process.execPath, args, { cwd: tmpdir(), detached: true, stdio: ["ignore", "ignore", "ignore", "ipc"], windowsHide: true });
  child.unref();
  let spawnFailed = false;
  let bindFailure: EngineBindFailure | undefined;
  child.on("error", () => { spawnFailed = true; });
  child.on("message", (message) => { bindFailure = message as EngineBindFailure; });
  return { pid: child.pid ?? null, failed: () => spawnFailed, bindFailure: () => bindFailure, release: () => { if (child.connected) child.disconnect(); } };
}

// Set once a WMI start did not give an engine (or could not run): this process starts engines the old way from then on.
let wmiFailed = false;
// The longest a start through WMI may take. Usually about a second, but PowerShell's first call on a freshly started
// machine can take several (Windows CI, 2026-11-22).
const WMI_START_MS = 10_000;
// v0.12: how an engine was started, for the plugin service's log: through WMI or as a child; how long the WMI start took,
// and why it gave no engine when it did not (PowerShell would not start, it took too long, Win32_Process.Create's
// return value, or the first line PowerShell wrote on its error output).
export type StartNote = { via: "wmi" | "child"; wmiMs?: number; wmiError?: string };
let lastWmiStart: { ms: number; error?: string } | null = null;

// The new process gets this process's environment explicitly (WMI would give it the user's default one), on stdin, not
// on a command line. Resolves with its process id, or null when it could not be started this way.
export function startOutsideJob(commandLine: string[], cwd: string, env: NodeJS.ProcessEnv = process.env): Promise<number | null> {
  const quote = (text: string) => `'${text.replaceAll("'", "''")}'`;
  const vars = Object.entries(env).filter(([, value]) => value !== undefined).map(([name, value]) => `${name}=${value}`);
  const script = [
    "$ErrorActionPreference = 'Stop'",
    `$vars = ConvertFrom-Json ${quote(JSON.stringify(vars))}`,
    "$startup = New-CimInstance -ClassName Win32_ProcessStartup -ClientOnly -Property @{ ShowWindow = [uint16]0; EnvironmentVariables = [string[]]$vars }",
    `$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{ CommandLine = ${quote(windowsCommandLine(commandLine))}; CurrentDirectory = ${quote(cwd)}; ProcessStartupInformation = $startup }`,
    "Write-Output \"started $($r.ReturnValue) $($r.ProcessId)\"",
    "",
  ].join("\n");
  return new Promise((resolve) => {
    const begun = Date.now();
    let out = "";
    let err = "";
    let settled = false;
    const done = (pid: number | null, error = "no process id") => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      if (pid === null) wmiFailed = true;
      lastWmiStart = { ms: Date.now() - begun, ...(pid === null ? { error } : {}) };
      resolve(pid);
    };
    const shell = spawn("powershell.exe", ["-NoLogo", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", "-"], { windowsHide: true, stdio: ["pipe", "pipe", "pipe"] });
    const timer = setTimeout(() => { shell.kill(); done(null, "timed out"); }, WMI_START_MS);
    shell.on("error", (error) => done(null, `powershell: ${error.message}`));
    shell.stdout.on("data", (chunk) => { out += chunk; });
    shell.stderr.on("data", (chunk) => { if (err.length < 4000) err += chunk; });
    shell.on("close", () => {
      const match = /started (\d+) (\d+)/.exec(out);
      if (match && match[1] === "0" && Number(match[2]) > 0) { done(Number(match[2])); return; }
      const said = (text: string) => text.split(/\r?\n/).map((line) => line.trim()).find(Boolean);
      done(null, (match ? `Win32_Process.Create returned ${match[1]}` : said(err) ?? said(out) ?? "no output").slice(0, 300));
    });
    shell.stdin.on("error", () => {});
    shell.stdin.end(script);
  });
}

// v0.12: an engine started through WMI has no channel back; when it cannot bind its port it leaves the reason here
// (proxy.ts), for `cam install` to say.
export const startFailureFile = (root = dataDir()) => join(root, "state", "engine-start-failure.json");
function readStartFailure(pid: number): EngineBindFailure | undefined {
  try {
    const failure = JSON.parse(readFileSync(startFailureFile(), "utf8"));
    return failure?.pid === pid ? { port: failure.port, host: failure.host, code: failure.code } : undefined;
  } catch { return undefined; }
}

// v0.12: one engine start at a time across processes (Codex starts several plugin services at once, and a WMI start
// takes a second): the others wait for the engine the first one starts. A lock older than 20 s is left over.
function takeStartLock(): (() => void) | null {
  const file = join(dataDir(), "state", "engine-start.lock");
  try {
    mkdirSync(dirname(file), { recursive: true });
    writeFileSync(file, String(process.pid), { flag: "wx" });
    return () => { try { unlinkSync(file); } catch { /* gone */ } };
  } catch {
    try {
      if (Date.now() - statSync(file).mtimeMs > 20_000) { unlinkSync(file); writeFileSync(file, String(process.pid), { flag: "wx" }); return () => { try { unlinkSync(file); } catch { /* gone */ } }; }
    } catch { /* another process took it */ }
    return null;
  }
}

// An engine from v0.1-3 on stops listening at once and exits after its open requests; an older one does not know the
// request, so it is stopped (Codex retries what was cut off).
export async function retireEngine(port: number, running: Health, by: string | null): Promise<void> {
  if (running.build) {
    try {
      const response = await fetch(`http://127.0.0.1:${port}/__cam/retire`, { method: "POST", headers: { "x-cam-build": by ?? "" }, signal: AbortSignal.timeout(2000) });
      if ((await response.json())?.retiring === true) return;
    } catch { /* stop it instead */ }
  }
  try { process.kill(running.pid); } catch { /* already gone */ }
}

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));
// The build of each runtime folder, read again once for every different build a running engine reports.
const knownBuilds = new Map<string, { build: string | null; against: string | null | undefined }>();

export async function ensureEngine(options: { port?: number; waitMs?: number; extraArgs?: string[]; dir?: string; force?: boolean; client?: string; patienceMs?: number } = {}): Promise<{ state: EngineState; health: Health | null; replaced?: Health; bindFailure?: EngineBindFailure; start?: StartNote }> {
  const port = options.port ?? DEFAULT_PORT;
  const dir = options.dir ?? here;
  let probe = await probeEngine(port, 800, options.client);
  // v0.12: no answer in time, but something holds the port: asked again with more patience; still busy, it is left
  // alone this round (see probeEngine).
  if (probe.kind === "busy") probe = await probeEngine(port, options.patienceMs ?? 5000, options.client);
  if (probe.kind === "busy") return { state: "busy", health: null };
  const existing = probe.kind === "engine" ? probe.health : null;
  let replaced: Health | undefined;
  if (existing) {
    const known = knownBuilds.get(dir);
    if (!known || (known.build !== existing.build && known.against !== existing.build)) knownBuilds.set(dir, { build: buildOf(dir), against: existing.build });
    const build = knownBuilds.get(dir)!.build;
    if (build === existing.build || !shouldReplace(existing, { build, version: versionOf(dir) }, options.force)) return { state: "running", health: existing };
    await retireEngine(port, existing, build);
    // A retiring engine closes its listener at once; a stopped one lets go of the port as it exits.
    for (let i = 0; i < 20 && (await engineHealth(port, 300))?.pid === existing.pid; i++) await sleep(150);
    replaced = existing;
  }
  const waitMs = options.waitMs ?? 8000;
  // v0.12: another process is starting one right now: wait for it instead of starting a second. Its start through WMI
  // can take a while before the engine even runs, so the wait allows for that too.
  const unlock = takeStartLock();
  if (!unlock) {
    const deadline = Date.now() + WMI_START_MS + waitMs;
    while (Date.now() < deadline) {
      await sleep(250);
      const health = await engineHealth(port);
      if (health && health.pid !== replaced?.pid) return { state: "running", health, replaced };
    }
    return { state: "failed", health: null, replaced };
  }
  let started: Started | null = null;
  lastWmiStart = null;
  try {
    started = await startEngine(port, options.extraArgs, dir);
    // v0.12: the wait for the engine counts from here, once it is started. Counted from before, a slow start through
    // WMI used up most of it, and the start was reported as failed while the engine was still coming up (Windows CI,
    // 2026-11-22); `cam install` reports that as an engine that is not ready.
    const deadline = Date.now() + waitMs;
    let viaWmi = process.platform === "win32" && started.pid !== null && !wmiFailed && process.env.CAM_ENGINE_START !== "child";
    const note = (): StartNote => ({ via: viaWmi ? "wmi" : "child", ...(lastWmiStart ? { wmiMs: lastWmiStart.ms, ...(lastWmiStart.error ? { wmiError: lastWmiStart.error } : {}) } : {}) });
    while (Date.now() < deadline) {
      await sleep(150);
      const health = await engineHealth(port);
      if (health && health.pid !== replaced?.pid) return { state: replaced ? "replaced" : "started", health, replaced, start: note() };
      if (started.bindFailure() || started.failed()) {
        // An engine WMI started that died at once (a policy ending it): this process starts them as before from now on.
        if (viaWmi && !started.bindFailure()) {
          wmiFailed = true;
          viaWmi = false;
          lastWmiStart = { ms: lastWmiStart?.ms ?? 0, error: "the engine it started ended at once" };
          started.release();
          started = await startEngine(port, options.extraArgs, dir);
          continue;
        }
        break;
      }
    }
    return { state: "failed", health: null, replaced, bindFailure: started.bindFailure(), start: note() };
  } finally {
    started?.release();
    unlock();
  }
}

// `tasklist /FO CSV /NH` prints one quoted CSV row per process, or an INFO line when nothing matches.
export function countCodexProcesses(tasklistCsv: string): number {
  return tasklistCsv.split(/\r?\n/).filter((line) => /^"codex\.exe",/i.test(line.trim())).length;
}

// v0.1: `ps -A -o comm=` prints one executable per line: the bare name on Linux, the full path on macOS. Codex's
// command line and the app-server inside the desktop app are both named `codex`.
export function countCodexInPs(psOutput: string): number {
  return psOutput.split(/\r?\n/).filter((line) => posix.basename(line.trim()) === "codex").length;
}

// v0.4: Claude Code uses the engine too. Its command line and the desktop app are both `claude.exe` on Windows;
// `claude` (the command line) and `Claude` (the desktop app) on macOS and Linux.
export function countClaudeProcesses(tasklistCsv: string): number {
  return tasklistCsv.split(/\r?\n/).filter((line) => /^"claude\.exe",/i.test(line.trim())).length;
}

export function countClaudeInPs(psOutput: string): number {
  return psOutput.split(/\r?\n/).filter((line) => ["claude", "Claude"].includes(posix.basename(line.trim()))).length;
}

// The processes that may use the engine: Codex's and, since v0.4, Claude Code's.
export function listCodexProcesses(): Promise<number> {
  const windows = process.platform === "win32";
  const [file, args] = windows ? ["tasklist", ["/FO", "CSV", "/NH"]] : ["ps", ["-A", "-o", "comm="]];
  return new Promise((resolve) => {
    execFile(file, args, { windowsHide: true, maxBuffer: 16 * 1024 * 1024 }, (error, stdout) => {
      // If the check itself fails, assume Codex is still there rather than shutting down under it.
      resolve(error ? 1 : windows ? countCodexProcesses(stdout) + countClaudeProcesses(stdout) : countCodexInPs(stdout) + countClaudeInPs(stdout));
    });
  });
}

// v0.11: a plugin service of any platform checks the engine every few seconds while its platform runs (plugin-server.ts);
// one checked within this long counts as a client still there.
export const CLIENT_SEEN_MS = 60_000;

// Exit only after `misses` checks in a row found no Codex (v0.4: and no Claude Code; v0.11: and no plugin service of
// another platform checking in, `lastClient`), so a restart does not stop the engine.
export function watchForClients(onGone: () => void, options: { intervalMs?: number; misses?: number; count?: () => Promise<number>; lastClient?: () => number } = {}): () => void {
  const processes = options.count ?? listCodexProcesses;
  const lastClient = options.lastClient ?? (() => 0);
  const count = async () => (Date.now() - lastClient() < CLIENT_SEEN_MS ? 1 : await processes());
  const needed = options.misses ?? 2;
  let missed = 0;
  const timer = setInterval(async () => {
    missed = (await count()) > 0 ? 0 : missed + 1;
    if (missed >= needed) { clearInterval(timer); onGone(); }
  }, options.intervalMs ?? 15_000);
  timer.unref();
  return () => clearInterval(timer);
}
