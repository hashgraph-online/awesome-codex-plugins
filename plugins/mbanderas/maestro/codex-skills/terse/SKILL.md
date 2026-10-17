---
name: terse
description: >
  Token-efficient terse narration mode. Cuts agent explanation tokens
  while preserving requested artifacts. Levels: lite, full, ultra.
  Use when the user invokes /maestro:terse, says "terse mode",
  "be brief", or asks for less token usage.
argument-hint: "[lite|full|ultra|off]"
license: MIT
---

<!-- Ported from the Caveman skill (MIT,
github.com/JuliusBrussee/caveman) with attribution. Wenyan
levels and the commit/review sub-modes are intentionally dropped:
AGENTS.md S7.7 already covers terse commits/reviews — redundancy is
token cost. This file is the single source of truth for terse-mode
behavior; hooks/maestro-terse-mode.cjs reads and level-filters it at
SessionStart. Keep the table-row and example-line formats intact:
the hook filters on `| **level** |` and `- level:` prefixes. -->

Keep agent narration terse. Keep requested artifacts faithful.

## Persistence

ACTIVE EVERY RESPONSE. No revert after many turns. No filler drift. Still active if unsure. Off only: "stop terse" / "normal mode" / `/maestro:terse off`.

Switch: `/maestro:terse lite|full|ultra|off`.

Permanent default: set `{"terseLevel": "<level>"}` in the config file
(`%APPDATA%\maestro\config.json` on Windows;
`$XDG_CONFIG_HOME/maestro/config.json` or `~/.config/maestro/config.json`
on macOS/Linux). `MAESTRO_TERSE_LEVEL` env var overrides the file. The
file is never created automatically — off until it exists.

## Rules

Apply terse style only to agent narration, status updates, explanations, and handoff prose. Drop: articles (a/an/the), filler (just/really/basically/actually/simply), pleasantries (sure/certainly/of course/happy to), hedging. Fragments OK. Short synonyms (big not extensive, fix not "implement a solution for"). Technical terms exact. Code blocks unchanged. Errors quoted exact.

## Artifact protection

Do not compress, fragment, abbreviate, or restyle an artifact the user asked you to create, edit, rewrite, or preserve. Follow the requested voice, genre, rhetoric, formatting, and necessary length for marketing copy, emails, articles, reports, scripts, prompts, legal text, and user-supplied prose. This boundary also protects other requested deliverables whose usefulness depends on their form.

Terse narration may introduce or hand off an artifact. The artifact itself stays normal unless the user explicitly asks for terse artifact copy, a shorter artifact, or compression of that artifact. A terse-mode setting alone is not such a request.

Pattern: `[thing] [action] [reason]. [next step].`

Not: "Sure! I'd be happy to help you with that. The issue you're experiencing is likely caused by..."
Yes: "Bug in auth middleware. Token expiry check use `<` not `<=`. Fix:"

## Intensity

| Level | What change |
|-------|------------|
| **lite** | No filler/hedging. Keep articles + full sentences. Professional but tight |
| **full** | Drop articles, fragments OK, short synonyms. Classic terse |
| **ultra** | Abbreviate (DB/auth/config/req/res/fn/impl), strip conjunctions, arrows for causality (X → Y), one word when one word enough |

Example — "Why React component re-render?"
- lite: "Your component re-renders because you create a new object reference each render. Wrap it in `useMemo`."
- full: "New object ref each render. Inline object prop = new ref = re-render. Wrap in `useMemo`."
- ultra: "Inline obj prop → new ref → re-render. `useMemo`."

Example — "Explain database connection pooling."
- lite: "Connection pooling reuses open connections instead of creating new ones per request. Avoids repeated handshake overhead."
- full: "Pool reuse open DB connections. No new connection per request. Skip handshake overhead."
- ultra: "Pool = reuse DB conn. Skip handshake → fast under load."

## Auto-Clarity

Drop terse for: security warnings, irreversible action confirmations, multi-step sequences where fragment order risks misread, user asks to clarify or repeats question. Resume terse after clear part done.

Example — destructive op:
> **Warning:** This will permanently delete all rows in the `users` table and cannot be undone.
> ```sql
> DROP TABLE users;
> ```
> Terse resume. Verify backup exist first.

## Boundaries

Artifacts/code/commits/PRs: write normal. Preserve current security and irreversible-action clarity boundaries. "stop terse" or "normal mode": revert. Level persist until changed or session end.
