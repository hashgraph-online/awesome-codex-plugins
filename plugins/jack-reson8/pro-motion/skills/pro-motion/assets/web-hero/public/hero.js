// tutti.pics 首屏：一面会流动的字墙（WebGL）+ 站在前面的人（抠图）+ 闪光一下换一张海报。
// 字墙是 2D canvas 画的字 → 上传成纹理 → 片元着色器做液态扭曲、手指推字、硬光颗粒。
(() => {
  const T = k => I18N[k] ?? k;
  const LOOKS = [
    { who: 'demo-3', ground: '#FF2E93', ink: '#FF4A00', glow: '#FFE3F3', warp: 0.6, tpl: 25 },
    { who: 'demo-3', ground: '#1E3BFF', ink: '#F4F1EA', glow: '#8AA0FF', warp: 0.75, stars: true, tpl: 12 },
    { who: 'demo-8', ground: '#0D0D0D', ink: '#FFFFFF', glow: '#8a8a8a', warp: 0.6, mono: true, tpl: 51 },
    { who: 'demo-8', ground: '#FF6A00', ink: '#6E0014', glow: '#FFC07A', warp: 1.2, me: 'line', tpl: 31 },
    { who: 'demo-1', ground: '#B8F03C', ink: '#1F3A00', glow: '#F4FFB0', warp: 1.1, tpl: 26 },
    { who: 'demo-1', ground: '#7A3CFF', ink: '#FFD23F', glow: '#C9A6FF', warp: 0.9, stars: true, tpl: 17 },
  ];
  // tpl = App 里 Library.codeIDs 的下标：25 mag-vogue · 12 punch-star-pink · 51 keep-bw · 31 doodle-white · 26 mag-red · 17 punch-sparkle-lilac
  // 参数位先用 0 档；等主会话导出各模板默认档位的码后替换
  LOOKS.forEach(L => L.code = ShortCode.encode(ShortCode.payload(L.tpl)));
  LOOKS.forEach((L, i) => L.words = I18N.walls[i]);
  const WHO = { 'demo-1': .47, 'demo-3': .54, 'demo-8': .48 };
  let mine = false, badCode = ''; // 用户放了自己的照片后，所有海报都换成 TA
  const note = document.getElementById('note');
  const say = (t, bad) => { note.textContent = t; note.classList.toggle('bad', !!bad); note.hidden = !t; };
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const cv = document.getElementById('wall'), me = document.getElementById('me');
  const flash = document.getElementById('flash'), codeval = document.getElementById('codeval'), hint = document.getElementById('hint');
  const gl = cv.getContext('webgl', { antialias: false, premultipliedAlpha: false, preserveDrawingBuffer: true });
  if (!gl) { document.body.classList.add('nogl'); return; }
  const DPR = Math.min(1.5, devicePixelRatio || 1);
  const INNER = 0.86; // 屏幕只用纹理中间 86%，扭曲时边缘不露底
  let W, H, TW, TH;

  const VS = `attribute vec2 a; varying vec2 v; void main(){ v = a * .5 + .5; gl_Position = vec4(a, 0., 1.); }`;
  const FS = `precision highp float;
  varying vec2 v; uniform sampler2D T; uniform vec2 R; uniform float t, warp, kick, inner; uniform vec3 M, G;
  float h(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
  float n(vec2 p){ vec2 i = floor(p), f = fract(p); f = f * f * (3. - 2. * f);
    return mix(mix(h(i), h(i + vec2(1, 0)), f.x), mix(h(i + vec2(0, 1)), h(i + vec2(1, 1)), f.x), f.y); }
  void main(){
    vec2 asp = vec2(R.x / R.y, 1.);
    vec2 p = (v - .5) * asp;
    float w = warp * (1. + kick * 2.2);
    // 鱼眼：中间鼓、四周压，像 Lapse 那面被手撑开的字
    p *= 1. - .34 * w * dot(p, p);
    // 液态流动：两层噪声位移 + 竖向波
    float s = t * .12;
    vec2 q = vec2(n(p * 1.7 + vec2(s, 1.3)), n(p * 1.7 + vec2(4.1, -s)));
    p += (q - .5) * .2 * w;
    p.x += sin(p.y * 5. + t * .9) * .025 * w;
    p.y += sin(p.x * 3. - t * .6) * .02 * w;
    // 手指：按住的地方字被撑大、带一点旋涡
    vec2 m = (M.xy - .5) * asp; vec2 d = p - m; float f = exp(-dot(d, d) * 9.) * M.z;
    p = m + d * (1. - .55 * f);
    float a = f * 1.4; p = m + mat2(cos(a), -sin(a), sin(a), cos(a)) * (p - m);
    vec2 u = p / asp * inner + .5;
    vec4 c = texture2D(T, u);
    vec3 col = mix(G, c.rgb, c.a);
    // 硬光颗粒（每帧换）
    float g = h(floor(v * R / 1.5) + fract(t * 7.) * 91.) - .5;
    col = col + g * .16 * (1. - abs(col - .5) * 1.2);
    gl_FragColor = vec4(col, 1.);
  }`;
  function sh(type, src) { const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s); if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) console.error(gl.getShaderInfoLog(s)); return s; }
  const prog = gl.createProgram();
  gl.attachShader(prog, sh(gl.VERTEX_SHADER, VS)); gl.attachShader(prog, sh(gl.FRAGMENT_SHADER, FS)); gl.linkProgram(prog); gl.useProgram(prog);
  gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer());
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
  const aLoc = gl.getAttribLocation(prog, 'a'); gl.enableVertexAttribArray(aLoc); gl.vertexAttribPointer(aLoc, 2, gl.FLOAT, false, 0, 0);
  const U = {}; for (const k of ['T', 'R', 't', 'warp', 'kick', 'inner', 'M', 'G']) U[k] = gl.getUniformLocation(prog, k);
  const tex = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, tex);
  for (const [k, v] of [[gl.TEXTURE_MIN_FILTER, gl.LINEAR], [gl.TEXTURE_MAG_FILTER, gl.LINEAR], [gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE], [gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE]]) gl.texParameteri(gl.TEXTURE_2D, k, v);
  gl.uniform1i(U.T, 0); gl.uniform1f(U.inner, INNER);

  const rgb = hex => [1, 3, 5].map(i => parseInt(hex.slice(i, i + 2), 16) / 255);
  function rand(seed) { let s = seed >>> 0; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); }
  function loadImg(src) { return new Promise((ok, bad) => { const i = new Image(); i.onload = () => ok(i); i.onerror = bad; i.src = src; }); }

  // 照片（给星孔和黑白墙用），按屏幕 cover 的方式摆进纹理坐标，和前面的人对齐
  const PH = {}; let photo, photoGray, mx = 0.54;
  function drawCover(x, img) {
    const s = Math.max(W / img.width, H / img.height), iw = img.width * s, ih = img.height * s;
    const ox = (W - iw) * mx, oy = (H - ih) / 2; // 背景照片铺满整屏，人另外缩小站在前面
    const k = TW / (W / INNER), offX = (TW - W * k) / 2, offY = (TH - H * k) / 2;
    x.drawImage(img, offX + ox * k, offY + oy * k, iw * k, ih * k);
  }
  function grayOf(img) {
    const c = document.createElement('canvas'); c.width = img.width; c.height = img.height;
    const x = c.getContext('2d'); x.drawImage(img, 0, 0);
    const d = x.getImageData(0, 0, c.width, c.height);
    for (let i = 0; i < d.data.length; i += 4) {
      let g = .3 * d.data[i] + .59 * d.data[i + 1] + .11 * d.data[i + 2];
      g = Math.max(0, Math.min(255, (g - 128) * 1.4 + 120));
      d.data[i] = d.data[i + 1] = d.data[i + 2] = g;
    }
    x.putImageData(d, 0, 0); return c;
  }
  function star(x, cx, cy, r, rot) {
    x.beginPath();
    for (let i = 0; i < 10; i++) { const rr = i % 2 ? r * .44 : r, a = rot + i * Math.PI / 5 - Math.PI / 2; x[i ? 'lineTo' : 'moveTo'](cx + Math.cos(a) * rr, cy + Math.sin(a) * rr); }
    x.closePath();
  }

  const wallCanvas = document.createElement('canvas');
  function buildWall(L) {
    const c = wallCanvas; c.width = TW; c.height = TH;
    const x = c.getContext('2d'); x.clearRect(0, 0, TW, TH);
    if (L.mono && photoGray) { drawCover(x, photoGray); x.fillStyle = 'rgba(13,13,13,.5)'; x.fillRect(0, 0, TW, TH); }
    // 一排排字，大小交替，铺满整面墙
    const rows = []; let y = 0, k = 0;
    x.font = '100px Brand';
    while (y < TH) {
      const word = L.words[k % L.words.length], w100 = x.measureText(word).width || 100;
      const size = Math.min(TW * .98 / w100 * 100, TW / 2.15, TH / 3.4);
      rows.push([word, size, y]); y += size * 1.02; k++;
    }
    const extra = (TH - y) / 2;
    x.textBaseline = 'top'; x.textAlign = 'center'; if ('letterSpacing' in x) x.letterSpacing = TW * .012 + 'px';
    for (const pass of ['glow', 'ink']) {
      for (const [word, size, yy] of rows) {
        x.font = `${size}px Brand`;
        if (pass === 'glow') { x.shadowColor = L.glow; x.shadowBlur = size * .45; x.fillStyle = L.glow; x.fillText(word, TW / 2, yy + extra - size * .05, TW * 1.02); x.shadowBlur = size * .18; }
        else { x.shadowBlur = 0; x.fillStyle = x.strokeStyle = L.ink; x.lineJoin = 'round'; x.lineWidth = size * .035; x.strokeText(word, TW / 2, yy + extra - size * .05, TW * 1.02); }
        x.fillText(word, TW / 2, yy + extra - size * .05, TW * 1.02);
      }
    }
    x.shadowBlur = 0;
    if (L.stars && photo) {
      const r = rand(L.code.charCodeAt(0) * 31);
      for (let i = 0; i < 16; i++) {
        const big = r() < .25, rad = TW * (big ? .11 + r() * .07 : .03 + r() * .05);
        x.save(); star(x, r() * TW, r() * TH, rad, r() * 1.3); x.clip(); drawCover(x, photo); x.restore();
      }
    }
    gl.bindTexture(gl.TEXTURE_2D, tex);
    gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, true);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, c);
  }

  function resize() {
    W = innerWidth; H = innerHeight;
    cv.width = Math.round(W * DPR); cv.height = Math.round(H * DPR);
    gl.viewport(0, 0, cv.width, cv.height); gl.uniform2f(U.R, cv.width, cv.height);
    const scale = Math.min(1.6, DPR) / INNER;
    TW = Math.round(W * scale); TH = Math.round(H * scale);
    if (cur) buildWall(cur);
  }

  // 手指：按住推字；轻点 = 闪光出片
  const ptr = { x: .5, y: .45, tx: .5, ty: .45, z: 0, tz: .35, down: 0, sx: 0, sy: 0 };
  let lastInteract = -1e9;
  addEventListener('pointerdown', e => {
    if (e.target.closest('.cta, header, #sheet, #code, .note')) return;
    ptr.down = performance.now(); ptr.sx = e.clientX; ptr.sy = e.clientY; ptr.tz = 1; setPtr(e); lastInteract = performance.now();
  });
  addEventListener('pointermove', e => { if (ptr.down) setPtr(e); else if (e.pointerType === 'mouse') { setPtr(e); ptr.tz = .6; } });
  addEventListener('pointerup', e => {
    if (!ptr.down) return;
    const tap = performance.now() - ptr.down < 280 && Math.hypot(e.clientX - ptr.sx, e.clientY - ptr.sy) < 10;
    ptr.down = 0; ptr.tz = .35; lastInteract = performance.now();
    if (tap) shoot(e.clientX / W, e.clientY / H);
  });
  function setPtr(e) { ptr.tx = e.clientX / W; ptr.ty = 1 - e.clientY / H; }

  let cur = null, idx = 0, kick = 0;
  function apply(L) {
    const who = mine ? 'mine' : L.who;
    ({ img: photo, gray: photoGray } = PH[who]); mx = WHO[who];
    const src = PH[who].src;
    if (me.getAttribute('src') !== src) me.src = src;
    me.style.setProperty('--cx', mx); me.style.setProperty('--ar', (PH[who].img.width / PH[who].img.height).toFixed(4));
    cur = L; buildWall(L);
    document.documentElement.style.setProperty('--ground', L.ground);
    document.querySelector('meta[name=theme-color]').content = L.ground;
    me.classList.toggle('line', L.me === 'line');
    codeval.textContent = badCode || L.code.slice(3);
    document.getElementById('code').classList.toggle('bad', !!badCode);
  }
  function shoot(fx = .5, fy = .38) {
    flash.style.setProperty('--fx', fx * 100 + '%'); flash.style.setProperty('--fy', fy * 100 + '%');
    flash.classList.remove('go'); void flash.offsetWidth; flash.classList.add('go');
    me.style.setProperty('--ms', 1.035); setTimeout(() => me.style.setProperty('--ms', 1), 140);
    kick = 1; idx = (idx + 1) % LOOKS.length;
    setTimeout(() => apply(LOOKS[idx]), 60);
    hint.style.opacity = 0; document.body.classList.remove('is-today');
    if (document.body.dataset.page === '404' && LOOKS[0].tpl === -1) { LOOKS.shift(); document.body.classList.remove('broken'); idx = 0; say(T('fixed')); setTimeout(() => say(''), 2400); setTimeout(() => apply(LOOKS[0]), 60); return; }
    if (navigator.vibrate) navigator.vibrate(12);
  }

  let t0 = performance.now(), lastAuto = performance.now();
  let running = true;
  document.addEventListener('visibilitychange', () => { running = !document.hidden; if (running) requestAnimationFrame(frame); });
  cv.addEventListener('webglcontextlost', e => { e.preventDefault(); running = false; });
  cv.addEventListener('webglcontextrestored', () => location.reload());
  function frame(now) {
    if (!running) return;
    const t = reduce ? 0 : (now - t0) / 1000;
    if (!ptr.down && !reduce) { // 没人碰时，一根看不见的手指慢慢在墙上游
      ptr.tx = .5 + Math.sin(t * .37) * .28; ptr.ty = .55 + Math.sin(t * .23 + 1) * .22;
    }
    ptr.x += (ptr.tx - ptr.x) * .12; ptr.y += (ptr.ty - ptr.y) * .12; ptr.z += (ptr.tz - ptr.z) * .1;
    kick *= .93;
    gl.uniform1f(U.t, t); gl.uniform1f(U.warp, cur.warp); gl.uniform1f(U.kick, kick);
    gl.uniform3f(U.M, ptr.x, ptr.y, reduce ? 0 : ptr.z); gl.uniform3f(U.G, ...rgb(cur.ground));
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    me.style.setProperty('--px', ((.5 - ptr.x) * 10).toFixed(2) + 'px');
    me.style.setProperty('--py', ((ptr.y - .5) * 6).toFixed(2) + 'px');
    if (!reduce && now - lastAuto > 3400 && now - lastInteract > 7000) { lastAuto = now; shoot(.5, .3); }
    requestAnimationFrame(frame);
  }

  addEventListener('resize', resize);
  Promise.all([document.fonts.load('100px Brand'), ...Object.keys(WHO).map(w => Promise.all([loadImg(`/assets/img/${w}.jpg`), loadImg(`/assets/img/${w}-cut.webp`)]))]).then(([, ...imgs]) => {
    Object.keys(WHO).forEach((w, i) => PH[w] = { img: imgs[i][0], gray: grayOf(imgs[i][0]), src: `/assets/img/${w}-cut.webp`, cut: imgs[i][1] });
    resize();
    const start = codePage();
    apply(LOOKS[start]); idx = start;
    requestAnimationFrame(frame);
  });
  // ── 配方码页 /c/XXXXXX：停在这个码对应的海报上；抄错一位给候选，不报 404 ──
  // ── 只印码海报 /p/XXXXXX：整面墙就是这串码，不写 App 名；点一下换底色 ──
  function posterPage() {
    const m = location.pathname.match(/\/p\/([^/]+)/);
    if (!m) return false;
    const p = ShortCode.decode(decodeURIComponent(m[1]));
    const code = p === null ? 'TT·' + ShortCode.body(m[1]).slice(0, 6) : ShortCode.encode(p), b = code.slice(3);
    const inks = [['#FF2E93', '#160F12', '#FF9BCB'], ['#1E3BFF', '#F4F1EA', '#8AA0FF'], ['#0D0D0D', '#FFFFFF', '#777'], ['#FF6A00', '#160F12', '#FFC07A'], ['#B8F03C', '#1F3A00', '#F4FFB0']];
    LOOKS.length = 0;
    inks.forEach(([ground, ink, glow]) => LOOKS.push({ who: 'demo-3', ground, ink, glow, words: [b, 'TT·' + b, b.slice(0, 3), b.slice(3)], warp: .8, code }));
    document.body.classList.add('is-poster');
    lastInteract = performance.now() + 1e9;
    document.getElementById('posterUrl').textContent = `tutti.pics/c/${b}`;
    return true;
  }

  // ── 404：先是一面灰的"坏了"，点一下闪光才出片（假故障）──
  function brokenPage() {
    if (document.body.dataset.page !== '404') return false;
    LOOKS.unshift({ who: 'demo-3', ground: '#BDBAB3', ink: '#8F8B83', glow: '#D6D3CC', words: I18N.broken, warp: .35, mono: true, tpl: -1, code: 'TT·404' });
    document.body.classList.add('broken');
    lastInteract = performance.now() + 1e9;
    hint.textContent = T('hint_fix');
    say(T('n404'));
    return true;
  }

  // ── 模板页 /t/<id>：停在这个模板；?og=N 给分享卡截图用（只留画面、logo 和码）──
  const SLUGS = { 25: 'cover-star', 12: 'star-punch', 51: 'only-me-color', 31: 'white-outline', 26: 'red-special', 17: 'mirrored-sparkles' };
  function templatePage() {
    const og = new URLSearchParams(location.search).get('og');
    const m = location.pathname.match(/\/t\/([a-z0-9-]+)/);
    const i = og !== null ? +og : m ? LOOKS.findIndex(L => SLUGS[L.tpl] === m[1]) : -1;
    if (i < 0) return -1;
    lastInteract = performance.now() + 1e9;
    if (og !== null) document.body.classList.add('is-og');
    return i;
  }

  function codePage() {
    if (posterPage() || brokenPage()) return 0;
    const ti = templatePage();
    if (ti >= 0) return ti;
    const m = location.pathname.match(/\/c\/([^/]+)/);
    if (!m) { // 首页：每天开场换一张（今日玩法）
      const day = Math.floor((Date.now() + 8 * 3600e3) / 86400e3);
      document.body.classList.add('is-today');
      return day % LOOKS.length;
    }
    const raw = decodeURIComponent(m[1]);
    document.body.classList.add('is-code');
    lastInteract = performance.now() + 1e9;
    const p = ShortCode.decode(raw);
    if (p === null) {
      const near = ShortCode.nearby(raw).slice(0, 4);
      badCode = ShortCode.body(raw).slice(0, 8) + ' ?';
      say(near.length ? T('code_typo') : T('code_bad'), true);
      near.forEach(c => note.insertAdjacentHTML('beforeend', ` <a href="/c/${c.slice(3)}">${c}</a>`));
      return 0;
    }
    const code = ShortCode.encode(p), body = code.slice(3);
    if (m[1] !== body) history.replaceState(null, '', '/c/' + body + location.search);
    const i = Math.max(0, LOOKS.findIndex(L => L.tpl === ShortCode.split(p).index));
    LOOKS[i] = { ...LOOKS[i], code };
    if (LOOKS[i].tpl !== ShortCode.split(p).index) say(T('code_other'));
    return i;
  }

  // ── 用我的照片：本地抠图 → 所有海报换成 TA ──
  const file = document.getElementById('file'), btnLabel = document.getElementById('btnLabel');
  document.querySelector('label[for=file]').addEventListener('pointerdown', () => import('/try.js').then(m => m.preload()), { once: true });
  file.addEventListener('change', async () => {
    const f = file.files[0]; file.value = '';
    if (!f) return;
    lastInteract = performance.now() + 1e9; badCode = ''; // 用户自己的海报出来后不再自动翻
    btnLabel.textContent = T('finding'); say(T('finding_note'));
    kick = 1;
    try {
      const { cutOut } = await import('/try.js');
      const r = await cutOut(f);
      if (r.coverage < .02) { btnLabel.textContent = T('cta_other'); say(T('no_person'), true); return; }
      const blob = await new Promise(ok => r.cut.toBlob(ok, 'image/webp', .9));
      PH.mine = { img: r.img, gray: grayOf(r.img), src: URL.createObjectURL(blob), cut: r.cut }; WHO.mine = r.cx;
      mine = true; idx = -1; shoot(.5, .35);
      btnLabel.textContent = T('cta_again'); say(''); document.body.classList.add('has-mine');
    } catch (e) {
      console.error(e); btnLabel.textContent = T('cta_retry'); say(T('seg_fail'), true);
    }
  });

  document.getElementById('code').addEventListener('click', async () => {
    const em = document.querySelector('#code em');
    try { await navigator.clipboard.writeText(`${cur.code} https://tutti.pics/c/${cur.code.slice(3)}`); em.textContent = T('code_copied'); }
    catch { em.textContent = T('code_hold'); }
    setTimeout(() => (em.textContent = T('code_copy')), 2000);
  });

  // ── 存这张：把当前海报画成一张图（作品本身就是分享卡，角上带配方码）──
  async function poster() {
    const s = 2, out = document.createElement('canvas'); out.width = W * s; out.height = H * s;
    const x = out.getContext('2d');
    x.drawImage(cv, 0, 0, out.width, out.height);
    const r = me.getBoundingClientRect(), who = mine ? 'mine' : cur.who, cut = PH[who].cut, showMe = getComputedStyle(me).display !== 'none';
    if (showMe && cur.me === 'line') { // 白线：白色剪影往 8 个方向各偏 3px
      const sil = document.createElement('canvas'); sil.width = r.width * s; sil.height = r.height * s;
      const sx = sil.getContext('2d'); sx.drawImage(cut, 0, 0, sil.width, sil.height);
      sx.globalCompositeOperation = 'source-in'; sx.fillStyle = '#fff'; sx.fillRect(0, 0, sil.width, sil.height);
      for (let k = 0; k < 8; k++) { const a = k * Math.PI / 4; x.drawImage(sil, r.left * s + Math.cos(a) * 3 * s, r.top * s + Math.sin(a) * 3 * s); }
    }
    if (showMe) x.drawImage(cut, r.left * s, r.top * s, r.width * s, r.height * s);
    x.save(); x.translate(18 * s, (H - 34) * s); x.rotate(-.04);
    x.font = `600 ${13 * s}px ui-monospace, Menlo, monospace`;
    const label = `${cur.code}  tutti.pics`, tw = x.measureText(label).width;
    x.fillStyle = '#fff'; x.fillRect(-8 * s, -16 * s, tw + 16 * s, 24 * s);
    x.fillStyle = '#160F12'; x.fillText(label, 0, 0); x.restore();
    return new Promise(ok => out.toBlob(ok, 'image/jpeg', .92));
  }
  document.getElementById('save').addEventListener('click', async () => {
    const blob = await poster(), name = `tutti-${cur.code.slice(3)}.jpg`;
    const f = new File([blob], name, { type: 'image/jpeg' });
    if (navigator.canShare && navigator.canShare({ files: [f] })) {
      try { await navigator.share({ files: [f], text: T('save_text').replace('{code}', cur.code).replace('{url}', `https://tutti.pics/c/${cur.code.slice(3)}`) }); return; } catch (e) { if (e.name === 'AbortError') return; }
    }
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = name; a.click();
  });

  document.getElementById('psave').addEventListener('click', () => document.getElementById('save').click());
  window.TUTTI = { shoot, LOOKS, poster };
})();
