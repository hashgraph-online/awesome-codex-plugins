// native.js — PDF primitives on macOS frameworks, loaded by engine.js.
// PDFKit handles document structure, CoreGraphics handles page drawing and
// watermark stamping, CoreText handles line breaking, Vision handles OCR.
// Every function returns plain JSON-able data; errors throw and engine.js
// converts them into an error object with a code.
ObjC.import('Foundation');
ObjC.import('AppKit');
ObjC.import('PDFKit');
ObjC.import('CoreGraphics');
ObjC.import('CoreText');
ObjC.import('Quartz');
ObjC.import('Vision');

var NSUTF8 = $.NSUTF8StringEncoding;
var NSASCII = $.NSISOLatin1StringEncoding;

function unwrapString(s) {
  if (s === null || s === undefined) return '';
  try {
    var u = ObjC.unwrap(s);
    if (typeof u === 'string') return u;
    return u === null || u === undefined ? '' : String(u);
  } catch (e) {
    return '';
  }
}

function readTextFile(path) {
  var s = $.NSString.stringWithContentsOfFileEncodingError($(path), NSUTF8, $());
  if (s === null || s === undefined) throw new Error('cannot read ' + path);
  return unwrapString(s);
}

function writeTextFile(path, text) {
  var ok = $(text).writeToFileAtomicallyEncodingError($(path), NSUTF8, $());
  if (!ok) throw new Error('cannot write ' + path);
}

function fileExists(path) {
  return $.NSFileManager.defaultManager.fileExistsAtPath($(path));
}

function loadDoc(path) {
  if (!fileExists(path)) throw new Error('missing file: ' + path);
  var doc = $.PDFDocument.alloc.initWithURL($.NSURL.fileURLWithPath($(path)));
  if (doc.isNil()) throw new Error('not a readable PDF: ' + path);
  return doc;
}

// A fresh document carries no encryption dictionary, no /Info, and no
// structure tree. Copying pages into one is how a transform sheds the source's
// encryption and how a decrypt actually produces an unencrypted file.
function newEmptyDocument() {
  return $.PDFDocument.alloc.init;
}

function saveDoc(doc, path, options) {
  var ok;
  if (options) {
    ok = doc.writeToURLWithOptions($.NSURL.fileURLWithPath($(path)), options);
  } else {
    ok = doc.writeToURL($.NSURL.fileURLWithPath($(path)));
  }
  if (!ok) throw new Error('cannot write PDF: ' + path);
  return path;
}

// PDFKit hands back ObjC numbers, which serialize as strings through
// JSON.stringify. Every numeric field is coerced here so a consumer can compare
// page counts and coordinates without re-parsing.
function int(value, fallback) {
  var n = Number(value);
  return isNaN(n) ? fallback : n;
}

function pageCount(doc) {
  return int(doc.pageCount, 0);
}

function isLocked(doc) {
  return doc.isLocked === true;
}

function unlock(doc, password) {
  if (!isLocked(doc)) return true;
  return doc.unlockWithPassword($(password)) === true;
}

function pageBox(page) {
  var r = page.boundsForBox(0);
  return {
    x: int(r.origin.x, 0),
    y: int(r.origin.y, 0),
    width: int(r.size.width, 0),
    height: int(r.size.height, 0)
  };
}

function pageRotation(page) {
  return int(page.rotation, 0);
}

function pageText(page) {
  return unwrapString(page.string);
}

function docText(doc) {
  return unwrapString(doc.string);
}

// Line-level extraction with coordinates. PDF coordinates put the origin at
// the bottom-left corner, so `y` is measured from the page bottom.
function pageLines(page) {
  var box = pageBox(page);
  var rect = $.CGRectMake(box.x, box.y, box.width, box.height);
  var selection = page.selectionForRect(rect);
  if (!selection || selection.isNil()) return [];
  var byLine = selection.selectionsByLine;
  if (!byLine || byLine.isNil()) return [];
  var out = [];
  for (var i = 0; i < byLine.count; i++) {
    var line = byLine.objectAtIndex(i);
    var text = unwrapString(line.string);
    if (!text) continue;
    var b = line.boundsForPage(page);
    out.push({
      text: text,
      x: Math.round(int(b.origin.x, 0) * 100) / 100,
      y: Math.round(int(b.origin.y, 0) * 100) / 100,
      width: Math.round(int(b.size.width, 0) * 100) / 100,
      height: Math.round(int(b.size.height, 0) * 100) / 100
    });
  }
  return out;
}

// Character boxes let a caller detect column gaps and rebuild table cells
// without a full content-stream parser.
function pageChars(page, limit) {
  var text = pageText(page);
  var count = typeof limit === 'number' ? Math.min(limit, text.length) : text.length;
  var out = [];
  for (var i = 0; i < count; i++) {
    var r;
    try {
      r = page.characterBoundsAtIndex(i);
    } catch (e) {
      break;
    }
    if (!r) break;
    out.push({
      ch: text.charAt(i),
      x: Math.round(int(r.origin.x, 0) * 100) / 100,
      y: Math.round(int(r.origin.y, 0) * 100) / 100,
      width: Math.round(int(r.size.width, 0) * 100) / 100,
      height: Math.round(int(r.size.height, 0) * 100) / 100
    });
  }
  return out;
}

