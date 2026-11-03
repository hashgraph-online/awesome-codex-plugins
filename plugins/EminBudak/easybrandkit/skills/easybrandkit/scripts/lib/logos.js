"use strict";

// The site's own logos as it draws them, its look (colours and typefaces),
// and what its head and links say about it: icons, social preview images,
// the web manifest, app store listings and social media pages.
//
// Marks are <img> and outermost <svg> elements, plus elements named "logo" or
// "brand" that draw the logo themselves (CSS background, styled text). A
// mark is kept when it sits in the page header (the bar at the top) or the
// page footer (the block that ends the page), inside a link to the home page,
// or is named after the brand; customer, partner and payment strips are
// skipped. Everything is read from one DOM snapshot: no extra request, no
// page JavaScript, until the marks are cut out one by one. Once cut, a mark
// in the page body that sits on a picture is dropped (an event's lockup over
// a photo), and a mark the page draws as SVG is saved as a vector too.

const fs = require("fs");
const path = require("path");
const zlib = require("zlib");
const { capture, metrics } = require("./page");
const { sleep } = require("./time");

const LOGO_MAX = 6;
const LOGO_MARGIN = 12;
const THIRD_PARTY = /partner|client|customer|reference|sponsor|testimonial|marquee|carousel|swiper|slider|badge|payment|award|certificat/i;
// Whole class or id tokens, so a card's "card-header" or a dialog's
// "modal-footer" is not the page's header or footer.
const HEADER_TOKEN = /^(site-|page-|main-|global-)?(header|navbar|nav-bar|topbar|top-bar|masthead)([_-].*)?$/i;
const FOOTER_TOKEN = /^(site-|page-|main-|global-)?footer([_-].*)?$/i;
const MARK_TOKEN = /^([a-z0-9]+[_-]+)*(logo|brand)([_-]+[a-z0-9]+)*$/i;
const hasToken = (hint, pattern) => hint.split(/\s+/).some((token) => pattern.test(token));
const BRAND_STOPWORDS = new Set(["home", "the", "and", "www", "site", "app", "official", "web"]);
const IMAGE_META = new Set([
  "og:image", "og:image:url", "og:image:secure_url", "og:logo",
  "twitter:image", "twitter:image:src", "msapplication-tileimage",
]);
// A bot check served instead of the page (a CAPTCHA, "Just a moment…"):
// read as a site, it gave a kit named "Human Verification" in the check
// provider's orange. A form's reCAPTCHA or Turnstile script on a real home
// page is common, so a script counts only on a short page with no logo.
const CHALLENGE_TITLE = /human verification|just a moment|attention required|access denied|verify you are human|are you a robot|security check|checking your browser|pardon our interruption|ddos-guard|one more step|request blocked|captcha/i;
const CHALLENGE_SRC = /challenges\.cloudflare\.com|hcaptcha\.com|google\.com\/recaptcha|recaptcha\.net|captcha-delivery\.com|px-cdn\.net|perimeterx|awswaf/i;
const SOCIAL_HOSTS = [
  [/^instagram\.com$/, "instagram"],
  [/^(facebook|fb)\.com$/, "facebook"],
  [/^(twitter|x)\.com$/, "x"],
  [/^linkedin\.com$/, "linkedin"],
  [/^(youtube\.com|youtu\.be)$/, "youtube"],
  [/^tiktok\.com$/, "tiktok"],
  [/^pinterest\.[a-z.]+$/, "pinterest"],
  [/^threads\.(net|com)$/, "threads"],
  [/^github\.com$/, "github"],
  [/^medium\.com$/, "medium"],
  [/^t\.me$/, "telegram"],
  [/^discord\.(gg|com)$/, "discord"],
];

function absoluteUrl(raw, base) {
  try {
    const url = new URL(String(raw || "").trim(), base);
    return /^https?:$/.test(url.protocol) ? url.href : "";
  } catch {
    return "";
  }
}

function pathOf(url) {
  try {
    return decodeURIComponent(new URL(url).pathname).toLowerCase();
  } catch {
    return "";
  }
}

// The brand is the site's own name: og:site_name, else the first label of a
// host name (acme.com → acme). Matched against paths and labels, never host
// names, so images served from the brand's own CDN are not all "logos".
function brandTokens(pageUrl, siteName) {
  const tokens = new Set();
  try {
    const host = new URL(pageUrl).hostname.replace(/^www\./, "");
    if (!/^[\d.]+$/.test(host) && !host.includes(":")) tokens.add(host.split(".")[0].toLowerCase());
  } catch {
    // No host name to take a brand from.
  }
  for (const word of String(siteName || "").toLowerCase().split(/[^\p{L}\p{N}]+/u)) tokens.add(word);
  return [...tokens].filter((token) => token.length >= 3 && !BRAND_STOPWORDS.has(token));
}

