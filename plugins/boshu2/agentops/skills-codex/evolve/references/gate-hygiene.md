# Gate Hygiene — Pre-Gate Sync and Output Parsing

Two recurring gate-stage frictions that compound across long sessions: missing source-surface rebuilds (the gate runs against stale binaries) and trusting trailing status lines (the gate output mixes blocking and advisory signals).

## Pre-gate source-surface detection

Before invoking `pre-push-gate.sh` (or any binary-dependent gate), inspect the staged diff and rebuild downstream artifacts if any of these surfaces changed:

| Changed surface | Required pre-gate action |
|---|---|
| `cli/**/*.go` | `cd cli && make build && go install ./cmd/ao` — refreshes `cli/bin/ao` and `~/go/bin/ao` so the gate sees the new Go behaviour |
| `skills/**` or `hooks/**` | `cd cli && make sync-hooks` — refreshes `cli/embedded/{skills,hooks}/` so the embedded-parity check passes |
| `skills-codex/**` | `bash scripts/regen-codex-hashes.sh` — refreshes generated_hash values in the codex manifest |
| `schemas/**` and `docs/contracts/**` together | re-run contract validation locally first; do not let CI surface the drift |

Detection recipe:

```bash
changed=$(git diff --cached --name-only)
echo "$changed" | grep -q '^cli/.*\.go$' && (cd cli && make build && go install ./cmd/ao)
echo "$changed" | grep -qE '^(skills/|hooks/)' && (cd cli && make sync-hooks)
echo "$changed" | grep -q '^skills-codex/' && bash scripts/regen-codex-hashes.sh
```

Without these pre-gate steps, the gate may fail with stale-binary or embedded-drift errors that look like real regressions but are just plumbing. Each false failure costs a turn of recovery work.

## Gate output parsing

The pre-push gate (and similar two-pass scripts) emits both blocking and advisory results. Trusting only the trailing status line conflates them. Use a structured grep:

```bash
# Capture full output, then parse explicit failure markers
bash scripts/pre-push-gate.sh --fast 2>&1 | tee /tmp/gate.log

# Authoritative blocking failures (case-sensitive Pass N: FAILED|BLOCKED)
if grep -E '^.*Pass [0-9]+: (FAILED|BLOCKED)' /tmp/gate.log >/dev/null; then
  echo "BLOCKING failure detected"
  exit 1
fi

# Advisory issues — record but don't block
grep -E 'advisory|warning|WARN' /tmp/gate.log || true
```

Anti-pattern: reading `tail -1 /tmp/gate.log` and treating "passed (N skipped)" as authoritative. A run can show "Pass 1: FAILED" mid-output and "passed (X skipped)" at the end if Pass 2 ran in advisory-only mode against the worktree. The structural markers (`Pass N: FAILED|BLOCKED`) are the truth.

## When to use `PRE_PUSH_SKIP_EVAL=1`

Documented release valve for the eval canary lane only, when:
- The canary is flaking on pre-existing infra (filed as a tracked bead)
- The current diff is unrelated to evals/, schemas/eval-, or cli/cmd/ao/eval
- A recorded recent run has confirmed the canary is currently 50/50

Never use `--no-verify`. The pre-commit hook is a no-op for most diffs but the principle violation is durable in `git log` and surfaces in post-mortem.

## Pre-push diff-scope check (mandatory before every commit)

Two cheap pre-commit reads catch the failure modes that cost a full fix-and-repush round each (the 2026-05-29 `/crank` + codex-budget reds):

1. **`git status --short` must show ALL intended files staged.** A half-staged commit — the feature gate-script left out while only its test was committed — let CI run the *old* code so the new assertion could not pass (the #612 red). A feature and its test are one commit, not the test alone.
2. **`git diff origin/main --stat` must be SCOPE-ONLY.** Confirm: no collateral deletions (a `git checkout --theirs` conflict take silently dropped two *unrelated* skill rows in the #600 rebase), and no lossy whole-file reformats (a 252-line `catalog.json` round-trip — discard those and use the idempotent appender). For generated/narrative files, restore `origin/main`'s version and **re-run the generator** rather than hand-merging.

## Triage red precisely — pre-existing-main vs your-change

Not every red is yours. The `agentops` main branch carries known pre-existing failures a local gate or a broad generator will surface:

- **Local `mkdocs --strict`** fails on tracked docs because the system `mkdocs` (≤1.1.2) can't parse the modern `mkdocs.yml` (needs material plugins). CI uses the venv and passes. Confirm a flagged file is `git ls-tree origin/main`-tracked AND absent from your diff → pre-existing, proceed.
- **~7 codex `.agentops-generated.json` drifts** (deps, provenance, red-team, release, scenario, trace, using-agentops): `regen-codex-hashes.sh` "updates" them because they're drifted on main. **REVERT them** (`git checkout origin/main -- <those>`) and keep only your skill's hash; surgically rebuild the manifest from `origin/main` + your delta. The CI artifact gate is changed-files-scoped (`--scope head`) so it ignores the pre-existing drift; sweeping them in adds unrelated churn and risks a manifest↔marker mismatch.

**Rule:** only fix red your own diff introduced. When a generator touches files outside your bead's scope, revert those files. "The generator changed it" never justifies shipping unrelated drift.

## See also

- [new-skill-landing.md](new-skill-landing.md) — the six derived surfaces a new/modified skill must regenerate in one shot (the companion to this diff-scope discipline).
