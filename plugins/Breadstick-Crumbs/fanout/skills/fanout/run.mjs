// fanout run: the whole fan-out as one command.
//   fanout run ["goal" | --goal-file TASKS.md] [--yes] [--agent claude|codex|"<cmd>"] [--model m] [--session-model m] [--budget usd] [--fixes 2] [--max-sessions 4] [--full-tests] [--no-draft] [--review] [--mix] [--no-merge]
//
// 1. Plan: uses .fanout/plan.md if it exists. A goal written as "## name" sections with the files in
//    backticks is drafted into a plan without AI (draft.mjs); an agent writes the contract files and
//    checks the names the draft flags (all of the plan with --review), and fanout tests and commits them. Otherwise a coordinator agent writes the
//    plan from the goal and the plan rules (plannerPrompt), and commits the contract files.
// 2. Approve: shows the plan once (skip with --yes).
// 3. Lanes: one agent per session, in parallel, each in .fanout/lanes/<name> on branch fanout/<name>.
//    Their work is committed for them; files the plan forbids are reverted. A session that builds on
//    others is tested against their branches as soon as they and it are done (earlyTest), and a failure
//    goes straight back to it. --mix puts the sessions others build on in Claude, the rest in Codex.
// 4. Rehearse: merge everything on a scratch copy and test. A break goes back to the lane that caused
//    it, which fixes its own branch, with the branches merged ahead of it brought in first (bringIn).
//    A lane that fails --fixes times stops the run for a human.
// 5. Merge into the base branch in order, rebuild generated files, test once more.
//
// Agents: "claude" and "codex" run headless; anything else is a shell command that gets the brief on
// stdin and runs in the lane's folder, so any CLI agent works. A session can pick its own with "agent:".
import { spawn, execFileSync, spawnSync } from "node:child_process";
import { readFileSync, existsSync, appendFileSync, mkdirSync, writeFileSync, rmSync } from "node:fs";
import { createInterface } from "node:readline/promises";
import { join, dirname } from "node:path";
import { tmpdir } from "node:os";
import { fileURLToPath } from "node:url";
import { parsePlan, parseRegen, planSetting, check, rehearse, blockReason, mainRoot, appendLog, matches, ownsFile, contractOwner, failureLines, runPlanCmd, copyIncludes } from "./fanout.mjs";
import { draftPlan, jsExports } from "./draft.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const SCRIPT = join(HERE, "fanout.mjs");
const WIN = process.platform === "win32";

