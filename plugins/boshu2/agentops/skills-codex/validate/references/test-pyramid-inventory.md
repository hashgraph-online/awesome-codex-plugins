# Test Pyramid Inventory (Step 2g, MANDATORY)

Assess test coverage against the test pyramid standard (the test pyramid standard (loaded via `/standards`)).

Read `skills/validate/references/test-pyramid-weighting.md` for test pyramid weighting — L3+ tests found all production bugs, weight them 5x.

**Test Pyramid Weighting:** Weight test coverage by level: L0–L1 at 1x, L2 at 3x, L3+ at 5x. Unit-only coverage is a WARN signal, not a PASS. See `references/test-pyramid-weighting.md`.

**Run even in `--quick` mode** — this is cheap (file existence checks) and high-signal.

1. **Identify changed modules** from git diff or target scope
2. **For each changed module, check coverage pyramid (L0–L3):**
   - L0: Does a contract/spec enforcement test cover this module?
   - L1: Does a unit test file exist for this module?
   - L2: If module crosses boundaries, does an integration test exist?
3. **For boundary-touching code, check bug-finding pyramid (BF1–BF5):**
   - BF4 (Chaos): Do external call sites have failure injection tests?
   - BF1 (Property): Do data transformations have property tests?
   - BF2 (Golden): Do output generators have golden file tests?
4. **Compute weighted pyramid score** for changed code paths:

   **Formula:**
   ```
   weighted_score = (L0_count x 1 + L1_count x 1 + L2_count x 3 + L3_count x 5 + L4_count x 5) / max_possible
   ```
   Where `max_possible = total_test_count x 5` (the score if every test were L3+).

   Count tests at each level for changed code paths:
   - L0: Build/compile checks (weight 1)
   - L1: Unit tests (weight 1)
   - L2: Integration tests (weight 3)
   - L3: E2E/system tests (weight 5)
   - L4: Smoke/fresh-context tests (weight 5)

   **Interpretation:**
   - `weighted_score >= 0.6` — strong pyramid, L2+ tests present
   - `0.3 <= weighted_score < 0.6` — acceptable, but recommend more integration tests
   - `weighted_score < 0.3` AND all tests are L0-L1 only — **WARN: unit-only test coverage** (feeds into vibe verdict as a WARN signal, not a separate gate)

   **Satisfaction exposure:** The `weighted_score` is also exposed as `satisfaction_score` (with source `"test-pyramid-weighted"`) in the test_pyramid output block AND promoted to the top-level verdict JSON as `satisfaction_score` (verdict schema field, `skills/council/schemas/verdict.json`: number 0.0-1.0, "Probabilistic satisfaction score (0.0 = unsatisfied, 1.0 = fully satisfied). Optional — absent means not computed."). Downstream consumers (e.g., `/validate` STEP 1.8 holdout evaluation) can use `satisfaction_score` as a normalized quality signal.

   **Include in council packet and vibe report output:**
   ```
   ## Test Pyramid Score
   | Level | Count | Weight | Contribution |
   |-------|-------|--------|--------------|
   | L0    | 2     | 1x     | 2            |
   | L1    | 8     | 1x     | 8            |
   | L2    | 0     | 3x     | 0            |
   | L3    | 0     | 5x     | 0            |
   | L4    | 0     | 5x     | 0            |
   | **Total** | **10** | | **10 / 50 = 0.20** |
   WARN: weighted_score 0.20 < 0.3 and all tests are L0-L1 only
   ```

5. **Build coverage table** and include in council packet as `context.test_pyramid`:

```json
"test_pyramid": {
  "coverage": {
    "L0": {"status": "pass", "files": ["test_spec_enforcement.py"]},
    "L1": {"status": "pass", "files": ["test_module.py"]},
    "L2": {"status": "gap", "reason": "crosses subsystem boundary, no integration test"}
  },
  "bug_finding": {
    "BF4_chaos": {"status": "gap", "reason": "external API calls without failure injection"},
    "BF1_property": {"status": "na", "reason": "no data transformations in scope"}
  },
  "weighted_score": 0.20,
  "satisfaction_score": 0.20,
  "satisfaction_source": "test-pyramid-weighted",
  "score_breakdown": {"L0": 2, "L1": 8, "L2": 0, "L3": 0, "L4": 0},
  "max_possible": 50,
  "warn_unit_only": true,
  "verdict": "WARN: weighted_score 0.20 < 0.3, all tests L0-L1 only"
}
```

**Verdict rules:**
- `weighted_score < 0.3` AND all tests L0-L1 only — **WARN: unit-only coverage** (include in council findings)
- Missing L1 on feature code — **WARN** (include in council findings)
- Missing L0 on spec-changing code — **WARN**
- Missing BF4 on boundary code — **WARN** (advisory, not blocking)
- All levels covered with `weighted_score >= 0.6` — no mention needed

When coverage gaps are found, run `/test <module>` to generate test candidates for uncovered code.
