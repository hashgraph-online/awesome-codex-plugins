// Purpose: P3-2 — lifecycle of the engine (the local proxy): one instance per machine, `ensure` starts it in the
// background when it is not running, and it exits by itself once no Codex process is left.
// v0.1-3 — an engine reports which code it runs (build and version). After a plugin update, the new plugin's `ensure`
// asks the older engine still running to retire: it stops listening at once, finishes what is in flight, then exits,
// and an engine of the new code takes the port.
// Input: the port; the plugin's own source folder; process lists from `tasklist` on Windows and `ps` on macOS and
// Linux. Output: health checks, a detached engine process.

import { execFile, spawn } from "node:child_process";
import { createHash } from "node:crypto";
import { readdirSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, posix } from "node:path";
import { fileURLToPath } from "node:url";

export const ENGINE_SERVICE = "codex-attachment-manager";
export const DEFAULT_PORT = 17891;
const here = dirname(fileURLToPath(import.meta.url));

// build and version are missing on engines from before v0.1-3.
export type Health = { ok: true; service: string; pid: number; startedAt: string; port: number; build?: string | null; version?: string | null };
export type EngineState = "running" | "started" | "replaced" | "failed";

export function isEngineHealth(value: unknown): value is Health {
  const health = value as Partial<Health> | null;
  return !!health && health.ok === true && health.service === ENGINE_SERVICE && typeof health.pid === "number";
}

// Loopback only, and never through a system proxy: plain http.get on 127.0.0.1.
export async function engineHealth(port = DEFAULT_PORT, timeoutMs = 800): Promise<Health | null> {
  try {
    const response = await fetch(`http://127.0.0.1:${port}/__cam/health`, { signal: AbortSignal.timeout(timeoutMs) });
    const body = await response.json();
    return isEngineHealth(body) ? body : null;
  } catch {
    return null;
  }
}

// Which code a runtime folder holds: a hash of its .ts files, line endings normalised (a copy made from a Windows
// checkout has CRLF). null when the folder is gone, e.g. a plugin version Codex has removed.
export function buildOf(dir = here): string | null {
  try {
    const hash = createHash("sha256");
    for (const name of readdirSync(dir).filter((file) => file.endsWith(".ts")).sort()) {
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

// Only different code of the same or a newer version replaces a running engine. A plugin server left over from before
// an update either finds its folder replaced (then it reads the new code, the same as the new engine's) or gone (no
// build), or it is an older version: none of them pushes the new engine out.
export function shouldReplace(running: Health, own: { build: string | null; version: string | null }): boolean {
  if (!own.build || running.build === own.build) return false;
  return compareVersions(own.version ?? "0.0.0", running.version ?? "0.0.0") >= 0;
}

// Detached and hidden, so it outlives whoever asked for it (a plugin server instance, the CLI). Its working folder is
// not the plugin's: Windows will not delete a folder a running process works in, and Codex replaces the plugin's
// folder on every update and removes it on uninstall.
export function spawnEngine(port = DEFAULT_PORT, extraArgs: string[] = [], dir = here): number | undefined {
  const child = spawn(process.execPath, [join(dir, "proxy.ts"), "--port", String(port), ...extraArgs], { cwd: tmpdir(), detached: true, stdio: "ignore", windowsHide: true });
  child.unref();
  return child.pid;
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

export async function ensureEngine(options: { port?: number; waitMs?: number; extraArgs?: string[]; dir?: string } = {}): Promise<{ state: EngineState; health: Health | null; replaced?: Health }> {
  const port = options.port ?? DEFAULT_PORT;
  const dir = options.dir ?? here;
  const existing = await engineHealth(port);
  let replaced: Health | undefined;
  if (existing) {
    const known = knownBuilds.get(dir);
    if (!known || (known.build !== existing.build && known.against !== existing.build)) knownBuilds.set(dir, { build: buildOf(dir), against: existing.build });
    const build = knownBuilds.get(dir)!.build;
    if (build === existing.build || !shouldReplace(existing, { build, version: versionOf(dir) })) return { state: "running", health: existing };
    await retireEngine(port, existing, build);
    // A retiring engine closes its listener at once; a stopped one lets go of the port as it exits.
    for (let i = 0; i < 20 && (await engineHealth(port, 300))?.pid === existing.pid; i++) await sleep(150);
    replaced = existing;
  }
  spawnEngine(port, options.extraArgs, dir);
  const deadline = Date.now() + (options.waitMs ?? 8000);
  while (Date.now() < deadline) {
    await sleep(150);
    const health = await engineHealth(port);
    if (health && health.pid !== replaced?.pid) return { state: replaced ? "replaced" : "started", health, replaced };
  }
  return { state: "failed", health: null, replaced };
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

export function listCodexProcesses(): Promise<number> {
  const windows = process.platform === "win32";
  const [file, args] = windows ? ["tasklist", ["/FI", "IMAGENAME eq codex.exe", "/FO", "CSV", "/NH"]] : ["ps", ["-A", "-o", "comm="]];
  return new Promise((resolve) => {
    execFile(file, args, { windowsHide: true }, (error, stdout) => {
      // If the check itself fails, assume Codex is still there rather than shutting down under it.
      resolve(error ? 1 : windows ? countCodexProcesses(stdout) : countCodexInPs(stdout));
    });
  });
}

// Exit only after `misses` checks in a row found no Codex, so a Codex restart does not stop the engine.
export function watchForCodex(onGone: () => void, options: { intervalMs?: number; misses?: number; count?: () => Promise<number> } = {}): () => void {
  const count = options.count ?? listCodexProcesses;
  const needed = options.misses ?? 2;
  let missed = 0;
  const timer = setInterval(async () => {
    missed = (await count()) > 0 ? 0 : missed + 1;
    if (missed >= needed) { clearInterval(timer); onGone(); }
  }, options.intervalMs ?? 15_000);
  timer.unref();
  return () => clearInterval(timer);
}