const git = (cwd, ...a) => {
  const r = spawnSync("git", a, { cwd, encoding: "utf8" });
  return { ok: r.status === 0, out: `${r.stdout ?? ""}${r.stderr ?? ""}` };
};
const tail = (s, n = 20) => s.trimEnd().split("\n").slice(-n).join("\n");
const sh = (cmd, cwd) => {
  const r = spawnSync(cmd, { cwd, shell: true, encoding: "utf8" });
  return { ok: r.status === 0, out: `${r.stdout ?? ""}${r.stderr ?? ""}` };
};
// The plan's own commands (test:, check:, regen) run in sh syntax, in Git's bash on Windows (planShell).
const psh = (cmd, cwd) => { const r = runPlanCmd(cmd, cwd); return { ok: r.status === 0, out: `${r.stdout ?? ""}${r.stderr ?? ""}` }; };
const q = (s) => (WIN ? `"${s}"` : `'${s.replaceAll("'", `'\\''`)}'`);

// Binaries can be swapped (tests point these at a fake agent).
const bin = (name) => process.env[`FANOUT_${name.toUpperCase()}_BIN`] || name;

// Sign-in check before any agent runs. A signed-out CLI otherwise fails every agent one by one (seen on the
// benchmark: each Claude agent ended with "OAuth session expired" and the run went on to a meaningless score).
// Returns one line saying what to do, or null. API-key and cloud-provider setups don't use the CLI's login,
// and output the check can't read is let through rather than blocking a CLI that answers differently.
const signedIn = {};
export function signInProblem(kinds) {
  for (const k of new Set(kinds)) {
    if (k === "claude" && !(process.env.ANTHROPIC_API_KEY || process.env.CLAUDE_CODE_USE_BEDROCK || process.env.CLAUDE_CODE_USE_VERTEX)) {
      signedIn.claude ??= (() => {
        const r = sh(`${bin("claude")} auth status`);
        try { return JSON.parse(r.out.slice(r.out.indexOf("{"))).loggedIn === true; } catch { return true; }
      })();
      if (!signedIn.claude) return "claude is not signed in (`claude auth status`): run `claude auth login`, then run again.";
    }
    if (k === "codex") {
      signedIn.codex ??= sh(`${bin("codex")} login status`).ok;
      if (!signedIn.codex) return "codex is not signed in (`codex login status` failed): run `codex login`, then run again.";
    }
  }
  return null;
}

// Runs one agent with the prompt on stdin. Never throws; returns cost, tokens, seconds, any error and
// the agent's session id. With `resume` (a session id from an earlier run) it continues that session
// with just `prompt`; if that fails it starts fresh with `fallbackPrompt`.
export async function runAgent({ resume, fallbackPrompt, ...opts }) {
  if (!resume) return withSettingsFallback({ ...opts, prompt: fallbackPrompt ?? opts.prompt });
  const r = await runOnce({ ...opts, resume });
  if (!r.error) return r;
  const fresh = await withSettingsFallback({ ...opts, prompt: fallbackPrompt ?? opts.prompt });
  fresh.seconds += r.seconds; fresh.inTokens += r.inTokens; fresh.outTokens += r.outTokens;
  if (fresh.costUsd != null && r.costUsd != null) fresh.costUsd += r.costUsd;
  return fresh;
}

// Headless Claude startup cost, trivial "say ok" call through `claude -p` with the flags below:
//   before (default tool set): ~39k input tokens, $0.31 cold cache / $0.08 warm
//   --tools Read,Edit,Write,Glob,Grep,Bash: ~8.6k input tokens, $0.03 cold / $0.002 warm
// The built-in tool schemas (Task, WebFetch, notebook, cron, ...) were most of that. --allowedTools still
// limits Bash to node/npm/npx(/git). --setting-sources and --disable-slash-commands made no measurable
// difference here, and --bare needs an API key, so they are not used.
const CLAUDE_TOOLS = "Read,Edit,Write,Glob,Grep,Bash";
// Read-only shell tools agents reach for (piping test output to tail, listing files). Without them each
// attempt is refused and costs a turn. Writes still go through Edit/Write, where the guard checks them.
const READ_ONLY_BASH = ["cd", "ls", "cat", "head", "tail", "grep", "wc", "pwd", "echo"].map((c) => `Bash(${c}:*)`);
// Session agents start with the project's settings only, not the user's own: personal hooks and plugins
// run on every agent and tool call (measured here: a trivial call went from 9s to 15s and doubled its
// tokens). FANOUT_USER_SETTINGS=1 keeps them.
const settingSources = (userSettings) => (process.env.FANOUT_USER_SETTINGS || userSettings ? [] : ["--setting-sources", "project,local"]);

// fanout's edit guard, as a plain hook in a settings file passed with --settings, so every session agent
// has it whatever the user has installed. (Loading fanout with --plugin-dir would also bring the guard,
// but Claude Code then protects the plugin's own files: agents working on a checkout of fanout itself
// could not edit anything, and said nothing.)
let guardFile = null;
function guardSettings() {
  if (!guardFile) {
    guardFile = join(tmpdir(), `fanout-guard-${process.pid}.json`);
    const hook = { type: "command", command: `node "${SCRIPT.replaceAll("\\", "/")}" guard` };
    writeFileSync(guardFile, JSON.stringify({ hooks: { PreToolUse: [{ matcher: "Write|Edit|NotebookEdit|apply_patch", hooks: [hook] }] } }));
  }
  return ["--settings", q(guardFile.replaceAll("\\", "/"))];
}

// Some setups keep what Claude needs to run at all in the user's settings (Bedrock or Vertex, a proxy, an
// API key helper). If a lean start fails before doing any work, run once more with the user's settings.
async function withSettingsFallback(opts) {
  const r = await runOnce(opts);
  if ((opts.agent ?? "claude") !== "claude" || process.env.FANOUT_USER_SETTINGS || !r.error || r.turns > 0) return r;
  const again = await runOnce({ ...opts, userSettings: true });
  again.fellBack = true;
  again.seconds += r.seconds;
  if (again.costUsd != null && r.costUsd != null) again.costUsd += r.costUsd;
  return again;
}

// The plan's own commands (test:, check:) are allowed exactly as written, so a session can run them
// before it finishes (on a real project the test was `bash tools/check-theme.sh`, which agents were
// refused). Commands with quotes or commas are left out: they can't go through --allowedTools safely.
export const allowCommands = (cmds) => cmds.filter((c) => c && !/["',]/.test(c)).map((c) => `Bash(${c})`);

function runOnce({ agent = "claude", cwd, prompt, model, budget, plugin = false, allowGit = false, allow = [], resume, userSettings = false }) {
  // Only Claude reports a dollar cost; for any other agent it is unknown (null), not zero.
  const rec = { agent, seconds: 0, costUsd: agent === "claude" ? 0 : null, inTokens: 0, outTokens: 0, error: null, sessionId: null };
  const t0 = Date.now();
  let cmd;
  if (agent === "claude") {
    const tools = ["Read", "Edit", "Write", "Glob", "Grep", "Bash(node:*)", "Bash(npm:*)", ...READ_ONLY_BASH, ...(allowGit ? ["Bash(git:*)"] : []), ...allowCommands(allow)];
    const sources = settingSources(userSettings);
    cmd = [bin("claude"), "-p", ...(resume ? ["--resume", resume] : []), "--tools", CLAUDE_TOOLS, "--permission-mode", "acceptEdits", "--allowedTools", q(tools.join(",")), "--output-format", "stream-json", "--verbose",
      "--strict-mcp-config", ...sources, ...guardSettings(), ...(model ? ["--model", model] : []), ...(budget ? ["--max-budget-usd", budget] : [])].join(" ");
  } else if (agent === "codex") {
    // Codex sessions run on low reasoning effort: on the sheet benchmark they took 165-201s against
    // 287-611s at Codex's default, with the same hidden-test score. FANOUT_CODEX_EFFORT (minimal|low|medium|
    // high) overrides it; "default" leaves Codex's own setting. FANOUT_CODEX_TIER sets its service tier
    // ("fast" = Codex's Fast tier, service_tier=priority: about a fifth quicker there, at more usage).
    const effort = (process.env.FANOUT_CODEX_EFFORT ?? "low") === "default" ? null : process.env.FANOUT_CODEX_EFFORT ?? "low", tier = process.env.FANOUT_CODEX_TIER === "fast" ? "priority" : process.env.FANOUT_CODEX_TIER;
    const conf = (k, v) => (v && /^\w+$/.test(v) ? ["-c", `${k}=${v}`] : []);
    cmd = [bin("codex"), "exec", "--json", "-s", "workspace-write", "--skip-git-repo-check", "-C", q(cwd), ...(model ? ["-m", model] : []),
      ...conf("model_reasoning_effort", effort), ...conf("service_tier", tier), ...(resume ? ["resume", resume] : [])].join(" ");
  } else cmd = agent;
  return new Promise((done) => {
    const p = spawn(cmd, { cwd, shell: true });
    let out = "";
    p.stdout.on("data", (d) => (out += d));
    p.stderr.on("data", (d) => (out += d));
    p.stdin.on("error", () => {});
    p.stdin.end(prompt);
    p.on("close", (code) => {
      rec.seconds = Math.round((Date.now() - t0) / 1000);
      try {
        if (agent === "claude") {
          // stream-json: one event per line, the last one the result. The tool calls in between show
          // where an agent's time goes (turns, reads, searches, test runs).
          const events = out.split("\n").filter((l) => l.startsWith("{")).map((l) => { try { return JSON.parse(l); } catch { return null; } }).filter(Boolean);
          const j = events.findLast((e) => e.type === "result") ?? JSON.parse(out.slice(out.indexOf("{")));
          const u = j.usage ?? {};
          rec.sessionId = j.session_id ?? null;
          rec.costUsd = j.total_cost_usd ?? 0;
          rec.inTokens = (u.input_tokens ?? 0) + (u.cache_read_input_tokens ?? 0) + (u.cache_creation_input_tokens ?? 0);
          rec.outTokens = u.output_tokens ?? 0;
          rec.turns = j.num_turns ?? null;
          rec.modelSeconds = j.duration_api_ms != null ? Math.round(j.duration_api_ms / 1000) : null;
          rec.tools = {};
          for (const e of events) for (const c of e.type === "assistant" ? e.message?.content ?? [] : [])
            if (c.type === "tool_use") (rec.tools[c.name] ??= []).push(c.input?.file_path ?? c.input?.pattern ?? c.input?.command ?? "");
          if (process.env.FANOUT_TRACE_DIR) writeFileSync(join(process.env.FANOUT_TRACE_DIR, `${Date.now()}-${(rec.sessionId ?? "agent").slice(0, 8)}.jsonl`), out);
          if (j.is_error) rec.error = String(j.result ?? j.subtype).slice(0, 200);
        } else if (agent === "codex") {
          for (const line of out.split("\n")) {
            if (!line.startsWith("{")) continue;
            const e = JSON.parse(line);
            if (e.type === "thread.started" && e.thread_id) rec.sessionId = e.thread_id;
            if (e.type === "turn.completed" && e.usage) { rec.inTokens += e.usage.input_tokens ?? 0; rec.outTokens += e.usage.output_tokens ?? 0; }
            if (e.type === "turn.failed") rec.error = JSON.stringify(e.error ?? e).slice(0, 200);
          }
        }
      } catch { rec.error = `exit ${code}: ${tail(out, 3)}`.slice(0, 300); }
      if (code !== 0 && !rec.error) rec.error = `exit ${code}: ${tail(out, 3)}`.slice(0, 300);
      done(rec);
    });
  });
}

// Starts one agent per item, a moment apart. Launching several headless Claude agents in the same instant
// sometimes left their shells without PATH ("npm: command not found"), and each agent then lost turns.
export const staggered = (items, fn, gapMs = Number(process.env.FANOUT_STAGGER_MS ?? 1500)) =>
  Promise.all(items.map((x, i) => new Promise((r) => setTimeout(r, i * gapMs)).then(() => fn(x))));

// Uncommitted files in a checkout (changed, deleted or new, not ignored), outside .fanout/.
const changedPaths = (cwd) => [...new Set(git(cwd, "ls-files", "-z", "--modified", "--deleted", "--others", "--exclude-standard").out.split("\0"))]
  .filter((f) => f && !f.startsWith(".fanout/"));

// Commits just these paths in the main checkout. Other sessions may be working there too: `git add -A`
// would sweep their uncommitted files into fanout's commit, and `commit -- <paths>` leaves anything
// they staged out of it as well.
export function commitPaths(root, paths, msg) {
  if (!paths.length) return false;
  git(root, "add", "-A", "--", ...paths);
  return git(root, "commit", "-qm", msg, "--", ...paths).ok;
}

// What fanout itself writes in the main checkout: the planner's contracts and shared changes go in files
// some session owns (a contract is in its owner's owns:), and regen rebuilds generated files. A file
// outside all of those was written by someone else.
export const fanoutPaths = (paths, sessions, regen) =>
  paths.filter((f) => sessions.some((s) => ownsFile(s, f)) || regen.some((g) => g.paths.some((p) => matches(p, f))));

// Stages a lane's work, reverts files the plan forbids it to change, commits the rest.
export function commitLane(wt, sessions, s, regen, msg) {
  git(wt, "add", "-A");
  const staged = git(wt, "diff", "--cached", "--name-only").out.split("\n").filter(Boolean);
  const reverted = [];
  for (const f of staged) {
    if (!blockReason(sessions, s, regen, f)) continue;
    reverted.push(f);
    git(wt, "reset", "-q", "--", f);
    if (git(wt, "cat-file", "-e", `HEAD:${f}`).ok) git(wt, "checkout", "--", f); else git(wt, "clean", "-fq", "--", f);
  }
  const c = git(wt, "commit", "-qm", msg);
  return { committed: c.ok, reverted };
}

// Before a fix round, merges into the lane's branch every branch merged ahead of it, so its own checkout has
// the real code it builds on instead of the contract stubs, and the plan's test reproduces the break there.
// On the sheet benchmark the fix agents had only the stubs and spent 12-15 of their 17-18 commands
// rebuilding a merged copy by hand; the fixes themselves were one edit. A branch that conflicts is left out.
export function bringIn(wt, order, name, regen) {
  const merged = [], conflicted = [];
  for (const o of order.slice(0, Math.max(0, order.indexOf(name)))) {
    const b = `fanout/${o}`;
    if (!git(wt, "rev-parse", "--verify", "--quiet", b).ok || git(wt, "merge-base", "--is-ancestor", b, "HEAD").ok) continue;
    if (git(wt, "merge", "--no-ff", "--no-edit", "-m", `fanout: merge ${o} into ${name} to fix against it`, b).ok) merged.push(o);
    else { git(wt, "merge", "--abort"); conflicted.push(o); }
  }
  if (merged.length) for (const g of regen) psh(g.cmd, wt);
  return { merged, conflicted };
}

// The sessions each session builds on: those exposing what it uses, the ones it is "after", and theirs in
// turn. All of them merge ahead of it.
export function dependencies(sessions) {
  const direct = Object.fromEntries(sessions.map((s) => [s.name, new Set([...s.after,
    ...s.uses.map((u) => contractOwner(sessions.filter((x) => x !== s), u)?.name).filter(Boolean)])]));
  const all = (n, seen = new Set()) => { for (const d of direct[n] ?? []) if (!seen.has(d)) { seen.add(d); all(d, seen); } return seen; };
  return Object.fromEntries(sessions.map((s) => [s.name, [...all(s.name)]]));
}

// --mix: Claude for the sessions others build on, Codex for the rest. On the sheet benchmark Codex
// sessions took 2-3x as long as Claude ones (165-201s on low effort), so they go where nothing waits on
// them; the Claude sessions on the chain the others build on ran at full speed with at most three of them
// (six Claude sessions at once ran at about half speed). Above three, the sessions with the most sessions
// built on them stay in Claude. Claude slots left over go to the other sessions in plan order: on a
// four-session sheet plan only one session had others building on it, and one Claude + three Codex took
// 5m 04s against 3m 59s for four Claude sessions. A session's own agent: wins (agent: claude takes a slot).
export const MIX_CLAUDE_MAX = 3;
export function mixAgents(sessions, maxClaude = MIX_CLAUDE_MAX) {
  const deps = dependencies(sessions), free = sessions.filter((s) => !s.agent);
  const dependents = (s) => sessions.filter((x) => deps[x.name].includes(s.name)).length;
  const ranked = [...free.filter((s) => dependents(s) > 0).sort((a, b) => dependents(b) - dependents(a)), ...free.filter((s) => dependents(s) === 0)];
  const claude = ranked.slice(0, Math.max(0, maxClaude - sessions.filter((s) => s.agent === "claude").length)).map((s) => s.name);
  return Object.fromEntries(sessions.map((s) => [s.name, s.agent || (claude.includes(s.name) ? "claude" : "codex")]));
}

// Which finished sessions are ready for an early test (earlyTest): those with dependencies, once each of
// them is settled. A session with none settles when it finishes; one with some, after its own early test
// (and fix), so a session further down a chain is tested against the fixed code. done() and settle()
// return the sessions that became ready, each once.
export function readyTracker(sessions) {
  const deps = dependencies(sessions), done = new Set(), settled = new Set(), started = new Set();
  const ready = () => {
    for (const s of sessions) if (done.has(s.name) && !deps[s.name].length) settled.add(s.name);
    const r = sessions.filter((s) => deps[s.name].length && done.has(s.name) && !started.has(s.name) && deps[s.name].every((d) => settled.has(d)));
    r.forEach((s) => started.add(s.name));
    return r;
  };
  return { done: (n) => { done.add(n); return ready(); }, settle: (n) => { settled.add(n); return ready(); } };
}

// A finished session's test against the finished sessions it builds on, before rehearse. On the sheet
// benchmark recalc broke against formula's real code in about 3 of 10 four-session runs, found only by
// rehearse once every session was done; a fix round then cost 21-49s more. Here the sessions merged ahead
// of it are brought into its branch (bringIn) as soon as they and it are done, and the plan's test runs
// in its checkout while the other sessions still work. No agent runs unless it fails. Only the test, not
// the session's check:, which is about the fully merged code. Returns null when nothing new was merged.
export function earlyTest(wt, order, name, regen, test) {
  if (!test) return null;
  const before = git(wt, "rev-parse", "HEAD").out.trim();
  const { merged, conflicted } = bringIn(wt, order, name, regen);
  if (!merged.length) return null;
  const r = psh(test, wt);
  // A pass leaves nothing to fix: the branch goes back to the session's own commits (rehearse merges them
  // all anyway), without what the test and the regen wrote. A failure keeps the merges for the fix.
  if (r.ok) { git(wt, "reset", "-q", "--hard", before); git(wt, "clean", "-fdq"); }
  return { ok: r.ok, merged, conflicted, out: r.out };
}

// Contracts a session builds against are pasted into its brief when they're small, so it doesn't spend
// turns reading them (each turn resends the whole conversation). Larger ones are just named.
const CONTRACT_INLINE_BYTES = 8000;
function inlineContracts(s, root) {
  if (!root) return "";
  const files = s.uses.filter((u) => !/[*?{]/.test(u) && existsSync(join(root, u)));
  const texts = files.map((f) => [f, readFileSync(join(root, f), "utf8")]);
  if (!texts.length || texts.reduce((n, [, t]) => n + t.length, 0) > CONTRACT_INLINE_BYTES) return "";
  return "Their current contents (no need to read them again):\n" + texts.map(([f, t]) => `--- ${f}\n${t.trimEnd()}`).join("\n");
}

// With a drafted plan, a session only gets its own sections of the goal, but what a contract's functions
// must do is written in the owner's. On the sheet benchmark recalc-table passed formula text with its
// leading "=" to parseFormula, which formula's section says takes the text without it; the stub it built
// against had only the signature, and its short tests didn't call it, so the early test and rehearse
// passed and four hidden tests failed. So the owner's lines naming a contract's exports are added to the
// brief, without AI.
export function contractSpecLines(s, sessions, specs, root) {
  const out = [];
  for (const f of s.uses.filter((u) => !/[*?{]/.test(u) && existsSync(join(root ?? "", u)))) {
    const owner = contractOwner(sessions.filter((x) => x !== s), f);
    if (!owner || !specs?.[owner.name]) continue;
    const src = readFileSync(join(root, f), "utf8");
    const names = f.endsWith(".php") ? [...src.matchAll(/^function\s+&?\s*([A-Za-z_]\w*)\s*\(/gm)].map((m) => m[1]) : jsExports(src);
    if (!names.length) continue;
    const named = new RegExp(`(?<![\\w$])(?:${names.map((n) => n.replace(/\$/g, "\\$")).join("|")})(?![\\w$])`);
    const spec = specs[owner.name], body = spec.slice(Math.max(0, spec.search(/^## /m))); // not the shared opening text
    const lines = body.split("\n").filter((l) => named.test(l)).slice(0, 30);
    if (lines.length) out.push(`What the goal says about ${f} (from ${owner.name}'s part; build against exactly this):\n${lines.join("\n")}`);
  }
  return out.join("\n");
}

