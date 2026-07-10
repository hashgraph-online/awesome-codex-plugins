> See probes-intro.md for confidence scoring reference.

## Category: `docs`

### Probe: docs-staleness

**Activation:** `docs/` directory present in the repo root **AND** Session Config `docs-staleness.enabled: true`.

**Detection Method:**

```bash
# Step 1: Verify the probe exists; skip if missing
test -f skills/discovery/probes/docs-staleness.mjs || { echo "SKIPPED: docs-staleness -- skills/discovery/probes/docs-staleness.mjs not found"; exit 0; }

# Step 2: Run the probe. It reads docs-staleness.thresholds.living from $CONFIG
# (passed from the discovery skill) and scans docs/*.md (root level) +
# docs/examples/*.md for filesystem-mtime staleness.
node --input-type=module -e "
import {runProbe} from './skills/discovery/probes/docs-staleness.mjs';
const cfg = JSON.parse(process.env.SO_CONFIG || '{}');
const r = await runProbe(process.cwd(), cfg);
for (const f of r.findings) {
  console.log('FINDING:', JSON.stringify(f));
}
console.log('METRICS:', JSON.stringify(r.metrics));
if (r.skipped_reason) console.log('SKIPPED:', r.skipped_reason);
"
```

**Output:** one `FINDING:` line per finding, one `METRICS:` line per run. Summary JSONL record appended to `.orchestrator/metrics/docs-staleness.jsonl`.

**Default severity:** low (within 2× the `living` threshold), medium (within 3×), high (beyond 3×). mtime-cannot-be-read errors → low.

**Threshold (days):** `living` = 90 (default). Configurable via Session Config `docs-staleness.thresholds.living`; non-numeric or non-positive values fall back to the default.

**Scope:** only `docs/*.md` (root level, non-recursive) and `docs/examples/*.md` are scanned. `docs/adr/` (historically stable, immutable-by-design decision records) and `docs/prd/` (active work-in-progress documents scoped to a project's lifecycle) are deliberately excluded — staleness there is expected and not a defect. Other `docs/` subdirectories are out of scope for this probe.

---

**Config-only gate (no scope token):** `docs-staleness` follows the same pattern as the supply-chain probe — activation is config-gated (`docs-staleness.enabled: true`), not exposed as a `/discovery` `scope` argument value. See `skills/discovery/SKILL.md` Phase 2 marker table and Phase 3 dispatch bullet.

---

### Probe: ssot-code-diff

**Activation:** `CLAUDE.md` or `README.md` present in the repo root. No Session Config gate — this probe always runs when the docs category is dispatched.

**Detection Method:**

```bash
# Step 1: Verify the probe exists; skip if missing
test -f skills/discovery/probes/ssot-code-diff.mjs || { echo "SKIPPED: ssot-code-diff -- skills/discovery/probes/ssot-code-diff.mjs not found"; exit 0; }

# Step 2: Run the probe. It reads no config keys — it diffs a hand-curated
# registry of doc "count" claims (blocked-commands.json rules, .claude/rules/
# file count, skills/ user-facing directory count, commands/ file count)
# against the live code/filesystem value each claim describes.
node --input-type=module -e "
import {runProbe} from './skills/discovery/probes/ssot-code-diff.mjs';
const cfg = JSON.parse(process.env.SO_CONFIG || '{}');
const r = await runProbe(process.cwd(), cfg);
for (const f of r.findings) {
  console.log('FINDING:', JSON.stringify(f));
}
console.log('METRICS:', JSON.stringify(r.metrics));
if (r.skipped_reason) console.log('SKIPPED:', r.skipped_reason);
"
```

**Output:** one `FINDING:` line per finding, one `METRICS:` line per run. Summary JSONL record appended to `.orchestrator/metrics/ssot-code-diff.jsonl`.

**Default severity:** high for the `blocked-commands.json` rule-count registry entry (policy/security-relevant — Destructive-Command Guard); medium for the other three registry entries (`.claude/rules/*.md` count, `skills/` user-facing count, `commands/*.md` count). All findings carry confidence 0.9.

**Threshold:** none (this is an exact-match diff, not a staleness window) — any claimed count that does not equal the live code/filesystem count is a finding.

**Scope:** a deliberately conservative, hand-curated claim registry (v1, four entries) over a fixed small set of known doc sources (`CLAUDE.md`, `AGENTS.md`, `.orchestrator/steering/structure.md`, `skills/hook-development/SKILL.md` for the policy-related entries; `README.md`, `docs/components.md`, `.orchestrator/steering/structure.md` for the inventory entries). `CHANGELOG.md`, `docs/adr/`, `docs/prd/`, and `docs/retro/` are never scanned — same principle as the docs-staleness probe (historical/immutable documents are not "living" claims to re-verify). A missing code/filesystem source (e.g. `blocked-commands.json` absent) gracefully skips that one registry entry only; it never throws.
