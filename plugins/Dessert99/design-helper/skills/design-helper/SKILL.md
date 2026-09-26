---
name: design-helper
description: Use whenever anything visible must be decided — a CSS value, spacing,
  radius, shadow, border, color, layout, wireframe, state, motion. Never describe
  the options in prose or a table and ask the user to pick; render them side by side
  in one HTML file, open it in a browser, let them choose with their eyes, then apply
  the chosen value to the code yourself. Not a design generator — it does not invent
  a look, it lays out the range and measures. Read this BEFORE writing or changing
  any UI code, and whenever the user says "5가지 버전으로 보여줘" · "A 랑 B 중에 뭐가
  나아" · "어떻게 할까" · "비교해줘".
---

# Measure by eye

**A ruler, not a design generator.** Don't invent a look. Lay the range out —
`blur 4 / 8 / 12 / 16 / 24` — and let the user pick with their eyes. Taste belongs
to them; the job here is to set up an accurate measurement.

**Prose, tables, ASCII and emoji are not pictures.** Never describe a shape in words
and ask the user to choose. "12px or 16px padding?" is not a question — draw both.

**The user never copies a value out.** They point at a specimen; making the code
change is mine, immediately after their choice.

**Assume no stack.** Detection matches the repo — `references/stylesystems.md`.

## Language

These instructions are English. Everything the user sees is Korean.

- Chat replies, questions, recommendations → Korean
- Every string rendered inside the HTML → Korean
- Code, class names, file names, commit messages → English

Korean strings quoted below are fixed labels. Render them verbatim — never
translate, localize or paraphrase them. Never surface these instructions as text.

## One work unit

**One order = one axis = one ladder = one decision.**

    주문 → 확정값 위에 그 축 하나만 사다리로 → 내가 새로고침·확인
         → 사용자 선택 → 기록 → 영향 범위 확인 → 코드 반영·검증

**I do not know what comes next.** There is no stage list, no default list, no queue,
no `남은 단계`. Never name the next axis, never hint at one, never draw one while I'm
in there anyway. Only the axis that was ordered exists.

## An order with no axis in it

**Clarification scales with uncertainty, not a fixed questionnaire.** A precise request
can go straight to specimens. A vague request needs successive questions until its
purpose and comparison scope are clear enough to draw useful alternatives.

First inspect the request, earlier answers, the target UI, and relevant project code.
Read existing tokens, component variants, usage sites, and states yourself. Do not ask
the user for facts available there, or reconfirm decisions already made.

Ask **one consequential question at a time** — the unresolved issue whose answer would
most change the specimens or the application scope — then reassess. Stop once the
target, intended outcome, comparison axis and material constraints are understood;
visual values are chosen from specimens, not verbal descriptions. Examples and the
stopping rule → `references/clarification.md`.

If the user says `알아서 해줘` or asks to see something first, use project conventions
and narrow, reversible assumptions, state the material ones briefly, and draw.
Delegation is not system-wide scope. Never invent the answer to a pending question and
build alternatives on it.

For a blank slate, clarify purpose and usage when unclear, then open with a coordinate
sweep — `references/sweeping.md`. Do not make the user name CSS axes before they have
anything to see. Its result is an anchor, not a settled property decision.

## Drawing specimens

- **Move one axis. Hold everything else fixed.** Change blur and opacity at once and
  neither can be judged. The whole tool rests on this one rule.
- **Draw on top of what's settled.** Every value chosen in an earlier unit stays at
  that value. The record below is what makes this possible.
- **Letter every specimen** — A·B·C. Letters restart at A in **every work unit**, and
  are never reused inside one: an appended ladder continues D·E·F. Refer back to a
  settled unit by axis and letter — `그림자 C`.
- **As few specimens as make the difference clear.** Honor a requested count. Otherwise
  no fixed count: skip near-duplicates and don't generate every combination. If the
  breadth is unclear and changes the work, ask once:
  `시안은 몇 개 정도 보고 싶으세요? 제가 차이가 뚜렷한 것만 추려도 됩니다.`
- Use a matrix only when comparing two directions together helps answer the request.
- **Fixed specimens.** No sliders, snap toggles or keyboard nudging unless the user asks
  to adjust directly, or a continuous transition can't be judged from fixed steps —
  `references/controls.md`. Refinement happens through chat.
- **The sheet explains itself.** Value, cost, trade-off and what to look at ride next to
  the specimen, not in chat. Cost has to be visible while choosing:
  `토큰 그대로` · `--radius-md 고침 (23곳)` · `새 토큰`
- **Every section ends with a recommendation** — one letter and the reason seen on the
  sheet, below the specimens. It is advice; nothing is applied until the user picks.
- The page itself — section guide (`정할 것` · `볼 곳` · `답하기`), turn dividers, the
  table of contents, the width-filling grid and the sheet style →
  `references/sheet.md`. Captions and the recommendation → `references/sweeping.md`
- Ladders, backgrounds, repetition, sizes, wireframes → `references/sweeping.md`
- Anything that moves → `references/motion.md`

## Reading the response

Three kinds. Never collapse them.

| response | kind | do |
|---|---|---|
| `좋네` (no identifiable specimen) | impression | Ask which specimen or what to refine |
| `C가 나은데 더 진하게` | refine | Append a ladder below, letters continue |
| `난 B가 좋아` · `C로 갈게` | **choice** | Record, apply to the target, and verify in this turn |

