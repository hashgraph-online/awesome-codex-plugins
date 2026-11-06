"use strict";

// The claims a site makes about itself, found by rules in the pages it shows
// (see PAGE_MODEL in facts.js): numbers with what they count, quotes with the
// person under them, the names in a row of customer logos, plans with their
// prices, integrations, security standards, and the ratings, FAQs and
// company details in its JSON-LD. Every claim keeps the page's own words and
// the page it came from. Nothing is reworded or added: a claim the rules
// cannot pin to a name, a label or a price is left out.

const isNode = (n) => n !== null && typeof n === "object";
const clip = (text, max) => (text.length > max ? `${text.slice(0, max - 1).trimEnd()}…` : text);

// ---- Reading a page's tree ----

// A page with the lookups the rules share: each element's parent and depth,
// and its text, worked out once.
function pageOf({ role, url, readAt, model }) {
  const parent = new Map();
  const depth = new Map();
  const all = [];
  const visit = (node, up, level) => {
    parent.set(node, up);
    depth.set(node, level);
    all.push(node);
    for (const kid of node.kids || []) if (isNode(kid)) visit(kid, node, level + 1);
  };
  if (model && model.tree) visit(model.tree, null, 0);
  return { role, url, readAt, model, parent, depth, all, texts: new Map() };
}

// An element's text as a reader gets it: blocks on lines of their own, an
// element marked aria-hidden left out, and one drawn as a picture of its
// words (a price that rolls its digits) read by its label.
function textOf(page, node) {
  if (typeof node === "string") return node;
  if (page.texts.has(node)) return page.texts.get(node);
  let out = "";
  if (node.hidden || node.tag === "img" || node.tag === "svg") out = "";
  else if (node.tag === "br") out = "\n";
  else if (node.role === "img" && node.label) out = node.label;
  else {
    for (const kid of node.kids || []) out += textOf(page, kid);
  }
  if (node.block) out = `\n${out}\n`;
  page.texts.set(node, out);
  return out;
}

// Its lines, each said once in a row: a heading drawn twice for an effect,
// or a price in a hidden label and again in rolling digits, is one line.
function linesOf(page, node) {
  const lines = [];
  for (const raw of textOf(page, node).split("\n")) {
    // A ticker draws its figure twice (one copy rolling out, one in), and
    // two blocks set side by side can run together ("Stripe.From").
    const line = tidy(raw.replace(/(\p{Ll}[.!?])(\p{Lu}\p{Ll})/gu, "$1 $2").replace(/^(item|slide) \d+ of \d+[:.]\s*/i, ""));
    if (line && line !== lines[lines.length - 1]) lines.push(line);
  }
  return lines;
}
const tidy = (text) => text.replace(/\s+/g, " ").replace(/(^|\s)(\S*\d\S*)(?:\s\2)+(?=\s|$)/g, "$1$2").trim();
const lineOf = (page, node) => tidy(linesOf(page, node).join(" "));

function* ancestors(page, node) {
  for (let up = page.parent.get(node); up; up = page.parent.get(up)) yield up;
}

// "main" unless the element sits in the page's menu bar ("nav") or footer.
function regionOf(page, node) {
  for (let n = node; n; n = page.parent.get(n)) if (n.region) return n.region;
  return "main";
}

const words = (cls) => String(cls || "").toLowerCase().split(/[\s_-]+/);

// A product mockup or an illustration draws made-up figures (a $5.46 order,
// a chart's axis), and an element marked aria-hidden is decoration or a
// copy. Neither is the site speaking.
const ART = new Set(["graphic", "graphics", "mockup", "mock", "illustration", "illo", "artwork", "demo"]);
function decorative(page, node) {
  for (let n = node; n; n = page.parent.get(n)) {
    if (n.hidden) return true;
    if (words(n.cls).some((word) => ART.has(word)) || /illustration/i.test(n.label || "")) return true;
  }
  return false;
}

const inMain = (page, node) => regionOf(page, node) === "main" && !decorative(page, node);
const contains = (page, outer, inner) => {
  for (let n = inner; n; n = page.parent.get(n)) if (n === outer) return true;
  return false;
};

// The largest font a piece of text in the element is drawn in, leaving out
// one part of it.
function textSize(page, node, skip = null) {
  if (node === skip || !isNode(node) || node.hidden) return 0;
  let size = (node.kids || []).some((kid) => typeof kid === "string" && kid.trim()) ? node.fs || 0 : 0;
  for (const kid of node.kids || []) size = Math.max(size, textSize(page, kid, skip));
  return size;
}

// Lines that are links or buttons: "Read the story", "Get started".
function actionLines(page, node) {
  const lines = new Set();
  const visit = (n) => {
    if (!isNode(n)) return;
    if (n.tag === "a" || n.tag === "button" || n.role === "button" || n.role === "link") {
      const line = lineOf(page, n);
      if (line) lines.add(line);
    }
    for (const kid of n.kids || []) visit(kid);
  };
  visit(node);
  return lines;
}
const CTA = /^(read|watch|see|learn|view|get|start|try|sign|book|request|contact|explore|discover|find|download|join|talk)\b.{0,40}$|[→↗]$/i;

const siblings = (page, node) => ((page.parent.get(node) || {}).kids || []).filter(isNode);

// ---- Numbers ----

