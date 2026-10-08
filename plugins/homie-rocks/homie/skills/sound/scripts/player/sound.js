/*
 * sound.js: a game's sound effects and music, from the files the Homie plugin's sound skill made
 * (sound.json beside them lists what exists). Plain JavaScript, no dependencies.
 *
 *   import { createSound } from './sound.js';            // bundle games: from src/; static games: from sound/
 *   const sound = createSound({ base: 'sound/' });        // where sound.json and the files are served, relative to the page
 *   sound.play('jump');                                   // a random variant, a little pitch jitter, never more than 4 at once
 *   sound.play('coin', { pitch: combo, volume: 0.8, pan: -0.3 });
 *   sound.music('theme');                                 // the theme's first loop, from the first touch on
 *   sound.section('chase');                               // the next loop, starting exactly on the next bar line
 *   sound.duck(0.4, 0.5);                                 // music down to 40% for half a second (a big hit, a line of speech)
 *   sound.volume({ sfx: 1, music: 0.6 }); sound.mute(true);
 *
 * Sound starts on the first touch, click or key, with no "tap for sound" screen: browsers keep audio
 * suspended until a person has touched the page, so the first gesture resumes it (a held stick counts
 * when the finger lifts). A sound asked for before that is dropped, not queued: a late hit is worse than none.
 * window.__homieSound holds counters for a playtest (what played, when); it never controls anything.
 *
 * THE CAPTURE LOG (off unless a recorder asks). A recorder that renders the page frame by frame cannot
 * record the speaker, so it asks for a log instead: before the page's scripts run it sets
 *
 *   window.__homieSoundCapture = { events: [] };
 *
 * and from then on every sound this player schedules is pushed onto `events` as it is scheduled, stamped
 * with performance.now() (`t`, ms), enough to mix the same sound again offline from the same files:
 *
 *   { t, type: 'start', id, bus: 'sfx' | 'music', name, url, gain, rate, pan, loop, delay, fadeIn, bar? }
 *   { t, type: 'stop', id, delay, fade, curve: 'cut' | 'linear' | 'target' }
 *   { t, type: 'duck', to, seconds }                 music down to `to`, back after `seconds`
 *   { t, type: 'levels', master, sfx, music, muted }
 *   { t, type: 'drop', name, why }                   asked for and not played: 'locked', 'missing', 'loading', 'voices'
 *
 * `delay` is seconds after `t`; `url` is absolute; `rate` is the playback rate after pitch and jitter (the
 * random choices are in the log, so the mix repeats them). With the log on, bar lines are counted on the page's
 * clock (performance.now) instead of the audio clock, so a recorder's virtual clock moves them too.
 * A game with its own audio code can push the same events itself; the video skill's `trailer` reads them.
 * Without that global nothing is logged and nothing here costs anything.
 */
