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
//   screen-01.png  the first screen at 2x, with what floats over it hidden
//                  (see page.js hideOverlays)
//   card.png       the kit on one picture: logos, colors, fonts, first screen
//   appstore-icon.png, appstore-shot-01.png, x-profile.jpg …
//                  the app icon and screenshots from the app store listings
//                  the site links to, and its social profile pictures
//   FACTS.md, facts.json, pages/
//                  with --facts: the site's own claims with their pages
//                  (see facts.js)
//
// The files are made in a part folder of the run's own and put in place only
// once the run has ended well, so a run that fails, is refused or is stopped
// leaves the folder as it was (see run.js).

const fs = require("fs");
const path = require("path");
const { launch, openPage, navigate, triedSoFar, triedNotes, refusedNotes, proxyNotes, takeMove, pageFailed, noKit } = require("./chrome");
const { metrics, walk, waitForContent, hideOverlays, resetPictureWait, capture } = require("./page");
const { findLogos, captureLogos, readWords } = require("./logos");
const { renderCard } = require("./card");
const { brandYml } = require("./brandyml");
const { readFactPages, writeFacts } = require("./facts");
const { classify, readSource } = require("./stores");
const { setTimeLimit, timeLeft, outOfTime, sleep } = require("./time");
const { SaveError, toldPlainly, removedFrom, startRun, discardRun, saveRun } = require("./run");
const { checkDir } = require("./folder");
const { guardFor, refusedAddresses, readUrl, notPublicByForm, interfacesUnread } = require("./address");
const { moreFiles } = require("./program");
const { plainText } = require("./text");
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
// address; anything that is not http(s) is refused, and so is one the URL
// parser here cannot read, as one whose host has a label of broken punycode
// (see address.js readUrl).
function normalizeUrl(raw) {
  const text = String(raw || "").trim();
  if (!text) throw new Error("Give a website address, for example: easybrandkit acme.com");
  const url = readUrl(/^[a-z][a-z0-9+.-]*:\/\//i.test(text) ? text : `https://${text}`);
  if (!url || !/^https?:$/.test(url.protocol) || !url.hostname) throw new Error(`Not a web address: ${text}`);
  return url.href;
}

// A blog or a help centre on a host of its own: a first label such as blog.
// with a site left after it. news.com is a site of its own, and so is
// support.co.uk, where what is left is a country's second level.
function sideSite(hostname) {
  if (!/^(blog|docs|help|support|news|community)\./i.test(hostname)) return false;
  const rest = hostname.split(".").filter(Boolean).slice(1);
  return rest.length >= 2 && !(rest.length === 2 && rest[1].length === 2 && /^(ac|co|com|edu|gov|net|or|org)$/i.test(rest[0]));
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
  const side = sideSite(page.hostname);
  const home = page.pathname
    .split("/")
    .filter(Boolean)
    .every((part, i) => i < 2 && /^([a-z]{2}([-_][a-z]{2,4})?|home|index\.(html?|php))$/i.test(part));
  if (home && !side) return null;
  return `${page.protocol}//${side ? page.host.replace(/^[^.]+\./, "") : page.host}/`;
}

// The kit's folder made ready for a kit written straight into it, as runs
// did up to 0.4.0: made when it is not there, refused as checkDir refuses
// it, and an earlier kit's own files removed, while the user's files stay.
// makeKit no longer calls it, since a run that then failed lost the earlier
// kit; it is kept for code that writes a kit itself. A folder under a kit
// file's name is not the kit's, and a pages that is not a folder is not
// looked into.
function prepareDir(dir) {
  const names = checkDir(dir);
  fs.mkdirSync(dir, { recursive: true });
  if (!names) return;
  const pages = fs.lstatSync(path.join(dir, "pages"), { throwIfNoEntry: false });
  const pagesFolder = Boolean(pages && pages.isDirectory());
  for (const name of names) {
    if (name.startsWith("pages/") && !pagesFolder) continue;
    const at = fs.lstatSync(path.join(dir, name), { throwIfNoEntry: false });
    if (at && !at.isDirectory()) fs.rmSync(path.join(dir, name), { force: true });
  }
  if (pagesFolder) {
    try {
      fs.rmdirSync(path.join(dir, "pages"));
    } catch {
      // Holding files that are not the kit's.
    }
  }
}

// What a logo's alt text names, without the word logo: "" when that leaves
// nothing, says where its link goes ("Back to the home page"), or is more
// than a name could be.
function logoName(alt) {
  const name = plainText(alt, 200)
    .replace(/(^|\s)logo(type)?(?=\s|$)/gi, " ")
    .trim();
  return name.length <= 40 && !/(^|\s)home( ?page)?(\s|$)/i.test(name) ? name : "";
}

// A part of a page's title that only says what kind of page it is, in the
// words sites give their menus and their home page: no brand is named that.
const PAGE_KIND = /^(home|home ?page|start|welcome|overview|features?|products?|solutions|pricing|plans|plans (and|&) pricing|prices|about|about us|company|team|careers|jobs|blog|news|press|docs|documentation|guides?|tutorials?|getting started|get started|quick ?start|introduction|downloads?|installation|help|help cent(er|re)|support|faqs?|contact|contact us|customers|case studies|testimonials|security|trust cent(er|re)|integrations|changelog|roadmap|log ?in|sign (in|up)|privacy|privacy policy|terms|terms of (service|use))$/i;

// The site's name: og:site_name, else the title up to its first separator
// ("Acme | Payments for teams" is Acme), else the host name. A page past the
// home page, read as given when the home page could not be read (deeper),
// can put its own subject first ("Features · Acme") or its brand ("PDF.js -
// Home", "Jekyll • Simple, blog-aware, static sites"). When its title has
// more than one part, its name is the part that its logo's alt text (logo)
// or its host names; else, of the parts that do not just say what kind of
// page it is, the one of fewest words, as a brand's name is shorter than a
// tagline next to it, and of two as short, the last, as most such titles
// put the page first. A title of one part comes after what that alt text
// names, and is not taken when it only says what kind of page it is.
function brandName(siteName, title, url, { deeper = false, logo = "" } = {}) {
  const own = plainText(siteName, 200);
  if (own) return own;
  const label = new URL(url).hostname.replace(/^www\./, "").split(".")[0];
  // By now one space stands between two words, whatever the page wrote.
  const parts = plainText(title).split(/ [|·•:\u2013\u2014-] /);
  const fits = (part) => Boolean(part) && part.length <= 40 && !(deeper && PAGE_KIND.test(part));
  const mark = deeper ? logoName(logo) : "";
  if (deeper && parts.length > 1) {
    const same = (a, b) => a.replace(/\s+/g, "").toLowerCase() === b.replace(/\s+/g, "").toLowerCase();
    const named = parts.find((part) => fits(part) && ((mark && same(part, mark)) || same(part, label)));
    if (named) return named;
    const words = (part) => part.split(" ").length;
    const shortest = parts.filter(fits).reduce((best, part) => (!best || words(part) <= words(best) ? part : best), "");
    if (shortest) return shortest;
  }
  if (mark) return mark;
  if (fits(parts[0])) return parts[0];
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

// The first screen at 2x, without what hideOverlays tells floats over it,
// as a cookie bar, a chat bubble or a promo box.
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

const BROWSER_GONE = "The browser was closed or crashed before the kit was done, so no kit was made. Try again.";

const errorPage = ({ status, unreachable, blank }) => status >= 400 || Boolean(unreachable) || blank;

// Throws when the tab does not show the site's own page: a bot check, whatever
// status it came with, a page the server answered with an error or the
// browser could not open, or a blank page it moved on to. A CDN's 5xx page or
// a site's own 404 has a logo, colors and fonts of its own, and a kit made
// from them would pass for the brand's.
function refuseOtherPage(cdp, url, pageUrl, challenge) {
  refuseMove(cdp, url);
  if (challenge) {
    throw pageFailed(`${pageUrl} answered with a bot check ("${challenge}") instead of its page, so no kit was made. Get the logo and colors from the site in a normal browser.`, `answered with a bot check ("${challenge}")`);
  }
  const { status, url: at, unreachable, blank } = cdp.answer;
  const led = at && at.split("#")[0] !== url.split("#")[0];
  const what = status >= 400 ? `${led ? `led to ${at}, which ` : ""}answered ${status}` : unreachable ? `led to ${unreachable}, which could not be opened` : blank ? "moved on to a blank page" : "";
  if (what) throw pageFailed(`${url} ${what}, so no kit was made.`, what);
}

// Throws when the tab's page has tried to move on to an address the run's
// rule refused, which the browser did not open (see chrome.js takeMove):
// the tab shows the browser's error page in its place.
function refuseMove(cdp, url) {
  const moved = takeMove(cdp);
  if (moved) throw pageFailed(`${url} led to ${moved.url}, which ${moved.why}, so no kit was made.`, `led to ${moved.url}, which ${moved.why}`);
}

// The https address read in the place of an http address on port 80 that
// gave no answer (see readPage): the same host and path on port 443. "" for
// any other address.
function httpsInPlace(raw) {
  const url = new URL(raw);
  if (url.protocol !== "http:" || url.port) return "";
  url.protocol = "https:";
  return url.href;
}

// alsoNamed: more names the brand goes by. deeper: the page is one past the
// home page, read as given when the home page could not be read. guard: the
// run's rule for the addresses it opens (see address.js), which a page the
// browser is to open is held to as well. browser: one started for it with
// that rule, which it closes as it would its own.
//
// An http address on port 80 that gives no answer in its time, or to which
// the browser makes no connection, is read over https on port 443 in its
// place, as Chrome's own move to https did before the kit turned it off
// (see chrome.js launch): a site that serves only https, with nothing on
// port 80, was told as down. That address is not the one asked for, so the
// run's rule holds it to port 443 and the public internet, and one the rule
// refuses is not tried. What it gives is told by both addresses (inPlace).
async function readPage(url, dir, log, { alsoNamed = "", facts = false, deeper = false, guard = guardFor(url), browser = null } = {}) {
  const chrome = browser || (await launch(SCREEN, { guard }));
  // A browser that has just not answered is not waited for again as it is
  // asked to quit.
  let unanswered = false;
  // The address asked for and what it did, once another is read in its
  // place.
  let inPlace = null;
  try {
    const cdp = await openPage(chrome, SCREEN);
    resetPictureWait();
    log(`Opening ${url}`);
    let pageUrl;
    try {
      pageUrl = await navigate(cdp, url);
    } catch (err) {
      const other = err.silent ? httpsInPlace(url) : "";
      if (!other || (await guard.judge(other))) throw err;
      inPlace = { url, said: err.silent };
      url = other;
      log(`Opening ${url}`);
      pageUrl = await navigate(cdp, url);
    }
    refuseMove(cdp, url);
    // An error page is not waited for or walked. A bot check can come with
    // an error status too, and is read like any page: it may let the browser
    // through to the site.
    if (errorPage(cdp.answer)) {
      const challenge = await metrics(cdp)
        .then((size) => findLogos(cdp, pageUrl, size.width, size.height, alsoNamed))
        .then((page) => page.challenge, () => "");
      if (!challenge) refuseOtherPage(cdp, url, pageUrl, "");
    }
    // No overlay hiding before the logos: a fixed header that does not look
    // like page chrome would be hidden with the logo in it, and the cut-out
    // hides whatever paints over a mark anyway.
    const content = await waitForContent(cdp);
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
    // Also a page that has moved on to such a page since it loaded.
    refuseOtherPage(cdp, url, pageUrl, found.challenge);
    // The words first, while the page is as the snapshot saw it.
    const { headings, ctas, unread } = await readWords(cdp, found.wordTargets);
    const text = { title: found.title, description: found.description, headings, ctas };
    log(`Cutting out ${found.marks.length === 1 ? "1 logo" : `${found.marks.length} logos`}`);
    const logos = await captureLogos(cdp, found.marks, dir, m.width, m.height);
    // A page still showing its loader has no logo yet. An empty kit would
    // pass for a site without one.
    if (!logos.length && content === "no time") {
      throw pageFailed(`${pageUrl} shows no content yet and the run has no time left to wait for it, so nothing was read. Try again, or give it more time with --timeout.`, "shows no content yet", true);
    }
    if (!logos.length && content === "loader") {
      throw pageFailed(`${pageUrl} still shows no content after 30 s, so nothing was read. Try again, or check the page in a browser.`, "still shows no content after 30 s");
    }
    log("Taking the first screen");
    const screenshots = await captureFirstScreen(cdp, dir);
    refuseOtherPage(cdp, url, pageUrl, "");
    const name = brandName(found.siteName, found.title, pageUrl, { deeper, logo: (logos.find((logo) => logo.alt) || {}).alt });
    const colors = withLogoColor(found.brand.colors, logos);
    log("Drawing the card");
    let cardError = "the browser gave back an empty picture";
    const card = await renderCard(chrome, { url: pageUrl, name, colors, fonts: found.brand.fonts, logos, screenshots }, dir).catch((err) => {
      // A file that cannot be written fails the run: what it has of the file
      // would otherwise go into the kit.
      if (err.syscall) throw err;
      const said = String(err.message || err);
      // A tab that did not answer once the run's time was up got a second at
      // most, which a busy machine can miss: more time is what helps then.
      const more = "Give it more time with --timeout";
      if (err.timedOut) cardError = outOfTime() ? `the run's time ran out. ${more}` : "the browser tab stopped answering";
      else if (err.closed) cardError = "the kit's connection to its tab closed";
      else if (err.browserSaid) cardError = `${said.charAt(0).toLowerCase()}${said.slice(1)}${err.outOfTime ? `. ${more}` : ""}`;
      else cardError = said;
      return null;
    });
    // The claims last, from the page as the kit leaves it and the pages it
    // links to: the kit is made the same way with or without them. A page
    // read as given is not filed as the home page.
    const role = deeper ? "given" : "home";
    const factPages = facts ? await readFactPages(cdp, pageUrl, log, { role, guard }).catch((err) => ({ pages: [], skipped: [{ role, url: pageUrl, reason: plainText(String(err.message || err)) }] })) : null;
    // A browser that was killed or crashed on the way has left the kit
    // without its card or its claims: the run fails, so that an earlier kit
    // in the folder stays as it was.
    if (!(await chrome.alive())) throw new Error(BROWSER_GONE);
    // The addresses that are not web addresses the pages tried to open, and
    // whether the browser runs in a sandbox of its own (see triedNotes),
    // those the run's rule did not let them open (see refusedNotes), and
    // the requests the kit's proxy refused while the kit read its pages
    // (see proxyNotes).
    const tried = await triedSoFar(cdp);
    const proxy = chrome.proxy || { refused: [], refusedMore: false };
    return { pageUrl, found, name, colors, text, wordsUnread: unread, logos, screenshots, card, cardError: card ? "" : cardError, factPages, tried, refused: cdp.refused || [], refusedMore: Boolean(cdp.refusedMore), asked: [...proxy.refused], askedMore: Boolean(proxy.refusedMore), sandboxed: Boolean(chrome.sandboxed), inPlace: inPlace && { ...inPlace, read: url } };
  } catch (err) {
    // A page read in the place of the address asked for that fails is told
    // with what that address did. A tab that stopped answering is told as
    // the tab's, in its own line's words and with its advice.
    const bothTold = (failed, { tab = false } = {}) => {
      if (!inPlace || !failed.pageFailed) return failed;
      const what = tab ? `${inPlace.said}, and the browser tab stopped answering while it read ${url}, tried in its place` : `${inPlace.said}, and ${url}, tried in its place, ${failed.pageFailed}`;
      const advice = failed.outOfTime ? " Try again, or give it more time with --timeout." : tab ? " Try again." : "";
      return pageFailed(`${inPlace.url} ${what}, so no kit was made.${advice}`, what, failed.outOfTime);
    };
    // A browser that ended on the way is told as that, whichever call was
    // waiting for it; a call it never answered is not told by its name in
    // the DevTools protocol. One that did not answer a wait for its tab has
    // just been waited for, and is not asked again. Once the run's time is
    // up, a second tells one that has ended from one that is slow.
    if (err.syscall) throw err;
    unanswered = Boolean(err.noAnswer || err.timedOut);
    if (!(await chrome.alive(err.noAnswer ? 0 : outOfTime() ? 1_000 : undefined))) throw new Error(BROWSER_GONE);
    if (err.browserSaid) throw noKit(err);
    if (err.timedOut) {
      const spent = outOfTime();
      throw bothTold(pageFailed(`The browser tab stopped answering while it read ${url}, so no kit was made. ${spent ? "Try again, or give it more time with --timeout." : "Try again."}`, "stopped answering", spent), { tab: true });
    }
    // An answer larger than the kit takes, as a very large page's snapshot.
    if (err.tooLarge) throw bothTold(pageFailed(`${url} is too large to read, so no kit was made.`, "is too large to read"));
    // The tab closed while the browser runs.
    if (err.closed) throw new Error(`The kit's connection to the browser tab closed while it read ${url}, so no kit was made. Try again.`);
    throw bothTold(err);
  } finally {
    await chrome.close({ hurry: unanswered });
  }
}

async function readSources(links, dir, log, skip = [], guard = null) {
  const picked = [];
  for (const type of SOURCE_ORDER.filter((kind) => !skip.includes(kind))) {
    const link = links.find((one) => one.type === type && classify(one.url));
    if (link) picked.push(classify(link.url));
  }
  if (!picked.length) return [];
  log(`Reading ${picked.length === 1 ? "1 store listing or profile" : `${Math.min(picked.length, MAX_SOURCES)} store listings and profiles`}`);
  return Promise.all(picked.slice(0, MAX_SOURCES).map((source) => readSource(source, dir, guard)));
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

// What a listing's pictures gave a kit, in words: said of a kit made from
// the listing alone, or the note for one whose website was read too.
function listingGave(assets) {
  const shots = assets.filter((asset) => asset.kind === "screenshot").length;
  const icon = assets.some((asset) => asset.kind === "icon");
  return {
    alone: [icon && "the app icon", shots && (shots === 1 ? "a screenshot" : "screenshots")].filter(Boolean).join(" and "),
    withSite: [icon && "icon", shots && (shots === 1 ? "screenshot" : "screenshots")].filter(Boolean).join(" and "),
    plural: shots > 1 || (icon && shots > 0),
  };
}

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

// The settings that name a proxy for programs to reach the web through, as
// a network that reaches the web only through one gives them, which the
// kit does not use: its browser goes through the kit's own proxy, which
// connects to each site itself, as the kit's own requests do (see proxy.js
// and address.js guardFor).
const PROXY_SETTINGS = ["https_proxy", "HTTPS_PROXY", "http_proxy", "HTTP_PROXY", "all_proxy", "ALL_PROXY"];

// What the address given did that such a network makes it do: no name is
// found, no connection is made, or no answer comes.
const UNREACHED = /^(could not be opened \(net::ERR_(NAME_NOT_RESOLVED|NAME_RESOLUTION_FAILED|CONNECTION_[A-Z_]+|ADDRESS_UNREACHABLE|INTERNET_DISCONNECTED|TIMED_OUT|EMPTY_RESPONSE)\)|did not answer|is on a host whose name could not be looked up)/;
const STORE_UNREACHED = /could not be looked up|did not answer in|connect E(CONNREFUSED|TIMEDOUT|HOSTUNREACH|NETUNREACH)/;

// A last line that says the address given could not be reached, with the
// word, when one of those settings is given, that the kit does not use the
// proxy it names; the setting's value is not said, as it can hold a
// password. An address of this machine or of a private network by its form,
// a name under .local or of one label among them, as a server under
// development that is not running, gets no such word.
function notThroughProxy(message, unreached) {
  const name = PROXY_SETTINGS.find((one) => process.env[one]);
  if (!name || !unreached) return message;
  const text = String(message).trim();
  return `${text}${/[.!?]$/.test(text) ? "" : "."} easybrandkit does not use the proxy ${name} names: its browser and its own requests connect to each site themselves, so on a network that reaches the web only through that proxy, no site can be read.`;
}

// What an https address read for one given with no scheme does when the
// site speaks plain http, as a server under development on a port of its
// own does: Chrome reads its http answer to the browser's TLS hello as a
// TLS error, and some servers close the connection.
const NOT_TLS = /^could not be opened \(net::ERR_(SSL_PROTOCOL_ERROR|SSL_VERSION_OR_CIPHER_MISMATCH|CONNECTION_REFUSED|CONNECTION_RESET|CONNECTION_CLOSED|EMPTY_RESPONSE)\)$/;

// A last line about the address given that was written with no scheme,
// which was read as https://, with the word to give it as http:// when the
// site speaks plain http.
function readAsHttps(message, asked) {
  const text = String(message).trim();
  return `${text}${/[.!?]$/.test(text) ? "" : "."} It was given with no http:// or https://, so it was read as https://: if the site speaks plain http, as a server under development often does, give it as ${asked.replace(/^https:/, "http:")}.`;
}

// namedBy: when another source named the site, as a store listing names its
// maker's website, and not the user, the address of that source. The site
// is then read as a page easybrandkit chose itself, as the website a
// listing names is, held to the rule for one (see address.js); refused
// there, it ends the run before anything is opened. The source is not
// opened, so the run has no address of its own: every address it opens is
// held to the rule, one on the source's scheme, host and port included.
async function makeKit(rawUrl, { dir, stores = true, facts = false, timeLimit = 120_000, namedBy = "", log = () => {} } = {}) {
  setTimeLimit(timeLimit);
  // MAKERSMCP_REFUSE_ADDRESSES, a value of which that does not parse ends
  // the run here, before any work.
  const refused = refusedAddresses();
  // This machine's network interfaces, whose addresses and IPv6 networks
  // the rule refuses away from the address given (see address.js ownIp):
  // a system that does not let them be read ends the run here too, as no
  // address could be told from one of this machine's.
  const unread = interfacesUnread();
  if (unread) {
    throw new Error(`This machine's network interfaces could not be read: ${unread.words}. Without them easybrandkit cannot tell this machine's own addresses from those on the public internet, so no kit was made.${moreFiles(unread) || " Run it where the system lets a program read them: on Linux, a service needs AF_NETLINK among its RestrictAddressFamilies."}`);
  }
  const asked = normalizeUrl(rawUrl);
  // Written with no scheme, which reads as https:// (see normalizeUrl).
  const bare = !/^[a-z][a-z0-9+.-]*:\/\//i.test(String(rawUrl || "").trim());
  // On this machine or a private network by its form, a name under .local
  // or of one label among them, which no proxy of the system's stands in
  // front of (see notThroughProxy).
  const local = notPublicByForm(new URL(asked));
  const source = namedBy ? normalizeUrl(namedBy) : "";
  const host = new URL(asked).hostname.toLowerCase();
  const listing = PLATFORM_HOST.test(host) ? classify(asked) : null;
  if (PLATFORM_HOST.test(host) && !(listing && (listing.type === "appstore" || listing.type === "googleplay"))) {
    throw new Error(`${asked} is a page on ${host.replace(/^(www|m|mobile)\./, "")}, not the brand's own site. Give the brand's website, or its App Store or Google Play listing.`);
  }
  // The rule for every address the run opens. The address given is opened
  // whatever its host and port, unless the setting refuses where it is; a
  // site another source named is not the address given, and with it the
  // run has none. A store listing is read from its store's own hosts (see
  // stores.js).
  const guard = guardFor(source ? null : asked, { refused });
  if (!listing) {
    const why = await guard.judge(asked);
    if (why) throw new Error(notThroughProxy(`${asked}${source ? `, named by ${source},` : ""} ${why}, so no kit was made.`, UNREACHED.test(why) && !local));
  }
  const notes = [];
  const target = dir || (listing ? `easybrandkit-${listing.type}-${listing.id}` : `easybrandkit-${host.replace(/^www\./, "")}`);
  // The files are made in the run's part folder, work, and go in place only
  // once everything has been read and written.
  const earlier = checkDir(target, { facts });
  let run;
  try {
    run = startRun(target, earlier);
  } catch (err) {
    // For the CLI, which says that an earlier kit is as it was.
    if (earlier) err.earlierKit = target;
    throw err;
  }
  const work = run.work;
  // The browser, once the folder is known to take the kit and before any
  // work: one that cannot be started stops the run here, before anything is
  // read. The first page read takes it.
  let browser = null;
  const take = () => {
    const one = browser;
    browser = null;
    return one;
  };
  try {
    browser = await launch(SCREEN, { guard });
    let given = null;
    let read = null;
    let page = "";
    if (listing) {
      log(`Reading the ${listing.type === "appstore" ? "App Store" : "Google Play"} listing`);
      given = await readSource(listing, work, guard);
      if (!given.ok) throw new Error(notThroughProxy(`${asked} could not be read: ${given.error}.`, STORE_UNREACHED.test(given.error)));
      page = siteOfListing(given.site || "");
    } else {
      page = homePageOf(asked) || asked;
    }
    // The app's own name, up to a tagline ("Duolingo: Learn Languages").
    const appName = given ? String(given.name || "").split(/\s*[:|\u2013\u2014]\s*|\s+-\s+/)[0] : "";
    // A page that fails ends the run when it is the address the user gave,
    // or when the run has used up its time on it. When it is another page
    // the kit chose to read, the run goes on with what it has: a listing
    // keeps what the listing gave, and a deeper address is read as given,
    // whose own failure then ends the run and names it. What the failed read
    // wrote does not go into the kit.
    let failed = "";
    if (page) {
      const had = fs.readdirSync(work);
      try {
        // A page the kit chose that the run's rule refuses is not asked for:
        // the browser holds every document to the rule (see chrome.js
        // holdDocuments), and its proxy every request (see proxy.js).
        read = await readPage(page, work, log, { alsoNamed: appName, facts, guard, browser: take() });
      } catch (err) {
        if (!err.pageFailed || page === asked || err.outOfTime) throw err;
        failed = err.pageFailed;
        for (const name of fs.readdirSync(work)) if (!had.includes(name)) fs.rmSync(path.join(work, name), { recursive: true, force: true });
      }
      if (failed && !listing) read = await readPage(asked, work, log, { alsoNamed: appName, facts, deeper: true, guard, browser: take() });
    }
    // A listing none of whose pictures came, and no website to read: a name
    // alone is no kit to put in the place of an earlier one.
    if (listing && !read && !given.assets.length) {
      throw new Error(`${asked}: no picture of the listing could be downloaded, ${failed ? `and the website it names, ${page}, ${failed}` : "and it names no website"}, so no kit was made.`);
    }
    const gave = given ? listingGave(given.assets) : {};
    const onlyListing = `so only the listing was read: the kit has ${gave.alone} but no logos, colors or fonts.`;
    if (listing && read && !gave.withSite) notes.push(`${asked} is a store listing none of whose pictures could be downloaded, so the kit comes from the website it names, ${page}.`);
    else if (listing && read) notes.push(`${asked} is a store listing: its ${gave.withSite} ${gave.plural ? "come" : "comes"} from the listing, the rest from the website it names, ${page}.`);
    else if (listing && failed) notes.push(`${asked} is a store listing, and the website it names, ${page}, ${failed}, ${onlyListing} For those, give an address of the product's site that opens.`);
    else if (listing) notes.push(`${asked} is a store listing that names no website, ${onlyListing} Give the product's website for those.`);
    else if (failed) notes.push(`The home page, ${page}, could not be read: it ${failed}. ${asked} was read as given, and its name, header and colors can differ from the home page's.`);
    else if (page !== asked) notes.push(`${asked} is not the home page, so ${page} was read instead: the home page carries the brand's own header and colors.`);
    if (read && read.inPlace) notes.push(`${read.inPlace.url} ${read.inPlace.said}, so ${read.inPlace.read} was read in its place.`);
    const found = read ? read.found : { brand: { fonts: {} }, icons: [], images: [], manifest: "", links: [] };
    if (read && !read.logos.length) notes.push("No logo was found on the page itself.");
    if (read && read.wordsUnread) {
      const some = read.text.headings.length || read.text.ctas.length ? "Some of the page's headings and button labels were" : "The page's headings and button labels were";
      notes.push(`${some} not read: ${read.wordsUnread === "time" ? "the run's time ran out. Give it more time with --timeout." : "the browser tab stopped answering."}`);
    }
    if (read && !read.card) notes.push(`The card could not be drawn: ${read.cardError.split(work).join(path.resolve(target)).replace(/[.\s]+$/, "")}.`);
    if (read) notes.push(...triedNotes(read.tried, read), ...refusedNotes(read.refused, read.refusedMore), ...proxyNotes(read.asked, read.askedMore));
    if (facts && !read) notes.push(failed ? "No facts were read: the website it names could not be read." : "No facts were read: the listing names no website.");
    const others = stores && read ? await readSources(found.links, work, log, given ? [given.type] : [], guard) : [];
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
      notes: notes.map((note) => plainText(note, 2_000)),
    };
    fs.writeFileSync(path.join(work, "brand.json"), JSON.stringify(kit, null, 2) + "\n");
    writeMarkdown(kit, work);
    // The page's ground is not in brand.json: its list of colors can file
    // that color under the header or footer.
    fs.writeFileSync(path.join(work, "_brand.yml"), brandYml(kit, { background: found.brand.background || "", site: read ? read.pageUrl : "" }));
    // FACTS.md says the home page was not read, and why, as BRAND.md does.
    if (facts && read && failed && !listing) read.factPages.skipped.unshift({ role: "home", url: page, reason: `it ${failed}` });
    const claims = facts && read ? await writeFacts(work, { name: kit.name, site: kit.url, generator: kit.generator, ...read.factPages }) : null;
    // The folder is read again as the files go in: it can have changed
    // while the site was read.
    await saveRun(run, () => checkDir(target, { saving: true }) || []);
    return { dir: target, kit, facts: claims };
  } catch (err) {
    if (err instanceof SaveError || !(err instanceof Error)) throw err;
    // A write that failed because the folder the new kit was made in was
    // removed meanwhile is told as that, and an earlier kit only while it is
    // still there.
    const removed = removedFrom(run);
    const plain = removed && err.syscall ? new Error(removed.said) : toldPlainly(err, run);
    // The address given, or the page read in its place, that could not be
    // reached, as on a network that reaches the web only through a proxy.
    if (plain === err && err.pageFailed && bare && NOT_TLS.test(err.pageFailed)) plain.message = readAsHttps(plain.message, asked);
    if (plain === err && err.pageFailed && UNREACHED.test(err.pageFailed) && !local) plain.message = notThroughProxy(plain.message, true);
    // For the CLI, which says that an earlier kit is as it was. saveRun's
    // own errors say what the folder holds.
    if (removed ? removed.earlier : run.earlier) plain.earlierKit = target;
    throw plain;
  } finally {
    if (browser) await take().close();
    discardRun(run);
  }
}

module.exports = { makeKit, normalizeUrl, homePageOf, siteOfListing, prepareDir, brandName };
