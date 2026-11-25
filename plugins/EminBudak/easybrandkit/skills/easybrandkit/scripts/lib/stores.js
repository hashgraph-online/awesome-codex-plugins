"use strict";

// A brand's own images from its app store listings and social profiles: the
// app icon at 1024 px, the store screenshots, the profile picture, and the
// listing's name, maker and description. The site links to them; these are
// the pictures a mockup or a video of the app should use.
//
// It fetches only HTTPS URLs on port 443 of the listed store, social and
// image hosts, re-checks every redirect, refuses addresses that are not on
// the public internet and those MAKERSMCP_REFUSE_ADDRESSES names (see
// address.js), looks each host up once a run, by the run's own lookup,
// connects only to the addresses it judged, through no proxy (see
// dial.js), and caps each file at 15 MB.

const fs = require("fs");
const https = require("https");
const path = require("path");
const zlib = require("zlib");
const { timeLeft } = require("./time");
const { noControls, plainText, noEndSlashes } = require("./text");
const { isPublicAddress, atRefused, awayWhy, mixedAnswers, guardFor } = require("./address");
const { judgedRequest } = require("./dial");

const MAX_BYTES = 15 * 1024 * 1024;
const MAX_SCREENSHOTS = 5;
const UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36";

// Pinterest's own hosts: pinterest.com with its country sites, as
// uk.pinterest.com, and a list of the country domains that send their
// visitors there with the path kept, as pinterest.co.uk and pinterest.be
// do, each checked on 2026-11-20. A host such as pinterest.acme.example is
// not one.
const PINTEREST = [
  /^([a-z]{2}\.|www\.)?pinterest\.com$/,
  /^(www\.)?pinterest\.(at|be|ca|ch|cl|co|co\.in|co\.kr|co\.nz|co\.uk|com\.au|com\.bo|com\.ec|com\.mx|com\.pe|com\.py|com\.uy|com\.vn|de|dk|ec|es|fr|hu|id|ie|in|it|jp|kr|mx|nl|nz|pe|ph|pt|ru|se|th|tw|vn)$/,
];
const FETCH_HOSTS = [
  /^itunes\.apple\.com$/, /^apps\.apple\.com$/, /^[a-z0-9-]+\.mzstatic\.com$/,
  /^play\.google\.com$/, /^play-lh\.googleusercontent\.com$/, /^lh\d\.googleusercontent\.com$/,
  /^(www\.)?instagram\.com$/, /^[a-z0-9.-]+\.cdninstagram\.com$/, /^[a-z0-9.-]+\.fbcdn\.net$/,
  /^(www\.|m\.)?youtube\.com$/, /^yt\d\.(ggpht|googleusercontent)\.com$/, /^i\.ytimg\.com$/,
  /^(www\.|m\.)?facebook\.com$/, /^(www\.)?linkedin\.com$/, /^media\.licdn\.com$/,
  /^(www\.)?(x|twitter)\.com$/, /^pbs\.twimg\.com$/,
  /^(www\.)?tiktok\.com$/, /^[a-z0-9.-]+\.tiktokcdn(-[a-z]+)?\.com$/,
  /^(www\.)?threads\.(net|com)$/, /^i\.pinimg\.com$/,
  ...PINTEREST,
];
const PROFILE_HOSTS = [
  [/^(www\.)?instagram\.com$/, "instagram"],
  [/^(www\.|m\.)?youtube\.com$/, "youtube"],
  [/^(www\.|m\.)?facebook\.com$/, "facebook"],
  [/^(www\.)?linkedin\.com$/, "linkedin"],
  [/^(www\.)?(x|twitter)\.com$/, "x"],
  [/^(www\.)?tiktok\.com$/, "tiktok"],
  [/^(www\.)?threads\.(net|com)$/, "threads"],
  ...PINTEREST.map((pattern) => [pattern, "pinterest"]),
];