const NUMBER = String.raw`\d{1,3}(?:[,.\u00a0 ]\d{3})+(?:[.,]\d+)?|\d+(?:[.,]\d+)?`;
const CURRENCY = String.raw`(?:[A-Z]{1,3})?[$€£¥₹₺₩₽]|(?:USD|EUR|GBP|TRY)\s?`;
const MAGNITUDE = String.raw`(?:[kKMBT]|[Bb]n|[Mm]n|[Mm]illion|[Bb]illion|[Tt]rillion|[Mm]io|[Mm]rd|[Mm]ilyon|[Mm]ilyar|bin)`;
// The whole text of a figure: "135+", "$1.9T", "99.999%", "200M+", "10x".
const FIGURE = new RegExp(`^(?:${CURRENCY})?\\s?(?:${NUMBER})\\s?(?:${MAGNITUDE}(?![a-z]))?\\s?[+%xX×]?\\+?$`);
// A number in a sentence that claims something: "3,000 users", "75% of",
// "250 million+ API requests", "10x faster".
const CLAIM = new RegExp(`(?<![A-Za-z0-9])(?:${CURRENCY})?(?:${NUMBER})\\s?(?:${MAGNITUDE}\\b\\+?|[+%×]|[xX]\\b)|\\b\\d{1,3}(?:,\\d{3})+\\b\\+?`);
// A price: "$10", "30¢", "499 TL", "€8".
const MONEY = new RegExp(`(?:${CURRENCY})\\s?\\d[\\d.,]*|\\d[\\d.,]*\\s?(?:[$€£¥₹₺¢]|USD|EUR|GBP|TRY|TL)(?![a-z])`);
// A promotion, in English or another language. The Turkish words list both
// i's: a dotted capital İ does not match i, even ignoring case.
const PROMO = /\b(off|save|saving|savings|discounts?|coupons?|promo|perks)\b|(?<![\p{L}])([iİ]nd[iİ]r[iİ]m|kampanya|f[ıi]rsat|rabatt|remise|r[ée]duction|descuento|oferta|desconto|sconto)/iu;
const VERSION = /\b(TLS|SSL|iOS|iPadOS|macOS|Android|Windows|Node(\.js)?|Python|PHP|Java|Ruby|Chrome|Firefox|Safari|Edge|version|v)\s?$/i;
const FEE = /^\+|\bfees?\b|\bstarting at\b|\/(mo|month|year|yr)\b/i;
const SCALED = new RegExp(`${MAGNITUDE}(?![a-z])|[+%xX\u00d7]`);

// A figure that counts something. A sum of money without a magnitude is a
// price ("$5.46"), a lone small number is a step ("1", "02"), and a year is
// a date.
function isStat(line) {
  if (!FIGURE.test(line) || /^(19|20)\d\d$/.test(line)) return false;
  const digits = line.replace(/^\D+/, "");
  if (new RegExp(`^(?:${CURRENCY})`).test(line)) return new RegExp(MAGNITUDE).test(digits.replace(/^[\d.,\s]+/, ""));
  return SCALED.test(digits.replace(/^[\d.,\s]+/, "")) || (parseFloat(digits.replace(/[^\d.]/g, "")) >= 10 && !/^0\d/.test(digits));
}

// A figure drawn larger than the words beside it, as a stat block draws
// "135+" over "currencies and payment methods supported". The words are
// what the figure's own small box holds besides it; a box that also holds
// another figure is the row of stats, not this one.
function figureStats(page, taken) {
  const figures = [];
  for (const node of page.all) {
    if (node.tag === "sup" || node.tag === "sub" || !node.kids) continue;
    const line = lineOf(page, node);
    if (!FIGURE.test(line)) continue;
    if (node.kids.some((kid) => isNode(kid) && lineOf(page, kid) === line)) continue;
    if (!inMain(page, node)) continue;
    figures.push(node);
  }
  const count = new Map();
  for (const figure of figures) for (const up of ancestors(page, figure)) count.set(up, (count.get(up) || 0) + 1);
  const stats = [];
  for (const figure of figures) {
    if (!isStat(lineOf(page, figure)) || taken.some((outer) => contains(page, outer, figure))) continue;
    let item = figure;
    for (let i = 0; i < 4; i++) {
      const up = page.parent.get(item);
      if (!up || count.get(up) > 1 || regionOf(page, up) !== "main") break;
      item = up;
    }
    if (item === figure) continue;
    // A dashboard drawn on the page (a firewall's "Allowed 950.8k" over a
    // chart's axis) packs many figures together; a row of stats has a few.
    let around = item;
    for (let i = 0; i < 3 && page.parent.get(around); i++) around = page.parent.get(around);
    if (count.get(around) >= 7) continue;
    const value = lineOf(page, figure);
    const lines = linesOf(page, item);
    const at = lines.indexOf(value);
    if (at === -1) continue;
    // The words right under the figure, else right above it.
    const label = lines[at + 1] || lines[at - 1] || "";
    if (label.length < 3 || label.length > 160 || !/\p{L}{2}/u.test(label) || CTA.test(label) || isStat(label)) continue;
    const size = textSize(page, figure);
    if (!(size >= 20 && size >= 1.25 * textSize(page, item, figure))) continue;
    stats.push({ value, label, quote: lines[at + 1] ? `${value} ${label}` : `${label} ${value}`, node: item });
  }
  return stats;
}