function cssColorToHex(color) {
  const m = String(color || "").match(/rgba?\(\s*(\d+)[,\s]+(\d+)[,\s]+(\d+)(?:[,\s/]+([\d.]+))?/);
  if (!m || (m[4] !== undefined && parseFloat(m[4]) === 0)) return "";
  return "#" + [m[1], m[2], m[3]].map((v) => Number(v).toString(16).padStart(2, "0")).join("");
}

// An app store listing or a social profile, as one canonical URL; share and
// intent links and bare home pages are not the brand's own pages.
function brandLink(raw, base) {
  let url;
  try {
    url = new URL(String(raw || "").trim(), base);
  } catch {
    return null;
  }
  if (!/^https?:$/.test(url.protocol)) return null;
  const host = url.hostname.toLowerCase().replace(/^(www|m|mobile)\./, "");
  const id = url.pathname.match(/\/id(\d{5,})/);
  if (/^(apps|itunes)\.apple\.com$/.test(host) && id) {
    // A developer page lists the maker's apps; its id is not an app's.
    const kind = /\/developer\//.test(url.pathname) ? "developer" : "app";
    return { type: "appstore", url: `https://apps.apple.com/${kind}/id${id[1]}` };
  }
  const pkg = url.searchParams.get("id");
  if (host === "play.google.com" && url.pathname.startsWith("/store/apps/details") && pkg) {
    return { type: "googleplay", url: `https://play.google.com/store/apps/details?id=${pkg}` };
  }
  const page = url.pathname.replace(/\/+$/, "");
  if (!page || /\/(sharer|share|intent|sharearticle|dialog)(\/|\.|$)|\/pin\/create/i.test(page)) return null;
  for (const [pattern, type] of SOCIAL_HOSTS) {
    if (pattern.test(host)) return { type, url: `https://${host}${page}` };
  }
  return null;
}

// alsoNamed: more names the brand goes by, such as the app a store listing
// named when its maker's domain says something else (Things on culturedcode.com).
async function findLogos(cdp, pageUrl, pageWidth, pageHeight, alsoNamed = "") {
  const snap = await cdp.send("DOMSnapshot.captureSnapshot", {
    computedStyles: ["visibility", "opacity", "background-color", "overflow-x", "overflow-y", "color", "font-family"],
  });
  const doc = (snap.documents || [])[0];
  const empty = { marks: [], icons: [], images: [], manifest: "", links: [], siteName: "", title: "", description: "", challenge: "", brand: { colors: [], fonts: {} }, wordTargets: [] };
  if (!doc || !doc.nodes || !doc.layout) return empty;
  const strings = snap.strings || [];
  const str = (index) => (typeof index === "number" && index >= 0 ? strings[index] || "" : "");
  const nodes = doc.nodes;
  const names = (nodes.nodeName || []).map(str);
  const parents = nodes.parentIndex || [];
  const attrCache = new Map();
  const attrs = (i) => {
    if (!attrCache.has(i)) {
      const out = {};
      const list = (nodes.attributes || [])[i] || [];
      for (let k = 0; k + 1 < list.length; k += 2) out[str(list[k]).toLowerCase()] = str(list[k + 1]);
      attrCache.set(i, out);
    }
    return attrCache.get(i);
  };
  const base = str(doc.baseURL) || str(doc.documentURL) || pageUrl;
  const layoutIndex = new Map();
  doc.layout.nodeIndex.forEach((nodeIndex, li) => layoutIndex.set(nodeIndex, li));
  const boxOf = (i) => {
    const li = layoutIndex.get(i);
    return li === undefined ? null : doc.layout.bounds[li] || null;
  };
  const styleOf = (i, k) => {
    const li = layoutIndex.get(i);
    return li === undefined ? "" : str((doc.layout.styles[li] || [])[k]);
  };
  const currentSrc = new Map();
  const rare = nodes.currentSourceURL;
  if (rare && rare.index) rare.index.forEach((nodeIndex, k) => currentSrc.set(nodeIndex, str(rare.value[k])));
  let pageOrigin = "";
  try {
    pageOrigin = new URL(base).origin;
  } catch {
    // An origin-less page has no home link either.
  }
  const isHomeHref = (raw) => {
    try {
      const href = new URL(raw || "", base);
      return href.origin === pageOrigin && !href.search && /^\/([a-z]{2}(-[a-z]{2})?\/?)?(index\.html?)?$/i.test(href.pathname);
    } catch {
      return false;
    }
  };

  // The head and the links: icons, social preview images, the manifest, the
  // site name, and app store and social media pages. Meta tags and JSON-LD
  // first, the links on the page as the fallback.
  const icons = [];
  const images = [];
  const links = [];
  let manifest = "";
  let siteName = "";
  let title = "";
  let challengeScript = false;
  let description = "";
  let ogDescription = "";
  const addImage = (property, raw) => {
    const url = absoluteUrl(raw, base);
    if (url && !images.some((image) => image.url === url)) images.push({ property, url });
  };
  const addLink = (raw, from) => {
    const link = brandLink(raw, base);
    if (link && !links.some((known) => known.url === link.url)) links.push({ ...link, from });
  };
  const ldJson = [];
  names.forEach((name, i) => {
    const a = attrs(i);
    if (name === "LINK") {
      const rel = (a.rel || "").toLowerCase();
      const href = absoluteUrl(a.href, base);
      if (!href) return;
      if (/(^|\s)(icon|apple-touch-icon(-precomposed)?|mask-icon)(\s|$)/.test(rel)) {
        icons.push({ rel, href, sizes: a.sizes || "" });
      }
      if (/(^|\s)manifest(\s|$)/.test(rel)) manifest = href;
    } else if (name === "META") {
      const key = (a.property || a.name || a.itemprop || "").toLowerCase();
      const content = a.content || "";
      if (key === "og:site_name") siteName = content;
      if (key === "description" && !description) description = content.replace(/\s+/g, " ").trim();
      if (key === "og:description" && !ogDescription) ogDescription = content.replace(/\s+/g, " ").trim();
      if (IMAGE_META.has(key)) addImage(key, content);
      const appId = (content.match(/app-id=([\w.]+)/) || [])[1] || content.trim();
      if ((key === "apple-itunes-app" || key === "al:ios:app_store_id" || key === "twitter:app:id:iphone") && /^\d{5,}$/.test(appId)) {
        addLink(`https://apps.apple.com/app/id${appId}`, "meta");
      }
      if ((key === "google-play-app" || key === "al:android:package" || key === "twitter:app:id:googleplay") && /^[\w.]+\.[\w.]+$/.test(appId)) {
        addLink(`https://play.google.com/store/apps/details?id=${appId}`, "meta");
      }
    } else if (name === "#text" && parents[i] >= 0 && names[parents[i]] === "SCRIPT") {
      if (/ld\+json/i.test(attrs(parents[i]).type || "")) ldJson.push(str((nodes.nodeValue || [])[i]));
    } else if (name === "#text" && parents[i] >= 0 && names[parents[i]] === "TITLE" && !title) {
      title = str((nodes.nodeValue || [])[i]).trim();
    } else if ((name === "SCRIPT" || name === "IFRAME") && CHALLENGE_SRC.test(a.src || "")) {
      challengeScript = true;
    }
  });
  const walkLd = (value) => {
    if (Array.isArray(value)) return value.forEach(walkLd);
    if (!value || typeof value !== "object") return;
    const logo = value.logo;
    if (typeof logo === "string") addImage("ld+json:logo", logo);
    else if (logo && typeof logo === "object") addImage("ld+json:logo", logo.url || logo.contentUrl);
    for (const same of [].concat(value.sameAs || [])) addLink(same, "ld+json");
    for (const key of ["@graph", "publisher", "brand", "organization", "author"]) walkLd(value[key]);
  };
  for (const text of ldJson) {
    try {
      walkLd(JSON.parse(text));
    } catch {
      // Broken JSON-LD carries nothing usable.
    }
  }
  names.forEach((name, i) => {
    if (name !== "A") return;
    let from = "page";
    for (let p = parents[i]; p >= 0; p = parents[p]) {
      if (names[p] === "FOOTER") from = "footer";
      else if (names[p] === "HEADER" || names[p] === "NAV") from = "header";
      else continue;
      break;
    }
    addLink(attrs(i).href, from);
  });
  if (icons.length === 0) {
    const fallback = absoluteUrl("/favicon.ico", base);
    if (fallback) icons.push({ rel: "default", href: fallback, sizes: "" });
  }

  const brand = brandTokens(pageUrl, `${siteName} ${alsoNamed}`);

  // Every ancestor of an <img> or <svg>: a "logo" wrapper around one is
  // captured through the image, not a second time as itself.
  const wrapsImage = new Set();
  const isMarkName = (name) => name === "IMG" || name === "svg";
  names.forEach((name, i) => {
    if (!isMarkName(name)) return;
    for (let p = parents[i]; p >= 0 && !wrapsImage.has(p); p = parents[p]) wrapsImage.add(p);
  });
  const insideSvg = (i) => {
    for (let p = parents[i]; p >= 0; p = parents[p]) if (names[p] === "svg") return true;
    return false;
  };
  const inside = ([x, y, w, h], [bx, by, bw, bh], share) => {
    const cut = Math.max(0, Math.min(x + w, bx + bw) - Math.max(x, bx)) * Math.max(0, Math.min(y + h, by + bh) - Math.max(y, by));
    return cut >= share * w * h;
  };

  const candidates = [];
  names.forEach((name, i) => {
    const own = attrs(i);
    const hint = `${own.class || ""} ${own.id || ""}`;
    let kind = "";
    if (name === "IMG") kind = "img";
    else if (name === "svg" && !insideSvg(i)) kind = "svg";
    else if (!isMarkName(name) && !wrapsImage.has(i) && hasToken(hint, MARK_TOKEN)) kind = "css";
    if (!kind) return;
    const box = boxOf(i);
    if (!box) return;
    const [x, y, w, h] = box;
    if (!(w >= 12 && h >= 10 && w <= 800 && h <= 400)) return;
    // Off the page (a drawer parked at -9999 px) or not drawn. A closed menu
    // fades its panel to opacity 0 (not inherited, so every element up the
    // tree is checked) or folds it into a box that clips it.
    if (x < 0 || y < 0 || x + w > pageWidth + 1 || y + h > pageHeight + 1) return;
    if (styleOf(i, 0) === "hidden") return;

    const src = kind === "img" ? currentSrc.get(i) || absoluteUrl(own.src, base) : "";
    let where = "page";
    let homeLink = kind === "css" && name === "A" && isHomeHref(own.href);
    let linkLabel = "";
    let thirdParty = THIRD_PARTY.test(`${hint} ${pathOf(src)}`);
    for (let p = i, depth = 0; p >= 0 && depth < 60; p = parents[p], depth++) {
      if (p !== i) {
        const parentBox = boxOf(p);
        if (parseFloat(styleOf(p, 1)) === 0) return;
        // <html> and <body> scroll the page rather than clip it, even with
        // overflow-x: hidden and a viewport-high box.
        const clips = names[p] !== "HTML" && names[p] !== "BODY" && [styleOf(p, 3), styleOf(p, 4)].some((v) => v && v !== "visible");
        if (clips && parentBox && !inside(box, parentBox, 0.8)) return;
        const a = attrs(p);
        const parentHint = `${a.class || ""} ${a.id || ""}`;
        const role = (a.role || "").toLowerCase();
        // The page header is a bar at the top, the page footer the block that
        // ends the page: a <header> around a hero or an article is neither.
        if (where === "page" && parentBox) {
          const [, by, , bh] = parentBox;
          const headerLike = names[p] === "HEADER" || names[p] === "NAV" || role === "banner" || role === "navigation" || hasToken(parentHint, HEADER_TOKEN);
          const footerLike = names[p] === "FOOTER" || role === "contentinfo" || hasToken(parentHint, FOOTER_TOKEN);
          if (headerLike && by <= 120 && bh <= 400) where = "header";
          else if (footerLike && by + bh >= pageHeight * 0.9 - 50) where = "footer";
        }
        if (names[p] === "A" && !linkLabel) {
          linkLabel = `${a["aria-label"] || ""} ${a.title || ""} `;
          homeLink = homeLink || isHomeHref(a.href);
        }
        if (depth < 8 && THIRD_PARTY.test(parentHint)) thirdParty = true;
      }
    }
    if (thirdParty) return;

    // The brand's name counts in what a reader is told (alt, title, label)
    // and in the file's name; class names often carry a site-wide prefix.
    // Not in the folders above the file: a product page under /things/
    // keeps every picture there, the press logos too, and Apple's logo came
    // back as a Things logo.
    const labels = `${own.alt || ""} ${own.title || ""} ${own["aria-label"] || ""}`;
    const named = `${labels} ${pathOf(src).split("/").pop()} ${linkLabel}`.toLowerCase();
    const brandHit = brand.some((token) => named.includes(token));
    const logoHit = /logo|brand/i.test(`${labels} ${hint} ${pathOf(src)}`);
    const keep =
      where === "header" ? homeLink || brandHit || logoHit
      : where === "footer" ? homeLink || brandHit
      : brandHit && logoHit;
    if (!keep) return;
    // The colour it sits on as CSS has it: the first element up from it with
    // a background, white when none has one. The cut's own pixels have the
    // last word (captureLogos): CSS says white under a logo on a hero photo.
    let background = "";
    for (let p = i; p >= 0 && !background; p = parents[p]) background = cssColorToHex(styleOf(p, 2));
    candidates.push({ kind, where, x, y, w, h, src, alt: own.alt || "", background: background || "#ffffff", backendNodeId: (nodes.backendNodeId || [])[i] });
  });

  // Header marks first, then the footer, then the page, each top to bottom.
  // One file per image, even when a page loads it twice under a build hash
  // (acme-logo.IozOd3nk.png is acme-logo.png), and one per drawn logo (a
  // "brand" link and the "brand" text inside it).
  const rank = { header: 0, footer: 1, page: 2 };
  candidates.sort((a, b) => rank[a.where] - rank[b.where] || a.y - b.y || a.x - b.x);
  const seen = new Set();
  const marks = [];
  for (const c of candidates) {
    const key =
      c.kind === "img" && c.src
        ? pathOf(c.src).split("/").pop().replace(/\.[a-z0-9_-]{6,12}(?=\.[a-z0-9]+$)/i, "")
        : `${c.kind}:${c.where}:${Math.round(c.w)}x${Math.round(c.h)}`;
    if (seen.has(key)) continue;
    if (marks.some((m) => m.where === c.where && inside([c.x, c.y, c.w, c.h], [m.x - 1, m.y - 1, m.w + 2, m.h + 2], 1))) continue;
    seen.add(key);
    marks.push(c);
    if (marks.length >= LOGO_MAX) break;
  }
  const challenge = marks.length === 0 && (CHALLENGE_TITLE.test(title) || (challengeScript && pageHeight < 1200)) ? title || "a bot check" : "";
  return {
    marks,
    icons,
    images,
    manifest,
    links,
    siteName,
    title,
    description: description || ogDescription,
    challenge,
    brand: brandLook(names, parents, attrs, boxOf, styleOf, pageWidth, pageHeight),
    wordTargets: wordTargets(names, parents, attrs, boxOf, styleOf, nodes.backendNodeId || [], pageWidth, pageHeight),
  };
}

// The brand's look as the page draws it: the colours of its buttons and
// headings, of the links in its text, its header and footer backgrounds and
// its large surfaces, and its heading and body typefaces. Only solid colours
// count: a 10% tint behind a card is not a brand colour. Buttons and links
// count only in colour: white, grey and black ones (a language switch,
// footer links) say nothing of the brand.
function solidHex(css) {
  const m = String(css || "").match(/rgba?\(\s*(\d+)[,\s]+(\d+)[,\s]+(\d+)(?:[,\s/]+([\d.]+)(%?))?/);
  if (!m) return "";
  if (m[4] !== undefined && parseFloat(m[4]) / (m[5] ? 100 : 1) < 0.9) return "";
  return "#" + [m[1], m[2], m[3]].map((v) => Number(v).toString(16).padStart(2, "0")).join("");
}

const colourful = (hex) => {
  const [r, g, b] = [1, 3, 5].map((k) => parseInt(hex.slice(k, k + 2), 16));
  return Math.max(r, g, b) - Math.min(r, g, b) >= 40;
};

// A button in the brand's color, from 40 px wide: a round search button in
// that color is often the only place a site shows it besides its logo.
function isBrandButton(name, role, background, w, h) {
  return (name === "BUTTON" || name === "A" || role === "button") && Boolean(background) && colourful(background) && w >= 40 && w <= 600 && h >= 24 && h <= 120;
}

function brandLook(names, parents, attrs, boxOf, styleOf, pageWidth, pageHeight) {
  const tally = new Map();
  const add = (role, hex, weight = 1) => {
    if (!hex) return;
    if (!tally.has(role)) tally.set(role, new Map());
    tally.get(role).set(hex, (tally.get(role).get(hex) || 0) + weight);
  };
  const family = (css) => String(css || "").split(",")[0].replace(/["']/g, "").trim();
  const fonts = {};
  let header = "";
  let footer = "";
  names.forEach((name, i) => {
    const box = boxOf(i);
    if (name === "#text" || !box || !(box[2] > 0 && box[3] > 0)) return;
    if (styleOf(i, 0) === "hidden" || parseFloat(styleOf(i, 1)) === 0) return;
    const [, y, w, h] = box;
    const a = attrs(i);
    const role = (a.role || "").toLowerCase();
    const background = solidHex(styleOf(i, 2));
    if (name === "H1" || name === "H2") {
      add("heading", solidHex(styleOf(i, 5)));
      if (!fonts.heading) fonts.heading = family(styleOf(i, 6));
    }
    if (name === "P" && !fonts.body) fonts.body = family(styleOf(i, 6));
    if (isBrandButton(name, role, background, w, h)) add("button", background);
    const linkColour = name === "A" && !background && /^(P|LI)$/.test(names[parents[i]] || "") ? solidHex(styleOf(i, 5)) : "";
    if (linkColour && colourful(linkColour)) add("link", linkColour);
    if (background && w >= pageWidth * 0.5 && h >= 80) add("surface", background, w * h);
    if (background && !header && (name === "HEADER" || role === "banner") && y <= 120 && h <= 400) header = background;
    if (background && (name === "FOOTER" || role === "contentinfo") && y + h >= pageHeight * 0.9 - 50) footer = background;
  });
  const top = (role, n) => [...(tally.get(role) || new Map()).entries()].sort((p, q) => q[1] - p[1]).slice(0, n).map(([hex]) => hex);
  const colors = [];
  const push = (role, hexes) => {
    for (const hex of hexes) if (hex && !colors.some((c) => c.hex === hex)) colors.push({ hex, role });
  };
  push("button", top("button", 2));
  push("heading", top("heading", 1));
  push("link", top("link", 1));
  push("header", [header]);
  push("footer", [footer]);
  push("surface", top("surface", 3));
  // The page's own ground: the solid color that covers most of it, when it
  // covers at least half. A page left on the browser's white has none, nor
  // has one whose largest colored area is a band across a white page. The
  // list above can file this color under the header or footer instead.
  const [ground] = [...(tally.get("surface") || new Map()).entries()].sort((p, q) => q[1] - p[1]);
  const background = ground && ground[1] >= pageWidth * pageHeight * 0.5 ? ground[0] : "";
  return { colors: colors.slice(0, 8), fonts, background };
}

// The page's own words, for copy that has to say what the product is: its
// headings in reading order (not the footer's column titles or a menu's)
// and what its filled buttons say, top of the page first. Only what a
// visitor can see counts, so a heading in a closed menu stays out. The
// snapshot picks the elements; their text is read as the page renders it
// (innerText), because a snapshot's text pieces lose the line breaks and the
// spaces between them.
function wordTargets(names, parents, attrs, boxOf, styleOf, backendIds, pageWidth, pageHeight) {
  const within = (i, test) => {
    for (let p = parents[i]; p >= 0; p = parents[p]) if (test(names[p], (attrs(p).role || "").toLowerCase())) return true;
    return false;
  };
  const inFooter = (i) => within(i, (name, role) => name === "FOOTER" || role === "contentinfo");
  const inChrome = (i) => within(i, (name, role) => name === "FOOTER" || name === "NAV" || role === "contentinfo" || role === "navigation");
  // A filled button: its own solid background, unlike what it sits on.
  const ground = (i) => {
    for (let p = parents[i]; p >= 0; p = parents[p]) {
      const hex = solidHex(styleOf(p, 2));
      if (hex) return hex;
    }
    return "#ffffff";
  };
  const visible = (i) => {
    const box = boxOf(i);
    if (!box || !(box[2] > 0 && box[3] > 0)) return false;
    const [x, y, w, h] = box;
    if (x + w <= 0 || y + h <= 0 || x >= pageWidth || y >= pageHeight) return false;
    for (let p = i, depth = 0; p >= 0 && depth < 60; p = parents[p], depth++) {
      if (styleOf(p, 0) === "hidden" || parseFloat(styleOf(p, 1)) === 0) return false;
    }
    return true;
  };
  const headings = [];
  const buttons = [];
  names.forEach((name, i) => {
    if (/^H[1-3]$/.test(name)) {
      if (headings.length < 30 && visible(i) && !inChrome(i)) headings.push({ kind: "heading", tag: name.toLowerCase(), backendNodeId: backendIds[i] });
      return;
    }
    const role = (attrs(i).role || "").toLowerCase();
    if (name !== "BUTTON" && name !== "A" && role !== "button") return;
    const box = boxOf(i);
    const fill = solidHex(styleOf(i, 2));
    if (!box || !fill || fill === ground(i) || !(box[2] >= 40 && box[2] <= 400 && box[3] >= 24 && box[3] <= 80)) return;
    if (buttons.length < 30 && visible(i) && !inFooter(i)) buttons.push({ kind: "cta", y: box[1], backendNodeId: backendIds[i] });
  });
  buttons.sort((a, b) => a.y - b.y);
  return [...headings, ...buttons];
}

// "Build faster Build faster": a heading that holds its words twice, one
// copy drawn and one for an effect or a screen reader, says them once.
function sayOnce(text) {
  const mid = (text.length - 1) / 2;
  return Number.isInteger(mid) && text[mid] === " " && text.slice(0, mid) === text.slice(mid + 1) ? text.slice(0, mid) : text;
}

const INNER_TEXT = `function () { return String(this.innerText || this.textContent || ""); }`;

async function readWords(cdp, targets) {
  const headings = [];
  const ctas = [];
  for (const target of targets) {
    let text = "";
    try {
      const { object } = await cdp.send("DOM.resolveNode", { backendNodeId: target.backendNodeId });
      if (!object || !object.objectId) continue;
      const { result } = await cdp.send("Runtime.callFunctionOn", { objectId: object.objectId, functionDeclaration: INNER_TEXT, returnByValue: true });
      text = sayOnce(String((result && result.value) || "").replace(/\s+/g, " ").trim()).slice(0, 200);
    } catch {
      // A node the page has replaced since the snapshot: its words are skipped.
      continue;
    }
    if (text.length < 2) continue;
    // A language switch ("EN", "pt-BR") is a button, not something to say.
    if (target.kind === "cta" && /^[a-z]{2}([-_][a-z]{2})?$/i.test(text)) continue;
    if (target.kind === "heading" && headings.length < 12 && !headings.some((h) => h.text === text)) headings.push({ tag: target.tag, text });
    if (target.kind === "cta" && ctas.length < 6 && !ctas.some((c) => c.toLowerCase() === text.toLowerCase())) ctas.push(text);
  }
  return { headings, ctas };
}

// The box where the mark is actually painted. Layout bounds ignore CSS
// transforms, so a logo inside a scaled product mockup was cut from the
// wrong place (the mockup's window buttons came back as "the logo"). When
// the node is gone by now (a header that re-creates its logo when the page
// returns to the top), the snapshot's layout box stands in.
async function paintedBox(cdp, mark, scrollY) {
  try {
    const { quads = [] } = await cdp.send("DOM.getContentQuads", { backendNodeId: mark.backendNodeId });
    if (quads.length > 0) {
      const xs = quads.flatMap((q) => [q[0], q[2], q[4], q[6]]);
      const ys = quads.flatMap((q) => [q[1], q[3], q[5], q[7]]);
      const box = { x: Math.min(...xs), y: Math.min(...ys) + scrollY, w: Math.max(...xs) - Math.min(...xs), h: Math.max(...ys) - Math.min(...ys) };
      return box.w >= 12 && box.h >= 10 ? box : null;
    }
  } catch {
    // A detached node: fall back to the layout box below.
  }
  return { x: mark.x, y: mark.y, w: mark.w, h: mark.h };
}

// The logo alone, as it stands once the page has settled. Before each
// capture the page's finite animations are finished (a header logo still
// fading in would be caught half see-through), and every element painting
// into the capture is hidden unless it is the mark, inside it, around it
// (its ancestors paint the ground), or a ground behind it (a hero image under
// a see-through header). Without that, the margin cut a line of text under
// one shop's logo in half, caught the tops of the buttons under another's,
// and an open popup's backdrop greyed a third one's header. What lies above
// the mark is found by stacking order, with every element made hit-testable
// for the moment it takes; everything is put back after the capture.
const ISOLATE_MARK = `function (r) {
  try {
    document.getAnimations().forEach(function (a) {
      var t = a.effect && a.effect.getComputedTiming();
      if (t && isFinite(t.endTime)) a.finish();
    });
  } catch (e) {}
  var mark = this;
  var related = function (el) { return el === mark || mark.contains(el) || el.contains(mark); };
  var sx = window.scrollX, sy = window.scrollY;
  var above = new Set();
  try {
    mark.scrollIntoView({ block: "center", inline: "center" });
    var m = mark.getBoundingClientRect();
    var probe = document.createElement("style");
    probe.textContent = "*{pointer-events:auto!important}";
    document.documentElement.appendChild(probe);
    var stack = document.elementsFromPoint(m.left + m.width / 2, m.top + m.height / 2);
    probe.remove();
    for (var i = 0; i < stack.length && !related(stack[i]); i++) above.add(stack[i]);
  } catch (e) {}
  window.scrollTo(sx, sy);
  var mb = mark.getBoundingClientRect();
  var rx = r.x - window.scrollX, ry = r.y - window.scrollY;
  var hidden = [];
  var all = document.querySelectorAll("body *");
  for (var j = 0; j < all.length; j++) {
    var el = all[j];
    if (related(el)) continue;
    var b = el.getBoundingClientRect();
    if (!b.width || !b.height || b.right <= rx || b.left >= rx + r.w || b.bottom <= ry || b.top >= ry + r.h) continue;
    var ground = b.left <= mb.left + 1 && b.top <= mb.top + 1 && b.right >= mb.right - 1 && b.bottom >= mb.bottom - 1;
    if (ground && !above.has(el)) continue;
    hidden.push([el, el.style.getPropertyValue("visibility"), el.style.getPropertyPriority("visibility")]);
  }
  hidden.forEach(function (h) { h[0].style.setProperty("visibility", "hidden", "important"); });
  window.__easybrandkitRestore = function () {
    hidden.forEach(function (h) {
      if (h[1]) h[0].style.setProperty("visibility", h[1], h[2]);
      else h[0].style.removeProperty("visibility");
    });
    window.__easybrandkitRestore = null;
  };
  return hidden.length;
}`;

async function isolateMark(cdp, mark, rect) {
  try {
    const { object } = await cdp.send("DOM.resolveNode", { backendNodeId: mark.backendNodeId });
    if (!object || !object.objectId) return false;
    await cdp.send("Runtime.callFunctionOn", {
      objectId: object.objectId,
      functionDeclaration: ISOLATE_MARK,
      arguments: [{ value: rect }],
      returnByValue: true,
    });
    await sleep(150);
    return true;
  } catch {
    return false;
  }
}

async function restorePage(cdp) {
  await cdp.send("Runtime.evaluate", { expression: "window.__easybrandkitRestore && window.__easybrandkitRestore()" }).catch(() => {});
}

// A PNG text chunk that names the file a site's logo cut. Tools reading the
// kit can tell a logo from an app icon by it: a small header logo cut at 8x
// can come out square and pass for one.
const CRC_TABLE = Array.from({ length: 256 }, (_, n) => {
  let c = n;
  for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
  return c >>> 0;
});
function crc32(buf) {
  let c = 0xffffffff;
  for (const byte of buf) c = CRC_TABLE[(c ^ byte) & 0xff] ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
}
function tagPng(png, keyword, text) {
  if (png.length < 33 || png.toString("ascii", 12, 16) !== "IHDR") return png;
  const data = Buffer.from(`${keyword}\0${text}`, "latin1");
  const chunk = Buffer.alloc(12 + data.length);
  chunk.writeUInt32BE(data.length, 0);
  chunk.write("tEXt", 4, "ascii");
  data.copy(chunk, 8);
  chunk.writeUInt32BE(crc32(chunk.subarray(4, 8 + data.length)), 8 + data.length);
  return Buffer.concat([png.subarray(0, 33), chunk, png.subarray(33)]);
}

// The mark's box where it comes to rest. ISOLATE_MARK finishes the page's
// finite animations before the capture, so a box measured before that can be
// stale: the box is measured after them too, and again until it holds still
// (a logo moved by script). One capture held only the left third of a header
// icon, at the capture's edge.
const FINISH_ANIMATIONS = `(() => {
  try {
    document.getAnimations().forEach((a) => {
      const t = a.effect && a.effect.getComputedTiming();
      if (t && isFinite(t.endTime)) a.finish();
    });
  } catch (e) {}
})()`;
async function restingBox(cdp, mark, scrollY) {
  await cdp.send("Runtime.evaluate", { expression: FINISH_ANIMATIONS }).catch(() => {});
  await sleep(150);
  let box = await paintedBox(cdp, mark, scrollY);
  for (let i = 0; box && i < 8; i++) {
    await sleep(200);
    const next = await paintedBox(cdp, mark, scrollY);
    if (!next) break;
    const still = ["x", "y", "w", "h"].every((k) => Math.abs(next[k] - box[k]) < 1);
    box = next;
    if (still) break;
  }
  return box;
}

// Each mark is brought to the middle of the screen and cut out there, as a
// visitor sees it. Cut from beyond the screen, the page is drawn on a screen
// as tall as itself, so a cookie bar fixed to the bottom lands on the
// footer, right over its logo. On the screen, whatever floats over the mark
// is in the frame and hidden with the rest.
const CENTER_MARK = `function () { this.scrollIntoView({ block: "center", inline: "center", behavior: "instant" }); }`;
async function bringIntoView(cdp, mark) {
  try {
    const { object } = await cdp.send("DOM.resolveNode", { backendNodeId: mark.backendNodeId });
    if (object && object.objectId) {
      await cdp.send("Runtime.callFunctionOn", { objectId: object.objectId, functionDeclaration: CENTER_MARK });
      await sleep(300);
    }
  } catch {
    // A detached node: its layout box is cut from wherever it was drawn.
  }
  return (await metrics(cdp)).scrollY;
}

// The logo as a vector file, run in the page. With no text, `this` is an
// inline <svg>: it is copied with the page's styles written onto every part
// as plain attributes (a class in the site's stylesheet, currentColor and
// CSS variables resolved to the colors they came to), without the parts the
// page hides, and with the symbols and gradients it uses from elsewhere in
// the page. With text, the text is the SVG file an <img> showed, kept as it
// is. Either way scripts, event handlers and embedded HTML are dropped and
// links are made absolute.
const SVG_FILE = `function (text, base) {
  var NS = "http://www.w3.org/2000/svg";
  var NOT_DRAWN = /^(defs|symbol|clippath|mask|pattern|marker|lineargradient|radialgradient|filter)$/;
  var INHERITED = ["fill", "fill-opacity", "fill-rule", "stroke", "stroke-width", "stroke-opacity", "stroke-linecap", "stroke-linejoin", "stroke-miterlimit", "stroke-dasharray", "stroke-dashoffset", "visibility", "clip-rule", "color", "font-family", "font-size", "font-weight", "font-style", "letter-spacing", "text-anchor", "dominant-baseline", "paint-order"];
  var OWN = { "opacity": "1", "clip-path": "none", "mask": "none", "filter": "none", "stop-color": "rgb(0, 0, 0)", "stop-opacity": "1", "mix-blend-mode": "normal" };
  var local = function (v) { return String(v).replace(/url\\((["']?)[^"')]*#([^"')]+)\\1\\)/g, "url(#$2)"); };
  var parts = function (el) { return [el].concat([].slice.call(el.getElementsByTagName("*"))); };
  var root;
  if (typeof text === "string") {
    var doc = new DOMParser().parseFromString(text, "image/svg+xml");
    root = doc.documentElement;
    if (!root || root.namespaceURI !== NS || doc.getElementsByTagName("parsererror").length) return "";
  } else {
    var source = this;
    if (!source || source.namespaceURI !== NS) return "";
    base = document.baseURI;
    root = source.cloneNode(true);
    var from = parts(source);
    var to = parts(root);
    var unused = function (el) {
      for (var p = el.parentNode; p && p !== source; p = p.parentNode) if (NOT_DRAWN.test(String(p.localName).toLowerCase())) return true;
      return false;
    };
    // Each part's look goes on as plain attributes (fill="#f7f8f8"), which
    // tools reading SVG outside a browser understand. A style attribute over
    // fill="currentColor" left one importer guessing, and Linear's white logo
    // came out black. The root says where it differs from the SVG defaults,
    // a group where it differs from its parent, and every shape carries its
    // own fill and stroke, for readers that skip what the root passes down.
    var DRAWN = /^(path|rect|circle|ellipse|line|polyline|polygon|text|tspan|textpath|use)$/;
    var PAINT = /^(fill|stroke)/;
    var INITIAL = { "fill": "rgb(0, 0, 0)", "fill-opacity": "1", "fill-rule": "nonzero", "stroke": "none", "stroke-width": "1px", "stroke-opacity": "1", "stroke-linecap": "butt", "stroke-linejoin": "miter", "stroke-miterlimit": "4", "stroke-dasharray": "none", "stroke-dashoffset": "0px", "visibility": "visible", "clip-rule": "nonzero", "font-style": "normal", "font-weight": "400", "font-size": "16px", "letter-spacing": "normal", "text-anchor": "start", "dominant-baseline": "auto", "paint-order": "normal" };
    var TYPE = /^(font-|letter-spacing|text-anchor|dominant-baseline)/;
    var hex = function (v) {
      var m = /^rgb\\((\\d+), (\\d+), (\\d+)\\)$/.exec(v);
      return m ? "#" + [m[1], m[2], m[3]].map(function (n) { return ("0" + Number(n).toString(16)).slice(-2); }).join("") : v;
    };
    var hasText = source.getElementsByTagName("text").length > 0;
    var gone = [];
    for (var i = 0; i < from.length; i++) {
      var cs = getComputedStyle(from[i]);
      if (i > 0 && cs.display === "none" && !unused(from[i])) { gone.push(to[i]); continue; }
      var up = i > 0 ? getComputedStyle(from[i].parentNode) : null;
      var look = {};
      var drawn = i > 0 && DRAWN.test(String(from[i].localName).toLowerCase());
      INHERITED.forEach(function (prop) {
        var v = cs.getPropertyValue(prop);
        if (!v || (TYPE.test(prop) && !hasText)) return;
        var differs = drawn && PAINT.test(prop) ? INITIAL[prop] !== v : up ? up.getPropertyValue(prop) !== v : prop === "color" || INITIAL[prop] !== v;
        if (differs) look[prop] = v;
      });
      Object.keys(OWN).forEach(function (prop) {
        var v = cs.getPropertyValue(prop);
        if (v && v !== OWN[prop]) look[prop] = v;
      });
      // What the page set (a class, fill="currentColor", fill="var(--text)")
      // is replaced by what it came to.
      INHERITED.concat(Object.keys(OWN)).forEach(function (prop) { to[i].removeAttribute(prop); });
      [].slice.call(to[i].attributes).forEach(function (at) {
        if (at.value.indexOf("var(") !== -1) to[i].removeAttribute(at.name);
      });
      to[i].removeAttribute("style");
      Object.keys(look).forEach(function (prop) {
        var v = hex(local(look[prop]));
        if (prop === "mix-blend-mode") to[i].setAttribute("style", prop + ":" + v);
        else to[i].setAttribute(prop, v);
      });
    }
    gone.forEach(function (el) { if (el.parentNode) el.parentNode.removeChild(el); });
    var box = source.getBoundingClientRect();
    if (!root.getAttribute("viewBox")) root.setAttribute("viewBox", "0 0 " + box.width + " " + box.height);
    root.setAttribute("width", String(Math.round(box.width * 100) / 100));
    root.setAttribute("height", String(Math.round(box.height * 100) / 100));
    var defs = null;
    for (var round = 0; round < 5; round++) {
      var wanted = [];
      parts(root).forEach(function (el) {
        [].slice.call(el.attributes).forEach(function (at) {
          if (/(^|:)href$/.test(at.name) && at.value.charAt(0) === "#") wanted.push(at.value.slice(1));
          at.value.replace(/url\\(#([^)]+)\\)/g, function (all, id) { wanted.push(id); return all; });
        });
      });
      var added = false;
      wanted.forEach(function (id) {
        if (parts(root).some(function (el) { return el.getAttribute("id") === id; })) return;
        var used = document.getElementById(id);
        if (!used || used.namespaceURI !== NS) return;
        if (!defs) { defs = document.createElementNS(NS, "defs"); root.insertBefore(defs, root.firstChild); }
        defs.appendChild(used.cloneNode(true));
        added = true;
      });
      if (!added) break;
    }
  }
  parts(root).forEach(function (el) {
    var name = String(el.localName).toLowerCase();
    if (/^(script|foreignobject|iframe|object|embed|audio|video|canvas)$/.test(name) || (name === "style" && typeof text !== "string")) {
      if (el.parentNode) el.parentNode.removeChild(el);
      return;
    }
    [].slice.call(el.attributes).forEach(function (at) {
      if (/^on/i.test(at.name)) { el.removeAttribute(at.name); return; }
      if (!/(^|:)href$/.test(at.name) || at.value.charAt(0) === "#") return;
      if (/^\\s*(javascript|vbscript):/i.test(at.value)) { el.removeAttribute(at.name); return; }
      try { at.value = new URL(at.value, base).href; } catch (e) {}
    });
  });
  return new XMLSerializer().serializeToString(root);
}`;

// The SVG file an <img> showed, as the browser loaded it: no second request,
// and nothing fetched from here at an address the page gave. "" when the
// image is not an SVG file or its text is gone.
async function svgSource(cdp, src) {
  const data = String(src || "").match(/^data:image\/svg\+xml(;[^,]*)?,(.*)$/is);
  try {
    if (data) return /;base64/i.test(data[1] || "") ? Buffer.from(data[2], "base64").toString("utf8") : decodeURIComponent(data[2]);
    if (!/\.svg$/.test(pathOf(src))) return "";
    const { frameTree } = await cdp.send("Page.getFrameTree");
    const { content = "", base64Encoded } = await cdp.send("Page.getResourceContent", { frameId: frameTree.frame.id, url: src });
    return base64Encoded ? Buffer.from(content, "base64").toString("utf8") : content;
  } catch {
    return "";
  }
}

// Writes the mark's vector as file in dir when the page draws it as SVG (an
// inline <svg>, or an <img> of an SVG file). The file name, or "".
const SVG_LIMIT = 2_000_000;
async function saveVector(cdp, mark, dir, file) {
  if (mark.kind !== "svg" && mark.kind !== "img") return "";
  try {
    const text = mark.kind === "img" ? await svgSource(cdp, mark.src) : null;
    if (text === "" || (text && text.length > SVG_LIMIT)) return "";
    const { object } = await cdp.send("DOM.resolveNode", { backendNodeId: mark.backendNodeId });
    if (!object || !object.objectId) return "";
    const { result } = await cdp.send("Runtime.callFunctionOn", {
      objectId: object.objectId,
      functionDeclaration: SVG_FILE,
      arguments: [{ value: text }, { value: mark.src || "" }],
      returnByValue: true,
    });
    const svg = String((result && result.value) || "");
    if (!svg.startsWith("<svg") || svg.length > SVG_LIMIT) return "";
    fs.writeFileSync(path.join(dir, file), svg + "\n");
    return file;
  } catch {
    return "";
  }
}

// Each mark with a margin of its real background, scaled so the short side
// reaches 240 px and the long side about 1000 px (at most 8x). The files are
// logo-01.png, logo-02.png … in dir, in the order of the marks, with
// logo-01.svg next to a mark the page draws as SVG.
async function captureLogos(cdp, marks, dir, pageWidth, pageHeight) {
  const written = [];
  await cdp.send("DOM.getDocument", { depth: 0 });
  for (const mark of marks) {
    const scrollY = await bringIntoView(cdp, mark);
    const box = await restingBox(cdp, mark, scrollY);
    if (!box) continue;
    const x = Math.max(0, box.x - LOGO_MARGIN);
    const y = Math.max(0, box.y - LOGO_MARGIN);
    const width = Math.min(pageWidth - x, box.w + 2 * LOGO_MARGIN);
    const height = Math.min(pageHeight - y, box.h + 2 * LOGO_MARGIN);
    if (!(width > 0 && height > 0)) continue;
    const scale = Math.min(8, Math.max(2, 240 / height, 1000 / width));
    const isolated = await isolateMark(cdp, mark, { x, y, w: width, h: height });
    let shot;
    try {
      shot = await capture(cdp, x, y, width, height, scale);
    } finally {
      if (isolated) await restorePage(cdp);
    }
    const png = tagPng(Buffer.from(shot.data || "", "base64"), "Source", "easybrandkit logo");
    if (png.length < 33) continue;
    // What the cut sits on, read from its own pixels along the sides where
    // the margin is whole. A mark in the page body on a picture is an event's
    // or a campaign's lockup (Stripe Sessions, white over a photo), not the
    // brand's logo. A header or footer logo over a hero picture stays, but
    // the color that is not the ground could be the picture's as well as
    // the logo's, so it gives no logo color.
    const ground = groundOf(png, Math.round(4 * scale), {
      top: box.y - LOGO_MARGIN >= 0,
      left: box.x - LOGO_MARGIN >= 0,
      bottom: box.y + box.h + LOGO_MARGIN <= pageHeight,
      right: box.x + box.w + LOGO_MARGIN <= pageWidth,
    });
    const onPicture = Boolean(ground && !ground.solid);
    if (onPicture && mark.where === "page") continue;
    const background = ground ? ground.hex : mark.background;
    const color = onPicture ? "" : logoInk(png, background);
    const file = `logo-${String(written.length + 1).padStart(2, "0")}.png`;
    fs.writeFileSync(path.join(dir, file), png);
    written.push({
      file,
      svg: await saveVector(cdp, mark, dir, file.replace(/\.png$/, ".svg")),
      where: mark.where,
      kind: mark.kind,
      background,
      onPicture,
      width: png.readUInt32BE(16),
      height: png.readUInt32BE(20),
      color,
      src: mark.src,
      alt: mark.alt,
    });
  }
  return written;
}

// The pixels of a PNG as Chrome writes it: 8-bit RGB or RGBA, not
// interlaced. Null for anything else.
function decodePng(png) {
  let pos = 8;
  let width = 0;
  let height = 0;
  let channels = 0;
  const idat = [];
  while (pos + 8 <= png.length) {
    const len = png.readUInt32BE(pos);
    const type = png.toString("ascii", pos + 4, pos + 8);
    const data = png.subarray(pos + 8, pos + 8 + len);
    if (type === "IHDR") {
      if (data[8] !== 8 || data[12] !== 0 || (data[9] !== 2 && data[9] !== 6)) return null;
      width = data.readUInt32BE(0);
      height = data.readUInt32BE(4);
      channels = data[9] === 6 ? 4 : 3;
    } else if (type === "IDAT") idat.push(data);
    pos += 12 + len;
  }
  if (!width || !height || !idat.length) return null;
  const raw = zlib.inflateSync(Buffer.concat(idat));
  const stride = width * channels;
  const pixels = Buffer.alloc(height * stride);
  for (let y = 0; y < height; y++) {
    const filter = raw[y * (stride + 1)];
    for (let x = 0; x < stride; x++) {
      const v = raw[y * (stride + 1) + 1 + x];
      const a = x >= channels ? pixels[y * stride + x - channels] : 0;
      const b = y > 0 ? pixels[(y - 1) * stride + x] : 0;
      const c = x >= channels && y > 0 ? pixels[(y - 1) * stride + x - channels] : 0;
      let p = v;
      if (filter === 1) p = v + a;
      else if (filter === 2) p = v + b;
      else if (filter === 3) p = v + ((a + b) >> 1);
      else if (filter === 4) {
        const pa = Math.abs(b - c);
        const pb = Math.abs(a - c);
        const pc = Math.abs(a + b - 2 * c);
        p = v + (pa <= pb && pa <= pc ? a : pb <= pc ? b : c);
      }
      pixels[y * stride + x] = p & 0xff;
    }
  }
  return { width, height, pixel: (x, y) => pixels.subarray(y * stride + x * channels, y * stride + x * channels + 3) };
}

// The color a logo is drawn in: the most common color of the cut that is
// not its background, read from the pixels, so a logo drawn in the brand's
// pink says pink whether it is an SVG fill, an image or a font. Edge pixels
// blend into the background and spread over many shades; the fill does not.
function logoInk(png, background) {
  let image;
  try {
    image = decodePng(png);
  } catch {
    return "";
  }
  if (!image) return "";
  const ground = [1, 3, 5].map((k) => parseInt(background.slice(k, k + 2), 16));
  const shades = new Map();
  let seen = 0;
  for (let y = 0; y < image.height; y += 2) {
    for (let x = 0; x < image.width; x += 2) {
      const [r, g, b] = image.pixel(x, y);
      seen++;
      if (Math.abs(r - ground[0]) + Math.abs(g - ground[1]) + Math.abs(b - ground[2]) < 60) continue;
      const key = ((r >> 4) << 8) | ((g >> 4) << 4) | (b >> 4);
      const shade = shades.get(key) || { n: 0, r: 0, g: 0, b: 0 };
      shade.n++;
      shade.r += r;
      shade.g += g;
      shade.b += b;
      shades.set(key, shade);
    }
  }
  let top = null;
  for (const shade of shades.values()) if (!top || shade.n > top.n) top = shade;
  if (!top || top.n < seen * 0.02) return "";
  return "#" + [top.r, top.g, top.b].map((v) => Math.round(v / top.n).toString(16).padStart(2, "0")).join("");
}

// What a cut sits on, from its pixels: the middle color of the band along
// its edges, and whether that band is one solid color (nine in ten of its
// pixels close to the middle one). A photo or a pattern is not. Only the
// sides given are read, since a mark at the page's edge has no margin there.
// Null when no side is left or the PNG cannot be read.
function groundOf(png, band, sides = { top: true, right: true, bottom: true, left: true }) {
  let image;
  try {
    image = decodePng(png);
  } catch {
    return null;
  }
  if (!image) return null;
  const { width, height } = image;
  const depth = Math.max(1, Math.min(band, Math.floor(Math.min(width, height) / 4)));
  const step = Math.max(1, Math.floor(Math.max(width, height) / 300));
  const samples = [];
  for (let k = 0; k < depth; k += Math.max(1, Math.floor(depth / 4))) {
    for (let x = 0; x < width; x += step) {
      if (sides.top) samples.push(image.pixel(x, k));
      if (sides.bottom) samples.push(image.pixel(x, height - 1 - k));
    }
    for (let y = depth; y < height - depth; y += step) {
      if (sides.left) samples.push(image.pixel(k, y));
      if (sides.right) samples.push(image.pixel(width - 1 - k, y));
    }
  }
  if (samples.length < 16) return null;
  const middle = [0, 1, 2].map((c) => samples.map((p) => p[c]).sort((p, q) => p - q)[samples.length >> 1]);
  const near = samples.filter((p) => Math.abs(p[0] - middle[0]) + Math.abs(p[1] - middle[1]) + Math.abs(p[2] - middle[2]) < 48).length;
  return { hex: "#" + middle.map((v) => v.toString(16).padStart(2, "0")).join(""), solid: near >= samples.length * 0.9 };
}

module.exports = { findLogos, captureLogos, readWords, brandLink, brandTokens, tagPng, logoInk, groundOf };
