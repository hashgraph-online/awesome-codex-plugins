import { markdownText } from "./offline-reports.mjs";

const SCHEMA = "urn:suede:seo-metadata-snapshot:v1";
const POLICY = "clean-html-v1";
const arrays = ["headings", "robots", "hreflang", "images", "jsonLd", "social"];
const fields = ["title", "description", "h1", "canonical", "noindex", ...arrays];
const object = (v) => v !== null && typeof v === "object" && !Array.isArray(v);
const fail = (message) => { throw new Error(`Invalid metadata snapshot: ${message}`); };

function url(value, nullable = false) {
  if (value === null && nullable) return true;
  if (typeof value !== "string") return false;
  try {
    const parsed = new URL(value);
    return ["https:", "http:"].includes(parsed.protocol) && !parsed.username && !parsed.password && parsed.href === value;
  } catch { return false; }
}

function stable(value) {
  if (Array.isArray(value)) return value.map(stable);
  if (object(value)) return Object.fromEntries(Object.keys(value).sort().map((k) => [k, stable(value[k])]));
  if (value === null || ["string", "boolean"].includes(typeof value) || (typeof value === "number" && Number.isFinite(value))) return value;
  fail("non-JSON metadata value");
}
const ordered = (values) => values.map(stable).sort((a, b) => JSON.stringify(a).localeCompare(JSON.stringify(b)));

export function createMetadataSnapshot(pages, { origin, capturedAt = new Date().toISOString(), sourceKind = "supplied", complete = false } = {}) {
  const result = {
    schema: SCHEMA, version: 1, capturedAt,
    scope: { origin: new URL(origin).origin, sourceKind, routePolicy: POLICY },
    coverage: { complete, observedPages: pages.length,
      reason: sourceKind === "local-build" ? "Selected local HTML files; hidden directories, node_modules and 404/500 files excluded." : "Only supplied or successfully collected HTML; discovery, skipped requests and caps may omit pages." },
    pages: pages.map((p) => {
      if (!p.technical) fail(`source evidence missing for ${p.url}`);
      return { url: p.url, metadata: {
        title: p.title, description: p.description, h1: p.h1, headings: p.headings,
        canonical: p.technical.canonical, noindex: p.technical.noindex,
        robots: ordered(p.technical.robots), hreflang: ordered(p.technical.hreflang),
        images: ordered(p.technical.images), jsonLd: ordered(p.jsonLd), social: ordered(p.technical.social),
      } };
    }).sort((a, b) => a.url.localeCompare(b.url)),
  };
  validateMetadataSnapshot(result);
  return result;
}

export function validateMetadataSnapshot(snapshot) {
  if (!object(snapshot) || snapshot.schema !== SCHEMA || snapshot.version !== 1) fail("unsupported schema/version");
  if (typeof snapshot.capturedAt !== "string" || !/^\d{4}-\d\d-\d\dT.+(?:Z|[+-]\d\d:\d\d)$/.test(snapshot.capturedAt) || !Number.isFinite(Date.parse(snapshot.capturedAt))) fail("capturedAt must be an ISO timestamp");
  const calendarDate = snapshot.capturedAt.slice(0, 10);
  if (new Date(`${calendarDate}T00:00:00Z`).toISOString().slice(0, 10) !== calendarDate) fail("capturedAt has an impossible calendar date");
  const { scope, coverage, pages } = snapshot;
  if (!object(scope) || !url(`${scope.origin}/`) || new URL(scope.origin).origin !== scope.origin
      || !["local-build", "live-sitemap", "supplied"].includes(scope.sourceKind) || scope.routePolicy !== POLICY) fail("unsupported site scope");
  if (!object(coverage) || typeof coverage.complete !== "boolean" || typeof coverage.reason !== "string"
      || !Number.isSafeInteger(coverage.observedPages) || !Array.isArray(pages) || pages.length > 10000 || coverage.observedPages !== pages.length) fail("invalid coverage/page count");
  if (coverage.complete && scope.sourceKind !== "local-build") fail("complete coverage is supported only for a selected local build");
  const identities = new Set();
  for (const page of pages) {
    if (!object(page) || !url(page.url) || new URL(page.url).origin !== scope.origin || new URL(page.url).hash || identities.has(page.url)) fail("invalid, foreign or duplicate page URL");
    identities.add(page.url);
    const m = page.metadata;
    if (!object(m) || ["title", "description", "h1"].some((k) => typeof m[k] !== "string") || !url(m.canonical, true)
        || typeof m.noindex !== "boolean" || arrays.some((k) => !Array.isArray(m[k]))) fail(`missing or malformed metadata for ${page.url}`);
    if (m.headings.some((v) => typeof v !== "string")
        || m.robots.some((v) => !object(v) || typeof v.agent !== "string" || typeof v.content !== "string")
        || m.hreflang.some((v) => !object(v) || typeof v.language !== "string" || typeof v.href !== "string" || !url(v.url, true))
        || m.social.some((v) => !object(v) || typeof v.name !== "string" || typeof v.content !== "string")
        || m.jsonLd.some((v) => !object(v) || typeof v.valid !== "boolean" || (v.valid ? !("value" in v) : typeof v.error !== "string"))
        || m.images.some((v) => !object(v) || !url(v.url, true) || (v.alt !== null && typeof v.alt !== "string")
          || ["src", "width", "height", "srcset", "sizes", "loading", "fetchpriority"].some((k) => typeof v[k] !== "string"))) fail(`malformed source evidence for ${page.url}`);
    const noindex = m.robots.some((r) => /(?:^|[,;\s])(?:noindex|none)(?=$|[,;\s])/i.test(r.content));
    if (noindex !== m.noindex) fail(`inconsistent source noindex for ${page.url}`);
    stable(m);
  }
  return snapshot;
}

