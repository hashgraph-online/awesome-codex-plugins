#!/usr/bin/env node
// fanout: plan parallel sessions, check for overlap, verify branches, guard edits.
//   fanout check  [plan.md]                         plan defaults to .fanout/plan.md in the main checkout
//   fanout verify [--session name] [--base <branch>]    session defaults to the fanout/<name> branch
//   fanout rehearse [plan.md] [--base <branch>] [--test cmd]   merge every branch in order on a scratch worktree, test once (bisect on failure)
//   fanout guard                                    PreToolUse hook (installed by the plugin)
//   fanout install-git-hook [--force]               same rules as a git pre-commit hook, for agents outside Claude Code
//   fanout run ["goal" | --goal-file f] [--yes] [--agent claude|codex|"<cmd>"] [--mix]   do the whole fan-out: plan, agents, rehearse, fix, merge (see run.mjs)
//   fanout status [--base <branch>]                     one table: each session's branch, commits, files, worktree, verify flags, agent state and cost (fanout run), last run and rehearse
//   fanout overlap [--base <branch>] [--all]            every active checkout (any worktree, any session) and its changes, files changed in more than one, dry-run merge
//   fanout log [--last 20]                          past runs and rehearsals from .fanout/log.jsonl: time, cost, fixes, test runs
import { readFileSync, writeFileSync, appendFileSync, mkdirSync, chmodSync, existsSync, realpathSync, readdirSync, copyFileSync } from "node:fs";
import { execFileSync, spawnSync, spawn } from "node:child_process";
import { resolve, relative, isAbsolute, join, dirname, basename } from "node:path";
import { pathToFileURL, fileURLToPath } from "node:url";
import { claimsActive, claimsOn, branchOf, liveClaims, claimedByOther, editedByOthers, writeState, autoClaim, refusalText, taskFromTranscript, hookTranscript, recheckClaim, selfCheckText,
  notices, repoInfo, logEvent, readEvents, waitChecked, claimCmd, startCmd, showClaims, releaseCmd, initCmd, cleanTask, precheck, readState } from "./claims.mjs";

const SESSION_KEYS = ["owns", "after", "exposes", "uses", "done", "task", "check", "agent", "model"];
const PLAN_KEYS = ["test", "regen"];

