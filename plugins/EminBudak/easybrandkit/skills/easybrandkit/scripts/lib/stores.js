"use strict";

// A brand's own images from its app store listings and social profiles: the
// app icon at 1024 px, the store screenshots, the profile picture, and the
// listing's name, maker and description. The site links to them; these are
// the pictures a mockup or a video of the app should use.
//
// It fetches only HTTPS URLs on the listed store, social and image hosts,
// re-checks every redirect, refuses non-public addresses and caps each file
// at 15 MB.

const fs = require("fs");
const path = require("path");
const net = require("net");
const { promises: dns } = require("dns");
const { timeLeft } = require("./time");

const MAX_BYTES = 15 * 1024 * 1024;
const MAX_SCREENSHOTS = 5;
const UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36";

const FETCH_HOSTS = [
  /^itunes\.apple\.com$/, /^apps\.apple\.com$/, /^[a-z0-9-]+\.mzstatic\.com$/,
  /^play\.google\.com$/, /^play-lh\.googleusercontent\.com$/, /^lh\d\.googleusercontent\.com$/,
  /^(www\.)?instagram\.com$/, /^[a-z0-9.-]+\.cdninstagram\.com$/, /^[a-z0-9.-]+\.fbcdn\.net$/,
  /^(www\.|m\.)?youtube\.com$/, /^yt\d\.(ggpht|googleusercontent)\.com$/, /^i\.ytimg\.com$/,
  /^(www\.|m\.)?facebook\.com$/, /^(www\.)?linkedin\.com$/, /^media\.licdn\.com$/,
  /^(www\.)?(x|twitter)\.com$/, /^pbs\.twimg\.com$/,
  /^(www\.)?tiktok\.com$/, /^[a-z0-9.-]+\.tiktokcdn(-[a-z]+)?\.com$/,
  /^(www\.)?threads\.(net|com)$/, /^(www\.)?pinterest\.[a-z.]+$/, /^i\.pinimg\.com$/,
];
const PROFILE_HOSTS = [
  [/^(www\.)?instagram\.com$/, "instagram"],
  [/^(www\.|m\.)?youtube\.com$/, "youtube"],
  [/^(www\.|m\.)?facebook\.com$/, "facebook"],
  [/^(www\.)?linkedin\.com$/, "linkedin"],
  [/^(www\.)?(x|twitter)\.com$/, "x"],
  [/^(www\.)?tiktok\.com$/, "tiktok"],
  [/^(www\.)?threads\.(net|com)$/, "threads"],
  [/^(www\.)?pinterest\.[a-z.]+$/, "pinterest"],
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
  for (const [pattern, type] of PROFILE_HOSTS) {
    const page = url.pathname.replace(/\/+$/, "");
    if (pattern.test(host) && page) return { type, url: `https://${host}${page}` };
  }
  return null;
}

function isPublicAddress(address) {
  const family = net.isIP(address);
  if (family === 4) {
    const [a, b, c] = address.split(".").map(Number);
    return !(
      a === 0 || a === 10 || a === 127 || a >= 224 ||
      (a === 100 && b >= 64 && b <= 127) ||
      (a === 169 && b === 254) ||
      (a === 172 && b >= 16 && b <= 31) ||
      (a === 192 && b === 168) ||
      (a === 192 && b === 0 && (c === 0 || c === 2)) ||
      (a === 198 && (b === 18 || b === 19 || (b === 51 && c === 100))) ||
      (a === 203 && b === 0 && c === 113)
    );
  }
  if (family === 6) {
    const normalized = address.toLowerCase();
    const first = Number.parseInt(normalized.split(":")[0], 16);
    return Number.isFinite(first) && first >= 0x2000 && first <= 0x3fff && !normalized.startsWith("2001:db8:");
  }
  return false;
}

