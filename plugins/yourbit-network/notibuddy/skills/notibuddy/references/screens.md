# Custom Native Screens & SwiftUI UI Builder Reference

NotiBuddy renders native iOS / iPadOS SwiftUI views directly from structured JSON passed in `notibuddy_notify` (`screen: ...`) or `nb notify --screen <file.json>`.

## Inline Custom UI Builder (`screen.template`)

Supported on **both local** `notibuddy` MCP/`nb` CLI sessions and the **hosted cloud MCP** (`mcp.notibuddy.app`; `fieldType: "secret"` stays local-only). The relay validates and caches only the content-free structural skeleton while your labels, data, and replies remain end-to-end encrypted. Read the live `notibuddy://screens/builder` MCP resource for full schema rules and structural limits, and pass `dry_run: true` to run full certifier validation and get a phone-width text `preview` plus a single-use `draft_id`.

### Top-Level Shape

```json
{
  "title": "Screen title in feed / notification",
  "sensitive": true,
  "screen": {
    "template": {
      "root": { "kind": "vstack", "spacing": "regular", "children": [] },
      "actions": [
        {
          "id": "deploy",
          "label": "Approve & Deploy",
          "role": "primary",
          "requireBio": true,
          "enabledWhen": [{ "op": "allChecked", "checklist": "preflight" }]
        },
        { "id": "cancel", "label": "Cancel", "role": "decline", "requireBio": false }
      ]
    },
    "thread": { "sessionId": "rel-42", "step": 1, "totalSteps": 2 }
  }
}
```

### All 12 Native Composable Blocks

| Group | `kind` | Key Properties & Notes |
|---|---|---|
| Layout | `vstack` | `spacing`: `"compact" \| "regular" \| "relaxed"`, `children`: block[] |
| Layout | `card` | Optional `header` string, `children`: block[] |
| Layout | `divider` | Hairline divider inside a `card` or `vstack` |
| Content | `heading` | `text`: string, optional `level`: `1 \| 2 \| 3` |
| Content | `text` | `text`: string, optional `style`: `"body" \| "caption" \| "mono"` |
| Content | `badge` | `label`: string, `tone`: `"neutral" \| "info" \| "success" \| "warning" \| "danger"` |
| Content | `alert` | `severity`: `"info" \| "success" \| "warning" \| "danger"`, `title`: string, optional `body` |
| Data | `kpiStrip` | `items`: `[{ "label": "Error Rate", "value": "0.02%" }, ...]` |
| Data | `keyValueList` | `rows`: `[{ "key": "Commit", "value": "8f3c19a" }, ...]` |
| Data | `diffViewer` | `diff`: `{ "filename": "...", "language": "sql", "original": "...", "modified": "..." }` |
| Interactive | `checklist` | `id`: string, optional `title`, `items`: `string[]` (referenced by `allChecked`) |
| Interactive | `formField` | `id`: string, `label`: string, `fieldType` (`text`, `email`, `url`, `date`, `toggle`, `stepper`, `picker`, `secret`), plus field-specific bounds (`min`/`max`/`defaultInt` for `stepper`, `options`/`defaultOptionIndex` for `picker`, `defaultBool` for `toggle`, `placeholder`/`required`) |

### Conditional Button Gating (`enabledWhen`) & Actions

Define **1–3 `actions`** per screen (`"dismiss"` is a reserved action `id` for host dismissal—use `"cancel"`, `"reject"`, `"hold"`, etc.). Keep destructive or high-stakes actions locked until prerequisites pass on-device:
- `{ "op": "allChecked", "checklist": "<checklist-id>" }` — unlocks once every item in that checklist is tapped.
- `{ "op": "isNotEmpty", "field": "<field-id>" }` — unlocks once a required note/input field is non-empty.
- `{ "op": "equals", "field": "<field-id>", "value": true }` — matches a boolean `toggle`, integer `stepper`/`picker` index, or a `picker` option label string.

### Reusable Templates, Drafts & CLI Attestation

- Pass `dry_run: true` to validate with the certifier, inspect a phone-width text `preview`, and get a single-use `draft_id` that can be sent directly without re-sending the full JSON payload.
- Pre-register an inline layout once and get its content-addressed `tpl_...` ID:
  `nb screen register ./my-screen.json --mode strict`
- Subsequent runs can pass `{ "screen": { "templateId": "tpl_...", "labels": {...}, "data": {...} } }`.

---

## 8 Built-In Certified Templates (`screen.templateId`)

Available on **both** local sessions and the hosted cloud MCP (`mcp.notibuddy.app`):

| Slug (`templateId`) | Face ID | Composed Blocks | Ideal Use Case |
|---|---|---|---|
| `deployment_gate` | Yes | `badge`, `alert`, `kpiStrip`, `keyValueList`, `checklist`, `toggle` | Canary-to-prod promotion |
| `db_migration_approval` | Yes | `badge`, `alert`, `keyValueList`, `diffViewer`, `checklist` | Destructive SQL / DDL sign-off |
| `incident_triage` | Rollback | `badge`, `alert`, `kpiStrip`, `keyValueList`, `picker`, `text` | Live outage ack / rollback |
| `code_review_form` | Optional | `badge`, `text`, `keyValueList`, `diffViewer`, `picker`, `text` | Agent patch review before merge |
| `kpi_status_card` | Optional | `heading`, `badge`, `kpiStrip`, `divider`, `text`, `keyValueList` | Eval & nightly cost digests |
| `action_checklist` | Yes | `heading`, `text`, `checklist`, `divider`, `toggle` | Release & key rotation gates |
| `parameter_tuning_form` | Yes | `text`, `keyValueList`, `stepper`, `picker`, `toggle`, `text` | Live limits, concurrency, budgets |
| `multi_choice_audit` | Yes | `heading`, `badge`, `text`, `keyValueList`, 2x `picker`, `text`, `toggle` | Security & access audits |

Pass flat named `screen.slots` for any built-in slug. Look up exact slot names and limits in `notibuddy://screens/<slug>` (also summarized at `https://notibuddy.app/screens.md`).

### Verifying Settled Screen Replies

Only act after verifying:
1. `status === "resolved"`
2. `answer.action` matches your approving action ID (either semantic inline `id` like `"promote"` or `"a0"`/`"a1"` ordinal—never `"dismiss"` or a decline/cancel button)
3. `answer.authenticated === true` when `requireBio: true` or `requires_auth: true` was set
4. Any submitted `answer.form` / `answer.checklists` fields match your preconditions.
