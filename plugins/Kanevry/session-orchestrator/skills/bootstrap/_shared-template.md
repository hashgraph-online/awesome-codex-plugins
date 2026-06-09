# Bootstrap Shared Template Partials

> This file is NOT a standalone template. It contains shared step definitions
> referenced from `standard-template.md` and `deep-template.md` via
> `<!-- @include _shared-template.md#section-name -->` markers.
>
> When the bootstrap skill reads a tier template, sections marked with an
> include marker must be sourced from the corresponding heading in this file.
> The tier templates remain fully readable on their own — the markers serve as
> an editorial cross-reference so the canonical text lives in one place.

---

## #parallel-sessions-rule — Step 3a: Install Parallel-Sessions Rule

Write the vendored rule from `$PLUGIN_ROOT/templates/_shared/rules/parallel-sessions.md` to `$REPO_ROOT/.claude/rules/parallel-sessions.md`.

Idempotency:
- Missing → create
- Exists and byte-identical → skip silently
- Exists and differs → overwrite (vendored is canonical)

Shell:
```bash
mkdir -p "$REPO_ROOT/.claude/rules"
cp "$PLUGIN_ROOT/templates/_shared/rules/parallel-sessions.md" "$REPO_ROOT/.claude/rules/parallel-sessions.md"
```

Why: PSA-003 destructive-command safeguards require every consumer repo to carry the rule. See issue #155.

Note: This step runs before the baseline-fetch step (S99/D99). If that step executes and fetches a newer version of `parallel-sessions.md` from the baseline, the baseline version wins (S99 overwrites by design — acceptable).

---

## #agents-scaffold — Step: .claude/agents/ Scaffold (#189)

Copy the opinionated agent templates into the consumer repo:

```bash
mkdir -p "$REPO_ROOT/.claude/agents"
cp "$PLUGIN_ROOT/skills/bootstrap/templates/agents/"*.md "$REPO_ROOT/.claude/agents/"
```

This scaffolds 3 opinionated agents (`project-discovery`, `project-code-review`, `project-quality-gate`) following CLAUDE.md Agent Authoring Rules. Consumer repos should edit descriptions/bodies to match project specifics — but keep the frontmatter structure intact (validated by `agent-frontmatter-invalid` probe).

**Idempotency:** Existing files under `.claude/agents/` are not overwritten — skip any file that already exists.

---

## #vault-registration — Step: Vault-Registration Prompt (Product Repos) (#190)

If this repo shows product-repo signals (framework dep + personas/content dir + product env vars), offer to register a vault entry in Session Config.

**Detection (via `scripts/lib/product-repo-detect.mjs`):**

```bash
node --input-type=module -e "
import { detectProductRepo, hasVaultConfig } from '${PLUGIN_ROOT}/scripts/lib/product-repo-detect.mjs';
const result = detectProductRepo({ repoRoot: process.cwd() });
const already = hasVaultConfig('$REPO_ROOT/CLAUDE.md') || hasVaultConfig('$REPO_ROOT/AGENTS.md');
if (!result.isProductRepo || already) process.exit(0);
process.stdout.write(JSON.stringify(result, null, 2));
process.exit(10);  // signal: prompt user
"
```

When the script exits 10 (product signals detected, no vault yet): prompt the user:

> Repo appears to carry product data (framework: \<detected>, signals: \<list>). Create vault registration in Session Config? [Y/n]

**On Y (default):** Append the following block to the `## Session Config` section of CLAUDE.md:

```yaml
vault:
  path: ${VAULT_PATH:-$HOME/Projects/vault}
  product-domain: <prompt user for a short domain tag, e.g. "buchhaltung", "lead-gen">
  persona-db: <optional: path to persona data file, blank if N/A>
```

**On N:** skip silently. The detection may re-run on next bootstrap; idempotency comes from `hasVaultConfig` — once `vault:` exists in Session Config, the prompt is skipped.

**Examples from real repos:**

| Repo | Framework | Signals | Vault Entry |
|------|-----------|---------|-------------|
| ExampleSaaS | Next.js | supabase, stripe, personas/ | `product-domain: accounting` |
| ExampleLeadGen | Next.js | stripe, posthog | `product-domain: lead-gen` |
| ExamplePortfolio | Nuxt | postgres, sentry | `product-domain: portfolio` |

