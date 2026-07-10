# Interaction Design

The behavioral layer: cognitive load, state modeling, input patterns, feedback loops, and emotional timing. Read alongside `motion-and-interaction.md` (which covers animation mechanics). This file covers the *why* of behavior; motion covers the *how* of animating it.

---

## Cognitive Laws

Four empirically-grounded constraints on interaction speed and accuracy. Apply before specifying any interactive pattern.

### Fitts's Law — target size and distance

Acquisition time scales with distance and shrinks with target size. Large targets near the pointer are fast; small targets far away are slow and error-prone.

**Hard rules:**
- Touch targets ≥ 44×44pt (Apple HIG) / 48×48dp (Material). This is the *interactive area*, not the visual icon — a 16px icon can have a 44px tap area via padding.
- Pointer targets: 24×24px minimum; more for dense UIs.
- Screen edges are infinite targets (pointer cannot overshoot) → use for persistent navigation (macOS menu bar, taskbar).
- Bottom-of-screen placement reduces reach distance for right-hand thumb on mobile.
- Destructive actions: intentionally small and distant to prevent accidental activation.

| Pattern | Fitts's Law application |
|---|---|
| Primary CTA | Large, high-contrast, in thumb reach zone |
| Floating action button | Bottom-right on mobile |
| Navigation tabs | Bottom nav on mobile beats top nav for one-handed use |
| Modal actions | Buttons near bottom of modal, not scattered across it |
| Form submit | Full-width or prominent, directly below last field |
| Close button | Large hit target; consider bottom-dismiss on mobile |
| Destructive action | Small, distant, away from the primary flow |

Audit: test on real devices — what looks adequate in design tools is routinely too small in hand. High mis-tap rates are almost always Fitts's Law failures.

### Hick's Law — choice and decision time

Decision time grows logarithmically with the number of simultaneous choices. Adding options always costs something, even if not proportionally.

**Hard rules:**
- Group before reducing — categorization reduces apparent complexity more than deletion.
- Navigation: limit top-level items (≤7); group secondary items in overflow menus.
- Toolbars: surface most-common actions; tuck the rest behind an overflow control.
- Onboarding: one decision per step, not multiple choices per screen.
- Pricing: three tiers is the sweet spot; more creates analysis paralysis.
- Smart defaults: for high-frequency, low-variance decisions, skip the choice entirely.

Do not confuse "fewer simultaneous choices" with "less functionality." The goal is reducing cognitive load at any moment, not removing features.

### Miller's Law — working memory chunks

Realistic working memory limit: 4 ± 1 *meaningful chunks* (Cowan 2001). The "magic 7" is outdated and misapplied. A chunk is whatever has meaning to the person — a word, a familiar pattern, a concept.

**Hard rules:**
- Navigation: group menu items by category; flat lists of 10+ items are harder to scan than 3 groups of 3–4.
- Forms: break into named sections; each section should feel completeable as a unit.
- Codes and numbers: format as chunks (`555-867-5309`, `XXXX-XXXX` verification codes).
- Data tables: visual grouping (alternating rows, section headers) to break long lists.
- Onboarding: 3–5 named phases rather than a raw step count of 12.
- Feature lists: 3–5 bullet points per tier; beyond that, users stop reading.

Structure first, count second. Meaningful groupings matter more than hitting any number.

### Doherty Threshold — response time and flow

Under 400ms → user stays in flow. Over 400ms → they notice the wait; cognitive engagement drops.

| Response time | User perception |
|---|---|
| 0–100ms | Instant — system feels like a direct extension of the action |
| 100–300ms | Fast — perceptible but not disruptive |
| 300–400ms | Approaching the edge — some users notice |
| 400ms–1s | Slow — response indicator required |
| 1s+ | Broken flow — progress feedback required |
| 10s+ | Task-level disruption; users switch context |

**Hard rules:**
- Button visual state change on press: within 100ms regardless of whether the underlying action completes.
- Search / filter: results begin appearing before 400ms; if not, show skeleton immediately.
- Autocomplete: first suggestions within 300ms of typing.
- If you cannot meet the threshold: acknowledge within 100ms (button state change), then skeleton/spinner if completion takes 400ms–3s, then progress if 3s+.
- Optimistic UI: update the interface immediately, reconcile on server response.
- Never show a loading indicator for actions that complete under 400ms — a flash of spinner is itself disruptive.

