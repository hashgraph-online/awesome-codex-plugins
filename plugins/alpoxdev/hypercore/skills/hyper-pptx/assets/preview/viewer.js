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
 *     way a reader would: content taller than its box, or two text blocks
 *     painted over each other.
 *
 * Charts are drawn from the same cached values the chart part carries, with
 * the same colours and the same number format, so the preview and the .pptx
 * cannot disagree about the picture.
 *
 * Result: <body data-pp-result="{...}"> with per-slide overflow, overlap,
 * outside, and coverage.
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

  function svgEl(tag) {
    return document.createElementNS("http://www.w3.org/2000/svg", tag);
  }

  function themeOf(slide) {
    var t = deck.theme;
    if (!slide.dark) {
      return { bg: t.bg, fg: t.fg, muted: t.muted, accent: t.accent, surface: t.surface, line: t.line };
    }
    return { bg: t.darkBg, fg: t.darkFg, muted: t.darkMuted, accent: t.darkAccent,
             surface: t.darkSurface, line: t.line };
  }

  // -------------------------------------------------------------------------
  // Number formatting
  // -------------------------------------------------------------------------

  // A deck formats axis ticks and data labels with an OOXML format code such as
  // "0.0" or "#,##0원". Only the parts that appear in real decks are honoured:
  // decimals, thousands separators, percent, and a literal suffix.
  function fmtNum(v, code) {
    if (typeof v !== "number" || !isFinite(v)) return String(v);
    if (!code || code === "General") {
      return String(Math.round(v * 1000) / 1000);
    }
    var pct = code.indexOf("%") >= 0;
    var suffix = pct ? "%" : "";
    var body = code.replace(/\[[^\]]*\]/g, "");
    var lit = "";
    var literalMatch = body.match(/"(.*?)"/);
    if (literalMatch) lit = literalMatch[1];
    if (!literalMatch) {
      var tail = body.replace(/[0#,.%\s]/g, "");
      if (tail) lit = tail;
    }
    var dot = body.indexOf(".");
    var dec = 0;
    if (dot >= 0) {
      dec = body.slice(dot + 1).replace(/[^0#]/g, "").length;
    }
    var thousands = body.indexOf(",") >= 0;
    var val = pct ? v * 100 : v;
    var sign = val < 0 ? "-" : "";
    var fixed = Math.abs(val).toFixed(dec);
    var parts = fixed.split(".");
    if (thousands) {
      parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    }
    return sign + parts.join(".") + suffix + lit;
  }

  // -------------------------------------------------------------------------
  // Text
  // -------------------------------------------------------------------------

  function applyParagraph(p, node) {
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

  function renderText(shape, host) {
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
      var node = applyParagraph(p, el("div", "pp-p"));
      node.textContent = (p.bullet === false ? "" : (p.level > 0 ? "\u2013 " : "\u2022  ")) + p.text;
      inner.appendChild(node);
    });
    box.appendChild(inner);
    box.dataset.shapeId = String(shape.id || "");
    if (shape.role) box.dataset.role = String(shape.role);
    host.appendChild(box);
    return box;
  }

  // PowerPoint measures a linear gradient angle counter-clockwise from the
  // positive x axis; CSS measures it clockwise from "to top". 90 - angle maps
  // one to the other, and flipping the sign of the projection keeps a
  // top-to-bottom band (90) pointing down in both.
  // DrawingML measures the gradient vector clockwise from the x axis, so 0 runs
  // left to right and 90 runs top to bottom. CSS measures from "to top", so the
  // two differ by a quarter turn: 0 becomes 90deg, 90 becomes 180deg.
  function cssAngle(deg) {
    return (deg + 90) % 360;
  }

  function renderRect(shape, host) {
    var box = el("div", "pp-rect");
    box.style.left = px(shape.x) + "px";
    box.style.top = px(shape.y) + "px";
    box.style.width = px(shape.cx) + "px";
    box.style.height = px(shape.cy) + "px";
    if (shape.type === "ellipse") box.style.borderRadius = "50%";
    else if (shape.radius) box.style.borderRadius = px(shape.radius) + "px";
    if (shape.gradient) {
      box.style.background = "linear-gradient(" + cssAngle(shape.gradient.angle)
        + "deg, #" + shape.gradient.from + ", #" + shape.gradient.to + ")";
    } else {
      box.style.background = "#" + shape.fill;
    }
    if (shape.alpha) box.style.opacity = String(shape.alpha);
    if (shape.line) box.style.border = "1px solid #" + shape.line;
    host.appendChild(box);
  }

  // -------------------------------------------------------------------------
  // Table
  // -------------------------------------------------------------------------

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

  // -------------------------------------------------------------------------
  // Pictures
  // -------------------------------------------------------------------------

  // The picture geometry is already resolved: x/y/cx/cy is the box, and crop is
  // the fraction of the source that the box hides. Scaling the background so the
  // visible window fills the box reproduces the crop without a second layout.
  function renderImage(img, host) {
    var box = el("div", "pp-image");
    box.style.left = px(img.x) + "px";
    box.style.top = px(img.y) + "px";
    box.style.width = px(img.cx) + "px";
    box.style.height = px(img.cy) + "px";
    var c = img.crop || { l: 0, t: 0, r: 0, b: 0 };
    var visW = Math.max(0.05, 1 - (c.l + c.r) / 100);
    var visH = Math.max(0.05, 1 - (c.t + c.b) / 100);
    var url = "url('" + String(img.path).replace(/'/g, "%27") + "')";
    box.style.backgroundImage = url;
    box.style.backgroundRepeat = "no-repeat";
    if (visW > 0.999 && visH > 0.999) {
      box.style.backgroundSize = "100% 100%";
      box.style.backgroundPosition = "0 0";
    } else {
      // A percentage background-position aligns the same percentage point of
      // the picture with that of the box. To hide l/(l+r) of the width on each
      // side, the visible window starts at l/(l+r) of the picture, so that is
      // the position percentage; 0/0 or 100/100 would pin the wrong edge.
      var pxPct = c.l + c.r > 0 ? (c.l / (c.l + c.r)) * 100 : 0;
      var pyPct = c.t + c.b > 0 ? (c.t / (c.t + c.b)) * 100 : 0;
      box.style.backgroundSize = (100 / visW) + "% " + (100 / visH) + "%";
      box.style.backgroundPosition = pxPct + "% " + pyPct + "%";
    }
    if (img.alt) box.setAttribute("aria-label", img.alt);
    host.appendChild(box);
  }

  // -------------------------------------------------------------------------
  // Chart
  // -------------------------------------------------------------------------

  function seriesValues(ch) {
    var all = [];
    (ch.series || []).forEach(function (s) {
      (s.values || []).forEach(function (v) { all.push(v); });
    });
    return all;
  }

  function niceStep(raw) {
    if (!(raw > 0)) return 1;
    var mag = Math.pow(10, Math.floor(Math.log(raw) / Math.LN10));
    var norm = raw / mag;
    var step = norm <= 1 ? 1 : norm <= 2 ? 2 : norm <= 2.5 ? 2.5 : norm <= 5 ? 5 : 10;
    return step * mag;
  }

  function renderChart(ch, t, host) {
    var W = px(ch.cx), H = px(ch.cy);
    var svg = svgEl("svg");
    svg.setAttribute("class", "pp-chart");
    svg.setAttribute("width", W);
    svg.setAttribute("height", H);
    svg.style.left = px(ch.x) + "px";
    svg.style.top = px(ch.y) + "px";

    var legendPos = ch.legend || "none";
    var hasLegend = legendPos !== "none" && (ch.series || []).length > 1 && ch.type !== "pie";
    var axisTitle = ch.valueAxisTitle || null;
    var catTitle = ch.categoryAxisTitle || null;
    // A ring has no value axis, so the axis gutter would just push it right of
    // centre. The gutters are therefore per chart type.
    var pieChart = ch.type === "pie" || ch.type === "doughnut";
    var padL = pieChart ? 12 : 76 + (axisTitle ? 26 : 0);
    var padR = 26;
    var padT = 18;
    var padB = pieChart ? 18 : 52 + (catTitle ? 26 : 0) + (hasLegend ? 22 : 0);
    var plotW = Math.max(10, W - padL - padR);
    var plotH = Math.max(10, H - padT - padB);
    var fmt = ch.numberFormat || "General";
    var muted = "#" + t.muted;
    var fg = "#" + t.fg;
    var lineColor = "#" + t.line;
    var isPie = ch.type === "pie" || ch.type === "doughnut";
    var isStacked = ch.type === "stacked" || ch.type === "stackedBar";
    var isHorizontal = ch.type === "bar" || ch.type === "stackedBar";
    var isScatter = ch.type === "scatter";
    var cats = ch.categories || [];
    var series = ch.series || [];
    // A combo draws two chart types over one category axis: bars read the left
    // value axis, the line reads a second one on the right. Splitting them here
    // keeps the drawing blocks below from having to know about the mix.
    var isCombo = ch.type === "combo";
    var barSeries = isCombo
      ? series.filter(function (s) { return (s.as || "bar") !== "line"; })
      : series;
    var lineSeries = isCombo
      ? series.filter(function (s) { return (s.as || "bar") === "line"; })
      : series;
    var colors = (ch.colors || []).map(function (c) { return "#" + c; });
    // The SVG carries pixel coordinates, so its font sizes are CSS pixels, not
    // points. 11px reads as 8pt next to 18pt body text; 16px is the 12pt a deck
    // chart needs when it is projected.
    var fsAxis = 15;
    var fsCat = 16;
    var fsData = 16;
    var fsLegend = 15;

    function line(x1, y1, x2, y2, color, width, dash) {
      var l = svgEl("line");
      l.setAttribute("x1", x1); l.setAttribute("y1", y1);
      l.setAttribute("x2", x2); l.setAttribute("y2", y2);
      l.setAttribute("stroke", color);
      l.setAttribute("stroke-width", width || 1);
      if (dash) l.setAttribute("stroke-dasharray", dash);
      svg.appendChild(l);
      return l;
    }

    function text(x, y, str, anchor, color, size, weight) {
      var tx = svgEl("text");
      tx.setAttribute("x", x); tx.setAttribute("y", y);
      tx.setAttribute("text-anchor", anchor || "start");
      tx.setAttribute("fill", color);
      tx.setAttribute("font-size", size || 11);
      if (weight) tx.setAttribute("font-weight", weight);
      tx.setAttribute("font-family", "inherit");
      tx.textContent = str;
      svg.appendChild(tx);
      return tx;
    }

    if (isPie) {
      var s0 = series[0] || { values: [] };
      var total = s0.values.reduce(function (a, b) { return a + b; }, 0) || 1;
      // The legend column is measured from the names, not guessed: a Korean
      // label is about 16px at 15px type. The ring then takes the square that
      // is left, so a long name never pushes the ring off centre.
      var legendW = 0;
      if (legendPos !== "none") {
        var nameW = cats.reduce(function (a, c) {
          var w = 0;
          for (var ci2 = 0; ci2 < c.length; ci2 += 1) {
            w += c.charCodeAt(ci2) > 255 ? 17 : 9;
          }
          return Math.max(a, w);
        }, 0);
        legendW = Math.min(plotW * 0.42, nameW + 46);
      }
      // The ring and the legend are one block: the ring is centred inside the
      // space the legend leaves, and the block as a whole is centred in the
      // plot, so no side carries a dead margin.
      var outer = Math.max(20, Math.min((plotW - legendW - 30) / 2, plotH / 2 - 6));
      var groupW = outer * 2 + (legendW > 0 ? 30 + legendW : 0);
      var cx = padL + Math.max(0, (plotW - groupW) / 2) + outer;
      var cy = padT + plotH / 2;
      var inner = ch.type === "doughnut" ? outer * (1 - (ch.hole || 50) / 100) : 0;
      var start = -Math.PI / 2;
      s0.values.forEach(function (v, ci) {
        var ang = (v / total) * Math.PI * 2;
        var mid = start + ang / 2;
        var path = svgEl("path");
        var x1 = cx + outer * Math.cos(start), y1 = cy + outer * Math.sin(start);
        var x2 = cx + outer * Math.cos(start + ang), y2 = cy + outer * Math.sin(start + ang);
        var large = ang > Math.PI ? 1 : 0;
        var d = "M " + cx + " " + cy + " L " + x1 + " " + y1
          + " A " + outer + " " + outer + " 0 " + large + " 1 " + x2 + " " + y2 + " Z";
        if (inner > 0) {
          var x3 = cx + inner * Math.cos(start + ang), y3 = cy + inner * Math.sin(start + ang);
          var x4 = cx + inner * Math.cos(start), y4 = cy + inner * Math.sin(start);
          d = "M " + x1 + " " + y1
            + " A " + outer + " " + outer + " 0 " + large + " 1 " + x2 + " " + y2
            + " L " + x3 + " " + y3
            + " A " + inner + " " + inner + " 0 " + large + " 0 " + x4 + " " + y4 + " Z";
        }
        path.setAttribute("d", d);
        path.setAttribute("fill", colors[ci % colors.length]);
        path.setAttribute("stroke", "#" + ch.bg);
        path.setAttribute("stroke-width", "1.5");
        svg.appendChild(path);
        if (ch.labels) {
          var lr = inner > 0 ? (inner + outer) / 2 : outer * 0.66;
          text(cx + lr * Math.cos(mid), cy + lr * Math.sin(mid) + 4,
            fmtNum(v, fmt), "middle", "#" + ch.bg, fsData, "700");
        }
        start += ang;
      });
      if (legendPos !== "none") {
        var lx = cx + outer + 30;
        var ly = cy - (s0.values.length * 24) / 2 + 14;
        cats.forEach(function (c, ci) {
          var sw = svgEl("rect");
          sw.setAttribute("x", lx); sw.setAttribute("y", ly - 9);
          sw.setAttribute("width", 10); sw.setAttribute("height", 10);
          sw.setAttribute("fill", colors[ci % colors.length]);
          svg.appendChild(sw);
          // The share belongs in the legend when the slices carry no labels:
          // a ring whose title claims 47% must show where that 47% is.
          var share = ch.labels ? c
            : c + "  " + Math.round((s0.values[ci] / total) * 100) + "%";
          text(lx + 18, ly, share, "start", fg, fsLegend);
          ly += 24;
        });
      }
      host.appendChild(svg);
      return;
    }

    // Value axis range. Stacked charts sum their series; everything else uses
    // the raw values with zero included, so bars always start from the rule.
    var maxV = 0, minV = 0;
    if (isStacked) {
      var perCat = cats.map(function () { return 0; });
      series.forEach(function (s) {
        s.values.forEach(function (v, ci) { perCat[ci] += v; });
      });
      maxV = Math.max.apply(null, perCat.concat([0]));
      minV = Math.min.apply(null, perCat.concat([0]));
    } else if (isCombo) {
      var bvals = [];
      barSeries.forEach(function (s) {
        (s.values || []).forEach(function (v) { bvals.push(v); });
      });
      bvals.push(0);
      maxV = Math.max.apply(null, bvals);
      minV = Math.min.apply(null, bvals);
    } else {
      var vals = seriesValues(ch).concat([0]);
      maxV = Math.max.apply(null, vals);
      minV = Math.min.apply(null, vals);
    }
    if (isScatter) {
      var all = seriesValues(ch);
      maxV = Math.max.apply(null, all);
      minV = 0;
    }
    if (maxV === minV) maxV = minV + 1;
    var ticks = 4;
    var step = niceStep((maxV - minV) / ticks);
    var top = Math.ceil(maxV / step) * step;
    var bottom = Math.floor(minV / step) * step;
    if (top === bottom) top = bottom + step;
    var span = top - bottom;
    var scale = function (v) { return plotH - ((v - bottom) / span) * plotH; };
    var yOf = function (v) { return padT + scale(v); };

    // The secondary axis. It is computed from the line series alone, so a rate
    // of 8..14% fills the plot height instead of hugging the baseline beside
    // bars measured in hundreds.
    var yOf2 = yOf;
    if (isCombo && lineSeries.length) {
      var lvals = [];
      lineSeries.forEach(function (s) {
        (s.values || []).forEach(function (v) { lvals.push(v); });
      });
      lvals.push(0);
      var max2 = Math.max.apply(null, lvals);
      var min2 = Math.min.apply(null, lvals);
      if (max2 === min2) max2 = min2 + 1;
      var step2 = niceStep((max2 - min2) / ticks);
      var top2 = Math.ceil(max2 / step2) * step2;
      var bottom2 = Math.floor(min2 / step2) * step2;
      if (top2 === bottom2) top2 = bottom2 + step2;
      var span2 = top2 - bottom2;
      yOf2 = function (v) { return padT + (plotH - ((v - bottom2) / span2) * plotH); };
      for (var t2 = bottom2; t2 <= top2 + 1e-9; t2 += step2) {
        text(padL + plotW + 8, yOf2(t2) + 4, fmtNum(t2, fmt), "start", muted, fsAxis);
      }
    }

    // A horizontal bar chart puts its value axis on the bottom and its
    // categories on the left. Drawing value labels on the left as well stacks
    // them on top of the category names, which is unreadable.
    var xOf = function (v) { return padL + ((v - bottom) / span) * plotW; };
    for (var tv = bottom; tv <= top + 1e-9; tv += step) {
      if (isHorizontal) {
        var gx = xOf(tv);
        line(gx, padT, gx, padT + plotH, lineColor, 1);
        text(gx, padT + plotH + 26, fmtNum(tv, fmt), "middle", muted, fsAxis);
      } else {
        var gy = yOf(tv);
        line(padL, gy, padL + plotW, gy, lineColor, 1);
        text(padL - 10, gy + 4, fmtNum(tv, fmt), "end", muted, fsAxis);
      }
    }

    var slot = plotW / Math.max(1, cats.length);
    var nSeries = series.length;
    // A horizontal chart with two categories would otherwise stretch its bars
    // over the whole plot height and read as a divergent axis. Bars keep a
    // fixed thickness and the group is centred in the plot.
    var rowH = isHorizontal ? Math.min(slot, 78) : slot;
    var rowTop = isHorizontal ? padT + (plotH - rowH * cats.length) / 2 : padT;

    // Clustered vertical bars. Combo shares this with a plain column chart: the
    // bar half of a combo is an ordinary clustered group on the left axis.
    function drawColumns(list) {
      var n = Math.max(1, list.length);
      var bw = Math.min(96, (slot * 0.6) / n);
      list.forEach(function (s, bi) {
        var si = series.indexOf(s);
        s.values.forEach(function (v, ci) {
          var base = yOf(0);
          var yv = yOf(v);
          var bx = padL + slot * ci + slot / 2 - (bw * n) / 2 + bw * bi;
          var r = svgEl("rect");
          r.setAttribute("x", bx);
          r.setAttribute("y", Math.min(yv, base));
          r.setAttribute("width", Math.max(2, bw - 2));
          r.setAttribute("height", Math.max(1, Math.abs(base - yv)));
          r.setAttribute("fill", colors[si % colors.length]);
          svg.appendChild(r);
          if (ch.labels) {
            // In a combo the line sweeps over the bar tops, so the bar value
            // goes inside the bar instead of above it.
            if (isCombo) {
              text(bx + (bw - 2) / 2, Math.min(yv, base) + 20,
                fmtNum(v, fmt), "middle", "#" + ch.bg, fsData, "700");
            } else {
              text(bx + (bw - 2) / 2, Math.min(yv, base) - 9,
                fmtNum(v, fmt), "middle", fg, fsData, "700");
            }
          }
        });
      });
    }

    if (ch.type === "line" || ch.type === "area" || ch.type === "combo") {
      var drawn = 0;
      var drawnSeries = isCombo ? lineSeries : series;
      drawnSeries.forEach(function (s) {
        var si = series.indexOf(s);
        var yv = isCombo ? yOf2 : yOf;
        var color = colors[si % colors.length];
        var pts = s.values.map(function (v, ci) {
          return [padL + slot * (ci + 0.5), yv(v)];
        });
        if (ch.type === "area") {
          var d = "M " + pts[0][0] + " " + yOf(bottom);
          pts.forEach(function (p) { d += " L " + p[0] + " " + p[1]; });
          d += " L " + pts[pts.length - 1][0] + " " + yOf(bottom) + " Z";
          var area = svgEl("path");
          area.setAttribute("d", d);
          area.setAttribute("fill", color);
          // A 90% fill turns the plot into a solid block and hides the grid
          // behind it. A light wash plus the series line keeps the shape.
          area.setAttribute("opacity", "0.2");
          svg.appendChild(area);
          var edge = svgEl("polyline");
          edge.setAttribute("points", pts.map(function (p) { return p[0] + "," + p[1]; }).join(" "));
          edge.setAttribute("fill", "none");
          edge.setAttribute("stroke", color);
          edge.setAttribute("stroke-width", "2.5");
          edge.setAttribute("stroke-linejoin", "round");
          svg.appendChild(edge);
          drawn += 1;
        } else {
          var poly = svgEl("polyline");
          poly.setAttribute("points", pts.map(function (p) { return p[0] + "," + p[1]; }).join(" "));
          poly.setAttribute("fill", "none");
          poly.setAttribute("stroke", color);
          poly.setAttribute("stroke-width", "2.5");
          poly.setAttribute("stroke-linejoin", "round");
          svg.appendChild(poly);
          pts.forEach(function (p) {
            var c = svgEl("circle");
            c.setAttribute("cx", p[0]); c.setAttribute("cy", p[1]);
            c.setAttribute("r", 3.5);
            c.setAttribute("fill", color);
            c.setAttribute("stroke", "#" + ch.bg);
            c.setAttribute("stroke-width", "1.5");
            svg.appendChild(c);
          });
        }
        // A combo labels the line on its own scale; the bars carry their own.
        if (ch.labels && !isCombo) {
          pts.forEach(function (p, ci) {
            text(p[0], p[1] - 11, fmtNum(s.values[ci], fmt), "middle", fg, fsData, "700");
          });
        }
        drawn += 1;
      });
      if (isCombo) drawColumns(barSeries);
    } else if (ch.type === "scatter") {
      // x comes from the category when every label parses as a number, and from
      // the point position otherwise; the value is always y. Plotting the value
      // on both axes would draw a diagonal line through the origin.
      var xs = cats.slice(0, (series[0] || { values: [] }).values.length);
      var numeric = xs.length > 0 && xs.every(function (c) { return isFinite(Number(c)) && String(c).trim() !== ""; });
      var xv = numeric ? xs.map(Number) : xs.map(function (_, i) { return i + 1; });
      var xMin = numeric ? Math.min.apply(null, xv.concat([0])) : 0;
      var xMax = Math.max.apply(null, xv.concat([1]));
      var xSpan = xMax - xMin || 1;
      var xOfV = function (v) { return padL + ((v - xMin) / xSpan) * plotW; };
      series.forEach(function (s, si) {
        var color = colors[si % colors.length];
        s.values.forEach(function (v, ci) {
          var c = svgEl("circle");
          c.setAttribute("cx", xOfV(xv[ci]));
          c.setAttribute("cy", yOf(v));
          c.setAttribute("r", 5);
          c.setAttribute("fill", color);
          svg.appendChild(c);
          if (ch.labels) {
            text(xOfV(xv[ci]), yOf(v) - 11, fmtNum(v, fmt), "middle", fg, fsData, "700");
          }
        });
      });
      // Numeric categories are their own x ticks; named ones are labels.
      for (var xi = 0; xi < xv.length; xi += 1) {
        text(xOfV(xv[xi]), padT + plotH + 26,
          numeric ? fmtNum(xv[xi], fmt) : String(xs[xi]),
          "middle", muted, fsCat);
      }
    } else if (isHorizontal) {
      if (isStacked) {
        var acc = cats.map(function () { return 0; });
        series.forEach(function (s, si) {
          s.values.forEach(function (v, ci) {
            var len = (v / span) * plotW;
            var x0 = padL + (acc[ci] / span) * plotW;
            var r = svgEl("rect");
            r.setAttribute("x", x0);
            r.setAttribute("y", rowTop + rowH * ci + rowH * 0.14);
            r.setAttribute("width", Math.max(0, len));
            r.setAttribute("height", Math.max(2, rowH * 0.72));
            r.setAttribute("fill", colors[si % colors.length]);
            svg.appendChild(r);
            if (ch.labels) {
              text(x0 + len / 2, rowTop + rowH * ci + rowH * 0.5 + 5,
                fmtNum(v, fmt), "middle", "#" + ch.bg, fsData, "700");
            }
            acc[ci] += v;
          });
        });
      } else {
        var bh = Math.min(38, (rowH * 0.62) / nSeries);
        barSeries.forEach(function (s) {
          var si = series.indexOf(s);
          s.values.forEach(function (v, ci) {
            var r = svgEl("rect");
            r.setAttribute("x", padL);
            var bhN = Math.max(1, barSeries.length);
            var bsi = barSeries.indexOf(s);
            r.setAttribute("y", rowTop + rowH * ci + rowH * 0.5 - (bh * bhN) / 2 + bh * bsi);
            r.setAttribute("width", Math.max(1, (v / span) * plotW));
            r.setAttribute("height", Math.max(2, bh - 2));
            r.setAttribute("fill", colors[si % colors.length]);
            svg.appendChild(r);
            if (ch.labels) {
              text(padL + Math.max(1, (v / span) * plotW) + 8,
                rowTop + rowH * ci + rowH * 0.5 - (bh * bhN) / 2 + bh * bsi + bh / 2 + 5,
                fmtNum(v, fmt), "start", fg, fsData, "700");
            }
          });
        });
      }
    } else {
      if (isStacked) {
        var accc = cats.map(function () { return 0; });
        barSeries.forEach(function (s) {
          var si = series.indexOf(s);
          s.values.forEach(function (v, ci) {
            var y0 = yOf(accc[ci]);
            var y1 = yOf(accc[ci] + v);
            var bw = Math.min(96, slot * 0.58);
            var r = svgEl("rect");
            r.setAttribute("x", padL + slot * ci + (slot - bw) / 2);
            r.setAttribute("y", Math.min(y0, y1));
            r.setAttribute("width", bw);
            r.setAttribute("height", Math.max(1, Math.abs(y1 - y0)));
            r.setAttribute("fill", colors[si % colors.length]);
            svg.appendChild(r);
            if (ch.labels) {
              text(padL + slot * ci + slot / 2, Math.min(y0, y1) + Math.abs(y1 - y0) / 2 + 4,
                fmtNum(v, fmt), "middle", "#" + ch.bg, 11, "700");
            }
            accc[ci] += v;
          });
        });
      } else {
        drawColumns(barSeries);
      }
    }

    if (!isScatter) {
      cats.forEach(function (c, ci) {
        if (isHorizontal) {
          text(padL - 12, rowTop + rowH * ci + rowH * 0.5 + 5, c, "end", muted, fsCat);
        } else {
          text(padL + slot * (ci + 0.5), padT + plotH + 26, c, "middle", muted, fsCat);
        }
      });
    }

    // The baseline is drawn last so bars cannot hide the zero rule.
    if (planAxis()) line(padL, yOf(0), padL + plotW, yOf(0), "#" + t.muted, 1);

    function planAxis() {
      return ch.type !== "line" && ch.type !== "area" && ch.type !== "scatter";
    }

    if (catTitle) {
      text(padL + plotW / 2, H - (hasLegend ? 28 : 8), catTitle, "middle", muted, fsAxis);
    }
    if (axisTitle) {
      var vt = text(0, 0, axisTitle, "middle", muted, fsAxis);
      vt.setAttribute("transform", "translate(16," + (padT + plotH / 2) + ") rotate(-90)");
    }

    if (hasLegend) {
      var items = series.map(function (s, si) {
        return { name: s.name, color: colors[si % colors.length] };
      });
      // A Korean glyph is about 17px at 15px type and a Latin one about 9px, so
      // counting characters would under-measure "모바일" by a third and let the
      // next swatch land on its label.
      var widths = items.map(function (it) {
        var w = 0;
        var nm = String(it.name);
        for (var k2 = 0; k2 < nm.length; k2 += 1) {
          w += nm.charCodeAt(k2) > 255 ? 17 : 9;
        }
        return w + 34;
      });
      var totalW = widths.reduce(function (a, b) { return a + b; }, 0);
      var lx2 = padL + Math.max(0, (plotW - totalW) / 2);
      var ly2 = H - 10;
      items.forEach(function (it, k) {
        var sw = svgEl("rect");
        sw.setAttribute("x", lx2); sw.setAttribute("y", ly2 - 9);
        sw.setAttribute("width", 10); sw.setAttribute("height", 10);
        sw.setAttribute("fill", it.color);
        svg.appendChild(sw);
        text(lx2 + 15, ly2, it.name, "start", fg, fsLegend);
        lx2 += widths[k];
      });
    }

    host.appendChild(svg);
  }

  // -------------------------------------------------------------------------
  // Slide
  // -------------------------------------------------------------------------

  function buildSlide(slide) {
    var t = themeOf(slide);
    var stage = el("section", "pp-slide");
    stage.dataset.index = String(slide.index);
    stage.style.width = px(deck.size.w) + "px";
    stage.style.height = px(deck.size.h) + "px";
    stage.style.background = "#" + slide.bg;
    stage.style.fontFamily = '"' + deck.theme.fonts.eastAsian + '", "'
      + deck.theme.fonts.latin + '", sans-serif';

    var images = slide.images || [];
    images.forEach(function (img) {
      if ((img.layer || "front") === "back") renderImage(img, stage);
    });
    if (slide.scrim) {
      var scrim = el("div", "pp-rect");
      scrim.style.left = "0";
      scrim.style.top = "0";
      scrim.style.width = px(deck.size.w) + "px";
      scrim.style.height = px(deck.size.h) + "px";
      scrim.style.background = "#" + slide.scrim.color;
      scrim.style.opacity = String(slide.scrim.alpha);
      stage.appendChild(scrim);
    }
    slide.shapes.forEach(function (shape) {
      if (shape.type === "rect" || shape.type === "ellipse") renderRect(shape, stage);
      else renderText(shape, stage);
    });
    if (slide.table) renderTable(slide.table, t, stage);
    if (slide.chart) renderChart(slide.chart, t, stage);
    images.forEach(function (img) {
      if ((img.layer || "front") !== "back") renderImage(img, stage);
    });
    return stage;
  }

  // -------------------------------------------------------------------------
  // Measurement
  // -------------------------------------------------------------------------

  function rectOf(node, stage) {
    var r = node.getBoundingClientRect();
    var s = stage.getBoundingClientRect();
    return { l: r.left - s.left, t: r.top - s.top, r: r.right - s.left, b: r.bottom - s.top };
  }

  function areaOf(r) {
    return Math.max(0, r.r - r.l) * Math.max(0, r.b - r.t);
  }

  // Two text blocks that cover each other are worse than either one overflowing:
  // the reader loses a sentence and the deck looks broken. Reported only when the
  // boxes overlap by more than a fifth of the smaller box, which is far past what
  // a deliberate overlap (a caption over a picture) would produce.
  function overlaps(a, b) {
    var w = Math.min(a.r, b.r) - Math.max(a.l, b.l);
    var h = Math.min(a.b, b.b) - Math.max(a.t, b.t);
    if (w <= 0 || h <= 0) return 0;
    var inter = w * h;
    var small = Math.min(areaOf(a), areaOf(b));
    return small > 0 ? inter / small : 0;
  }

  function measure() {
    var report = { slides: [], size: { w: px(deck.size.w), h: px(deck.size.h) } };
    var stages = document.querySelectorAll(".pp-slide");
    stages.forEach(function (stage) {
      var idx = parseInt(stage.dataset.index, 10);
      var entry = { index: idx, kind: "", overflow: [], emptyText: [], outside: [],
                    overlap: [], coverage: 0 };
      if (deck.slides[idx]) entry.kind = deck.slides[idx].kind;
      var limitW = parseFloat(stage.style.width);
      var limitH = parseFloat(stage.style.height);
      var boxes = [];
      stage.querySelectorAll(".pp-text").forEach(function (box) {
        var inner = box.querySelector(".pp-text-in");
        var style = getComputedStyle(box);
        var availH = box.clientHeight - parseFloat(style.paddingTop) - parseFloat(style.paddingBottom);
        var availW = box.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight);
        var needH = inner.scrollHeight;
        var needW = inner.scrollWidth;
        var str = (inner.textContent || "").trim();
        if (!str) entry.emptyText.push({ shape: box.dataset.shapeId });
        if (needH > availH + 1 || needW > availW + 1) {
          entry.overflow.push({
            shape: box.dataset.shapeId,
            text: str.slice(0, 48),
            needH: needH, availH: availH,
            needW: needW, availW: availW
          });
        }
        var r = rectOf(box, stage);
        if (r.l < -1 || r.t < -1 || r.r > limitW + 1 || r.b > limitH + 1) {
          entry.outside.push({ shape: box.dataset.shapeId, text: str.slice(0, 32) });
        }
        if (str) boxes.push({ shape: box.dataset.shapeId, text: str.slice(0, 24), r: r });
      });

      for (var i = 0; i < boxes.length; i++) {
        for (var j = i + 1; j < boxes.length; j++) {
          var ratio = overlaps(boxes[i].r, boxes[j].r);
          if (ratio > 0.2) {
            entry.overlap.push({
              a: boxes[i].shape, b: boxes[j].shape,
              ratio: Math.round(ratio * 100) / 100,
              textA: boxes[i].text, textB: boxes[j].text
            });
          }
        }
      }

      // Content coverage: the share of the canvas that carries something. A slide
      // far below a third reads as unfinished, and this number is what the
      // balance decision in the layout engine is judged by.
      var minL = limitW, minT = limitH, maxR = 0, maxB = 0, found = false;
      var consider = function (r) {
        if (areaOf(r) <= 0) return;
        minL = Math.min(minL, r.l); minT = Math.min(minT, r.t);
        maxR = Math.max(maxR, r.r); maxB = Math.max(maxB, r.b);
        found = true;
      };
      // Chrome (footer, page number) is layout furniture, not content; counting
      // it would let an almost empty slide pass the coverage check.
      stage.querySelectorAll(".pp-text, .pp-rect, .pp-image, .pp-chart, .pp-table").forEach(function (node) {
        if (node.style.opacity === "0") return;
        if (node.dataset && node.dataset.role === "chrome") return;
        consider(rectOf(node, stage));
      });
      if (found) {
        entry.coverage = Math.round(((maxR - minL) * (maxB - minT)) / (limitW * limitH) * 1000) / 1000;
        entry.box = { l: Math.round(minL), t: Math.round(minT),
                      r: Math.round(maxR), b: Math.round(maxB) };
      }
      report.slides.push(entry);
    });
    report.ok = report.slides.every(function (s) {
      return s.overflow.length === 0 && s.outside.length === 0 && s.overlap.length === 0;
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
