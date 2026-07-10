# Avoiding AI Slop

The bar is two tests, one per register. On **brand surfaces**: **if someone can look at the interface and say "AI made that" without hesitation, it has failed.** Average is no longer findable. AI landing pages have flooded the internet, so restraint without intent now reads as mediocre, not refined. On **product surfaces** familiarity is a feature, so the test flips: would a user fluent in Linear, Figma, Notion, or Stripe sit down and trust this, or pause at every subtly-off component? Product slop fails through strangeness without purpose, not through flatness. This file is the cross-register ban-list and the output-completeness contract. Aesthetic-specific palettes, fonts, and shadow systems live in aesthetic-systems.md; the neutral color/typography/layout baseline lives in design-principles.md; motion and reveal tells live in motion-and-interaction.md; loading states and real-data hardening live in engineering-and-performance.md.

Run two checks before you commit to a direction:

- **First-order:** if someone could guess the theme + palette from the *category alone* ("fintech → navy and gold", "AI tool → SaaS cream"), you reached for the first training-data reflex. Rework.
- **Second-order:** if someone could guess the aesthetic family from *category-plus-anti-reference* ("AI workflow tool that's not SaaS-cream → editorial-typographic"), you hit the trap one tier deeper. Rework until neither answer is obvious.

---

## The Tells: Absolute Ban-List (any register)

These are hard bans. If you are about to write one, rewrite the element with different structure. Match-and-refuse.

### Color
- **Purple/blue "AI gradient":** the single most recognizable fingerprint. Replace with a neutral base + one considered accent.
- **`oklch(97% 0.01 60)` and its neighbors** (warm cream/sand/beige body bg). The whole warm-neutral band (OKLCH L 0.84-0.97, C < 0.06, hue 40-100) reads as cream/paper. Token names `--paper`, `--cream`, `--sand`, `--bone`, `--linen`, `--parchment`, `--ivory` are tells. Tint toward the brand hue or stay neutral; never default-tint "for warmth." (see design-principles.md, aesthetic-systems.md.)
- **Pure `#000000` / pure `#ffffff`.** Use off-black (`#0a0a0a`, `#121212`, zinc-950) and true off-white.
- **The premium-consumer reflex palette** (beige + brass + oxblood + espresso). Banned bg `#f5f1ea #f7f5f1 #fbf8f1 #efeae0 #ece6db #faf7f1 #e8dfcb`; banned accents `#b08947 #b6553a #9a2436 #9c6e2a #bc7c3a #7d5621`; banned text `#1a1714 #1a1814 #1b1814`. Rotate alternatives, no repeat in a row.
- **Gradient text** (`background-clip: text` + gradient bg) on large headers. **Neon / outer glows** by default. **Oversaturated accents** (keep saturation < 80%). **Generic black `box-shadow`** (tint shadows to the bg hue).
- **Dark-glow:** dark background + colored `box-shadow` glow as the default "cool" look. The dark-mode variant of the neon ban; if dark surfaces need depth, use surface lightness, not glow.
- **The AI hue bands:** purple/violet at hue **260-310**, and cyan at hue **160-200** on dark backgrounds, applied to headings or large text. These are the checkable numbers behind the purple/blue reflex.

### Layout
- **Three identical feature cards** in a row: the most generic AI layout. Use 2-column zig-zag, asymmetric grid, scroll-pinned, horizontal-scroll, or masonry.
- **Centered hero over a dark mesh/blob** as the default. **Evenly-spaced symmetric everything.**
- **Identical card grids** (same-sized icon + heading + text, repeated). **Cards nested inside cards.** Use spacing and dividers for hierarchy. Cards earn their elevation; the border + shadow + white-bg card is a default, not a decision.
- **The hero-metric template** (big number + small label + supporting stats + gradient accent) when there is no real data behind it.
- **Side-stripe borders:** `border-left`/`border-right` > 1px as a colored accent on cards, list rows, callouts, alerts. Use a full 1px hairline perimeter, a 4-8% surface tint, or a leading glyph instead. On a *rounded* card a thick one-sided accent (≥2px while the other sides are hairlines) clashes with the corners; ≥3px fails unconditionally.
- **Ghost-card:** `border: 1px solid` + `box-shadow` with blur ≥16px on the same element. Commit to one: a defined edge, OR a soft elevation at ≤8px blur. Never both as decoration.
- **Over-rounding:** border-radius ≥32px (and 24/28px) on cards, sections, or inputs is a generated-UI tell. Cards top out at 12-16px by default; full-pill stays at tag/button scale. (Soft systems deliberately override per the precedence rule.)
- **Icon-tile-stack:** a 32-128px rounded-square icon container stacked directly above a heading. The universal AI feature-card template; every generator outputs this exact shape. Put the icon side-by-side with the heading, or in flow without its own container.
- **`border-t` + `border-b` on every row** of a long list/spec table. **Filled-track progress bars** as comparison visuals (drop the `bg-zinc-200` track).
- **Default left sidebar** on every dashboard. **Box-in-box-in-box** nesting. (see design-principles.md.)

