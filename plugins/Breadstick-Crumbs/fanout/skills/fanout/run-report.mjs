import { git } from "./workspace.mjs";
import { tokenCount } from "./agent.mjs";

export function loadPrices(text) {
  const header = text.split(/^## /m)[0];
  const block = header.match(/^prices:[ \t]*([^\r\n]*)(?:\r?\n((?:[ \t]+[^\r\n]+(?:\r?\n|$))*))?/m);
  const plan = {};
  if (block?.[1]?.trim()) Object.assign(plan, JSON.parse(block[1]));
  for (const line of (block?.[2] ?? "").trimEnd().split(/\r?\n/).filter(Boolean)) {
    if (/^\s*#/.test(line)) continue;
    const entry = line.match(/^\s*([\w./:-]+)\s*:\s*\{([^}]*)\}\s*$/);
    if (!entry) throw new Error("prices: use model: {in: number, out: number, cached_in: number}");
    const [, model, rates] = entry;
    plan[model] = JSON.parse(`{${rates.replace(/\b(in|out|cached_in)\s*:/g, '"$1":')}}`);
  }
  const env = process.env.FANOUT_PRICES ? JSON.parse(process.env.FANOUT_PRICES) : {};
  const prices = { ...env, ...plan };
  for (const [model, rates] of Object.entries(prices)) {
    if (!rates || ![rates.in, rates.out, rates.cached_in ?? rates.in].every((x) => Number.isFinite(x) && x >= 0))
      throw new Error(`invalid prices for ${model}; rates must be nonnegative numbers per million tokens`);
  }
  return prices;
}

export function estimate(record, prices) {
  if (record.costUsd != null || !tokenCount(record)) return;
  const model = record.model ?? record.agent;
  const rate = Object.hasOwn(prices, model) ? prices[model] : null;
  if (!rate) return;
  record.costUsd = ((record.inTokens - record.cachedTokens) * rate.in + record.cachedTokens * (rate.cached_in ?? rate.in) + record.outTokens * rate.out) / 1_000_000;
  record.estimatedCost = true;
}

export function renderReport({ root, base, laneBase, sessions, agents, live, result, logs, checks, testResult }) {
  const lines = ["# Fanout run", "", `Base: ${base} (${laneBase})`, `Result: ${result}`, `Command logs: ${logs.folder}`];
  for (const s of sessions) {
    const lane = live.sessions[s.name];
    const records = agents.filter((a) => a.session === s.name);
    const stat = git(root, "diff", "--stat", laneBase, `refs/heads/fanout/${s.name}`, "--");
    const check = Object.hasOwn(checks, s.name) ? checks[s.name] : null;
    const sum = (key) => records.reduce((total, record) => total + record[key], 0);
    const known = records.filter((record) => record.costUsd != null);
    const cost = known.reduce((total, record) => total + record.costUsd, 0);
    const amount = known.length ? `$${cost.toFixed(6)}${known.some((record) => record.estimatedCost) ? " estimated" : ""}${known.length < records.length ? " + unknown" : ""}` : "unknown";
    lines.push("", `## ${s.name}`, "",
      `- State: ${lane?.state ?? "not started"}`,
      `- Session ID: ${lane?.sessionId ?? "unavailable"}`,
      `- Check: ${check ? `${check.ok ? "passed" : "failed"} (${check.logPath})` : s.check ? "not run" : "not configured"}`,
      `- Test: ${testResult ?? "not run"}`,
      `- Usage: ${sum("inTokens")} input (${sum("cachedTokens")} cached), ${sum("outTokens")} output, ${sum("seconds")}s, ${amount}`,
      "", stat.ok && stat.out.trim() ? `    ${stat.out.trimEnd().replaceAll("\n", "\n    ")}` : "No committed file changes.");
    for (const record of records.filter((a) => a.sessionId || a.summary || a.error))
      lines.push("", `${record.role} (${record.sessionId ?? record.agent})`, "", ...(record.error ? [record.error, ""] : []),
        ...(record.summary ? record.summary.trim().split(/\r?\n/).map((line) => `> ${line}`) : []));
  }
  return lines.join("\n") + "\n";
}
