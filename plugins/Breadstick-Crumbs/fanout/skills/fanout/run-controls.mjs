import { readFileSync, existsSync, readdirSync } from "node:fs";
import { join, dirname, resolve } from "node:path";
import { parsePlan, parseRegen, planSetting, copyIncludes, appendLog, failureLines, runPlanCmd } from "./fanout.mjs";
import { commitLane } from "./run.mjs";
import { runAgent, tokenCount } from "./agent.mjs";
import { estimate, loadPrices } from "./run-report.mjs";
import { git, gitStatus, activeChildren, markAborted, planHash, win as WIN, alive, recordedProcess, worktreeList, validLaneName, laneHealth, stopProcess, dropWorktree, readLive, writeLive, commandLogs } from "./workspace.mjs";

const log = (...args) => console.log("fanout:", ...args);

export async function abort(root) {
  const live = readLive(root);
  if (!live || (!live.pid && !activeChildren(live))) { log("no active run to abort"); return 0; }
  const owner = live.running && recordedProcess(live.pid, live.ownerSince);
  if (owner && !stopProcess(live.pid, { group: false, force: WIN })) {
    console.error(`fanout abort: could not stop run process ${live.pid}.`);
    return 1;
  }
  if (!WIN && owner) {
    // Give the owner time to run its signal handler before taking over.
    for (let i = 0; i < 20 && alive(live.pid); i++) await new Promise((resolve) => setTimeout(resolve, 50));
    if (alive(live.pid) && !stopProcess(live.pid, { group: false })) return 1;
  }
  const latest = readLive(root) ?? live;
  if (latest.startedAt !== live.startedAt) {
    console.error("fanout abort: run state changed while stopping the process.");
    return 1;
  }
  const stuck = Object.values(latest.sessions ?? {}).filter((s) => {
    if (recordedProcess(s.pid, s.pidSince, true)) return !stopProcess(s.pid);
    if (s.pid) { s.state = "aborted"; s.pid = null; }
    return false;
  });
  markAborted(root, latest);
  if (stuck.length) { console.error(`fanout abort: could not stop process(es) ${stuck.map((s) => s.pid).join(", ")}.`); return 1; }
  log("aborted; lane worktrees are available for inspection");
  return 0;
}

export function clean(root, argv) {
  const live = readLive(root);
  if (live?.running || activeChildren(live)) { console.error("fanout clean: abort the active run first."); return 1; }
  const laneDir = join(root, ".fanout", "lanes");
  const targets = new Map(["rehearse", "base"].map((name) => [join(root, ".fanout", name), null]));
  const paths = new Set(existsSync(laneDir) ? readdirSync(laneDir).map((name) => join(laneDir, name)) : []);
  const branches = new Set();
  for (const { path, branch } of worktreeList(root)) {
    const absolute = resolve(path);
    if (dirname(absolute) !== laneDir) continue;
    paths.add(absolute);
    if (branch?.startsWith("refs/heads/fanout/")) targets.set(absolute, branch.slice("refs/heads/".length));
  }
  for (const path of paths) if (!targets.has(path)) targets.set(path, null);
  let planned = [];
  try { planned = parsePlan(readFileSync(join(root, ".fanout", "plan.md"), "utf8")).map((s) => s.name); }
  catch (e) { if (e.code !== "ENOENT") throw e; }
  for (const name of [...planned, ...Object.keys(live?.sessions ?? {})]) {
    if (validLaneName(name)) branches.add(`fanout/${name}`);
  }
  let failed = false;
  for (const [path, branch] of targets) {
    const error = dropWorktree(root, path, { force: argv.includes("--force") });
    if (error) { console.error(`fanout clean: ${path}: ${error}`); failed = true; }
    else if (branch) branches.add(branch);
  }
  const prune = git(root, "worktree", "prune");
  if (!prune.ok) { console.error(prune.error.trim()); failed = true; }
  if (argv.includes("--branches")) for (const branch of branches) {
    if (!git(root, "show-ref", "--verify", "--quiet", `refs/heads/${branch}`).ok) continue;
    const r = git(root, "branch", "-D", branch);
    if (!r.ok) { console.error(r.error.trim()); failed = true; }
  }
  if (!failed) log("cleaned lane and scratch worktrees");
  return failed ? 1 : 0;
}