### Typography
- **Inter / Roboto / Open Sans / Arial / system default** when personality matters. The most modern move is not the font everyone else uses. Note: Geist is approaching Inter-level saturation; it stays a fine deliberate product-register choice, but it is no longer a differentiator on its own.
- **Reflex-reject display serifs** as a default: Fraunces, Newsreader, Lora, Crimson, Playfair Display, Cormorant, Instrument Serif, DM Serif. Also reflex sans: DM Sans, Outfit, Plus Jakarta Sans, Space Grotesk, Syne. Identity-preservation wins when an existing brand already committed to a font.
- **The editorial-typographic lane on a non-editorial brief:** display serif (often italic) + small mono labels + ruled separators + monochromatic restraint. Use only when the brief literally is a magazine/terminal/signage system.
- **Italic-serif display hero:** an oversized italic serif (Fraunces, Recoleta, Playfair) as the primary hero headline. Reads as taste in isolation, but it is the universal AI-startup hero. Set it roman or change face; italic display earns its place only on genuinely editorial registers.
- **The long-sentence display H1:** the oversized-headline tell is a *long, full-sentence* headline at display size dominating the viewport. A punchy 1-2-word headline at the same size is fine; set long headlines smaller or tighten the copy.
- **`<br>`-broken italic headlines** ("for thirty\<br>*years.*"). **Vertical rotated text.** **Gradient headline** as a shortcut for "premium." **Lazy all-caps everywhere.** (see design-principles.md, aesthetic-systems.md.)

### Components & micro-UI
- **Tiny uppercase tracked eyebrow above every section:** the #1 violated rule (appears on 55-95% of generations). Max 1 eyebrow per 3 sections, hero counts as 1; if section A has one, the next 2 cannot. Count `uppercase tracking` instances mechanically before shipping; if count > ceil(sectionCount / 3), it fails. The per-hero detector shape: text ≤14px with letter-spacing ≥1.6px uppercase (or weight ≥700 in the accent color) sitting directly above an h1 or an h2 ≥48px, including as a pill chip. Best alternative: drop it.
- **Hand-drawn / sketchy SVG illustrations:** `loose-sketch`/`doodle`/`wavy` class names, `feTurbulence`/`feDisplacementMap` "paper grain", crude 5-30-path scenes depicting a tangible subject. Reads amateurish, not whimsical; if the scene can't be rendered with real assets, ship no illustration.
- **`repeating-linear-gradient` stripe backgrounds** as surface decoration (diagonal stripes in `body::before` or behind sections).
- **Numbered section markers** as scaffolding: `00 / INDEX`, `001 · Capabilities`, `06 · how it works`, `SECTION 01`, `QUESTION 05`, `01 / 4` pagination, "Stage 1 / Step 1 / Phase 01." The step content is the label ("Install", "Configure", "Ship").
- **Split-header** (big left headline + small floating right explainer paragraph). Stack headline on top, body below at max 65ch, unless the right column carries a real visual/interactive element.
- **Emoji icons** in code, markup, visible text, or alt text. Replace with icon-library glyphs (Phosphor, Heroicons, Tabler). Allow only when the user explicitly asks for a playful/chat/social vibe, and then sparingly.
- **Lucide/Feather as the exclusive set.** **Cliché icon metaphors** (rocket = Launch, shield = Security → bolt, fingerprint, vault).
- **Pill "New"/"Beta" badges**, **accordion FAQ**, **3-card carousel testimonials with dots**, **modals for simple actions**, **sun/moon dark-mode toggle**, **filled + ghost button pair** as the only CTA shape. All generic defaults; reach for the alternative listed in design-principles.md.
- **Glassmorphism as default.** **Custom mouse cursors** (perf- and a11y-hostile). **Decorative colored status dots** before nav links / list rows / badges. **Middle-dot (`·`) as default separator** (max 1 per metadata line).
- **Decoration text strips** at hero bottom (`TYPE / FORM / MOTION`, `DESIGN · BUILD · SHIP`, `ESTD. 2018 · LISBON`). **Locale/time/weather strips** ("Lisbon 14:23 · 18°C"), banned for 99% of briefs. **Scroll cues** ("Scroll", "↓ scroll", animated mouse-wheel): the user is already looking at the hero.

