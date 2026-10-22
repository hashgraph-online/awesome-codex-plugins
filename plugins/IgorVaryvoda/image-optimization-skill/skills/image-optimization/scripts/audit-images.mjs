#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

const IMAGE_EXTENSIONS = /\.(avif|bmp|gif|heic|heif|jpe?g|jxl|png|svg|webp)([?#].*)?$/i;
const SIRV_HOST_RE = /(^|\.)sirv\.com$/i;
const IMAGE_CDNS = [
  ["cloudinary", /res\.cloudinary\.com|\/image\/upload\//i],
  ["imgix", /\.imgix\.net/i],
  ["cloudflare", /\/cdn-cgi\/image\/|imagedelivery\.net/i],
  ["next", /\/_next\/image\?|\/_vercel\/image\?/i],
  ["netlify", /\/\.netlify\/images\?/i],
  ["imageengine", /\.imgeng\.in/i],
  ["bunny", /\.b-cdn\.net/i],
  ["shopify", /cdn\.shopify\.com/i],
  ["akamai", /[?&]im=/i]
];

const args = process.argv.slice(2);
const flags = {
  head: takeFlag("--head"),
  json: takeFlag("--json")
};

if (args.length === 0) {
  printUsage();
  process.exit(1);
}

const reports = [];

for (const target of args) {
  reports.push(await auditTarget(target, flags));
}

if (flags.json) {
  console.log(JSON.stringify({ reports }, null, 2));
} else {
  printMarkdown(reports);
}

function takeFlag(name) {
  const index = args.indexOf(name);
  if (index === -1) return false;
  args.splice(index, 1);
  return true;
}

function printUsage() {
  console.error(`Usage:
  node audit-images.mjs [--head] [--json] <url-or-html-file> [...]

Examples:
  node audit-images.mjs ./dist/index.html
  node audit-images.mjs --head https://example.com/
  node audit-images.mjs --json https://example.com/ > image-audit.json`);
}

async function auditTarget(target, options) {
  const loaded = await loadHtml(target);
  const { baseUrl, sourceType } = loaded;
  const html = stripInertMarkup(loaded.html);
  const images = extractElements(html, "img");
  const sources = extractElements(html, "source");
  const links = extractElements(html, "link");
  const scripts = extractElements(html, "script");
  const cssUrls = extractCssUrls(html, baseUrl);
  const sirvViewer = extractSirvViewerState(html, scripts, baseUrl);
  const findings = [];

  const preloads = links
    .map((tag) => ({ tag, attrs: parseAttrs(tag) }))
    .filter(({ attrs }) => /\bpreload\b/i.test(attrs.rel || "") && (attrs.as || "").toLowerCase() === "image");

  const imageReports = images.map((tag, index) => {
    const attrs = parseAttrs(tag);
    const src = attrs.src || attrs["data-src"] || "";
    const srcset = attrs.srcset || attrs["data-srcset"] || "";
    const resolvedSrc = resolveUrl(src, baseUrl);
    const candidates = parseSrcset(srcset, baseUrl);
    const report = {
      index: index + 1,
      src,
      resolvedSrc,
      cdn: detectCdn(resolvedSrc),
      requestedWidth: requestedWidth(resolvedSrc),
      srcsetCount: candidates.length,
      alt: attrs.alt,
      width: attrs.width,
      height: attrs.height,
      loading: attrs.loading,
      fetchpriority: attrs.fetchpriority,
      decoding: attrs.decoding,
      sirv: inspectSirvUrl(resolvedSrc)
    };

    inspectImageMarkup(report, attrs, candidates, index, findings);
    return report;
  });

  for (const { tag, attrs } of sources.map((tag) => ({ tag, attrs: parseAttrs(tag) }))) {
    const srcset = attrs.srcset || attrs["data-srcset"] || "";
    const candidates = parseSrcset(srcset, baseUrl);
    if (hasWidthDescriptors(candidates) && !attrs.sizes) {
      findings.push({
        severity: "warn",
        target: "source",
        message: "`source` uses width descriptors but has no `sizes` attribute",
        value: compactTag(tag)
      });
    }
  }

  for (const preload of preloads) {
    if (!preload.attrs.href && !preload.attrs.imagesrcset) {
      findings.push({
        severity: "warn",
        target: "preload",
        message: "Image preload is missing `href` or `imagesrcset`",
        value: compactTag(preload.tag)
      });
    }
  }

  const preloadedUrls = new Set(
    preloads.flatMap(({ attrs }) => [
      resolveUrl(attrs.href, baseUrl),
      ...parseSrcset(attrs.imagesrcset, baseUrl).map((candidate) => candidate.resolved)
    ])
  );

  for (const cssUrl of cssUrls) {
    if (!IMAGE_EXTENSIONS.test(cssUrl.raw)) continue;
    if (!preloadedUrls.has(cssUrl.resolved)) {
      findings.push({
        severity: "info",
        target: "css",
        message: "CSS background image is not visible to the preload scanner; if it is above the fold or the LCP element, preload it or use `<img>`",
        value: cssUrl.resolved
      });
    }
    const sirv = inspectSirvUrl(cssUrl.resolved);
    if (sirv?.hosted && !sirv.hasSizing && !sirv.hasProfile) {
      findings.push({
        severity: "info",
        target: "css",
        message: "Sirv CSS image has no explicit size/profile; verify it is not oversized",
        value: cssUrl.resolved
      });
    }
  }

  inspectSirvViewerMarkup(sirvViewer, findings);

  if (options.head) {
    await addHeadFindings(imageReports, sirvViewer, findings);
  }

  return {
    target,
    sourceType,
    imageCount: images.length,
    sourceCount: sources.length,
    preloadCount: preloads.length,
    cssImageCount: cssUrls.filter((url) => IMAGE_EXTENSIONS.test(url.raw)).length,
    sirvViewerCount: sirvViewer.containers.length,
    sirvViewerAssetCount: sirvViewer.assets.length,
    sirvScriptCount: sirvViewer.scripts.length,
    sirvViewer: {
      containers: sirvViewer.containers,
      assets: sirvViewer.assets,
      scripts: sirvViewer.scripts
    },
    images: imageReports,
    findings,
    summary: summarize(findings)
  };
}

async function loadHtml(target) {
  if (/^https?:\/\//i.test(target)) {
    const response = await fetch(target, {
      headers: {
        "user-agent": "image-optimization-skill-audit/1.0"
      }
    });
    if (!response.ok) {
      throw new Error(`Failed to fetch ${target}: ${response.status} ${response.statusText}`);
    }
    return {
      html: await response.text(),
      baseUrl: target,
      sourceType: "url"
    };
  }

  const absolute = path.resolve(target);
  return {
    html: await fs.readFile(absolute, "utf8"),
    baseUrl: pathToFileURL(absolute).href,
    sourceType: "file"
  };
}

function stripInertMarkup(html) {
  return html
    .replace(/<!--[\s\S]*?-->/g, "")
    .replace(/<noscript\b[\s\S]*?<\/noscript>/gi, "")
    .replace(/<template\b[\s\S]*?<\/template>/gi, "")
    .replace(/(<script\b[^>]*>)[\s\S]*?<\/script>/gi, "$1</script>");
}

function extractElements(html, tagName) {
  const pattern = new RegExp(`<${tagName}\\b[^>]*>`, "gi");
  return html.match(pattern) || [];
}

function extractCssUrls(html, baseUrl) {
  const urls = [];
  const pattern = /url\(\s*(['"]?)(.*?)\1\s*\)/gi;
  let match;

  while ((match = pattern.exec(html))) {
    const raw = decodeHtmlEntities(match[2].trim());
    const resolved = resolveUrl(raw, baseUrl);
    if (resolved) urls.push({ raw, resolved });
  }

  return urls;
}

function parseAttrs(tag) {
  const attrs = {};
  const pattern = /([:@\w.-]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'=<>`]+)))?/g;
  const tagNames = new Set(["div", "img", "link", "script", "source"]);
  let match;

  while ((match = pattern.exec(tag))) {
    const name = match[1].toLowerCase();
    if (tagNames.has(name)) continue;
    attrs[name] = decodeHtmlEntities(match[2] ?? match[3] ?? match[4] ?? "");
  }

  return attrs;
}

function extractSirvViewerState(html, scriptTags, baseUrl) {
  const divs = extractElements(html, "div");
  const parsedDivs = divs.map((tag, index) => ({ tag, index, attrs: parseAttrs(tag) }));
  const hasSirvContainer = parsedDivs.some(({ attrs }) => (attrs.class || "").split(/\s+/).includes("Sirv"));
  const containers = [];
  const assets = [];
  const scripts = scriptTags
    .map((tag) => ({ tag, attrs: parseAttrs(tag) }))
    .filter(({ attrs }) => /scripts\.sirv\.com\/sirvjs\/v3\/sirv\.js/i.test(attrs.src || ""))
    .map(({ tag, attrs }, index) => ({
      index: index + 1,
      src: attrs.src || "",
      resolvedSrc: resolveUrl(attrs.src || "", baseUrl),
      modules: parseSirvScriptModules(attrs.src || "", baseUrl),
      tag: compactTag(tag)
    }));

  parsedDivs.forEach(({ tag, index, attrs }) => {
    const classes = (attrs.class || "").split(/\s+/).filter(Boolean);
    const isSirvContainer = classes.includes("Sirv");
    const src = attrs["data-src"] || attrs["data-bg-src"] || "";
    const assetUrls = splitSirvAssetList(src);
    const assetTypes = assetUrls.map((assetUrl) => inferSirvAssetType(assetUrl, attrs));

    if (isSirvContainer) {
      containers.push({
        index: index + 1,
        src,
        resolvedSrc: assetUrls.map((assetUrl) => resolveUrl(assetUrl, baseUrl)).filter(Boolean),
        assetTypes: [...new Set(assetTypes)],
        options: attrs["data-options"] || "",
        breakpoints: attrs["data-breakpoints"] || "",
        hasDataAlt: Object.hasOwn(attrs, "data-alt"),
        hasStyle: Object.hasOwn(attrs, "style"),
        tag: compactTag(tag)
      });
    }

    if (src && (isSirvContainer || hasSirvContainer || assetUrls.some(isLikelySirvViewerUrl))) {
      assets.push({
        index: index + 1,
        src,
        resolvedSrc: assetUrls.map((assetUrl) => resolveUrl(assetUrl, baseUrl)).filter(Boolean),
        assetTypes: [...new Set(assetTypes)],
        type: attrs["data-type"] || "",
        options: attrs["data-options"] || "",
        hasDataAlt: Object.hasOwn(attrs, "data-alt"),
        tag: compactTag(tag)
      });
    }
  });

  return { containers, assets, scripts };
}

function isLikelySirvViewerUrl(value) {
  if (!value) return false;

  const clean = value.split(/[?#]/)[0].toLowerCase();
  if (/\.(spin|view|glb|gltf|usdz|obj|fbx|stl|blend)$/.test(clean)) return true;
  if (/(^https?:\/\/[^/]*sirv\.com\/|scripts\.sirv\.com|video\.sirv\.com)/i.test(value)) return true;
  return false;
}

function splitSirvAssetList(value) {
  if (!value) return [];
  return value
    .split(",")
    .map((part) => part.trim())
    .filter(Boolean);
}

function parseSirvScriptModules(src, baseUrl) {
  const resolved = resolveUrl(src, baseUrl);
  if (!/^https?:\/\//i.test(resolved || "")) return null;

  const modules = new URL(resolved).searchParams.get("modules");
  if (!modules) return null;
  return modules
    .split(",")
    .map((moduleName) => moduleName.trim())
    .filter(Boolean);
}

function inferSirvAssetType(src, attrs = {}) {
  if ((attrs["data-type"] || "").toLowerCase() === "zoom") return "zoom";
  if ((attrs["data-type"] || "").toLowerCase() === "static") return "static";
  if ((attrs["data-bg-src"] || "") === src) return "background";

  const clean = src.split(/[?#]/)[0].toLowerCase();
  if (/\.spin$/.test(clean)) return "spin";
  if (/\.view$/.test(clean)) return "smart-gallery";
  if (/\.(mp4|m4v|webm|ogg|ogv|mov)$/.test(clean)) return "video";
  if (/(youtube\.com|youtu\.be|vimeo\.com|player\.vimeo\.com)/i.test(src)) return "video";
  if (/\.(glb|gltf|usdz|obj|fbx|stl|blend)$/.test(clean)) return "model";
  if (/\.pdf$/.test(clean)) return "pdf";
  if (IMAGE_EXTENSIONS.test(src)) return "image";
  return "unknown";
}

// HTML spec candidate parsing: a URL ends at whitespace, so commas inside URLs
// (Cloudinary `w_400,q_auto`) are kept; a comma only separates candidates.
function parseSrcset(srcset, baseUrl) {
  const candidates = [];
  const value = srcset || "";
  let pos = 0;

  while (pos < value.length) {
    while (pos < value.length && /[\s,]/.test(value[pos])) pos++;
    if (pos >= value.length) break;

    let start = pos;
    while (pos < value.length && !/\s/.test(value[pos])) pos++;
    let url = value.slice(start, pos);
    let descriptor = "";

    if (url.endsWith(",")) {
      url = url.replace(/,+$/, "");
    } else {
      start = pos;
      while (pos < value.length && value[pos] !== ",") pos++;
      descriptor = value.slice(start, pos).trim();
    }

    const decodedUrl = decodeHtmlEntities(url);
    candidates.push({
      raw: decodedUrl,
      resolved: resolveUrl(decodedUrl, baseUrl),
      descriptor
    });
  }

  return candidates;
}

function detectCdn(url) {
  if (!/^https?:\/\//i.test(url || "")) return null;
  if (SIRV_HOST_RE.test(new URL(url).hostname)) return "sirv";
  return IMAGE_CDNS.find(([, pattern]) => pattern.test(url))?.[0] || null;
}

function requestedWidth(url) {
  if (!url) return null;
  const match =
    url.match(/[?&](?:w|width)=(\d+)(?:&|#|$)/i) ||
    url.match(/[/,]w_(\d+)(?:[,/]|$)/i) ||
    url.match(/\/cdn-cgi\/image\/(?:[^/]*,)?width=(\d+)/i) ||
    url.match(/[?&]im=Resize,width=(\d+)/i);
  return match ? Number(match[1]) : null;
}

function hasWidthDescriptors(candidates) {
  return candidates.some((candidate) => /\d+w$/.test(candidate.descriptor));
}

function resolveUrl(value, baseUrl) {
  if (!value || /^(data|blob|about|javascript):/i.test(value) || value.startsWith("#")) return "";

  try {
    return new URL(value, baseUrl).href;
  } catch {
    return value;
  }
}

function inspectImageMarkup(report, attrs, candidates, index, findings) {
  const label = `img[${report.index}]`;

  if (!report.src && candidates.length === 0) {
    findings.push({
      severity: "warn",
      target: label,
      message: "Image has no `src`, `data-src`, or `srcset`",
      value: compactAttrs(attrs)
    });
  }

  if (!Object.hasOwn(attrs, "alt")) {
    findings.push({
      severity: "warn",
      target: label,
      message: "Image is missing `alt`",
      value: report.src || compactAttrs(attrs)
    });
  }

  if (!report.width || !report.height) {
    findings.push({
      severity: "warn",
      target: label,
      message: "Image is missing width/height; verify CLS is reserved with CSS if intentional",
      value: report.src || compactAttrs(attrs)
    });
  }

  if (hasWidthDescriptors(candidates) && !attrs.sizes) {
    findings.push({
      severity: "warn",
      target: label,
      message: "`srcset` uses width descriptors but image has no `sizes` attribute",
      value: report.src || candidates[0]?.raw || ""
    });
  }

  if (index === 0 && (report.loading || "").toLowerCase() === "lazy") {
    findings.push({
      severity: "error",
      target: label,
      message: "First image is lazy loaded; this is risky if it is the LCP image",
      value: report.src
    });
  }

  if (index === 0 && !/high/i.test(report.fetchpriority || "")) {
    findings.push({
      severity: "info",
      target: label,
      message: "First image has no `fetchpriority=\"high\"`; verify LCP priority another way",
      value: report.src
    });
  }

  // 2x covers DPR 2 screens; `width` may be intrinsic rather than rendered size, so warn, not error.
  const slotWidth = Number(report.width);
  if (!hasWidthDescriptors(candidates) && report.requestedWidth && slotWidth > 0 && report.requestedWidth > slotWidth * 2) {
    findings.push({
      severity: "warn",
      target: label,
      message: `Image URL requests ${report.requestedWidth}px for a ${slotWidth}px \`width\`; add width candidates or a smaller size`,
      value: report.resolvedSrc
    });
  }

  if (report.sirv?.hosted) {
    inspectSirvMarkup(label, report.sirv, findings);
  } else if (!report.cdn && report.resolvedSrc && IMAGE_EXTENSIONS.test(report.resolvedSrc)) {
    findings.push({
      severity: "info",
      target: label,
      message: "Image is not served by a known image CDN; confirm a build step or CDN resizes and converts it",
      value: report.resolvedSrc
    });
  }
}

function inspectSirvUrl(value) {
  if (!/^https?:\/\//i.test(value || "")) return null;

  const url = new URL(value);
  const hosted = SIRV_HOST_RE.test(url.hostname);
  if (!hosted) return null;

  const params = url.searchParams;
  const format = params.get("format");
  const scaleOption = params.get("scale.option");

  return {
    hosted,
    hostname: url.hostname,
    hasSizing: ["w", "h", "s", "thumbnail"].some((param) => params.has(param)),
    hasProfile: params.has("profile"),
    hasQuality: params.has("q"),
    format,
    scaleOption,
    query: url.search
  };
}

function inspectSirvMarkup(label, sirv, findings) {
  if (!sirv.hasSizing && !sirv.hasProfile) {
    findings.push({
      severity: "warn",
      target: label,
      message: "Sirv image has no size parameter or profile; it may serve an oversized master",
      value: sirv.query || "(no query)"
    });
  }

  if (/^(avif|webp)$/i.test(sirv.format || "")) {
    findings.push({
      severity: "info",
      target: label,
      message: "Sirv image forces a modern format; verify fallback/negotiation is intentional",
      value: `format=${sirv.format}`
    });
  }

  if ((sirv.scaleOption || "").toLowerCase() === "ignore") {
    findings.push({
      severity: "warn",
      target: label,
      message: "Sirv `scale.option=ignore` can distort images",
      value: sirv.query
    });
  }
}

function inspectSirvViewerMarkup(sirvViewer, findings) {
  if (sirvViewer.containers.length === 0 && sirvViewer.assets.length === 0) return;

  if (sirvViewer.scripts.length === 0) {
    findings.push({
      severity: "error",
      target: "sirv-media-viewer",
      message: "Sirv `data-src`/viewer markup found but no Sirv JS script was detected",
      value: "Expected https://scripts.sirv.com/sirvjs/v3/sirv.js"
    });
  }

  for (const script of sirvViewer.scripts) {
    if (!script.modules) {
      findings.push({
        severity: "info",
        target: "sirv-media-viewer",
        message: "Full Sirv JS is loaded; consider a documented `modules` bundle if this page only needs a narrow viewer feature set",
        value: script.src
      });
    } else {
      findings.push({
        severity: "info",
        target: "sirv-media-viewer",
        message: "Sirv JS uses a module-limited bundle; verify modules cover every viewer asset type",
        value: script.modules.join(", ")
      });
    }
  }

  const firstContainer = sirvViewer.containers[0];
  if (firstContainer && !/autostart\s*:\s*created/i.test(firstContainer.options)) {
    findings.push({
      severity: "info",
      target: `sirv-viewer[${firstContainer.index}]`,
      message: "First Sirv viewer uses default lazy initialization; use `autostart:created` if it is above the fold or likely LCP",
      value: firstContainer.tag
    });
  }

  for (const container of sirvViewer.containers) {
    if (!container.hasStyle && !/layout\.aspectRatio/i.test(container.options)) {
      findings.push({
        severity: "info",
        target: `sirv-viewer[${container.index}]`,
        message: "Sirv viewer has no inline style or `layout.aspectRatio`; verify CSS reserves stable space to prevent CLS",
        value: container.tag
      });
    }

    if (!container.src && !container.breakpoints && sirvViewer.assets.length === 0) {
      findings.push({
        severity: "warn",
        target: `sirv-viewer[${container.index}]`,
        message: "Sirv viewer container has no direct `data-src`; verify child assets are present after rendering",
        value: container.tag
      });
    }
  }

  for (const asset of sirvViewer.assets) {
    if (!asset.hasDataAlt && asset.assetTypes.some((type) => ["image", "zoom", "spin", "video", "model", "smart-gallery", "pdf"].includes(type))) {
      findings.push({
        severity: "info",
        target: `sirv-asset[${asset.index}]`,
        message: "Sirv viewer asset has no `data-alt`; verify Sirv file description metadata supplies accessible text",
        value: asset.tag
      });
    }

    if (asset.assetTypes.includes("unknown")) {
      findings.push({
        severity: "info",
        target: `sirv-asset[${asset.index}]`,
        message: "Could not infer Sirv viewer asset type; verify the URL is supported by Sirv Media Viewer",
        value: asset.src
      });
    }
  }
}

async function addHeadFindings(imageReports, sirvViewer, findings) {
  const imageUrls = imageReports.map((image) => image.resolvedSrc);
  const viewerUrls = sirvViewer.assets.flatMap((asset) => asset.resolvedSrc || []);
  const urls = [...new Set([...imageUrls, ...viewerUrls].filter((src) => /^https?:\/\//i.test(src)))];

  for (const url of urls) {
    try {
      const response = await fetch(url, { method: "HEAD" });
      const contentType = response.headers.get("content-type") || "";
      const contentLength = Number(response.headers.get("content-length") || 0);
      const isViewerMedia = sirvViewer.assets.some((asset) => (asset.resolvedSrc || []).includes(url));

      if (!response.ok) {
        findings.push({
          severity: "error",
          target: "http",
          message: `Image HEAD returned ${response.status}`,
          value: url
        });
      }

      if (contentType && !isViewerMedia && !contentType.startsWith("image/")) {
        findings.push({
          severity: "warn",
          target: "http",
          message: `Image URL returned non-image content type: ${contentType}`,
          value: url
        });
      }

      if (contentLength > 500_000) {
        findings.push({
          severity: "warn",
          target: "http",
          message: `Image response is large: ${formatBytes(contentLength)}`,
          value: url
        });
      }
    } catch (error) {
      findings.push({
        severity: "warn",
        target: "http",
        message: `Could not HEAD image: ${error.message}`,
        value: url
      });
    }
  }
}

function summarize(findings) {
  return findings.reduce(
    (summary, finding) => {
      summary[finding.severity] = (summary[finding.severity] || 0) + 1;
      return summary;
    },
    { error: 0, warn: 0, info: 0 }
  );
}

function printMarkdown(reports) {
  console.log("# Image Audit\n");

  for (const report of reports) {
    console.log(`## ${report.target}`);
    console.log(`- Source: ${report.sourceType}`);
    console.log(`- Images: ${report.imageCount}`);
    console.log(`- Source elements: ${report.sourceCount}`);
    console.log(`- Image preloads: ${report.preloadCount}`);
    console.log(`- CSS image URLs: ${report.cssImageCount}`);
    console.log(`- Sirv viewer containers: ${report.sirvViewerCount}`);
    console.log(`- Sirv viewer assets: ${report.sirvViewerAssetCount}`);
    console.log(`- Sirv JS scripts: ${report.sirvScriptCount}`);
    console.log(`- Findings: ${report.summary.error} error, ${report.summary.warn} warn, ${report.summary.info} info`);

    if (report.findings.length === 0) {
      console.log("\nNo obvious image markup issues found.\n");
      continue;
    }

    console.log("\n### Findings");
    for (const finding of report.findings) {
      console.log(`- [${finding.severity}] ${finding.target}: ${finding.message}`);
      if (finding.value) console.log(`  ${finding.value}`);
    }
    console.log("");
  }
}

function compactTag(tag) {
  return tag.replace(/\s+/g, " ").trim().slice(0, 240);
}

function compactAttrs(attrs) {
  return Object.entries(attrs)
    .map(([name, value]) => `${name}=${JSON.stringify(value)}`)
    .join(" ")
    .slice(0, 240);
}

function decodeHtmlEntities(value) {
  return value
    .replace(/&amp;/g, "&")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">");
}

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