// Group characters into visual lines by baseline, then split a line into runs
// at gaps wider than `gapFactor` times the median advance. A sign of a table
// column boundary is exactly such a gap, so the caller can reason about cells.
function textRuns(page) {
  var chars = pageChars(page);
  if (!chars.length) return [];
  var lines = [];
  var current = [];
  var lastY = null;
  for (var i = 0; i < chars.length; i++) {
    var c = chars[i];
    if (lastY === null || Math.abs(c.y - lastY) <= Math.max(2, c.height * 0.4)) {
      current.push(c);
      lastY = c.y;
    } else {
      lines.push(current);
      current = [c];
      lastY = c.y;
    }
    if (c.ch === '\n' || c.ch === '\r') {
      lines.push(current);
      current = [];
      lastY = null;
    }
  }
  if (current.length) lines.push(current);

  var out = [];
  for (var li = 0; li < lines.length; li++) {
    var line = lines[li].filter(function (c) { return c.ch !== '\n' && c.ch !== '\r'; });
    if (!line.length) continue;
    var advances = line.map(function (c) { return c.width; }).filter(function (w) { return w > 0; });
    advances.sort(function (a, b) { return a - b; });
    var median = advances.length ? advances[Math.floor(advances.length / 2)] : 6;
    var gapThreshold = Math.max(median * 1.6, 8);
    var runs = [];
    var run = { text: '', x: line[0].x, endX: line[0].x, y: line[0].y, height: line[0].height };
    for (var ci = 0; ci < line.length; ci++) {
      var ch = line[ci];
      if (ci > 0) {
        var prev = line[ci - 1];
        var gap = ch.x - (prev.x + prev.width);
        if (gap > gapThreshold) {
          run.text = run.text.replace(/\s+$/, '');
          if (run.text) runs.push(run);
          run = { text: '', x: ch.x, endX: ch.x, y: ch.y, height: ch.height };
        }
      }
      run.text += ch.ch;
      run.endX = ch.x + ch.width;
    }
    run.text = run.text.replace(/\s+$/, '');
    if (run.text) runs.push(run);
    var text = line.map(function (c) { return c.ch; }).join('').replace(/\s+$/, '');
    out.push({
      text: text,
      y: Math.round(line[0].y * 100) / 100,
      height: Math.round(line[0].height * 100) / 100,
      runs: runs.map(function (r) {
        return { text: r.text, x: Math.round(r.x * 100) / 100, width: Math.round((r.endX - r.x) * 100) / 100 };
      })
    });
  }
  return out;
}

// Render one page to a PNG file. `scale` multiplies the page size; 2 gives a
// 144 dpi raster, which is enough for a legibility readback and for OCR.
function renderPagePNG(page, path, scale) {
  var box = pageBox(page);
  var s = scale || 2;
  var width = Math.round(box.width * s);
  var height = Math.round(box.height * s);
  var image = page.thumbnailOfSizeForBox($.CGSizeMake(width, height), 0);
  if (!image || image.isNil()) throw new Error('page rasterization failed');
  var rep = $.NSBitmapImageRep.imageRepWithData(image.TIFFRepresentation);
  if (!rep || rep.isNil()) throw new Error('page rasterization produced no bitmap');
  var data = rep.representationUsingTypeProperties(4, $.NSDictionary.dictionary);
  if (!data || data.isNil()) throw new Error('PNG encoding failed');
  var ok = data.writeToFileAtomically($(path), true);
  if (!ok) throw new Error('cannot write PNG: ' + path);
  return { path: path, width: int(rep.pixelsWide, width), height: int(rep.pixelsHigh, height) };
}

// Fraction of sampled pixels darker than `threshold`. A page that should carry
// text but reports almost no ink is blank or failed to render; a page with
// large dark areas and no text is likely an un-OCRed scan.
function inkRatio(page, threshold) {
  var box = pageBox(page);
  if (!box.width || !box.height) return null;
  var width = 300;
  var height = Math.max(1, Math.round(width * box.height / box.width));
  var image = page.thumbnailOfSizeForBox($.CGSizeMake(width, height), 0);
  if (!image || image.isNil()) return null;
  var rep = $.NSBitmapImageRep.imageRepWithData(image.TIFFRepresentation);
  if (!rep || rep.isNil()) return null;
  var w = int(rep.pixelsWide, 0);
  var h = int(rep.pixelsHigh, 0);
  var t = typeof threshold === 'number' ? threshold : 0.85;
  var dark = 0;
  var total = 0;
  for (var y = 0; y < h; y += 2) {
    for (var x = 0; x < w; x += 2) {
      var c = rep.colorAtXY(x, y);
      if (!c) continue;
      var luminance = c.redComponent * 0.299 + c.greenComponent * 0.587 + c.blueComponent * 0.114;
      if (luminance < t) dark++;
      total++;
    }
  }
  if (!total) return null;
  return Math.round(dark / total * 10000) / 10000;
}