// shortTests: sessions keep their own tests short, since rehearse runs the full test command on the merged
// branches. On the sheet benchmark it cut the sessions' cost by a fifth (Sonnet) to a third (Haiku).
export function brief(s, sessions, regen, test, note = "", root = null, { shortTests = false } = {}) {
  const others = sessions.filter((x) => x !== s).map((x) => x.name);
  return [
    `You are session "${s.name}" of a parallel fan-out. ${others.length ? `Other agents are working on ${others.join(", ")} at the same time.` : ""}`,
    `Task: ${s.task || s.done || s.name}`,
    s.done ? `Done when: ${s.done}` : "",
    s.check ? `After all branches merge, this must pass: \`${s.check}\`.` : "",
    `You may change only: ${s.owns.join(", ")}. Edits anywhere else are refused or reverted.`,
    s.uses.length ? `Shared interfaces you build against (frozen: read them, don't edit them): ${s.uses.join(", ")}.` : "",
    inlineContracts(s, root),
    regen.length ? `Generated files (${regen.flatMap((r) => r.paths).join(", ")}) are rebuilt after merging; you may run the generator to test, but your changes to them are discarded.` : "",
    test ? `Run \`${test}\` before you finish.` : "",
    shortTests ? "Keep your own tests short: at most 3, for your main behaviour, unless the task itself is about tests. All branches are merged and tested together after you finish." : "",
    "Don't commit: your work is committed for you. Read only the files you need.",
    note,
  ].filter(Boolean).join("\n");
}

