// virtual-clock.js: a frame-exact clock for recording browser games.
//
// Inject this BEFORE any page script runs (capture.ts does it with CDP
// Page.addScriptToEvaluateOnNewDocument; in Playwright use page.addInitScript({ path })).
// After injection the page's time only moves when the recorder says so:
//
//   window.__vc.step(1000 / 30)   advance 33.33 ms: fire due timers, run every queued
//                                 requestAnimationFrame callback once, step CSS/Web animations
//   window.__vc.flush()           run timers due now and nothing else (no time passes)
//   window.__vc.now()             virtual ms since the page started
//   window.__vc.pending()         { raf, timers } waiting callbacks
//
// Replaced: requestAnimationFrame, cancelAnimationFrame, performance.now, Date.now,
// new Date(), Date(), setTimeout, setInterval, clearTimeout, clearInterval,
// requestIdleCallback, Math.random (seeded mulberry32), document.getAnimations() timing.
// Not replaced: AudioContext.currentTime, event.timeStamp, Web Workers, <video> playback,
// crypto.getRandomValues. A game that reads those is not frame-exact; see references/virtual-clock.md.
//
// Optional config, set before this script (capture.ts prepends it):
//   window.__VC_CONFIG = { seed: 1, epoch: Date.UTC(2026, 10, 9, 18) }
(() => {
  if (window.__vc) return;
  const cfg = window.__VC_CONFIG || {};

  // Seeded Math.random: same sequence on every run.
  let s = (cfg.seed ?? 1) >>> 0;
  Math.random = function random() {
    s = (s + 0x6d2b79f5) | 0;
    let t = Math.imul(s ^ (s >>> 15), 1 | s);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };

  let now = 0; // virtual milliseconds since the page started
  const epoch = cfg.epoch ?? Date.UTC(2026, 10, 9, 18, 0, 0);

  Object.defineProperty(performance, 'now', { value: () => now, configurable: true, writable: true });

  const RealDate = Date;
  const VDate = new Proxy(RealDate, {
    construct(T, args) { return args.length ? new T(...args) : new T(epoch + now); },
    apply() { return new RealDate(epoch + now).toString(); },
    get(T, p) { return p === 'now' ? () => epoch + now : Reflect.get(T, p); },
  });
  window.Date = VDate;

  // requestAnimationFrame: callbacks wait in a queue until step().
  let rafId = 0;
  let raf = new Map();
  window.requestAnimationFrame = (cb) => { const id = ++rafId; raf.set(id, cb); return id; };
  window.cancelAnimationFrame = (id) => { raf.delete(id); };

  // Timers fire in time order inside step().
  let timerId = 0;
  const timers = new Map();
  const add = (fn, ms, args, every) => {
    const id = ++timerId;
    const f = typeof fn === 'function' ? fn : new Function(String(fn));
    timers.set(id, { at: now + Math.max(0, Number(ms) || 0), fn: f, args, every });
    return id;
  };
  window.setTimeout = (fn, ms, ...args) => add(fn, ms, args, 0);
  window.setInterval = (fn, ms, ...args) => add(fn, ms, args, Math.max(1, Number(ms) || 0));
  window.clearTimeout = window.clearInterval = (id) => { timers.delete(id); };
  window.requestIdleCallback = (fn) => add(() => fn({ didTimeout: false, timeRemaining: () => 16 }), 1, [], 0);
  window.cancelIdleCallback = (id) => { timers.delete(id); };

  function runTimers(until) {
    for (let guard = 0; guard < 100000; guard++) {
      let next = null, nextId = 0;
      for (const [id, t] of timers) if (t.at <= until && (!next || t.at < next.at || (t.at === next.at && id < nextId))) { next = t; nextId = id; }
      if (!next) return;
      now = Math.max(now, next.at);
      if (next.every) next.at += next.every; else timers.delete(nextId);
      try { next.fn(...next.args); } catch (e) { console.error(e); }
    }
    console.error('virtual-clock: timer loop guard hit (a timer keeps rescheduling itself at the same time)');
  }

  // CSS animations, transitions and element.animate(): paused, then set from the virtual clock.
  const born = new WeakMap();
  function stepAnimations() {
    if (!document.getAnimations) return;
    for (const a of document.getAnimations()) {
      if (!born.has(a)) { born.set(a, now - (Number(a.currentTime) || 0)); try { a.pause(); } catch { /* finished */ } }
      try { a.currentTime = now - born.get(a); } catch { /* ignore */ }
    }
  }

  window.__vc = {
    now: () => now,
    pending: () => ({ raf: raf.size, timers: timers.size }),
    flush() { runTimers(now); stepAnimations(); return now; },
    step(ms) {
      const target = now + ms;
      runTimers(target);
      now = target;
      const q = raf; raf = new Map();
      for (const cb of q.values()) { try { cb(now); } catch (e) { console.error(e); } }
      stepAnimations();
      return now;
    },
  };
})();
