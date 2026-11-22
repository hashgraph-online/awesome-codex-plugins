# Warli

Also called: warli art, warli painting.

Family: Folk and print traditions. Cadence: steps 8 times a second. Usual tool: HyperFrames (canvas or SVG).

White figures drawn in simple shapes on a terracotta wall: a circle for a head, two triangles joined at their tips for a body, stick arms and legs, a ring of people dancing hand in hand round a tarpa player, trees, huts and a sun. It is a living tradition with working artists; the demo here is a code study of its visual rules, not the craft itself, and a film should credit the tradition and, where it can, commission or license work from the artists.

Warli painting is tribal art made mostly by the Warli people of the North Sahyadri Range in Maharashtra, India, usually on the mud walls of village huts, in a white pigment of rice flour and water with a gum binder. Its basic shapes are the circle, triangle and square; people and animals are drawn as two inverse triangles joined at their tips, and the tarpa dance, in which men and women entwine hands and circle the tarpa player, is a central subject.

## What makes it read as this

- White (rice-paste) lines and fills only, on a red-brown mud ground
- Figures of a circle head and two triangles that meet at their tips, with stick limbs
- A ring or spiral dance, hands joined, round a central player
- Trees as a trunk with paired branches; a sun as a circle with strokes
- Borders of repeating diamonds; huts as a square with a triangle roof

## Timing

Figures appear one at a time over about 3 seconds and the spiral turns slowly while they step between two poses. The picture steps about 8 times a second, and the poses at 4.

## How to build it

- Ground: base colour plus a dozen big soft radial gradients for daubed mud, then a fine speckle
- A figure is two filled triangles, a disc and stroked limbs (`warliFigure()` in `looks-folk.js`), turned so the head points outward
- Place figures along a spiral and add a slow rotation of the whole spiral from stepped time
- Trees: a trunk and branches as paired strokes that shorten toward the top, a dot at each tip

## Assets

All in code. A scan of a mud-plastered wall makes a stronger ground if the user has one. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

Drum and tarpa-like reed drone, claps on the pose changes. Practice note.

## What makes it look wrong

- Colour: the tradition is white on brown or red-brown
- Rounded, realistic bodies
- Presenting a machine-made picture as authentic Warli art

## Tested demo

This is the look from `art-forms/looks-folk.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=warli` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  warli: { kind: '2d', fps: 8, draw(g, t, W, H) {
    // white on a mud-wall red: a spiral of stick-limbed figures dancing hand in hand round a tarpa player, a sun, trees, and a chain of diamonds along the edge
    const ts = held(t, 8), step = frameOf(t, 4) % 2, spin = ts * 0.3, cx = 480, cy = 288;
    bg(g, W, H, '#9b4a2d');
    for (let i = 0; i < 16; i++) { const b = g.createRadialGradient(hash(i, 1) * W, hash(i, 2) * H, 10, hash(i, 1) * W, hash(i, 2) * H, 120 + hash(i, 3) * 160); b.addColorStop(0, i % 2 ? 'rgba(190,100,60,.28)' : 'rgba(70,24,12,.3)'); b.addColorStop(1, 'rgba(0,0,0,0)'); g.fillStyle = b; g.fillRect(0, 0, W, H); }   // a daubed mud wall
    speckle(g, W, H, 5, 60, [235, 190, 150]);
    g.strokeStyle = WHITE; g.lineWidth = 2.4; g.lineJoin = 'round';
    for (const y of [26, H - 26]) { const n = 36, k = prog(ts, 0, 1); for (let i = 0; i < n * k; i++) { const x = 30 + i * ((W - 60) / n); g.beginPath(); g.moveTo(x, y); g.lineTo(x + 13, y - 10); g.lineTo(x + 26, y); g.lineTo(x + 13, y + 10); g.closePath(); g.stroke(); } }
    g.beginPath(); for (const y of [48, H - 48]) { g.moveTo(30, y); g.lineTo(W - 30, y); } g.stroke();
    const sun = prog(ts, 0.1, 0.8); g.lineWidth = 3; strokePart(g, circlePts(140, 120, 30, 28), sun); for (let i = 0; i < 14 * sun; i++) { const a = (i / 14) * TAU; g.beginPath(); g.moveTo(140 + Math.cos(a) * 40, 120 + Math.sin(a) * 40); g.lineTo(140 + Math.cos(a) * 56, 120 + Math.sin(a) * 56); g.stroke(); }
    warliTree(g, 860, 440, 1.2, prog(ts, 1.8, 1.2)); warliTree(g, 100, 440, 0.9, prog(ts, 2.4, 1.2));
    for (const [hx, st] of [[230, 3.0], [730, 3.3]]) { const k = prog(ts, st, 0.6); if (k > 0) { g.lineWidth = 3; strokePart(g, [[hx - 34, 440], [hx - 34, 400], [hx, 372], [hx + 34, 400], [hx + 34, 440], [hx - 34, 440]], k); strokePart(g, [[hx - 8, 440], [hx - 8, 414], [hx + 8, 414], [hx + 8, 440]], k); } }   // two huts
    for (let i = 0; i < 22; i++) {   // the dance: one spiral, eleven figures to a turn, heads outward, hands joined
      if (prog(ts, 0.3 + i * 0.07, 0.1) <= 0) continue;
      const a = (i * TAU) / 11 + spin, r = 78 + i * 4.2, s = 9 + r * 0.06;
      warliFigure(g, cx + Math.cos(a) * r, cy + Math.sin(a) * r, s, a + Math.PI / 2, (step + i) % 2, s * 1.45);
    }
    if (prog(ts, 0.1, 0.4) > 0) { warliFigure(g, cx, cy + 6, 14, 0, step, 14); g.beginPath(); g.moveTo(cx + 30, cy - 6); g.lineTo(cx + 78, cy - 30); g.lineTo(cx + 78, cy + 14); g.closePath(); g.stroke(); g.beginPath(); g.arc(cx + 82, cy - 8, 4, 0, TAU); g.fill(); }   // the tarpa: a gourd horn
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Warli_painting>

Facts checked on 2026-11-21. Lines marked "practice note" are working advice, not sourced facts.
