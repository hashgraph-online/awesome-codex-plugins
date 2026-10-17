---
name: fitts-law
description: 'Use this skill whenever the question involves how easy it is to *hit* an interactive target — buttons, links, form controls, drag handles, scrollbars, mobile tap targets, anything the user must move a pointer or finger to. Trigger when sizing buttons, designing toolbars, picking a hit-area for icon buttons, designing for touch screens, debugging "users keep mis-clicking," or arguing about button density vs. usability. Trigger when the user mentions touch targets, target size, "fat fingers," pointer accuracy, edge gestures, or accessibility around motor impairments. Routes to sub-aspect skills for touch targets, screen edges, and pointer acceleration.'
---

# Fitts's Law

Fitts's Law is the foundational quantitative model of how long it takes to acquire (point to) a target with a directed movement. The classic formulation:

```
T = a + b · log₂(D / W + 1)
```

Where T is movement time, D is the distance from the starting position to the target, W is the target's width along the axis of motion, and a, b are device-and-context constants. The logarithmic relationship is the core insight: doubling the size of a target reduces movement time by a constant amount; halving the distance to a target also reduces it by a constant amount; targets at the edges of the screen are effectively infinite in one dimension because the cursor stops there.

## Definition (in our own words)

The time to move a cursor or finger to a target is determined by two things: how *far* the target is from where you start, and how *big* the target is. Big nearby targets are fastest; small distant targets are slowest. Edges and corners of the screen are exceptional: the cursor (or finger) cannot overshoot, so they behave as effectively infinite-sized targets along that one axis.

## Origins and research lineage

- **Fitts (1954)** "The information capacity of the human motor system in controlling the amplitude of movement" — the original paper, derived from a peg-in-hole task with varying target sizes and distances.
- **Card, Moran & Newell (1983)** incorporated Fitts's Law into the early HCI canon as one of the foundational "pointer mechanics" laws.
- **MacKenzie (1992)** refined the formulation to better handle on-screen pointer tasks (the form above is "Shannon's formulation," credited to MacKenzie).
- **Mobile / touch research** (Henze, Bailly, and many others) has extended Fitts's Law to touch-screen interaction, where the "pointer" is a finger with a wider effective contact area than a cursor.

The law has held up across input modalities (mouse, trackpad, touch, stylus, eye-tracking) for over half a century. The constants change; the relationship doesn't.

## Why Fitts's Law matters

Every clickable element imposes a Fitts's Law cost — a small one for big nearby buttons, a large one for tiny distant ones. On a single screen the cost is barely perceptible. Multiplied across a workflow with many clicks, the costs compound.

Worse, small targets aren't just slower; they're *less reliable*. The user may overshoot, undershoot, or miss entirely — leading to misclicks that cost a redo or, worse, an unintended action.

For touch interfaces, Fitts's Law is also an accessibility issue. Users with motor impairments, tremor, or one-handed use cases pay a much higher cost on small targets than typical users do.

## When to apply

- **Sizing buttons and icon buttons.** Especially in dense UI where the temptation is to shrink them.
- **Designing for touch.** Mobile, tablet, kiosk, and any screen the user touches.
- **Designing toolbars and menus.** Distance between current cursor and likely target matters.
- **Designing screen-edge interactions.** Edge gestures, edge-aligned navigation, full-bleed CTAs.
- **Designing for accessibility.** Larger targets benefit users with motor or vision impairments and don't penalize anyone.
- **Reviewing why users misclick something.** Almost always a Fitts's Law diagnosis.

## When NOT to apply (or when to be careful)

- **Very dense expert UIs.** Power users on familiar tools tolerate (and sometimes prefer) compact targets — they're using muscle memory, not search-and-acquire. A code editor's 16px tab close button is fine for daily users; not fine for new ones.
- **When the law conflicts with safety.** Destructive actions can deliberately use *smaller* or *farther* targets to make accidental activation harder. The Fitts's Law cost is *intentional*.
- **When the law conflicts with hierarchy.** A primary action is bigger because it's primary, not because Fitts's Law mathematically demands it. Hierarchy and Fitts's Law usually agree (primary = larger = faster), but when they don't, hierarchy is often the right tiebreaker.

## Practical sizes

The most common Fitts's Law decisions are about minimum target size. Standards converge on:

