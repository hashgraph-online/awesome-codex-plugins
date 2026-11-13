// engine.js — the hyper-pdf runtime. One entry point, one JSON result.
//
//   osascript -l JavaScript engine.js <command> [arguments...] [--flags]
//
// Every command prints exactly one JSON object on stdout and exits with 0 when
// the work succeeded, 1 when a check failed but the output exists for
// inspection, and 2 when the command could not run (bad arguments, missing
// input, unsupported reader). Nothing writes to stderr on a normal path; the
// caller reads stdout only.
//
// The engine is deliberately dependency-free: PDFKit and CoreGraphics ship with
// macOS, so no Homebrew formula, Python package, or network fetch is needed.
// On a host without those frameworks every command answers
// {status:"blocked", code:"NO_PDF_FRAMEWORK"} instead of guessing.
ObjC.import('Foundation');

// osascript passes the script path as written on the command line, so a bare
// `engine.js` arrives with no directory. Resolve it against the working
// directory; the sibling modules are always next to this file.
var RUNTIME_DIR = (function () {
  var args = $.NSProcessInfo.processInfo.arguments;
  var self = '';
  for (var i = 0; i < args.count; i++) {
    var value = ObjC.unwrap(args.objectAtIndex(i));
    if (/engine\.js$/.test(value)) self = value;
  }
  if (!self) return '';
  if (self.charAt(0) !== '/') {
    var cwd = ObjC.unwrap($.NSFileManager.defaultManager.currentDirectoryPath);
    self = cwd.replace(/\/$/, '') + '/' + self;
  }
  return self.replace(/\/[^\/]*$/, '');
})();

function emit(payload, exitCode) {
  var text = JSON.stringify(payload, null, 2);
  $.NSFileHandle.fileHandleWithStandardOutput.writeData($(text + '\n').dataUsingEncoding($.NSUTF8StringEncoding));
  // osascript only reports 0 or 1: $.exit does not exist in JXA, and an
  // uncaught exception is the only way to leave with a failure status. The
  // exit code therefore answers one question — was output produced — while the
  // JSON `status` field carries the finer distinction.
  if (exitCode === 2) {
    // A sentinel, not an Error: run() below must not print a second payload
    // for a status that was already reported.
    var stop = new Error(payload.code || 'error');
    stop.hyperPdfEmitted = true;
    throw stop;
  }
}

// osascript runs this file as a module, so a module's function declarations do
// not leak into scope. Indirect eval evaluates in the global scope, which is
// what makes the primitives callable from here; the required-name check then
// turns a broken or missing module into a named failure instead of a TypeError
// halfway through a document.
var REQUIRED_PRIMITIVES = [
  'loadDoc', 'saveDoc', 'isLocked', 'unlock', 'pageBox', 'pageRotation',
  'pageText', 'docText', 'textRuns', 'renderPagePNG', 'inkRatio', 'drawLine',
  'newContext', 'beginPage', 'endPage', 'closeContext', 'drawPage',
  'watermarkPage', 'ocrImage', 'listAnnotations', 'setFieldValue',
  'addFreeText', 'documentAttributes', 'applyAttributes', 'rawScan',
  'ttcFontNames', 'readTextFile', 'writeTextFile', 'fileExists',
  'strokeLine', 'fillRect', 'wrapText', 'lineWidth', 'injectLanguage',
  'renderHTML', 'findHtmlRenderer', 'taskOutput', 'newEmptyDocument',
  'ctxSave', 'ctxRestore', 'ctxTranslate', 'ctxScale', 'ctxRotate', 'drawAnnotation'
];

function loadModule(name) {
  var path = RUNTIME_DIR + '/' + name;
  var source = $.NSString.stringWithContentsOfFileEncodingError($(path), $.NSUTF8StringEncoding, $());
  if (source === null || source === undefined) throw new Error('runtime module missing: ' + path);
  var indirect = eval;
  indirect(ObjC.unwrap(source));
  var missing = REQUIRED_PRIMITIVES.filter(function (key) {
    return indirect('typeof ' + key) === 'undefined';
  });
  if (missing.length) throw new Error('runtime module ' + name + ' is missing: ' + missing.join(', '));
  return true;
}