### Fake content (the "Jane Doe" effect)

| ❌ The tell | ✅ Ship instead |
|---|---|
| Div-based fake product preview (fake task list, terminal, dashboard from `<div>` rectangles), the **#1 LLM-design Tell** | Real screenshot, generated image, real mini component, or skip the preview. Text + gradient blob is not a hero. |
| Fake version stamps: "v0.6.2-rc.1", "Build 0048", "last sync 4s ago · main" | Nothing. These are devtool fixtures, banned on marketing/landing/portfolio pages. |
| Generic names "John Doe", "Sarah Chan"; repeated avatars; SVG-egg / Lucide-user icons; identical blog dates | Locale-appropriate names, a unique asset per person, randomized dates. |
| Fake round numbers `99.99%`, `50%`, `1234567`; AI-invented specs `92%`, `4.1×`, `5.8 mm` | Organic data `47.2%`, `$99.00`, `+1 (312) 847-1928`. Specs only if sourced or labeled `<!-- mock -->`. |
| Placeholder brands "Acme", "Nexus", "SmartFlow", "Cloudly", "NovaCore"; Lorem Ipsum; plain text wordmarks on a social-proof wall | Contextual invented brand names; real draft copy; real SVG logos (`https://cdn.simpleicons.org/{slug}/ffffff`), no category labels underneath. |
| Broken Unsplash links from guessed IDs (404 → broken-image placeholder) | Verified URLs, or `https://picsum.photos/seed/{descriptive-seed}/{w}/{h}`. Image-led briefs (restaurant, hotel, magazine, product) **must** ship real imagery; a solid-color rectangle where a hero photo belongs is worse than a representative stock photo. |

### Copy
- **Em-dash (`—`) anywhere visible:** the #1 *visual* tell, zero allowance. Banned in headlines, eyebrows, pills, buttons, body, quotes, attribution, captions, alt text. Also banned: en-dash separator (`–`) and ` -- ` substitute. Use comma, colon, semicolon, period, parentheses, or ` - `. Ranges use a hyphen (`2018-2026`).
- **Buzzwords:** streamline, empower, supercharge, leverage, unleash, transform, seamless, world-class, enterprise-grade, next-generation, cutting-edge, game-changer, elevate, delve, tapestry, robust, "in the world of...". **Cliché loading copy** ("Herding pixels", "Teaching robots to dance"). **"Oops!" errors** and **exclamation-mark success** messages.
- **Performative-craftsman labels** ("Quietly trusted by", "From the field", "Field notes"). **Negation pivot** ("It's not just X, it's Y"). **Triadic everything** (every list is three). Button labels are verb + object ("Save changes" beats "OK"); link text stands alone ("View pricing plans" beats "Click here").
- **Aphoristic cadence:** 3+ sections each landing on a short rebuttal sentence ("X. No Y." / "X. Just Y." / "Not a feature. A platform."). Once is voice; the repeated pattern is the tell.
- **"Theater" framing:** dismissing something as "X theater", or staging a strawman just to correct it. Make the specific claim instead.

---

## Why It Happens (so you know what to override)

Slop is a *behavioral* default, not a memory or decoding failure. Controlled 2025 studies (GPT-4 variants, DeepSeek) found greedy-decoded truncation matched the model's highest-confidence solution and that 200-turn context degradation was minimal. So fix it with enforcement, not by re-feeding context.

| Cause | Mechanism | Override |
|---|---|---|
| **Output limits** | The model estimates a full response exceeds its ~8,000-token budget and preemptively compresses. | Chunk: outline → per-component → assembly. Pause/resume at clean breakpoints (below). |
| **RLHF / compute** | Stopping pressure is calibrated aggressively; short confident summaries are rewarded over exhaustive correct output. Safety tuning resists large codebases. | Replace weak "make it work" with explicit, verifiable completeness criteria. |
| **Training-data bias** | Tutorials, docs, forum answers, and blogs are full of `# implement here` and "similarly for the rest." The model assigns high probability to truncation tokens where complete code belongs. | Override aggressively; the tutorial pattern often beats a soft completeness instruction. |
| **Cognitive shortcuts** | On tasks it reads as straightforward, the model surface-summarizes. Even seasonal signals shift it (measurable December brevity; stating a non-winter month recovers length). | Pre-decompose every task into discrete steps; verify each requirement explicitly. |
| **Design reflex** | The first aesthetic the weights surface for a category dominates the distribution. | First-order + second-order category-reflex checks (top of file). |