---

## State Machines

Model every non-trivial UI component as a finite state machine to eliminate impossible states and make behavior predictable.

**Components:**
- **States** — Distinct modes the UI can be in: `idle`, `loading`, `success`, `error`, `empty`, `disabled`, `editing`
- **Events** — Things that cause transitions: click, submit, API response, timeout, validation
- **Transitions** — Valid state-to-state paths: `on event X in state A → go to state B`
- **Guards** — Conditions on transitions: `isValid`, `hasPermission`, `isOnline`
- **Actions** — Side effects during transitions: fetch data, show toast, log event

**Standard machines:**

| UI pattern | State sequence |
|---|---|
| Form | `idle` → `editing` → `validating` → `submitting` → `success` / `error` → `idle` |
| Data fetch | `idle` → `loading` → `success` / `error`; `error` → `retrying` → `success` / `error` |
| Authentication | `logged-out` → `authenticating` → `logged-in` → `logging-out` → `logged-out` |
| Multi-step wizard | `step1` → `step2` → … → `review` → `submitting` → `complete` |
| Toggle | `off` ↔ `on` (add `pending` for async toggles) |
| File upload | `idle` → `selecting` → `uploading` → `success` / `error` |

**Rules:**
- Every state has at least one way out. No dead ends.
- No impossible combinations: never `loading` + `error` simultaneously — these are separate states.
- Every state maps to exactly one UI representation (including loading, empty, error).
- Start with the happy path, add error and edge states after.
- Keep machines focused — one per concern.

**Why it matters:** State machines give design and engineering a shared language. Every UI branch (loading skeleton, error message, empty state, disabled form) is a deliberate state, not an afterthought to discover in QA.

---

## Form Design

Single column, almost always. Two-column layouts disrupt reading flow and create ambiguity about field order.

**Layout:**
- Field width reflects expected input length: a postcode field is narrow; a bio field is wide. Width is an affordance for what belongs there.
- Top-aligned labels — faster to scan, more resilient to long labels than left-aligned or placeholder-only patterns.
- Group related fields using proximity and section headings.
- Mark optional, not required — when most fields are required, flagging optional reduces visual noise.

**Labels and instructions:**
- Every field has a persistent, visible label. Never rely on placeholder text as the only label (it disappears on input; it fails accessibility).
- Helper text: below the label, above the field. "Format: DD/MM/YYYY."
- Character counts: show remaining characters when limits exist; show them always, not only on approach.
- Labels: sentence case, not ALL CAPS.

**Input type selection:**

| Data type | Input type |
|---|---|
| Short text | Text input |
| Long text | Textarea (with visible resize handle) |
| One from ≤5 options | Radio buttons (all visible simultaneously) |
| One from 6+ options | Select / combobox |
| Multiple from few options | Checkboxes |
| Date | Date picker or segmented fields (day/month/year) — never freeform text for structured dates |
| Phone / card numbers | Formatted text input with masking |
| Password | Password input with show/hide toggle |

**Validation:**
- On blur (when the user leaves the field), not on every keystroke — real-time typing validation is distracting.
- Error placement: directly below the field, not at the top of the form.
- Error messages: explain what went wrong and how to fix it. "Email address must include @" not "Invalid email".
- Success indication: subtle checkmark for fields with non-obvious correctness (password strength, username availability).
- Server-side errors: surface inline to the field if possible; summarize at top if multiple fields are affected.

**Multi-step forms:**
- Show a step indicator that names the steps, not just "Step 2 of 5."
- Each step completeable as a unit — related fields together.
- Allow back navigation without losing data.
- Auto-save or "save and continue" for long forms.
- Confirm before discarding partial input.

**Accessibility:**
- Every field: `<label for>` or `aria-label`.
- Error messages: `aria-describedby` pointing to the field.
- Focus order follows visual order.
- Error summary at top: keyboard-focusable, links to each failing field.
- Never rely on color alone for required or error states.

**Minimum:** remove every optional field you can. Fewer fields = higher completion.

---

## Navigation Patterns

Selecting the wrong navigation pattern is the most expensive IA mistake — it compounds across every screen in the product.

**Pattern selection:**

