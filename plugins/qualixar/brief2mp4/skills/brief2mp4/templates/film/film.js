/* film.js: one paused GSAP timeline for the archive desk look, built from the beats' data- attributes.
 * Rules it keeps: every state is a function of t (no clock, no random); starting states live in CSS; each beat's exit starts
 * after its entrances end; SVG routes are drawn with pixel lengths (getTotalLength); the camera moves at one
 * constant speed in every beat, so a hard cut joins two moves of the same velocity.
 * Beat attributes: data-t0, data-t1 (seconds; not HyperFrames' own data-start, which would let its runtime hide the beat), data-kind (archive | map | counter | title), data-fx, data-fy (focus 0-1),
 * data-s0 (start scale), data-rate (scale per second), data-vx, data-vy (px per second), data-dip-in, data-dip-out (seconds),
 * data-count-from, data-count-to, data-count-at, data-count-end (counter, seconds from the beat start). */
(function () {
  var W = 1296, H = 740;                                        /* the plate */
  var tl = gsap.timeline({ paused: true });
  var num = function (el, name, dflt) { var v = parseFloat(el.getAttribute("data-" + name)); return isNaN(v) ? dflt : v; };
  var clamp = function (v, lo, hi) { return Math.max(lo, Math.min(hi, v)); };
  var fmt = function (v, dec) { return v.toLocaleString("en-US", { minimumFractionDigits: dec, maximumFractionDigits: dec }); };

  function splitWords(el) {                                     /* inline spans only: a transformed span would count as its own text block */
    var words = el.textContent.trim().split(/\s+/);
    el.textContent = "";
    return words.map(function (w, i) {
      var span = document.createElement("span");
      span.className = "wi"; span.textContent = w; el.appendChild(span);
      if (i < words.length - 1) el.appendChild(document.createTextNode(" "));
      return span;
    });
  }
  function splitChars(el) {                                     /* typed date stamp: one span per character */
    var lines = [""], chars = [];                                 /* text, not markup: "&amp;" stays one "&", and <br> splits lines */
    Array.prototype.forEach.call(el.childNodes, function (n) {
      if (n.nodeName === "BR") lines.push(""); else lines[lines.length - 1] += n.textContent;
    });
    el.textContent = "";
    lines.forEach(function (line, li) {
      Array.from(line).forEach(function (c) {
        var s = document.createElement("span"); s.className = "ch"; s.textContent = c; el.appendChild(s); chars.push(s);
      });
      if (li < lines.length - 1) el.appendChild(document.createElement("br"));
    });
    return chars;
  }

  function camera(beat, t0, dur) {
    var target = beat.querySelector(".shot, .mapbox");
    if (!target) return;
    var fx = num(beat, "fx", 0.5), fy = num(beat, "fy", 0.5), s0 = num(beat, "s0", 1.08), rate = num(beat, "rate", 0.014);
    var vx = num(beat, "vx", -10), vy = num(beat, "vy", -4);
    var s1 = s0 + rate * dur;
    /* stay inside the picture: the overscan on each side at the end of the move bounds the drift (it only matters for very long beats) */
    var dx = clamp(vx * dur, -(s1 - 1) * W * (1 - fx), (s1 - 1) * W * fx), dy = clamp(vy * dur, -(s1 - 1) * H * (1 - fy), (s1 - 1) * H * fy);
    if (s1 <= 1) { dx = vx * dur; dy = vy * dur; }
    target.style.transformOrigin = (fx * 100) + "% " + (fy * 100) + "%";
    tl.fromTo(target, { scale: s0, x: 0, y: 0 }, { scale: s1, x: dx, y: dy, duration: dur, ease: "none", immediateRender: false }, t0);
  }

  function mapMotion(beat, t0, dur) {
    var routes = beat.querySelectorAll(".mm-route"), t = t0 + Math.min(0.5, dur * 0.1);
    var hl = beat.querySelectorAll(".mm-hl");
    if (hl.length) tl.fromTo(hl, { opacity: 0.25 }, { opacity: 1, duration: 0.6, ease: "power2.out", immediateRender: false }, t0 + 0.1);
    Array.prototype.forEach.call(routes, function (p, i) {
      var L = p.getTotalLength() || parseFloat(p.getAttribute("data-len")) || 1;
      p.style.strokeDasharray = L + " " + L; p.style.strokeDashoffset = L;
      tl.fromTo(p, { strokeDashoffset: L }, { strokeDashoffset: 0, duration: clamp(dur * 0.45, 1.2, 3.2), ease: "power2.inOut", immediateRender: false }, t + i * 0.25);
    });
    beat.querySelectorAll(".mm-dot, .mm-ring, .mm-label").forEach(function (el) { el.style.opacity = 0; });
    var dots = beat.querySelectorAll(".mm-dot"), rings = beat.querySelectorAll(".mm-ring"), labels = beat.querySelectorAll(".mm-label");
    Array.prototype.forEach.call(dots, function (d, i) {
      var at = t0 + 0.35 + i * (clamp(dur * 0.45, 1.2, 3.2) / Math.max(1, dots.length));
      tl.fromTo(d, { opacity: 0 }, { opacity: 1, duration: 0.3, ease: "power2.out", immediateRender: false }, at);
      tl.fromTo(labels[i], { opacity: 0 }, { opacity: 1, duration: 0.4, ease: "power2.out", immediateRender: false }, at + 0.15);
      tl.fromTo(rings[i], { opacity: 0.9, attr: { r: 12 } }, { opacity: 0, attr: { r: 40 }, duration: 0.9, ease: "power1.out", immediateRender: false }, at);
    });
  }

  function counter(beat, t0) {
    var n = beat.querySelector(".ledger .n");
    if (!n) return;
    var from = num(beat, "count-from", 0), to = num(beat, "count-to", 0), at = num(beat, "count-at", 0.6), end = num(beat, "count-end", at + 2);
    var dec = (String(beat.getAttribute("data-count-to")).split(".")[1] || "").length;
    var o = { v: from };
    n.textContent = fmt(from, dec);
    tl.fromTo(o, { v: from }, { v: to, duration: Math.max(0.4, end - at), ease: "power2.out", immediateRender: false,
      onUpdate: function () { n.textContent = fmt(dec ? o.v : Math.round(o.v), dec); } }, t0 + at);
  }

  function texts(beat, t0, dur) {
    var stamp = beat.querySelector(".stamp"), cap = beat.querySelector(".caption"), credit = beat.querySelector(".credit");
    if (stamp) tl.fromTo(splitChars(stamp), { opacity: 0 }, { opacity: 1, duration: 0.04, stagger: 0.035, ease: "none", immediateRender: false }, t0 + 0.15);
    if (cap) {
      tl.fromTo(splitWords(cap), { opacity: 0 }, { opacity: 1, duration: 0.4, stagger: 0.06, ease: "power2.out", immediateRender: false }, t0 + 0.35);
      tl.fromTo(cap, { y: 18 }, { y: 0, duration: 0.8, ease: "power3.out", immediateRender: false }, t0 + 0.35);
    }
    var led = beat.querySelector(".ledger");
    if (led) tl.fromTo(led, { opacity: 0 }, { opacity: 1, duration: 0.4, ease: "power2.out", immediateRender: false }, t0 + 0.3);
    if (credit) tl.fromTo(credit, { opacity: 0 }, { opacity: 1, duration: 0.6, ease: "power1.out", immediateRender: false }, t0 + 0.9);
  }

  Array.prototype.forEach.call(document.querySelectorAll(".beat"), function (beat, i, all) {
    var t0 = num(beat, "t0", 0), t1 = num(beat, "t1", 0), dur = t1 - t0;
    var dipIn = num(beat, "dip-in", 0), dipOut = num(beat, "dip-out", 0);
    camera(beat, t0, dur); texts(beat, t0, dur); counter(beat, t0);
    if (beat.querySelector(".mm-route, .mm-dot, .mm-hl")) mapMotion(beat, t0, dur);
    if (dipIn) tl.fromTo(beat, { autoAlpha: 0 }, { autoAlpha: 1, duration: dipIn, ease: "power1.out", immediateRender: false }, t0);   /* the first beat of an act has no .first class when it dips in */
    else if (i > 0) tl.set(beat, { autoAlpha: 1 }, t0);
    if (dipOut) tl.to(beat, { autoAlpha: 0, duration: dipOut, ease: "power1.in" }, t1 - dipOut);   /* also the last beat of an act: the next act fades in from the same dark */
    else if (i < all.length - 1) tl.set(beat, { autoAlpha: 0 }, t1);
  });

  Array.prototype.forEach.call(document.querySelectorAll(".sub"), function (sub) {
    tl.set(sub, { autoAlpha: 1 }, num(sub, "t0", 0));
    tl.set(sub, { autoAlpha: 0 }, num(sub, "t1", 0));
  });

  window.__timelines = window.__timelines || {};
  window.__timelines["main"] = tl;
})();
