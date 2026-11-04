// Source-only checks. This module never fetches alternates or image assets.
// URL identity deliberately retains origin, path spelling, slash and query.
import { markdownText } from "./offline-reports.mjs";
const LANGUAGES = new Set(`aa ab ae af ak am an ar as av ay az ba be bg bh bi bm bn bo br bs ca ce ch co cr cs cu cv cy da de dv dz ee el en eo es et eu fa ff fi fj fo fr fy ga gd gl gn gu gv ha he hi ho hr ht hu hy hz ia id ie ig ii ik io is it iu ja jv ka kg ki kj kk kl km kn ko kr ks ku kv kw ky la lb lg li ln lo lt lu lv mg mh mi mk ml mn mr ms mt my na nb nd ne ng nl nn no nr nv ny oc oj om or os pa pi pl ps pt qu rm rn ro ru rw sa sc sd se sg si sk sl sm sn so sq sr ss st su sv sw ta te tg th ti tk tl tn to tr ts tt tw ty ug uk ur uz ve vi vo wa wo xh yi yo za zh zu`.split(" "));
const REGIONS = new Set(`ad ae af ag ai al am ao aq ar as at au aw ax az ba bb bd be bf bg bh bi bj bl bm bn bo bq br bs bt bv bw by bz ca cc cd cf cg ch ci ck cl cm cn co cr cu cv cw cx cy cz de dj dk dm do dz ec ee eg eh er es et fi fj fk fm fo fr ga gb gd ge gf gg gh gi gl gm gn gp gq gr gs gt gu gw gy hk hm hn hr ht hu id ie il im in io iq ir is it je jm jo jp ke kg kh ki km kn kp kr kw ky kz la lb lc li lk lr ls lt lu lv ly ma mc md me mf mg mh mk ml mm mn mo mp mq mr ms mt mu mv mw mx my mz na nc ne nf ng ni nl no np nr nu nz om pa pe pf pg ph pk pl pm pn pr ps pt pw py qa re ro rs ru rw sa sb sc sd se sg sh si sj sk sl sm sn so sr ss st sv sx sy sz tc td tf tg th tj tk tl tm tn to tr tt tv tw tz ua ug um us uy uz va vc ve vg vi vn vu wf ws ye yt za zm zw`.split(" "));
const scriptNames = new Intl.DisplayNames(["en"], { type: "script", fallback: "none" });

function languageValid(value) {
  const lower = value.toLowerCase();
  if (lower === "x-default") return true;
  const match = lower.match(/^([a-z]{2})(?:-([a-z]{4}))?(?:-([a-z]{2}))?$/);
  if (!match || !LANGUAGES.has(match[1]) || (match[3] && !REGIONS.has(match[3]))) return false;
  if (!match[2]) return true;
  const script = match[2][0].toUpperCase() + match[2].slice(1);
  return scriptNames.of(script) !== undefined;
}

function decode(value) {
  return value.replace(/&(?:amp|quot|apos|lt|gt|nbsp);|&#(?:x[0-9a-f]+|\d+);/gi, (entity) => {
    const names = { amp: "&", quot: '"', apos: "'", lt: "<", gt: ">", nbsp: " " };
    if (entity[1] !== "#") return names[entity.slice(1, -1).toLowerCase()];
    const raw = entity.slice(2, -1);
    const n = /^x/i.test(raw) ? Number.parseInt(raw.slice(1), 16) : Number(raw);
    return n > 0 && n <= 0x10ffff && !(n >= 0xd800 && n <= 0xdfff) ? String.fromCodePoint(n) : "\ufffd";
  });
}