| Situation | Recommended pattern |
|---|---|
| Mobile, 3–5 primary destinations | Bottom tab bar |
| Desktop app, many destinations or nested structure | Side navigation / sidebar |
| Simple marketing site or docs | Top navigation bar |
| Deep content hierarchy | Breadcrumbs + local sidebar |
| Parallel views of the same content | Tabs or segmented control |
| Occasional, non-primary access | Utility nav or overflow menu |

**Pattern notes:**
- **Bottom tab bar:** icons + labels; always visible; 3–5 destinations maximum.
- **Side navigation:** vertical list; scales to many items; supports nested structure with expand/collapse.
- **Top nav bar:** horizontal links in header; 4–7 destinations; simpler hierarchies only.
- **Breadcrumbs:** essential in deep hierarchies; show the path from root to current page.
- **Hamburger / drawer:** hides navigation; reduces discoverability — reserve for secondary nav or extremely constrained contexts, never for primary navigation on desktop.
- **Segmented control:** compact tab variant for 2–4 tightly related views.

**Four design principles:**
1. **Orientation** — Users always know where they are: active state, breadcrumb, page title.
2. **Wayfinding** — Users can predict where a destination takes them before clicking (label scent). Validate with first-click tests.
3. **Reachability** — Primary destinations in thumb reach (bottom of screen on mobile).
4. **Consistency** — Navigation placement and structure never change between screens.

**Active states:** must be distinguishable across default, hover, focus, active, disabled, and notification badge. Distinguish by more than color alone — add weight, underline, or indicator bar.

**Common mistakes:**
- Hamburger menu for primary navigation on desktop.
- Mixing global + local navigation in the same visual component.
- Using internal product names users don't recognize as labels.
- More than 7 top-level destinations without revisiting the IA.
- Inconsistent active states across sections.

---

## Error Handling UX

A four-layer system, not a single error message.

**Hierarchy:**
1. **Prevention** — inline validation before submission, smart defaults, confirmation dialogs for destructive actions, constraint-based inputs, auto-save to prevent data loss.
2. **Detection** — real-time field validation (on blur), form-level validation on submit, network error detection, timeout handling, permission and auth checks.
3. **Communication** — human language (not error codes); always: what happened + why + what to do; place message near the source; appropriate severity (error / warning / info / success).
4. **Recovery** — preserve user input (never clear forms on error), offer retry for transient failures, auto-retry with backoff for network errors, undo for accidental actions, alternative paths.

**Error message format:**
> [What happened]. [Why, if helpful]. [What to do — one specific action.]

| ✓ | Your session expired. Sign in again to continue. |
|---|---|
| ✗ | Error 401. Unauthorized. |
| ✓ | Email address must include @. Check for typos. |
| ✗ | Invalid email. |

**Error states by context:**

| Context | Approach |
|---|---|
| Form field | Inline error directly below the field; summary at top if multiple fields fail |
| Full-page failure | Full-page error with retry + back option |
| Network / API failure | Toast or banner with retry action |
| Zero search results | Explain what was searched; suggest corrections and alternatives |
| Permission denied | Explain what access is needed and how to request it |

Never blame the user. Preserve their data. Test error paths as thoroughly as happy paths.

---

## Feedback Patterns

Every user action needs acknowledgment. The question is what kind and where.

**Hierarchy (innermost wins):**
1. Inline / contextual — closest to the action (preferred)
2. Component-level — within the current component
3. Page-level — toast or banner
4. System-level — notification outside the current view

**Types:**

| Type | Examples |
|---|---|
| Immediate | Button state change on click, inline validation on input, toggle visual response |
| Confirmation | Success toast, completion animation, undo option |
| Status | Progress bars, status badges, typing / uploading / syncing indicators |
| Notification | In-app alerts, badge counts, banners, push |

**Timing:**
- Toasts: auto-dismiss after 3–5 seconds.
- Errors: persist until resolved or dismissed by the user.
- Confirmations: brief display with an undo window.
- Status: persist while relevant.

**Channels:** Visual (color, icon, animation) / Text (toast, inline label) / Haptic (mobile). Never rely on one channel alone — color without text or icon fails accessibility.

**Rules:**
- Acknowledge every user action.
- Match feedback intensity to action importance (silent for trivial, explicit for consequential).
- Don't interrupt flow for minor confirmations.
- Prefer undo over "Are you sure?" dialogs — undo keeps flow; confirmation breaks it.