// Route the text baseline for each line so an invisible OCR layer lands on top
// of the glyphs it describes. CoreText draws from the baseline upward, so the
// descent is subtracted once at draw time.
function measureLines(lines, fontSize, fontPath) {
  var font = resolveFont(fontPath, fontSize);
  var attrs = $.NSMutableDictionary.dictionary;
  attrs.setObjectForKey(font, 'NSFont');
  return lines.map(function (line) {
    var cf = $.CFAttributedStringCreate($(), $(line), attrs);
    var ts = $.CTTypesetterCreateWithAttributedString(cf);
    var n = Number($.CTTypesetterSuggestLineBreak(ts, 0, 100000));
    if (!n) return 0;
    var ctLine = $.CTTypesetterCreateLine(ts, $.CFRangeMake(0, n));
    var bounds = $.CTLineGetBoundsWithOptions(ctLine, 0);
    return bounds.size.width;
  });
}

// Font resolution order: the name the caller asked for, then the Korean UI
// face, then the system face, then Helvetica. A missing Korean-capable face
// silently produces tofu boxes, so the last resort is reported by the caller.
function resolveFont(fontPath, size) {
  var font = null;
  if (fontPath) {
    font = $.NSFont.fontWithNameSize($(fontPath), size);
    if (font && !font.isNil()) return font;
  }
  font = $.NSFont.fontWithNameSize('AppleSDGothicNeo-Regular', size);
  if (font && !font.isNil()) return font;
  font = $.NSFont.systemFontOfSize(size);
  if (font && !font.isNil()) return font;
  return $.NSFont.fontWithNameSize('Helvetica', size);
}

// Draw one line of text at a baseline position through CoreText. Used for the
// visible text of the native composer and for watermark text.
function drawLine(ctx, text, x, baselineY, options) {
  var o = options || {};
  var color = o.color || [0, 0, 0, 1];
  if (isSurface(ctx)) {
    ctx.ops.push({
      op: 'text',
      text: text,
      x: x,
      y: baselineY,
      size: o.size || 11,
      fontPath: o.fontPath || null,
      color: color,
      invisible: Boolean(o.invisible)
    });
    return;
  }
  drawTextNow(ctx, {
    text: text,
    x: x,
    y: baselineY,
    size: o.size || 11,
    fontPath: o.fontPath || null,
    color: color,
    invisible: Boolean(o.invisible)
  });
}

// One font lookup per run: an attributed string is built at replay time, when
// the target CGContext for that page actually exists.
function drawTextNow(ctx, op) {
  var font = resolveFont(op.fontPath, op.size);
  var color = op.color;
  var attrs = $.NSMutableDictionary.dictionary;
  attrs.setObjectForKey(font, 'NSFont');
  attrs.setObjectForKey(
    $.NSColor.colorWithCalibratedRedGreenBlueAlpha(color[0], color[1], color[2], color.length > 3 ? color[3] : 1),
    'NSColor'
  );
  var cf = $.CFAttributedStringCreate($(), $(op.text), attrs);
  var line = $.CTLineCreateWithAttributedString(cf);
  $.CGContextSaveGState(ctx);
  $.CGContextSetTextDrawingMode(ctx, op.invisible ? 3 : 0);
  $.CGContextSetTextPosition(ctx, op.x, op.y);
  $.CTLineDraw(line, ctx);
  $.CGContextRestoreGState(ctx);
}

function lineWidth(text, size, fontPath) {
  return measureLines([text], size || 11, fontPath)[0] || 0;
}

// Split `text` into lines that fit `maxWidth`, breaking at spaces and at CJK
// character boundaries. CoreText suggests the break so the result matches what
// the renderer would produce instead of a naive character count.
function wrapText(text, maxWidth, size, fontPath) {
  var font = resolveFont(fontPath, size || 11);
  var attrs = $.NSMutableDictionary.dictionary;
  attrs.setObjectForKey(font, 'NSFont');
  var out = [];
  var paragraphs = String(text).split(/\r?\n/);
  for (var p = 0; p < paragraphs.length; p++) {
    var source = paragraphs[p];
    if (!source) { out.push(''); continue; }
    var cf = $.CFAttributedStringCreate($(), $(source), attrs);
    var ts = $.CTTypesetterCreateWithAttributedString(cf);
    var start = 0;
    var total = source.length;
    while (start < total) {
      var n = Number($.CTTypesetterSuggestLineBreak(ts, start, maxWidth));
      if (!n || n <= 0) n = 1;
      out.push(source.substr(start, n));
      start += n;
    }
  }
  return out;
}

// Page drawing goes through a recorded-op surface rather than a live
// CGPDFContext. JXA drops CGRect arguments at the C boundary, so
// CGPDFContextCreate always builds a 612x792 Letter canvas no matter what size
// is asked for: every A4 document came out Letter with its top 50 pt clipped,
// and no MediaBox value (NSValue, CFData, MediaBox dict key) changes it. An
// NSView subclass exporting dataWithPDFInsideRect does honour the rect, keeps
// text and embedded fonts, and gives one true-sized PDF per page, which is why
// the primitives record and the recorder replays into that view.
var SURFACE_OPS = null;
var SURFACE_VIEW = null;

