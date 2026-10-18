---
name: memory
description: 'Write, find or curate lessons and agent rules with stated evidence and limits. Use when: asked to remember something or write a rule into agent instructions.'
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
   behavior; add a new one only when none fits.
2. **Size the claim to its evidence.** One incident supports a narrow
   observation scoped to the conditions it actually had. A universal rule needs
   repeated independent occurrences and later reapplication.
3. **State all five fields:** applicability, action, support, limits and invalidation.
   Use the template below; an entry with no invalidation is incomplete.
4. **Review before admission.** Draft outside Git. A fresh reviewer who is not
   the author checks factual support and disclosure of the exact text, paths
   and destination before it enters `.context/`, an instruction file such as
   `AGENTS.md`, or any Git object. Promoting an entry into an instruction file
   is a separate policy change owned by that file.
5. **Saving proves nothing.** Only later work can show that reuse changed an
   action and helped. Until then a saved rule is an untested hypothesis.

```markdown
### <one-line claim>
- Applies when: <the conditions the evidence covered>
- Action: <the check or step to take>
- Support: <cited sources; number of independent occurrences>
- Limits: <where it is untested or may not hold>
- Invalidate when: <the change or contrary evidence that retires it>
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

Memory owns these operations; other roles link here instead of keeping their
own procedures. Capture includes bounded source maps, verdicts, corrections and
failed or harmful reuse; it is never a required completion step. Load only the
selected operation's reference. The optional
[OKF page profile](references/learn/okf-page-profile.md) checks structure only.

## One authority per fact

BD or the caller's tracker owns work, status, dependencies and handoffs; Git
owns content and delivery history; native sessions and CASS own episode
evidence. Reviewed Markdown topic pages in a selected project `.context/` or an
external bundle hold reusable claims as evidence, not another work account.
Existing docs, ADRs and code keep their declared authority; a page points to
those owners instead of copying their policy. Do not make one lesson file per
session, copy a transcript lake, or silently initialize a memory store.

For a selected project `.context/`, start at its small authored `README.md` map
when relevant, then read likely pages and their current source owners with
ordinary filesystem tools such as `rg` and `cat`; this needs neither BD nor AO.
Reads create no directory, index or private import. The optional
`ao config context` route supports external bundles and an explicitly bound
canonical direct `<consumer>/.context`; it requires native BD and preserves the
policy and identity bindings. Other consumer-overlapping roots remain refused.

## Access, storage and honest limits

Use only sources already authorized for the task, owner, model/provider and
exact destination. Read permission does not imply publication or Git storage.
This lean path supports **public or already-cleared trial inputs only**. Neither
this skill nor a prompt, worktree or same-user shell enforces restricted-source
access, so do not retrieve restricted material through this path. The existing
`ao session read-source` supported profile grants no broader or automatic
transcript access. Unavailable and denied evidence remain explicit gaps; do not
fetch then redact.

Drafts and review proof stay in caller-selected protected external non-Git
storage. Missing routing does not authorize a workspace fallback. Preserve
requested legacy `.agents/` proof and unique evidence under owner policy.
No blind TTL or delete operation is part of Memory. Labels and structural
parsers do not prove isolation. `docs/adr/ADR-0016-state-tiers.md` owns these
boundaries in a repository checkout; the operation references carry the
installed rules.

Saved pages, retrieval counts and structural checks prove no benefit. Only later
work can demonstrate that reuse changed an action and helped its outcome; keep
failed, harmful and no-change results. Mining is separately budgeted off-path
and cannot delay finishing an already authorized change or alter its verdict.
