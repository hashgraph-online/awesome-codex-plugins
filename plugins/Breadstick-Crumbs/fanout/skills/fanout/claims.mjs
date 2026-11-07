// Claims: which session is doing what, kept in git so every session of a repo sees them at once.
//   fanout start "<task>" [files...]              claim this session's task (agents without hooks: AGENTS.md says so)
//   fanout done                                   test this branch merged with the other sessions' work (fanout.mjs)
//   fanout inbox                                  changes other sessions committed since this one last looked (notices)
//   fanout claim <name> "<task>" [files...] [--exposes a,b] [--distinct "how it differs"]   files named here are locked
//   fanout claims [--all]                         live claims (--all: expired ones too)
//   fanout release <name> [--to <branch>]         end a claim, or hand it to another branch
//   fanout init                                   claims on for good, git hook, AGENTS.md block
//
// Claims are on by themselves in a repo with two or more checkouts used in the last day (claimsActive). In
// Claude Code nothing has to be run: the session-start hook tells a session what the others are doing, and
// on its first edit the guard claims its task for it, with the user's request as the task (autoClaim).
//
// The state is a commit on refs/fanout/state whose tree holds one JSON file per claim (claim-<name>.json),
// written with git plumbing: no checkout, nothing in anyone's diff. Every worktree of a repo shares its refs,
// so a claim is visible to all local sessions the moment it is written; a team can push and fetch the ref.
// Writes are compare-and-swap on the ref (update-ref with the old value), retried, so two sessions claiming
// at once can't lose one.
//
// A session is its checkout's branch. With claims on, the edit guard and the git hook refuse a file another
// session claimed by name, warn about one another session is also editing, and record each file a session
// edits. Every new task is checked against the live ones for the same work (taskOverlap) before it's accepted.
import { spawnSync } from "node:child_process";
import { existsSync, statSync, readdirSync, readFileSync, writeFileSync, rmSync, appendFileSync } from "node:fs";
import { join, resolve, dirname } from "node:path";
import { tmpdir } from "node:os";
import { matches } from "./fanout.mjs";

export const REF = "refs/fanout/state";
const IDLE_HOURS = 24;

const git = (cwd, args, input) => {
  const r = spawnSync("git", args, { cwd, encoding: "utf8", input, maxBuffer: 64 << 20 });
  return { ok: r.status === 0, out: r.stdout ?? "", err: r.stderr ?? "" };
};
const IDENT = ["-c", "user.name=fanout", "-c", "user.email=fanout@local"];

export const claimsOn = (cwd) => git(cwd, ["config", "--get", "fanout.claims"]).out.trim() === "true";