async function checkFetchUrl(raw) {
  const url = new URL(raw);
  const host = url.hostname.toLowerCase();
  if (url.protocol !== "https:") throw new Error(`not HTTPS: ${raw}`);
  if (url.username || url.password || (url.port && url.port !== "443")) throw new Error(`not a plain URL: ${raw}`);
  if (!FETCH_HOSTS.some((pattern) => pattern.test(host))) throw new Error(`host not allowed: ${host}`);
  const records = await dns.lookup(host, { all: true, verbatim: true });
  if (!records.length || !records.every((record) => isPublicAddress(record.address))) {
    throw new Error(`host does not resolve to a public address: ${host}`);
  }
  return url;
}

// GET with every redirect re-checked against the host list, a size cap and
// a timeout inside the run's deadline.
async function get(raw, { binary = false, accept = "*/*" } = {}) {
  let current = raw;
  for (let hop = 0; hop < 5; hop++) {
    const url = await checkFetchUrl(current);
    const left = timeLeft();
    if (left < 2_000) throw new Error("out of time");
    const res = await fetch(url, {
      redirect: "manual",
      headers: { "user-agent": UA, accept, "accept-language": "en-US,en;q=0.8" },
      signal: AbortSignal.timeout(Math.min(25_000, left - 1_000)),
    });
    if (res.status >= 300 && res.status < 400 && res.headers.get("location")) {
      current = new URL(res.headers.get("location"), url).href;
      continue;
    }
    if (!res.ok) throw new Error(`HTTP ${res.status} from ${url.hostname}`);
    const declared = Number(res.headers.get("content-length") || 0);
    if (declared > MAX_BYTES) throw new Error(`larger than 15 MB: ${url.hostname}`);
    const chunks = [];
    let size = 0;
    for await (const chunk of res.body) {
      size += chunk.length;
      if (size > MAX_BYTES) throw new Error(`larger than 15 MB: ${url.hostname}`);
      chunks.push(chunk);
    }
    const body = Buffer.concat(chunks);
    return { body: binary ? body : body.toString("utf8"), type: res.headers.get("content-type") || "", url: url.href };
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
// login wall, a removed app) comes back with ok:false and the reason.
async function readSource(link, dir) {
  const source = { type: link.type, url: link.url, ok: false, assets: [] };
  try {
    let plan = null;
    if (link.type === "appstore") {
      const lookup = async (country, lang) => appStorePlan(JSON.parse((await get(appStoreLookupUrl(link.id, country, lang), { accept: "application/json" })).body));
      plan = await lookup(link.country, link.lang);
      if (!plan && link.lang) plan = await lookup(link.country, "");
      if (!plan && link.country !== "us") plan = await lookup("us", "");
    } else if (link.type === "googleplay") {
      plan = playPlan((await get(link.url, { accept: "text/html" })).body);
    } else {
      plan = profilePlan((await get(link.url, { accept: "text/html" })).body);
    }
    if (!plan) throw new Error("the page has no listing or profile data (removed, private or behind a login)");
    const { images, ...facts } = plan;
    Object.assign(source, facts);
    let shot = 0;
    for (const image of images) {
      try {
        const { body } = await get(image.url, { binary: true, accept: "image/png,image/jpeg,image/webp,*/*;q=0.5" });
        const info = imageInfo(body);
        if (!info) continue;
        const suffix = image.kind === "screenshot" ? `shot-${String(++shot).padStart(2, "0")}` : image.kind;
        const file = `${link.type}-${suffix}.${info.ext}`;
        fs.writeFileSync(path.join(dir, file), body);
        source.assets.push({ file, kind: image.kind, url: image.url, width: info.width, height: info.height, alpha: info.alpha });
      } catch {
        // One image that will not come is skipped; the rest still count.
      }
    }
    source.ok = source.assets.length > 0 || Boolean(source.name);
    if (!source.ok) source.error = "no images could be downloaded";
  } catch (err) {
    source.error = err.message;
  }
  return source;
}

module.exports = { classify, appStoreLookupUrl, appStorePlan, playPlan, profilePlan, imageInfo, isPublicAddress, checkFetchUrl, readSource };
