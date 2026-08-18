# Skill Authoring Doctrine

Principles for writing `SKILL.md` bodies so an agent follows the same
*process* on every run. Structure (frontmatter, sections, output contracts)
lives in [skill-template.md](skill-template.md) and
[audit-checks.md](audit-checks.md). This reference governs the sentences
inside that structure. The deep audit's advisory `authoring` block
(see [audit-checks.md](audit-checks.md)) mechanically flags three detectable
failure modes; everything else is author judgment.

Idea provenance: distilled clean-room from the skill-authoring ideas at
<https://github.com/mattpocock/skills> (MIT). Concepts only — no upstream
prose, names, prompts, scripts, or examples are reproduced here.

## 1. The no-op test

A sentence belongs in the skill only when it alters what the agent would
otherwise do. Vague intensifiers such as "be thorough" fail: they spend
tokens without changing the default. Prefer a concrete, observable
instruction ("read every `references/*.md` before editing") or a single
strong pretrained cue the model already knows how to obey.

Whether a line is load-bearing depends on the model. Authors who disagree
should settle it by executing the skill, not by debating intent. Because of
that relativity, the audit's `noop-phrase` finding is advisory: it names
suspects from a fixed phrase list; the author decides.

## 2. Negation

Telling the agent what to avoid tends to surface the forbidden pattern in
context and raise its salience. Prefer naming the desired behavior
("write one-line comments") so the unwanted pattern is never primed.

Hard bans remain valid when nothing positive can replace them (this
repository's ban on `claude -p` is one). Even then, put the recovery path
in the same paragraph — ban plus what to do instead — which matches this
repo's "Anti-pattern: X. Corrective: Y" habit. The audit's
`negation-without-positive` finding flags a paragraph where every clause
forbids and none directs.

## 3. Completion criteria

End each workflow step on a condition the agent can evaluate, and make that
condition cover the whole obligation. Two properties matter:

- **Checkable** — done vs not-done is decidable. "Understanding reached" is
  not; "every changed path appears in the manifest" is.
- **Exhaustive** — the bar covers the full duty. "Produce a change list"
  allows a partial list; "every modified file accounted for" does not.

A fuzzy exit invites *premature completion*: attention drifts from the work
to finishing, and the step ends early. Tighten the exit criterion before
restructuring the skill — that is the cheap local fix. The audit's
`step-missing-done-condition` finding flags workflow subphases that lack any
done phrasing ("Done when", "Checkpoint:", "Stop after", "until … exit 0").

## 4. Leading words

A leading word is one pretrained concept token that holds a behavioral
region: *tight* (loop), *red* (failing check), *fresh* (context),
*frontier*, *quarantine*. Used as a token — not re-explained each time —
it builds a shared meaning across the skill and leans on priors the model
already has, buying behavior for almost no context cost.

Look for restated qualities that want collapsing: three near-synonyms for
"fast and deterministic" are one idea; *tight* says it once. Invented terms
need a single clear definition; pretrained words are free. A leading word
that does not beat the model's default is itself a no-op — strengthen the
word rather than adding more prose.

## 5. Description discipline

The frontmatter description loads every turn, so prune it hardest. It has
two jobs: name what the skill does, and list genuinely distinct trigger
branches. One trigger per branch — synonym padding for the same branch is
duplication that burns context and dulls matching. Prefer trigger wording
callers actually use, especially shared leading words, so the description
aligns with real prompts. This sharpens, rather than replaces, the
structural `description-has-triggers` and `trigger-clarity` checks.

## 6. Context load vs cognitive load

Every skill bills one of two accounts. A model-discoverable skill keeps its
description in the window every turn — a standing **context load** whether
or not it fires. A human-only skill costs nothing per turn but spends
**cognitive load**: the human indexes which skills exist and when to call
them.

Choosing the account is a required authoring decision. This repository
already exposes the levers: `user-invocable` frontmatter, `tier` and
`disposition` metadata, and the generated router (`docs/SKILL-ROUTER.md`)
that reduces cognitive load once human-reached skills multiply. Prefer
model discovery only when autonomous reach or cross-skill invocation is
required; otherwise keep the window clean. Splitting one skill into several
also spends one of those loads — split only when a distinct trigger
vocabulary or independently reachable behavior pays for the new entry.

## Applying the doctrine

When creating or healing a skill, walk the body once per principle: remove
no-op lines, convert bare bans into positive targets (keeping paired
guardrails), give each workflow step a checkable exhaustive exit, collapse
restatements into leading words, prune the description to one trigger per
branch, and confirm the intended load account. The advisory `authoring`
audit block names the mechanical suspects; the author owns the judgment
calls.