// Claims switch on by themselves where sessions run in parallel: a repo with two or more checkouts (the main
// one and worktrees) used in the last day. `git config fanout.claims true|false` forces them on or off. A
// checkout counts as used when its index or HEAD changed (git touches the index on every status, add and
// commit); fanout's own lanes and rehearse copy don't count. Reads file times only: the guard runs on every edit.
export function activeCheckouts(cwd, now = Date.now(), common = git(cwd, ["rev-parse", "--path-format=absolute", "--git-common-dir"]).out.trim()) {
  if (!common) return 0;
  const mtime = (p) => { try { return statSync(p).mtimeMs; } catch { return 0; } };
  const dirs = [common];
  try { for (const d of readdirSync(join(common, "worktrees"))) {
    const wt = join(common, "worktrees", d);
    let to = ""; try { to = readFileSync(join(wt, "gitdir"), "utf8"); } catch { /* none */ }
    if (!/[\\/]\.fanout[\\/]/.test(to)) dirs.push(wt);
  } } catch { /* no worktrees */ }
  return dirs.filter((d) => Math.max(mtime(join(d, "index")), mtime(join(d, "HEAD"))) > now - IDLE_HOURS * 3600 * 1000).length;
}
// The same facts for a hook that runs after every tool call, from git's own files instead of git: each git call
// took about 60ms on Windows, and the hook needed six (400ms per tool call). { root, gitDir, common, branch,
// claims, notices } or null outside a repo. Only the repository's own config is read for fanout.* settings.
export function repoInfo(cwd) {
  let dir = cwd;
  for (;;) {
    const dot = join(dir, ".git");
    if (existsSync(dot)) {
      let gitDir = dot;
      try { if (!statSync(dot).isDirectory()) gitDir = resolve(dir, readFileSync(dot, "utf8").match(/^gitdir:\s*(.+)$/m)[1].trim()); } catch { return null; }
      let common = gitDir;
      try { common = resolve(gitDir, readFileSync(join(gitDir, "commondir"), "utf8").trim()); } catch { /* the main checkout */ }
      let head = "", config = "";
      try { head = readFileSync(join(gitDir, "HEAD"), "utf8"); } catch { /* none */ }
      try { config = readFileSync(join(common, "config"), "utf8"); } catch { /* none */ }
      const section = config.match(/^\[fanout\][^\n]*\n((?:(?!\[)[^\n]*\n?)*)/m)?.[1] ?? "";
      const setting = (k) => section.match(new RegExp(`^\\s*${k}\\s*=\\s*(\\S+)`, "mi"))?.[1]?.toLowerCase();
      const branch = head.match(/^ref: refs\/heads\/(.+)$/m)?.[1]?.trim() ?? null;
      const c = setting("claims");
      return { root: dir, gitDir, common, branch, claims: c === "true" ? true : c === "false" ? false : activeCheckouts(dir, Date.now(), common) >= 2, notices: setting("notices") !== "false" };
    }
    const up = dirname(dir);
    if (up === dir) return null;
    dir = up;
  }
}
// Newest change to any branch tip (loose refs or packed-refs): when it hasn't moved, no session has committed.
export function refsStamp(common) {
  let t = 0;
  const walk = (d) => { try { for (const e of readdirSync(d, { withFileTypes: true })) { const p = join(d, e.name); if (e.isDirectory()) walk(p); else t = Math.max(t, statSync(p).mtimeMs); } } catch { /* none */ } };
  walk(join(common, "refs", "heads"));
  try { t = Math.max(t, statSync(join(common, "packed-refs")).mtimeMs); } catch { /* none */ }
  return t;
}
export function claimsActive(cwd) {
  const v = git(cwd, ["config", "--get", "fanout.claims"]).out.trim();
  return v === "true" ? true : v === "false" ? false : activeCheckouts(cwd) >= 2;
}

// What the user asked this session for: the latest user message of at least a few words in its Claude Code
// transcript (hooks get its path). Tool results and fanout's own notes aren't user messages; tags such as
// <system-reminder> blocks are dropped. Used as the task of a claim made for a session on its first edit.
export function taskFromTranscript(path) {
  let lines;
  try { lines = readFileSync(path, "utf8").split("\n"); } catch { return ""; }
  let task = "";
  for (const l of lines) {
    if (!l.includes('"user"')) continue;
    let j; try { j = JSON.parse(l); } catch { continue; }
    if (j.type !== "user" || j.isMeta) continue;
    const c = j.message?.content, text = typeof c === "string" ? c : Array.isArray(c) ? c.filter((x) => x.type === "text").map((x) => x.text).join("\n") : "";
    const clean = cleanTask(text);
    if (clean.length >= 15) task = clean;
  }
  return task.slice(0, 600);
}
export const cleanTask = (text) => String(text ?? "").replace(/<([a-z][\w-]*)[^>]*>[\s\S]*?<\/\1>/gi, "").replace(/\s+/g, " ").trim();
// The transcript holding this hook's own task. A subagent's hooks get its parent session's transcript_path, so
// four lanes started as subagents were each claimed with the parent's last message ("Yes, start the build") and
// three were refused as the same work. A subagent's own transcript, starting with its brief, sits beside the
// parent's: <session>/subagents/agent-<id>.jsonl. Found by agent_id, else by the tool call being checked.
export function hookTranscript(input = {}) {
  const t = input.transcript_path ?? input.transcriptPath;
  if (!t) return t;
  const dir = join(t.replace(/\.jsonl$/, ""), "subagents"), id = input.agent_id ?? input.agentId;
  if (id && existsSync(join(dir, `agent-${id}.jsonl`))) return join(dir, `agent-${id}.jsonl`);
  const call = input.tool_use_id ?? input.toolUseId;
  if (!call) return t;
  let files = [];
  try { files = readdirSync(dir).filter((f) => /^agent-.*\.jsonl$/.test(f)); } catch { return t; }
  const own = files.find((f) => { try { return readFileSync(join(dir, f), "utf8").includes(`"${call}"`); } catch { return false; } });
  return own ? join(dir, own) : t;
}
export const slugName = (s) => String(s).toLowerCase().replace(/[^a-z0-9._-]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 60);
export const branchOf = (cwd) => git(cwd, ["branch", "--show-current"]).out.trim() || null;

// Every claim decision and notice, one JSON line each, so real use can be checked afterwards (fanout log): was a
// refusal right, did a notice help. In the repository's git dir, so nothing shows in anyone's status. Never throws:
// inside Codex's sandbox it isn't writable.
export function logEvent(cwd, rec, common = null) {
  try {
    const c = common ?? git(cwd, ["rev-parse", "--path-format=absolute", "--git-common-dir"]).out.trim();
    if (c) appendFileSync(join(c, "fanout-events.jsonl"), JSON.stringify({ at: new Date().toISOString(), ...rec }) + "\n");
  } catch { /* logging never gets in the way */ }
}
export function readEvents(common) {
  try { return readFileSync(join(common, "fanout-events.jsonl"), "utf8").split("\n").filter(Boolean).map((l) => { try { return JSON.parse(l); } catch { return null; } }).filter(Boolean); } catch { return []; }
}

// { head, claims: { name: claim } } as stored on the ref (expired ones included).
export function readState(cwd) {
  const head = git(cwd, ["rev-parse", "--verify", "--quiet", REF]).out.trim() || null;
  if (!head) return { head: null, claims: {} };
  const entries = git(cwd, ["ls-tree", head]).out.split("\n").filter(Boolean).map((l) => {
    const [meta, path] = l.split("\t");
    return { sha: meta.split(" ")[2], path };
  });
  const claims = {};
  if (entries.length) {
    // One cat-file for every blob: "<sha> blob <size>\n<content>\n" each.
    const out = Buffer.from(git(cwd, ["cat-file", "--batch"], entries.map((e) => e.sha).join("\n") + "\n").out, "utf8");
    let pos = 0;
    for (const e of entries) {
      const nl = out.indexOf(10, pos), size = Number(out.subarray(pos, nl).toString().split(" ")[2]);
      const body = out.subarray(nl + 1, nl + 1 + size).toString();
      pos = nl + 1 + size + 1;
      if (e.path.startsWith("claim-")) try { const c = JSON.parse(body); claims[c.name] = c; } catch { /* skip a broken entry */ }
    }
  }
  return { head, claims };
}

// mutate(claims) changes the object in place and returns false to write nothing. Retries on a race.
export function writeState(cwd, mutate, msg = "fanout: claims") {
  for (let attempt = 0; attempt < 10; attempt++) {
    const { head, claims } = readState(cwd);
    const result = mutate(claims);
    if (result === false) return { ok: true, written: false, claims };
    const lines = Object.values(claims).map((c) => {
      const sha = git(cwd, ["hash-object", "-w", "--stdin"], JSON.stringify(c, null, 1)).out.trim();
      return `100644 blob ${sha}\tclaim-${c.name}.json`;
    });
    const tree = git(cwd, ["mktree"], lines.join("\n") + (lines.length ? "\n" : "")).out.trim();
    const commit = git(cwd, [...IDENT, "commit-tree", tree, ...(head ? ["-p", head] : []), "-m", msg]).out.trim();
    if (git(cwd, ["update-ref", REF, commit, head ?? ""]).ok) return { ok: true, written: true, claims, result };
  }
  return { ok: false, written: false };
}

// The tree merging b into a would make, written as objects only (no checkout or ref changes), and whether it
// merged without a conflict; null if git can't (older than 2.38).
export function mergedTree(cwd, a, b) {
  const r = spawnSync("git", ["merge-tree", "--write-tree", "--no-messages", a, b], { cwd, encoding: "utf8" });
  const tree = (r.stdout ?? "").split("\n")[0].trim();
  return (r.status === 0 || r.status === 1) && /^[0-9a-f]{40,64}$/.test(tree) ? { tree, clean: r.status === 0 } : null;
}

// Whether merging head into the base tip would leave the base's tree unchanged. Both are commit ids, so the
// answer never changes: kept for the life of the process (a hook checks every claim several times per call).
const inBase = new Map();
// The base's tip, commit time and tree, worked out once per pass over the claims, not once per claim.
const baseOf = (cwd, base) => {
  if (!base) return null;
  const tip = git(cwd, ["rev-parse", "--verify", "--quiet", base]).out.trim();
  let time, tree;
  return tip && { tip,
    time: () => (time ??= (Number(git(cwd, ["log", "-1", "--format=%ct", tip]).out.trim()) || 0) * 1000),
    tree: () => (tree ??= git(cwd, ["rev-parse", `${tip}^{tree}`]).out.trim()) };
};

// A claim ends when its branch is gone, when its branch has moved and is now merged into the base, or
// after IDLE_HOURS with no commit on the branch and no claim update. Merged also covers a squash or rebase
// merge, where the base got the branch's changes as new commits and the branch never becomes its ancestor:
// merging it would leave the base unchanged. Unlike deleting a branch, ending a claim loses no work, so the
// changes being in the base is enough. Either way the branch can be "merged" while its session still works:
// one that merged another session's branch (as a notice tells it to) and edits on holds only that branch's
// commits once it reaches the base. So a merged claim ends only when it has been quiet since the base got
// there and its checkout has nothing uncommitted. Checked only then, so a working session costs no merge here.
export function isLive(cwd, c, base, now = Date.now(), b = baseOf(cwd, base)) {
  const head = git(cwd, ["rev-parse", "--verify", "--quiet", `refs/heads/${c.branch}`]).out.trim();
  if (!head) return false;
  if (c.path && !existsSync(c.path)) return false;
  const lastCommit = (Number(git(cwd, ["log", "-1", "--format=%ct", head]).out.trim()) || 0) * 1000, touched = Date.parse(c.updated ?? c.at) || 0;
  // Commit times are whole seconds and claim times milliseconds: compare whole seconds, or a claim updated
  // in the same second as the base's commit looks newer than it (on a fast machine, every time).
  if (b && c.branch !== base && head !== c.start && b.time() >= Math.max(lastCommit, Math.floor(touched / 1000) * 1000)) {
    const key = `${b.tip}:${head}`;
    if (!inBase.has(key)) {
      let merged = git(cwd, ["merge-base", "--is-ancestor", head, b.tip]).ok;
      if (!merged) { const m = mergedTree(cwd, b.tip, head); merged = !!m?.clean && m.tree === b.tree(); }
      inBase.set(key, merged);
    }
    if (inBase.get(key) && !(c.path && git(c.path, ["status", "--porcelain"]).out.trim())) return false;
  }
  return Math.max(lastCommit, touched) > now - IDLE_HOURS * 3600 * 1000;
}
export function liveClaims(cwd, base) {
  const { claims } = readState(cwd), b = baseOf(cwd, base);
  return Object.values(claims).filter((c) => isLive(cwd, c, base, Date.now(), b));
}

// A claim's files and exposes are locks: no other session may change them. Its edits are the files it has
// changed so far, recorded as it goes: another session may change them too (both may need package.json), and
// is told who else is.
const covers = (c, rel) => [...(c.files ?? []), ...(c.exposes ?? [])].some((g) => matches(g, rel));
// The live claim of another branch locking rel, if any.
export const claimedByOther = (claims, branch, rel) => claims.find((c) => c.branch !== branch && covers(c, rel)) ?? null;
export const editedByOthers = (claims, branch, rel) => claims.filter((c) => c.branch !== branch && (c.edits ?? []).includes(rel));

// ---------- task overlap ----------
// A model call compares the new task with every live one (judge). Measured with bench/task-overlap.mjs on
// two sets of 40 labelled pairs written by other agents, the second held out until the prompt was fixed:
//   shared words (wordOverlap, kept as the baseline): at best 17/40 and 20/40, no better than chance;
//   Haiku: 36/40 and 33/40, no false alarms, but it missed a third of the held-out duplicates, mostly a bug
//     described by its symptom against the same bug described by its fix;
//   Sonnet: 40/40 on both, about $0.012 per check.
// So the judge runs on Sonnet (FANOUT_CLAIM_JUDGE_MODEL changes it), and with no judge the claim goes ahead
// with a warning rather than a word count's guess.
const STOP = new Set("a an the and or of to in on for with by from at as is are be into onto this that it its their our your new add make use using via so all any each per when then than not no".split(" "));
const stem = (w) => w.replace(/(ing|ed|es|s)$/, "") || w;
export const words = (s) => new Set(String(s).toLowerCase().split(/[^a-z0-9]+/).filter((w) => w.length > 2 && !STOP.has(w)).map(stem));
export function wordOverlap(a, b) {
  const A = words(a), B = words(b);
  if (!A.size || !B.size) return 0;
  let n = 0;
  for (const w of A) if (B.has(w)) n++;
  return n / Math.min(A.size, B.size);
}

// The model reasons about each session before it decides: asked for the decision first, it flagged pairs its
// own reason called different (5 of 8 false alarms in the first validation run).
export function judgePrompt(task, others) {
  return `Coding sessions are working in parallel on one repository. A new session wants to start the task below. Compare it with each existing session.

SAME work means: once either task is done, most of the other one is already done too, so doing both would duplicate effort or produce two competing implementations of one thing. This includes the same change described in different words or detail, one task containing the other, and a bug described by its symptom in one and by its fix in the other.
DIFFERENT work means: each task delivers something the other doesn't, so both are needed. Sharing a feature area, a file, a command, or a kind of work (both add tests, both add a flag, both improve search) does not make them the same.

New task: ${task}

Existing sessions:
${others.map((c) => `- ${c.name}: ${c.task || "(no task given)"}${c.files?.length ? ` [files: ${c.files.slice(0, 8).join(", ")}]` : ""}`).join("\n")}

For each existing session, first say what each task delivers, then decide. Reply with only JSON:
{"sessions": [{"name": "<session>", "reason": "<what each delivers, one sentence>", "same": true|false}]}`;
}

const bin = (name) => process.env[`FANOUT_${name.toUpperCase()}_BIN`] || name;
// Which CLI runs the check: FANOUT_CLAIM_JUDGE_AGENT (claude|codex), else Claude when it's signed in, else
// Codex when it is, so a Codex-only setup gets the check too. null when neither is.
export function judgeAgent(cwd) {
  const want = process.env.FANOUT_CLAIM_JUDGE_AGENT;
  if (want === "claude" || want === "codex") return want;
  const claude = spawnSync(`${bin("claude")} auth status`, { cwd, shell: true, encoding: "utf8", timeout: 30000 });
  try { if (JSON.parse((claude.stdout ?? "").slice(claude.stdout.indexOf("{"))).loggedIn === true) return "claude"; } catch { /* not there */ }
  if (process.env.ANTHROPIC_API_KEY) return "claude";
  if (spawnSync(`${bin("codex")} login status`, { cwd, shell: true, encoding: "utf8", timeout: 30000 }).status === 0) return "codex";
  return null;
}

// The judge's answer text from one model call, no tools: Claude (Sonnet by default, project settings only),
// or Codex (its own default model, low reasoning effort, read-only sandbox, nothing saved), whose last message
// is written to a file (-o). FANOUT_CLAIM_JUDGE_MODEL picks the model for either.
function askModel(agent, prompt, cwd) {
  const model = process.env.FANOUT_CLAIM_JUDGE_MODEL;
  if (agent === "claude") {
    const r = spawnSync(`${bin("claude")} -p --model ${model || "sonnet"} --tools "" --setting-sources project,local --strict-mcp-config --output-format json`,
      { cwd, shell: true, encoding: "utf8", input: prompt, timeout: 120000 });
    const out = r.stdout ?? "", j = JSON.parse(out.slice(out.indexOf("{")));
    return j.is_error ? null : { text: String(j.result ?? ""), costUsd: j.total_cost_usd ?? null };
  }
  const file = join(tmpdir(), `fanout-judge-${process.pid}-${Date.now()}.txt`);
  const effort = process.env.FANOUT_CLAIM_JUDGE_EFFORT || "low";
  const cmd = `${bin("codex")} exec --json --ephemeral -s read-only --skip-git-repo-check${model ? ` -m ${model}` : ""} -c model_reasoning_effort=${effort} -o "${file}"`;
  // Watched, not just waited on: when the account is rate-limited Codex keeps reconnecting after a 429 (seen on
  // the benchmark after a day of heavy use: calls ran into the timeout), so the first such event ends the call.
  // Answers took 12-22s; rate-limited, Codex often goes quiet without printing the 429 at all. So one 45s try,
  // and silence past that counts as unavailable too: the agent then compares the tasks itself.
  const r = spawnSync(process.execPath, ["-e", CODEX_WATCH, cmd], { cwd, encoding: "utf8", input: prompt, timeout: 45000 });
  if (r.status === 3 || r.error?.code === "ETIMEDOUT" || r.signal) return { rateLimited: true };
  try { return { text: readFileSync(file, "utf8"), costUsd: null }; } catch { return null; } finally { try { rmSync(file); } catch { /* none */ } }
}
// Runs the codex command with stdin passed through; exits 3 at the first rate-limit error event, or after 40s
// (inside fanout's 45s). It ends Codex's whole process tree itself: on Windows killing this process would leave
// codex running, and elsewhere killing only the shell left codex holding the output pipe open, so the check
// waited the full 45s (seen on Linux CI). So codex runs in its own process group there, and the group is killed.
const CODEX_WATCH = `const { spawn, spawnSync } = require("node:child_process");
const win = process.platform === "win32";
const p = spawn(process.argv[1], { shell: true, stdio: ["pipe", "pipe", "inherit"], detached: !win });
const stop = () => { if (win) spawnSync("taskkill", ["/pid", String(p.pid), "/T", "/F"], { stdio: "ignore" }); else try { process.kill(-p.pid, "SIGKILL"); } catch {} process.exit(3); };
setTimeout(stop, 40000).unref();
process.stdin.pipe(p.stdin);
let buf = "";
p.stdout.on("data", (d) => { buf += d; let i; while ((i = buf.indexOf("\\n")) >= 0) { const l = buf.slice(0, i); buf = buf.slice(i + 1);
  if (/"type":"(error|turn.failed)"/.test(l) && /429|rate.?limit|usage limit|too many requests/i.test(l)) stop(); } });
p.on("close", (c) => process.exit(c ?? 1));`;

// One model call comparing the task with every live claim. Returns { same: [names], why, agent, costUsd }
// (costUsd null for Codex: it uses the ChatGPT plan's quota) or null when it can't run (no CLI signed in,
// unreadable answer): the claim then goes ahead with a warning.
// Inside a Codex session's sandbox there's no network (CODEX_SANDBOX_NETWORK_DISABLED=1), so no model call can
// answer: one from fanout start there hung until its timeout. The agent compares the tasks itself instead.
export const noNetwork = () => process.env.CODEX_SANDBOX_NETWORK_DISABLED === "1";
export function judge(task, others, cwd) {
  if (process.env.FANOUT_CLAIM_JUDGE === "off" || !others.length || noNetwork()) return null;
  const agent = judgeAgent(cwd);
  if (!agent) return null;
  // Tried twice: on the held-out pairs 9 of 40 Codex calls hung until the timeout while other Codex
  // processes were running; alone, six in a row answered in 12-22s.
  for (let attempt = 0; attempt < 2; attempt++) {
    try {
      const r = askModel(agent, judgePrompt(task, others), cwd);
      if (r?.rateLimited) return null; // rate-limited or silent: another try would wait as long again
      if (!r) continue;
      const a = JSON.parse(r.text.slice(r.text.indexOf("{"), r.text.lastIndexOf("}") + 1));
      const names = new Set(others.map((c) => c.name)), hits = (a.sessions ?? []).filter((s) => s.same === true && names.has(s.name));
      return { same: hits.map((s) => s.name), why: hits.map((s) => s.reason).join(" ") || String((a.sessions ?? [])[0]?.reason ?? ""), agent, costUsd: r.costUsd };
    } catch { /* unreadable answer: try again */ }
  }
  return null;
}

// The live claims of other branches doing the same work as `task`. by: "judge", "none" (nothing to compare),
// or "unchecked" (the judge couldn't run).
export function taskOverlap(task, others, cwd) {
  if (!task || !others.length) return { same: [], by: "none" };
  const j = judge(task, others, cwd);
  if (!j) return { same: [], by: "unchecked" };
  return { same: others.filter((c) => j.same.includes(c.name)), why: j.why, by: "judge", costUsd: j.costUsd };
}

// ---------- notices ----------
// A running session is told when another session commits changes to a file it has read or edited: its own
// checkout still has the old code, and a clean merge can break anyway (two parallel patches that each pass
// alone, Xia et al. 2026: a message describing the other change recovered 82% of such breaks). The base branch
// counts as a session too, so work merged into it while this session runs is noticed the same way.
// Runs after every tool call (PostToolUse), so the common case costs no git call at all: no branch tip has moved
// (refsStamp) and the file just read or edited isn't one another session changed (the lists kept from the last
// check). What this session has read, and what it was told about each branch, live in a file in its own git dir
// (not on the shared ref: a write per Read would be a write for every session to see).
const NOTICE_DIFF_LINES = 60;
// Returns the notice text ("" when there's nothing new). read: a file this tool call read; edited: files it changed.
// all: every file another session changed is news, not only those this session used (fanout inbox: without hooks
// fanout can't see what an agent read).
export function notices(root, gitDir, branch, base, { read, edited = [], common = gitDir, all = false } = {}) {
  const file = join(gitDir, "fanout-notices.json"), stamp = refsStamp(common);
  let st; try { st = JSON.parse(readFileSync(file, "utf8")); } catch { st = { reads: [], changed: {}, told: {} }; }
  // Inside Codex's sandbox a worktree's git dir isn't writable: the notice then just comes again next time.
  const save = () => { try { writeFileSync(file, JSON.stringify(st)); } catch { /* read-only */ } };
  const touched = [read, ...edited].filter(Boolean), newRead = read && !st.reads.includes(read);
  if (newRead) st.reads.push(read);
  if (!all && stamp === st.stamp && !touched.some((f) => Object.values(st.changed).some((c) => c.files.includes(f)))) { if (newRead) save(); return ""; }
  st.stamp = stamp;
  const tips = {};
  for (const l of git(root, ["for-each-ref", "--format=%(refname:short) %(objectname)", "refs/heads"]).out.split("\n")) { const [b, t] = l.split(" "); if (b && b !== branch) tips[b] = t; }
  const live = liveClaims(root, base), mineClaim = live.find((c) => c.branch === branch);
  const edits = new Set([...(mineClaim?.edits ?? []), ...edited]), mine = new Set([...st.reads, ...edits]);
  const sessions = [...live.filter((c) => c.branch !== branch), ...(base && base !== branch && tips[base] ? [{ branch: base, name: base, base: true }] : [])];
  const out = [], changedNow = {};
  for (const c of sessions) {
    const tip = tips[c.branch];
    if (!tip) continue;
    // Every file the other side changed since this session's code split from it (kept for the fast path), of
    // those this session uses, minus what it was already told at this tip; a newer tip makes them news again.
    const prev = st.changed[c.branch];
    if (prev?.tip === tip) changedNow[c.branch] = prev;
    else {
      const from = git(root, ["merge-base", "HEAD", tip]).out.trim();
      changedNow[c.branch] = { tip, from, files: from && from !== tip ? git(root, ["diff", "--name-only", from, tip]).out.split("\n").filter(Boolean) : [] };
    }
    const { from, files } = changedNow[c.branch], told = st.told[c.branch] ?? { tip: null, files: [] };
    const sinceTold = told.tip && told.tip !== tip ? git(root, ["diff", "--name-only", told.tip, tip]).out.split("\n") : [];
    let hits = all ? files : files.filter((f) => mine.has(f));
    let fresh = hits.filter((f) => !told.files.includes(f) || sinceTold.includes(f));
    // Only what merging their branch would change here is news. A change this checkout already has (their
    // branch was squash- or rebase-merged into the base, and this session has the base's version) isn't.
    // Checked only when something is new, since this runs whenever any branch moves.
    if (fresh.length) {
      const m = mergedTree(root, "HEAD", tip);
      if (m) { const would = new Set(git(root, ["diff", "--name-only", "HEAD", m.tree]).out.split("\n")); hits = hits.filter((f) => would.has(f)); fresh = fresh.filter((f) => would.has(f)); }
    }
    st.told[c.branch] = { tip, files: [...new Set([...told.files.filter((f) => !sinceTold.includes(f)), ...hits])] };
    if (!fresh.length) continue;
    logEvent(root, { kind: "notice", via: all ? "inbox" : "hook", session: branch, from: c.branch, files: fresh, ...(all ? { yours: fresh.filter((f) => mine.has(f)) } : {}) }, common);
    const diff = git(root, ["diff", from, tip, "--", ...fresh]).out.split("\n");
    const shown = diff.slice(0, NOTICE_DIFF_LINES).join("\n") + (diff.length > NOTICE_DIFF_LINES ? `\n... (${diff.length - NOTICE_DIFF_LINES} more lines: git diff ${from.slice(0, 9)} ${c.branch} -- ${fresh.join(" ")})` : "");
    const who = c.base ? `New commits on ${c.branch} (work merged since this session started)` : `Session "${c.name}" (branch ${c.branch}${c.task ? `: ${c.task.slice(0, 120)}` : ""}) committed`;
    const yours = fresh.filter((f) => mine.has(f)), both = fresh.filter((f) => edits.has(f));
    out.push(`fanout: ${who} change ${fresh.join(", ")}, ${all ? (yours.length ? `and you changed ${yours.join(", ")} too.` : "which your work may use.") : "which this session has read or edited."} Your checkout still has the old version:\n${shown}\n`
      // "If your work depends on this code" alone: a session that added a line next to the other's in the same
      // file judged it didn't depend on it, didn't merge, and the branches conflicted (bench/RESULTS.md).
      + (both.length ?`You changed ${both.join(", ")} too, so your branches will conflict there when merged, even if your work doesn't depend on theirs. Before you commit, merge their branch (git merge ${c.branch}) and resolve the conflict, keeping both changes.`
        : `If your work depends on this code, build against the new version: bring it in (git merge ${c.branch}) or ask the user, rather than writing code that only works with the old one.`));
  }
  st.changed = changedNow;
  save();
  return out.join("\n\n");
}

// ---------- commands ----------
const ago = (iso) => { const m = Math.round((Date.now() - Date.parse(iso)) / 60000); return m < 60 ? `${m}m` : m < 2880 ? `${Math.round(m / 60)}h` : `${Math.round(m / 1440)}d`; };
const optOf = (argv, f) => { const i = argv.indexOf(f); return i >= 0 ? argv[i + 1] : undefined; };
const positional = (argv) => argv.filter((a, i) => !a.startsWith("--") && !(i > 0 && ["--exposes", "--distinct", "--to", "--base"].includes(argv[i - 1])));

export function claimCmd(cwd, argv, base, script) {
  const [name0, task, ...files] = positional(argv);
  const name = slugName(name0 ?? "");
  if (!name || !task) { console.error(`usage: fanout claim <name> "<what this session is doing>" [files or globs...] [--exposes a,b]`); return 2; }
  const branch = branchOf(cwd);
  if (!branch) { console.error("fanout claim: check out a branch first; a claim belongs to a branch."); return 2; }
  const exposes = (optOf(argv, "--exposes") ?? "").split(",").map((s) => s.trim()).filter(Boolean), distinct = optOf(argv, "--distinct");
  const live = liveClaims(cwd, base), mine = live.find((c) => c.name === name);
  const taken = live.find((c) => c.name === name && c.branch !== branch);
  if (taken) { console.error(`fanout claim: "${name}" is already claimed by branch ${taken.branch} (${taken.task}). Pick another name, or if that session is finished: fanout release ${name}`); return 1; }
  const others = live.filter((c) => c.branch !== branch);
  const clash = [...files, ...exposes].flatMap((f) => others.filter((c) => [...(c.files ?? []), ...(c.exposes ?? [])].some((g) => matches(g, f) || matches(f, g))).map((c) => `${f} (claimed by ${c.name} on ${c.branch})`));
  if (clash.length) { console.error(`fanout claim: these are already claimed:\n  ${clash.join("\n  ")}\nLeave them to that session, or ask it to release them.`); return 1; }
  let by = "none";
  // The same claim again (AGENTS.md asks for it just before the first edit): compare it with any older claim it
  // hasn't met yet, which is how two sessions that started at the same moment find each other.
  if (!distinct && mine && mine.task === task && !mine.refusedAs) {
    const rc = recheckClaim(cwd, mine, live, "cli");
    if (rc.refused.length) logEvent(cwd, { kind: "refused", via: "recheck", session: name, branch, task, as: rc.refused.map((c) => c.name), asTasks: rc.refused.map((c) => c.task), why: rc.why });
    if (rc.refused.length) { console.error(`fanout claim: this looks like the same work as:\n${rc.refused.map((c) => `  ${c.name} (branch ${c.branch}, claimed earlier): ${c.task}`).join("\n")}${rc.why ? `\n  (${rc.why})` : ""}\nDon't do it twice: tell the user which session already has it.`); return 1; }
    if (rc.unchecked.length) console.log(selfCheckText(rc.unchecked, name, script));
  }
  if (!distinct && !(mine && mine.task === task && !mine.refusedAs)) {
    const o = taskOverlap(task, others, cwd);
    by = o.by;
    if (o.same.length) logEvent(cwd, { kind: "refused", via: "cli", session: name, branch, task, as: o.same.map((c) => c.name), asTasks: o.same.map((c) => c.task), why: o.why, by: o.by, costUsd: o.costUsd });
    if (o.same.length) {
      console.error(`fanout claim: this looks like the same work as:\n${o.same.map((c) => `  ${c.name} (branch ${c.branch}, ${ago(c.updated ?? c.at)} ago): ${c.task}`).join("\n")}${o.why ? `\n  (${o.why})` : ""}\n`
        + `Don't do it twice: pick other work, or coordinate with that session. If it really is different, run again with --distinct "<how it differs>".`);
      return 1;
    }
  }
  const start = git(cwd, ["rev-parse", "HEAD"]).out.trim(), now = new Date().toISOString();
  const path = git(cwd, ["rev-parse", "--show-toplevel"]).out.trim();
  const w = writeState(cwd, (claims) => {
    const b = baseOf(cwd, base);
    for (const c of Object.values(claims)) if (!isLive(cwd, c, base, Date.now(), b)) delete claims[c.name]; // prune expired ones
    const cur = claims[name];
    // A fresh claim clears an earlier refusal (refusedAs) for this session. unchecked: no model compared it.
    claims[name] = { name, task, branch, path, files: [...new Set([...(cur?.files ?? []), ...files])], exposes: [...new Set([...(cur?.exposes ?? []), ...exposes])],
      edits: cur?.edits ?? [], start: cur?.start ?? start, at: cur?.at ?? now, updated: now, ...(distinct ? { distinct } : {}), ...(by === "unchecked" ? { unchecked: true } : {}),
      comparedWith: [...new Set([...(cur?.comparedWith ?? []), ...(by !== "none" ? others.map((c) => c.name) : [])])] };
  }, `fanout: claim ${name}`);
  if (!w.ok) { console.error("fanout claim: couldn't write the claim (the state ref kept changing); try again."); return 1; }
  logEvent(cwd, { kind: "claim", via: "cli", session: name, branch, task, files, by, ...(distinct ? { distinct } : {}) });
  console.log(`claimed ${name} for ${branch}: ${task}${files.length ? ` (${files.join(", ")})` : ""}`);
  // No model to ask (a sandbox without network, no CLI signed in): the agent running this is one, so it
  // compares the tasks itself, as Claude sessions shown the list did (the duplicate one stopped).
  if (by === "unchecked") console.log(selfCheckText(others, name, script));
  if (!claimsActive(cwd)) console.log(`Claims aren't on in this repo (only one session is active); run \`node "${script}" init\` to keep them on.`);
  return 0;
}

// The list an agent compares its task with when no model can (a sandbox without network, no CLI signed in).
export const selfCheckText = (others, name, script) => `\nOther sessions are working here right now:\n${others.map((c) => `  ${c.name} (branch ${c.branch}): ${c.task || "(no task)"}`).join("\n")}\n`
  + `${noNetwork() ? "fanout can't reach a model from this sandbox to compare them with your task" : "fanout couldn't compare them with your task (no claude or codex CLI signed in)"}, so do it yourself now: `
  + `if your task is the same work as one of these (even in other words, or one containing the other), don't do it. Run node "${script}" release ${name} and tell the user which session already has it.`;

// fanout start "<task>" [files...]: claim this session's task without picking a name (its claim, or one named
// after its branch). For agents told about fanout in AGENTS.md; Claude Code sessions are claimed on their own.
export function startCmd(cwd, argv, base, script) {
  const branch = branchOf(cwd);
  if (!branch) { console.error("fanout start: check out a branch first."); return 2; }
  const mine = liveClaims(cwd, base).filter((c) => c.branch === branch).sort((a, b) => Date.parse(b.updated ?? b.at) - Date.parse(a.updated ?? a.at))[0];
  return claimCmd(cwd, [mine?.name ?? slugName(branch), ...argv], base, script);
}

// Sessions that claim at the same moment can't see each other: with two Codex sessions started together, each
// ran fanout start before the other's claim existed, and both built the same feature. So at each later
// checkpoint (an edit, fanout start or done, a commit) a claim is compared once with every older live claim it
// hasn't been compared with yet; the newer one yields. Each pair is judged at most once (comparedWith).
// Returns { refused: claims it's the same work as, unchecked: older claims no model could compare, why }.
export function recheckClaim(cwd, mine, live, via = "cli") {
  const older = live.filter((c) => c.branch !== mine.branch && !c.refusedAs && !(mine.comparedWith ?? []).includes(c.name)
    && (Date.parse(c.at) < Date.parse(mine.at) || (c.at === mine.at && c.name < mine.name)));
  if (!older.length || !mine.task || mine.distinct) return { refused: [], unchecked: [] };
  const o = taskOverlap(mine.task, older, cwd);
  const refused = o.same, unchecked = o.by === "unchecked" ? older : [];
  writeState(cwd, (claims) => {
    const c = claims[mine.name];
    if (!c || c.branch !== mine.branch) return false;
    c.comparedWith = [...new Set([...(c.comparedWith ?? []), ...older.map((x) => x.name)])];
    if (refused.length) { c.refusedAs = refused.map((x) => x.name); c.why = o.why; }
  }, `fanout: recheck ${mine.name}`);
  if (refused.length) { mine.refusedAs = refused.map((x) => x.name); mine.why = o.why; }
  if (refused.length && via !== "cli") logEvent(cwd, { kind: "refused", via, session: mine.name, branch: mine.branch, task: mine.task, as: refused.map((x) => x.name), asTasks: refused.map((x) => x.task), why: o.why });
  return { refused, unchecked, why: o.why };
}

// Claude Code sessions, on their first edit: the claim is made for them, with the user's request as the task,
// and checked against the others like any claim. A session doing work another already claimed is stopped,
// and stays stopped (refusedAs) until it claims something else or says how its work differs.
// The claim is written before the check, marked checking: the model call takes seconds (38s once, in the demo),
// and a session whose first edit came meanwhile didn't see this one and claimed the same work too. Now it sees it,
// and of two claims for the same work only the newer yields. Another hook of this session (agents often edit two
// files at once) waits for the check rather than going ahead (waitChecked); one of them got through that way.
export const claimsAt = (a, b) => Date.parse(a.at) < Date.parse(b.at) || (a.at === b.at && a.name < b.name); // a is older
export function autoClaim(cwd, branch, task, base, live, via = "edit") {
  const others = live.filter((c) => c.branch !== branch);
  const name = slugName(branch), now = new Date().toISOString();
  const claim = { name, task: task.slice(0, 600), branch, path: git(cwd, ["rev-parse", "--show-toplevel"]).out.trim(), files: [], exposes: [], edits: [],
    start: git(cwd, ["rev-parse", "HEAD"]).out.trim(), at: now, updated: now, auto: true, comparedWith: others.map((c) => c.name), checking: true }; // tried once, whatever the outcome
  let existing = null;
  writeState(cwd, (claims) => { if (claims[name]?.branch === branch) { existing = claims[name]; return false; } claims[name] = claim; }, `fanout: claim ${name} (first edit)`);
  if (existing) return waitChecked(cwd, existing);
  const o = prechecked(cwd, task, others) ?? taskOverlap(task, others, cwd);
  const same = o.same.filter((c) => claimsAt(c, claim)); // a newer one yields to this, not the other way round
  delete claim.checking;
  if (same.length) { claim.refusedAs = same.map((c) => c.name); claim.why = o.why; }
  writeState(cwd, (claims) => { const c = claims[name]; if (!c || c.branch !== branch) return false; delete c.checking; if (same.length) { c.refusedAs = claim.refusedAs; c.why = o.why; } }, `fanout: checked ${name}`);
  logEvent(cwd, { kind: same.length ? "refused" : "claim", via, session: name, branch, task: claim.task, by: o.by, costUsd: o.costUsd ?? null, ...(o.early ? { early: true } : {}),
    ...(same.length ? { as: same.map((c) => c.name), asTasks: same.map((c) => c.task), why: o.why } : {}) });
  return claim;
}
// The same check, started when the user sends the request (UserPromptSubmit), so the first edit finds the
// answer ready instead of waiting about 15s for the model. Kept in the session's git dir, not as a claim: a
// session that only answers a question never edits, and a claim for it could refuse a later session doing the work.
const PRECHECK = "fanout-precheck.json", sig = (c) => `${c.name}\n${c.task}`;
const pause = (ms) => Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms);
export function precheck(cwd, branch, task, base) {
  const gitDir = repoInfo(cwd)?.gitDir, others = liveClaims(cwd, base).filter((c) => c.branch !== branch);
  if (!gitDir || !task || !others.length) return;
  // Two messages sent in a row start two of these: the same task is checked once.
  let was; try { was = JSON.parse(readFileSync(join(gitDir, PRECHECK), "utf8")); } catch { was = null; }
  if (was?.task === task && (was.pending ? Date.now() - was.at < 120000 : others.every((c) => was.others?.includes(sig(c))))) return;
  const put = (x) => { try { writeFileSync(join(gitDir, PRECHECK), JSON.stringify({ task, at: Date.now(), ...x })); } catch { /* read-only */ } };
  put({ pending: true });
  const o = taskOverlap(task, others, cwd);
  put({ others: others.map(sig), same: o.same.map((c) => c.name), why: o.why, by: o.by, costUsd: o.costUsd ?? null });
}
// Sessions that claimed since the early check are checked now, on their own.
function prechecked(cwd, task, others) {
  const file = join(repoInfo(cwd)?.gitDir ?? tmpdir(), PRECHECK);
  const read = () => { try { return JSON.parse(readFileSync(file, "utf8")); } catch { return null; } };
  let p = read();
  if (p?.task !== task) return null;
  while (p?.pending && Date.now() - p.at < 120000) { pause(500); p = read(); }
  try { rmSync(file); } catch { /* gone */ }
  if (!p || p.pending || p.by !== "judge" || Date.now() - p.at > 3600e3) return null;
  const known = new Set(p.others), fresh = others.filter((c) => !known.has(sig(c)));
  const o = fresh.length ? taskOverlap(task, fresh, cwd) : { same: [] };
  if (fresh.length && o.by !== "judge") return null;
  return { same: [...others.filter((c) => known.has(sig(c)) && p.same.includes(c.name)), ...o.same], why: [p.why, o.why].filter(Boolean).join("; "),
    by: "judge", costUsd: (p.costUsd ?? 0) + (o.costUsd ?? 0), early: true };
}

