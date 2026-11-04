import test from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, readFileSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { parsePage } from "../lib/audit.mjs";

const api = await import("../lib/metadata-drift.mjs").catch(() => ({}));
const origin = "https://example.test";
const date = "2026-10-24T08:00:00.000Z";
function page(route = "/a", head = "", title = "A useful page", body = "<h1>Useful</h1>") {
  return parsePage(`<html><head><title>${title}</title><meta name="description" content="A clear description">${head}</head><body>${body}</body></html>`, `${origin}${route}`);
}
function snapshot(pages, sourceKind = "local-build", complete = true) {
  assert.equal(typeof api.createMetadataSnapshot, "function", "metadata snapshot capture is absent");
  return api.createMetadataSnapshot(pages, { origin, capturedAt: date, sourceKind, complete });
}

test("metadata captures absolute canonical, scoped indexing, social fields and exact URL identities", () => {
  const p = page("/a?edition=2", '<link rel="canonical" href="https://other.test/a"><meta name="googlebot" content="none"><meta property="og:title" content="A social title">');
  const result = snapshot([p, page("/a/"), page("/a")]);
  assert.equal(result.pages.length, 3);
  const metadata = result.pages.find((r) => r.url.endsWith("edition=2")).metadata;
  assert.equal(metadata.canonical, "https://other.test/a");
  assert.equal(metadata.noindex, true);
  assert.deepEqual(metadata.robots, [{ agent: "googlebot", content: "none" }]);
  assert.deepEqual(metadata.social, [{ name: "og:title", content: "A social title" }]);
});

test("unchanged source and reordered annotations or JSON keys do not create drift", () => {
  const first = '<link rel="alternate" hreflang="en" href="https://example.test/a"><link rel="alternate" hreflang="fr" href="https://example.test/fr"><script type="application/ld+json">{"@type":"WebPage","name":"Useful"}</script>';
  const second = '<script type="application/ld+json">{"name":"Useful","@type":"WebPage"}</script><link rel="alternate" hreflang="fr" href="https://example.test/fr"><link rel="alternate" hreflang="en" href="https://example.test/a">';
  const report = api.compareMetadataSnapshots(snapshot([page("/a", first)]), snapshot([page("/a", second)]));
  assert.deepEqual(report.changes, []);
  assert.deepEqual(report.added, []);
  assert.deepEqual(report.missing, []);
});

test("title loss, introduced noindex and cross-origin canonical drift are reviewable regressions", () => {
  const before = snapshot([page("/a", '<link rel="canonical" href="https://example.test/a">')]);
  const after = snapshot([page("/a", '<link rel="canonical" href="https://other.test/a"><meta name="bingbot" content="noindex">', "")]);
  const result = api.compareMetadataSnapshots(before, after);
  for (const field of ["title", "noindex", "canonical"]) {
    const change = result.changes.find((r) => r.field === field);
    assert.equal(change.severity, "error", field);
    assert.ok(change.remediation.length > 10);
  }
  assert.equal(result.changes.find((r) => r.field === "canonical").after, "https://other.test/a");
});

test("invalid JSON-LD, removed descriptions and headings get field-specific findings", () => {
  const before = snapshot([page("/a", '<script type="application/ld+json">{"@type":"Product"}</script>')]);
  const p = page("/a", '<script type="application/ld+json">broken</script>', "A useful page", "<p>Body</p>");
  p.description = "";
  const result = api.compareMetadataSnapshots(before, snapshot([p]));
  assert.equal(result.changes.find((r) => r.field === "jsonLd").severity, "error");
  assert.equal(result.changes.find((r) => r.field === "description").severity, "warn");
  assert.equal(result.changes.find((r) => r.field === "h1").severity, "warn");
});

