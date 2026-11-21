import test from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { parsePage, runAudit, renderAudit } from "../lib/audit.mjs";

const en = "https://example.test/en";
const fr = "https://example.test/fr";
const alt = (language, href) => `<link rel="alternate" hreflang="${language}" href="${href}">`;
function page(url, head = "", body = "") {
  return parsePage(`<html><head><title>Useful page</title>${head}</head><body><main><h1>Useful page</h1><p>A distinct useful explanation.</p>${body}</main></body></html>`, url);
}
const international = (pages) => runAudit(pages).hreflang;
const codes = (result) => result.issues.map((issue) => issue.code);

test("healthy language cluster has checked return links and optional fallback advice", () => {
  const declarations = alt("EN", en) + alt("fr", fr);
  const rows = international([page(en, declarations), page(fr, declarations)]);
  assert.equal(rows[0].checkedTargets, 2);
  assert.equal(rows[0].unmeasuredTargets, 0);
  assert.deepEqual(codes(rows[0]), ["fallback-advice"]);
  assert.equal(rows[0].issues[0].severity, "info");
  const fallback = international([page(en, declarations + alt("x-default", en)), page(fr, declarations)]);
  assert.deepEqual(fallback[0].issues, []);
});

test("no HTML alternates is not an international SEO failure", () => {
  const row = international([page(en)])[0];
  assert.equal(row.status, "not-declared");
  assert.deepEqual(row.issues, []);
});

test("broken return links, canonical conflicts and scoped noindex are actionable", () => {
  const rows = international([
    page(en, alt("en", en) + alt("fr", fr)),
    page(fr, alt("fr", fr) + '<link rel="canonical" href="https://other.test/fr"><meta name="googlebot" content="noindex">'),
  ]);
  assert.ok(codes(rows[0]).includes("missing-return"));
  assert.ok(codes(rows[0]).includes("target-canonical"));
  assert.ok(codes(rows[0]).includes("target-noindex"));
  for (const issue of rows[0].issues.filter((i) => i.severity === "error")) {
    assert.equal(issue.target, fr);
    assert.ok(issue.remediation.length > 10);
  }
});

test("relative alternate URLs, conflicting locales and missing self-reference are detected", () => {
  const row = international([page(en, alt("fr", "/fr") + alt("FR", "https://example.test/autre"))])[0];
  assert.ok(codes(row).includes("alternate-url"));
  assert.ok(codes(row).includes("conflicting-language"));
  assert.ok(codes(row).includes("missing-self"));
});

test("language and region validation supports script variants and rejects reserved/unknown codes", () => {
  for (const language of ["en-GB", "zh-Hant", "zh-Hans-US", "de", "fr-ca"]) {
    assert.ok(!codes(international([page(en, alt(language, en))])[0]).includes("invalid-language"), language);
  }
  for (const language of ["en-UK", "en-EU", "zz", "en_US", "US", "es-419", "en-XX", ""]) {
    assert.ok(codes(international([page(en, alt(language, en))])[0]).includes("invalid-language"), language);
  }
});

test("uncollected alternates are unmeasured, with no invented HTTP or return-link verdict", () => {
  const row = international([page(en, alt("en", en) + alt("fr", fr))])[0];
  assert.equal(row.checkedTargets, 1);
  assert.equal(row.unmeasuredTargets, 1);
  assert.ok(codes(row).includes("target-unmeasured"));
  assert.ok(!codes(row).includes("missing-return"));
  assert.ok(!JSON.stringify(row).includes("404"));
});

test("cross-origin and query-specific targets retain their own identities", () => {
  const translated = "https://fr.example.test/en?edition=2";
  const declarations = alt("en", en) + alt("fr", translated);
  const rows = international([
    page(en, declarations), page(translated, declarations),
    page("https://fr.example.test/en?edition=1"),
  ]);
  assert.equal(rows[0].checkedTargets, 2);
  assert.ok(!codes(rows[0]).includes("missing-return"));
  const partial = international([page(en, declarations), page("https://fr.example.test/en?edition=1")]);
  assert.equal(partial[0].unmeasuredTargets, 1);
});

test("duplicate and fragment-bearing declarations cannot silently pass", () => {
  const row = international([page(en, alt("en", en) + alt("en", en) + alt("fr", `${fr}#section`))])[0];
  assert.ok(codes(row).includes("duplicate-language"));
  assert.ok(codes(row).includes("alternate-url"));
});

