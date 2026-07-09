# Phase 2.2: CLAUDE.md (or AGENTS.md) Drift Check

> Sub-file of the session-end skill. Executed as part of Phase 2 (Quality Gate) when `drift-check.enabled` is `true`.
> For the full session close-out flow, see `SKILL.md`. For validator contract, see `skills/claude-md-drift-check/SKILL.md`.
> Project-instruction file resolution: `CLAUDE.md` and `AGENTS.md` (Codex CLI) are transparent aliases — see [skills/_shared/instruction-file-resolution.md](../_shared/instruction-file-resolution.md). All references to `CLAUDE.md` below resolve via that precedence rule; the drift checker accepts either filename.

### 2.2 CLAUDE.md (or AGENTS.md) Drift Check (if configured)

Projects can opt-in to a narrative-drift gate at session close. This is gated on the `drift-check.enabled` config flag (default `false`) — projects without `CLAUDE.md`/`AGENTS.md` or `_meta/` narrative are unaffected. When enabled, the gate reads the `drift-check.mode`, `drift-check.include-paths`, and all `drift-check.check-*` flags and invokes the `claude-md-drift-check` validator. See `docs/session-config-reference.md` for field semantics, and `skills/claude-md-drift-check/SKILL.md` for the validator contract.

The checks are complementary to `vault-sync` (Phase 2.1): vault-sync validates frontmatter and wiki-links inside the vault tree; drift-check validates narrative claims, surface counts, generated-rule freshness, and rule-scoping contracts in top-level repo docs.

**Gate:** Only run this subsection if `$CONFIG | jq -r '."drift-check".enabled // false'` is `true`. If `false` or missing, skip silently.

**Invocation pattern** (exact bash contract — keep in sync with `skills/claude-md-drift-check/checker.sh`):

```bash
DC_ENABLED=$(echo "$CONFIG" | jq -r '."drift-check".enabled // false')
if [[ "$DC_ENABLED" == "true" ]]; then
  DC_MODE=$(echo "$CONFIG" | jq -r '."drift-check".mode // "warn"')

  # Build --include-path args from the config array (one flag per entry)
  DC_INCLUDE_ARGS=()
  while IFS= read -r pat; do
    [[ -z "$pat" ]] && continue
    DC_INCLUDE_ARGS+=(--include-path "$pat")
  done < <(echo "$CONFIG" | jq -r '."drift-check"."include-paths" // [] | .[]')

  # Build per-check skip flags (checks default to true; add --skip-* when false)
  DC_SKIP_ARGS=()
  [[ "$(echo "$CONFIG" | jq -r '."drift-check"."check-path-resolver" // true')" == "false" ]] && DC_SKIP_ARGS+=(--skip-path-resolver)
  [[ "$(echo "$CONFIG" | jq -r '."drift-check"."check-project-count-sync" // true')" == "false" ]] && DC_SKIP_ARGS+=(--skip-project-count)
  [[ "$(echo "$CONFIG" | jq -r '."drift-check"."check-issue-reference-freshness" // true')" == "false" ]] && DC_SKIP_ARGS+=(--skip-issue-refs)
  [[ "$(echo "$CONFIG" | jq -r '."drift-check"."check-session-file-existence" // true')" == "false" ]] && DC_SKIP_ARGS+=(--skip-session-files)
  [[ "$(echo "$CONFIG" | jq -r '."drift-check"."check-command-count" // true')" == "false" ]] && DC_SKIP_ARGS+=(--skip-command-count)
  [[ "$(echo "$CONFIG" | jq -r '."drift-check"."check-session-config-parity" // true')" == "false" ]] && DC_SKIP_ARGS+=(--skip-session-config-parity)
  [[ "$(echo "$CONFIG" | jq -r '."drift-check"."check-vault-dir-parity" // true')" == "false" ]] && DC_SKIP_ARGS+=(--skip-vault-dir-parity)
  [[ "$(echo "$CONFIG" | jq -r '."drift-check"."check-generated-rule-staleness" // true')" == "false" ]] && DC_SKIP_ARGS+=(--skip-generated-rule-staleness)
  [[ "$(echo "$CONFIG" | jq -r '."drift-check"."check-rule-scoping" // true')" == "false" ]] && DC_SKIP_ARGS+=(--skip-rule-scoping)
  [[ "$(echo "$CONFIG" | jq -r '."drift-check"."check-docs-parity" // true')" == "false" ]] && DC_SKIP_ARGS+=(--skip-docs-parity)

  # Invoke checker; capture JSON on stdout and exit code
  DC_EXIT=0
  DC_JSON=$(VAULT_DIR="$PWD" bash "$PLUGIN_ROOT/skills/claude-md-drift-check/checker.sh" \
    --mode "$DC_MODE" "${DC_INCLUDE_ARGS[@]}" "${DC_SKIP_ARGS[@]}" 2>/dev/null) || DC_EXIT=$?

  DC_STATUS=$(echo "$DC_JSON" | jq -r '.status // "infra-error"')
  DC_ERR_COUNT=$(echo "$DC_JSON" | jq -r '.errors // [] | length')
  DC_WARN_COUNT=$(echo "$DC_JSON" | jq -r '.warnings // [] | length')
fi
```

