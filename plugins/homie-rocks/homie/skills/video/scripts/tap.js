/*
 * tap.js: a copy of what a game's own WebAudio mix sends to the speaker, for a
 * trailer's soundtrack. Injected ahead of the game's modules (puppeteer
 * evaluateOnNewDocument) and active only in the studio's game frame (/<id>/__game/).
 *
 *   - every connect(node -> ctx.destination) of a live AudioContext goes through one
 *     unity-gain bus per context instead, so what the speaker gets is unchanged;
 *   - the bus also feeds an AudioWorklet that copies each render quantum, stamped with
 *     its context frame (currentFrame), as 16-bit stereo;
 *   - window.__homieTap.take() drains those copies (base64) with the context frame of
 *     each run's first sample; window.__homieTap.clock() samples (ctx.currentTime, page
 *     epoch ms) so the audio clock can be fitted to the picture's clock.
 *
 * Nothing here changes a gain, a node or a schedule of the game's own.
 */
(function () {
  'use strict';
  if (!/\/__game\//.test(location.pathname)) return;
  const AC = window.AudioContext;
  if (!AC || window.__homieTap) return;
  const origConnect = AudioNode.prototype.connect;
  const origDisconnect = AudioNode.prototype.disconnect;
  const WORKLET = `
class HomieTap extends AudioWorkletProcessor {
  constructor() { super(); this.on = false; this.cap = 128 * 24; this.buf = new Int16Array(this.cap * 2); this.n = 0; this.f0 = 0;
    this.port.onmessage = (e) => { if (e.data && 'on' in e.data) { this.flush(); this.on = !!e.data.on; } }; }
  flush() { if (this.n) { this.port.postMessage({ f: this.f0, n: this.n, d: this.buf.slice(0, this.n * 2) }); this.n = 0; } }
  process(inputs) {
    if (!this.on) return true;
    const inp = inputs[0] || []; const L = inp[0]; const R = inp[1] || inp[0];
    const n = L ? L.length : 128;
    if (this.n === 0) this.f0 = currentFrame;
    else if (this.f0 + this.n !== currentFrame) { this.flush(); this.f0 = currentFrame; }
    const b = this.buf; let o = this.n * 2;
    for (let i = 0; i < n; i += 1) {
      let l = L ? L[i] : 0; let r = R ? R[i] : 0;
      l = l > 1 ? 1 : l < -1 ? -1 : l; r = r > 1 ? 1 : r < -1 ? -1 : r;
      b[o++] = Math.round(l * 32767); b[o++] = Math.round(r * 32767);
    }
    this.n += n;
    if (this.n + 128 > this.cap) this.flush();
    return true;
  }
}
registerProcessor('homie-tap', HomieTap);`;
  const S = { ctxs: [], buses: new Map(), chunks: [], on: false, errors: [] };
  function busFor(ctx) {
    let b = S.buses.get(ctx);
    if (b) return b;
    const bus = ctx.createGain();
    origConnect.call(bus, ctx.destination);
    b = { bus, node: null, ready: false, idx: S.ctxs.length };
    S.buses.set(ctx, b);
    S.ctxs.push(ctx);
    const url = URL.createObjectURL(new Blob([WORKLET], { type: 'text/javascript' }));
    ctx.audioWorklet.addModule(url).then(() => {
      const node = new AudioWorkletNode(ctx, 'homie-tap', { numberOfInputs: 1, numberOfOutputs: 1, outputChannelCount: [2], channelCount: 2, channelCountMode: 'explicit', channelInterpretation: 'speakers' });
      origConnect.call(bus, node);
      const z = ctx.createGain(); z.gain.value = 0;
      origConnect.call(node, z); origConnect.call(z, ctx.destination);
      node.port.onmessage = (e) => { if (b.idx === 0) S.chunks.push(e.data); };
      b.node = node; b.ready = true;
      if (S.on && b.idx === 0) node.port.postMessage({ on: true });
    }).catch((e) => { S.errors.push(`addModule: ${String((e && e.message) || e)}`); });
    return b;
  }
  AudioNode.prototype.connect = function (target, ...rest) {
    try {
      if (target instanceof AudioDestinationNode && this.context instanceof AC) {
        const b = busFor(this.context);
        origConnect.call(this, b.bus, ...rest);
        return target;
      }
    } catch (e) { S.errors.push(`connect: ${String((e && e.message) || e)}`); }
    return origConnect.call(this, target, ...rest);
  };
  AudioNode.prototype.disconnect = function (...a) {
    if (a[0] instanceof AudioDestinationNode && S.buses.has(this.context)) a[0] = S.buses.get(this.context).bus;
    return origDisconnect.apply(this, a);
  };
  const b64 = (i16) => {
    const u8 = new Uint8Array(i16.buffer, i16.byteOffset, i16.byteLength); let s = '';
    for (let k = 0; k < u8.length; k += 0x8000) s += String.fromCharCode.apply(null, u8.subarray(k, k + 0x8000));
    return btoa(s);
  };
  window.__homieTap = {
    start() { S.on = true; const b = S.ctxs[0] && S.buses.get(S.ctxs[0]); if (b && b.ready) b.node.port.postMessage({ on: true }); return { ctxs: S.ctxs.length, ready: !!(b && b.ready), rate: S.ctxs[0] ? S.ctxs[0].sampleRate : null }; },
    stop() { S.on = false; const b = S.ctxs[0] && S.buses.get(S.ctxs[0]); if (b && b.ready) b.node.port.postMessage({ on: false }); },
    /** The copies since the last take, as runs of contiguous context frames. */
    take() {
      if (!S.chunks.length) return [];
      const cs = S.chunks.splice(0);
      const runs = []; let cur = null;
      for (const c of cs) {
        if (cur && c.f === cur.f + cur.n) { cur.parts.push(c.d); cur.n += c.n; }
        else { cur = { f: c.f, n: c.n, parts: [c.d] }; runs.push(cur); }
      }
      return runs.map((r) => { const a = new Int16Array(r.n * 2); let o = 0; for (const p of r.parts) { a.set(p, o); o += p.length; } return { f: r.f, frames: r.n, b64: b64(a) }; });
    },
    clock() {
      const c = S.ctxs[0];
      const wall = performance.timeOrigin + performance.now();
      if (!c) return { ctxs: 0, wall };
      let ot = null; try { const o = c.getOutputTimestamp(); ot = [o.contextTime, performance.timeOrigin + o.performanceTime]; } catch (e) { /* */ }
      return { ctxs: S.ctxs.length, now: c.currentTime, wall, ot, state: c.state, rate: c.sampleRate, ready: !!(S.buses.get(c) || {}).ready, errors: S.errors.slice(0, 5) };
    },
  };
}());
