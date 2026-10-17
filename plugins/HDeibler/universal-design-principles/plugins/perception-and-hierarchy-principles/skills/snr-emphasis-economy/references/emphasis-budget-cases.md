# Emphasis economy: case studies and budgets

A reference complementing `snr-emphasis-economy` with concrete budget examples and case studies of well-spent and ill-spent emphasis.

## Sample emphasis budgets per surface

The numbers below are illustrative defaults; tune to your product. Each "instance" is a single use of the cue on the screen at a glance.

### A working application screen (settings, dashboard, inbox)

```
Brand color (filled buttons / accents)        1 instance
Brand color (links, icons, subtle accents)   ≤ 5 instances
Destructive (red) color                       0–1 instances
Success (green) color                         0–2 instances
Warning (amber) color                         0–1 instances
Bold text (display/heading roles only)        ≤ 5 instances
"New" / "Beta" badges                         ≤ 1 active at a time
Animated motion (looping)                      0
Animated motion (state-change one-shot)        per-event
```

### A marketing landing page

```
Brand color (hero CTA)                        1 dominant instance
Brand color (other surfaces, gradients)      ≤ 3 instances
Saturated photography or illustration          1 hero, modest below
Bold text                                      headlines + CTAs
Animation (entrance / scroll-reveal)           1–2 events per fold
```

### A pricing page

```
Highlighted "Recommended" tier                 1
Brand color CTA on each tier                   3 (one per tier, but only one filled)
"Save N%" badges                              ≤ 1 (annual toggle)
```

### A checkout / payment flow

```
Primary action (Pay)                           1 dominant per step
Secondary actions (back, skip)                 1–2 ghost-style
Trust signals (lock icon, brand badges)        ≤ 3
Error / validation                             only when active, then dominant
```

The pattern: as the page becomes more *task-focused*, the emphasis budget shrinks. Marketing tolerates more; payments tolerate less.

## Case study: emphasis inflation

A common pattern: a product launches with disciplined emphasis. Over years, every team adds a "small thing":

- Marketing wants a "New!" callout for the new feature.
- Sales wants a banner for the upcoming webinar.
- Customer success wants a "complete your profile" prompt.
- Product wants to highlight the analytics tab.
- Engineering wants a "system status" indicator.

Each addition individually justified, none audited against the others. Within 18 months: every screen has 3–5 active highlights, the user tunes them all out, and the next "important callout" needs to be even bigger to register.

The fix is institutional: *one team owns the highlight budget across all screens*. Adding a highlight requires retiring another. Without this, inflation is inevitable.

## Case study: red-color budget

A SaaS product had:
- Red as brand primary (all CTAs).
- Red for "delete" buttons.
- Red for error states.
- Red for "overdue" status.
- Red highlight color for new-feature callouts.

Result: nothing red registered as urgent. The error state in particular failed user testing — users weren't reading the validation message because the page was already "covered in red."

The fix: re-platform the brand to a non-red primary (royal blue), reserve red exclusively for destructive and error states. Validation suddenly worked again.

## Cross-domain examples

### Newspaper headlines

A traditional newspaper front page has *one* dominant headline. Breaking news might warrant a cross-page banner (rare). The next-tier headline is visibly smaller. The eye reads the dominant first, the secondary second. Multiple front-page leads reads as a chaotic news day, not a normal one.

### Theatrical lighting

A stage with everything brightly lit has no focal point. Lighting designers reserve full intensity for the moment that matters; rest of the stage sits in fill light. The audience's eye follows the bright; multiple equally-bright actors fight.

### Restaurant menu design

A "Chef's Recommendation" or "Most popular" mark on a single dish exploits the same principle. Menus with too many "starred" items degrade the signal of any one star.

## Heuristics for trimming

When auditing emphasis on a busy surface:

1. **List every emphasized element** (every colored, bold, badged, animated element).
2. **Rank by genuine importance** to the user's task.
3. **Demote everything below rank #3.**

Demotion means: lose the color emphasis (back to neutral), lose the bold (back to regular weight), lose the badge (defer to a less prominent surface).

Resistance is normal; stakeholders will object that "their" element is important. The compromise: a rotating spotlight (e.g., a "feature of the week" slot) where one promotional surface holds the emphasis, rotating across teams.

## Resources

- **Material Design Color** — material.io. Documents how Material's "primary color" is supposed to be used sparingly.
- **Nielsen Norman Group** — multiple articles on banner blindness and the emphasis-inflation problem.
- **Refactoring UI** — chapters on color and emphasis discipline.