const log = (...a) => console.log("fanout:", ...a);

// The planner gets the plan rules and the repo's file list up front instead of reading the whole skill
// and exploring (it took 17 turns that way on the library benchmark). It reads only the code it needs
// to write the contracts.
// When draftPlan wrote the plan, an agent writes the contract files and looks at the names the draft
// flagged (a session using something from a file another session owns). With `full` (--review) it reviews
// the whole plan instead: on the sheet benchmark that took 76s against 26s for contracts alone, and the
// flags caught the one hidden dependency it found on the library task. Running the tests and committing
// are left to fanout (contractsReady, then the leftover commit), which saves the planner's turns for them.
export function contractsPrompt({ goal, base, plan, maxSessions = 4, flags = [], full = false }) {
  const fix = `Change the plan only where it's wrong. Keep at most ${maxSessions} sessions. If you change it, run the check until it reports no problems.`;
  const steps = [
    full ? `Review the plan against the goal and the code. The draft only knows the files the goal names, so look for what it can't see: a task that changes existing behaviour without naming the file (find where that code lives, and give the file to that session or make it a shared contract), a session whose task needs a file another session owns, a missing uses/exposes, a file in the wrong session. ${fix}`
      : flags.length ? `The draft found sessions whose spec names something defined in a file another session owns:\n${flags.map((f) => `- ${f.session}: \`${f.name}\` (${f.file}, owned by ${f.owner})`).join("\n")}\nFor each, read the spec and that code. If the session only calls it as it is, leave it. If the goal needs it changed for that session, make that change on ${base} now as a small shared change that keeps the tests passing, or give the file to that session in the plan. ${fix}` : "",
    /exposes:/.test(plan) ? `The plan exposes files: write each one on ${base} as a working interface the other sessions can build against: the real module with its exports and signatures, and bodies that throw "not implemented" where the work belongs to a session. Read only the code you need for that.` : "",
  ].filter(Boolean);
  return `fanout drafted .fanout/plan.md for the goal below from the goal's sections, without AI. It passes \`node "${SCRIPT}" check\`. Do this, then stop:

