---
name: bootstrap
user-invocable: true
tags: [bootstrap, setup, scaffold, init]
model: sonnet
model-preference: sonnet
model-preference-codex: gpt-5.4-mini
model-preference-cursor: claude-sonnet-4-6
description: >
  Use this skill when scaffolding the minimum repository structure required by session-orchestrator.
  Invoked automatically by the Bootstrap Gate when CLAUDE.md, Session Config,
  or bootstrap.lock is missing. Also available as /bootstrap for manual invocation.
  Three intensity tiers: fast (demos/spikes), standard (MVPs), deep (production/team).
---

# Bootstrap Skill

## Overview

This skill runs when the Bootstrap Gate is closed (missing CLAUDE.md, Session Config, or `.orchestrator/bootstrap.lock`) or when the user invokes `/bootstrap` directly. It scaffolds the minimum structure required by all session-orchestrator skills, commits it, and writes the lock file that opens the gate for all future invocations.

**Anti-bureaucracy contract:** At most ONE `AskUserQuestion` call in the normal case (tier confirmation). A second question is only asked when the archetype is truly ambiguous on the Public Path for Standard/Deep tiers. No wizard, no multi-step flow.

## Invocation Context

Before starting, determine how this skill was invoked:

- **Transitive (gate-closed):** Invoked from another skill's Phase 0. The user's original intent (their first prompt) is available in context. After bootstrap completes, execution must return to the original skill's Phase 1.
- **Direct (`/bootstrap`):** User invoked manually. Parse `$ARGUMENTS` for flags: `--fast`, `--standard`, `--deep`, `--upgrade <tier>`, `--retroactive`. See `commands/bootstrap.md` for flag semantics.

Store `INVOCATION_MODE = transitive | direct`.

**Mode dispatch (direct invocation only):**
- If `--upgrade <tier>` is present in `$ARGUMENTS`: jump to **Upgrade Flow** section. Do not proceed to Phase 1.
- If `--retroactive` is present in `$ARGUMENTS`: jump to **Retroactive Flow** section. Do not proceed to Phase 1.
- If `--sync-rules` is present in `$ARGUMENTS`: jump to **Sync-Rules Flow** section. Do not proceed to Phase 1.
- If `--ecosystem-health` is present in `$ARGUMENTS`: jump to **Ecosystem-Health Flow** section. Do not proceed to Phase 1.
- Otherwise: continue to Phase 1 below.

## Phase 0.5: Determine Private vs. Public Path

**Before dispatching to any tier template**, read `skills/bootstrap/public-fallback.md` and execute Step 1 (PATH_TYPE detection). Store the result as `PATH_TYPE = private | public`. This detection is silent — no user interaction.

- `private`: `plan-baseline-path` is present in Session Config AND the path exists on disk. Baseline templates will be used for CLAUDE.md generation and archetype file sourcing.
- `public`: `plan-baseline-path` is absent, empty, or points to a non-existent path. Plugin-bundled templates from `templates/` will be used.

Pass `PATH_TYPE` into Phase 1 and all subsequent phases. All tier templates (`fast-template.md`, `standard-template.md`, `deep-template.md`) must consult `public-fallback.md` for CLAUDE.md generation and archetype file sourcing when `PATH_TYPE = public`.

## Phase 1: Detect Tier + Archetype

Read `skills/bootstrap/intensity-heuristic.md` and execute the tier + archetype recommendation algorithm.

Inputs to the heuristic:
1. **User's first prompt** — the message that triggered this skill (most important signal)
2. **Repo name** — `basename $(git rev-parse --show-toplevel)` (secondary signal)
3. **Existing files** — `ls -la` of repo root (presence of `package.json`, `pyproject.toml`, etc. shifts archetype)
4. **$ARGUMENTS flags** — if `--fast`, `--standard`, or `--deep` is present, skip heuristic and use the specified tier directly

Output from Phase 1:
- `RECOMMENDED_TIER` = `fast` | `standard` | `deep`
- `RECOMMENDED_ARCHETYPE` = `static-html` | `node-minimal` | `nextjs-minimal` | `python-uv` | `null`
- `HEURISTIC_REASON` = one-sentence explanation of why this tier was chosen (shown to user)
- `PATH_TYPE` = `private` (plan-baseline-path configured and path exists) | `public` (no baseline)

