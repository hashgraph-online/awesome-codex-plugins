# Evaluate PGO Workflow

Evaluate profile-guided optimization as a reproducible whole-program build input.

## Workflow Steps

### 1. Select Representative Evidence

- [ ] Choose whole-program CPU profiles from representative workloads.
- [ ] Record workload, duration, binary revision, main package, and profile digest.
- [ ] Review profile sensitivity and storage policy.

### 2. Build the Comparison

- [ ] Build matching final artifacts with `-pgo=off` and the selected profile.
- [ ] Keep toolchain, source, flags, environment, and target constant.
- [ ] Treat different main packages as separate PGO decisions.

### 3. Validate

- [ ] Benchmark representative final-binary workloads on supported targets.
- [ ] Compare latency, throughput, memory, build time, and artifact size.
- [ ] Re-profile the optimized artifact and verify the intended cost moved.
- [ ] Reject correctness or material workload regressions.

### 4. Preserve Provenance

- [ ] Hand PGO mode, profile digest, source workload, and main package to
      `go-cli-distribution` and release automation.
- [ ] Preserve the exact selected profile with the released build inputs.
- [ ] Define a refresh trigger or cadence.

## Exit Criteria

- [ ] PGO and `-pgo=off` artifacts were compared under equivalent conditions.
- [ ] The selected profile is representative, protected, and reproducible.
- [ ] Released bytes can be traced to the exact PGO input.
