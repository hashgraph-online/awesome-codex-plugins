// fanout demo: claims and notices with real Claude Code sessions, in a throwaway repo, in about two minutes.
//   fanout demo [--yes] [--record demo.svg] [--keep]
//
// Two things happen at once, each with real headless Sonnet sessions and fanout's plugin hooks (nothing about
// fanout in their tasks):
// 1. Same work in other words: "dark-mode" is asked for a dark mode toggle, "night-theme" for a night theme users
//    can switch on. The second is stopped at its first edit, before it changes anything.
// 2. A change another session needs to know: "receipt" builds a receipt on formatPrice(cents). Meanwhile
//    "prices" (scripted, no agent) commits formatPrice(cents, currency), which throws without a currency. receipt
//    is told, with the diff, and builds against the new version, so the merged code works.
// What fanout does is narrated from its own event log (claims.mjs, logEvent), as it happens. --record writes the
// narration as an animated SVG (no dependencies), for the README.
import { spawn, execFileSync, spawnSync } from "node:child_process";
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, existsSync, copyFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { createInterface } from "node:readline/promises";
import { readEvents, readState } from "./claims.mjs";

const SCRIPT = join(dirname(fileURLToPath(import.meta.url)), "fanout.mjs").replaceAll("\\", "/");
const bin = (name) => process.env[`FANOUT_${name.toUpperCase()}_BIN`] || name;
const g = (cwd, ...a) => execFileSync("git", a, { cwd, encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] });

const TASKS = {
  "dark-mode": "Add a dark mode toggle to the settings page: a checkbox in renderSettings (settings.js) that switches the page to dark colours (styles.css). Keep it small. Don't commit.",
  "night-theme": "Users have asked for a night theme they can turn on themselves, because the white page is too bright at night. Build it. Keep it small. Don't commit.",
  receipt: "Add receipt.js exporting renderReceipt(cart). A cart looks like sampleCart in cart.js. One line per item: the name, ' x', the quantity, two spaces, then the line price (quantity times priceCents) formatted with formatPrice from money.js. Last line: 'Total: ' and the total, formatted the same way. Check it with a quick node -e call. Don't commit.",
};
const MONEY_NEW = "export function formatPrice(cents, currency) {\n  const sign = { USD: '$', EUR: '€' }[currency];\n  if (!sign) throw new Error(`Unknown or missing currency: ${currency}`);\n  return sign + (cents / 100).toFixed(2);\n}\n";
const CHECK = `import { renderReceipt } from "./receipt.js";
const out = renderReceipt({ currency: "EUR", items: [{ name: "Tea", qty: 2, priceCents: 350 }] });
if (!/Tea x2 +€7\\.00/.test(out) || !/Total: €7\\.00/.test(out)) { console.error(out); process.exit(1); }`;