---

## Loading States

**Pattern selection:**

| Pattern | Use when |
|---|---|
| **Skeleton screen** | Content structure is known; fill layout shapes with shimmer; preferred over spinner |
| **Indeterminate spinner** | Unknown content structure or duration under ~10s |
| **Determinate progress bar** | Duration or percentage is measurable |
| **Optimistic UI** | High confidence the action will succeed; show result immediately, reconcile on server response |
| **Progressive loading** | Critical content first, enhance progressively; blur-up images (low-res placeholder → full) |

**Duration guidelines:**

| Duration | Indicator |
|---|---|
| Under 100ms | Nothing — no indicator needed |
| 100ms–1s | Subtle: skeleton appear, opacity fade |
| 1–10s | Clear loading state; determinate progress if measurable |
| Over 10s | Detailed progress, estimated time, background-continue option |

**Transition rules:**
- Fade content in — don't pop.
- Stagger list items 30–50ms intervals.
- Avoid layout shifts when content loads (`aspect-ratio` on image containers prevents CLS).
- Maintain scroll position on refresh.
- Skeleton shapes must match actual content proportions — an avatar skeleton for a text block is worse than no skeleton.

---

## Gesture Patterns

**Core gestures:**

| Gesture | Primary uses |
|---|---|
| Tap | Select, activate, toggle |
| Double-tap | Zoom, like / favorite |
| Long-press | Context menu, reorder mode, peek / preview |
| Swipe | Navigate between views, dismiss, reveal row actions |
| Pinch | Zoom in / out |
| Drag | Move, reorder, adjust slider values |
| Pull | Pull-to-refresh |

**Design rules:**
- Every gesture must pair with a visible affordance. Users don't discover gestures by accident.
- Every gesture must have a non-gesture alternative (a button or menu item). Non-negotiable on touch.
- Provide immediate visual response when a gesture starts.
- Show threshold indicators — snap points, rubber-banding — so users know when the gesture will commit.
- Direction lock: after initial movement, lock to horizontal or vertical to resolve scroll vs. swipe conflict.
- System gestures take priority — never fight back-swipe or notification-pull.

Accessibility: every gesture must have a non-gesture alternative; support switch control and voice control; document custom gestures.

---

## Interfaces That Feel

Technical correctness is the floor. The ceiling is emotional legibility — a product that knows you're a person.

**Translation process:**
1. **Name the felt state** — What is the person actually experiencing? Waiting anxiously. Recovering from a mistake. Celebrating a small win. Being overwhelmed by options.
2. **Find the physical analogue** — What in the physical world has that quality? A soft surface absorbs impact. The slow release of a door closing. A held breath before exhaling.
3. **Extract the behavioral property** — Weight, resistance, speed, recovery arc, rhythm.
4. **Apply to the interface** — Easing curve, delay, copy tone, color temperature, spacing, animation duration.

**Copy voice by state:**

| State | Voice |
|---|---|
| Loading | Present and calm — "Getting your data" not "Loading…" |
| Empty | Invitational — tell them what belongs here and what to do first |
| Error (user-caused) | Clear, directive, blame-free — one specific next step |
| Error (system failure) | Own it, apologize briefly, offer a path forward |
| Success | Warm and brief — acknowledge without overdoing it |
| Onboarding | Contextual — what they can do, not how the app works |

**Emotional timing:**
- Heavy news arrives slowly; good news can be instant.
- After an error: give 300–600ms before the next prompt — don't rush the recovery.
- System error copy must own the failure; never make the user feel responsible.
- Micro-wins deserve acknowledgment — silent success is a missed connection.
- The loading state sets expectation; match its mood to what's coming.

**Motion as emotional signal:**
- Ease-in conveys weight and momentum.
- Ease-out conveys natural deceleration, something landing softly.
- Stiff spring: snappy and confident.
- Loose spring: playful and forgiving.
- Duration for UI response: 150–300ms. For transitions that carry meaning: 400–600ms.

**Review check — run on every state:**
- What is the person feeling when they hit this state?
- Is the interface acknowledging that feeling or ignoring it?
- Does the copy sound like a person wrote it?
- Does the motion convey intent or just fill time?
- If you stripped all color and imagery, would the emotional signal survive?