${steps.map((s, i) => `${i + 1}. ${s}`).join("\n")}

Don't implement the tasks, run the tests or commit: fanout tests the contracts and commits them.

The plan:
${plan}

Goal: ${goal}`;
}

// After the contracts are written: rebuild generated files and run the plan's test on the base branch.
export function contractsReady(root, text) {
  for (const g of parseRegen(text)) psh(g.cmd, root);
  const test = planSetting(text, "test");
  return test ? psh(test, root) : { ok: true, out: "" };
}

// maxSessions: above about four agents writing at once, one account's agents slow each other down
// (sheet benchmark: three lanes ran at full speed, six at about a third of it).
export function plannerPrompt({ goal, base, root, extra = "", maxSessions = 4 }) {
  const files = git(root, "ls-files").out.split("\n").filter(Boolean);
  let list = files.join("\n");
  if (files.length > 300) {
    // Too many to list: one line per folder with its file count, then the top-level files.
    const counts = new Map(), top = [];
    for (const f of files) {
      const i = f.lastIndexOf("/");
      if (i < 0) top.push(f); else counts.set(f.slice(0, i), (counts.get(f.slice(0, i)) ?? 0) + 1);
    }
    const byPath = (a, b) => (a < b ? -1 : a > b ? 1 : 0);
    list = `${files.length} files, summarised by folder:\n` + [...counts].sort(([a], [b]) => byPath(a, b)).map(([d, n]) => `${d}/ (${n} files)`).join("\n")
      + `\nTop-level files:\n` + top.sort(byPath).join("\n");
  }
  return `Plan a parallel fan-out for the goal below, then stop. The fanout script is ${SCRIPT} (run it with node).

1. Write .fanout/plan.md in exactly this shape:

test: <the project's full test command>
regen: <generated paths> via <command>      (one line per set of generated files several sessions would touch; omit if none)

## <session-name>
owns: <paths or globs only this session may change>
task: <one line: what this session builds>
done: <how to tell it is finished>
check: <a command that exits 0 only when done: holds on the merged code: a grep, a script, a request>
exposes: <files of its own that other sessions build against>   (optional)
uses: <exposed files from other sessions it builds against>      (optional)

Rules: every file has at most one owner. Keep sessions few, substantial and independent; if the goal is small, use one session. Use at most ${maxSessions} sessions: group related tasks into one session rather than giving each its own, because more agents running at once slow each other down. Anything several sessions need (shared types, function signatures, changes to a shared module) belongs to one owner and is listed under its exposes and the others' uses.

2. Run \`node "${SCRIPT}" check\` and fix the plan until it reports no problems and no NOTE.
3. If anything is exposed, write those files on ${base} now as working interfaces or stubs the other sessions can build against, run the tests, and commit ("fanout: contracts") just the files you wrote (\`git add <file>...\`, not \`git add -A\`: others may be working in this checkout). Don't implement the rest of the tasks, create worktrees or start sessions: that happens next. Treat the plan as approved.
${extra}
Files in the repository:
${list}

Goal: ${goal}`;
}

// The common options only; the README's Options section has the rest.
export const RUN_HELP = `usage: fanout run ["goal" | --goal-file TASKS.md] [options]

Plans the work, runs one agent per session in parallel, tests their branches together, sends each break
back to the session that caused it, and merges into the current branch. With no goal it uses .fanout/plan.md.

  --yes                 start without asking to approve the plan
  --agent <a>           claude (default), codex, or any command that reads the brief on stdin
  --no-merge            stop when everything passes, before merging
  --session-model <m>   model for the sessions (e.g. haiku); --model sets the planner's

More: --mix, --max-sessions 4, --budget <usd>, --fixes 2, --full-tests, --review, --no-draft
(README, "Options").`;

