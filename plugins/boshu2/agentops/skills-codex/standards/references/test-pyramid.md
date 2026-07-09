# AI-Native Test Shape — L0 through L7

> Shared reference for RPI lifecycle skills. Loaded by `/discovery`, `/plan`, `/pre-mortem`, `/implement`, `/crank`, `/validate`, and `/post-mortem`.

## The AI-Native Test Shape

The traditional test pyramid (many L1 unit, fewer L2 integration, fewest L3 E2E) was an **economic optimization**: unit tests were cheapest for humans to write. AI agents eliminate that cost differential. When writing tests at any level costs roughly the same, the shape should optimize for **bug-finding value**, not writing cost.

**Evidence from 14,753 sessions and 946 council verdicts:**
- L0–L1 (contract + unit): Found **zero** production bugs. Useful only as regression guards.
- L2 (integration): Found **moderate** bugs — component interaction failures.
- L3+ (component, E2E, smoke): Found **all** real production bugs.

```
The Traditional Pyramid          The AI-Native Shape
(human cost-optimized)           (bug-finding-optimized)

      /  E2E  \                      /  L3/E2E  \
     / Integr. \                    /             \
    /   Unit    \                  /      L2       \    ← BULK: where bugs live
                                  /      L1         \
                                 /  L0 (contracts)   \
```

**The principle:** AI agents should write tests where bugs are found, not where tests are cheapest. L2 integration tests are the default *starting point* for all agent-written tests. L1 unit tests are always written for regression safety. AI agents write both — L2 first for bug-finding, L1 always for regression guards. The shift is in priority and sequencing, not elimination.

## Why This Matters for Agent Workflows

1. **Tests are specs, not verification.** In `--test-first` mode, agents write failing tests first, then implement. L2 describes *behavior* without over-specifying *implementation* — the right abstraction level for agent TDD.

2. **Tests are the ratchet between agents.** When swarm workers modify adjacent files, L2 integration tests catch conflicts at handoff boundaries. L1 tests miss these because they mock away the interaction.

3. **Coverage-as-constraint, not coverage-as-metric.** A coverage floor gives agents a safety net. Agents make different mistakes than humans (correct logic, wrong variable; perfect function, wrong call site). L2 catches those better than L1.

4. **Test runtime is the real bottleneck.** Agents can write 500 tests in minutes. But a 10-minute test suite blocks every feedback loop. Optimize for execution speed across levels, not test count at L1.

## The Full Testing Lifecycle

| Level | Name | What It Tests | When It Runs | Who Writes It | Bug-Finding Value |
|-------|------|---------------|--------------|---------------|-------------------|
| L0 | Contract Tests | Spec boundaries — registration, imports, file existence | Every commit (CI) | Agent from SPEC.md | Low (guards only) |
| L1 | Unit Tests | Single function/class behavior in isolation | Every commit (CI) | Agent via TDD | **Always write — regression safety** |
| L2 | Integration Tests | Multiple modules working together within a subsystem | Every commit (CI) | **Agent default — write these first** | **High (3x weight)** |
| L3 | Component Tests | Full subsystem end-to-end with mocked external deps | Pre-merge gate | Agent or human | **Highest (5x weight)** |
| L4 | Smoke Tests | Critical path works after deployment — "does it boot?" | Post-deploy (staging) | Human defines, agent implements | **Highest (5x weight)** |
| L5 | E2E Tests | Full system flow across subsystems, real infrastructure | Staging environment | Human designs, agent executes | High |
| L6 | Acceptance Tests | Does it do what the user actually needed? | Staging with real data | Human validates | Varies |
| L7 | Canary / Prod Validation | Does it work under real load with real users? | Production (gradual rollout) | Automated monitors + human judgment | Varies |

## Agent Autonomy Boundaries