| Context | Minimum target size | Source / convention |
|---|---|---|
| Touch (general) | 44×44 px | Apple HIG; matches average fingertip contact |
| Touch (Material) | 48×48 dp | Google Material Design |
| Touch (WCAG 2.5.5 Level AAA) | 44×44 CSS px | WCAG Success Criterion 2.5.5 |
| Touch (WCAG 2.5.8 Level AA, 2.2) | 24×24 CSS px (with spacing) | WCAG Success Criterion 2.5.8 |
| Mouse-pointer UI | 32×32 px (button), 24×24 (icon button with hover-friendly hit area) | Common in dense desktop apps |
| Trackpad / fine pointer | 16×16 px is feasible but error-prone | Reserve for power-user tools |

The numbers are *minimums*; bigger is usually better when space allows.

## Distance: the other half of the equation

Target size gets most of the attention, but distance matters equally. Two strategies:

### Place high-frequency targets close to the user's natural starting position

After the user clicks "Add row," their cursor is wherever they clicked. The next thing they're likely to do (label the new row) should be close by. Don't make them traverse the screen.

### Use proximity for related actions

If a user just clicked a row to select it, the contextual actions (edit, delete, share) should appear *near* that row — in a row-action toolbar or popover — not in a sidebar or a top toolbar 600px away. Distance kills speed.

### Use anchored controls for sustained interaction

A floating action button (FAB) is anchored — distance from any starting cursor position is roughly constant. For mobile in particular, this is a Fitts's Law win.

## Edges and corners: the magic real estate

Because the pointer cannot move past the screen edge, edges and corners act as effectively-infinite targets along one axis. This is why Mac's menu bar lives at the top edge (cursor can fly up without overshooting) and why Windows's Start button lives at the corner (zero precision required to hit).

In web UIs:

- **Sticky headers** at the top edge: navigation links there are easier to hit than mid-page.
- **Fixed bottom toolbars** on mobile: thumb travels naturally to the bottom; the bottom edge stops it.
- **Side sheets** that slide in from the right: their edge is anchored to the screen edge, easier to grab than mid-screen panels.

A common modern web mistake: pages with no bleed, where every interactive element has 24px+ of margin. The screen edge advantage is forfeited.

## Touch-specific notes

Touch screens present a few twists Fitts's Law accounts for:

- **The finger has a wide contact area.** ~10–15mm at typical pressure, much larger than a cursor. This is why touch targets need to be larger than mouse targets — but also why touch is faster than mouse for nearby targets (no fine positioning required).
- **The finger occludes its target.** Once you press, you can't see what's under your finger. Targets need to confirm hit visually (state change after touch).
- **Thumb reach varies.** On a phone held one-handed, the thumb easily reaches the lower portion of the screen but strains for the top corners. Place primary actions in thumb-reach zones (lower 2/3 of the screen).
- **Edge gestures compete with edge buttons.** Modern phones use edge swipes for system gestures (back, app switcher); a button right at the edge may be triggered by accident. A small inset (8–12px from the absolute edge) keeps Fitts's edge advantage without conflicting with system gestures.

## Worked examples

### Example 1: an icon-only button

A common case where Fitts's Law gets violated.

**Anti-pattern:**

```html
<button style="
  width: 16px; height: 16px;
  padding: 0; border: 0;
  background: transparent;
">
  <CloseIcon style="width: 16px; height: 16px;" />
</button>
```

A 16×16 hit area is hard to hit even with a mouse and impossible reliably with touch.

**Right:**

```html
<button aria-label="Close" style="
  width: 36px; height: 36px;
  padding: 0; border: 0; border-radius: 0.375rem;
  background: transparent;
  display: grid; place-items: center;
">
  <CloseIcon style="width: 16px; height: 16px;" />
</button>
```

The icon stays 16px (visual weight); the button is 36×36 (easy hit). On touch surfaces, push to 44×44.

### Example 2: a toolbar of icon buttons

```html
<div style="display: flex; gap: 0.25rem;">
  <button aria-label="Bold" style="width: 32px; height: 32px;"><BoldIcon /></button>
  <button aria-label="Italic" style="width: 32px; height: 32px;"><ItalicIcon /></button>
  <button aria-label="Underline" style="width: 32px; height: 32px;"><UnderlineIcon /></button>
</div>
```

