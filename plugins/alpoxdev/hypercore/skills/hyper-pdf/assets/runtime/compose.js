// compose.js — deterministic PDF composition from a JSON layout spec.
//
// No browser, no HTML engine, no external converter. Text is measured with
// CoreText and drawn with CoreGraphics, so the same spec paginates the same way
// on every run, and Korean text breaks where a reader expects. That
// determinism is why this path sits next to HTML rendering: an invoice or a
// contract must not reflow because a font or a browser build changed.
//
// Every document is described as blocks. A block is drawn in reading order and
// the composer decides page breaks, running headers, and footers.

function buildDocument(spec, outPath) {
  var page = spec.page || {};
  var width = page.width || 595.28;
  var height = page.height || 841.89;
  var margin = page.margin || 56.7;
  var gutter = margin;
  var contentWidth = width - margin * 2;
  var fontPath = spec.font || null;
  var baseSize = spec.fontSize || 11;
  var footerText = spec.footer || null;
  var headerText = spec.header || null;
  var showNumbers = spec.pageNumbers !== false;

  var state = {
    ctx: newContext(outPath, width, height),
    width: width,
    height: height,
    margin: margin,
    contentWidth: contentWidth,
    fontPath: fontPath,
    y: 0,
    page: 0,
    footerText: footerText,
    headerText: headerText,
    showNumbers: showNumbers,
    fontPathResolved: fontPath
  };
  openPage(state);

  var blocks = spec.blocks || [];
  var rendered = [];
  for (var i = 0; i < blocks.length; i++) {
    var report = drawBlock(state, blocks[i], baseSize);
    rendered.push(report);
  }
  if (spec.signature) drawSignature(state, spec.signature, baseSize);
  closePage(state);
  closeContext(state.ctx);

  var language = spec.lang || null;
  var languageReport = null;
  if (language) {
    try {
      languageReport = injectLanguage(outPath, language);
    } catch (error) {
      languageReport = { injected: false, reason: String(error && error.message || error) };
    }
  }

  var scan = rawScan(outPath);
  var issues = [];
  if (scan.fontFile2 + scan.fontFile3 === 0) {
    issues.push('FONT_NOT_EMBEDDED');
  }
  if (scan.type3 > 0) {
    issues.push('TYPE3_GLYPHS');
  }
  if (!scan.language) issues.push('NO_LANGUAGE_TAG');
  if (scan.structureTree === 0) issues.push('NO_STRUCTURE_TREE');

  if (language && languageReport && !languageReport.injected) {
    issues.push('LANGUAGE_TAG_FAILED');
  }

  return {
    status: issues.length ? 'caveated' : 'ok',
    out: outPath,
    pages: state.page,
    blocks: rendered.length,
    language: languageReport,
    issues: issues,
    message: issues.length
      ? 'Composition succeeded. The flagged items are what a screen reader or a font-substituting reader loses; see the accessibility notes before shipping this file as a public document.'
      : 'Composition succeeded with embedded fonts, a language tag, and a structure tree.'
  };
}

function openPage(state) {
  state.page++;
  // state.y is the distance from the page's top edge to the current cursor.
  // Layout grows downward, matching how the document reads.
  state.y = state.margin;
  beginPage(state.ctx, state.width, state.height);
  ctxSave(state.ctx);
  // Layout below is written top-down because that is how a document reads, but
  // PDF draws bottom-up. Flipping the context would also mirror the glyphs, so
  // the conversion happens once in each drawing primitive instead.
  if (state.headerText) {
    drawTextLine(state, state.headerText, state.margin, state.margin * 0.45, {
      size: 9,
      color: [0.45, 0.45, 0.45, 1]
    });
  }
}

function closePage(state) {
  if (state.showNumbers) {
    var label = String(state.page);
    drawTextLine(state, label, state.width / 2 - 6, state.height - state.margin * 0.75, {
      size: 9,
      color: [0.4, 0.4, 0.4, 1]
    });
  }
  if (state.footerText) {
    drawTextLine(state, state.footerText, state.margin, state.height - state.margin * 0.75, {
      size: 8,
      color: [0.45, 0.45, 0.45, 1]
    });
  }
  ctxRestore(state.ctx);
  endPage(state.ctx);
}

// Returns true when the block fits on the current page. When it does not, the
// page is finished and a fresh one starts, so the caller draws at the new
// cursor instead of splitting the block.
function ensureSpace(state, needed) {
  if (state.y + needed <= state.height - state.margin) return true;
  closePage(state);
  openPage(state);
  return false;
}

// Every coordinate that enters the page goes through one of the three helpers
// below. `topY` is a distance from the page's top edge, which is how the spec
// and the layout code think; the helpers convert to the bottom-up space PDF
// draws in. Doing it in three places keeps the tenth of a millimetre in the
// baseline consistent across blocks.
function baselineOf(state, topY, size) {
  return state.height - topY - size * 0.86;
}