// This session's claim, once its check is done (at most 2 minutes: the check's own timeout).
export function waitChecked(cwd, claim, timeoutMs = 120000) {
  const end = Date.now() + timeoutMs;
  let c = claim;
  while (c?.checking && Date.now() < end) {
    pause(500);
    c = readState(cwd).claims[claim.name] ?? null;
  }
  return c ?? claim;
}
export const refusalText = (c, live, script) => {
  const same = live.filter((x) => (c.refusedAs ?? []).includes(x.name));
  return `this session's task looks like the same work as another session's:\n${same.map((x) => `  ${x.name} (branch ${x.branch}): ${x.task}`).join("\n") || `  ${c.refusedAs.join(", ")}`}${c.why ? `\n  (${c.why})` : ""}\n`
    + `Don't do it twice: tell the user which session already has it. If the user wants a different part, claim that: node "${script}" start "<what you'll do instead>". If it really is different work: node "${script}" start "${c.task.slice(0, 80).replace(/"/g, "'")}" --distinct "<how it differs>"`;
};

export function showClaims(cwd, base, all) {
  const { claims } = readState(cwd);
  const b = baseOf(cwd, base), list = Object.values(claims).map((c) => ({ ...c, live: isLive(cwd, c, base, Date.now(), b) })).filter((c) => all || c.live);
  if (!list.length) { console.log(all ? "No claims." : "No live claims."); return 0; }
  for (const c of list.sort((a, b) => (a.branch < b.branch ? -1 : 1)))
    console.log(`${c.name}${c.live ? "" : " (expired)"}${c.refusedAs ? ` (stopped: same work as ${c.refusedAs.join(", ")})` : ""}  ${c.branch}  ${ago(c.updated ?? c.at)} ago  ${c.task || "(no task)"}`
      + `${c.files?.length ? `\n  files: ${c.files.join(", ")}` : ""}${c.exposes?.length ? `\n  exposes: ${c.exposes.join(", ")}` : ""}${c.edits?.length ? `\n  editing: ${c.edits.join(", ")}` : ""}`);
  return 0;
}

