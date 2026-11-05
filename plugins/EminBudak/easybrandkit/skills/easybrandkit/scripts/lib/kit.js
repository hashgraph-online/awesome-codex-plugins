"use strict";

// A brand kit from a website: the site is opened in a headless browser on a
// 1600x900 desktop screen, walked from top to bottom so its lazy parts
// render, and read once. What comes out, in one folder:
//
//   brand.json     everything below, for tools
//   BRAND.md       the same, for people and coding agents
//   _brand.yml     the name, logo, colors and fonts for Quarto and Shiny,
//                  in the brand.yml format
//   logo-01.png …  the site's own logos as it draws them, each cut on its
//                  real background (no transparency, short side >= 240 px),
//                  header marks first
//   logo-01.svg …  the same logo as a vector, when the page draws it as SVG
//   screen-01.png  the first screen as a visitor sees it, at 2x, without
//                  cookie bars and chat bubbles
//   card.png       the kit on one picture: logos, colors, fonts, first screen
//   appstore-icon.png, appstore-shot-01.png, x-profile.jpg …
//                  the app icon and screenshots from the app store listings
//                  the site links to, and its social profile pictures
//   FACTS.md, facts.json, pages/
//                  with --facts: the site's own claims with their pages
//                  (see facts.js)

const fs = require("fs");
const path = require("path");
const { launch, openPage, navigate } = require("./chrome");
const { metrics, walk, waitForContent, hideOverlays, resetPictureWait, capture } = require("./page");
const { findLogos, captureLogos, readWords } = require("./logos");
const { renderCard } = require("./card");
const { brandYml } = require("./brandyml");
const { readFactPages, writeFacts, removeFacts } = require("./facts");
const { classify, readSource } = require("./stores");
const { setTimeLimit, timeLeft, sleep } = require("./time");
const version = require("./version");

// Logos are read from the desktop layout: a narrow screen shows the mobile
// header, where the logo sits in a menu or is drawn differently.
const SCREEN = { width: 1600, height: 900 };
const MAX_SOURCES = 6;
// Store listings first: their icon and screenshots are the app as it is.
// Instagram, Facebook and TikTok serve nothing without a login, so they are
// not asked. One source of each kind: a page linking three YouTube videos
// has one channel.
const SOURCE_ORDER = ["appstore", "googleplay", "x", "youtube", "linkedin", "threads", "pinterest"];

// "acme.com", "www.acme.com/pricing" and "https://acme.com" all mean a web
// address; anything that is not http(s) is refused.
function normalizeUrl(raw) {
  const text = String(raw || "").trim();
  if (!text) throw new Error("Give a website address, for example: easybrandkit acme.com");
  let url;
  try {
    url = new URL(/^[a-z][a-z0-9+.-]*:\/\//i.test(text) ? text : `https://${text}`);
  } catch {
    throw new Error(`Not a web address: ${text}`);
  }
  if (!/^https?:$/.test(url.protocol) || !url.hostname) throw new Error(`Not a web address: ${text}`);
  return url.href;
}

// The brand lives on the product's home page (a language path such as /tr
// is fine). A blog, a help centre or a sub-page can wear another theme, with
// other colours and another logo: read from a blog post, a blue product came
// out orange. For such an address this gives the home page to read instead,
// and null when the address is a home page already.
function homePageOf(raw) {
  let page;
  try {
    page = new URL(raw);
  } catch {
    return null;
  }
  const side = /^(blog|docs|help|support|news|community)\./i.test(page.hostname);
  const home = page.pathname
    .split("/")
    .filter(Boolean)
    .every((part, i) => i < 2 && /^([a-z]{2}([-_][a-z]{2,4})?|home|index\.(html?|php))$/i.test(part));
  if (home && !side) return null;
  return `${page.protocol}//${side ? page.host.replace(/^[^.]+\./, "") : page.host}/`;
}

// The files an earlier kit lists, by name only: a brand.json someone edited
// cannot point the clean-up outside the folder.
function kitFiles(kit) {
  const files = [
    ...[].concat(kit.logos || []).flatMap((logo) => [logo && logo.file, logo && logo.svg]),
    ...[].concat(kit.screenshots || []).map((shot) => shot && shot.file),
    kit.card && kit.card.file,
    ...[].concat(kit.stores || []).flatMap((source) => [].concat((source && source.assets) || []).map((asset) => asset && asset.file)),
  ];
  return files.filter((file) => typeof file === "string" && file).map((file) => path.basename(file));
}

// The kit's folder: created when missing, reused when an earlier easybrandkit run
// made it (that kit's files are replaced), refused when it holds anything
// else, so a run never mixes into or overwrites someone's own files.
function prepareDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
  if (fs.readdirSync(dir).length === 0) return;
  let old = null;
  try {
    old = JSON.parse(fs.readFileSync(path.join(dir, "brand.json"), "utf8"));
  } catch {
    // Not a kit.
  }
  if (!old || old.version !== 1) {
    throw new Error(`${dir} is not empty and holds no earlier brand kit. Pick another folder with --out.`);
  }
  for (const file of [...kitFiles(old), "brand.json", "BRAND.md", "_brand.yml"]) fs.rmSync(path.join(dir, file), { force: true });
  removeFacts(dir);
}

