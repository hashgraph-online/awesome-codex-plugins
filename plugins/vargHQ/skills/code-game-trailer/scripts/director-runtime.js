// director-runtime.js: the in-page half of capture.ts. Injected right after virtual-clock.js,
// before page scripts. capture.ts calls, per shot:
//
//   __trailer.begin(shot)   install the shot's trailer camera, hidden selectors, overlay, letterbox
//   __trailer.tick(lt, ms)  set the shot clock to lt seconds, advance the page by ms (virtual), and
//                           return the game's events from that frame (window.__game.events, if any)
//   __trailer.text()        the visible text on the page (for the HUD / IP / caption audit)
//   __trailer.end()         remove everything begin() added
//
// Trailer camera: the game's own camera is overridden only inside renderer.render(scene, gameCamera)
// and restored right after, so gameplay code never sees the change. Needs the page to expose
// window.__game = { renderer, camera } (names configurable in the director's "hooks").
(() => {
  if (window.__trailer) return;
  const EASE = {
    linear: (u) => u,
    inOutSine: (u) => 0.5 - 0.5 * Math.cos(Math.PI * u),
    inOutCubic: (u) => (u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2),
    outCubic: (u) => 1 - Math.pow(1 - u, 3),
    inCubic: (u) => u * u * u,
    outQuart: (u) => 1 - Math.pow(1 - u, 4),
    outExpo: (u) => (u >= 1 ? 1 : 1 - Math.pow(2, -10 * u)),
  };
  const ev = (expr) => (typeof expr === 'string' ? (0, eval)(expr) : expr);
  const cr = (p0, p1, p2, p3, t) => { // uniform Catmull-Rom, per component
    const t2 = t * t, t3 = t2 * t;
    return p1.map((_, i) => 0.5 * (2 * p1[i] + (-p0[i] + p2[i]) * t + (2 * p0[i] - 5 * p1[i] + 4 * p2[i] - p3[i]) * t2 + (-p0[i] + 3 * p1[i] - 3 * p2[i] + p3[i]) * t3));
  };
  let shot = null, lt = 0, hook = null, added = [];

  function sample(cam, t) { // keys -> { pos, look, fov, roll } at shot time t (seconds)
    const k = cam.keys, n = k.length;
    if (n === 1) return k[0];
    const t0 = k[0].t ?? 0, t1 = k[n - 1].t ?? shot.duration;
    const u = Math.min(1, Math.max(0, (t - t0) / Math.max(1e-6, t1 - t0)));
    const te = t0 + (EASE[cam.ease || 'inOutSine'] || EASE.linear)(u) * (t1 - t0);
    let i = 0;
    while (i < n - 2 && te > (k[i + 1].t ?? t1)) i++;
    const a = k[i], b = k[i + 1], ta = a.t ?? t0, tb = b.t ?? t1;
    const s = Math.min(1, Math.max(0, (te - ta) / Math.max(1e-6, tb - ta)));
    const A = k[Math.max(0, i - 1)], B = k[Math.min(n - 1, i + 2)];
    const lerp = (x, y) => (x ?? 0) + ((y ?? 0) - (x ?? 0)) * s;
    return {
      pos: cr(A.pos, a.pos, b.pos, B.pos, s),
      look: a.look && b.look ? cr(A.look || a.look, a.look, b.look, B.look || b.look, s) : null,
      fov: a.fov != null || b.fov != null ? lerp(a.fov ?? b.fov, b.fov ?? a.fov) : null,
      roll: lerp(a.roll, b.roll),
    };
  }

  function installCamera(cfg, hooks) {
    const renderer = ev(hooks.renderer || 'window.__game && window.__game.renderer');
    const gameCam = ev(hooks.camera || 'window.__game && window.__game.camera');
    if (!renderer || !gameCam) throw new Error('trailer camera needs window.__game.renderer and .camera (or director "hooks")');
    const space = cfg.space && cfg.space !== 'world' ? ev(cfg.space) : null;
    const lookAtObj = cfg.lookAt ? ev(cfg.lookAt) : null;
    const V = gameCam.position.constructor, Qn = gameCam.quaternion.constructor;
    const save = { p: new V(), q: new Qn(), up: new V() };
    const orig = renderer.render;
    renderer.render = function (scene, cam, ...rest) {
      if (cam !== gameCam) return orig.call(this, scene, cam, ...rest);
      save.p.copy(cam.position); save.q.copy(cam.quaternion); save.up.copy(cam.up);
      const fov0 = cam.fov, k = sample(cfg, lt);
      const p = new V(...k.pos);
      if (space) { space.updateMatrixWorld(true); space.localToWorld(p); }
      let look;
      if (lookAtObj) { lookAtObj.updateMatrixWorld(true); look = new V().setFromMatrixPosition(lookAtObj.matrixWorld).add(new V(...(cfg.lookOffset || [0, 0, 0]))); }
      else { look = new V(...(k.look || [0, 0, -1])); if (space) space.localToWorld(look); }
      if (cfg.handheld) { // deterministic drift: sums of sines of the shot clock
        const h = cfg.handheld, t = lt;
        p.x += h * 0.06 * (Math.sin(t * 1.7) + 0.5 * Math.sin(t * 4.1 + 1));
        p.y += h * 0.05 * (Math.sin(t * 2.3 + 2) + 0.5 * Math.sin(t * 5.3));
        look.x += h * 0.12 * Math.sin(t * 1.1 + 3); look.y += h * 0.1 * Math.sin(t * 1.9 + 4);
      }
      cam.up.set(0, 1, 0); cam.position.copy(p); cam.lookAt(look);
      if (k.roll) cam.rotateZ((k.roll * Math.PI) / 180);
      if (k.fov != null) { cam.fov = k.fov; cam.updateProjectionMatrix(); }
      cam.updateMatrixWorld(true);
      try { return orig.call(this, scene, cam, ...rest); }
      finally {
        cam.position.copy(save.p); cam.quaternion.copy(save.q); cam.up.copy(save.up);
        if (cam.fov !== fov0) { cam.fov = fov0; cam.updateProjectionMatrix(); }
        cam.updateMatrixWorld(true);
      }
    };
    return () => { renderer.render = orig; };
  }

  function add(el) { document.documentElement.appendChild(el); added.push(el); return el; }

  window.__trailer = {
    begin(s, hooks = {}) {
      shot = s; lt = 0;
      if (s.camera && s.camera.keys && s.camera.keys.length) hook = installCamera(s.camera, hooks);
      if (s.hide && s.hide.length) {
        const st = document.createElement('style');
        st.textContent = `${s.hide.join(',')} { visibility: hidden !important; }`;
        add(st);
      }
      if (s.letterbox) { // e.g. 2.39 -> black bars top and bottom
        const st = document.createElement('style');
        st.textContent = `.__tr_bar{position:fixed;left:0;right:0;height:calc((100vh - 100vw / ${Number(s.letterbox)}) / 2);background:#000;z-index:2147483646;pointer-events:none}`;
        add(st);
        for (const side of ['top', 'bottom']) { const d = document.createElement('div'); d.className = '__tr_bar'; d.style[side] = '0'; add(d); }
      }
      if (s.overlay) {
        const o = typeof s.overlay === 'string' ? { html: s.overlay } : s.overlay;
        if (o.css) { const st = document.createElement('style'); st.textContent = o.css; add(st); }
        const d = document.createElement('div');
        d.id = '__trailer_overlay';
        d.style.cssText = 'position:fixed;inset:0;z-index:2147483647;pointer-events:none';
        d.innerHTML = o.html || '';
        add(d);
      }
      window.__vc.flush();
    },
    tick(t, ms) {
      lt = t;
      window.__vc.step(ms);
      const g = window.__game;
      const e = g && 'events' in g ? g.events : null;
      return Array.isArray(e) ? e.map((x) => x.type || String(x)) : [];
    },
    text() { return (document.body ? document.body.innerText : '') + '\n' + ((document.getElementById('__trailer_overlay') || {}).innerText || ''); },
    end() {
      if (hook) hook(); hook = null;
      for (const el of added) el.remove();
      added = []; shot = null;
    },
  };
})();
