// fx-demo.js — one second per primitive added in motion-lib's beat / time / particles / light / transitions / glitch / stylised sections.
// Smoke test + gallery:  node tools/render-fast.js fx-demo.html stills/fx --stills 0.6,1.6,…   (or open fx-demo.html and scrub)
const LOWS = [0, .5, 1, 1.5, 2, 2.5, 3], HIGHS = Array.from({ length: 40 }, (_, i) => i * .125);
const A = () => { ctx.fillStyle = '#FB7ACB'; ctx.fillRect(0, 0, W, H); ctx.fillStyle = '#1a1020'; ctx.font = SANS(900, 520); ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText('A', W / 2, H / 2); };
const B = () => { ctx.fillStyle = '#3B7AFA'; ctx.fillRect(0, 0, W, H); for (let i = 0; i < 6; i++) disc(200 + (i % 3) * 340, 640 + Math.floor(i / 3) * 640, 120, ['#FCB901', '#F4F0E8', '#FB7ACB'][i % 3]); };
const word = (s, size = 300, color = '#fff') => () => { ctx.fillStyle = color; ctx.font = SANS(900, size); ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(s, W / 2, H / 2); };
const LOGO = []; // filled in setup
const DEMOS = [
  ['beatCam', u => { ctx.save(); beatCam(u, LOWS, HIGHS, { amt: 1.6 }); A(); ctx.restore(); }],
  ['curlParticles', u => { ctx.fillStyle = '#0B0B14'; ctx.fillRect(0, 0, W, H); curlParticles(u + 2, { n: 260, rate: 130, emit: i => [W * hash(i * 3.1), H * .95], color: '#7FD4FF', size: 5 }); }],
  ['assemble', u => { ctx.fillStyle = '#0B0B14'; ctx.fillRect(0, 0, W, H); assemble(LOGO, seg(u, .05, .85), { color: '#FCB901', r: 6 }); }],
  ['saber', u => { ctx.fillStyle = '#05060C'; ctx.fillRect(0, 0, W, H); saber(heartP(W / 2, H / 2, 26), { prog: eox(seg(u, 0, .7)), color: '#FF3FA4', w: 10 }); saber(ellP(W / 2, H / 2, 420, 420, 60), { prog: eox(seg(u, .1, .8)), color: '#2FB6FF', seed: 5 }); }],
  ['shine', u => { ctx.fillStyle = '#05060C'; ctx.fillRect(0, 0, W, H); const L = layer('_d', word('tutti', 260, '#FFE9A8')); ctx.drawImage(L, 0, 0); shine(L, W / 2 + Math.sin(u * 3) * 300, H * .38, { len: .7 }); }],
  ['whipPan', u => whipPan(A, B, seg(u, .15, .75))],
  ['iris star', u => iris(A, B, seg(u, .1, .8), { shape: 'star', ring: 14 })],
  ['inkReveal', u => inkReveal(A, B, seg(u, .05, .9), { cx: W * .3, cy: H * .7 })],
  ['shatter', u => shatter(A, B, seg(u, .1, .9))],
  ['infiniteZoom', u => infiniteZoom(k => { ctx.fillStyle = ['#FB7ACB', '#3B7AFA', '#FCB901', '#388D56'][((k % 4) + 4) % 4]; ctx.fillRect(0, 0, W, H); ctx.fillStyle = '#F4F0E8'; ctx.fillRect(W / 2 - W / 6.4 - 12, H / 2 - H / 6.4 - 12, W / 3.2 + 24, H / 3.2 + 24); ctx.font = SANS(900, 120); ctx.fillStyle = '#111'; ctx.textAlign = 'center'; ctx.fillText('TAKE ' + (k + 1), W / 2, H * .2); }, u * 1.5)],
  ['panels', u => { ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, W, H); panels([{ poly: [[40, 40], [1040, 40], [1040, 700], [40, 820]], t0: 0, draw: A, from: [-400, 0] }, { poly: [[40, 860], [1040, 740], [1040, 1300], [40, 1300]], t0: .2, draw: B, from: [400, 0] }, { poly: [[40, 1340], [1040, 1340], [1040, 1880], [40, 1880]], t0: .4, draw: () => { ctx.fillStyle = '#111'; ctx.fillRect(0, 0, W, H); ctx.fillStyle = '#fff'; ctx.font = SANS(900, 160); ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText('もう一回', W / 2, 1610); } }], u); }],
  ['rgbSplit + glitch', u => { const L = layer('_d', A); const G = layer('_g', () => glitchSlices(L, pulse(HIGHS, u, 6))); rgbSplit(G, 30 * pulse(LOWS, u, 4) + 6); crt(); }],
  ['mosaic', u => mosaic(layer('_d', B), lerp(80, 4, eox(seg(u, 0, .8))))],
  ['dither', u => { const L = layer('_d', () => { const g = ctx.createRadialGradient(W / 2, H * .4, 50, W / 2, H * .5, 900); g.addColorStop(0, '#fff'); g.addColorStop(1, '#000'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H); toonBall(W / 2, H * .62, 300 + u * 40, { base: '#bbb', shade: '#555', hi: '#fff' }); }); dither(L, { palette: ['#1B1B2F', '#6B5C7B', '#F2EBDD'], px: 5 }); }],
  ['slitScan', u => slitScan(t => { ctx.fillStyle = '#F4F0E8'; ctx.fillRect(0, 0, W, H); hero(W / 2 + Math.sin(t * 6) * 360, H / 2, 160, { color: '#FB7ACB' }); }, u, { bands: 32, lag: 1.6 })],
  ['echo', u => { ctx.fillStyle = '#F4F0E8'; ctx.fillRect(0, 0, W, H); echo(t => hero(lerp(150, 930, eio(seg(t, 0, .9))), H / 2 + Math.sin(t * 9) * 200, 90, { color: '#3B7AFA' }), u, { n: 6 }); }],
  ['extrude', u => { ctx.fillStyle = '#FCB901'; ctx.fillRect(0, 0, W, H); ctx.save(); ctx.translate(W / 2, H / 2); ctx.rotate(-.08 + Math.sin(u * 2) * .04); extrude((c, face) => { ctx.font = SANS(900, 300); ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillStyle = face ? '#FB7ACB' : c; ctx.fillText('POP', 0, 0); }, { depth: lerp(4, 70, eox(seg(u, 0, .6))), side: '#7A1F55' }); ctx.restore(); }],
  ['toonBall', u => { ctx.fillStyle = '#FFF4E0'; ctx.fillRect(0, 0, W, H); toonBall(W / 2, H / 2, 320, { light: -2.3 + u * 2, rim: '#FFD0EC' }); toonBall(300, 1500, 120, { base: '#62C0DA', shade: '#2B7E9A', hi: '#fff' }); }],
  ['paper', u => { ctx.fillStyle = '#E9DFCB'; ctx.fillRect(0, 0, W, H); paper(() => disc(W / 2, H * .6, 380, '#388D56')); paper(() => { ctx.fillStyle = '#DC644A'; ctx.beginPath(); starPath(ctx, W / 2, H * .35 + Math.sin(u * 4) * 30, 220, u); ctx.fill(); }, { lift: 24, seed: 4 }); }],
  ['riso', u => riso(() => { ctx.fillStyle = '#000'; ctx.font = SANS(900, 340); ctx.textAlign = 'center'; ctx.fillText('出片', W / 2, H * .45); disc(W / 2, H * .7, 200, '#000'); })],
  ['textOnPath', u => { blush(u); const pts = ellP(W / 2, H / 2, 380, 380, 80, -Math.PI); doodle(pts, { color: '#4E8A6E', w: 6 }); textOnPath('神图，玩一下就来 · ONE MORE TAKE · ', pts, { offset: u * .25, font: SANS(800, 58) }); }],
  ['zoomThrough', u => zoomThrough(() => { A(); disc(W / 2, H * .62, 90, '#111'); }, B, seg(u, .05, .9), { cy: H * .62 })],
  ['pixelDissolve', u => pixelDissolve(A, B, seg(u, .05, .9), { order: 'wipe' })],
  ['tear', u => tear(A, B, seg(u, .05, .9))],
  ['morph', u => { ctx.fillStyle = '#F4F0E8'; ctx.fillRect(0, 0, W, H); ctx.fillStyle = '#FB7ACB'; smoothPath(morph(ellP(W / 2, H / 2, 300, 300, 60), heartP(W / 2, H / 2, 22), Math.sin(u * Math.PI)), true); ctx.fill(); }],
  ['flash + stutter', u => { [A, B][stutter(u, 0, [0, 0, 1, 0, 1, 1], 10)](); flash(u, [.4], { mode: 'invert', frames: 30 }); }],
  ['glow', u => { ctx.fillStyle = '#07070D'; ctx.fillRect(0, 0, W, H); const L = layer('_d', () => { word('NEON', 240, '#FF7AD0')(); disc(W / 2, H * .7, 60 + u * 40, '#FFF0A0'); }); ctx.drawImage(L, 0, 0); glow(L, { threshold: .3 }); }],
  ['scatterGrow', u => { ctx.fillStyle = '#E8F1E4'; ctx.fillRect(0, 0, W, H); scatterGrow(seg(u, 0, .9), (x, y, s, i) => { ctx.save(); ctx.translate(x, y); ctx.scale(s, s); ctx.fillStyle = ['#388D56', '#FB7ACB', '#FCB901'][i % 3]; ctx.beginPath(); starPath(ctx, 0, 0, 34, i); ctx.fill(); ctx.restore(); }, { origin: [W / 2, H] }); }],
  ['taper', u => { ctx.fillStyle = '#FBF8F2'; ctx.fillRect(0, 0, W, H); taper(ellP(W / 2, H / 2, 380, 300, 50, -1.6, 1.1), { prog: eox(seg(u, 0, .7)), w: 30 }); taper(starP(W / 2, H / 2, 200), { w: 18, color: '#DC644A', prog: eox(seg(u, .2, .9)) }); }],
  ['clothDrop', u => { ctx.fillStyle = '#2B2B33'; ctx.fillRect(0, 0, W, H); clothDrop(() => { ctx.fillStyle = '#DC644A'; ctx.fillRect(140, 300, 800, 1200); word('SALE', 220, '#FBF8F2')(); }, seg(u, 0, .95)); }],
  ['watercolor', u => { ctx.fillStyle = '#F6F1E7'; ctx.fillRect(0, 0, W, H); watercolor(W * .42, H * .45, 300, '#3B7AFA'); watercolor(W * .6, H * .58, 260, '#FB7ACB', { seed: 5 }); }],
  ['hatch', u => hatch(layer('_d', () => { ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, W, H); toonBall(W / 2, H / 2, 360, { base: '#bbb', shade: '#555', hi: '#fff', ink: '#000' }); }))],
  ['ascii', u => ascii(layer('_d', () => { ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H); toonBall(W / 2, H / 2, 380, { base: '#ccc', shade: '#555', hi: '#fff', ink: '#000' }); }), { decode: seg(u, 0, .8) })],
  ['tategaki', u => { ctx.fillStyle = '#0a0a0a'; ctx.fillRect(0, 0, W, H); ctx.fillStyle = '#d6001c'; ctx.fillRect(620, 0, 300, H); tategaki('もう一回', 770, 260, 280, { t0: 0 }); tategaki('出片', 330, 500, 160, { t0: .3, color: '#d6001c' }); }],
  ['filmDamage', u => { A(); filmDamage(u, { leak: .7, hits: [.3] }); }],
];
const DUR = DEMOS.length;
startFilm({
  dur: DUR,
  setup: async () => { LOGO.push(...samplePts(word('tutti', 300), 14)); },
  render(t) {
    const k = Math.min(DEMOS.length - 1, Math.floor(t)), u = t - k; DEMOS[k][1](u);
    ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over'; ctx.fillStyle = 'rgba(0,0,0,.6)'; rr(ctx, 30, 30, 560, 74, 20); ctx.fill(); ctx.fillStyle = '#fff'; ctx.font = MONO(40); ctx.textAlign = 'left'; ctx.textBaseline = 'middle'; ctx.fillText(`${k + 1}. ${DEMOS[k][0]}`, 54, 68); ctx.restore();
  },
});
