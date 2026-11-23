// Purpose: v0.13 — the plugin keeps itself up to date (docs/design.md section 11). About once a day a plugin service asks
// GitHub which release is the latest, the "pointer": the repository's latest published release. When the version the
// platform has installed differs from it, the service installs that release with the platform's own command line:
// Codex's `codex plugin` (adapters/codex/update.ts), Claude Code's `claude plugin` (adapters/claude/update.ts). Nothing
// running is replaced: the new version takes effect when Codex restarts or a new Claude Code session starts. Following
// the pointer both ways is what makes a rollback possible: marking an earlier release as the latest takes everyone back
// to it. An install from a local folder (a developer's checkout) is left alone. Off with the panel's switch (saved
// here, for both platforms) or CAM_AUTO_UPDATE=0.
// The check sends nothing about the user: one request for a public page, through the same outbound proxy the engine
// uses, without cookies.
// Input: the platform's install (through its command line), GitHub's answer. Output: the platform's plugin cache,
// through its command line; state/update.json in the data folder.

import { spawn, type ChildProcess } from "node:child_process";
import { mkdirSync, readFileSync, renameSync, statSync, unlinkSync, utimesSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { connectUpstream, outboundProxy, readSystemProxy } from "./engine/transport.ts";
import { dataDir } from "./paths.ts";

export const REPO = "chipfighter/context-attachment-manager";
// The repository's name before 2026-10-11 (GitHub redirects it): marketplaces added then still name it.
const OLD_REPO = "chipfighter/codex-attachment-manager";
export const releasePage = (version: string) => `https://github.com/${REPO}/releases/tag/v${version}`;

export type Host = "codex" | "claude";
export type Release = { tag: string; version: string };
// What a platform has installed, and whether it may be updated here: only an install from this repository on GitHub.
export type Installed = { eligible: true; version: string } | { eligible: false; reason: string; version?: string };
export interface Platform {
  host: Host;
  inspect(): Promise<Installed>;
  // Installs the release; resolves with the version installed afterwards (the same one unless something held it back).
  apply(release: Release): Promise<string>;
}
export type HostStatus = {
  checkedAt: string;
  result: "up-to-date" | "updated" | "skipped" | "failed" | "waiting";
  latest?: string; installed?: string; from?: string; to?: string; updatedAt?: string; reason?: string;
};
export type UpdateState = {
  // The panel's switch, for both platforms; on unless turned off.
  auto?: boolean;
  hosts?: Partial<Record<Host, HostStatus>>;
  // Per platform, the running version whose "updated" note the user has seen (panel).
  seen?: Partial<Record<Host, string>>;
};

// owner/name from what a platform records as a marketplace's source: an owner/name, an HTTPS or SSH Git address.
export function isOurRepo(source: unknown): boolean {
  if (typeof source !== "string") return false;
  const name = source.trim().toLowerCase().replace(/^git@github\.com:/, "").replace(/^(?:https?:\/\/)?(?:www\.)?github\.com\//, "").replace(/\.git$/, "").replace(/\/+$/, "");
  return name === REPO || name === OLD_REPO;
}

// "0.12.0", "v0.12.0" → [0, 12, 0]; anything else (a pre-release, a dev build) → null.
export function parseVersion(text: unknown): [number, number, number] | null {
  const match = typeof text === "string" ? /^v?(\d+)\.(\d+)\.(\d+)$/.exec(text.trim()) : null;
  return match ? [Number(match[1]), Number(match[2]), Number(match[3])] : null;
}
export function compareVersions(a: string, b: string): number {
  const [x, y] = [parseVersion(a), parseVersion(b)];
  if (!x || !y) return 0;
  for (let i = 0; i < 3; i++) if (x[i] !== y[i]) return x[i] - y[i];
  return 0;
}

// GitHub answers /releases/latest with a redirect to the latest release's page.
export function releaseFromLocation(location: string | undefined): Release | null {
  const match = location ? /\/releases\/tag\/(v\d+\.\d+\.\d+)\/?$/.exec(location.trim()) : null;
  return match ? { tag: match[1], version: match[1].slice(1) } : null;
}

// One HEAD request through the outbound proxy (the engine's way out, engine/transport.ts). host/port/secure: for tests.
export async function latestRelease(options: { host?: string; port?: number; secure?: boolean; timeoutMs?: number; env?: NodeJS.ProcessEnv } = {}): Promise<Release> {
  const env = options.env ?? process.env;
  // Tests and a pinned machine: the release to follow, without asking GitHub.
  if (env.CAM_UPDATE_LATEST) {
    const pinned = parseVersion(env.CAM_UPDATE_LATEST);
    if (!pinned) throw new Error(`CAM_UPDATE_LATEST is not a version: ${env.CAM_UPDATE_LATEST}`);
    return { tag: `v${pinned.join(".")}`, version: pinned.join(".") };
  }
  const host = options.host ?? "github.com";
  const secure = options.secure ?? true;
  const timeoutMs = options.timeoutMs ?? 20_000;
  const via = options.host ? null : outboundProxy(env, readSystemProxy, host);
  const socket = await connectUpstream(via, host, AbortSignal.timeout(timeoutMs), options.port ?? (secure ? 443 : 80), secure, ["http/1.1"], timeoutMs);
  return new Promise((resolve, reject) => {
    let head = "";
    let settled = false;
    const timer = setTimeout(() => finish(new Error("no answer from GitHub")), timeoutMs);
    const finish = (error: Error | null, release?: Release) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      socket.destroy();
      if (error) reject(error); else resolve(release!);
    };
    socket.on("error", (error) => finish(error));
    socket.on("close", () => finish(new Error("GitHub closed the connection")));
    socket.on("data", (chunk: Buffer) => {
      head += chunk.toString("latin1");
      const end = head.indexOf("\r\n\r\n");
      if (end < 0 && head.length < 64 * 1024) return;
      const lines = head.slice(0, end < 0 ? undefined : end).split("\r\n");
      const status = Number(lines[0]?.split(" ")[1]);
      const location = lines.find((line) => /^location\s*:/i.test(line))?.replace(/^location\s*:\s*/i, "");
      const release = status >= 300 && status < 400 ? releaseFromLocation(location) : null;
      finish(release ? null : new Error(`GitHub answered ${status || "nothing"}${location ? ` → ${location}` : ""}`), release ?? undefined);
    });
    socket.write(`HEAD /${REPO}/releases/latest HTTP/1.1\r\nHost: ${host}\r\nUser-Agent: context-attachment-manager-update\r\nAccept: text/html\r\nConnection: close\r\n\r\n`);
  });
}

// ---- the state file, shared by every plugin service on the machine ----
export const updateFile = (root = dataDir()) => join(root, "state", "update.json");
export function readUpdateState(root = dataDir()): UpdateState {
  try {
    const json = JSON.parse(readFileSync(updateFile(root), "utf8"));
    return json && typeof json === "object" ? json : {};
  } catch {
    return {};
  }
}
// Best effort, never throws: a state that cannot be written only means the next check comes sooner.
export function changeUpdateState(change: (state: UpdateState) => UpdateState, root = dataDir()): UpdateState {
  const next = change(readUpdateState(root));
  try {
    const file = updateFile(root);
    mkdirSync(dirname(file), { recursive: true });
    writeFileSync(`${file}.${process.pid}.tmp`, JSON.stringify(next, null, 2));
    renameSync(`${file}.${process.pid}.tmp`, file);
  } catch { /* see above */ }
  return next;
}
export const autoUpdateOn = (state: UpdateState, env: NodeJS.ProcessEnv = process.env) => env.CAM_AUTO_UPDATE !== "0" && state.auto !== false;

// About once a day; sooner again after a check that failed, or found the new release not installable yet (the pointer
// moved before the platform's own copy of the repository did).
export const DAY_MS = 20 * 60 * 60_000;
export const RETRY_MS = 6 * 60 * 60_000;
export function due(status: HostStatus | undefined, now: number): boolean {
  if (!status) return true;
  const at = Date.parse(status.checkedAt);
  if (!Number.isFinite(at) || at > now) return true;
  return now - at >= (status.result === "failed" || status.result === "waiting" ? RETRY_MS : DAY_MS);
}

// One check at a time on the machine: Codex starts several plugin services at once, Claude Code one per session.
// The holder touches the lock every minute while it works: a check may take a while (Codex's `plugin list` took 114 s on
// a machine with several git marketplaces, 2026-11-23, and an update runs several commands). One not touched for 15
// minutes is left over from a service that ended mid-way.
export const LOCK_STALE_MS = 15 * 60_000;
export function takeLock(root: string, refreshMs = 60_000): (() => void) | null {
  const file = join(root, "state", "update.lock");
  const take = () => {
    writeFileSync(file, String(process.pid), { flag: "wx" });
    const keep = setInterval(() => { try { const now = new Date(); utimesSync(file, now, now); } catch { /* gone */ } }, refreshMs);
    keep.unref?.();
    return () => { clearInterval(keep); try { unlinkSync(file); } catch { /* gone */ } };
  };
  try {
    mkdirSync(dirname(file), { recursive: true });
    return take();
  } catch {
    try {
      if (Date.now() - statSync(file).mtimeMs > LOCK_STALE_MS) { unlinkSync(file); return take(); }
    } catch { /* another service took it */ }
    return null;
  }
}

export type UpdateOutcome = { ran: false; why: "off" | "not-due" | "busy" } | { ran: true; status: HostStatus };
export async function updateOnce(platform: Platform, options: { root?: string; env?: NodeJS.ProcessEnv; now?: () => number; latest?: () => Promise<Release>; force?: boolean } = {}): Promise<UpdateOutcome> {
  const root = options.root ?? dataDir();
  const env = options.env ?? process.env;
  const now = options.now ?? Date.now;
  const state = readUpdateState(root);
  if (!autoUpdateOn(state, env)) return { ran: false, why: "off" };
  if (!options.force && !due(state.hosts?.[platform.host], now())) return { ran: false, why: "not-due" };
  const unlock = takeLock(root);
  if (!unlock) return { ran: false, why: "busy" };
  let status: HostStatus;
  try {
    status = await check(platform, options.latest ?? (() => latestRelease({ env })), now);
  } finally {
    unlock();
  }
  changeUpdateState((current) => ({ ...current, hosts: { ...current.hosts, [platform.host]: status } }), root);
  return { ran: true, status };
}

async function check(platform: Platform, latest: () => Promise<Release>, now: () => number): Promise<HostStatus> {
  const at = () => new Date(now()).toISOString();
  try {
    const installed = await platform.inspect();
    if (!installed.eligible) return { checkedAt: at(), result: "skipped", reason: installed.reason, ...(installed.version ? { installed: installed.version } : {}) };
    const release = await latest();
    if (release.version === installed.version) return { checkedAt: at(), result: "up-to-date", latest: release.version, installed: installed.version };
    const after = await platform.apply(release);
    if (after === release.version) return { checkedAt: at(), result: "updated", latest: release.version, installed: after, from: installed.version, to: after, updatedAt: at() };
    return { checkedAt: at(), result: "waiting", latest: release.version, installed: after };
  } catch (error) {
    return { checkedAt: at(), result: "failed", reason: String(error instanceof Error ? error.message : error).slice(0, 300) };
  }
}

// In a plugin service: a first check two minutes after it starts (Codex starts its services all at once, at launch),
// then every few hours while it runs; updateOnce decides whether one is due. Never throws.
export function startUpdater(host: Host, platform: () => Platform, options: { running: string | null; root?: string; firstMs?: number; everyMs?: number; onResult?: (outcome: UpdateOutcome) => void }): () => void {
  const root = options.root ?? dataDir();
  // The version the user has seen noted: the one running when the plugin first did this.
  if (options.running && !readUpdateState(root).seen?.[host]) {
    changeUpdateState((state) => (state.seen?.[host] ? state : { ...state, seen: { ...state.seen, [host]: options.running! } }), root);
  }
  const run = () => { updateOnce(platform(), { root }).then((outcome) => options.onResult?.(outcome), () => {}); };
  const first = setTimeout(run, options.firstMs ?? 2 * 60_000);
  const every = setInterval(run, options.everyMs ?? RETRY_MS);
  first.unref?.();
  every.unref?.();
  return () => { clearTimeout(first); clearInterval(every); };
}

// What the panel shows about updates for the platform it is on. notes: the running version's release page (the panel
// itself names no address: it loads nothing from the network).
export type UpdateView = { version: string | null; auto: boolean; status: HostStatus | null; pending: string | null; updated: string | null; notes: string | null };
export function updateView(host: Host, running: string | null, root = dataDir(), env: NodeJS.ProcessEnv = process.env): UpdateView {
  const state = readUpdateState(root);
  const status = state.hosts?.[host] ?? null;
  // Installed and waiting for a restart (Codex) or a new session (Claude Code).
  const pending = status?.result === "updated" && status.to && status.to !== running ? status.to : null;
  // Running a version the user has not seen noted yet.
  const seen = state.seen?.[host];
  const updated = running && seen && seen !== running ? running : null;
  return { version: running, auto: autoUpdateOn(state, env), status, pending, updated, notes: running && parseVersion(running) ? releasePage(running) : null };
}
export function changeUpdate(host: Host, change: { auto?: boolean; seen?: string }, root = dataDir()): UpdateState {
  return changeUpdateState((state) => ({
    ...state,
    ...(typeof change.auto === "boolean" ? { auto: change.auto } : {}),
    ...(typeof change.seen === "string" && parseVersion(change.seen) ? { seen: { ...state.seen, [host]: change.seen } } : {}),
  }), root);
}

// ---- running a platform's command line ----
export type Ran = { ok: boolean; code: number | null; stdout: string; stderr: string };
// How long one command may take. It runs in the background, so long enough for a slow network: Codex's `plugin list`
// took 114 s on a machine with several git marketplaces (2026-11-23), against 3 minutes before.
export const COMMAND_TIMEOUT_MS = 10 * 60_000;
// A command still running at its time limit is stopped with everything it started: `claude plugin update` cloning over
// SSH left its git and ssh running when only it was stopped (2026-11-23). On Windows taskkill stops the tree; elsewhere
// the command leads its own process group.
function stopTree(child: ChildProcess): void {
  if (child.pid === undefined) return;
  try {
    if (process.platform === "win32") spawn("taskkill", ["/pid", String(child.pid), "/T", "/F"], { windowsHide: true, stdio: "ignore" }).on("error", () => child.kill()).unref();
    else process.kill(-child.pid, "SIGKILL");
  } catch {
    child.kill();
  }
}
// Asynchronous: the plugin service keeps answering its platform meanwhile. An npm-installed command on Windows is a
// .cmd shim, which only cmd.exe can start.
export function runCommand(command: string, args: string[], options: { env?: NodeJS.ProcessEnv; timeoutMs?: number } = {}): Promise<Ran> {
  const shim = process.platform === "win32" && /\.(cmd|bat)$/i.test(command);
  return new Promise((resolve) => {
    let stdout = "";
    let stderr = "";
    let settled = false;
    const done = (ran: Ran) => { if (!settled) { settled = true; clearTimeout(timer); resolve(ran); } };
    const child = spawn(shim ? "cmd.exe" : command, shim ? ["/d", "/s", "/c", command, ...args] : args, { env: options.env ?? process.env, windowsHide: true, stdio: ["ignore", "pipe", "pipe"], detached: process.platform !== "win32" });
    const timer = setTimeout(() => { stopTree(child); done({ ok: false, code: null, stdout, stderr: `${stderr}\ntimed out` }); }, options.timeoutMs ?? COMMAND_TIMEOUT_MS);
    child.stdout.on("data", (chunk) => { if (stdout.length < 1 << 20) stdout += chunk; });
    child.stderr.on("data", (chunk) => { if (stderr.length < 1 << 20) stderr += chunk; });
    child.on("error", (error) => done({ ok: false, code: null, stdout, stderr: String(error) }));
    child.on("close", (code) => done({ ok: code === 0, code, stdout, stderr }));
  });
}
// The JSON a command printed, after any warnings before it.
export function jsonOf(text: string): any {
  const start = text.search(/[[{]/);
  if (start < 0) throw new Error("no JSON in the output");
  return JSON.parse(text.slice(start));
}
export const failure = (what: string, ran: Ran) => new Error(`${what} failed (${ran.code ?? "no exit code"}): ${(ran.stderr || ran.stdout).trim().split(/\r?\n/).slice(-3).join(" ").slice(0, 240)}`);