```
┌───────────────────────────────────────────────────────────┐
│  AGENT-AUTONOMOUS (L0–L3)                                 │
│  Agent writes tests AND implementation.                   │
│  DEFAULT: Start at L2 (integration), add L1 for           │
│  regression guards, L0 for contracts, L3 for subsystems.  │
│                                                           │
│  L0: Contract — from SPEC.md alone                        │
│  L1: Unit     — always write for regression safety        │
│  L2: Integration — DEFAULT for all agent-written tests    │
│  L3: Component — agent writes, human defines scenarios    │
├───────────────────────────────────────────────────────────┤
│  HUMAN-GUIDED (L4–L7)                                     │
│  Human defines WHAT to test.                              │
│  Agent builds the test infrastructure.                    │
│                                                           │
│  L4: Smoke     — human defines "critical path"            │
│  L5: E2E       — human designs flow, agent harness        │
│  L6: Acceptance— human only validates                     │
│  L7: Prod      — monitors + human judgment                │
└───────────────────────────────────────────────────────────┘
```

## RPI Phase Mapping

| RPI Phase | Test Levels | What Happens |
|-----------|-------------|--------------|
| **Discovery** (`/discovery`, `/plan`) | L0–L3 scoping | Plan identifies which test levels apply. **Default: L2 required for all code-change issues.** Issues include `test_level` metadata. |
| **Pre-mortem** (`/pre-mortem`) | L0–L3 coverage check | Validates plan covers appropriate test levels. **Flags L1-only coverage as WARN.** |
| **Implementation** (`/implement`, `/crank`) | L0–L2 writing + execution | **TDD writes L2 integration tests first (RED).** L0 contracts from specs. L1 as regression guards. |
| **Validation** (`/validate`, `/post-mortem`) | L0–L3 coverage audit | Assesses test coverage. **L2+ coverage weighted 3-5x over L1 in vibe scoring.** |

## Test Level Selection Guide

Use this decision tree when planning which test levels to include:

```
Is it a code change (not docs/chore)?
  YES → L2 (integration) REQUIRED as default
  NO  → Skip testing

Does the change touch external APIs or I/O?
  YES → Add L0 (contract) + L1 (unit) for boundary guards
  NO  → L1 always (regression safety) + L2 required

Does it cross module boundaries?
  YES → L2 is already required — ensure cross-module paths tested
  NO  → L2 still required (test function-to-function interaction)

Does it affect a full subsystem workflow?
  YES → Add L3 (component)
  NO  → L2 sufficient

Is it deploying to staging/prod?
  YES → L4 (smoke) required, L5 (E2E) recommended
  NO  → Skip L4–L7
```

## Test Level Metadata for Issues

When creating issues in `/plan`, include test level metadata:

```json
{
  "test_levels": {
    "required": ["L2"],
    "recommended": ["L1", "L3"],
    "deferred": [],
    "rationale": "AI-native default: L2 first for bug-finding, L1 always for regression safety. AI agents write both. L3 if full subsystem affected."
  }
}
```

## Bug-Finding Levels (Agent-Autonomous)

> **Proven 2026-03-14 on jren-cm:** 3,321 L1 unit tests found 0 new bugs. These levels found 8.
> Evidence: `/Users/fullerbt/gt/jren_cm/crew/ichigo/scripts/.agents/council/2026-03-14-post-mortem-full-session-methodology.md`

L0–L3 are the **coverage shape** — they verify code works as designed.
These are the **bug-finding shape** — they find bugs the coverage shape misses.

