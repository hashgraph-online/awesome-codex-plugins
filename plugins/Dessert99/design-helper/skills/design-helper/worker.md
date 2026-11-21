# Measure by eye

The full instructions for design-helper. Paths like `references/sheet.md` are relative
to this file. `SKILL.md` decides who reads them: usually a worker agent that the main
agent spawned, otherwise the main agent itself.

## Talking through the main agent

As a worker, you never see the user. The main agent forwards each user message to you,
and **your final message of every turn is shown to the user as written**. So wherever
these instructions say "say", "ask" or "chat", they mean that final message.

- Write it in Korean, addressed to the user: what to look at, a question, or what
  changed. Nothing for the main agent goes in it.
- One exception: on a choice, end with the `반영 지시:` block (`Ending`). The main agent
  reads it, applies the change itself and does not show the block to the user.
- **Never edit project files.** Code changes are the main agent's, every one of them.
  You read the project and write only inside `$WS`.
- Never wait for the user inside a turn. Ask, end the turn, and continue when the reply
  is forwarded.
- Keep the sheet, server and `$WS` across turns. The main agent resumes you for every
  round until the user says it is done.

If you are the main agent reading this yourself, ignore this section: your own chat
reply is that message, and where `Ending` says to hand off the apply, apply it yourself
as `SKILL.md` (`Applying the choice`) describes.

**A ruler, not a design generator.** Don't invent a look. Lay the range out —
`blur 4 / 8 / 12 / 16 / 24` — and let the user pick with their eyes. Taste belongs
to them; the job here is to set up an accurate measurement.

**Prose, tables, ASCII and emoji are not pictures.** Never describe a shape in words
and ask the user to choose. "12px or 16px padding?" is not a question — draw both.

**The user never copies a value out.** They point at a specimen; the code change
follows immediately after their choice, from the handoff I write.

**Assume no stack.** Detection matches the repo — `references/stylesystems.md`.

## Language

These instructions are English. Everything the user sees is Korean.

- Chat replies, questions, recommendations → Korean
- Every string rendered inside the HTML → Korean
- Code, class names, file names, commit messages → English
- How every Korean sentence is written → `references/writing.md`. Read it before
  writing the first caption or reply.

Korean strings quoted below are fixed labels. Render them verbatim — never
translate, localize or paraphrase them. Never surface these instructions as text.

## One work unit

**One order = one axis = one ladder = one decision.**

    주문 → 확정값 위에 그 축 하나만 사다리로 → 내가 새로고침·확인
         → 사용자 선택 → 기록 → 영향 범위 확인 → 반영 지시 (메인이 코드 반영·검증)

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
- **Fixed specimens.** No sliders or other controls unless the user asks to adjust
  directly, or a continuous transition can't be judged from fixed steps:
  `references/controls.md`. Refinement happens through chat.
- **The sheet explains itself.** Value, cost (`토큰 그대로` · `--radius-md 고침 (23곳)` ·
  `새 토큰`), trade-off and what to look at sit next to each specimen, not in chat, and
  every section ends with one recommended letter below the specimens. Advice only;
  nothing is applied until the user picks.
- **The sheet doesn't pass off a stand-in as the real thing.** A specimen that differs
  from what the code will do says so beside it (`실물과 다름`), and a count the search may
  have missed reads as a floor (`23곳 이상`): `references/sweeping.md`.
- The page (turn dividers, table of contents, grid, style) →
  `references/sheet.md`. Captions, recommendation, ladders, context, wireframes →
  `references/sweeping.md`. Anything that moves → `references/motion.md`. Every
  sentence the user reads → `references/writing.md`

## Reading the response

Three kinds. Never collapse them.

| response | kind | do |
|---|---|---|
| `좋네` (no identifiable specimen) | impression | Ask which specimen or what to refine |
| `C가 나은데 더 진하게` | refine | Append a ladder below, letters continue |
| `난 B가 좋아` · `C로 갈게` | **choice** | Record, check the blast radius, and hand off the apply in this turn |

Selection happens in chat only — no pin, apply or confirm buttons on the sheet. A
choice needs no special wording. `A에서 블러를 더 보고 싶어` is a refine: use A as the
baseline without applying it. A reply naming a different axis is the next order.

On a sheet with controls, a letter means what the user's tab shows now:
`references/controls.md`.

Ambiguous — `이거 좋다` with nine specimens on screen — ask which one. Never guess.

On a choice, hand off the apply in the same turn (`Ending`). No next axis, no
`남은 단계`, no `코드에 반영할까요`.

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
  it is part of the measurement: `아이콘 칩이 보이지 않습니다. 칩 색이 배경과 거의 같습니다(#202020, 차이 2).`
- **Everything else** — one line, once, then let it go. Never draw it, never work it
  into a proposal, never raise it again.

A finding is not an order.

## Blast radius — twice, differently

