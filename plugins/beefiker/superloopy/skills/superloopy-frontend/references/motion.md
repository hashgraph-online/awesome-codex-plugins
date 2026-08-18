# Web Motion Implementation Guide

This is the Web implementation specialization for [`references/motion-core.md`](motion-core.md). Load the cross-platform temporal contract first, then use this file only when browser-owned nodes and Web motion mechanisms implement the changed claim. Native, Qt, and other routes do not inherit these React, browser, or animation-library examples.

Motion must communicate hierarchy, storytelling, feedback, or state change. Give each non-trivial animation a one-sentence reason; “it looks cool” is not enough. If the repository cannot support a working and verified effect within scope, reduce the animation quantity and complexity and ship a clear static surface.

The React examples below apply only when the project already uses the named libraries, or the user approves adding them. They are **starting templates**, not proof. Adapt them to the project and collect real-browser interaction evidence before calling the motion complete.

## Applicability and inherited authority

Use this reference only when a motion or animated-interaction claim changes. It does not expand a narrow nonvisual change into a motion redesign, anti-slop pass, or visual artifact. The project's existing motion primitives and authoritative design source remain authoritative; use `DESIGN.md` only when it is already that source or as a scoped mapping/receipt synchronized with it. A repository without a formal design-system document is not blocked.

Resolve timing, interaction, supported input, and breakpoint behavior from the current product and target contract. Ask the minimum necessary questions only when material unknowns would change the implementation, and batch independent unknowns. This reference does not make SEO applicable: assess SEO only for the current crawlable public Web target or a distinct deployed public Web target in scope, never because animation code runs in a browser.

The `1024px` media conditions in the templates below are illustrative. Replace them with the actual target-derived breakpoint that has enough space for the effect, and keep the static layout outside that condition; never add or claim a breakpoint merely because it appears in an example.

## Ownership and performance rules

- Avoid raw `window.addEventListener("scroll", …)` loops for continuous animation. Use a project-native motion value, GSAP ScrollTrigger, IntersectionObserver, or a progressively enhanced CSS scroll-driven animation.
- Do not store scroll progress, pointer position, or magnetic-hover offsets in React state. Use Motion values, GSAP setters, refs, or another value channel outside React rendering.
- Do not drive the same DOM property on the same element from multiple animation engines. Motion and GSAP may coexist only on disjoint elements/properties with explicit ownership; isolate Three.js inside its canvas boundary.
- Keep effect setup and cleanup in the component that owns the animated nodes. In React Server Component projects, that owner is a bounded client component; it does not have to force the entire rendered subtree client-side.
- Animate compositor-friendly `transform` and `opacity` by default. Treat filters as potentially expensive and verify them on the target device.
- Every GSAP or event-driven effect must return cleanup. Prefer `gsap.matchMedia().revert()` when media conditions own setup.

## Reduced motion and static layout

The unanimated DOM is the fallback and must expose every item in normal document flow. Create pin/scrub effects only inside `(prefers-reduced-motion: no-preference)` and an appropriate viewport condition. Do not merely return early from JavaScript while leaving `sticky`, horizontal flex, or clipped overflow styles active; that can preserve the disorienting layout or hide content.

## Template 1 — sticky scroll-stack with one driver

GSAP owns pinning and transforms. The CSS fallback is an ordinary vertical list; do not combine ScrollTrigger pinning with `position: sticky` on the same card.

```tsx
"use client";
import { useEffect, useRef } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

export function StickyStack({ cards }: { cards: React.ReactNode[] }) {
  const root = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!root.current) return;
    const mm = gsap.matchMedia();
    mm.add(
      { animate: "(min-width: 1024px) and (prefers-reduced-motion: no-preference)" },
      (context) => {
        if (!context.conditions?.animate) return;
        const elements = gsap.utils.toArray<HTMLElement>(".stack-card");
        elements.slice(0, -1).forEach((card, index) => {
          ScrollTrigger.create({
            trigger: card,
            start: "top top",
            endTrigger: elements[elements.length - 1],
            end: "top top",
            pin: true,
            pinSpacing: false,
          });
          gsap.to(card, {
            scale: 0.92,
            opacity: 0.55,
            ease: "none",
            scrollTrigger: {
              trigger: elements[index + 1],
              start: "top bottom",
              end: "top top",
              scrub: true,
            },
          });
        });
      },
      root.current,
    );
    return () => mm.revert();
  }, []);

  return (
    <div ref={root} className="relative grid gap-8">
      {cards.map((card, index) => (
        <section key={index} className="stack-card flex min-h-[70dvh] items-center justify-center">
          {card}
        </section>
      ))}
    </div>
  );
}
```

