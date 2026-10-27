---
name: cometchat-moderation
description: "Trust & Safety for CometChat — auto-moderate text/image/video/file with dashboard rules + keyword lists, block or flag-for-review, let users report messages, and keep an audit trail. Cross-family: rules/lists/queues are dashboard+REST; report/block UI is built into each family's UI Kit. Triggers: 'add moderation', 'profanity filter', 'image moderation', 'block bad words', 'report a message', 'flag inappropriate content', 'content safety', 'spam/scam detection', 'CSAM/minor safety', 'malware scan attachments', 'moderation queue'."
license: "MIT"
compatibility: "CometChat Moderation (dashboard rules/lists + Flagged/Blocked/Reviewed queues) · Moderation REST API v3 · per-family UI Kit report/block + Chat SDK flagging."
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat moderation trust-safety profanity image-moderation spam csam malware report flag audit"
---

> **Ground truth:** capabilities and rule names are FETCHED from the live docs — `{DOCS_BASE}/moderation/overview`, `/moderation/{rules-management,lists-management,flagged-messages,blocked-messages,reviewed-messages}`, `{DOCS_BASE}/rest-api/moderation-apis/overview`, and the client hooks `{DOCS_BASE}/ui-kit/<family>/core-features#moderation` (built-in report) + `{DOCS_BASE}/sdk/<platform>/ai-moderation` (SDK flagging). `DOCS_BASE = https://www.cometchat.com/docs`; append `.md`. Most of this is dashboard configuration; verify the exact rule/list options and any REST shapes against the docs before asserting them.

## Use this skill when
Making a chat safe/compliant: profanity/toxicity filtering, image/video safety, spam/scam detection, malware scanning of attachments, letting users report content, a moderator review queue, or an audit trail for T&S. Trust & Safety is a procurement gate for social, gaming, marketplace, dating, education and healthcare apps.

## How it works
Every message runs through the **rule engine** as it's sent; a rule either lets it through, **blocks** it (hidden immediately), or **flags** it for a moderator. Users can also **report** a message manually, which flags it. Blocked/flagged items land in dashboard queues; a moderator's decision (approve/block/mark reviewed) moves it to the audit trail.

```
send → rules → pass → delivered
             → block → Blocked Messages
             → flag  → Flagged Messages → moderator → Reviewed Messages (audit)
```

## 1. Configure rules + lists (dashboard / REST)
- **Rules Management** (`/moderation/rules-management`): turn on the built-in rules you need and set each to **block** or **flag**. Available categories (fetch the current list — it grows):
  - **Text:** word-pattern match (profanity), contact/email removal, spam & scam, platform circumvention, toxicity, hate & harassment, self-harm, explicit content, privacy/sensitive-info, impersonation, violent/terroristic, non-consensual sexual content.
  - **Image:** unsafe/prohibited, minor-safety/CSAM, graphic violence, explicit/sexual, hate symbols, fraud (fake IDs), **malware scan**.
  - **Video / Audio / File:** **malware & virus scan** of attachments.
- **Lists Management** (`/moderation/lists-management`): your own keyword / regex / sentence lists, linked to rules — this is the "banned words" surface. Lists are reusable across rules.
- **Programmatic setup:** the **Moderation REST API** (`/rest-api/moderation-apis/overview`) manages rules + keyword lists from your server (e.g. per-tenant config, CI-seeded rules). Fetch its shapes before writing calls.

## 2. Wire the client (per family — built into the UI Kit)
- **Report a message:** the UI Kits ship a built-in **Report Message** action on the message — enable it via that family's moderation feature (`{DOCS_BASE}/ui-kit/<family>/core-features#moderation`; wire through `cometchat-<family>-features`). No hand-rolled report UI.
- **Blocked content:** rule-blocked messages simply don't render for recipients; nothing extra to build.
- **SDK path (custom UI / headless):** flag messages directly with the Chat SDK (`{DOCS_BASE}/sdk/<platform>/ai-moderation`) — the per-feature fallback when a family has no drop-in.

## 3. Moderator review + audit
- **Flagged Messages** / **Blocked Messages** dashboards: moderators review, approve false positives, or confirm blocks — and use them to refine rules.
- **Reviewed Messages** is the **audit trail** of every moderation decision (who did what, when) for compliance records — pair with `cometchat-compliance` for retention/eDiscovery of these records.

## Legacy extensions — migrate, don't double-run
If the app still uses the **legacy extensions** (Profanity Filter, Data Masking, Image Moderation), **disable them before enabling the new moderation rules.** Running both processes every message twice → performance issues and message delays. Treat this as a required migration step, not optional.

## Enablement note
Moderation is a dashboard/plan capability — enable it on the app (and on the **production** app, not just dev). `npx @cometchat/skills-cli@3 features` can toggle app extensions/AI after `auth login`; the rule/list configuration itself is done in the dashboard or via the Moderation REST API.

## Common pitfalls
1. **Legacy extensions left on** alongside new rules — double-processing, delays. Disable the old ones first.
2. **Rules configured on dev only** — content ships unmoderated in production; enable on the production app.
3. **Hand-rolling a report button** — the UI Kit already ships Report Message; wire the built-in.
4. **Block vs flag confused** — block hides immediately (good for clear violations); flag routes to a human (good for borderline). Set each rule deliberately.
5. **No one watching the queues** — flagged content needs a moderator workflow; wire notifications/ownership.
6. **Assuming a rule exists** — fetch the current rule catalog; don't promise a category the docs don't list.

## Verify it works
A message with a banned word/keyword is blocked or flagged per the rule · an unsafe image is caught · an attachment is malware-scanned · a user's Report action flags a message into the queue · a moderator decision appears in Reviewed Messages · legacy extensions are off · rules are enabled on the production app.
