// Live page audit for the Suede AI Skills MCP.
//
// Fetches one public URL plus its robots.txt, sitemap and llms.txt, then grades
// what is actually served: the raw HTML a crawler or answer engine receives.
// Dependency-free on purpose (the server ships with none), so the HTML reading
// is tag-level pattern matching, which is what crawlers that do not run
// JavaScript see anyway.

import dns from "node:dns/promises";
import net from "node:net";

export const AUDIT_USER_AGENT = "SuedeSkillsMCP/1.0 (+https://skills.suedeai.ai)";
const MAX_PAGE_BYTES = 2 * 1024 * 1024;
const MAX_SIDE_BYTES = 512 * 1024;
const MAX_REDIRECTS = 5;
const DEFAULT_TIMEOUT_MS = 12000;

// Answer-engine retrieval bots fetch a page to cite it in an answer. Blocking
// them removes the page from those answers. Training crawlers are a separate,
// legitimate policy choice, so they are reported but never penalized.
export const ANSWER_BOTS = ["OAI-SearchBot", "ChatGPT-User", "PerplexityBot", "Perplexity-User", "Claude-SearchBot", "Claude-User"];
export const TRAINING_BOTS = ["GPTBot", "ClaudeBot", "Google-Extended", "Applebot-Extended", "CCBot"];

const CTA_VERBS = [
  "get", "start", "book", "try", "buy", "shop", "order", "download", "install", "join", "sign up", "signup",
  "subscribe", "schedule", "call", "contact", "request", "claim", "grade", "audit", "see pricing", "view pricing",
  "pricing", "demo", "talk to", "learn more", "apply", "register", "create", "launch", "hire", "add to cart", "checkout"
];

const LANES = [
  { key: "findability", label: "Findability", weight: 35 },
  { key: "ai", label: "AI search readiness", weight: 30 },
  { key: "action", label: "Page action", weight: 20 },
  { key: "share", label: "Share preview", weight: 15 }
];

export function letterGrade(score) {
  if (score >= 90) return "A";
  if (score >= 80) return "B";
  if (score >= 70) return "C";
  if (score >= 60) return "D";
  return "F";
}

const GRADE_ORDER = ["A", "B", "C", "D", "F"];
function capGrade(grade, cap) {
  return GRADE_ORDER.indexOf(grade) < GRADE_ORDER.indexOf(cap) ? cap : grade;
}

// ---------------------------------------------------------------------------
// Network

function isPrivateAddress(address) {
  if (net.isIPv4(address)) {
    const [a, b] = address.split(".").map(Number);
    return (
      a === 0 || a === 10 || a === 127 || (a === 100 && b >= 64 && b <= 127) || (a === 169 && b === 254) ||
      (a === 172 && b >= 16 && b <= 31) || (a === 192 && b === 168) || (a === 198 && (b === 18 || b === 19)) || a >= 224
    );
  }
  const lower = address.toLowerCase();
  if (lower === "::1" || lower === "::") return true;
  if (lower.startsWith("::ffff:")) return isPrivateAddress(lower.slice(7));
  return lower.startsWith("fc") || lower.startsWith("fd") || lower.startsWith("fe80") || lower.startsWith("ff");
}

async function assertPublicHost(hostname, allowPrivate) {
  if (allowPrivate) return;
  const host = hostname.replace(/^\[|\]$/g, "");
  if (host === "localhost" || host.endsWith(".localhost") || host.endsWith(".local") || host.endsWith(".internal")) {
    throw auditError(`Refusing to audit a local host: ${hostname}`);
  }
  const addresses = net.isIP(host) ? [{ address: host }] : await dns.lookup(host, { all: true }).catch(() => {
    throw auditError(`Could not resolve ${hostname}`);
  });
  if (addresses.some(({ address }) => isPrivateAddress(address))) {
    throw auditError(`Refusing to audit ${hostname}: it resolves to a private or reserved address`);
  }
}

function auditError(message) {
  const error = new Error(message);
  error.auditFailure = true;
  return error;
}

async function readCapped(response, maxBytes) {
  if (!response.body) return { text: "", truncated: false };
  const reader = response.body.getReader();
  const chunks = [];
  let size = 0;
  let truncated = false;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    size += value.byteLength;
    if (size > maxBytes) {
      chunks.push(value.subarray(0, value.byteLength - (size - maxBytes)));
      truncated = true;
      await reader.cancel().catch(() => {});
      break;
    }
    chunks.push(value);
  }
  return { text: Buffer.concat(chunks).toString("utf8"), truncated, bytes: Math.min(size, maxBytes) };
}