**Idempotent.** If CLAUDE.md already has a `vault:` key inside Session Config, the prompt is skipped.

---

## #baseline-fetch — Step S99: (Optional) Fetch Canonical Rules + Agents from Baseline

This step is OPT-IN and only executes when ALL of the following are true:
- `baseline-ref` is present in Session Config (e.g., `baseline-ref: main`)
- `GITLAB_TOKEN` env var is set
- The session-orchestrator plugin includes `scripts/lib/fetch-baseline.mjs`
- A GitLab host is resolvable (`gitlab-host` Session Config key or `GITLAB_HOST` env)

When triggered, this step pulls the canonical `.claude/rules/*.md` and (optionally) `.claude/agents/*.md` files directly from the baseline GitLab project (project 52 by default) into the new repo, then writes `.claude/.baseline-fetch.lock` recording the fetch.

Without this step, rules arrive in the repo via Clank's weekly baseline sync MRs (the legacy path). This step short-circuits that delay so a freshly-bootstrapped repo starts with current rules immediately.

**Implementation:**

```bash
BASELINE_REF=$(echo "$CONFIG" | jq -r '."baseline-ref" // empty')
BASELINE_PROJECT_ID=$(echo "$CONFIG" | jq -r '."baseline-project-id" // "52"')

# The .mjs fetcher requires a GitLab host (it fails closed with no private default).
# Resolve it from Session Config (`gitlab-host`) or the GITLAB_HOST env var — never a hardcoded default.
GITLAB_HOST_CFG=$(echo "$CONFIG" | jq -r '."gitlab-host" // empty')
export GITLAB_HOST="${GITLAB_HOST:-$GITLAB_HOST_CFG}"

if [[ -n "$BASELINE_REF" && -n "${GITLAB_TOKEN:-}" && -n "${GITLAB_HOST:-}" && -f "$PLUGIN_ROOT/scripts/lib/fetch-baseline.mjs" ]]; then
  # Default rule manifest — superset will harmlessly 404 individual files
  # if the baseline ever drops one (cache will keep last-known-good).
  RULES_MANIFEST=$(mktemp)
  cat > "$RULES_MANIFEST" <<MANIFEST
.claude/rules/development.md
.claude/rules/security.md
.claude/rules/security-web.md
.claude/rules/security-compliance.md
.claude/rules/testing.md
.claude/rules/test-quality.md
.claude/rules/frontend.md
.claude/rules/backend.md
.claude/rules/backend-data.md
.claude/rules/infrastructure.md
.claude/rules/swift.md
.claude/rules/mvp-scope.md
.claude/rules/cli-design.md
.claude/rules/parallel-sessions.md
.claude/rules/ai-agent.md
.claude/rules/claude-code-usage.md
MANIFEST

  echo "Fetching canonical rules from baseline (project $BASELINE_PROJECT_ID, ref $BASELINE_REF)…"
  # The .mjs CLI is single-file: it prints ONE file body to stdout, exit 0 on success
  # (1=auth, 2=404, 3=network). There is no batch and no lock-write in the CLI — the
  # bootstrap layer orchestrates the per-rule loop and writes the lock itself.
  SUCCESS_LOG=$(mktemp)
  while IFS= read -r rule_path; do
    [[ -z "$rule_path" ]] && continue
    mkdir -p "$REPO_ROOT/$(dirname "$rule_path")"
    if node "$PLUGIN_ROOT/scripts/lib/fetch-baseline.mjs" \
         "$BASELINE_PROJECT_ID" "$rule_path" "$BASELINE_REF" > "$REPO_ROOT/$rule_path"; then
      printf '%s\n' "$rule_path" >> "$SUCCESS_LOG"
    else
      # A 404 (or any error) for one rule must not abort the batch — drop the empty
      # target the redirect created and continue with the next manifest line.
      rm -f "$REPO_ROOT/$rule_path"
    fi
  done < "$RULES_MANIFEST"

  if [[ -s "$SUCCESS_LOG" ]]; then
    FETCHED_JSON=$(jq -R . < "$SUCCESS_LOG" | jq -s .)
    LOCK_FILE="$REPO_ROOT/.claude/.baseline-fetch.lock"
    mkdir -p "$REPO_ROOT/.claude"
    node --input-type=module -e "
      import { writeFileSync } from 'node:fs';
      const files = JSON.parse(process.env.FETCHED_JSON);
      const lock = {
        version: 1,
        project_id: Number(process.env.BASELINE_PROJECT_ID),
        baseline_ref: process.env.BASELINE_REF,
        fetched_at: new Date().toISOString().replace(/\.\d{3}Z\$/, 'Z'),
        files,
      };
      writeFileSync(process.env.LOCK_FILE, JSON.stringify(lock, null, 2) + '\n');
    " FETCHED_JSON="$FETCHED_JSON" BASELINE_PROJECT_ID="$BASELINE_PROJECT_ID" \
        BASELINE_REF="$BASELINE_REF" LOCK_FILE="$LOCK_FILE"
    echo "Wrote .claude/.baseline-fetch.lock ($(wc -l < "$SUCCESS_LOG" | tr -d ' ') files)"
  else
    echo "WARNING: baseline fetch produced no files; rules will arrive via Clank sync MRs (legacy path)" >&2
  fi
  rm -f "$SUCCESS_LOG"
  rm -f "$RULES_MANIFEST"
else
  echo "Skipping baseline fetch: baseline-ref / GITLAB_TOKEN / GITLAB_HOST not configured (legacy Clank-sync path)"
fi
```