function surfaceViewClass() {
  if (SURFACE_VIEW) return SURFACE_VIEW;
  // registerSubclass returns a result object, not the class, so the class is
  // fetched back by name from the global scope after registration.
  ObjC.registerSubclass({
    name: 'HyperPDFPageView',
    superclass: 'NSView',
    methods: {
      'drawRect:': {
        types: ['void', '{CGRect={CGPoint=dd}{CGSize=dd}}', '@', ':'],
        implementation: function (rect) {
          replayOps($.NSGraphicsContext.currentContext.CGContext, SURFACE_OPS || []);
        }
      }
    }
  });
  SURFACE_VIEW = $['HyperPDFPageView'];
  if (!SURFACE_VIEW) throw new Error('could not register the page view class');
  return SURFACE_VIEW;
}

function isSurface(ctx) {
  return Boolean(ctx) && ctx.kind === 'cursor-surface';
}

function replayOps(ctx, ops) {
  for (var i = 0; i < ops.length; i++) {
    var op = ops[i];
    switch (op.op) {
      case 'save': $.CGContextSaveGState(ctx); break;
      case 'restore': $.CGContextRestoreGState(ctx); break;
      case 'translate': $.CGContextTranslateCTM(ctx, op.x, op.y); break;
      case 'scale': $.CGContextScaleCTM(ctx, op.x, op.y); break;
      case 'rotate': $.CGContextRotateCTM(ctx, op.angle); break;
      case 'fillRect':
        $.CGContextSetRGBFillColor(ctx, op.color[0], op.color[1], op.color[2], op.color.length > 3 ? op.color[3] : 1);
        $.CGContextFillRect(ctx, $.CGRectMake(op.x, op.y, op.w, op.h));
        break;
      case 'stroke':
        $.CGContextSetRGBStrokeColor(ctx, op.color[0], op.color[1], op.color[2], op.color.length > 3 ? op.color[3] : 1);
        $.CGContextSetLineWidth(ctx, op.width);
        $.CGContextMoveToPoint(ctx, op.x1, op.y1);
        $.CGContextAddLineToPoint(ctx, op.x2, op.y2);
        $.CGContextStrokePath(ctx);
        break;
      case 'text': drawTextNow(ctx, op); break;
      case 'page': op.page.drawWithBoxToContext(0, ctx); break;
      case 'annotation': op.annotation.drawWithBoxInContext(0, ctx); break;
      default: break;
    }
  }
}

function newContext(path, width, height) {
  return {
    kind: 'cursor-surface',
    path: path,
    pages: [],
    ops: null,
    width: width,
    height: height
  };
}

function beginPage(ctx, width, height) {
  if (!isSurface(ctx)) throw new Error('beginPage needs a surface');
  ctx.ops = [];
  ctx.pageWidth = width;
  ctx.pageHeight = height;
}

function endPage(ctx) {
  if (!isSurface(ctx)) throw new Error('endPage needs a surface');
  if (!ctx.ops) throw new Error('endPage without beginPage');
  ctx.pages.push({ width: ctx.pageWidth, height: ctx.pageHeight, ops: ctx.ops });
  ctx.ops = null;
}

function closeContext(ctx) {
  if (!isSurface(ctx)) return;
  if (!ctx.pages.length) throw new Error('no pages were begun before close');
  var viewClass = surfaceViewClass();
  var parts = [];
  try {
    var combined = $.PDFDocument.alloc.init;
    for (var i = 0; i < ctx.pages.length; i++) {
      var spec = ctx.pages[i];
      var rect = $.CGRectMake(0, 0, spec.width, spec.height);
      var view = viewClass.alloc.initWithFrame(rect);
      SURFACE_OPS = spec.ops;
      var data = view.dataWithPDFInsideRect(rect);
      SURFACE_OPS = null;
      if (!data || data.isNil()) throw new Error('page ' + (i + 1) + ' produced no PDF data');
      var partPath = ctx.path + '.part-' + (i + 1);
      if (!data.writeToFileAtomically($(partPath), true)) throw new Error('cannot write page ' + (i + 1));
      parts.push(partPath);
      var partDoc = $.PDFDocument.alloc.initWithURL($.NSURL.fileURLWithPath($(partPath)));
      if (!partDoc || partDoc.isNil()) throw new Error('page ' + (i + 1) + ' is not a readable PDF');
      combined.insertPageAtIndex(partDoc.pageAtIndex(0), i);
    }
    if (!combined.writeToURL($.NSURL.fileURLWithPath($(ctx.path)))) {
      throw new Error('cannot write PDF: ' + ctx.path);
    }
  } finally {
    // Per-page PDFs exist only to be joined; a failed write must not leave
    // .part-N files beside the output.
    for (var p = 0; p < parts.length; p++) {
      $.NSFileManager.defaultManager.removeItemAtPathError($(parts[p]), $());
    }
    ctx.pages = [];
  }
}

