/*
 * clock.js: one virtual clock for a page that is being rendered frame by frame (record-fixed.mjs).
 * Injected ahead of the page's own scripts (puppeteer evaluateOnNewDocument), into every frame.
 *
 * A film at 30 frames a second needs the page to be exactly 1/30 s older in each frame, however
 * long the frame took to draw and to copy. So time in the page stops being the wall's: it moves
 * only when the recorder calls window.__homieClock.step(ms), and then everything that tells the
 * page the time agrees:
 *
 *   performance.now()                 the virtual time, in ms, from 0 when the document began
 *   Date.now(), new Date()            the wall time the document began at, plus the virtual time
 *   requestAnimationFrame             called once a step, with the virtual time
 *   setTimeout / setInterval          fired in order, each at its own virtual time, inside the step
 *   CSS animations and transitions,   paused and set to their place by the virtual time every step
 *   element.animate() (Web Animations)  (document.getAnimations()), finished when they reach their end
 *
 * A countdown driven by setInterval, a callout that fades with a CSS animation and a game loop on
 * requestAnimationFrame therefore stay in step with one another: with only some of them virtual,
 * a one-second callout is over between two frames and never appears in the film.
 *
 * NOT on this clock, because the page cannot reach them or they are not time the page reads:
 *   - AudioContext.currentTime and anything scheduled on it (the sound is rebuilt from a log)
 *   - <video> and <audio> elements, which play at their own rate
 *   - Web Workers and worklets (their timers and performance.now are their own)
 *   - event.timeStamp, document.timeline.currentTime, performance.timeOrigin
 *   - the network: a server keeps real time, so a page fed by one sees it run fast or slow
 *   - an animation the page itself paused before the clock first saw it is left alone
 *
 * Nothing here draws, and nothing changes what a callback does: only when it is called.
 */
(function () {
  'use strict';
  if (window.__homieClock) return;
  const real = {
    raf: window.requestAnimationFrame.bind(window),
    setTimeout: window.setTimeout.bind(window),
    clearTimeout: window.clearTimeout.bind(window),
    Date: window.Date,
  };
  const epoch = real.Date.now();
  let now = 0; // virtual ms since this document began
  let seq = 1;
  const timers = new Map(); // id -> { at, fn, args, every }
  let rafs = new Map(); // id -> fn
  const anims = new WeakMap(); // Animation -> { t0, ours }
  const errors = [];
  const guard = (fn, args) => { try { fn(...args); } catch (e) { if (errors.length < 20) errors.push(String(e && e.message || e)); real.setTimeout(() => { throw e; }, 0); } };

  /* ---- the clocks the page reads */
  try { Object.defineProperty(performance, 'now', { configurable: true, value: () => now }); } catch (e) { /* frozen */ }
  // A function, not a class: Date() without `new` is legal and returns a string.
  function VDate(...a) {
    if (!new.target) return new real.Date(epoch + now).toString();
    return Reflect.construct(real.Date, a.length ? a : [epoch + now], new.target);
  }
  VDate.prototype = real.Date.prototype;
  VDate.now = () => epoch + Math.floor(now);
  VDate.parse = real.Date.parse; VDate.UTC = real.Date.UTC;
  window.Date = VDate;

  /* ---- timers */
  const addTimer = (fn, ms, args, every) => {
    const id = seq++;
    const wait = Math.max(0, Number(ms) || 0);
    timers.set(id, { at: now + wait, fn: typeof fn === 'function' ? fn : () => (0, eval)(String(fn)), args, every: every ? Math.max(1, wait) : 0 });
    return id;
  };
  window.setTimeout = (fn, ms, ...args) => addTimer(fn, ms, args, false);
  window.setInterval = (fn, ms, ...args) => addTimer(fn, ms, args, true);
  window.clearTimeout = window.clearInterval = (id) => { timers.delete(id); };
  window.requestAnimationFrame = (fn) => { const id = seq++; rafs.set(id, fn); return id; };
  window.cancelAnimationFrame = (id) => { rafs.delete(id); };

  /** Run every timer due by `to`, each at its own time, earliest first (a timer set by a timer runs in the same step when it is due). */
  function runTimers(to) {
    for (let guardCount = 0; guardCount < 20000; guardCount++) {
      let next = null; let nextId = 0;
      for (const [id, t] of timers) if (t.at <= to && (next === null || t.at < next.at || (t.at === next.at && id < nextId))) { next = t; nextId = id; }
      if (!next) break;
      if (next.at > now) now = next.at;
      if (next.every) next.at += next.every; else timers.delete(nextId);
      guard(next.fn, next.args);
    }
    now = to;
  }

  /** Every animation in the document, at its place by the virtual clock. */
  function runAnimations() {
    let list = [];
    try { list = document.getAnimations(); } catch (e) { return 0; }
    for (const a of list) {
      let s = anims.get(a);
      if (!s) {
        // First sight: one the page paused itself stays the page's; a running one becomes ours from where it is.
        s = { ours: a.playState !== 'paused', t0: now - (Number(a.currentTime) || 0) / (a.playbackRate || 1) };
        anims.set(a, s);
        if (s.ours) { try { a.pause(); } catch (e) { s.ours = false; } }
      }
      if (!s.ours) continue;
      const at = (now - s.t0) * (a.playbackRate || 1);
      let end = Infinity;
      try { end = a.effect ? a.effect.getComputedTiming().endTime : Infinity; } catch (e) { /* no effect */ }
      try {
        if (Number(end) <= at) { a.finish(); anims.delete(a); } else a.currentTime = at;
      } catch (e) { /* an animation that cannot be sought is left where it is */ }
    }
    return list.length;
  }

  /**
   * One frame: the clock moves on by `ms`, the timers due in it fire, then the frame callbacks, then
   * the animations are placed. All of it inside a real animation frame of the browser, and the promise
   * resolves a real frame later, so what was drawn has been presented when the recorder copies it.
   */
  function step(ms) {
    return new Promise((done) => {
      let ran = false;
      const run = () => {
        if (ran) return; ran = true;
        const to = now + Math.max(0, Number(ms) || 0);
        runTimers(to);
        const due = rafs; rafs = new Map();
        for (const fn of due.values()) guard(fn, [now]);
        const n = runAnimations();
        let settled = false;
        const finish = () => { if (settled) return; settled = true; done({ now, timers: timers.size, frames: due.size, animations: n, errors: errors.splice(0) }); };
        real.raf(() => finish());
        real.setTimeout(finish, 250); // a frame the browser is not painting (hidden, off screen) has no animation frames
      };
      real.raf(run);
      real.setTimeout(run, 250);
    });
  }

  window.__homieClock = { step, get now() { return now; }, epoch, virtual: true };
})();
