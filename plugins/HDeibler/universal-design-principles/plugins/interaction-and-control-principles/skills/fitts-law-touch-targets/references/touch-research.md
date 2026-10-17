# Touch targets: research and platform notes

A reference complementing `fitts-law-touch-targets` with the empirical research on touch input and platform-specific guidance.

## Empirical findings

- **Parhi, P., Karlson, A. K., Bederson, B. B.** (2006). "Target size study for one-handed thumb use on small touchscreen devices." *MobileHCI*. Found that error rates rise sharply below ~9.6mm targets for thumb input.
- **Henze, N., Rukzio, E., Boll, S.** (2011). "100,000,000 taps: Analysis and improvement of touch performance in the large." Large-scale game data analysis confirming Fitts's Law applies to touch with target-size minimums around 9–11mm.
- **Lee, S. & Zhai, S.** (2009). "The performance of touch screen soft buttons." *CHI*. Showed performance degrades meaningfully below 10mm touch-target widths.

The convergent finding: ~10mm physical target ≈ ~44 CSS pixels at typical mobile pixel density. Apple's 44pt and Material's 48dp recommendations both round to this.

## Platform target-size standards

| Platform | Recommended minimum | Notes |
|---|---|---|
| **Apple HIG (iOS)** | 44×44 pt | Used since iOS launch; rarely violated |
| **Material Design (Android)** | 48×48 dp | Slightly larger to accommodate variable Android device density |
| **Microsoft (Windows touch)** | 40×40 px | Slightly smaller; documented in Windows touch guidance |
| **WCAG 2.5.5 (AAA)** | 44×44 CSS px | Strictest accessibility level |
| **WCAG 2.5.8 (AA, 2.2)** | 24×24 CSS px (with adequate spacing) | Minimum accessibility |

The practical guideline: 44×44 CSS pixels is the safe minimum across platforms and accessibility levels. Don't go smaller without specific reason.

## Thumb-reach research

Steven Hoober's research (UX Matters, 2013, 2017) on how users actually hold phones found:

- **49%** of users hold their phone one-handed.
- **36%** cradle the phone in two hands but operate primarily with one thumb.
- **15%** use two thumbs simultaneously.

The implication: most-mode-of-use is thumb-on-the-same-hand-as-grip. Designs that require both hands or that place primary actions out of thumb reach lose usability for the dominant mode.

Hoober's reachability map shows the bottom 60% of a typical phone screen is "easy" for thumb; the top corners are "hard." Bottom navigation and FAB placement at bottom-right exploit this directly.

## Touchscreen physics

Why touch is different from mouse:

- **Contact area, not point.** A finger contact is ~10–15mm wide at typical pressure; the OS converts this to a single touch point, but underlying contact uncertainty persists.
- **Occlusion.** Once the finger touches, it covers the target. Visual feedback can't appear *under* the finger; it must radiate beyond (ripple effects, glow).
- **No hover.** Touch has no mouse-over equivalent. UI patterns relying on hover (tooltips, hover-revealed actions) must have touch alternatives.
- **Sticky / sweaty / cold fingers** all degrade touch accuracy. Outdoor / glove use (winter, industrial) further degrades.

These physics imply the target-size minimums; designs that ignore them work in lab tests and fail in the rain.

## Cross-domain examples

### ATM design

ATMs have used large physical buttons (~25mm) for decades because the user might be wearing gloves, in poor lighting, in a hurry. Touchscreen ATMs maintain large targets for the same reasons.

### Industrial controls

Manufacturing floor touchscreen interfaces (HMI panels) typically use 60×60mm minimum targets — operators wear gloves, work in dusty/wet environments, and must hit targets reliably.

### Voting machines

Voting machine UI explicitly uses very large targets (often 80mm+) because the user population includes elderly voters, people in unfamiliar environments, and users who must vote correctly without practice.

### In-vehicle infotainment

Car dashboard touch targets are larger than phone targets because:

- Vehicle motion makes precise touch harder.
- Glancing-while-driving means the user sees the target only briefly.
- Errors carry safety risk.

Tesla's all-touchscreen approach has been criticized in part for inadequate target sizes for some controls.

## Resources

- **Apple Human Interface Guidelines** (developer.apple.com/design) — comprehensive touch guidance.
- **Material Design** (material.io) — Android-perspective touch guidance.
- **Hoober, S.** "How Do Users Really Hold Mobile Devices?" — UXMatters articles.
- **WCAG 2.5.5 and 2.5.8** — accessibility minimums.

## Closing

Touch targets are one of the few design decisions where the right answer is well-known and rarely controversial: at least 44×44 CSS pixels, 8+ pixels of spacing between, anchored to thumb-reachable zones. Designs that violate these defaults usually do so by accident; deliberately violating requires a strong specific reason.
