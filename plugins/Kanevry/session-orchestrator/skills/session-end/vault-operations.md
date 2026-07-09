# Phase 2.1: Vault Validation

> Sub-file of the session-end skill. Executed as part of Phase 2 (Quality Gate) when `vault-sync.enabled` is `true`.
> For the full session close-out flow, see `SKILL.md`.

### 2.1 Vault Validation (if configured)

Projects that maintain an Obsidian-style markdown vault can opt-in to a frontmatter + wiki-link validation gate at session close. This is gated on the `vault-sync.enabled` config flag (default `false`) — projects without a vault are unaffected. When enabled, the gate reads three more config fields (`vault-sync.mode`, `vault-sync.vault-dir`, `vault-sync.exclude`) and invokes the `vault-sync` validator. See `docs/session-config-reference.md` for field semantics, and `skills/vault-sync/SKILL.md` for the validator contract.

**Gate:** Only run this subsection if `$CONFIG | jq -r '."vault-sync".enabled // false'` is `true`. If `false` or missing, skip silently.

**Invocation pattern** (exact bash contract — keep in sync with `skills/vault-sync/validator.sh`):

```bash
# Read config (defaults: mode=warn, vault-dir=$PWD, exclude=[])
VS_ENABLED=$(echo "$CONFIG" | jq -r '."vault-sync".enabled // false')
if [[ "$VS_ENABLED" == "true" ]]; then
  VS_MODE=$(echo "$CONFIG" | jq -r '."vault-sync".mode // "warn"')
  VS_DIR=$(echo "$CONFIG" | jq -r '."vault-sync"."vault-dir" // empty')
  : "${VS_DIR:=$PWD}"

  # Build --exclude args from the config array (one flag per entry)
  VS_EXCLUDE_ARGS=()
  while IFS= read -r pat; do
    [[ -z "$pat" ]] && continue
    VS_EXCLUDE_ARGS+=(--exclude "$pat")
  done < <(echo "$CONFIG" | jq -r '."vault-sync".exclude // [] | .[]')

  # Invoke validator; capture JSON on stdout and exit code
  VS_JSON=$(VAULT_DIR="$VS_DIR" bash "$PLUGIN_ROOT/skills/vault-sync/validator.sh" \
    --mode "$VS_MODE" "${VS_EXCLUDE_ARGS[@]}" 2>/dev/null) || VS_EXIT=$?
  VS_EXIT="${VS_EXIT:-0}"

  VS_STATUS=$(echo "$VS_JSON" | jq -r '.status')
  VS_ERR_COUNT=$(echo "$VS_JSON" | jq -r '.errors | length')
  VS_WARN_COUNT=$(echo "$VS_JSON" | jq -r '.warnings | length')
fi
```

**Reporting rules:**

- **`mode: off`** — validator reports `status: skipped-mode-off`; include a single line "Vault validation: skipped (mode=off)" in the quality gate report and move on. Never blocks.
- **`mode: warn`** — validator always exits 0. If `.errors | length > 0`, surface the error list in the report under "Vault validation warnings (mode=warn)" with file + path + message for each entry. Also list any `.warnings` (dangling wiki-links) in the same section. Never blocks close, but remind the user that flipping to `mode: hard` would have blocked on N files.
- **`mode: hard`** — validator exits 1 on errors. On exit 1: do NOT block the close. Surface the full error list in the quality gate report, then default to **warn + carryover + continue** (Recommended): file a carryover issue (labels `carryover`, `priority:high`) titled `[Carryover] Vault validation (hard) — <N> frontmatter errors` capturing the offending files for a follow-up session, log a Deviation entry in STATE.md `## Deviations`, then continue the close. Offer "Override and close" (continue without a carryover issue; log the Deviation) as an alternative via AskUserQuestion. The user can also (a) fix the offending frontmatter, (b) add the file pattern to `vault-sync.exclude` if it is a legitimate index file (e.g. `_MOC.md`, `_overview.md`), or (c) temporarily set `vault-sync.mode: warn` while backfilling frontmatter across the vault. On exit 0 with warnings: include them in the report but do not block.
- **Exit 2** (infra error — missing `node`, `pnpm`, or `validator.mjs`) — treat as a skipped gate with a loud warning ("Vault validation: infrastructure error — <reason>"). Do NOT block the session close on infra failures; the goal is to surface configuration problems, not to wedge sessions when Node is unavailable.

**Success line format** (when `errors: [] && warnings: []`):
```
Vault validation: ok (N files checked, M excluded, mode=<mode>)
```