// The site's name: og:site_name, else the title up to its first separator
// ("Acme | Payments for teams" is Acme), else the host name.
function brandName(siteName, title, url) {
  if (siteName.trim()) return siteName.trim();
  const first = String(title || "").split(/\s+[|·•:\u2013\u2014-]\s+/)[0].trim();
  if (first && first.length <= 40) return first;
  const label = new URL(url).hostname.replace(/^www\./, "").split(".")[0];
  return label.charAt(0).toUpperCase() + label.slice(1);
}

// The logo's own color joins the page's colors, right after the buttons,
// when it has a hue: many sites show their brand color only in the logo.
// A black or white wordmark says nothing the text and the header do not,
// and a color the page already lists (or one a shade from it) is not added.
function withLogoColor(colors, logos) {
  const rgb = (hex) => [1, 3, 5].map((k) => parseInt(hex.slice(k, k + 2), 16));
  const hued = (hex) => Math.max(...rgb(hex)) - Math.min(...rgb(hex)) >= 40;
  const ink = logos.map((logo) => logo.color).find((hex) => hex && hued(hex));
  if (!ink) return colors;
  const near = (hex) => rgb(hex).reduce((sum, v, k) => sum + Math.abs(v - rgb(ink)[k]), 0) < 24;
  if (colors.some((color) => near(color.hex))) return colors;
  const at = colors.findIndex((color) => color.role !== "button");
  const list = [...colors];
  list.splice(at === -1 ? list.length : at, 0, { hex: ink, role: "logo" });
  return list.slice(0, 8);
}

// The first screen as a visitor sees it, at 2x, without the cookie bar, chat
// bubble or promo box floating over it.
async function captureFirstScreen(cdp, dir) {
  await cdp.send("Runtime.evaluate", { expression: "window.scrollTo({ top: 0, left: 0, behavior: 'instant' })" }).catch(() => {});
  await sleep(600);
  const m = await metrics(cdp);
  await hideOverlays(cdp, m.width, m.viewportHeight);
  const shot = await capture(cdp, 0, 0, m.width, m.viewportHeight, 2, false);
  const png = Buffer.from(shot.data || "", "base64");
  if (png.length < 24) return [];
  fs.writeFileSync(path.join(dir, "screen-01.png"), png);
  return [{ file: "screen-01.png", width: png.readUInt32BE(16), height: png.readUInt32BE(20) }];
}