// The throwaway repo: a settings page and a small shop, one worktree per session.
export function demoRepo() {
  const dir = mkdtempSync(join(tmpdir(), "fanout-demo-")), repo = join(dir, "repo");
  mkdirSync(repo);
  g(repo, "init", "-q", "-b", "main"); g(repo, "config", "user.email", "demo@fanout"); g(repo, "config", "user.name", "fanout demo");
  const files = {
    "package.json": '{ "type": "module" }\n',
    "settings.js": "export function renderSettings() {\n  return '<h1>Settings</h1><label><input type=checkbox id=notify> Email me</label>';\n}\n",
    "styles.css": "body { background: white; color: black; }\n",
    "money.js": "export function formatPrice(cents) {\n  return '$' + (cents / 100).toFixed(2);\n}\n",
    "cart.js": "import { formatPrice } from './money.js';\n\nexport const sampleCart = { currency: 'USD', items: [{ name: 'Pen', qty: 3, priceCents: 120 }, { name: 'Pad', qty: 1, priceCents: 450 }] };\n\nexport const cartTotal = (cart) => cart.items.reduce((sum, i) => sum + i.qty * i.priceCents, 0);\nexport const renderTotal = (cart) => 'Total: ' + formatPrice(cartTotal(cart));\n",
  };
  for (const [f, body] of Object.entries(files)) writeFileSync(join(repo, f), body);
  g(repo, "add", "-A"); g(repo, "commit", "-qm", "a settings page and a small shop");
  const wt = {};
  for (const n of ["dark-mode", "night-theme", "receipt", "prices"]) { wt[n] = join(dir, n); g(repo, "worktree", "add", "-q", "-b", n, wt[n]); }
  // fanout's plugin hooks, as hooks/hooks.json has them, pointing at this checkout's script.
  const hook = (sub) => [{ type: "command", command: `node "${SCRIPT}" ${sub}` }];
  const settings = join(dir, "settings.json");
  writeFileSync(settings, JSON.stringify({ hooks: {
    PreToolUse: [{ matcher: "Write|Edit|NotebookEdit", hooks: hook("guard") }],
    PostToolUse: [{ matcher: "Read|Write|Edit|MultiEdit|NotebookEdit|Bash|PowerShell", hooks: hook("notice") }],
    SessionStart: [{ hooks: hook("session-start") }] } }));
  return { dir, repo, wt, settings };
}

// One narration line per event fanout logged.
export function describe(e) {
  const short = (s, n = 70) => (s && s.length > n ? s.slice(0, n - 1) + "…" : s ?? "");
  if (e.kind === "claim") return { tone: "ok", text: `${e.branch}: claimed${e.via === "edit" || e.via === "shell" ? " on its first edit" : ""}: "${short(e.task, 42)}"` };
  if (e.kind === "refused") return { tone: "stop", text: `${e.branch}: STOPPED at its first edit: same work as ${(e.as ?? []).join(", ")}` };
  if (e.kind === "notice") return { tone: "note", text: `${e.session}: told ${e.from} committed a change to ${e.files.join(", ")}, with the diff` };
  if (e.kind === "told") return { tone: "note", text: `${e.session}: told at start what the others are doing (${(e.others ?? []).join(", ")})` };
  if (e.kind === "locked") return { tone: "stop", text: `${e.session}: stopped changing ${e.file}, claimed by ${e.owner}` };
  return null;
}