test("source extraction ignores decoys and handles attributes with quotes, entities and base URLs", () => {
  const source = `<html><head><base href="https://cdn.example.test/assets/">
    <!-- ${alt("fr", fr)} -->
    <script>const x = '${alt("de", fr)}<img src="fake">';</script>
    <template>${alt("it", fr)}<img src="fake"></template>
    <link data-rel="alternate" data-hreflang="en" data-href="${en}">
    ${alt("en", en)}
    </head><body><img data-src="fake" title="a > b" src='photo.jpg?a=1&amp;b=2' alt="A &quot;photo&quot;" width=640 height=480>
    <template><img src="fake"><template><img src="fake"></template></template>
    <script>"<img src='fake'>"</script>${alt("es", fr)}</body></html>`;
  const p = parsePage(source, en);
  assert.equal(p.technical.hreflang.length, 1);
  assert.equal(p.technical.images.length, 1);
  assert.equal(p.technical.images[0].url, "https://cdn.example.test/assets/photo.jpg?a=1&b=2");
  assert.equal(p.technical.images[0].alt, 'A "photo"');
});

test("raw-text comment openers cannot swallow later annotations or mixed-case image attributes", () => {
  const source = `<HTML><HEAD><SCRIPT>const comment = '<!--';</SCRIPT>${alt("en", en)}</HEAD><BODY><IMG SRC='/real.jpg' ALT='A > B' WIDTH=20 HEIGHT=30 /></BODY></HTML>`;
  const p = parsePage(source, en);
  assert.equal(p.technical.hreflang.length, 1);
  assert.equal(p.technical.images.length, 1);
  assert.equal(p.technical.images[0].url, "https://example.test/real.jpg");
  assert.equal(p.technical.images[0].alt, "A > B");
});

test("return annotation must use the source locale, and trailing slash remains distinct", () => {
  const rows = international([page(en, alt("en", en) + alt("fr", fr)), page(fr, alt("fr", fr) + alt("de", en))]);
  assert.ok(codes(rows[0]).includes("missing-return"));
  const partial = international([page(en, alt("en", en) + alt("fr", `${fr}/`)), page(fr)]);
  assert.equal(partial[0].unmeasuredTargets, 1);
});

test("unquoted image URL trailing slash is retained and optional head tags are supported", () => {
  const p = parsePage(`<!doctype html><title>Page</title><link rel=alternate hreflang=en href=${en}><body><img src=/x/ alt=View width=20 height=30><img src=/y/></body>`, en);
  assert.equal(p.technical.hreflang.length, 1);
  assert.equal(p.technical.images[0].url, "https://example.test/x/");
  assert.equal(p.technical.images[1].url, "https://example.test/y/");
});

test("image findings preserve image identity and suggest concrete fixes", () => {
  const row = runAudit([page(en, "", '<img src="/hero.jpg" loading="lazy" fetchpriority="high" srcset="/hero.jpg 640w">')]).images[0];
  assert.equal(row.imageCount, 1);
  assert.deepEqual(new Set(codes(row)), new Set(["missing-alt", "image-dimensions", "responsive-sizes", "priority-lazy"]));
  assert.ok(row.issues.every((i) => i.image === 1 && i.target === "https://example.test/hero.jpg" && i.remediation));
});

test("decorative alt is review advice, valid images need no mandatory lazy loading or modern format", () => {
  const body = '<img src="/icon.svg" alt="" width="20" height="20"><img src="/photo.jpg" alt="Our storefront" width="640" height="480" srcset="/photo.jpg 1x, /photo-2x.jpg 2x">';
  const row = runAudit([page(en, "", body)]).images[0];
  assert.deepEqual(codes(row), ["decorative-alt-review"]);
  assert.equal(row.issues[0].severity, "info");
});

test("missing src fallback and nonpositive dimensions are reported without fetching assets", () => {
  const row = runAudit([page(en, "", '<picture><source srcset="/x.webp"><img data-src="/x.jpg" alt="A view" width="0" height="auto"></picture>')]).images[0];
  assert.deepEqual(codes(row), ["image-source", "image-dimensions"]);
  assert.equal(row.issues[0].target, "");
});

test("Markdown includes source scope, coverage, remediation and escapes untrusted table cells", () => {
  const result = runAudit([page(en, alt("fr", "https://example.test/fr?x=a|b"), '<img src="/x|y.jpg">')]);
  const md = renderAudit(result, { site: "example.test", generatedAt: "2026-10-24" });
  assert.match(md, /## 8\. Hreflang/);
  assert.match(md, /## 9\. Images/);
  assert.match(md, /unmeasured/i);
  assert.match(md, /HTML source/);
  assert.match(md, /alt attribute/i);
  assert.ok(!md.includes("x=a|b"));
  assert.ok(!md.includes("x|y.jpg"));
});

test("untrusted URL text cannot render Markdown images, links or inline HTML in new report sections", () => {
  const result = runAudit([page(en, "", '<img src="https://a.test/![x](https://evil.test/a.png)?a=`b`&amp;c=&lt;img&gt;">')]);
  const md = renderAudit(result, { site: "example.test", generatedAt: "2026-10-24" }).split("## 8. Hreflang")[1];
  assert.ok(!md.includes("![x]("));
  assert.ok(!md.includes("`b`"));
  assert.ok(!md.includes("<img>"));
  assert.ok(md.includes("&#91;x&#93;"));
});