async function readPage(url, dir, log, alsoNamed = "", facts = false) {
  const chrome = await launch(SCREEN);
  let cdp;
  try {
    cdp = await openPage(chrome.base, SCREEN);
    resetPictureWait();
    log(`Opening ${url}`);
    const pageUrl = await navigate(cdp, url);
    // No overlay hiding before the logos: a fixed header that does not look
    // like page chrome would be hidden with the logo in it, and the cut-out
    // hides whatever paints over a mark anyway.
    const loaded = await waitForContent(cdp);
    log("Reading the page");
    await walk(cdp);
    // Back at the top, headers swap their scrolled style and re-render.
    await sleep(1_000);
    let m = await metrics(cdp);
    let found = await findLogos(cdp, pageUrl, m.width, m.height, alsoNamed);
    // A single-page app can still be drawing its header, and a lazy footer
    // logo loads only once the walk reaches it: when either one is missing,
    // give the page one more walk.
    const has = (where) => found.marks.some((mark) => mark.where === where);
    if (!(has("header") && has("footer")) && timeLeft() > 40_000) {
      await sleep(2_000);
      await walk(cdp);
      await sleep(1_000);
      m = await metrics(cdp);
      found = await findLogos(cdp, pageUrl, m.width, m.height, alsoNamed);
    }
    if (found.challenge) {
      throw new Error(`${pageUrl} answered with a bot check ("${found.challenge}") instead of its page, so no kit was made. Get the logo and colors from the site in a normal browser.`);
    }
    // The words first, while the page is as the snapshot saw it.
    const { headings, ctas } = await readWords(cdp, found.wordTargets);
    const text = { title: found.title, description: found.description, headings, ctas };
    log(`Cutting out ${found.marks.length === 1 ? "1 logo" : `${found.marks.length} logos`}`);
    const logos = await captureLogos(cdp, found.marks, dir, m.width, m.height);
    // A page still showing its loader has no logo yet. An empty kit would
    // pass for a site without one.
    if (!logos.length && !loaded) {
      throw new Error(`${pageUrl} still shows no content after 30 s, so nothing was read. Try again, or check the page in a browser.`);
    }
    log("Taking the first screen");
    const screenshots = await captureFirstScreen(cdp, dir);
    const name = brandName(found.siteName, found.title, pageUrl);
    const colors = withLogoColor(found.brand.colors, logos);
    log("Drawing the card");
    const card = await renderCard(chrome.base, { url: pageUrl, name, colors, fonts: found.brand.fonts, logos, screenshots }, dir).catch(() => null);
    // The claims last, from the page as the kit leaves it and the pages it
    // links to: the kit is made the same way with or without them.
    const factPages = facts ? await readFactPages(cdp, pageUrl, log).catch((err) => ({ pages: [], skipped: [{ role: "home", url: pageUrl, reason: String(err.message || err) }] })) : null;
    return { pageUrl, found, name, colors, text, logos, screenshots, card, factPages };
  } finally {
    if (cdp) cdp.close();
    await chrome.close();
  }
}

async function readSources(links, dir, log, skip = []) {
  const picked = [];
  for (const type of SOURCE_ORDER.filter((kind) => !skip.includes(kind))) {
    const source = links.filter((link) => link.type === type).map((link) => classify(link.url)).find(Boolean);
    if (source) picked.push(source);
  }
  if (!picked.length) return [];
  log(`Reading ${picked.length === 1 ? "1 store listing or profile" : `${Math.min(picked.length, MAX_SOURCES)} store listings and profiles`}`);
  return Promise.all(picked.slice(0, MAX_SOURCES).map((source) => readSource(source, dir)));
}

