#!/usr/bin/env node
// Mechanical gate for a Superloopy research session: the claim ledger and the synthesis
// are checked against the Phase 3b rules instead of trusting that the rules were followed.
// Prose rules only bind when something fails closed on them, so this exits non-zero.
import { readdir, readFile, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { pathToFileURL } from "node:url";

const LEDGER_COLUMNS = [
  "id",
  "claim",
  "risk",
  "cost",
  "observations",
  "counter",
  "primary",
  "observed",
  "as-of",
  "depends-on",
  "status"
];
const STATUSES = new Set(["verified", "unresolved", "refuted", "deferred"]);
const RISKS = new Set(["high", "normal"]);
// Closed labels make “two independent surfaces” checkable instead of relabelling one observation.
export const SURFACES = new Set(["rendered", "api", "repo", "registry", "standard", "filing", "legal", "dataset", "survey", "press", "community", "runtime"]);
// System/authority surfaces give high-risk claims primary footing beyond commentary.
export const PRIMARY_SURFACES = new Set(["api", "repo", "registry", "standard", "filing", "legal", "dataset", "runtime"]);
const BLOCKED_COLUMNS = ["url", "tiers", "reason", "substitute", "status"];
const BLOCKED_STATUSES = new Set(["substituted", "gap", "open"]);
const TRUTH_COLUMNS = ["id", "expected", "source", "observed", "status", "claim"];
const TRUTH_STATUSES = new Set(["holds", "violated", "unknown"]);
const LADDER_TIERS = new Set(["api", "plain", "tls", "headless"]);
const TERMINAL_REASONS = new Set(["auth-required", "paywall", "removed", "legal"]);
const COUNTRY_SECOND_LEVEL = new Set(["ac", "co", "com", "edu", "gov", "net", "org"]);
const EMPTY_VALUES = new Set(["", "-", "none", "n/a", "na", "tbd", "unknown"]);
const REQUIRED_SYNTHESIS_SECTIONS = ["Executive answer", "Sources", "Verified claims", "Contradictions", "Gaps"];

const args = parseArgs(process.argv.slice(2));
if (process.argv[1] !== undefined && import.meta.url === pathToFileURL(process.argv[1]).href) {
  if (args.help || args.root === undefined) {
    process.stdout.write("Usage: validate-research-evidence.mjs --root <evidence-root> [--json] [--report <path>]\n");
    process.exit(args.help ? 0 : 2);
  }
  let report;
  try {
    report = await validate(args.root);
  } catch (error) {
    report = failedRun(args.root, error instanceof Error ? error.message : String(error));
  }
  if (args.report !== undefined) await writeFile(args.report, `${JSON.stringify(report, null, 2)}\n`);
  process.stdout.write(args.json ? `${JSON.stringify(report, null, 2)}\n` : `${formatReport(report)}\n`);
  process.exit(report.ok ? 0 : 1);
}

function failedRun(root, ...problems) {
  return { ok: false, root, problems, ledger: null, blocked: null, expectedTruths: null, synthesis: null };
}

export async function validate(root) {
  const problems = [];
  const ledgerText = await readOptional(join(root, "claim-ledger.md"));
  if (ledgerText === null) {
    return failedRun(root, "Missing claim-ledger.md: the synthesis has no allowlist to draw from.");
  }

  const ledger = parseLedger(ledgerText);
  problems.push(...ledger.problems);
  problems.push(...checkRows(ledger.rows));
  problems.push(...checkDependencies(ledger.rows));

  const rootFiles = await listRootFiles(root);
  const synthesisText = await readOptional(join(root, "SYNTHESIS.md"));
  const synthesis = synthesisText === null ? null : checkSynthesis(synthesisText, ledger.rows, rootFiles);
  if (synthesis === null) {
    problems.push("Missing SYNTHESIS.md: research is not complete without the cited deliverable.");
  } else {
    problems.push(...synthesis.problems);
  }

  // A blocked source is only allowed to leave the run once the ladder is exhausted and the
  // outcome is recorded: silently dropped sources are the coverage gap nobody sees.
  const blockedText = await readOptional(join(root, "blocked-sources.md"));
  const blocked = blockedText === null ? null : parseBlockedSources(blockedText);
  if (blocked !== null) {
    problems.push(...blocked.problems);
    problems.push(...checkBlockedSources(blocked.rows, synthesisText ?? ""));
  }

  const truthsText = await readOptional(join(root, "expected-truths.md"));
  const truths = truthsText === null ? null : parseExpectedTruths(truthsText);
  if (truths !== null) {
    problems.push(...truths.problems);
    problems.push(...checkExpectedTruths(truths.rows, ledger.rows, synthesisText ?? ""));
  }

  const indexText = await readOptional(join(root, "INDEX.md"));
  problems.push(...checkIndex(indexText, root, rootFiles, ledger.rows));

  return {
    ok: problems.length === 0,
    root,
    problems,
    ledger: tally(ledger.rows, ["verified", "unresolved", "refuted", "deferred"]),
    blocked: blocked === null ? null : tally(blocked.rows, ["substituted", "gap", "open"]),
    expectedTruths: truths === null ? null : tally(truths.rows, ["holds", "violated", "unknown"]),
    synthesis: synthesis === null ? null : { sources: synthesis.sources, citations: synthesis.citations }
  };
}

// One shape for every ledger summary: total rows plus a count per status.
function tally(rows, statuses) {
  const summary = { rows: rows.length };
  for (const status of statuses) summary[status] = rows.filter((row) => row.status === status).length;
  return summary;
}

async function listRootFiles(root) {
  try {
    return await readdir(root);
  } catch {
    return [];
  }
}

// One markdown-table reader for every ledger in the session: the header row names the columns,
// so a renamed or dropped column fails loudly instead of silently reading as a blank cell.
export function parseTable(text, options) {
  const problems = [];
  const rows = [];
  const tableLines = text
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.startsWith("|"));
  const headerIndex = tableLines.findIndex((line) => cells(line)[0]?.toLowerCase() === options.columns[0]);
  if (headerIndex === -1) {
    return { rows, problems: [`${options.label} has no table header starting with \`${options.columns[0]}\`.`] };
  }

  const header = cells(tableLines[headerIndex]).map((cell) => cell.toLowerCase());
  const missing = options.columns.filter((column) => !header.includes(column));
  if (missing.length > 0) problems.push(`${options.label} header missing columns: ${missing.join(", ")}.`);

  const seen = new Set();
  for (const line of tableLines.slice(headerIndex + 1)) {
    const values = cells(line);
    if (values.length === 0 || values.every((value) => /^:?-{1,}:?$/u.test(value))) continue;
    if (values.length !== header.length) {
      problems.push(`${options.label} row has ${values.length} cells, header has ${header.length}: ${values[0] ?? line}`);
      continue;
    }
    const row = {};
    header.forEach((column, index) => {
      row[column] = values[index];
    });
    for (const column of options.lowercase ?? []) row[column] = (row[column] ?? "").toLowerCase();
    if (options.uniqueFirstColumn === true) {
      const key = row[options.columns[0]];
      if (seen.has(key)) problems.push(`${options.label} duplicate ${options.columns[0]}: ${key}`);
      seen.add(key);
    }
    rows.push(row);
  }
  return { rows, problems };
}