export function createSound({ base = 'sound/', manifest = 'sound.json', maxPerName = 4, maxVoices = 24 } = {}) {
  const AC = window.AudioContext || window.webkitAudioContext;
  const ctx = AC ? new AC({ latencyHint: 'interactive' }) : null;
  const url = (f) => new URL(f, new URL(base, document.baseURI)).toString();
  const buses = {};
  const buffers = new Map();
  const live = new Map();
  const stats = { unlocked: false, unlockedAt: null, plays: [], missing: [], errors: [], music: null };
  let meta = { sfx: {}, music: {} };
  let muted = false;
  const levels = { master: 1, sfx: 1, music: 0.7 };
  let track = null;
  // The capture log: only when a recorder put the global there before this ran (see the head of this file).
  let cap = null;
  try { const c = window.__homieSoundCapture; if (c && Array.isArray(c.events)) cap = c; } catch (e) { /* not ours to read */ }
  let capId = 0;
  const logEv = (e) => { if (cap) { e.t = performance.now(); cap.events.push(e); } return e; };
  const fileOf = new Map(); // a variant's key -> the file that decoded (what the log names)

  if (ctx) {
    buses.master = ctx.createGain();
    // A gentle safety limiter: many hits at once must not clip.
    const comp = ctx.createDynamicsCompressor();
    comp.threshold.value = -6; comp.knee.value = 6; comp.ratio.value = 8; comp.attack.value = 0.003; comp.release.value = 0.15;
    buses.master.connect(comp).connect(ctx.destination);
    buses.sfx = ctx.createGain(); buses.sfx.connect(buses.master);
    buses.music = ctx.createGain(); buses.music.connect(buses.master);
    buses.duck = ctx.createGain(); buses.duck.connect(buses.music);
    applyLevels();
    try { if (navigator.audioSession) navigator.audioSession.type = 'playback'; } catch (e) { /* not iOS */ }
    const unlock = () => {
      if (ctx.state !== 'running') ctx.resume().catch(() => {});
      try { const b = ctx.createBuffer(1, 1, 22050); const s = ctx.createBufferSource(); s.buffer = b; s.connect(ctx.destination); s.start(0); } catch (e) { /* closed */ }
      if (!stats.unlocked && ctx.state === 'running') { stats.unlocked = true; stats.unlockedAt = performance.now(); }
      if (track && !track.started && ctx.state === 'running') startTrack();
    };
    for (const ev of ['pointerdown', 'pointerup', 'touchstart', 'touchend', 'keydown', 'click']) window.addEventListener(ev, unlock, { capture: true, passive: true });
    ctx.addEventListener('statechange', () => { if (ctx.state === 'running') { stats.unlocked = true; stats.unlockedAt = stats.unlockedAt || performance.now(); if (track && !track.started) startTrack(); } });
  }

  const ready = fetch(url(manifest)).then((r) => { if (!r.ok) throw new Error(`${manifest}: HTTP ${r.status}`); return r.json(); }).then((m) => {
    meta = { sfx: m.sfx || {}, music: m.music || {} };
    const variants = Object.values(meta.sfx).flat();
    const loops = Object.values(meta.music).flatMap((t) => Object.values(t.loops || {}));
    return Promise.all([...variants, ...loops].map(loadFirst));
  }).catch((e) => { stats.errors.push(String(e && e.message || e)); });

  function load(file) {
    if (!ctx || buffers.has(file)) return buffers.get(file);
    const p = fetch(url(file)).then((r) => { if (!r.ok) throw new Error(`${file}: HTTP ${r.status}`); return r.arrayBuffer(); })
      .then((b) => new Promise((ok, no) => ctx.decodeAudioData(b, ok, no)))
      .then((buf) => { buffers.set(file, buf); return buf; })
      .catch((e) => { stats.errors.push(String(e && e.message || e)); buffers.delete(file); return null; });
    buffers.set(file, p);
    return p;
  }

  // A list's own key, never a file's name: a list of ONE file ("jump.wav", or ["jump.wav"]) used to be kept under
  // that file's name, so loading the file found the list's own unfinished promise and waited on itself for ever
  // (`ready` never resolved, and music asked for before it never started).
  const keyOf = (list) => `=${Array.isArray(list) ? list.join('|') : list}`;
  /** A file listed as [ogg, wav]: the first this browser decodes wins (older Safari cannot decode Ogg). */
  function loadFirst(list) {
    const files = Array.isArray(list) ? list : [list];
    const key = keyOf(list);
    if (buffers.has(key)) return buffers.get(key);
    const p = files.reduce((prev, f) => prev.then((buf) => buf || load(f).then((b) => (b instanceof AudioBuffer ? b : null))), Promise.resolve(null))
      .then((buf) => { if (buf) { buffers.set(key, buf); fileOf.set(key, files.find((f) => buffers.get(f) === buf) ?? files[0]); } else buffers.delete(key); return buf; });
    buffers.set(key, p);
    return p;
  }
  const loopBuffer = (list) => buffers.get(keyOf(list));

  function applyLevels() {
    if (!ctx) return;
    const t = ctx.currentTime;
    buses.master.gain.setTargetAtTime(muted ? 0 : levels.master, t, 0.02);
    buses.sfx.gain.setTargetAtTime(levels.sfx, t, 0.02);
    buses.music.gain.setTargetAtTime(levels.music, t, 0.05);
    logEv({ type: 'levels', master: levels.master, sfx: levels.sfx, music: levels.music, muted });
  }

  function play(name, { volume = 1, pitch = 0, pan = 0, jitter = 0.35 } = {}) {
    stats.plays.push({ name, t: Math.round(performance.now()) });
    if (stats.plays.length > 500) stats.plays.splice(0, 250);
    if (!ctx || ctx.state !== 'running') { logEv({ type: 'drop', name, why: 'locked' }); return null; }
    const variants = meta.sfx[name];
    if (!variants || !variants.length) { if (!stats.missing.includes(name)) stats.missing.push(name); logEv({ type: 'drop', name, why: 'missing' }); return null; }
    const variant = variants[Math.floor(Math.random() * variants.length)];
    const buf = loopBuffer(variant);
    if (!(buf instanceof AudioBuffer)) { logEv({ type: 'drop', name, why: 'loading' }); return null; }
    const mine = live.get(name) || [];
    while (mine.length >= maxPerName) { const old = mine.shift(); try { old.stop(); } catch (e) { /* ended */ } logEv({ type: 'stop', id: old.capId, delay: 0, fade: 0, curve: 'cut' }); }
    let total = 0; for (const v of live.values()) total += v.length;
    if (total >= maxVoices) { logEv({ type: 'drop', name, why: 'voices' }); return null; }
    const src = ctx.createBufferSource();
    src.buffer = buf;
    src.playbackRate.value = 2 ** ((pitch + (Math.random() * 2 - 1) * jitter) / 12);
    if (cap) { src.capId = ++capId; logEv({ type: 'start', id: src.capId, bus: 'sfx', name, url: url(fileOf.get(keyOf(variant)) ?? (Array.isArray(variant) ? variant[0] : variant)), gain: volume, rate: src.playbackRate.value, pan: Math.max(-1, Math.min(1, pan || 0)), loop: false, delay: 0, fadeIn: 0 }); }
    const g = ctx.createGain(); g.gain.value = volume;
    let node = src.connect(g);
    if (pan && ctx.createStereoPanner) { const p = ctx.createStereoPanner(); p.pan.value = Math.max(-1, Math.min(1, pan)); node = node.connect(p); }
    node.connect(buses.sfx);
    src.onended = () => { const i = mine.indexOf(src); if (i >= 0) mine.splice(i, 1); };
    mine.push(src); live.set(name, mine);
    src.start();
    return src;
  }

  function startTrack() {
    if (!track || !ctx || ctx.state !== 'running') return;
    const buf = loopBuffer(track.loops[track.section]);
    if (!(buf instanceof AudioBuffer)) { ready.then(() => { if (track && !track.started) startTrack(); }); return; }
    track.started = true;
    track.t0 = ctx.currentTime + 0.05;
    track.c0 = performance.now() / 1000 + 0.05; // the same moment on the page's clock, for the capture log's bar lines
    track.node = loopNode(buf, track.t0, track.fade, track.section);
    stats.music = { name: track.name, section: track.section, since: Math.round(performance.now()) };
  }

  function loopNode(buf, at, fade, sectionName) {
    const src = ctx.createBufferSource(); src.buffer = buf; src.loop = true;
    if (cap) {
      const list = track.loops[sectionName];
      src.capId = ++capId;
      logEv({ type: 'start', id: src.capId, bus: 'music', name: `${track.name}/${sectionName}`, url: url(fileOf.get(keyOf(list)) ?? (Array.isArray(list) ? list[0] : list)), gain: 1, rate: 1, pan: 0, loop: true, delay: Math.max(0, at - ctx.currentTime), fadeIn: Math.max(0.005, fade), bar: track.bar });
    }
    const g = ctx.createGain(); g.gain.setValueAtTime(0, at); g.gain.linearRampToValueAtTime(1, at + Math.max(0.005, fade));
    src.connect(g).connect(buses.duck);
    src.start(at);
    return { src, g };
  }

  let loaded = false;
  ready.then(() => { loaded = true; });
  function music(name, opts = {}) {
    // Called before sound.json has arrived (the usual case: at the top of the game): start it once it has.
    if (!loaded) { ready.then(() => music(name, opts)); return; }
    const { section = null, fade = 0.4 } = opts;
    const t = meta.music[name];
    if (!t) { stats.errors.push(`no music "${name}" in ${manifest}`); return; }
    stopMusic({ fade: 0.2 });
    const first = section || Object.keys(t.loops || {})[0];
    track = { name, loops: t.loops, bar: t.barSeconds, section: first, started: false, fade };
    startTrack();
  }

  /** Switch loops on the next bar line (every loop shares the tempo, so bar lines line up). */
  function section(name, { fade = 0.03 } = {}) {
    if (!track || !track.loops[name] || name === track.section) return;
    track.section = name;
    if (!track.started) return;
    const buf = loopBuffer(track.loops[name]);
    if (!(buf instanceof AudioBuffer)) return;
    const now = ctx.currentTime;
    let at = track.t0 + Math.ceil((now + 0.02 - track.t0) / track.bar) * track.bar;
    if (cap) {
      // With the capture log on, the next bar line is counted on the page's clock: a recorder's virtual clock is the
      // one the film is on, and the audio clock runs at the wall's speed beside it.
      const cnow = performance.now() / 1000;
      const wait = track.c0 + Math.ceil((cnow + 0.02 - track.c0) / track.bar) * track.bar - cnow;
      at = now + wait; track.c0 = cnow + wait;
    }
    const old = track.node;
    old.g.gain.setValueAtTime(1, at - fade); old.g.gain.linearRampToValueAtTime(0, at);
    try { old.src.stop(at + 0.05); } catch (e) { /* */ }
    logEv({ type: 'stop', id: old.src.capId, delay: Math.max(0, at - fade - now), fade, curve: 'linear' });
    track.node = loopNode(buf, at - fade, fade, name);
    track.t0 = at;
    stats.music = { name: track.name, section: name, since: Math.round(performance.now()) };
  }

  function stopMusic({ fade = 0.5 } = {}) {
    if (!track) return;
    if (track.node && ctx) { const t = ctx.currentTime; track.node.g.gain.setTargetAtTime(0, t, fade / 3); try { track.node.src.stop(t + fade + 0.1); } catch (e) { /* */ } logEv({ type: 'stop', id: track.node.src.capId, delay: 0, fade, curve: 'target' }); }
    track = null; stats.music = null;
  }

  function duck(to = 0.4, seconds = 0.4) {
    if (!ctx) return;
    const t = ctx.currentTime; const g = buses.duck.gain;
    g.cancelScheduledValues(t); g.setTargetAtTime(to, t, 0.015); g.setTargetAtTime(1, t + seconds, 0.12);
    logEv({ type: 'duck', to, seconds });
  }

  const api = {
    ready, play, music, section, stopMusic, duck,
    volume(v) { Object.assign(levels, v || {}); applyLevels(); },
    mute(on = true) { muted = !!on; applyLevels(); },
    get context() { return ctx; },
    state: () => ({ unlocked: stats.unlocked, running: ctx ? ctx.state === 'running' : false, loaded: new Set([...buffers.values()].filter((b) => b instanceof AudioBuffer)).size, music: stats.music, missing: stats.missing.slice(), errors: stats.errors.slice(0, 10) }),
  };
  try { window.__homieSound = { get stats() { return { ...api.state(), plays: stats.plays.slice(-100), unlockedAt: stats.unlockedAt }; } }; } catch (e) { /* frozen global */ }
  return api;
}