Each button has a 32×32 hit area. The 4px gap is small enough to keep buttons close (low D in Fitts's formula), but large enough to prevent accidental neighbor-clicks.

### Example 3: a primary action below the form

```html
<form style="display: grid; gap: 1rem;">
  <input />
  <input />
  <input />
  <button class="primary" style="
    height: 44px;
    padding: 0 1.5rem;
    align-self: end;
  ">
    Submit
  </button>
</form>
```

The Submit button is 44px tall (touch-friendly), aligned to the right edge of the form (predictable position users will learn). Distance from the last input is small — the user's cursor is already nearby.

### Example 4: mobile bottom navigation

```html
<nav style="
  position: fixed; bottom: 0; left: 0; right: 0;
  display: grid; grid-template-columns: repeat(5, 1fr);
  height: calc(56px + env(safe-area-inset-bottom));
  padding-bottom: env(safe-area-inset-bottom);
">
  <button style="display: grid; gap: 2px; place-items: center;">
    <HomeIcon />
    <span style="font-size: 10px;">Home</span>
  </button>
  <!-- … 4 more items … -->
</nav>
```

Bottom-anchored: thumb reaches naturally and the screen edge stops travel. Each item is ~76px wide × 56px tall — generous targets. Five-item maximum to keep per-item width above ~72px.

### Example 5: edge-aligned destructive button (intentional Fitts's penalty)

```html
<!-- The save button is large, central, and easy. The destructive button is
     small and visually demoted. The user must aim deliberately. -->
<div style="display: flex; justify-content: space-between; align-items: center;">
  <button class="text-button danger" style="font-size: 0.875rem;">
    Delete account
  </button>
  <button class="primary" style="height: 44px; padding: 0 2rem;">
    Save changes
  </button>
</div>
```

The destructive action's *small target size* and *visual demotion* are deliberate Fitts's Law penalties. They're features.

## Anti-patterns

- **The microscopic close button.** A 12×12 X in the corner of a popover. Hard to hit with a mouse, impossible with touch.
- **The dense menu.** A right-click menu with 4px row heights. Fine when the user means to pick the third item; murder when they want the second-to-last.
- **The scattered actions.** Related actions placed at opposite ends of a screen so the user must traverse for each one.
- **The "we have so much screen real estate" trap.** Spreading buttons across the page so the eye has to travel. Cluster related actions.
- **The ignored edge.** An app with 24px margins on every side, forfeiting the edge-as-target benefit. Modern web apps often suffer this.
- **The misclick-friendly destructive.** Putting "Delete" right next to "Edit" with the same size and styling. Fitts's Law makes the misclick easy; the consequence is severe. Either widen the gap, demote the destructive visually, or add confirmation.

## Heuristics

1. **The 44px rule.** On any touch surface, every interactive element should occupy at least 44×44 CSS pixels of hit area, even if the visual element inside is smaller.
2. **The traverse audit.** Pick a common task. Trace the cursor path through it. If the cursor crosses the screen multiple times, restructure to reduce traversal.
3. **The edge audit.** Are any of your high-frequency actions at screen edges? If not, you may be leaving Fitts's Law performance on the table.
4. **The misclick log.** If your analytics or support shows users frequently undoing or correcting an action, the Fitts's setup of that action is probably wrong (too small, too close to a different action, too far from the natural cursor position).

## Related principles

- **`affordance`** — Fitts's Law sets the *size* a target needs; affordance sets whether the user knows it's a target at all.
- **`defensible-space`** — separating destructive controls from common ones is an *intentional* Fitts's Law penalty for safety.
- **`mapping`** — placing controls *near* the things they affect reduces Fitts's distance.
- **`visibility`** — a target you can't see has effectively infinite distance.
- **`accessibility`** (process) — Fitts's Law is fundamentally about motor accessibility; bigger and edge-aligned targets help everyone.

## Sub-aspect skills

- **`fitts-law-touch-targets`** — applying the law to touchscreen interfaces specifically.
- **`fitts-law-screen-edges`** — exploiting (and respecting) the screen-edge advantage.
- **`fitts-law-pointer-acceleration`** — how cursor speed and acceleration interact with target size, especially on trackpad and mouse.
