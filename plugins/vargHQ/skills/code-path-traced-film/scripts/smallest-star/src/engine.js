// WebGL2 pipeline: accumulate path-traced samples -> variance-guided a-trous denoise -> bloom -> tone map.
import { VS, ptFS, PREP_FS, ATROUS_FS, COMP_FS, DOWN_FS, UP_FS, FINAL_FS } from './shader.js';

export const QUALITY = {
  draft: { primary: 64, shadow: 24, bounce: 28, cells: 44, cellsBounce: 10, cellsShadow: 8, bounces: 1 },
  final: { primary: 90, shadow: 32, bounce: 40, cells: 60, cellsBounce: 14, cellsShadow: 12, bounces: 1 },
  ultra: { primary: 90, shadow: 32, bounce: 40, cells: 60, cellsBounce: 14, cellsShadow: 12, bounces: 2 },
};

export class Engine {
  constructor(canvas, w, h, quality = 'final', log = console.log) {
    this.w = w; this.h = h; this.log = log;
    canvas.width = w; canvas.height = h;
    const gl = canvas.getContext('webgl2', { antialias: false, alpha: false, depth: false, stencil: false, preserveDrawingBuffer: true, powerPreference: 'high-performance' });
    if (!gl) throw new Error('no webgl2');
    this.gl = gl;
    for (const e of ['EXT_color_buffer_float', 'EXT_float_blend', 'OES_texture_float_linear']) if (!gl.getExtension(e)) throw new Error('missing ' + e);
    const t0 = performance.now();
    this.pPT = this.program(VS, ptFS(QUALITY[quality] || QUALITY.final), 'pt');
    this.pPrep = this.program(VS, PREP_FS, 'prep');
    this.pAtrous = this.program(VS, ATROUS_FS, 'atrous');
    this.pComp = this.program(VS, COMP_FS, 'comp');
    this.pDown = this.program(VS, DOWN_FS, 'down');
    this.pUp = this.program(VS, UP_FS, 'up');
    this.pFinal = this.program(VS, FINAL_FS, 'final');
    this.compileMs = performance.now() - t0;
    const vb = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, vb);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
    this.vao = gl.createVertexArray(); gl.bindVertexArray(this.vao);
    gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);
    // targets
    this.acc = this.fbo(w, h, [gl.RGBA32F, gl.RGBA32F, gl.RGBA32F, gl.RGBA32F], gl.NEAREST);
    this.dnA = this.fbo(w, h, [gl.RGBA16F], gl.NEAREST);
    this.dnB = this.fbo(w, h, [gl.RGBA16F], gl.NEAREST);
    this.hdr = this.fbo(w, h, [gl.RGBA16F], gl.LINEAR);
    this.bloom = [];
    let bw = w, bh = h;
    for (let i = 0; i < 7; i++) { bw = Math.max(2, bw >> 1); bh = Math.max(2, bh >> 1); this.bloom.push(this.fbo(bw, bh, [gl.RGBA16F], gl.LINEAR)); }
    this.out = this.fbo(w, h, [gl.RGBA8], gl.NEAREST);
    this.pixels = new Uint8Array(w * h * 4);
  }

  program(vs, fs, name) {
    const gl = this.gl;
    const mk = (type, src) => {
      const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s);
      if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) {
        const info = gl.getShaderInfoLog(s) || '';
        const lines = src.split('\n');
        const ctx = [...info.matchAll(/ERROR: \d+:(\d+)/g)].slice(0, 6).map(m => `  L${m[1]}: ${lines[+m[1] - 1]}`).join('\n');
        throw new Error(`shader ${name} compile failed:\n${info}\n${ctx}`);
      }
      return s;
    };
    const p = gl.createProgram();
    gl.attachShader(p, mk(gl.VERTEX_SHADER, vs)); gl.attachShader(p, mk(gl.FRAGMENT_SHADER, fs));
    gl.bindAttribLocation(p, 0, 'aPos');
    gl.linkProgram(p);
    if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw new Error(`program ${name} link failed: ${gl.getProgramInfoLog(p)}`);
    return { p, loc: new Map(), name };
  }

  fbo(w, h, formats, filter) {
    const gl = this.gl;
    const f = gl.createFramebuffer(); gl.bindFramebuffer(gl.FRAMEBUFFER, f);
    const tex = formats.map((fmt, i) => {
      const t = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, t);
      gl.texStorage2D(gl.TEXTURE_2D, 1, fmt, w, h);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, filter); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, filter);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0 + i, gl.TEXTURE_2D, t, 0);
      return t;
    });
    gl.drawBuffers(formats.map((_, i) => gl.COLOR_ATTACHMENT0 + i));
    const st = gl.checkFramebufferStatus(gl.FRAMEBUFFER);
    if (st !== gl.FRAMEBUFFER_COMPLETE) throw new Error('fbo incomplete ' + st);
    return { f, tex, w, h };
  }

  use(prog) { this.gl.useProgram(prog.p); this.cur = prog; }
  loc(n) { const c = this.cur; if (!c.loc.has(n)) c.loc.set(n, this.gl.getUniformLocation(c.p, n)); return c.loc.get(n); }
  set(n, v) {
    const gl = this.gl; const l = this.loc(n); if (l === null) return;
    if (typeof v === 'number') gl.uniform1f(l, v);
    else if (v.length === 2) gl.uniform2fv(l, v);
    else if (v.length === 3) gl.uniform3fv(l, v);
    else if (v.length === 4) gl.uniform4fv(l, v);
    else if (v.length === 9) gl.uniformMatrix3fv(l, false, v);
  }
  seti(n, v) { const l = this.loc(n); if (l !== null) this.gl.uniform1i(l, v); }
  tex(n, unit, t) { const gl = this.gl; gl.activeTexture(gl.TEXTURE0 + unit); gl.bindTexture(gl.TEXTURE_2D, t); this.seti(n, unit); }
  target(t) { const gl = this.gl; gl.bindFramebuffer(gl.FRAMEBUFFER, t.f); gl.viewport(0, 0, t.w, t.h); this.set('uRes', [t.w, t.h]); }
  draw() { this.gl.drawArrays(this.gl.TRIANGLES, 0, 3); }
  sync() { const gl = this.gl; const b = new Float32Array(4); gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.FLOAT, b); }

  // uniformsAt(t) -> { pt: {...uniforms}, post: {...} }
  accumulate(uniformsAt, t, o) {
    const gl = this.gl; const spp = o.spp;
    gl.bindVertexArray(this.vao);
    gl.bindFramebuffer(gl.FRAMEBUFFER, this.acc.f); gl.viewport(0, 0, this.w, this.h);
    gl.disable(gl.BLEND); gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT);
    gl.enable(gl.BLEND); gl.blendFunc(gl.ONE, gl.ONE);
    this.use(this.pPT);
    const shutter = o.shutter ?? 0;
    let post = null;
    for (let s = 0; s < spp; s++) {
      const ts = t + ((s + 0.5) / spp - 0.5) * shutter;
      const U = uniformsAt(ts);
      post = U.post;
      for (const k in U.pt) this.set(k, U.pt[k]);
      this.set('uRes', [this.w, this.h]);
      this.set('uTime', ts); this.set('uSlice', shutter / spp);
      this.seti('uPass', s); this.seti('uSeed', o.seed | 0);
      const bands = o.bands ?? 4;
      gl.enable(gl.SCISSOR_TEST);
      for (let bnd = 0; bnd < bands; bnd++) {
        const y0 = Math.floor(this.h * bnd / bands), y1 = Math.floor(this.h * (bnd + 1) / bands);
        gl.scissor(0, y0, this.w, y1 - y0);
        this.draw();
        this.sync();
      }
      gl.disable(gl.SCISSOR_TEST);
    }
    gl.disable(gl.BLEND);
    return uniformsAt(t).post;
  }

  resolve(post, o) {
    const gl = this.gl; const N = o.spp; const mode = o.mode | 0;
    // denoise
    this.use(this.pPrep); this.target(this.dnA); this.tex('tRad', 0, this.acc.tex[0]); this.set('uN', N); this.draw();
    let src = this.dnA, dst = this.dnB;
    const iters = (mode === 4) ? 0 : (o.denoise ?? 4);
    if (iters > 0) {
      this.use(this.pAtrous);
      for (let i = 0; i < iters; i++) {
        this.target(dst);
        this.tex('tCol', 0, src.tex[0]); this.tex('tAlb', 1, this.acc.tex[2]); this.tex('tNrm', 2, this.acc.tex[3]);
        this.set('uN', N); this.seti('uStep', 1 << i);
        this.set('uSig', o.sig ?? [0.06, 48.0, 0.02, 3.0]);
        this.draw();
        const tmp = src; src = dst; dst = tmp;
      }
    }
    // composite
    this.use(this.pComp); this.target(this.hdr);
    this.tex('tCol', 0, src.tex[0]); this.tex('tEmi', 1, this.acc.tex[1]); this.tex('tAlb', 2, this.acc.tex[2]); this.tex('tNrm', 3, this.acc.tex[3]); this.tex('tRad', 4, this.acc.tex[0]);
    this.set('uN', N); this.seti('uMode', mode); this.draw();
    // bloom
    const raw = mode >= 1 && mode <= 3;
    if (!raw) {
      this.use(this.pDown);
      let prev = this.hdr;
      for (let i = 0; i < this.bloom.length; i++) {
        const b = this.bloom[i]; this.target(b);
        this.tex('tSrc', 0, prev.tex[0]); this.set('uTexel', [1 / prev.w, 1 / prev.h]); this.set('uThresh', i === 0 ? (post.bloomThresh ?? 0.35) : -1.0);
        this.draw(); prev = b;
      }
      this.use(this.pUp); gl.enable(gl.BLEND); gl.blendFunc(gl.ONE, gl.ONE);
      for (let i = this.bloom.length - 1; i > 0; i--) {
        const b = this.bloom[i - 1]; const s = this.bloom[i]; this.target(b);
        this.tex('tSrc', 0, s.tex[0]); this.set('uTexel', [1 / s.w, 1 / s.h]); this.set('uGain', post.bloomSpread ?? 0.85);
        this.draw();
      }
      gl.disable(gl.BLEND);
    }
    // final
    this.use(this.pFinal); this.target(this.out);
    this.tex('tHdr', 0, this.hdr.tex[0]); this.tex('tBloom', 1, this.bloom[0].tex[0]);
    this.set('uExposure', post.exposure ?? 3.5); this.set('uBloom', post.bloom ?? 0.5); this.set('uVig', post.vig ?? 0.35);
    this.set('uGrain', post.grain ?? 0.035); this.set('uSat', post.sat ?? 1.08); this.set('uContrast', post.contrast ?? 0.25);
    this.set('uLift', post.lift ?? [0.012, 0.014, 0.03]); this.set('uFadeOut', post.fade ?? 1.0);
    this.seti('uRaw', raw ? 1 : 0); this.seti('uFrame', o.seed | 0);
    this.draw();
    gl.readPixels(0, 0, this.w, this.h, gl.RGBA, gl.UNSIGNED_BYTE, this.pixels);
    return this.pixels;
  }

  render(uniformsAt, t, o) {
    const post = this.accumulate(uniformsAt, t, o);
    return this.resolve(post, o);
  }

  // show the last resolved frame on the canvas (interactive page)
  present() {
    const gl = this.gl;
    gl.bindFramebuffer(gl.READ_FRAMEBUFFER, this.out.f); gl.bindFramebuffer(gl.DRAW_FRAMEBUFFER, null);
    gl.blitFramebuffer(0, 0, this.w, this.h, 0, this.h, this.w, 0, gl.COLOR_BUFFER_BIT, gl.NEAREST);
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
  }
}