Keep `start: "top top"` so pinning begins at the viewport edge. Exercise forward and reverse scrolling, confirm the last card is never pinned, and inspect cleanup after route changes.

## Template 2 — horizontal pan with responsive measurement

The base CSS is a visible vertical grid. It becomes a horizontal track only under the same condition that creates ScrollTrigger, so mobile and reduced-motion users retain normal document flow.

```tsx
"use client";
import { useEffect, useRef } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

export function HorizontalPan({ panels }: { panels: React.ReactNode[] }) {
  const wrap = useRef<HTMLElement>(null);
  const track = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!wrap.current || !track.current) return;
    const mm = gsap.matchMedia();
    mm.add(
      { animate: "(min-width: 1024px) and (prefers-reduced-motion: no-preference)" },
      (context) => {
        if (!context.conditions?.animate) return;
        const distance = () => Math.max(0, track.current!.scrollWidth - wrap.current!.clientWidth);
        gsap.to(track.current, {
          x: () => -distance(),
          ease: "none",
          scrollTrigger: {
            trigger: wrap.current,
            start: "top top",
            end: () => `+=${Math.max(distance(), 1)}`,
            pin: true,
            scrub: 1,
            invalidateOnRefresh: true,
          },
        });
      },
      wrap.current,
    );
    return () => mm.revert();
  }, []);

  return (
    <section ref={wrap} className="horizontal-pan">
      <div ref={track} className="horizontal-track">
        {panels.map((panel, index) => (
          <article key={index} className="horizontal-panel">
            {panel}
          </article>
        ))}
      </div>
    </section>
  );
}
```

```css
.horizontal-track {
  display: grid;
  gap: 2rem;
}

.horizontal-panel {
  min-width: 0;
}

@media (min-width: 1024px) and (prefers-reduced-motion: no-preference) {
  .horizontal-pan {
    overflow: hidden;
  }

  .horizontal-track {
    display: flex;
    align-items: center;
    gap: 0;
    height: 100dvh;
  }

  .horizontal-panel {
    flex: 0 0 100%;
  }
}
```

Function-based `x` and `end` values remeasure on ScrollTrigger refresh. Test a resize while the trigger is active, tracks narrower than the container, late-loading fonts/images, and reverse scrolling.

## Template 3 — viewport reveal with Motion

For items that only enter as they become visible, Motion is simpler than a pin/scrub engine. Use this only when Motion is already present or approved.

```tsx
"use client";
import { motion, useReducedMotion } from "motion/react";

export function RevealStagger({ items }: { items: string[] }) {
  const reduce = useReducedMotion();
  return (
    <ul className="grid gap-6">
      {items.map((item, index) => (
        <motion.li
          key={item}
          initial={reduce ? false : { opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.3 }}
          transition={{
            duration: reduce ? 0 : 0.6,
            delay: reduce ? 0 : Math.min(index, 6) * 0.06,
            ease: [0.16, 1, 0.3, 1],
          }}
        >
          {item}
        </motion.li>
      ))}
    </ul>
  );
}
```

## Evidence checklist

- Exercise the interaction, not only its resting screenshot, across the target-derived browser/OS/input and breakpoint matrix. Treat 390 / 768 / 1280 px only as optional baseline samples when selected by the product's supported range; they are never universal proof.
- Exercise each target-supported viewport, resize, orientation, or container transition while pin/scrub motion is active and verify the endpoint remains aligned.
- Toggle reduced motion and confirm every item stays visible in static document flow.
- Navigate away and back; verify no duplicate triggers, listeners, or transforms remain.
- Check each supported input around the animated section, including keyboard, touch, or pointer only where the target contract includes it.
- When the changed motion has a visible-state or layout consequence, record the observed states and project-specific adaptation in `VISUAL_QA.md`; retain real interaction, accessibility, cleanup, and regression evidence rather than treating a resting screenshot as proof.

Selected motion mechanisms were adapted under MIT from Taste Skill; see `references/upstream-notice.md`.
