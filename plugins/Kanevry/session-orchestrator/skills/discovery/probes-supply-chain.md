> See probes-intro.md for confidence scoring reference.

## Category: `supply-chain`

### Probe: supply-chain-slopcheck

**Activation:** One or more package manifests present (`package.json`, `requirements.txt`, or `Cargo.toml` in the repo root) **AND** Session Config `slopcheck.enabled: true` **AND** `slopcheck.sources` includes `"discovery"`.

When `slopcheck.enabled: false` (the default), this probe is silently skipped regardless of manifest presence.

**Detection Method:**

```bash
# Step 1: Verify gating conditions are met; skip otherwise
node -e "
const cfg = JSON.parse(process.env.SO_CONFIG || '{}');
const sc = cfg.slopcheck ?? {};
if (!sc.enabled) { console.log('SKIPPED: supply-chain-slopcheck -- slopcheck.enabled is false'); process.exit(0); }
const sources = Array.isArray(sc.sources) ? sc.sources : ['plan', 'discovery'];
if (!sources.includes('discovery')) { console.log('SKIPPED: supply-chain-slopcheck -- \"discovery\" not in slopcheck.sources'); process.exit(0); }
"

# Step 2: Run the probe
test -f skills/discovery/probes/supply-chain-slopcheck.mjs || { echo "SKIPPED: supply-chain-slopcheck -- probe file not found"; exit 0; }

node --input-type=module -e "
import probe from './skills/discovery/probes/supply-chain-slopcheck.mjs';
const r = await probe({ repoRoot: process.cwd() });
for (const f of r.findings) {
  console.log('FINDING:', JSON.stringify(f));
}
console.log('SUMMARY:', JSON.stringify(r.summary));
"
```

**Output:** one `FINDING:` line per non-LEGITIMATE package (up to `MAX_PACKAGES=100` sampled), one `SUMMARY:` line with counts. No external metrics file is written — findings are consumed directly by the discovery skill's Phase 4 aggregator.

**Classification → Severity mapping:**

| Classification | Severity | Meaning |
|---|---|---|
| `SLOP` | critical | Package not found in registry — likely a hallucinated name or typosquat target |
| `ASSUMED` | medium | Registry probe could not definitively classify (timeout, new package, unsupported registry) |
| `LEGITIMATE` | _(no finding)_ | Package exists in registry with published versions |
| `SUS` | _(reserved — never emitted in MVP)_ | See note below |

> **NOTE on SUS:** The `SUS` classification is defined in `CLASSIFICATIONS` (see `scripts/lib/slopcheck.mjs`) but is **never emitted** in the MVP. The npm-deprecated-flag and audit-warning detection paths that would produce SUS findings are not yet implemented. Do not rely on SUS findings until a future wave wires up that detection. See PRD § 5 in `docs/prd/2026-05-22-gsd-pattern-adoption-quickwins.md` for the full design intent.

**Supported manifest formats:**

| File | Registry | Notes |
|---|---|---|
| `package.json` | npm | `dependencies` + `devDependencies` |
| `requirements.txt` | pip | Name-only extraction; skips VCS/path deps |
| `Cargo.toml` | cargo | `[dependencies]` + `[dev-dependencies]`; skips `path =` and `git =` deps |

**Registry support matrix (MVP):**

| Registry | Classification | Status |
|---|---|---|
| npm | Full (`LEGITIMATE` / `SLOP` / `ASSUMED`) | Implemented — `npm view <pkg> versions --json` |
| pip | Always `ASSUMED` | Skeleton — full probe out-of-scope for MVP |
| cargo | Always `ASSUMED` | Skeleton — full probe out-of-scope for MVP |

**Fail-soft contract:**

- Missing manifest → silently skipped (no finding)
- `scripts/lib/slopcheck.mjs` unavailable → low-severity informational finding + summary note
- `classifyPackages()` throws → zero findings, error in summary `skipped_reason`
- >100 packages in repo → sample first 100, warn to stderr

**Output shape (from probe module):**

```json
{
  "probe": "supply-chain-slopcheck",
  "findings": [
    {
      "severity": "critical",
      "title": "Package \"hallucinated-pkg\" (npm) classified as SLOP",
      "evidence": { "name": "hallucinated-pkg", "registry": "npm", "classification": "SLOP", "file": "/repo/package.json" },
      "recommendation": "Package not found in registry. Verify the exact package name..."
    }
  ],
  "summary": { "total": 42, "legitimate": 38, "assumed": 3, "sus": 0, "slop": 1, "sampled": false, "errors": 0 }
}
```

**Module:** `skills/discovery/probes/supply-chain-slopcheck.mjs` (default export `async function supplyChainSlopcheck({ repoRoot })`).
Classifier: `scripts/lib/slopcheck.mjs` → `classifyPackages()`. Cache at `.orchestrator/runtime/slopcheck-cache.json` (24 h TTL).

---

**Session-end integration:** This probe is invoked only on-demand via `/discovery` (scope `all` or `supply-chain`). There is no automatic session-end invocation. The gating logic (`slopcheck.enabled: true` + `slopcheck.sources` includes `discovery`) is enforced by the probe itself — the discovery skill does not need separate gating logic beyond the stack-detection table in Phase 2.
