---
name: orgx-deviation-reporting
description: Record material skill deviations within authorized OrgX tracking without blocking routine work, PR updates, or merges.
tools:
  - mcp__orgx__*
---

# OrgX — skill deviation reporting

Use this skill for a material deviation affecting work the user has authorized
OrgX to track. Loading a skill, editing a file, or accepting a routine suggestion
does not itself require telemetry. Reuse existing tracking authorization; do not
ask for it again at each event. Reporting is not a prerequisite for continuing
work, updating a PR, or carrying out an authorized merge.

## When to record

You should record a deviation when:

- A skill found a material defect, changed assumption, or failed check.
- Accepting or rejecting a suggestion materially changed the result (pass
  `outcome: confirmed` or `outcome: rejected`).
- A recurring pattern warrants a corrective action or a useful handoff note.

Batch related findings at a useful milestone. If OrgX recording is outside the
user's requested scope, summarize the finding in the task evidence instead of
creating an external report.

Do **not** record the same deviation more than once per 10-minute window —
the server dedupes on `dedupe_key` automatically; duplicate POSTs waste
tokens.

## How to record

Use the documented HTTP endpoint through an already authorized OrgX runtime or
OpenClaw bridge. This plugin's `commander` MCP profile does not expose a skill
deviation operation. Do not invent `orgx.post_skill_deviation`, translate this
write into an unrelated tool, or send credentials in chat. If no authorized
transport is available, keep the deviation in the task's local evidence and
report that OrgX delivery is pending. Continue independent work without making
connection repair a merge or completion gate.

```
POST /api/v1/skills/{skill_id}/deviations
Authorization: Bearer <OrgX API key>
Content-Type: application/json

{
  "evidence_kind":      "file_edit" | "commit" | "pr" | "chat_turn" | "task_output",
  "evidence_ref":       "<repo>#<pr>" | "<path>:<line>" | "<commit_sha>",
  "summary":            "<one-line description>",
  "application_source": "plugin_codex",
  "confidence":         0.0..1.0,
  "outcome":            "pending" | "confirmed" | "rejected" | "ignored",
  "trigger_context":    { "file_path": "...", "rule_matched": "..." },
  "dedupe_key":         "<sha1(skill_id | evidence_kind | evidence_ref | floor(epoch/600))>",
  "captured_at":        "2026-04-17T10:00:00Z"
}
```

### Computing `dedupe_key`

```ts
import { createHash } from "node:crypto";

const bucket = Math.floor(Date.now() / 1000 / 600);
const material = [skillId, evidenceKind, evidenceRef, String(bucket)].join("|");
const dedupe_key = createHash("sha1").update(material).digest("hex");
```

10-minute bucketing handles save-happy editors without losing legitimate
re-fires beyond that window.

## What happens next

Your deviation lands in `skill_deviations`. The nightly rollup feeds it
into the Daily Brief proof strip's "Deviations caught" tile + updates
the skill's confidence sparkline. Agents whose loadout doesn't include
the skill may get a cross-pollination proposal surfaced.

## Links

- Full contract: https://github.com/hopeatina/orgx/blob/main/orgx/docs/api-contracts/daily-brief-schema.md#04
- SDK reference implementation (Node): https://github.com/useorgx/openclaw-plugin/blob/main/src/deviations-sdk.ts
- Daily Brief surface: https://useorgx.com/today