export function parseBlockedSources(text) {
  return parseTable(text, { label: "blocked-sources.md", columns: BLOCKED_COLUMNS, lowercase: ["status"] });
}

export function parseExpectedTruths(text) {
  return parseTable(text, {
    label: "expected-truths.md",
    columns: TRUTH_COLUMNS,
    lowercase: ["status"],
    uniqueFirstColumn: true
  });
}

// An expected truth that reality violated has to land somewhere the reader can see: a ledger
// claim or a published gap. Otherwise the diff was found and then quietly dropped.
function checkExpectedTruths(rows, ledgerRows, synthesisText) {
  const problems = [];
  const gaps = section(synthesisText, "Gaps");
  const ledgerIds = new Set(ledgerRows.map((row) => row.id));
  for (const row of rows) {
    const id = isBlank(row.id) ? "<blank id>" : row.id;
    if (isBlank(row.id)) problems.push("expected-truths.md row has no id.");
    if (isBlank(row.expected)) problems.push(`${id}: expected truth text is empty.`);
    if (isBlank(row.source)) problems.push(`${id}: no intent source recorded, so the expectation has no authority.`);
    if (!TRUTH_STATUSES.has(row.status)) {
      problems.push(`${id}: status must be holds, violated, or unknown, found "${row.status}".`);
      continue;
    }
    if (row.status === "holds" && isBlank(row.observed)) {
      problems.push(`${id}: recorded as holding with no observed reality.`);
    }
    if (row.status === "unknown" && !gaps.includes(row.id)) {
      problems.push(`${id}: unmeasured expected truth that the synthesis Gaps section never names.`);
    }
    if (row.status !== "violated") continue;
    if (isBlank(row.observed)) problems.push(`${id}: recorded as violated with no observed reality.`);
    const claim = (row.claim ?? "").trim();
    if (claim.toLowerCase() === "gap") {
      if (!gaps.includes(row.id)) {
        problems.push(`${id}: violated and routed to a gap the synthesis Gaps section never names.`);
      }
      continue;
    }
    const linked = dependencyIds(claim).filter((value) => ledgerIds.has(value));
    if (linked.length === 0) {
      problems.push(`${id}: violated but claim "${claim || "none"}" is not a ledger id or \`gap\`.`);
    }
  }
  return problems;
}