export function releaseCmd(cwd, argv) {
  const name = slugName(positional(argv)[0] ?? ""), to = optOf(argv, "--to");
  if (!name) { console.error("usage: fanout release <name> [--to <branch>]"); return 2; }
  let was = null;
  const w = writeState(cwd, (claims) => {
    if (!claims[name]) return false;
    was = claims[name];
    if (to) claims[name] = { ...was, branch: to, path: null, updated: new Date().toISOString() };
    else delete claims[name];
  }, `fanout: release ${name}`);
  if (!w.ok) { console.error("fanout release: couldn't write; try again."); return 1; }
  if (!was) { console.error(`fanout release: no claim named ${name}.`); return 1; }
  console.log(to ? `handed ${name} from ${was.branch} to ${to}` : `released ${name} (was ${was.branch}: ${was.task})`);
  return 0;
}

// The block fanout init puts in AGENTS.md, for agents without fanout's hooks (Codex and others): two commands.
// AGENTS.md is committed and shared, so they run fanout through npx, not this machine's path to the script.
const BLOCK_START = "<!-- fanout -->", BLOCK_END = "<!-- /fanout -->";
export const FANOUT_NPX = "npx -y github:Breadstick-Crumbs/fanout";
export const agentsBlock = () => `${BLOCK_START}
## Other sessions may be working here too (fanout)

- First, before you read or change any code, run \`${FANOUT_NPX} start "<your task in one line>"\`. It claims your task and shows what the other sessions are doing. If it says another session already has that work, or lists one doing the same thing, don't do it: tell the user which one has it. Commits are refused until you've run it.
- Run the same command again just before your first edit: a session that started at the same moment as yours shows up then.
- Before you commit, and again before you finish, run \`${FANOUT_NPX} inbox\`. It shows changes other sessions have committed since you started, with the diff. If one changes code your work uses, build against the new version (merge their branch, or tell the user) instead of code that only works with the old one.
- When you've committed, run \`${FANOUT_NPX} done\`. It tests your branch merged with the other sessions' work and says if one breaks the other.
${BLOCK_END}`;