function drawTextLine(state, text, x, topY, options) {
  var o = options || {};
  var size = o.size || 11;
  drawLine(state.ctx, text, x, baselineOf(state, topY, size), {
    size: size,
    color: o.color || [0.05, 0.05, 0.05, 1],
    fontPath: state.fontPathResolved
  });
  return topY + size * 0.86;
}

function ruleAt(state, y, color, thickness) {
  var bottom = state.height - y;
  strokeLine(state.ctx, state.margin, bottom, state.margin + state.contentWidth, bottom, color, thickness);
}

function boxAt(state, x, top, width, height, color) {
  fillRect(state.ctx, x, state.height - top - height, width, height, color);
}

// A paragraph is measured line by line so the composer can break between lines
// rather than pushing whole paragraphs to the next page.
function drawParagraph(state, block, baseSize) {
  var size = block.size || baseSize;
  var leading = block.leading || Math.round(size * 1.65 * 100) / 100;
  var color = colorOf(block.color);
  var indent = block.indent || 0;
  var available = state.contentWidth - indent;
  var lines = wrapText(block.text || '', available, size, state.fontPathResolved);
  var drawn = 0;
  for (var i = 0; i < lines.length; i++) {
    // A paragraph may continue across a page break; the break happens between
    // lines, never inside one.
    ensureSpace(state, leading);
    drawTextLine(state, lines[i], state.margin + indent, state.y, { size: size, color: color });
    state.y += leading;
    drawn++;
  }
  return { type: 'paragraph', lines: drawn, pages: state.page };
}

function drawHeading(state, block, baseSize) {
  var level = block.level || 1;
  var size = block.size || [0, 22, 17, 14, 12, 11][Math.min(level, 5)] || 14;
  var leading = Math.round(size * 1.5 * 100) / 100;
  ensureSpace(state, leading * (block.keepWithNext ? 2.2 : 1));
  state.y += size * 0.4;
  drawTextLine(state, block.text || '', state.margin, state.y, { size: size, color: [0.05, 0.05, 0.05, 1] });
  state.y += leading;
  if (block.rule) {
    ruleAt(state, state.y, [0.7, 0.7, 0.7, 1], 0.6);
    state.y += 6;
  }
  state.y += size * 0.25;
  return { type: 'heading', level: level, page: state.page };
}

function drawBulletList(state, block, baseSize) {
  var size = block.size || baseSize;
  var leading = Math.round(size * 1.6 * 100) / 100;
  var items = block.items || [];
  var indent = 16;
  var count = 0;
  for (var i = 0; i < items.length; i++) {
    var marker = block.ordered ? String(i + 1) + '.' : '\u2022';
    ensureSpace(state, leading);
    drawTextLine(state, marker, state.margin, state.y, { size: size });
    var lines = wrapText(items[i], state.contentWidth - indent, size, state.fontPathResolved);
    for (var l = 0; l < lines.length; l++) {
      ensureSpace(state, leading);
      drawTextLine(state, lines[l], state.margin + indent, state.y, { size: size });
      state.y += leading;
    }
    state.y += size * 0.3;
    count++;
  }
  return { type: 'list', items: count, page: state.page };
}