function parseArgs(argv) {
  var positional = [];
  var flags = {};
  for (var i = 0; i < argv.length; i++) {
    var token = argv[i];
    if (token.indexOf('--') === 0) {
      var name = token.slice(2);
      var eq = name.indexOf('=');
      if (eq >= 0) {
        flags[name.slice(0, eq)] = name.slice(eq + 1);
      } else if (i + 1 < argv.length && argv[i + 1].indexOf('--') !== 0) {
        flags[name] = argv[i + 1];
        i++;
      } else {
        flags[name] = true;
      }
    } else {
      positional.push(token);
    }
  }
  return { positional: positional, flags: flags };
}

function num(value, fallback) {
  if (value === undefined || value === null || value === true) return fallback;
  var parsed = Number(value);
  return isNaN(parsed) ? fallback : parsed;
}

function parsePages(spec, total) {
  // "1-3,7,10-" → [{from,to}] in 1-based inclusive page numbers.
  var out = [];
  if (!spec) return out;
  var parts = String(spec).split(',');
  for (var i = 0; i < parts.length; i++) {
    var piece = parts[i].trim();
    if (!piece) continue;
    var range = piece.match(/^(\d+)?\s*-\s*(\d+)?$/);
    if (range) {
      var from = range[1] ? Number(range[1]) : 1;
      var to = range[2] ? Number(range[2]) : total;
      if (from < 1) from = 1;
      if (to > total) to = total;
      if (from <= to) out.push({ from: from, to: to });
      continue;
    }
    var single = Number(piece);
    if (single >= 1 && single <= total) out.push({ from: single, to: single });
  }
  return out;
}