Selection happens in chat only — no pin, apply or confirm buttons on the sheet. A
choice needs no special wording. `A에서 블러를 더 보고 싶어` is a refine: use A as the
baseline without applying it. A reply naming a different axis is the next order.

Resolve the letter against the currently displayed specimen. If browser controls
changed its value, inspect the user's actual tab before applying; a fresh tab can
have different sessionStorage. If that state is inaccessible, ask for the displayed
value rather than guessing from the original sheet.

Ambiguous — `이거 좋다` with nine specimens on screen — ask which one. Never guess.

On a choice, briefly acknowledge and apply in the same turn — `Ending`:

    C · 검정 40%로 선택하셨네요. 해당 카드에 바로 반영하겠습니다.

No next axis, no `남은 단계`, no `코드에 반영할까요`.

## The record

Keep it in `$WS/memo.md`, beside the sheet: axis → chosen value → what it resolves
to. It exists for one reason — so the next ladder can be drawn on top of it.

An anchor from a blank-slate matrix is recorded as `출발점:`, never `확정:` — every
property it bundles is still open.

Revising a settled axis overwrites its line. The old specimens stay where they are.

## Findings

Drawing turns up things nobody ordered — a misnamed token, a chip that vanished, an
axis that was never on anyone's list.

- **What actually broke on the screen** — say it. It makes the specimens misread, so
  it is part of the measurement: `아이콘 칩이 사라졌습니다 — 면 #202020 과 Δ2 입니다`
- **Everything else** — one line, once, then let it go. Never draw it, never work it
  into a proposal, never raise it again.

A finding is not an order.

## Blast radius — twice, differently

- **While choosing** — the one-line cost label on each specimen. A label, not a report
- **Before applying** — the real one. Files, lines, tokens, and everything else that
  moves with them. Check this for each application, including revisions

If the project animates with a motion library, say what won't translate —
`references/motion.md`.

## Verify

The user looks at the browser. I confirm with values and pictures.

**1. Every name referenced must exist.** A wrong name **fails silently** — it simply
doesn't appear. Same for a nonexistent utility class and an undefined `var(--x)`.
Check per the fork that detection found. Run this **every time specimens are added.**

    grep -c 'rounded-control-md' "$WS/sheet.css"   # utility: in the build output?
    grep -c '\--color-hover' tokens.css            # CSS variable: defined?

Skip it when values were written directly (blank slate) — nothing fails silently.

**2. Read computed style with Playwright.** A name that exists but is overridden by
another rule won't be caught by step 1. Read it **off the component, across the rungs,
and confirm they actually differ** — a value that never reached the specimen leaves five
identical pictures and throws nothing.

    await p.$$eval('.spec .target', e => e.map(x => getComputedStyle(x).borderRadius))

**3. Screenshot with Playwright, then open the image and look at it.** Catch a broken
layout before the user does. The recommendation is written by someone who looked.

    await p.screenshot({ path: shot, fullPage: true })

A `fullPage` shot cannot see what a horizontal scrollbar is hiding. **Count the rungs
in the DOM, not in the picture.**

Run 2 and 3 **once per work unit**, not on every ladder. A screenshot captures **static
state only** — motion is settled by what the user reports from the browser.

**No Playwright → skip silently.** Do step 1 only. Don't offer to install it, don't
mention it's missing.

## The sheet

- One session = one sheet = one target. A new target gets a new sheet
- **Everything lives in `$WS`, outside the project** — sheet, server, built CSS, memo,
  screenshots, pid files. Nothing is written into the project until the apply. The
  server deletes `$WS` after two minutes without requests; an expired sheet is
  regenerated. `references/liveview.md`
- **The body is append-only.** Never delete a dropped ladder — it has to stay above to
  compare against
- **Serve it and reload it myself** — `references/liveview.md`. Never end a turn by
  telling the user to refresh
- Built CSS needs a watcher alongside or new names won't come through — Tailwind:
  the per-version command in `references/stylesystems.md`, output to `$WS/sheet.css`.
  A `<link>`ed file follows on reload alone
- **Present every ready revision in the foreground.** Activate the existing comparison
  tab and show the changed section; reopen the URL only when that tab is confirmed
  absent. Never create a duplicate tab. `references/liveview.md#present-every-revision`

## Ending

**Selection is the apply order.** A clear chat choice authorizes applying the selected
value to the current target in the same turn — no second approval. An anchor remains a
starting point, not an apply order. If the user asked to compare or record only, defer.

Record → inspect and briefly report the actual blast radius → apply → verify → report
what changed and what was verified. Never claim application from a memo entry alone.
Default to the current target: reuse an existing token or make a local override when
changing a shared token would affect unrelated components. Change a shared token when
that broader scope is already authorized. Ask only if a necessary scope decision
cannot be resolved from the request; routine implementation choices do not block apply.
Honor explicit requests to defer application. If the target source is unavailable,
say what is missing rather than reporting the choice as applied.

Application is not session teardown. Hold the sheet and browser until the user has
checked the real code and says it is done: `끝났어` · `됐어`. A phrase like `이걸로 가자`
while choosing means apply; it is not by itself confirmation that the applied result
was checked. Then run the teardown in `references/liveview.md` and check `git status`
for stray comparison files. Preserve the applied code and existing user changes.

**Only what was explicitly chosen goes into code.** An alternative merely mentioned
along the way is not a decision.