// The index is the only file the orchestrator re-reads, so a stale index means the detail it
// points away from is unreachable in practice.
function checkIndex(text, root, files, ledgerRows) {
  const problems = [];
  if (text === null) {
    return ["Missing INDEX.md: the session has no summary layer to read back."];
  }
  if (text.trim() === "") problems.push("INDEX.md is empty.");
  for (const file of files.filter((file) => /^wave-.*\.md$/u.test(file))) {
    if (!text.includes(file)) problems.push(`INDEX.md never names ${file}, so its detail is unreachable.`);
  }
  for (const row of ledgerRows) {
    if (!new RegExp(`(^|[^A-Za-z0-9._-])${escapeId(row.id)}([^A-Za-z0-9._-]|$)`, "u").test(text)) {
      problems.push(`INDEX.md has no line for claim ${row.id}.`);
    }
  }
  return problems;
}

function checkBlockedSources(rows, synthesisText) {
  const problems = [];
  const gaps = section(synthesisText, "Gaps");
  for (const row of rows) {
    const url = isBlank(row.url) ? "<blank url>" : row.url;
    if (isBlank(row.url)) problems.push("blocked-sources.md row has no URL.");
    if (!BLOCKED_STATUSES.has(row.status)) {
      problems.push(`${url}: status must be substituted, gap, or open, found "${row.status}".`);
      continue;
    }
    if (row.status === "open") {
      problems.push(`${url}: still open — the ladder is unfinished, so coverage is unproven.`);
      continue;
    }

    const tiers = tokens(row.tiers).filter((tier) => LADDER_TIERS.has(tier));
    const unknownTiers = tokens(row.tiers).filter((tier) => !LADDER_TIERS.has(tier));
    if (unknownTiers.length > 0) {
      problems.push(`${url}: unknown ladder tier(s) ${unknownTiers.join(", ")}; use ${[...LADDER_TIERS].join(", ")}.`);
    }
    const terminal = isTerminalReason(row.reason);
    if (!terminal && tiers.length < LADDER_TIERS.size) {
      problems.push(
        `${url}: only ${tiers.length}/${LADDER_TIERS.size} ladder tiers tried and no terminal reason (${[...TERMINAL_REASONS].join(", ")}) — not exhausted.`
      );
    }
    if (isBlank(row.reason)) problems.push(`${url}: no terminal reason recorded.`);
    if (row.status === "substituted" && isBlank(row.substitute)) {
      problems.push(`${url}: marked substituted with no substitute source.`);
    }
    if (row.status === "gap" && !gaps.includes(row.url)) {
      problems.push(`${url}: recorded as a gap but the synthesis Gaps section never names it.`);
    }
  }
  return problems;
}