// Lines appear at their real times (sped up, gaps capped), then the whole thing loops.
export function svgRecording(lines, { width = Math.max(480, Math.ceil(Math.max(...lines.map((l) => l.text.length)) * 7.9) + 40), title = "fanout demo" } = {}) {
  const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  let t = 0.6, prev = null;
  const at = lines.map((l) => { if (prev !== null) t += Math.min(Math.max((l.t - prev) / 6, 0.35), 1.6); prev = l.t; return t; });
  const total = t + 5, lh = 20, height = 46 + lines.length * lh + 16;
  const colour = { ok: "#7ee787", stop: "#ff7b72", note: "#e3b341", head: "#c9d1d9", dim: "#8b949e", done: "#79c0ff" };
  const rows = lines.map((l, i) => {
    const p = ((at[i] / total) * 100).toFixed(2);
    return `<style>@keyframes l${i}{0%,${p}%{opacity:0}${(Math.min(+p + 0.5, 99)).toFixed(2)}%,97%{opacity:1}100%{opacity:0}}</style>`
      + `<text x="16" y="${46 + i * lh}" fill="${colour[l.tone] ?? colour.head}" style="animation:l${i} ${total.toFixed(1)}s linear infinite">${esc(l.text)}</text>`;
  });
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" font-size="13">
<title>${esc(title)}</title>
<rect width="${width}" height="${height}" rx="8" fill="#0d1117"/>
<circle cx="18" cy="16" r="5" fill="#ff5f56"/><circle cx="34" cy="16" r="5" fill="#ffbd2e"/><circle cx="50" cy="16" r="5" fill="#27c93f"/>
<text x="${width / 2}" y="20" fill="#8b949e" text-anchor="middle">${esc(title)}</text>
${rows.join("\n")}
</svg>
`;
}

function runClaude(cwd, task, settings) {
  return new Promise((done) => {
    const t0 = Date.now();
    const cmd = `${bin("claude")} -p --model sonnet --permission-mode acceptEdits --tools Read,Edit,Write,Glob,Grep,Bash --allowedTools "Read,Edit,Write,Glob,Grep,Bash(node:*),Bash(ls:*),Bash(cat:*),Bash(git:*)" --setting-sources project,local --settings "${settings.replaceAll("\\", "/")}" --strict-mcp-config --output-format json --max-budget-usd 0.5`;
    const p = spawn(cmd, { cwd, shell: true });
    let out = "";
    p.stdout.on("data", (d) => (out += d)); p.stderr.on("data", (d) => (out += d));
    p.stdin.end(task);
    p.on("close", () => { let j = {}; try { j = JSON.parse(out.slice(out.indexOf("{"))); } catch { /* not json */ } done({ seconds: Math.round((Date.now() - t0) / 1000), cost: j.total_cost_usd ?? 0, error: j.is_error ? String(j.result).slice(0, 160) : null, result: String(j.result ?? "") }); });
  });
}

// In the narration, a start note only where it tells a session the other half of scene 1 is taken.
const shown = (e) => e.kind !== "told" || (e.others ?? []).some((n) => n === "dark-mode" || n === "night-theme");

export async function demo(argv) {
  const flag = (f) => argv.includes(f), opt = (f) => { const i = argv.indexOf(f); return i >= 0 ? argv[i + 1] : null; };
  const record = opt("--record");
  console.log(`fanout demo: three real Claude Code sessions (Sonnet) in a throwaway repo, with fanout's hooks and nothing about
fanout in their tasks. About two minutes and $0.10 on your Claude account.
  1. dark-mode and night-theme get the same work in other words. Watch the second one get stopped.
  2. receipt builds on formatPrice() while another session commits a change to it. Watch receipt get told.`);
  if (!flag("--yes")) {
    if (!process.stdin.isTTY) { console.log("\nRun again with --yes to start."); return 0; }
    const rl = createInterface({ input: process.stdin, output: process.stdout });
    const ok = /^y/i.test(await rl.question("\nStart? [y/N] "));
    rl.close();
    if (!ok) return 0;
  }
  const { dir, repo, wt, settings } = demoRepo();
  const lines = [], t0 = Date.now();
  const say = (text, tone = "head") => { const t = (Date.now() - t0) / 1000; lines.push({ t, text: text ? `${String(Math.round(t)).padStart(3)}s  ${text}` : "", tone }); console.log(text ? `${String(Math.round(t)).padStart(3)}s  ${text}` : ""); };
  lines.push({ t: 0, text: "$ fanout demo", tone: "dim" });
  say("dark-mode: \"Add a dark mode toggle to the settings page\"", "dim");
  say("night-theme: \"Users want a night theme they can turn on themselves\"", "dim");
  say("receipt: \"Add renderReceipt(cart), prices via formatPrice from money.js\"", "dim");
  // Narrate fanout's own decisions as it logs them.
  let seen = 0;
  const poll = setInterval(() => { const ev = readEvents(join(repo, ".git")); for (const e of ev.slice(seen)) { const d = shown(e) && describe(e); if (d) say(d.text, d.tone); } seen = ev.length; }, 400);
  // The other side of scene 2: a session that claims its task, then commits the new formatPrice.
  spawnSync(process.execPath, [SCRIPT, "start", "prices need a currency"], { cwd: wt.prices, encoding: "utf8", env: { ...process.env, FANOUT_CLAIM_JUDGE: "off" } });
  const prices = new Promise((r) => setTimeout(() => {
    writeFileSync(join(wt.prices, "money.js"), MONEY_NEW);
    writeFileSync(join(wt.prices, "cart.js"), readFileSync(join(wt.prices, "cart.js"), "utf8").replace("formatPrice(cartTotal(cart))", "formatPrice(cartTotal(cart), cart.currency)"));
    g(wt.prices, "commit", "--no-verify", "-qam", "prices take a currency");
    say("prices: committed formatPrice(cents, currency): throws without a currency", "dim"); r();
  }, 20000));
  const runs = await Promise.all([
    runClaude(wt["dark-mode"], TASKS["dark-mode"], settings),
    // night-theme starts once dark-mode has claimed its task, so the story reads the same every time (two sessions
    // starting at the same moment are handled too: the newer claim yields).
    (async () => { for (let i = 0; i < 120 && !readState(repo).claims["dark-mode"]; i++) await new Promise((r) => setTimeout(r, 500)); return runClaude(wt["night-theme"], TASKS["night-theme"], settings); })(),
    runClaude(wt.receipt, TASKS.receipt, settings),
    prices,
  ]);
  await new Promise((r) => setTimeout(r, 600));
  clearInterval(poll);
  for (const e of readEvents(join(repo, ".git")).slice(seen)) { const d = shown(e) && describe(e); if (d) say(d.text, d.tone); }
  // The results, checked rather than taken from the agents' own reports.
  const changed = (n) => g(wt[n], "status", "--porcelain").trim().split("\n").filter(Boolean).length;
  const dm = changed("dark-mode"), nt = changed("night-theme"), oneStopped = (dm === 0) !== (nt === 0);
  // What the stopped session said, in its own words (first sentence).
  const stopped = nt === 0 ? ["night-theme", runs[1]] : dm === 0 ? ["dark-mode", runs[0]] : null;
  // Its first sentence, and the next when the first doesn't say why ("I haven't made any changes.").
  const sentences = stopped?.[1].result ? stopped[1].result.replace(/[*`]/g, "").replace(/\s+/g, " ").split(/(?<=[.!?])\s/) : [];
  const first = sentences[0]?.length < 40 && sentences[1] ? `${sentences[0]} ${sentences[1]}` : sentences[0] ?? "";
  if (first) say(`${stopped[0]} says: "${first.length > 96 ? first.slice(0, 96).replace(/\s+\S*$/, "") + "…" : first}"`, "dim");
  say("");
  say(`dark-mode changed ${dm} file(s); night-theme changed ${nt}${oneStopped ? ": done once" : ""}`, oneStopped ? "done" : "stop");
  g(repo, "merge", "-q", "--no-edit", "prices");
  if (existsSync(join(wt.receipt, "receipt.js"))) copyFileSync(join(wt.receipt, "receipt.js"), join(repo, "receipt.js"));
  writeFileSync(join(repo, "check.mjs"), CHECK);
  const works = spawnSync(process.execPath, ["check.mjs"], { cwd: repo, encoding: "utf8" }).status === 0;
  say(works ? "merged prices + receipt: the EUR receipt is right (built on the new formatPrice)" : "merged prices + receipt: the EUR receipt check fails", works ? "done" : "stop");
  const cost = runs.slice(0, 3).reduce((n, r) => n + (r.cost ?? 0), 0);
  say("$" + `${cost.toFixed(2)} for the three sessions, about $0.01 per same-work check`, "dim");
  for (const r of runs.slice(0, 3)) if (r.error) console.log(`(a session failed: ${r.error})`);
  if (record) { writeFileSync(record, svgRecording(lines)); console.log(`recording written to ${record}`); }
  if (flag("--keep")) console.log(`repo kept at ${repo}`);
  else try { rmSync(dir, { recursive: true, force: true, maxRetries: 5, retryDelay: 300 }); } catch { console.log(`couldn't remove ${dir} (a file still in use); delete it later`); }
  return works && oneStopped ? 0 : 1;
}