---

## Output-Completeness Rules (non-negotiable)

A partial output is a broken output. Treat every task as production-critical. If the user asks for a full file, deliver the full file. If they ask for 5 components, deliver 5. If the output is 500 lines, produce all 500.

**Banned in code blocks (hard failures):**
`// ...` · `// rest of code` · `// implement here` · `// TODO` · `/* ... */` · `// similar to above` · `// continue pattern` · `// add more as needed` · bare `...` standing in for omitted code.

**Banned in prose:**
"Let me know if you want me to continue" · "I can provide more details if needed" · "for brevity" · "the rest follows the same pattern" · "similarly for the remaining" · "and so on" (replacing real content) · "I'll leave that as an exercise" · "as mentioned earlier" / "see above" (to dodge repeating necessary context).

**Banned structural shortcuts:**
A skeleton when a full implementation was requested · showing the first and last section while skipping the middle · replacing repeated logic with one example + a description · describing what code should do instead of writing it.

### Scope → Build → Cross-check
1. **Scope:** read the full request, count distinct deliverables (files, functions, sections, answers), lock that number.
2. **Build:** generate every deliverable completely. No partial drafts, no "you can extend this later."
3. **Cross-check:** re-read the original request, compare your deliverable count against the locked count, add anything missing before responding.

### When you approach the token limit
Do not compress remaining sections. Do not skip to a conclusion. Write at full quality to a clean breakpoint (end of a function, file, or section), then end with exactly:

```
[PAUSED - X of Y complete. Send "continue" to resume from: next section name]
```

On "continue", pick up exactly where you stopped. No recap, no repetition.

### Production bar for content
Ship real content with full state coverage: default, hover, focus-visible, active, disabled, loading, error, success, empty, overflow, long/short text, first-run. No placeholder copy/images, dead `#` links, fake controls, or unused scaffold at presentation. Do not replace required imagery with generic cards, bullets, emoji, fake metrics, decorative CSS panels, or filler copy. Battle-test every page with browser screenshotting and computer use before calling it done. (Real-data hardening: see engineering-and-performance.md.)

---

## Anti-Slop Checklist

Run before declaring done.

- [ ] **Category-reflex:** neither first-order nor second-order guess is obvious.
- [ ] **Color:** no purple/blue gradient (hue 260-310; cyan 160-200 on dark), no dark-glow, no cream/sand bg, no beige+brass palette, no pure `#000`/`#fff`, no gradient text on headers.
- [ ] **Layout:** no three-equal cards, no nested cards, no ghost-card (1px border + ≥16px shadow), no ≥24px card radii, no icon-tile-stack, no decorative hero metric, no side-stripe or thick one-sided accent borders, no reflexive left sidebar.
- [ ] **Type:** not Inter/Roboto/Open Sans by reflex, no reflex display serif, no italic-serif hero, no full-sentence display H1, no editorial-typographic lane on a non-editorial brief.
- [ ] **Eyebrows:** `uppercase tracking` count ≤ ceil(sectionCount / 3), no eyebrow chip glued to the hero headline. No numbered section markers, no split-header, no sketchy SVG illustrations, no stripe backgrounds, no decoration strips, no scroll cues, no locale strips.
- [ ] **Fake content:** no div fake-screenshots, no version stamps, no John Doe / Acme, no fake round numbers, no Lorem Ipsum, no broken image URLs; real imagery on image-led briefs.
- [ ] **Copy:** zero em-dashes (`—`/`–`/` -- `) anywhere visible; no buzzwords; no "Oops!"; no aphoristic rebuttal cadence (3+ sections); no "theater" framing; verb+object buttons; standalone link text.
- [ ] **No emoji** in code, markup, text, or alt (unless explicitly requested).
- [ ] **Completeness:** no banned code/prose patterns; every requested item present and finished; code blocks are runnable, not described; nothing shortened to save space.
- [ ] **Slop test:** brand surface: could a viewer say "AI made that" without doubt? Product surface: would a fluent Linear/Figma/Notion/Stripe user pause at subtly-off components? If yes, rework before shipping.
