"use strict";

// card.png: the kit on one picture, to look at or to share. The site's name
// and address, its first screen, its logos as cut, its colors with their hex
// values and its fonts, drawn in a tab of its own from data the kit already
// holds: no request goes out.

const fs = require("fs");
const path = require("path");
const { connect } = require("./chrome");
const { capture, resetPictureWait } = require("./page");

const CARD = { width: 1600, height: 900, scale: 1.5 };

const escape = (text) => String(text).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);

// Black or white text, whichever reads better on the swatch.
function inkOn(hex) {
  const [r, g, b] = [1, 3, 5].map((k) => parseInt(hex.slice(k, k + 2), 16) / 255).map((v) => (v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4));
  return 0.2126 * r + 0.7152 * g + 0.0722 * b > 0.4 ? "#111111" : "#ffffff";
}

const ROLE_NAMES = { button: "Buttons", logo: "Logo", heading: "Headings", link: "Links", header: "Header", footer: "Footer", surface: "Surface" };

function cardHtml(kit, dir) {
  const image = (file) => `data:image/png;base64,${fs.readFileSync(path.join(dir, file)).toString("base64")}`;
  const host = new URL(kit.url).hostname.replace(/^www\./, "");
  const logos = kit.logos.slice(0, 3);
  const colors = kit.colors.slice(0, 6);
  const screen = kit.screenshots[0];
  const fonts = [kit.fonts.heading && `Headings: ${kit.fonts.heading}`, kit.fonts.body && `Body: ${kit.fonts.body}`].filter(Boolean);
  return `<!doctype html><html><head><meta charset="utf-8"><style>
  *{box-sizing:border-box;margin:0}
  html,body{width:${CARD.width}px;height:${CARD.height}px;background:#f4f3ef;color:#111;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
  .card{display:flex;flex-direction:column;height:100%;padding:56px 64px 44px}
  .top{display:flex;align-items:baseline;gap:20px}
  h1{font-size:56px;line-height:1;letter-spacing:-0.02em;font-weight:700}
  .host{font-size:24px;color:#6b6a66}
  .body{flex:1;display:flex;align-items:center;gap:48px;margin-top:24px;min-height:0}
  .screen{flex:0 0 ${screen ? "58%" : "0"};display:${screen ? "block" : "none"}}
  .screen img{width:100%;border-radius:14px;box-shadow:0 18px 50px rgba(0,0,0,.16);display:block}
  .facts{flex:1;display:flex;flex-direction:column;gap:30px;min-width:0}
  .label{font-size:15px;letter-spacing:.08em;text-transform:uppercase;color:#8a8984;margin-bottom:12px;font-weight:600}
  .logos{display:flex;flex-wrap:wrap;gap:12px}
  .logos img{height:76px;max-width:100%;border-radius:10px;border:1px solid rgba(0,0,0,.08);display:block}
  .none{font-size:20px;color:#8a8984}
  .swatches{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
  .swatch{height:84px;border-radius:10px;padding:12px 14px;display:flex;flex-direction:column;justify-content:space-between;border:1px solid rgba(0,0,0,.08)}
  .swatch b{font:600 18px ui-monospace,SFMono-Regular,Menlo,monospace}
  .swatch span{font-size:14px;opacity:.85}
  .fonts{font-size:22px;line-height:1.5}
  .foot{margin-top:28px;font:500 20px ui-monospace,SFMono-Regular,Menlo,monospace;color:#6b6a66}
  </style></head><body><div class="card">
  <div class="top"><h1>${escape(kit.name)}</h1><div class="host">${escape(host)}</div></div>
  <div class="body">
    <div class="screen">${screen ? `<img src="${image(screen.file)}">` : ""}</div>
    <div class="facts">
      <div><div class="label">Logos</div>${logos.length ? `<div class="logos">${logos.map((logo) => `<img src="${image(logo.file)}">`).join("")}</div>` : `<div class="none">No logo found on the page</div>`}</div>
      <div><div class="label">Colors</div>${colors.length ? `<div class="swatches">${colors.map((color) => `<div class="swatch" style="background:${color.hex};color:${inkOn(color.hex)}"><b>${color.hex}</b><span>${escape(ROLE_NAMES[color.role] || color.role)}</span></div>`).join("")}</div>` : `<div class="none">No solid colors found</div>`}</div>
      <div><div class="label">Fonts</div><div class="fonts">${fonts.length ? fonts.map(escape).join("<br>") : "Not found"}</div></div>
    </div>
  </div>
  <div class="foot">github.com/EminBudak/easybrandkit</div>
  </div></body></html>`;
}

// Drawn in a new tab of the browser the kit was read with.
async function renderCard(base, kit, dir) {
  const res = await fetch(`${base}/json/new?about:blank`, { method: "PUT", signal: AbortSignal.timeout(10_000) });
  const target = await res.json();
  const cdp = await connect(target.webSocketDebuggerUrl);
  try {
    await cdp.send("Page.enable");
    await cdp.send("Emulation.setDeviceMetricsOverride", { width: CARD.width, height: CARD.height, deviceScaleFactor: 1, mobile: false });
    const { frameTree } = await cdp.send("Page.getFrameTree");
    await cdp.send("Page.setDocumentContent", { frameId: frameTree.frame.id, html: cardHtml(kit, dir) });
    resetPictureWait();
    const shot = await capture(cdp, 0, 0, CARD.width, CARD.height, CARD.scale, false);
    const png = Buffer.from(shot.data || "", "base64");
    if (png.length < 24) return null;
    fs.writeFileSync(path.join(dir, "card.png"), png);
    return { file: "card.png", width: png.readUInt32BE(16), height: png.readUInt32BE(20) };
  } finally {
    cdp.close();
    await fetch(`${base}/json/close/${target.id}`, { signal: AbortSignal.timeout(5_000) }).catch(() => {});
  }
}

module.exports = { renderCard, cardHtml, inkOn };