export function tokens(value) {
  if (isBlank(value)) return [];
  return value
    .toLowerCase()
    .split(/[\s,;·/]+/u)
    .map((token) => token.trim())
    .filter((token) => token !== "");
}

async function readOptional(path) {
  try {
    return await readFile(path, "utf8");
  } catch (error) {
    if (error instanceof Error && "code" in error && error.code === "ENOENT") return null;
    throw error;
  }
}

export function parseLedger(text) {
  const parsed = parseTable(text, {
    label: "claim-ledger.md",
    columns: LEDGER_COLUMNS,
    lowercase: ["status", "risk"],
    uniqueFirstColumn: true
  });
  if (parsed.rows.length === 0 && !parsed.problems.some((problem) => problem.includes("no table header"))) {
    parsed.problems.push("claim-ledger.md has a header but no claim rows.");
  }
  return parsed;
}

function checkRows(rows) {
  const problems = [];
  for (const row of rows) {
    const id = row.id === "" ? "<blank id>" : row.id;
    if (!/^[A-Za-z0-9][A-Za-z0-9._-]*$/u.test(row.id)) problems.push(`${id}: id must be a plain token.`);
    if (isBlank(row.claim)) problems.push(`${id}: claim text is empty.`);
    if (!RISKS.has(row.risk)) problems.push(`${id}: risk must be high or normal, found "${row.risk}".`);
    if (!STATUSES.has(row.status)) {
      problems.push(`${id}: status must be verified, unresolved, refuted, or deferred, found "${row.status}".`);
      continue;
    }
    if (isBlank(row.cost)) problems.push(`${id}: error cost is unpriced, so verify-or-defer was never decided.`);
    if (row.status !== "verified") continue;

    const surfaces = observationSurfaces(row.observations);
    if (surfaces.length < 2) {
      problems.push(
        `${id}: verified needs 2+ observations on distinct surfaces, found ${surfaces.length} (${row.observations}).`
      );
    }
    const unknown = surfaces.filter((surface) => !SURFACES.has(surface));
    if (unknown.length > 0) {
      problems.push(
        `${id}: unknown surface label(s) ${unknown.join(", ")}; use one of ${[...SURFACES].join(", ")}.`
      );
    }
    if (row.risk === "high" && observationDomains(row.observations).length < 2) {
      problems.push(`${id}: a high-risk verified claim needs observations from 2+ independent domains.`);
    }
    if (row.risk === "high" && !surfaces.some((surface) => PRIMARY_SURFACES.has(surface))) {
      problems.push(
        `${id}: a high-risk verified claim needs at least one primary surface (${[...PRIMARY_SURFACES].join(", ")}), found ${surfaces.join(", ") || "none"}.`
      );
    }
    if (isBlank(row.counter)) problems.push(`${id}: verified without a counter-search result.`);
    if (isBlank(row.primary)) problems.push(`${id}: verified without a primary source.`);
    if (!isIsoDate(row.observed)) problems.push(`${id}: observed must be an ISO date, found "${row.observed}".`);
    if (row.risk === "high" && !isIsoDate(row["as-of"])) {
      problems.push(`${id}: a high-risk verified claim needs an ISO as-of date, found "${row["as-of"]}".`);
    }
  }
  return problems;
}

// Two URLs on the same surface agree by construction, so the gate counts distinct surface
// labels rather than distinct links.
export function observationSurfaces(value) {
  if (isBlank(value)) return [];
  const labels = new Set();
  for (const entry of value.split(/[·|;]/u)) {
    const text = entry.trim();
    if (text === "") continue;
    // Split on the first colon that is not a URL scheme, so a bare link contributes no surface
    // label: two unlabelled URLs must not read as two independent surfaces.
    let separator = -1;
    for (let index = text.indexOf(":"); index !== -1; index = text.indexOf(":", index + 1)) {
      if (text.slice(index + 1, index + 3) === "//") continue;
      separator = index;
      break;
    }
    if (separator === -1) continue;
    const label = text.slice(0, separator).trim().toLowerCase();
    const target = text.slice(separator + 1).trim();
    if (label === "" || target === "" || label.includes("/")) continue;
    labels.add(label);
  }
  return [...labels];
}