**Detecting PATH_TYPE:** Already determined in Phase 0.5 — use the stored `PATH_TYPE` value. Do not re-run detection.

**Fast tier:** `RECOMMENDED_ARCHETYPE` is always `null`. No stack selection needed.

## Phase 2: Present Tier Confirmation (One Question)

Present exactly one `AskUserQuestion` unless:
- `$ARGUMENTS` includes `--fast`, `--standard`, or `--deep` (tier pre-selected, skip question)
- `--retroactive` flag (no scaffolding at all, skip to Phase 4)

```
AskUserQuestion({
  questions: [{
    question: "Leeres Repo erkannt. Basierend auf '<HEURISTIC_REASON>' empfehle ich **<RECOMMENDED_TIER>**. Passt das?",
    header: "Bootstrap",
    options: [
      { label: "<RECOMMENDED_TIER> (Empfohlen)", description: "<one-line description of what this tier scaffolds>" },
      { label: "fast", description: "Nur CLAUDE.md + .gitignore + README. Für Demos, Spikes, Playgrounds." },
      { label: "standard", description: "Fast + package.json/Manifest + TypeScript + Linting + Tests. Für MVPs und echte Produkte." },
      { label: "deep", description: "Standard + CI + CODEOWNERS + CHANGELOG. Für Production, Team, Langlebige Repos." },
      { label: "Abbrechen", description: "Bootstrap abbrechen. Das ursprüngliche Kommando wird ebenfalls abgebrochen." }
    ],
    multiSelect: false
  }]
})
```

If user selects "Abbrechen": stop. Report "Bootstrap abgebrochen. Kein Kommando wird ausgeführt." Do not continue.

Store confirmed tier as `CONFIRMED_TIER`.

### Optional Second Question (Public Path + Standard/Deep + Ambiguous Archetype Only)

If ALL of the following are true:
1. `PATH_TYPE = public`
2. `CONFIRMED_TIER` is `standard` or `deep`
3. `intensity-heuristic.md` returned `ARCHETYPE_CONFIDENCE = low` (truly ambiguous)

Then ask one more question — and only then:

```
AskUserQuestion({
  questions: [{
    question: "Welchen Tech-Stack soll ich für das Grundgerüst verwenden?",
    header: "Archetype",
    options: [
      { label: "node-minimal", description: "package.json + TypeScript + Vitest. Für CLIs, Tools, Libraries." },
      { label: "nextjs-minimal", description: "Next.js bare setup. Für Web Apps, SaaS, Fullstack." },
      { label: "static-html", description: "HTML/CSS/JS, kein Build-Step. Für Animationen, Landingpages, Visualisierungen." },
      { label: "python-uv", description: "pyproject.toml + uv + pytest. Für Python Scripts, APIs, ML." }
    ],
    multiSelect: false
  }]
})
```

Store as `CONFIRMED_ARCHETYPE`. Maximum interactions in bootstrap flow: **2 questions total**.

## Upgrade Flow (`--upgrade <tier>`)

Entered when `$ARGUMENTS` contains `--upgrade <tier>`. No scaffolding questions are asked.

**Steps:**

1. **Read existing lock.** Read `.orchestrator/bootstrap.lock`. If missing, abort with: `Error: No bootstrap.lock found. Run /bootstrap first to bootstrap this repo.`

2. **Parse current and target tier.**
   - `CURRENT_TIER` = value of `tier:` field in the lock file.
   - `TARGET_TIER` = the `<tier>` argument supplied after `--upgrade`.
   - Valid values for both: `fast` | `standard` | `deep`.

3. **Refuse downgrade.** Tier order: `fast < standard < deep`. If `TARGET_TIER` ranks lower than or equal to `CURRENT_TIER`, abort with:
   `Error: Cannot downgrade from <CURRENT_TIER> to <TARGET_TIER>. Upgrade path is one-directional (fast → standard → deep).`
   Exit non-zero.

