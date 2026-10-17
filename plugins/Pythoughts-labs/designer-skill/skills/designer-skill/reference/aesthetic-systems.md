# Aesthetic Systems

A menu of five opinionated, **mutually exclusive** design languages. Pick ONE per surface and execute it whole. These systems intentionally contradict each other — Minimalist bans shadows and gradients; Soft requires them; Brutalist forbids `border-radius` entirely. **Every rule below is scoped to its own system, never universal.** A value that is law in one profile is a banned anti-pattern in another (see the [Cross-System Contradictions](#cross-system-contradictions) table).

Before anything: dark vs light is **never a default**. Write one sentence of physical scene — who uses this, where, under what ambient light, in what mood — and let it force the answer. If it doesn't, add detail until it does.

Shared motion *mechanics* (animate only `transform`/`opacity`, `IntersectionObserver` not scroll listeners, stagger formulas, blur/`backdrop-filter` perf guardrails) live in **motion-and-interaction.md**. This file carries each system's signature *feel* only.

---

## When to use which

| System | Pick it when… | Substrate | One-line tell |
|---|---|---|---|
| **Minimalist / Editorial** | Document-style workspace tools (Notion-like), editorial calm, rejecting generic SaaS | Warm white / bone | Hairline borders, off-black serif heads, no shadows |
| **Brutalist / Industrial** | Data-heavy dashboards, portfolios, sites that should feel like declassified blueprints | Newsprint **or** dead CRT | 90° corners, monospace telemetry, single hazard red |
| **Soft** | Premium consumer / health / agency / lifestyle where haptic depth signals expense | OLED black **or** warm cream **or** silver | Glass, diffused ambient shadows, nested squircles |
| **High-end / Premium (Stitch)** | SaaS/product where calibrated restraint reads "expensive and intentional" | Warm-neutral Zinc/Slate | One sub-80% accent, whisper borders, weight-driven hierarchy |
| **Brand-identity** | Brand sites, campaigns, logo/identity systems where distinctiveness IS the bar | Whatever the voice demands | Committed color, named reference, font chosen by procedure |
| **Product register** | App shells, dashboards, settings — inside-the-product surfaces where trust IS the bar | Quiet neutrals, two layers | Second neutral layer, accent = action only, familiar affordances |

> Minimalist, Brutalist, Soft, and Stitch are **product/marketing build systems**. Brand-identity and Product are fluid *strategy* registers — no fixed hexes; Brand-identity commits per project, Product overlays whichever build system the app runs on.

---

## 1. Minimalist / Editorial

**Signature traits.** Ultra-flat "document-style" surfaces, extreme typographic contrast, asymmetrical bento with hairline borders, massive macro-whitespace, color as a scarce resource.

**Palette (warm monochrome + spot pastels).**
| Role | Value |
|---|---|
| Canvas | `#FFFFFF` or warm bone `#F7F6F3` / `#FBFBFA` |
| Card surface | `#FFFFFF` or `#F9F9F8` |
| Border / divider | `#EAEAEA` or `rgba(0,0,0,0.06)` |
| Body text | never `#000000` — use `#111111` or `#2F3437`, `line-height: 1.6` |
| Secondary text | muted gray `#787774` |
| Spot pastels (tags/inline-code only) | Pale Red `#FDEBEC`/text `#9F2F2D` · Pale Blue `#E1F3FE`/`#1F6C9F` · Pale Green `#EDF3EC`/`#346538` · Pale Yellow `#FBF3DB`/`#956400` |

**Typography (3-part stack).** Sans (body/UI): `'SF Pro Display','Geist Sans','Helvetica Neue','Switzer',sans-serif`. Editorial serif (hero/quotes): `'Lyon Text','Newsreader','Playfair Display','Instrument Serif',serif`, `letter-spacing -0.02em` to `-0.04em`, `line-height 1.1`. Mono (code/keys/meta): `'Geist Mono','SF Mono','JetBrains Mono',monospace`.

**Spacing.** Section padding `py-24`/`py-32`; constrain text to `max-w-4xl`/`max-w-5xl`; card internal padding `24px–40px`; card radius `8px` or `12px` max, buttons `4px–6px`.

**Motion feel.** Invisible, quiet. Scroll entry: `translateY(12px)` + `opacity 0` → resolve over `600ms` `cubic-bezier(0.16, 1, 0.3, 1)`. Hover lift: shadow `0 0 0` → `0 2px 8px rgba(0,0,0,0.04)` over `200ms`. Active button `scale(0.98)`. Stagger `calc(var(--index) * 80ms)`.

**Bans — within this system.** No `Inter`/`Roboto`/`Open Sans`. No thin-line icons (`Lucide`, `Feather`, standard Heroicons) — use Phosphor (Bold/Fill) or Radix at standardized stroke. No `shadow-md`/`lg`/`xl` (shadows opacity `< 0.05`). No gradients, neon, or 3D glassmorphism (subtle navbar blur is the only exception). No `rounded-full` on large containers/cards/primary buttons (pills allowed at tag scale only). No primary-colored hero backgrounds.

---

## 2. Brutalist / Industrial

**Signature traits.** Fuses 1960s Swiss print + industrial manuals + aerospace/military terminals. Rigid CSS-grid blueprint, visible compartmentalization, bimodal density (dense monospace clusters vs vast negative space framing macro-type), engineered analog degradation.

**Pick exactly ONE substrate and commit — never mix the two.**

| | Swiss Industrial Print (light) | Tactical Telemetry / CRT (dark) |
|---|---|---|
| Background | `#F4F4F0` or `#EAE8E3` (matte paper) | `#0A0A0A` or `#121212` (never pure `#000000`) |
| Foreground | `#050505`–`#111111` carbon ink | `#EAEAEA` white phosphor |
| Accent | `#E61919` / `#FF2A2A` aviation red — ONLY accent | same red, same rules |
| Extra | — | Terminal green `#4AF626` on ONE element only, else omit |

**Typography.** Macro headers (neo-grotesque): Neue Haas Grotesk Black, **Inter Extra Bold/Black** (allowed *here only*), Archivo Black, Roboto Flex Heavy, Monument Extended — `clamp(4rem, 10vw, 15rem)`, tracking `-0.03em` to `-0.06em`, `line-height 0.85`–`0.95`, UPPERCASE. Data/telemetry (mono): JetBrains Mono, IBM Plex Mono, Space Mono, VT323, Courier Prime — fixed `10px–14px`, tracking `0.05em`–`0.1em`, `line-height 1.2`–`1.4`, UPPERCASE. Serif (Playfair/EB Garamond/Times) **exceedingly sparingly**, only when degraded with halftone/1-bit dithering.

**Spacing.** Strict CSS Grid; elements anchored to tracks, never floating. `1px`/`2px solid` borders and full-width `<hr>` delineate zones. Use `display:grid; gap:1px` with contrasting parent/child bg for razor-thin dividers. ASCII framing `[ DELIVERY SYSTEMS ]`, `< RE-IND >`, `>>>`, `///`; `®`/`©`/`™` as geometry; crosshairs `+` at intersections; strings like `REV 2.6`, `UNIT / D-01`.

**Motion feel.** Mechanical, not fluid. Texture over interpolation: CRT scanlines `repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.1) 2px, rgba(0,0,0,0.1) 4px)`, global low-opacity SVG noise grain, halftone via `mix-blend-mode: multiply` + SVG dot patterns.

**Bans — within this system.** No `border-radius` anywhere — all corners exactly 90°. No gradients, no soft drop shadows, no modern translucency/glassmorphism. No consumer UI conventions. Colors simulate physical media or primitive emissive displays only.

---

## 3. Soft

**Signature traits.** Haptic, machined depth that signals expense; never the same layout twice. Before coding, roll the engine and pick **one Vibe** and **one Layout**.

**Vibe (pick 1).**
| Vibe | For | Palette + material |
|---|---|---|
| Ethereal Glass | SaaS / AI / Tech | OLED black `#050505`, glowing purple/emerald radial mesh orbs, vantablack cards with `backdrop-blur-2xl` + `white/10` hairlines, wide geometric grotesk |
| Editorial Luxury | Lifestyle / Real Estate / Agency | warm cream `#FDFBF7` / sage / espresso, high-contrast variable serif heads, film-grain `opacity-[0.03]` |
| Soft Structuralism | Consumer / Health / Portfolio | silver-grey or pure white, massive bold grotesk, **unbelievably soft diffused ambient shadows** |

**Layout (pick 1).** Asymmetrical Bento (`col-span-8 row-span-2` beside stacked `col-span-4`; mobile → `grid-cols-1`, `gap-6`) · Z-Axis Cascade (overlapping cards, `-2deg`/`3deg` rotation; remove all rotation/overlap < `768px`) · Editorial Split (massive type `w-1/2` left, scrollable content right; mobile → full-width stack).

**Component signatures.** **Double-Bezel (Doppelrand):** outer shell `bg-black/5` + `ring-1 ring-black/5` + `p-1.5`/`p-2` + `rounded-[2rem]`; inner core distinct bg + `shadow-[inset_0_1px_1px_rgba(255,255,255,0.15)]` + `rounded-[calc(2rem-0.375rem)]` for concentric curves. **Button-in-button:** pill CTAs `rounded-full px-6 py-3`; trailing `↗` nested in `w-8 h-8 rounded-full bg-black/5` flush to inner padding. **Ambient shadow (the Soft signature, concrete):** a large-radius, low-opacity, slightly negative-spread stack — `box-shadow: 0 24px 60px -20px rgba(0,0,0,0.12), 0 8px 24px -12px rgba(0,0,0,0.08)` — never a harsh `shadow-md` / `rgba(0,0,0,0.3)`.

**Spacing.** Macro-whitespace `py-24` to `py-40`. Eyebrow tags `rounded-full px-3 py-1 text-[10px] uppercase tracking-[0.2em]`. Sections `min-h-[100dvh]`, never `h-screen`.

**Motion feel.** Real-world mass and spring. `transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)]`. Scroll entry: `translate-y-16 blur-md opacity-0` → `translate-y-0 blur-0 opacity-100` over `800ms+`. Magnetic hover: `active:scale-[0.98]`, inner icon `group-hover:translate-x-1 group-hover:-translate-y-[1px] scale-105`.

**Bans — within this system.** No `Inter`/`Roboto`/`Arial`/`Open Sans`/`Helvetica` (use Geist, Clash Display, PP Editorial New, Plus Jakarta Sans). No generic 1px-solid-gray borders, no harsh dark `shadow-md`/`rgba(0,0,0,0.3)`. No edge-to-edge sticky navbars glued to top (float a glass pill: `mt-6 mx-auto w-max rounded-full`). No symmetrical 3-column Bootstrap grids without whitespace. No `linear`/`ease-in-out` transitions.

---

## 4. High-end / Premium (Stitch)

**Signature traits.** Calibrated neutral restraint that reads expensive and intentional. Tune via dials — **Creativity 8 / Density 4 / Variance 8 / Motion Intent 6** baseline; adapt to vibe. Hierarchy through weight and color, **not** screaming size.

**Palette (one accent rule).**
| Role | Value |
|---|---|
| Canvas | Canvas White `#F9FAFB` (warm-neutral, never blue-white) |
| Surface | Pure White `#FFFFFF` |
| Ink | Charcoal `#18181B` (Zinc-950, never pure black) |
| Body / meta | Steel `#71717A`; tertiary Muted Slate `#94A3B8` |
| Border | Whisper `rgba(226,232,240,0.5)` |
| Shadow | Diffused `rgba(0,0,0,0.05)` |
| **Accent — pick ONE, sat < 80%** | Emerald `#10B981` (growth) · Electric Blue `#3B82F6` (SaaS/dev) · Deep Rose `#E11D48` (creative) · Amber `#F59E0B` (social) |

**Typography.** Display: `Geist`/`Satoshi`/`Cabinet Grotesk`/`Outfit`, tracking `-0.025em`, weight `700–900`, leading `1.1`, `clamp(2.25rem, 5vw, 3.75rem)`. Body: same family weight 400, leading `1.65`, 65ch, color `#71717A`, `1rem`/`1.125rem`. Mono: `Geist Mono`/`JetBrains Mono` at `0.8125rem`; **when Density > 7, all numbers switch to monospace.**

**Spacing.** Grid-first, `max-width: 1400px` centered, padding `1rem`/`2rem`/`4rem` (mobile/tablet/desktop). Cards `rounded-[2.5rem]`, pure white, whisper border, shadow `0 20px 40px -15px rgba(0,0,0,0.05)`, padding `2rem–2.5rem` — used ONLY when elevation serves hierarchy; high-density layouts replace cards with `border-top` dividers or negative space. Bento: Row 1 = 3 cols, Row 2 = 2 cols (70/30). Hero: inline-image typography (photos at type-height between words); centered hero banned when variance > 4; max 1 primary CTA.

**Motion feel.** Spring exclusively: `stiffness: 100, damping: 20`, no linear easing. Perpetual micro-loops (Pulse/Typewriter/Float/Shimmer) on active components. Stagger `calc(var(--index) * 100ms)`.

**Bans — within this system.** No `Inter` (premium contexts). No generic serifs (`Times New Roman`/`Georgia`/`Garamond`/`Palatino`) — only `Fraunces`/`Instrument Serif`/`Editorial New` if needed; serif always banned in dashboards. No pure black, no neon/outer glows, no accents > 80% saturation, no overlapping elements, no 3-equal-card rows, no `flexbox` percentage math (`calc(33% - 1rem)`), no `h-screen`, no circular spinners (skeletal shimmer only), no fake round numbers (`99.99%` → `47.2%`).

---

## 5. Brand-identity

**Signature traits.** Design IS the product. Distinctiveness is the bar; restraint without intent reads as mediocre. The real bar: a visitor asking **"how was this made?"** — not "which AI made this?". Run the **inverse test** before building: describe what you're about to build the way a competitor would describe theirs; if that sentence fits the category's modal landing page, restart. No fixed palette — **commit per project** and name a real reference.

**Color (commitment axis — name the reference first).**
| Strategy | Dosage | Reference |
|---|---|---|
| Restrained | tinted neutrals + one accent ≤10% | "Stripe purple-on-white restraint" |
| Committed | one saturated color carries 30–60% | "Klim #ff4500 orange drench" |
| Full palette | 3–4 named roles | "Liquid Death acid-green", "Mailchimp yellow" |
| Drenched | the surface IS the color | brand heroes / campaigns |

The `≤10%` rule is **Restrained-only**; Committed/Full/Drenched deliberately exceed it. When Committed or Drenched, don't hedge with neutrals — commit. Palette IS voice; don't converge across projects; reach past the obvious cultural-symbol palette.

**Typography (font-selection procedure — every project, never skip).** (1) Write three physical-object brand-voice words ("warm and mechanical and opinionated", not "modern/elegant"). (2) List three reflex fonts; reject any on the reflex-reject list. (3) Browse a real catalog (Google Fonts, Pangram Pangram, Future Fonts, Adobe Fonts, ABC Dinamo, Klim, Velvetyne); find the font for the brand as a physical object; reject the first thing that "looks designy". (4) Cross-check — if the pick lines up with the reflex, start over. **Reflex-reject (greenfield only):** Fraunces · Newsreader · Lora · Crimson · Playfair Display · Cormorant · Syne · IBM Plex (Sans/Mono/Serif) · Space Mono · Space Grotesk · Inter · DM Sans/Serif · Outfit · Plus Jakarta Sans · Instrument Sans/Serif. Modular scale, fluid `clamp()`, **≥1.25 ratio** between steps (flat 1.1× reads uncommitted).

**Spacing & permissions.** Asymmetric compositions, fluid `clamp()` spacing, intentional grid-breaking for emphasis; cards via `repeat(auto-fit, minmax(280px, 1fr))` when cards are right. Take permissions product can't: ambitious first-load motion (reveals + typographic choreography, not fade-on-scroll-everything — some brands skip entrance motion entirely), single-purpose viewports, unexpected color, art direction per section.

**Imagery (required when the brief implies it — zero images is a bug, not restraint).** Four operational rules: (1) **Search for the brand's physical object, not the category** — "handmade pasta on a scratched wooden table" beats "Italian food"; "cypress trees above a limestone hotel facade at dusk" beats "luxury hotel". (2) **One decisive photo beats five mediocre ones** — hero imagery commits to a mood; padding an indecisive hero with more stock never rescues it. (3) **Alt text is part of the voice** — "Coastal fettuccine, hand-cut, served on the terrace", never "pasta dish". (4) **"Imagery" is broader than photos** — product screenshots, custom data-viz, generated SVG, canvas/WebGL all count; the all-typography page is the failure mode, not a style. Unsplash URLs take the shape `https://images.unsplash.com/photo-{id}?auto=format&fit=crop&w=1600&q=80` — verify the IDs actually resolve, or pick fewer photos you're confident in.

**Identity-board modes (for logo/identity decks).** Default `3×3` board on a dark/light canvas, strong gutters, sparse type. Compact palette-mode map:

| Mode | Cues + palette |
|---|---|
| Dark Developer | near-black + mono, terminal/grid, cyan/blue/coral/lime |
| Dark Operator | black/dark-red/amber, glowing UI chips, reward motifs |
| Dark Nature/Calm | deep green + lime, misty landscapes, editorial grid |
| Dark Security | black/navy, shields, radar, red/blue alert chips |
| Light Editorial | warm ivory paper, small serif, seals, deep blue/red/gold |
| Luxury/Fashion | ivory/stone/espresso, serif wordmark, emboss, paper grain |
| Voice/Comms | dark indigo + lilac glow, waveform/mic |
| Cultural/Experimental | halftone/CRT/print, bold accent, poster panels |

Accents must repeat across panels; one accent can carry the system. Logo via one (max two) of: Monogram+Meaning, Product Action, Metaphor Fusion, Negative Space, Construction Geometry.

**Bans — within this register.** Monospace as lazy "technical" shorthand. Large rounded-corner icons above every heading. Single-family pages chosen by reflex (deliberate single family is fine). All-caps body copy. Timid palettes / average layouts (safe = invisible). Defaulting to editorial-magazine (serif + italic + drop caps) on non-magazine briefs. Repeated tiny uppercase tracked kickers above every section.

---

## 6. Product register

**Signature traits.** The tool disappears into the task. Inside the app, trust replaces distinctiveness as the bar; familiarity is a feature, not a failure. Applies on top of whichever build system the product uses.

**Color (accent = action).** Run **two neutral layers**: the content surface plus a second neutral — slightly warmer or cooler — for sidebars, toolbars, and panels, so structure reads without borders doing all the work. The accent means **action and nothing else**: primary actions, current selection, state indicators — never decoration. Restrained is the floor; a single surface may earn Committed (a drenched welcome screen, one category color carrying a report). Standardize a **state-rich semantic vocabulary** across every screen: hover, focus, active, disabled, selected, loading, error, warning, success, info — each state one consistent color treatment, everywhere.

**Permissions.** What's reflex-rejected on brand surfaces is legitimate here: system fonts and `Inter` are honest choices for UI. Standard navigation patterns (top bar + side nav, breadcrumbs, tabs, command palettes) are assets, not laziness. Density is a feature. Consistency beats surprise on every call.

**Bans — within this register.** Display fonts in UI labels, buttons, or data. Reinvented standard affordances — custom scrollbars, weird form controls, non-standard modals. Heavy or full-saturation color on inactive states. Inconsistent component vocabulary — if the save button looks different in two places, one of them is wrong. **Modal as first thought** — modals are usually laziness; exhaust inline and progressive-disclosure alternatives first.

**The product slop test.** Not "would someone say AI made this" — that's the brand test. Here: would a user fluent in Linear, Figma, Notion, Raycast, or Stripe sit down and trust this immediately, or pause at every subtly-off component? The product failure mode is strangeness without purpose, not flatness.

---

## Cross-System Contradictions

The same property gets opposite verdicts. This is by design — proof the rules are scoped, not universal.

| Property | Minimalist | Brutalist | Soft | High-end (Stitch) |
|---|---|---|---|---|
| `Inter` font | ❌ banned | ✅ **required** (Extra Bold/Black, macro-type) | ❌ banned | ❌ banned |
| Drop shadows | opacity `< 0.05` | ❌ banned entirely | ✅ **required** (soft, diffused, ambient) | diffused `rgba(0,0,0,0.05)` only |
| `border-radius` | crisp `4–12px` | ❌ **90° / none** | `rounded-[2rem]` squircles | `rounded-[2.5rem]` cards |
| Gradients | ❌ banned | ❌ banned | ✅ glass mesh orbs | ❌ no gradient text/neon |
| Color dosage | scarce spot pastels | single hazard red | vibe-driven | one accent < 80% sat |
| Motion | quiet `600ms` fade | mechanical/static | spring blur-up `800ms` | spring `100/20` + loops |

---

## Never mix two systems' signatures in one surface

A page is one language. Glass orbs (Soft) on hairline-border bento (Minimalist) reads as confused, not eclectic. CRT scanlines (Brutalist) under whisper-shadow cards (Stitch) cancel each other. Brutalist itself forbids mixing its *own* two substrates (Swiss Print vs Tactical Telemetry). Brand-identity may art-direct different *sections* into different visual worlds — but that is one voice spanning worlds, not two systems colliding on the same surface. Pick one, commit, and let the bans of that system do their job.
