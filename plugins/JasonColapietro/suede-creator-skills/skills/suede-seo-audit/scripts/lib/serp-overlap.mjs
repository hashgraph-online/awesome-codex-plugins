const normalizeKeyword = (value = "") => String(value).normalize("NFKC").trim().replace(/\s+/g, " ").toLowerCase();
import { markdownText } from "./offline-reports.mjs";

// Code-point order keeps greedy grouping independent of the machine locale.
const compareText = (a, b) => a < b ? -1 : a > b ? 1 : 0;

function resultUrl(value) {
  if (typeof value !== "string" || !value.trim()) throw new Error("Organic result requires a URL");
  if (value.length > 16384) throw new Error("Organic URL exceeds 16,384 characters; review the stored input");
  const url = new URL(value);
  if (!/^https?:$/.test(url.protocol) || url.username || url.password) throw new Error("Organic URL must be HTTP(S), without credentials");
  url.hash = "";
  return url.href;
}

// Same-depth document-URL overlap. This is a review artifact, not an automatic
// replacement for reviewed target paths or a content calendar.
export function clusterSerpOverlap(rows, { depth = 10, threshold = 0.3, context } = {}) {
  if (!Array.isArray(rows) || rows.length > 500) throw new Error("Supply at most 500 stored keyword rows; no implicit sampling");
  if (!Number.isSafeInteger(depth) || depth < 1 || depth > 100) throw new Error("SERP depth must be an integer from 1 through 100");
  if (!Number.isFinite(threshold) || threshold <= 0 || threshold > 1) throw new Error("Overlap threshold must be greater than zero and at most one");
  if (typeof context !== "string" || !context.trim() || context.length > 1000) throw new Error("Supply collection context (engine, locale, device, period or a fixture label)");
  const seen = new Set();
  const samples = []; const excluded = [];
  let sampleBytes = 0;
  for (const row of rows) {
    if (typeof row?.keyword !== "string" || !row.keyword.trim() || row.keyword.length > 500) throw new Error("Every stored row requires a keyword of at most 500 characters");
    const keyword = normalizeKeyword(row.keyword);
    if (seen.has(keyword)) throw new Error(`Duplicate keyword: ${keyword}`);
    seen.add(keyword);
    if (row.collectionContext !== undefined && row.collectionContext !== context) throw new Error(`Mixed collection context for ${keyword}`);
    if (!Array.isArray(row.organic)) { excluded.push({ keyword, reason: "No stored organic-result array." }); continue; }
    const ranks = new Map();
    for (const result of row.organic) {
      if (!Number.isSafeInteger(result?.rank) || result.rank < 1 || ranks.has(result.rank)) throw new Error(`Invalid or duplicate organic rank for ${keyword}`);
      ranks.set(result.rank, resultUrl(result.url));
    }
    const urls = Array.from({ length: depth }, (_, i) => ranks.get(i + 1));
    if (urls.some((u) => !u) || new Set(urls).size !== depth) {
      excluded.push({ keyword, reason: `Need ${depth} distinct document URLs at every organic rank 1–${depth}; the stored sample is short, gapped or duplicated.` });
      continue;
    }
    const sample = { keyword, urls, exportDepthComplete: typeof row.serpDepthComplete === "boolean" ? row.serpDepthComplete : null };
    sampleBytes += Buffer.byteLength(JSON.stringify(sample));
    if (sampleBytes > 5_000_000) throw new Error("Sample evidence budget exceeded; reduce keywords or top-K depth. No report was written.");
    samples.push(sample);
  }
  samples.sort((a, b) => compareText(a.keyword, b.keyword));
  excluded.sort((a, b) => compareText(a.keyword, b.keyword));
  const pairs = []; const scores = new Map();
  let pairBytes = 0;
  const pairKey = (left, right) => JSON.stringify([left, right].sort());
  for (let i = 0; i < samples.length; i++) for (let j = i + 1; j < samples.length; j++) {
    const left = samples[i]; const right = samples[j];
    const rightSet = new Set(right.urls);
    const sharedUrls = left.urls.filter((u) => rightSet.has(u)).sort();
    const overlap = sharedUrls.length / depth;
    scores.set(pairKey(left.keyword, right.keyword), overlap);
    if (overlap >= threshold) {
      const pair = { left: left.keyword, right: right.keyword, sharedCount: sharedUrls.length, overlap, sharedUrls };
      pairBytes += Buffer.byteLength(JSON.stringify(pair));
      if (pairBytes > 2_000_000) throw new Error("Pair evidence budget exceeded; reduce keywords or top-K depth. No report was written or silently sampled.");
      pairs.push(pair);
    }
  }
  const groups = [];
  for (const { keyword } of samples) {
    const group = groups.find((members) => members.every((member) => scores.get(pairKey(member, keyword)) >= threshold));
    if (group) group.push(keyword); else groups.push([keyword]);
  }
  const clusters = groups.map((keywords, index) => {
    let minimum = null;
    for (let i = 0; i < keywords.length; i++) for (let j = i + 1; j < keywords.length; j++) {
      const score = scores.get(pairKey(keywords[i], keywords[j]));
      minimum = minimum === null ? score : Math.min(minimum, score);
    }
    return { id: `serp-${String(index + 1).padStart(3, "0")}`, label: keywords[0], keywords, minimumPairOverlap: minimum };
  });
  return { schema: "urn:suede:serp-overlap:v1", collectionContext: context, contextVerified: false,
    method: "Deterministic greedy complete-link grouping over shared top-K document URLs; overlap = shared URLs / K.",
    depth, threshold, inputKeywords: rows.length, evidenceBudget: { sampleMaximumBytes: 5_000_000, pairMaximumBytes: 2_000_000, sampleBytes, pairBytes }, samples, excluded, pairs, clusters };
}

export function renderSerpOverlap(report) {
  const text = markdownText;
  const lines = ["# Stored SERP overlap review", "", `User-supplied collection context: ${text(report.collectionContext)}. This label is not verified provenance.`, "",
    "No requests or provider calls. This report compares supplied historical organic-result URLs. It does not establish current rankings, search demand or semantic intent. Confirm comparable engine, locale, device and collection period before using the grouping.", "",
    `${report.samples.length} complete top-${report.depth} samples; ${report.excluded.length} excluded; shared-URL threshold ${report.threshold}.`, "",
    `${text(report.method)} Every pair within a group must meet the threshold; overlapping pairs can remain in separate groups when a transitive chain fails that test. Existing calendars and target paths were not changed.`, "",
    "| Cluster | Keywords | Minimum pair overlap |", "|---|---|---|"];
  for (const c of report.clusters) lines.push(`| ${c.id} | ${text(c.keywords.join("; "))} | ${c.minimumPairOverlap ?? "single keyword"} |`);
  lines.push("", "## Pair evidence", "", "| Left query | Right query | Shared / K | Overlap | Shared document URLs |", "|---|---|---|---|---|");
  for (const p of report.pairs) lines.push(`| ${text(p.left)} | ${text(p.right)} | ${p.sharedCount} / ${report.depth} | ${p.overlap} | ${text(p.sharedUrls.join("; "))} |`);
  lines.push("", "## Excluded samples", "", "| Query | Reason |", "|---|---|");
  for (const e of report.excluded) lines.push(`| ${text(e.keyword)} | ${text(e.reason)} |`);
  return `${lines.join("\n")}\n`;
}