4. **Compute delta.** Determine which files the target tier adds over the current tier:
   - `fast → standard`: all Standard-tier files (`package.json`/`pyproject.toml`, `tsconfig.json`, `eslint.config.mjs`, `.prettierrc`, `.editorconfig`, `tests/`, `src/`)
   - `standard → deep`: all Deep-tier files (CI pipeline, `CODEOWNERS`, `CHANGELOG.md`, issue templates, MR/PR template, branch protection)
   - `fast → deep`: union of both deltas (apply Standard first, then Deep)

5. **Check idempotency.** For each file in the delta, skip if it already exists on disk. Only write files that are absent. This makes the operation safe to run twice.

6. **Apply delta files.** Execute only the relevant template steps for the missing files. Read the appropriate template (`standard-template.md` and/or `deep-template.md`) and execute ONLY the steps that produce the delta files. Do NOT re-run already-completed steps.

7. **Update bootstrap.lock atomically.** Overwrite `.orchestrator/bootstrap.lock` with `tier: <TARGET_TIER>`. Preserve `archetype`, `timestamp` (update to now), and `source` from the existing lock. Write `plugin-version` from `$PLUGIN_ROOT/package.json` (current plugin version at upgrade time).

8. **Commit.** Stage only the delta files that were just written and commit:
   ```bash
   # DELTA_FILES must be populated with the explicit list of files written in step 6
   for _f in "${DELTA_FILES[@]}"; do
     [[ -e "$_f" ]] && git add -- "$_f"
   done
   git commit -m "chore: bootstrap upgrade to <TARGET_TIER>"
   ```

9. **Report.** Print a one-line summary: `Bootstrap upgraded from <CURRENT_TIER> to <TARGET_TIER>. <N> files added.`

---

## Retroactive Flow (`--retroactive`)

Entered when `$ARGUMENTS` contains `--retroactive`. Writes the lock file and, per #182, optionally patches missing mandatory Session Config fields with defaults.

**Purpose:** Adopt an existing repo that already has `CLAUDE.md` + `## Session Config` but was bootstrapped manually (no `bootstrap.lock`). Writes the lock so the gate passes on all future invocations, and ensures the Session Config block satisfies the validated schema defined in `scripts/lib/config-schema.mjs`.

**Steps:**

1. **Verify preconditions.** Confirm `CLAUDE.md` (or `AGENTS.md`) exists and contains `## Session Config`. If not, abort: `Error: CLAUDE.md with Session Config required for retroactive bootstrap.`

2. **Check lock not already present.** If `.orchestrator/bootstrap.lock` already exists and has valid `version` + `tier` fields, report: `bootstrap.lock already present (tier: <tier>). Nothing to do.` and exit 0 (idempotent).

3. **Infer tier from file inventory.** Examine the repo root:

   | Condition (evaluated in order) | Inferred Tier |
   |---|---|
   | CI file present (`.gitlab-ci.yml` OR `.github/workflows/`) AND `CHANGELOG.md` present | `deep` |
   | Package manifest present (`package.json` OR `pyproject.toml`) | `standard` |
   | Neither of the above | `fast` |

   Store as `INFERRED_TIER`.

4. **Infer archetype.** Best-effort detection from existing files:
   - `pyproject.toml` present → `python-uv`
   - `package.json` with `next` in dependencies → `nextjs-minimal`
   - `package.json` without `next` → `node-minimal`
   - No manifest → `null`

   Store as `INFERRED_ARCHETYPE`.

5. **Write bootstrap.lock.** Create `.orchestrator/` if needed, then write:
   ```yaml
   # .orchestrator/bootstrap.lock
   version: 1
   tier: <INFERRED_TIER>
   archetype: <INFERRED_ARCHETYPE or null>
   timestamp: <current ISO 8601 UTC>
   source: retroactive
   plugin-version: <current plugin version from $PLUGIN_ROOT/package.json>
   ```