// Turns claims on for good (not only when two sessions are active), installs the git hook, and writes the
// AGENTS.md block (replacing an earlier one) so agents without hooks know the two commands.
export function initCmd(cwd, script, installHook, argv) {
  git(cwd, ["config", "fanout.claims", "true"]);
  const hook = installHook(cwd, argv.includes("--force"));
  const root = git(cwd, ["rev-parse", "--show-toplevel"]).out.trim(), file = join(root, "AGENTS.md");
  let text = ""; try { text = readFileSync(file, "utf8"); } catch { /* new file */ }
  const block = agentsBlock(), i = text.indexOf(BLOCK_START), j = text.indexOf(BLOCK_END);
  text = i >= 0 && j > i ? text.slice(0, i) + block + text.slice(j + BLOCK_END.length) : `${text}${text && !text.endsWith("\n") ? "\n" : ""}${text ? "\n" : ""}${block}\n`;
  writeFileSync(file, text);
  console.log(`Claims are on for this repo. Each session's task is claimed before its first edit; work another session already has is refused.`);
  if (hook) console.log("(The git hook wasn't installed, so only Claude Code sessions are held to claims; see above.)");
  console.log(`Wrote the instructions for agents without fanout's hooks (Codex and others) to AGENTS.md. Commit it so every session sees it.`);
  return 0;
}
