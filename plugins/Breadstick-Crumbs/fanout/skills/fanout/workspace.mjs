import { spawnSync } from "node:child_process";
import { existsSync, lstatSync, mkdirSync, mkdtempSync, openSync, closeSync, fstatSync, readSync, readFileSync, readdirSync, realpathSync, renameSync, rmdirSync, unlinkSync, writeFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { basename, dirname, join, resolve } from "node:path";

export const win = process.platform === "win32";
export function git(cwd, ...args) {
  const r = spawnSync("git", args, { cwd, encoding: "utf8", windowsHide: true });
  return { ok: r.status === 0, out: r.stdout ?? "", error: r.stderr || r.error?.message || "" };
}

export const gitStatus = (cwd) => spawnSync("git", ["status", "--porcelain=v1", "-z", "--no-renames", "--", ".", ":(exclude,top).fanout"], { cwd, encoding: "utf8", windowsHide: true });

export function checkout(cwd) {
  const top = git(cwd, "rev-parse", "--show-toplevel");
  return resolve(top.ok ? top.out.trim() : cwd);
}

export function runRoot(cwd) {
  const top = checkout(cwd), parent = dirname(top);
  return basename(parent) === "lanes" && basename(dirname(parent)) === ".fanout"
    ? dirname(dirname(parent)) : top;
}

export function validLaneName(name) {
  // A lane name is both a Git ref component and a directory name.
  return Boolean(name) && !/[\x00-\x20\x7f~^:?*\[\\/<>"|]|\.\.|@\{|^\.|\.$|\.lock$/.test(name)
    && (!win || !/^(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)/i.test(name));
}

export function laneHealth(path, branch, base, root) {
  if (!existsSync(path)) return "missing";
  const top = git(path, "rev-parse", "--show-toplevel");
  if (!top.ok || realpathSync(top.out.trim()) !== realpathSync(path)) return "not a worktree";
  const actual = git(path, "symbolic-ref", "--quiet", "--short", "HEAD").out.trim();
  if (actual !== branch) return actual ? `on ${actual}, expected ${branch}` : "detached HEAD";
  const common = (cwd) => git(cwd, "rev-parse", "--path-format=absolute", "--git-common-dir").out.trim();
  if (!common(path) || realpathSync(common(path)) !== realpathSync(common(root))) return "belongs to a different repository";
  if (base && !git(path, "merge-base", "--is-ancestor", base, "HEAD").ok) return `does not descend from ${base}`;
  return "ok";
}

export function worktreeList(root) {
  return git(root, "worktree", "list", "--porcelain", "-z").out.split("\0\0").map((entry) => {
    const fields = entry.split("\0");
    return { path: fields[0].slice("worktree ".length), branch: fields.find((s) => s.startsWith("branch "))?.slice(7) };
  }).filter((w) => w.path);
}

// Remove only a registered worktree or an empty leftover folder.
export function dropWorktree(root, path, { force = false } = {}) {
  const registered = () => worktreeList(root).some((w) => resolve(w.path) === resolve(path));
  if (registered()) {
    let result;
    for (let i = 0; i < 4; i++) {
      result = git(root, "worktree", "remove", ...(force ? ["--force"] : []), path);
      if (result.ok) return null;
      if (!/permission denied|resource busy|access is denied/i.test(result.error)) break;
      pause();
      if (!registered()) break;
    }
    if (registered()) return result.error.trim() || "git worktree remove failed";
  }
  if (!existsSync(path)) return null;
  for (let i = 0; i < 4; i++) {
    try {
      if (!lstatSync(path).isDirectory() || readdirSync(path).length) return "unregistered path is not an empty directory";
      rmdirSync(path);
      return null;
    } catch (e) {
      if (e.code === "ENOENT") return null;
      if (i === 3 || !["EPERM", "EBUSY", "EACCES"].includes(e.code)) return e.message;
      pause();
    }
  }
}

function pause() {
  Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, 150);
}

export function alive(pid, group = false) {
  if (!Number.isSafeInteger(pid) || pid <= 1) return false;
  try { process.kill(group && !win ? -pid : pid, 0); return true; } catch (e) { return e.code === "EPERM"; }
}

export const activeChildren = (live) => Object.values(live?.sessions ?? {}).some((s) => alive(s.pid, true));
export const planHash = (text) => createHash("sha256").update(text).digest("hex");

// A stale live file can outlast a PID. POSIX groups may still exist after their
// leader exits, so a missing leader can still identify a live group.
export function recordedProcess(pid, launchedAt, group = false) {
  if (!alive(pid, group)) return false;
  if (!Number.isFinite(launchedAt) || (!win && group && !alive(pid))) return true;
  let started;
  if (win) {
    const r = spawnSync("powershell.exe", ["-NoProfile", "-NonInteractive", "-Command",
      `([DateTimeOffset](Get-Process -Id ${pid} -ErrorAction Stop).StartTime).ToUnixTimeMilliseconds()`],
    { encoding: "utf8", windowsHide: true, timeout: 5000 });
    if (r.status === 0 && r.stdout.trim()) started = Number(r.stdout.trim());
  } else {
    const r = spawnSync("ps", ["-p", String(pid), "-o", "etime="], { encoding: "utf8", timeout: 5000 });
    const elapsed = r.stdout?.trim().match(/^(?:(\d+)-)?(?:(\d+):)?(\d+):(\d+)$/);
    if (elapsed) {
      const [, days = 0, hours = 0, minutes, seconds] = elapsed;
      started = Date.now() - (((Number(days) * 24 + Number(hours)) * 60 + Number(minutes)) * 60 + Number(seconds)) * 1000;
    }
  }
  // Recheck liveness if the process disappeared during lookup.
  return alive(pid, group) && (!Number.isFinite(started) || Math.abs(started - launchedAt) < 5000);
}

// Publish a nonempty directory in one step. A contender can remove an expired PID
// marker and the empty directory it leaves, but cannot replace a new owner's lock.
export function workspaceLock(root) {
  const state = join(root, ".fanout"), lock = join(state, "lock"), marker = String(process.pid);
  mkdirSync(state, { recursive: true });
  const pending = mkdtempSync(join(state, "lock-"));
  writeFileSync(join(pending, marker), "");
  const remove = (dir, file) => {
    try { if (file) unlinkSync(join(dir, file)); } catch (e) { if (e.code !== "ENOENT") throw e; }
    try { rmdirSync(dir); } catch (e) { if (!["ENOENT", "ENOTEMPTY", "EEXIST"].includes(e.code)) throw e; }
  };
  try {
    for (let attempt = 0; attempt < 3; attempt++) {
      try {
        renameSync(pending, lock);
        return () => remove(lock, marker);
      } catch (error) {
        let entries;
        try { entries = readdirSync(lock); } catch (e) { if (e.code === "ENOENT" && ["ENOENT", "EPERM", "EACCES"].includes(error.code)) continue; throw error; }
        if (entries.length > 1 || (entries[0] && (!/^\d+$/.test(entries[0]) || alive(Number(entries[0]))))) return null;
        remove(lock, entries[0]);
      }
    }
    return null;
  } finally { if (existsSync(pending)) remove(pending, marker); }
}

export function stopProcess(pid, { group = true, force = true } = {}) {
  if (!alive(pid, group) || pid === process.pid) return true;
  if (win) return spawnSync("taskkill", ["/PID", String(pid), "/T", "/F"], { windowsHide: true }).status === 0 || !alive(pid);
  try { process.kill(group ? -pid : pid, force ? "SIGKILL" : "SIGTERM"); return true; }
  catch { return !alive(pid, group); }
}

export function readLive(root) {
  try {
    const live = JSON.parse(readFileSync(join(root, ".fanout", "live.json"), "utf8"));
    return { ...live, sessions: live.sessions ?? {}, running: alive(live.pid) };
  } catch { return null; }
}

export function writeLive(root, live) {
  const path = join(root, ".fanout", "live.json");
  const tmp = `${path}.${process.pid}.tmp`;
  writeFileSync(tmp, JSON.stringify(live));
  renameSync(tmp, path);
}

export function markAborted(root, live) {
  live.phase = live.result = "aborted";
  live.pid = null;
  for (const lane of Object.values(live.sessions ?? {})) {
    if (lane.pid || lane.since) { lane.state = "aborted"; lane.since = null; }
    if (!alive(lane.pid, true)) lane.pid = null;
  }
  writeLive(root, live);
}

export function commandLogs(root, label) {
  const path = join(root, ".fanout", "logs");
  mkdirSync(path, { recursive: true });
  const folder = mkdtempSync(join(path, `${label}-${new Date().toISOString().replaceAll(":", "-")}-`));
  let index = 0;
  return {
    folder,
    run(step, run) {
      const file = join(folder, `${++index}-${step.replace(/[^\w.-]/g, "-")}.log`);
      const fd = openSync(file, "w+");
      try {
        const result = run(fd);
        if (result.error) writeFileSync(fd, `${result.error.message}\n`);
        let out = "";
        if (result.status !== 0) {
          const { size } = fstatSync(fd);
          const buffer = Buffer.alloc(Math.min(size, 1024 * 1024));
          const read = readSync(fd, buffer, 0, buffer.length, size - buffer.length);
          out = buffer.toString("utf8", 0, read);
        }
        return { ...result, logPath: file, out };
      } finally { closeSync(fd); }
    },
  };
}
