---
name: start
description: One command from "plugin installed" to "running brief on your idea." Combines /mycelium:setup (project-state initialization) and /mycelium:interview (10-minute discovery brief) into a single flow. Run this immediately after installing the Mycelium plugin — it's the recommended entry point for first-time users.
metadata:
  framework_dependency: "mycelium"
  framework_dependency_note: "This skill is designed to run within the Mycelium framework (https://github.com/haabe/mycelium). Standalone use will skip the canvas state, theory gates, and harness behavior the skill assumes. Install: /plugin install mycelium@haabe-mycelium."
---

# /mycelium:start — combined first-time entry

When this skill runs, follow the flow below. The skill is designed so a first-time user goes from "plugin installed" to "holding a one-page brief on their idea" in a single invocation.

## Step 1: Welcome (~30 seconds of context, then move on)

Output a short welcome before doing anything. Do NOT skip this — the install-to-here gap is the friction point this skill exists to address. The user just installed a framework with dozens of skills and has no context yet.

> "Welcome to Mycelium.
>
> Mycelium makes the agent think before it builds — it can't skip the hard questions; each step has to clear an evidence check first. Grounded in 30+ established product-thinking frameworks; you'll meet the relevant ones as they come up.
>
> Two quick steps:
>   1. Set up Mycelium's files in `.claude/` — about 10 seconds. Your existing files (CLAUDE.md, README, etc.) aren't changed. A new `.claude/` directory is added, and setup may add an `AGENTS.md` at the project root (it asks first when you are there to answer).
>   2. A 10-minute discovery brief: one line about the project, 4 questions about your idea, then a one-page brief covering who it's for, the biggest assumption, the biggest risk, and your next concrete move.
>
> One thing to know before you answer: once the brief exists, the agent builds the product itself only after a delivery diamond is open with its reasons written down, new files and edits to existing code alike. Code in a folder listed under `prototype_paths` in `.claude/diamonds/active.yml` stays free, and you can lift the hold yourself with `.claude/state/delivery-skip-ack`. Uninstalling is one command.
>
> Let's begin."

## Step 2: Detect existing state — HARD GATE

**This must be the very first action after the welcome. Do NOT run any other Bash commands, Edit/Write operations, or "let me prepare the directories" reasoning before this gate fires.**

Run exactly this check, and only this check:

```bash
test -f "${CLAUDE_PROJECT_DIR:-.}/.claude/diamonds/active.yml"; echo "state=$?"; find .claude/state/hooks-alive "${TMPDIR:-/tmp}/mycelium-hooks-alive-$(id -u)" -mmin -60 2>/dev/null
```

(`${CLAUDE_PROJECT_DIR:-.}` since v0.286.0: Codex CLI does not set the variable, and the bare form
tested `/.claude/...`, so an initialized project read as new and setup ran over it.)

- **Hooks (v0.286.0)**: if the `find` printed nothing, Mycelium's hooks did not run in this
  session: its gates and the rules it gives the agent at session start are off, and nothing else
  will say so. Tell the user in one line before going on: "Mycelium's hooks are not running in
  this session, so its gates are off. On Codex CLI, open `/hooks`, trust Mycelium's hooks and
  start a new session; on Claude Code, check the plugin is enabled in `/plugin`." Then continue
  with the state result below. If it printed a path, say nothing about it. (Since v0.318.0 the hooks do nothing in a project with no `.claude/canvas/` or `.claude/diamonds/`; there they only stamp the temp-folder marker, which is why the `find` names both.)

- **If `state=0`** (file EXISTS): the project already has Mycelium state. Skip directly to Step 4 routing output. **Do NOT run setup. Do NOT run mkdir. Do NOT touch `.gitkeep` stubs.** Setup-style operations on an already-initialized project waste tokens and trigger Read-before-Write tool errors when the agent then tries to write to existing files. Detected during 2026-05-09 plugin-form dogfood — the agent ran `mkdir -p .claude/...` before honoring this gate, then hit a Write error on `active.yml` and only then realized the project was initialized. The fix is structural: the gate is the first action.

- **If `state=1`** (file does NOT exist): invoke the setup workflow inline. Follow the instructions in `${CLAUDE_PLUGIN_ROOT}/skills/setup/SKILL.md` exactly — same Step 1 detection (which will fall through), Step 2 directory creation with `.gitkeep` stubs, Step 3 starter file writes, Step 5 confirmation message — **but DEFER setup's Step 4 (the AGENTS.md prompt) to after the brief** (see below). Do not duplicate the setup logic here; reference it.

**AGENTS.md deferral (v0.56.0)**: in the /start composition, setup's Step 4 question does NOT fire before the interview. A first-time user's opening minutes must go to their idea, not to file administration — the 2026-07-02 roadmap dogfood run showed the AGENTS.md exchange consuming the first two conversational rounds before Question 1 was asked. Instead: after the brief is rendered and the depth menu is answered, IF `<project_root>/AGENTS.md` is absent or lacks a Mycelium section, ask setup's Step 4 question then (one exchange, at the natural pause). Setup's detect-first rule still applies: an AGENTS.md that already covers Mycelium is skipped silently. When `/mycelium:setup` is run standalone (not via /start), its Step 4 order is unchanged.

After setup completes, do NOT print setup's "Next:" line — this skill is the next step. Print:

> "Setup done. Now: one line about the project, then 4 questions about your idea, ~10 minutes."

## Step 3: Run interview (universal-flow shape)

Invoke the interview workflow inline. Follow the instructions in `${CLAUDE_PLUGIN_ROOT}/skills/interview/SKILL.md` from Phase 0 onward.