function main(argv) {
  var parsed = parseArgs(argv);
  var command = parsed.positional[0];
  var flags = parsed.flags;
  var args = parsed.positional.slice(1);

  if (!command || command === 'help' || flags.help) {
    emit({
      status: 'ok',
      commands: [
        'info <pdf>',
        'text <pdf> [--pages 1-3] [--runs]',
        'tables <pdf> [--pages]',
        'images <pdf> [--out-dir DIR]',
        'render <pdf> --out-dir DIR [--pages] [--scale 2]',
        'ocr <pdf> --out OUT.pdf [--pages] [--langs ko-KR,en-US]',
        'merge --out OUT.pdf <a.pdf> <b.pdf> ...',
        'split <pdf> --out-dir DIR [--pages] [--every N]',
        'rotate <pdf> --out OUT.pdf --angle 90 [--pages]',
        'watermark <pdf> --out OUT.pdf --text "..." [--angle] [--size] [--opacity]',
        'stamp <pdf> --out OUT.pdf --text "..." [--page N] [--x] [--y] [--size]',
        'encrypt <pdf> --out OUT.pdf [--user-password] [--owner-password]',
        'decrypt <pdf> --out OUT.pdf --password "..."',
        'metadata <pdf> [--set key=value] [--out OUT.pdf]',
        'form <pdf> [--fill name=value] [--out OUT.pdf]',
        'flatten <pdf> --out OUT.pdf',
        'check <pdf> [--pages] [--scan-threshold 0.02]',
        'fonts',
        'html <input.html> --out OUT.pdf [--renderer PATH] [--untagged]',
        'build --spec SPEC.json --out OUT.pdf'
      ]
    }, 0);
    return;
  }

  try {
    loadModule('native.js');
  } catch (error) {
    emit({ status: 'blocked', code: 'NO_PDF_FRAMEWORK', message: String(error && error.message || error) }, 2);
    return;
  }

  if (command === 'fonts') {
    emit({ status: 'ok', fonts: ttcFontNames() }, 0);
    return;
  }

  if (command === 'html') {
    if (!args[0] || !flags.out) {
      emit({ status: 'error', code: 'ARGS', message: 'html requires an input HTML file and --out' }, 2);
      return;
    }
    var htmlPath = args[0];
    if (!fileExists(htmlPath)) {
      emit({ status: 'error', code: 'NO_INPUT', message: 'input HTML not found: ' + htmlPath }, 2);
      return;
    }
    var renderOptions = {
      renderer: flags.renderer || null,
      tagged: flags.untagged ? false : true,
      virtualTimeBudget: num(flags['timeout-ms'], 8000)
    };
    var renderResult = renderHTML(htmlPath, flags.out, renderOptions);
    if (!renderResult.rendered) {
      emit({
        status: 'blocked',
        code: renderResult.code,
        message: renderResult.code === 'NO_HTML_RENDERER'
          ? 'No Chromium-based renderer was found. Pass --renderer /path/to/chrome, or build the document from a layout spec with `build --spec`.'
          : 'The renderer ran but produced no PDF. Check that the HTML loads its assets from absolute file:// paths.',
        renderer: renderResult.renderer,
        log: renderResult.log
      }, 2);
      return;
    }
    var htmlScan = rawScan(flags.out);
    var htmlIssues = [];
    if (htmlScan.structureTree === 0) htmlIssues.push('NO_STRUCTURE_TREE');
    if (htmlScan.fontFile2 + htmlScan.fontFile3 === 0) htmlIssues.push('FONT_NOT_EMBEDDED');
    if (htmlScan.type3 > 0) htmlIssues.push('TYPE3_GLYPHS');
    if (!htmlScan.language) htmlIssues.push('NO_LANGUAGE_TAG');
    var htmlDoc = loadDoc(flags.out);
    emit({
      status: htmlIssues.length ? 'caveated' : 'ok',
      out: flags.out,
      pages: pageCount(htmlDoc),
      renderer: renderResult.renderer,
      taggedRequested: renderResult.tagged,
      raw: htmlScan,
      issues: htmlIssues
    }, htmlIssues.length ? 1 : 0);
    return;
  }

  if (command === 'build') {
    if (!flags.spec || !flags.out) {
      emit({ status: 'error', code: 'ARGS', message: 'build requires --spec and --out' }, 2);
      return;
    }
    loadModule('compose.js');
    var spec = JSON.parse(readTextFile(flags.spec));
    var report = buildDocument(spec, flags.out);
    emit(report, report.status === 'ok' ? 0 : 1);
    return;
  }

  if (command === 'merge') {
    if (!flags.out || args.length === 0) {
      emit({ status: 'error', code: 'ARGS', message: 'merge requires --out and at least one input PDF' }, 2);
      return;
    }
    var merged = $.PDFDocument.alloc.init;
    var sources = [];
    for (var m = 0; m < args.length; m++) {
      var sourceDoc = loadDoc(args[m]);
      sources.push({ path: args[m], pages: pageCount(sourceDoc), locked: isLocked(sourceDoc) });
      for (var p = 0; p < pageCount(sourceDoc); p++) {
        merged.insertPageAtIndex(sourceDoc.pageAtIndex(p), merged.pageCount);
      }
    }
    saveDoc(merged, flags.out);
    emit({ status: 'ok', out: flags.out, pages: pageCount(merged), sources: sources }, 0);
    return;
  }

  if (!args[0]) {
    emit({ status: 'error', code: 'ARGS', message: command + ' requires an input PDF' }, 2);
    return;
  }

  var path = args[0];
  var doc = loadDoc(path);
  // `decrypt` owns its own password gate so it can tell a missing password
  // (ENCRYPTED) apart from a wrong one (BAD_PASSWORD).
  if (command !== 'decrypt' && isLocked(doc)) {
    var password = flags.password || flags['user-password'];
    if (!password || !unlock(doc, password)) {
      emit({ status: 'blocked', code: 'ENCRYPTED', message: 'the PDF is password protected; pass --password' }, 2);
      return;
    }
  }
  var total = pageCount(doc);

  switch (command) {
    case 'info': {
      var pages = [];
      for (var i = 0; i < total; i++) {
        var page = doc.pageAtIndex(i);
        var box = pageBox(page);
        pages.push({
          page: i + 1,
          width: Math.round(box.width * 100) / 100,
          height: Math.round(box.height * 100) / 100,
          rotation: pageRotation(page),
          textChars: pageText(page).length,
          annotations: listAnnotations(page).length
        });
      }
      emit({
        status: 'ok',
        path: path,
        pages: total,
        encrypted: isLocked(doc) || rawScan(path).encrypted,
        metadata: documentAttributes(doc),
        raw: rawScan(path),
        pageDetails: pages
      }, 0);
      return;
    }

    case 'text': {
      var wanted = parsePages(flags.pages, total);
      var scope = wanted.length ? wanted : [{ from: 1, to: total }];
      var out = [];
      for (var s = 0; s < scope.length; s++) {
        for (var n = scope[s].from; n <= scope[s].to; n++) {
          var page2 = doc.pageAtIndex(n - 1);
          var entry = { page: n, text: pageText(page2) };
          if (flags.runs) entry.lines = textRuns(page2);
          out.push(entry);
        }
      }
      var chars = out.reduce(function (acc, page3) { return acc + page3.text.length; }, 0);
      emit({
        status: 'ok',
        path: path,
        pages: total,
        extractedPages: out.length,
        characters: chars,
        scanned: chars === 0,
        content: out
      }, 0);
      return;
    }

    case 'tables': {
      var tableScope = parsePages(flags.pages, total);
      var tablePages = tableScope.length ? tableScope : [{ from: 1, to: total }];
      var tables = [];
      for (var t = 0; t < tablePages.length; t++) {
        for (var tn = tablePages[t].from; tn <= tablePages[t].to; tn++) {
          var tablePage = doc.pageAtIndex(tn - 1);
          var lines = textRuns(tablePage);
          var rows = lines.filter(function (line) { return line.runs.length > 1; });
          if (!rows.length) continue;
          var columns = Math.max.apply(null, rows.map(function (r) { return r.runs.length; }));
          tables.push({
            page: tn,
            columns: columns,
            rows: rows.map(function (r) {
              return r.runs.map(function (run) { return run.text; });
            })
          });
        }
      }
      emit({
        status: 'ok',
        path: path,
        tables: tables,
        limitation: 'Row boundaries come from baseline alignment and cell boundaries from horizontal gaps. A ruled table with wrapped cells or a borderless table with uneven spacing needs a manual read.'
      }, 0);
      return;
    }

    case 'images': {
      var outDir = flags['out-dir'];
      if (!outDir) {
        emit({ status: 'error', code: 'ARGS', message: 'images requires --out-dir' }, 2);
        return;
      }
      $.NSFileManager.defaultManager.createDirectoryAtPathWithIntermediateDirectoriesAttributesError($(outDir), true, $(), $());
      var extracted = [];
      for (var ip = 0; ip < total; ip++) {
        var imagePage = doc.pageAtIndex(ip);
        var imageBox = pageBox(imagePage);
        var rendered = renderPagePNG(imagePage, outDir + '/page-' + (ip + 1) + '.png', 2);
        extracted.push({
          page: ip + 1,
          raster: rendered.path,
          width: rendered.width,
          height: rendered.height,
          note: 'Page raster at 2x. Embedded image objects keep their own resolution and are not resampled by this command.'
        });
      }
      emit({ status: 'ok', path: path, pages: total, images: extracted }, 0);
      return;
    }

    case 'render': {
      var renderDir = flags['out-dir'];
      if (!renderDir) {
        emit({ status: 'error', code: 'ARGS', message: 'render requires --out-dir' }, 2);
        return;
      }
      $.NSFileManager.defaultManager.createDirectoryAtPathWithIntermediateDirectoriesAttributesError($(renderDir), true, $(), $());
      var scale = num(flags.scale, 2);
      var renderScope = parsePages(flags.pages, total);
      var renderPages = renderScope.length ? renderScope : [{ from: 1, to: total }];
      var files = [];
      for (var r = 0; r < renderPages.length; r++) {
        for (var rn = renderPages[r].from; rn <= renderPages[r].to; rn++) {
          var renderedPage = renderPagePNG(doc.pageAtIndex(rn - 1), renderDir + '/page-' + rn + '.png', scale);
          files.push({ page: rn, path: renderedPage.path, width: renderedPage.width, height: renderedPage.height });
        }
      }
      emit({ status: 'ok', path: path, scale: scale, files: files }, 0);
      return;
    }

    case 'split': {
      var splitDir = flags['out-dir'];
      if (!splitDir) {
        emit({ status: 'error', code: 'ARGS', message: 'split requires --out-dir' }, 2);
        return;
      }
      $.NSFileManager.defaultManager.createDirectoryAtPathWithIntermediateDirectoriesAttributesError($(splitDir), true, $(), $());
      var groups = [];
      var every = num(flags.every, 0);
      if (every > 0) {
        for (var e = 1; e <= total; e += every) {
          groups.push({ from: e, to: Math.min(total, e + every - 1) });
        }
      } else {
        var splitScope = parsePages(flags.pages, total);
        groups = splitScope.length ? splitScope : [];
      }
      if (!groups.length) {
        emit({ status: 'error', code: 'ARGS', message: 'split requires --pages or --every' }, 2);
        return;
      }
      var written = [];
      for (var g = 0; g < groups.length; g++) {
        var part = $.PDFDocument.alloc.init;
        var target = splitDir + '/pages-' + groups[g].from + '-' + groups[g].to + '.pdf';
        for (var gn = groups[g].from; gn <= groups[g].to; gn++) {
          part.insertPageAtIndex(doc.pageAtIndex(gn - 1), part.pageCount);
        }
        saveDoc(part, target);
        written.push({ from: groups[g].from, to: groups[g].to, out: target, pages: pageCount(part) });
      }
      emit({ status: 'ok', path: path, sourcePages: total, parts: written }, 0);
      return;
    }

    case 'rotate': {
      if (!flags.out) {
        emit({ status: 'error', code: 'ARGS', message: 'rotate requires --out' }, 2);
        return;
      }
      var angle = num(flags.angle, 90);
      if ([0, 90, 180, 270, -90, -180, -270].indexOf(angle) < 0) {
        emit({ status: 'error', code: 'ARGS', message: 'angle must be a multiple of 90' }, 2);
        return;
      }
      var rotateScope = parsePages(flags.pages, total);
      var rotatePages = rotateScope.length ? rotateScope : [{ from: 1, to: total }];
      var rotated = 0;
      for (var ro = 0; ro < rotatePages.length; ro++) {
        for (var ron = rotatePages[ro].from; ron <= rotatePages[ro].to; ron++) {
          var rotatePage = doc.pageAtIndex(ron - 1);
          var current = pageRotation(rotatePage);
          rotatePage.rotation = ((current + angle) % 360 + 360) % 360;
          rotated++;
        }
      }
      saveDoc(doc, flags.out);
      emit({ status: 'ok', out: flags.out, pagesRotated: rotated, angle: angle }, 0);
      return;
    }

    case 'watermark': {
      if (!flags.out || !flags.text) {
        emit({ status: 'error', code: 'ARGS', message: 'watermark requires --out and --text' }, 2);
        return;
      }
      var opacity = num(flags.opacity, 0.3);
      var wmSize = num(flags.size, 48);
      var wmAngle = num(flags.angle, 45);
      var fontPath = flags.font || null;
      var wmScope = parsePages(flags.pages, total);
      var wmPages = wmScope.length ? wmScope : [{ from: 1, to: total }];
      var wanted = {};
      for (var ws = 0; ws < wmPages.length; ws++) {
        for (var wn = wmPages[ws].from; wn <= wmPages[ws].to; wn++) wanted[wn] = true;
      }
      var firstBox = pageBox(doc.pageAtIndex(0));
      var ctx = newContext(flags.out, firstBox.width, firstBox.height);
      for (var wp = 0; wp < total; wp++) {
        var wmPage = doc.pageAtIndex(wp);
        var wmBox = pageBox(wmPage);
        beginPage(ctx, wmBox.width, wmBox.height);
        drawPage(ctx, wmPage);
        if (wanted[wp + 1]) {
          watermarkPage(ctx, $.CGRectMake(0, 0, wmBox.width, wmBox.height), flags.text, {
            size: wmSize,
            angle: wmAngle,
            color: [0.5, 0.5, 0.5, opacity],
            fontPath: fontPath
          });
        }
        endPage(ctx);
      }
      closeContext(ctx);
      emit({ status: 'ok', out: flags.out, pages: total, watermarked: Object.keys(wanted).length, text: flags.text }, 0);
      return;
    }

    case 'stamp': {
      if (!flags.out || !flags.text) {
        emit({ status: 'error', code: 'ARGS', message: 'stamp requires --out and --text' }, 2);
        return;
      }
      var stampPage = num(flags.page, 1);
      if (stampPage < 1 || stampPage > total) {
        emit({ status: 'error', code: 'ARGS', message: 'page is out of range' }, 2);
        return;
      }
      var stampTarget = doc.pageAtIndex(stampPage - 1);
      var stampBox = pageBox(stampTarget);
      var sx = num(flags.x, stampBox.width / 2 - 120);
      var sy = num(flags.y, stampBox.height - 120);
      var sw = num(flags.width, 240);
      var sh = num(flags.height, 60);
      addFreeText(stampTarget, $.CGRectMake(sx, sy, sw, sh), flags.text, {
        size: num(flags.size, 24),
        fontPath: flags.font || null,
        color: [0.85, 0.2, 0.2, num(flags.opacity, 0.5)]
      });
      saveDoc(doc, flags.out);
      emit({ status: 'ok', out: flags.out, page: stampPage, text: flags.text, rect: [sx, sy, sw, sh] }, 0);
      return;
    }

    case 'encrypt': {
      if (!flags.out) {
        emit({ status: 'error', code: 'ARGS', message: 'encrypt requires --out' }, 2);
        return;
      }
      var userPassword = flags['user-password'] || flags.password;
      var ownerPassword = flags['owner-password'] || userPassword;
      if (!userPassword) {
        emit({ status: 'error', code: 'ARGS', message: 'encrypt requires --user-password' }, 2);
        return;
      }
      var options = $.NSMutableDictionary.dictionary;
      options.setObjectForKey($(String(userPassword)), $.PDFDocumentUserPasswordOption);
      options.setObjectForKey($(String(ownerPassword)), $.PDFDocumentOwnerPasswordOption);
      saveDoc(doc, flags.out, options);
      var reopened = loadDoc(flags.out);
      emit({
        status: 'ok',
        out: flags.out,
        locked: isLocked(reopened),
        note: 'PDFKit applies RC4 128-bit owner/user passwords. It does not offer AES-256 or a permission bit set.'
      }, 0);
      return;
    }

    case 'decrypt': {
      if (!flags.out) {
        emit({ status: 'error', code: 'ARGS', message: 'decrypt requires --out' }, 2);
        return;
      }
      var pass = flags.password || flags['user-password'];
      if (isLocked(doc)) {
        if (!pass) {
          emit({ status: 'blocked', code: 'ENCRYPTED', message: 'the PDF is password protected; pass --password' }, 2);
          return;
        }
        if (!unlock(doc, pass)) {
          emit({ status: 'blocked', code: 'BAD_PASSWORD', message: 'the password did not unlock the document' }, 2);
          return;
        }
      }
      // Rewriting an unlocked document keeps its encryption dictionary.
      // Copying the pages into a new document is what actually drops it.
      var plain = newEmptyDocument();
      for (var dp = 0; dp < total; dp++) {
        plain.insertPageAtIndex(doc.pageAtIndex(dp), plain.pageCount);
      }
      saveDoc(plain, flags.out);
      var check = loadDoc(flags.out);
      var plainScan = rawScan(flags.out);
      emit({
        status: plainScan.encrypted ? 'caveated' : 'ok',
        out: flags.out,
        pages: pageCount(check),
        locked: isLocked(check),
        encryptedBytes: plainScan.encrypted,
        note: plainScan.encrypted
          ? 'the encryption dictionary survived the rewrite; the file still prompts for a password'
          : 'page content was copied into an unencrypted document'
      }, plainScan.encrypted ? 1 : 0);
      return;
    }

    case 'metadata': {
      var attributes = documentAttributes(doc);
      if (flags.set) {
        var pairs = String(flags.set).split(';');
        var changes = {};
        for (var pi = 0; pi < pairs.length; pi++) {
          var pair = pairs[pi].split('=');
          if (pair.length < 2) continue;
          changes[pair[0].trim()] = pair.slice(1).join('=').trim();
        }
        var appliedKeys = applyAttributes(doc, changes);
        var target2 = flags.out || path;
        if (flags.out || flags['in-place']) saveDoc(doc, target2);
        var afterAttributes = documentAttributes(doc);
        var notApplied = Object.keys(changes).filter(function (k) {
          return appliedKeys.indexOf(k) < 0 && appliedKeys.indexOf(k.charAt(0).toUpperCase() + k.slice(1).toLowerCase()) < 0;
        });
        emit({
          status: appliedKeys.length ? 'ok' : 'caveated',
          out: flags.out || flags['in-place'] ? target2 : null,
          before: attributes,
          after: afterAttributes,
          applied: appliedKeys,
          ignored: notApplied,
          appliedToFile: Boolean(flags.out || flags['in-place'])
        }, appliedKeys.length ? 0 : 1);
        return;
      }
      emit({ status: 'ok', path: path, attributes: attributes, raw: rawScan(path) }, 0);
      return;
    }

    case 'form': {
      var fields = [];
      for (var fp = 0; fp < total; fp++) {
        var formPage = doc.pageAtIndex(fp);
        var annotations = listAnnotations(formPage);
        for (var fa = 0; fa < annotations.length; fa++) {
          if (!annotations[fa].fieldName) continue;
          fields.push({
            page: fp + 1,
            name: annotations[fa].fieldName,
            type: annotations[fa].widgetType,
            value: annotations[fa].value,
            rect: annotations[fa].rect
          });
        }
      }
      var fill = flags.fill;
      if (!fill) {
        emit({ status: 'ok', path: path, fields: fields, fillable: fields.length > 0 }, 0);
        return;
      }
      if (!flags.out) {
        emit({ status: 'error', code: 'ARGS', message: 'form --fill requires --out' }, 2);
        return;
      }
      var assignments = String(fill).split(';');
      var applied = [];
      var missing = [];
      for (var ai = 0; ai < assignments.length; ai++) {
        var assignment = assignments[ai].split('=');
        if (assignment.length < 2) continue;
        var fieldName = assignment[0].trim();
        var fieldValue = assignment.slice(1).join('=').trim();
        var hits = 0;
        for (var hp = 0; hp < total; hp++) {
          hits += setFieldValue(doc.pageAtIndex(hp), fieldName, fieldValue);
        }
        if (hits) applied.push({ field: fieldName, value: fieldValue, widgets: hits });
        else missing.push(fieldName);
      }
      saveDoc(doc, flags.out);
      emit({ status: missing.length ? 'caveated' : 'ok', out: flags.out, applied: applied, missing: missing, fields: fields.length }, missing.length ? 1 : 0);
      return;
    }

    case 'flatten': {
      if (!flags.out) {
        emit({ status: 'error', code: 'ARGS', message: 'flatten requires --out' }, 2);
        return;
      }
      // Redraw every page into a fresh context. Annotations that PDFKit keeps
      // out of the page content (FreeText, stamps) are baked into the pixels;
      // interactive widgets are dropped, so the output is print-only.
      var flatBox = pageBox(doc.pageAtIndex(0));
      var flatCtx = newContext(flags.out, flatBox.width, flatBox.height);
      for (var flp = 0; flp < total; flp++) {
        var flatPage = doc.pageAtIndex(flp);
        var fb = pageBox(flatPage);
        beginPage(flatCtx, fb.width, fb.height);
        drawPage(flatCtx, flatPage);
        var flatAnnotations = flatPage.annotations;
        if (flatAnnotations && !flatAnnotations.isNil()) {
          for (var fla = 0; fla < flatAnnotations.count; fla++) {
            var annotation = flatAnnotations.objectAtIndex(fla);
            try { drawAnnotation(flatCtx, annotation); } catch (e) { /* not every subtype draws itself */ }
          }
        }
        endPage(flatCtx);
      }
      closeContext(flatCtx);
      var flatCheck = loadDoc(flags.out);
      var remainingFields = 0;
      for (var rp = 0; rp < pageCount(flatCheck); rp++) {
        var rest = listAnnotations(flatCheck.pageAtIndex(rp));
        for (var ri = 0; ri < rest.length; ri++) if (rest[ri].fieldName) remainingFields++;
      }
      emit({ status: 'ok', out: flags.out, pages: pageCount(flatCheck), remainingFormFields: remainingFields }, 0);
      return;
    }

    case 'ocr': {
      if (!flags.out) {
        emit({ status: 'error', code: 'ARGS', message: 'ocr requires --out' }, 2);
        return;
      }
      var langs = flags.langs ? String(flags.langs).split(',') : ['ko-KR', 'en-US'];
      var ocrScope = parsePages(flags.pages, total);
      var ocrPages = ocrScope.length ? ocrScope : [{ from: 1, to: total }];
      var tmpDir = flags['work-dir'] || (flags.out.replace(/\/[^\/]*$/, '') + '/.hyper-pdf-ocr');
      $.NSFileManager.defaultManager.createDirectoryAtPathWithIntermediateDirectoriesAttributesError($(tmpDir), true, $(), $());
      var firstOcrBox = pageBox(doc.pageAtIndex(0));
      var ocrCtx = newContext(flags.out, firstOcrBox.width, firstOcrBox.height);
      var ocrStats = [];
      var wantedOcr = {};
      for (var os = 0; os < ocrPages.length; os++) {
        for (var on = ocrPages[os].from; on <= ocrPages[os].to; on++) wantedOcr[on] = true;
      }
      for (var op = 0; op < total; op++) {
        var ocrPage = doc.pageAtIndex(op);
        var ob = pageBox(ocrPage);
        beginPage(ocrCtx, ob.width, ob.height);
        drawPage(ocrCtx, ocrPage);
        var observed = 0;
        if (wantedOcr[op + 1]) {
          var pngPath = tmpDir + '/ocr-page-' + (op + 1) + '.png';
          renderPagePNG(ocrPage, pngPath, 2);
          var observations = ocrImage(pngPath, langs);
          observed = observations.length;
          ctxSave(ocrCtx);
          ctxTranslate(ocrCtx, 0, ob.height);
          ctxScale(ocrCtx, 1, -1);
          for (var oi = 0; oi < observations.length; oi++) {
            var observation = observations[oi];
            var boxHeight = observation.height * ob.height;
            var fontSize = Math.max(4, boxHeight * 0.9);
            var baseY = (1 - observation.y) * ob.height - boxHeight * 0.1;
            drawLine(ocrCtx, observation.text, observation.x * ob.width, baseY, {
              size: fontSize,
              invisible: true,
              color: [0, 0, 0, 1]
            });
          }
          ctxRestore(ocrCtx);
        }
        endPage(ocrCtx);
        ocrStats.push({ page: op + 1, observations: observed });
      }
      closeContext(ocrCtx);
      var ocrResult = loadDoc(flags.out);
      emit({
        status: 'ok',
        out: flags.out,
        pages: pageCount(ocrResult),
        languages: langs,
        textCharacters: docText(ocrResult).length,
        pages_ocred: Object.keys(wantedOcr).length,
        perPage: ocrStats,
        note: 'Recognized text is drawn in invisible render mode, so the page looks unchanged while text selection, search, and copy recover the OCR result.'
      }, 0);
      return;
    }

    case 'check': {
      var issues = [];
      var scan = rawScan(path);
      var checkPages = [];
      var scanThreshold = num(flags['scan-threshold'], 0.02);
      for (var cp = 0; cp < total; cp++) {
        var checkPage = doc.pageAtIndex(cp);
        var chars = pageText(checkPage).length;
        var ink = inkRatio(checkPage);
        checkPages.push({
          page: cp + 1,
          textChars: chars,
          inkRatio: ink,
          likelyScan: chars < 20 && ink !== null && ink > scanThreshold
        });
        if (chars < 20 && ink !== null && ink > scanThreshold) {
          issues.push({ code: 'PAGE_NEEDS_OCR', page: cp + 1, detail: 'page carries ink but almost no extractable text' });
        }
        if (ink !== null && ink < 0.0005) {
          issues.push({ code: 'PAGE_BLANK', page: cp + 1, detail: 'page renders almost no ink' });
        }
      }
      if (scan.fontFile2 + scan.fontFile3 === 0) {
        issues.push({ code: 'FONT_NOT_EMBEDDED', detail: 'no embedded font program found; a reader without the font substitutes and reflows' });
      }
      if (scan.type3 > 0) {
        issues.push({ code: 'TYPE3_GLYPHS', detail: 'Type3 font programs found; these are rendered glyph outlines, not selectable text fonts' });
      }
      if (scan.structureTree === 0) {
        issues.push({ code: 'NO_STRUCTURE_TREE', detail: 'no structure tree; screen readers cannot recover reading order' });
      }
      if (!scan.language) {
        issues.push({ code: 'NO_LANGUAGE_TAG', detail: 'no /Lang entry; screen readers guess pronunciation' });
      }
      if (scan.encrypted) {
        issues.push({ code: 'ENCRYPTED', detail: 'document is encrypted; text extraction and assistive tech need the password' });
      }
      if (scan.javascript > 0) {
        issues.push({ code: 'CONTAINS_JAVASCRIPT', detail: 'document carries JavaScript actions' });
      }
      if (scan.launch > 0) {
        issues.push({ code: 'CONTAINS_LAUNCH_ACTION', detail: 'document carries a launch action' });
      }
      emit({
        status: 'ok',
        path: path,
        pages: total,
        raw: scan,
        pageChecks: checkPages,
        issues: issues,
        verdict: issues.filter(function (i) { return i.code === 'PAGE_BLANK' || i.code === 'PAGE_NEEDS_OCR'; }).length ? 'attn' : 'ok'
      }, 0);
      return;
    }

    default:
      emit({ status: 'error', code: 'UNKNOWN_COMMAND', message: 'unknown command: ' + command }, 2);
  }
}

function run(argv) {
  try {
    main(argv);
  } catch (error) {
    // The failing branch already wrote its payload; re-emitting here would
    // print two JSON objects and hide the real cause.
    if (error && error.hyperPdfEmitted) throw error;
    emit({
      status: 'error',
      code: 'RUNTIME',
      message: String(error && error.message || error),
      stack: error && error.stack ? String(error.stack).split('\n').slice(0, 4) : null
    }, 2);
  }
}