6. **Patch Session Config (#182).** Run the validator against the current `## Session Config` block; append any missing mandatory fields with defaults. The 7 mandatory fields (per `scripts/lib/config-schema.mjs`) are: `test-command`, `typecheck-command`, `lint-command`, `agents-per-wave`, `waves`, `persistence`, `enforcement`.

   ```bash
   CONFIG_OUT="$(node "$PLUGIN_ROOT/scripts/parse-config.mjs" 2>&1 >/dev/null)"
   # parse-config.mjs emits validation warnings to stderr when enforcement=warn.
   # Grep for 'must be' lines (issued by validate-config.mjs) to detect missing fields.
   MISSING_FIELDS="$(echo "$CONFIG_OUT" | grep -oE '(test-command|typecheck-command|lint-command|agents-per-wave|waves|persistence|enforcement)' | sort -u || true)"
   if [[ -n "$MISSING_FIELDS" ]]; then
     # Detect package manager to pick sensible defaults for commands.
     PM_DEFAULTS="$(node --input-type=module -e "
       import {detectPackageManager, defaultQualityGateCommands} from '$PLUGIN_ROOT/scripts/lib/package-manager.mjs';
       const pm = detectPackageManager(process.cwd());
       const cmds = defaultQualityGateCommands(pm);
       console.log('test-command: ' + cmds.test.command);
       console.log('typecheck-command: ' + cmds.typecheck.command);
       console.log('lint-command: ' + cmds.lint.command);
     " 2>/dev/null)"

     CONFIG_FILE="CLAUDE.md"
     [[ -f "AGENTS.md" ]] && CONFIG_FILE="AGENTS.md"

     # Append each missing field under the ## Session Config block.
     for field in $MISSING_FIELDS; do
       case "$field" in
         test-command|typecheck-command|lint-command)
           default_line="$(echo "$PM_DEFAULTS" | grep "^$field:")" ;;
         agents-per-wave) default_line="agents-per-wave: 6" ;;
         waves)           default_line="waves: 5" ;;
         persistence)     default_line="persistence: true" ;;
         enforcement)     default_line="enforcement: warn" ;;
       esac
       # Insert after `## Session Config` line if not already present.
       grep -q "^$field:" "$CONFIG_FILE" \
         || awk -v insert="$default_line" '/^## Session Config/ && !done { print; print ""; print insert; done=1; next } { print }' "$CONFIG_FILE" > "$CONFIG_FILE.tmp" \
         && mv "$CONFIG_FILE.tmp" "$CONFIG_FILE"
     done
     echo "Patched $CONFIG_FILE with defaults for: $MISSING_FIELDS"
   fi
   ```

   This patch is best-effort: existing fields are never overwritten. If no fields are missing, this step is a no-op.

7. **Commit.** Stage the lock file (and the patched config file, if it changed) and commit:
   ```bash
   mkdir -p .orchestrator
   git add .orchestrator/bootstrap.lock
   # Also stage CLAUDE.md/AGENTS.md if step 6 patched it.
   git diff --name-only --cached CLAUDE.md AGENTS.md 2>/dev/null | head -1 >/dev/null || {
     [[ -f CLAUDE.md ]] && git diff --quiet CLAUDE.md || git add CLAUDE.md
     [[ -f AGENTS.md ]] && git diff --quiet AGENTS.md || git add AGENTS.md
   }
   git commit -m "chore: bootstrap lock (retroactive)"
   ```

8. **Report.** Print: `Retroactive bootstrap complete. Lock written (tier: <INFERRED_TIER>, source: retroactive).` Include a second line `Patched Session Config: <fields>` when step 6 applied any patches, otherwise `No config changes.`.

---

## Sync-Rules Flow (`--sync-rules`)

Entered when `$ARGUMENTS` contains `--sync-rules`. This is a standalone flow — it short-circuits the tier/archetype/scaffolding flow. No `bootstrap.lock` read, no template dispatched, no initial commit.

**Purpose:** Vendor canonical rules from the plugin's `rules/` library (`rules/always-on/*.md`, and in the future `rules/opt-in-stack/*.md` and `rules/opt-in-domain/*.md`) into the consumer repo's `.claude/rules/`. Plugin-sourced files (identified by a `<!-- source: session-orchestrator plugin … -->` header) are overwritten on re-run; files without that header are preserved as local overrides. See `rules/_index.md` for the canonical manifest and `scripts/lib/rules-sync.mjs` for the implementation.

**Steps:**

1. **Resolve plugin root.** The plugin's `rules/_index.md` lives next to `SKILL.md`'s plugin directory. Use the plugin root inferred by the harness (`PLUGIN_ROOT`).

2. **Invoke `scripts/lib/rules-sync.mjs`.** Run the CLI entrypoint from the consumer repo:

   ```bash
   node "$PLUGIN_ROOT/scripts/lib/rules-sync.mjs" --repo-root "$(pwd)"
   ```

   The script reads `rules/_index.md` from the plugin, iterates `always-on/` sources, and writes each file into `.claude/rules/` under the target repo. Stdout is a JSON object with `written[]`, `skipped[]`, `preserved[]`, and `errors[]`. Exit 1 on any error, 0 otherwise.

   Add `--dry-run` to preview without writing.

3. **Interpret the output.** Report a human summary:
   - `written`: files newly created OR plugin-owned files overwritten with fresh canonical content.
   - `skipped`: plugin-owned files already up-to-date (byte-identical).
   - `preserved`: existing `.claude/rules/*.md` files that do NOT carry the plugin source header — left untouched as local overrides.
   - `errors`: per-file failures (missing source, read/write errors, malformed `_index.md`).

4. **Commit (optional).** `--sync-rules` does not auto-commit. If rules changed, prompt the user to review `git status` and stage/commit the updates manually. Rationale: rules are canonical artifacts and should travel with an intentional review, not land silently.

5. **Report.** Print: `rules-sync complete. Written: <N>. Skipped: <N>. Preserved: <N>. Errors: <N>.` If `errors > 0`, non-zero exit.

**Local overrides.** Any `.claude/rules/<name>.md` without the plugin source header is considered local and never overwritten. To replace a local override with the canonical version, delete it before re-running.

**Idempotency.** Running `/bootstrap --sync-rules` twice in a row with no upstream changes emits `written: 0, skipped: <N>`. Safe to wire into CI or scheduled maintenance.

---

## Phase 3: Dispatch to Template

Based on `CONFIRMED_TIER`, read and execute the corresponding template file:

| Tier | Template File |
|------|--------------|
| `fast` | `skills/bootstrap/fast-template.md` |
| `standard` | `skills/bootstrap/standard-template.md` |
| `deep` | `skills/bootstrap/deep-template.md` |

Pass the following context into the template execution:
- `CONFIRMED_TIER`
- `CONFIRMED_ARCHETYPE`
- `PATH_TYPE`
- `REPO_ROOT` = `$(git rev-parse --show-toplevel)`
- `REPO_NAME` = `$(basename "$REPO_ROOT")`
- `PLATFORM` = detected platform from `skills/_shared/platform-tools.md`

Follow the template's instructions precisely. The template is responsible for creating all files and the initial git commit.

**Platform note for CLAUDE.md generation:**
When `PATH_TYPE = public`, read `skills/bootstrap/public-fallback.md` for the full platform-specific CLAUDE.md generation logic (claude init path for Claude Code; `_minimal` template synthesis for Codex/Cursor). When `PATH_TYPE = private`, use the baseline scripts at `$BASELINE_PATH`.

## Phase 3.4: Vault-Registration Prompt (#190)

Standard and Deep tier templates include Step 5.5 (standard) / D6.6 (deep) which runs `scripts/lib/product-repo-detect.mjs` to check for product-repo signals (framework dep, content dir, product env vars). When signals are detected and no `vault:` key exists in Session Config, the template prompts the user to register a vault entry. Idempotency via `hasVaultConfig`. Fast tier skips this step.

## Phase 3.5: Owner Persona Interview (first-run only)

> Closes session-orchestrator issues #175 (D2 owner interview) + #173 (C4 hardware-sharing consent).

**WHEN:** Runs after Phase 3.4 when `~/.config/session-orchestrator/owner.yaml` is absent AND `--no-interview` was NOT passed. Skipped entirely on `--upgrade`, `--retroactive`, `--sync-rules`, and `--ecosystem-health` flows.

**WHAT:** The coordinator dispatches 5 `AskUserQuestion` calls using definitions from `scripts/lib/owner-interview.mjs`:

1. **Language** — `de` | `en` | other (free text)
2. **Tone style** — `direct` (recommended) | `neutral` | `friendly`
3. **Output level** — `lite` (verbose) | `full` (default) | `ultra` (telegraphic)
4. **Preamble** — `minimal` (one-line updates) | `verbose` (explain before action)
5. **Hardware-sharing consent (C4)** — `No` (default) | `Yes` (generates random `hash-salt`) | `Preview`

**HOW (coordinator steps):**

```js
import { runOwnerInterview, getInterviewQuestions, applyInterviewAnswers } from '$PLUGIN_ROOT/scripts/lib/owner-interview.mjs';
const probe = runOwnerInterview({ skipIfExists: true });
if (probe.status === 'pending') {
  // dispatch AskUserQuestion for each of probe.questions, collect answers[]
  const result = applyInterviewAnswers(answers, { path: probe.path });
  // result: { ok, path, errors }
}
```

**WHERE:** Written to `~/.config/session-orchestrator/owner.yaml` (user-global, never committed).

**RE-TRIGGER:** `/bootstrap --owner-reset` sets `force: true` in `runOwnerInterview`, archives the existing yaml to `owner.yaml.bak-<timestamp>`, and re-runs the 5 questions.

## Phase 3.6: (Optional) Rules-Fetch Bridge

> Closes session-orchestrator issue #110.

After the tier template completes scaffolding (Phase 3), the Standard and Deep templates run an optional rules-fetch step that pulls canonical `.claude/rules/*.md` (and optionally `.claude/agents/*.md`) directly from the baseline GitLab project. The step is opt-in and only fires when:

- `baseline-ref` is present in Session Config
- `GITLAB_TOKEN` env var is set
- `scripts/lib/fetch-baseline.sh` is present in the plugin

When triggered, the step:

1. Sources `scripts/lib/fetch-baseline.sh` (defines `fetch_baseline_file`, `fetch_baseline_files_batch`, `write_baseline_fetch_lock`)
2. Fetches each rule listed in a default manifest from the configured `baseline-project-id` (default `52`) at the configured `baseline-ref`
3. Writes `.claude/.baseline-fetch.lock` recording what was fetched
4. Populates `.claude/.baseline-cache/` for offline fallback on subsequent invocations

When the fetch fails (network error, auth, missing file), bootstrap **does not abort**. Rules will arrive in the repo via Clank's weekly baseline sync MRs (the legacy path). A warning is printed.

**Why opt-in:** Repos without `baseline-ref` continue to receive rules via the existing Clank sync flow. The fetch bridge is a faster on-demand alternative for newly-bootstrapped repos that want current rules immediately.

**Local edits:** Re-running bootstrap with `baseline-ref` set will overwrite `.claude/rules/*.md` (rules are canonical). Repo-specific extensions belong in `.claude/rules/local/*.md` (not fetched, not overwritten).

See `standard-template.md` (Step S99) and `deep-template.md` (Step D99) for the implementation, and `docs/session-config-reference.md` for the `baseline-ref` and `baseline-project-id` field definitions.

### `.claude/.baseline-fetch.lock` Schema

The lock file is committed to git and records what was fetched.

```yaml
# .claude/.baseline-fetch.lock
version: 1
project_id: 52
baseline_ref: main
fetched_at: 2026-04-17T13:42:00Z   # ISO 8601 UTC
files:
  - .claude/rules/development.md
  - .claude/rules/security.md
  - .claude/rules/...
```

| Field | Description |
|---|---|
| `version` | Lock file schema version. Currently `1`. |
| `project_id` | GitLab project ID the files were fetched from. |
| `baseline_ref` | The git ref (branch/tag/SHA) at fetch time. |
| `fetched_at` | ISO 8601 UTC timestamp. |
| `files` | List of fetched file paths (relative to repo root). |

---

## Ecosystem-Health Flow (`--ecosystem-health`)

Entered when `$ARGUMENTS` contains `--ecosystem-health`. This is a **standalone flow** — it does not scaffold repo structure and does not write `bootstrap.lock`. Dispatch immediately; do not proceed to Phase 1.

**Purpose:** Populate the `health-endpoints`, `pipelines`, and `criticalIssueLabels` configuration consumed by `skills/ecosystem-health/SKILL.md`. Runs the interactive wizard in `scripts/lib/ecosystem-wizard.mjs`, which detects CI provider + package manager automatically and prompts the user for the remaining values.

**Steps:**

1. **Run the wizard.**

   ```bash
   node "$PLUGIN_ROOT/scripts/lib/ecosystem-wizard.mjs" --repo-root "$(pwd)"
   ```

   The wizard will:
   - Detect CI provider (`.gitlab-ci.yml` → `gitlab`; `.github/workflows/` → `github`; else `none`)
   - Detect package manager from lockfile
   - Prompt for health endpoints (format: `Name|URL`, comma-separated)
   - Prompt for CI pipeline identifiers (format: `id` or `id:label`, comma-separated)
   - Prompt for critical issue labels (comma-separated strings)

2. **Wizard writes two files** (or skips each if already present):
   - `CLAUDE.md` (or `AGENTS.md`) — appends `ecosystem-health:` block inside `## Session Config`
   - `.orchestrator/policy/ecosystem.json` — full policy file (schema: `.orchestrator/policy/ecosystem.schema.json`)

3. **No auto-commit.** The wizard prints what it wrote. The user reviews with `git status && git diff` and commits manually.

**Report:** The wizard prints a one-line summary per file:

```
Ecosystem-Health Wizard complete.
Written: .orchestrator/policy/ecosystem.json, CLAUDE.md
Skipped (already present): (none)

Review changes with: git status && git diff
```

**Idempotency:** Safe to re-run. If both output files are already present with matching content, the wizard exits 0 with "Nothing to do." To update, remove the existing `ecosystem-health:` key from Session Config and delete `.orchestrator/policy/ecosystem.json`, then re-run.

See `skills/ecosystem-health/wizard.md` for the full prompt spec and schema details.

---

## Phase 4: Write bootstrap.lock

After all template files are written and committed, write `.orchestrator/bootstrap.lock` (and, if the rules-fetch bridge ran, also `.claude/.baseline-fetch.lock` — see Phase 3.6):

```yaml
# .orchestrator/bootstrap.lock
version: 1
tier: <CONFIRMED_TIER>
archetype: <CONFIRMED_ARCHETYPE or null>
timestamp: <current ISO 8601 UTC timestamp>
source: <projects-baseline | plugin-template | claude-init>
plugin-version: <current plugin version from package.json>
```

Determine `source`:
- `projects-baseline` if `PATH_TYPE = private` and baseline scripts were used
- `claude-init` if `claude init` was used successfully on Claude Code
- `plugin-template` otherwise

Read `plugin-version` from the session-orchestrator plugin's `package.json` (`$PLUGIN_ROOT/package.json`, field `version`). This enables the freshness probe (#290) to detect plugin upgrades that need re-bootstrap. Example:

```bash
PLUGIN_VERSION="$(node -e "const p=require('$PLUGIN_ROOT/package.json');console.log(p.version);" 2>/dev/null || node --input-type=module -e "import pkg from '$PLUGIN_ROOT/package.json' assert {type:'json'}; console.log(pkg.version);")"
```

The template's initial git commit includes `bootstrap.lock`. If the template already wrote the lock file (as `fast-template.md` does), skip this step — the lock is already committed.

## Phase 5: Resume

Report bootstrap completion with a one-line summary:

```
Bootstrap complete (tier: <tier>, archetype: <archetype or "none">). Resuming <original command>…
```

If invoked transitively: return control to the originating skill. The original skill resumes from its Phase 1.
If invoked directly via `/bootstrap`: report the created files list and stop.

## Critical Rules

- **NEVER create application code during bootstrap** — only structural files (CLAUDE.md, .gitignore, README.md, manifests, CI). The feature that follows brings its own implementation.
- **NEVER skip the lock file write** — `.orchestrator/bootstrap.lock` is the gate's mechanical truth. Bootstrap without a lock file is incomplete.
- **NEVER ask more than 2 questions** — even if the user's intent is unclear, make a best-effort recommendation and let the user correct via `/bootstrap --upgrade` later.
- **ALWAYS commit** — bootstrap ends with a git commit. The lock file is part of that commit.
- **ALWAYS check for retroactive flag** — if `--retroactive` is in `$ARGUMENTS`, skip all scaffolding and jump directly to writing `bootstrap.lock` (tier inferred from existing file inventory, fallback: `fast`).
- **NEVER abort bootstrap on rules-fetch failure** — rules-fetch is opt-in and best-effort. The legacy Clank sync path is the safety net.
