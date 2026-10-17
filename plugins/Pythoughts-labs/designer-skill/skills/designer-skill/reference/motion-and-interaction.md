# Motion & Interaction

Motion is part of the build, not a finishing sticker. Every animation must convey state, give feedback, or clarify hierarchy. Cut motion that exists only for decoration — animation fatigue is a real cost. Spend the budget on the moments that earn it.

GPU/hardware-acceleration rules (animate only `transform`/`opacity`, `will-change` sparingly, 16ms/60fps budget, CSS variables trigger child recalc) live in **engineering-and-performance.md**. This file owns *what* to animate, *how fast*, *with which curve*, and *the interaction patterns*. Cross-ref it for the *why it's fast*.

---

## 1. Should this animate at all?

Decide by how often the user sees it. The more frequent, the less motion.

| Frequency | Examples | Decision |
| --- | --- | --- |
| **100+ times/day** | Keyboard shortcuts, command palette toggle | **No animation. Ever.** |
| **Tens of times/day** | Hover effects, list navigation | Remove or drastically reduce |
| **Occasional** | Modals, drawers, toasts | Standard animation |
| **Rare / first-time** | Onboarding, feedback forms, celebrations | Can add delight |

**Never animate keyboard-initiated actions.** Raycast has no open/close animation — optimal for something used hundreds of times a day. Animation on hundreds-of-times-daily actions feels slow, delayed, and disconnected from the input.

---

## 2. Purpose of animation

Every animation must answer "why does this animate?" in one sentence. If the answer is "it looks cool" and the user sees it often, don't animate.

Valid purposes:
- **Spatial consistency** — toast enters and exits from the same direction so swipe-to-dismiss feels intuitive.
- **State indication** — a morphing feedback button shows the state change.
- **Explanation** — a marketing animation showing how a feature works.
- **Feedback** — a button scales down on press, confirming the interface heard the user.
- **Preventing jarring changes** — elements appearing/disappearing without transition feel broken.

Each ScrollTrigger, marquee, and pinned section needs its own reason. GSAP everywhere because GSAP is available is amateur.

---

## 3. Easing

Use custom curves. Built-in CSS easings are too weak; they lack the punch that makes animation feel intentional. Don't craft curves from scratch — use [easing.dev](https://easing.dev/) or [easings.co](https://easings.co/) for stronger variants.

**Easing decision:**

| Situation | Easing |
| --- | --- |
| Entering or exiting | **ease-out** (starts fast, feels responsive) |
| Moving / morphing on screen | ease-in-out |
| Hover / color change | ease |
| Constant motion (marquee, progress bar) | linear |
| Default | ease-out |

```css
/* Strong ease-out curves for UI */
--ease-out:     cubic-bezier(0.23, 1, 0.32, 1);    /* Strong ease-out for UI */
--ease-in-out:  cubic-bezier(0.77, 0, 0.175, 1);   /* Strong ease-in-out for on-screen movement */
--ease-drawer:  cubic-bezier(0.32, 0.72, 0, 1);    /* iOS-like drawer curve (Ionic) */

/* Named ease-out family */
--ease-out-quart: cubic-bezier(0.25, 1, 0.5, 1);   /* Smooth */
--ease-out-quint: cubic-bezier(0.22, 1, 0.36, 1);  /* Snappier */
--ease-out-expo:  cubic-bezier(0.16, 1, 0.3, 1);   /* Confident, decisive */
```

**Never use `ease-in` for UI.** It starts slow, delaying the initial movement at the exact moment the user is watching most closely. A dropdown with `ease-in` at 300ms *feels* slower than `ease-out` at the same 300ms.

❌ **Banned — feel dated and tacky:**
```css
/* bounce:   cubic-bezier(0.34, 1.56, 0.64, 1) */
/* elastic:  cubic-bezier(0.68, -0.6, 0.32, 1.6) */
```
Bounce and elastic draw attention to the animation itself. Also banned: `linear` and `ease-in-out` as the *default* register on high-end work — physics-based curves feel real and expensive.

---

## 4. Duration

Timing matters more than easing for "feels right." Match duration to interaction type.

| Element | Duration |
| --- | --- |
| Button press feedback | **100–160ms** |
| Tooltips, small popovers | **125–200ms** |
| Dropdowns, selects | **150–250ms** |
| Modals, drawers | **200–500ms** |
| Toggle switches, show/hide | 200–300ms |
| Entrance (page load, hero reveal) | 500–800ms |
| Marketing / explanatory | Can be longer |

The 100/300/500 rule: **100–150ms** instant feedback, **200–300ms** state changes, **300–500ms** layout changes, **500–800ms** entrances.

