# migration-elicit.md — Phase 2 ELICIT (project-wide extraction)

Collect what the code cannot reveal — across the **whole project**, not a single task. This is
independent of `ready`'s `elicitation.md`: that one is task-focused; this is project-wide, with its
own question scope, strategy, and completion bar. The only thing shared is the asymmetric-depth
principle (extract domain, present technical).

**Floor, not ceiling.** This is not a script. The guardrails and the depth floor below are the
floor; how you run the conversation is yours. Never hardcode questions or stack choices.

**Calibrate to the project's character first.** Right-size the conversation to what the project *is* —
a 200-line CLI and a 200k-line multi-domain platform do not earn the same depth. Read scale, domain
density, and surface area from SCAN, then spend deep extraction where the domain is core and a light
confirm where it's peripheral (right-sized, effort-proportional). Don't run uniform full-depth
ceremony on a trivial repo, nor a light pass on a domain-heavy one. (State the read in prose, not a
grade — a grade becomes a ceiling.)

## The core frame — self-infer first, ask deeply only where being wrong is dangerous

You have just read the code (SCAN). Use it. Don't ask what the code already answers; do confirm what
would be catastrophic if your inference is wrong. Four cases:

| Inferable from code? | Wrong is dangerous? | Action |
|---|---|---|
| yes | no | infer, brief confirm ("is this right?") at most |
| yes | **yes** | present your inference, **confirm deeply** (domain rules, invariants) |
| no | **yes** | **ask deeply** (business model, policy decisions, security policy) |
| no | no | apply a default, skip the confirm |

The load-bearing rule: **"areas where a false belief breaks the whole project" — the business model,
domain invariants, security policy — must be user-confirmed even when the code lets you infer them.**
Code can show *what* the auth check does but not *whether it is the whole policy*; it shows a state
field but not *which transitions are forbidden by the business*. Technical WHY and conventions, by
contrast, need only a light confirm when the code answers them.

**A thin / undocumented codebase RAISES the bar — it does not lower it.** Sparse code is migration's
most common *and most dangerous* input: least to infer from, most that lives only with the user. "The
code didn't tell me much" is never a license for a thin harness — it means **ask more, mine the user
harder.** A hollow harness from a sparse codebase is the exact failure migration exists to prevent.

**Ask grounded questions, not spray.** A confident question can state its **site** (the exact module /
rule / policy), **why the code doesn't already answer it**, and the **consequence** of getting it
wrong. Can't ground all three? Don't press it as blocking — vague "is something missing?" spray
fatigues the user and erodes trust.

## The SCAN map is a ledger — every item must close (observable coverage)

SCAN produces a **manifest**: every entity/module, pattern, security surface, external dependency, and
*gap* (something a domain like this usually has, absent here). Treat it as a **ledger** — each item
must end ELICIT in exactly one **recorded** disposition, so completeness is a *scan over the ledger*
(evidence), not a "did I cover everything?" feeling (evidence-not-assertion):
- **confirmed** — its domain purpose / governing rule is user-confirmed.
- **asked-answered** — surfaced to the user and resolved.
- **N/A — reason** — genuinely not load-bearing here, with the reason recorded.

Drive a question from each open item (translate to the user's language, below):
- **entity/module** → purpose + governing rules (structural: what it owns/relates to; behavioral:
  lifecycle, who may act, what's forbidden).
- **pattern** → intentional convention, or incidental?
- **security surface** → is this the *whole* policy, or only part?
- **architecture** → why this structure? what did it rule out?
- **gap** → is the absence intentional, or not-yet-implemented?

No item is silently dropped — an un-dispositioned row is an open question, not a pass. (This is
migration's form of `ready`'s decision-surface accounting: the SCAN manifest *is* the surface.)

## Delivery — structured questions that never dead-end

When options are enumerable, prefer the platform's structured-input tool (2–4 options, recommended
first labeled `(Recommended)`, "Other" allowed); pure open questions stay plain text. Give each
structured question a **very short header/label (a word or two)** and keep option labels short — an
over-long header/label, or more options than the cap allows, makes the structured tool **reject the
call**. If the structured-input tool ever rejects or fails, **immediately re-ask the same question as
plain text** — never stall or dead-end on a tool error.

**For a DOMAIN (extract) question delivered as choices, an explicit open option is MANDATORY** — a
"none of these — here's mine" / "I have a different idea" choice *visible among the options*, not just
the platform's generic "Other". **The open option counts toward the 4-option cap** — so a domain choice
question carries **at most 3 substantive options + the open one** (4 total); if more substantive options
than that are in play, drop to **plain text** rather than overflow the cap (overflowing rejects the
call). Domain knowledge is the **user's**; your options are a *scaffold / recommendation*, never the
boundary of what they may answer — boxing a domain question into your options is the opposite of
extracting. A genuinely open domain question (where you can't even enumerate sensible options) is
better asked as **plain text**. (Technical *present* questions, where the option space is legitimately
yours, don't need the mandatory open option — there the recommendation is the point.)

## Translate code into the user's language (the user may be non-technical)

The user may not know developer terms. Don't ask "is this an invariant?" — ask "if this changes,
must something else change too?" Don't ask "what's the authorization model?" — ask "who is allowed
to do this, and who must be blocked?" Translate the code context into the user's language, and
translate their plain-language answer back into the precise rule.

## Existing-docs handling

Existing docs are **reference material**, not authority — they may be stale. Read them, then review
any existing CLAUDE.md/AGENTS.md **critically**: decide what to fold into the dryforge system, what
to drop (already covered by the new `docs/`, or wrong), and what to improve and re-state. Present
that review to the user — what goes where, what is dropped and why — and get approval before
generating.

## Don't fabricate

Extract domain knowledge; never invent it. If the user can't answer and the code can't settle it,
record it as an open question for the user — a fabricated domain rule sends every later agent
confidently wrong.

## Completion bar (observable — a scan over the ledger)

ELICIT is done only when **every SCAN-ledger item is dispositioned** (confirmed / asked-answered /
N/A-with-reason) — a *scan over the ledger*, not a feeling. In particular:
- **Business model & policy decisions: user-confirmed, never inferred** — a false belief here breaks
  the whole project (the load-bearing rule above).
- **No "I don't understand why this is here" survives in a dangerous area** (business logic, domain
  invariants, security) — such an item stays `open`, never silently closed.
- **For every business-logic piece, the "are there rules not visible in the code?" question was asked**
  — code shows the *implemented* rules; the unimplemented-but-intended ones live only with the user.

The ceiling is open — how you lead the conversation is yours; *what must be dispositioned* is not.

## Universality guard

Stack-agnostic. Every example above is an illustration of a *kind* of question, never tied to a
stack. What an entity, a convention, or a security policy looks like is whatever the project is,
discovered at runtime.
