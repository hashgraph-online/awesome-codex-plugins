---
name: memory
description: "Find or curate supported lessons and agent rules. Use when: asked to remember, trace a corrected claim, audit instructions or write an agent rule."
practices:
- evidence-based-engineering
- continuous-learning
hexagonal_role: supporting
consumes: []
produces:
- applicable-context
- reviewed-topic-pages
- ranked-toil-evidence
context_rel: []
skill_api_version: 1
user-invocable: true
metadata:
  graph_root: true
  tier: execution
  dependencies: []
  capabilities: [recall_applicable_context, mine_supported_observations, curate_topic_pages, toil_mining]
  effects: [write_protected_drafts, update_authorized_topic_pages, write_requested_toil_report]
  canonical_status: canonical
  disposition: keep_off_path
output_contract: 'bounded applicable evidence or no-match; reviewed topic-page updates or no-change; ranked toil evidence with support, limits and unresolved gaps'
---

# Memory

Use maintained experience only when it changes an action. Memory is optional:
no mandatory recall at RPI entry, lesson at completion, worksheet, page quota or
background mining. A trivial edit can proceed directly to implementation.

## Rules for any saved lesson or rule

Apply these whenever a request would save or promote a lesson, including a
request to turn an incident into a rule for an instruction file:

1. **Look for an existing entry first.** Search the selected `.context/` pages,
   external topic pages or the target instruction file (`AGENTS.md`,
   `CLAUDE.md`, a team rules file). Amend the entry that already covers the
   behavior; add a new one only when none fits. If the final code, tests,
   comments or a doc already explain the reasoning, point there rather than
   save a copy; save only what they cannot show a later reader, such as
   ruled-out causes, why the fix works and what brings the failure back.
   Effort, a finished task or a large diff never qualifies a lesson. If nothing
   qualifies, save nothing and say why.
2. **Size the claim to its evidence.** One incident supports a narrow
   observation scoped to the conditions it actually had. A universal rule needs
   repeated independent occurrences and later reapplication. When a recurring
   correction is a mechanical slip that a lint rule, test or hook could catch,
   propose that check alongside the prose rule or in its place, as
   [Postmortem](../postmortem/SKILL.md) does for such a miss; a check fails
   where a rule can only ask.
3. **State all five fields:** applicability, action, support, limits and invalidation.
   Use the template below; an entry with no invalidation is incomplete. For an
   incident, applicability includes the exact error text or observable symptom,
   the words a later search will use. An instruction file such as `AGENTS.md`
   loads into every session, so its entry is usually one line: the action and
   when it applies, worded as information rather than an order to read, linking
   the project `.context/` page or the doc beside the governed code (never an
   external-bundle page from a checked-in file) that carries all five fields. A
   line that only restates what agents already do by default earns no place.
4. **Review before admission.** Give the draft inline in your reply unless the
   caller named storage outside Git; never write it into the repository before
   review. A fresh reviewer who is not the author checks factual support and
   disclosure of the exact text, paths and destination before it enters
   `.context/`, an instruction file such as `AGENTS.md`, or any Git object.
   Promoting an entry into an instruction file is a separate policy change
   owned by that file. On an explicit request to remember something, the
   runtime's own memory store (such as Claude Code auto-memory or Codex memory)
   is a valid destination; rules 1-3 still apply, and fresh review is owed only
   when that store is shared or checked in.
5. **Saving proves nothing.** Saved pages, retrieval counts and structural
   checks prove no benefit. Only later work can show that reuse changed an
   action and helped; keep failed, harmful and no-change results. Until then a
   saved rule is an untested hypothesis.

```markdown
### <one-line claim>
- Applies when: <the conditions the evidence covered>
- Action: <the check or step to take>
- Support: <cited sources; number of independent occurrences>
- Limits: <where it is untested or may not hold>
- Invalidate when: <the change or contrary evidence that retires it, and how to check it>
```

Keep rare useful constraints; age or low frequency alone is no reason to delete
them. Learning may also simplify or remove rules.

## Choose one operation

| Need | Read on demand |
|---|---|
| An earlier constraint or source map may change the next action | [Find / recall](references/recall.md) |
| Capture useful evidence from selected sources, episodes or corrections | [Capture / mine / learn](references/mine-learn.md) |
| Update, qualify, consolidate or retire a supported claim | [Curate / qualify / retire](references/curate.md) |
| Rank repeated operational friction in supplied history | [Toil evidence](references/toil.md) |
| Trace a corrected claim or audit the loaded instruction set | [Instruction sources](references/instruction-sources.md) |

Memory owns these operations. Whether recurring evidence warrants a general
rule is decided by [Research's pattern mode](../research/SKILL.md#pattern-evidence)
(independent exemplars and a holdout). Capture includes bounded source maps,
verdicts, corrections and failed or harmful reuse; it is never a required
completion step. Load only the selected operation's reference. The optional
[OKF page profile](references/learn/okf-page-profile.md) checks structure only.

## One authority per fact

BD or the caller's tracker owns work and handoffs, Git owns content history,
and native sessions or CASS own episodes. Reviewed topic pages in a project
`.context/` or an external bundle hold reusable claims and point to the docs,
ADRs and code that own a policy instead of copying it. Do not make one lesson
file per session, copy a transcript lake, or silently initialize a memory
store. Read a project `.context/` from its `README.md` map, when present, with
`rg` and `cat`; this needs neither BD nor AO and creates nothing. External bundles and the
`ao config context` route are in [Find / recall](references/recall.md).

## Access, storage and honest limits

Use only sources already authorized for the task, owner, model/provider and
exact destination; read permission does not imply publication or Git storage.
This path supports **public or already-cleared trial inputs only** and enforces
no restricted-source access, so do not retrieve restricted material through it;
`ao session read-source` grants no broader transcript access. Unavailable and
denied evidence remain explicit gaps; do not fetch then redact. Drafts and
review proof go inline in your reply or to storage outside Git that the caller
named; missing routing does not authorize a workspace fallback. Preserve
requested legacy `.agents/` proof and unique evidence under owner policy.
No blind TTL or delete operation is part of Memory. Labels and structural
parsers do not prove isolation. In a repository checkout,
`docs/adr/ADR-0016-state-tiers.md` owns these boundaries. Mining is budgeted
separately and cannot delay an authorized change or alter its verdict.
