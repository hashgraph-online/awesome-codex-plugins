/* dom_boxes.js: list the text blocks and cards in the current page, in CSS pixels, for check_clutter.py.
 *
 * check_clutter.py --dom injects this file and calls it at each sample time. You can also paste it into
 * a browser console, or run it from Puppeteer or Playwright after seeking your timeline, and save the
 * result as the JSON that check_clutter.py --boxes reads:
 *
 *   window.b2mCollectBoxes()  ->  [{ id, kind: "text" | "card", x, y, w, h, text }, ...]
 *
 * A text block is a leaf block-level element that has visible text. Its box is the tight rectangle around
 * the text itself (not the whole block), so a wide empty block does not count as crowding.
 * A card is a box with its own fill, gradient, border or shadow that holds text, is at least 40 px each
 * way and is not the whole frame (a full-frame backdrop is not a card).
 * Hidden elements (display none, visibility hidden, effective opacity under 5%) are skipped.
 */
(function () {
  function effectiveOpacity(el) {
    var o = 1;
    for (var n = el; n && n.nodeType === 1; n = n.parentElement) {
      var cs = getComputedStyle(n);
      if (cs.display === 'none' || cs.visibility === 'hidden') return 0;
      o *= parseFloat(cs.opacity);
    }
    return o;
  }
  function isLeafBlock(el, cs) {
    if (cs.display === 'inline' || cs.display === 'contents') return false;
    if (!(el.textContent || '').trim()) return false;
    for (var c = el.firstElementChild; c; c = c.nextElementSibling) {
      var d = getComputedStyle(c).display;
      if (d !== 'inline' && d !== 'none' && d !== 'contents') return false;
    }
    return true;
  }
  function textRect(el) {
    var range = document.createRange();
    range.selectNodeContents(el);
    var x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    Array.prototype.forEach.call(range.getClientRects(), function (r) {
      if (r.width < 1 || r.height < 1) return;
      x0 = Math.min(x0, r.left); y0 = Math.min(y0, r.top);
      x1 = Math.max(x1, r.right); y1 = Math.max(y1, r.bottom);
    });
    return x1 > x0 ? { x: x0, y: y0, w: x1 - x0, h: y1 - y0 } : null;
  }
  function paintsAsCard(cs) {
    var bg = cs.backgroundColor.match(/rgba?\(([^)]+)\)/);
    var alpha = bg ? (bg[1].split(',').length > 3 ? parseFloat(bg[1].split(',')[3]) : 1) : 0;
    var border = parseFloat(cs.borderTopWidth) > 0 && cs.borderTopStyle !== 'none' && cs.borderTopColor !== 'transparent';
    return alpha > 0.05 || cs.backgroundImage !== 'none' || cs.boxShadow !== 'none' || border;
  }
  function label(el, i) {
    return el.id || (el.getAttribute('data-id')) || (el.tagName.toLowerCase() + '#' + i);
  }
  window.b2mCollectBoxes = function () {
    var out = [], all = document.body.getElementsByTagName('*');
    var vw = window.innerWidth, vh = window.innerHeight;
    for (var i = 0; i < all.length; i++) {
      var el = all[i], cs = getComputedStyle(el);
      if (/^(SCRIPT|STYLE|SVG|CANVAS|VIDEO|AUDIO|IMG)$/i.test(el.tagName) || el.closest('svg') || effectiveOpacity(el) < 0.05) continue;
      if (isLeafBlock(el, cs)) {
        var tr = textRect(el);
        if (tr) out.push({ id: label(el, i), kind: 'text', x: tr.x, y: tr.y, w: tr.w, h: tr.h, text: el.textContent.trim().slice(0, 40) });
      }
      var r = el.getBoundingClientRect();
      var holdsText = (el.textContent || '').trim().length > 0;
      if (r.width >= 40 && r.height >= 40 && r.width * r.height < 0.95 * vw * vh && holdsText && paintsAsCard(cs)) {
        out.push({ id: label(el, i), kind: 'card', x: r.left, y: r.top, w: r.width, h: r.height });
      }
    }
    return out;
  };
})();