// Save/restore and transforms are recorded like everything else, so callers
// never touch a live CGContext of their own.
function ctxSave(ctx) {
  if (isSurface(ctx)) { ctx.ops.push({ op: 'save' }); return; }
  $.CGContextSaveGState(ctx);
}

function ctxRestore(ctx) {
  if (isSurface(ctx)) { ctx.ops.push({ op: 'restore' }); return; }
  $.CGContextRestoreGState(ctx);
}

function ctxTranslate(ctx, x, y) {
  if (isSurface(ctx)) { ctx.ops.push({ op: 'translate', x: x, y: y }); return; }
  $.CGContextTranslateCTM(ctx, x, y);
}

function ctxScale(ctx, x, y) {
  if (isSurface(ctx)) { ctx.ops.push({ op: 'scale', x: x, y: y }); return; }
  $.CGContextScaleCTM(ctx, x, y);
}

function ctxRotate(ctx, angle) {
  if (isSurface(ctx)) { ctx.ops.push({ op: 'rotate', angle: angle }); return; }
  $.CGContextRotateCTM(ctx, angle);
}

function fillRect(ctx, x, y, width, height, color) {
  if (isSurface(ctx)) {
    ctx.ops.push({ op: 'fillRect', x: x, y: y, w: width, h: height, color: color });
    return;
  }
  $.CGContextSetRGBFillColor(ctx, color[0], color[1], color[2], color.length > 3 ? color[3] : 1);
  $.CGContextFillRect(ctx, $.CGRectMake(x, y, width, height));
}

function strokeLine(ctx, x1, y1, x2, y2, color, lineWidth) {
  if (isSurface(ctx)) {
    ctx.ops.push({ op: 'stroke', x1: x1, y1: y1, x2: x2, y2: y2, color: color, width: lineWidth || 0.5 });
    return;
  }
  $.CGContextSetRGBStrokeColor(ctx, color[0], color[1], color[2], color.length > 3 ? color[3] : 1);
  $.CGContextSetLineWidth(ctx, lineWidth || 0.5);
  $.CGContextMoveToPoint(ctx, x1, y1);
  $.CGContextAddLineToPoint(ctx, x2, y2);
  $.CGContextStrokePath(ctx);
}

// Redraw a page into the current context. PDF page content is authored in a
// bottom-left origin space, so the caller flips the context only when drawing
// annotation text in top-left coordinates.
function drawPage(ctx, page) {
  if (isSurface(ctx)) { ctx.ops.push({ op: 'page', page: page }); return; }
  page.drawWithBoxToContext(0, ctx);
}

// Bake one annotation into the page. FreeText and stamps live outside the page
// content stream, so a print-only copy has to draw them; a surface records the
// reference and replays it at export time.
function drawAnnotation(ctx, annotation) {
  if (isSurface(ctx)) { ctx.ops.push({ op: 'annotation', annotation: annotation }); return; }
  annotation.drawWithBoxInContext(0, ctx);
}

// Text watermark: rotate around the page center and stamp one line per page.
function watermarkPage(ctx, pageBoxRect, text, options) {
  var o = options || {};
  var size = o.size || 48;
  var angle = typeof o.angle === 'number' ? o.angle : 45;
  var cx = pageBoxRect.origin.x + pageBoxRect.size.width / 2;
  var cy = pageBoxRect.origin.y + pageBoxRect.size.height / 2;
  var width = lineWidth(text, size, o.fontPath);
  ctxSave(ctx);
  ctxTranslate(ctx, cx, cy);
  ctxRotate(ctx, angle * Math.PI / 180);
  drawLine(ctx, text, -width / 2, -size / 3, {
    size: size,
    color: o.color || [0.5, 0.5, 0.5, 0.3],
    fontPath: o.fontPath
  });
  ctxRestore(ctx);
}

// Vision OCR on one rendered page. Returns recognized observations with PDF
// coordinates so a caller can place an invisible text layer.
function ocrImage(path, languages) {
  var image = $.NSImage.alloc.initWithContentsOfFile($(path));
  if (!image || image.isNil()) throw new Error('OCR input is not an image: ' + path);
  var cg = image.CGImageForProposedRectContextHints($(), $(), $());
  if (!cg) throw new Error('OCR could not decode the image');
  var request = $.VNRecognizeTextRequest.alloc.init;
  request.recognitionLevel = 0;
  request.usesLanguageCorrection = true;
  if (languages && languages.length) request.recognitionLanguages = $(languages);
  var handler = $.VNImageRequestHandler.alloc.initWithCGImageOptions(cg, $());
  var error = $();
  var ok = handler.performRequestsError($([request]), error);
  if (!ok) throw new Error('OCR request failed');
  var results = request.results;
  var out = [];
  for (var i = 0; i < results.count; i++) {
    var observation = results.objectAtIndex(i);
    var candidates = observation.topCandidates(1);
    if (!candidates || candidates.count === 0) continue;
    var top = candidates.objectAtIndex(0);
    var box = observation.boundingBox;
    out.push({
      text: unwrapString(top.string),
      confidence: Math.round(int(top.confidence, 0) * 100) / 100,
      x: int(box.origin.x, 0),
      y: int(box.origin.y, 0),
      width: int(box.size.width, 0),
      height: int(box.size.height, 0)
    });
  }
  return out;
}