test("inert script/comment/template metadata cannot hide title loss or create schema drift", () => {
  const decoys = `<script>const example='<title>Fake</title><meta name="description" content="Fake"><h1>Fake</h1>';</script>
    <!-- <script type="application/ld+json">{"@type":"Product"}</script> -->
    <template><title>Template title</title><script type="application/ld+json">{"@type":"Product"}</script></template>`;
  const source = (title) => `<head>${decoys}${title}<meta name="description" content="Real description"><script type = 'application/ld+json'>{"@type":"WebPage"}</script></head><body><h1>Real <span>heading</span></h1></body>`;
  const beforePage = parsePage(source("<title>Real title</title>"), `${origin}/a`);
  assert.equal(beforePage.title, "Real title");
  assert.equal(beforePage.description, "Real description");
  assert.equal(beforePage.h1, "Real heading");
  assert.equal(beforePage.jsonLd.length, 1);
  assert.equal(beforePage.jsonLd[0].value["@type"], "WebPage");
  const afterPage = parsePage(source(""), `${origin}/a`);
  assert.equal(api.compareMetadataSnapshots(snapshot([beforePage]), snapshot([afterPage])).changes.find((r) => r.field === "title").severity, "error");
});

test("impossible calendar dates are rejected rather than normalized", () => {
  const value = snapshot([page()]); value.capturedAt = "2027-02-30T08:00:00Z";
  assert.throws(() => api.validateMetadataSnapshot(value), /timestamp|date/i);
});

test("complete build absence differs from incomplete live inventory omission", () => {
  const before = snapshot([page("/a"), page("/b")]);
  const after = snapshot([page("/a"), page("/c")]);
  assert.deepEqual(api.compareMetadataSnapshots(before, after).missing, [{ url: `${origin}/b`, status: "absent-from-build" }]);
  assert.deepEqual(api.compareMetadataSnapshots(before, after).added, [`${origin}/c`]);
  const live = snapshot([page("/a")], "live-sitemap", false);
  assert.deepEqual(api.compareMetadataSnapshots(before, live).missing, [{ url: `${origin}/b`, status: "not-observed" }]);
  assert.throws(() => snapshot([page()], "live-sitemap", true), /coverage|complete/i);
});

test("malformed, duplicate, foreign-origin and incompatible snapshots fail closed", () => {
  const good = snapshot([page()]);
  for (const mutate of [
    (s) => { s.version = 99; },
    (s) => { s.capturedAt = "yesterday"; },
    (s) => { s.pages.push(s.pages[0]); s.coverage.observedPages++; },
    (s) => { delete s.pages[0].metadata.title; },
    (s) => { s.pages[0].metadata.noindex = "false"; },
    (s) => { s.pages[0].url = "https://foreign.test/a"; },
    (s) => { s.coverage.observedPages = 99; },
  ]) {
    const bad = structuredClone(good); mutate(bad);
    assert.throws(() => api.compareMetadataSnapshots(good, bad));
  }
  const foreign = api.createMetadataSnapshot([parsePage("<title>Other</title>", "https://foreign.test/a")], { origin: "https://foreign.test", capturedAt: date, sourceKind: "local-build", complete: true });
  assert.throws(() => api.compareMetadataSnapshots(good, foreign), /origin|site/i);
});

test("drift Markdown makes malicious metadata inert and retains both values", () => {
  const before = snapshot([page()]);
  const after = snapshot([page("/a", "", "![x](https://evil.test/tracker)")]);
  const md = api.renderMetadataDrift(api.compareMetadataSnapshots(before, after));
  assert.ok(md.includes("A useful page"));
  assert.ok(!md.includes("![x]("));
  assert.match(md, /HTML source/);
});

test("removing a canonical destination is drift rather than an invented self-canonical", () => {
  const before = snapshot([page('/a', '<link rel="canonical" href="https://example.test/a">')]);
  for (const annotation of ['<link rel="canonical">', '<link rel="canonical" href="">', '<link rel="canonical" href="   ">']) {
    const after = snapshot([page('/a', annotation)]);
    assert.equal(after.pages[0].metadata.canonical, null);
    const change = api.compareMetadataSnapshots(before, after).changes.find(c => c.field === 'canonical');
    assert.equal(change.before, 'https://example.test/a');
    assert.equal(change.after, null);
    assert.equal(change.severity, 'warn');
  }
});