export async function cli(argv) {
  const flag = (f) => argv.includes(f);
  if (flag("--help") || flag("-h")) { console.log(RUN_HELP); return 0; }
  const opt = (f, d) => { const i = argv.indexOf(f); return i >= 0 ? argv[i + 1] : d; };
  const goalFile = opt("--goal-file");
  const goal = argv[0] && !argv[0].startsWith("--") ? argv[0] : goalFile && existsSync(goalFile) ? readFileSync(goalFile, "utf8") : null;
  const defaultAgent = opt("--agent", "claude"), model = opt("--model"), budget = opt("--budget");
  // Sessions can run on a cheaper model than the planner: a session's own "model:" wins, then --session-model, then --model.
  const sessionModel = opt("--session-model"), modelFor = (s) => s.model || sessionModel || model;
  const maxFixes = Number(opt("--fixes", "2")), maxSessions = Number(opt("--max-sessions", "4")), shortTests = !flag("--full-tests");
  const root = mainRoot(process.cwd());
  const base = git(root, "branch", "--show-current").out.trim();
  if (!base) { console.error("fanout run: check out the branch to build on first (e.g. main)."); return 2; }
  // A clean start is still needed although fanout commits only its own paths: the lanes branch from the
  // base's last commit and rehearse tests commits, so uncommitted work would be missing from both; git
  // refuses to merge into a checkout whose index has staged changes; and a file you had changed that the
  // planner also writes couldn't be told apart from the planner's change.
  if (git(root, "status", "--porcelain").out.split("\n").some((l) => l && !l.slice(3).startsWith(".fanout/"))) {
    console.error("fanout run: commit or stash your changes first; the run builds on a clean " + base + ".");
    return 2;
  }
  mkdirSync(join(root, ".fanout"), { recursive: true });
  const exclude = join(root, ".git", "info", "exclude");
  if (!(existsSync(exclude) && readFileSync(exclude, "utf8").includes(".fanout/"))) appendFileSync(exclude, "\n.fanout/\n");
  const planPath = join(root, ".fanout", "plan.md");
  const start = git(root, "rev-parse", "HEAD").out.trim();
  const agents = [], fixes = {}, earlyFixes = {}, phases = {}, t0 = Date.now();
  let testRuns = 0, phaseStart = t0, sessions = [], specs = {};
  // A drafted plan's one-line tasks leave out most of the goal, so each session's brief gets its own sections.
  const specNote = (s) => (specs[s.name] ? `\nFull spec for this session:\n${specs[s.name]}` : "") + (s.uses.length ? `\n${contractSpecLines(s, sessions, specs, root)}`.trimEnd() : "");
  const phase = (name) => { const now = Date.now(); phases[name] = Math.round((now - phaseStart) / 1000); phaseStart = now; };
  // .fanout/live.json: where the run is, for `fanout status` in another terminal. Cost is known per
  // finished agent run (Claude reports it at the end), so a running session shows its time so far.
  const live = { pid: process.pid, startedAt: new Date().toISOString(), phase: "plan", sessions: {} };
  const writeLive = () => { try { writeFileSync(join(root, ".fanout", "live.json"), JSON.stringify(live)); } catch { /* status is best effort */ } };
  const setLive = (name, fields) => { live.sessions[name] = { ...live.sessions[name], ...fields }; writeLive(); };
  writeLive();
  const track = (role, session, r) => {
    agents.push({ role, session, ...r });
    const cur = live.sessions[session ?? "(planner)"] ?? {};
    setLive(session ?? "(planner)", { costUsd: cur.costUsd === null || r.costUsd == null ? null : (cur.costUsd ?? 0) + r.costUsd, tokens: (cur.tokens ?? 0) + r.inTokens + r.outTokens });
    return r;
  };
  const totals = () => {
    const known = agents.filter((a) => a.costUsd != null);
    return { costUsd: known.reduce((a, x) => a + x.costUsd, 0), costUnknown: known.length < agents.length,
      tokens: agents.reduce((a, x) => a + x.inTokens + x.outTokens, 0), fixes: [...Object.values(fixes), ...Object.values(earlyFixes)].reduce((a, b) => a + b, 0), earlyFixes: Object.keys(earlyFixes).length };
  };
  // Every path that got past the preconditions ends here, so each run leaves one line in .fanout/log.jsonl.
  const finish = (code, result) => {
    live.phase = "finished"; live.result = result; live.pid = null; writeLive();
    appendLog(root, { kind: "run", sessions: sessions.length, seconds: Math.round((Date.now() - t0) / 1000), phases, testRuns, ...totals(), result,
      agents: agents.map((a) => ({ role: a.role, session: a.session, agent: a.agent.split(" ")[0], seconds: a.seconds, costUsd: a.costUsd, tokens: a.inTokens + a.outTokens, error: a.error })) });
    return code;
  };

  const signInStop = (kinds) => { const p = signInProblem(kinds); if (p) console.error(`fanout run: ${p}`); return p; };

  // 1. Plan
  if (!existsSync(planPath)) {
    if (!goal) { console.error('fanout run: no .fanout/plan.md. Pass a goal: fanout run "add coupons and tax", or --goal-file TASKS.md'); return 2; }
    let draft = flag("--no-draft") ? null : draftPlan({ goal, root, maxSessions });
    if (draft) {
      writeFileSync(planPath, draft.text);
      if (!sh(`node "${SCRIPT}" check`, root).ok) { rmSync(planPath); draft = null; }
    }
    if (draft) {
      specs = draft.specs;
      // The draft can't see what the goal doesn't name; it flags what a session uses from another session's
      // file, and only that (or --review) gets an agent's review. With neither flags nor contracts, no agent.
      const full = flag("--review"), work = [full ? "reviewing it" : draft.flags.length ? `checking ${draft.flags.length} name(s) used across sessions` : "", draft.contracts ? "writing the contracts" : ""].filter(Boolean);
      if (work.length && signInStop(["claude"])) { rmSync(planPath); return 2; }
      log(`drafted the plan from the goal's sections${work.length ? `; ${work.join(" and ")}…` : ""}`);
      const prompt = contractsPrompt({ goal, base, plan: draft.text, maxSessions, flags: draft.flags, full });
      let retry = "";
      for (let i = 0; i < (work.length ? 2 : 0); i++) {
        track("plan", null, await runAgent({ agent: "claude", cwd: root, prompt: prompt + retry, model, budget, plugin: true }));
        const c = sh(`node "${SCRIPT}" check`, root), t = c.ok ? contractsReady(root, readFileSync(planPath, "utf8")) : c;
        if (t.ok) break;
        retry = `\n\nAfter your changes, ${c.ok ? "the tests fail on " + base : "the plan fails the check"}:\n${tail(t.out)}\nFix it.`;
      }
    } else {
      if (signInStop(["claude"])) return 2;
      log("planning…");
      const prompt = plannerPrompt({ goal, base, root, maxSessions });
      for (let i = 0; i < 2; i++) {
        track("plan", null, await runAgent({ agent: "claude", cwd: root, prompt: i ? `${prompt}\n\nThe plan you wrote fails the check:\n${tail(sh(`node "${SCRIPT}" check`, root).out)}\nFix it.` : prompt, model, budget, plugin: true, allowGit: true }));
        if (existsSync(planPath) && sh(`node "${SCRIPT}" check`, root).ok) break;
      }
    }
  }
  if (!existsSync(planPath)) { console.error("fanout run: no plan was written."); return finish(1, "no plan"); }
  // The planner is told to commit the contracts, but doesn't always (seen on a real project: the shared
  // change was written and left uncommitted, so every lane branched without it and rehearse tested code
  // that never switched the new pages on). The tree was clean before planning, but another session can
  // write in this checkout meanwhile, so only files the plan gives to a session or to regen are taken.
  const text = readFileSync(planPath, "utf8"), regen = parseRegen(text), test = planSetting(text, "test");
  sessions = parsePlan(text);
  const leftover = changedPaths(root), contracts = fanoutPaths(leftover, sessions, regen);
  if (commitPaths(root, contracts, "fanout: contracts")) log(`committed ${contracts.length} file(s) the planner left uncommitted as "fanout: contracts"`);
  const stray = leftover.filter((f) => !contracts.includes(f));
  if (stray.length) log(`left ${stray.length} uncommitted file(s) outside the plan alone: ${stray.slice(0, 5).join(", ")}${stray.length > 5 ? ", ..." : ""}`);
  phase("plan");
  const { problems, order } = check(sessions, root, regen);
  if (problems.length) { problems.forEach((p) => console.log(p)); console.error("fanout run: fix the plan, then run again."); return finish(1, "plan invalid"); }

  // 2. Approve
  const mix = flag("--mix") ? mixAgents(sessions) : null;
  const agentFor = (s) => s.agent || mix?.[s.name] || defaultAgent;
  if (signInStop(sessions.map(agentFor))) return finish(1, "not signed in");
  console.log(`\n${text.trim()}\n\nMerge order: ${order.join(" -> ")}`);
  if (mix) console.log(`Agents (--mix: ${MIX_CLAUDE_MAX} sessions in Claude, those others build on first; Codex for the rest): ${sessions.map((s) => `${s.name} ${agentFor(s)}`).join(", ")}`);
  if (!flag("--yes")) {
    if (!process.stdin.isTTY) { console.log("\nRun again with --yes to start these sessions."); return agents.length ? finish(0, "planned") : 0; }
    const rl = createInterface({ input: process.stdin, output: process.stdout });
    const ok = /^y/i.test(await rl.question("\nStart these sessions? [y/N] "));
    rl.close();
    if (!ok) { log(`not started. Plan kept at .fanout/plan.md; anything committed since ${start.slice(0, 7)} is still on ${base}.`); return finish(0, "not started"); }
  }
  phaseStart = Date.now(); // time spent waiting for approval isn't the tool's

  // 3. Lanes
  sh(`node "${SCRIPT}" install-git-hook`, root);
  git(root, "worktree", "prune");
  const wt = Object.fromEntries(sessions.map((s) => [s.name, join(root, ".fanout", "lanes", s.name)]));
  let copiedTold = 0;
  for (const s of sessions) {
    if (!existsSync(wt[s.name])) {
      const exists = git(root, "rev-parse", "--verify", "--quiet", `fanout/${s.name}`).ok;
      const r = exists ? git(root, "worktree", "add", "-q", wt[s.name], `fanout/${s.name}`) : git(root, "worktree", "add", "-q", "-b", `fanout/${s.name}`, wt[s.name], base);
      if (!r.ok) { console.error(`fanout run: can't create the worktree for ${s.name}:\n${r.out}`); return finish(1, "worktree failed"); }
      const { copied, failed } = copyIncludes(root, wt[s.name]);
      if ((copied.length || failed.length) && !copiedTold++) log(`copied into each session's folder (.worktreeinclude): ${copied.slice(0, 8).join(", ") || "nothing"}${copied.length > 8 ? ` and ${copied.length - 8} more` : ""}${failed.length ? `; could not copy: ${failed.slice(0, 8).join(", ")}` : ""}`);
    }
  }
  log(`starting ${sessions.length} sessions: ${sessions.map((s) => `${s.name} (${agentFor(s)})`).join(", ")}`);
  const ahead = (s) => Number(git(root, "rev-list", "--count", `${base}..fanout/${s.name}`).out.trim()) || 0;
  // An agent run that errors (crash, budget, non-zero exit) is tried once more with the same brief; its
  // partial work is not committed. A run that ends cleanly but changes nothing is only flagged: a session
  // can genuinely have nothing to do. If no session changed anything, though, the run stops rather than
  // report success (that is how a blocked agent shows up: it ends cleanly and edits nothing).
  const runLane = async (s) => {
    if (ahead(s) > 0) { log(`${s.name}: already has commits, not started again`); setLive(s.name, { state: "skipped" }); return { sessionId: null, seconds: 0, skipped: true }; }
    let r;
    for (let attempt = 0; attempt < 2; attempt++) {
      setLive(s.name, { state: attempt ? "retrying" : "working", since: Date.now() });
      r = track("lane", s.name, await runAgent({ agent: agentFor(s), cwd: wt[s.name], prompt: brief(s, sessions, regen, test, specNote(s), root, { shortTests }), model: modelFor(s), budget, allow: [test, s.check] }));
      if (!r.error) {
        const { reverted } = commitLane(wt[s.name], sessions, s, regen, `fanout: ${s.name}`);
        r.noChanges = ahead(s) === 0;
        setLive(s.name, { state: r.noChanges ? "no changes" : "done", since: null });
        log(`${s.name}: done in ${r.seconds}s${r.fellBack ? ", ran with your user settings (a project-only start failed)" : ""}${reverted.length ? `, reverted out-of-lane: ${reverted.join(", ")}` : ""}${r.noChanges ? ", made no changes" : ""}`);
        return r;
      }
      log(`${s.name}: agent failed (${r.error})${attempt ? "" : ", trying once more"}`);
    }
    setLive(s.name, { state: "failed", since: null });
    return { ...r, failed: true };
  };
  // A session that builds on others gets an early test once they and it are done (earlyTest), and a
  // failure goes straight back to it while the rest still work, instead of waiting for rehearse.
  const session = {}, tracker = readyTracker(sessions), rounds = [];
  const earlyRound = async (s) => {
    if (ahead(s) === 0) return;
    const e = earlyTest(wt[s.name], order, s.name, regen, test);
    if (!e) return;
    testRuns++;
    if (e.ok) { log(`${s.name}: tests pass with ${e.merged.join(", ")} merged in`); return; }
    earlyFixes[s.name] = 1;
    log(`${s.name}: tests fail with ${e.merged.join(", ")} merged in; sending it the failure now`);
    const report = `Your work was committed. ${e.merged.join(", ")} finished too and ${e.merged.length > 1 ? "are" : "is"} now merged into your branch, and \`${test}\` fails there:\n${failureLines(e.out)}\n\n`
      + `${e.conflicted.length ? `${e.conflicted.join(", ")} conflicted with your branch and ${e.conflicted.length > 1 ? "were" : "was"} left out.\n` : ""}Their real code is in your checkout: fix the break within the files you may change.`;
    setLive(s.name, { state: "fixing (early)", since: Date.now() });
    const fix = track("fix", s.name, await runAgent({ agent: agentFor(s), cwd: wt[s.name], model: modelFor(s), budget, allow: [test, s.check], resume: session[s.name], prompt: report,
      fallbackPrompt: brief(s, sessions, regen, test, `${specNote(s)}\n${report}`, root, { shortTests }) }));
    session[s.name] = fix.sessionId ?? session[s.name];
    const fixed = commitLane(wt[s.name], sessions, s, regen, `fanout: fix ${s.name}`);
    setLive(s.name, { state: "fixed", since: null });
    log(`${s.name}: ${fix.error ? `fix agent failed (${fix.error}); rehearse will check it` : fixed.committed ? `fixed in ${fix.seconds}s` : `fix agent changed nothing (${fix.seconds}s); rehearse will check it`}`);
  };
  const startRounds = (ready) => ready.forEach((s) => rounds.push(earlyRound(s).catch((e) => log(`${s.name}: early test failed to run (${e.message})`)).then(() => startRounds(tracker.settle(s.name)))));
  live.phase = "sessions"; writeLive();
  const lanes = await staggered(sessions, async (s) => {
    const r = await runLane(s);
    session[s.name] = r.sessionId;
    if (!r.failed) startRounds(tracker.done(s.name));
    return r;
  });
  for (let i = 0; i < rounds.length; i++) await rounds[i]; // rounds can start more rounds as they end
  const failed = sessions.find((s, i) => lanes[i].failed);
  if (failed) {
    log(`stopped: ${failed.name} agent failed twice. Its work is in .fanout/lanes/${failed.name}; run again to retry unfinished sessions.`);
    return finish(1, `stopped: ${failed.name} agent failed`);
  }
  if (lanes.every((l) => l.noChanges || l.skipped) && !lanes.some((l) => l.skipped)) {
    log("stopped: no session changed anything. If that's unexpected, the agents may have been blocked from editing; run again with FANOUT_TRACE_DIR set to see their tool calls.");
    return finish(1, "stopped: no changes");
  }
  phase("sessions");

  // 4. Rehearse, and send each break back to the lane that caused it
  live.phase = "rehearse"; writeLive();
  for (;;) {
    const r = rehearse(order, { cwd: root, base, test, regen, checks: sessions });
    testRuns += r.testRuns;
    if (r.ok) { log("rehearse: all branches merge and pass together"); break; }
    const head = r.log.find((l) => /^(BROKE after|CONFLICT merging|REGEN FAILED after|CHECK FAILED) /.test(l)) ?? "";
    const name = head.match(/(?:after|merging|FAILED) ([^\s:]+)/)?.[1];
    const s = sessions.find((x) => x.name === name);
    if (!s) {
      // FLAKY or BASE FAILS: no lane caused it, so no agent is sent to fix it.
      console.log(r.log.join("\n"));
      log("stopped: rehearse found a problem no session caused (above). Fix it on " + base + ", then run again.");
      return finish(1, r.log.some((l) => l.startsWith("FLAKY")) ? "stopped: flaky test" : "stopped: tests fail on base");
    }
    log(`rehearse: ${head.split(":")[0]}`);
    if ((fixes[name] = (fixes[name] ?? 0) + 1) > maxFixes) {
      console.log(r.log.join("\n"));
      log(`stopped: ${name ?? "a lane"} still breaks after ${maxFixes} fixes. Its work is in .fanout/lanes/${name}; fix it there, then run again.`);
      return finish(1, `stopped: ${name} still breaks`);
    }
    const { merged, conflicted } = bringIn(wt[name], order, name, regen);
    const brought = [merged.length ? `${merged.join(", ")} ${merged.length > 1 ? "are" : "is"} now merged into your branch, so their real code is in your checkout: run the tests there to see the break.` : "",
      conflicted.length ? `${conflicted.join(", ")} conflicted with your branch and ${conflicted.length > 1 ? "were" : "was"} left out.` : ""].filter(Boolean).join(" ");
    const report = `Your branch was merged with the others in plan order and it broke:\n${r.log.join("\n")}\n\n${brought ? brought + "\n" : ""}Fix it within the files you may change.`;
    setLive(name, { state: `fixing (${fixes[name]})`, since: Date.now() });
    // Resume the lane's own session with just the break report; if that fails, send the full brief again.
    const fix = await runAgent({ agent: agentFor(s), cwd: wt[name], model: modelFor(s), budget, allow: [test, s.check], resume: session[name], prompt: report,
      fallbackPrompt: brief(s, sessions, regen, test, `${specNote(s)}\n${report}`, root, { shortTests }) });
    session[name] = fix.sessionId ?? session[name];
    track("fix", name, fix);
    const fixed = commitLane(wt[name], sessions, s, regen, `fanout: fix ${name}`);
    // A fix that changes nothing would only meet the same failure again: on a real project two fix rounds in a
    // row ($1.19, $1.22) changed nothing, as the failing check couldn't run at all (cmd.exe given sh syntax).
    if (!fixed.committed && !fix.error) {
      console.log(r.log.join("\n"));
      log(`stopped: ${name}'s fix agent changed nothing${fixed.reverted.length ? ` it may change (reverted: ${fixed.reverted.join(", ")})` : ""}, so the same failure would come back. The cause may be outside its files, or in the test or check itself (above). Its work is in .fanout/lanes/${name}.`);
      return finish(1, `stopped: ${name} fix changed nothing`);
    }
    setLive(name, { state: "fixed", since: null });
  }

  // 5. Merge
  phase("rehearse");
  const stats = () => {
    const t = totals();
    return `${agents.length} agent runs, ${t.fixes} fixes, $${t.costUsd.toFixed(2)}${t.costUnknown ? " + unknown" : ""} agent cost, ${Math.round(t.tokens / 1000)}k tokens, ${Math.round((Date.now() - t0) / 1000)}s`;
  };
  live.phase = "merge"; writeLive();
  if (flag("--no-merge")) { log(`ready to merge in order ${order.join(" -> ")} (${stats()})`); return finish(0, "ready to merge"); }
  for (const name of order) {
    const m = git(root, "merge", "--no-ff", "--no-edit", "-m", `fanout: merge ${name}`, `fanout/${name}`);
    if (!m.ok) { git(root, "merge", "--abort"); console.error(`fanout run: merging ${name} into ${base} conflicted, though rehearse passed. Is ${base} changed?\n${tail(m.out)}`); return finish(1, "merge conflict"); }
  }
  for (const g of regen) if (g.cmd) psh(g.cmd, root);
  commitPaths(root, fanoutPaths(changedPaths(root), [], regen), "fanout: regenerate");
  const final = test ? psh(test, root) : { ok: true };
  if (test) testRuns++;
  for (const s of sessions) { git(root, "worktree", "remove", "--force", wt[s.name]); git(root, "branch", "-D", `fanout/${s.name}`); }
  phase("merge");
  log(`${final.ok ? "merged" : "merged, but tests fail"} into ${base}: ${order.join(" -> ")} (${stats()})`);
  if (!final.ok) console.log(tail(final.out));
  return finish(final.ok ? 0 : 1, final.ok ? "merged" : "merged, tests fail");
}
