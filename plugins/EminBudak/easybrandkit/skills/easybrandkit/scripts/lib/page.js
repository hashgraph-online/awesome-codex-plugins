"use strict";

// Reading a page as the browser draws it: its size, a walk from top to
// bottom so lazy and scroll-revealed parts render, floating overlays hidden,
// and screenshots that wait for their pictures.

const { timeLeft, sleep } = require("./time");

const STEP_PAUSE_MS = 350;

async function metrics(cdp) {
  const m = await cdp.send("Page.getLayoutMetrics");
  const viewport = m.cssLayoutViewport || m.layoutViewport || {};
  const visual = m.cssVisualViewport || m.visualViewport || {};
  const content = m.cssContentSize || m.contentSize || {};
  return {
    width: Math.max(1, Math.floor(viewport.clientWidth || 0)),
    viewportHeight: Math.max(1, Math.floor(viewport.clientHeight || 0)),
    scrollY: Math.max(0, Math.floor(visual.pageY || 0)),
    height: Math.max(1, Math.ceil(content.height || 0)),
  };
}

// What the nearest of an element and those above it says, by what own says
// of each one (something truthy), asked once per element: a page can nest its
// elements as deep as it likes, and a walk up from each of them would then
// hold the one thread that answers Ctrl-C and the run's own time limit.
function nearest(parents, own) {
  const known = new Map();
  return (start) => {
    const passed = [];
    let said;
    for (let at = start; at >= 0; at = parents[at]) {
      if (known.has(at)) {
        said = known.get(at);
        break;
      }
      passed.push(at);
      said = own(at);
      if (said) break;
    }
    for (const at of passed) known.set(at, said);
    return said;
  };
}

function wheel(cdp, x, y, deltaY) {
  return cdp.send("Input.dispatchMouseEvent", { type: "mouseWheel", x, y, deltaX: 0, deltaY });
}

// Wheel down a screen at a time until the bottom, re-reading the height so
// lazily loaded content extends the walk. If the page does not move (the
// pointer sits on an inner scroller), retry once from the left edge. Then
// back to the top in one turn of the wheel.
async function walk(cdp) {
  let m = await metrics(cdp);
  const step = Math.max(200, Math.floor(m.viewportHeight * 0.8));
  const midY = Math.floor(m.viewportHeight / 2);
  for (let i = 0; i < 80 && timeLeft() > 20_000; i++) {
    if (m.scrollY + m.viewportHeight >= m.height - 2) break;
    const before = m.scrollY;
    await wheel(cdp, Math.floor(m.width / 2), midY, step);
    await sleep(STEP_PAUSE_MS);
    m = await metrics(cdp);
    if (m.scrollY === before) {
      await wheel(cdp, 8, midY, step);
      await sleep(STEP_PAUSE_MS);
      m = await metrics(cdp);
      if (m.scrollY === before) break;
    }
  }
  await sleep(800);
  await wheel(cdp, 8, midY, -(m.height + m.viewportHeight));
  await sleep(600);
}

// A single-page app can show a bare loading screen for a long time (25 s on
// one site, in a fresh browser). The page is looked at once in any case, and
// then, up to 30 s while the run has the time for it, until it is taller than
// the screen or has a link or an image. Says "content" once the page shows
// some, "loader" when it is still a bare loader after the whole wait, and
// "no time" when the run had no time left to wait that long.
async function waitForContent(cdp) {
  for (let waited = 0; ; waited += 1_000) {
    const m = await metrics(cdp);
    if (m.height > m.viewportHeight + 50) return "content";
    const snap = await cdp.send("DOMSnapshot.captureSnapshot", { computedStyles: [] });
    const names = (((snap.documents || [])[0] || {}).nodes || {}).nodeName || [];
    if (names.some((i) => snap.strings[i] === "A" || snap.strings[i] === "IMG")) return "content";
    if (waited >= 30_000) return "loader";
    if (timeLeft() <= 50_000) return "no time";
    await sleep(1_000);
  }
}

// Floating overlays sit over the content: a promo box, a chat bubble, a
// cookie bar, a modal backdrop. Hide every position:fixed element except the
// page's own chrome: a short bar on the top edge (navigation) and a tall,
// narrow bar on the left or right edge (an app's sidebar). Each one takes two
// calls to the browser, so no more are hidden than any page has, and none
// once the run has nearly used up its time.
const MANY_OVERLAYS = 500;
function isPageChrome([x, y, width, height], viewportWidth, viewportHeight) {
  const topBar = y <= 20 && height <= viewportHeight * 0.3;
  const sideBar =
    height >= viewportHeight * 0.5 &&
    width <= viewportWidth * 0.35 &&
    (x <= 2 || x + width >= viewportWidth - 2);
  return topBar || sideBar;
}