function observationDomains(value) {
  const domains = new Set();
  for (const match of (value ?? "").matchAll(/https?:\/\/[^\s·|;]+/gu)) {
    let hostname;
    try { hostname = new URL(match[0]).hostname; } catch { continue; }
    const parts = hostname.replace(/^www\./u, "").split(".");
    const width = parts.at(-1)?.length === 2 && COUNTRY_SECOND_LEVEL.has(parts.at(-2)) ? 3 : 2;
    if (parts.length >= width) domains.add(parts.slice(-width).join("."));
  }
  return [...domains];
}

function checkDependencies(rows) {
  const problems = [];
  const byId = new Map(rows.map((row) => [row.id, row]));
  for (const row of rows) {
    for (const dependency of dependencyIds(row["depends-on"])) {
      const target = byId.get(dependency);
      if (target === undefined) {
        problems.push(`${row.id}: depends-on references unknown id ${dependency}.`);
        continue;
      }
      if (target.id === row.id) problems.push(`${row.id}: depends on itself.`);
      if (row.status === "verified" && (target.status === "refuted" || target.status === "unresolved")) {
        problems.push(`${row.id}: verified while dependency ${dependency} is ${target.status}.`);
      }
    }
  }
  problems.push(...findCycles(rows));
  return problems;
}

export function dependencyIds(value) {
  if (isBlank(value)) return [];
  return value
    .split(/[,·;]/u)
    .map((entry) => entry.trim())
    .filter((entry) => entry !== "");
}

function findCycles(rows) {
  const graph = new Map(rows.map((row) => [row.id, dependencyIds(row["depends-on"])]));
  const state = new Map();
  const problems = [];
  const walk = (id, path) => {
    if (state.get(id) === "done") return;
    if (state.get(id) === "open") {
      problems.push(`Dependency cycle: ${[...path, id].join(" -> ")}`);
      return;
    }
    state.set(id, "open");
    for (const next of graph.get(id) ?? []) {
      if (graph.has(next)) walk(next, [...path, id]);
    }
    state.set(id, "done");
  };
  for (const id of graph.keys()) walk(id, []);
  return problems;
}

function checkSynthesis(text, rows, rootFiles) {
  const problems = [];
  for (const section of REQUIRED_SYNTHESIS_SECTIONS) {
    if (!new RegExp(`^##\\s+${section}`, "mu").test(text)) problems.push(`SYNTHESIS.md missing "## ${section}" section.`);
  }

  const sources = new Set();
  for (const match of section(text, "Sources").matchAll(/^\s*[-*]\s+Source\s+(\d+):\s+\S/gimu)) {
    sources.add(Number(match[1]));
  }
  const citations = new Set();
  for (const match of text.matchAll(/\[Source\s+(\d+)\]/giu)) citations.add(Number(match[1]));
  const dangling = [...citations].filter((number) => !sources.has(number)).sort((a, b) => a - b);
  if (dangling.length > 0) {
    problems.push(`SYNTHESIS.md cites sources with no numbered entry: ${dangling.map((n) => `[Source ${n}]`).join(", ")}.`);
  }
  if (citations.size === 0) problems.push("SYNTHESIS.md carries no [Source N] citations.");

  // Only cleared rows may be asserted: an id in the deliverable that the ledger did not verify
  // means the gate was bypassed rather than passed.
  const verified = new Set(rows.filter((row) => row.status === "verified").map((row) => row.id));
  const byId = new Map(rows.map((row) => [row.id, row]));
  const verifiedSection = section(text, "Verified claims");
  for (const row of rows.filter((row) => row.status !== "verified")) {
    if (new RegExp(`(^|[^A-Za-z0-9._-])${escapeId(row.id)}([^A-Za-z0-9._-]|$)`, "u").test(verifiedSection)) {
      problems.push(`SYNTHESIS.md lists ${row.id} as verified but the ledger says ${row.status}.`);
    }
  }
  for (const line of verifiedSection.split("\n").filter((line) => /^\s*[-*]\s+/u.test(line))) {
    if (!/^\s*[-*]\s+[A-Za-z0-9][A-Za-z0-9._-]*\s*\|\s*[^|\n]+\|\s*[^|\n]+\s*$/u.test(line)) problems.push(`SYNTHESIS.md has an unstructured verified-claim row: ${line.trim()}`);
  }
  for (const match of verifiedSection.matchAll(/^\s*[-*]\s+([A-Za-z0-9][A-Za-z0-9._-]*)\s*\|\s*([^|\n]+)\|\s*([^|\n]+)\s*$/gmu)) {
    const [, id, rawVerdict, rawArtifact] = match;
    if (byId.has(id)) {
      if (!verified.has(id)) problems.push(`SYNTHESIS.md lists ${id} as verified but the ledger says ${byId.get(id).status}.`);
      continue;
    }
    const verdict = rawVerdict.trim().toLowerCase();
    const artifact = rawArtifact.trim();
    const isCodeClaim = ["confirmed", "refuted", "partial"].includes(verdict) && /^verify-[A-Za-z0-9._-]+\.md$/u.test(artifact);
    if (!isCodeClaim || !rootFiles.includes(artifact)) {
      problems.push(`SYNTHESIS.md verified claims reference ${id}, which is neither a ledger claim nor a present code-verification artifact.`);
    }
  }
  return { problems, sources: sources.size, citations: citations.size };
}