export function parsePlan(text) {
  const sessions = [];
  for (const block of text.split(/^## /m).slice(1)) {
    const [name, ...rest] = block.split("\n");
    const get = (k) => (rest.find((l) => l.startsWith(k + ":")) ?? "").slice(k.length + 1).trim();
    const list = (k) => get(k).split(",").map((s) => s.trim()).filter(Boolean);
    const keys = rest.map((l) => l.match(/^([A-Za-z_-]+):/)?.[1]).filter(Boolean);
    sessions.push({ name: name.trim(), owns: list("owns"), after: list("after"), exposes: list("exposes"), uses: list("uses"),
      task: get("task"), done: get("done"), check: get("check"), agent: get("agent"), model: get("model"), keys });
  }
  return sessions;
}

// Plan-wide settings sit above the first "## " block, e.g. "test: npm test".
export const planSetting = (text, key) =>
  (text.split(/^## /m)[0].split("\n").find((l) => l.startsWith(key + ":")) ?? "").slice(key.length + 1).trim();

// "regen: src/gen/**, api.d.ts via npm run codegen" (any number of lines above the first "## "):
// generated files no session owns or commits; the command rebuilds them after merging.
export const parseRegen = (text) => text.split(/^## /m)[0].split("\n").filter((l) => l.startsWith("regen:")).map((l) => {
  const [paths, cmd = ""] = l.slice(6).split(/\s+via\s+/);
  return { paths: paths.split(",").map((x) => x.trim()).filter(Boolean), cmd: cmd.trim() };
});

const norm = (p) => p.replaceAll("\\", "/").replace(/^\.\//, "");

// Glob to regex: ** = any depth, * = within a segment, ? = one char, {a,b} = alternatives.
export function globToRegex(glob) {
  const g = norm(glob);
  let re = "", i = 0, brace = 0;
  while (i < g.length) {
    const c = g[i];
    if (c === "*") {
      if (g[i + 1] === "*") {
        i += 2;
        if (g[i] === "/") { re += "(?:.*/)?"; i++; } else re += ".*";
        continue;
      }
      re += "[^/]*";
    } else if (c === "?") re += "[^/]";
    else if (c === "{") { re += "(?:"; brace++; }
    else if (c === "}" && brace) { re += ")"; brace--; }
    else if (c === "," && brace) re += "|";
    else re += c.replace(/[.+^$()|[\]\\]/g, "\\$&");
    i++;
  }
  return new RegExp("^" + re + "$");
}

export const matches = (glob, path) => {
  const g = norm(glob);
  // A trailing slash means "everything under this directory".
  if (g.endsWith("/")) return norm(path).startsWith(g);
  return globToRegex(g).test(norm(path));
};
export const ownsFile = (session, path) => session.owns.some((g) => matches(g, path));
// Contracts: files a session exposes to others. They are committed to main before the
// sessions start and stay frozen on every fanout branch, the owner's included.
const exposes = (session, path) => (session.exposes ?? []).some((g) => g === path || matches(g, path));
export const contractOwner = (sessions, path) => sessions.find((s) => exposes(s, path));
export const contractChanges = (sessions, changed) => changed.filter((f) => contractOwner(sessions, f));
export const regenFor = (regen, path) => regen.find((r) => r.paths.some((g) => matches(g, path)));

// Why this session may not change rel, or null if it may. Shared by the edit guard and the git hook.
export function blockReason(sessions, s, regen, rel) {
  const owner = contractOwner(sessions, rel);
  if (owner && owner.name !== s.name) return `${rel} is a contract (exposed by "${owner.name}") and is frozen for every other session. Ask the coordinator to change the plan, or ask "${owner.name}" to evolve it.`;
  const r = regenFor(regen, rel);
  if (r) return `${rel} is generated (\`${r.cmd}\` rebuilds it after merging). Change its source instead, and don't commit it.`;
  if (ownsFile(s, rel)) return null;
  return `session "${s.name}" does not own ${rel}. Owned: ${s.owns.join(", ")}. Ask the coordinator to change the plan.`;
}

const isGlob = (s) => /[*?{]/.test(s);
const prefix = (g) => norm(g).split(/[*?{]/)[0];
const prefixClash = (a, b) => {
  const pa = prefix(a), pb = prefix(b);
  return pa === pb || (isGlob(a) && pb.startsWith(pa)) || (isGlob(b) && pa.startsWith(pb));
};

function git(args, cwd) {
  return execFileSync("git", args, { cwd, encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] });
}
// Files a lane changed itself, against base. Before a fix round fanout run merges the branches ahead of
// a lane into it, so it can test on their real code; files that came in only through those merges aren't
// the lane's edits. Its own commits are the first-parent, non-merge ones.
function laneChanged(base, head, cwd) {
  const changed = git(["diff", "--name-only", `${base}...${head}`], cwd).split("\n").filter(Boolean);
  if (git(["rev-list", "--merges", "--count", `${base}..${head}`], cwd).trim() === "0") return changed;
  const own = new Set(git(["log", "--first-parent", "--no-merges", "--name-only", "--format=", `${base}..${head}`], cwd).split("\n").filter(Boolean));
  return changed.filter((f) => own.has(f));
}
function repoFiles(cwd) {
  try { return git(["ls-files", "--cached", "--others", "--exclude-standard"], cwd).split("\n").filter(Boolean); }
  catch { return null; }
}

// With a git repo, two patterns clash only if a real file matches both, or if one
// of them names paths that don't exist yet and the prefixes overlap.
// Without a repo, falls back to comparing the literal prefixes.
// Returns null for no overlap, else a detail string ("" when there is nothing to add).
function overlap(a, b, files) {
  if (!files) return prefixClash(a, b) ? "" : null;
  const shared = files.filter((f) => matches(a, f) && matches(b, f));
  if (shared.length) return `: ${shared.slice(0, 3).join(", ")}${shared.length > 3 ? ` +${shared.length - 3} more` : ""}`;
  const ma = files.some((f) => matches(a, f)), mb = files.some((f) => matches(b, f));
  return (!ma || !mb) && prefixClash(a, b) ? ": new paths may overlap" : null;
}

export function check(sessions, cwd, regen = []) {
  const problems = [];
  const files = cwd ? repoFiles(cwd) : null;
  for (let i = 0; i < sessions.length; i++)
    for (let j = i + 1; j < sessions.length; j++)
      for (const a of sessions[i].owns) for (const b of sessions[j].owns) {
        const o = overlap(a, b, files);
        if (o !== null) problems.push(`CLASH ${sessions[i].name} (${a}) <-> ${sessions[j].name} (${b})${o}`);
      }
  for (const r of regen) {
    if (!r.cmd) problems.push(`REGEN ${r.paths.join(", ")}: no command (write "regen: <paths> via <command>")`);
    for (const g of r.paths) for (const s of sessions) for (const a of s.owns) {
      const o = overlap(g, a, files);
      if (o !== null) problems.push(`REGEN ${g} is generated but ${s.name} owns ${a}${o}`);
    }
  }
  // A session that uses a contract merges after the session exposing it.
  const deps = new Map(sessions.map((s) => [s.name, [...s.after]]));
  for (const s of sessions) {
    if (!s.owns.length) problems.push(`PLAN ${s.name} has no owns: line`);
    for (const k of s.keys ?? []) {
      if (PLAN_KEYS.includes(k)) problems.push(`PLAN ${k}: goes above the first "##" line, once for the whole plan, not inside ${s.name}`);
      else if (!SESSION_KEYS.includes(k)) problems.push(`PLAN unknown field "${k}:" in ${s.name} (known: ${SESSION_KEYS.join(", ")})`);
    }
    for (const e of s.exposes ?? [])
      if (!ownsFile(s, e)) problems.push(`EXPOSES ${e} (in ${s.name}): not in its owns`);
    for (const u of s.uses ?? []) {
      const owner = contractOwner(sessions.filter((x) => x !== s), u);
      if (!owner) { problems.push(`USES ${u} (in ${s.name}): no other session exposes it`); continue; }
      if (!deps.get(s.name).includes(owner.name)) deps.get(s.name).push(owner.name);
    }
  }
  const order = [], seen = new Set();
  const visit = (s, stack = []) => {
    if (seen.has(s.name)) return;
    if (stack.includes(s.name)) { problems.push("CYCLE in after/uses: " + [...stack, s.name].join(" -> ")); return; }
    for (const d of deps.get(s.name)) {
      const t = sessions.find((x) => x.name === d);
      if (t) visit(t, [...stack, s.name]); else problems.push(`UNKNOWN after: ${d} (in ${s.name})`);
    }
    seen.add(s.name); order.push(s.name);
  };
  sessions.forEach((s) => visit(s));
  return { problems, order };
}

export const verify = (session, changed) => changed.filter((f) => !ownsFile(session, f));

const arg = (argv, flag, dflt) => { const i = argv.indexOf(flag); return i >= 0 ? argv[i + 1] : dflt; };

// Sessions work on branch fanout/<name>; the plan lives in the main checkout at .fanout/plan.md.
// Both can be found from inside any worktree, so nothing needs configuring.
const BRANCH_PREFIX = "fanout/";
function currentSession(cwd) {
  try {
    const b = git(["branch", "--show-current"], cwd).trim();
    return b.startsWith(BRANCH_PREFIX) ? b.slice(BRANCH_PREFIX.length) : null;
  } catch { return null; }
}
export function mainRoot(cwd) {
  try { return resolve(git(["rev-parse", "--path-format=absolute", "--git-common-dir"], cwd).trim(), ".."); }
  catch { return cwd; }
}
// The branch the main checkout is on (master, trunk, ...), else main if the repo has it.
// defaultBase without a git call, from the main checkout's HEAD file (for the hook that runs on every tool call).
function mainBranch(common) {
  let b = null;
  try { b = readFileSync(join(common, "HEAD"), "utf8").match(/^ref: refs\/heads\/(.+)$/m)?.[1]?.trim(); } catch { /* none */ }
  return b && !b.startsWith(BRANCH_PREFIX) ? b : "main";
}
function defaultBase(cwd) {
  try {
    const b = git(["branch", "--show-current"], mainRoot(cwd)).trim();
    if (b && !b.startsWith(BRANCH_PREFIX)) return b;
  } catch { /* detached or not a repo */ }
  return "main";
}
// The repo's own default branch, for overlap (no plan): origin/HEAD, else main or master, else the
// checkout's branch. Not defaultBase: a fan-out builds on whatever branch the main checkout is on, but
// with no plan the main checkout may just be on a feature branch (seen: docs/caching-findings).
function repoDefaultBranch(cwd) {
  const root = mainRoot(cwd), has = (b) => { try { git(["rev-parse", "--verify", "--quiet", "refs/heads/" + b], root); return true; } catch { return false; } };
  try {
    const b = git(["symbolic-ref", "-q", "--short", "refs/remotes/origin/HEAD"], root).trim().replace(/^origin\//, "");
    if (b && has(b)) return b;
  } catch { /* no remote HEAD */ }
  return ["main", "master"].find(has) ?? defaultBase(cwd);
}
// The plan beside this lane (lanes sit in <checkout>/.fanout/lanes/<name>), else this checkout's, else the main
// checkout's. A session the desktop app runs in its own worktree writes the plan and lanes there: read only from
// the main checkout, the guard didn't know the lanes, and their edits fell through to claims.
function defaultPlan(cwd) {
  const main = resolve(mainRoot(cwd), ".fanout", "plan.md");
  let top;
  try { top = resolve(git(["rev-parse", "--show-toplevel"], cwd).trim()); } catch { return main; }
  const lanes = dirname(top), fanoutDir = dirname(lanes);
  const near = [...(basename(lanes) === "lanes" && basename(fanoutDir) === ".fanout" ? [join(fanoutDir, "plan.md")] : []), join(top, ".fanout", "plan.md")];
  return near.find((p) => existsSync(p)) ?? main;
}

// Merges the branches in plan order on a throwaway worktree, then rebuilds generated files and runs the
// test command once. Only if that fails does it bisect over the merge order (about log2(n) more runs)
// to name the branch whose merge broke things, so a passing rehearsal costs one test run, not n.
// The worktree sits in .fanout/ inside the main checkout so node_modules etc. still resolve.
// Output is a few lines plus the failing tests of a failing run (failureLines): cheap for an agent to act on.
// A session's "check:" is a command proving its own done: (a grep, a curl, a script). The test alone can
// pass on code that doesn't do the job (a lint can't see a dead link or a missing switch), so once all
// branches merge and pass, each session's check runs on the merged code; a failure names that session.
// The shell for the plan's own commands (test:, check:, regen), which are written in sh syntax (`!`, `&&`, quotes).
// On Windows Node's shell is cmd.exe, which can't run them: on a real project a check starting `! grep` failed
// every time, whatever the code, and two fix rounds ($2.41) were spent on it. So there they run in Git's own bash
// (found from git, not PATH, where bash.exe may be WSL's); cmd.exe only if it isn't there. FANOUT_SHELL overrides.
let planShellFound;
export function planShell() {
  if (process.env.FANOUT_SHELL) return process.env.FANOUT_SHELL;
  if (process.platform !== "win32") return true;
  if (planShellFound === undefined) {
    const exec = (spawnSync("git", ["--exec-path"], { encoding: "utf8" }).stdout ?? "").trim(); // <Git>/mingw64/libexec/git-core
    planShellFound = exec ? [join(exec, "..", "..", "..", "bin", "bash.exe"), join(exec, "..", "..", "..", "usr", "bin", "bash.exe")].find(existsSync) ?? true : true;
  }
  return planShellFound;
}
export const runPlanCmd = (cmd, cwd) => spawnSync(cmd, { cwd, shell: planShell(), encoding: "utf8" });

// A fresh worktree has only tracked files, so a project whose tests read a gitignored .env or local database
// fails there though it passes in the checkout. Claude Code copies the gitignored files listed in
// .worktreeinclude (.gitignore syntax) into its worktrees; fanout reads the same file for its own (rehearse's
// scratch copy, fanout run's lanes), so it's set up once for both. Git matches the patterns, but only over the
// checkout's ignored files and the ignored folders a pattern names: walking all of node_modules took 9-10s on a
// real project, this about 0.2s.
const gitZ = (cwd, args) => (spawnSync("git", ["--literal-pathspecs", args[0], "-z", ...args.slice(1)], { cwd, encoding: "utf8", maxBuffer: 64 << 20 }).stdout ?? "").split("\0").filter(Boolean);
// Whether a .worktreeinclude pattern can match inside an ignored folder ("pkg/cache/"). A pattern with no
// slash but a trailing one ("secrets", "cache/", "**/cache/") matches a name at any depth; one with a slash
// is a path from the repo root ("config/secrets.json", "data/**").
const reaches = (pat, dir) => {
  const p = pat.replace(/^!/, "").replace(/^\/+/, ""), rest = p.replace(/^(\*\*\/)+/, "").replace(/\/+$/, ""), d = dir.replace(/\/+$/, "");
  if (!rest.includes("/")) return d.split("/").some((seg) => matches(rest, seg));
  if (rest !== p.replace(/\/+$/, "")) return d.split("/").includes(rest.split("/")[0]); // **/a/b: a named in the folder's path
  return rest.startsWith(`${d}/`) || rest === d || matches(rest, d) || d.startsWith(`${rest}/`);
};
export function worktreeIncludes(root) {
  let pats;
  try { pats = readFileSync(join(root, ".worktreeinclude"), "utf8").split(/\r?\n/).map((l) => l.trim()).filter((l) => l && !l.startsWith("#")); } catch { return []; }
  const where = gitZ(root, ["ls-files", "--others", "--ignored", "--exclude-standard", "--directory"])
    .filter((f) => !f.endsWith("/") || pats.some((p) => reaches(p, f)));
  // In batches short enough for Windows' command line (32,767 characters), whatever the path lengths.
  const out = [];
  for (let i = 0; i < where.length;) {
    const batch = [];
    for (let len = 0; i < where.length && (!batch.length || len + where[i].length < 8000);) { len += where[i].length + 1; batch.push(where[i++]); }
    out.push(...gitZ(root, ["ls-files", "--others", "--ignored", "--exclude-from=.worktreeinclude", "--", ...batch]));
  }
  return out;
}
// A file that can't be copied (a dangling symlink, one locked on Windows) is reported, not fatal.
export function copyIncludes(root, wt) {
  const copied = [], failed = [];
  for (const f of worktreeIncludes(root)) {
    const to = join(wt, f);
    try { if (!existsSync(to)) { mkdirSync(dirname(to), { recursive: true }); copyFileSync(join(root, f), to); } copied.push(f); }
    catch (e) { failed.push(`${f} (${e.code ?? e.message})`); }
  }
  return { copied, failed };
}
const listed = (xs) => `${xs.slice(0, 8).join(", ")}${xs.length > 8 ? ` and ${xs.length - 8} more` : ""}`;
// Gitignored files in the checkout that a scratch copy lacks: the likely cause when the base fails only there.
// Files only: an ignored folder (node_modules/) is still found by walking up, since the copy sits in .fanout/.
const missingIgnored = (root, wt) => gitZ(root, ["ls-files", "--others", "--ignored", "--exclude-standard", "--directory"]).filter((f) => !f.endsWith("/") && !existsSync(join(wt, f)));

export function rehearse(order, { cwd, base = "main", test, regen = [], checks = [], tail = 20, prefix = BRANCH_PREFIX }) {
  const log = [], root = mainRoot(cwd), wt = join(root, ".fanout", "rehearse");
  let testRuns = 0;
  const sh = (cmd) => { if (cmd === test) testRuns++; return runPlanCmd(cmd, wt); };
  const tailOf = (r) => failureLines(`${r.stdout ?? ""}${r.stderr ?? ""}`, tail);
  const g = (...a) => execFileSync("git", ["-c", "user.name=fanout", "-c", "user.email=fanout@local", ...a],
    { cwd: wt, encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] });
  const drop = () => { try { git(["worktree", "remove", "--force", wt], root); } catch { /* not there */ } };
  drop();
  git(["worktree", "add", "--detach", wt, base], root);
  let ok = true;
  try {
    const { copied, failed } = copyIncludes(root, wt);
    if (copied.length) log.push(`COPIED from your checkout (.worktreeinclude): ${listed(copied)}`);
    if (failed.length) log.push(`COULD NOT COPY (.worktreeinclude): ${listed(failed)}`);
    const merged = [[base, g("rev-parse", "HEAD").trim()]]; // [name, commit]: merged[k] = state after k merges
    for (const name of order) {
      const branch = prefix + name; // fanout/<name>, or any branch with prefix ""
      try { git(["rev-parse", "--verify", "--quiet", branch], root); }
      catch { log.push(`SKIP ${name}: no branch ${branch}`); continue; }
      try { g("merge", "--no-ff", "--no-edit", branch); }
      catch {
        const files = g("diff", "--name-only", "--diff-filter=U").split("\n").filter(Boolean);
        log.push(`CONFLICT merging ${name}: ${files.join(", ")}`);
        ok = false; break;
      }
      merged.push([name, g("rev-parse", "HEAD").trim()]);
    }
    // State after the first k merges: rebuild generated files (as the real merge will), then test.
    const probe = (k) => {
      g("reset", "-q", "--hard", merged[k][1]); g("clean", "-fdq");
      for (const x of regen.filter((x) => x.cmd)) {
        const r = sh(x.cmd);
        if (r.status !== 0) return { pass: false, lines: [`REGEN FAILED after ${merged[k][0]}: \`${x.cmd}\` exited ${r.status}`, tailOf(r)] };
      }
      if (!test) return { pass: true };
      const r = sh(test);
      return { pass: r.status === 0, lines: [`BROKE after ${merged[k][0]}: \`${test}\` exited ${r.status}`, tailOf(r)] };
    };
    const n = merged.length - 1;
    if (ok && n) {
      const full = probe(n);
      if (full.pass) {
        log.push(...(test ? [`OK after ${merged[n][0]} (all ${n} merged)`] : merged.slice(1).map(([name]) => `MERGED ${name}`)));
        for (const c of checks.filter((c) => c.check && merged.some(([m]) => m === c.name))) {
          const r = sh(c.check);
          if (r.status === 0) log.push(`CHECK OK ${c.name}`);
          else { log.push(`CHECK FAILED ${c.name}: \`${c.check}\` exited ${r.status}`, tailOf(r)); ok = false; }
        }
      } else {
        // Invariant: state lo passes (the base is assumed to until checked below), state hi fails.
        let lo = 0, hi = n, bad = full;
        while (hi - lo > 1) {
          const mid = (lo + hi) >> 1, r = probe(mid);
          if (r.pass) { lo = mid; log.push(`OK after ${merged[mid][0]}`); } else { hi = mid; bad = r; }
        }
        // Before blaming a branch: the same code failing again rules out a flaky test, and when the
        // first branch is blamed, the base itself must pass. Each costs a run only on this failure path.
        const baseRun = () => (hi === 1 ? probe(0) : { pass: true });
        let b;
        if (probe(hi).pass) {
          log.push(`FLAKY: \`${test}\` failed, then passed on a rerun of the same code (after ${merged[hi][0]}). No branch is blamed; fix or quarantine the flaky test.`, bad.lines[1]);
        } else if (!(b = baseRun()).pass) {
          // A base that passes in the checkout and fails here is usually a gitignored file the copy lacks (.env):
          // name the ones missing, or "fix main" sends the user after code that's fine.
          const missing = missingIgnored(root, wt);
          log.push(`BASE FAILS: \`${test}\` already fails on ${base} before any branch is merged, in fanout's scratch copy (${norm(relative(root, wt))}). Fix ${base} first.`
            + (missing.length ? ` If it passes in your checkout, the copy may lack gitignored files it needs: ${missing.slice(0, 6).join(", ")}${missing.length > 6 ? ", ..." : ""}. List the ones it needs in .worktreeinclude (one per line, .gitignore syntax; Claude Code's worktrees use the same file) and fanout copies them in.` : ""), b.lines[1]);
        } else log.push(...bad.lines);
        ok = false;
      }
    }
  } finally { drop(); }
  if (ok) log.push(test || checks.some((c) => c.check) ? "All branches merge and pass together." : "All branches merge cleanly (no test command: add `test:` to the plan).");
  return { ok, log, testRuns };
}

// The part of a failing run an agent needs. With TAP output (node --test when not on a terminal) the end is
// mostly the summary (# pass, # skipped, # duration_ms), so fix agents on the sheet benchmark reran the
// tests to see what failed. Here each "not ok" line comes with the diagnostics under it, then the counts.
// Other output: the last `tail` lines, as before.
export function failureLines(out, tail = 20, max = 80) {
  const lines = out.trimEnd().split("\n");
  const starts = lines.flatMap((l, i) => (/^\s*not ok\b/.test(l) ? [i] : []));
  if (!starts.length) return lines.slice(-tail).join("\n");
  const picked = [];
  for (const i of starts) {
    // A test file's own top-level "not ok" only repeats the failures listed under its subtests.
    if (picked.length && /^not ok \d+ - \S+\.(m?[jt]s|cjs)$/.test(lines[i])) continue;
    picked.push(lines[i]);
    for (let j = i + 1, n = 0; j < lines.length && n < 25 && !/^\s*(not )?ok\b|^\s*# Subtest|^# tests\b/.test(lines[j]); j++, n++) picked.push(lines[j]);
  }
  const counts = lines.filter((l) => /^# (tests|pass|fail) \d/.test(l));
  return [...(picked.length > max ? [...picked.slice(0, max), `... (${picked.length - max} more lines)`] : picked), ...counts].join("\n");
}

// Run log: one JSON line per fan-out or rehearsal in .fanout/log.jsonl (git-ignored, stays local),
// so real projects produce their own numbers: time, cost, fixes, test runs, result.
export function appendLog(cwd, rec) {
  try {
    const dir = join(mainRoot(cwd), ".fanout");
    mkdirSync(dir, { recursive: true });
    appendFileSync(join(dir, "log.jsonl"), JSON.stringify({ at: new Date().toISOString(), ...rec }) + "\n");
  } catch { /* logging must never break a run */ }
}

function showLog(cwd, limit = 20, days = 7) {
  let lines = [];
  try { lines = readFileSync(join(mainRoot(cwd), ".fanout", "log.jsonl"), "utf8").split("\n").filter(Boolean); } catch { /* none yet */ }
  const recs = lines.slice(-limit).map((l) => { try { return JSON.parse(l); } catch { return null; } }).filter(Boolean);
  if (recs.length) {
    console.log("when              kind      sessions  time    fixes  test runs  cost     result");
    for (const r of recs) {
      const cost = r.costUsd == null ? "" : `$${r.costUsd.toFixed(2)}${r.costUnknown ? "+?" : ""}`;
      console.log([r.at.slice(0, 16).replace("T", " "), (r.kind ?? "").padEnd(8), String(r.sessions ?? "").padEnd(8),
        mins(r.seconds).padEnd(6), String(r.fixes ?? "").padEnd(5), String(r.testRuns ?? "").padEnd(9), cost.padEnd(7), r.result ?? ""].join("  "));
    }
  } else console.log("No runs logged yet.");
  return showClaimLog(cwd, days);
}

// Claims in real use, from the events every claim decision and notice writes (claims.mjs, logEvent), so each
// refusal and notice can be checked by hand: was it the same work, did the notice matter. Plus what the
// after-each-tool-call hook cost, summed over every checkout.
function showClaimLog(cwd, days) {
  let common;
  try { common = git(["rev-parse", "--path-format=absolute", "--git-common-dir"], cwd).trim(); } catch { return 0; }
  const since = Date.now() - days * 86400000, ev = readEvents(common).filter((e) => Date.parse(e.at) >= since);
  const times = [common, ...(() => { try { return readdirSync(join(common, "worktrees")).map((d) => join(common, "worktrees", d)); } catch { return []; } })()]
    .map((d) => { try { return JSON.parse(readFileSync(join(d, "fanout-hook-time.json"), "utf8")); } catch { return null; } }).filter(Boolean);
  const calls = times.reduce((n, t) => n + t.calls, 0);
  if (!ev.length && !calls) { console.log(`\nNo claims or notices in the last ${days} days.`); return 0; }
  const of = (k) => ev.filter((e) => e.kind === k), when = (e) => e.at.slice(0, 16).replace("T", " ");
  const judged = ev.filter((e) => e.by === "judge"), cost = judged.reduce((n, e) => n + (e.costUsd ?? 0), 0);
  console.log(`\nClaims, last ${days} days: ${of("claim").length} claimed, ${of("refused").length} refused as the same work, ${of("locked").length} edit(s) of a locked file stopped, ${of("notice").length} notice(s).`);
  if (judged.length) console.log(`  Same-work checks by a model: ${judged.length}${cost ? `, $${cost.toFixed(3)}` : ""}.`);
  if (calls) console.log(`  The after-each-tool-call hook: ${calls} call(s), ${Math.round(times.reduce((n, t) => n + t.ms, 0) / calls)}ms on average, ${Math.max(...times.map((t) => t.max))}ms at most (Node's start included).`);
  if (of("refused").length) {
    console.log("\nRefused (check each: was it really the same work?):");
    for (const e of of("refused")) console.log(`  ${when(e)}  ${e.branch} (${e.via}): ${e.task || "(no task)"}\n    same as ${(e.as ?? []).map((n, i) => `${n}: ${e.asTasks?.[i] ?? ""}`).join("; ")}${e.why ? `\n    why: ${e.why}` : ""}`);
  }
  if (of("notice").length) {
    console.log("\nNotices (did the session need them?):");
    for (const e of of("notice")) console.log(`  ${when(e)}  ${e.session} told of ${e.from}'s change to ${e.files.join(", ")}${e.yours?.length ? ` (it had changed ${e.yours.join(", ")} too)` : ""} [${e.via}]`);
  }
  if (of("locked").length) {
    console.log("\nLocked files:");
    for (const e of of("locked")) console.log(`  ${when(e)}  ${e.session} stopped changing ${e.file}, claimed by ${e.owner} (${e.via})`);
  }
  return 0;
}
// Reads only existing state (plan, branches, lanes, log); works from the main checkout or any lane worktree.
function showStatus(cwd, base) {
  const root = mainRoot(cwd);
  let text;
  // Claims first: they cover sessions fanout didn't start, so they show with or without a plan.
  const claims = liveClaims(root, base);
  if (claims.length) { console.log("claims:"); for (const c of claims) console.log(`  ${c.name}  ${c.branch}  ${c.task || "(no task)"}  ${(c.files ?? []).length} file(s)`); }
  try { text = readFileSync(join(root, ".fanout", "plan.md"), "utf8"); } catch { console.log("No plan"); return 0; }
  const sessions = parsePlan(text), regen = parseRegen(text);
  if (!sessions.length) { console.log("No plan"); return 0; }
  const live = readLive(root);
  let behind = 0; // commits on base that some lane doesn't have
  const rows = [["session", "branch", "ahead", "files", "worktree", "verify"]];
  for (const s of sessions) {
    const branch = BRANCH_PREFIX + s.name, lane = existsSync(join(root, ".fanout", "lanes", s.name)) ? "yes" : "no";
    try { git(["rev-parse", "--verify", "--quiet", "refs/heads/" + branch], root); }
    catch { rows.push([s.name, "not started", "-", "-", lane, "-"]); continue; }
    try {
      const ahead = git(["rev-list", "--count", `${base}..${branch}`], root).trim();
      behind = Math.max(behind, Number(git(["rev-list", "--count", `${branch}..${base}`], root).trim()) || 0);
      const changed = laneChanged(base, branch, root);
      const contracts = contractChanges(sessions, changed);
      const frozen = contracts.filter((f) => contractOwner(sessions, f).name !== s.name);
      const generated = changed.filter((f) => regenFor(regen, f));
      const out = verify(s, changed).filter((f) => !contracts.includes(f) && !generated.includes(f));
      const flags = [out.length && `out of lane ${out.length}`, frozen.length && `contract ${frozen.length}`, generated.length && `generated ${generated.length}`].filter(Boolean);
      rows.push([s.name, branch, ahead, String(changed.length), lane, flags.join(", ") || "ok"]);
    } catch { rows.push([s.name, branch, "?", "?", lane, `no base ${base}`]); }
  }
  if (live) {
    rows[0].push("agent", "cost");
    for (const r of rows.slice(1)) r.push(...liveCells(live.sessions[r[0]], live.running));
    if (live.sessions["(planner)"]) rows.push(["(planner)", "-", "-", "-", "-", "-", ...liveCells({ state: "done", ...live.sessions["(planner)"] }, false)]);
  }
  const w = rows[0].map((_, i) => Math.max(...rows.map((r) => r[i].length)));
  rows.forEach((r) => console.log(r.map((c, i) => c.padEnd(w[i])).join("  ").trimEnd()));
  let recs = [];
  try { recs = readFileSync(join(root, ".fanout", "log.jsonl"), "utf8").split("\n").filter(Boolean).map((l) => { try { return JSON.parse(l); } catch { return null; } }).filter(Boolean); } catch { /* none yet */ }
  // On a real project the base moved on while lanes waited for review, and the merge then conflicted.
  if (behind) console.log(`${base} has ${behind} commit(s) the lanes don't. Run \`fanout rehearse\` again before merging: it tests them on ${base} as it is now.`);
  if (live?.running) {
    const cost = Object.values(live.sessions).reduce((a, x) => (a == null || x.costUsd === null ? null : a + (x.costUsd ?? 0)), 0);
    console.log(`run in progress: ${live.phase}, ${mins((Date.now() - Date.parse(live.startedAt)) / 1000)} so far, ${cost == null ? "cost unknown" : `$${cost.toFixed(2)}`} for finished agent runs`);
  }
  for (const kind of ["run", "rehearse"]) {
    const r = recs.findLast((x) => x.kind === kind);
    console.log(`last ${kind}: ${r ? `${r.at.slice(0, 16).replace("T", " ")}  ${r.result ?? ""}` : "none"}`);
  }
  return 0;
}

const mins = (s) => (s == null ? "" : s < 90 ? `${Math.round(s)}s` : `${(s / 60).toFixed(1)}m`);
// .fanout/live.json, written by `fanout run` as it goes. `running` is false once the run finished or its
// process is gone (killed, crashed), so a stale file never reads as a run in progress.
function readLive(root) {
  let live;
  try { live = JSON.parse(readFileSync(join(root, ".fanout", "live.json"), "utf8")); } catch { return null; }
  let alive = false;
  if (live.pid) try { process.kill(live.pid, 0); alive = true; } catch (e) { alive = e.code === "EPERM"; }
  return { ...live, running: alive };
}
function liveCells(x, running) {
  if (!x) return ["-", "-"];
  let state = x.state ?? "-";
  if (x.since) state = running ? `${state} ${mins((Date.now() - x.since) / 1000)}` : `${state}, stopped`;
  return [state, x.costUsd === null ? "?" : x.costUsd == null ? "-" : `$${x.costUsd.toFixed(2)}`];
}
// Every checkout of the repo (main checkout and worktrees, whoever made them: fanout lanes, the desktop
// app's sessions, a human), what each has changed against the base, committed or not, and where two
// collide. Needs no plan. Pairs that share files also get a dry-run merge of their commits
// (git merge-tree, nothing is written), so "conflict" means a real one. Built from a real case: two
// sessions, one in the main checkout with uncommitted edits, one in a worktree, both about to edit footer.php.
export function checkoutOverlap(cwd, base, { activeHours = 24 } = {}) {
  const root = mainRoot(cwd);
  const trees = git(["worktree", "list", "--porcelain"], root).split(/\n\n+/).filter(Boolean).map((b) => ({
    path: b.match(/^worktree (.+)$/m)?.[1], head: b.match(/^HEAD (\w+)$/m)?.[1], branch: b.match(/^branch refs\/heads\/(.+)$/m)?.[1] ?? null,
  })).filter((t) => t.path && t.head && !/[\\/]\.fanout[\\/]rehearse$/.test(t.path));
  const out = [], cutoff = Date.now() / 1000 - activeHours * 3600;
  let idle = 0;
  for (const t of trees) {
    const committed = t.branch === base ? [] : spawnSync("git", ["diff", "--name-only", `${base}...${t.head}`], { cwd: root, encoding: "utf8" }).stdout?.split("\n").filter(Boolean) ?? [];
    const st = spawnSync("git", ["status", "--porcelain", "-uall"], { cwd: t.path, encoding: "utf8" });
    const dirty = (st.stdout ?? "").split("\n").filter(Boolean).map((l) => l.slice(3).replace(/^.* -> /, "").replace(/^"|"$/g, "")).filter((f) => !f.startsWith(".fanout/"));
    const files = [...new Set([...committed, ...dirty])];
    if (!files.length) continue;
    // Old worktrees nobody works in (finished or abandoned sessions) would drown the live ones:
    // a checkout counts only with uncommitted changes or a commit in the last activeHours (null = all).
    const last = Number(spawnSync("git", ["log", "-1", "--format=%ct", t.head], { cwd: root, encoding: "utf8" }).stdout) || 0;
    if (activeHours != null && !dirty.length && last < cutoff) { idle++; continue; }
    const name = t.branch ?? `(detached ${t.head.slice(0, 7)})`;
    out.push({ name, path: t.path, head: t.head, committed, dirty, files, behind: Number(spawnSync("git", ["rev-list", "--count", `${t.head}..${base}`], { cwd: root, encoding: "utf8" }).stdout) || 0 });
  }
  // Stable output: the base's own checkout first, then by name (git lists worktrees by path).
  out.sort((a, b) => (a.name === base ? -1 : b.name === base ? 1 : a.name < b.name ? -1 : a.name > b.name ? 1 : 0));
  const pairs = [];
  for (let i = 0; i < out.length; i++) for (let j = i + 1; j < out.length; j++) {
    const a = out[i], b = out[j], shared = a.files.filter((f) => b.files.includes(f));
    if (!shared.length) continue;
    let conflicts = null;
    if (a.committed.some((f) => shared.includes(f)) && b.committed.some((f) => shared.includes(f)) && a.head !== b.head) {
      const m = spawnSync("git", ["merge-tree", "--write-tree", "--name-only", "--no-messages", a.head, b.head], { cwd: root, encoding: "utf8" });
      conflicts = m.status === 1 ? (m.stdout ?? "").split("\n").slice(1).filter(Boolean) : [];
    }
    pairs.push({ a: a.name, b: b.name, shared, conflicts, uncommitted: shared.filter((f) => a.dirty.includes(f) || b.dirty.includes(f)) });
  }
  return { checkouts: out, pairs, idle };
}

function showOverlap(cwd, base, all) {
  const { checkouts, pairs, idle } = checkoutOverlap(cwd, base, { activeHours: all ? null : 24 });
  const skipped = idle ? ` (${idle} older checkout(s) with no recent work skipped; --all shows them)` : "";
  const claims = liveClaims(cwd, base), on = claimsActive(cwd);
  const claimOf = (branch) => claims.filter((c) => c.branch === branch).map((c) => `claimed: ${c.name}, ${c.task || "no task"}`).join("; ") || (on ? "no claim" : "");
  if (!checkouts.length) {
    console.log(`No active checkout has changes against ${base}${skipped}.`);
    for (const c of claims) console.log(`${c.branch}: claimed ${c.name}, ${c.task || "no task"} (no changes yet)`);
    return 0;
  }
  if (skipped) console.log(skipped.trim().slice(1, -1));
  for (const c of checkouts) { const k = claimOf(c.name); console.log(`${c.name}: ${c.files.length} file(s) changed${c.dirty.length ? ` (${c.dirty.length} uncommitted)` : ""}${c.behind ? `, ${c.behind} commit(s) behind ${base}` : ""}${k ? ` [${k}]` : ""}  ${c.path}`); }
  for (const c of claims.filter((c) => !checkouts.some((k) => k.name === c.branch))) console.log(`${c.branch}: claimed ${c.name}, ${c.task || "no task"} (no changes yet)`);
  if (!pairs.length) { console.log("No overlaps: no file is changed in more than one checkout."); return 0; }
  const list = (fs) => fs.slice(0, 5).join(", ") + (fs.length > 5 ? ` +${fs.length - 5} more` : "");
  for (const p of pairs) {
    console.log(`OVERLAP ${p.a} <-> ${p.b}: ${list(p.shared)}`);
    if (p.conflicts?.length) console.log(`  CONFLICT if merged: ${list(p.conflicts)}`);
    else if (p.conflicts) console.log("  their commits merge cleanly");
    if (p.uncommitted.length) console.log(`  uncommitted, so not merge-checked: ${list(p.uncommitted)}`);
  }
  return pairs.some((p) => p.conflicts?.length) ? 1 : 0;
}

const explicitPlan = (argv) => (argv[1] && !argv[1].startsWith("--") ? argv[1] : null);

function main(argv) {
  const cmd = argv[0] ?? "overlap"; // bare `fanout`: every session, claim and overlap at once
  if (cmd === "guard") return guard(argv);
  if (cmd === "session-start") return sessionStart();
  if (cmd === "notice") return noticeHook();
  if (cmd === "prompt") return promptHook();
  if (cmd === "precheck") return precheckCmd(argv[1]);
  if (cmd === "run") return import("./run.mjs").then((m) => m.cli(argv.slice(1)));
  if (cmd === "demo") return import("./demo.mjs").then((m) => m.demo(argv.slice(1)));
  const cwd = resolve(arg(argv, "--cwd", process.cwd()));
  if (cmd === "precommit") return precommit(cwd);
  if (cmd === "install-git-hook") return installHook(cwd, argv.includes("--force"));
  if (cmd === "status") return showStatus(cwd, arg(argv, "--base") ?? defaultBase(cwd));
  if (cmd === "overlap") return showOverlap(cwd, arg(argv, "--base") ?? repoDefaultBranch(cwd), argv.includes("--all"));
  if (cmd === "log") return showLog(cwd, Number(arg(argv, "--last", "20")), Number(arg(argv, "--days", "7")));
  const SCRIPT = norm(fileURLToPath(import.meta.url));
  if (cmd === "start") return startCmd(cwd, argv.slice(1), arg(argv, "--base") ?? defaultBase(cwd), SCRIPT);
  if (cmd === "done") return doneCmd(cwd, argv);
  if (cmd === "inbox") return inboxCmd(cwd);
  if (cmd === "claim") return claimCmd(cwd, argv.slice(1), arg(argv, "--base") ?? defaultBase(cwd), SCRIPT);
  if (cmd === "claims") return showClaims(cwd, arg(argv, "--base") ?? defaultBase(cwd), argv.includes("--all"));
  if (cmd === "release") return releaseCmd(cwd, argv.slice(1));
  if (cmd === "init") return initCmd(cwd, SCRIPT, installHook, argv);
  if (!["check", "verify", "rehearse"].includes(cmd)) {
    const help = cmd === "--help" || cmd === "-h" || cmd === "help";
    (help ? console.log : console.error)(`usage: fanout [command]
  (no command)                            every session in this repo, what each has claimed and changed, and overlaps
  start "<task>" [files...]               claim this session's task (refused if another session has the same work)
  done                                    test this branch merged with the other sessions' work
  inbox                                   changes other sessions committed since you last looked (agents without hooks)
  demo [--yes] [--record f.svg]           claims and notices with real Claude Code sessions in a throwaway repo (~2 min, ~$0.10)
  run ["goal" | --goal-file f] [--yes]   split a job across agents: plan, agents, rehearse, fix, merge (fanout run --help)
  overlap [--base <branch>] [--all]       same as no command
  init                                    claims on for good in this repo (they also switch on by themselves with 2+ active sessions)
  claim <name> "<task>" [files...]        claim a task by name; the files named are locked for other sessions
  claims [--all]                          what every session has claimed
  release <name> [--to <branch>]          end a claim, or hand it over
  check [plan.md]                         is the plan safe? prints the merge order
  verify [--session name] [--base <b>]    anything outside a session's lane?
  rehearse [--base <branch>] [--test cmd] merge every branch on a scratch copy, test once
  status [--base <branch>]                each session's branch, commits, files, flags, agent state and cost
  log [--last 20]                         past runs and rehearsals
  install-git-hook [--force]              enforce the plan on every commit
  guard                                   the edit hook (installed by the plugin)`);
    return help ? 0 : 2;
  }
  const planPath = explicitPlan(argv) ?? defaultPlan(cwd);
  let text;
  try { text = readFileSync(planPath, "utf8"); } catch { console.error(`No plan at ${planPath}`); return 2; }
  const sessions = parsePlan(text), regen = parseRegen(text);
  if (cmd === "check") {
    const { problems, order } = check(sessions, cwd, regen);
    problems.forEach((p) => console.log(p));
    if (!planSetting(text, "test")) console.log('NOTE no "test:" line above the first "##": rehearse can only check that branches merge, not that they work together.');
    if (sessions.length && !sessions.some((s) => s.check)) console.log(`NOTE no session has a "check:" line. A test can pass on code that doesn't do the job (a lint can't see a dead link); give each session a command that proves its done:.`);
    console.log("Merge order:", order.join(" -> "));
    return problems.length ? 1 : 0;
  }
  if (cmd === "rehearse") {
    const { problems, order } = check(sessions, cwd, regen);
    if (problems.length) { problems.forEach((p) => console.log(p)); console.log("Fix the plan first (fanout check)."); return 1; }
    const t0 = Date.now();
    const { ok, log, testRuns } = rehearse(order, { cwd, base: arg(argv, "--base") ?? defaultBase(cwd), test: arg(argv, "--test") ?? planSetting(text, "test"), regen, checks: sessions });
    log.forEach((l) => console.log(l));
    appendLog(cwd, { kind: "rehearse", sessions: order.length, seconds: Math.round((Date.now() - t0) / 1000), testRuns,
      result: ok ? "pass" : (log.find((l) => /^(BROKE|CONFLICT|REGEN FAILED|CHECK FAILED|FLAKY|BASE FAILS)/.test(l)) ?? "fail").split(":")[0] });
    return ok ? 0 : 1;
  }
  const name = arg(argv, "--session") ?? currentSession(cwd);
  const s = sessions.find((x) => x.name === name);
  if (!s) { console.error(`No session "${name}" in plan. Pass --session or run from a fanout/<name> branch.`); return 2; }
  const base = arg(argv, "--base") ?? defaultBase(cwd), head = arg(argv, "--head", "HEAD");
  const changed = laneChanged(base, head, cwd);
  const contracts = contractChanges(sessions, changed);
  const frozen = contracts.filter((f) => contractOwner(sessions, f).name !== name), evolved = contracts.filter((f) => !frozen.includes(f));
  const generated = changed.filter((f) => regenFor(regen, f));
  const out = verify(s, changed).filter((f) => !contracts.includes(f) && !generated.includes(f));
  out.forEach((f) => console.log(`OUT OF LANE ${name}: ${f}`));
  frozen.forEach((f) => console.log(`CONTRACT CHANGED ${name}: ${f} (exposed by ${contractOwner(sessions, f).name})`));
  evolved.forEach((f) => console.log(`NOTE ${name} changed its exposed file ${f}; sessions that use it should merge ${name} first and be told`));
  generated.forEach((f) => console.log(`GENERATED CHANGED ${name}: ${f} (rebuilt after merging; don't commit it)`));
  console.log(`${name}: ${changed.length} changed, ${out.length} outside its owns, ${frozen.length} contracts changed, ${generated.length} generated`);
  return out.length || frozen.length || generated.length ? 1 : 0;
}

// Files a tool call would write. Claude Code sends file_path / notebook_path; Codex sends
// apply_patch with the patch text in tool_input.command ("*** Update File: path" etc.).
export function editTargets(toolInput = {}) {
  const direct = toolInput.file_path ?? toolInput.notebook_path;
  if (direct) return [direct];
  const patch = typeof toolInput.command === "string" ? toolInput.command : typeof toolInput.input === "string" ? toolInput.input : "";
  return [...patch.matchAll(/^\*\*\* (?:(?:Add|Update|Delete) File|Move to): (.+)$/gm)].map((m) => m[1].trim());
}

// Git and hooks can spell the same directory differently (symlinks, junctions, Windows short names).
// Resolve the nearest existing ancestor so new files and directories work too.
function physicalPath(path) {
  let dir = path;
  for (;;) {
    try { return resolve(realpathSync.native(dir), relative(dir, path)); }
    catch {
      const parent = dirname(dir);
      if (parent === dir) return path;
      dir = parent;
    }
  }
}

function hookRelative(root, path) {
  const rel = norm(relative(physicalPath(root), physicalPath(path)));
  return rel === ".." || rel.startsWith("../") || isAbsolute(rel) ? null : rel;
}

// The plan and this checkout's session, or null when not on a fanout/<name> branch with a plan.
function loadSession(cwd) {
  const name = currentSession(cwd);
  if (!name) return null;
  let text;
  try { text = readFileSync(defaultPlan(cwd), "utf8"); } catch { return null; }
  const sessions = parsePlan(text), s = sessions.find((x) => x.name === name);
  return s ? { sessions, s, regen: parseRegen(text) } : null;
}

// PreToolUse hook (Claude Code and Codex): blocks file edits outside the session's owns, on contracts and on generated files.
// Active only on a fanout/<name> branch with a plan present, so it does nothing in normal work.
function guard() {
  let input = {};
  try { input = JSON.parse(readFileSync(0, "utf8")); } catch { return 0; }
  // Grok Build runs Claude Code hooks but sends camelCase fields (toolInput, transcriptPath): take either.
  const targets = editTargets(input.tool_input ?? input.toolInput);
  if (!targets.length) return 0;
  const cwd = input.cwd ?? process.cwd(), notes = [];
  // The session comes from the checkout the file is in, not the agent's cwd, so a subagent or
  // parallel session working from the main checkout is still held to its lane's plan.
  const why = targets.map((t) => {
    const abs = isAbsolute(t) ? t : resolve(cwd, t);
    let dir = dirname(abs);
    while (!existsSync(dir) && dirname(dir) !== dir) dir = dirname(dir);
    let root;
    try { root = git(["rev-parse", "--show-toplevel"], dir).trim(); } catch { return null; } // not a repo
    const rel = hookRelative(root, abs);
    if (rel === null) return null; // outside the repo: not our business
    // A fanout run's lane follows its plan; any other checkout follows the claims, where they're on.
    const ctx = loadSession(dir);
    if (ctx) return blockReason(ctx.sessions, ctx.s, ctx.regen, rel);
    if (!claimsActive(root)) return null;
    const r = claimReason(root, [rel], { transcript: () => hookTranscript(input) });
    notes.push(...r.notes);
    return r.block;
  }).filter(Boolean);
  why.forEach((w) => console.error("fanout: " + w));
  if (why.length) return 2;
  // Allowed, with a note for the agent (a file another session is also changing).
  if (notes.length) console.log(JSON.stringify({ hookSpecificOutput: { hookEventName: "PreToolUse", additionalContext: notes.join("\n") } }));
  return 0;
}

// With claims on: { block, notes } for this checkout's session changing these files. A session with no
// claim yet gets one (autoClaim: the user's request from its transcript as the task, checked for the same
// work as another session's); a session whose task was refused as duplicate work is stopped. A file another
// session claimed by name is refused; one another session is also editing is allowed with a note, the
// first time. Each file is recorded in the session's edits. Ignored files (build output, node_modules) and
// fanout's own folder are left alone.
export function claimReason(root, rels, { transcript, requireClaim = false, via = "edit" } = {}) {
  const files = rels.filter((f) => !f.startsWith(".fanout/") && spawnSync("git", ["check-ignore", "-q", "--", f], { cwd: root }).status !== 0);
  const branch = branchOf(root);
  if (!files.length || !branch) return { block: null, notes: [] };
  const base = defaultBase(root), live = liveClaims(root, base), script = norm(fileURLToPath(import.meta.url));
  // Locks first: the most useful thing to say, claimed or not.
  const taken = files.map((f) => [f, claimedByOther(live, branch, f)]).filter(([, c]) => c);
  if (taken.length) taken.forEach(([f, c]) => logEvent(root, { kind: "locked", via, session: branch, file: f, owner: c.name }));
  if (taken.length) return { block: taken.map(([f, c]) => `${f} is claimed by session "${c.name}" (branch ${c.branch}: ${c.task || "no task given"}). Leave it to that session: work on something else, or coordinate with it. If that session is finished or abandoned: node "${script}" release ${c.name}`).join("\n"), notes: [] };
  let mine = live.filter((c) => c.branch === branch).sort((a, b) => Date.parse(b.updated ?? b.at) - Date.parse(a.updated ?? a.at))[0];
  // A commit from an agent without hooks, in a repo set up with fanout init: AGENTS.md told it to run fanout start
  // first, and a Codex session given that skipped it and duplicated another's work, so its commit waits for it.
  if (!mine && requireClaim) return { block: `this session (branch ${branch}) hasn't claimed its task. Run first: node "${script}" start "<your task in one line>"
It shows what the other sessions are doing; if one already has your work, don't commit it.
(A person committing by hand, not an agent: git commit --no-verify skips this check.)`, notes: [] };
  const notes = [];
  if (!mine) { const t = typeof transcript === "function" ? transcript() : transcript; mine = autoClaim(root, branch, t ? taskFromTranscript(t) : "", base, live, via); }
  else if (mine.checking) mine = waitChecked(root, mine);
  else if (!mine.refusedAs) {
    // An older claim this one hasn't been compared with: one made at the same moment as it (recheckClaim).
    const rc = recheckClaim(root, mine, live, via);
    if (rc.unchecked.length) notes.push(selfCheckText(rc.unchecked, mine.name, script).trim());
  }
  if (mine.refusedAs?.length) return { block: refusalText(mine, live, script), notes: [] };
  const fresh = files.filter((f) => !(mine.edits ?? []).includes(f));
  // Says what goes wrong and what to run: "keep your change small and compatible" left two one-line additions at
  // the same spot conflicting in 3 of 3 runs; this wording, 0 of 3 (bench/RESULTS.md, "The shared-file note").
  notes.push(...fresh.flatMap((f) => { const o = editedByOthers(live, branch, f); return o.length ? [`fanout: ${f} is also being changed by ${o.map((c) => `session "${c.name}" (branch ${c.branch}: ${c.task || "no task given"})`).join(" and ")}. Two branches that change lines near each other in one file conflict when merged, even one-line additions. Before you commit, check for their committed changes to it (${o.map((c) => `git log HEAD..${c.branch} -- "${f}"`).join("; ")}); if there are any, merge their branch first and resolve the conflict, so the merged code keeps both changes.`] : []; }));
  if (fresh.length) writeState(root, (claims) => {
    const c = claims[mine.name];
    if (!c) return false;
    c.edits = [...new Set([...(c.edits ?? []), ...fresh])]; c.updated = new Date().toISOString();
  }, `fanout: ${mine.name} edits ${fresh.join(", ")}`);
  return { block: null, notes };
}

// SessionStart hook (Claude Code): tells a new session what the others in this repo are doing, before it
// plans anything. Prints nothing when claims are off or nobody else has claimed anything.
function sessionStart() {
  let input = {};
  try { input = JSON.parse(readFileSync(0, "utf8")); } catch { return 0; }
  const cwd = input.cwd ?? process.cwd();
  let root;
  try { root = git(["rev-parse", "--show-toplevel"], cwd).trim(); } catch { return 0; }
  if (loadSession(root) || !claimsActive(root)) return 0;
  const branch = branchOf(root), others = liveClaims(root, defaultBase(root)).filter((c) => c.branch !== branch && !c.refusedAs);
  if (!others.length) return 0;
  const text = `fanout: other sessions are working in this repo right now:\n${others.slice(0, 12).map((c) => `- ${c.name} (branch ${c.branch}): ${c.task || "no task given"}${c.files?.length ? ` [claimed files: ${c.files.join(", ")}]` : ""}`).join("\n")}\n`
    + `Don't do their work. Your task is claimed for you on your first edit, and refused if another session already has the same work.`;
  console.log(JSON.stringify({ hookSpecificOutput: { hookEventName: "SessionStart", additionalContext: text } }));
  logEvent(root, { kind: "told", session: branch, others: others.slice(0, 12).map((c) => c.name), otherTasks: others.slice(0, 12).map((c) => c.task) });
  return 0;
}

// UserPromptSubmit hook (Claude Code): starts the same-work check in the background while the session reads and
// plans, so its first edit doesn't wait for it. Returns at once and prints nothing.
function promptHook() {
  let input = {};
  try { input = JSON.parse(readFileSync(0, "utf8")); } catch { return 0; }
  const cwd = input.cwd ?? process.cwd(), task = cleanTask(input.prompt).slice(0, 600);
  if (task.length < 15 || !existsSync(cwd)) return 0;
  // Every check runs in the background process too: each git call here would hold up the user's message.
  spawn(process.execPath, [fileURLToPath(import.meta.url), "precheck", task], { cwd, detached: true, stdio: "ignore", windowsHide: true }).unref();
  return 0;
}
function precheckCmd(task) {
  let root;
  try { root = git(["rev-parse", "--show-toplevel"], process.cwd()).trim(); } catch { return 0; }
  const branch = branchOf(root);
  if (!branch || loadSession(root) || !claimsActive(root)) return 0;
  const all = Object.values(readState(root).claims);
  if (all.some((c) => c.branch === branch)) return 0;
  precheck(root, branch, task, defaultBase(root));
  return 0;
}

// PostToolUse hook (Claude Code): with claims on, tells the session when another session (or the base branch)
// has committed changes to a file it has read or edited (claims.mjs, notices). Silent otherwise.
function noticeHook() {
  let input = {};
  try { input = JSON.parse(readFileSync(0, "utf8")); } catch { return 0; }
  const cwd = input.cwd ?? process.cwd(), info = repoInfo(cwd);
  if (!info?.branch || !info.claims || info.branch.startsWith(BRANCH_PREFIX) || process.env.FANOUT_NOTICES === "off") return 0;
  const { root, gitDir, common, branch } = info;
  const tool = input.tool_name ?? input.toolName ?? "", ti = input.tool_input ?? input.toolInput ?? {};
  const rel = (p) => hookRelative(root, isAbsolute(p) ? p : resolve(cwd, p));
  const read = tool === "Read" && ti.file_path ? rel(ti.file_path) : null, base = mainBranch(common);
  const edited = /^(Write|Edit|MultiEdit|NotebookEdit)$/.test(tool) ? editTargets(ti).map(rel).filter(Boolean) : [];
  // Edits made through the shell never reach the edit guard. In the desktop app's auto mode sessions edit that
  // way (python, heredocs, cat >>): on a real project with five active checkouts, no session was ever claimed.
  // So after a shell command, files it changed (uncommitted, or committed on this branch) go through the same
  // claim rules after the fact: the first claims the task, a duplicate or a locked file is reported back.
  let block = null;
  const extra = [];
  if (/^(Bash|PowerShell)$/.test(tool)) {
    const r = shellEdits(root, gitDir, base);
    if (r.length) {
      const c = claimReason(root, r, { transcript: () => hookTranscript(input), via: "shell" });
      block = c.block; extra.push(...c.notes); edited.push(...r);
    }
  }
  const text = [...extra, info.notices ? notices(root, gitDir, branch, base, { read, edited, common }) : ""].filter(Boolean).join("\n\n");
  if (block) console.log(JSON.stringify({ decision: "block", reason: `fanout: that command changed files, and ${block}\nUndo your change to these files.` + (text ? `\n\n${text}` : "") }));
  // As feedback the agent must answer, not as added context: with real Sonnet sessions, a notice sent as context
  // reached the session 4 times and was ignored every time; sent this way it was acted on 3 times out of 3.
  else if (text) console.log(JSON.stringify({ decision: "block", reason: text }));
  // What the hook costs per tool call, Node's start included, for fanout log: kept per checkout in its git dir.
  try {
    const f = join(gitDir, "fanout-hook-time.json");
    let t = { calls: 0, ms: 0, max: 0 }; try { t = JSON.parse(readFileSync(f, "utf8")); } catch { /* first call */ }
    const ms = Math.round(process.uptime() * 1000);
    writeFileSync(f, JSON.stringify({ calls: t.calls + 1, ms: t.ms + ms, max: Math.max(t.max, ms) }));
  } catch { /* read-only */ }
  return 0;
}

// Files this checkout has changed that weren't seen at the last check: uncommitted ones, and ones committed on
// its branch since it split from the base. Kept in its git dir, so a shell command that changes nothing costs
// two git calls and no write.
function shellEdits(root, gitDir, base) {
  const file = join(gitDir, "fanout-shell-edits.json");
  let seen = [];
  try { seen = JSON.parse(readFileSync(file, "utf8")); } catch { /* first time */ }
  const all = changedFiles(root, base), fresh = all.filter((f) => !seen.includes(f));
  if (fresh.length) try { writeFileSync(file, JSON.stringify([...seen, ...fresh])); } catch { /* read-only */ }
  return fresh;
}
// Every file this checkout has changed: uncommitted (new ones too), and committed on its branch since the base.
function changedFiles(root, base) {
  const dirty = spawnSync("git", ["status", "--porcelain", "-z", "--untracked-files=all"], { cwd: root, encoding: "utf8" }).stdout ?? "";
  const parts = dirty.split("\0"), files = [];
  for (let i = 0; i < parts.length; i++) { if (parts[i].length < 4) continue; files.push(parts[i].slice(3)); if (/^[RC]/.test(parts[i])) i++; } // a rename's old path follows it
  const committed = spawnSync("git", ["diff", "--name-only", `${base}...HEAD`], { cwd: root, encoding: "utf8" }).stdout ?? "";
  const all = [...new Set([...files, ...committed.split("\n")].map((f) => norm(f.trim())).filter((f) => f && !f.startsWith(".fanout/") && !f.startsWith(".claude/")))];
  return all;
}

// For agents without hooks (Codex and others), the notices a Claude Code session gets after each tool call, on
// demand: fanout inbox, and printed by fanout done and the git hook. null where notices don't apply.
function inboxText(cwd) {
  const info = repoInfo(cwd);
  if (!info?.branch || info.branch.startsWith(BRANCH_PREFIX) || !info.notices || process.env.FANOUT_NOTICES === "off") return null;
  const base = mainBranch(info.common);
  return notices(info.root, info.gitDir, info.branch, base, { edited: changedFiles(info.root, base), common: info.common, all: true });
}
function inboxCmd(cwd) {
  const t = inboxText(cwd);
  console.log(t === null ? "fanout inbox: notices don't apply here (not on a branch, a fanout run lane, or notices are off)." : t || "fanout inbox: nothing new. No other session has committed changes since you last looked.");
  return 0;
}

// fanout done: this branch's commits merged with every other session's that has a live claim, on a scratch
// copy, and the test run once (rehearse, bisecting only on failure). Says whose merge broke it.
function doneCmd(cwd, argv) {
  const root = mainRoot(cwd), branch = branchOf(cwd), base = arg(argv, "--base") ?? defaultBase(cwd);
  const news = inboxText(cwd);
  if (news) console.log(news + "\n");
  if (!branch || branch === base) { console.error(`fanout done: run it in a session's own branch (not ${base}), after committing.`); return 2; }
  let test = arg(argv, "--test") ?? (spawnSync("git", ["config", "--get", "fanout.test"], { cwd, encoding: "utf8" }).stdout ?? "").trim();
  try { if (!test) test = planSetting(readFileSync(defaultPlan(cwd), "utf8"), "test"); } catch { /* no plan */ }
  try { if (!test && JSON.parse(readFileSync(join(root, "package.json"), "utf8")).scripts?.test) test = "npm test"; } catch { /* no package.json */ }
  // First: is this the same work as an older claim it hasn't been compared with (they started at once)?
  const live = liveClaims(root, base), mine = live.filter((c) => c.branch === branch).sort((a, b) => Date.parse(b.updated ?? b.at) - Date.parse(a.updated ?? a.at))[0], script = norm(fileURLToPath(import.meta.url));
  if (mine && !mine.refusedAs) { const rc = recheckClaim(root, mine, live, "done"); if (rc.unchecked.length) console.log(selfCheckText(rc.unchecked, mine.name, script).trim()); }
  if (mine?.refusedAs) { console.error(`fanout done: ${refusalText(mine, live, script)}`); return 1; }
  const ahead = (b) => Number(spawnSync("git", ["rev-list", "--count", `${base}..${b}`], { cwd: root, encoding: "utf8" }).stdout) || 0;
  const others = [...new Set(liveClaims(root, base).filter((c) => c.branch !== branch && c.branch !== base && ahead(c.branch)).sort((a, b) => Date.parse(a.at) - Date.parse(b.at)).map((c) => c.branch))];
  if (git(["status", "--porcelain", "--untracked-files=no"], cwd).trim()) console.log("fanout done: you have uncommitted changes; only commits are tested. Commit first for a full check.");
  if (!ahead(branch)) { console.error(`fanout done: ${branch} has no commits on top of ${base} yet.`); return 2; }
  const { ok, log } = rehearse([...others, branch], { cwd: root, base, test, prefix: "" });
  log.forEach((l) => console.log(l));
  const head = log.find((l) => /^(BROKE after|CONFLICT merging|REGEN FAILED after) /.test(l)) ?? "", who = head.match(/(?:after|merging) (\S+?):?(?:\s|$)/)?.[1];
  if (ok) console.log(`fanout done: ${branch} works with ${others.length ? others.join(", ") : "nothing else yet (no other session has commits)"} on ${base}${test ? ` (\`${test}\` passes)` : " (no test command: merges only; set one with git config fanout.test \"<cmd>\")"}.`);
  else if (who === branch) console.log(`fanout done: merging ${branch} after ${others.join(", ") || base} breaks (above). Fix it on your branch.`);
  else if (who) console.log(`fanout done: it already breaks at ${who}, before your branch is merged (above): that session's work, not yours.`);
  return ok ? 0 : 1;
}

// git pre-commit hook: the same rules on staged files, so agents outside Claude Code are held to the plan
// (on a fanout/* lane) or the claims (elsewhere, when they're on) too.
function precommit(cwd) {
  const ctx = loadSession(cwd);
  const staged = git(["diff", "--cached", "--name-only"], cwd).split("\n").filter(Boolean);
  if (!ctx) {
    if (!claimsActive(cwd)) return 0;
    const { block, notes } = claimReason(cwd, staged, { requireClaim: claimsOn(cwd), via: "commit" });
    notes.forEach((n) => console.error(n));
    const news = block ? null : inboxText(cwd);
    if (news) console.error(news);
    if (block) block.split("\n").forEach((w) => console.error("fanout: " + w));
    return block ? 1 : 0;
  }
  const why = staged.map((f) => blockReason(ctx.sessions, ctx.s, ctx.regen, f)).filter(Boolean);
  why.forEach((w) => console.error("fanout: " + w));
  return why.length ? 1 : 0;
}

const HOOK_MARK = "# fanout pre-commit";
function installHook(cwd, force) {
  let path;
  try { path = resolve(cwd, git(["rev-parse", "--git-path", "hooks/pre-commit"], cwd).trim()); }
  catch { console.error("Not a git repo."); return 2; }
  if (existsSync(path) && !readFileSync(path, "utf8").includes(HOOK_MARK) && !force) {
    console.error(`${path} already exists and isn't fanout's. Add "node <fanout.mjs> precommit" to it, or pass --force to replace it.`);
    return 1;
  }
  const script = norm(fileURLToPath(import.meta.url));
  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, `#!/bin/sh
${HOOK_MARK}
case "$(git branch --show-current)" in fanout/*) ;; *) [ "$(git config --get fanout.claims)" = true ] || exit 0 ;; esac
script='${script}'
[ -f "$script" ] || { echo "fanout: $script is gone (plugin updated?). Run: node <new fanout.mjs> install-git-hook" >&2; exit 1; }
exec node "$script" precommit
`);
  chmodSync(path, 0o755);
  console.log(`Installed ${path}. Commits on fanout/* branches now follow the plan, and with claims on (fanout init) every other branch follows the claims, whatever agent makes them.`);
  return 0;
}

// Run when executed directly, including through an npm/npx bin link (argv[1] is then the link).
const isMain = () => { try { return import.meta.url === pathToFileURL(realpathSync(process.argv[1])).href; } catch { return false; } };
if (isMain()) Promise.resolve(main(process.argv.slice(2))).then((code) => process.exit(code));