async function hideOverlays(cdp, viewportWidth, viewportHeight) {
  const snap = await cdp.send("DOMSnapshot.captureSnapshot", { computedStyles: ["position"] });
  const doc = (snap.documents || [])[0];
  if (!doc || !doc.layout) return 0;
  const strings = snap.strings || [];
  const backendIds = [];
  const fixed = new Map();
  doc.layout.nodeIndex.forEach((nodeIndex, i) => {
    if (strings[(doc.layout.styles[i] || [])[0]] === "fixed") fixed.set(nodeIndex, doc.layout.bounds[i] || []);
  });
  // A fixed box of no size still shows what overflows it: a shop's cookie
  // banner sat in a 0 px wide fixed wrapper. Such a box is measured by what
  // it holds.
  const held = new Map();
  const parentOf = doc.nodes.parentIndex || [];
  // One above the node index, so that the first node counts as something.
  const fixedAbove = nearest(parentOf, (n) => (fixed.has(n) ? n + 1 : 0));
  doc.layout.nodeIndex.forEach((nodeIndex, i) => {
    const [x, y, w, h] = doc.layout.bounds[i] || [];
    if (!(w > 0 && h > 0)) return;
    const n = (fixedAbove(parentOf[nodeIndex]) || 0) - 1;
    if (n < 0) return;
    const [x0, y0, x1, y1] = held.get(n) || [x, y, x + w, y + h];
    held.set(n, [Math.min(x0, x), Math.min(y0, y), Math.max(x1, x + w), Math.max(y1, y + h)]);
  });
  for (const [nodeIndex, own] of fixed) {
    const box = held.get(nodeIndex);
    const bounds = own[2] > 0 && own[3] > 0 ? own : box ? [box[0], box[1], box[2] - box[0], box[3] - box[1]] : null;
    if (bounds && !isPageChrome(bounds, viewportWidth, viewportHeight)) {
      backendIds.push(doc.nodes.backendNodeId[nodeIndex]);
    }
  }
  if (backendIds.length === 0) return 0;
  await cdp.send("DOM.getDocument", { depth: 0 });
  const { nodeIds = [] } = await cdp.send("DOM.pushNodesByBackendIdsToFrontend", {
    backendNodeIds: backendIds.slice(0, MANY_OVERLAYS),
  });
  let hidden = 0;
  for (const nodeId of nodeIds) {
    if (timeLeft() < 5_000) break;
    if (!nodeId) continue;
    try {
      const { attributes = [] } = await cdp.send("DOM.getAttributes", { nodeId });
      const at = attributes.indexOf("style");
      const style = at >= 0 && at % 2 === 0 ? attributes[at + 1] : "";
      await cdp.send("DOM.setAttributeValue", {
        nodeId,
        name: "style",
        value: `${style};display:none !important`,
      });
      hidden++;
    } catch {
      // A node that vanished meanwhile needs no hiding.
    }
  }
  await sleep(300);
  return hidden;
}

// Pictures still on their way when a capture starts: a capture first waits
// until every video in its frame shows a picture, every picture in it has
// loaded and no fade-in in it is still running, 8 s at most for the page.
// This only reads the page.
const PICTURE_WAIT_MS = 8_000;
let pictureWaitLeft = PICTURE_WAIT_MS;
const PENDING_PICTURES = `(clip) => {
  const inFrame = (r) => r.width >= 16 && r.height >= 16 &&
    r.left + scrollX < clip.x + clip.width && r.right + scrollX > clip.x &&
    r.top + scrollY < clip.y + clip.height && r.bottom + scrollY > clip.y;
  const shown = (el) => { const s = getComputedStyle(el); return s.display !== "none" && s.visibility !== "hidden"; };
  let pending = 0;
  for (const el of document.querySelectorAll("video, img")) {
    if (!inFrame(el.getBoundingClientRect()) || !shown(el)) continue;
    if (el.tagName === "VIDEO") {
      // A video with a picture, a poster, an error or no source is done.
      if (el.readyState >= 2 || el.poster || el.error || el.networkState === 3) continue;
      if (el.currentSrc || el.getAttribute("src") || el.querySelector("source[src]")) pending++;
    } else if (!el.complete || !(el.currentSrc || el.getAttribute("src"))) {
      // Still loading, or a lazy picture whose address the page sets once it sees it.
      pending++;
    }
  }
  for (const animation of document.getAnimations()) {
    const effect = animation.effect;
    const timing = effect && effect.getComputedTiming ? effect.getComputedTiming() : null;
    // A fade-in ends; a spinner, a marquee or a carousel's loop does not.
    if (animation.playState !== "running" || !timing || !(timing.endTime <= 3000)) continue;
    if (effect.target && effect.target.getBoundingClientRect && inFrame(effect.target.getBoundingClientRect())) pending++;
  }
  return pending;
}`;

function resetPictureWait() {
  pictureWaitLeft = PICTURE_WAIT_MS;
}

async function waitForPictures(cdp, clip) {
  const expression = `(${PENDING_PICTURES})(${JSON.stringify(clip)})`;
  let waited = false;
  while (pictureWaitLeft > 0 && timeLeft() > 30_000) {
    const pending = await cdp
      .send("Runtime.evaluate", { expression, returnByValue: true }, 5_000)
      .then(({ result }) => Number(result && result.value) || 0, () => 0);
    if (!pending) break;
    waited = true;
    await sleep(250);
    pictureWaitLeft -= 250;
  }
  // The last picture to arrive is painted on the next frame.
  if (waited) await sleep(200);
}

// A frame that lies on the screen is captured as the screen shows it: drawn
// again beyond the viewport, videos and some pictures came out as blank
// boxes. Only a frame that does not fit on the screen (a logo down in the
// footer) is drawn beyond it.
async function capture(cdp, x, y, width, height, scale = 1, beyondViewport = true) {
  await waitForPictures(cdp, { x, y, width, height });
  if (beyondViewport) {
    const m = await metrics(cdp);
    const onScreen = x >= 0 && x + width <= m.width + 1 && y >= m.scrollY - 1 && y + height <= m.scrollY + m.viewportHeight + 1;
    if (onScreen) beyondViewport = false;
  }
  return cdp.send(
    "Page.captureScreenshot",
    { format: "png", captureBeyondViewport: beyondViewport, clip: { x, y, width, height, scale } },
    60_000,
  );
}

module.exports = { metrics, walk, waitForContent, nearest, isPageChrome, hideOverlays, resetPictureWait, capture };
