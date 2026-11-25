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
import { execFileSync, spawnSync } from "node:child_process";
import { readFileSync, existsSync, appendFileSync, mkdirSync, writeFileSync, rmSync, readdirSync } from "node:fs";
import { createInterface } from "node:readline/promises";
import { join, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { parsePlan, parseRegen, planSetting, check, rehearse, blockReason, checkCommandNotes, appendLog, matches, ownsFile, contractOwner, failureLines, runPlanCmd, copyIncludes } from "./fanout.mjs";
import { draftPlan, jsExports } from "./draft.mjs";
import { planHash, activeChildren, markAborted, workspaceLock, checkout, laneHealth, worktreeList, dropWorktree, gitStatus, stopProcess, readLive, writeLive, commandLogs } from "./workspace.mjs";

import { loadPrices, estimate, renderReport } from "./run-report.mjs";
import { runAgent, signInProblem, agentCommand, agentEnv, tokenCount } from "./agent.mjs";


const HERE = dirname(fileURLToPath(import.meta.url));
const SCRIPT = join(HERE, "fanout.mjs");
export { runAgent, signInProblem, allowCommands } from "./agent.mjs";

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
  if (!git(wt, "add", "-A").ok) return { committed: false, reverted: [] };
  const stagedFiles = git(wt, "diff", "--cached", "--name-only", "--no-renames", "-z");
  if (!stagedFiles.ok) return { committed: false, reverted: [] };
  const staged = stagedFiles.out.split("\0").filter(Boolean);
  const reverted = [];
  for (const f of staged) {
    if (!blockReason(sessions, s, regen, f)) continue;
    reverted.push(f);
    const restored = git(wt, "cat-file", "-e", `HEAD:${f}`).ok
      ? git(wt, "--literal-pathspecs", "restore", "--source=HEAD", "--staged", "--worktree", "--", f)
      : git(wt, "--literal-pathspecs", "rm", "--cached", "-fq", "--", f);
    if (!restored.ok) return { committed: false, reverted };
    if (!git(wt, "cat-file", "-e", `HEAD:${f}`).ok && !git(wt, "--literal-pathspecs", "clean", "-fq", "--", f).ok)
      return { committed: false, reverted };
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
export function earlyTest(wt, order, name, regen, test, logs) {
  if (!test) return null;
  const before = git(wt, "rev-parse", "HEAD").out.trim();
  const { merged, conflicted } = bringIn(wt, order, name, regen);
  if (!merged.length) return null;
  const r = logs ? logs.run(`early-${name}`, (fd) => runPlanCmd(test, wt, fd)) : psh(test, wt);
  const ok = r.ok ?? r.status === 0;
  // A pass leaves nothing to fix: the branch goes back to the session's own commits (rehearse merges them
  // all anyway), without what the test and the regen wrote. A failure keeps the merges for the fix.
  if (ok) { git(wt, "reset", "-q", "--hard", before); git(wt, "clean", "-fdq"); }
  return { ok, merged, conflicted, out: r.out, logPath: r.logPath };
}

// Contracts a session builds against are pasted into its brief when they're small, so it doesn't spend
// turns reading them (each turn resends the whole conversation). Larger ones are just named.
const CONTRACT_INLINE_BYTES = 8000;
function readContractAt(root, base, file) {
  const r = spawnSync("git", ["cat-file", "blob", `${base}:${file.replaceAll("\\", "/").replace(/^\.\//, "")}`], { cwd: root, encoding: "utf8" });
  return r.status === 0 ? r.stdout : null;
}

function inlineContracts(s, root, contract) {
  if (!root && !contract) return "";
  const read = contract ?? ((file) => {
    try { return readFileSync(join(root, file), "utf8"); } catch { return null; }
  });
  const texts = s.uses.filter((u) => !/[*?{]/.test(u)).map((f) => [f, read(f)]).filter(([, body]) => body != null);
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
export function brief(s, sessions, regen, test, note = "", root = null, { shortTests = false, contract } = {}) {
  const others = sessions.filter((x) => x !== s).map((x) => x.name);
  return [
    `You are session "${s.name}" of a parallel fan-out. ${others.length ? `Other agents are working on ${others.join(", ")} at the same time.` : ""}`,
    `Task: ${s.task || s.done || s.name}`,
    s.done ? `Done when: ${s.done}` : "",
    s.check ? `After all branches merge, this must pass: \`${s.check}\`.` : "",
    `You may change only: ${s.owns.join(", ")}. Edits anywhere else are refused or reverted.`,
    s.uses.length ? `Shared interfaces you build against (frozen: read them, don't edit them): ${s.uses.join(", ")}.` : "",
    inlineContracts(s, root, contract),
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
  --base <branch>       build on a different local branch
  --dry-run             preview lane commands and briefs from an existing plan
  --clean-env           strip inherited CLAUDE* and ANTHROPIC* variables for Claude
  --token-budget <n>    stop each lane at its reported token limit, including retries
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
  const root = checkout(process.cwd()), current = git(root, "branch", "--show-current").out.trim();
  const base = opt("--base", current), baseRef = `refs/heads/${base}`;
  const baseCommit = git(root, "rev-parse", "--verify", "--quiet", baseRef);
  const tokenBudget = flag("--token-budget") ? Number(opt("--token-budget")) : undefined;
  if (!base || !baseCommit.ok || base.startsWith("fanout/") || base.startsWith("-")) {
    console.error(`fanout run: choose an existing local base branch (${base || "none checked out"}).`);
    return 2;
  }
  if (tokenBudget != null && (!Number.isSafeInteger(tokenBudget) || tokenBudget <= 0)) {
    console.error("fanout run: --token-budget must be a positive integer.");
    return 2;
  }
  const start = baseCommit.out.trim(), alternate = current !== base, dry = flag("--dry-run");
  const green = gitStatus(root);
  if (!dry && !alternate && (green.status !== 0 || green.stdout)) {
    console.error("fanout run: commit or stash your changes first; the run builds on a clean " + base + ".");
    return 2;
  }
  const planPath = join(root, ".fanout", "plan.md");
  if (!existsSync(planPath) && (dry || !goal)) {
    console.error(dry ? "fanout run: --dry-run needs an existing .fanout/plan.md." :
      'fanout run: no .fanout/plan.md. Pass a goal: fanout run "add coupons and tax", or --goal-file TASKS.md');
    return 2;
  }
  const cleanEnv = flag("--clean-env") || process.env.FANOUT_SCRUB_ENV === "1";
  const defaultSettings = Boolean(process.env.FANOUT_USER_SETTINGS);
  const mixFor = (sessions) => flag("--mix") ? mixAgents(sessions) : null;
  const lanePath = (name) => join(root, ".fanout", "lanes", name);
  if (dry) {
    const text = readFileSync(planPath, "utf8"), sessions = parsePlan(text), regen = parseRegen(text), test = planSetting(text, "test");
    const { problems, order, notes } = check(sessions, root, regen, start, { baseOnly: alternate });
    for (const line of [...notes, ...problems]) console.log(line);
    if (problems.length) return 1;
    const mix = mixFor(sessions);
    console.log(`Base: ${base} (${start})\nMerge order: ${order.join(" -> ")}`);
    for (const s of sessions) {
      const agent = s.agent || mix?.[s.name] || defaultAgent, cwd = lanePath(s.name);
      const env = agentEnv(agent, cleanEnv);
      const removed = Object.keys(process.env).filter((key) => !Object.hasOwn(env, key)).sort();
      const prompt = brief(s, sessions, regen, test, "", null, { shortTests, contract: (file) => readContractAt(root, start, file) });
      const command = agentCommand({ agent, cwd, model: modelFor(s), budget, allow: [test, s.check], lane: true }, true);
      const already = git(root, "rev-parse", "--verify", "--quiet", `refs/heads/fanout/${s.name}`).ok
        && Number(git(root, "rev-list", "--count", `${start}..refs/heads/fanout/${s.name}`).out);
      console.log(`\n[${s.name}]${already ? " (skipped if the existing lane passes validation)" : ""}\nWorking folder: ${cwd}\nCommand: ${command}\nEnvironment: ${removed.length ? `unset ${removed.join(", ")}` : "inherited"}\nBrief (stdin):\n${prompt}`);
    }
    return 0;
  }

  const unlock = workspaceLock(root);
  if (!unlock) { console.error("fanout run: another operation owns this checkout."); return 2; }
  try {
    return await runInCheckout();
  } finally { unlock(); }

  async function runInCheckout() {
    const prior = readLive(root);
    if (prior?.running || activeChildren(prior)) {
      console.error("fanout run: a run or its agents are still active in this checkout. Use fanout status or fanout abort.");
      return 2;
    }
    mkdirSync(join(root, ".fanout"), { recursive: true });
    const exclude = resolve(root, git(root, "rev-parse", "--git-path", "info/exclude").out.trim());
    mkdirSync(dirname(exclude), { recursive: true });
    if (!(existsSync(exclude) && readFileSync(exclude, "utf8").includes(".fanout/"))) appendFileSync(exclude, "\n.fanout/\n");

    let buildRoot = root, buildPath = planPath, scratch = null;
    if (alternate) {
      scratch = join(root, ".fanout", "base");
      if (existsSync(scratch) || worktreeList(root).some((w) => resolve(w.path) === scratch)) {
        console.error(`fanout run: ${scratch} is left over from another run. Inspect it or use fanout clean first.`);
        return 2;
      }
      const occupied = worktreeList(root).some((w) => w.branch === baseRef);
      const detached = flag("--no-merge") && occupied;
      const setup = git(root, "worktree", "add", "-q", ...(detached ? ["--detach", scratch, start] : [scratch, base]));
      if (!setup.ok) { console.error(`fanout run: could not check out ${base} in ${scratch}.\n${setup.out}`); return 2; }
      buildRoot = scratch;
      copyIncludes(root, buildRoot);
      buildPath = join(buildRoot, ".fanout", "plan.md");
      mkdirSync(dirname(buildPath), { recursive: true });
      if (existsSync(planPath)) writeFileSync(buildPath, readFileSync(planPath));
    }

    const agents = [], fixes = Object.create(null), earlyFixes = Object.create(null), phases = {}, t0 = Date.now();
    let testRuns = 0, phaseStart = t0, sessions = [], specs = {}, laneBase = start, prices = {}, logs, checks = {}, testResult;
    const specNote = (s) => (Object.hasOwn(specs, s.name) ? `\nFull spec for this session:\n${specs[s.name]}` : "") + (s.uses.length ? `\n${contractSpecLines(s, sessions, specs, buildRoot)}`.trimEnd() : "");
    const phase = (name) => { const now = Date.now(); phases[name] = Math.round((now - phaseStart) / 1000); phaseStart = now; };
    const live = { pid: process.pid, ownerSince: Date.now() - process.uptime() * 1000, startedAt: new Date().toISOString(),
      phase: "plan", base, laneBase, sessions: Object.create(null) };
    const save = () => writeLive(root, live);
    const setLive = (name, fields) => {
      live.sessions[name] = { ...live.sessions[name], ...fields };
      save();
    };
    const track = (role, session, r) => {
      estimate(r, prices);
      agents.push({ role, session, ...r });
      const name = session ?? "(planner)", cur = live.sessions[name] ?? {};
      setLive(name, {
        costUsd: cur.costUsd === null || r.costUsd == null ? null : (cur.costUsd ?? 0) + r.costUsd,
        tokens: (cur.tokens ?? 0) + tokenCount(r),
        sessionId: r.sessionId ?? cur.sessionId,
        ...(r.fellBack && !r.error ? { userSettings: true } : {}),
        rounds: [...(cur.rounds ?? []), { role, sessionId: r.sessionId, error: r.error }],
      });
      return r;
    };
    const launch = (name, opts) => {
      const lane = name !== "(planner)";
      return runAgent({ ...opts, cleanEnv, userSettings: lane ? live.sessions[name]?.userSettings : defaultSettings, lane,
        tokenBudget: tokenBudget == null || !lane ? undefined : Math.max(0, tokenBudget - (live.sessions[name]?.tokens ?? 0)),
        onStart: (pid) => setLive(name, { pid, pidSince: Date.now() }),
        onSession: (sessionId) => setLive(name, { sessionId }),
        onStop: () => setLive(name, { pid: null }),
      });
    };
    const totals = () => {
      const known = agents.filter((a) => a.costUsd != null);
      return { costUsd: known.reduce((a, x) => a + x.costUsd, 0), costUnknown: known.length < agents.length,
        estimatedCost: known.some((a) => a.estimatedCost), tokens: agents.reduce((a, x) => a + tokenCount(x), 0),
        fixes: [...Object.values(fixes), ...Object.values(earlyFixes)].reduce((a, b) => a + b, 0), earlyFixes: Object.keys(earlyFixes).length };
    };
    const finish = (code, result, record = true) => {
      live.phase = "finished"; live.result = result; live.pid = null; save();
      if (!record) return code;
      appendLog(root, { kind: "run", sessions: sessions.length, seconds: Math.round((Date.now() - t0) / 1000), phases, testRuns, ...totals(), result,
        agents: agents.map(({ tools, ...agent }) => ({ ...agent, agent: agent.agent.split(" ")[0], tokens: tokenCount(agent) })) });
      if (logs) {
        const report = renderReport({ root, base, laneBase, sessions, agents, live, result, logs, checks, testResult });
        const path = join(root, ".fanout", "report.md");
        writeFileSync(path, report);
        console.log(`\n${report}\nReport: ${path}`);
      }
      return code;
    };

    const interrupt = () => {
      for (const x of Object.values(live.sessions)) stopProcess(x.pid);
      markAborted(root, live);
      process.exit(130);
    };
    save();
    process.once("SIGINT", interrupt);
    process.once("SIGTERM", interrupt);
    const signInStop = (kinds, cwd, selectedModel) => {
      const p = signInProblem(kinds, { cwd, cleanEnv, userSettings: defaultSettings, model: selectedModel });
      if (p) console.error(`fanout run: ${p}`);
      return p;
    };
    try {
      // 1. Plan
      if (!existsSync(buildPath)) {
        if (!goal) { console.error('fanout run: no .fanout/plan.md. Pass a goal: fanout run "add coupons and tax", or --goal-file TASKS.md'); return finish(2, "planning could not start"); }
        let draft = flag("--no-draft") ? null : draftPlan({ goal, root: buildRoot, maxSessions });
        if (draft) {
          writeFileSync(buildPath, draft.text);
          if (!sh(`node "${SCRIPT}" check`, buildRoot).ok) { rmSync(buildPath); draft = null; }
        }
        if (draft) {
          specs = draft.specs;
          // The draft can't see what the goal doesn't name; it flags what a session uses from another session's
          // file, and only that (or --review) gets an agent's review. With neither flags nor contracts, no agent.
          const full = flag("--review"), work = [full ? "reviewing it" : draft.flags.length ? `checking ${draft.flags.length} name(s) used across sessions` : "", draft.contracts ? "writing the contracts" : ""].filter(Boolean);
          if (work.length && signInStop(["claude"], buildRoot, model)) { rmSync(buildPath); return finish(2, "planning could not start"); }
          log(`drafted the plan from the goal's sections${work.length ? `; ${work.join(" and ")}…` : ""}`);
          const prompt = contractsPrompt({ goal, base, plan: draft.text, maxSessions, flags: draft.flags, full });
          let retry = "";
          for (let i = 0; i < (work.length ? 2 : 0); i++) {
            track("plan", null, await launch("(planner)", { agent: "claude", cwd: buildRoot, prompt: prompt + retry, model, budget, plugin: true }));
            const c = sh(`node "${SCRIPT}" check`, buildRoot), t = c.ok ? contractsReady(buildRoot, readFileSync(buildPath, "utf8")) : c;
            if (t.ok) break;
            retry = `\n\nAfter your changes, ${c.ok ? "the tests fail on " + base : "the plan fails the check"}:\n${tail(t.out)}\nFix it.`;
          }
        } else {
          if (signInStop(["claude"], buildRoot, model)) return finish(2, "planning could not start");
          log("planning…");
          const prompt = plannerPrompt({ goal, base, root: buildRoot, maxSessions });
          for (let i = 0; i < 2; i++) {
            track("plan", null, await launch("(planner)", { agent: "claude", cwd: buildRoot, prompt: i ? `${prompt}\n\nThe plan you wrote fails the check:\n${tail(sh(`node "${SCRIPT}" check`, buildRoot).out)}\nFix it.` : prompt, model, budget, plugin: true, allowGit: true }));
            if (existsSync(buildPath) && sh(`node "${SCRIPT}" check`, buildRoot).ok) break;
          }
        }
      }
      if (!existsSync(buildPath)) { console.error("fanout run: no plan was written."); return finish(1, "no plan"); }
      // The planner is told to commit the contracts, but doesn't always (seen on a real project: the shared
      // change was written and left uncommitted, so every lane branched without it and rehearse tested code
      // that never switched the new pages on). The tree was clean before planning, but another session can
      // write in this checkout meanwhile, so only files the plan gives to a session or to regen are taken.
      const text = readFileSync(buildPath, "utf8"), regen = parseRegen(text), test = planSetting(text, "test");
      sessions = parsePlan(text);
      live.planHash = planHash(text);
      if (alternate) writeFileSync(planPath, text);
      try { prices = loadPrices(text); }
      catch (e) { console.error(`fanout run: ${e.message}`); return finish(2, "invalid prices"); }
      const leftover = changedPaths(buildRoot), contracts = fanoutPaths(leftover, sessions, regen);
      if (commitPaths(buildRoot, contracts, "fanout: contracts")) log(`committed ${contracts.length} file(s) the planner left uncommitted as "fanout: contracts"`);
      const stray = leftover.filter((f) => !contracts.includes(f));
      if (stray.length) log(`left ${stray.length} uncommitted file(s) outside the plan alone: ${stray.slice(0, 5).join(", ")}${stray.length > 5 ? ", ..." : ""}`);
      phase("plan");
      laneBase = git(buildRoot, "rev-parse", "HEAD").out.trim();
      live.laneBase = laneBase; save();
      const { problems, order, notes } = check(sessions, buildRoot, regen, laneBase);
      for (const note of [...notes, ...checkCommandNotes(sessions, buildRoot)]) console.log(note);
      if (problems.length) { problems.forEach((p) => console.log(p)); console.error("fanout run: fix the plan, then run again."); return finish(1, "plan invalid"); }

      // 2. Approve
      const mix = mixFor(sessions);
      const agentFor = (s) => s.agent || mix?.[s.name] || defaultAgent;
      console.log(`\n${text.trim()}\n\nMerge order: ${order.join(" -> ")}`);
      if (mix) console.log(`Agents (--mix: ${MIX_CLAUDE_MAX} sessions in Claude, those others build on first; Codex for the rest): ${sessions.map((s) => `${s.name} ${agentFor(s)}`).join(", ")}`);
      if (!flag("--yes")) {
        if (!process.stdin.isTTY) { console.log("\nRun again with --yes to start these sessions."); return finish(0, "planned", agents.length > 0); }
        const rl = createInterface({ input: process.stdin, output: process.stdout });
        const ok = /^y/i.test(await rl.question("\nStart these sessions? [y/N] "));
        rl.close();
        if (!ok) { log(`not started. Plan kept at .fanout/plan.md; anything committed since ${start.slice(0, 7)} is still on ${base}.`); return finish(0, "not started"); }
      }
      phaseStart = Date.now(); // time spent waiting for approval isn't the tool's

      // 3. Lanes
      sh(`node "${SCRIPT}" install-git-hook`, root);
      git(root, "worktree", "prune");
      const wt = Object.fromEntries(sessions.map((s) => [s.name, lanePath(s.name)]));
      logs = commandLogs(root, "run");
      let copiedTold = 0;
      for (const s of sessions) {
        const path = wt[s.name], branch = `fanout/${s.name}`;
        const health = laneHealth(path, branch, laneBase, root);
        if (health !== "ok" && health !== "missing") {
          const empty = health === "not a worktree" && readdirSync(path).length === 0;
          const error = empty ? dropWorktree(root, path) : health;
          if (error) { console.error(`fanout run: invalid lane ${path}: ${error}. Inspect it before retrying.`); return finish(1, "invalid worktree"); }
        }
        if (!existsSync(path)) {
          const ref = `refs/heads/${branch}`;
          const exists = git(root, "rev-parse", "--verify", "--quiet", ref).ok;
          if (exists && !git(root, "merge-base", "--is-ancestor", laneBase, ref).ok) {
            console.error(`fanout run: ${branch} does not descend from ${base} (${laneBase.slice(0, 12)}); inspect that branch before retrying.`);
            return finish(1, "invalid lane branch");
          }
          const r = exists ? git(root, "worktree", "add", "-q", path, branch) : git(root, "worktree", "add", "-q", "-b", branch, path, laneBase);
          if (!r.ok) { console.error(`fanout run: can't create the worktree at ${path}:\n${r.out}`); return finish(1, "worktree failed"); }
          const { copied, failed } = copyIncludes(root, path);
          if ((copied.length || failed.length) && !copiedTold++) log(`copied into each session's folder (.worktreeinclude): ${copied.slice(0, 8).join(", ") || "nothing"}${copied.length > 8 ? ` and ${copied.length - 8} more` : ""}${failed.length ? `; could not copy: ${failed.slice(0, 8).join(", ")}` : ""}`);
        }
        const verified = laneHealth(path, branch, laneBase, root);
        if (verified !== "ok") { console.error(`fanout run: invalid lane ${path}: ${verified}`); return finish(1, "invalid worktree"); }
        const previous = prior?.sessions?.[s.name];
        setLive(s.name, { agent: agentFor(s), model: modelFor(s), budget, tokenBudget, cleanEnv, userSettings: defaultSettings,
          codexEffort: process.env.FANOUT_CODEX_EFFORT ?? "low", codexTier: process.env.FANOUT_CODEX_TIER ?? "",
          ...(prior?.laneBase === laneBase && previous?.agent === agentFor(s) ? { sessionId: previous.sessionId, rounds: previous.rounds } : {}) });
      }
      const ahead = (s) => Number(git(root, "rev-list", "--count", `${laneBase}..refs/heads/fanout/${s.name}`).out.trim()) || 0;
      const preflighted = new Set();
      for (const s of sessions.filter((s) => !ahead(s))) {
        const agent = agentFor(s), model = modelFor(s), key = JSON.stringify([agent, model]);
        if (!preflighted.has(key) && signInStop([agent], wt[s.name], model)) return finish(1, "not signed in");
        preflighted.add(key);
      }
      log(`starting ${sessions.length} sessions: ${sessions.map((s) => `${s.name} (${agentFor(s)})`).join(", ")}`);
      // An agent run that errors (crash, budget, non-zero exit) is tried once more with the same brief; its
      // partial work is not committed. A run that ends cleanly but changes nothing is only flagged: a session
      // can genuinely have nothing to do. If no session changed anything, though, the run stops rather than
      // report success (that is how a blocked agent shows up: it ends cleanly and edits nothing).
      const runLane = async (s) => {
        if (ahead(s) > 0) { log(`${s.name}: already has commits, not started again`); setLive(s.name, { state: "skipped" }); return { sessionId: live.sessions[s.name].sessionId, seconds: 0, skipped: true }; }
        let r;
        for (let attempt = 0; attempt < 2; attempt++) {
          setLive(s.name, { state: attempt ? "retrying" : "working", since: Date.now() });
          r = track("lane", s.name, await launch(s.name, { agent: agentFor(s), cwd: wt[s.name], prompt: brief(s, sessions, regen, test, specNote(s), buildRoot, { shortTests }), model: modelFor(s), budget, allow: [test, s.check] }));
          if (!r.error) {
            const { reverted } = commitLane(wt[s.name], sessions, s, regen, `fanout: ${s.name}`);
            r.noChanges = ahead(s) === 0;
            setLive(s.name, { state: r.noChanges ? "no changes" : "done", since: null });
            log(`${s.name}: done in ${r.seconds}s${r.fellBack ? ", ran with your user settings (a project-only start failed)" : ""}${reverted.length ? `, reverted out-of-lane: ${reverted.join(", ")}` : ""}${r.noChanges ? ", made no changes" : ""}`);
            return r;
          }
          log(`${s.name}: agent failed (${r.error})${attempt || r.budgetExceeded ? "" : ", trying once more"}`);
          if (r.budgetExceeded) break;
        }
        setLive(s.name, { state: "failed", since: null });
        return { ...r, failed: true };
      };
      // A session that builds on others gets an early test once they and it are done (earlyTest), and a
      // failure goes straight back to it while the rest still work, instead of waiting for rehearse.
      const session = Object.create(null), tracker = readyTracker(sessions), rounds = [];
      const earlyRound = async (s) => {
        if (ahead(s) === 0) return;
        const e = earlyTest(wt[s.name], order, s.name, regen, test, logs);
        if (!e) return;
        testRuns++;
        log(`${s.name}: early test output: ${e.logPath}`);
        if (e.ok) { log(`${s.name}: tests pass with ${e.merged.join(", ")} merged in`); return; }
        earlyFixes[s.name] = 1;
        log(`${s.name}: tests fail with ${e.merged.join(", ")} merged in; sending it the failure now`);
        const report = `Your work was committed. ${e.merged.join(", ")} finished too and ${e.merged.length > 1 ? "are" : "is"} now merged into your branch, and \`${test}\` fails there:\n${failureLines(e.out)}\n\n`
          + `${e.conflicted.length ? `${e.conflicted.join(", ")} conflicted with your branch and ${e.conflicted.length > 1 ? "were" : "was"} left out.\n` : ""}Their real code is in your checkout: fix the break within the files you may change.`;
        setLive(s.name, { state: "fixing (early)", since: Date.now() });
        const fix = track("fix", s.name, await launch(s.name, { agent: agentFor(s), cwd: wt[s.name], model: modelFor(s), budget, allow: [test, s.check], resume: session[s.name], prompt: report,
          fallbackPrompt: brief(s, sessions, regen, test, `${specNote(s)}\n${report}`, buildRoot, { shortTests }) }));
        session[s.name] = fix.sessionId ?? session[s.name];
        if (fix.budgetExceeded) { setLive(s.name, { state: "token budget reached", since: null }); return; }
        const fixed = commitLane(wt[s.name], sessions, s, regen, `fanout: fix ${s.name}`);
        setLive(s.name, { state: "fixed", since: null });
        log(`${s.name}: ${fix.error ? `fix agent failed (${fix.error}); rehearse will check it` : fixed.committed ? `fixed in ${fix.seconds}s` : `fix agent changed nothing (${fix.seconds}s); rehearse will check it`}`);
      };
      const startRounds = (ready) => ready.forEach((s) => rounds.push(earlyRound(s).catch((e) => log(`${s.name}: early test failed to run (${e.message})`)).then(() => startRounds(tracker.settle(s.name)))));
      live.phase = "sessions"; save();
      const lanes = await staggered(sessions, async (s) => {
        const r = await runLane(s);
        session[s.name] = r.sessionId;
        if (!r.failed) startRounds(tracker.done(s.name));
        return r;
      });
      for (let i = 0; i < rounds.length; i++) await rounds[i]; // rounds can start more rounds as they end
      const failed = sessions.find((s, i) => lanes[i].failed);
      if (failed) {
        log(`stopped: ${failed.name} agent failed. Its work is in .fanout/lanes/${failed.name}; run again to retry unfinished sessions.`);
        return finish(1, `stopped: ${failed.name} ${lanes[sessions.indexOf(failed)].budgetExceeded ? "reached its token budget" : "agent failed"}`);
      }
      if (lanes.every((l) => l.noChanges || l.skipped) && !lanes.some((l) => l.skipped)) {
        log("stopped: no session changed anything. If that's unexpected, the agents may have been blocked from editing; run again with FANOUT_TRACE_DIR set to see their tool calls.");
        return finish(1, "stopped: no changes");
      }
      const budgetStop = sessions.find((s) => live.sessions[s.name].state === "token budget reached");
      if (budgetStop) return finish(1, `stopped: ${budgetStop.name} reached its token budget`);
      phase("sessions");

      // 4. Rehearse, and send each break back to the lane that caused it
      live.phase = "rehearse"; save();
      for (;;) {
        const r = rehearse(order, { cwd: root, base: laneBase, baseLabel: base, test, regen, checks: sessions, logs });
        checks = r.checks;
        testResult = test ? (r.testPassed === true ? "passed in rehearsal" : r.testPassed === false ? "failed in rehearsal" : "not run") : "not configured";
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
        const fix = await launch(s.name, { agent: agentFor(s), cwd: wt[name], model: modelFor(s), budget, allow: [test, s.check], resume: session[name], prompt: report,
          fallbackPrompt: brief(s, sessions, regen, test, `${specNote(s)}\n${report}`, buildRoot, { shortTests }) });
        session[name] = fix.sessionId ?? session[name];
        track("fix", name, fix);
        if (fix.budgetExceeded) return finish(1, `stopped: ${name} reached its token budget`);
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
        return `${agents.length} agent runs, ${t.fixes} fixes, $${t.costUsd.toFixed(2)}${t.estimatedCost ? " estimated" : ""}${t.costUnknown ? " + unknown" : ""} agent cost, ${Math.round(t.tokens / 1000)}k tokens, ${Math.round((Date.now() - t0) / 1000)}s`;
      };
      live.phase = "merge"; save();
      if (flag("--no-merge")) { log(`ready to merge in order ${order.join(" -> ")} (${stats()})`); return finish(0, "ready to merge"); }
      if (git(buildRoot, "rev-parse", "HEAD").out.trim() !== laneBase || git(buildRoot, "branch", "--show-current").out.trim() !== base) {
        console.error(`fanout run: ${base} changed during the run; the lanes are ready for review.`);
        return finish(1, "base changed");
      }
      for (const name of order) {
        const m = git(buildRoot, "merge", "--no-ff", "--no-edit", "-m", `fanout: merge ${name}`, `fanout/${name}`);
        if (!m.ok) { git(buildRoot, "merge", "--abort"); console.error(`fanout run: merging ${name} into ${base} conflicted, though rehearse passed. Is ${base} changed?\n${tail(m.out)}`); return finish(1, "merge conflict"); }
      }
      for (const g of regen) if (g.cmd) {
        const generated = logs.run("final-regen", (fd) => runPlanCmd(g.cmd, buildRoot, fd));
        if (generated.status !== 0) return finish(1, `merged, regeneration failed (${generated.logPath})`);
      }
      commitPaths(buildRoot, fanoutPaths(changedPaths(buildRoot), [], regen), "fanout: regenerate");
      const final = test ? logs.run("final-test", (fd) => runPlanCmd(test, buildRoot, fd)) : { status: 0 };
      if (test) { testRuns++; testResult = final.status === 0 ? "passed after merge" : "failed after merge"; }
      phase("merge");
      log(`${final.status === 0 ? "merged" : "merged, but tests fail"} into ${base}: ${order.join(" -> ")} (${stats()})`);
      if (final.status !== 0) console.log(`${failureLines(final.out)}\nFull output: ${final.logPath}`);
      if (final.status === 0) for (const s of sessions) {
        live.sessions[s.name].head = git(wt[s.name], "rev-parse", "HEAD").out.trim();
      }
      const code = finish(final.status === 0 ? 0 : 1, final.status === 0 ? "merged" : "merged, tests fail");
      if (!code) for (const s of sessions) {
        const error = dropWorktree(root, wt[s.name], { force: true });
        if (error) console.error(`fanout run: could not remove ${wt[s.name]}: ${error}. Try fanout clean.`);
        else if (git(root, "merge-base", "--is-ancestor", `refs/heads/fanout/${s.name}`, baseRef).ok) git(root, "branch", "-D", `fanout/${s.name}`);
      }
      return code;
    } catch (e) {
      console.error(`fanout run: ${e.message}`);
      if (activeChildren(live)) for (const lane of Object.values(live.sessions)) stopProcess(lane.pid);
      return finish(1, "run failed");
    } finally {
      process.removeListener("SIGINT", interrupt);
      process.removeListener("SIGTERM", interrupt);
      if (scratch) {
        const error = dropWorktree(root, scratch);
        if (error) console.error(`fanout run: kept ${scratch}: ${error}`);
      }
    }
  }
}