// Follow redirects by hand so every hop is checked against the private-host
// guard, and so the redirect chain can be reported.
export async function fetchChecked(startUrl, { allowPrivate = false, timeoutMs = DEFAULT_TIMEOUT_MS, maxBytes = MAX_PAGE_BYTES } = {}) {
  const chain = [];
  let current = new URL(startUrl);
  const started = Date.now();
  for (let hop = 0; hop <= MAX_REDIRECTS; hop += 1) {
    if (!["http:", "https:"].includes(current.protocol)) throw auditError(`Unsupported URL scheme: ${current.protocol}`);
    await assertPublicHost(current.hostname, allowPrivate);
    const remaining = Math.max(1000, timeoutMs - (Date.now() - started));
    let response;
    try {
      response = await fetch(current, {
        redirect: "manual",
        headers: { "user-agent": AUDIT_USER_AGENT, accept: "text/html,application/xhtml+xml,text/plain;q=0.9,*/*;q=0.5" },
        signal: AbortSignal.timeout(remaining)
      });
    } catch (error) {
      const reason = error?.name === "TimeoutError" ? `timed out after ${timeoutMs} ms` : error?.cause?.code || error?.message || "network error";
      throw auditError(`Could not fetch ${current.href}: ${reason}`);
    }
    if (response.status >= 300 && response.status < 400 && response.headers.get("location")) {
      chain.push({ url: current.href, status: response.status });
      await response.body?.cancel().catch(() => {});
      current = new URL(response.headers.get("location"), current);
      continue;
    }
    const body = await readCapped(response, maxBytes);
    return {
      url: current.href,
      status: response.status,
      headers: response.headers,
      contentType: response.headers.get("content-type") || "",
      ...body,
      redirects: chain,
      elapsedMs: Date.now() - started
    };
  }
  throw auditError(`Too many redirects (more than ${MAX_REDIRECTS}) starting at ${startUrl}`);
}

// ---------------------------------------------------------------------------
// HTML reading

