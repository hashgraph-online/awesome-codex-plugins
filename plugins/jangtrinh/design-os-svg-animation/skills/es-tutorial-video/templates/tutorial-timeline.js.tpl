/* {{TITLE}} tutorial timeline: beat grid, chapters, on-screen elements and bilingual captions.
 * Grid, duration and music credit come from tutorial.config.json (D.CONFIG). Every excerpt comes verbatim from
 * data/evidence.js (extract-evidence.py), never typed by hand. Authored from skills/es-tutorial-video/concepts.md. */
(function (root) {
  const D = root.DOS, E = root.EVIDENCE, C = D.CONFIG;
  const BAR = 240 / C.grid.bpm, DB0 = C.grid.db0, B = BAR / 4, T = C.duration;
  // Story bars warp onto music bars so each chapter fits its voice clip. Knots are integer bars, so every chapter
  // boundary stays on a downbeat. Pairs: [story bar, music bar].
  const WARP = [[-1, -1], [200, 200]];
  const warp = (n) => {
    let i = WARP.findIndex(([s]) => s >= n);
    i = i < 0 ? WARP.length - 1 : Math.max(1, i);
    const [s0, m0] = WARP[i - 1], [s1, m1] = WARP[i];
    return m0 + (n - s0) * (m1 - m0) / (s1 - s0);
  };
  const bar = (n) => DB0 + warp(n) * BAR;      // absolute time of a (story) bar's downbeat

  // chapters: [id, start bar, end bar, number, title, sub, card image]  (first = title card with number 0, last = outro)
  const CH = [
  ].map(([id, a, z, num, title, sub, img]) => ({ id, t0: bar(a), t1: Math.min(bar(z), T), num, title, sub, img }));

  const EL = [], CAP = [];
  const el = (o) => EL.push(o);
  const cap = (a, z, vi, en) => CAP.push({ t0: bar(a), t1: bar(z), vi, en });
  const ex = (k, pick, more) => ({ path: E[k].path, from: E[k].from, lines: pick ? pick.map((i) => E[k].lines[i]) : E[k].lines, more: !!more });
  const val = (k) => ({ path: E[k].path, value: E[k].value });
  const line = (k) => E[k].lines[E[k].lines.length - 1];
  const R = { L: [72, 132, 1010, 640], R: [1120, 132, 728, 640], F: [72, 132, 1776, 640], LW: [72, 132, 1180, 640], RN: [1290, 132, 558, 640] };

  // el({ type: 'file', t0: bar(9), t1: bar(24), rect: R.L, ...ex('some_key'), tag: 'label' });
  // cap(9, 12, 'Lời tiếng Việt.', 'English line.');

  Object.assign(D, { BAR, DB0, B, T, bar, CH, EL, CAP, CREDIT: C.music.credit, tl: { el, cap, ex, val, line, R, E } });
})(window);