function section(text, heading) {
  const lines = text.split("\n");
  const start = lines.findIndex((line) => new RegExp(`^##\\s+${heading}`, "u").test(line));
  if (start === -1) return "";
  const rest = lines.slice(start + 1);
  const end = rest.findIndex((line) => /^##\s+/u.test(line));
  return (end === -1 ? rest : rest.slice(0, end)).join("\n");
}

function escapeId(id) {
  return id.replace(/[.*+?^${}()|[\]\\]/gu, "\\$&");
}

function isIsoDate(value) {
  if (!/^\d{4}-\d{2}-\d{2}$/u.test(value)) return false;
  const date = new Date(`${value}T00:00:00Z`);
  return !Number.isNaN(date.valueOf()) && date.toISOString().slice(0, 10) === value;
}

function isTerminalReason(value) {
  const reason = (value ?? "").trim().toLowerCase();
  if (TERMINAL_REASONS.has(reason)) return true;
  const separator = reason.indexOf(":");
  return separator > 0 && TERMINAL_REASONS.has(reason.slice(0, separator).trim()) && reason.slice(separator + 1).trim() !== "";
}

function cells(line) {
  return line
    .replace(/^\|/u, "")
    .replace(/\|$/u, "")
    .split("|")
    .map((cell) => cell.trim());
}

function isBlank(value) {
  return value === undefined || EMPTY_VALUES.has(value.trim().toLowerCase());
}

function formatReport(report) {
  const lines = [`Superloopy research evidence: ${report.ok ? "pass" : "fail"}`, `root: ${report.root}`];
  for (const [label, summary] of [
    ["ledger", report.ledger],
    ["blocked sources", report.blocked],
    ["expected truths", report.expectedTruths]
  ]) {
    if (summary === null || summary === undefined) continue;
    const detail = Object.entries(summary)
      .filter(([key]) => key !== "rows")
      .map(([key, value]) => `${key} ${value}`)
      .join(", ");
    lines.push(`${label}: ${summary.rows} rows (${detail})`);
  }
  if (report.synthesis !== null && report.synthesis !== undefined) {
    lines.push(`synthesis: ${report.synthesis.sources} numbered sources, ${report.synthesis.citations} cited`);
  }
  for (const problem of report.problems) lines.push(`- ${problem}`);
  return lines.join("\n");
}

function parseArgs(argv) {
  const args = { json: false, help: false };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === "--json") args.json = true;
    else if (token === "--help" || token === "-h") args.help = true;
    else if (token === "--root") args.root = argv[index += 1];
    else if (token === "--report") args.report = argv[index += 1];
    else if (args.root === undefined) args.root = token;
  }
  return args;
}