**Hard rule: keep UI animations under 300ms.** A 180ms dropdown feels more responsive than a 400ms one. **Never use durations over 500ms for feedback** — it feels laggy.

**Exit ≈ 75% of enter duration.** Faster exits keep dismissal feeling responsive. More broadly, use **asymmetric timing**: slow where the user decides, fast where the system responds (hold-to-delete press 2s linear, release 200ms ease-out).

Product register: **150–250ms on most transitions.** No orchestrated page-load sequences — users load into a task, not a show.

---

## 5. Springs

Springs simulate physics and settle on parameters, not a fixed duration. They maintain velocity when interrupted — CSS animations and keyframes restart from zero — so a click-then-Escape reverses smoothly from its current position.

**Use springs for:** drag with momentum; elements that should feel "alive" (Apple's Dynamic Island); interruptible gestures; decorative mouse-tracking.

```js
// Apple's approach (recommended — easier to reason about)
{ type: "spring", duration: 0.5, bounce: 0.2 }

// Traditional physics (more control)
{ type: "spring", mass: 1, stiffness: 100, damping: 10 }
```

Keep **bounce subtle (0.1–0.3)**. Avoid bounce in most UI; reserve it for drag-to-dismiss and playful interactions. For perpetual micro-interactions and Stitch-style "alive" components, use `{ stiffness: 100, damping: 20 }` — never linear easing.

**Decorative mouse-tracking** through a spring instead of binding visuals directly to the pointer (which feels artificial because it lacks motion):
```jsx
import { useSpring } from 'framer-motion';
const springRotation = useSpring(mouseX * 0.1, { stiffness: 100, damping: 10 });
```
This only works because it's decorative. A functional graph in a banking app is better with no animation.

---

## 6. Micro-interactions

| ✅ Do | ❌ Don't |
| --- | --- |
| `:active { transform: scale(0.97) }` (subtle 0.95–0.98) | Animate from `scale(0)` — nothing in reality appears from nothing |
| Enter from `scale(0.95); opacity: 0` | `transform: scale(0)` on entry |
| Hover scale 1.02–1.05, shadow/color shift | Hover with no feedback (feels dead) |
| Click: quick scale down→up (0.95 → 1) | Block interaction during the animation |
| Card hover feedback via the card's background, border, or shadow | Transform an `<img>` on `:hover` — incl. Tailwind `group-hover:scale/rotate/translate` driving a child image; the image is not an action target, the motion adds no information |

```css
.button { transition: transform 160ms ease-out; }
.button:active { transform: scale(0.97); }   /* instant press feedback */
```

`scale()` also scales children — font size, icons, content scale proportionally on press. That's a feature.

**Delight button (physical press):**
```css
.button { transition: transform 0.1s, box-shadow 0.1s; }
.button:active { transform: translateY(2px); box-shadow: 0 2px 4px rgba(0,0,0,0.2); }
.button:hover { transform: translateY(-2px); transition: transform 0.2s cubic-bezier(0.25, 1, 0.5, 1); } /* ease-out-quart */
```

**Origin-aware popovers.** Default `transform-origin: center` is wrong for almost every popover — scale from the trigger. **Modals are the exception**: keep `center` because they aren't anchored to a trigger.
```css
.popover { transform-origin: var(--radix-popover-content-transform-origin); } /* Radix */
.popover { transform-origin: var(--transform-origin); }                       /* Base UI */
```

**Tooltips: delay first, then skip.** Delay the first tooltip to prevent accidental activation; once one is open, adjacent tooltips open instantly with no animation. This makes the whole toolbar feel faster.
```css
.tooltip { transition: transform 125ms ease-out, opacity 125ms ease-out; transform-origin: var(--transform-origin); }
.tooltip[data-starting-style], .tooltip[data-ending-style] { opacity: 0; transform: scale(0.97); }
.tooltip[data-instant] { transition-duration: 0ms; }
```

**Use CSS transitions, not keyframes, for rapidly-triggered / interruptible UI.** Transitions retarget mid-animation; keyframes restart from zero and jump (toasts, toggles).

**Mask imperfect crossfades with subtle blur.** When a crossfade shows two overlapping states, add `filter: blur(2px)` during the transition to blend them into one perceived morph. **Keep blur under 20px** — heavy blur is expensive, especially in Safari.

---

## 7. CSS transforms & clip-path techniques

**Percentage translate** adapts to element size — `translateY(100%)` moves an element by its own height regardless of dimensions (how Sonner places toasts, how Vaul hides drawers). Prefer percentages over hardcoded px.

**`@starting-style`** animates entry from `display: none` with CSS only, replacing the `useEffect → mounted` pattern. **3D depth** via `rotateX`/`rotateY` + `transform-style: preserve-3d` (orbits, coin flips) needs no JS.

**`clip-path: inset(top right bottom left)`** is a primary animation tool, hardware-accelerated. Each value "eats" into the element.

| Effect | Technique |
| --- | --- |
| Hidden right → visible | `inset(0 100% 0 0)` → `inset(0 0 0 0)`, `transition: clip-path 200ms ease-out` |
| Scroll image reveal | start `inset(0 0 100% 0)` → `inset(0 0 0 0)` on viewport enter (IntersectionObserver / `useInView { once: true, margin: "-100px" }`) |
| Hold-to-delete | overlay `inset(0 100% 0 0)`; on `:active` → `inset(0 0 0 0)` over **2s linear**; release snaps back **200ms ease-out**; `scale(0.97)` on the button |
| Comparison slider | overlay two images, clip top with `inset(0 50% 0 0)`, drive right inset from drag — no extra DOM |
| Perfect tab color transition | duplicate the tab list, style the copy "active", clip so only the active tab shows, animate the clip on change |

**Motion materials — match material to effect** (not transform/opacity only):

| Material | Use for |
| --- | --- |
| transform / opacity | movement, press feedback, simple reveals, list choreography |
| blur / filter / backdrop-filter | focus pulls, depth, glass/lens, softened entrances |
| clip-path / masks | wipes, reveals, editorial cropping |
| shadow / glow / color filters | energy, affordance, focus, active state |
| `grid-template-rows` or FLIP transforms | expand/reflow without animating `height` directly |

Hard rule: **avoid casually animating `width`, `height`, `top`, `left`, margins**; keep expensive effects bounded; verify smoothness in-browser. (See engineering-and-performance.md.)

---

## 8. Gestures

| Rule | Value / code |
| --- | --- |
| Dismiss on velocity, not just distance | `velocity = Math.abs(swipeAmount) / timeTaken;` if `>= SWIPE_THRESHOLD || velocity > 0.11` → dismiss |
| Damping past a boundary | the more they drag past the limit, the less it moves (real things slow before stopping) |
| Over-drag with friction | allow it with increasing friction, never a hard invisible wall |
| Pointer capture | once dragging starts, capture all pointer events so the drag continues outside element bounds |
| Multi-touch protection | `function onPress() { if (isDragging) return; /* start drag */ }` — ignore later touches |

```js
const timeTaken = new Date().getTime() - dragStartTime.current.getTime();
const velocity = Math.abs(swipeAmount) / timeTaken;
if (Math.abs(swipeAmount) >= SWIPE_THRESHOLD || velocity > 0.11) { dismiss(); }
```

**Hint at invisible gestures and always provide a visible fallback.** Swipe-to-delete is undiscoverable: partially reveal the action peeking from the edge, add first-use coach marks, and keep a menu "Delete". Never gesture-only.

---

## 9. Scroll & GSAP patterns

**Never** use `window.addEventListener('scroll', …)`, `window.scrollY` in React state, or `requestAnimationFrame` loops touching React state — every frame, no batching, jank. Use **Motion `useScroll()` / `useMotionValue` + `useTransform`**, **GSAP ScrollTrigger**, **IntersectionObserver**, or CSS `animation-timeline: scroll()`.

**CSS scroll-driven** (Chrome/Edge/Safari; Firefox flag only) — always supply a static fallback:
```css
@supports (animation-timeline: scroll()) { .hero { animation-timeline: scroll(); } }
```

**Prefer Motion `whileInView` for simple scroll-reveal staggers; reserve GSAP for actual pin/scrub:**
```jsx
initial={{opacity:0, y:24}} whileInView={{opacity:1, y:0}}
viewport={{once:true, amount:0.3}}
transition={{duration:0.6, delay:i*0.06, ease:[0.16,1,0.3,1]}}
```

**GSAP pinning** — use `start:'top top'` + `pin:true` so the section pins at the viewport top. `start:'top center'` / `'top 80%'` fires halfway through scroll instead of pinning (the common failure).
```js
// Sticky-stack
ScrollTrigger.create({ trigger: card, start:'top top', endTrigger: lastCard, end:'top top', pin:true, pinSpacing:false });
// Horizontal-pan
gsap.to(track, { x:-distance, ease:'none', scrollTrigger:{ trigger:wrap, start:'top top', end:()=>`+=${distance}`, pin:true, scrub:1, invalidateOnRefresh:true } });
```

**Use Motion `layout`/`layoutId` only for visible state changes** (reordering lists, expanding modals, shared elements between routes) — wrapping static content "for safety" costs measurement work every frame. For `staggerChildren`, parent (variants) and children must share the same Client Component tree.

**View Transitions API** (same-doc all browsers; cross-doc no Firefox) and **`@property`** (animate gradients/colors CSS can't normally interpolate) are the cinematic-morphing tools. See **overdrive** territory in the source skills; gate everything behind progressive enhancement.

**Overdrive verification — five tests before shipping any ambitious effect:**

| Test | Question |
| --- | --- |
| **Wow** | Show someone cold — do they actually react? |
| **Removal** | Take it away — is the page diminished, or did nobody notice? |
| **Device** | Phone, tablet, low-end hardware — still smooth? |
| **Accessibility** | Reduced motion on — still beautiful? |
| **Context** | Right for THIS brand and audience? |

"Extraordinary" means something different per surface: visual/marketing = sensory impact; functional UI = how it *feels* (a dialog morphing from its trigger, 100k rows scrolling at 60fps); performance-critical = invisible but felt — it never hesitates. A particle system on a settings page is embarrassing; a settings page with instant optimistic saves and animated state transitions is also extraordinary.

**Marquee: max one per page.** Two or more reads as lazy filler. Pick the one section where it serves the content.

---

## 10. Stagger

Sibling stagger is legitimate for cards-in-a-grid or list-items-appearing. **Whole-section fade-on-scroll is NOT a list** and is the saturated AI default — the tell is the uniform reflex (one identical entrance on every section), not motion itself.

- Keep delays **30–80ms between items**.
- Cap total time: **10 items × 50ms = 500ms**. Beyond that, reduce per-item delay or cap the staggered count.
- Stagger is decorative — never block interaction while it plays.

```css
.item { opacity: 0; transform: translateY(8px); animation: fadeIn 300ms ease-out forwards; }
.item { animation-delay: calc(var(--i, 0) * 50ms); }   /* set style="--i: 0", "--i: 1", … */
@keyframes fadeIn { to { opacity: 1; transform: translateY(0); } }
```

Minimalist register: `animation-delay: calc(var(--index) * 80ms)`; Stitch/perpetual register: `calc(var(--index) * 100ms)`. The opacity + height combination for list enter/exit has **no formula** — tune by trial and error until it feels right.

**Hero moment: one signature entrance, once** — not on every visit, not on every section. "Bolder" is never scroll-fade-rise on every section.

---

## 11. Perceived performance

Perception of speed matters as much as actual speed.

- **The 80ms threshold:** anything under ~80ms feels instant (brains buffer sensory input that long). Target it for micro-interactions.
- **`ease-out` at 200ms feels faster than `ease-in` at 200ms** — the user sees immediate movement.
- **Fast-spinning spinner** makes loading feel faster at the same load time. **Instant tooltips after the first** make the toolbar feel faster.
- **Preemptive start** (begin transitions while loading) and **early completion** (progressive images, streaming HTML, skeleton fade-ins).
- **Optimistic UI** for low-stakes actions (likes, follows); **never** for payments or destructive actions — show success immediately, roll back on failure.
- **Skeleton screens > spinners** — match the layout shape; they preview content and feel faster.
- **Ease-in makes tasks feel shorter** (peak-end effect weights final moments); ease-out feels satisfying for entrances. Too-fast responses can *decrease* perceived value for complex ops — a brief delay signals "real work."

---

## Reveal-animation trap

Reveal animations must **enhance an already-visible default**. Don't gate content visibility on a class-triggered transition: transitions pause on hidden tabs and headless renderers, so the section ships blank. Render visible, then animate the enhancement.

## Reduced motion (non-negotiable)

Every animated feature needs a `@media (prefers-reduced-motion: reduce)` alternative — typically crossfade or instant. Reduced motion means fewer and gentler animations (keep opacity/color that aids comprehension; remove movement/position), not necessarily zero.

```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```
In Motion, wrap with `useReducedMotion()` and degrade to static. Infinite loops, parallax, scroll-hijack, and magnetic physics MUST collapse to static/instant.

## Eight interaction states & delight

Design all eight states; hover and focus are different (keyboard users never see hover): **Default, Hover** (`@media (hover: hover) and (pointer: fine)`), **Focus** (`:focus-visible`, visible ring, never `outline:none` without replacement), **Active, Disabled, Loading, Error, Success**. Validate forms on blur, errors below fields. Prefer **Undo over confirmation dialogs** — the mechanics: remove from the UI immediately, show an undo toast, perform the actual delete only when the toast expires. Reserve confirmations for irreversible (account deletion), high-cost, or batch operations — and label confirm buttons with named actions ("Delete project" / "Keep project"), never Yes/No. Full focus/form/loading engineering lives in engineering-and-performance.md (Accessibility, Core Web Vitals & Loading).

**Delight amplifies, never blocks:** keep delight moments **< 1 second**, skippable, never delaying core functionality; **vary responses** (not the same animation every time); gate sound behind system settings + a mute option, never on every interaction.