| Level | Name | What It Finds | Agent Writes? | Bugs Found (jren-cm) |
|-------|------|---------------|---------------|---------------------|
| BF1 | Property-Based | Edge cases from randomized inputs (non-IPv4, empty strings, unicode) | Yes | 1 crash |
| BF2 | Golden/Snapshot | Output drift, template regression | Yes | 0 (regression guard) |
| BF3 | Mutation | Untested code paths (operator flips that tests don't catch) | Yes (config) | 13 gaps |
| BF4 | Chaos/Negative | Unhandled exceptions at system boundaries (corrupt DB, permissions, timeouts) | Yes | 4 bugs |
| BF5 | Script Functional | Bash runtime crashes, jq logic errors, undefined functions | Yes | 2 critical bugs |
| BF6 | Regression | Reintroduced bugs that were previously fixed | Yes | N/A (guard) |
| BF7 | Performance | Speed regressions in parsers, renderers, hot paths | Yes (config) | N/A (baseline) |
| BF8 | Backward Compat | Breaking changes to input formats consumers depend on | Yes | N/A (guard) |
| BF9 | Security (In-Test) | Secrets leakage in output, unsanitized inputs, unsafe permissions | Yes | N/A (guard) |

### Bug-Finding Level Details

**BF1 — Property-Based Testing**

Randomize inputs to every data transformation. Catches crashes on inputs no human would write.

| Language | Tool | Example |
|----------|------|---------|
| Python | `hypothesis` | `@given(st.text())` on parsers |
| Go | `gopter` or `rapid` | `rapid.Check(t, func(t *rapid.T) { ... })` |
| TypeScript | `fast-check` | `fc.assert(fc.property(fc.string(), (s) => ...))` |
| Rust | `proptest` | `proptest! { fn test(s in ".*") { ... } }` |

**BF2 — Golden/Snapshot Testing**

Generate canonical output, save as golden file. Test asserts exact match. Use `GOLDEN_UPDATE=1` env var to regenerate.

| Language | Tool | Pattern |
|----------|------|---------|
| Python | `pytest` + `tmp_path` | `assert output == golden_path.read_text()` |
| Go | `testdata/` convention | `golden.Update(t, got)` / `golden.Get(t)` |
| TypeScript | `vitest` snapshot | `expect(output).toMatchSnapshot()` |
| Rust | `insta` | `insta::assert_snapshot!(output)` |

**BF3 — Mutation Testing**

Flip operators and conditions in source. If tests still pass, there's an untested path.

| Language | Tool | Command |
|----------|------|---------|
| Python | `mutmut` | `mutmut run --paths-to-mutate src/critical.py` |
| Go | `go-mutesting` | `go-mutesting ./pkg/critical/...` |
| TypeScript | `stryker` | `npx stryker run --mutate 'src/critical/**'` |
| Rust | `cargo-mutants` | `cargo mutants --package critical` |

**Target critical modules only.** Full-codebase mutation is too slow (hours). Pick the 3-5 modules with highest blast radius.

**BF4 — Chaos/Negative Testing**

Inject failures at every system boundary. The bugs L1 mocks away.

```python
# Python pattern
@patch("module.external_call", side_effect=TimeoutError)
def test_timeout_returns_specific_error(mock):
    result = function_under_test()
    assert result.error_class == "timeout"  # NOT "unknown"
```

```go
// Go pattern
func TestHandlesCorruptDB(t *testing.T) {
    db := newCorruptDB()
    store, err := NewStore(db)
    require.NoError(t, err)
    assert.False(t, store.Enabled())  // graceful degradation, not crash
}
```

**Checklist for every subsystem:**
- [ ] External API timeout → specific error, not crash
- [ ] External API connection refused → specific error
- [ ] File permission denied → graceful failure
- [ ] Database corruption → degraded mode, not crash
- [ ] Invalid/missing config → clear error message

**BF5 — Script Functional Testing**

Stub external tools via PATH override, source the script, call its functions, verify output.

```bash
# Create stub directory with fake oc/kubectl
STUB_DIR=$(mktemp -d)
cat > "${STUB_DIR}/oc" << 'EOF'
#!/bin/bash
echo '{"items": [{"status": {"phase": "Failed"}}]}'
EOF
chmod +x "${STUB_DIR}/oc"

# Run specialist with stubbed tools
PATH="${STUB_DIR}:${ORIGINAL_PATH}" source specialist.sh
result=$(scan 2>&1)
echo "$result" | python3 -c "import json,sys; json.load(sys.stdin)"  # valid JSON?
```

**BF6 — Regression Testing (Bug-Specific Replay)**

Every bug fix gets a test that reproduces the exact failure. Name it after the bug ID. These prevent regressions and serve as executable documentation.

| Language | Pattern | Naming |
|----------|---------|--------|
| Python | `def test_bug_ag_xyz_empty_input_crashes():` | `test_bug_<id>_<description>` |
| Go | `func TestBug_AG_XYZ_EmptyInputCrashes(t *testing.T) {` | `TestBug_<ID>_<Description>` |
| Shell | Separate test file: `tests/regression/test_ag_xyz.sh` | `test_<id>.sh` |

```python
# Python pattern
def test_bug_ag_m0r_parse_reader_crashes_on_empty_value():
    """Regression: parse_reader crashed on config lines with empty values (ag-m0r)."""
    stream = io.StringIO("SITE_NAME=\nDB_HOST=prod-db")
    ctx = parse_reader(stream)  # must not raise
    assert ctx.site_name == ""  # empty, not crash
    assert ctx.db_host == "prod-db"
```

```go
// Go pattern
func TestBug_AG_3B7_NilMapPanic(t *testing.T) {
    // Regression: passing nil options caused panic in processGoals (ag-3b7)
    result, err := processGoals(nil)
    require.NoError(t, err)
    assert.Empty(t, result)
}
```

**BF7 — Performance/Benchmark Testing**

Detect speed regressions mechanically. Set baselines, fail on significant deviation.

| Language | Tool | Pattern |
|----------|------|---------|
| Python | `pytest-benchmark` | `def test_parse_speed(benchmark): benchmark(parse_reader, large_input)` |
| Go | Built-in `testing.B` | `func BenchmarkParseConfig(b *testing.B) { for b.Loop() { parse(input) } }` |
| TypeScript | `vitest bench` | `bench('parse', () => { parseConfig(input) })` |
| Rust | `criterion` | `c.bench_function("parse", \|b\| b.iter(\|\| parse(input)))` |

```python
# Python pattern — pytest-benchmark
def test_parse_config_performance(benchmark):
    """Parser must handle 1000-line config in <100ms."""
    large_config = "\n".join(f"KEY_{i}=value_{i}" for i in range(1000))
    result = benchmark(parse_reader, io.StringIO(large_config))
    assert isinstance(result, SiteContext)
```

```go
// Go pattern — built-in benchmarks
func BenchmarkParseConfig(b *testing.B) {
    input := generateLargeConfig(1000) // 1000 key-value pairs
    b.ResetTimer()
    for b.Loop() {
        parseConfig(input)
    }
}
```

**Target critical hot paths only.** Full-codebase benchmarks are maintenance burden. Pick parsers, renderers, and high-frequency functions.

**BF8 — Backward Compatibility Testing**

Old inputs must still parse after code changes. Maintain a corpus of real inputs from prior versions (anonymized) as fixtures.

| Language | Pattern | Fixture Location |
|----------|---------|-----------------|
| Python | `@pytest.mark.parametrize("fixture", glob("tests/fixtures/compat/*.env"))` | `tests/fixtures/compat/` |
| Go | `testdata/compat/` convention | `testdata/compat/` |
| Shell | `tests/fixtures/compat/` | `tests/fixtures/compat/` |

```python
# Python pattern
@pytest.mark.parametrize("fixture", sorted(glob("tests/fixtures/compat/*.env")))
def test_legacy_config_parses(fixture):
    """Every historical config.env must still parse without error."""
    ctx = parse_config_env(fixture)
    assert ctx.site_name  # minimal validity — at least one required field populated
```

```go
// Go pattern
func TestBackwardCompat(t *testing.T) {
    fixtures, _ := filepath.Glob("testdata/compat/*.env")
    for _, f := range fixtures {
        t.Run(filepath.Base(f), func(t *testing.T) {
            cfg, err := ParseConfigFile(f)
            require.NoError(t, err, "legacy config must still parse")
            assert.NotEmpty(t, cfg.SiteName)
        })
    }
}
```

**Maintenance:** When changing input formats, add the OLD format as a new compat fixture BEFORE making the change. This prevents silent breakage for consumers that haven't upgraded yet.

**BF9 — Security Testing (In-Test)**

Test that secrets are redacted, inputs are sanitized, and sensitive data never leaks into output. Distinct from security scanning (semgrep/gitleaks) — these are behavioral tests.

| Category | What to Test | Pattern |
|----------|-------------|---------|
| Secrets redaction | `render_export()` output contains no raw passwords/tokens | Assert output lacks patterns like `PASSWORD=actual_value` |
| Input sanitization | Untrusted input can't inject commands/paths | Parameterize with injection payloads (`../`, `; rm`, `${VAR}`) |
| Error message safety | Stack traces and error messages don't leak secrets | Assert error output contains no sensitive env vars |
| File permission safety | Generated files have correct permissions (not world-readable) | `os.stat()` after creation, assert mode |

```python
# Python pattern — secrets redaction
def test_render_export_redacts_secrets():
    """render_export must never emit raw secret values."""
    ctx = SiteContext(site_name="test", db_password="s3cr3t!", api_key="ak-12345")
    output = render_export(ctx)
    assert "s3cr3t!" not in output, "raw password leaked in export"
    assert "ak-12345" not in output, "raw API key leaked in export"
    assert "REDACTED" in output or "****" in output, "secrets not visibly redacted"
```

```go
// Go pattern — path traversal rejection
func TestRejectsPathTraversal(t *testing.T) {
    payloads := []string{"../../../etc/passwd", "..\\windows\\system32", "foo/../bar"}
    for _, p := range payloads {
        t.Run(p, func(t *testing.T) {
            _, err := LoadConfig(p)
            assert.Error(t, err, "must reject path traversal")
        })
    }
}
```

### When to Use Bug-Finding Levels

```
After L0–L3 coverage is complete, run bug-finding levels:

  Has data transformations (parse/render/serialize)?
    YES → BF1 (property-based) — randomize all inputs

  Has output generators (config files, reports, manifests)?
    YES → BF2 (golden) — snapshot every output

  Has critical modules (auth, state, error handling)?
    YES → BF3 (mutation) — targeted mutation on those modules

  Has external boundaries (APIs, databases, filesystems)?
    YES → BF4 (chaos) — inject failures at every boundary

  Has bash/shell scripts?
    YES → BF5 (functional) — stub tools, verify behavior

  Fixing a bug?
    YES → BF6 (regression) — reproduce the exact failure before fixing

  Has hot-path functions (parsers, renderers, serializers)?
    YES → BF7 (performance) — benchmark and set baseline

  Has input formats that external consumers depend on?
    YES → BF8 (backward compat) — maintain fixture corpus

  Has secrets, credentials, or sensitive data in scope?
    YES → BF9 (security) — test redaction and sanitization
```

### Bug-Finding in RPI Phases

| RPI Phase | Bug-Finding Action |
|-----------|--------------------|
| `/plan` | Classify which BF levels apply per issue |
| `/pre-mortem` | Verify BF levels are planned for boundary-touching code |
| `/implement` | Write BF tests alongside L0–L3 (or as separate wave) |
| `/validate` | **Check BF coverage before council** — flag missing chaos/property tests on boundary code |
| `/post-mortem` | Assess BF bug discovery count. If BF4 found 0 bugs → either code is solid or chaos tests are too weak |
| `/implement` (bug fix) | **BF6 mandatory** — reproduce bug as failing test BEFORE writing fix |
| `/validate` (performance) | Check BF7 benchmarks if hot-path code changed |
| `/plan` (format changes) | Flag BF8 backward compat — add old format as fixture before changing |
| `/pre-mortem` (security) | Verify BF9 tests planned for code handling secrets or user input |

## Fixture Fidelity — guard tests must use the real persisted shape

> **Proven 2026-05-31 (ag-mjlg / PR #652):** a next-work materialize over-creation bug (44 beads planned vs 16 expected) shipped green because `TestNextWorkMaterialize_SkipsConsumed` set `consumed` at the **per-item** level while the real `next-work.jsonl` marks `consumed` at the **batch** level. The guard test exercised a data shape production never emits, so CI passed on a fixture that could not catch the bug.

**The standard:** regression, idempotency, skip, dedup, and consumed/already-done guard tests MUST build their fixtures from the **real persisted data shape** — round-trip an actual on-disk sample (write → read back through the production serializer/parser), or assert against a checked-in real example. Do NOT hand-construct the in-memory struct via a convenient constructor when production reads the value from disk: the constructor lets you set fields at a granularity (per-item vs batch-level, flat vs nested) that the persisted format never produces, giving a false green.

**Why it bites agents specifically:** an agent writing a guard test reaches for the cheapest fixture — the in-memory constructor — because it compiles fastest and reads cleanest. That fixture silently diverges from the persisted shape, and the test then "passes" by asserting on a state the system can't reach. The skip/dedup logic under test reads the persisted shape, so the test proves nothing about the real path.

**How to comply:**
- Round-trip the fixture: serialize a sample with the production writer, read it back with the production reader, then assert. If that path doesn't exist yet, write the sample to a temp file in the real on-disk format and load it through the production loader.
- Match the marker granularity exactly: if production records `consumed`/`skip`/`dedup` state at the batch (or parent, or envelope) level, set it there — never only at the item level.
- Prefer a checked-in real sample (a trimmed copy of an actual artifact) over a synthetic one for the canonical happy/skip cases.

**Pre-mortem / checklist flag:** when reviewing a plan or diff that adds a skip/dedup/consumed/idempotency guard test, FLAG any fixture built only from an in-memory constructor or that sets the guard marker at item-level when the persisted artifact marks it at batch-level. Require the fixture to round-trip the real persisted shape before the test counts as coverage. (See `.claude/rules/go.md` → "Guard-test fixtures must use the real persisted shape.")

## Coverage Assessment Template

Used by `/post-mortem` and `/validate` to assess test shape health:

### Coverage Shape (L0–L3)

| Level | Tests Exist? | Tests Pass? | Coverage Gap? | Action |
|-------|-------------|-------------|---------------|--------|
| L0 Contract | yes/no | yes/no/na | description | add/fix/ok |
| L1 Unit | yes/no | yes/no/na | description | add/fix/ok |
| L2 Integration | yes/no | yes/no/na | description | add/fix/ok |
| L3 Component | yes/no | yes/no/na | description | add/fix/ok |
| L4+ | human-gated | — | — | defer to human |

### Bug-Finding Shape (BF1–BF9)

| Level | Tests Exist? | Bugs Found? | Gap? | Action |
|-------|-------------|-------------|------|--------|
| BF1 Property | yes/no | count | data transforms without property tests | add for parsers/renderers |
| BF2 Golden | yes/no | N/A | output generators without golden files | add for config/report generators |
| BF3 Mutation | yes/no | surviving mutants | critical modules with <80% mutation score | target top 3 modules |
| BF4 Chaos | yes/no | count | external boundaries without failure injection | add for every API/DB/FS boundary |
| BF5 Script Functional | yes/no | count | bash scripts without functional tests | add for top 10 by complexity |
| BF6 Regression | yes/no | count | bug fixes without reproducing tests | add for every bug fix |
| BF7 Performance | yes/no | baseline set? | hot-path functions without benchmarks | add for parsers/renderers |
| BF8 Backward Compat | yes/no | fixtures count | input formats without compat corpus | add fixture corpus |
| BF9 Security | yes/no | count | code handling secrets without redaction tests | add for every secret boundary |