function writeMarkdown(kit, dir) {
  const lines = [`# ${kit.name} brand kit`, "", `Read from ${kit.url} on ${kit.capturedAt.slice(0, 10)} by easybrandkit ${kit.generator.split(" ")[1]}.`, ""];
  lines.push("## Colors", "");
  if (kit.colors.length) {
    lines.push("| Hex | Where the site uses it |", "| --- | --- |");
    const meaning = {
      button: "buttons",
      logo: "the logo itself",
      heading: "headings",
      link: "links in text",
      header: "header background",
      footer: "footer background",
      surface: "large background areas",
    };
    for (const color of kit.colors) lines.push(`| \`${color.hex}\` | ${meaning[color.role] || color.role} |`);
  } else {
    lines.push("No solid colors found.");
  }
  lines.push("", "## Fonts", "");
  lines.push(`- Headings: ${kit.fonts.heading || "not found"}`, `- Body text: ${kit.fonts.body || "not found"}`, "");
  const words = kit.text;
  if (words.title || words.description || words.headings.length || words.ctas.length) {
    lines.push("## Words on the page", "");
    if (words.title) lines.push(`- Title: ${words.title}`);
    if (words.description) lines.push(`- Description: ${words.description}`);
    for (const heading of words.headings) lines.push(`- ${heading.tag.toUpperCase()}: ${heading.text}`);
    if (words.ctas.length) lines.push(`- Buttons: ${words.ctas.map((cta) => `"${cta}"`).join(", ")}`);
    lines.push("");
  }
  lines.push("## Logos", "");
  if (kit.logos.length) {
    lines.push("| File | Where | Background | Size | Vector |", "| --- | --- | --- | --- | --- |");
    for (const logo of kit.logos) {
      const ground = logo.onPicture ? `a picture, mostly \`${logo.background}\`` : `\`${logo.background}\``;
      lines.push(`| ${logo.file} | ${logo.where} | ${ground} | ${logo.width}x${logo.height} | ${logo.svg || ""} |`);
    }
    lines.push("", "Each logo is cut from the page on the background it sits on, so it has no transparency. Use the files as they are; place a logo on its own background color or one close to it.");
    if (kit.logos.some((logo) => logo.onPicture)) lines.push("A logo on a picture was cut with part of that picture around it.");
    if (kit.logos.some((logo) => logo.svg)) lines.push("", "A .svg file is the same logo as the page draws it, as a vector with no background: use it to place the logo on another color or at a larger size.");
  } else {
    lines.push("No logo found on the page. The icons and images below may still show it.");
  }
  if (kit.screenshots.length) {
    lines.push("", "## First screen", "");
    for (const shot of kit.screenshots) lines.push(`- ${shot.file} (${shot.width}x${shot.height})`);
  }
  if (kit.card) lines.push("", "## Card", "", `- ${kit.card.file} (${kit.card.width}x${kit.card.height}): the kit on one picture`);
  const sources = kit.stores.filter((source) => source.ok);
  if (sources.length) {
    lines.push("", "## App stores and profiles", "");
    const label = { appstore: "App Store", googleplay: "Google Play" };
    for (const source of sources) {
      const files = source.assets.map((asset) => asset.file).join(", ");
      const title = [source.name, source.by && `by ${source.by}`].filter(Boolean).join(" ");
      lines.push(`- ${label[source.type] || source.type}: ${title || source.url}${files ? ` (${files})` : ""}`);
    }
  }
  const media = [...kit.icons.map((icon) => `- ${icon.rel}${icon.sizes ? ` ${icon.sizes}` : ""}: ${icon.href}`), ...kit.images.map((image) => `- ${image.property}: ${image.url}`)];
  if (media.length) lines.push("", "## Icons and preview images", "", ...media);
  if (kit.links.length) lines.push("", "## Links", "", ...kit.links.map((link) => `- ${link.type}: ${link.url}`));
  if (kit.notes.length) lines.push("", "## Notes", "", ...kit.notes.map((note) => `- ${note}`));
  fs.writeFileSync(path.join(dir, "BRAND.md"), lines.join("\n") + "\n");
}

// Stores and social networks wear their own brand. Read as a site, an App
// Store link gave a kit named "Today for iPhone" in Apple's colors, and an
// X profile would give X's. A store listing is read for what it is (icon,
// screenshots, the developer's website) and the brand comes from that
// website; a profile link is refused.
const PLATFORM_HOST = /^(www\.|m\.|mobile\.)?((apps|itunes)\.apple\.com|play\.google\.com|(x|twitter|instagram|facebook|fb|linkedin|youtube|tiktok|threads|pinterest)\.(com|net))$/i;

// The website a listing names, as the brand's page: as given (a product's
// own page on a maker's site is its brand), but the home page instead of a
// support or legal page, which Google Play often links.
function siteOfListing(raw) {
  try {
    const url = new URL(raw);
    if (!/^https?:$/.test(url.protocol) || PLATFORM_HOST.test(url.hostname)) return "";
    return /\/(help|support|contact|privacy|terms|faq|legal)\b/i.test(url.pathname) ? `${url.origin}/` : url.href;
  } catch {
    return "";
  }
}

// A failed run leaves nothing half made: its own files go, and so does the
// folder when this run created it.
const RUN_FILE = /^((logo|screen)-\d+\.png|logo-\d+\.svg|card\.png|(appstore|googleplay|x|youtube|linkedin|threads|pinterest)-(icon|profile|shot-\d+)\.(png|jpg|webp))$/;
function cleanUp(target, existed) {
  for (const file of fs.readdirSync(target)) if (RUN_FILE.test(file)) fs.rmSync(path.join(target, file), { force: true });
  if (!existed) {
    try {
      fs.rmdirSync(target);
    } catch {
      // Not empty: what is left there is not this run's.
    }
  }
}