// A short block of text with a claiming number in it, outside prices and
// promotions: "Why OpenAI chose Linear and scaled to 3,000 users".
function sentenceStats(page, taken) {
  const stats = [];
  // A pricing page's numbers are its terms ("+ 1.5% for international cards").
  if (page.role === "pricing") return stats;
  for (const node of page.all) {
    if (!node.block || !node.kids || node.kids.some((kid) => isNode(kid) && kid.block)) continue;
    const line = lineOf(page, node);
    if (line.length < 12 || line.length > 220 || FIGURE.test(line)) continue;
    // A version is not a claim: "TLS 1.2+", "iOS 15+".
    const claim = [...line.matchAll(new RegExp(CLAIM.source, "g"))].find((m) => !VERSION.test(line.slice(Math.max(0, m.index - 12), m.index)));
    if (!claim) continue;
    if (PROMO.test(line) || FEE.test(line) || /^up to\b/i.test(line) || (MONEY.test(line) && !new RegExp(`(?:${CURRENCY})\\s?(?:${NUMBER})\\s?${MAGNITUDE}\\b`).test(line))) continue;
    if (!inMain(page, node) || taken.some((outer) => contains(page, outer, node))) continue;
    stats.push({ value: claim[0].trim(), label: "", quote: line, node });
  }
  return stats;
}

// ---- Testimonials ----