function canonicalMetadata(metadata) {
  const result = { ...metadata };
  for (const field of ["robots", "hreflang", "images", "jsonLd", "social"]) result[field] = ordered(result[field]);
  return stable(result);
}

function finding(field, before, after, origin) {
  let severity = "info";
  let reason = "Source metadata changed; review the intended change.";
  if (field === "noindex" && after) { severity = "error"; reason = "An HTML robots indexing restriction was introduced."; }
  if (field === "title" && !after.trim()) { severity = "error"; reason = "The page title disappeared."; }
  if (["description", "h1"].includes(field) && !after.trim()) { severity = "warn"; reason = `The ${field} disappeared.`; }
  if (field === "canonical") {
    severity = after && new URL(after).origin !== origin ? "error" : "warn";
    reason = after ? "The declared canonical changed; verify the destination and intended URL ownership." : "The declared canonical disappeared.";
  }
  if (field === "jsonLd") {
    if (after.filter((b) => !b.valid).length > before.filter((b) => !b.valid).length) { severity = "error"; reason = "Additional JSON-LD blocks no longer parse."; }
    else if (before.length && !after.length) { severity = "warn"; reason = "Structured data disappeared."; }
  }
  return { severity, reason, remediation: `Compare the ${field} source before and after; accept the intended change or restore the reviewed baseline, then capture again.` };
}

export function compareMetadataSnapshots(baseline, current) {
  validateMetadataSnapshot(baseline); validateMetadataSnapshot(current);
  if (baseline.scope.origin !== current.scope.origin) throw new Error("Cannot compare different site origins");
  if (Date.parse(current.capturedAt) < Date.parse(baseline.capturedAt)) throw new Error("Current snapshot predates the baseline");
  const before = new Map(baseline.pages.map((p) => [p.url, canonicalMetadata(p.metadata)]));
  const after = new Map(current.pages.map((p) => [p.url, canonicalMetadata(p.metadata)]));
  const completeBuilds = [baseline, current].every((s) => s.scope.sourceKind === "local-build" && s.coverage.complete);
  const missing = [...before.keys()].filter((u) => !after.has(u)).sort().map((u) => ({ url: u, status: completeBuilds ? "absent-from-build" : "not-observed" }));
  const added = [...after.keys()].filter((u) => !before.has(u)).sort();
  const changes = [];
  for (const [pageUrl, metadata] of before) {
    if (!after.has(pageUrl)) continue;
    for (const field of fields) {
      const a = metadata[field]; const b = after.get(pageUrl)[field];
      if (JSON.stringify(a) !== JSON.stringify(b)) changes.push({ url: pageUrl, field, before: a, after: b, ...finding(field, a, b, baseline.scope.origin) });
    }
  }
  return { schema: "urn:suede:seo-metadata-drift:v1", site: baseline.scope.origin,
    baseline: { capturedAt: baseline.capturedAt, scope: baseline.scope, coverage: baseline.coverage },
    current: { capturedAt: current.capturedAt, scope: current.scope, coverage: current.coverage },
    comparedPages: [...before.keys()].filter((u) => after.has(u)).length, added, missing, changes };
}

export function renderMetadataDrift(report) {
  const text = markdownText;
  const value = (v) => text(JSON.stringify(v).slice(0, 2000));
  const lines = [`# SEO metadata drift — ${text(report.site)}`, "", `Baseline ${text(report.baseline.capturedAt)}; current ${text(report.current.capturedAt)}.`, "",
    "HTML source comparison only. Response headers, HTTP status, indexing, rankings and field performance were not measured. Missing inventory URLs do not establish a live deletion or 404. JSON retains full values; Markdown values are capped at 2,000 characters.", "",
    `${report.comparedPages} URLs compared; ${report.changes.length} field changes; ${report.added.length} newly observed; ${report.missing.length} absent or unobserved.`, "",
    "| URL | Field | Severity | Before | After | Review | Next action |", "|---|---|---|---|---|---|---|"];
  for (const c of report.changes) lines.push(`| ${text(c.url)} | ${c.field} | ${c.severity} | ${value(c.before)} | ${value(c.after)} | ${text(c.reason)} | ${text(c.remediation)} |`);
  if (!report.changes.length) lines.push("| – | – | – | – | – | No source field changes. | – |");
  lines.push("", "## Inventory changes", "", "| URL | Observation |", "|---|---|");
  for (const u of report.added) lines.push(`| ${text(u)} | newly-observed |`);
  for (const row of report.missing) lines.push(`| ${text(row.url)} | ${row.status} |`);
  return `${lines.join("\n")}\n`;
}
