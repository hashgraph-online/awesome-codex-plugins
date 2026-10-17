---
name: caveman-internal
description: |
  Internal token-compression protocol for Cavekit agent artifacts — handoff
  notes, artifact summaries, context bundles, review notes, status lines.
  NOT the user-facing /caveman skill; that one compresses assistant replies to
  the user. This skill compresses machine-to-machine prose so the next agent in
  the loop reads fewer tokens. Three intensities (lite / full / ultra) with
  automatic selection based on budget pressure. Used by task-builder, builder,
  inspector, verifier, convergence-monitor, and the stop-hook status block.
---

# Caveman Internal Protocol

## Scope

### IN-scope (compress)
- Artifact summaries written to `.cavekit/artifacts/`
- Context bundles between tasks (`.cavekit/context-bundles/`)
- Review notes and gap lists (non-user-facing)
- `state.md` `notes:` field and `loop-log.md` entries
- Status-block body (dashboard injected by the stop hook)
- Inter-agent handoff memos

### OUT-of-scope (never compress)
- Source code (any language, any file)
- Git commit messages and PR descriptions
- Kits (specs), build sites, DESIGN.md
- Error messages that a human will act on
- Security warnings and deprecation notices
- Structured findings tables (P0/P1/P2/P3, coverage matrices)
- Regression test names and assertion messages

Compressing out-of-scope content is a bug. If a reader cannot act on a
compressed artifact, regenerate it verbose and log a caveman fallback — see
"Fallback protocol" below.

## Intensity levels

### Lite — trim the fat (~20% savings)

Professional tone. Grammar intact. Drop filler, pleasantries, hedging. Keep
articles and full sentences.

> Rate-limit middleware passes unit tests. Integration failed on 429 header
> case sensitivity. Fix in progress.

### Full — default (~40% savings)

Classic caveman. Drop articles, filler, pleasantries. Fragments fine.
Technical terms stay exact. Pattern: `[thing] [action] [reason]. [next].`

> Rate-limit mw pass unit. Integration fail on 429 header case. Fixing.

### Ultra — maximum grunt (~65% savings)

Telegraphic. Abbreviate common terms (DB, auth, config, req, res, fn, impl,
mw, mcp). Arrow notation for causality. One-word answers when enough.

> mw ok, int fail header case → fix

## Automatic intensity selection

Consult the session budget ledger before writing an internal artifact:

| Budget remaining | Intensity |
|------------------|-----------|
| > 50 %           | lite      |
| 20 – 50 %        | full      |
| < 20 %           | ultra     |

Override rules:
- `depth = thorough` tasks clamp to **lite** regardless of pressure (accuracy
  matters more than tokens when the stakes are high).
- `phase = inspecting` clamps to **lite** for the gap-analysis output.
- Security-sensitive artifacts clamp to **lite**.
- If the caller sets `caveman_intensity` explicitly in the artifact envelope,
  use that and skip auto-selection.

See `references/budget-thresholds.md` for the detailed decision table.

## Fallback protocol

If a downstream reader cannot reconstruct intent from a compressed artifact:

1. Regenerate the artifact in **full prose** (no compression).
2. Append a one-line entry to `state.md`'s "Caveman fallbacks" section:
   ```
   - 2026-04-17T12:34Z T-017 verifier fallback: artifact summary re-expanded
   ```
3. If the same artifact category fails 3+ times in one session, clamp that
   category to `lite` for the rest of the session and log to `state.md`.

## Envelope

Every compressed artifact carries a tiny header:

```
<!-- caveman: intensity=full version=1 -->
```

Readers that see this header know the body is compressed and apply the
reverse-expansion grammar (re-add articles, re-expand abbreviations) when
rendering for a human.

## Examples

| Verbose                                                                 | Full                                        | Ultra                |
|-------------------------------------------------------------------------|---------------------------------------------|----------------------|
| "The build completed successfully after three waves."                   | "Build complete. 3 waves."                  | "Build ok 3w"        |
| "All tests pass, but one test was skipped due to a missing fixture."    | "Tests pass. One skipped, missing fixture." | "Tests ok 1 skip fx" |
| "The reviewer flagged two critical issues in the auth middleware."     | "Reviewer: 2 P0 in auth mw."                | "Rev 2 P0 auth mw"   |

## Integration with the existing `caveman` skill

The user-facing `caveman` skill governs how the assistant **speaks to the user**
during a session (answers, explanations, replies). This `caveman-internal`
skill governs how agents **write artifacts** for each other. Both must be on
or both off for a coherent experience, so `caveman_mode = off` in config also
disables this skill.
