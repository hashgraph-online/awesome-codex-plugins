/* viewer.js — render a resolved hyper-pptx deck in the browser and measure it.
 *
 * The page embeds the resolved deck JSON (output of layout.jq) in
 * <script id="pp-deck" type="application/json">. This script turns every slide
 * into an absolutely positioned stage at 1/9525 EMU-to-pixel scale, which is
 * exactly 1280x720 for a 12192000x6858000 EMU canvas.
 *
 * Two jobs:
 *   - paint the slides, so the preview is what PowerPoint will show;
 *   - measure each text box after layout, so a caller can detect overflow the
 *     way a reader would: content taller than its box, or a line wider than it.
 *
 * Result: <body data-pp-result="{...}"> with per-slide, per-shape overflow.
 */
(function () {
  "use strict";

  var EMU = 9525;
  var deck = JSON.parse(document.getElementById("pp-deck").textContent);
  var params = new URLSearchParams(location.search);
  var capture = params.get("capture");
  var only = capture === null ? null : parseInt(capture, 10);

  function px(emu) {
    return emu / EMU;
  }

  function el(tag, cls) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    return node;
  }

  function themeOf(slide) {
    var t = deck.theme;
    if (!slide.dark) {
      return { bg: t.bg, fg: t.fg, muted: t.muted, accent: t.accent, surface: t.surface, line: t.line };
    }
    return { bg: t.darkBg, fg: t.darkFg, muted: t.darkMuted, accent: t.darkAccent,
             surface: t.darkSurface, line: t.line };
  }

  function applyParagraph(p, node, t) {
    node.style.fontSize = px(p.size * 12700) + "px";
    node.style.lineHeight = "1.32";
    node.style.color = "#" + p.color;
    node.style.fontWeight = p.bold ? "700" : "400";
    node.style.marginTop = px((p.spaceBefore || 0) * 12700) + "px";
    if (p.bullet === false) {
      node.style.paddingLeft = px((p.level || 0) * 342900) + "px";
      node.style.textIndent = "0";
    } else if (p.level > 0) {
      node.style.paddingLeft = px(685800) + "px";
      node.style.textIndent = px(-285750) + "px";
    } else {
      node.style.paddingLeft = px(342900) + "px";
      node.style.textIndent = px(-342900) + "px";
    }
    return node;
  }

  function renderText(shape, t, host) {
    var box = el("div", "pp-text");
    box.style.left = px(shape.x) + "px";
    box.style.top = px(shape.y) + "px";
    box.style.width = px(shape.cx) + "px";
    box.style.height = px(shape.cy) + "px";
    box.style.padding = px(shape.inset[1]) + "px " + px(shape.inset[2]) + "px "
      + px(shape.inset[3]) + "px " + px(shape.inset[0]) + "px";
    box.style.textAlign = shape.align === "c" ? "center" : shape.align === "r" ? "right" : "left";
    box.style.display = "flex";
    box.style.flexDirection = "column";
    box.style.justifyContent = shape.anchor === "b" ? "flex-end"
      : shape.anchor === "ctr" ? "center" : "flex-start";
    var inner = el("div", "pp-text-in");
    shape.paragraphs.forEach(function (p) {
      var node = applyParagraph(p, el("div", "pp-p"), t);
      node.textContent = (p.bullet === false ? "" : (p.level > 0 ? "\u2013 " : "\u2022  ")) + p.text;
      inner.appendChild(node);
    });
    box.appendChild(inner);
    box.dataset.shapeId = String(shape.id || "");
    host.appendChild(box);
    return box;
  }

  function renderRect(shape, host) {
    var box = el("div", "pp-rect");
    box.style.left = px(shape.x) + "px";
    box.style.top = px(shape.y) + "px";
    box.style.width = px(shape.cx) + "px";
    box.style.height = px(shape.cy) + "px";
    box.style.background = "#" + shape.fill;
    if (shape.line) box.style.border = "1px solid #" + shape.line;
    if (shape.radius) box.style.borderRadius = px(shape.radius) + "px";
    host.appendChild(box);
  }

  function renderTable(tb, t, host) {
    var wrap = el("div", "pp-table");
    wrap.style.left = px(tb.x) + "px";
    wrap.style.top = px(tb.y) + "px";
    wrap.style.width = px(tb.cx) + "px";
    var table = el("table");
    table.style.width = "100%";
    table.style.borderCollapse = "collapse";
    table.style.fontSize = px(tb.size * 12700) + "px";
    table.style.tableLayout = "fixed";
    var cg = el("colgroup");
    tb.colWidths.forEach(function (w) {
      var c = el("col");
      c.style.width = px(w) + "px";
      cg.appendChild(c);
    });
    table.appendChild(cg);

    var head = el("tr");
    head.style.background = "#" + tb.headerFill;
    tb.header.forEach(function (cellText) {
      var th = el("th");
      th.textContent = cellText;
      th.style.color = "#" + tb.headerColor;
      th.style.fontWeight = "700";
      th.style.padding = "4px 10px";
      th.style.height = px(tb.rowHeights[0]) + "px";
      th.style.textAlign = "left";
      head.appendChild(th);
    });
    table.appendChild(head);

    tb.rows.forEach(function (row, r) {
      var tr = el("tr");
      tr.style.background = "#" + (r % 2 === 1 ? tb.altFill : tb.bodyFill);
      row.forEach(function (cellText) {
        var td = el("td");
        td.textContent = cellText;
        td.style.color = "#" + tb.bodyColor;
        td.style.padding = "4px 10px";
        td.style.height = px(tb.rowHeights[r + 1]) + "px";
        td.style.borderBottom = "1px solid #" + t.line;
        tr.appendChild(td);
      });
      table.appendChild(tr);
    });
    wrap.appendChild(table);
    host.appendChild(wrap);
  }

  function renderChart(ch, t, host) {
    var svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("class", "pp-chart");
    var W = px(ch.cx), H = px(ch.cy);
    svg.setAttribute("width", W);
    svg.setAttribute("height", H);
    svg.style.left = px(ch.x) + "px";
    svg.style.top = px(ch.y) + "px";

    var padL = 56, padR = 24, padT = 16, padB = 44;
    var plotW = W - padL - padR, plotH = H - padT - padB;
    var values = ch.series.reduce(function (acc, s) { return acc.concat(s.values); }, []);
    var maxV = Math.max.apply(null, values.concat([0]));
    var minV = Math.min.apply(null, values.concat([0]));
    if (maxV === minV) maxV = minV + 1;
    var span = maxV - (minV < 0 ? minV : 0);
    var scale = function (v) { return plotH - ((v - (minV < 0 ? minV : 0)) / span) * plotH; };

    function line(x1, y1, x2, y2, color, width) {
      var l = document.createElementNS("http://www.w3.org/2000/svg", "line");
      l.setAttribute("x1", x1); l.setAttribute("y1", y1);
      l.setAttribute("x2", x2); l.setAttribute("y2", y2);
      l.setAttribute("stroke", color);
      l.setAttribute("stroke-width", width || 1);
      svg.appendChild(l);
    }
    function label(x, y, text, anchor, color, size) {
      var tx = document.createElementNS("http://www.w3.org/2000/svg", "text");
      tx.setAttribute("x", x); tx.setAttribute("y", y);
      tx.setAttribute("text-anchor", anchor || "start");
      tx.setAttribute("fill", color);
      tx.setAttribute("font-size", size || 11);
      tx.textContent = text;
      svg.appendChild(tx);
    }

    var ticks = 4;
    for (var i = 0; i <= ticks; i++) {
      var v = (minV < 0 ? minV : 0) + (span / ticks) * i;
      var y = padT + scale(v);
      line(padL, y, padL + plotW, y, "#" + t.line, 1);
      label(padL - 8, y + 4, String(Math.round(v * 10) / 10), "end", "#" + t.muted, 11);
    }

    var cats = ch.categories;
    var slot = plotW / cats.length;
    var nSeries = ch.series.length;

    if (ch.type === "line") {
      ch.series.forEach(function (s, si) {
        var pts = s.values.map(function (v, ci) {
          return (padL + slot * (ci + 0.5)) + "," + (padT + scale(v));
        }).join(" ");
        var poly = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
        poly.setAttribute("points", pts);
        poly.setAttribute("fill", "none");
        poly.setAttribute("stroke", "#" + ch.colors[si % ch.colors.length]);
        poly.setAttribute("stroke-width", "2.5");
        svg.appendChild(poly);
        s.values.forEach(function (v, ci) {
          var c = document.createElementNS("http://www.w3.org/2000/svg", "circle");
          c.setAttribute("cx", padL + slot * (ci + 0.5));
          c.setAttribute("cy", padT + scale(v));
          c.setAttribute("r", 3.5);
          c.setAttribute("fill", "#" + ch.colors[si % ch.colors.length]);
          svg.appendChild(c);
        });
      });
    } else if (ch.type === "pie") {
      var s0 = ch.series[0];
      var total = s0.values.reduce(function (a, b) { return a + b; }, 0) || 1;
      var cx = padL + plotW / 2, cy = padT + plotH / 2;
      var r = Math.min(plotW, plotH) / 2 - 8;
      var start = -Math.PI / 2;
      s0.values.forEach(function (v, ci) {
        var ang = (v / total) * Math.PI * 2;
        var path = document.createElementNS("http://www.w3.org/2000/svg", "path");
        var x1 = cx + r * Math.cos(start), y1 = cy + r * Math.sin(start);
        var x2 = cx + r * Math.cos(start + ang), y2 = cy + r * Math.sin(start + ang);
        var large = ang > Math.PI ? 1 : 0;
        path.setAttribute("d", "M " + cx + " " + cy + " L " + x1 + " " + y1
          + " A " + r + " " + r + " 0 " + large + " 1 " + x2 + " " + y2 + " Z");
        path.setAttribute("fill", "#" + ch.colors[ci % ch.colors.length]);
        svg.appendChild(path);
        start += ang;
      });
    } else {
      var bw = Math.min(110, (slot * 0.5) / nSeries);
      ch.series.forEach(function (s, si) {
        s.values.forEach(function (v, ci) {
          var base = padT + scale(0);
          var top = padT + scale(v);
          var x = padL + slot * ci + slot / 2 - (bw * nSeries) / 2 + bw * si;
          var rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
          rect.setAttribute("x", x);
          rect.setAttribute("y", Math.min(top, base));
          rect.setAttribute("width", bw - 2);
          rect.setAttribute("height", Math.max(1, Math.abs(base - top)));
          rect.setAttribute("fill", "#" + ch.colors[si % ch.colors.length]);
          svg.appendChild(rect);
        });
      });
    }

    cats.forEach(function (c, ci) {
      label(padL + slot * (ci + 0.5), H - padB + 18, c, "middle", "#" + t.muted, 11);
    });

    if (nSeries > 1) {
      var ly = H - 12;
      var lx = padL;
      ch.series.forEach(function (s, si) {
        var sw = document.createElementNS("http://www.w3.org/2000/svg", "rect");
        sw.setAttribute("x", lx);
        sw.setAttribute("y", ly - 8);
        sw.setAttribute("width", 10);
        sw.setAttribute("height", 10);
        sw.setAttribute("fill", "#" + ch.colors[si % ch.colors.length]);
        svg.appendChild(sw);
        label(lx + 14, ly, s.name, "start", "#" + t.fg, 11);
        lx += 14 + s.name.length * 7 + 16;
      });
    }

    host.appendChild(svg);
  }

  function renderImage(img, host) {
    var box = el("div", "pp-image");
    box.style.left = px(img.x) + "px";
    box.style.top = px(img.y) + "px";
    box.style.width = px(img.cx) + "px";
    box.style.height = px(img.cy) + "px";
    box.style.background = "url('" + img.path.replace(/'/g, "%27") + "') center/cover no-repeat";
    host.appendChild(box);
  }

  function buildSlide(slide) {
    var t = themeOf(slide);
    var stage = el("section", "pp-slide");
    stage.dataset.index = String(slide.index);
    stage.style.width = px(deck.size.w) + "px";
    stage.style.height = px(deck.size.h) + "px";
    stage.style.background = "#" + t.bg;
    stage.style.fontFamily = '"' + deck.theme.fonts.eastAsian + '", "' + deck.theme.fonts.latin + '", sans-serif';

    slide.shapes.forEach(function (shape) {
      if (shape.type === "rect") renderRect(shape, stage);
      else renderText(shape, t, stage);
    });
    if (slide.table) renderTable(slide.table, t, stage);
    if (slide.chart) renderChart(slide.chart, t, stage);
    if (slide.image) renderImage(slide.image, stage);

    // The footer and page number arrive as ordinary text shapes from the
    // layout, so they are not drawn here.
    return stage;
  }

  function measure() {
    var report = { slides: [], size: { w: px(deck.size.w), h: px(deck.size.h) } };
    var slides = document.querySelectorAll(".pp-slide");
    slides.forEach(function (stage) {
      var idx = parseInt(stage.dataset.index, 10);
      var entry = { index: idx, kind: "", overflow: [], emptyText: [], outside: [] };
      if (deck.slides[idx]) entry.kind = deck.slides[idx].kind;
      var limitW = parseFloat(stage.style.width);
      var limitH = parseFloat(stage.style.height);
      stage.querySelectorAll(".pp-text").forEach(function (box) {
        var inner = box.querySelector(".pp-text-in");
        var style = getComputedStyle(box);
        var availH = box.clientHeight - parseFloat(style.paddingTop) - parseFloat(style.paddingBottom);
        var availW = box.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight);
        var needH = inner.scrollHeight;
        var needW = inner.scrollWidth;
        var text = (inner.textContent || "").trim();
        if (!text) entry.emptyText.push({ shape: box.dataset.shapeId });
        if (needH > availH + 1 || needW > availW + 1) {
          entry.overflow.push({
            shape: box.dataset.shapeId,
            text: text.slice(0, 48),
            needH: needH, availH: availH,
            needW: needW, availW: availW
          });
        }
        var r = box.getBoundingClientRect();
        var s = stage.getBoundingClientRect();
        if (r.left < s.left - 1 || r.top < s.top - 1
            || r.right > s.right + 1 || r.bottom > s.bottom + 1) {
          entry.outside.push({ shape: box.dataset.shapeId, text: text.slice(0, 32) });
        }
      });
      report.slides.push(entry);
    });
    report.ok = report.slides.every(function (s) {
      return s.overflow.length === 0 && s.outside.length === 0;
    });
    return report;
  }

  var root = document.getElementById("pp-root");
  deck.slides.forEach(function (slide) {
    var stage = buildSlide(slide);
    if (only !== null && slide.index !== only) stage.style.display = "none";
    root.appendChild(stage);
  });

  if (only !== null) {
    document.body.classList.add("pp-capture");
    document.title = "slide " + (only + 1);
  }

  requestAnimationFrame(function () {
    var report = measure();
    document.body.dataset.ppResult = JSON.stringify(report);
    document.body.dataset.ppReady = "1";
  });
})();