function listAnnotations(page) {
  var annotations = page.annotations;
  var out = [];
  if (!annotations || annotations.isNil()) return out;
  for (var i = 0; i < annotations.count; i++) {
    var a = annotations.objectAtIndex(i);
    var fieldName = null;
    var widgetType = null;
    var value = null;
    try { fieldName = a.fieldName ? unwrapString(a.fieldName) : null; } catch (e) { fieldName = null; }
    try { widgetType = a.widgetFieldType ? unwrapString(a.widgetFieldType) : null; } catch (e) { widgetType = null; }
    try { value = a.widgetStringValue ? unwrapString(a.widgetStringValue) : null; } catch (e) { value = null; }
    var b = a.bounds;
    out.push({
      type: unwrapString(a.type),
      fieldName: fieldName,
      widgetType: widgetType,
      value: value,
      rect: [int(b.origin.x, 0), int(b.origin.y, 0), int(b.size.width, 0), int(b.size.height, 0)],
      contents: a.contents ? String(unwrapString(a.contents)).slice(0, 200) : null
    });
  }
  return out;
}

function setFieldValue(page, fieldName, value) {
  var annotations = page.annotations;
  if (!annotations || annotations.isNil()) return 0;
  var hits = 0;
  for (var i = 0; i < annotations.count; i++) {
    var a = annotations.objectAtIndex(i);
    var name = null;
    try { name = a.fieldName ? unwrapString(a.fieldName) : ''; } catch (e) { name = ''; }
    if (name !== fieldName) continue;
    a.widgetStringValue = value;
    hits++;
  }
  return hits;
}

function addFreeText(page, rect, text, options) {
  var o = options || {};
  var props = $.NSDictionary.dictionary;
  var annotation = $.PDFAnnotation.alloc.initWithBoundsForTypeWithProperties(rect, $.PDFAnnotationSubtypeFreeText, props);
  if (!annotation || annotation.isNil()) throw new Error('cannot create annotation');
  annotation.contents = text;
  annotation.font = resolveFont(o.fontPath, o.size || 24);
  var color = o.color || [0.85, 0.2, 0.2, 0.5];
  annotation.fontColor = $.NSColor.colorWithCalibratedRedGreenBlueAlpha(color[0], color[1], color[2], color[3]);
  page.addAnnotation(annotation);
  return annotation;
}

function documentAttributes(doc) {
  var source = doc.documentAttributes;
  var out = {};
  if (!source || source.isNil()) return out;
  var keys = ['Title', 'Author', 'Subject', 'Keywords', 'Creator', 'Producer', 'CreationDate', 'ModDate'];
  var names = [
    $.PDFDocumentTitleAttribute,
    $.PDFDocumentAuthorAttribute,
    $.PDFDocumentSubjectAttribute,
    $.PDFDocumentKeywordsAttribute,
    $.PDFDocumentCreatorAttribute,
    $.PDFDocumentProducerAttribute,
    $.PDFDocumentCreationDateAttribute,
    $.PDFDocumentModificationDateAttribute
  ];
  for (var i = 0; i < names.length; i++) {
    try {
      var value = source.objectForKey(names[i]);
      if (value && !value.isNil()) out[keys[i]] = String(unwrapString(value));
    } catch (e) {
      // A missing attribute is not an error.
    }
  }
  return out;
}

function applyAttributes(doc, attributes) {
  var current = doc.documentAttributes;
  var target = current && !current.isNil() ? $.NSMutableDictionary.dictionaryWithDictionary(current) : $.NSMutableDictionary.dictionary;
  var map = {
    Title: $.PDFDocumentTitleAttribute,
    Author: $.PDFDocumentAuthorAttribute,
    Subject: $.PDFDocumentSubjectAttribute,
    Keywords: $.PDFDocumentKeywordsAttribute,
    Creator: $.PDFDocumentCreatorAttribute
  };
  // CLI keys arrive lowercase (`title=...`); match the canonical attribute
  // names case-insensitively so the mapping is never silently skipped.
  var byLower = {};
  for (var name in map) {
    if (Object.prototype.hasOwnProperty.call(map, name)) byLower[name.toLowerCase()] = name;
  }
  var applied = [];
  for (var key in attributes) {
    if (!Object.prototype.hasOwnProperty.call(attributes, key)) continue;
    var canonical = byLower[String(key).toLowerCase()];
    if (!canonical) continue;
    var value = attributes[key];
    if (value === null || value === undefined) continue;
    target.setObjectForKey($(String(value)), map[canonical]);
    applied.push(canonical);
  }
  doc.documentAttributes = target;
  return applied;
}

