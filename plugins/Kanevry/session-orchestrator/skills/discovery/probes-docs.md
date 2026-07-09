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