**Failure handling:** If the fetch fails, this step DOES NOT abort bootstrap. The repo still has its scaffold; rules will arrive via the legacy Clank weekly sync MR. The user is informed via stderr.

**Idempotency:** Re-running bootstrap on an existing repo will overwrite `.claude/rules/*.md` files. Local edits to baseline rules in a repo will be lost on re-fetch — this is intentional (rules are canonical). Repo-specific extensions belong in `.claude/rules/local/*.md` (not fetched).

---

## #quality-gate-policy — Step 6.5: Quality-Gate Policy File (#183)

Write the canonical quality-gate commands to `.orchestrator/policy/quality-gates.json`. Bootstrap detects the package manager and writes sensible defaults; users may hand-edit afterwards.

**Idempotency:** Skip this step if `.orchestrator/policy/quality-gates.json` already exists. Do not overwrite user edits.

```bash
POLICY_FILE="$REPO_ROOT/.orchestrator/policy/quality-gates.json"
if [[ ! -f "$POLICY_FILE" ]]; then
  mkdir -p "$REPO_ROOT/.orchestrator/policy"
  # Detect package manager via scripts/lib/package-manager.mjs (falls back to npm defaults)
  PM_JSON="$(node --input-type=module -e "
    import { detectPackageManager, defaultQualityGateCommands } from '$PLUGIN_ROOT/scripts/lib/package-manager.mjs';
    const pm = detectPackageManager('$REPO_ROOT');
    process.stdout.write(JSON.stringify(defaultQualityGateCommands(pm)));
  " 2>/dev/null)"

  # Fallback if node helper unavailable: hardcode npm defaults
  if [[ -z "$PM_JSON" ]]; then
    PM_JSON='{"test":{"command":"npm test","required":true},"typecheck":{"command":"npm run typecheck","required":true},"lint":{"command":"npm run lint","required":true}}'
  fi

  jq -n --argjson cmds "$PM_JSON" '{
    "version": 1,
    "rationale": "Canonical quality-gate commands. Generated by bootstrap. Edit to change test/typecheck/lint invocations across skills. Schema: .orchestrator/policy/quality-gates.schema.json",
    "commands": $cmds
  }' > "$POLICY_FILE"
  echo "Wrote $POLICY_FILE"
fi
```

---

## #state-md-scaffold — Step 6.6: STATE.md Scaffold (#184)

Scaffold a placeholder `.claude/STATE.md` using the template at `skills/bootstrap/STATE.md.template`. The placeholder records `status: idle` — sessions overwrite it at Pre-Wave 1b.

**Idempotency:** Skip if `.claude/STATE.md` already exists.

```bash
STATE_FILE="$REPO_ROOT/.claude/STATE.md"
if [[ ! -f "$STATE_FILE" ]]; then
  mkdir -p "$REPO_ROOT/.claude"
  ISO_NOW="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  sed "s|<ISO>|$ISO_NOW|g" "$PLUGIN_ROOT/skills/bootstrap/STATE.md.template" > "$STATE_FILE"
  echo "Wrote $STATE_FILE"
fi
```

On Codex CLI / Cursor IDE, substitute `.codex/` or `.cursor/` for `.claude/` per the platform state-directory convention.