const QUOTE_PART = new Set(["text", "body", "content", "copy", "message"]);
const BYLINE_PART = new Set(["author", "name", "role", "title", "company", "byline", "meta", "cite", "attribution", "avatar", "logo", "image", "headshot", "person"]);
const QUOTED = /^["“„«‘'].{30,}["”“»’']$/s;
const PARTICLE = "(?:de|da|das|do|dos|van|von|der|den|del|della|di|du|la|le|bin|ibn|al|el)";
const PERSON = new RegExp(`^(?:[-–—~]\\s*)?(\\p{Lu}[\\p{L}'’.-]*(?:\\s+(?:${PARTICLE}\\s+)?\\p{Lu}[\\p{L}'’.-]*){1,3})(?=$|\\s*[,|·•–—-]|\\s+(?:at|@)\\s)`, "u");
const NOT_A_PERSON = /^(read|watch|see|learn|view|customer|case|success|the|our|more|full|story|stories)\b/i;
const PORTRAIT = /avatar|headshot|portrait|photo|picture|profile|image of/i;

function quoteNodes(page) {
  const found = page.all.filter((node) => {
    if (!node.kids) return false;
    const own = words(node.cls);
    const marked =
      node.tag === "q" ||
      node.tag === "blockquote" ||
      ((own.includes("quote") || (own.includes("testimonial") && own.some((word) => QUOTE_PART.has(word)))) && !own.some((word) => BYLINE_PART.has(word)));
    if (!marked && !(node.block && QUOTED.test(lineOf(page, node)))) return false;
    const length = lineOf(page, node).length;
    return length >= 40 && length <= 1500 && inMain(page, node);
  });
  return found.filter((node) => !found.some((other) => other !== node && contains(page, node, other)));
}

// The texts an element holds, one per element that holds text, in order:
// a byline set as "Michael Truell" and "Co-founder & CEO" is two parts.
function partsOf(page, node, out = []) {
  if (!isNode(node) || node.hidden || node.tag === "img" || node.tag === "svg") return out;
  if (node.role === "img" && node.label) {
    out.push(node.label);
    return out;
  }
  let own = "";
  const flush = () => {
    const text = tidy(own);
    if (/[\p{L}\p{N}]/u.test(text)) out.push(text);
    own = "";
  };
  for (const kid of node.kids || []) {
    if (typeof kid === "string") own += kid;
    else {
      flush();
      partsOf(page, kid, out);
    }
  }
  flush();
  return out;
}

// "Kurtis Moyer, Lead Product Manager of Payments, Mindbody", "Jane Doe,
// CTO at Acme", or the name, the role and the company as parts of their
// own: the person, their role and their company.
function readByline(parts) {
  for (let i = 0; i < parts.length; i++) {
    const match = parts[i].match(PERSON);
    if (!match || NOT_A_PERSON.test(match[1]) || parts[i].length > 140) continue;
    const person = match[1].trim();
    let rest = parts[i].slice(match[0].length).replace(/^[\s,|·•–—-]+/, "").trim();
    const used = [parts[i]];
    let next = i + 1;
    if (!rest && parts[next] && parts[next].length <= 120 && !CTA.test(parts[next])) {
      // "Susy Schöneberg" and then ", VP of Impact" as the text after it.
      rest = parts[next++].replace(/^[\s,|·•–—-]+/, "");
      used.push(rest);
    }
    let role = rest;
    let company = "";
    const at = rest.match(/^(.*?)\s+(?:at|@)\s+(.+)$/i);
    if (at) [role, company] = [at[1], at[2]];
    else if (rest.includes(",")) {
      const pieces = rest.split(",");
      company = pieces.pop().trim();
      role = pieces.join(",").trim();
    } else if (rest && parts[next] && parts[next].length <= 60 && !CTA.test(parts[next]) && !PERSON.test(parts[next])) {
      company = parts[next];
      used.push(company);
    }
    const byline = used.map((part) => part.replace(/[\s,]+$/, "")).join(", ");
    return { person, role: role.trim(), company: company.trim(), byline };
  }
  return null;
}

const hasHeading = (node) => isNode(node) && (/^h[1-3]$/.test(node.tag) || (node.kids || []).some(hasHeading));

function testimonials(page) {
  const quotes = quoteNodes(page);
  const found = [];
  for (const node of quotes) {
    const own = linesOf(page, node);
    const quote = own.reduce((a, b) => (b.length > a.length ? b : a), "");
    // The card: the quote's box, widened while it holds no other quote, no
    // heading of a section and not much more than a byline.
    let card = node;
    for (let i = 0; i < 4; i++) {
      const up = page.parent.get(card);
      if (!up || quotes.some((other) => other !== node && contains(page, up, other))) break;
      if (linesOf(page, up).length - own.length > 6 || hasHeading(up)) break;
      card = up;
    }
    const actions = actionLines(page, card);
    const all = partsOf(page, card);
    const quoted = partsOf(page, node);
    const end = all.lastIndexOf(quoted[quoted.length - 1]);
    const usable = (part) => !actions.has(part) && !CTA.test(part) && !quote.includes(part);
    const after = all.filter((part, i) => i > end && usable(part));
    const byline = readByline(after) || readByline(all.filter(usable));
    if (!byline) continue;
    if (!byline.company) {
      const logo = imagesIn(page, card).map(imageName).find((name) => name && !PORTRAIT.test(name) && !name.toLowerCase().includes(byline.person.toLowerCase()));
      if (logo) byline.company = logo;
    }
    const text = quote.replace(/^["“„«‘']+|["”“»’']+$/g, "").trim();
    found.push({ quote: text, ...byline, node: card });
  }
  return found;
}

// ---- Logos and names ----

function imagesIn(page, node) {
  const out = [];
  const visit = (n) => {
    if (!isNode(n)) return;
    if (n.tag === "img" || n.tag === "svg" || (n.role === "img" && n.label)) out.push(n);
    for (const kid of n.kids || []) visit(kid);
  };
  visit(node);
  return out;
}

// The name an image gives for itself, without "logo" and the like:
// "GitHub icon" is GitHub, "Logo of Amazon" is Amazon.
function imageName(node) {
  const raw = String(node.alt || node.label || node.title || "").trim();
  if (!raw || PORTRAIT.test(raw)) return "";
  const name = raw
    .replace(/\b(company|customer|client|brand|partner)?\s*(logo(type|mark)?s?|wordmark|icon|emblem|image|img|svg|png)\b(\s+(of|for))?/gi, " ")
    .replace(/^\s*(the)\s+/i, "")
    .replace(/[\s|:–—-]+$|^[\s|:–—-]+/g, "")
    .replace(/\s+/g, " ")
    .trim();
  return name.length >= 2 && name.length <= 40 && /\p{L}/u.test(name) ? name : "";
}

const logoSized = (node) => node.w >= 30 && node.h >= 10 && node.w <= 420 && node.h <= 200;

// A caption for a row of logos: the short text just before or after it,
// a level or two up ("Trusted by 50,000 teams", "Powering the companies
// building the future"). One that speaks of customers or backers wins,
// then a heading, then the nearest text.
const CAPTION = /\b(trusted|used by|loved|powering|powers|customers|clients|companies|teams|brands|businesses|join|choose|rely|backed|investors|partners|featured|as seen|work with)\b/i;
function captionOf(page, node) {
  const found = [];
  let at = node;
  for (let level = 0; level < 4 && at; level++) {
    const row = siblings(page, at);
    const i = row.indexOf(at);
    for (const next of [row[i - 1], row[i + 1]]) {
      if (!next || next.tag === "a" || next.tag === "button" || imagesIn(page, next).length) continue;
      const line = lineOf(page, next);
      if (line.length >= 3 && line.length <= 140 && /\p{L}{2}/u.test(line) && !QUOTED.test(line)) found.push({ line, heading: hasHeading(next) });
    }
    at = page.parent.get(at);
  }
  const pick = found.find((c) => CAPTION.test(c.line)) || found.find((c) => c.heading) || found[0];
  return pick ? pick.line : "";
}

const NOT_CUSTOMERS = /\b(investors?|backed|funded|backers|press|featured|as seen|in the news|media|awards?|recogni[sz]ed|partners?|integrat\w*|works with|connects?|payments?|pay with|accept)\b/i;

// Rows of four or more named logos in the page body. The row is the
// smallest box that holds them with little text of its own.
function logoWalls(page) {
  const items = page.all.filter((node) => {
    if (!(node.tag === "img" || node.tag === "svg" || node.role === "img") || !imageName(node) || !logoSized(node)) return false;
    return regionOf(page, node) === "main" && ![...ancestors(page, node)].some((up) => words(up.cls).some((word) => ART.has(word)));
  });
  const under = new Map();
  for (const item of items) {
    let up = page.parent.get(item);
    for (let level = 0; up && level < 6; level++, up = page.parent.get(up)) {
      if (!under.has(up)) under.set(up, []);
      under.get(up).push(item);
    }
  }
  const taken = new Set();
  const walls = [];
  const boxes = [...under.keys()].sort((a, b) => page.depth.get(b) - page.depth.get(a));
  for (const box of boxes) {
    const free = under.get(box).filter((item) => !taken.has(item));
    const names = [...new Set(free.map(imageName))];
    if (names.length < 4) continue;
    const ownText = lineOf(page, box).length - names.join(" ").length;
    if (ownText > 300) continue;
    free.forEach((item) => taken.add(item));
    if (walls.some((wall) => wall.names.join() === names.join())) continue;
    const caption = captionOf(page, box);
    const hint = [caption, ...[box, ...ancestors(page, box)].slice(0, 4).map((n) => n.cls || "")].join(" ");
    // Badges for security standards are not customers either.
    const badges = names.filter((name) => /certif|complian|badge|award/i.test(name) || STANDARDS.some(([pattern]) => pattern.test(name)));
    const customers = page.role !== "integrations" && !NOT_CUSTOMERS.test(hint.replace(/[_-]+/g, " ")) && badges.length < names.length / 2;
    walls.push({ names, caption, customers, node: box });
  }
  return walls;
}

// A link one level below a listing page (/customers/ramp under
// /customers) that shows a logo: a customer story or an integration.
function childPath(href, base) {
  try {
    const url = new URL(href);
    const root = new URL(base);
    const prefix = root.pathname.replace(/\/+$/, "");
    if (url.host !== root.host || !prefix) return "";
    const rest = url.pathname.replace(/\/+$/, "");
    return rest.startsWith(`${prefix}/`) && !rest.slice(prefix.length + 1).includes("/") ? rest.slice(prefix.length + 1) : "";
  } catch {
    return "";
  }
}

function listedCards(page) {
  const cards = [];
  const seen = new Set();
  for (const node of page.all) {
    if (node.tag !== "a" || !node.href || seen.has(node.href) || !childPath(node.href, page.url) || !inMain(page, node)) continue;
    const logo = imagesIn(page, node).map(imageName).find(Boolean);
    if (!logo) continue;
    seen.add(node.href);
    const actions = actionLines(page, node);
    const lines = linesOf(page, node).filter((line) => !CTA.test(line) && !(actions.has(line) && line.length < 25));
    cards.push({ name: logo, first: lines[0] || "", headline: lines.reduce((a, b) => (b.length > a.length ? b : a), ""), link: node.href, node });
  }
  return cards;
}

// ---- Pricing ----

const NOT_A_PLAN = /^(total|subtotal|grand total|estimated? (total|cost)|monthly estimate|summary|plan subscription|toplam|ara toplam)\b/i;
const NO_PRICE = /^(free|free forever|custom|custom pricing|contact (us|sales)|talk to (us|sales)|let'?s talk|get a quote|request a quote|ücretsiz|özel|kostenlos|gratuit|gratis|grátis|gratuito)$/i;
const PERIOD = /^(\/|per\b|a month|month|mo\b|user|seat|yearly|monthly|annually)/i;
const TERMS = /\b(per|month|monthly|mo|year|yearly|annual|annually|yr|user|users|seat|seats|member|editor|billed|forever|free for|transaction|one-time|lifetime)\b|\//i;

// A plan card: its name, then a price ("$10 per user/month", "Free",
// "Custom") within its first lines, then what the price is for.
function planOf(page, card) {
  if (!inMain(page, card)) return null;
  // A plan shows more than a name and a sum: a cost calculator's rows
  // ("Total Compute", "$10") do not.
  const lines = linesOf(page, card).slice(0, 16);
  if (lines.length < 3) return null;
  const heading = (function find(n) {
    if (!isNode(n) || n.hidden) return null;
    if (/^h[1-6]$/.test(n.tag)) return n;
    for (const kid of n.kids || []) {
      const h = find(kid);
      if (h) return h;
    }
    return null;
  })(card);
  const actions = actionLines(page, card);
  let nameAt = heading ? lines.indexOf(lineOf(page, heading)) : -1;
  if (nameAt === -1 || lines[nameAt].length > 40) nameAt = lines[0].length <= 30 && !MONEY.test(lines[0]) ? 0 : -1;
  // A button is not a plan's name ("Get started" over "Contact sales"), and
  // neither is a step of a cost calculator ("1. Choose your plan").
  if (nameAt === -1 || actions.has(lines[nameAt]) || CTA.test(lines[nameAt]) || /^\d+[.)]\s/.test(lines[nameAt]) || NOT_A_PLAN.test(lines[nameAt])) return null;
  let priceAt = -1;
  for (let i = nameAt + 1; i < Math.min(lines.length, nameAt + 8); i++) {
    if ((MONEY.test(lines[i]) && lines[i].length <= 60 && !PROMO.test(lines[i]) && !/^[-\u2212]/.test(lines[i])) || NO_PRICE.test(lines[i])) {
      priceAt = i;
      break;
    }
  }
  if (priceAt === -1) return null;
  let price = lines[priceAt];
  let next = priceAt + 1;
  if (lines[next] && lines[next].length <= 25 && PERIOD.test(lines[next])) price = `${price} ${lines[next++]}`;
  const terms = lines[next] && lines[next].length <= 80 && TERMS.test(lines[next]) && !MONEY.test(lines[next]) ? lines[next++] : "";
  const listed = [];
  (function items(n) {
    if (!isNode(n) || n.hidden) return;
    if (n.tag === "li") listed.push(lineOf(page, n));
    else for (const kid of n.kids || []) items(kid);
  })(card);
  const features = listed.filter((line) => line && !actions.has(line) && !CTA.test(line)).slice(0, 12);
  const between = lines.slice(nameAt + 1, priceAt).filter((line) => line.length <= 40 && !actions.has(line) && !CTA.test(line));
  return { plan: lines[nameAt], price, terms, features, money: MONEY.test(price), quote: [lines[nameAt], ...between, price, terms].filter(Boolean).join(" ") };
}

// Rows of two to eight plan cards side by side, at least one with a price.
function plans(page) {
  const groups = [];
  for (const node of page.all) {
    const kids = (node.kids || []).filter((kid) => isNode(kid) && !kid.hidden && kid.block);
    if (kids.length < 2 || kids.length > 8 || !inMain(page, node)) continue;
    const found = kids.map((kid) => planOf(page, kid)).filter(Boolean);
    const names = new Set(found.map((plan) => plan.plan.toLowerCase()));
    if (found.length < 2 || names.size < found.length || !found.some((plan) => plan.money) || found.length < kids.length * 0.6) continue;
    groups.push({ node, plans: found });
  }
  // A row of plan rows is not itself a row of plans: the innermost rows are kept.
  const kept = groups.filter((group) => !groups.some((other) => other !== group && contains(page, group.node, other.node)));
  const out = [];
  for (const group of kept) {
    for (const plan of group.plans) {
      if (!out.some((known) => known.plan.toLowerCase() === plan.plan.toLowerCase())) out.push({ ...plan, node: group.node });
    }
  }
  return out;
}

// ---- Security standards ----

const STANDARDS = [
  [/\bSOC ?([123])(?:\s*(?:Type|Typ)\s*(II|I|2|1)\b)?/i, (m) => `SOC ${m[1]}${m[2] ? ` Type ${{ 1: "I", 2: "II" }[m[2]] || m[2].toUpperCase()}` : ""}`],
  [/\bISO(?:\/IEC)?\s?(27001|27017|27018|27701|9001|42001|22301|14001|20000-1)\b/i, (m) => `ISO ${m[1]}`],
  [/\bGDPR\b|General Data Protection Regulation/i, () => "GDPR"],
  [/\bCCPA\b|\bCPRA\b|California Consumer Privacy Act/i, () => "CCPA"],
  [/\bHIPAA\b/i, () => "HIPAA"],
  [/\bPCI[ -]?DSS\b|\bPCI (?:Service Provider )?Level ?(?:1|One)\b/i, () => "PCI DSS"],
  [/\bFedRAMP\b/i, () => "FedRAMP"],
  [/\bStateRAMP\b/i, () => "StateRAMP"],
  [/\bCSA STAR\b/i, () => "CSA STAR"],
  [/\bTISAX\b/i, () => "TISAX"],
  [/\bHITRUST\b/i, () => "HITRUST"],
  [/\bCyber Essentials(?: Plus)?\b/i, (m) => (/plus/i.test(m[0]) ? "Cyber Essentials Plus" : "Cyber Essentials")],
  [/\bBSI C5\b|\bC5 (?:attestation|certified|certification|compliance)\b/i, () => "BSI C5"],
  [/\bIRAP\b/, () => "IRAP"],
  [/\bNIST(?: SP)? 800-(?:53|171)\b|\bNIST CSF\b|\bNIST Cybersecurity Framework\b/i, (m) => m[0].replace(/\s+/g, " ")],
  [/\bFERPA\b/, () => "FERPA"],
  [/\bCOPPA\b/, () => "COPPA"],
  [/\bKVKK\b/, () => "KVKK"],
  [/\bLGPD\b/, () => "LGPD"],
  [/\bPIPEDA\b/, () => "PIPEDA"],
  [/\bData Privacy Framework\b/i, () => "Data Privacy Framework"],
  [/\bWCAG(?: 2(?:\.[0-2])?)?\b/, (m) => m[0]],
];

// The sentence a match sits in, when its block of text is long, or the
// words around it when the block has no sentences.
function sentenceAround(text, index) {
  // A link at the end ("Request SOC 2 →") is not part of the claim.
  const line = text.replace(/(?<=[.!?)])\s+[^.!?]{1,40}[\u2192\u2197]$/, "");
  if (line.length <= 240) return line;
  let at = 0;
  for (const part of line.split(/(?<=[.!?])\s+/)) {
    if (index < at + part.length + 1) {
      if (part.length <= 240) return part;
      const from = Math.max(0, line.lastIndexOf(" ", Math.max(0, index - 100)));
      const to = line.indexOf(" ", Math.min(line.length, index + 120));
      return `${from > 0 ? "…" : ""}${line.slice(from, to === -1 ? line.length : to).trim()}${to === -1 ? "" : "…"}`;
    }
    at += part.length + 1;
  }
  return clip(line, 240);
}

function standards(page) {
  const found = [];
  const add = (standard, quote, node) => {
    if (!found.some((known) => known.standard === standard)) found.push({ standard, quote, node });
  };
  for (const node of page.all) {
    if (regionOf(page, node) === "nav" || decorative(page, node)) continue;
    const texts = [];
    if (node.tag === "img" || node.tag === "svg" || node.role === "img") {
      const name = String(node.alt || node.label || node.title || "").trim();
      if (name) texts.push(name);
    } else if (node.block && node.kids && !node.kids.some((kid) => isNode(kid) && kid.block)) {
      // A short link ("GDPR" in a footer) names a page, not a claim.
      const line = lineOf(page, node);
      const linked = node.tag === "a" || [...ancestors(page, node)].some((up) => up.tag === "a");
      if (!(linked && line.length <= 40)) texts.push(line);
    }
    for (const text of texts) {
      for (const [pattern, name] of STANDARDS) {
        const match = text.match(pattern);
        if (match) add(name(match), sentenceAround(text, match.index), node);
      }
    }
  }
  return found;
}

// ---- JSON-LD ----

function jsonLdObjects(model) {
  const out = [];
  const walk = (value) => {
    if (Array.isArray(value)) return value.forEach(walk);
    if (!isNode(value)) return;
    out.push(value);
    for (const key of Object.keys(value)) if (isNode(value[key])) walk(value[key]);
  };
  for (const text of (model && model.jsonLd) || []) {
    try {
      walk(JSON.parse(text));
    } catch {
      // Broken JSON-LD says nothing.
    }
  }
  return out;
}

const typeOf = (value) => [].concat(value["@type"] || []).map(String);
const plain = (value) =>
  String(value === undefined || value === null ? "" : value)
    .replace(/<[^>]*>/g, " ")
    .replace(/&nbsp;/g, " ")
    .replace(/&quot;/g, '"')
    .replace(/&#39;|&apos;/g, "'")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&amp;/g, "&")
    .replace(/\s+/g, " ")
    .trim();
const nameOf = (value) => (isNode(value) ? plain(value.name) : plain(value));
const excerpt = (object) => clip(JSON.stringify(object), 300);

function ldRatings(page) {
  return jsonLdObjects(page.model)
    .filter((value) => isNode(value.aggregateRating))
    .map((value) => {
      const r = value.aggregateRating;
      return {
        value: plain(r.ratingValue),
        best: plain(r.bestRating) || "5",
        count: plain(r.ratingCount || r.reviewCount),
        item: nameOf(value),
        platform: "",
        from: "json-ld",
        quote: excerpt({ name: value.name, aggregateRating: r }),
      };
    })
    .filter((rating) => rating.value);
}

const PLATFORMS = /\b(G2|Capterra|Trustpilot|App Store|Google Play|Product Hunt|Gartner(?: Peer Insights)?|TrustRadius|GetApp|Software Advice|Chrome Web Store|Shopify App Store|Clutch|Google Reviews?)\b/i;
const RATING = /(\d(?:[.,]\d{1,2})?)\s?(?:\/\s?(5|10)\b|out of (5|10)\b|stars?\b|★)/i;

function shownRatings(page) {
  const found = [];
  for (const node of page.all) {
    if (!node.block || !node.kids || node.kids.some((kid) => isNode(kid) && kid.block) || !inMain(page, node)) continue;
    const line = lineOf(page, node);
    const rating = line.length <= 200 && line.match(RATING);
    const platform = rating && line.match(PLATFORMS);
    if (!platform) continue;
    found.push({ value: rating[1].replace(",", "."), best: rating[2] || rating[3] || "5", count: "", item: "", platform: platform[1], from: "page", quote: line, node });
  }
  return found;
}

function ldFaqs(page) {
  const out = [];
  for (const value of jsonLdObjects(page.model)) {
    if (!typeOf(value).includes("Question")) continue;
    const answer = [].concat(value.acceptedAnswer || value.suggestedAnswer || [])[0];
    const question = plain(value.name);
    const text = answer ? plain(answer.text) : "";
    if (question && text) out.push({ question, answer: clip(text, 1200), from: "json-ld" });
  }
  return out;
}

// Questions the page shows with their answers: a <details> and its
// <summary>, or a question in a section about questions.
function shownFaqs(page) {
  const out = [];
  for (const node of page.all) {
    if (node.tag !== "details" || !inMain(page, node)) continue;
    const summary = (node.kids || []).find((kid) => isNode(kid) && kid.tag === "summary");
    if (!summary) continue;
    const question = lineOf(page, summary);
    const answer = linesOf(page, node).filter((line) => line !== question).join(" ");
    if (question && answer) out.push({ question, answer: clip(answer, 1200), from: "page", node });
  }
  for (const node of page.all) {
    if (!/^h[1-6]$/.test(node.tag) || !/\b(faqs?|frequently asked|questions)\b/i.test(lineOf(page, node)) || !inMain(page, node)) continue;
    let section = page.parent.get(node);
    while (section && linesOf(page, section).length < 3) section = page.parent.get(section);
    if (!section) continue;
    // A question and, right after it in the same box, its answer. An answer
    // the page keeps folded away is not on the page, so its question is
    // left out too.
    (function visit(n) {
      if (!isNode(n) || n.hidden) return;
      const line = n.block && n !== node ? lineOf(page, n) : "";
      if (/\?$/.test(line) && line.length <= 200 && linesOf(page, n).length === 1) {
        const row = siblings(page, n);
        const next = row[row.indexOf(n) + 1];
        const answer = next ? lineOf(page, next) : "";
        if (answer.length >= 20 && !/\?$/.test(answer)) out.push({ question: line, answer: clip(answer, 1200), from: "page", node: section });
        return;
      }
      for (const kid of n.kids || []) visit(kid);
    })(section);
  }
  return out;
}

function ldCompany(page) {
  const out = [];
  for (const value of jsonLdObjects(page.model)) {
    if (!typeOf(value).some((type) => /Organization|Corporation|LocalBusiness/.test(type))) continue;
    const add = (field, text, raw) => {
      if (text && !out.some((known) => known.field === field)) out.push({ field, value: text, quote: excerpt({ [raw]: value[raw] }) });
    };
    add("Name", plain(value.name), "name");
    add("Legal name", plain(value.legalName), "legalName");
    add("Founded", plain(value.foundingDate), "foundingDate");
    const founders = [].concat(value.founder || value.founders || []).map(nameOf).filter(Boolean);
    add("Founders", founders.join(", "), value.founder ? "founder" : "founders");
    const staff = value.numberOfEmployees;
    const staffText = isNode(staff) ? plain(staff.value || [staff.minValue, staff.maxValue].filter(Boolean).join(" to ")) : plain(staff);
    add("Employees", staffText, "numberOfEmployees");
    const address = isNode(value.address) ? [value.address.addressLocality, value.address.addressRegion, value.address.addressCountry].map(nameOf).filter(Boolean).join(", ") : plain(value.address);
    add("Address", address, "address");
  }
  return out;
}

// ---- All of it ----

const keyOf = (text) => text.toLowerCase().replace(/[^\p{L}\p{N}]+/gu, " ").trim();

// Every page's claims, each with its page's address and the time it was
// read, each said once.
function findClaims(pages) {
  const read = pages.map(pageOf);
  const at = (page) => ({ url: page.url, readAt: page.readAt });
  const out = { stats: [], testimonials: [], customers: [], logoWalls: [], pricing: [], integrations: [], compliance: [], ratings: [], faqs: [], company: [] };
  const once = (list, key, item) => {
    if (!key || list.some((known) => known._key === key)) return;
    list.push({ _key: key, ...item });
  };
  // The page made for a subject is the better source on it.
  const byRole = (role) => [...read.filter((page) => page.role === role), ...read.filter((page) => page.role !== role)];

  for (const page of read) {
    const quotes = testimonials(page);
    for (const t of quotes) once(out.testimonials, keyOf(t.quote), { quote: t.quote, person: t.person, role: t.role, company: t.company, byline: t.byline, ...at(page) });
    const tiers = page.role === "pricing" || !read.some((other) => other.role === "pricing") ? plans(page) : [];
    for (const plan of tiers) once(out.pricing, keyOf(plan.plan), { plan: plan.plan, price: plan.price, terms: plan.terms, features: plan.features, quote: plan.quote, ...at(page) });
    const walls = logoWalls(page);
    // The same row of logos on several pages is listed once.
    for (const wall of walls) once(out.logoWalls, wall.names.join("|"), { caption: wall.caption, names: wall.names, customers: wall.customers, ...at(page) });
    const taken = [...quotes, ...tiers, ...walls].map((item) => item.node);
    for (const stat of [...figureStats(page, taken), ...sentenceStats(page, taken)]) once(out.stats, keyOf(stat.quote), { value: stat.value, label: stat.label, quote: stat.quote, ...at(page) });
    if (page.role === "customers") {
      for (const card of listedCards(page)) once(out.customers, keyOf(card.name), { name: card.name, from: "customer story", quote: card.headline, link: card.link, ...at(page) });
    }
    if (page.role === "integrations") {
      for (const card of listedCards(page)) once(out.integrations, keyOf(card.name), { name: card.first && card.first.length <= 40 ? card.first : card.name, link: card.link, ...at(page) });
      if (!out.integrations.length) for (const wall of walls) for (const name of wall.names) once(out.integrations, keyOf(name), { name, link: "", ...at(page) });
    }
    for (const { node, ...rating } of [...ldRatings(page), ...shownRatings(page)]) once(out.ratings, keyOf(`${rating.platform} ${rating.item} ${rating.value}`), { ...rating, ...at(page) });
    for (const faq of [...ldFaqs(page), ...shownFaqs(page)]) once(out.faqs, keyOf(faq.question), { question: faq.question, answer: faq.answer, from: faq.from, ...at(page) });
    for (const item of ldCompany(page)) once(out.company, item.field, { ...item, ...at(page) });
  }
  for (const page of byRole("security")) for (const item of standards(page)) once(out.compliance, item.standard, { standard: item.standard, quote: item.quote, ...at(page) });
  // "SOC 2" says less than "SOC 2 Type II" from the same site.
  out.compliance = out.compliance.filter((item) => !out.compliance.some((other) => other !== item && other.standard.startsWith(`${item.standard} `)));
  for (const wall of out.logoWalls.filter((w) => w.customers)) {
    for (const name of wall.names) once(out.customers, keyOf(name), { name, from: "logo wall", quote: wall.caption, link: "", url: wall.url, readAt: wall.readAt });
  }
  for (const t of out.testimonials.filter((item) => item.company)) once(out.customers, keyOf(t.company), { name: t.company, from: "testimonial", quote: t.byline, link: "", url: t.url, readAt: t.readAt });
  for (const list of Object.values(out)) for (const item of list) delete item._key;
  out.stats = out.stats.slice(0, 40);
  out.faqs = out.faqs.slice(0, 40);
  out.integrations = out.integrations.slice(0, 200);
  return out;
}

module.exports = { findClaims, pageOf, textOf, linesOf, lineOf, tidy, regionOf, imageName, childPath, FIGURE, CLAIM, MONEY };
