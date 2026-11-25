import { spawn, spawnSync } from "node:child_process";
import { existsSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { tmpdir } from "node:os";
import { fileURLToPath } from "node:url";
import { win as WIN, stopProcess } from "./workspace.mjs";

const SCRIPT = fileURLToPath(new URL("./fanout.mjs", import.meta.url));
const tail = (s, n = 20) => s.trimEnd().split("\n").slice(-n).join("\n");
const q = (s) => (WIN ? `"${s}"` : `'${s.replaceAll("'", `'\\''`)}'`);

// Binaries can be swapped (tests point these at a fake agent).
const bin = (name) => process.env[`FANOUT_${name.toUpperCase()}_BIN`] || name;

export function agentEnv(agent, cleanEnv) {
  const env = { ...process.env };
  if (cleanEnv && agent === "claude") {
    for (const key of Object.keys(env)) if (/^(?:CLAUDE|ANTHROPIC)/i.test(key)) delete env[key];
  }
  return env;
}

function executable(name) {
  const command = bin(name);
  return existsSync(command) ? q(resolve(command)) : command;
}

export function signInProblem(kinds, { cwd = process.cwd(), cleanEnv = process.env.FANOUT_SCRUB_ENV === "1", userSettings = false, model } = {}) {
  for (const kind of new Set(kinds)) {
    if (!["claude", "codex"].includes(kind)) continue;
    const env = agentEnv(kind, cleanEnv);
    const probe = (args, input) => spawnSync(`${executable(kind)} ${args.join(" ")}`,
      { cwd, env, input, shell: true, encoding: "utf8", timeout: 45000, windowsHide: true });
    if (kind === "claude") {
      const ping = (useSettings) => {
        const r = probe(["-p", "--tools", q(""), "--max-turns", "1", "--output-format", "json", "--strict-mcp-config",
          ...settingSources(useSettings), ...(model ? ["--model", q(model)] : [])], "Reply only OK.");
        let answer;
        try { answer = JSON.parse(r.stdout); } catch { /* malformed result is a failed probe */ }
        return r.status === 0 && answer && !answer.is_error ? null
          : r.stderr?.trim() || answer?.result || r.error?.message || r.stdout?.trim() || "no response";
      };
      const problem = ping(userSettings);
      if (problem && ((userSettings || process.env.FANOUT_USER_SETTINGS) || ping(true)))
        return `claude is not signed in or could not start: ${problem}. Run \`claude auth login\` or verify the CLI environment.`;
    } else {
      const status = probe(["login", "status"]);
      if (status.status !== 0) return `codex is not signed in: ${(status.stderr || status.stdout || status.error?.message || "login status failed").trim()}. Run \`codex login\`.`;
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
  if (!r.error || r.budgetExceeded || opts.strictResume) return r;
  const fresh = await withSettingsFallback({ ...opts, tokenBudget: remainingBudget(opts.tokenBudget, r), prompt: fallbackPrompt ?? opts.prompt });
  return combine(fresh, r);
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
const settingSources = (userSettings = Boolean(process.env.FANOUT_USER_SETTINGS)) => (userSettings ? [] : ["--setting-sources", "project,local"]);

// fanout's edit guard, as a plain hook in a settings file passed with --settings, so every session agent
// has it whatever the user has installed. (Loading fanout with --plugin-dir would also bring the guard,
// but Claude Code then protects the plugin's own files: agents working on a checkout of fanout itself
// could not edit anything, and said nothing.)
let guardFile = null;
function guardSettings(preview) {
  const path = join(tmpdir(), `fanout-guard-${process.pid}.json`);
  if (!guardFile && !preview) {
    guardFile = path;
    const hook = { type: "command", command: `node "${SCRIPT.replaceAll("\\", "/")}" guard` };
    writeFileSync(guardFile, JSON.stringify({ hooks: { PreToolUse: [{ matcher: "Write|Edit|NotebookEdit|apply_patch", hooks: [hook] }] } }));
  }
  return ["--settings", q(path.replaceAll("\\", "/"))];
}

// Some setups keep what Claude needs to run at all in the user's settings (Bedrock or Vertex, a proxy, an
// API key helper). If a lean start fails before doing any work, run once more with the user's settings.
async function withSettingsFallback(opts) {
  const r = await runOnce(opts);
  if ((opts.agent ?? "claude") !== "claude" || opts.userSettings || process.env.FANOUT_USER_SETTINGS || !r.error || r.budgetExceeded || r.turns > 0) return r;
  const again = await runOnce({ ...opts, userSettings: true, tokenBudget: remainingBudget(opts.tokenBudget, r) });
  again.fellBack = true;
  return combine(again, r);
}

// The plan's own commands (test:, check:) are allowed exactly as written, so a session can run them
// before it finishes (on a real project the test was `bash tools/check-theme.sh`, which agents were
// refused). Commands with quotes or commas are left out: they can't go through --allowedTools safely.
export const allowCommands = (cmds) => cmds.filter((c) => c && !/["',]/.test(c)).map((c) => `Bash(${c})`);

export const tokenCount = (r) => r.inTokens + r.outTokens;
const remainingBudget = (limit, r) => limit == null ? undefined : Math.max(0, limit - tokenCount(r));

function combine(current, earlier) {
  for (const key of ["seconds", "inTokens", "cachedTokens", "outTokens"]) current[key] += earlier[key];
  if (current.costUsd != null && earlier.costUsd != null) current.costUsd += earlier.costUsd;
  current.sessionId ??= earlier.sessionId;
  return current;
}

export function agentCommand({ agent = "claude", cwd, model, budget, allowGit = false, allow = [], resume, userSettings, lane = false,
  codexEffort = process.env.FANOUT_CODEX_EFFORT ?? "low", codexTier = process.env.FANOUT_CODEX_TIER ?? "" }, preview = false) {
  let cmd;
  if (agent === "claude") {
    const tools = ["Read", "Edit", "Write", "Glob", "Grep", "Bash(node:*)", "Bash(npm:*)", ...READ_ONLY_BASH, ...(allowGit ? ["Bash(git:*)"] : []), ...allowCommands(allow)];
    const sources = settingSources(userSettings);
    cmd = [executable("claude"), "-p", ...(resume ? ["--resume", q(resume)] : []), "--tools", CLAUDE_TOOLS, "--permission-mode", "acceptEdits", "--allowedTools", q(tools.join(",")), "--output-format", "stream-json", "--verbose",
      "--strict-mcp-config", ...sources, ...guardSettings(preview), ...(model ? ["--model", q(model)] : []), ...(budget ? ["--max-budget-usd", q(String(budget))] : [])].join(" ");
  } else if (agent === "codex") {
    // Codex sessions run on low reasoning effort: on the sheet benchmark they took 165-201s against
    // 287-611s at Codex's default, with the same hidden-test score. FANOUT_CODEX_EFFORT (minimal|low|medium|
    // high) overrides it; "default" leaves Codex's own setting. FANOUT_CODEX_TIER sets its service tier
    // ("fast" = Codex's Fast tier, service_tier=priority: about a fifth quicker there, at more usage).
    const effort = codexEffort === "default" ? null : codexEffort;
    const tier = codexTier === "fast" ? "priority" : codexTier;
    const conf = (k, v) => (v && /^\w+$/.test(v) ? ["-c", `${k}=${v}`] : []);
    cmd = [executable("codex"), "exec", "--json", "-s", "workspace-write", "-C", q(cwd),
      ...(!lane ? ["--skip-git-repo-check"] : []), ...(model ? ["-m", q(model)] : []),
      ...conf("model_reasoning_effort", effort), ...conf("service_tier", tier), ...(resume ? ["resume", q(resume)] : []), "-"].join(" ");
  } else cmd = agent;
  return cmd;
}

function runOnce(opts) {
  const { agent = "claude", cwd, prompt, cleanEnv = process.env.FANOUT_SCRUB_ENV === "1", tokenBudget, onStart, onSession, onStop } = opts;
  const rec = { agent, model: opts.model, seconds: 0, costUsd: null, inTokens: 0, cachedTokens: 0, outTokens: 0, summary: "", error: null, sessionId: null };
  const exceeded = () => {
    rec.budgetExceeded = true;
    rec.error = `token budget reached (${tokenCount(rec)} reported tokens; ${tokenBudget} remaining at start)`;
  };
  if (tokenBudget === 0) { exceeded(); return Promise.resolve(rec); }

  return new Promise((done) => {
    const t0 = Date.now(), cmd = agentCommand(opts);
    const p = spawn(cmd, { cwd, shell: true, env: agentEnv(agent, cleanEnv), detached: !WIN, windowsHide: true });
    if (p.pid) onStart?.(p.pid);
    let pending = "", diagnostics = "", trace = "";
    const claudeMessages = new Set();
    const diagnostic = (value) => { diagnostics = (diagnostics + value).slice(-8000); };
    const usage = (u, replace = false) => {
      const cached = agent === "claude" ? u.cache_read_input_tokens ?? 0 : u.cached_input_tokens ?? 0;
      const input = (u.input_tokens ?? 0) + (agent === "claude" ? cached + (u.cache_creation_input_tokens ?? 0) : 0);
      rec.inTokens = (replace ? 0 : rec.inTokens) + input;
      rec.cachedTokens = (replace ? 0 : rec.cachedTokens) + cached;
      rec.outTokens = (replace ? 0 : rec.outTokens) + (u.output_tokens ?? 0);
      if (tokenBudget != null && tokenCount(rec) >= tokenBudget) {
        exceeded();
        stopProcess(p.pid);
      }
    };
    const event = (line) => {
      let e;
      try { e = JSON.parse(line); } catch { diagnostic(line + "\n"); return; }
      if (!e || typeof e !== "object") return;
      const id = agent === "claude" ? e.session_id : e.type === "thread.started" ? e.thread_id : null;
      if (id && id !== rec.sessionId) { rec.sessionId = id; onSession?.(id); }
      if (agent === "claude") {
        if (e.type === "assistant") {
          const u = e.message?.usage, id = e.message?.id;
          if (u && (!id || !claudeMessages.has(id))) {
            if (id) claudeMessages.add(id);
            usage(u);
          }
          rec.tools ??= {};
          for (const c of e.message?.content ?? []) if (c.type === "tool_use")
            (rec.tools[c.name] ??= []).push(c.input?.file_path ?? c.input?.pattern ?? c.input?.command ?? "");
        }
        if (e.type === "result" || (!e.type && (e.session_id || e.is_error))) {
          if (e.usage) usage(e.usage, true);
          rec.costUsd = e.total_cost_usd ?? null;
          rec.turns = e.num_turns ?? null;
          rec.modelSeconds = e.duration_api_ms != null ? Math.round(e.duration_api_ms / 1000) : null;
          if (typeof e.result === "string") rec.summary = e.result;
          if (e.is_error && !rec.budgetExceeded) rec.error = String(e.result ?? e.subtype).slice(0, 200);
        }
      } else if (agent === "codex") {
        if (e.type === "turn.completed" && e.usage) usage(e.usage);
        if (e.type === "item.completed" && e.item?.type === "agent_message") rec.summary = e.item.text ?? "";
        if (e.type === "turn.failed" && !rec.budgetExceeded) rec.error = JSON.stringify(e.error ?? e).slice(0, 200);
      } else if (e.type === "usage" && e.usage) {
        if (typeof e.model === "string") rec.model = e.model;
        usage(e.usage);
      } else if (e.type === "summary" && typeof e.text === "string") {
        rec.summary = e.text;
      } else {
        diagnostic(line + "\n");
      }
    };
    p.stdout.setEncoding("utf8");
    p.stderr.setEncoding("utf8");
    p.stdout.on("data", (chunk) => {
      if (agent === "claude" && process.env.FANOUT_TRACE_DIR) trace += chunk;
      const lines = (pending + chunk).split("\n");
      pending = lines.pop();
      for (const line of lines) event(line);
    });
    p.stderr.on("data", diagnostic);
    p.stdin.on("error", () => {});
    p.stdin.end(prompt);
    p.on("error", (error) => { rec.error = error.message; });
    p.on("close", (code, signal) => {
      if (pending) event(pending);
      onStop?.(p.pid);
      rec.seconds = Math.round((Date.now() - t0) / 1000);
      rec.tools ??= {};
      if (trace) {
        const tag = (rec.sessionId ?? "agent").slice(0, 8).replace(/[^\w-]/g, "_");
        try { writeFileSync(join(process.env.FANOUT_TRACE_DIR, `${Date.now()}-${tag}.jsonl`), trace); }
        catch (e) { console.error(`fanout: could not save Claude trace: ${e.message}`); }
      }
      if (!["claude", "codex"].includes(agent) && !rec.summary) rec.summary = diagnostics.trim();
      if (code !== 0 && !rec.error) rec.error = `exit ${code ?? signal}: ${tail(diagnostics, 3)}`.slice(0, 300);
      if (code === 0 && !rec.error && ["claude", "codex"].includes(agent) && !rec.sessionId)
        rec.error = `no ${agent} session was reported: ${tail(diagnostics, 3)}`.slice(0, 300);
      done(rec);
    });
  });
}