Because setup just ran, the canvas is empty — /interview's canvas-state detection will route to the Universal Brief Flow (the 4-question brief shape, not the legacy time-budget-routed ceremony). Render the brief, write canvas state, render the depth menu. Per opp-006 narration discipline in interview/SKILL.md, do not narrate phase numbers to the user — reference the outcome (e.g., "the brief", "the project-type question") instead of the phase index.

**Where the product lives (v0.270.0).** Before the depth menu, ask in one line where the product's
own files will live and record the answer as `product_paths` at the top of
`.claude/diamonds/active.yml`: `app/` for software, `pilot/` for a service's documents, `course/`
for lessons, `manuscript/` for a book, or `[]` if the product is code only. The delivery gate knows
code by its extension and everything else only by this: a bookkeeping service in the E2E second
world wrote its whole client pack under an L0 in discover and nothing noticed. If the user does not
know yet, leave it; the next session start asks again.

After the brief is rendered and the user picks a depth-menu option, the start skill is done. Hand off to whatever the user chose (`/mycelium:assumption-test` for "Test the biggest assumption", a prototype folder for "Build a prototype to learn", continued discovery for "Go deeper", a graceful exit for stopping, etc.).

## Step 3b: Derive purpose properties (immediately after why/how/what land)

**The why/how/what are not decoration — everything below is checked against them, so they have to be
checkable.** Propose a property list from what the user just wrote, then have them confirm it. Write
to `purpose.yml#purpose_properties`. Full contract: `docs/purpose-stance.md`.

**For each element, ask yourself: can I name a specific solution that would CONTRADICT this?**
- Yes → it is a candidate property. Record `verbatim`, `source` (why/how/what), and the contradicting
  solution in `contradicted_by`.
- No → **do not force one.** Quality adjectives ("secure", "accessible", "fast", "simple") yield
  nothing checkable, because every candidate solution claims to satisfy them. Measured 2026-08-23:
  "accessible and secure" produced no checkable property at all.

**When a word fails, ask the user — and offer candidates rather than an open question:**

> You said "secure". Which of these would you call a violation?
> (a) passwords stored in plaintext (b) no transport encryption (c) sessions that never expire (d) something else

**Recognition is cheap; generation is not.** If they answer, you have a property. **If they cannot,
record it as an aspiration** (`aspiration_reason`) and say plainly: *"'secure' stays undefined, so no
solution will be checked against it."* A skip is a recorded choice, never a blank.

**The user marks `binding: true` on the few whose violation would break the product.** Only those are
ever checked. Set `confirmed_by: human` once they have.

**This is NOT `/mycelium:user-interview`.** That skill asks about specific past behaviour, which is
right for discovering user needs and wrong here — this elicits a definition from the builder about
their own intent, where the question is hypothetical by design.

## Step 4: Routing for already-initialized projects

If Step 2 detected existing canvas state (the user has Mycelium installed already on this project), do NOT run setup or interview. Instead, print:

**If the project has canvas state but no `purpose.yml#purpose_properties`, say so in the same
breath** — it existed before v0.120.0, so nothing below has ever been checked against its own
why/how/what, and `/mycelium:purpose-properties` is the retrofit. One line, not a sales pitch.

> "This project already has Mycelium state from [date of last write to .claude/diamonds/active.yml]. Last diamond touched: [scale, phase, confidence, name]. Three options:
>   1. Run `/mycelium:diamond-assess` to see current state and what to work on next.
>   2. Run `/mycelium:interview` to add a new idea as a sibling diamond on this product.
>   3. Stop and look around. Canvas files are in `.claude/canvas/`."

Then exit. The user picks the next move.

## What this skill does NOT do

- Does NOT modify CLAUDE.md, README.md, CONTRIBUTORS.md, or LICENSE.
- Does NOT block or prompt at the welcome step — it's read-and-continue, not interactive.
- Does NOT replace setup or interview. They remain invocable directly. start is the convenience composition.
- Does NOT run on every session — only on first invocation. After the first run, canvas state exists and Step 2 routes to diamond-assess.

## Why this skill exists

Without `/mycelium:start`, the first-time plugin user has to:
1. Run `/plugin install mycelium@haabe-mycelium` (Claude Code message: "installed")
2. Wonder what to do
3. Find `/mycelium:setup` (no obvious pointer at install time)
4. Run setup (gets a brief next-step message)
5. Run `/mycelium:interview`
6. Get value (the brief)

That's 5 typed commands and 2 cognitive gaps before value lands. The void between steps 1 and 5 is real friction.

`/mycelium:start` collapses 1→6 into 1→2 with a welcome message that gives the framework a 30-second introduction at exactly the moment the user has the question "what is this and what do I do." Setup+interview both still exist as separate skills for users who want them piecewise.

## Theory grounding

- Norman: visible affordances at the moment of cognitive need (the welcome message at the install gate).
- Krug "Don't Make Me Think": one command instead of two, with explanation built in.
- Hashimoto regeneration zones: the welcome is generation-cheap context that the user can re-read or skip; doesn't add discipline cost to the actual work.
- Brownfield-additive principle (Bentes 2026-05-08): the start skill respects the same "no project root modification" constraint as setup — it adds project state without touching user-owned root files.

## Source

The friction this skill addresses surfaced 2026-05-09 during the founder's smoke-test of the v0.20.x plugin form. The user reported: "the onboarding has worsened substantially since converting to plugin. The user is left in the unknown void for quite a bit."

Setup + welcome + immediate interview transition is the first response. If the welcome-as-text approach proves insufficient (subsequent dogfood reports the void persists), graduate to: SessionStart hook that detects first-run-after-install and emits the welcome unprompted.
