# The libraries

Specimens use the project's own library, at the project's version. Only when the project
has none is a copy downloaded into `$WS`, and the caption names its version.

| library | in package.json | file a specimen loads | global | license |
|---|---|---|---|---|
| GSAP | `gsap` | `gsap/dist/gsap.min.js` as `lib-gsap.js`, plugins as `lib-<Plugin>.js` | `gsap` | free for all use including plugins (Webflow's standard license, since 2025); not for building a visual animation builder |
| Motion | `motion`, or the older `framer-motion` | `motion/dist/motion.js` as `lib-motion.js` | `Motion` | MIT |

Copy the file from the project's `node_modules` into the section folder under the `lib-`
name, so it is never confused with the kit's `motion.js`; without one,
`npm pack gsap` or `npm pack motion` into `$WS/vendor` and copy from there. For a project
on `framer-motion`, use `motion` at the same major version or the latest when the major
differs, and say so once in `실물과 다름`: the engine is the same, the import name is not.

## GSAP

    <script src="lib-gsap.js"></script>
    <script src="lib-ScrollTrigger.js"></script>   <!-- only when used -->
    <script src="../motion.js"></script>
    <script>
      const tl = gsap.timeline();
      // The reduced branch exists from step 7 on.
      if (dhMotion.reduced) tl.from('.title, .card', { opacity: 0, duration: 0.15 });
      else tl.from('.title', { y: 24, opacity: 0, duration: 0.4, ease: 'power2.out' })
            .from('.card', { y: 24, opacity: 0, duration: 0.4, ease: 'power2.out', stagger: 0.06 }, 0.1);
      dhMotion.gsap(tl, { track: ['.title', '.card'] });
    </script>

- One timeline per specimen; everything the moment does is in it, so seeking reaches all
  of it. Register plugins (`gsap.registerPlugin(Flip)`) before building it.
- Animate `x`, `y`, `scale`, `rotation`, `opacity`. Animating `width`, `height`, `top` or
  `margin` makes the page reflow; `motion.cjs` reports it under `layout`.
- Flip: record the state, change the layout, then build the timeline from
  `Flip.from(state, { ... })` and add it to `tl`.
- ScrollTrigger (scrubbed or played by scrolling) is connected with `dhMotion.journey`, not
  `dhMotion.gsap` (Scroll, below).

## Motion

    <script src="lib-motion.js"></script>
    <script src="../motion.js"></script>
    <script>
      const { animate, stagger } = Motion;
      const controls = dhMotion.reduced
        ? animate('.title, .card', { opacity: [0, 1] }, { duration: 0.15 })
        : animate([
            ['.title', { y: [24, 0], opacity: [0, 1] }, { duration: 0.4 }],
            ['.card', { y: [24, 0], opacity: [0, 1] },
              { type: 'spring', bounce: 0.2, visualDuration: 0.4, delay: stagger(0.06), at: 0.1 }],
          ]);
      dhMotion.motion(controls, { track: ['.title', '.card'] });
    </script>

- One `animate()` call per specimen, a sequence when several elements move, so one set of
  controls covers the moment. Give every value as `[from, to]`.
- A React project's `<motion.div initial animate transition>` becomes the same values in
  `animate()`; the engine is the same. `AnimatePresence` exit timing and `layoutId`
  hand-overs are imitated: write the from and to boxes as `x`, `y`, `scale` and say so in
  `실물과 다름`.
- A spring's length is computed by the library; `motion.cjs` reports it as `duration`.
- When the code gives no transition, Motion picks a spring for `x`, `y`, `scale` and
  `rotate` and a tween for `opacity` and colors. `animate()` with no transition gives the
  same defaults, so copy the code's transition as it is, or leave it out the same way.
- Motion's `scroll()`, `inView` and `useScroll` follow the page's own scroll on Motion's
  frame loop, which `dhMotion.journey` can't drive. Draw them live (the person scrolls
  inside the iframe) and say once that this section has no bar, graph or strip.

## Scroll

A scroll-linked moment has no clock, so the scroll becomes one. Put everything that builds
the animations in one function and hand it to `dhMotion.journey`:

    <script src="lib-gsap.js"></script>
    <script src="lib-ScrollTrigger.js"></script>
    <script src="../motion.js"></script>
    <script>
      gsap.registerPlugin(ScrollTrigger);
      dhMotion.journey(() => {
        gsap.from('.feature', { y: 60, opacity: 0, stagger: 0.15, ease: 'none',
          scrollTrigger: { trigger: '.features', start: 'top 80%', end: 'top 20%', scrub: true } });
      }, { track: ['.feature'], speed: 1000 });
    </script>

- The page scrolls one fixed path, the same in every specimen: down to the bottom, up to
  the top, down again, at `speed` px/s with a short pause between legs. GSAP's clock is
  driven by hand along it, so the bar, the frame strip and `motion.cjs` see exactly the same
  scene, and going back in time rebuilds from the top (no reload needed).
- The path is the interruption for scroll: scrolling back up mid-way and down again.
- `scroller: '.wrap'` when the page scrolls inside an element instead of the window.
- `motion.cjs` measures in page coordinates (the scroll itself is not motion) and adds,
  per element, `seenAt` (its progress when it first became half visible: 100 means it
  finished where nobody saw it) and `replays` (how often it played again).

## Interruption

A second trigger mid-way (close while opening) has to sit on the one clock too. Compute the
path first, then connect it:

- **Motion:** sample the forward animation with the library's generators
  (`Motion.spring({ keyframes: [360, 0], bounce, visualDuration })` or `Motion.keyframes`),
  which return `next(ms) => { value, done }`. At the interrupt time read the value and the
  velocity (difference of two nearby samples), start a second generator from there with
  that velocity, and write the value yourself in `seek`:
  `dhMotion.custom({ duration: () => total, seek: (s) => { el.style.transform = ... } })`.
  Seeking plain `animate()` controls does not fire `onUpdate` while paused: values written
  only in `onUpdate` never move.
- **GSAP:** build the forward tween paused, seek it to the interrupt time, read the value
  with `gsap.getProperty`, then build the return tween from that value and add both to one
  timeline (`tl.add(forward, 0).add(back, t)` with `forward` cut at `t`); connect with
  `dhMotion.gsap(tl)`.
- The three usual behaviours: reverse from where it is, finish opening then close,
  jump to closed.

## No library yet

When the project has neither, ask once in step 1, with the deciding facts: GSAP for
timelines, scroll scenes and SVG; Motion for a React project's component motion (enter,
exit, layout). The answer is recorded in `README.md` `구현 방침` (`대화로 결정`), with a
note that the package must be added.

## The reference snippet

The `기준 코드` written at step 7 uses the project's library and stack (a `useGSAP` hook
in React with GSAP, `motion` components in React with Motion, plain calls otherwise), the
picked values, and the reduced branch through `prefers-reduced-motion` (GSAP
`gsap.matchMedia()`, Motion `useReducedMotion`). Ten to twenty lines; the spec table is
the source of truth.
