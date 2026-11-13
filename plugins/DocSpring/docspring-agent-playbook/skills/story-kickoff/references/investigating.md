# Investigating a ticket in bounded areas

Step 2 of the full path in [`../SKILL.md`](../SKILL.md): how big to make the investigation, the standard areas, and how
to brief and delegate to investigators.

## Right-size it

- **Default: do it yourself, or use one or two investigators.** Use more only for a broad change with real risk, and
  never more than one investigator per area that needs investigating.
- **A small behavior fix (one function, one caller): do K1, K3 and K4 yourself** in a single written pass, without
  delegating. A change with no behavior effect at all takes the short path in `../SKILL.md` instead.
- **A brief is a short list of specific questions with a stop condition and a length cap.** Name what to leave alone
  ("don't read test helper internals", "don't reproduce the build"). Say when to stop ("stop once each question has
  an answer") and how long the answer should be ("a few findings, under a page").
- **Never write "be thorough", "every" or "exhaustive" into a subagent brief.** Investigators given open-ended briefs
  like that run for many minutes and come back with surveys of side paths nobody needed.
- **Dependency, OS and runtime upgrades:** the investigation is the release notes for each version in the jump, plus
  a list of your call sites for anything with a risky change. Let the build and CI catch renamed packages and compile
  errors instead of reproducing them up front.

## Areas

Pick the ones that apply and add ticket-specific ones. Name the investigated HEAD and the comparison base in every
brief and every handoff.

- **K1 Root cause and blast radius.** Verify the ticket's diagnosis in the investigated code. Find the callers and entry
  points that reach the code (web, API, admin screens, background jobs, scheduled tasks, scripts, imports and
  exports, data migrations, client code, SDKs), and the same class of bug elsewhere in the codebase.
- **K2 Existing data.** What stored rows, files and caches look like today, whether some are already wrong because of
  the bug, and whether the fix needs a repair (which, under "the smallest complete change", is the user's call) or a
  read-only production check first. Note your schema rules (which columns may be dropped, and when).
- **K3 Behavior contracts.** Who relies on today's behavior: customers (promises found in step 1), the public API
  and its spec, SDKs and other clients, stored client state (saved settings, subscriptions, cached IDs), webhooks,
  embedded widgets, docs pages and marketing copy, and every region and self-hosted install that runs the code. A
  behavior change outside the ticket's scope is listed here, never slipped in.
- **K4 Test plan.** The existing tests that cover the area, what each new test must prove, the level it belongs at
  (unit, request, browser), and the concrete way each regression test fails on the parent commit. Check the traps in
  the "Tests" section of [lessons.md](lessons.md#tests).
- **K5 Failure handling, security and performance**, when the ticket touches external calls, authentication, tokens
  or permissions, billing, generated output, data deletion or large tables.

## Delegating

The investigator is defined in [`../agents/kickoff-investigator.md`](../agents/kickoff-investigator.md). In Claude Code,
copy it to `.claude/agents/` and launch it by its name. In other harnesses, paste the file's body (below the
frontmatter) at the top of a general-purpose subagent's prompt. Launch one investigator per area, all at once, and give
each:

- the workspace path, the investigated HEAD (and whether uncommitted changes count), the comparison base and the
  path to `kickoff.md`
- the area ID and its brief
- the first finding number to use (K2 starts at `K2-F01`)
- the instruction to return its handoff to you. Investigators write no files; you save each handoff as
  `investigations/K2-findings.md`.

A brief, for example:

```
K3 Behavior contracts. Questions:
1. Which API responses include the `status` field this ticket renames? List the serializers.
2. Do the SDK templates or the docs pages name the field?
3. Does any client store the old value (webhook subscriptions, saved filters)?
Leave alone: test helpers, the admin screens. Stop once the three questions have answers.
Answer in under a page.
```

Without subagents, work through the areas yourself one after another, writing each area's handoff before starting
the next. Don't describe that as parallel or independent in the plan or the PR.

Investigators don't run tests that share state. They list the commands they'd run under "Proposed verification", and
you run those one at a time.

When the handoffs are back, read each one against the code before relying on it: an investigator's mistakes come back
in the same confident tone as its findings.
