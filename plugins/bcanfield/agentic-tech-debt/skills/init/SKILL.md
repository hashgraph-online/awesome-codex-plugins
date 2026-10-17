---
name: init
description: Write or refresh the "## Tech debt operations" section in AGENTS.md so a team shares one source of truth for debt-ops disciplines and cached quality commands. Idempotent. Only the managed section changes; other sections are untouched. Invoke explicitly via $init (solo users get the same content from the SessionStart inject).
---

# init

Write or update a `## Tech debt operations` section in `./AGENTS.md`. Idempotent — only the managed section changes.

## 1. Read the cached commands

```bash
TOPLEVEL=$(git rev-parse --show-toplevel)
REPO_HASH=$(printf '%s' "$TOPLEVEL" | shasum | cut -c1-12)

# Hooks and skills share one deterministic cache base (ADR 0011). Override the
# base with DEBT_OPS_CACHE; default is ~/.cache/debt-ops.
CACHE_DIR="${DEBT_OPS_CACHE:-$HOME/.cache/debt-ops}/cache/$REPO_HASH"

LIST="$CACHE_DIR/feedback.list"
[ -f "$LIST" ] && cat "$LIST"

# Detected ADR/registry dirs. Fall back to the co-located defaults if the
# cache files aren't written yet.
ADR_DIR=$( [ -s "$CACHE_DIR/adr-dir" ] && cat "$CACHE_DIR/adr-dir" || echo "docs/adr" )
REGISTRY_DIR=$( [ -s "$CACHE_DIR/registry-dir" ] && cat "$CACHE_DIR/registry-dir" || echo "docs/debt" )
echo "adr-dir: $ADR_DIR"
echo "registry-dir: $REGISTRY_DIR"
```

If the file doesn't exist, the SessionStart discovery prompt hasn't run yet. Tell the developer:

> No cached quality commands yet. Start a new session so I can detect them, then re-run $init.

…and stop.

## 2. Compose the section (template)

Substitute `{{COMMANDS}}` with the cache contents verbatim, `{{ADR_DIR}}` with the detected `adr-dir`, and `{{REGISTRY_DIR}}` with the detected `registry-dir` (from step 1).

```markdown
## Tech debt operations

<!-- this section is auto-managed by the debt-ops Codex plugin; safe to edit, run $init to regenerate -->

### Disciplines

1. The test for debt: would a future reader ask "why this way?" If yes, register via the `$add` skill immediately — no prompt. This is judgment, not a marker scan: a `TODO`/`FIXME`/`HACK`/`XXX` is the obvious case, but an unmade decision, a stub, a loosened type, or a default picked "for now" all count even with no marker in the diff. Use `payoff_trigger: unknown` if unsure. Announce: `+1 entry: <slug> (drop?)`. Over-register freely; the developer drops with "drop it".

2. When making an architecturally significant change — a data model, public interface, security boundary, release pipeline, or a dep-manifest change that is a major-version bump or a *new* top-level dependency — draft an ADR under `{{ADR_DIR}}/` in Nygard format: a `# NNNN — Title` heading, `**Date:**` and `**Status:**` lines, then Context, Decision, Consequences, Alternatives, Payoff trigger. Create the directory if needed. Only draft an ADR when there are two credible alternatives; if you cannot list two, it is a comment, not an ADR. An ADR with a payoff trigger *is* deliberate debt — when you write one, also invoke `$add` so the registry entry mirrors the ADR (don't conclude "no markers, no debt").

3. Read entries under `{{REGISTRY_DIR}}/` before changing files they reference.

### Quality commands

These run after every edit under a 3 s budget per command. Edit freely; the plugin reads tolerantly. Lines starting with `#` are estimates/comments and are skipped at run time.

<!-- debt-ops:feedback v1 -->
{{COMMANDS}}
<!-- /debt-ops:feedback -->
```

## 3. Apply

- **If `./AGENTS.md` doesn't exist:** Write it with the section above as the entire file.
- **If `./AGENTS.md` has a `## Tech debt operations` section:** Edit to replace exactly that section — from the heading through (but not including) the next `## ` heading, or through EOF if no next heading. Leave every other byte unchanged.
- **If `./AGENTS.md` exists without the section:** Edit to append the section after the last existing line, with a single blank line between.

## 4. Announce

`charter updated: ./AGENTS.md — disciplines + N quality commands`

(N = count of non-comment, non-blank lines inside the marker block.)

## Marker contract — do not deviate

- `<!-- debt-ops:feedback v1 -->` is the open marker `feedback.py` keys on. Exact string; the `v1` is part of the marker.
- `<!-- /debt-ops:feedback -->` is the close marker.
- The self-explaining `<!-- this section is auto-managed by … -->` line is mandatory — a teammate without the plugin reads that to understand what they're seeing.
- Never touch any byte outside the `## Tech debt operations` section.