// Scan the raw bytes for structures that PDFKit does not expose. This is not a
// parser: it answers "did the writer embed fonts, emit a structure tree, tag
// the language, or leave Type3 glyph fallbacks" for a post-generation check.
function rawScan(path) {
  var data = $.NSData.dataWithContentsOfFile($(path));
  if (!data || data.isNil()) throw new Error('cannot read ' + path);
  var bytes = int(data.length, 0);
  var ascii = $.NSString.alloc.initWithDataEncoding(data, NSASCII);
  var text = ascii && !ascii.isNil() ? unwrapString(ascii) : '';
  function count(pattern) {
    var total = 0;
    var at = 0;
    for (;;) {
      var found = text.indexOf(pattern, at);
      if (found < 0) break;
      total++;
      at = found + pattern.length;
    }
    return total;
  }
  var header = text.slice(0, 16);
  return {
    bytes: bytes,
    version: (header.match(/^%PDF-([0-9.]+)/) || [])[1] || null,
    encrypted: count('/Encrypt') > 0,
    objectStreams: count('/ObjStm'),
    crossReferenceStreams: count('/Type /XRef') + count('/Type/XRef'),
    fontFile2: count('/FontFile2'),
    fontFile3: count('/FontFile3'),
    type0: count('/Type0') + count('/Type0 '),
    type3: count('/Subtype /Type3') + count('/Subtype/Type3'),
    structureTree: count('/StructTreeRoot'),
    markInfo: count('/MarkInfo'),
    language: (text.match(/\/Lang\s*\(([^)]{0,24})\)/) || [])[1] || null,
    images: count('/Subtype /Image') + count('/Subtype/Image'),
    acroForm: count('/AcroForm'),
    linearized: count('/Linearized') > 0,
    javascript: count('/JavaScript') + count('/JS'),
    launch: count('/Launch'),
    embeddedFiles: count('/EmbeddedFile'),
    attachments: count('/FileAttachment')
  };
}

// CoreGraphics writes an /Info dictionary but no /Lang entry, and PDFKit has no
// API for it. Korean text without /Lang makes a screen reader guess the
// language and read Hangul with English pronunciation rules, so the tag is
// added by an incremental update: the original bytes stay untouched, a new
// catalogue object carries the tag, and a second cross-reference section points
// back at the first. This is the append-only form the PDF specification defines
// for exactly this situation, so existing offsets stay valid.
function taskOutput(commandPath, taskArgs) {
  var task = $.NSTask.alloc.init;
  task.launchPath = $(commandPath);
  task.arguments = $(taskArgs);
  var pipe = $.NSPipe.pipe;
  task.standardOutput = pipe;
  task.standardError = pipe;
  try {
    task.launch;
  } catch (error) {
    return { launched: false, status: -1, output: String(error && error.message || error) };
  }
  task.waitUntilExit;
  var data = pipe.fileHandleForReading.readDataToEndOfFile;
  var text = ObjC.unwrap($.NSString.alloc.initWithDataEncoding(data, NSUTF8)) || '';
  return { launched: true, status: Number(task.terminationStatus), output: text };
}

// Chromium renders HTML to PDF with a real print engine and can emit a tagged
// PDF, which is the only path here that produces a structure tree. The binary
// is discovered rather than assumed: a Playwright install, a Chrome app bundle,
// or a headless shell on PATH all work, and a missing binary is reported as a
// capability gap instead of a failure.
function findHtmlRenderer(explicit) {
  if (explicit) {
    return fileExists(explicit) ? explicit : null;
  }
  var candidates = [];
  var home = ObjC.unwrap($.NSUserName());
  var known = [
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Chromium.app/Contents/MacOS/Chromium',
    '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
    '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'
  ];
  for (var i = 0; i < known.length; i++) candidates.push(known[i]);
  var cacheRoot = '/Users/' + home + '/Library/Caches/ms-playwright';
  var listing = $.NSFileManager.defaultManager.contentsOfDirectoryAtPathError($(cacheRoot), $());
  if (listing && !listing.isNil()) {
    for (var j = 0; j < listing.count; j++) {
      var entry = unwrapString(listing.objectAtIndex(j));
      if (!/^chromium/.test(entry)) continue;
      var dir = cacheRoot + '/' + entry;
      var inner = $.NSFileManager.defaultManager.contentsOfDirectoryAtPathError($(dir), $());
      if (!inner || inner.isNil()) continue;
      for (var k = 0; k < inner.count; k++) {
        var bin = unwrapString(inner.objectAtIndex(k));
        if (!/^chrome/.test(bin)) continue;
        var path = dir + '/' + bin + '/chrome-headless-shell';
        if (fileExists(path)) candidates.push(path);
        var path2 = dir + '/' + bin + '/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing';
        if (fileExists(path2)) candidates.push(path2);
      }
    }
  }
  for (var c = 0; c < candidates.length; c++) {
    if (fileExists(candidates[c])) return candidates[c];
  }
  return null;
}