// What a link is: an App Store app, a Google Play app or a social profile.
function classify(raw) {
  let url;
  try {
    url = new URL(String(raw || "").trim());
  } catch {
    return null;
  }
  if (url.protocol !== "https:" && url.protocol !== "http:") return null;
  const host = url.hostname.toLowerCase();
  const id = url.pathname.match(/\/id(\d{5,})/);
  if (/^(apps|itunes)\.apple\.com$/.test(host) && id) {
    const country = ((url.pathname.match(/^\/([a-z]{2})\//i) || [])[1] || "us").toLowerCase();
    // A developer page's id is the maker's: the lookup answers with the
    // maker first and its apps after, and the first app stands for the brand.
    const kind = /\/developer\//.test(url.pathname) ? "developer" : "app";
    // The listing's language (?l=tr): the lookup API answers a storefront in
    // English unless it is asked for one, and a Turkish listing came back
    // with English screenshots.
    const lang = (url.searchParams.get("l") || "").toLowerCase();
    if (/^[a-z]{2}$/.test(lang)) return { type: "appstore", id: id[1], country, lang, url: `https://apps.apple.com/${country}/${kind}/id${id[1]}?l=${lang}` };
    return { type: "appstore", id: id[1], country, url: `https://apps.apple.com/${country}/${kind}/id${id[1]}` };
  }
  const pkg = url.searchParams.get("id");
  if (host === "play.google.com" && url.pathname.startsWith("/store/apps/details") && /^[\w.]+$/.test(pkg || "")) {
    const hl = /^[a-z]{2}(-[A-Z]{2})?$/.test(url.searchParams.get("hl") || "") ? url.searchParams.get("hl") : "en";
    const gl = (url.searchParams.get("gl") || "").toUpperCase();
    if (/^[A-Z]{2}$/.test(gl)) return { type: "googleplay", id: pkg, hl, gl, url: `https://play.google.com/store/apps/details?id=${pkg}&hl=${hl}&gl=${gl}` };
    return { type: "googleplay", id: pkg, hl, url: `https://play.google.com/store/apps/details?id=${pkg}&hl=${hl}` };
  }
  const page = noEndSlashes(url.pathname);
  for (const [pattern, type] of PROFILE_HOSTS) {
    if (pattern.test(host) && page) return { type, url: `https://${host}${page}` };
  }
  return null;
}

// The address of a store's page or picture, refused unless it is a plain
// HTTPS address on a listed host, at addresses that are all on the public
// internet, none of them this machine's own or one the run's rule refuses
// (guard, see address.js), with the addresses its host was found at, which
// its request connects to
// (see get). The host is looked up by the run's own lookup, which asks the
// DNS once a run for each name (guard.found): a name a page, a listing's
// picture or a redirect names again is not looked up again.
async function judgedFetch(raw, guard = null) {
  const url = new URL(raw);
  const host = url.hostname.toLowerCase();
  if (url.protocol !== "https:") throw new Error(`not HTTPS: ${raw}`);
  if (url.username || url.password || (url.port && url.port !== "443")) throw new Error(`not a plain URL: ${raw}`);
  if (!FETCH_HOSTS.some((pattern) => pattern.test(host))) throw new Error(`host not allowed: ${host}`);
  const rule = guard || guardFor(null);
  const addresses = await rule.found(host);
  if (!addresses.length) throw new Error(`host ${host} could not be looked up`);
  const refused = addresses.map((address) => rule.refused.match(address)).find(Boolean);
  if (refused) throw new Error(`host ${host} ${atRefused(refused)}`);
  // Each address is on the public internet and none is this machine's own,
  // as for any address the run was not given (see address.js awayWhy). A
  // name whose answers mix is said to answer so, as in "host
  // play.google.com answers with an address on the public internet, ...",
  // where "host play.google.com is on a host whose name answers ..." said
  // that the host is on a host.
  const mixed = mixedAnswers(addresses);
  if (mixed) throw new Error(`host ${host} ${mixed}`);
  const away = awayWhy(addresses);
  if (away) throw new Error(`host ${host} ${away}`);
  return { url, addresses };
}

// The address alone, judged as above.
async function checkFetchUrl(raw, guard = null) {
  return (await judgedFetch(raw, guard)).url;
}

// The answer to a GET of url, connected to one of the addresses its host
// was found and judged at, and to no other: the DNS is asked nothing again,
// so a name whose next answer is another address still reaches none of
// those, and no proxy the environment names is used (see dial.js).
function answerOf(url, { headers, signal, addresses }) {
  return new Promise((resolve, reject) => {
    const req = https.get(url, { headers, signal, ...judgedRequest(url, () => addresses, { signal }) }, resolve);
    req.on("error", reject);
  });
}

// An answer's body, decompressed, failed past 15 MB.
async function bodyOf(res, host) {
  const coding = String(res.headers["content-encoding"] || "").trim().toLowerCase();
  const decoder = coding === "gzip" || coding === "x-gzip" ? zlib.createGunzip() : coding === "deflate" ? zlib.createInflate() : coding === "br" ? zlib.createBrotliDecompress() : null;
  if (!decoder && coding && coding !== "identity") throw new Error(`answered in an encoding the kit does not read (${coding.slice(0, 40)}): ${host}`);
  const stream = decoder ? res.pipe(decoder) : res;
  if (decoder) res.on("error", (err) => decoder.destroy(err));
  const chunks = [];
  let size = 0;
  try {
    for await (const chunk of stream) {
      size += chunk.length;
      if (size > MAX_BYTES) throw new Error(`larger than 15 MB: ${host}`);
      chunks.push(chunk);
    }
  } finally {
    res.destroy();
    if (decoder) decoder.destroy();
  }
  return Buffer.concat(chunks);
}

// GET with every redirect re-checked against the host list and the run's
// rule (guard), connected only to the addresses judged, with a size cap and
// a timeout inside the run's deadline.
async function get(raw, { binary = false, accept = "*/*", guard = null } = {}) {
  let current = raw;
  for (let hop = 0; hop < 5; hop++) {
    const { url, addresses } = await judgedFetch(current, guard);
    const left = timeLeft();
    if (left < 2_000) throw new Error("out of time");
    const wait = Math.min(25_000, left - 1_000);
    const signal = AbortSignal.timeout(wait);
    try {
      const res = await answerOf(url, { headers: { "user-agent": UA, accept, "accept-language": "en-US,en;q=0.8", "accept-encoding": "gzip, deflate, br" }, signal, addresses });
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        res.destroy();
        current = new URL(res.headers.location, url).href;
        continue;
      }
      if (res.statusCode < 200 || res.statusCode >= 300) {
        res.destroy();
        throw new Error(`HTTP ${res.statusCode} from ${url.hostname}`);
      }
      if (Number(res.headers["content-length"] || 0) > MAX_BYTES) {
        res.destroy();
        throw new Error(`larger than 15 MB: ${url.hostname}`);
      }
      const body = await bodyOf(res, url.hostname);
      return { body: binary ? body : body.toString("utf8"), type: String(res.headers["content-type"] || ""), url: url.href };
    } catch (err) {
      // Told by the server that did not answer, not in the words of Node's
      // timer, which name nothing.
      if (signal.aborted) throw new Error(`${url.hostname} did not answer in ${Math.round(wait / 1_000)} s`);
      throw err;
    }
  }
  throw new Error(`too many redirects: ${raw}`);
}

// Width, height and transparency from the header bytes of a PNG, JPEG or WebP.
function imageInfo(buf) {
  if (buf.length > 26 && buf.readUInt32BE(0) === 0x89504e47) {
    return { ext: "png", width: buf.readUInt32BE(16), height: buf.readUInt32BE(20), alpha: buf[25] === 4 || buf[25] === 6 };
  }
  if (buf.length > 4 && buf[0] === 0xff && buf[1] === 0xd8) {
    for (let i = 2; i + 9 < buf.length; ) {
      if (buf[i] !== 0xff) {
        i++;
        continue;
      }
      const marker = buf[i + 1];
      const length = buf.readUInt16BE(i + 2);
      if (marker >= 0xc0 && marker <= 0xcf && ![0xc4, 0xc8, 0xcc].includes(marker)) {
        return { ext: "jpg", width: buf.readUInt16BE(i + 7), height: buf.readUInt16BE(i + 5), alpha: false };
      }
      i += 2 + length;
    }
    return { ext: "jpg", width: 0, height: 0, alpha: false };
  }
  if (buf.length > 30 && buf.toString("ascii", 0, 4) === "RIFF" && buf.toString("ascii", 8, 12) === "WEBP") {
    const chunk = buf.toString("ascii", 12, 16);
    if (chunk === "VP8X") {
      return { ext: "webp", width: 1 + buf.readUIntLE(24, 3), height: 1 + buf.readUIntLE(27, 3), alpha: (buf[20] & 0x10) !== 0 };
    }
    if (chunk === "VP8L") {
      const bits = buf.readUInt32LE(21);
      return { ext: "webp", width: 1 + (bits & 0x3fff), height: 1 + ((bits >> 14) & 0x3fff), alpha: ((bits >> 28) & 1) === 1 };
    }
    return { ext: "webp", width: buf.readUInt16LE(26) & 0x3fff, height: buf.readUInt16LE(28) & 0x3fff, alpha: false };
  }
  return null;
}

function decodeEntities(text) {
  return String(text || "")
    .replace(/&quot;/g, '"').replace(/&#39;|&#x27;/g, "'").replace(/&lt;/g, "<").replace(/&gt;/g, ">")
    .replace(/&#(\d+);/g, (_, n) => String.fromCodePoint(Number(n)))
    .replace(/&#x([0-9a-f]+);/gi, (_, n) => String.fromCodePoint(parseInt(n, 16)))
    .replace(/&amp;/g, "&");
}

function metaContent(html, key) {
  const tags = html.match(/<meta\b[^>]*>/gi) || [];
  for (const tag of tags) {
    const name = (tag.match(/\b(?:property|name|itemprop)\s*=\s*["']([^"']+)["']/i) || [])[1];
    if (name && name.toLowerCase() === key) return decodeEntities((tag.match(/\bcontent\s*=\s*["']([^"']*)["']/i) || [])[1] || "");
  }
  return "";
}

// The lookup API's address for one storefront, in one language when given
// ("tr" in the tr storefront asks for tr_tr).
function appStoreLookupUrl(id, country, lang) {
  return `https://itunes.apple.com/lookup?id=${id}&country=${country}&entity=software${lang ? `&lang=${lang}_${country}` : ""}`;
}

// App Store: the lookup API gives the name, maker, rating, icon and
// screenshots. mzstatic serves any size of an image by its last path part,
// so the icon is taken at 1024 px and each screenshot at 1290 px wide, PNG.
function appStorePlan(lookup) {
  const app = ((lookup && lookup.results) || []).find((result) => result && result.wrapperType !== "artist" && result.trackName);
  if (!app) return null;
  const resize = (raw, size) => String(raw || "").replace(/\/[^/]+\.(jpg|jpeg|png|webp)$/i, `/${size}.png`);
  const shots = [...(app.screenshotUrls || []), ...(app.ipadScreenshotUrls || [])].slice(0, MAX_SCREENSHOTS);
  return {
    name: app.trackName || "",
    by: app.sellerName || app.artistName || "",
    site: app.sellerUrl || "",
    category: app.primaryGenreName || "",
    rating: app.averageUserRating || null,
    ratings: app.userRatingCount || null,
    // The whole text (the stores allow 4000 characters): the feature list a
    // video or a page wants comes after the first few hundred.
    description: String(app.description || "").slice(0, 4000),
    images: [
      ...(app.artworkUrl512 ? [{ kind: "icon", url: resize(app.artworkUrl512, "1024x1024bb") }] : []),
      ...shots.map((shot) => {
        const [, w, h] = String(shot).match(/\/(\d+)x(\d+)[a-z]*\.\w+$/i) || [];
        const size = w && h ? `1290x${Math.round((Number(h) * 1290) / Number(w))}bb` : "1290x0w";
        return { kind: "screenshot", url: resize(shot, size) };
      }),
    ],
  };
}

// Google Play: the listing page marks its screenshots with
// data-screenshot-index (their alt text is in the page's language: "Ekran
// görüntüsü resmi" with hl=tr) and names its icon by alt text or og:image;
// googleusercontent serves any width by its "=…" suffix.
function playPlan(html) {
  const imgs = html.match(/<img\b[^>]*>/gi) || [];
  const src = (tag) => decodeEntities((tag.match(/\bsrc\s*=\s*["']([^"']+)["']/i) || [])[1] || "");
  const alt = (tag) => decodeEntities((tag.match(/\balt\s*=\s*["']([^"']*)["']/i) || [])[1] || "").toLowerCase();
  const sized = (raw, size) => (raw ? raw.replace(/=[^/=]*$/, "") + size : "");
  const icon = src(imgs.find((tag) => alt(tag) === "icon image") || "") || metaContent(html, "og:image");
  const isShot = (tag) => /\bdata-screenshot-index\s*=/i.test(tag) || alt(tag) === "screenshot image";
  const shots = [...new Set(imgs.filter(isShot).map(src).filter(Boolean).map((raw) => raw.replace(/=[^/=]*$/, "")))];
  // "… - Apps on Google Play", "… - Google Play'de Uygulamalar" (the store
  // writes a hyphen or an en dash before its own name).
  const title = metaContent(html, "og:title").replace(/\s*[-\u2013]\s*[^-\u2013]*Google Play[^-\u2013]*$/i, "");
  if (!icon && !shots.length && !title) return null;
  // The developer's website: the link with the "public" (globe) icon, whose
  // label is in the page's language ("Website", "Web sitesi").
  const site = decodeEntities((html.match(/<a\b[^>]*href="(https?:\/\/[^"]+)"[^>]*>\s*<i\b[^>]*>public<\/i>/i) || [])[1] || "");
  // The listing's whole text, line breaks kept. The meta description stops
  // short, before the feature list.
  const body = (html.match(/<div\b[^>]*data-g-id="description"[^>]*>([\s\S]*?)<\/div>/i) || [])[1] || "";
  const text = decodeEntities(body.replace(/<br\s*\/?>/gi, "\n").replace(/<[^>]+>/g, "")).replace(/[ \t]+\n/g, "\n").trim();
  return {
    name: title,
    by: decodeEntities((html.match(/<a\b[^>]*href="\/store\/apps\/dev(?:eloper)?\?id=[^"]*"[^>]*>\s*(?:<span[^>]*>)?([^<]+)/i) || [])[1] || "").trim(),
    site,
    category: "",
    rating: null,
    ratings: null,
    description: (text || metaContent(html, "description")).slice(0, 4000),
    images: [
      ...(icon ? [{ kind: "icon", url: sized(icon, "=s1024") }] : []),
      ...shots.slice(0, MAX_SCREENSHOTS).map((raw) => ({ kind: "screenshot", url: sized(raw, "=w1440") })),
    ],
  };
}

// A social profile: its Open Graph picture (the profile photo or channel
// avatar) and title, when the page serves them without a login.
function profilePlan(html) {
  // X serves its avatars in fixed sizes: _400x400 is the largest.
  const image = (metaContent(html, "og:image") || metaContent(html, "twitter:image")).replace(
    /(pbs\.twimg\.com\/profile_images\/.+)_(normal|bigger|mini|200x200)\.(\w+)$/,
    "$1_400x400.$3",
  );
  const title = (metaContent(html, "og:title") || metaContent(html, "twitter:title")).replace(/\s*[|·-]\s*LinkedIn$/i, "");
  if (!image && !title) return null;
  return {
    name: title,
    by: "",
    category: "",
    rating: null,
    ratings: null,
    description: (metaContent(html, "og:description") || metaContent(html, "description")).slice(0, 600),
    images: image ? [{ kind: "profile", url: decodeEntities(image) }] : [],
  };
}

// One listing or profile, its pictures saved in dir as <type>-icon.png,
// <type>-shot-01.png … <type>-profile.jpg. A source that cannot be read (a
// login wall, a removed app) comes back with ok:false and the reason. A
// picture that cannot be written, as on a full disk, fails the run instead:
// what it has of the file would otherwise go into the kit. guard: the run's
// rule for the addresses it opens, whose refused addresses are refused here
// too, and whose lookup each host is found by; without one, the listing
// gets a lookup of its own.
async function readSource(link, dir, guard = guardFor(null)) {
  const source = { type: link.type, url: link.url, ok: false, assets: [] };
  let notWritten = null;
  try {
    let plan = null;
    if (link.type === "appstore") {
      const lookup = async (country, lang) => appStorePlan(JSON.parse((await get(appStoreLookupUrl(link.id, country, lang), { accept: "application/json", guard })).body));
      plan = await lookup(link.country, link.lang);
      if (!plan && link.lang) plan = await lookup(link.country, "");
      if (!plan && link.country !== "us") plan = await lookup("us", "");
    } else if (link.type === "googleplay") {
      plan = playPlan((await get(link.url, { accept: "text/html", guard })).body);
    } else {
      plan = profilePlan((await get(link.url, { accept: "text/html", guard })).body);
    }
    if (!plan) throw new Error("the page has no listing or profile data (removed, private or behind a login)");
    const { images, ...facts } = plan;
    Object.assign(source, facts, { name: plainText(facts.name, 200), by: plainText(facts.by, 200), category: plainText(facts.category, 100), description: noControls(facts.description) });
    let shot = 0;
    for (const image of images) {
      let body;
      let info;
      try {
        ({ body } = await get(image.url, { binary: true, accept: "image/png,image/jpeg,image/webp,*/*;q=0.5", guard }));
        info = imageInfo(body);
      } catch {
        // One image that will not come is skipped; the rest still count.
        continue;
      }
      if (!info) continue;
      const suffix = image.kind === "screenshot" ? `shot-${String(++shot).padStart(2, "0")}` : image.kind;
      const file = `${link.type}-${suffix}.${info.ext}`;
      try {
        fs.writeFileSync(path.join(dir, file), body);
      } catch (err) {
        notWritten = err;
        throw err;
      }
      source.assets.push({ file, kind: image.kind, url: image.url, width: info.width, height: info.height, alpha: info.alpha });
    }
    source.ok = source.assets.length > 0 || Boolean(source.name);
    if (!source.ok) source.error = "no images could be downloaded";
  } catch (err) {
    if (err === notWritten) throw err;
    source.error = err.message;
  }
  return source;
}

module.exports = { classify, appStoreLookupUrl, appStorePlan, playPlan, profilePlan, imageInfo, isPublicAddress, checkFetchUrl, readSource };
