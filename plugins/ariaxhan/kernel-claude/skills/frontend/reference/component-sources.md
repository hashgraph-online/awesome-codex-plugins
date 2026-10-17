# Component sources

Curated open-source libraries an agent may pull real building blocks from when implementing
a design direction. Licenses verified 2026-08-07; re-verify per component at pull time.

## The four rules

1. **Pull the primitive, restyle it to the active mood + motion direction. Never ship a
   component stock.** Stock components reintroduce same-site-syndrome with prettier parts:
   strip their default palette/typography/spacing and re-token to the project.
2. **Verify the license of the specific component you pull.** Repo-level licenses below;
   some repos (react-bits) mix terms per component.
3. **The tired-defaults blacklist applies regardless of source.** Never as the identity
   move: fade-up-on-scroll stagger, generic hover scale/lift, border-beam, shimmer/shiny
   text, count-up numbers, infinite logo marquee, spotlight cards, aurora-blob backgrounds,
   bento-for-its-own-sake, basic tilt-on-hover. Supporting cast at most.
4. **Dependency justification still applies** (kernel anti-pattern: built-in beats
   library). A copy-paste component is a snippet, not a dependency; an npm install is a
   dependency and must earn itself.

## Animated components (React / Tailwind / shadcn ecosystem)

| library | strength | install | license |
|---|---|---|---|
| react-bits (DavidHDev/react-bits) | text effects, ~45 WebGL backgrounds, cursor toys, physics | shadcn registry / jsrepo | MIT + Commons Clause on some — check per component |
| magicui (magicuidesign/magicui) | 150+ animated components, landing-page effects | shadcn registry | MIT |
| motion-primitives (ibelick/motion-primitives) | container morphs, springs, text effects | shadcn-style CLI | MIT |
| animata (codse/animata) | product widgets, bento, micro-interactions | copy-paste | MIT |
| cult-ui (nolly-studio/cult-ui) | texture/material surfaces, iOS-style morphs | shadcn registry | MIT |
| kokonutui (kokonut-labs/kokonutui) | animated cards/buttons/AI-chat widgets | shadcn registry | MIT |
| uilayouts (ui-layouts/uilayouts) | layout-level patterns: sticky scroll, reveals, tabs | copy-paste / registry | MIT |
| smoothui (educlopez/smoothui) | tasteful micro-interaction snippets | copy-paste | MIT |
| stackzero-labs/ui | e-commerce blocks (product cards, carts, ratings) | shadcn registry | MIT |

## Shader / canvas / 3D

| library | strength | install | license |
|---|---|---|---|
| paper-shaders (paper-design/shaders) | zero-dep React shader backgrounds; first choice for liquid-material | npm | Apache-2.0 |
| shadergradient (ruucm/shadergradient) | designer-grade moving 3D gradients + configurator | npm | MIT |
| tsparticles | particles, confetti, fireworks (celebration moments) | npm | MIT |
| cobe (shuding/cobe) | 5KB WebGL globe hero widget | npm | MIT |
| react-three-fiber + drei (pmndrs) | full 3D scenes; drei ready-made effects | npm | MIT |
| vanta.js (tengbao/vanta) | drop-in 3D backgrounds; dated aesthetic, reliable | npm | MIT |

## Motion primitives / infrastructure

| library | strength | install | license |
|---|---|---|---|
| motion (motion/react, ex-framer) | default spring/layout/gesture engine | npm | MIT |
| anime.js v4 | timelines, SVG, spring physics | npm | MIT |
| auto-animate (formkit) | zero-config list/layout FLIP transitions | npm | MIT |
| lenis (darkroomengineering) | smooth-scroll foundation (grand-tour prerequisite) | npm | MIT |
| tailwindcss-animate | CSS enter/exit baseline shadcn assumes | npm | MIT |
| GSAP | timelines, ScrollTrigger, SplitText; all plugins now free | npm | custom no-charge, NOT OSI — flag in project docs when used |

## Design-direction primitives

| library | strength | license |
|---|---|---|
| open-props (argyleink/open-props) | curated token defaults; the easing curves especially | MIT |
| fontsource | deterministic npm installs of open fonts for pairings | MIT (fonts keep OFL) |

## Do-not-use ledger (licensing)

| library | reason |
|---|---|
| originui / coss.com/ui | relicensed AGPL-3.0 — copyleft, do not pull |
| aceternity ui | no verifiable open license; inspiration only, never copy |
| hover.dev | no license file, mostly paid |
| background-snippets (ibelick) | no license file; trivial to reimplement instead |
| uiverse galaxy | MIT but quality too uneven for curated use |

## Extending this registry

Append a row with: strength (one line), install style, license verified from the repo on a
stated date. A library with no license file goes in the do-not-use ledger, not the tables.