async function makeKit(rawUrl, { dir, stores = true, facts = false, timeLimit = 120_000, log = () => {} } = {}) {
  setTimeLimit(timeLimit);
  const asked = normalizeUrl(rawUrl);
  const host = new URL(asked).hostname.toLowerCase();
  const listing = PLATFORM_HOST.test(host) ? classify(asked) : null;
  if (PLATFORM_HOST.test(host) && !(listing && (listing.type === "appstore" || listing.type === "googleplay"))) {
    throw new Error(`${asked} is a page on ${host.replace(/^(www|m|mobile)\./, "")}, not the brand's own site. Give the brand's website, or its App Store or Google Play listing.`);
  }
  const notes = [];
  const target = dir || (listing ? `easybrandkit-${listing.type}-${listing.id}` : `easybrandkit-${host.replace(/^www\./, "")}`);
  const existed = fs.existsSync(target);
  prepareDir(target);
  let given = null;
  let read = null;
  try {
    let page = "";
    if (listing) {
      log(`Reading the ${listing.type === "appstore" ? "App Store" : "Google Play"} listing`);
      given = await readSource(listing, target);
      if (!given.ok) throw new Error(`${asked} could not be read: ${given.error}.`);
      page = siteOfListing(given.site || "");
      notes.push(
        page
          ? `${asked} is a store listing: its icon and screenshots come from the listing, the rest from the website it names, ${page}.`
          : `${asked} is a store listing that names no website, so only the listing was read: the kit has the app icon and screenshots but no logos, colors or fonts. Give the product's website for those.`,
      );
    } else {
      const home = homePageOf(asked);
      if (home) notes.push(`${asked} is not the home page, so ${home} was read instead: the home page carries the brand's own header and colors.`);
      page = home || asked;
    }
    // The app's own name, up to a tagline ("Duolingo: Learn Languages").
    const appName = given ? String(given.name || "").split(/\s*[:|\u2013\u2014]\s*|\s+-\s+/)[0] : "";
    if (page) read = await readPage(page, target, log, appName, facts);
  } catch (err) {
    cleanUp(target, existed);
    throw err;
  }
  const found = read ? read.found : { brand: { fonts: {} }, icons: [], images: [], manifest: "", links: [] };
  if (read && !read.logos.length) notes.push("No logo was found on the page itself.");
  if (facts && !read) notes.push("No facts were read: the listing names no website.");
  const others = stores && read ? await readSources(found.links, target, log, given ? [given.type] : []) : [];
  const sources = [...(given ? [given] : []), ...others];
  for (const source of others) {
    if (!source.ok) notes.push(`${source.url} could not be read: ${source.error}.`);
  }
  const kit = {
    version: 1,
    url: read ? read.pageUrl : asked,
    // A listing names the product the user pointed at; its maker's site can
    // carry the company's name instead.
    name: (given && given.name) || (read ? read.name : "App"),
    capturedAt: new Date().toISOString(),
    generator: `easybrandkit ${version}`,
    colors: read ? read.colors : [],
    fonts: found.brand.fonts,
    text: read ? read.text : { title: given.name || "", description: given.description || "", headings: [], ctas: [] },
    logos: read ? read.logos : [],
    screenshots: read ? read.screenshots : [],
    card: read ? read.card : null,
    icons: found.icons,
    images: found.images,
    manifest: found.manifest,
    links: found.links,
    stores: sources,
    notes,
  };
  fs.writeFileSync(path.join(target, "brand.json"), JSON.stringify(kit, null, 2) + "\n");
  writeMarkdown(kit, target);
  // The page's ground is not in brand.json: its list of colors can file
  // that color under the header or footer.
  fs.writeFileSync(path.join(target, "_brand.yml"), brandYml(kit, { background: found.brand.background || "", site: read ? read.pageUrl : "" }));
  const claims = facts && read ? writeFacts(target, { name: kit.name, site: kit.url, generator: kit.generator, ...read.factPages }) : null;
  return { dir: target, kit, facts: claims };
}

module.exports = { makeKit, normalizeUrl, homePageOf, siteOfListing, prepareDir, brandName };