function drawTable(state, block, baseSize) {
  var size = block.size || Math.max(8, baseSize - 1);
  var leading = Math.round(size * 1.5 * 100) / 100;
  var padding = 4;
  var header = block.header || null;
  var rows = block.rows || [];
  var columns = block.columns || (header ? header.length : (rows[0] ? rows[0].length : 1));
  var weights = block.widths || null;
  var totalWeight = 0;
  var wi;
  for (wi = 0; wi < columns; wi++) {
    totalWeight += weights ? (weights[wi] || 1) : 1;
  }
  var colWidths = [];
  for (wi = 0; wi < columns; wi++) {
    colWidths.push(state.contentWidth * ((weights ? (weights[wi] || 1) : 1) / totalWeight));
  }

  function cellLines(cell) {
    return wrapText(String(cell === null || cell === undefined ? '' : cell), colWidths[0] - padding * 2, size, state.fontPathResolved);
  }

  function drawRow(cells, isHeader) {
    var wrapped = [];
    var maxLines = 1;
    for (var c = 0; c < columns; c++) {
      var cellText = cells[c] === null || cells[c] === undefined ? '' : String(cells[c]);
      var lines = wrapText(cellText, colWidths[c] - padding * 2, size, state.fontPathResolved);
      wrapped.push(lines);
      if (lines.length > maxLines) maxLines = lines.length;
    }
    var rowHeight = maxLines * leading + padding * 2;
    if (!ensureSpace(state, rowHeight)) {
      // The table continues on the following page and repeats its header so a
      // reader who lands mid-table still knows what the columns mean.
      if (header && !isHeader) drawRow(header, true);
    }
    var top = state.y;
    if (isHeader) {
      boxAt(state, state.margin, top, state.contentWidth, rowHeight, [0.93, 0.93, 0.93, 1]);
    }
    var x = state.margin;
    for (var c2 = 0; c2 < columns; c2++) {
      for (var l = 0; l < wrapped[c2].length; l++) {
        drawTextLine(state, wrapped[c2][l], x + padding, top + padding + leading * l, { size: size });
      }
      x += colWidths[c2];
    }
    // Grid: vertical rules every row, horizontal rule under the header only.
    // A full grid on every row reads as noise in a financial table.
    var gx = state.margin;
    var topEdge = state.height - top;
    for (var c3 = 0; c3 <= columns; c3++) {
      strokeLine(state.ctx, gx, topEdge, gx, topEdge - rowHeight, [0.78, 0.78, 0.78, 1], 0.4);
      if (c3 < columns) gx += colWidths[c3];
    }
    strokeLine(state.ctx, state.margin, topEdge, state.margin + state.contentWidth, topEdge, isHeader ? [0.5, 0.5, 0.5, 1] : [0.78, 0.78, 0.78, 1], isHeader ? 0.7 : 0.4);
    state.y += rowHeight;
  }

  if (header) drawRow(header, true);
  for (var r = 0; r < rows.length; r++) drawRow(rows[r], false);
  ruleAt(state, state.y, [0.5, 0.5, 0.5, 1], 0.7);
  state.y += size * 1.1;
  return { type: 'table', rows: rows.length, columns: columns, page: state.page };
}

function drawKeyValue(state, block, baseSize) {
  var size = block.size || baseSize;
  var leading = Math.round(size * 1.55 * 100) / 100;
  var labelWidth = block.labelWidth || Math.min(160, state.contentWidth * 0.34);
  var pairs = block.pairs || [];
  for (var i = 0; i < pairs.length; i++) {
    var pair = pairs[i];
    var valueLines = wrapText(String(pair[1] === undefined ? '' : pair[1]), state.contentWidth - labelWidth, size, state.fontPathResolved);
    var blockHeight = Math.max(leading, valueLines.length * leading);
    ensureSpace(state, blockHeight);
    drawTextLine(state, String(pair[0]), state.margin, state.y, { size: size, color: [0.32, 0.32, 0.32, 1] });
    for (var l = 0; l < valueLines.length; l++) {
      drawTextLine(state, valueLines[l], state.margin + labelWidth, state.y + leading * l, { size: size });
    }
    state.y += blockHeight;
    state.y += size * 0.25;
  }
  return { type: 'keyValue', pairs: pairs.length, page: state.page };
}

function drawRule(state) {
  ensureSpace(state, 18);
  ruleAt(state, state.y + 6, [0.75, 0.75, 0.75, 1], 0.6);
  state.y += 18;
  return { type: 'rule', page: state.page };
}

function drawSpacer(state, block) {
  state.y += block.height || 12;
  return { type: 'spacer', page: state.page };
}

function drawSignature(state, signature, baseSize) {
  var size = baseSize;
  var leading = Math.round(size * 1.6 * 100) / 100;
  ensureSpace(state, leading * 5);
  state.y += leading * 0.8;
  ruleAt(state, state.y, [0.6, 0.6, 0.6, 1], 0.5);
  state.y += leading * 0.5;
  drawTextLine(state, signature.label || '', state.margin, state.y, { size: size - 1, color: [0.3, 0.3, 0.3, 1] });
  state.y += leading;
  var lines = signature.lines || [];
  for (var i = 0; i < lines.length; i++) {
    drawTextLine(state, lines[i], state.margin, state.y, { size: size });
    state.y += leading;
  }
}

function colorOf(value) {
  if (!value) return [0.05, 0.05, 0.05, 1];
  if (value[0] !== undefined) return value;
  if (value.muted) return [0.4, 0.4, 0.4, 1];
  return [0.05, 0.05, 0.05, 1];
}

function drawBlock(state, block, baseSize) {
  var kind = block.type || 'paragraph';
  switch (kind) {
    case 'heading': return drawHeading(state, block, baseSize);
    case 'list': return drawBulletList(state, block, baseSize);
    case 'table': return drawTable(state, block, baseSize);
    case 'keyValue': return drawKeyValue(state, block, baseSize);
    case 'rule': return drawRule(state, block);
    case 'spacer': return drawSpacer(state, block);
    case 'pageBreak':
      closePage(state);
      openPage(state);
      return { type: 'pageBreak', page: state.page };
    case 'paragraph':
    default: return drawParagraph(state, block, baseSize);
  }
}