---
name: memory
description: 'Find reviewed context, capture evidence or curate maintained claims. Use when: prior evidence can change an action, or learning is requested; no mandatory recall or lesson.'
---
# Memory

Use maintained experience only when it helps an actual task. Memory is optional:
no mandatory recall at RPI entry, lesson at completion, worksheet, page quota or
background mining. A trivial edit can proceed directly to implementation.

## Choose one operation

| Need | Read on demand |
|---|---|
| An earlier constraint or source map may change the next action | [Find / recall](references/recall.md) |
| Capture useful evidence from selected sources, episodes or corrections | [Capture / mine / learn](references/mine-learn.md) |
| Update, qualify, consolidate or retire a supported claim | [Curate / qualify / retire](references/curate.md) |
| Find repeated operational friction in supplied history | [Toil evidence](#toil-evidence) |

Memory owns these find, capture and curate operations; other roles link here
instead of maintaining their own procedures. Capture/mine/learn includes bounded
source maps, verdicts, corrections and failed or harmful reuse; it is not a
required completion step. The optional
[OKF page profile](references/learn/okf-page-profile.md) checks structure only.
Do not load every operation reference just because Memory was selected.

## One authority per fact

BD or the caller's tracker owns work/status/dependencies/handoffs; Git owns
content and delivery history; native sessions and CASS own episode evidence.
Caller-selected reviewed Markdown topic pages hold reusable claims in a project
`.context/` or an external bundle. These are evidence, not another work account.
Existing docs, ADRs and code retain their declared authority; a page points to
those owners instead of copying their policy. Search and update an existing topic
page before making a new one. Do not make one lesson file per session, copy a
transcript lake, or silently initialize a memory store. Source evidence is not
policy.

For an explicitly selected project `.context/`, start at its small authored
`README.md` map only when relevant to the task, then read likely pages and their
current source owners with ordinary filesystem tools such as `rg` and `cat`.
Portable reading of cleared project pages needs neither BD nor AO. The map
links topics and source owners; it does not mirror tracker status or inventory
every source. No directory, index or private import is created automatically.
The optional `ao config context` route supports external bundles and an explicitly
bound canonical direct `<consumer>/.context`. It requires native BD and preserves
the policy and identity bindings; other consumer-overlapping roots remain refused.
Draft staging and review evidence stay external to Git, consumer and bundle.

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
payload, destination paths and metadata before any Git object/index/stash or
import, including admission to project `.context/`. Proof and drafts stay outside
the project in protected non-Git storage. The caller selects storage;
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

## Toil evidence

Read only the explicitly supplied, authorized history within the stated window.
Preserve queries, filters and representative source references. Exclude machine
echoes and restored copies before clustering equivalent human actions. For
supplied Codex JSONL in a source checkout, the optional helper
`python3 scripts/toil-mining/recent_human.py --since <zoned-time> --until <zoned-time>
<explicit-session-paths>` extracts to stdout without discovering sessions or
reading attachments. Missing `client_id`, malformed records and exclusions stay
counted and disclosed; the extractor does not itself infer toil. It is not
bundled with standalone skill installs and adds no Python runtime dependency
to ordinary Memory use.

Report frequency, observed elapsed/token cost and failure or correction rate
separately. A recurring-toil claim needs three resolvable occurrences; smaller
groups remain tentative with their actual count. For a composite ranking, show
the measured inputs and formula; missing factors remain unmeasured, never an
invented average. Rank by demonstrated burden, not frequency or salience alone.
Each candidate includes clustering confidence, representative evidence, limits
and the smallest plausible automation shape. Separate observations from advice.

Return the ranked evidence inline by default, with checked/not-checked sources.
Only write a report when requested, using the authorized destination under the
storage rules above. Mining creates no tracker items, automations, ownership or
queue. A packaging request can use [Skill Builder](../skill-builder/SKILL.md);
evidence alone grants no authority to adopt a rule or schedule a job.

## Prompt

```text
Use Memory find/recall for this parser change. Search the caller-selected reviewed
project .context/ or external topic pages for an applicable constraint. Return
only evidence that changes the next check, or no-match; do not mine or save a
new lesson.
```

## It's working if

A small task skips unnecessary recall. A matching narrow claim changes an actual
check without expanding its limits. Mining includes failures and corrections,
can end in no-change, and curation updates an existing topic page after exact
review. A stored page is never reported as a measured improvement.