`$PLUGIN_ROOT` resolution follows the same fallback chain as `skills/_shared/config-reading.md`.

**Reporting rules:**

- **`mode: off`** — checker reports `status: skipped-mode-off`; include a single line "CLAUDE.md drift: skipped (mode=off)" in the quality gate report. Never blocks.
- **`mode: warn`** — checker always exits 0. If `.errors | length > 0`, surface the list in the report under "CLAUDE.md drift warnings (mode=warn)" with check + file:line + message for each entry. Also list any `.warnings` (e.g. `#NN` the checker could not resolve via glab). Never blocks close; note that `mode: hard` would have routed the same errors through the carryover path below.
- **`mode: hard`** — checker exits 1 on errors. On exit 1: do NOT block the close. Surface the full error list, then default to **warn + carryover + continue** (Recommended): file a carryover issue (labels `carryover`, `priority:high`) titled `[Carryover] CLAUDE.md drift (hard) — <E> errors` capturing the drift items for a follow-up session, log a Deviation entry in STATE.md `## Deviations`, then continue the close. Offer "Override and close" (continue without a carryover issue; log the Deviation) as an alternative via AskUserQuestion. The user can also (a) fix the drift directly in `CLAUDE.md` (or `AGENTS.md` on Codex CLI) / `_meta/`, or (b) temporarily set `mode: warn` while backfilling, or (c) disable a specific check via its `check-*` flag if it reports false positives on this codebase.
- **Exit 2** (infra error — missing `node`, unreadable `VAULT_DIR`, malformed args) — treat as a skipped gate with a loud warning ("CLAUDE.md drift: infrastructure error — <reason>"). Do NOT block the session close on infra failures.

**Exit-code dispatch:** The checker writes infra-error JSON to stderr (suppressed by `2>/dev/null` above), so `DC_JSON` is empty when `DC_EXIT == 2`. Always branch on `DC_EXIT` first, then `DC_STATUS`:

```bash
if [[ "$DC_EXIT" == "2" ]]; then
  # infra error — DC_JSON is empty, stderr was suppressed. Surface loud warning, do not block.
elif [[ "$DC_STATUS" == "invalid" && "$DC_MODE" == "hard" ]]; then
  # hard-mode: surface + warn + carryover + continue (no hard block — #724)
elif [[ "$DC_STATUS" == "invalid" ]]; then
  # warn-mode report
else
  # ok / skipped — emit success line
fi
```

**Partial-skip awareness:** The checker may report `checks_skipped` in its JSON output even on successful runs. Common causes: `glab` not on PATH (Check 3 degrades gracefully), no `01-projects/` directory (Check 2 inapplicable). Surface these in the report as informational lines, not errors:

```
CLAUDE.md drift: ok (N files scanned, mode=<mode>)
  - Skipped: issue-reference-freshness (glab not found in PATH)
```

**Success line format** (when `errors: [] && warnings: []`):

```
CLAUDE.md drift: ok (N files scanned, mode=<mode>)
```

**Error line format** (hard mode, carryover):

```
CLAUDE.md drift: INVALID (mode=hard) — E errors, W warnings across N files
  [path-resolver]       CLAUDE.md:L — <message>
  [project-count-sync]  CLAUDE.md:L — <message>
  [issue-reference-freshness] CLAUDE.md:L — <message>
  [session-file-existence]    _meta/foo.md:L — <message>
```
