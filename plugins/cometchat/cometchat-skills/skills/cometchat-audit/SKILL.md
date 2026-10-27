---
name: cometchat-audit
description: "Review an EXISTING CometChat integration and report what's wrong or risky — security (no client Auth Key, server tokens), correctness (init→login→render order, no raw localization keys, no dead affordances), version drift (version_conflict), production-readiness, accessibility & localization gaps — ranked, with fixes routed to the right skill. Read-only: it reports, it doesn't rewrite unless you ask. Triggers: 'audit my cometchat integration', 'review my chat setup', 'is my cometchat secure / production ready', 'check my cometchat code', 'health check', 'what's wrong with my chat'."
license: "MIT"
compatibility: "Any CometChat integration (React v7 · Angular v5 · React Native v5 · iOS v5 · Android v6 · Flutter v6 · headless SDK). Read-only review; fixes route to the family skills."
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat audit review health-check security production-readiness diagnostics"
---

> **Ground truth:** the authority for "correct" is `RULES.md` + the resolved family's skills (`cometchat-<family>-core`/`-production`/`-troubleshooting`) and the offline probe `npx @cometchat/skills detect --json`. Verify every symbol/prop you flag against the family catalog + docs (via `-core/references/docs-map.md`); never flag from memory. This is a **read-only** review — produce the report first; only change code if the user says so (then hand each fix to the owning skill).

## Use this skill when
Someone wants an existing CometChat integration checked — before a launch, a security review, an upgrade, or a "why is this flaky / is this safe" question. It is the proactive complement to the per-family troubleshooting skills (`cometchat-<family>-troubleshooting`, which react to a specific symptom).

## How to run the audit
1. **Detect** — `npx @cometchat/skills detect --json`: framework, installed UI Kit, `version_conflict`, `existing_cometchat`. Resolve `<family>` from `peers.yaml`. If nothing is detected, say so and stop (nothing to audit).
2. **Read the integration** — the init/login/lifecycle file, where the surface renders, the env/secret files, the server token endpoint (if any), and any custom message/theme/feature code. Do NOT read `node_modules`/`.d.ts`.
3. **Score each check below**, gather evidence (`file:line`), and write a **ranked report** — most severe first — with, per finding, the fix and the skill that owns it. Then offer to apply fixes; don't auto-edit.

## The checklist
**Security (highest severity)**
- Auth Key present in client code / bundle / binary? → critical; must move to server-minted tokens (`cometchat-security`, `cometchat-<family>-production`).
- Token endpoint deriving the UID from a client parameter (`?uid=`)? → impersonation.
- REST API Key anywhere client-side or in the repo? → critical.
- Sessions revocable on offboarding (flush tokens)? RBAC roles configured, or everyone on `default`? (`cometchat-security`.)

**Correctness**
- `init() → login() → render` order honored; no component rendered before login resolves; no init during SSR; StrictMode/double-invoke guarded.
- `initFromSettings` used (ai-agent attribution), not the classic builder init.
- Surface has real dimensions (not a collapsed 0-height box); host CSS not leaking into `.cometchat`.
- No raw localization keys rendered (`group_info` etc.).
- No dead affordances — every default-on control wired or hidden.
- Listeners removed on unmount/dispose (no duplicate messages/leaks).

**Version & drift**
- `version_conflict` from detect (UI Kit major ≠ the family's target)? → route to `cometchat-<family>-migration`.
- Kit/SDK versions pinned (not a floating major)? iOS: the exact kit+SDK+Calls pins.

**Production-readiness**
- HTTPS everywhere; logout teardown (session + push tokens); dashboard extensions/AI enabled on the PRODUCTION app; error handling in place (React families: an error boundary such as `CometChatErrorBoundary`; iOS/Android/Flutter: SDK error listeners / kit error-state views). (`cometchat-<family>-production`.)

**Accessibility & localization (enterprise procurement)**
- Focus rings / contrast not stripped by global CSS; chat container labelled; reduced-motion honored (`cometchat-a11y`).
- Locale set before render; no raw keys; RTL handled if targeted (`cometchat-i18n`).

**Compliance (if in scope)**
- App in the right data-residency region; a data-deletion path exists (`cometchat-compliance`); moderation enabled if the product needs T&S (`cometchat-moderation`).

## The report format
Lead with a one-line verdict (ship / fix-first / not-ready) and counts by severity. Then a table: `Severity · Finding · Evidence (file:line) · Fix · Owning skill`. List what PASSED too, so the reader knows it was checked. End with the top 3 things to fix first. Do not inflate severity, and do not flag a "problem" you didn't verify against docs/catalog.

## Common pitfalls (of the auditor)
1. **Flagging from memory** — verify each symbol/prop against the catalog + docs before calling it wrong.
2. **Auto-editing** — this is read-only; report, then ask.
3. **Reading `node_modules`/`.d.ts`** — audit the user's code + docs, not kit internals.
4. **Severity inflation** — a dev-only Auth Key in a local `.env` is not the same as one shipped in production; judge by what actually reaches users.

## Verify it works
The report names the framework + family, lists ranked findings each with `file:line` + a fix + an owning skill, states what passed, and gives a clear verdict — and nothing was edited unless the user approved.
