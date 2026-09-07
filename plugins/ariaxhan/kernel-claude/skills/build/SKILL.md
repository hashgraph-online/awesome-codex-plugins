---
name: build
description: "Solution exploration and implementation. Generate 2-3 approaches, pick simplest. Never implement first idea. Triggers: build, implement, create, feature, add."
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, Task
kernel:
  kind: methodology
  version: 1
  side_effects: none
  confirmation: none
---

# BUILD SKILL

Prerequisite: run `agentdb recall` with the feature, subsystem/library, known files or
symbols, and desired outcome. Run it again after repository inspection reveals better
paths/symbols or the scope changes. Reference on demand: skills/build/reference/build-research.md.

## Goal first

Before touching code, state: GOAL, CONSTRAINTS, INPUTS, OUTPUTS, DONE-WHEN. If any
field is genuinely unknowable, the feature is underspecified; run the interview below
and write the spec to `_meta/plans/` before implementing. State the DONE-WHEN criteria
at the start of the session, not the end.

## The interview

When a feature is underspecified, interview the user with the AskUserQuestion tool
rather than guessing or asking one vague open question. Cover, in order of leverage:

1. Intent: which of 2-3 plausible readings of the request is meant.
2. Implementation shape: the genuine forks (storage, framework, integration boundary)
   where the user's answer changes the build.
3. UI/UX: only the decisions the user would veto if guessed wrong.
4. Edge cases and failure behavior: what should happen when input is empty, huge,
   concurrent, or malicious.
5. Tradeoffs: name the axis (speed vs completeness, flexibility vs simplicity) and let
   the user place the slider.

Rules, enforced by taste:
- Interviews are for bounded choices with real options. Open-ended strategy and design
  direction stay prose conversation, never option polls.
- Every question must change what gets built; if all answers lead to the same code,
  don't ask.
- Offer a recommended option first when the evidence supports one.
- Batch related questions (the tool takes up to 4); one interview beats five
  interruptions.
- The answers land in the spec at `_meta/plans/<feature>.md` (or the active commission),
  quoted, so the authority behind each decision is traceable.

## Research cache

Check `ls _meta/research/` for a topic match before any web search. Each cached doc
carries frontmatter (`query`, `date`, `ttl` in days); fresh hit means skip the search,
stale or missing means search and write the result back with frontmatter. Rough TTLs:
anti-patterns 7, framework docs 30, package versions 3, architecture 30.

Research without verification is theory fiction: build a 10-line proof of a cached
finding before committing to it across the codebase. AgentDB learnings are never
cached; check them separately after the cache.

## Verify assumptions, don't guess them

Confirm against the actual repo before writing: tech stack and versions, where the
code should live, naming conventions in neighboring files, the existing error-handling
pattern, the test framework, and whether a needed dependency is already present.
An external API you haven't grepped in-repo gets resolved through installed package
source or official docs, never from memory.

## Explore 2-3 approaches, pick the simplest

Never implement the first idea. For each candidate note: approach, rough lines of
code, dependencies (and how battle-tested they are), and complexity. Choose by, in
order: minimal code, battle-tested package over novel one, fewest edge cases, active
maintenance, performance only if a bottleneck actually exists.

Write the chosen approach + rejected alternatives to `_meta/plans/{feature}.md`, under
50 lines. Skip the plan entirely when the diff can be described in one sentence.

## Execute

Smallest viable change, following existing patterns, one commit per logical unit.
Before each unit ask whether fewer lines would do; after it, verify it works and
commit. Tier 2+: you are working a contract; touch only contract-listed files.
Keep sessions scoped to one feature or one bug, and if the same mistake happens
twice, stop and restart with a refined prompt instead of a third try.

## Validate, then done

Run what the project configures: tests, lint, types. Walk the DONE-WHEN criteria and
cover at least 3 edge cases (empty/null, boundary, error path). Evidence first: paste
the actual command output, not "seems to work."

"Done" = verified live, not committed. Committed, pushed, deployed, and working are
four different states; run a command that confirms the real one (deploy check, curl
the served asset, the passing test, the exercised code path) before claiming done.
If it can't be checked headlessly, say "deployed, your check," never "it works."

On failure: stop, check the research doc for the error, apply a documented fix if one
exists, otherwise roll back to the last good state and ask whether a simpler approach
was missed. A solution that keeps feeling complex is usually the wrong approach, not
an implementation problem.

<on_complete>
agentdb write-end '{"skill":"build","feature":"X","files":["Y"],"approach":"Z"}'
</on_complete>