// Small non-rendering tokenizer: quote-aware tags, exact attribute names, and
// inert/raw-text blocks. It is not a browser DOM or an HTML conformance checker.
function* tags(html) {
  const source = String(html);
  const token = /<!--[\s\S]*?(?:-->|$)|<!doctype\b[^>]*>|<\/?[a-z][a-z0-9:-]*(?:[^'"<>]|"[^"]*"|'[^']*')*>/gi;
  let templateDepth = 0;
  let cursor = 0;
  let match;
  while ((match = token.exec(source))) {
    if (!templateDepth && match.index > cursor) yield { name: "#text", text: source.slice(cursor, match.index) };
    cursor = token.lastIndex;
    const text = match[0];
    if (text.startsWith("<!")) continue;
    const name = text.match(/^<\/?([a-z0-9:-]+)/i)[1].toLowerCase();
    const closing = text.startsWith("</");
    const attrs = Object.create(null);
    const rest = text.slice(text.match(/^<\/?[a-z0-9:-]+/i)[0].length).replace(/>$/, "");
    for (const a of rest.matchAll(/([^\s=/'"<>]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+)))?/g)) {
      const key = a[1].toLowerCase();
      if (!(key in attrs)) attrs[key] = decode(a[2] ?? a[3] ?? a[4] ?? "");
    }
    if (["script", "style", "textarea", "title", "xmp", "iframe", "noscript"].includes(name) && !closing) {
      const start = token.lastIndex;
      const end = new RegExp(`</${name}\\s*>`, "gi");
      end.lastIndex = start;
      const finish = end.exec(source);
      if (!templateDepth) yield { name, closing, attrs, rawText: source.slice(start, finish?.index ?? source.length) };
      if (!finish) return;
      token.lastIndex = end.lastIndex;
      cursor = end.lastIndex;
      continue;
    }
    if (name === "plaintext" && !closing) return;
    if (name === "template") { templateDepth = Math.max(0, templateDepth + (closing ? -1 : 1)); continue; }
    if (templateDepth) continue;
    yield { name, closing, attrs };
  }
  if (!templateDepth && cursor < source.length) yield { name: "#text", text: source.slice(cursor) };
}

function httpUrl(value, base) {
  try {
    const url = new URL(value, base);
    return ["https:", "http:"].includes(url.protocol) && !url.username && !url.password ? url.href : null;
  } catch { return null; }
}

function alternateUrl(value) {
  const url = /^https?:\/\//i.test(value) ? httpUrl(value) : null;
  return url && !new URL(url).hash ? url : null;
}

export function extractTechnical(html, url) {
  const elements = [...tags(html)];
  const head = [];
  // HTML permits omitted head start/end tags. Stop the implicit head at the
  // first body element; annotations explicitly placed in the body do not count.
  let inHead = true;
  for (const element of elements) {
    if (element.name === "#text" && !element.text.trim()) continue;
    if (element.name === "head") { inHead = !element.closing; continue; }
    if (!["html", "base", "basefont", "bgsound", "link", "meta", "title", "script", "style", "noscript"].includes(element.name)) inHead = false;
    if (inHead && !element.closing) head.push(element);
  }
  const base = head.find((e) => e.name === "base" && "href" in e.attrs);
  const baseUrl = base ? httpUrl(base.attrs.href, url) ?? url : url;
  const links = head.filter((e) => e.name === "link");
  const hasRel = (e, rel) => (e.attrs.rel ?? "").toLowerCase().split(/\s+/).includes(rel);
  const canonical = links.find((e) => hasRel(e, "canonical"));
  const robots = head.filter((e) => e.name === "meta" && ["robots", "googlebot", "googlebot-news", "bingbot"].includes((e.attrs.name ?? "").toLowerCase()))
    .map((e) => ({ agent: e.attrs.name.toLowerCase(), content: e.attrs.content ?? "" }));
  const cleanText = (value) => decode(value).replace(/\s+/g, " ").trim();
  const h1s = [];
  let heading = null;
  for (const e of elements) {
    if (e.name === "h1") {
      if (heading !== null) h1s.push(cleanText(heading));
      heading = e.closing ? null : "";
    } else if (heading !== null && e.name === "#text") heading += e.text;
    else if (heading !== null && e.name === "br") heading += " ";
  }
  if (heading !== null) h1s.push(cleanText(heading));
  const headings = [];
  let currentHeading = null;
  for (const e of elements) {
    if (/^h[1-6]$/.test(e.name)) {
      if (currentHeading !== null) headings.push(cleanText(currentHeading));
      currentHeading = e.closing ? null : "";
    } else if (currentHeading !== null && e.name === "#text") currentHeading += e.text;
    else if (currentHeading !== null && e.name === "br") currentHeading += " ";
  }
  if (currentHeading !== null) headings.push(cleanText(currentHeading));
  const jsonLd = elements.filter((e) => e.name === "script" && (e.attrs.type ?? "").trim().toLowerCase() === "application/ld+json").map((e) => {
    try { return { valid: true, value: JSON.parse(e.rawText) }; }
    catch (error) { return { valid: false, error: error.message }; }
  });
  return {
    baseUrl, headings,
    title: cleanText(head.find((e) => e.name === "title")?.rawText ?? ""),
    description: head.find((e) => e.name === "meta" && (e.attrs.name ?? "").toLowerCase() === "description")?.attrs.content ?? "",
    h1: h1s[0] ?? "",
    jsonLd,
    canonical: canonical?.attrs.href?.trim() ? httpUrl(canonical.attrs.href.trim(), baseUrl) : null,
    robots,
    social: head.filter((e) => e.name === "meta" && /^(og:|twitter:)/i.test(e.attrs.property ?? e.attrs.name ?? ""))
      .map((e) => ({ name: (e.attrs.property ?? e.attrs.name).toLowerCase(), content: e.attrs.content ?? "" })),
    noindex: robots.some((r) => /(?:^|[,;\s])(?:noindex|none)(?=$|[,;\s])/i.test(r.content)),
    hreflang: links.filter((e) => hasRel(e, "alternate") && "hreflang" in e.attrs).map((e) => ({
      language: e.attrs.hreflang.trim().toLowerCase(), href: (e.attrs.href ?? "").trim(),
      url: alternateUrl((e.attrs.href ?? "").trim()),
    })),
    images: elements.filter((e) => e.name === "img" && !e.closing).map(({ attrs: a }) => ({
      src: (a.src ?? "").trim(), url: a.src?.trim() ? httpUrl(a.src.trim(), baseUrl) : null,
      alt: a.alt ?? null, width: a.width ?? "", height: a.height ?? "",
      srcset: a.srcset ?? "", sizes: a.sizes ?? "",
      loading: (a.loading ?? "").trim().toLowerCase(),
      fetchpriority: (a.fetchpriority ?? "").trim().toLowerCase(),
    })),
  };
}

function issue(severity, code, message, remediation, evidence = {}) {
  return { severity, code, message, remediation, ...evidence };
}

export function checkHreflang(pages) {
  const inventory = new Map(pages.map((p) => [p.url, p]));
  return pages.map((page) => {
    const declarations = page.technical?.hreflang ?? [];
    const issues = [];
    const checked = new Set();
    const unmeasured = new Set();
    const row = { url: page.url, path: page.path, status: page.technical ? (declarations.length ? "checked" : "not-declared") : "unmeasured", declarations, checkedTargets: 0, unmeasuredTargets: 0, issues };
    if (!declarations.length) return row;
    const locales = new Map();
    const valid = declarations.filter((d) => d.url && languageValid(d.language));
    const self = valid.filter((d) => d.url === page.url).map((d) => d.language);
    for (const declaration of declarations) {
      const { language, href, url } = declaration;
      const evidence = { language, target: href };
      if (!languageValid(language)) issues.push(issue("error", "invalid-language", `Unsupported hreflang code: ${language || "(empty)"}.`, "Use an ISO 639-1 language, optional ISO 15924 script and ISO 3166-1 region, or x-default.", evidence));
      if (!url) issues.push(issue("error", "alternate-url", `Alternate URL must be absolute HTTP(S), without credentials or a fragment: ${href || "(empty)"}.`, "Replace the href with the full canonical URL of the localized page.", evidence));
      if (locales.has(language)) issues.push(issue("error", locales.get(language) === href ? "duplicate-language" : "conflicting-language", `More than one declaration for ${language || "(empty)"}.`, "Keep one destination per language code; remove duplicates and resolve conflicting destinations.", evidence));
      else locales.set(language, href);
    }
    if (!self.length) issues.push(issue("error", "missing-self", "The alternate set does not include this page's own URL.", "Add an alternate for this page using its locale and canonical URL.", { target: page.url }));
    if (!declarations.some((d) => d.language === "x-default" && d.url)) issues.push(issue("info", "fallback-advice", "No x-default fallback is declared.", "Consider a fallback for unmatched visitors when the language-selection experience needs one."));
    for (const { language, url } of valid) {
      if (checked.has(url) || unmeasured.has(url)) continue;
      const target = inventory.get(url);
      const evidence = { language, target: url };
      if (!target?.technical) {
        unmeasured.add(url);
        issues.push(issue("info", "target-unmeasured", "Alternate was not in the inspected HTML inventory; availability and return links are unmeasured.", "Include this URL in a later source inventory and verify its response and return links.", evidence));
        continue;
      }
      checked.add(url);
      if (target.technical.noindex) issues.push(issue("error", "target-noindex", "Alternate has an HTML robots indexing restriction.", "Review the target's robots directives and include an indexable localized destination.", evidence));
      if (target.technical.canonical && target.technical.canonical !== url) issues.push(issue("error", "target-canonical", `Alternate declares a different canonical: ${target.technical.canonical}.`, "Align the alternate destination with the intended canonical localized page.", evidence));
      if (url !== page.url && !target.technical.hreflang.some((d) => d.url === page.url && languageValid(d.language) && (!self.length || self.includes(d.language)))) {
        issues.push(issue("error", "missing-return", "The inspected alternate has no matching return annotation to this page.", "Add a reciprocal alternate on the target using this page's locale and canonical URL.", evidence));
      }
    }
    row.checkedTargets = checked.size;
    row.unmeasuredTargets = unmeasured.size;
    return row;
  });
}

export function checkImages(pages) {
  const positive = (v) => /^\d+$/.test(v) && Number(v) > 0 && Number.isFinite(Number(v));
  return pages.map((page) => {
    const images = page.technical?.images ?? [];
    const issues = [];
    for (const [index, image] of images.entries()) {
      const evidence = { image: index + 1, target: image.url ?? image.src };
      const add = (severity, code, message, remediation) => issues.push(issue(severity, code, message, remediation, evidence));
      if (!image.src || (!image.url && !/^data:image\//i.test(image.src))) add("error", "image-source", "Image has no supported src fallback.", "Provide an img src fallback, including when using picture, srcset or a lazy loader.");
      if (image.alt === null) add("error", "missing-alt", "Image has no alt attribute.", "Add an alt attribute describing an informative image, or use empty alt for a decorative image after review.");
      else if (!image.alt.trim()) add("info", "decorative-alt-review", "Empty alt marks the image as decorative.", "Check that the image adds no information or link purpose that needs a text alternative.");
      if (!positive(image.width) || !positive(image.height)) add("warn", "image-dimensions", "Positive width and height attributes are missing or invalid.", "Provide intrinsic dimensions or verify that CSS reserves the correct aspect ratio; inspect the rendered layout.");
      if (/(?:^|[\s,])\d+w(?:\s*,|\s*$)/i.test(image.srcset) && !image.sizes.trim()) add("warn", "responsive-sizes", "Width-based srcset has no sizes attribute.", "Set sizes to match the rendered image width at each layout breakpoint.");
      if (image.loading === "lazy" && image.fetchpriority === "high") add("warn", "priority-lazy", "Image combines lazy loading with high fetch priority.", "Check the rendered critical image: load it eagerly if needed immediately, or remove high priority for a deferred image.");
    }
    return { url: page.url, path: page.path, status: page.technical ? "checked" : "unmeasured", imageCount: images.length, images, issues };
  });
}

export function renderTechnicalMarkdown(hreflang = [], images = []) {
  const cell = markdownText;
  const lines = ["## 8. Hreflang", "", "HTML source annotations only. HTTP Link headers and sitemap alternates, live availability and indexing are unmeasured. Uncollected destinations are not classified as broken.", "", "| Page URL | Declarations | Targets inspected | Targets unmeasured | Status |", "|---|---:|---:|---:|---|"];
  for (const row of hreflang) lines.push(`| ${cell(row.url)} | ${row.declarations.length} | ${row.checkedTargets} | ${row.unmeasuredTargets} | ${row.status} |`);
  const findings = (rows, image = false) => {
    lines.push("", "| Page URL | Severity | Code | Target | Evidence | Next action |", "|---|---|---|---|---|---|");
    for (const row of rows) for (const i of row.issues) lines.push(`| ${cell(row.url)} | ${i.severity} | ${i.code} | ${cell(i.target)} | ${cell(image ? `Image ${i.image}: ${i.message}` : i.message)} | ${cell(i.remediation)} |`);
    if (!rows.some((r) => r.issues.length)) lines.push("| – | – | – | – | No source findings in the inspected set. | – |");
    lines.push("");
  };
  findings(hreflang);
  lines.push("## 9. Images", "", "HTML source inventory only. Image bytes, rendered dimensions, alt accuracy, LCP and Core Web Vitals are unmeasured. Dimension advice requires a CSS/layout check; empty alt requires a decorative-purpose review.", "", `Inspected ${images.reduce((sum, row) => sum + row.imageCount, 0)} img elements across ${images.filter((r) => r.status === "checked").length} pages.`);
  findings(images, true);
  return lines.join("\n");
}
