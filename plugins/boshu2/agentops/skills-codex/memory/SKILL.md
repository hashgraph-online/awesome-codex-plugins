---
name: memory
description: 'Recall applicable reviewed topic pages or maintain them through separately budgeted mining, learning and curation. Triggers: "memory", "recall prior work", "mine and learn", "curate memory", "qualify or retire a lesson".'
---
# Memory

Use maintained experience only when it helps an actual task. Memory is optional:
no mandatory recall at RPI entry, lesson at completion, worksheet, page quota or
background mining. A trivial edit can proceed directly to implementation.

## Choose one operation

| Need | Read on demand |
|---|---|
| An earlier constraint may change the next action | [Recall](references/recall.md) |
| Learn from a bounded set of episodes, failures or corrections | [Mine / learn](references/mine-learn.md) |
| Update, qualify, consolidate or retire a supported claim | [Curate / qualify / retire](references/curate.md) |

`learn` remains a compatible optional entrypoint for the mine/learn operation.
Specialist miners and operationalization tools are optional, never hard edges.
Do not load all operation references just because Memory was selected.

## One authority per fact

BD or the caller's tracker owns work/status/dependencies/handoffs; Git owns
content and delivery history; native sessions and CASS own episode evidence.
The caller-selected reviewed external Markdown topic pages hold reusable claims,
not another work account. Search and update an existing topic page before making
a new one. Do not make one lesson file per session, copy a transcript lake, or
silently initialize a memory store. Source evidence is not policy.

A useful entry states **applicability, action, support, limits and invalidation**:
when it applies, what to do, the evidence, where it may fail, and what would
change or retire it. One incident supports a narrow observation, not a universal
rule. Stronger general rules need stronger independent/repeated evidence and
later reapplication. Keep rare useful constraints; age or low frequency alone
is no reason to delete them. Learning may simplify or remove rules.

## Access, storage and honest limits

Use only sources already authorized for the task, owner, model/provider and
exact destination. Read permission does not imply publication or Git storage.
This lean path supports **public or already-cleared trial inputs only**. Native
restricted-source enforcement is not implemented by this skill, a prompt, a
worktree or a same-user shell; do not retrieve restricted material through this
path. The existing `ao session read-source` supported profile does not grant
broader access or automatic transcript access. Unavailable and denied evidence
remain explicit gaps; do not fetch then redact.

Draft outside Git in caller-selected protected external staging. Obtain fresh
author-distinct factual-support and destination-disclosure review of the exact
payload before any Git object/index/stash or import. The caller selects storage;
missing routing does not authorize a workspace fallback. Preserve requested
legacy `.agents/` proof and unique evidence under owner policy. No blind TTL or
delete operation is part of Memory. Use the caller's supported protection and
recovery controls; labels and structural parsers do not prove isolation.
`docs/adr/ADR-0016-state-tiers.md` owns these boundaries in a repository
checkout; the operation references carry the installed rules.

Saved pages, retrieval counts and structural checks prove no benefit. Only later
work can demonstrate that reuse changed an action and helped its outcome; keep
failed, harmful and no-change results. Mining is separately budgeted off-path
and cannot delay finishing an already authorized change or alter its verdict.

## Prompt

```text
Use Memory recall for this parser change. Search the caller-selected reviewed
external topic pages for an applicable constraint. Return only evidence that
changes the next check, or no-match; do not mine or save a new lesson.
```

## It's working if

A small task skips unnecessary recall. A matching narrow claim changes an actual
check without expanding its limits. Mining includes failures and corrections,
can end in no-change, and curation updates an existing topic page after exact
review. A stored page is never reported as a measured improvement.