const ENTITIES = { amp: "&", lt: "<", gt: ">", quot: '"', apos: "'", nbsp: " ", "#39": "'", mdash: "—", ndash: "–", hellip: "…", rsquo: "’", lsquo: "‘", rdquo: "”", ldquo: "“" };
export function decodeEntities(value) {
  return String(value)
    .replace(/&#x([0-9a-f]+);/gi, (_, hex) => safeCodePoint(parseInt(hex, 16)))
    .replace(/&#(\d+);/g, (_, dec) => safeCodePoint(Number(dec)))
    .replace(/&([a-z0-9#]+);/gi, (match, name) => ENTITIES[name.toLowerCase()] ?? match);
}
function safeCodePoint(code) {
  try {
    return String.fromCodePoint(code);
  } catch {
    return "";
  }
}

function attributes(tag) {
  const attrs = {};
  const pattern = /([a-zA-Z_:][-a-zA-Z0-9_:.]*)\s*(?:=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'=<>`]+)))?/g;
  const inner = tag.replace(/^<\s*[a-zA-Z0-9-]+/, "").replace(/\/?>$/, "");
  let match;
  while ((match = pattern.exec(inner))) {
    attrs[match[1].toLowerCase()] = decodeEntities(match[2] ?? match[3] ?? match[4] ?? "");
  }
  return attrs;
}

function stripTags(html) {
  return decodeEntities(html.replace(/<[^>]+>/g, " ")).replace(/\s+/g, " ").trim();
}

export function readHtml(html, baseUrl) {
  const withoutComments = html.replace(/<!--[\s\S]*?-->/g, "");
  const head = (withoutComments.match(/<head\b[^>]*>([\s\S]*?)<\/head>/i) || [null, withoutComments])[1];
  const metas = [...withoutComments.matchAll(/<meta\b[^>]*>/gi)].map((m) => attributes(m[0]));
  const links = [...withoutComments.matchAll(/<link\b[^>]*>/gi)].map((m) => attributes(m[0]));
  const meta = (key) => {
    const wanted = key.toLowerCase();
    const found = metas.find((attrs) => (attrs.name || attrs.property || "").toLowerCase() === wanted);
    return found ? found.content ?? "" : null;
  };
  const titleMatch = head.match(/<title\b[^>]*>([\s\S]*?)<\/title>/i) || withoutComments.match(/<title\b[^>]*>([\s\S]*?)<\/title>/i);
  const htmlTag = withoutComments.match(/<html\b[^>]*>/i);

  const jsonLd = [];
  for (const match of withoutComments.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)) {
    const attrs = attributes(`<script ${match[1]}>`);
    if ((attrs.type || "").toLowerCase().trim() !== "application/ld+json") continue;
    try {
      jsonLd.push({ ok: true, value: JSON.parse(match[2].trim()) });
    } catch (error) {
      jsonLd.push({ ok: false, error: error.message });
    }
  }
  const schemaTypes = new Set();
  const collectTypes = (node) => {
    if (Array.isArray(node)) return node.forEach(collectTypes);
    if (!node || typeof node !== "object") return;
    const type = node["@type"];
    if (typeof type === "string") schemaTypes.add(type);
    if (Array.isArray(type)) type.filter((t) => typeof t === "string").forEach((t) => schemaTypes.add(t));
    if (node["@graph"]) collectTypes(node["@graph"]);
    for (const [key, value] of Object.entries(node)) {
      if (key !== "@graph" && value && typeof value === "object") collectTypes(value);
    }
  };
  jsonLd.filter((block) => block.ok).forEach((block) => collectTypes(block.value));

  const body = withoutComments
    .replace(/<(script|style|noscript|template|svg|iframe)\b[\s\S]*?<\/\1>/gi, " ")
    .replace(/<head\b[\s\S]*?<\/head>/i, " ");
  const headings = [...body.matchAll(/<h([1-6])\b[^>]*>([\s\S]*?)<\/h\1>/gi)].map((m) => ({ level: Number(m[1]), text: stripTags(m[2]) }));
  const anchors = [...body.matchAll(/<a\b([^>]*)>([\s\S]*?)<\/a>/gi)].map((m) => {
    const attrs = attributes(`<a ${m[1]}>`);
    return { href: attrs.href || "", text: stripTags(m[2]) || attrs["aria-label"] || attrs.title || "" };
  });
  const buttons = [...body.matchAll(/<button\b([^>]*)>([\s\S]*?)<\/button>/gi)].map((m) => {
    const attrs = attributes(`<button ${m[1]}>`);
    return { text: stripTags(m[2]) || attrs["aria-label"] || "" };
  });
  const inputs = [...body.matchAll(/<input\b[^>]*>/gi)].map((m) => attributes(m[0]))
    .filter((attrs) => ["submit", "button"].includes((attrs.type || "").toLowerCase()))
    .map((attrs) => ({ text: attrs.value || attrs["aria-label"] || "" }));
  const images = [...body.matchAll(/<img\b[^>]*>/gi)].map((m) => attributes(m[0]));
  const text = stripTags(body);
  const words = text ? text.split(/\s+/).filter((word) => /[\p{L}\p{N}]/u.test(word)).length : 0;
  const canonicalLink = links.find((attrs) => (attrs.rel || "").toLowerCase().split(/\s+/).includes("canonical"));
  let canonical = null;
  if (canonicalLink?.href) {
    try {
      canonical = new URL(canonicalLink.href, baseUrl).href;
    } catch {
      canonical = canonicalLink.href;
    }
  }
  return {
    title: titleMatch ? stripTags(titleMatch[1]) : null,
    description: meta("description"),
    robotsMeta: [meta("robots"), meta("googlebot")].filter((value) => value !== null).join(", ") || null,
    viewport: meta("viewport"),
    lang: htmlTag ? attributes(htmlTag[0]).lang || null : null,
    canonical,
    canonicalRaw: canonicalLink?.href ?? null,
    og: { title: meta("og:title"), description: meta("og:description"), image: meta("og:image"), url: meta("og:url"), type: meta("og:type") },
    twitterCard: meta("twitter:card"),
    jsonLd,
    schemaTypes: [...schemaTypes],
    headings,
    anchors,
    actions: [...anchors, ...buttons, ...inputs],
    images,
    words,
    text
  };
}

// ---------------------------------------------------------------------------
// robots.txt

export function parseRobots(text) {
  const groups = [];
  const sitemaps = [];
  let current = null;
  let lastWasAgent = false;
  for (const rawLine of String(text).split(/\r?\n/)) {
    const line = rawLine.replace(/#.*/, "").trim();
    if (!line) continue;
    const index = line.indexOf(":");
    if (index === -1) continue;
    const field = line.slice(0, index).trim().toLowerCase();
    const value = line.slice(index + 1).trim();
    if (field === "sitemap") {
      if (value) sitemaps.push(value);
      continue;
    }
    if (field === "user-agent") {
      if (!current || !lastWasAgent) {
        current = { agents: [], rules: [] };
        groups.push(current);
      }
      current.agents.push(value.toLowerCase());
      lastWasAgent = true;
      continue;
    }
    lastWasAgent = false;
    if (!current) continue;
    if (field === "allow" || field === "disallow") current.rules.push({ allow: field === "allow", path: value });
  }
  return { groups, sitemaps };
}

function ruleMatches(rulePath, target) {
  if (!rulePath) return false;
  const anchored = rulePath.endsWith("$");
  const body = anchored ? rulePath.slice(0, -1) : rulePath;
  const pattern = body.split("*").map((part) => part.replace(/[.+?^${}()|[\]\\]/g, "\\$&")).join(".*");
  return new RegExp(`^${pattern}${anchored ? "$" : ""}`).test(target);
}

// Google's documented semantics: the most specific user-agent group wins, then
// the longest matching rule, with allow winning a tie. An empty Disallow allows.
export function robotsAllows(robots, agent, targetPath) {
  const name = agent.toLowerCase();
  let group = robots.groups.find((g) => g.agents.includes(name));
  if (!group) {
    const partial = robots.groups.filter((g) => g.agents.some((a) => a !== "*" && name.startsWith(a)));
    group = partial.sort((a, b) => Math.max(...b.agents.map((x) => x.length)) - Math.max(...a.agents.map((x) => x.length)))[0];
  }
  if (!group) group = robots.groups.find((g) => g.agents.includes("*"));
  if (!group) return true;
  let best = null;
  for (const rule of group.rules) {
    if (!rule.path) continue;
    if (!ruleMatches(rule.path, targetPath)) continue;
    const length = rule.path.length;
    if (!best || length > best.length || (length === best.length && rule.allow)) best = { allow: rule.allow, length };
  }
  return best ? best.allow : true;
}

// ---------------------------------------------------------------------------
// Grading

function check(lane, id, label, status, detail, fix, weight = 1) {
  return { lane, id, label, status, detail, fix: status === "pass" ? null : fix || null, weight };
}

function textHasAction(text) {
  const lower = text.toLowerCase().trim();
  if (!lower || lower.length > 60) return false;
  return CTA_VERBS.some((verb) => lower === verb || lower.startsWith(`${verb} `) || lower.includes(` ${verb} `) || lower.endsWith(` ${verb}`));
}

function words(value) {
  return (String(value).toLowerCase().match(/[a-z0-9]+/g) || []).filter((word) => word.length > 2);
}

export function gradePage({ requestedUrl, page, robotsText, robotsStatus, sitemap, llms, primaryAction }) {
  const finalUrl = new URL(page.url);
  const html = /html|xml/i.test(page.contentType) || /<html|<head|<body/i.test(page.text) ? page.text : "";
  const doc = readHtml(html, page.url);
  const checks = [];

  // Findability
  const ok = page.status >= 200 && page.status < 300;
  checks.push(check("findability", "status", "Page responds 200", ok ? "pass" : "fail",
    `HTTP ${page.status}${page.redirects.length ? ` after ${page.redirects.length} redirect(s)` : ""}`,
    "Serve the page with a 200 status at its canonical URL.", 3));
  checks.push(check("findability", "https", "Served over HTTPS", finalUrl.protocol === "https:" ? "pass" : "fail",
    finalUrl.protocol, "Redirect HTTP to HTTPS and serve the page over HTTPS.", 1));
  if (page.redirects.length > 1) {
    checks.push(check("findability", "redirects", "Short redirect chain", "warn", `${page.redirects.length} hops before the page`,
      "Point links and the canonical at the final URL so crawlers reach it in one request.", 1));
  }
  const xRobots = page.headers.get("x-robots-tag") || "";
  const noindex = /noindex/i.test(`${doc.robotsMeta || ""} ${xRobots}`);
  checks.push(check("findability", "indexable", "Indexable (no noindex)", noindex ? "fail" : "pass",
    noindex ? `noindex found in ${doc.robotsMeta ? "meta robots" : "X-Robots-Tag header"}` : "no noindex directive",
    "Remove noindex from the robots meta tag or X-Robots-Tag header if this page should rank.", 3));
  const robots = robotsStatus === 200 ? parseRobots(robotsText) : { groups: [], sitemaps: [] };
  const crawlPath = `${finalUrl.pathname}${finalUrl.search}`;
  const googleAllowed = robotsAllows(robots, "Googlebot", crawlPath);
  checks.push(check("findability", "robots-google", "robots.txt lets Google crawl the page", googleAllowed ? "pass" : "fail",
    robotsStatus === 200 ? (googleAllowed ? "allowed" : `disallowed for ${crawlPath}`) : `robots.txt returned ${robotsStatus ?? "no response"} (treated as allow)`,
    `Remove the Disallow rule that covers ${crawlPath} for Googlebot.`, 3));
  const canonicalStatus = !doc.canonical ? "fail" : new URL(doc.canonical).host !== finalUrl.host ? "warn" : "pass";
  checks.push(check("findability", "canonical", "Canonical URL declared", canonicalStatus,
    doc.canonical ? doc.canonical : "no rel=canonical link",
    doc.canonical ? "Point the canonical at this host unless the copy really lives elsewhere." : `Add <link rel="canonical" href="${finalUrl.origin}${finalUrl.pathname}"> to the head.`, 2));
  const titleLength = doc.title ? doc.title.length : 0;
  checks.push(check("findability", "title", "Title tag", !doc.title ? "fail" : titleLength < 15 || titleLength > 65 ? "warn" : "pass",
    doc.title ? `"${doc.title}" (${titleLength} characters)` : "missing",
    doc.title ? "Write a 15 to 65 character title that leads with the page's main query and the brand." : "Add a <title> that names what the page offers and who it is for.", 2));
  const descLength = doc.description ? doc.description.length : 0;
  checks.push(check("findability", "description", "Meta description", !doc.description ? "fail" : descLength < 70 || descLength > 170 ? "warn" : "pass",
    doc.description ? `${descLength} characters` : "missing",
    doc.description ? "Rewrite the description to 70 to 170 characters: the outcome, the proof, the next step." : "Add a meta description that states the outcome and the next step.", 1));
  const sitemapFound = Boolean(sitemap?.found);
  checks.push(check("findability", "sitemap", "XML sitemap reachable", sitemapFound ? "pass" : "warn",
    sitemapFound ? sitemap.url : "no sitemap in robots.txt and none at /sitemap.xml",
    `Publish /sitemap.xml and list it in robots.txt with "Sitemap: ${finalUrl.origin}/sitemap.xml".`, 1));
  checks.push(check("findability", "lang", "Language declared", doc.lang ? "pass" : "warn", doc.lang || "no lang attribute on <html>",
    'Add lang="en" (or the page language) to the <html> tag.', 0.5));
  checks.push(check("findability", "viewport", "Mobile viewport", doc.viewport ? "pass" : "fail", doc.viewport || "no viewport meta tag",
    'Add <meta name="viewport" content="width=device-width, initial-scale=1">.', 1));

  // AI search readiness
  const blockedAnswer = ANSWER_BOTS.filter((bot) => !robotsAllows(robots, bot, crawlPath));
  const blockedTraining = TRAINING_BOTS.filter((bot) => !robotsAllows(robots, bot, crawlPath));
  checks.push(check("ai", "answer-bots", "Answer engines can fetch the page", blockedAnswer.length ? "fail" : "pass",
    blockedAnswer.length ? `blocked in robots.txt: ${blockedAnswer.join(", ")}` : `allowed: ${ANSWER_BOTS.join(", ")}`,
    `Allow ${blockedAnswer.join(", ")} in robots.txt so ChatGPT, Perplexity and Claude can cite the page.`, 3));
  const h1s = doc.headings.filter((h) => h.level === 1);
  checks.push(check("ai", "h1", "One clear H1", h1s.length === 1 ? "pass" : h1s.length === 0 ? "fail" : "warn",
    h1s.length ? `${h1s.length} H1: "${h1s[0].text.slice(0, 90)}"` : "no H1 in the served HTML",
    h1s.length ? "Keep one H1 for the page's main promise and demote the others to H2." : "Add one H1 that states what the page offers.", 2));
  const wordCount = doc.words;
  checks.push(check("ai", "text", "Readable text in the served HTML", wordCount >= 250 ? "pass" : wordCount >= 100 ? "warn" : "fail",
    `${wordCount} words before JavaScript runs`,
    "Render the main copy in the HTML response. Most AI crawlers do not run JavaScript, so client-only text is invisible to them.", 3));
  const badLd = doc.jsonLd.filter((block) => !block.ok).length;
  const ldStatus = !doc.jsonLd.length ? "fail" : badLd ? "fail" : "pass";
  checks.push(check("ai", "schema", "Valid JSON-LD structured data", ldStatus,
    !doc.jsonLd.length ? "no JSON-LD" : badLd ? `${badLd} of ${doc.jsonLd.length} JSON-LD block(s) do not parse` : `types: ${doc.schemaTypes.join(", ") || "none named"}`,
    !doc.jsonLd.length ? "Add JSON-LD for the page type (Organization, WebSite, Product, Service, Article or FAQPage) that matches the visible content." : "Fix the JSON syntax in the broken JSON-LD block.", 2));
  const h2s = doc.headings.filter((h) => h.level === 2).length;
  checks.push(check("ai", "structure", "Sectioned with H2 headings", h2s >= 2 ? "pass" : "warn", `${h2s} H2 heading(s)`,
    "Break the page into H2 sections that each answer one question a buyer asks.", 1));
  const questionHeadings = doc.headings.filter((h) => h.level >= 2 && /\?\s*$/.test(h.text)).length;
  const hasFaq = doc.schemaTypes.some((type) => /faq|qapage/i.test(type));
  checks.push(check("ai", "answers", "Answer-ready questions", questionHeadings || hasFaq ? "pass" : "warn",
    hasFaq ? "FAQ structured data present" : `${questionHeadings} question-style heading(s)`,
    "Add a short FAQ with the questions buyers type into ChatGPT or Google, each answered in two or three sentences.", 1));
  checks.push(check("ai", "llms", "llms.txt published", llms?.found ? "pass" : "warn",
    llms?.found ? `${finalUrl.origin}/llms.txt` : "no /llms.txt",
    "Publish /llms.txt: a plain-text summary of the site with links to its key pages.", 0.5));
  if (blockedTraining.length) {
    checks.push(check("ai", "training-bots", "Training crawler policy", "info",
      `training crawlers disallowed: ${blockedTraining.join(", ")} (a policy choice; answer engines are scored separately)`, null, 0));
  }
  const altMissing = doc.images.filter((img) => !("alt" in img)).length;
  if (doc.images.length) {
    checks.push(check("ai", "alt", "Images carry alt text", altMissing === 0 ? "pass" : altMissing / doc.images.length > 0.2 ? "warn" : "pass",
      `${altMissing} of ${doc.images.length} image(s) without an alt attribute`, "Describe each meaningful image in its alt attribute.", 0.5));
  }

  // Page action
  const ctas = doc.actions.filter((action) => textHasAction(action.text));
  const ctaLabels = [...new Set(ctas.map((action) => action.text.trim()))];
  checks.push(check("action", "cta", "Clear call to action", ctaLabels.length ? "pass" : "fail",
    ctaLabels.length ? `found: ${ctaLabels.slice(0, 6).map((label) => `"${label}"`).join(", ")}` : "no link or button reads as a next step",
    "Add one primary button that names the next step and its payoff, such as \"Get my free audit\".", 3));
  if (primaryAction) {
    const wanted = words(primaryAction);
    const present = doc.actions.some((action) => {
      const have = new Set(words(action.text));
      return wanted.length && wanted.filter((word) => have.has(word)).length >= Math.ceil(wanted.length / 2);
    });
    checks.push(check("action", "primary-action", "Primary action is on the page", present ? "pass" : "fail",
      present ? `a link or button matches "${primaryAction}"` : `no link or button matches "${primaryAction}"`,
      `Put "${primaryAction}" on a button in the first screen and repeat it at the end of the page.`, 2));
  }
  const contact = doc.anchors.some((a) => /^(mailto:|tel:)/i.test(a.href) || /contact|book|schedule|demo/i.test(`${a.href} ${a.text}`));
  checks.push(check("action", "contact", "Direct contact or booking path", contact ? "pass" : "warn",
    contact ? "contact, booking or demo link present" : "no contact, booking, mailto or tel link",
    "Add a contact or booking link so a ready buyer has a direct path.", 1));
  checks.push(check("action", "speed", "Fast HTML response", page.elapsedMs <= 1500 ? "pass" : page.elapsedMs <= 4000 ? "warn" : "fail",
    `${page.elapsedMs} ms to fetch the HTML from this machine`, "Cache the HTML at the edge and trim server work before the first byte.", 1));

  // Share preview
  checks.push(check("share", "og-title", "Open Graph title", doc.og.title ? "pass" : "fail", doc.og.title || "missing",
    `Add <meta property="og:title" content="${(doc.title || "Page title").replace(/"/g, "&quot;")}">.`, 1));
  checks.push(check("share", "og-description", "Open Graph description", doc.og.description ? "pass" : "fail", doc.og.description ? "present" : "missing",
    "Add og:description with the outcome the page delivers.", 1));
  let ogImageStatus = "fail";
  if (doc.og.image) {
    try {
      ogImageStatus = /^https?:$/.test(new URL(doc.og.image).protocol) ? "pass" : "warn";
    } catch {
      ogImageStatus = "warn";
    }
  }
  checks.push(check("share", "og-image", "Open Graph image", ogImageStatus, doc.og.image || "missing",
    doc.og.image ? "Use an absolute https URL for og:image." : "Add a 1200x630 og:image so shared links show a preview card.", 2));
  checks.push(check("share", "twitter-card", "X/Twitter card", doc.twitterCard ? "pass" : "warn", doc.twitterCard || "missing",
    'Add <meta name="twitter:card" content="summary_large_image">.', 0.5));

  // Scores
  const lanes = LANES.map((lane) => {
    const scored = checks.filter((c) => c.lane === lane.key && c.status !== "info" && c.weight > 0);
    const total = scored.reduce((sum, c) => sum + c.weight, 0);
    const earned = scored.reduce((sum, c) => sum + c.weight * (c.status === "pass" ? 1 : c.status === "warn" ? 0.5 : 0), 0);
    const score = total ? Math.round((earned / total) * 100) : 100;
    return { key: lane.key, label: lane.label, score, grade: letterGrade(score), weight: lane.weight };
  });
  const totalWeight = lanes.reduce((sum, lane) => sum + lane.weight, 0);
  const overallScore = Math.round(lanes.reduce((sum, lane) => sum + lane.score * lane.weight, 0) / totalWeight);
  let overallGrade = letterGrade(overallScore);
  const caps = [];
  if (!ok) {
    overallGrade = capGrade(overallGrade, "F");
    caps.push(`HTTP ${page.status} caps the grade at F`);
  } else if (noindex) {
    overallGrade = capGrade(overallGrade, "D");
    caps.push("noindex caps the grade at D");
  } else if (!googleAllowed) {
    overallGrade = capGrade(overallGrade, "D");
    caps.push("a robots.txt block on Googlebot caps the grade at D");
  }

  const severityRank = (c) => (c.status === "fail" ? 2 : 1) * c.weight;
  const topFixes = checks
    .filter((c) => (c.status === "fail" || c.status === "warn") && c.fix)
    .sort((a, b) => severityRank(b) - severityRank(a))
    .slice(0, 5)
    .map((c) => ({ id: c.id, lane: c.lane, label: c.label, status: c.status, fix: c.fix }));

  return {
    requestedUrl,
    finalUrl: page.url,
    status: page.status,
    fetchedAt: new Date().toISOString(),
    fetchMs: page.elapsedMs,
    htmlBytes: page.bytes ?? page.text.length,
    htmlTruncated: Boolean(page.truncated),
    overall: { grade: overallGrade, score: overallScore, caps },
    lanes: lanes.map(({ key, label, score, grade }) => ({ key, label, score, grade })),
    page: {
      title: doc.title,
      description: doc.description,
      canonical: doc.canonical,
      h1: h1s.map((h) => h.text).slice(0, 3),
      words: wordCount,
      schemaTypes: doc.schemaTypes,
      ctas: ctaLabels.slice(0, 10)
    },
    robots: {
      status: robotsStatus ?? null,
      sitemaps: robots.sitemaps.slice(0, 10),
      blockedAnswerBots: blockedAnswer,
      blockedTrainingBots: blockedTraining
    },
    checks: checks.map(({ weight, ...rest }) => rest),
    topFixes,
    notChecked: [
      "Rendered layout and design on desktop and mobile (no browser runs here)",
      "Content that appears only after JavaScript runs",
      "Core Web Vitals and real-user speed",
      "Rankings, traffic, backlinks and AI citations"
    ]
  };
}

export function reportMarkdown(report) {
  const lines = [
    `# Suede Live Page Audit: ${report.finalUrl}`,
    "",
    `**Overall: ${report.overall.grade}** (${report.overall.score}/100)${report.overall.caps.length ? `. ${report.overall.caps.join("; ")}.` : ""}`,
    "",
    "| Lane | Grade | Score |",
    "|---|---|---|",
    ...report.lanes.map((lane) => `| ${lane.label} | ${lane.grade} | ${lane.score} |`),
    ""
  ];
  if (report.topFixes.length) {
    lines.push("## Top fixes", ...report.topFixes.map((fix, i) => `${i + 1}. **${fix.label}** (${fix.status}): ${fix.fix}`), "");
  }
  lines.push("## Every check");
  for (const lane of report.lanes) {
    lines.push(`### ${lane.label}`);
    for (const c of report.checks.filter((item) => item.lane === lane.key)) {
      const mark = c.status === "pass" ? "PASS" : c.status === "warn" ? "WARN" : c.status === "fail" ? "FAIL" : "INFO";
      lines.push(`- ${mark} ${c.label}: ${c.detail}`);
    }
  }
  lines.push(
    "",
    "## Checked from the served HTML",
    `Fetched ${report.finalUrl} (HTTP ${report.status}, ${report.htmlBytes} bytes, ${report.fetchMs} ms) at ${report.fetchedAt}, plus robots.txt, the sitemap and llms.txt.`,
    "",
    "## Outside this audit",
    ...report.notChecked.map((item) => `- ${item}`),
    "",
    "For the rendered, design and conversion review, run $suede-visibility-grader. For a full technical SEO report, run $suede-seo-audit. For AI citation work, run $suede-ai-seo."
  );
  return lines.join("\n");
}

async function sideFetch(url, options) {
  try {
    return await fetchChecked(url, { ...options, maxBytes: MAX_SIDE_BYTES });
  } catch {
    return null;
  }
}

export async function auditUrl(rawUrl, { primaryAction, allowPrivate = false, timeoutMs = DEFAULT_TIMEOUT_MS } = {}) {
  let start;
  try {
    start = new URL(/^[a-z][a-z0-9+.-]*:\/\//i.test(rawUrl) ? rawUrl : `https://${rawUrl}`);
  } catch {
    throw auditError(`Not a valid URL: ${rawUrl}`);
  }
  if (!["http:", "https:"].includes(start.protocol)) throw auditError(`Only http and https URLs can be audited, got ${start.protocol}`);
  const options = { allowPrivate, timeoutMs };
  const page = await fetchChecked(start.href, options);
  const origin = new URL(page.url).origin;
  const [robotsResponse, llmsResponse] = await Promise.all([
    sideFetch(`${origin}/robots.txt`, options),
    sideFetch(`${origin}/llms.txt`, options)
  ]);
  const robotsText = robotsResponse?.status === 200 ? robotsResponse.text : "";
  const robotsStatus = robotsResponse ? robotsResponse.status : null;
  const declared = robotsStatus === 200 ? parseRobots(robotsText).sitemaps : [];
  let sitemap = { found: false };
  for (const candidate of [...declared.slice(0, 2), `${origin}/sitemap.xml`]) {
    let target;
    try {
      target = new URL(candidate, origin).href;
    } catch {
      continue;
    }
    const response = await sideFetch(target, options);
    if (response?.status === 200 && /<(urlset|sitemapindex)\b/i.test(response.text)) {
      sitemap = { found: true, url: response.url };
      break;
    }
  }
  const llmsText = llmsResponse?.status === 200 ? llmsResponse.text : "";
  const llms = { found: Boolean(llmsText.trim()) && !/^\s*<(!doctype|html)/i.test(llmsText) };
  return gradePage({ requestedUrl: rawUrl, page, robotsText, robotsStatus, sitemap, llms, primaryAction });
}
