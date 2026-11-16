/* Widget kit runtime: state with revisions, requests with every outcome, strings, formatting.
   Inlined by scripts/build_widget.py before the widget's own script. Works outside Telegram
   (window.TelegramWidget undefined): it draws the empty state and never asks. */
var W = window.TelegramWidget || null;
var K = {
  lang: String(navigator.language || "en").slice(0, 2),
  S: {},
  R: {},
  I: {},
  busy: 0,
  // Strings: the build keeps one language (the bot sends the HTML that matches the user).
  t: function (k) {
    var d = K.I[K.lang] || K.I[Object.keys(K.I)[0]] || {};
    return k in d ? d[k] : k;
  },
  add: function (o) {
    for (var l in o) K.I[l] = Object.assign(K.I[l] || {}, o[l]);
  },
  $: function (i) { return document.getElementById(i); },
  h: function (tag, cls, txt) {
    var e = document.createElement(tag);
    e.className = cls || "";
    if (txt != null) e.textContent = txt;
    return e;
  },
  // Adopt a state only if it is not older than the newest one seen for this field.
  take: function (f, s) {
    if (!s || typeof s != "object" || (f in K.R && +s.r < K.R[f])) return 0;
    K.R[f] = +s.r || 0;
    K.S[f] = s;
    return 1;
  },
  load: function (f) {
    try { K.take(f, JSON.parse(W[f])); } catch (e) {}
  },
  can: function () { return !!(W && W.viewer && !W.isPreview); },
  st: function (txt, kind) {
    var n = K.$("st");
    if (n) { n.textContent = txt || ""; n.className = "st " + (kind || ""); }
  },
  // Call inside the tap handler, synchronously: one tap unlocks one request.
  ask: function (data, o) {
    o = o || {};
    if (!K.can() || K.busy) return 0;
    K.busy = 1;
    K.st(K.t("wait"));
    K.draw();
    // request() throws TypeError synchronously for empty or > 64-byte data; the executor runs
    // synchronously too (still inside the tap) and turns the throw into a rejection, so busy
    // never stays set.
    new Promise(function (r) { r(W.request(data)); }).then(function (a) {
      var r = {};
      try { r = JSON.parse(a.result) || {}; } catch (e) {}
      K.busy = 0;
      K.take(o.f || "chatData", r.s);
      var ok = r.ok && !r.err;
      K.st(r.msg || (ok ? o.done : K.t(r.err || "INVALID_ANSWER")), ok ? "ok" : "e");
      try { W.HapticFeedback.notificationOccurred(ok ? "success" : "error"); } catch (e) {}
      if (o.then) o.then(r);
      K.draw();
    }, function (e) {
      K.busy = 0;
      K.st(K.t(e.code || "FAILED"), "e");
      if (o.fail) o.fail(e);
      K.draw();
    });
    return 1;
  },
  // Background refresh: only the original in the private chat may ask without a tap.
  sync: function (data, f) {
    if (W && W.chatType == "private" && K.can() && !W.isForward && !K.busy)
      W.request(data).then(function (a) {
        try { if (K.take(f || "chatData", JSON.parse(a.result).s)) K.draw(); } catch (e) {}
      }, function () {});
  },
  nf: function (n, o) {
    try { return new Intl.NumberFormat(K.lang, o).format(n); } catch (e) { return "" + n; }
  },
  money: function (minor, cur) { return K.nf(minor / 100, { style: "currency", currency: cur }); },
  time: function (sec, o) {
    try { return new Intl.DateTimeFormat(K.lang, o || { hour: "2-digit", minute: "2-digit" }).format(sec * 1000); } catch (e) { return ""; }
  },
  start: function (draw, o) {
    o = o || {};
    K.draw = draw;
    var d = document.documentElement;
    if (!d.dir) d.dir = /^(ar|he|fa|ur)/.test(K.lang) ? "rtl" : "ltr";
    if (W) {
      K.load("chatData");
      K.load("publicData");
      W.onEvent("chatDataChanged", function () { K.load("chatData"); draw(); });
      W.onEvent("publicDataChanged", function () { K.load("publicData"); draw(); });
      W.onEvent("themeChanged", draw);
      if (o.watch) W.watchPublicData();
      if (o.sync) W.onEvent("activated", function () { K.sync(o.sync, o.f); });
    }
    draw();
    if (o.sync) K.sync(o.sync, o.f);
    if (W) W.ready();
  }
};