export async function ask(root, argv) {
  const [id, message] = argv;
  if (!id || !message) { console.error('usage: fanout ask <session-id> "<message>" [--check]'); return 2; }
  const live = readLive(root);
  if (live?.running || activeChildren(live)) { console.error("fanout ask: wait for the active run or abort it first."); return 1; }
  const matches = Object.entries(live?.sessions ?? {}).filter(([name, lane]) =>
    name !== "(planner)" && (lane.sessionId === id || lane.rounds?.some((r) => r.sessionId === id)));
  if (matches.length !== 1 || !["claude", "codex"].includes(matches[0][1].agent)) {
    console.error(`fanout ask: ${id} does not identify a single resumable lane in this checkout.`);
    return 2;
  }
  const [name, lane] = matches[0];
  let text;
  try { text = readFileSync(join(root, ".fanout", "plan.md"), "utf8"); } catch { /* handled below */ }
  const sessions = parsePlan(text ?? ""), s = sessions.find((s) => s.name === name);
  if (!s || planHash(text) !== live.planHash) {
    console.error("fanout ask: restore the plan used by the recorded run before resuming.");
    return 2;
  }
  const regen = parseRegen(text), test = planSetting(text, "test");
  const cwd = join(root, ".fanout", "lanes", name), branch = `fanout/${name}`;
  if (!existsSync(cwd)) {
    const ref = `refs/heads/${branch}`;
    const exists = git(root, "show-ref", "--verify", "--quiet", ref).ok;
    const head = exists ? ref : lane.head;
    if (!head || !git(root, "merge-base", "--is-ancestor", live.laneBase, head).ok) {
      console.error(`fanout ask: no usable branch for ${name}.`);
      return 1;
    }
    const r = git(root, "worktree", "add", "-q", ...(exists ? [cwd, branch] : ["-b", branch, cwd, head]));
    if (!r.ok) { console.error(r.error.trim()); return 1; }
    copyIncludes(root, cwd);
  }
  const health = laneHealth(cwd, branch, live.laneBase, root);
  if (health !== "ok") { console.error(`fanout ask: ${cwd}: ${health}`); return 1; }
  const status = gitStatus(cwd);
  if (status.status !== 0 || status.stdout) { console.error(`fanout ask: commit or stash existing changes in ${cwd} first.`); return 1; }
  live.pid = process.pid;
  live.ownerSince = Date.now() - process.uptime() * 1000;
  live.phase = "ask";
  lane.state = "resuming";
  lane.since = Date.now();
  const save = () => writeLive(root, live);
  const interrupt = () => { stopProcess(lane.pid); markAborted(root, live); process.exit(130); };
  save();
  process.once("SIGINT", interrupt);
  process.once("SIGTERM", interrupt);
  let outcome = "ask failed";
  try {
    const r = await runAgent({ agent: lane.agent, cwd, prompt: message, resume: id, strictResume: true, lane: true,
      model: lane.model, budget: lane.budget, cleanEnv: lane.cleanEnv, userSettings: lane.userSettings,
      tokenBudget: lane.tokenBudget, codexEffort: lane.codexEffort, codexTier: lane.codexTier,
      allow: [test, s.check], onStart: (pid) => { lane.pid = pid; lane.pidSince = Date.now(); save(); }, onStop: () => { lane.pid = null; save(); } });
    estimate(r, loadPrices(text));
    lane.sessionId = r.sessionId ?? lane.sessionId;
    (lane.rounds ??= []).push({ role: "ask", sessionId: r.sessionId, error: r.error });
    appendLog(root, { kind: "ask", session: name, ...r, tokens: tokenCount(r), result: r.error ?? "resumed" });
    if (r.error) { console.error(`fanout ask: ${r.error}`); return 1; }
    const { committed, reverted } = commitLane(cwd, sessions, s, regen, `fanout: follow-up for ${name}`);
    if (r.summary) console.log(r.summary);
    if (reverted.length) log(`reverted out-of-lane changes: ${reverted.join(", ")}`);
    if (!committed && gitStatus(cwd).stdout) { console.error(`fanout ask: could not commit changes in ${cwd}.`); return 1; }
    lane.head = git(cwd, "rev-parse", "HEAD").out.trim();
    log(`${name}: ${committed ? "committed follow-up" : "no changes to commit"}. Run fanout rehearse to check the branches together.`);
    if (argv.includes("--check") && s.check) {
      const logs = commandLogs(root, "ask");
      const check = logs.run(`check-${name}`, (fd) => runPlanCmd(s.check, cwd, fd));
      log(`check ${check.status === 0 ? "passed" : "failed"}: ${check.logPath}`);
      if (check.status !== 0) { console.log(failureLines(check.out)); return 1; }
    }
    outcome = "ask completed";
    return 0;
  } finally {
    lane.state = live.result = outcome;
    lane.since = null;
    live.phase = "finished";
    live.pid = null;
    save();
    process.removeListener("SIGINT", interrupt);
    process.removeListener("SIGTERM", interrupt);
  }
}