// HTML → PDF through the discovered renderer. `tagged` asks for a structure
// tree; the renderer silently ignores the flag if the build does not support
// it, so the caller always re-scans the output rather than trusting the flag.
function renderHTML(htmlPath, outPath, options) {
  var o = options || {};
  var renderer = findHtmlRenderer(o.renderer);
  if (!renderer) {
    return { rendered: false, code: 'NO_HTML_RENDERER', renderer: null };
  }
  var headlessArgs = [
    '--headless',
    '--disable-gpu',
    '--no-sandbox',
    '--disable-dev-shm-usage',
    '--virtual-time-budget=' + (o.virtualTimeBudget || 8000),
    '--print-to-pdf=' + outPath,
    '--no-pdf-header-footer'
  ];
  if (o.tagged !== false) headlessArgs.unshift('--export-tagged-pdf');
  headlessArgs.push('file://' + htmlPath);
  var result = taskOutput(renderer, headlessArgs);
  var produced = fileExists(outPath);
  return {
    rendered: produced,
    renderer: renderer,
    status: result.status,
    tagged: o.tagged !== false,
    log: result.launched ? result.output.slice(0, 600) : result.output,
    code: produced ? null : 'RENDER_FAILED'
  };
}

function injectLanguage(path, language) {
  var data = $.NSData.dataWithContentsOfFile($(path));
  if (!data || data.isNil()) throw new Error('cannot read ' + path);
  var raw = ObjC.unwrap($.NSString.alloc.initWithDataEncoding(data, NSASCII)) || '';
  if (!raw) throw new Error('cannot decode ' + path);
  if (/\/Lang\s*\(/.test(raw)) return { injected: false, reason: 'already tagged' };
  var catalogMatch = raw.match(/(\d+)\s+0\s+obj\s*<<([\s\S]{0,4000}?)\/Type\s*\/Catalog([\s\S]{0,4000}?)>>/);
  if (!catalogMatch) return { injected: false, reason: 'no uncompressed catalogue object to extend' };
  var catalogNumber = catalogMatch[1];
  var body = catalogMatch[2] + '/Type /Catalog' + catalogMatch[3];
  var pagesRef = body.match(/\/Pages\s+(\d+\s+0\s+R)/);
  if (!pagesRef) return { injected: false, reason: 'catalogue has no page tree reference' };

  var trailerStart = raw.lastIndexOf('trailer');
  var prevMatch = raw.slice(trailerStart).match(/startxref\s+(\d+)/);
  var rootMatch = raw.slice(trailerStart).match(/\/Root\s+(\d+)\s+0\s+R/);
  var infoMatch = raw.slice(trailerStart).match(/\/Info\s+(\d+)\s+0\s+R/);
  var prevXref = prevMatch ? Number(prevMatch[1]) : null;
  if (prevXref === null) return { injected: false, reason: 'no trailer to chain from' };

  var nextNumber = 1;
  var numbers = raw.match(/(\d+)\s+0\s+obj/g) || [];
  for (var i = 0; i < numbers.length; i++) {
    var n = Number(numbers[i].split(/\s+/)[0]);
    if (n >= nextNumber) nextNumber = n + 1;
  }
  var rootNumber = rootMatch ? Number(rootMatch[1]) : Number(catalogNumber);

  var escaped = String(language).replace(/([()\\])/g, '\\$1');
  var header = '\n' + nextNumber + ' 0 obj\n<< /Type /Catalog /Pages ' + pagesRef[1] + ' /Lang (' + escaped + ') >>\nendobj\n';
  // data.length is bridged as a string-like value; coerce before arithmetic or
  // the offsets concatenate and every cross-reference entry points nowhere.
  var baseOffset = int(data.length, 0);
  var objectOffset = baseOffset + 1;
  var xrefOffset = baseOffset + header.length;
  if (xrefOffset <= 0) return { injected: false, reason: 'could not compute an append offset' };
  var trailer = 'xref\n0 1\n0000000000 65535 f \n' + nextNumber + ' 1\n' +
    ('0000000000' + objectOffset).slice(-10) + ' 00000 n \n' +
    'trailer\n<< /Size ' + (nextNumber + 1) + ' /Root ' + nextNumber + ' 0 R' +
    (infoMatch ? ' /Info ' + infoMatch[1] + ' 0 R' : '') +
    ' /Prev ' + prevXref + ' >>\nstartxref\n' + xrefOffset + '\n%%EOF\n';

  var handle = $.NSFileHandle.fileHandleForWritingAtPath($(path));
  if (!handle || handle.isNil()) return { injected: false, reason: 'output is not writable' };
  handle.seekToEndOfFile;
  handle.writeData($(header + trailer).dataUsingEncoding(NSASCII));
  handle.closeFile;
  return { injected: true, language: language, catalog: nextNumber };
}

function ttcFontNames() {
  var found = [];
  var dirs = ['/System/Library/Fonts', '/Library/Fonts', '/Users/' + $.NSUserName().js + '/Library/Fonts'];
  for (var i = 0; i < dirs.length; i++) {
    var dir = dirs[i];
    var listing = $.NSFileManager.defaultManager.contentsOfDirectoryAtPathError($(dir), $());
    if (!listing || listing.isNil()) continue;
    for (var j = 0; j < listing.count; j++) {
      var name = unwrapString(listing.objectAtIndex(j));
      if (/\.(ttf|otf|ttc|otc)$/i.test(name)) found.push(dir + '/' + name);
    }
  }
  found.sort();
  return found;
}