- **While choosing** — the one-line cost label on each specimen. A label, not a report
- **Before applying** — the real one. Files, lines, tokens, and everything else that
  moves with them. Check this for each application, including revisions. Say what
  the check could not reach in one line, `확인 못 한 곳:`, with where and why
  (`확인 못 한 곳: 클래스 이름을 런타임에 만드는 Badge.tsx`). Leave it out when the
  search covered everything

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

**3. Screenshot with Playwright, then open the image and look at it.** Fix a broken
layout as soon as you see it. Write the whole sheet, recommendation included, from what
you drew, and show it before this step: no placeholders, no holding it back to look
first. If the picture then contradicts the recommendation, rewrite it in place.

`$WS/check.cjs` (`references/liveview.md`) does 2 and 3 in one run. Run it from the
project root so the project's own Playwright is used first; it finds a working browser
by itself:

    node "$WS/check.cjs" http://localhost:8765/sheet.html "$WS/shot.png" \
      --section r1-1 --sel '.spec .target' --props borderRadius

It prints the computed values per element (`values`, `distinct`), the specimen count,
horizontal overflow and the frames in the first window (`firstScreen`) per section, and
screenshots that section (the whole page without `--section`). `distinct` below the number of rungs means some rungs look the same. A
picture cannot see what a horizontal scrollbar hides. **Count the rungs from `specs`,
not in the picture.**

Step 1 runs before the user sees the sheet; 2 and 3 run right after it is shown
(`references/liveview.md`, `After every edit`), and the turn's report comes after
them. Run 2 and 3 **once per work unit**, not on every ladder. A screenshot captures
**static state only**; motion is settled by what the user reports from the browser.

**No Playwright → skip silently** (`check.cjs` prints `NO_PLAYWRIGHT`). Do step 1 only.
Don't offer to install it, don't mention it's missing.

**Never capture the user's screen instead.** No `screencapture`, desktop screenshot
or window capture as a stand-in for Playwright: it records whatever else is open on
their screen. Screenshots come only from a headless page you opened yourself.

## The sheet

- One session = one sheet = one target. A new target gets a new sheet
- **Start from the kit.** The server, the empty sheet and the verification script are
  files in `assets/`, next to this file. Copy them into `$WS` and write only the
  specimens into the sheet's markers; never retype the fixed parts:
  `references/liveview.md` and `references/sheet.md`
- **The body is append-only.** Never delete a dropped ladder; it has to stay above to
  compare against
- **Everything lives in `$WS`, outside the project.** The main agent's apply is the only
  change the project ever gets. Serving,
  reloading, bringing the user's tab forward, the two-minute self-cleanup and teardown
  are all in `references/liveview.md`. Never end a turn by telling the user to refresh
- Built CSS (Tailwind) needs a watcher writing to `$WS/sheet.css`, or new class names
  won't show: `references/stylesystems.md`

## Ending

**Selection is the apply order.** A clear chat choice authorizes applying the selected
value to the current target in the same turn — no second approval. An anchor remains a
starting point, not an apply order. If the user asked to compare or record only, defer.

**I never apply it myself.** Record → check the actual blast radius → decide the scope
→ end the turn with the handoff. The main agent edits the code and verifies it. If the
target source is unavailable, say what is missing instead of writing a handoff.

Default to the current target: reuse an existing token, or make a local override when
changing a shared token would affect unrelated components. Change a shared token only
when that broader scope is already authorized. Ask only if a necessary scope decision
can't be resolved from the request.

The final message tells the user, in Korean, what was chosen, its blast radius and the
`확인 못 한 곳:` line when there is one. Then it ends with the block for the main agent:

    반영 지시:
    - 확정: 그림자 블러 = C · 12px
    - 고칠 곳: src/components/Card.tsx:24 `shadow-md` → `shadow-[0_4px_12px_rgb(0_0_0/0.12)]`
    - 범위: 이 카드만. `--shadow-md` 는 그대로 둔다 (다른 사용처 23곳)
    - 함께: `prefers-reduced-motion: reduce` 분기 (references/motion.md)
    - 검증: Card 의 computed `boxShadow` 가 위 값인지

Everything from `반영 지시:` on is for the main agent; the user never sees it. Give
exact files, lines, the current text and the new text, so it can edit without searching
again. Leave out `함께` and `검증` when there is nothing to add.

The main agent's next message starts with `반영 완료:` and the files it changed, or says
what failed. The changed code is now the baseline: read it before drawing on top of it.

Applying is not the end. Keep the sheet and server until the user has checked the real
code and says it is done (`끝났어` · `됐어`; `이걸로 가자` is a choice, not that). Then
run the teardown in `references/liveview.md`, which also checks `git status` for stray
comparison files.

**Only what was explicitly chosen goes into the handoff.** An alternative merely
mentioned along the way is not a decision.
